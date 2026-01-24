#!/usr/bin/env python
"""Verification script for new Core Classes integration.

Tests:
1. Import verification
2. Feature flag check
3. Class instantiation
4. Migration status logging
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

logger = logging.getLogger(__name__)


def test_core_imports():
    """Test that all new classes can be imported."""
    logger.info("Testing Core imports...")

    try:
        from src.core import (
            RegimeOptimizer,
            RegimeOptimizationConfig,
            RegimeResultsManager,
            RegimeResult,
            IndicatorSetOptimizer,
            IndicatorOptimizationResult,
        )
        logger.info("✓ All Core imports successful")
        return True
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def test_thread_integration():
    """Test that optimization thread can import new classes."""
    logger.info("Testing Thread integration...")

    try:
        from src.ui.threads.regime_optimization_thread import (
            RegimeOptimizationThread,
            USE_OPTUNA_TPE
        )
        logger.info(f"✓ Thread integration successful (USE_OPTUNA_TPE={USE_OPTUNA_TPE})")
        return True
    except ImportError as e:
        logger.error(f"✗ Thread integration failed: {e}")
        return False


def test_feature_flag():
    """Test feature flag status."""
    logger.info("Testing Feature flag...")

    try:
        from src.ui.threads.regime_optimization_thread import USE_OPTUNA_TPE

        if USE_OPTUNA_TPE:
            logger.info("✓ Feature flag: Optuna TPE ENABLED (recommended)")
        else:
            logger.warning("⚠ Feature flag: Grid Search ENABLED (deprecated)")

        return True
    except ImportError as e:
        logger.error(f"✗ Feature flag check failed: {e}")
        return False


def test_class_instantiation():
    """Test basic class instantiation (without data)."""
    logger.info("Testing Class instantiation...")

    try:
        from src.core import RegimeResultsManager

        # Test RegimeResultsManager (no constructor params needed)
        manager = RegimeResultsManager()
        logger.info("✓ RegimeResultsManager instantiation successful")

        return True
    except Exception as e:
        logger.error(f"✗ Class instantiation failed: {e}")
        return False


def print_migration_status():
    """Print migration status summary."""
    logger.info("\n" + "="*60)
    logger.info("MIGRATION STATUS SUMMARY")
    logger.info("="*60)

    status = {
        "✅ New Classes Created": [
            "src/core/regime_optimizer.py",
            "src/core/regime_results_manager.py",
            "src/core/indicator_set_optimizer.py"
        ],
        "✅ Integration Complete": [
            "src/core/__init__.py (exports added)",
            "src/ui/threads/regime_optimization_thread.py (hybrid mode)"
        ],
        "⚠ Deprecated (Fallback)": [
            "Grid Search in regime_optimization_thread.py"
        ],
        "🔄 Next Steps": [
            "Update UI to use Optuna mode",
            "Add progress visualization for Optuna trials",
            "Remove deprecated grid search after testing",
            "Update ARCHITECTURE.md"
        ]
    }

    for category, items in status.items():
        logger.info(f"\n{category}:")
        for item in items:
            logger.info(f"  - {item}")

    logger.info("\n" + "="*60)


def main():
    """Run all verification tests."""
    logger.info("Starting Integration Verification...\n")

    tests = [
        ("Core Imports", test_core_imports),
        ("Thread Integration", test_thread_integration),
        ("Feature Flag", test_feature_flag),
        ("Class Instantiation", test_class_instantiation),
    ]

    results = []
    for name, test_func in tests:
        logger.info(f"\n--- {name} ---")
        success = test_func()
        results.append((name, success))

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("="*60)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {name}")

    all_passed = all(success for _, success in results)

    if all_passed:
        logger.info("\n✓ All verification tests PASSED")
        print_migration_status()
        return 0
    else:
        logger.error("\n✗ Some verification tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
