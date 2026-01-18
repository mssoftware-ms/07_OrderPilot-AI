"""JSON Config Generator from Hardcoded Strategies.

Converts analyzed hardcoded strategies to JSON configuration format.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .strategy_analyzer import ConditionInfo, StrategyAnalysis

logger = logging.getLogger(__name__)


class JSONConfigGenerator:
    """Generates JSON config from strategy analysis.

    Converts StrategyAnalysis objects to JSON configuration format
    compatible with the TradingBotConfig schema.

    Example:
        >>> generator = JSONConfigGenerator()
        >>> json_config = generator.generate_from_analysis(analysis)
        >>> generator.save_config(json_config, "output.json")
    """

    def __init__(self, schema_version: str = "1.0.0"):
        """Initialize generator.

        Args:
            schema_version: Schema version for generated configs
        """
        self.schema_version = schema_version

    def generate_from_analysis(
        self,
        analysis: StrategyAnalysis,
        include_regime: bool = True,
        include_strategy_set: bool = True,
    ) -> dict[str, Any]:
        """Generate JSON config from strategy analysis.

        Args:
            analysis: Strategy analysis to convert
            include_regime: Include auto-generated regime
            include_strategy_set: Include strategy set and routing

        Returns:
            JSON config dict
        """
        config: dict[str, Any] = {
            "schema_version": self.schema_version,
            "indicators": [],
            "regimes": [],
            "strategies": [],
            "strategy_sets": [],
            "routing": [],
        }

        # Generate indicators
        config["indicators"] = self._generate_indicators(analysis)

        # Generate regime (if requested)
        if include_regime:
            regime = self._generate_regime_from_strategy(analysis)
            if regime:
                config["regimes"].append(regime)

        # Generate strategy
        strategy = self._generate_strategy(analysis)
        config["strategies"].append(strategy)

        # Generate strategy set (if requested)
        if include_strategy_set:
            strategy_set = self._generate_strategy_set(analysis)
            config["strategy_sets"].append(strategy_set)

            # Generate routing
            if config["regimes"]:
                routing = self._generate_routing(analysis, config["regimes"][0]["id"])
                config["routing"].append(routing)

        logger.info(f"Generated JSON config for strategy: {analysis.name}")

        return config

    def generate_from_multiple_analyses(
        self, analyses: list[StrategyAnalysis]
    ) -> dict[str, Any]:
        """Generate combined JSON config from multiple strategies.

        Args:
            analyses: List of strategy analyses

        Returns:
            Combined JSON config dict
        """
        config: dict[str, Any] = {
            "schema_version": self.schema_version,
            "indicators": [],
            "regimes": [],
            "strategies": [],
            "strategy_sets": [],
            "routing": [],
        }

        # Collect all unique indicators
        indicator_ids = set()
        for analysis in analyses:
            for indicator in self._generate_indicators(analysis):
                indicator_id = indicator["id"]
                if indicator_id not in indicator_ids:
                    config["indicators"].append(indicator)
                    indicator_ids.add(indicator_id)

        # Generate regime for each strategy type
        regime_by_type: dict[str, dict] = {}
        for analysis in analyses:
            if analysis.strategy_type not in regime_by_type:
                regime = self._generate_regime_from_strategy(analysis)
                if regime:
                    regime_by_type[analysis.strategy_type] = regime
                    config["regimes"].append(regime)

        # Generate strategies
        for analysis in analyses:
            strategy = self._generate_strategy(analysis)
            config["strategies"].append(strategy)

        # Generate strategy sets (one per strategy type)
        strategy_sets_by_type: dict[str, dict] = {}
        for analysis in analyses:
            if analysis.strategy_type not in strategy_sets_by_type:
                strategy_set = {
                    "id": f"set_{analysis.strategy_type}",
                    "name": f"{analysis.strategy_type.replace('_', ' ').title()} Strategies",
                    "strategies": [],
                }
                strategy_sets_by_type[analysis.strategy_type] = strategy_set
                config["strategy_sets"].append(strategy_set)

            # Add strategy to set
            strategy_sets_by_type[analysis.strategy_type]["strategies"].append(
                {"strategy_id": self._strategy_id_from_name(analysis.name)}
            )

        # Generate routing
        for strategy_type, regime in regime_by_type.items():
            strategy_set = strategy_sets_by_type.get(strategy_type)
            if strategy_set:
                routing = {
                    "strategy_set_id": strategy_set["id"],
                    "match": {"all_of": [regime["id"]]},
                }
                config["routing"].append(routing)

        logger.info(f"Generated combined JSON config for {len(analyses)} strategies")

        return config

    def _generate_indicators(self, analysis: StrategyAnalysis) -> list[dict[str, Any]]:
        """Generate indicator definitions from analysis.

        Args:
            analysis: Strategy analysis

        Returns:
            List of indicator definitions
        """
        indicators = []
        seen_indicator_ids = set()  # Track by ID, not name

        for dep in analysis.required_indicators:
            indicator = self._create_indicator_definition(dep.name)
            if indicator and indicator["id"] not in seen_indicator_ids:
                indicators.append(indicator)
                seen_indicator_ids.add(indicator["id"])

        return indicators

    def _create_indicator_definition(self, indicator_name: str) -> dict[str, Any] | None:
        """Create indicator definition from name.

        Args:
            indicator_name: Indicator name (e.g., "rsi", "adx", "sma_fast")

        Returns:
            Indicator definition or None
        """
        # Map common indicator names to types and params
        # NOTE: Types must match IndicatorType enum in models.py (UPPERCASE)
        indicator_map = {
            # RSI
            "rsi": {"type": "RSI", "params": {"period": 14}},
            "rsi_14": {"type": "RSI", "params": {"period": 14}},
            # ADX
            "adx": {"type": "ADX", "params": {"period": 14}},
            "adx_14": {"type": "ADX", "params": {"period": 14}},
            # SMA
            "sma_fast": {"type": "SMA", "params": {"period": 20}},
            "sma_20": {"type": "SMA", "params": {"period": 20}},
            "sma_slow": {"type": "SMA", "params": {"period": 50}},
            "sma_50": {"type": "SMA", "params": {"period": 50}},
            # EMA
            "ema_fast": {"type": "EMA", "params": {"period": 12}},
            "ema_12": {"type": "EMA", "params": {"period": 12}},
            "ema_slow": {"type": "EMA", "params": {"period": 26}},
            "ema_26": {"type": "EMA", "params": {"period": 26}},
            # MACD
            "macd": {"type": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
            # Bollinger Bands
            "bb_upper": {"type": "BBANDS", "params": {"period": 20, "std": 2}},
            "bb_middle": {"type": "BBANDS", "params": {"period": 20, "std": 2}},
            "bb_lower": {"type": "BBANDS", "params": {"period": 20, "std": 2}},
            "bb_width": {"type": "BBANDS", "params": {"period": 20, "std": 2}},
            # ATR
            "atr": {"type": "ATR", "params": {"period": 14}},
            "atr_14": {"type": "ATR", "params": {"period": 14}},
            # Stochastic
            "stoch_k": {"type": "STOCH", "params": {"k_period": 14, "d_period": 3}},
            "stoch_d": {"type": "STOCH", "params": {"k_period": 14, "d_period": 3}},
            # Volume
            "volume": {"type": "Volume", "params": {}},
            "volume_ratio": {"type": "Volume", "params": {}},
            # Custom/Derived Indicators (map to base indicator type)
            "sma_alignment": {"type": "SMA", "params": {"period": 20}},  # Trend alignment from SMA
            "macd_hist": {"type": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},  # MACD histogram
            "bb_pct": {"type": "BBANDS", "params": {"period": 20, "std": 2}},  # BB position %
            "di_spread": {"type": "ADX", "params": {"period": 14}},  # DI+/DI- spread
            "rsi_momentum": {"type": "RSI", "params": {"period": 14}},  # RSI rate of change
            "rsi_divergence": {"type": "RSI", "params": {"period": 14}},  # RSI divergence
            "sma_distance": {"type": "SMA", "params": {"period": 20}},  # Distance from SMA
            "price_vs_sma20": {"type": "SMA", "params": {"period": 20}},  # Price vs SMA20
            "price_position": {"type": "SMA", "params": {"period": 20}},  # Price position
            "atr_ratio": {"type": "ATR", "params": {"period": 14}},  # ATR as % of price
        }

        if indicator_name not in indicator_map:
            logger.warning(f"Unknown indicator: {indicator_name}")
            return None

        info = indicator_map[indicator_name]

        # Use normalized indicator ID
        indicator_id = self._normalize_indicator_id(indicator_name)

        return {"id": indicator_id, "type": info["type"], "params": info["params"]}

    def _generate_regime_from_strategy(
        self, analysis: StrategyAnalysis
    ) -> dict[str, Any] | None:
        """Generate regime definition from strategy entry conditions.

        Args:
            analysis: Strategy analysis

        Returns:
            Regime definition or None
        """
        if not analysis.entry_conditions:
            return None

        regime_id = f"{analysis.strategy_type}_regime"
        regime_name = f"{analysis.strategy_type.replace('_', ' ').title()} Market"

        # Convert entry conditions to regime conditions
        conditions = self._convert_conditions_to_json(analysis.entry_conditions)

        return {
            "id": regime_id,
            "name": regime_name,
            "conditions": {"all": conditions},
            "priority": 10,
            "scope": "entry",
        }

    def _generate_strategy(self, analysis: StrategyAnalysis) -> dict[str, Any]:
        """Generate strategy definition.

        Args:
            analysis: Strategy analysis

        Returns:
            Strategy definition
        """
        strategy_id = self._strategy_id_from_name(analysis.name)

        # Convert conditions
        entry_conditions = self._convert_conditions_to_json(analysis.entry_conditions)
        exit_conditions = self._convert_conditions_to_json(analysis.exit_conditions)

        return {
            "id": strategy_id,
            "name": analysis.name,
            "entry": {"all": entry_conditions} if entry_conditions else {"all": []},
            "exit": {"all": exit_conditions} if exit_conditions else {"all": []},
            "risk": {
                "position_size": analysis.position_size,
                "stop_loss": analysis.stop_loss,
                "take_profit": analysis.take_profit,
            },
        }

    def _generate_strategy_set(self, analysis: StrategyAnalysis) -> dict[str, Any]:
        """Generate strategy set definition.

        Args:
            analysis: Strategy analysis

        Returns:
            Strategy set definition
        """
        strategy_id = self._strategy_id_from_name(analysis.name)

        return {
            "id": f"set_{strategy_id}",
            "name": f"{analysis.name} Set",
            "strategies": [{"strategy_id": strategy_id}],
        }

    def _generate_routing(self, analysis: StrategyAnalysis, regime_id: str) -> dict[str, Any]:
        """Generate routing rule.

        Args:
            analysis: Strategy analysis
            regime_id: Regime ID to route to

        Returns:
            Routing rule
        """
        strategy_id = self._strategy_id_from_name(analysis.name)

        return {
            "strategy_set_id": f"set_{strategy_id}",
            "match": {"all_of": [regime_id]},
        }

    def _convert_conditions_to_json(
        self, conditions: list[ConditionInfo]
    ) -> list[dict[str, Any]]:
        """Convert ConditionInfo list to JSON condition format.

        Args:
            conditions: List of condition info

        Returns:
            List of JSON condition dicts
        """
        json_conditions = []

        for cond in conditions:
            json_cond: dict[str, Any] = {
                "left": {"indicator_id": self._normalize_indicator_id(cond.indicator), "field": "value"}
            }

            # Operator
            json_cond["op"] = cond.operator

            # Right side
            if cond.compare_indicator:
                # Indicator-to-indicator comparison
                json_cond["right"] = {
                    "indicator_id": self._normalize_indicator_id(cond.compare_indicator),
                    "field": "value",
                }
            elif cond.min_value is not None and cond.max_value is not None:
                # Between operator
                json_cond["op"] = "between"
                json_cond["right"] = {"min": cond.min_value, "max": cond.max_value}
            elif cond.value is not None:
                # Constant value comparison
                json_cond["right"] = {"value": cond.value}
            else:
                # Skip invalid condition
                continue

            json_conditions.append(json_cond)

        return json_conditions

    def _normalize_indicator_id(self, indicator_name: str) -> str:
        """Normalize indicator name to standard ID.

        Args:
            indicator_name: Raw indicator name

        Returns:
            Normalized indicator ID
        """
        # Map to standard IDs (hardcoded reference → JSON ID)
        id_map = {
            # RSI
            "rsi": "rsi14",
            "rsi_14": "rsi14",
            # ADX
            "adx": "adx14",
            "adx_14": "adx14",
            # SMA
            "sma_fast": "sma20",
            "sma_20": "sma20",
            "sma_slow": "sma50",
            "sma_50": "sma50",
            # EMA
            "ema_fast": "ema12",
            "ema_12": "ema12",
            "ema_slow": "ema26",
            "ema_26": "ema26",
            # ATR
            "atr": "atr14",
            "atr_14": "atr14",
            # MACD
            "macd": "macd12_26_9",
            "macd_signal": "macd_signal9",
            # Bollinger Bands
            "bb_upper": "bbands20_upper",
            "bb_lower": "bbands20_lower",
            "bb_middle": "bbands20_middle",
            "bb_width": "bbands20_width",
            # Stochastic
            "stoch_k": "stoch14_k",
            "stoch_d": "stoch14_d",
            # Volume
            "volume": "volume",
            # Custom/Derived Indicators (map to base)
            "sma_alignment": "sma20",  # Derived from SMA
            "macd_hist": "macd12_26_9",  # MACD histogram
            "bb_pct": "bbands20_middle",  # BB position percentage
            "di_spread": "adx14",  # DI spread (from ADX)
            "rsi_momentum": "rsi14",  # RSI momentum
            "rsi_divergence": "rsi14",  # RSI divergence
            "sma_distance": "sma20",  # Distance from SMA
            "price_vs_sma20": "sma20",  # Price vs SMA20
            "price_position": "sma20",  # Price position
            "atr_ratio": "atr14",  # ATR ratio
            "volume_ratio": "volume",  # Volume ratio
        }

        return id_map.get(indicator_name, indicator_name)

    def _strategy_id_from_name(self, name: str) -> str:
        """Convert strategy name to ID.

        Args:
            name: Strategy name

        Returns:
            Strategy ID (snake_case)
        """
        # Remove common suffixes
        name = name.replace("Strategy", "").replace("Trading", "").strip()

        # Convert to snake_case
        import re

        # Insert underscore before uppercase letters
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name)

        # Lowercase and clean
        return name.lower().replace(" ", "_").replace("__", "_")

    def save_config(self, config: dict[str, Any], output_path: Path | str) -> None:
        """Save JSON config to file.

        Args:
            config: JSON config dict
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved JSON config to {output_path}")

    def generate_and_save(
        self,
        analysis: StrategyAnalysis,
        output_path: Path | str,
        include_regime: bool = True,
        include_strategy_set: bool = True,
    ) -> None:
        """Generate and save JSON config in one step.

        Args:
            analysis: Strategy analysis
            output_path: Output file path
            include_regime: Include auto-generated regime
            include_strategy_set: Include strategy set and routing
        """
        config = self.generate_from_analysis(
            analysis, include_regime=include_regime, include_strategy_set=include_strategy_set
        )
        self.save_config(config, output_path)
