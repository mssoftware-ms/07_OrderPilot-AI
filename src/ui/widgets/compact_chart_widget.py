"""Compact Chart Widget for Trading Tab using Lightweight Charts.

Provides a small lightweight chart display (max 450px x 250px) with:
- Real-time OHLCV candlestick chart
- Volume histogram (bottom 25%)
- Pop-up enlargement functionality
- Integration with parent ChartWindow data
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import pandas as pd

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QDialog, QSizeGrip
)

try:
    from lightweight_charts.widgets import QtChart
    LIGHTWEIGHT_CHARTS_AVAILABLE = True
except ImportError:
    LIGHTWEIGHT_CHARTS_AVAILABLE = False
    logging.warning("lightweight-charts not installed. Compact chart will not be available.")

if TYPE_CHECKING:
    from src.ui.widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)


class CompactChartWidget(QWidget):
    """Compact chart widget for Trading tab using Lightweight Charts.

    Features:
        - Maximum size: 450px x 250px
        - QtChart with candlesticks and volume histogram
        - Click to enlarge in pop-up
        - Real-time OHLCV data updates
    """

    # Signal emitted when user wants to enlarge chart
    enlarge_requested = pyqtSignal()

    def __init__(self, parent_chart: "ChartWindow | None" = None):
        """Initialize compact chart widget.

        Args:
            parent_chart: Parent ChartWindow for data access
        """
        super().__init__()

        self._parent_chart = parent_chart
        self._chart = None

        if not LIGHTWEIGHT_CHARTS_AVAILABLE:
            logger.warning("lightweight-charts not installed. Widget will show installation instructions.")

        # Always setup UI - fallback will be shown if library unavailable
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup widget UI."""
        # Set widget size FIRST (critical for layout visibility)
        self.setMinimumSize(450, 250)
        self.setMaximumSize(450, 250)
        self.setVisible(True)  # Explicitly make visible

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # GroupBox container
        group = QGroupBox("Live Chart")
        group.setMaximumSize(450, 250)
        group.setMinimumSize(450, 250)

        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(4, 4, 4, 4)
        group_layout.setSpacing(2)

        # Header with symbol and enlarge button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self._symbol_label = QLabel("--")
        self._symbol_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        header_layout.addWidget(self._symbol_label)

        self._price_label = QLabel("--")
        self._price_label.setStyleSheet("font-size: 11px; color: #26a69a;")
        header_layout.addWidget(self._price_label)

        header_layout.addStretch()

        # Enlarge button
        self._enlarge_btn = QPushButton("🔍")
        self._enlarge_btn.setFixedSize(24, 24)
        self._enlarge_btn.setToolTip("Chart vergrößern")
        self._enlarge_btn.setStyleSheet(
            "font-size: 12px; padding: 0px; "
            "background-color: #2a2a2a; border: 1px solid #555; border-radius: 3px;"
        )
        self._enlarge_btn.clicked.connect(self._on_enlarge_clicked)
        header_layout.addWidget(self._enlarge_btn)

        group_layout.addLayout(header_layout)

        # Chart container
        chart_container = QWidget()
        chart_container.setMinimumHeight(200)
        chart_container.setMaximumHeight(200)
        chart_inner_layout = QVBoxLayout(chart_container)
        chart_inner_layout.setContentsMargins(0, 0, 0, 0)

        # Initialize lightweight chart
        if LIGHTWEIGHT_CHARTS_AVAILABLE:
            self._chart = QtChart(chart_container)

            # Chart Layout & Styling (matching reference)
            self._chart.layout(background_color='#1a1a2e', text_color='#ffffff')

            # Candlestick Styling
            self._chart.candle_style(
                up_color='#26a69a',
                down_color='#ef5350',
                border_up_color='#26a69a',
                border_down_color='#ef5350',
                wick_up_color='#26a69a',
                wick_down_color='#ef5350'
            )

            # Volume Histogram - bottom 25% of chart
            self._chart.volume_config(
                up_color='rgba(38, 166, 154, 0.6)',
                down_color='rgba(239, 83, 80, 0.6)',
                scale_margin_top=0.75,  # Volume in bottom 25%
                scale_margin_bottom=0.0
            )

            # Crosshair & Navigation
            self._chart.crosshair(mode='normal')
            self._chart.time_scale(right_offset=10, min_bar_spacing=3)

            # Legend
            self._chart.legend(visible=True, font_size=10)

            # Add chart webview to layout
            chart_inner_layout.addWidget(self._chart.get_webview())
        else:
            # Fallback if library not available - show installation instructions
            fallback_widget = QWidget()
            fallback_layout = QVBoxLayout(fallback_widget)
            fallback_layout.setContentsMargins(8, 20, 8, 8)

            error_label = QLabel("⚠️ lightweight-charts nicht installiert")
            error_label.setStyleSheet("color: #ef5350; font-size: 12px; font-weight: bold;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_layout.addWidget(error_label)

            install_label = QLabel("Bitte installieren:\npip install lightweight-charts>=2.0")
            install_label.setStyleSheet("color: #aaaaaa; font-size: 10px; margin-top: 10px;")
            install_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_layout.addWidget(install_label)

            fallback_layout.addStretch()
            chart_inner_layout.addWidget(fallback_widget)

        group_layout.addWidget(chart_container)

        group.setLayout(group_layout)
        layout.addWidget(group)

    def update_symbol(self, symbol: str) -> None:
        """Update displayed symbol.

        Args:
            symbol: Trading symbol (e.g., BTC/USD)
        """
        if hasattr(self, '_symbol_label') and self._symbol_label:
            self._symbol_label.setText(symbol)

    def update_chart_data(self, df: pd.DataFrame) -> None:
        """Update chart with OHLCV DataFrame.

        Args:
            df: DataFrame with columns: time, open, high, low, close, volume
        """
        if not LIGHTWEIGHT_CHARTS_AVAILABLE or self._chart is None:
            return

        if df is None or df.empty:
            logger.debug("No data to update compact chart")
            return

        try:
            # Ensure DataFrame has required columns
            required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"DataFrame missing required columns. Has: {df.columns.tolist()}")
                return

            # Update chart with latest data (last 100 candles for compact view)
            chart_df = df[required_cols].tail(100).copy()
            self._chart.set(chart_df)

            # Update price label with latest close
            if not chart_df.empty and hasattr(self, '_price_label') and self._price_label:
                latest_price = chart_df.iloc[-1]['close']
                self._price_label.setText(f"${latest_price:,.2f}")

            logger.debug(f"Updated compact chart with {len(chart_df)} candles")

        except Exception as e:
            logger.error(f"Failed to update compact chart: {e}", exc_info=True)

    def update_price(self, price: float) -> None:
        """Update current price display (backward compatibility).

        This method only updates the price label. For full chart functionality,
        use update_chart_data() with OHLCV DataFrame.

        Args:
            price: Current price
        """
        if price <= 0:
            return

        # Update price label only
        if hasattr(self, '_price_label') and self._price_label:
            self._price_label.setText(f"${price:,.2f}")

        # Try to fetch full chart data from parent if available
        if self._parent_chart:
            try:
                # Check if parent has chart data available
                if hasattr(self._parent_chart, 'chart_data'):
                    self.update_chart_data(self._parent_chart.chart_data)
                elif hasattr(self._parent_chart, 'df'):
                    self.update_chart_data(self._parent_chart.df)
            except Exception as e:
                logger.debug(f"Could not fetch chart data from parent: {e}")

    def clear_data(self) -> None:
        """Clear chart data."""
        if self._chart:
            try:
                # Clear by setting empty DataFrame
                empty_df = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                self._chart.set(empty_df)
            except Exception as e:
                logger.error(f"Failed to clear compact chart: {e}")

        if hasattr(self, '_price_label') and self._price_label:
            self._price_label.setText("--")

    def _on_enlarge_clicked(self) -> None:
        """Handle enlarge button click."""
        if not LIGHTWEIGHT_CHARTS_AVAILABLE:
            logger.warning("Cannot enlarge chart: lightweight-charts not available")
            return

        # Get current data from parent chart if available
        chart_data = None
        if self._parent_chart and hasattr(self._parent_chart, 'get_chart_data'):
            chart_data = self._parent_chart.get_chart_data()

        # Create enlarged dialog
        dialog = EnlargedChartDialog(
            chart_data=chart_data,
            symbol=self._symbol_label.text(),
            parent=self
        )
        dialog.exec()


