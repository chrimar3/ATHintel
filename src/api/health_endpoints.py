"""
🏥 Health Check API Endpoints

Production-ready health check endpoints for load balancers, monitoring systems,
and operational health verification of the energy assessment platform.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

# FastAPI with graceful fallback
try:
    from fastapi import FastAPI, HTTPException, Depends
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.warning("FastAPI not available, health endpoints will use mock responses")

from monitoring.health_system import get_health_monitor, HealthStatus, HealthMonitoringSystem
from config.production_config import get_config

logger = logging.getLogger(__name__)

class HealthEndpoints:
    """Health check endpoints for the energy assessment system"""
    
    def __init__(self):
        self.config = get_config()
        self.start_time = datetime.now()
        self._readiness_cache: Optional[Dict[str, Any]] = None
        self._readiness_cache_time: Optional[datetime] = None
        self.cache_duration = timedelta(seconds=10)  # Cache readiness for 10 seconds
    
    async def liveness_probe(self) -> Dict[str, Any]:
        """
        Kubernetes liveness probe - indicates if the application is running
        Should return 200 if the application is alive, even if degraded
        """
        return {
            "status": "alive",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "version": "2.0.0",
            "environment": self.config.environment
        }
    
    async def readiness_probe(self) -> Dict[str, Any]:
        """
        Kubernetes readiness probe - indicates if the application can serve traffic
        Returns 200 only if all critical systems are healthy
        """
        # Check cache first to avoid overwhelming health checks
        now = datetime.now()
        if (self._readiness_cache and self._readiness_cache_time and 
            now - self._readiness_cache_time < self.cache_duration):
            return self._readiness_cache
        
        try:
            health_monitor = await get_health_monitor()
            health_summary = await health_monitor.get_system_health_summary()
            
            # Determine readiness based on critical components
            is_ready = True
            critical_issues = []
            
            for name, component in health_summary['components'].items():
                check = health_monitor.health_checks.get(name)
                
                # Critical components must be healthy for readiness
                if check and check.critical:
                    if component['status'] in ['critical', 'unhealthy']:
                        is_ready = False
                        critical_issues.append(f"{name}: {component['message']}")
            
            status_code = 200 if is_ready else 503
            
            readiness_result = {
                "status": "ready" if is_ready else "not_ready",
                "timestamp": datetime.now().isoformat(),
                "critical_issues": critical_issues,
                "overall_health": health_summary['overall_status'],
                "components": {
                    name: {
                        "status": comp['status'],
                        "message": comp['message']
                    }
                    for name, comp in health_summary['components'].items()
                }
            }
            
            # Cache the result
            self._readiness_cache = readiness_result
            self._readiness_cache_time = now
            
            if not is_ready:
                logger.warning(f"Readiness check failed: {critical_issues}")
            
            return readiness_result
            
        except Exception as e:
            logger.error(f"Readiness probe failed: {e}")
            return {
                "status": "not_ready",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def detailed_health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check with detailed component status
        For operational monitoring and debugging
        """
        try:
            health_monitor = await get_health_monitor()
            health_summary = await health_monitor.get_system_health_summary()
            
            # Add additional system information
            health_summary.update({
                "application": {
                    "name": "ATHintel Energy Assessment System",
                    "version": "2.0.0",
                    "environment": self.config.environment,
                    "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                    "start_time": self.start_time.isoformat()
                },
                "configuration": {
                    "ml_predictions_enabled": self.config.get_feature_flags()['ml_predictions_enabled'],
                    "caching_enabled": self.config.get_feature_flags()['caching_enabled'],
                    "performance_monitoring_enabled": self.config.get_feature_flags()['performance_monitoring_enabled'],
                    "max_concurrent_assessments": self.config.pipeline.max_concurrent_assessments,
                    "database_pool_size": f"{self.config.database.min_connections}-{self.config.database.max_connections}"
                }
            })
            
            return health_summary
            
        except Exception as e:
            logger.error(f"Detailed health check failed: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "application": {
                    "name": "ATHintel Energy Assessment System",
                    "version": "2.0.0",
                    "environment": self.config.environment
                }
            }
    
    async def component_health_check(self, component_name: str) -> Dict[str, Any]:
        """
        Individual component health check
        For targeted monitoring of specific system components
        """
        try:
            health_monitor = await get_health_monitor()
            
            if component_name not in health_monitor.health_checks:
                raise HTTPException(
                    status_code=404,
                    detail=f"Component '{component_name}' not found. Available components: {list(health_monitor.health_checks.keys())}"
                )
            
            health_check = health_monitor.health_checks[component_name]
            result = await health_check.execute()
            
            return {
                "component": component_name,
                "result": result.to_dict(),
                "is_critical": health_check.critical,
                "failure_count": health_check.failure_count,
                "last_success": health_check.last_success.isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Component health check failed for {component_name}: {e}")
            return {
                "component": component_name,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def performance_metrics(self) -> Dict[str, Any]:
        """
        Performance metrics endpoint for monitoring systems
        """
        try:
            health_monitor = await get_health_monitor()
            
            # Collect performance metrics from health checks
            performance_data = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "component_metrics": {}
            }
            
            for name, check in health_monitor.health_checks.items():
                if check.last_result:
                    performance_data["component_metrics"][name] = {
                        "response_time_ms": check.last_result.response_time_ms,
                        "failure_count": check.failure_count,
                        "last_check": check.last_result.timestamp.isoformat(),
                        "status": check.last_result.status.value
                    }
            
            # Add application-level metrics
            performance_data.update({
                "application_metrics": {
                    "active_health_checks": len(health_monitor.health_checks),
                    "active_alerts": len([a for a in health_monitor.alerts.values() if not a.resolved_at]),
                    "monitoring_active": health_monitor.monitoring_active,
                    "check_interval_seconds": health_monitor.check_interval
                }
            })
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Performance metrics collection failed: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def alerts_status(self) -> Dict[str, Any]:
        """
        Current alerts status for operational awareness
        """
        try:
            health_monitor = await get_health_monitor()
            
            # Get active and recent resolved alerts
            active_alerts = [
                alert for alert in health_monitor.alerts.values() 
                if not alert.resolved_at
            ]
            
            recent_resolved = [
                alert for alert in health_monitor.alerts.values()
                if alert.resolved_at and 
                datetime.now() - alert.resolved_at < timedelta(hours=24)
            ]
            
            # Group by severity
            alerts_by_severity = {}
            for alert in active_alerts:
                severity = alert.severity.value
                if severity not in alerts_by_severity:
                    alerts_by_severity[severity] = []
                alerts_by_severity[severity].append(alert.to_dict())
            
            return {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "active_alerts": len(active_alerts),
                    "resolved_in_24h": len(recent_resolved),
                    "total_alerts": len(health_monitor.alerts)
                },
                "active_by_severity": alerts_by_severity,
                "recent_resolved": [alert.to_dict() for alert in recent_resolved[-5:]],  # Last 5 resolved
                "alert_handlers": len(health_monitor.alert_handlers)
            }
            
        except Exception as e:
            logger.error(f"Alerts status collection failed: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

# Create health endpoints instance
health_endpoints = HealthEndpoints()

# FastAPI integration
if FASTAPI_AVAILABLE:
    def create_health_router():
        """Create FastAPI router with health endpoints"""
        from fastapi import APIRouter
        
        router = APIRouter(prefix="/health", tags=["health"])
        
        @router.get("/live")
        async def liveness():
            """Liveness probe for Kubernetes"""
            return await health_endpoints.liveness_probe()
        
        @router.get("/ready")
        async def readiness():
            """Readiness probe for Kubernetes"""
            result = await health_endpoints.readiness_probe()
            status_code = 200 if result.get('status') == 'ready' else 503
            return JSONResponse(content=result, status_code=status_code)
        
        @router.get("/")
        async def detailed_health():
            """Detailed system health check"""
            return await health_endpoints.detailed_health_check()
        
        @router.get("/component/{component_name}")
        async def component_health(component_name: str):
            """Individual component health check"""
            return await health_endpoints.component_health_check(component_name)
        
        @router.get("/metrics")
        async def performance_metrics():
            """Performance metrics for monitoring"""
            return await health_endpoints.performance_metrics()
        
        @router.get("/alerts")
        async def alerts_status():
            """Current alerts status"""
            return await health_endpoints.alerts_status()
        
        return router

# Standalone health check functions for direct use
async def check_liveness() -> Dict[str, Any]:
    """Standalone liveness check"""
    return await health_endpoints.liveness_probe()

async def check_readiness() -> bool:
    """Standalone readiness check returning boolean"""
    result = await health_endpoints.readiness_probe()
    return result.get('status') == 'ready'

async def get_health_status() -> Dict[str, Any]:
    """Get current health status"""
    return await health_endpoints.detailed_health_check()

# Health monitoring startup/shutdown
async def start_health_monitoring():
    """Start background health monitoring"""
    try:
        health_monitor = await get_health_monitor()
        
        # Start monitoring in background
        asyncio.create_task(health_monitor.start_monitoring())
        
        logger.info("Health monitoring started")
        
    except Exception as e:
        logger.error(f"Failed to start health monitoring: {e}")

async def stop_health_monitoring():
    """Stop background health monitoring"""
    try:
        health_monitor = await get_health_monitor()
        await health_monitor.stop_monitoring()
        
        logger.info("Health monitoring stopped")
        
    except Exception as e:
        logger.error(f"Failed to stop health monitoring: {e}")

# Example usage for testing
async def example_health_check():
    """Example of using health check system"""
    print("Running health check example...")
    
    # Start health monitoring
    await start_health_monitoring()
    
    # Wait a moment for checks to run
    await asyncio.sleep(2)
    
    # Get health status
    health_status = await get_health_status()
    
    print(f"Overall status: {health_status['overall_status']}")
    print(f"Components: {len(health_status['components'])}")
    
    for name, component in health_status['components'].items():
        print(f"  {name}: {component['status']} - {component['message']}")
    
    # Check readiness
    is_ready = await check_readiness()
    print(f"System ready for traffic: {is_ready}")
    
    # Stop monitoring
    await stop_health_monitoring()

if __name__ == "__main__":
    asyncio.run(example_health_check())