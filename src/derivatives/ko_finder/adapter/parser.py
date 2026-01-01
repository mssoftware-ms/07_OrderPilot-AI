"""
HTML-Parser für Onvista KO-Listen.

Implementiert robustes Parsing mit:
- Header-basiertem Spaltenmapping (keine festen Indizes)
- Parser-Confidence Berechnung
- Fehlertoleranz bei HTML-Änderungen
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup, Tag

from ..constants import DATA_SOURCE, PARSER_SCHEMA_VERSION, Direction
from ..models import KnockoutProduct, ProductFlag, Quote, UnderlyingSnapshot

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Ergebnis des Parsings."""

    products: list[KnockoutProduct]
    success: bool = True
    error: str | None = None
    confidence: float = 1.0
    rows_parsed: int = 0
    rows_failed: int = 0
    schema_version: str = PARSER_SCHEMA_VERSION


class OnvistaParser:
    """
    Parser für Onvista KO-Listen HTML.

    Verwendet header-basiertes Spaltenmapping für Robustheit
    gegen HTML-Änderungen.
    """

    # Erwartete Header (deutsch, Onvista-spezifisch)
    # WICHTIG: Reihenfolge und Spezifität beachten!
    # "Brief Kurs" muss vor "Hebel (Brief)" gematched werden
    HEADER_MAPPINGS = {
        "wkn": ["WKN", "wkn"],
        "name": ["Name", "Bezeichnung", "Produkt"],
        "issuer": ["Emittent", "Herausgeber"],
        "type": ["Typ", "Art", "Produkttyp"],
        "leverage": ["Hebel (Brief)", "Hebel (Ask)", "Hebel", "Leverage"],
        "spread": ["Spread", "Spread %", "Spread Ask"],
        "bid": ["Geld Kurs", "Geld", "Bid", "Kaufkurs"],
        "ask": ["Brief Kurs", "Ask", "Verkaufskurs"],
        "ko_level": ["K.O.-Schwelle", "KO-Schwelle", "Knock-Out", "KO", "Barriere"],
        "underlying": ["Basiswert", "Underlying"],
        "distance": ["Abstand", "KO-Abstand", "Abstand %"],
    }

    def __init__(self) -> None:
        """Initialisiere Parser."""
        self._column_map: dict[str, int] = {}

    def parse(
        self,
        html: str,
        direction: Direction,
        source_url: str = "",
        run_id: str = "",
    ) -> ParseResult:
        """
        Parse HTML und extrahiere KO-Produkte.

        Args:
            html: HTML-Content der Seite
            direction: LONG oder SHORT
            source_url: URL für Referenz
            run_id: Run-ID für Logging

        Returns:
            ParseResult mit Produkten und Metadaten
        """
        try:
            # Versuche lxml (schneller), fallback auf html.parser (eingebaut)
            try:
                soup = BeautifulSoup(html, "lxml")
            except Exception:
                logger.info("lxml not available, using html.parser")
                soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            logger.error("Failed to parse HTML: %s", e)
            return ParseResult(
                products=[],
                success=False,
                error=f"HTML parsing failed: {e}",
                confidence=0.0,
            )

        # Tabelle finden
        table = self._find_table(soup)
        if not table:
            logger.warning("No product table found in HTML")
            return ParseResult(
                products=[],
                success=False,
                error="No product table found",
                confidence=0.0,
            )

        # Header extrahieren und mappen
        if not self._extract_headers(table):
            return ParseResult(
                products=[],
                success=False,
                error="Failed to extract table headers",
                confidence=0.0,
            )

        # Zeilen parsen
        products: list[KnockoutProduct] = []
        rows_parsed = 0
        rows_failed = 0

        rows = table.find_all("tr")[1:]  # Skip header row

        for row in rows:
            try:
                product = self._parse_row(row, direction, source_url)
                if product:
                    products.append(product)
                    rows_parsed += 1
            except Exception as e:
                logger.debug("Failed to parse row: %s", e)
                rows_failed += 1

        # Confidence berechnen
        total_rows = rows_parsed + rows_failed
        confidence = rows_parsed / total_rows if total_rows > 0 else 0.0

        logger.info(
            "Parsed %d products (%d failed) with %.2f confidence",
            rows_parsed,
            rows_failed,
            confidence,
            extra={
                "run_id": run_id,
                "direction": direction.name,
                "parsed": rows_parsed,
                "failed": rows_failed,
            },
        )

        return ParseResult(
            products=products,
            success=True,
            confidence=confidence,
            rows_parsed=rows_parsed,
            rows_failed=rows_failed,
        )

    def _find_table(self, soup: BeautifulSoup) -> Tag | None:
        """Finde die Produkt-Tabelle im HTML."""
        # Versuche verschiedene Selektoren
        selectors = [
            "table.derivative-table",
            "table.product-table",
            "table[data-qa='derivative-list']",
            "div.derivative-list table",
            "main table",
            "table",
        ]

        for selector in selectors:
            table = soup.select_one(selector)
            if table and self._is_product_table(table):
                return table

        # Fallback: Alle Tabellen durchsuchen
        for table in soup.find_all("table"):
            if self._is_product_table(table):
                return table

        return None

    def _is_product_table(self, table: Tag) -> bool:
        """Prüfe ob Tabelle eine Produkt-Tabelle ist."""
        headers = table.find_all("th")
        if not headers:
            return False

        header_texts = [h.get_text(strip=True).lower() for h in headers]

        # Mindestens WKN oder Hebel muss vorhanden sein
        key_headers = ["wkn", "hebel", "leverage", "spread"]
        return any(any(kh in ht for kh in key_headers) for ht in header_texts)

    def _extract_headers(self, table: Tag) -> bool:
        """Extrahiere und mappe Tabellen-Header."""
        self._column_map = {}

        header_row = table.find("tr")
        if not header_row:
            return False

        headers = header_row.find_all(["th", "td"])
        if not headers:
            return False

        for idx, header in enumerate(headers):
            header_text = header.get_text(strip=True).lower()

            # Mappe Header auf bekannte Felder
            # Priorisiere exakte/längere Matches um Überschreibungen zu vermeiden
            for field, variants in self.HEADER_MAPPINGS.items():
                for variant in variants:
                    variant_lower = variant.lower()
                    if variant_lower in header_text:
                        # Prüfe ob wir schon ein Match haben
                        if field in self._column_map:
                            # Überschreibe nur wenn neues Match spezifischer ist
                            # (längeres Variant = spezifischer)
                            existing_idx = self._column_map[field]
                            existing_header = headers[existing_idx].get_text(strip=True).lower()
                            # Behalte das spezifischere Match (kürzerer Header-Text)
                            if len(header_text) < len(existing_header):
                                self._column_map[field] = idx
                        else:
                            self._column_map[field] = idx
                        break

        logger.debug("Column mapping: %s", self._column_map)

        # Mindestens WKN muss gefunden werden
        return "wkn" in self._column_map

    def _parse_row(
        self,
        row: Tag,
        direction: Direction,
        source_url: str,
    ) -> KnockoutProduct | None:
        """Parse einzelne Tabellenzeile."""
        cells = row.find_all("td")
        if not cells:
            return None

        def get_cell_text(field: str) -> str:
            """Hole Text aus Zelle für Feld."""
            idx = self._column_map.get(field)
            if idx is not None and idx < len(cells):
                return cells[idx].get_text(strip=True)
            return ""

        def get_cell_link(field: str) -> str:
            """Hole Link aus Zelle."""
            idx = self._column_map.get(field)
            if idx is not None and idx < len(cells):
                link = cells[idx].find("a")
                if link and link.get("href"):
                    return link["href"]
            return ""

        # WKN extrahieren (Pflichtfeld)
        wkn = get_cell_text("wkn")
        if not wkn or len(wkn) < 5:
            return None

        # Parse Werte zuerst
        leverage = self._parse_float(get_cell_text("leverage"))
        knockout_level = self._parse_float(get_cell_text("ko_level"))
        bid = self._parse_float(get_cell_text("bid"))
        ask = self._parse_float(get_cell_text("ask"))
        spread = self._parse_float(get_cell_text("spread"))

        # Quote erstellen
        quote = Quote(
            bid=bid,
            ask=ask,
            spread_pct=spread,
            quote_as_of=datetime.now(),
            missing=bid is None or ask is None,
        )

        # Berechne Spread wenn nicht vorhanden
        if quote.spread_pct is None and bid and ask:
            quote.spread_pct = quote.calculate_spread_pct()

        # Produkt erstellen (mit allen Werten, damit __post_init__ korrekt läuft)
        product = KnockoutProduct(
            wkn=wkn,
            name=get_cell_text("name"),
            issuer=get_cell_text("issuer"),
            direction=direction,
            source=DATA_SOURCE,
            source_url=source_url or get_cell_link("wkn"),
            fetched_at=datetime.now(),
            parse_schema_version=PARSER_SCHEMA_VERSION,
            leverage=leverage,
            knockout_level=knockout_level,
            quote=quote,
        )

        # KO-Abstand (aus HTML wenn vorhanden)
        distance = self._parse_float(get_cell_text("distance"))
        if distance is not None:
            product.ko_distance_pct = distance

        # Parser-Confidence basierend auf gefüllten Feldern
        product.parser_confidence = self._calculate_confidence(product)

        # Flags setzen
        if product.parser_confidence < 0.8:
            product.flags.append(ProductFlag.PARSING_UNCERTAIN)

        return product

    def _parse_float(self, text: str) -> float | None:
        """Parse float aus Text mit deutscher Formatierung."""
        if not text or text in ["-", "–", "n.a.", "n/a", ""]:
            return None

        try:
            # Entferne Währungscodes und Symbole (EUR, USD, €, $, etc.)
            cleaned = re.sub(r"(EUR|USD|CHF|GBP|[€$£])", "", text, flags=re.IGNORECASE)

            # Entferne Tausender-Punkte, ersetze Komma durch Punkt
            cleaned = cleaned.replace(".", "").replace(",", ".")

            # Entferne Prozentzeichen
            cleaned = re.sub(r"[%]", "", cleaned)

            # Entferne Leerzeichen
            cleaned = cleaned.strip()

            return float(cleaned)

        except (ValueError, AttributeError):
            return None

    def _calculate_confidence(self, product: KnockoutProduct) -> float:
        """Berechne Parser-Confidence für Produkt."""
        confidence = 1.0

        # Pflichtfelder
        if not product.wkn:
            confidence -= 0.3
        if product.leverage is None:
            confidence -= 0.15
        if product.knockout_level is None:
            confidence -= 0.15

        # Quote-Qualität
        if not product.quote.is_valid:
            confidence -= 0.2

        # Spread vorhanden
        if product.spread_pct is None:
            confidence -= 0.1

        return max(0.0, confidence)
