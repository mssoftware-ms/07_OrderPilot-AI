"""UI Widgets Package for OrderPilot-AI Trading Application.

Phase 2 Integration (Regime + Levels):
- RegimeBadgeWidget: Kompaktes Regime-Badge für Toolbars
- RegimeInfoPanel: Erweitertes Panel mit ADX/DI Metriken
"""

# Phase 2.2 - Regime Display Widgets
from .regime_badge_widget import (
    RegimeBadgeWidget,
    RegimeInfoPanel,
    create_regime_badge,
    create_regime_info_panel,
    REGIME_STYLES,
)

__all__ = [
    # Phase 2.2: Regime Display
    "RegimeBadgeWidget",
    "RegimeInfoPanel",
    "create_regime_badge",
    "create_regime_info_panel",
    "REGIME_STYLES",
]
