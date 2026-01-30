"""
CEL Function Palette Widget.

Provides a categorized, searchable palette of CEL functions and indicators
that can be inserted into the CEL editor.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTreeWidget, QTreeWidgetItem, QPushButton,
    QGroupBox, QTextEdit
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

if TYPE_CHECKING:
    pass


class CelFunctionPalette(QWidget):
    """Draggable palette of CEL functions and indicators."""

    function_selected = pyqtSignal(str, str)  # name, code_snippet

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._populate_tree()

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Header
        header = QLabel("<b>CEL Function Palette</b>")
        layout.addWidget(header)

        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter functions...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Function tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Function"])
        self.tree.setColumnCount(1)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)

        # Description panel
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)

        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMaximumHeight(100)
        font = QFont("Consolas", 9)
        self.desc_text.setFont(font)
        desc_layout.addWidget(self.desc_text)

        layout.addWidget(desc_group)

        # Insert button
        self.insert_btn = QPushButton("↑ Insert at Cursor")
        self.insert_btn.setEnabled(False)
        self.insert_btn.clicked.connect(self._on_insert_clicked)
        layout.addWidget(self.insert_btn)

    def _populate_tree(self):
        """Populate function tree."""
        self.tree.clear()

        # Categories with functions
        categories = {
            "Indicators": [
                ("RSI", "rsi14.value", "Relative Strength Index (0-100)"),
                ("EMA", "ema34.value", "Exponential Moving Average"),
                ("MACD", "macd_12_26_9.value", "MACD value"),
                ("MACD Signal", "macd_12_26_9.signal", "MACD signal line"),
                ("Stochastic K", "stoch_5_3_3.k", "Stochastic %K"),
                ("Stochastic D", "stoch_5_3_3.d", "Stochastic %D"),
                ("ADX", "adx14.value", "Average Directional Index"),
                ("ATR", "atr14.value", "Average True Range"),
                ("BB Upper", "bb_20_2.upper", "Bollinger Band upper"),
                ("BB Lower", "bb_20_2.lower", "Bollinger Band lower"),
                ("Volume Ratio", "volume_ratio_20.value", "Volume vs. average"),
            ],

            "Math Functions": [
                ("Absolute", "abs(value)", "Absolute value"),
                ("Minimum", "min(a, b)", "Minimum of two values"),
                ("Maximum", "max(a, b)", "Maximum of two values"),
                ("Round", "round(value, 2)", "Round to decimals"),
                ("Floor", "floor(value)", "Round down"),
                ("Ceil", "ceil(value)", "Round up"),
                ("Square Root", "sqrt(value)", "Square root"),
                ("Power", "pow(x, y)", "x to the power of y"),
                ("Exp", "exp(value)", "e^x"),
            ],

            "Trading Functions": [
                ("Is Trade Open", "is_trade_open(trade)", "Check if trade is open"),
                ("Is Long", "is_long(trade)", "Check if trade is long"),
                ("Is Short", "is_short(trade)", "Check if trade is short"),
                ("Bullish Bias", "is_bullish_signal(strategy)", "Check bullish bias"),
                ("Bearish Bias", "is_bearish_signal(strategy)", "Check bearish bias"),
                ("In Regime", "in_regime(regime, 'R1')", "Regime match"),
                ("Stop Hit Long", "stop_hit_long(trade, price)", "Long stop hit"),
                ("Stop Hit Short", "stop_hit_short(trade, price)", "Short stop hit"),
                ("Take Profit Hit", "tp_hit(trade, price)", "Take profit hit"),
                ("Price Above EMA", "price_above_ema(price, ema)", "Price > EMA"),
                ("Price Below EMA", "price_below_ema(price, ema)", "Price < EMA"),
                ("Price Above Level", "price_above_level(price, level)", "Price > level"),
                ("Price Below Level", "price_below_level(price, level)", "Price < level"),
                ("Pct Change", "pct_change(old, new)", "Percent change"),
                ("Pct From Level", "pct_from_level(price, level)", "Percent distance to level"),
                ("Level At Pct", "level_at_pct(entry, 2.5, 'long')", "Level at percent"),
                ("Retracement", "retracement(from, to, 0.618)", "Retracement level"),
                ("Extension", "extension(from, to, 1.618)", "Extension level"),
            ],
            "Pattern Functions": [
                ("Pin Bar Bullish", "pin_bar_bullish()", "Bullish pin bar detected"),
                ("Pin Bar Bearish", "pin_bar_bearish()", "Bearish pin bar detected"),
                ("Inside Bar", "inside_bar()", "Inside bar detected"),
                ("Inverted Hammer", "inverted_hammer()", "Inverted hammer detected"),
                ("Bull Flag", "bull_flag()", "Bull flag pattern"),
                ("Bear Flag", "bear_flag()", "Bear flag pattern"),
                ("Cup and Handle", "cup_and_handle()", "Cup and handle pattern"),
                ("Double Bottom", "double_bottom()", "Double bottom pattern"),
                ("Double Top", "double_top()", "Double top pattern"),
                ("Ascending Triangle", "ascending_triangle()", "Ascending triangle pattern"),
                ("Descending Triangle", "descending_triangle()", "Descending triangle pattern"),
            ],
            "Breakout Functions": [
                ("Breakout Above", "breakout_above()", "Breakout above level/pivot"),
                ("Breakdown Below", "breakdown_below()", "Breakdown below level/pivot"),
                ("False Breakout", "false_breakout()", "False breakout detected"),
                ("Break of Structure", "break_of_structure()", "BOS detected"),
            ],
            "Regime Functions": [
                ("Trigger Regime Analysis", "trigger_regime_analysis()", "Trigger regime detection on chart (updates regime badge & draws lines)"),
                ("Last Closed Regime", "last_closed_regime()", "Get regime name from previous candle (e.g. 'STRONG_BULL')"),
                ("Current Regime", "regime", "Current regime name string (e.g. 'STRONG_BULL')"),
                ("Side Variable", "side", "Trade side: 'long' or 'short' - REQUIRED in entry_expression!"),
                ("Side is Long", "side == 'long'", "Check if evaluating long entry"),
                ("Side is Short", "side == 'short'", "Check if evaluating short entry"),
            ],
            "SMC Functions": [
                ("Liquidity Swept", "liquidity_swept()", "Liquidity sweep detected"),
                ("FVG Exists", "fvg_exists()", "Fair Value Gap detected"),
                ("Order Block Retest", "order_block_retest()", "Order block retest"),
                ("Harmonic Pattern", "harmonic_pattern_detected()", "Harmonic pattern detected"),
            ],

            "Logic & Comparison": [
                ("Equal", "==", "Equal to"),
                ("Not Equal", "!=", "Not equal to"),
                ("Greater Than", ">", "Greater than"),
                ("Less Than", "<", "Less than"),
                ("Greater or Equal", ">=", "Greater than or equal"),
                ("Less or Equal", "<=", "Less than or equal"),
                ("AND", "&&", "Logical AND"),
                ("OR", "||", "Logical OR"),
                ("NOT", "!", "Logical NOT"),
                ("In Array", "in", "Element in array"),
            ],

            "Null Handling": [
                ("Is Null", "isnull(value)", "Check if value is null"),
                ("Null Replace", "nz(value, default)", "Replace null with default"),
                ("Coalesce", "coalesce(a, b, c)", "First non-null value"),
                ("Clamp", "clamp(value, min, max)", "Constrain value to range"),
            ],

            "Array Functions": [
                ("Has", "has(array, element)", "Array contains element"),
                ("Size", "size(array)", "Array length"),
                ("First", "first(array)", "First element"),
                ("Last", "last(array)", "Last element"),
                ("All", "all(array, condition)", "All elements match"),
                ("Any", "any(array, condition)", "Any element matches"),
                ("Filter", "filter(array, condition)", "Filter by condition"),
                ("Map", "map(array, expr)", "Transform each element"),
                ("Index Of", "indexOf(array, element)", "Index of element"),
                ("Slice", "slice(array, 0, 3)", "Slice array"),
                ("Distinct", "distinct(array)", "Unique elements"),
                ("Sort", "sort(array)", "Sort array"),
                ("Reverse", "reverse(array)", "Reverse array"),
            ],

            "Trade Variables": [
                ("Entry Price", "trade.entry_price", "Trade entry price"),
                ("Current Price", "trade.current_price", "Current market price"),
                ("Stop Price", "trade.stop_price", "Current stop loss"),
                ("PnL %", "trade.pnl_pct", "Profit/Loss in percent"),
                ("PnL USDT", "trade.pnl_usdt", "Profit/Loss in USDT"),
                ("Side", "trade.side", "Trade side (long/short)"),
                ("Leverage", "trade.leverage", "Trade leverage"),
                ("Fees %", "trade.fees_pct", "Fees in percent"),
                ("Trailing Stop", "trade.tr_stop_price", "Trailing stop price"),
                ("Bars in Trade", "trade.bars_in_trade", "Bars since entry"),
            ],

            "Market Variables": [
                ("Close", "close", "Current close price"),
                ("Open", "open", "Current open price"),
                ("High", "high", "Current high price"),
                ("Low", "low", "Current low price"),
                ("Volume", "volume", "Current volume"),
                ("ATR %", "atrp", "ATR in percent"),
                ("Regime", "regime", "Market regime (R0, R1, etc.)"),
                ("Direction", "direction", "Trend direction (UP/DOWN/NONE)"),
                ("Squeeze On", "squeeze_on", "Bollinger squeeze active"),
            ],

            "Config Variables": [
                ("Min Volume Percentile", "cfg.min_volume_pctl", "Minimum volume percentile"),
                ("Min ATR %", "cfg.min_atrp_pct", "Minimum ATR percent"),
                ("Max ATR %", "cfg.max_atrp_pct", "Maximum ATR percent"),
                ("Max Leverage", "cfg.max_leverage", "Maximum allowed leverage"),
                ("Max Fees %", "cfg.max_fees_pct", "Maximum fee percent"),
                ("No Trade Regimes", "cfg.no_trade_regimes", "Blocked regimes array"),
            ],
        }

        # Store items for search
        self.all_items = []

        # Add categories and items
        for category_name, functions in categories.items():
            category_item = QTreeWidgetItem(self.tree, [category_name])
            category_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
            category_item.setExpanded(False)

            for name, code, description in functions:
                func_item = QTreeWidgetItem(category_item, [name])
                func_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'name': name,
                    'code': code,
                    'description': description
                })
                self.all_items.append(func_item)

    def _on_search_changed(self, text: str):
        """Filter functions by search text."""
        search_lower = text.lower()

        # Show/hide items based on search
        for item in self.all_items:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            name = data['name'].lower()
            code = data['code'].lower()
            desc = data['description'].lower()

            # Match if search is in name, code, or description
            matches = (search_lower in name or
                      search_lower in code or
                      search_lower in desc)

            item.setHidden(not matches)

            # Expand parent if child matches
            if matches:
                parent = item.parent()
                if parent:
                    parent.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click - show description."""
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data:
            # Category clicked
            self.desc_text.clear()
            self.insert_btn.setEnabled(False)
            return

        # Function clicked - show description
        desc_html = f"""
        <p><b>{data['name']}</b></p>
        <p><code style="color: #4ec9b0;">{data['code']}</code></p>
        <p>{data['description']}</p>
        """

        self.desc_text.setHtml(desc_html)
        self.insert_btn.setEnabled(True)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click - insert function."""
        self._on_insert_clicked()

    def _on_insert_clicked(self):
        """Insert selected function into editor."""
        current = self.tree.currentItem()
        if not current:
            return

        data = current.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        # Emit signal with function code
        self.function_selected.emit(data['name'], data['code'])
