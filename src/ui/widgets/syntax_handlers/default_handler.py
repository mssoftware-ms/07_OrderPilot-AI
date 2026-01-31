"""
Handler for default/unrecognized tokens.
"""

from .base_handler import BaseTokenHandler, TokenMatch


class DefaultHandler(BaseTokenHandler):
    """
    Fallback handler for unrecognized characters.

    Always matches and consumes a single character.
    """

    def __init__(self, default_style: int):
        """
        Initialize default handler.

        Args:
            default_style: Style constant for default text
        """
        self._default_style = default_style

    def try_match(self, text: str, position: int) -> TokenMatch:
        """Match any character."""
        if position >= len(text):
            return TokenMatch(matched=False)

        # Always match one character
        return TokenMatch(
            matched=True,
            length=1,
            style=self._default_style
        )

    def get_priority(self) -> int:
        """Default handler has lowest priority (last resort)."""
        return 999
