"""Chart Adapter for Lightweight Charts.

Converts BacktestResult models to JSON format compatible with TradingView's
Lightweight Charts library for visualization in web views.
"""

import json
import logging
from datetime import datetime
from typing import Any, Literal

from src.core.models.backtest_models import BacktestResult, Bar, EquityPoint, Trade, TradeSide

logger = logging.getLogger(__name__)


class ChartAdapter:
    """Adapter for converting BacktestResult to Lightweight Charts format.

    Provides conversion methods for candlestick data, equity curves, indicators,
    and trade markers compatible with TradingView Lightweight Charts.
    """

    @staticmethod
    def backtest_result_to_chart_data(result: BacktestResult) -> dict[str, Any]:
        """Convert comprehensive BacktestResult to Lightweight Charts JSON format.

        Args:
            result: BacktestResult instance with bars, trades, equity curve, etc.

        Returns:
            Dictionary with all chart data ready for Lightweight Charts:
            {
                'candlesticks': [...],      # OHLC data
                'equity_curve': [...],      # Account equity over time
                'markers': [...],           # Entry/Exit markers
                'indicators': {...},        # Technical indicators
                'metadata': {...}           # Chart metadata
            }

        Example:
            >>> adapter = ChartAdapter()
            >>> chart_data = adapter.backtest_result_to_chart_data(backtest_result)
            >>> json_str = json.dumps(chart_data)
        """
        logger.info(f"Converting BacktestResult for {result.symbol} to chart data")

        # Convert bars to candlestick format
        candlesticks = ChartAdapter.bars_to_candlesticks(result.bars)
        logger.debug(f"Converted {len(candlesticks)} candlesticks")

        # Convert equity curve
        equity_curve = ChartAdapter.equity_to_line_series(result.equity_curve)
        logger.debug(f"Converted equity curve with {len(equity_curve)} points")

        # Build markers from trades
        markers = ChartAdapter.build_markers_from_trades(result.trades)
        logger.debug(f"Built {len(markers)} trade markers")

        # Convert indicators
        indicators = ChartAdapter.indicators_to_series(result.indicators)
        logger.debug(f"Converted {len(indicators)} indicators")

        # Build metadata
        metadata = {
            'symbol': result.symbol,
            'timeframe': result.timeframe,
            'mode': result.mode,
            'start': result.start.isoformat(),
            'end': result.end.isoformat(),
            'strategy_name': result.strategy_name,
            'initial_capital': result.initial_capital,
            'final_capital': result.final_capital,
            'total_pnl': result.total_pnl,
            'total_pnl_pct': result.total_pnl_pct,
            'metrics': {
                'total_trades': result.metrics.total_trades,
                'win_rate': result.metrics.win_rate,
                'profit_factor': result.metrics.profit_factor,
                'sharpe_ratio': result.metrics.sharpe_ratio,
                'max_drawdown_pct': result.metrics.max_drawdown_pct,
                'total_return_pct': result.metrics.total_return_pct,
            }
        }

        chart_data = {
            'candlesticks': candlesticks,
            'equity_curve': equity_curve,
            'markers': markers,
            'indicators': indicators,
            'metadata': metadata
        }

        logger.info(
            f"Chart data ready: {len(candlesticks)} bars, "
            f"{len(equity_curve)} equity points, "
            f"{len(markers)} markers, "
            f"{len(indicators)} indicators"
        )

        return chart_data

    @staticmethod
    def bars_to_candlesticks(bars: list[Bar]) -> list[dict[str, Any]]:
        """Convert Bar list to Lightweight Charts candlestick format.

        Args:
            bars: List of Bar instances

        Returns:
            List of candlestick dictionaries:
            [
                {time: '2024-01-01', open: 100, high: 105, low: 99, close: 102},
                ...
            ]
        """
        if not bars:
            return []

        candlesticks = []
        for bar in bars:
            candlestick = {
                'time': ChartAdapter._format_time(bar.time),
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
            }

            # Optionally include volume
            if bar.volume:
                candlestick['volume'] = int(bar.volume)

            candlesticks.append(candlestick)

        return candlesticks

    @staticmethod
    def equity_to_line_series(equity_curve: list[EquityPoint]) -> list[dict[str, Any]]:
        """Convert EquityPoint list to Lightweight Charts line series format.

        Args:
            equity_curve: List of EquityPoint instances

        Returns:
            List of line series data points:
            [
                {time: '2024-01-01', value: 10000},
                ...
            ]
        """
        if not equity_curve:
            return []

        return [
            {
                'time': ChartAdapter._format_time(point.time),
                'value': float(point.equity)
            }
            for point in equity_curve
        ]

    @staticmethod
    def build_markers_from_trades(
        trades: list[Trade],
        show_stop_loss: bool = False,
        show_take_profit: bool = False
    ) -> list[dict[str, Any]]:
        """Build entry/exit markers from Trade list.

        Args:
            trades: List of Trade instances
            show_stop_loss: Whether to show stop loss levels as markers
            show_take_profit: Whether to show take profit levels as markers

        Returns:
            List of marker dictionaries for Lightweight Charts:
            [
                {
                    time: '2024-01-01',
                    position: 'belowBar',  # or 'aboveBar'
                    color: 'green',
                    shape: 'arrowUp',      # or 'arrowDown', 'circle'
                    text: 'Buy @ 100.00'
                },
                ...
            ]
        """
        if not trades:
            return []

        markers = []

        for trade in trades:
            # Entry marker
            entry_marker = ChartAdapter._build_entry_marker(trade)
            markers.append(entry_marker)

            # Exit marker (if trade is closed)
            if trade.exit_time and trade.exit_price:
                exit_marker = ChartAdapter._build_exit_marker(trade)
                markers.append(exit_marker)

            # Optional: Stop Loss / Take Profit markers
            if show_stop_loss and trade.stop_loss:
                sl_marker = ChartAdapter._build_sl_tp_marker(
                    trade, 'stop_loss', trade.stop_loss
                )
                markers.append(sl_marker)

            if show_take_profit and trade.take_profit:
                tp_marker = ChartAdapter._build_sl_tp_marker(
                    trade, 'take_profit', trade.take_profit
                )
                markers.append(tp_marker)

        # Sort markers by time
        markers.sort(key=lambda m: m['time'])

        return markers

    @staticmethod
    def _build_entry_marker(trade: Trade) -> dict[str, Any]:
        """Build entry marker for a trade.

        Args:
            trade: Trade instance

        Returns:
            Entry marker dictionary
        """
        is_long = trade.side == TradeSide.LONG

        return {
            'time': ChartAdapter._format_time(trade.entry_time),
            'position': 'belowBar' if is_long else 'aboveBar',
            'color': '#26a69a' if is_long else '#ef5350',  # Green for long, red for short
            'shape': 'arrowUp' if is_long else 'arrowDown',
            'text': f"{'BUY' if is_long else 'SELL'} @ {trade.entry_price:.2f}",
            'id': f"{trade.id}_entry"
        }

    @staticmethod
    def _build_exit_marker(trade: Trade) -> dict[str, Any]:
        """Build exit marker for a trade.

        Args:
            trade: Trade instance (must have exit_time and exit_price)

        Returns:
            Exit marker dictionary
        """
        is_long = trade.side == TradeSide.LONG
        is_winner = trade.is_winner

        # Exit position opposite of entry
        position = 'aboveBar' if is_long else 'belowBar'

        # Color based on P&L (green for profit, red for loss)
        color = '#4caf50' if is_winner else '#f44336'

        # Shape: circle for exit
        shape = 'circle'

        # Text with P&L
        pnl_sign = '+' if trade.realized_pnl >= 0 else ''
        text = (
            f"{'SELL' if is_long else 'COVER'} @ {trade.exit_price:.2f} "
            f"({pnl_sign}{trade.realized_pnl_pct:.2f}%)"
        )

        return {
            'time': ChartAdapter._format_time(trade.exit_time),
            'position': position,
            'color': color,
            'shape': shape,
            'text': text,
            'id': f"{trade.id}_exit"
        }

    @staticmethod
    def _build_sl_tp_marker(
        trade: Trade,
        marker_type: Literal['stop_loss', 'take_profit'],
        price: float
    ) -> dict[str, Any]:
        """Build stop loss or take profit marker.

        Args:
            trade: Trade instance
            marker_type: Type of marker ('stop_loss' or 'take_profit')
            price: SL or TP price level

        Returns:
            SL/TP marker dictionary
        """
        is_stop_loss = marker_type == 'stop_loss'
        is_long = trade.side == TradeSide.LONG

        # Position: SL below for long (above for short), TP opposite
        if is_stop_loss:
            position = 'belowBar' if is_long else 'aboveBar'
        else:
            position = 'aboveBar' if is_long else 'belowBar'

        # Color: Red for SL, green for TP
        color = '#ff6b6b' if is_stop_loss else '#51cf66'

        # Shape: square for levels
        shape = 'square'

        # Text
        text = f"{'SL' if is_stop_loss else 'TP'}: {price:.2f}"

        return {
            'time': ChartAdapter._format_time(trade.entry_time),
            'position': position,
            'color': color,
            'shape': shape,
            'text': text,
            'id': f"{trade.id}_{marker_type}"
        }

    @staticmethod
    def indicators_to_series(
        indicators: dict[str, list[tuple[datetime, float]]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Convert indicator data to Lightweight Charts line series.

        Args:
            indicators: Dictionary mapping indicator names to time-series data
                       {name: [(datetime, value), ...]}

        Returns:
            Dictionary of line series data:
            {
                'SMA_20': [{time: '2024-01-01', value: 100.5}, ...],
                'RSI': [{time: '2024-01-01', value: 65.2}, ...],
                ...
            }
        """
        if not indicators:
            return {}

        result = {}

        for name, data_points in indicators.items():
            series = [
                {
                    'time': ChartAdapter._format_time(timestamp),
                    'value': float(value)
                }
                for timestamp, value in data_points
            ]
            result[name] = series

        return result

    @staticmethod
    def _format_time(dt: datetime) -> str:
        """Format datetime for Lightweight Charts.

        Lightweight Charts accepts:
        - UNIX timestamp (seconds)
        - YYYY-MM-DD for daily data
        - YYYY-MM-DD HH:MM:SS for intraday

        Args:
            dt: Datetime object

        Returns:
            Formatted time string
        """
        # For intraday data, use UNIX timestamp (more flexible)
        # Lightweight Charts expects seconds, not milliseconds
        return str(int(dt.timestamp()))

    @staticmethod
    def to_json(chart_data: dict[str, Any], indent: int | None = None) -> str:
        """Convert chart data to JSON string.

        Args:
            chart_data: Chart data dictionary from backtest_result_to_chart_data()
            indent: Optional indentation for pretty printing

        Returns:
            JSON string

        Example:
            >>> json_str = ChartAdapter.to_json(chart_data, indent=2)
            >>> with open('chart.json', 'w') as f:
            ...     f.write(json_str)
        """
        return json.dumps(chart_data, indent=indent, default=str)

    @staticmethod
    def validate_chart_data(chart_data: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate chart data structure.

        Args:
            chart_data: Chart data dictionary

        Returns:
            Tuple of (is_valid, error_messages)

        Example:
            >>> is_valid, errors = ChartAdapter.validate_chart_data(chart_data)
            >>> if not is_valid:
            ...     print("Validation errors:", errors)
        """
        errors = []

        # Check required keys
        required_keys = ['candlesticks', 'equity_curve', 'markers', 'indicators', 'metadata']
        for key in required_keys:
            if key not in chart_data:
                errors.append(f"Missing required key: {key}")

        # Validate candlesticks
        if 'candlesticks' in chart_data:
            candlesticks = chart_data['candlesticks']
            if not isinstance(candlesticks, list):
                errors.append("candlesticks must be a list")
            elif candlesticks:
                # Check first candlestick structure
                first = candlesticks[0]
                required_candle_keys = ['time', 'open', 'high', 'low', 'close']
                for key in required_candle_keys:
                    if key not in first:
                        errors.append(f"Candlestick missing key: {key}")
                        break

        # Validate equity curve
        if 'equity_curve' in chart_data:
            equity = chart_data['equity_curve']
            if not isinstance(equity, list):
                errors.append("equity_curve must be a list")
            elif equity:
                first = equity[0]
                if 'time' not in first or 'value' not in first:
                    errors.append("Equity point must have 'time' and 'value'")

        # Validate markers
        if 'markers' in chart_data:
            markers = chart_data['markers']
            if not isinstance(markers, list):
                errors.append("markers must be a list")

        # Validate indicators
        if 'indicators' in chart_data:
            indicators = chart_data['indicators']
            if not isinstance(indicators, dict):
                errors.append("indicators must be a dict")

        is_valid = len(errors) == 0
        return is_valid, errors
