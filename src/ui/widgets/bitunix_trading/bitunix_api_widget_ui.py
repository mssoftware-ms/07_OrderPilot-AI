"""Bitunix Trading API Widget - UI Components Module.

This module contains all UI construction methods for the BitunixTradingAPIWidget.
Separated from event handling and business logic for maintainability.

Components:
    - Left Column: Symbol, Direction, Order Type, Limit Price
    - Middle Column: Quantity, Volume, Leverage, Last Price
    - TP/SL Column: Take Profit, Stop Loss, Trailing controls
    - Right Column: BUY/SELL buttons, Paper Trading, Slider, Presets
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QSlider,
    QButtonGroup, QCheckBox
)


class BitunixAPIWidgetUI:
    """Mixin providing UI construction methods for BitunixTradingAPIWidget."""

    def _setup_ui(self):
        """Setup compact UI layout - 4 columns: Left, Middle, TP/SL, Right."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 12, 8, 8)
        main_layout.setSpacing(6)

        # Main horizontal layout with 4 columns
        h_layout = QHBoxLayout()
        h_layout.setSpacing(12)

        # LEFT COLUMN: Symbol, Direction, Order Type, Limit Price (240px)
        left_column = self._build_left_column()
        h_layout.addWidget(left_column)

        # MIDDLE COLUMN: Stückzahl, Volumen, Leverage, Last Price (220px)
        middle_column = self._build_middle_column()
        h_layout.addWidget(middle_column)

        # TP/SL COLUMN: Take Profit, Stop Loss, Trailing (180px)
        tpsl_column = self._build_tpsl_column()
        h_layout.addWidget(tpsl_column)

        # RIGHT COLUMN: BUY/SELL buttons, Paper Trading, Slider, Presets (270px)
        right_column = self._build_right_column()
        h_layout.addWidget(right_column)

        main_layout.addLayout(h_layout)

        # Bottom: Adapter status (right-aligned, small)
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        self.adapter_status_label = QLabel("disconnected")
        self.adapter_status_label.setStyleSheet("color: #888; font-size: 9px;")
        status_layout.addWidget(self.adapter_status_label)
        main_layout.addLayout(status_layout)

        self.setLayout(main_layout)
        self.setMaximumHeight(250)
        self.setMinimumWidth(1005)
        self.setMaximumWidth(1005)

    def _build_left_column(self) -> QWidget:
        """Build left column with Symbol, Direction, Order Type, Limit Price.

        Returns:
            QWidget: Left column widget (240px wide)
        """
        widget = QWidget()
        widget.setFixedWidth(240)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        # Symbol Selection
        self.symbol_combo = QComboBox()
        self.symbol_combo.setFixedWidth(190)
        self.symbol_combo.addItems(["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"])

        symbol_label = QLabel("Symbol:")
        grid.addWidget(symbol_label, 0, 0)
        grid.addWidget(self.symbol_combo, 0, 1)

        # Direction (Long/Short)
        direction_widget = self._create_direction_buttons()
        direction_label = QLabel("Direction:")
        grid.addWidget(direction_label, 1, 0)
        grid.addWidget(direction_widget, 1, 1)

        # Order Type (Market/Limit)
        order_type_widget = self._create_order_type_buttons()
        order_type_label = QLabel("Order Type:")
        grid.addWidget(order_type_label, 2, 0)
        grid.addWidget(order_type_widget, 2, 1)

        # Limit Price (only for Limit orders)
        self.limit_price_label = QLabel("Limit Price:")
        grid.addWidget(self.limit_price_label, 3, 0)

        self.limit_price_spin = QDoubleSpinBox()
        self.limit_price_spin.setFixedWidth(190)
        self.limit_price_spin.setRange(0.0, 1000000.0)
        self.limit_price_spin.setDecimals(2)
        self.limit_price_spin.setSingleStep(0.1)
        self.limit_price_spin.setValue(0.0)
        self.limit_price_spin.setVisible(False)
        grid.addWidget(self.limit_price_spin, 3, 1)
        self.limit_price_label.setVisible(False)

        layout.addLayout(grid)
        widget.setLayout(layout)
        return widget

    def _create_direction_buttons(self) -> QWidget:
        """Create Long/Short direction buttons.

        Returns:
            QWidget: Direction button widget
        """
        direction_widget = QWidget()
        direction_layout = QHBoxLayout()
        direction_layout.setContentsMargins(0, 0, 0, 0)
        direction_layout.setSpacing(6)

        self.long_btn = QPushButton("Long")
        self.short_btn = QPushButton("Short")
        self.long_btn.setFixedWidth(92)
        self.short_btn.setFixedWidth(92)
        self.long_btn.setFixedHeight(32)
        self.short_btn.setFixedHeight(32)
        self.long_btn.setCheckable(True)
        self.short_btn.setCheckable(True)
        self.long_btn.setChecked(True)

        self.long_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #888;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #26a69a;
                color: white;
                font-weight: bold;
            }
        """)
        self.short_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #888;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #ef5350;
                color: white;
                font-weight: bold;
            }
        """)

        direction_layout.addWidget(self.long_btn)
        direction_layout.addWidget(self.short_btn)
        direction_widget.setLayout(direction_layout)
        return direction_widget

    def _create_order_type_buttons(self) -> QWidget:
        """Create Market/Limit order type buttons.

        Returns:
            QWidget: Order type button widget
        """
        order_type_widget = QWidget()
        order_type_layout = QHBoxLayout()
        order_type_layout.setContentsMargins(0, 0, 0, 0)
        order_type_layout.setSpacing(6)

        self.order_type_group = QButtonGroup()
        self.order_type_group.setExclusive(True)
        self.market_btn = QPushButton("Market")
        self.limit_btn = QPushButton("Limit")
        self.market_btn.setFixedWidth(92)
        self.limit_btn.setFixedWidth(92)
        self.market_btn.setFixedHeight(32)
        self.limit_btn.setFixedHeight(32)
        self.market_btn.setCheckable(True)
        self.limit_btn.setCheckable(True)
        self.order_type_group.addButton(self.market_btn)
        self.order_type_group.addButton(self.limit_btn)
        self.market_btn.setChecked(True)

        self.market_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #888;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
        """)
        self.limit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #888;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
        """)

        order_type_layout.addWidget(self.market_btn)
        order_type_layout.addWidget(self.limit_btn)
        order_type_widget.setLayout(order_type_layout)
        return order_type_widget

    def _build_middle_column(self) -> QWidget:
        """Build middle column with Stückzahl, Volumen, Leverage, Last Price.

        Returns:
            QWidget: Middle column widget (220px wide)
        """
        widget = QWidget()
        widget.setFixedWidth(220)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        # Quantity (Base Asset)
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setFixedWidth(150)
        self.quantity_spin.setRange(0.001, 10000.0)
        self.quantity_spin.setDecimals(3)
        self.quantity_spin.setSingleStep(0.001)
        self.quantity_spin.setValue(0.01)
        self.quantity_spin.setSuffix(" BTC")

        quantity_label = QLabel("Stückzahl:")
        grid.addWidget(quantity_label, 0, 0)
        grid.addWidget(self.quantity_spin, 0, 1)

        # Volume (USDT)
        self.volume_spin = QDoubleSpinBox()
        self.volume_spin.setFixedWidth(150)
        self.volume_spin.setRange(1.0, 1000000.0)
        self.volume_spin.setDecimals(2)
        self.volume_spin.setSingleStep(10.0)
        self.volume_spin.setValue(1000.0)
        self.volume_spin.setSuffix(" USDT")

        volume_label = QLabel("Volumen:")
        grid.addWidget(volume_label, 1, 0)
        grid.addWidget(self.volume_spin, 1, 1)

        # Leverage
        self.leverage_spin = QSpinBox()
        self.leverage_spin.setFixedWidth(150)
        self.leverage_spin.setRange(1, 200)
        self.leverage_spin.setValue(10)
        self.leverage_spin.setSuffix("x")

        leverage_label = QLabel("Leverage:")
        grid.addWidget(leverage_label, 2, 0)
        grid.addWidget(self.leverage_spin, 2, 1)

        # Current Price Display
        self.price_label = QLabel("—")
        self.price_label.setStyleSheet("color: #888; font-size: 11px;")

        last_price_label = QLabel("Last Price:")
        grid.addWidget(last_price_label, 3, 0)
        grid.addWidget(self.price_label, 3, 1)

        layout.addLayout(grid)
        widget.setLayout(layout)
        return widget

    def _build_tpsl_column(self) -> QWidget:
        """Build TP/SL column with Take Profit, Stop Loss, Trailing controls.

        Returns:
            QWidget: TP/SL column widget (180px wide)
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        # Take Profit
        tp_widget = self._create_tp_controls()
        tp_label = QLabel("TP:")
        grid.addWidget(tp_label, 0, 0)
        grid.addWidget(tp_widget, 0, 1)

        # Stop Loss
        sl_widget = self._create_sl_controls()
        sl_label = QLabel("SL:")
        grid.addWidget(sl_label, 1, 0)
        grid.addWidget(sl_widget, 1, 1)

        layout.addLayout(grid)

        # Sync SL Button (rechtsbündig mit TP/SL Feldern)
        sync_layout = QHBoxLayout()
        sync_layout.setContentsMargins(0, 0, 0, 0)
        self.sync_sl_btn = QPushButton("Sync SL")
        self.sync_sl_btn.setFixedWidth(130)
        self.sync_sl_btn.setStyleSheet("font-size: 10px; padding: 4px;")
        sync_layout.addStretch()
        sync_layout.addWidget(self.sync_sl_btn)
        layout.addLayout(sync_layout)

        # Trailing Stop
        self.trailing_cb = QCheckBox("Use Trailing")
        self.trailing_cb.setChecked(False)
        layout.addWidget(self.trailing_cb)

        # Trailing Info
        self.trailing_info = QLabel("Last SL: —")
        self.trailing_info.setStyleSheet("color: #666; font-size: 9px;")
        layout.addWidget(self.trailing_info)

        widget.setLayout(layout)
        widget.setFixedWidth(180)
        return widget

    def _create_tp_controls(self) -> QWidget:
        """Create Take Profit checkbox and spinbox.

        Returns:
            QWidget: TP control widget
        """
        tp_widget = QWidget()
        tp_layout = QHBoxLayout()
        tp_layout.setContentsMargins(0, 0, 0, 0)
        tp_layout.setSpacing(4)

        self.tp_cb = QCheckBox()
        self.tp_cb.setChecked(False)
        tp_layout.addWidget(self.tp_cb)

        self.tp_spin = QDoubleSpinBox()
        self.tp_spin.setFixedWidth(100)
        self.tp_spin.setRange(0.0, 1000.0)
        self.tp_spin.setDecimals(1)
        self.tp_spin.setSuffix(" %")
        self.tp_spin.setValue(2.0)  # Default 2%
        self.tp_spin.setEnabled(False)
        tp_layout.addWidget(self.tp_spin)

        tp_widget.setLayout(tp_layout)
        return tp_widget

    def _create_sl_controls(self) -> QWidget:
        """Create Stop Loss checkbox and spinbox.

        Returns:
            QWidget: SL control widget
        """
        sl_widget = QWidget()
        sl_layout = QHBoxLayout()
        sl_layout.setContentsMargins(0, 0, 0, 0)
        sl_layout.setSpacing(4)

        self.sl_cb = QCheckBox()
        self.sl_cb.setChecked(True)
        sl_layout.addWidget(self.sl_cb)

        self.sl_spin = QDoubleSpinBox()
        self.sl_spin.setFixedWidth(100)
        self.sl_spin.setRange(0.0, 100.0)
        self.sl_spin.setDecimals(1)
        self.sl_spin.setSuffix(" %")
        self.sl_spin.setValue(1.0)  # Default 1%
        sl_layout.addWidget(self.sl_spin)

        sl_widget.setLayout(sl_layout)
        return sl_widget

    def _build_right_column(self) -> QWidget:
        """Build right column with BUY/SELL buttons, Paper Trading, Slider, Presets.

        Returns:
            QWidget: Right column widget (270px wide)
        """
        widget = QWidget()
        widget.setFixedWidth(270)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # BUY/SELL buttons (top row)
        buttons_layout = self._create_buy_sell_buttons()
        layout.addLayout(buttons_layout)

        # Paper Trading button
        self.trade_mode_btn = QPushButton("Paper Trading")
        self.trade_mode_btn.setCheckable(True)
        self.trade_mode_btn.setFixedHeight(32)
        self.trade_mode_btn.setFixedWidth(270)
        layout.addWidget(self.trade_mode_btn)

        # 8px vertical spacing before slider
        layout.addSpacing(8)

        # Leverage slider with orange indicator
        slider_layout = self._create_leverage_slider()
        layout.addLayout(slider_layout)

        # Preset buttons (10, 20, 30, ..., 200)
        presets_widget = self._create_preset_buttons()
        layout.addWidget(presets_widget)

        widget.setLayout(layout)
        return widget

    def _create_buy_sell_buttons(self) -> QHBoxLayout:
        """Create BUY and SELL buttons.

        Returns:
            QHBoxLayout: Layout with BUY and SELL buttons
        """
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(0)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        self.buy_btn = QPushButton("BUY")
        self.buy_btn.setFixedWidth(130)
        self.buy_btn.setFixedHeight(32)
        self.buy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #888;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        buttons_layout.addWidget(self.buy_btn)

        buttons_layout.addStretch()  # Stretch between buttons

        self.sell_btn = QPushButton("SELL")
        self.sell_btn.setFixedWidth(130)
        self.sell_btn.setFixedHeight(32)
        self.sell_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #888;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
        """)
        buttons_layout.addWidget(self.sell_btn)

        return buttons_layout

    def _create_leverage_slider(self) -> QHBoxLayout:
        """Create horizontal leverage slider with orange indicator.

        Returns:
            QHBoxLayout: Layout with leverage slider
        """
        slider_layout = QHBoxLayout()
        slider_layout.setContentsMargins(0, 0, 0, 0)
        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setFixedWidth(270)
        self.exposure_slider.setRange(1, 200)
        self.exposure_slider.setSingleStep(10)
        self.exposure_slider.setPageStep(10)
        self.exposure_slider.setValue(10)
        self.exposure_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 6px;
                background: #3a3a3a;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #ffa726;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #2a2a2a;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffa726;
                border: 2px solid #ff9800;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
        """)
        slider_layout.addWidget(self.exposure_slider)
        return slider_layout

    def _create_preset_buttons(self) -> QWidget:
        """Create preset leverage buttons (10-200).

        Returns:
            QWidget: Widget with preset buttons
        """
        presets_widget = QWidget()
        presets_widget.setFixedWidth(270)
        presets_layout = QGridLayout()
        presets_layout.setContentsMargins(0, 0, 0, 0)
        presets_layout.setHorizontalSpacing(4)
        presets_layout.setVerticalSpacing(2)

        preset_values = list(range(10, 210, 10))  # 10-200
        for idx, value in enumerate(preset_values):
            btn = QPushButton(str(value))
            btn.setFixedSize(24, 14)
            btn.setStyleSheet(
                "background-color: #3a3a3a; color: #aaa; font-size: 8px; "
                "border-radius: 2px; padding: 0px;"
            )
            # Store value for later connection in events module
            btn.setProperty("preset_value", value)
            row = idx // 10
            col = idx % 10
            presets_layout.addWidget(btn, row, col)

        presets_widget.setLayout(presets_layout)
        return presets_widget
