"""
Handler for operator tokens.
"""

from typing import Set
from .base_handler import BaseTokenHandler, TokenMatch


class OperatorHandler(BaseTokenHandler):
    """Handles operators (both single and multi-character)."""

    def __init__(self, operator_style: int, multi_char_ops: Set[str], single_char_ops: str):
        """
        Initialize operator handler.

        Args:
            operator_style: Style constant for operators
            multi_char_ops: Set of multi-character operators (e.g., '==', '!=')
            single_char_ops: String of single-character operators (e.g., '<>=!+-*/')
        """
        self._operator_style = operator_style
        self._multi_char_ops = multi_char_ops
        self._single_char_ops = single_char_ops

    def try_match(self, text: str, position: int) -> TokenMatch:
        """Match operator at position."""
        if position >= len(text):
            return TokenMatch(matched=False)

        # Try multi-character operators first
        if position < len(text) - 1:
            two_char = text[position:position+2]
            if two_char in self._multi_char_ops:
                return TokenMatch(
                    matched=True,
                    length=2,
                    style=self._operator_style
                )

        # Try single-character operators
        if text[position] in self._single_char_ops:
            return TokenMatch(
                matched=True,
                length=1,
                style=self._operator_style
            )

        return TokenMatch(matched=False)

    def get_priority(self) -> int:
        """Operators have medium priority."""
        return 40
