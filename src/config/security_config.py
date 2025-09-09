"""
🛡️ Security Configuration Management

This module provides secure configuration management for all security-related
settings, implementing environment-based secret management and encryption.

Critical Security Features:
✅ Environment-based secret management
✅ Secret rotation support
✅ Encryption key management
✅ Secure default configurations
✅ Production security validation
✅ Audit logging for configuration changes

Usage:
    from config.security_config import SecurityConfig
    
    config = SecurityConfig()
    jwt_secret = config.get_jwt_secret()
    db_encryption_key = config.get_db_encryption_key()
"""

import os
import secrets
import base64
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class SecurityConfigException(Exception):
    """Exception for security configuration errors"""
    pass

class SecurityConfig:
    """
    Secure configuration management for ATHintel platform
    
    Handles all security-sensitive configuration including:
    - JWT secrets and encryption keys
    - Database encryption configuration
    - API rate limiting settings
    - File operation security settings
    - Audit and logging configuration
    """
    
    def __init__(self, environment: str = None):
        """
        Initialize security configuration
        
        Args:
            environment: Environment name (development, staging, production)
        """
        self.environment = environment or os.getenv('ATHINTEL_ENV', 'development')
        self.config_dir = Path("config/security")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption for storing secrets
        self._init_encryption()
        
        # Load configuration
        self.config = self._load_security_config()
        
        # Validate configuration for production
        if self.environment == 'production':
            self._validate_production_config()
        
        logger.info(f"🛡️ SecurityConfig initialized for {self.environment} environment")
    
    def _init_encryption(self):
        """Initialize encryption for local secret storage"""
        key_file = self.config_dir / "master.key"
        
        if key_file.exists():
            # Load existing key
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set secure permissions (readable only by owner)
            os.chmod(key_file, 0o600)
            logger.info("🔑 Generated new master encryption key")
        
        self.cipher = Fernet(key)
    
    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration from environment and files"""
        config = {}
        
        # JWT Configuration
        config['jwt'] = {
            'secret_key': self._get_jwt_secret(),
            'algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
            'access_token_expire_hours': int(os.getenv('JWT_ACCESS_EXPIRE_HOURS', '24')),
            'refresh_token_expire_days': int(os.getenv('JWT_REFRESH_EXPIRE_DAYS', '30')),
            'issuer': os.getenv('JWT_ISSUER', 'athintel.com'),
            'audience': os.getenv('JWT_AUDIENCE', 'athintel-api')
        }
        
        # Database Configuration
        config['database'] = {
            'encryption_key': self._get_db_encryption_key(),
            'enable_encryption': os.getenv('DB_ENCRYPTION_ENABLED', 'true').lower() == 'true',
            'connection_timeout': int(os.getenv('DB_CONNECTION_TIMEOUT', '30')),
            'max_connections': int(os.getenv('DB_MAX_CONNECTIONS', '100')),
            'ssl_mode': os.getenv('DB_SSL_MODE', 'require'),
            'audit_enabled': os.getenv('DB_AUDIT_ENABLED', 'true').lower() == 'true'
        }
        
        # API Security Configuration
        config['api'] = {
            'rate_limit_per_minute': int(os.getenv('API_RATE_LIMIT_MINUTE', '100')),
            'rate_limit_per_hour': int(os.getenv('API_RATE_LIMIT_HOUR', '1000')),
            'max_request_size': int(os.getenv('API_MAX_REQUEST_SIZE', '10485760')),  # 10MB
            'enable_cors': os.getenv('API_ENABLE_CORS', 'false').lower() == 'true',
            'allowed_origins': os.getenv('API_ALLOWED_ORIGINS', '').split(','),
            'require_https': os.getenv('API_REQUIRE_HTTPS', 'true').lower() == 'true',
            'session_timeout': int(os.getenv('API_SESSION_TIMEOUT', '3600'))
        }
        
        # File Security Configuration
        config['file_operations'] = {
            'max_file_size': int(os.getenv('FILE_MAX_SIZE', '52428800')),  # 50MB
            'allowed_extensions': os.getenv('FILE_ALLOWED_EXTENSIONS', 
                '.json,.csv,.txt,.md,.yaml,.yml,.log,.jsonl,.xml,.html,.pdf,.png,.jpg,.jpeg,.gif,.webp').split(','),
            'scan_uploads': os.getenv('FILE_SCAN_UPLOADS', 'true').lower() == 'true',
            'quarantine_suspicious': os.getenv('FILE_QUARANTINE_SUSPICIOUS', 'true').lower() == 'true'
        }
        
        # Audit and Logging Configuration
        config['audit'] = {
            'enable_security_logging': os.getenv('AUDIT_SECURITY_ENABLED', 'true').lower() == 'true',
            'enable_api_logging': os.getenv('AUDIT_API_ENABLED', 'true').lower() == 'true',
            'enable_file_logging': os.getenv('AUDIT_FILE_ENABLED', 'true').lower() == 'true',
            'log_retention_days': int(os.getenv('AUDIT_RETENTION_DAYS', '90')),
            'compress_logs': os.getenv('AUDIT_COMPRESS_LOGS', 'true').lower() == 'true',
            'remote_logging': os.getenv('AUDIT_REMOTE_ENDPOINT', '')
        }
        
        # Energy Assessment Configuration
        config['energy'] = {
            'max_assessment_batch_size': int(os.getenv('ENERGY_MAX_BATCH_SIZE', '100')),
            'assessment_timeout': int(os.getenv('ENERGY_ASSESSMENT_TIMEOUT', '300')),
            'cache_assessments': os.getenv('ENERGY_CACHE_ENABLED', 'true').lower() == 'true',
            'confidence_threshold': float(os.getenv('ENERGY_CONFIDENCE_THRESHOLD', '0.6')),
            'max_upgrade_budget': float(os.getenv('ENERGY_MAX_UPGRADE_BUDGET', '50000'))
        }
        
        return config
    
    def _get_jwt_secret(self) -> str:
        """Get JWT secret from environment or generate secure default"""
        # First, try to get from environment
        secret = os.getenv('JWT_SECRET_KEY')
        if secret:
            return secret
        
        # Try to load from encrypted storage
        secret_file = self.config_dir / "jwt_secret.enc"
        if secret_file.exists():
            try:
                with open(secret_file, 'rb') as f:
                    encrypted_secret = f.read()
                return self.cipher.decrypt(encrypted_secret).decode()
            except Exception as e:
                logger.warning(f"Failed to decrypt JWT secret: {e}")
        
        # Generate new secret if not found
        if self.environment == 'production':
            raise SecurityConfigException(
                "JWT_SECRET_KEY environment variable is required in production"
            )
        
        # Generate and store new secret for development
        new_secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        
        try:
            encrypted_secret = self.cipher.encrypt(new_secret.encode())
            with open(secret_file, 'wb') as f:
                f.write(encrypted_secret)
            os.chmod(secret_file, 0o600)
            logger.warning("🔑 Generated new JWT secret for development - set JWT_SECRET_KEY for production")
        except Exception as e:
            logger.error(f"Failed to store JWT secret: {e}")
        
        return new_secret
    
    def _get_db_encryption_key(self) -> str:
        """Get database encryption key from environment or generate secure default"""
        # First, try to get from environment
        key = os.getenv('DB_ENCRYPTION_KEY')
        if key:
            return key
        
        # Try to load from encrypted storage
        key_file = self.config_dir / "db_key.enc"
        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    encrypted_key = f.read()
                return self.cipher.decrypt(encrypted_key).decode()
            except Exception as e:
                logger.warning(f"Failed to decrypt DB key: {e}")
        
        # Generate new key if not found
        if self.environment == 'production':
            raise SecurityConfigException(
                "DB_ENCRYPTION_KEY environment variable is required in production"
            )
        
        # Generate and store new key for development
        new_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        
        try:
            encrypted_key = self.cipher.encrypt(new_key.encode())
            with open(key_file, 'wb') as f:
                f.write(encrypted_key)
            os.chmod(key_file, 0o600)
            logger.warning("🔑 Generated new DB encryption key for development - set DB_ENCRYPTION_KEY for production")
        except Exception as e:
            logger.error(f"Failed to store DB encryption key: {e}")
        
        return new_key
    
    def _validate_production_config(self):
        """Validate security configuration for production environment"""
        errors = []
        
        # Check for required environment variables
        required_env_vars = [
            'JWT_SECRET_KEY',
            'DB_ENCRYPTION_KEY',
            'API_ALLOWED_ORIGINS'
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                errors.append(f"Missing required environment variable: {var}")
        
        # Validate JWT secret strength
        jwt_secret = os.getenv('JWT_SECRET_KEY', '')
        if len(jwt_secret) < 32:
            errors.append("JWT_SECRET_KEY must be at least 32 characters for production")
        
        # Validate HTTPS requirement
        if not self.config['api']['require_https']:
            errors.append("HTTPS must be required in production (API_REQUIRE_HTTPS=true)")
        
        # Validate CORS configuration
        if self.config['api']['enable_cors'] and not self.config['api']['allowed_origins']:
            errors.append("CORS origins must be explicitly configured in production")
        
        if errors:
            error_msg = "Production security validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise SecurityConfigException(error_msg)
        
        logger.info("✅ Production security configuration validated")
    
    # Configuration getter methods
    
    def get_jwt_config(self) -> Dict[str, Any]:
        """Get JWT configuration"""
        return self.config['jwt'].copy()
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret key"""
        return self.config['jwt']['secret_key']
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config['database'].copy()
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API security configuration"""
        return self.config['api'].copy()
    
    def get_file_config(self) -> Dict[str, Any]:
        """Get file operations configuration"""
        return self.config['file_operations'].copy()
    
    def get_audit_config(self) -> Dict[str, Any]:
        """Get audit configuration"""
        return self.config['audit'].copy()
    
    def get_energy_config(self) -> Dict[str, Any]:
        """Get energy assessment configuration"""
        return self.config['energy'].copy()
    
    # Security utilities
    
    def generate_api_key(self, user_id: str) -> str:
        """Generate secure API key for user"""
        timestamp = str(int(datetime.now().timestamp()))
        data = f"{user_id}:{timestamp}:{secrets.token_urlsafe(16)}"
        return base64.urlsafe_b64encode(data.encode()).decode()
    
    def rotate_secrets(self) -> Dict[str, str]:
        """Rotate JWT and encryption secrets (for scheduled rotation)"""
        if self.environment == 'production':
            raise SecurityConfigException("Secret rotation must be done through secure CI/CD pipeline in production")
        
        rotated = {}
        
        # Rotate JWT secret
        new_jwt_secret = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        secret_file = self.config_dir / "jwt_secret.enc"
        encrypted_secret = self.cipher.encrypt(new_jwt_secret.encode())
        with open(secret_file, 'wb') as f:
            f.write(encrypted_secret)
        rotated['jwt_secret'] = 'rotated'
        
        # Rotate DB encryption key
        new_db_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        key_file = self.config_dir / "db_key.enc"
        encrypted_key = self.cipher.encrypt(new_db_key.encode())
        with open(key_file, 'wb') as f:
            f.write(encrypted_key)
        rotated['db_key'] = 'rotated'
        
        # Reload configuration
        self.config = self._load_security_config()
        
        logger.info("🔄 Security secrets rotated")
        return rotated
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get recommended security headers for HTTP responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
        }
    
    def validate_request_size(self, size: int) -> bool:
        """Validate request size against configured limits"""
        return size <= self.config['api']['max_request_size']
    
    def is_allowed_file_extension(self, extension: str) -> bool:
        """Check if file extension is allowed"""
        return extension.lower() in self.config['file_operations']['allowed_extensions']
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment and configuration info (for debugging)"""
        return {
            'environment': self.environment,
            'config_loaded': datetime.now().isoformat(),
            'jwt_algorithm': self.config['jwt']['algorithm'],
            'db_encryption_enabled': self.config['database']['enable_encryption'],
            'api_require_https': self.config['api']['require_https'],
            'audit_enabled': self.config['audit']['enable_security_logging']
        }

# Global security config instance
_security_config = None

def get_security_config() -> SecurityConfig:
    """Get global security configuration instance"""
    global _security_config
    if _security_config is None:
        _security_config = SecurityConfig()
    return _security_config

def reset_security_config():
    """Reset global security configuration (for testing)"""
    global _security_config
    _security_config = None

if __name__ == "__main__":
    # Configuration validation and testing
    print("🧪 Testing Security Configuration...")
    
    config = SecurityConfig()
    
    print(f"Environment: {config.environment}")
    print(f"JWT Secret Length: {len(config.get_jwt_secret())} characters")
    print(f"DB Encryption: {'✅ Enabled' if config.get_database_config()['enable_encryption'] else '❌ Disabled'}")
    print(f"API HTTPS Required: {'✅ Yes' if config.get_api_config()['require_https'] else '❌ No'}")
    print(f"Audit Logging: {'✅ Enabled' if config.get_audit_config()['enable_security_logging'] else '❌ Disabled'}")
    
    # Test security headers
    headers = config.get_security_headers()
    print(f"Security Headers: {len(headers)} configured")
    
    # Test environment info
    env_info = config.get_environment_info()
    print(f"Configuration Info: {env_info}")
    
    print("✅ Security configuration test completed")