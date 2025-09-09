"""
⏱️ Timeout Management and Graceful Degradation

Advanced timeout management with graceful degradation strategies:
- Adaptive timeouts based on service performance
- Cascade timeout prevention  
- Graceful degradation with fallback responses
- Performance-based timeout adjustment
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, Union, TypeVar, Generic
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import statistics
import threading
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TimeoutStrategy(Enum):
    """Timeout handling strategies"""
    FAIL_FAST = "fail_fast"            # Fail immediately on timeout
    GRACEFUL_DEGRADATION = "graceful"  # Return fallback response
    BEST_EFFORT = "best_effort"        # Return partial results
    ADAPTIVE = "adaptive"              # Adjust timeout based on performance


@dataclass
class TimeoutConfig:
    """Timeout configuration"""
    initial_timeout: float = 10.0      # Initial timeout in seconds
    min_timeout: float = 1.0           # Minimum allowed timeout
    max_timeout: float = 60.0          # Maximum allowed timeout
    strategy: TimeoutStrategy = TimeoutStrategy.ADAPTIVE
    adaptation_factor: float = 1.5     # Factor for timeout adaptation
    performance_window: int = 100      # Window size for performance tracking
    percentile_target: float = 0.95    # Target percentile for timeout setting


@dataclass  
class TimeoutResult(Generic[T]):
    """Result of timeout-protected operation"""
    success: bool
    value: Optional[T]
    elapsed_ms: float
    timed_out: bool
    fallback_used: bool = False
    partial_result: bool = False
    error: Optional[Exception] = None


@dataclass
class PerformanceMetric:
    """Performance metric for timeout adaptation"""
    timestamp: float
    duration_ms: float
    success: bool
    operation: str


class AdaptiveTimeoutManager:
    """
    Adaptive timeout manager that adjusts timeouts based on service performance
    """
    
    def __init__(self, name: str, config: TimeoutConfig = None):
        self.name = name
        self.config = config or TimeoutConfig()
        
        # Performance tracking
        self.performance_history: deque = deque(maxlen=self.config.performance_window)
        self.current_timeout = self.config.initial_timeout
        
        # Statistics
        self.total_operations = 0
        self.total_timeouts = 0
        self.total_adaptations = 0
        
        self.lock = threading.RLock()
        
        # Background adaptation
        self._last_adaptation = time.time()
        self._adaptation_interval = 60.0  # Adapt every minute
        
        logger.info(f"Adaptive timeout manager '{name}' initialized with {self.config.initial_timeout}s timeout")
    
    async def execute_with_timeout(
        self,
        operation: Callable,
        *args,
        operation_name: str = "unknown",
        custom_timeout: Optional[float] = None,
        fallback_function: Optional[Callable] = None,
        **kwargs
    ) -> TimeoutResult[T]:
        """
        Execute operation with adaptive timeout
        
        Args:
            operation: Function to execute
            *args, **kwargs: Function arguments
            operation_name: Name for performance tracking
            custom_timeout: Override calculated timeout
            fallback_function: Function to call on timeout for graceful degradation
            
        Returns:
            Timeout result with value or error
        """
        with self.lock:
            self.total_operations += 1
            timeout = custom_timeout or self.current_timeout
        
        start_time = time.time()
        
        try:
            # Execute with timeout
            if asyncio.iscoroutinefunction(operation):
                result = await asyncio.wait_for(operation(*args, **kwargs), timeout=timeout)
            else:
                # Run sync operation in thread pool with timeout
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, operation, *args, **kwargs),
                    timeout=timeout
                )
            
            elapsed = (time.time() - start_time) * 1000
            
            # Record successful operation
            self._record_performance(operation_name, elapsed, True)
            
            return TimeoutResult(
                success=True,
                value=result,
                elapsed_ms=elapsed,
                timed_out=False
            )
            
        except asyncio.TimeoutError:
            elapsed = (time.time() - start_time) * 1000
            
            # Record timeout
            self._record_performance(operation_name, elapsed, False)
            
            with self.lock:
                self.total_timeouts += 1
            
            # Handle timeout based on strategy
            if self.config.strategy == TimeoutStrategy.GRACEFUL_DEGRADATION and fallback_function:
                try:
                    fallback_result = await self._execute_fallback(fallback_function, *args, **kwargs)
                    return TimeoutResult(
                        success=True,
                        value=fallback_result,
                        elapsed_ms=elapsed,
                        timed_out=True,
                        fallback_used=True
                    )
                except Exception as e:
                    logger.error(f"Fallback function failed: {e}")
            
            logger.warning(f"Operation '{operation_name}' timed out after {timeout:.1f}s")
            
            return TimeoutResult(
                success=False,
                value=None,
                elapsed_ms=elapsed,
                timed_out=True,
                error=asyncio.TimeoutError(f"Operation timed out after {timeout:.1f}s")
            )
            
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            self._record_performance(operation_name, elapsed, False)
            
            return TimeoutResult(
                success=False,
                value=None,
                elapsed_ms=elapsed,
                timed_out=False,
                error=e
            )
    
    async def _execute_fallback(self, fallback_function: Callable, *args, **kwargs) -> Any:
        """Execute fallback function with its own timeout"""
        fallback_timeout = min(self.current_timeout * 0.5, 5.0)  # 50% of current timeout, max 5s
        
        if asyncio.iscoroutinefunction(fallback_function):
            return await asyncio.wait_for(fallback_function(*args, **kwargs), timeout=fallback_timeout)
        else:
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, fallback_function, *args, **kwargs),
                timeout=fallback_timeout
            )
    
    def _record_performance(self, operation: str, duration_ms: float, success: bool) -> None:
        """Record performance metric"""
        metric = PerformanceMetric(
            timestamp=time.time(),
            duration_ms=duration_ms,
            success=success,
            operation=operation
        )
        
        with self.lock:
            self.performance_history.append(metric)
            
            # Trigger adaptation if enough time has passed
            if time.time() - self._last_adaptation >= self._adaptation_interval:
                self._adapt_timeout()
    
    def _adapt_timeout(self) -> None:
        """Adapt timeout based on performance history"""
        if len(self.performance_history) < 10:
            return  # Not enough data
        
        # Get successful operations only
        successful_operations = [m for m in self.performance_history if m.success]
        
        if not successful_operations:
            # No successful operations, increase timeout
            new_timeout = min(self.current_timeout * self.config.adaptation_factor, self.config.max_timeout)
        else:
            # Calculate target timeout based on percentile
            response_times = [m.duration_ms / 1000 for m in successful_operations]  # Convert to seconds
            
            if len(response_times) > 1:
                target_percentile_index = int(len(response_times) * self.config.percentile_target)
                sorted_times = sorted(response_times)
                target_timeout = sorted_times[min(target_percentile_index, len(sorted_times) - 1)]
                
                # Apply adaptation factor for buffer
                new_timeout = target_timeout * self.config.adaptation_factor
                
                # Ensure within bounds
                new_timeout = max(self.config.min_timeout, min(new_timeout, self.config.max_timeout))
            else:
                new_timeout = self.current_timeout
        
        # Update timeout if significantly different
        if abs(new_timeout - self.current_timeout) > 0.5:  # At least 500ms difference
            old_timeout = self.current_timeout
            self.current_timeout = new_timeout
            self.total_adaptations += 1
            self._last_adaptation = time.time()
            
            logger.info(f"Timeout adapted for '{self.name}': {old_timeout:.1f}s -> {new_timeout:.1f}s")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get timeout manager statistics"""
        with self.lock:
            recent_metrics = list(self.performance_history)
            
            if not recent_metrics:
                return {
                    'name': self.name,
                    'current_timeout': self.current_timeout,
                    'total_operations': self.total_operations,
                    'total_timeouts': self.total_timeouts,
                    'timeout_rate': 0,
                    'avg_response_time_ms': 0
                }
            
            successful_metrics = [m for m in recent_metrics if m.success]
            response_times = [m.duration_ms for m in recent_metrics]
            
            return {
                'name': self.name,
                'current_timeout': self.current_timeout,
                'total_operations': self.total_operations,
                'total_timeouts': self.total_timeouts,
                'total_adaptations': self.total_adaptations,
                'timeout_rate': self.total_timeouts / max(1, self.total_operations),
                'success_rate': len(successful_metrics) / len(recent_metrics),
                'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
                'p95_response_time_ms': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else 0,
                'performance_samples': len(recent_metrics)
            }
    
    def reset_timeout(self) -> None:
        """Reset timeout to initial value"""
        with self.lock:
            self.current_timeout = self.config.initial_timeout
            self.performance_history.clear()
            logger.info(f"Timeout reset to {self.config.initial_timeout}s for '{self.name}'")


