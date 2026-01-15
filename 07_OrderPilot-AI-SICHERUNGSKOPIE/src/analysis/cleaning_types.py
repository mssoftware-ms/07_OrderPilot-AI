"""Data Cleaning Types - CleaningStats Dataclass.

Module 1/6 of data_cleaning.py split (Lines 25-31).
"""

from dataclasses import dataclass


@dataclass
class CleaningStats:
    """Statistics from data cleaning operation.

    Attributes:
        total_bars: Total number of bars processed
        bad_ticks_removed: Number of bad ticks removed/replaced
        bad_tick_types: Breakdown by detection type
        cleaning_percentage: Percentage of data cleaned
    """

    total_bars: int
    bad_ticks_removed: int
    bad_tick_types: dict[str, int]
    cleaning_percentage: float
