"""Backtest Config Module - Regime analysis tab components.

Split from entry_analyzer_backtest_config.py (1354 LOC → 3 modules)

Modules:
- backtest_config_ui.py: UI setup and widget creation (~280 LOC)
- backtest_config_persistence.py: Config I/O and table operations (~420 LOC)
- regime_detection_logic.py: Core regime detection algorithm (~530 LOC)

Date: 2026-01-31 (Task 3.2.1)
"""

from .backtest_config_ui import BacktestConfigUIMixin
from .backtest_config_persistence import BacktestConfigPersistenceMixin
from .regime_detection_logic import RegimeDetectionLogicMixin


class BacktestConfigMixin(
    BacktestConfigUIMixin,
    BacktestConfigPersistenceMixin,
    RegimeDetectionLogicMixin,
):
    """Combined backtest config mixin (backward compatible).

    This class combines all three mixins to provide the complete
    BacktestConfigMixin interface. This maintains backward compatibility
    with existing code that imports BacktestConfigMixin directly.

    Attributes (defined in parent class):
        _candles: list[dict] - Chart candle data
        _symbol: str - Trading symbol
        _timeframe: str - Chart timeframe
        _regime_config: dict | None - Loaded regime config
        _regime_config_path: Path | None - Current config path
        _regime_config_dirty: bool - Unsaved changes flag
        _detected_regimes_table: QTableWidget - Results table
        _regime_config_table: QTableWidget - Config table (52 columns)
        _regime_start_day: QLabel - Chart start day
        _regime_end_day: QLabel - Chart end day
        _regime_period_days: QLabel - Period in days
        _regime_num_bars: QLabel - Number of bars
        _regime_config_path_label: QLabel - Config path display
        _regime_config_load_btn: QPushButton - Load button
        _regime_config_save_btn: QPushButton - Save button
        _regime_config_save_as_btn: QPushButton - Save as button
    """
    pass


__all__ = [
    "BacktestConfigMixin",
    "BacktestConfigUIMixin",
    "BacktestConfigPersistenceMixin",
    "RegimeDetectionLogicMixin",
]
