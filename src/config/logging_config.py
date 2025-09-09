"""
📋 Logging Configuration

Comprehensive logging setup for production energy assessment system.
Provides structured logging, error tracking, and performance monitoring.
"""

import logging
import logging.config
import os
from datetime import datetime
from typing import Dict, Any
import json

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra context if available
        if hasattr(record, 'property_id'):
            log_entry['property_id'] = record.property_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'processing_id'):
            log_entry['processing_id'] = record.processing_id
        
        if hasattr(record, 'execution_time_ms'):
            log_entry['execution_time_ms'] = record.execution_time_ms
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def setup_logging(environment: str = None, log_level: str = None):
    """Setup comprehensive logging configuration"""
    
    # Get environment from env var or parameter
    env = environment or os.getenv('ENVIRONMENT', 'development')
    level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d: %(message)s'
            },
            'json': {
                '()': JSONFormatter
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'standard' if env == 'development' else 'json',
                'stream': 'ext://sys.stdout'
            },
            'file_info': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json' if env == 'production' else 'detailed',
                'filename': f'{log_dir}/energy_assessment.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 5,
                'encoding': 'utf8'
            },
            'file_error': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json' if env == 'production' else 'detailed',
                'filename': f'{log_dir}/energy_assessment_errors.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 10,
                'encoding': 'utf8'
            },
            'security': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'WARNING',
                'formatter': 'json',
                'filename': f'{log_dir}/security.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 10,
                'encoding': 'utf8'
            }
        },
        'loggers': {
            # Root logger
            '': {
                'handlers': ['console', 'file_info', 'file_error'],
                'level': level,
                'propagate': False
            },
            # Security-specific logger
            'security': {
                'handlers': ['console', 'security'],
                'level': 'WARNING',
                'propagate': False
            },
            # ML model logger
            'ml.energy_prediction': {
                'handlers': ['console', 'file_info'],
                'level': 'INFO',
                'propagate': True
            },
            # Pipeline logger
            'pipelines.energy_assessment': {
                'handlers': ['console', 'file_info'],
                'level': 'DEBUG' if env == 'development' else 'INFO',
                'propagate': True
            },
            # CQRS logger
            'infrastructure.cqrs': {
                'handlers': ['console', 'file_info'],
                'level': 'INFO',
                'propagate': True
            },
            # Domain events logger
            'domains.energy.events': {
                'handlers': ['console', 'file_info'],
                'level': 'INFO',
                'propagate': True
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for environment: {env}, level: {level}")

class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
    
    def authentication_failure(self, user_id: str, reason: str, ip_address: str = None):
        """Log authentication failure"""
        self.logger.warning(
            f"Authentication failure: {reason}",
            extra={
                'user_id': user_id,
                'ip_address': ip_address,
                'event_type': 'auth_failure'
            }
        )
    
    def unauthorized_access(self, user_id: str, resource: str, action: str):
        """Log unauthorized access attempt"""
        self.logger.warning(
            f"Unauthorized access attempt: {action} on {resource}",
            extra={
                'user_id': user_id,
                'resource': resource,
                'action': action,
                'event_type': 'unauthorized_access'
            }
        )
    
    def suspicious_activity(self, user_id: str, activity: str, details: Dict[str, Any]):
        """Log suspicious activity"""
        self.logger.warning(
            f"Suspicious activity: {activity}",
            extra={
                'user_id': user_id,
                'activity': activity,
                'details': details,
                'event_type': 'suspicious_activity'
            }
        )

class PerformanceLogger:
    """Specialized logger for performance monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
    
    def slow_operation(self, operation: str, duration_ms: float, threshold_ms: float = 1000):
        """Log slow operations"""
        if duration_ms > threshold_ms:
            self.logger.warning(
                f"Slow operation detected: {operation}",
                extra={
                    'operation': operation,
                    'execution_time_ms': duration_ms,
                    'threshold_ms': threshold_ms,
                    'event_type': 'slow_operation'
                }
            )
    
    def resource_usage(self, resource_type: str, usage: float, limit: float):
        """Log resource usage"""
        usage_percent = (usage / limit) * 100
        
        level = 'info'
        if usage_percent > 90:
            level = 'critical'
        elif usage_percent > 75:
            level = 'warning'
        
        getattr(self.logger, level)(
            f"Resource usage: {resource_type} at {usage_percent:.1f}%",
            extra={
                'resource_type': resource_type,
                'usage': usage,
                'limit': limit,
                'usage_percent': usage_percent,
                'event_type': 'resource_usage'
            }
        )

class PropertyAssessmentLogger:
    """Specialized logger for property assessment pipeline"""
    
    def __init__(self):
        self.logger = logging.getLogger('pipelines.energy_assessment')
    
    def assessment_started(self, property_id: str, processing_id: str, user_id: str = None):
        """Log assessment start"""
        self.logger.info(
            f"Energy assessment started for property {property_id}",
            extra={
                'property_id': property_id,
                'processing_id': processing_id,
                'user_id': user_id,
                'event_type': 'assessment_started'
            }
        )
    
    def assessment_completed(self, property_id: str, processing_id: str, 
                           duration_ms: float, energy_class: str, confidence: float):
        """Log successful assessment completion"""
        self.logger.info(
            f"Energy assessment completed for property {property_id}: {energy_class} (confidence: {confidence:.2f})",
            extra={
                'property_id': property_id,
                'processing_id': processing_id,
                'execution_time_ms': duration_ms,
                'energy_class': energy_class,
                'confidence': confidence,
                'event_type': 'assessment_completed'
            }
        )
    
    def assessment_failed(self, property_id: str, processing_id: str, 
                         error: str, stage: str = None):
        """Log assessment failure"""
        self.logger.error(
            f"Energy assessment failed for property {property_id}: {error}",
            extra={
                'property_id': property_id,
                'processing_id': processing_id,
                'error': error,
                'failed_stage': stage,
                'event_type': 'assessment_failed'
            }
        )
    
    def ml_prediction_fallback(self, property_id: str, reason: str):
        """Log ML prediction fallback"""
        self.logger.warning(
            f"ML prediction fallback for property {property_id}: {reason}",
            extra={
                'property_id': property_id,
                'reason': reason,
                'event_type': 'ml_fallback'
            }
        )

# Global logger instances
security_logger = SecurityLogger()
performance_logger = PerformanceLogger()
assessment_logger = PropertyAssessmentLogger()

def get_security_logger() -> SecurityLogger:
    """Get security logger instance"""
    return security_logger

def get_performance_logger() -> PerformanceLogger:
    """Get performance logger instance"""
    return performance_logger

def get_assessment_logger() -> PropertyAssessmentLogger:
    """Get assessment logger instance"""
    return assessment_logger

# Initialize logging on module import
if not logging.getLogger().handlers:
    setup_logging()