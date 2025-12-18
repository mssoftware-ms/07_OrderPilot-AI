"""Bot Panels Mixin for ChartWindow.

Provides additional tabs for tradingbot control and monitoring:
- Bot Control (Start/Stop, Settings)
- Daily Strategy Selection
- Signals & Trade Management
- KI Logs
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal, QSettings
from PyQt6.QtGui import QColor, QDesktopServices, QAction
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from src.core.tradingbot import BotController, FullBotConfig

logger = logging.getLogger(__name__)


class BotPanelsMixin:
    """Mixin providing bot control and monitoring panels."""

    # Signals for bot events
    bot_started = pyqtSignal()
    bot_stopped = pyqtSignal()
    bot_config_changed = pyqtSignal(object)

    def _init_bot_panels(self) -> None:
        """Initialize bot panel state."""
        self._bot_controller: BotController | None = None
        self._bot_update_timer: QTimer | None = None
        self._ki_log_entries: list[dict] = []
        self._signal_history: list[dict] = []
        self._trade_history: list[dict] = []
        self._current_bot_symbol: str = ""  # Track current symbol for settings
        self._bot_settings = QSettings("OrderPilot", "TradingApp")

        # Initialize settings manager
        from src.core.tradingbot.bot_settings_manager import get_bot_settings_manager
        self._bot_settings_manager = get_bot_settings_manager()

        # Update symbol display and load settings (delayed to ensure UI is ready)
        QTimer.singleShot(100, self.update_bot_symbol)
        # Load signal history after UI is ready
        QTimer.singleShot(200, self._load_signal_history)
        # Connect chart line drag signal (delayed to ensure chart_widget exists)
        QTimer.singleShot(300, self._connect_chart_line_signals)

    def _create_bot_control_tab(self) -> QWidget:
        """Create bot control tab with start/stop and settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # ==================== CONTROL GROUP (full width at top) ====================
        control_group = QGroupBox("Bot Control")
        control_layout = QHBoxLayout()  # Horizontal for compact layout
        control_layout.setContentsMargins(8, 8, 8, 8)

        # Status indicator
        self.bot_status_label = QLabel("Status: STOPPED")
        self.bot_status_label.setStyleSheet(
            "font-weight: bold; color: #9e9e9e; font-size: 14px;"
        )
        control_layout.addWidget(self.bot_status_label)
        control_layout.addStretch()

        # Start/Stop buttons inline
        self.bot_start_btn = QPushButton("Start Bot")
        self.bot_start_btn.setStyleSheet(
            "background-color: #26a69a; color: white; font-weight: bold; "
            "padding: 8px 16px;"
        )
        self.bot_start_btn.clicked.connect(self._on_bot_start_clicked)
        control_layout.addWidget(self.bot_start_btn)

        self.bot_stop_btn = QPushButton("Stop Bot")
        self.bot_stop_btn.setStyleSheet(
            "background-color: #ef5350; color: white; font-weight: bold; "
            "padding: 8px 16px;"
        )
        self.bot_stop_btn.setEnabled(False)
        self.bot_stop_btn.clicked.connect(self._on_bot_stop_clicked)
        control_layout.addWidget(self.bot_stop_btn)

        self.bot_pause_btn = QPushButton("Pause")
        self.bot_pause_btn.setStyleSheet("padding: 8px;")
        self.bot_pause_btn.setEnabled(False)
        self.bot_pause_btn.clicked.connect(self._on_bot_pause_clicked)
        control_layout.addWidget(self.bot_pause_btn)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # ==================== SETTINGS GROUP ====================
        settings_group = QGroupBox("Bot Settings")
        settings_layout = QFormLayout()

        # Symbol (read from chart)
        self.bot_symbol_label = QLabel("-")
        self.bot_symbol_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        settings_layout.addRow("Symbol:", self.bot_symbol_label)

        # KI Mode
        self.ki_mode_combo = QComboBox()
        self.ki_mode_combo.addItems(["NO_KI", "LOW_KI", "FULL_KI"])
        self.ki_mode_combo.setCurrentIndex(0)
        self.ki_mode_combo.currentTextChanged.connect(self._on_ki_mode_changed)
        self.ki_mode_combo.setToolTip(
            "KI Mode:\n"
            "• NO_KI: Rein regelbasiert, kein LLM-Call\n"
            "• LOW_KI: Daily Strategy Selection (1 Call/Tag)\n"
            "• FULL_KI: Daily + Intraday Events (RegimeFlip, Exit, Signal)"
        )
        settings_layout.addRow("KI Mode:", self.ki_mode_combo)

        # Trailing Mode
        self.trailing_mode_combo = QComboBox()
        self.trailing_mode_combo.addItems(["PCT", "ATR", "SWING"])
        self.trailing_mode_combo.setCurrentIndex(0)
        self.trailing_mode_combo.setToolTip(
            "Trailing Stop Mode:\n"
            "• PCT: Fester Prozent-Abstand vom aktuellen Kurs\n"
            "• ATR: Volatilitäts-basiert (ATR-Multiple), Regime-angepasst\n"
            "• SWING: Bollinger Bands als Support/Resistance"
        )
        self.trailing_mode_combo.currentTextChanged.connect(self._on_trailing_mode_changed)
        settings_layout.addRow("Trailing Mode:", self.trailing_mode_combo)

        # Initial Stop Loss %
        self.initial_sl_spin = QDoubleSpinBox()
        self.initial_sl_spin.setRange(0.1, 10.0)
        self.initial_sl_spin.setValue(2.0)
        self.initial_sl_spin.setSuffix(" %")
        self.initial_sl_spin.setDecimals(2)
        self.initial_sl_spin.setToolTip(
            "Initial Stop-Loss in Prozent vom Entry-Preis.\n"
            "Dies ist der EINZIGE fixe Parameter - alle anderen Exits sind dynamisch.\n"
            "Empfohlen: 1.5-3% für Aktien, 2-5% für Crypto."
        )
        settings_layout.addRow("Initial SL %:", self.initial_sl_spin)

        # Account capital for bot
        self.bot_capital_spin = QDoubleSpinBox()
        self.bot_capital_spin.setRange(100, 10000000)
        self.bot_capital_spin.setValue(10000)
        self.bot_capital_spin.setPrefix("€")
        self.bot_capital_spin.setDecimals(0)
        self.bot_capital_spin.setToolTip(
            "Verfügbares Kapital für den Bot.\n"
            "Basis für Positionsgrößen-Berechnung und P&L%."
        )
        settings_layout.addRow("Kapital:", self.bot_capital_spin)

        # Risk per trade %
        self.risk_per_trade_spin = QDoubleSpinBox()
        self.risk_per_trade_spin.setRange(0.1, 100.0)
        self.risk_per_trade_spin.setValue(10.0)
        self.risk_per_trade_spin.setSuffix(" %")
        self.risk_per_trade_spin.setDecimals(2)
        self.risk_per_trade_spin.setToolTip(
            "Prozent des Kapitals, das pro Trade investiert wird.\n"
            "Beispiel: 10.000€ Kapital × 10% = 1.000€ pro Trade.\n"
            "P&L% wird auf diesen Betrag berechnet."
        )
        settings_layout.addRow("Risk/Trade %:", self.risk_per_trade_spin)

        # Max daily trades
        self.max_trades_spin = QSpinBox()
        self.max_trades_spin.setRange(1, 50)
        self.max_trades_spin.setValue(10)
        settings_layout.addRow("Max Trades/Day:", self.max_trades_spin)

        # Max daily loss %
        self.max_daily_loss_spin = QDoubleSpinBox()
        self.max_daily_loss_spin.setRange(0.5, 10.0)
        self.max_daily_loss_spin.setValue(3.0)
        self.max_daily_loss_spin.setSuffix(" %")
        self.max_daily_loss_spin.setDecimals(2)
        settings_layout.addRow("Max Daily Loss %:", self.max_daily_loss_spin)

        # Disable restrictions checkbox (for paper trading)
        self.disable_restrictions_cb = QCheckBox("Restriktionen deaktivieren")
        self.disable_restrictions_cb.setChecked(True)  # Default: checked for paper mode
        self.disable_restrictions_cb.setToolTip(
            "Deaktiviert Max Trades/Day und Max Daily Loss Limits.\n"
            "Empfohlen für Paper Trading und Strategie-Tests.\n"
            "⚠️ Im Live-Modus sollten Restriktionen AKTIVIERT sein!"
        )
        self.disable_restrictions_cb.setStyleSheet(
            "color: #ff9800; font-weight: bold;"
        )
        settings_layout.addRow("Paper Mode:", self.disable_restrictions_cb)

        # Disable MACD exit checkbox
        self.disable_macd_exit_cb = QCheckBox("MACD-Exit deaktivieren")
        self.disable_macd_exit_cb.setChecked(False)
        self.disable_macd_exit_cb.setToolTip(
            "Deaktiviert den automatischen Verkauf bei MACD-Kreuzungen.\n"
            "Position wird nur durch Stop-Loss geschlossen.\n"
            "MACD-Signale werden trotzdem im Chart angezeigt."
        )
        settings_layout.addRow("Stop-Loss Only:", self.disable_macd_exit_cb)

        settings_group.setLayout(settings_layout)

        # ==================== TRAILING STOP SETTINGS ====================
        trailing_group = QGroupBox("Trailing Stop Settings")
        trailing_layout = QFormLayout()

        # Regime-Adaptive checkbox
        self.regime_adaptive_cb = QCheckBox("Regime-Adaptiv")
        self.regime_adaptive_cb.setChecked(True)
        self.regime_adaptive_cb.setToolTip(
            "Passt ATR-Multiplier automatisch an Marktregime an:\n"
            "• Trending (ADX > 25): Engerer Stop (mehr Gewinn mitnehmen)\n"
            "• Ranging (ADX < 20): Weiterer Stop (weniger Whipsaws)"
        )
        self.regime_adaptive_cb.stateChanged.connect(self._on_regime_adaptive_changed)
        trailing_layout.addRow("Adaptive:", self.regime_adaptive_cb)

        # Trailing Activation Threshold
        self.trailing_activation_spin = QDoubleSpinBox()
        self.trailing_activation_spin.setRange(0.0, 100.0)
        self.trailing_activation_spin.setValue(0.0)
        self.trailing_activation_spin.setSingleStep(1.0)
        self.trailing_activation_spin.setDecimals(1)
        self.trailing_activation_spin.setSuffix(" %")
        self.trailing_activation_spin.setToolTip(
            "Ab welchem GEWINN (Return on Risk) der Trailing Stop aktiviert wird.\n\n"
            "Beispiel bei 100€ Risiko:\n"
            "• 0% = sofort wenn im Gewinn\n"
            "• 10% = Trailing erst ab 10€ Gewinn aktiv\n"
            "• 50% = Trailing erst ab 50€ Gewinn aktiv\n\n"
            "Bis zur Aktivierung gilt nur der Initial Stop Loss (rot)."
        )
        trailing_layout.addRow("Aktivierung ab:", self.trailing_activation_spin)

        # Trailing Stop Distance (PCT mode)
        self.trailing_distance_spin = QDoubleSpinBox()
        self.trailing_distance_spin.setRange(0.1, 10.0)
        self.trailing_distance_spin.setValue(1.5)
        self.trailing_distance_spin.setSingleStep(0.1)
        self.trailing_distance_spin.setDecimals(2)
        self.trailing_distance_spin.setSuffix(" %")
        self.trailing_distance_spin.setToolTip(
            "Abstand des Trailing Stops zum AKTUELLEN Kurs in %.\n\n"
            "Beispiel LONG:\n"
            "• Kurs bei 102€, Abstand 1.5% → Stop bei 100.47€\n"
            "• Kurs steigt auf 105€ → Stop steigt auf 103.43€\n\n"
            "Beispiel SHORT:\n"
            "• Kurs bei 98€, Abstand 1.5% → Stop bei 99.47€\n"
            "• Kurs fällt auf 95€ → Stop fällt auf 96.43€\n\n"
            "Stop bewegt sich NUR in günstige Richtung!"
        )
        trailing_layout.addRow("Abstand (PCT):", self.trailing_distance_spin)

        # ATR Multiplier (fixed, when not adaptive)
        self.atr_multiplier_spin = QDoubleSpinBox()
        self.atr_multiplier_spin.setRange(0.5, 8.0)
        self.atr_multiplier_spin.setValue(2.5)
        self.atr_multiplier_spin.setSingleStep(0.1)
        self.atr_multiplier_spin.setDecimals(2)
        self.atr_multiplier_spin.setToolTip(
            "Fester ATR-Multiplier (wenn Regime-Adaptiv AUS).\n"
            "Stop = Highest High - (ATR × Multiplier)\n"
            "Höher = weiterer Stop, weniger Whipsaws"
        )
        trailing_layout.addRow("ATR Multiplier:", self.atr_multiplier_spin)

        # ATR Trending (for adaptive mode)
        self.atr_trending_spin = QDoubleSpinBox()
        self.atr_trending_spin.setRange(0.5, 5.0)
        self.atr_trending_spin.setValue(2.0)
        self.atr_trending_spin.setSingleStep(0.1)
        self.atr_trending_spin.setDecimals(2)
        self.atr_trending_spin.setToolTip(
            "ATR-Multiplier für TRENDING Märkte (ADX > 25).\n"
            "Niedriger = engerer Stop = mehr Gewinn mitnehmen\n"
            "Empfohlen: 1.5-2.5x"
        )
        trailing_layout.addRow("ATR Trending:", self.atr_trending_spin)

        # ATR Ranging (for adaptive mode)
        self.atr_ranging_spin = QDoubleSpinBox()
        self.atr_ranging_spin.setRange(1.0, 8.0)
        self.atr_ranging_spin.setValue(3.5)
        self.atr_ranging_spin.setSingleStep(0.1)
        self.atr_ranging_spin.setDecimals(2)
        self.atr_ranging_spin.setToolTip(
            "ATR-Multiplier für RANGING/CHOPPY Märkte (ADX < 20).\n"
            "Höher = weiterer Stop = weniger Whipsaws\n"
            "Empfohlen: 3.0-4.0x"
        )
        trailing_layout.addRow("ATR Ranging:", self.atr_ranging_spin)

        # Volatility Bonus
        self.volatility_bonus_spin = QDoubleSpinBox()
        self.volatility_bonus_spin.setRange(0.0, 2.0)
        self.volatility_bonus_spin.setValue(0.5)
        self.volatility_bonus_spin.setSingleStep(0.1)
        self.volatility_bonus_spin.setDecimals(2)
        self.volatility_bonus_spin.setToolTip(
            "Extra ATR-Multiplier bei hoher Volatilität.\n"
            "Wird hinzuaddiert wenn ATR > 2% des Preises.\n"
            "Empfohlen: 0.3-0.5x"
        )
        trailing_layout.addRow("Vol. Bonus:", self.volatility_bonus_spin)

        # Min Step %
        self.min_step_spin = QDoubleSpinBox()
        self.min_step_spin.setRange(0.05, 2.0)
        self.min_step_spin.setValue(0.3)
        self.min_step_spin.setSingleStep(0.05)
        self.min_step_spin.setSuffix(" %")
        self.min_step_spin.setDecimals(2)
        self.min_step_spin.setToolTip(
            "Mindest-Bewegung für Stop-Update.\n"
            "Verhindert zu häufige kleine Anpassungen.\n"
            "Empfohlen: 0.2-0.5% für Crypto"
        )
        trailing_layout.addRow("Min Step:", self.min_step_spin)

        trailing_group.setLayout(trailing_layout)

        # ==================== SIDE-BY-SIDE LAYOUT FOR SETTINGS ====================
        settings_row = QHBoxLayout()
        settings_row.setSpacing(10)
        settings_row.addWidget(settings_group)
        settings_row.addWidget(trailing_group)
        layout.addLayout(settings_row)

        # Update visibility based on trailing mode and regime_adaptive
        self._on_trailing_mode_changed()
        self._on_regime_adaptive_changed()

        # ==================== BOTTOM ROW: DISPLAY + HELP ====================
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        # Display options (compact)
        display_group = QGroupBox("Chart Display")
        display_layout = QHBoxLayout()  # Horizontal for compact layout
        display_layout.setContentsMargins(8, 8, 8, 8)

        self.show_entry_markers_cb = QCheckBox("Entry Markers")
        self.show_entry_markers_cb.setChecked(True)
        self.show_entry_markers_cb.stateChanged.connect(self._on_display_option_changed)
        display_layout.addWidget(self.show_entry_markers_cb)

        self.show_stop_lines_cb = QCheckBox("Stop Lines")
        self.show_stop_lines_cb.setChecked(True)
        self.show_stop_lines_cb.stateChanged.connect(self._on_display_option_changed)
        display_layout.addWidget(self.show_stop_lines_cb)

        self.show_debug_hud_cb = QCheckBox("Debug HUD")
        self.show_debug_hud_cb.setChecked(False)
        self.show_debug_hud_cb.stateChanged.connect(self._on_debug_hud_changed)
        display_layout.addWidget(self.show_debug_hud_cb)

        display_group.setLayout(display_layout)
        bottom_row.addWidget(display_group)

        # Help button
        help_btn = QPushButton("📖 Trading-Bot Hilfe")
        help_btn.setStyleSheet("padding: 8px; font-size: 12px;")
        help_btn.setToolTip("Öffnet die ausführliche Dokumentation zum Trading-Bot")
        help_btn.clicked.connect(self._on_open_help_clicked)
        bottom_row.addWidget(help_btn)

        bottom_row.addStretch()
        layout.addLayout(bottom_row)

        layout.addStretch()
        return widget

    def _on_open_help_clicked(self) -> None:
        """Open the trading bot help documentation."""
        # Find project root and help file
        try:
            # Navigate from src/ui/widgets/chart_window_mixins to project root
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent.parent
            help_file = project_root / "Help" / "tradingbot-hilfe.html"

            if help_file.exists():
                url = QUrl.fromLocalFile(str(help_file))
                QDesktopServices.openUrl(url)
                logger.info(f"Opened help file: {help_file}")
            else:
                logger.warning(f"Help file not found: {help_file}")
        except Exception as e:
            logger.error(f"Failed to open help: {e}")

    def _create_strategy_selection_tab(self) -> QWidget:
        """Create daily strategy selection tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ==================== CURRENT STRATEGY ====================
        current_group = QGroupBox("Current Strategy")
        current_layout = QFormLayout()

        self.active_strategy_label = QLabel("None")
        self.active_strategy_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #26a69a;"
        )
        current_layout.addRow("Active:", self.active_strategy_label)

        self.regime_label = QLabel("Unknown")
        current_layout.addRow("Regime:", self.regime_label)

        self.volatility_label = QLabel("Normal")
        current_layout.addRow("Volatility:", self.volatility_label)

        self.selection_time_label = QLabel("-")
        current_layout.addRow("Selected At:", self.selection_time_label)

        self.next_selection_label = QLabel("-")
        current_layout.addRow("Next Selection:", self.next_selection_label)

        current_group.setLayout(current_layout)
        layout.addWidget(current_group)

        # ==================== STRATEGY SCORES ====================
        scores_group = QGroupBox("Strategy Scores")
        scores_layout = QVBoxLayout()

        self.strategy_scores_table = QTableWidget()
        self.strategy_scores_table.setColumnCount(5)
        self.strategy_scores_table.setHorizontalHeaderLabels([
            "Strategy", "Score", "PF", "WinRate", "MaxDD"
        ])
        self.strategy_scores_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.strategy_scores_table.setAlternatingRowColors(True)
        self.strategy_scores_table.setMaximumHeight(200)
        scores_layout.addWidget(self.strategy_scores_table)

        scores_group.setLayout(scores_layout)
        layout.addWidget(scores_group)

        # ==================== WALK-FORWARD RESULTS ====================
        wf_group = QGroupBox("Walk-Forward Results")
        wf_layout = QVBoxLayout()

        self.wf_results_text = QTextEdit()
        self.wf_results_text.setReadOnly(True)
        self.wf_results_text.setMaximumHeight(150)
        self.wf_results_text.setPlaceholderText(
            "Walk-forward evaluation results will appear here..."
        )
        wf_layout.addWidget(self.wf_results_text)

        wf_group.setLayout(wf_layout)
        layout.addWidget(wf_group)

        # Manual override button
        override_layout = QHBoxLayout()
        self.force_reselect_btn = QPushButton("Force Re-Selection")
        self.force_reselect_btn.clicked.connect(self._on_force_reselect)
        override_layout.addWidget(self.force_reselect_btn)
        override_layout.addStretch()
        layout.addLayout(override_layout)

        layout.addStretch()
        return widget

    def _create_signals_tab(self) -> QWidget:
        """Create signals & trade management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Use splitter for top/bottom sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # ==================== CURRENT POSITION ====================
        position_widget = QWidget()
        position_layout = QVBoxLayout(position_widget)
        position_layout.setContentsMargins(0, 0, 0, 0)

        position_group = QGroupBox("Current Position")
        position_form = QFormLayout()
        position_form.setVerticalSpacing(2)  # Compact spacing
        position_form.setContentsMargins(8, 8, 8, 8)

        self.position_side_label = QLabel("FLAT")
        self.position_side_label.setStyleSheet("font-weight: bold;")
        position_form.addRow("Side:", self.position_side_label)

        self.position_entry_label = QLabel("-")
        position_form.addRow("Entry:", self.position_entry_label)

        self.position_size_label = QLabel("-")
        position_form.addRow("Size:", self.position_size_label)

        self.position_invested_label = QLabel("-")
        self.position_invested_label.setStyleSheet("font-weight: bold;")
        position_form.addRow("Invested:", self.position_invested_label)

        self.position_stop_label = QLabel("-")
        position_form.addRow("Stop:", self.position_stop_label)

        self.position_current_label = QLabel("-")
        self.position_current_label.setStyleSheet("font-weight: bold;")
        position_form.addRow("Current:", self.position_current_label)

        self.position_pnl_label = QLabel("-")
        position_form.addRow("P&L:", self.position_pnl_label)

        self.position_bars_held_label = QLabel("-")
        position_form.addRow("Bars Held:", self.position_bars_held_label)

        position_group.setLayout(position_form)
        position_group.setMaximumHeight(160)  # Compact height (-30%)
        position_layout.addWidget(position_group)
        splitter.addWidget(position_widget)

        # ==================== SIGNAL HISTORY ====================
        signals_widget = QWidget()
        signals_layout = QVBoxLayout(signals_widget)
        signals_layout.setContentsMargins(0, 0, 0, 0)

        signals_group = QGroupBox("Recent Signals")
        signals_inner = QVBoxLayout()

        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(16)
        self.signals_table.setHorizontalHeaderLabels([
            "Time", "Type", "Side", "Score", "Entry", "Stop", "SL%", "TR%", "TR Kurs", "TRA%", "TR Lock", "Status", "Current", "Δ%", "P&L €", "P&L %"
        ])
        self.signals_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.signals_table.setAlternatingRowColors(True)
        self.signals_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.signals_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Context menu for signals table
        self.signals_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.signals_table.customContextMenuRequested.connect(self._show_signals_context_menu)

        # Connect cell editing for bidirectional chart trading (SL% and TR% columns)
        self.signals_table.cellChanged.connect(self._on_signals_table_cell_changed)
        self._signals_table_updating = False  # Flag to prevent recursive updates

        signals_inner.addWidget(self.signals_table)

        signals_group.setLayout(signals_inner)
        signals_layout.addWidget(signals_group)
        splitter.addWidget(signals_widget)

        layout.addWidget(splitter)
        return widget

    def _create_ki_logs_tab(self) -> QWidget:
        """Create KI logs tab for monitoring AI decisions."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ==================== KI STATUS ====================
        status_group = QGroupBox("KI Status")
        status_layout = QFormLayout()

        self.ki_status_label = QLabel("Inactive")
        status_layout.addRow("Status:", self.ki_status_label)

        self.ki_calls_today_label = QLabel("0")
        status_layout.addRow("Calls Today:", self.ki_calls_today_label)

        self.ki_last_call_label = QLabel("-")
        status_layout.addRow("Last Call:", self.ki_last_call_label)

        self.ki_cost_today_label = QLabel("$0.00")
        status_layout.addRow("Cost Today:", self.ki_cost_today_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # ==================== LOG VIEWER ====================
        log_group = QGroupBox("KI Log")
        log_layout = QVBoxLayout()

        self.ki_log_text = QPlainTextEdit()
        self.ki_log_text.setReadOnly(True)
        self.ki_log_text.setStyleSheet(
            "font-family: monospace; font-size: 11px;"
        )
        self.ki_log_text.setPlaceholderText(
            "KI request/response logs will appear here...\n"
            "Format: [timestamp] [type] message"
        )
        log_layout.addWidget(self.ki_log_text)

        # Clear button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self._clear_ki_log)
        log_layout.addWidget(clear_btn)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        return widget

    # ==================== EVENT HANDLERS ====================

    def _on_bot_start_clicked(self) -> None:
        """Handle bot start button click."""
        logger.info("Bot start requested")
        self._update_bot_status("STARTING", "#ffeb3b")

        # Build config from UI
        try:
            self._start_bot_with_config()
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            self._update_bot_status("ERROR", "#f44336")
            return

        self.bot_start_btn.setEnabled(False)
        self.bot_stop_btn.setEnabled(True)
        self.bot_pause_btn.setEnabled(True)

    def _on_bot_stop_clicked(self) -> None:
        """Handle bot stop button click."""
        logger.info("Bot stop requested")
        self._stop_bot()

        self._update_bot_status("STOPPED", "#9e9e9e")
        self.bot_start_btn.setEnabled(True)
        self.bot_stop_btn.setEnabled(False)
        self.bot_pause_btn.setEnabled(False)

    def _on_bot_pause_clicked(self) -> None:
        """Handle bot pause button click."""
        if self._bot_controller:
            # Toggle pause
            if self.bot_pause_btn.text() == "Pause":
                self._bot_controller.pause()
                self.bot_pause_btn.setText("Resume")
                self._update_bot_status("PAUSED", "#ff9800")
            else:
                self._bot_controller.resume()
                self.bot_pause_btn.setText("Pause")
                self._update_bot_status("RUNNING", "#26a69a")

    def _on_ki_mode_changed(self, mode: str) -> None:
        """Handle KI mode change."""
        logger.info(f"KI mode changed to: {mode}")
        if self._bot_controller:
            self._bot_controller.set_ki_mode(mode)

    def _on_trailing_mode_changed(self, mode: str = "") -> None:
        """Handle trailing mode change - toggle field visibility based on mode."""
        current_mode = self.trailing_mode_combo.currentText()
        is_pct = current_mode == "PCT"
        is_atr = current_mode == "ATR"

        disabled_style = "color: #666666;"
        enabled_style = ""

        # PCT distance only for PCT mode
        self.trailing_distance_spin.setEnabled(is_pct)
        self.trailing_distance_spin.setStyleSheet(enabled_style if is_pct else disabled_style)

        # ATR settings only for ATR mode
        self.regime_adaptive_cb.setEnabled(is_atr)
        self.atr_multiplier_spin.setEnabled(is_atr)
        self.atr_trending_spin.setEnabled(is_atr)
        self.atr_ranging_spin.setEnabled(is_atr)
        self.volatility_bonus_spin.setEnabled(is_atr)

        self.regime_adaptive_cb.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.atr_multiplier_spin.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.atr_trending_spin.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.atr_ranging_spin.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.volatility_bonus_spin.setStyleSheet(enabled_style if is_atr else disabled_style)

        # Update regime-adaptive visibility when in ATR mode
        if is_atr:
            self._on_regime_adaptive_changed()

    def _on_regime_adaptive_changed(self, state: int = 0) -> None:
        """Handle regime-adaptive checkbox change - toggle field visibility."""
        # Only apply if ATR mode is active
        if self.trailing_mode_combo.currentText() != "ATR":
            return

        is_adaptive = self.regime_adaptive_cb.isChecked()

        # Fixed multiplier only visible when NOT adaptive
        self.atr_multiplier_spin.setEnabled(not is_adaptive)

        # Adaptive settings only visible when adaptive
        self.atr_trending_spin.setEnabled(is_adaptive)
        self.atr_ranging_spin.setEnabled(is_adaptive)
        self.volatility_bonus_spin.setEnabled(is_adaptive)

        # Update styling to show enabled/disabled state
        disabled_style = "color: #666666;"
        enabled_style = ""

        self.atr_multiplier_spin.setStyleSheet(enabled_style if not is_adaptive else disabled_style)
        self.atr_trending_spin.setStyleSheet(enabled_style if is_adaptive else disabled_style)
        self.atr_ranging_spin.setStyleSheet(enabled_style if is_adaptive else disabled_style)
        self.volatility_bonus_spin.setStyleSheet(enabled_style if is_adaptive else disabled_style)

    def _on_display_option_changed(self, state: int) -> None:
        """Handle display option checkbox change."""
        if not hasattr(self, 'chart_widget'):
            return

        # Entry markers visibility
        show_markers = self.show_entry_markers_cb.isChecked()
        if hasattr(self.chart_widget, '_bot_overlay_state'):
            if not show_markers:
                self.chart_widget.clear_bot_markers()

        # Stop lines visibility
        show_stops = self.show_stop_lines_cb.isChecked()
        if hasattr(self.chart_widget, '_bot_overlay_state'):
            if not show_stops:
                self.chart_widget.clear_stop_lines()
            elif self._bot_controller and self._bot_controller.position:
                # Re-display position if showing
                self.chart_widget.display_position(self._bot_controller.position)

    def _on_debug_hud_changed(self, state: int) -> None:
        """Handle debug HUD checkbox change."""
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'set_debug_hud_visible'):
            self.chart_widget.set_debug_hud_visible(state == Qt.CheckState.Checked.value)

    def _on_force_reselect(self) -> None:
        """Handle force re-selection button click."""
        logger.info("Forcing strategy re-selection")
        if self._bot_controller:
            self._bot_controller.force_strategy_reselection()

    def _clear_ki_log(self) -> None:
        """Clear KI log display."""
        self.ki_log_text.clear()
        self._ki_log_entries.clear()

    # ==================== SYMBOL & SETTINGS MANAGEMENT ====================

    def update_bot_symbol(self, symbol: str | None = None) -> None:
        """Update the bot panel with current symbol and load its settings.

        Args:
            symbol: Symbol to use, or None to get from chart
        """
        # Get symbol from chart if not provided
        if symbol is None:
            symbol = getattr(self, 'current_symbol', None)
            if symbol is None and hasattr(self, 'chart_widget'):
                symbol = getattr(self.chart_widget, 'current_symbol', None)

        if not symbol:
            symbol = "UNKNOWN"

        # Update label
        if hasattr(self, 'bot_symbol_label'):
            self.bot_symbol_label.setText(symbol)

        # Load settings if symbol changed
        if symbol != self._current_bot_symbol:
            self._current_bot_symbol = symbol
            self._load_bot_settings(symbol)
            logger.info(f"Bot panel updated for symbol: {symbol}")

    def _load_bot_settings(self, symbol: str) -> None:
        """Load saved settings for a symbol into UI controls.

        Args:
            symbol: Symbol to load settings for
        """
        settings = self._bot_settings_manager.get_settings(symbol)

        if not settings:
            logger.debug(f"No saved settings for {symbol}, using defaults")
            return

        logger.info(f"Loading bot settings for {symbol}")

        try:
            # Bot settings
            if "ki_mode" in settings:
                idx = self.ki_mode_combo.findText(settings["ki_mode"])
                if idx >= 0:
                    self.ki_mode_combo.setCurrentIndex(idx)

            if "trailing_mode" in settings:
                idx = self.trailing_mode_combo.findText(settings["trailing_mode"])
                if idx >= 0:
                    self.trailing_mode_combo.setCurrentIndex(idx)

            if "initial_sl_pct" in settings:
                self.initial_sl_spin.setValue(settings["initial_sl_pct"])

            if "bot_capital" in settings:
                self.bot_capital_spin.setValue(settings["bot_capital"])

            if "risk_per_trade_pct" in settings:
                self.risk_per_trade_spin.setValue(settings["risk_per_trade_pct"])

            if "max_trades_per_day" in settings:
                self.max_trades_spin.setValue(settings["max_trades_per_day"])

            if "max_daily_loss_pct" in settings:
                self.max_daily_loss_spin.setValue(settings["max_daily_loss_pct"])

            if "disable_restrictions" in settings:
                self.disable_restrictions_cb.setChecked(settings["disable_restrictions"])

            if "disable_macd_exit" in settings:
                self.disable_macd_exit_cb.setChecked(settings["disable_macd_exit"])

            # Trailing stop settings
            if "regime_adaptive" in settings:
                self.regime_adaptive_cb.setChecked(settings["regime_adaptive"])

            if "atr_multiplier" in settings:
                self.atr_multiplier_spin.setValue(settings["atr_multiplier"])

            if "atr_trending" in settings:
                self.atr_trending_spin.setValue(settings["atr_trending"])

            if "atr_ranging" in settings:
                self.atr_ranging_spin.setValue(settings["atr_ranging"])

            if "volatility_bonus" in settings:
                self.volatility_bonus_spin.setValue(settings["volatility_bonus"])

            if "min_step_pct" in settings:
                self.min_step_spin.setValue(settings["min_step_pct"])

            if "trailing_activation_pct" in settings:
                self.trailing_activation_spin.setValue(settings["trailing_activation_pct"])

            if "trailing_pct_distance" in settings:
                self.trailing_distance_spin.setValue(settings["trailing_pct_distance"])

            # Update UI state
            self._on_trailing_mode_changed()
            self._on_regime_adaptive_changed()

            logger.info(f"Loaded {len(settings)} settings for {symbol}")

        except Exception as e:
            logger.error(f"Error loading settings for {symbol}: {e}")

    def _save_bot_settings(self, symbol: str) -> None:
        """Save current UI settings for a symbol.

        Args:
            symbol: Symbol to save settings for
        """
        settings = {
            # Bot settings
            "ki_mode": self.ki_mode_combo.currentText(),
            "trailing_mode": self.trailing_mode_combo.currentText(),
            "initial_sl_pct": self.initial_sl_spin.value(),
            "bot_capital": self.bot_capital_spin.value(),
            "risk_per_trade_pct": self.risk_per_trade_spin.value(),
            "max_trades_per_day": self.max_trades_spin.value(),
            "max_daily_loss_pct": self.max_daily_loss_spin.value(),
            "disable_restrictions": self.disable_restrictions_cb.isChecked(),
            "disable_macd_exit": self.disable_macd_exit_cb.isChecked(),

            # Trailing stop settings
            "regime_adaptive": self.regime_adaptive_cb.isChecked(),
            "atr_multiplier": self.atr_multiplier_spin.value(),
            "atr_trending": self.atr_trending_spin.value(),
            "atr_ranging": self.atr_ranging_spin.value(),
            "volatility_bonus": self.volatility_bonus_spin.value(),
            "min_step_pct": self.min_step_spin.value(),
            "trailing_activation_pct": self.trailing_activation_spin.value(),
            "trailing_pct_distance": self.trailing_distance_spin.value(),
        }

        self._bot_settings_manager.save_settings(symbol, settings)
        logger.info(f"Saved bot settings for {symbol}")

    # ==================== BOT CONTROL ====================

    def _start_bot_with_config(self) -> None:
        """Start bot with current UI configuration."""
        from src.core.tradingbot import (
            BotConfig,
            FullBotConfig,
            KIMode,
            MarketType,
            RiskConfig,
            TrailingMode,
        )

        # Get symbol from chart
        symbol = getattr(self, 'current_symbol', 'AAPL')
        if hasattr(self, 'chart_widget'):
            symbol = getattr(self.chart_widget, 'current_symbol', symbol)

        # Build config (convert uppercase UI values to lowercase enum values)
        ki_mode = KIMode(self.ki_mode_combo.currentText().lower())
        trailing_mode = TrailingMode(self.trailing_mode_combo.currentText().lower())

        # Determine market type from symbol
        market_type = MarketType.CRYPTO if '/' in symbol else MarketType.NASDAQ

        config = FullBotConfig.create_default(symbol, market_type)

        # Override with UI values
        config.bot.ki_mode = ki_mode
        config.bot.trailing_mode = trailing_mode
        config.bot.disable_restrictions = self.disable_restrictions_cb.isChecked()
        config.bot.disable_macd_exit = self.disable_macd_exit_cb.isChecked()
        config.risk.initial_stop_loss_pct = self.initial_sl_spin.value()
        config.risk.risk_per_trade_pct = self.risk_per_trade_spin.value()
        config.risk.max_trades_per_day = self.max_trades_spin.value()
        config.risk.max_daily_loss_pct = self.max_daily_loss_spin.value()

        # Trailing stop settings
        config.risk.regime_adaptive_trailing = self.regime_adaptive_cb.isChecked()
        config.risk.trailing_atr_multiple = self.atr_multiplier_spin.value()
        config.risk.trailing_atr_trending = self.atr_trending_spin.value()
        config.risk.trailing_atr_ranging = self.atr_ranging_spin.value()
        config.risk.trailing_volatility_bonus = self.volatility_bonus_spin.value()
        config.risk.trailing_min_step_pct = self.min_step_spin.value()
        config.risk.trailing_activation_pct = self.trailing_activation_spin.value()
        config.risk.trailing_pct_distance = self.trailing_distance_spin.value()

        # Create and start controller with callbacks
        from src.core.tradingbot.bot_controller import BotController

        self._bot_controller = BotController(
            config,
            on_signal=self._on_bot_signal,
            on_decision=self._on_bot_decision,
            on_order=self._on_bot_order,
            on_log=self._on_bot_log,
            on_trading_blocked=self._on_trading_blocked,
            on_macd_signal=self._on_macd_signal,
        )

        # Register state change callback (receives StateTransition object)
        self._bot_controller._state_machine._on_transition = lambda t: (
            self._on_bot_state_change(t.from_state.value, t.to_state.value)
        )

        # Warmup from chart data (skip waiting for 60 bars)
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
            try:
                chart_data = self.chart_widget.data
                # Convert DataFrame to list of dicts for warmup
                warmup_bars = []
                for timestamp, row in chart_data.iterrows():
                    warmup_bars.append({
                        'timestamp': timestamp,
                        'open': float(row['open']),
                        'high': float(row['high']),
                        'low': float(row['low']),
                        'close': float(row['close']),
                        'volume': float(row.get('volume', 0)),
                    })
                loaded = self._bot_controller.warmup_from_history(warmup_bars)
                logger.info(f"Bot warmup: {loaded} bars from chart history")
            except Exception as e:
                logger.warning(f"Could not warmup from chart data: {e}")

        # Start the bot
        self._bot_controller.start()
        self._update_bot_status("RUNNING", "#26a69a")

        # Start update timer
        if not self._bot_update_timer:
            self._bot_update_timer = QTimer()
            self._bot_update_timer.timeout.connect(self._update_bot_display)
        self._bot_update_timer.start(1000)

        # Save settings for this symbol
        self._save_bot_settings(symbol)

        logger.info(f"Bot started for {symbol} with {ki_mode.value} mode")

    def _stop_bot(self) -> None:
        """Stop the running bot."""
        if self._bot_controller:
            self._bot_controller.stop()
            self._bot_controller = None

        if self._bot_update_timer:
            self._bot_update_timer.stop()

        logger.info("Bot stopped")

    # ==================== CALLBACKS ====================

    def _on_bot_signal(self, signal: Any) -> None:
        """Handle bot signal event."""
        signal_type = signal.signal_type.value if hasattr(signal, 'signal_type') else "unknown"
        side = signal.side.value if hasattr(signal, 'side') else "unknown"
        entry_price = getattr(signal, 'entry_price', 0)
        score = getattr(signal, 'score', 0)

        # Determine status based on signal type
        if signal_type == "confirmed":
            status = "ENTERED"
        elif signal_type == "candidate":
            status = "PENDING"
        else:
            status = "ACTIVE"

        # Debug: Log signal reception with type
        self._add_ki_log_entry(
            "SIGNAL",
            f"Signal empfangen: type={signal_type} side={side} @ {entry_price:.4f} → status={status}"
        )

        logger.info(
            f"Bot signal received: {signal_type} {side} @ {entry_price:.4f} (Score: {score:.2f})"
        )

        # For confirmed signals, DON'T add a new entry - update the existing candidate instead
        if signal_type == "confirmed":
            # Find and update the last candidate signal for this side
            for sig in reversed(self._signal_history):
                if sig["type"] == "candidate" and sig["side"] == side and sig["status"] == "PENDING":
                    # Update existing candidate to confirmed
                    sig["type"] = "confirmed"
                    sig["status"] = "ENTERED"
                    sig["score"] = score  # Update with confirmed score
                    sig["price"] = entry_price  # Update price
                    sig["is_open"] = True
                    sig["label"] = f"E:{int(score * 100)}"  # Entry label like E:66
                    sig["entry_timestamp"] = int(datetime.now().timestamp())  # Unix timestamp for chart marker
                    logger.info(f"Updated candidate to confirmed: {side} @ {entry_price:.4f}")
                    break
            else:
                # No candidate found - add new confirmed entry (shouldn't happen normally)
                self._signal_history.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "type": signal_type,
                    "side": side,
                    "score": score,
                    "price": entry_price,
                    "status": "ENTERED",
                    "quantity": 0.0,
                    "current_price": entry_price,
                    "pnl_currency": 0.0,
                    "pnl_percent": 0.0,
                    "is_open": True,
                    "label": f"E:{int(score * 100)}",
                    "entry_timestamp": int(datetime.now().timestamp())  # Unix timestamp for chart marker
                })
        else:
            # Candidate signal - add new entry
            self._signal_history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": signal_type,
                "side": side,
                "score": score,
                "price": entry_price,
                "status": status,
                "quantity": 0.0,
                "current_price": entry_price,
                "pnl_currency": 0.0,
                "pnl_percent": 0.0,
                "is_open": False,
                "label": ""  # No label for candidates
            })

        self._update_signals_table()

        # NOTE: Chart markers are added in _on_bot_order after fill confirmation
        # Don't add markers here to avoid duplicates

    def _on_bot_decision(self, decision: Any) -> None:
        """Handle bot decision event."""
        from src.core.tradingbot.models import BotAction

        action = decision.action if hasattr(decision, 'action') else None
        self._add_ki_log_entry("DEBUG", f"_on_bot_decision called: action={action.value if action else 'unknown'}")

        # Handle stop line updates on chart
        if hasattr(self, 'chart_widget') and action:
            try:
                if action == BotAction.ENTER:
                    # Draw initial stop line (red, solid)
                    stop_price = getattr(decision, 'stop_price_after', None)
                    self._add_ki_log_entry("DEBUG", f"ENTER: stop_price_after={stop_price}, has chart={hasattr(self, 'chart_widget')}")
                    if stop_price:
                        # Get SL% for label
                        initial_sl_pct = self.initial_sl_spin.value() if hasattr(self, 'initial_sl_spin') else 0.0
                        sl_label = f"SL @ {stop_price:.2f} ({initial_sl_pct:.2f}%)" if initial_sl_pct > 0 else f"SL @ {stop_price:.2f}"

                        self._add_ki_log_entry("DEBUG", f"Calling add_stop_line({stop_price})")
                        self.chart_widget.add_stop_line(
                            "initial_stop",  # Separate ID for initial stop
                            stop_price,
                            line_type="initial",
                            color="#ef5350",  # Red for initial stop loss
                            label=sl_label
                        )
                        self._add_ki_log_entry("STOP", f"Initial Stop-Line gezeichnet @ {stop_price:.2f} ({initial_sl_pct:.2f}%)")
                        for sig in reversed(self._signal_history):
                            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                                sig["stop_price"] = stop_price
                                sig["initial_sl_pct"] = initial_sl_pct
                                self._save_signal_history()
                                self._add_ki_log_entry("DEBUG", f"stop_price {stop_price:.2f} ({initial_sl_pct:.2f}%) in Signal-History gespeichert")
                                break
                    else:
                        self._add_ki_log_entry("ERROR", "stop_price_after ist None - keine Stop-Line!")

                elif action == BotAction.ADJUST_STOP:
                    # Update trailing stop line (orange, solid, separate from initial)
                    new_stop = getattr(decision, 'stop_price_after', None)
                    old_stop = getattr(decision, 'stop_price_before', None)
                    if new_stop:
                        # Calculate change percentage if old_stop available
                        if old_stop:
                            change_pct = ((new_stop - old_stop) / old_stop) * 100
                            self._add_ki_log_entry(
                                "TRAILING",
                                f"Stop angepasst: {old_stop:.2f} → {new_stop:.2f} ({change_pct:+.2f}%)"
                            )
                            logger.info(f"Trailing stop updated: {old_stop:.2f} -> {new_stop:.2f} ({change_pct:+.2f}%)")
                        else:
                            self._add_ki_log_entry(
                                "TRAILING",
                                f"Trailing Stop aktiviert @ {new_stop:.2f}"
                            )
                            logger.info(f"Trailing stop activated: {new_stop:.2f}")

                        # Get TR% and TRA% for label
                        trailing_pct = self.trailing_distance_spin.value() if hasattr(self, 'trailing_distance_spin') else 0.0
                        # Calculate TRA% (distance from current price)
                        tra_pct = 0.0
                        if self._bot_controller and self._bot_controller._last_features:
                            current_price = self._bot_controller._last_features.close
                            if current_price > 0:
                                tra_pct = abs((current_price - new_stop) / current_price) * 100
                        tr_label = f"TSL @ {new_stop:.2f} ({trailing_pct:.2f}% / TRA: {tra_pct:.2f}%)"

                        # Add/update trailing stop line (separate from initial stop)
                        self.chart_widget.add_stop_line(
                            "trailing_stop",  # Separate ID for trailing stop
                            new_stop,
                            line_type="trailing",
                            color="#ff9800",  # Orange for trailing stop
                            label=tr_label
                        )
                        self._add_ki_log_entry(
                            "CHART",
                            f"Trailing Stop Linie gezeichnet @ {new_stop:.2f} ({trailing_pct:.2f}% / TRA: {tra_pct:.2f}%) (orange)"
                        )
                        for sig in reversed(self._signal_history):
                            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                                sig["stop_price"] = new_stop
                                sig["trailing_stop_price"] = new_stop
                                sig["trailing_stop_pct"] = trailing_pct
                                self._save_signal_history()
                                logger.info(f"Signal history updated: trailing_stop_price={new_stop:.2f}, trailing_stop_pct={trailing_pct:.2f}%")
                                break

                elif action == BotAction.EXIT:
                    # Remove both stop lines
                    if hasattr(self.chart_widget, 'remove_stop_line'):
                        self.chart_widget.remove_stop_line("initial_stop")
                        self.chart_widget.remove_stop_line("trailing_stop")
                        logger.info("Removed stop lines on exit")

                    # Get exit price for final P&L calculation
                    exit_price = None
                    if self._bot_controller and self._bot_controller._last_features:
                        exit_price = self._bot_controller._last_features.close

                    # Update signal history - mark position as CLOSED with final P&L
                    reason_codes = getattr(decision, 'reason_codes', []) or []
                    for signal in reversed(self._signal_history):
                        if signal["status"] == "ENTERED" and signal.get("is_open", False):
                            # Calculate and save final P&L at exit price
                            if exit_price and signal.get("quantity", 0) > 0:
                                entry_price = signal["price"]
                                side = signal["side"]

                                # Get invested capital
                                invested_capital = signal.get("invested_capital", 0)
                                if invested_capital <= 0:
                                    initial_cap = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000.0
                                    risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10.0
                                    invested_capital = initial_cap * (risk_pct / 100)

                                # Calculate price change percentage
                                price_change_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0

                                # P&L based on price change: LONG = price change, SHORT = -price change
                                if side == "long":
                                    pnl_percent = price_change_pct
                                else:
                                    pnl_percent = -price_change_pct

                                # P&L€ = invested × P&L%
                                pnl_currency = invested_capital * (pnl_percent / 100)

                                signal["current_price"] = exit_price
                                signal["pnl_currency"] = pnl_currency
                                signal["pnl_percent"] = pnl_percent

                                self._add_ki_log_entry(
                                    "EXIT",
                                    f"Position geschlossen: {signal['pnl_currency']:+.2f}€ ({signal['pnl_percent']:+.2f}%)"
                                )

                            signal["status"] = "CLOSED"
                            signal["is_open"] = False
                            # Add exit reason to status if available
                            if reason_codes:
                                signal["status"] = f"CLOSED ({reason_codes[0]})"
                            logger.debug(f"Marked signal as CLOSED: {signal['side']} @ {signal['price']}")
                            break
                    self._update_signals_table()

                    # Add exit marker to chart
                    from datetime import datetime
                    side = decision.side.value if hasattr(decision, 'side') and hasattr(decision.side, 'value') else 'long'

                    # exit_price was already retrieved above
                    if exit_price:
                        if "STOP_HIT" in reason_codes:
                            # Stop-loss was triggered
                            if hasattr(self.chart_widget, 'add_stop_triggered_marker'):
                                self.chart_widget.add_stop_triggered_marker(
                                    timestamp=datetime.now(),
                                    price=exit_price,
                                    side=side
                                )
                                logger.info(f"Added stop-triggered marker at {exit_price:.4f}")
                        else:
                            # Normal exit (signal, time stop, etc.)
                            if hasattr(self.chart_widget, 'add_exit_marker'):
                                reason = reason_codes[0] if reason_codes else "EXIT"
                                self.chart_widget.add_exit_marker(
                                    timestamp=datetime.now(),
                                    price=exit_price,
                                    side=side,
                                    reason=reason
                                )
                                logger.info(f"Added exit marker at {exit_price:.4f} ({reason})")

            except Exception as e:
                logger.error(f"Failed to update stop line: {e}", exc_info=True)

        # Log KI decisions
        if hasattr(decision, 'source') and decision.source == 'llm':
            self._add_ki_log_entry(
                "DECISION",
                f"Action: {action.value if action else 'unknown'}, Confidence: {decision.confidence:.2f}"
            )

    def _on_bot_log(self, log_type: str, message: str) -> None:
        """Handle bot activity log event.

        Args:
            log_type: Type of log entry (BAR, FEATURE, REGIME, SIGNAL, etc.)
            message: Log message
        """
        # Add to KI log with color-coded type
        self._add_ki_log_entry(log_type, message)

        # Update KI status label based on log type
        if log_type == "START":
            self.ki_status_label.setText("Active")
            self.ki_status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        elif log_type == "STOP":
            self.ki_status_label.setText("Inactive")
            self.ki_status_label.setStyleSheet("color: #9e9e9e;")
        elif log_type == "ERROR":
            self.ki_status_label.setText("Error")
            self.ki_status_label.setStyleSheet("color: #f44336; font-weight: bold;")

    def _on_bot_order(self, order: Any) -> None:
        """Handle bot order intent event - simulate fill for paper trading.

        Args:
            order: OrderIntent from BotController
        """
        from datetime import datetime

        # Debug: Log entry into callback
        order_qty = getattr(order, 'quantity', 'N/A')
        order_side = order.side.value if hasattr(order.side, 'value') else str(getattr(order, 'side', 'N/A'))
        order_symbol = getattr(order, 'symbol', 'N/A')
        self._add_ki_log_entry("ORDER", f"Order empfangen: {order_side} {order_symbol} qty={order_qty}")

        logger.info(
            f"Bot order received: {order_side} {order_symbol} qty={order_qty} @ market"
        )

        # For paper trading, immediately simulate the fill
        if not self._bot_controller:
            self._add_ki_log_entry("ERROR", "Bot controller is None - cannot process order!")
            return

        try:
            # Get signal info BEFORE simulate_fill (it clears _current_signal)
            signal = self._bot_controller._current_signal
            score = signal.score * 100 if signal else 0.0  # Convert to 0-100
            signal_entry_price = signal.entry_price if signal else None

            # Get current market price for fill (NOT stop_price - that's the stop-loss!)
            fill_price = None

            # Priority 1: Use signal entry price (most accurate)
            if signal_entry_price:
                fill_price = signal_entry_price

            # Priority 2: Use latest close from chart data
            if fill_price is None and hasattr(self, 'chart_widget'):
                if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                    fill_price = float(self.chart_widget.data['close'].iloc[-1])

            # Priority 3: Use last features from bot controller
            if fill_price is None and self._bot_controller._last_features:
                fill_price = self._bot_controller._last_features.close

            if fill_price is None:
                self._add_ki_log_entry("ERROR", "Kein Marktpreis für Paper-Fill verfügbar")
                logger.error("Cannot simulate fill: no market price available")
                return

            self._add_ki_log_entry("FILL", f"Simuliere Fill: qty={order.quantity:.4f} @ {fill_price:.4f}")

            # Simulate fill (this clears _current_signal!)
            self._bot_controller.simulate_fill(
                fill_price=fill_price,
                fill_qty=order.quantity,
                order_id=order.id if hasattr(order, 'id') else f"paper_{datetime.now().timestamp()}"
            )
            logger.info(f"Paper fill simulated: {order.quantity:.4f} @ {fill_price:.4f}")

            # Update the last ENTERED signal in history with quantity
            self._add_ki_log_entry("DEBUG", f"Suche ENTERED-Signal. History: {len(self._signal_history)} Einträge")
            found_signal = False
            for sig in reversed(self._signal_history):
                sig_status = sig['status']
                sig_qty = sig.get('quantity', 'N/A')
                self._add_ki_log_entry("DEBUG", f"  → status={sig_status}, qty={sig_qty}")
                if sig_status == "ENTERED" and sig.get("quantity", 0) == 0.0:
                    sig["quantity"] = order.quantity
                    sig["price"] = fill_price  # Update with actual fill price
                    # Invested capital = Initial Capital × Risk/Trade %
                    initial_cap = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000.0
                    risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10.0
                    sig["invested_capital"] = initial_cap * (risk_pct / 100)
                    # Also store position value for reference
                    sig["position_value"] = fill_price * order.quantity
                    # Store risk_amount if available (for ROI calculation on risk capital)
                    if hasattr(order, 'risk_amount') and order.risk_amount:
                        sig["risk_amount"] = order.risk_amount
                    sig["is_open"] = True
                    # Set entry label if not already set
                    if not sig.get("label"):
                        sig["label"] = f"E:{int(score)}"
                    found_signal = True
                    risk_info = f", risk={sig.get('risk_amount', 0):.2f}€" if sig.get('risk_amount') else ""
                    self._add_ki_log_entry("FILL", f"Signal aktualisiert: qty={order.quantity:.4f}, price={fill_price:.4f}, invested={sig['invested_capital']:.2f}€ (={initial_cap:.0f}×{risk_pct:.1f}%){risk_info}, label={sig['label']}")
                    logger.info(f"Updated signal history with qty={order.quantity}")
                    break

            if not found_signal:
                self._add_ki_log_entry("WARNING", "Kein ENTERED-Signal mit qty=0 gefunden!")

            # Refresh table immediately
            self._update_signals_table()

            # Add entry marker to chart (using pre-saved score)
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'add_entry_confirmed'):
                side = order.side.value if hasattr(order.side, 'value') else str(order.side)

                self.chart_widget.add_entry_confirmed(
                    timestamp=datetime.now(),
                    price=fill_price,
                    side=side,
                    score=score
                )
                logger.info(f"Entry marker added to chart: {side} @ {fill_price:.4f}")

        except Exception as e:
            self._add_ki_log_entry("ERROR", f"Paper-Fill fehlgeschlagen: {e}")
            logger.error(f"Failed to simulate paper fill: {e}", exc_info=True)

    def _on_macd_signal(self, signal_type: str, price: float) -> None:
        """Handle MACD cross signal - add marker to chart.

        Args:
            signal_type: "MACD_BEARISH_CROSS" or "MACD_BULLISH_CROSS"
            price: Current price where signal occurred
        """
        from datetime import datetime

        # Log to KI log
        self._add_ki_log_entry(
            "MACD",
            f"{signal_type} @ {price:.2f} (nur Marker, kein Verkauf)"
        )

        # Add marker to chart
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'add_macd_marker'):
            try:
                is_bearish = "BEARISH" in signal_type
                self.chart_widget.add_macd_marker(
                    timestamp=datetime.now(),
                    price=price,
                    is_bearish=is_bearish
                )
                logger.info(f"MACD marker added: {signal_type} @ {price:.2f}")
            except Exception as e:
                logger.error(f"Failed to add MACD marker: {e}")

    def _on_trading_blocked(self, reasons: list[str]) -> None:
        """Handle trading blocked notification - show popup.

        Args:
            reasons: List of reasons why trading is blocked
        """
        # Build message
        reason_list = "\n".join(f"  • {r}" for r in reasons)
        message = (
            f"⚠️ Trading wurde blockiert!\n\n"
            f"Gründe:\n{reason_list}\n\n"
            f"Der Bot wird keine neuen Positionen eröffnen, "
            f"bis die Blockierung aufgehoben wird."
        )

        # Log to KI log
        self._add_ki_log_entry("BLOCKED", f"Trading blockiert: {', '.join(reasons)}")

        # Show warning popup
        msg_box = QMessageBox(self if hasattr(self, 'window') else None)
        msg_box.setWindowTitle("Trading Blockiert")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)

        # Add hint about restrictions checkbox
        if not self._bot_controller.config.bot.disable_restrictions:
            msg_box.setInformativeText(
                "💡 Tipp: Im Paper-Modus können Sie die Restriktionen "
                "deaktivieren (Checkbox im Bot Control Tab)."
            )

        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

        logger.warning(f"Trading blocked popup shown: {reasons}")

    def _on_bot_state_change(self, old_state: str, new_state: str) -> None:
        """Handle bot state change."""
        logger.info(f"Bot state: {old_state} -> {new_state}")

        # Update status display
        colors = {
            "FLAT": "#607d8b",
            "SIGNAL": "#ffeb3b",
            "ENTERED": "#26a69a",
            "MANAGE": "#2196f3",
            "EXITED": "#9c27b0",
            "PAUSED": "#ff9800",
            "ERROR": "#f44336"
        }
        self._update_bot_status(new_state, colors.get(new_state, "#9e9e9e"))

        # Update debug HUD
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'update_debug_info'):
            self.chart_widget.update_debug_info(state=new_state)

    # ==================== DISPLAY UPDATES ====================

    def _update_bot_status(self, status: str, color: str) -> None:
        """Update bot status label."""
        self.bot_status_label.setText(f"Status: {status}")
        self.bot_status_label.setStyleSheet(
            f"font-weight: bold; color: {color}; font-size: 14px;"
        )

    def _update_bot_display(self) -> None:
        """Update all bot display elements."""
        if not self._bot_controller:
            return

        # Periodic diagnostic logging (every 60 bars = ~1 minute)
        bar_count = self._bot_controller._bar_count
        if bar_count > 0 and bar_count % 60 == 0:
            self._log_bot_diagnostics()

        # Update live P&L in signals table
        self._update_signals_pnl()

        # Update position display
        position = self._bot_controller.position

        # Debug logging for position display (every 10 seconds)
        if bar_count > 0 and bar_count % 10 == 0:
            if position:
                logger.debug(
                    f"[DISPLAY] Position: {position.side.value} entry={position.entry_price:.4f} "
                    f"qty={position.quantity:.4f} current={position.current_price:.4f} "
                    f"pnl={position.unrealized_pnl:.2f} trailing={position.trailing is not None}"
                )
            else:
                logger.debug("[DISPLAY] No position")
        if position:  # PositionState doesn't have is_open, check if position exists
            self.position_side_label.setText(position.side.value.upper())
            self.position_side_label.setStyleSheet(
                f"font-weight: bold; color: {'#26a69a' if position.side.value == 'long' else '#ef5350'};"
            )
            self.position_entry_label.setText(f"{position.entry_price:.4f}")
            self.position_size_label.setText(f"{position.quantity:.4f}")

            # Calculate and display invested amount (Initial Capital × Risk/Trade %)
            initial_cap = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000.0
            risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10.0
            invested = initial_cap * (risk_pct / 100)
            self.position_invested_label.setText(f"{invested:.2f} €")

            if position.trailing:  # Correct attribute: trailing (not trailing_state)
                self.position_stop_label.setText(
                    f"{position.trailing.current_stop_price:.4f}"  # Correct: current_stop_price
                )
            else:
                self.position_stop_label.setText("-")

            # Display current price
            self.position_current_label.setText(f"{position.current_price:.4f}")

            # Display P&L with color - based on price change × invested capital
            initial_cap = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000.0
            risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10.0
            invested_capital = initial_cap * (risk_pct / 100)

            # Calculate price change percentage
            entry_price = position.entry_price
            current_price = position.current_price
            price_change_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0

            # P&L% = price change for LONG, -price change for SHORT
            from src.core.tradingbot.models import TradeSide
            if position.side == TradeSide.LONG:
                pnl_pct = price_change_pct
            else:
                pnl_pct = -price_change_pct

            # P&L€ = invested × P&L%
            pnl = invested_capital * (pnl_pct / 100)

            # Debug: log invested capital calculation (every 30 seconds)
            if self._bot_controller and self._bot_controller._bar_count % 30 == 0:
                logger.debug(f"[P&L] capital={initial_cap:.0f}€, risk_pct={risk_pct:.1f}%, invested={invested_capital:.2f}€, Δ%={price_change_pct:.2f}%, pnl={pnl:.2f}€, pnl_pct={pnl_pct:.2f}%")
            pnl_color = "#26a69a" if pnl >= 0 else "#ef5350"  # Green for profit, red for loss
            pnl_sign = "+" if pnl >= 0 else ""
            self.position_pnl_label.setText(f"{pnl_sign}{pnl:.2f} € ({pnl_sign}{pnl_pct:.2f}%)")
            self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {pnl_color}; font-size: 14px;")
            self.position_bars_held_label.setText(str(position.bars_held))
        else:
            self.position_side_label.setText("FLAT")
            self.position_side_label.setStyleSheet("font-weight: bold; color: #9e9e9e;")
            self.position_entry_label.setText("-")
            self.position_size_label.setText("-")
            self.position_invested_label.setText("-")
            self.position_stop_label.setText("-")
            self.position_current_label.setText("-")
            self.position_pnl_label.setText("-")
            self.position_pnl_label.setStyleSheet("font-weight: bold; color: #9e9e9e;")
            self.position_bars_held_label.setText("-")

        # Update strategy display
        if hasattr(self._bot_controller, 'current_strategy'):
            strategy = self._bot_controller.current_strategy
            if strategy:
                self.active_strategy_label.setText(strategy.name)

        # Update regime display
        if hasattr(self._bot_controller, 'last_regime'):
            regime = self._bot_controller.last_regime
            if regime:
                self.regime_label.setText(regime.regime.value)
                self.volatility_label.setText(regime.volatility.value)

    def _update_signals_pnl(self) -> None:
        """Update P&L values for all open positions in signal history."""
        if not self._bot_controller:
            return

        # Get current price from bot controller's last features or position
        current_price = None
        if self._bot_controller._last_features:
            current_price = self._bot_controller._last_features.close
        elif self._bot_controller.position:
            current_price = self._bot_controller.position.current_price

        if current_price is None:
            return

        # Debug: Show signal history status every few seconds
        bar_count = self._bot_controller._bar_count if self._bot_controller else 0
        show_debug = (bar_count % 5 == 0) and len(self._signal_history) > 0

        if show_debug:
            entered_signals = [s for s in self._signal_history if s["status"] == "ENTERED"]
            if entered_signals:
                for es in entered_signals:
                    self._add_ki_log_entry(
                        "P&L-CHECK",
                        f"ENTERED: qty={es.get('quantity', 0)}, is_open={es.get('is_open', False)}, price={es.get('price', 0):.2f}"
                    )

        # Update P&L for all ENTERED signals
        table_updated = False
        active_count = 0
        for signal in self._signal_history:
            # Check for ENTERED status OR is_open flag (for positions that might have different status text)
            qty = signal.get("quantity", 0)
            is_active = (signal["status"] == "ENTERED" or signal.get("is_open", False)) and qty > 0
            if is_active:
                active_count += 1
                entry_price = signal["price"]
                side = signal["side"]

                # Get invested capital
                invested_capital = signal.get("invested_capital", 0)
                if invested_capital <= 0:
                    # Fallback: use current settings
                    initial_cap = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000.0
                    risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10.0
                    invested_capital = initial_cap * (risk_pct / 100)

                # Calculate price change percentage
                price_change_pct = ((current_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0

                # P&L based on price change and invested capital
                # LONG: price up = profit, SHORT: price up = loss
                if side == "long":
                    pnl_percent = price_change_pct
                else:  # short
                    pnl_percent = -price_change_pct

                # P&L€ = invested × P&L%
                pnl_currency = invested_capital * (pnl_percent / 100)

                # Update signal data
                signal["current_price"] = current_price
                signal["pnl_currency"] = pnl_currency
                signal["pnl_percent"] = pnl_percent
                table_updated = True

                # Debug: Log P&L calculation (every 5 bars)
                if show_debug:
                    self._add_ki_log_entry(
                        "P&L-CALC",
                        f"P&L berechnet: {pnl_currency:+.2f}€ ({pnl_percent:+.2f}%) | Entry={entry_price:.2f} Current={current_price:.2f}"
                    )

        # Debug: Log P&L update status (only occasionally to avoid spam)
        if bar_count % 10 == 0 and len(self._signal_history) > 0:
            logger.debug(f"P&L update: {active_count} active signals, current_price={current_price:.2f}")

        # Only update table if something changed
        if table_updated:
            self._update_signals_table()

    def _update_signals_table(self) -> None:
        """Update signals table with recent entries."""
        # Prevent recursive cellChanged events
        self._signals_table_updating = True

        recent_signals = list(reversed(self._signal_history[-20:]))
        self.signals_table.setRowCount(len(recent_signals))

        for row, signal in enumerate(recent_signals):
            # Basic columns
            self.signals_table.setItem(row, 0, QTableWidgetItem(signal["time"]))

            # Type column - show entry label (E:66) for confirmed, otherwise type
            signal_type = signal["type"]
            label = signal.get("label", "")
            if label and signal_type == "confirmed":
                type_item = QTableWidgetItem(label)
                type_item.setForeground(QColor("#26a69a"))  # Green for entries
            else:
                type_item = QTableWidgetItem(signal_type)
            self.signals_table.setItem(row, 1, type_item)

            self.signals_table.setItem(row, 2, QTableWidgetItem(signal["side"]))
            self.signals_table.setItem(row, 3, QTableWidgetItem(f"{signal['score'] * 100:.0f}"))
            self.signals_table.setItem(row, 4, QTableWidgetItem(f"{signal['price']:.4f}"))

            # Stop Loss column (5) - Initial Stop Price
            stop_price = signal.get("stop_price", 0.0)
            if stop_price > 0:
                self.signals_table.setItem(row, 5, QTableWidgetItem(f"{stop_price:.2f}"))
            else:
                self.signals_table.setItem(row, 5, QTableWidgetItem("-"))

            # SL% column (6) - Stop Loss Percent from Entry (EDITABLE for active positions)
            initial_sl_pct = signal.get("initial_sl_pct", 0.0)
            is_active = signal.get("status") == "ENTERED" and signal.get("is_open", False)
            if initial_sl_pct > 0:
                sl_pct_item = QTableWidgetItem(f"{initial_sl_pct:.2f}")
                sl_pct_item.setForeground(QColor("#ef5350"))  # Red for stop loss
            else:
                # Fallback: calculate from entry and stop price
                entry_price = signal.get("price", 0)
                if entry_price > 0 and stop_price > 0:
                    calculated_sl_pct = abs((stop_price - entry_price) / entry_price) * 100
                    sl_pct_item = QTableWidgetItem(f"{calculated_sl_pct:.2f}")
                    sl_pct_item.setForeground(QColor("#ef5350"))
                else:
                    sl_pct_item = QTableWidgetItem("-")
            # Make editable for active positions
            if is_active:
                sl_pct_item.setFlags(sl_pct_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.signals_table.setItem(row, 6, sl_pct_item)

            # TR% column (7) - Trailing Stop Percent (EDITABLE for active positions)
            trailing_pct = signal.get("trailing_stop_pct", 0.0)
            trailing_price = signal.get("trailing_stop_price", 0.0)

            # Calculate TR% from trailing_stop_price if not stored but price exists
            if trailing_pct <= 0 and trailing_price > 0 and entry_price > 0:
                side = signal.get("side", "long")
                if side == "long":
                    trailing_pct = abs((entry_price - trailing_price) / entry_price) * 100
                else:
                    trailing_pct = abs((trailing_price - entry_price) / entry_price) * 100

            if trailing_pct > 0:
                tr_pct_item = QTableWidgetItem(f"{trailing_pct:.2f}")
                tr_pct_item.setForeground(QColor("#ff9800"))  # Orange for trailing
            else:
                tr_pct_item = QTableWidgetItem("-")
            # Make editable for active positions
            if is_active:
                tr_pct_item.setFlags(tr_pct_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.signals_table.setItem(row, 7, tr_pct_item)

            # TR Kurs column (8) - Current Trailing Stop Price
            if trailing_price > 0:
                tr_price_item = QTableWidgetItem(f"{trailing_price:.2f}")
                tr_price_item.setForeground(QColor("#ff9800"))  # Orange for trailing
                self.signals_table.setItem(row, 8, tr_price_item)
            else:
                self.signals_table.setItem(row, 8, QTableWidgetItem("-"))

            # TRA% column (9) - Trailing Distance to current price
            # Calculate how far the trailing stop is from current price
            current_price_for_tra = signal.get("current_price", signal["price"])
            if trailing_price > 0 and current_price_for_tra > 0:
                tra_pct = abs((current_price_for_tra - trailing_price) / current_price_for_tra) * 100
                tra_item = QTableWidgetItem(f"{tra_pct:.2f}")
                tra_item.setForeground(QColor("#ff9800"))  # Orange for trailing
                self.signals_table.setItem(row, 9, tra_item)
            else:
                self.signals_table.setItem(row, 9, QTableWidgetItem("-"))

            # Lock column (10) - TR% Lock checkbox for active positions
            if is_active and trailing_price > 0:
                lock_checkbox = QCheckBox()
                # Block signals during initialization to prevent false triggers
                lock_checkbox.blockSignals(True)
                lock_checkbox.setChecked(signal.get("tr_lock_active", False))
                lock_checkbox.setToolTip(
                    "TR% Lock: Sperrt den TRA% Abstand.\n"
                    "Bei neuer Kerze wird TR nachgezogen wenn Kurs steigt (LONG) bzw. fällt (SHORT)."
                )
                # Calculate index in original signal_history list
                # recent_signals is reversed, so row 0 = last signal in history
                signal_index = len(self._signal_history) - 1 - row
                lock_checkbox.stateChanged.connect(
                    lambda state, idx=signal_index: self._on_row_tr_lock_changed(idx, state)
                )
                lock_checkbox.blockSignals(False)
                # Create widget container for centering
                lock_widget = QWidget()
                lock_layout = QHBoxLayout(lock_widget)
                lock_layout.addWidget(lock_checkbox)
                lock_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lock_layout.setContentsMargins(0, 0, 0, 0)
                self.signals_table.setCellWidget(row, 10, lock_widget)
            else:
                self.signals_table.setItem(row, 10, QTableWidgetItem("-"))

            # Status column (11)
            self.signals_table.setItem(row, 11, QTableWidgetItem(signal["status"]))

            # P&L columns - show for positions that have quantity (active OR closed)
            has_position = signal.get("quantity", 0) > 0
            status = signal["status"]
            is_closed = status.startswith("CLOSED")

            if has_position:
                current_price = signal.get("current_price", signal["price"])
                entry_price = signal["price"]
                pnl_currency = signal.get("pnl_currency", 0.0)
                pnl_percent = signal.get("pnl_percent", 0.0)

                # Current price (12) - show exit price for closed, current for active
                if is_closed:
                    current_item = QTableWidgetItem(f"{current_price:.2f} (Exit)")
                else:
                    current_item = QTableWidgetItem(f"{current_price:.2f}")
                self.signals_table.setItem(row, 12, current_item)

                # Price change % (Δ%) (13) - how much the price changed since entry
                if entry_price > 0:
                    price_change_pct = ((current_price - entry_price) / entry_price) * 100
                else:
                    price_change_pct = 0.0
                price_sign = "+" if price_change_pct >= 0 else ""
                price_color = "#26a69a" if price_change_pct >= 0 else "#ef5350"
                price_item = QTableWidgetItem(f"{price_sign}{price_change_pct:.2f}%")
                price_item.setForeground(QColor(price_color))
                self.signals_table.setItem(row, 13, price_item)

                # P&L in currency (14) - colored
                pnl_sign = "+" if pnl_currency >= 0 else ""
                pnl_item = QTableWidgetItem(f"{pnl_sign}{pnl_currency:.2f} €")
                pnl_color = "#26a69a" if pnl_currency >= 0 else "#ef5350"
                pnl_item.setForeground(QColor(pnl_color))
                self.signals_table.setItem(row, 14, pnl_item)

                # P&L in percent (15) - colored
                pct_sign = "+" if pnl_percent >= 0 else ""
                pct_item = QTableWidgetItem(f"{pct_sign}{pnl_percent:.2f}%")
                pct_item.setForeground(QColor(pnl_color))
                self.signals_table.setItem(row, 15, pct_item)
            else:
                # Empty cells for positions without quantity (candidates, pending)
                self.signals_table.setItem(row, 12, QTableWidgetItem("-"))
                self.signals_table.setItem(row, 13, QTableWidgetItem("-"))
                self.signals_table.setItem(row, 14, QTableWidgetItem("-"))
                self.signals_table.setItem(row, 15, QTableWidgetItem("-"))

        # Reset flag after table update
        self._signals_table_updating = False

    def _add_ki_log_entry(self, entry_type: str, message: str) -> None:
        """Add entry to KI log (uses local time)."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{entry_type}] {message}"
        self.ki_log_text.appendPlainText(entry)
        self._ki_log_entries.append({
            "time": timestamp,
            "type": entry_type,
            "message": message
        })

    def _log_bot_diagnostics(self) -> None:
        """Log periodic bot diagnostics for debugging."""
        if not self._bot_controller:
            return

        bc = self._bot_controller

        # Get current state
        state = bc.state.value if hasattr(bc.state, 'value') else str(bc.state)

        # Check can_trade conditions
        can_trade = bc.can_trade
        reasons = []

        if hasattr(bc, '_state_machine'):
            if bc._state_machine.is_paused():
                reasons.append("PAUSED")
            if bc._state_machine.is_error():
                reasons.append("ERROR")

        # Only check restrictions if enabled
        if not bc.config.bot.disable_restrictions:
            if bc._trades_today >= bc.config.risk.max_trades_per_day:
                reasons.append(f"MAX_TRADES({bc._trades_today}/{bc.config.risk.max_trades_per_day})")

            account_value = 10000.0
            daily_pnl_pct = (bc._daily_pnl / account_value) * 100
            if daily_pnl_pct <= -bc.config.risk.max_daily_loss_pct:
                reasons.append(f"MAX_LOSS({daily_pnl_pct:.2f}%)")

            if bc._consecutive_losses >= bc.config.risk.loss_streak_cooldown:
                reasons.append(f"LOSS_STREAK({bc._consecutive_losses}/{bc.config.risk.loss_streak_cooldown})")
        else:
            reasons.append("UNRESTRICTED")

        # Position status
        pos_status = "None"
        if bc.position:
            pos_status = f"{bc.position.side.value.upper()} @ {bc.position.entry_price:.2f}"

        # Build diagnostic message
        status_str = "✅" if can_trade else "❌"
        reason_str = ", ".join(reasons) if reasons else "OK"

        self._add_ki_log_entry(
            "DIAG",
            f"State={state} | CanTrade={status_str} [{reason_str}] | Pos={pos_status} | Trades={bc._trades_today} | Losses={bc._consecutive_losses}"
        )

    def update_strategy_scores(self, scores: list[dict]) -> None:
        """Update strategy scores table.

        Args:
            scores: List of strategy score dicts with keys:
                    name, score, profit_factor, win_rate, max_drawdown
        """
        self.strategy_scores_table.setRowCount(len(scores))
        for row, score_data in enumerate(scores):
            self.strategy_scores_table.setItem(
                row, 0, QTableWidgetItem(score_data.get("name", "-"))
            )
            self.strategy_scores_table.setItem(
                row, 1, QTableWidgetItem(f"{score_data.get('score', 0):.2f}")
            )
            self.strategy_scores_table.setItem(
                row, 2, QTableWidgetItem(f"{score_data.get('profit_factor', 0):.2f}")
            )
            self.strategy_scores_table.setItem(
                row, 3, QTableWidgetItem(f"{score_data.get('win_rate', 0):.1%}")
            )
            self.strategy_scores_table.setItem(
                row, 4, QTableWidgetItem(f"{score_data.get('max_drawdown', 0):.1%}")
            )

    def update_walk_forward_results(self, results: dict) -> None:
        """Update walk-forward results display.

        Args:
            results: Walk-forward results dict
        """
        text = []
        if results:
            text.append(f"Training Window: {results.get('training_days', 'N/A')} days")
            text.append(f"Test Window: {results.get('test_days', 'N/A')} days")
            text.append(f"IS Profit Factor: {results.get('is_pf', 0):.2f}")
            text.append(f"OOS Profit Factor: {results.get('oos_pf', 0):.2f}")
            text.append(f"OOS Degradation: {results.get('degradation', 0):.1%}")
            text.append(f"Passed Gate: {'Yes' if results.get('passed', False) else 'No'}")
        self.wf_results_text.setText("\n".join(text))

    def log_ki_request(self, request: dict, response: dict | None = None) -> None:
        """Log a KI request/response pair.

        Args:
            request: Request data sent to KI
            response: Response received (if any)
        """
        self._add_ki_log_entry("REQUEST", f"Sent: {len(str(request))} chars")
        if response:
            if response.get("error"):
                self._add_ki_log_entry("ERROR", response["error"])
            else:
                action = response.get("action", "unknown")
                confidence = response.get("confidence", 0)
                self._add_ki_log_entry(
                    "RESPONSE",
                    f"Action: {action}, Confidence: {confidence:.2f}"
                )

        # Update counts
        calls = int(self.ki_calls_today_label.text()) + 1
        self.ki_calls_today_label.setText(str(calls))
        self.ki_last_call_label.setText(datetime.now().strftime("%H:%M:%S"))

    # ==================== SIGNAL HISTORY PERSISTENCE ====================

    def _get_signal_history_key(self) -> str:
        """Get settings key for signal history based on current symbol."""
        symbol = getattr(self, 'symbol', '') or self._current_bot_symbol
        safe_symbol = symbol.replace("/", "_").replace(":", "_")
        return f"SignalHistory/{safe_symbol}"

    def _save_signal_history(self) -> None:
        """Save signal history to settings for the current symbol."""
        if not self._signal_history:
            return

        key = self._get_signal_history_key()
        if not key or key == "SignalHistory/":
            return

        try:
            # Convert to JSON-serializable format
            history_json = json.dumps(self._signal_history)
            self._bot_settings.setValue(key, history_json)
            logger.info(f"Saved {len(self._signal_history)} signals for {key}")
        except Exception as e:
            logger.error(f"Failed to save signal history: {e}")

    def _load_signal_history(self) -> None:
        """Load signal history from settings for the current symbol."""
        key = self._get_signal_history_key()
        if not key or key == "SignalHistory/":
            return

        try:
            history_json = self._bot_settings.value(key)
            if history_json:
                if isinstance(history_json, str):
                    self._signal_history = json.loads(history_json)
                else:
                    self._signal_history = history_json

                logger.info(f"Loaded {len(self._signal_history)} signals for {key}")

                # Update table
                if hasattr(self, 'signals_table'):
                    self._update_signals_table()

                # Check for active positions and schedule restoration
                active_positions = [s for s in self._signal_history
                                   if s.get("status") == "ENTERED" and s.get("is_open", False)]
                if active_positions:
                    logger.info(f"Found {len(active_positions)} active positions, scheduling restoration")
                    # Store active positions for later restoration when chart is ready
                    # P&L timer will be started in _restore_persisted_position after chart data loads
                    self._pending_position_restore = active_positions
                    # Connect to chart data_loaded signal if available
                    if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'data_loaded'):
                        self.chart_widget.data_loaded.connect(self._on_chart_data_loaded_restore_position)
                    else:
                        # Fallback: try after longer delay
                        QTimer.singleShot(2000, lambda: self._restore_persisted_position(active_positions))

        except Exception as e:
            logger.error(f"Failed to load signal history: {e}")

    def _on_chart_data_loaded_restore_position(self) -> None:
        """Called when chart data is loaded - restore persisted positions."""
        if hasattr(self, '_pending_position_restore') and self._pending_position_restore:
            logger.info("Chart data loaded - restoring persisted positions")
            # Small delay to ensure chart is fully rendered
            QTimer.singleShot(500, lambda: self._restore_persisted_position(self._pending_position_restore))
            # Disconnect signal to avoid multiple calls
            try:
                self.chart_widget.data_loaded.disconnect(self._on_chart_data_loaded_restore_position)
            except:
                pass

    def _restore_persisted_position(self, active_positions: list) -> None:
        """Restore chart elements and Current Position display for persisted positions."""
        if not active_positions:
            logger.warning("_restore_persisted_position called with no active positions")
            return

        # Use the most recent active position
        position = active_positions[-1]
        logger.info(f"Restoring persisted position: {position}")

        try:
            # 1. Update Current Position display
            side = position.get("side", "long")
            entry_price = position.get("price", 0)
            quantity = position.get("quantity", 0)
            stop_price = position.get("stop_price", 0)

            # If no stop_price saved, calculate from Initial SL % setting
            if stop_price == 0 and entry_price > 0:
                initial_sl_pct = self.initial_sl_spin.value() if hasattr(self, 'initial_sl_spin') else 2.0
                if side == "long":
                    stop_price = entry_price * (1 - initial_sl_pct / 100)
                else:  # short
                    stop_price = entry_price * (1 + initial_sl_pct / 100)
                logger.info(f"Calculated fallback stop_price: {stop_price:.2f} (entry={entry_price:.2f}, SL%={initial_sl_pct}%, side={side})")
                # Save the calculated stop_price to signal history
                position["stop_price"] = stop_price
                self._save_signal_history()

            logger.info(f"Position details: side={side}, entry={entry_price}, qty={quantity}, stop={stop_price}")

            self.position_side_label.setText(side.upper())
            self.position_side_label.setStyleSheet(
                f"font-weight: bold; color: {'#26a69a' if side == 'long' else '#ef5350'};"
            )
            self.position_entry_label.setText(f"{entry_price:.4f}")
            self.position_size_label.setText(f"{quantity:.4f}")

            # Calculate and display invested amount
            initial_cap = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000.0
            risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10.0
            invested = initial_cap * (risk_pct / 100)
            self.position_invested_label.setText(f"{invested:.2f} €")

            if stop_price > 0:
                self.position_stop_label.setText(f"{stop_price:.4f}")
            else:
                self.position_stop_label.setText("-")
                logger.warning("No stop_price found in persisted position!")

            # Bars held - estimate from signal time if possible
            self.position_bars_held_label.setText("N/A (restored)")

            # 2. Draw stop line on chart
            if stop_price > 0:
                if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'add_stop_line'):
                    # Get SL% from position or calculate
                    initial_sl_pct = position.get("initial_sl_pct", 0.0)
                    if initial_sl_pct <= 0 and entry_price > 0:
                        initial_sl_pct = abs((stop_price - entry_price) / entry_price) * 100
                    sl_label = f"SL @ {stop_price:.2f} ({initial_sl_pct:.2f}%)" if initial_sl_pct > 0 else f"SL @ {stop_price:.2f}"

                    logger.info(f"Drawing stop line @ {stop_price:.2f} ({initial_sl_pct:.2f}%)")
                    self.chart_widget.add_stop_line(
                        "initial_stop",
                        stop_price,
                        line_type="initial",
                        color="#ef5350",  # Red for initial stop loss
                        label=sl_label
                    )
                    logger.info(f"Restored stop line @ {stop_price:.2f}")
                    self._add_ki_log_entry("RESTORE", f"Stop-Line wiederhergestellt @ {stop_price:.2f} ({initial_sl_pct:.2f}%)")
                else:
                    logger.warning(f"Cannot draw stop line: chart_widget={hasattr(self, 'chart_widget')}, add_stop_line={hasattr(self.chart_widget, 'add_stop_line') if hasattr(self, 'chart_widget') else 'N/A'}")
            else:
                logger.warning(f"stop_price is {stop_price}, not drawing stop line")

            # 2b. Draw entry marker or line on chart
            entry_timestamp = position.get("entry_timestamp")
            if hasattr(self, 'chart_widget'):
                if entry_timestamp and hasattr(self.chart_widget, 'add_entry_confirmed'):
                    # Use marker if timestamp available
                    score = position.get("score", 0)
                    self.chart_widget.add_entry_confirmed(
                        timestamp=entry_timestamp,
                        price=entry_price,
                        side=side,
                        score=score * 100 if score <= 1 else score  # Normalize score
                    )
                    logger.info(f"Restored entry marker @ {entry_price:.2f} at timestamp {entry_timestamp}")
                    self._add_ki_log_entry("RESTORE", f"Entry-Marker wiederhergestellt @ {entry_price:.2f}")
                elif hasattr(self.chart_widget, 'add_stop_line'):
                    # Fallback: use horizontal line for entry (green, dashed)
                    entry_color = "#26a69a" if side == "long" else "#ef5350"
                    self.chart_widget.add_stop_line(
                        "entry_line",
                        entry_price,
                        line_type="target",  # Will use green color by default
                        color=entry_color,
                        label=f"Entry @ {entry_price:.2f}"
                    )
                    logger.info(f"Restored entry line @ {entry_price:.2f}")
                    self._add_ki_log_entry("RESTORE", f"Entry-Line wiederhergestellt @ {entry_price:.2f}")

            # 2c. Draw trailing stop line if available (separate from initial stop)
            trailing_stop_price = position.get("trailing_stop_price", 0.0)
            logger.info(f"[RESTORE DEBUG] trailing_stop_price from position: {trailing_stop_price}")

            # Fallback: Calculate trailing stop if not saved but profit exceeds trigger
            if trailing_stop_price == 0 and entry_price > 0 and hasattr(self, 'chart_widget'):
                # Get current price from chart data
                current_price = None
                if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                    if len(self.chart_widget.data) > 0:
                        try:
                            current_price = float(self.chart_widget.data.iloc[-1]['close'])
                        except (KeyError, IndexError, TypeError):
                            pass

                if current_price:
                    # Calculate current profit %
                    if side == "long":
                        profit_pct = ((current_price - entry_price) / entry_price) * 100
                    else:  # short
                        profit_pct = ((entry_price - current_price) / entry_price) * 100

                    # Get trailing stop settings
                    trailing_trigger = self.trailing_trigger_spin.value() if hasattr(self, 'trailing_trigger_spin') else 0.2
                    trailing_pct = self.trailing_distance_spin.value() if hasattr(self, 'trailing_distance_spin') else 0.35

                    logger.info(f"Trailing stop fallback check: profit={profit_pct:.2f}%, trigger={trailing_trigger}%, trailing_pct={trailing_pct}%")

                    # If profit exceeds trigger, calculate and set trailing stop
                    if profit_pct >= trailing_trigger:
                        if side == "long":
                            trailing_stop_price = current_price * (1 - trailing_pct / 100)
                        else:  # short
                            trailing_stop_price = current_price * (1 + trailing_pct / 100)

                        # Save to signal history
                        position["trailing_stop_price"] = trailing_stop_price
                        position["trailing_stop_pct"] = trailing_pct
                        self._save_signal_history()

                        logger.info(f"Calculated fallback trailing stop: {trailing_stop_price:.2f} (profit={profit_pct:.2f}% >= trigger={trailing_trigger}%)")
                        self._add_ki_log_entry("RESTORE", f"Trailing Stop berechnet @ {trailing_stop_price:.2f} (Gewinn {profit_pct:.2f}% >= {trailing_trigger}%)")

            if trailing_stop_price > 0 and hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'add_stop_line'):
                # Get TR% from position or calculate
                trailing_stop_pct = position.get("trailing_stop_pct", 0.0)
                if trailing_stop_pct <= 0 and entry_price > 0:
                    trailing_stop_pct = abs((trailing_stop_price - entry_price) / entry_price) * 100

                # Get current_price for TRA% calculation
                tr_current_price = position.get("current_price", 0.0)
                if tr_current_price == 0 and hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                    if len(self.chart_widget.data) > 0:
                        try:
                            tr_current_price = float(self.chart_widget.data.iloc[-1]['close'])
                        except (KeyError, IndexError, TypeError):
                            tr_current_price = 0.0

                # Calculate TRA% (distance from current price)
                tra_pct = 0.0
                if tr_current_price > 0:
                    tra_pct = abs((tr_current_price - trailing_stop_price) / tr_current_price) * 100
                tr_label = f"TSL @ {trailing_stop_price:.2f} ({trailing_stop_pct:.2f}% / TRA: {tra_pct:.2f}%)"

                self.chart_widget.add_stop_line(
                    "trailing_stop",
                    trailing_stop_price,
                    line_type="trailing",
                    color="#ff9800",  # Orange for trailing stop
                    label=tr_label
                )
                logger.info(f"Restored trailing stop line @ {trailing_stop_price:.2f} ({trailing_stop_pct:.2f}% / TRA: {tra_pct:.2f}%)")
                self._add_ki_log_entry("RESTORE", f"Trailing Stop-Line wiederhergestellt @ {trailing_stop_price:.2f} ({trailing_stop_pct:.2f}% / TRA: {tra_pct:.2f}%)")

            # 3. Log the restoration
            self._add_ki_log_entry(
                "RESTORE",
                f"Position wiederhergestellt: {side.upper()} {quantity:.4f} @ {entry_price:.4f}, Stop: {stop_price:.2f}"
            )

            # 4. Update signals table to show current data
            self._update_signals_table()
            logger.info("Signals table updated after restoration")

            # 5. Start P&L update timer (now that chart data is available)
            self._start_pnl_update_timer()
            logger.info("P&L update timer started for restored position")

            # Clear pending restore
            self._pending_position_restore = None

        except Exception as e:
            logger.error(f"Failed to restore persisted position: {e}", exc_info=True)

    def _start_pnl_update_timer(self) -> None:
        """Start timer for live P&L updates on restored positions."""
        if not hasattr(self, '_pnl_update_timer') or self._pnl_update_timer is None:
            self._pnl_update_timer = QTimer()
            self._pnl_update_timer.timeout.connect(self._update_restored_positions_pnl)
            self._pnl_update_timer.start(1000)  # Update every second

    def _update_restored_positions_pnl(self) -> None:
        """Update P&L for restored positions using current price."""
        # Get current price from chart widget's data DataFrame
        current_price = None
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'data'):
            chart_data = self.chart_widget.data
            if chart_data is not None and len(chart_data) > 0:
                try:
                    current_price = float(chart_data.iloc[-1]['close'])
                except (KeyError, IndexError, TypeError):
                    pass

        if current_price is None:
            return

        updated = False
        for signal in self._signal_history:
            if signal.get("status") == "ENTERED" and signal.get("is_open", False):
                entry_price = signal.get("price", 0)
                quantity = signal.get("quantity", 0)
                side = signal.get("side", "long")

                if quantity > 0 and entry_price > 0:
                    # Get invested capital
                    invested_capital = signal.get("invested_capital", 0)
                    if invested_capital <= 0:
                        initial_cap = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000.0
                        risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10.0
                        invested_capital = initial_cap * (risk_pct / 100)

                    # Calculate price change percentage
                    price_change_pct = ((current_price - entry_price) / entry_price) * 100

                    # P&L based on price change: LONG = price change, SHORT = -price change
                    if side == "long":
                        pnl_percent = price_change_pct
                    else:
                        pnl_percent = -price_change_pct

                    # P&L€ = invested × P&L%
                    pnl_currency = invested_capital * (pnl_percent / 100)

                    signal["current_price"] = current_price
                    signal["pnl_currency"] = pnl_currency
                    signal["pnl_percent"] = pnl_percent
                    updated = True

                    # Also update Current Position display
                    self.position_current_label.setText(f"{current_price:.4f}")
                    pnl_color = "#26a69a" if pnl_currency >= 0 else "#ef5350"
                    pnl_sign = "+" if pnl_currency >= 0 else ""
                    self.position_pnl_label.setText(f"{pnl_sign}{pnl_currency:.2f} € ({pnl_sign}{pnl_percent:.2f}%)")
                    self.position_pnl_label.setStyleSheet(f"font-weight: bold; color: {pnl_color}; font-size: 14px;")

        if updated:
            self._update_signals_table()

    # ==================== SIGNALS TABLE CONTEXT MENU ====================

    def _show_signals_context_menu(self, position) -> None:
        """Show context menu for signals table."""
        row = self.signals_table.rowAt(position.y())
        if row < 0:
            return

        # Get the signal data for this row
        recent_signals = list(reversed(self._signal_history[-20:]))
        if row >= len(recent_signals):
            return

        signal = recent_signals[row]
        status = signal.get("status", "")
        is_entered = status == "ENTERED" and signal.get("is_open", False)

        menu = QMenu(self.signals_table)

        # Sell action - only for ENTERED positions
        sell_action = QAction("Verkaufen (Sofort)", menu)
        sell_action.setEnabled(is_entered)
        if is_entered:
            sell_action.triggered.connect(lambda: self._sell_signal(row, signal))
        menu.addAction(sell_action)

        menu.addSeparator()

        # Delete action - only for non-ENTERED signals
        delete_action = QAction("Löschen", menu)
        delete_action.setEnabled(not is_entered)
        if not is_entered:
            delete_action.triggered.connect(lambda: self._delete_signal(row, signal))
        menu.addAction(delete_action)

        menu.exec(self.signals_table.viewport().mapToGlobal(position))

    def _sell_signal(self, row: int, signal: dict) -> None:
        """Sell/close the position for the given signal."""
        symbol = getattr(self, 'symbol', '') or self._current_bot_symbol
        side = signal.get("side", "long")
        quantity = signal.get("quantity", 0)

        if quantity <= 0:
            QMessageBox.warning(self, "Fehler", "Keine gültige Position zum Verkaufen.")
            return

        # Confirm sell
        reply = QMessageBox.question(
            self,
            "Position verkaufen",
            f"Position {side.upper()} {quantity:.4f} {symbol} sofort verkaufen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Get current price for exit
        exit_price = signal.get("current_price", signal.get("price", 0))

        try:
            # If bot controller exists, reset its position
            if self._bot_controller and self._bot_controller._position:
                self._bot_controller._position = None
                # Remove stop lines from chart
                if hasattr(self, 'chart_widget'):
                    self.chart_widget.remove_stop_line("initial_stop")
                    self.chart_widget.remove_stop_line("trailing_stop")
                self._add_ki_log_entry("MANUAL", f"Position manuell geschlossen: {side} {quantity:.4f} @ {exit_price:.4f}")
            else:
                # Manual update without bot controller
                self._add_ki_log_entry("MANUAL", f"Position manuell als geschlossen markiert: {side} {quantity:.4f}")

            # Update signal status
            # Find the actual signal in history (row is reversed)
            actual_index = len(self._signal_history) - 1 - row
            if 0 <= actual_index < len(self._signal_history):
                sig = self._signal_history[actual_index]

                # Get invested capital
                invested_capital = sig.get("invested_capital", 0)
                if invested_capital <= 0:
                    initial_cap = self.bot_capital_spin.value() if hasattr(self, 'bot_capital_spin') else 10000.0
                    risk_pct = self.risk_per_trade_spin.value() if hasattr(self, 'risk_per_trade_spin') else 10.0
                    invested_capital = initial_cap * (risk_pct / 100)

                # Calculate price change percentage
                entry_price = sig.get("price", 0)
                price_change_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0

                # P&L based on price change: LONG = price change, SHORT = -price change
                if side == "long":
                    pnl_percent = price_change_pct
                else:
                    pnl_percent = -price_change_pct

                # P&L€ = invested × P&L%
                pnl_currency = invested_capital * (pnl_percent / 100)

                sig["status"] = "CLOSED (MANUAL)"
                sig["is_open"] = False
                sig["current_price"] = exit_price
                sig["pnl_currency"] = pnl_currency
                sig["pnl_percent"] = pnl_percent

            self._update_signals_table()
            self._save_signal_history()

            QMessageBox.information(
                self,
                "Position geschlossen",
                f"Position wurde geschlossen.\nP&L: {pnl_currency:+.2f}€ ({pnl_percent:+.2f}%)"
            )

        except Exception as e:
            logger.error(f"Error selling signal: {e}")
            QMessageBox.critical(self, "Fehler", f"Fehler beim Verkaufen: {e}")

    def _delete_signal(self, row: int, signal: dict) -> None:
        """Delete a signal from history (only non-ENTERED signals)."""
        status = signal.get("status", "")
        if status == "ENTERED" and signal.get("is_open", False):
            QMessageBox.warning(
                self,
                "Löschen nicht möglich",
                "Aktive Positionen können nicht gelöscht werden.\nBitte erst verkaufen."
            )
            return

        # Confirm delete
        reply = QMessageBox.question(
            self,
            "Signal löschen",
            f"Signal '{signal.get('type', 'unknown')}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Find and remove the actual signal (row is reversed)
        actual_index = len(self._signal_history) - 1 - row
        if 0 <= actual_index < len(self._signal_history):
            removed = self._signal_history.pop(actual_index)
            logger.info(f"Deleted signal: {removed}")
            self._update_signals_table()
            self._save_signal_history()

    # ==================== CHART TRADING (BIDIRECTIONAL) ====================

    def _connect_chart_line_signals(self) -> None:
        """Connect chart line drag signals for bidirectional chart trading."""
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'stop_line_moved'):
            self.chart_widget.stop_line_moved.connect(self._on_chart_stop_line_moved)
            logger.info("Connected chart stop_line_moved signal for chart trading")
        # Connect candle closed signal for TR% lock feature
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'candle_closed'):
            self.chart_widget.candle_closed.connect(self._on_candle_closed)
            logger.info("Connected candle_closed signal for TR% lock feature")

    def _on_chart_stop_line_moved(self, line_id: str, new_price: float) -> None:
        """Handle stop line being dragged in the chart.

        Updates the signal history, table, and recalculates dependent values.

        Args:
            line_id: ID of the line ("initial_stop", "trailing_stop", "entry_line")
            new_price: New price after drag
        """
        logger.info(f"Chart line moved: {line_id} -> {new_price:.4f}")

        # Find the active position in signal history
        for sig in reversed(self._signal_history):
            if sig.get("status") == "ENTERED" and sig.get("is_open", False):
                entry_price = sig.get("price", 0)
                side = sig.get("side", "long")

                if line_id == "initial_stop":
                    # Update stop price and recalculate SL%
                    sig["stop_price"] = new_price
                    new_sl_pct = 0.0
                    if entry_price > 0:
                        new_sl_pct = abs((new_price - entry_price) / entry_price) * 100
                        sig["initial_sl_pct"] = new_sl_pct
                    self._add_ki_log_entry("CHART", f"Stop Loss verschoben → {new_price:.2f} ({new_sl_pct:.2f}%)")
                    logger.info(f"Updated initial_stop to {new_price:.2f}")

                    # Redraw line with correct label including %
                    if hasattr(self, "chart_widget") and self.chart_widget:
                        label = f"SL @ {new_price:.2f} ({new_sl_pct:.2f}%)"
                        self.chart_widget.add_stop_line(
                            line_id="initial_stop",
                            price=new_price,
                            line_type="initial",
                            label=label
                        )

                elif line_id == "trailing_stop":
                    # Update trailing stop price (NOT stop_price - that's the initial SL!)
                    sig["trailing_stop_price"] = new_price
                    # Recalculate TR% from entry price
                    new_tr_pct = 0.0
                    if entry_price > 0:
                        if side == "long":
                            new_tr_pct = abs((entry_price - new_price) / entry_price) * 100
                        else:
                            new_tr_pct = abs((new_price - entry_price) / entry_price) * 100
                        sig["trailing_stop_pct"] = new_tr_pct
                    # Calculate TRA% from current price
                    current_price = sig.get("current_price", entry_price)
                    tra_pct = abs((current_price - new_price) / current_price) * 100 if current_price > 0 else 0.0
                    self._add_ki_log_entry("CHART", f"Trailing Stop verschoben → {new_price:.2f} ({new_tr_pct:.2f}% / TRA: {tra_pct:.2f}%)")
                    logger.info(f"Updated trailing_stop to {new_price:.2f}")

                    # Redraw line with correct label including % and TRA%
                    if hasattr(self, "chart_widget") and self.chart_widget:
                        label = f"TSL @ {new_price:.2f} ({new_tr_pct:.2f}% / TRA: {tra_pct:.2f}%)"
                        self.chart_widget.add_stop_line(
                            line_id="trailing_stop",
                            price=new_price,
                            line_type="trailing",
                            label=label
                        )

                elif line_id == "entry_line":
                    # Update entry price and recalculate SL%
                    old_entry = entry_price
                    sig["price"] = new_price
                    # Recalculate SL% based on new entry
                    stop_price = sig.get("stop_price", 0)
                    if new_price > 0 and stop_price > 0:
                        sig["initial_sl_pct"] = abs((stop_price - new_price) / new_price) * 100
                    self._add_ki_log_entry("CHART", f"Entry verschoben → {new_price:.2f} (war {old_entry:.2f})")
                    logger.info(f"Updated entry_line to {new_price:.2f}")

                # CRITICAL: Sync stop changes to bot controller for stop-hit detection
                if line_id in ("initial_stop", "trailing_stop"):
                    self._sync_stop_to_bot_controller(new_price)

                # Save and update UI
                self._save_signal_history()
                self._update_signals_table()
                break

    def _on_signals_table_cell_changed(self, row: int, column: int) -> None:
        """Handle table cell editing - update chart lines when SL% or TR% changes.

        This enables bidirectional editing: Table → Chart
        Column 6 = SL%, Column 7 = TR%

        Args:
            row: Row index that was edited
            column: Column index that was edited (6=SL%, 7=TR%)
        """
        # Skip if we're programmatically updating the table
        if self._signals_table_updating:
            return

        # Only handle SL% (col 6) and TR% (col 7) columns
        if column not in (6, 7):
            return

        # Get the edited cell
        item = self.signals_table.item(row, column)
        if not item:
            return

        # Parse the new percentage value
        try:
            new_pct = float(item.text().replace(",", ".").replace("%", "").strip())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid percentage value in row {row}, column {column}")
            return

        if new_pct <= 0:
            logger.warning(f"Percentage must be positive: {new_pct}")
            return

        # Find the corresponding signal in history
        # Table rows are in reverse order of signal_history
        visible_signals = [s for s in self._signal_history if s.get("status") in ("ENTERED", "EXITED")]
        signal_idx = len(visible_signals) - 1 - row

        if signal_idx < 0 or signal_idx >= len(visible_signals):
            logger.warning(f"Could not find signal for row {row}")
            return

        sig = visible_signals[signal_idx]

        # Only allow editing active positions
        if not (sig.get("status") == "ENTERED" and sig.get("is_open", False)):
            logger.info(f"Signal at row {row} is not an active position")
            return

        entry_price = sig.get("price", 0)
        side = sig.get("side", "long")

        if entry_price <= 0:
            logger.warning(f"Invalid entry price: {entry_price}")
            return

        # Calculate new stop price based on side
        if side == "long":
            new_stop_price = entry_price * (1 - new_pct / 100)
        else:
            new_stop_price = entry_price * (1 + new_pct / 100)

        logger.info(f"Table edit: col={column}, new_pct={new_pct:.2f}%, new_stop={new_stop_price:.2f}")

        if column == 6:  # SL% - Update Initial Stop Loss
            sig["stop_price"] = new_stop_price
            sig["initial_sl_pct"] = new_pct

            # Update chart line
            if hasattr(self, "chart_widget") and self.chart_widget:
                label = f"SL @ {new_stop_price:.2f} ({new_pct:.2f}%)"
                self.chart_widget.add_stop_line(
                    line_id="initial_stop",
                    price=new_stop_price,
                    line_type="initial",
                    label=label
                )

            self._add_ki_log_entry("TABLE", f"Stop Loss geändert → {new_stop_price:.2f} ({new_pct:.2f}%)")
            logger.info(f"Updated initial_stop from table to {new_stop_price:.2f}")

        elif column == 7:  # TR% - Update Trailing Stop
            sig["trailing_stop_price"] = new_stop_price
            sig["trailing_stop_pct"] = new_pct
            # NOTE: Do NOT update sig["stop_price"] - that's for initial SL only!

            # Calculate TRA% from current price
            current_price = sig.get("current_price", entry_price)
            tra_pct = abs((current_price - new_stop_price) / current_price) * 100 if current_price > 0 else 0.0

            # Update chart line with TRA%
            if hasattr(self, "chart_widget") and self.chart_widget:
                label = f"TSL @ {new_stop_price:.2f} ({new_pct:.2f}% / TRA: {tra_pct:.2f}%)"
                self.chart_widget.add_stop_line(
                    line_id="trailing_stop",
                    price=new_stop_price,
                    line_type="trailing",
                    label=label
                )

            self._add_ki_log_entry("TABLE", f"Trailing Stop geändert → {new_stop_price:.2f} ({new_pct:.2f}% / TRA: {tra_pct:.2f}%)")
            logger.info(f"Updated trailing_stop from table to {new_stop_price:.2f}")

        # CRITICAL: Sync stop changes to bot controller for stop-hit detection
        self._sync_stop_to_bot_controller(new_stop_price)

        # Save changes
        self._save_signal_history()

        # Update the table to show calculated values (e.g., TR Kurs)
        # Set flag to prevent recursive cellChanged
        self._signals_table_updating = True
        try:
            self._update_signals_table()
        finally:
            self._signals_table_updating = False

    def _sync_stop_to_bot_controller(self, new_stop_price: float) -> None:
        """Sync stop price to bot controller's internal position.

        CRITICAL: The bot controller's position.trailing.current_stop_price
        must be updated for stop-hit detection to work correctly.
        Without this sync, the visual stop line and the actual bot stop are different!

        Args:
            new_stop_price: New stop price to sync
        """
        if not hasattr(self, '_bot_controller') or not self._bot_controller:
            logger.debug("No bot controller to sync stop to")
            return

        position = getattr(self._bot_controller, '_position', None)
        if not position:
            logger.debug("Bot controller has no active position")
            return

        trailing = getattr(position, 'trailing', None)
        if not trailing:
            logger.debug("Position has no trailing state")
            return

        old_stop = trailing.current_stop_price
        trailing.current_stop_price = new_stop_price

        # Also update initial_stop_price if this is lower (for initial SL drag)
        if new_stop_price < trailing.initial_stop_price:
            trailing.initial_stop_price = new_stop_price

        logger.info(
            f"[BOT SYNC] Stop synced to bot controller: {old_stop:.4f} → {new_stop_price:.4f}"
        )
        self._add_ki_log_entry(
            "SYNC",
            f"Bot-Stop synchronisiert: {old_stop:.2f} → {new_stop_price:.2f}"
        )

    # ==================== TR% LOCK FEATURE (Per-Signal) ====================

    def _on_row_tr_lock_changed(self, signal_index: int, state: int) -> None:
        """Handle TR% lock checkbox change for a specific signal row.

        When activated, stores the current TRA% (trailing distance from current price)
        in the signal so it can be maintained as the price moves.

        Args:
            signal_index: Index of the signal in _signal_history
            state: Checkbox state
        """
        is_locked = state == Qt.CheckState.Checked.value

        # Get signal by index
        if signal_index < 0 or signal_index >= len(self._signal_history):
            logger.warning(f"TR% Lock: Signal-Index {signal_index} ungültig")
            return

        signal = self._signal_history[signal_index]

        if is_locked:
            # Calculate current TRA% (distance from current price to trailing stop)
            current_price = signal.get("current_price", signal.get("price", 0))
            trailing_price = signal.get("trailing_stop_price", 0)

            if current_price <= 0 or trailing_price <= 0:
                logger.warning(f"TR% Lock: Ungültige Preise für Signal #{signal_index}")
                return

            # Calculate TRA% - distance from current price
            tra_pct = abs((current_price - trailing_price) / current_price) * 100

            # Store lock state in signal
            signal["tr_lock_active"] = True
            signal["tr_lock_tra_pct"] = tra_pct
            signal["tr_lock_last_close"] = current_price

            logger.info(
                f"TR% Lock aktiviert für Signal #{signal_index}: TRA%={tra_pct:.2f}%, "
                f"Side={signal.get('side', 'LONG')}, Price={current_price:.2f}, TR={trailing_price:.2f}"
            )
            self._add_ki_log_entry(
                "TR_LOCK",
                f"TR% Lock aktiviert: TRA%={tra_pct:.2f}% bei Kurs {current_price:.2f}"
            )
        else:
            # Clear lock state in signal
            signal["tr_lock_active"] = False
            signal.pop("tr_lock_tra_pct", None)
            signal.pop("tr_lock_last_close", None)

            logger.info(f"TR% Lock deaktiviert für Signal #{signal_index}")
            self._add_ki_log_entry("TR_LOCK", "TR% Lock deaktiviert")

        self._save_signal_history()

    def _get_signals_with_active_lock(self) -> list[dict]:
        """Get all signals that have TR% lock active."""
        locked_signals = []
        for signal in self._signal_history:
            if signal.get("tr_lock_active", False):
                status = signal.get("status", "")
                # Only include active positions
                if status == "ENTERED" and signal.get("is_open", False):
                    locked_signals.append(signal)
        return locked_signals

    def _on_candle_closed(self, previous_close: float, new_open: float) -> None:
        """Handle candle close event for TR% lock feature.

        When TR% lock is active on any signal, adjusts the trailing stop
        to maintain the locked TRA% distance from the new price.

        Args:
            previous_close: Close price of the closed candle
            new_open: Open price of the new candle (current price)
        """
        # Get all signals with active TR% lock
        locked_signals = self._get_signals_with_active_lock()
        if not locked_signals:
            return

        current_price = previous_close  # Use the just-closed candle's close
        any_updated = False

        for signal in locked_signals:
            # Get lock parameters from signal
            locked_tra_pct = signal.get("tr_lock_tra_pct", 0)
            if locked_tra_pct <= 0:
                continue

            locked_side = signal.get("side", "LONG").upper()
            last_close = signal.get("tr_lock_last_close", current_price)
            signal_time = signal.get("time", "?")

            # Check direction condition
            # LONG: Only adjust if price rose (new close > previous close)
            # SHORT: Only adjust if price fell (new close < previous close)
            if locked_side == "LONG":
                if current_price <= last_close:
                    logger.debug(
                        f"TR% Lock (LONG, {signal_time}): Kurs nicht gestiegen "
                        f"({last_close:.2f} → {current_price:.2f}), TR-Linie bleibt"
                    )
                    signal["tr_lock_last_close"] = current_price
                    continue
            else:  # SHORT
                if current_price >= last_close:
                    logger.debug(
                        f"TR% Lock (SHORT, {signal_time}): Kurs nicht gefallen "
                        f"({last_close:.2f} → {current_price:.2f}), TR-Linie bleibt"
                    )
                    signal["tr_lock_last_close"] = current_price
                    continue

            # Calculate new trailing stop price based on locked TRA%
            if locked_side == "LONG":
                new_trailing_price = current_price * (1 - locked_tra_pct / 100)
            else:
                new_trailing_price = current_price * (1 + locked_tra_pct / 100)

            old_trailing = signal.get("trailing_stop_price", 0)

            # Only move trailing stop in the favorable direction
            if locked_side == "LONG":
                if new_trailing_price <= old_trailing:
                    logger.debug(
                        f"TR% Lock (LONG, {signal_time}): Neuer TR ({new_trailing_price:.2f}) "
                        f"nicht höher als alter TR ({old_trailing:.2f}), übersprungen"
                    )
                    signal["tr_lock_last_close"] = current_price
                    continue
            else:
                if new_trailing_price >= old_trailing:
                    logger.debug(
                        f"TR% Lock (SHORT, {signal_time}): Neuer TR ({new_trailing_price:.2f}) "
                        f"nicht niedriger als alter TR ({old_trailing:.2f}), übersprungen"
                    )
                    signal["tr_lock_last_close"] = current_price
                    continue

            # Update signal
            signal["trailing_stop_price"] = new_trailing_price
            entry_price = signal.get("price", current_price)
            new_tr_pct = abs((entry_price - new_trailing_price) / entry_price) * 100
            signal["trailing_stop_pct"] = new_tr_pct
            signal["current_price"] = current_price
            signal["tr_lock_last_close"] = current_price

            # Update chart line (using standard trailing_stop line_id)
            if hasattr(self, 'chart_widget'):
                new_tra_pct = abs((current_price - new_trailing_price) / current_price) * 100
                label_text = f"TSL @ {new_trailing_price:.2f} ({new_tr_pct:.2f}% / TRA: {new_tra_pct:.2f}%)"
                self.chart_widget.update_stop_line(
                    line_id="trailing_stop",
                    new_price=new_trailing_price,
                    label=label_text
                )

            # Sync to bot controller
            self._sync_stop_to_bot_controller(new_trailing_price)

            logger.info(
                f"TR% Lock ({signal_time}): TR nachgezogen {old_trailing:.2f} → {new_trailing_price:.2f} "
                f"(TRA%={locked_tra_pct:.2f}%, Kurs={current_price:.2f})"
            )
            self._add_ki_log_entry(
                "TR_LOCK",
                f"TR nachgezogen: {old_trailing:.2f} → {new_trailing_price:.2f}"
            )
            any_updated = True

        if any_updated:
            self._update_signals_table()
            self._save_signal_history()
