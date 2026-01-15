"""
Datenmodelle für den KO-Finder.

Enthält:
- Quote: Bid/Ask/Spread Daten
- UnderlyingSnapshot: Basiswert-Informationen
- KnockoutProduct: Vollständiges KO-Produkt
- SearchResponse: API-Antwort mit Meta-Informationen
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .constants import DATA_SOURCE, PARSER_SCHEMA_VERSION, Direction


class ProductFlag(Enum):
    """Qualitäts-Flags für Produkte."""

    MISSING_FIELDS = "missing_fields"
    STALE_QUOTE = "stale_quote"
    PARSING_UNCERTAIN = "parsing_uncertain"
    LOW_CONFIDENCE = "low_confidence"
    INACTIVE = "inactive"
    KO_NEAR = "ko_near"  # KO-Schwelle sehr nah


@dataclass
class Quote:
    """Kurs-Informationen (Bid/Ask/Spread)."""

    bid: float | None = None
    ask: float | None = None
    spread_pct: float | None = None
    quote_as_of: datetime | None = None
    stale: bool = False
    missing: bool = False

    @property
    def is_valid(self) -> bool:
        """Prüft ob Quote gültig ist (Bid und Ask vorhanden, nicht stale)."""
        return (
            self.bid is not None
            and self.ask is not None
            and not self.stale
            and not self.missing
        )

    def calculate_spread_pct(self) -> float | None:
        """Berechnet Spread in Prozent aus Bid/Ask."""
        if self.bid is not None and self.ask is not None and self.bid > 0:
            return ((self.ask - self.bid) / self.bid) * 100
        return None


@dataclass
class UnderlyingSnapshot:
    """Snapshot des Basiswerts."""

    symbol: str = ""
    name: str = ""
    price: float | None = None
    currency: str = "EUR"
    as_of: datetime | None = None
    source: str = DATA_SOURCE


@dataclass
class KnockoutProduct:
    """
    Vollständiges Knock-Out Produkt.

    Alle Daten stammen ausschließlich von Onvista (source="onvista").
    """

    # Identifikation
    wkn: str = ""
    isin: str | None = None
    name: str = ""

    # Emittent und Richtung
    issuer: str = ""
    issuer_id: int | None = None
    direction: Direction = Direction.LONG

    # Produkt-Daten
    knockout_level: float | None = None
    leverage: float | None = None
    ratio: float | None = None  # Bezugsverhältnis
    expiry: datetime | None = None  # Laufzeitende (None = open-end)

    # Kurs-Daten
    quote: Quote = field(default_factory=Quote)
    underlying: UnderlyingSnapshot = field(default_factory=UnderlyingSnapshot)

    # Berechnete Werte
    ko_distance_pct: float | None = None
    score: float | None = None

    # Meta & Qualität
    source: str = DATA_SOURCE
    source_url: str = ""
    fetched_at: datetime = field(default_factory=datetime.now)
    parse_schema_version: str = PARSER_SCHEMA_VERSION
    parser_confidence: float = 1.0
    flags: list[ProductFlag] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Berechne abgeleitete Werte."""
        self._calculate_ko_distance()
        self._check_flags()

    def _calculate_ko_distance(self) -> None:
        """Berechne KO-Abstand in Prozent."""
        if (
            self.knockout_level is not None
            and self.underlying.price is not None
            and self.underlying.price > 0
        ):
            if self.direction == Direction.LONG:
                # Long: KO unter aktuellem Kurs
                self.ko_distance_pct = (
                    (self.underlying.price - self.knockout_level)
                    / self.underlying.price
                    * 100
                )
            else:
                # Short: KO über aktuellem Kurs
                self.ko_distance_pct = (
                    (self.knockout_level - self.underlying.price)
                    / self.underlying.price
                    * 100
                )

    def _check_flags(self) -> None:
        """Setze automatische Flags basierend auf Datenqualität."""
        # Missing fields
        if self.knockout_level is None or self.leverage is None:
            if ProductFlag.MISSING_FIELDS not in self.flags:
                self.flags.append(ProductFlag.MISSING_FIELDS)

        # Quote-Probleme
        if not self.quote.is_valid:
            if ProductFlag.STALE_QUOTE not in self.flags:
                self.flags.append(ProductFlag.STALE_QUOTE)

        # Low confidence
        if self.parser_confidence < 0.8:
            if ProductFlag.LOW_CONFIDENCE not in self.flags:
                self.flags.append(ProductFlag.LOW_CONFIDENCE)

        # KO nah
        if self.ko_distance_pct is not None and self.ko_distance_pct < 1.0:
            if ProductFlag.KO_NEAR not in self.flags:
                self.flags.append(ProductFlag.KO_NEAR)

    @property
    def is_tradeable(self) -> bool:
        """Prüft ob Produkt handelbar erscheint."""
        return (
            self.quote.is_valid
            and ProductFlag.INACTIVE not in self.flags
            and self.ko_distance_pct is not None
            and self.ko_distance_pct > 0
        )

    @property
    def spread_pct(self) -> float | None:
        """Spread in Prozent (aus Quote oder berechnet)."""
        if self.quote.spread_pct is not None:
            return self.quote.spread_pct
        return self.quote.calculate_spread_pct()

    def update_ko_distance(self, underlying_price: float) -> None:
        """
        Aktualisiere KO-Abstand mit neuem Underlying-Preis.

        Args:
            underlying_price: Aktueller Underlying-Kurs
        """
        if self.knockout_level is None or underlying_price <= 0:
            return

        self.underlying.price = underlying_price

        if self.direction == Direction.LONG:
            # Long: KO unter aktuellem Kurs
            self.ko_distance_pct = (
                (underlying_price - self.knockout_level)
                / underlying_price
                * 100
            )
        else:
            # Short: KO über aktuellem Kurs
            self.ko_distance_pct = (
                (self.knockout_level - underlying_price)
                / underlying_price
                * 100
            )

        # KO_NEAR Flag aktualisieren
        if ProductFlag.KO_NEAR in self.flags:
            self.flags.remove(ProductFlag.KO_NEAR)
        if self.ko_distance_pct is not None and self.ko_distance_pct < 1.0:
            self.flags.append(ProductFlag.KO_NEAR)


