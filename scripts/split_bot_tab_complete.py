"""
Complete automatic splitter for bot_tab.py BotTab class.

Splits BotTab class (123-2168) into 5 modules based on method categories.
"""

import ast
import os
import py_compile
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Source file
SOURCE_FILE = Path("src/ui/widgets/bitunix_trading/bot_tab.py")
TARGET_DIR = Path("src/ui/widgets/bitunix_trading/bot_tab_modules")

def extract_methods_from_class(filepath: Path, class_name: str) -> List[Dict[str, Any]]:
    """Extract all methods from a specific class."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    tree = ast.parse(content, str(filepath))

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append({
                        'name': item.name,
                        'lineno': item.lineno,
                        'end_lineno': item.end_lineno or item.lineno
                    })
            return methods

    return []

def categorize_methods(methods: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Categorize methods by their purpose."""
    categories = {
        'ui': [],        # UI creation methods
        'controls': [],  # Bot control methods
        'monitoring': [],# Position/P&L monitoring
        'logs': [],      # Logging methods
        'main': []       # Main coordination (__init__, etc.)
    }

    for m in methods:
        name = m['name']

        # Main coordination
        if name in ['__init__']:
            categories['main'].append(m)
        # UI creation
        elif any(x in name for x in ['_setup_ui', '_create_', '_setup_signals', '_setup_timers']):
            categories['ui'].append(m)
        # Controls
        elif any(x in name.lower() for x in ['start', 'stop', 'pause', 'resume', 'toggle', 'handle', 'clicked', 'apply', 'settings']):
            categories['controls'].append(m)
        # Monitoring
        elif any(x in name.lower() for x in ['monitor', 'update', 'position', 'pnl', 'display', 'status', 'sltp', '_get_position', '_get_pnl']):
            categories['monitoring'].append(m)
        # Logs
        elif any(x in name.lower() for x in ['log', 'history', 'trade', 'signal_received', 'error', 'order', 'journal']):
            categories['logs'].append(m)
        # Default to monitoring
        else:
            categories['monitoring'].append(m)

    return categories

def print_categorization(categories: Dict[str, List[Dict[str, Any]]]):
    """Print method categorization for review."""
    print("\n" + "=" * 80)
    print("📋 METHOD CATEGORIZATION")
    print("=" * 80)

    for cat_name, methods in categories.items():
        if methods:
            print(f"\n{cat_name.upper()}: {len(methods)} methods")
            for m in sorted(methods, key=lambda x: x['lineno']):
                print(f"  - {m['name']:40} (lines {m['lineno']:4}-{m['end_lineno']:4})")

    print("\n" + "=" * 80)

def extract_lines(filepath: Path, start: int, end: int) -> List[str]:
    """Extract lines from file (1-indexed)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return lines[start-1:end]

def get_common_imports() -> List[str]:
    """Get common imports needed by all modules."""
    return [
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
        '    QSpinBox,',
        '    QDoubleSpinBox,',
        '    QCheckBox,',
        '    QComboBox,',
        '    QDialog,',
        '    QDialogButtonBox,',
        '    QFormLayout,',
        '    QMessageBox,',
        '    QFrame,',
        '    QProgressBar,',
        '    QSplitter,',
        '    QHeaderView,',
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
        '    MarketContextBuilder,',
        '    MarketContextBuilderConfig,',
        '    RegimeDetectorService,',
        '    RegimeConfig,',
        '    LevelEngine,',
        '    LevelEngineConfig,',
        '    EntryScoreEngine,',
        '    EntryScoreConfig,',
        '    LLMValidationService,',
        '    LLMValidationConfig,',
        '    TriggerExitEngine,',
        '    TriggerExitConfig,',
        '    LeverageRulesEngine,',
        '    LeverageRulesConfig,',
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
        'BOT_SETTINGS_FILE = Path("config/bot_settings.json")',
        '',
    ]

def main():
    """Run the complete analysis."""
    print("=" * 80)
    print("🔧 BOT_TAB.PY COMPLETE ANALYSIS")
    print("=" * 80)

    if not SOURCE_FILE.exists():
        print(f"❌ Source file not found: {SOURCE_FILE}")
        return

    # Extract BotTab methods
    methods = extract_methods_from_class(SOURCE_FILE, 'BotTab')
    print(f"\n✅ Found {len(methods)} methods in BotTab class")

    # Categorize methods
    categories = categorize_methods(methods)
    print_categorization(categories)

    # Calculate LOC per category
    print("\n" + "=" * 80)
    print("📊 LOC DISTRIBUTION")
    print("=" * 80)

    for cat_name, methods in categories.items():
        if methods:
            total_loc = sum(m['end_lineno'] - m['lineno'] + 1 for m in methods)
            print(f"{cat_name.upper():15} {len(methods):3} methods, ~{total_loc:4} LOC")

    print("\n" + "=" * 80)
    print("⚠️  NOTE: This is ANALYSIS ONLY")
    print("    Next step: Create splitting script based on this categorization")
    print("=" * 80)

if __name__ == "__main__":
    main()
