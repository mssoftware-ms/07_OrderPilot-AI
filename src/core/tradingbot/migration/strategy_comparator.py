"""Strategy Comparison Framework.

Compares JSON configurations against hardcoded strategy definitions
to verify equivalence and detect differences.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..config.models import Condition, StrategyDefinition, TradingBotConfig
from ..strategy_catalog import StrategyCatalog
from .strategy_analyzer import ConditionInfo, StrategyAnalysis, StrategyAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class ConditionDiff:
    """Difference in a single condition."""

    field: str  # "entry" or "exit"
    index: int  # Condition index
    json_condition: str  # JSON representation
    hardcoded_condition: str  # Hardcoded representation
    difference_type: str  # "missing", "extra", "different_operator", "different_threshold"
    severity: str  # "major", "minor"


@dataclass
class ParameterDiff:
    """Difference in a parameter."""

    parameter_name: str
    json_value: Any
    hardcoded_value: Any
    difference_pct: float | None = None  # Percentage difference for numeric values


@dataclass
class ComparisonResult:
    """Complete comparison result."""

    # Required fields (no defaults)
    strategy_name: str
    is_equivalent: bool
    overall_similarity: float  # 0.0 to 1.0

    # Entry/Exit condition matching
    entry_conditions_match: bool
    exit_conditions_match: bool

    # Risk parameter matching
    risk_parameters_match: bool

    # Indicator dependencies matching
    indicators_match: bool

    # Regime preferences matching
    regimes_match: bool

    # Optional fields (with defaults)
    condition_diffs: list[ConditionDiff] = field(default_factory=list)
    parameter_diffs: list[ParameterDiff] = field(default_factory=list)
    missing_indicators: list[str] = field(default_factory=list)
    extra_indicators: list[str] = field(default_factory=list)
    regime_diffs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def has_major_differences(self) -> bool:
        """Check if there are major differences that affect behavior."""
        # Major differences: entry/exit logic or risk parameters differ significantly
        if not self.entry_conditions_match or not self.exit_conditions_match:
            return True

        if not self.risk_parameters_match:
            # Check if risk parameter differences are significant
            for diff in self.parameter_diffs:
                if diff.difference_pct and diff.difference_pct > 10.0:
                    return True

        return False

    def has_minor_differences(self) -> bool:
        """Check if there are minor differences (cosmetic or non-critical)."""
        return (
            len(self.condition_diffs) > 0
            or len(self.parameter_diffs) > 0
            or len(self.missing_indicators) > 0
            or len(self.extra_indicators) > 0
        )


class StrategyComparator:
    """Compares JSON configurations against hardcoded strategies.

    Validates that JSON configs produce equivalent behavior to hardcoded
    strategy definitions.

    Example:
        >>> comparator = StrategyComparator()
        >>> result = comparator.compare_json_to_hardcoded(
        ...     json_config=config,
        ...     strategy_id="trend_following_conservative",
        ...     hardcoded_strategy_name="trend_following_conservative"
        ... )
        >>> print(f"Equivalent: {result.is_equivalent}")
        >>> print(f"Similarity: {result.overall_similarity:.1%}")
    """

    def __init__(self):
        """Initialize comparator."""
        self.catalog = StrategyCatalog()
        self.analyzer = StrategyAnalyzer()

    def compare_json_to_hardcoded(
        self,
        json_config: TradingBotConfig,
        strategy_id: str,
        hardcoded_strategy_name: str,
    ) -> ComparisonResult:
        """Compare JSON config strategy against hardcoded strategy.

        Args:
            json_config: Loaded JSON configuration
            strategy_id: Strategy ID in JSON config
            hardcoded_strategy_name: Name of hardcoded strategy in catalog

        Returns:
            ComparisonResult with detailed differences
        """
        # Get JSON strategy
        json_strategy = self._find_json_strategy(json_config, strategy_id)
        if json_strategy is None:
            raise ValueError(f"Strategy '{strategy_id}' not found in JSON config")

        # Get hardcoded strategy
        hardcoded_def = self.catalog.get_strategy(hardcoded_strategy_name)
        if hardcoded_def is None:
            raise ValueError(
                f"Hardcoded strategy '{hardcoded_strategy_name}' not found in catalog"
            )

        # Analyze hardcoded strategy
        hardcoded_analysis = self.analyzer.analyze_strategy_definition(hardcoded_def)

        # Create result
        result = ComparisonResult(
            strategy_name=strategy_id,
            is_equivalent=False,  # Will be determined
            overall_similarity=0.0,  # Will be calculated
            entry_conditions_match=False,
            exit_conditions_match=False,
            risk_parameters_match=False,
            indicators_match=False,
            regimes_match=False,
        )

        # Compare entry conditions
        result.entry_conditions_match, entry_diffs = self._compare_conditions(
            json_strategy.entry, hardcoded_analysis.entry_conditions, "entry"
        )
        result.condition_diffs.extend(entry_diffs)

        # Compare exit conditions
        result.exit_conditions_match, exit_diffs = self._compare_conditions(
            json_strategy.exit, hardcoded_analysis.exit_conditions, "exit"
        )
        result.condition_diffs.extend(exit_diffs)

        # Compare risk parameters
        result.risk_parameters_match, param_diffs = self._compare_risk_parameters(
            json_strategy.risk, hardcoded_analysis
        )
        result.parameter_diffs.extend(param_diffs)

        # Compare indicators
        result.indicators_match, missing, extra = self._compare_indicators(
            json_config, hardcoded_analysis
        )
        result.missing_indicators.extend(missing)
        result.extra_indicators.extend(extra)

        # Compare regimes (if available)
        result.regimes_match, regime_diffs = self._compare_regimes(
            json_config, hardcoded_analysis
        )
        result.regime_diffs.extend(regime_diffs)

        # Calculate overall similarity
        result.overall_similarity = self._calculate_similarity(result)

        # Determine equivalence
        result.is_equivalent = (
            result.entry_conditions_match
            and result.exit_conditions_match
            and result.risk_parameters_match
            and not result.has_major_differences()
        )

        # Add warnings and notes
        self._add_warnings_and_notes(result)

        return result

    def _find_json_strategy(
        self, json_config: TradingBotConfig, strategy_id: str
    ) -> StrategyDefinition | None:
        """Find strategy in JSON config by ID."""
        for strategy in json_config.strategies:
            if strategy.id == strategy_id:
                return strategy
        return None

    def _compare_conditions(
        self,
        json_condition_group: dict[str, list[Condition]] | Any,
        hardcoded_conditions: list[ConditionInfo],
        field_name: str,
    ) -> tuple[bool, list[ConditionDiff]]:
        """Compare condition groups (entry or exit).

        Args:
            json_condition_group: JSON condition group (ConditionGroup model or dict)
            hardcoded_conditions: List of hardcoded conditions
            field_name: "entry" or "exit"

        Returns:
            Tuple of (conditions_match, list of differences)
        """
        diffs = []

        # Handle None case
        if json_condition_group is None:
            json_conditions = []
        # Handle Pydantic ConditionGroup model
        elif hasattr(json_condition_group, "all") or hasattr(json_condition_group, "any"):
            json_conditions = getattr(json_condition_group, "all", None) or getattr(json_condition_group, "any", None) or []
        # Handle dict format
        else:
            json_conditions = json_condition_group.get("all", []) or json_condition_group.get("any", [])

        # Quick length check
        if len(json_conditions) != len(hardcoded_conditions):
            diffs.append(
                ConditionDiff(
                    field=field_name,
                    index=-1,
                    json_condition=f"{len(json_conditions)} conditions",
                    hardcoded_condition=f"{len(hardcoded_conditions)} conditions",
                    difference_type="different_count",
                    severity="major",
                )
            )

        # Compare each condition
        max_len = max(len(json_conditions), len(hardcoded_conditions))
        for i in range(max_len):
            if i >= len(json_conditions):
                # Missing in JSON
                hc = hardcoded_conditions[i]
                diffs.append(
                    ConditionDiff(
                        field=field_name,
                        index=i,
                        json_condition="(missing)",
                        hardcoded_condition=f"{hc.indicator} {hc.operator} {hc.value}",
                        difference_type="missing",
                        severity="major",
                    )
                )
            elif i >= len(hardcoded_conditions):
                # Extra in JSON
                jc = json_conditions[i]
                diffs.append(
                    ConditionDiff(
                        field=field_name,
                        index=i,
                        json_condition=self._format_json_condition(jc),
                        hardcoded_condition="(not in hardcoded)",
                        difference_type="extra",
                        severity="major",
                    )
                )
            else:
                # Compare conditions
                jc = json_conditions[i]
                hc = hardcoded_conditions[i]
                cond_diff = self._compare_single_condition(jc, hc, field_name, i)
                if cond_diff:
                    diffs.append(cond_diff)

        conditions_match = len(diffs) == 0
        return conditions_match, diffs

    def _compare_single_condition(
        self, json_cond: Condition, hardcoded_cond: ConditionInfo, field: str, index: int
    ) -> ConditionDiff | None:
        """Compare a single condition.

        Returns:
            ConditionDiff if conditions differ, None if they match
        """
        # Compare indicator
        json_indicator = json_cond.left.indicator_id
        if json_indicator != hardcoded_cond.indicator:
            return ConditionDiff(
                field=field,
                index=index,
                json_condition=self._format_json_condition(json_cond),
                hardcoded_condition=f"{hardcoded_cond.indicator} {hardcoded_cond.operator} {hardcoded_cond.value}",
                difference_type="different_indicator",
                severity="major",
            )

        # Compare operator
        if json_cond.op != hardcoded_cond.operator:
            return ConditionDiff(
                field=field,
                index=index,
                json_condition=self._format_json_condition(json_cond),
                hardcoded_condition=f"{hardcoded_cond.indicator} {hardcoded_cond.operator} {hardcoded_cond.value}",
                difference_type="different_operator",
                severity="major",
            )

        # Compare value
        if hasattr(json_cond.right, "value") and json_cond.right.value is not None:
            json_value = json_cond.right.value
            hardcoded_value = hardcoded_cond.value

            if json_value != hardcoded_value:
                # Allow small float differences
                if (
                    isinstance(json_value, float)
                    and isinstance(hardcoded_value, float)
                    and abs(json_value - hardcoded_value) < 0.01
                ):
                    return None  # Close enough

                return ConditionDiff(
                    field=field,
                    index=index,
                    json_condition=self._format_json_condition(json_cond),
                    hardcoded_condition=f"{hardcoded_cond.indicator} {hardcoded_cond.operator} {hardcoded_cond.value}",
                    difference_type="different_threshold",
                    severity="minor" if abs(json_value - hardcoded_value) < 5 else "major",
                )

        return None

    def _compare_risk_parameters(
        self, json_risk: dict, hardcoded_analysis: StrategyAnalysis
    ) -> tuple[bool, list[ParameterDiff]]:
        """Compare risk parameters.

        Returns:
            Tuple of (parameters_match, list of differences)
        """
        diffs = []

        # Position size
        json_pos_size = json_risk.position_size or 0.02
        if abs(json_pos_size - hardcoded_analysis.position_size) > 0.001:
            pct_diff = (
                abs(json_pos_size - hardcoded_analysis.position_size)
                / hardcoded_analysis.position_size
                * 100
            )
            diffs.append(
                ParameterDiff(
                    parameter_name="position_size",
                    json_value=json_pos_size,
                    hardcoded_value=hardcoded_analysis.position_size,
                    difference_pct=pct_diff,
                )
            )

        # Stop loss
        json_stop_loss = json_risk.stop_loss or 0.02
        if abs(json_stop_loss - hardcoded_analysis.stop_loss) > 0.001:
            pct_diff = (
                abs(json_stop_loss - hardcoded_analysis.stop_loss)
                / hardcoded_analysis.stop_loss
                * 100
            )
            diffs.append(
                ParameterDiff(
                    parameter_name="stop_loss",
                    json_value=json_stop_loss,
                    hardcoded_value=hardcoded_analysis.stop_loss,
                    difference_pct=pct_diff,
                )
            )

        # Take profit
        json_take_profit = json_risk.take_profit or 0.06
        if abs(json_take_profit - hardcoded_analysis.take_profit) > 0.001:
            pct_diff = (
                abs(json_take_profit - hardcoded_analysis.take_profit)
                / hardcoded_analysis.take_profit
                * 100
            )
            diffs.append(
                ParameterDiff(
                    parameter_name="take_profit",
                    json_value=json_take_profit,
                    hardcoded_value=hardcoded_analysis.take_profit,
                    difference_pct=pct_diff,
                )
            )

        parameters_match = len(diffs) == 0
        return parameters_match, diffs

    def _compare_indicators(
        self, json_config: TradingBotConfig, hardcoded_analysis: StrategyAnalysis
    ) -> tuple[bool, list[str], list[str]]:
        """Compare indicator dependencies.

        Returns:
            Tuple of (indicators_match, missing_indicators, extra_indicators)
        """
        json_indicators = {ind.id for ind in json_config.indicators}
        hardcoded_indicators = {dep.name for dep in hardcoded_analysis.required_indicators}

        missing = list(hardcoded_indicators - json_indicators)
        extra = list(json_indicators - hardcoded_indicators)

        indicators_match = len(missing) == 0 and len(extra) == 0
        return indicators_match, missing, extra

    def _compare_regimes(
        self, json_config: TradingBotConfig, hardcoded_analysis: StrategyAnalysis
    ) -> tuple[bool, list[str]]:
        """Compare regime preferences.

        Returns:
            Tuple of (regimes_match, list of differences)
        """
        diffs = []

        # Extract regime IDs from JSON config
        json_regimes = {regime.id for regime in json_config.regimes}
        hardcoded_regimes = set(hardcoded_analysis.preferred_regimes)

        missing = hardcoded_regimes - json_regimes
        extra = json_regimes - hardcoded_regimes

        if missing:
            diffs.append(f"Missing regimes: {', '.join(missing)}")
        if extra:
            diffs.append(f"Extra regimes: {', '.join(extra)}")

        regimes_match = len(diffs) == 0
        return regimes_match, diffs

    def _calculate_similarity(self, result: ComparisonResult) -> float:
        """Calculate overall similarity score (0.0 to 1.0).

        Weighted scoring:
        - Entry conditions: 30%
        - Exit conditions: 30%
        - Risk parameters: 25%
        - Indicators: 10%
        - Regimes: 5%
        """
        score = 0.0

        # Entry conditions (30%)
        if result.entry_conditions_match:
            score += 0.30
        else:
            # Partial credit based on number of matching conditions
            entry_diffs = [d for d in result.condition_diffs if d.field == "entry"]
            if entry_diffs:
                # Rough estimate of partial match
                score += 0.30 * (1.0 - min(len(entry_diffs) / 5.0, 1.0))

        # Exit conditions (30%)
        if result.exit_conditions_match:
            score += 0.30
        else:
            exit_diffs = [d for d in result.condition_diffs if d.field == "exit"]
            if exit_diffs:
                score += 0.30 * (1.0 - min(len(exit_diffs) / 5.0, 1.0))

        # Risk parameters (25%)
        if result.risk_parameters_match:
            score += 0.25
        else:
            # Partial credit if differences are small
            avg_diff_pct = (
                sum(d.difference_pct or 0 for d in result.parameter_diffs)
                / len(result.parameter_diffs)
                if result.parameter_diffs
                else 0
            )
            score += 0.25 * max(0, 1.0 - avg_diff_pct / 100.0)

        # Indicators (10%)
        if result.indicators_match:
            score += 0.10
        else:
            total_indicators = len(result.missing_indicators) + len(result.extra_indicators)
            if total_indicators > 0:
                score += 0.10 * (1.0 - min(total_indicators / 5.0, 1.0))

        # Regimes (5%)
        if result.regimes_match:
            score += 0.05

        return min(score, 1.0)

    def _format_json_condition(self, cond: Condition) -> str:
        """Format JSON condition for display."""
        left = cond.left.indicator_id
        op = cond.op

        if hasattr(cond.right, "value") and cond.right.value is not None:
            right = str(cond.right.value)
        elif hasattr(cond.right, "indicator_id") and cond.right.indicator_id is not None:
            right = cond.right.indicator_id
        else:
            right = "(unknown)"

        return f"{left} {op} {right}"

    def _add_warnings_and_notes(self, result: ComparisonResult) -> None:
        """Add warnings and notes to result."""
        # Major differences warning
        if result.has_major_differences():
            result.warnings.append(
                "Major differences detected - strategy behavior may differ significantly"
            )

        # Risk parameter warnings
        for diff in result.parameter_diffs:
            if diff.difference_pct and diff.difference_pct > 20:
                result.warnings.append(
                    f"{diff.parameter_name} differs by {diff.difference_pct:.1f}% "
                    f"({diff.json_value} vs {diff.hardcoded_value})"
                )

        # Condition count mismatch
        entry_count_diff = [
            d for d in result.condition_diffs if d.difference_type == "different_count"
        ]
        if entry_count_diff:
            result.warnings.append("Entry/exit condition count mismatch")

        # Notes for minor differences
        if result.has_minor_differences() and not result.has_major_differences():
            result.notes.append(
                "Minor differences found - review before production deployment"
            )

        # Equivalence note
        if result.is_equivalent:
            result.notes.append("Strategies are functionally equivalent")
        elif result.overall_similarity > 0.90:
            result.notes.append("Strategies are very similar (>90% match)")
        elif result.overall_similarity > 0.75:
            result.notes.append("Strategies are somewhat similar (>75% match)")
        else:
            result.notes.append("Strategies differ significantly (<75% match)")
