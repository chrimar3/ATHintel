"""
🛡️ Secure Error Handler

Prevents information disclosure through error messages while maintaining
operational visibility through secure audit logging:

- Sanitized error messages for external responses
- Detailed error logging for internal monitoring  
- Error classification and severity assessment
- Structured error codes for client applications
- Security-aware stack trace handling
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import json
import hashlib

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM_RESOURCE = "system_resource"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for error tracking"""
    error_id: str
    timestamp: datetime
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    endpoint: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecureErrorResponse:
    """Secure error response for external clients"""
    error_code: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    error_id: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON responses"""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "severity": self.severity.value,
                "category": self.category.value,
                "error_id": self.error_id,
                "timestamp": self.timestamp
            },
            "details": self.details
        }


class SensitiveDataPattern:
    """Patterns for identifying sensitive data in error messages"""
    
    # Regex patterns for sensitive information
    PATTERNS = {
        'database_connection': re.compile(r'postgresql://[^@]+:[^@]+@[^/]+/\w+', re.IGNORECASE),
        'api_key': re.compile(r'(?:api[_-]?key|token|secret)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{20,})', re.IGNORECASE),
        'password': re.compile(r'password["\']?\s*[:=]\s*["\']?([^\s"\']+)', re.IGNORECASE),
        'jwt_token': re.compile(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*', re.IGNORECASE),
        'file_path': re.compile(r'(?:/[a-zA-Z0-9_.-]+){3,}', re.IGNORECASE),
        'ip_address': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'uuid': re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.IGNORECASE),
    }
    
    @classmethod
    def sanitize_message(cls, message: str) -> str:
        """Remove sensitive data from error message"""
        sanitized = message
        
        for pattern_name, pattern in cls.PATTERNS.items():
            if pattern_name == 'database_connection':
                # Replace connection strings with placeholder
                sanitized = pattern.sub('postgresql://[REDACTED]/[DATABASE]', sanitized)
            elif pattern_name in ['api_key', 'password', 'jwt_token']:
                # Replace secrets with masked version
                sanitized = pattern.sub(lambda m: f"{pattern_name.upper()}:[REDACTED]", sanitized)
            elif pattern_name == 'file_path':
                # Replace file paths with generic path
                sanitized = pattern.sub('/[PATH_REDACTED]', sanitized)
            elif pattern_name in ['ip_address', 'email']:
                # Replace with type indicator
                sanitized = pattern.sub(f'[{pattern_name.upper()}_REDACTED]', sanitized)
            elif pattern_name == 'uuid':
                # Replace UUIDs with placeholder
                sanitized = pattern.sub('[UUID_REDACTED]', sanitized)
        
        return sanitized


class ErrorClassifier:
    """Classifies errors by category and severity"""
    
    # Error patterns for automatic classification
    CLASSIFICATION_RULES = {
        # Authentication errors
        (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH): [
            'authentication failed', 'invalid credentials', 'unauthorized',
            'jwt token expired', 'invalid token', 'authentication required'
        ],
        
        # Authorization errors
        (ErrorCategory.AUTHORIZATION, ErrorSeverity.MEDIUM): [
            'access denied', 'insufficient permissions', 'forbidden',
            'not authorized', 'permission denied'
        ],
        
        # Validation errors
        (ErrorCategory.VALIDATION, ErrorSeverity.LOW): [
            'validation error', 'invalid input', 'bad request',
            'missing required field', 'invalid format'
        ],
        
        # Database errors
        (ErrorCategory.DATABASE, ErrorSeverity.CRITICAL): [
            'connection refused', 'database error', 'deadlock detected',
            'constraint violation', 'table does not exist'
        ],
        
        # External service errors
        (ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH): [
            'service unavailable', 'timeout', 'connection timeout',
            'circuit breaker open', 'external api error'
        ],
        
        # System resource errors
        (ErrorCategory.SYSTEM_RESOURCE, ErrorSeverity.CRITICAL): [
            'out of memory', 'disk full', 'resource exhausted',
            'too many open files', 'system overload'
        ],
        
        # Configuration errors
        (ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH): [
            'configuration error', 'missing configuration',
            'invalid configuration', 'config file not found'
        ]
    }
    
    @classmethod
    def classify_error(cls, error: Exception, message: str) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Classify error by category and severity"""
        error_text = f"{str(error)} {message}".lower()
        
        # Check classification rules
        for (category, severity), keywords in cls.CLASSIFICATION_RULES.items():
            if any(keyword in error_text for keyword in keywords):
                return category, severity
        
        # Check exception type for classification
        error_type = type(error).__name__.lower()
        
        if 'auth' in error_type or 'permission' in error_type:
            return ErrorCategory.AUTHORIZATION, ErrorSeverity.MEDIUM
        elif 'validation' in error_type or 'value' in error_type:
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW
        elif 'connection' in error_type or 'timeout' in error_type:
            return ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH
        elif 'memory' in error_type or 'resource' in error_type:
            return ErrorCategory.SYSTEM_RESOURCE, ErrorSeverity.CRITICAL
        
        # Default classification
        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM


