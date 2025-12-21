"""Unit tests for Backtest Result Converter.

Tests the conversion from Backtrader results to comprehensive BacktestResult models.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.core.models.backtest_models import BacktestResult, Trade, TradeSide


class TestBacktestConverter:
    """Test suite for backtest result conversion."""

    def test_backtest_result_creation(self):
        """Test creating a BacktestResult instance."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)

        result = BacktestResult(
            symbol="AAPL",
            timeframe="1D",
            mode="backtest",
            start=start_date,
            end=end_date,
            initial_capital=10000.0,
            final_capital=12000.0,
            bars=[],
            trades=[],
            equity_curve=[],
            metrics={
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "expectancy": None,
                "max_drawdown_pct": 0.0,
                "max_drawdown_duration_days": None,
                "sharpe_ratio": None,
                "sortino_ratio": None,
                "avg_r_multiple": None,
                "best_r_multiple": None,
                "worst_r_multiple": None,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "total_return_pct": 0.0,
                "annual_return_pct": None,
                "avg_trade_duration_minutes": None,
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0
            },
            strategy_name="Test Strategy"
        )

        assert result.symbol == "AAPL"
        assert result.timeframe == "1D"
        assert result.initial_capital == 10000.0
        assert result.final_capital == 12000.0
        assert result.total_pnl == 2000.0
        assert abs(result.total_pnl_pct - 20.0) < 0.0001  # Floating point tolerance

    def test_trade_model(self):
        """Test Trade model with computed fields."""
        trade = Trade(
            id=f"trade_{uuid.uuid4().hex[:8]}",
            symbol="AAPL",
            side=TradeSide.LONG,
            size=100.0,
            entry_time=datetime(2024, 1, 1, 10, 0),
            entry_price=150.0,
            entry_reason="Strategy signal",
            exit_time=datetime(2024, 1, 2, 15, 30),
            exit_price=155.0,
            exit_reason="Take profit",
            stop_loss=145.0,
            take_profit=160.0,
            realized_pnl=500.0,
            realized_pnl_pct=3.33
        )

        # Test computed fields
        assert trade.is_winner is True
        assert trade.duration is not None
        assert trade.duration > 0  # Should be ~29.5 hours in seconds

        # Test R-multiple calculation
        assert trade.r_multiple is not None
        # Risk was $5 per share * 100 shares = $500
        # Profit was $500
        # R-multiple should be 1.0
        assert abs(trade.r_multiple - 1.0) < 0.01

    def test_trade_json_serialization(self):
        """Test that Trade can be serialized to JSON."""
        trade = Trade(
            id="test_trade_1",
            symbol="AAPL",
            side=TradeSide.LONG,
            size=100.0,
            entry_time=datetime(2024, 1, 1),
            entry_price=150.0,
            entry_reason="Test",
            realized_pnl=500.0,
            realized_pnl_pct=3.33
        )

        # Test model_dump (Pydantic v2)
        trade_dict = trade.model_dump()
        assert trade_dict['symbol'] == "AAPL"
        assert trade_dict['side'] == "long"

        # Test JSON serialization
        trade_json = trade.model_dump_json()
        assert "AAPL" in trade_json
        assert "long" in trade_json

    def test_backtest_result_json_serialization(self):
        """Test that BacktestResult can be serialized to JSON."""
        result = BacktestResult(
            symbol="AAPL",
            timeframe="1D",
            mode="backtest",
            start=datetime(2024, 1, 1),
            end=datetime(2024, 12, 31),
            initial_capital=10000.0,
            final_capital=12000.0,
            bars=[],
            trades=[],
            equity_curve=[],
            metrics={
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "expectancy": None,
                "max_drawdown_pct": 0.0,
                "max_drawdown_duration_days": None,
                "sharpe_ratio": None,
                "sortino_ratio": None,
                "avg_r_multiple": None,
                "best_r_multiple": None,
                "worst_r_multiple": None,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "total_return_pct": 20.0,
                "annual_return_pct": None,
                "avg_trade_duration_minutes": None,
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0
            },
            strategy_name="Test"
        )

        # Test JSON serialization
        result_json = result.model_dump_json()
        assert "AAPL" in result_json
        assert "backtest" in result_json

        # Verify datetime is ISO formatted
        assert "2024-01-01" in result_json


class TestConverterFunctions:
    """Test converter helper functions."""

    def test_converter_import(self):
        """Test that converter module can be imported."""
        try:
            from src.core.backtesting.result_converter import (
                backtrader_to_backtest_result,
            )
            assert callable(backtrader_to_backtest_result)
        except ImportError:
            pytest.skip("Backtrader not installed")

    def test_backtest_models_import(self):
        """Test that backtest models can be imported."""
        from src.core.models.backtest_models import (
            BacktestMetrics,
            BacktestResult,
            Bar,
            EquityPoint,
            Trade,
            TradeSide,
        )

        assert BacktestResult is not None
        assert BacktestMetrics is not None
        assert Bar is not None
        assert Trade is not None
        assert TradeSide is not None
        assert EquityPoint is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
