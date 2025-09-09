"""
Resilience Testing Suite for Circuit Breaker Patterns
Tests fault tolerance, recovery mechanisms, and system stability
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import random

from src.infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitState
from src.infrastructure.resilience.retry_policies import RetryPolicy, ExponentialBackoff
from src.infrastructure.resilience.external_service_client import ExternalServiceClient


class CircuitBreakerTestState(Enum):
    """Test states for circuit breaker"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ResilienceTestMetrics:
    """Metrics for resilience testing"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    circuit_breaker_opens: int
    circuit_breaker_closes: int
    total_downtime_seconds: float
    recovery_time_seconds: float
    success_rate: float


class MockFailingService:
    """Mock service that can be configured to fail"""
    
    def __init__(self, failure_rate: float = 0.0, failure_duration: float = 0.0):
        self.failure_rate = failure_rate
        self.failure_duration = failure_duration
        self.start_time = time.time()
        self.call_count = 0
        
    async def call_service(self, *args, **kwargs):
        """Simulate service call with configurable failures"""
        self.call_count += 1
        elapsed = time.time() - self.start_time
        
        # Simulate temporary failure period
        if elapsed < self.failure_duration:
            raise ConnectionError("Service temporarily unavailable")
        
        # Simulate random failures based on failure rate
        if random.random() < self.failure_rate:
            raise TimeoutError("Service timeout")
        
        # Simulate processing time
        await asyncio.sleep(0.01)
        return {"result": "success", "call_count": self.call_count}


class TestCircuitBreakerBasicFunctionality:
    """Test basic circuit breaker functionality"""

    @pytest.fixture
    def circuit_breaker(self):
        """Circuit breaker with test configuration"""
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1.0,
            success_threshold=2
        )

    @pytest.fixture
    def failing_service(self):
        """Mock service that always fails"""
        service = MockFailingService(failure_rate=1.0)
        return service

    @pytest.fixture 
    def recovering_service(self):
        """Mock service that fails initially then recovers"""
        service = MockFailingService(failure_rate=0.0, failure_duration=2.0)
        return service

    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state (normal operation)"""
        
        async def successful_operation():
            await asyncio.sleep(0.01)
            return "success"
        
        # Initially should be closed
        assert circuit_breaker.state == CircuitState.CLOSED
        
        # Successful calls should work normally
        for _ in range(10):
            result = await circuit_breaker.call(successful_operation)
            assert result == "success"
        
        # Should remain closed after successful calls
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0

    async def test_circuit_breaker_opens_on_failures(self, circuit_breaker, failing_service):
        """Test circuit breaker opens after failure threshold is reached"""
        
        failure_count = 0
        
        # Make calls that will fail
        for i in range(5):
            try:
                await circuit_breaker.call(failing_service.call_service)
                assert False, "Expected failure"
            except Exception:
                failure_count += 1
                
                # Circuit should open after threshold failures
                if i >= circuit_breaker.failure_threshold - 1:
                    assert circuit_breaker.state == CircuitState.OPEN
                else:
                    assert circuit_breaker.state == CircuitState.CLOSED
        
        assert failure_count == 5
        assert circuit_breaker.failure_count >= circuit_breaker.failure_threshold

    async def test_circuit_breaker_open_state_behavior(self, circuit_breaker, failing_service):
        """Test circuit breaker behavior when open"""
        
        # Force circuit to open by triggering failures
        for _ in range(circuit_breaker.failure_threshold):
            try:
                await circuit_breaker.call(failing_service.call_service)
            except Exception:
                pass
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Calls should fail fast when circuit is open
        start_time = time.perf_counter()
        
        try:
            await circuit_breaker.call(failing_service.call_service)
            assert False, "Expected circuit open exception"
        except circuit_breaker.CircuitOpenError:
            pass
        
        elapsed = time.perf_counter() - start_time
        
        # Should fail fast (much quicker than actual service call)
        assert elapsed < 0.01, f"Circuit breaker didn't fail fast: {elapsed:.3f}s"

    async def test_circuit_breaker_half_open_transition(self, circuit_breaker, recovering_service):
        """Test transition from open to half-open state"""
        
        # Force circuit to open
        for _ in range(circuit_breaker.failure_threshold):
            try:
                await circuit_breaker.call(recovering_service.call_service)
            except Exception:
                pass
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(circuit_breaker.recovery_timeout + 0.1)
        
        # Next call should transition to half-open
        try:
            result = await circuit_breaker.call(recovering_service.call_service)
            # Service should succeed now (past failure duration)
            assert result["result"] == "success"
            # But circuit should still be half-open after first success
            assert circuit_breaker.state == CircuitState.HALF_OPEN
        except Exception:
            # If it fails, should go back to open
            assert circuit_breaker.state == CircuitState.OPEN

    async def test_circuit_breaker_recovery(self, circuit_breaker, recovering_service):
        """Test complete circuit breaker recovery cycle"""
        
        # Force circuit to open with initial failures
        for _ in range(circuit_breaker.failure_threshold):
            try:
                await circuit_breaker.call(recovering_service.call_service)
            except Exception:
                pass
        
        assert circuit_breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(circuit_breaker.recovery_timeout + 0.5)
        
        # Make successful calls to close circuit
        success_count = 0
        for i in range(circuit_breaker.success_threshold + 1):
            try:
                result = await circuit_breaker.call(recovering_service.call_service)
                assert result["result"] == "success"
                success_count += 1
                
                # After success threshold, circuit should close
                if i >= circuit_breaker.success_threshold - 1:
                    assert circuit_breaker.state == CircuitState.CLOSED
                else:
                    assert circuit_breaker.state == CircuitState.HALF_OPEN
                    
            except Exception as e:
                pytest.fail(f"Unexpected failure during recovery: {e}")
        
        assert success_count == circuit_breaker.success_threshold + 1
        assert circuit_breaker.state == CircuitState.CLOSED

    async def test_circuit_breaker_metrics(self, circuit_breaker):
        """Test circuit breaker metrics collection"""
        
        # Mix of successful and failing calls
        successful_service = MockFailingService(failure_rate=0.0)
        failing_service = MockFailingService(failure_rate=1.0)
        
        # Make some successful calls
        for _ in range(5):
            await circuit_breaker.call(successful_service.call_service)
        
        # Make some failing calls
        for _ in range(3):
            try:
                await circuit_breaker.call(failing_service.call_service)
            except Exception:
                pass
        
        metrics = circuit_breaker.get_metrics()
        
        # Verify metrics
        assert metrics['total_calls'] == 8
        assert metrics['successful_calls'] == 5
        assert metrics['failed_calls'] == 3
        assert metrics['current_state'] == CircuitState.OPEN.value  # Should be open after 3 failures
        assert 'failure_rate' in metrics
        assert 'avg_response_time' in metrics

    async def test_circuit_breaker_concurrent_access(self, circuit_breaker):
        """Test circuit breaker under concurrent access"""
        
        service = MockFailingService(failure_rate=0.2)  # 20% failure rate
        concurrent_requests = 50
        
        async def make_request():
            try:
                result = await circuit_breaker.call(service.call_service)
                return {'success': True, 'result': result}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Execute concurrent requests
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        # Analyze results
        successful = sum(1 for r in results if r['success'])
        failed = sum(1 for r in results if not r['success'])
        
        assert successful + failed == concurrent_requests
        
        # Circuit breaker should handle concurrent access properly
        final_metrics = circuit_breaker.get_metrics()
        assert final_metrics['total_calls'] == concurrent_requests

    async def test_circuit_breaker_timeout_handling(self, circuit_breaker):
        """Test circuit breaker with timeout scenarios"""
        
        async def slow_service():
            await asyncio.sleep(2.0)  # Slow service
            return "success"
        
        # Configure circuit breaker with timeout
        circuit_with_timeout = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1.0,
            call_timeout=0.5  # 500ms timeout
        )
        
        # Calls should timeout and count as failures
        timeout_count = 0
        
        for _ in range(3):
            try:
                await circuit_with_timeout.call(slow_service)
            except asyncio.TimeoutError:
                timeout_count += 1
            except circuit_with_timeout.CircuitOpenError:
                # Circuit opened due to timeouts
                break
        
        assert timeout_count >= circuit_with_timeout.failure_threshold
        assert circuit_with_timeout.state == CircuitState.OPEN


