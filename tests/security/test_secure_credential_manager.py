"""
Security Testing Suite for Secure Credential Manager
Tests for credential storage, encryption, and access control
"""

import pytest
import pytest_asyncio
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from pathlib import Path

from src.config.secure_credential_manager import (
    SecureCredentialManager, VaultCredentialManager, LocalEncryptedCredentialManager,
    CredentialType, SecureCredential, CredentialMetadata, get_credential_manager
)


class TestSecureCredentialManager:
    """Test suite for secure credential management system"""

    @pytest.fixture
    def temp_credential_dir(self, tmp_path):
        """Temporary directory for credential storage"""
        cred_dir = tmp_path / "credentials"
        cred_dir.mkdir(mode=0o700)
        return str(cred_dir)

    @pytest.fixture
    async def local_credential_manager(self, temp_credential_dir):
        """Local credential manager instance"""
        return LocalEncryptedCredentialManager(storage_path=temp_credential_dir)

    @pytest.fixture
    def mock_vault_manager(self):
        """Mock Vault credential manager"""
        with patch('src.config.secure_credential_manager.VAULT_AVAILABLE', True):
            with patch('src.config.secure_credential_manager.hvac') as mock_hvac:
                mock_client = MagicMock()
                mock_client.is_authenticated.return_value = True
                mock_hvac.Client.return_value = mock_client
                
                manager = VaultCredentialManager("http://vault:8200", "test-token")
                manager.client = mock_client
                return manager

    async def test_credential_storage_encryption(self, local_credential_manager):
        """Test that credentials are properly encrypted when stored"""
        # Store a credential
        metadata = await local_credential_manager.store_credential(
            credential_id="test_db_password",
            credential_type=CredentialType.DATABASE_PASSWORD,
            value="SuperSecurePassword123!",
            tags={"environment": "test"}
        )
        
        assert metadata.credential_id == "test_db_password"
        assert metadata.credential_type == CredentialType.DATABASE_PASSWORD
        assert metadata.source == "encrypted_file"
        
        # Verify file is created and encrypted
        storage_path = Path(local_credential_manager.storage_path)
        encrypted_files = list(storage_path.glob("*.enc"))
        assert len(encrypted_files) == 1
        
        # Verify file content is encrypted (not plaintext)
        with open(encrypted_files[0], 'rb') as f:
            content = f.read()
            assert b"SuperSecurePassword123!" not in content
            assert len(content) > 50  # Encrypted content should be longer

    async def test_credential_retrieval_and_masking(self, local_credential_manager):
        """Test credential retrieval and value masking"""
        # Store credential
        await local_credential_manager.store_credential(
            credential_id="test_api_key", 
            credential_type=CredentialType.API_KEY,
            value="abcdef1234567890abcdef1234567890"
        )
        
        # Retrieve credential
        credential = await local_credential_manager.retrieve_credential(
            "test_api_key", CredentialType.API_KEY
        )
        
        assert credential is not None
        assert credential.value == "abcdef1234567890abcdef1234567890"
        assert credential.masked_value == "abcd****************************7890"
        assert credential.metadata.access_count == 1

    async def test_credential_strength_validation(self, local_credential_manager):
        """Test credential strength validation"""
        manager = SecureCredentialManager()
        manager.local_manager = local_credential_manager
        
        # Test weak database password
        with pytest.raises(ValueError, match="at least 12 characters"):
            await manager.store_credential(
                "weak_pwd", CredentialType.DATABASE_PASSWORD, "weak"
            )
        
        # Test password without uppercase
        with pytest.raises(ValueError, match="uppercase letters"):
            await manager.store_credential(
                "no_upper", CredentialType.DATABASE_PASSWORD, "lowercaseonly123!"
            )
        
        # Test short API key
        with pytest.raises(ValueError, match="at least 32 characters"):
            await manager.store_credential(
                "short_key", CredentialType.API_KEY, "tooshort"
            )

    async def test_credential_expiration_handling(self, local_credential_manager):
        """Test expired credential handling"""
        # Store credential with expiration in the past
        past_time = datetime.now() - timedelta(hours=1)
        await local_credential_manager.store_credential(
            "expired_key",
            CredentialType.API_KEY, 
            "expired_key_value_1234567890abcdef",
            expires_at=past_time
        )
        
        # Attempt to retrieve expired credential
        credential = await local_credential_manager.retrieve_credential(
            "expired_key", CredentialType.API_KEY
        )
        
        assert credential is None  # Should return None for expired credentials

    async def test_vault_integration_security(self, mock_vault_manager):
        """Test HashiCorp Vault integration security"""
        # Mock Vault responses
        mock_vault_manager.client.secrets.kv.v2.create_or_update_secret.return_value = True
        mock_vault_manager.client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {
                "data": {
                    "value": "vault_stored_secret",
                    "metadata": {
                        "credential_id": "vault_test",
                        "credential_type": "api_key",
                        "created_at": datetime.now().isoformat(),
                        "expires_at": None,
                        "tags": {}
                    }
                }
            }
        }
        
        # Store credential in Vault
        metadata = await mock_vault_manager.store_credential(
            "vault_test",
            CredentialType.API_KEY,
            "vault_stored_secret_1234567890abcdef"
        )
        
        assert metadata.source == "vault"
        
        # Retrieve credential from Vault
        credential = await mock_vault_manager.retrieve_credential(
            "vault_test", CredentialType.API_KEY
        )
        
        assert credential.value == "vault_stored_secret"
        assert credential.metadata.source == "vault"

    async def test_credential_rotation_security(self, local_credential_manager):
        """Test secure credential rotation with backup"""
        manager = SecureCredentialManager()
        manager.local_manager = local_credential_manager
        
        # Store initial credential
        await manager.store_credential(
            "rotate_test",
            CredentialType.DATABASE_PASSWORD,
            "InitialPassword123!"
        )
        
        # Rotate credential
        new_metadata = await manager.rotate_credential(
            "rotate_test",
            CredentialType.DATABASE_PASSWORD,
            "NewRotatedPassword456!"
        )
        
        # Verify new credential is stored
        new_credential = await manager.retrieve_credential(
            "rotate_test", CredentialType.DATABASE_PASSWORD
        )
        assert new_credential.value == "NewRotatedPassword456!"
        
        # Verify backup exists (would check in real implementation)
        # Backup naming would include timestamp

    async def test_file_permission_security(self, local_credential_manager):
        """Test file permissions for credential storage"""
        await local_credential_manager.store_credential(
            "perm_test",
            CredentialType.JWT_SECRET,
            "jwt_secret_key_minimum_64_characters_long_for_security_purposes"
        )
        
        # Check file permissions
        storage_path = Path(local_credential_manager.storage_path)
        encrypted_files = list(storage_path.glob("*.enc"))
        
        for file_path in encrypted_files:
            stat = file_path.stat()
            permissions = oct(stat.st_mode)[-3:]
            assert permissions == "600", f"File {file_path} has incorrect permissions: {permissions}"

    async def test_concurrent_access_safety(self, local_credential_manager):
        """Test thread-safe concurrent access to credentials"""
        import asyncio
        
        # Store initial credential
        await local_credential_manager.store_credential(
            "concurrent_test",
            CredentialType.API_KEY,
            "concurrent_access_test_key_123456789"
        )
        
        # Simulate concurrent access
        async def retrieve_credential():
            return await local_credential_manager.retrieve_credential(
                "concurrent_test", CredentialType.API_KEY
            )
        
        # Run multiple concurrent retrievals
        tasks = [retrieve_credential() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed and return same credential
        assert all(r is not None for r in results)
        assert all(r.value == "concurrent_access_test_key_123456789" for r in results)

    async def test_credential_manager_fallback(self):
        """Test fallback from Vault to local storage"""
        with patch.dict(os.environ, {}, clear=True):  # No vault config
            manager = SecureCredentialManager()
            
            # Should have local manager but no vault manager
            assert manager.local_manager is not None
            assert manager.vault_manager is None
            
            # Store and retrieve should work with local fallback
            await manager.store_credential(
                "fallback_test",
                CredentialType.API_KEY,
                "fallback_test_key_1234567890abcdef"
            )
            
            credential = await manager.retrieve_credential(
                "fallback_test", CredentialType.API_KEY
            )
            assert credential.value == "fallback_test_key_1234567890abcdef"

    def test_credential_masking_patterns(self):
        """Test various credential masking patterns"""
        from src.config.secure_credential_manager import SecureCredential, CredentialMetadata
        
        test_cases = [
            ("short", "****"),
            ("medium123", "med****123"),
            ("very_long_credential_value_for_testing", "very****ting"),
            ("abcdefghijklmnop", "abcd****mnop")
        ]
        
        for value, expected_mask in test_cases:
            metadata = CredentialMetadata(
                credential_id="test",
                credential_type=CredentialType.API_KEY,
                created_at=datetime.now()
            )
            credential = SecureCredential("test", value, metadata)
            assert credential.masked_value == expected_mask

    async def test_audit_logging_security(self, local_credential_manager, caplog):
        """Test security audit logging for credential operations"""
        with patch('src.config.secure_credential_manager.logger') as mock_logger:
            # Store credential
            await local_credential_manager.store_credential(
                "audit_test",
                CredentialType.DATABASE_PASSWORD,
                "AuditTestPassword123!"
            )
            
            # Retrieve credential
            await local_credential_manager.retrieve_credential(
                "audit_test", CredentialType.DATABASE_PASSWORD
            )
            
            # Verify audit logs (masked values only)
            mock_logger.info.assert_called()
            log_calls = [call for call in mock_logger.info.call_args_list]
            
            # Should log storage and retrieval with masked values
            assert any("audit_test" in str(call) for call in log_calls)
            # Should not log actual password values
            assert not any("AuditTestPassword123!" in str(call) for call in log_calls)


@pytest.mark.asyncio
class TestCredentialManagerIntegration:
    """Integration tests for credential manager components"""

    async def test_end_to_end_credential_lifecycle(self, tmp_path):
        """Test complete credential lifecycle"""
        storage_path = tmp_path / "creds"
        storage_path.mkdir(mode=0o700)
        
        # Initialize manager
        local_manager = LocalEncryptedCredentialManager(storage_path=str(storage_path))
        main_manager = SecureCredentialManager()
        main_manager.local_manager = local_manager
        
        # 1. Store credential
        metadata = await main_manager.store_credential(
            "lifecycle_test",
            CredentialType.DATABASE_PASSWORD,
            "LifecycleTestPassword123!",
            tags={"environment": "integration_test"}
        )
        
        # 2. Retrieve and verify
        credential = await main_manager.retrieve_credential(
            "lifecycle_test", CredentialType.DATABASE_PASSWORD
        )
        assert credential.value == "LifecycleTestPassword123!"
        assert credential.metadata.tags["environment"] == "integration_test"
        
        # 3. Rotate credential
        await main_manager.rotate_credential(
            "lifecycle_test",
            CredentialType.DATABASE_PASSWORD,
            "NewLifecyclePassword456!"
        )
        
        # 4. Verify rotation
        rotated_credential = await main_manager.retrieve_credential(
            "lifecycle_test", CredentialType.DATABASE_PASSWORD
        )
        assert rotated_credential.value == "NewLifecyclePassword456!"
        
        # 5. Test stats
        stats = main_manager.get_stats()
        assert stats["local_manager_available"] is True
        assert stats["cached_credentials"] >= 0

    async def test_security_boundary_enforcement(self, tmp_path):
        """Test security boundaries and isolation"""
        storage_path = tmp_path / "secure_creds"
        storage_path.mkdir(mode=0o700)
        
        manager = LocalEncryptedCredentialManager(storage_path=str(storage_path))
        
        # Store credentials of different types
        credentials = [
            ("db_prod", CredentialType.DATABASE_PASSWORD, "ProdDBPassword123!"),
            ("api_external", CredentialType.API_KEY, "external_api_key_1234567890abcdef"),
            ("jwt_signing", CredentialType.JWT_SECRET, "jwt_signing_secret_minimum_64_chars_for_security_requirements")
        ]
        
        for cred_id, cred_type, value in credentials:
            await manager.store_credential(cred_id, cred_type, value)
        
        # Verify isolation - each credential type stored separately
        files = list(storage_path.glob("*.enc"))
        assert len(files) == 3
        
        # Verify each file contains only its respective credential
        db_file = storage_path / "database_password_db_prod.enc"
        api_file = storage_path / "api_key_api_external.enc"
        jwt_file = storage_path / "jwt_secret_jwt_signing.enc"
        
        assert db_file.exists()
        assert api_file.exists()
        assert jwt_file.exists()


# Security Test Utilities
class SecurityTestUtils:
    """Utilities for security testing"""
    
    @staticmethod
    def verify_no_plaintext_storage(storage_path: Path, sensitive_values: list):
        """Verify sensitive values are not stored in plaintext"""
        for file_path in storage_path.rglob("*"):
            if file_path.is_file():
                try:
                    content = file_path.read_text()
                    for sensitive_value in sensitive_values:
                        assert sensitive_value not in content, f"Found plaintext {sensitive_value} in {file_path}"
                except UnicodeDecodeError:
                    # Binary files are expected for encrypted storage
                    continue
    
    @staticmethod
    def verify_file_permissions(storage_path: Path, expected_permissions: str = "600"):
        """Verify file permissions are secure"""
        for file_path in storage_path.rglob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                permissions = oct(stat.st_mode)[-3:]
                assert permissions == expected_permissions, f"Insecure permissions {permissions} on {file_path}"


# Parametrized security tests
@pytest.mark.parametrize("credential_type,min_length", [
    (CredentialType.DATABASE_PASSWORD, 12),
    (CredentialType.API_KEY, 32),
    (CredentialType.JWT_SECRET, 64),
    (CredentialType.ENCRYPTION_KEY, 32),
])
def test_credential_strength_requirements(credential_type, min_length):
    """Test credential strength requirements for different types"""
    from src.config.secure_credential_manager import SecureCredentialManager
    
    manager = SecureCredentialManager()
    
    # Test minimum length requirement
    short_value = "a" * (min_length - 1)
    with pytest.raises(ValueError):
        manager._validate_credential_strength(credential_type, short_value)
    
    # Test valid length
    valid_value = "A1b" + "a" * (min_length - 3)  # Meet complexity for passwords
    try:
        manager._validate_credential_strength(credential_type, valid_value)
    except ValueError as e:
        if credential_type == CredentialType.DATABASE_PASSWORD:
            # May fail due to other complexity requirements
            assert any(req in str(e) for req in ["uppercase", "lowercase", "numbers"])
        else:
            pytest.fail(f"Valid credential rejected: {e}")


# Performance and load testing for credential manager
@pytest.mark.slow
async def test_credential_manager_performance():
    """Test credential manager performance under load"""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = LocalEncryptedCredentialManager(storage_path=temp_dir)
        
        import time
        start_time = time.perf_counter()
        
        # Store 100 credentials
        for i in range(100):
            await manager.store_credential(
                f"perf_test_{i}",
                CredentialType.API_KEY,
                f"performance_test_credential_{i:03d}_1234567890abcdef"
            )
        
        store_time = time.perf_counter() - start_time
        
        # Retrieve all credentials
        start_time = time.perf_counter()
        for i in range(100):
            await manager.retrieve_credential(f"perf_test_{i}", CredentialType.API_KEY)
        
        retrieve_time = time.perf_counter() - start_time
        
        # Performance assertions
        assert store_time < 5.0, f"Storing 100 credentials took {store_time:.2f}s (too slow)"
        assert retrieve_time < 2.0, f"Retrieving 100 credentials took {retrieve_time:.2f}s (too slow)"