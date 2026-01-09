"""
Risk Manager Risk Analysis - Full Risk Calculation.

Refactored from risk_manager.py.

Contains:
- calculate_full_risk: Combines SL/TP + position sizing into full risk analysis
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .risk_calculation import RiskCalculation
    from .risk_manager import RiskManager


class RiskManagerRiskAnalysis:
    """Helper for full risk analysis."""

    def __init__(self, parent: RiskManager):
        self.parent = parent

    def calculate_full_risk(
        self,
        balance: Decimal,
        entry_price: Decimal,
        side: str,
        atr: Decimal,
    ) -> RiskCalculation:
        """
        Berechnet vollständige Risiko-Analyse.

        Args:
            balance: Verfügbares Kapital (USDT)
            entry_price: Entry-Preis
            side: "BUY" oder "SELL"
            atr: ATR Wert

        Returns:
            RiskCalculation mit allen Details
        """
        from .risk_calculation import RiskCalculation

        # SL/TP berechnen
        stop_loss, take_profit = self.parent._sl_tp.calculate_sl_tp(
            entry_price, side, atr
        )

        # Position Size berechnen
        quantity = self.parent._position_sizing.calculate_position_size(
            balance, entry_price, stop_loss
        )

        # Distanzen
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = abs(take_profit - entry_price)

        # Prozente
        sl_percent = float(sl_distance / entry_price * 100)
        tp_percent = float(tp_distance / entry_price * 100)
        atr_percent = float(atr / entry_price * 100)

        # Position Value und Risk Amount
        position_value = quantity * entry_price
        risk_amount = quantity * sl_distance

        # Risk:Reward Ratio
        if sl_distance > 0:
            risk_reward = float(tp_distance / sl_distance)
        else:
            risk_reward = 0.0

        # Risk Percent (actual)
        if balance > 0:
            actual_risk_percent = float(risk_amount / balance * 100)
        else:
            actual_risk_percent = 0.0

        return RiskCalculation(
            entry_price=entry_price,
            side=side.upper(),
            stop_loss=stop_loss,
            take_profit=take_profit,
            sl_distance=sl_distance,
            tp_distance=tp_distance,
            sl_percent=round(sl_percent, 2),
            tp_percent=round(tp_percent, 2),
            quantity=quantity,
            position_value_usd=position_value.quantize(Decimal("0.01")),
            risk_amount_usd=risk_amount.quantize(Decimal("0.01")),
            risk_percent=round(actual_risk_percent, 2),
            atr_value=atr,
            atr_percent=round(atr_percent, 2),
            risk_reward_ratio=round(risk_reward, 2),
        )