class TestRetryPolicies:
    """Test retry policy implementations"""

    @pytest.fixture
    def exponential_backoff(self):
        """Exponential backoff retry policy"""
        return ExponentialBackoff(
            max_retries=3,
            initial_delay=0.1,
            max_delay=2.0,
            exponential_base=2.0
        )

    @pytest.fixture
    def linear_backoff(self):
        """Linear backoff retry policy"""
        return RetryPolicy(
            max_retries=3,
            delay_strategy='linear',
            initial_delay=0.1,
            delay_increment=0.1
        )

    async def test_exponential_backoff_delays(self, exponential_backoff):
        """Test exponential backoff delay calculation"""
        
        expected_delays = [0.1, 0.2, 0.4]  # Exponential: 0.1 * 2^n
        actual_delays = []
        
        for attempt in range(3):
            delay = exponential_backoff.calculate_delay(attempt)
            actual_delays.append(delay)
        
        for expected, actual in zip(expected_delays, actual_delays):
            assert abs(actual - expected) < 0.01, f"Delay mismatch: expected {expected}, got {actual}"

    async def test_exponential_backoff_max_delay(self):
        """Test exponential backoff respects max delay"""
        
        backoff = ExponentialBackoff(
            max_retries=10,
            initial_delay=0.5,
            max_delay=2.0,
            exponential_base=2.0
        )
        
        # Later attempts should not exceed max delay
        for attempt in range(5, 10):
            delay = backoff.calculate_delay(attempt)
            assert delay <= backoff.max_delay, f"Delay {delay} exceeds max {backoff.max_delay} at attempt {attempt}"

    async def test_retry_policy_with_failing_service(self, exponential_backoff):
        """Test retry policy with a failing service"""
        
        failing_service = MockFailingService(failure_rate=0.7)  # 70% failure rate
        
        retry_attempts = []
        
        async def tracked_service_call():
            retry_attempts.append(time.time())
            return await failing_service.call_service()
        
        start_time = time.time()
        
        try:
            result = await exponential_backoff.execute_with_retry(tracked_service_call)
            # If successful, verify result
            assert result["result"] == "success"
        except Exception:
            # Expected to fail sometimes with 70% failure rate
            pass
        
        elapsed = time.time() - start_time
        
        # Should have made multiple attempts
        assert len(retry_attempts) > 1, "Should have retried"
        assert len(retry_attempts) <= exponential_backoff.max_retries + 1, "Should not exceed max retries"
        
        # Should have delays between attempts
        if len(retry_attempts) > 1:
            delay_between_attempts = retry_attempts[1] - retry_attempts[0]
            assert delay_between_attempts >= exponential_backoff.initial_delay * 0.9, "Should have initial delay"

    async def test_retry_policy_success_after_failures(self, exponential_backoff):
        """Test retry policy succeeds after initial failures"""
        
        # Service that fails first 2 attempts then succeeds
        call_count = 0
        
        async def eventually_successful_service():
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                raise ConnectionError(f"Attempt {call_count} failed")
            
            return {"result": "success", "attempt": call_count}
        
        result = await exponential_backoff.execute_with_retry(eventually_successful_service)
        
        assert result["result"] == "success"
        assert result["attempt"] == 3  # Should succeed on 3rd attempt
        assert call_count == 3

    async def test_retry_policy_gives_up_after_max_retries(self, exponential_backoff):
        """Test retry policy gives up after max retries"""
        
        always_failing_service = MockFailingService(failure_rate=1.0)
        
        with pytest.raises(Exception):  # Should eventually give up
            await exponential_backoff.execute_with_retry(always_failing_service.call_service)

    async def test_jitter_in_retry_delays(self):
        """Test jitter is applied to retry delays"""
        
        backoff_with_jitter = ExponentialBackoff(
            max_retries=5,
            initial_delay=1.0,
            max_delay=10.0,
            jitter=True
        )
        
        delays = []
        for attempt in range(5):
            delay = backoff_with_jitter.calculate_delay(attempt)
            delays.append(delay)
        
        # With jitter, delays should vary
        assert len(set(delays)) > 1, "Delays should vary with jitter"
        
        # But should still be in reasonable range
        for delay in delays:
            assert 0.5 <= delay <= 10.0, f"Delay {delay} out of reasonable range"


