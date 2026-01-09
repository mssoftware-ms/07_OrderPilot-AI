"""
Risk Manager Trade Validation - Complete Trade Validation.

Refactored from risk_manager.py.

Contains:
- validate_trade: Validates if trade can be executed (daily loss + risk limits)
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .risk_calculation import RiskCalculation
    from .risk_manager import RiskManager


class RiskManagerTradeValidation:
    """Helper for trade validation."""

    def __init__(self, parent: RiskManager):
        self.parent = parent

    def validate_trade(
        self,
        balance: Decimal,
        entry_price: Decimal,
        side: str,
        atr: Decimal,
    ) -> tuple[bool, str, RiskCalculation | None]:
        """
        Validiert ob Trade durchgeführt werden darf.

        Args:
            balance: Verfügbares Kapital
            entry_price: Entry-Preis
            side: "BUY" oder "SELL"
            atr: ATR Wert

        Returns:
            Tuple (is_valid, reason, risk_calculation)
        """
        # Daily Loss Check
        can_trade, reason = self.parent._daily_tracking.check_daily_loss_limit(balance)
        if not can_trade:
            return False, reason, None

        # Berechne Risiko
        risk_calc = self.parent._risk_analysis.calculate_full_risk(
            balance, entry_price, side, atr
        )

        # Validiere Position Size
        if risk_calc.quantity <= 0:
            return False, "Position size would be zero", risk_calc

        # Validiere Position Value
        if risk_calc.position_value_usd > balance * Decimal(str(self.parent.leverage)):
            return (
                False,
                f"Position value {risk_calc.position_value_usd} exceeds "
                f"available margin (Balance: {balance}, Leverage: {self.parent.leverage}x)",
                risk_calc,
            )

        # Validiere Risk Amount
        max_risk = balance * (
            self.parent.risk_per_trade_percent / Decimal("100")
        ) * Decimal("1.1")  # 10% Toleranz
        if risk_calc.risk_amount_usd > max_risk:
            return (
                False,
                f"Risk amount {risk_calc.risk_amount_usd} exceeds "
                f"max allowed {max_risk}",
                risk_calc,
            )

        return True, "Trade validated", risk_calc
