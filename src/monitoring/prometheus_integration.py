"""
📊 Prometheus/Grafana Integration

Enterprise monitoring integration with Prometheus metrics collection and Grafana dashboards:
- Custom metrics for energy assessment platform
- System performance and business metrics
- Health monitoring integration
- Grafana dashboard provisioning
- Alert rules for critical conditions
"""

import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import threading
from collections import defaultdict, deque

# Prometheus client
try:
    from prometheus_client import (
        Counter, Gauge, Histogram, Summary, Info,
        CollectorRegistry, REGISTRY, generate_latest,
        multiprocess, values
    )
    from prometheus_client.exposition import MetricsHandler
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("Prometheus client not available, metrics will use mock implementation")

from config.production_config import get_config
from monitoring.health_system import get_health_monitor
from infrastructure.resilience import get_resilience_manager, get_timeout_registry

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge" 
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    INFO = "info"


@dataclass
class MetricDefinition:
    """Metric definition for registration"""
    name: str
    metric_type: MetricType
    description: str
    labels: List[str] = None
    buckets: List[float] = None  # For histograms
    objectives: Dict[float, float] = None  # For summaries


class PrometheusMetricsCollector:
    """
    Prometheus metrics collector for ATHintel platform
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or REGISTRY
        self.config = get_config()
        
        # Metric storage
        self.metrics: Dict[str, Any] = {}
        self.custom_collectors: List[Callable] = []
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Initialize core metrics
        if PROMETHEUS_AVAILABLE:
            self._initialize_core_metrics()
        else:
            self._initialize_mock_metrics()
        
        logger.info("Prometheus metrics collector initialized")
    
    def _initialize_core_metrics(self):
        """Initialize core platform metrics"""
        
        # System metrics
        self.metrics['system_uptime'] = Gauge(
            'athintel_system_uptime_seconds',
            'System uptime in seconds',
            registry=self.registry
        )
        
        self.metrics['system_info'] = Info(
            'athintel_system_info',
            'System information',
            registry=self.registry
        )
        
        # Energy assessment metrics
        self.metrics['assessments_total'] = Counter(
            'athintel_assessments_total',
            'Total number of energy assessments performed',
            ['status', 'energy_class'],
            registry=self.registry
        )
        
        self.metrics['assessment_duration'] = Histogram(
            'athintel_assessment_duration_seconds',
            'Energy assessment processing duration',
            ['assessment_type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry
        )
        
        self.metrics['assessment_score'] = Histogram(
            'athintel_assessment_score_points',
            'Energy assessment scores',
            ['energy_class'],
            buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            registry=self.registry
        )
        
        # Property metrics
        self.metrics['properties_processed'] = Counter(
            'athintel_properties_processed_total',
            'Total properties processed',
            ['region', 'property_type'],
            registry=self.registry
        )
        
        self.metrics['property_value'] = Histogram(
            'athintel_property_value_euros',
            'Property valuations in euros',
            ['region', 'energy_class'],
            buckets=[50000, 100000, 150000, 200000, 300000, 500000, 750000, 1000000, 2000000],
            registry=self.registry
        )
        
        # ML model metrics
        self.metrics['ml_predictions_total'] = Counter(
            'athintel_ml_predictions_total',
            'Total ML predictions made',
            ['model_type', 'status'],
            registry=self.registry
        )
        
        self.metrics['ml_model_accuracy'] = Gauge(
            'athintel_ml_model_accuracy_ratio',
            'ML model accuracy',
            ['model_name'],
            registry=self.registry
        )
        
        self.metrics['ml_prediction_confidence'] = Histogram(
            'athintel_ml_prediction_confidence',
            'ML prediction confidence scores',
            ['model_type'],
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            registry=self.registry
        )
        
        # Database metrics
        self.metrics['database_connections'] = Gauge(
            'athintel_database_connections_active',
            'Active database connections',
            registry=self.registry
        )
        
        self.metrics['database_query_duration'] = Histogram(
            'athintel_database_query_duration_seconds',
            'Database query execution time',
            ['query_type'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=self.registry
        )
        
        self.metrics['database_errors'] = Counter(
            'athintel_database_errors_total',
            'Database errors',
            ['error_type'],
            registry=self.registry
        )
        
        # Cache metrics
        self.metrics['cache_operations'] = Counter(
            'athintel_cache_operations_total',
            'Cache operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.metrics['cache_hit_ratio'] = Gauge(
            'athintel_cache_hit_ratio',
            'Cache hit ratio',
            ['cache_type'],
            registry=self.registry
        )
        
        # API metrics
        self.metrics['api_requests'] = Counter(
            'athintel_api_requests_total',
            'API requests',
            ['endpoint', 'method', 'status_code'],
            registry=self.registry
        )
        
        self.metrics['api_response_time'] = Histogram(
            'athintel_api_response_time_seconds',
            'API response time',
            ['endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        # External service metrics
        self.metrics['external_service_calls'] = Counter(
            'athintel_external_service_calls_total',
            'External service calls',
            ['service', 'status'],
            registry=self.registry
        )
        
        self.metrics['external_service_response_time'] = Histogram(
            'athintel_external_service_response_time_seconds',
            'External service response time',
            ['service'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry
        )
        
        # Business metrics
        self.metrics['energy_savings_estimated'] = Counter(
            'athintel_energy_savings_estimated_kwh',
            'Total estimated energy savings in kWh',
            ['region', 'intervention_type'],
            registry=self.registry
        )
        
        self.metrics['subsidies_identified'] = Counter(
            'athintel_subsidies_identified_total',
            'Government subsidies identified',
            ['program_type', 'region'],
            registry=self.registry
        )
        
        self.metrics['roi_calculated'] = Histogram(
            'athintel_roi_calculated_years',
            'Calculated ROI in years',
            ['intervention_type'],
            buckets=[1, 2, 3, 5, 7, 10, 15, 20, 25, 30],
            registry=self.registry
        )
        
        # Health metrics
        self.metrics['health_check_duration'] = Histogram(
            'athintel_health_check_duration_seconds',
            'Health check duration',
            ['check_name'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
            registry=self.registry
        )
        
        self.metrics['health_check_status'] = Gauge(
            'athintel_health_check_status',
            'Health check status (1=healthy, 0=unhealthy)',
            ['check_name'],
            registry=self.registry
        )
        
        # Initialize system info
        self.metrics['system_info'].info({
            'version': '2.0.0',
            'environment': self.config.environment,
            'python_version': '3.11+',
            'start_time': datetime.now().isoformat()
        })
    
    def _initialize_mock_metrics(self):
        """Initialize mock metrics when Prometheus is not available"""
        logger.warning("Using mock metrics - Prometheus client not available")
        
        class MockMetric:
            def __init__(self, name):
                self.name = name
            
            def inc(self, amount=1, **labels):
                pass
            
            def set(self, value, **labels):
                pass
            
            def observe(self, value, **labels):
                pass
            
            def info(self, value):
                pass
            
            def labels(self, **labels):
                return self
        
        # Create mock metrics with same names
        metric_names = [
            'system_uptime', 'system_info', 'assessments_total', 'assessment_duration',
            'assessment_score', 'properties_processed', 'property_value',
            'ml_predictions_total', 'ml_model_accuracy', 'ml_prediction_confidence',
            'database_connections', 'database_query_duration', 'database_errors',
            'cache_operations', 'cache_hit_ratio', 'api_requests', 'api_response_time',
            'external_service_calls', 'external_service_response_time',
            'energy_savings_estimated', 'subsidies_identified', 'roi_calculated',
            'health_check_duration', 'health_check_status'
        ]
        
        for name in metric_names:
            self.metrics[name] = MockMetric(name)
    
    def record_assessment(
        self,
        duration_seconds: float,
        score: float,
        energy_class: str,
        status: str = "completed",
        assessment_type: str = "full"
    ):
        """Record energy assessment metrics"""
        with self.lock:
            self.metrics['assessments_total'].labels(
                status=status,
                energy_class=energy_class
            ).inc()
            
            self.metrics['assessment_duration'].labels(
                assessment_type=assessment_type
            ).observe(duration_seconds)
            
            self.metrics['assessment_score'].labels(
                energy_class=energy_class
            ).observe(score)
    
    def record_property(
        self,
        region: str,
        property_type: str,
        value_euros: float,
        energy_class: str
    ):
        """Record property processing metrics"""
        with self.lock:
            self.metrics['properties_processed'].labels(
                region=region,
                property_type=property_type
            ).inc()
            
            self.metrics['property_value'].labels(
                region=region,
                energy_class=energy_class
            ).observe(value_euros)
    
    def record_ml_prediction(
        self,
        model_type: str,
        confidence: float,
        status: str = "success"
    ):
        """Record ML prediction metrics"""
        with self.lock:
            self.metrics['ml_predictions_total'].labels(
                model_type=model_type,
                status=status
            ).inc()
            
            self.metrics['ml_prediction_confidence'].labels(
                model_type=model_type
            ).observe(confidence)
    
    def record_database_operation(
        self,
        query_type: str,
        duration_seconds: float,
        error_type: Optional[str] = None
    ):
        """Record database operation metrics"""
        with self.lock:
            self.metrics['database_query_duration'].labels(
                query_type=query_type
            ).observe(duration_seconds)
            
            if error_type:
                self.metrics['database_errors'].labels(
                    error_type=error_type
                ).inc()
    
    def record_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_seconds: float
    ):
        """Record API request metrics"""
        with self.lock:
            self.metrics['api_requests'].labels(
                endpoint=endpoint,
                method=method,
                status_code=str(status_code)
            ).inc()
            
            self.metrics['api_response_time'].labels(
                endpoint=endpoint
            ).observe(response_time_seconds)
    
    def record_external_service_call(
        self,
        service: str,
        response_time_seconds: float,
        status: str = "success"
    ):
        """Record external service call metrics"""
        with self.lock:
            self.metrics['external_service_calls'].labels(
                service=service,
                status=status
            ).inc()
            
            self.metrics['external_service_response_time'].labels(
                service=service
            ).observe(response_time_seconds)
    
    def record_business_metric(
        self,
        metric_type: str,
        value: float,
        **labels
    ):
        """Record business metrics"""
        with self.lock:
            if metric_type == "energy_savings":
                self.metrics['energy_savings_estimated'].labels(
                    region=labels.get('region', 'unknown'),
                    intervention_type=labels.get('intervention_type', 'unknown')
                ).inc(value)
            
            elif metric_type == "subsidy_identified":
                self.metrics['subsidies_identified'].labels(
                    program_type=labels.get('program_type', 'unknown'),
                    region=labels.get('region', 'unknown')
                ).inc()
            
            elif metric_type == "roi_calculated":
                self.metrics['roi_calculated'].labels(
                    intervention_type=labels.get('intervention_type', 'unknown')
                ).observe(value)
    
    def update_gauge(self, metric_name: str, value: float, **labels):
        """Update gauge metric"""
        with self.lock:
            if metric_name in self.metrics:
                if labels:
                    self.metrics[metric_name].labels(**labels).set(value)
                else:
                    self.metrics[metric_name].set(value)
    
    def add_custom_collector(self, collector_func: Callable):
        """Add custom metrics collector function"""
        self.custom_collectors.append(collector_func)
        logger.info(f"Added custom metrics collector: {collector_func.__name__}")
    
    async def collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # Update system uptime
            uptime = time.time() - self._get_system_start_time()
            self.metrics['system_uptime'].set(uptime)
            
            # Collect health metrics
            await self._collect_health_metrics()
            
            # Collect resilience metrics
            await self._collect_resilience_metrics()
            
            # Run custom collectors
            for collector in self.custom_collectors:
                try:
                    if asyncio.iscoroutinefunction(collector):
                        await collector(self)
                    else:
                        collector(self)
                except Exception as e:
                    logger.error(f"Custom collector failed: {e}")
        
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
    
    async def _collect_health_metrics(self):
        """Collect health monitoring metrics"""
        try:
            health_monitor = await get_health_monitor()
            health_summary = await health_monitor.get_system_health_summary()
            
            # Record health check statuses
            for component_name, component_data in health_summary.get('components', {}).items():
                status_value = 1 if component_data['status'] == 'healthy' else 0
                self.metrics['health_check_status'].labels(
                    check_name=component_name
                ).set(status_value)
            
        except Exception as e:
            logger.error(f"Health metrics collection failed: {e}")
    
    async def _collect_resilience_metrics(self):
        """Collect resilience pattern metrics"""
        try:
            resilience_manager = get_resilience_manager()
            timeout_registry = get_timeout_registry()
            
            resilience_stats = resilience_manager.get_all_stats()
            timeout_stats = timeout_registry.get_all_stats()
            
            # Circuit breaker metrics
            for cb_name, cb_stats in resilience_stats.get('circuit_breakers', {}).items():
                # Circuit breaker state (1=closed, 0.5=half-open, 0=open)
                state_value = 1 if cb_stats['state'] == 'closed' else (0.5 if cb_stats['state'] == 'half_open' else 0)
                self.update_gauge('circuit_breaker_state', state_value, circuit_breaker=cb_name)
                
                # Failure rate
                self.update_gauge('circuit_breaker_failure_rate', cb_stats.get('failure_rate', 0), circuit_breaker=cb_name)
            
            # Timeout metrics
            for tm_name, tm_stats in timeout_stats.get('managers', {}).items():
                self.update_gauge('timeout_manager_current_timeout', tm_stats.get('current_timeout', 0), manager=tm_name)
                self.update_gauge('timeout_manager_timeout_rate', tm_stats.get('timeout_rate', 0), manager=tm_name)
            
        except Exception as e:
            logger.error(f"Resilience metrics collection failed: {e}")
    
    def _get_system_start_time(self) -> float:
        """Get system start time (mock implementation)"""
        # In real implementation, this would track actual system start time
        return time.time() - 3600  # Mock: system started 1 hour ago
    
    def get_metrics_output(self) -> str:
        """Get Prometheus formatted metrics output"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self.registry).decode('utf-8')
        else:
            return "# Prometheus client not available - using mock metrics\n"


