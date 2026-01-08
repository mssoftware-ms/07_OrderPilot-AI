from __future__ import annotations


from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from PyQt6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QProgressBar, QSplitter, QTableWidget, QVBoxLayout, QWidget,
)


class SLTPProgressBar(QProgressBar):
    """Custom progress bar showing price position between SL and TP."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(50)
        self.setTextVisible(True)
        self.setMinimumHeight(28)
        self.setMaximumHeight(32)
        self._sl_price = 0.0
        self._tp_price = 0.0
        self._current_price = 0.0
        self._entry_price = 0.0
        self._side = "long"

    def set_prices(self, entry: float, sl: float, tp: float, current: float, side: str = "long"):
        """Update the bar with new prices."""
        self._entry_price = entry
        self._sl_price = sl
        self._tp_price = tp
        self._current_price = current
        self._side = side.lower()

        if sl <= 0 or tp <= 0 or sl == tp:
            self.setValue(50)
            self.setFormat("No SL/TP set")
            return

        # Calculate position as percentage (SL=0%, TP=100%)
        total_range = tp - sl
        if total_range != 0:
            position = ((current - sl) / total_range) * 100
            position = max(0, min(100, position))  # Clamp to 0-100
        else:
            position = 50

        self.setValue(int(position))

        # Format text
        pnl_pct = 0
        if entry > 0:
            if self._side == "long":
                pnl_pct = ((current - entry) / entry) * 100
            else:
                pnl_pct = ((entry - current) / entry) * 100

        sign = "+" if pnl_pct >= 0 else ""
        self.setFormat(f"SL: {sl:.2f} | Current: {current:.2f} ({sign}{pnl_pct:.2f}%) | TP: {tp:.2f}")
        self.update()

    def paintEvent(self, event):
        """Custom paint for gradient background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        rect.adjust(1, 1, -1, -1)

        # Background gradient: red (SL) -> orange (entry) -> green (TP)
        gradient = QLinearGradient(rect.left(), 0, rect.right(), 0)
        gradient.setColorAt(0.0, QColor("#ef5350"))   # Red (SL)
        gradient.setColorAt(0.5, QColor("#ff9800"))   # Orange (Entry)
        gradient.setColorAt(1.0, QColor("#26a69a"))   # Green (TP)

        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 4, 4)

        # Draw current position marker
        if self._sl_price > 0 and self._tp_price > 0 and self._tp_price != self._sl_price:
            total_range = self._tp_price - self._sl_price
            pos_ratio = (self._current_price - self._sl_price) / total_range
            pos_ratio = max(0, min(1, pos_ratio))

            marker_x = rect.left() + (rect.width() * pos_ratio)

            # Draw marker line
            painter.setPen(QColor("#ffffff"))
            painter.drawLine(int(marker_x), rect.top() + 2, int(marker_x), rect.bottom() - 2)

            # Draw marker triangle
            painter.setBrush(QColor("#ffffff"))
            triangle_size = 6
            points = [
                (int(marker_x), rect.top()),
                (int(marker_x - triangle_size), rect.top() - triangle_size),
                (int(marker_x + triangle_size), rect.top() - triangle_size),
            ]
            from PyQt6.QtGui import QPolygon
            from PyQt6.QtCore import QPoint
            polygon = QPolygon([QPoint(x, y) for x, y in points])
            painter.drawPolygon(polygon)

        # Draw text
        painter.setPen(QColor("#ffffff"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.format())

        painter.end()

    def reset_bar(self):
        """Reset bar to default state."""
        self._sl_price = 0.0
        self._tp_price = 0.0
        self._current_price = 0.0
        self._entry_price = 0.0
        self.setValue(50)
        self.setFormat("No active position")
        self.update()

class BotUISignalsMixin:
    """BotUISignalsMixin extracted from BotUIPanelsMixin."""
    def _create_signals_tab(self) -> QWidget:
        """Create signals & trade management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        splitter = QSplitter(Qt.Orientation.Vertical)

        splitter.addWidget(self._build_current_position_widget())
        splitter.addWidget(self._build_signals_widget())
        layout.addWidget(splitter)
        return widget

    def _build_current_position_widget(self) -> QWidget:
        position_widget = QWidget()
        position_layout = QVBoxLayout(position_widget)
        position_layout.setContentsMargins(0, 0, 0, 0)

        position_group = QGroupBox("Current Position")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(8, 8, 8, 8)
        group_layout.setSpacing(8)

        # Add SL/TP Progress Bar at the top
        self.sltp_progress_bar = SLTPProgressBar()
        self.sltp_progress_bar.reset_bar()
        group_layout.addWidget(self.sltp_progress_bar)

        # Add position details
        details_widget = QWidget()
        details_widget.setLayout(self._build_position_layout())
        group_layout.addWidget(details_widget)

        position_group.setLayout(group_layout)
        position_group.setMaximumHeight(220)
        position_layout.addWidget(position_group)
        return position_widget

    def _build_position_layout(self) -> QHBoxLayout:
        position_h_layout = QHBoxLayout()
        position_h_layout.setContentsMargins(8, 8, 8, 8)
        position_h_layout.setSpacing(20)

        position_h_layout.addWidget(self._build_position_left_column())
        position_h_layout.addWidget(self._build_position_right_column())
        position_h_layout.addStretch()
        return position_h_layout

    def _build_position_left_column(self) -> QWidget:
        left_widget = QWidget()
        left_widget.setMinimumWidth(180)
        left_widget.setMaximumWidth(220)
        left_form = QFormLayout(left_widget)
        left_form.setVerticalSpacing(2)
        left_form.setContentsMargins(0, 0, 0, 0)

        self.position_side_label = QLabel("FLAT")
        self.position_side_label.setStyleSheet("font-weight: bold;")
        left_form.addRow("Side:", self.position_side_label)

        self.position_strategy_label = QLabel("-")
        left_form.addRow("Strategy:", self.position_strategy_label)

        self.position_entry_label = QLabel("-")
        left_form.addRow("Entry:", self.position_entry_label)

        self.position_size_label = QLabel("-")
        left_form.addRow("Size:", self.position_size_label)

        self.position_invested_label = QLabel("-")
        self.position_invested_label.setStyleSheet("font-weight: bold;")
        left_form.addRow("Invested:", self.position_invested_label)

        self.position_stop_label = QLabel("-")
        left_form.addRow("Stop:", self.position_stop_label)

        self.position_current_label = QLabel("-")
        self.position_current_label.setStyleSheet("font-weight: bold;")
        left_form.addRow("Current:", self.position_current_label)

        self.position_pnl_label = QLabel("-")
        left_form.addRow("P&L:", self.position_pnl_label)

        self.position_bars_held_label = QLabel("-")
        left_form.addRow("Bars Held:", self.position_bars_held_label)
        return left_widget

    def _build_position_right_column(self) -> QWidget:
        right_widget = QWidget()
        right_widget.setMinimumWidth(160)
        right_form = QFormLayout(right_widget)
        right_form.setVerticalSpacing(2)
        right_form.setContentsMargins(0, 0, 0, 0)

        self.position_score_label = QLabel("-")
        self.position_score_label.setStyleSheet("font-weight: bold; color: #26a69a;")
        right_form.addRow("Score:", self.position_score_label)

        self.position_tr_price_label = QLabel("-")
        right_form.addRow("TR Kurs:", self.position_tr_price_label)

        self.deriv_separator = QLabel("── Derivat ──")
        self.deriv_separator.setStyleSheet("color: #ff5722; font-weight: bold;")
        right_form.addRow(self.deriv_separator)

        self.deriv_wkn_label = QLabel("-")
        self.deriv_wkn_label.setStyleSheet("font-weight: bold;")
        right_form.addRow("WKN:", self.deriv_wkn_label)

        self.deriv_leverage_label = QLabel("-")
        right_form.addRow("Hebel:", self.deriv_leverage_label)

        self.deriv_spread_label = QLabel("-")
        right_form.addRow("Spread:", self.deriv_spread_label)

        self.deriv_ask_label = QLabel("-")
        right_form.addRow("Ask:", self.deriv_ask_label)

        self.deriv_pnl_label = QLabel("-")
        self.deriv_pnl_label.setStyleSheet("font-weight: bold;")
        right_form.addRow("D P&L:", self.deriv_pnl_label)
        return right_widget

    def _build_signals_widget(self) -> QWidget:
        signals_widget = QWidget()
        signals_layout = QVBoxLayout(signals_widget)
        signals_layout.setContentsMargins(0, 0, 0, 0)

        signals_group = QGroupBox("Recent Signals")
        signals_inner = QVBoxLayout()
        self._build_signals_table()
        signals_inner.addWidget(self.signals_table)
        signals_group.setLayout(signals_inner)
        signals_layout.addWidget(signals_group)
        return signals_widget

    def _build_signals_table(self) -> None:
        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(19)
        self.signals_table.setHorizontalHeaderLabels(
            [
                "Time", "Type", "Side", "Entry", "Stop", "SL%", "TR%",
                "TRA%", "TR Lock", "Status", "Current", "P&L €", "P&L %",
                "D P&L €", "D P&L %", "Heb", "WKN", "Score", "TR Stop",
            ]
        )
        for col in [13, 14, 15, 16]:
            self.signals_table.setColumnHidden(col, True)
        self.signals_table.setColumnHidden(17, True)
        self.signals_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.signals_table.setAlternatingRowColors(True)
        self.signals_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.signals_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.signals_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.signals_table.customContextMenuRequested.connect(
            self._show_signals_context_menu
        )
        self.signals_table.cellChanged.connect(self._on_signals_table_cell_changed)
        self.signals_table.itemSelectionChanged.connect(
            self._on_signals_table_selection_changed
        )
        self._signals_table_updating = False
