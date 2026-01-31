"""
Handler for identifier tokens (keywords, functions, variables, indicators).
"""

from typing import Set
from .base_handler import BaseTokenHandler, TokenMatch


class IdentifierHandler(BaseTokenHandler):
    """
    Handles identifiers and classifies them as keywords, functions, etc.

    This handler matches any identifier (word starting with letter or underscore)
    and determines the appropriate style based on keyword sets.
    """

    def __init__(
        self,
        keywords: Set[str],
        trading_keywords: Set[str],
        functions: Set[str],
        variables: Set[str],
        keyword_style: int,
        function_style: int,
        variable_style: int,
        indicator_style: int,
        identifier_style: int
    ):
        """
        Initialize identifier handler.

        Args:
            keywords: Set of CEL keywords
            trading_keywords: Set of trading-specific keywords
            functions: Set of known function names
            variables: Set of known variables (e.g., 'trade', 'cfg')
            keyword_style: Style for keywords
            function_style: Style for functions
            variable_style: Style for variables
            indicator_style: Style for indicators (e.g., rsi14.value)
            identifier_style: Style for unrecognized identifiers
        """
        self._keywords = keywords
        self._trading_keywords = trading_keywords
        self._functions = functions
        self._variables = variables
        self._keyword_style = keyword_style
        self._function_style = function_style
        self._variable_style = variable_style
        self._indicator_style = indicator_style
        self._identifier_style = identifier_style

    def try_match(self, text: str, position: int) -> TokenMatch:
        """Match identifier at position."""
        if position >= len(text):
            return TokenMatch(matched=False)

        # Must start with letter or underscore
        if not (text[position].isalpha() or text[position] == '_'):
            return TokenMatch(matched=False)

        # Consume identifier
        i = position + 1
        while i < len(text) and (text[i].isalnum() or text[i] == '_'):
            i += 1

        word = text[position:i]
        word_len = i - position

        # Check for indicator access (e.g., rsi14.value)
        if i < len(text) and text[i] == '.':
            # Find end of property access
            j = i + 1
            while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                j += 1

            # Style entire indicator reference
            return TokenMatch(
                matched=True,
                length=j - position,
                style=self._indicator_style
            )

        # Determine style based on word
        style = self._get_word_style(word)

        return TokenMatch(
            matched=True,
            length=word_len,
            style=style
        )

    def _get_word_style(self, word: str) -> int:
        """Determine the appropriate style for a word."""
        if word in self._keywords or word in self._trading_keywords:
            return self._keyword_style
        elif word in self._functions:
            return self._function_style
        elif word in self._variables:
            return self._variable_style
        else:
            return self._identifier_style

    def get_priority(self) -> int:
        """Identifiers have low priority (matched after everything else)."""
        return 50
