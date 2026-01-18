"""Strategy Set Executor with Parameter Override Support.

Executes strategy sets with temporary parameter overrides for indicators
and strategies. Manages state restoration after execution.

Architecture:
    MatchedStrategySet + OriginalConfig → Executor → ExecutedStrategies
    (with overrides applied)                           ↓
                                                 (state restored)
"""

from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .models import (
    IndicatorDefinition,
    IndicatorOverride,
    RiskSettings,
    StrategyDefinition,
    StrategyReference,
    StrategySetDefinition,
)
from .router import MatchedStrategySet

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for strategy set execution.

    Tracks original state for restoration after execution.

    Attributes:
        strategy_set: The strategy set being executed
        original_indicators: Original indicator definitions (before overrides)
        original_strategies: Original strategy definitions (before overrides)
        applied_overrides: Track which overrides were applied
    """
    strategy_set: StrategySetDefinition
    original_indicators: dict[str, IndicatorDefinition]
    original_strategies: dict[str, StrategyDefinition]
    applied_overrides: dict[str, Any]

    def __repr__(self) -> str:
        return (
            f"ExecutionContext(strategy_set='{self.strategy_set.id}', "
            f"overrides={len(self.applied_overrides)})"
        )


class StrategySetExecutor:
    """Executes strategy sets with parameter overrides.

    Applies temporary overrides to indicators and strategies, executes
    the strategy set, then restores original state.

    Features:
    - Indicator parameter overrides
    - Strategy parameter overrides (entry, exit, risk)
    - State restoration (immutable pattern)
    - Execution tracking

    Example:
        >>> executor = StrategySetExecutor(indicators, strategies)
        >>> context = executor.prepare_execution(matched_strategy_set)
        >>> # Use overridden parameters...
        >>> executor.restore_state(context)  # Restore originals
    """

    def __init__(
        self,
        indicators: list[IndicatorDefinition],
        strategies: list[StrategyDefinition]
    ):
        """Initialize executor with original indicators and strategies.

        Args:
            indicators: List of indicator definitions
            strategies: List of strategy definitions
        """
        self.original_indicators = {ind.id: ind for ind in indicators}
        self.original_strategies = {strat.id: strat for strat in strategies}

        # Working copies (will be modified by overrides)
        self.current_indicators = deepcopy(self.original_indicators)
        self.current_strategies = deepcopy(self.original_strategies)

        logger.info(
            f"Initialized StrategySetExecutor with "
            f"{len(indicators)} indicators, {len(strategies)} strategies"
        )

    def _apply_indicator_overrides(
        self,
        overrides: list[IndicatorOverride]
    ) -> dict[str, dict[str, Any]]:
        """Apply indicator parameter overrides.

        Args:
            overrides: List of IndicatorOverride objects

        Returns:
            Dict mapping indicator_id -> {param_name -> original_value}
        """
        applied = {}

        for override in overrides:
            indicator_id = override.indicator_id

            if indicator_id not in self.current_indicators:
                logger.warning(
                    f"Indicator override for unknown indicator: '{indicator_id}'. "
                    f"Skipping."
                )
                continue

            indicator = self.current_indicators[indicator_id]

            # Track original params
            original_params = deepcopy(indicator.params)
            applied[indicator_id] = original_params

            # Apply overrides
            indicator.params.update(override.params)

            logger.debug(
                f"Applied indicator override: '{indicator_id}' "
                f"{override.params}"
            )

        return applied

    def _apply_strategy_overrides(
        self,
        strategy_ref: StrategyReference
    ) -> dict[str, Any]:
        """Apply strategy parameter overrides.

        Args:
            strategy_ref: StrategyReference with optional overrides

        Returns:
            Dict mapping field_name -> original_value
        """
        strategy_id = strategy_ref.strategy_id
        applied = {}

        if strategy_id not in self.current_strategies:
            logger.warning(
                f"Strategy override for unknown strategy: '{strategy_id}'. "
                f"Skipping."
            )
            return applied

        if not strategy_ref.strategy_overrides:
            return applied

        strategy = self.current_strategies[strategy_id]
        overrides = strategy_ref.strategy_overrides

        # Apply entry overrides
        if "entry" in overrides:
            applied["entry"] = deepcopy(strategy.entry)
            strategy.entry = overrides["entry"]
            logger.debug(f"Applied entry override for '{strategy_id}'")

        # Apply exit overrides
        if "exit" in overrides:
            applied["exit"] = deepcopy(strategy.exit)
            strategy.exit = overrides["exit"]
            logger.debug(f"Applied exit override for '{strategy_id}'")

        # Apply risk overrides
        if "risk" in overrides:
            applied["risk"] = deepcopy(strategy.risk)
            # Merge risk params (not replace entirely)
            risk_override = overrides["risk"]
            if strategy.risk is None:
                if isinstance(risk_override, RiskSettings):
                    strategy.risk = deepcopy(risk_override)
                elif isinstance(risk_override, dict):
                    strategy.risk = RiskSettings(**risk_override)
                else:
                    logger.warning(
                        f"Unsupported risk override type for '{strategy_id}': "
                        f"{type(risk_override)}. Skipping."
                    )
            else:
                if isinstance(risk_override, RiskSettings):
                    risk_data = risk_override.model_dump(exclude_none=True)
                elif isinstance(risk_override, dict):
                    risk_data = {
                        key: value for key, value in risk_override.items()
                        if value is not None
                    }
                else:
                    logger.warning(
                        f"Unsupported risk override type for '{strategy_id}': "
                        f"{type(risk_override)}. Skipping."
                    )
                    risk_data = {}

                for key, value in risk_data.items():
                    setattr(strategy.risk, key, value)
            logger.debug(f"Applied risk override for '{strategy_id}'")

        return applied

    def prepare_execution(
        self,
        matched_strategy_set: MatchedStrategySet
    ) -> ExecutionContext:
        """Prepare strategy set for execution with overrides.

        Applies all overrides and returns context for restoration.

        Args:
            matched_strategy_set: The matched strategy set to execute

        Returns:
            ExecutionContext with original state for restoration
        """
        strategy_set = matched_strategy_set.strategy_set

        logger.info(f"Preparing execution for strategy set: '{strategy_set.id}'")

        # Track all applied overrides
        all_overrides = {}

        # Apply indicator overrides
        if strategy_set.indicator_overrides:
            indicator_overrides = self._apply_indicator_overrides(
                strategy_set.indicator_overrides
            )
            all_overrides["indicators"] = indicator_overrides

        # Apply strategy overrides
        strategy_overrides = {}
        for strategy_ref in strategy_set.strategies:
            overrides = self._apply_strategy_overrides(strategy_ref)
            if overrides:
                strategy_overrides[strategy_ref.strategy_id] = overrides

        if strategy_overrides:
            all_overrides["strategies"] = strategy_overrides

        # Create execution context
        context = ExecutionContext(
            strategy_set=strategy_set,
            original_indicators=deepcopy(self.original_indicators),
            original_strategies=deepcopy(self.original_strategies),
            applied_overrides=all_overrides
        )

        logger.info(
            f"Execution prepared: {len(all_overrides)} override type(s) applied"
        )

        return context

    def restore_state(self, context: ExecutionContext) -> None:
        """Restore original state after execution.

        Args:
            context: ExecutionContext with original state
        """
        logger.info(
            f"Restoring state for strategy set: '{context.strategy_set.id}'"
        )

        # Restore indicators
        if "indicators" in context.applied_overrides:
            for indicator_id, original_params in context.applied_overrides["indicators"].items():
                if indicator_id in self.current_indicators:
                    self.current_indicators[indicator_id].params = original_params
                    logger.debug(f"Restored indicator params: '{indicator_id}'")

        # Restore strategies
        if "strategies" in context.applied_overrides:
            for strategy_id, original_fields in context.applied_overrides["strategies"].items():
                if strategy_id not in self.current_strategies:
                    continue

                strategy = self.current_strategies[strategy_id]

                if "entry" in original_fields:
                    strategy.entry = original_fields["entry"]
                if "exit" in original_fields:
                    strategy.exit = original_fields["exit"]
                if "risk" in original_fields:
                    strategy.risk = original_fields["risk"]

                logger.debug(f"Restored strategy params: '{strategy_id}'")

        logger.info("State restoration complete")

    def get_current_indicator(self, indicator_id: str) -> IndicatorDefinition | None:
        """Get current indicator definition (with overrides applied).

        Args:
            indicator_id: Indicator identifier

        Returns:
            Current IndicatorDefinition, or None if not found
        """
        return self.current_indicators.get(indicator_id)

    def get_current_strategy(self, strategy_id: str) -> StrategyDefinition | None:
        """Get current strategy definition (with overrides applied).

        Args:
            strategy_id: Strategy identifier

        Returns:
            Current StrategyDefinition, or None if not found
        """
        return self.current_strategies.get(strategy_id)

    def get_strategy_ids_from_set(
        self,
        strategy_set: StrategySetDefinition
    ) -> list[str]:
        """Extract strategy IDs from strategy set.

        Args:
            strategy_set: StrategySetDefinition

        Returns:
            List of strategy IDs
        """
        return [ref.strategy_id for ref in strategy_set.strategies]

    def reset_to_original(self) -> None:
        """Reset all state to original (remove all overrides).

        Useful for cleanup or switching between strategy sets.
        """
        logger.info("Resetting executor to original state")

        self.current_indicators = deepcopy(self.original_indicators)
        self.current_strategies = deepcopy(self.original_strategies)

        logger.info("Reset complete")
