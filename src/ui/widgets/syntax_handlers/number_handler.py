"""
Handler for numeric literal tokens.
"""

from .base_handler import BaseTokenHandler, TokenMatch


class NumberHandler(BaseTokenHandler):
    """Handles numeric literals (integers and floats)."""

    def __init__(self, number_style: int):
        """
        Initialize number handler.

        Args:
            number_style: Style constant for numbers
        """
        self._number_style = number_style

    def try_match(self, text: str, position: int) -> TokenMatch:
        """Match number at position."""
        if position >= len(text):
            return TokenMatch(matched=False)

        char = text[position]

        # Check if starts with digit or decimal point
        is_number_start = char.isdigit()
        is_decimal_start = (
            char == '.' and
            position + 1 < len(text) and
            text[position + 1].isdigit()
        )

        if not (is_number_start or is_decimal_start):
            return TokenMatch(matched=False)

        # Consume number
        i = position + 1
        has_dot = (char == '.')

        while i < len(text):
            if text[i].isdigit():
                i += 1
            elif text[i] == '.' and not has_dot:
                has_dot = True
                i += 1
            else:
                break

        length = i - position

        return TokenMatch(
            matched=True,
            length=length,
            style=self._number_style
        )

    def get_priority(self) -> int:
        """Numbers have medium-high priority."""
        return 20
