"""
KO-Finder Modul für Onvista Knock-Out Produkt-Suche.

WICHTIG: Onvista ist die EINZIGE erlaubte Datenquelle.
Siehe docs/ONVISTA_SCRAPING_NOTES.md für Details.

Verwendung:
    from src.derivatives.ko_finder import KOFinderService, KOFilterConfig

    config = KOFilterConfig(min_leverage=5.0, max_spread_pct=2.0)
    service = KOFinderService()
    result = await service.search("NASDAQ 100", config)
"""

from .config import KOFilterConfig
from .constants import (
    DATA_SOURCE,
    DEFAULT_BROKER_ID,
    DEFAULT_MAX_SPREAD_PCT,
    DEFAULT_MIN_LEVERAGE,
    DEFAULT_TOP_N,
    Direction,
    Issuer,
    SortColumn,
    SortOrder,
)
from .models import (
    KnockoutProduct,
    ProductFlag,
    Quote,
    SearchMeta,
    SearchRequest,
    SearchResponse,
    UnderlyingSnapshot,
)

__all__ = [
    # Config
    "KOFilterConfig",
    # Constants
    "DATA_SOURCE",
    "DEFAULT_BROKER_ID",
    "DEFAULT_MAX_SPREAD_PCT",
    "DEFAULT_MIN_LEVERAGE",
    "DEFAULT_TOP_N",
    "Direction",
    "Issuer",
    "SortColumn",
    "SortOrder",
    # Models
    "KnockoutProduct",
    "ProductFlag",
    "Quote",
    "SearchMeta",
    "SearchRequest",
    "SearchResponse",
    "UnderlyingSnapshot",
]
