"""Entry Analyzer Mixin for Chart Widget.

Provides integration of the Entry Analyzer popup
with the embedded TradingView chart.

Phase 3: Added BackgroundRunner for live analysis.
Phase 4: Added Regime Filter dropdown for filtering regime lines on chart.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QMessageBox, QComboBox, QStyledItemDelegate, QWidget, QHBoxLayout, QLabel

from .live_analysis_bridge import LiveAnalysisBridge

if TYPE_CHECKING:
    from src.analysis.visible_chart.types import AnalysisResult, EntryEvent, RegimeType

logger = logging.getLogger(__name__)

# Import debug logger
try:
    from src.analysis.visible_chart.debug_logger import debug_logger
except ImportError:
    debug_logger = logger


# ==================== Regime Filter CheckableComboBox ====================


class CheckBoxDelegate(QStyledItemDelegate):
    """Delegate to render checkboxes in QComboBox dropdown."""

    def paint(self, painter, option, index):
        """Paint the item with a checkbox if checkable."""
        from PyQt6.QtCore import QRect
        from PyQt6.QtGui import QPen, QColor, QBrush
        from PyQt6.QtWidgets import QStyle, QStyleOptionButton, QApplication

        # Get the item
        model = index.model()
        item = model.itemFromIndex(index) if hasattr(model, 'itemFromIndex') else None

        # Draw selection background if selected/hovered
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(60, 60, 70))

        if item and item.isCheckable():
            # Draw checkbox
            check_option = QStyleOptionButton()
            check_option.rect = QRect(option.rect.x() + 4, option.rect.y(), 20, option.rect.height())
            check_option.state = QStyle.StateFlag.State_Enabled

            if item.checkState() == Qt.CheckState.Checked:
                check_option.state |= QStyle.StateFlag.State_On
            else:
                check_option.state |= QStyle.StateFlag.State_Off

            QApplication.style().drawControl(QStyle.ControlElement.CE_CheckBox, check_option, painter)

            # Draw text after checkbox with item's foreground color
            text_rect = QRect(option.rect.x() + 26, option.rect.y(), option.rect.width() - 30, option.rect.height())
            foreground = item.foreground()
            if foreground.color().isValid():
                painter.setPen(QPen(foreground.color()))
            else:
                painter.setPen(QPen(option.palette.text().color()))
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, index.data())
        else:
            # Non-checkable item (header) - draw with bold style
            painter.save()
            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(QColor("#e0e0e0")))  # Light gray for header
            text_rect = QRect(option.rect.x() + 6, option.rect.y(), option.rect.width() - 10, option.rect.height())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, index.data())
            painter.restore()

    def sizeHint(self, option, index):
        """Return size hint for items."""
        from PyQt6.QtCore import QSize
        size = super().sizeHint(option, index)
        return QSize(size.width(), max(size.height(), 24))  # Minimum height of 24px


class CheckableComboBox(QComboBox):
    """QComboBox with checkable items for multi-select regime filtering.

    Allows users to select multiple regimes to display on the chart.
    Emits selectionChanged signal when selection changes.
    """

    selectionChanged = pyqtSignal(list)  # Emits list of selected regime IDs

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Use QStandardItemModel for checkable items
        self._model = QStandardItemModel(self)
        self.setModel(self._model)

        # CRITICAL: Set delegate to render checkboxes
        self._delegate = CheckBoxDelegate(self)
        self.setItemDelegate(self._delegate)

        # Configure the view for better dropdown
        view = self.view()
        view.pressed.connect(self._handle_item_pressed)
        view.viewport().installEventFilter(self)  # Don't close popup on click
        view.setMouseTracking(True)  # Enable hover effects

        # Set minimum width and max visible items
        self.setMinimumWidth(140)
        self.setMaximumWidth(200)
        self.setMaxVisibleItems(12)  # Show all 10 items (1 header + 9 regimes)

        # Placeholder text
        self._placeholder = "Filter..."

        # Regime colors for visual indication
        self._regime_colors = {
            "STRONG_TF": "#6d28d9",
            "STRONG_BULL": "#16a34a",
            "STRONG_BEAR": "#dc2626",
            "TF": "#8b5cf6",
            "BULL_EXHAUSTION": "#fbbf24",
            "BEAR_EXHAUSTION": "#fb923c",
            "BULL": "#22c55e",
            "BEAR": "#ef4444",
            "SIDEWAYS": "#f59e0b",
        }

        logger.debug("CheckableComboBox initialized with CheckBoxDelegate")
        import sys
        print(f"[COMBO] Created CheckableComboBox id={id(self)}, model id={id(self._model)}", flush=True)
        sys.stdout.flush()

    def eventFilter(self, obj, event) -> bool:
        """Event filter for viewport - not used for blocking anymore."""
        return super().eventFilter(obj, event)

    def hidePopup(self) -> None:
        """Override to prevent popup from closing when clicking items."""
        # Only hide if user clicked outside the popup or pressed Escape
        # Check if mouse is still over the view
        view = self.view()
        if view and view.underMouse():
            # Mouse is over the dropdown - don't close
            print(f"[COMBO] hidePopup blocked - mouse over view", flush=True)
            return
        print(f"[COMBO] hidePopup allowed", flush=True)
        super().hidePopup()

    def showPopup(self) -> None:
        """Override to log when popup is shown."""
        item_count = self._model.rowCount()
        logger.info(f"🔽 [v2] Regime filter popup: {item_count} items, enabled={self.isEnabled()}, id={id(self)}")
        print(f"[COMBO] showPopup called on {id(self)}, model={id(self._model)}, items={item_count}", flush=True)
        if item_count == 0:
            logger.warning("⚠️ No items in regime filter - this shouldn't happen!")
            # Debug: Check if model is the same as _model
            actual_model = self.model()
            print(f"[COMBO] self.model()={id(actual_model)}, self._model={id(self._model)}, same={actual_model is self._model}", flush=True)
            # Emergency: try populating directly
            print(f"[COMBO] Emergency populate with 9 regimes...", flush=True)
            self._emergency_populate()
        super().showPopup()

    def _handle_item_pressed(self, index) -> None:
        """Toggle check state when item is clicked."""
        print(f"[COMBO] _handle_item_pressed called, index={index.row()}", flush=True)
        item = self._model.itemFromIndex(index)
        if not item:
            return

        # Check if it's the header item (index 0 or special data)
        is_header = index.row() == 0 or item.data(Qt.ItemDataRole.UserRole) == "__header__"
        
        if is_header:
            # Toggle all items based on current header state (approximation)
            # If current text says "All", uncheck all. If "None" or mixed, check all.
            current_text = item.text()
            should_check = "✗" in current_text or "/" in current_text or not "✓ Alle" in current_text
            
            print(f"[COMBO] Header clicked. Toggle all to: {should_check}", flush=True)
            
            for i in range(self._model.rowCount()):
                child = self._model.item(i)
                if child and child.isCheckable():
                    child.setCheckState(Qt.CheckState.Checked if should_check else Qt.CheckState.Unchecked)
            
            self._update_display_text()
            selected = self.get_selected_items()
            print(f"[COMBO] Emitting selectionChanged (ALL): {selected}", flush=True)
            self.selectionChanged.emit(selected)
            return

        if item.isCheckable():
            # Toggle check state
            if item.checkState() == Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Unchecked)
                print(f"[COMBO] Set to UNCHECKED", flush=True)
            else:
                item.setCheckState(Qt.CheckState.Checked)
                print(f"[COMBO] Set to CHECKED", flush=True)
            self._update_display_text()
            selected = self.get_selected_items()
            print(f"[COMBO] Emitting selectionChanged: {selected}", flush=True)
            self.selectionChanged.emit(selected)
            logger.debug(f"Toggled {item.text()}, selected: {selected}")

    def _update_display_text(self) -> None:
        """Update the display text to show selected count."""
        selected = self.get_selected_items()
        # Count only checkable items (exclude header)
        checkable_count = 0
        for i in range(self._model.rowCount()):
            item = self._model.item(i)
            if item and item.isCheckable():
                checkable_count += 1

        if checkable_count == 0:
            return

        # Update the first item (header) to show count
        header_item = self._model.item(0)
        if header_item:
            if len(selected) == checkable_count:
                header_item.setText(f"✓ Alle ({checkable_count})")
            elif len(selected) == 0:
                header_item.setText(f"✗ Keine (0/{checkable_count})")
            else:
                header_item.setText(f"✓ {len(selected)}/{checkable_count}")
            self.setCurrentIndex(0)  # Always show header

    def add_header_item(self, text: str = "✓ Alle") -> None:
        """Add a non-checkable header item that shows selection count."""
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Not checkable, just display
        item.setData("__header__", Qt.ItemDataRole.UserRole)
        self._model.appendRow(item)

    def add_item(self, text: str, data: Any = None, checked: bool = True) -> None:
        """Add a checkable item to the combobox."""
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setData(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole)
        if data is not None:
            item.setData(data, Qt.ItemDataRole.UserRole)

        # Add color indicator if available
        regime_id = data if data else text.upper().replace(" ", "_")
        if regime_id in self._regime_colors:
            from PyQt6.QtGui import QColor
            item.setForeground(QColor(self._regime_colors[regime_id]))

        self._model.appendRow(item)

    def add_separator_item(self, text: str = "─" * 15) -> None:
        """Add a non-selectable separator item."""
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setEnabled(False)
        self._model.appendRow(item)

    def get_selected_items(self) -> list[str]:
        """Get list of selected regime IDs."""
        selected = []
        for i in range(self._model.rowCount()):
            item = self._model.item(i)
            if item and item.isCheckable() and item.checkState() == Qt.CheckState.Checked:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data and data != "__header__":
                    selected.append(data)
        return selected

    def select_all(self) -> None:
        """Select all checkable items."""
        for i in range(self._model.rowCount()):
            item = self._model.item(i)
            if item and item.isCheckable():
                item.setCheckState(Qt.CheckState.Checked)
        self._update_display_text()
        self.selectionChanged.emit(self.get_selected_items())

    def deselect_all(self) -> None:
        """Deselect all checkable items."""
        for i in range(self._model.rowCount()):
            item = self._model.item(i)
            if item and item.isCheckable():
                item.setCheckState(Qt.CheckState.Unchecked)
        self._update_display_text()
        self.selectionChanged.emit(self.get_selected_items())

    def set_selected(self, regime_ids: list[str]) -> None:
        """Set which regimes are selected."""
        for i in range(self._model.rowCount()):
            item = self._model.item(i)
            if item and item.isCheckable():
                data = item.data(Qt.ItemDataRole.UserRole)
                regime_id = data if data else item.text()
                if regime_id in regime_ids:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)
        self._update_display_text()

    def clear_items(self) -> None:
        """Clear all items from the combobox."""
        import traceback
        print(f"[REGIME_FILTER] clear_items called! Stack trace:", flush=True)
        traceback.print_stack(limit=5)
        self._model.clear()

    def _emergency_populate(self) -> None:
        """Emergency method to populate if items are missing."""
        from PyQt6.QtGui import QColor
        print(f"[COMBO] _emergency_populate: clearing and adding items...", flush=True)
        self._model.clear()

        # Add header
        header = QStandardItem("✓ Alle (9)")
        header.setFlags(Qt.ItemFlag.ItemIsEnabled)
        header.setData("__header__", Qt.ItemDataRole.UserRole)
        self._model.appendRow(header)

        # Add regimes
        regimes = [
            ("🟣 STRONG_TF", "STRONG_TF", "#6d28d9"),
            ("🟢 STRONG_BULL", "STRONG_BULL", "#16a34a"),
            ("🔴 STRONG_BEAR", "STRONG_BEAR", "#dc2626"),
            ("💜 TF", "TF", "#8b5cf6"),
            ("⚠️ BULL_EXHAUST", "BULL_EXHAUSTION", "#fbbf24"),
            ("⚠️ BEAR_EXHAUST", "BEAR_EXHAUSTION", "#fb923c"),
            ("🟢 BULL", "BULL", "#22c55e"),
            ("🔴 BEAR", "BEAR", "#ef4444"),
            ("🟡 SIDEWAYS", "SIDEWAYS", "#f59e0b"),
        ]

        for display, regime_id, color in regimes:
            item = QStandardItem(display)
            item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            item.setData(Qt.CheckState.Checked, Qt.ItemDataRole.CheckStateRole)
            item.setData(regime_id, Qt.ItemDataRole.UserRole)
            item.setForeground(QColor(color))
            self._model.appendRow(item)

        self.setCurrentIndex(0)
        print(f"[COMBO] _emergency_populate done: {self._model.rowCount()} items", flush=True)


class AnalysisWorker(QThread):
    """Background worker for running analysis without blocking UI."""

    finished = pyqtSignal(object)  # AnalysisResult
    error = pyqtSignal(str)

    def __init__(
        self,
        visible_range: dict,
        symbol: str,
        timeframe: str,
        candles: list[dict],
        use_optimizer: bool = True,
        json_config_path: str | None = None,
        parent: Any = None,
    ) -> None:
        """Initialize the analysis worker.

        Args:
            visible_range: Dict with 'from' and 'to' timestamps.
            symbol: Trading symbol.
            timeframe: Chart timeframe.
            candles: Pre-loaded candle data from chart.
            use_optimizer: If True, run FastOptimizer (Phase 2).
            json_config_path: Path to JSON config file for regime parameters.
            parent: Parent QObject.
        """
        super().__init__(parent)
        self._visible_range = visible_range
        self._symbol = symbol
        self._timeframe = timeframe
        self._candles = candles
        self._use_optimizer = use_optimizer
        self._json_config_path = json_config_path

    def run(self) -> None:
        """Execute the analysis in background thread."""
        try:
            from src.analysis.visible_chart.analyzer import VisibleChartAnalyzer
            from src.analysis.visible_chart.types import VisibleRange
            from src.analysis.visible_chart.debug_logger import debug_logger

            # Convert range
            from_raw = self._visible_range.get("from")
            to_raw = self._visible_range.get("to")
            from_ts = int(from_raw) if from_raw is not None else 0
            to_ts = int(to_raw) if to_raw is not None else 0
            from_idx = None
            to_idx = None

            if self._candles:
                from_idx = int(round(from_raw)) if from_raw is not None else None
                to_idx = int(round(to_raw)) if to_raw is not None else None
                if from_idx is not None and to_idx is not None:
                    max_idx = len(self._candles) - 1
                    if 0 <= from_idx <= max_idx and 0 <= to_idx <= max_idx:
                        from_ts = self._candles[from_idx]["timestamp"]
                        to_ts = self._candles[to_idx]["timestamp"]

            debug_logger.info(
                "EntryAnalyzerWorker: range raw=%s -> ts=(%s,%s) idx=(%s,%s)",
                self._visible_range,
                from_ts,
                to_ts,
                from_idx,
                to_idx,
            )

            if from_ts == 0 or to_ts == 0:
                self.error.emit("Invalid visible range")
                return

            if not self._candles:
                self.error.emit("No candle data available")
                return

            visible_range = VisibleRange(
                from_ts=from_ts,
                to_ts=to_ts,
                from_idx=from_idx if from_idx is not None else self._visible_range.get("from_idx"),
                to_idx=to_idx if to_idx is not None else self._visible_range.get("to_idx"),
            )

            # Run analysis with pre-loaded candles
            # Issue #28: Use JSON config path for regime parameters
            analyzer = VisibleChartAnalyzer(
                use_optimizer=self._use_optimizer,
                json_config_path=self._json_config_path,
            )
            result = analyzer.analyze_with_candles(
                visible_range=visible_range,
                symbol=self._symbol,
                timeframe=self._timeframe,
                candles=self._candles,
            )

            self.finished.emit(result)

        except Exception as e:
            logger.exception("Analysis failed")
            self.error.emit(str(e))


class EntryAnalyzerMixin:
    """Mixin to add Entry Analyzer functionality to chart widget.

    Requires the chart widget to have:
    - get_visible_range(callback) method
    - add_bot_marker() method (from BotOverlayMixin)
    - clear_bot_markers() method
    - _symbol attribute
    - _timeframe attribute

    Phase 3 additions:
    - Live mode with BackgroundRunner
    - Incremental updates on new candles
    - Auto-reanalysis on schedule

    Phase 4 additions:
    - Regime filter dropdown for filtering displayed regime lines
    - Store current regime data for re-filtering
    """

    _entry_analyzer_popup = None
    _analysis_worker = None
    _live_bridge: LiveAnalysisBridge | None = None
    _live_mode_enabled: bool = False
    _auto_draw_entries: bool = True
    _current_json_config_path: str | None = None  # Issue #28: Current JSON config path

    # Phase 4: Regime Filter
    _regime_filter_combo: CheckableComboBox | None = None
    _current_regime_data: list[dict] = []  # Store current regime data for re-filtering
    _regime_filter_enabled: bool = True  # Whether filtering is active

    def _init_entry_analyzer(self) -> None:
        """Initialize entry analyzer connections.

        Must be called from chart widget __init__.
        """
        # Connect to chart signals if they exist
        if hasattr(self, "symbol_changed"):
            self.symbol_changed.connect(self._on_entry_analyzer_symbol_changed)
        if hasattr(self, "timeframe_changed"):
            self.timeframe_changed.connect(self._on_entry_analyzer_timeframe_changed)
        if hasattr(self, "data_loaded"):
            self.data_loaded.connect(self._on_entry_analyzer_data_loaded)

    # ==================== Regime Filter Methods (Phase 4) ====================

    def create_regime_filter_widget(self) -> QWidget:
        """Create the regime filter widget for toolbar integration.

        Returns a container widget with label and checkable combobox.
        Call this from toolbar setup to add the filter.

        Returns:
            QWidget containing label and filter combobox
        """
        container = QWidget()
        container.setMinimumWidth(180)  # Ensure container has minimum width
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)

        # Label
        label = QLabel("Filter:")
        label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        layout.addWidget(label)

        # Checkable ComboBox
        self._regime_filter_combo = CheckableComboBox()
        self._regime_filter_combo.setToolTip("Wähle welche Regimes im Chart angezeigt werden")

        # Apply styling to ensure visibility
        self._regime_filter_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d30;
                color: #e0e0e0;
                border: 1px solid #4a4a4d;
                border-radius: 3px;
                padding: 3px 8px;
                min-width: 130px;
            }
            QComboBox:hover {
                border-color: #6366f1;
            }
            QComboBox:enabled {
                background-color: #2d2d30;
            }
            QComboBox:disabled {
                background-color: #1a1a1a;
                color: #666;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #9ca3af;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d30;
                border: 1px solid #4a4a4d;
                selection-background-color: #3d3d40;
                outline: none;
            }
        """)

        self._regime_filter_combo.setEnabled(True)  # Ensure enabled

        # Add default regime types (will be updated when regimes are detected)
        self._populate_regime_filter_defaults()

        # Connect signal
        self._regime_filter_combo.selectionChanged.connect(self._on_regime_filter_changed)

        layout.addWidget(self._regime_filter_combo)

        # Debug: Check if items were added
        item_count = self._regime_filter_combo._model.rowCount()
        logger.info(f"✓ Regime filter widget created with {item_count} items, enabled={self._regime_filter_combo.isEnabled()}")
        print(f"[REGIME_FILTER] Widget created with {item_count} items, enabled={self._regime_filter_combo.isEnabled()}")

        return container

    def _populate_regime_filter_defaults(self) -> None:
        """Populate the regime filter with default regime types."""
        print("[REGIME_FILTER] _populate_regime_filter_defaults called")  # Direct stdout
        if not self._regime_filter_combo:
            logger.warning("_populate_regime_filter_defaults: combo is None")
            print("[REGIME_FILTER] ERROR: combo is None!")
            return

        logger.debug("_populate_regime_filter_defaults: Starting...")

        # Clear existing items
        self._regime_filter_combo.clear_items()

        # Add header item first (shows selection count)
        self._regime_filter_combo.add_header_item("✓ Alle (9)")
        logger.debug(f"After header: rowCount={self._regime_filter_combo._model.rowCount()}")

        # Default regimes based on 9-level hierarchy
        default_regimes = [
            ("🟣 STRONG_TF", "STRONG_TF"),
            ("🟢 STRONG_BULL", "STRONG_BULL"),
            ("🔴 STRONG_BEAR", "STRONG_BEAR"),
            ("💜 TF", "TF"),
            ("⚠️ BULL_EXHAUST", "BULL_EXHAUSTION"),
            ("⚠️ BEAR_EXHAUST", "BEAR_EXHAUSTION"),
            ("🟢 BULL", "BULL"),
            ("🔴 BEAR", "BEAR"),
            ("🟡 SIDEWAYS", "SIDEWAYS"),
        ]

        for display_name, regime_id in default_regimes:
            self._regime_filter_combo.add_item(display_name, data=regime_id, checked=True)

        final_count = self._regime_filter_combo._model.rowCount()
        logger.debug(f"After adding items: rowCount={final_count}")

        self._regime_filter_combo._update_display_text()
        self._regime_filter_combo.setCurrentIndex(0)
        self._regime_filter_combo.setEnabled(True)  # Ensure enabled after populating

        logger.info(f"✓ Regime filter populated: {final_count} items (1 header + {len(default_regimes)} regimes)")
        print(f"[REGIME_FILTER] ✓ Populated combo id={id(self._regime_filter_combo)} with {final_count} items")

    def _update_regime_filter_from_data(self, regimes: list[dict]) -> None:
        """Update regime filter options based on detected regimes.

        Args:
            regimes: List of regime period dicts with 'regime' key
        """
        if not self._regime_filter_combo:
            return

        # Extract unique regime IDs from data
        detected_regime_ids = set()
        for regime_data in regimes:
            regime_id = regime_data.get('regime', 'UNKNOWN')
            detected_regime_ids.add(regime_id)

        # Get currently selected items to preserve selection
        currently_selected = self._regime_filter_combo.get_selected_items()

        # Clear and repopulate
        self._regime_filter_combo.clear_items()

        # Regime display mapping with colors
        regime_display = {
            "STRONG_TF": "🟣 STRONG_TF",
            "STRONG_BULL": "🟢 STRONG_BULL",
            "STRONG_BEAR": "🔴 STRONG_BEAR",
            "TF": "💜 TF",
            "BULL_EXHAUSTION": "⚠️ BULL_EXHAUST",
            "BEAR_EXHAUSTION": "⚠️ BEAR_EXHAUST",
            "BULL": "🟢 BULL",
            "BEAR": "🔴 BEAR",
            "SIDEWAYS": "🟡 SIDEWAYS",
            "UNKNOWN": "❓ UNKNOWN",
        }

        # Add header item first
        num_regimes = len(detected_regime_ids)
        self._regime_filter_combo.add_header_item(f"✓ Alle ({num_regimes})")

        # Add detected regimes
        for regime_id in sorted(detected_regime_ids):
            display_name = regime_display.get(regime_id, f"📊 {regime_id}")
            # Preserve previous selection state, default to checked
            is_checked = regime_id in currently_selected if currently_selected else True
            self._regime_filter_combo.add_item(display_name, data=regime_id, checked=is_checked)

        self._regime_filter_combo._update_display_text()
        self._regime_filter_combo.setCurrentIndex(0)
        logger.info(f"Regime filter updated with {num_regimes} detected regimes: {detected_regime_ids}")

    def _on_regime_filter_changed(self, selected_regimes: list[str]) -> None:
        """Handle regime filter selection change.

        Re-draws regime lines based on current filter selection.

        Args:
            selected_regimes: List of selected regime IDs
        """
        logger.info(f"Regime filter changed: {selected_regimes}")
        print(f"[FILTER] _on_regime_filter_changed: {selected_regimes}", flush=True)

        # If no cached regime data, try to reconstruct from existing chart lines
        if not self._current_regime_data:
            self._reconstruct_regime_data_from_chart()

        if not self._current_regime_data:
            logger.warning("No regime data available to filter - clearing all lines")
            print(f"[FILTER] WARNING: No regime data to filter! Clearing lines.", flush=True)
            # Proceed to _apply_regime_filter anyway, which will clear lines if data is empty

        print(f"[FILTER] Have {len(self._current_regime_data)} regime entries to filter", flush=True)
        # Apply filter and redraw
        self._apply_regime_filter(selected_regimes)

    def _reconstruct_regime_data_from_chart(self) -> None:
        """Reconstruct _current_regime_data from existing regime lines in chart.

        This is needed when regime lines were loaded from saved chart state
        but _current_regime_data is empty.
        """
        if not hasattr(self, '_bot_overlay_state'):
            logger.debug("No _bot_overlay_state available")
            return

        regime_lines = getattr(self._bot_overlay_state, 'regime_lines', {})
        if not regime_lines:
            logger.debug("No regime lines in bot overlay state")
            return

        logger.info(f"Reconstructing regime data from {len(regime_lines)} chart lines")
        print(f"[FILTER] Reconstructing from {len(regime_lines)} existing lines", flush=True)

        reconstructed = []
        for line_id, regime_line in regime_lines.items():
            # RegimeLine has: line_id, timestamp, color, regime_name, label
            regime_entry = {
                'start_timestamp': regime_line.timestamp,
                'regime': regime_line.regime_name,
                'score': 100.0,  # Default score since we don't have original
                'duration_bars': 0,
                'duration_time': '0s',
                'line_id': line_id,
            }
            reconstructed.append(regime_entry)

        # Sort by timestamp
        reconstructed.sort(key=lambda x: x['start_timestamp'])
        self._current_regime_data = reconstructed
        logger.info(f"Reconstructed {len(reconstructed)} regime entries")
        
        # Update the filter dropdown with the actual regimes we found
        # This fixes the issue where restored regimes (e.g. "STRONG_TREND_BEAR") 
        # were hidden because they weren't in the default filter list.
        self._update_regime_filter_from_data(reconstructed)

    def _apply_regime_filter(self, selected_regimes: list[str] | None = None) -> None:
        """Apply regime filter and redraw regime lines.

        Args:
            selected_regimes: List of regime IDs to show. If None, get from combo.
        """
        print(f"[FILTER] _apply_regime_filter called with: {selected_regimes}", flush=True)

        if selected_regimes is None and self._regime_filter_combo:
            selected_regimes = self._regime_filter_combo.get_selected_items()
            print(f"[FILTER] Got selection from combo: {selected_regimes}", flush=True)

        if not selected_regimes:
            # No selection means show nothing
            print(f"[FILTER] No regimes selected - clearing all lines", flush=True)
            if hasattr(self, "clear_regime_lines"):
                self.clear_regime_lines()
            return

        # Filter regime data
        filtered_regimes = [
            r for r in self._current_regime_data
            if r.get('regime', 'UNKNOWN') in selected_regimes
        ]

        logger.info(f"Applying filter: {len(filtered_regimes)}/{len(self._current_regime_data)} regimes visible")
        print(f"[FILTER] Filtered: {len(filtered_regimes)}/{len(self._current_regime_data)} regimes", flush=True)
        
        # Debug: Show what was filtered out
        if len(self._current_regime_data) > 0 and len(filtered_regimes) == 0:
            all_regimes = set(r.get('regime', 'UNKNOWN') for r in self._current_regime_data)
            print(f"[FILTER] All available regimes: {all_regimes}", flush=True)
            print(f"[FILTER] Selected regimes: {selected_regimes}", flush=True)

        # Redraw filtered regimes (use internal method to avoid storing again)
        self._draw_regime_lines_internal(filtered_regimes)
        print(f"[FILTER] Redraw complete", flush=True)

    def select_all_regimes(self) -> None:
        """Select all regimes in the filter."""
        if self._regime_filter_combo:
            self._regime_filter_combo.select_all()

    def deselect_all_regimes(self) -> None:
        """Deselect all regimes in the filter."""
        if self._regime_filter_combo:
            self._regime_filter_combo.deselect_all()

    def set_regime_filter_visible(self, regime_ids: list[str]) -> None:
        """Set which regimes are visible via the filter.

        Args:
            regime_ids: List of regime IDs to show
        """
        if self._regime_filter_combo:
            self._regime_filter_combo.set_selected(regime_ids)
            self._apply_regime_filter(regime_ids)

    # ==================== End Regime Filter Methods ====================

    def show_entry_analyzer(self) -> None:
        """Show the Entry Analyzer popup dialog."""
        from src.ui.dialogs.entry_analyzer import EntryAnalyzerPopup

        if self._entry_analyzer_popup is None:
            self._entry_analyzer_popup = EntryAnalyzerPopup(self)
            self._entry_analyzer_popup.analyze_requested.connect(
                self._start_visible_range_analysis
            )
            self._entry_analyzer_popup.draw_entries_requested.connect(
                self._draw_entry_markers
            )
            self._entry_analyzer_popup.clear_entries_requested.connect(
                self._clear_entry_markers
            )
            # Issue #21: Connect regime lines signal
            self._entry_analyzer_popup.draw_regime_lines_requested.connect(
                self._draw_regime_lines
            )
            # Issue #32: Connect finished signal to reset button
            self._entry_analyzer_popup.finished.connect(
                self._on_entry_analyzer_closed
            )

        # Set context for AI/Validation
        symbol = getattr(self, "_symbol", None) or getattr(self, "current_symbol", "UNKNOWN")
        timeframe = getattr(self, "_timeframe", None) or getattr(self, "current_timeframe", "1m")
        candles = self._get_candles_for_validation()
        self._entry_analyzer_popup.set_context(symbol, timeframe, candles)

        self._entry_analyzer_popup.show()
        self._entry_analyzer_popup.raise_()
        self._entry_analyzer_popup.activateWindow()

    def hide_entry_analyzer(self) -> None:
        """Hide the Entry Analyzer popup dialog if it exists."""
        if self._entry_analyzer_popup:
            self._entry_analyzer_popup.close()

    def _get_candles_for_validation(self) -> list[dict]:
        """Get candle data for validation from chart data.

        Returns:
            List of candle dicts with OHLCV data.
        """
        candles = []
        data = getattr(self, "data", None)

        if data is not None and hasattr(data, "iterrows"):
            try:
                from src.ui.widgets.chart_mixins.data_loading_utils import (
                    get_local_timezone_offset_seconds,
                )

                local_offset = get_local_timezone_offset_seconds()
                has_time_column = "time" in data.columns

                for idx, row in data.iterrows():
                    if has_time_column:
                        timestamp = int(row.get("time", 0))
                    else:
                        timestamp = 0
                        if hasattr(idx, "timestamp"):
                            timestamp = int(idx.timestamp()) + local_offset
                        elif isinstance(idx, (int, float)):
                            timestamp = int(idx)

                    candle = {
                        "timestamp": timestamp,
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "close": float(row.get("close", 0)),
                        "volume": float(row.get("volume", 0)),
                    }
                    candles.append(candle)
                debug_logger.info(
                    "EntryAnalyzer: extracted %d candles (has_time_column=%s, local_offset=%s)",
                    len(candles),
                    has_time_column,
                    local_offset,
                )
            except Exception as e:
                logger.warning("Failed to extract candles: %s", e)
                debug_logger.exception("EntryAnalyzer: candle extraction failed")

        return candles

    # ─────────────────────────────────────────────────────────────────
    # Live Mode API (Phase 3)
    # ─────────────────────────────────────────────────────────────────

    def start_live_entry_analysis(
        self,
        reanalyze_interval_sec: float = 60.0,
        use_optimizer: bool = True,
        auto_draw: bool = True,
    ) -> None:
        """Start continuous live entry analysis.

        Args:
            reanalyze_interval_sec: Interval for scheduled reanalysis.
            use_optimizer: Whether to use the optimizer.
            auto_draw: Automatically draw new entries on chart.
        """
        if self._live_bridge is None:
            self._live_bridge = LiveAnalysisBridge(self)
            self._live_bridge.result_ready.connect(self._on_live_result)
            self._live_bridge.new_entry.connect(self._on_live_new_entry)
            self._live_bridge.regime_changed.connect(self._on_live_regime_change)
            self._live_bridge.error_occurred.connect(self._on_live_error)

        self._auto_draw_entries = auto_draw
        # Issue #28: Pass JSON config path for regime parameters
        self._live_bridge.start_live_analysis(
            reanalyze_interval_sec,
            use_optimizer,
            json_config_path=self._current_json_config_path,
        )
        self._live_mode_enabled = True

        # Trigger initial analysis
        self._request_live_analysis()

        logger.info(
            "Live entry analysis started (json=%s)", self._current_json_config_path
        )

    def stop_live_entry_analysis(self) -> None:
        """Stop continuous live entry analysis."""
        if self._live_bridge:
            self._live_bridge.stop_live_analysis()
        self._live_mode_enabled = False
        logger.info("Live entry analysis stopped")

    def is_live_analysis_running(self) -> bool:
        """Check if live analysis is running.

        Returns:
            True if live mode is active.
        """
        return self._live_mode_enabled and (
            self._live_bridge is not None and self._live_bridge.is_running()
        )

    def on_new_candle_received(self, candle: dict) -> None:
        """Handle new candle data for incremental update.

        Call this from chart's streaming data handler.

        Args:
            candle: New candle dict with OHLCV data.
        """
        if not self._live_mode_enabled or not self._live_bridge:
            return

        if not hasattr(self, "get_visible_range"):
            return

        # Get current visible range and push update
        def on_range(range_data: dict | None) -> None:
            if range_data and self._live_bridge:
                symbol = getattr(self, "_symbol", None) or getattr(self, "symbol", "UNKNOWN")
                timeframe = getattr(self, "_timeframe", None) or getattr(self, "timeframe", "1m")
                self._live_bridge.push_new_candle(candle, range_data, symbol, timeframe)

        self.get_visible_range(on_range)

    def get_live_metrics(self) -> dict:
        """Get live analysis performance metrics.

        Returns:
            Dict with performance statistics.
        """
        if self._live_bridge:
            return self._live_bridge.get_metrics()
        return {}

    def _request_live_analysis(self) -> None:
        """Request live analysis of current visible range."""
        if not self._live_bridge or not hasattr(self, "get_visible_range"):
            return

        def on_range(range_data: dict | None) -> None:
            if range_data and self._live_bridge:
                symbol = getattr(self, "_symbol", None) or getattr(self, "symbol", "UNKNOWN")
                timeframe = getattr(self, "_timeframe", None) or getattr(self, "timeframe", "1m")
                self._live_bridge.request_analysis(range_data, symbol, timeframe)

        self.get_visible_range(on_range)

    def _on_live_result(self, result: Any) -> None:
        """Handle live analysis result.

        Args:
            result: AnalysisResult from background runner.
        """
        # Stop loading animation
        if self._entry_analyzer_popup:
            self._entry_analyzer_popup.set_analyzing(False)
            self._entry_analyzer_popup.set_result(result)

        # Auto-draw entries
        if self._auto_draw_entries and result.entries:
            self._clear_entry_markers()
            self._draw_entry_markers(result.entries)

        logger.debug(
            "Live result: %d entries, regime=%s",
            len(result.entries),
            result.regime.value,
        )

    # ... (other methods) ...

    def _start_visible_range_analysis(self, json_config_path: str = "") -> None:
        """Start analysis of the visible chart range using Live Bridge.

        Issue #28: Now accepts json_config_path from the popup signal.

        Args:
            json_config_path: Path to JSON config file from popup (empty for defaults).
        """
        if not hasattr(self, "get_visible_range"):
            logger.error("Chart widget has no get_visible_range method")
            if self._entry_analyzer_popup:
                self._entry_analyzer_popup.set_analyzing(False)
            return

        # Store the JSON config path for this analysis
        self._current_json_config_path = json_config_path if json_config_path else None
        logger.info("Using JSON config for analysis: %s", self._current_json_config_path)

        # Enable live mode and request analysis
        # This unifies the "Analyze" button with the Live/Incremental architecture
        self.start_live_entry_analysis(auto_draw=True)

        # Manually set analyzing state (will be cleared in _on_live_result)
        if self._entry_analyzer_popup:
            self._entry_analyzer_popup.set_analyzing(True)

    def _draw_entry_markers(self, entries: list[EntryEvent]) -> None:
        """Draw entry markers on the chart.

        LONG entries are displayed in GREEN (below bar, arrow up).
        SHORT entries are displayed in RED (above bar, arrow down).

        Args:
            entries: List of entry events to draw.
        """
        if not hasattr(self, "add_bot_marker"):
            logger.warning("Chart widget has no add_bot_marker method")
            return

        from src.analysis.visible_chart.types import EntrySide
        from src.ui.widgets.chart_mixins.bot_overlay_types import MarkerType

        for entry in entries:
            # Always use ENTRY_CONFIRMED for clear LONG=green, SHORT=red display
            # The to_chart_marker() method handles colors:
            # - LONG: #26a69a (green), arrowUp, belowBar
            # - SHORT: #ef5350 (red), arrowDown, aboveBar
            marker_type = MarkerType.ENTRY_CONFIRMED

            # Build descriptive text with confidence and reason
            reasons_str = ", ".join(entry.reason_tags[:2]) if entry.reason_tags else ""
            text = f"{entry.side.value.upper()} {entry.confidence:.0%}"
            if reasons_str:
                text = f"{text} [{reasons_str}]"

            self.add_bot_marker(
                timestamp=entry.timestamp,
                price=entry.price,
                marker_type=marker_type,
                side=entry.side.value,
                text=text,
                score=entry.confidence,
            )

        logger.info(
            "Drew %d entry markers on chart (LONG=green, SHORT=red)",
            len(entries),
        )

    def _clear_entry_markers(self) -> None:
        """Clear all entry markers from the chart."""
        if hasattr(self, "clear_bot_markers"):
            self.clear_bot_markers()
            logger.info("Cleared entry markers")
        elif hasattr(self, "_clear_all_markers"):
            self._clear_all_markers()
            logger.info("Cleared all markers")

    def _get_price_at_timestamp(self, timestamp: int) -> float | None:
        """Get the close price at a specific timestamp.

        Args:
            timestamp: Unix timestamp in seconds

        Returns:
            Close price or None if not found
        """
        if not hasattr(self, '_candles') or not self._candles:
            return None

        # Find candle closest to timestamp
        closest_candle = None
        min_diff = float('inf')

        for candle in self._candles:
            candle_time = candle.get('time', 0)
            diff = abs(candle_time - timestamp)
            if diff < min_diff:
                min_diff = diff
                closest_candle = candle

        if closest_candle:
            return closest_candle.get('close', None)
        return None

    def _draw_regime_lines(self, regimes: list[dict]) -> None:
        """Draw regime period lines on the chart (Issue #21 COMPLETE).

        Stores regime data for filtering and draws lines based on current filter.

        Displays vertical lines showing START of each regime period with:
        - Start line: Light color for regime start
        - Each regime type has unique color pair

        Color Table:
        ┌─────────────────────┬─────────────┬─────────────┬─────────────────────┐
        │ Regime Type         │ START Color │ END Color   │ Description         │
        ├─────────────────────┼─────────────┼─────────────┼─────────────────────┤
        │ STRONG_TREND_BULL   │ #A8E6A3     │ #7BC67A     │ Light/Dark Green    │
        │ STRONG_TREND_BEAR   │ #FFB3BA     │ #FF8A94     │ Light/Dark Red      │
        │ OVERBOUGHT          │ #FFD4A3     │ #FFB870     │ Light/Dark Orange   │
        │ OVERSOLD            │ #A3D8FF     │ #70B8FF     │ Light/Dark Blue     │
        │ RANGE               │ #D3D3D3     │ #AAAAAA     │ Light/Dark Gray     │
        │ UNKNOWN             │ #E0E0E0     │ #C0C0C0     │ Very Light Gray     │
        └─────────────────────┴─────────────┴─────────────┴─────────────────────┘

        Args:
            regimes: List of regime PERIODS with start_timestamp, end_timestamp, regime, score, duration
        """
        if not hasattr(self, "add_regime_line"):
            logger.warning("Chart widget has no add_regime_line method")
            return

        # Phase 4: Store regime data for filtering
        self._current_regime_data = regimes.copy() if regimes else []

        # Update filter dropdown with detected regimes
        self._update_regime_filter_from_data(regimes)

        # Apply current filter (if filter exists, use its selection; otherwise show all)
        if self._regime_filter_combo:
            selected = self._regime_filter_combo.get_selected_items()
            if selected:
                filtered_regimes = [r for r in regimes if r.get('regime', 'UNKNOWN') in selected]
            else:
                filtered_regimes = regimes  # Show all if nothing selected
        else:
            filtered_regimes = regimes  # No filter widget, show all

        # Draw the filtered regimes
        self._draw_regime_lines_internal(filtered_regimes)

    def _draw_regime_lines_internal(self, regimes: list[dict]) -> None:
        """Internal method to draw regime lines without storing data.

        Called by _draw_regime_lines and _apply_regime_filter.

        Args:
            regimes: Filtered list of regime PERIODS to draw
        """
        if not hasattr(self, "add_regime_line"):
            return

        # Color mapping: regime_type -> (start_color, end_color)
        # Issue #5: Each regime has unique, distinguishable color
        # Supports v2 JSON regime IDs (BULL_TREND, BEAR_TREND, CHOP_ZONE...) and legacy names
        regime_colors = {
            # === V2 JSON Regime IDs ===
            "BULL_TREND": ("#22c55e", "#22c55e"),           # Green for bullish trend
            "BEAR_TREND": ("#ef4444", "#ef4444"),           # Red for bearish trend
            "CHOP_ZONE": ("#f59e0b", "#f59e0b"),            # Amber for chop/sideways
            "SIDEWAYS": ("#f59e0b", "#f59e0b"),             # Amber for sideways
            
            # === Generic V2 Pattern Matching ===
            "BULL": ("#22c55e", "#22c55e"),                 # Green for any bullish
            "BEAR": ("#ef4444", "#ef4444"),                 # Red for any bearish
            "CHOP": ("#f59e0b", "#f59e0b"),                 # Amber for chop
            "RANGE": ("#f59e0b", "#f59e0b"),                # Amber for range
            
            # === Extended V2 Regimes ===
            "STRONG_BULL": ("#16a34a", "#16a34a"),          # Dark green for strong bull (RSI confirmed)
            "STRONG_BEAR": ("#dc2626", "#dc2626"),          # Dark red for strong bear (RSI confirmed)
            "STRONG_TF": ("#6d28d9", "#6d28d9"),            # Dark purple for strong trend following
            "TF": ("#8b5cf6", "#8b5cf6"),                   # Purple for trend following
            "TREND_FOLLOWING": ("#8b5cf6", "#8b5cf6"),      # Purple for trend following (alias)
            "STRONG_TREND": ("#6d28d9", "#6d28d9"),         # Dark purple for strong trend
            "WEAK_TREND": ("#a3a3a3", "#a3a3a3"),           # Gray for weak trend
            "NO_TRADE": ("#6b7280", "#6b7280"),             # Dark gray for no trade zone

            # === Exhaustion / Reversal Warning Regimes ===
            "BULL_EXHAUSTION": ("#fbbf24", "#fbbf24"),      # Yellow-amber for bullish exhaustion (reversal warning)
            "BEAR_EXHAUSTION": ("#fb923c", "#fb923c"),      # Orange for bearish exhaustion (reversal warning)
            
            # === Overbought/Oversold ===
            "OVERBOUGHT": ("#f97316", "#f97316"),           # Orange
            "OVERSOLD": ("#3b82f6", "#3b82f6"),             # Blue
            "SIDEWAYS_OVERBOUGHT": ("#f97316", "#f97316"),  # Orange
            "SIDEWAYS_OVERSOLD": ("#3b82f6", "#3b82f6"),    # Blue
            
            # === Legacy Names ===
            "STRONG_TREND_BULL": ("#22c55e", "#22c55e"),
            "STRONG_TREND_BEAR": ("#ef4444", "#ef4444"),
            
            # === Fallback ===
            "UNKNOWN": ("#9ca3af", "#9ca3af"),              # Gray for unknown
        }
        
        def get_regime_color(regime_id: str) -> tuple[str, str]:
            """Get color for regime ID with intelligent pattern matching."""
            # Exact match first
            if regime_id in regime_colors:
                return regime_colors[regime_id]
            
            # Pattern matching for v2 regime IDs
            regime_upper = regime_id.upper()
            
            # Check for TF/TREND_FOLLOWING first (before BULL/BEAR checks)
            if regime_upper == "STRONG_TF":
                return ("#6d28d9", "#6d28d9")  # Dark purple for strong TF
            elif regime_upper == "TF":
                return ("#8b5cf6", "#8b5cf6")  # Purple for TF
            elif "TREND_FOLLOWING" in regime_upper or ("TREND" in regime_upper and "FOLLOWING" in regime_upper):
                return ("#8b5cf6", "#8b5cf6")  # Purple for trend following
            elif "STRONG_TREND" in regime_upper:
                return ("#6d28d9", "#6d28d9")  # Dark purple for strong trend
            # Check for exhaustion/reversal patterns BEFORE general BULL/BEAR
            elif "EXHAUSTION" in regime_upper:
                if "BULL" in regime_upper:
                    return ("#fbbf24", "#fbbf24")  # Yellow-amber for bull exhaustion
                elif "BEAR" in regime_upper:
                    return ("#fb923c", "#fb923c")  # Orange for bear exhaustion
                return ("#fbbf24", "#fbbf24")  # Default yellow for any exhaustion
            elif "BULL" in regime_upper:
                return ("#22c55e", "#22c55e")  # Green
            elif "BEAR" in regime_upper:
                return ("#ef4444", "#ef4444")  # Red
            elif "CHOP" in regime_upper or "SIDEWAYS" in regime_upper or "RANGE" in regime_upper:
                return ("#f59e0b", "#f59e0b")  # Amber
            elif "OVERBOUGHT" in regime_upper:
                return ("#f97316", "#f97316")  # Orange
            elif "OVERSOLD" in regime_upper:
                return ("#3b82f6", "#3b82f6")  # Blue
            elif "NO_TRADE" in regime_upper or "NOTRADE" in regime_upper:
                return ("#6b7280", "#6b7280")  # Dark gray
            
            # Fallback
            return regime_colors["UNKNOWN"]

        # Clear existing regime lines first
        if hasattr(self, "clear_regime_lines"):
            self.clear_regime_lines()

        # Draw new regime lines (START only for each period)
        for i, regime_data in enumerate(regimes):
            start_timestamp = regime_data.get('start_timestamp', 0)
            regime = regime_data.get('regime', 'UNKNOWN')
            score = regime_data.get('score', 0)
            duration_bars = regime_data.get('duration_bars', 0)
            duration_time = regime_data.get('duration_time', '0s')

            # Get colors for this regime type (with intelligent pattern matching)
            start_color, end_color = get_regime_color(regime)

            logger.debug(f"Regime {i}: {regime} -> color: {start_color}")

            # Create label (just regime name with score, no "START" prefix)
            regime_label = f"{regime.replace('_', ' ')} ({score:.1f})"

            # Add regime line to chart
            self.add_regime_line(
                line_id=f"regime_{i}",
                timestamp=start_timestamp,
                regime_name=regime,
                label=regime_label,
                color=start_color
            )

            # Add arrow markers at regime start (Issue: Regime arrows)
            # Get price at regime start timestamp
            start_price = self._get_price_at_timestamp(start_timestamp)
            if start_price is not None and hasattr(self, 'add_bot_marker'):
                from src.ui.widgets.chart_mixins.bot_overlay_types import MarkerType

                # Determine marker type based on regime
                if "BULL" in regime.upper() or "UP" in regime.upper():
                    marker_type = MarkerType.REGIME_BULL
                    side = "long"
                elif "BEAR" in regime.upper() or "DOWN" in regime.upper():
                    marker_type = MarkerType.REGIME_BEAR
                    side = "short"
                else:
                    # For other regimes (RANGE, OVERBOUGHT, OVERSOLD), skip marker
                    continue

                # Add marker arrow
                self.add_bot_marker(
                    timestamp=start_timestamp,
                    price=start_price,
                    marker_type=marker_type,
                    side=side,
                    text=f"{regime.replace('_', ' ')}",
                    score=score
                )
                logger.debug(f"Added regime marker: {marker_type.value} at {start_price:.2f}")

        logger.info(
            "Drew %d regime periods (%d lines) on chart",
            len(regimes),
            len(regimes)  # 1 line per period (start only)
        )

    def _on_entry_analyzer_closed(self, result: int) -> None:
        """Handle Entry Analyzer dialog close event (Issue #32).

        Args:
            result: Dialog result code (Accepted/Rejected).
        """
        logger.info("Entry Analyzer dialog closed")

        # Issue #32: Reset button state when dialog closes
        if hasattr(self, 'entry_analyzer_button'):
            self.entry_analyzer_button.setChecked(False)

    def _on_entry_analyzer_symbol_changed(self, symbol: str) -> None:
        """Handle symbol change to update live analysis.

        Args:
            symbol: New symbol.
        """
        if self._live_mode_enabled:
            logger.info("Symbol changed to %s, refreshing live analysis", symbol)
            # Short delay to allow data to load?
            # Ideally we wait for data_loaded signal, but for now request update.
            self._request_live_analysis()

    def _on_entry_analyzer_timeframe_changed(self, timeframe: str) -> None:
        """Handle timeframe change to update live analysis.

        Args:
            timeframe: New timeframe.
        """
        if self._live_mode_enabled:
            logger.info("Timeframe changed to %s, refreshing live analysis", timeframe)
            self._request_live_analysis()

    def _on_entry_analyzer_data_loaded(self) -> None:
        """Handle data loaded event to update live analysis.
        
        This ensures analysis runs after new symbol/timeframe data 
        is actually available in the chart.
        """
        if self._live_mode_enabled:
            logger.info("Chart data loaded, refreshing live analysis")
            self._request_live_analysis()
