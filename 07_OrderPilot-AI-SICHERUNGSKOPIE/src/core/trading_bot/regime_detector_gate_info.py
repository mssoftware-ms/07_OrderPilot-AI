"""
Regime Detector Gate Info - Gate Information Logic.

Refactored from regime_detector.py.

Contains:
- get_regime_gate_info: Provides detailed gate information for UI
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .regime_detector import RegimeDetectorService
    from .regime_result import RegimeResult


class RegimeDetectorGateInfo:
    """Helper for gate information."""

    def __init__(self, parent: RegimeDetectorService):
        self.parent = parent

    def get_regime_gate_info(self, result: RegimeResult) -> dict:
        """
        Gibt detaillierte Gate-Info für UI zurück.

        Returns dict mit:
        - allowed: bool
        - reason: str | None
        - allowed_entry_types: list[str]
        """
        from .regime_types import RegimeType

        if result.regime == RegimeType.CHOP_RANGE:
            return {
                "allowed": False,
                "reason": "CHOP_RANGE: Market-Entries blockiert",
                "allowed_entry_types": ["BREAKOUT", "RETEST", "SFP_RECLAIM"],
                "recommendation": "Warte auf Breakout oder Mean-Reversion Setup",
            }
        elif result.regime == RegimeType.NEUTRAL:
            return {
                "allowed": False,
                "reason": "NEUTRAL: Regime unklar",
                "allowed_entry_types": [],
                "recommendation": "Kein Entry, warte auf klares Signal",
            }
        elif result.regime == RegimeType.VOLATILITY_EXPLOSIVE:
            return {
                "allowed": True,
                "reason": "VOLATILITY_EXPLOSIVE: Erhöhte Vorsicht",
                "allowed_entry_types": ["ALL"],
                "recommendation": "Reduziere Position Size, engere Stops",
            }
        else:
            return {
                "allowed": True,
                "reason": None,
                "allowed_entry_types": ["ALL"],
                "recommendation": f"Trend {result.regime.value} - Entry erlaubt",
            }
