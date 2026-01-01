"""
Ranking Engine für KO-Produkte.

Implementiert das KO-Score-System basierend auf:
- Gate-Prüfung (KO muss hinter Stop + Gap liegen)
- Spread-Effizienz (Underlying-Equivalent-Spread)
- Hebel-Score (logarithmisch saturiert)
- KO-Safety-Score (Margin hinter Stop)
- Expected Value (EV) Berechnung

Siehe: 01_Projectplan/KO_Scoring_System.md
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..constants import Direction
from ..models import KnockoutProduct, ProductFlag

if TYPE_CHECKING:
    from ..config import KOFilterConfig

logger = logging.getLogger(__name__)


@dataclass
class ScoringParams:
    """Parameter für das KO-Scoring-System."""

    # Trading-Plan (anpassbar je nach Strategie)
    dsl: float = 0.01  # Stop-Loss: -1%
    dtp: float = 0.02  # Take-Profit: +2%
    dgap: float = 0.005  # Gap-Puffer: 0.5% (KO muss mindestens dsl + dgap unter Kurs)

    # Score-Parameter
    ues0: float = 0.0005  # Spread-Referenz für S_spread
    L_cap: float = 10.0  # Hebel-Sättigung
    m_good: float = 0.005  # 0.5% extra hinter Stop für volle KO-Safety
    EV_ref: float = -0.01  # EV-Referenz für S_ev

    # Optimaler KO-Abstand (Band, linearer Abfall außerhalb)
    ko_optimal_min: float = 0.05
    ko_optimal_max: float = 0.15
    ko_far_max: float = 0.30

    # Gewichte (müssen 1.0 ergeben)
    w_spread: float = 0.45
    w_lev: float = 0.30
    w_ko: float = 0.20
    w_ev: float = 0.05


@dataclass
class ScoreBreakdown:
    """Detaillierte Aufschlüsselung des Scores."""

    total: float = 0.0
    gate_passed: bool = False

    # Teil-Scores (0-1)
    s_spread: float = 0.0
    s_lev: float = 0.0
    s_ko: float = 0.0
    s_ev: float = 0.0

    # Berechnete Werte
    dko: float = 0.0  # KO-Abstand in %
    margin: float = 0.0  # Margin hinter Stop
    spread_pct: float = 0.0
    ues: float = 0.0  # Underlying-Equivalent-Spread
    ev: float = 0.0  # Expected Value


class RankingEngine:
    """
    Ranking Engine für KO-Produkte.

    Implementiert das vollständige Scoring-System aus
    01_Projectplan/KO_Scoring_System.md
    """

    def __init__(
        self,
        config: KOFilterConfig,
        params: ScoringParams | None = None,
        underlying_price: float | None = None,
    ) -> None:
        """
        Initialisiere Ranking Engine.

        Args:
            config: Filter-Konfiguration
            params: Optional: Custom Scoring-Parameter
            underlying_price: Aktueller Underlying-Kurs (für KO-Abstand)
        """
        self.config = config
        self.params = params or ScoringParams()
        self.underlying_price = underlying_price

    def rank(
        self,
        products: list[KnockoutProduct],
        top_n: int | None = None,
    ) -> list[KnockoutProduct]:
        """
        Ranke Produkte nach Score (absteigend).

        Args:
            products: Zu rankende Produkte
            top_n: Optional: Nur Top-N zurückgeben

        Returns:
            Sortierte Produktliste
        """
        # Scores berechnen
        for product in products:
            breakdown = self._calculate_breakdown(product)
            product.score = breakdown.total

        # Sortieren: Score desc, dann Spread asc als Tie-Break
        sorted_products = sorted(
            products,
            key=lambda p: (
                -(p.score or 0),  # Score desc
                p.spread_pct or float("inf"),  # Spread asc
                -(p.leverage or 0),  # Leverage desc
            ),
        )

        # Top-N beschränken
        if top_n is not None:
            sorted_products = sorted_products[:top_n]

        return sorted_products

    def calculate_score(self, product: KnockoutProduct) -> float:
        """
        Berechne Score für einzelnes Produkt.

        Args:
            product: Zu bewertendes Produkt

        Returns:
            Score (0-100, höher = besser)
        """
        breakdown = self._calculate_breakdown(product)
        return breakdown.total

    def _calculate_breakdown(self, product: KnockoutProduct) -> ScoreBreakdown:
        """Berechne detaillierte Score-Aufschlüsselung."""
        breakdown = ScoreBreakdown()
        p = self.params

        # 1. KO-Abstand berechnen
        dko = self._calculate_ko_distance(product)
        breakdown.dko = dko * 100 if dko else 0  # In Prozent für Anzeige

        if dko is None:
            # Kein KO-Abstand berechenbar
            logger.debug(f"No KO distance for {product.wkn}")
            return breakdown

        # 2. Gate-Prüfung: KO muss UNTERHALB des Stop-Loss liegen
        # Bei LONG mit SL=-1% und Gap=0.5%: KO muss mindestens 1.5% unter Kurs liegen
        # Beispiel: Kurs=100€, SL bei 99€ (-1%), KO muss bei <=98.50€ liegen (-1.5%)
        gate_threshold = p.dsl + p.dgap
        if dko < gate_threshold:
            # Gate fail → Score = 0 (KO zu nah am Stop-Loss)
            logger.debug(
                f"Gate fail for {product.wkn}: KO-Abstand {dko*100:.2f}% < "
                f"benötigt {gate_threshold*100:.2f}% (SL {p.dsl*100:.1f}% + Gap {p.dgap*100:.1f}%)"
            )
            return breakdown

        breakdown.gate_passed = True

        # 3. Margin hinter Stop
        margin = dko - p.dsl
        breakdown.margin = margin * 100  # In Prozent

        # 4. Spread aus Bid/Ask
        spread, half_spread = self._calculate_spread(product)
        breakdown.spread_pct = spread * 100 if spread else 0

        if spread is None or product.leverage is None:
            # Fehlende Daten
            return breakdown

        # 5. Underlying-Equivalent-Spread
        ues = spread / product.leverage
        breakdown.ues = ues * 100  # In Prozent

        # 6. EV berechnen
        ev = self._calculate_ev(product.leverage, half_spread)
        breakdown.ev = ev * 100  # In Prozent

        # 7. Teil-Scores berechnen (alle 0-1)

        # S_spread: Spread-Effizienz
        breakdown.s_spread = 1 / (1 + (ues / p.ues0) ** 2)

        # S_lev: Hebel-Score (logarithmisch saturiert)
        breakdown.s_lev = math.log(1 + product.leverage) / math.log(1 + p.L_cap)
        breakdown.s_lev = min(1.0, breakdown.s_lev)  # Cap bei 1.0

        # S_ko: KO-Distanz-Score (optimaler Abstand im Band)
        breakdown.s_ko = self._calculate_ko_score(dko)

        # S_ev: EV-Score
        breakdown.s_ev = self._clamp(1 + ev / abs(p.EV_ref), 0, 1)

        # 8. Final Score (0-100)
        breakdown.total = 100 * (
            p.w_spread * breakdown.s_spread
            + p.w_lev * breakdown.s_lev
            + p.w_ko * breakdown.s_ko
            + p.w_ev * breakdown.s_ev
        )

        # Quality-Penalty für Flags
        quality_penalty = self._calculate_quality_penalty(product)
        breakdown.total = max(0.0, breakdown.total - quality_penalty)

        return breakdown

    def _calculate_ko_distance(self, product: KnockoutProduct) -> float | None:
        """
        Berechne KO-Abstand als Dezimalzahl.

        Returns:
            KO-Abstand (z.B. 0.05 für 5%) oder None
        """
        if product.knockout_level is None:
            return None

        # Underlying-Preis: Erst aus Produkt, dann aus Engine
        u0 = None
        if product.underlying and product.underlying.price:
            u0 = product.underlying.price
        elif self.underlying_price:
            u0 = self.underlying_price

        if not u0 or u0 <= 0:
            # Fallback: aus ko_distance_pct wenn vorhanden
            if product.ko_distance_pct is not None:
                return product.ko_distance_pct / 100
            return None

        ko = product.knockout_level

        if product.direction == Direction.LONG:
            # LONG: KO unter Kurs
            return (u0 - ko) / u0
        else:
            # SHORT: KO über Kurs
            return (ko - u0) / u0

    def _calculate_ko_score(self, dko: float) -> float:
        """Score KO-Distanz: optimal im Band, linearer Abfall außerhalb."""
        p = self.params
        if dko <= p.ko_optimal_min:
            return self._clamp(dko / p.ko_optimal_min, 0, 1)
        if dko >= p.ko_optimal_max:
            if dko >= p.ko_far_max:
                return 0.0
            return self._clamp(
                1 - (dko - p.ko_optimal_max) / (p.ko_far_max - p.ko_optimal_max),
                0,
                1,
            )
        return 1.0

    def _calculate_spread(
        self, product: KnockoutProduct
    ) -> tuple[float | None, float | None]:
        """
        Berechne Spread und Half-Spread.

        Returns:
            (spread, half_spread) als Dezimalzahlen oder (None, None)
        """
        bid = product.quote.bid
        ask = product.quote.ask

        if bid and ask and bid > 0 and ask > 0:
            mid = (bid + ask) / 2
            spread = (ask - bid) / mid
            return spread, spread / 2

        # Fallback: spread_pct aus Produkt
        if product.spread_pct is not None:
            spread = product.spread_pct / 100
            return spread, spread / 2

        return None, None

    def _calculate_ev(self, leverage: float, half_spread: float) -> float:
        """
        Berechne Expected Value.

        Args:
            leverage: Hebel
            half_spread: Halber Spread (für Entry/Exit Kosten)

        Returns:
            EV als Dezimalzahl
        """
        p = self.params
        h = half_spread

        # Brutto-Renditen
        r_tp_gross = leverage * p.dtp
        r_sl_gross = -leverage * p.dsl

        # Netto-Renditen (Entry Ask, Exit Bid)
        # f(x) = ((1 + x) * (1 - h) / (1 + h)) - 1
        def net_return(r_gross: float) -> float:
            return ((1 + r_gross) * (1 - h) / (1 + h)) - 1

        r_tp = net_return(r_tp_gross)
        r_sl = net_return(r_sl_gross)

        # Treffer-Wahrscheinlichkeit (driftlos)
        p_tp = p.dsl / (p.dsl + p.dtp)
        p_sl = 1 - p_tp

        # Expected Value
        return p_tp * r_tp + p_sl * r_sl

    def _calculate_quality_penalty(self, product: KnockoutProduct) -> float:
        """Berechne Penalty basierend auf Qualitäts-Flags."""
        penalty = 0.0

        if ProductFlag.PARSING_UNCERTAIN in product.flags:
            penalty += 3.0

        if ProductFlag.LOW_CONFIDENCE in product.flags:
            penalty += 5.0

        if ProductFlag.KO_NEAR in product.flags:
            penalty += 5.0

        if ProductFlag.MISSING_FIELDS in product.flags:
            penalty += 2.0

        # Parser-Confidence einbeziehen
        if product.parser_confidence < 1.0:
            confidence_penalty = (1.0 - product.parser_confidence) * 5
            penalty += confidence_penalty

        return penalty

    @staticmethod
    def _clamp(x: float, min_val: float, max_val: float) -> float:
        """Clamp x zwischen min und max."""
        return max(min_val, min(max_val, x))


def rank_products(
    products: list[KnockoutProduct],
    config: KOFilterConfig,
    top_n: int | None = None,
    underlying_price: float | None = None,
) -> list[KnockoutProduct]:
    """
    Convenience-Funktion für Ranking.

    Args:
        products: Zu rankende Produkte
        config: Filter-Konfiguration
        top_n: Optional: Nur Top-N
        underlying_price: Aktueller Underlying-Kurs

    Returns:
        Sortierte Produktliste
    """
    engine = RankingEngine(config, underlying_price=underlying_price)
    return engine.rank(products, top_n)
