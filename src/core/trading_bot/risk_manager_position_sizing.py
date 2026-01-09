"""
Risk Manager Position Sizing - Risk-based Position Size Calculation.

Refactored from risk_manager.py.

Contains:
- calculate_position_size: Risk-based position sizing
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .risk_manager import RiskManager

logger = logging.getLogger(__name__)


class RiskManagerPositionSizing:
    """Helper for position size calculation."""

    def __init__(self, parent: RiskManager):
        self.parent = parent

    def calculate_position_size(
        self,
        balance: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal,
        risk_percent: Decimal | None = None,
    ) -> Decimal:
        """
        Berechnet Position Size basierend auf Risiko.

        Args:
            balance: Verfügbares Kapital (USDT)
            entry_price: Entry-Preis
            stop_loss: Stop Loss Preis
            risk_percent: Risiko % (default: aus Config)

        Returns:
            Position Size in BTC (gerundet auf 3 Dezimalstellen)
        """
        if risk_percent is None:
            risk_percent = self.parent.risk_per_trade_percent

        # Risiko-Betrag berechnen
        risk_amount = balance * (risk_percent / Decimal("100"))

        # SL-Distanz berechnen
        sl_distance = abs(entry_price - stop_loss)

        if sl_distance <= 0:
            logger.warning("SL distance is zero or negative, using minimum position")
            return Decimal("0.001")

        # Position Size = Risk Amount / SL Distance
        # Bei Leverage: Position kann größer sein
        quantity = risk_amount / sl_distance

        # Max Position Size Limit
        if quantity > self.parent.max_position_size:
            logger.info(
                f"Position size {quantity} exceeds max {self.parent.max_position_size}, capping"
            )
            quantity = self.parent.max_position_size

        # Minimum Position Size
        min_position = Decimal("0.001")  # 0.001 BTC minimum
        if quantity < min_position:
            logger.info(f"Position size {quantity} below minimum, using {min_position}")
            quantity = min_position

        # Runden auf 3 Dezimalstellen
        quantity = quantity.quantize(Decimal("0.001"))

        logger.debug(
            f"Position size calculated: Balance={balance}, Risk={risk_percent}%, "
            f"SL Distance={sl_distance}, Quantity={quantity}"
        )

        return quantity
