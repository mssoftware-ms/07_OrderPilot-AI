"""Demo script for trading mode configuration.

Demonstrates:
- Creating profiles for different trading modes
- Mode-specific validation and safety checks
- Safe mode switching
- Loading/saving mode configurations

Usage:
    python tools/demo_trading_modes.py
"""

import logging
import sys
from decimal import Decimal
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    BrokerType,
    ProfileConfig,
    TradingMode,
    ConfigManager,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_factory_methods():
    """Demonstrate profile factory methods for each mode."""
    logger.info("\n" + "="*80)
    logger.info("DEMO: Profile Factory Methods")
    logger.info("="*80)

    # 1. Create backtest profile
    logger.info("\n[1/3] Creating BACKTEST profile")
    backtest = ProfileConfig.create_backtest_profile(
        name="demo_backtest",
        initial_capital=Decimal("50000")
    )
    logger.info(f"  Profile: {backtest.profile_name}")
    logger.info(f"  Mode: {backtest.trading_mode.value}")
    logger.info(f"  Broker: {backtest.broker.broker_type.value}")
    logger.info(f"  Initial Capital: ${backtest.backtest.initial_capital:,}")
    logger.info(f"  Manual Approval: {backtest.execution.manual_approval_default}")
    logger.info(f"  ✓ Safe for backtest: {backtest.is_safe_for_mode(TradingMode.BACKTEST)[0]}")

    # 2. Create paper trading profile
    logger.info("\n[2/3] Creating PAPER TRADING profile")
    paper = ProfileConfig.create_paper_profile(
        name="demo_paper",
        broker_type=BrokerType.ALPACA
    )
    logger.info(f"  Profile: {paper.profile_name}")
    logger.info(f"  Mode: {paper.trading_mode.value}")
    logger.info(f"  Broker: {paper.broker.broker_type.value}")
    logger.info(f"  Paper Trading: {paper.broker.paper_trading}")
    logger.info(f"  Manual Approval: {paper.execution.manual_approval_default}")
    logger.info(f"  Emergency Stop: {paper.execution.emergency_stop_active}")
    logger.info(f"  ✓ Safe for paper: {paper.is_safe_for_mode(TradingMode.PAPER)[0]}")

    # 3. Create live trading profile
    logger.info("\n[3/3] Creating LIVE TRADING profile")
    live = ProfileConfig.create_live_profile(
        name="demo_live",
        broker_type=BrokerType.ALPACA
    )
    logger.info(f"  Profile: {live.profile_name}")
    logger.info(f"  Mode: {live.trading_mode.value}")
    logger.info(f"  Broker: {live.broker.broker_type.value}")
    logger.info(f"  Paper Trading: {live.broker.paper_trading} (REAL MONEY)")
    logger.info(f"  Manual Approval: {live.execution.manual_approval_default} ⚠️  REQUIRED")
    logger.info(f"  Emergency Stop: {live.execution.emergency_stop_active} ⚠️  REQUIRED")
    logger.info(f"  Max Daily Loss: ${live.trading.max_daily_loss}")
    logger.info(f"  Max Positions: {live.trading.max_open_positions}")
    logger.info(f"  ✓ Safe for live: {live.is_safe_for_mode(TradingMode.LIVE)[0]}")


def demo_safety_validation():
    """Demonstrate safety validation for different modes."""
    logger.info("\n" + "="*80)
    logger.info("DEMO: Safety Validation")
    logger.info("="*80)

    # Create paper profile
    paper = ProfileConfig.create_paper_profile()

    # Check safety for different modes
    logger.info("\n[1/3] Checking if PAPER profile is safe for BACKTEST mode")
    is_safe, issues = paper.is_safe_for_mode(TradingMode.BACKTEST)
    logger.info(f"  Safe: {is_safe}")
    if not is_safe:
        for issue in issues:
            logger.info(f"    ❌ {issue}")

    logger.info("\n[2/3] Checking if PAPER profile is safe for PAPER mode")
    is_safe, issues = paper.is_safe_for_mode(TradingMode.PAPER)
    logger.info(f"  Safe: {is_safe}")
    if not is_safe:
        for issue in issues:
            logger.info(f"    ❌ {issue}")
    else:
        logger.info("    ✓ All safety checks passed")

    logger.info("\n[3/3] Checking if PAPER profile is safe for LIVE mode")
    is_safe, issues = paper.is_safe_for_mode(TradingMode.LIVE)
    logger.info(f"  Safe: {is_safe}")
    if not is_safe:
        for issue in issues:
            logger.info(f"    ❌ {issue}")


