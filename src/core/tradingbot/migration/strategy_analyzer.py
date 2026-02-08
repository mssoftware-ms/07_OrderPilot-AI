"""Strategy Analyzer.

Analyzes strategy definitions and extracts:
- Strategy metadata (name, description, type)
- Entry conditions
- Exit conditions
- Risk parameters
- Indicator dependencies

Strategy-type inference rules are loaded from config/regime_config.json.
Prepares data for JSON config generation.
"""

from __future__ import annotations

import ast
import inspect
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class IndicatorDependency:
    """Indicator used by a strategy."""

    name: str  # e.g., "rsi", "adx", "sma_fast"
    field: str = "value"  # Field accessed (e.g., "value", "upper", "lower")
    min_value: float | None = None  # Inferred min threshold
    max_value: float | None = None  # Inferred max threshold


@dataclass
class ConditionInfo:
    """Extracted condition information."""

    indicator: str
    operator: str  # "gt", "lt", "eq", "between"
    value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    compare_indicator: str | None = None  # For indicator-to-indicator comparisons


@dataclass
class StrategyAnalysis:
    """Complete analysis of a hardcoded strategy."""

    name: str
    description: str = ""
    strategy_type: str = "unknown"  # "trend", "mean_reversion", "breakout", etc.

    # Entry/Exit conditions
    entry_conditions: list[ConditionInfo] = field(default_factory=list)
    exit_conditions: list[ConditionInfo] = field(default_factory=list)

    # Risk parameters
    position_size: float = 0.02
    stop_loss: float = 0.02
    take_profit: float = 0.06

    # Indicator dependencies
    required_indicators: list[IndicatorDependency] = field(default_factory=list)

    # Regime preferences
    preferred_regimes: list[str] = field(default_factory=list)

    # Source code info
    source_file: str | None = None
    source_class: str | None = None


