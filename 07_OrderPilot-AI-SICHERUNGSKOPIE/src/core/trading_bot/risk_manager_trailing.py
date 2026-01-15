"""
Risk Manager Trailing - Trailing Stop Calculation.

Refactored from risk_manager.py.

Contains:
- adjust_sl_for_trailing: Calculates new trailing stop (percent or ATR based)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .risk_manager import RiskManager

logger = logging.getLogger(__name__)


class RiskManagerTrailing:
    """Helper for trailing stop calculation."""

    def __init__(self, parent: RiskManager):
        self.parent = parent

    def adjust_sl_for_trailing(
        self,
        current_price: Decimal,
        current_sl: Decimal,
        entry_price: Decimal,
        side: str,
        atr: Decimal | None = None,
        activation_percent: Decimal | None = None,
    ) -> tuple[Decimal, bool]:
        """
        Berechnet neuen Trailing Stop.

        Unterstützt zwei Modi:
        - 'percent_based': Feste Prozent vom aktuellen Preis
        - 'atr_based': ATR-Multiplikator

        Args:
            current_price: Aktueller Marktpreis
            current_sl: Aktueller Stop Loss
            entry_price: Entry-Preis
            side: "BUY" oder "SELL"
            atr: ATR Wert für Trailing Distance (optional bei percent_based)
            activation_percent: Min. Profit % für Aktivierung

        Returns:
            Tuple (new_sl, was_updated)
        """
        # Aktivierungsschwelle
        if activation_percent is None:
            if self.parent.strategy_config:
                activation_percent = Decimal(
                    str(self.parent.strategy_config.trailing_stop_activation_percent)
                )
            elif self.parent.config:
                activation_percent = self.parent.config.trailing_stop_activation_percent
            else:
                activation_percent = Decimal("0.5")

        # Trailing Distance berechnen
        trailing_type = "atr_based"
        if self.parent.strategy_config:
            trailing_type = self.parent.strategy_config.trailing_stop_type

        if trailing_type == "percent_based":
            # Prozent-basierter Trailing Stop
            if self.parent.strategy_config:
                trail_percent = Decimal(
                    str(self.parent.strategy_config.trailing_stop_percent)
                )
            else:
                trail_percent = Decimal("0.3")
            trailing_distance = current_price * (trail_percent / Decimal("100"))
        else:
            # ATR-basierter Trailing Stop
            if atr is None:
                logger.warning("ATR required for atr_based trailing, using 0.3% fallback")
                trailing_distance = current_price * Decimal("0.003")
            else:
                if self.parent.strategy_config:
                    trailing_multiplier = Decimal(
                        str(self.parent.strategy_config.trailing_stop_atr_multiplier)
                    )
                elif self.parent.config:
                    trailing_multiplier = self.parent.config.trailing_stop_atr_multiplier
                else:
                    trailing_multiplier = Decimal("1.0")
                trailing_distance = atr * trailing_multiplier

        if side.upper() == "BUY":
            # Long: Prüfe ob Preis gestiegen ist
            profit_percent = (current_price - entry_price) / entry_price * 100

            if profit_percent < activation_percent:
                return current_sl, False

            # Neuer SL = Preis - Trailing Distance
            new_sl = current_price - trailing_distance
            new_sl = new_sl.quantize(Decimal("0.01"))

            # SL darf nur steigen, nie fallen
            if new_sl > current_sl:
                return new_sl, True

        else:  # SELL (Short)
            # Short: Prüfe ob Preis gefallen ist
            profit_percent = (entry_price - current_price) / entry_price * 100

            if profit_percent < activation_percent:
                return current_sl, False

            # Neuer SL = Preis + Trailing Distance
            new_sl = current_price + trailing_distance
            new_sl = new_sl.quantize(Decimal("0.01"))

            # SL darf nur sinken, nie steigen
            if new_sl < current_sl:
                return new_sl, True

        return current_sl, False
