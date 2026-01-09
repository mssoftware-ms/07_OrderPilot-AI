"""
Risk Calculation Dataclass.

Refactored from risk_manager.py.

Contains:
- RiskCalculation dataclass
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class RiskCalculation:
    """Ergebnis einer Risiko-Berechnung."""

    # Entry
    entry_price: Decimal
    side: str  # "BUY" oder "SELL"

    # SL/TP
    stop_loss: Decimal
    take_profit: Decimal
    sl_distance: Decimal
    tp_distance: Decimal
    sl_percent: float
    tp_percent: float

    # Position Size
    quantity: Decimal
    position_value_usd: Decimal
    risk_amount_usd: Decimal
    risk_percent: float

    # ATR Info
    atr_value: Decimal
    atr_percent: float

    # Risk:Reward
    risk_reward_ratio: float

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "entry_price": str(self.entry_price),
            "side": self.side,
            "stop_loss": str(self.stop_loss),
            "take_profit": str(self.take_profit),
            "sl_distance": str(self.sl_distance),
            "tp_distance": str(self.tp_distance),
            "sl_percent": self.sl_percent,
            "tp_percent": self.tp_percent,
            "quantity": str(self.quantity),
            "position_value_usd": str(self.position_value_usd),
            "risk_amount_usd": str(self.risk_amount_usd),
            "risk_percent": self.risk_percent,
            "atr_value": str(self.atr_value),
            "atr_percent": self.atr_percent,
            "risk_reward_ratio": self.risk_reward_ratio,
        }
