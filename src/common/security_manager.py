"""Security Managers for OrderPilot-AI.

Provides encryption, credential storage, and session management.
"""

import json
import logging
import os
import secrets
import sys
from base64 import b64decode, b64encode
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Windows credential manager for secure storage
if sys.platform == "win32":
    try:
        import keyring
        from keyring.backends.Windows import WinVaultKeyring
        KEYRING_AVAILABLE = True
    except ImportError:
        KEYRING_AVAILABLE = False
else:
    KEYRING_AVAILABLE = False

from .security_config import SecurityContext, SecurityLevel

logger = logging.getLogger(__name__)


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""

    def __init__(self, master_password: str | None = None):
        """Initialize encryption manager.

        Args:
            master_password: Master password for key derivation
        """
        self.master_password = master_password or os.environ.get('ORDERPILOT_MASTER_KEY', '')
        self._cipher_suite: Fernet | None = None
        self._key: bytes | None = None

        if self.master_password:
            self._initialize_encryption()

    def _initialize_encryption(self):
        """Initialize encryption with master password."""
        # Derive key from master password
        salt = b'orderpilot-ai-salt-2024'  # In production, use random salt stored securely
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = b64encode(kdf.derive(self.master_password.encode()))
        self._key = key
        self._cipher_suite = Fernet(key)

        logger.info("Encryption initialized")

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data.

        Args:
            data: Data to encrypt

        Returns:
            Encrypted data as base64 string
        """
        if not self._cipher_suite:
            logger.warning("Encryption not initialized, returning plain text")
            return data

        try:
            encrypted = self._cipher_suite.encrypt(data.encode())
            return b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data.

        Args:
            encrypted_data: Encrypted data as base64 string

        Returns:
            Decrypted data
        """
        if not self._cipher_suite:
            logger.warning("Encryption not initialized, returning as-is")
            return encrypted_data

        try:
            encrypted = b64decode(encrypted_data.encode())
            decrypted = self._cipher_suite.decrypt(encrypted)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_dict(self, data: dict[str, Any]) -> str:
        """Encrypt dictionary data.

        Args:
            data: Dictionary to encrypt

        Returns:
            Encrypted JSON string
        """
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: str) -> dict[str, Any]:
        """Decrypt dictionary data.

        Args:
            encrypted_data: Encrypted JSON string

        Returns:
            Decrypted dictionary
        """
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)

    def rotate_key(self, new_password: str) -> bool:
        """Rotate encryption key.

        Args:
            new_password: New master password

        Returns:
            True if successful
        """
        try:
            old_cipher = self._cipher_suite

            # Create new encryption with new password
            self.master_password = new_password
            self._initialize_encryption()

            # Re-encrypt existing data would happen here
            # This is simplified - in production, would re-encrypt all stored data

            logger.info("Encryption key rotated successfully")
            return True

        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            # Restore old encryption
            self._cipher_suite = old_cipher
            return False


