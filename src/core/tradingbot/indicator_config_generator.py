"""JSON Config Generator from Optimization Results.

Generates production-ready JSON strategy configs from indicator optimization
results, including regimes, strategies, and routing.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from .indicator_optimizer import IndicatorScore

logger = logging.getLogger(__name__)


class IndicatorConfigGenerator:
    """Generates JSON configs from optimization results.

    Example:
        >>> generator = IndicatorConfigGenerator()
        >>> optimization_results = {
        ...     "RSI": [best_rsi_score1, best_rsi_score2],
        ...     "ADX": [best_adx_score1]
        ... }
        >>> config = generator.generate_regime_config(
        ...     "R2_range",
        ...     optimization_results,
        ...     output_path="03_JSON/Trading_Bot/optimized_range_strategy.json"
        ... )
    """

    def __init__(self):
        """Initialize config generator."""
        self.schema_version = "1.0.0"

    def generate_regime_config(
        self,
        regime_id: str,
        optimization_results: dict[str, list[IndicatorScore]],
        output_path: str | None = None,
        strategy_name: str | None = None
    ) -> dict[str, Any]:
        """Generate complete JSON config for a specific regime.

        Args:
            regime_id: Regime ID (e.g., "R2_range")
            optimization_results: Dictionary mapping indicator type to best scores
            output_path: Optional path to save JSON file
            strategy_name: Optional custom strategy name

        Returns:
            JSON config dictionary
        """
        if strategy_name is None:
            strategy_name = f"optimized_{regime_id.lower()}"

        # Build config structure
        config = {
            "schema_version": self.schema_version,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "regime_id": regime_id,
                "strategy_name": strategy_name,
                "source": "indicator_optimization",
                "total_indicators": sum(len(scores) for scores in optimization_results.values())
            },
            "indicators": self._build_indicators_section(optimization_results),
            "regimes": self._build_regimes_section(regime_id, optimization_results),
            "strategies": self._build_strategies_section(
                strategy_name, regime_id, optimization_results
            ),
            "strategy_sets": self._build_strategy_sets_section(strategy_name),
            "routing": self._build_routing_section(strategy_name, regime_id)
        }

        # Save to file if path provided
        if output_path:
            self.save_config(config, output_path)

        return config

    def _build_indicators_section(
        self,
        optimization_results: dict[str, list[IndicatorScore]]
    ) -> list[dict[str, Any]]:
        """Build indicators section of config.

        Args:
            optimization_results: Dictionary mapping indicator type to best scores

        Returns:
            List of indicator definitions
        """
        indicators = []

        for indicator_type, scores in optimization_results.items():
            for idx, score in enumerate(scores):
                indicator_id = f"{indicator_type.lower()}_{idx + 1}"

                indicator_def = {
                    "id": indicator_id,
                    "type": indicator_type,
                    "params": score.params,
                    "metadata": {
                        "composite_score": score.composite_score,
                        "sharpe_ratio": score.sharpe_ratio,
                        "win_rate": score.win_rate,
                        "combination_id": score.combination_id
                    }
                }

                indicators.append(indicator_def)

        return indicators

    def _build_regimes_section(
        self,
        regime_id: str,
        optimization_results: dict[str, list[IndicatorScore]]
    ) -> list[dict[str, Any]]:
        """Build regimes section of config.

        Args:
            regime_id: Regime ID
            optimization_results: Dictionary mapping indicator type to best scores

        Returns:
            List of regime definitions
        """
        # Build CEL expression from best indicators
        cel_conditions = []

        # Add regime-specific conditions based on regime_id
        regime_conditions = self._get_regime_base_conditions(regime_id)
        cel_conditions.extend(regime_conditions)

        # Combine into single CEL expression
        cel_expression = " && ".join(cel_conditions)

        regime_def = {
            "id": f"regime_{regime_id.lower()}",
            "name": f"Optimized {regime_id} Regime",
            "conditions": {
                "all": [
                    {
                        "cel_expression": cel_expression
                    }
                ]
            },
            "priority": 10,
            "scope": "entry"
        }

        return [regime_def]

    def _get_regime_base_conditions(self, regime_id: str) -> list[str]:
        """Get base CEL conditions for a regime.

        Args:
            regime_id: Regime ID (R1_trend, R2_range, etc.)

        Returns:
            List of CEL condition strings
        """
        # Base conditions per regime type
        regime_conditions = {
            "R1_trend": [
                "adx_1.value > 25",  # Strong trend
                "atr_1.value > 0.5"   # Sufficient volatility
            ],
            "R2_range": [
                "adx_1.value < 20",   # Weak trend
                "chop_1.value > 61.8"  # Choppy/range-bound
            ],
            "R3_breakout": [
                "bb_width_1.value < 0.015",  # Squeeze
                "atr_1.value > 0.3"           # Volatility pickup
            ],
            "R4_volatile": [
                "atr_1.value > 1.5",          # High volatility
                "bb_width_1.value > 0.03"     # Wide bands
            ],
            "R5_orderflow": [
                "cmf_1.value != 0",           # Volume flow present
                "obv_1.value != 0"            # OBV active
            ]
        }

        return regime_conditions.get(regime_id, ["true"])  # Default to always true

    def _build_strategies_section(
        self,
        strategy_name: str,
        regime_id: str,
        optimization_results: dict[str, list[IndicatorScore]]
    ) -> list[dict[str, Any]]:
        """Build strategies section of config.

        Args:
            strategy_name: Strategy name
            regime_id: Regime ID
            optimization_results: Dictionary mapping indicator type to best scores

        Returns:
            List of strategy definitions
        """
        # Build entry conditions from top indicators
        entry_conditions = self._build_entry_conditions(regime_id, optimization_results)

        # Build exit conditions
        exit_conditions = self._build_exit_conditions(regime_id)

        strategy = {
            "id": strategy_name,
            "name": strategy_name,
            "entry": entry_conditions,
            "exit": exit_conditions,
            "risk": self._build_risk_section(regime_id)
        }

        return [strategy]

    def _build_entry_conditions(
        self,
        regime_id: str,
        optimization_results: dict[str, list[IndicatorScore]]
    ) -> dict[str, list[dict]]:
        """Build entry conditions using CEL.

        Args:
            regime_id: Regime ID
            optimization_results: Dictionary mapping indicator type to best scores

        Returns:
            Entry conditions structure
        """
        # Get top indicator for each type
        cel_conditions = []

        # Add regime-specific entry logic
        if regime_id == "R1_trend":
            # Trend following: momentum + trend alignment
            if "RSI" in optimization_results:
                cel_conditions.append("rsi_1.value > 50 && rsi_1.value < 80")
            if "MACD" in optimization_results:
                cel_conditions.append("macd_1.histogram > 0")

        elif regime_id == "R2_range":
            # Mean reversion: oversold/overbought
            if "RSI" in optimization_results:
                cel_conditions.append("(rsi_1.value < 30 || rsi_1.value > 70)")
            if "BB" in optimization_results:
                cel_conditions.append("(bb_1.percent < 0.1 || bb_1.percent > 0.9)")

        elif regime_id == "R3_breakout":
            # Breakout: squeeze + momentum
            if "BB_WIDTH" in optimization_results:
                cel_conditions.append("bb_width_1.value < 0.015")
            if "CCI" in optimization_results:
                cel_conditions.append("abs(cci_1.value) > 100")

        else:
            # Generic: use top indicators
            for indicator_type in list(optimization_results.keys())[:3]:
                cel_conditions.append(f"{indicator_type.lower()}_1.value > 0")

        # Combine with OR logic (any condition triggers entry)
        return {
            "any": [
                {"cel_expression": cond}
                for cond in cel_conditions
            ]
        }

    def _build_exit_conditions(self, regime_id: str) -> dict[str, list[dict]]:
        """Build exit conditions.

        Args:
            regime_id: Regime ID

        Returns:
            Exit conditions structure
        """
        # Standard exit conditions
        exit_conditions = {
            "any": []
        }

        # Stop loss hit
        exit_conditions["any"].append({
            "cel_expression": "trade.side == 'long' ? trade.current_price <= trade.stop_price : trade.current_price >= trade.stop_price"
        })

        # Take profit hit
        exit_conditions["any"].append({
            "cel_expression": "trade.pnl_pct >= trade.take_profit_pct"
        })

        # Regime-specific exits
        if regime_id == "R1_trend":
            # Trend reversal
            exit_conditions["any"].append({
                "cel_expression": "adx_1.value < 20"
            })

        elif regime_id == "R2_range":
            # Profit target reached or opposite band touched
            exit_conditions["any"].append({
                "cel_expression": "trade.pnl_pct > 1.5"
            })

        return exit_conditions

    def _build_risk_section(self, regime_id: str) -> dict[str, float]:
        """Build risk management section.

        Args:
            regime_id: Regime ID

        Returns:
            Risk parameters dictionary
        """
        # Risk parameters per regime type
        risk_params = {
            "R1_trend": {
                "position_size": 0.03,  # 3% per trade (higher for trends)
                "stop_loss": 0.025,     # 2.5% stop
                "take_profit": 0.06     # 6% target (2.4:1 R:R)
            },
            "R2_range": {
                "position_size": 0.02,  # 2% per trade (conservative)
                "stop_loss": 0.015,     # 1.5% stop (tight for ranges)
                "take_profit": 0.03     # 3% target (2:1 R:R)
            },
            "R3_breakout": {
                "position_size": 0.025,  # 2.5% per trade
                "stop_loss": 0.03,       # 3% stop (wider for volatility)
                "take_profit": 0.09      # 9% target (3:1 R:R)
            },
            "R4_volatile": {
                "position_size": 0.015,  # 1.5% per trade (reduced size)
                "stop_loss": 0.04,       # 4% stop (very wide)
                "take_profit": 0.08      # 8% target (2:1 R:R)
            }
        }

        return risk_params.get(regime_id, {
            "position_size": 0.02,
            "stop_loss": 0.025,
            "take_profit": 0.05
        })

    def _build_strategy_sets_section(self, strategy_name: str) -> list[dict[str, Any]]:
        """Build strategy sets section.

        Args:
            strategy_name: Strategy name

        Returns:
            List of strategy set definitions
        """
        return [
            {
                "id": f"set_{strategy_name}",
                "name": f"{strategy_name} Set",
                "strategies": [
                    {
                        "strategy_id": strategy_name
                    }
                ]
            }
        ]

    def _build_routing_section(
        self,
        strategy_name: str,
        regime_id: str
    ) -> list[dict[str, Any]]:
        """Build routing section.

        Args:
            strategy_name: Strategy name
            regime_id: Regime ID

        Returns:
            List of routing rules
        """
        return [
            {
                "strategy_set_id": f"set_{strategy_name}",
                "match": {
                    "all_of": [
                        f"regime_{regime_id.lower()}"
                    ]
                }
            }
        ]

    def save_config(self, config: dict[str, Any], output_path: str) -> None:
        """Save config to JSON file.

        Args:
            config: JSON config dictionary
            output_path: Path to save file
        """
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path_obj, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved config to {output_path}")

    def generate_batch_configs(
        self,
        optimization_results_by_regime: dict[str, dict[str, list[IndicatorScore]]],
        output_dir: str = "03_JSON/Trading_Bot"
    ) -> dict[str, str]:
        """Generate configs for multiple regimes.

        Args:
            optimization_results_by_regime: Nested dict: regime_id -> indicator_type -> scores
            output_dir: Directory to save configs

        Returns:
            Dictionary mapping regime_id to output file path
        """
        output_paths = {}

        for regime_id, optimization_results in optimization_results_by_regime.items():
            strategy_name = f"optimized_{regime_id.lower()}"
            output_path = f"{output_dir}/{strategy_name}.json"

            config = self.generate_regime_config(
                regime_id=regime_id,
                optimization_results=optimization_results,
                output_path=output_path,
                strategy_name=strategy_name
            )

            output_paths[regime_id] = output_path
            logger.info(f"Generated config for {regime_id}: {output_path}")

        return output_paths
