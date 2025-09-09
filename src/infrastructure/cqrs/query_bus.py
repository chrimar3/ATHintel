"""
🔍 CQRS Query Bus

Query bus implementation for routing and executing queries in the CQRS architecture.
Handles query validation, caching, routing, and result optimization.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Type
from decimal import Decimal
import logging
import hashlib
import json

from .queries import Query, QueryResult, PagedQueryResult
from domains.energy.value_objects.energy_class import EnergyClass

logger = logging.getLogger(__name__)

class QueryHandler:
    """Base class for query handlers"""
    
    async def handle(self, query: Query) -> QueryResult:
        """Handle a query and return result"""
        raise NotImplementedError()

class QueryBusError(Exception):
    """Base exception for query bus errors"""
    pass

class QueryValidationError(QueryBusError):
    """Query validation failed"""
    pass

class QueryHandlerNotFoundError(QueryBusError):
    """No handler found for query type"""
    pass

class QueryCache:
    """Simple in-memory cache for query results"""
    
    def __init__(self, default_ttl_seconds: int = 300):  # 5 minute default TTL
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl_seconds
    
    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if not expired"""
        if cache_key in self._cache:
            cached_item = self._cache[cache_key]
            if datetime.now() < cached_item['expires_at']:
                return cached_item['result']
            else:
                # Remove expired item
                del self._cache[cache_key]
        return None
    
    def set(self, cache_key: str, result: Dict[str, Any], ttl_seconds: Optional[int] = None):
        """Cache a result with TTL"""
        ttl = ttl_seconds or self._default_ttl
        self._cache[cache_key] = {
            'result': result,
            'expires_at': datetime.now() + timedelta(seconds=ttl),
            'created_at': datetime.now()
        }
    
    def clear(self):
        """Clear all cached results"""
        self._cache.clear()
    
    def _generate_cache_key(self, query: Query) -> str:
        """Generate cache key from query parameters"""
        query_data = {
            'type': query.__class__.__name__,
            'params': query.__dict__
        }
        # Remove dynamic fields that shouldn't affect caching
        query_data['params'].pop('query_id', None)
        query_data['params'].pop('requested_at', None)
        
        query_json = json.dumps(query_data, sort_keys=True, default=str)
        return hashlib.md5(query_json.encode()).hexdigest()

