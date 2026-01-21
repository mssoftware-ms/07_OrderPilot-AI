"""CEL Strategy Editor Widget - Separate tab for CEL strategy development.

Provides:
- JSON strategy file load/save operations
- 4 workflow CEL editors (Entry, Exit, Before Exit, Update Stop)
- Integrated CEL command reference browser
- Function palette with quick insert
- Dark theme conformant design
- Optimized layout with resizable panels
"""

from __future__ import annotations

import json
import os
from typing import Optional, Dict, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton,
    QTabWidget, QLabel, QLineEdit, QFileDialog, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QStatusBar, QGroupBox,
    QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.ui.widgets.cel_editor_widget import CelEditorWidget
from src.ui.widgets.cel_function_palette import CelFunctionPalette


class CelCommandReference(QWidget):
    """CEL Command Reference Browser - displays commands from CEL_Befehle_Liste_v2.md."""

    command_selected = pyqtSignal(str, str)  # command_name, code_snippet

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_cel_commands()

    def _setup_ui(self):
        """Setup UI with search and tree view."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search box
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Search:")
        search_label.setStyleSheet("color: #d4d4d4;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search commands...")
        self.search_box.textChanged.connect(self._on_search_changed)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus {
                border: 1px solid #4a90e2;
            }
        """)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        layout.addLayout(search_layout)

        # Tree widget for commands
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Command / Function"])
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3a3a3a;
                selection-background-color: #4a90e2;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #2a2a2a;
            }
            QTreeWidget::branch {
                background-color: #1e1e1e;
            }
        """)

        layout.addWidget(self.tree)

        # Description panel
        desc_label = QLabel("📖 Description:")
        desc_label.setStyleSheet("color: #d4d4d4; font-weight: bold;")
        layout.addWidget(desc_label)

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(100)
        self.description_text.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #d4d4d4;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11pt;
            }
        """)
        layout.addWidget(self.description_text)

        # Insert button
        self.insert_btn = QPushButton("↑ Insert at Cursor")
        self.insert_btn.clicked.connect(self._on_insert_clicked)
        self.insert_btn.setEnabled(False)
        self.insert_btn.setStyleSheet("""
            QPushButton {
                background-color: #26a69a;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2bbbad;
            }
            QPushButton:disabled {
                background-color: #3a3a3a;
                color: #666;
            }
        """)
        layout.addWidget(self.insert_btn)

    def _load_cel_commands(self):
        """Load CEL commands from CEL_Befehle_Liste_v2.md."""
        # Categories based on CEL_Befehle_Liste_v2.md structure
        categories = {
            "Mathematical Functions": [
                ("abs(x)", "Absolute value", "abs(value)"),
                ("min(a, b)", "Minimum of two values", "min(a, b)"),
                ("max(a, b)", "Maximum of two values", "max(a, b)"),
                ("round(x)", "Round to nearest integer", "round(value)"),
                ("floor(x)", "Round down", "floor(value)"),
                ("ceil(x)", "Round up", "ceil(value)"),
                ("pow(x, y)", "x to power of y", "pow(base, exponent)"),
                ("sqrt(x)", "Square root", "sqrt(value)"),
                ("log(x)", "Natural logarithm", "log(value)"),
                ("log10(x)", "Base-10 logarithm", "log10(value)"),
                ("sin(x)", "Sine", "sin(angle)"),
                ("cos(x)", "Cosine", "cos(angle)"),
                ("tan(x)", "Tangent", "tan(angle)"),
            ],
            "Logical & Comparison": [
                ("==", "Equal to", "a == b"),
                ("!=", "Not equal to", "a != b"),
                ("<", "Less than", "a < b"),
                (">", "Greater than", "a > b"),
                ("<=", "Less than or equal", "a <= b"),
                (">=", "Greater than or equal", "a >= b"),
                ("&&", "Logical AND", "condition1 && condition2"),
                ("||", "Logical OR", "condition1 || condition2"),
                ("!", "Logical NOT", "!condition"),
                ("in", "Contains", "value in array"),
                ("? :", "Ternary operator", "condition ? value_if_true : value_if_false"),
            ],
            "String & Type Functions": [
                ("type(x)", "Get type of value", "type(variable)"),
                ("string(x)", "Convert to string", "string(value)"),
                ("int(x)", "Convert to integer", "int(value)"),
                ("double(x)", "Convert to double", "double(value)"),
                ("bool(x)", "Convert to boolean", "bool(value)"),
                ("contains(s, sub)", "String contains substring", "contains(text, substring)"),
                ("startsWith(s, prefix)", "String starts with", "startsWith(text, prefix)"),
                ("endsWith(s, suffix)", "String ends with", "endsWith(text, suffix)"),
                ("toLowerCase(s)", "Convert to lowercase", "toLowerCase(text)"),
                ("toUpperCase(s)", "Convert to uppercase", "toUpperCase(text)"),
                ("length(s)", "String length", "length(text)"),
                ("substring(s, start, end)", "Extract substring", "substring(text, start, end)"),
                ("split(s, delimiter)", "Split string", "split(text, delimiter)"),
            ],
            "Array & Collection Functions": [
                ("size(array)", "Array length", "size(array)"),
                ("has(array, element)", "Array contains element", "has(array, element)"),
                ("all(array, condition)", "All elements match", "all(array, condition)"),
                ("any(array, condition)", "Any element matches", "any(array, condition)"),
                ("map(array, fn)", "Transform array", "map(array, function)"),
                ("filter(array, condition)", "Filter array", "filter(array, condition)"),
                ("first(array)", "First element", "first(array)"),
                ("last(array)", "Last element", "last(array)"),
                ("sum(array)", "Sum of elements", "sum(array)"),
                ("avg(array)", "Average of elements", "avg(array)"),
                ("distinct(array)", "Unique elements", "distinct(array)"),
                ("sort(array)", "Sort array", "sort(array)"),
                ("reverse(array)", "Reverse array", "reverse(array)"),
            ],
            "Trading Functions": [
                ("isnull(x)", "Check if null", "isnull(value)"),
                ("isnotnull(x)", "Check if not null", "isnotnull(value)"),
                ("nz(value, default)", "Replace null", "nz(value, 0)"),
                ("coalesce(a, b, c)", "First non-null value", "coalesce(a, b, c)"),
                ("clamp(value, min, max)", "Constrain to range", "clamp(value, 0, 100)"),
                ("is_trade_open()", "Trade currently open", "is_trade_open()"),
                ("is_long()", "Current trade is LONG", "is_long()"),
                ("is_short()", "Current trade is SHORT", "is_short()"),
                ("stop_hit_long()", "Long stop loss hit", "stop_hit_long()"),
                ("stop_hit_short()", "Short stop loss hit", "stop_hit_short()"),
                ("tp_hit()", "Take profit hit", "tp_hit()"),
                ("price_above_ema(period)", "Price > EMA", "price_above_ema(34)"),
                ("price_below_ema(period)", "Price < EMA", "price_below_ema(34)"),
            ],
            "Technical Indicators": [
                ("rsi14.value", "RSI (14-period)", "rsi14.value"),
                ("rsi5.value", "RSI (5-period)", "rsi5.value"),
                ("ema34.value", "EMA (34-period)", "ema34.value"),
                ("ema200.value", "EMA (200-period)", "ema200.value"),
                ("sma50.value", "SMA (50-period)", "sma50.value"),
                ("macd_12_26_9.value", "MACD value", "macd_12_26_9.value"),
                ("macd_12_26_9.signal", "MACD signal", "macd_12_26_9.signal"),
                ("macd_12_26_9.histogram", "MACD histogram", "macd_12_26_9.histogram"),
                ("stoch_14_3_3.k", "Stochastic %K", "stoch_14_3_3.k"),
                ("stoch_14_3_3.d", "Stochastic %D", "stoch_14_3_3.d"),
                ("adx14.value", "ADX (14-period)", "adx14.value"),
                ("adx14.plus_di", "ADX +DI", "adx14.plus_di"),
                ("adx14.minus_di", "ADX -DI", "adx14.minus_di"),
                ("atr14.value", "ATR (14-period)", "atr14.value"),
                ("bb_20_2.upper", "Bollinger upper band", "bb_20_2.upper"),
                ("bb_20_2.middle", "Bollinger middle band", "bb_20_2.middle"),
                ("bb_20_2.lower", "Bollinger lower band", "bb_20_2.lower"),
                ("bb_20_2.width", "Bollinger width", "bb_20_2.width"),
                ("cci20.value", "CCI (20-period)", "cci20.value"),
                ("mfi14.value", "MFI (14-period)", "mfi14.value"),
                ("volume_ratio_20.value", "Volume ratio", "volume_ratio_20.value"),
                ("chop14.value", "Choppiness Index", "chop14.value"),
            ],
            "Pattern Recognition": [
                ("hammer()", "Hammer pattern", "hammer()"),
                ("doji()", "Doji pattern", "doji()"),
                ("engulfing_bullish()", "Bullish Engulfing", "engulfing_bullish()"),
                ("engulfing_bearish()", "Bearish Engulfing", "engulfing_bearish()"),
                ("harami_bullish()", "Bullish Harami", "harami_bullish()"),
                ("harami_bearish()", "Bearish Harami", "harami_bearish()"),
                ("morning_star()", "Morning Star", "morning_star()"),
                ("evening_star()", "Evening Star", "evening_star()"),
            ],
            "Time Functions": [
                ("now()", "Current timestamp", "now()"),
                ("timestamp()", "Bar timestamp", "timestamp()"),
                ("bar_age()", "Bars since entry", "bar_age()"),
                ("bars_since(condition)", "Bars since condition", "bars_since(condition)"),
                ("is_time_in_range(start, end)", "Time in range", "is_time_in_range('09:30', '16:00')"),
                ("is_new_day()", "New trading day", "is_new_day()"),
                ("is_new_hour()", "New hour started", "is_new_hour()"),
            ],
            "Variables": [
                ("trade.entry_price", "Entry price", "trade.entry_price"),
                ("trade.current_price", "Current price", "trade.current_price"),
                ("trade.stop_price", "Stop loss price", "trade.stop_price"),
                ("trade.pnl_pct", "P&L in percent", "trade.pnl_pct"),
                ("trade.pnl_usdt", "P&L in USDT", "trade.pnl_usdt"),
                ("trade.side", "Trade side (long/short)", "trade.side"),
                ("trade.leverage", "Leverage used", "trade.leverage"),
                ("close", "Close price", "close"),
                ("open", "Open price", "open"),
                ("high", "High price", "high"),
                ("low", "Low price", "low"),
                ("volume", "Volume", "volume"),
                ("atrp", "ATR in percent", "atrp"),
                ("regime", "Market regime", "regime"),
                ("direction", "Trend direction", "direction"),
                ("cfg.min_atrp_pct", "Min ATR percent", "cfg.min_atrp_pct"),
                ("cfg.max_leverage", "Max leverage", "cfg.max_leverage"),
            ],
        }

        self.tree.clear()

        for category, items in categories.items():
            category_item = QTreeWidgetItem([category])
            category_item.setFont(0, QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tree.addTopLevelItem(category_item)

            for name, description, code in items:
                child = QTreeWidgetItem([name])
                child.setData(0, Qt.ItemDataRole.UserRole, {
                    "name": name,
                    "description": description,
                    "code": code
                })
                category_item.addChild(child)

            category_item.setExpanded(False)

    def _on_search_changed(self, text: str):
        """Filter tree by search text."""
        search_text = text.lower()

        # Show/hide items based on search
        for i in range(self.tree.topLevelItemCount()):
            category = self.tree.topLevelItem(i)
            category_visible = False

            for j in range(category.childCount()):
                child = category.child(j)
                data = child.data(0, Qt.ItemDataRole.UserRole)

                # Check if name, description, or code matches
                matches = (
                    search_text in data["name"].lower() or
                    search_text in data["description"].lower() or
                    search_text in data["code"].lower()
                )

                child.setHidden(not matches if search_text else False)

                if matches:
                    category_visible = True

            category.setHidden(not category_visible if search_text else False)

            # Expand category if search matches
            if search_text and category_visible:
                category.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Show description when item is clicked."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            self.description_text.setPlainText(
                f"{data['name']}\n"
                f"{data['code']}\n\n"
                f"{data['description']}"
            )
            self.insert_btn.setEnabled(True)
            self.selected_command = data["code"]
        else:
            self.description_text.clear()
            self.insert_btn.setEnabled(False)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Insert command on double-click."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            self.command_selected.emit(data["name"], data["code"])

    def _on_insert_clicked(self):
        """Insert selected command."""
        if hasattr(self, 'selected_command'):
            item = self.tree.currentItem()
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data:
                self.command_selected.emit(data["name"], data["code"])


