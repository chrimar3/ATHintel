"""
🔐 Secure Credential Management System

Enterprise-grade credential management with HashiCorp Vault integration:
- Encrypted storage for database passwords and API keys
- Automatic credential rotation and validation
- Secure environment variable handling
- Audit logging for credential access
- Fallback mechanisms for high availability
"""

import os
import json
import logging
import asyncio
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# HashiCorp Vault integration (optional dependency)
try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    logging.warning("HashiCorp Vault client not available, using local encryption")

logger = logging.getLogger(__name__)


class CredentialType(Enum):
    """Types of credentials managed"""
    DATABASE_PASSWORD = "database_password"
    API_KEY = "api_key"
    ENCRYPTION_KEY = "encryption_key"
    JWT_SECRET = "jwt_secret"
    EXTERNAL_SERVICE_TOKEN = "external_service_token"


@dataclass
class CredentialMetadata:
    """Metadata for credential tracking"""
    credential_id: str
    credential_type: CredentialType
    created_at: datetime
    expires_at: Optional[datetime]
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    source: str = "vault"  # vault, env, encrypted_file
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SecureCredential:
    """Secure credential container"""
    credential_id: str
    value: str
    metadata: CredentialMetadata
    masked_value: str = field(init=False)
    
    def __post_init__(self):
        """Create masked version for logging"""
        if len(self.value) <= 8:
            self.masked_value = "*" * len(self.value)
        else:
            self.masked_value = self.value[:4] + "*" * (len(self.value) - 8) + self.value[-4:]


class VaultCredentialManager:
    """
    HashiCorp Vault integration for credential management
    """
    
    def __init__(self, vault_url: str, vault_token: str, mount_point: str = "secret"):
        if not VAULT_AVAILABLE:
            raise ImportError("HashiCorp Vault client (hvac) is required for VaultCredentialManager")
        
        self.vault_url = vault_url
        self.mount_point = mount_point
        self.client = hvac.Client(url=vault_url, token=vault_token)
        
        # Verify Vault connection
        if not self.client.is_authenticated():
            raise ConnectionError("Failed to authenticate with HashiCorp Vault")
        
        logger.info(f"Connected to HashiCorp Vault at {vault_url}")
    
    async def store_credential(
        self,
        credential_id: str,
        credential_type: CredentialType,
        value: str,
        expires_at: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> CredentialMetadata:
        """Store credential in Vault"""
        try:
            path = f"{self.mount_point}/data/{credential_type.value}/{credential_id}"
            
            metadata = CredentialMetadata(
                credential_id=credential_id,
                credential_type=credential_type,
                created_at=datetime.now(),
                expires_at=expires_at,
                source="vault",
                tags=tags or {}
            )
            
            # Store in Vault with metadata
            vault_data = {
                "data": {
                    "value": value,
                    "metadata": {
                        "credential_id": credential_id,
                        "credential_type": credential_type.value,
                        "created_at": metadata.created_at.isoformat(),
                        "expires_at": expires_at.isoformat() if expires_at else None,
                        "tags": tags or {}
                    }
                }
            }
            
            self.client.secrets.kv.v2.create_or_update_secret(
                path=f"{credential_type.value}/{credential_id}",
                secret=vault_data["data"],
                mount_point=self.mount_point
            )
            
            logger.info(f"Stored credential {credential_id} in Vault")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to store credential in Vault: {e}")
            raise
    
    async def retrieve_credential(self, credential_id: str, credential_type: CredentialType) -> Optional[SecureCredential]:
        """Retrieve credential from Vault"""
        try:
            path = f"{credential_type.value}/{credential_id}"
            
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )
            
            if not response or "data" not in response:
                return None
            
            data = response["data"]["data"]
            metadata_dict = data.get("metadata", {})
            
            # Reconstruct metadata
            metadata = CredentialMetadata(
                credential_id=credential_id,
                credential_type=credential_type,
                created_at=datetime.fromisoformat(metadata_dict.get("created_at", datetime.now().isoformat())),
                expires_at=datetime.fromisoformat(metadata_dict["expires_at"]) if metadata_dict.get("expires_at") else None,
                last_accessed=datetime.now(),
                access_count=metadata_dict.get("access_count", 0) + 1,
                source="vault",
                tags=metadata_dict.get("tags", {})
            )
            
            # Update access tracking
            await self._update_access_tracking(credential_id, credential_type, metadata)
            
            return SecureCredential(
                credential_id=credential_id,
                value=data["value"],
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential from Vault: {e}")
            return None
    
    async def _update_access_tracking(
        self,
        credential_id: str,
        credential_type: CredentialType,
        metadata: CredentialMetadata
    ):
        """Update access tracking in Vault"""
        try:
            # Update metadata with access info
            path = f"{credential_type.value}/{credential_id}"
            
            current = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )
            
            if current and "data" in current:
                data = current["data"]["data"]
                data["metadata"]["last_accessed"] = metadata.last_accessed.isoformat()
                data["metadata"]["access_count"] = metadata.access_count
                
                self.client.secrets.kv.v2.create_or_update_secret(
                    path=path,
                    secret=data,
                    mount_point=self.mount_point
                )
                
        except Exception as e:
            logger.debug(f"Failed to update access tracking: {e}")  # Non-critical


