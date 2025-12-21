"""Comprehensive Security Module for OrderPilot-AI.

This module provides all security functionality in a unified interface:
- Security configuration and types
- Password hashing and API key management
- Rate limiting and validation
- Encryption and credential storage
- Session management
- Audit logging (integrated with main logging system)

Consolidates functionality from multiple security modules for better maintainability.
"""

# Core security functionality
from .security_core import (
    SecurityLevel,
    SecurityAction,
    SecurityContext,
    RateLimiter,
    hash_password,
    verify_password,
    generate_api_key,
    validate_api_key,
    rate_limit,
    rate_limiter,
    is_strong_password,
    sanitize_input
)

# Advanced security features
from .security_manager import (
    EncryptionManager,
    CredentialManager,
    SessionManager,
    require_auth,
    encryption_manager,
    credential_manager,
    session_manager
)

# Audit logging (now integrated with main logging)
from .logging_setup import (
    log_security_action,
    get_audit_logger,
    get_security_audit_logger
)

# Convenience aliases for backward compatibility
def audit_action(action, context, details=None, success=True):
    """Backward compatibility wrapper for audit logging."""
    log_security_action(
        action=action,
        user_id=context.user_id if context else "unknown",
        session_id=context.session_id if context else "unknown",
        ip_address=context.ip_address if context else None,
        details=details,
        success=success
    )

# Create global audit logger instance for compatibility
audit_logger = get_audit_logger()

# Re-export all components for backward compatibility
__all__ = [
    # Types and configuration
    'SecurityLevel',
    'SecurityAction',
    'SecurityContext',

    # Validation and rate limiting
    'RateLimiter',
    'hash_password',
    'verify_password',
    'generate_api_key',
    'validate_api_key',
    'rate_limit',
    'is_strong_password',
    'sanitize_input',

    # Audit logging
    'audit_action',
    'log_security_action',
    'get_audit_logger',
    'get_security_audit_logger',

    # Encryption and session management
    'EncryptionManager',
    'CredentialManager',
    'SessionManager',
    'require_auth',

    # Global instances
    'encryption_manager',
    'credential_manager',
    'session_manager',
    'audit_logger',
    'rate_limiter'
]
