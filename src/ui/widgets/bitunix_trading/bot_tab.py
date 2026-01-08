"""
Bot Tab - UI Widget für den Trading Bot

Integriert den TradingBotEngine in das Bitunix Trading Widget als Tab.

Features:
- Start/Stop Steuerung
- Live Status-Anzeige (State, Signal, Position)
- Statistiken (Trades, Win Rate, PnL)
- Log-Viewer mit Echtzeit-Updates
- Settings Dialog
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
    TradingBotEngine,
    BotState,
    BotConfig,
    BotStatistics,
    SignalDirection,
    TradeSignal,
    MonitoredPosition,
    ExitResult,
    TradeLogEntry,
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
        self._bot_engine: TradingBotEngine | None = None
        self._is_initialized = False

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
        """Startet den Bot."""
        if self._bot_engine and self._bot_engine.state != BotState.IDLE:
            return

        try:
            self._log("🚀 Starte Trading Bot...")

            # Bot Engine erstellen wenn nötig
            if not self._bot_engine:
                self._initialize_bot_engine()

            # Bot starten
            await self._bot_engine.start()

            # UI aktualisieren
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.update_timer.start()

            self._log("✅ Bot gestartet!")

        except Exception as e:
            self._log(f"❌ Fehler beim Starten: {e}")
            logger.exception("Bot start failed")
            QMessageBox.critical(self, "Fehler", f"Bot konnte nicht gestartet werden:\n{e}")

    @qasync.asyncSlot()
    async def _on_stop_clicked(self) -> None:
        """Stoppt den Bot."""
        if not self._bot_engine:
            return

        try:
            self._log("⏹ Stoppe Trading Bot...")

            # Bot stoppen
            await self._bot_engine.stop()

            # UI aktualisieren
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.update_timer.stop()

            self._log("✅ Bot gestoppt!")

        except Exception as e:
            self._log(f"❌ Fehler beim Stoppen: {e}")
            logger.exception("Bot stop failed")

    @qasync.asyncSlot()
    async def _on_close_position_clicked(self) -> None:
        """Schließt die aktuelle Position manuell."""
        if not self._bot_engine:
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
                await self._bot_engine.manual_close_position()
                self._log("✅ Position geschlossen!")
            except Exception as e:
                self._log(f"❌ Fehler: {e}")

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
        """Aktualisiert das Status Panel mit aktuellen Engine-Ergebnissen."""
        if not self._status_panel or not self._bot_engine:
            return

        try:
            # Hole letzte Engine-Ergebnisse wenn verfügbar
            engine = self._bot_engine

            # Regime-Ergebnis (falls im Engine gecached)
            regime_result = getattr(engine, '_last_regime_result', None)

            # Entry Score (falls vorhanden)
            score_result = getattr(engine, '_last_entry_score', None)

            # LLM Validation (falls vorhanden)
            llm_result = getattr(engine, '_last_llm_result', None)

            # Trigger Result (falls vorhanden)
            trigger_result = getattr(engine, '_last_trigger_result', None)

            # Leverage Result (falls vorhanden)
            leverage_result = getattr(engine, '_last_leverage_result', None)

            # Update all at once
            self._status_panel.update_all(
                regime_result=regime_result,
                score_result=score_result,
                llm_result=llm_result,
                trigger_result=trigger_result,
                leverage_result=leverage_result,
            )
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

    def _log_signal_to_journal(self, signal: TradeSignal) -> None:
        """Loggt ein Signal ins Journal."""
        if not self._journal_widget:
            return

        signal_data = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "symbol": getattr(self._bot_engine, '_config', {}).symbol if self._bot_engine else "-",
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

        llm_data = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "symbol": getattr(self._bot_engine, '_config', {}).symbol if self._bot_engine else "-",
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

    def _initialize_bot_engine(self) -> None:
        """Initialisiert die Bot Engine."""
        from src.core.trading_bot import BotConfig, TradingBotEngine

        config = self._get_current_config()
        self._bot_engine = TradingBotEngine(
            adapter=self._adapter,
            config=config,
        )

        # Callbacks registrieren
        self._bot_engine.set_state_callback(self._on_state_changed)
        self._bot_engine.set_signal_callback(self._on_signal_updated)
        self._bot_engine.set_position_opened_callback(self._on_position_opened)
        self._bot_engine.set_position_closed_callback(self._on_position_closed)
        self._bot_engine.set_error_callback(self._on_bot_error)
        self._bot_engine.set_log_callback(self._on_bot_log)

        self._is_initialized = True
        self._log("✅ Bot Engine initialisiert")

        # Issue #20: Versuche gespeicherte Position wiederherzustellen
        self._restore_saved_position()

    def _get_current_config(self) -> BotConfig:
        """Gibt aktuelle Bot-Konfiguration zurück (lädt aus Datei wenn vorhanden)."""
        return self._load_settings()

    def _apply_config(self, config: BotConfig) -> None:
        """Wendet neue Konfiguration an und speichert sie."""
        self._save_settings(config)
        if self._bot_engine:
            self._bot_engine.update_config(config)

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
        # Statistiken aktualisieren
        if self._bot_engine:
            self.stats_updated.emit(self._bot_engine.statistics)

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
        """Periodisches UI Update."""
        if self._bot_engine:
            # Force refresh stats
            self.stats_updated.emit(self._bot_engine.statistics)

            # Phase 5: Status Panel auch aktualisieren wenn sichtbar
            if self._status_panel and self._status_panel.isVisible():
                self._update_status_panel()

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

        Der TradingBotEngine erhält Marktdaten über den Adapter, der diese
        vom HistoryManager bezieht.
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

        Wird aufgerufen wenn der Chart neue Daten lädt. Der Bot verwendet
        diese Daten anstatt eigene API-Calls zu machen.

        Args:
            data: DataFrame mit OHLCV-Daten
            symbol: Symbol (z.B. 'BTCUSDT')
            timeframe: Timeframe (z.B. '5m', '1H')
        """
        if self._bot_engine:
            self._bot_engine.set_chart_data(data, symbol, timeframe)
            logger.debug(f"BotTab: Chart data forwarded to engine ({symbol} {timeframe})")

    def clear_chart_data(self) -> None:
        """Löscht Chart-Daten im Engine (z.B. bei Symbol-Wechsel)."""
        if self._bot_engine:
            self._bot_engine.clear_chart_data()

    def on_tick_price_updated(self, price: float) -> None:
        """
        Empfängt Live-Tick-Preise vom Chart-Streaming.

        Aktualisiert die Position im Bot Engine und refresht die UI.

        Args:
            price: Aktueller Marktpreis vom Streaming
        """
        if not self._bot_engine:
            return

        # Nur updaten wenn Bot läuft und Position offen ist
        if self._bot_engine.state != BotState.IN_POSITION:
            return

        # Price Update an Engine senden (async)
        from decimal import Decimal
        asyncio.create_task(
            self._bot_engine.on_price_update(Decimal(str(price)))
        )

        # UI aktualisieren - Position vom Monitor holen
        if self._bot_engine.position_monitor.has_position:
            position = self._bot_engine.position_monitor.position
            if position:
                # current_price aktualisieren
                position.current_price = Decimal(str(price))
                self.position_updated.emit(position)

    def cleanup(self) -> None:
        """Cleanup bei Widget-Zerstörung (App schließt)."""
        self.update_timer.stop()
        if self._bot_engine:
            # Position speichern, NICHT schließen!
            if self._bot_engine.has_position:
                self._bot_engine.save_position()
                logger.info("BotTab cleanup: Position saved for next start")
            # Bot stoppen (Position ist bereits gespeichert)
            asyncio.create_task(self._bot_engine.stop(close_position=False))

    def _restore_saved_position(self) -> None:
        """Issue #20: Stellt gespeicherte Position beim Start wieder her."""
        if not self._bot_engine:
            return

        try:
            # Versuche Position zu laden
            if self._bot_engine.load_position():
                self._log("📂 Gespeicherte Position wiederhergestellt")
                logger.info("BotTab: Restored saved position on startup")
                # UI aktualisieren
                self._update_display()
            else:
                logger.debug("BotTab: No saved position found to restore")
        except Exception as e:
            logger.warning(f"BotTab: Failed to restore saved position: {e}")
            self._log(f"⚠️ Position konnte nicht wiederhergestellt werden: {e}")


