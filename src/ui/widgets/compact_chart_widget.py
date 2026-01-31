"""Compact Chart Widget for Trading Tab using Lightweight Charts.

Provides a small lightweight chart display (max 450px x 250px) with:
- Real-time OHLCV candlestick chart
- Volume hidden in compact view, shown in popup
- Pop-up enlargement functionality
- Integration with parent ChartWindow data
- Timeframe selection and Zoom support
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import pandas as pd

from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QSettings, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QDialog, QSizeGrip, QComboBox
)

from src.ui.icons import get_icon

try:
    from lightweight_charts.widgets import QtChart
    LIGHTWEIGHT_CHARTS_AVAILABLE = True
except Exception as exc:  # noqa: BLE001 - broad on purpose for CI environments
    LIGHTWEIGHT_CHARTS_AVAILABLE = False
    logging.warning(
        "lightweight-charts unavailable (%s). Compact chart will not be available.",
        exc,
    )

if TYPE_CHECKING:
    from src.ui.widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)


class CompactChartWidget(QWidget):
    """Compact chart widget for Trading tab using Lightweight Charts.

    Features:
        - Maximum size: 450px x 250px
        - QtChart with candlesticks
        - Click to enlarge in pop-up
        - Real-time OHLCV data updates
        - Timeframe selection (1m, 5m, 15m, 1h, 4h, 1d)
        - Zooming and Scrolling enabled
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
        self._last_raw_data: pd.DataFrame | None = None
        self._current_timeframe = "1h"  # Default timeframe

        if not LIGHTWEIGHT_CHARTS_AVAILABLE:
            logger.warning("lightweight-charts not installed. Widget will show installation instructions.")

        # Always setup UI - fallback will be shown if library unavailable
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup widget UI."""
        # Set widget size FIRST (critical for layout visibility)
        self.setMinimumSize(450, 250)
        self.setMaximumSize(450, 250)
        self.setVisible(True)

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

        # Header with symbol, controls and enlarge button
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)

        self._symbol_label = QLabel("--")
        self._symbol_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        header_layout.addWidget(self._symbol_label)

        self._price_label = QLabel("--")
        self._price_label.setStyleSheet("font-size: 11px; color: #26a69a;")
        header_layout.addWidget(self._price_label)

        header_layout.addStretch()

        # Timeframe Selector
        self._tf_combo = QComboBox()
        self._tf_combo.addItems(["1m", "5m", "15m", "1h", "4h", "1d"])
        self._tf_combo.setCurrentText(self._current_timeframe)
        self._tf_combo.setFixedWidth(50)
        self._tf_combo.setFixedHeight(22)
        self._tf_combo.setStyleSheet("""
            QComboBox {
                font-size: 10px;
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 3px;
                color: white;
                padding-left: 2px;
            }
            QComboBox::drop-down { border: none; width: 0px; }
        """)
        self._tf_combo.currentTextChanged.connect(self._on_timeframe_changed)
        header_layout.addWidget(self._tf_combo)

        # Refresh Button
        self._refresh_btn = QPushButton()
        self._refresh_btn.setIcon(get_icon("refresh"))
        self._refresh_btn.setIconSize(QtCore.QSize(16, 16))
        self._refresh_btn.setFixedSize(26, 22)
        self._refresh_btn.setToolTip("Chart aktualisieren")
        self._refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #3a3a3a; }
        """)
        self._refresh_btn.clicked.connect(self._on_refresh_clicked)
        header_layout.addWidget(self._refresh_btn)

        # Zoom All Button
        self._zoom_all_btn = QPushButton()
        self._zoom_all_btn.setIcon(get_icon("zoom_all"))
        self._zoom_all_btn.setIconSize(QtCore.QSize(16, 16))
        self._zoom_all_btn.setFixedSize(26, 22)
        self._zoom_all_btn.setToolTip("Alles zoomen")
        self._zoom_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #3a3a3a; }
        """)
        self._zoom_all_btn.clicked.connect(self._on_zoom_all_clicked)
        header_layout.addWidget(self._zoom_all_btn)

        # Enlarge button
        self._enlarge_btn = QPushButton()
        self._enlarge_btn.setIcon(get_icon("expand"))
        self._enlarge_btn.setIconSize(QtCore.QSize(16, 16))
        self._enlarge_btn.setFixedSize(26, 22)
        self._enlarge_btn.setToolTip("Chart vergrößern")
        self._enlarge_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #3a3a3a; }
        """)
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
            try:
                # Issue #18: QtChart only accepts widget parameter (no volume_enabled or toolbox)
                # Create chart - volume and toolbox must be configured via chart options after creation
                self._chart = QtChart(chart_container)
                self._apply_chart_styling(self._chart, font_size=10, show_volume=False)
                chart_inner_layout.addWidget(self._chart.get_webview())
            except Exception as e:
                logger.error(f"Failed to initialize QtChart: {e}")
                self._show_fallback(chart_inner_layout, f"Fehler bei Chart-Init: {e}")
        else:
            self._show_fallback(chart_inner_layout)

        group_layout.addWidget(chart_container)
        group.setLayout(group_layout)
        layout.addWidget(group)

    def resizeEvent(self, event) -> None:
        """Handle resize event to ensure chart fits."""
        super().resizeEvent(event)
        if self._chart:
            QtCore.QTimer.singleShot(200, self.fit_chart)

    def fit_chart(self):
        """Fit chart to view."""
        if self._chart:
            try:
                self._chart.fit()
            except Exception:
                pass

    def _show_fallback(self, layout: QVBoxLayout, message: str | None = None) -> None:
        """Show fallback widget if chart cannot be loaded."""
        fallback_widget = QWidget()
        fallback_layout = QVBoxLayout(fallback_widget)
        fallback_layout.setContentsMargins(8, 20, 8, 8)

        msg = message or "⚠️ lightweight-charts nicht installiert"
        error_label = QLabel(msg)
        error_label.setStyleSheet("color: #ef5350; font-size: 12px; font-weight: bold;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fallback_layout.addWidget(error_label)

        if not message:
            install_label = QLabel("Bitte installieren:\npip install lightweight-charts>=2.0")
            install_label.setStyleSheet("color: #aaaaaa; font-size: 10px; margin-top: 10px;")
            install_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback_layout.addWidget(install_label)

        fallback_layout.addStretch()
        layout.addWidget(fallback_widget)

    def _on_timeframe_changed(self, tf: str) -> None:
        """Handle timeframe change."""
        self._current_timeframe = tf
        if self._last_raw_data is not None:
            self.update_chart_data(self._last_raw_data)

    def _on_zoom_all_clicked(self) -> None:
        """Handle zoom all click."""
        if self._chart:
            try:
                self._chart.fit()
            except Exception as e:
                logger.error(f"Failed to fit chart: {e}")

    def _on_refresh_clicked(self) -> None:
        """Handle refresh click."""
        if self._parent_chart:
            if hasattr(self._parent_chart, 'get_chart_data'):
                data = self._parent_chart.get_chart_data()
                if data is not None and not data.empty:
                    self.update_chart_data(data)
            elif hasattr(self._parent_chart, 'df'):
                self.update_chart_data(self._parent_chart.df)

    @staticmethod
    def _apply_chart_styling(chart: QtChart, font_size: int, show_volume: bool = True) -> None:
        """Apply shared chart styling with user-configured colors."""
        bullish_color, bearish_color = CompactChartWidget._get_candle_colors()

        chart.layout(background_color='#0f1624', text_color='#ffffff')
        chart.candle_style(
            up_color=bullish_color,
            down_color=bearish_color,
            border_up_color=bullish_color,
            border_down_color=bearish_color,
            wick_up_color=bullish_color,
            wick_down_color=bearish_color
        )

        # Remove all built-in toolbars/overlays to match expected minimal UI
        CompactChartWidget._disable_chart_ui(chart)

        if show_volume:
            chart.volume_config(
                up_color=CompactChartWidget._format_rgba(bullish_color, 0.6),
                down_color=CompactChartWidget._format_rgba(bearish_color, 0.6),
                scale_margin_top=0.75,
                scale_margin_bottom=0.0
            )
        else:
            try:
                # Standard library may not have 'visible' param, so we push it out of view
                chart.volume_config(scale_margin_top=1.0, scale_margin_bottom=0.0)
            except:
                pass

        chart.crosshair(mode='normal')
        chart.time_scale(right_offset=5, min_bar_spacing=0.5, visible=True, time_visible=True)
        chart.legend(visible=False, font_size=font_size)

    @staticmethod
    def _disable_chart_ui(chart: QtChart) -> None:
        """Hide lightweight-charts toolbars/branding without breaking older versions."""
        try:
            if hasattr(chart, "toolbox"):
                chart.toolbox(visible=False)
            if hasattr(chart, "toolbar"):
                chart.toolbar(visible=False)
            if hasattr(chart, "toolbar_visible"):
                chart.toolbar_visible(False)
        except Exception:
            logger.debug("Could not hide chart toolbox/toolbar", exc_info=True)

        # Also hide watermark/logo if available
        try:
            chart.watermark(visible=False)
        except Exception:
            pass

        # Soft-disable grids to reduce visual noise (fails gracefully if unsupported)
        try:
            chart.grid(vert_enabled=False, horz_enabled=False)
        except Exception:
            try:
                chart.grid(visible=False)
            except Exception:
                pass

    @staticmethod
    def _get_candle_colors() -> tuple[str, str]:
        """Fetch candle colors from settings (fallback to defaults)."""
        settings = QSettings("OrderPilot", "TradingApp")

        # Get current theme to load theme-specific colors
        theme_name = settings.value("theme", "Dark Orange")
        t_key = theme_name.lower().replace(" ", "_")

        bullish = settings.value(f"{t_key}_chart_bullish_color", "#26a69a")
        bearish = settings.value(f"{t_key}_chart_bearish_color", "#ef5350")
        return bullish, bearish

    @staticmethod
    def _format_rgba(hex_color: str, alpha: float) -> str:
        """Convert hex color to rgba() string with given alpha."""
        color = hex_color.lstrip("#")
        if len(color) != 6:
            return f"rgba(38, 166, 154, {alpha})"
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"

    def _resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample OHLCV data to selected timeframe."""
        if df is None or df.empty:
            return df

        required = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required):
            return df

        data = df.copy()
        if "time" in data.columns:
            if pd.api.types.is_numeric_dtype(data["time"]):
                data.index = pd.to_datetime(data["time"], unit="s", utc=True)
            else:
                data.index = pd.to_datetime(data["time"], utc=True)
        elif not isinstance(data.index, pd.DatetimeIndex):
            try:
                data.index = pd.to_datetime(data.index, utc=True)
            except:
                return df

        if "volume" not in data.columns:
            data["volume"] = 0.0

        tf_map = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h", "1d": "1d"}
        freq = tf_map.get(timeframe, "1h")

        resampled = data.resample(freq).agg({
            "open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"
        }).dropna(subset=["open", "high", "low", "close"])

        if resampled.empty:
            return resampled

        resampled = resampled.reset_index()
        # Get datetime column name dynamically (could be 'index' or original index name like 'timestamp')
        datetime_col = resampled.columns[0]
        resampled["time"] = (resampled[datetime_col].astype("int64") // 10**9).astype(int)
        return resampled[["time", "open", "high", "low", "close", "volume"]]

    def _calculate_bar_spacing(self, num_bars: int) -> float:
        """Calculate optimal bar spacing based on data count."""
        if num_bars <= 0:
            return 0.5

        # Approximate chart width (minus axis/padding)
        chart_width = self.width() - 50
        if chart_width <= 0:
            chart_width = 400

        spacing = chart_width / num_bars
        # Clamp spacing to reasonable limits (lightweight-charts constraints)
        return max(0.1, min(spacing, 50.0))

    def update_symbol(self, symbol: str) -> None:
        """Update displayed symbol."""
        if hasattr(self, '_symbol_label') and self._symbol_label:
            self._symbol_label.setText(symbol)

    def update_chart_data(self, df: pd.DataFrame) -> None:
        """Update chart with OHLCV DataFrame."""
        if not LIGHTWEIGHT_CHARTS_AVAILABLE or self._chart is None:
            return

        if df is None or df.empty:
            return

        self._last_raw_data = df

        try:
            chart_df = self._resample_data(df, self._current_timeframe)
            if chart_df is None or chart_df.empty:
                return

            self._chart.set(chart_df)
            spacing = self._calculate_bar_spacing(len(chart_df))
            self._chart.time_scale(right_offset=5, min_bar_spacing=spacing)

            QtCore.QTimer.singleShot(100, self.fit_chart)

            if not chart_df.empty and hasattr(self, '_price_label') and self._price_label:
                latest_price = chart_df.iloc[-1]['close']
                self._price_label.setText(f"${latest_price:,.2f}")

        except Exception as e:
            logger.error(f"Failed to update compact chart: {e}", exc_info=True)

    def update_price(self, price: float) -> None:
        """Update current price display."""
        if price <= 0:
            return
        if hasattr(self, '_price_label') and self._price_label:
            self._price_label.setText(f"${price:,.2f}")
        if self._parent_chart and self._last_raw_data is None:
            self._on_refresh_clicked()

    def clear_data(self) -> None:
        """Clear chart data."""
        if self._chart:
            try:
                empty_df = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                self._chart.set(empty_df)
            except Exception as e:
                logger.error(f"Failed to clear compact chart: {e}")
        if hasattr(self, '_price_label') and self._price_label:
            self._price_label.setText("--")
        self._last_raw_data = None

    def _on_enlarge_clicked(self) -> None:
        """Handle enlarge button click."""
        if not LIGHTWEIGHT_CHARTS_AVAILABLE:
            return
        chart_data = self._last_raw_data
        if chart_data is None and self._parent_chart and hasattr(self._parent_chart, 'get_chart_data'):
            chart_data = self._parent_chart.get_chart_data()
        dialog = EnlargedChartDialog(chart_data=chart_data, symbol=self._symbol_label.text(), parent=self)
        dialog.exec()


class EnlargedChartDialog(QDialog):
    """Pop-up dialog showing enlarged chart with Lightweight Charts."""

    def __init__(self, chart_data: pd.DataFrame | None, symbol: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._chart_data = chart_data
        self._symbol = symbol
        self._chart = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle(f"Chart - {self._symbol}")
        self.setModal(False)
        self.resize(800, 600)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint |
                           Qt.WindowType.WindowMaximizeButtonHint | Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

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

        chart_container = QWidget()
        chart_container.setMinimumSize(760, 520)
        chart_inner_layout = QVBoxLayout(chart_container)
        chart_inner_layout.setContentsMargins(0, 0, 0, 0)

        if LIGHTWEIGHT_CHARTS_AVAILABLE:
            self._chart = QtChart(chart_container)
            CompactChartWidget._apply_chart_styling(self._chart, font_size=12, show_volume=True)
            if self._chart_data is not None and not self._chart_data.empty:
                self._chart.set(self._chart_data)
            chart_inner_layout.addWidget(self._chart.get_webview())
        else:
            error_label = QLabel("lightweight-charts nicht installiert")
            error_label.setStyleSheet("color: #ef5350;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chart_inner_layout.addWidget(error_label)

        layout.addWidget(chart_container)
        size_grip = QSizeGrip(self)
        grip_layout = QHBoxLayout()
        grip_layout.addStretch()
        grip_layout.addWidget(size_grip)
        layout.addLayout(grip_layout)
