"""
MarketContext Cache - Caching-Layer für MarketContext.

Verhindert doppelte Berechnung durch:
- TTL-basiertes Caching
- Hash-basierte Invalidierung
- Per Symbol/Timeframe Caching

Phase 1.4 der Bot-Integration.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

import pandas as pd

from .market_context import MarketContext, create_empty_context
from .market_context_builder import MarketContextBuilder, MarketContextBuilderConfig

logger = logging.getLogger(__name__)


# CACHE ENTRY
@dataclass
class CacheEntry:
    """Einzelner Cache-Eintrag."""

    context: MarketContext
    created_at: datetime
    expires_at: datetime
    data_hash: str
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self) -> bool:
        """Prüft ob Eintrag abgelaufen ist."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def age_seconds(self) -> int:
        """Alter des Eintrags in Sekunden."""
        return int((datetime.now(timezone.utc) - self.created_at).total_seconds())

    def touch(self) -> None:
        """Aktualisiert Zugriffszeitpunkt."""
        self.last_accessed = datetime.now(timezone.utc)
        self.hit_count += 1


# CACHE STATS
@dataclass
class CacheStats:
    """Statistiken über Cache-Nutzung."""

    hits: int = 0
    misses: int = 0
    invalidations: int = 0
    expirations: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Hit-Rate als Prozent."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "invalidations": self.invalidations,
            "expirations": self.expirations,
            "evictions": self.evictions,
            "hit_rate_pct": round(self.hit_rate, 2),
            "total_requests": self.hits + self.misses,
        }


# CACHE CONFIG
@dataclass
class CacheConfig:
    """Konfiguration für den Cache."""

    # TTL pro Timeframe (in Sekunden)
    ttl_by_timeframe: dict[str, int] = field(default_factory=lambda: {
        "1m": 30,
        "5m": 60,
        "15m": 120,
        "1h": 300,
        "4h": 600,
        "1d": 1800,
    })

    # Default TTL wenn Timeframe nicht bekannt
    default_ttl: int = 60

    # Max Einträge im Cache
    max_entries: int = 100

    # Hash-basierte Invalidierung aktivieren
    hash_invalidation: bool = True

    # Automatische Bereinigung
    auto_cleanup: bool = True
    cleanup_interval: int = 300  # 5 Minuten


