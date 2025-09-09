"""
🛡️ Infrastructure Resilience Module

Comprehensive resilience patterns for production-ready fault tolerance:

- Circuit Breaker Pattern: Prevents cascading failures
- Retry Mechanisms: Exponential backoff with jitter
- Bulkhead Pattern: Resource isolation 
- Timeout Management: Adaptive timeouts with graceful degradation
- External Service Client: Resilient API integrations
"""

from .circuit_breaker import (
    # Circuit Breaker
    CircuitBreaker,
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    
    # Retry Mechanism
    RetryMechanism, 
    RetryConfig,
    
    # Bulkhead Pattern
    Bulkhead,
    BulkheadConfig,
    BulkheadRejectedException,
    BulkheadTimeoutException,
    
    # Combined Manager
    ResilienceManager,
    get_resilience_manager,
    
    # Convenience Functions
    with_circuit_breaker,
    with_retry,
    with_bulkhead,
    with_full_resilience
)

from .timeout_manager import (
    # Timeout Management
    AdaptiveTimeoutManager,
    TimeoutConfig,
    TimeoutStrategy,
    TimeoutResult,
    
    # Cascade Protection
    CascadeTimeoutManager,
    
    # Registry
    TimeoutManagerRegistry,
    get_timeout_registry,
    
    # Convenience Functions
    execute_with_timeout,
    execute_with_graceful_degradation,
    
    # Decorators
    with_adaptive_timeout,
    with_graceful_degradation
)

from .external_service_client import (
    # Client Classes
    ExternalServiceClient,
    ServiceEndpoint,
    ServiceType,
    ApiResponse,
    
    # Global Client
    get_external_service_client,
    
    # Greek Market APIs
    get_energy_data,
    get_property_valuation, 
    get_government_subsidies,
    get_weather_data
)

# Version info
__version__ = "1.0.0"
__author__ = "ATHintel Energy Assessment Platform"

# Module exports
__all__ = [
    # Circuit Breaker
    'CircuitBreaker',
    'CircuitState', 
    'CircuitBreakerConfig',
    'CircuitBreakerOpenError',
    
    # Retry
    'RetryMechanism',
    'RetryConfig', 
    
    # Bulkhead
    'Bulkhead',
    'BulkheadConfig',
    'BulkheadRejectedException',
    'BulkheadTimeoutException',
    
    # Resilience Manager
    'ResilienceManager',
    'get_resilience_manager',
    
    # Timeout Management
    'AdaptiveTimeoutManager',
    'TimeoutConfig',
    'TimeoutStrategy', 
    'TimeoutResult',
    'CascadeTimeoutManager',
    'TimeoutManagerRegistry',
    'get_timeout_registry',
    
    # External Service Client
    'ExternalServiceClient',
    'ServiceEndpoint',
    'ServiceType',
    'ApiResponse',
    'get_external_service_client',
    
    # Convenience Functions
    'with_circuit_breaker',
    'with_retry', 
    'with_bulkhead',
    'with_full_resilience',
    'execute_with_timeout',
    'execute_with_graceful_degradation',
    
    # Decorators
    'with_adaptive_timeout',
    'with_graceful_degradation',
    
    # Greek Market APIs
    'get_energy_data',
    'get_property_valuation',
    'get_government_subsidies',
    'get_weather_data',
]