class CascadeTimeoutManager:
    """
    Manages cascading timeouts to prevent timeout storms
    """
    
    def __init__(self):
        self.active_operations: Dict[str, List[datetime]] = {}
        self.cascade_threshold = 5  # Max concurrent operations before cascade protection
        self.cascade_timeout_reduction = 0.7  # Reduce timeout by 30% during cascade
        self.lock = threading.RLock()
        
        logger.info("Cascade timeout manager initialized")
    
    @asynccontextmanager
    async def protect_cascade(self, operation_name: str, base_timeout: float):
        """
        Context manager for cascade protection
        
        Args:
            operation_name: Name of the operation type
            base_timeout: Base timeout value
            
        Yields:
            Adjusted timeout value
        """
        # Register operation start
        with self.lock:
            if operation_name not in self.active_operations:
                self.active_operations[operation_name] = []
            
            # Clean up old operations (older than 5 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=5)
            self.active_operations[operation_name] = [
                op_time for op_time in self.active_operations[operation_name]
                if op_time > cutoff_time
            ]
            
            # Add current operation
            self.active_operations[operation_name].append(datetime.now())
            
            # Calculate adjusted timeout
            active_count = len(self.active_operations[operation_name])
            if active_count > self.cascade_threshold:
                adjusted_timeout = base_timeout * self.cascade_timeout_reduction
                logger.warning(
                    f"Cascade protection activated for '{operation_name}': "
                    f"{active_count} concurrent operations, timeout reduced to {adjusted_timeout:.1f}s"
                )
            else:
                adjusted_timeout = base_timeout
        
        try:
            yield adjusted_timeout
        finally:
            # Unregister operation
            with self.lock:
                if operation_name in self.active_operations and self.active_operations[operation_name]:
                    self.active_operations[operation_name].pop()
    
    def get_cascade_stats(self) -> Dict[str, Any]:
        """Get cascade protection statistics"""
        with self.lock:
            return {
                'active_operations': {
                    name: len(ops) for name, ops in self.active_operations.items()
                },
                'cascade_threshold': self.cascade_threshold,
                'timeout_reduction_factor': self.cascade_timeout_reduction
            }


