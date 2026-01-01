"""Icon provider for OrderPilot-AI with dual-color SVG support.

Provides SVG-based icons that work in both light and dark modes.
"""

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer


def _svg_to_icon(svg_data: str, primary_color: str = "#FFFFFF", secondary_color: str = "#4A9EFF") -> QIcon:
    """Convert SVG string to QIcon with color substitution.

    Args:
        svg_data: SVG XML string with {{primary}} and {{secondary}} placeholders
        primary_color: Primary color (default: white)
        secondary_color: Secondary color (default: blue)

    Returns:
        QIcon with rendered SVG
    """
    # Substitute colors
    svg_colored = svg_data.replace("{{primary}}", primary_color)
    svg_colored = svg_colored.replace("{{secondary}}", secondary_color)

    # Render SVG
    svg_bytes = QByteArray(svg_colored.encode('utf-8'))
    renderer = QSvgRenderer(svg_bytes)

    # Create pixmap
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)


# SVG icon templates
_ICONS = {
    "chart": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 3v18h18" stroke="{{primary}}" stroke-width="2" fill="none" stroke-linecap="round"/>
        <path d="M7 13l4-4 3 3 5-5" stroke="{{secondary}}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="7" cy="13" r="1.5" fill="{{secondary}}"/>
        <circle cx="11" cy="9" r="1.5" fill="{{secondary}}"/>
        <circle cx="14" cy="12" r="1.5" fill="{{secondary}}"/>
        <circle cx="19" cy="7" r="1.5" fill="{{secondary}}"/>
    </svg>
    """,

    "order": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <rect x="4" y="4" width="16" height="16" rx="2" stroke="{{primary}}" stroke-width="2" fill="none"/>
        <path d="M8 12h8M12 8v8" stroke="{{secondary}}" stroke-width="2" stroke-linecap="round"/>
    </svg>
    """,

    "settings": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="3" stroke="{{secondary}}" stroke-width="2" fill="none"/>
        <path d="M12 3v2m0 14v2M21 12h-2M5 12H3m15.364-6.364l-1.414 1.414M7.05 16.95l-1.414 1.414m12.728 0l-1.414-1.414M7.05 7.05L5.636 5.636" stroke="{{primary}}" stroke-width="2" stroke-linecap="round"/>
    </svg>
    """,

    "connect": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <circle cx="18" cy="6" r="3" stroke="{{secondary}}" stroke-width="2" fill="none"/>
        <circle cx="6" cy="18" r="3" stroke="{{secondary}}" stroke-width="2" fill="none"/>
        <path d="M8.5 16.5l7-7" stroke="{{primary}}" stroke-width="2" stroke-linecap="round"/>
    </svg>
    """,

    "disconnect": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <circle cx="18" cy="6" r="3" stroke="{{secondary}}" stroke-width="2" fill="none"/>
        <circle cx="6" cy="18" r="3" stroke="{{secondary}}" stroke-width="2" fill="none"/>
        <path d="M9 15l-1 1m7-7l1-1" stroke="{{primary}}" stroke-width="2" stroke-linecap="round"/>
        <path d="M5 5l14 14" stroke="{{primary}}" stroke-width="2" stroke-linecap="round"/>
    </svg>
    """,

    "refresh": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M21 12a9 9 0 11-9-9c2.52 0 4.77 1.03 6.4 2.7L21 8" stroke="{{primary}}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M21 3v5h-5" stroke="{{secondary}}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """,

    "watchlist": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 5.5l2.5 5 5.5.8-4 3.9.9 5.3-4.9-2.6-4.9 2.6.9-5.3-4-3.9 5.5-.8z" stroke="{{primary}}" stroke-width="2" fill="{{secondary}}" fill-opacity="0.3"/>
    </svg>
    """,

    "data_source": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="12" cy="6" rx="8" ry="3" stroke="{{primary}}" stroke-width="2" fill="none"/>
        <path d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6" stroke="{{primary}}" stroke-width="2" fill="none"/>
        <path d="M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" stroke="{{secondary}}" stroke-width="2" fill="none"/>
    </svg>
    """,

    "backtest": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <rect x="3" y="3" width="18" height="18" rx="2" stroke="{{primary}}" stroke-width="2" fill="none"/>
        <path d="M3 9h18M9 3v18" stroke="{{primary}}" stroke-width="2"/>
        <path d="M12 12l3 3 3-3" stroke="{{secondary}}" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """,

    "portfolio": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <rect x="4" y="8" width="16" height="12" rx="2" stroke="{{primary}}" stroke-width="2" fill="none"/>
        <path d="M8 8V6a2 2 0 012-2h4a2 2 0 012 2v2" stroke="{{primary}}" stroke-width="2" fill="none"/>
        <path d="M12 12v4" stroke="{{secondary}}" stroke-width="2" stroke-linecap="round"/>
    </svg>
    """,

    "ai": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="9" stroke="{{primary}}" stroke-width="2" fill="none"/>
        <path d="M12 8v8M8 12h8" stroke="{{secondary}}" stroke-width="2" stroke-linecap="round"/>
        <circle cx="8" cy="8" r="1.5" fill="{{secondary}}"/>
        <circle cx="16" cy="8" r="1.5" fill="{{secondary}}"/>
        <circle cx="8" cy="16" r="1.5" fill="{{secondary}}"/>
        <circle cx="16" cy="16" r="1.5" fill="{{secondary}}"/>
        <path d="M12 5v2m0 10v2M5 12h2m10 0h2" stroke="{{primary}}" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    """,

    "optimize": """
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 18h18M3 12h18M3 6h18" stroke="{{primary}}" stroke-width="2" stroke-linecap="round"/>
        <circle cx="8" cy="6" r="2" fill="{{secondary}}" stroke="{{primary}}" stroke-width="1"/>
        <circle cx="16" cy="12" r="2" fill="{{secondary}}" stroke="{{primary}}" stroke-width="1"/>
        <circle cx="12" cy="18" r="2" fill="{{secondary}}" stroke="{{primary}}" stroke-width="1"/>
    </svg>
    """,
}


class IconProvider:
    """Provides themed icons for the application."""

    def __init__(self, theme: str = "dark"):
        """Initialize icon provider.

        Args:
            theme: Theme name ("dark" or "light")
        """
        self.theme = theme
        self._cache = {}
        self._update_colors()

    def _update_colors(self):
        """Update colors based on theme."""
        if self.theme == "dark":
            self.primary_color = "#E0E0E0"  # Light gray for dark mode
            self.secondary_color = "#4A9EFF"  # Blue accent
        else:
            self.primary_color = "#2C2C2C"  # Dark gray for light mode
            self.secondary_color = "#1976D2"  # Darker blue accent

    def set_theme(self, theme: str):
        """Change theme and clear cache.

        Args:
            theme: Theme name ("dark" or "light")
        """
        self.theme = theme
        self._update_colors()
        self._cache.clear()

    def get_icon(self, name: str) -> QIcon:
        """Get icon by name.

        Args:
            name: Icon name

        Returns:
            QIcon instance
        """
        cache_key = f"{name}_{self.theme}"

        if cache_key not in self._cache:
            if name in _ICONS:
                svg_data = _ICONS[name]
                self._cache[cache_key] = _svg_to_icon(
                    svg_data,
                    self.primary_color,
                    self.secondary_color
                )
            else:
                # Return empty icon if not found
                self._cache[cache_key] = QIcon()

        return self._cache[cache_key]

    def get_available_icons(self) -> list[str]:
        """Get list of available icon names.

        Returns:
            List of icon names
        """
        return list(_ICONS.keys())


# Global icon provider instance
_icon_provider = IconProvider()


def get_icon(name: str) -> QIcon:
    """Get icon by name using global provider.

    Args:
        name: Icon name

    Returns:
        QIcon instance
    """
    return _icon_provider.get_icon(name)


def set_icon_theme(theme: str):
    """Set global icon theme.

    Args:
        theme: Theme name ("dark" or "light")
    """
    _icon_provider.set_theme(theme)


def get_available_icons() -> list[str]:
    """Get list of available icon names.

    Returns:
        List of icon names
    """
    return _icon_provider.get_available_icons()
