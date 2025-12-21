"""Position Sizer for Tradingbot.

Calculates position sizes based on risk parameters.
Supports multiple sizing methods:
- Fixed fractional (% of account)
- ATR-based (volatility-adjusted)
- Fixed quantity
"""

from __future__ import annotations

import logging

from .execution_types import PositionSizeResult, RiskLimits
from .models import Signal

logger = logging.getLogger(__name__)


class PositionSizer:
    """Calculates position sizes based on risk parameters.

    Supports multiple sizing methods:
    - Fixed fractional (% of account)
    - ATR-based (volatility-adjusted)
    - Fixed quantity
    """

    def __init__(
        self,
        account_value: float,
        risk_limits: RiskLimits | None = None,
        default_risk_pct: float = 1.0,
        include_fees: bool = True,
        fee_pct: float = 0.1
    ):
        """Initialize position sizer.

        Args:
            account_value: Current account value
            risk_limits: Risk limit configuration
            default_risk_pct: Default risk per trade
            include_fees: Include fees in calculations
            fee_pct: Fee percentage (round-trip)
        """
        self.account_value = account_value
        self.risk_limits = risk_limits or RiskLimits()
        self.default_risk_pct = default_risk_pct
        self.include_fees = include_fees
        self.fee_pct = fee_pct

        logger.info(
            f"PositionSizer initialized: account=${account_value:.2f}, "
            f"default_risk={default_risk_pct}%"
        )

    def calculate_size(
        self,
        signal: Signal,
        current_price: float,
        atr: float | None = None,
        risk_pct: float | None = None
    ) -> PositionSizeResult:
        """Calculate position size for a signal.

        Args:
            signal: Entry signal with stop-loss
            current_price: Current market price
            atr: Average True Range (for ATR-based sizing)
            risk_pct: Override risk percentage

        Returns:
            PositionSizeResult with calculated size
        """
        risk_pct = risk_pct or self.default_risk_pct
        constraints = []

        # Calculate stop distance
        stop_distance = abs(current_price - signal.stop_loss_price)
        if stop_distance <= 0:
            return PositionSizeResult(
                quantity=0,
                risk_amount=0,
                position_value=0,
                risk_pct_actual=0,
                sizing_method="rejected",
                constraints_applied=["ZERO_STOP_DISTANCE"]
            )

        # Calculate base risk amount
        risk_amount = self.account_value * (risk_pct / 100)

        # Apply max risk per trade limit
        max_risk = self.account_value * (self.risk_limits.max_risk_per_trade_pct / 100)
        if risk_amount > max_risk:
            risk_amount = max_risk
            constraints.append("MAX_RISK_PER_TRADE")

        # Calculate quantity based on risk
        quantity = risk_amount / stop_distance

        # Calculate position value
        position_value = quantity * current_price

        # Apply max position size limits
        max_position_pct = self.risk_limits.max_position_size_pct
        max_position_value = self.account_value * (max_position_pct / 100)

        if self.risk_limits.max_position_value:
            max_position_value = min(max_position_value, self.risk_limits.max_position_value)

        if position_value > max_position_value:
            quantity = max_position_value / current_price
            position_value = max_position_value
            risk_amount = quantity * stop_distance
            constraints.append("MAX_POSITION_SIZE")

        # Account for fees
        if self.include_fees:
            fee_amount = position_value * (self.fee_pct / 100)
            # Reduce quantity slightly to account for fees
            quantity = quantity * (1 - self.fee_pct / 100 / 2)
            position_value = quantity * current_price

        # Calculate actual risk percentage
        risk_pct_actual = (risk_amount / self.account_value) * 100

        return PositionSizeResult(
            quantity=round(quantity, 8),  # Crypto precision
            risk_amount=risk_amount,
            position_value=position_value,
            risk_pct_actual=risk_pct_actual,
            sizing_method="fixed_fractional",
            constraints_applied=constraints
        )

    def calculate_size_atr(
        self,
        signal: Signal,
        current_price: float,
        atr: float,
        atr_multiple: float = 2.0,
        risk_pct: float | None = None
    ) -> PositionSizeResult:
        """Calculate position size using ATR-based stop distance.

        Args:
            signal: Entry signal
            current_price: Current price
            atr: Average True Range
            atr_multiple: ATR multiple for stop distance
            risk_pct: Risk percentage

        Returns:
            PositionSizeResult
        """
        risk_pct = risk_pct or self.default_risk_pct
        constraints = []

        # ATR-based stop distance
        stop_distance = atr * atr_multiple

        if stop_distance <= 0:
            return PositionSizeResult(
                quantity=0,
                risk_amount=0,
                position_value=0,
                risk_pct_actual=0,
                sizing_method="atr_rejected",
                constraints_applied=["ZERO_ATR"]
            )

        # Risk amount
        risk_amount = self.account_value * (risk_pct / 100)
        max_risk = self.account_value * (self.risk_limits.max_risk_per_trade_pct / 100)
        if risk_amount > max_risk:
            risk_amount = max_risk
            constraints.append("MAX_RISK_PER_TRADE")

        # Quantity
        quantity = risk_amount / stop_distance
        position_value = quantity * current_price

        # Position size limits
        max_position_value = self.account_value * (self.risk_limits.max_position_size_pct / 100)
        if position_value > max_position_value:
            quantity = max_position_value / current_price
            position_value = max_position_value
            risk_amount = quantity * stop_distance
            constraints.append("MAX_POSITION_SIZE")

        risk_pct_actual = (risk_amount / self.account_value) * 100

        return PositionSizeResult(
            quantity=round(quantity, 8),
            risk_amount=risk_amount,
            position_value=position_value,
            risk_pct_actual=risk_pct_actual,
            sizing_method="atr_based",
            constraints_applied=constraints
        )

    def update_account_value(self, value: float) -> None:
        """Update account value.

        Args:
            value: New account value
        """
        self.account_value = value
        logger.debug(f"Account value updated: ${value:.2f}")
