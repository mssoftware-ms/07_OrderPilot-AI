"""Tab for KI Data Overview - shows all data sent to AI analysis.

This tab displays the data that will be/was sent to the AI for analysis,
allowing users to verify and inspect the input data.
"""

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTreeWidget, QTreeWidgetItem, QSplitter,
    QGroupBox, QScrollArea, QFrame,
)
from PyQt6.QtGui import QFont, QColor

if TYPE_CHECKING:
    from src.core.analysis.context import AnalysisContext
    from src.core.trading_bot.market_context import MarketContext

logger = logging.getLogger(__name__)


class DataOverviewTab(QWidget):
    """Tab displaying all data sent to AI for analysis.

    Shows:
    - Strategy configuration
    - Active timeframes and their data
    - Technical indicators
    - Support/Resistance levels
    - Market context summary
    """

    def __init__(self, context: "AnalysisContext"):
        super().__init__()
        self.context = context
        self._market_context: Optional["MarketContext"] = None
        self._last_features: dict = {}
        self._setup_ui()

    def _setup_ui(self):
        """Setup the data overview UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("📊 KI-Datenübersicht")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2196F3;")
        header_layout.addWidget(header)

        # Refresh button
        self.btn_refresh = QPushButton("🔄 Aktualisieren")
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.btn_refresh.clicked.connect(self._refresh_data)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_refresh)

        layout.addLayout(header_layout)

        # Status bar
        self.status_label = QLabel("Keine Daten geladen")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        layout.addWidget(self.status_label)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background-color: #333; }")

        # Tree view for structured data
        tree_group = QGroupBox("Strukturierte Daten")
        tree_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        tree_layout = QVBoxLayout(tree_group)

        self.data_tree = QTreeWidget()
        self.data_tree.setHeaderLabels(["Kategorie", "Wert", "Details"])
        self.data_tree.setAlternatingRowColors(True)
        self.data_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                color: #ddd;
                border: 1px solid #333;
                border-radius: 3px;
            }
            QTreeWidget::item:alternate {
                background-color: #252525;
            }
            QTreeWidget::item:selected {
                background-color: #2196F3;
            }
        """)
        self.data_tree.setColumnWidth(0, 200)
        self.data_tree.setColumnWidth(1, 150)
        tree_layout.addWidget(self.data_tree)

        splitter.addWidget(tree_group)

        # Raw JSON view
        json_group = QGroupBox("Rohdaten (JSON)")
        json_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        json_layout = QVBoxLayout(json_group)

        self.json_view = QTextEdit()
        self.json_view.setReadOnly(True)
        self.json_view.setFont(QFont("Consolas", 10))
        self.json_view.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ddd;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 10px;
            }
        """)
        self.json_view.setPlaceholderText(
            "Hier werden die Rohdaten angezeigt, die an die KI gesendet werden...\n\n"
            "Klicken Sie auf 'Aktualisieren', um die aktuellen Daten zu laden."
        )
        json_layout.addWidget(self.json_view)

        splitter.addWidget(json_group)

        # Set initial sizes
        splitter.setSizes([400, 300])

        layout.addWidget(splitter, stretch=1)

        # Footer
        footer = QLabel(
            "💡 Diese Übersicht zeigt alle Daten, die zur Analyse an die KI gesendet werden. "
            "Nutzen Sie diese zur Überprüfung der Datenqualität."
        )
        footer.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        footer.setWordWrap(True)
        layout.addWidget(footer)

    def set_market_context(self, context: "MarketContext") -> None:
        """Set the MarketContext for data display.

        Args:
            context: MarketContext instance
        """
        self._market_context = context
        self._refresh_data()

    def set_features(self, features: dict) -> None:
        """Set the features data from Deep Analysis.

        Args:
            features: Dictionary of timeframe -> feature data
        """
        self._last_features = features
        self._refresh_data()

    def _refresh_data(self) -> None:
        """Refresh the data display.

        Issue #34: Actively fetch data from chart widget if available.
        """
        self.data_tree.clear()

        # Try to get chart data if not already set
        self._try_fetch_chart_data()

        data = self._collect_all_data()

        # Check if data has any actual content
        has_content = (
            data.get("strategy")
            or data.get("timeframes")
            or (data.get("market_context") and len(data["market_context"]) > 1)
            or data.get("indicators")
            or data.get("levels")
            or data.get("chart_data")  # Issue #34: Include chart data
        )

        if not has_content:
            self.status_label.setText(
                "⚠️ Keine Daten verfügbar. Bitte öffnen Sie einen Chart und starten Sie eine Analyse."
            )
            self.status_label.setStyleSheet("color: #FFA500; padding: 5px;")
            # Still show the (mostly empty) data structure
            self.json_view.setText(json.dumps(data, indent=2, ensure_ascii=False, default=str))
            return

        # Populate tree
        self._populate_tree(data)

        # Show JSON
        self.json_view.setText(json.dumps(data, indent=2, ensure_ascii=False, default=str))

        # Update status
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_label.setText(f"✅ Daten aktualisiert um {timestamp}")
        self.status_label.setStyleSheet("color: #4CAF50; padding: 5px;")

    def _try_fetch_chart_data(self) -> None:
        """Try to fetch data from the chart widget (Issue #34).

        This attempts to get live data from the chart if no context is set.
        """
        # Skip if we already have market context
        if self._market_context:
            return

        try:
            # Try to get chart widget from parent hierarchy
            from PyQt6.QtWidgets import QApplication
            main_window = None
            for widget in QApplication.topLevelWidgets():
                if hasattr(widget, 'chart_widget'):
                    main_window = widget
                    break

            if not main_window:
                return

            chart = getattr(main_window, 'chart_widget', None)
            if not chart:
                return

            # Build a simple context from chart data
            chart_data = {}

            if hasattr(chart, 'current_symbol'):
                chart_data['symbol'] = chart.current_symbol
            if hasattr(chart, 'current_timeframe'):
                chart_data['timeframe'] = chart.current_timeframe
            if hasattr(chart, 'data') and chart.data is not None and len(chart.data) > 0:
                df = chart.data
                chart_data['candles'] = {
                    'count': len(df),
                    'latest_close': float(df.iloc[-1].get('close', 0)) if 'close' in df.columns else None,
                    'latest_time': str(df.iloc[-1].get('time', '')) if 'time' in df.columns else None,
                }
            if hasattr(chart, 'active_indicators'):
                chart_data['active_indicators'] = list(chart.active_indicators.keys())

            # Store as pseudo market context if we have useful data
            if chart_data:
                self._last_features['chart_data'] = chart_data
                logger.info(f"Fetched chart data: {chart_data}")

        except Exception as e:
            logger.debug(f"Could not fetch chart data: {e}")

    def _collect_all_data(self) -> dict:
        """Collect all data that would be sent to AI.

        Returns:
            Dictionary with all data categories
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "strategy": {},
            "timeframes": {},
            "indicators": {},
            "levels": {},
            "market_context": {},
        }

        # Strategy info from context
        try:
            strategy = self.context.get_selected_strategy()
            if strategy:
                data["strategy"] = {
                    "name": strategy.name,
                    "risk_reward": getattr(strategy, 'risk_reward', None),
                    "confluence_threshold": getattr(strategy, 'confluence_threshold', None),
                }
        except Exception as e:
            logger.debug(f"Could not get strategy: {e}")

        # Timeframes from context
        try:
            timeframes = self.context.get_active_timeframes()
            if timeframes:
                data["timeframes"] = {
                    tf.tf: {
                        "role": tf.role,
                        "lookback": tf.lookback,
                    }
                    for tf in timeframes
                }
        except Exception as e:
            logger.debug(f"Could not get timeframes: {e}")

        # Features from last analysis
        if self._last_features:
            for tf, features in self._last_features.items():
                if tf == 'chart_data':
                    # Chart data from _try_fetch_chart_data (Issue #34)
                    data["chart_data"] = features
                else:
                    if tf not in data["timeframes"]:
                        data["timeframes"][tf] = {}
                    data["timeframes"][tf]["features"] = features

        # Market context
        if self._market_context:
            ctx = self._market_context
            data["market_context"] = {
                "symbol": ctx.symbol,
                "timeframe": ctx.timeframe,
                "regime": ctx.regime.value if hasattr(ctx.regime, 'value') else str(ctx.regime) if ctx.regime else None,
                "trend": ctx.trend.value if hasattr(ctx.trend, 'value') else str(ctx.trend) if ctx.trend else None,
            }

            logger.debug(f"Market context found: {ctx.symbol}, regime={ctx.regime}, trend={ctx.trend}")

            # Candle summary
            if ctx.candle_summary:
                cs = ctx.candle_summary
                data["market_context"]["candles"] = {
                    "open": cs.open,
                    "high": cs.high,
                    "low": cs.low,
                    "close": cs.close,
                }

            # Indicators - Issue #37: Ensure all indicator values are displayed
            # Try to get indicators from the primary timeframe (usually 5m)
            ind = None
            if hasattr(ctx, 'indicators_5m') and ctx.indicators_5m:
                ind = ctx.indicators_5m
            elif hasattr(ctx, 'indicators_1h') and ctx.indicators_1h:
                ind = ctx.indicators_1h
            elif hasattr(ctx, 'indicators_4h') and ctx.indicators_4h:
                ind = ctx.indicators_4h
            elif hasattr(ctx, 'indicators_1d') and ctx.indicators_1d:
                ind = ctx.indicators_1d

            if ind:
                data["indicators"] = {
                    "timeframe": ind.timeframe if hasattr(ind, 'timeframe') else "unknown",
                    "rsi": ind.rsi_14 if hasattr(ind, 'rsi_14') else None,
                    "atr": ind.atr_14 if hasattr(ind, 'atr_14') else None,
                    "atr_percent": ind.atr_percent if hasattr(ind, 'atr_percent') else None,
                    "adx": ind.adx_14 if hasattr(ind, 'adx_14') else None,
                    "di_plus": ind.plus_di if hasattr(ind, 'plus_di') else None,  # DI+ (Plus Directional Indicator)
                    "di_minus": ind.minus_di if hasattr(ind, 'minus_di') else None,  # DI- (Minus Directional Indicator)
                    "ema_fast": ind.ema_20 if hasattr(ind, 'ema_20') else None,
                    "ema_slow": ind.ema_50 if hasattr(ind, 'ema_50') else None,
                }
                logger.debug(f"Indicators found from {ind.timeframe}: ADX={data['indicators']['adx']}, DI+={data['indicators']['di_plus']}, DI-={data['indicators']['di_minus']}, ATR={data['indicators']['atr']}")
            else:
                logger.warning("No indicators found in market context")

            # Levels
            if ctx.levels and ctx.levels.levels:
                data["levels"] = {
                    "count": len(ctx.levels.levels),
                    "items": [
                        {
                            "type": lvl.level_type.value if hasattr(lvl.level_type, 'value') else str(lvl.level_type),
                            "price_low": lvl.price_low,
                            "price_high": lvl.price_high,
                            "strength": lvl.strength,
                        }
                        for lvl in ctx.levels.levels[:10]  # Limit to 10
                    ]
                }
        else:
            logger.warning("No market context available for data overview")

        return data

    def _populate_tree(self, data: dict) -> None:
        """Populate the tree widget with data.

        Args:
            data: Data dictionary to display
        """
        # Strategy section
        if data.get("strategy"):
            strategy_item = QTreeWidgetItem(["📋 Strategie", "", ""])
            strategy_item.setExpanded(True)
            for key, value in data["strategy"].items():
                child = QTreeWidgetItem([str(key), str(value), ""])
                strategy_item.addChild(child)
            self.data_tree.addTopLevelItem(strategy_item)

        # Timeframes section
        if data.get("timeframes"):
            tf_item = QTreeWidgetItem(["⏱️ Timeframes", f"{len(data['timeframes'])} aktiv", ""])
            tf_item.setExpanded(True)
            for tf_name, tf_data in data["timeframes"].items():
                tf_child = QTreeWidgetItem([tf_name, tf_data.get("role", ""), ""])
                tf_child.setExpanded(True)

                # Add features if available
                if "features" in tf_data:
                    for feat_key, feat_val in tf_data["features"].items():
                        if isinstance(feat_val, (list, dict)):
                            feat_child = QTreeWidgetItem([feat_key, f"{len(feat_val)} items", ""])
                        else:
                            feat_child = QTreeWidgetItem([feat_key, str(feat_val), ""])
                        tf_child.addChild(feat_child)

                tf_item.addChild(tf_child)
            self.data_tree.addTopLevelItem(tf_item)

        # Market Context section
        if data.get("market_context"):
            mc_item = QTreeWidgetItem(["📈 Market Context", "", ""])
            mc_item.setExpanded(True)
            for key, value in data["market_context"].items():
                if isinstance(value, dict):
                    child = QTreeWidgetItem([str(key), "", ""])
                    for sub_key, sub_val in value.items():
                        sub_child = QTreeWidgetItem([sub_key, str(sub_val), ""])
                        child.addChild(sub_child)
                    mc_item.addChild(child)
                else:
                    child = QTreeWidgetItem([str(key), str(value), ""])
                    mc_item.addChild(child)
            self.data_tree.addTopLevelItem(mc_item)

        # Indicators section - Issue #37: Display all indicators including DI+/DI-
        if data.get("indicators"):
            timeframe = data["indicators"].get("timeframe", "unknown")
            ind_item = QTreeWidgetItem(["📊 Indikatoren", f"Timeframe: {timeframe}", ""])
            ind_item.setExpanded(True)

            # Define display names for better readability
            indicator_names = {
                "timeframe": "Timeframe",
                "rsi": "RSI (14)",
                "atr": "ATR (14)",
                "atr_percent": "ATR %",
                "adx": "ADX (14)",
                "di_plus": "DI+ (Plus Directional Indicator)",
                "di_minus": "DI- (Minus Directional Indicator)",
                "ema_fast": "EMA Fast (20)",
                "ema_slow": "EMA Slow (50)"
            }

            for key, value in data["indicators"].items():
                # Skip timeframe as it's already shown in the parent
                if key == "timeframe":
                    continue

                display_name = indicator_names.get(key, key)
                if value is not None:
                    value_str = f"{value:.4f}" if isinstance(value, float) else str(value)
                    child = QTreeWidgetItem([display_name, value_str, ""])
                    ind_item.addChild(child)
                else:
                    # Show indicator with "N/A" if not available
                    child = QTreeWidgetItem([display_name, "N/A", ""])
                    child.setForeground(1, QColor(128, 128, 128))  # Gray color for unavailable values
                    ind_item.addChild(child)
            self.data_tree.addTopLevelItem(ind_item)

        # Levels section
        if data.get("levels") and data["levels"].get("items"):
            levels_item = QTreeWidgetItem(["🎯 Support/Resistance", f"{data['levels']['count']} Levels", ""])
            levels_item.setExpanded(True)
            for lvl in data["levels"]["items"]:
                lvl_child = QTreeWidgetItem([
                    lvl["type"],
                    f"{lvl['price_low']:.2f} - {lvl['price_high']:.2f}",
                    f"Stärke: {lvl.get('strength', 'N/A')}"
                ])
                levels_item.addChild(lvl_child)
            self.data_tree.addTopLevelItem(levels_item)

        # Chart Data section (Issue #34: From active chart widget)
        if data.get("chart_data"):
            chart_item = QTreeWidgetItem(["📉 Chart Daten (Live)", "", ""])
            chart_item.setExpanded(True)
            for key, value in data["chart_data"].items():
                if isinstance(value, dict):
                    child = QTreeWidgetItem([str(key), "", ""])
                    for sub_key, sub_val in value.items():
                        sub_child = QTreeWidgetItem([sub_key, str(sub_val), ""])
                        child.addChild(sub_child)
                    chart_item.addChild(child)
                elif isinstance(value, list):
                    child = QTreeWidgetItem([str(key), f"{len(value)} items", ", ".join(str(v) for v in value[:5])])
                    chart_item.addChild(child)
                else:
                    child = QTreeWidgetItem([str(key), str(value), ""])
                    chart_item.addChild(child)
            self.data_tree.addTopLevelItem(chart_item)
