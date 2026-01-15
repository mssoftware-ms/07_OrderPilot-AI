"""
Bitunix Trading UI - UI Building Methods

Handles all UI construction for BitunixTradingWidget:
- Account info section (balance, margin, PnL, reset button)
- Order entry section (symbol, type, quantity, price, investment, leverage, SL/TP)
- Positions table section (7 columns with color coding)

Module 1/2 of bitunix_trading_widget.py split (Lines 273-572)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QDoubleSpinBox,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget


class BitunixTradingUI:
    """Verwaltet UI-Komponenten für Bitunix Trading Widget.

    Verantwortlich für:
    - Account Info Section (Balance, Margin, PnL, Reset)
    - Order Entry Section (Symbol, Type, Quantity, Price, Investment, Leverage, SL/TP, Buttons)
    - Positions Table Section (7-Column-Tabelle mit Farb-Coding)
    """

    def __init__(self, parent_widget: "QWidget"):
        """Initialisiert BitunixTradingUI.

        Args:
            parent_widget: Das BitunixTradingWidget
        """
        self.parent = parent_widget

    def build_account_section(self) -> QGroupBox:
        """Build account information display.

        Returns:
            Account info group box
        """
        group = QGroupBox("Account Info")
        layout = QVBoxLayout(group)

        # Balance row
        balance_layout = QHBoxLayout()
        balance_layout.addWidget(QLabel("Balance:"))
        self.parent.balance_label = QLabel("-- USDT")
        self.parent.balance_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        balance_layout.addWidget(self.parent.balance_label)
        balance_layout.addStretch()
        layout.addLayout(balance_layout)

        # Margin row
        margin_layout = QHBoxLayout()
        margin_layout.addWidget(QLabel("Available Margin:"))
        self.parent.margin_label = QLabel("-- USDT")
        self.parent.margin_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        margin_layout.addWidget(self.parent.margin_label)
        margin_layout.addStretch()
        layout.addLayout(margin_layout)

        # PnL row
        pnl_layout = QHBoxLayout()
        pnl_layout.addWidget(QLabel("Daily PnL:"))
        self.parent.pnl_label = QLabel("-- USDT")
        pnl_layout.addWidget(self.parent.pnl_label)
        pnl_layout.addStretch()
        layout.addLayout(pnl_layout)

        # Reset Button (Paper only)
        self.parent.reset_btn = QPushButton("🔄 Reset Paper Account")
        self.parent.reset_btn.clicked.connect(self.parent._reset_paper_account)
        self.parent.reset_btn.setStyleSheet("background-color: #555; color: #aaa; font-size: 10px; margin-top: 5px;")
        layout.addWidget(self.parent.reset_btn)

        return group

    def build_order_entry_section(self) -> QGroupBox:
        """Build order entry panel.

        Returns:
            Order entry group box
        """
        group = QGroupBox("Place Order")
        layout = QVBoxLayout(group)

        # Symbol display
        symbol_layout = QHBoxLayout()
        symbol_layout.addWidget(QLabel("Symbol:"))
        self.parent.symbol_label = QLabel("--")
        self.parent.symbol_label.setStyleSheet("font-weight: bold; color: #FFC107;")
        symbol_layout.addWidget(self.parent.symbol_label)
        symbol_layout.addStretch()
        layout.addLayout(symbol_layout)

        # Order type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.parent.order_type_combo = QComboBox()
        self.parent.order_type_combo.addItems(["Market", "Limit"])
        self.parent.order_type_combo.currentTextChanged.connect(self.parent._on_order_type_changed)
        type_layout.addWidget(self.parent.order_type_combo)
        layout.addLayout(type_layout)

        # Quantity
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Quantity:"))
        self.parent.quantity_spin = QDoubleSpinBox()
        self.parent.quantity_spin.setDecimals(4)
        self.parent.quantity_spin.setMinimum(0.0001)
        self.parent.quantity_spin.setMaximum(1000000)
        self.parent.quantity_spin.setValue(0.01)
        self.parent.quantity_spin.valueChanged.connect(self.parent._on_quantity_changed)
        qty_layout.addWidget(self.parent.quantity_spin)
        layout.addLayout(qty_layout)

        # Price (for limit orders)
        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("Price:"))
        self.parent.price_spin = QDoubleSpinBox()
        self.parent.price_spin.setDecimals(2)
        self.parent.price_spin.setMinimum(0)
        self.parent.price_spin.setMaximum(1000000)
        self.parent.price_spin.setEnabled(False)  # Disabled by default (Market order)
        self.parent.price_spin.valueChanged.connect(self.parent._on_price_changed)
        price_layout.addWidget(self.parent.price_spin)
        layout.addLayout(price_layout)

        # Investment Amount (USDT)
        investment_layout = QHBoxLayout()
        investment_layout.addWidget(QLabel("Investment (USDT):"))
        self.parent.investment_spin = QDoubleSpinBox()
        self.parent.investment_spin.setRange(0, 1000000)
        self.parent.investment_spin.setDecimals(2)
        self.parent.investment_spin.setValue(100.0)  # Default $100
        self.parent.investment_spin.setSingleStep(10.0)
        self.parent.investment_spin.setMinimumWidth(150)
        self.parent.investment_spin.valueChanged.connect(self.parent._on_investment_changed)
        investment_layout.addWidget(self.parent.investment_spin)
        layout.addLayout(investment_layout)

        # Leverage
        leverage_layout = QHBoxLayout()
        leverage_layout.addWidget(QLabel("Leverage:"))
        self.parent.leverage_slider = QSlider(Qt.Orientation.Horizontal)
        self.parent.leverage_slider.setMinimum(1)
        self.parent.leverage_slider.setMaximum(20)
        self.parent.leverage_slider.setValue(1)
        self.parent.leverage_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.parent.leverage_slider.setTickInterval(1)
        self.parent.leverage_slider.valueChanged.connect(self.parent._on_leverage_changed)
        leverage_layout.addWidget(self.parent.leverage_slider)
        self.parent.leverage_value = QLabel("1x")
        self.parent.leverage_value.setStyleSheet("font-weight: bold; min-width: 40px;")
        leverage_layout.addWidget(self.parent.leverage_value)
        layout.addLayout(leverage_layout)

        # Stop Loss
        sl_layout = QHBoxLayout()
        sl_layout.addWidget(QLabel("Stop Loss:"))
        self.parent.stop_loss_spin = QDoubleSpinBox()
        self.parent.stop_loss_spin.setDecimals(2)
        self.parent.stop_loss_spin.setMinimum(0)
        self.parent.stop_loss_spin.setMaximum(1000000)
        self.parent.stop_loss_spin.setSpecialValueText("None")
        sl_layout.addWidget(self.parent.stop_loss_spin)
        layout.addLayout(sl_layout)

        # Take Profit
        tp_layout = QHBoxLayout()
        tp_layout.addWidget(QLabel("Take Profit:"))
        self.parent.take_profit_spin = QDoubleSpinBox()
        self.parent.take_profit_spin.setDecimals(2)
        self.parent.take_profit_spin.setMinimum(0)
        self.parent.take_profit_spin.setMaximum(1000000)
        self.parent.take_profit_spin.setSpecialValueText("None")
        tp_layout.addWidget(self.parent.take_profit_spin)
        layout.addLayout(tp_layout)

        # Direction Toggle (LONG / SHORT)
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Direction:"))
        self.parent.direction_combo = QComboBox()
        self.parent.direction_combo.addItems(["LONG", "SHORT"])
        direction_layout.addWidget(self.parent.direction_combo)
        layout.addLayout(direction_layout)

        # Buy/Sell Buttons
        button_layout = QHBoxLayout()
        self.parent.buy_button = QPushButton("🟢 BUY")
        self.parent.buy_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.parent.buy_button.clicked.connect(self.parent._on_buy_clicked)
        self.parent.buy_button.setEnabled(False)
        button_layout.addWidget(self.parent.buy_button)

        self.parent.sell_button = QPushButton("🔴 SELL")
        self.parent.sell_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.parent.sell_button.clicked.connect(self.parent._on_sell_clicked)
        self.parent.sell_button.setEnabled(False)
        button_layout.addWidget(self.parent.sell_button)
        layout.addLayout(button_layout)

        return group

    def build_positions_section(self) -> QGroupBox:
        """Build positions table.

        Returns:
            Positions group box
        """
        group = QGroupBox("Open Positions")
        layout = QVBoxLayout(group)

        # Positions Table (7 Columns)
        self.parent.positions_table = QTableWidget()
        self.parent.positions_table.setColumnCount(7)
        self.parent.positions_table.setHorizontalHeaderLabels([
            "Symbol",
            "Direction",  # NEW COLUMN
            "Quantity",
            "Entry Price",
            "Current Price",
            "Leverage",
            "PnL (USDT)"
        ])

        # Auto-resize columns for better layout
        header = self.parent.positions_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Symbol
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Direction
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Quantity
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Entry Price
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Current Price
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Leverage
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # PnL

        layout.addWidget(self.parent.positions_table)

        # Buttons: Refresh and Delete
        buttons_layout = QHBoxLayout()

        refresh_button = QPushButton("🔄 Refresh Positions")
        refresh_button.clicked.connect(self.parent._load_positions)
        buttons_layout.addWidget(refresh_button)

        delete_button = QPushButton("🗑️ Delete Row")
        delete_button.clicked.connect(self.parent._delete_selected_row)
        delete_button.setStyleSheet("background-color: #d32f2f; color: white;")
        buttons_layout.addWidget(delete_button)

        layout.addLayout(buttons_layout)

        return group
