"""
Create mixins for backtest_tab.py based on method categorization.

Splits BacktestTab class into 7 mixins for better modularity.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any

SOURCE_FILE = Path("src/ui/widgets/bitunix_trading/backtest_tab.py")
TARGET_DIR = Path("src/ui/widgets/bitunix_trading")

# Mixin definitions based on analysis
MIXINS = {
    'backtest_tab_ui_setup_mixin.py': {
        'class_name': 'BacktestTabUISetupMixin',
        'description': 'UI creation for Setup and Execution tabs',
        'methods': [
            '_setup_ui',
            '_create_compact_button_row',
            '_create_setup_tab',
            '_create_execution_tab',
            '_create_kpi_card',
        ],
    },
    'backtest_tab_ui_results_mixin.py': {
        'class_name': 'BacktestTabUIResultsMixin',
        'description': 'UI creation and updates for Results tab',
        'methods': [
            '_create_results_tab',
            '_update_metrics_table',
            '_update_trades_table',
            '_update_breakdown_table',
        ],
    },
    'backtest_tab_ui_batch_mixin.py': {
        'class_name': 'BacktestTabUIBatchMixin',
        'description': 'UI creation and updates for Batch tab',
        'methods': [
            '_create_batch_tab',
            '_update_batch_results_table',
            '_update_wf_results_table',
        ],
    },
    'backtest_tab_callbacks_mixin.py': {
        'class_name': 'BacktestTabCallbacksMixin',
        'description': 'Button click callbacks and handlers',
        'methods': [
            '_on_backtest_btn_clicked',
            '_on_batch_btn_clicked',
            '_on_wf_btn_clicked',
            '_on_save_template_clicked',
            '_on_load_template_clicked',
            '_on_derive_variant_clicked',
            '_on_auto_generate_clicked',
            '_on_load_configs_clicked',
            '_on_indicator_set_changed',
        ],
    },
    'backtest_tab_config_mixin.py': {
        'class_name': 'BacktestTabConfigMixin',
        'description': 'Configuration management and parameter handling',
        'methods': [
            'collect_engine_configs',
            '_get_default_engine_configs',
            '_build_backtest_config',
            '_build_entry_config',
            'get_parameter_specification',
            'get_parameter_space_from_configs',
            '_convert_v2_to_parameters',
            '_get_nested_value',
        ],
    },
    'backtest_tab_update_mixin.py': {
        'class_name': 'BacktestTabUpdateMixin',
        'description': 'UI update methods and progress tracking',
        'methods': [
            '_on_progress_updated',
            '_on_log_message',
            '_log',
        ],
    },
    'backtest_tab_export_mixin.py': {
        'class_name': 'BacktestTabExportMixin',
        'description': 'Export functions (CSV, JSON, batch results)',
        'methods': [
            '_export_csv',
            '_export_equity_csv',
            '_export_json',
            '_export_batch_results',
            '_export_variants_json',
        ],
    },
}

def extract_method(lines: List[str], method_name: str, start_line: int) -> tuple[int, int] | None:
    """Find method start and end lines."""
    # Find method start
    method_start = None
    for i in range(start_line - 1, len(lines)):
        if f'def {method_name}(' in lines[i]:
            method_start = i + 1  # 1-indexed
            break

    if not method_start:
        return None

    # Find method end (next method or class end)
    indent_level = len(lines[method_start - 1]) - len(lines[method_start - 1].lstrip())
    method_end = None

    for i in range(method_start, len(lines)):
        line = lines[i]
        if line.strip() and not line.strip().startswith('#'):
            current_indent = len(line) - len(line.lstrip())
            # Check if we hit next method at same indent level
            if current_indent == indent_level and line.strip().startswith('def '):
                method_end = i  # 1-indexed
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

def create_mixin(filename: str, config: Dict[str, Any], source_lines: List[str]) -> bool:
    """Create a single mixin file."""
    print(f"\n📝 Creating {filename}...")

    # Extract all methods
    all_method_lines = []
    for method_name in config['methods']:
        result = extract_method(source_lines, method_name, 1)
        if result:
            start, end = result
            all_method_lines.extend(source_lines[start-1:end-1])
        else:
            print(f"   ⚠️  Method {method_name} not found, skipping...")

    if not all_method_lines:
        print(f"   ❌ No methods found for {filename}")
        return False

    # Build content
    content = get_common_imports()
    content += f'\nclass {config["class_name"]}:\n'
    content += f'    """{config["description"]}"""\n\n'

    # Add methods
    for line in all_method_lines:
        content += line

    # Write file
    target_path = TARGET_DIR / filename
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Count LOC
    productive_loc = len([l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')])
    total_loc = len(content.split('\n'))

    print(f"   ✅ {total_loc} total LOC, {productive_loc} productive LOC")
    print(f"   🔧 {len(config['methods'])} methods included")

    return True

def main():
    """Create all mixins."""
    print("=" * 80)
    print("🔧 CREATING BACKTEST_TAB MIXINS")
    print("=" * 80)

    if not SOURCE_FILE.exists():
        print(f"❌ Source file not found: {SOURCE_FILE}")
        return

    # Read source file
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\n📁 Source: {SOURCE_FILE} ({len(lines)} lines)")

    # Create all mixins
    success_count = 0
    for filename, config in MIXINS.items():
        if create_mixin(filename, config, lines):
            success_count += 1

    print("\n" + "=" * 80)
    print(f"✅ MIXINS CREATED: {success_count}/{len(MIXINS)}")
    print("=" * 80)

    if success_count == len(MIXINS):
        print("\n📋 NEXT STEPS:")
        print("1. Validate syntax of all mixins")
        print("2. Create new backtest_tab.py that inherits from all mixins")
        print("3. Test that UI still works")
        print("4. Commit changes")

if __name__ == "__main__":
    main()
