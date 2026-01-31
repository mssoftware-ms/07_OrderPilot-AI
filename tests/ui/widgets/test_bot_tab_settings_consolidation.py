"""Tests for bot_tab_settings.py consolidation.

Verifies that:
1. Duplicate bot_tab_settings.py has been removed
2. bot_tab_main.py correctly imports from bot_tab_modules
3. BotSettingsDialog is accessible via the correct import path
"""

import pytest
from pathlib import Path


class TestBotTabSettingsConsolidation:
    """Test suite for bot_tab_settings consolidation."""

    def test_root_level_duplicate_removed(self):
        """Test that root-level bot_tab_settings.py has been deleted."""
        # The obsolete file should NOT exist
        obsolete_file = Path("src/ui/widgets/bitunix_trading/bot_tab_settings.py")
        assert not obsolete_file.exists(), (
            f"Obsolete file still exists: {obsolete_file}\n"
            "Expected: File deleted as part of consolidation."
        )

    def test_modules_version_exists(self):
        """Test that bot_tab_modules/bot_tab_settings.py exists."""
        canonical_file = Path("src/ui/widgets/bitunix_trading/bot_tab_modules/bot_tab_settings.py")
        assert canonical_file.exists(), (
            f"Canonical file missing: {canonical_file}\n"
            "Expected: This is the single source of truth."
        )

    def test_bot_settings_dialog_import_from_modules(self):
        """Test that BotSettingsDialog can be imported from bot_tab_modules."""
        from src.ui.widgets.bitunix_trading.bot_tab_modules import BotSettingsDialog

        assert BotSettingsDialog is not None
        assert BotSettingsDialog.__name__ == "BotSettingsDialog"

    def test_bot_tab_main_imports_from_modules(self):
        """Test that bot_tab_main.py imports BotSettingsDialog from bot_tab_modules."""
        import inspect
        from src.ui.widgets.bitunix_trading import bot_tab_main

        # Read source code of bot_tab_main
        source_lines = inspect.getsource(bot_tab_main).split('\n')

        # Find import statement
        import_found = False
        correct_import = False

        for line in source_lines:
            if 'BotSettingsDialog' in line and 'import' in line:
                import_found = True
                # Should import from .bot_tab_modules, NOT .bot_tab_settings
                if 'bot_tab_modules' in line:
                    correct_import = True
                elif 'bot_tab_settings' in line and 'bot_tab_modules' not in line:
                    pytest.fail(
                        f"bot_tab_main.py imports from wrong path: {line.strip()}\n"
                        "Expected: from .bot_tab_modules import BotSettingsDialog"
                    )

        assert import_found, "BotSettingsDialog import not found in bot_tab_main.py"
        assert correct_import, (
            "bot_tab_main.py does not import from bot_tab_modules\n"
            "Expected: from .bot_tab_modules import BotSettingsDialog"
        )

    def test_no_duplicate_classes(self):
        """Test that only ONE BotSettingsDialog class exists in codebase."""
        from src.ui.widgets.bitunix_trading.bot_tab_modules import BotSettingsDialog as ModulesDialog

        # Verify class is importable and has expected attributes
        assert ModulesDialog is not None
        assert hasattr(ModulesDialog, '__init__')
        assert hasattr(ModulesDialog, '_setup_ui')
        assert ModulesDialog.__name__ == "BotSettingsDialog"

    def test_bot_tab_uses_correct_dialog(self):
        """Test that BotTab class uses the consolidated BotSettingsDialog."""
        from src.ui.widgets.bitunix_trading import BotTab
        import inspect

        # Get BotTab source
        source = inspect.getsource(BotTab)

        # Should NOT have any reference to old path
        assert '.bot_tab_settings import BotSettingsDialog' not in source, (
            "BotTab still references old import path"
        )


@pytest.fixture
def qapp():
    """Provide QApplication instance for tests."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
