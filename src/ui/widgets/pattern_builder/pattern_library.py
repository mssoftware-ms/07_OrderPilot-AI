"""Pattern Library - Pre-built candlestick pattern templates.

Provides drag & drop templates for common patterns:
- Reversal patterns (Engulfing, Hammer, etc.)
- Continuation patterns (Flags, etc.)
- Indecision patterns (Doji, Spinning Top)
"""

from typing import Dict, List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QMessageBox, QInputDialog, QHBoxLayout,
    QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDrag

from ui.windows.cel_editor.theme import TEXT_PRIMARY, ACCENT_TEAL, BACKGROUND_PRIMARY


class PatternLibrary(QWidget):
    """Pattern Library widget with pre-built templates.

    Features:
    - Categorized pattern templates (Reversal, Continuation, Indecision)
    - Drag & drop to canvas
    - Custom pattern save
    - Pattern preview

    Signals:
    - pattern_selected: Emitted when pattern is double-clicked (pattern_data)
    """

    # Signal emitted when pattern is selected
    pattern_selected = pyqtSignal(dict)  # Pattern data

    def __init__(self, parent=None):
        """Initialize pattern library."""
        super().__init__(parent)

        self._setup_ui()
        self._load_templates()

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header = QLabel("Pattern Library")
        header.setStyleSheet(f"color: {ACCENT_TEAL}; font-size: 14px; font-weight: bold;")
        layout.addWidget(header)

        # Tree widget for categories
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {BACKGROUND_PRIMARY};
                color: {TEXT_PRIMARY};
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: #2a2a2a;
            }}
            QTreeWidget::item:selected {{
                background: {ACCENT_TEAL};
            }}
        """)

        # Double-click to load pattern
        self.tree.itemDoubleClicked.connect(self._on_pattern_double_clicked)

        layout.addWidget(self.tree)

        # Buttons
        button_layout = QHBoxLayout()

        self.load_btn = QPushButton("Load")
        self.load_btn.setToolTip("Load selected pattern to canvas")
        self.load_btn.clicked.connect(self._on_load_pattern)
        self.load_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT_TEAL};
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #00d9ff;
            }}
        """)
        button_layout.addWidget(self.load_btn)

        self.save_btn = QPushButton("Save Current")
        self.save_btn.setToolTip("Save current canvas pattern to library")
        self.save_btn.clicked.connect(self._on_save_pattern)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background: #3a3a3a;
                color: {TEXT_PRIMARY};
                border: 1px solid #4a4a4a;
                padding: 6px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: #4a4a4a;
            }}
        """)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

        # Info label
        info = QLabel("Double-click to load pattern")
        info.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 10px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

    def _load_templates(self):
        """Load pre-built pattern templates."""
        # Create categories
        reversal_category = QTreeWidgetItem(self.tree, ["📈 Reversal Patterns"])
        reversal_category.setExpanded(True)

        continuation_category = QTreeWidgetItem(self.tree, ["🔄 Continuation Patterns"])
        continuation_category.setExpanded(False)

        indecision_category = QTreeWidgetItem(self.tree, ["⚖️ Indecision Patterns"])
        indecision_category.setExpanded(False)

        # Reversal patterns
        patterns_reversal = [
            ("Bullish Engulfing", self._get_bullish_engulfing_pattern()),
            ("Bearish Engulfing", self._get_bearish_engulfing_pattern()),
            ("Hammer", self._get_hammer_pattern()),
            ("Shooting Star", self._get_shooting_star_pattern()),
            ("Morning Star", self._get_morning_star_pattern()),
            ("Evening Star", self._get_evening_star_pattern()),
        ]

        for name, pattern_data in patterns_reversal:
            item = QTreeWidgetItem(reversal_category, [name])
            item.setData(0, Qt.ItemDataRole.UserRole, pattern_data)

        # Continuation patterns
        patterns_continuation = [
            ("Bull Flag", self._get_bull_flag_pattern()),
            ("Bear Flag", self._get_bear_flag_pattern()),
        ]

        for name, pattern_data in patterns_continuation:
            item = QTreeWidgetItem(continuation_category, [name])
            item.setData(0, Qt.ItemDataRole.UserRole, pattern_data)

        # Indecision patterns
        patterns_indecision = [
            ("Doji", self._get_doji_pattern()),
            ("Spinning Top", self._get_spinning_top_pattern()),
            ("Harami", self._get_harami_pattern()),
        ]

        for name, pattern_data in patterns_indecision:
            item = QTreeWidgetItem(indecision_category, [name])
            item.setData(0, Qt.ItemDataRole.UserRole, pattern_data)

    # ========== Pattern Templates ==========

    def _get_bullish_engulfing_pattern(self) -> dict:
        """Bullish Engulfing: Small bearish + large bullish."""
        return {
            "candles": [
                {
                    "type": "bearish",
                    "index": -1,
                    "position": {"x": 100, "y": 200},
                    "ohlc": {"open": 60, "high": 65, "low": 50, "close": 52}
                },
                {
                    "type": "bullish",
                    "index": 0,
                    "position": {"x": 200, "y": 200},
                    "ohlc": {"open": 48, "high": 70, "low": 45, "close": 68}
                }
            ],
            "relations": [
                {
                    "start_candle_index": 0,
                    "end_candle_index": -1,
                    "relation_type": "greater",
                    "property": "close"
                }
            ],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 2,
                "relation_count": 1,
                "description": "Bullish reversal: Large green candle engulfs previous red"
            }
        }

    def _get_bearish_engulfing_pattern(self) -> dict:
        """Bearish Engulfing: Small bullish + large bearish."""
        return {
            "candles": [
                {
                    "type": "bullish",
                    "index": -1,
                    "position": {"x": 100, "y": 200},
                    "ohlc": {"open": 50, "high": 65, "low": 48, "close": 62}
                },
                {
                    "type": "bearish",
                    "index": 0,
                    "position": {"x": 200, "y": 200},
                    "ohlc": {"open": 68, "high": 70, "low": 45, "close": 46}
                }
            ],
            "relations": [
                {
                    "start_candle_index": 0,
                    "end_candle_index": -1,
                    "relation_type": "less",
                    "property": "close"
                }
            ],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 2,
                "relation_count": 1,
                "description": "Bearish reversal: Large red candle engulfs previous green"
            }
        }

    def _get_hammer_pattern(self) -> dict:
        """Hammer: Bullish reversal with long lower wick."""
        return {
            "candles": [
                {
                    "type": "hammer",
                    "index": 0,
                    "position": {"x": 150, "y": 200},
                    "ohlc": {"open": 55, "high": 58, "low": 30, "close": 56}
                }
            ],
            "relations": [],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 1,
                "relation_count": 0,
                "description": "Bullish reversal: Small body with long lower wick"
            }
        }

    def _get_shooting_star_pattern(self) -> dict:
        """Shooting Star: Bearish reversal with long upper wick."""
        return {
            "candles": [
                {
                    "type": "shooting_star",
                    "index": 0,
                    "position": {"x": 150, "y": 200},
                    "ohlc": {"open": 54, "high": 75, "low": 52, "close": 55}
                }
            ],
            "relations": [],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 1,
                "relation_count": 0,
                "description": "Bearish reversal: Small body with long upper wick"
            }
        }

    def _get_morning_star_pattern(self) -> dict:
        """Morning Star: 3-candle bullish reversal."""
        return {
            "candles": [
                {
                    "type": "bearish",
                    "index": -2,
                    "position": {"x": 100, "y": 200},
                    "ohlc": {"open": 65, "high": 68, "low": 50, "close": 52}
                },
                {
                    "type": "doji",
                    "index": -1,
                    "position": {"x": 200, "y": 250},
                    "ohlc": {"open": 48, "high": 52, "low": 42, "close": 49}
                },
                {
                    "type": "bullish",
                    "index": 0,
                    "position": {"x": 300, "y": 200},
                    "ohlc": {"open": 50, "high": 70, "low": 48, "close": 68}
                }
            ],
            "relations": [
                {
                    "start_candle_index": -1,
                    "end_candle_index": -2,
                    "relation_type": "less",
                    "property": "low"
                },
                {
                    "start_candle_index": 0,
                    "end_candle_index": -1,
                    "relation_type": "greater",
                    "property": "close"
                }
            ],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 3,
                "relation_count": 2,
                "description": "Bullish reversal: Bearish, Doji gap, Bullish"
            }
        }

    def _get_evening_star_pattern(self) -> dict:
        """Evening Star: 3-candle bearish reversal."""
        return {
            "candles": [
                {
                    "type": "bullish",
                    "index": -2,
                    "position": {"x": 100, "y": 200},
                    "ohlc": {"open": 50, "high": 68, "low": 48, "close": 65}
                },
                {
                    "type": "doji",
                    "index": -1,
                    "position": {"x": 200, "y": 150},
                    "ohlc": {"open": 68, "high": 72, "low": 66, "close": 69}
                },
                {
                    "type": "bearish",
                    "index": 0,
                    "position": {"x": 300, "y": 200},
                    "ohlc": {"open": 67, "high": 70, "low": 45, "close": 48}
                }
            ],
            "relations": [
                {
                    "start_candle_index": -1,
                    "end_candle_index": -2,
                    "relation_type": "greater",
                    "property": "high"
                },
                {
                    "start_candle_index": 0,
                    "end_candle_index": -1,
                    "relation_type": "less",
                    "property": "close"
                }
            ],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 3,
                "relation_count": 2,
                "description": "Bearish reversal: Bullish, Doji gap, Bearish"
            }
        }

    def _get_bull_flag_pattern(self) -> dict:
        """Bull Flag: Continuation pattern with pullback."""
        return {
            "candles": [
                {
                    "type": "marubozu_long",
                    "index": -3,
                    "position": {"x": 100, "y": 200},
                    "ohlc": {"open": 45, "high": 70, "low": 44, "close": 69}
                },
                {
                    "type": "bearish",
                    "index": -2,
                    "position": {"x": 200, "y": 220},
                    "ohlc": {"open": 68, "high": 69, "low": 58, "close": 60}
                },
                {
                    "type": "bearish",
                    "index": -1,
                    "position": {"x": 300, "y": 230},
                    "ohlc": {"open": 60, "high": 62, "low": 52, "close": 54}
                },
                {
                    "type": "bullish",
                    "index": 0,
                    "position": {"x": 400, "y": 200},
                    "ohlc": {"open": 55, "high": 75, "low": 54, "close": 73}
                }
            ],
            "relations": [
                {
                    "start_candle_index": 0,
                    "end_candle_index": -3,
                    "relation_type": "greater",
                    "property": "close"
                }
            ],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 4,
                "relation_count": 1,
                "description": "Continuation: Strong bullish, pullback, breakout"
            }
        }

    def _get_bear_flag_pattern(self) -> dict:
        """Bear Flag: Continuation pattern with bounce."""
        return {
            "candles": [
                {
                    "type": "marubozu_short",
                    "index": -3,
                    "position": {"x": 100, "y": 200},
                    "ohlc": {"open": 70, "high": 71, "low": 45, "close": 46}
                },
                {
                    "type": "bullish",
                    "index": -2,
                    "position": {"x": 200, "y": 180},
                    "ohlc": {"open": 47, "high": 58, "low": 46, "close": 56}
                },
                {
                    "type": "bullish",
                    "index": -1,
                    "position": {"x": 300, "y": 170},
                    "ohlc": {"open": 56, "high": 65, "low": 55, "close": 63}
                },
                {
                    "type": "bearish",
                    "index": 0,
                    "position": {"x": 400, "y": 200},
                    "ohlc": {"open": 62, "high": 64, "low": 40, "close": 42}
                }
            ],
            "relations": [
                {
                    "start_candle_index": 0,
                    "end_candle_index": -3,
                    "relation_type": "less",
                    "property": "close"
                }
            ],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 4,
                "relation_count": 1,
                "description": "Continuation: Strong bearish, bounce, breakdown"
            }
        }

    def _get_doji_pattern(self) -> dict:
        """Doji: Indecision candle."""
        return {
            "candles": [
                {
                    "type": "doji",
                    "index": 0,
                    "position": {"x": 150, "y": 200},
                    "ohlc": {"open": 55, "high": 65, "low": 45, "close": 56}
                }
            ],
            "relations": [],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 1,
                "relation_count": 0,
                "description": "Indecision: Open ≈ Close"
            }
        }

    def _get_spinning_top_pattern(self) -> dict:
        """Spinning Top: Indecision with long wicks."""
        return {
            "candles": [
                {
                    "type": "spinning_top",
                    "index": 0,
                    "position": {"x": 150, "y": 200},
                    "ohlc": {"open": 52, "high": 70, "low": 35, "close": 58}
                }
            ],
            "relations": [],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 1,
                "relation_count": 0,
                "description": "Indecision: Small body, long wicks both sides"
            }
        }

    def _get_harami_pattern(self) -> dict:
        """Harami: Small candle inside previous large body."""
        return {
            "candles": [
                {
                    "type": "bearish",
                    "index": -1,
                    "position": {"x": 100, "y": 200},
                    "ohlc": {"open": 70, "high": 72, "low": 40, "close": 42}
                },
                {
                    "type": "bullish",
                    "index": 0,
                    "position": {"x": 200, "y": 220},
                    "ohlc": {"open": 50, "high": 58, "low": 48, "close": 56}
                }
            ],
            "relations": [
                {
                    "start_candle_index": 0,
                    "end_candle_index": -1,
                    "relation_type": "greater",
                    "property": "open"
                },
                {
                    "start_candle_index": 0,
                    "end_candle_index": -1,
                    "relation_type": "less",
                    "property": "close"
                }
            ],
            "metadata": {
                "version": "1.0.0",
                "candle_count": 2,
                "relation_count": 2,
                "description": "Indecision: Small candle within previous body"
            }
        }

    # ========== Event Handlers ==========

    def _on_pattern_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle pattern double-click (load to canvas).

        Args:
            item: Tree widget item
            column: Column index
        """
        pattern_data = item.data(0, Qt.ItemDataRole.UserRole)
        if pattern_data:
            self.pattern_selected.emit(pattern_data)

    def _on_load_pattern(self):
        """Load selected pattern to canvas."""
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select a pattern from the library first."
            )
            return

        pattern_data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if pattern_data:
            self.pattern_selected.emit(pattern_data)
        else:
            QMessageBox.information(
                self,
                "Invalid Selection",
                "Please select a pattern (not a category)."
            )

    def _on_save_pattern(self):
        """Save current canvas pattern to library (custom category)."""
        # Get pattern name from user
        name, ok = QInputDialog.getText(
            self,
            "Save Pattern",
            "Enter pattern name:",
            text="My Custom Pattern"
        )

        if not ok or not name:
            return

        # Get current pattern from canvas (parent must implement get_current_pattern)
        parent = self.parent()
        if hasattr(parent, "pattern_canvas"):
            pattern_data = parent.pattern_canvas.get_pattern_data()

            if not pattern_data.get("candles"):
                QMessageBox.warning(
                    self,
                    "Empty Pattern",
                    "Cannot save empty pattern. Please draw some candles first."
                )
                return

            # Find or create "Custom" category
            custom_category = None
            for i in range(self.tree.topLevelItemCount()):
                item = self.tree.topLevelItem(i)
                if "Custom" in item.text(0):
                    custom_category = item
                    break

            if not custom_category:
                custom_category = QTreeWidgetItem(self.tree, ["⭐ Custom Patterns"])
                custom_category.setExpanded(True)

            # Add pattern to custom category
            pattern_item = QTreeWidgetItem(custom_category, [name])
            pattern_item.setData(0, Qt.ItemDataRole.UserRole, pattern_data)

            QMessageBox.information(
                self,
                "✅ Pattern Saved",
                f"Pattern '{name}' saved to Custom category."
            )
        else:
            QMessageBox.warning(
                self,
                "Cannot Save",
                "Canvas not available. Please try again."
            )

    def get_selected_pattern(self) -> Optional[dict]:
        """Get currently selected pattern data.

        Returns:
            Pattern data dict or None
        """
        current_item = self.tree.currentItem()
        if current_item:
            return current_item.data(0, Qt.ItemDataRole.UserRole)
        return None
