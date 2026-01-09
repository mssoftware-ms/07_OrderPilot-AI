"""Backtest Tab UI - Setup & Execution Tabs Module.

Creates Setup and Execution configuration tabs:
- Setup Tab: Data source, symbol, timeframe, strategy, risk settings
- Execution Tab: Fees, slippage, leverage, advanced options

Module 2/4 of backtest_tab_ui.py split.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QDateEdit,
    QWidget,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BacktestTabUISetup:
    """Setup and Execution tabs builder for backtest tab.

    Creates configuration tabs for data source, strategy, and execution settings.
    """

    def __init__(self, parent: QWidget):
        """
        Args:
            parent: BacktestTab Widget
        """
        self.parent = parent

    def create_setup_tab(self) -> QWidget:
        """Erstellt Setup Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Datenquelle ---
        data_group = QGroupBox("📁 Datenquelle")
        data_layout = QFormLayout(data_group)

        self.parent.symbol_combo = QComboBox()
        self.parent.symbol_combo.setEditable(True)
        self.parent.symbol_combo.addItems([
            "bitunix:BTCUSDT",
            "bitunix:ETHUSDT",
            "bitunix:SOLUSDT",
            "alpaca:BTC/USD",
            "alpaca:ETH/USD",
        ])
        data_layout.addRow("Symbol:", self.parent.symbol_combo)

        # Timeframe
        self.parent.timeframe_combo = QComboBox()
        self.parent.timeframe_combo.addItems([
            "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1D"
        ])
        self.parent.timeframe_combo.setCurrentText("5m")  # Default für Daytrading
        data_layout.addRow("Timeframe:", self.parent.timeframe_combo)

        # Zeitraum
        date_layout = QHBoxLayout()
        self.parent.start_date = QDateEdit()
        self.parent.start_date.setDate(datetime.now().date() - timedelta(days=90))
        self.parent.start_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("Von:"))
        date_layout.addWidget(self.parent.start_date)

        self.parent.end_date = QDateEdit()
        self.parent.end_date.setDate(datetime.now().date())
        self.parent.end_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("Bis:"))
        date_layout.addWidget(self.parent.end_date)

        data_layout.addRow("Zeitraum:", date_layout)

        # Quick-Select Buttons
        quick_layout = QHBoxLayout()
        for days, label in [(7, "1W"), (30, "1M"), (90, "3M"), (180, "6M"), (365, "1Y")]:
            btn = QPushButton(label)
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, d=days: self.parent._set_date_range(d))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        data_layout.addRow("", quick_layout)

        layout.addWidget(data_group)

        # --- Strategy ---
        strategy_group = QGroupBox("🎯 Strategy")
        strategy_layout = QFormLayout(strategy_group)

        self.parent.strategy_combo = QComboBox()
        self.parent.strategy_combo.addItems([
            "Default (Confluence-Based)",
            "Trend Following",
            "Mean Reversion",
            "Breakout",
            "Custom...",
        ])
        strategy_layout.addRow("Strategy:", self.parent.strategy_combo)

        self.parent.initial_capital = QDoubleSpinBox()
        self.parent.initial_capital.setRange(100, 10_000_000)
        self.parent.initial_capital.setValue(10_000)
        self.parent.initial_capital.setPrefix("$ ")
        self.parent.initial_capital.setSingleStep(1000)
        strategy_layout.addRow("Startkapital:", self.parent.initial_capital)

        layout.addWidget(strategy_group)

        # --- Risk Settings ---
        risk_group = QGroupBox("⚠️ Risk Management")
        risk_layout = QFormLayout(risk_group)

        self.parent.risk_per_trade = QDoubleSpinBox()
        self.parent.risk_per_trade.setRange(0.1, 10)
        self.parent.risk_per_trade.setValue(1.0)
        self.parent.risk_per_trade.setSuffix(" %")
        self.parent.risk_per_trade.setSingleStep(0.5)
        risk_layout.addRow("Risiko/Trade:", self.parent.risk_per_trade)

        self.parent.max_daily_loss = QDoubleSpinBox()
        self.parent.max_daily_loss.setRange(0.5, 20)
        self.parent.max_daily_loss.setValue(3.0)
        self.parent.max_daily_loss.setSuffix(" %")
        risk_layout.addRow("Max Daily Loss:", self.parent.max_daily_loss)

        self.parent.max_trades_day = QSpinBox()
        self.parent.max_trades_day.setRange(1, 100)
        self.parent.max_trades_day.setValue(10)
        risk_layout.addRow("Max Trades/Tag:", self.parent.max_trades_day)

        layout.addWidget(risk_group)

        layout.addStretch()
        return widget

    def create_execution_tab(self) -> QWidget:
        """Erstellt Execution Settings Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Fees ---
        fee_group = QGroupBox("💰 Gebühren")
        fee_layout = QFormLayout(fee_group)

        self.parent.fee_maker = QDoubleSpinBox()
        self.parent.fee_maker.setRange(0, 1)
        self.parent.fee_maker.setValue(0.02)
        self.parent.fee_maker.setDecimals(3)
        self.parent.fee_maker.setSuffix(" %")
        fee_layout.addRow("Maker Fee:", self.parent.fee_maker)

        self.parent.fee_taker = QDoubleSpinBox()
        self.parent.fee_taker.setRange(0, 1)
        self.parent.fee_taker.setValue(0.06)
        self.parent.fee_taker.setDecimals(3)
        self.parent.fee_taker.setSuffix(" %")
        fee_layout.addRow("Taker Fee:", self.parent.fee_taker)

        layout.addWidget(fee_group)

        # --- Slippage ---
        slip_group = QGroupBox("📉 Slippage")
        slip_layout = QFormLayout(slip_group)

        self.parent.slippage_method = QComboBox()
        self.parent.slippage_method.addItems(["Fixed BPS", "ATR-Based", "Volume-Adjusted"])
        slip_layout.addRow("Methode:", self.parent.slippage_method)

        self.parent.slippage_bps = QDoubleSpinBox()
        self.parent.slippage_bps.setRange(0, 100)
        self.parent.slippage_bps.setValue(5)
        self.parent.slippage_bps.setSuffix(" bps")
        slip_layout.addRow("Slippage:", self.parent.slippage_bps)

        layout.addWidget(slip_group)

        # --- Leverage ---
        lev_group = QGroupBox("📈 Leverage")
        lev_layout = QFormLayout(lev_group)

        self.parent.max_leverage = QSpinBox()
        self.parent.max_leverage.setRange(1, 125)
        self.parent.max_leverage.setValue(20)
        self.parent.max_leverage.setSuffix("x")
        lev_layout.addRow("Max Leverage:", self.parent.max_leverage)

        self.parent.liq_buffer = QDoubleSpinBox()
        self.parent.liq_buffer.setRange(0, 50)
        self.parent.liq_buffer.setValue(5)
        self.parent.liq_buffer.setSuffix(" %")
        lev_layout.addRow("Liquidation Buffer:", self.parent.liq_buffer)

        layout.addWidget(lev_group)

        # --- Advanced ---
        adv_group = QGroupBox("🔧 Erweitert")
        adv_layout = QFormLayout(adv_group)

        self.parent.assume_taker = QCheckBox()
        self.parent.assume_taker.setChecked(True)
        adv_layout.addRow("Market = Taker:", self.parent.assume_taker)

        self.parent.include_funding = QCheckBox()
        self.parent.include_funding.setChecked(False)
        adv_layout.addRow("Funding Rates:", self.parent.include_funding)

        layout.addWidget(adv_group)

        layout.addStretch()
        return widget
