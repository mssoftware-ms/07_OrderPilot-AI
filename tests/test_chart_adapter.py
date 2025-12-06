"""Unit tests for ChartAdapter.

Tests the conversion from BacktestResult to Lightweight Charts format.
"""

import json
import uuid
from datetime import datetime, timedelta

import pytest

from src.core.models.backtest_models import (
    BacktestMetrics,
    BacktestResult,
    Bar,
    EquityPoint,
    Trade,
    TradeSide,
)
from src.ui.chart.chart_adapter import ChartAdapter


class TestChartAdapter:
    """Test suite for ChartAdapter."""

    @pytest.fixture
    def sample_bars(self):
        """Create sample bars for testing."""
        bars = []
        base_date = datetime(2024, 1, 1, 9, 30)

        for i in range(10):
            bar = Bar(
                time=base_date + timedelta(minutes=i),
                open=100.0 + i,
                high=105.0 + i,
                low=99.0 + i,
                close=102.0 + i,
                volume=1000 + i * 100,
                symbol="AAPL"
            )
            bars.append(bar)

        return bars

    @pytest.fixture
    def sample_trades(self):
        """Create sample trades for testing."""
        trades = []

        # Long winning trade
        trade1 = Trade(
            id=f"trade_1_{uuid.uuid4().hex[:8]}",
            symbol="AAPL",
            side=TradeSide.LONG,
            size=100.0,
            entry_time=datetime(2024, 1, 1, 10, 0),
            entry_price=100.0,
            entry_reason="Buy signal",
            exit_time=datetime(2024, 1, 2, 15, 0),
            exit_price=105.0,
            exit_reason="Take profit",
            stop_loss=95.0,
            take_profit=110.0,
            realized_pnl=500.0,
            realized_pnl_pct=5.0
        )
        trades.append(trade1)

        # Short losing trade
        trade2 = Trade(
            id=f"trade_2_{uuid.uuid4().hex[:8]}",
            symbol="AAPL",
            side=TradeSide.SHORT,
            size=100.0,
            entry_time=datetime(2024, 1, 3, 10, 0),
            entry_price=105.0,
            entry_reason="Sell signal",
            exit_time=datetime(2024, 1, 4, 14, 0),
            exit_price=107.0,
            exit_reason="Stop loss",
            stop_loss=108.0,
            take_profit=100.0,
            realized_pnl=-200.0,
            realized_pnl_pct=-1.9
        )
        trades.append(trade2)

        return trades

    @pytest.fixture
    def sample_equity_curve(self):
        """Create sample equity curve for testing."""
        equity_points = []
        base_date = datetime(2024, 1, 1)
        equity = 10000.0

        for i in range(10):
            equity_points.append(
                EquityPoint(
                    time=base_date + timedelta(days=i),
                    equity=equity + i * 100
                )
            )

        return equity_points

    @pytest.fixture
    def sample_backtest_result(self, sample_bars, sample_trades, sample_equity_curve):
        """Create complete BacktestResult for testing."""
        return BacktestResult(
            symbol="AAPL",
            timeframe="1min",
            mode="backtest",
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 10),
            initial_capital=10000.0,
            final_capital=10900.0,
            bars=sample_bars,
            trades=sample_trades,
            equity_curve=sample_equity_curve,
            metrics=BacktestMetrics(
                total_trades=2,
                winning_trades=1,
                losing_trades=1,
                win_rate=0.5,
                profit_factor=2.5,
                max_drawdown_pct=5.0,
                total_return_pct=9.0
            ),
            strategy_name="Test Strategy",
            strategy_params={"param1": 10, "param2": 20}
        )

    def test_bars_to_candlesticks(self, sample_bars):
        """Test conversion of bars to candlestick format."""
        candlesticks = ChartAdapter.bars_to_candlesticks(sample_bars)

        assert len(candlesticks) == 10
        assert all('time' in c for c in candlesticks)
        assert all('open' in c for c in candlesticks)
        assert all('high' in c for c in candlesticks)
        assert all('low' in c for c in candlesticks)
        assert all('close' in c for c in candlesticks)
        assert all('volume' in c for c in candlesticks)

        # Check first candlestick values
        first = candlesticks[0]
        assert first['open'] == 100.0
        assert first['high'] == 105.0
        assert first['low'] == 99.0
        assert first['close'] == 102.0
        assert first['volume'] == 1000

    def test_bars_to_candlesticks_empty(self):
        """Test conversion with empty bars list."""
        candlesticks = ChartAdapter.bars_to_candlesticks([])
        assert candlesticks == []

    def test_equity_to_line_series(self, sample_equity_curve):
        """Test conversion of equity curve to line series."""
        line_series = ChartAdapter.equity_to_line_series(sample_equity_curve)

        assert len(line_series) == 10
        assert all('time' in point for point in line_series)
        assert all('value' in point for point in line_series)

        # Check values
        first = line_series[0]
        assert first['value'] == 10000.0

        last = line_series[-1]
        assert last['value'] == 10900.0

    def test_build_markers_from_trades(self, sample_trades):
        """Test building markers from trades."""
        markers = ChartAdapter.build_markers_from_trades(sample_trades)

        # Should have 4 markers: 2 entries + 2 exits
        assert len(markers) == 4

        # All markers should have required fields
        for marker in markers:
            assert 'time' in marker
            assert 'position' in marker
            assert 'color' in marker
            assert 'shape' in marker
            assert 'text' in marker
            assert 'id' in marker

        # Check entry markers
        entry_markers = [m for m in markers if '_entry' in m['id']]
        assert len(entry_markers) == 2

        # Long entry should be below bar with green color
        long_entry = next(m for m in entry_markers if 'BUY' in m['text'])
        assert long_entry['position'] == 'belowBar'
        assert long_entry['color'] == '#26a69a'
        assert long_entry['shape'] == 'arrowUp'

        # Short entry should be above bar with red color
        short_entry = next(m for m in entry_markers if 'SELL' in m['text'])
        assert short_entry['position'] == 'aboveBar'
        assert short_entry['color'] == '#ef5350'
        assert short_entry['shape'] == 'arrowDown'

        # Check exit markers
        exit_markers = [m for m in markers if '_exit' in m['id']]
        assert len(exit_markers) == 2

        # Winning trade exit should be green
        winning_exit = next(m for m in exit_markers if '+' in m['text'])
        assert winning_exit['color'] == '#4caf50'
        assert '5.00%' in winning_exit['text']

        # Losing trade exit should be red
        losing_exit = next(m for m in exit_markers if '-' in m['text'])
        assert losing_exit['color'] == '#f44336'
        assert '-1.90%' in losing_exit['text']

    def test_build_markers_with_sl_tp(self, sample_trades):
        """Test building markers with stop loss and take profit."""
        markers = ChartAdapter.build_markers_from_trades(
            sample_trades,
            show_stop_loss=True,
            show_take_profit=True
        )

        # Should have 2 entries + 2 exits + 2 SL + 2 TP = 8 markers (2 trades × 4 markers)
        assert len(markers) == 8

        # Check SL markers
        sl_markers = [m for m in markers if '_stop_loss' in m['id']]
        assert len(sl_markers) == 2
        assert all('SL:' in m['text'] for m in sl_markers)
        assert all(m['color'] == '#ff6b6b' for m in sl_markers)

        # Check TP markers
        tp_markers = [m for m in markers if '_take_profit' in m['id']]
        assert len(tp_markers) == 2
        assert all('TP:' in m['text'] for m in tp_markers)
        assert all(m['color'] == '#51cf66' for m in tp_markers)

    def test_indicators_to_series(self):
        """Test conversion of indicators to line series."""
        indicators = {
            'SMA_20': [
                (datetime(2024, 1, 1), 100.5),
                (datetime(2024, 1, 2), 101.2),
                (datetime(2024, 1, 3), 102.0),
            ],
            'RSI': [
                (datetime(2024, 1, 1), 65.0),
                (datetime(2024, 1, 2), 70.0),
                (datetime(2024, 1, 3), 68.5),
            ]
        }

        series = ChartAdapter.indicators_to_series(indicators)

        assert len(series) == 2
        assert 'SMA_20' in series
        assert 'RSI' in series

        # Check SMA_20
        sma_series = series['SMA_20']
        assert len(sma_series) == 3
        assert all('time' in point for point in sma_series)
        assert all('value' in point for point in sma_series)
        assert sma_series[0]['value'] == 100.5

        # Check RSI
        rsi_series = series['RSI']
        assert len(rsi_series) == 3
        assert rsi_series[0]['value'] == 65.0

    def test_backtest_result_to_chart_data(self, sample_backtest_result):
        """Test full conversion of BacktestResult to chart data."""
        chart_data = ChartAdapter.backtest_result_to_chart_data(sample_backtest_result)

        # Check structure
        assert 'candlesticks' in chart_data
        assert 'equity_curve' in chart_data
        assert 'markers' in chart_data
        assert 'indicators' in chart_data
        assert 'metadata' in chart_data

        # Check candlesticks
        assert len(chart_data['candlesticks']) == 10

        # Check equity curve
        assert len(chart_data['equity_curve']) == 10

        # Check markers (2 trades = 4 markers)
        assert len(chart_data['markers']) == 4

        # Check metadata
        metadata = chart_data['metadata']
        assert metadata['symbol'] == 'AAPL'
        assert metadata['timeframe'] == '1min'
        assert metadata['strategy_name'] == 'Test Strategy'
        assert metadata['total_pnl'] == 900.0
        assert 'metrics' in metadata
        assert metadata['metrics']['total_trades'] == 2
        assert metadata['metrics']['win_rate'] == 0.5

    def test_to_json(self, sample_backtest_result):
        """Test JSON serialization."""
        chart_data = ChartAdapter.backtest_result_to_chart_data(sample_backtest_result)
        json_str = ChartAdapter.to_json(chart_data, indent=2)

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed is not None
        assert 'candlesticks' in parsed
        assert 'equity_curve' in parsed
        assert 'markers' in parsed

    def test_validate_chart_data(self, sample_backtest_result):
        """Test chart data validation."""
        chart_data = ChartAdapter.backtest_result_to_chart_data(sample_backtest_result)

        is_valid, errors = ChartAdapter.validate_chart_data(chart_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_chart_data_invalid(self):
        """Test validation with invalid data."""
        # Missing required keys
        invalid_data = {'candlesticks': []}

        is_valid, errors = ChartAdapter.validate_chart_data(invalid_data)

        assert is_valid is False
        assert len(errors) > 0
        assert any('Missing required key' in err for err in errors)

    def test_validate_chart_data_malformed_candlesticks(self):
        """Test validation with malformed candlesticks."""
        invalid_data = {
            'candlesticks': [{'time': '2024-01-01'}],  # Missing OHLC
            'equity_curve': [],
            'markers': [],
            'indicators': {},
            'metadata': {}
        }

        is_valid, errors = ChartAdapter.validate_chart_data(invalid_data)

        assert is_valid is False
        assert any('Candlestick missing key' in err for err in errors)

    def test_format_time(self):
        """Test time formatting for Lightweight Charts."""
        dt = datetime(2024, 1, 1, 12, 30, 45)
        formatted = ChartAdapter._format_time(dt)

        # Should be UNIX timestamp (seconds as string)
        assert isinstance(formatted, str)
        assert formatted.isdigit()

        # Verify it's correct timestamp
        timestamp = int(formatted)
        reconstructed = datetime.fromtimestamp(timestamp)
        assert reconstructed.year == 2024
        assert reconstructed.month == 1
        assert reconstructed.day == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
