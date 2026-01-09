"""
Signal Generator Long Conditions - Long Entry Condition Checks.

Refactored from signal_generator.py.

Contains:
- _check_long_conditions: Checks all LONG entry conditions (5 conditions)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from .signal_types import ConditionResult

if TYPE_CHECKING:
    from .signal_generator import SignalGenerator


class SignalGeneratorLongConditions:
    """Helper for long condition checks."""

    def __init__(self, parent: SignalGenerator):
        self.parent = parent

    def check_long_conditions(
        self, df: pd.DataFrame, current: pd.Series
    ) -> list[ConditionResult]:
        """Prüft alle LONG Entry-Bedingungen."""
        conditions = []

        # 1. Regime Check (nicht BEAR)
        # Wird extern geprüft, hier nur Placeholder
        conditions.append(
            ConditionResult(
                name="regime_favorable",
                met=True,  # Wird von generate_signal überschrieben
                description="Regime is not STRONG_TREND_BEAR",
            )
        )

        # 2. Preis über EMA20 UND EMA20 > EMA50
        ema20 = current.get("ema_20") or current.get("EMA_20")
        ema50 = current.get("ema_50") or current.get("EMA_50")
        price = current.get("close", 0)

        if ema20 and ema50 and price:
            price_above_ema = price > ema20 and ema20 > ema50
            conditions.append(
                ConditionResult(
                    name="ema_alignment",
                    met=price_above_ema,
                    value=f"Price: {price:.2f}, EMA20: {ema20:.2f}, EMA50: {ema50:.2f}",
                    description="Price > EMA20 > EMA50 (bullish alignment)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="ema_alignment",
                    met=False,
                    description="EMA data not available",
                )
            )

        # 3. RSI zwischen 40-70 (nicht überkauft)
        rsi = current.get("rsi_14") or current.get("RSI_14") or current.get("rsi")

        if rsi is not None:
            rsi_ok = 40 <= rsi <= 70
            conditions.append(
                ConditionResult(
                    name="rsi_favorable",
                    met=rsi_ok,
                    value=rsi,
                    threshold="40-70",
                    description=f"RSI at {rsi:.1f} (not overbought, room to rise)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="rsi_favorable",
                    met=False,
                    description="RSI data not available",
                )
            )

        # 4. MACD Linie > Signal Linie
        macd = current.get("macd") or current.get("MACD")
        macd_signal = current.get("macd_signal") or current.get("MACD_signal")

        if macd is not None and macd_signal is not None:
            macd_bullish = macd > macd_signal
            conditions.append(
                ConditionResult(
                    name="macd_bullish",
                    met=macd_bullish,
                    value=f"MACD: {macd:.2f}, Signal: {macd_signal:.2f}",
                    description="MACD line above signal line (bullish momentum)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="macd_bullish",
                    met=False,
                    description="MACD data not available",
                )
            )

        # 5. ADX > 20 (Trend vorhanden)
        adx = current.get("adx_14") or current.get("ADX_14") or current.get("adx")

        if adx is not None:
            adx_ok = adx > self.parent.ADX_THRESHOLD
            conditions.append(
                ConditionResult(
                    name="adx_trending",
                    met=adx_ok,
                    value=adx,
                    threshold=self.parent.ADX_THRESHOLD,
                    description=f"ADX at {adx:.1f} (trend present)"
                    if adx_ok
                    else f"ADX at {adx:.1f} (weak trend)",
                )
            )
        else:
            conditions.append(
                ConditionResult(
                    name="adx_trending",
                    met=False,
                    description="ADX data not available",
                )
            )

        return conditions
