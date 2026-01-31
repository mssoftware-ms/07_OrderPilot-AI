"""Entry Signal Engine with ATR-normalized features and robust regime detection.

This module provides a complete replacement for the simplistic SMA-based entry detection.

**REFACTORED**: This module now delegates to specialized submodules:
- entry_signal_engine_core.py: Types, feature calculation, entry generation
- entry_signal_engine_indicators.py: Technical indicator calculations
- entry_signal_engine_regime.py: Regime detection logic
- generators/: Regime-specific entry generators

Backward compatibility is maintained via re-exports in this module.
"""

from __future__ import annotations

# Re-export all public APIs for backward compatibility
from .entry_signal_engine_core import (
    EntryEvent,
    EntrySide,
    OptimParams,
    RegimeType,
    calculate_features,
    debug_summary,
    generate_entries,
)
from .entry_signal_engine_regime import detect_regime, detect_regime_v2

__all__ = [
    # Types
    "RegimeType",
    "EntrySide",
    "EntryEvent",
    "OptimParams",
    # Feature calculation
    "calculate_features",
    # Regime detection
    "detect_regime",
    "detect_regime_v2",
    # Entry generation
    "generate_entries",
    # Debug utilities
    "debug_summary",
]
