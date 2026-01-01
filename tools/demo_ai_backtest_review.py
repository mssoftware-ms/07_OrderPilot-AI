"""Demo script for AI Backtest Review functionality.

Demonstrates:
- Creating a sample backtest result
- Reviewing backtest with AI analysis
- Extracting insights and recommendations
- Parameter optimization suggestions

Usage:
    python tools/demo_ai_backtest_review.py
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.openai_service import OpenAIService, BacktestReview, AIConfig
from src.core.models.backtest_models import (
    BacktestResult,
    BacktestMetrics,
    Trade,
    TradeSide,
    EquityPoint
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_backtest_result() -> BacktestResult:
    """Create a realistic sample backtest result."""
    start = datetime(2023, 1, 1)
    end = datetime(2023, 12, 31)

    # Create realistic metrics
    metrics = BacktestMetrics(
        total_trades=75,
        winning_trades=48,
        losing_trades=27,
        win_rate=0.64,
        profit_factor=1.85,
        expectancy=125.50,
        max_drawdown_pct=-12.3,
        max_drawdown_duration_days=32.0,
        sharpe_ratio=1.45,
        sortino_ratio=1.85,
        avg_r_multiple=2.1,
        best_r_multiple=6.5,
        worst_r_multiple=-1.8,
        avg_win=280.0,
        avg_loss=-120.0,
        largest_win=1250.0,
        largest_loss=-380.0,
        total_return_pct=35.8,
        annual_return_pct=35.8,
        avg_trade_duration_minutes=2880.0,  # 2 days
        max_consecutive_wins=8,
        max_consecutive_losses=4
    )

    # Create sample trades
    trades = [
        Trade(
            id=f"trade_{i}",
            symbol="AAPL",
            side=TradeSide.LONG if i % 3 != 0 else TradeSide.SHORT,
            size=100.0,
            entry_time=start + timedelta(days=i * 5),
            entry_price=150.0 + (i * 2.5),
            entry_reason="Strategy signal",
            exit_time=start + timedelta(days=i * 5 + 2),
            exit_price=150.0 + (i * 2.5) + (10.0 if i % 2 == 0 else -5.0),
            exit_reason="Exit signal" if i % 2 == 0 else "Stop loss",
            realized_pnl=1000.0 if i % 2 == 0 else -500.0,
            realized_pnl_pct=6.67 if i % 2 == 0 else -3.33,
            stop_loss=145.0 + (i * 2.5)
        )
        for i in range(5)  # Just show 5 example trades
    ]

    # Create equity curve
    equity_curve = [
        EquityPoint(time=start + timedelta(days=i * 30), equity=10000 + (i * 1000))
        for i in range(13)
    ]

    return BacktestResult(
        symbol="AAPL",
        timeframe="1D",
        mode="backtest",
        start=start,
        end=end,
        initial_capital=10000.0,
        final_capital=13580.0,
        trades=trades,
        equity_curve=equity_curve,
        metrics=metrics,
        strategy_name="RSI MACD Combo",
        strategy_params={
            "rsi_period": 14,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "stop_loss_pct": 2.5,
            "take_profit_pct": 5.0
        }
    )


async def demo_ai_backtest_review():
    """Demonstrate AI backtest review functionality."""
    logger.info("=" * 80)
    logger.info("AI BACKTEST REVIEW DEMO")
    logger.info("=" * 80)

    # Step 1: Create sample backtest result
    logger.info("\n[1/4] Creating sample backtest result...")
    result = create_sample_backtest_result()

    logger.info(f"  Strategy: {result.strategy_name}")
    logger.info(f"  Symbol: {result.symbol}")
    logger.info(f"  Period: {result.start.date()} to {result.end.date()}")
    logger.info(f"  Total Return: {result.metrics.total_return_pct:.2f}%")
    logger.info(f"  Sharpe Ratio: {result.metrics.sharpe_ratio:.2f}")
    logger.info(f"  Max Drawdown: {result.metrics.max_drawdown_pct:.2f}%")
    logger.info(f"  Win Rate: {result.metrics.win_rate * 100:.1f}%")
    logger.info(f"  Total Trades: {result.metrics.total_trades}")

    # Step 2: Initialize AI service
    logger.info("\n[2/4] Initializing AI service...")

    # Check for API key in environment
    import os
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.warning("  ⚠️  OPENAI_API_KEY not found in environment variables")
        logger.info("  This demo will simulate the review process without actual AI calls")
        logger.info("  To enable real AI review, set OPENAI_API_KEY environment variable")

        # Create simulated review
        review = BacktestReview(
            overall_assessment=(
                "The RSI MACD Combo strategy demonstrates strong performance with excellent risk-adjusted returns. "
                "A 35.8% annual return combined with a Sharpe ratio of 1.45 indicates consistent profitability "
                "with manageable volatility. The 64% win rate and 1.85 profit factor show the strategy "
                "successfully identifies high-probability setups."
            ),
            performance_rating=8.5,
            strengths=[
                "Exceptional Sharpe ratio of 1.45 demonstrates excellent risk-adjusted returns",
                "High win rate of 64% with strong profit factor of 1.85",
                "Average R-multiple of 2.1 shows effective risk management",
                "Relatively low max drawdown of 12.3% for the return achieved",
                "Good trade frequency with 75 trades over the period"
            ],
            weaknesses=[
                "Max consecutive losses of 4 could be improved with better filtering",
                "Some large losing trades reaching -$380",
                "Average trade duration of 2 days may miss shorter-term opportunities"
            ],
            suggested_improvements=[
                {
                    "improvement": "Add volatility filter to avoid choppy markets",
                    "expected_impact": "Could reduce losing streaks and improve win rate to 68%",
                    "implementation_difficulty": "easy"
                },
                {
                    "improvement": "Implement dynamic position sizing based on ATR",
                    "expected_impact": "Reduce large losses by 30-40%",
                    "implementation_difficulty": "medium"
                },
                {
                    "improvement": "Add trend confirmation with 200-day MA",
                    "expected_impact": "Filter out counter-trend trades, potentially improve profit factor to 2.0+",
                    "implementation_difficulty": "easy"
                }
            ],
            parameter_recommendations={
                "rsi_period": 12,  # Slightly more responsive
                "rsi_oversold": 25,  # More conservative entry
                "rsi_overbought": 75,  # More conservative exit
                "macd_fast": 11,
                "macd_slow": 24,
                "stop_loss_pct": 2.0,  # Tighter stops
                "take_profit_pct": 6.0,  # Higher profit targets
                "volatility_filter": True,
                "trend_filter_period": 200
            },
            risk_assessment=(
                "Low to moderate risk profile. Max drawdown of 12.3% is very manageable and the 32-day "
                "recovery period is acceptable. The positive expectancy of $125.50 per trade provides "
                "a solid edge. Risk per trade is well-controlled at 2.5%. Overall risk characteristics "
                "are suitable for most trading accounts."
            ),
            max_drawdown_analysis=(
                "Max drawdown of 12.3% occurred during a 32-day period in late summer when markets "
                "entered consolidation. The strategy showed good resilience with prompt recovery once "
                "trending resumed. This drawdown is well within acceptable ranges given the 35.8% return. "
                "The worst losing streak of 4 trades corresponds to this period."
            ),
            market_conditions_analysis=(
                "Strategy performs excellently in trending markets (both up and down) due to the "
                "momentum-following nature of MACD combined with RSI mean reversion elements. "
                "Performance degrades slightly in ranging markets but remains profitable. "
                "The combination of indicators provides good adaptability across market conditions."
            ),
            adaptability_score=0.82
        )

        logger.info("  ✓ Using simulated AI review")
    else:
        logger.info("  ✓ OPENAI_API_KEY found")

        # Create AI config
        config = AIConfig(
            enabled=True,
            model_default="gpt-4o-mini",
            model_critical="gpt-4o",
            cost_limit_monthly=50.0,
            timeouts={"read_ms": 30000, "connect_ms": 5000}
        )

        # Initialize service
        service = OpenAIService(config, api_key)
        await service.initialize()

        try:
            logger.info("  Calling OpenAI API for backtest review...")
            review = await service.review_backtest(result)
            logger.info("  ✓ AI review completed")
        finally:
            await service.close()

    # Step 3: Display review results
    logger.info("\n[3/4] AI Review Results:")
    logger.info("=" * 80)

    logger.info(f"\n📊 Overall Assessment:")
    logger.info(f"   {review.overall_assessment}")

    logger.info(f"\n⭐ Performance Rating: {review.performance_rating:.1f}/10")
    logger.info(f"🎯 Adaptability Score: {review.adaptability_score:.2f}")

    logger.info(f"\n💪 Strengths:")
    for i, strength in enumerate(review.strengths, 1):
        logger.info(f"   {i}. {strength}")

    logger.info(f"\n⚠️  Weaknesses:")
    for i, weakness in enumerate(review.weaknesses, 1):
        logger.info(f"   {i}. {weakness}")

    logger.info(f"\n🔧 Suggested Improvements:")
    for i, improvement in enumerate(review.suggested_improvements, 1):
        logger.info(f"   {i}. {improvement['improvement']}")
        logger.info(f"      Impact: {improvement['expected_impact']}")
        logger.info(f"      Difficulty: {improvement['implementation_difficulty']}")

    logger.info(f"\n📈 Parameter Recommendations:")
    for param, value in review.parameter_recommendations.items():
        logger.info(f"   • {param}: {value}")

    logger.info(f"\n⚖️  Risk Assessment:")
    logger.info(f"   {review.risk_assessment}")

    logger.info(f"\n📉 Max Drawdown Analysis:")
    logger.info(f"   {review.max_drawdown_analysis}")

    logger.info(f"\n🌍 Market Conditions Analysis:")
    logger.info(f"   {review.market_conditions_analysis}")

    # Step 4: Summary
    logger.info("\n[4/4] Summary:")
    logger.info("=" * 80)
    logger.info(f"✓ Strategy '{result.strategy_name}' reviewed successfully")
    logger.info(f"✓ Performance rating: {review.performance_rating:.1f}/10")
    logger.info(f"✓ {len(review.strengths)} strengths identified")
    logger.info(f"✓ {len(review.weaknesses)} weaknesses identified")
    logger.info(f"✓ {len(review.suggested_improvements)} improvements suggested")
    logger.info(f"✓ {len(review.parameter_recommendations)} parameters to optimize")

    logger.info("\n" + "=" * 80)
    logger.info("DEMO COMPLETE")
    logger.info("=" * 80)
    logger.info("\nKey Takeaways:")
    logger.info("  1. review_backtest() analyzes BacktestResult with AI")
    logger.info("  2. Returns structured BacktestReview with actionable insights")
    logger.info("  3. Provides performance rating and adaptability score")
    logger.info("  4. Suggests specific improvements with expected impact")
    logger.info("  5. Recommends parameter adjustments for optimization")
    logger.info("\nNext Steps:")
    logger.info("  • Implement suggested improvements")
    logger.info("  • Test recommended parameters")
    logger.info("  • Use Phase 6.2 for automated parameter optimization")

    return 0


async def main():
    """Run the demo."""
    try:
        return await demo_ai_backtest_review()
    except Exception as e:
        logger.exception(f"Demo failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
