"""
🌐 External Service Client with Resilience Patterns

Production-ready client for external API integrations with comprehensive
fault tolerance, monitoring, and Greek energy market specific services:

- Energy API providers (HEDNO, DAPEEP, EU databases)
- Property valuation services
- Market data providers  
- Government subsidy APIs (Εξοικονομώ programs)
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import ssl
import certifi
from urllib.parse import urljoin, urlencode

from .circuit_breaker import (
    ResilienceManager, 
    CircuitBreakerConfig, 
    RetryConfig, 
    BulkheadConfig,
    get_resilience_manager
)
from config.production_config import get_config

logger = logging.getLogger(__name__)


class ServiceType(Enum):
    """External service types"""
    ENERGY_DATA = "energy_data"
    PROPERTY_VALUATION = "property_valuation" 
    MARKET_DATA = "market_data"
    GOVERNMENT_API = "government_api"
    WEATHER_API = "weather_api"


@dataclass
class ServiceEndpoint:
    """External service endpoint configuration"""
    name: str
    base_url: str
    service_type: ServiceType
    api_key: Optional[str] = None
    timeout_seconds: float = 30.0
    rate_limit_per_minute: int = 60
    requires_auth: bool = True
    health_check_path: str = "/health"
    
    # Resilience configurations
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    retry_config: Optional[RetryConfig] = None
    bulkhead_config: Optional[BulkheadConfig] = None


@dataclass
class ApiResponse:
    """Standardized API response"""
    success: bool
    data: Any
    status_code: int
    response_time_ms: float
    service_name: str
    timestamp: datetime
    error_message: Optional[str] = None
    cached: bool = False


class ExternalServiceClient:
    """
    Production-ready external service client with resilience patterns
    """
    
    def __init__(self):
        self.config = get_config()
        self.resilience_manager = get_resilience_manager()
        
        # SSL context for secure connections
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Session with connection pooling
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Service configurations
        self.services = self._initialize_service_configs()
        
        # Request cache for GET requests
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds = 300  # 5 minutes
        
        # Rate limiting
        self.rate_limiters: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"External service client initialized with {len(self.services)} services")
    
    def _initialize_service_configs(self) -> Dict[str, ServiceEndpoint]:
        """Initialize service endpoint configurations"""
        services = {}
        
        # Greek Energy Market APIs
        if self.config.external_services.hedno_api_key:
            services['hedno'] = ServiceEndpoint(
                name='hedno',
                base_url='https://api.hedno.gr/v1',
                service_type=ServiceType.ENERGY_DATA,
                api_key=self.config.external_services.hedno_api_key,
                timeout_seconds=15.0,
                rate_limit_per_minute=100,
                circuit_breaker_config=CircuitBreakerConfig(
                    failure_threshold=3,
                    recovery_timeout=60,
                    timeout_seconds=15.0
                ),
                retry_config=RetryConfig(
                    max_attempts=3,
                    base_delay=2.0,
                    max_delay=30.0
                ),
                bulkhead_config=BulkheadConfig(
                    max_concurrent=10,
                    queue_size=50
                )
            )
        
        if self.config.external_services.dapeep_api_key:
            services['dapeep'] = ServiceEndpoint(
                name='dapeep',
                base_url='https://api.dapeep.gr/v1',
                service_type=ServiceType.ENERGY_DATA,
                api_key=self.config.external_services.dapeep_api_key,
                timeout_seconds=20.0,
                rate_limit_per_minute=50,
                circuit_breaker_config=CircuitBreakerConfig(
                    failure_threshold=5,
                    recovery_timeout=120,
                    timeout_seconds=20.0
                ),
                retry_config=RetryConfig(
                    max_attempts=2,
                    base_delay=1.5
                ),
                bulkhead_config=BulkheadConfig(
                    max_concurrent=5,
                    queue_size=25
                )
            )
        
        # Property Valuation Services
        if self.config.external_services.spitogatos_api_key:
            services['spitogatos'] = ServiceEndpoint(
                name='spitogatos',
                base_url='https://api.spitogatos.gr/v2',
                service_type=ServiceType.PROPERTY_VALUATION,
                api_key=self.config.external_services.spitogatos_api_key,
                timeout_seconds=10.0,
                rate_limit_per_minute=120,
                circuit_breaker_config=CircuitBreakerConfig(
                    failure_threshold=4,
                    recovery_timeout=45,
                    timeout_seconds=10.0
                ),
                bulkhead_config=BulkheadConfig(
                    max_concurrent=15,
                    queue_size=100
                )
            )
        
        # Government APIs (Εξοικονομώ programs)
        services['minenv'] = ServiceEndpoint(
            name='minenv',
            base_url='https://ypen.gov.gr/api/v1',
            service_type=ServiceType.GOVERNMENT_API,
            timeout_seconds=30.0,
            rate_limit_per_minute=30,
            requires_auth=False,
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=300,  # 5 minutes for government services
                timeout_seconds=30.0
            ),
            retry_config=RetryConfig(
                max_attempts=4,
                base_delay=5.0,
                max_delay=60.0
            ),
            bulkhead_config=BulkheadConfig(
                max_concurrent=3,  # Conservative for government APIs
                queue_size=10
            )
        )
        
        # Weather data for energy calculations
        if self.config.external_services.weather_api_key:
            services['weather'] = ServiceEndpoint(
                name='weather',
                base_url='https://api.openweathermap.org/data/2.5',
                service_type=ServiceType.WEATHER_API,
                api_key=self.config.external_services.weather_api_key,
                timeout_seconds=8.0,
                rate_limit_per_minute=1000,
                circuit_breaker_config=CircuitBreakerConfig(
                    failure_threshold=5,
                    recovery_timeout=30,
                    timeout_seconds=8.0
                ),
                bulkhead_config=BulkheadConfig(
                    max_concurrent=20,
                    queue_size=200
                )
            )
        
        return services
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                ssl=self.ssl_context,
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                keepalive_timeout=30
            )
            
            timeout = aiohttp.ClientTimeout(total=60)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'ATHintel-EnergyAssessment/2.0.0',
                    'Accept': 'application/json'
                }
            )
    
    async def get(
        self,
        service_name: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl_seconds: Optional[int] = None
    ) -> ApiResponse:
        """
        GET request with resilience patterns
        
        Args:
            service_name: Name of the service
            endpoint: API endpoint path
            params: Query parameters
            use_cache: Whether to use response caching
            cache_ttl_seconds: Override cache TTL
            
        Returns:
            API response
        """
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        
        service_config = self.services[service_name]
        
        # Check cache first
        if use_cache:
            cached_response = self._get_cached_response(service_name, endpoint, params)
            if cached_response:
                return cached_response
        
        # Execute with resilience patterns
        response = await self.resilience_manager.execute_with_resilience(
            service_name=f"{service_name}_get",
            func=self._execute_get_request,
            service_config=service_config,
            endpoint=endpoint,
            params=params or {},
            circuit_config=service_config.circuit_breaker_config,
            retry_config=service_config.retry_config,
            bulkhead_config=service_config.bulkhead_config
        )
        
        # Cache successful GET responses
        if use_cache and response.success:
            self._cache_response(
                service_name, 
                endpoint, 
                params, 
                response, 
                cache_ttl_seconds or self.cache_ttl_seconds
            )
        
        return response
    
    async def post(
        self,
        service_name: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> ApiResponse:
        """
        POST request with resilience patterns
        
        Args:
            service_name: Name of the service
            endpoint: API endpoint path
            data: Form data
            json_data: JSON data
            
        Returns:
            API response
        """
        if service_name not in self.services:
            raise ValueError(f"Unknown service: {service_name}")
        
        service_config = self.services[service_name]
        
        # Execute with resilience patterns
        return await self.resilience_manager.execute_with_resilience(
            service_name=f"{service_name}_post",
            func=self._execute_post_request,
            service_config=service_config,
            endpoint=endpoint,
            data=data,
            json_data=json_data,
            circuit_config=service_config.circuit_breaker_config,
            retry_config=service_config.retry_config,
            bulkhead_config=service_config.bulkhead_config
        )
    
    async def _execute_get_request(
        self,
        service_config: ServiceEndpoint,
        endpoint: str,
        params: Dict[str, Any]
    ) -> ApiResponse:
        """Execute GET request"""
        await self._ensure_session()
        
        # SECURITY: Validate authentication for services that require it
        if service_config.requires_auth and (not service_config.api_key or service_config.api_key.strip() == ""):
            return ApiResponse(
                success=False,
                data=None,
                status_code=401,
                response_time_ms=0,
                service_name=service_config.name,
                timestamp=datetime.now(),
                error_message="Authentication required but no valid API key configured"
            )
        
        # Check rate limiting
        await self._check_rate_limit(service_config.name)
        
        # Prepare URL and headers
        url = urljoin(service_config.base_url, endpoint.lstrip('/'))
        if params:
            url = f"{url}?{urlencode(params)}"
        
        headers = {}
        if service_config.requires_auth and service_config.api_key:
            headers['Authorization'] = f'Bearer {service_config.api_key}'
        
        start_time = datetime.now()
        
        try:
            async with self.session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=service_config.timeout_seconds)
            ) as response:
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                return ApiResponse(
                    success=response.status < 400,
                    data=response_data,
                    status_code=response.status,
                    response_time_ms=response_time,
                    service_name=service_config.name,
                    timestamp=start_time,
                    error_message=None if response.status < 400 else f"HTTP {response.status}"
                )
                
        except asyncio.TimeoutError:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return ApiResponse(
                success=False,
                data=None,
                status_code=408,
                response_time_ms=response_time,
                service_name=service_config.name,
                timestamp=start_time,
                error_message=f"Request timeout after {service_config.timeout_seconds}s"
            )
        
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return ApiResponse(
                success=False,
                data=None,
                status_code=0,
                response_time_ms=response_time,
                service_name=service_config.name,
                timestamp=start_time,
                error_message=str(e)
            )
    
    async def _execute_post_request(
        self,
        service_config: ServiceEndpoint,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> ApiResponse:
        """Execute POST request"""
        await self._ensure_session()
        
        # SECURITY: Validate authentication for services that require it
        if service_config.requires_auth and (not service_config.api_key or service_config.api_key.strip() == ""):
            return ApiResponse(
                success=False,
                data=None,
                status_code=401,
                response_time_ms=0,
                service_name=service_config.name,
                timestamp=datetime.now(),
                error_message="Authentication required but no valid API key configured"
            )
        
        # Check rate limiting
        await self._check_rate_limit(service_config.name)
        
        # Prepare URL and headers
        url = urljoin(service_config.base_url, endpoint.lstrip('/'))
        headers = {}
        
        if service_config.requires_auth and service_config.api_key:
            headers['Authorization'] = f'Bearer {service_config.api_key}'
        
        if json_data:
            headers['Content-Type'] = 'application/json'
        
        start_time = datetime.now()
        
        try:
            async with self.session.post(
                url,
                headers=headers,
                data=data,
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=service_config.timeout_seconds)
            ) as response:
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                
                return ApiResponse(
                    success=response.status < 400,
                    data=response_data,
                    status_code=response.status,
                    response_time_ms=response_time,
                    service_name=service_config.name,
                    timestamp=start_time,
                    error_message=None if response.status < 400 else f"HTTP {response.status}"
                )
                
        except asyncio.TimeoutError:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return ApiResponse(
                success=False,
                data=None,
                status_code=408,
                response_time_ms=response_time,
                service_name=service_config.name,
                timestamp=start_time,
                error_message=f"Request timeout after {service_config.timeout_seconds}s"
            )
        
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return ApiResponse(
                success=False,
                data=None,
                status_code=0,
                response_time_ms=response_time,
                service_name=service_config.name,
                timestamp=start_time,
                error_message=str(e)
            )
    
    async def _check_rate_limit(self, service_name: str) -> None:
        """Check and enforce rate limiting"""
        service_config = self.services[service_name]
        
        if service_name not in self.rate_limiters:
            self.rate_limiters[service_name] = {
                'requests': deque(),
                'max_per_minute': service_config.rate_limit_per_minute
            }
        
        rate_limiter = self.rate_limiters[service_name]
        current_time = datetime.now()
        
        # Remove requests older than 1 minute
        cutoff_time = current_time - timedelta(minutes=1)
        while rate_limiter['requests'] and rate_limiter['requests'][0] < cutoff_time:
            rate_limiter['requests'].popleft()
        
        # Check if we're at the limit
        if len(rate_limiter['requests']) >= rate_limiter['max_per_minute']:
            sleep_time = 60.0 / rate_limiter['max_per_minute']
            logger.warning(f"Rate limit reached for {service_name}, sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        # Record this request
        rate_limiter['requests'].append(current_time)
    
    def _get_cached_response(
        self,
        service_name: str,
        endpoint: str,
        params: Optional[Dict[str, Any]]
    ) -> Optional[ApiResponse]:
        """Get cached response if available and not expired"""
        cache_key = self._generate_cache_key(service_name, endpoint, params)
        
        if cache_key in self.response_cache:
            cached_entry = self.response_cache[cache_key]
            
            # Check if cache entry is still valid
            if datetime.now() < cached_entry['expires_at']:
                response = cached_entry['response']
                response.cached = True
                logger.debug(f"Cache hit for {service_name}/{endpoint}")
                return response
            else:
                # Remove expired entry
                del self.response_cache[cache_key]
                logger.debug(f"Cache expired for {service_name}/{endpoint}")
        
        return None
    
    def _cache_response(
        self,
        service_name: str,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        response: ApiResponse,
        cache_ttl_seconds: int
    ) -> None:
        """Cache response"""
        cache_key = self._generate_cache_key(service_name, endpoint, params)
        
        self.response_cache[cache_key] = {
            'response': response,
            'expires_at': datetime.now() + timedelta(seconds=cache_ttl_seconds),
            'cached_at': datetime.now()
        }
        
        # Clean up old cache entries (keep max 1000)
        if len(self.response_cache) > 1000:
            # Remove oldest 100 entries
            oldest_keys = sorted(
                self.response_cache.keys(),
                key=lambda k: self.response_cache[k]['cached_at']
            )[:100]
            
            for key in oldest_keys:
                del self.response_cache[key]
        
        logger.debug(f"Cached response for {service_name}/{endpoint}")
    
    def _generate_cache_key(
        self,
        service_name: str,
        endpoint: str,
        params: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key"""
        params_str = json.dumps(params, sort_keys=True) if params else ""
        return f"{service_name}:{endpoint}:{params_str}"
    
    async def health_check(self, service_name: str) -> Dict[str, Any]:
        """
        Perform health check on external service
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            Health check result
        """
        if service_name not in self.services:
            return {
                'service': service_name,
                'healthy': False,
                'error': 'Unknown service'
            }
        
        service_config = self.services[service_name]
        
        try:
            response = await self.get(
                service_name,
                service_config.health_check_path,
                use_cache=False
            )
            
            return {
                'service': service_name,
                'healthy': response.success,
                'status_code': response.status_code,
                'response_time_ms': response.response_time_ms,
                'timestamp': response.timestamp.isoformat(),
                'error': response.error_message
            }
            
        except Exception as e:
            return {
                'service': service_name,
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Health check all configured services"""
        results = {}
        
        # Run health checks concurrently
        tasks = [
            self.health_check(service_name)
            for service_name in self.services.keys()
        ]
        
        health_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, service_name in enumerate(self.services.keys()):
            result = health_results[i]
            if isinstance(result, Exception):
                results[service_name] = {
                    'service': service_name,
                    'healthy': False,
                    'error': str(result)
                }
            else:
                results[service_name] = result
        
        # Calculate summary
        healthy_services = sum(1 for r in results.values() if r.get('healthy', False))
        
        return {
            'services': results,
            'summary': {
                'total_services': len(self.services),
                'healthy_services': healthy_services,
                'unhealthy_services': len(self.services) - healthy_services,
                'overall_healthy': healthy_services == len(self.services)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        # Get resilience stats
        resilience_stats = self.resilience_manager.get_all_stats()
        
        # Cache stats
        cache_stats = {
            'total_entries': len(self.response_cache),
            'hit_rate': 0,  # Would need to track hits/misses
            'entries_by_service': {}
        }
        
        for cache_key in self.response_cache:
            service = cache_key.split(':')[0]
            cache_stats['entries_by_service'][service] = cache_stats['entries_by_service'].get(service, 0) + 1
        
        # Rate limiter stats
        rate_limiter_stats = {}
        for service_name, limiter in self.rate_limiters.items():
            rate_limiter_stats[service_name] = {
                'current_requests': len(limiter['requests']),
                'max_per_minute': limiter['max_per_minute'],
                'utilization': len(limiter['requests']) / limiter['max_per_minute']
            }
        
        return {
            'services': list(self.services.keys()),
            'resilience': resilience_stats,
            'cache': cache_stats,
            'rate_limiters': rate_limiter_stats,
            'session_active': self.session is not None and not self.session.closed
        }
    
    async def close(self):
        """Close client session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("External service client session closed")


# Global client instance
_external_client = None


async def get_external_service_client() -> ExternalServiceClient:
    """Get or create global external service client"""
    global _external_client
    if _external_client is None:
        _external_client = ExternalServiceClient()
        await _external_client._ensure_session()
    return _external_client


# Convenience functions for Greek energy market APIs
async def get_energy_data(
    provider: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None
) -> ApiResponse:
    """Get energy data from Greek providers (HEDNO, DAPEEP)"""
    client = await get_external_service_client()
    return await client.get(provider, endpoint, params)


async def get_property_valuation(
    location: str,
    property_type: str,
    area: float
) -> ApiResponse:
    """Get property valuation from Spitogatos"""
    client = await get_external_service_client()
    return await client.get('spitogatos', '/valuations', {
        'location': location,
        'type': property_type,
        'area': area
    })


async def get_government_subsidies(
    property_type: str,
    energy_class: str,
    region: str
) -> ApiResponse:
    """Get available government subsidies (Εξοικονομώ programs)"""
    client = await get_external_service_client()
    return await client.get('minenv', '/subsidies', {
        'property_type': property_type,
        'energy_class': energy_class,
        'region': region
    })


async def get_weather_data(
    lat: float,
    lon: float,
    days: int = 7
) -> ApiResponse:
    """Get weather data for energy calculations"""
    client = await get_external_service_client()
    return await client.get('weather', '/forecast', {
        'lat': lat,
        'lon': lon,
        'cnt': days * 8,  # 3-hour intervals
        'units': 'metric'
    })