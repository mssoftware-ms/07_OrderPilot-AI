#!/usr/bin/env python3
"""CLI Tool for validating JSON strategy configurations.

Usage:
    python tools/validate_config.py <config_file>
    python tools/validate_config.py --all 03_JSON/Trading_Bot/configs/
    python tools/validate_config.py --schema-only <config_file>

Examples:
    # Validate single config
    python tools/validate_config.py 03_JSON/Trading_Bot/configs/production.json

    # Validate all configs in directory
    python tools/validate_config.py --all 03_JSON/Trading_Bot/configs/

    # Quick schema-only validation (skip Pydantic)
    python tools/validate_config.py --schema-only config.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add specific path to avoid triggering src.__init__
project_root = Path(__file__).parent.parent
config_module_path = project_root / "src" / "core" / "tradingbot"
sys.path.insert(0, str(config_module_path))

# Import from config module directly
from config.loader import ConfigLoader, ConfigLoadError


def validate_single_file(loader: ConfigLoader, config_path: Path, schema_only: bool = False) -> bool:
    """Validate a single config file.

    Args:
        loader: ConfigLoader instance
        config_path: Path to config file
        schema_only: Skip Pydantic validation

    Returns:
        True if valid, False otherwise
    """
    print(f"\n{'='*70}")
    print(f"Validating: {config_path}")
    print(f"{'='*70}")

    try:
        if schema_only:
            # Quick schema-only validation
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            import jsonschema
            jsonschema.validate(instance=config_data, schema=loader.schema)
            print("✅ JSON Schema validation: PASSED")
        else:
            # Full validation (schema + Pydantic)
            config = loader.load_config(config_path)
            print("✅ JSON Schema validation: PASSED")
            print("✅ Pydantic validation: PASSED")

            # Print summary
            print(f"\n📊 Config Summary:")
            print(f"   Schema Version: {config.schema_version}")
            print(f"   Indicators: {len(config.indicators)}")
            print(f"   Regimes: {len(config.regimes)}")
            print(f"   Strategies: {len(config.strategies)}")
            print(f"   Strategy Sets: {len(config.strategy_sets)}")
            print(f"   Routing Rules: {len(config.routing)}")

            if config.metadata:
                print(f"\n📝 Metadata:")
                if config.metadata.author:
                    print(f"   Author: {config.metadata.author}")
                if config.metadata.tags:
                    print(f"   Tags: {', '.join(config.metadata.tags)}")
                if config.metadata.notes:
                    print(f"   Notes: {config.metadata.notes}")

        return True

    except ConfigLoadError as e:
        print(f"❌ Validation FAILED:")
        print(f"   {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error:")
        print(f"   {type(e).__name__}: {e}")
        return False


def validate_directory(loader: ConfigLoader, directory: Path, schema_only: bool = False) -> tuple[int, int]:
    """Validate all configs in directory.

    Args:
        loader: ConfigLoader instance
        directory: Directory containing configs
        schema_only: Skip Pydantic validation

    Returns:
        Tuple of (valid_count, total_count)
    """
    try:
        json_files = loader.list_configs(directory)
    except ConfigLoadError as e:
        print(f"❌ Error listing configs: {e}")
        return 0, 0

    if not json_files:
        print(f"⚠️  No JSON files found in {directory}")
        return 0, 0

    print(f"\n{'='*70}")
    print(f"Found {len(json_files)} JSON files in {directory}")
    print(f"{'='*70}")

    results = []
    for config_path in json_files:
        is_valid = validate_single_file(loader, config_path, schema_only)
        results.append((config_path.name, is_valid))

    # Summary
    valid_count = sum(1 for _, is_valid in results if is_valid)
    total_count = len(results)

    print(f"\n{'='*70}")
    print(f"SUMMARY: {valid_count}/{total_count} configs valid")
    print(f"{'='*70}")

    for filename, is_valid in results:
        status = "✅ VALID" if is_valid else "❌ INVALID"
        print(f"  {status:12} {filename}")

    return valid_count, total_count


def main():
    parser = argparse.ArgumentParser(
        description="Validate JSON strategy configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "config_path",
        type=str,
        help="Path to config file or directory"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all JSON files in directory"
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Skip Pydantic validation (faster)"
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="03_JSON/schema/strategy_config_schema.json",
        help="Path to JSON Schema file (default: 03_JSON/schema/strategy_config_schema.json)"
    )

    args = parser.parse_args()

    # Initialize loader
    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"❌ JSON Schema not found: {schema_path}")
        print(f"   Run Phase 0 setup to create schema file.")
        sys.exit(1)

    try:
        loader = ConfigLoader(schema_path)
    except ConfigLoadError as e:
        print(f"❌ Failed to initialize ConfigLoader: {e}")
        sys.exit(1)

    config_path = Path(args.config_path)

    # Validate
    if args.all:
        # Validate directory
        valid_count, total_count = validate_directory(loader, config_path, args.schema_only)
        sys.exit(0 if valid_count == total_count else 1)
    else:
        # Validate single file
        is_valid = validate_single_file(loader, config_path, args.schema_only)
        sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
