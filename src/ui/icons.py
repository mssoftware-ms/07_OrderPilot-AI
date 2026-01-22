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
DEFAULT_ICONS_DIR = (Path(__file__).parent / "assets" / "icons").resolve()
logger.debug(f"📢 DEFAULT_ICONS_DIR resolved to: {DEFAULT_ICONS_DIR}")

def invert_icon_to_white(icon_path: Path) -> QPixmap:
    """Invertiert schwarze Icons zu weiß mit transparentem Hintergrund.

    Args:
        icon_path: Pfad zum schwarzen Icon

    Returns:
        QPixmap mit weißem Icon auf transparentem Hintergrund

    BUG-005 FIX: Falls Inversion fehlschlägt, wird das Original-Icon zurückgegeben
    """
    # Lade das Original-Icon
    original_img = QImage(str(icon_path))
    if original_img.isNull():
        logger.error(f"❌ Failed to load icon image: {icon_path} (exists: {icon_path.exists()})")
        return QPixmap()

    logger.debug(f"🔄 Inverting icon to white: {icon_path.name} ({original_img.width()}x{original_img.height()})")

    # BUG-005 FIX: Try-except to fallback to original icon if inversion fails
    try:
        # Ensure we are in ARGB32 for transparency support
        if original_img.format() != QImage.Format.Format_ARGB32:
            original_img = original_img.convertToFormat(QImage.Format.Format_ARGB32)

        # Create a new image of the same size with transparency
        inverted_img = QImage(original_img.size(), QImage.Format.Format_ARGB32)
        inverted_img.fill(Qt.GlobalColor.transparent)

        # Use QPainter with CompositionMode to invert color while keeping alpha
        painter = QPainter(inverted_img)
        try:
            # 1. Draw original icon
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.drawImage(0, 0, original_img)

            # 2. SourceIn mode: keeps destination alpha but uses source color
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(inverted_img.rect(), QColor(255, 255, 255))
        finally:
            # BUG-005 FIX: Ensure painter.end() is always called
            painter.end()

        if inverted_img.isNull():
            logger.error(f"❌ Inversion result image is null for {icon_path.name}, using original")
            return QPixmap(str(icon_path))  # Fallback to original

        # Convert to QPixmap for display
        res = QPixmap.fromImage(inverted_img)
        if res.isNull():
            logger.error(f"❌ QPixmap.fromImage failed for {icon_path.name}, using original")
            return QPixmap(str(icon_path))  # Fallback to original
        else:
            logger.debug(f"✅ Inversion complete for {icon_path.name} using QImage+QPainter")

        return res

    except Exception as e:
        # BUG-005 FIX: Fallback to original icon on any exception
        logger.error(f"❌ Icon inversion failed for {icon_path.name}: {e}, using original")
        return QPixmap(str(icon_path))


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
        self.icons_dir = (icons_dir or DEFAULT_ICONS_DIR).resolve()
        self._cache = {}
        logger.debug(f"IconProvider initialized with icons_dir: {self.icons_dir}")

    def configure(self, icons_dir: str | Path | None = None, invert_to_white: bool | None = None):
        """Update provider configuration.

        Args:
            icons_dir: New icons directory path
            invert_to_white: New inversion setting
        """
        changed = False
        if icons_dir is not None:
            new_dir = Path(icons_dir).resolve()
            if self.icons_dir != new_dir:
                self.icons_dir = new_dir
                changed = True
        if invert_to_white is not None:
            if self.invert_to_white != invert_to_white:
                self.invert_to_white = invert_to_white
                changed = True

        if changed:
            self._cache.clear()
            logger.debug(f"IconProvider reconfigured and cache cleared: dir={self.icons_dir}, invert={self.invert_to_white}")
        else:
            logger.debug("IconProvider configuration unchanged, keeping cache.")

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
            file_size = icon_path.stat().st_size
            logger.debug(f"🔍 Loading icon {name}: {icon_path} ({file_size} bytes)")

            if self.invert_to_white:
                # Issue #15: Invertiere schwarze Material Design Icons zu weiß
                pixmap = invert_icon_to_white(icon_path)
                if pixmap.isNull():
                    logger.error(f"❌ Inversion failed for {name}, pixmap is null")
                icon = QIcon(pixmap)
            else:
                icon = QIcon(str(icon_path))

            self._cache[cache_key] = icon
            logger.debug(f"✅ Loaded icon: {name} from {icon_path}")
            return icon
        else:
            logger.error(f"❌ Icon NOT FOUND: {icon_path} (Base dir: {self.icons_dir})")
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


def refresh_icons():
    """Clear icon cache and force reload."""
    _icon_provider.configure()


def configure_icon_provider(icons_dir: str | Path | None = None, invert_to_white: bool | None = None):
    """Configure the global icon provider."""
    import traceback
    stack = "".join(traceback.format_stack()[-3:])
    logger.debug(f"🔧 configure_icon_provider called with dir={icons_dir}, invert={invert_to_white}\nCalled from:\n{stack}")
    _icon_provider.configure(icons_dir, invert_to_white)


def get_available_icons() -> list[str]:
    """Get available icon names."""
    return _icon_provider.get_available_icons()
