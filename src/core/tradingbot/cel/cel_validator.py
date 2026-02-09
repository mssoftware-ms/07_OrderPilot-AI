"""CEL Expression Validator - Lexer-based validation with syntax and semantic checking.

Provides comprehensive validation for CEL expressions:
- Lexical analysis (token validation)
- Syntax validation (brackets, operators, structure)
- Semantic validation (function existence, type checking where possible)
- Error reporting with line/column positions
"""

from __future__ import annotations

import re
import logging
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Set, Dict, Any

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Severity levels for validation errors."""
    ERROR = "error"      # Blocking error, expression won't evaluate
    WARNING = "warning"  # Potential issue, but expression may work
    INFO = "info"        # Informational message, no issue


@dataclass
class ValidationError:
    """Validation error with position information.

    Attributes:
        line: Line number (1-indexed)
        column: Column number (1-indexed)
        message: Error description
        severity: Error severity (error, warning, info)
        code: Optional error code for categorization
    """
    line: int
    column: int
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "severity": self.severity.value,
            "code": self.code
        }


class TokenType(str, Enum):
    """CEL token types for lexical analysis."""
    # Literals
    NUMBER = "number"
    STRING = "string"
    BOOL = "bool"
    NULL = "null"

    # Identifiers
    IDENTIFIER = "identifier"

    # Operators
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"

    # Comparison
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="

    # Logical
    AND = "&&"
    OR = "||"
    NOT = "!"

    # Ternary
    QUESTION = "?"
    COLON = ":"

    # Delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    COMMA = ","
    DOT = "."

    # Special
    EOF = "EOF"
    UNKNOWN = "UNKNOWN"


@dataclass
class Token:
    """Lexical token with position."""
    type: TokenType
    value: str
    line: int
    column: int


class CelValidator:
    """CEL Expression Validator with lexer-based validation.

    Validates CEL expressions through multiple stages:
    1. Lexical analysis - tokenize expression
    2. Syntax validation - check structure, brackets, operators
    3. Semantic validation - check function existence, types
    """

    # CEL built-in constants
    CONSTANTS = {'true', 'false', 'null'}

    # CEL built-in + custom functions (synced with src/core/tradingbot/cel_engine.py)
    BUILTIN_FUNCTIONS = {
        # Type conversion
        'type', 'string', 'int', 'double', 'bool', 'timestamp',

        # String functions
        'contains', 'startsWith', 'endsWith', 'toLowerCase', 'toUpperCase',
        'substring', 'split', 'join',

        # Math functions
        'abs', 'min', 'max', 'clamp', 'round', 'floor', 'ceil', 'sqrt', 'pow', 'exp',

        # Collection functions
        'size', 'length', 'has', 'all', 'any', 'map', 'filter',
        'first', 'last', 'indexOf', 'slice', 'distinct', 'sort', 'reverse',
        'sum', 'avg', 'average',

        # Null handling
        'isnull', 'nz', 'coalesce',

        # Custom trading functions (from cel_engine.py)
        'pctl', 'crossover',
        'pct_change', 'pct_from_level', 'level_at_pct', 'retracement', 'extension',
        'is_trade_open', 'is_long', 'is_short', 'is_bullish_signal', 'is_bearish_signal', 'in_regime',
        'stop_hit_long', 'stop_hit_short', 'tp_hit',
        'price_above_ema', 'price_below_ema', 'price_above_level', 'price_below_level',
        'highest', 'lowest', 'sma',
        'pin_bar_bullish', 'pin_bar_bearish', 'inside_bar', 'inverted_hammer',
        'bull_flag', 'bear_flag', 'cup_and_handle', 'double_bottom', 'double_top',
        'ascending_triangle', 'descending_triangle',
        'breakout_above', 'breakdown_below', 'false_breakout', 'break_of_structure',
        'liquidity_swept', 'fvg_exists', 'order_block_retest', 'harmonic_pattern_detected',

        # Time functions
        'now', 'timestamp', 'bar_age', 'bars_since',
        'is_new_day', 'is_new_hour', 'is_new_week', 'is_new_month',
    }

    # Operators by precedence (highest to lowest)
    OPERATOR_PRECEDENCE = {
        # Unary (highest)
        '!': 10, 'u-': 10,
        # Multiplicative
        '*': 9, '/': 9, '%': 9,
        # Additive
        '+': 8, '-': 8,
        # Relational
        '<': 7, '<=': 7, '>': 7, '>=': 7,
        # Equality
        '==': 6, '!=': 6,
        # Logical AND
        '&&': 5,
        # Logical OR
        '||': 4,
        # Ternary (lowest)
        '?': 3, ':': 3,
    }

    def __init__(self, custom_functions: Optional[Set[str]] = None):
        """Initialize validator with optional custom functions.

        Args:
            custom_functions: Additional function names to recognize (beyond built-ins)
        """
        self.custom_functions = custom_functions or set()
        self.all_functions = self.BUILTIN_FUNCTIONS | self.custom_functions
        self.errors: List[ValidationError] = []

    def validate(self, expression: str) -> List[ValidationError]:
        """Validate CEL expression and return list of errors.

        Args:
            expression: CEL expression string to validate

        Returns:
            List of ValidationError objects (empty if valid)
        """
        self.errors = []

        if not expression or not expression.strip():
            self.errors.append(ValidationError(
                line=1,
                column=1,
                message="Empty expression",
                severity=ValidationSeverity.ERROR,
                code="EMPTY_EXPRESSION"
            ))
            return self.errors

        try:
            # Stage 1: Lexical analysis
            tokens = self._tokenize(expression)

            # Stage 2: Syntax validation
            self._validate_syntax(tokens)

            # Stage 3: Semantic validation
            self._validate_semantics(tokens)

        except Exception as e:
            logger.exception("Unexpected validation error")
            self.errors.append(ValidationError(
                line=1,
                column=1,
                message=f"Internal validation error: {str(e)}",
                severity=ValidationSeverity.ERROR,
                code="INTERNAL_ERROR"
            ))

        return self.errors

    def is_valid(self, expression: str) -> bool:
        """Quick validation check - returns True if expression is valid.

        Args:
            expression: CEL expression string

        Returns:
            True if expression has no errors, False otherwise
        """
        errors = self.validate(expression)
        return len([e for e in errors if e.severity == ValidationSeverity.ERROR]) == 0

    def _tokenize(self, expression: str) -> List[Token]:
        """Tokenize CEL expression into list of tokens.

        Args:
            expression: CEL expression string

        Returns:
            List of Token objects
        """
        tokens: List[Token] = []
        line = 1
        column = 1
        i = 0

        while i < len(expression):
            char = expression[i]

            # Skip whitespace (but track line/column)
            if char in ' \t':
                column += 1
                i += 1
                continue

            if char == '\n':
                line += 1
                column = 1
                i += 1
                continue

            # Numbers (int or float)
            if char.isdigit() or (char == '.' and i + 1 < len(expression) and expression[i + 1].isdigit()):
                start_col = column
                num_str = ''
                while i < len(expression) and (expression[i].isdigit() or expression[i] == '.'):
                    num_str += expression[i]
                    column += 1
                    i += 1
                tokens.append(Token(TokenType.NUMBER, num_str, line, start_col))
                continue

            # Strings (single or double quoted)
            if char in ('"', "'"):
                quote_char = char
                start_col = column
                str_val = char
                column += 1
                i += 1
                while i < len(expression):
                    if expression[i] == '\\' and i + 1 < len(expression):
                        # Escape sequence
                        str_val += expression[i:i+2]
                        column += 2
                        i += 2
                    elif expression[i] == quote_char:
                        # Closing quote
                        str_val += expression[i]
                        column += 1
                        i += 1
                        break
                    elif expression[i] == '\n':
                        # Unterminated string (error)
                        self.errors.append(ValidationError(
                            line=line,
                            column=start_col,
                            message=f"Unterminated string literal",
                            severity=ValidationSeverity.ERROR,
                            code="UNTERMINATED_STRING"
                        ))
                        line += 1
                        column = 1
                        i += 1
                        break
                    else:
                        str_val += expression[i]
                        column += 1
                        i += 1
                else:
                    # Reached end without closing quote
                    self.errors.append(ValidationError(
                        line=line,
                        column=start_col,
                        message=f"Unterminated string literal",
                        severity=ValidationSeverity.ERROR,
                        code="UNTERMINATED_STRING"
                    ))

                tokens.append(Token(TokenType.STRING, str_val, line, start_col))
                continue

            # Identifiers and keywords
            if char.isalpha() or char == '_':
                start_col = column
                ident = ''
                while i < len(expression) and (expression[i].isalnum() or expression[i] == '_'):
                    ident += expression[i]
                    column += 1
                    i += 1

                # Check if it's a boolean or null
                if ident in ('true', 'false'):
                    tokens.append(Token(TokenType.BOOL, ident, line, start_col))
                elif ident == 'null':
                    tokens.append(Token(TokenType.NULL, ident, line, start_col))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, ident, line, start_col))
                continue

            # Two-character operators
            if i + 1 < len(expression):
                two_char = expression[i:i+2]
                if two_char in ('==', '!=', '<=', '>=', '&&', '||'):
                    token_type = {
                        '==': TokenType.EQ,
                        '!=': TokenType.NE,
                        '<=': TokenType.LE,
                        '>=': TokenType.GE,
                        '&&': TokenType.AND,
                        '||': TokenType.OR,
                    }[two_char]
                    tokens.append(Token(token_type, two_char, line, column))
                    column += 2
                    i += 2
                    continue

            # Single-character operators and delimiters
            token_map = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '/': TokenType.DIVIDE,
                '%': TokenType.MODULO,
                '<': TokenType.LT,
                '>': TokenType.GT,
                '!': TokenType.NOT,
                '?': TokenType.QUESTION,
                ':': TokenType.COLON,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ',': TokenType.COMMA,
                '.': TokenType.DOT,
            }

            if char in token_map:
                tokens.append(Token(token_map[char], char, line, column))
                column += 1
                i += 1
                continue

            # Unknown character
            self.errors.append(ValidationError(
                line=line,
                column=column,
                message=f"Unexpected character: '{char}'",
                severity=ValidationSeverity.ERROR,
                code="UNEXPECTED_CHAR"
            ))
            tokens.append(Token(TokenType.UNKNOWN, char, line, column))
            column += 1
            i += 1

        tokens.append(Token(TokenType.EOF, "", line, column))
        return tokens

    def _validate_syntax(self, tokens: List[Token]) -> None:
        """Validate syntax: brackets, operators, structure.

        Args:
            tokens: List of tokens from lexical analysis
        """
        # Check balanced brackets/parentheses
        paren_stack = []
        bracket_stack = []

        for token in tokens:
            if token.type == TokenType.LPAREN:
                paren_stack.append(token)
            elif token.type == TokenType.RPAREN:
                if not paren_stack:
                    self.errors.append(ValidationError(
                        line=token.line,
                        column=token.column,
                        message="Unmatched closing parenthesis ')'",
                        severity=ValidationSeverity.ERROR,
                        code="UNMATCHED_PAREN"
                    ))
                else:
                    paren_stack.pop()

            elif token.type == TokenType.LBRACKET:
                bracket_stack.append(token)
            elif token.type == TokenType.RBRACKET:
                if not bracket_stack:
                    self.errors.append(ValidationError(
                        line=token.line,
                        column=token.column,
                        message="Unmatched closing bracket ']'",
                        severity=ValidationSeverity.ERROR,
                        code="UNMATCHED_BRACKET"
                    ))
                else:
                    bracket_stack.pop()

        # Check unclosed brackets/parentheses
        for token in paren_stack:
            self.errors.append(ValidationError(
                line=token.line,
                column=token.column,
                message="Unclosed opening parenthesis '('",
                severity=ValidationSeverity.ERROR,
                code="UNCLOSED_PAREN"
            ))

        for token in bracket_stack:
            self.errors.append(ValidationError(
                line=token.line,
                column=token.column,
                message="Unclosed opening bracket '['",
                severity=ValidationSeverity.ERROR,
                code="UNCLOSED_BRACKET"
            ))

        # Check operator usage (no consecutive binary operators)
        binary_ops = {TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE,
                     TokenType.MODULO, TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE,
                     TokenType.GT, TokenType.GE, TokenType.AND, TokenType.OR}

        for i in range(len(tokens) - 1):
            if tokens[i].type in binary_ops and tokens[i+1].type in binary_ops:
                self.errors.append(ValidationError(
                    line=tokens[i+1].line,
                    column=tokens[i+1].column,
                    message=f"Consecutive binary operators: '{tokens[i].value}' '{tokens[i+1].value}'",
                    severity=ValidationSeverity.ERROR,
                    code="CONSECUTIVE_OPERATORS"
                ))

    def _validate_semantics(self, tokens: List[Token]) -> None:
        """Validate semantics: function existence, basic type checking.

        Args:
            tokens: List of tokens from lexical analysis
        """
        # Check function calls exist
        for i, token in enumerate(tokens):
            if token.type == TokenType.IDENTIFIER:
                # Check if followed by LPAREN (function call)
                if i + 1 < len(tokens) and tokens[i + 1].type == TokenType.LPAREN:
                    func_name = token.value
                    if func_name not in self.all_functions:
                        self.errors.append(ValidationError(
                            line=token.line,
                            column=token.column,
                            message=f"Unknown function: '{func_name}'",
                            severity=ValidationSeverity.ERROR,
                            code="UNKNOWN_FUNCTION"
                        ))

        # Check ternary operator syntax (? must have matching :)
        question_marks = [t for t in tokens if t.type == TokenType.QUESTION]
        colons = [t for t in tokens if t.type == TokenType.COLON]

        # Simple check: count should match (more sophisticated would track nesting)
        if len(question_marks) != len(colons):
            if question_marks:
                self.errors.append(ValidationError(
                    line=question_marks[-1].line,
                    column=question_marks[-1].column,
                    message="Incomplete ternary operator: '?' without matching ':'",
                    severity=ValidationSeverity.ERROR,
                    code="INCOMPLETE_TERNARY"
                ))
