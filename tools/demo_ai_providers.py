"""Demo script for AI Provider integration.

Demonstrates:
- OpenAI GPT-5.1 with Thinking mode
- OpenAI GPT-5.1 Instant (no thinking)
- Anthropic Claude Sonnet 4.5
- Structured outputs across providers
- Streaming responses
- Reasoning modes

Usage:
    # Set environment variables first
    export OPENAI_API_KEY="your-openai-key"
    export ANTHROPIC_API_KEY="your-anthropic-key"

    python tools/demo_ai_providers.py
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field

from src.ai.providers import (
    AIProvider,
    ReasoningMode,
    create_provider,
    get_anthropic_sonnet45,
    get_openai_gpt51_instant,
    get_openai_gpt51_thinking,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== Test Models ====================

class TradingRecommendation(BaseModel):
    """Structured trading recommendation."""
    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="Recommended action: buy, sell, hold")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(..., description="Reasoning for the recommendation")
    key_factors: List[str] = Field(..., description="Key factors influencing decision")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    target_price: float | None = Field(None, description="Target price if applicable")


class MarketAnalysis(BaseModel):
    """Structured market analysis."""
    market_sentiment: str = Field(..., description="Overall market sentiment")
    trend_direction: str = Field(..., description="Trend direction: bullish, bearish, neutral")
    volatility_assessment: str = Field(..., description="Volatility assessment")
    key_drivers: List[str] = Field(..., description="Key market drivers")
    outlook: str = Field(..., description="Market outlook")


# ==================== Demos ====================

async def demo_openai_thinking():
    """Demonstrate OpenAI GPT-5.1 with Thinking mode."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: OpenAI GPT-5.1 with Thinking Mode")
    logger.info("=" * 80)

    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  OPENAI_API_KEY not set. Skipping OpenAI demos.")
        return

    provider = await get_openai_gpt51_thinking(reasoning_mode=ReasoningMode.HIGH)

    try:
        await provider.initialize()

        prompt = """Analyze AAPL stock for a potential trade. Consider:
- Recent price action and momentum
- Market conditions
- Risk factors
- Technical indicators

Provide a structured recommendation."""

        logger.info("\n[1/2] Getting structured recommendation with HIGH reasoning...")
        recommendation = await provider.structured_completion(
            prompt,
            TradingRecommendation
        )

        logger.info("\n📊 Trading Recommendation:")
        logger.info(f"  Symbol: {recommendation.symbol}")
        logger.info(f"  Action: {recommendation.action.upper()}")
        logger.info(f"  Confidence: {recommendation.confidence:.2%}")
        logger.info(f"  Risk Level: {recommendation.risk_level.upper()}")
        if recommendation.target_price:
            logger.info(f"  Target Price: ${recommendation.target_price:.2f}")
        logger.info(f"\n  Reasoning: {recommendation.reasoning}")
        logger.info(f"\n  Key Factors:")
        for i, factor in enumerate(recommendation.key_factors, 1):
            logger.info(f"    {i}. {factor}")

        logger.info("\n[2/2] Streaming analysis...")
        full_response = ""
        async for chunk in provider.stream_completion(
            "Explain why AAPL might be a good long-term investment in 2-3 sentences."
        ):
            full_response += chunk
            print(chunk, end="", flush=True)
        print()

        logger.info(f"\n✓ Received {len(full_response)} characters via streaming")

    finally:
        await provider.close()


async def demo_openai_instant():
    """Demonstrate OpenAI GPT-5.1 Instant (no thinking)."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: OpenAI GPT-5.1 Instant (No Thinking)")
    logger.info("=" * 80)

    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  OPENAI_API_KEY not set. Skipping OpenAI demos.")
        return

    provider = await get_openai_gpt51_instant()

    try:
        await provider.initialize()

        prompt = """Provide a quick market sentiment analysis for today's trading session.
Focus on major indices and key sectors."""

        logger.info("\n[1/1] Getting quick market analysis (no thinking)...")
        analysis = await provider.structured_completion(
            prompt,
            MarketAnalysis
        )

        logger.info("\n📈 Market Analysis (Instant):")
        logger.info(f"  Sentiment: {analysis.market_sentiment}")
        logger.info(f"  Trend: {analysis.trend_direction.upper()}")
        logger.info(f"  Volatility: {analysis.volatility_assessment}")
        logger.info(f"\n  Key Drivers:")
        for i, driver in enumerate(analysis.key_drivers, 1):
            logger.info(f"    {i}. {driver}")
        logger.info(f"\n  Outlook: {analysis.outlook}")

    finally:
        await provider.close()


async def demo_anthropic_sonnet():
    """Demonstrate Anthropic Claude Sonnet 4.5."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: Anthropic Claude Sonnet 4.5")
    logger.info("=" * 80)

    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("⚠️  ANTHROPIC_API_KEY not set. Skipping Anthropic demo.")
        return

    provider = await get_anthropic_sonnet45()

    try:
        await provider.initialize()

        prompt = """Analyze the current cryptocurrency market, focusing on Bitcoin and Ethereum.
Consider regulatory environment, adoption trends, and technical factors.

Provide a structured market analysis."""

        logger.info("\n[1/2] Getting crypto market analysis...")
        analysis = await provider.structured_completion(
            prompt,
            MarketAnalysis
        )

        logger.info("\n₿ Crypto Market Analysis:")
        logger.info(f"  Sentiment: {analysis.market_sentiment}")
        logger.info(f"  Trend: {analysis.trend_direction.upper()}")
        logger.info(f"  Volatility: {analysis.volatility_assessment}")
        logger.info(f"\n  Key Drivers:")
        for i, driver in enumerate(analysis.key_drivers, 1):
            logger.info(f"    {i}. {driver}")
        logger.info(f"\n  Outlook: {analysis.outlook}")

        logger.info("\n[2/2] Streaming explanation...")
        full_response = ""
        async for chunk in provider.stream_completion(
            "Explain Bitcoin's value proposition in simple terms (2-3 sentences)."
        ):
            full_response += chunk
            print(chunk, end="", flush=True)
        print()

        logger.info(f"\n✓ Received {len(full_response)} characters via streaming")

    finally:
        await provider.close()


