"""Standalone Migration Tool: v1 to v2.1 JSON Format.

Migrates old strategy and indicator_set JSONs to v2.1 format WITHOUT importing the full app.

Usage:
    python migrations/migrate_standalone.py --dir 03_JSON/Trading_Bot
"""
import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def detect_kind(data: dict) -> str | None:
    """Detect kind from v1 JSON structure."""
    if "strategies" in data and "routing" in data:
        return "strategy_config"
    elif "optimization_results" in data:
        return "regime_optimization_results"
    elif "indicators" in data:
        return "indicator_set"
    return None


def migrate_to_v2(data: dict, kind: str) -> dict:
    """Migrate to v2.1 format."""
    migrated = data.copy()

    # Add/fix required fields
    migrated["kind"] = kind
    migrated["schema_version"] = "2.1.0"

    # Remove disallowed fields
    if "metadata" in migrated:
        del migrated["metadata"]

    return migrated


def migrate_file(input_path: Path) -> bool:
    """Migrate single file in-place."""
    try:
        # Load original
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check if already v2.1
        if data.get("kind") and data.get("schema_version", "").startswith("2.1."):
            logger.info(f"✅ {input_path.name} already v2.1")
            return True

        # Detect kind
        kind = detect_kind(data)
        if not kind:
            logger.error(f"❌ {input_path.name}: Cannot detect kind")
            return False

        logger.info(f"🔄 {input_path.name}: Migrating '{kind}'")

        # Migrate
        migrated = migrate_to_v2(data, kind)

        # Write back
        with open(input_path, 'w', encoding='utf-8') as f:
            json.dump(migrated, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 {input_path.name}: Saved")
        return True

    except Exception as e:
        logger.error(f"❌ {input_path.name}: {e}")
        return False


def migrate_directory(dir_path: Path) -> dict[str, int]:
    """Migrate all JSONs in directory."""
    results = {"success": 0, "skipped": 0, "failed": 0}

    json_files = list(dir_path.glob("*.json"))
    logger.info(f"\n📂 Found {len(json_files)} JSON files in {dir_path}")
    logger.info("=" * 80)

    for json_file in sorted(json_files):
        success = migrate_file(json_file)

        if success:
            results["success"] += 1
        else:
            results["failed"] += 1

    logger.info("=" * 80)
    logger.info(f"\n📊 RESULTS:")
    logger.info(f"  ✅ Migrated: {results['success']}")
    logger.info(f"  ❌ Failed:   {results['failed']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Migrate v1 JSONs to v2.1 format")
    parser.add_argument("--dir", type=Path, required=True, help="Directory to migrate")

    args = parser.parse_args()

    if not args.dir.exists():
        logger.error(f"Directory not found: {args.dir}")
        return 1

    results = migrate_directory(args.dir)
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    exit(main())
