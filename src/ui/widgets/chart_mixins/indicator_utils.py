"""Indicator Utils - Utilities, dataclass, and configs.

Refactored from 676 LOC monolith using composition pattern.

Module 1/7 of indicator_mixin.py split.

Contains:
- _ts_to_local_unix(): Timestamp conversion utility
- IndicatorInstance: Dataclass for instance management
- get_indicator_configs(): Get overlay/oscillator configs
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.indicators.engine import IndicatorType

from src.core.indicators.registry import get_overlay_configs, get_oscillator_configs


def _ts_to_local_unix(ts) -> int:
    """Convert timestamp to Unix seconds (UTC).

    Handles both timezone-aware and naive datetimes.
    Naive datetimes are interpreted as UTC.
    """
    from datetime import timezone
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return int(ts.timestamp())


@dataclass
class IndicatorInstance:
    """Instance of an indicator (multi-add support)."""
    instance_id: str
    ind_id: str
    ind_type: "IndicatorType"
    params: dict
    display_name: str
    is_overlay: bool
    color: str
    min_val: float | None
    max_val: float | None


def get_indicator_configs():
    """Get indicator configuration dictionaries.

    Returns:
        Tuple of (overlay_configs, oscillator_configs)
    """
    return get_overlay_configs(), get_oscillator_configs()