class CredentialManager:
    """Manages secure storage of credentials."""

    def __init__(self, encryption_manager: EncryptionManager | None = None):
        """Initialize credential manager.

        Args:
            encryption_manager: Encryption manager for local storage
        """
        self.encryption_manager = encryption_manager or EncryptionManager()
        self.service_name = "OrderPilot-AI"

        # Use Windows Credential Manager if available
        if KEYRING_AVAILABLE:
            try:
                self.keyring = WinVaultKeyring()
                logger.info("Using Windows Credential Manager")
            except Exception:
                self.keyring = None
                logger.warning("Windows Credential Manager unavailable")
        else:
            self.keyring = None

    def store_credential(self, key: str, value: str, encrypt: bool = True) -> bool:
        """Store credential securely.

        Args:
            key: Credential key
            value: Credential value
            encrypt: Whether to encrypt before storing

        Returns:
            True if successful
        """
        try:
            # Encrypt if requested
            if encrypt:
                value = self.encryption_manager.encrypt(value)

            # Try Windows Credential Manager first
            if self.keyring:
                keyring.set_password(self.service_name, key, value)
                logger.debug(f"Stored credential {key} in Windows Credential Manager")
                return True

            # Fallback to encrypted file storage
            cred_file = self._get_credential_file()
            creds = self._load_credentials_file()
            creds[key] = value
            self._save_credentials_file(creds)

            logger.debug(f"Stored credential {key} in encrypted file")
            return True

        except Exception as e:
            logger.error(f"Failed to store credential: {e}")
            return False

    def retrieve_credential(self, key: str, decrypt: bool = True) -> str | None:
        """Retrieve credential.

        Args:
            key: Credential key
            decrypt: Whether to decrypt after retrieving

        Returns:
            Credential value or None
        """
        try:
            value = None

            # Try Windows Credential Manager first
            if self.keyring:
                value = keyring.get_password(self.service_name, key)

            # Fallback to file storage
            if not value:
                creds = self._load_credentials_file()
                value = creds.get(key)

            if value and decrypt:
                value = self.encryption_manager.decrypt(value)

            return value

        except Exception as e:
            logger.error(f"Failed to retrieve credential: {e}")
            return None

    def delete_credential(self, key: str) -> bool:
        """Delete credential.

        Args:
            key: Credential key

        Returns:
            True if successful
        """
        try:
            # Try Windows Credential Manager
            if self.keyring:
                try:
                    keyring.delete_password(self.service_name, key)
                except Exception:
                    pass

            # Also remove from file storage
            creds = self._load_credentials_file()
            if key in creds:
                del creds[key]
                self._save_credentials_file(creds)

            logger.debug(f"Deleted credential {key}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete credential: {e}")
            return False

    def _get_credential_file(self) -> str:
        """Get path to credential file.

        Returns:
            Path to credential file
        """
        app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
        cred_dir = os.path.join(app_data, 'OrderPilot-AI')
        os.makedirs(cred_dir, exist_ok=True)
        return os.path.join(cred_dir, 'credentials.enc')

    def _load_credentials_file(self) -> dict[str, str]:
        """Load credentials from file.

        Returns:
            Credentials dictionary
        """
        cred_file = self._get_credential_file()

        if not os.path.exists(cred_file):
            return {}

        try:
            with open(cred_file) as f:
                encrypted = f.read()
                return self.encryption_manager.decrypt_dict(encrypted)
        except Exception:
            return {}

    def _save_credentials_file(self, creds: dict[str, str]):
        """Save credentials to file.

        Args:
            creds: Credentials dictionary
        """
        cred_file = self._get_credential_file()

        try:
            encrypted = self.encryption_manager.encrypt_dict(creds)
            with open(cred_file, 'w') as f:
                f.write(encrypted)
        except Exception as e:
            logger.error(f"Failed to save credentials file: {e}")


class SessionManager:
    """Manages user sessions."""

    def __init__(self):
        """Initialize session manager."""
        self.sessions: dict[str, SecurityContext] = {}
        self.session_timeout = timedelta(hours=8)

    def create_session(self, user_id: str, ip_address: str | None = None) -> str:
        """Create new session.

        Args:
            user_id: User identifier
            ip_address: Client IP address

        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)

        context = SecurityContext(
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            security_level=SecurityLevel.MEDIUM
        )

        self.sessions[session_id] = context

        logger.info(f"Session created for user {user_id}")
        return session_id

    def validate_session(self, session_id: str) -> SecurityContext | None:
        """Validate session.

        Args:
            session_id: Session ID

        Returns:
            Security context if valid
        """
        context = self.sessions.get(session_id)

        if not context:
            return None

        # Check timeout
        if datetime.utcnow() - context.timestamp > self.session_timeout:
            self.terminate_session(session_id)
            return None

        # Update timestamp
        context.timestamp = datetime.utcnow()
        return context

    def terminate_session(self, session_id: str):
        """Terminate session.

        Args:
            session_id: Session ID
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session {session_id} terminated")


# Authentication decorator

def require_auth(security_level: SecurityLevel = SecurityLevel.MEDIUM):
    """Decorator requiring authentication.

    Args:
        security_level: Required security level
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get context from kwargs or thread-local
            context = kwargs.get('security_context')

            if not context:
                raise PermissionError("Authentication required")

            if context.security_level.value < security_level.value:
                raise PermissionError(f"Insufficient security level: {security_level.value} required")

            return func(*args, **kwargs)

        return wrapper
    return decorator


# Initialize global security components
encryption_manager = EncryptionManager()
credential_manager = CredentialManager(encryption_manager)
session_manager = SessionManager()
