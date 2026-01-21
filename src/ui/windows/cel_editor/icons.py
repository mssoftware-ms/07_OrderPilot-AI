"""Material Design Icons Loader for CEL Editor.

Loads Google Material Icons from the global icon repository.
Path: /mnt/d/03_Git/01_Global/01_GlobalDoku/google_material-design-icons-master/png
"""

import os
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap, QImage, QColor
from PyQt6.QtCore import QSize, Qt


# Global Material Icons Repository Path (detect Windows vs WSL)
import platform
if platform.system() == "Windows":
    MATERIAL_ICONS_BASE = Path("D:/03_Git/01_Global/01_GlobalDoku/google_material-design-icons-master/png")
else:
    MATERIAL_ICONS_BASE = Path("/mnt/d/03_Git/01_Global/01_GlobalDoku/google_material-design-icons-master/png")

class MaterialIconLoader:
    """Loader for Google Material Design Icons."""

    def __init__(self, base_path: Path = MATERIAL_ICONS_BASE):
        """Initialize icon loader.

        Args:
            base_path: Base path to Material Icons PNG directory.
        """
        self.base_path = base_path
        self._cache: dict[str, QIcon] = {}

    def _invert_to_white(self, pixmap: QPixmap) -> QPixmap:
        """Invert black icon to white while preserving transparency."""
        if pixmap.isNull():
            return pixmap
            
        img = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        for y in range(img.height()):
            for x in range(img.width()):
                pixel = img.pixelColor(x, y)
                if pixel.alpha() > 0:
                    pixel.setRgb(255, 255, 255, pixel.alpha())
                    img.setPixelColor(x, y, pixel)
        return QPixmap.fromImage(img)

    def get_icon(
        self,
        category: str,
        name: str,
        variant: str = "baseline",
        color: str = "black",
        size: str = "24dp",
        density: str = "1x"
    ) -> QIcon:
        """Load Material Design Icon.

        Args:
            category: Icon category (e.g., 'action', 'content', 'navigation')
            name: Icon name (e.g., 'settings', 'add', 'delete')
            variant: Icon variant ('baseline', 'outline', 'round', 'sharp', 'twotone')
            color: Icon color ('black', 'white')
            size: Icon size ('18dp', '24dp', '36dp', '48dp')
            density: Screen density ('1x', '2x', '3x')

        Returns:
            QIcon object loaded from PNG file.

        Example:
            >>> loader = MaterialIconLoader()
            >>> icon = loader.get_icon('action', 'settings')
            >>> icon = loader.get_icon('content', 'add', variant='baseline', size='24dp')
        """
        # Create cache key
        cache_key = f"{category}/{name}/{variant}_{color}_{size}_{density}"

        # Check cache
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Build icon path
        # Example: action/settings/materialicons/24dp/1x/baseline_settings_black_24dp.png
        icon_filename = f"{variant}_{name}_{color}_{size}.png"
        icon_path = (
            self.base_path
            / category
            / name
            / "materialicons"
            / size
            / density
            / icon_filename
        )

        # Load icon
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            if color == "white":
                pixmap = self._invert_to_white(pixmap)
            icon = QIcon(pixmap)
            self._cache[cache_key] = icon
            return icon
        else:
            # Return empty icon if not found
            # print(f"⚠️  Icon not found: {icon_path}")
            return QIcon()

    def get_pixmap(
        self,
        category: str,
        name: str,
        variant: str = "baseline",
        color: str = "black",
        size: str = "24dp",
        density: str = "1x",
        scaled_size: QSize | None = None
    ) -> QPixmap:
        """Load Material Design Icon as QPixmap.

        Args:
            category: Icon category
            name: Icon name
            variant: Icon variant
            color: Icon color
            size: Icon size
            density: Screen density
            scaled_size: Optional QSize to scale the pixmap

        Returns:
            QPixmap object.
        """
        icon = self.get_icon(category, name, variant, color, size, density)

        if scaled_size:
            return icon.pixmap(scaled_size)
        else:
            # Extract size number (e.g., '24dp' → 24)
            size_px = int(size.replace('dp', ''))
            return icon.pixmap(QSize(size_px, size_px))

    def list_available_icons(self, category: str) -> list[str]:
        """List all available icons in a category.

        Args:
            category: Icon category (e.g., 'action', 'content')

        Returns:
            List of icon names in the category.
        """
        category_path = self.base_path / category
        if not category_path.exists():
            return []

        # List all subdirectories (icon names)
        return [
            d.name for d in category_path.iterdir()
            if d.is_dir() and (d / "materialicons").exists()
        ]

    def list_categories(self) -> list[str]:
        """List all available icon categories.

        Returns:
            List of category names.
        """
        if not self.base_path.exists():
            return []

        return [
            d.name for d in self.base_path.iterdir()
            if d.is_dir()
        ]


# Pre-defined icon constants for CEL Editor
class CelEditorIcons:
    """Pre-defined Material Icons for CEL Editor UI."""

    def __init__(self, loader: MaterialIconLoader | None = None):
        """Initialize with optional custom loader."""
        self.loader = loader or MaterialIconLoader()

    # Pre-defined icon constants for CEL Editor
    def _get_icon(self, category: str, name: str) -> QIcon:
        """Helper to get white icon."""
        return self.loader.get_icon(category, name, color="white")

    # Toolbar icons
    @property
    def new_file(self) -> QIcon:
        return self._get_icon('action', 'note_add')

    @property
    def open_file(self) -> QIcon:
        return self._get_icon('file', 'folder_open')

    @property
    def save(self) -> QIcon:
        return self._get_icon('content', 'save')

    @property
    def undo(self) -> QIcon:
        return self._get_icon('content', 'undo')

    @property
    def redo(self) -> QIcon:
        return self._get_icon('content', 'redo')

    # View mode icons
    @property
    def view_pattern(self) -> QIcon:
        return self._get_icon('action', 'view_module')

    @property
    def view_code(self) -> QIcon:
        return self._get_icon('action', 'code')

    @property
    def view_chart(self) -> QIcon:
        return self._get_icon('editor', 'show_chart')

    @property
    def view_split(self) -> QIcon:
        return self._get_icon('action', 'view_agenda')

    # Pattern Builder icons
    @property
    def add_candle(self) -> QIcon:
        return self._get_icon('content', 'add')

    @property
    def delete_candle(self) -> QIcon:
        return self._get_icon('action', 'delete')

    @property
    def clear_all(self) -> QIcon:
        return self._get_icon('content', 'clear')

    @property
    def zoom_in(self) -> QIcon:
        return self._get_icon('action', 'zoom_in')

    @property
    def zoom_out(self) -> QIcon:
        return self._get_icon('action', 'zoom_out')

    @property
    def zoom_fit(self) -> QIcon:
        return self._get_icon('maps', 'zoom_out_map')

    @property
    def back(self) -> QIcon:
        return self._get_icon('navigation', 'arrow_back')

    # AI Assistant icons
    @property
    def ai_generate(self) -> QIcon:
        return self._get_icon('action', 'auto_awesome')

    @property
    def ai_suggest(self) -> QIcon:
        return self._get_icon('action', 'tips_and_updates')

    # Settings icons
    @property
    def settings(self) -> QIcon:
        return self._get_icon('action', 'settings')

    @property
    def help(self) -> QIcon:
        return self._get_icon('action', 'help')


# Global icon loader instance
icon_loader = MaterialIconLoader()
cel_icons = CelEditorIcons(icon_loader)
