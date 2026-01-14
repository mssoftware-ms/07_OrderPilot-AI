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
        # Find active position
        active_sig = None
        if hasattr(self, '_find_active_signal'):
            active_sig = self._find_active_signal()

        if not active_sig:
            QMessageBox.warning(
                self,
                "Keine offene Position",
                "Es gibt keine offene Position für Chart-Elemente.",
            )
            return

        # Get position details
        entry_price = active_sig.get("price", 0)
        stop_price = active_sig.get("stop_price", 0)
        trailing_price = active_sig.get("trailing_stop_price", 0)
        side = active_sig.get("side", "long")
        initial_sl_pct = active_sig.get("initial_sl_pct", 0)
        trailing_pct = active_sig.get("trailing_stop_pct", 0)
        trailing_activation_pct = active_sig.get("trailing_activation_pct", 0)
        current_price = active_sig.get("current_price", entry_price)

        if entry_price <= 0:
            QMessageBox.warning(
                self,
                "Keine Entry-Daten",
                "Entry-Preis ist nicht verfügbar.",
            )
            return

        # Check for chart widget
        if not hasattr(self, 'chart_widget') or not self.chart_widget:
            QMessageBox.warning(
                self,
                "Kein Chart",
                "Chart-Widget ist nicht verfügbar.",
            )
            return

        try:
            # Calculate percentages if not available
            if initial_sl_pct <= 0 and stop_price > 0 and entry_price > 0:
                initial_sl_pct = abs((stop_price - entry_price) / entry_price) * 100

            if trailing_pct <= 0 and trailing_price > 0 and entry_price > 0:
                if side == "long":
                    trailing_pct = abs((entry_price - trailing_price) / entry_price) * 100
                else:
                    trailing_pct = abs((trailing_price - entry_price) / entry_price) * 100

            # Calculate TRA% (distance from current price)
            tra_pct = 0
            if trailing_price > 0 and current_price > 0:
                tra_pct = abs((current_price - trailing_price) / current_price) * 100

            # Draw Entry Line (blue)
            entry_label = f"Entry @ {entry_price:.2f}"
            self.chart_widget.add_stop_line(
                line_id="entry_line",
                price=entry_price,
                line_type="initial",
                color="#2196f3",  # Blue
                label=entry_label
            )

            # Draw Stop-Loss Line (red) with percentage
            if stop_price > 0:
                sl_label = f"SL @ {stop_price:.2f} ({initial_sl_pct:.2f}%)"
                self.chart_widget.add_stop_line(
                    line_id="initial_stop",
                    price=stop_price,
                    line_type="initial",
                    color="#ef5350",  # Red
                    label=sl_label
                )

            # Draw Trailing-Stop Line (orange) with percentage
            if trailing_price > 0:
                tr_is_active = active_sig.get("tr_active", False)
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

            # Log action
            if hasattr(self, '_add_ki_log_entry'):
                lines_drawn = ["Entry"]
                if stop_price > 0:
                    lines_drawn.append(f"SL ({initial_sl_pct:.2f}%)")
                if trailing_price > 0:
                    lines_drawn.append(f"TR ({trailing_pct:.2f}%)")
                self._add_ki_log_entry("CHART", f"Elemente gezeichnet: {', '.join(lines_drawn)}")

            logger.info(
                f"Issue #18: Chart elements drawn - Entry: {entry_price:.2f}, "
                f"SL: {stop_price:.2f} ({initial_sl_pct:.2f}%), "
                f"TR: {trailing_price:.2f} ({trailing_pct:.2f}%)"
            )

        except Exception as e:
            logger.exception(f"Issue #18: Failed to draw chart elements: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Zeichnen der Chart-Elemente:\n{str(e)}",
            )

