"""Bitunix Trading API Widget - Compact Vertical UI for Dock.

This module provides a compact vertical layout (360px width) suitable
for the bitunixTradingDock. Contains all UI elements in a vertical stack.

Features:
    - Vertical layout for narrow dock panels
    - Collapsible sections
    - Same controls as horizontal version
    - Optimized for 380px dock width
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox, QSpinBox, QSlider,
    QButtonGroup, QCheckBox, QFrame
)


class BitunixAPIWidgetCompactUI:
    """Mixin providing compact vertical UI for BitunixTradingAPIWidget.

    This layout is designed for dock panels with ~380px width.
    All controls are stacked vertically with sections for:
    - Symbol & Direction
    - Order Entry (Quantity, Volume, Leverage)
    - TP/SL Controls
    - Action Buttons (BUY/SELL)
    """

    def _setup_compact_ui(self):
        """Setup compact vertical UI layout for dock panels."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ─────────────────────────────────────────────────────────────────
        # SECTION 1: Symbol & Direction
        # ─────────────────────────────────────────────────────────────────
        symbol_section = self._build_compact_symbol_section()
        main_layout.addWidget(symbol_section)

        # Separator
        main_layout.addWidget(self._create_separator())

        # ─────────────────────────────────────────────────────────────────
        # SECTION 2: Order Entry (Quantity, Volume, Leverage)
        # ─────────────────────────────────────────────────────────────────
        order_section = self._build_compact_order_section()
        main_layout.addWidget(order_section)

        # Separator
        main_layout.addWidget(self._create_separator())

        # ─────────────────────────────────────────────────────────────────
        # SECTION 3: TP/SL Controls
        # ─────────────────────────────────────────────────────────────────
        tpsl_section = self._build_compact_tpsl_section()
        main_layout.addWidget(tpsl_section)

        # Separator
        main_layout.addWidget(self._create_separator())

        # ─────────────────────────────────────────────────────────────────
        # SECTION 4: Action Buttons
        # ─────────────────────────────────────────────────────────────────
        action_section = self._build_compact_action_section()
        main_layout.addWidget(action_section)

        # Stretch at bottom
        main_layout.addStretch()

        # Adapter status (bottom)
        status_layout = QHBoxLayout()
        status_layout.addStretch()
        self.adapter_status_label = QLabel("disconnected")
        self.adapter_status_label.setStyleSheet("color: #888; font-size: 9px;")
        status_layout.addWidget(self.adapter_status_label)
        main_layout.addLayout(status_layout)

        self.setLayout(main_layout)
        self.setMinimumWidth(320)
        self.setMaximumWidth(400)

    def _create_separator(self) -> QFrame:
        """Create a horizontal separator line."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #3a3a3a;")
        line.setFixedHeight(1)
        return line

    def _build_compact_symbol_section(self) -> QWidget:
        """Build compact symbol and direction section.

        Returns:
            QWidget: Symbol section widget
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Symbol Selection
        symbol_row = QHBoxLayout()
        symbol_label = QLabel("Symbol:")
        symbol_label.setFixedWidth(60)
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"])
        symbol_row.addWidget(symbol_label)
        symbol_row.addWidget(self.symbol_combo, 1)
        layout.addLayout(symbol_row)

        # Direction Buttons (Long/Short)
        direction_row = QHBoxLayout()
        direction_row.setSpacing(8)

        self.long_btn = QPushButton("Long")
        self.short_btn = QPushButton("Short")
        self.long_btn.setCheckable(True)
        self.short_btn.setCheckable(True)
        self.long_btn.setChecked(True)
        self.long_btn.setFixedHeight(36)
        self.short_btn.setFixedHeight(36)

        self.long_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #888;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #26a69a;
                color: white;
            }
        """)
        self.short_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #888;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #ef5350;
                color: white;
            }
        """)

        direction_row.addWidget(self.long_btn, 1)
        direction_row.addWidget(self.short_btn, 1)
        layout.addLayout(direction_row)

        # Order Type Buttons (Market/Limit)
        order_type_row = QHBoxLayout()
        order_type_row.setSpacing(8)

        self.order_type_group = QButtonGroup()
        self.order_type_group.setExclusive(True)
        self.market_btn = QPushButton("Market")
        self.limit_btn = QPushButton("Limit")
        self.market_btn.setCheckable(True)
        self.limit_btn.setCheckable(True)
        self.order_type_group.addButton(self.market_btn)
        self.order_type_group.addButton(self.limit_btn)
        self.market_btn.setChecked(True)
        self.market_btn.setFixedHeight(30)
        self.limit_btn.setFixedHeight(30)

        btn_style = """
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
        """
        self.market_btn.setStyleSheet(btn_style)
        self.limit_btn.setStyleSheet(btn_style)

        order_type_row.addWidget(self.market_btn, 1)
        order_type_row.addWidget(self.limit_btn, 1)
        layout.addLayout(order_type_row)

        # Limit Price (hidden by default)
        limit_row = QHBoxLayout()
        self.limit_price_label = QLabel("Limit:")
        self.limit_price_label.setFixedWidth(60)
        self.limit_price_spin = QDoubleSpinBox()
        self.limit_price_spin.setRange(0.0, 1000000.0)
        self.limit_price_spin.setDecimals(2)
        self.limit_price_spin.setSingleStep(0.1)
        self.limit_price_spin.setValue(0.0)
        self.limit_price_spin.setVisible(False)
        self.limit_price_label.setVisible(False)
        limit_row.addWidget(self.limit_price_label)
        limit_row.addWidget(self.limit_price_spin, 1)
        layout.addLayout(limit_row)

        widget.setLayout(layout)
        return widget

    def _build_compact_order_section(self) -> QWidget:
        """Build compact order entry section.

        Returns:
            QWidget: Order section widget
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Quantity - 4 decimal places
        qty_row = QHBoxLayout()
        qty_label = QLabel("Stück:")
        qty_label.setFixedWidth(60)
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.0001, 10000.0)
        self.quantity_spin.setDecimals(4)
        self.quantity_spin.setSingleStep(0.0001)
        self.quantity_spin.setValue(0.01)
        self.quantity_spin.setSuffix(" BTC")
        qty_row.addWidget(qty_label)
        qty_row.addWidget(self.quantity_spin, 1)
        layout.addLayout(qty_row)

        # Volume
        vol_row = QHBoxLayout()
        vol_label = QLabel("Vol:")
        vol_label.setFixedWidth(60)
        self.volume_spin = QDoubleSpinBox()
        self.volume_spin.setRange(1.0, 1000000.0)
        self.volume_spin.setDecimals(2)
        self.volume_spin.setSingleStep(10.0)
        self.volume_spin.setValue(1000.0)
        self.volume_spin.setSuffix(" USDT")
        vol_row.addWidget(vol_label)
        vol_row.addWidget(self.volume_spin, 1)
        layout.addLayout(vol_row)

        # Leverage with slider
        lev_row = QHBoxLayout()
        lev_label = QLabel("Hebel:")
        lev_label.setFixedWidth(60)
        self.leverage_spin = QSpinBox()
        self.leverage_spin.setRange(1, 200)
        self.leverage_spin.setValue(10)
        self.leverage_spin.setSuffix("x")
        self.leverage_spin.setFixedWidth(70)
        lev_row.addWidget(lev_label)
        lev_row.addWidget(self.leverage_spin)

        self.exposure_slider = QSlider(Qt.Orientation.Horizontal)
        self.exposure_slider.setRange(1, 200)
        self.exposure_slider.setValue(10)
        self.exposure_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #3a3a3a;
                border-radius: 2px;
            }
            QSlider::sub-page:horizontal {
                background: #ffa726;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ffa726;
                width: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
        """)
        lev_row.addWidget(self.exposure_slider, 1)
        layout.addLayout(lev_row)

        # Preset buttons (compact grid)
        presets_row = QHBoxLayout()
        presets_row.setSpacing(2)
        self._preset_buttons = []
        for value in [10, 25, 50, 75, 100, 125, 150, 200]:
            btn = QPushButton(str(value))
            btn.setFixedSize(36, 20)
            btn.setStyleSheet(
                "background-color: #3a3a3a; color: #aaa; font-size: 9px; "
                "border-radius: 2px; padding: 0px;"
            )
            btn.setProperty("preset_value", value)
            self._preset_buttons.append(btn)
            presets_row.addWidget(btn)
        layout.addLayout(presets_row)

        # Current Price
        price_row = QHBoxLayout()
        price_label_static = QLabel("Preis:")
        price_label_static.setFixedWidth(60)
        self.price_label = QLabel("—")
        self.price_label.setStyleSheet("color: #ffa726; font-size: 12px; font-weight: bold;")
        price_row.addWidget(price_label_static)
        price_row.addWidget(self.price_label, 1)
        layout.addLayout(price_row)

        widget.setLayout(layout)
        return widget

    def _build_compact_tpsl_section(self) -> QWidget:
        """Build compact TP/SL section.

        Returns:
            QWidget: TP/SL section widget
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Take Profit
        tp_row = QHBoxLayout()
        tp_row.setSpacing(4)
        self.tp_cb = QCheckBox("TP")
        self.tp_cb.setFixedWidth(50)
        self.tp_spin = QDoubleSpinBox()
        self.tp_spin.setRange(0.0, 1000.0)
        self.tp_spin.setDecimals(1)
        self.tp_spin.setSuffix(" %")
        self.tp_spin.setValue(2.0)
        self.tp_spin.setEnabled(False)
        tp_row.addWidget(self.tp_cb)
        tp_row.addWidget(self.tp_spin, 1)
        layout.addLayout(tp_row)

        # Stop Loss
        sl_row = QHBoxLayout()
        sl_row.setSpacing(4)
        self.sl_cb = QCheckBox("SL")
        self.sl_cb.setChecked(True)
        self.sl_cb.setFixedWidth(50)
        self.sl_spin = QDoubleSpinBox()
        self.sl_spin.setRange(0.0, 100.0)
        self.sl_spin.setDecimals(1)
        self.sl_spin.setSuffix(" %")
        self.sl_spin.setValue(1.0)
        sl_row.addWidget(self.sl_cb)
        sl_row.addWidget(self.sl_spin, 1)
        layout.addLayout(sl_row)

        # Trailing & Sync
        trailing_row = QHBoxLayout()
        trailing_row.setSpacing(4)
        self.trailing_cb = QCheckBox("Trailing")
        self.trailing_cb.setFixedWidth(70)
        self.sync_sl_btn = QPushButton("Sync SL")
        self.sync_sl_btn.setFixedHeight(24)
        self.sync_sl_btn.setStyleSheet("font-size: 10px;")
        trailing_row.addWidget(self.trailing_cb)
        trailing_row.addWidget(self.sync_sl_btn, 1)
        layout.addLayout(trailing_row)

        # Trailing info
        self.trailing_info = QLabel("Last SL: —")
        self.trailing_info.setStyleSheet("color: #666; font-size: 9px;")
        layout.addWidget(self.trailing_info)

        widget.setLayout(layout)
        return widget

    def _build_compact_action_section(self) -> QWidget:
        """Build compact action buttons section.

        Returns:
            QWidget: Action section widget
        """
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # BUY/SELL buttons
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(8)

        self.buy_btn = QPushButton("BUY")
        self.buy_btn.setFixedHeight(44)
        self.buy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #888;
                font-weight: bold;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:enabled {
                background-color: #26a69a;
                color: white;
            }
            QPushButton:hover:enabled {
                background-color: #2bbd9e;
            }
        """)

        self.sell_btn = QPushButton("SELL")
        self.sell_btn.setFixedHeight(44)
        self.sell_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: #888;
                font-weight: bold;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:enabled {
                background-color: #ef5350;
                color: white;
            }
            QPushButton:hover:enabled {
                background-color: #f44336;
            }
        """)

        buttons_row.addWidget(self.buy_btn, 1)
        buttons_row.addWidget(self.sell_btn, 1)
        layout.addLayout(buttons_row)

        # Paper Trading toggle
        self.trade_mode_btn = QPushButton("Paper Trading")
        self.trade_mode_btn.setCheckable(True)
        self.trade_mode_btn.setFixedHeight(32)
        self.trade_mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #D32F2F;
            }
        """)
        layout.addWidget(self.trade_mode_btn)

        widget.setLayout(layout)
        return widget
