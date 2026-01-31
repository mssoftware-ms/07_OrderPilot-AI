"""Integration Bridge between JSON Config and TradingBot.

Provides adapters to integrate the new JSON-based configuration system
with the existing TradingBot architecture.

Architecture:
    JSON Config → ConfigBridge → Existing Bot Components

Components:
- IndicatorValueCalculator: Calculates indicator values from FeatureVector
- RegimeDetectorBridge: Bridges JSON RegimeDetector with RegimeState
- StrategySetAdapter: Converts MatchedStrategySet to StrategyDefinition
- ConfigBasedStrategyCatalog: Alternative to hardcoded StrategyCatalog

This bridge allows gradual migration:
- If JSON config present: use JSON-based regime/strategy detection
- If not: fallback to hardcoded strategies
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import (
    ConfigLoader,
    ConditionEvaluator,
    MatchedStrategySet,
    RegimeDetector,
    StrategyRouter,
    StrategySetExecutor,
    TradingBotConfig,
)
from .config_reloader import ConfigReloader
from .models import FeatureVector, RegimeState
from .strategy_definitions import StrategyDefinition

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class IndicatorValueCalculator:
    """Calculates indicator values from FeatureVector for condition evaluation.

    Maps FeatureVector fields to indicator_id/field format expected by
    ConditionEvaluator.

    Example:
        feature_vector.rsi = 65.5
        → {"rsi14": {"value": 65.5}}
    """

    # Mapping: indicator_id → FeatureVector field name
    INDICATOR_MAPPING = {
        # RSI
        "rsi14": "rsi",
        "rsi": "rsi",

        # ADX
        "adx14": "adx",
        "adx": "adx",

        # MACD - all common naming variants
        "macd": "macd",
        "macd_signal": "macd_signal",
        "macd_histogram": "macd_histogram",
        "macd12_26_9": "macd",  # Alias: macd12_26_9 → macd
        "macd_12_26_9": "macd",  # Alias
        "macd_line": "macd",  # Alias

        # SMA
        "sma20": "sma_fast",
        "sma50": "sma_slow",
        "sma_fast": "sma_fast",
        "sma_slow": "sma_slow",

        # EMA
        "ema12": "ema_fast",
        "ema26": "ema_slow",
        "ema_fast": "ema_fast",
        "ema_slow": "ema_slow",

        # Bollinger Bands - all common naming variants
        "bb_upper": "bb_upper",
        "bb_middle": "bb_middle",
        "bb_lower": "bb_lower",
        "bb_width": "bb_width",
        "bbands20_upper": "bb_upper",  # Alias
        "bbands20_middle": "bb_middle",  # Alias
        "bbands20_lower": "bb_lower",  # Alias
        "bbands20_width": "bb_width",  # Alias
        "bbands_upper": "bb_upper",  # Alias
        "bbands_middle": "bb_middle",  # Alias
        "bbands_lower": "bb_lower",  # Alias
        "bbands_width": "bb_width",  # Alias

        # ATR
        "atr14": "atr",
        "atr": "atr",

        # Stochastic - all common naming variants
        "stoch_k": "stoch_k",
        "stoch_d": "stoch_d",
        "stoch14_k": "stoch_k",  # Alias
        "stoch14_d": "stoch_d",  # Alias
        "stochastic_k": "stoch_k",  # Alias
        "stochastic_d": "stoch_d",  # Alias

        # CCI
        "cci20": "cci",
        "cci": "cci",

        # MFI
        "mfi14": "mfi",
        "mfi": "mfi",

        # Volume - including ratio (uses volume_sma if available)
        "volume": "volume",
        "volume_sma": "volume_sma",
        "volume_ratio": "volume_ratio",  # Calculated field

        # Price
        "close": "close",
        "open": "open",
        "high": "high",
        "low": "low",

        # Derived indicators - map to closest available
        # These are calculated from other indicators in FeatureVector
        "momentum_score": "rsi",  # Fallback: use RSI as momentum proxy
        "price_strength": "adx",  # Fallback: use ADX as strength proxy

        # Choppiness Index (range detection)
        "chop": "adx",  # Fallback: use inverted ADX logic (low ADX = choppy)
        "chop14": "adx",  # Alias: chop14 → adx
        "choppiness": "adx",  # Alias

        # Additional Bollinger Band aliases
        "bb20": "bb_width",  # Alias: bb20 → bb_width (general BB reference)
        "bb20_upper": "bb_upper",  # Alias
        "bb20_middle": "bb_middle",  # Alias
        "bb20_lower": "bb_lower",  # Alias
        "bb20_width": "bb_width",  # Alias
    }

    @classmethod
    def calculate_indicator_values(
        cls,
        feature_vector: FeatureVector
    ) -> dict[str, dict[str, float]]:
        """Calculate indicator values from FeatureVector.

        Args:
            feature_vector: Current feature vector from FeatureEngine

        Returns:
            Dict mapping indicator_id → {field → value}
            Format: {"rsi14": {"value": 65.5}, "adx14": {"value": 30}, ...}
        """
        indicator_values = {}

        for indicator_id, feature_field in cls.INDICATOR_MAPPING.items():
            # Get value from FeatureVector
            value = getattr(feature_vector, feature_field, None)

            if value is not None:
                # Convert to float if needed
                if isinstance(value, (int, float)):
                    indicator_values[indicator_id] = {"value": float(value)}
                else:
                    # Skip non-numeric values
                    logger.debug(
                        f"Skipping non-numeric value for {indicator_id}: {type(value)}"
                    )

        # ========== Composite Indicators ==========
        # Add composite indicators with multiple sub-fields

        # Bollinger Bands composite: bb20, bbands20
        for bb_alias in ["bb20", "bbands20", "bb", "bbands"]:
            bb_upper = getattr(feature_vector, "bb_upper", None)
            bb_middle = getattr(feature_vector, "bb_middle", None)
            bb_lower = getattr(feature_vector, "bb_lower", None)
            bb_width = getattr(feature_vector, "bb_width", None)

            if bb_upper is not None or bb_middle is not None:
                indicator_values[bb_alias] = {
                    "value": float(bb_middle) if bb_middle else 0.0,
                    "upper": float(bb_upper) if bb_upper else 0.0,
                    "middle": float(bb_middle) if bb_middle else 0.0,
                    "lower": float(bb_lower) if bb_lower else 0.0,
                    "width": float(bb_width) if bb_width else 0.0,
                }

        # MACD composite: macd12_26_9
        for macd_alias in ["macd12_26_9", "macd_12_26_9"]:
            macd = getattr(feature_vector, "macd", None)
            macd_signal = getattr(feature_vector, "macd_signal", None)
            macd_histogram = getattr(feature_vector, "macd_histogram", None)

            if macd is not None:
                indicator_values[macd_alias] = {
                    "value": float(macd),
                    "line": float(macd),
                    "signal": float(macd_signal) if macd_signal else 0.0,
                    "histogram": float(macd_histogram) if macd_histogram else 0.0,
                }

        # Stochastic composite: stoch14
        for stoch_alias in ["stoch14", "stochastic"]:
            stoch_k = getattr(feature_vector, "stoch_k", None)
            stoch_d = getattr(feature_vector, "stoch_d", None)

            if stoch_k is not None:
                indicator_values[stoch_alias] = {
                    "value": float(stoch_k),
                    "k": float(stoch_k),
                    "d": float(stoch_d) if stoch_d else 0.0,
                }

        logger.debug(
            f"Calculated {len(indicator_values)} indicator values from FeatureVector"
        )

        return indicator_values


class RegimeDetectorBridge:
    """Bridge between JSON-based RegimeDetector and existing RegimeState.

    Allows bot to use JSON-defined regimes while maintaining compatibility
    with existing RegimeState structure.
    """

    def __init__(self, regime_detector: RegimeDetector):
        """Initialize bridge with JSON-based regime detector.

        Args:
            regime_detector: RegimeDetector instance from JSON config
        """
        self.regime_detector = regime_detector
        logger.info("RegimeDetectorBridge initialized")

    def detect_regime_from_features(
        self,
        feature_vector: FeatureVector
    ) -> RegimeState:
        """Detect market regime from feature vector.

        Args:
            feature_vector: Current feature vector from FeatureEngine

        Returns:
            RegimeState compatible with existing bot code
        """
        # Calculate indicator values
        indicator_values = IndicatorValueCalculator.calculate_indicator_values(
            feature_vector
        )

        # Detect active regimes
        active_regimes = self.regime_detector.detect_active_regimes(indicator_values)

        # Convert to RegimeState
        if active_regimes:
            # Use highest priority regime
            primary_regime = active_regimes[0]  # Already sorted by priority

            regime_state = RegimeState(
                trending=primary_regime.id == "trending" or "trend" in primary_regime.id.lower(),
                ranging=primary_regime.id == "range" or "range" in primary_regime.id.lower(),
                volatile="volatile" in primary_regime.id.lower() or "breakout" in primary_regime.id.lower(),
                regime_strength=primary_regime.confidence,
                regime_name=primary_regime.name,
                last_updated=primary_regime.activated_at,
            )

            logger.debug(
                f"Detected regime: {regime_state.regime_name} "
                f"(strength: {regime_state.regime_strength:.2f})"
            )

            return regime_state
        else:
            # No regime detected - return neutral state
            logger.debug("No regime detected - returning neutral state")
            return RegimeState(
                trending=False,
                ranging=False,
                volatile=False,
                regime_strength=0.0,
                regime_name="neutral",
            )


class ConfigBasedStrategyCatalog:
    """Alternative to hardcoded StrategyCatalog using JSON config.

    Provides the same interface as StrategyCatalog but loads strategies
    from JSON configuration instead of hardcoded templates.

    This allows gradual migration:
    - Old code: StrategyCatalog (hardcoded)
    - New code: ConfigBasedStrategyCatalog (JSON)
    """

    def __init__(
        self,
        config: TradingBotConfig,
        feature_vector: FeatureVector | None = None,
        config_reloader: ConfigReloader | None = None
    ):
        """Initialize catalog from JSON config.

        Args:
            config: Loaded TradingBotConfig from JSON
            feature_vector: Optional current feature vector for regime detection
            config_reloader: Optional ConfigReloader for live reloading
        """
        self.config = config
        self.config_reloader = config_reloader

        # Initialize components
        self.regime_detector = RegimeDetector(config.regimes)
        self.strategy_router = StrategyRouter(config.routing, config.strategy_sets)
        self.strategy_executor = StrategySetExecutor(
            config.indicators,
            config.strategies
        )

        # Bridges
        self.regime_bridge = RegimeDetectorBridge(self.regime_detector)

        logger.info(
            f"ConfigBasedStrategyCatalog initialized: "
            f"{len(config.indicators)} indicators, "
            f"{len(config.regimes)} regimes, "
            f"{len(config.strategies)} strategies, "
            f"{len(config.strategy_sets)} strategy sets"
        )

    def get_active_strategy_sets(
        self,
        feature_vector: FeatureVector
    ) -> list[MatchedStrategySet]:
        """Get active strategy sets for current market conditions.

        Args:
            feature_vector: Current feature vector from FeatureEngine

        Returns:
            List of matched strategy sets
        """
        # Calculate indicator values
        indicator_values = IndicatorValueCalculator.calculate_indicator_values(
            feature_vector
        )

        # Detect active regimes
        active_regimes = self.regime_detector.detect_active_regimes(indicator_values)

        # Route to strategy sets
        matched_sets = self.strategy_router.route_regimes(active_regimes)

        logger.info(
            f"Active strategy sets: {len(matched_sets)} "
            f"(from {len(active_regimes)} active regimes)"
        )

        return matched_sets

    def get_current_regime(
        self,
        feature_vector: FeatureVector
    ) -> RegimeState:
        """Get current market regime as RegimeState.

        Args:
            feature_vector: Current feature vector from FeatureEngine

        Returns:
            RegimeState compatible with existing bot code
        """
        return self.regime_bridge.detect_regime_from_features(feature_vector)

    def get_strategy_ids_from_sets(
        self,
        matched_sets: list[MatchedStrategySet]
    ) -> list[str]:
        """Extract strategy IDs from matched strategy sets.

        Args:
            matched_sets: List of matched strategy sets

        Returns:
            List of strategy IDs to execute
        """
        strategy_ids = []

        for matched_set in matched_sets:
            ids = self.strategy_executor.get_strategy_ids_from_set(
                matched_set.strategy_set
            )
            strategy_ids.extend(ids)

        return strategy_ids

    # ==================== Compatibility Methods ====================
    # These methods maintain compatibility with existing StrategyCatalog interface

    def get_strategy(self, strategy_id: str) -> StrategyDefinition | None:
        """Get strategy by ID (for compatibility).

        Note: Returns None for JSON-based strategies since they don't use
        the StrategyDefinition format. Use get_active_strategy_sets() instead.

        Args:
            strategy_id: Strategy identifier

        Returns:
            None (JSON strategies don't use StrategyDefinition)
        """
        logger.warning(
            f"get_strategy('{strategy_id}') called on ConfigBasedStrategyCatalog. "
            f"JSON strategies don't use StrategyDefinition. "
            f"Use get_active_strategy_sets() instead."
        )
        return None

    def get_all_strategies(self) -> list[StrategyDefinition]:
        """Get all strategies (for compatibility).

        Note: Returns empty list since JSON strategies don't use
        StrategyDefinition format.

        Returns:
            Empty list
        """
        logger.warning(
            "get_all_strategies() called on ConfigBasedStrategyCatalog. "
            "JSON strategies don't use StrategyDefinition. "
            "Use get_active_strategy_sets() instead."
        )
        return []

    def list_strategies(self) -> list[str]:
        """List all strategy IDs.

        Returns:
            List of strategy IDs from JSON config
        """
        return [s.id for s in self.config.strategies]

    def list_strategy_sets(self) -> list[str]:
        """List all strategy set IDs.

        Returns:
            List of strategy set IDs from JSON config
        """
        return [s.id for s in self.config.strategy_sets]

    def list_regimes(self) -> list[str]:
        """List all regime IDs.

        Returns:
            List of regime IDs from JSON config
        """
        return [r.id for r in self.config.regimes]

    # ==================== Config Reloading ====================

    def reload_config(self, new_config: TradingBotConfig | None = None) -> None:
        """Reload configuration (thread-safe).

        Reinitializes all components with new config. Can be called
        with explicit config or will use ConfigReloader if available.

        Args:
            new_config: New config to load, or None to reload from ConfigReloader

        Raises:
            ValueError: If neither new_config nor config_reloader provided
        """
        import threading

        # Get new config
        if new_config is None:
            if self.config_reloader is None:
                raise ValueError("No config provided and no ConfigReloader available")
            new_config = self.config_reloader.reload_config()

        # Rebuild components with new config
        logger.info(f"Reloading catalog with new config...")

        # Thread-safe update
        with threading.RLock():
            self.config = new_config

            # Rebuild components
            self.regime_detector = RegimeDetector(new_config.regimes)
            self.strategy_router = StrategyRouter(
                new_config.routing,
                new_config.strategy_sets
            )
            self.strategy_executor = StrategySetExecutor(
                new_config.indicators,
                new_config.strategies
            )
            self.regime_bridge = RegimeDetectorBridge(self.regime_detector)

        logger.info(
            f"Catalog reloaded: "
            f"{len(new_config.indicators)} indicators, "
            f"{len(new_config.regimes)} regimes, "
            f"{len(new_config.strategies)} strategies, "
            f"{len(new_config.strategy_sets)} strategy sets"
        )

    def enable_auto_reload(
        self,
        config_path: Path | str,
        schema_path: Path | str | None = None,
        event_bus: "EventBus | None" = None
    ) -> None:
        """Enable automatic config reloading with file watching.

        Args:
            config_path: Path to JSON config file
            schema_path: Path to JSON schema (optional)
            event_bus: Event bus for reload events (optional)
        """
        if self.config_reloader is not None:
            logger.warning("Auto-reload already enabled")
            return

        # Create reloader with callback
        self.config_reloader = ConfigReloader(
            config_path=config_path,
            schema_path=schema_path,
            on_reload=self.reload_config,
            event_bus=event_bus,
            auto_reload=True
        )

        # Start watching
        self.config_reloader.start_watching()
        logger.info(f"Auto-reload enabled for {config_path}")

    def disable_auto_reload(self) -> None:
        """Disable automatic config reloading."""
        if self.config_reloader is None:
            logger.debug("Auto-reload not enabled")
            return

        self.config_reloader.stop_watching()
        logger.info("Auto-reload disabled")


def load_json_config_if_available(
    config_path: Path | str | None = None
) -> TradingBotConfig | None:
    """Load JSON config if available, otherwise return None.

    Args:
        config_path: Optional path to JSON config file.
                    If None, tries default locations.

    Returns:
        Loaded TradingBotConfig or None if not found/invalid
    """
    if config_path is None:
        # Try default locations
        from pathlib import Path

        default_paths = [
            Path("03_JSON/Trading_Bot/configs/active_config.json"),
            Path("config/trading_bot_config.json"),
            Path("trading_bot_config.json"),
        ]

        for path in default_paths:
            if path.exists():
                config_path = path
                break

    if config_path is None:
        logger.info("No JSON config found - using hardcoded strategies")
        return None

    try:
        loader = ConfigLoader()
        config = loader.load_config(config_path)
        logger.info(f"Loaded JSON config from: {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load JSON config from {config_path}: {e}")
        return None


def create_strategy_catalog(
    feature_vector: FeatureVector | None = None,
    json_config_path: Path | str | None = None
) -> ConfigBasedStrategyCatalog | None:
    """Factory function: Create strategy catalog from JSON or fallback to hardcoded.

    Args:
        feature_vector: Optional current feature vector
        json_config_path: Optional path to JSON config

    Returns:
        ConfigBasedStrategyCatalog if JSON config available, None otherwise
        (caller should fallback to hardcoded StrategyCatalog)
    """
    config = load_json_config_if_available(json_config_path)

    if config:
        return ConfigBasedStrategyCatalog(config, feature_vector)
    else:
        return None
