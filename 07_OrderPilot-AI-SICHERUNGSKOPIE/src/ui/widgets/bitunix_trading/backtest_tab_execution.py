"""Backtest Tab Execution - Single Backtest Execution.

Refactored from backtest_tab_main.py.

Contains:
- build_backtest_config: Create BacktestConfig from UI values
- on_start_clicked: Start single backtest
- on_stop_clicked: Stop backtest
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from .backtest_tab_main import BacktestTab

logger = logging.getLogger(__name__)


class BacktestTabExecution:
    """Helper for single backtest execution."""

    def __init__(self, parent: "BacktestTab"):
        self.parent = parent

    def build_backtest_config(self):
        """Erstellt BacktestConfig aus UI-Werten.

        Returns:
            ReplayBacktestConfig Objekt
        """
        from src.core.backtesting import ReplayBacktestConfig, ExecutionConfig, SlippageMethod

        symbol = self.parent.symbol_combo.currentText()
        start = datetime.combine(self.parent.start_date.date().toPyDate(), datetime.min.time(), tzinfo=timezone.utc)
        end = datetime.combine(self.parent.end_date.date().toPyDate(), datetime.max.time(), tzinfo=timezone.utc)

        # Slippage Method Mapping
        slippage_map = {
            0: SlippageMethod.FIXED_BPS,
            1: SlippageMethod.ATR_BASED,
            2: SlippageMethod.VOLUME_ADJUSTED,
        }
        slippage_method = slippage_map.get(self.parent.slippage_method.currentIndex(), SlippageMethod.FIXED_BPS)

        # ExecutionConfig erstellen
        exec_config = ExecutionConfig(
            fee_rate_maker=self.parent.fee_maker.value(),
            fee_rate_taker=self.parent.fee_taker.value(),
            slippage_method=slippage_method,
            slippage_bps=self.parent.slippage_bps.value(),
            max_leverage=self.parent.max_leverage.value(),
            liquidation_buffer_pct=self.parent.liq_buffer.value(),
            assume_taker=self.parent.assume_taker.isChecked(),
        )

        # Timeframe aus UI holen
        selected_tf = self.parent.timeframe_combo.currentText()

        # MTF Timeframes: alle höher als der ausgewählte
        all_tfs = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1D"]
        try:
            selected_idx = all_tfs.index(selected_tf)
            mtf_timeframes = all_tfs[selected_idx + 1:] if selected_idx < len(all_tfs) - 1 else ["1D"]
        except ValueError:
            mtf_timeframes = ["5m", "15m", "1h", "4h", "1D"]

        # BacktestConfig erstellen
        config = ReplayBacktestConfig(
            symbol=symbol,
            start_date=start,
            end_date=end,
            initial_capital=self.parent.initial_capital.value(),
            base_timeframe=selected_tf,
            mtf_timeframes=mtf_timeframes,
            execution=exec_config,
            risk_per_trade_pct=self.parent.risk_per_trade.value(),
            max_daily_loss_pct=self.parent.max_daily_loss.value(),
            max_trades_per_day=self.parent.max_trades_day.value(),
        )

        return config

    @qasync.asyncSlot()
    async def on_start_clicked(self) -> None:
        """Startet den Backtest."""
        if self.parent._is_running:
            return

        self.parent._is_running = True
        self.parent._current_runner = None
        self.parent.start_btn.setEnabled(False)
        self.parent.stop_btn.setEnabled(True)
        self.parent.status_label.setText("RUNNING")
        self.parent.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
        self.parent.status_detail.setText("Backtest läuft...")
        self.parent.progress_bar.setValue(0)

        self.parent._settings.save_settings()
        self.parent._logging.log("🚀 Backtest gestartet...")

        try:
            # Build config from UI
            config = self.build_backtest_config()

            self.parent._logging.log(f"Symbol: {config.symbol}")
            self.parent._logging.log(f"Zeitraum: {config.start_date.date()} bis {config.end_date.date()}")
            self.parent._logging.log(f"Kapital: ${config.initial_capital:,.2f}")

            # Import BacktestRunner
            from src.core.backtesting import BacktestRunner

            # Get signal callback from config_manager
            signal_callback = self.parent.config_manager.get_signal_callback()

            # Runner erstellen mit Signal-Callback
            self.parent._current_runner = BacktestRunner(
                config,
                signal_callback=signal_callback,
            )
            self.parent._current_runner.set_progress_callback(
                lambda p, m: self.parent.progress_updated.emit(p, m)
            )

            self.parent._logging.log("📊 Starte Replay-Backtest...")

            # Run backtest asynchron
            result = await self.parent._current_runner.run()

            if self.parent._current_runner._should_stop:
                self.parent._logging.log("⏹ Backtest abgebrochen")
                return

            self.parent._logging.log("✅ Backtest abgeschlossen!")
            self.parent.progress_updated.emit(100, "Fertig!")

            self.parent._current_result = result
            self.parent.backtest_finished.emit(result)

        except Exception as e:
            logger.exception("Backtest failed")
            self.parent._logging.log(f"❌ Fehler: {e}")
            QMessageBox.critical(self.parent, "Backtest Fehler", str(e))
        finally:
            self.parent._is_running = False
            self.parent.start_btn.setEnabled(True)
            self.parent.stop_btn.setEnabled(False)
            self.parent.status_label.setText("IDLE")
            self.parent.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")

    def on_stop_clicked(self) -> None:
        """Stoppt den Backtest."""
        if self.parent._current_runner:
            self.parent._current_runner.stop()
        self.parent._is_running = False
        self.parent._logging.log("⏹ Backtest wird gestoppt...")
        self.parent.status_detail.setText("Abbrechen...")
        self.parent.stop_btn.setEnabled(False)