async def demo_reasoning_comparison():
    """Compare different reasoning modes."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: Reasoning Mode Comparison")
    logger.info("=" * 80)

    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  OPENAI_API_KEY not set. Skipping comparison demo.")
        return

    prompt = "Should I invest in tech stocks right now? Consider market conditions and risk."

    # Test different reasoning modes
    for mode in [ReasoningMode.MINIMAL, ReasoningMode.MEDIUM, ReasoningMode.HIGH]:
        logger.info(f"\n[{mode.value.upper()}] Testing reasoning mode...")

        provider = create_provider(
            AIProvider.OPENAI,
            "gpt-5.1",
            reasoning_mode=mode
        )

        try:
            await provider.initialize()

            import time
            start = time.time()

            recommendation = await provider.structured_completion(
                prompt,
                TradingRecommendation
            )

            elapsed = time.time() - start

            logger.info(f"  ⏱️  Response time: {elapsed:.2f}s")
            logger.info(f"  Action: {recommendation.action}")
            logger.info(f"  Confidence: {recommendation.confidence:.2%}")
            logger.info(f"  Reasoning depth: {len(recommendation.reasoning)} chars")

        finally:
            await provider.close()


async def demo_multi_provider():
    """Demonstrate using multiple providers simultaneously."""
    logger.info("\n" + "=" * 80)
    logger.info("DEMO: Multi-Provider Comparison")
    logger.info("=" * 80)

    prompt = "Is gold a good hedge against inflation? Give a brief analysis."

    providers = []

    # Collect available providers
    if os.getenv("OPENAI_API_KEY"):
        providers.append(("OpenAI GPT-5.1", await get_openai_gpt51_thinking()))

    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append(("Anthropic Sonnet 4.5", await get_anthropic_sonnet45()))

    if not providers:
        logger.warning("⚠️  No API keys set. Skipping multi-provider demo.")
        return

    try:
        # Initialize all
        for name, provider in providers:
            await provider.initialize()

        # Query all in parallel
        logger.info(f"\n[Querying {len(providers)} providers in parallel...]")

        tasks = [
            provider.structured_completion(prompt, MarketAnalysis)
            for _, provider in providers
        ]

        results = await asyncio.gather(*tasks)

        # Display results
        for (name, _), analysis in zip(providers, results):
            logger.info(f"\n📊 {name}:")
            logger.info(f"  Sentiment: {analysis.market_sentiment}")
            logger.info(f"  Trend: {analysis.trend_direction}")
            logger.info(f"  Outlook: {analysis.outlook[:100]}...")

    finally:
        # Close all
        for _, provider in providers:
            await provider.close()


async def main():
    """Run all demos."""
    logger.info("=" * 80)
    logger.info("AI PROVIDERS DEMO")
    logger.info("=" * 80)

    logger.info("\nAvailable Providers:")
    if os.getenv("OPENAI_API_KEY"):
        logger.info("  ✓ OpenAI (GPT-5.1, GPT-5.1 Instant)")
    else:
        logger.info("  ✗ OpenAI (OPENAI_API_KEY not set)")

    if os.getenv("ANTHROPIC_API_KEY"):
        logger.info("  ✓ Anthropic (Claude Sonnet 4.5)")
    else:
        logger.info("  ✗ Anthropic (ANTHROPIC_API_KEY not set)")

    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("\n❌ No API keys found in environment variables!")
        logger.info("\nTo run this demo, set at least one API key:")
        logger.info("  export OPENAI_API_KEY='your-key'")
        logger.info("  export ANTHROPIC_API_KEY='your-key'")
        return 1

    try:
        # Run demos
        await demo_openai_thinking()
        await demo_openai_instant()
        await demo_anthropic_sonnet()
        await demo_reasoning_comparison()
        await demo_multi_provider()

        logger.info("\n" + "=" * 80)
        logger.info("DEMOS COMPLETE")
        logger.info("=" * 80)
        logger.info("\nKey Features Demonstrated:")
        logger.info("  1. Multiple AI providers (OpenAI, Anthropic)")
        logger.info("  2. Structured outputs with Pydantic models")
        logger.info("  3. Reasoning modes (none, minimal, low, medium, high)")
        logger.info("  4. Streaming responses")
        logger.info("  5. Parallel provider queries")
        logger.info("  6. Environment variable configuration")

        return 0

    except Exception as e:
        logger.exception(f"Demo failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
