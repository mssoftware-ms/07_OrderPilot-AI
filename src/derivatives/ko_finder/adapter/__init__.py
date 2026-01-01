"""
Onvista Adapter für KO-Finder.

Enthält:
- OnvistaURLBuilder: URL-Generierung für KO-Listen
- OnvistaFetcher: HTTP-Client mit Rate-Limiting
- PlaywrightFetcher: Headless-Browser für Bot-Protection
- OnvistaParser: HTML → Modelle Konvertierung
- OnvistaNormalizer: Daten-Normalisierung
"""

from .fetcher import OnvistaFetcher
from .normalizer import OnvistaNormalizer
from .parser import OnvistaParser
from .playwright_fetcher import PlaywrightFetcher
from .url_builder import OnvistaURLBuilder

__all__ = [
    "OnvistaURLBuilder",
    "OnvistaFetcher",
    "PlaywrightFetcher",
    "OnvistaParser",
    "OnvistaNormalizer",
]
