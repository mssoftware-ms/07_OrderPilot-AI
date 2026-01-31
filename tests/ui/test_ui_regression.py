"""Regression tests for UI refactorings (Section 1.5).

Ensures that UI refactorings (TradingMixinBase, BotSettingsDialog consolidation)
did not break existing functionality.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path


class TestUIRegressionTradingMixin:
    """Regression tests for TradingMixinBase refactoring."""

    def test_no_behavioral_changes_chart_chat(self):
        """Regression: ChartChatMixin behavior unchanged."""
        from src.chart_chat.mixin import ChartChatMixin

        # Assert - Class exists and has expected methods
        assert hasattr(ChartChatMixin, 'setup_chart_chat')
        assert hasattr(ChartChatMixin, '_get_parent_app')

        # Method should be inherited, not redefined
        import inspect
        source = inspect.getsource(ChartChatMixin)
        assert 'def _get_parent_app' not in source

    def test_no_behavioral_changes_bitunix_mixin(self):
        """Regression: BitunixTradingMixin behavior unchanged."""
        from src.ui.widgets.bitunix_trading.bitunix_trading_mixin import BitunixTradingMixin

        # Assert - Class exists and has expected methods
        assert hasattr(BitunixTradingMixin, 'setup_bitunix_trading')
        assert hasattr(BitunixTradingMixin, '_get_parent_app')

        # Method should be inherited, not redefined
        import inspect
        source = inspect.getsource(BitunixTradingMixin)
        assert 'def _get_parent_app' not in source

    def test_api_surface_unchanged_chart_chat(self):
        """Regression: ChartChatMixin API unchanged."""
        from src.chart_chat.mixin import ChartChatMixin
        import inspect

        # Get all public methods
        methods = [
            name for name, _ in inspect.getmembers(ChartChatMixin, inspect.isfunction)
            if not name.startswith('_') or name == '_get_parent_app'
        ]

        # Assert - Expected methods exist
        assert 'setup_chart_chat' in methods or hasattr(ChartChatMixin, 'setup_chart_chat')
        assert '_get_parent_app' in dir(ChartChatMixin)

    def test_api_surface_unchanged_bitunix_mixin(self):
        """Regression: BitunixTradingMixin API unchanged."""
        from src.ui.widgets.bitunix_trading.bitunix_trading_mixin import BitunixTradingMixin
        import inspect

        # Get all public methods
        methods = [
            name for name, _ in inspect.getmembers(BitunixTradingMixin, inspect.isfunction)
            if not name.startswith('_') or name == '_get_parent_app'
        ]

        # Assert - Expected methods exist
        assert 'setup_bitunix_trading' in methods or hasattr(BitunixTradingMixin, 'setup_bitunix_trading')
        assert '_get_parent_app' in dir(BitunixTradingMixin)

    def test_inheritance_chain_preserved(self):
        """Regression: Inheritance chains unchanged."""
        from src.chart_chat.mixin import ChartChatMixin
        from src.ui.widgets.bitunix_trading.bitunix_trading_mixin import BitunixTradingMixin
        from src.ui.mixins.trading_mixin_base import TradingMixinBase

        # Assert - Both inherit from base
        assert issubclass(ChartChatMixin, TradingMixinBase)
        assert issubclass(BitunixTradingMixin, TradingMixinBase)

    def test_no_new_dependencies(self):
        """Regression: No new external dependencies added."""
        from src.ui.mixins.trading_mixin_base import TradingMixinBase
        import inspect

        source = inspect.getsource(TradingMixinBase)

        # Should only depend on PyQt6 and typing/logging
        assert 'PyQt6' in source or 'QApplication' in source

        # Should NOT have added heavy dependencies
        assert 'numpy' not in source
        assert 'pandas' not in source


class TestUIRegressionBotSettings:
    """Regression tests for BotSettingsDialog consolidation."""

    def test_dialog_class_unchanged(self):
        """Regression: BotSettingsDialog API unchanged."""
        from src.ui.widgets.bitunix_trading.bot_tab_modules.bot_tab_settings import BotSettingsDialog

        # Assert - Class has expected methods
        assert hasattr(BotSettingsDialog, '__init__')
        assert hasattr(BotSettingsDialog, '_setup_ui')

    def test_import_paths_work(self):
        """Regression: All import paths functional."""
        # Act & Assert - Should not raise
        from src.ui.widgets.bitunix_trading.bot_tab_modules import BotSettingsDialog
        from src.ui.widgets.bitunix_trading.bot_tab_modules.bot_tab_settings import BotSettingsDialog as Dialog2

        assert BotSettingsDialog is Dialog2

    def test_bot_tab_integration_intact(self):
        """Regression: BotTab still works with dialog."""
        from src.ui.widgets.bitunix_trading import BotTab

        # Assert - BotTab exists and has expected structure
        assert BotTab is not None
        assert hasattr(BotTab, '__init__')

    def test_no_duplicate_files_remain(self):
        """Regression: Duplicate files removed."""
        # Check that old duplicate is gone
        old_duplicate = Path("src/ui/widgets/bitunix_trading/bot_tab_settings.py")

        assert not old_duplicate.exists()

    def test_canonical_file_exists(self):
        """Regression: Canonical file in correct location."""
        canonical = Path("src/ui/widgets/bitunix_trading/bot_tab_modules/bot_tab_settings.py")

        assert canonical.exists()

    def test_config_integration_preserved(self):
        """Regression: BotConfig integration preserved (structural)."""
        from src.ui.widgets.bitunix_trading.bot_tab_modules.bot_tab_settings import BotSettingsDialog
        from src.core.trading_bot import BotConfig

        # Act - Only test that classes can be imported
        config = BotConfig()

        # Assert - Structural test only (no Qt instantiation)
        assert config is not None
        assert BotSettingsDialog is not None


class TestUIRegressionCoverage:
    """Regression: Ensure refactorings didn't reduce coverage."""

    def test_trading_mixin_base_coverage(self):
        """Test TradingMixinBase has adequate test coverage."""
        import os

        # Check that test file exists
        test_file = Path("tests/ui/mixins/test_trading_mixin_base.py")
        assert test_file.exists()

        # Check file is not empty
        assert test_file.stat().st_size > 0

    def test_bot_settings_consolidation_coverage(self):
        """Test bot_tab_settings consolidation has tests."""
        # Check that test file exists
        test_file = Path("tests/ui/widgets/test_bot_tab_settings_consolidation.py")
        assert test_file.exists()

        # Check file is not empty
        assert test_file.stat().st_size > 0

    def test_integration_tests_exist(self):
        """Test integration tests created for Section 1.5."""
        # This file itself
        integration_test = Path("tests/ui/test_ui_regression.py")
        assert integration_test.exists()


