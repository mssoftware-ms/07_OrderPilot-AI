from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from PyQt6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QProgressBar, QPushButton, QSplitter, QTableWidget, QVBoxLayout, QWidget,
    QMessageBox, QPlainTextEdit, QFileDialog
)

from .bot_sltp_progressbar import SLTPProgressBar

logger = logging.getLogger(__name__)

class BotUISignalsChartMixin:
    """Chart element drawing"""

    def _on_draw_chart_elements_clicked(self) -> None:
        """Issue #18: Draw chart elements (Entry, SL, TR) for active position.

        Zeichnet Entry-Linie, Stop-Loss und Trailing-Stop Linien im Chart.
        Labels zeigen die Werte in Prozent an.
        Linien können im Chart verschoben werden - Werte in Signals werden automatisch aktualisiert.
        """
        # Validate preconditions
        active_sig = self._validate_and_get_active_signal()
        if not active_sig:
            return

        position_data = self._extract_position_data(active_sig)
        if not self._validate_position_data(position_data):
            return

        try:
            # Calculate missing percentages
            position_data = self._calculate_percentages(position_data)

            # Draw all chart lines
            self._draw_chart_lines(position_data)

            # Log success
            self._log_chart_elements_drawn(position_data)

        except Exception as e:
            logger.exception(f"Issue #18: Failed to draw chart elements: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Zeichnen der Chart-Elemente:\n{str(e)}",
            )

    def _validate_and_get_active_signal(self) -> dict | None:
        """Validate and retrieve active signal.

        Returns:
            Active signal dict or None if not found/invalid.
        """
        if not hasattr(self, '_find_active_signal'):
            return None

        active_sig = self._find_active_signal()
        if not active_sig:
            QMessageBox.warning(
                self,
                "Keine offene Position",
                "Es gibt keine offene Position für Chart-Elemente.",
            )
            return None

        return active_sig

    def _extract_position_data(self, active_sig: dict) -> dict:
        """Extract position data from active signal.

        Args:
            active_sig: Active signal dictionary.

        Returns:
            Dictionary with position data.
        """
        entry_price = active_sig.get("price", 0)
        return {
            "entry_price": entry_price,
            "stop_price": active_sig.get("stop_price", 0),
            "trailing_price": active_sig.get("trailing_stop_price", 0),
            "side": active_sig.get("side", "long"),
            "initial_sl_pct": active_sig.get("initial_sl_pct", 0),
            "trailing_pct": active_sig.get("trailing_stop_pct", 0),
            "trailing_activation_pct": active_sig.get("trailing_activation_pct", 0),
            "current_price": active_sig.get("current_price", entry_price),
            "tr_is_active": active_sig.get("tr_active", False),
        }

    def _validate_position_data(self, position_data: dict) -> bool:
        """Validate position data and chart widget.

        Args:
            position_data: Position data dictionary.

        Returns:
            True if valid, False otherwise (shows warning).
        """
        if position_data["entry_price"] <= 0:
            QMessageBox.warning(
                self,
                "Keine Entry-Daten",
                "Entry-Preis ist nicht verfügbar.",
            )
            return False

        if not hasattr(self, 'chart_widget') or not self.chart_widget:
            QMessageBox.warning(
                self,
                "Kein Chart",
                "Chart-Widget ist nicht verfügbar.",
            )
            return False

        return True

    def _calculate_percentages(self, position_data: dict) -> dict:
        """Calculate missing percentage values.

        Args:
            position_data: Position data dictionary.

        Returns:
            Updated position data with calculated percentages.
        """
        entry_price = position_data["entry_price"]
        stop_price = position_data["stop_price"]
        trailing_price = position_data["trailing_price"]
        current_price = position_data["current_price"]
        side = position_data["side"]

        # Calculate initial SL percentage if missing
        if position_data["initial_sl_pct"] <= 0 and stop_price > 0 and entry_price > 0:
            position_data["initial_sl_pct"] = abs((stop_price - entry_price) / entry_price) * 100

        # Calculate trailing percentage if missing
        if position_data["trailing_pct"] <= 0 and trailing_price > 0 and entry_price > 0:
            if side == "long":
                position_data["trailing_pct"] = abs((entry_price - trailing_price) / entry_price) * 100
            else:
                position_data["trailing_pct"] = abs((trailing_price - entry_price) / entry_price) * 100

        # Calculate TRA% (distance from current price)
        position_data["tra_pct"] = 0
        if trailing_price > 0 and current_price > 0:
            position_data["tra_pct"] = abs((current_price - trailing_price) / current_price) * 100

        return position_data

    def _draw_chart_lines(self, position_data: dict) -> None:
        """Draw all chart lines (Entry, SL, TR).

        Args:
            position_data: Position data with calculated values.
        """
        # Draw Entry Line (blue)
        self.chart_widget.add_stop_line(
            line_id="entry_line",
            price=position_data["entry_price"],
            line_type="initial",
            color="#2196f3",
            label=f"Entry @ {position_data['entry_price']:.2f}"
        )

        # Draw Stop-Loss Line (red)
        if position_data["stop_price"] > 0:
            sl_label = f"SL @ {position_data['stop_price']:.2f} ({position_data['initial_sl_pct']:.2f}%)"
            self.chart_widget.add_stop_line(
                line_id="initial_stop",
                price=position_data["stop_price"],
                line_type="initial",
                color="#ef5350",
                label=sl_label
            )

        # Draw Trailing-Stop Line (orange/gray)
        if position_data["trailing_price"] > 0:
            self._draw_trailing_line(position_data)

    def _draw_trailing_line(self, position_data: dict) -> None:
        """Draw trailing stop line with active/inactive styling.

        Args:
            position_data: Position data dictionary.
        """
        trailing_price = position_data["trailing_price"]
        trailing_pct = position_data["trailing_pct"]
        tra_pct = position_data["tra_pct"]
        tr_is_active = position_data["tr_is_active"]

        if tr_is_active:
            tr_label = f"TSL @ {trailing_price:.2f} ({trailing_pct:.2f}% / TRA: {tra_pct:.2f}%)"
            color = "#ff9800"  # Orange when active
        else:
            tr_label = f"TSL @ {trailing_price:.2f} ({trailing_pct:.2f}%) [inaktiv]"
            color = "#888888"  # Gray when inactive

        self.chart_widget.add_stop_line(
            line_id="trailing_stop",
            price=trailing_price,
            line_type="trailing",
            color=color,
            label=tr_label
        )

    def _log_chart_elements_drawn(self, position_data: dict) -> None:
        """Log successful chart element drawing.

        Args:
            position_data: Position data dictionary.
        """
        # KI Log
        if hasattr(self, '_add_ki_log_entry'):
            lines_drawn = ["Entry"]
            if position_data["stop_price"] > 0:
                lines_drawn.append(f"SL ({position_data['initial_sl_pct']:.2f}%)")
            if position_data["trailing_price"] > 0:
                lines_drawn.append(f"TR ({position_data['trailing_pct']:.2f}%)")
            self._add_ki_log_entry("CHART", f"Elemente gezeichnet: {', '.join(lines_drawn)}")

        # Python logger
        logger.info(
            f"Issue #18: Chart elements drawn - Entry: {position_data['entry_price']:.2f}, "
            f"SL: {position_data['stop_price']:.2f} ({position_data['initial_sl_pct']:.2f}%), "
            f"TR: {position_data['trailing_price']:.2f} ({position_data['trailing_pct']:.2f}%)"
        )

