"""CEL Engine Utilities - Helper functions and context management.

This module contains utility functions for the CEL engine, including:
- Context value resolution
- Singleton factory pattern
- Helper methods for flag evaluation

Part of the CEL (Common Expression Language) engine refactoring.
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .cel_engine_core import CELEngine

logger = logging.getLogger(__name__)


class CELContextHelper:
    """Helper methods for CEL context value resolution."""

    def __init__(self, engine_instance: CELEngine):
        """Initialize context helper.

        Args:
            engine_instance: Reference to parent CEL engine instance
        """
        self.engine = engine_instance

    def get_context_value(self, key: str) -> Any:
        """Resolve a value from the last evaluation context.

        Supports both flat keys (e.g., "pattern.pin_bar_bullish")
        and nested dicts (e.g., context["pattern"]["pin_bar_bullish"]).

        Args:
            key: Context key to resolve

        Returns:
            Resolved value or None if not found
        """
        ctx = self.engine._last_context or {}
        if key in ctx:
            return ctx.get(key)
        if "." in key:
            namespace, sub = key.split(".", 1)
            container = ctx.get(namespace)
            if isinstance(container, dict):
                return container.get(sub)
        return None

    def context_flag(self, *keys: str) -> bool:
        """Return boolean flag for the first available key.

        Args:
            *keys: Multiple key options to try in order

        Returns:
            Boolean value of first found key, False if none found
        """
        for key in keys:
            value = self.get_context_value(key)
            if value is not None:
                return bool(value)
        return False


# Singleton instance for convenience
_default_engine: CELEngine | None = None


def get_cel_engine() -> CELEngine:
    """Get or create default CEL engine instance.

    Returns:
        Default CELEngine instance (singleton)
    """
    global _default_engine
    if _default_engine is None:
        from .cel_engine_core import CELEngine
        _default_engine = CELEngine()
    return _default_engine


def reset_cel_engine() -> None:
    """Reset singleton CEL engine instance (primarily for testing)."""
    global _default_engine
    _default_engine = None
