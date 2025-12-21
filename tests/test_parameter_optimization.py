"""Tests for Parameter Optimization.

Tests cover:
- ParameterOptimizer grid search
- Score calculation
- Sensitivity analysis
- AI-guided optimization
- Parameter refinement
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.core.backtesting.optimization import (
    ParameterOptimizer,
    ParameterRange,
    OptimizationResult,
    OptimizerConfig,
    AIOptimizationInsight,
    quick_optimize,
)
from src.core.models.backtest_models import (
    BacktestResult,
    BacktestMetrics,
)


@pytest.fixture
def sample_backtest_result():
    """Create sample backtest result for testing."""
    metrics = BacktestMetrics(
        total_trades=50,
        winning_trades=30,
        losing_trades=20,
        win_rate=0.6,
        profit_factor=1.5,
        expectancy=50.0,
        max_drawdown_pct=-12.5,
        sharpe_ratio=1.2,
        sortino_ratio=1.5,
        total_return_pct=25.0,
        annual_return_pct=25.0,
    )

    return BacktestResult(
        symbol="AAPL",
        timeframe="1D",
        mode="backtest",
        start=datetime(2023, 1, 1),
        end=datetime(2023, 12, 31),
        initial_capital=10000.0,
        final_capital=12500.0,
        metrics=metrics,
        strategy_name="Test Strategy"
    )


class TestParameterRange:
    """Tests for ParameterRange model."""

    def test_parameter_range_creation(self):
        """Test creating a ParameterRange."""
        param = ParameterRange(
            name="fast_period",
            values=[10, 15, 20],
            type="discrete"
        )

        assert param.name == "fast_period"
        assert param.values == [10, 15, 20]
        assert param.type == "discrete"


class TestOptimizerConfig:
    """Tests for OptimizerConfig."""

    def test_default_config(self):
        """Test default optimizer configuration."""
        config = OptimizerConfig()

        assert config.max_workers == 4
        assert config.primary_metric == "sharpe_ratio"
        assert config.use_ai_guidance is True
        assert config.min_trades == 10

    def test_custom_config(self):
        """Test custom optimizer configuration."""
        config = OptimizerConfig(
            max_workers=8,
            primary_metric="sortino_ratio",
            min_trades=20
        )

        assert config.max_workers == 8
        assert config.primary_metric == "sortino_ratio"
        assert config.min_trades == 20


class TestParameterOptimizer:
    """Tests for ParameterOptimizer."""

    @pytest.mark.asyncio
    async def test_optimizer_initialization(self):
        """Test optimizer initialization."""
        async def mock_runner(params):
            return None

        optimizer = ParameterOptimizer(mock_runner)

        assert optimizer.backtest_runner == mock_runner
        assert optimizer.config.primary_metric == "sharpe_ratio"
        assert optimizer._tests == []

    @pytest.mark.asyncio
    async def test_grid_search_simple(self, sample_backtest_result):
        """Test simple grid search optimization."""
        # Mock backtest runner that returns results with varying Sharpe ratios
        call_count = 0

        async def mock_runner(params):
            nonlocal call_count
            # Create result with Sharpe ratio based on parameters
            sharpe = 1.0 + (params.get("fast_period", 10) / 100.0)

            result = BacktestResult(
                symbol="TEST",
                timeframe="1D",
                mode="backtest",
                start=datetime(2023, 1, 1),
                end=datetime(2023, 12, 31),
                initial_capital=10000.0,
                final_capital=11000.0,
                metrics=BacktestMetrics(
                    total_trades=50,
                    winning_trades=30,
                    losing_trades=20,
                    win_rate=0.6,
                    profit_factor=1.5,
                    max_drawdown_pct=-10.0,
                    sharpe_ratio=sharpe,
                    total_return_pct=10.0
                )
            )
            call_count += 1
            return result

        # Create optimizer
        config = OptimizerConfig(use_ai_guidance=False)
        optimizer = ParameterOptimizer(mock_runner, config)

        # Define parameter ranges
        ranges = [
            ParameterRange(name="fast_period", values=[10, 15, 20]),
            ParameterRange(name="slow_period", values=[40, 50])
        ]

        # Run optimization
        result = await optimizer.grid_search(ranges)

        # Verify results
        assert result.total_tests == 6  # 3 * 2 combinations
        assert result.successful_tests == 6
        assert result.best_score > 0
        assert "fast_period" in result.best_parameters
        assert "slow_period" in result.best_parameters
        assert result.best_parameters["fast_period"] == 20  # Highest fast_period gives best Sharpe

    @pytest.mark.asyncio
    async def test_grid_search_with_failures(self):
        """Test grid search with some failed tests."""
        call_count = 0

        async def mock_runner(params):
            nonlocal call_count
            call_count += 1

            # Fail on specific parameter combination
            if params.get("fast_period") == 15:
                raise ValueError("Test failure")

            return BacktestResult(
                symbol="TEST",
                timeframe="1D",
                mode="backtest",
                start=datetime(2023, 1, 1),
                end=datetime(2023, 12, 31),
                initial_capital=10000.0,
                final_capital=11000.0,
                metrics=BacktestMetrics(
                    total_trades=50,
                    winning_trades=30,
                    losing_trades=20,
                    win_rate=0.6,
                    profit_factor=1.5,
                    max_drawdown_pct=-10.0,
                    sharpe_ratio=1.2,
                    total_return_pct=10.0
                )
            )

        config = OptimizerConfig(use_ai_guidance=False)
        optimizer = ParameterOptimizer(mock_runner, config)

        ranges = [
            ParameterRange(name="fast_period", values=[10, 15, 20])
        ]

        result = await optimizer.grid_search(ranges)

        assert result.total_tests == 3
        assert result.successful_tests == 2  # One failed
        assert result.best_score > 0

    def test_calculate_score(self, sample_backtest_result):
        """Test score calculation."""
        async def mock_runner(params):
            return None

        optimizer = ParameterOptimizer(mock_runner)

        score = optimizer._calculate_score(sample_backtest_result)

        # Should return Sharpe ratio as primary metric
        assert score == 1.2

    def test_calculate_score_with_constraints(self):
        """Test score calculation with constraint violations."""
        async def mock_runner(params):
            return None

        optimizer = ParameterOptimizer(mock_runner)

        # Result with too few trades
        result = BacktestResult(
            symbol="TEST",
            timeframe="1D",
            mode="backtest",
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31),
            initial_capital=10000.0,
            final_capital=11000.0,
            metrics=BacktestMetrics(
                total_trades=5,  # Below min_trades
                winning_trades=3,
                losing_trades=2,
                win_rate=0.6,
                profit_factor=1.5,
                max_drawdown_pct=-10.0,
                sharpe_ratio=1.5,
                total_return_pct=10.0
            )
        )

        score = optimizer._calculate_score(result)
        assert score == float('-inf')

    def test_extract_metrics(self, sample_backtest_result):
        """Test metric extraction."""
        async def mock_runner(params):
            return None

        optimizer = ParameterOptimizer(mock_runner)

        metrics = optimizer._extract_metrics(sample_backtest_result)

        assert "sharpe_ratio" in metrics
        assert "total_return_pct" in metrics
        assert "win_rate" in metrics
        assert metrics["sharpe_ratio"] == 1.2
        assert metrics["total_return_pct"] == 25.0

    @pytest.mark.asyncio
    async def test_sensitivity_analysis(self):
        """Test parameter sensitivity analysis."""
        async def mock_runner(params):
            # Sharpe varies significantly with fast_period
            sharpe = 0.5 + (params.get("fast_period", 10) / 50.0)
            # Sharpe doesn't vary much with slow_period
            sharpe += (params.get("slow_period", 40) / 1000.0)

            return BacktestResult(
                symbol="TEST",
                timeframe="1D",
                mode="backtest",
                start=datetime(2023, 1, 1),
                end=datetime(2023, 12, 31),
                initial_capital=10000.0,
                final_capital=11000.0,
                metrics=BacktestMetrics(
                    total_trades=50,
                    winning_trades=30,
                    losing_trades=20,
                    win_rate=0.6,
                    profit_factor=1.5,
                    max_drawdown_pct=-10.0,
                    sharpe_ratio=sharpe,
                    total_return_pct=10.0
                )
            )

        config = OptimizerConfig(use_ai_guidance=False)
        optimizer = ParameterOptimizer(mock_runner, config)

        ranges = [
            ParameterRange(name="fast_period", values=[10, 20, 30]),
            ParameterRange(name="slow_period", values=[40, 50])
        ]

        result = await optimizer.grid_search(ranges)

        # Check sensitivity analysis
        assert "fast_period" in result.sensitivity_analysis
        assert "slow_period" in result.sensitivity_analysis

        # fast_period should have higher sensitivity
        fast_sensitivity = result.sensitivity_analysis["fast_period"]["sensitivity_score"]
        slow_sensitivity = result.sensitivity_analysis["slow_period"]["sensitivity_score"]

        assert fast_sensitivity > slow_sensitivity


class TestAIOptimizationInsight:
    """Tests for AIOptimizationInsight model."""

    def test_insight_creation(self):
        """Test creating AI optimization insights."""
        insight = AIOptimizationInsight(
            summary="Optimization found good parameters",
            best_parameter_analysis="Fast period of 15 performs best",
            parameter_importance={"fast_period": 0.8, "slow_period": 0.3},
            sensitivity_insights=["Fast period is critical"],
            recommendations=[
                {"improvement": "Test faster periods", "expected_impact": "Higher Sharpe"}
            ],
            confidence_score=0.85
        )

        assert insight.confidence_score == 0.85
        assert len(insight.parameter_importance) == 2
        assert insight.parameter_importance["fast_period"] > insight.parameter_importance["slow_period"]


class TestQuickOptimize:
    """Tests for quick_optimize convenience function."""

    @pytest.mark.asyncio
    async def test_quick_optimize(self):
        """Test quick optimize function."""
        async def mock_runner(params):
            sharpe = 1.0 + (params.get("period", 10) / 100.0)

            return BacktestResult(
                symbol="TEST",
                timeframe="1D",
                mode="backtest",
                start=datetime(2023, 1, 1),
                end=datetime(2023, 12, 31),
                initial_capital=10000.0,
                final_capital=11000.0,
                metrics=BacktestMetrics(
                    total_trades=50,
                    winning_trades=30,
                    losing_trades=20,
                    win_rate=0.6,
                    profit_factor=1.5,
                    max_drawdown_pct=-10.0,
                    sharpe_ratio=sharpe,
                    total_return_pct=10.0
                )
            )

        result = await quick_optimize(
            mock_runner,
            {"period": [10, 15, 20]},
            primary_metric="sharpe_ratio"
        )

        assert result.total_tests == 3
        assert result.successful_tests == 3
        assert result.best_parameters["period"] == 20


class TestOptimizationResult:
    """Tests for OptimizationResult model."""

    def test_optimization_result_creation(self, sample_backtest_result):
        """Test creating optimization result."""
        from src.core.backtesting.optimization import ParameterTest

        tests = [
            ParameterTest(
                parameters={"fast": 10, "slow": 40},
                score=1.2,
                metrics={"sharpe_ratio": 1.2}
            ),
            ParameterTest(
                parameters={"fast": 15, "slow": 50},
                score=1.5,
                metrics={"sharpe_ratio": 1.5}
            )
        ]

        result = OptimizationResult(
            best_parameters={"fast": 15, "slow": 50},
            best_score=1.5,
            best_result=sample_backtest_result,
            all_tests=tests,
            total_tests=2,
            successful_tests=2,
            optimization_time_seconds=10.5,
            sensitivity_analysis={}
        )

        assert result.best_score == 1.5
        assert result.total_tests == 2
        assert result.successful_tests == 2
        assert len(result.all_tests) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
