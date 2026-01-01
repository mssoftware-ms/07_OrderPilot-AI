from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QIcon, QPixmap

def _load_app_icon() -> QIcon:
    """Load application icon from marketing assets."""
    root_dir = Path(__file__).resolve().parents[2]
    icon_dir = root_dir / "02_Marketing" / "Icons"
    png_icon = icon_dir / "Icon-Orderpilot-AI-Arrow2-256x256.png"
    ico_icon = icon_dir / "Icon-Orderpilot-AI-256x256.ico"

    if png_icon.exists():
        return QIcon(str(png_icon))
    if ico_icon.exists():
        return QIcon(str(ico_icon))

    logger.warning("Application icon not found in %s", icon_dir)
    return QIcon()

def _get_startup_icon_path() -> Path:
    root_dir = Path(__file__).resolve().parents[2]
    return root_dir / "02_Marketing" / "Icons" / "Icon-Orderpilot-AI-Arrow2.png"