class CelStrategyEditorWidget(QWidget):
    """Main CEL Strategy Editor Widget - separate tab for CEL development."""

    strategy_changed = pyqtSignal(dict)  # Emits strategy dict when changed

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_file: Optional[Path] = None
        self.strategy_data: Dict[str, Any] = self._create_empty_strategy()
        self.modified = False

        self._setup_ui()
        self._connect_signals()

    def _create_empty_strategy(self) -> Dict[str, Any]:
        """Create empty strategy structure."""
        return {
            "schema_version": "1.0.0",
            "strategy_type": "CUSTOM_CEL",
            "name": "Untitled Strategy",
            "workflow": {
                "entry": {"language": "CEL", "expression": "", "enabled": True},
                "exit": {"language": "CEL", "expression": "", "enabled": True},
                "before_exit": {"language": "CEL", "expression": "", "enabled": True},
                "update_stop": {"language": "CEL", "expression": "", "enabled": True}
            },
            "metadata": {
                "created_with": "OrderPilot-AI CEL Editor",
                "version": "1.0.0"
            }
        }

    def _setup_ui(self):
        """Setup UI with dark theme."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Set dark background
        self.setStyleSheet("background-color: #1e1e1e;")

        # === TOP TOOLBAR: File Operations ===
        toolbar_group = QGroupBox()
        toolbar_group.setStyleSheet("""
            QGroupBox {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px;
            }
        """)

        toolbar_layout = QHBoxLayout(toolbar_group)

        # File operation buttons
        self.new_btn = QPushButton("📁 New")
        self.load_btn = QPushButton("📂 Load")
        self.save_btn = QPushButton("💾 Save")
        self.save_as_btn = QPushButton("💾 Save As")

        button_style = """
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a9ff2;
            }
            QPushButton:pressed {
                background-color: #3a80d2;
            }
        """

        for btn in [self.new_btn, self.load_btn, self.save_btn, self.save_as_btn]:
            btn.setStyleSheet(button_style)
            toolbar_layout.addWidget(btn)

        toolbar_layout.addStretch()

        # Strategy name
        name_label = QLabel("Strategy:")
        name_label.setStyleSheet("color: #d4d4d4; font-weight: bold;")
        toolbar_layout.addWidget(name_label)

        self.strategy_name = QLineEdit()
        self.strategy_name.setText("Untitled Strategy")
        self.strategy_name.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                min-width: 200px;
            }
        """)
        toolbar_layout.addWidget(self.strategy_name)

        layout.addWidget(toolbar_group)

        # === MAIN CONTENT: Horizontal Split ===
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3a3a3a;
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: #4a90e2;
            }
        """)

        # LEFT PANEL: CEL Editors (50%)
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)

        # RIGHT PANEL: Reference + Palette (50%)
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set initial sizes (50/50 split)
        main_splitter.setSizes([500, 500])

        layout.addWidget(main_splitter)

        # === BOTTOM STATUS BAR ===
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #2a2a2a;
                color: #d4d4d4;
                border-top: 1px solid #3a3a3a;
            }
        """)
        self.status_bar.showMessage("Ready")
        layout.addWidget(self.status_bar)

    def _create_left_panel(self) -> QWidget:
        """Create left panel with CEL editors."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Workflow tabs
        self.workflow_tabs = QTabWidget()
        self.workflow_tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #1e1e1e;
                border: 1px solid #3a3a3a;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #d4d4d4;
                border: 1px solid #3a3a3a;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4a90e2;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #3a3a3a;
            }
        """)

        # Create 4 workflow editors
        self.cel_editors = {}
        workflow_types = [
            ("Entry", "entry"),
            ("Exit", "exit"),
            ("Before Exit", "before_exit"),
            ("Update Stop", "update_stop")
        ]

        for label, workflow_type in workflow_types:
            editor = CelEditorWidget(self, workflow_type)
            self.cel_editors[workflow_type] = editor
            self.workflow_tabs.addTab(editor, label)

        layout.addWidget(self.workflow_tabs)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create right panel with reference and palette."""
        panel = QWidget()
        panel.setStyleSheet("background-color: #1e1e1e;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Vertical splitter for reference (60%) and palette (40%)
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #3a3a3a;
                height: 4px;
            }
            QSplitter::handle:hover {
                background-color: #4a90e2;
            }
        """)

        # Top: CEL Command Reference (60%)
        ref_group = QGroupBox("📚 CEL Command Reference")
        ref_group.setStyleSheet("""
            QGroupBox {
                background-color: #2a2a2a;
                color: #d4d4d4;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        ref_layout = QVBoxLayout(ref_group)

        self.command_reference = CelCommandReference(self)
        ref_layout.addWidget(self.command_reference)

        right_splitter.addWidget(ref_group)

        # Bottom: Function Palette (40%)
        palette_group = QGroupBox("🔧 Function Palette")
        palette_group.setStyleSheet("""
            QGroupBox {
                background-color: #2a2a2a;
                color: #d4d4d4;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
        """)
        palette_layout = QVBoxLayout(palette_group)

        self.function_palette = CelFunctionPalette(self)
        palette_layout.addWidget(self.function_palette)

        right_splitter.addWidget(palette_group)

        # Set initial sizes (60/40 split)
        right_splitter.setSizes([600, 400])

        layout.addWidget(right_splitter)

        return panel

    def _connect_signals(self):
        """Connect all signals."""
        # File operations
        self.new_btn.clicked.connect(self._on_new_clicked)
        self.load_btn.clicked.connect(self._on_load_clicked)
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.save_as_btn.clicked.connect(self._on_save_as_clicked)

        # Strategy name
        self.strategy_name.textChanged.connect(self._on_strategy_name_changed)

        # Command reference
        self.command_reference.command_selected.connect(self._on_command_selected)

        # Function palette
        self.function_palette.function_selected.connect(self._on_function_selected)

        # Editor changes
        for editor in self.cel_editors.values():
            editor.code_changed.connect(self._on_code_changed)

    def _on_new_clicked(self):
        """Create new strategy."""
        if self.modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Do you want to save changes before creating a new strategy?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._on_save_clicked()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        self.strategy_data = self._create_empty_strategy()
        self.current_file = None
        self.modified = False

        self.strategy_name.setText("Untitled Strategy")

        # Clear all editors
        for editor in self.cel_editors.values():
            editor.set_code("")

        self.status_bar.showMessage("New strategy created")

    def _on_load_clicked(self):
        """Load strategy from JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load CEL Strategy",
            "03_JSON/Trading_Bot",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.strategy_data = json.load(f)

            self.current_file = Path(file_path)
            self.modified = False

            # Update UI
            self.strategy_name.setText(self.strategy_data.get("name", "Untitled Strategy"))

            # Load workflow expressions
            workflow = self.strategy_data.get("workflow", {})
            for workflow_type, editor in self.cel_editors.items():
                workflow_data = workflow.get(workflow_type, {})
                expression = workflow_data.get("expression", "")
                editor.set_code(expression)

            self.status_bar.showMessage(f"Loaded: {self.current_file.name}")

        except Exception as e:
            QMessageBox.critical(
                self, "Load Error",
                f"Failed to load strategy:\n{str(e)}"
            )

    def _on_save_clicked(self):
        """Save strategy to current file or prompt for new file."""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self._on_save_as_clicked()

    def _on_save_as_clicked(self):
        """Save strategy to new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CEL Strategy",
            "03_JSON/Trading_Bot",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        # Ensure .json extension
        if not file_path.endswith('.json'):
            file_path += '.json'

        self._save_to_file(Path(file_path))

    def _save_to_file(self, file_path: Path):
        """Save strategy to specified file."""
        try:
            # Update workflow expressions from editors
            for workflow_type, editor in self.cel_editors.items():
                self.strategy_data["workflow"][workflow_type]["expression"] = editor.get_code()

            # Update name
            self.strategy_data["name"] = self.strategy_name.text()

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.strategy_data, f, indent=2)

            self.current_file = file_path
            self.modified = False

            self.status_bar.showMessage(f"Saved: {file_path.name}")

        except Exception as e:
            QMessageBox.critical(
                self, "Save Error",
                f"Failed to save strategy:\n{str(e)}"
            )

    def _on_strategy_name_changed(self, text: str):
        """Update strategy name."""
        self.strategy_data["name"] = text
        self.modified = True

    def _on_code_changed(self, code: str):
        """Mark as modified when code changes."""
        self.modified = True

    def _on_command_selected(self, name: str, code: str):
        """Insert command from reference."""
        current_editor = self.cel_editors[self.workflow_tabs.tabText(self.workflow_tabs.currentIndex()).lower().replace(' ', '_')]
        current_editor.insert_text(code)
        self.status_bar.showMessage(f"Inserted: {name}")

    def _on_function_selected(self, name: str, code: str):
        """Insert function from palette."""
        current_editor = self.cel_editors[self.workflow_tabs.tabText(self.workflow_tabs.currentIndex()).lower().replace(' ', '_')]
        current_editor.insert_text(code)
        self.status_bar.showMessage(f"Inserted: {name}")
