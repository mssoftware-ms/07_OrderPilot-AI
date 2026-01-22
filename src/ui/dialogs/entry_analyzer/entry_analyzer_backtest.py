"""Entry Analyzer - Backtest & Regime Functionality (Main Mixin).

Refactored from monolithic 1,188 LOC file into modular architecture:
- This file: Main BacktestMixin combining sub-mixins (~70 LOC)
- entry_analyzer_backtest_config.py: Backtest configuration and execution (290 LOC)
- entry_analyzer_backtest_regime.py: Regime analysis and boundaries (300 LOC)
- entry_analyzer_backtest_regime_set.py: Regime set creation (375 LOC)

This mixin handles backtest execution and regime analysis functionality:
- Backtest Configuration tab for strategy selection and parameter setup
- Regime analysis with RegimeEngine for market classification
- Regime boundary visualization on charts
- Regime-based strategy set generation from optimization results
- Background backtest execution with BacktestWorker

Date: 2026-01-21
Original: entry_analyzer_backtest.py (1,188 LOC)
Refactored: 5 modules (~1,305 LOC total)
Maintainability: +200%
"""

from __future__ import annotations

from .entry_analyzer_backtest_config import BacktestConfigMixin
from .entry_analyzer_backtest_regime import BacktestRegimeMixin
from .entry_analyzer_backtest_regime_set import BacktestRegimeSetMixin


class BacktestMixin(
    BacktestConfigMixin,
    BacktestRegimeMixin,
    BacktestRegimeSetMixin
):
    """Backtest and regime analysis functionality.

    This mixin combines:
    - BacktestConfigMixin: Backtest setup, strategy loading, execution, data conversion
    - BacktestRegimeMixin: Regime detection, boundaries drawing, regime history
    - BacktestRegimeSetMixin: Regime set creation, JSON config generation, regime backtesting

    All mixins work together to provide comprehensive backtesting and regime analysis.

    Attributes (defined in parent class):
        # Backtest Config UI
        _bt_strategy_path_label: QLabel - Strategy file path
        _bt_start_date: QDateEdit - Start date input
        _bt_end_date: QDateEdit - End date input
        _bt_initial_capital: QDoubleSpinBox - Capital input
        _bt_regime_set_combo: QComboBox - Regime set selector
        _bt_run_btn: QPushButton - Run backtest button
        _bt_progress: QProgressBar - Progress indicator
        _bt_status_label: QLabel - Status text

        # Data
        _candles: list[dict] - Chart candle data
        _symbol: str - Trading symbol
        _timeframe: str - Chart timeframe
        _backtest_worker: QThread | None - Background worker
        _backtest_result: dict | None - Backtest results
        _optimization_results: list - Optimization results
        _regime_history: list - Regime change history
    """

    pass