class TestExternalServiceClient:
    """Test external service client with resilience patterns"""

    @pytest.fixture
    def resilient_client(self):
        """External service client with resilience patterns"""
        return ExternalServiceClient(
            base_url="https://api.example.com",
            circuit_breaker_config={
                'failure_threshold': 3,
                'recovery_timeout': 2.0,
                'success_threshold': 2
            },
            retry_config={
                'max_retries': 3,
                'initial_delay': 0.1,
                'max_delay': 1.0,
                'exponential_base': 2.0
            },
            timeout=5.0
        )

    async def test_client_successful_requests(self, resilient_client):
        """Test client with successful external service responses"""
        
        # Mock successful HTTP responses
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"data": "success"}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            result = await resilient_client.get("/test/endpoint")
            
            assert result["data"] == "success"
            assert mock_request.call_count == 1

    async def test_client_retry_on_transient_failures(self, resilient_client):
        """Test client retries on transient failures"""
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            # First two calls fail, third succeeds
            mock_responses = [
                AsyncMock(status=503),  # Service unavailable
                AsyncMock(status=502),  # Bad gateway
                AsyncMock(status=200)   # Success
            ]
            
            for i, mock_response in enumerate(mock_responses):
                if i < 2:
                    mock_response.raise_for_status.side_effect = Exception("Server error")
                else:
                    mock_response.json.return_value = {"data": "success"}
            
            mock_request.return_value.__aenter__.side_effect = mock_responses
            
            result = await resilient_client.get("/test/endpoint")
            
            assert result["data"] == "success"
            assert mock_request.call_count == 3  # Should have retried

    async def test_client_circuit_breaker_integration(self, resilient_client):
        """Test client circuit breaker integration"""
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            # Always return server error
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_response.raise_for_status.side_effect = Exception("Server error")
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Make requests until circuit breaker opens
            failure_count = 0
            circuit_open_count = 0
            
            for i in range(10):
                try:
                    await resilient_client.get("/test/endpoint")
                except resilient_client.CircuitOpenError:
                    circuit_open_count += 1
                except Exception:
                    failure_count += 1
            
            # Should have some failures that triggered circuit to open
            assert failure_count > 0, "Should have some failures"
            # Should have some circuit open errors after threshold reached
            assert circuit_open_count > 0, "Circuit breaker should have opened"

    async def test_client_timeout_handling(self, resilient_client):
        """Test client timeout handling"""
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            # Simulate timeout
            mock_request.side_effect = asyncio.TimeoutError("Request timeout")
            
            start_time = time.perf_counter()
            
            with pytest.raises(asyncio.TimeoutError):
                await resilient_client.get("/slow/endpoint")
            
            elapsed = time.perf_counter() - start_time
            
            # Should respect timeout setting (with retries, might take longer)
            assert elapsed < resilient_client.timeout * (resilient_client.max_retries + 1) * 1.5

    async def test_client_rate_limiting(self):
        """Test client rate limiting functionality"""
        
        rate_limited_client = ExternalServiceClient(
            base_url="https://api.example.com",
            rate_limit={'requests_per_second': 2}  # 2 requests per second
        )
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"data": "success"}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # Make multiple requests
            start_time = time.perf_counter()
            
            for _ in range(4):
                await rate_limited_client.get("/test")
            
            elapsed = time.perf_counter() - start_time
            
            # Should take at least 1.5 seconds for 4 requests at 2/sec
            assert elapsed >= 1.5, f"Rate limiting not working: {elapsed:.2f}s for 4 requests"

    async def test_client_metrics_collection(self, resilient_client):
        """Test client metrics collection"""
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            # Mix of successful and failed responses
            responses = [
                AsyncMock(status=200),  # Success
                AsyncMock(status=200),  # Success  
                AsyncMock(status=500),  # Error
                AsyncMock(status=200),  # Success
            ]
            
            for i, response in enumerate(responses):
                if i == 2:  # Third response fails
                    response.raise_for_status.side_effect = Exception("Server error")
                else:
                    response.json.return_value = {"data": f"success_{i}"}
            
            mock_request.return_value.__aenter__.side_effect = responses
            
            # Make requests
            results = []
            for i in range(4):
                try:
                    result = await resilient_client.get(f"/test/{i}")
                    results.append(result)
                except Exception:
                    results.append(None)
            
            # Check metrics
            metrics = resilient_client.get_metrics()
            
            assert metrics['total_requests'] == 4
            assert metrics['successful_requests'] == 3
            assert metrics['failed_requests'] == 1
            assert 'avg_response_time' in metrics
            assert 'success_rate' in metrics


