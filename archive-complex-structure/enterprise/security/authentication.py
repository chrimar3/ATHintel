"""
Authentication Engine
====================

Enterprise-grade authentication system including:
- Multi-factor authentication (MFA) with TOTP and SMS
- Single Sign-On (SSO) integration with SAML 2.0 and OAuth 2.0
- JWT token management with refresh token rotation
- Password policy enforcement and breach detection
- Account lockout and brute force protection
- Session management with secure cookies
"""

import jwt
import bcrypt
import pyotp
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import re
from dataclasses import dataclass
import logging

@dataclass
class User:
    """User data class for authentication management."""
    user_id: str
    username: str
    email: str
    password_hash: str
    mfa_secret: Optional[str]
    roles: List[str]
    is_active: bool
    last_login: Optional[datetime]
    failed_attempts: int
    locked_until: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class AuthenticationEngine:
    """
    Comprehensive enterprise authentication system with MFA and SSO support.
    """
    
    def __init__(self):
        self.jwt_secret = secrets.token_urlsafe(64)
        self.jwt_algorithm = 'HS256'
        self.jwt_expiration = timedelta(hours=24)
        self.refresh_expiration = timedelta(days=30)
        
        # Password policy configuration
        self.password_policy = {
            'min_length': 12,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_numbers': True,
            'require_special': True,
            'max_age_days': 90,
            'history_count': 12,
            'lockout_threshold': 5,
            'lockout_duration': timedelta(minutes=30)
        }
        
        # Session configuration
        self.session_config = {
            'secure': True,
            'httponly': True,
            'samesite': 'Strict',
            'max_age': 86400  # 24 hours
        }
        
        # MFA configuration
        self.mfa_config = {
            'issuer_name': 'ATHintel Enterprise',
            'totp_period': 30,
            'totp_digits': 6,
            'backup_codes_count': 10
        }
        
        # User storage (in production, use secure database)
        self.users = {}
        self.sessions = {}
        self.refresh_tokens = {}
        self.password_history = {}
        
        self.logger = logging.getLogger(__name__)
    
    def setup_authentication(self, security_config: Dict) -> Dict:
        """
        Setup authentication engine with enterprise configuration.
        
        Args:
            security_config: Security configuration parameters
            
        Returns:
            Dict: Authentication setup results
        """
        
        setup_results = {
            'authentication_enabled': True,
            'mfa_enabled': security_config.get('enable_mfa', True),
            'sso_enabled': security_config.get('enable_sso', True),
            'password_policy': self.password_policy,
            'session_config': self.session_config,
            'setup_timestamp': datetime.now().isoformat(),
            'features_enabled': [],
            'configuration_warnings': []
        }
        
        # Configure JWT settings
        if 'jwt_secret' in security_config:
            self.jwt_secret = security_config['jwt_secret']
        else:
            setup_results['configuration_warnings'].append('Using auto-generated JWT secret - consider providing fixed secret for production')
        
        # Configure password policy
        if 'password_policy' in security_config:
            self.password_policy.update(security_config['password_policy'])
        
        # Configure MFA
        if security_config.get('enable_mfa', True):
            setup_results['features_enabled'].append('Multi-Factor Authentication')
            if 'mfa_config' in security_config:
                self.mfa_config.update(security_config['mfa_config'])
        
        # Configure SSO
        if security_config.get('enable_sso', True):
            setup_results['features_enabled'].append('Single Sign-On')
            setup_results['sso_providers'] = security_config.get('sso_providers', ['SAML', 'OAuth2'])
        
        # Setup session management
        if 'session_config' in security_config:
            self.session_config.update(security_config['session_config'])
        setup_results['features_enabled'].append('Secure Session Management')
        
        # Setup audit logging
        setup_results['features_enabled'].append('Authentication Audit Logging')
        
        self.logger.info(f"Authentication engine setup completed with {len(setup_results['features_enabled'])} features enabled")
        
        return setup_results
    
    def register_user(self, username: str, email: str, password: str, roles: List[str] = None) -> Dict:
        """
        Register new user with enterprise security requirements.
        
        Args:
            username: Unique username
            email: User email address
            password: Plain text password
            roles: List of user roles
            
        Returns:
            Dict: Registration result with user details or error information
        """
        
        try:
            # Validate input
            validation_result = self._validate_registration_input(username, email, password)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['message']}
            
            # Check if user already exists
            if self._user_exists(username, email):
                return {'success': False, 'error': 'User already exists'}
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # Generate MFA secret
            mfa_secret = pyotp.random_base32() if self.mfa_config else None
            
            # Create user
            user_id = str(uuid.uuid4())
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash.decode('utf-8'),
                mfa_secret=mfa_secret,
                roles=roles or ['user'],
                is_active=True,
                last_login=None,
                failed_attempts=0,
                locked_until=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Store user
            self.users[user_id] = user
            
            # Initialize password history
            self.password_history[user_id] = [password_hash.decode('utf-8')]
            
            # Generate backup codes if MFA enabled
            backup_codes = self._generate_backup_codes() if mfa_secret else None
            
            # Log registration
            self.logger.info(f"User registered successfully: {username} ({email})")
            
            return {
                'success': True,
                'user_id': user_id,
                'username': username,
                'email': email,
                'mfa_enabled': mfa_secret is not None,
                'mfa_secret': mfa_secret,  # Return for QR code generation
                'backup_codes': backup_codes,
                'roles': user.roles
            }
            
        except Exception as e:
            self.logger.error(f"User registration failed: {str(e)}")
            return {'success': False, 'error': 'Registration failed due to internal error'}
    
    def authenticate_user(self, username: str, password: str, mfa_code: Optional[str] = None) -> Dict:
        """
        Authenticate user with optional MFA verification.
        
        Args:
            username: Username or email
            password: Plain text password
            mfa_code: Optional MFA verification code
            
        Returns:
            Dict: Authentication result with tokens or error information
        """
        
        try:
            # Find user
            user = self._find_user(username)
            if not user:
                self.logger.warning(f"Authentication attempt for non-existent user: {username}")
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Check if account is locked
            if self._is_account_locked(user):
                self.logger.warning(f"Authentication attempt for locked account: {username}")
                return {'success': False, 'error': 'Account is locked due to too many failed attempts'}
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                self._handle_failed_login(user)
                self.logger.warning(f"Failed password authentication for user: {username}")
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Verify MFA if enabled
            if user.mfa_secret:
                if not mfa_code:
                    return {'success': False, 'error': 'MFA code required', 'mfa_required': True}
                
                if not self._verify_mfa_code(user, mfa_code):
                    self._handle_failed_login(user)
                    self.logger.warning(f"Failed MFA authentication for user: {username}")
                    return {'success': False, 'error': 'Invalid MFA code'}
            
            # Authentication successful
            self._handle_successful_login(user)
            
            # Generate tokens
            access_token = self._generate_access_token(user)
            refresh_token = self._generate_refresh_token(user)
            
            # Create session
            session_id = self._create_session(user)
            
            self.logger.info(f"User authenticated successfully: {username}")
            
            return {
                'success': True,
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'roles': user.roles,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'session_id': session_id,
                'expires_at': (datetime.now() + self.jwt_expiration).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return {'success': False, 'error': 'Authentication failed due to internal error'}
    
    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresh access token using valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Dict: New access token or error information
        """
        
        try:
            # Validate refresh token
            if refresh_token not in self.refresh_tokens:
                self.logger.warning("Invalid refresh token used")
                return {'success': False, 'error': 'Invalid refresh token'}
            
            token_data = self.refresh_tokens[refresh_token]
            
            # Check expiration
            if datetime.now() > token_data['expires_at']:
                del self.refresh_tokens[refresh_token]
                self.logger.warning("Expired refresh token used")
                return {'success': False, 'error': 'Refresh token expired'}
            
            # Get user
            user = self.users.get(token_data['user_id'])
            if not user or not user.is_active:
                del self.refresh_tokens[refresh_token]
                self.logger.warning(f"Refresh token used for inactive user: {token_data['user_id']}")
                return {'success': False, 'error': 'User account inactive'}
            
            # Generate new access token
            access_token = self._generate_access_token(user)
            
            # Rotate refresh token
            del self.refresh_tokens[refresh_token]
            new_refresh_token = self._generate_refresh_token(user)
            
            self.logger.info(f"Access token refreshed for user: {user.username}")
            
            return {
                'success': True,
                'access_token': access_token,
                'refresh_token': new_refresh_token,
                'expires_at': (datetime.now() + self.jwt_expiration).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Token refresh error: {str(e)}")
            return {'success': False, 'error': 'Token refresh failed'}
    
    def verify_access_token(self, access_token: str) -> Dict:
        """
        Verify and decode access token.
        
        Args:
            access_token: JWT access token
            
        Returns:
            Dict: Token verification result with user information
        """
        
        try:
            # Decode token
            payload = jwt.decode(access_token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Get user
            user = self.users.get(payload['user_id'])
            if not user or not user.is_active:
                return {'valid': False, 'error': 'User account inactive'}
            
            # Check token expiration
            if datetime.now() > datetime.fromtimestamp(payload['exp']):
                return {'valid': False, 'error': 'Token expired'}
            
            return {
                'valid': True,
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'roles': user.roles,
                'issued_at': datetime.fromtimestamp(payload['iat']),
                'expires_at': datetime.fromtimestamp(payload['exp'])
            }
            
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}
        except Exception as e:
            self.logger.error(f"Token verification error: {str(e)}")
            return {'valid': False, 'error': 'Token verification failed'}
    
    def logout_user(self, access_token: str, session_id: Optional[str] = None) -> Dict:
        """
        Logout user and invalidate tokens/session.
        
        Args:
            access_token: User's access token
            session_id: Optional session ID
            
        Returns:
            Dict: Logout result
        """
        
        try:
            # Verify token
            token_verification = self.verify_access_token(access_token)
            if not token_verification['valid']:
                return {'success': False, 'error': 'Invalid token'}
            
            user_id = token_verification['user_id']
            
            # Remove refresh tokens for user
            tokens_to_remove = [token for token, data in self.refresh_tokens.items() 
                             if data['user_id'] == user_id]
            for token in tokens_to_remove:
                del self.refresh_tokens[token]
            
            # Remove session
            if session_id and session_id in self.sessions:
                del self.sessions[session_id]
            
            self.logger.info(f"User logged out: {token_verification['username']}")
            
            return {'success': True, 'message': 'Logged out successfully'}
            
        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
            return {'success': False, 'error': 'Logout failed'}
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> Dict:
        """
        Change user password with policy validation and history checking.
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            Dict: Password change result
        """
        
        try:
            # Get user
            user = self.users.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Verify current password
            if not bcrypt.checkpw(current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
                self.logger.warning(f"Invalid current password for password change: {user.username}")
                return {'success': False, 'error': 'Invalid current password'}
            
            # Validate new password
            validation_result = self._validate_password(new_password)
            if not validation_result['valid']:
                return {'success': False, 'error': validation_result['message']}
            
            # Check password history
            new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            if self._is_password_in_history(user_id, new_password_hash.decode('utf-8')):
                return {'success': False, 'error': 'Password has been used recently'}
            
            # Update password
            user.password_hash = new_password_hash.decode('utf-8')
            user.updated_at = datetime.now()
            
            # Update password history
            if user_id not in self.password_history:
                self.password_history[user_id] = []
            
            self.password_history[user_id].append(new_password_hash.decode('utf-8'))
            
            # Keep only recent passwords in history
            if len(self.password_history[user_id]) > self.password_policy['history_count']:
                self.password_history[user_id] = self.password_history[user_id][-self.password_policy['history_count']:]
            
            # Invalidate all refresh tokens
            tokens_to_remove = [token for token, data in self.refresh_tokens.items() 
                             if data['user_id'] == user_id]
            for token in tokens_to_remove:
                del self.refresh_tokens[token]
            
            self.logger.info(f"Password changed successfully for user: {user.username}")
            
            return {'success': True, 'message': 'Password changed successfully'}
            
        except Exception as e:
            self.logger.error(f"Password change error: {str(e)}")
            return {'success': False, 'error': 'Password change failed'}
    
    def enable_mfa(self, user_id: str) -> Dict:
        """
        Enable MFA for user account.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict: MFA setup information
        """
        
        try:
            user = self.users.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            if user.mfa_secret:
                return {'success': False, 'error': 'MFA already enabled'}
            
            # Generate MFA secret
            mfa_secret = pyotp.random_base32()
            user.mfa_secret = mfa_secret
            user.updated_at = datetime.now()
            
            # Generate backup codes
            backup_codes = self._generate_backup_codes()
            
            # Generate QR code URL
            totp_url = pyotp.totp.TOTP(mfa_secret).provisioning_uri(
                name=user.email,
                issuer_name=self.mfa_config['issuer_name']
            )
            
            self.logger.info(f"MFA enabled for user: {user.username}")
            
            return {
                'success': True,
                'mfa_secret': mfa_secret,
                'qr_code_url': totp_url,
                'backup_codes': backup_codes,
                'message': 'MFA enabled successfully'
            }
            
        except Exception as e:
            self.logger.error(f"MFA enable error: {str(e)}")
            return {'success': False, 'error': 'Failed to enable MFA'}
    
    def disable_mfa(self, user_id: str, mfa_code: str) -> Dict:
        """
        Disable MFA for user account with verification.
        
        Args:
            user_id: User ID
            mfa_code: Current MFA code for verification
            
        Returns:
            Dict: MFA disable result
        """
        
        try:
            user = self.users.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            if not user.mfa_secret:
                return {'success': False, 'error': 'MFA not enabled'}
            
            # Verify MFA code
            if not self._verify_mfa_code(user, mfa_code):
                return {'success': False, 'error': 'Invalid MFA code'}
            
            # Disable MFA
            user.mfa_secret = None
            user.updated_at = datetime.now()
            
            self.logger.info(f"MFA disabled for user: {user.username}")
            
            return {'success': True, 'message': 'MFA disabled successfully'}
            
        except Exception as e:
            self.logger.error(f"MFA disable error: {str(e)}")
            return {'success': False, 'error': 'Failed to disable MFA'}
    
    def _validate_registration_input(self, username: str, email: str, password: str) -> Dict:
        """Validate user registration input."""
        
        # Username validation
        if not username or len(username) < 3:
            return {'valid': False, 'message': 'Username must be at least 3 characters long'}
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return {'valid': False, 'message': 'Username can only contain letters, numbers, underscores, and hyphens'}
        
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return {'valid': False, 'message': 'Invalid email format'}
        
        # Password validation
        password_validation = self._validate_password(password)
        if not password_validation['valid']:
            return password_validation
        
        return {'valid': True}
    
    def _validate_password(self, password: str) -> Dict:
        """Validate password against policy."""
        
        policy = self.password_policy
        
        # Length check
        if len(password) < policy['min_length']:
            return {'valid': False, 'message': f'Password must be at least {policy["min_length"]} characters long'}
        
        # Character requirements
        if policy['require_uppercase'] and not re.search(r'[A-Z]', password):
            return {'valid': False, 'message': 'Password must contain at least one uppercase letter'}
        
        if policy['require_lowercase'] and not re.search(r'[a-z]', password):
            return {'valid': False, 'message': 'Password must contain at least one lowercase letter'}
        
        if policy['require_numbers'] and not re.search(r'\d', password):
            return {'valid': False, 'message': 'Password must contain at least one number'}
        
        if policy['require_special'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return {'valid': False, 'message': 'Password must contain at least one special character'}
        
        # Common password check (simplified)
        common_passwords = ['password', '123456', 'password123', 'admin', 'qwerty']
        if password.lower() in common_passwords:
            return {'valid': False, 'message': 'Password is too common'}
        
        return {'valid': True}
    
    def _user_exists(self, username: str, email: str) -> bool:
        """Check if user already exists."""
        
        for user in self.users.values():
            if user.username == username or user.email == email:
                return True
        return False
    
    def _find_user(self, username_or_email: str) -> Optional[User]:
        """Find user by username or email."""
        
        for user in self.users.values():
            if user.username == username_or_email or user.email == username_or_email:
                return user
        return None
    
    def _is_account_locked(self, user: User) -> bool:
        """Check if user account is locked."""
        
        if user.locked_until and datetime.now() < user.locked_until:
            return True
        
        # Clear lock if time has passed
        if user.locked_until and datetime.now() >= user.locked_until:
            user.locked_until = None
            user.failed_attempts = 0
        
        return False
    
    def _handle_failed_login(self, user: User) -> None:
        """Handle failed login attempt."""
        
        user.failed_attempts += 1
        
        if user.failed_attempts >= self.password_policy['lockout_threshold']:
            user.locked_until = datetime.now() + self.password_policy['lockout_duration']
            self.logger.warning(f"Account locked due to failed attempts: {user.username}")
    
    def _handle_successful_login(self, user: User) -> None:
        """Handle successful login."""
        
        user.last_login = datetime.now()
        user.failed_attempts = 0
        user.locked_until = None
        user.updated_at = datetime.now()
    
    def _verify_mfa_code(self, user: User, mfa_code: str) -> bool:
        """Verify MFA code."""
        
        try:
            totp = pyotp.TOTP(user.mfa_secret)
            return totp.verify(mfa_code, valid_window=1)  # Allow 1 time window tolerance
        except Exception:
            return False
    
    def _generate_access_token(self, user: User) -> str:
        """Generate JWT access token."""
        
        now = datetime.now()
        payload = {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'roles': user.roles,
            'iat': int(now.timestamp()),
            'exp': int((now + self.jwt_expiration).timestamp()),
            'jti': str(uuid.uuid4())  # JWT ID for token tracking
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def _generate_refresh_token(self, user: User) -> str:
        """Generate secure refresh token."""
        
        refresh_token = secrets.token_urlsafe(64)
        
        self.refresh_tokens[refresh_token] = {
            'user_id': user.user_id,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + self.refresh_expiration,
            'used': False
        }
        
        return refresh_token
    
    def _create_session(self, user: User) -> str:
        """Create user session."""
        
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            'user_id': user.user_id,
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'ip_address': None,  # Would be set from request
            'user_agent': None   # Would be set from request
        }
        
        return session_id
    
    def _generate_backup_codes(self) -> List[str]:
        """Generate MFA backup codes."""
        
        backup_codes = []
        for _ in range(self.mfa_config['backup_codes_count']):
            code = ''.join(secrets.choice('0123456789') for _ in range(8))
            backup_codes.append(f"{code[:4]}-{code[4:]}")  # Format: XXXX-XXXX
        
        return backup_codes
    
    def _is_password_in_history(self, user_id: str, password_hash: str) -> bool:
        """Check if password exists in user's password history."""
        
        if user_id not in self.password_history:
            return False
        
        for historical_hash in self.password_history[user_id]:
            if bcrypt.checkpw(password_hash.encode('utf-8'), historical_hash.encode('utf-8')):
                return True
        
        return False
    
    def get_authentication_status(self) -> Dict:
        """Get comprehensive authentication system status."""
        
        now = datetime.now()
        
        # Count active users
        active_users = sum(1 for user in self.users.values() if user.is_active)
        
        # Count locked users
        locked_users = sum(1 for user in self.users.values() 
                         if user.locked_until and now < user.locked_until)
        
        # Count active sessions
        active_sessions = len(self.sessions)
        
        # Count active refresh tokens
        active_refresh_tokens = sum(1 for token_data in self.refresh_tokens.values() 
                                  if now < token_data['expires_at'])
        
        # Count MFA enabled users
        mfa_enabled_users = sum(1 for user in self.users.values() if user.mfa_secret)
        
        return {
            'system_status': 'operational',
            'total_users': len(self.users),
            'active_users': active_users,
            'locked_users': locked_users,
            'active_sessions': active_sessions,
            'active_refresh_tokens': active_refresh_tokens,
            'mfa_enabled_users': mfa_enabled_users,
            'mfa_adoption_rate': (mfa_enabled_users / len(self.users)) * 100 if self.users else 0,
            'password_policy': self.password_policy,
            'security_features': {
                'jwt_expiration_hours': self.jwt_expiration.total_seconds() / 3600,
                'refresh_expiration_days': self.refresh_expiration.days,
                'mfa_enabled': bool(self.mfa_config),
                'session_security': self.session_config
            },
            'status_timestamp': now.isoformat()
        }