"""Entry Signal Generation Module.

Generates LONG (green) and SHORT (red) entry signals
based on feature analysis and regime detection.

Now includes entry_signal_engine with ATR-normalized features
and robust regime detection for better performance on 1m/5m timeframes.

Issue #28: Added params_loader for JSON-based parameter loading.
"""

from __future__ import annotations

from .entry_signal_engine import (
    OptimParams,
    RegimeType,
    EntrySide,
    EntryEvent,
    calculate_features,
    detect_regime,
    generate_entries,
    debug_summary,
)
from .params_loader import (
    load_optim_params_from_json,
    get_default_json_path,
)

__all__ = [
    "OptimParams",
    "RegimeType",
    "EntrySide",
    "EntryEvent",
    "calculate_features",
    "detect_regime",
    "generate_entries",
    "debug_summary",
    "load_optim_params_from_json",
    "get_default_json_path",
]
