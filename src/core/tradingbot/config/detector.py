"""Regime Detector for Market Phase Classification.

Detects active market regimes by evaluating regime conditions against
indicator values. Supports multiple simultaneous regimes with priority
and scope filtering.

Architecture:
    RegimeDefinitions + IndicatorValues -> RegimeDetector -> ActiveRegimes

    detector = RegimeDetector(regime_definitions)
    active = detector.detect_active_regimes(indicator_values, scope="entry")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime

from .evaluator import ConditionEvaluator
from .models import RegimeDefinition, RegimeScope

logger = logging.getLogger(__name__)


@dataclass
class ActiveRegime:
    """An active market regime with metadata.

    Attributes:
        definition: The regime definition
        confidence: Confidence score (0.0-1.0). Currently always 1.0 for active regimes
        activated_at: Timestamp when regime became active
    """
    definition: RegimeDefinition
    confidence: float = 1.0
    activated_at: datetime | None = None

    def __post_init__(self):
        """Set activation timestamp if not provided."""
        if self.activated_at is None:
            self.activated_at = datetime.utcnow()

    @property
    def id(self) -> str:
        """Regime ID."""
        return self.definition.id

    @property
    def name(self) -> str:
        """Regime name."""
        return self.definition.name

    @property
    def priority(self) -> int:
        """Regime priority."""
        return self.definition.priority

    @property
    def scope(self) -> RegimeScope | None:
        """Regime scope."""
        return self.definition.scope

    def __repr__(self) -> str:
        scope_str = f", scope={self.scope.value}" if self.scope else ""
        return f"ActiveRegime(id='{self.id}', priority={self.priority}{scope_str})"


class RegimeDetector:
    """Detects active market regimes from indicator values.

    Evaluates all regime definitions and returns those whose conditions
    are met, sorted by priority (highest first).

    Features:
    - Multi-regime support (multiple regimes can be active simultaneously)
    - Priority-based ordering
    - Scope filtering (entry/exit/in_trade)
    - Detailed logging

    Example:
        >>> regimes = [
        ...     RegimeDefinition(
        ...         id="trending",
        ...         name="Trending Market",
        ...         conditions=ConditionGroup(...),
        ...         priority=10
        ...     ),
        ...     RegimeDefinition(
        ...         id="low_vol",
        ...         name="Low Volume",
        ...         conditions=ConditionGroup(...),
        ...         priority=5
        ...     )
        ... ]
        >>> detector = RegimeDetector(regimes)
        >>> indicator_values = {"adx14": {"value": 28.5}, "vol_ratio": {"value": 0.3}}
        >>> active = detector.detect_active_regimes(indicator_values)
        >>> print([r.id for r in active])
        ['trending', 'low_vol']  # Both active, sorted by priority
    """

    def __init__(self, regime_definitions: list[RegimeDefinition]):
        """Initialize detector with regime definitions.

        Args:
            regime_definitions: List of RegimeDefinition objects
        """
        self.regime_definitions = regime_definitions
        logger.info(f"Initialized RegimeDetector with {len(regime_definitions)} regimes")

    def detect_active_regimes(
        self,
        indicator_values: dict[str, dict[str, float]],
        scope: RegimeScope | str | None = None
    ) -> list[ActiveRegime]:
        """Detect all active regimes for current market conditions.

        Args:
            indicator_values: Dict mapping indicator_id -> {field -> value}
            scope: Optional scope filter ("entry", "exit", "in_trade", or None for global)
                  Can be RegimeScope enum or string

        Returns:
            List of ActiveRegime objects, sorted by priority (highest first)
        """
        # Convert string scope to enum if needed
        if isinstance(scope, str):
            scope = RegimeScope(scope)

        evaluator = ConditionEvaluator(indicator_values)
        active_regimes = []

        # Evaluate each regime
        for regime_def in self.regime_definitions:
            # Skip if scope filter doesn't match
            if scope is not None and regime_def.scope is not None:
                if regime_def.scope != scope:
                    logger.debug(
                        f"Skipping regime '{regime_def.id}' (scope={regime_def.scope.value}, "
                        f"requested={scope.value})"
                    )
                    continue

            # Evaluate regime conditions
            try:
                is_active = evaluator.evaluate_group(regime_def.conditions)

                if is_active:
                    active_regime = ActiveRegime(definition=regime_def)
                    active_regimes.append(active_regime)
                    logger.info(
                        f"Regime ACTIVE: '{regime_def.id}' ({regime_def.name}) "
                        f"[priority={regime_def.priority}]"
                    )
                else:
                    logger.debug(
                        f"Regime inactive: '{regime_def.id}' ({regime_def.name})"
                    )

            except Exception as e:
                logger.error(
                    f"Error evaluating regime '{regime_def.id}': {e}. "
                    f"Treating as inactive."
                )

        # Sort by priority (highest first)
        active_regimes.sort(key=lambda r: r.priority, reverse=True)

        logger.info(
            f"Detected {len(active_regimes)} active regime(s): "
            f"{[r.id for r in active_regimes]}"
        )

        return active_regimes

    def get_highest_priority_regime(
        self,
        indicator_values: dict[str, dict[str, float]],
        scope: RegimeScope | str | None = None
    ) -> ActiveRegime | None:
        """Get the single highest-priority active regime.

        Args:
            indicator_values: Dict mapping indicator_id -> {field -> value}
            scope: Optional scope filter

        Returns:
            Highest priority ActiveRegime, or None if no regimes active
        """
        active = self.detect_active_regimes(indicator_values, scope=scope)
        return active[0] if active else None

    def is_regime_active(
        self,
        regime_id: str,
        indicator_values: dict[str, dict[str, float]]
    ) -> bool:
        """Check if a specific regime is currently active.

        Args:
            regime_id: ID of regime to check
            indicator_values: Dict mapping indicator_id -> {field -> value}

        Returns:
            True if regime is active, False otherwise
        """
        active = self.detect_active_regimes(indicator_values)
        return any(r.id == regime_id for r in active)

    def get_active_regimes_by_scope(
        self,
        indicator_values: dict[str, dict[str, float]]
    ) -> dict[str, list[ActiveRegime]]:
        """Get active regimes grouped by scope.

        Args:
            indicator_values: Dict mapping indicator_id -> {field -> value}

        Returns:
            Dict mapping scope name -> list of ActiveRegime
            Keys: "entry", "exit", "in_trade", "global" (None scope)
        """
        all_active = self.detect_active_regimes(indicator_values)

        result = {
            "entry": [],
            "exit": [],
            "in_trade": [],
            "global": []
        }

        for regime in all_active:
            if regime.scope is None:
                result["global"].append(regime)
            else:
                result[regime.scope.value].append(regime)

        return result

    def get_regime_definition(self, regime_id: str) -> RegimeDefinition | None:
        """Get regime definition by ID.

        Args:
            regime_id: Regime identifier

        Returns:
            RegimeDefinition if found, None otherwise
        """
        for regime_def in self.regime_definitions:
            if regime_def.id == regime_id:
                return regime_def
        return None
