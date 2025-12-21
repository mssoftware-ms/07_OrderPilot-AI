"""
Cache-Manager für KO-Finder mit Stale-While-Revalidate.

Implementiert:
- In-Memory Cache mit TTL
- Stale-While-Revalidate Pattern
- Key basierend auf (underlying, direction, filter-hash)
"""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from ..constants import CACHE_MAX_SIZE, CACHE_TTL_KO_LIST

if TYPE_CHECKING:
    from ..config import KOFilterConfig
    from ..models import SearchResponse

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Einzelner Cache-Eintrag."""

    key: str
    value: T
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = CACHE_TTL_KO_LIST
    hit_count: int = 0

    @property
    def age_seconds(self) -> float:
        """Alter in Sekunden."""
        return time.time() - self.created_at

    @property
    def is_expired(self) -> bool:
        """Prüft ob Eintrag abgelaufen ist."""
        return self.age_seconds > self.ttl_seconds

    @property
    def is_stale(self) -> bool:
        """Prüft ob Eintrag "stale" ist (alt aber noch nutzbar)."""
        # Stale = zwischen TTL und 2x TTL
        return self.ttl_seconds < self.age_seconds <= (self.ttl_seconds * 2)


class CacheManager:
    """
    In-Memory Cache mit Stale-While-Revalidate.

    Thread-safe durch Lock.
    """

    def __init__(
        self,
        ttl_seconds: int = CACHE_TTL_KO_LIST,
        max_size: int = CACHE_MAX_SIZE,
    ) -> None:
        """
        Initialisiere Cache.

        Args:
            ttl_seconds: Time-to-Live für Einträge
            max_size: Maximale Anzahl Einträge
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: dict[str, CacheEntry] = {}
        self._lock = Lock()

    def get(self, key: str) -> CacheEntry | None:
        """
        Hole Eintrag aus Cache.

        Args:
            key: Cache-Key

        Returns:
            CacheEntry oder None
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return None

            # Komplett abgelaufen (> 2x TTL)?
            if entry.age_seconds > (entry.ttl_seconds * 2):
                del self._cache[key]
                return None

            entry.hit_count += 1
            return entry

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> CacheEntry:
        """
        Setze Cache-Eintrag.

        Args:
            key: Cache-Key
            value: Zu cachender Wert
            ttl_seconds: Optional: Custom TTL

        Returns:
            Erstellter CacheEntry
        """
        with self._lock:
            # Eviction wenn voll
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            entry = CacheEntry(
                key=key,
                value=value,
                ttl_seconds=ttl_seconds or self.ttl_seconds,
            )

            self._cache[key] = entry
            return entry

    def invalidate(self, key: str) -> bool:
        """
        Invalidiere Cache-Eintrag.

        Args:
            key: Cache-Key

        Returns:
            True wenn Eintrag existierte
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """
        Lösche alle Einträge.

        Returns:
            Anzahl gelöschter Einträge
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def _evict_oldest(self) -> None:
        """Entferne ältesten Eintrag."""
        if not self._cache:
            return

        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at,
        )
        del self._cache[oldest_key]

    @staticmethod
    def build_key(
        underlying: str,
        direction: str,
        config: KOFilterConfig,
    ) -> str:
        """
        Erstelle Cache-Key aus Parametern.

        Args:
            underlying: Underlying-Symbol
            direction: LONG oder SHORT
            config: Filter-Konfiguration

        Returns:
            Eindeutiger Cache-Key
        """
        # Config-Hash für Filter-Parameter
        config_str = (
            f"{config.min_leverage}:{config.max_spread_pct}:"
            f"{config.min_ko_distance_pct}:{config.issuer_ids_str}"
        )
        config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]

        return f"ko:{underlying}:{direction}:{config_hash}"


class SWRCache:
    """
    Stale-While-Revalidate Cache Wrapper.

    Gibt sofort cached Wert zurück (auch wenn stale)
    und signalisiert ob Revalidierung nötig ist.
    """

    def __init__(self, cache: CacheManager) -> None:
        """
        Initialisiere SWR Cache.

        Args:
            cache: Underlying CacheManager
        """
        self.cache = cache

    def get_with_status(
        self,
        key: str,
    ) -> tuple[Any | None, bool, bool]:
        """
        Hole Wert mit Status-Informationen.

        Args:
            key: Cache-Key

        Returns:
            Tuple: (value, is_fresh, needs_revalidation)
            - value: Cached Wert oder None
            - is_fresh: True wenn nicht abgelaufen
            - needs_revalidation: True wenn Refresh empfohlen
        """
        entry = self.cache.get(key)

        if entry is None:
            return None, False, True

        is_fresh = not entry.is_expired
        needs_revalidation = entry.is_expired or entry.is_stale

        return entry.value, is_fresh, needs_revalidation
