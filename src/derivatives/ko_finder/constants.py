"""
Konstanten für den Onvista KO-Finder.

Enthält:
- Issuer-IDs und Mappings
- Base-URLs und Endpunkte
- Default-Werte
- HTTP-Header
"""

from __future__ import annotations

from enum import Enum
from typing import Final


# =============================================================================
# Issuer Mappings (Onvista-spezifische IDs)
# =============================================================================

class Issuer(Enum):
    """Unterstützte Emittenten mit Onvista-IDs."""

    HSBC = 53159
    SOCIETE_GENERALE = 54101
    UBS = 53882
    VONTOBEL = 53163

    @property
    def display_name(self) -> str:
        """Anzeigename für UI."""
        names = {
            Issuer.HSBC: "HSBC",
            Issuer.SOCIETE_GENERALE: "Société Générale",
            Issuer.UBS: "UBS",
            Issuer.VONTOBEL: "Vontobel",
        }
        return names[self]


# Alle Standard-Issuer als kommaseparierter String
DEFAULT_ISSUER_IDS: Final[str] = ",".join(str(i.value) for i in Issuer)


# =============================================================================
# URLs und Endpunkte
# =============================================================================

ONVISTA_BASE_URL: Final[str] = "https://www.onvista.de"
ONVISTA_KO_LIST_PATH: Final[str] = "/derivate/Knock-Outs"
ONVISTA_KO_LIST_URL: Final[str] = f"{ONVISTA_BASE_URL}{ONVISTA_KO_LIST_PATH}"


# =============================================================================
# URL-Parameter
# =============================================================================

class Direction(Enum):
    """Handelsrichtung für KO-Produkte."""

    LONG = 0
    SHORT = 1

    @property
    def exercise_right_param(self) -> str | None:
        """URL-Parameter für idExerciseRight."""
        if self == Direction.SHORT:
            return "1"
        return None  # Long braucht keinen Parameter


class SortColumn(Enum):
    """Verfügbare Sortierspalten."""

    SPREAD_PCT = "spreadAskPct"
    LEVERAGE = "gearingAsk"  # Onvista verwendet gearingAsk für Hebel
    KO_DISTANCE = "knockoutDistance"


class SortOrder(Enum):
    """Sortierrichtung."""

    ASC = "ASC"
    DESC = "DESC"


# =============================================================================
# Default-Werte
# =============================================================================

# Filter-Defaults (keine Anlageberatung!)
DEFAULT_MIN_LEVERAGE: Final[float] = 5.0
DEFAULT_MAX_SPREAD_PCT: Final[float] = 2.0
DEFAULT_TOP_N: Final[int] = 10
DEFAULT_BROKER_ID: Final[int] = 8260  # Trade Republic

# Minimaler KO-Abstand (um "Quasi-Treffer" zu vermeiden)
DEFAULT_MIN_KO_DISTANCE_PCT: Final[float] = 0.5


# =============================================================================
# HTTP-Einstellungen
# =============================================================================

HTTP_TIMEOUT_CONNECT: Final[float] = 5.0
HTTP_TIMEOUT_READ: Final[float] = 10.0
HTTP_MAX_RETRIES: Final[int] = 3
HTTP_BACKOFF_FACTOR: Final[float] = 1.5
HTTP_JITTER: Final[float] = 0.5

# Rate-Limiting
RATE_LIMIT_MIN_DELAY: Final[float] = 1.5  # Sekunden zwischen Requests (Onvista ist streng)
CIRCUIT_BREAKER_THRESHOLD: Final[int] = 3  # Fehler bis Pause
CIRCUIT_BREAKER_TIMEOUT: Final[float] = 60.0  # Sekunden Pause

# User-Agent (Browser-ähnlich, aktuell 2024/2025)
HTTP_USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

HTTP_HEADERS: Final[dict[str, str]] = {
    "User-Agent": HTTP_USER_AGENT,
    "Referer": "https://www.onvista.de/",
    "Origin": "https://www.onvista.de",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}


# =============================================================================
# Parser-Einstellungen
# =============================================================================

PARSER_SCHEMA_VERSION: Final[str] = "1.0.0"
PARSER_MIN_CONFIDENCE: Final[float] = 0.8  # Unter diesem Wert: exclude

# Erwartete Tabellen-Header (für robustes Parsing)
EXPECTED_TABLE_HEADERS: Final[list[str]] = [
    "WKN",
    "Emittent",
    "Hebel",
    "Spread",
    "Geld",
    "Brief",
    "KO-Schwelle",
]


# =============================================================================
# Cache-Einstellungen
# =============================================================================

CACHE_TTL_KO_LIST: Final[int] = 30  # Sekunden
CACHE_TTL_UNDERLYING_MAP: Final[int] = 3600  # 1 Stunde
CACHE_MAX_SIZE: Final[int] = 100  # Max Einträge


# =============================================================================
# Datenquelle (für Assertions)
# =============================================================================

DATA_SOURCE: Final[str] = "onvista"


# =============================================================================
# Symbol-Mapping (Ticker → Onvista URL-Slug)
# Onvista verwendet dedizierte URLs: /Knock-Outs-auf-{SLUG}
# =============================================================================

SYMBOL_TO_ONVISTA_SLUG: Final[dict[str, str]] = {
    # Crypto
    "BTC/USD": "Bitcoin",
    "BTC": "Bitcoin",
    "ETH/USD": "Ethereum",
    "ETH": "Ethereum",
    "SOL/USD": "Solana",
    "SOL": "Solana",
    "XRP/USD": "Ripple",
    "XRP": "Ripple",
    "DOGE/USD": "Dogecoin",
    "DOGE": "Dogecoin",
    "ADA/USD": "Cardano",
    "ADA": "Cardano",
    "DOT/USD": "Polkadot",
    "DOT": "Polkadot",
    "AVAX/USD": "Avalanche",
    "AVAX": "Avalanche",
    "LINK/USD": "Chainlink",
    "LINK": "Chainlink",
    "LTC/USD": "Litecoin",
    "LTC": "Litecoin",
    # US Aktien (häufige)
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet-A",
    "GOOG": "Alphabet-A",
    "AMZN": "Amazon",
    "META": "Meta-Platforms-A",
    "TSLA": "Tesla",
    "NVDA": "NVIDIA",
    "AMD": "AMD",
    "NFLX": "Netflix",
    "DIS": "Walt-Disney",
    "PYPL": "PayPal-Holdings",
    "INTC": "Intel",
    "CRM": "Salesforce",
    "ORCL": "Oracle",
    "CSCO": "Cisco-Systems",
    "IBM": "IBM",
    "BA": "Boeing",
    "JPM": "JPMorgan-Chase",
    "V": "Visa",
    "MA": "Mastercard",
    "WMT": "Walmart",
    "KO": "Coca-Cola",
    "PEP": "PepsiCo",
    "MCD": "McDonalds",
    "NKE": "Nike",
    # Indizes
    "SPY": "S-P-500",
    "QQQ": "Nasdaq-100",
    "NDX": "Nasdaq-100",
    "SPX": "S-P-500",
    "DAX": "DAX",
    # Deutsche Aktien
    "SAP": "SAP",
    "SIE": "Siemens",
    "ALV": "Allianz",
    "DTE": "Deutsche-Telekom",
    "BAS": "BASF",
    "BMW": "BMW",
    "VOW3": "Volkswagen-VZ",
    "MBG": "Mercedes-Benz-Group",
    "DAI": "Mercedes-Benz-Group",
}
