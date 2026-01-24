"""JSON-based Regime Engine for Tradingbot.

Refactored from hardcoded RegimeEngine to JSON-based configuration.
Uses IndicatorEngine for calculations and RegimeDetector for evaluation.

Architecture:
    JSON Config -> IndicatorEngine (calculate) -> RegimeDetector (evaluate) -> RegimeState

Migration:
    - Old: RegimeEngine.classify(features) -> RegimeState
    - New: RegimeEngineJSON.classify(data, config_path) -> RegimeState
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.core.indicators.engine import IndicatorEngine
from src.core.indicators.types import IndicatorConfig, IndicatorType

from .config.detector import RegimeDetector
from .config.loader import ConfigLoader
from .models import (
    FeatureVector,
    RegimeState,
    RegimeType,
    VolatilityLevel,
)

logger = logging.getLogger(__name__)


class RegimeEngineJSON:
    """JSON-based regime engine using IndicatorEngine + RegimeDetector.

    Replaces hardcoded thresholds with configurable JSON-based regime definitions.

    Features:
    - Load regime definitions from JSON
    - Calculate indicators using IndicatorEngine
    - Evaluate regimes using RegimeDetector
    - Convert to legacy RegimeState for compatibility

    Example:
        >>> engine = RegimeEngineJSON()
        >>> state = engine.classify_from_config(
        ...     data=df,  # OHLCV DataFrame
        ...     config_path="03_JSON/Trading_Bot/momentum_downtrend.json"
        ... )
        >>> print(state.regime_label)
        'TREND_DOWN (EXTREME)'
    """

    def __init__(self):
        """Initialize JSON-based regime engine."""
        self.indicator_engine = IndicatorEngine()
        self.config_loader = ConfigLoader()
        self._cached_config = None
        self._cached_config_path = None
        logger.info("RegimeEngineJSON initialized (JSON-based regime detection)")

    def classify_from_config(
        self,
        data: pd.DataFrame,
        config_path: str | Path,
        scope: str = "entry"
    ) -> RegimeState:
        """Classify market regime using JSON configuration.

        Args:
            data: OHLCV DataFrame with columns: open, high, low, close, volume
            config_path: Path to JSON strategy config
            scope: Regime scope ("entry", "exit", "in_trade")

        Returns:
            RegimeState with regime and volatility classification
        """
        # 1. Load JSON config
        config = self._load_config(config_path)

        # 2. Calculate indicators
        indicator_values = self._calculate_indicators(data, config)

        # 3. Detect active regimes
        detector = RegimeDetector(config.regimes)
        active_regimes = detector.detect_active_regimes(indicator_values, scope=scope)

        # 4. Convert to RegimeState
        state = self._convert_to_regime_state(
            active_regimes=active_regimes,
            indicator_values=indicator_values,
            timestamp=datetime.utcnow()
        )

        logger.info(
            f"Regime classified from JSON: {state.regime_label} "
            f"(confidence={state.regime_confidence:.2f})"
        )

        return state

    def classify_from_features(
        self,
        features: FeatureVector,
        config_path: str | Path,
        scope: str = "entry"
    ) -> RegimeState:
        """Classify regime from pre-calculated FeatureVector.

        Convenience wrapper that converts FeatureVector to indicator_values dict.

        Args:
            features: Pre-calculated feature vector
            config_path: Path to JSON strategy config
            scope: Regime scope

        Returns:
            RegimeState
        """
        # Convert FeatureVector to indicator_values dict
        indicator_values = self._features_to_indicator_values(features)

        # Load config
        config = self._load_config(config_path)

        # Detect regimes
        detector = RegimeDetector(config.regimes)
        active_regimes = detector.detect_active_regimes(indicator_values, scope=scope)

        # Convert to RegimeState
        return self._convert_to_regime_state(
            active_regimes=active_regimes,
            indicator_values=indicator_values,
            timestamp=features.timestamp
        )

    def _load_config(self, config_path: str | Path):
        """Load and cache JSON configuration.

        Args:
            config_path: Path to JSON file

        Returns:
            TradingBotConfig object
        """
        config_path = str(config_path)

        # Use cache if same path
        if self._cached_config_path == config_path:
            return self._cached_config

        # Load new config
        config = self.config_loader.load_config(config_path)
        self._cached_config = config
        self._cached_config_path = config_path

        logger.info(
            f"Loaded config: {len(config.regimes)} regimes, "
            f"{len(config.indicators)} indicators"
        )

        return config

    def _calculate_indicators(
        self,
        data: pd.DataFrame,
        config
    ) -> dict[str, dict[str, float]]:
        """Calculate all indicators defined in config.

        Args:
            data: OHLCV DataFrame
            config: TradingBotConfig

        Returns:
            Dict mapping indicator_id -> {field -> value}
            Example: {"momentum_score": {"value": -4.2}, "volume_ratio": {"value": 2.8}}
        """
        indicator_values = {}

        for ind_def in config.indicators:
            try:
                # Create IndicatorConfig
                ind_config = IndicatorConfig(
                    indicator_type=IndicatorType(ind_def.type.lower()),
                    params=ind_def.params,
                    use_talib=False,  # Use pandas_ta by default
                    cache_results=True
                )

                # Calculate indicator
                result = self.indicator_engine.calculate(data, ind_config)

                # Extract value(s)
                if isinstance(result.values, pd.Series):
                    # Single value indicator
                    latest_value = result.values.iloc[-1] if len(result.values) > 0 else None
                    indicator_values[ind_def.id] = {"value": latest_value}
                elif isinstance(result.values, pd.DataFrame):
                    # Multi-value indicator (e.g., MACD, BB)
                    indicator_values[ind_def.id] = {}
                    for col in result.values.columns:
                        latest_value = result.values[col].iloc[-1] if len(result.values) > 0 else None
                        indicator_values[ind_def.id][col] = latest_value

                    # Add field aliases for user-friendly naming
                    if 'bandwidth' in indicator_values[ind_def.id]:
                        # Alias: bandwidth → width (for BB indicators)
                        indicator_values[ind_def.id]['width'] = indicator_values[ind_def.id]['bandwidth']
                elif isinstance(result.values, dict):
                    # Dict result (e.g., from custom indicators)
                    indicator_values[ind_def.id] = result.values
                else:
                    logger.warning(
                        f"Unknown result type for {ind_def.id}: {type(result.values)}"
                    )

                logger.debug(f"Calculated {ind_def.id}: {indicator_values[ind_def.id]}")

            except Exception as e:
                logger.error(f"Failed to calculate indicator {ind_def.id}: {e}")
                # Set null value to avoid missing key errors
                indicator_values[ind_def.id] = {"value": None}

        return indicator_values

    def _features_to_indicator_values(
        self,
        features: FeatureVector
    ) -> dict[str, dict[str, float]]:
        """Convert FeatureVector to indicator_values dict.

        Maps common FeatureVector attributes to indicator format.

        Args:
            features: Feature vector

        Returns:
            Dict mapping indicator_id -> {field -> value}
        """
        indicator_values = {}

        # Map common indicators
        mappings = {
            "sma_20": ("sma20", features.sma_20),
            "sma_50": ("sma50", features.sma_50),
            "adx": ("adx", features.adx),
            "adx_14": ("adx14", features.adx),
            "rsi_14": ("rsi14", features.rsi_14),
            "atr_14": ("atr14", features.atr_14),
            "atr": ("atr", features.atr_14),
            "bb_upper": ("bb20", features.bb_upper),
            "bb_lower": ("bb20", features.bb_lower),
            "bb_width": ("bb20", features.bb_width),
            "volume": ("volume", features.volume),
            "volume_sma": ("volume_sma", features.volume_sma),
        }

        for attr_name, (ind_id, value) in mappings.items():
            if value is not None:
                if ind_id not in indicator_values:
                    indicator_values[ind_id] = {}

                # Determine field name
                if attr_name.startswith("bb_"):
                    field = attr_name.replace("bb_", "")  # upper, lower, width
                elif attr_name.startswith("volume_"):
                    field = attr_name.replace("volume_", "") or "value"
                else:
                    field = "value"

                indicator_values[ind_id][field] = value

        # Calculate composite indicators from FeatureVector data
        # These are needed for JSON configs that reference momentum_score, volume_ratio, etc.

        # 1. MOMENTUM_SCORE: Price momentum based on SMA crossovers
        if "sma20" in indicator_values and "sma50" in indicator_values and features.close is not None:
            sma_fast = indicator_values["sma20"].get("value")
            sma_slow = indicator_values["sma50"].get("value")
            close = features.close

            if sma_fast is not None and sma_slow is not None and sma_slow > 0:
                # Component 1: SMA crossover distance (trend strength)
                sma_diff_pct = ((sma_fast - sma_slow) / sma_slow) * 100

                # Component 2: Current price vs Fast SMA (current momentum)
                if sma_fast > 0:
                    price_vs_sma_pct = ((close - sma_fast) / sma_fast) * 100
                    # Combined score (weighted: 60% SMA crossover, 40% price position)
                    momentum_score = (sma_diff_pct * 0.6) + (price_vs_sma_pct * 0.4)
                else:
                    momentum_score = sma_diff_pct

                indicator_values["momentum_score"] = {"value": momentum_score}

        # 2. VOLUME_RATIO: Volume relative to moving average
        if "volume" in indicator_values and "volume_sma" in indicator_values:
            volume = indicator_values["volume"].get("value")
            volume_ma = indicator_values["volume_sma"].get("value")

            if volume is not None and volume_ma is not None and volume_ma > 0:
                volume_ratio = volume / volume_ma
                indicator_values["volume_ratio"] = {"value": volume_ratio}
            else:
                # Neutral ratio if no data
                indicator_values["volume_ratio"] = {"value": 1.0}

        # 3. PRICE_STRENGTH: Complex composite indicator
        # Note: This is a simplified version. For full calculation, use classify_from_config()
        if "momentum_score" in indicator_values and "volume_ratio" in indicator_values:
            momentum = indicator_values["momentum_score"].get("value", 0)
            vol_ratio = indicator_values["volume_ratio"].get("value", 1.0)
            rsi = indicator_values.get("rsi14", {}).get("value", 50)

            # Simplified price strength (weighted combination)
            # Full calculation requires BB position and more indicators
            price_strength = (momentum * 0.5) + ((vol_ratio - 1.0) * 10 * 0.3) + ((rsi - 50) * 0.2)
            indicator_values["price_strength"] = {"value": price_strength}

        # Handle composite BB indicator
        if "bb20" in indicator_values:
            # Add middle band if upper/lower exist
            if "upper" in indicator_values["bb20"] and "lower" in indicator_values["bb20"]:
                upper = indicator_values["bb20"]["upper"]
                lower = indicator_values["bb20"]["lower"]
                if upper is not None and lower is not None:
                    indicator_values["bb20"]["middle"] = (upper + lower) / 2

            # Add width alias for bandwidth (user-friendly naming)
            if "bandwidth" in indicator_values["bb20"]:
                indicator_values["bb20"]["width"] = indicator_values["bb20"]["bandwidth"]
            elif "width" in indicator_values["bb20"]:
                # If width exists but bandwidth doesn't, create reverse alias
                indicator_values["bb20"]["bandwidth"] = indicator_values["bb20"]["width"]

        logger.debug(f"Converted FeatureVector to {len(indicator_values)} indicators")

        return indicator_values

    def calculate_indicator_values(
        self,
        data: pd.DataFrame,
        config_path: str | Path
    ) -> dict[str, dict[str, float]]:
        """Calculate indicator values from JSON configuration.

        Args:
            data: OHLCV DataFrame with columns: open, high, low, close, volume
            config_path: Path to JSON strategy config

        Returns:
            Dict mapping indicator_id -> {field -> value}
        """
        config = self._load_config(config_path)
        return self._calculate_indicators(data, config)

    @staticmethod
    def _first_indicator_value(
        indicator_values: dict[str, dict[str, float]],
        ids: list[str],
        field: str = "value",
    ) -> float | None:
        """Return first matching indicator value for a list of IDs."""
        for indicator_id in ids:
            value = indicator_values.get(indicator_id, {}).get(field)
            if value is not None:
                return value
        return None

    def _convert_to_regime_state(
        self,
        active_regimes: list,
        indicator_values: dict[str, dict[str, float]],
        timestamp: datetime
    ) -> RegimeState:
        """Convert active regimes to legacy RegimeState format.

        Mapping logic:
        - If "extreme_downtrend" or "extreme_uptrend" active → TREND_DOWN/UP, EXTREME vol
        - If "strong_downtrend" or "strong_uptrend" active → TREND_DOWN/UP, HIGH vol
        - If "moderate_downtrend" or "moderate_uptrend" active → TREND_DOWN/UP, NORMAL vol
        - If "range_bound" active → RANGE, volatility from indicators
        - Else → RANGE, NORMAL

        Args:
            active_regimes: List of ActiveRegime objects
            indicator_values: Calculated indicator values
            timestamp: Current timestamp

        Returns:
            RegimeState
        """
        # Default values
        regime = RegimeType.RANGE
        volatility = VolatilityLevel.NORMAL
        regime_confidence = 0.5
        volatility_confidence = 0.5

        if not active_regimes:
            logger.info("No active regimes → defaulting to RANGE/NORMAL")
            return RegimeState(
                timestamp=timestamp,
                regime=regime,
                volatility=volatility,
                regime_confidence=regime_confidence,
                volatility_confidence=volatility_confidence,
                adx_value=self._first_indicator_value(indicator_values, ["adx", "adx14"]),
                atr_pct=self._calc_atr_pct_from_indicators(indicator_values),
                bb_width_pct=indicator_values.get("bb20", {}).get("width")
            )

        # Use highest priority regime
        highest = active_regimes[0]
        regime_id = highest.id.lower()

        # Map regime ID to RegimeType
        if "extreme_downtrend" in regime_id:
            regime = RegimeType.TREND_DOWN
            volatility = VolatilityLevel.EXTREME
            regime_confidence = 0.9
            volatility_confidence = 0.85
        elif "extreme_uptrend" in regime_id:
            regime = RegimeType.TREND_UP
            volatility = VolatilityLevel.EXTREME
            regime_confidence = 0.9
            volatility_confidence = 0.85
        elif "strong_downtrend" in regime_id:
            regime = RegimeType.TREND_DOWN
            volatility = VolatilityLevel.HIGH
            regime_confidence = 0.8
            volatility_confidence = 0.75
        elif "strong_uptrend" in regime_id:
            regime = RegimeType.TREND_UP
            volatility = VolatilityLevel.HIGH
            regime_confidence = 0.8
            volatility_confidence = 0.75
        elif "moderate_downtrend" in regime_id or "downtrend" in regime_id:
            regime = RegimeType.TREND_DOWN
            volatility = VolatilityLevel.NORMAL
            regime_confidence = 0.7
            volatility_confidence = 0.65
        elif "moderate_uptrend" in regime_id or "uptrend" in regime_id:
            regime = RegimeType.TREND_UP
            volatility = VolatilityLevel.NORMAL
            regime_confidence = 0.7
            volatility_confidence = 0.65
        elif "range" in regime_id:
            regime = RegimeType.RANGE
            # Determine volatility from indicators
            volume_ratio = indicator_values.get("volume_ratio", {}).get("value")
            if volume_ratio is not None:
                if volume_ratio > 2.5:
                    volatility = VolatilityLevel.EXTREME
                    volatility_confidence = 0.8
                elif volume_ratio > 1.5:
                    volatility = VolatilityLevel.HIGH
                    volatility_confidence = 0.75
                elif volume_ratio < 0.8:
                    volatility = VolatilityLevel.LOW
                    volatility_confidence = 0.7
                else:
                    volatility = VolatilityLevel.NORMAL
                    volatility_confidence = 0.65
            regime_confidence = 0.6

        # Check for high/low volatility regimes
        for active in active_regimes:
            if "high_volatility" in active.id.lower():
                volatility = VolatilityLevel.HIGH
                volatility_confidence = max(volatility_confidence, 0.75)
            elif "low_volatility" in active.id.lower():
                volatility = VolatilityLevel.LOW
                volatility_confidence = max(volatility_confidence, 0.7)

        logger.info(
            f"Mapped {len(active_regimes)} active regime(s) → {regime.name} / {volatility.name} "
            f"(regime_conf={regime_confidence:.2f}, vol_conf={volatility_confidence:.2f})"
        )

        return RegimeState(
            timestamp=timestamp,
            regime=regime,
            volatility=volatility,
            regime_confidence=regime_confidence,
            volatility_confidence=volatility_confidence,
            adx_value=self._first_indicator_value(indicator_values, ["adx", "adx14"]),
            atr_pct=self._calc_atr_pct_from_indicators(indicator_values),
            bb_width_pct=indicator_values.get("bb20", {}).get("width")
        )

    def _calc_atr_pct_from_indicators(
        self,
        indicator_values: dict[str, dict[str, float]]
    ) -> float | None:
        """Calculate ATR as percentage of price from indicator values.

        Args:
            indicator_values: Dict with indicator values

        Returns:
            ATR% or None if not available
        """
        atr = self._first_indicator_value(indicator_values, ["atr14", "atr"])

        # Try to get close price from various sources
        close = None
        for key in ["close", "price", "sma20", "sma50"]:
            if key in indicator_values and "value" in indicator_values[key]:
                close = indicator_values[key]["value"]
                break

        if atr is not None and close is not None and close > 0:
            return (atr / close) * 100

        return None

    def get_regime_descriptions(self, config_path: str | Path) -> dict[str, str]:
        """Get descriptions of all regimes in config.

        Args:
            config_path: Path to JSON config

        Returns:
            Dict mapping regime_id -> regime_name
        """
        config = self._load_config(config_path)
        return {regime.id: regime.name for regime in config.regimes}

    def list_required_indicators(self, config_path: str | Path) -> list[str]:
        """List all indicators required by config.

        Args:
            config_path: Path to JSON config

        Returns:
            List of indicator IDs
        """
        config = self._load_config(config_path)
        return [ind.id for ind in config.indicators]
