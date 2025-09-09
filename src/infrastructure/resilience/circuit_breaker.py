"""
🔧 Circuit Breaker and Resilience Patterns

Implements fault tolerance patterns for external service interactions:
- Circuit breaker pattern with automatic failure detection and recovery
- Retry mechanisms with exponential backoff and jitter
- Bulkhead pattern for resource isolation
- Timeout management with graceful degradation
"""

import asyncio
import time
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import deque
import random
import threading
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Failures to trigger open state
    recovery_timeout: int = 30  # Seconds before trying half-open
    success_threshold: int = 3  # Successes to close circuit
    timeout_seconds: float = 10.0  # Request timeout
    sliding_window_size: int = 100  # Request window size
    minimum_requests: int = 10  # Minimum requests before evaluation


@dataclass
class CallResult:
    """Result of a protected call"""
    success: bool
    response_time_ms: float
    error: Optional[Exception] = None
    timestamp: float = field(default_factory=time.time)


class CircuitBreaker:
    """
    Circuit breaker implementation with monitoring and automatic recovery
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        
        # Request history for statistics
        self.call_history: deque = deque(maxlen=self.config.sliding_window_size)
        self.lock = threading.RLock()
        
        # Monitoring
        self.total_calls = 0
        self.total_failures = 0
        self.total_rejections = 0
        self.state_transitions = []
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {self.config}")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: When circuit is open
            TimeoutError: When request times out
            Exception: Original function exception
        """
        with self.lock:
            self.total_calls += 1
            
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if not self._should_attempt_reset():
                    self.total_rejections += 1
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Next attempt in {self._time_until_retry():.1f}s"
                    )
                else:
                    # Transition to half-open
                    self._transition_to_half_open()
        
        # Execute with timeout
        start_time = time.time()
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs),
                timeout=self.config.timeout_seconds
            )
            
            response_time = (time.time() - start_time) * 1000
            self._record_success(response_time)
            
            return result
            
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            error = TimeoutError(f"Request timeout after {self.config.timeout_seconds}s")
            self._record_failure(error, response_time)
            raise error
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._record_failure(e, response_time)
            raise
    
    def _record_success(self, response_time_ms: float) -> None:
        """Record successful call"""
        with self.lock:
            result = CallResult(success=True, response_time_ms=response_time_ms)
            self.call_history.append(result)
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            
            logger.debug(f"Circuit '{self.name}': Success in {response_time_ms:.1f}ms")
    
    def _record_failure(self, error: Exception, response_time_ms: float) -> None:
        """Record failed call"""
        with self.lock:
            self.total_failures += 1
            result = CallResult(success=False, response_time_ms=response_time_ms, error=error)
            self.call_history.append(result)
            
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED:
                if self._should_trip():
                    self._transition_to_open()
            elif self.state == CircuitState.HALF_OPEN:
                self._transition_to_open()
            
            logger.warning(f"Circuit '{self.name}': Failure - {error}")
    
    def _should_trip(self) -> bool:
        """Check if circuit should trip to open state"""
        if len(self.call_history) < self.config.minimum_requests:
            return False
        
        # Calculate failure rate in sliding window
        recent_failures = sum(1 for call in self.call_history if not call.success)
        failure_rate = recent_failures / len(self.call_history)
        
        return (self.failure_count >= self.config.failure_threshold and 
                failure_rate > 0.5)  # More than 50% failure rate
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt reset to half-open"""
        return time.time() - self.last_failure_time >= self.config.recovery_timeout
    
    def _time_until_retry(self) -> float:
        """Time until next retry attempt"""
        return max(0, self.config.recovery_timeout - (time.time() - self.last_failure_time))
    
    def _transition_to_open(self) -> None:
        """Transition to open state"""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.success_count = 0
        self._record_state_transition(old_state, CircuitState.OPEN)
        logger.warning(f"Circuit breaker '{self.name}' OPENED")
    
    def _transition_to_half_open(self) -> None:
        """Transition to half-open state"""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.failure_count = 0
        self._record_state_transition(old_state, CircuitState.HALF_OPEN)
        logger.info(f"Circuit breaker '{self.name}' HALF-OPEN")
    
    def _transition_to_closed(self) -> None:
        """Transition to closed state"""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self._record_state_transition(old_state, CircuitState.CLOSED)
        logger.info(f"Circuit breaker '{self.name}' CLOSED")
    
    def _record_state_transition(self, from_state: CircuitState, to_state: CircuitState) -> None:
        """Record state transition for monitoring"""
        transition = {
            'timestamp': time.time(),
            'from_state': from_state.value,
            'to_state': to_state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count
        }
        self.state_transitions.append(transition)
        
        # Keep only last 50 transitions
        if len(self.state_transitions) > 50:
            self.state_transitions = self.state_transitions[-50:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self.lock:
            recent_calls = list(self.call_history)
            
            if not recent_calls:
                return {
                    'name': self.name,
                    'state': self.state.value,
                    'total_calls': self.total_calls,
                    'total_failures': self.total_failures,
                    'total_rejections': self.total_rejections,
                    'failure_rate': 0,
                    'avg_response_time_ms': 0,
                    'time_until_retry': self._time_until_retry() if self.state == CircuitState.OPEN else 0
                }
            
            successful_calls = [c for c in recent_calls if c.success]
            response_times = [c.response_time_ms for c in recent_calls]
            
            return {
                'name': self.name,
                'state': self.state.value,
                'total_calls': self.total_calls,
                'total_failures': self.total_failures,
                'total_rejections': self.total_rejections,
                'failure_rate': (len(recent_calls) - len(successful_calls)) / len(recent_calls),
                'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
                'p95_response_time_ms': statistics.quantiles(response_times, n=20)[18] if len(response_times) > 1 else 0,
                'time_until_retry': self._time_until_retry() if self.state == CircuitState.OPEN else 0,
                'recent_state_transitions': self.state_transitions[-10:]  # Last 10 transitions
            }
    
    def reset(self) -> None:
        """Manually reset circuit breaker to closed state"""
        with self.lock:
            old_state = self.state
            self._transition_to_closed()
            logger.info(f"Circuit breaker '{self.name}' manually reset from {old_state.value}")


class RetryConfig:
    """Retry mechanism configuration"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: List[type] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            ConnectionError, 
            TimeoutError,
            asyncio.TimeoutError,
            OSError
        ]


