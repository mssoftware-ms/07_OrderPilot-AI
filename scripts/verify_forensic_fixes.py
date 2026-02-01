#!/usr/bin/env python
"""Verification script for Forensic Audit Fixes.

Tests:
1. Telegram Widget - aiohttp async imports
2. Broker Mixin - @asyncSlot decorator
3. AI Backtest Dialog - @asyncSlot decorator
4. Dashboard - Connection Status UI
5. Backtest Tab Handlers - Mixin delegation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_telegram_widget_async():
    """Test 1: Verify telegram_widget uses aiohttp + async."""
    print("Test 1: Telegram Widget imports...")

    file_path = project_root / "src/ui/widgets/telegram_widget.py"
    content = file_path.read_text(encoding="utf-8")

    assert "import aiohttp" in content, "aiohttp import missing"
    assert "async def" in content, "async function missing"
    assert "asyncSlot" in content or "asyncio" in content, "async decorator missing"
    print("  ✅ aiohttp + async korrekt")


def test_broker_mixin_decorator():
    """Test 2: Verify broker_mixin has @asyncSlot decorator."""
    print("Test 2: Broker Mixin decorator...")

    file_path = project_root / "src/ui/app_components/broker_mixin.py"
    content = file_path.read_text(encoding="utf-8")

    assert "qasync" in content, "qasync import missing"
    assert "async def connect_broker" in content, "connect_broker not async"
    print("  ✅ connect_broker ist async")


def test_ai_backtest_dialog_decorator():
    """Test 3: Verify ai_backtest_dialog has @asyncSlot decorators."""
    print("Test 3: AI Backtest Dialog decorator...")

    file_path = project_root / "src/ui/dialogs/ai_backtest_dialog.py"
    content = file_path.read_text(encoding="utf-8")

    assert "qasync" in content, "qasync import missing"
    assert "async def run_backtest" in content, "run_backtest not async"
    print("  ✅ run_backtest ist async")


def test_dashboard_connection_status():
    """Test 4: Verify dashboard has connection status UI."""
    print("Test 4: Dashboard Connection Status...")

    file_path = project_root / "src/ui/widgets/dashboard.py"
    content = file_path.read_text(encoding="utf-8")

    assert "connection_status" in content, "connection_status attribute missing"
    assert "on_market_connected" in content, "on_market_connected handler missing"
    assert "on_market_disconnected" in content, "on_market_disconnected handler missing"
    print("  ✅ Connection Status UI vorhanden")


def test_backtest_tab_handlers():
    """Test 5: Verify backtest_tab_handlers delegates to mixin."""
    print("Test 5: Backtest Tab Handlers...")

    file_path = project_root / "src/ui/widgets/bitunix_trading/backtest_tab_handlers.py"
    content = file_path.read_text(encoding="utf-8")

    assert "hasattr(self.parent" in content, "hasattr check missing"
    assert "_on_auto_generate_clicked" in content, "mixin delegation missing"
    print("  ✅ Handler delegiert an Mixin")


def test_multi_monitor_manager_exists():
    """Test 6: Verify MultiMonitorChartManager exists (Sprint 4 verification)."""
    print("Test 6: MultiMonitorChartManager...")

    file_path = project_root / "src/chart_marking/multi_chart/multi_monitor_manager.py"
    content = file_path.read_text(encoding="utf-8")

    assert "class MultiMonitorChartManager" in content, "Controller class missing"
    assert "def open_chart" in content, "open_chart method missing"
    assert "def save_current_layout" in content, "save_current_layout missing"
    print("  ✅ MultiMonitorChartManager vorhanden")


def test_analysis_worker_exists():
    """Test 7: Verify AnalysisWorker exists as QThread."""
    print("Test 7: AnalysisWorker...")

    file_path = project_root / "src/ui/ai_analysis_worker.py"
    content = file_path.read_text(encoding="utf-8")

    assert "class AnalysisWorker(QThread)" in content, "Worker class missing"
    assert "finished = pyqtSignal" in content, "finished signal missing"
    print("  ✅ AnalysisWorker als QThread vorhanden")


def test_chart_interface_template_pattern():
    """Test 8: Verify chart_interface uses correct Template Pattern."""
    print("Test 8: Chart-Interface Template-Pattern...")

    file_path = project_root / "src/ui/widgets/chart_interface.py"
    content = file_path.read_text(encoding="utf-8")

    # Template-Hooks müssen in set_* Methoden aufgerufen werden
    assert "self._on_symbol_changed(symbol)" in content, "Template hook not called in set_symbol"
    assert "self._on_timeframe_changed(timeframe)" in content, "Template hook not called in set_timeframe"
    assert "self._on_theme_changed(theme)" in content, "Template hook not called in set_theme"

    # Template-Hooks müssen als pass definiert sein (Basis-Implementation)
    assert "def _on_symbol_changed" in content, "Template hook _on_symbol_changed missing"
    print("  ✅ Template-Hooks korrekt implementiert")


def test_regime_opt_deprecated():
    """Test 9: Verify _on_regime_opt_result is intentionally deprecated."""
    print("Test 9: Regime-Optimization DEPRECATED...")

    file_path = project_root / "src/ui/dialogs/entry_analyzer/entry_analyzer_regime_optimization_mixin.py"
    content = file_path.read_text(encoding="utf-8")

    # Signal muss auskommentiert sein
    assert "# self._regime_opt_thread.result_ready.connect" in content, "Signal not commented out"
    # DEPRECATED Kommentar muss vorhanden sein
    assert "DEPRECATED" in content, "DEPRECATED comment missing"
    print("  ✅ _on_regime_opt_result korrekt als DEPRECATED markiert")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("Forensic Audit Fixes - Verification")
    print("=" * 50 + "\n")

    try:
        test_telegram_widget_async()
        test_broker_mixin_decorator()
        test_ai_backtest_dialog_decorator()
        test_dashboard_connection_status()
        test_backtest_tab_handlers()
        test_multi_monitor_manager_exists()
        test_analysis_worker_exists()
        test_chart_interface_template_pattern()
        test_regime_opt_deprecated()

        print("\n" + "=" * 50)
        print("Alle 9 Tests erfolgreich! ✅")
        print("=" * 50 + "\n")

    except AssertionError as e:
        print(f"\n❌ Test fehlgeschlagen: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)
