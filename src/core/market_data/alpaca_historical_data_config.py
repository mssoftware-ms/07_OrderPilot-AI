"""Historical Data Configuration - Filter and Stats Dataclasses.

Configuration for bad tick filtering and statistics tracking.

Module 1/4 of historical_data_manager.py split (Lines 18-50).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FilterConfig:
    """Configuration for bad tick filtering.

    Attributes:
        enabled: Enable/disable filtering
        method: Detection method ("hampel", "zscore", "basic")
        cleaning_mode: How to handle bad ticks ("interpolate", "remove", "forward_fill")
        hampel_window: Window size for Hampel filter
        hampel_threshold: Threshold for Hampel filter (MAD multiples)
        zscore_threshold: Z-score threshold for outlier detection
        volume_multiplier: Volume spike threshold multiplier
        log_stats: Log filtering statistics
    """

    enabled: bool = True
    method: str = "hampel"  # "hampel", "zscore", or "basic"
    cleaning_mode: str = "interpolate"  # "interpolate", "remove", "forward_fill"
    hampel_window: int = 15
    hampel_threshold: float = 3.5
    zscore_threshold: float = 4.0
    volume_multiplier: float = 10.0
    log_stats: bool = True


@dataclass
class FilterStats:
    """Statistics from bad tick filtering operation.

    Attributes:
        total_bars: Total number of bars processed
        bad_ticks_found: Number of bad ticks detected
        bad_ticks_interpolated: Number interpolated
        bad_ticks_removed: Number removed
        filtering_percentage: Percentage of data affected
        bad_tick_types: Breakdown by detection type
    """

    total_bars: int = 0
    bad_ticks_found: int = 0
    bad_ticks_interpolated: int = 0
    bad_ticks_removed: int = 0
    filtering_percentage: float = 0.0
    bad_tick_types: dict = field(default_factory=dict)