class QueryBus:
    """
    Query bus for routing and executing queries
    
    Provides:
    - Query validation
    - Handler routing
    - Result caching
    - Performance optimization
    - Async execution support
    """
    
    def __init__(self, enable_caching: bool = True):
        self._handlers: Dict[Type[Query], QueryHandler] = {}
        self._middleware: List[Callable] = []
        self._cache = QueryCache() if enable_caching else None
        
    def register_handler(self, query_type: Type[Query], handler: QueryHandler):
        """Register a query handler"""
        self._handlers[query_type] = handler
        logger.info(f"Registered query handler for {query_type.__name__}")
    
    def add_middleware(self, middleware: Callable):
        """Add middleware to the processing pipeline"""
        self._middleware.append(middleware)
        logger.info(f"Added query middleware: {middleware.__name__}")
    
    async def execute(self, query: Query, use_cache: bool = True) -> QueryResult:
        """Execute a query and return result"""
        start_time = datetime.now()
        
        try:
            # Set query metadata
            query.query_id = str(uuid.uuid4())
            
            # Validate query
            validation_errors = query.validate()
            if validation_errors:
                return QueryResult(
                    success=False,
                    query_id=query.query_id,
                    validation_errors=validation_errors,
                    execution_time_ms=self._calculate_execution_time(start_time)
                )
            
            # Check cache first if enabled
            cached_result = None
            cache_key = None
            
            if self._cache and use_cache:
                cache_key = self._cache._generate_cache_key(query)
                cached_result = self._cache.get(cache_key)
                
                if cached_result:
                    logger.debug(f"Query {query.__class__.__name__} served from cache")
                    result = QueryResult(**cached_result)
                    result.cached = True
                    result.execution_time_ms = self._calculate_execution_time(start_time)
                    return result
            
            # Apply middleware
            for middleware in self._middleware:
                try:
                    await middleware(query)
                except Exception as e:
                    logger.error(f"Query middleware {middleware.__name__} failed: {e}")
                    return QueryResult(
                        success=False,
                        query_id=query.query_id,
                        execution_time_ms=self._calculate_execution_time(start_time)
                    )
            
            # Find and execute handler
            handler = self._get_handler(query)
            result = await handler.handle(query)
            
            # Set execution metadata
            result.query_id = query.query_id
            result.execution_time_ms = self._calculate_execution_time(start_time)
            result.cached = False
            
            # Cache result if caching is enabled and query was successful
            if self._cache and use_cache and result.success and cache_key:
                cache_ttl = self._get_cache_ttl(query)
                self._cache.set(cache_key, result.__dict__, cache_ttl)
            
            # Log successful execution
            logger.info(f"Query {query.__class__.__name__} executed successfully in {result.execution_time_ms}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}", exc_info=True)
            return QueryResult(
                success=False,
                query_id=query.query_id if hasattr(query, 'query_id') else "unknown",
                execution_time_ms=self._calculate_execution_time(start_time)
            )
    
    def _get_handler(self, query: Query) -> QueryHandler:
        """Get handler for query type"""
        query_type = type(query)
        
        if query_type not in self._handlers:
            available_handlers = list(self._handlers.keys())
            raise QueryHandlerNotFoundError(
                f"No handler registered for query {query_type.__name__}. "
                f"Available handlers: {[h.__name__ for h in available_handlers]}"
            )
        
        return self._handlers[query_type]
    
    def _calculate_execution_time(self, start_time: datetime) -> float:
        """Calculate execution time in milliseconds"""
        return (datetime.now() - start_time).total_seconds() * 1000
    
    def _get_cache_ttl(self, query: Query) -> int:
        """Get cache TTL based on query type"""
        # Different TTLs for different query types
        cache_ttls = {
            'GetPropertyEnergyAssessmentQuery': 600,  # 10 minutes
            'SearchPropertiesByEnergyClassQuery': 300,  # 5 minutes
            'GetUpgradeRecommendationsQuery': 1800,  # 30 minutes
            'GetEnergyMarketDataQuery': 3600,  # 1 hour
            'GetMarketBenchmarkQuery': 7200,  # 2 hours
            'GetDashboardDataQuery': 60,  # 1 minute
            'GetEnergyTrendsQuery': 14400,  # 4 hours
        }
        
        query_name = query.__class__.__name__
        return cache_ttls.get(query_name, 300)  # Default 5 minutes

# Query Middleware Functions

async def query_logging_middleware(query: Query):
    """Middleware for query logging"""
    logger.info(f"Executing query: {query.__class__.__name__} "
                f"(ID: {getattr(query, 'query_id', 'unknown')})")

async def query_performance_middleware(query: Query):
    """Middleware for query performance monitoring"""
    logger.debug(f"Performance tracking for {query.__class__.__name__}")

async def query_security_middleware(query: Query):
    """Middleware for query security validation and authorization"""
    from config.security_config import SecurityConfig
    
    # Get security configuration
    security_config = SecurityConfig()
    
    # Check if query has proper authentication
    if not hasattr(query, 'requested_by') or not query.requested_by:
        raise QueryBusError("Query must have 'requested_by' field for authentication")
    
    # Block anonymous queries for sensitive data in production
    if query.requested_by == "anonymous":
        sensitive_queries = [
            'GetEnergyPortfolioQuery',
            'GetPortfolioAnalysisQuery', 
            'GetDashboardDataQuery',
            'GetPerformanceMetricsQuery'
        ]
        
        if query.__class__.__name__ in sensitive_queries:
            if security_config.environment == "production":
                raise QueryBusError(f"Anonymous access to {query.__class__.__name__} not allowed in production")
            else:
                logger.warning(f"Anonymous access to sensitive query in {security_config.environment}: {query.__class__.__name__}")
    
    # Validate user authentication for sensitive queries
    if query.requested_by != "system" and _is_sensitive_query(query):
        if not _validate_query_user_authentication(query.requested_by):
            raise QueryBusError(f"Invalid or expired authentication for user: {query.requested_by}")
    
    # Query-specific authorization checks
    _check_query_authorization(query)
    
    logger.debug(f"Security validation passed for query {query.__class__.__name__} by {query.requested_by}")

