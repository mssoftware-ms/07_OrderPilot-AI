"""
Create sub-mixins for backtest_tab_callbacks_mixin.py.

Splits into 3 focused mixins by functional area.
"""

from pathlib import Path
from typing import List, Any

SOURCE_FILE = Path("src/ui/widgets/bitunix_trading/backtest_tab_callbacks_mixin.py")
TARGET_DIR = Path("src/ui/widgets/bitunix_trading")

# Mixin definitions
MIXINS = {
    'backtest_callbacks_testing_mixin.py': {
        'class_name': 'BacktestCallbacksTestingMixin',
        'description': 'Backtest and optimization testing callbacks',
        'methods': [
            '_on_batch_btn_clicked',
            '_on_wf_btn_clicked',
        ],
    },
    'backtest_callbacks_template_mixin.py': {
        'class_name': 'BacktestCallbacksTemplateMixin',
        'description': 'Template management callbacks',
        'methods': [
            '_on_save_template_clicked',
            '_on_load_template_clicked',
            '_on_derive_variant_clicked',
        ],
    },
    'backtest_callbacks_config_mixin.py': {
        'class_name': 'BacktestCallbacksConfigMixin',
        'description': 'Configuration management callbacks',
        'methods': [
            '_on_auto_generate_clicked',
            '_on_load_configs_clicked',
            '_on_indicator_set_changed',
        ],
    },
}

def extract_method(lines: List[str], method_name: str, start_line: int) -> tuple[int, int] | None:
    """Find method start and end lines."""
    method_start = None
    for i in range(start_line - 1, len(lines)):
        if f'def {method_name}(' in lines[i]:
            method_start = i + 1
            break

    if not method_start:
        return None

    indent_level = len(lines[method_start - 1]) - len(lines[method_start - 1].lstrip())
    method_end = None

    for i in range(method_start, len(lines)):
        line = lines[i]
        if line.strip() and not line.strip().startswith('#'):
            current_indent = len(line) - len(line.lstrip())
            if current_indent == indent_level and line.strip().startswith('def '):
                method_end = i
                break

    if not method_end:
        method_end = len(lines)

    return (method_start, method_end)

def get_common_imports() -> str:
    """Get common imports for all mixins."""
    return '''from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QMessageBox, QFileDialog, QProgressBar, QTabWidget, QLineEdit,
    QHeaderView,
)

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)

'''

def create_mixin(filename: str, config: dict[str, Any], source_lines: List[str]) -> bool:
    """Create a single mixin file."""
    print(f"\n📝 Creating {filename}...")

    all_method_lines = []
    for method_name in config['methods']:
        result = extract_method(source_lines, method_name, 1)
        if result:
            start, end = result
            all_method_lines.extend(source_lines[start-1:end-1])
            all_method_lines.append('\n')
        else:
            print(f"   ⚠️  Method {method_name} not found, skipping...")

    if not all_method_lines:
        print(f"   ❌ No methods found for {filename}")
        return False

    content = get_common_imports()
    content += f'class {config["class_name"]}:\n'
    content += f'    """{config["description"]}"""\n\n'

    for line in all_method_lines:
        content += line

    target_path = TARGET_DIR / filename
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)

    productive_loc = len([l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')])
    total_loc = len(content.split('\n'))

    print(f"   ✅ {total_loc} total LOC, {productive_loc} productive LOC")
    print(f"   🔧 {len(config['methods'])} methods included")

    return True

def create_main_mixin():
    """Create new main mixin file."""
    print("\n📝 Creating new backtest_tab_callbacks_mixin.py...")

    content = '''from __future__ import annotations

import logging

from .backtest_callbacks_testing_mixin import BacktestCallbacksTestingMixin
from .backtest_callbacks_template_mixin import BacktestCallbacksTemplateMixin
from .backtest_callbacks_config_mixin import BacktestCallbacksConfigMixin

logger = logging.getLogger(__name__)


class BacktestTabCallbacksMixin(
    BacktestCallbacksTestingMixin,
    BacktestCallbacksTemplateMixin,
    BacktestCallbacksConfigMixin,
):
    """Backtest Tab Callbacks - Uses sub-mixin pattern for better modularity.

    Coordinates backtest callbacks by combining:
    - Testing: Batch and walk-forward testing callbacks
    - Template: Template saving, loading, and derivation
    - Config: Configuration management and auto-generation
    """
    pass
'''

    target_path = TARGET_DIR / 'backtest_tab_callbacks_mixin.py'
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"   ✅ backtest_tab_callbacks_mixin.py created (27 LOC)")
    return True

def main():
    """Create all mixins."""
    print("=" * 80)
    print("🔧 CREATING BACKTEST_TAB_CALLBACKS SUB-MIXINS")
    print("=" * 80)

    if not SOURCE_FILE.exists():
        print(f"❌ Source file not found: {SOURCE_FILE}")
        return

    # Create backup first
    backup_path = TARGET_DIR / 'backtest_tab_callbacks_mixin_pre_split.py'
    with open(SOURCE_FILE, 'r', encoding='utf-8') as src:
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    print(f"✅ Backup created: {backup_path}")

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\n📁 Source: {SOURCE_FILE} ({len(lines)} lines)")

    success_count = 0
    for filename, config in MIXINS.items():
        if create_mixin(filename, config, lines):
            success_count += 1

    # Create new main mixin
    if create_main_mixin():
        success_count += 1

    print("\n" + "=" * 80)
    print(f"✅ FILES CREATED: {success_count}/{len(MIXINS) + 1}")
    print("=" * 80)

    print("\n📋 NEXT STEPS:")
    print("1. Validate syntax of all mixins")
    print("2. Test that backtest tab still works")
    print("3. Commit changes")

if __name__ == "__main__":
    main()
