"""Security Configuration and Types for OrderPilot-AI.

Defines security levels, actions, and context dataclasses.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


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
    permissions: list[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.permissions is None:
            self.permissions = []
