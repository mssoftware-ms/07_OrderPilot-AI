"""
Handler for string literal tokens.
"""

from .base_handler import BaseTokenHandler, TokenMatch


class StringHandler(BaseTokenHandler):
    """Handles string literals (both single and double quotes)."""

    def __init__(self, string_style: int):
        """
        Initialize string handler.

        Args:
            string_style: Style constant for strings
        """
        self._string_style = string_style

    def try_match(self, text: str, position: int) -> TokenMatch:
        """Match string literal at position."""
        if position >= len(text):
            return TokenMatch(matched=False)

        quote_char = text[position]
        if quote_char not in ('"', "'"):
            return TokenMatch(matched=False)

        # Find closing quote
        i = position + 1
        while i < len(text):
            if text[i] == quote_char and text[i-1] != '\\':
                # Found closing quote
                length = i - position + 1
                return TokenMatch(
                    matched=True,
                    length=length,
                    style=self._string_style
                )
            i += 1

        # No closing quote found - still style what we have
        length = len(text) - position
        return TokenMatch(
            matched=True,
            length=length,
            style=self._string_style
        )

    def get_priority(self) -> int:
        """Strings have high priority."""
        return 15
