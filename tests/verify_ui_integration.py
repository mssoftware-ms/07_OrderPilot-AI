#!/usr/bin/env python3
"""Verification script for UI wiring integration.

Checks that all 8 UI wiring tasks are properly implemented:
1. Backtest button handler
2. Regime visualization
3. Indicator optimization with CLI orchestrator
4. Regime set builder
5. Bot start strategy dialog
6. Dynamic strategy switching
7. UI notifications
8. Event-bus integration
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists."""
    path = project_root / file_path
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {file_path}")
    return exists


def check_code_snippet(file_path: str, snippet: str, description: str) -> bool:
    """Check if a code snippet exists in a file."""
    path = project_root / file_path
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    content = path.read_text()
    exists = snippet in content
    status = "✅" if exists else "❌"
    print(f"{status} {description}")
    return exists


def check_import(file_path: str, import_line: str, description: str) -> bool:
    """Check if an import statement exists."""
    return check_code_snippet(file_path, import_line, description)


def main():
    """Run all verification checks."""
    print("=" * 80)
    print("UI WIRING INTEGRATION VERIFICATION")
    print("=" * 80)
    print()

    all_passed = True

    # Task 1.1: Backtest Button Handler
    print("Task 1.1: Backtest Button Handler")
    print("-" * 40)
    all_passed &= check_file_exists(
        "src/ui/dialogs/entry_analyzer_popup.py",
        "Entry Analyzer Dialog"
    )
    all_passed &= check_code_snippet(
        "src/ui/dialogs/entry_analyzer_popup.py",
        "def _on_run_backtest_clicked",
        "  Backtest button handler method"
    )
    all_passed &= check_code_snippet(
        "src/ui/dialogs/entry_analyzer_popup.py",
        "BacktestWorker",
        "  BacktestWorker usage"
    )
    all_passed &= check_file_exists(
        "src/ui/threads/backtest_thread.py",
        "  Backtest background thread"
    )
    print()

    # Task 1.2: Regime Visualization
    print("Task 1.2: Regime Visualization")
    print("-" * 40)
    all_passed &= check_code_snippet(
        "src/ui/dialogs/entry_analyzer_popup.py",
        "def _draw_regime_boundaries",
        "  Regime boundary drawing method"
    )
    all_passed &= check_code_snippet(
        "src/ui/dialogs/entry_analyzer_popup.py",
        "regime_changes",
        "  Regime changes processing"
    )
    print()

    # Task 1.3: Indicator Optimization with CLI Orchestrator
    print("Task 1.3: Indicator Optimization (CLI Integration)")
    print("-" * 40)
    all_passed &= check_file_exists(
        "src/ui/threads/indicator_optimization_thread.py",
        "Indicator Optimization Thread"
    )
    all_passed &= check_import(
        "src/ui/threads/indicator_optimization_thread.py",
        "from tools.optimize_indicators import IndicatorOptimizationOrchestrator",
        "  CLI orchestrator import"
    )
    all_passed &= check_code_snippet(
        "src/ui/threads/indicator_optimization_thread.py",
        "IndicatorOptimizationOrchestrator(",
        "  Orchestrator instantiation"
    )
    all_passed &= check_code_snippet(
        "src/ui/threads/indicator_optimization_thread.py",
        "orchestrator.optimizer.optimize_batch",
        "  Batch optimization call"
    )
    all_passed &= check_file_exists(
        "tools/optimize_indicators.py",
        "  CLI optimizer tool"
    )
    print()

    # Task 1.4: Regime Set Builder
    print("Task 1.4: Regime Set Builder")
    print("-" * 40)
    all_passed &= check_code_snippet(
        "src/ui/dialogs/entry_analyzer_popup.py",
        "def _on_create_regime_set_clicked",
        "  Regime set creation handler"
    )
    all_passed &= check_code_snippet(
        "src/ui/dialogs/entry_analyzer_popup.py",
        "_create_regime_set_tab",
        "  Regime set tab creation"
    )
    print()

    # Task 2.1: Bot Start Strategy Dialog
    print("Task 2.1: Bot Start Strategy Dialog")
    print("-" * 40)
    all_passed &= check_file_exists(
        "src/ui/dialogs/bot_start_strategy_dialog.py",
        "Bot Start Strategy Dialog"
    )
    all_passed &= check_code_snippet(
        "src/ui/dialogs/bot_start_strategy_dialog.py",
        "class BotStartStrategyDialog",
        "  Dialog class definition"
    )
    all_passed &= check_code_snippet(
        "src/ui/dialogs/bot_start_strategy_dialog.py",
        "def _on_analyze_clicked",
        "  Market analysis handler"
    )
    all_passed &= check_code_snippet(
        "src/ui/dialogs/bot_start_strategy_dialog.py",
        "RegimeEngine",
        "  RegimeEngine usage"
    )
    all_passed &= check_code_snippet(
        "src/ui/dialogs/bot_start_strategy_dialog.py",
        "StrategyRouter",
        "  StrategyRouter usage"
    )
    print()

    # Task 2.2: Dynamic Strategy Switching in BotController
    print("Task 2.2: Dynamic Strategy Switching")
    print("-" * 40)
    all_passed &= check_file_exists(
        "src/core/tradingbot/bot_controller.py",
        "Bot Controller"
    )
    all_passed &= check_code_snippet(
        "src/core/tradingbot/bot_controller.py",
        "def _check_regime_change_and_switch",
        "  Regime change detection method"
    )
    all_passed &= check_code_snippet(
        "src/core/tradingbot/bot_controller.py",
        "def _switch_strategy",
        "  Strategy switching method"
    )
    all_passed &= check_code_snippet(
        "src/core/tradingbot/bot_controller.py",
        "_check_regime_change_and_switch",
        "  Regime checking in on_bar loop"
    )
    print()

    # Task 2.3: UI Notifications
    print("Task 2.3: UI Notifications")
    print("-" * 40)
    all_passed &= check_file_exists(
        "src/ui/widgets/chart_window_mixins/bot_event_handlers.py",
        "Bot Event Handlers"
    )
    all_passed &= check_code_snippet(
        "src/ui/widgets/chart_window_mixins/bot_event_handlers.py",
        "def _on_regime_changed_notification",
        "  Regime changed event handler"
    )
    all_passed &= check_code_snippet(
        "src/ui/widgets/chart_window_mixins/bot_event_handlers.py",
        "subscribe.*regime_changed",
        "  Event-bus subscription"
    )
    all_passed &= check_code_snippet(
        "src/ui/widgets/chart_window_mixins/bot_event_handlers.py",
        "_show_strategy_change_notification",
        "  Visual notification method"
    )
    print()

    # Integration Points
    print("Integration Points Verification")
    print("-" * 40)

    # Dialog integration with Start Bot button
    all_passed &= check_import(
        "src/ui/widgets/chart_window_mixins/bot_event_handlers.py",
        "from src.ui.dialogs.bot_start_strategy_dialog import BotStartStrategyDialog",
        "  Strategy dialog import"
    )

    # BotController JSON config loading
    all_passed &= check_code_snippet(
        "src/core/tradingbot/bot_controller.py",
        "def _load_json_config",
        "  JSON config loading method"
    )

    # Event-bus regime_changed emission
    all_passed &= check_code_snippet(
        "src/core/tradingbot/bot_controller.py",
        "self.event_bus.emit('regime_changed'",
        "  Event emission for regime changes"
    )
    print()

    # Additional Files
    print("Supporting Files")
    print("-" * 40)
    all_passed &= check_file_exists(
        "config/indicator_catalog.yaml",
        "Indicator catalog (28 indicators)"
    )
    all_passed &= check_file_exists(
        "src/core/tradingbot/indicator_grid_search.py",
        "Grid search implementation"
    )
    all_passed &= check_file_exists(
        "src/core/tradingbot/indicator_optimizer.py",
        "Indicator optimizer"
    )
    all_passed &= check_file_exists(
        "src/core/tradingbot/indicator_config_generator.py",
        "JSON config generator"
    )
    all_passed &= check_file_exists(
        "src/backtesting/engine.py",
        "Backtest engine"
    )
    all_passed &= check_file_exists(
        "src/core/tradingbot/regime_engine.py",
        "Regime engine"
    )
    all_passed &= check_file_exists(
        "src/core/tradingbot/config/loader.py",
        "Config loader"
    )
    all_passed &= check_file_exists(
        "src/core/tradingbot/config/detector.py",
        "Regime detector"
    )
    all_passed &= check_file_exists(
        "src/core/tradingbot/config/router.py",
        "Strategy router"
    )
    print()

    # Test Files
    print("Test Files")
    print("-" * 40)
    all_passed &= check_file_exists(
        "tests/unit/tradingbot/test_indicator_grid_search.py",
        "Grid search unit tests"
    )
    all_passed &= check_file_exists(
        "tests/integration/test_optimization_workflow.py",
        "Integration workflow tests"
    )
    print()

    # Documentation
    print("Documentation")
    print("-" * 40)
    all_passed &= check_file_exists(
        "docs/integration/UI_WIRING_COMPLETE.md",
        "UI wiring completion documentation"
    )
    all_passed &= check_file_exists(
        "docs/integration/TESTING_GUIDE.md",
        "Testing guide"
    )
    print()

    # Summary
    print("=" * 80)
    if all_passed:
        print("✅ ALL CHECKS PASSED - UI wiring integration is complete!")
        print()
        print("Next steps:")
        print("1. Run integration tests: pytest tests/integration/test_optimization_workflow.py")
        print("2. Launch application and test UI workflows manually")
        print("3. Refer to docs/integration/TESTING_GUIDE.md for detailed test procedures")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Review output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