@dataclass
class SearchMeta:
    """Meta-Informationen zur Suche."""

    run_id: str = ""
    fetch_time_ms: int = 0
    as_of: datetime = field(default_factory=datetime.now)

    # Status pro Richtung
    long_status: str = "OK"
    short_status: str = "OK"
    errors: list[str] = field(default_factory=list)

    # Parser-Qualität
    parser_confidence_avg: float = 1.0
    parser_confidence_min: float = 1.0

    # Zähler
    long_found: int = 0
    long_filtered: int = 0
    short_found: int = 0
    short_filtered: int = 0

    # Cache-Info
    cache_hit: bool = False
    cache_age_s: float = 0.0

    # Quelle
    source: str = DATA_SOURCE


@dataclass
class SearchRequest:
    """Suchanfrage für KO-Produkte."""

    underlying: str
    underlying_name: str = ""
    config: Any = None  # KOFilterConfig


@dataclass
class SearchResponse:
    """
    Vollständige Suchantwort mit Long/Short Ergebnissen.

    Alle Daten stammen ausschließlich von Onvista.
    """

    underlying: str = ""
    underlying_name: str = ""
    as_of: datetime = field(default_factory=datetime.now)

    # Ergebnisse
    long: list[KnockoutProduct] = field(default_factory=list)
    short: list[KnockoutProduct] = field(default_factory=list)

    # Meta
    meta: SearchMeta = field(default_factory=SearchMeta)

    # Filter-Kriterien (für Anzeige)
    criteria: dict = field(default_factory=dict)

    @property
    def total_results(self) -> int:
        """Gesamtanzahl Ergebnisse."""
        return len(self.long) + len(self.short)

    @property
    def has_errors(self) -> bool:
        """Prüft ob Fehler aufgetreten sind."""
        return bool(self.meta.errors)
