"""Backtest Tab Settings - Settings Persistence.

Refactored from backtest_tab_main.py.

Contains:
- load_settings: Load settings from JSON and QSettings
- save_settings: Save settings to JSON and QSettings
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .backtest_tab_main import BacktestTab

logger = logging.getLogger(__name__)

BACKTEST_SETTINGS_FILE = Path("config/backtest_settings.json")


class BacktestTabSettings:
    """Helper for settings persistence."""

    def __init__(self, parent: "BacktestTab"):
        self.parent = parent

    def load_settings(self) -> None:
        """Lädt alle Einstellungen aus JSON und QSettings."""
        try:
            # JSON laden
            if BACKTEST_SETTINGS_FILE.exists():
                with open(BACKTEST_SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)

                # Apply settings to UI widgets
                if 'symbol' in settings and self.parent.symbol_combo.findText(settings['symbol']) >= 0:
                    self.parent.symbol_combo.setCurrentText(settings['symbol'])

                if 'initial_capital' in settings:
                    self.parent.initial_capital.setValue(settings['initial_capital'])
                if 'risk_per_trade' in settings:
                    self.parent.risk_per_trade.setValue(settings['risk_per_trade'])
                if 'max_daily_loss' in settings:
                    self.parent.max_daily_loss.setValue(settings['max_daily_loss'])
                if 'max_trades_day' in settings:
                    self.parent.max_trades_day.setValue(settings['max_trades_day'])

                # Execution tab
                if 'fee_maker' in settings:
                    self.parent.fee_maker.setValue(settings['fee_maker'])
                if 'fee_taker' in settings:
                    self.parent.fee_taker.setValue(settings['fee_taker'])
                if 'slippage_bps' in settings:
                    self.parent.slippage_bps.setValue(settings['slippage_bps'])
                if 'slippage_method' in settings:
                    self.parent.slippage_method.setCurrentIndex(settings['slippage_method'])
                if 'max_leverage' in settings:
                    self.parent.max_leverage.setValue(settings['max_leverage'])
                if 'liq_buffer' in settings:
                    self.parent.liq_buffer.setValue(settings['liq_buffer'])
                if 'assume_taker' in settings:
                    self.parent.assume_taker.setChecked(settings['assume_taker'])

                # Batch/WF tab
                if 'batch_method' in settings:
                    self.parent.batch_method.setCurrentIndex(settings['batch_method'])
                if 'batch_iterations' in settings:
                    self.parent.batch_iterations.setValue(settings['batch_iterations'])
                if 'batch_target' in settings:
                    self.parent.batch_target.setCurrentIndex(settings['batch_target'])
                if 'wf_train_days' in settings:
                    self.parent.wf_train_days.setValue(settings['wf_train_days'])
                if 'wf_test_days' in settings:
                    self.parent.wf_test_days.setValue(settings['wf_test_days'])
                if 'wf_step_days' in settings:
                    self.parent.wf_step_days.setValue(settings['wf_step_days'])
                if 'wf_reoptimize' in settings:
                    self.parent.wf_reoptimize.setChecked(settings['wf_reoptimize'])

                logger.info("Backtest settings loaded from JSON")

            # Fallback: QSettings
            else:
                from PyQt6.QtCore import QSettings
                qsettings = QSettings("OrderPilot-AI", "BacktestTab")

                if qsettings.contains("symbol"):
                    symbol = qsettings.value("symbol", "BTC/USD")
                    if self.parent.symbol_combo.findText(symbol) >= 0:
                        self.parent.symbol_combo.setCurrentText(symbol)

                if qsettings.contains("initial_capital"):
                    self.parent.initial_capital.setValue(qsettings.value("initial_capital", 10000, type=float))
                if qsettings.contains("risk_per_trade"):
                    self.parent.risk_per_trade.setValue(qsettings.value("risk_per_trade", 1.0, type=float))

                logger.info("Backtest settings loaded from QSettings")

        except Exception as e:
            logger.warning(f"Could not load backtest settings: {e}")

    def save_settings(self) -> None:
        """Speichert alle Einstellungen in JSON und QSettings."""
        try:
            BACKTEST_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

            settings = {
                # Setup Tab
                "symbol": self.parent.symbol_combo.currentText(),
                "initial_capital": self.parent.initial_capital.value(),
                "risk_per_trade": self.parent.risk_per_trade.value(),
                "max_daily_loss": self.parent.max_daily_loss.value(),
                "max_trades_day": self.parent.max_trades_day.value(),

                # Execution Tab
                "fee_maker": self.parent.fee_maker.value(),
                "fee_taker": self.parent.fee_taker.value(),
                "slippage_bps": self.parent.slippage_bps.value(),
                "slippage_method": self.parent.slippage_method.currentIndex(),
                "max_leverage": self.parent.max_leverage.value(),
                "liq_buffer": self.parent.liq_buffer.value(),
                "assume_taker": self.parent.assume_taker.isChecked(),

                # Batch/WF Tab
                "batch_method": self.parent.batch_method.currentIndex(),
                "batch_iterations": self.parent.batch_iterations.value(),
                "batch_target": self.parent.batch_target.currentIndex(),
                "wf_train_days": self.parent.wf_train_days.value(),
                "wf_test_days": self.parent.wf_test_days.value(),
                "wf_step_days": self.parent.wf_step_days.value(),
                "wf_reoptimize": self.parent.wf_reoptimize.isChecked(),
            }

            # Save as JSON
            with open(BACKTEST_SETTINGS_FILE, "w") as f:
                json.dump(settings, f, indent=2)

            # Backup in QSettings
            from PyQt6.QtCore import QSettings
            qsettings = QSettings("OrderPilot-AI", "BacktestTab")
            for key, value in settings.items():
                qsettings.setValue(key, value)
            qsettings.sync()

            logger.info("Backtest settings saved to JSON and QSettings")

        except Exception as e:
            logger.warning(f"Could not save backtest settings: {e}")
