"""Tests for Security Module."""

from datetime import datetime, timedelta

from src.common.security import (
    CredentialManager,
    EncryptionManager,
    RateLimiter,
    SecurityLevel,
    SessionManager,
    generate_api_key,
    hash_password,
    validate_api_key,
    verify_password,
)


class TestEncryption:
    """Test encryption functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.encryption_manager = EncryptionManager("test_password_123")

    def test_encrypt_decrypt_string(self):
        """Test string encryption and decryption."""
        original = "sensitive_api_key_12345"

        encrypted = self.encryption_manager.encrypt(original)
        assert encrypted != original

        decrypted = self.encryption_manager.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_decrypt_dict(self):
        """Test dictionary encryption and decryption."""
        original = {
            "api_key": "secret_key",
            "password": "secret_password",
            "user_id": 12345
        }

        encrypted = self.encryption_manager.encrypt_dict(original)
        assert isinstance(encrypted, str)

        decrypted = self.encryption_manager.decrypt_dict(encrypted)
        assert decrypted == original
        assert decrypted["api_key"] == "secret_key"

    def test_encryption_without_key(self):
        """Test encryption without master key."""
        manager = EncryptionManager()  # No master password

        original = "test_data"
        result = manager.encrypt(original)

        # Without key, should return original
        assert result == original


class TestCredentialManager:
    """Test credential management."""

    def setup_method(self):
        """Setup test fixtures."""
        self.cred_manager = CredentialManager()

    def test_store_retrieve_credential(self):
        """Test storing and retrieving credentials."""
        key = "test_api_key"
        value = "super_secret_key_123"

        # Store credential
        success = self.cred_manager.store_credential(key, value)
        assert success is True

        # Retrieve credential
        retrieved = self.cred_manager.retrieve_credential(key)
        assert retrieved == value

        # Clean up
        self.cred_manager.delete_credential(key)

    def test_delete_credential(self):
        """Test credential deletion."""
        key = "temp_key"
        value = "temp_value"

        # Store and then delete
        self.cred_manager.store_credential(key, value)
        success = self.cred_manager.delete_credential(key)
        assert success is True

        # Should not be retrievable
        retrieved = self.cred_manager.retrieve_credential(key)
        assert retrieved is None


class TestSessionManager:
    """Test session management."""

    def setup_method(self):
        """Setup test fixtures."""
        self.session_manager = SessionManager()

    def test_create_session(self):
        """Test session creation."""
        user_id = "test_user_123"
        session_id = self.session_manager.create_session(user_id, "127.0.0.1")

        assert session_id is not None
        assert len(session_id) > 20

    def test_validate_session(self):
        """Test session validation."""
        user_id = "test_user"
        session_id = self.session_manager.create_session(user_id)

        # Valid session
        context = self.session_manager.validate_session(session_id)
        assert context is not None
        assert context.user_id == user_id
        assert context.security_level == SecurityLevel.MEDIUM

    def test_invalid_session(self):
        """Test invalid session validation."""
        context = self.session_manager.validate_session("invalid_session_id")
        assert context is None

    def test_session_timeout(self):
        """Test session timeout."""
        user_id = "timeout_user"
        session_id = self.session_manager.create_session(user_id)

        # Manually set old timestamp
        context = self.session_manager.sessions[session_id]
        context.timestamp = datetime.utcnow() - timedelta(hours=10)

        # Should be invalid due to timeout
        validated = self.session_manager.validate_session(session_id)
        assert validated is None

    def test_terminate_session(self):
        """Test session termination."""
        user_id = "term_user"
        session_id = self.session_manager.create_session(user_id)

        # Terminate session
        self.session_manager.terminate_session(session_id)

        # Should be invalid
        context = self.session_manager.validate_session(session_id)
        assert context is None


class TestRateLimiter:
    """Test rate limiting."""

    def setup_method(self):
        """Setup test fixtures."""
        self.rate_limiter = RateLimiter()

    def test_rate_limit_within_bounds(self):
        """Test rate limiting within allowed bounds."""
        self.rate_limiter.set_limit("api", max_requests=5, time_window=60)

        identifier = "user_123"

        # First 5 requests should succeed
        for i in range(5):
            allowed = self.rate_limiter.check_limit("api", identifier)
            assert allowed is True

    def test_rate_limit_exceeded(self):
        """Test rate limiting when exceeded."""
        self.rate_limiter.set_limit("trading", max_requests=2, time_window=60)

        identifier = "user_456"

        # First 2 should succeed
        assert self.rate_limiter.check_limit("trading", identifier) is True
        assert self.rate_limiter.check_limit("trading", identifier) is True

        # Third should fail
        assert self.rate_limiter.check_limit("trading", identifier) is False

    def test_rate_limit_different_users(self):
        """Test rate limiting for different users."""
        self.rate_limiter.set_limit("test", max_requests=1, time_window=60)

        # User 1
        assert self.rate_limiter.check_limit("test", "user1") is True
        assert self.rate_limiter.check_limit("test", "user1") is False

        # User 2 should still be allowed
        assert self.rate_limiter.check_limit("test", "user2") is True


class TestPasswordUtils:
    """Test password utilities."""

    def test_hash_and_verify_password(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"

        hash_str, salt = hash_password(password)

        # Hash should be different from password
        assert hash_str != password

        # Verification should succeed
        assert verify_password(password, hash_str, salt) is True

        # Wrong password should fail
        assert verify_password("WrongPassword", hash_str, salt) is False

    def test_different_salts_produce_different_hashes(self):
        """Test that different salts produce different hashes."""
        password = "TestPassword"

        hash1, salt1 = hash_password(password)
        hash2, salt2 = hash_password(password)

        # Different salts
        assert salt1 != salt2

        # Different hashes
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1, salt1) is True
        assert verify_password(password, hash2, salt2) is True


class TestAPIKey:
    """Test API key utilities."""

    def test_generate_api_key(self):
        """Test API key generation."""
        key1 = generate_api_key()
        key2 = generate_api_key()

        # Should be unique
        assert key1 != key2

        # Should be proper length
        assert len(key1) >= 32
        assert len(key2) >= 32

    def test_validate_api_key(self):
        """Test API key validation."""
        # Valid key
        valid_key = generate_api_key()
        assert validate_api_key(valid_key) is True

        # Invalid keys
        assert validate_api_key("too_short") is False
        assert validate_api_key("") is False
        assert validate_api_key("invalid@#$%^&*()") is False