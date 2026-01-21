"""Entry Analyzer - Regime Analysis Mixin.

Extracted from entry_analyzer_backtest.py to keep files under 550 LOC.
Handles market regime detection and analysis:
- Current regime analysis with RegimeEngine
- Regime boundary drawing on chart
- Regime history handling from optimization
- Real-time regime classification

Date: 2026-01-21
LOC: ~300
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BacktestRegimeMixin:
    """Regime analysis functionality.

    Provides regime detection and visualization with:
    - Current regime analysis using RegimeEngine
    - Indicator calculation (RSI, MACD, ADX, ATR, BB)
    - FeatureVector building from candle data
    - Regime classification (TREND_UP/DOWN, RANGE, HIGH_VOL, SQUEEZE)
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

    def _on_analyze_current_regime_clicked(self) -> None:
        """Analyze current market regime.

        Original: entry_analyzer_backtest.py:326-490

        Performs real-time regime analysis:
        1. Gets chart data (last 200 candles)
        2. Calculates indicators: RSI(14), MACD(12,26,9), ADX(14), ATR(14), BB(20,2)
        3. Builds FeatureVector from latest candle
        4. Uses RegimeEngine.classify() for regime detection
        5. Displays regime (TREND_UP, TREND_DOWN, RANGE) with volatility level
        6. Shows interpretation and trading recommendations
        7. Updates header label with regime color
        """
        if not self._candles or len(self._candles) < 50:
            QMessageBox.warning(
                self,
                "Insufficient Data",
                "Need at least 50 candles for regime analysis.\n"
                "Load more chart data first."
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
            if 'timestamp' not in df.columns and 'time' in df.columns:
                df['timestamp'] = df['time']

            required_cols = ['open', 'high', 'low', 'close', 'volume']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            # Calculate indicators
            logger.debug("Calculating indicators...")

            # RSI (14)
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # MACD (12, 26, 9)
            ema_fast = df['close'].ewm(span=12).mean()
            ema_slow = df['close'].ewm(span=26).mean()
            df['macd'] = ema_fast - ema_slow
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']

            # ADX (14)
            high_diff = df['high'].diff()
            low_diff = -df['low'].diff()
            plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
            minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
            tr = pd.concat([
                df['high'] - df['low'],
                abs(df['high'] - df['close'].shift()),
                abs(df['low'] - df['close'].shift())
            ], axis=1).max(axis=1)
            atr = tr.rolling(window=14).mean()
            plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            df['adx'] = dx.rolling(window=14).mean()

            # ATR (14)
            df['atr'] = atr

            # Bollinger Bands (20, 2)
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (2 * bb_std)
            df['bb_lower'] = df['bb_middle'] - (2 * bb_std)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

            # Get latest candle with indicators
            latest = df.iloc[-1]

            # Build FeatureVector
            from src.analysis.regime_engine import FeatureVector

            features = FeatureVector(
                rsi=float(latest['rsi']) if pd.notna(latest['rsi']) else 50.0,
                macd=float(latest['macd']) if pd.notna(latest['macd']) else 0.0,
                macd_signal=float(latest['macd_signal']) if pd.notna(latest['macd_signal']) else 0.0,
                adx=float(latest['adx']) if pd.notna(latest['adx']) else 20.0,
                atr=float(latest['atr']) if pd.notna(latest['atr']) else 0.0,
                bb_width=float(latest['bb_width']) if pd.notna(latest['bb_width']) else 0.05,
                volatility=float(latest['atr'] / latest['close']) if pd.notna(latest['atr']) and latest['close'] > 0 else 0.01,
                trend_strength=float(latest['adx']) if pd.notna(latest['adx']) else 20.0,
            )

            # Classify regime
            from src.analysis.regime_engine import RegimeEngine

            regime_engine = RegimeEngine()
            regime = regime_engine.classify(features)

            logger.info(f"Current regime: {regime.value}")

            # Build interpretation text
            regime_colors = {
                "trend_up": "#22c55e",
                "trend_down": "#ef4444",
                "range": "#f59e0b",
                "high_vol": "#a855f7",
                "squeeze": "#3b82f6",
                "no_trade": "#6b7280",
            }

            regime_interpretations = {
                "trend_up": "📈 Strong uptrend - Look for LONG entries on pullbacks",
                "trend_down": "📉 Strong downtrend - Look for SHORT entries on rallies",
                "range": "↔️ Range-bound market - Trade support/resistance bounces",
                "high_vol": "⚡ High volatility - Use wider stops, reduce position size",
                "squeeze": "🎯 Volatility squeeze - Prepare for breakout",
                "no_trade": "⚠️ No clear pattern - Stay flat or reduce exposure",
            }

            regime_text = regime.value.replace("_", " ").title()
            color = regime_colors.get(regime.value, "#888")
            interpretation = regime_interpretations.get(regime.value, "Unknown regime")

            # Update header label
            self._regime_label.setText(f"Regime: {regime_text}")
            self._regime_label.setStyleSheet(
                f"font-weight: bold; font-size: 14pt; padding: 5px; color: {color};"
            )

            # Show detailed analysis
            details = (
                f"Current Market Regime: {regime_text}\n\n"
                f"{interpretation}\n\n"
                f"Technical Indicators:\n"
                f"  RSI(14): {latest['rsi']:.1f}\n"
                f"  MACD: {latest['macd']:.4f}\n"
                f"  ADX(14): {latest['adx']:.1f}\n"
                f"  ATR(14): {latest['atr']:.4f}\n"
                f"  BB Width: {latest['bb_width']:.4f}\n"
                f"  Volatility: {features.volatility:.4f}\n\n"
                f"Recommendation:\n"
                f"  - Use strategies optimized for {regime_text}\n"
                f"  - Adjust position sizing based on volatility\n"
                f"  - Monitor for regime changes"
            )

            QMessageBox.information(
                self,
                "Current Regime Analysis",
                details
            )

            logger.info("Regime analysis complete")

        except Exception as e:
            logger.error(f"Regime analysis failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"Failed to analyze regime:\n\n{str(e)}"
            )

    def _draw_regime_boundaries(self, results: dict) -> None:
        """Draw vertical lines for regime boundaries on chart.

        Original: entry_analyzer_backtest.py:691-765

        Args:
            results: Backtest results dict with regime_history
        """
        regime_history = results.get('regime_history', [])
        if not regime_history:
            QMessageBox.information(
                self,
                "No Regime History",
                "No regime changes detected in backtest results."
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
            timestamp = change.get('timestamp')
            regime = change.get('regime', 'unknown')
            color = regime_colors.get(regime, "#888")

            # TODO: Implement chart.add_regime_line(timestamp, regime, color)
            logger.debug(f"Regime boundary: {timestamp} -> {regime}")

        QMessageBox.information(
            self,
            "Regime Boundaries",
            f"Drew {len(regime_history)} regime boundaries on chart.\n\n"
            f"Note: Chart integration pending - boundaries logged for now."
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

        # Enable draw boundaries button
        self._bt_draw_boundaries_btn.setEnabled(True)
        self._bt_create_regime_set_btn.setEnabled(True)

        logger.info("Regime history ready for visualization")
