"""
MarketContext - Single Source of Truth für alle Analyse-Konsumenten.

Dieses Modul definiert das kanonische Datenmodell, das von:
- Trading-Engine (Auto-Trade)
- AI Analyse Popup (Overview/Deep)
- Chatbot (Q&A + Chart-Zeichnung)

identisch verwendet wird.

Phase 1 der Bot-Integration: Canonical MarketContext.

Refactored from 868 LOC monolith using composition pattern.

Module 8/8 of market_context.py split (Main Re-Export Module).
"""

from __future__ import annotations

# Re-export all enums
from .market_context_enums import (
    LevelStrength,
    LevelType,
    RegimeType,
    SetupType,
    SignalStrength,
    TrendDirection,
)

# Re-export all dataclasses
from .market_context_candles import CandleSummary
from .market_context_indicators import IndicatorSnapshot
from .market_context_levels import Level, LevelsSnapshot
from .market_context_signals import SignalSnapshot
from .market_context_main import MarketContext

# Re-export factory functions
from .market_context_factories import (
    create_empty_context,
    create_indicator_snapshot_from_df,
)

__all__ = [
    # Enums
    "RegimeType",
    "TrendDirection",
    "LevelType",
    "LevelStrength",
    "SignalStrength",
    "SetupType",
    # Dataclasses
    "CandleSummary",
    "IndicatorSnapshot",
    "Level",
    "LevelsSnapshot",
    "SignalSnapshot",
    "MarketContext",
    # Factory Functions
    "create_empty_context",
    "create_indicator_snapshot_from_df",
]
