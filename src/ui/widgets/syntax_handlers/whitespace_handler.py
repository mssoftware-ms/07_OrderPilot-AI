"""
Handler for whitespace tokens.
"""

from .base_handler import BaseTokenHandler, TokenMatch


class WhitespaceHandler(BaseTokenHandler):
    """Handles whitespace characters."""

    def __init__(self, default_style: int):
        """
        Initialize whitespace handler.

        Args:
            default_style: Style constant for default/whitespace
        """
        self._default_style = default_style

    def try_match(self, text: str, position: int) -> TokenMatch:
        """Match whitespace at position."""
        if position >= len(text):
            return TokenMatch(matched=False)

        if text[position].isspace():
            return TokenMatch(
                matched=True,
                length=1,
                style=self._default_style
            )

        return TokenMatch(matched=False)

    def get_priority(self) -> int:
        """Whitespace has lowest priority."""
        return 100