class TestResilienceIntegration:
    """Integration tests for resilience patterns"""

    async def test_cascading_failure_prevention(self):
        """Test prevention of cascading failures across services"""
        
        # Set up multiple services with circuit breakers
        service_a = ExternalServiceClient(
            base_url="https://service-a.com",
            circuit_breaker_config={'failure_threshold': 2, 'recovery_timeout': 1.0}
        )
        
        service_b = ExternalServiceClient(
            base_url="https://service-b.com", 
            circuit_breaker_config={'failure_threshold': 2, 'recovery_timeout': 1.0}
        )
        
        # Mock service A failing, service B healthy
        with patch('aiohttp.ClientSession.request') as mock_request:
            def side_effect(*args, **kwargs):
                url = str(args[1]) if len(args) > 1 else kwargs.get('url', '')
                
                if 'service-a' in url:
                    # Service A always fails
                    response = AsyncMock()
                    response.status = 500
                    response.raise_for_status.side_effect = Exception("Service A down")
                    return response
                else:
                    # Service B succeeds
                    response = AsyncMock()
                    response.status = 200
                    response.json.return_value = {"data": "service_b_success"}
                    return response
            
            mock_request.return_value.__aenter__.side_effect = side_effect
            
            # Make requests to both services
            service_a_failures = 0
            service_b_successes = 0
            
            for i in range(10):
                # Try service A
                try:
                    await service_a.get("/endpoint")
                except Exception:
                    service_a_failures += 1
                
                # Try service B
                try:
                    result = await service_b.get("/endpoint")
                    if result and result.get("data") == "service_b_success":
                        service_b_successes += 1
                except Exception:
                    pass
            
            # Service A should fail and circuit should open
            assert service_a_failures >= service_a.circuit_breaker.failure_threshold
            assert service_a.circuit_breaker.state == CircuitState.OPEN
            
            # Service B should continue working (no cascading failure)
            assert service_b_successes > 5  # Most requests should succeed
            assert service_b.circuit_breaker.state == CircuitState.CLOSED

    async def test_bulkhead_isolation(self):
        """Test bulkhead pattern isolates failures"""
        
        # Simulate resource pools for different operations
        class ResourcePool:
            def __init__(self, pool_size: int):
                self.pool_size = pool_size
                self.in_use = 0
                self.semaphore = asyncio.Semaphore(pool_size)
            
            async def acquire(self):
                await self.semaphore.acquire()
                self.in_use += 1
            
            def release(self):
                self.semaphore.release()
                self.in_use -= 1
            
            @property
            def available(self):
                return self.pool_size - self.in_use
        
        # Separate pools for different operations
        search_pool = ResourcePool(5)
        analysis_pool = ResourcePool(3)
        
        async def search_operation(fail: bool = False):
            await search_pool.acquire()
            try:
                await asyncio.sleep(0.1)
                if fail:
                    raise Exception("Search failed")
                return "search_success"
            finally:
                search_pool.release()
        
        async def analysis_operation(fail: bool = False):
            await analysis_pool.acquire()
            try:
                await asyncio.sleep(0.1)
                if fail:
                    raise Exception("Analysis failed")
                return "analysis_success"
            finally:
                analysis_pool.release()
        
        # Flood search operations (some failing)
        search_tasks = []
        for i in range(10):
            task = search_operation(fail=(i % 3 == 0))  # Every 3rd search fails
            search_tasks.append(task)
        
        # Normal analysis operations
        analysis_tasks = []
        for i in range(5):
            task = analysis_operation(fail=False)
            analysis_tasks.append(task)
        
        # Execute concurrently
        all_tasks = search_tasks + analysis_tasks
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Count results
        search_results = results[:10]
        analysis_results = results[10:]
        
        search_successes = sum(1 for r in search_results if r == "search_success")
        analysis_successes = sum(1 for r in analysis_results if r == "analysis_success")
        
        # Analysis operations should not be affected by search failures
        assert analysis_successes == 5, "Analysis operations should not be affected by search failures"
        
        # Some search operations should fail, but not all
        assert 0 < search_successes < 10, "Some search operations should succeed despite failures"

    async def test_graceful_degradation(self):
        """Test graceful degradation when services are unavailable"""
        
        class PropertyService:
            def __init__(self):
                self.cache = {}
                self.external_client = ExternalServiceClient(
                    base_url="https://external-api.com",
                    circuit_breaker_config={'failure_threshold': 2, 'recovery_timeout': 1.0}
                )
            
            async def get_property_details(self, property_id: str):
                """Get property details with fallback to cached data"""
                
                # Try external service first
                try:
                    result = await self.external_client.get(f"/properties/{property_id}")
                    # Update cache on success
                    self.cache[property_id] = result
                    return {**result, "source": "external_api", "fresh": True}
                
                except Exception:
                    # Fall back to cache
                    if property_id in self.cache:
                        return {**self.cache[property_id], "source": "cache", "fresh": False}
                    
                    # Last resort: minimal data
                    return {
                        "property_id": property_id,
                        "status": "limited_data",
                        "source": "fallback",
                        "fresh": False
                    }
        
        service = PropertyService()
        
        # Pre-populate cache
        service.cache["prop_123"] = {"id": "prop_123", "name": "Cached Property"}
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            # External service is down
            mock_request.side_effect = Exception("Service unavailable")
            
            # Request should fall back to cache
            result = await service.get_property_details("prop_123")
            
            assert result["source"] == "cache"
            assert result["fresh"] is False
            assert result["name"] == "Cached Property"
            
            # Request for unknown property should return fallback
            unknown_result = await service.get_property_details("unknown_prop")
            
            assert unknown_result["source"] == "fallback" 
            assert unknown_result["status"] == "limited_data"

    @pytest.mark.slow
    async def test_system_recovery_after_outage(self):
        """Test system recovery after complete outage"""
        
        # Simulate complete system outage and recovery
        outage_duration = 2.0  # 2 seconds
        recovery_delay = 0.5   # 0.5 seconds
        
        class OutageSimulator:
            def __init__(self):
                self.start_time = time.time()
                self.outage_duration = outage_duration
                self.recovery_delay = recovery_delay
            
            def is_service_available(self):
                elapsed = time.time() - self.start_time
                
                # Service is down for outage_duration
                if elapsed < self.outage_duration:
                    return False
                
                # Service is recovering (partial availability)
                if elapsed < self.outage_duration + self.recovery_delay:
                    return random.random() > 0.5  # 50% availability during recovery
                
                # Service is fully recovered
                return True
        
        simulator = OutageSimulator()
        
        circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=0.5,
            success_threshold=2
        )
        
        async def service_call():
            if simulator.is_service_available():
                await asyncio.sleep(0.01)
                return "success"
            else:
                raise Exception("Service unavailable")
        
        # Track system behavior during outage and recovery
        start_time = time.time()
        test_duration = outage_duration + recovery_delay + 1.0  # Total test time
        
        metrics = ResilienceTestMetrics(
            total_requests=0,
            successful_requests=0,
            failed_requests=0,
            circuit_breaker_opens=0,
            circuit_breaker_closes=0,
            total_downtime_seconds=0,
            recovery_time_seconds=0,
            success_rate=0
        )
        
        downtime_start = None
        recovery_start = None
        
        while time.time() - start_time < test_duration:
            metrics.total_requests += 1
            
            try:
                await circuit_breaker.call(service_call)
                metrics.successful_requests += 1
                
                # Track recovery
                if recovery_start is None and metrics.successful_requests > 0:
                    recovery_start = time.time()
                    if downtime_start:
                        metrics.total_downtime_seconds = recovery_start - downtime_start
                
            except circuit_breaker.CircuitOpenError:
                metrics.failed_requests += 1
                # Circuit is open - track downtime
                if downtime_start is None:
                    downtime_start = time.time()
                    metrics.circuit_breaker_opens += 1
                    
            except Exception:
                metrics.failed_requests += 1
            
            # Check if circuit closed after being open
            if (circuit_breaker.state == CircuitState.CLOSED and 
                metrics.circuit_breaker_opens > 0 and
                metrics.circuit_breaker_closes == 0):
                metrics.circuit_breaker_closes += 1
                
                if recovery_start:
                    metrics.recovery_time_seconds = time.time() - recovery_start
            
            await asyncio.sleep(0.1)  # Test every 100ms
        
        # Calculate final metrics
        metrics.success_rate = (metrics.successful_requests / metrics.total_requests) * 100
        
        # Assertions for recovery behavior
        assert metrics.circuit_breaker_opens > 0, "Circuit breaker should have opened during outage"
        assert metrics.circuit_breaker_closes > 0, "Circuit breaker should have closed after recovery"
        assert metrics.total_downtime_seconds > 0, "Should track downtime period"
        assert metrics.recovery_time_seconds < recovery_delay + 1.0, "Recovery should be reasonably fast"
        
        # Final success rate should be reasonable after recovery
        assert metrics.success_rate > 30, f"Final success rate too low: {metrics.success_rate:.1f}%"