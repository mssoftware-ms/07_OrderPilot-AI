"""Regime Optimization - Data Updates & Transformations Mixin.

Handles data transformations and config building logic.

Agent: CODER-013
Task: 3.1.3 - Split regime_optimization_mixin
File: 4/5 - Updates (450 LOC target)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class RegimeOptimizationUpdatesMixin:
    """Data transformation and config building logic.

    Handles:
        - Parameter format conversion
        - Indicator building from params
        - Regime building from params
        - Helper utilities for data transformation
    """

    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes.

        Args:
            timeframe: Timeframe string like "1m", "5m", "15m", "1h", "4h", "1d"

        Returns:
            Number of minutes for one candle
        """
        timeframe = timeframe.lower().strip()

        # Parse number and unit
        if timeframe.endswith("m"):
            return int(timeframe[:-1])
        elif timeframe.endswith("h"):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith("d"):
            return int(timeframe[:-1]) * 1440
        elif timeframe.endswith("w"):
            return int(timeframe[:-1]) * 10080
        else:
            # Default to 5 minutes if unknown
            logger.warning(f"Unknown timeframe format: {timeframe}, defaulting to 5m")
            return 5

    def _convert_params_to_v2_format(self, params: dict) -> dict:
        """Convert flat optimizer parameters to v2.0 nested format.

        Args:
            params: Flat dict like {"adx_period": 14, "adx_trending_threshold": 25, ...}

        Returns:
            Nested dict like {"adx.period": 14, "BULL.adx_min": 25, ...}
        """
        converted = {}

        # Known mappings from ADX/DI-based flat format to v2.0 format
        param_mappings = {
            # ADX indicator parameters
            "adx_period": "adx.period",
            "di_diff_threshold": "adx.di_diff_threshold",
            # Regime thresholds
            "adx_trending_threshold": "BULL.adx_min",  # Trending threshold for BULL/BEAR
            "adx_weak_threshold": "SIDEWAYS.adx_max",  # Weak threshold for SIDEWAYS
            # RSI parameters
            "rsi_period": "rsi.period",
            "rsi_strong_bull": "BULL.rsi_strong_bull",
            "rsi_strong_bear": "BEAR.rsi_strong_bear",
            # ATR parameters
            "atr_period": "atr.period",
            "strong_move_pct": "atr.strong_move_pct",
            "extreme_move_pct": "atr.extreme_move_pct",
        }

        for old_key, new_key in param_mappings.items():
            if old_key in params:
                converted[new_key] = params[old_key]

                # Special handling for shared thresholds
                if old_key == "adx_trending_threshold":
                    # Trending threshold is used by both BULL and BEAR
                    converted["BEAR.adx_min"] = params[old_key]

                elif old_key == "di_diff_threshold":
                    # DI difference used by both BULL and BEAR
                    converted["BULL.di_diff_min"] = params[old_key]
                    converted["BEAR.di_diff_min"] = params[old_key]

                elif old_key == "extreme_move_pct":
                    # Extreme move threshold shared
                    converted["BULL.extreme_move_pct"] = params[old_key]
                    converted["BEAR.extreme_move_pct"] = params[old_key]

        # Pass through any already-converted params
        for key, value in params.items():
            if "." in key and key not in converted:
                converted[key] = value

        return converted

    def _update_regime_threshold(self, regime: dict, threshold_name: str, threshold_value: float) -> None:
        """Update regime threshold in conditions.

        Args:
            regime: Regime dict from JSON
            threshold_name: Name of threshold (e.g., "adx_threshold", "rsi_low")
            threshold_value: New threshold value
        """
        conditions = regime.get("conditions", {})

        # Map threshold names to condition updates
        if threshold_name == "adx_threshold":
            # Update ADX value threshold in conditions
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "adx" and cond.get("op") in ["gt", "lt"]:
                        cond["right"]["value"] = int(threshold_value)

        elif threshold_name == "rsi_low":
            # Update RSI lower bound (SIDEWAYS regime)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi" and cond.get("op") == "between":
                        cond["right"]["min"] = int(threshold_value)

        elif threshold_name == "rsi_high":
            # Update RSI upper bound (SIDEWAYS regime)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi" and cond.get("op") == "between":
                        cond["right"]["max"] = int(threshold_value)

        elif threshold_name == "rsi_overbought":
            # Update RSI overbought threshold (SIDEWAYS_OVERBOUGHT)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi" and cond.get("op") == "gt":
                        cond["right"]["value"] = int(threshold_value)

        elif threshold_name == "rsi_oversold":
            # Update RSI oversold threshold (SIDEWAYS_OVERSOLD)
            if "all" in conditions:
                for cond in conditions["all"]:
                    left = cond.get("left", {})
                    if left.get("indicator_id") == "rsi" and cond.get("op") == "lt":
                        cond["right"]["value"] = int(threshold_value)

    def _build_indicators_from_params(self, params: dict) -> list[dict]:
        """Build v2.0 indicators[] structure from flattened params.

        Uses the original JSON indicators (if loaded) and updates param values
        with optimized params. This preserves all indicator types (including
        custom ones like CHANDELIER, ADX_LEAF_WEST, etc.).

        Param formats supported:
        - Flat: "adx_period", "rsi_period"
        - JSON dot-notation: "MOMENTUM_RSI.period", "STRENGTH_ADX.trending_threshold"

        Args:
            params: Flattened params dict from optimization result

        Returns:
            List of indicator dicts in v2.0 format
        """
        import copy

        # Try to get original indicators from loaded JSON config
        original_indicators = None
        if hasattr(self, "_regime_config") and self._regime_config:
            try:
                # Get indicators from optimization_results[0].indicators
                if hasattr(self._regime_config, "optimization_results"):
                    opt_results = self._regime_config.optimization_results
                    if opt_results and len(opt_results) > 0:
                        if hasattr(opt_results[0], "indicators"):
                            original_indicators = opt_results[0].indicators
                        elif isinstance(opt_results[0], dict):
                            original_indicators = opt_results[0].get("indicators", [])
                elif isinstance(self._regime_config, dict):
                    opt_results = self._regime_config.get("optimization_results", [])
                    if opt_results and len(opt_results) > 0:
                        original_indicators = opt_results[0].get("indicators", [])
            except Exception as e:
                logger.warning(f"Could not extract indicators from config: {e}")

        if original_indicators:
            # Use original indicators and update param values from params
            indicators = []
            for ind_data in original_indicators:
                # Deep copy to avoid modifying original
                if hasattr(ind_data, "model_dump"):
                    indicator = ind_data.model_dump()
                elif hasattr(ind_data, "dict"):
                    indicator = ind_data.dict()
                else:
                    indicator = copy.deepcopy(ind_data) if isinstance(ind_data, dict) else {}

                ind_name = indicator.get("name", "")
                ind_type = indicator.get("type", "")

                # Update params with optimized values
                if "params" in indicator and isinstance(indicator["params"], list):
                    for param in indicator["params"]:
                        if not isinstance(param, dict):
                            continue
                        param_name = param.get("name", "")

                        # Try JSON dot-notation first: "INDICATOR_NAME.param_name"
                        json_key = f"{ind_name}.{param_name}"
                        if json_key in params:
                            param["value"] = self._format_param_value(params[json_key])
                            continue

                        # Try flat format mapping
                        flat_value = self._get_flat_param_for_indicator(
                            params, ind_name, ind_type, param_name
                        )
                        if flat_value is not None:
                            param["value"] = self._format_param_value(flat_value)

                indicators.append(indicator)

            logger.info(
                f"Built {len(indicators)} indicators from original JSON config: "
                f"{[i.get('name', '?') for i in indicators]}"
            )
            return indicators

        # Fallback: Build default indicator structure if no JSON loaded
        logger.warning("No JSON indicators found, building default indicator structure")
        return self._build_default_indicators_from_params(params)

    def _format_param_value(self, value: float | int) -> int | float:
        """Format parameter value (int if whole number, else float)."""
        if isinstance(value, float) and value == int(value):
            return int(value)
        if isinstance(value, float):
            return round(value, 2)
        return value

    def _get_flat_param_for_indicator(
        self, params: dict, ind_name: str, ind_type: str, param_name: str
    ) -> float | None:
        """Map flat optimizer params to indicator param names.

        Args:
            params: Flat params dict
            ind_name: Indicator name (e.g., "STRENGTH_ADX")
            ind_type: Indicator type (e.g., "ADX")
            param_name: Parameter name (e.g., "period")

        Returns:
            Parameter value or None if not found
        """
        # Build possible flat key names based on indicator type
        type_lower = ind_type.lower() if ind_type else ""

        # Direct mappings
        flat_keys = [
            f"{type_lower}_{param_name}",  # e.g., "adx_period"
            param_name,  # Direct match
        ]

        for key in flat_keys:
            if key in params:
                return params[key]

        return None

    def _build_default_indicators_from_params(self, params: dict) -> list[dict]:
        """Build default indicator structure when no JSON is loaded.

        Fallback method for backwards compatibility.

        Args:
            params: Flattened params dict from optimization result

        Returns:
            List of indicator dicts in v2.0 format
        """
        indicators_map = {}

        indicator_info = {
            "adx": {"name": "STRENGTH_ADX", "type": "ADX"},
            "rsi": {"name": "MOMENTUM_RSI", "type": "RSI"},
            "atr": {"name": "VOLATILITY_ATR", "type": "ATR"},
        }

        param_mapping = {
            "adx_period": ("adx", "period"),
            "adx_trending_threshold": ("adx", "trending_threshold"),
            "adx_weak_threshold": ("adx", "weak_threshold"),
            "di_diff_threshold": ("adx", "di_diff_threshold"),
            "rsi_period": ("rsi", "period"),
            "rsi_strong_bull": ("rsi", "strong_bull"),
            "rsi_strong_bear": ("rsi", "strong_bear"),
            "atr_period": ("atr", "period"),
            "strong_move_pct": ("atr", "strong_move_pct"),
            "extreme_move_pct": ("atr", "extreme_move_pct"),
        }

        param_ranges = {
            "period": {"min": 5, "max": 50, "step": 1},
            "trending_threshold": {"min": 20, "max": 40, "step": 1},
            "weak_threshold": {"min": 15, "max": 25, "step": 1},
            "di_diff_threshold": {"min": 3, "max": 15, "step": 1},
            "strong_bull": {"min": 50, "max": 70, "step": 1},
            "strong_bear": {"min": 30, "max": 50, "step": 1},
            "strong_move_pct": {"min": 0.5, "max": 3.0, "step": 0.1},
            "extreme_move_pct": {"min": 2.0, "max": 5.0, "step": 0.5},
        }

        for param_key, param_value in params.items():
            if param_key in param_mapping:
                indicator_id, param_name = param_mapping[param_key]
            elif "." in param_key:
                parts = param_key.split(".", 1)
                if len(parts) != 2:
                    continue
                indicator_id, param_name = parts
                if indicator_id.isupper():
                    continue
            else:
                continue

            if indicator_id not in indicator_info:
                continue

            info = indicator_info[indicator_id]

            if indicator_id not in indicators_map:
                indicators_map[indicator_id] = {
                    "name": info["name"],
                    "type": info["type"],
                    "params": []
                }

            param_entry = {
                "name": param_name,
                "value": self._format_param_value(param_value)
            }

            if param_name in param_ranges:
                param_entry["range"] = param_ranges[param_name]

            indicators_map[indicator_id]["params"].append(param_entry)

        indicators = list(indicators_map.values())
        indicators.sort(key=lambda x: x["name"])

        logger.info(f"Built {len(indicators)} default indicators: {[i['name'] for i in indicators]}")
        return indicators

    def _build_regimes_from_params(self, params: dict) -> list[dict]:
        """Build v2.0 regimes[] structure from optimization params.

        Uses the original JSON regimes (if loaded) and updates threshold values
        with optimized params. This preserves all regime IDs (including custom
        ones like STRONG_BULL, STRONG_BEAR, STRONG_SIDEWAYS).

        Param formats supported:
        - Flat: "adx_trending_threshold", "di_diff_threshold"
        - JSON dot-notation: "STRONG_BULL.adx_min", "BEAR.di_diff_min"

        Args:
            params: Flattened params dict from optimization result

        Returns:
            List of regime dicts in v2.0 format
        """
        import copy

        # Try to get original regimes from loaded JSON config
        original_regimes = None
        if hasattr(self, "_regime_config") and self._regime_config:
            try:
                # Get regimes from optimization_results[0].regimes
                if hasattr(self._regime_config, "optimization_results"):
                    opt_results = self._regime_config.optimization_results
                    if opt_results and len(opt_results) > 0:
                        if hasattr(opt_results[0], "regimes"):
                            original_regimes = opt_results[0].regimes
                        elif isinstance(opt_results[0], dict):
                            original_regimes = opt_results[0].get("regimes", [])
                elif isinstance(self._regime_config, dict):
                    opt_results = self._regime_config.get("optimization_results", [])
                    if opt_results and len(opt_results) > 0:
                        original_regimes = opt_results[0].get("regimes", [])
            except Exception as e:
                logger.warning(f"Could not extract regimes from config: {e}")

        if original_regimes:
            # Use original regimes and update threshold values from params
            regimes = []
            for regime_data in original_regimes:
                # Deep copy to avoid modifying original
                if hasattr(regime_data, "model_dump"):
                    regime = regime_data.model_dump()
                elif hasattr(regime_data, "dict"):
                    regime = regime_data.dict()
                else:
                    regime = copy.deepcopy(regime_data) if isinstance(regime_data, dict) else {"id": str(regime_data)}

                regime_id = regime.get("id", "").upper()

                # Update thresholds with optimized values
                if "thresholds" in regime and isinstance(regime["thresholds"], list):
                    for thresh in regime["thresholds"]:
                        if not isinstance(thresh, dict):
                            continue
                        thresh_name = thresh.get("name", "")

                        # Try JSON dot-notation first: "REGIME_ID.threshold_name"
                        json_key = f"{regime_id}.{thresh_name}"
                        if json_key in params:
                            thresh["value"] = self._round_value(params[json_key])
                            continue

                        # Try flat format mapping
                        flat_value = self._get_flat_param_for_threshold(
                            params, regime_id, thresh_name
                        )
                        if flat_value is not None:
                            thresh["value"] = self._round_value(flat_value)

                regimes.append(regime)

            logger.info(
                f"Built {len(regimes)} regimes from original JSON config with updated thresholds"
            )
            return regimes

        # Fallback: Build default 3-regime structure if no JSON loaded
        logger.warning("No JSON regimes found, building default 3-regime structure")
        return self._build_default_regimes_from_params(params)

    def _round_value(self, value: float | int) -> float:
        """Round value appropriately based on magnitude."""
        if isinstance(value, int):
            return float(value)
        if abs(value) >= 10:
            return round(value, 1)
        return round(value, 2)

    def _get_flat_param_for_threshold(
        self, params: dict, regime_id: str, thresh_name: str
    ) -> float | None:
        """Map flat optimizer params to regime threshold names.

        Args:
            params: Flat params dict
            regime_id: Regime ID (e.g., "BULL", "STRONG_BULL")
            thresh_name: Threshold name (e.g., "adx_min", "di_diff_min")

        Returns:
            Parameter value or None if not found
        """
        # Direct mappings from optimizer params to threshold names
        mapping = {
            "adx_min": "adx_trending_threshold",
            "adx_max": "adx_weak_threshold",
            "di_diff_min": "di_diff_threshold",
            "rsi_strong_bull": "rsi_strong_bull",
            "rsi_strong_bear": "rsi_strong_bear",
            "strong_move_pct": "strong_move_pct",
            "extreme_move_pct": "extreme_move_pct",
        }

        if thresh_name in mapping:
            flat_key = mapping[thresh_name]
            if flat_key in params:
                return params[flat_key]

        return None

    def _build_default_regimes_from_params(self, params: dict) -> list[dict]:
        """Build default 3-regime structure when no JSON is loaded.

        Fallback method for backwards compatibility.

        Args:
            params: Flattened params dict from optimization result

        Returns:
            List of 3 regime dicts (BULL, BEAR, SIDEWAYS)
        """
        adx_trending = params.get("adx_trending_threshold", 25)
        adx_weak = params.get("adx_weak_threshold", 20)
        di_diff = params.get("di_diff_threshold", 5)
        rsi_strong_bull = params.get("rsi_strong_bull", 55)
        rsi_strong_bear = params.get("rsi_strong_bear", 45)
        extreme_move_pct = params.get("extreme_move_pct", 3.0)

        threshold_ranges = {
            "adx_min": {"min": 15, "max": 40, "step": 1},
            "adx_max": {"min": 15, "max": 30, "step": 1},
            "di_diff_min": {"min": 3, "max": 15, "step": 1},
            "rsi_strong_bull": {"min": 50, "max": 70, "step": 1},
            "rsi_strong_bear": {"min": 30, "max": 50, "step": 1},
            "extreme_move_pct": {"min": 2.0, "max": 5.0, "step": 0.5},
        }

        regimes = [
            {
                "id": "BULL",
                "name": "Bullischer Trend",
                "thresholds": [
                    {"name": "adx_min", "value": round(adx_trending, 1), "range": threshold_ranges["adx_min"]},
                    {"name": "di_diff_min", "value": round(di_diff, 1), "range": threshold_ranges["di_diff_min"]},
                    {"name": "rsi_strong_bull", "value": round(rsi_strong_bull, 1), "range": threshold_ranges["rsi_strong_bull"]},
                    {"name": "extreme_move_pct", "value": round(extreme_move_pct, 2), "range": threshold_ranges["extreme_move_pct"]},
                ],
                "priority": 90,
                "scope": "entry"
            },
            {
                "id": "BEAR",
                "name": "Bärischer Trend",
                "thresholds": [
                    {"name": "adx_min", "value": round(adx_trending, 1), "range": threshold_ranges["adx_min"]},
                    {"name": "di_diff_min", "value": round(di_diff, 1), "range": threshold_ranges["di_diff_min"]},
                    {"name": "rsi_strong_bear", "value": round(rsi_strong_bear, 1), "range": threshold_ranges["rsi_strong_bear"]},
                    {"name": "extreme_move_pct", "value": round(extreme_move_pct, 2), "range": threshold_ranges["extreme_move_pct"]},
                ],
                "priority": 85,
                "scope": "entry"
            },
            {
                "id": "SIDEWAYS",
                "name": "Seitwärts / Range",
                "thresholds": [
                    {"name": "adx_max", "value": round(adx_weak, 1), "range": threshold_ranges["adx_max"]},
                ],
                "priority": 50,
                "scope": "entry"
            },
        ]

        logger.info(
            f"Built default 3 regimes: adx_trending={adx_trending:.1f}, "
            f"adx_weak={adx_weak:.1f}, di_diff={di_diff:.1f}"
        )
        return regimes

