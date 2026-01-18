#!/usr/bin/env python3
"""Deploy JSON Configs for all strategies.

Generates JSON configs from hardcoded strategies and deploys them
to config/bot_configs/strategies/ directory.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.tradingbot.migration.strategy_analyzer import StrategyAnalyzer
from src.core.tradingbot.migration.json_generator import JSONConfigGenerator
from src.core.tradingbot.strategies.catalog import StrategyCatalog


def main():
    """Generate and deploy all JSON configs."""
    # Setup
    catalog = StrategyCatalog()
    analyzer = StrategyAnalyzer(catalog)
    generator = JSONConfigGenerator()

    # Output directory
    output_dir = project_root / "config" / "bot_configs" / "strategies"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate all strategies
    print("=== Deploying JSON Configs ===\n")

    all_strategies = catalog.list_strategies()
    successful = []
    failed = []

    for strategy_name in all_strategies:
        try:
            print(f"Processing: {strategy_name}")

            # Analyze
            strategy_def = catalog.get_strategy(strategy_name)
            analysis = analyzer.analyze_strategy_definition(strategy_def)

            # Generate & Save
            output_path = output_dir / f"{strategy_name}.json"
            generator.generate_and_save(analysis, output_path)

            print(f"  ✓ Saved to {output_path.relative_to(project_root)}\n")
            successful.append(strategy_name)

        except Exception as e:
            print(f"  ✗ FAILED: {e}\n")
            failed.append((strategy_name, str(e)))

    # Summary
    print("=" * 60)
    print(f"✓ Successfully deployed: {len(successful)}/{len(all_strategies)}")
    print(f"  Output directory: {output_dir.relative_to(project_root)}")

    if failed:
        print(f"\n✗ Failed: {len(failed)}")
        for name, error in failed:
            print(f"  - {name}: {error}")
        return 1

    print("\n✅ All configs deployed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
