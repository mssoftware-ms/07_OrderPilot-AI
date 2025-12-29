"""Core Security Module for OrderPilot-AI.

This module provides comprehensive security functionality including:
- Security configuration and types
- Password hashing and API key management
- Rate limiting and validation
- Core security utilities

Consolidated from security_config.py and security_validator.py
"""

import hashlib
import secrets
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional


class SecurityLevel(Enum):
    """Security levels for operations."""
    LOW = "low"  # Public operations
    MEDIUM = "medium"  # Authenticated operations
    HIGH = "high"  # Trading operations
    CRITICAL = "critical"  # Admin/financial operations


class SecurityAction(Enum):
    """Security-relevant actions."""
    LOGIN = "login"
    LOGOUT = "logout"
    API_KEY_ACCESS = "api_key_access"
    ORDER_PLACED = "order_placed"
    ORDER_CANCELLED = "order_cancelled"
    POSITION_CLOSED = "position_closed"
    SETTINGS_CHANGED = "settings_changed"
    STRATEGY_MODIFIED = "strategy_modified"
    DATA_EXPORT = "data_export"
    KILL_SWITCH_ACTIVATED = "kill_switch_activated"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    ENCRYPTION_KEY_ROTATED = "encryption_key_rotated"


@dataclass
class SecurityContext:
    """Security context for operations."""
    user_id: str
    session_id: str
    ip_address: str | None = None
    timestamp: datetime = None
    security_level: SecurityLevel = SecurityLevel.LOW
    permissions: List[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.permissions is None:
            self.permissions = []


class RateLimiter:
    """Rate limiting implementation with sliding window."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed.

        Args:
            key: Unique identifier for rate limiting

        Returns:
            True if request is allowed
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        request_times = self.requests[key]
        while request_times and request_times[0] < window_start:
            request_times.popleft()

        # Check if under limit
        if len(request_times) < self.max_requests:
            request_times.append(now)
            return True

        return False

    def get_remaining(self, key: str) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        request_times = self.requests[key]
        while request_times and request_times[0] < window_start:
            request_times.popleft()

        return max(0, self.max_requests - len(request_times))


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password with salt.

    Args:
        password: Plain text password
        salt: Optional salt (generated if None)

    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)

    # Use PBKDF2 with SHA-256
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    )

    return password_hash.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Verify password against stored hash.

    Args:
        password: Plain text password
        stored_hash: Stored password hash
        salt: Salt used for hashing

    Returns:
        True if password is correct
    """
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, stored_hash)


def generate_api_key() -> str:
    """Generate a secure API key.

    Returns:
        URL-safe base64 encoded API key
    """
    return secrets.token_urlsafe(32)


def validate_api_key(api_key: str) -> bool:
    """Validate API key format.

    Args:
        api_key: API key to validate

    Returns:
        True if format is valid
    """
    if not api_key or not isinstance(api_key, str):
        return False

    # Check length and characters
    if len(api_key) < 32 or len(api_key) > 64:
        return False

    # Should be URL-safe base64
    try:
        import base64
        base64.urlsafe_b64decode(api_key + '==')  # Add padding
        return True
    except Exception:
        return False


def rate_limit(key: str, max_requests: int = 100, window_seconds: int = 60) -> Callable:
    """Rate limiting decorator.

    Args:
        key: Rate limiting key
        max_requests: Max requests per window
        window_seconds: Window size in seconds

    Returns:
        Decorator function
    """
    limiter = RateLimiter(max_requests, window_seconds)

    def decorator(func):
        def wrapper(*args, **kwargs):
            if not limiter.is_allowed(key):
                raise Exception(f"Rate limit exceeded for {key}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global rate limiter instance
rate_limiter = RateLimiter()


# Validation helpers
def is_strong_password(password: str) -> bool:
    """Check if password meets strength requirements.

    Args:
        password: Password to check

    Returns:
        True if password is strong
    """
    if len(password) < 8:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)

    return sum([has_upper, has_lower, has_digit, has_special]) >= 3


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """Sanitize user input.

    Args:
        value: Input to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized input
    """
    if not isinstance(value, str):
        value = str(value)

    # Truncate
    value = value[:max_length]

    # Remove null bytes and control characters
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')

    return value.strip()