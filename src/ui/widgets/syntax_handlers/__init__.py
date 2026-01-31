"""
Syntax handlers for CEL lexer.

Token Handler Pattern for modular syntax highlighting.
"""

from .base_handler import BaseTokenHandler, TokenMatch
from .handler_registry import HandlerRegistry
from .whitespace_handler import WhitespaceHandler
from .comment_handler import CommentHandler
from .string_handler import StringHandler
from .number_handler import NumberHandler
from .operator_handler import OperatorHandler
from .identifier_handler import IdentifierHandler
from .default_handler import DefaultHandler

__all__ = [
    'BaseTokenHandler',
    'TokenMatch',
    'HandlerRegistry',
    'WhitespaceHandler',
    'CommentHandler',
    'StringHandler',
    'NumberHandler',
    'OperatorHandler',
    'IdentifierHandler',
    'DefaultHandler',
]
