"""Pattern-Strategy Mapper - Link detected patterns to trading strategies."""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from src.analysis.patterns.base_detector import Pattern

from src.strategies.strategy_models import (
    PatternStrategyMapping,
    PATTERN_STRATEGIES,
    TradingStrategy
)

logger = logging.getLogger(__name__)


@dataclass
class TradeSetup:
    """Complete trade setup for a detected pattern."""

    # Pattern Info
    pattern: Any  # Pattern object
    pattern_strategy: PatternStrategyMapping

    # Entry Details
    entry_price: float
    entry_condition: str

    # Exit Details
    stop_loss: float
    target_price: float
    risk_reward_ratio: float

    # Confirmation
    confirmation_pending: List[str]  # e.g., ["Volume spike", "RSI >50"]
    confidence_score: float  # 0-100

    # Additional Info
    notes: str


class PatternStrategyMapper:
    """Map detected patterns to trading strategies with success rates."""

    def __init__(self):
        """Initialize mapper with pre-defined strategies."""
        self.strategies = PATTERN_STRATEGIES

    def get_strategy(self, pattern_type: str) -> Optional[PatternStrategyMapping]:
        """Get trading strategy for a pattern type.

        Args:
            pattern_type: Pattern type string (e.g., "cup_and_handle")

        Returns:
            PatternStrategyMapping if found, else None
        """
        return self.strategies.get(pattern_type)

    def map_pattern_to_strategy(
        self,
        pattern: Any  # Pattern object
    ) -> Optional[PatternStrategyMapping]:
        """Map a detected Pattern to its trading strategy.

        Args:
            pattern: Detected Pattern object

        Returns:
            PatternStrategyMapping if pattern has known strategy, else None
        """
        return self.get_strategy(pattern.pattern_type)

    def generate_trade_setup(
        self,
        pattern: Any,  # Pattern object
        current_price: float
    ) -> Optional[TradeSetup]:
        """Generate complete trade setup for a pattern.

        Args:
            pattern: Detected Pattern object
            current_price: Current market price

        Returns:
            TradeSetup object if strategy exists, else None
        """
        strategy_mapping = self.map_pattern_to_strategy(pattern)

        if not strategy_mapping:
            logger.warning(f"No strategy found for pattern type: {pattern.pattern_type}")
            return None

        strategy = strategy_mapping.strategy

        # Calculate entry, stop, target based on pattern and strategy rules
        entry_price = self._calculate_entry_price(pattern, current_price, strategy)
        stop_loss = self._calculate_stop_loss(pattern, entry_price, strategy)
        target_price = self._calculate_target(pattern, entry_price, strategy)

        # Risk-Reward
        risk = abs(entry_price - stop_loss)
        reward = abs(target_price - entry_price)
        rr_ratio = reward / risk if risk > 0 else 0

        # Confirmation checks
        confirmation_pending = self._check_confirmations(pattern, strategy)

        # Confidence score (based on pattern score + confirmation status)
        confidence = self._calculate_confidence(pattern, confirmation_pending)

        return TradeSetup(
            pattern=pattern,
            pattern_strategy=strategy_mapping,
            entry_price=entry_price,
            entry_condition=strategy.description,
            stop_loss=stop_loss,
            target_price=target_price,
            risk_reward_ratio=rr_ratio,
            confirmation_pending=confirmation_pending,
            confidence_score=confidence,
            notes=f"Success Rate: {strategy.success_rate}% | Avg Profit: {strategy.avg_profit}"
        )

    def _calculate_entry_price(
        self,
        pattern: Any,
        current_price: float,
        strategy: TradingStrategy
    ) -> float:
        """Calculate entry price based on pattern and strategy.

        Simplified implementation - can be extended with more logic.
        """
        # For breakout strategies: Entry at breakout level
        if "BREAKOUT" in strategy.strategy_type.value:
            # Use pattern's end price (approximation)
            if hasattr(pattern, 'pivots') and pattern.pivots:
                return pattern.pivots[-1].price
            return current_price

        # For retest strategies: Entry at retest level
        elif "RETEST" in strategy.strategy_type.value:
            if hasattr(pattern, 'pivots') and pattern.pivots:
                return pattern.pivots[-2].price if len(pattern.pivots) > 1 else current_price
            return current_price

        # Default: Current price
        return current_price

    def _calculate_stop_loss(
        self,
        pattern: Any,
        entry_price: float,
        strategy: TradingStrategy
    ) -> float:
        """Calculate stop loss based on strategy rules.

        Uses pattern structure and strategy.stop_loss_placement.
        """
        # Simplified: Use pattern score as percentage distance
        # In production: Parse stop_loss_placement string and calculate exact level
        score = getattr(pattern, 'score', 50)
        sl_distance_pct = (100 - score) / 100 * 0.05  # 0-5% based on score

        direction_bias = getattr(pattern, 'direction_bias', None)
        if direction_bias and hasattr(direction_bias, 'value'):
            if direction_bias.value == "UP":
                return entry_price * (1 - sl_distance_pct)
            else:
                return entry_price * (1 + sl_distance_pct)

        # Default: 2% stop loss
        return entry_price * 0.98

    def _calculate_target(
        self,
        pattern: Any,
        entry_price: float,
        strategy: TradingStrategy
    ) -> float:
        """Calculate target price based on strategy rules.

        Uses pattern height and strategy.target_calculation.
        """
        # Simplified: Use avg_profit midpoint
        avg_profit_str = strategy.avg_profit.replace("%", "")

        if "-" in avg_profit_str:
            low, high = avg_profit_str.split("-")
            avg_pct = (float(low) + float(high)) / 2 / 100
        else:
            avg_pct = float(avg_profit_str) / 100

        direction_bias = getattr(pattern, 'direction_bias', None)
        if direction_bias and hasattr(direction_bias, 'value'):
            if direction_bias.value == "UP":
                return entry_price * (1 + avg_pct)
            else:
                return entry_price * (1 - avg_pct)

        # Default: 5% target
        return entry_price * 1.05

    def _check_confirmations(
        self,
        pattern: Any,
        strategy: TradingStrategy
    ) -> List[str]:
        """Check which confirmations are pending.

        Returns list of pending confirmations (empty if all confirmed).
        """
        pending = []

        if strategy.volume_confirmation:
            pending.append("Volume Spike (2x avg)")

        if strategy.rsi_condition:
            pending.append(f"RSI {strategy.rsi_condition}")

        if strategy.macd_confirmation:
            pending.append("MACD Crossover")

        return pending

    def _calculate_confidence(
        self,
        pattern: Any,
        confirmation_pending: List[str]
    ) -> float:
        """Calculate overall confidence score.

        Args:
            pattern: Pattern with score (0-100)
            confirmation_pending: List of pending confirmations

        Returns:
            Confidence score (0-100)
        """
        # Start with pattern score
        confidence = getattr(pattern, 'score', 50)

        # Reduce by 10% for each pending confirmation
        penalty = len(confirmation_pending) * 10
        confidence = max(0, confidence - penalty)

        return confidence

    def get_all_phase1_patterns(self) -> List[str]:
        """Get list of all Phase 1 pattern types.

        Returns:
            List of pattern type strings
        """
        return [
            pattern_type
            for pattern_type, mapping in self.strategies.items()
            if mapping.implementation_phase == 1
        ]
