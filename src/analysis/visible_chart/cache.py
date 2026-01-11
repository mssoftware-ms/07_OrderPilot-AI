"""Caching Layer for Visible Chart Analyzer.

Provides intelligent caching for:
- Feature calculations (expensive)
- Regime detection (stable within short periods)
- Optimization results (reusable if range overlaps)

Phase 2.6: Caching & Wiederverwendung
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from .types import RegimeType, VisibleRange

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cached value with metadata.

    Attributes:
        value: The cached data.
        created_at: Unix timestamp when created.
        ttl_seconds: Time-to-live in seconds (0 = no expiry).
        hits: Number of cache hits.
        range_hash: Hash of the visible range for overlap detection.
    """

    value: Any
    created_at: float = field(default_factory=time.time)
    ttl_seconds: float = 0.0
    hits: int = 0
    range_hash: str = ""

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl_seconds <= 0:
            return False
        return time.time() - self.created_at > self.ttl_seconds

    def increment_hits(self) -> None:
        """Increment hit counter."""
        self.hits += 1


@dataclass
class CacheStats:
    """Cache performance statistics.

    Attributes:
        hits: Total cache hits.
        misses: Total cache misses.
        evictions: Number of expired entries removed.
        feature_hits: Feature-specific hits.
        regime_hits: Regime-specific hits.
        optimizer_hits: Optimizer-specific hits.
    """

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    feature_hits: int = 0
    regime_hits: int = 0
    optimizer_hits: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate overall hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class AnalyzerCache:
    """Thread-safe cache for analyzer computations.

    Caches expensive calculations to avoid redundant work when:
    - User scrolls slightly (range overlap)
    - Re-analysis on same data
    - Multiple optimizer iterations on same features

    Cache Keys:
    - features: {symbol}_{timeframe}_{range_hash}
    - regime: {symbol}_{timeframe}_{range_hash}
    - optimizer: {symbol}_{timeframe}_{range_hash}_{regime}
    """

    # Default TTLs in seconds
    DEFAULT_FEATURE_TTL = 300.0  # 5 minutes
    DEFAULT_REGIME_TTL = 120.0  # 2 minutes
    DEFAULT_OPTIMIZER_TTL = 60.0  # 1 minute (results can vary)

    # Maximum cache size
    MAX_ENTRIES = 100

    def __init__(
        self,
        feature_ttl: float = DEFAULT_FEATURE_TTL,
        regime_ttl: float = DEFAULT_REGIME_TTL,
        optimizer_ttl: float = DEFAULT_OPTIMIZER_TTL,
    ) -> None:
        """Initialize the cache.

        Args:
            feature_ttl: TTL for feature cache entries.
            regime_ttl: TTL for regime cache entries.
            optimizer_ttl: TTL for optimizer cache entries.
        """
        self._feature_cache: dict[str, CacheEntry] = {}
        self._regime_cache: dict[str, CacheEntry] = {}
        self._optimizer_cache: dict[str, CacheEntry] = {}

        self._feature_ttl = feature_ttl
        self._regime_ttl = regime_ttl
        self._optimizer_ttl = optimizer_ttl

        self._lock = Lock()
        self._stats = CacheStats()

    @staticmethod
    def _compute_range_hash(
        visible_range: VisibleRange, tolerance_pct: float = 0.1
    ) -> str:
        """Compute a hash for the visible range.

        Uses bucketing with tolerance to allow cache hits on
        small scrolls (within tolerance_pct of range duration).

        Args:
            visible_range: The visible time range.
            tolerance_pct: Tolerance as percentage of duration.

        Returns:
            Hash string for the range.
        """
        duration = visible_range.duration_seconds
        bucket_size = max(60, int(duration * tolerance_pct))  # Min 1 minute

        # Bucket the from/to timestamps
        from_bucket = visible_range.from_ts // bucket_size
        to_bucket = visible_range.to_ts // bucket_size

        hash_input = f"{from_bucket}_{to_bucket}_{bucket_size}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _make_feature_key(
        self, symbol: str, timeframe: str, visible_range: VisibleRange
    ) -> str:
        """Create cache key for features."""
        range_hash = self._compute_range_hash(visible_range)
        return f"feat_{symbol}_{timeframe}_{range_hash}"

    def _make_regime_key(
        self, symbol: str, timeframe: str, visible_range: VisibleRange
    ) -> str:
        """Create cache key for regime."""
        range_hash = self._compute_range_hash(visible_range)
        return f"regime_{symbol}_{timeframe}_{range_hash}"

    def _make_optimizer_key(
        self,
        symbol: str,
        timeframe: str,
        visible_range: VisibleRange,
        regime: RegimeType,
    ) -> str:
        """Create cache key for optimizer results."""
        range_hash = self._compute_range_hash(visible_range)
        return f"opt_{symbol}_{timeframe}_{range_hash}_{regime.value}"

    def _evict_expired(self, cache: dict[str, CacheEntry]) -> int:
        """Remove expired entries from a cache.

        Args:
            cache: The cache dictionary to clean.

        Returns:
            Number of entries evicted.
        """
        expired_keys = [k for k, v in cache.items() if v.is_expired()]
        for key in expired_keys:
            del cache[key]
        return len(expired_keys)

    def _enforce_size_limit(self, cache: dict[str, CacheEntry]) -> None:
        """Enforce maximum cache size using LRU eviction.

        Args:
            cache: The cache dictionary to limit.
        """
        if len(cache) <= self.MAX_ENTRIES:
            return

        # Sort by (hits, created_at) ascending - evict least valuable
        sorted_entries = sorted(
            cache.items(), key=lambda x: (x[1].hits, x[1].created_at)
        )

        # Remove oldest/least-hit entries
        to_remove = len(cache) - self.MAX_ENTRIES
        for key, _ in sorted_entries[:to_remove]:
            del cache[key]
            self._stats.evictions += 1

    # ─────────────────────────────────────────────────────────────────
    # Feature Cache
    # ─────────────────────────────────────────────────────────────────

    def get_features(
        self, symbol: str, timeframe: str, visible_range: VisibleRange
    ) -> dict[str, list[float]] | None:
        """Get cached features if available.

        Args:
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            visible_range: Visible time range.

        Returns:
            Cached features dict or None if not cached.
        """
        key = self._make_feature_key(symbol, timeframe, visible_range)

        with self._lock:
            self._evict_expired(self._feature_cache)

            entry = self._feature_cache.get(key)
            if entry and not entry.is_expired():
                entry.increment_hits()
                self._stats.hits += 1
                self._stats.feature_hits += 1
                logger.debug("Feature cache HIT: %s", key)
                return entry.value

            self._stats.misses += 1
            logger.debug("Feature cache MISS: %s", key)
            return None

    def set_features(
        self,
        symbol: str,
        timeframe: str,
        visible_range: VisibleRange,
        features: dict[str, list[float]],
    ) -> None:
        """Cache calculated features.

        Args:
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            visible_range: Visible time range.
            features: The features to cache.
        """
        key = self._make_feature_key(symbol, timeframe, visible_range)
        range_hash = self._compute_range_hash(visible_range)

        with self._lock:
            self._feature_cache[key] = CacheEntry(
                value=features,
                ttl_seconds=self._feature_ttl,
                range_hash=range_hash,
            )
            self._enforce_size_limit(self._feature_cache)
            logger.debug("Feature cache SET: %s", key)

    # ─────────────────────────────────────────────────────────────────
    # Regime Cache
    # ─────────────────────────────────────────────────────────────────

    def get_regime(
        self, symbol: str, timeframe: str, visible_range: VisibleRange
    ) -> RegimeType | None:
        """Get cached regime if available.

        Args:
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            visible_range: Visible time range.

        Returns:
            Cached regime or None if not cached.
        """
        key = self._make_regime_key(symbol, timeframe, visible_range)

        with self._lock:
            self._evict_expired(self._regime_cache)

            entry = self._regime_cache.get(key)
            if entry and not entry.is_expired():
                entry.increment_hits()
                self._stats.hits += 1
                self._stats.regime_hits += 1
                logger.debug("Regime cache HIT: %s", key)
                return entry.value

            self._stats.misses += 1
            logger.debug("Regime cache MISS: %s", key)
            return None

    def set_regime(
        self,
        symbol: str,
        timeframe: str,
        visible_range: VisibleRange,
        regime: RegimeType,
    ) -> None:
        """Cache detected regime.

        Args:
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            visible_range: Visible time range.
            regime: The regime to cache.
        """
        key = self._make_regime_key(symbol, timeframe, visible_range)
        range_hash = self._compute_range_hash(visible_range)

        with self._lock:
            self._regime_cache[key] = CacheEntry(
                value=regime,
                ttl_seconds=self._regime_ttl,
                range_hash=range_hash,
            )
            self._enforce_size_limit(self._regime_cache)
            logger.debug("Regime cache SET: %s", key)

    # ─────────────────────────────────────────────────────────────────
    # Optimizer Cache
    # ─────────────────────────────────────────────────────────────────

    def get_optimizer_result(
        self,
        symbol: str,
        timeframe: str,
        visible_range: VisibleRange,
        regime: RegimeType,
    ) -> dict[str, Any] | None:
        """Get cached optimizer result if available.

        Args:
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            visible_range: Visible time range.
            regime: Current market regime.

        Returns:
            Cached optimizer result or None if not cached.
        """
        key = self._make_optimizer_key(symbol, timeframe, visible_range, regime)

        with self._lock:
            self._evict_expired(self._optimizer_cache)

            entry = self._optimizer_cache.get(key)
            if entry and not entry.is_expired():
                entry.increment_hits()
                self._stats.hits += 1
                self._stats.optimizer_hits += 1
                logger.debug("Optimizer cache HIT: %s", key)
                return entry.value

            self._stats.misses += 1
            logger.debug("Optimizer cache MISS: %s", key)
            return None

    def set_optimizer_result(
        self,
        symbol: str,
        timeframe: str,
        visible_range: VisibleRange,
        regime: RegimeType,
        result: dict[str, Any],
    ) -> None:
        """Cache optimizer result.

        Args:
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            visible_range: Visible time range.
            regime: Current market regime.
            result: The optimizer result to cache.
        """
        key = self._make_optimizer_key(symbol, timeframe, visible_range, regime)
        range_hash = self._compute_range_hash(visible_range)

        with self._lock:
            self._optimizer_cache[key] = CacheEntry(
                value=result,
                ttl_seconds=self._optimizer_ttl,
                range_hash=range_hash,
            )
            self._enforce_size_limit(self._optimizer_cache)
            logger.debug("Optimizer cache SET: %s", key)

    # ─────────────────────────────────────────────────────────────────
    # Cache Management
    # ─────────────────────────────────────────────────────────────────

    def invalidate_all(self) -> None:
        """Clear all caches."""
        with self._lock:
            self._feature_cache.clear()
            self._regime_cache.clear()
            self._optimizer_cache.clear()
            logger.info("All caches invalidated")

    def invalidate_symbol(self, symbol: str) -> int:
        """Invalidate all caches for a symbol.

        Args:
            symbol: Symbol to invalidate.

        Returns:
            Number of entries invalidated.
        """
        count = 0
        with self._lock:
            for cache in [
                self._feature_cache,
                self._regime_cache,
                self._optimizer_cache,
            ]:
                keys_to_remove = [k for k in cache if f"_{symbol}_" in k]
                for key in keys_to_remove:
                    del cache[key]
                    count += 1
        logger.info("Invalidated %d entries for symbol %s", count, symbol)
        return count

    def get_stats(self) -> CacheStats:
        """Get cache statistics.

        Returns:
            Current cache stats.
        """
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                evictions=self._stats.evictions,
                feature_hits=self._stats.feature_hits,
                regime_hits=self._stats.regime_hits,
                optimizer_hits=self._stats.optimizer_hits,
            )

    def get_size(self) -> dict[str, int]:
        """Get current cache sizes.

        Returns:
            Dict with cache names and entry counts.
        """
        with self._lock:
            return {
                "features": len(self._feature_cache),
                "regime": len(self._regime_cache),
                "optimizer": len(self._optimizer_cache),
            }


# Module-level singleton for shared caching
_global_cache: AnalyzerCache | None = None


def get_analyzer_cache() -> AnalyzerCache:
    """Get or create the global analyzer cache.

    Returns:
        The shared AnalyzerCache instance.
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = AnalyzerCache()
    return _global_cache


def reset_analyzer_cache() -> None:
    """Reset the global cache (for testing)."""
    global _global_cache
    if _global_cache:
        _global_cache.invalidate_all()
    _global_cache = None
