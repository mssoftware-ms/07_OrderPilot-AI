"""
Risk Manager SL/TP - Stop Loss and Take Profit Calculation.

Refactored from risk_manager.py.

Contains:
- calculate_sl_tp: SL/TP calculation (percent or ATR based)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .risk_manager import RiskManager

logger = logging.getLogger(__name__)


class RiskManagerSLTP:
    """Helper for SL/TP calculation."""

    def __init__(self, parent: RiskManager):
        self.parent = parent

    def calculate_sl_tp(
        self,
        entry_price: Decimal,
        side: str,
        atr: Decimal | None = None,
    ) -> tuple[Decimal, Decimal]:
        """
        Berechnet Stop Loss und Take Profit.

        Unterstützt zwei Modi:
        - 'percent_based': Feste Prozent vom Entry (bevorzugt für Risikokontrolle)
        - 'atr_based': ATR-Multiplikator (dynamisch je nach Volatilität)

        Args:
            entry_price: Erwarteter Entry-Preis
            side: "BUY" (Long) oder "SELL" (Short)
            atr: Average True Range Wert (optional bei percent_based)

        Returns:
            Tuple (stop_loss, take_profit)
        """
        # Stop Loss Distanz berechnen
        if self.parent.sl_type == "percent_based":
            sl_distance = entry_price * (self.parent.sl_percent / Decimal("100"))
        else:
            if atr is None:
                logger.warning("ATR required for atr_based SL, using 1% fallback")
                sl_distance = entry_price * Decimal("0.01")
            else:
                sl_distance = atr * self.parent.sl_atr_multiplier

        # Take Profit Distanz berechnen
        if self.parent.tp_type == "percent_based":
            tp_distance = entry_price * (self.parent.tp_percent / Decimal("100"))
        else:
            if atr is None:
                logger.warning("ATR required for atr_based TP, using 2% fallback")
                tp_distance = entry_price * Decimal("0.02")
            else:
                tp_distance = atr * self.parent.tp_atr_multiplier

        if side.upper() == "BUY":
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:  # SELL (Short)
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance

        # Runden auf 2 Dezimalstellen (USD)
        stop_loss = stop_loss.quantize(Decimal("0.01"))
        take_profit = take_profit.quantize(Decimal("0.01"))

        sl_pct = (sl_distance / entry_price * Decimal("100")).quantize(Decimal("0.01"))
        tp_pct = (tp_distance / entry_price * Decimal("100")).quantize(Decimal("0.01"))

        logger.info(
            f"SL/TP calculated: Entry={entry_price}, Side={side}, "
            f"SL={stop_loss} ({sl_pct}%), TP={take_profit} ({tp_pct}%)"
        )

        return stop_loss, take_profit
