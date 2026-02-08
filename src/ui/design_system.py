"""
Design System for OrderPilot-AI (PyQt6).

Defines atomic design tokens (Colors, Spacing, Typography) to ensure
consistency across the application.

Also provides ThemeService singleton for centralized theme management
and change notifications.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Callable, List
import logging

logger = logging.getLogger(__name__)

@dataclass
class ColorPalette:
    """Defines a semantic color palette."""
    name: str
    
    # Backgrounds
    background_main: str    # Main window background
    background_surface: str # Cards, panels, docked widgets
    background_input: str   # Text inputs, tables
    
    # Borders & Dividers
    border_main: str
    border_focus: str
    
    # Text
    text_primary: str       # High emphasis
    text_secondary: str     # Medium emphasis (labels)
    text_inverse: str       # Text on primary color
    
    # Brand / Action
    primary: str            # Main accent color (Orange/White)
    primary_hover: str
    primary_pressed: str
    
    # Functional
    success: str
    warning: str
    error: str
    info: str
    
    # Components
    selection_bg: str
    selection_text: str
    
    # Specific Button Styling
    button_background: str
    button_border: str
    button_text: str
    button_hover_border: str
    button_hover_text: str


@dataclass
class Typography:
    """Defines font settings."""
    font_family: str = "'Aptos', 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif"
    size_xs: str = "11px"
    size_sm: str = "12px"
    size_md: str = "14px" # Base size
    size_lg: str = "16px"
    size_xl: str = "18px"
    
@dataclass
class Spacing:
    """Defines spacing tokens."""
    xs: str = "2px"
    sm: str = "4px"
    md: str = "8px"
    lg: str = "16px"
    xl: str = "24px"
    radius_sm: str = "4px"
    radius_md: str = "6px"
    # Button height
    button_height: str = "32px"

# --- THEMES ---

DARK_ORANGE_PALETTE = ColorPalette(
    name="Dark Orange",
    background_main="#0F1115",    # Very dark grey/black
    background_surface="#1A1D23", # Slightly lighter
    background_input="#23262E",
    
    border_main="#32363E",
    border_focus="#F29F05",
    
    text_primary="#EAECEF",
    text_secondary="#848E9C",
    text_inverse="#0F1115",
    
    primary="#F29F05",        # Bright Orange
    primary_hover="#FFAD1F",
    primary_pressed="#D98A00",
    
    success="#0ECB81",
    warning="#F6465D",
    error="#F6465D",
    info="#5D6878",
    
    selection_bg="rgba(242, 159, 5, 0.2)",
    selection_text="#F29F05",
    
    # Standard Dark Orange Buttons
    button_background="#2A2D33",
    button_border="#3A3D43",
    button_text="#EAECEF",
    button_hover_border="#F29F05",
    button_hover_text="#F29F05"
)

DARK_WHITE_PALETTE = ColorPalette(
    name="Dark White",
    background_main="#09090b",    # Zinc-950
    background_surface="#18181b", # Zinc-900
    background_input="#27272a",   # Zinc-800
    
    border_main="#3f3f46",        # Zinc-700
    border_focus="#ffffff",
    
    text_primary="#f4f4f5",       # Zinc-100
    text_secondary="#a1a1aa",     # Zinc-400
    text_inverse="#09090b",
    
    primary="#ffffff",            # Pure White
    primary_hover="#e4e4e7",      # Zinc-200
    primary_pressed="#d4d4d8",    # Zinc-300
    
    success="#4ade80",
    warning="#fbbf24",
    error="#f87171",
    info="#94a3b8",
    
    selection_bg="rgba(255, 255, 255, 0.15)",
    selection_text="#ffffff",
    
    # User Requested: Black button, White border, White text
    button_background="#000000",
    button_border="#FFFFFF",
    button_text="#FFFFFF",
    button_hover_border="#FFFFFF",
    button_hover_text="#000000"
)

# Available themes map
THEMES: Dict[str, ColorPalette] = {
    "dark_orange": DARK_ORANGE_PALETTE,
    "dark_white": DARK_WHITE_PALETTE,
    # Mapping legacy names for compatibility
    "dark": DARK_ORANGE_PALETTE,
    "light": DARK_ORANGE_PALETTE # Fallback for now, user didn't request Light
}


# ==============================================================================
# ThemeService - Centralized Theme Management with Change Notifications
# ==============================================================================

class ThemeService:
    """Singleton service for centralized theme management.

    Provides:
    - Current theme palette access
    - Theme change notifications via callbacks
    - Automatic QSettings synchronization

    Usage:
        from src.ui.design_system import theme_service

        # Get current palette
        palette = theme_service.get_palette()

        # Subscribe to changes (widget should call this in __init__)
        theme_service.subscribe(self._on_theme_changed)

        # Unsubscribe (widget should call this in closeEvent or destructor)
        theme_service.unsubscribe(self._on_theme_changed)

        # Change theme (only SettingsDialog/main app should call this)
        theme_service.set_theme("Dark White")
    """

    _instance: Optional["ThemeService"] = None

    def __new__(cls) -> "ThemeService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._subscribers: List[Callable[[ColorPalette], None]] = []
        self._current_theme_name: str = "Dark Orange"
        self._current_palette: ColorPalette = DARK_ORANGE_PALETTE

        # Load initial theme from QSettings
        self._load_from_settings()

    def _load_from_settings(self) -> None:
        """Load the current theme from QSettings."""
        try:
            from PyQt6.QtCore import QSettings
            settings = QSettings("OrderPilot", "TradingApp")
            theme_name = settings.value("theme/name", settings.value("theme", "Dark Orange"))
            self._set_theme_internal(theme_name, notify=False)
        except Exception as e:
            logger.debug(f"Could not load theme from settings: {e}")

    def _set_theme_internal(self, theme_name: str, notify: bool = True) -> None:
        """Internal theme setter."""
        key = theme_name.lower().replace(" ", "_")
        palette = THEMES.get(key, DARK_ORANGE_PALETTE)

        old_name = self._current_theme_name
        self._current_theme_name = theme_name
        self._current_palette = palette

        if notify and old_name != theme_name:
            self._notify_subscribers()

    def _notify_subscribers(self) -> None:
        """Notify all subscribers of theme change."""
        logger.debug(f"Theme changed to '{self._current_theme_name}', notifying {len(self._subscribers)} subscribers")
        for callback in self._subscribers[:]:  # Copy list to allow unsubscribe during iteration
            try:
                callback(self._current_palette)
            except Exception as e:
                logger.error(f"Error notifying theme subscriber: {e}")

    # --- Public API ---

    def get_palette(self) -> ColorPalette:
        """Get the current theme palette."""
        return self._current_palette

    def get_theme_name(self) -> str:
        """Get the current theme name."""
        return self._current_theme_name

    def set_theme(self, theme_name: str) -> None:
        """Set the current theme and notify all subscribers.

        Args:
            theme_name: Theme name (e.g., "Dark Orange", "Dark White")
        """
        self._set_theme_internal(theme_name, notify=True)

        # Also save to QSettings
        try:
            from PyQt6.QtCore import QSettings
            settings = QSettings("OrderPilot", "TradingApp")
            settings.setValue("theme/name", theme_name)
            settings.setValue("theme", theme_name)  # Legacy key
        except Exception as e:
            logger.error(f"Could not save theme to settings: {e}")

    def subscribe(self, callback: Callable[[ColorPalette], None]) -> None:
        """Subscribe to theme changes.

        Args:
            callback: Function to call when theme changes. Receives new ColorPalette.
        """
        if callback not in self._subscribers:
            self._subscribers.append(callback)
            logger.debug(f"Theme subscriber added, total: {len(self._subscribers)}")

    def unsubscribe(self, callback: Callable[[ColorPalette], None]) -> None:
        """Unsubscribe from theme changes.

        Args:
            callback: Previously subscribed callback function.
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
            logger.debug(f"Theme subscriber removed, total: {len(self._subscribers)}")

    def refresh(self) -> None:
        """Force refresh from QSettings and notify subscribers.

        Use after settings dialog closes to ensure all widgets update.
        """
        self._load_from_settings()
        self._notify_subscribers()


# Global singleton instance
theme_service = ThemeService()
