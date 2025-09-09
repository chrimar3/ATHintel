"""
🗄️ Database Manager

Production-ready database management with connection pooling, query optimization,
caching, and comprehensive error handling for the energy assessment system.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import hashlib
import json
from decimal import Decimal

# Optional dependencies with graceful fallback
try:
    import asyncpg
    from asyncpg import Pool
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logging.warning("asyncpg not available, using mock database manager")

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("redis not available, disabling cache")

from config.production_config import get_config

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Base exception for database errors"""
    pass

class ConnectionError(DatabaseError):
    """Database connection error"""
    pass

class QueryError(DatabaseError):
    """Query execution error"""
    pass

class OptimizedQuery:
    """Optimized query with caching and performance monitoring"""
    
    def __init__(self, sql: str, cache_ttl: int = 0, name: str = None):
        self.sql = sql
        self.cache_ttl = cache_ttl
        self.name = name or f"query_{hash(sql) % 10000}"
        self.execution_count = 0
        self.total_duration = 0.0
        self.last_executed = None
    
    def get_cache_key(self, params: Dict[str, Any]) -> str:
        """Generate cache key for query with parameters"""
        if not params:
            return f"query:{self.name}"
        
        # Sort parameters for consistent cache keys
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
        return f"query:{self.name}:{param_hash}"
    
    def record_execution(self, duration: float):
        """Record query execution metrics"""
        self.execution_count += 1
        self.total_duration += duration
        self.last_executed = datetime.now()
    
    @property
    def average_duration(self) -> float:
        """Get average execution duration"""
        return self.total_duration / max(self.execution_count, 1)

