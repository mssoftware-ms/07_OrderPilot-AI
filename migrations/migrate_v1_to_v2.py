"""Migration Tool: v1 to v2.1 JSON Format.

Migrates old strategy and indicator_set JSONs to v2.1 format:
- Adds `kind` field
- Adds `schema_version` field
- Standardized structure
- Validates output against schema

Usage:
    python migrations/migrate_v1_to_v2.py --input path/to/old.json --output path/to/new.json
    python migrations/migrate_v1_to_v2.py --dir 03_JSON/Trading_Bot --dry-run
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.tradingbot.config.kind_loader import KindConfigLoader
from src.core.tradingbot.config.validator import ValidationError

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def detect_kind(data: dict) -> str | None:
    """Detect kind from v1 JSON structure."""
    if "strategies" in data:
        return "strategy_config"
    elif "indicators" in data and "optimization_results" not in data:
        return "indicator_set"
    elif "optimization_results" in data:
        return "regime_optimization_results"
    return None


def migrate_strategy_config(data: dict) -> dict:
    """Migrate strategy_config to v2.1."""
    migrated = data.copy()

    # Add required fields
    migrated["kind"] = "strategy_config"
    migrated["schema_version"] = "2.1.0"

    # Ensure strategies is list
    if "strategies" in migrated and not isinstance(migrated["strategies"], list):
        migrated["strategies"] = [migrated["strategies"]]

    # Standardize indicators
    if "indicators" in migrated:
        indicators = migrated["indicators"]
        if isinstance(indicators, dict):
            # Convert dict to list format
            migrated["indicators"] = [
                {"name": k, **v} for k, v in indicators.items()
            ]

    return migrated


def migrate_indicator_set(data: dict) -> dict:
    """Migrate indicator_set to v2.1."""
    migrated = data.copy()

    # Add required fields
    migrated["kind"] = "indicator_set"
    migrated["schema_version"] = "2.1.0"

    # Ensure indicators is list
    if "indicators" in migrated and isinstance(migrated["indicators"], dict):
        migrated["indicators"] = [
            {"name": k, **v} for k, v in migrated["indicators"].items()
        ]

    return migrated


def migrate_regime_optimization_results(data: dict) -> dict:
    """Migrate regime_optimization_results to v2.1."""
    migrated = data.copy()

    # Add required fields
    migrated["kind"] = "regime_optimization_results"
    migrated["schema_version"] = "2.1.0"

    return migrated


def migrate_file(input_path: Path, output_path: Path, dry_run: bool = False) -> bool:
    """Migrate single file from v1 to v2.1.

    Args:
        input_path: Path to v1 JSON
        output_path: Path for v2.1 JSON
        dry_run: If True, don't write output

    Returns:
        True if migration successful, False otherwise
    """
    try:
        # Load original
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if already v2.1
        if "kind" in data and "schema_version" in data:
            logger.info(f"✅ {input_path.name} already v2.1 (skipping)")
            return True

        # Detect kind
        kind = detect_kind(data)
        if not kind:
            logger.error(f"❌ {input_path.name}: Cannot detect kind")
            return False

        logger.info(f"🔄 {input_path.name}: Detected as '{kind}'")

        # Migrate based on kind
        if kind == "strategy_config":
            migrated = migrate_strategy_config(data)
        elif kind == "indicator_set":
            migrated = migrate_indicator_set(data)
        elif kind == "regime_optimization_results":
            migrated = migrate_regime_optimization_results(data)
        else:
            logger.error(f"❌ {input_path.name}: Unknown kind '{kind}'")
            return False

        # Validate migrated JSON
        try:
            loader = KindConfigLoader()
            # Write to temp file for validation
            temp_path = output_path.parent / f".temp_{output_path.name}"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(migrated, f, indent=2, ensure_ascii=False)

            loader.load(temp_path)
            temp_path.unlink()  # Clean up temp file

            logger.info(f"✅ {input_path.name}: Validation passed")

        except ValidationError as e:
            logger.error(f"❌ {input_path.name}: Validation failed: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return False

        # Write output (if not dry-run)
        if not dry_run:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(migrated, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 {input_path.name} → {output_path.name}")
        else:
            logger.info(f"🔍 DRY RUN: Would write to {output_path.name}")

        return True

    except Exception as e:
        logger.error(f"❌ {input_path.name}: {e}")
        return False


def migrate_directory(dir_path: Path, dry_run: bool = False) -> dict[str, int]:
    """Migrate all JSONs in directory.

    Args:
        dir_path: Directory containing v1 JSONs
        dry_run: If True, don't write outputs

    Returns:
        Dict with counts: success, skipped, failed
    """
    results = {"success": 0, "skipped": 0, "failed": 0}

    json_files = list(dir_path.glob("*.json"))
    logger.info(f"\n📂 Found {len(json_files)} JSON files in {dir_path}")
    logger.info("=" * 80)

    for json_file in sorted(json_files):
        # Create output path (same name, or .v2.1.json suffix in dry-run)
        if dry_run:
            output_path = json_file.parent / f"{json_file.stem}.v2.1.json"
        else:
            output_path = json_file

        success = migrate_file(json_file, output_path, dry_run)

        if success:
            if "already v2.1" in str(success):
                results["skipped"] += 1
            else:
                results["success"] += 1
        else:
            results["failed"] += 1

    logger.info("=" * 80)
    logger.info(f"\n📊 RESULTS:")
    logger.info(f"  ✅ Migrated: {results['success']}")
    logger.info(f"  ⏭️  Skipped:  {results['skipped']}")
    logger.info(f"  ❌ Failed:   {results['failed']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Migrate v1 JSONs to v2.1 format")
    parser.add_argument("--input", type=Path, help="Input JSON file")
    parser.add_argument("--output", type=Path, help="Output JSON file")
    parser.add_argument("--dir", type=Path, help="Directory to migrate all JSONs")
    parser.add_argument("--dry-run", action="store_true", help="Don't write outputs, just validate")

    args = parser.parse_args()

    if args.input and args.output:
        # Single file mode
        success = migrate_file(args.input, args.output, args.dry_run)
        sys.exit(0 if success else 1)

    elif args.dir:
        # Directory mode
        results = migrate_directory(args.dir, args.dry_run)
        sys.exit(0 if results["failed"] == 0 else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
