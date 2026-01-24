"""Entry Analyzer - Indicator Signals Calculation Mixin.

Extracted from entry_analyzer_indicators.py to keep files under 550 LOC.
Handles indicator drawing and entry signal calculation:
- Draw optimized indicators on chart with color palette
- Calculate entry signals for indicators (BB, RSI, MACD, SMA)
- Chart marker placement for entry signals
- Signal confidence scoring

Date: 2026-01-21
LOC: ~480
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox, QTableWidget

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class IndicatorsSignalsMixin:
    """Indicator signals calculation functionality.

    Provides signal generation and visualization with:
    - Draw optimized indicators on chart with 8-color palette
    - Entry signal calculation for 4 indicators (BB, RSI, MACD, SMA)
    - Chart marker placement with confidence scores
    - Support for long/short trade sides
    - Detailed signal logging and error handling

    Attributes (defined in parent class):
        _optimization_results_table: QTableWidget - Results table
        _candles: list[dict] - Chart candles
    """

    # Type hints for parent class attributes
    _optimization_results_table: QTableWidget
    _candles: list[dict]

    def _on_draw_indicators_clicked(self) -> None:
        """Draw selected indicators on chart with optimized parameters.

        Original: entry_analyzer_indicators.py:684-786

        Features:
        - Parse indicator name and parameters from results table
        - Cycle through color palette (8 colors)
        - Call parent._add_indicator_instance() to draw on chart
        - Show success/error summary
        """
        # Get selected rows
        selected_rows = self._optimization_results_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.information(
                self, "No Selection", "Please select one or more indicators from the results table."
            )
            return

        # Get parent chart window
        parent = self.parent()
        if not hasattr(parent, "_add_indicator_instance"):
            QMessageBox.warning(
                self, "Chart Not Available", "Cannot access chart window to draw indicators."
            )
            logger.error("Parent window does not have _add_indicator_instance method")
            return

        # Color palette for indicators
        colors = [
            "#2196f3",  # Blue
            "#4caf50",  # Green
            "#ff9800",  # Orange
            "#9c27b0",  # Purple
            "#f44336",  # Red
            "#00bcd4",  # Cyan
            "#ffeb3b",  # Yellow
            "#795548",  # Brown
        ]

        drawn_count = 0
        errors = []

        for i, row_index in enumerate(selected_rows):
            row = row_index.row()

            try:
                # Extract indicator info from table
                indicator_name = self._optimization_results_table.item(
                    row, 0
                ).text()  # Indicator column
                params_str = self._optimization_results_table.item(
                    row, 1
                ).text()  # Parameters column

                # Parse parameters string (e.g., "period=14, std=2.0")
                params = {}
                for param_pair in params_str.split(","):
                    param_pair = param_pair.strip()
                    if "=" in param_pair:
                        key, value = param_pair.split("=")
                        key = key.strip()
                        value = value.strip()
                        # Try to convert to int/float
                        try:
                            if "." in value:
                                params[key] = float(value)
                            else:
                                params[key] = int(value)
                        except ValueError:
                            params[key] = value

                # Select color (cycle through palette)
                color = colors[i % len(colors)]

                # Draw indicator on chart
                parent._add_indicator_instance(ind_id=indicator_name, params=params, color=color)

                drawn_count += 1
                logger.info(f"Drew indicator: {indicator_name} with params {params}")

            except Exception as e:
                error_msg = f"{indicator_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to draw indicator {indicator_name}: {e}")

        # Show result message
        if drawn_count > 0:
            msg = f"Successfully drew {drawn_count} indicator(s) on chart."
            if errors:
                msg += f"\n\nErrors ({len(errors)}):\n" + "\n".join(errors)
            QMessageBox.information(self, "Indicators Drawn", msg)
        else:
            QMessageBox.warning(
                self, "Draw Failed", f"Failed to draw indicators:\n\n" + "\n".join(errors)
            )

    def _on_show_entries_clicked(self) -> None:
        """Calculate and show entry signals for selected indicators.

        Original: entry_analyzer_indicators.py:788-957

        Process:
        1. Parse indicator name, parameters, test type, trade side from results table
        2. Calculate entry signals using _calculate_entry_signals()
        3. Draw markers on chart using parent.add_bot_marker()
        4. Show total signals summary
        """
        # Get selected rows
        selected_rows = self._optimization_results_table.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.information(
                self, "No Selection", "Please select one or more indicators from the results table."
            )
            return

        # Get parent chart window
        parent = self.parent()
        if not hasattr(parent, "add_bot_marker"):
            QMessageBox.warning(
                self, "Chart Not Available", "Cannot access chart window to draw entry signals."
            )
            logger.error("Parent window does not have add_bot_marker method")
            return

        # Use the same data that was used for optimization (from self._candles)
        if not self._candles or len(self._candles) == 0:
            QMessageBox.warning(
                self,
                "No Optimization Data",
                "No data available from indicator optimization.\n\n"
                "Please run 'Optimize Indicators' first before showing entry signals.",
            )
            logger.error("No candles data available for entry signal calculation")
            return

        # Convert candles to DataFrame
        try:
            chart_data = self._convert_candles_to_dataframe(self._candles)
            logger.info(f"Converted {len(chart_data)} candles to DataFrame for entry signals")
        except Exception as e:
            QMessageBox.warning(
                self,
                "Data Conversion Error",
                f"Could not convert candle data to DataFrame.\n\nError: {str(e)}",
            )
            logger.error(f"Failed to convert candles: {e}")
            return

        if chart_data is None or len(chart_data) == 0:
            QMessageBox.warning(self, "No Data", "Chart data is empty after conversion.")
            return

        # Prepare DataFrame for indicator calculation
        df = chart_data.copy()

        # Verify structure
        if df.index.name != "timestamp" and "timestamp" not in df.columns:
            QMessageBox.warning(
                self, "Data Format Error", "Chart data does not have proper timestamp index."
            )
            logger.error(f"DataFrame index: {df.index.name}, columns: {df.columns.tolist()}")
            return

        # Ensure we have required OHLCV columns
        required_cols = ["open", "high", "low", "close", "volume"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            QMessageBox.warning(
                self,
                "Data Format Error",
                f"Chart data missing required columns: {', '.join(missing_cols)}\n\n"
                f"Available columns: {', '.join(df.columns.tolist())}",
            )
            logger.error(f"Missing columns: {missing_cols}, available: {df.columns.tolist()}")
            return

        df = df[required_cols]
        logger.info(f"Prepared DataFrame for entry signals: {len(df)} rows, index: {df.index.name}")

        # Import pandas_ta for indicator calculations

        total_signals = 0
        errors = []

        for row_index in selected_rows:
            row = row_index.row()

            try:
                # Extract indicator info from table
                indicator_name = self._optimization_results_table.item(row, 0).text()
                params_str = self._optimization_results_table.item(row, 1).text()
                test_type = (
                    self._optimization_results_table.item(row, 3).text().lower()
                )  # entry/exit
                trade_side = (
                    self._optimization_results_table.item(row, 4).text().lower()
                )  # long/short

                # Parse parameters
                params = {}
                for param_pair in params_str.split(","):
                    param_pair = param_pair.strip()
                    if "=" in param_pair:
                        key, value = param_pair.split("=")
                        key = key.strip()
                        value = value.strip()
                        try:
                            if "." in value:
                                params[key] = float(value)
                            else:
                                params[key] = int(value)
                        except ValueError:
                            params[key] = value

                # Calculate indicator and find entry signals
                signals = self._calculate_entry_signals(df, indicator_name, params, trade_side)

                # Draw signals on chart
                from src.ui.widgets.chart_mixins.bot_overlay_types import MarkerType

                for signal in signals:
                    marker_type = MarkerType.ENTRY_CONFIRMED

                    # Text for marker
                    text = f"{trade_side.upper()} {indicator_name}"
                    if params:
                        param_str = ", ".join([f"{k}={v}" for k, v in list(params.items())[:2]])
                        text += f" [{param_str}]"

                    parent.add_bot_marker(
                        timestamp=signal["timestamp"],
                        price=signal["price"],
                        marker_type=marker_type,
                        side=trade_side,
                        text=text,
                        score=signal.get("confidence", 0.8),
                    )

                total_signals += len(signals)
                logger.info(f"Drew {len(signals)} entry signals for {indicator_name} {params}")

            except Exception as e:
                error_msg = f"{indicator_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to calculate entry signals for {indicator_name}: {e}")

        # Show result message
        if total_signals > 0:
            msg = f"Successfully drew {total_signals} entry signal(s) on chart."
            if errors:
                msg += f"\n\nErrors ({len(errors)}):\n" + "\n".join(errors)
            QMessageBox.information(self, "Entry Signals Drawn", msg)
        else:
            msg = "No entry signals found for selected indicators."
            if errors:
                msg += f"\n\nErrors:\n" + "\n".join(errors)
            QMessageBox.warning(self, "No Signals", msg)

    def _calculate_entry_signals(
        self, df: pd.DataFrame, indicator: str, params: dict, side: str
    ) -> list:
        """Calculate entry signals for a specific indicator.

        Original: entry_analyzer_indicators.py:959-1116

        Supports indicators:
        - BB (Bollinger Bands): Touch lower/upper band with bounce
        - RSI: Cross 30 (long) or 70 (short)
        - MACD: Cross signal line
        - SMA: Price crosses SMA

        Args:
            df: DataFrame with OHLCV data (timestamp index)
            indicator: Indicator name (RSI, BB, MACD, SMA, etc.)
            params: Indicator parameters (e.g., {'period': 14})
            side: 'long' or 'short'

        Returns:
            List of signal dictionaries with timestamp, price, confidence
        """
        import pandas_ta as ta

        signals = []

        try:
            if indicator == "BB":
                # Bollinger Bands entry logic
                period = params.get("period", 20)
                std = params.get("std", 2.0)

                bbands = ta.bbands(df["close"], length=period, std=std)
                if bbands is None or bbands.empty:
                    return signals

                bb_lower = bbands.iloc[:, 0]
                bb_middle = bbands.iloc[:, 1]
                bb_upper = bbands.iloc[:, 2]

                if side == "long":
                    # LONG: Price touches lower band (oversold)
                    touches_lower = df["low"] <= bb_lower * 1.001  # 0.1% tolerance
                    bouncing_up = df["close"] > bb_lower

                    for i in range(1, len(df)):
                        if touches_lower.iloc[i] and bouncing_up.iloc[i]:
                            signals.append(
                                {
                                    "timestamp": df.index[i],
                                    "price": df["close"].iloc[i],
                                    "confidence": 0.75,
                                }
                            )

                else:  # short
                    # SHORT: Price touches upper band (overbought)
                    touches_upper = df["high"] >= bb_upper * 0.999
                    bouncing_down = df["close"] < bb_upper

                    for i in range(1, len(df)):
                        if touches_upper.iloc[i] and bouncing_down.iloc[i]:
                            signals.append(
                                {
                                    "timestamp": df.index[i],
                                    "price": df["close"].iloc[i],
                                    "confidence": 0.75,
                                }
                            )

            elif indicator == "RSI":
                # RSI entry logic
                period = params.get("period", 14)
                rsi = ta.rsi(df["close"], length=period)

                if rsi is None:
                    return signals

                if side == "long":
                    # LONG: RSI crosses above 30 (oversold bounce)
                    for i in range(1, len(df)):
                        if rsi.iloc[i - 1] < 30 and rsi.iloc[i] >= 30:
                            signals.append(
                                {
                                    "timestamp": df.index[i],
                                    "price": df["close"].iloc[i],
                                    "confidence": 0.7,
                                }
                            )

                else:  # short
                    # SHORT: RSI crosses below 70 (overbought reversal)
                    for i in range(1, len(df)):
                        if rsi.iloc[i - 1] > 70 and rsi.iloc[i] <= 70:
                            signals.append(
                                {
                                    "timestamp": df.index[i],
                                    "price": df["close"].iloc[i],
                                    "confidence": 0.7,
                                }
                            )

            elif indicator == "MACD":
                # MACD entry logic
                fast = params.get("fast", 12)
                slow = params.get("slow", 26)
                signal = params.get("signal", 9)

                macd = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
                if macd is None or macd.empty:
                    return signals

                macd_line = macd.iloc[:, 0]
                signal_line = macd.iloc[:, 1]

                if side == "long":
                    # LONG: MACD crosses above signal
                    for i in range(1, len(df)):
                        if (
                            macd_line.iloc[i - 1] < signal_line.iloc[i - 1]
                            and macd_line.iloc[i] > signal_line.iloc[i]
                        ):
                            signals.append(
                                {
                                    "timestamp": df.index[i],
                                    "price": df["close"].iloc[i],
                                    "confidence": 0.8,
                                }
                            )

                else:  # short
                    # SHORT: MACD crosses below signal
                    for i in range(1, len(df)):
                        if (
                            macd_line.iloc[i - 1] > signal_line.iloc[i - 1]
                            and macd_line.iloc[i] < signal_line.iloc[i]
                        ):
                            signals.append(
                                {
                                    "timestamp": df.index[i],
                                    "price": df["close"].iloc[i],
                                    "confidence": 0.8,
                                }
                            )

            elif indicator == "SMA":
                # SMA crossover logic
                period = params.get("period", 20)
                sma = ta.sma(df["close"], length=period)

                if sma is None:
                    return signals

                if side == "long":
                    # LONG: Price crosses above SMA
                    for i in range(1, len(df)):
                        if (
                            df["close"].iloc[i - 1] < sma.iloc[i - 1]
                            and df["close"].iloc[i] > sma.iloc[i]
                        ):
                            signals.append(
                                {
                                    "timestamp": df.index[i],
                                    "price": df["close"].iloc[i],
                                    "confidence": 0.65,
                                }
                            )

                else:  # short
                    # SHORT: Price crosses below SMA
                    for i in range(1, len(df)):
                        if (
                            df["close"].iloc[i - 1] > sma.iloc[i - 1]
                            and df["close"].iloc[i] < sma.iloc[i]
                        ):
                            signals.append(
                                {
                                    "timestamp": df.index[i],
                                    "price": df["close"].iloc[i],
                                    "confidence": 0.65,
                                }
                            )

            # Add more indicators as needed (ADX, PSAR, etc.)

        except Exception as e:
            logger.error(f"Error calculating entry signals for {indicator}: {e}")

        return signals

    # Helper method reference (implemented in BacktestConfigMixin)
    def _convert_candles_to_dataframe(self, candles: list[dict]) -> pd.DataFrame:
        """Convert candles list to pandas DataFrame.

        This method is implemented in BacktestConfigMixin.
        """