class EnlargedChartDialog(QDialog):
    """Pop-up dialog showing enlarged chart with Lightweight Charts."""

    def __init__(
        self,
        chart_data: pd.DataFrame | None,
        symbol: str,
        parent: QWidget | None = None
    ):
        """Initialize enlarged chart dialog.

        Args:
            chart_data: OHLCV DataFrame to display
            symbol: Trading symbol
            parent: Parent widget
        """
        super().__init__(parent)

        self._chart_data = chart_data
        self._symbol = symbol
        self._chart = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup dialog UI."""
        self.setWindowTitle(f"Chart - {self._symbol}")
        self.setModal(False)
        self.resize(800, 600)

        # Window flags for resizing
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header
        header = QHBoxLayout()

        symbol_label = QLabel(self._symbol)
        symbol_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(symbol_label)

        if self._chart_data is not None and not self._chart_data.empty:
            current_price = self._chart_data.iloc[-1]['close']
            price_label = QLabel(f"${current_price:,.2f}")
            price_label.setStyleSheet("font-size: 14px; color: #26a69a;")
            header.addWidget(price_label)

        header.addStretch()

        close_btn = QPushButton("✕ Schließen")
        close_btn.setFixedHeight(28)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # Chart container
        chart_container = QWidget()
        chart_container.setMinimumSize(760, 520)
        chart_inner_layout = QVBoxLayout(chart_container)
        chart_inner_layout.setContentsMargins(0, 0, 0, 0)

        if LIGHTWEIGHT_CHARTS_AVAILABLE:
            # Create enlarged chart
            self._chart = QtChart(chart_container)

            # Apply same styling as compact chart
            self._chart.layout(background_color='#1a1a2e', text_color='#ffffff')

            self._chart.candle_style(
                up_color='#26a69a',
                down_color='#ef5350',
                border_up_color='#26a69a',
                border_down_color='#ef5350',
                wick_up_color='#26a69a',
                wick_down_color='#ef5350'
            )

            self._chart.volume_config(
                up_color='rgba(38, 166, 154, 0.6)',
                down_color='rgba(239, 83, 80, 0.6)',
                scale_margin_top=0.75,
                scale_margin_bottom=0.0
            )

            self._chart.crosshair(mode='normal')
            self._chart.time_scale(right_offset=15, min_bar_spacing=6)
            self._chart.legend(visible=True, font_size=12)

            # Set data if available
            if self._chart_data is not None and not self._chart_data.empty:
                self._chart.set(self._chart_data)

            chart_inner_layout.addWidget(self._chart.get_webview())
        else:
            error_label = QLabel("lightweight-charts nicht installiert")
            error_label.setStyleSheet("color: #ef5350;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chart_inner_layout.addWidget(error_label)

        layout.addWidget(chart_container)

        # Size grip for resizing
        size_grip = QSizeGrip(self)
        grip_layout = QHBoxLayout()
        grip_layout.addStretch()
        grip_layout.addWidget(size_grip)
        layout.addLayout(grip_layout)
