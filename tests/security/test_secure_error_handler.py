"""
Security Testing Suite for Secure Error Handler
Tests for error sanitization and information disclosure prevention
"""

import pytest
import json
import re
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.utils.secure_error_handler import (
    SecureErrorHandler, ErrorContext, SensitiveDataPattern,
    ErrorClassifier, ErrorCategory, ErrorSeverity,
    get_secure_error_handler, create_error_context
)


class TestSensitiveDataPattern:
    """Test sensitive data pattern detection and sanitization"""

    def test_database_connection_sanitization(self):
        """Test database connection string sanitization"""
        test_cases = [
            "postgresql://user:password@localhost:5432/dbname",
            "postgresql://admin:secret123@db.example.com/production",
            "mysql://root:supersecret@127.0.0.1/test_db"
        ]
        
        for connection_string in test_cases:
            error_msg = f"Database connection failed: {connection_string}"
            sanitized = SensitiveDataPattern.sanitize_message(error_msg)
            
            # Should not contain original credentials
            assert "password" not in sanitized
            assert "secret123" not in sanitized
            assert "supersecret" not in sanitized
            
            # Should contain sanitized placeholder
            assert "postgresql://[REDACTED]/[DATABASE]" in sanitized

    def test_api_key_sanitization(self):
        """Test API key sanitization"""
        test_cases = [
            "API_KEY=abcdef1234567890abcdef1234567890",
            'api_key: "sk-1234567890abcdef1234567890abcdef"',
            "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ]
        
        for api_key_msg in test_cases:
            error_msg = f"API request failed: {api_key_msg}"
            sanitized = SensitiveDataPattern.sanitize_message(error_msg)
            
            # Should not contain actual keys
            assert "abcdef1234567890abcdef1234567890" not in sanitized
            assert "sk-1234567890abcdef1234567890abcdef" not in sanitized
            
            # Should contain redacted markers
            assert "[REDACTED]" in sanitized

    def test_password_sanitization(self):
        """Test password sanitization in error messages"""
        test_cases = [
            'password="SuperSecret123!"',
            "password: MyP@ssw0rd",
            "pwd=admin123"
        ]
        
        for password_msg in test_cases:
            error_msg = f"Authentication failed with {password_msg}"
            sanitized = SensitiveDataPattern.sanitize_message(error_msg)
            
            # Should not contain actual passwords
            assert "SuperSecret123!" not in sanitized
            assert "MyP@ssw0rd" not in sanitized
            assert "admin123" not in sanitized
            
            # Should contain redacted marker
            assert "PASSWORD:[REDACTED]" in sanitized

    def test_jwt_token_sanitization(self):
        """Test JWT token sanitization"""
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        error_msg = f"Token validation failed: {jwt_token}"
        
        sanitized = SensitiveDataPattern.sanitize_message(error_msg)
        
        # Should not contain actual JWT
        assert jwt_token not in sanitized
        assert "JWT_TOKEN:[REDACTED]" in sanitized

    def test_file_path_sanitization(self):
        """Test file path sanitization"""
        test_cases = [
            "/home/user/secret/config.ini",
            "/var/lib/app/credentials/database.conf",
            "C:\\Users\\admin\\Documents\\secrets.txt"
        ]
        
        for file_path in test_cases:
            error_msg = f"Failed to read file: {file_path}"
            sanitized = SensitiveDataPattern.sanitize_message(error_msg)
            
            # Should not contain actual paths
            assert file_path not in sanitized
            assert "/[PATH_REDACTED]" in sanitized

    def test_ip_address_sanitization(self):
        """Test IP address sanitization"""
        test_cases = [
            "192.168.1.100",
            "10.0.0.1",
            "172.16.254.1"
        ]
        
        for ip_address in test_cases:
            error_msg = f"Connection failed to {ip_address}"
            sanitized = SensitiveDataPattern.sanitize_message(error_msg)
            
            # Should not contain actual IP
            assert ip_address not in sanitized
            assert "[IP_ADDRESS_REDACTED]" in sanitized

    def test_email_sanitization(self):
        """Test email address sanitization"""
        test_cases = [
            "admin@company.com",
            "user.test@example.org"
        ]
        
        for email in test_cases:
            error_msg = f"Failed to send notification to {email}"
            sanitized = SensitiveDataPattern.sanitize_message(error_msg)
            
            # Should not contain actual email
            assert email not in sanitized
            assert "[EMAIL_REDACTED]" in sanitized

    def test_uuid_sanitization(self):
        """Test UUID sanitization"""
        test_cases = [
            "123e4567-e89b-12d3-a456-426614174000",
            "550e8400-e29b-41d4-a716-446655440000"
        ]
        
        for uuid in test_cases:
            error_msg = f"Failed to process user {uuid}"
            sanitized = SensitiveDataPattern.sanitize_message(error_msg)
            
            # Should not contain actual UUID
            assert uuid not in sanitized
            assert "[UUID_REDACTED]" in sanitized


class TestErrorClassifier:
    """Test error classification system"""

    def test_authentication_error_classification(self):
        """Test authentication error classification"""
        test_cases = [
            ("Invalid credentials provided", ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
            ("JWT token expired", ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
            ("Authentication failed", ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH),
        ]
        
        for error_msg, expected_category, expected_severity in test_cases:
            exception = ValueError(error_msg)
            category, severity = ErrorClassifier.classify_error(exception, error_msg)
            
            assert category == expected_category
            assert severity == expected_severity

    def test_authorization_error_classification(self):
        """Test authorization error classification"""
        test_cases = [
            ("Access denied", ErrorCategory.AUTHORIZATION, ErrorSeverity.MEDIUM),
            ("Insufficient permissions", ErrorCategory.AUTHORIZATION, ErrorSeverity.MEDIUM),
            ("Permission denied", ErrorCategory.AUTHORIZATION, ErrorSeverity.MEDIUM),
        ]
        
        for error_msg, expected_category, expected_severity in test_cases:
            exception = PermissionError(error_msg)
            category, severity = ErrorClassifier.classify_error(exception, error_msg)
            
            assert category == expected_category
            assert severity == expected_severity

    def test_validation_error_classification(self):
        """Test validation error classification"""
        test_cases = [
            ("Invalid input format", ErrorCategory.VALIDATION, ErrorSeverity.LOW),
            ("Missing required field", ErrorCategory.VALIDATION, ErrorSeverity.LOW),
            ("Bad request format", ErrorCategory.VALIDATION, ErrorSeverity.LOW),
        ]
        
        for error_msg, expected_category, expected_severity in test_cases:
            exception = ValueError(error_msg)
            category, severity = ErrorClassifier.classify_error(exception, error_msg)
            
            assert category == expected_category
            assert severity == expected_severity

    def test_database_error_classification(self):
        """Test database error classification"""
        test_cases = [
            ("Connection refused", ErrorCategory.DATABASE, ErrorSeverity.CRITICAL),
            ("Database deadlock detected", ErrorCategory.DATABASE, ErrorSeverity.CRITICAL),
            ("Table does not exist", ErrorCategory.DATABASE, ErrorSeverity.CRITICAL),
        ]
        
        for error_msg, expected_category, expected_severity in test_cases:
            exception = ConnectionError(error_msg)
            category, severity = ErrorClassifier.classify_error(exception, error_msg)
            
            assert category == expected_category
            assert severity == expected_severity

    def test_external_service_error_classification(self):
        """Test external service error classification"""
        test_cases = [
            ("Service unavailable", ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH),
            ("Connection timeout", ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH),
            ("Circuit breaker open", ErrorCategory.EXTERNAL_SERVICE, ErrorSeverity.HIGH),
        ]
        
        for error_msg, expected_category, expected_severity in test_cases:
            exception = TimeoutError(error_msg)
            category, severity = ErrorClassifier.classify_error(exception, error_msg)
            
            assert category == expected_category
            assert severity == expected_severity

    def test_system_resource_error_classification(self):
        """Test system resource error classification"""
        test_cases = [
            ("Out of memory", ErrorCategory.SYSTEM_RESOURCE, ErrorSeverity.CRITICAL),
            ("Disk full", ErrorCategory.SYSTEM_RESOURCE, ErrorSeverity.CRITICAL),
            ("Too many open files", ErrorCategory.SYSTEM_RESOURCE, ErrorSeverity.CRITICAL),
        ]
        
        for error_msg, expected_category, expected_severity in test_cases:
            exception = OSError(error_msg)
            category, severity = ErrorClassifier.classify_error(exception, error_msg)
            
            assert category == expected_category
            assert severity == expected_severity


class TestSecureErrorHandler:
    """Test secure error handler functionality"""

    @pytest.fixture
    def error_handler(self):
        """Create error handler instance"""
        return SecureErrorHandler(enable_debug_mode=False)

    @pytest.fixture
    def debug_error_handler(self):
        """Create error handler with debug mode enabled"""
        return SecureErrorHandler(enable_debug_mode=True)

    @pytest.fixture
    def error_context(self):
        """Create sample error context"""
        return ErrorContext(
            error_id="test-error-123",
            timestamp=datetime.now(),
            user_id="user_123",
            request_id="req_456",
            endpoint="/api/properties",
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )

    def test_production_error_sanitization(self, error_handler):
        """Test error sanitization in production mode"""
        # Create error with sensitive information
        sensitive_error = ValueError("Database connection failed: postgresql://admin:secret123@db.example.com/prod")
        
        response = error_handler.handle_error(sensitive_error)
        
        # Should not contain sensitive information
        assert "admin" not in response.message
        assert "secret123" not in response.message
        assert "db.example.com" not in response.message
        
        # Should use generic message in production
        assert response.message == "An error occurred"
        assert response.error_code.startswith("VALID")

    def test_debug_mode_sanitization(self, debug_error_handler):
        """Test error sanitization in debug mode"""
        # Create error with sensitive information
        sensitive_error = ValueError("API key invalid: sk-1234567890abcdef1234567890abcdef")
        
        response = debug_error_handler.handle_error(sensitive_error)
        
        # Should contain sanitized version in debug mode
        assert "API_KEY:[REDACTED]" in response.message
        # Should not contain actual API key
        assert "sk-1234567890abcdef1234567890abcdef" not in response.message

    def test_authentication_error_handling(self, error_handler, error_context):
        """Test authentication error handling"""
        response = error_handler.handle_authentication_error(
            "Invalid username or password",
            context=error_context
        )
        
        # Should use generic authentication message
        assert response.message == "Authentication failed. Please check your credentials."
        assert response.category == ErrorCategory.AUTHENTICATION
        assert response.severity == ErrorSeverity.HIGH
        assert response.error_code == "AUTH_001"

    def test_validation_error_handling(self, error_handler, error_context):
        """Test validation error handling"""
        validation_errors = [
            "Property ID is required",
            "Price must be a positive number",
            "Invalid email format: not_an_email"
        ]
        
        response = error_handler.handle_validation_error(
            validation_errors,
            context=error_context
        )
        
        assert response.category == ErrorCategory.VALIDATION
        assert response.severity == ErrorSeverity.LOW
        assert response.error_code == "VALID_001"
        assert "validation_errors" in response.details
        
        # Should sanitize email in validation errors
        sanitized_errors = response.details["validation_errors"]
        assert any("[EMAIL_REDACTED]" in error for error in sanitized_errors)

    @patch('src.utils.secure_error_handler.logger')
    def test_audit_logging(self, mock_logger, error_handler, error_context):
        """Test security audit logging"""
        error = ValueError("Database connection failed")
        
        response = error_handler.handle_error(
            error,
            context=error_context,
            include_details=True
        )
        
        # Verify audit logging was called
        mock_logger.warning.assert_called()
        
        # Check log contains context but not sensitive data
        log_calls = mock_logger.warning.call_args_list
        assert any("error_id" in str(call) for call in log_calls)
        assert any("user_id" in str(call) for call in log_calls)

    def test_error_response_structure(self, error_handler):
        """Test error response structure and serialization"""
        error = ValueError("Test error message")
        response = error_handler.handle_error(error, include_details=True)
        
        # Test response structure
        assert hasattr(response, 'error_code')
        assert hasattr(response, 'message')
        assert hasattr(response, 'severity')
        assert hasattr(response, 'category')
        assert hasattr(response, 'error_id')
        assert hasattr(response, 'timestamp')
        
        # Test serialization
        response_dict = response.to_dict()
        assert 'error' in response_dict
        assert 'code' in response_dict['error']
        assert 'message' in response_dict['error']
        assert 'severity' in response_dict['error']
        assert 'category' in response_dict['error']

    def test_stack_trace_sanitization(self, error_handler):
        """Test stack trace sanitization for high severity errors"""
        # Create error that would be classified as high severity
        database_error = ConnectionError("Database connection refused")
        
        with patch('src.utils.secure_error_handler.logger') as mock_logger:
            response = error_handler.handle_error(database_error)
            
            # Should log stack trace for critical errors
            mock_logger.critical.assert_called()
            
            # Verify stack trace is included in internal logs
            log_call_args = mock_logger.critical.call_args
            if log_call_args and 'extra' in log_call_args[1]:
                error_data = json.loads(log_call_args[1]['extra']['error_data'])
                assert 'stack_trace' in error_data

    def test_concurrent_error_handling(self, error_handler):
        """Test thread-safe error handling"""
        import asyncio
        import threading
        
        errors = [
            ValueError("Validation error 1"),
            ConnectionError("Database error 2"),
            TimeoutError("Service timeout 3"),
            PermissionError("Access denied 4"),
        ]
        
        results = []
        
        def handle_error(error):
            response = error_handler.handle_error(error)
            results.append(response)
        
        # Create threads for concurrent error handling
        threads = []
        for error in errors:
            thread = threading.Thread(target=handle_error, args=(error,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all errors were handled
        assert len(results) == 4
        
        # Verify each response has unique error ID
        error_ids = [r.error_id for r in results]
        assert len(set(error_ids)) == 4  # All unique

    def test_custom_message_sanitization(self, error_handler):
        """Test custom error message sanitization"""
        error = ValueError("Original error")
        custom_message = "Custom error with API key: sk-abcdef1234567890abcdef1234567890"
        
        response = error_handler.handle_error(
            error,
            custom_message=custom_message
        )
        
        # In production mode, should use generic message
        assert response.message != custom_message
        assert "sk-abcdef1234567890abcdef1234567890" not in response.message

    def test_safe_details_preparation(self, error_handler, error_context):
        """Test safe details preparation for error responses"""
        # Add sensitive context
        error_context.additional_context = {
            "property_id": "prop_123",
            "api_key": "sensitive_key_value",  # Should be filtered out
            "user_input": "safe_value",
            "database_url": "postgresql://user:pass@localhost/db"  # Should be sanitized
        }
        
        error = ValueError("Test error")
        response = error_handler.handle_error(
            error,
            context=error_context,
            include_details=True
        )
        
        # Should include safe details
        assert response.details is not None
        assert "endpoint" in response.details
        assert "request_id" in response.details
        
        # Should include sanitized context
        if "context" in response.details:
            context_data = response.details["context"]
            assert "api_key" not in context_data  # Filtered out
            assert "property_id" in context_data  # Safe value included
            
            # Database URL should be sanitized
            if "database_url" in context_data:
                assert "postgresql://[REDACTED]/[DATABASE]" in context_data["database_url"]


class TestErrorHandlerIntegration:
    """Integration tests for error handler"""

    def test_error_handling_decorator(self):
        """Test error handling decorator functionality"""
        from src.utils.secure_error_handler import handle_errors_securely
        
        @handle_errors_securely(include_details=False)
        def test_function():
            raise ValueError("Test error with sensitive data: password=secret123")
        
        result = test_function()
        
        # Should return SecureErrorResponse
        assert hasattr(result, 'error_code')
        assert hasattr(result, 'message')
        
        # Should not contain sensitive data
        assert "secret123" not in result.message

    async def test_async_error_handling_decorator(self):
        """Test async error handling decorator"""
        from src.utils.secure_error_handler import handle_errors_securely
        
        @handle_errors_securely(include_details=True)
        async def test_async_function():
            raise ConnectionError("Database error with connection string: postgresql://user:pass@db/prod")
        
        result = await test_async_function()
        
        # Should return SecureErrorResponse
        assert hasattr(result, 'error_code')
        assert result.category == ErrorCategory.DATABASE
        
        # Should sanitize connection string
        assert "postgresql://user:pass@db/prod" not in str(result.__dict__)

    def test_global_error_handler_instance(self):
        """Test global error handler singleton"""
        handler1 = get_secure_error_handler()
        handler2 = get_secure_error_handler()
        
        # Should return same instance
        assert handler1 is handler2

    def test_error_context_creation(self):
        """Test error context creation helper"""
        context = create_error_context(
            user_id="test_user",
            endpoint="/api/test",
            custom_field="custom_value"
        )
        
        assert context.user_id == "test_user"
        assert context.endpoint == "/api/test"
        assert context.additional_context["custom_field"] == "custom_value"
        assert context.error_id is not None
        assert context.timestamp is not None


# Security-specific test scenarios
@pytest.mark.parametrize("error_type,expected_category", [
    ("Authentication failed", ErrorCategory.AUTHENTICATION),
    ("Access denied", ErrorCategory.AUTHORIZATION),
    ("Invalid input", ErrorCategory.VALIDATION),
    ("Database error", ErrorCategory.DATABASE),
    ("Service timeout", ErrorCategory.EXTERNAL_SERVICE),
    ("Out of memory", ErrorCategory.SYSTEM_RESOURCE),
    ("Config missing", ErrorCategory.CONFIGURATION),
])
def test_error_category_mapping(error_type, expected_category):
    """Test error type to category mapping"""
    error = ValueError(error_type)
    category, _ = ErrorClassifier.classify_error(error, error_type)
    assert category == expected_category


@pytest.mark.parametrize("sensitive_data", [
    "postgresql://user:password@host/db",
    "api_key=sk-1234567890abcdef",
    "password=secret123",
    "jwt=eyJhbGciOiJIUzI1NiIs",
    "/home/user/secret/config",
    "192.168.1.100",
    "admin@company.com",
    "123e4567-e89b-12d3-a456-426614174000"
])
def test_comprehensive_sanitization(sensitive_data):
    """Test comprehensive sanitization of various sensitive data types"""
    error_message = f"Error occurred with {sensitive_data}"
    sanitized = SensitiveDataPattern.sanitize_message(error_message)
    
    # Should not contain original sensitive data
    assert sensitive_data not in sanitized
    
    # Should contain some form of redaction
    assert "[REDACTED]" in sanitized or "[PATH_REDACTED]" in sanitized or "[DATABASE]" in sanitized


# Performance testing for error handling
@pytest.mark.slow
def test_error_handler_performance():
    """Test error handler performance under load"""
    import time
    
    handler = SecureErrorHandler()
    
    # Test handling many errors quickly
    start_time = time.perf_counter()
    
    for i in range(1000):
        error = ValueError(f"Test error {i} with sensitive data: api_key=secret_{i}")
        response = handler.handle_error(error)
        assert "secret_" not in response.message
    
    elapsed = time.perf_counter() - start_time
    
    # Should handle 1000 errors in reasonable time
    assert elapsed < 2.0, f"Error handling took {elapsed:.2f}s (too slow)"


# Memory usage testing
def test_error_handler_memory_efficiency():
    """Test error handler doesn't leak memory"""
    import gc
    import sys
    
    handler = SecureErrorHandler()
    
    # Get initial memory usage
    gc.collect()
    initial_objects = len(gc.get_objects())
    
    # Handle many errors
    for i in range(100):
        error = ValueError(f"Memory test error {i}")
        response = handler.handle_error(error)
        del response  # Explicitly delete
    
    # Force garbage collection
    gc.collect()
    final_objects = len(gc.get_objects())
    
    # Should not have significant object leakage
    object_increase = final_objects - initial_objects
    assert object_increase < 50, f"Potential memory leak: {object_increase} new objects"