"""
Create sub-mixins for bot_callbacks_signal_mixin.py.

Splits into 3 focused mixins.
"""

from pathlib import Path
from typing import List, Any

SOURCE_FILE = Path("src/ui/widgets/chart_window_mixins/bot_callbacks_signal_mixin_pre_split.py")
TARGET_DIR = Path("src/ui/widgets/chart_window_mixins")

# Mixin definitions
MIXINS = {
    'bot_callbacks_signal_handling_mixin.py': {
        'class_name': 'BotCallbacksSignalHandlingMixin',
        'description': 'Signal callback handling and tracking',
        'methods': [
            '_on_bot_signal',
            '_on_bot_signal_update',
            '_on_bot_signal_cleared',
            '_add_confirmed_signal',
            '_update_candidate_to_confirmed',
            '_update_or_add_candidate',
            '_draw_chart_for_confirmed_signal',
            '_on_bot_exit_signal',
            '_update_sl_tp_and_progressbar',
            '_clear_signal_row',
            '_clear_candidate_row',
        ],
    },
    'bot_callbacks_position_lifecycle_mixin.py': {
        'class_name': 'BotCallbacksPositionLifecycleMixin',
        'description': 'Position lifecycle callbacks (enter, exit, adjust)',
        'methods': [
            '_handle_bot_enter',
            '_handle_bot_adjust_stop',
            '_handle_bot_exit',
            '_on_hedge_close_signal',
            '_should_block_rsi_exit',
            '_should_block_tp_exit',
            '_should_block_adx_exit',
            '_should_block_volume_exit',
            '_visualize_position_on_chart',
        ],
    },
    'bot_callbacks_signal_utils_mixin.py': {
        'class_name': 'BotCallbacksSignalUtilsMixin',
        'description': 'Signal utilities and helpers',
        'methods': [
            '_find_signal_row',
            '_find_candidate_row',
            '_format_signal_time',
            '_format_signal_side',
            '_format_price',
            '_format_percentage',
            '_format_pnl',
            '_apply_pnl_color',
            '_get_signal_icon',
            '_get_strategy_details',
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

import logging
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QTableWidgetItem

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
    print("\n📝 Creating new bot_callbacks_signal_mixin.py...")

    content = '''from __future__ import annotations

import logging

from .bot_callbacks_signal_handling_mixin import BotCallbacksSignalHandlingMixin
from .bot_callbacks_position_lifecycle_mixin import BotCallbacksPositionLifecycleMixin
from .bot_callbacks_signal_utils_mixin import BotCallbacksSignalUtilsMixin

logger = logging.getLogger(__name__)


class BotCallbacksSignalMixin(
    BotCallbacksSignalHandlingMixin,
    BotCallbacksPositionLifecycleMixin,
    BotCallbacksSignalUtilsMixin,
):
    """Bot Callbacks Signal Mixin - Uses sub-mixin pattern for better modularity.

    Coordinates bot signal callbacks by combining:
    - Signal Handling: Signal callbacks and tracking
    - Position Lifecycle: Enter, exit, adjust callbacks
    - Signal Utils: Formatting and helper functions
    """
    pass
'''

    target_path = TARGET_DIR / 'bot_callbacks_signal_mixin.py'
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"   ✅ bot_callbacks_signal_mixin.py created (25 LOC)")
    return True

def main():
    """Create all mixins."""
    print("=" * 80)
    print("🔧 CREATING BOT_CALLBACKS_SIGNAL SUB-MIXINS")
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

    # Create new main mixin
    if create_main_mixin():
        success_count += 1

    print("\n" + "=" * 80)
    print(f"✅ FILES CREATED: {success_count}/{len(MIXINS) + 1}")
    print("=" * 80)

    print("\n📋 NEXT STEPS:")
    print("1. Validate syntax of all mixins")
    print("2. Test that bot still works")
    print("3. Commit changes")

if __name__ == "__main__":
    main()
