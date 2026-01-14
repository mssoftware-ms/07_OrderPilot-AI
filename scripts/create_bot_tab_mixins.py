"""
Create mixins for bot_tab.py based on method categorization.

This creates 4 mixin classes that BotTab will inherit from.
"""

import ast
from pathlib import Path
from typing import List, Dict, Any

SOURCE_FILE = Path("src/ui/widgets/bitunix_trading/bot_tab.py")
TARGET_DIR = Path("src/ui/widgets/bitunix_trading")

# Mixin definitions based on analysis
MIXINS = {
    'bot_tab_ui_mixin.py': {
        'class_name': 'BotTabUIMixin',
        'description': 'UI creation methods for BotTab',
        'methods': [
            '_setup_ui',
            '_create_header_section',
            '_create_signal_section',
            '_create_position_section',
            '_create_stats_section',
            '_create_separator',
            '_create_log_section',
            '_setup_signals',
            '_setup_timers',
        ],
        'line_ranges': [(203, 699)],
    },
    'bot_tab_controls_mixin.py': {
        'class_name': 'BotTabControlsMixin',
        'description': 'Bot control methods (settings, toggle, apply)',
        'methods': [
            '_handle_settings_click',
            '_on_settings_clicked',
            '_toggle_status_panel',
            '_toggle_journal',
            '_apply_config',
            '_save_settings',
            '_load_settings',
        ],
        'line_ranges': [(795, 840), (844, 857), (906, 915), (1636, 1675)],
    },
    'bot_tab_monitoring_mixin.py': {
        'class_name': 'BotTabMonitoringMixin',
        'description': 'Position monitoring and display methods',
        'methods': [
            '_on_status_panel_refresh',
            '_update_status_panel',
            '_initialize_new_engines',
            'update_engine_configs',
            '_update_sltp_bar',
            '_reset_sltp_bar',
            '_get_current_config',
            '_on_state_changed',
            '_on_signal_updated',
            '_on_position_opened',
            '_on_position_closed',
            '_update_status_display',
            '_update_signal_display',
            '_update_position_display',
            '_update_stats_display',
            '_periodic_update',
            'set_chart_data',
            'clear_chart_data',
            'on_tick_price_updated',
            'cleanup',
            '_save_position_to_file',
            '_restore_saved_position',
        ],
        'line_ranges': [(855, 1131), (1521, 1644), (1679, 1897), (2000, 2168)],
    },
    'bot_tab_logs_mixin.py': {
        'class_name': 'BotTabLogsMixin',
        'description': 'Logging and journal methods',
        'methods': [
            '_log_signal_to_journal',
            '_log_llm_to_journal',
            '_log_error_to_journal',
            '_log_engine_results_to_journal',
            '_on_bot_error',
            '_on_bot_log',
            '_log',
            '_append_log',
            'set_history_manager',
        ],
        'line_ranges': [(920, 963), (1601, 1708), (1971, 1998)],
    },
}

def extract_lines(filepath: Path, start: int, end: int) -> List[str]:
    """Extract lines from file (1-indexed)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return lines[start-1:end]

def get_mixin_header(class_name: str, description: str) -> List[str]:
    """Get mixin class header."""
    return [
        '"""',
        f'{class_name} - {description}',
        '',
        'This mixin is part of the split BotTab implementation.',
        'Contains methods extracted from bot_tab.py for better modularity.',
        '"""',
        '',
        'from __future__ import annotations',
        '',
        'import asyncio',
        'import json',
        'import logging',
        'from datetime import datetime, timezone',
        'from decimal import Decimal',
        'from pathlib import Path',
        'from typing import TYPE_CHECKING',
        '',
        'import qasync',
        'from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot',
        'from PyQt6.QtGui import QColor, QTextCursor',
        'from PyQt6.QtWidgets import (',
        '    QWidget,',
        '    QVBoxLayout,',
        '    QHBoxLayout,',
        '    QLabel,',
        '    QPushButton,',
        '    QGroupBox,',
        '    QTableWidget,',
        '    QTableWidgetItem,',
        '    QTextEdit,',
        '    QFrame,',
        '    QProgressBar,',
        '    QSplitter,',
        '    QHeaderView,',
        '    QMessageBox,',
        ')',
        '',
        'if TYPE_CHECKING:',
        '    from src.core.broker.bitunix_paper_adapter import BitunixPaperAdapter',
        '    from src.core.market_data.history_provider import HistoryManager',
        '',
        'from src.core.trading_bot import (',
        '    BotState,',
        '    BotConfig,',
        '    BotStatistics,',
        '    SignalDirection,',
        '    TradeSignal,',
        '    MonitoredPosition,',
        '    ExitResult,',
        '    TradeLogEntry,',
        '    MarketContext,',
        '    RegimeType,',
        ')',
        '',
        'try:',
        '    from src.ui.widgets.trading_status_panel import TradingStatusPanel',
        '    HAS_STATUS_PANEL = True',
        'except ImportError:',
        '    HAS_STATUS_PANEL = False',
        '',
        'try:',
        '    from src.ui.widgets.trading_journal_widget import TradingJournalWidget',
        '    HAS_JOURNAL = True',
        'except ImportError:',
        '    HAS_JOURNAL = False',
        '',
        'logger = logging.getLogger(__name__)',
        '',
        'BOT_SETTINGS_FILE = Path("config/bot_settings.json")',
        '',
        '',
        f'class {class_name}:',
        f'    """{description}"""',
        '',
    ]

def create_mixin(filename: str, config: Dict[str, Any], source_file: Path, target_dir: Path) -> bool:
    """Create a single mixin file."""
    print(f"\n📝 Creating {filename}...")

    # Collect method bodies from all line ranges
    method_lines = []
    for start, end in config['line_ranges']:
        method_lines.extend(extract_lines(source_file, start, end))

    # Build content
    content = get_mixin_header(config['class_name'], config['description'])

    # Add method bodies (with proper indentation)
    for line in method_lines:
        # Ensure proper class-level indentation
        if line.strip() and not line.startswith('    '):
            content.append('    ' + line.rstrip())
        else:
            content.append(line.rstrip())

    # Write file
    target_path = target_dir / filename
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

    # Count lines
    productive_loc = len([l for l in content if l.strip() and not l.strip().startswith('#')])
    total_loc = len(content)

    print(f"✅ {filename} created")
    print(f"   📊 {total_loc} total LOC, {productive_loc} productive LOC")
    print(f"   🔧 {len(config['methods'])} methods: {', '.join(config['methods'][:3])}...")

    return True

def main():
    """Create all mixins."""
    print("=" * 80)
    print("🔧 CREATING BOT_TAB MIXINS")
    print("=" * 80)

    if not SOURCE_FILE.exists():
        print(f"❌ Source file not found: {SOURCE_FILE}")
        return

    # Create all mixins
    success_count = 0
    for filename, config in MIXINS.items():
        if create_mixin(filename, config, SOURCE_FILE, TARGET_DIR):
            success_count += 1

    print("\n" + "=" * 80)
    print(f"✅ MIXINS CREATED: {success_count}/{len(MIXINS)}")
    print("=" * 80)

    print("\n📋 NEXT STEPS:")
    print("1. Review generated mixin files")
    print("2. Update bot_tab.py to inherit from mixins")
    print("3. Test that all methods still work")
    print("4. Validate syntax")
    print("5. Commit changes")

if __name__ == "__main__":
    main()
