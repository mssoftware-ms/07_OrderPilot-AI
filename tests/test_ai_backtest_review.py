"""Tests for AI Backtest Review functionality.

Tests cover:
- BacktestReview model validation
- review_backtest() method with BacktestResult
- Prompt building with PromptBuilder
- Integration with OpenAI service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.ai.openai_service import OpenAIService, BacktestReview, AIConfig
from src.core.models.backtest_models import (
    BacktestResult,
    BacktestMetrics,
    Trade,
    TradeSide,
    Bar,
    EquityPoint
)


@pytest.fixture
def ai_config():
    """Create test AI configuration."""
    return AIConfig(
        enabled=True,
        model_default="gpt-4o-mini",
        model_critical="gpt-4o",
        cost_limit_monthly=50.0,
        timeouts={"read_ms": 15000, "connect_ms": 5000}
    )


@pytest.fixture
def sample_backtest_result():
    """Create sample backtest result for testing."""
    start = datetime(2023, 1, 1)
    end = datetime(2023, 12, 31)

    metrics = BacktestMetrics(
        total_trades=50,
        winning_trades=30,
        losing_trades=20,
        win_rate=0.6,
        profit_factor=1.5,
        expectancy=50.0,
        max_drawdown_pct=-15.5,
        max_drawdown_duration_days=45.0,
        sharpe_ratio=1.2,
        sortino_ratio=1.5,
        avg_r_multiple=1.8,
        best_r_multiple=5.0,
        worst_r_multiple=-2.0,
        avg_win=150.0,
        avg_loss=-80.0,
        largest_win=500.0,
        largest_loss=-250.0,
        total_return_pct=25.0,
        annual_return_pct=25.0,
        avg_trade_duration_minutes=1440.0,  # 1 day
        max_consecutive_wins=5,
        max_consecutive_losses=3
    )

    # Create some sample trades
    trades = [
        Trade(
            id="trade_1",
            symbol="AAPL",
            side=TradeSide.LONG,
            size=100.0,
            entry_time=start + timedelta(days=10),
            entry_price=150.0,
            entry_reason="Buy signal",
            exit_time=start + timedelta(days=11),
            exit_price=155.0,
            exit_reason="Sell signal",
            realized_pnl=500.0,
            realized_pnl_pct=3.33,
            stop_loss=145.0,
            take_profit=160.0
        ),
        Trade(
            id="trade_2",
            symbol="AAPL",
            side=TradeSide.LONG,
            size=100.0,
            entry_time=start + timedelta(days=20),
            entry_price=160.0,
            entry_reason="Buy signal",
            exit_time=start + timedelta(days=21),
            exit_price=158.0,
            exit_reason="Stop loss",
            realized_pnl=-200.0,
            realized_pnl_pct=-1.25,
            stop_loss=158.0
        )
    ]

    # Create equity curve
    equity_curve = [
        EquityPoint(time=start, equity=10000.0),
        EquityPoint(time=start + timedelta(days=180), equity=11000.0),
        EquityPoint(time=end, equity=12500.0)
    ]

    return BacktestResult(
        symbol="AAPL",
        timeframe="1D",
        mode="backtest",
        start=start,
        end=end,
        initial_capital=10000.0,
        final_capital=12500.0,
        trades=trades,
        equity_curve=equity_curve,
        metrics=metrics,
        strategy_name="SMA Crossover",
        strategy_params={"fast_period": 20, "slow_period": 50}
    )


class TestBacktestReviewModel:
    """Tests for BacktestReview Pydantic model."""

    def test_backtest_review_creation(self):
        """Test creating a BacktestReview instance."""
        review = BacktestReview(
            overall_assessment="Strong performance with good risk management",
            performance_rating=7.5,
            strengths=["High win rate", "Good Sharpe ratio"],
            weaknesses=["Large drawdowns", "Few trades"],
            suggested_improvements=[
                {
                    "improvement": "Reduce position size",
                    "expected_impact": "Lower drawdown",
                    "implementation_difficulty": "easy"
                }
            ],
            parameter_recommendations={"fast_period": 15, "slow_period": 45},
            risk_assessment="Moderate risk with acceptable drawdowns",
            max_drawdown_analysis="Max drawdown within acceptable range",
            market_conditions_analysis="Strategy performs well in trending markets",
            adaptability_score=0.75
        )

        assert review.performance_rating == 7.5
        assert review.adaptability_score == 0.75
        assert len(review.strengths) == 2
        assert len(review.weaknesses) == 2

    def test_backtest_review_validation(self):
        """Test BacktestReview validation constraints."""
        with pytest.raises(ValueError):
            # Performance rating out of range
            BacktestReview(
                overall_assessment="Test",
                performance_rating=11.0,  # > 10.0
                strengths=["Test"],
                weaknesses=["Test"],
                suggested_improvements=[],
                parameter_recommendations={},
                risk_assessment="Test",
                max_drawdown_analysis="Test",
                market_conditions_analysis="Test",
                adaptability_score=0.5
            )

        with pytest.raises(ValueError):
            # Adaptability score out of range
            BacktestReview(
                overall_assessment="Test",
                performance_rating=5.0,
                strengths=["Test"],
                weaknesses=["Test"],
                suggested_improvements=[],
                parameter_recommendations={},
                risk_assessment="Test",
                max_drawdown_analysis="Test",
                market_conditions_analysis="Test",
                adaptability_score=1.5  # > 1.0
            )


class TestReviewBacktestMethod:
    """Tests for review_backtest() method."""

    @pytest.mark.asyncio
    async def test_review_backtest_with_result(
        self,
        ai_config,
        sample_backtest_result
    ):
        """Test review_backtest() with BacktestResult."""
        service = OpenAIService(ai_config, "test_api_key")

        # Mock structured_completion to return a BacktestReview
        mock_review = BacktestReview(
            overall_assessment="Solid strategy with good risk-adjusted returns",
            performance_rating=7.5,
            strengths=[
                "Positive Sharpe ratio of 1.2",
                "60% win rate is above average",
                "Good profit factor of 1.5"
            ],
            weaknesses=[
                "Max drawdown of 15.5% is moderate",
                "Average loss larger than ideal"
            ],
            suggested_improvements=[
                {
                    "improvement": "Implement tighter stop losses",
                    "expected_impact": "Reduce average loss by 20%",
                    "implementation_difficulty": "easy"
                },
                {
                    "improvement": "Add volatility filter",
                    "expected_impact": "Reduce drawdown periods",
                    "implementation_difficulty": "medium"
                }
            ],
            parameter_recommendations={
                "fast_period": 15,
                "slow_period": 45,
                "stop_loss_pct": 2.0
            },
            risk_assessment="Moderate risk profile with acceptable drawdowns",
            max_drawdown_analysis="Max drawdown of 15.5% occurred over 45 days, within acceptable range",
            market_conditions_analysis="Strategy performs best in trending markets",
            adaptability_score=0.75
        )

        with patch.object(service, 'structured_completion', new=AsyncMock(return_value=mock_review)):
            review = await service.review_backtest(sample_backtest_result)

        assert isinstance(review, BacktestReview)
        assert review.performance_rating == 7.5
        assert len(review.strengths) >= 1
        assert len(review.weaknesses) >= 1
        assert "fast_period" in review.parameter_recommendations

    @pytest.mark.asyncio
    async def test_review_backtest_prompt_building(
        self,
        ai_config,
        sample_backtest_result
    ):
        """Test that review_backtest() builds correct prompt."""
        service = OpenAIService(ai_config, "test_api_key")

        # Mock structured_completion to capture the prompt
        captured_prompt = None

        async def mock_completion(prompt, response_model, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompt
            return BacktestReview(
                overall_assessment="Test",
                performance_rating=5.0,
                strengths=["Test"],
                weaknesses=["Test"],
                suggested_improvements=[],
                parameter_recommendations={},
                risk_assessment="Test",
                max_drawdown_analysis="Test",
                market_conditions_analysis="Test",
                adaptability_score=0.5
            )

        with patch.object(service, 'structured_completion', new=mock_completion):
            await service.review_backtest(sample_backtest_result)

        # Verify prompt contains key information
        assert captured_prompt is not None
        assert "SMA Crossover" in captured_prompt
        assert "AAPL" in captured_prompt
        assert "25.00%" in captured_prompt  # total_return
        assert "1.2" in captured_prompt  # sharpe_ratio
        assert "15.5" in captured_prompt  # max_drawdown

    @pytest.mark.asyncio
    async def test_review_backtest_context_data(
        self,
        ai_config,
        sample_backtest_result
    ):
        """Test that review_backtest() passes correct context."""
        service = OpenAIService(ai_config, "test_api_key")

        captured_context = None

        async def mock_completion(prompt, response_model, context=None, **kwargs):
            nonlocal captured_context
            captured_context = context
            return BacktestReview(
                overall_assessment="Test",
                performance_rating=5.0,
                strengths=["Test"],
                weaknesses=["Test"],
                suggested_improvements=[],
                parameter_recommendations={},
                risk_assessment="Test",
                max_drawdown_analysis="Test",
                market_conditions_analysis="Test",
                adaptability_score=0.5
            )

        with patch.object(service, 'structured_completion', new=mock_completion):
            await service.review_backtest(sample_backtest_result)

        # Verify context contains expected fields
        assert captured_context is not None
        assert captured_context["type"] == "backtest_review"
        assert captured_context["strategy"] == "SMA Crossover"
        assert captured_context["symbol"] == "AAPL"
        assert captured_context["total_return"] == 25.0


class TestPromptBuilderIntegration:
    """Tests for PromptBuilder integration."""

    def test_build_backtest_prompt_with_metrics(self):
        """Test building backtest prompt with metrics."""
        from src.ai.prompts import PromptBuilder

        performance_metrics = {
            "total_return": "25.00%",
            "sharpe_ratio": "1.20",
            "max_drawdown": "-15.50%"
        }

        trade_statistics = {
            "total_trades": 50,
            "win_rate": "60.0%",
            "avg_win": "$150.00"
        }

        prompt = PromptBuilder.build_backtest_prompt(
            strategy_name="Test Strategy",
            test_period="2023-01-01 to 2023-12-31",
            market_conditions="365 days, AAPL on 1D timeframe",
            performance_metrics=performance_metrics,
            trade_statistics=trade_statistics
        )

        # Verify prompt contains all key information
        assert "Test Strategy" in prompt
        assert "2023-01-01 to 2023-12-31" in prompt
        assert "25.00%" in prompt
        assert "1.20" in prompt
        assert "50" in prompt or "50.0" in prompt  # total_trades can be formatted differently


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_full_backtest_review_workflow(
        self,
        ai_config,
        sample_backtest_result
    ):
        """Test complete workflow from BacktestResult to BacktestReview."""
        service = OpenAIService(ai_config, "test_api_key")

        # Create realistic mock response
        mock_review = BacktestReview(
            overall_assessment=(
                "The SMA Crossover strategy shows solid performance with a 25% return "
                "over the test period. The 60% win rate and 1.2 Sharpe ratio indicate "
                "good risk-adjusted returns."
            ),
            performance_rating=7.5,
            strengths=[
                "High win rate of 60% demonstrates consistent signal quality",
                "Sharpe ratio of 1.2 shows good risk-adjusted returns",
                "Profit factor of 1.5 indicates winning trades outweigh losses",
                "Positive expectancy of $50 per trade"
            ],
            weaknesses=[
                "Max drawdown of 15.5% is moderate and may be uncomfortable",
                "Average loss of $80 is relatively high",
                "Only 50 trades over 365 days limits statistical significance"
            ],
            suggested_improvements=[
                {
                    "improvement": "Implement dynamic position sizing based on volatility",
                    "expected_impact": "Could reduce max drawdown by 20-30%",
                    "implementation_difficulty": "medium"
                },
                {
                    "improvement": "Add trend filter to avoid choppy markets",
                    "expected_impact": "Improve win rate to 65-70%",
                    "implementation_difficulty": "easy"
                },
                {
                    "improvement": "Use tighter stop losses with trailing mechanism",
                    "expected_impact": "Reduce average loss to $60",
                    "implementation_difficulty": "easy"
                }
            ],
            parameter_recommendations={
                "fast_period": 15,
                "slow_period": 45,
                "stop_loss_pct": 2.0,
                "position_size_pct": 10.0
            },
            risk_assessment=(
                "Moderate risk profile. Max drawdown of 15.5% is acceptable for most traders. "
                "The 45-day drawdown duration suggests good recovery characteristics."
            ),
            max_drawdown_analysis=(
                "Max drawdown occurred during summer consolidation period. Duration of 45 days "
                "is reasonable. Recovery was swift once trending resumed."
            ),
            market_conditions_analysis=(
                "Strategy performs best in clear trending markets. May struggle in sideways "
                "or highly volatile conditions. Consider adding volatility filter."
            ),
            adaptability_score=0.75
        )

        with patch.object(service, 'structured_completion', new=AsyncMock(return_value=mock_review)):
            review = await service.review_backtest(sample_backtest_result)

        # Verify complete workflow
        assert isinstance(review, BacktestReview)
        assert 0 <= review.performance_rating <= 10
        assert 0 <= review.adaptability_score <= 1
        assert len(review.strengths) > 0
        assert len(review.weaknesses) > 0
        assert len(review.suggested_improvements) > 0
        assert len(review.parameter_recommendations) > 0
        assert review.risk_assessment != ""
        assert review.max_drawdown_analysis != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
