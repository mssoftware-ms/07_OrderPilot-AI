"""
Handler for comment tokens.
"""

from .base_handler import BaseTokenHandler, TokenMatch


class CommentHandler(BaseTokenHandler):
    """Handles // style comments."""

    def __init__(self, comment_style: int):
        """
        Initialize comment handler.

        Args:
            comment_style: Style constant for comments
        """
        self._comment_style = comment_style

    def try_match(self, text: str, position: int) -> TokenMatch:
        """Match comment at position."""
        if position >= len(text) - 1:
            return TokenMatch(matched=False)

        # Check for // comment
        if text[position:position+2] == '//':
            # Find end of line
            end_pos = text.find('\n', position)
            if end_pos == -1:
                end_pos = len(text)

            length = end_pos - position

            return TokenMatch(
                matched=True,
                length=length,
                style=self._comment_style
            )

        return TokenMatch(matched=False)

    def get_priority(self) -> int:
        """Comments have high priority (must match before operators)."""
        return 10
