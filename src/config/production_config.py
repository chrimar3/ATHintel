"""
🏭 Production Configuration Management

Production-ready configuration management with environment-specific settings,
validation, and secure defaults for the energy assessment system.
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    name: str = os.getenv('DB_NAME', 'energy_assessment')
    user: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASSWORD', '')
    
    # Connection pool settings
    min_connections: int = int(os.getenv('DB_MIN_CONNECTIONS', '5'))
    max_connections: int = int(os.getenv('DB_MAX_CONNECTIONS', '20'))
    connection_timeout: int = int(os.getenv('DB_CONNECTION_TIMEOUT', '30'))
    
    # SSL and security
    ssl_mode: str = os.getenv('DB_SSL_MODE', 'prefer')
    ssl_cert: Optional[str] = os.getenv('DB_SSL_CERT')
    ssl_key: Optional[str] = os.getenv('DB_SSL_KEY')
    ssl_ca: Optional[str] = os.getenv('DB_SSL_CA')
    
    def get_connection_url(self) -> str:
        """Get database connection URL"""
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.name}"

@dataclass
class CacheConfig:
    """Cache configuration settings"""
    redis_url: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    default_ttl: int = int(os.getenv('CACHE_DEFAULT_TTL', '3600'))  # 1 hour
    max_memory: str = os.getenv('REDIS_MAX_MEMORY', '256mb')
    
    # Cache-specific TTLs
    assessment_cache_ttl: int = int(os.getenv('ASSESSMENT_CACHE_TTL', '1800'))  # 30 minutes
    market_data_cache_ttl: int = int(os.getenv('MARKET_DATA_CACHE_TTL', '3600'))  # 1 hour
    ml_prediction_cache_ttl: int = int(os.getenv('ML_PREDICTION_CACHE_TTL', '7200'))  # 2 hours

@dataclass
class MLConfig:
    """Machine Learning configuration settings"""
    model_path: str = os.getenv('ML_MODEL_PATH', '/app/models')
    prediction_timeout: int = int(os.getenv('ML_PREDICTION_TIMEOUT', '30'))
    thread_pool_workers: int = int(os.getenv('ML_THREAD_POOL_WORKERS', '4'))
    
    # Model-specific settings
    ensemble_enabled: bool = os.getenv('ML_ENSEMBLE_ENABLED', 'true').lower() == 'true'
    fallback_enabled: bool = os.getenv('ML_FALLBACK_ENABLED', 'true').lower() == 'true'
    confidence_threshold: float = float(os.getenv('ML_CONFIDENCE_THRESHOLD', '0.7'))
    
    # Performance settings
    batch_size: int = int(os.getenv('ML_BATCH_SIZE', '32'))
    max_concurrent_predictions: int = int(os.getenv('ML_MAX_CONCURRENT', '10'))

@dataclass
class PipelineConfig:
    """Pipeline processing configuration"""
    max_processing_time: int = int(os.getenv('PIPELINE_MAX_TIME', '300'))  # 5 minutes
    parallel_processing: bool = os.getenv('PIPELINE_PARALLEL', 'true').lower() == 'true'
    max_concurrent_assessments: int = int(os.getenv('PIPELINE_MAX_CONCURRENT', '50'))
    
    # Stage-specific timeouts
    validation_timeout: int = int(os.getenv('VALIDATION_TIMEOUT', '10'))
    feature_extraction_timeout: int = int(os.getenv('FEATURE_TIMEOUT', '15'))
    recommendation_timeout: int = int(os.getenv('RECOMMENDATION_TIMEOUT', '30'))
    
    # Error handling
    max_retries: int = int(os.getenv('PIPELINE_MAX_RETRIES', '3'))
    retry_delay: int = int(os.getenv('PIPELINE_RETRY_DELAY', '5'))

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    environment: str = os.getenv('ENVIRONMENT', 'development')
    jwt_secret_key: str = os.getenv('JWT_SECRET_KEY', '')
    jwt_algorithm: str = os.getenv('JWT_ALGORITHM', 'HS256')
    jwt_expiration: int = int(os.getenv('JWT_EXPIRATION', '3600'))  # 1 hour
    
    # Rate limiting
    rate_limit_requests: int = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    rate_limit_window: int = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))  # 1 hour
    
    # CORS settings
    cors_origins: List[str] = field(default_factory=lambda: os.getenv('CORS_ORIGINS', '*').split(','))
    cors_methods: List[str] = field(default_factory=lambda: ['GET', 'POST', 'PUT', 'DELETE'])
    
    # Security headers
    enable_security_headers: bool = os.getenv('SECURITY_HEADERS', 'true').lower() == 'true'
    hsts_max_age: int = int(os.getenv('HSTS_MAX_AGE', '31536000'))  # 1 year

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    enable_metrics: bool = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    metrics_port: int = int(os.getenv('METRICS_PORT', '9090'))
    
    # Health check settings
    health_check_interval: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '30'))
    readiness_timeout: int = int(os.getenv('READINESS_TIMEOUT', '10'))
    
    # Error tracking
    sentry_dsn: Optional[str] = os.getenv('SENTRY_DSN')
    error_sample_rate: float = float(os.getenv('ERROR_SAMPLE_RATE', '1.0'))
    
    # Performance monitoring
    performance_monitoring: bool = os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true'
    slow_query_threshold: float = float(os.getenv('SLOW_QUERY_THRESHOLD', '1000'))  # 1 second

@dataclass
class ExternalServicesConfig:
    """External services configuration"""
    # Greek government APIs
    gov_api_base_url: str = os.getenv('GOV_API_BASE_URL', 'https://api.gov.gr')
    gov_api_key: str = os.getenv('GOV_API_KEY', '')
    gov_api_timeout: int = int(os.getenv('GOV_API_TIMEOUT', '30'))
    
    # Weather/climate data
    weather_api_url: str = os.getenv('WEATHER_API_URL', 'https://api.openweathermap.org')
    weather_api_key: str = os.getenv('WEATHER_API_KEY', '')
    
    # Market data providers
    energy_market_api_url: str = os.getenv('ENERGY_MARKET_API_URL', '')
    energy_market_api_key: str = os.getenv('ENERGY_MARKET_API_KEY', '')

class ProductionConfig:
    """Main production configuration class"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
        # Initialize configuration sections
        self.database = DatabaseConfig()
        self.cache = CacheConfig()
        self.ml = MLConfig()
        self.pipeline = PipelineConfig()
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        self.external_services = ExternalServicesConfig()
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"Production configuration loaded for environment: {self.environment}")
    
    def _validate_config(self):
        """Validate critical configuration settings"""
        errors = []
        warnings = []
        
        # Validate database configuration
        if not self.database.password and self.environment == 'production':
            errors.append("Database password is required for production environment")
        
        # Validate security configuration
        if not self.security.jwt_secret_key:
            if self.environment == 'production':
                errors.append("JWT secret key is required for production environment")
            else:
                warnings.append("JWT secret key not set, using insecure default")
        
        if len(self.security.jwt_secret_key) < 32 and self.security.jwt_secret_key:
            warnings.append("JWT secret key should be at least 32 characters long")
        
        # Validate ML configuration
        if not os.path.exists(self.ml.model_path):
            warnings.append(f"ML model path does not exist: {self.ml.model_path}")
        
        # Validate external services for production
        if self.environment == 'production':
            if not self.external_services.gov_api_key:
                warnings.append("Government API key not configured")
            
            if not self.external_services.weather_api_key:
                warnings.append("Weather API key not configured")
        
        # Log validation results
        if errors:
            error_msg = f"Configuration validation failed: {'; '.join(errors)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if warnings:
            for warning in warnings:
                logger.warning(f"Configuration warning: {warning}")
    
    def get_performance_limits(self) -> Dict[str, Any]:
        """Get performance limits for the application"""
        base_limits = {
            'max_concurrent_assessments': self.pipeline.max_concurrent_assessments,
            'max_processing_time': self.pipeline.max_processing_time,
            'ml_prediction_timeout': self.ml.prediction_timeout,
            'rate_limit_requests': self.security.rate_limit_requests,
            'rate_limit_window': self.security.rate_limit_window
        }
        
        # Adjust limits based on environment
        if self.environment == 'production':
            # More conservative limits in production
            base_limits['max_concurrent_assessments'] = min(
                base_limits['max_concurrent_assessments'], 100
            )
        elif self.environment == 'development':
            # More permissive limits in development
            base_limits['max_concurrent_assessments'] = max(
                base_limits['max_concurrent_assessments'], 10
            )
        
        return base_limits
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags configuration"""
        return {
            'ml_predictions_enabled': self.ml.ensemble_enabled,
            'ml_fallback_enabled': self.ml.fallback_enabled,
            'parallel_processing_enabled': self.pipeline.parallel_processing,
            'caching_enabled': bool(self.cache.redis_url),
            'monitoring_enabled': self.monitoring.enable_metrics,
            'security_headers_enabled': self.security.enable_security_headers,
            'performance_monitoring_enabled': self.monitoring.performance_monitoring
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == 'development'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)"""
        config_dict = {
            'environment': self.environment,
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'name': self.database.name,
                'ssl_mode': self.database.ssl_mode
            },
            'ml': {
                'prediction_timeout': self.ml.prediction_timeout,
                'ensemble_enabled': self.ml.ensemble_enabled,
                'confidence_threshold': self.ml.confidence_threshold
            },
            'pipeline': {
                'max_processing_time': self.pipeline.max_processing_time,
                'parallel_processing': self.pipeline.parallel_processing,
                'max_concurrent_assessments': self.pipeline.max_concurrent_assessments
            },
            'security': {
                'rate_limit_requests': self.security.rate_limit_requests,
                'rate_limit_window': self.security.rate_limit_window,
                'enable_security_headers': self.security.enable_security_headers
            },
            'monitoring': {
                'enable_metrics': self.monitoring.enable_metrics,
                'performance_monitoring': self.monitoring.performance_monitoring
            }
        }
        return config_dict

# Global configuration instance
_config_instance = None

def get_config() -> ProductionConfig:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ProductionConfig()
    return _config_instance

def reload_config() -> ProductionConfig:
    """Reload configuration (useful for testing)"""
    global _config_instance
    _config_instance = ProductionConfig()
    return _config_instance

# Environment validation helper
def validate_environment():
    """Validate that environment variables are properly set"""
    required_vars = []
    
    env = os.getenv('ENVIRONMENT', 'development')
    
    if env == 'production':
        required_vars.extend([
            'DB_HOST',
            'DB_PASSWORD', 
            'JWT_SECRET_KEY',
            'REDIS_URL'
        ])
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables for {env}: {missing_vars}")

# Initialize and validate on import
try:
    validate_environment()
except ValueError as e:
    logger.warning(f"Environment validation warning: {e}")
    # Don't fail on import, just warn