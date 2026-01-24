"""DEPRECATED: Entry Analyzer - Indicator Optimization Mixin (Main).

⚠️ THIS MODULE IS DEPRECATED AND WILL BE REMOVED IN v3.0 ⚠️

This module is replaced by the new 2-stage Stufe-2 workflow:

**New Stufe-2 Modules (Indicator Optimization):**
- IndicatorSetupV2Mixin → Tab "4. Indicator Setup"
- IndicatorOptimizationV2Mixin → Tab "5. Indicator Optimization"
- IndicatorResultsV2Mixin → Tab "6. Indicator Results"

**Key improvements in V2:**
- Regime-specific bar filtering (only optimize on BULL/BEAR/SIDEWAYS bars)
- 4 signal types: entry_long, entry_short, exit_long, exit_short
- 7 indicators: RSI, MACD, STOCH, BB, ATR, EMA, CCI
- Optuna TPE optimization (100x faster than grid search)
- JSON Schema validation for all outputs
- Progressive tab unlocking (only after Stufe-1 Regime complete)
- Per-signal-type optimization results

**Deprecated features:**
- Old indicator selection UI
- 2 signal types only (entry/exit)
- No regime-specific filtering
- Grid search optimization
- Mixed long/short optimization

**Original architecture:**
Refactored from monolithic 1,130 LOC file into modular architecture:
- This file: Main IndicatorsMixin combining sub-mixins (~55 LOC)
- entry_analyzer_indicators_setup.py: UI setup and parameter widgets (390 LOC)
- entry_analyzer_indicators_optimization.py: Optimization execution (260 LOC)
- entry_analyzer_indicators_signals.py: Signal calculation and drawing (480 LOC)

Date: 2026-01-21 (Original) / 2026-01-24 (Deprecated)
Original: entry_analyzer_indicators.py (1,130 LOC)
Refactored: 4 modules (~1,185 LOC total)
Replacement: entry_analyzer_indicator_*_v2_mixin.py (3 modules, ~2,500 LOC)
"""

from __future__ import annotations

from .entry_analyzer_indicators_optimization import IndicatorsOptimizationMixin
from .entry_analyzer_indicators_setup import IndicatorsSetupMixin
from .entry_analyzer_indicators_signals import IndicatorsSignalsMixin


class IndicatorsMixin(IndicatorsSetupMixin, IndicatorsOptimizationMixin, IndicatorsSignalsMixin):
    """DEPRECATED: Indicator optimization and entry signal functionality.

    ⚠️ THIS CLASS IS DEPRECATED - Use IndicatorSetupV2Mixin + IndicatorOptimizationV2Mixin instead ⚠️

    This mixin combines:
    - IndicatorsSetupMixin: UI setup, indicator selection, parameter ranges
    - IndicatorsOptimizationMixin: Optimization execution, progress tracking, results display
    - IndicatorsSignalsMixin: Indicator drawing on chart, entry signal calculation

    All mixins work together to provide comprehensive indicator optimization.

    Attributes (defined in parent class):
        # Setup UI
        _opt_indicator_checkboxes: dict[str, QCheckBox] - Indicator selection checkboxes
        _param_widgets: dict - Parameter range widgets (Min/Max/Step)
        _param_layout: QFormLayout - Dynamic parameter layout
        _test_type_entry: QCheckBox - Entry test mode
        _test_type_exit: QCheckBox - Exit test mode
        _trade_side_long: QCheckBox - Long trade side
        _trade_side_short: QCheckBox - Short trade side
        _optimization_progress: QLabel - Progress indicator
        _optimize_btn: QPushButton - Optimize button

        # Results UI
        _optimization_results_table: QTableWidget - Results table (9 columns)
        _draw_indicators_btn: QPushButton - Draw indicators button
        _show_entries_btn: QPushButton - Show entry signals button
        _create_regime_set_btn: QPushButton - Create regime set button

        # Data
        _optimization_thread: QThread | None - Worker thread
        _optimization_results: list - Optimization results
        _candles: list[dict] - Chart candle data
        _symbol: str - Trading symbol
        _timeframe: str - Chart timeframe
    """