class RetryMechanism:
    """
    Retry mechanism with exponential backoff and jitter
    """
    
    def __init__(self, name: str, config: RetryConfig = None):
        self.name = name
        self.config = config or RetryConfig()
        
        # Statistics
        self.total_attempts = 0
        self.total_retries = 0
        self.success_after_retry = 0
        
        logger.info(f"Retry mechanism '{name}' initialized with max_attempts={self.config.max_attempts}")
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry mechanism
        
        Args:
            func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: Last exception if all attempts fail
        """
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            self.total_attempts += 1
            
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                if attempt > 1:
                    self.success_after_retry += 1
                    logger.info(f"Retry '{self.name}': Success on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if exception is retryable
                if not self._is_retryable(e):
                    logger.debug(f"Retry '{self.name}': Non-retryable exception {type(e).__name__}")
                    raise e
                
                # Don't retry on last attempt
                if attempt == self.config.max_attempts:
                    logger.error(f"Retry '{self.name}': All {self.config.max_attempts} attempts failed")
                    break
                
                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_delay(attempt)
                self.total_retries += 1
                
                logger.warning(
                    f"Retry '{self.name}': Attempt {attempt} failed with {type(e).__name__}, "
                    f"retrying in {delay:.2f}s"
                )
                
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def _is_retryable(self, exception: Exception) -> bool:
        """Check if exception is retryable"""
        return any(isinstance(exception, exc_type) for exc_type in self.config.retryable_exceptions)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter"""
        # Exponential backoff
        delay = min(
            self.config.base_delay * (self.config.exponential_base ** (attempt - 1)),
            self.config.max_delay
        )
        
        # Add jitter to prevent thundering herd
        if self.config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry statistics"""
        return {
            'name': self.name,
            'total_attempts': self.total_attempts,
            'total_retries': self.total_retries,
            'success_after_retry': self.success_after_retry,
            'retry_rate': self.total_retries / max(1, self.total_attempts),
            'config': {
                'max_attempts': self.config.max_attempts,
                'base_delay': self.config.base_delay,
                'max_delay': self.config.max_delay
            }
        }


class BulkheadConfig:
    """Bulkhead pattern configuration"""
    
    def __init__(
        self,
        max_concurrent: int = 10,
        queue_size: int = 100,
        timeout_seconds: float = 30.0
    ):
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size
        self.timeout_seconds = timeout_seconds


class Bulkhead:
    """
    Bulkhead pattern implementation for resource isolation
    """
    
    def __init__(self, name: str, config: BulkheadConfig = None):
        self.name = name
        self.config = config or BulkheadConfig()
        
        # Semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        # Statistics
        self.active_requests = 0
        self.queued_requests = 0
        self.total_requests = 0
        self.rejected_requests = 0
        self.max_active_seen = 0
        
        self.lock = threading.RLock()
        
        logger.info(f"Bulkhead '{name}' initialized with max_concurrent={self.config.max_concurrent}")
    
    @asynccontextmanager
    async def acquire(self):
        """
        Acquire bulkhead resource with timeout
        
        Context manager for resource acquisition and cleanup
        """
        with self.lock:
            self.total_requests += 1
            
            # Check if we should reject (queue full)
            if self.queued_requests >= self.config.queue_size:
                self.rejected_requests += 1
                raise BulkheadRejectedException(
                    f"Bulkhead '{self.name}' queue full ({self.config.queue_size})"
                )
            
            self.queued_requests += 1
        
        try:
            # Wait for semaphore with timeout
            await asyncio.wait_for(
                self.semaphore.acquire(),
                timeout=self.config.timeout_seconds
            )
            
            with self.lock:
                self.active_requests += 1
                self.queued_requests -= 1
                self.max_active_seen = max(self.max_active_seen, self.active_requests)
            
            logger.debug(f"Bulkhead '{self.name}': Resource acquired ({self.active_requests} active)")
            
            try:
                yield
            finally:
                with self.lock:
                    self.active_requests -= 1
                self.semaphore.release()
                logger.debug(f"Bulkhead '{self.name}': Resource released ({self.active_requests} active)")
                
        except asyncio.TimeoutError:
            with self.lock:
                self.queued_requests -= 1
                self.rejected_requests += 1
            raise BulkheadTimeoutException(
                f"Bulkhead '{self.name}' timeout waiting for resource ({self.config.timeout_seconds}s)"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bulkhead statistics"""
        with self.lock:
            return {
                'name': self.name,
                'active_requests': self.active_requests,
                'queued_requests': self.queued_requests,
                'total_requests': self.total_requests,
                'rejected_requests': self.rejected_requests,
                'max_active_seen': self.max_active_seen,
                'rejection_rate': self.rejected_requests / max(1, self.total_requests),
                'utilization': self.active_requests / self.config.max_concurrent,
                'config': {
                    'max_concurrent': self.config.max_concurrent,
                    'queue_size': self.config.queue_size,
                    'timeout_seconds': self.config.timeout_seconds
                }
            }


