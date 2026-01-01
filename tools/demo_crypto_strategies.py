"""Demo: Cryptocurrency Trading Strategies.

Demonstrates:
1. Loading crypto-specific trading strategies from YAML
2. Inspecting strategy configuration and indicators
3. Compiling strategies for backtesting
4. Comparing different crypto strategies
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_load_strategies():
    """Demo: Load and inspect crypto strategies."""
    logger.info("=== Demo 1: Loading Crypto Strategies ===\n")

    from src.core.strategy.loader import StrategyLoader

    loader = StrategyLoader()
    strategies_dir = Path("examples/strategies")

    # List of crypto strategies
    crypto_strategies = [
        "crypto_volatility_breakout.yaml",
        "crypto_mean_reversion.yaml",
        "crypto_momentum_combo.yaml"
    ]

    loaded_strategies = {}

    for strategy_file in crypto_strategies:
        strategy_path = strategies_dir / strategy_file

        if not strategy_path.exists():
            logger.warning(f"❌ Strategy file not found: {strategy_file}")
            continue

        try:
            strategy = loader.load_strategy_from_file(str(strategy_path))
            loaded_strategies[strategy.name] = strategy

            logger.info(f"✅ Loaded: {strategy.name}")
            logger.info(f"   Category: {strategy.category}")
            logger.info(f"   Asset Class: {strategy.asset_class}")
            logger.info(f"   Version: {strategy.version}")
            logger.info(f"   Recommended Symbols: {', '.join(strategy.recommended_symbols[:3])}")
            logger.info(f"   Recommended Timeframes: {', '.join(strategy.recommended_timeframes[:3])}")
            logger.info(f"   Indicators: {len(strategy.indicators)}")
            logger.info("")

        except Exception as e:
            logger.error(f"❌ Failed to load {strategy_file}: {e}")

    logger.info(f"📊 Summary: Loaded {len(loaded_strategies)}/{ len(crypto_strategies)} strategies\n")

    return loaded_strategies


def demo_inspect_strategy_details():
    """Demo: Inspect detailed strategy configuration."""
    logger.info("=== Demo 2: Inspecting Strategy Details ===\n")

    from src.core.strategy.loader import StrategyLoader

    loader = StrategyLoader()
    strategy_path = Path("examples/strategies/crypto_volatility_breakout.yaml")

    if not strategy_path.exists():
        logger.error("Strategy file not found!")
        return

    strategy = loader.load_strategy_from_file(str(strategy_path))

    logger.info(f"📈 Strategy: {strategy.name}")
    logger.info(f"📝 Description:\n{strategy.description}\n")

    # Indicators
    logger.info("🔧 Indicators:")
    for indicator in strategy.indicators:
        logger.info(f"   - {indicator.type} (alias: {indicator.alias})")
        logger.info(f"     Params: {indicator.params}")
        logger.info(f"     Source: {indicator.source}")

    logger.info("")

    # Entry Conditions
    logger.info("📊 Entry Long Condition:")
    logger.info(f"   Type: {strategy.entry_long.type}")
    if hasattr(strategy.entry_long, 'operator'):
        logger.info(f"   Operator: {strategy.entry_long.operator}")

    logger.info("")

    # Risk Management
    if strategy.risk_management:
        logger.info("⚠️ Risk Management:")
        rm = strategy.risk_management
        logger.info(f"   Stop Loss: {rm.stop_loss_pct}%")
        logger.info(f"   Take Profit: {rm.take_profit_pct}%")
        logger.info(f"   Position Size: {rm.position_size_pct}%")
        if rm.trailing_stop_enabled:
            logger.info(f"   Trailing Stop: Enabled (trigger: {rm.trailing_stop_trigger_pct}%)")

    logger.info("")

    # Notes
    if strategy.notes:
        logger.info("📝 Strategy Notes:")
        lines = strategy.notes.split('\n')
        for line in lines[:10]:  # Show first 10 lines
            logger.info(f"   {line}")
        if len(lines) > 10:
            logger.info(f"   ... ({len(lines) - 10} more lines)")

    logger.info("")


def demo_compile_strategies():
    """Demo: Compile strategies to executable format."""
    logger.info("=== Demo 3: Compiling Strategies ===\n")

    from src.core.strategy.loader import StrategyLoader
    from src.core.strategy.compiler import StrategyCompiler

    loader = StrategyLoader()
    compiler = StrategyCompiler()

    strategies_dir = Path("examples/strategies")
    crypto_strategies = [
        "crypto_volatility_breakout.yaml",
        "crypto_mean_reversion.yaml",
        "crypto_momentum_combo.yaml"
    ]

    for strategy_file in crypto_strategies:
        strategy_path = strategies_dir / strategy_file

        if not strategy_path.exists():
            logger.warning(f"❌ Strategy file not found: {strategy_file}")
            continue

        try:
            # Load strategy
            strategy = loader.load_strategy_from_file(str(strategy_path))

            logger.info(f"🔧 Compiling: {strategy.name}...")

            # Compile to Backtrader strategy
            compiled = compiler.compile(strategy)

            logger.info(f"✅ Successfully compiled!")
            logger.info(f"   Compiled class: {compiled.__name__}")
            logger.info("")

        except Exception as e:
            logger.error(f"❌ Compilation failed for {strategy_file}: {e}")
            import traceback
            traceback.print_exc()
            logger.info("")


def demo_compare_strategies():
    """Demo: Compare different crypto strategies."""
    logger.info("=== Demo 4: Comparing Crypto Strategies ===\n")

    from src.core.strategy.loader import StrategyLoader

    loader = StrategyLoader()
    strategies_dir = Path("examples/strategies")

    strategies = {}

    # Load all crypto strategies
    for strategy_file in strategies_dir.glob("crypto_*.yaml"):
        try:
            strategy = loader.load_strategy_from_file(str(strategy_file))
            strategies[strategy.name] = strategy
        except Exception as e:
            logger.warning(f"Failed to load {strategy_file.name}: {e}")

    if not strategies:
        logger.error("No strategies found!")
        return

    # Comparison table
    logger.info("📊 Strategy Comparison:\n")
    logger.info("%-40s | %-20s | %-10s | %-15s" % ("Name", "Category", "Indicators", "Risk (SL%)"))
    logger.info("-" * 90)

    for name, strategy in strategies.items():
        num_indicators = len(strategy.indicators)
        category = strategy.category
        stop_loss = strategy.risk_management.stop_loss_pct if strategy.risk_management else "N/A"

        logger.info("%-40s | %-20s | %-10d | %-15s" % (
            name[:40],
            category[:20],
            num_indicators,
            f"{stop_loss}%"
        ))

    logger.info("")

    # Recommended use cases
    logger.info("🎯 Recommended Use Cases:\n")

    for name, strategy in strategies.items():
        logger.info(f"📈 {name}:")

        # Parse category for use case
        if "Trend" in strategy.category:
            logger.info("   ✓ Best for: Strong trending markets")
            logger.info("   ✗ Avoid: Range-bound / sideways markets")
        elif "Mean Reversion" in strategy.category:
            logger.info("   ✓ Best for: Range-bound / consolidation")
            logger.info("   ✗ Avoid: Strong trending markets")
        elif "Momentum" in strategy.category:
            logger.info("   ✓ Best for: Medium to strong trends")
            logger.info("   ✗ Avoid: Low volatility / choppy markets")

        # Symbols
        symbols = ", ".join(strategy.recommended_symbols[:3])
        logger.info(f"   Recommended: {symbols}")

        # Timeframes
        timeframes = ", ".join(strategy.recommended_timeframes[:3])
        logger.info(f"   Timeframes: {timeframes}")

        logger.info("")


async def demo_backtest_strategy():
    """Demo: Simulate backtesting with a crypto strategy."""
    logger.info("=== Demo 5: Backtesting Simulation ===\n")

    from src.core.strategy.loader import StrategyLoader
    from src.core.market_data import (
        AlpacaCryptoProvider,
        Timeframe,
        AssetClass,
        DataRequest
    )
    import os

    # Check for credentials
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")

    if not api_key or not api_secret:
        logger.warning("⚠️ Alpaca credentials not found in environment!")
        logger.info("Set ALPACA_API_KEY and ALPACA_API_SECRET to run backtest simulation")
        logger.info("Skipping backtest demo...\n")
        return

    # Load strategy
    loader = StrategyLoader()
    strategy_path = Path("examples/strategies/crypto_volatility_breakout.yaml")

    if not strategy_path.exists():
        logger.error("Strategy file not found!")
        return

    strategy = loader.load_strategy_from_file(str(strategy_path))

    logger.info(f"📈 Strategy: {strategy.name}")
    logger.info(f"🪙 Symbol: {strategy.recommended_symbols[0]}")
    logger.info(f"⏰ Timeframe: {strategy.recommended_timeframes[0]}")
    logger.info("")

    # Fetch historical data
    logger.info("📥 Fetching historical crypto data...")

    provider = AlpacaCryptoProvider(api_key, api_secret)

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)  # Last 30 days

    symbol = strategy.recommended_symbols[0]  # BTC/USD

    bars = await provider.fetch_bars(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timeframe=Timeframe.HOUR_1
    )

    if not bars:
        logger.error("❌ No data received!")
        return

    logger.info(f"✅ Fetched {len(bars)} bars for {symbol}")
    logger.info(f"   Date range: {bars[0].timestamp} to {bars[-1].timestamp}")
    logger.info(f"   Latest price: ${bars[-1].close}")
    logger.info("")

    # Show strategy signals (simulated)
    logger.info("🎯 Simulated Strategy Signals:\n")

    logger.info("Note: This is a simplified simulation.")
    logger.info("For real backtesting, use the Backtest module with full strategy compilation.")
    logger.info("")

    # Show indicator values from last bar (simplified)
    last_bar = bars[-1]
    logger.info(f"Latest Bar ({last_bar.timestamp}):")
    logger.info(f"   OHLC: {last_bar.open} / {last_bar.high} / {last_bar.low} / {last_bar.close}")
    logger.info(f"   Volume: {last_bar.volume}")

    # Simple indicator calculation (would be done by compiled strategy)
    # Calculate simple SMA as example
    if len(bars) >= 50:
        sma_50 = sum(bar.close for bar in bars[-50:]) / 50
        logger.info(f"   SMA(50): ${sma_50:.2f}")

        price = last_bar.close
        if price > sma_50:
            logger.info(f"   📈 Price above SMA → Potential LONG bias")
        else:
            logger.info(f"   📉 Price below SMA → Potential SHORT bias")

    logger.info("")


def main():
    """Run all demos."""
    logger.info("=" * 80)
    logger.info("OrderPilot-AI - Crypto Trading Strategies Demo")
    logger.info("=" * 80)
    logger.info("")

    try:
        # Demo 1: Load strategies
        loaded_strategies = demo_load_strategies()

        # Demo 2: Inspect strategy details
        demo_inspect_strategy_details()

        # Demo 3: Compile strategies
        demo_compile_strategies()

        # Demo 4: Compare strategies
        demo_compare_strategies()

        # Demo 5: Backtest simulation (async)
        asyncio.run(demo_backtest_strategy())

    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)

    logger.info("=" * 80)
    logger.info("Demo completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
