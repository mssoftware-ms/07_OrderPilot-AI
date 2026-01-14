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

logger = logging.getLogger(__name__)

# Pfad für persistente Bot-Einstellungen
BOT_SETTINGS_FILE = Path("config/bot_settings.json")


class BotTab(QWidget):
    """
    Bot Trading Tab - UI für automatischen Trading Bot.

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

        self._setup_ui()
        self._setup_signals()
        self._setup_timers()

    def _setup_ui(self) -> None:
        """Erstellt das UI Layout."""
        print("DEBUG BotTab: _setup_ui() called")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # --- Header: Bot Status ---
        header = self._create_header_section()
        layout.addWidget(header)
        print(f"DEBUG BotTab: Settings button created, enabled={self.settings_btn.isEnabled()}")

        # --- Phase 5: Trading Status Panel (Engine Results) ---
        if HAS_STATUS_PANEL:
            self._status_panel = TradingStatusPanel()
            self._status_panel.setVisible(False)  # Initial versteckt
            self._status_panel.refresh_requested.connect(self._on_status_panel_refresh)
            layout.addWidget(self._status_panel)
        else:
            self._status_panel = None

        # --- Phase 5.4: Trading Journal ---
        if HAS_JOURNAL:
            self._journal_widget = TradingJournalWidget()
            self._journal_widget.setVisible(False)  # Initial versteckt
            layout.addWidget(self._journal_widget)
        else:
            self._journal_widget = None

        # NOTE: WhatsApp Widget wurde in das ChartWindow Trading Bot Panel verschoben

        # --- Splitter für Signal/Position und Log ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top Section: Signal + Position + Stats
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Signal Section
        top_layout.addWidget(self._create_signal_section())

        # Position Section
        top_layout.addWidget(self._create_position_section())

        # Statistics Section
        top_layout.addWidget(self._create_stats_section())

        splitter.addWidget(top_widget)

        # Bottom Section: Log
        splitter.addWidget(self._create_log_section())
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)

    def _create_header_section(self) -> QWidget:
        """Erstellt Header mit Status und Buttons."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        layout = QHBoxLayout(frame)

        # Bot Icon und Status
        self.status_icon = QLabel("🤖")
        self.status_icon.setStyleSheet("font-size: 24px;")
        layout.addWidget(self.status_icon)

        status_layout = QVBoxLayout()
        self.status_label = QLabel("IDLE")
        self.status_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #888;
        """)
        status_layout.addWidget(self.status_label)

        self.status_detail = QLabel("Bot ist gestoppt")
        self.status_detail.setStyleSheet("color: #666; font-size: 11px;")
        status_layout.addWidget(self.status_detail)
        layout.addLayout(status_layout)

        layout.addStretch()

        # Buttons
        self.start_btn = QPushButton("▶ Start Bot")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.start_btn.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Stop Bot")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        layout.addWidget(self.stop_btn)

        # Phase 5: Toggle für Status Panel
        self.status_panel_btn = QPushButton("📊")
        self.status_panel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:checked { background-color: #1565C0; }
        """)
        self.status_panel_btn.setToolTip("Engine Status Panel ein/ausblenden")
        self.status_panel_btn.setCheckable(True)
        self.status_panel_btn.clicked.connect(self._toggle_status_panel)
        layout.addWidget(self.status_panel_btn)

        # Phase 5.4: Toggle für Journal
        self.journal_btn = QPushButton("📔")
        self.journal_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
            QPushButton:checked { background-color: #6A1B9A; }
        """)
        self.journal_btn.setToolTip("Trading Journal ein/ausblenden")
        self.journal_btn.setCheckable(True)
        self.journal_btn.clicked.connect(self._toggle_journal)
        layout.addWidget(self.journal_btn)

        # NOTE: WhatsApp Button wurde in das ChartWindow Trading Bot Panel verschoben

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #666; }
        """)
        self.settings_btn.setToolTip("Bot Settings")
        self.settings_btn.setEnabled(True)
        self.settings_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        print(f"DEBUG: Connecting settings button clicked signal...")
        self.settings_btn.clicked.connect(lambda checked=False: self._handle_settings_click())
        receiver_count = self.settings_btn.receivers(self.settings_btn.clicked)
        print(f"DEBUG: Settings button has {receiver_count} receivers connected")

        layout.addWidget(self.settings_btn)

        return frame

    def _create_signal_section(self) -> QGroupBox:
        """Erstellt Signal-Anzeige Sektion."""
        group = QGroupBox("📊 Aktuelles Signal")
        layout = QVBoxLayout(group)

        # Direction und Confidence
        row1 = QHBoxLayout()

        self.signal_direction = QLabel("—")
        self.signal_direction.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 5px 15px;
            border-radius: 4px;
            background-color: #333;
        """)
        row1.addWidget(self.signal_direction)

        row1.addWidget(QLabel("Confluence:"))
        self.signal_confluence = QLabel("—")
        self.signal_confluence.setStyleSheet("font-weight: bold;")
        row1.addWidget(self.signal_confluence)

        row1.addStretch()

        self.signal_regime = QLabel("Regime: —")
        self.signal_regime.setStyleSheet("color: #888;")
        row1.addWidget(self.signal_regime)

        layout.addLayout(row1)

        # Conditions
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Conditions:"))
        self.signal_conditions = QLabel("—")
        self.signal_conditions.setWordWrap(True)
        self.signal_conditions.setStyleSheet("color: #aaa; font-size: 11px;")
        row2.addWidget(self.signal_conditions, 1)
        layout.addLayout(row2)

        # SL/TP Visual Bar (nur sichtbar wenn Position offen)
        self.sltp_container = QWidget()
        sltp_layout = QVBoxLayout(self.sltp_container)
        sltp_layout.setContentsMargins(0, 10, 0, 0)

        # Labels für SL / Current / TP
        sltp_labels_row = QHBoxLayout()
        self.sltp_sl_label = QLabel("SL: —")
        self.sltp_sl_label.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 11px;")
        sltp_labels_row.addWidget(self.sltp_sl_label)
        sltp_labels_row.addStretch()
        self.sltp_current_label = QLabel("—")
        self.sltp_current_label.setStyleSheet("color: #fff; font-weight: bold; font-size: 12px;")
        sltp_labels_row.addWidget(self.sltp_current_label)
        sltp_labels_row.addStretch()
        self.sltp_tp_label = QLabel("TP: —")
        self.sltp_tp_label.setStyleSheet("color: #26a69a; font-weight: bold; font-size: 11px;")
        sltp_labels_row.addWidget(self.sltp_tp_label)
        sltp_layout.addLayout(sltp_labels_row)

        # Progress Bar (simuliert Balken zwischen SL und TP)
        self.sltp_bar = QProgressBar()
        self.sltp_bar.setTextVisible(False)
        self.sltp_bar.setMinimum(0)
        self.sltp_bar.setMaximum(100)
        self.sltp_bar.setValue(50)  # Default: Mitte
        self.sltp_bar.setMaximumHeight(20)
        # Grün-Rot Gradient: Rot=0% (SL), Grün=100% (TP)
        self.sltp_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #222;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef5350, stop:0.5 #ffa726, stop:1 #26a69a);
                border-radius: 2px;
            }
        """)
        sltp_layout.addWidget(self.sltp_bar)

        # P&L Display unter dem Balken
        self.sltp_pnl_label = QLabel("P&L: —")
        self.sltp_pnl_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")
        self.sltp_pnl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sltp_layout.addWidget(self.sltp_pnl_label)

        layout.addWidget(self.sltp_container)
        self.sltp_container.setVisible(True)  # Immer sichtbar, zeigt "keine Position" wenn nicht aktiv

        # Last Update
        row3 = QHBoxLayout()
        self.signal_timestamp = QLabel("Letztes Update: —")
        self.signal_timestamp.setStyleSheet("color: #666; font-size: 10px;")
        row3.addWidget(self.signal_timestamp)
        row3.addStretch()
        layout.addLayout(row3)

        return group

    def _create_position_section(self) -> QGroupBox:
        """Erstellt Position-Anzeige Sektion."""
        group = QGroupBox("📈 Aktive Position")
        layout = QVBoxLayout(group)

        # Position Details Grid
        details_layout = QHBoxLayout()

        # Left Column
        left = QVBoxLayout()

        side_row = QHBoxLayout()
        side_row.addWidget(QLabel("Richtung:"))
        self.pos_side = QLabel("—")
        self.pos_side.setStyleSheet("font-weight: bold;")
        side_row.addWidget(self.pos_side)
        side_row.addStretch()
        left.addLayout(side_row)

        entry_row = QHBoxLayout()
        entry_row.addWidget(QLabel("Entry:"))
        self.pos_entry = QLabel("—")
        entry_row.addWidget(self.pos_entry)
        entry_row.addStretch()
        left.addLayout(entry_row)

        current_row = QHBoxLayout()
        current_row.addWidget(QLabel("Aktuell:"))
        self.pos_current = QLabel("—")
        self.pos_current.setStyleSheet("font-weight: bold;")
        current_row.addWidget(self.pos_current)
        current_row.addStretch()
        left.addLayout(current_row)

        details_layout.addLayout(left)

        # Right Column
        right = QVBoxLayout()

        sl_row = QHBoxLayout()
        sl_row.addWidget(QLabel("SL:"))
        self.pos_sl = QLabel("—")
        self.pos_sl.setStyleSheet("color: #f44336;")
        sl_row.addWidget(self.pos_sl)
        sl_row.addStretch()
        right.addLayout(sl_row)

        tp_row = QHBoxLayout()
        tp_row.addWidget(QLabel("TP:"))
        self.pos_tp = QLabel("—")
        self.pos_tp.setStyleSheet("color: #4CAF50;")
        tp_row.addWidget(self.pos_tp)
        tp_row.addStretch()
        right.addLayout(tp_row)

        pnl_row = QHBoxLayout()
        pnl_row.addWidget(QLabel("PnL:"))
        self.pos_pnl = QLabel("—")
        self.pos_pnl.setStyleSheet("font-weight: bold;")
        pnl_row.addWidget(self.pos_pnl)
        pnl_row.addStretch()
        right.addLayout(pnl_row)

        details_layout.addLayout(right)
        layout.addLayout(details_layout)

        # SL/TP Progress Bar
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("SL"))
        self.sl_tp_progress = QProgressBar()
        self.sl_tp_progress.setRange(0, 100)
        self.sl_tp_progress.setValue(50)
        self.sl_tp_progress.setTextVisible(False)
        self.sl_tp_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 3px;
                background-color: #1a1a1a;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f44336, stop:0.5 #FFC107, stop:1 #4CAF50
                );
            }
        """)
        progress_layout.addWidget(self.sl_tp_progress, 1)
        progress_layout.addWidget(QLabel("TP"))
        layout.addLayout(progress_layout)

        # Close Button
        self.close_position_btn = QPushButton("❌ Position schließen")
        self.close_position_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #B71C1C; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.close_position_btn.setEnabled(False)
        self.close_position_btn.clicked.connect(self._on_close_position_clicked)
        layout.addWidget(self.close_position_btn)

        return group

    def _create_stats_section(self) -> QGroupBox:
        """Erstellt Statistik-Anzeige."""
        group = QGroupBox("📊 Tagesstatistik")
        layout = QHBoxLayout(group)

        # Trades
        trades_layout = QVBoxLayout()
        self.stats_trades = QLabel("0")
        self.stats_trades.setStyleSheet("font-size: 18px; font-weight: bold;")
        trades_layout.addWidget(self.stats_trades, alignment=Qt.AlignmentFlag.AlignCenter)
        trades_layout.addWidget(QLabel("Trades"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(trades_layout)

        layout.addWidget(self._create_separator())

        # Win Rate
        wr_layout = QVBoxLayout()
        self.stats_winrate = QLabel("—%")
        self.stats_winrate.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        wr_layout.addWidget(self.stats_winrate, alignment=Qt.AlignmentFlag.AlignCenter)
        wr_layout.addWidget(QLabel("Win Rate"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(wr_layout)

        layout.addWidget(self._create_separator())

        # PnL
        pnl_layout = QVBoxLayout()
        self.stats_pnl = QLabel("$0.00")
        self.stats_pnl.setStyleSheet("font-size: 18px; font-weight: bold;")
        pnl_layout.addWidget(self.stats_pnl, alignment=Qt.AlignmentFlag.AlignCenter)
        pnl_layout.addWidget(QLabel("Daily PnL"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(pnl_layout)

        layout.addWidget(self._create_separator())

        # Max Drawdown
        dd_layout = QVBoxLayout()
        self.stats_drawdown = QLabel("$0.00")
        self.stats_drawdown.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")
        dd_layout.addWidget(self.stats_drawdown, alignment=Qt.AlignmentFlag.AlignCenter)
        dd_layout.addWidget(QLabel("Max DD"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(dd_layout)

        return group

    def _create_separator(self) -> QFrame:
        """Erstellt vertikalen Separator."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #333;")
        return sep

    def _create_log_section(self) -> QGroupBox:
        """Erstellt Log-Viewer."""
        group = QGroupBox("📝 Bot Log")
        layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d0d;
                color: #aaa;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.log_text)

        # Clear Button
        clear_btn = QPushButton("🗑 Log löschen")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #888;
                padding: 5px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #444; }
        """)
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        layout.addWidget(clear_btn)

        return group

    def _setup_signals(self) -> None:
        """Verbindet interne Signals für Thread-sichere Updates."""
        self.status_changed.connect(self._update_status_display)
        self.signal_updated.connect(self._update_signal_display)
        self.position_updated.connect(self._update_position_display)
        self.stats_updated.connect(self._update_stats_display)
        self.log_message.connect(self._append_log)

    def _setup_timers(self) -> None:
        """Erstellt Timer für periodische Updates."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._periodic_update)
        self.update_timer.setInterval(1000)  # 1 Sekunde

    # === Bot Control ===

    @qasync.asyncSlot()
    async def _on_start_clicked(self) -> None:
        """Startet den Bot (neue Engine-Pipeline)."""
        try:
            self._log("🚀 Starte Trading Bot (neue Engine-Pipeline)...")
            logger.info("Bot start clicked - initializing pipeline...")

            # KRITISCH: Prüfe ob HistoryManager verfügbar ist
            if not self._history_manager:
                error_msg = (
                    "❌ HistoryManager nicht verfügbar!\n\n"
                    "Die Pipeline benötigt einen HistoryManager für Marktdaten.\n"
                    "Bitte öffne zuerst einen Chart mit einem Symbol."
                )
                self._log(error_msg)
                logger.error("Bot start failed: HistoryManager is None")
                QMessageBox.warning(
                    self,
                    "HistoryManager fehlt",
                    error_msg,
                )
                return

            # Neue Engines initialisieren (Phase 1-4)
            if not self._context_builder:
                self._log("🔧 Initialisiere Trading Engines...")
                self._initialize_new_engines()
                self._log("✅ Engines initialisiert")

            # UI aktualisieren
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.update_timer.start()

            self._log("✅ Bot gestartet! Pipeline läuft jede Sekunde.")
            logger.info("Bot started successfully - pipeline running every second")

        except Exception as e:
            self._log(f"❌ Fehler beim Starten: {e}")
            logger.exception("Bot start failed")
            QMessageBox.critical(self, "Fehler", f"Bot konnte nicht gestartet werden:\n{e}")

    @qasync.asyncSlot()
    async def _on_stop_clicked(self) -> None:
        """Stoppt den Bot (neue Engine-Pipeline)."""
        try:
            self._log("⏹ Stoppe Trading Bot...")

            # Timer stoppen (Pipeline stoppt automatisch)
            self.update_timer.stop()

            # UI aktualisieren
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

            self._log("✅ Bot gestoppt! Pipeline wurde angehalten.")

        except Exception as e:
            self._log(f"❌ Fehler beim Stoppen: {e}")
            logger.exception("Bot stop failed")

    @qasync.asyncSlot()
    async def _on_close_position_clicked(self) -> None:
        """Schließt die aktuelle Position manuell (neue Pipeline)."""
        if not self._current_position:
            QMessageBox.warning(self, "Keine Position", "Es ist keine Position geöffnet.")
            return

        confirm = QMessageBox.question(
            self,
            "Position schließen",
            "Position wirklich manuell schließen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                self._log("🔄 Schließe Position manuell...")
                # Hole aktuellen Preis aus letztem MarketContext
                current_price = self._last_market_context.current_price if self._last_market_context else self._position_entry_price
                context_id = self._last_market_context.context_id if self._last_market_context else "manual_close"

                await self._close_position(
                    exit_price=current_price,
                    exit_reason="Manual Close (User)",
                    context_id=context_id,
                )
                self._log("✅ Position geschlossen!")
            except Exception as e:
                self._log(f"❌ Fehler: {e}")
                logger.exception("Manual position close failed")

    def _handle_settings_click(self) -> None:
        """Handler für Settings-Button mit Debug-Output."""
        print("=" * 50)
        print("DEBUG: Settings button was clicked!")
        print("=" * 50)
        # Visuelle Bestätigung dass Button geklickt wurde
        self.settings_btn.setText("...")
        self.settings_btn.repaint()  # Force immediate repaint
        try:
            self._on_settings_clicked()
        finally:
            self.settings_btn.setText("⚙")

    @pyqtSlot()
    def _on_settings_clicked(self) -> None:
        """Öffnet Settings Dialog."""
        print("DEBUG: _on_settings_clicked() called")
        logger.info("Settings button clicked!")
        self._log("⚙ Öffne Einstellungen...")
        try:
            print("DEBUG: Getting config...")
            config = self._get_current_config()
            print(f"DEBUG: Config loaded: {config.symbol}")
            logger.info(f"Config loaded: {config.symbol}")

            print("DEBUG: Creating dialog...")
            dialog = BotSettingsDialog(config, self)
            print("DEBUG: Dialog created, calling exec()...")

            result = dialog.exec()
            print(f"DEBUG: Dialog result: {result}")
            logger.info(f"Dialog result: {result}")

            if result == QDialog.DialogCode.Accepted:
                new_config = dialog.get_config()
                self._apply_config(new_config)
                self._log("⚙ Einstellungen aktualisiert")
            else:
                self._log("⚙ Einstellungen abgebrochen")
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            import traceback
            traceback.print_exc()
            logger.exception("Settings dialog error")
            self._log(f"❌ Settings Fehler: {e}")
            QMessageBox.critical(self, "Fehler", f"Settings konnten nicht geöffnet werden:\n{e}")

    # === Phase 5: Status Panel Methods ===

    def _toggle_status_panel(self) -> None:
        """Togglet die Sichtbarkeit des Status Panels."""
        if self._status_panel:
            visible = self.status_panel_btn.isChecked()
            self._status_panel.setVisible(visible)
            if visible:
                self._log("📊 Status Panel eingeblendet")
                self._update_status_panel()
            else:
                self._log("📊 Status Panel ausgeblendet")

    def _on_status_panel_refresh(self) -> None:
        """Callback wenn Status Panel Refresh angefordert wird."""
        self._update_status_panel()

    def _update_status_panel(self) -> None:
        """Aktualisiert das Status Panel mit aktuellen Engine-Ergebnissen.

        Nutzt die Ergebnisse aus der neuen Engine-Pipeline:
        - self._last_regime_result (von RegimeDetectorService)
        - self._last_entry_score (von EntryScoreEngine)
        - self._last_llm_result (von LLMValidationService)
        - self._last_trigger_result (von TriggerExitEngine)
        - self._last_leverage_result (von LeverageRulesEngine)
        """
        if not self._status_panel:
            return

        try:
            # Regime Result
            regime_result = None
            if self._last_market_context and self._last_market_context.regime:
                regime_result = self._last_market_context.regime

            # Entry Score Result
            score_result = self._last_entry_score

            # LLM Validation Result
            llm_result = self._last_llm_result

            # Trigger Result
            trigger_result = self._last_trigger_result

            # Leverage Result
            leverage_result = self._last_leverage_result

            # Update all at once
            self._status_panel.update_all(
                regime_result=regime_result,
                score_result=score_result,
                llm_result=llm_result,
                trigger_result=trigger_result,
                leverage_result=leverage_result,
            )

            logger.debug("Status Panel updated with new engine results")

        except Exception as e:
            logger.warning(f"Failed to update status panel: {e}")

    # === Phase 5.4: Journal Methods ===

    def _toggle_journal(self) -> None:
        """Togglet die Sichtbarkeit des Trading Journals."""
        if self._journal_widget:
            visible = self.journal_btn.isChecked()
            self._journal_widget.setVisible(visible)
            if visible:
                self._log("📔 Trading Journal eingeblendet")
                self._journal_widget.refresh_trades()
            else:
                self._log("📔 Trading Journal ausgeblendet")

    # NOTE: WhatsApp Methods wurden in das ChartWindow Trading Bot Panel verschoben
    # (siehe panels_mixin.py und whatsapp_widget.py)

    def _log_signal_to_journal(self, signal: TradeSignal) -> None:
        """Loggt ein Signal ins Journal."""
        if not self._journal_widget:
            return

        # Symbol aus Config laden (neue Pipeline)
        config = self._get_current_config()
        signal_data = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "symbol": config.symbol if config else "-",
            "direction": signal.direction.value if hasattr(signal.direction, 'value') else str(signal.direction),
            "score": getattr(signal, 'entry_score', 0) or len(signal.conditions_met) / 5,
            "quality": getattr(signal, 'quality', 'MODERATE'),
            "gate_status": getattr(signal, 'gate_status', 'PASSED'),
            "trigger": signal.regime or "-",
        }
        self._journal_widget.add_signal(signal_data)

    def _log_llm_to_journal(self, llm_result: dict) -> None:
        """Loggt ein LLM-Ergebnis ins Journal."""
        if not self._journal_widget:
            return

        # Symbol aus Config laden (neue Pipeline)
        config = self._get_current_config()
        llm_data = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "symbol": config.symbol if config else "-",
            **llm_result,
        }
        self._journal_widget.add_llm_output(llm_data)

    def _log_error_to_journal(self, error_msg: str, context: str = "") -> None:
        """Loggt einen Fehler ins Journal."""
        if not self._journal_widget:
            return

        error_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "ERROR",
            "message": error_msg,
            "context": context,
        }
        self._journal_widget.add_error(error_data)

    # === Bot Engine ===

    # OLD: _initialize_bot_engine() REMOVED - using new engine pipeline
    # def _initialize_bot_engine(): DELETED

    def _initialize_new_engines(self) -> None:
        """Initialisiert die neuen Engines (Phase 1-4).

        Diese Methode erstellt alle neuen Trading-Engines:
        - MarketContextBuilder: Baut MarketContext aus DataFrame
        - RegimeDetectorService: Erkennt Markt-Regime
        - LevelEngine: Erkennt Support/Resistance Levels
        - EntryScoreEngine: Berechnet normalisierten Entry-Score
        - LLMValidationService: AI-Validierung (Quick→Deep)
        - TriggerExitEngine: Entry-Trigger + Exit-Management
        - LeverageRulesEngine: Dynamisches Leverage-Regelwerk
        """
        try:
            # 1. MarketContextBuilder - Single Source of Truth
            builder_config = MarketContextBuilderConfig(
                enable_caching=True,
                enable_preflight=True,
                require_regime=True,
                require_levels=True,
            )
            self._context_builder = MarketContextBuilder(config=builder_config)
            logger.info("✅ MarketContextBuilder initialized")

            # 2. RegimeDetectorService
            regime_config = RegimeConfig(
                trend_lookback=50,
                volatility_lookback=20,
                threshold_strong_trend=0.7,
                threshold_weak_trend=0.4,
                threshold_chop=0.3,
            )
            self._regime_detector = RegimeDetectorService(config=regime_config)
            logger.info("✅ RegimeDetectorService initialized")

            # 3. LevelEngine
            level_config = LevelEngineConfig(
                swing_lookback=20,
                min_touches=2,
                price_tolerance_pct=0.5,
                enable_daily_levels=True,
                enable_weekly_levels=True,
            )
            self._level_engine = LevelEngine(config=level_config)
            logger.info("✅ LevelEngine initialized")

            # 4. EntryScoreEngine
            entry_config = EntryScoreConfig(
                # Weights
                weight_trend=0.25,
                weight_rsi=0.15,
                weight_macd=0.15,
                weight_adx=0.15,
                weight_volatility=0.15,
                weight_volume=0.15,
                # Quality thresholds
                score_excellent=0.8,
                score_good=0.6,
                score_acceptable=0.4,
            )
            self._entry_score_engine = EntryScoreEngine(config=entry_config)
            logger.info("✅ EntryScoreEngine initialized")

            # 5. LLMValidationService
            llm_config = LLMValidationConfig(
                quick_threshold_score=0.7,
                deep_threshold_score=0.5,
                veto_modifier=-0.3,
                boost_modifier=0.2,
                enable_quick=True,
                enable_deep=True,
            )
            self._llm_validation = LLMValidationService(config=llm_config)
            logger.info("✅ LLMValidationService initialized")

            # 6. TriggerExitEngine
            trigger_config = TriggerExitConfig(
                # Entry triggers
                enable_breakout=True,
                enable_pullback=True,
                enable_sfp=True,
                # Exit settings
                use_atr_stops=True,
                atr_sl_multiplier=2.0,
                atr_tp_multiplier=3.0,
                enable_trailing=True,
            )
            self._trigger_exit_engine = TriggerExitEngine(config=trigger_config)
            logger.info("✅ TriggerExitEngine initialized")

            # 7. LeverageRulesEngine
            leverage_config = LeverageRulesConfig(
                # Asset tiers
                tier_blue_chip_max=5.0,
                tier_mid_cap_max=3.0,
                tier_small_cap_max=2.0,
                # Regime modifiers
                strong_trend_modifier=1.0,
                weak_trend_modifier=0.7,
                chop_range_modifier=0.5,
                volatility_explosive_modifier=0.3,
            )
            self._leverage_engine = LeverageRulesEngine(config=leverage_config)
            logger.info("✅ LeverageRulesEngine initialized")

            self._log("✅ Alle neuen Engines initialisiert (Phase 1-4)")

        except Exception as e:
            logger.exception("Failed to initialize new engines")
            self._log(f"❌ Fehler bei Engine-Initialisierung: {e}")
            raise

    def update_engine_configs(self) -> None:
        """Aktualisiert die Konfiguration aller laufenden Engines.

        Lädt Config-Files und wendet sie auf die laufenden Engine-Instanzen an.
        WICHTIG: Sofort wirksam, kein Bot-Neustart nötig (Punkt 2).
        """
        if not self._context_builder:
            logger.warning("Engines not initialized yet - skipping config update")
            return

        try:
            from src.core.trading_bot import (
                load_entry_score_config,
                load_trigger_exit_config,
                load_leverage_config,
                load_llm_validation_config,
            )

            # 1. Entry Score Config laden und anwenden
            if self._entry_score_engine:
                entry_config = load_entry_score_config()
                self._entry_score_engine.config = entry_config
                logger.info(f"✅ EntryScoreEngine config updated: weights={entry_config.weight_trend}/{entry_config.weight_rsi}/{entry_config.weight_macd}")

            # 2. Trigger/Exit Config laden und anwenden
            if self._trigger_exit_engine:
                trigger_config = load_trigger_exit_config()
                self._trigger_exit_engine.config = trigger_config
                logger.info(f"✅ TriggerExitEngine config updated: breakout={trigger_config.enable_breakout}, pullback={trigger_config.enable_pullback}")

            # 3. Leverage Config laden und anwenden
            if self._leverage_engine:
                leverage_config = load_leverage_config()
                self._leverage_engine.config = leverage_config
                logger.info(f"✅ LeverageRulesEngine config updated: blue_chip_max={leverage_config.tier_blue_chip_max}x")

            # 4. LLM Validation Config laden und anwenden
            if self._llm_validation:
                llm_config = load_llm_validation_config()
                self._llm_validation.config = llm_config
                logger.info(f"✅ LLMValidationService config updated: quick_threshold={llm_config.quick_threshold_score}")

            # Note: RegimeDetector und LevelEngine haben keine Config-Files
            # (nutzen Builder-Config bzw. fest codierte Werte)

            self._log("⚙️ Engine-Konfigurationen aktualisiert (sofort wirksam)")
            logger.info("All engine configs reloaded and applied to running instances")

        except Exception as e:
            logger.exception(f"Failed to update engine configs: {e}")
            self._log(f"❌ Fehler beim Aktualisieren der Engine-Configs: {e}")

    async def _process_market_data_through_engines(self, symbol: str, timeframe: str = "1m") -> None:
        """Holt Marktdaten und schickt sie durch die Engine-Pipeline.

        Pipeline:
        1. DataFrame von HistoryManager holen
        2. MarketContext bauen (via MarketContextBuilder)
        3. EntryScore berechnen
        4. LLM Validation (Quick→Deep)
        5. Trigger prüfen
        6. Leverage berechnen
        7. Ergebnisse speichern für Status Panel

        Args:
            symbol: Trading-Symbol (z.B. "BTCUSDT")
            timeframe: Timeframe (z.B. "1m", "5m")
        """
        if not self._context_builder or not self._history_manager:
            logger.warning(
                f"Pipeline skipped - context_builder={self._context_builder is not None}, "
                f"history_manager={self._history_manager is not None}"
            )
            return

        try:
            # 1. DataFrame holen (letzten 200 Kerzen für Indikatoren)
            import pandas as pd
            df = await self._history_manager.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                limit=200,
            )

            if df is None or df.empty:
                logger.warning(f"No data available for {symbol} {timeframe}")
                return

            # 2. MarketContext bauen
            context = self._context_builder.build(df, symbol=symbol, timeframe=timeframe)
            self._last_market_context = context
            logger.debug(f"MarketContext built: {context.context_id}")

            # 3. EntryScore berechnen
            if self._entry_score_engine:
                entry_result = self._entry_score_engine.calculate(context)
                self._last_entry_score = entry_result
                logger.debug(f"Entry Score: {entry_result.final_score:.3f} ({entry_result.quality.value})")

            # 4. LLM Validation (Quick→Deep)
            if self._llm_validation and self._last_entry_score:
                llm_result = await self._llm_validation.validate(
                    context=context,
                    entry_score=self._last_entry_score.final_score,
                    direction="long" if self._last_entry_score.direction.value == "long" else "short",
                )
                self._last_llm_result = llm_result
                logger.debug(f"LLM Validation: {llm_result.action.value} (tier={llm_result.tier.value})")

            # 5. Trigger prüfen
            if self._trigger_exit_engine and self._last_entry_score:
                trigger_result = self._trigger_exit_engine.check_trigger(
                    context=context,
                    direction="long" if self._last_entry_score.direction.value == "long" else "short",
                )
                self._last_trigger_result = trigger_result
                logger.debug(f"Trigger: {trigger_result.status.value} (type={trigger_result.trigger_type.value if trigger_result.trigger_type else 'None'})")

            # 6. Leverage berechnen
            if self._leverage_engine:
                leverage_result = self._leverage_engine.calculate(
                    symbol=symbol,
                    regime=context.regime.regime_type,
                )
                self._last_leverage_result = leverage_result
                logger.debug(f"Leverage: {leverage_result.final_leverage:.1f}x (action={leverage_result.action.value})")

            # 7. Trade-Ausführung (falls Trigger aktiv und keine offene Position)
            await self._execute_trade_if_triggered(symbol=symbol, context=context)

            # 8. Position Monitoring (falls offene Position)
            await self._monitor_open_position(context=context)

            # 9. Status Panel aktualisieren (falls sichtbar)
            if self._status_panel and self.status_panel_btn.isChecked():
                self._update_status_panel()

            # 10. Journal Log (mit MarketContext ID)
            self._log_engine_results_to_journal()

        except Exception as e:
            logger.exception(f"Failed to process market data through engines: {e}")
            self._log(f"❌ Engine-Pipeline Fehler: {e}")

    async def _execute_trade_if_triggered(self, symbol: str, context: MarketContext) -> None:
        """Führt Trade aus wenn alle Bedingungen erfüllt sind.

        Bedingungen für Entry:
        1. Kein offener Trade (self._current_position is None)
        2. Trigger-Status = TRIGGERED
        3. Entry Score Quality >= ACCEPTABLE
        4. LLM Validation != VETO

        Args:
            symbol: Trading-Symbol
            context: Aktueller MarketContext
        """
        # 1. Prüfen ob bereits Position offen
        if self._current_position is not None:
            logger.debug("Position already open - skipping entry")
            return

        # 2. Prüfen ob Trigger aktiv
        if not self._last_trigger_result or self._last_trigger_result.status.value != "triggered":
            logger.debug(f"No trigger - status: {self._last_trigger_result.status.value if self._last_trigger_result else 'None'}")
            return

        # 3. Prüfen ob Entry Score gut genug
        if not self._last_entry_score or self._last_entry_score.quality.value not in ["excellent", "good", "acceptable"]:
            logger.warning(f"Entry score quality too low: {self._last_entry_score.quality.value if self._last_entry_score else 'None'}")
            self._log(f"⚠️ Entry Score zu niedrig: {self._last_entry_score.quality.value if self._last_entry_score else 'None'}")
            return

        # 4. Prüfen ob LLM Veto
        if self._last_llm_result and self._last_llm_result.action.value == "veto":
            logger.warning(f"LLM VETO - blocking trade: {self._last_llm_result.reasoning[:100]}")
            self._log(f"🚫 LLM VETO: {self._last_llm_result.reasoning[:50]}...")
            return

        # Alle Bedingungen erfüllt → Trade ausführen
        try:
            direction = self._last_entry_score.direction.value  # "long" or "short"
            entry_price = context.current_price

            # Position Size berechnen (mit Leverage)
            leverage = self._last_leverage_result.final_leverage if self._last_leverage_result else 1.0

            # Hole Risk-Settings aus Config
            config = self._get_current_config()
            risk_per_trade_pct = config.risk_per_trade_pct  # z.B. 1.0 = 1% des Kapitals

            # Hole Kontogröße vom Adapter
            account_balance = await self._adapter.get_balance()

            # Berechne Position Size
            risk_amount = account_balance * (risk_per_trade_pct / 100.0)

            # Stop Loss Distanz aus TriggerExitEngine
            exit_levels = self._last_trigger_result.exit_levels
            if not exit_levels:
                logger.error("No exit levels from TriggerExitEngine")
                return

            sl_price = exit_levels.stop_loss
            tp_price = exit_levels.take_profit

            # SL-Distanz in %
            if direction == "long":
                sl_distance_pct = abs((entry_price - sl_price) / entry_price)
            else:
                sl_distance_pct = abs((sl_price - entry_price) / entry_price)

            # Quantity berechnen: Risk / SL-Distanz
            quantity = (risk_amount / (entry_price * sl_distance_pct)) * leverage

            # Position öffnen über Adapter
            self._log(f"🚀 Opening {direction.upper()} position: {quantity:.4f} {symbol} @ {entry_price:.2f}")
            self._log(f"   SL: {sl_price:.2f} | TP: {tp_price:.2f} | Leverage: {leverage:.1f}x")

            order_result = await self._adapter.place_order(
                symbol=symbol,
                side="buy" if direction == "long" else "sell",
                quantity=quantity,
                order_type="market",
            )

            if order_result and order_result.get("status") == "filled":
                # Position erfolgreich eröffnet
                self._current_position = {
                    "symbol": symbol,
                    "side": direction,
                    "entry_price": entry_price,
                    "quantity": quantity,
                    "stop_loss": sl_price,
                    "take_profit": tp_price,
                    "leverage": leverage,
                    "entry_time": datetime.now(timezone.utc),
                    "context_id": context.context_id,
                    "trigger_type": self._last_trigger_result.trigger_type.value if self._last_trigger_result.trigger_type else "unknown",
                }

                self._position_entry_price = entry_price
                self._position_side = direction
                self._position_quantity = quantity
                self._position_stop_loss = sl_price
                self._position_take_profit = tp_price

                self._log(f"✅ Position opened: {direction.upper()} {quantity:.4f} @ {entry_price:.2f}")

                # Show SL/TP Visual Bar
                self.sltp_container.setVisible(True)
                self._update_sltp_bar(entry_price)

                # Journal Log
                if self._journal_widget:
                    trade_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "context_id": context.context_id,
                        "action": "ENTRY",
                        "side": direction,
                        "price": entry_price,
                        "quantity": quantity,
                        "stop_loss": sl_price,
                        "take_profit": tp_price,
                        "leverage": leverage,
                        "trigger": self._last_trigger_result.trigger_type.value if self._last_trigger_result.trigger_type else "unknown",
                        "entry_score": self._last_entry_score.final_score,
                        "llm_action": self._last_llm_result.action.value if self._last_llm_result else "none",
                    }
                    self._journal_widget.add_trade(trade_data)

                # NOTE: WhatsApp Notification erfolgt über das ChartWindow Trading Bot Panel
            else:
                logger.error(f"Order failed: {order_result}")
                self._log(f"❌ Order failed: {order_result}")

        except Exception as e:
            logger.exception(f"Failed to execute trade: {e}")
            self._log(f"❌ Trade execution error: {e}")

    async def _monitor_open_position(self, context: MarketContext) -> None:
        """Überwacht offene Position und managed Exit.

        Exit-Bedingungen:
        1. Stop Loss hit
        2. Take Profit hit
        3. Trailing Stop triggered
        4. Exit-Signal von TriggerExitEngine

        Args:
            context: Aktueller MarketContext
        """
        if not self._current_position:
            return  # Keine offene Position

        try:
            current_price = context.current_price
            side = self._current_position["side"]
            entry_price = self._current_position["entry_price"]

            # Prüfe SL/TP
            should_exit = False
            exit_reason = ""

            if side == "long":
                # Long Position
                if current_price <= self._position_stop_loss:
                    should_exit = True
                    exit_reason = "Stop Loss hit"
                elif current_price >= self._position_take_profit:
                    should_exit = True
                    exit_reason = "Take Profit hit"
            else:
                # Short Position
                if current_price >= self._position_stop_loss:
                    should_exit = True
                    exit_reason = "Stop Loss hit"
                elif current_price <= self._position_take_profit:
                    should_exit = True
                    exit_reason = "Take Profit hit"

            # Trailing Stop Update (falls aktiviert)
            if self._trigger_exit_engine and not should_exit:
                # Hole neue Exit-Levels (mit Trailing)
                exit_signal = self._trigger_exit_engine.check_exit(
                    context=context,
                    entry_price=entry_price,
                    side=side,
                )

                if exit_signal and exit_signal.exit_type.value == "trailing_stop":
                    # Trailing Stop wurde getriggert
                    should_exit = True
                    exit_reason = "Trailing Stop triggered"
                elif exit_signal and exit_signal.updated_levels:
                    # SL/TP Update (Trailing)
                    new_sl = exit_signal.updated_levels.stop_loss
                    new_tp = exit_signal.updated_levels.take_profit

                    if new_sl != self._position_stop_loss or new_tp != self._position_take_profit:
                        logger.info(f"Updating SL/TP: SL {self._position_stop_loss:.2f} → {new_sl:.2f}, TP {self._position_take_profit:.2f} → {new_tp:.2f}")
                        self._position_stop_loss = new_sl
                        self._position_take_profit = new_tp
                        self._current_position["stop_loss"] = new_sl
                        self._current_position["take_profit"] = new_tp
                        self._log(f"📊 Trailing Update: SL={new_sl:.2f} TP={new_tp:.2f}")

            # Exit ausführen falls nötig
            if should_exit:
                await self._close_position(
                    exit_price=current_price,
                    exit_reason=exit_reason,
                    context_id=context.context_id,
                )
            else:
                # Update SL/TP Visual Bar
                self._update_sltp_bar(current_price)

        except Exception as e:
            logger.exception(f"Failed to monitor position: {e}")
            self._log(f"❌ Position monitoring error: {e}")

    async def _close_position(self, exit_price: float, exit_reason: str, context_id: str) -> None:
        """Schließt die offene Position.

        Args:
            exit_price: Exit-Preis
            exit_reason: Grund für Exit
            context_id: MarketContext ID
        """
        if not self._current_position:
            return

        try:
            symbol = self._current_position["symbol"]
            side = self._current_position["side"]
            quantity = self._current_position["quantity"]
            entry_price = self._current_position["entry_price"]

            # Order platzieren (gegenläufig)
            close_side = "sell" if side == "long" else "buy"

            self._log(f"🔴 Closing {side.upper()} position: {quantity:.4f} {symbol} @ {exit_price:.2f}")
            self._log(f"   Reason: {exit_reason}")

            order_result = await self._adapter.place_order(
                symbol=symbol,
                side=close_side,
                quantity=quantity,
                order_type="market",
            )

            if order_result and order_result.get("status") == "filled":
                # P&L berechnen
                if side == "long":
                    pnl = (exit_price - entry_price) * quantity
                else:
                    pnl = (entry_price - exit_price) * quantity

                pnl_pct = (pnl / (entry_price * quantity)) * 100

                self._log(f"✅ Position closed: P&L = ${pnl:.2f} ({pnl_pct:+.2f}%)")

                # Journal Log
                if self._journal_widget:
                    trade_data = {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "context_id": context_id,
                        "action": "EXIT",
                        "side": side,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "quantity": quantity,
                        "pnl": pnl,
                        "pnl_pct": pnl_pct,
                        "exit_reason": exit_reason,
                        "hold_time": str(datetime.now(timezone.utc) - self._current_position["entry_time"]),
                    }
                    self._journal_widget.add_trade(trade_data)

                # NOTE: WhatsApp Notification erfolgt über das ChartWindow Trading Bot Panel

                # Position löschen
                self._current_position = None
                self._position_entry_price = 0.0
                self._position_side = ""
                self._position_quantity = 0.0
                self._position_stop_loss = 0.0
                self._position_take_profit = 0.0

                # Reset SL/TP Visual Bar (bleibt sichtbar, zeigt nur "keine Position")
                self._reset_sltp_bar()
            else:
                logger.error(f"Close order failed: {order_result}")
                self._log(f"❌ Close order failed: {order_result}")

        except Exception as e:
            logger.exception(f"Failed to close position: {e}")
            self._log(f"❌ Position close error: {e}")

    def _update_sltp_bar(self, current_price: float) -> None:
        """Aktualisiert den visuellen SL/TP Balken im Signals-Tab.

        Der Balken zeigt die Position zwischen SL (0%) und TP (100%):
        - Rot (links) = Stop Loss
        - Orange (mitte) = aktueller Preis
        - Grün (rechts) = Take Profit

        Args:
            current_price: Aktueller Marktpreis
        """
        if not self._current_position:
            return

        try:
            sl_price = self._position_stop_loss
            tp_price = self._position_take_profit
            entry_price = self._position_entry_price
            side = self._position_side

            # Berechne Position zwischen SL und TP (0-100%)
            if side == "long":
                # Long: SL < Entry < Current < TP
                price_range = tp_price - sl_price
                current_offset = current_price - sl_price
            else:
                # Short: TP < Current < Entry < SL
                price_range = sl_price - tp_price
                current_offset = sl_price - current_price

            # Position in % (0 = SL, 100 = TP)
            if price_range > 0:
                position_pct = (current_offset / price_range) * 100
                position_pct = max(0, min(100, position_pct))  # Clamp 0-100
            else:
                position_pct = 50  # Fallback

            # Update Bar
            self.sltp_bar.setValue(int(position_pct))

            # Update Labels
            self.sltp_sl_label.setText(f"SL: {sl_price:.2f}")
            self.sltp_current_label.setText(f"{current_price:.2f}")
            self.sltp_tp_label.setText(f"TP: {tp_price:.2f}")

            # Berechne P&L
            quantity = self._position_quantity
            if side == "long":
                pnl = (current_price - entry_price) * quantity
            else:
                pnl = (entry_price - current_price) * quantity

            pnl_pct = (pnl / (entry_price * quantity)) * 100

            # Update P&L Label mit Farbe
            pnl_color = "#26a69a" if pnl >= 0 else "#ef5350"
            pnl_sign = "+" if pnl >= 0 else ""
            self.sltp_pnl_label.setText(f"P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%)")
            self.sltp_pnl_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold; font-size: 12px; margin-top: 5px;")

        except Exception as e:
            logger.exception(f"Failed to update SL/TP bar: {e}")

    def _reset_sltp_bar(self) -> None:
        """Setzt den SL/TP Visual Bar auf Default-Werte zurück (keine aktive Position)."""
        try:
            # Reset Labels
            self.sltp_sl_label.setText("SL: —")
            self.sltp_current_label.setText("—")
            self.sltp_tp_label.setText("TP: —")
            self.sltp_pnl_label.setText("P&L: —")
            self.sltp_pnl_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")

            # Reset Bar
            self.sltp_bar.setValue(50)  # Mitte

            logger.debug("SL/TP bar reset to default state (no position)")
        except Exception as e:
            logger.exception(f"Failed to reset SL/TP bar: {e}")

    def _log_engine_results_to_journal(self) -> None:
        """Loggt Engine-Ergebnisse ins Trading Journal mit MarketContext ID."""
        if not self._journal_widget or not self._last_market_context:
            return

        try:
            # Entry Score
            if self._last_entry_score:
                entry_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "context_id": self._last_market_context.context_id,
                    "score": self._last_entry_score.final_score,
                    "quality": self._last_entry_score.quality.value,
                    "direction": self._last_entry_score.direction.value,
                    "components": {
                        comp.name: comp.value
                        for comp in self._last_entry_score.components
                    },
                }
                self._journal_widget.add_entry_score(entry_data)

            # LLM Result
            if self._last_llm_result:
                llm_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "context_id": self._last_market_context.context_id,
                    "action": self._last_llm_result.action.value,
                    "tier": self._last_llm_result.tier.value,
                    "reasoning": self._last_llm_result.reasoning[:200] if self._last_llm_result.reasoning else "",
                }
                self._journal_widget.add_llm_output(llm_data)

        except Exception as e:
            logger.exception(f"Failed to log engine results to journal: {e}")

    def _get_current_config(self) -> BotConfig:
        """Gibt aktuelle Bot-Konfiguration zurück (lädt aus Datei wenn vorhanden)."""
        return self._load_settings()

    def _apply_config(self, config: BotConfig) -> None:
        """Wendet neue Konfiguration an und speichert sie."""
        self._save_settings(config)
        # Neue Pipeline: Engine-Configs sofort aktualisieren
        self.update_engine_configs()

    def _save_settings(self, config: BotConfig) -> None:
        """Speichert Bot-Einstellungen in JSON-Datei."""
        try:
            # Stelle sicher dass Verzeichnis existiert
            BOT_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Config zu Dictionary konvertieren
            settings = config.to_dict()

            with open(BOT_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            logger.info(f"Bot-Einstellungen gespeichert: {BOT_SETTINGS_FILE}")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {e}")

    def _load_settings(self) -> BotConfig:
        """Lädt Bot-Einstellungen aus JSON-Datei."""
        try:
            if BOT_SETTINGS_FILE.exists():
                with open(BOT_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                logger.info(f"Bot-Einstellungen geladen: {BOT_SETTINGS_FILE}")
                return BotConfig.from_dict(settings)
        except Exception as e:
            logger.warning(f"Fehler beim Laden der Einstellungen: {e}")

        # Fallback: Default-Konfiguration
        return BotConfig(symbol="BTCUSDT")

    # === Callbacks (Thread-sicher via Signals) ===

    def _on_state_changed(self, state: BotState) -> None:
        """Callback wenn sich der Bot-State ändert."""
        self.status_changed.emit(state.value)

    def _on_signal_updated(self, signal: TradeSignal) -> None:
        """Callback wenn ein neues Signal generiert wurde."""
        self.signal_updated.emit(signal)
        # Phase 5.4: Log to journal
        self._log_signal_to_journal(signal)

    def _on_position_opened(self, position: MonitoredPosition) -> None:
        """Callback wenn eine Position geöffnet wurde."""
        self.position_updated.emit(position)

    def _on_position_closed(self, trade_log: TradeLogEntry) -> None:
        """Callback wenn eine Position geschlossen wurde."""
        # Position ist jetzt None (geschlossen)
        self.position_updated.emit(None)
        # Statistiken werden über _update_stats_display() aktualisiert
        # (alte _bot_engine.statistics entfernt - neue Pipeline hat eigene Stats)

    def _on_bot_error(self, error: str) -> None:
        """Callback für Bot-Fehler."""
        self._log(f"❌ Fehler: {error}")
        # Phase 5.4: Log to journal
        self._log_error_to_journal(error, context="Bot Engine")

    def _on_bot_log(self, message: str) -> None:
        """Callback für Bot-Log-Nachrichten."""
        self.log_message.emit(message)

    # === UI Updates ===

    def _update_status_display(self, state: str) -> None:
        """Aktualisiert Status-Anzeige."""
        state_config = {
            "IDLE": ("🤖", "#888", "Bot ist gestoppt"),
            "STARTING": ("🔄", "#FFC107", "Bot startet..."),
            "ANALYZING": ("🔍", "#2196F3", "Analysiere Markt..."),
            "WAITING_SIGNAL": ("⏳", "#9C27B0", "Warte auf Signal..."),
            "VALIDATING": ("🧠", "#FF9800", "Validiere Signal mit AI..."),
            "OPENING_POSITION": ("📈", "#4CAF50", "Öffne Position..."),
            "IN_POSITION": ("💰", "#4CAF50", "Position aktiv"),
            "CLOSING_POSITION": ("📉", "#f44336", "Schließe Position..."),
            "STOPPING": ("⏸", "#FFC107", "Bot stoppt..."),
            "ERROR": ("❌", "#f44336", "Fehler aufgetreten"),
        }

        icon, color, detail = state_config.get(state, ("❓", "#888", state))

        self.status_icon.setText(icon)
        self.status_label.setText(state)
        self.status_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {color};
        """)
        self.status_detail.setText(detail)

    def _update_signal_display(self, signal: TradeSignal | None) -> None:
        """Aktualisiert Signal-Anzeige."""
        if signal is None:
            self.signal_direction.setText("—")
            self.signal_direction.setStyleSheet("""
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #333;
            """)
            self.signal_confluence.setText("—")
            self.signal_regime.setText("Regime: —")
            self.signal_conditions.setText("—")
            self.signal_timestamp.setText("Letztes Update: —")
            return

        # Direction
        if signal.direction == SignalDirection.LONG:
            self.signal_direction.setText("📈 LONG")
            self.signal_direction.setStyleSheet("""
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #1B5E20; color: #4CAF50;
            """)
        elif signal.direction == SignalDirection.SHORT:
            self.signal_direction.setText("📉 SHORT")
            self.signal_direction.setStyleSheet("""
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #B71C1C; color: #f44336;
            """)
        else:
            self.signal_direction.setText("— NEUTRAL")
            self.signal_direction.setStyleSheet("""
                font-size: 18px; font-weight: bold;
                padding: 5px 15px; border-radius: 4px;
                background-color: #333;
            """)

        # Confluence
        total = len(signal.conditions_met) + len(signal.conditions_failed)
        met = len(signal.conditions_met)
        self.signal_confluence.setText(f"{met}/{total}")

        # Regime
        self.signal_regime.setText(f"Regime: {signal.regime or '—'}")

        # Conditions
        conditions = ", ".join([c.name for c in signal.conditions_met])
        self.signal_conditions.setText(conditions if conditions else "—")

        # Timestamp
        self.signal_timestamp.setText(f"Update: {datetime.now().strftime('%H:%M:%S')}")

    def _update_position_display(self, position: MonitoredPosition | None) -> None:
        """Aktualisiert Position-Anzeige."""
        if position is None:
            self.pos_side.setText("—")
            self.pos_side.setStyleSheet("font-weight: bold;")
            self.pos_entry.setText("—")
            self.pos_current.setText("—")
            self.pos_sl.setText("—")
            self.pos_tp.setText("—")
            self.pos_pnl.setText("—")
            self.sl_tp_progress.setValue(50)
            self.close_position_btn.setEnabled(False)
            return

        # Side
        if position.side == "BUY":
            self.pos_side.setText("🟢 LONG")
            self.pos_side.setStyleSheet("font-weight: bold; color: #4CAF50;")
        else:
            self.pos_side.setText("🔴 SHORT")
            self.pos_side.setStyleSheet("font-weight: bold; color: #f44336;")

        # Prices
        self.pos_entry.setText(f"${position.entry_price:,.2f}")
        if position.current_price:
            self.pos_current.setText(f"${position.current_price:,.2f}")

        self.pos_sl.setText(f"${position.stop_loss:,.2f}")
        self.pos_tp.setText(f"${position.take_profit:,.2f}")

        # PnL
        pnl = position.unrealized_pnl
        pnl_pct = position.unrealized_pnl_percent
        if pnl >= 0:
            self.pos_pnl.setText(f"+${pnl:,.2f} (+{pnl_pct:.2f}%)")
            self.pos_pnl.setStyleSheet("font-weight: bold; color: #4CAF50;")
        else:
            self.pos_pnl.setText(f"-${abs(pnl):,.2f} ({pnl_pct:.2f}%)")
            self.pos_pnl.setStyleSheet("font-weight: bold; color: #f44336;")

        # Progress Bar (Position zwischen SL und TP)
        if position.current_price and position.stop_loss and position.take_profit:
            price = float(position.current_price)
            sl = float(position.stop_loss)
            tp = float(position.take_profit)

            if position.side == "BUY":
                total_range = tp - sl
                if total_range > 0:
                    progress = int((price - sl) / total_range * 100)
                    progress = max(0, min(100, progress))
                    self.sl_tp_progress.setValue(progress)
            else:  # SHORT
                total_range = sl - tp
                if total_range > 0:
                    progress = int((sl - price) / total_range * 100)
                    progress = max(0, min(100, progress))
                    self.sl_tp_progress.setValue(progress)

        self.close_position_btn.setEnabled(True)

    def _update_stats_display(self, stats: BotStatistics) -> None:
        """Aktualisiert Statistik-Anzeige."""
        self.stats_trades.setText(str(stats.trades_total))

        # Win Rate
        wr = stats.win_rate
        self.stats_winrate.setText(f"{wr:.1f}%")
        if wr >= 50:
            self.stats_winrate.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        else:
            self.stats_winrate.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")

        # PnL
        pnl = stats.total_pnl
        if pnl >= 0:
            self.stats_pnl.setText(f"+${pnl:,.2f}")
            self.stats_pnl.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        else:
            self.stats_pnl.setText(f"-${abs(pnl):,.2f}")
            self.stats_pnl.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")

        # Drawdown
        dd = stats.max_drawdown
        self.stats_drawdown.setText(f"-${abs(dd):,.2f}")

    def _periodic_update(self) -> None:
        """Periodisches UI Update (Punkt 4: Performance-Tuning).

        Läuft die Engine-Pipeline NUR wenn ein neuer Bar verfügbar ist.
        Bei gleichen Bars: nur lightweight SL/TP Bar Update.
        """
        if self._context_builder:
            # Get current symbol from bot config
            config = self._get_current_config()

            # Performance: Prüfe ob neuer Bar existiert
            asyncio.create_task(
                self._check_and_run_pipeline(
                    symbol=config.symbol,
                    timeframe=self._pipeline_timeframe,
                )
            )

        # Phase 5: Status Panel auch aktualisieren wenn sichtbar
        if self._status_panel and self._status_panel.isVisible():
            self._update_status_panel()

    async def _check_and_run_pipeline(self, symbol: str, timeframe: str) -> None:
        """Prüft ob neuer Bar existiert und startet Pipeline nur dann (Performance).

        Args:
            symbol: Trading-Symbol (z.B. "BTCUSDT")
            timeframe: Zeiteinheit (z.B. "1m", "5m", "15m")
        """
        try:
            # Check if new bar exists
            has_new_bar = await self._has_new_bar(symbol, timeframe)

            if has_new_bar:
                # Neuer Bar → Full Pipeline ausführen
                logger.debug(f"New bar detected at {symbol} {timeframe} - running pipeline")
                await self._process_market_data_through_engines(
                    symbol=symbol,
                    timeframe=timeframe,
                )
            else:
                # Kein neuer Bar → nur lightweight P&L Update
                if self._current_position and self._last_market_context:
                    # Get latest tick price for P&L update
                    if self._history_manager:
                        df = await self._history_manager.get_historical_data(
                            symbol=symbol,
                            timeframe="1s",  # Latest tick
                            limit=1,
                        )
                        if df is not None and not df.empty and 'close' in df.columns:
                            current_price = float(df['close'].iloc[-1])
                            self._update_sltp_bar(current_price)
        except Exception as e:
            logger.exception(f"Failed to check and run pipeline: {e}")

    async def _has_new_bar(self, symbol: str, timeframe: str) -> bool:
        """Prüft ob ein neuer Bar vorhanden ist (Performance-Optimierung).

        Args:
            symbol: Trading-Symbol
            timeframe: Zeiteinheit

        Returns:
            True wenn neuer Bar existiert, False sonst
        """
        try:
            if not self._history_manager:
                return False

            # Get latest 2 bars
            df = await self._history_manager.get_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                limit=2,
            )

            if df is None or df.empty or 'time' not in df.columns:
                return False

            # Get latest bar timestamp
            latest_timestamp = int(df['time'].iloc[-1])

            # Compare with last processed timestamp
            if latest_timestamp != self._last_bar_timestamp:
                self._last_bar_timestamp = latest_timestamp
                logger.debug(f"New bar timestamp: {latest_timestamp} (previous: {self._last_bar_timestamp})")
                return True

            return False
        except Exception as e:
            logger.exception(f"Failed to check for new bar: {e}")
            return False  # Skip pipeline on error

    def _log(self, message: str) -> None:
        """Fügt Log-Nachricht hinzu."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._append_log(f"[{timestamp}] {message}")

    def _append_log(self, message: str) -> None:
        """Fügt Text zum Log hinzu (Thread-sicher)."""
        self.log_text.append(message)
        # Auto-scroll
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    # === Public API ===

    def set_history_manager(self, manager: "HistoryManager") -> None:
        """Setzt den History Manager und verbindet ihn mit dem Adapter.

        Die Engine-Pipeline erhält Marktdaten über den Adapter, der diese
        vom HistoryManager bezieht. Wird für MarketContextBuilder benötigt.
        """
        self._history_manager = manager

        # Connect to adapter for market data access
        if manager and hasattr(self._adapter, 'set_history_manager'):
            self._adapter.set_history_manager(manager)
            logger.info("BotTab.set_history_manager: Connected HistoryManager to PaperAdapter")
            self._log("✅ HistoryManager verbunden - Marktdaten verfügbar")

    def set_chart_data(
        self,
        data: "pd.DataFrame",
        symbol: str,
        timeframe: str,
    ) -> None:
        """
        Übergibt Chart-Daten an den Bot Engine.

        NOTE: Die neue Engine-Pipeline holt Daten über den HistoryManager.
        Diese Methode bleibt für Kompatibilität, triggert aber ggf. ein
        Pipeline-Update wenn Engines initialisiert sind.

        Args:
            data: DataFrame mit OHLCV-Daten
            symbol: Symbol (z.B. 'BTCUSDT')
            timeframe: Timeframe (z.B. '5m', '1H')
        """
        # Neue Pipeline: Daten werden über _process_market_data_through_engines() verarbeitet
        # Diese Methode bleibt für Chart-Signale, triggert optionales Update
        if self._context_builder and data is not None and not data.empty:
            logger.debug(f"BotTab: Chart data received ({symbol} {timeframe}), pipeline uses HistoryManager")

    def clear_chart_data(self) -> None:
        """Löscht Chart-Daten im Engine (z.B. bei Symbol-Wechsel)."""
        # Neue Pipeline: Cached Context invalidieren
        self._last_market_context = None
        self._last_entry_score = None
        self._last_llm_result = None
        self._last_trigger_result = None
        self._last_leverage_result = None
        logger.debug("BotTab: Chart data cleared, cache invalidated")

    def on_tick_price_updated(self, price: float) -> None:
        """
        Empfängt Live-Tick-Preise vom Chart-Streaming.

        Aktualisiert die Position und refresht die UI (neue Pipeline).

        Args:
            price: Aktueller Marktpreis vom Streaming
        """
        # Neue Pipeline: Position direkt in self._current_position
        if not self._current_position:
            return

        # SL/TP Bar aktualisieren
        self._update_sltp_bar(price)

        # Position P&L aktualisieren
        entry = self._position_entry_price
        side = self._position_side
        qty = self._position_quantity

        if entry > 0 and qty > 0:
            if side == "long":
                pnl = (price - entry) * qty
                pnl_pct = ((price - entry) / entry) * 100
            else:  # short
                pnl = (entry - price) * qty
                pnl_pct = ((entry - price) / entry) * 100

            # P&L Label aktualisieren
            color = "#4CAF50" if pnl >= 0 else "#f44336"
            sign = "+" if pnl >= 0 else ""
            self.sltp_pnl_label.setText(f"P&L: {sign}${pnl:.2f} ({sign}{pnl_pct:.2f}%)")
            self.sltp_pnl_label.setStyleSheet(f"color: {color}; font-size: 11px; margin-top: 5px;")

    def cleanup(self) -> None:
        """Cleanup bei Widget-Zerstörung (App schließt)."""
        self.update_timer.stop()
        # Neue Pipeline: Position direkt speichern
        if self._current_position:
            self._save_position_to_file()
            logger.info("BotTab cleanup: Position saved for next start")
        # Bot-State zurücksetzen
        self._bot_running = False
        logger.debug("BotTab cleanup completed")

    def _save_position_to_file(self) -> bool:
        """Speichert aktive Position in Datei (für Wiederherstellung beim Neustart)."""
        import json
        from pathlib import Path

        position_file = Path("config/trading_bot/active_position.json")
        try:
            position_file.parent.mkdir(parents=True, exist_ok=True)

            if self._current_position:
                # entry_time zu ISO-String konvertieren
                pos_data = self._current_position.copy()
                if "entry_time" in pos_data and hasattr(pos_data["entry_time"], "isoformat"):
                    pos_data["entry_time"] = pos_data["entry_time"].isoformat()

                data = {
                    "position": pos_data,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
                position_file.write_text(json.dumps(data, indent=2))
                logger.info(f"Position saved: {pos_data.get('symbol')} {pos_data.get('side')}")
                return True
            else:
                # Keine Position - Datei löschen falls vorhanden
                if position_file.exists():
                    position_file.unlink()
                    logger.debug("No position to save, removed old file")
                return True

        except Exception as e:
            logger.error(f"Failed to save position: {e}")
            return False

    def _restore_saved_position(self) -> None:
        """Issue #20: Stellt gespeicherte Position beim Start wieder her."""
        import json
        from pathlib import Path
        from datetime import datetime

        position_file = Path("config/trading_bot/active_position.json")

        try:
            if not position_file.exists():
                logger.debug("BotTab: No saved position file found")
                return

            data = json.loads(position_file.read_text())
            position_data = data.get("position")

            if not position_data:
                logger.debug("BotTab: Saved position file is empty")
                return

            # Position wiederherstellen
            self._current_position = position_data

            # entry_time von ISO-String zurück konvertieren
            if "entry_time" in self._current_position:
                entry_time_str = self._current_position["entry_time"]
                if isinstance(entry_time_str, str):
                    self._current_position["entry_time"] = datetime.fromisoformat(entry_time_str)

            # UI-Variablen setzen
            self._position_entry_price = position_data.get("entry_price", 0)
            self._position_side = position_data.get("side", "long")
            self._position_quantity = position_data.get("quantity", 0)
            self._position_stop_loss = position_data.get("stop_loss")
            self._position_take_profit = position_data.get("take_profit")

            self._log("📂 Gespeicherte Position wiederhergestellt")
            logger.info(
                f"BotTab: Restored saved position: {position_data.get('symbol')} "
                f"{position_data.get('side')} @ {position_data.get('entry_price')}"
            )

            # UI aktualisieren
            self._update_display()

            # SL/TP Bar anzeigen
            if self._position_entry_price:
                self.sltp_container.setVisible(True)
                self._update_sltp_bar(self._position_entry_price)

            # Position-Datei nach erfolgreichem Laden löschen (wird beim nächsten Save neu erstellt)
            position_file.unlink()
            logger.debug("BotTab: Removed position file after successful restore")

        except Exception as e:
            logger.warning(f"BotTab: Failed to restore saved position: {e}")
            self._log(f"⚠️ Position konnte nicht wiederhergestellt werden: {e}")
