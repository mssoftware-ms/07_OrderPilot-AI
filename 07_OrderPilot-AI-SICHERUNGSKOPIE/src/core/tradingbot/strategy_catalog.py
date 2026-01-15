"""Strategy Catalog for Tradingbot.

Defines pre-built strategy profiles for daily selection.
Each strategy has specific entry/exit rules, applicable regimes,
and parameter ranges.

REFACTORED: Split into multiple files to meet 600 LOC limit.
- strategy_definitions.py: StrategyType, EntryRule, ExitRule, StrategyDefinition
- strategy_templates.py: StrategyTemplatesMixin with template creation methods
- strategy_catalog.py: Main StrategyCatalog class (this file)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

# Re-export types for backward compatibility
from .strategy_definitions import (
    EntryRule,
    ExitRule,
    StrategyDefinition,
    StrategyType,
)
from .strategy_templates import StrategyTemplatesMixin

if TYPE_CHECKING:
    from .models import RegimeState

__all__ = [
    "StrategyType",
    "EntryRule",
    "ExitRule",
    "StrategyDefinition",
    "StrategyCatalog",
]

logger = logging.getLogger(__name__)


class StrategyCatalog(StrategyTemplatesMixin):
    """Catalog of pre-built trading strategies.

    Provides strategy definitions for different market conditions
    and regime types.
    """

    def __init__(self):
        """Initialize strategy catalog with built-in strategies."""
        self._strategies: dict[str, StrategyDefinition] = {}
        self._register_builtin_strategies()
        logger.info(f"StrategyCatalog initialized with {len(self._strategies)} strategies")

    def _register_builtin_strategies(self) -> None:
        """Register all built-in strategy definitions."""
        # 1. Trend Following
        self._strategies["trend_following_conservative"] = self._create_trend_following_conservative()
        self._strategies["trend_following_aggressive"] = self._create_trend_following_aggressive()

        # 2. Mean Reversion
        self._strategies["mean_reversion_bb"] = self._create_mean_reversion_bb()
        self._strategies["mean_reversion_rsi"] = self._create_mean_reversion_rsi()

        # 3. Breakout
        self._strategies["breakout_volatility"] = self._create_breakout_volatility()
        self._strategies["breakout_momentum"] = self._create_breakout_momentum()

        # 4. Momentum
        self._strategies["momentum_macd"] = self._create_momentum_macd()

        # 5. Scalping (for high frequency)
        self._strategies["scalping_range"] = self._create_scalping_range()

        # 6. Sideways/Range Market (Issue #45)
        self._strategies["sideways_range_bounce"] = self._create_sideways_range_bounce()

    # ==================== Query Methods ====================

    def get_strategy(self, name: str) -> StrategyDefinition | None:
        """Get strategy by name.

        Args:
            name: Strategy name

        Returns:
            StrategyDefinition or None if not found
        """
        return self._strategies.get(name)

    def get_all_strategies(self) -> list[StrategyDefinition]:
        """Get all registered strategies.

        Returns:
            List of all strategy definitions
        """
        return list(self._strategies.values())

    def get_strategies_for_regime(
        self,
        regime: "RegimeState"
    ) -> list[StrategyDefinition]:
        """Get strategies applicable for current regime.

        Args:
            regime: Current regime state

        Returns:
            List of applicable strategies
        """
        return [
            s for s in self._strategies.values()
            if s.is_applicable(regime)
        ]

    def get_strategies_by_type(
        self,
        strategy_type: StrategyType
    ) -> list[StrategyDefinition]:
        """Get strategies of a specific type.

        Args:
            strategy_type: Strategy type

        Returns:
            List of matching strategies
        """
        return [
            s for s in self._strategies.values()
            if s.strategy_type == strategy_type
        ]

    def register_strategy(
        self,
        name: str,
        strategy: StrategyDefinition
    ) -> None:
        """Register a custom strategy.

        Args:
            name: Strategy name
            strategy: Strategy definition
        """
        self._strategies[name] = strategy
        logger.info(f"Registered custom strategy: {name}")

    def list_strategies(self) -> list[str]:
        """List all strategy names.

        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())
