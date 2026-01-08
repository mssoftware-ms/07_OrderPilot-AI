"""
Regime Badge Widget - Zeigt Markt-Regime als Badge an.

Ein wiederverwendbares PyQt6-Widget, das das aktuelle Markt-Regime
als farbcodiertes Badge darstellt.

Phase 2.2 der Bot-Integration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QFrame,
    QToolTip,
)
from PyQt6.QtGui import QFont, QCursor

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


# =============================================================================
# REGIME BADGE COLORS & ICONS
# =============================================================================

REGIME_STYLES = {
    "STRONG_TREND_BULL": {
        "icon": "🚀",
        "label": "Strong Trend ↑",
        "short": "BULL",
        "bg_color": "#1B5E20",  # Dark green
        "text_color": "#A5D6A7",  # Light green
        "border_color": "#4CAF50",  # Green
        "tooltip": "Starker Aufwärtstrend - Market Entries erlaubt",
    },
    "STRONG_TREND_BEAR": {
        "icon": "📉",
        "label": "Strong Trend ↓",
        "short": "BEAR",
        "bg_color": "#B71C1C",  # Dark red
        "text_color": "#FFCDD2",  # Light red
        "border_color": "#F44336",  # Red
        "tooltip": "Starker Abwärtstrend - Market Entries erlaubt",
    },
    "WEAK_TREND_BULL": {
        "icon": "📈",
        "label": "Weak Trend ↑",
        "short": "W-BULL",
        "bg_color": "#33691E",  # Dark olive
        "text_color": "#C5E1A5",  # Light lime
        "border_color": "#8BC34A",  # Lime
        "tooltip": "Schwacher Aufwärtstrend - Vorsicht geboten",
    },
    "WEAK_TREND_BEAR": {
        "icon": "📉",
        "label": "Weak Trend ↓",
        "short": "W-BEAR",
        "bg_color": "#880E4F",  # Dark pink
        "text_color": "#F8BBD0",  # Light pink
        "border_color": "#E91E63",  # Pink
        "tooltip": "Schwacher Abwärtstrend - Vorsicht geboten",
    },
    "CHOP_RANGE": {
        "icon": "📊",
        "label": "Choppy/Range",
        "short": "CHOP",
        "bg_color": "#E65100",  # Dark orange
        "text_color": "#FFCC80",  # Light orange
        "border_color": "#FF9800",  # Orange
        "tooltip": "Seitwärtsbewegung - KEINE Market Entries (nur Breakout/Retest)",
    },
    "VOLATILITY_EXPLOSIVE": {
        "icon": "💥",
        "label": "High Volatility",
        "short": "VOLATILE",
        "bg_color": "#4A148C",  # Dark purple
        "text_color": "#E1BEE7",  # Light purple
        "border_color": "#9C27B0",  # Purple
        "tooltip": "Hohe Volatilität - KEINE Market Entries (Vorsicht!)",
    },
    "NEUTRAL": {
        "icon": "⚖️",
        "label": "Neutral",
        "short": "NEUTRAL",
        "bg_color": "#37474F",  # Dark blue-grey
        "text_color": "#B0BEC5",  # Light blue-grey
        "border_color": "#607D8B",  # Blue-grey
        "tooltip": "Unklarer Markt - Abwarten empfohlen",
    },
    "UNKNOWN": {
        "icon": "❓",
        "label": "Unknown",
        "short": "N/A",
        "bg_color": "#424242",  # Dark grey
        "text_color": "#9E9E9E",  # Grey
        "border_color": "#757575",  # Medium grey
        "tooltip": "Regime nicht erkannt - Daten fehlen",
    },
}


# =============================================================================
# REGIME BADGE WIDGET
# =============================================================================


class RegimeBadgeWidget(QFrame):
    """
    Kompaktes Badge-Widget zur Anzeige des Markt-Regimes.

    Features:
    - Farbcodiertes Badge basierend auf Regime-Typ
    - Icon + Label oder nur Icon (compact mode)
    - Tooltip mit Details
    - Click-Signal für erweiterte Infos

    Usage:
        badge = RegimeBadgeWidget(compact=True)
        badge.set_regime("STRONG_TREND_BULL", adx=35.5, gate_reason="")
        layout.addWidget(badge)
    """

    # Signals
    clicked = pyqtSignal()  # Emitted when badge is clicked
    regime_changed = pyqtSignal(str)  # Emitted when regime changes

    def __init__(
        self,
        compact: bool = False,
        show_icon: bool = True,
        parent: QWidget | None = None,
    ):
        """
        Initialize the Regime Badge Widget.

        Args:
            compact: If True, show only icon and short label
            show_icon: If True, show emoji icon
            parent: Parent widget
        """
        super().__init__(parent)
        self._compact = compact
        self._show_icon = show_icon
        self._current_regime = "UNKNOWN"
        self._adx_value: float | None = None
        self._gate_reason: str = ""
        self._allows_entry: bool = False

        self._setup_ui()
        self._apply_regime_style("UNKNOWN")

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(4)

        # Icon label
        self._icon_label = QLabel()
        self._icon_label.setFont(QFont("Segoe UI Emoji", 12))
        if self._show_icon:
            layout.addWidget(self._icon_label)

        # Text label
        self._text_label = QLabel()
        self._text_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(self._text_label)

        # Entry indicator (small dot)
        self._entry_indicator = QLabel()
        self._entry_indicator.setFixedSize(8, 8)
        self._entry_indicator.setStyleSheet(
            "border-radius: 4px; background-color: #888;"
        )
        layout.addWidget(self._entry_indicator)

        # Set fixed height for consistency
        self.setFixedHeight(28)

    def set_regime(
        self,
        regime: str,
        adx: float | None = None,
        gate_reason: str = "",
        allows_entry: bool = True,
    ) -> None:
        """
        Update the displayed regime.

        Args:
            regime: Regime type (e.g., "STRONG_TREND_BULL")
            adx: Optional ADX value to display in tooltip
            gate_reason: Optional reason why entries are blocked
            allows_entry: Whether market entries are allowed
        """
        old_regime = self._current_regime
        self._current_regime = regime
        self._adx_value = adx
        self._gate_reason = gate_reason
        self._allows_entry = allows_entry

        self._apply_regime_style(regime)
        self._update_tooltip()
        self._update_entry_indicator()

        if old_regime != regime:
            self.regime_changed.emit(regime)
            logger.debug(f"Regime changed: {old_regime} -> {regime}")

    def set_regime_from_result(self, result) -> None:
        """
        Update from a RegimeResult object.

        Args:
            result: RegimeResult from RegimeDetectorService
        """
        if result is None:
            self.set_regime("UNKNOWN")
            return

        self.set_regime(
            regime=result.regime.value if hasattr(result.regime, 'value') else str(result.regime),
            adx=result.adx,
            gate_reason=result.gate_reason,
            allows_entry=result.allows_market_entry,
        )

    def get_regime(self) -> str:
        """Return current regime type."""
        return self._current_regime

    def _apply_regime_style(self, regime: str) -> None:
        """Apply visual style based on regime."""
        style = REGIME_STYLES.get(regime, REGIME_STYLES["UNKNOWN"])

        # Update icon
        self._icon_label.setText(style["icon"])

        # Update text
        text = style["short"] if self._compact else style["label"]
        self._text_label.setText(text)

        # Apply colors
        self.setStyleSheet(f"""
            RegimeBadgeWidget {{
                background-color: {style["bg_color"]};
                border: 2px solid {style["border_color"]};
                border-radius: 4px;
            }}
            QLabel {{
                color: {style["text_color"]};
                background: transparent;
                border: none;
            }}
        """)

    def _update_tooltip(self) -> None:
        """Update tooltip with detailed information."""
        style = REGIME_STYLES.get(self._current_regime, REGIME_STYLES["UNKNOWN"])

        tooltip_parts = [
            f"<b>{style['label']}</b>",
            f"<br>{style['tooltip']}",
        ]

        if self._adx_value is not None:
            tooltip_parts.append(f"<br><br>ADX: {self._adx_value:.1f}")

        if self._gate_reason:
            tooltip_parts.append(f"<br><br>⚠️ {self._gate_reason}")

        entry_status = "✅ Entry erlaubt" if self._allows_entry else "❌ Entry blockiert"
        tooltip_parts.append(f"<br><br>{entry_status}")

        self.setToolTip("".join(tooltip_parts))

    def _update_entry_indicator(self) -> None:
        """Update the entry indicator dot."""
        if self._allows_entry:
            self._entry_indicator.setStyleSheet(
                "border-radius: 4px; background-color: #4CAF50;"  # Green
            )
            self._entry_indicator.setToolTip("Market Entry erlaubt")
        else:
            self._entry_indicator.setStyleSheet(
                "border-radius: 4px; background-color: #F44336;"  # Red
            )
            self._entry_indicator.setToolTip("Market Entry blockiert")

    def mousePressEvent(self, event) -> None:
        """Handle mouse click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# =============================================================================
