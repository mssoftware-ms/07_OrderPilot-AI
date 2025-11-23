"""Security Module for OrderPilot-AI - Facade Module.

This module maintains backward compatibility by re-exporting components
from the new modular security subsystem:

- security_config: Types, enums, and configuration
- security_validator: Password hashing, API key validation, rate limiting
- security_audit: Audit logging and security event tracking
- security_manager: Encryption, credential storage, session management

Provides encryption, authentication, audit logging, and secure credential management.
Implements defense-in-depth security measures for trading operations.
"""

# Import all components from new modular structure

from .security_config import (
    SecurityLevel,
    SecurityAction,
    SecurityContext
)

from .security_validator import (
    RateLimiter,
    hash_password,
    verify_password,
    generate_api_key,
    validate_api_key,
    rate_limit,
    rate_limiter
)

from .security_audit import (
    AuditLogger,
    audit_action,
    get_audit_logger,
    audit_logger
)

from .security_manager import (
    EncryptionManager,
    CredentialManager,
    SessionManager,
    require_auth,
    encryption_manager,
    credential_manager,
    session_manager
)

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

    # Audit logging
    'AuditLogger',
    'audit_action',
    'get_audit_logger',

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