class GrafanaDashboardProvisioner:
    """
    Grafana dashboard provisioning and management
    """
    
    def __init__(self):
        self.config = get_config()
        
    def generate_energy_dashboard(self) -> Dict[str, Any]:
        """Generate energy assessment dashboard configuration"""
        return {
            "dashboard": {
                "id": None,
                "title": "ATHintel Energy Assessment Platform",
                "tags": ["energy", "assessments", "athintel"],
                "timezone": "UTC",
                "panels": [
                    {
                        "id": 1,
                        "title": "Assessment Rate",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "rate(athintel_assessments_total[5m])",
                                "legendFormat": "Assessments/sec"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 6, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Assessment Duration",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(athintel_assessment_duration_seconds_bucket[5m]))",
                                "legendFormat": "95th percentile"
                            },
                            {
                                "expr": "histogram_quantile(0.50, rate(athintel_assessment_duration_seconds_bucket[5m]))",
                                "legendFormat": "50th percentile"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 12, "x": 6, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Energy Class Distribution",
                        "type": "piechart",
                        "targets": [
                            {
                                "expr": "sum by(energy_class) (athintel_assessments_total)",
                                "legendFormat": "Class {{energy_class}}"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 6, "x": 18, "y": 0}
                    },
                    {
                        "id": 4,
                        "title": "ML Model Performance",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "athintel_ml_model_accuracy_ratio",
                                "legendFormat": "{{model_name}} accuracy"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 6}
                    },
                    {
                        "id": 5,
                        "title": "External Service Health",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "avg(athintel_health_check_status)",
                                "legendFormat": "Health Score"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 6, "x": 12, "y": 6}
                    },
                    {
                        "id": 6,
                        "title": "Business Metrics - Energy Savings",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "rate(athintel_energy_savings_estimated_kwh[1h])",
                                "legendFormat": "kWh savings/hour"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 12}
                    }
                ],
                "time": {
                    "from": "now-6h",
                    "to": "now"
                },
                "refresh": "30s"
            }
        }
    
    def generate_system_dashboard(self) -> Dict[str, Any]:
        """Generate system monitoring dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "ATHintel System Monitoring",
                "tags": ["system", "infrastructure", "athintel"],
                "timezone": "UTC",
                "panels": [
                    {
                        "id": 1,
                        "title": "System Uptime",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "athintel_system_uptime_seconds",
                                "legendFormat": "Uptime"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "s"
                            }
                        },
                        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "API Response Time",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(athintel_api_response_time_seconds_bucket[5m]))",
                                "legendFormat": "95th percentile"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 12, "x": 6, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Database Connections",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "athintel_database_connections_active",
                                "legendFormat": "Active connections"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 6, "x": 18, "y": 0}
                    },
                    {
                        "id": 4,
                        "title": "Circuit Breaker Status",
                        "type": "timeseries",
                        "targets": [
                            {
                                "expr": "circuit_breaker_state",
                                "legendFormat": "{{circuit_breaker}}"
                            }
                        ],
                        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 6}
                    }
                ]
            }
        }
    
    def generate_alert_rules(self) -> Dict[str, Any]:
        """Generate Prometheus alert rules"""
        return {
            "groups": [
                {
                    "name": "athintel.rules",
                    "rules": [
                        {
                            "alert": "HighAssessmentLatency",
                            "expr": "histogram_quantile(0.95, rate(athintel_assessment_duration_seconds_bucket[5m])) > 30",
                            "for": "2m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High assessment processing latency",
                                "description": "95th percentile assessment duration is {{ $value }}s"
                            }
                        },
                        {
                            "alert": "MLModelAccuracyDegraded",
                            "expr": "athintel_ml_model_accuracy_ratio < 0.85",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "ML model accuracy degraded",
                                "description": "Model {{ $labels.model_name }} accuracy is {{ $value }}"
                            }
                        },
                        {
                            "alert": "CircuitBreakerOpen",
                            "expr": "circuit_breaker_state == 0",
                            "for": "1m",
                            "labels": {
                                "severity": "critical"
                            },
                            "annotations": {
                                "summary": "Circuit breaker is open",
                                "description": "Circuit breaker {{ $labels.circuit_breaker }} is open"
                            }
                        },
                        {
                            "alert": "HealthCheckFailing",
                            "expr": "athintel_health_check_status == 0",
                            "for": "2m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "Health check failing",
                                "description": "Health check {{ $labels.check_name }} is failing"
                            }
                        },
                        {
                            "alert": "HighDatabaseLatency",
                            "expr": "histogram_quantile(0.95, rate(athintel_database_query_duration_seconds_bucket[5m])) > 1.0",
                            "for": "3m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High database query latency",
                                "description": "95th percentile database query time is {{ $value }}s"
                            }
                        }
                    ]
                }
            ]
        }


class MonitoringIntegrator:
    """
    Integration coordinator for monitoring systems
    """
    
    def __init__(self):
        self.metrics_collector = PrometheusMetricsCollector()
        self.dashboard_provisioner = GrafanaDashboardProvisioner()
        
        # Background collection task
        self.collection_task: Optional[asyncio.Task] = None
        self.collection_interval = 30  # seconds
        self.running = False
        
    async def start_monitoring(self):
        """Start monitoring collection"""
        if self.running:
            logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Monitoring integration started")
    
    async def stop_monitoring(self):
        """Stop monitoring collection"""
        if not self.running:
            return
        
        self.running = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitoring integration stopped")
    
    async def _collection_loop(self):
        """Background metrics collection loop"""
        while self.running:
            try:
                await self.metrics_collector.collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    def get_metrics_endpoint(self):
        """Get metrics endpoint for Prometheus scraping"""
        return self.metrics_collector.get_metrics_output()
    
    def provision_dashboards(self) -> Dict[str, Any]:
        """Provision all Grafana dashboards"""
        return {
            "energy_dashboard": self.dashboard_provisioner.generate_energy_dashboard(),
            "system_dashboard": self.dashboard_provisioner.generate_system_dashboard(),
            "alert_rules": self.dashboard_provisioner.generate_alert_rules()
        }


# Global monitoring integrator instance
_monitoring_integrator = None


def get_monitoring_integrator() -> MonitoringIntegrator:
    """Get or create global monitoring integrator"""
    global _monitoring_integrator
    if _monitoring_integrator is None:
        _monitoring_integrator = MonitoringIntegrator()
    return _monitoring_integrator


# Convenience functions
def record_assessment_metric(duration: float, score: float, energy_class: str):
    """Record assessment metrics"""
    integrator = get_monitoring_integrator()
    integrator.metrics_collector.record_assessment(duration, score, energy_class)


def record_ml_prediction_metric(model_type: str, confidence: float):
    """Record ML prediction metrics"""
    integrator = get_monitoring_integrator()
    integrator.metrics_collector.record_ml_prediction(model_type, confidence)


def record_business_metric(metric_type: str, value: float, **labels):
    """Record business metrics"""
    integrator = get_monitoring_integrator()
    integrator.metrics_collector.record_business_metric(metric_type, value, **labels)


async def start_monitoring_system():
    """Start the monitoring system"""
    integrator = get_monitoring_integrator()
    await integrator.start_monitoring()


async def stop_monitoring_system():
    """Stop the monitoring system"""
    integrator = get_monitoring_integrator()
    await integrator.stop_monitoring()


def get_prometheus_metrics():
    """Get Prometheus metrics output"""
    integrator = get_monitoring_integrator()
    return integrator.get_metrics_endpoint()