class ResilienceManager:
    """
    Combined resilience patterns manager
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_mechanisms: Dict[str, RetryMechanism] = {}
        self.bulkheads: Dict[str, Bulkhead] = {}
        
        logger.info("Resilience manager initialized")
    
    def get_or_create_circuit_breaker(
        self, 
        name: str, 
        config: CircuitBreakerConfig = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name, config)
        return self.circuit_breakers[name]
    
    def get_or_create_retry_mechanism(
        self, 
        name: str, 
        config: RetryConfig = None
    ) -> RetryMechanism:
        """Get or create retry mechanism"""
        if name not in self.retry_mechanisms:
            self.retry_mechanisms[name] = RetryMechanism(name, config)
        return self.retry_mechanisms[name]
    
    def get_or_create_bulkhead(
        self, 
        name: str, 
        config: BulkheadConfig = None
    ) -> Bulkhead:
        """Get or create bulkhead"""
        if name not in self.bulkheads:
            self.bulkheads[name] = Bulkhead(name, config)
        return self.bulkheads[name]
    
    async def execute_with_resilience(
        self,
        service_name: str,
        func: Callable,
        *args,
        circuit_config: CircuitBreakerConfig = None,
        retry_config: RetryConfig = None,
        bulkhead_config: BulkheadConfig = None,
        **kwargs
    ) -> Any:
        """
        Execute function with all resilience patterns
        
        Args:
            service_name: Name of the service/resource
            func: Function to execute
            *args, **kwargs: Function arguments
            circuit_config: Circuit breaker configuration
            retry_config: Retry configuration  
            bulkhead_config: Bulkhead configuration
            
        Returns:
            Function result
        """
        # Get resilience components
        circuit_breaker = self.get_or_create_circuit_breaker(f"{service_name}_circuit", circuit_config)
        retry_mechanism = self.get_or_create_retry_mechanism(f"{service_name}_retry", retry_config)
        bulkhead = self.get_or_create_bulkhead(f"{service_name}_bulkhead", bulkhead_config)
        
        # Execute with bulkhead -> circuit breaker -> retry -> function
        async with bulkhead.acquire():
            return await retry_mechanism.execute(
                lambda: circuit_breaker.call(func, *args, **kwargs)
            )
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all resilience components"""
        return {
            'circuit_breakers': {name: cb.get_stats() for name, cb in self.circuit_breakers.items()},
            'retry_mechanisms': {name: rm.get_stats() for name, rm in self.retry_mechanisms.items()},
            'bulkheads': {name: bh.get_stats() for name, bh in self.bulkheads.items()},
            'summary': {
                'total_circuit_breakers': len(self.circuit_breakers),
                'total_retry_mechanisms': len(self.retry_mechanisms),
                'total_bulkheads': len(self.bulkheads),
                'open_circuits': len([cb for cb in self.circuit_breakers.values() if cb.state == CircuitState.OPEN])
            }
        }
    
    def reset_all_circuit_breakers(self) -> None:
        """Reset all circuit breakers"""
        for cb in self.circuit_breakers.values():
            cb.reset()
        logger.info("All circuit breakers reset")


