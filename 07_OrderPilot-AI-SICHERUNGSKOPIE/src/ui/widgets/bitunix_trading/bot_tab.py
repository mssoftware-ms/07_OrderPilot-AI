"""
Bot Tab - UI Widget für den Trading Bot

Verwendet die neue Engine-Pipeline (MarketContext → Regime → Levels →
EntryScore → LLM Validation → Trigger/Exit → Leverage) für automatisiertes Trading.

Features:
- Start/Stop Steuerung
- Live Status-Anzeige (State, Signal, Position)
- Statistiken (Trades, Win Rate, PnL)
- Log-Viewer mit Echtzeit-Updates
- Settings Dialog mit 6 Sub-Tabs für Engine-Konfiguration
- Trading Status Panel mit Live Engine-Ergebnissen
- Trading Journal für Audit Trail

Architecture:
- Uses mixin pattern for better modularity (bot_tab_*_mixin.py)
- BotTab inherits from 4 mixins: UI, Controls, Monitoring, Logs
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QFrame,
    QProgressBar,
    QSplitter,
    QHeaderView,
)

if TYPE_CHECKING:
    from src.core.broker.bitunix_paper_adapter import BitunixPaperAdapter
    from src.core.market_data.history_provider import HistoryManager

from src.core.trading_bot import (
    # Core Types (ohne TradingBotEngine - neue Pipeline wird direkt verwendet)
    BotState,
    BotConfig,
    BotStatistics,
    SignalDirection,
    TradeSignal,
    MonitoredPosition,
    ExitResult,
    TradeLogEntry,
    # Phase 1-4: New Engines - Unified Pipeline
    MarketContextBuilder,
    MarketContextBuilderConfig,
    RegimeDetectorService,
    RegimeConfig,
    LevelEngine,
    LevelEngineConfig,
    EntryScoreEngine,
    EntryScoreConfig,
    LLMValidationService,
    LLMValidationConfig,
    TriggerExitEngine,
    TriggerExitConfig,
    LeverageRulesEngine,
    LeverageRulesConfig,
    MarketContext,
    RegimeType,
)

# Phase 5 - Trading Status Panel Integration
try:
    from src.ui.widgets.trading_status_panel import TradingStatusPanel
    HAS_STATUS_PANEL = True
except ImportError:
    HAS_STATUS_PANEL = False

# Phase 5.4 - Trading Journal Integration
try:
    from src.ui.widgets.trading_journal_widget import TradingJournalWidget
    HAS_JOURNAL = True
except ImportError:
    HAS_JOURNAL = False

# Phase 5 - Engine Settings Widgets
try:
    from src.ui.widgets.settings import (
        EntryScoreSettingsWidget,
        TriggerExitSettingsWidget,
        LeverageSettingsWidget,
        LLMValidationSettingsWidget,
        LevelSettingsWidget,
    )
    HAS_ENGINE_SETTINGS = True
except ImportError:
    HAS_ENGINE_SETTINGS = False

# NOTE: WhatsApp Integration wurde in das ChartWindow Trading Bot Panel verschoben
# (siehe panels_mixin.py)

# Import extracted BotSettingsDialog
from .bot_tab_modules import BotSettingsDialog

# Import mixins (split BotTab implementation)
from .bot_tab_ui_mixin import BotTabUIMixin
from .bot_tab_controls_mixin import BotTabControlsMixin
from .bot_tab_monitoring_mixin import BotTabMonitoringMixin
from .bot_tab_logs_mixin import BotTabLogsMixin

logger = logging.getLogger(__name__)

# Pfad für persistente Bot-Einstellungen
BOT_SETTINGS_FILE = Path("config/bot_settings.json")


class BotTab(BotTabUIMixin, BotTabControlsMixin, BotTabMonitoringMixin, BotTabLogsMixin, QWidget):
    """
    Bot Trading Tab - UI für automatischen Trading Bot.

    Uses mixin pattern for better modularity:
    - BotTabUIMixin: UI creation methods (_setup_ui, _create_* methods)
    - BotTabControlsMixin: Control methods (settings, toggle, apply)
    - BotTabMonitoringMixin: Monitoring and display methods (_update_*, _on_*)
    - BotTabLogsMixin: Logging and journal methods (_log_*, set_history_manager)

    Zeigt:
    - Bot Status und Steuerung
    - Aktuelles Signal
    - Offene Position mit SL/TP
    - Tagesstatistiken
    - Live Log
    """

    # Signals für Thread-sichere UI Updates
    status_changed = pyqtSignal(str)  # BotState
    signal_updated = pyqtSignal(object)  # TradeSignal | None
    position_updated = pyqtSignal(object)  # MonitoredPosition | None
    stats_updated = pyqtSignal(object)  # BotStatistics
    log_message = pyqtSignal(str)

    def __init__(
        self,
        paper_adapter: "BitunixPaperAdapter",
        history_manager: "HistoryManager | None" = None,
        parent: QWidget | None = None,
    ):
        """
        Args:
            paper_adapter: Bitunix Paper Adapter (NUR Paper!)
            history_manager: History Manager für Daten
            parent: Parent Widget
        """
        super().__init__(parent)

        self._adapter = paper_adapter
        self._history_manager = history_manager
        # OLD: self._bot_engine removed - using new engine pipeline now
        self._is_initialized = False

        # Phase 1-4: New Engines (initialized on demand)
        self._context_builder: MarketContextBuilder | None = None
        self._regime_detector: RegimeDetectorService | None = None
        self._level_engine: LevelEngine | None = None
        self._entry_score_engine: EntryScoreEngine | None = None
        self._llm_validation: LLMValidationService | None = None
        self._trigger_exit_engine: TriggerExitEngine | None = None
        self._leverage_engine: LeverageRulesEngine | None = None

        # Latest engine results (for Status Panel display)
        self._last_market_context: MarketContext | None = None
        self._last_regime_result = None
        self._last_levels_result = None
        self._last_entry_score = None
        self._last_llm_result = None
        self._last_trigger_result = None
        self._last_leverage_result = None

        # Current open position (managed by new engine pipeline)
        self._current_position: dict | None = None
        self._position_entry_price: float = 0.0
        self._position_side: str = ""  # "long" or "short"
        self._position_quantity: float = 0.0
        self._position_stop_loss: float = 0.0
        self._position_take_profit: float = 0.0

        # Performance: Pipeline nur bei neuen Bars ausführen (Punkt 4)
        self._last_bar_timestamp: int = 0  # Letzter Bar-Timestamp
        self._pipeline_timeframe: str = "1m"  # Einstellbar: "1m", "5m", "15m", etc.

        # Connect history_manager to adapter for market data access
        if history_manager and hasattr(paper_adapter, 'set_history_manager'):
            paper_adapter.set_history_manager(history_manager)
            logger.info("BotTab: Connected HistoryManager to PaperAdapter")

        # Initialize UI (from BotTabUIMixin)
        self._setup_ui()
        self._setup_signals()
        self._setup_timers()