# REGIME INFO PANEL (Extended View)
# =============================================================================


class RegimeInfoPanel(QFrame):
    """
    Erweitertes Panel für Regime-Informationen.

    Zeigt detaillierte Regime-Daten inkl. ADX, DI+, DI-, ATR.

    Usage:
        panel = RegimeInfoPanel()
        panel.set_regime_result(result)
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            RegimeInfoPanel {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 6px;
            }
            QLabel {
                color: #ccc;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(16)

        # Regime Badge (compact)
        self._badge = RegimeBadgeWidget(compact=False, show_icon=True)
        layout.addWidget(self._badge)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #444;")
        layout.addWidget(sep)

        # Metrics
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)

        # ADX
        adx_layout = QHBoxLayout()
        adx_layout.setSpacing(4)
        self._adx_label = QLabel("ADX:")
        self._adx_label.setStyleSheet("color: #888; font-size: 10px;")
        self._adx_value = QLabel("--")
        self._adx_value.setStyleSheet("color: #fff; font-weight: bold;")
        adx_layout.addWidget(self._adx_label)
        adx_layout.addWidget(self._adx_value)
        metrics_layout.addLayout(adx_layout)

        # DI+
        dip_layout = QHBoxLayout()
        dip_layout.setSpacing(4)
        self._dip_label = QLabel("DI+:")
        self._dip_label.setStyleSheet("color: #888; font-size: 10px;")
        self._dip_value = QLabel("--")
        self._dip_value.setStyleSheet("color: #4CAF50; font-weight: bold;")
        dip_layout.addWidget(self._dip_label)
        dip_layout.addWidget(self._dip_value)
        metrics_layout.addLayout(dip_layout)

        # DI-
        dim_layout = QHBoxLayout()
        dim_layout.setSpacing(4)
        self._dim_label = QLabel("DI-:")
        self._dim_label.setStyleSheet("color: #888; font-size: 10px;")
        self._dim_value = QLabel("--")
        self._dim_value.setStyleSheet("color: #F44336; font-weight: bold;")
        dim_layout.addWidget(self._dim_label)
        dim_layout.addWidget(self._dim_value)
        metrics_layout.addLayout(dim_layout)

        # ATR
        atr_layout = QHBoxLayout()
        atr_layout.setSpacing(4)
        self._atr_label = QLabel("ATR:")
        self._atr_label.setStyleSheet("color: #888; font-size: 10px;")
        self._atr_value = QLabel("--")
        self._atr_value.setStyleSheet("color: #FF9800; font-weight: bold;")
        atr_layout.addWidget(self._atr_label)
        atr_layout.addWidget(self._atr_value)
        metrics_layout.addLayout(atr_layout)

        layout.addLayout(metrics_layout)
        layout.addStretch()

        # Gate Status
        self._gate_label = QLabel("")
        self._gate_label.setStyleSheet("color: #F44336; font-size: 10px;")
        layout.addWidget(self._gate_label)

    def set_regime_result(self, result) -> None:
        """
        Update panel from RegimeResult.

        Args:
            result: RegimeResult from RegimeDetectorService
        """
        if result is None:
            self._badge.set_regime("UNKNOWN")
            self._adx_value.setText("--")
            self._dip_value.setText("--")
            self._dim_value.setText("--")
            self._atr_value.setText("--")
            self._gate_label.setText("")
            return

        # Update badge
        self._badge.set_regime_from_result(result)

        # Update metrics
        self._adx_value.setText(f"{result.adx:.1f}" if result.adx else "--")
        self._dip_value.setText(f"{result.di_plus:.1f}" if result.di_plus else "--")
        self._dim_value.setText(f"{result.di_minus:.1f}" if result.di_minus else "--")
        self._atr_value.setText(f"{result.atr:.4f}" if result.atr else "--")

        # Color ADX based on strength
        if result.adx:
            if result.adx >= 25:
                self._adx_value.setStyleSheet("color: #4CAF50; font-weight: bold;")
            elif result.adx >= 20:
                self._adx_value.setStyleSheet("color: #FF9800; font-weight: bold;")
            else:
                self._adx_value.setStyleSheet("color: #F44336; font-weight: bold;")

        # Update gate status
        if not result.allows_market_entry and result.gate_reason:
            self._gate_label.setText(f"⚠️ {result.gate_reason}")
        else:
            self._gate_label.setText("")

    def set_regime_from_data(
        self,
        regime: str,
        adx: float | None = None,
        di_plus: float | None = None,
        di_minus: float | None = None,
        atr: float | None = None,
        allows_entry: bool = True,
        gate_reason: str = "",
    ) -> None:
        """
        Update panel from individual values.

        Args:
            regime: Regime type string
            adx: ADX value
            di_plus: DI+ value
            di_minus: DI- value
            atr: ATR value
            allows_entry: Whether entries are allowed
            gate_reason: Reason for blocking entries
        """
        self._badge.set_regime(regime, adx, gate_reason, allows_entry)
        self._adx_value.setText(f"{adx:.1f}" if adx else "--")
        self._dip_value.setText(f"{di_plus:.1f}" if di_plus else "--")
        self._dim_value.setText(f"{di_minus:.1f}" if di_minus else "--")
        self._atr_value.setText(f"{atr:.4f}" if atr else "--")

        if not allows_entry and gate_reason:
            self._gate_label.setText(f"⚠️ {gate_reason}")
        else:
            self._gate_label.setText("")


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_regime_badge(
    compact: bool = True,
    show_icon: bool = True,
) -> RegimeBadgeWidget:
    """
    Factory function to create a RegimeBadgeWidget.

    Args:
        compact: Use compact mode (short labels)
        show_icon: Show emoji icon

    Returns:
        RegimeBadgeWidget instance
    """
    return RegimeBadgeWidget(compact=compact, show_icon=show_icon)


def create_regime_info_panel() -> RegimeInfoPanel:
    """
    Factory function to create a RegimeInfoPanel.

    Returns:
        RegimeInfoPanel instance
    """
    return RegimeInfoPanel()
