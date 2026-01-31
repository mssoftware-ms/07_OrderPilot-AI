"""Entry Signal Generation Module.

Generates LONG (green) and SHORT (red) entry signals
based on feature analysis and regime detection.

Now includes entry_signal_engine with ATR-normalized features
and robust regime detection for better performance on 1m/5m timeframes.

Issue #28: Added params_loader for JSON-based parameter loading.

**REFACTORED v2.0**: Entry signal engine split into modular components:
- entry_signal_engine_core.py: Core types and feature calculation
- entry_signal_engine_indicators.py: Technical indicator functions
- entry_signal_engine_regime.py: Regime detection logic
- generators/: Regime-specific entry generators

Backward compatibility maintained via re-exports.
"""

from __future__ import annotations

from .entry_signal_engine import (
    EntryEvent,
    EntrySide,
    OptimParams,
    RegimeType,
    calculate_features,
    debug_summary,
    detect_regime,
    detect_regime_v2,
    generate_entries,
)
from .params_loader import get_default_json_path, load_optim_params_from_json

__all__ = [
    # Core types
    "OptimParams",
    "RegimeType",
    "EntrySide",
    "EntryEvent",
    # Feature calculation
    "calculate_features",
    # Regime detection
    "detect_regime",
    "detect_regime_v2",
    # Entry generation
    "generate_entries",
    # Debug utilities
    "debug_summary",
    # Parameter loading
    "load_optim_params_from_json",
    "get_default_json_path",
]
