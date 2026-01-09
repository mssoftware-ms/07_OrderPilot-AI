"""Data Loading Utils - Timezone and utility functions.

Refactored from 498 LOC monolith using composition pattern.

Module 1/6 of data_loading_mixin.py split.

Contains:
- get_local_timezone_offset_seconds(): Local timezone offset calculation
"""

from __future__ import annotations

import time


def get_local_timezone_offset_seconds() -> int:
    """Get local timezone offset in seconds (positive for east of UTC).

    This accounts for DST automatically.
    """
    # time.timezone is seconds west of UTC (negative for CET)
    # time.daylight tells if DST is observed, time.altzone is DST offset
    if time.daylight and time.localtime().tm_isdst > 0:
        return -time.altzone
    return -time.timezone
