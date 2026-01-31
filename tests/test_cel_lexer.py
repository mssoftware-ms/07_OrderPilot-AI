"""
Tests for CEL Lexer syntax highlighting.

Tests the styleText() function and Token Handler Pattern.
"""

import pytest
from PyQt6.QtGui import QColor
from unittest.mock import Mock, MagicMock

# Import with fallback for headless environments
try:
    from src.ui.widgets.cel_lexer import CelLexer, QSCI_AVAILABLE
except ImportError:
    pytest.skip("QScintilla not available", allow_module_level=True)


@pytest.fixture
def mock_editor():
    """Create a mock editor for testing."""
    editor = Mock()
    editor.text = Mock(return_value="")
    return editor


@pytest.fixture
def lexer(mock_editor):
    """Create a lexer instance with mock editor."""
    lex = CelLexer()
    lex.editor = Mock(return_value=mock_editor)
    lex.startStyling = Mock()
    lex.setStyling = Mock()
    return lex


class TestCelLexerBaseline:
    """Baseline tests for CEL Lexer before refactoring."""

    def test_lexer_initialization(self, lexer):
        """Test lexer initializes correctly."""
        assert lexer is not None
        assert hasattr(lexer, 'KEYWORDS')
        assert hasattr(lexer, 'OPERATORS')
        assert hasattr(lexer, 'ALL_FUNCTIONS')

    def test_style_text_keywords(self, lexer, mock_editor):
        """Test styling of keywords."""
        test_text = "true false null"
        mock_editor.text.return_value = test_text

        lexer.styleText(0, len(test_text))

        # Verify startStyling was called
        lexer.startStyling.assert_called_once_with(0)

        # Verify setStyling was called (at least for keywords)
        assert lexer.setStyling.call_count > 0

    def test_style_text_operators(self, lexer, mock_editor):
        """Test styling of operators."""
        test_text = "x == 5 && y != 3"
        mock_editor.text.return_value = test_text

        lexer.styleText(0, len(test_text))

        lexer.startStyling.assert_called_once_with(0)
        assert lexer.setStyling.call_count > 0

    def test_style_text_strings(self, lexer, mock_editor):
        """Test styling of string literals."""
        test_text = '"hello" and \'world\''
        mock_editor.text.return_value = test_text

        lexer.styleText(0, len(test_text))

        lexer.startStyling.assert_called_once_with(0)
        assert lexer.setStyling.call_count > 0

    def test_style_text_numbers(self, lexer, mock_editor):
        """Test styling of numbers."""
        test_text = "42 3.14 0.5"
        mock_editor.text.return_value = test_text

        lexer.styleText(0, len(test_text))

        lexer.startStyling.assert_called_once_with(0)
        assert lexer.setStyling.call_count > 0

    def test_style_text_comments(self, lexer, mock_editor):
        """Test styling of comments."""
        test_text = "// This is a comment\nx = 5"
        mock_editor.text.return_value = test_text

        lexer.styleText(0, len(test_text))

        lexer.startStyling.assert_called_once_with(0)
        assert lexer.setStyling.call_count > 0

    def test_style_text_functions(self, lexer, mock_editor):
        """Test styling of function names."""
        test_text = "abs(x) max(y, z)"
        mock_editor.text.return_value = test_text

        lexer.styleText(0, len(test_text))

        lexer.startStyling.assert_called_once_with(0)
        assert lexer.setStyling.call_count > 0

    def test_style_text_indicators(self, lexer, mock_editor):
        """Test styling of indicators (e.g., rsi14.value)."""
        test_text = "rsi14.value > 70"
        mock_editor.text.return_value = test_text

        lexer.styleText(0, len(test_text))

        lexer.startStyling.assert_called_once_with(0)
        assert lexer.setStyling.call_count > 0

    def test_style_text_variables(self, lexer, mock_editor):
        """Test styling of variables (trade., cfg.)."""
        test_text = "trade.direction == 'long'"
        mock_editor.text.return_value = test_text

        lexer.styleText(0, len(test_text))

        lexer.startStyling.assert_called_once_with(0)
        assert lexer.setStyling.call_count > 0

    def test_style_text_complex_expression(self, lexer, mock_editor):
        """Test styling of complex CEL expression."""
        test_text = """// Check bullish condition
rsi14.value < 30 &&
macd.histogram > 0 &&
trade.direction == 'long'
"""
        mock_editor.text.return_value = test_text

        lexer.styleText(0, len(test_text))

        lexer.startStyling.assert_called_once_with(0)
        assert lexer.setStyling.call_count > 0

    def test_style_text_no_editor(self, lexer):
        """Test styleText handles missing editor gracefully."""
        lexer.editor = Mock(return_value=None)

        # Should not raise exception
        lexer.styleText(0, 10)

    def test_default_colors(self, lexer):
        """Test default color scheme."""
        assert lexer.defaultColor(lexer.DEFAULT) == QColor("#d4d4d4")
        assert lexer.defaultColor(lexer.KEYWORD) == QColor("#569cd6")
        assert lexer.defaultColor(lexer.STRING) == QColor("#ce9178")
        assert lexer.defaultColor(lexer.COMMENT) == QColor("#6a9955")
        assert lexer.defaultColor(lexer.NUMBER) == QColor("#b5cea8")

    def test_descriptions(self, lexer):
        """Test style descriptions."""
        assert lexer.description(lexer.DEFAULT) == "Default"
        assert lexer.description(lexer.KEYWORD) == "Keyword"
        assert lexer.description(lexer.OPERATOR) == "Operator"
        assert lexer.description(lexer.STRING) == "String"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
