"""Bot UI Control Handlers - Event Handler Module.

All event handlers for bot control UI widgets.
Extracted from BotUIControlMixin for Single Responsibility.

Module 2/4 of bot_ui_control_mixin.py split.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

logger = logging.getLogger(__name__)


class BotUIControlHandlers:
    """Event handlers for bot control UI interactions.

    Handles all UI events (clicks, value changes, state changes) and updates
    widget states accordingly.
    """

    def __init__(self, parent):
        """Initialize event handlers.

        Args:
            parent: Parent widget (typically BotUIControlMixin)
        """
        self.parent = parent

    def on_open_help_clicked(self) -> None:
        """Open the trading bot help documentation."""
        try:
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent.parent
            help_file = project_root / "Help" / "tradingbot-hilfe.html"

            if help_file.exists():
                url = QUrl.fromLocalFile(str(help_file))
                QDesktopServices.openUrl(url)
                logger.info(f"Opened help file: {help_file}")
            else:
                logger.warning(f"Help file not found: {help_file}")
        except Exception as e:
            logger.error(f"Failed to open help: {e}")

    def on_leverage_override_changed(self, state: int) -> None:
        """Handler für Leverage Override Checkbox."""
        enabled = state == Qt.CheckState.Checked.value
        self.parent.leverage_slider.setEnabled(enabled)

        if enabled:
            self.parent.leverage_value_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #FF9800; min-width: 50px;"
            )
            logger.info(f"Leverage Override aktiviert: {self.parent.leverage_slider.value()}x")
        else:
            self.parent.leverage_value_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #888; min-width: 50px;"
            )
            logger.info("Leverage Override deaktiviert - automatischer Hebel aktiv")

    def on_leverage_slider_changed(self, value: int) -> None:
        """Handler für Leverage Slider Wertänderung."""
        self.parent.leverage_value_label.setText(f"{value}x")

        # Farbcodierung nach Risiko
        if value <= 10:
            color = "#4CAF50"  # Grün - niedrig
        elif value <= 25:
            color = "#FF9800"  # Orange - mittel
        elif value <= 50:
            color = "#FF5722"  # Dunkel-Orange - hoch
        else:
            color = "#F44336"  # Rot - sehr hoch

        self.parent.leverage_value_label.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {color}; min-width: 50px;"
        )

        logger.debug(f"Leverage geändert auf {value}x")

    def on_trade_direction_changed(self, direction: str) -> None:
        """Handler für Trade Direction Änderung."""
        # Farbcodierung nach Richtung
        colors = {
            "AUTO": "#9E9E9E",      # Grau - automatisch
            "BOTH": "#2196F3",      # Blau - beide Richtungen
            "LONG_ONLY": "#4CAF50", # Grün - nur Long
            "SHORT_ONLY": "#F44336" # Rot - nur Short
        }
        color = colors.get(direction, "#9E9E9E")
        self.parent.trade_direction_combo.setStyleSheet(
            f"QComboBox {{ font-weight: bold; color: {color}; }}"
        )

        if direction == "AUTO":
            logger.info("Trade Direction: AUTO - wird durch Backtesting ermittelt")
        else:
            logger.info(f"Trade Direction manuell gesetzt: {direction}")