def _is_sensitive_query(query: Query) -> bool:
    """Check if query contains sensitive information"""
    sensitive_query_types = [
        'GetEnergyPortfolioQuery',
        'GetPortfolioAnalysisQuery',
        'GetDashboardDataQuery', 
        'GetPerformanceMetricsQuery',
        'GetEnergyReportsQuery'
    ]
    return query.__class__.__name__ in sensitive_query_types

def _validate_query_user_authentication(user_id: str) -> bool:
    """Validate user authentication for queries"""
    # TODO: Implement proper JWT token validation
    # For now, reject obviously invalid user IDs
    if not user_id or len(user_id) < 3 or user_id in ['test', 'admin', 'guest']:
        return False
    return True

def _check_query_authorization(query: Query):
    """Check if user is authorized to execute specific query"""
    query_name = query.__class__.__name__
    user_id = query.requested_by
    
    # Define admin-only queries
    admin_only_queries = [
        'GetPerformanceMetricsQuery',
        'GetEnergyTrendsQuery'
    ]
    
    if query_name in admin_only_queries:
        if not _query_user_has_admin_privileges(user_id):
            raise QueryBusError(f"User {user_id} not authorized to execute {query_name}")

def _query_user_has_admin_privileges(user_id: str) -> bool:
    """Check if user has administrative privileges for queries"""
    admin_users = ['system', 'admin_user', 'energy_admin', 'data_analyst']
    return user_id in admin_users

# Query Handler Implementations

from .queries import (
    GetPropertyEnergyAssessmentQuery, SearchPropertiesByEnergyClassQuery,
    GetUpgradeRecommendationsQuery, GetEnergyPortfolioQuery,
    GetMarketBenchmarkQuery, GetDashboardDataQuery, GetEnergyTrendsQuery
)

class GetPropertyEnergyAssessmentHandler(QueryHandler):
    """Handler for property energy assessment queries"""
    
    async def handle(self, query: GetPropertyEnergyAssessmentQuery) -> QueryResult:
        try:
            logger.info(f"Retrieving assessment for property {query.property_id}")
            
            # Mock data - in production this would query the database
            assessment_data = {
                'property_id': query.property_id,
                'current_energy_class': 'C',
                'annual_consumption': 180.5,
                'annual_cost': 1200.0,
                'last_assessed': datetime.now().isoformat(),
                'confidence_score': 0.87,
                'assessor_type': 'ml_system'
            }
            
            if query.include_recommendations:
                assessment_data['recommendations'] = [
                    {
                        'upgrade_type': 'wall_insulation',
                        'estimated_cost': 8500,
                        'annual_savings': 420,
                        'roi': 15.2,
                        'payback_years': 5.1
                    }
                ]
            
            if query.include_market_comparison:
                assessment_data['market_comparison'] = {
                    'regional_average_class': 'D',
                    'performance_percentile': 68,
                    'similar_properties_average': 195.2
                }
            
            return QueryResult(
                success=True,
                query_id=query.query_id,
                data=assessment_data
            )
            
        except Exception as e:
            return QueryResult(
                success=False,
                query_id=query.query_id
            )