# MARKET CONTEXT CACHE
class MarketContextCache:
    """
    Thread-sicherer Cache für MarketContext.

    Features:
    - TTL-basiertes Caching (pro Timeframe konfigurierbar)
    - Hash-basierte Invalidierung (wenn Daten sich ändern)
    - LRU-Eviction wenn max_entries erreicht
    - Thread-sicher

    Usage:
        cache = MarketContextCache()

        # Get or Build
        context = cache.get_or_build(df, "BTCUSD", "5m")

        # Mit Custom Builder
        context = cache.get_or_build(
            df, "BTCUSD", "5m",
            builder=my_custom_builder
        )

        # Manuell invalidieren
        cache.invalidate("BTCUSD", "5m")

        # Stats
        print(cache.stats.to_dict())
    """

    def __init__(
        self,
        config: CacheConfig | None = None,
        builder_config: MarketContextBuilderConfig | None = None,
    ):
        self.config = config or CacheConfig()
        self._builder = MarketContextBuilder(builder_config)
        self._cache: dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self._stats = CacheStats()

        # Cleanup Timer
        self._cleanup_timer: threading.Timer | None = None
        if self.config.auto_cleanup:
            self._schedule_cleanup()

    def get_or_build(
        self,
        df: pd.DataFrame | None,
        symbol: str,
        timeframe: str = "5m",
        force_rebuild: bool = False,
        builder: MarketContextBuilder | None = None,
    ) -> MarketContext:
        """
        Holt Context aus Cache oder baut neu.

        Args:
            df: DataFrame mit OHLCV-Daten
            symbol: Trading-Symbol
            timeframe: Timeframe
            force_rebuild: Cache ignorieren und neu bauen
            builder: Optionaler Custom Builder

        Returns:
            MarketContext (aus Cache oder neu gebaut)
        """
        cache_key = self._make_key(symbol, timeframe)

        # Check if we should use cache
        if not force_rebuild:
            with self._lock:
                entry = self._cache.get(cache_key)

                if entry and not entry.is_expired:
                    # Check hash if enabled
                    if self.config.hash_invalidation and df is not None:
                        current_hash = self._compute_data_hash(df)
                        if current_hash != entry.data_hash:
                            # Data changed, invalidate
                            logger.debug(f"Cache invalidated (hash mismatch) for {cache_key}")
                            self._stats.invalidations += 1
                        else:
                            # Cache hit
                            entry.touch()
                            self._stats.hits += 1
                            logger.debug(f"Cache hit for {cache_key} (age: {entry.age_seconds}s)")
                            return entry.context
                    else:
                        # No hash check, use cached
                        entry.touch()
                        self._stats.hits += 1
                        return entry.context

                elif entry and entry.is_expired:
                    self._stats.expirations += 1
                    logger.debug(f"Cache expired for {cache_key}")

        # Cache miss - build new context
        self._stats.misses += 1

        actual_builder = builder or self._builder
        context = actual_builder.build(df, symbol, timeframe)

        # Store in cache
        self._store(cache_key, context, df, timeframe)

        return context

    def get(self, symbol: str, timeframe: str = "5m") -> MarketContext | None:
        """
        Holt Context aus Cache ohne zu bauen.

        Returns:
            MarketContext oder None wenn nicht im Cache
        """
        cache_key = self._make_key(symbol, timeframe)

        with self._lock:
            entry = self._cache.get(cache_key)

            if entry and not entry.is_expired:
                entry.touch()
                self._stats.hits += 1
                return entry.context

            self._stats.misses += 1
            return None

    def store(
        self,
        context: MarketContext,
        df: pd.DataFrame | None = None,
    ) -> None:
        """
        Speichert Context manuell im Cache.

        Args:
            context: MarketContext zum Speichern
            df: Optional DataFrame für Hash-Berechnung
        """
        cache_key = self._make_key(context.symbol, context.timeframe)
        self._store(cache_key, context, df, context.timeframe)

    def invalidate(self, symbol: str, timeframe: str | None = None) -> int:
        """
        Invalidiert Cache-Einträge.

        Args:
            symbol: Symbol zu invalidieren
            timeframe: Optional spezifischer Timeframe (sonst alle)

        Returns:
            Anzahl invalidierter Einträge
        """
        invalidated = 0

        with self._lock:
            if timeframe:
                # Spezifischer Timeframe
                cache_key = self._make_key(symbol, timeframe)
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    invalidated = 1
            else:
                # Alle Timeframes für Symbol
                keys_to_delete = [
                    k for k in self._cache.keys() if k.startswith(f"{symbol}:")
                ]
                for key in keys_to_delete:
                    del self._cache[key]
                    invalidated += 1

        if invalidated > 0:
            self._stats.invalidations += invalidated
            logger.debug(f"Invalidated {invalidated} cache entries for {symbol}")

        return invalidated

    def clear(self) -> int:
        """
        Leert den gesamten Cache.

        Returns:
            Anzahl gelöschter Einträge
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats.evictions += count
            logger.info(f"Cache cleared: {count} entries removed")
            return count

    @property
    def stats(self) -> CacheStats:
        """Gibt Cache-Statistiken zurück."""
        return self._stats

    @property
    def size(self) -> int:
        """Aktuelle Anzahl Einträge im Cache."""
        with self._lock:
            return len(self._cache)

    def get_entries_info(self) -> list[dict]:
        """
        Gibt Info über alle Cache-Einträge zurück.

        Returns:
            Liste von Entry-Infos
        """
        with self._lock:
            return [
                {
                    "key": key,
                    "symbol": entry.context.symbol,
                    "timeframe": entry.context.timeframe,
                    "age_seconds": entry.age_seconds,
                    "hit_count": entry.hit_count,
                    "is_expired": entry.is_expired,
                    "data_hash": entry.data_hash[:8] + "...",
                }
                for key, entry in self._cache.items()
            ]

    # =========================================================================
    # INTERNAL METHODS
    # =========================================================================

    def _store(
        self,
        cache_key: str,
        context: MarketContext,
        df: pd.DataFrame | None,
        timeframe: str,
    ) -> None:
        """Speichert Entry im Cache."""
        with self._lock:
            # Evict if necessary
            if len(self._cache) >= self.config.max_entries:
                self._evict_lru()

            # Calculate TTL
            ttl = self.config.ttl_by_timeframe.get(
                timeframe.lower(), self.config.default_ttl
            )

            now = datetime.now(timezone.utc)

            entry = CacheEntry(
                context=context,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl),
                data_hash=self._compute_data_hash(df) if df is not None else "",
            )

            self._cache[cache_key] = entry
            logger.debug(f"Cached {cache_key} (TTL: {ttl}s)")

    def _evict_lru(self) -> None:
        """Entfernt ältesten ungenutzten Eintrag (LRU)."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed,
        )

        del self._cache[lru_key]
        self._stats.evictions += 1
        logger.debug(f"Evicted LRU entry: {lru_key}")

    def _cleanup_expired(self) -> int:
        """Entfernt abgelaufene Einträge."""
        removed = 0

        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items() if v.is_expired
            ]

            for key in expired_keys:
                del self._cache[key]
                removed += 1

        if removed > 0:
            self._stats.expirations += removed
            logger.debug(f"Cleaned up {removed} expired cache entries")

        return removed

    def _schedule_cleanup(self) -> None:
        """Plant nächsten Cleanup."""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()

        self._cleanup_timer = threading.Timer(
            self.config.cleanup_interval,
            self._run_cleanup,
        )
        self._cleanup_timer.daemon = True
        self._cleanup_timer.start()

    def _run_cleanup(self) -> None:
        """Führt Cleanup durch und plant nächsten."""
        self._cleanup_expired()

        if self.config.auto_cleanup:
            self._schedule_cleanup()

    @staticmethod
    def _make_key(symbol: str, timeframe: str) -> str:
        """Erzeugt Cache-Key."""
        return f"{symbol.upper()}:{timeframe.lower()}"

    @staticmethod
    def _compute_data_hash(df: pd.DataFrame | None) -> str:
        """
        Berechnet Hash für DataFrame.

        Verwendet nur die letzten 5 Rows für Performance.
        """
        if df is None or df.empty:
            return ""

        # Use last 5 rows for hash (performance)
        tail = df.tail(5)

        # Create hash from OHLCV values
        hash_data = {
            "last_ts": str(tail.index[-1]),
            "last_close": float(tail["close"].iloc[-1]),
            "last_volume": float(tail.get("volume", pd.Series([0])).iloc[-1]),
            "row_count": len(df),
        }

        hash_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.md5(hash_str.encode()).hexdigest()

    def __del__(self):
        """Cleanup bei Zerstörung."""
        if self._cleanup_timer:
            self._cleanup_timer.cancel()


