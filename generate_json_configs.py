#!/usr/bin/env python3
"""Standalone script to generate JSON configs from hardcoded strategies.

This script imports ONLY the migration modules to avoid dependency conflicts.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Direct imports to avoid loading core.__init__.py
import importlib.util

def import_module_from_path(module_path):
    """Import module directly from file path."""
    spec = importlib.util.spec_from_file_location("temp_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import modules directly
strategy_analyzer_path = project_root / "src/core/tradingbot/migration/strategy_analyzer.py"
json_generator_path = project_root / "src/core/tradingbot/migration/json_generator.py"
catalog_path = project_root / "src/core/tradingbot/strategies/catalog.py"

sa_module = import_module_from_path(strategy_analyzer_path)
jg_module = import_module_from_path(json_generator_path)
cat_module = import_module_from_path(catalog_path)

StrategyAnalyzer = sa_module.StrategyAnalyzer
JSONConfigGenerator = jg_module.JSONConfigGenerator
StrategyCatalog = cat_module.StrategyCatalog


def main():
    """Generate all JSON configs."""
    print("=" * 70)
    print("JSON Config Generation - Phase 6.1")
    print("=" * 70)

    # Setup
    catalog = StrategyCatalog()
    analyzer = StrategyAnalyzer(catalog)
    generator = JSONConfigGenerator(schema_version="1.0.0")

    # Output directory
    output_dir = Path("config/bot_configs/strategies")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nOutput Directory: {output_dir}")
    print(f"Strategies to convert: {len(catalog.list_strategies())}\n")

    # Generate configs
    successful = []
    failed = []

    for strategy_name in sorted(catalog.list_strategies()):
        try:
            print(f"[{len(successful) + len(failed) + 1}/9] Processing: {strategy_name}")

            # Step 1: Analyze
            strategy_def = catalog.get_strategy(strategy_name)
            analysis = analyzer.analyze_strategy_definition(strategy_def)
            print(f"     ✓ Analyzed ({len(analysis.entry_conditions)} entry, "
                  f"{len(analysis.exit_conditions)} exit, "
                  f"{len(analysis.required_indicators)} indicators)")

            # Step 2: Generate JSON
            json_config = generator.generate_from_analysis(
                analysis,
                include_regime=True,
                include_strategy_set=True
            )
            print(f"     ✓ Generated JSON config")

            # Step 3: Save
            output_path = output_dir / f"{strategy_name}.json"
            generator.save_config(json_config, output_path)
            print(f"     ✓ Saved to {output_path.relative_to(Path.cwd())}\n")

            successful.append(strategy_name)

        except Exception as e:
            print(f"     ✗ FAILED: {e}\n")
            failed.append((strategy_name, str(e)))

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Successful: {len(successful)}/{len(catalog.list_strategies())}")

    if successful:
        for name in successful:
            print(f"   ✓ {name}")

    if failed:
        print(f"\n✗ Failed: {len(failed)}")
        for name, error in failed:
            print(f"   ✗ {name}: {error}")
        return 1

    print(f"\n{'=' * 70}")
    print("✅ ALL CONFIGS GENERATED SUCCESSFULLY!")
    print(f"{'=' * 70}")
    print(f"\nJSON Configs deployed to: {output_dir}")
    print("\nNext Steps:")
    print("  1. Validate configs: pytest tests/core/tradingbot/test_migration_suite.py")
    print("  2. Integrate with Bot: See docs/integration/PHASE_6_PLAN.md")
    print("  3. Test JSON-based trading: python start_orderpilot.py --strategy-config <path>")

    return 0


if __name__ == "__main__":
    sys.exit(main())
