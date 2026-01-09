"""Data Loading Cleaning - Bad tick removal.

Refactored from 498 LOC monolith using composition pattern.

Module 2/6 of data_loading_mixin.py split.

Contains:
- clean_bad_ticks(): Remove extreme wicks (bad ticks)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


class DataLoadingCleaning:
    """Helper für DataLoadingMixin bad tick cleaning."""

    def __init__(self, parent):
        """
        Args:
            parent: DataLoadingMixin Instanz
        """
        self.parent = parent

    def clean_bad_ticks(self, data: "pd.DataFrame") -> "pd.DataFrame":
        """
        Bereinige Bad Ticks in historischen OHLCV-Daten.

        Bad Ticks erzeugen extreme Wicks (High/Low weit vom Körper entfernt).
        Diese Funktion korrigiert solche Ausreißer.

        Args:
            data: OHLCV DataFrame

        Returns:
            Bereinigter DataFrame
        """
        if data.empty:
            return data

        # Arbeite mit Kopie
        df = data.copy()

        # Maximale erlaubte Wick-Größe als % vom Kerzenkörper
        max_wick_pct = 10.0  # 10% vom Preis

        for i in range(len(df)):
            row = df.iloc[i]
            body_high = max(row['open'], row['close'])
            body_low = min(row['open'], row['close'])
            mid_price = (body_high + body_low) / 2 if body_high > 0 else row['close']

            if mid_price <= 0:
                continue

            # Prüfe High - ist es unrealistisch hoch?
            if row['high'] > body_high:
                wick_up_pct = ((row['high'] - body_high) / mid_price) * 100
                if wick_up_pct > max_wick_pct:
                    # Bad tick - korrigiere High auf body_high + kleiner Puffer
                    new_high = body_high * 1.005  # 0.5% über Body
                    df.iloc[i, df.columns.get_loc('high')] = new_high
                    logger.debug(
                        f"Bad tick corrected: High {row['high']:.2f} -> {new_high:.2f} "
                        f"(was {wick_up_pct:.1f}% above body)"
                    )

            # Prüfe Low - ist es unrealistisch tief?
            if row['low'] < body_low:
                wick_down_pct = ((body_low - row['low']) / mid_price) * 100
                if wick_down_pct > max_wick_pct:
                    # Bad tick - korrigiere Low auf body_low - kleiner Puffer
                    new_low = body_low * 0.995  # 0.5% unter Body
                    df.iloc[i, df.columns.get_loc('low')] = new_low
                    logger.debug(
                        f"Bad tick corrected: Low {row['low']:.2f} -> {new_low:.2f} "
                        f"(was {wick_down_pct:.1f}% below body)"
                    )

        return df
