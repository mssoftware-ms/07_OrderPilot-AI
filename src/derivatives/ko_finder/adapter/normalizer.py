"""
Normalizer für Onvista KO-Produkt-Daten.

Aufgaben:
- Zahlen normalisieren (deutsche Formatierung)
- Währungen vereinheitlichen
- Plausibilitätsprüfungen
- Qualitätsflags setzen
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING

from ..constants import Direction
from ..models import KnockoutProduct, ProductFlag, Quote

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class OnvistaNormalizer:
    """
    Normalisierer für Onvista-Daten.

    Bereinigt und validiert geparste Produkt-Daten.
    """

    def normalize_products(
        self,
        products: list[KnockoutProduct],
        underlying_price: float | None = None,
    ) -> list[KnockoutProduct]:
        """
        Normalisiere Liste von Produkten.

        Args:
            products: Geparste Produkte
            underlying_price: Optional: Aktueller Underlying-Kurs

        Returns:
            Normalisierte Produkte
        """
        normalized = []

        for product in products:
            try:
                norm_product = self.normalize_product(product, underlying_price)
                if norm_product:
                    normalized.append(norm_product)
            except Exception as e:
                logger.warning(
                    "Failed to normalize product %s: %s",
                    product.wkn,
                    e,
                )

        return normalized

    def normalize_product(
        self,
        product: KnockoutProduct,
        underlying_price: float | None = None,
    ) -> KnockoutProduct | None:
        """
        Normalisiere einzelnes Produkt.

        Args:
            product: Geparstes Produkt
            underlying_price: Optional: Aktueller Underlying-Kurs

        Returns:
            Normalisiertes Produkt oder None bei Fehler
        """
        # Underlying-Preis setzen wenn vorhanden
        if underlying_price is not None:
            product.underlying.price = underlying_price
            product.underlying.as_of = datetime.now()

        # Quote normalisieren
        self._normalize_quote(product.quote)

        # Spread berechnen wenn nicht vorhanden
        if product.quote.spread_pct is None:
            product.quote.spread_pct = product.quote.calculate_spread_pct()

        # KO-Abstand berechnen
        self._calculate_ko_distance(product)

        # Plausibilitätsprüfungen
        self._validate_product(product)

        return product

    def _normalize_quote(self, quote: Quote) -> None:
        """Normalisiere Quote-Daten."""
        # Negative Werte korrigieren
        if quote.bid is not None and quote.bid < 0:
            quote.bid = None
            quote.missing = True

        if quote.ask is not None and quote.ask < 0:
            quote.ask = None
            quote.missing = True

        # Bid > Ask ist ungültig
        if (
            quote.bid is not None
            and quote.ask is not None
            and quote.bid > quote.ask
        ):
            quote.stale = True
            logger.warning("Invalid quote: bid > ask")

        # Spread normalisieren (muss positiv sein)
        if quote.spread_pct is not None and quote.spread_pct < 0:
            quote.spread_pct = abs(quote.spread_pct)

    def _calculate_ko_distance(self, product: KnockoutProduct) -> None:
        """Berechne KO-Abstand wenn möglich."""
        # Bereits berechnet?
        if product.ko_distance_pct is not None:
            return

        # Können wir berechnen?
        if product.knockout_level is None:
            return

        if product.underlying.price is None or product.underlying.price <= 0:
            return

        underlying_price = product.underlying.price
        ko_level = product.knockout_level

        if product.direction == Direction.LONG:
            # Long: KO unter aktuellem Kurs
            if ko_level < underlying_price:
                product.ko_distance_pct = (
                    (underlying_price - ko_level) / underlying_price * 100
                )
        else:
            # Short: KO über aktuellem Kurs
            if ko_level > underlying_price:
                product.ko_distance_pct = (
                    (ko_level - underlying_price) / underlying_price * 100
                )

    def _validate_product(self, product: KnockoutProduct) -> None:
        """Führe Plausibilitätsprüfungen durch und setze Flags."""
        # Hebel prüfen
        if product.leverage is not None:
            if product.leverage <= 0:
                product.leverage = None
                if ProductFlag.MISSING_FIELDS not in product.flags:
                    product.flags.append(ProductFlag.MISSING_FIELDS)

            elif product.leverage > 500:
                # Sehr hoher Hebel - möglicherweise Parsing-Fehler
                if ProductFlag.PARSING_UNCERTAIN not in product.flags:
                    product.flags.append(ProductFlag.PARSING_UNCERTAIN)

        # KO-Abstand prüfen
        if product.ko_distance_pct is not None:
            if product.ko_distance_pct <= 0:
                # KO bereits erreicht oder überschritten
                if ProductFlag.INACTIVE not in product.flags:
                    product.flags.append(ProductFlag.INACTIVE)

            elif product.ko_distance_pct < 0.5:
                # Sehr nahe am KO
                if ProductFlag.KO_NEAR not in product.flags:
                    product.flags.append(ProductFlag.KO_NEAR)

        # KO-Level Plausibilität
        if (
            product.knockout_level is not None
            and product.underlying.price is not None
        ):
            if product.direction == Direction.LONG:
                # Long: KO muss unter Underlying sein
                if product.knockout_level >= product.underlying.price:
                    if ProductFlag.INACTIVE not in product.flags:
                        product.flags.append(ProductFlag.INACTIVE)
            else:
                # Short: KO muss über Underlying sein
                if product.knockout_level <= product.underlying.price:
                    if ProductFlag.INACTIVE not in product.flags:
                        product.flags.append(ProductFlag.INACTIVE)

        # Quote prüfen
        if not product.quote.is_valid:
            if ProductFlag.STALE_QUOTE not in product.flags:
                product.flags.append(ProductFlag.STALE_QUOTE)


def parse_german_number(text: str) -> float | None:
    """
    Parse Zahl mit deutscher Formatierung.

    Args:
        text: Text wie "1.234,56" oder "1234,56%"

    Returns:
        Float oder None
    """
    if not text or text in ["-", "–", "n.a.", "n/a", ""]:
        return None

    try:
        # Entferne Tausender-Punkte
        cleaned = text.replace(".", "")

        # Ersetze Komma durch Punkt
        cleaned = cleaned.replace(",", ".")

        # Entferne Währung/Prozent
        cleaned = re.sub(r"[%€$\s]", "", cleaned)

        return float(cleaned)

    except (ValueError, AttributeError):
        return None


def parse_percentage(text: str) -> float | None:
    """
    Parse Prozentangabe.

    Args:
        text: Text wie "2,5%" oder "2.5 %"

    Returns:
        Float (als Prozent, nicht Dezimal)
    """
    value = parse_german_number(text)
    if value is not None:
        # Schon als Prozent interpretieren
        return value
    return None
