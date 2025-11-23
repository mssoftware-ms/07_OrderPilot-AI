"""Security Audit Logging for OrderPilot-AI.

Provides audit logging for security-relevant actions.
"""

import json
import logging
from datetime import datetime
from functools import wraps
from typing import Any

from src.common.event_bus import Event, EventType, event_bus
from src.database import get_db_manager
from src.database.models import AuditLog

from .security_config import SecurityAction, SecurityContext

logger = logging.getLogger(__name__)


class AuditLogger:
    """Handles security audit logging."""

    def __init__(self):
        """Initialize audit logger."""
        self.db_manager = get_db_manager()

    def log_action(
        self,
        action: SecurityAction,
        context: SecurityContext,
        details: dict[str, Any] | None = None,
        success: bool = True
    ):
        """Log security-relevant action.

        Args:
            action: Action performed
            context: Security context
            details: Additional details
            success: Whether action was successful
        """
        try:
            with self.db_manager.session() as session:
                audit_log = AuditLog(
                    timestamp=datetime.utcnow(),
                    action=action.value,
                    user_id=context.user_id,
                    session_id=context.session_id,
                    ip_address=context.ip_address,
                    security_level=context.security_level.value,
                    success=success,
                    details=json.dumps(details) if details else None
                )
                session.add(audit_log)
                session.commit()

            # Also emit event
            event_bus.emit(Event(
                type=EventType.SECURITY_AUDIT,
                timestamp=datetime.utcnow(),
                data={
                    'action': action.value,
                    'user_id': context.user_id,
                    'success': success,
                    'security_level': context.security_level.value
                }
            ))

            logger.debug(f"Audit logged: {action.value} by {context.user_id}")

        except Exception as e:
            logger.error(f"Failed to log audit: {e}")

    def get_audit_logs(
        self,
        user_id: str | None = None,
        action: SecurityAction | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100
    ) -> list[AuditLog]:
        """Get audit logs.

        Args:
            user_id: Filter by user
            action: Filter by action
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum results

        Returns:
            List of audit logs
        """
        try:
            with self.db_manager.session() as session:
                query = session.query(AuditLog)

                if user_id:
                    query = query.filter(AuditLog.user_id == user_id)
                if action:
                    query = query.filter(AuditLog.action == action.value)
                if start_date:
                    query = query.filter(AuditLog.timestamp >= start_date)
                if end_date:
                    query = query.filter(AuditLog.timestamp <= end_date)

                return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()

        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []


# Audit logging decorator

def audit_action(action: SecurityAction):
    """Decorator for audit logging.

    Args:
        action: Security action to log
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            context = kwargs.get('security_context')
            audit_logger = AuditLogger()

            try:
                result = func(*args, **kwargs)
                if context:
                    audit_logger.log_action(action, context, success=True)
                return result

            except Exception as e:
                if context:
                    audit_logger.log_action(
                        action, context,
                        details={'error': str(e)},
                        success=False
                    )
                raise

        return wrapper
    return decorator


# Lazy initialization for audit_logger to avoid database dependency on import
_audit_logger = None

def get_audit_logger():
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# For backward compatibility
audit_logger = get_audit_logger
