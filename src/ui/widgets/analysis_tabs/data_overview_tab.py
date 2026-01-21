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
        header.setProperty("class", "header")
        header_layout.addWidget(header)

        # Refresh button
        self.btn_refresh = QPushButton("🔄 Aktualisieren")
        self.btn_refresh.setProperty("class", "primary")
        self.btn_refresh.clicked.connect(self._refresh_data)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_refresh)

        layout.addLayout(header_layout)

        # Status bar
        self.status_label = QLabel("Keine Daten geladen")
        self.status_label.setProperty("class", "status-label")
        layout.addWidget(self.status_label)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        # Theme handles styling

        # Tree view for structured data
        tree_group = QGroupBox("Strukturierte Daten")
        # Theme handles styling
        tree_layout = QVBoxLayout(tree_group)

        self.data_tree = QTreeWidget()
        self.data_tree.setHeaderLabels(["Kategorie", "Wert", "Details"])
        self.data_tree.setAlternatingRowColors(True)
        # Theme handles styling
        self.data_tree.setColumnWidth(0, 200)
        self.data_tree.setColumnWidth(1, 150)
        tree_layout.addWidget(self.data_tree)

        splitter.addWidget(tree_group)

        # Raw JSON view
        json_group = QGroupBox("Rohdaten (JSON)")
        # Theme handles styling
        json_layout = QVBoxLayout(json_group)

        self.json_view = QTextEdit()
        self.json_view.setReadOnly(True)
        self.json_view.setFont(QFont("Consolas", 10))
        # Theme handles styling
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
        footer.setProperty("class", "info-label")
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

        # Collect each data type using helper methods
        data["strategy"] = self._collect_strategy_data()
        data["timeframes"] = self._collect_timeframes_data()
        self._merge_features_data(data)

        if self._market_context:
            data["market_context"] = self._collect_market_context_base()
            self._add_candle_summary(data["market_context"])
            data["indicators"] = self._collect_indicators_data()
            data["levels"] = self._collect_levels_data()
        else:
            logger.warning("No market context available for data overview")

        return data

    def _collect_strategy_data(self) -> dict:
        """Collect strategy information from context."""
        try:
            strategy = self.context.get_selected_strategy()
            if strategy:
                return {
                    "name": strategy.name,
                    "risk_reward": getattr(strategy, 'risk_reward', None),
                    "confluence_threshold": getattr(strategy, 'confluence_threshold', None),
                }
        except Exception as e:
            logger.debug(f"Could not get strategy: {e}")
        return {}

    def _collect_timeframes_data(self) -> dict:
        """Collect active timeframes from context."""
        try:
            timeframes = self.context.get_active_timeframes()
            if timeframes:
                return {
                    tf.tf: {
                        "role": tf.role,
                        "lookback": tf.lookback,
                    }
                    for tf in timeframes
                }
        except Exception as e:
            logger.debug(f"Could not get timeframes: {e}")
        return {}

    def _merge_features_data(self, data: dict) -> None:
        """Merge features from last analysis into data dict."""
        if not self._last_features:
            return

        for tf, features in self._last_features.items():
            if tf == 'chart_data':
                data["chart_data"] = features
            else:
                if tf not in data["timeframes"]:
                    data["timeframes"][tf] = {}
                data["timeframes"][tf]["features"] = features

    def _collect_market_context_base(self) -> dict:
        """Collect base market context information."""
        ctx = self._market_context
        context_data = {
            "symbol": ctx.symbol,
            "timeframe": ctx.timeframe,
            "regime": ctx.regime.value if hasattr(ctx.regime, 'value') else str(ctx.regime) if ctx.regime else None,
            "trend": ctx.trend.value if hasattr(ctx.trend, 'value') else str(ctx.trend) if ctx.trend else None,
        }
        logger.debug(f"Market context found: {ctx.symbol}, regime={ctx.regime}, trend={ctx.trend}")
        return context_data

    def _add_candle_summary(self, context_data: dict) -> None:
        """Add candle summary to market context if available."""
        if not self._market_context or not self._market_context.candle_summary:
            return

        cs = self._market_context.candle_summary
        context_data["candles"] = {
            "open": cs.open,
            "high": cs.high,
            "low": cs.low,
            "close": cs.close,
        }

    def _find_best_indicators(self):
        """Find best available indicators from market context.

        Returns:
            Indicator object or None
        """
        ctx = self._market_context
        if not ctx:
            return None

        # Try to get indicators from primary timeframe (priority order: 5m, 1h, 4h, 1d)
        for attr_name in ['indicators_5m', 'indicators_1h', 'indicators_4h', 'indicators_1d']:
            if hasattr(ctx, attr_name):
                ind = getattr(ctx, attr_name)
                if ind:
                    return ind
        return None

    def _collect_indicators_data(self) -> dict:
        """Collect indicator values from market context."""
        ind = self._find_best_indicators()
        if not ind:
            logger.warning("No indicators found in market context")
            return {}

        indicators = {
            "timeframe": ind.timeframe if hasattr(ind, 'timeframe') else "unknown",
            "rsi": ind.rsi_14 if hasattr(ind, 'rsi_14') else None,
            "atr": ind.atr_14 if hasattr(ind, 'atr_14') else None,
            "atr_percent": ind.atr_percent if hasattr(ind, 'atr_percent') else None,
            "adx": ind.adx_14 if hasattr(ind, 'adx_14') else None,
            "di_plus": ind.plus_di if hasattr(ind, 'plus_di') else None,
            "di_minus": ind.minus_di if hasattr(ind, 'minus_di') else None,
            "ema_fast": ind.ema_20 if hasattr(ind, 'ema_20') else None,
            "ema_slow": ind.ema_50 if hasattr(ind, 'ema_50') else None,
        }
        logger.debug(f"Indicators found from {indicators['timeframe']}: ADX={indicators['adx']}, DI+={indicators['di_plus']}, DI-={indicators['di_minus']}, ATR={indicators['atr']}")
        return indicators

    def _collect_levels_data(self) -> dict:
        """Collect support/resistance levels from market context."""
        ctx = self._market_context
        if not ctx or not ctx.levels or not ctx.levels.levels:
            return {}

        return {
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

    def _populate_tree(self, data: dict) -> None:
        """Populate the tree widget with data.

        Args:
            data: Data dictionary to display
        """
        # Add all sections
        self._add_strategy_section(data)
        self._add_timeframes_section(data)
        self._add_market_context_section(data)
        self._add_indicators_section(data)
        self._add_levels_section(data)
        self._add_chart_data_section(data)

    def _add_strategy_section(self, data: dict) -> None:
        """Add strategy section to tree.

        Args:
            data: Data dictionary containing strategy info.
        """
        if not data.get("strategy"):
            return

        strategy_item = QTreeWidgetItem(["📋 Strategie", "", ""])
        strategy_item.setExpanded(True)
        for key, value in data["strategy"].items():
            child = QTreeWidgetItem([str(key), str(value), ""])
            strategy_item.addChild(child)
        self.data_tree.addTopLevelItem(strategy_item)

    def _add_timeframes_section(self, data: dict) -> None:
        """Add timeframes section to tree.

        Args:
            data: Data dictionary containing timeframes info.
        """
        if not data.get("timeframes"):
            return

        tf_item = QTreeWidgetItem(["⏱️ Timeframes", f"{len(data['timeframes'])} aktiv", ""])
        tf_item.setExpanded(True)

        for tf_name, tf_data in data["timeframes"].items():
            tf_child = QTreeWidgetItem([tf_name, tf_data.get("role", ""), ""])
            tf_child.setExpanded(True)

            # Add features if available
            if "features" in tf_data:
                self._add_timeframe_features(tf_child, tf_data["features"])

            tf_item.addChild(tf_child)

        self.data_tree.addTopLevelItem(tf_item)

    def _add_timeframe_features(
        self, parent_item: QTreeWidgetItem, features: dict
    ) -> None:
        """Add timeframe features to parent tree item.

        Args:
            parent_item: Parent tree item to add features to.
            features: Dictionary of feature data.
        """
        for feat_key, feat_val in features.items():
            if isinstance(feat_val, (list, dict)):
                feat_child = QTreeWidgetItem([feat_key, f"{len(feat_val)} items", ""])
            else:
                feat_child = QTreeWidgetItem([feat_key, str(feat_val), ""])
            parent_item.addChild(feat_child)

    def _add_market_context_section(self, data: dict) -> None:
        """Add market context section to tree.

        Args:
            data: Data dictionary containing market context info.
        """
        if not data.get("market_context"):
            return

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

    def _add_indicators_section(self, data: dict) -> None:
        """Add indicators section to tree (Issue #37: Display all indicators including DI+/DI-).

        Args:
            data: Data dictionary containing indicators info.
        """
        if not data.get("indicators"):
            return

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
            self._add_indicator_item(ind_item, display_name, value)

        self.data_tree.addTopLevelItem(ind_item)

    def _add_indicator_item(
        self, parent_item: QTreeWidgetItem, display_name: str, value
    ) -> None:
        """Add indicator item to parent with proper formatting.

        Args:
            parent_item: Parent tree item.
            display_name: Display name for the indicator.
            value: Indicator value (can be None).
        """
        if value is not None:
            value_str = f"{value:.4f}" if isinstance(value, float) else str(value)
            child = QTreeWidgetItem([display_name, value_str, ""])
            parent_item.addChild(child)
        else:
            # Show indicator with "N/A" if not available
            child = QTreeWidgetItem([display_name, "N/A", ""])
            child.setForeground(1, QColor(128, 128, 128))  # Gray color for unavailable values
            parent_item.addChild(child)

    def _add_levels_section(self, data: dict) -> None:
        """Add support/resistance levels section to tree.

        Args:
            data: Data dictionary containing levels info.
        """
        if not (data.get("levels") and data["levels"].get("items")):
            return

        levels_item = QTreeWidgetItem([
            "🎯 Support/Resistance",
            f"{data['levels']['count']} Levels",
            ""
        ])
        levels_item.setExpanded(True)

        for lvl in data["levels"]["items"]:
            lvl_child = QTreeWidgetItem([
                lvl["type"],
                f"{lvl['price_low']:.2f} - {lvl['price_high']:.2f}",
                f"Stärke: {lvl.get('strength', 'N/A')}"
            ])
            levels_item.addChild(lvl_child)

        self.data_tree.addTopLevelItem(levels_item)

    def _add_chart_data_section(self, data: dict) -> None:
        """Add chart data section to tree (Issue #34: From active chart widget).

        Args:
            data: Data dictionary containing chart data.
        """
        if not data.get("chart_data"):
            return

        chart_item = QTreeWidgetItem(["📉 Chart Daten (Live)", "", ""])
        chart_item.setExpanded(True)

        for key, value in data["chart_data"].items():
            self._add_chart_data_item(chart_item, key, value)

        self.data_tree.addTopLevelItem(chart_item)

    def _add_chart_data_item(
        self, parent_item: QTreeWidgetItem, key: str, value
    ) -> None:
        """Add chart data item with appropriate formatting based on value type.

        Args:
            parent_item: Parent tree item.
            key: Data key.
            value: Data value (dict, list, or scalar).
        """
        if isinstance(value, dict):
            child = QTreeWidgetItem([str(key), "", ""])
            for sub_key, sub_val in value.items():
                sub_child = QTreeWidgetItem([sub_key, str(sub_val), ""])
                child.addChild(sub_child)
            parent_item.addChild(child)
        elif isinstance(value, list):
            preview = ", ".join(str(v) for v in value[:5])
            child = QTreeWidgetItem([str(key), f"{len(value)} items", preview])
            parent_item.addChild(child)
        else:
            child = QTreeWidgetItem([str(key), str(value), ""])
            parent_item.addChild(child)
