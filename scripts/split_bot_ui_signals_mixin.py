"""
Split bot_ui_signals_mixin.py into smaller components.

1. Extract SLTPProgressBar to separate file
2. Split BotUISignalsMixin into 4 sub-mixins
"""

from pathlib import Path

SOURCE_FILE = Path("src/ui/widgets/chart_window_mixins/bot_ui_signals_mixin_pre_split.py")
TARGET_DIR = Path("src/ui/widgets/chart_window_mixins")

def extract_sltp_progressbar():
    """Extract SLTPProgressBar class to separate file."""
    print("\n📝 Extracting SLTPProgressBar...")

    with open(SOURCE_FILE, 'r') as f:
        lines = f.readlines()

    # Find class boundaries
    class_start = None
    class_end = None

    for i, line in enumerate(lines):
        if 'class SLTPProgressBar(QProgressBar):' in line:
            class_start = i
        elif class_start and 'class BotUISignalsMixin:' in line:
            class_end = i
            break

    if not class_start or not class_end:
        print("❌ Could not find SLTPProgressBar class boundaries")
        return False

    # Build content
    content = """from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from PyQt6.QtWidgets import QProgressBar


"""
    content += ''.join(lines[class_start:class_end])

    # Write file
    target_path = TARGET_DIR / 'bot_sltp_progressbar.py'
    with open(target_path, 'w') as f:
        f.write(content)

    productive_loc = len([l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')])
    print(f"   ✅ bot_sltp_progressbar.py created ({productive_loc} productive LOC)")
    return True

def create_main_mixin():
    """Create new main mixin file that imports sub-mixins and SLTPProgressBar."""
    print("\n📝 Creating new bot_ui_signals_mixin.py...")

    content = """from __future__ import annotations

import logging

from .bot_sltp_progressbar import SLTPProgressBar
from .bot_ui_signals_widgets_mixin import BotUISignalsWidgetsMixin
from .bot_ui_signals_actions_mixin import BotUISignalsActionsMixin
from .bot_ui_signals_chart_mixin import BotUISignalsChartMixin
from .bot_ui_signals_log_mixin import BotUISignalsLogMixin

logger = logging.getLogger(__name__)


class BotUISignalsMixin(
    BotUISignalsWidgetsMixin,
    BotUISignalsActionsMixin,
    BotUISignalsChartMixin,
    BotUISignalsLogMixin,
):
    \"\"\"Bot UI Signals Tab - Uses sub-mixin pattern for better modularity.

    Coordinates signal display and position management by combining:
    - Widgets: UI creation (signals table, position info, status)
    - Actions: Signal and position actions (clear, sell)
    - Chart: Chart element drawing
    - Log: Bot log management and export

    Also exports SLTPProgressBar for convenience.
    \"\"\"
    pass


# Re-export for backward compatibility
__all__ = ['BotUISignalsMixin', 'SLTPProgressBar']
"""

    target_path = TARGET_DIR / 'bot_ui_signals_mixin.py'
    with open(target_path, 'w') as f:
        f.write(content)

    print(f"   ✅ bot_ui_signals_mixin.py created (35 LOC)")
    return True

def main():
    """Execute the split."""
    print("=" * 80)
    print("🔧 SPLITTING BOT_UI_SIGNALS_MIXIN.PY")
    print("=" * 80)

    if not SOURCE_FILE.exists():
        print(f"❌ Source file not found: {SOURCE_FILE}")
        return

    # Extract SLTPProgressBar
    if not extract_sltp_progressbar():
        return

    # Create new main mixin
    if not create_main_mixin():
        return

    print("\n" + "=" * 80)
    print("✅ SPLIT COMPLETE (partial)")
    print("=" * 80)
    print("\n📋 NEXT STEPS:")
    print("1. Run create_bot_ui_signals_submixins.py to create the 4 sub-mixins")
    print("2. Validate all files")
    print("3. Commit")

if __name__ == "__main__":
    main()