class BotSettingsDialog(QDialog):
    """Tab-basierter Dialog für Bot-Einstellungen.

    Tabs:
    - Basic: Grundeinstellungen (Risk, SL/TP, Signal, AI)
    - Entry Score: Gewichte und Quality Thresholds
    - Trigger/Exit: SL/TP-Modi, Trailing
    - Leverage: Tiers, Regime-Anpassung, Safety
    - LLM Validation: Thresholds, Modifiers
    - Levels: Level-Detection Settings
    """

    def __init__(self, config: BotConfig, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("⚙ Trading Bot Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        self._config = config
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Erstellt das Tab-basierte Dialog-Layout."""
        layout = QVBoxLayout(self)

        # Tab Widget für verschiedene Settings-Bereiche
        tabs = QTabWidget()

        # Tab 1: Basic Settings (bisherige Inhalte)
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        self._create_basic_settings(basic_layout)
        tabs.addTab(basic_tab, "⚙ Basic")

        # Tab 2-6: Engine Settings (nur wenn verfügbar)
        if HAS_ENGINE_SETTINGS:
            self._entry_score_widget = EntryScoreSettingsWidget()
            tabs.addTab(self._entry_score_widget, "📊 Entry Score")

            self._trigger_exit_widget = TriggerExitSettingsWidget()
            tabs.addTab(self._trigger_exit_widget, "🎯 Trigger/Exit")

            self._leverage_widget = LeverageSettingsWidget()
            tabs.addTab(self._leverage_widget, "⚡ Leverage")

            self._llm_widget = LLMValidationSettingsWidget()
            tabs.addTab(self._llm_widget, "🤖 LLM Validation")

            self._levels_widget = LevelSettingsWidget()
            tabs.addTab(self._levels_widget, "📈 Levels")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        if HAS_ENGINE_SETTINGS:
            apply_all_btn = QPushButton("Alle übernehmen")
            apply_all_btn.clicked.connect(self._apply_all_engine_settings)
            button_layout.addWidget(apply_all_btn)

            save_all_btn = QPushButton("Alle speichern")
            save_all_btn.clicked.connect(self._save_all_engine_settings)
            button_layout.addWidget(save_all_btn)

        button_layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        button_layout.addWidget(buttons)

        layout.addLayout(button_layout)

    def _create_basic_settings(self, layout: QVBoxLayout) -> None:
        """Erstellt die Basic Settings (bisheriger Dialog-Inhalt)."""

        # Risk Management - KEINE Begrenzungen, User entscheidet
        risk_group = QGroupBox("Risk Management")
        risk_layout = QFormLayout(risk_group)

        self.risk_spin = QDoubleSpinBox()
        self.risk_spin.setRange(0.1, 100.0)  # Bis 100% möglich
        self.risk_spin.setSingleStep(0.5)
        self.risk_spin.setValue(float(self._config.risk_per_trade_percent))
        self.risk_spin.setSuffix(" %")
        risk_layout.addRow("Risiko pro Trade:", self.risk_spin)

        self.daily_loss_spin = QDoubleSpinBox()
        self.daily_loss_spin.setRange(0.1, 100.0)  # Bis 100% möglich
        self.daily_loss_spin.setSingleStep(1.0)
        self.daily_loss_spin.setValue(float(self._config.max_daily_loss_percent))
        self.daily_loss_spin.setSuffix(" %")
        risk_layout.addRow("Max. Tagesverlust:", self.daily_loss_spin)

        layout.addWidget(risk_group)

        # SL/TP - Erweiterte Ranges
        sltp_group = QGroupBox("SL/TP (ATR Multiplikator)")
        sltp_layout = QFormLayout(sltp_group)

        self.sl_spin = QDoubleSpinBox()
        self.sl_spin.setRange(0.1, 100.0)  # Flexibel
        self.sl_spin.setSingleStep(0.1)
        self.sl_spin.setValue(float(self._config.sl_atr_multiplier))
        self.sl_spin.setSuffix(" x ATR")
        sltp_layout.addRow("Stop Loss:", self.sl_spin)

        self.tp_spin = QDoubleSpinBox()
        self.tp_spin.setRange(0.1, 100.0)  # Flexibel
        self.tp_spin.setSingleStep(0.1)
        self.tp_spin.setValue(float(self._config.tp_atr_multiplier))
        self.tp_spin.setSuffix(" x ATR")
        sltp_layout.addRow("Take Profit:", self.tp_spin)

        self.trailing_check = QCheckBox("Trailing Stop aktivieren")
        self.trailing_check.setChecked(self._config.trailing_stop_enabled)
        sltp_layout.addRow(self.trailing_check)

        self.trailing_spin = QDoubleSpinBox()
        self.trailing_spin.setRange(0.1, 100.0)  # Flexibel
        self.trailing_spin.setSingleStep(0.1)
        self.trailing_spin.setValue(float(self._config.trailing_stop_atr_multiplier))
        self.trailing_spin.setSuffix(" x ATR")
        sltp_layout.addRow("Trailing Abstand:", self.trailing_spin)

        layout.addWidget(sltp_group)

        # Signal - Erweiterte Ranges
        signal_group = QGroupBox("Signal-Einstellungen")
        signal_layout = QFormLayout(signal_group)

        self.confluence_spin = QSpinBox()
        self.confluence_spin.setRange(1, 10)  # Flexibel
        self.confluence_spin.setValue(self._config.min_confluence_score)
        signal_layout.addRow("Min. Confluence:", self.confluence_spin)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)  # 1 Sek bis 1 Stunde
        self.interval_spin.setValue(self._config.analysis_interval_seconds)
        self.interval_spin.setSuffix(" Sek")
        signal_layout.addRow("Analyse-Intervall:", self.interval_spin)

        layout.addWidget(signal_group)

        # AI - Erweiterte Ranges
        ai_group = QGroupBox("AI Validation")
        ai_layout = QFormLayout(ai_group)

        self.ai_check = QCheckBox("AI Validation aktivieren")
        self.ai_check.setChecked(self._config.ai.enabled)
        ai_layout.addRow(self.ai_check)

        self.ai_threshold_spin = QSpinBox()
        self.ai_threshold_spin.setRange(0, 100)  # 0-100%
        self.ai_threshold_spin.setValue(self._config.ai.confidence_threshold)
        self.ai_threshold_spin.setSuffix(" %")
        ai_layout.addRow("Min. Confidence:", self.ai_threshold_spin)

        self.ai_provider_combo = QComboBox()
        self.ai_provider_combo.addItems(["openai", "anthropic", "gemini"])
        self.ai_provider_combo.setCurrentText(self._config.ai.provider)
        ai_layout.addRow("Provider:", self.ai_provider_combo)

        layout.addWidget(ai_group)

    def _apply_all_engine_settings(self) -> None:
        """Wendet alle Engine-Settings an ohne zu speichern."""
        if HAS_ENGINE_SETTINGS:
            self._entry_score_widget.apply_settings()
            self._trigger_exit_widget.apply_settings()
            self._leverage_widget.apply_settings()
            self._llm_widget.apply_settings()
            self._levels_widget.apply_settings()
            QMessageBox.information(self, "Settings Applied", "All engine settings have been applied.")

    def _save_all_engine_settings(self) -> None:
        """Speichert alle Engine-Settings."""
        if HAS_ENGINE_SETTINGS:
            self._entry_score_widget.save_settings()
            self._trigger_exit_widget.save_settings()
            self._leverage_widget.save_settings()
            self._llm_widget.save_settings()
            self._levels_widget.save_settings()
            QMessageBox.information(self, "Settings Saved", "All engine settings have been saved.")

    def get_config(self) -> BotConfig:
        """Gibt die aktualisierten Einstellungen zurück."""
        from decimal import Decimal
        from src.core.trading_bot import AIConfig

        return BotConfig(
            symbol=self._config.symbol,
            # paper_mode ist eine Property, nicht setzen
            risk_per_trade_percent=Decimal(str(self.risk_spin.value())),
            max_daily_loss_percent=Decimal(str(self.daily_loss_spin.value())),
            sl_atr_multiplier=Decimal(str(self.sl_spin.value())),
            tp_atr_multiplier=Decimal(str(self.tp_spin.value())),
            trailing_stop_enabled=self.trailing_check.isChecked(),
            trailing_stop_atr_multiplier=Decimal(str(self.trailing_spin.value())),
            min_confluence_score=self.confluence_spin.value(),
            analysis_interval_seconds=self.interval_spin.value(),
            ai=AIConfig(
                enabled=self.ai_check.isChecked(),
                confidence_threshold=self.ai_threshold_spin.value(),
                provider=self.ai_provider_combo.currentText(),
            ),
        )