def demo_mode_switching():
    """Demonstrate safe mode switching."""
    logger.info("\n" + "="*80)
    logger.info("DEMO: Mode Switching")
    logger.info("="*80)

    # Start with paper profile
    profile = ProfileConfig.create_paper_profile()
    logger.info(f"\n[Initial] Mode: {profile.trading_mode.value}")

    # Safe switch: Paper → Backtest (will fail validation)
    logger.info("\n[1/3] Attempting to switch PAPER → BACKTEST")
    try:
        profile.switch_to_mode(TradingMode.BACKTEST, validate=True)
        logger.info("  ✓ Switch succeeded")
    except ValueError as e:
        logger.info(f"  ❌ Switch rejected: {str(e)[:80]}...")

    # Switch without validation (unsafe)
    logger.info("\n[2/3] Forcing switch PAPER → BACKTEST (no validation)")
    profile.switch_to_mode(TradingMode.BACKTEST, validate=False)
    logger.info(f"  Mode after switch: {profile.trading_mode.value}")
    logger.info("  ⚠️  Warning: Configuration may not be safe for backtest mode")

    # Try to switch to LIVE (should fail)
    logger.info("\n[3/3] Attempting to switch BACKTEST → LIVE")
    try:
        profile.switch_to_mode(TradingMode.LIVE, validate=True)
        logger.info("  ✓ Switch succeeded")
    except ValueError as e:
        logger.info(f"  ❌ Switch rejected (as expected)")
        logger.info(f"  Reason: Configuration not safe for live trading")


def demo_config_manager():
    """Demonstrate ConfigManager with mode profiles."""
    logger.info("\n" + "="*80)
    logger.info("DEMO: ConfigManager Integration")
    logger.info("="*80)

    # Create temporary config directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)

        # Create config manager
        manager = ConfigManager(config_dir=config_dir)

        # Create and save profiles for each mode
        logger.info("\n[1/3] Creating and saving mode profiles")
        backtest = ProfileConfig.create_backtest_profile(name="backtest")
        paper = ProfileConfig.create_paper_profile(name="paper")
        live = ProfileConfig.create_live_profile(name="live")

        manager.save_profile(backtest)
        manager.save_profile(paper)
        manager.save_profile(live)

        logger.info(f"  ✓ Saved 3 profiles to {config_dir}")

        # List available profiles
        logger.info("\n[2/3] Listing available profiles")
        profiles = manager.list_profiles()
        for profile_name in profiles:
            logger.info(f"  • {profile_name}")

        # Load each profile
        logger.info("\n[3/3] Loading profiles")
        for profile_name in profiles:
            loaded = manager.load_profile(profile_name)
            logger.info(f"  • {profile_name}: mode={loaded.trading_mode.value}, "
                       f"broker={loaded.broker.broker_type.value}")


def demo_validation_errors():
    """Demonstrate validation errors for invalid configurations."""
    logger.info("\n" + "="*80)
    logger.info("DEMO: Validation Errors")
    logger.info("="*80)

    # Try to create LIVE mode with paper_trading=True
    logger.info("\n[1/2] Attempting to create LIVE mode with paper_trading=True")
    try:
        from src.config import BrokerConfig, ExecutionConfig
        profile = ProfileConfig(
            profile_name="invalid_live",
            trading_mode=TradingMode.LIVE,
            broker=BrokerConfig(
                broker_type=BrokerType.ALPACA,
                paper_trading=True  # ❌ Invalid for LIVE
            ),
            execution=ExecutionConfig(
                manual_approval_default=True
            )
        )
        logger.info("  ❌ Validation should have failed!")
    except ValueError as e:
        logger.info(f"  ✓ Correctly rejected: {e}")

    # Try to create LIVE mode without manual approval
    logger.info("\n[2/2] Attempting to create LIVE mode without manual approval")
    try:
        from src.config import BrokerConfig, ExecutionConfig
        profile = ProfileConfig(
            profile_name="invalid_live2",
            trading_mode=TradingMode.LIVE,
            broker=BrokerConfig(
                broker_type=BrokerType.ALPACA,
                paper_trading=False
            ),
            execution=ExecutionConfig(
                manual_approval_default=False  # ❌ Invalid for LIVE
            )
        )
        logger.info("  ❌ Validation should have failed!")
    except ValueError as e:
        logger.info(f"  ✓ Correctly rejected: {e}")


def main():
    """Run all demos."""
    logger.info("="*80)
    logger.info("TRADING MODE CONFIGURATION DEMO")
    logger.info("="*80)

    try:
        demo_factory_methods()
        demo_safety_validation()
        demo_mode_switching()
        demo_config_manager()
        demo_validation_errors()

        logger.info("\n" + "="*80)
        logger.info("DEMO COMPLETE")
        logger.info("="*80)
        logger.info("\nKey Takeaways:")
        logger.info("  1. Use factory methods to create mode-specific profiles")
        logger.info("  2. Always validate before switching to LIVE mode")
        logger.info("  3. LIVE mode requires manual_approval_default=True")
        logger.info("  4. LIVE mode requires paper_trading=False")
        logger.info("  5. Use is_safe_for_mode() to check configuration safety")

        return 0

    except Exception as e:
        logger.exception(f"Demo failed: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.exception(f"Demo crashed: {e}")
        sys.exit(1)
