"""
Create sub-mixins for BotUISignalsMixin.

Splits into 4 focused mixins.
"""

from pathlib import Path
from typing import List, Any

SOURCE_FILE = Path("src/ui/widgets/chart_window_mixins/bot_ui_signals_mixin_pre_split.py")
TARGET_DIR = Path("src/ui/widgets/chart_window_mixins")

# Mixin definitions
MIXINS = {
    'bot_ui_signals_widgets_mixin.py': {
        'class_name': 'BotUISignalsWidgetsMixin',
        'description': 'UI widget creation for signals tab',
        'methods': [
            '_create_signals_tab',
            '_build_bitunix_hedge_widget',
            '_on_bitunix_order_placed',
            '_on_bitunix_position_opened',
            '_on_bitunix_trade_closed',
            '_build_status_widget_fallback',
            '_build_current_position_widget',
            '_build_position_layout',
            '_build_position_left_column',
            '_build_position_right_column',
            '_build_signals_widget',
            '_build_signals_table',
            '_update_leverage_column_visibility',
        ],
    },
    'bot_ui_signals_actions_mixin.py': {
        'class_name': 'BotUISignalsActionsMixin',
        'description': 'Signal and position actions',
        'methods': [
            '_on_clear_selected_signal',
            '_on_clear_all_signals',
            '_on_sell_position_clicked',
            '_update_sell_button_state',
            '_export_signals_to_xlsx',
        ],
    },
    'bot_ui_signals_chart_mixin.py': {
        'class_name': 'BotUISignalsChartMixin',
        'description': 'Chart element drawing',
        'methods': [
            '_on_draw_chart_elements_clicked',
        ],
    },
    'bot_ui_signals_log_mixin.py': {
        'class_name': 'BotUISignalsLogMixin',
        'description': 'Bot log management',
        'methods': [
            '_append_bot_log',
            '_set_bot_run_status_label',
            '_clear_bot_log',
            '_save_bot_log',
            '_build_bot_log_widget',
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

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from PyQt6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QProgressBar, QPushButton, QSplitter, QTableWidget, QVBoxLayout, QWidget,
    QMessageBox, QPlainTextEdit, QFileDialog
)

from .bot_sltp_progressbar import SLTPProgressBar

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

def main():
    """Create all mixins."""
    print("=" * 80)
    print("🔧 CREATING BOT_UI_SIGNALS SUB-MIXINS")
    print("=" * 80)

    if not SOURCE_FILE.exists():
        print(f"❌ Source file not found: {SOURCE_FILE}")
        return

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\n📁 Source: {SOURCE_FILE} ({len(lines)} lines)")

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
        print("2. Test that UI still works")
        print("3. Commit changes")

if __name__ == "__main__":
    main()
