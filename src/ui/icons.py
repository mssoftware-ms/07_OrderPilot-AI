"""Icon provider for OrderPilot-AI using Google Material Design PNGs.

Loads pre-processed white icons from src/ui/assets/icons.
Icons are automatically inverted from black to white with transparent background.
"""
import os
import logging
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)

# Default base path for icons relative to this file
DEFAULT_ICONS_DIR = Path(__file__).parent / "assets" / "icons"

def invert_icon_to_white(icon_path: Path) -> QPixmap:
    """Invertiert schwarze Icons zu weiß mit transparentem Hintergrund.

    Args:
        icon_path: Pfad zum schwarzen Icon

    Returns:
        QPixmap mit weißem Icon auf transparentem Hintergrund
    """
    # Lade das Original-Icon
    original = QPixmap(str(icon_path))
    if original.isNull():
        logger.warning(f"Failed to load icon: {icon_path}")
        return QPixmap()

    # Erstelle neues Pixmap mit Alpha-Kanal
    inverted = QPixmap(original.size())
    inverted.fill(Qt.GlobalColor.transparent)

    # Erstelle QImage für Pixel-Manipulation
    img = original.toImage().convertToFormat(QImage.Format.Format_ARGB32)

    # Invertiere schwarz zu weiß, behalte Alpha
    for y in range(img.height()):
        for x in range(img.width()):
            pixel = img.pixelColor(x, y)
            if pixel.alpha() > 0:  # Nur nicht-transparente Pixel
                # Setze zu Weiß, behalte Alpha
                pixel.setRgb(255, 255, 255, pixel.alpha())
                img.setPixelColor(x, y, pixel)

    return QPixmap.fromImage(img)


class IconProvider:
    """Provides PNG-based icons for the application."""

    def __init__(self, theme: str = "dark", invert_to_white: bool = True, icons_dir: Path = None):
        """Initialize icon provider.

        Args:
            theme: Theme name ("dark" or "light")
            invert_to_white: If True, inverts black icons to white automatically
            icons_dir: Optional custom path to icons directory
        """
        self.theme = theme
        self.invert_to_white = invert_to_white
        self.icons_dir = icons_dir or DEFAULT_ICONS_DIR
        self._cache = {}

    def configure(self, icons_dir: str | Path | None = None, invert_to_white: bool | None = None):
        """Update provider configuration.

        Args:
            icons_dir: New icons directory path
            invert_to_white: New inversion setting
        """
        if icons_dir is not None:
            self.icons_dir = Path(icons_dir)
        if invert_to_white is not None:
            self.invert_to_white = invert_to_white
        
        self._cache.clear()
        logger.info(f"IconProvider reconfigured: dir={self.icons_dir}, invert={self.invert_to_white}")

    def set_theme(self, theme: str):
        """Change theme.

        Currently icons are white-only (requested), so this just clears cache.
        """
        self.theme = theme
        self._cache.clear()

    def get_icon(self, name: str) -> QIcon:
        """Get icon by name from PNG assets.

        Args:
            name: Icon name (e.g., 'chart', 'settings')

        Returns:
            QIcon instance (inverted to white if invert_to_white=True)
        """
        cache_key = f"{name}_{'white' if self.invert_to_white else 'original'}_{hash(str(self.icons_dir))}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        icon_path = self.icons_dir / f"{name}.png"

        if icon_path.exists():
            if self.invert_to_white:
                # Issue #15: Invertiere schwarze Material Design Icons zu weiß
                pixmap = invert_icon_to_white(icon_path)
                icon = QIcon(pixmap)
            else:
                icon = QIcon(str(icon_path))

            self._cache[cache_key] = icon
            return icon
        else:
            logger.warning(f"Icon not found: {icon_path}")
            # Return empty icon as fallback
            return QIcon()

    def get_available_icons(self) -> list[str]:
        """Get list of available icon names based on files in assets.

        Returns:
            List of icon names
        """
        if not self.icons_dir.exists():
            return []
        return [f.stem for f in self.icons_dir.glob("*.png")]


# Global icon provider instance
_icon_provider = IconProvider()


def get_icon(name: str) -> QIcon:
    """Get icon by name using global provider."""
    return _icon_provider.get_icon(name)


def set_icon_theme(theme: str):
    """Set global icon theme."""
    _icon_provider.set_theme(theme)


def configure_icon_provider(icons_dir: str | Path | None = None, invert_to_white: bool | None = None):
    """Configure the global icon provider."""
    _icon_provider.configure(icons_dir, invert_to_white)


def get_available_icons() -> list[str]:
    """Get available icon names."""
    return _icon_provider.get_available_icons()
