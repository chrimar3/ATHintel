"""
🛡️ Resilience Patterns Demo

Demonstrates the comprehensive resilience patterns implementation:
- Circuit breaker protection for external services
- Retry mechanisms with exponential backoff
- Bulkhead pattern for resource isolation
- Adaptive timeout management
- Integrated health monitoring
"""

import asyncio
import random
import time
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def simulate_unreliable_service(service_name: str, failure_rate: float = 0.3) -> Dict[str, Any]:
    """
    Simulate an unreliable external service
    
    Args:
        service_name: Name of the service
        failure_rate: Probability of failure (0.0 to 1.0)
        
    Returns:
        Service response data
    """
    # Random delay to simulate network latency
    delay = random.uniform(0.1, 2.0)
    await asyncio.sleep(delay)
    
    # Random failure based on failure rate
    if random.random() < failure_rate:
        raise ConnectionError(f"Service {service_name} is temporarily unavailable")
    
    return {
        'service': service_name,
        'data': f"Response from {service_name}",
        'timestamp': datetime.now().isoformat(),
        'response_time_ms': delay * 1000
    }


async def simulate_slow_service(service_name: str, slow_probability: float = 0.2) -> Dict[str, Any]:
    """
    Simulate a service that occasionally responds slowly
    
    Args:
        service_name: Name of the service
        slow_probability: Probability of slow response
        
    Returns:
        Service response data
    """
    # Occasionally respond very slowly
    if random.random() < slow_probability:
        delay = random.uniform(5.0, 15.0)  # Very slow
    else:
        delay = random.uniform(0.1, 1.0)   # Normal speed
    
    await asyncio.sleep(delay)
    
    return {
        'service': service_name,
        'data': f"Slow response from {service_name}",
        'timestamp': datetime.now().isoformat(),
        'response_time_ms': delay * 1000
    }


async def fallback_service_response(service_name: str) -> Dict[str, Any]:
    """
    Fallback response when primary service fails
    
    Args:
        service_name: Name of the primary service
        
    Returns:
        Fallback response data
    """
    return {
        'service': f"{service_name}_fallback",
        'data': f"Fallback response for {service_name}",
        'timestamp': datetime.now().isoformat(),
        'is_fallback': True
    }


async def demo_circuit_breaker_pattern():
    """Demonstrate circuit breaker pattern"""
    logger.info("🔌 DEMO: Circuit Breaker Pattern")
    logger.info("=" * 50)
    
    from src.infrastructure.resilience import get_resilience_manager, CircuitBreakerConfig
    
    # Get resilience manager
    resilience_manager = get_resilience_manager()
    
    # Create circuit breaker with aggressive settings for demo
    circuit_config = CircuitBreakerConfig(
        failure_threshold=3,     # Open after 3 failures
        recovery_timeout=10,     # Try recovery after 10 seconds
        timeout_seconds=3.0      # 3 second timeout
    )
    
    circuit_breaker = resilience_manager.get_or_create_circuit_breaker(
        "demo_service", 
        circuit_config
    )
    
    logger.info(f"Initial circuit state: {circuit_breaker.state.value}")
    
    # Make requests that will trigger circuit breaker
    for i in range(10):
        try:
            logger.info(f"Request {i+1}: Circuit state = {circuit_breaker.state.value}")
            
            result = await circuit_breaker.call(
                simulate_unreliable_service,
                "demo_service",
                failure_rate=0.8  # High failure rate
            )
            
            logger.info(f"  ✅ Success: {result['data']}")
            
        except Exception as e:
            logger.info(f"  ❌ Failed: {type(e).__name__}: {e}")
        
        # Brief pause between requests
        await asyncio.sleep(1)
        
        # Show circuit breaker stats
        stats = circuit_breaker.get_stats()
        logger.info(f"  Stats: {stats['total_calls']} calls, {stats['total_failures']} failures, {stats['failure_rate']:.2%} failure rate")
    
    logger.info(f"Final circuit state: {circuit_breaker.state.value}")
    
    # Wait for recovery and test
    if circuit_breaker.state.value == 'open':
        logger.info(f"Waiting {circuit_config.recovery_timeout} seconds for recovery...")
        await asyncio.sleep(circuit_config.recovery_timeout + 1)
        
        try:
            result = await circuit_breaker.call(
                simulate_unreliable_service,
                "demo_service",
                failure_rate=0.1  # Lower failure rate for recovery
            )
            logger.info(f"  ✅ Recovery success: {result['data']}")
        except Exception as e:
            logger.info(f"  ❌ Recovery failed: {e}")
    
    logger.info("")


