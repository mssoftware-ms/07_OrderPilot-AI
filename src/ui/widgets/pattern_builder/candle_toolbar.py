"""Candle Toolbar for Pattern Builder - Add/remove candles with visual buttons.

QToolBar with 8 candle type buttons + add/remove/clear actions.
Emits signals when user wants to add a candle to the canvas.
"""

from typing import Optional
from PyQt6.QtWidgets import QToolBar, QPushButton, QButtonGroup, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction

from ui.windows.cel_editor.theme import (
    CANDLE_BULLISH_BODY, CANDLE_BEARISH_BODY, CANDLE_DOJI_BODY,
    ACCENT_TEAL, TEXT_PRIMARY
)
from ui.windows.cel_editor.icons import cel_icons


class CandleToolbar(QToolBar):
    """Toolbar for adding candles to the pattern builder canvas.

    Features:
    - 8 candle type buttons (Bullish, Bearish, Doji, Hammer, etc.)
    - Add/Remove/Clear action buttons
    - Active candle type tracking
    - Visual feedback for selected type
    - Icon integration from Material Icons

    Signals:
    - candle_add_requested(candle_type: str): User clicked Add button
    - candle_remove_requested(): User clicked Remove button
    - pattern_clear_requested(): User clicked Clear button

    Usage:
        toolbar = CandleToolbar()
        toolbar.candle_add_requested.connect(canvas.add_candle)
        main_window.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)
    """

    # Signals
    candle_add_requested = pyqtSignal(str)  # candle_type
    candle_remove_requested = pyqtSignal()
    pattern_clear_requested = pyqtSignal()
    zoom_fit_requested = pyqtSignal()
    zoom_back_requested = pyqtSignal()

    # Candle type configuration
    CANDLE_TYPES = [
        {
            "id": "bullish",
            "name": "Bullish",
            "icon": "trending_up",
            "color": CANDLE_BULLISH_BODY,
            "tooltip": "Bullish candle (close > open)\nGreen body with wicks"
        },
        {
            "id": "bearish",
            "name": "Bearish",
            "icon": "trending_down",
            "color": CANDLE_BEARISH_BODY,
            "tooltip": "Bearish candle (close < open)\nRed body with wicks"
        },
        {
            "id": "doji",
            "name": "Doji",
            "icon": "remove",
            "color": CANDLE_DOJI_BODY,
            "tooltip": "Doji candle (open ≈ close)\nSmall or no body, long wicks"
        },
        {
            "id": "hammer",
            "name": "Hammer",
            "icon": "arrow_downward",
            "color": CANDLE_DOJI_BODY,
            "tooltip": "Hammer pattern\nSmall body at top, long lower wick"
        },
        {
            "id": "shooting_star",
            "name": "Shooting Star",
            "icon": "arrow_upward",
            "color": CANDLE_DOJI_BODY,
            "tooltip": "Shooting Star pattern\nSmall body at bottom, long upper wick"
        },
        {
            "id": "spinning_top",
            "name": "Spinning Top",
            "icon": "swap_vert",
            "color": CANDLE_DOJI_BODY,
            "tooltip": "Spinning Top pattern\nSmall body, long wicks both sides"
        },
        {
            "id": "marubozu_long",
            "name": "Marubozu Long",
            "icon": "vertical_align_top",
            "color": CANDLE_BULLISH_BODY,
            "tooltip": "Marubozu Long (Bullish)\nLarge green body, no wicks"
        },
        {
            "id": "marubozu_short",
            "name": "Marubozu Short",
            "icon": "vertical_align_bottom",
            "color": CANDLE_BEARISH_BODY,
            "tooltip": "Marubozu Short (Bearish)\nLarge red body, no wicks"
        }
    ]

    def __init__(self, parent=None):
        """Initialize candle toolbar.

        Args:
            parent: Parent widget (usually main window)
        """
        super().__init__("Candle Toolbar", parent)

        # Current state
        self.active_candle_type: Optional[str] = "bullish"  # Default selection

        # Setup toolbar
        self._setup_toolbar()

        # Create UI
        self._create_candle_type_buttons()
        self.addSeparator()
        self._create_action_buttons()

    def _setup_toolbar(self):
        """Configure toolbar properties."""
        self.setObjectName("CandleToolbar")
        self.setMovable(False)  # Fixed position
        self.setIconSize(QSize(32, 32))

        # Allow toolbar to be vertical (left/right sides)
        self.setAllowedAreas(
            Qt.ToolBarArea.LeftToolBarArea |
            Qt.ToolBarArea.RightToolBarArea
        )

        # Set orientation to vertical by default
        self.setOrientation(Qt.Orientation.Vertical)

    def _create_candle_type_buttons(self):
        """Create candle type selection buttons."""
        # Label
        label = QLabel("  Candle Types:  ")
        label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: bold; padding: 4px;")
        self.addWidget(label)

        # Button group for exclusive selection
        self.candle_button_group = QButtonGroup(self)
        self.candle_button_group.setExclusive(True)

        # Create button for each candle type
        self.candle_buttons = {}
        for candle_type in self.CANDLE_TYPES:
            btn = QPushButton(candle_type["name"])
            btn.setCheckable(True)
            btn.setToolTip(candle_type["tooltip"])
            btn.setProperty("candle_type", candle_type["id"])

            # Style button with candle color
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #2d2d2d;
                    color: {candle_type["color"]};
                    border: 2px solid #404040;
                    border-radius: 4px;
                    padding: 8px;
                    text-align: left;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #353535;
                    border-color: {candle_type["color"]};
                }}
                QPushButton:checked {{
                    background-color: {candle_type["color"]};
                    color: #1e1e1e;
                    border-color: {candle_type["color"]};
                }}
            """)

            # Add icon if available
            icon = self._get_candle_icon(candle_type["icon"])
            if icon:
                btn.setIcon(icon)

            # Connect signal
            btn.clicked.connect(self._on_candle_type_selected)

            # Add to button group
            self.candle_button_group.addButton(btn)

            # Add to toolbar
            self.addWidget(btn)

            # Store reference
            self.candle_buttons[candle_type["id"]] = btn

        # Select default type (bullish)
        if "bullish" in self.candle_buttons:
            self.candle_buttons["bullish"].setChecked(True)

    def _create_action_buttons(self):
        """Create add/remove/clear action buttons."""
        # Label
        label = QLabel("  Actions:  ")
        label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: bold; padding: 4px;")
        self.addWidget(label)

        # Add Candle button
        self.add_btn = QPushButton(cel_icons.add_candle, "Add Candle")
        self.add_btn.setObjectName("primary")  # Primary button style
        self.add_btn.setToolTip("Add selected candle type to canvas (at center)")
        self.add_btn.setIconSize(QSize(24, 24))
        self.add_btn.clicked.connect(self._on_add_candle_clicked)
        self.addWidget(self.add_btn)

        # Remove Selected button
        self.remove_btn = QPushButton(cel_icons.delete_candle, "Remove")
        self.remove_btn.setToolTip("Remove selected candle(s) from canvas")
        self.remove_btn.setIconSize(QSize(24, 24))
        self.remove_btn.clicked.connect(self._on_remove_candle_clicked)
        self.addWidget(self.remove_btn)

        # Clear All button
        self.clear_btn = QPushButton(cel_icons.clear_all, "Clear All")
        self.clear_btn.setToolTip("Clear all candles from pattern")
        self.clear_btn.setIconSize(QSize(24, 24))
        self.clear_btn.clicked.connect(self._on_clear_pattern_clicked)
        self.addWidget(self.clear_btn)

        # Separator
        self.addSeparator()

        # Zoom Controls Label
        zoom_label = QLabel("  View:  ")
        zoom_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: bold; padding: 4px;")
        self.addWidget(zoom_label)

        # Zoom Fit button (analog zu Chart: "Alles zoomen")
        self.zoom_fit_btn = QPushButton(cel_icons.zoom_fit, "Alles zoomen")
        self.zoom_fit_btn.setToolTip("Zoom to fit all candles in view")
        self.zoom_fit_btn.setIconSize(QSize(24, 24))
        self.zoom_fit_btn.clicked.connect(self._on_zoom_fit_clicked)
        self.addWidget(self.zoom_fit_btn)

        # Zoom Back button (analog zu Chart: "Zurück")
        self.zoom_back_btn = QPushButton(cel_icons.back, "Zurück")
        self.zoom_back_btn.setToolTip("Zurück zur vorherigen Ansicht")
        self.zoom_back_btn.setIconSize(QSize(24, 24))
        self.zoom_back_btn.clicked.connect(self._on_zoom_back_clicked)
        self.addWidget(self.zoom_back_btn)

    def _get_candle_icon(self, icon_name: str) -> Optional[QIcon]:
        """Get icon for candle type.

        Args:
            icon_name: Icon name (navigation category)

        Returns:
            QIcon or None if not found
        """
        try:
            return cel_icons.loader.get_icon('navigation', icon_name)
        except Exception:
            # Icon not found, return None
            return None

    def _on_candle_type_selected(self):
        """Handle candle type button click."""
        # Find which button was clicked
        sender = self.sender()
        if sender and sender.isChecked():
            candle_type = sender.property("candle_type")
            self.active_candle_type = candle_type

            # Update add button text
            self.add_btn.setText(f"Add {sender.text()}")

    def _on_add_candle_clicked(self):
        """Handle add candle button click."""
        if self.active_candle_type:
            self.candle_add_requested.emit(self.active_candle_type)

    def _on_remove_candle_clicked(self):
        """Handle remove candle button click."""
        self.candle_remove_requested.emit()

    def _on_clear_pattern_clicked(self):
        """Handle clear pattern button click."""
        self.pattern_clear_requested.emit()

    def _on_zoom_fit_clicked(self):
        """Handle zoom fit button click (analog zu Chart: 'Alles zoomen')."""
        self.zoom_fit_requested.emit()

    def _on_zoom_back_clicked(self):
        """Handle zoom back button click (analog zu Chart: 'Zurück')."""
        self.zoom_back_requested.emit()

    def set_active_candle_type(self, candle_type: str):
        """Set active candle type programmatically.

        Args:
            candle_type: Candle type ID (bullish, bearish, doji, etc.)
        """
        if candle_type in self.candle_buttons:
            self.candle_buttons[candle_type].setChecked(True)
            self.active_candle_type = candle_type
            self.add_btn.setText(f"Add {self.candle_buttons[candle_type].text()}")

    def get_active_candle_type(self) -> Optional[str]:
        """Get currently selected candle type.

        Returns:
            Candle type ID or None
        """
        return self.active_candle_type
