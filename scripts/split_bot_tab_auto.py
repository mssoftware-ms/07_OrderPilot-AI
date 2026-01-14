"""
Automatic splitter for bot_tab.py into multiple modules.

Splits BotTab (123-2165) and BotSettingsDialog (2168-2441) classes.
"""

import ast
import os
import py_compile
from pathlib import Path
from typing import List, Dict, Any

# Source file
SOURCE_FILE = Path("src/ui/widgets/bitunix_trading/bot_tab.py")
TARGET_DIR = Path("src/ui/widgets/bitunix_trading/bot_tab_modules")

# Splitting strategy
SPLITS = {
    'bot_tab_settings.py': {
        'description': 'BotSettingsDialog class (standalone)',
        'line_ranges': [(2168, 2441)],
        'imports': [
            'from __future__ import annotations',
            'import logging',
            'from pathlib import Path',
            'from typing import TYPE_CHECKING',
            'from PyQt6.QtCore import Qt',
            'from PyQt6.QtWidgets import (',
            '    QWidget,',
            '    QVBoxLayout,',
            '    QHBoxLayout,',
            '    QLabel,',
            '    QPushButton,',
            '    QGroupBox,',
            '    QDoubleSpinBox,',
            '    QSpinBox,',
            '    QCheckBox,',
            '    QComboBox,',
            '    QDialog,',
            '    QDialogButtonBox,',
            '    QFormLayout,',
            '    QMessageBox,',
            '    QTabWidget,',
            ')',
            '',
            'if TYPE_CHECKING:',
            '    from src.core.broker.bitunix_paper_adapter import BitunixPaperAdapter',
            '',
            'from src.core.trading_bot import (',
            '    BotConfig,',
            '    AIConfig,',
            ')',
            '',
            '# Engine Settings Widgets',
            'try:',
            '    from src.ui.widgets.settings import (',
            '        EntryScoreSettingsWidget,',
            '        TriggerExitSettingsWidget,',
            '        LeverageSettingsWidget,',
            '        LLMValidationSettingsWidget,',
            '        LevelSettingsWidget,',
            '    )',
            '    HAS_ENGINE_SETTINGS = True',
            'except ImportError:',
            '    HAS_ENGINE_SETTINGS = False',
            '',
            'logger = logging.getLogger(__name__)',
            '',
        ],
        'note': 'Standalone settings dialog with 6 tabs'
    }
}

def extract_lines(filepath: Path, start: int, end: int) -> List[str]:
    """Extract lines from file (1-indexed)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return lines[start-1:end]

def create_module(name: str, config: Dict[str, Any], source_file: Path, target_dir: Path) -> bool:
    """Create a single module file."""
    print(f"\n📝 Creating {name}...")

    # Collect lines from all ranges
    all_lines = []
    for start, end in config['line_ranges']:
        all_lines.extend(extract_lines(source_file, start, end))

    # Build content
    content = []

    # Add header
    content.append('"""')
    content.append(f'Bot Tab Module - {config["description"]}')
    content.append('')
    content.append('Extracted from bot_tab.py for better modularity.')
    if 'note' in config:
        content.append(f'Note: {config["note"]}')
    content.append('"""')
    content.append('')

    # Add imports
    if 'imports' in config:
        content.extend(config['imports'])
        content.append('')

    # Add extracted code
    content.extend(line.rstrip() for line in all_lines)

    # Write file
    target_path = target_dir / name
    target_dir.mkdir(parents=True, exist_ok=True)

    with open(target_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

    # Validate syntax
    try:
        py_compile.compile(str(target_path), doraise=True)
        print(f"✅ {name} created successfully (syntax OK)")

        # Count lines
        productive_loc = len([l for l in content if l.strip() and not l.strip().startswith('#')])
        total_loc = len(content)
        print(f"   📊 {total_loc} total LOC, {productive_loc} productive LOC")

        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error in {name}:")
        print(f"   {e}")
        return False

def main():
    """Run the automatic splitting."""
    print("=" * 80)
    print("🔧 AUTOMATIC BOT_TAB.PY SPLITTER")
    print("=" * 80)

    if not SOURCE_FILE.exists():
        print(f"❌ Source file not found: {SOURCE_FILE}")
        return

    print(f"\n📁 Source: {SOURCE_FILE}")
    print(f"📂 Target: {TARGET_DIR}")

    # Create all modules
    success_count = 0
    for module_name, config in SPLITS.items():
        if create_module(module_name, config, SOURCE_FILE, TARGET_DIR):
            success_count += 1

    print("\n" + "=" * 80)
    print(f"✅ SPLITTING COMPLETE: {success_count}/{len(SPLITS)} modules created")
    print("=" * 80)

    if success_count == len(SPLITS):
        print("\n📋 NEXT STEPS:")
        print("1. Review generated files in", TARGET_DIR)
        print("2. Update bot_tab.py imports")
        print("3. Test that BotSettingsDialog still works")
        print("4. Commit changes")
    else:
        print("\n⚠️  Some modules failed. Review errors above.")

if __name__ == "__main__":
    main()
