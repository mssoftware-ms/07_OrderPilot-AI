"""Entry Analyzer - Regime Analysis Mixin.

Extracted from entry_analyzer_backtest.py to keep files under 550 LOC.
Handles market regime detection and analysis:
- Current regime analysis with RegimeEngineJSON
- Regime boundary drawing on chart
- Regime history handling from optimization
- Real-time regime classification

Date: 2026-01-21
LOC: ~300
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BacktestRegimeMixin:
    """Regime analysis functionality.

    Provides regime detection and visualization with:
    - Current regime analysis using RegimeEngineJSON
    - Indicator calculation via IndicatorEngine (JSON config)
    - Regime classification based on JSON-defined regimes
    - Regime interpretation and recommendations
    - Regime boundaries drawing on chart as vertical lines
    - Regime history handling from optimization results

    Attributes (defined in parent class):
        _candles: list[dict] - Chart candle data
        _regime_label: QLabel - Regime display label in header
    """

    # Type hints for parent class attributes
    _candles: list[dict]
    _regime_label: Any
    _regime_config: object | None

    def _on_analyze_current_regime_clicked(self) -> None:
        """Analyze current market regime.

        Original: entry_analyzer_backtest.py:326-490

        Performs real-time regime analysis:
        1. Gets chart data (last 200 candles)
        2. Loads JSON-based regime config (Entry Analyzer)
        3. Calculates indicators via RegimeEngineJSON
        4. Detects active regimes via RegimeDetector
        5. Displays regime with volatility level + interpretation
        6. Updates header label with regime color
        """
        if not self._candles or len(self._candles) < 50:
            QMessageBox.warning(
                self,
                "Insufficient Data",
                "Need at least 50 candles for regime analysis.\n" "Load more chart data first.",
            )
            return

        try:
            logger.info("Starting current regime analysis...")

            # Get last 200 candles for analysis (need history for indicators)
            analysis_candles = self._candles[-200:] if len(self._candles) > 200 else self._candles

            # Convert to DataFrame
            import pandas as pd

            df = pd.DataFrame(analysis_candles)

            # Ensure required columns
            if "timestamp" not in df.columns and "time" in df.columns:
                df["timestamp"] = df["time"]

            required_cols = ["open", "high", "low", "close", "volume"]
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            # Load JSON-based regime config
            if self._regime_config is None:
                self._load_default_regime_config()
            config = self._regime_config
            if config is None:
                raise ValueError("Regime config is not loaded.")

            from src.core.tradingbot.config.detector import RegimeDetector
            from src.core.tradingbot.models import RegimeType
            from src.core.tradingbot.regime_engine_json import RegimeEngineJSON

            engine = RegimeEngineJSON()
            indicator_values = engine._calculate_indicators(df, config)
            detector = RegimeDetector(config.regimes)
            active_regimes = detector.detect_active_regimes(indicator_values, scope="entry")
            regime_state = engine._convert_to_regime_state(
                active_regimes=active_regimes,
                indicator_values=indicator_values,
                timestamp=datetime.utcnow(),
            )

            active_label = active_regimes[0].name if active_regimes else "Unknown"
            active_id = active_regimes[0].id if active_regimes else "unknown"

            logger.info(
                f"Current regime: {active_label} ({active_id}) " f"-> {regime_state.regime_label}"
            )

            # Build interpretation text (v2.0 unified naming: BULL/BEAR/SIDEWAYS)
            regime_colors = {
                RegimeType.BULL: "#22c55e",
                RegimeType.BEAR: "#ef4444",
                RegimeType.SIDEWAYS: "#f59e0b",
                RegimeType.UNKNOWN: "#6b7280",
                # Legacy aliases
                "BULL": "#22c55e",
                "BEAR": "#ef4444",
                "SIDEWAYS": "#f59e0b",
            }

            regime_interpretations = {
                RegimeType.BULL: "Bullish trend - focus on LONG pullbacks",
                RegimeType.BEAR: "Bearish trend - focus on SHORT rallies",
                RegimeType.SIDEWAYS: "Range-bound market - trade support/resistance",
                RegimeType.UNKNOWN: "No clear regime - reduce exposure",
                # Legacy aliases
                "BULL": "Bullish trend - focus on LONG pullbacks",
                "BEAR": "Bearish trend - focus on SHORT rallies",
                "SIDEWAYS": "Range-bound market - trade support/resistance",
            }

            color = regime_colors.get(regime_state.regime, "#888")
            interpretation = regime_interpretations.get(regime_state.regime, "Unknown regime")

            # Update header label
            self._regime_label.setText(f"Regime: {active_label}")
            self._regime_label.setStyleSheet(
                f"font-weight: bold; font-size: 14pt; padding: 5px; color: {color};"
            )

            def format_value(value: float | None, fmt: str) -> str:
                if value is None:
                    return "n/a"
                if isinstance(value, float) and math.isnan(value):
                    return "n/a"
                return format(value, fmt)

            rsi_val = indicator_values.get("rsi14", {}).get("value")
            macd_val = indicator_values.get("macd_12_26_9", {}).get("macd")
            adx_val = indicator_values.get("adx14", {}).get("value")
            atr_val = indicator_values.get("atr14", {}).get("value")
            bb_width = indicator_values.get("bb20", {}).get("width")

            # Show detailed analysis
            details = (
                f"Detected Regime: {active_label} ({active_id})\n"
                f"Legacy Regime: {regime_state.regime_label}\n"
                f"Confidence: {regime_state.regime_confidence:.2f}\n\n"
                f"{interpretation}\n\n"
                f"Indicators (from JSON config):\n"
                f"  RSI(14): {format_value(rsi_val, '.1f')}\n"
                f"  MACD: {format_value(macd_val, '.4f')}\n"
                f"  ADX(14): {format_value(adx_val, '.1f')}\n"
                f"  ATR(14): {format_value(atr_val, '.4f')}\n"
                f"  BB Width: {format_value(bb_width, '.4f')}\n\n"
                f"Recommendation:\n"
                f"  - Use strategies optimized for {active_label}\n"
                f"  - Adjust position sizing based on volatility\n"
                f"  - Monitor for regime changes"
            )

            QMessageBox.information(self, "Current Regime Analysis", details)

            logger.info("Regime analysis complete")

        except Exception as e:
            logger.error(f"Regime analysis failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Analysis Error", f"Failed to analyze regime:\n\n{str(e)}")

    def _draw_regime_boundaries(self, results: dict) -> None:
        """Draw vertical lines for regime boundaries on chart.

        Original: entry_analyzer_backtest.py:691-765

        Args:
            results: Backtest results dict with regime_history
        """
        regime_history = results.get("regime_history", [])
        if not regime_history:
            QMessageBox.information(
                self, "No Regime History", "No regime changes detected in backtest results."
            )
            return

        logger.info(f"Drawing {len(regime_history)} regime boundaries")

        # Clear existing regime lines (if any)
        # TODO: Implement chart.clear_regime_lines() when chart integration is ready

        # Add regime boundary lines to chart
        regime_colors = {
            "trend_up": "#22c55e",
            "trend_down": "#ef4444",
            "range": "#f59e0b",
            "high_vol": "#a855f7",
            "squeeze": "#3b82f6",
            "no_trade": "#6b7280",
        }

        for change in regime_history:
            timestamp = change.get("timestamp")
            regime = change.get("regime", "unknown")
            color = regime_colors.get(regime, "#888")

            # TODO: Implement chart.add_regime_line(timestamp, regime, color)
            logger.debug(f"Regime boundary: {timestamp} -> {regime}")

        QMessageBox.information(
            self,
            "Regime Boundaries",
            f"Drew {len(regime_history)} regime boundaries on chart.\n\n"
            f"Note: Chart integration pending - boundaries logged for now.",
        )

    def _on_regime_history_ready(self, regime_history: list) -> None:
        """Handle regime history from optimization.

        Original: entry_analyzer_backtest.py:766-783

        Args:
            regime_history: List of regime change dicts
        """
        if not regime_history:
            return

        logger.info(f"Received regime history: {len(regime_history)} changes")

        # Store regime history
        self._regime_history = regime_history

        # Enable draw boundaries button (if present)
        draw_btn = getattr(self, "_bt_draw_boundaries_btn", None)
        if draw_btn is not None:
            draw_btn.setEnabled(True)
        create_btn = getattr(self, "_bt_create_regime_set_btn", None)
        if create_btn is not None:
            create_btn.setEnabled(True)

        logger.info("Regime history ready for visualization")
