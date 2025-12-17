"""Bot Panels Mixin for ChartWindow.

Provides additional tabs for tradingbot control and monitoring:
- Bot Control (Start/Stop, Settings)
- Daily Strategy Selection
- Signals & Trade Management
- KI Logs
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
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

    def _create_bot_control_tab(self) -> QWidget:
        """Create bot control tab with start/stop and settings."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ==================== CONTROL GROUP ====================
        control_group = QGroupBox("Bot Control")
        control_layout = QVBoxLayout()

        # Status indicator
        status_layout = QHBoxLayout()
        self.bot_status_label = QLabel("Status: STOPPED")
        self.bot_status_label.setStyleSheet(
            "font-weight: bold; color: #9e9e9e; font-size: 14px;"
        )
        status_layout.addWidget(self.bot_status_label)
        status_layout.addStretch()
        control_layout.addLayout(status_layout)

        # Start/Stop buttons
        btn_layout = QHBoxLayout()

        self.bot_start_btn = QPushButton("Start Bot")
        self.bot_start_btn.setStyleSheet(
            "background-color: #26a69a; color: white; font-weight: bold; "
            "padding: 10px 20px;"
        )
        self.bot_start_btn.clicked.connect(self._on_bot_start_clicked)
        btn_layout.addWidget(self.bot_start_btn)

        self.bot_stop_btn = QPushButton("Stop Bot")
        self.bot_stop_btn.setStyleSheet(
            "background-color: #ef5350; color: white; font-weight: bold; "
            "padding: 10px 20px;"
        )
        self.bot_stop_btn.setEnabled(False)
        self.bot_stop_btn.clicked.connect(self._on_bot_stop_clicked)
        btn_layout.addWidget(self.bot_stop_btn)

        self.bot_pause_btn = QPushButton("Pause")
        self.bot_pause_btn.setStyleSheet("padding: 10px;")
        self.bot_pause_btn.setEnabled(False)
        self.bot_pause_btn.clicked.connect(self._on_bot_pause_clicked)
        btn_layout.addWidget(self.bot_pause_btn)

        control_layout.addLayout(btn_layout)

        # Risk Warning Banner
        risk_warning = QLabel(
            "⚠️ RISIKO-HINWEIS: Automatisierter Handel birgt erhebliche Risiken. "
            "Vergangene Performance garantiert keine zukünftigen Ergebnisse. "
            "Handeln Sie nur mit Kapital, dessen Verlust Sie verkraften können. "
            "Keine Anlageberatung!"
        )
        risk_warning.setWordWrap(True)
        risk_warning.setStyleSheet(
            "background-color: #fff3cd; color: #856404; padding: 8px; "
            "border: 1px solid #ffc107; border-radius: 4px; font-size: 11px;"
        )
        control_layout.addWidget(risk_warning)

        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        # ==================== SETTINGS GROUP ====================
        settings_group = QGroupBox("Bot Settings")
        settings_layout = QFormLayout()

        # Symbol (read from chart)
        self.bot_symbol_label = QLabel("AAPL")
        self.bot_symbol_label.setStyleSheet("font-weight: bold;")
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
            "• PCT: Fester Prozent-Abstand vom Höchst-/Tiefstpreis\n"
            "• ATR: Volatilitäts-basiert (ATR-Multiple), Regime-angepasst\n"
            "• SWING: Bollinger Bands als Support/Resistance"
        )
        settings_layout.addRow("Trailing Mode:", self.trailing_mode_combo)

        # Initial Stop Loss %
        self.initial_sl_spin = QDoubleSpinBox()
        self.initial_sl_spin.setRange(0.1, 10.0)
        self.initial_sl_spin.setValue(2.0)
        self.initial_sl_spin.setSuffix(" %")
        self.initial_sl_spin.setDecimals(1)
        self.initial_sl_spin.setToolTip(
            "Initial Stop-Loss in Prozent vom Entry-Preis.\n"
            "Dies ist der EINZIGE fixe Parameter - alle anderen Exits sind dynamisch.\n"
            "Empfohlen: 1.5-3% für Aktien, 2-5% für Crypto."
        )
        settings_layout.addRow("Initial SL %:", self.initial_sl_spin)

        # Risk per trade %
        self.risk_per_trade_spin = QDoubleSpinBox()
        self.risk_per_trade_spin.setRange(0.1, 5.0)
        self.risk_per_trade_spin.setValue(1.0)
        self.risk_per_trade_spin.setSuffix(" %")
        self.risk_per_trade_spin.setDecimals(1)
        self.risk_per_trade_spin.setToolTip(
            "Maximales Risiko pro Trade in Prozent des Kontostands.\n"
            "Bestimmt die Positionsgröße: Größere SL% = kleinere Position.\n"
            "Empfohlen: 0.5-2% für konservativ, max 3% für aggressiv."
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
        settings_layout.addRow("Max Daily Loss %:", self.max_daily_loss_spin)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # ==================== DISPLAY OPTIONS ====================
        display_group = QGroupBox("Chart Display")
        display_layout = QVBoxLayout()

        self.show_entry_markers_cb = QCheckBox("Show Entry Markers")
        self.show_entry_markers_cb.setChecked(True)
        self.show_entry_markers_cb.stateChanged.connect(self._on_display_option_changed)
        display_layout.addWidget(self.show_entry_markers_cb)

        self.show_stop_lines_cb = QCheckBox("Show Stop Lines")
        self.show_stop_lines_cb.setChecked(True)
        self.show_stop_lines_cb.stateChanged.connect(self._on_display_option_changed)
        display_layout.addWidget(self.show_stop_lines_cb)

        self.show_debug_hud_cb = QCheckBox("Show Debug HUD")
        self.show_debug_hud_cb.setChecked(False)
        self.show_debug_hud_cb.stateChanged.connect(self._on_debug_hud_changed)
        display_layout.addWidget(self.show_debug_hud_cb)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # ==================== HELP BUTTON ====================
        help_btn = QPushButton("📖 Trading-Bot Hilfe öffnen")
        help_btn.setStyleSheet(
            "padding: 8px; font-size: 12px;"
        )
        help_btn.setToolTip("Öffnet die ausführliche Dokumentation zum Trading-Bot")
        help_btn.clicked.connect(self._on_open_help_clicked)
        layout.addWidget(help_btn)

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

        self.position_side_label = QLabel("FLAT")
        self.position_side_label.setStyleSheet("font-weight: bold;")
        position_form.addRow("Side:", self.position_side_label)

        self.position_entry_label = QLabel("-")
        position_form.addRow("Entry:", self.position_entry_label)

        self.position_size_label = QLabel("-")
        position_form.addRow("Size:", self.position_size_label)

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
        position_layout.addWidget(position_group)
        splitter.addWidget(position_widget)

        # ==================== SIGNAL HISTORY ====================
        signals_widget = QWidget()
        signals_layout = QVBoxLayout(signals_widget)
        signals_layout.setContentsMargins(0, 0, 0, 0)

        signals_group = QGroupBox("Recent Signals")
        signals_inner = QVBoxLayout()

        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(6)
        self.signals_table.setHorizontalHeaderLabels([
            "Time", "Type", "Side", "Score", "Price", "Status"
        ])
        self.signals_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.signals_table.setAlternatingRowColors(True)
        signals_inner.addWidget(self.signals_table)

        signals_group.setLayout(signals_inner)
        signals_layout.addWidget(signals_group)
        splitter.addWidget(signals_widget)

        # ==================== STOP HISTORY ====================
        stop_widget = QWidget()
        stop_layout = QVBoxLayout(stop_widget)
        stop_layout.setContentsMargins(0, 0, 0, 0)

        stop_group = QGroupBox("Stop History")
        stop_inner = QVBoxLayout()

        self.stop_history_table = QTableWidget()
        self.stop_history_table.setColumnCount(4)
        self.stop_history_table.setHorizontalHeaderLabels([
            "Time", "Old Stop", "New Stop", "Reason"
        ])
        self.stop_history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.stop_history_table.setAlternatingRowColors(True)
        stop_inner.addWidget(self.stop_history_table)

        stop_group.setLayout(stop_inner)
        stop_layout.addWidget(stop_group)
        splitter.addWidget(stop_widget)

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
        config.risk.initial_stop_loss_pct = self.initial_sl_spin.value()
        config.risk.risk_per_trade_pct = self.risk_per_trade_spin.value()
        config.risk.max_trades_per_day = self.max_trades_spin.value()
        config.risk.max_daily_loss_pct = self.max_daily_loss_spin.value()

        # Create and start controller with callbacks
        from src.core.tradingbot.bot_controller import BotController

        self._bot_controller = BotController(
            config,
            on_signal=self._on_bot_signal,
            on_decision=self._on_bot_decision,
            on_order=self._on_bot_order,
            on_log=self._on_bot_log,
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

        logger.info(
            f"Bot signal received: {signal_type} {side} @ {entry_price:.4f} (Score: {score:.2f})"
        )

        # Add to signal history
        self._signal_history.append({
            "time": datetime.utcnow().strftime("%H:%M:%S"),
            "type": signal_type,
            "side": side,
            "score": score,
            "price": entry_price,
            "status": status
        })

        self._update_signals_table()

        # Only add marker to chart for CONFIRMED signals (after buy), not for candidates
        if signal_type == "confirmed":
            if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'display_signal'):
                try:
                    self.chart_widget.display_signal(signal)
                    logger.info(f"Confirmed signal marker added to chart: {side} @ {entry_price:.4f}")
                except Exception as e:
                    logger.error(f"Failed to display signal on chart: {e}", exc_info=True)
        else:
            logger.debug(f"Candidate signal - no chart marker (waiting for confirmation): {side} @ {entry_price:.4f}")

    def _on_bot_decision(self, decision: Any) -> None:
        """Handle bot decision event."""
        from src.core.tradingbot.models import BotAction

        action = decision.action if hasattr(decision, 'action') else None
        self._add_ki_log_entry("DEBUG", f"_on_bot_decision called: action={action.value if action else 'unknown'}")

        # Handle stop line updates on chart
        if hasattr(self, 'chart_widget') and action:
            try:
                if action == BotAction.ENTER:
                    # Draw initial stop line
                    stop_price = getattr(decision, 'stop_price_after', None)
                    self._add_ki_log_entry("DEBUG", f"ENTER: stop_price_after={stop_price}, has chart={hasattr(self, 'chart_widget')}")
                    if stop_price:
                        self._add_ki_log_entry("DEBUG", f"Calling add_stop_line({stop_price})")
                        self.chart_widget.add_stop_line(
                            "position_stop",
                            stop_price,
                            line_type="initial",
                            label=f"Initial SL @ {stop_price:.2f}"
                        )
                        self._add_ki_log_entry("STOP", f"Stop-Line gezeichnet @ {stop_price:.2f}")
                    else:
                        self._add_ki_log_entry("ERROR", "stop_price_after ist None - keine Stop-Line!")

                elif action == BotAction.ADJUST_STOP:
                    # Update trailing stop line
                    new_stop = getattr(decision, 'stop_price_after', None)
                    old_stop = getattr(decision, 'stop_price_before', None)
                    if new_stop:
                        self.chart_widget.add_stop_line(
                            "position_stop",
                            new_stop,
                            line_type="trailing",
                            label=f"Trailing SL @ {new_stop:.2f}"
                        )
                        logger.info(f"Updated stop line: {old_stop} -> {new_stop}")

                elif action == BotAction.EXIT:
                    # Remove stop line
                    if hasattr(self.chart_widget, 'remove_stop_line'):
                        self.chart_widget.remove_stop_line("position_stop")
                        logger.info("Removed stop line on exit")

                    # Add exit marker to chart
                    from datetime import datetime
                    reason_codes = getattr(decision, 'reason_codes', []) or []
                    side = decision.side.value if hasattr(decision, 'side') and hasattr(decision.side, 'value') else 'long'

                    # Get exit price from position or decision
                    exit_price = None
                    if self._bot_controller and self._bot_controller._last_features:
                        exit_price = self._bot_controller._last_features.close

                    if exit_price:
                        if "STOP_HIT" in reason_codes:
                            # Stop-loss was triggered
                            if hasattr(self.chart_widget, 'add_stop_triggered_marker'):
                                self.chart_widget.add_stop_triggered_marker(
                                    timestamp=datetime.utcnow(),
                                    price=exit_price,
                                    side=side
                                )
                                logger.info(f"Added stop-triggered marker at {exit_price:.4f}")
                        else:
                            # Normal exit (signal, time stop, etc.)
                            if hasattr(self.chart_widget, 'add_exit_marker'):
                                reason = reason_codes[0] if reason_codes else "EXIT"
                                self.chart_widget.add_exit_marker(
                                    timestamp=datetime.utcnow(),
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

        logger.info(
            f"Bot order received: {order.side.value if hasattr(order.side, 'value') else order.side} "
            f"{order.symbol} qty={order.quantity:.4f} @ market"
        )

        # For paper trading, immediately simulate the fill
        if self._bot_controller:
            try:
                # Get signal info BEFORE simulate_fill (it clears _current_signal)
                signal = self._bot_controller._current_signal
                score = signal.score * 100 if signal else 0.0  # Convert to 0-100
                signal_entry_price = signal.entry_price if signal else None

                # Get current price from the last known signal or estimate from order
                fill_price = getattr(order, 'stop_price', None)
                if fill_price is None and hasattr(self, 'chart_widget'):
                    # Use latest close price from chart data
                    if hasattr(self.chart_widget, 'data') and self.chart_widget.data is not None:
                        fill_price = float(self.chart_widget.data['close'].iloc[-1])
                    elif signal_entry_price:
                        # Fallback: get from signal
                        fill_price = signal_entry_price
                    else:
                        logger.warning("No price available for paper fill simulation")
                        return

                if fill_price is None:
                    logger.error("Cannot simulate fill: no price available")
                    return

                # Simulate fill (this clears _current_signal!)
                self._bot_controller.simulate_fill(
                    fill_price=fill_price,
                    fill_qty=order.quantity,
                    order_id=order.id if hasattr(order, 'id') else f"paper_{datetime.utcnow().timestamp()}"
                )
                logger.info(f"Paper fill simulated: {order.quantity:.4f} @ {fill_price:.4f}")

                # Add entry marker to chart (using pre-saved score)
                if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'add_entry_confirmed'):
                    side = order.side.value if hasattr(order.side, 'value') else str(order.side)

                    self.chart_widget.add_entry_confirmed(
                        timestamp=datetime.utcnow(),
                        price=fill_price,
                        side=side,
                        score=score
                    )
                    logger.info(f"Entry marker added to chart: {side} @ {fill_price:.4f}")

            except Exception as e:
                logger.error(f"Failed to simulate paper fill: {e}", exc_info=True)

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

        # Update position display
        position = self._bot_controller.position
        if position:  # PositionState doesn't have is_open, check if position exists
            self.position_side_label.setText(position.side.value.upper())
            self.position_side_label.setStyleSheet(
                f"font-weight: bold; color: {'#26a69a' if position.side.value == 'long' else '#ef5350'};"
            )
            self.position_entry_label.setText(f"{position.entry_price:.4f}")
            self.position_size_label.setText(f"{position.quantity:.4f}")

            if position.trailing:  # Correct attribute: trailing (not trailing_state)
                self.position_stop_label.setText(
                    f"{position.trailing.current_stop_price:.4f}"  # Correct: current_stop_price
                )

            # Display current price
            self.position_current_label.setText(f"{position.current_price:.4f}")

            # Display P&L with color
            pnl = position.unrealized_pnl
            pnl_pct = position.unrealized_pnl_pct
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

    def _update_signals_table(self) -> None:
        """Update signals table with recent entries."""
        self.signals_table.setRowCount(len(self._signal_history))
        for row, signal in enumerate(reversed(self._signal_history[-20:])):
            self.signals_table.setItem(row, 0, QTableWidgetItem(signal["time"]))
            self.signals_table.setItem(row, 1, QTableWidgetItem(signal["type"]))
            self.signals_table.setItem(row, 2, QTableWidgetItem(signal["side"]))
            self.signals_table.setItem(row, 3, QTableWidgetItem(f"{signal['score']:.0f}"))
            self.signals_table.setItem(row, 4, QTableWidgetItem(f"{signal['price']:.4f}"))
            self.signals_table.setItem(row, 5, QTableWidgetItem(signal["status"]))

    def _add_ki_log_entry(self, entry_type: str, message: str) -> None:
        """Add entry to KI log."""
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{entry_type}] {message}"
        self.ki_log_text.appendPlainText(entry)
        self._ki_log_entries.append({
            "time": timestamp,
            "type": entry_type,
            "message": message
        })

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
        self.ki_last_call_label.setText(datetime.utcnow().strftime("%H:%M:%S"))
