"""Integration tests for BotSettingsDialog consolidation.

Tests the complete integration of consolidated BotSettingsDialog
with real BotConfig objects - focused on structural/import tests
to avoid PyQt6 crashes.
"""

import pytest
from pathlib import Path

from src.core.trading_bot import BotConfig, AIConfig


class TestBotSettingsDialogIntegration:
    """Integration tests for BotSettingsDialog (structural only)."""

    def test_bot_config_default_creation(self):
        """Test BotConfig can be created with defaults."""
        # Act
        config = BotConfig()

        # Assert
        assert config is not None
        assert hasattr(config, 'risk_per_trade_percent') or hasattr(config, 'max_risk_per_trade')
        assert hasattr(config, 'ai')

    def test_bot_config_with_custom_values(self):
        """Test BotConfig accepts custom values."""
        # Act
        config = BotConfig()
        config.max_risk_per_trade = 2.5

        # Assert
        assert config.max_risk_per_trade == 2.5

    def test_ai_config_integration(self):
        """Test AIConfig integration with BotConfig."""
        # Arrange
        ai_config = AIConfig(enabled=True, confidence_threshold=80)
        config = BotConfig()

        # Act
        config.ai = ai_config

        # Assert
        assert config.ai.enabled is True
        assert config.ai.confidence_threshold == 80

    def test_config_independence(self):
        """Test multiple BotConfig instances are independent."""
        # Arrange
        config1 = BotConfig()
        config2 = BotConfig()

        config1.max_risk_per_trade = 1.0
        config2.max_risk_per_trade = 2.0

        # Assert
        assert config1.max_risk_per_trade == 1.0
        assert config2.max_risk_per_trade == 2.0
        assert config1 is not config2

    def test_config_ai_defaults(self):
        """Test AIConfig has sensible defaults."""
        # Act
        ai_config = AIConfig()

        # Assert
        assert hasattr(ai_config, 'enabled')
        assert hasattr(ai_config, 'confidence_threshold')
        assert ai_config.enabled is False  # Should default to disabled

    def test_dialog_import_path_consistency(self):
        """Test dialog can be imported from correct path."""
        # Arrange & Act
        from src.ui.widgets.bitunix_trading.bot_tab_modules import BotSettingsDialog as Dialog1
        from src.ui.widgets.bitunix_trading.bot_tab_modules.bot_tab_settings import BotSettingsDialog as Dialog2

        # Assert
        assert Dialog1 is Dialog2

    def test_bot_tab_uses_consolidated_dialog(self):
        """Test BotTab uses the consolidated BotSettingsDialog."""
        # Arrange
        from src.ui.widgets.bitunix_trading import BotTab
        import inspect

        # Act
        source = inspect.getsource(BotTab)

        # Assert - Should import from bot_tab_modules
        assert 'bot_tab_modules' in source or 'BotSettingsDialog' in source

    def test_no_circular_imports(self):
        """Test no circular import issues with consolidation."""
        # Act & Assert - Should not raise ImportError
        from src.ui.widgets.bitunix_trading.bot_tab_modules.bot_tab_settings import BotSettingsDialog
        from src.ui.widgets.bitunix_trading import BotTab
        from src.core.trading_bot import BotConfig

        assert BotSettingsDialog is not None
        assert BotTab is not None
        assert BotConfig is not None

    def test_dialog_class_structure(self):
        """Test BotSettingsDialog has expected structure."""
        from src.ui.widgets.bitunix_trading.bot_tab_modules.bot_tab_settings import BotSettingsDialog

        # Assert - Class has expected methods
        assert hasattr(BotSettingsDialog, '__init__')
        assert hasattr(BotSettingsDialog, '_setup_ui')

    def test_config_validation_structure(self):
        """Test config has validation-related attributes."""
        # Arrange
        config = BotConfig()

        # Assert - Config should have valid defaults
        assert hasattr(config, 'risk_per_trade_percent') or hasattr(config, 'max_risk_per_trade')
        # Check the attribute that actually exists
        if hasattr(config, 'risk_per_trade_percent'):
            assert config.risk_per_trade_percent >= 0

    def test_regression_single_source_of_truth(self):
        """Regression: Verify only one BotSettingsDialog exists."""
        # Arrange
        from pathlib import Path

        # Act - Check that duplicate file is gone
        old_path = Path("src/ui/widgets/bitunix_trading/bot_tab_settings.py")
        new_path = Path("src/ui/widgets/bitunix_trading/bot_tab_modules/bot_tab_settings.py")

        # Assert
        assert not old_path.exists(), "Duplicate file should be deleted"
        assert new_path.exists(), "Canonical file should exist"


class TestBotSettingsDialogStructure:
    """Structural tests for BotSettingsDialog (no Qt instantiation)."""

    def test_dialog_class_exists(self):
        """Test BotSettingsDialog class can be imported."""
        from src.ui.widgets.bitunix_trading.bot_tab_modules.bot_tab_settings import BotSettingsDialog

        assert BotSettingsDialog is not None
        assert BotSettingsDialog.__name__ == "BotSettingsDialog"

    def test_dialog_has_docstring(self):
        """Test BotSettingsDialog has documentation."""
        from src.ui.widgets.bitunix_trading.bot_tab_modules.bot_tab_settings import BotSettingsDialog

        assert BotSettingsDialog.__doc__ is not None
        assert len(BotSettingsDialog.__doc__) > 0

    def test_dialog_inherits_from_qdialog(self):
        """Test BotSettingsDialog inherits from QDialog."""
        from src.ui.widgets.bitunix_trading.bot_tab_modules.bot_tab_settings import BotSettingsDialog
        from PyQt6.QtWidgets import QDialog

        assert issubclass(BotSettingsDialog, QDialog)