async def demo_retry_mechanism():
    """Demonstrate retry mechanism with exponential backoff"""
    logger.info("🔄 DEMO: Retry Mechanism")
    logger.info("=" * 50)
    
    from src.infrastructure.resilience import get_resilience_manager, RetryConfig
    
    # Get resilience manager
    resilience_manager = get_resilience_manager()
    
    # Create retry mechanism
    retry_config = RetryConfig(
        max_attempts=4,
        base_delay=0.5,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=True
    )
    
    retry_mechanism = resilience_manager.get_or_create_retry_mechanism(
        "demo_retry",
        retry_config
    )
    
    logger.info(f"Retry config: max_attempts={retry_config.max_attempts}, base_delay={retry_config.base_delay}s")
    
    # Test retry with eventually successful service
    try:
        logger.info("Testing retry with eventually successful service...")
        start_time = time.time()
        
        result = await retry_mechanism.execute(
            simulate_unreliable_service,
            "retry_demo_service",
            failure_rate=0.6  # Will eventually succeed
        )
        
        elapsed = time.time() - start_time
        logger.info(f"  ✅ Eventually succeeded after {elapsed:.2f}s: {result['data']}")
        
    except Exception as e:
        logger.info(f"  ❌ All retries failed: {e}")
    
    # Show retry stats
    stats = retry_mechanism.get_stats()
    logger.info(f"Retry stats: {stats['total_attempts']} attempts, {stats['total_retries']} retries, {stats['retry_rate']:.2%} retry rate")
    
    logger.info("")


