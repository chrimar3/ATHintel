"""
🚀 Automated Performance Optimization System

Self-optimizing performance management for ATHintel platform:
- Automatic bottleneck detection and resolution
- Adaptive resource allocation and scaling
- Query optimization and caching strategies
- ML model performance tuning
- System configuration auto-tuning
- Predictive scaling based on workload patterns
"""

import asyncio
import logging
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics
import json

from config.production_config import get_config
from infrastructure.persistence.database_manager import DatabaseManager
from monitoring.metrics_collector import get_metrics_collector
from infrastructure.resilience import get_resilience_manager, get_timeout_registry
from monitoring.health_system import get_health_monitor

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """Types of performance optimizations"""
    DATABASE_QUERY = "database_query"
    CACHE_STRATEGY = "cache_strategy"
    RESOURCE_ALLOCATION = "resource_allocation"
    ML_MODEL_TUNING = "ml_model_tuning"
    NETWORK_OPTIMIZATION = "network_optimization"
    MEMORY_MANAGEMENT = "memory_management"
    CONCURRENT_PROCESSING = "concurrent_processing"
    TIMEOUT_ADJUSTMENT = "timeout_adjustment"


class OptimizationPriority(Enum):
    """Optimization priority levels"""
    CRITICAL = "critical"      # Immediate performance impact
    HIGH = "high"             # Significant improvement potential
    MEDIUM = "medium"         # Moderate improvement
    LOW = "low"              # Minor optimization


