"""Visible Chart Analyzer.

Orchestrates the analysis of the visible chart range,
generating entry signals using features, regime detection,
and signal scoring.

Phase 1: MVP with rules-based detection.
Phase 2: FastOptimizer integration for parameter optimization.
Phase 2.6: Caching & Wiederverwendung.
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
        """Analyze the visible chart range.

        Args:
            visible_range: The visible time range.
            symbol: Trading symbol.
            timeframe: Chart timeframe (default 1m).

        Returns:
            AnalysisResult with entries and indicator set info.
        """
        start_time = time.perf_counter()

        # Check for re-optimize trigger (symbol or regime change)
        symbol_changed = self._last_symbol is not None and self._last_symbol != symbol
        if symbol_changed:
            logger.info("Symbol changed: %s -> %s, invalidating cache", self._last_symbol, symbol)
            if self._use_cache:
                self._cache.invalidate_symbol(self._last_symbol)
        self._last_symbol = symbol

        logger.info(
            "Starting analysis for %s [%d - %d] (%d min)",
            symbol,
            visible_range.from_ts,
            visible_range.to_ts,
            visible_range.duration_minutes,
        )

        # Step 1: Load candle data
        candles = self._candle_loader.load(
            symbol=symbol,
            from_ts=visible_range.from_ts,
            to_ts=visible_range.to_ts,
            timeframe=timeframe,
        )

        if not candles:
            logger.warning("No candles found for visible range")
            return AnalysisResult(
                visible_range=visible_range,
                analysis_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Step 2: Calculate features (with cache)
        features = self._get_or_calculate_features(
            candles, symbol, timeframe, visible_range
        )

        # Step 3: Detect regime (with cache)
        regime = self._get_or_detect_regime(
            features, symbol, timeframe, visible_range
        )

        # Check for regime change trigger
        regime_changed = self._last_regime is not None and self._last_regime != regime
        if regime_changed:
            logger.info("Regime changed: %s -> %s", self._last_regime.value, regime.value)
        self._last_regime = regime

        # Step 4 & 5: Generate entries (with or without optimization)
        if self._use_optimizer:
            # Check optimizer cache first
            result = self._get_or_run_optimizer(
                candles, regime, features, symbol, timeframe, visible_range
            )
            active_set = result.get("active_set")
            alternatives = result.get("alternatives", [])
            entries = result.get("entries", [])
        else:
            # Phase 1: Default rules-based
            active_set = self._create_default_set(regime)
            entries = self._score_entries(candles, features, regime)
            entries = self._postprocess_entries(entries)
            alternatives = []

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

        logger.info(
            "Analysis complete: %d entries, regime=%s, optimized=%s, took %.1fms",
            len(entries),
            regime.value,
            self._use_optimizer,
            analysis_time,
        )

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
                # Breakout signals (placeholder)
                pass

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
