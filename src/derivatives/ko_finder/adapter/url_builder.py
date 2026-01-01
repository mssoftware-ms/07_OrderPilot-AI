"""
URL-Builder für Onvista KO-Listen.

Generiert parametrisierte URLs für die Knock-Out Produktlisten.
Onvista verwendet dedizierte URLs pro Underlying: /Knock-Outs-auf-{SLUG}
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode, quote

from ..config import KOFilterConfig
from ..constants import (
    DEFAULT_BROKER_ID,
    ONVISTA_BASE_URL,
    SYMBOL_TO_ONVISTA_SLUG,
    Direction,
    SortColumn,
    SortOrder,
)

logger = logging.getLogger(__name__)

# Standard-Spalten für die Tabelle (wie von Onvista erwartet)
DEFAULT_COLS = (
    "instrument,strikeAbs,knockOutAbs,dateMaturity,"
    "quote.bid,quote.ask,gearingAsk,spreadAskPct,"
    "derivativesSubCategory.id,issuer.name,urlProspectus"
)


class OnvistaURLBuilder:
    """
    Builder für Onvista KO-Listen URLs.

    Onvista verwendet dedizierte URLs pro Underlying:
    /derivate/Knock-Outs/Knock-Outs-auf-{SLUG}

    Nicht: /derivate/Knock-Outs?searchValue={name}
    """

    def __init__(self, base_url: str = ONVISTA_BASE_URL) -> None:
        """
        Initialisiere URL-Builder.

        Args:
            base_url: Basis-URL (Standard: https://www.onvista.de)
        """
        self.base_url = base_url

    def build_list_url(
        self,
        direction: Direction,
        config: KOFilterConfig,
        underlying_slug: str,
        sort_column: SortColumn = SortColumn.LEVERAGE,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> str:
        """
        Erstelle URL für KO-Listen-Seite.

        Args:
            direction: LONG oder SHORT
            config: Filter-Konfiguration
            underlying_slug: URL-Slug des Underlyings (z.B. "Bitcoin", "DAX")
            sort_column: Sortierspalte
            sort_order: Sortierrichtung

        Returns:
            Vollständige URL mit Query-Parametern
        """
        # Basis-Pfad mit Underlying-Slug
        base_path = f"{self.base_url}/derivate/Knock-Outs/Knock-Outs-auf-{underlying_slug}"

        params: dict[str, str] = {}

        # Spalten (wichtig für korrektes Rendering)
        params["cols"] = DEFAULT_COLS

        # Broker-ID (optional)
        if config.broker_id:
            params["brokerId"] = str(config.broker_id)

        # Feature-Filter (z.B. STOP_LOSS)
        if config.feature:
            params["feature"] = config.feature

        # Richtung: idExerciseRight
        # Long = 2 (Call), Short = 1 (Put)
        if direction == Direction.LONG:
            params["idExerciseRight"] = "2"
        else:
            params["idExerciseRight"] = "1"

        # Emittenten
        if config.issuers:
            params["idIssuer"] = config.issuer_ids_str

        # Sortierung
        params["sort"] = sort_column.value
        params["order"] = sort_order.value

        # Manuell URL bauen ohne Encoding von Kommas (Onvista erwartet uncodierte Kommas)
        query_parts = []
        for key, value in params.items():
            query_parts.append(f"{key}={value}")
        query_string = "&".join(query_parts)

        url = f"{base_path}?{query_string}"

        logger.debug(
            "Built URL for %s: %s",
            direction.name,
            url,
            extra={"direction": direction.name, "url": url},
        )

        return url

    def build_long_url(
        self,
        config: KOFilterConfig,
        underlying: str,
    ) -> str:
        """
        Erstelle Long-URL für Underlying.

        Args:
            config: Filter-Konfiguration
            underlying: Symbol/Name (wird zu Slug gemappt)

        Returns:
            URL für Long-Produkte
        """
        slug = self._get_slug(underlying)
        return self.build_list_url(
            direction=Direction.LONG,
            config=config,
            underlying_slug=slug,
        )

    def build_short_url(
        self,
        config: KOFilterConfig,
        underlying: str,
    ) -> str:
        """
        Erstelle Short-URL für Underlying.

        Args:
            config: Filter-Konfiguration
            underlying: Symbol/Name (wird zu Slug gemappt)

        Returns:
            URL für Short-Produkte
        """
        slug = self._get_slug(underlying)
        return self.build_list_url(
            direction=Direction.SHORT,
            config=config,
            underlying_slug=slug,
        )

    @staticmethod
    def _get_slug(underlying: str) -> str:
        """
        Konvertiere Underlying zu Onvista URL-Slug.

        Args:
            underlying: Symbol oder Name

        Returns:
            URL-Slug für Onvista
        """
        # Exakter Match
        if underlying in SYMBOL_TO_ONVISTA_SLUG:
            return SYMBOL_TO_ONVISTA_SLUG[underlying]

        # Uppercase Match
        upper = underlying.upper()
        if upper in SYMBOL_TO_ONVISTA_SLUG:
            return SYMBOL_TO_ONVISTA_SLUG[upper]

        # Fallback: Leerzeichen durch Bindestriche ersetzen
        return underlying.replace(" ", "-")

    @staticmethod
    def build_detail_url(wkn: str) -> str:
        """
        Erstelle URL für Produkt-Detailseite.

        Args:
            wkn: WKN des Produkts

        Returns:
            URL zur Detailseite
        """
        return f"https://www.onvista.de/derivate/{wkn}"
