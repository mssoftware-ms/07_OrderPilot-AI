"""Watchlist UI Builder - UI Construction.

Refactored from watchlist.py.

Contains:
- _build_market_status_label
- _build_input_row
- _build_table
- _configure_table
- _build_quick_add_row
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
)

if TYPE_CHECKING:
    from .watchlist import WatchlistWidget


class WatchlistUIBuilder:
    """Helper for UI construction."""

    def __init__(self, parent: WatchlistWidget):
        self.parent = parent

    def build_market_status_label(self) -> QLabel:
        """Build market status label."""
        self.parent.market_status_label = QLabel("Market: Checking...")
        self.parent.market_status_label.setStyleSheet(
            "background-color: #2A2D33; color: #EAECEF; padding: 5px; "
            "border-radius: 3px; font-weight: bold;"
        )
        return self.parent.market_status_label

    def build_input_row(self) -> QHBoxLayout:
        """Build symbol input row."""
        input_layout = QHBoxLayout()

        self.parent.symbol_input = QLineEdit()
        self.parent.symbol_input.setPlaceholderText(
            "Enter symbol (e.g., AAPL for stocks, BTC/USD for crypto)"
        )
        self.parent.symbol_input.returnPressed.connect(self.parent.add_symbol_from_input)
        input_layout.addWidget(self.parent.symbol_input)

        add_button = QPushButton("+")
        add_button.setMaximumWidth(40)
        add_button.clicked.connect(self.parent.add_symbol_from_input)
        add_button.setToolTip("Add symbol to watchlist")
        input_layout.addWidget(add_button)
        return input_layout

    def build_table(self) -> QTableWidget:
        """Build main table widget."""
        self.parent.table = QTableWidget()
        self.parent.table.setColumnCount(7)
        self.parent.table.setHorizontalHeaderLabels(
            ["Symbol", "Name", "WKN", "Price", "Change", "Change %", "Volume"]
        )

        self.configure_table()
        return self.parent.table

    def configure_table(self) -> None:
        """Configure table properties and styling."""
        table = self.parent.table

        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)

        table.setStyleSheet(
            """
            QTableWidget {
                alternate-background-color: #2d2d2d;
                background-color: #1e1e1e;
                color: #ffffff;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                color: #ffffff;
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #FF8C00;
                color: #ffffff;
            }
        """
        )

        header = table.horizontalHeader()
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        table.setColumnWidth(0, 80)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 80)
        table.setColumnWidth(3, 100)
        table.setColumnWidth(4, 80)
        table.setColumnWidth(5, 80)
        table.setColumnWidth(6, 100)

        # HIDE columns by default (User Request: "Price, Change, Volume can go")
        # Keep Symbol (0), Name (1), WKN (2)
        table.setColumnHidden(3, True)  # Price
        table.setColumnHidden(4, True)  # Change
        table.setColumnHidden(5, True)  # Change %
        table.setColumnHidden(6, True)  # Volume


        table.itemDoubleClicked.connect(self.parent.on_symbol_double_clicked)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self.parent.show_context_menu)

        header.sectionMoved.connect(self.parent.save_column_state)
        header.sectionResized.connect(self.parent.save_column_state)

    def build_quick_add_row(self) -> QHBoxLayout:
        """Build quick-add buttons row."""
        quick_add_layout = QHBoxLayout()

        indices_btn = QPushButton("Indices")
        indices_btn.clicked.connect(self.parent.add_indices)
        indices_btn.setToolTip("Add major indices (QQQ, DIA, SPY)")
        quick_add_layout.addWidget(indices_btn)

        tech_btn = QPushButton("Tech")
        tech_btn.clicked.connect(self.parent.add_tech_stocks)
        tech_btn.setToolTip("Add tech stocks (AAPL, MSFT, GOOGL, etc.)")
        quick_add_layout.addWidget(tech_btn)

        crypto_btn = QPushButton("Crypto")
        crypto_btn.clicked.connect(self.parent.add_crypto_pairs)
        crypto_btn.setToolTip("Add major crypto pairs (BTC/USD, ETH/USD, SOL/USD, etc.)")
        quick_add_layout.addWidget(crypto_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.parent.clear_watchlist)
        clear_btn.setToolTip("Clear all symbols")
        quick_add_layout.addWidget(clear_btn)
        return quick_add_layout