# Custom exceptions
class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open"""
    pass


class BulkheadRejectedException(Exception):
    """Request rejected by bulkhead"""
    pass


class BulkheadTimeoutException(Exception):
    """Timeout waiting for bulkhead resource"""
    pass


# Global resilience manager instance
_resilience_manager = None


def get_resilience_manager() -> ResilienceManager:
    """Get or create global resilience manager"""
    global _resilience_manager
    if _resilience_manager is None:
        _resilience_manager = ResilienceManager()
    return _resilience_manager


# Convenience functions
async def with_circuit_breaker(service_name: str, func: Callable, *args, **kwargs) -> Any:
    """Execute function with circuit breaker protection"""
    manager = get_resilience_manager()
    circuit = manager.get_or_create_circuit_breaker(service_name)
    return await circuit.call(func, *args, **kwargs)


async def with_retry(service_name: str, func: Callable, *args, **kwargs) -> Any:
    """Execute function with retry mechanism"""
    manager = get_resilience_manager()
    retry = manager.get_or_create_retry_mechanism(service_name)
    return await retry.execute(func, *args, **kwargs)


async def with_bulkhead(service_name: str, func: Callable, *args, **kwargs) -> Any:
    """Execute function with bulkhead protection"""
    manager = get_resilience_manager()
    bulkhead = manager.get_or_create_bulkhead(service_name)
    async with bulkhead.acquire():
        return await func(*args, **kwargs)


async def with_full_resilience(service_name: str, func: Callable, *args, **kwargs) -> Any:
    """Execute function with all resilience patterns"""
    manager = get_resilience_manager()
    return await manager.execute_with_resilience(service_name, func, *args, **kwargs)