class DatabaseManager:
    """
    Production-ready database manager with connection pooling, caching,
    and query optimization for energy assessment data.
    """
    
    def __init__(self):
        self.config = get_config()
        self.pool: Optional[Pool] = None
        self.redis_client: Optional[redis.Redis] = None
        self.queries: Dict[str, OptimizedQuery] = {}
        self._setup_optimized_queries()
    
    async def initialize(self):
        """Initialize database connections and cache"""
        await self._setup_database_pool()
        await self._setup_redis_cache()
        await self._ensure_database_schema()
        logger.info("Database manager initialized successfully")
    
    async def close(self):
        """Close all database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def _setup_database_pool(self):
        """Setup PostgreSQL connection pool"""
        if not ASYNCPG_AVAILABLE:
            logger.warning("PostgreSQL pool not available, using mock database")
            return
        
        try:
            db_config = self.config.database
            
            self.pool = await asyncpg.create_pool(
                host=db_config.host,
                port=db_config.port,
                user=db_config.user,
                password=db_config.password,
                database=db_config.name,
                min_size=db_config.min_connections,
                max_size=db_config.max_connections,
                command_timeout=db_config.connection_timeout,
                ssl=db_config.ssl_mode if db_config.ssl_mode != 'disable' else None
            )
            
            logger.info(f"Database pool created: {db_config.min_connections}-{db_config.max_connections} connections")
            
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise ConnectionError(f"Database connection failed: {e}")
    
    async def _setup_redis_cache(self):
        """Setup Redis cache connection"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, caching disabled")
            return
        
        try:
            self.redis_client = redis.from_url(
                self.config.cache.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache connection established")
            
        except Exception as e:
            logger.warning(f"Redis connection failed, caching disabled: {e}")
            self.redis_client = None
    
    def _setup_optimized_queries(self):
        """Setup pre-optimized queries for common operations"""
        
        # Property assessment queries
        self.queries['get_property'] = OptimizedQuery(
            sql="""
            SELECT p.*, pe.energy_class, pe.annual_consumption, pe.last_assessed
            FROM properties p
            LEFT JOIN property_energy pe ON p.id = pe.property_id
            WHERE p.id = $1
            """,
            cache_ttl=600,  # 10 minutes
            name='get_property'
        )
        
        self.queries['search_properties'] = OptimizedQuery(
            sql="""
            SELECT p.id, p.construction_year, p.total_area, p.building_type,
                   pe.energy_class, pe.annual_consumption
            FROM properties p
            LEFT JOIN property_energy pe ON p.id = pe.property_id
            WHERE ($1::text IS NULL OR pe.energy_class = ANY($1::text[]))
              AND ($2::int IS NULL OR p.construction_year >= $2)
              AND ($3::int IS NULL OR p.construction_year <= $3)
              AND ($4::decimal IS NULL OR p.total_area >= $4)
              AND ($5::decimal IS NULL OR p.total_area <= $5)
            ORDER BY pe.last_assessed DESC NULLS LAST
            LIMIT $6 OFFSET $7
            """,
            cache_ttl=300,  # 5 minutes
            name='search_properties'
        )
        
        # Assessment history queries
        self.queries['get_assessments'] = OptimizedQuery(
            sql="""
            SELECT * FROM property_assessments 
            WHERE property_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
            """,
            cache_ttl=1800,  # 30 minutes
            name='get_assessments'
        )
        
        # Market data queries
        self.queries['get_market_data'] = OptimizedQuery(
            sql="""
            SELECT * FROM energy_market_data 
            WHERE region = $1 AND data_type = $2 
              AND effective_date <= $3
            ORDER BY effective_date DESC 
            LIMIT 1
            """,
            cache_ttl=3600,  # 1 hour
            name='get_market_data'
        )
        
        # Portfolio queries
        self.queries['get_portfolio'] = OptimizedQuery(
            sql="""
            SELECT p.*, array_agg(pp.property_id) as property_ids,
                   count(pp.property_id) as property_count
            FROM portfolios p
            LEFT JOIN portfolio_properties pp ON p.id = pp.portfolio_id
            WHERE p.id = $1
            GROUP BY p.id, p.name, p.owner_id, p.created_at
            """,
            cache_ttl=600,  # 10 minutes
            name='get_portfolio'
        )
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            raise ConnectionError("Database pool not initialized")
        
        async with self.pool.acquire() as connection:
            yield connection
    
    async def execute_query(
        self,
        query_name: str,
        params: Dict[str, Any] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute optimized query with caching and performance monitoring"""
        
        if query_name not in self.queries:
            raise QueryError(f"Unknown query: {query_name}")
        
        query = self.queries[query_name]
        params = params or {}
        
        # Check cache first
        if use_cache and query.cache_ttl > 0 and self.redis_client:
            cached_result = await self._get_cached_result(query, params)
            if cached_result is not None:
                logger.debug(f"Cache hit for query: {query_name}")
                return cached_result
        
        # Execute query
        start_time = datetime.now()
        
        try:
            if ASYNCPG_AVAILABLE and self.pool:
                async with self.get_connection() as conn:
                    # Convert named parameters to positional for asyncpg
                    param_values = [params.get(f'param_{i+1}', None) for i in range(10)]
                    
                    # Execute query
                    rows = await conn.fetch(query.sql, *param_values[:query.sql.count('$')])
                    
                    # Convert to dict format
                    result = [dict(row) for row in rows]
            else:
                # Mock database response
                result = await self._mock_query_execution(query_name, params)
            
            # Record performance metrics
            duration = (datetime.now() - start_time).total_seconds() * 1000
            query.record_execution(duration)
            
            # Log slow queries
            if duration > self.config.monitoring.slow_query_threshold:
                logger.warning(f"Slow query detected: {query_name} ({duration:.2f}ms)")
            
            # Cache result if applicable
            if use_cache and query.cache_ttl > 0 and self.redis_client:
                await self._cache_result(query, params, result)
            
            logger.debug(f"Query {query_name} executed in {duration:.2f}ms, returned {len(result)} rows")
            return result
            
        except Exception as e:
            logger.error(f"Query execution failed: {query_name} - {e}")
            raise QueryError(f"Query {query_name} failed: {e}")
    
    async def _get_cached_result(self, query: OptimizedQuery, params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Get cached query result"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = query.get_cache_key(params)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data, parse_float=Decimal)
        
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        return None
    
    async def _cache_result(self, query: OptimizedQuery, params: Dict[str, Any], result: List[Dict[str, Any]]):
        """Cache query result"""
        if not self.redis_client:
            return
        
        try:
            cache_key = query.get_cache_key(params)
            serialized_result = json.dumps(result, default=str)
            
            await self.redis_client.setex(
                cache_key,
                query.cache_ttl,
                serialized_result
            )
        
        except Exception as e:
            logger.warning(f"Result caching failed: {e}")
    
    async def _mock_query_execution(self, query_name: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock query execution when database is not available"""
        
        # Mock responses for different query types
        mock_responses = {
            'get_property': [{
                'id': params.get('property_id', 'PROP_001'),
                'construction_year': 1995,
                'total_area': Decimal('85.5'),
                'building_type': 'apartment',
                'energy_class': 'C',
                'annual_consumption': Decimal('165.3'),
                'last_assessed': datetime.now() - timedelta(days=30)
            }],
            'search_properties': [
                {
                    'id': f'PROP_{i:03d}',
                    'construction_year': 1990 + (i % 30),
                    'total_area': Decimal(str(80 + (i % 50))),
                    'building_type': 'apartment',
                    'energy_class': ['C', 'D', 'B'][i % 3],
                    'annual_consumption': Decimal(str(150 + (i % 100)))
                }
                for i in range(1, min(params.get('limit', 50) + 1, 51))
            ],
            'get_assessments': [{
                'id': 'ASSESS_001',
                'property_id': params.get('property_id', 'PROP_001'),
                'energy_class': 'C',
                'confidence': 0.85,
                'created_at': datetime.now() - timedelta(days=15)
            }],
            'get_market_data': [{
                'region': params.get('region', 'athens'),
                'data_type': params.get('data_type', 'electricity_price'),
                'value': Decimal('0.15'),
                'effective_date': datetime.now() - timedelta(days=1)
            }],
            'get_portfolio': [{
                'id': params.get('portfolio_id', 'PORT_001'),
                'name': 'Sample Portfolio',
                'property_ids': ['PROP_001', 'PROP_002', 'PROP_003'],
                'property_count': 3
            }]
        }
        
        return mock_responses.get(query_name, [])
    
    async def _ensure_database_schema(self):
        """Ensure database schema is up to date"""
        if not ASYNCPG_AVAILABLE or not self.pool:
            logger.info("Skipping schema validation (database not available)")
            return
        
        try:
            async with self.get_connection() as conn:
                # Check if core tables exist
                tables_query = """
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
                
                existing_tables = await conn.fetch(tables_query)
                table_names = [row['table_name'] for row in existing_tables]
                
                required_tables = [
                    'properties', 'property_energy', 'property_assessments',
                    'portfolios', 'portfolio_properties', 'energy_market_data'
                ]
                
                missing_tables = [table for table in required_tables if table not in table_names]
                
                if missing_tables:
                    logger.warning(f"Missing database tables: {missing_tables}")
                else:
                    logger.info("Database schema validation passed")
        
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
    
    async def get_query_performance_stats(self) -> Dict[str, Any]:
        """Get query performance statistics"""
        stats = {}
        
        for name, query in self.queries.items():
            stats[name] = {
                'execution_count': query.execution_count,
                'average_duration_ms': query.average_duration,
                'last_executed': query.last_executed.isoformat() if query.last_executed else None,
                'cache_ttl': query.cache_ttl
            }
        
        return stats
    
    async def clear_cache(self, pattern: str = None):
        """Clear cache entries matching pattern"""
        if not self.redis_client:
            return
        
        try:
            if pattern:
                keys = await self.redis_client.keys(f"query:*{pattern}*")
            else:
                keys = await self.redis_client.keys("query:*")
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries")
        
        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")

# Global database manager instance
_db_manager = None

async def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
    return _db_manager

async def close_database_manager():
    """Close global database manager"""
    global _db_manager
    if _db_manager:
        await _db_manager.close()
        _db_manager = None