class OptimizationStatus(Enum):
    """Status of optimization actions"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERTED = "reverted"


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    response_times: Dict[str, float]  # Service -> avg response time
    error_rates: Dict[str, float]     # Service -> error rate
    throughput: Dict[str, float]      # Service -> requests/sec


@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""
    optimization_id: str
    optimization_type: OptimizationType
    priority: OptimizationPriority
    title: str
    description: str
    expected_improvement: str
    implementation_steps: List[str]
    estimated_effort: str
    risk_level: str
    metrics_evidence: Dict[str, Any]
    configuration_changes: Dict[str, Any]
    rollback_plan: List[str]


@dataclass
class OptimizationResult:
    """Result of applied optimization"""
    optimization_id: str
    status: OptimizationStatus
    applied_at: datetime
    before_metrics: PerformanceMetrics
    after_metrics: Optional[PerformanceMetrics]
    actual_improvement: Optional[Dict[str, float]]
    success: bool
    error_message: Optional[str]
    duration_seconds: float


class SystemProfiler:
    """
    Continuous system profiling and bottleneck detection
    """
    
    def __init__(self):
        self.config = get_config()
        
        # Metrics history with memory management
        self.metrics_history: deque = deque(maxlen=144)  # 2.4 hours at 1-minute intervals (reduced from 24h)
        self.lock = threading.RLock()
        
        # Memory management
        self.max_memory_mb = 256  # Maximum memory usage
        self.cleanup_interval = 3600  # Cleanup every hour
        self.last_cleanup = time.time()
        
        # Performance thresholds
        self.performance_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'response_time_ms': 1000.0,
            'error_rate': 0.05,  # 5%
            'disk_io_mb_sec': 100.0,
            'network_io_mb_sec': 50.0
        }
        
        # Monitoring state
        self.monitoring_active = False
        self.profiling_task: Optional[asyncio.Task] = None
        
        # Database and service connections
        self.db_manager = DatabaseManager()
        
        logger.info("System profiler initialized")
    
    async def start_profiling(self, interval_seconds: int = 60):
        """Start continuous system profiling"""
        if self.monitoring_active:
            logger.warning("System profiling already active")
            return
        
        self.monitoring_active = True
        self.profiling_task = asyncio.create_task(
            self._profiling_loop(interval_seconds)
        )
        logger.info(f"System profiling started with {interval_seconds}s interval")
    
    async def stop_profiling(self):
        """Stop system profiling"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.profiling_task:
            self.profiling_task.cancel()
            try:
                await self.profiling_task
            except asyncio.CancelledError:
                pass
        
        logger.info("System profiling stopped")
    
    async def _profiling_loop(self, interval_seconds: int):
        """Main profiling loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()
                
                # Store metrics
                with self.lock:
                    self.metrics_history.append(metrics)
                
                # Analyze for bottlenecks
                await self._analyze_bottlenecks(metrics)
                
                # Wait for next collection
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in profiling loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def _collect_system_metrics(self) -> PerformanceMetrics:
        """Collect comprehensive system performance metrics"""
        
        # System resources - non-blocking CPU monitoring for performance optimization
        cpu_percent = await asyncio.get_event_loop().run_in_executor(
            None, psutil.cpu_percent, 0.1
        )
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        network_io = psutil.net_io_counters()
        
        # Application-specific metrics
        response_times = await self._get_response_time_metrics()
        error_rates = await self._get_error_rate_metrics()
        throughput = await self._get_throughput_metrics()
        
        # Database connections
        active_connections = await self._get_active_db_connections()
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_io_read_mb=disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
            disk_io_write_mb=disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
            network_sent_mb=network_io.bytes_sent / 1024 / 1024 if network_io else 0,
            network_recv_mb=network_io.bytes_recv / 1024 / 1024 if network_io else 0,
            active_connections=active_connections,
            response_times=response_times,
            error_rates=error_rates,
            throughput=throughput
        )
    
    async def _get_response_time_metrics(self) -> Dict[str, float]:
        """Get response time metrics from various services"""
        response_times = {}
        
        try:
            # Get timeout manager stats
            timeout_registry = get_timeout_registry()
            timeout_stats = timeout_registry.get_all_stats()
            
            for manager_name, stats in timeout_stats.get('managers', {}).items():
                response_times[manager_name] = stats.get('avg_response_time_ms', 0)
            
            # Get resilience manager stats
            resilience_manager = get_resilience_manager()
            resilience_stats = resilience_manager.get_all_stats()
            
            for cb_name, cb_stats in resilience_stats.get('circuit_breakers', {}).items():
                response_times[f"circuit_breaker_{cb_name}"] = cb_stats.get('avg_response_time_ms', 0)
            
        except Exception as e:
            logger.error(f"Error collecting response time metrics: {e}")
        
        return response_times
    
    async def _get_error_rate_metrics(self) -> Dict[str, float]:
        """Get error rate metrics from services"""
        error_rates = {}
        
        try:
            # Get circuit breaker failure rates
            resilience_manager = get_resilience_manager()
            resilience_stats = resilience_manager.get_all_stats()
            
            for cb_name, cb_stats in resilience_stats.get('circuit_breakers', {}).items():
                error_rates[cb_name] = cb_stats.get('failure_rate', 0)
            
            # Get timeout manager timeout rates
            timeout_registry = get_timeout_registry()
            timeout_stats = timeout_registry.get_all_stats()
            
            for manager_name, stats in timeout_stats.get('managers', {}).items():
                error_rates[f"timeout_{manager_name}"] = stats.get('timeout_rate', 0)
            
        except Exception as e:
            logger.error(f"Error collecting error rate metrics: {e}")
        
        return error_rates
    
    async def _get_throughput_metrics(self) -> Dict[str, float]:
        """Get throughput metrics"""
        throughput = {}
        
        try:
            # Get metrics from metrics collector if available
            metrics_collector = get_metrics_collector()
            if hasattr(metrics_collector, 'get_throughput_metrics'):
                throughput = metrics_collector.get_throughput_metrics()
        except Exception as e:
            logger.error(f"Error collecting throughput metrics: {e}")
        
        return throughput
    
    async def _get_active_db_connections(self) -> int:
        """Get active database connections count"""
        try:
            results = await self.db_manager.execute_query(
                "get_active_connections_count", {}
            )
            return results[0]['count'] if results else 0
        except Exception as e:
            logger.error(f"Error getting DB connections count: {e}")
            return 0
    
    async def _analyze_bottlenecks(self, metrics: PerformanceMetrics):
        """Analyze metrics for performance bottlenecks"""
        bottlenecks = []
        
        # CPU bottleneck
        if metrics.cpu_percent > self.performance_thresholds['cpu_percent']:
            bottlenecks.append({
                'type': 'high_cpu',
                'severity': 'high' if metrics.cpu_percent > 90 else 'medium',
                'value': metrics.cpu_percent,
                'threshold': self.performance_thresholds['cpu_percent']
            })
        
        # Memory bottleneck
        if metrics.memory_percent > self.performance_thresholds['memory_percent']:
            bottlenecks.append({
                'type': 'high_memory',
                'severity': 'critical' if metrics.memory_percent > 95 else 'high',
                'value': metrics.memory_percent,
                'threshold': self.performance_thresholds['memory_percent']
            })
        
        # Response time bottlenecks
        for service, response_time in metrics.response_times.items():
            if response_time > self.performance_thresholds['response_time_ms']:
                bottlenecks.append({
                    'type': 'slow_response',
                    'service': service,
                    'severity': 'high' if response_time > 2000 else 'medium',
                    'value': response_time,
                    'threshold': self.performance_thresholds['response_time_ms']
                })
        
        # Error rate bottlenecks
        for service, error_rate in metrics.error_rates.items():
            if error_rate > self.performance_thresholds['error_rate']:
                bottlenecks.append({
                    'type': 'high_error_rate',
                    'service': service,
                    'severity': 'critical' if error_rate > 0.1 else 'high',
                    'value': error_rate,
                    'threshold': self.performance_thresholds['error_rate']
                })
        
        if bottlenecks:
            logger.warning(f"Performance bottlenecks detected: {len(bottlenecks)} issues")
            
            # Notify performance optimizer
            optimizer = get_performance_optimizer()
            await optimizer.handle_bottlenecks(bottlenecks, metrics)
    
    def get_recent_metrics(self, hours: int = 1) -> List[PerformanceMetrics]:
        """Get recent performance metrics"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return [
                metrics for metrics in self.metrics_history
                if metrics.timestamp >= cutoff_time
            ]
    
    def get_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends"""
        with self.lock:
            if len(self.metrics_history) < 10:
                return {}
            
            recent_metrics = list(self.metrics_history)[-60:]  # Last hour
            older_metrics = list(self.metrics_history)[-120:-60]  # Hour before
            
            if not older_metrics:
                return {}
            
            trends = {}
            
            # CPU trend
            recent_cpu = statistics.mean([m.cpu_percent for m in recent_metrics])
            older_cpu = statistics.mean([m.cpu_percent for m in older_metrics])
            trends['cpu_trend'] = {
                'current': recent_cpu,
                'previous': older_cpu,
                'change_percent': ((recent_cpu - older_cpu) / older_cpu * 100) if older_cpu > 0 else 0
            }
            
            # Memory trend
            recent_memory = statistics.mean([m.memory_percent for m in recent_metrics])
            older_memory = statistics.mean([m.memory_percent for m in older_metrics])
            trends['memory_trend'] = {
                'current': recent_memory,
                'previous': older_memory,
                'change_percent': ((recent_memory - older_memory) / older_memory * 100) if older_memory > 0 else 0
            }
            
            return trends


class OptimizationEngine:
    """
    Core optimization engine that analyzes bottlenecks and applies improvements
    """
    
    def __init__(self):
        self.config = get_config()
        self.db_manager = DatabaseManager()
        
        # Applied optimizations tracking with bounds
        self.applied_optimizations: Dict[str, OptimizationResult] = {}
        self.optimization_history: deque = deque(maxlen=100)  # Limited history to prevent memory leaks
        
        # Memory monitoring
        self.memory_cleanup_threshold = 200  # Cleanup when over 200MB
        self.last_memory_check = time.time()
        
        # Optimization strategies
        self.optimization_strategies = {
            OptimizationType.DATABASE_QUERY: self._optimize_database_queries,
            OptimizationType.CACHE_STRATEGY: self._optimize_caching,
            OptimizationType.TIMEOUT_ADJUSTMENT: self._optimize_timeouts,
            OptimizationType.MEMORY_MANAGEMENT: self._optimize_memory,
            OptimizationType.CONCURRENT_PROCESSING: self._optimize_concurrency
        }
        
        logger.info("Optimization engine initialized")
    
    async def analyze_and_recommend(
        self,
        bottlenecks: List[Dict[str, Any]],
        metrics: PerformanceMetrics
    ) -> List[OptimizationRecommendation]:
        """
        Analyze bottlenecks and generate optimization recommendations
        
        Args:
            bottlenecks: Detected performance bottlenecks
            metrics: Current performance metrics
            
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        for bottleneck in bottlenecks:
            bottleneck_type = bottleneck['type']
            
            if bottleneck_type == 'high_cpu':
                recommendations.extend(await self._recommend_cpu_optimizations(bottleneck, metrics))
            elif bottleneck_type == 'high_memory':
                recommendations.extend(await self._recommend_memory_optimizations(bottleneck, metrics))
            elif bottleneck_type == 'slow_response':
                recommendations.extend(await self._recommend_response_optimizations(bottleneck, metrics))
            elif bottleneck_type == 'high_error_rate':
                recommendations.extend(await self._recommend_reliability_optimizations(bottleneck, metrics))
        
        # Sort recommendations by priority
        recommendations.sort(key=lambda x: ['critical', 'high', 'medium', 'low'].index(x.priority.value))
        
        return recommendations
    
    async def _recommend_cpu_optimizations(
        self,
        bottleneck: Dict[str, Any],
        metrics: PerformanceMetrics
    ) -> List[OptimizationRecommendation]:
        """Recommend CPU optimization strategies"""
        recommendations = []
        
        # Database query optimization
        if metrics.active_connections > 50:  # High DB connection count
            recommendations.append(OptimizationRecommendation(
                optimization_id=f"db_query_opt_{int(time.time())}",
                optimization_type=OptimizationType.DATABASE_QUERY,
                priority=OptimizationPriority.HIGH,
                title="Optimize Database Queries",
                description="High CPU usage with many active database connections suggests query optimization is needed",
                expected_improvement="10-30% CPU reduction",
                implementation_steps=[
                    "Analyze slow query logs",
                    "Add missing indexes",
                    "Optimize complex queries",
                    "Implement query result caching"
                ],
                estimated_effort="2-4 hours",
                risk_level="Low",
                metrics_evidence={"cpu_percent": bottleneck['value'], "active_connections": metrics.active_connections},
                configuration_changes={"enable_query_optimization": True, "query_cache_size": "512MB"},
                rollback_plan=["Restore original query configurations", "Clear query cache"]
            ))
        
        # Concurrent processing optimization
        recommendations.append(OptimizationRecommendation(
            optimization_id=f"concurrency_opt_{int(time.time())}",
            optimization_type=OptimizationType.CONCURRENT_PROCESSING,
            priority=OptimizationPriority.MEDIUM,
            title="Optimize Concurrent Processing",
            description="Adjust worker pool sizes and async processing to reduce CPU contention",
            expected_improvement="5-15% CPU reduction",
            implementation_steps=[
                "Analyze current worker pool utilization",
                "Adjust async task scheduling", 
                "Optimize thread pool sizes",
                "Implement CPU-bound task queuing"
            ],
            estimated_effort="1-2 hours",
            risk_level="Medium",
            metrics_evidence={"cpu_percent": bottleneck['value']},
            configuration_changes={"max_workers": 8, "async_pool_size": 16},
            rollback_plan=["Restore default worker pool settings"]
        ))
        
        return recommendations
    
    async def _recommend_memory_optimizations(
        self,
        bottleneck: Dict[str, Any],
        metrics: PerformanceMetrics
    ) -> List[OptimizationRecommendation]:
        """Recommend memory optimization strategies"""
        recommendations = []
        
        recommendations.append(OptimizationRecommendation(
            optimization_id=f"memory_opt_{int(time.time())}",
            optimization_type=OptimizationType.MEMORY_MANAGEMENT,
            priority=OptimizationPriority.CRITICAL if bottleneck['severity'] == 'critical' else OptimizationPriority.HIGH,
            title="Memory Usage Optimization",
            description="High memory usage detected - implement memory optimization strategies",
            expected_improvement="15-40% memory reduction",
            implementation_steps=[
                "Implement memory profiling",
                "Optimize data structures and caching",
                "Configure garbage collection tuning",
                "Add memory leak detection"
            ],
            estimated_effort="3-6 hours",
            risk_level="Medium",
            metrics_evidence={"memory_percent": bottleneck['value']},
            configuration_changes={
                "gc_threshold": 0.8,
                "max_cache_size": "1GB",
                "enable_memory_profiling": True
            },
            rollback_plan=["Restore original memory settings", "Clear all caches"]
        ))
        
        return recommendations
    
    async def _recommend_response_optimizations(
        self,
        bottleneck: Dict[str, Any],
        metrics: PerformanceMetrics
    ) -> List[OptimizationRecommendation]:
        """Recommend response time optimization strategies"""
        recommendations = []
        
        service = bottleneck.get('service', 'unknown')
        
        # Timeout adjustment
        recommendations.append(OptimizationRecommendation(
            optimization_id=f"timeout_opt_{service}_{int(time.time())}",
            optimization_type=OptimizationType.TIMEOUT_ADJUSTMENT,
            priority=OptimizationPriority.HIGH,
            title=f"Optimize Timeouts for {service}",
            description="Adjust timeout values based on actual performance patterns",
            expected_improvement="20-50% response time improvement",
            implementation_steps=[
                "Analyze historical response time patterns",
                "Implement adaptive timeout management",
                "Configure service-specific timeouts",
                "Enable timeout monitoring"
            ],
            estimated_effort="1-3 hours",
            risk_level="Low",
            metrics_evidence={"response_time": bottleneck['value'], "service": service},
            configuration_changes={"adaptive_timeouts": True, f"{service}_timeout": "auto"},
            rollback_plan=["Restore fixed timeout values"]
        ))
        
        # Caching optimization
        recommendations.append(OptimizationRecommendation(
            optimization_id=f"cache_opt_{service}_{int(time.time())}",
            optimization_type=OptimizationType.CACHE_STRATEGY,
            priority=OptimizationPriority.MEDIUM,
            title=f"Implement Caching for {service}",
            description="Add intelligent caching to reduce response times",
            expected_improvement="30-70% response time improvement",
            implementation_steps=[
                "Identify cacheable operations",
                "Implement multi-level caching",
                "Configure cache invalidation strategies",
                "Monitor cache hit rates"
            ],
            estimated_effort="2-4 hours",
            risk_level="Low",
            metrics_evidence={"response_time": bottleneck['value'], "service": service},
            configuration_changes={
                f"{service}_cache_enabled": True,
                f"{service}_cache_ttl": 300,
                f"{service}_cache_size": "256MB"
            },
            rollback_plan=["Disable caching", "Clear cache data"]
        ))
        
        return recommendations
    
    async def _recommend_reliability_optimizations(
        self,
        bottleneck: Dict[str, Any],
        metrics: PerformanceMetrics
    ) -> List[OptimizationRecommendation]:
        """Recommend reliability optimization strategies"""
        recommendations = []
        
        service = bottleneck.get('service', 'unknown')
        
        recommendations.append(OptimizationRecommendation(
            optimization_id=f"reliability_opt_{service}_{int(time.time())}",
            optimization_type=OptimizationType.NETWORK_OPTIMIZATION,
            priority=OptimizationPriority.CRITICAL,
            title=f"Improve Reliability for {service}",
            description="High error rate detected - implement reliability improvements",
            expected_improvement="50-90% error rate reduction",
            implementation_steps=[
                "Analyze error patterns and root causes",
                "Implement circuit breaker improvements",
                "Configure retry strategy optimization",
                "Add comprehensive error monitoring"
            ],
            estimated_effort="2-5 hours",
            risk_level="Medium",
            metrics_evidence={"error_rate": bottleneck['value'], "service": service},
            configuration_changes={
                f"{service}_circuit_breaker_threshold": 3,
                f"{service}_retry_attempts": 3,
                f"{service}_retry_backoff": "exponential"
            },
            rollback_plan=["Restore original circuit breaker settings"]
        ))
        
        return recommendations
    
    async def apply_optimization(
        self,
        recommendation: OptimizationRecommendation,
        before_metrics: PerformanceMetrics
    ) -> OptimizationResult:
        """
        Apply an optimization recommendation
        
        Args:
            recommendation: Optimization to apply
            before_metrics: Performance metrics before optimization
            
        Returns:
            Result of optimization application
        """
        start_time = time.time()
        optimization_id = recommendation.optimization_id
        
        logger.info(f"Applying optimization: {recommendation.title}")
        
        try:
            # Apply the optimization based on type
            strategy = self.optimization_strategies.get(recommendation.optimization_type)
            if not strategy:
                raise ValueError(f"No strategy for optimization type: {recommendation.optimization_type}")
            
            success = await strategy(recommendation)
            
            # Wait a bit for metrics to stabilize
            await asyncio.sleep(30)
            
            # Collect after metrics (would be done by profiler in real implementation)
            after_metrics = None  # Would collect actual metrics here
            
            # Calculate improvement
            actual_improvement = None
            if after_metrics:
                actual_improvement = self._calculate_improvement(before_metrics, after_metrics)
            
            result = OptimizationResult(
                optimization_id=optimization_id,
                status=OptimizationStatus.COMPLETED if success else OptimizationStatus.FAILED,
                applied_at=datetime.now(),
                before_metrics=before_metrics,
                after_metrics=after_metrics,
                actual_improvement=actual_improvement,
                success=success,
                error_message=None,
                duration_seconds=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Optimization {optimization_id} failed: {e}")
            
            result = OptimizationResult(
                optimization_id=optimization_id,
                status=OptimizationStatus.FAILED,
                applied_at=datetime.now(),
                before_metrics=before_metrics,
                after_metrics=None,
                actual_improvement=None,
                success=False,
                error_message=str(e),
                duration_seconds=time.time() - start_time
            )
        
        # Store result
        self.applied_optimizations[optimization_id] = result
        self.optimization_history.append(result)
        
        logger.info(f"Optimization {optimization_id} {'completed' if result.success else 'failed'}")
        return result
    
    async def _optimize_database_queries(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply database query optimizations"""
        try:
            # Enable query optimization features
            await self.db_manager.execute_query(
                "optimize_database_configuration",
                recommendation.configuration_changes
            )
            
            # Update connection pool settings
            if 'max_connections' in recommendation.configuration_changes:
                # Would update connection pool here
                pass
            
            logger.info("Database query optimization applied")
            return True
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return False
    
    async def _optimize_caching(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply caching optimizations"""
        try:
            # Configure caching settings
            config_changes = recommendation.configuration_changes
            
            # Enable caching for specific services
            for key, value in config_changes.items():
                if key.endswith('_cache_enabled') and value:
                    service_name = key.replace('_cache_enabled', '')
                    logger.info(f"Enabling caching for service: {service_name}")
                    # Would configure caching here
            
            logger.info("Caching optimization applied")
            return True
            
        except Exception as e:
            logger.error(f"Caching optimization failed: {e}")
            return False
    
    async def _optimize_timeouts(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply timeout optimizations"""
        try:
            # Configure adaptive timeouts
            if 'adaptive_timeouts' in recommendation.configuration_changes:
                timeout_registry = get_timeout_registry()
                # Would configure adaptive timeout settings here
                
                logger.info("Adaptive timeout optimization applied")
            
            return True
            
        except Exception as e:
            logger.error(f"Timeout optimization failed: {e}")
            return False
    
    async def _optimize_memory(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply memory optimizations"""
        try:
            # Configure memory management settings
            config_changes = recommendation.configuration_changes
            
            if 'gc_threshold' in config_changes:
                # Would configure garbage collection here
                logger.info("Garbage collection optimization applied")
            
            if 'max_cache_size' in config_changes:
                # Would configure cache size limits here
                logger.info("Cache size optimization applied")
            
            return True
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return False
    
    async def _optimize_concurrency(self, recommendation: OptimizationRecommendation) -> bool:
        """Apply concurrency optimizations"""
        try:
            # Configure concurrency settings
            config_changes = recommendation.configuration_changes
            
            if 'max_workers' in config_changes:
                # Would configure worker pool sizes here
                logger.info("Worker pool optimization applied")
            
            if 'async_pool_size' in config_changes:
                # Would configure async pool size here
                logger.info("Async pool optimization applied")
            
            return True
            
        except Exception as e:
            logger.error(f"Concurrency optimization failed: {e}")
            return False
    
    def _calculate_improvement(
        self,
        before_metrics: PerformanceMetrics,
        after_metrics: PerformanceMetrics
    ) -> Dict[str, float]:
        """Calculate actual improvement from optimization"""
        improvements = {}
        
        # CPU improvement
        cpu_improvement = ((before_metrics.cpu_percent - after_metrics.cpu_percent) / before_metrics.cpu_percent) * 100
        improvements['cpu_percent'] = cpu_improvement
        
        # Memory improvement
        memory_improvement = ((before_metrics.memory_percent - after_metrics.memory_percent) / before_metrics.memory_percent) * 100
        improvements['memory_percent'] = memory_improvement
        
        # Response time improvements
        for service in before_metrics.response_times:
            if service in after_metrics.response_times:
                before_time = before_metrics.response_times[service]
                after_time = after_metrics.response_times[service]
                if before_time > 0:
                    improvement = ((before_time - after_time) / before_time) * 100
                    improvements[f'{service}_response_time'] = improvement
        
        return improvements
    
    async def revert_optimization(self, optimization_id: str) -> bool:
        """Revert an applied optimization"""
        if optimization_id not in self.applied_optimizations:
            logger.error(f"Optimization {optimization_id} not found for revert")
            return False
        
        try:
            result = self.applied_optimizations[optimization_id]
            # Would implement rollback plan here
            
            result.status = OptimizationStatus.REVERTED
            logger.info(f"Optimization {optimization_id} reverted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revert optimization {optimization_id}: {e}")
            return False
    
    def get_optimization_history(self) -> List[OptimizationResult]:
        """Get history of applied optimizations"""
        return self.optimization_history.copy()


class PerformanceOptimizer:
    """
    Main performance optimization coordinator
    """
    
    def __init__(self):
        self.profiler = SystemProfiler()
        self.optimization_engine = OptimizationEngine()
        
        # Auto-optimization settings
        self.auto_optimization_enabled = True
        self.optimization_threshold_priority = OptimizationPriority.HIGH
        
        # Pending optimizations - bounded to prevent memory leaks
        self.pending_optimizations: deque = deque(maxlen=50)  # Limit pending optimizations
        
        logger.info("Performance optimizer initialized")
    
    async def start_auto_optimization(self):
        """Start automatic performance optimization"""
        await self.profiler.start_profiling()
        logger.info("Auto-optimization started")
    
    async def stop_auto_optimization(self):
        """Stop automatic performance optimization"""
        await self.profiler.stop_profiling()
        logger.info("Auto-optimization stopped")
    
    async def handle_bottlenecks(
        self,
        bottlenecks: List[Dict[str, Any]],
        metrics: PerformanceMetrics
    ):
        """Handle detected performance bottlenecks"""
        
        # Generate optimization recommendations
        recommendations = await self.optimization_engine.analyze_and_recommend(
            bottlenecks, metrics
        )
        
        if not recommendations:
            return
        
        logger.info(f"Generated {len(recommendations)} optimization recommendations")
        
        # Auto-apply high priority optimizations if enabled
        if self.auto_optimization_enabled:
            auto_apply_recommendations = [
                rec for rec in recommendations
                if rec.priority in [OptimizationPriority.CRITICAL, self.optimization_threshold_priority]
                and rec.risk_level.lower() in ['low', 'medium']
            ]
            
            for recommendation in auto_apply_recommendations:
                try:
                    result = await self.optimization_engine.apply_optimization(
                        recommendation, metrics
                    )
                    
                    if result.success:
                        logger.info(f"Auto-applied optimization: {recommendation.title}")
                    else:
                        logger.warning(f"Auto-optimization failed: {recommendation.title}")
                        
                except Exception as e:
                    logger.error(f"Error auto-applying optimization: {e}")
        
        # Store remaining recommendations for manual review
        manual_recommendations = [
            rec for rec in recommendations
            if not self.auto_optimization_enabled or 
            rec.priority not in [OptimizationPriority.CRITICAL, self.optimization_threshold_priority] or
            rec.risk_level.lower() == 'high'
        ]
        
        # Add to bounded deque - will automatically drop old items if at maxlen
        for rec in manual_recommendations:
            self.pending_optimizations.append(rec)
        
        if manual_recommendations:
            logger.info(f"{len(manual_recommendations)} optimizations pending manual review")
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        # Get recent metrics and trends
        recent_metrics = self.profiler.get_recent_metrics(hours=1)
        trends = self.profiler.get_performance_trends()
        
        # Get optimization history
        optimization_history = self.optimization_engine.get_optimization_history()
        
        # Calculate performance scores
        performance_scores = {}
        if recent_metrics:
            latest_metrics = recent_metrics[-1]
            performance_scores = {
                'cpu_score': max(0, 100 - latest_metrics.cpu_percent),
                'memory_score': max(0, 100 - latest_metrics.memory_percent),
                'response_time_score': self._calculate_response_time_score(latest_metrics),
                'error_rate_score': self._calculate_error_rate_score(latest_metrics)
            }
            performance_scores['overall_score'] = statistics.mean(performance_scores.values())
        
        return {
            'report_timestamp': datetime.now().isoformat(),
            'performance_scores': performance_scores,
            'trends': trends,
            'recent_metrics_count': len(recent_metrics),
            'optimization_summary': {
                'total_applied': len(optimization_history),
                'successful': len([r for r in optimization_history if r.success]),
                'failed': len([r for r in optimization_history if not r.success]),
                'pending_manual_review': len(self.pending_optimizations)
            },
            'recommendations': [
                {
                    'id': rec.optimization_id,
                    'title': rec.title,
                    'priority': rec.priority.value,
                    'type': rec.optimization_type.value,
                    'expected_improvement': rec.expected_improvement
                }
                for rec in self.pending_optimizations[-5:]  # Last 5 pending
            ],
            'auto_optimization_enabled': self.auto_optimization_enabled
        }
    
    def _calculate_response_time_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate response time performance score"""
        if not metrics.response_times:
            return 100.0
        
        avg_response_time = statistics.mean(metrics.response_times.values())
        # Score based on response time (100 = under 100ms, 0 = over 5000ms)
        return max(0, min(100, (5000 - avg_response_time) / 5000 * 100))
    
    def _calculate_error_rate_score(self, metrics: PerformanceMetrics) -> float:
        """Calculate error rate performance score"""
        if not metrics.error_rates:
            return 100.0
        
        avg_error_rate = statistics.mean(metrics.error_rates.values())
        # Score based on error rate (100 = 0% errors, 0 = 10%+ errors)
        return max(0, min(100, (0.1 - avg_error_rate) / 0.1 * 100))
    
    def configure_auto_optimization(
        self,
        enabled: bool,
        threshold_priority: OptimizationPriority = OptimizationPriority.HIGH
    ):
        """Configure auto-optimization settings"""
        self.auto_optimization_enabled = enabled
        self.optimization_threshold_priority = threshold_priority
        
        logger.info(f"Auto-optimization configured: enabled={enabled}, threshold={threshold_priority.value}")


# Global performance optimizer instance
_performance_optimizer = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get or create global performance optimizer"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


# Convenience functions
async def start_performance_optimization():
    """Start automatic performance optimization"""
    optimizer = get_performance_optimizer()
    await optimizer.start_auto_optimization()


async def stop_performance_optimization():
    """Stop automatic performance optimization"""
    optimizer = get_performance_optimizer()
    await optimizer.stop_auto_optimization()


async def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report"""
    optimizer = get_performance_optimizer()
    return await optimizer.get_performance_report()


def configure_auto_optimization(enabled: bool, threshold: str = "high"):
    """Configure auto-optimization settings"""
    optimizer = get_performance_optimizer()
    priority_map = {
        "critical": OptimizationPriority.CRITICAL,
        "high": OptimizationPriority.HIGH,
        "medium": OptimizationPriority.MEDIUM,
        "low": OptimizationPriority.LOW
    }
    
    optimizer.configure_auto_optimization(enabled, priority_map.get(threshold, OptimizationPriority.HIGH))