"""
CEL Expression Validator with syntax and semantic checks.

Validates CEL (Common Expression Language) code for:
- Syntax errors (brackets, quotes, operators)
- Semantic errors (unknown functions, invalid arguments)
- Type errors (where determinable)
"""

from dataclasses import dataclass
from typing import List, Set, Optional
import re

try:
    from src.core.tradingbot.cel.cel_validator import CelValidator as CoreCelValidator
    CORE_FUNCTIONS: Set[str] = set(CoreCelValidator.BUILTIN_FUNCTIONS)
except Exception:
    CoreCelValidator = None
    CORE_FUNCTIONS = set()


@dataclass
class ValidationError:
    """CEL validation error."""

    line: int  # 0-indexed line number
    column: int  # 0-indexed column number
    message: str  # Error message
    severity: str = "error"  # error, warning, info

    def __str__(self) -> str:
        return f"Line {self.line + 1}, Col {self.column + 1}: {self.message}"


class CelValidator:
    """Validator for CEL expressions with trading-specific knowledge."""

    # Known CEL keywords
    KEYWORDS = {
        'true', 'false', 'null',
        'in', 'has', 'all', 'any',
        'map', 'filter', 'first', 'last',
        'size', 'type', 'string', 'int', 'double', 'bool'
    }

    # Trading-specific variables
    TRADING_VARS = {
        'trade', 'cfg', 'regime', 'direction',
        'open', 'high', 'low', 'close', 'volume',
        'atrp', 'atr', 'bbwidth', 'squeeze_on',
        'spread_bps', 'depth_bid', 'depth_ask', 'obi'
    }

    # All known functions (synced to core CEL validator if available)
    ALL_FUNCTIONS = CORE_FUNCTIONS or {
        'abs', 'min', 'max', 'clamp', 'round', 'floor', 'ceil', 'sqrt', 'pow', 'exp',
        'type', 'string', 'int', 'double', 'bool', 'timestamp',
        'contains', 'startsWith', 'endsWith', 'toLowerCase', 'toUpperCase',
        'substring', 'split', 'join',
        'size', 'length', 'has', 'all', 'any', 'map', 'filter',
        'first', 'last', 'indexOf', 'slice', 'distinct', 'sort', 'reverse',
        'sum', 'avg', 'average',
        'isnull', 'nz', 'coalesce',
        'pctl', 'crossover',
        'pct_change', 'pct_from_level', 'level_at_pct', 'retracement', 'extension',
        'is_trade_open', 'is_long', 'is_short', 'is_bullish_signal', 'is_bearish_signal', 'in_regime',
        'stop_hit_long', 'stop_hit_short', 'tp_hit',
        'price_above_ema', 'price_below_ema', 'price_above_level', 'price_below_level',
        'highest', 'lowest', 'sma',
        'now', 'timestamp', 'bar_age', 'bars_since', 'is_new_day', 'is_new_hour', 'is_new_week', 'is_new_month',
    }

    # Valid operators
    OPERATORS = {
        '==', '!=', '<', '>', '<=', '>=',
        '&&', '||', '!',
        '+', '-', '*', '/', '%',
        '?', ':'
    }

    def __init__(self):
        """Initialize validator."""
        pass

    def validate(self, code: str) -> List[ValidationError]:
        """Validate CEL code and return list of errors.

        Args:
            code: CEL expression code

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Split into lines for line-level validation
        lines = code.split('\n')

        # 1. Check bracket balance
        errors.extend(self._check_brackets(code))

        # 2. Check quote balance
        errors.extend(self._check_quotes(code))

        # 3. Check function names
        errors.extend(self._check_functions(code))

        # 4. Check operators
        errors.extend(self._check_operators(code))

        # 5. Check for common syntax errors
        errors.extend(self._check_syntax(code))

        return errors

    def _check_brackets(self, code: str) -> List[ValidationError]:
        """Check bracket balance (parentheses, square, curly).

        Args:
            code: CEL code

        Returns:
            List of bracket-related errors
        """
        errors = []
        stack = []  # Stack of (bracket_type, line, col)

        # Track position
        line = 0
        col = 0

        bracket_pairs = {'(': ')', '[': ']', '{': '}'}
        opening = set(bracket_pairs.keys())
        closing = set(bracket_pairs.values())

        for char in code:
            if char == '\n':
                line += 1
                col = 0
                continue

            if char in opening:
                stack.append((char, line, col))
            elif char in closing:
                if not stack:
                    errors.append(ValidationError(
                        line, col,
                        f"Unmatched closing bracket '{char}'"
                    ))
                else:
                    opener, opener_line, opener_col = stack.pop()
                    expected = bracket_pairs[opener]
                    if char != expected:
                        errors.append(ValidationError(
                            line, col,
                            f"Mismatched brackets: '{opener}' at line {opener_line + 1} "
                            f"closed with '{char}'"
                        ))

            col += 1

        # Check for unclosed brackets
        for bracket, br_line, br_col in stack:
            errors.append(ValidationError(
                br_line, br_col,
                f"Unclosed bracket '{bracket}'"
            ))

        return errors

    def _check_quotes(self, code: str) -> List[ValidationError]:
        """Check quote balance (single and double quotes).

        Args:
            code: CEL code

        Returns:
            List of quote-related errors
        """
        errors = []

        # Track position
        line = 0
        col = 0

        in_single = False
        in_double = False
        single_start = None
        double_start = None

        i = 0
        while i < len(code):
            char = code[i]

            if char == '\n':
                # Quotes should not span lines (in most cases)
                if in_single:
                    errors.append(ValidationError(
                        single_start[0], single_start[1],
                        "Unclosed single quote (quotes should not span lines)"
                    ))
                    in_single = False
                if in_double:
                    errors.append(ValidationError(
                        double_start[0], double_start[1],
                        "Unclosed double quote (quotes should not span lines)"
                    ))
                    in_double = False
                line += 1
                col = 0
                i += 1
                continue

            # Check for escaped quotes
            if i > 0 and code[i - 1] == '\\':
                col += 1
                i += 1
                continue

            if char == '"' and not in_single:
                if in_double:
                    in_double = False
                    double_start = None
                else:
                    in_double = True
                    double_start = (line, col)
            elif char == "'" and not in_double:
                if in_single:
                    in_single = False
                    single_start = None
                else:
                    in_single = True
                    single_start = (line, col)

            col += 1
            i += 1

        # Check for unclosed quotes at end
        if in_single and single_start:
            errors.append(ValidationError(
                single_start[0], single_start[1],
                "Unclosed single quote"
            ))
        if in_double and double_start:
            errors.append(ValidationError(
                double_start[0], double_start[1],
                "Unclosed double quote"
            ))

        return errors

    def _check_functions(self, code: str) -> List[ValidationError]:
        """Check for unknown function names.

        Args:
            code: CEL code

        Returns:
            List of function-related errors
        """
        errors = []

        # Regex to find function calls: identifier followed by (
        # This is a simple heuristic and may have false positives
        func_pattern = re.compile(r'\b([a-zA-Z_]\w*)\s*\(')

        lines = code.split('\n')
        for line_num, line in enumerate(lines):
            for match in func_pattern.finditer(line):
                func_name = match.group(1)
                col = match.start(1)

                # Check if it's a known keyword (not a function call)
                if func_name in self.KEYWORDS:
                    continue

                # Check if it's a known function
                if func_name not in self.ALL_FUNCTIONS:
                    errors.append(ValidationError(
                        line_num, col,
                        f"Unknown function '{func_name}'",
                        severity="warning"
                    ))

        return errors

    def _check_operators(self, code: str) -> List[ValidationError]:
        """Check for invalid operator usage.

        Args:
            code: CEL code

        Returns:
            List of operator-related errors
        """
        errors = []

        # Check for common operator mistakes
        lines = code.split('\n')
        for line_num, line in enumerate(lines):
            # Check for single = instead of ==
            if re.search(r'[^=!<>]=(?!=)', line):
                # Find all positions
                for match in re.finditer(r'[^=!<>]=((?!=))', line):
                    col = match.start() + 1
                    errors.append(ValidationError(
                        line_num, col,
                        "Assignment operator '=' not valid in CEL. Use '==' for comparison."
                    ))

            # Check for invalid operator combinations
            if '===' in line:
                col = line.find('===')
                errors.append(ValidationError(
                    line_num, col,
                    "Invalid operator '==='. Use '==' for equality."
                ))

        return errors

    def _check_syntax(self, code: str) -> List[ValidationError]:
        """Check for common syntax errors.

        Args:
            code: CEL code

        Returns:
            List of syntax errors
        """
        errors = []

        lines = code.split('\n')
        for line_num, line in enumerate(lines):
            stripped = line.strip()

            # Check for trailing operators (incomplete expressions)
            if stripped and stripped[-1] in {'+', '-', '*', '/', '%', '&&', '||'}:
                errors.append(ValidationError(
                    line_num, len(line) - 1,
                    f"Incomplete expression: trailing operator '{stripped[-1]}'"
                ))

            # Check for multiple operators in a row (except unary minus)
            if re.search(r'[+*/]{2,}', line):
                col = re.search(r'[+*/]{2,}', line).start()
                errors.append(ValidationError(
                    line_num, col,
                    "Invalid syntax: multiple operators in a row"
                ))

        return errors

    def validate_and_format_errors(self, code: str) -> str:
        """Validate code and return formatted error message.

        Args:
            code: CEL code to validate

        Returns:
            Formatted error message (empty string if no errors)
        """
        errors = self.validate(code)

        if not errors:
            return ""

        # Group by severity
        error_msgs = [e for e in errors if e.severity == "error"]
        warning_msgs = [e for e in errors if e.severity == "warning"]

        result = []

        if error_msgs:
            result.append(f"❌ {len(error_msgs)} Error(s):")
            for err in error_msgs[:5]:  # Limit to first 5
                result.append(f"  • {err}")
            if len(error_msgs) > 5:
                result.append(f"  ... and {len(error_msgs) - 5} more errors")

        if warning_msgs:
            result.append(f"⚠️  {len(warning_msgs)} Warning(s):")
            for warn in warning_msgs[:3]:  # Limit to first 3
                result.append(f"  • {warn}")
            if len(warning_msgs) > 3:
                result.append(f"  ... and {len(warning_msgs) - 3} more warnings")

        return "\n".join(result)
