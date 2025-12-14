"""Logging Configuration for OrderPilot-AI Trading Application.

Provides JSON-formatted logging with rotation support, AI telemetry tracking,
and structured logging for audit trails.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from pythonjsonlogger.json import JsonFormatter

# Import security types for audit logging
try:
    from .security_core import SecurityAction, SecurityContext
except ImportError:
    # Fallback if security_core not available
    SecurityAction = None
    SecurityContext = None


class AITelemetryFilter(logging.Filter):
    """Custom filter to add AI telemetry data to log records."""

    def filter(self, record):
        """Add AI-specific fields to the log record if present."""
        # Add default AI fields if they don't exist
        if not hasattr(record, 'ai_model'):
            record.ai_model = None
        if not hasattr(record, 'ai_tokens'):
            record.ai_tokens = None
        if not hasattr(record, 'ai_cost'):
            record.ai_cost = None
        if not hasattr(record, 'ai_latency'):
            record.ai_latency = None
        if not hasattr(record, 'prompt_version'):
            record.prompt_version = None
        return True


class TradingJsonFormatter(JsonFormatter):
    """Custom JSON formatter for trading application logs."""

    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to the JSON log output."""
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['environment'] = os.getenv('TRADING_ENV', 'development')

        # Add context fields if they exist
        if hasattr(record, 'symbol'):
            log_record['symbol'] = record.symbol
        if hasattr(record, 'strategy'):
            log_record['strategy'] = record.strategy
        if hasattr(record, 'order_id'):
            log_record['order_id'] = record.order_id

        # Add AI telemetry fields
        ai_fields = ['ai_model', 'ai_tokens', 'ai_cost', 'ai_latency', 'prompt_version']
        for field in ai_fields:
            if hasattr(record, field) and getattr(record, field) is not None:
                log_record[field] = getattr(record, field)


def configure_logging(
    level: str = "INFO",
    log_dir: Path | None = None,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 10
) -> None:
    """Configure comprehensive logging for the trading application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (defaults to ./logs)
        enable_console: Enable console output
        enable_file: Enable file output
        enable_json: Use JSON format for logs
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    # Create logs directory if needed
    if log_dir is None:
        log_dir = Path("./logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Formatters
    if enable_json:
        json_format = '%(timestamp)s %(level)s %(name)s %(message)s'
        formatter = TradingJsonFormatter(json_format)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Console Handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(AITelemetryFilter())
        root_logger.addHandler(console_handler)

    # File Handlers
    if enable_file:
        # Main application log
        app_log_path = log_dir / "orderpilot.log"
        file_handler = logging.handlers.RotatingFileHandler(
            app_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(AITelemetryFilter())
        root_logger.addHandler(file_handler)

        # Separate audit log for trading operations
        audit_logger = logging.getLogger('audit')
        audit_log_path = log_dir / "audit.log"
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        audit_handler.setFormatter(formatter)
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False

        # Separate AI telemetry log
        ai_logger = logging.getLogger('ai_telemetry')
        ai_log_path = log_dir / "ai_telemetry.log"
        ai_handler = logging.handlers.RotatingFileHandler(
            ai_log_path,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        ai_handler.setFormatter(formatter)
        ai_handler.addFilter(AITelemetryFilter())
        ai_logger.addHandler(ai_handler)
        ai_logger.setLevel(logging.INFO)
        ai_logger.propagate = False

    # Configure specific loggers
    configure_module_loggers()

    logging.info(f"Logging configured: level={level}, log_dir={log_dir}")


def configure_module_loggers():
    """Configure logging levels for specific modules."""
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)

    # Set specific levels for app modules
    logging.getLogger('tradingapp.broker').setLevel(logging.INFO)
    logging.getLogger('tradingapp.strategy').setLevel(logging.INFO)
    logging.getLogger('tradingapp.ai').setLevel(logging.DEBUG)


def log_order_action(
    action: str,
    order_id: str,
    symbol: str,
    details: dict[str, Any],
    logger_name: str = 'audit'
) -> None:
    """Log order-related actions to the audit log.

    Args:
        action: The action performed (create, submit, fill, cancel, etc.)
        order_id: Unique order identifier
        symbol: Trading symbol
        details: Additional order details
        logger_name: Name of the logger to use
    """
    logger = logging.getLogger(logger_name)
    extra = {
        'order_id': order_id,
        'symbol': symbol,
        'action': action,
        **details
    }
    logger.info(f"Order action: {action}", extra=extra)


def log_security_action(
    action: Any,  # SecurityAction enum or string
    user_id: str = "system",
    session_id: str = "unknown",
    ip_address: str = None,
    details: dict[str, Any] = None,
    success: bool = True
) -> None:
    """Log security-relevant actions.

    Args:
        action: Security action performed
        user_id: User identifier
        session_id: Session identifier
        ip_address: IP address
        details: Additional details
        success: Whether action succeeded
    """
    logger = logging.getLogger('security_audit')

    # Convert action to string if it's an enum
    action_str = action.value if hasattr(action, 'value') else str(action)

    extra = {
        'security_action': action_str,
        'user_id': user_id,
        'session_id': session_id,
        'ip_address': ip_address,
        'success': success,
        'details': details or {}
    }

    level = logging.WARNING if not success else logging.INFO
    logger.log(level, f"Security action: {action_str}", extra=extra)


def get_audit_logger() -> logging.Logger:
    """Get the audit logger instance."""
    return logging.getLogger('audit')


def get_security_audit_logger() -> logging.Logger:
    """Get the security audit logger instance."""
    return logging.getLogger('security_audit')


def log_ai_request(
    model: str,
    tokens: int,
    cost: float,
    latency: float,
    prompt_version: str,
    request_type: str,
    details: dict[str, Any] | None = None
) -> None:
    """Log AI API requests for telemetry and cost tracking.

    Args:
        model: AI model used
        tokens: Token count
        cost: Estimated cost
        latency: Request latency in seconds
        prompt_version: Version of the prompt template
        request_type: Type of AI request (analysis, order_review, etc.)
        details: Additional request details
    """
    logger = logging.getLogger('ai_telemetry')
    extra = {
        'ai_model': model,
        'ai_tokens': tokens,
        'ai_cost': cost,
        'ai_latency': latency,
        'prompt_version': prompt_version,
        'request_type': request_type
    }
    if details:
        extra.update(details)

    logger.info(f"AI request: {request_type}", extra=extra)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