class SearchPropertiesByEnergyClassHandler(QueryHandler):
    """Handler for property search queries"""
    
    async def handle(self, query: SearchPropertiesByEnergyClassQuery) -> PagedQueryResult:
        try:
            logger.info(f"Searching properties with filters: {query.energy_classes}")
            
            # Mock data - in production this would query the database with filters
            total_count = 847
            
            # Simulate filtered results
            properties = []
            for i in range(min(query.page_size, 50)):  # Limit for demo
                property_id = f"PROP_{(query.page - 1) * query.page_size + i + 1:04d}"
                properties.append({
                    'property_id': property_id,
                    'energy_class': 'C',
                    'construction_year': 1995,
                    'building_type': 'apartment',
                    'total_area': 85.5,
                    'location': 'Athens, Attiki',
                    'last_assessed': '2024-08-15',
                    'annual_consumption': 165.3,
                    'upgrade_potential': 'High'
                })
            
            total_pages = (total_count + query.page_size - 1) // query.page_size
            
            return PagedQueryResult(
                success=True,
                query_id=query.query_id,
                data={'properties': properties},
                total_count=total_count,
                page=query.page,
                page_size=query.page_size,
                total_pages=total_pages,
                has_next=query.page < total_pages,
                has_previous=query.page > 1
            )
            
        except Exception as e:
            return PagedQueryResult(
                success=False,
                query_id=query.query_id,
                page=query.page,
                page_size=query.page_size
            )

class GetDashboardDataHandler(QueryHandler):
    """Handler for dashboard data queries"""
    
    async def handle(self, query: GetDashboardDataQuery) -> QueryResult:
        try:
            logger.info(f"Retrieving dashboard data for user {query.user_id}")
            
            # Mock dashboard data
            dashboard_data = {
                'user_id': query.user_id,
                'summary': {
                    'total_properties': 23,
                    'average_energy_class': 'C+',
                    'total_annual_cost': 28750,
                    'potential_savings': 8420,
                    'active_upgrades': 3
                },
                'recent_assessments': [
                    {
                        'property_id': 'PROP_001',
                        'assessed_date': '2024-09-02',
                        'energy_class': 'B+',
                        'improvement': 'Upgraded from C'
                    }
                ]
            }
            
            if query.include_alerts:
                dashboard_data['alerts'] = [
                    {
                        'type': 'energy_spike',
                        'property_id': 'PROP_007',
                        'message': 'Energy consumption 25% above average',
                        'severity': 'medium'
                    }
                ]
            
            if query.include_recommendations:
                dashboard_data['top_recommendations'] = [
                    {
                        'property_id': 'PROP_003',
                        'upgrade_type': 'heat_pump',
                        'potential_roi': 18.5,
                        'priority': 'high'
                    }
                ]
            
            return QueryResult(
                success=True,
                query_id=query.query_id,
                data=dashboard_data
            )
            
        except Exception as e:
            return QueryResult(
                success=False,
                query_id=query.query_id
            )

# Factory function for creating configured query bus

def create_query_bus() -> QueryBus:
    """Create and configure query bus with default handlers and middleware"""
    bus = QueryBus(enable_caching=True)
    
    # Register middleware
    bus.add_middleware(query_logging_middleware)
    bus.add_middleware(query_performance_middleware)
    bus.add_middleware(query_security_middleware)
    
    # Register handlers
    bus.register_handler(GetPropertyEnergyAssessmentQuery, GetPropertyEnergyAssessmentHandler())
    bus.register_handler(SearchPropertiesByEnergyClassQuery, SearchPropertiesByEnergyClassHandler())
    bus.register_handler(GetDashboardDataQuery, GetDashboardDataHandler())
    
    # Additional handlers would be registered here in a complete implementation
    
    logger.info("Query bus configured with default handlers and middleware")
    return bus

# Global query bus instance
_query_bus = None

def get_query_bus() -> QueryBus:
    """Get global query bus instance"""
    global _query_bus
    if _query_bus is None:
        _query_bus = create_query_bus()
    return _query_bus