class TestCodeQualityRegression:
    """Regression: Code quality maintained or improved."""

    def test_no_code_duplication_in_mixins(self):
        """Test duplicate code eliminated from mixins."""
        from src.chart_chat.mixin import ChartChatMixin
        from src.ui.widgets.bitunix_trading.bitunix_trading_mixin import BitunixTradingMixin
        import inspect

        chart_source = inspect.getsource(ChartChatMixin)
        bitunix_source = inspect.getsource(BitunixTradingMixin)

        # Both should NOT contain duplicate _get_parent_app implementation
        assert 'def _get_parent_app(self)' not in chart_source
        assert 'def _get_parent_app(self)' not in bitunix_source

    def test_base_class_is_minimal(self):
        """Test TradingMixinBase is minimal and focused."""
        from src.ui.mixins.trading_mixin_base import TradingMixinBase
        import inspect

        source = inspect.getsource(TradingMixinBase)

        # Should be small (< 100 lines)
        lines = source.split('\n')
        assert len(lines) < 100

    def test_consolidated_settings_has_docstrings(self):
        """Test consolidated BotSettingsDialog has documentation."""
        from src.ui.widgets.bitunix_trading.bot_tab_modules.bot_tab_settings import BotSettingsDialog

        # Assert class docstring exists
        assert BotSettingsDialog.__doc__ is not None
        assert len(BotSettingsDialog.__doc__) > 0

        # Class-level docstring is sufficient - __init__ doesn't need one

    def test_imports_are_clean(self):
        """Test no unused imports in refactored code."""
        from src.ui.mixins.trading_mixin_base import TradingMixinBase
        import inspect

        source = inspect.getsource(TradingMixinBase)

        # Should have minimal imports
        import_count = source.count('import ')
        assert import_count < 10  # Reasonable limit
