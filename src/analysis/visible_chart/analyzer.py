"""Visible Chart Analyzer.

Orchestrates the analysis of the visible chart range,
generating entry signals using features, regime detection,
and signal scoring.

Phase 1: MVP with rules-based detection.
Phase 2: FastOptimizer integration for parameter optimization.
Phase 2.6: Caching & Wiederverwendung.
Issue #27: Comprehensive debug logging.
"""

from __future__ import annotations

import logging
import time
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
    ) -> None:
        """Initialize the analyzer.

        Args:
            use_optimizer: If True, use FastOptimizer for parameter tuning.
            use_cache: If True, use caching for features/regime/optimizer.
            cache: Optional custom cache instance. Uses global if None.
        """
        self._candle_loader = CandleLoader()
        self._use_optimizer = use_optimizer
        self._use_cache = use_cache
        self._cache = cache if cache else get_analyzer_cache()
        self._optimizer = None
        self._last_symbol: str | None = None
        self._last_regime: RegimeType | None = None

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

        MVP: Simple features (SMA, RSI approximation).
        Later: Full feature families.

        Args:
            candles: List of candle dicts.

        Returns:
            Dict of feature name -> values.
        """
        if len(candles) < 20:
            return {}

        closes = [c["close"] for c in candles]

        # Simple SMA
        sma_20 = []
        for i in range(len(closes)):
            if i < 19:
                sma_20.append(closes[i])
            else:
                sma_20.append(sum(closes[i - 19 : i + 1]) / 20)

        # Price vs SMA (trend indicator)
        price_vs_sma = [
            (closes[i] - sma_20[i]) / sma_20[i] if sma_20[i] != 0 else 0
            for i in range(len(closes))
        ]

        # Simple volatility (ATR approximation)
        volatility = []
        for i, c in enumerate(candles):
            tr = c["high"] - c["low"]
            volatility.append(tr / c["close"] if c["close"] != 0 else 0)

        return {
            "sma_20": sma_20,
            "price_vs_sma": price_vs_sma,
            "volatility": volatility,
            "closes": closes,
        }

    def _detect_regime(self, features: dict[str, list[float]]) -> RegimeType:
        """Detect market regime from features.

        MVP: Simple rules-based detection.
        Later: HMM or ML-based.

        Args:
            features: Calculated features.

        Returns:
            Detected regime type.
        """
        if not features or "price_vs_sma" not in features:
            return RegimeType.NO_TRADE

        price_vs_sma = features["price_vs_sma"]
        volatility = features.get("volatility", [])

        if not price_vs_sma:
            return RegimeType.NO_TRADE

        # Average trend strength (last 20 values)
        recent_trend = price_vs_sma[-20:] if len(price_vs_sma) >= 20 else price_vs_sma
        avg_trend = sum(recent_trend) / len(recent_trend)

        # Average volatility
        recent_vol = volatility[-20:] if len(volatility) >= 20 else volatility
        avg_vol = sum(recent_vol) / len(recent_vol) if recent_vol else 0

        # Regime classification
        if avg_vol > 0.015:  # High volatility
            return RegimeType.HIGH_VOL
        elif avg_trend > 0.005:  # Uptrend
            return RegimeType.TREND_UP
        elif avg_trend < -0.005:  # Downtrend
            return RegimeType.TREND_DOWN
        elif avg_vol < 0.005:  # Low volatility = squeeze
            return RegimeType.SQUEEZE
        else:
            return RegimeType.RANGE

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

        MVP: Simple rules-based scoring.
        Later: Optimized scoring based on indicator set.

        Args:
            candles: List of candles.
            features: Calculated features.
            regime: Current regime.

        Returns:
            List of detected entry events.
        """
        if regime == RegimeType.NO_TRADE:
            return []

        entries = []
        price_vs_sma = features.get("price_vs_sma", [])

        for i, candle in enumerate(candles):
            if i < 20:  # Skip warmup period
                continue

            score = 0.0
            side = None
            reasons = []

            trend = price_vs_sma[i] if i < len(price_vs_sma) else 0

            # Simple entry logic based on regime
            if regime in (RegimeType.TREND_UP,):
                # Long on pullback in uptrend
                if trend > 0 and trend < 0.01:  # Mild pullback in uptrend
                    score = 0.6 + abs(trend) * 10
                    side = EntrySide.LONG
                    reasons.append("trend_pullback")

            elif regime == RegimeType.TREND_DOWN:
                # Short on pullback in downtrend
                if trend < 0 and trend > -0.01:  # Mild pullback in downtrend
                    score = 0.6 + abs(trend) * 10
                    side = EntrySide.SHORT
                    reasons.append("trend_pullback")

            elif regime == RegimeType.RANGE:
                # Mean reversion at extremes
                if trend < -0.008:  # Oversold
                    score = 0.5 + abs(trend) * 30
                    side = EntrySide.LONG
                    reasons.append("oversold")
                elif trend > 0.008:  # Overbought
                    score = 0.5 + abs(trend) * 30
                    side = EntrySide.SHORT
                    reasons.append("overbought")

            elif regime == RegimeType.SQUEEZE:
                # SQUEEZE: Look for range extremes and small directional moves
                # Don't wait for volatility expansion (which doesn't exist in a squeeze period)
                closes = features.get("closes", [])

                if len(closes) > i and i >= 20:
                    # Calculate local range
                    recent_prices = closes[max(0, i-20):i+1]
                    if len(recent_prices) >= 10:
                        local_high = max(recent_prices)
                        local_low = min(recent_prices)
                        current_price = closes[i]

                        if local_high > local_low:
                            # Position in range (0 = low, 1 = high)
                            position = (current_price - local_low) / (local_high - local_low)

                            # Near bottom of range - potential long
                            if position < 0.3 and trend > -0.005:
                                score = 0.50 + (0.3 - position) * 0.6  # 0.50-0.68
                                side = EntrySide.LONG
                                reasons.append("squeeze_range_low")
                            # Near top of range - potential short
                            elif position > 0.7 and trend < 0.005:
                                score = 0.50 + (position - 0.7) * 0.6  # 0.50-0.68
                                side = EntrySide.SHORT
                                reasons.append("squeeze_range_high")
                            # Small trend in middle
                            elif 0.4 < position < 0.6:
                                if trend > 0.002:
                                    score = 0.50 + abs(trend) * 20  # Start at 0.50
                                    side = EntrySide.LONG
                                    reasons.append("squeeze_trend_long")
                                elif trend < -0.002:
                                    score = 0.50 + abs(trend) * 20  # Start at 0.50
                                    side = EntrySide.SHORT
                                    reasons.append("squeeze_trend_short")

            # Add entry if score threshold met
            if side and score >= 0.5:
                entries.append(
                    EntryEvent(
                        timestamp=candle["timestamp"],
                        side=side,
                        confidence=min(score, 1.0),
                        price=candle["close"],
                        reason_tags=reasons,
                        regime=regime,
                    )
                )

        return entries

    def _postprocess_entries(self, entries: list[EntryEvent]) -> list[EntryEvent]:
        """Apply postprocessing rules to entries.

        - Cooldown: Minimum time between signals
        - Clustering: Merge nearby signals
        - Rate limiting: Max signals per hour

        Args:
            entries: Raw entry events.

        Returns:
            Filtered entry events.
        """
        if not entries:
            return entries

        # Sort by timestamp
        entries = sorted(entries, key=lambda e: e.timestamp)

        # Apply cooldown (minimum 5 minutes between signals)
        cooldown_seconds = 5 * 60
        filtered = []
        last_ts = 0

        for entry in entries:
            if entry.timestamp - last_ts >= cooldown_seconds:
                filtered.append(entry)
                last_ts = entry.timestamp

        # Rate limiting: max 6 signals per hour
        max_per_hour = 6
        if len(filtered) > max_per_hour:
            # Keep highest confidence signals
            filtered = sorted(filtered, key=lambda e: -e.confidence)[:max_per_hour]
            filtered = sorted(filtered, key=lambda e: e.timestamp)

        logger.debug(
            "Postprocess: %d -> %d entries (cooldown + rate limit)",
            len(entries),
            len(filtered),
        )

        return filtered

    def _run_optimizer(
        self,
        candles: list[dict],
        regime: RegimeType,
        features: dict[str, list[float]],
    ) -> dict[str, Any]:
        """Run FastOptimizer to find optimal indicator set.

        Args:
            candles: Candle data.
            regime: Detected regime.
            features: Pre-calculated features.

        Returns:
            Dict with active_set, alternatives, and entries.
        """
        from .optimizer import FastOptimizer, OptimizerConfig

        # Lazy init optimizer
        if self._optimizer is None:
            config = OptimizerConfig(
                time_budget_ms=2000,  # 2 seconds
                max_iterations=50,
                early_stop_no_improve=15,
                top_k=3,
            )
            self._optimizer = FastOptimizer(config)

        # Run optimization
        opt_result = self._optimizer.optimize(candles, regime, features)

        return {
            "active_set": opt_result.best_set,
            "alternatives": opt_result.alternatives,
            "entries": opt_result.entries,
        }
