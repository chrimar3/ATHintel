"""
🏥 Resilient Health Checks

Enhanced health checks that integrate with resilience patterns:
- Circuit breaker-aware health monitoring
- Degraded service detection and reporting
- Adaptive health check intervals based on service stability
- Integration with external service resilience patterns
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from ..resilience import (
    get_resilience_manager,
    get_timeout_registry,
    get_external_service_client,
    CircuitState
)
from monitoring.health_system import (
    HealthCheck,
    HealthStatus,
    HealthCheckResult,
    get_health_monitor
)

logger = logging.getLogger(__name__)


class ServiceHealthLevel(Enum):
    """Service health levels based on resilience state"""
    OPTIMAL = "optimal"          # All systems operational
    DEGRADED = "degraded"        # Some resilience patterns active
    IMPAIRED = "impaired"        # Multiple patterns active, reduced functionality
    CRITICAL = "critical"        # Major systems failing


@dataclass
class ResilienceHealthMetrics:
    """Health metrics from resilience patterns"""
    circuit_breakers: Dict[str, Dict[str, Any]]
    timeout_managers: Dict[str, Dict[str, Any]]
    bulkheads: Dict[str, Dict[str, Any]]
    retry_mechanisms: Dict[str, Dict[str, Any]]
    external_services: Dict[str, Dict[str, Any]]
    overall_level: ServiceHealthLevel


class ResilienceAwareHealthCheck(HealthCheck):
    """
    Health check that considers resilience patterns state
    """
    
    def __init__(self, name: str, critical: bool = True):
        super().__init__(name, critical)
        self.resilience_manager = get_resilience_manager()
        self.timeout_registry = get_timeout_registry()
        
    async def check_health(self) -> HealthCheckResult:
        """Check health with resilience pattern awareness"""
        start_time = time.time()
        
        try:
            # Get resilience statistics
            resilience_stats = self.resilience_manager.get_all_stats()
            timeout_stats = self.timeout_registry.get_all_stats()
            
            # Analyze resilience state
            health_level = self._analyze_resilience_health(resilience_stats, timeout_stats)
            
            # Determine health status based on resilience state
            if health_level == ServiceHealthLevel.OPTIMAL:
                status = HealthStatus.HEALTHY
                message = "All resilience patterns operating normally"
            elif health_level == ServiceHealthLevel.DEGRADED:
                status = HealthStatus.WARNING
                message = "Some resilience patterns active - service degraded"
            elif health_level == ServiceHealthLevel.IMPAIRED:
                status = HealthStatus.WARNING
                message = "Multiple resilience patterns active - service impaired"
            else:  # CRITICAL
                status = HealthStatus.CRITICAL
                message = "Critical resilience failures detected"
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details={
                    'resilience_health_level': health_level.value,
                    'circuit_breakers': resilience_stats['circuit_breakers'],
                    'timeout_managers': timeout_stats['managers'],
                    'bulkheads': resilience_stats['bulkheads'],
                    'retry_mechanisms': resilience_stats['retry_mechanisms'],
                    'open_circuits': resilience_stats['summary']['open_circuits']
                }
            )
            
        except Exception as e:
            logger.error(f"Resilience health check failed: {e}")
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {e}",
                timestamp=datetime.now(),
                response_time_ms=response_time
            )
    
    def _analyze_resilience_health(
        self,
        resilience_stats: Dict[str, Any],
        timeout_stats: Dict[str, Any]
    ) -> ServiceHealthLevel:
        """Analyze resilience patterns to determine health level"""
        
        # Count problematic patterns
        issues = 0
        critical_issues = 0
        
        # Check circuit breakers
        open_circuits = resilience_stats['summary']['open_circuits']
        if open_circuits > 0:
            issues += open_circuits
            # Open circuits for critical services are more serious
            for cb_name, cb_stats in resilience_stats['circuit_breakers'].items():
                if cb_stats['state'] == 'open' and 'critical' in cb_name.lower():
                    critical_issues += 1
        
        # Check timeout managers
        for tm_name, tm_stats in timeout_stats['managers'].items():
            timeout_rate = tm_stats.get('timeout_rate', 0)
            if timeout_rate > 0.1:  # More than 10% timeout rate
                issues += 1
                if timeout_rate > 0.3:  # More than 30% timeout rate
                    critical_issues += 1
        
        # Check bulkheads
        for bh_name, bh_stats in resilience_stats['bulkheads'].items():
            rejection_rate = bh_stats.get('rejection_rate', 0)
            utilization = bh_stats.get('utilization', 0)
            
            if rejection_rate > 0.05:  # More than 5% rejection rate
                issues += 1
            if utilization > 0.9:  # More than 90% utilization
                issues += 1
                
            if rejection_rate > 0.2 or utilization > 0.95:
                critical_issues += 1
        
        # Check retry mechanisms
        for rm_name, rm_stats in resilience_stats['retry_mechanisms'].items():
            retry_rate = rm_stats.get('retry_rate', 0)
            if retry_rate > 0.2:  # More than 20% retry rate
                issues += 1
                if retry_rate > 0.5:  # More than 50% retry rate
                    critical_issues += 1
        
        # Determine health level
        if critical_issues > 2:
            return ServiceHealthLevel.CRITICAL
        elif critical_issues > 0 or issues > 5:
            return ServiceHealthLevel.IMPAIRED
        elif issues > 2:
            return ServiceHealthLevel.DEGRADED
        else:
            return ServiceHealthLevel.OPTIMAL


class ExternalServiceHealthCheck(HealthCheck):
    """
    Health check for external services with resilience integration
    """
    
    def __init__(self, service_name: str, critical: bool = False):
        super().__init__(f"external_service_{service_name}", critical)
        self.service_name = service_name
        
    async def check_health(self) -> HealthCheckResult:
        """Check external service health through resilient client"""
        start_time = time.time()
        
        try:
            # Get external service client
            client = await get_external_service_client()
            
            # Perform health check
            health_result = await client.health_check(self.service_name)
            
            response_time = (time.time() - start_time) * 1000
            
            if health_result['healthy']:
                status = HealthStatus.HEALTHY
                message = f"External service '{self.service_name}' is healthy"
            else:
                status = HealthStatus.WARNING if not self.critical else HealthStatus.CRITICAL
                message = f"External service '{self.service_name}' is unhealthy: {health_result.get('error', 'Unknown error')}"
            
            return HealthCheckResult(
                name=self.name,
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=health_result
            )
            
        except Exception as e:
            logger.error(f"External service health check failed for {self.service_name}: {e}")
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {e}",
                timestamp=datetime.now(),
                response_time_ms=response_time
            )


class AdaptiveHealthMonitor:
    """
    Health monitor with adaptive intervals based on service stability
    """
    
    def __init__(self):
        self.base_check_interval = 30  # Base interval in seconds
        self.min_check_interval = 10   # Minimum interval
        self.max_check_interval = 300  # Maximum interval (5 minutes)
        
        # Track stability for adaptive intervals
        self.service_stability: Dict[str, List[bool]] = {}  # Service -> [recent health results]
        self.stability_window = 20  # Number of recent results to consider
        
        logger.info("Adaptive health monitor initialized")
    
    def calculate_check_interval(self, service_name: str, recent_health: bool) -> int:
        """
        Calculate adaptive check interval based on service stability
        
        Args:
            service_name: Name of the service
            recent_health: Most recent health status
            
        Returns:
            Check interval in seconds
        """
        # Initialize if new service
        if service_name not in self.service_stability:
            self.service_stability[service_name] = []
        
        # Add recent health result
        self.service_stability[service_name].append(recent_health)
        
        # Keep only recent results
        if len(self.service_stability[service_name]) > self.stability_window:
            self.service_stability[service_name] = self.service_stability[service_name][-self.stability_window:]
        
        # Calculate stability score (percentage of healthy checks)
        stability_score = sum(self.service_stability[service_name]) / len(self.service_stability[service_name])
        
        # Adjust interval based on stability
        if stability_score >= 0.95:  # Very stable (95%+ healthy)
            interval = min(self.base_check_interval * 2, self.max_check_interval)
        elif stability_score >= 0.80:  # Stable (80%+ healthy)
            interval = self.base_check_interval
        elif stability_score >= 0.60:  # Unstable (60%+ healthy)
            interval = max(self.base_check_interval // 2, self.min_check_interval)
        else:  # Very unstable (< 60% healthy)
            interval = self.min_check_interval
        
        logger.debug(f"Service '{service_name}' stability: {stability_score:.2f}, interval: {interval}s")
        
        return interval
    
    def get_stability_stats(self) -> Dict[str, Any]:
        """Get stability statistics for all services"""
        stats = {}
        
        for service_name, health_history in self.service_stability.items():
            if health_history:
                stability_score = sum(health_history) / len(health_history)
                interval = self.calculate_check_interval(service_name, health_history[-1])
                
                stats[service_name] = {
                    'stability_score': stability_score,
                    'current_interval': interval,
                    'recent_checks': len(health_history),
                    'recent_healthy': sum(health_history),
                    'recent_unhealthy': len(health_history) - sum(health_history)
                }
        
        return stats


class IntegratedResilienceHealthCheck:
    """
    Integrated health check that combines system health with resilience patterns
    """
    
    def __init__(self):
        self.adaptive_monitor = AdaptiveHealthMonitor()
        
    async def get_comprehensive_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status including resilience patterns
        
        Returns:
            Complete health assessment with resilience integration
        """
        # Get basic health status
        health_monitor = await get_health_monitor()
        basic_health = await health_monitor.get_system_health_summary()
        
        # Get resilience health
        resilience_check = ResilienceAwareHealthCheck("resilience_patterns")
        resilience_health = await resilience_check.check_health()
        
        # Get external services health
        try:
            client = await get_external_service_client()
            external_health = await client.health_check_all()
        except Exception as e:
            logger.error(f"External services health check failed: {e}")
            external_health = {
                'services': {},
                'summary': {
                    'total_services': 0,
                    'healthy_services': 0,
                    'unhealthy_services': 0,
                    'overall_healthy': False
                },
                'error': str(e)
            }
        
        # Get adaptive monitoring stats
        stability_stats = self.adaptive_monitor.get_stability_stats()
        
        # Determine overall health level
        overall_level = self._determine_overall_health_level(
            basic_health,
            resilience_health,
            external_health
        )
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health_level': overall_level.value,
            'system_health': basic_health,
            'resilience_health': {
                'status': resilience_health.status.value,
                'message': resilience_health.message,
                'details': resilience_health.details
            },
            'external_services_health': external_health,
            'adaptive_monitoring': {
                'stability_stats': stability_stats,
                'total_services': len(stability_stats)
            },
            'recommendations': self._generate_health_recommendations(
                overall_level,
                resilience_health.details
            )
        }
    
    def _determine_overall_health_level(
        self,
        basic_health: Dict[str, Any],
        resilience_health: HealthCheckResult,
        external_health: Dict[str, Any]
    ) -> ServiceHealthLevel:
        """Determine overall health level"""
        
        # Check basic system health
        system_status = basic_health.get('overall_status', 'critical').lower()
        
        # Check resilience health
        resilience_level = resilience_health.details.get('resilience_health_level', 'critical')
        
        # Check external services
        external_healthy = external_health.get('summary', {}).get('overall_healthy', False)
        
        # Determine overall level (most restrictive wins)
        if system_status == 'critical' or resilience_level == 'critical':
            return ServiceHealthLevel.CRITICAL
        elif system_status in ['unhealthy', 'warning'] or resilience_level == 'impaired' or not external_healthy:
            return ServiceHealthLevel.IMPAIRED
        elif resilience_level == 'degraded':
            return ServiceHealthLevel.DEGRADED
        else:
            return ServiceHealthLevel.OPTIMAL
    
    def _generate_health_recommendations(
        self,
        overall_level: ServiceHealthLevel,
        resilience_details: Dict[str, Any]
    ) -> List[str]:
        """Generate health recommendations based on current status"""
        recommendations = []
        
        if overall_level == ServiceHealthLevel.CRITICAL:
            recommendations.extend([
                "🚨 IMMEDIATE ACTION REQUIRED: Critical system failures detected",
                "Check application logs for detailed error information",
                "Verify database and Redis connectivity",
                "Consider scaling down non-essential services"
            ])
        
        elif overall_level == ServiceHealthLevel.IMPAIRED:
            recommendations.extend([
                "⚠️  ATTENTION: System operating in degraded mode",
                "Monitor error rates and response times closely",
                "Prepare for potential service disruption"
            ])
        
        elif overall_level == ServiceHealthLevel.DEGRADED:
            recommendations.extend([
                "ℹ️  INFO: Resilience patterns active, monitor performance",
                "Check if increased load requires scaling"
            ])
        
        # Add specific resilience recommendations
        open_circuits = resilience_details.get('open_circuits', 0)
        if open_circuits > 0:
            recommendations.append(f"🔌 {open_circuits} circuit breaker(s) open - check external service connectivity")
        
        # Check timeout patterns
        timeout_issues = 0
        for tm_name, tm_stats in resilience_details.get('timeout_managers', {}).items():
            if tm_stats.get('timeout_rate', 0) > 0.1:
                timeout_issues += 1
        
        if timeout_issues > 0:
            recommendations.append(f"⏱️  {timeout_issues} service(s) experiencing high timeout rates - investigate performance")
        
        if not recommendations:
            recommendations.append("✅ System operating optimally")
        
        return recommendations


# Global integrated health check instance
_integrated_health_check = None


async def get_integrated_health_check() -> IntegratedResilienceHealthCheck:
    """Get or create global integrated health check"""
    global _integrated_health_check
    if _integrated_health_check is None:
        _integrated_health_check = IntegratedResilienceHealthCheck()
    return _integrated_health_check


# Convenience function for comprehensive health status
async def get_comprehensive_health_status() -> Dict[str, Any]:
    """Get comprehensive health status including resilience patterns"""
    health_check = await get_integrated_health_check()
    return await health_check.get_comprehensive_health_status()