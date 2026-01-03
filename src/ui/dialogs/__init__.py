"""UI Dialogs Package for OrderPilot-AI Trading Application.

Imports are guarded so that optional dependencies (e.g. qasync) do not
break unrelated dialogs like the Pattern Database manager.
"""

AIBacktestDialog = None
BacktestDialog = None
ChartMarkingsManagerDialog = None
LayoutManagerDialog = None
OrderDialog = None
ParameterOptimizationDialog = None
PatternDatabaseDialog = None
SettingsDialog = None
ZoneEditDialog = None

try:
    from .ai_backtest_dialog import AIBacktestDialog  # noqa: F401
except Exception:
    pass

try:
    from .backtest_dialog import BacktestDialog  # noqa: F401
except Exception:
    pass

try:
    from .chart_markings_manager_dialog import ChartMarkingsManagerDialog  # noqa: F401
except Exception:
    pass

try:
    from .layout_manager_dialog import LayoutManagerDialog  # noqa: F401
except Exception:
    pass

try:
    from .order_dialog import OrderDialog  # noqa: F401
except Exception:
    pass

try:
    from .parameter_optimization_dialog import ParameterOptimizationDialog  # noqa: F401
except Exception:
    pass

try:
    from .pattern_db_dialog import PatternDatabaseDialog  # noqa: F401
except Exception:
    pass

try:
    from .settings_dialog import SettingsDialog  # noqa: F401
except Exception:
    pass

try:
    from .zone_edit_dialog import ZoneEditDialog  # noqa: F401
except Exception:
    pass

__all__ = [
    "AIBacktestDialog",
    "BacktestDialog",
    "ChartMarkingsManagerDialog",
    "LayoutManagerDialog",
    "OrderDialog",
    "ParameterOptimizationDialog",
    "PatternDatabaseDialog",
    "SettingsDialog",
    "ZoneEditDialog",
]
