"""Strategy Router for Regime-Based Strategy Selection.

Routes active regimes to appropriate strategy sets based on routing rules.
Supports complex matching logic (all_of, any_of, none_of).

Architecture:
    ActiveRegimes + RoutingRules → StrategyRouter → MatchedStrategySets

    router = StrategyRouter(routing_rules, strategy_sets)
    matched = router.route_regimes(active_regimes)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .detector import ActiveRegime
from .models import RoutingMatch, RoutingRule, StrategySetDefinition

logger = logging.getLogger(__name__)


@dataclass
class MatchedStrategySet:
    """A strategy set matched by routing rules.

    Attributes:
        strategy_set: The matched strategy set definition
        matched_by_rule: The routing rule that triggered the match
        active_regimes: List of active regimes that satisfied the rule
        match_score: Score indicating match quality (0.0-1.0)
    """
    strategy_set: StrategySetDefinition
    matched_by_rule: RoutingRule
    active_regimes: list[ActiveRegime]
    match_score: float = 1.0

    @property
    def id(self) -> str:
        """Strategy set ID."""
        return self.strategy_set.id

    @property
    def name(self) -> str:
        """Strategy set name."""
        return self.strategy_set.name or self.id

    def __repr__(self) -> str:
        regime_ids = [r.id for r in self.active_regimes]
        return f"MatchedStrategySet(id='{self.id}', regimes={regime_ids})"


class StrategyRouter:
    """Routes active regimes to strategy sets based on routing rules.

    Evaluates routing rules against active regimes to determine which
    strategy sets should be active. Supports complex matching logic:
    - all_of: All specified regimes must be active (AND)
    - any_of: At least one regime must be active (OR)
    - none_of: None of the regimes can be active (NOT)

    Example:
        >>> routing_rules = [
        ...     RoutingRule(
        ...         strategy_set_id="trend_set",
        ...         match=RoutingMatch(
        ...             all_of=["trending"],
        ...             none_of=["low_vol"]
        ...         )
        ...     )
        ... ]
        >>> router = StrategyRouter(routing_rules, strategy_sets)
        >>> matched = router.route_regimes(active_regimes)
    """

    def __init__(
        self,
        routing_rules: list[RoutingRule],
        strategy_sets: list[StrategySetDefinition]
    ):
        """Initialize router with routing rules and strategy sets.

        Args:
            routing_rules: List of routing rules
            strategy_sets: List of strategy set definitions
        """
        self.routing_rules = routing_rules
        self.strategy_sets = {ss.id: ss for ss in strategy_sets}
        logger.info(
            f"Initialized StrategyRouter with {len(routing_rules)} rules, "
            f"{len(strategy_sets)} strategy sets"
        )

    def _evaluate_match(
        self,
        match: RoutingMatch,
        active_regime_ids: set[str]
    ) -> bool:
        """Evaluate routing match against active regimes.

        Args:
            match: RoutingMatch criteria
            active_regime_ids: Set of active regime IDs

        Returns:
            True if match criteria are satisfied, False otherwise
        """
        # Check all_of: ALL specified regimes must be active
        if match.all_of is not None:
            if not all(regime_id in active_regime_ids for regime_id in match.all_of):
                logger.debug(
                    f"Match failed: all_of={match.all_of}, "
                    f"active={list(active_regime_ids)}"
                )
                return False

        # Check any_of: AT LEAST ONE regime must be active
        if match.any_of is not None:
            if not any(regime_id in active_regime_ids for regime_id in match.any_of):
                logger.debug(
                    f"Match failed: any_of={match.any_of}, "
                    f"active={list(active_regime_ids)}"
                )
                return False

        # Check none_of: NONE of the regimes can be active
        if match.none_of is not None:
            if any(regime_id in active_regime_ids for regime_id in match.none_of):
                logger.debug(
                    f"Match failed: none_of={match.none_of}, "
                    f"active={list(active_regime_ids)}"
                )
                return False

        return True

    def route_regimes(
        self,
        active_regimes: list[ActiveRegime]
    ) -> list[MatchedStrategySet]:
        """Route active regimes to strategy sets.

        Args:
            active_regimes: List of currently active regimes

        Returns:
            List of MatchedStrategySet objects
        """
        active_regime_ids = {r.id for r in active_regimes}
        matched_sets = []

        logger.info(
            f"Routing {len(active_regimes)} active regimes: "
            f"{list(active_regime_ids)}"
        )

        # Evaluate each routing rule
        for rule in self.routing_rules:
            if self._evaluate_match(rule.match, active_regime_ids):
                # Rule matched - find strategy set
                strategy_set_id = rule.strategy_set_id

                if strategy_set_id not in self.strategy_sets:
                    logger.error(
                        f"Routing rule references unknown strategy set: '{strategy_set_id}'. "
                        f"Skipping rule."
                    )
                    continue

                strategy_set = self.strategy_sets[strategy_set_id]

                # Calculate match score (for future priority logic)
                # Currently always 1.0, but could be based on number of matched regimes
                match_score = 1.0

                matched = MatchedStrategySet(
                    strategy_set=strategy_set,
                    matched_by_rule=rule,
                    active_regimes=active_regimes,
                    match_score=match_score
                )

                matched_sets.append(matched)

                logger.info(
                    f"Strategy set matched: '{strategy_set.id}' "
                    f"(rule: {rule.match})"
                )

        if not matched_sets:
            logger.warning(
                f"No strategy sets matched for regimes: {list(active_regime_ids)}"
            )

        logger.info(
            f"Routing complete: {len(matched_sets)} strategy set(s) matched"
        )

        return matched_sets

    def get_strategy_set(self, strategy_set_id: str) -> StrategySetDefinition | None:
        """Get strategy set definition by ID.

        Args:
            strategy_set_id: Strategy set identifier

        Returns:
            StrategySetDefinition if found, None otherwise
        """
        return self.strategy_sets.get(strategy_set_id)

    def get_all_strategy_sets(self) -> list[StrategySetDefinition]:
        """Get all registered strategy sets.

        Returns:
            List of all StrategySetDefinition objects
        """
        return list(self.strategy_sets.values())

    def get_routing_rules_for_regime(
        self,
        regime_id: str
    ) -> list[RoutingRule]:
        """Get all routing rules that reference a specific regime.

        Args:
            regime_id: Regime identifier

        Returns:
            List of RoutingRule objects that reference the regime
        """
        matching_rules = []

        for rule in self.routing_rules:
            match = rule.match

            # Check if regime is in any match criteria
            if match.all_of and regime_id in match.all_of:
                matching_rules.append(rule)
            elif match.any_of and regime_id in match.any_of:
                matching_rules.append(rule)
            elif match.none_of and regime_id in match.none_of:
                matching_rules.append(rule)

        return matching_rules

    def validate_routing_rules(self) -> list[str]:
        """Validate all routing rules.

        Checks that all referenced strategy sets exist.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        for i, rule in enumerate(self.routing_rules):
            if rule.strategy_set_id not in self.strategy_sets:
                errors.append(
                    f"Rule {i}: Strategy set '{rule.strategy_set_id}' not found. "
                    f"Available: {list(self.strategy_sets.keys())}"
                )

        if errors:
            logger.error(
                f"Routing validation failed with {len(errors)} error(s)"
            )
        else:
            logger.info("Routing validation passed")

        return errors
