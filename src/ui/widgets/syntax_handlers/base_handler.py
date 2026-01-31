"""
Base classes for syntax token handlers.

Provides abstract interface for token handling in Token Handler Pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TokenMatch:
    """
    Result of token matching.

    Attributes:
        matched: Whether the token was matched by this handler
        length: Number of characters consumed
        style: Style constant to apply (e.g., CelLexer.KEYWORD)
    """
    matched: bool
    length: int = 0
    style: int = 0


class BaseTokenHandler(ABC):
    """
    Base class for syntax token handlers.

    Each handler is responsible for recognizing and styling one category
    of tokens (e.g., keywords, operators, strings).
    """

    @abstractmethod
    def try_match(self, text: str, position: int) -> TokenMatch:
        """
        Try to match a token at the given position.

        Args:
            text: Full text being styled
            position: Current position in text

        Returns:
            TokenMatch indicating if matched and how to style
        """
        pass

    @abstractmethod
    def get_priority(self) -> int:
        """
        Get handler priority (lower = higher priority).

        Handlers are tried in order of priority. For example,
        multi-character operators should have higher priority
        than single-character operators.

        Returns:
            Priority value (0-100, lower is higher priority)
        """
        pass
