"""Bot Tab Main - Main Orchestrator for Bot Trading Tab.

Refactored from 850 LOC using further composition pattern (second-level split).

Module 3/3 of bot_tab_main.py second-level split (Main Orchestrator).

Thin orchestration layer that ties all modules together:
- Instantiates UI Manager, Control Manager, Display Updates, Settings Dialog
- Connects signals between UI and control logic
- Provides public API for external integration
- Manages timers and lifecycle
- Delegates button clicks and updates to helpers
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QTextCursor
from PyQt6.QtWidgets import (
    QDialog,
    QMessageBox,
    QWidget,
)

if TYPE_CHECKING:
    import pandas as pd

    from src.core.broker.bitunix_paper_adapter import BitunixPaperAdapter
    from src.core.market_data.history_provider import HistoryManager
    from src.core.trading_bot import (
        BotConfig,
        BotState,
        BotStatistics,
        EntryScoreEngine,
        LevelEngine,
        LeverageRulesEngine,
        LLMValidationService,
        MarketContext,
        MarketContextBuilder,
        MonitoredPosition,
        RegimeDetectorService,
        TradeSignal,
        TriggerExitEngine,
    )

from src.core.trading_bot import BotConfig

# Import helper modules
from .bot_tab_ui import BotTabUI
from .bot_tab_control import BotTabControl
from .bot_tab_display_updates import BotTabDisplayUpdates
from .bot_tab_modules import BotSettingsDialog

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

logger = logging.getLogger(__name__)

# Pfad für persistente Bot-Einstellungen
BOT_SETTINGS_FILE = Path("config/bot_settings.json")


class BotTab(QWidget):
    """
    Bot Trading Tab - Main Orchestrator.

    Zeigt:
    - Bot Status und Steuerung
    - Aktuelles Signal
    - Offene Position mit SL/TP
    - Tagesstatistiken
    - Live Log

    Architektur:
    - BotTabUI: UI Creation & Layout
    - BotTabControl: Engine Pipeline & Position Management
    - BotTabDisplayUpdates: Display Update Methods
    - BotSettingsDialog: Settings Dialog (separate module)
    - BotTab (this): Thin Orchestrator
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
        self._is_initialized = False
        self._bot_running = False

        # Phase 1-4: New Engines (initialized on demand by control manager)
        self._context_builder: "MarketContextBuilder | None" = None
        self._regime_detector: "RegimeDetectorService | None" = None
        self._level_engine: "LevelEngine | None" = None
        self._entry_score_engine: "EntryScoreEngine | None" = None
        self._llm_validation: "LLMValidationService | None" = None
        self._trigger_exit_engine: "TriggerExitEngine | None" = None
        self._leverage_engine: "LeverageRulesEngine | None" = None

        # Latest engine results (for Status Panel display)
        self._last_market_context: "MarketContext | None" = None
        self._last_regime_result = None
        self._last_levels_result = None
        self._last_entry_score = None
        self._last_llm_result = None
        self._last_trigger_result = None
        self._last_leverage_result = None

        # Current open position (managed by control manager)
        self._current_position: dict | None = None
        self._position_entry_price: float = 0.0
        self._position_side: str = ""  # "long" or "short"
        self._position_quantity: float = 0.0
        self._position_stop_loss: float = 0.0
        self._position_take_profit: float = 0.0

        # Performance: Pipeline nur bei neuen Bars ausführen
        self._last_bar_timestamp: int = 0
        self._pipeline_timeframe: str = "1m"  # Einstellbar: "1m", "5m", "15m", etc.

        # Connect history_manager to adapter for market data access
        if history_manager and hasattr(paper_adapter, 'set_history_manager'):
            paper_adapter.set_history_manager(history_manager)
            logger.info("BotTab: Connected HistoryManager to PaperAdapter")

        # Instantiate helper managers
        self.ui_manager = BotTabUI(self)
        self.control_manager = BotTabControl(self)
        self.display_updates = BotTabDisplayUpdates(self)

        # Setup UI, signals, timers (delegates to managers)
        self.ui_manager.setup_ui()
        self._setup_signals()
        self._setup_timers()

        # Phase 5: Trading Status Panel (if available)
        if HAS_STATUS_PANEL:
            self._status_panel = TradingStatusPanel()
            self._status_panel.setVisible(False)
            self._status_panel.refresh_requested.connect(self.control_manager.on_status_panel_refresh)
            # Add to layout after ui_manager setup
            self.layout().addWidget(self._status_panel)
        else:
            self._status_panel = None

        # Phase 5.4: Trading Journal (if available)
        if HAS_JOURNAL:
            self._journal_widget = TradingJournalWidget()
            self._journal_widget.setVisible(False)
            # Add to layout after ui_manager setup
            self.layout().addWidget(self._journal_widget)
        else:
            self._journal_widget = None

        # Restore saved position from previous session
        self.control_manager.restore_saved_position()

    def _setup_signals(self) -> None:
        """Verbindet alle Signals mit ihren Slots."""
        # Button Signals (delegate to control manager)
        self.start_btn.clicked.connect(self.control_manager.on_start_clicked)
        self.stop_btn.clicked.connect(self.control_manager.on_stop_clicked)
        self.close_position_btn.clicked.connect(self.control_manager.on_close_position_clicked)
        self.settings_btn.clicked.connect(self._handle_settings_click)

        # Toggle buttons (delegate to control manager)
        self.status_panel_btn.clicked.connect(self.control_manager.toggle_status_panel)
        self.journal_btn.clicked.connect(self.control_manager.toggle_journal)

        # Internal Signals for thread-safe UI updates (delegate to display_updates)
        self.status_changed.connect(self._update_status_display)
        self.signal_updated.connect(self._update_signal_display)
        self.position_updated.connect(self._update_position_display)
        self.stats_updated.connect(self._update_stats_display)
        self.log_message.connect(self._append_log)

    def _setup_timers(self) -> None:
        """Erstellt Timer für periodische Updates."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.control_manager.periodic_update)
        self.update_timer.setInterval(1000)  # 1 Sekunde

    # === Settings Dialog ===

    def _handle_settings_click(self) -> None:
        """Handler für Settings-Button mit Debug-Output."""
        print("=" * 50)
        print("DEBUG: Settings button was clicked!")
        print("=" * 50)
        # Visuelle Bestätigung dass Button geklickt wurde
        self.settings_btn.setText("...")
        self.settings_btn.repaint()
        try:
            self._on_settings_clicked()
        finally:
            self.settings_btn.setText("⚙")

    @pyqtSlot()
    def _on_settings_clicked(self) -> None:
        """Öffnet Settings Dialog."""
        print("DEBUG: _on_settings_clicked() called")
        logger.info("Settings button clicked!")
        self.control_manager._log("⚙ Öffne Einstellungen...")
        try:
            print("DEBUG: Getting config...")
            config = self.control_manager._get_current_config()
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
                self.control_manager.apply_config(new_config)
                self.control_manager._log("⚙ Einstellungen aktualisiert")
            else:
                self.control_manager._log("⚙ Einstellungen abgebrochen")
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            import traceback

            traceback.print_exc()
            logger.exception("Settings dialog error")
            self.control_manager._log(f"❌ Settings Fehler: {e}")
            QMessageBox.critical(self, "Fehler", f"Settings konnten nicht geöffnet werden:\n{e}")

    # === UI Updates (Thread-safe via Signals, delegated to display_updates) ===

    def _update_status_display(self, state: str) -> None:
        """Aktualisiert Status-Anzeige (delegiert zu display_updates)."""
        self.display_updates.update_status_display(state)

    def _update_signal_display(self, signal: "TradeSignal | None") -> None:
        """Aktualisiert Signal-Anzeige (delegiert zu display_updates)."""
        self.display_updates.update_signal_display(signal)

    def _update_position_display(self, position: "MonitoredPosition | None") -> None:
        """Aktualisiert Position-Anzeige (delegiert zu display_updates)."""
        self.display_updates.update_position_display(position)

    def _update_stats_display(self, stats: "BotStatistics") -> None:
        """Aktualisiert Statistik-Anzeige (delegiert zu display_updates)."""
        self.display_updates.update_stats_display(stats)

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
            self.control_manager._log("✅ HistoryManager verbunden - Marktdaten verfügbar")

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
        # Neue Pipeline: Daten werden über control_manager.process_market_data_through_engines() verarbeitet
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

        # SL/TP Bar aktualisieren (delegate to control manager)
        self.control_manager._update_sltp_bar(price)

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

    def update_engine_configs(self) -> None:
        """Aktualisiert die Konfiguration aller laufenden Engines (delegate to control)."""
        self.control_manager.update_engine_configs()

    def cleanup(self) -> None:
        """Cleanup bei Widget-Zerstörung (App schließt)."""
        self.control_manager.cleanup()
