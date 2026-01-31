"""
Registry for managing token handlers.

Coordinates multiple handlers in priority order.
"""

from typing import List
from .base_handler import BaseTokenHandler, TokenMatch


class HandlerRegistry:
    """
    Registry that coordinates multiple token handlers.

    Handlers are tried in priority order until one matches.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._handlers: List[BaseTokenHandler] = []
        self._sorted = False

    def register(self, handler: BaseTokenHandler):
        """
        Register a new token handler.

        Args:
            handler: Handler to register
        """
        self._handlers.append(handler)
        self._sorted = False

    def _ensure_sorted(self):
        """Ensure handlers are sorted by priority."""
        if not self._sorted:
            self._handlers.sort(key=lambda h: h.get_priority())
            self._sorted = True

    def try_match(self, text: str, position: int) -> TokenMatch:
        """
        Try to match a token using registered handlers.

        Handlers are tried in priority order until one matches.

        Args:
            text: Full text being styled
            position: Current position in text

        Returns:
            TokenMatch from the first matching handler, or no-match result
        """
        self._ensure_sorted()

        for handler in self._handlers:
            result = handler.try_match(text, position)
            if result.matched:
                return result

        # No handler matched
        return TokenMatch(matched=False)

    def clear(self):
        """Remove all registered handlers."""
        self._handlers.clear()
        self._sorted = False

    def get_handler_count(self) -> int:
        """Get number of registered handlers."""
        return len(self._handlers)
