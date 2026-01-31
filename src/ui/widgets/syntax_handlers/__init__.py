"""
Syntax handlers for CEL lexer.

Token Handler Pattern for modular syntax highlighting.
"""

from .base_handler import BaseTokenHandler, TokenMatch
from .handler_registry import HandlerRegistry

__all__ = [
    'BaseTokenHandler',
    'TokenMatch',
    'HandlerRegistry',
]
