"""Security Validation and Rate Limiting for OrderPilot-AI.

Provides password hashing, API key validation, and rate limiting.
"""

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Any

from .security_config import SecurityContext

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting for API and trading operations."""

    def __init__(self):
        """Initialize rate limiter."""
        self.limits: dict[str, dict[str, Any]] = {}
        self.requests: dict[str, list[datetime]] = {}

    def set_limit(self, key: str, max_requests: int, time_window: int):
        """Set rate limit.

        Args:
            key: Limit key (e.g., 'api', 'trading')
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        """
        self.limits[key] = {
            'max_requests': max_requests,
            'time_window': timedelta(seconds=time_window)
        }

    def check_limit(self, key: str, identifier: str) -> bool:
        """Check if rate limit exceeded.

        Args:
            key: Limit key
            identifier: User/session identifier

        Returns:
            True if within limits
        """
        if key not in self.limits:
            return True

        limit = self.limits[key]
        request_key = f"{key}:{identifier}"

        # Get recent requests
        if request_key not in self.requests:
            self.requests[request_key] = []

        now = datetime.utcnow()
        window_start = now - limit['time_window']

        # Remove old requests
        self.requests[request_key] = [
            req for req in self.requests[request_key]
            if req > window_start
        ]

        # Check limit
        if len(self.requests[request_key]) >= limit['max_requests']:
            logger.warning(f"Rate limit exceeded for {identifier} on {key}")
            return False

        # Add current request
        self.requests[request_key].append(now)
        return True


# Password hashing utilities

def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Hash password with salt.

    Args:
        password: Plain text password
        salt: Optional salt (generated if None)

    Returns:
        Tuple of (hash, salt)
    """
    if not salt:
        salt = secrets.token_hex(16)

    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    hash_str = hash_obj.hex()

    return hash_str, salt


def verify_password(password: str, hash_str: str, salt: str) -> bool:
    """Verify password against hash.

    Args:
        password: Plain text password
        hash_str: Password hash
        salt: Password salt

    Returns:
        True if password matches
    """
    test_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(test_hash, hash_str)


# API key utilities

def generate_api_key() -> str:
    """Generate secure API key.

    Returns:
        API key string
    """
    return secrets.token_urlsafe(32)


def validate_api_key(api_key: str) -> bool:
    """Validate API key format.

    Args:
        api_key: API key to validate

    Returns:
        True if valid format
    """
    # Basic validation - in production, check against database
    # URL-safe tokens can contain alphanumeric, underscore, and hyphen
    if len(api_key) < 32:
        return False

    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    return all(c in allowed_chars for c in api_key)


# Rate limiting decorator

def rate_limit(key: str, max_requests: int = 10, time_window: int = 60):
    """Decorator for rate limiting.

    Args:
        key: Rate limit key
        max_requests: Maximum requests
        time_window: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = RateLimiter()
            limiter.set_limit(key, max_requests, time_window)

            context = kwargs.get('security_context')
            identifier = context.user_id if context else 'anonymous'

            if not limiter.check_limit(key, identifier):
                raise PermissionError(f"Rate limit exceeded for {key}")

            return func(*args, **kwargs)

        return wrapper
    return decorator


# Initialize global rate limiter
rate_limiter = RateLimiter()

# Set default rate limits
rate_limiter.set_limit('api', max_requests=100, time_window=60)
rate_limiter.set_limit('trading', max_requests=10, time_window=60)
rate_limiter.set_limit('auth', max_requests=5, time_window=300)