class TimeoutManagerRegistry:
    """
    Registry for managing multiple timeout managers
    """
    
    def __init__(self):
        self.managers: Dict[str, AdaptiveTimeoutManager] = {}
        self.cascade_manager = CascadeTimeoutManager()
        self.lock = threading.RLock()
        
        logger.info("Timeout manager registry initialized")
    
    def get_or_create_manager(
        self,
        name: str,
        config: Optional[TimeoutConfig] = None
    ) -> AdaptiveTimeoutManager:
        """Get or create timeout manager"""
        with self.lock:
            if name not in self.managers:
                self.managers[name] = AdaptiveTimeoutManager(name, config)
            return self.managers[name]
    
    async def execute_with_adaptive_timeout(
        self,
        manager_name: str,
        operation: Callable,
        *args,
        operation_name: str = "unknown",
        config: Optional[TimeoutConfig] = None,
        fallback_function: Optional[Callable] = None,
        enable_cascade_protection: bool = True,
        **kwargs
    ) -> TimeoutResult[T]:
        """
        Execute operation with adaptive timeout and cascade protection
        
        Args:
            manager_name: Name of the timeout manager
            operation: Function to execute
            *args, **kwargs: Function arguments
            operation_name: Name for performance tracking
            config: Timeout configuration
            fallback_function: Fallback function for graceful degradation
            enable_cascade_protection: Enable cascade protection
            
        Returns:
            Timeout result
        """
        manager = self.get_or_create_manager(manager_name, config)
        
        if enable_cascade_protection:
            async with self.cascade_manager.protect_cascade(operation_name, manager.current_timeout) as adjusted_timeout:
                return await manager.execute_with_timeout(
                    operation,
                    *args,
                    operation_name=operation_name,
                    custom_timeout=adjusted_timeout,
                    fallback_function=fallback_function,
                    **kwargs
                )
        else:
            return await manager.execute_with_timeout(
                operation,
                *args,
                operation_name=operation_name,
                fallback_function=fallback_function,
                **kwargs
            )
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all timeout managers"""
        with self.lock:
            return {
                'managers': {name: manager.get_stats() for name, manager in self.managers.items()},
                'cascade_protection': self.cascade_manager.get_cascade_stats(),
                'total_managers': len(self.managers)
            }
    
    def reset_all_managers(self) -> None:
        """Reset all timeout managers"""
        with self.lock:
            for manager in self.managers.values():
                manager.reset_timeout()
        logger.info("All timeout managers reset")


# Global registry instance
_timeout_registry = None


def get_timeout_registry() -> TimeoutManagerRegistry:
    """Get or create global timeout registry"""
    global _timeout_registry
    if _timeout_registry is None:
        _timeout_registry = TimeoutManagerRegistry()
    return _timeout_registry


# Convenience functions
async def execute_with_timeout(
    service_name: str,
    operation: Callable,
    *args,
    timeout_config: Optional[TimeoutConfig] = None,
    fallback_function: Optional[Callable] = None,
    **kwargs
) -> TimeoutResult[T]:
    """Execute operation with adaptive timeout"""
    registry = get_timeout_registry()
    return await registry.execute_with_adaptive_timeout(
        service_name,
        operation,
        *args,
        operation_name=operation.__name__ if hasattr(operation, '__name__') else 'unknown',
        config=timeout_config,
        fallback_function=fallback_function,
        **kwargs
    )


async def execute_with_graceful_degradation(
    service_name: str,
    operation: Callable,
    fallback_function: Callable,
    *args,
    timeout_seconds: Optional[float] = None,
    **kwargs
) -> TimeoutResult[T]:
    """Execute operation with graceful degradation"""
    config = TimeoutConfig(
        strategy=TimeoutStrategy.GRACEFUL_DEGRADATION,
        initial_timeout=timeout_seconds or 10.0
    )
    
    registry = get_timeout_registry()
    return await registry.execute_with_adaptive_timeout(
        service_name,
        operation,
        *args,
        config=config,
        fallback_function=fallback_function,
        **kwargs
    )


# Decorators for easy timeout management
def with_adaptive_timeout(
    service_name: str,
    config: Optional[TimeoutConfig] = None,
    fallback_function: Optional[Callable] = None
):
    """Decorator for adaptive timeout"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await execute_with_timeout(
                service_name,
                func,
                *args,
                timeout_config=config,
                fallback_function=fallback_function,
                **kwargs
            )
            
            if result.success:
                return result.value
            else:
                if result.error:
                    raise result.error
                else:
                    raise asyncio.TimeoutError("Operation timed out")
        
        return wrapper
    return decorator


def with_graceful_degradation(
    service_name: str,
    fallback_function: Callable,
    timeout_seconds: Optional[float] = None
):
    """Decorator for graceful degradation"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await execute_with_graceful_degradation(
                service_name,
                func,
                fallback_function,
                *args,
                timeout_seconds=timeout_seconds,
                **kwargs
            )
            
            if result.success:
                return result.value
            else:
                if result.error:
                    raise result.error
                else:
                    raise asyncio.TimeoutError("Operation timed out")
        
        return wrapper
    return decorator