"""Test script for loading and validating YAML strategy definitions.

Demonstrates loading strategy definitions from YAML files and validating them.

Usage:
    python tools/test_strategy_yaml.py
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.strategy.definition import StrategyDefinition

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_and_validate_strategy(yaml_file: Path) -> StrategyDefinition:
    """Load and validate a strategy from YAML file.

    Args:
        yaml_file: Path to YAML strategy file

    Returns:
        Validated StrategyDefinition

    Raises:
        Exception: If strategy is invalid
    """
    logger.info(f"Loading strategy from: {yaml_file}")

    with open(yaml_file, "r") as f:
        yaml_content = f.read()

    # Parse YAML into StrategyDefinition
    strategy = StrategyDefinition.from_yaml(yaml_content)

    logger.info(f"✓ Strategy loaded: {strategy.name} v{strategy.version}")
    logger.info(f"  Description: {strategy.description[:100] if strategy.description else 'N/A'}...")
    logger.info(f"  Indicators: {len(strategy.indicators)}")
    logger.info(f"  Long trading: Yes")
    logger.info(f"  Short trading: {'Yes' if strategy.entry_short else 'No'}")

    return strategy


def print_strategy_details(strategy: StrategyDefinition) -> None:
    """Print detailed strategy information.

    Args:
        strategy: Strategy definition
    """
    print("\n" + "=" * 80)
    print(f"STRATEGY: {strategy.name}")
    print("=" * 80)

    print(f"\nVersion: {strategy.version}")
    print(f"Description: {strategy.description}")

    # Indicators
    print(f"\n{'INDICATORS':-^80}")
    for ind in strategy.indicators:
        params_str = ", ".join(f"{k}={v}" for k, v in ind.params.items())
        print(f"  • {ind.alias:15} = {ind.type:10} ({params_str})")

    # Entry/Exit Logic
    print(f"\n{'LONG POSITION LOGIC':-^80}")
    print(f"Entry:  {_format_condition(strategy.entry_long)}")
    print(f"Exit:   {_format_condition(strategy.exit_long)}")

    if strategy.entry_short:
        print(f"\n{'SHORT POSITION LOGIC':-^80}")
        print(f"Entry:  {_format_condition(strategy.entry_short)}")
        print(f"Exit:   {_format_condition(strategy.exit_short)}")

    # Risk Management
    print(f"\n{'RISK MANAGEMENT':-^80}")
    rm = strategy.risk_management
    if rm.stop_loss_pct:
        print(f"  Stop Loss: {rm.stop_loss_pct}%")
    if rm.stop_loss_atr:
        print(f"  Stop Loss: {rm.stop_loss_atr} × ATR")
    if rm.take_profit_pct:
        print(f"  Take Profit: {rm.take_profit_pct}%")
    if rm.take_profit_atr:
        print(f"  Take Profit: {rm.take_profit_atr} × ATR")
    if rm.trailing_stop_pct:
        print(f"  Trailing Stop: {rm.trailing_stop_pct}%")
    print(f"  Max Risk per Trade: {rm.max_risk_per_trade_pct}%")
    print(f"  Max Position Size: {rm.max_position_size_pct}%")

    # Metadata
    if strategy.meta:
        print(f"\n{'METADATA':-^80}")
        for key, value in strategy.meta.items():
            if key == "tags":
                print(f"  Tags: {', '.join(value)}")
            elif key == "notes":
                continue  # Skip notes (too long)
            else:
                print(f"  {key.capitalize()}: {value}")

    print("\n" + "=" * 80)


def _format_condition(cond, indent=0) -> str:
    """Format condition for display (recursive).

    Args:
        cond: Condition or LogicGroup
        indent: Indentation level

    Returns:
        Formatted string
    """
    from src.core.strategy.definition import Condition, LogicGroup

    prefix = "  " * indent

    if isinstance(cond, Condition):
        right_str = f"{cond.right}" if not isinstance(cond.right, list) else f"[{cond.right[0]}, {cond.right[1]}]"
        desc = f" ({cond.description})" if cond.description else ""
        return f"{prefix}{cond.left} {cond.operator} {right_str}{desc}"

    elif isinstance(cond, LogicGroup):
        lines = [f"{prefix}{cond.operator}:"]
        for sub_cond in cond.conditions:
            lines.append(_format_condition(sub_cond, indent + 1))
        return "\n".join(lines)

    return str(cond)


def main():
    """Run strategy YAML tests."""
    logger.info("=" * 80)
    logger.info("STRATEGY YAML LOADER & VALIDATOR")
    logger.info("=" * 80)

    # Find strategy files
    strategies_dir = Path(__file__).parent.parent / "examples" / "strategies"
    yaml_files = list(strategies_dir.glob("*.yaml"))

    if not yaml_files:
        logger.warning(f"No YAML files found in {strategies_dir}")
        return

    logger.info(f"\nFound {len(yaml_files)} strategy file(s):")
    for f in yaml_files:
        logger.info(f"  • {f.name}")

    print("\n")

    # Load and validate each strategy
    strategies = []
    for yaml_file in yaml_files:
        try:
            strategy = load_and_validate_strategy(yaml_file)
            strategies.append(strategy)
            print_strategy_details(strategy)

        except Exception as e:
            logger.error(f"✗ Failed to load {yaml_file.name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total strategies: {len(yaml_files)}")
    print(f"Successfully loaded: {len(strategies)}")
    print(f"Failed: {len(yaml_files) - len(strategies)}")

    if len(strategies) == len(yaml_files):
        logger.info("\n✓ ALL STRATEGIES LOADED AND VALIDATED SUCCESSFULLY!")
        return 0
    else:
        logger.error("\n✗ SOME STRATEGIES FAILED TO LOAD")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.exception(f"Script failed: {e}")
        sys.exit(1)
