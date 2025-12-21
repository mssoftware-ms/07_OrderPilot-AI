"""
Hard Filters für KO-Produkte.

Implementiert Ausschlusskriterien basierend auf:
- Mindesthebel
- Maximaler Spread
- Quote-Validität
- KO-Abstand
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..constants import Issuer
from ..models import KnockoutProduct, ProductFlag

if TYPE_CHECKING:
    from ..config import KOFilterConfig

logger = logging.getLogger(__name__)


@dataclass
class FilterResult:
    """Ergebnis der Filterung."""

    passed: list[KnockoutProduct]
    filtered_out: int = 0
    reasons: dict[str, int] = None  # Grund -> Anzahl

    def __post_init__(self) -> None:
        if self.reasons is None:
            self.reasons = {}


class HardFilters:
    """
    Hard Filters für KO-Produkte.

    Produkte, die diese Filter nicht bestehen, werden ausgeschlossen.
    """

    def __init__(self, config: KOFilterConfig) -> None:
        """
        Initialisiere Filter mit Konfiguration.

        Args:
            config: Filter-Konfiguration
        """
        self.config = config

    def apply(self, products: list[KnockoutProduct]) -> FilterResult:
        """
        Wende alle Filter auf Produkte an.

        Args:
            products: Zu filternde Produkte

        Returns:
            FilterResult mit gefilterten Produkten und Statistiken
        """
        passed = []
        reasons: dict[str, int] = {}

        for product in products:
            reject_reason = self._check_product(product)

            if reject_reason is None:
                passed.append(product)
            else:
                reasons[reject_reason] = reasons.get(reject_reason, 0) + 1

        filtered_out = len(products) - len(passed)

        logger.info(
            "Filtered %d products: %d passed, %d removed",
            len(products),
            len(passed),
            filtered_out,
            extra={"reasons": reasons},
        )

        return FilterResult(
            passed=passed,
            filtered_out=filtered_out,
            reasons=reasons,
        )

    def _check_product(self, product: KnockoutProduct) -> str | None:
        """
        Prüfe Produkt gegen alle Filter.

        Args:
            product: Zu prüfendes Produkt

        Returns:
            Ablehnungsgrund oder None wenn OK
        """
        # 1. Issuer prüfen
        if not self._check_issuer(product):
            return "invalid_issuer"

        # 2. Quote-Validität
        if not self._check_quote(product):
            return "invalid_quote"

        # 3. Mindesthebel
        if not self._check_leverage(product):
            return "low_leverage"

        # 4. Maximaler Spread
        if not self._check_spread(product):
            return "high_spread"

        # 5. KO-Abstand
        if not self._check_ko_distance(product):
            return "ko_too_close"

        # 6. Inactive Flag
        if ProductFlag.INACTIVE in product.flags:
            return "inactive"

        return None

    def _check_issuer(self, product: KnockoutProduct) -> bool:
        """Prüfe ob Issuer erlaubt ist."""
        if not self.config.issuers:
            return True

        # Prüfe nach ID wenn vorhanden
        if product.issuer_id is not None:
            allowed_ids = [i.value for i in self.config.issuers]
            return product.issuer_id in allowed_ids

        # Fallback: Nach Name prüfen
        allowed_names = [i.display_name.lower() for i in self.config.issuers]
        return product.issuer.lower() in allowed_names

    def _check_quote(self, product: KnockoutProduct) -> bool:
        """Prüfe Quote-Validität."""
        if not product.quote.is_valid:
            return False

        # Stale-Flag?
        if ProductFlag.STALE_QUOTE in product.flags:
            return False

        return True

    def _check_leverage(self, product: KnockoutProduct) -> bool:
        """Prüfe Mindesthebel."""
        if product.leverage is None:
            return False

        return product.leverage >= self.config.min_leverage

    def _check_spread(self, product: KnockoutProduct) -> bool:
        """Prüfe maximalen Spread."""
        spread = product.spread_pct
        if spread is None:
            return False

        return spread <= self.config.max_spread_pct

    def _check_ko_distance(self, product: KnockoutProduct) -> bool:
        """Prüfe KO-Abstand."""
        distance = product.ko_distance_pct
        if distance is None:
            # Kein Abstand berechenbar - überspringen
            # (Onvista liefert nicht immer den Underlying-Preis für Berechnung)
            return True

        # Negativ = KO bereits erreicht
        if distance <= 0:
            return False

        # Unter Mindestschwelle
        if distance < self.config.min_ko_distance_pct:
            return False

        return True


def apply_hard_filters(
    products: list[KnockoutProduct],
    config: KOFilterConfig,
) -> list[KnockoutProduct]:
    """
    Convenience-Funktion für Filter-Anwendung.

    Args:
        products: Zu filternde Produkte
        config: Filter-Konfiguration

    Returns:
        Gefilterte Produkte
    """
    filters = HardFilters(config)
    result = filters.apply(products)
    return result.passed