async def demo_bulkhead_pattern():
    """Demonstrate bulkhead pattern for resource isolation"""
    logger.info("🏗️ DEMO: Bulkhead Pattern")
    logger.info("=" * 50)
    
    from src.infrastructure.resilience import get_resilience_manager, BulkheadConfig
    
    # Get resilience manager
    resilience_manager = get_resilience_manager()
    
    # Create bulkhead with limited concurrency
    bulkhead_config = BulkheadConfig(
        max_concurrent=3,
        queue_size=5,
        timeout_seconds=10.0
    )
    
    bulkhead = resilience_manager.get_or_create_bulkhead(
        "demo_bulkhead",
        bulkhead_config
    )
    
    logger.info(f"Bulkhead config: max_concurrent={bulkhead_config.max_concurrent}, queue_size={bulkhead_config.queue_size}")
    
    async def make_slow_request(request_id: int):
        """Make a slow request through bulkhead"""
        try:
            async with bulkhead.acquire():
                logger.info(f"  Request {request_id}: Acquired resource")
                result = await simulate_slow_service(f"bulkhead_service_{request_id}")
                logger.info(f"  Request {request_id}: ✅ Completed")
                return result
        except Exception as e:
            logger.info(f"  Request {request_id}: ❌ Failed - {e}")
            return None
    
    # Launch many concurrent requests
    logger.info("Launching 8 concurrent requests (bulkhead limit is 3)...")
    
    tasks = [make_slow_request(i) for i in range(8)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = sum(1 for r in results if r and not isinstance(r, Exception))
    logger.info(f"Completed: {successful}/{len(results)} requests successful")
    
    # Show bulkhead stats
    stats = bulkhead.get_stats()
    logger.info(f"Bulkhead stats: {stats['total_requests']} total, {stats['rejected_requests']} rejected, {stats['utilization']:.2%} utilization")
    
    logger.info("")


async def demo_adaptive_timeout():
    """Demonstrate adaptive timeout management"""
    logger.info("⏱️ DEMO: Adaptive Timeout Management")
    logger.info("=" * 50)
    
    from src.infrastructure.resilience import get_timeout_registry, TimeoutConfig, TimeoutStrategy
    
    # Get timeout registry
    timeout_registry = get_timeout_registry()
    
    # Create timeout config with graceful degradation
    timeout_config = TimeoutConfig(
        initial_timeout=2.0,
        strategy=TimeoutStrategy.GRACEFUL_DEGRADATION
    )
    
    logger.info(f"Initial timeout: {timeout_config.initial_timeout}s")
    
    # Test adaptive timeout adjustment
    for round_num in range(3):
        logger.info(f"\nRound {round_num + 1}:")
        
        for i in range(5):
            result = await timeout_registry.execute_with_adaptive_timeout(
                "demo_timeout_service",
                simulate_slow_service,
                f"timeout_demo_{i}",
                operation_name="slow_service_call",
                config=timeout_config,
                fallback_function=lambda name: fallback_service_response(name)
            )
            
            if result.success:
                if result.fallback_used:
                    logger.info(f"  Request {i}: ⚠️ Timeout -> Fallback used ({result.elapsed_ms:.1f}ms)")
                else:
                    logger.info(f"  Request {i}: ✅ Success ({result.elapsed_ms:.1f}ms)")
            else:
                logger.info(f"  Request {i}: ❌ Failed ({result.elapsed_ms:.1f}ms)")
        
        # Show current timeout stats
        stats = timeout_registry.get_all_stats()
        if "demo_timeout_service" in stats['managers']:
            manager_stats = stats['managers']['demo_timeout_service']
            logger.info(f"  Current timeout: {manager_stats['current_timeout']:.1f}s")
            logger.info(f"  Timeout rate: {manager_stats['timeout_rate']:.2%}")
    
    logger.info("")


async def demo_combined_resilience():
    """Demonstrate combined resilience patterns"""
    logger.info("🛡️ DEMO: Combined Resilience Patterns")
    logger.info("=" * 50)
    
    from src.infrastructure.resilience import get_resilience_manager, CircuitBreakerConfig, RetryConfig, BulkheadConfig
    
    # Get resilience manager
    resilience_manager = get_resilience_manager()
    
    logger.info("Testing service with ALL resilience patterns...")
    
    # Execute with all resilience patterns
    for i in range(5):
        try:
            start_time = time.time()
            
            result = await resilience_manager.execute_with_resilience(
                service_name="combined_demo",
                func=simulate_unreliable_service,
                "combined_service",
                failure_rate=0.4,
                circuit_config=CircuitBreakerConfig(failure_threshold=2, recovery_timeout=5),
                retry_config=RetryConfig(max_attempts=3, base_delay=0.5),
                bulkhead_config=BulkheadConfig(max_concurrent=2, queue_size=3)
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Request {i+1}: ✅ Success in {elapsed:.2f}s - {result['data']}")
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.info(f"Request {i+1}: ❌ Failed in {elapsed:.2f}s - {e}")
        
        await asyncio.sleep(0.5)
    
    # Show combined stats
    stats = resilience_manager.get_all_stats()
    logger.info(f"\nCombined resilience stats:")
    logger.info(f"  Circuit breakers: {stats['summary']['total_circuit_breakers']}")
    logger.info(f"  Open circuits: {stats['summary']['open_circuits']}")
    logger.info(f"  Retry mechanisms: {stats['summary']['total_retry_mechanisms']}")
    logger.info(f"  Bulkheads: {stats['summary']['total_bulkheads']}")
    
    logger.info("")


async def demo_health_integration():
    """Demonstrate health monitoring integration with resilience"""
    logger.info("🏥 DEMO: Health Monitoring Integration")
    logger.info("=" * 50)
    
    from src.infrastructure.resilience import get_comprehensive_health_status
    
    try:
        # Get comprehensive health status
        health_status = await get_comprehensive_health_status()
        
        logger.info(f"Overall health level: {health_status['overall_health_level']}")
        
        # Show resilience health
        resilience_health = health_status['resilience_health']
        logger.info(f"Resilience status: {resilience_health['status']}")
        logger.info(f"Resilience message: {resilience_health['message']}")
        
        # Show recommendations
        recommendations = health_status.get('recommendations', [])
        if recommendations:
            logger.info("\nHealth recommendations:")
            for rec in recommendations:
                logger.info(f"  {rec}")
        
        # Show external services health
        external_health = health_status.get('external_services_health', {})
        if 'summary' in external_health:
            summary = external_health['summary']
            logger.info(f"\nExternal services: {summary['healthy_services']}/{summary['total_services']} healthy")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    
    logger.info("")


async def main():
    """Run all resilience pattern demos"""
    logger.info("🚀 ATHintel Resilience Patterns Demo")
    logger.info("=" * 60)
    logger.info("Demonstrating comprehensive fault tolerance patterns")
    logger.info("")
    
    try:
        # Run individual pattern demos
        await demo_circuit_breaker_pattern()
        await demo_retry_mechanism()
        await demo_bulkhead_pattern()
        await demo_adaptive_timeout()
        
        # Run combined demo
        await demo_combined_resilience()
        
        # Show health integration
        await demo_health_integration()
        
        logger.info("🎉 All demos completed successfully!")
        logger.info("Resilience patterns are ready for production use.")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("\n🧹 Cleaning up demo resources...")
        
        # Close any open connections
        try:
            from src.infrastructure.resilience import get_external_service_client
            client = await get_external_service_client()
            await client.close()
        except:
            pass  # Ignore cleanup errors


if __name__ == "__main__":
    asyncio.run(main())