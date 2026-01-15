"""
Engine-Komponenten für KO-Finder.

Enthält:
- HardFilters: Ausschlusskriterien
- RankingEngine: Scoring und Sortierung
- CacheManager: Stale-While-Revalidate Cache
"""

from .cache import CacheEntry, CacheManager
from .filters import HardFilters
from .ranking import RankingEngine

__all__ = [
    "HardFilters",
    "RankingEngine",
    "CacheManager",
    "CacheEntry",
]
