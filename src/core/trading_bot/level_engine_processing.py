"""Level Engine Processing - Merge, Strength, Classify, Select.

Refactored from 797 LOC monolith using composition pattern.

Module 3/4 of level_engine.py split.

Contains:
- _merge_overlapping_levels(): Merges nearby levels
- _calculate_level_strength(): Calculates strength based on touches
- _classify_levels(): Classifies as Support/Resistance
- _select_top_levels(): Filters to most important levels
"""

from __future__ import annotations

import pandas as pd
from typing import List

from src.core.trading_bot.level_engine_state import (
    Level,
    LevelStrength,
    LevelType,
)


class LevelEngineProcessing:
    """Helper für Level Processing (Merge, Strength, Classify, Select)."""

    def __init__(self, parent):
        """
        Args:
            parent: LevelEngine Instanz
        """
        self.parent = parent

    def merge_overlapping_levels(self, levels: List[Level]) -> List[Level]:
        """Merged überlappende Levels."""
        if len(levels) < 2:
            return levels

        # Sort by price
        levels = sorted(levels, key=lambda l: l.price_mid)
        merged = [levels[0]]

        for current in levels[1:]:
            last = merged[-1]

            # Check if overlapping or very close
            threshold = last.price_mid * (self.parent.config.proximity_merge_pct / 100)
            if current.price_low <= last.price_high + threshold:
                # Merge: expand zone, keep stronger method/type
                new_low = min(last.price_low, current.price_low)
                new_high = max(last.price_high, current.price_high)
                new_touches = last.touches + current.touches

                # Keep stronger level type
                strength_order = {
                    LevelStrength.KEY: 4,
                    LevelStrength.STRONG: 3,
                    LevelStrength.MODERATE: 2,
                    LevelStrength.WEAK: 1,
                }
                if strength_order.get(current.strength, 0) > strength_order.get(
                    last.strength, 0
                ):
                    last.strength = current.strength

                last.price_low = new_low
                last.price_high = new_high
                last.touches = new_touches
            else:
                merged.append(current)

        return merged

    def calculate_level_strength(
        self,
        levels: List[Level],
        df: pd.DataFrame,
    ) -> List[Level]:
        """Berechnet Stärke basierend auf Touches."""
        for level in levels:
            # Count how many times price touched this zone
            touches = 0
            for _, row in df.iterrows():
                if level.contains_price(row["high"]) or level.contains_price(
                    row["low"]
                ):
                    touches += 1

            level.touches = max(level.touches, touches)

            # Determine strength
            if level.touches >= self.parent.config.key_touch_threshold:
                level.strength = LevelStrength.KEY
            elif level.touches >= self.parent.config.strong_touch_threshold:
                level.strength = LevelStrength.STRONG
            elif level.touches >= 2:
                level.strength = LevelStrength.MODERATE
            else:
                level.strength = LevelStrength.WEAK

        return levels

    def classify_levels(
        self,
        levels: List[Level],
        current_price: float,
    ) -> List[Level]:
        """Klassifiziert Levels als Support oder Resistance."""
        for level in levels:
            # Skip already classified pivot levels
            if level.level_type in (
                LevelType.PIVOT,
                LevelType.DAILY_HIGH,
                LevelType.DAILY_LOW,
                LevelType.WEEKLY_HIGH,
                LevelType.WEEKLY_LOW,
                LevelType.VWAP,
            ):
                continue

            if level.price_mid < current_price:
                level.level_type = LevelType.SUPPORT
            else:
                level.level_type = LevelType.RESISTANCE

        return levels

    def select_top_levels(
        self,
        levels: List[Level],
        current_price: float,
    ) -> List[Level]:
        """Wählt die wichtigsten Levels aus."""
        # Separate supports and resistances
        supports = [l for l in levels if l.price_mid < current_price]
        resistances = [l for l in levels if l.price_mid >= current_price]

        # Sort by strength and proximity
        strength_order = {
            LevelStrength.KEY: 4,
            LevelStrength.STRONG: 3,
            LevelStrength.MODERATE: 2,
            LevelStrength.WEAK: 1,
        }

        supports.sort(
            key=lambda l: (-strength_order.get(l.strength, 0), -l.price_mid)
        )
        resistances.sort(
            key=lambda l: (-strength_order.get(l.strength, 0), l.price_mid)
        )

        # Take half from each side
        half = self.parent.config.max_levels // 2
        selected = supports[:half] + resistances[:half]

        return sorted(selected, key=lambda l: l.price_mid)