class SecureErrorHandler:
    """
    Main secure error handler with sanitization and audit logging
    """
    
    def __init__(self, enable_debug_mode: bool = False):
        self.enable_debug_mode = enable_debug_mode  # Only for development
        
        # Error code mapping
        self.error_codes = {
            (ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH): "AUTH_001",
            (ErrorCategory.AUTHORIZATION, ErrorSeverity.MEDIUM): "AUTHZ_001", 
            (ErrorCategory.VALIDATION, ErrorSeverity.LOW): "VALID_001",
            (ErrorCategory.DATABASE, ErrorSeverity.CRITICAL): "DB_001",
            (ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH): "EXT_001",
            (ErrorCategory.SYSTEM_RESOURCE, ErrorSeverity.CRITICAL): "SYS_001",
            (ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH): "CONFIG_001",
            (ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.MEDIUM): "BIZ_001",
            (ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM): "UNK_001"
        }
        
        # Generic error messages for external responses
        self.generic_messages = {
            ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your credentials.",
            ErrorCategory.AUTHORIZATION: "Access denied. You don't have permission to access this resource.",
            ErrorCategory.VALIDATION: "Invalid input provided. Please check your request and try again.",
            ErrorCategory.DATABASE: "A database error occurred. Please try again later.",
            ErrorCategory.EXTERNAL_SERVICE: "External service temporarily unavailable. Please try again later.",
            ErrorCategory.SYSTEM_RESOURCE: "System temporarily unavailable due to high load. Please try again later.",
            ErrorCategory.CONFIGURATION: "Service configuration error. Please contact support.",
            ErrorCategory.BUSINESS_LOGIC: "Request could not be processed. Please check your input.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again later."
        }
        
        logger.info(f"Secure error handler initialized (debug_mode: {enable_debug_mode})")
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        custom_message: Optional[str] = None,
        include_details: bool = False
    ) -> SecureErrorResponse:
        """
        Handle error with sanitization and secure response generation
        
        Args:
            error: Exception that occurred
            context: Error context information
            custom_message: Custom error message override
            include_details: Whether to include sanitized details (for internal APIs)
            
        Returns:
            Secure error response safe for external consumption
        """
        # Generate unique error ID
        error_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        # Create context if not provided
        if context is None:
            context = ErrorContext(
                error_id=error_id,
                timestamp=timestamp
            )
        
        # Get original error message
        original_message = custom_message or str(error)
        
        # Classify error
        category, severity = ErrorClassifier.classify_error(error, original_message)
        
        # Generate error code
        error_code = self.error_codes.get((category, severity), "UNK_001")
        
        # Create sanitized message for external response
        if self.enable_debug_mode:
            # In debug mode, include sanitized original message
            safe_message = SensitiveDataPattern.sanitize_message(original_message)
        else:
            # In production, use generic message
            safe_message = self.generic_messages.get(category, "An error occurred")
        
        # Log detailed error for internal monitoring
        self._log_detailed_error(error, context, category, severity, original_message)
        
        # Prepare details for response (if requested)
        details = None
        if include_details:
            details = self._prepare_safe_details(error, context)
        
        return SecureErrorResponse(
            error_code=error_code,
            message=safe_message,
            severity=severity,
            category=category,
            error_id=error_id,
            timestamp=timestamp.isoformat(),
            details=details
        )
    
    def _log_detailed_error(
        self,
        error: Exception,
        context: ErrorContext,
        category: ErrorCategory,
        severity: ErrorSeverity,
        original_message: str
    ):
        """Log detailed error information for internal monitoring"""
        
        # Create comprehensive log entry
        log_data = {
            "error_id": context.error_id,
            "timestamp": context.timestamp.isoformat(),
            "severity": severity.value,
            "category": category.value,
            "error_type": type(error).__name__,
            "error_message": original_message,
            "user_id": context.user_id,
            "request_id": context.request_id,
            "endpoint": context.endpoint,
            "ip_address": context.ip_address,
            "user_agent": context.user_agent,
            "additional_context": context.additional_context
        }
        
        # Add stack trace for high severity errors
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            log_data["stack_trace"] = traceback.format_exc()
        
        # Log with appropriate level based on severity
        if severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error occurred", extra={"error_data": json.dumps(log_data)})
        elif severity == ErrorSeverity.HIGH:
            logger.error("High severity error occurred", extra={"error_data": json.dumps(log_data)})
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error occurred", extra={"error_data": json.dumps(log_data)})
        else:
            logger.info("Low severity error occurred", extra={"error_data": json.dumps(log_data)})
    
    def _prepare_safe_details(
        self,
        error: Exception,
        context: ErrorContext
    ) -> Dict[str, Any]:
        """Prepare safe details for error response"""
        
        details = {
            "error_type": type(error).__name__,
            "timestamp": context.timestamp.isoformat(),
        }
        
        # Add safe context information
        if context.endpoint:
            details["endpoint"] = context.endpoint
        
        if context.request_id:
            details["request_id"] = context.request_id
        
        # Add sanitized additional context
        if context.additional_context:
            safe_context = {}
            for key, value in context.additional_context.items():
                if key not in ['password', 'api_key', 'token', 'secret']:
                    if isinstance(value, str):
                        safe_context[key] = SensitiveDataPattern.sanitize_message(value)
                    elif isinstance(value, (int, float, bool)):
                        safe_context[key] = value
                    else:
                        safe_context[key] = str(type(value).__name__)
            
            if safe_context:
                details["context"] = safe_context
        
        return details
    
    def handle_validation_error(
        self,
        validation_errors: List[str],
        context: Optional[ErrorContext] = None
    ) -> SecureErrorResponse:
        """Handle validation errors with field-level details"""
        
        error_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        if context is None:
            context = ErrorContext(error_id=error_id, timestamp=timestamp)
        
        # Sanitize validation errors
        safe_errors = [
            SensitiveDataPattern.sanitize_message(error) 
            for error in validation_errors
        ]
        
        # Log validation errors
        self._log_detailed_error(
            ValueError("Validation failed"),
            context,
            ErrorCategory.VALIDATION,
            ErrorSeverity.LOW,
            f"Validation errors: {validation_errors}"
        )
        
        return SecureErrorResponse(
            error_code="VALID_001",
            message="Input validation failed",
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            error_id=error_id,
            timestamp=timestamp.isoformat(),
            details={"validation_errors": safe_errors}
        )
    
    def handle_authentication_error(
        self,
        reason: str,
        context: Optional[ErrorContext] = None
    ) -> SecureErrorResponse:
        """Handle authentication errors with security logging"""
        
        error_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        if context is None:
            context = ErrorContext(error_id=error_id, timestamp=timestamp)
        
        # Log authentication failure (security event)
        security_log_data = {
            "event_type": "authentication_failure",
            "error_id": error_id,
            "timestamp": timestamp.isoformat(),
            "user_id": context.user_id,
            "ip_address": context.ip_address,
            "user_agent": context.user_agent,
            "reason": reason,
            "endpoint": context.endpoint
        }
        
        logger.warning("Authentication failure", extra={"security_event": json.dumps(security_log_data)})
        
        # Generic message to prevent user enumeration
        return SecureErrorResponse(
            error_code="AUTH_001",
            message="Authentication failed. Please check your credentials.",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHENTICATION,
            error_id=error_id,
            timestamp=timestamp.isoformat()
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error handling statistics (would be implemented with metrics collection)"""
        return {
            "error_categories": len(ErrorCategory),
            "severity_levels": len(ErrorSeverity),
            "error_codes_defined": len(self.error_codes),
            "debug_mode_enabled": self.enable_debug_mode,
            "sensitive_patterns_configured": len(SensitiveDataPattern.PATTERNS)
        }


# Global secure error handler instance
_error_handler = None


def get_secure_error_handler(debug_mode: bool = False) -> SecureErrorHandler:
    """Get or create global secure error handler"""
    global _error_handler
    if _error_handler is None:
        _error_handler = SecureErrorHandler(enable_debug_mode=debug_mode)
    return _error_handler


# Decorator for automatic error handling
def handle_errors_securely(include_details: bool = False):
    """Decorator for automatic secure error handling"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                handler = get_secure_error_handler()
                error_response = handler.handle_error(
                    error=e,
                    include_details=include_details
                )
                # Return error response or raise as needed by the application
                return error_response
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_secure_error_handler()
                error_response = handler.handle_error(
                    error=e,
                    include_details=include_details
                )
                return error_response
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Convenience functions
def create_error_context(
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    **additional_context
) -> ErrorContext:
    """Create error context for tracking"""
    return ErrorContext(
        error_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        user_id=user_id,
        request_id=request_id,
        endpoint=endpoint,
        ip_address=ip_address,
        user_agent=user_agent,
        additional_context=additional_context
    )