class LocalEncryptedCredentialManager:
    """
    Local encrypted credential storage for environments without Vault
    """
    
    def __init__(self, encryption_key: Optional[str] = None, storage_path: str = "/var/lib/athintel/credentials"):
        self.storage_path = storage_path
        self.credentials: Dict[str, SecureCredential] = {}
        
        # Initialize encryption
        if encryption_key:
            self.fernet = Fernet(encryption_key.encode())
        else:
            # Generate encryption key from system entropy
            password = os.getenv("CREDENTIAL_MASTER_KEY", secrets.token_urlsafe(32)).encode()
            salt = os.getenv("CREDENTIAL_SALT", "athintel_salt_2024").encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self.fernet = Fernet(key)
        
        # Ensure storage directory exists
        os.makedirs(storage_path, mode=0o700, exist_ok=True)
        
        # Load existing credentials
        asyncio.create_task(self._load_credentials())
        
        logger.info(f"Initialized local encrypted credential storage at {storage_path}")
    
    async def store_credential(
        self,
        credential_id: str,
        credential_type: CredentialType,
        value: str,
        expires_at: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> CredentialMetadata:
        """Store encrypted credential locally"""
        try:
            metadata = CredentialMetadata(
                credential_id=credential_id,
                credential_type=credential_type,
                created_at=datetime.now(),
                expires_at=expires_at,
                source="encrypted_file",
                tags=tags or {}
            )
            
            credential = SecureCredential(
                credential_id=credential_id,
                value=value,
                metadata=metadata
            )
            
            # Store in memory
            self.credentials[f"{credential_type.value}:{credential_id}"] = credential
            
            # Persist to disk
            await self._save_credential_to_disk(credential)
            
            logger.info(f"Stored encrypted credential {credential_id} locally")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to store credential locally: {e}")
            raise
    
    async def retrieve_credential(self, credential_id: str, credential_type: CredentialType) -> Optional[SecureCredential]:
        """Retrieve encrypted credential from local storage"""
        try:
            key = f"{credential_type.value}:{credential_id}"
            credential = self.credentials.get(key)
            
            if not credential:
                # Try loading from disk
                credential = await self._load_credential_from_disk(credential_id, credential_type)
            
            if credential:
                # Check if expired
                if credential.metadata.expires_at and datetime.now() > credential.metadata.expires_at:
                    logger.warning(f"Credential {credential_id} has expired")
                    return None
                
                # Update access tracking
                credential.metadata.last_accessed = datetime.now()
                credential.metadata.access_count += 1
                
                return credential
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential locally: {e}")
            return None
    
    async def _save_credential_to_disk(self, credential: SecureCredential):
        """Save encrypted credential to disk"""
        try:
            file_path = os.path.join(
                self.storage_path,
                f"{credential.metadata.credential_type.value}_{credential.credential_id}.enc"
            )
            
            # Prepare data for encryption
            data = {
                "credential_id": credential.credential_id,
                "value": credential.value,
                "metadata": {
                    "credential_type": credential.metadata.credential_type.value,
                    "created_at": credential.metadata.created_at.isoformat(),
                    "expires_at": credential.metadata.expires_at.isoformat() if credential.metadata.expires_at else None,
                    "tags": credential.metadata.tags
                }
            }
            
            # Encrypt and save
            encrypted_data = self.fernet.encrypt(json.dumps(data).encode())
            
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Set secure file permissions
            os.chmod(file_path, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save credential to disk: {e}")
    
    async def _load_credential_from_disk(self, credential_id: str, credential_type: CredentialType) -> Optional[SecureCredential]:
        """Load encrypted credential from disk"""
        try:
            file_path = os.path.join(
                self.storage_path,
                f"{credential_type.value}_{credential_id}.enc"
            )
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt data
            decrypted_data = self.fernet.decrypt(encrypted_data)
            data = json.loads(decrypted_data.decode())
            
            # Reconstruct credential
            metadata_dict = data["metadata"]
            metadata = CredentialMetadata(
                credential_id=credential_id,
                credential_type=credential_type,
                created_at=datetime.fromisoformat(metadata_dict["created_at"]),
                expires_at=datetime.fromisoformat(metadata_dict["expires_at"]) if metadata_dict.get("expires_at") else None,
                source="encrypted_file",
                tags=metadata_dict.get("tags", {})
            )
            
            credential = SecureCredential(
                credential_id=credential_id,
                value=data["value"],
                metadata=metadata
            )
            
            # Cache in memory
            self.credentials[f"{credential_type.value}:{credential_id}"] = credential
            
            return credential
            
        except Exception as e:
            logger.error(f"Failed to load credential from disk: {e}")
            return None
    
    async def _load_credentials(self):
        """Load all credentials from disk on startup"""
        try:
            if not os.path.exists(self.storage_path):
                return
            
            for filename in os.listdir(self.storage_path):
                if filename.endswith('.enc'):
                    # Parse filename to extract type and ID
                    parts = filename[:-4].split('_', 1)  # Remove .enc and split
                    if len(parts) == 2:
                        credential_type_str, credential_id = parts
                        try:
                            credential_type = CredentialType(credential_type_str)
                            await self._load_credential_from_disk(credential_id, credential_type)
                        except ValueError:
                            logger.warning(f"Unknown credential type in file: {filename}")
        except Exception as e:
            logger.error(f"Failed to load credentials from disk: {e}")


class SecureCredentialManager:
    """
    Main credential manager with automatic fallback between Vault and local storage
    """
    
    def __init__(self):
        self.vault_manager: Optional[VaultCredentialManager] = None
        self.local_manager: Optional[LocalEncryptedCredentialManager] = None
        
        # Initialize based on configuration
        self._initialize_managers()
        
        # Credential cache for performance
        self._cache: Dict[str, SecureCredential] = {}
        self._cache_ttl = 300  # 5 minutes
        self._cache_timestamps: Dict[str, datetime] = {}
        
        logger.info("Secure credential manager initialized")
    
    def _initialize_managers(self):
        """Initialize credential managers based on available configuration"""
        # Try to initialize Vault manager first
        vault_url = os.getenv("VAULT_URL")
        vault_token = os.getenv("VAULT_TOKEN")
        
        if vault_url and vault_token and VAULT_AVAILABLE:
            try:
                self.vault_manager = VaultCredentialManager(vault_url, vault_token)
                logger.info("Using HashiCorp Vault for credential management")
            except Exception as e:
                logger.warning(f"Failed to initialize Vault manager: {e}")
        
        # Always initialize local manager as fallback
        try:
            self.local_manager = LocalEncryptedCredentialManager()
            logger.info("Local encrypted credential manager initialized as fallback")
        except Exception as e:
            logger.error(f"Failed to initialize local credential manager: {e}")
            raise
    
    async def store_credential(
        self,
        credential_id: str,
        credential_type: CredentialType,
        value: str,
        expires_at: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> CredentialMetadata:
        """Store credential using primary manager with fallback"""
        
        # Validate credential strength
        self._validate_credential_strength(credential_type, value)
        
        # Try Vault first, then local
        managers = [self.vault_manager, self.local_manager]
        
        for manager in managers:
            if manager:
                try:
                    metadata = await manager.store_credential(
                        credential_id, credential_type, value, expires_at, tags
                    )
                    
                    # Clear cache for this credential
                    cache_key = f"{credential_type.value}:{credential_id}"
                    if cache_key in self._cache:
                        del self._cache[cache_key]
                        del self._cache_timestamps[cache_key]
                    
                    # Audit log
                    logger.info(f"Credential stored: {credential_id} (type: {credential_type.value}, source: {metadata.source})")
                    
                    return metadata
                    
                except Exception as e:
                    logger.warning(f"Failed to store credential with {type(manager).__name__}: {e}")
        
        raise RuntimeError("Failed to store credential with any available manager")
    
    async def retrieve_credential(self, credential_id: str, credential_type: CredentialType) -> Optional[SecureCredential]:
        """Retrieve credential with caching and fallback"""
        cache_key = f"{credential_type.value}:{credential_id}"
        
        # Check cache first
        if cache_key in self._cache:
            cache_time = self._cache_timestamps.get(cache_key, datetime.min)
            if datetime.now() - cache_time < timedelta(seconds=self._cache_ttl):
                credential = self._cache[cache_key]
                credential.metadata.access_count += 1
                return credential
        
        # Try managers in order
        managers = [self.vault_manager, self.local_manager]
        
        for manager in managers:
            if manager:
                try:
                    credential = await manager.retrieve_credential(credential_id, credential_type)
                    if credential:
                        # Cache the credential
                        self._cache[cache_key] = credential
                        self._cache_timestamps[cache_key] = datetime.now()
                        
                        # Audit log (with masked value)
                        logger.info(f"Credential retrieved: {credential_id} (source: {credential.metadata.source}, value: {credential.masked_value})")
                        
                        return credential
                        
                except Exception as e:
                    logger.warning(f"Failed to retrieve credential with {type(manager).__name__}: {e}")
        
        logger.warning(f"Credential not found: {credential_id} (type: {credential_type.value})")
        return None
    
    def _validate_credential_strength(self, credential_type: CredentialType, value: str):
        """Validate credential meets security requirements"""
        if credential_type == CredentialType.DATABASE_PASSWORD:
            if len(value) < 12:
                raise ValueError("Database password must be at least 12 characters")
            if not any(c.isupper() for c in value):
                raise ValueError("Database password must contain uppercase letters")
            if not any(c.islower() for c in value):
                raise ValueError("Database password must contain lowercase letters")
            if not any(c.isdigit() for c in value):
                raise ValueError("Database password must contain numbers")
        
        elif credential_type == CredentialType.API_KEY:
            if len(value) < 32:
                raise ValueError("API key must be at least 32 characters")
        
        elif credential_type == CredentialType.JWT_SECRET:
            if len(value) < 64:
                raise ValueError("JWT secret must be at least 64 characters")
    
    async def rotate_credential(
        self,
        credential_id: str,
        credential_type: CredentialType,
        new_value: str
    ) -> CredentialMetadata:
        """Rotate credential with automatic backup"""
        try:
            # Get existing credential for backup
            existing = await self.retrieve_credential(credential_id, credential_type)
            
            if existing:
                # Store backup with timestamp
                backup_id = f"{credential_id}_backup_{int(datetime.now().timestamp())}"
                await self.store_credential(
                    backup_id,
                    credential_type,
                    existing.value,
                    expires_at=datetime.now() + timedelta(days=30),  # 30-day backup retention
                    tags={"backup_for": credential_id, "backup_date": datetime.now().isoformat()}
                )
            
            # Store new credential
            metadata = await self.store_credential(credential_id, credential_type, new_value)
            
            logger.info(f"Credential rotated: {credential_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to rotate credential {credential_id}: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get credential manager statistics"""
        return {
            "vault_available": self.vault_manager is not None,
            "local_manager_available": self.local_manager is not None,
            "cached_credentials": len(self._cache),
            "cache_ttl_seconds": self._cache_ttl,
            "managers_initialized": sum([
                1 for manager in [self.vault_manager, self.local_manager] 
                if manager is not None
            ])
        }


# Global credential manager instance
_credential_manager = None


def get_credential_manager() -> SecureCredentialManager:
    """Get or create global credential manager"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = SecureCredentialManager()
    return _credential_manager


# Convenience functions
async def store_database_password(db_name: str, password: str) -> CredentialMetadata:
    """Store database password securely"""
    manager = get_credential_manager()
    return await manager.store_credential(
        credential_id=f"db_{db_name}",
        credential_type=CredentialType.DATABASE_PASSWORD,
        value=password,
        tags={"database": db_name, "type": "postgresql"}
    )


async def get_database_password(db_name: str) -> Optional[str]:
    """Retrieve database password securely"""
    manager = get_credential_manager()
    credential = await manager.retrieve_credential(
        credential_id=f"db_{db_name}",
        credential_type=CredentialType.DATABASE_PASSWORD
    )
    return credential.value if credential else None


async def store_api_key(service_name: str, api_key: str) -> CredentialMetadata:
    """Store API key securely"""
    manager = get_credential_manager()
    return await manager.store_credential(
        credential_id=f"api_{service_name}",
        credential_type=CredentialType.API_KEY,
        value=api_key,
        tags={"service": service_name, "type": "external_api"}
    )


async def get_api_key(service_name: str) -> Optional[str]:
    """Retrieve API key securely"""
    manager = get_credential_manager()
    credential = await manager.retrieve_credential(
        credential_id=f"api_{service_name}",
        credential_type=CredentialType.API_KEY
    )
    return credential.value if credential else None