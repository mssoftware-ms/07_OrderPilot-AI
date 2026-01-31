"""Entry Analyzer UI Mixin - User Interface Components.

Provides UI setup, widget creation, and regime filter management
for the Entry Analyzer functionality.

Part of the modular entry_analyzer split (Task 3.3.4):
- entry_analyzer_ui_mixin.py (this file): UI components
- entry_analyzer_events_mixin.py: Event handlers
- entry_analyzer_logic_mixin.py: Business logic

Agent: CODER-021
Task: 3.3.4 - entry_analyzer_mixin refactoring
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor, QIcon
from PyQt6.QtWidgets import QMenu, QWidget, QPushButton

from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class EntryAnalyzerUIMixin:
    """Mixin for Entry Analyzer UI components.

    Provides:
    - Regime filter widget creation and management
    - Filter menu population and defaults
    - UI state management (show/hide, selection)

    Requires the chart widget to have:
    - ICON_SIZE attribute (optional)
    - BUTTON_HEIGHT attribute (optional)
    """

    # Class attributes (declared for type checking)
    _regime_filter_button: QPushButton | None = None
    _regime_filter_menu: QMenu | None = None
    _current_regime_data: list[dict] = []
    _regime_filter_enabled: bool = True
    _entry_analyzer_popup = None

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

    # ==================== Regime Filter Widget ====================

    def create_regime_filter_widget(self) -> QWidget:
        """Create the regime filter widget for toolbar integration.

        Returns a container widget with the filter button.
        Call this from toolbar setup to add the filter.

        Returns:
            QWidget containing filter button
        """
        # Create the button as a QPushButton to match the "Markierungen" button
        self._regime_filter_button = QPushButton("Filter")
        self._regime_filter_button.setToolTip("Markierungen filtern")
        self._regime_filter_button.setIcon(get_icon("filter_alt"))

        # Standard toolbar button properties
        if hasattr(self, "ICON_SIZE"):
            self._regime_filter_button.setIconSize(self.ICON_SIZE)
        else:
            from PyQt6.QtCore import QSize

            self._regime_filter_button.setIconSize(QSize(20, 20))

        if hasattr(self, "BUTTON_HEIGHT"):
            self._regime_filter_button.setFixedHeight(self.BUTTON_HEIGHT)
        else:
            self._regime_filter_button.setFixedHeight(32)

        self._regime_filter_button.setProperty("class", "toolbar-button")

        # Create menu
        self._regime_filter_menu = QMenu(self._regime_filter_button)
        self._regime_filter_menu.setStyleSheet(
            """
            QMenu {
                background-color: #2d2d30;
                border: 1px solid #4a4a4d;
                color: #e0e0e0;
            }
            QMenu::item {
                padding: 5px 20px 5px 30px; /* Space for checkbox */
            }
            QMenu::item:selected {
                background-color: #3d3d40;
            }
            QMenu::indicator {
                width: 16px;
                height: 16px;
                left: 6px;
            }
        """
        )
        self._regime_filter_button.setMenu(self._regime_filter_menu)

        self._regime_filter_enabled = True

        # Add default regime types (will be updated when regimes are detected)
        self._populate_regime_filter_defaults()

        logger.info("✓ Regime filter button created (QPushButton)")
        return self._regime_filter_button

    def _populate_regime_filter_defaults(self) -> None:
        """Populate the regime filter menu with default regime types."""
        if not self._regime_filter_menu:
            return

        self._regime_filter_menu.clear()

        # Add "All" action
        all_action = QAction("Alle", self._regime_filter_menu)
        all_action.setCheckable(True)
        all_action.setChecked(True)
        all_action.setData("__header__")
        all_action.triggered.connect(self._on_regime_filter_action_triggered)
        self._regime_filter_menu.addAction(all_action)

        self._regime_filter_menu.addSeparator()

        # Default regimes based on 9-level hierarchy
        default_regimes = [
            ("STRONG_TF", "STRONG_TF"),
            ("STRONG_BULL", "STRONG_BULL"),
            ("STRONG_BEAR", "STRONG_BEAR"),
            ("TF", "TF"),
            ("BULL_EXHAUSTION", "BULL_EXHAUSTION"),
            ("BEAR_EXHAUSTION", "BEAR_EXHAUSTION"),
            ("BULL", "BULL"),
            ("BEAR", "BEAR"),
            ("SIDEWAYS", "SIDEWAYS"),
        ]

        for display_name, regime_id in default_regimes:
            action = QAction(display_name, self._regime_filter_menu)
            action.setCheckable(True)
            action.setChecked(True)
            action.setData(regime_id)
            action.triggered.connect(self._on_regime_filter_action_triggered)
            self._regime_filter_menu.addAction(action)

    def _update_regime_filter_from_data(self, regimes: list[dict]) -> None:
        """Update regime filter menu based on detected regimes.

        Args:
            regimes: List of regime period dicts with 'regime' key
        """
        print(
            f"[ENTRY_ANALYZER] _update_regime_filter_from_data called with {len(regimes)} items",
            flush=True,
        )

        # Ensure menu exists and is attached
        if not self._regime_filter_menu:
            if self._regime_filter_button:
                self._regime_filter_menu = self._regime_filter_button.menu()

            if not self._regime_filter_menu:
                print(
                    "[ENTRY_ANALYZER] _regime_filter_menu is None and could not be recovered!",
                    flush=True,
                )
                return

        try:
            # Extract unique regime IDs from data
            detected_regime_ids = set()
            for i, regime_data in enumerate(regimes):
                try:
                    # Handle both dict and object (just in case)
                    if isinstance(regime_data, dict):
                        regime_id = regime_data.get("regime", "UNKNOWN")
                    else:
                        regime_id = getattr(regime_data, "regime", "UNKNOWN")

                    detected_regime_ids.add(regime_id)
                except Exception as e:
                    print(
                        f"[ENTRY_ANALYZER] Error extracting ID from item {i}: {e}",
                        flush=True,
                    )
                    continue

            print(
                f"[ENTRY_ANALYZER] Detected unique IDs: {detected_regime_ids}", flush=True
            )

            # Get currently selected items to preserve selection
            currently_selected = []
            try:
                currently_selected = self.get_selected_items()
            except Exception:
                pass  # Ignore error getting selection from old menu state

            # Clear and repopulate
            self._regime_filter_menu.clear()

            # Add "All" action
            all_action = QAction(
                f"Alle ({len(detected_regime_ids)})", self._regime_filter_menu
            )
            all_action.setCheckable(True)
            all_action.setData("__header__")
            all_action.triggered.connect(self._on_regime_filter_action_triggered)
            self._regime_filter_menu.addAction(all_action)

            self._regime_filter_menu.addSeparator()

            # Regime display mapping
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

            all_checked_count = 0

            # Add detected regimes
            for regime_id in sorted(detected_regime_ids):
                display_name = regime_display.get(regime_id, f"📊 {regime_id}")
                action = QAction(display_name, self._regime_filter_menu)
                action.setCheckable(True)
                action.setData(regime_id)

                # Preserve selection logic
                is_checked = True
                if currently_selected:
                    is_checked = regime_id in currently_selected

                action.setChecked(is_checked)
                if is_checked:
                    all_checked_count += 1

                action.triggered.connect(self._on_regime_filter_action_triggered)
                self._regime_filter_menu.addAction(action)

            # Update "All" state
            all_checked = (all_checked_count == len(detected_regime_ids)) and (
                len(detected_regime_ids) > 0
            )
            all_action.setChecked(all_checked)

            logger.info(
                f"Regime filter updated with {len(detected_regime_ids)} detected regimes"
            )

        except Exception as e:
            logger.error(f"Critical error updating regime filter: {e}", exc_info=True)
            print(
                f"[ENTRY_ANALYZER] Critical error in _update_regime_filter_from_data: {e}",
                flush=True,
            )

    # ==================== Filter Selection Management ====================

    def get_selected_items(self) -> list[str]:
        """Get list of selected regime IDs."""
        if not self._regime_filter_menu:
            return []

        selected = []
        for action in self._regime_filter_menu.actions():
            if (
                action.isCheckable()
                and action.isChecked()
                and action.data() != "__header__"
            ):
                data = action.data()
                if data:
                    selected.append(data)
        return selected

    def select_all_regimes(self) -> None:
        """Select all regimes in the filter."""
        if not self._regime_filter_menu:
            return

        for action in self._regime_filter_menu.actions():
            if action.isCheckable():
                action.setChecked(True)
        self._on_regime_filter_changed(self.get_selected_items())

    def deselect_all_regimes(self) -> None:
        """Deselect all regimes in the filter."""
        if not self._regime_filter_menu:
            return

        for action in self._regime_filter_menu.actions():
            if action.isCheckable():
                action.setChecked(False)
        self._on_regime_filter_changed([])

    def set_regime_filter_visible(self, regime_ids: list[str]) -> None:
        """Set which regimes are visible via the filter.

        Args:
            regime_ids: List of regime IDs to show
        """
        if not self._regime_filter_menu:
            return

        for action in self._regime_filter_menu.actions():
            if action.isCheckable() and action.data() != "__header__":
                data = action.data()
                should_check = data in regime_ids
                action.setChecked(should_check)

        # Update All
        all_actions = [
            a
            for a in self._regime_filter_menu.actions()
            if a.isCheckable() and a.data() != "__header__"
        ]
        all_checked = all(a.isChecked() for a in all_actions)
        for action in self._regime_filter_menu.actions():
            if action.data() == "__header__":
                action.setChecked(all_checked)
                break

        self._apply_regime_filter(regime_ids)

    # ==================== Popup Management ====================

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
            # Patterns overlay
            self._entry_analyzer_popup.draw_patterns_requested.connect(
                self._draw_pattern_overlays
            )
            self._entry_analyzer_popup.clear_entries_requested.connect(
                self._clear_entry_markers
            )
            # Issue #21: Connect regime lines signal
            self._entry_analyzer_popup.draw_regime_lines_requested.connect(
                self._draw_regime_lines
            )
            # Issue #32: Connect finished signal to reset button
            self._entry_analyzer_popup.finished.connect(self._on_entry_analyzer_closed)

        # Set context for AI/Validation
        symbol = getattr(self, "_symbol", None) or getattr(
            self, "current_symbol", "UNKNOWN"
        )
        timeframe = getattr(self, "_timeframe", None) or getattr(
            self, "current_timeframe", "1m"
        )
        candles = self._get_candles_for_validation()
        self._entry_analyzer_popup.set_context(symbol, timeframe, candles)

        self._entry_analyzer_popup.show()
        self._entry_analyzer_popup.raise_()
        self._entry_analyzer_popup.activateWindow()

    def hide_entry_analyzer(self) -> None:
        """Hide the Entry Analyzer popup dialog if it exists."""
        if self._entry_analyzer_popup:
            self._entry_analyzer_popup.close()

    # ==================== Forward Declarations (implemented in other mixins) ====================

    def _on_regime_filter_action_triggered(self, checked: bool) -> None:
        """Handle menu action trigger (implemented in events mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerEventsMixin"
        )

    def _on_regime_filter_changed(self, selected_regimes: list[str]) -> None:
        """Handle regime filter change (implemented in events mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerEventsMixin"
        )

    def _apply_regime_filter(self, selected_regimes: list[str] | None = None) -> None:
        """Apply regime filter (implemented in logic mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerLogicMixin"
        )

    def _start_visible_range_analysis(self, json_config_path: str = "") -> None:
        """Start analysis (implemented in events mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerEventsMixin"
        )

    def _draw_entry_markers(self, entries: list) -> None:
        """Draw entry markers (implemented in logic mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerLogicMixin"
        )

    def _draw_pattern_overlays(self, overlays: list[dict]) -> None:
        """Draw pattern overlays (implemented in logic mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerLogicMixin"
        )

    def _clear_entry_markers(self) -> None:
        """Clear entry markers (implemented in logic mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerLogicMixin"
        )

    def _draw_regime_lines(self, regimes: list[dict]) -> None:
        """Draw regime lines (implemented in logic mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerLogicMixin"
        )

    def _on_entry_analyzer_closed(self, result: int) -> None:
        """Handle dialog close (implemented in events mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerEventsMixin"
        )

    def _get_candles_for_validation(self) -> list[dict]:
        """Get candles (implemented in logic mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerLogicMixin"
        )

    def _on_entry_analyzer_symbol_changed(self, symbol: str) -> None:
        """Handle symbol change (implemented in events mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerEventsMixin"
        )

    def _on_entry_analyzer_timeframe_changed(self, timeframe: str) -> None:
        """Handle timeframe change (implemented in events mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerEventsMixin"
        )

    def _on_entry_analyzer_data_loaded(self) -> None:
        """Handle data loaded (implemented in events mixin)."""
        raise NotImplementedError(
            "Must be provided by EntryAnalyzerEventsMixin"
        )