class StrategyAnalyzer:
    """Analyzes hardcoded strategy definitions.

    Extracts strategy logic from Python code for conversion to JSON config.

    Example:
        >>> analyzer = StrategyAnalyzer()
        >>> analysis = analyzer.analyze_strategy_class(TrendFollowingStrategy)
        >>> print(analysis.entry_conditions)
        [ConditionInfo(indicator='adx', operator='gt', value=25), ...]
    """

    def __init__(self, config=None):
        """Initialize analyzer.

        Args:
            config: Optional RegimeConfig with strategy_type_rules.
                    If None, auto-loads from config/regime_config.json.
        """
        self.analyses: dict[str, StrategyAnalysis] = {}
        self._config = config
        self._strategy_type_rules: list[dict] | None = None
        self._strategy_type_indicator_rules: list[dict] | None = None
        self._load_rules()

    def analyze_strategy_class(self, strategy_class: type) -> StrategyAnalysis:
        """Analyze a strategy class definition.

        Args:
            strategy_class: Strategy class to analyze

        Returns:
            StrategyAnalysis with extracted information
        """
        analysis = StrategyAnalysis(
            name=strategy_class.__name__,
            description=strategy_class.__doc__ or "",
            source_class=strategy_class.__name__,
        )

        # Try to get source file
        try:
            analysis.source_file = inspect.getfile(strategy_class)
        except (TypeError, OSError):
            pass

        # Analyze class attributes
        self._analyze_class_attributes(strategy_class, analysis)

        # Analyze methods (entry/exit logic)
        self._analyze_methods(strategy_class, analysis)

        # Infer strategy type
        analysis.strategy_type = self._infer_strategy_type(analysis)

        # Store analysis
        self.analyses[analysis.name] = analysis

        logger.info(f"Analyzed strategy: {analysis.name} ({analysis.strategy_type})")

        return analysis

    def analyze_strategy_definition(
        self, strategy_def: Any
    ) -> StrategyAnalysis:
        """Analyze a StrategyDefinition object.

        Args:
            strategy_def: StrategyDefinition object from catalog

        Returns:
            StrategyAnalysis with extracted information
        """
        # Extract basic info from profile
        profile = strategy_def.profile
        analysis = StrategyAnalysis(
            name=profile.name,
            description=profile.description or "",
            position_size=strategy_def.position_size_pct / 100.0,  # Convert pct to decimal
            stop_loss=strategy_def.stop_loss_pct / 100.0,  # Convert pct to decimal
            take_profit=0.06,  # Default, will be refined from exit rules
        )

        # Extract entry conditions from entry rules
        for entry_rule in strategy_def.entry_rules:
            condition = self._convert_entry_rule_to_condition(entry_rule)
            if condition:
                analysis.entry_conditions.append(condition)

                # Track indicator dependency
                if condition.indicator:
                    dep = IndicatorDependency(
                        name=condition.indicator,
                        min_value=condition.min_value,
                        max_value=condition.max_value,
                    )
                    if dep not in analysis.required_indicators:
                        analysis.required_indicators.append(dep)

        # Extract exit conditions from exit rules
        for exit_rule in strategy_def.exit_rules:
            condition = self._convert_exit_rule_to_condition(exit_rule)
            if condition:
                analysis.exit_conditions.append(condition)

                # Track indicator dependency
                if condition.indicator:
                    dep = IndicatorDependency(name=condition.indicator)
                    if dep not in analysis.required_indicators:
                        analysis.required_indicators.append(dep)

        # Extract regime preferences
        analysis.preferred_regimes = [r.value for r in profile.regimes]

        # Infer strategy type
        analysis.strategy_type = strategy_def.strategy_type.value

        # Note: Strategy-specific overrides should be defined in the
        # strategy JSON config files, not hardcoded here.

        # Store analysis
        self.analyses[analysis.name] = analysis

        logger.info(f"Analyzed strategy definition: {analysis.name}")

        return analysis

    def _convert_entry_rule_to_condition(self, entry_rule: Any) -> ConditionInfo | None:
        """Convert EntryRule to ConditionInfo.

        Args:
            entry_rule: EntryRule object

        Returns:
            ConditionInfo or None if rule cannot be converted
        """
        if not entry_rule.indicator or not entry_rule.condition:
            return None

        # Map condition strings to operators
        condition_map = {
            "above": "gt",
            "below": "lt",
            "crosses_above": "gt",
            "crosses_below": "lt",
            "aligned": "eq",
            "direction_match": "eq",
            "between": "between",
        }

        operator = condition_map.get(entry_rule.condition, "gt")

        if entry_rule.condition == "between" and entry_rule.threshold:
            # For "between" conditions like RSI between 30-70
            return ConditionInfo(
                indicator=entry_rule.indicator,
                operator="between",
                min_value=30.0,  # Default lower bound
                max_value=entry_rule.threshold,
            )
        elif entry_rule.threshold is not None:
            return ConditionInfo(
                indicator=entry_rule.indicator,
                operator=operator,
                value=entry_rule.threshold,
            )
        else:
            # No threshold means binary condition (e.g., "aligned")
            return ConditionInfo(
                indicator=entry_rule.indicator,
                operator=operator,
                value=1.0,  # Placeholder value
            )

    def _convert_exit_rule_to_condition(self, exit_rule: Any) -> ConditionInfo | None:
        """Convert ExitRule to ConditionInfo.

        Args:
            exit_rule: ExitRule object

        Returns:
            ConditionInfo or None if rule cannot be converted
        """
        if exit_rule.rule_type != "indicator":
            # Skip non-indicator rules (time, profit, trailing)
            return None

        params = exit_rule.params
        if "indicator" not in params or "condition" not in params:
            return None

        # Map condition strings to operators
        condition_map = {
            "above": "gt",
            "below": "lt",
            "crosses_above": "gt",
            "crosses_below": "lt",
            "crosses_against": "lt",
            "detected": "eq",
        }

        operator = condition_map.get(params["condition"], "lt")
        threshold = params.get("threshold")

        return ConditionInfo(
            indicator=params["indicator"],
            operator=operator,
            value=threshold if threshold is not None else 0.0,
        )

    def _analyze_class_attributes(
        self, strategy_class: type, analysis: StrategyAnalysis
    ) -> None:
        """Extract information from class attributes."""
        # Look for common attribute patterns
        for attr_name in dir(strategy_class):
            if attr_name.startswith("_"):
                continue

            try:
                attr_value = getattr(strategy_class, attr_name)

                # Position size
                if "position" in attr_name.lower() and "size" in attr_name.lower():
                    if isinstance(attr_value, (int, float)):
                        analysis.position_size = float(attr_value)

                # Stop loss
                if "stop" in attr_name.lower() and "loss" in attr_name.lower():
                    if isinstance(attr_value, (int, float)):
                        analysis.stop_loss = float(attr_value)

                # Take profit
                if "take" in attr_name.lower() and "profit" in attr_name.lower():
                    if isinstance(attr_value, (int, float)):
                        analysis.take_profit = float(attr_value)

            except (AttributeError, TypeError):
                continue

    def _analyze_methods(
        self, strategy_class: type, analysis: StrategyAnalysis
    ) -> None:
        """Analyze strategy methods to extract logic."""
        # Look for entry/exit methods
        for method_name in dir(strategy_class):
            if method_name.startswith("_"):
                continue

            try:
                method = getattr(strategy_class, method_name)
                if not callable(method):
                    continue

                # Entry logic
                if "entry" in method_name.lower() or "should_enter" in method_name.lower():
                    self._analyze_method_code(method, analysis, condition_type="entry")

                # Exit logic
                if "exit" in method_name.lower() or "should_exit" in method_name.lower():
                    self._analyze_method_code(method, analysis, condition_type="exit")

            except (AttributeError, TypeError):
                continue

    def _analyze_method_code(
        self, method: callable, analysis: StrategyAnalysis, condition_type: str
    ) -> None:
        """Analyze method source code to extract conditions.

        Uses AST parsing to extract comparison operations.
        """
        try:
            source = inspect.getsource(method)
            tree = ast.parse(source)

            # Visit AST nodes to find comparisons
            for node in ast.walk(tree):
                if isinstance(node, ast.Compare):
                    condition = self._extract_condition_from_compare(node)
                    if condition:
                        if condition_type == "entry":
                            analysis.entry_conditions.append(condition)
                        else:
                            analysis.exit_conditions.append(condition)

                        # Track indicator dependency
                        if condition.indicator:
                            dep = IndicatorDependency(
                                name=condition.indicator,
                                min_value=condition.min_value,
                                max_value=condition.max_value,
                            )
                            if dep not in analysis.required_indicators:
                                analysis.required_indicators.append(dep)

        except (OSError, TypeError, SyntaxError) as e:
            logger.debug(f"Could not parse method source: {e}")

    def _analyze_score_function(
        self, score_fn: callable, analysis: StrategyAnalysis, condition_type: str
    ) -> None:
        """Analyze a scoring function to extract logic."""
        try:
            source = inspect.getsource(score_fn)
            tree = ast.parse(source)

            # Extract conditions from comparisons
            for node in ast.walk(tree):
                if isinstance(node, ast.Compare):
                    condition = self._extract_condition_from_compare(node)
                    if condition:
                        if condition_type == "entry":
                            analysis.entry_conditions.append(condition)
                        else:
                            analysis.exit_conditions.append(condition)

        except (OSError, TypeError, SyntaxError) as e:
            logger.debug(f"Could not parse score function: {e}")

    def _extract_condition_from_compare(self, node: ast.Compare) -> ConditionInfo | None:
        """Extract condition info from AST Compare node.

        Handles patterns like:
        - features.rsi > 50
        - features.adx < 20
        - 30 < features.rsi < 70
        """
        if not node.ops or not node.comparators:
            return None

        # Get left side (usually attribute access like features.rsi)
        left_name = self._extract_attribute_name(node.left)
        if not left_name:
            return None

        # Get operator
        op = node.ops[0]
        operator = self._ast_op_to_string(op)
        if not operator:
            return None

        # Get right side (value or another attribute)
        right = node.comparators[0]

        if isinstance(right, ast.Constant):
            # Comparison to constant: features.rsi > 50
            return ConditionInfo(
                indicator=left_name,
                operator=operator,
                value=float(right.value) if isinstance(right.value, (int, float)) else None,
            )

        elif isinstance(right, ast.Attribute):
            # Comparison to another indicator: features.sma_fast > features.sma_slow
            right_name = self._extract_attribute_name(right)
            return ConditionInfo(
                indicator=left_name, operator=operator, compare_indicator=right_name
            )

        return None

    def _extract_attribute_name(self, node: ast.AST) -> str | None:
        """Extract attribute name from AST node.

        Handles: features.rsi → "rsi"
        """
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _ast_op_to_string(self, op: ast.cmpop) -> str | None:
        """Convert AST comparison operator to string."""
        op_map = {
            ast.Gt: "gt",
            ast.Lt: "lt",
            ast.GtE: "gte",
            ast.LtE: "lte",
            ast.Eq: "eq",
            ast.NotEq: "neq",
        }
        return op_map.get(type(op))

    def _load_rules(self) -> None:
        """Load strategy type inference rules from config."""
        # Try to get rules from provided config
        if self._config is not None:
            self._strategy_type_rules = getattr(
                self._config, "strategy_type_rules", []
            )
            self._strategy_type_indicator_rules = getattr(
                self._config, "strategy_type_indicator_rules", []
            )
            if self._strategy_type_rules:
                logger.info(
                    f"Loaded {len(self._strategy_type_rules)} strategy type rules from config"
                )
                return

        # Auto-load from regime_config.json
        try:
            from src.core.trading_bot.regime_result import RegimeConfig

            config = RegimeConfig.find_and_load()
            self._strategy_type_rules = config.strategy_type_rules
            self._strategy_type_indicator_rules = config.strategy_type_indicator_rules
            logger.info(
                f"Auto-loaded {len(self._strategy_type_rules)} strategy type rules"
            )
        except Exception as e:
            logger.debug(f"Could not load strategy type rules: {e}")
            self._strategy_type_rules = []
            self._strategy_type_indicator_rules = []

    def _infer_strategy_type(self, analysis: StrategyAnalysis) -> str:
        """Infer strategy type from name and conditions.

        Uses rules from config/regime_config.json if available,
        otherwise falls back to built-in defaults.
        """
        name_lower = analysis.name.lower()

        # 1. Try JSON-based name pattern matching
        if self._strategy_type_rules:
            for rule in self._strategy_type_rules:
                pattern = rule.get("pattern", "")
                strategy_type = rule.get("type", "")
                if pattern and strategy_type:
                    if re.search(pattern, name_lower):
                        return strategy_type
        else:
            # Fallback: built-in pattern matching
            if "trend" in name_lower:
                return "trend_following"
            elif "mean" in name_lower or "reversion" in name_lower:
                return "mean_reversion"
            elif "breakout" in name_lower:
                return "breakout"
            elif "momentum" in name_lower:
                return "momentum"
            elif "range" in name_lower:
                return "range_trading"

        # 2. Try JSON-based indicator matching
        if self._strategy_type_indicator_rules:
            for rule in self._strategy_type_indicator_rules:
                required_indicators = rule.get("indicators", [])
                strategy_type = rule.get("type", "")

                if not required_indicators or not strategy_type:
                    continue

                # Check if all required indicators are used
                has_all = all(
                    any(c.indicator == ind for c in analysis.entry_conditions)
                    for ind in required_indicators
                )

                if has_all:
                    # Check optional RSI value condition
                    rsi_value_lt = rule.get("rsi_value_lt")
                    if rsi_value_lt is not None:
                        rsi_conditions = [
                            c
                            for c in analysis.entry_conditions
                            if c.indicator == "rsi"
                        ]
                        if (
                            rsi_conditions
                            and rsi_conditions[0].value
                            and rsi_conditions[0].value < rsi_value_lt
                        ):
                            return strategy_type
                    else:
                        return strategy_type
        else:
            # Fallback: built-in indicator matching
            uses_adx = any(
                c.indicator == "adx" for c in analysis.entry_conditions
            )
            uses_rsi = any(
                c.indicator == "rsi" for c in analysis.entry_conditions
            )

            if uses_adx and uses_rsi:
                return "trend_momentum"
            elif uses_adx:
                return "trend_following"
            elif uses_rsi:
                rsi_conditions = [
                    c for c in analysis.entry_conditions if c.indicator == "rsi"
                ]
                if (
                    rsi_conditions
                    and rsi_conditions[0].value
                    and rsi_conditions[0].value < 40
                ):
                    return "mean_reversion"

        return "unknown"

    def list_analyses(self) -> list[str]:
        """List all analyzed strategy names.

        Returns:
            List of strategy names
        """
        return list(self.analyses.keys())

    def get_analysis(self, strategy_name: str) -> StrategyAnalysis | None:
        """Get analysis for a specific strategy.

        Args:
            strategy_name: Name of strategy

        Returns:
            StrategyAnalysis or None if not found
        """
        return self.analyses.get(strategy_name)

    def print_analysis(self, strategy_name: str) -> None:
        """Print analysis in human-readable format.

        Args:
            strategy_name: Name of strategy to print
        """
        analysis = self.get_analysis(strategy_name)
        if not analysis:
            print(f"Strategy '{strategy_name}' not found")
            return

        print("=" * 80)
        print(f"Strategy Analysis: {analysis.name}")
        print("=" * 80)
        print()

        print(f"Type: {analysis.strategy_type}")
        print(f"Description: {analysis.description[:100]}...")
        print()

        print("Entry Conditions:")
        for cond in analysis.entry_conditions:
            if cond.compare_indicator:
                print(f"  - {cond.indicator} {cond.operator} {cond.compare_indicator}")
            else:
                print(f"  - {cond.indicator} {cond.operator} {cond.value}")
        print()

        print("Exit Conditions:")
        for cond in analysis.exit_conditions:
            if cond.compare_indicator:
                print(f"  - {cond.indicator} {cond.operator} {cond.compare_indicator}")
            else:
                print(f"  - {cond.indicator} {cond.operator} {cond.value}")
        print()

        print("Risk Parameters:")
        print(f"  - Position Size: {analysis.position_size * 100:.1f}%")
        print(f"  - Stop Loss: {analysis.stop_loss * 100:.1f}%")
        print(f"  - Take Profit: {analysis.take_profit * 100:.1f}%")
        print()

        print("Required Indicators:")
        for ind in analysis.required_indicators:
            range_str = ""
            if ind.min_value or ind.max_value:
                range_str = f" (range: {ind.min_value or '?'} - {ind.max_value or '?'})"
            print(f"  - {ind.name}{range_str}")
        print()

        if analysis.source_file:
            print(f"Source: {analysis.source_file}")
        if analysis.source_class:
            print(f"Class: {analysis.source_class}")