# SINGLETON INSTANCE
_global_cache: MarketContextCache | None = None
_global_cache_lock = threading.Lock()


def get_global_cache(
    config: CacheConfig | None = None,
    builder_config: MarketContextBuilderConfig | None = None,
) -> MarketContextCache:
    """
    Gibt globale Cache-Instanz zurück (Singleton).

    Usage:
        cache = get_global_cache()
        context = cache.get_or_build(df, "BTCUSD", "5m")
    """
    global _global_cache

    with _global_cache_lock:
        if _global_cache is None:
            _global_cache = MarketContextCache(config, builder_config)

        return _global_cache


def reset_global_cache() -> None:
    """Setzt globalen Cache zurück."""
    global _global_cache

    with _global_cache_lock:
        if _global_cache:
            _global_cache.clear()
        _global_cache = None


# CONVENIENCE FUNCTIONS
def get_cached_context(
    df: pd.DataFrame | None,
    symbol: str,
    timeframe: str = "5m",
    force_rebuild: bool = False,
) -> MarketContext:
    """
    Convenience-Funktion für Cache-Zugriff.

    Verwendet globalen Cache.

    Usage:
        context = get_cached_context(df, "BTCUSD", "5m")
    """
    cache = get_global_cache()
    return cache.get_or_build(df, symbol, timeframe, force_rebuild)
