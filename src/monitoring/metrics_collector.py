"""
Real-time Metrics Collector
Story 1.3: Monitoring Dashboard
Collects and aggregates validation metrics for dashboard display
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics


@dataclass
class ValidationMetric:
    """Single validation metric data point"""
    timestamp: float
    property_id: str
    total_score: float
    validation_time_ms: float
    is_valid: bool
    error_count: int
    warning_count: int
    factors: Dict[str, float]


@dataclass
class AggregatedMetrics:
    """Aggregated metrics for a time window"""
    start_time: float
    end_time: float
    total_validations: int
    valid_count: int
    invalid_count: int
    avg_score: float
    min_score: float
    max_score: float
    avg_validation_time_ms: float
    p95_validation_time_ms: float
    p99_validation_time_ms: float
    errors_by_type: Dict[str, int]
    warnings_by_type: Dict[str, int]
    throughput_per_minute: float


class MetricsCollector:
    """
    Collects and aggregates validation metrics
    Provides real-time and historical data for dashboard
    """
    
    def __init__(self, max_history_hours: int = 168):  # 7 days default
        """
        Initialize metrics collector
        
        Args:
            max_history_hours: Maximum hours of history to retain
        """
        self.max_history_hours = max_history_hours
        self.metrics: deque = deque(maxlen=max_history_hours * 3600)  # 1 metric/second max
        self.aggregated_cache: Dict[str, AggregatedMetrics] = {}
        self.lock = threading.RLock()
        
        # Real-time counters
        self.current_minute_count = 0
        self.current_minute_start = time.time()
        
        # Alert thresholds
        self.alert_thresholds = {
            'low_score': 50,
            'high_latency_ms': 100,
            'error_rate': 0.1,
            'throughput_min': 100
        }
        
        # Active alerts
        self.active_alerts: List[Dict[str, Any]] = []
        
        # Start background aggregation thread
        self.running = True
        self.aggregation_thread = threading.Thread(target=self._background_aggregation)
        self.aggregation_thread.daemon = True
        self.aggregation_thread.start()
    
    def record_validation(self, validation_result: Dict[str, Any]) -> None:
        """
        Record a validation result
        
        Args:
            validation_result: Validation result from PropertyValidator
        """
        with self.lock:
            # Create metric from result
            metric = ValidationMetric(
                timestamp=time.time(),
                property_id=validation_result.get('property_id', 'unknown'),
                total_score=validation_result.get('total_score', 0),
                validation_time_ms=validation_result.get('validation_time_ms', 0),
                is_valid=validation_result.get('is_valid', False),
                error_count=len(validation_result.get('errors', [])),
                warning_count=len(validation_result.get('warnings', [])),
                factors=validation_result.get('score_breakdown', {})
            )
            
            self.metrics.append(metric)
            
            # Update real-time counter
            current_time = time.time()
            if current_time - self.current_minute_start > 60:
                self.current_minute_count = 1
                self.current_minute_start = current_time
            else:
                self.current_minute_count += 1
            
            # Check for alerts
            self._check_alerts(metric)
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """
        Get real-time metrics for dashboard
        
        Returns:
            Real-time metrics dictionary
        """
        with self.lock:
            if not self.metrics:
                return self._empty_metrics()
            
            # Last 60 seconds of data
            current_time = time.time()
            recent_metrics = [
                m for m in self.metrics 
                if current_time - m.timestamp <= 60
            ]
            
            if not recent_metrics:
                return self._empty_metrics()
            
            # Calculate real-time stats
            valid_count = sum(1 for m in recent_metrics if m.is_valid)
            scores = [m.total_score for m in recent_metrics]
            times = [m.validation_time_ms for m in recent_metrics]
            
            return {
                'timestamp': current_time,
                'last_minute': {
                    'total_validations': len(recent_metrics),
                    'valid_count': valid_count,
                    'invalid_count': len(recent_metrics) - valid_count,
                    'validity_rate': valid_count / len(recent_metrics) if recent_metrics else 0,
                    'avg_score': statistics.mean(scores) if scores else 0,
                    'avg_time_ms': statistics.mean(times) if times else 0,
                    'max_time_ms': max(times) if times else 0,
                    'throughput_per_minute': len(recent_metrics)
                },
                'current_second_rate': self.current_minute_count / max(1, current_time - self.current_minute_start),
                'active_alerts': self.active_alerts
            }
    
    def get_historical_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get historical metrics for trend analysis
        
        Args:
            hours: Number of hours of history to retrieve
            
        Returns:
            Historical metrics by hour
        """
        with self.lock:
            current_time = time.time()
            cutoff_time = current_time - (hours * 3600)
            
            # Filter metrics within time range
            historical = [
                m for m in self.metrics
                if m.timestamp >= cutoff_time
            ]
            
            if not historical:
                return {'hours': hours, 'data': []}
            
            # Aggregate by hour
            hourly_data = defaultdict(list)
            for metric in historical:
                hour_bucket = int(metric.timestamp // 3600) * 3600
                hourly_data[hour_bucket].append(metric)
            
            # Calculate stats for each hour
            result = []
            for hour_timestamp in sorted(hourly_data.keys()):
                hour_metrics = hourly_data[hour_timestamp]
                valid_count = sum(1 for m in hour_metrics if m.is_valid)
                scores = [m.total_score for m in hour_metrics]
                times = [m.validation_time_ms for m in hour_metrics]
                
                result.append({
                    'timestamp': hour_timestamp,
                    'hour': datetime.fromtimestamp(hour_timestamp).isoformat(),
                    'total_validations': len(hour_metrics),
                    'valid_count': valid_count,
                    'invalid_count': len(hour_metrics) - valid_count,
                    'validity_rate': valid_count / len(hour_metrics) if hour_metrics else 0,
                    'avg_score': statistics.mean(scores) if scores else 0,
                    'min_score': min(scores) if scores else 0,
                    'max_score': max(scores) if scores else 0,
                    'avg_time_ms': statistics.mean(times) if times else 0,
                    'p95_time_ms': statistics.quantiles(times, n=20)[18] if len(times) > 1 else 0,
                    'throughput_per_hour': len(hour_metrics)
                })
            
            return {
                'hours': hours,
                'data': result,
                'summary': self._calculate_summary(result)
            }
    
    def get_factor_analysis(self) -> Dict[str, Any]:
        """
        Analyze validation factors performance
        
        Returns:
            Factor-wise performance analysis
        """
        with self.lock:
            if not self.metrics:
                return {}
            
            # Last 1000 validations
            recent = list(self.metrics)[-1000:]
            
            # Aggregate factor scores
            factor_scores = defaultdict(list)
            for metric in recent:
                for factor, score in metric.factors.items():
                    factor_scores[factor].append(score)
            
            # Calculate stats per factor
            analysis = {}
            for factor, scores in factor_scores.items():
                if scores:
                    analysis[factor] = {
                        'avg_score': statistics.mean(scores),
                        'min_score': min(scores),
                        'max_score': max(scores),
                        'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
                        'failing_rate': sum(1 for s in scores if s < 50) / len(scores)
                    }
            
            return analysis
    
    def export_metrics(self, format: str = 'json', hours: int = 24) -> str:
        """
        Export metrics in specified format
        
        Args:
            format: Export format ('json' or 'csv')
            hours: Hours of data to export
            
        Returns:
            Exported data as string
        """
        historical = self.get_historical_metrics(hours)
        
        if format == 'json':
            return json.dumps(historical, indent=2, default=str)
        
        elif format == 'csv':
            lines = ['timestamp,hour,total,valid,invalid,validity_rate,avg_score,avg_time_ms,throughput']
            for row in historical['data']:
                lines.append(
                    f"{row['timestamp']},{row['hour']},{row['total_validations']},"
                    f"{row['valid_count']},{row['invalid_count']},{row['validity_rate']:.2f},"
                    f"{row['avg_score']:.1f},{row['avg_time_ms']:.2f},{row['throughput_per_hour']}"
                )
            return '\n'.join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def set_alert_threshold(self, alert_type: str, value: float) -> None:
        """
        Set alert threshold
        
        Args:
            alert_type: Type of alert
            value: Threshold value
        """
        with self.lock:
            self.alert_thresholds[alert_type] = value
    
    def clear_alerts(self) -> None:
        """Clear all active alerts"""
        with self.lock:
            self.active_alerts = []
    
    def _check_alerts(self, metric: ValidationMetric) -> None:
        """Check if metric triggers any alerts"""
        # Low score alert
        if metric.total_score < self.alert_thresholds['low_score']:
            self._add_alert('low_score', f"Property {metric.property_id} scored {metric.total_score:.1f}")
        
        # High latency alert
        if metric.validation_time_ms > self.alert_thresholds['high_latency_ms']:
            self._add_alert('high_latency', f"Validation took {metric.validation_time_ms:.1f}ms")
        
        # Check error rate (last 100 validations)
        recent = list(self.metrics)[-100:]
        if recent:
            error_rate = sum(1 for m in recent if not m.is_valid) / len(recent)
            if error_rate > self.alert_thresholds['error_rate']:
                self._add_alert('high_error_rate', f"Error rate {error_rate:.1%}")
    
    def _add_alert(self, alert_type: str, message: str) -> None:
        """Add alert if not already active"""
        # Check if similar alert exists
        for alert in self.active_alerts:
            if alert['type'] == alert_type and time.time() - alert['timestamp'] < 300:
                return  # Don't duplicate alerts within 5 minutes
        
        self.active_alerts.append({
            'type': alert_type,
            'message': message,
            'timestamp': time.time(),
            'time': datetime.now().isoformat()
        })
        
        # Keep only last 10 alerts
        if len(self.active_alerts) > 10:
            self.active_alerts = self.active_alerts[-10:]
    
    def _background_aggregation(self) -> None:
        """Background thread for aggregating metrics"""
        while self.running:
            try:
                # Clean old metrics
                with self.lock:
                    current_time = time.time()
                    cutoff_time = current_time - (self.max_history_hours * 3600)
                    
                    # Remove metrics older than max history
                    while self.metrics and self.metrics[0].timestamp < cutoff_time:
                        self.metrics.popleft()
                
                # Sleep for 60 seconds
                time.sleep(60)
                
            except Exception as e:
                print(f"Error in background aggregation: {e}")
                time.sleep(60)
    
    def _calculate_summary(self, hourly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from hourly data"""
        if not hourly_data:
            return {}
        
        total_validations = sum(h['total_validations'] for h in hourly_data)
        total_valid = sum(h['valid_count'] for h in hourly_data)
        avg_scores = [h['avg_score'] for h in hourly_data if h['avg_score'] > 0]
        avg_times = [h['avg_time_ms'] for h in hourly_data if h['avg_time_ms'] > 0]
        
        return {
            'total_validations': total_validations,
            'total_valid': total_valid,
            'total_invalid': total_validations - total_valid,
            'overall_validity_rate': total_valid / total_validations if total_validations else 0,
            'avg_score': statistics.mean(avg_scores) if avg_scores else 0,
            'avg_time_ms': statistics.mean(avg_times) if avg_times else 0,
            'avg_throughput_per_hour': total_validations / len(hourly_data) if hourly_data else 0
        }
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            'timestamp': time.time(),
            'last_minute': {
                'total_validations': 0,
                'valid_count': 0,
                'invalid_count': 0,
                'validity_rate': 0,
                'avg_score': 0,
                'avg_time_ms': 0,
                'max_time_ms': 0,
                'throughput_per_minute': 0
            },
            'current_second_rate': 0,
            'active_alerts': []
        }
    
    def shutdown(self) -> None:
        """Shutdown metrics collector"""
        self.running = False
        if self.aggregation_thread.is_alive():
            self.aggregation_thread.join(timeout=5)


# Global metrics collector instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def record_validation(validation_result: Dict[str, Any]) -> None:
    """
    Convenience function to record validation
    
    Args:
        validation_result: Validation result to record
    """
    collector = get_metrics_collector()
    collector.record_validation(validation_result)