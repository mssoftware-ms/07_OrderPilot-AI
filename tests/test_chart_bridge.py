"""Unit tests for ChartBridge.

Tests the Qt WebChannel bridge between Python and JavaScript.
"""

import json
import uuid
from datetime import datetime

import pytest
from PyQt6.QtCore import QObject

from src.core.models.backtest_models import (
    BacktestMetrics,
    BacktestResult,
    Bar,
    EquityPoint,
    Trade,
    TradeSide,
)
from src.ui.chart.chart_bridge import ChartBridge


class TestChartBridge:
    """Test suite for ChartBridge."""

    @pytest.fixture
    def sample_result(self):
        """Create sample BacktestResult."""
        return BacktestResult(
            symbol="AAPL",
            timeframe="1D",
            mode="backtest",
            start=datetime(2024, 1, 1),
            end=datetime(2024, 1, 10),
            initial_capital=10000.0,
            final_capital=11000.0,
            bars=[
                Bar(
                    time=datetime(2024, 1, i+1),
                    open=100.0 + i,
                    high=105.0 + i,
                    low=99.0 + i,
                    close=102.0 + i,
                    volume=10000,
                    symbol="AAPL"
                )
                for i in range(10)
            ],
            trades=[
                Trade(
                    id=f"trade_{uuid.uuid4().hex[:8]}",
                    symbol="AAPL",
                    side=TradeSide.LONG,
                    size=100.0,
                    entry_time=datetime(2024, 1, 2),
                    entry_price=101.0,
                    entry_reason="Test",
                    exit_time=datetime(2024, 1, 5),
                    exit_price=104.0,
                    exit_reason="Test exit",
                    realized_pnl=300.0,
                    realized_pnl_pct=3.0
                )
            ],
            equity_curve=[
                EquityPoint(time=datetime(2024, 1, i+1), equity=10000.0 + i * 100)
                for i in range(10)
            ],
            metrics=BacktestMetrics(
                total_trades=1,
                winning_trades=1,
                losing_trades=0,
                win_rate=1.0,
                profit_factor=3.0,
                max_drawdown_pct=2.0,
                total_return_pct=10.0
            ),
            strategy_name="Test Strategy"
        )

    def test_bridge_initialization(self, qtbot):
        """Test ChartBridge initialization."""
        bridge = ChartBridge()

        assert bridge is not None
        assert isinstance(bridge, QObject)
        assert bridge._current_result is None

    def test_load_backtest_result_object(self, qtbot, sample_result):
        """Test loading BacktestResult from Python object."""
        bridge = ChartBridge()

        # Connect signal spy
        with qtbot.waitSignal(bridge.chartDataReady, timeout=1000) as blocker:
            bridge.loadBacktestResultObject(sample_result)

        # Check signal was emitted with JSON data
        json_data = blocker.args[0]
        assert json_data is not None

        # Parse and validate JSON
        chart_data = json.loads(json_data)
        assert 'candlesticks' in chart_data
        assert 'equity_curve' in chart_data
        assert 'markers' in chart_data
        assert 'metadata' in chart_data

        assert len(chart_data['candlesticks']) == 10
        assert len(chart_data['equity_curve']) == 10
        assert len(chart_data['markers']) == 2  # 1 entry + 1 exit

    def test_load_backtest_result_json(self, qtbot, sample_result):
        """Test loading BacktestResult from JSON string."""
        bridge = ChartBridge()

        # Convert result to JSON
        result_json = sample_result.model_dump_json()

        # Connect signal spy
        with qtbot.waitSignal(bridge.chartDataReady, timeout=1000) as blocker:
            bridge.loadBacktestResult(result_json)

        # Check signal was emitted
        json_data = blocker.args[0]
        chart_data = json.loads(json_data)

        assert chart_data['metadata']['symbol'] == 'AAPL'
        assert len(chart_data['candlesticks']) == 10

    def test_load_invalid_json(self, qtbot):
        """Test loading invalid JSON emits error signal."""
        bridge = ChartBridge()

        # Connect error signal spy
        with qtbot.waitSignal(bridge.error, timeout=1000) as blocker:
            bridge.loadBacktestResult("invalid json")

        # Check error was emitted
        error_msg = blocker.args[0]
        assert "Invalid JSON" in error_msg

    def test_get_current_symbol(self, qtbot, sample_result):
        """Test getting current symbol."""
        bridge = ChartBridge()

        # Initially empty
        assert bridge.getCurrentSymbol() == ""

        # After loading
        bridge.loadBacktestResultObject(sample_result)
        assert bridge.getCurrentSymbol() == "AAPL"

    def test_get_metrics_summary(self, qtbot, sample_result):
        """Test getting metrics summary."""
        bridge = ChartBridge()

        # Initially empty
        assert bridge.getMetricsSummary() == "{}"

        # After loading
        bridge.loadBacktestResultObject(sample_result)
        summary_json = bridge.getMetricsSummary()

        summary = json.loads(summary_json)
        assert summary['total_trades'] == 1
        assert summary['win_rate'] == 1.0
        assert summary['total_return_pct'] == 10.0

    def test_clear_chart(self, qtbot, sample_result):
        """Test clearing the chart."""
        bridge = ChartBridge()

        # Load data first
        bridge.loadBacktestResultObject(sample_result)
        assert bridge.getCurrentSymbol() == "AAPL"

        # Clear chart
        with qtbot.waitSignal(bridge.chartDataReady, timeout=1000) as blocker:
            bridge.clearChart()

        # Check empty data was emitted
        json_data = blocker.args[0]
        chart_data = json.loads(json_data)

        assert len(chart_data['candlesticks']) == 0
        assert len(chart_data['equity_curve']) == 0
        assert len(chart_data['markers']) == 0
        assert chart_data['metadata']['cleared'] is True

        # Current result should be None
        assert bridge.getCurrentSymbol() == ""

    def test_toggle_markers(self, qtbot, sample_result):
        """Test toggling trade markers."""
        bridge = ChartBridge()
        bridge.loadBacktestResultObject(sample_result)

        # Toggle markers off
        with qtbot.waitSignal(bridge.chartDataReady, timeout=1000) as blocker:
            bridge.toggleMarkers(False)

        json_data = blocker.args[0]
        chart_data = json.loads(json_data)
        assert len(chart_data['markers']) == 0

        # Toggle markers on
        with qtbot.waitSignal(bridge.chartDataReady, timeout=1000) as blocker:
            bridge.toggleMarkers(True)

        json_data = blocker.args[0]
        chart_data = json.loads(json_data)
        assert len(chart_data['markers']) == 2  # Entry + Exit

    def test_update_trade(self, qtbot):
        """Test updating chart with new trade."""
        bridge = ChartBridge()

        trade = Trade(
            id=f"trade_{uuid.uuid4().hex[:8]}",
            symbol="AAPL",
            side=TradeSide.LONG,
            size=100.0,
            entry_time=datetime(2024, 1, 10),
            entry_price=105.0,
            entry_reason="New trade",
            realized_pnl=0.0,
            realized_pnl_pct=0.0
        )

        trade_json = trade.model_dump_json()

        # Update trade
        with qtbot.waitSignal(bridge.chartDataReady, timeout=1000) as blocker:
            bridge.updateTrade(trade_json)

        # Check update data
        json_data = blocker.args[0]
        update_data = json.loads(json_data)

        assert update_data['type'] == 'trade_update'
        assert 'markers' in update_data
        assert len(update_data['markers']) == 1  # Only entry marker (no exit yet)

    def test_signal_connections(self, qtbot):
        """Test that signals can be connected."""
        bridge = ChartBridge()

        # Track signal emissions
        chart_data_emitted = []
        error_emitted = []
        status_emitted = []

        bridge.chartDataReady.connect(lambda x: chart_data_emitted.append(x))
        bridge.error.connect(lambda x: error_emitted.append(x))
        bridge.statusChanged.connect(lambda x: status_emitted.append(x))

        # Trigger error
        bridge.loadBacktestResult("invalid")
        assert len(error_emitted) == 1

        # Clear chart (emits chartDataReady and statusChanged)
        bridge.clearChart()
        assert len(chart_data_emitted) == 1
        assert len(status_emitted) == 1

    def test_load_live_data_not_implemented(self, qtbot):
        """Test that loadLiveData emits error (not implemented yet)."""
        bridge = ChartBridge()

        with qtbot.waitSignal(bridge.error, timeout=1000) as blocker:
            bridge.loadLiveData("AAPL")

        error_msg = blocker.args[0]
        assert "not yet implemented" in error_msg.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
