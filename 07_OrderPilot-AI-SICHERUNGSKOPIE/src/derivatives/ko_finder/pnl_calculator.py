"""
P&L Berechnung für KO-Produkte.

Formeln:
LONG:  r_net = (1 + L*u) * g - 1
SHORT: r_net = (1 - L*u) * g - 1

Wobei:
- L = Hebel
- s = Spread (dezimal, z.B. 0.0027 für 0.27%)
- h = s/2 (Halbspread)
- g = (1-h)/(1+h) (Ask→Bid Faktor)
- u = (U1-U0)/U0 (Underlying Return)
- K = Kapital
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    """Handelsrichtung."""

    LONG = "long"
    SHORT = "short"


@dataclass
class DerivativePnL:
    """Ergebnis der Derivat-P&L-Berechnung."""

    r_net: float  # Netto-Rendite (dezimal)
    pnl_eur: float  # P&L in EUR
    pnl_pct: float  # P&L in % (= r_net * 100)
    v1: float  # Positionswert beim Exit
    p_bid1: float  # Geschätzter Bid beim Exit


def calculate_derivative_pnl(
    direction: Direction,
    leverage: float,  # L: Hebel
    spread_pct: float,  # s: Spread in % (z.B. 0.27)
    u0: float,  # U0: Underlying beim Einstieg
    u1: float,  # U1: Underlying beim Exit
    capital: float,  # K: Eingesetztes Kapital
    ask_entry: float,  # P_ask0: Derivat-Ask beim Einstieg
) -> DerivativePnL:
    """
    Berechne Derivat-P&L.

    Formeln:
    - h = s/2 (Halbspread)
    - u = (U1-U0)/U0 (Underlying Return)
    - g = (1-h)/(1+h) (Ask→Bid Faktor für Spread)

    LONG:  r_net = (1 + L*u) * g - 1
    SHORT: r_net = (1 - L*u) * g - 1

    PnL = K * r_net
    V1 = K * (1 + r_net)

    Args:
        direction: LONG oder SHORT
        leverage: Hebel (z.B. 6.5)
        spread_pct: Spread in Prozent (z.B. 0.27 für 0.27%)
        u0: Underlying-Kurs beim Einstieg
        u1: Underlying-Kurs aktuell/beim Exit
        capital: Eingesetztes Kapital in EUR
        ask_entry: Derivat-Ask-Kurs beim Einstieg

    Returns:
        DerivativePnL mit allen berechneten Werten
    """
    # Validierung
    if u0 <= 0:
        return DerivativePnL(
            r_net=0.0, pnl_eur=0.0, pnl_pct=0.0, v1=capital, p_bid1=ask_entry
        )

    # Spread als Dezimalzahl
    s = spread_pct / 100.0

    # Hilfswerte
    h = s / 2  # Halbspread
    u = (u1 - u0) / u0  # Underlying Return
    g = (1 - h) / (1 + h)  # Ask→Bid Faktor

    # Netto-Rendite je nach Richtung
    if direction == Direction.LONG:
        r_net = (1 + leverage * u) * g - 1
        p_bid1 = ask_entry * (1 + leverage * u) * g
    else:  # SHORT
        r_net = (1 - leverage * u) * g - 1
        p_bid1 = ask_entry * (1 - leverage * u) * g

    # P&L
    pnl_eur = capital * r_net
    pnl_pct = r_net * 100
    v1 = capital * (1 + r_net)

    return DerivativePnL(
        r_net=r_net,
        pnl_eur=pnl_eur,
        pnl_pct=pnl_pct,
        v1=v1,
        p_bid1=max(0.0, p_bid1),  # Bid kann nicht negativ sein
    )
