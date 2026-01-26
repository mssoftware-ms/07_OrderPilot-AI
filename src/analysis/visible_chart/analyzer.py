"""Visible Chart Analyzer.

Orchestrates the analysis of the visible chart range,
generating entry signals using features, regime detection,
and signal scoring.

Phase 1: MVP with rules-based detection.
Phase 2: FastOptimizer integration for parameter optimization.
Phase 2.6: Caching & Wiederverwendung.
Issue #27: Comprehensive debug logging.
Issue #28: JSON-based parameter loading (replaces hardcoded OptimParams).
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from .cache import AnalyzerCache, get_analyzer_cache
from .candle_loader import CandleLoader
from .types import (
    AnalysisResult,
    EntryEvent,
    EntrySide,
    IndicatorSet,
    RegimeType,
    VisibleRange,
)

logger = logging.getLogger(__name__)

# Import debug logger for Issue #27
try:
    from .debug_logger import debug_logger
except ImportError:
    debug_logger = logger


class VisibleChartAnalyzer:
    """Analyzes visible chart range and generates entry signals.

    This is the main orchestrator that:
    1. Loads candle data for the visible range
    2. Calculates features
    3. Detects market regime
    4. Scores potential entries
    5. Returns entry events for overlay rendering

    MVP implementation uses simple rules-based detection.
    Later phases will add optimization and ML components.
    """

    def __init__(
        self,
        use_optimizer: bool = False,
        use_cache: bool = True,
        cache: AnalyzerCache | None = None,
        json_config_path: Path | str | None = None,
    ) -> None:
        """Initialize the analyzer.

        Args:
            use_optimizer: If True, use FastOptimizer for parameter tuning.
            use_cache: If True, use caching for features/regime/optimizer.
            cache: Optional custom cache instance. Uses global if None.
            json_config_path: Path to JSON config file (entry_analyzer_regime.json).
                             If provided, parameters are loaded from this file
                             instead of using hardcoded defaults.
        """
        self._candle_loader = CandleLoader()
        self._use_optimizer = use_optimizer
        self._use_cache = use_cache
        self._cache = cache if cache else get_analyzer_cache()
        self._optimizer = None
        self._last_symbol: str | None = None
        self._last_regime: RegimeType | None = None
        self._json_config_path: Path | None = (
            Path(json_config_path) if json_config_path else None
        )
        self._cached_optim_params: Any = None  # Cache loaded params
        self._cached_regime_config: dict | None = None  # Cache regime config for v2 detection

    def _get_optim_params(self) -> Any:
        """Get OptimParams from JSON config or use defaults.

        Loads parameters from the JSON config file if available.
        Caches the loaded params to avoid repeated file reads.

        Returns:
            OptimParams instance (from JSON or defaults)
        """
        from src.analysis.entry_signals.entry_signal_engine import OptimParams

        # Return cached params if available
        if self._cached_optim_params is not None:
            return self._cached_optim_params

        # Try to load from JSON config
        if self._json_config_path is not None:
            from src.analysis.entry_signals.params_loader import (
                load_optim_params_from_json,
            )

            self._cached_optim_params = load_optim_params_from_json(
                self._json_config_path
            )
            logger.info(
                "Loaded OptimParams from JSON: %s", self._json_config_path
            )
            return self._cached_optim_params

        # Fallback to defaults
        self._cached_optim_params = OptimParams()
        return self._cached_optim_params

    def set_json_config_path(self, json_path: Path | str | None) -> None:
        """Set or update the JSON config path.

        Clears cached params so they will be reloaded on next use.

        Args:
            json_path: Path to JSON config file, or None to use defaults
        """
        self._json_config_path = Path(json_path) if json_path else None
        self._cached_optim_params = None  # Clear cache
        self._cached_regime_config = None  # Clear regime config cache
        logger.info("JSON config path updated: %s", self._json_config_path)

    def _get_regime_config(self) -> dict | None:
        """Get regime config from JSON for v2 detection.

        Returns:
            Regime config dict or None if not available.
        """
        if self._cached_regime_config is not None:
            return self._cached_regime_config

        if self._json_config_path is None or not self._json_config_path.exists():
            return None

        try:
            import json
            with open(self._json_config_path, "r", encoding="utf-8") as f:
                self._cached_regime_config = json.load(f)
            logger.debug("Loaded regime config from %s", self._json_config_path)
            return self._cached_regime_config
        except Exception as e:
            logger.warning("Failed to load regime config: %s", e)
            return None

    def analyze(
        self,
        visible_range: VisibleRange,
        symbol: str,
        timeframe: str = "1m",
    ) -> AnalysisResult:
        """Analyze the visible chart range (loads candles from database).

        Args:
            visible_range: The visible time range.
            symbol: Trading symbol.
            timeframe: Chart timeframe (default 1m).

        Returns:
            AnalysisResult with entries and indicator set info.
        """
        # Load candles from database/mock
        candles = self._candle_loader.load(
            symbol=symbol,
            from_ts=visible_range.from_ts,
            to_ts=visible_range.to_ts,
            timeframe=timeframe,
        )
        return self.analyze_with_candles(visible_range, symbol, timeframe, candles)

    def analyze_with_candles(
        self,
        visible_range: VisibleRange,
        symbol: str,
        timeframe: str,
        candles: list[dict],
    ) -> AnalysisResult:
        """Analyze with pre-loaded candle data.

        Use this when candles are already available (e.g., from chart widget).

        Args:
            visible_range: The visible time range.
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            candles: Pre-loaded candle data.

        Returns:
            AnalysisResult with entries and indicator set info.
        """
        start_time = time.perf_counter()

        # Issue #27: Comprehensive debug logging
        debug_logger.info("=" * 80)
        debug_logger.info("ENTRY ANALYZER: Starting new analysis")
        debug_logger.info("Symbol: %s | Timeframe: %s", symbol, timeframe)
        debug_logger.info("Visible Range: %d - %d (%d min)",
                         visible_range.from_ts, visible_range.to_ts,
                         visible_range.duration_minutes)
        debug_logger.info("Candles provided: %d", len(candles) if candles else 0)
        debug_logger.info("Optimizer enabled: %s | Cache enabled: %s",
                         self._use_optimizer, self._use_cache)

        # Check for re-optimize trigger (symbol or regime change)
        symbol_changed = self._last_symbol is not None and self._last_symbol != symbol
        if symbol_changed:
            logger.info("Symbol changed: %s -> %s, invalidating cache", self._last_symbol, symbol)
            debug_logger.info("SYMBOL CHANGE DETECTED: %s -> %s (cache invalidated)",
                            self._last_symbol, symbol)
            if self._use_cache:
                self._cache.invalidate_symbol(self._last_symbol)
        self._last_symbol = symbol

        logger.info(
            "Starting analysis for %s [%d - %d] (%d min) with %d candles",
            symbol,
            visible_range.from_ts,
            visible_range.to_ts,
            visible_range.duration_minutes,
            len(candles) if candles else 0,
        )

        if not candles:
            logger.warning("No candles found for visible range")
            debug_logger.warning("ANALYSIS ABORTED: No candles available")
            debug_logger.info("=" * 80)
            return AnalysisResult(
                visible_range=visible_range,
                analysis_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Step 2: Calculate features (with cache)
        debug_logger.info("STEP 2: Calculating features...")
        feature_start = time.perf_counter()
        features = self._get_or_calculate_features(
            candles, symbol, timeframe, visible_range
        )
        feature_time = (time.perf_counter() - feature_start) * 1000
        debug_logger.info("Features calculated in %.1fms (cached: %s)",
                         feature_time, hasattr(features, '_cached'))

        # Step 3: Detect regime (with cache)
        debug_logger.info("STEP 3: Detecting market regime...")
        regime_start = time.perf_counter()
        regime = self._get_or_detect_regime(
            features, symbol, timeframe, visible_range
        )
        regime_time = (time.perf_counter() - regime_start) * 1000
        debug_logger.info("Regime detected: %s (took %.1fms)", regime.value, regime_time)

        # Check for regime change trigger
        regime_changed = self._last_regime is not None and self._last_regime != regime
        if regime_changed:
            logger.info("Regime changed: %s -> %s", self._last_regime.value, regime.value)
            debug_logger.warning("REGIME CHANGE: %s -> %s", self._last_regime.value, regime.value)
        self._last_regime = regime

        # Step 4 & 5: Generate entries (with or without optimization)
        debug_logger.info("STEP 4: Generating entry signals...")
        entry_start = time.perf_counter()
        if self._use_optimizer:
            debug_logger.info("Using FastOptimizer for parameter tuning...")
            # Check optimizer cache first
            result = self._get_or_run_optimizer(
                candles, regime, features, symbol, timeframe, visible_range
            )
            active_set = result.get("active_set")
            alternatives = result.get("alternatives", [])
            entries = result.get("entries", [])
            debug_logger.info("Optimizer result: %d entries, %d alternative sets",
                            len(entries), len(alternatives))
            if not entries:
                debug_logger.warning(
                    "Optimizer produced no entries; falling back to rules-based scoring."
                )
                active_set = active_set or self._create_default_set(regime)
                entries = self._score_entries(candles, features, regime)
                debug_logger.info("Fallback scored %d raw entries", len(entries))
                entries = self._postprocess_entries(entries)
                debug_logger.info("Fallback postprocessing: %d entries", len(entries))
        else:
            debug_logger.info("Using default rules-based detection...")
            # Phase 1: Default rules-based
            active_set = self._create_default_set(regime)
            debug_logger.debug("Default indicator set created: %s", active_set)
            entries = self._score_entries(candles, features, regime)
            debug_logger.info("Scored %d raw entries", len(entries))
            entries = self._postprocess_entries(entries)
            debug_logger.info("After postprocessing: %d entries", len(entries))
            alternatives = []
        entry_time = (time.perf_counter() - entry_start) * 1000
        debug_logger.info("Entry generation completed in %.1fms", entry_time)

        analysis_time = (time.perf_counter() - start_time) * 1000

        # Log cache stats periodically
        if self._use_cache:
            stats = self._cache.get_stats()
            if (stats.hits + stats.misses) % 10 == 0:
                logger.debug(
                    "Cache stats: hit_rate=%.1f%%, hits=%d, misses=%d",
                    stats.hit_rate * 100,
                    stats.hits,
                    stats.misses,
                )
                debug_logger.debug("Cache stats: hit_rate=%.1f%%, hits=%d, misses=%d",
                                 stats.hit_rate * 100, stats.hits, stats.misses)

        logger.info(
            "Analysis complete: %d entries, regime=%s, optimized=%s, took %.1fms",
            len(entries),
            regime.value,
            self._use_optimizer,
            analysis_time,
        )

        # Issue #27: Final summary
        debug_logger.info("=" * 80)
        debug_logger.info("ANALYSIS COMPLETE:")
        debug_logger.info("  Total time: %.1fms", analysis_time)
        debug_logger.info("  Feature calc: %.1fms", feature_time)
        debug_logger.info("  Regime detect: %.1fms", regime_time)
        debug_logger.info("  Entry generation: %.1fms", entry_time)
        debug_logger.info("  Entries found: %d", len(entries))
        debug_logger.info("  Regime: %s", regime.value)
        debug_logger.info("  Indicator set: %s", active_set.name if active_set else "None")
        debug_logger.info("=" * 80)

        return AnalysisResult(
            entries=entries,
            active_set=active_set,
            alternative_sets=alternatives,
            regime=regime,
            visible_range=visible_range,
            analysis_time_ms=analysis_time,
            candle_count=len(candles),
            candles=candles,
        )

    def _get_or_calculate_features(
        self,
        candles: list[dict],
        symbol: str,
        timeframe: str,
        visible_range: VisibleRange,
    ) -> dict[str, list[float]]:
        """Get features from cache or calculate them.

        Args:
            candles: Candle data.
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            visible_range: Visible time range.

        Returns:
            Feature dictionary.
        """
        if self._use_cache:
            cached = self._cache.get_features(symbol, timeframe, visible_range)
            if cached is not None:
                return cached

        features = self._calculate_features(candles)

        if self._use_cache and features:
            self._cache.set_features(symbol, timeframe, visible_range, features)

        return features

    def _get_or_detect_regime(
        self,
        features: dict[str, list[float]],
        symbol: str,
        timeframe: str,
        visible_range: VisibleRange,
    ) -> RegimeType:
        """Get regime from cache or detect it.

        Args:
            features: Calculated features.
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            visible_range: Visible time range.

        Returns:
            Detected regime type.
        """
        if self._use_cache:
            cached = self._cache.get_regime(symbol, timeframe, visible_range)
            if cached is not None:
                return cached

        regime = self._detect_regime(features)

        if self._use_cache:
            self._cache.set_regime(symbol, timeframe, visible_range, regime)

        return regime

    def _get_or_run_optimizer(
        self,
        candles: list[dict],
        regime: RegimeType,
        features: dict[str, list[float]],
        symbol: str,
        timeframe: str,
        visible_range: VisibleRange,
    ) -> dict[str, Any]:
        """Get optimizer result from cache or run it.

        Args:
            candles: Candle data.
            regime: Detected regime.
            features: Calculated features.
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            visible_range: Visible time range.

        Returns:
            Dict with active_set, alternatives, and entries.
        """
        if self._use_cache:
            cached = self._cache.get_optimizer_result(
                symbol, timeframe, visible_range, regime
            )
            if cached is not None:
                return cached

        result = self._run_optimizer(candles, regime, features)

        if self._use_cache:
            self._cache.set_optimizer_result(
                symbol, timeframe, visible_range, regime, result
            )

        return result

    def _calculate_features(self, candles: list[dict]) -> dict[str, list[float]]:
        """Calculate technical features from candles.

        Uses ATR-normalized features from entry_signal_engine for better
        scale handling on 1m/5m timeframes.

        Args:
            candles: List of candle dicts.

        Returns:
            Dict of feature name -> values.
        """
        from src.analysis.entry_signals.entry_signal_engine import (
            calculate_features,
        )

        if len(candles) < 20:
            return {}

        # Use params from JSON config or defaults
        params = self._get_optim_params()
        features = calculate_features(candles, params)

        # Add backward-compatible keys for any existing code
        if "closes" in features:
            closes = features["closes"]
            features["sma_20"] = features.get("ema_slow", closes)

            # Convert ATR-normalized distance back to percentage for compatibility
            if "dist_ema_atr" in features and "atr" in features:
                dist = features["dist_ema_atr"]
                atr = features["atr"]
                ema_slow = features.get("ema_slow", closes)
                price_vs_sma = []
                for i in range(len(closes)):
                    if ema_slow[i] != 0:
                        price_vs_sma.append((closes[i] - ema_slow[i]) / ema_slow[i])
                    else:
                        price_vs_sma.append(0.0)
                features["price_vs_sma"] = price_vs_sma

            # Use ATR% as volatility
            features["volatility"] = features.get("atr_pct", [0.0] * len(closes))

        return features

    def _detect_regime(self, features: dict[str, list[float]]) -> RegimeType:
        """Detect market regime from features.

        Uses dynamic JSON-based detection (v2) if config is available,
        otherwise falls back to hardcoded detection.

        Args:
            features: Calculated features.

        Returns:
            Detected regime type.
        """
        if not features or "closes" not in features:
            return RegimeType.NO_TRADE

        # Try v2 detection with JSON config (dynamic thresholds)
        regime_config = self._get_regime_config()
        if regime_config is not None:
            from src.analysis.entry_signals.entry_signal_engine import (
                detect_regime_v2,
            )

            regime_id = detect_regime_v2(features, regime_config)
            logger.debug("detect_regime_v2 returned: %s", regime_id)

            # Convert string to RegimeType enum
            return RegimeType.from_string(regime_id)

        # Fallback to legacy detection (hardcoded thresholds)
        from src.analysis.entry_signals.entry_signal_engine import (
            detect_regime,
        )

        params = self._get_optim_params()
        return detect_regime(features, params)

    def _create_default_set(self, regime: RegimeType) -> IndicatorSet:
        """Create default indicator set for regime.

        MVP: Hardcoded defaults per regime.
        Later: Optimizer will find best parameters.

        Args:
            regime: Current market regime.

        Returns:
            Default indicator set.
        """
        if regime in (RegimeType.TREND_UP, RegimeType.TREND_DOWN):
            return IndicatorSet(
                name="Trend Following",
                regime=regime,
                score=0.75,
                parameters={
                    "trend": {"sma_length": 20, "adx_threshold": 25},
                    "momentum": {"rsi_length": 14, "rsi_oversold": 30, "rsi_overbought": 70},
                    "stop": {"atr_mult": 2.0},
                },
                families=["Trend", "Momentum", "Volatility"],
                description="Trend-following setup with pullback entries",
            )
        elif regime == RegimeType.RANGE:
            return IndicatorSet(
                name="Mean Reversion",
                regime=regime,
                score=0.70,
                parameters={
                    "mean_rev": {"bb_length": 20, "bb_std": 2.0},
                    "momentum": {"rsi_length": 14, "rsi_oversold": 25, "rsi_overbought": 75},
                    "stop": {"atr_mult": 1.5},
                },
                families=["Mean Reversion", "Momentum", "Volatility"],
                description="Range-bound mean reversion",
            )
        elif regime == RegimeType.SQUEEZE:
            return IndicatorSet(
                name="Breakout",
                regime=regime,
                score=0.65,
                parameters={
                    "squeeze": {"bb_length": 20, "kc_length": 20, "kc_mult": 1.5},
                    "volume": {"vol_ma": 20, "vol_mult": 1.5},
                    "stop": {"atr_mult": 2.5},
                },
                families=["Squeeze", "Volume", "Volatility"],
                description="Squeeze breakout setup",
            )
        else:
            return IndicatorSet(
                name="Conservative",
                regime=regime,
                score=0.50,
                parameters={
                    "filter": {"min_confidence": 0.8},
                    "stop": {"atr_mult": 3.0},
                },
                families=["Filter"],
                description="Conservative setup for uncertain conditions",
            )

    def _score_entries(
        self,
        candles: list[dict],
        features: dict[str, list[float]],
        regime: RegimeType,
    ) -> list[EntryEvent]:
        """Score potential entries across all candles.

        Uses robust ATR-normalized entry logic from entry_signal_engine.

        Args:
            candles: List of candles.
            features: Calculated features.
            regime: Current regime.

        Returns:
            List of detected entry events.
        """
        from src.analysis.entry_signals.entry_signal_engine import (
            generate_entries,
        )

        if regime == RegimeType.NO_TRADE:
            return []

        # Use params from JSON config or defaults
        # Enum values are now directly compatible (lowercase)
        params = self._get_optim_params()
        engine_entries = generate_entries(candles, features, regime, params)

        # Convert engine entries to analyzer entries
        # (They're now compatible, but we still convert for type safety)
        entries = []
        for e in engine_entries:
            entries.append(
                EntryEvent(
                    timestamp=e.timestamp,
                    side=e.side,  # Directly compatible
                    confidence=e.confidence,
                    price=e.price,
                    reason_tags=e.reason_tags,
                    regime=regime,
                )
            )

        debug_logger.info(
            "Generated %d entries using entry_signal_engine (regime=%s)",
            len(entries),
            regime.value,
        )

        return entries

    def _postprocess_entries(self, entries: list[EntryEvent]) -> list[EntryEvent]:
        """Apply postprocessing rules to entries.

        Note: The new entry_signal_engine already does clustering and cooldown,
        so this only applies optional rate limiting.

        Args:
            entries: Raw entry events.

        Returns:
            Filtered entry events.
        """
        if not entries:
            return entries

        # Sort by timestamp
        entries = sorted(entries, key=lambda e: e.timestamp)

        # Optional: Rate limiting (max signals per hour)
        # This is a safety measure; the engine already has cooldown
        max_per_hour = 12  # Increased from 6 since engine handles spacing
        if len(entries) > max_per_hour:
            # Keep highest confidence signals
            filtered = sorted(entries, key=lambda e: -e.confidence)[:max_per_hour]
            filtered = sorted(filtered, key=lambda e: e.timestamp)

            debug_logger.debug(
                "Postprocess: %d -> %d entries (rate limit only)",
                len(entries),
                len(filtered),
            )
            return filtered

        return entries

    def _run_optimizer(
        self,
        candles: list[dict],
        regime: RegimeType,
        features: dict[str, list[float]],
    ) -> dict[str, Any]:
        """Run FastOptimizer to find optimal indicator set.

        Now uses the FastOptimizer from indicator_optimization.

        Args:
            candles: Candle data.
            regime: Detected regime.
            features: Pre-calculated features.

        Returns:
            Dict with active_set, alternatives, and entries.
        """
        from src.analysis.entry_signals.entry_signal_engine import (
            generate_entries,
        )
        from src.analysis.indicator_optimization.optimizer import FastOptimizer

        # Use params from JSON config as base for optimization
        base_params = self._get_optim_params()
        optimizer = FastOptimizer()
        optimized_params = optimizer.optimize(
            candles, base_params=base_params, budget_ms=1200, seed=42
        )

        # Generate entries with optimized parameters
        # Recalculate features with new params
        from src.analysis.entry_signals.entry_signal_engine import calculate_features
        
        opt_features = calculate_features(candles, optimized_params)
        engine_entries = generate_entries(candles, opt_features, regime, optimized_params)

        # Convert engine entries to analyzer entries
        entries = []
        for e in engine_entries:
            entries.append(
                EntryEvent(
                    timestamp=e.timestamp,
                    side=e.side,
                    confidence=e.confidence,
                    price=e.price,
                    reason_tags=e.reason_tags,
                    regime=regime,
                )
            )

        # Create indicator set from optimized params
        active_set = self._create_optimized_set(regime, optimized_params)

        debug_logger.info(
            "Optimizer: %d entries with optimized params (regime=%s)",
            len(entries),
            regime.value,
        )

        return {
            "active_set": active_set,
            "alternatives": [],
            "entries": entries,
        }

    def _create_optimized_set(self, regime: RegimeType, params: Any) -> IndicatorSet:
        """Create indicator set from optimized parameters.

        Args:
            regime: Current regime.
            params: Optimized OptimParams.

        Returns:
            IndicatorSet with optimized parameters.
        """
        return IndicatorSet(
            name=f"Optimized {regime.value}",
            regime=regime,
            score=0.85,  # Higher score for optimized params
            parameters={
                "ema_fast": params.ema_fast,
                "ema_slow": params.ema_slow,
                "atr_period": params.atr_period,
                "rsi_period": params.rsi_period,
                "bb_period": params.bb_period,
                "bb_std": params.bb_std,
                "adx_period": params.adx_period,
                "min_confidence": params.min_confidence,
            },
            families=["Trend", "Momentum", "Volatility", "Volume"],
            description=f"ATR-optimized parameters for {regime.value}",
        )
