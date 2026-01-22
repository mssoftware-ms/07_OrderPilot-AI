"""Script to copy Google Material Design icons to project workspace.

This script finds and copies relevant icons from the Material Design icon library
and converts them to white with transparent background for use in the Entry Analyzer.

Icons needed for Entry Analyzer:
- settings (⚙️)
- trending_up (📈)
- build (🔧)
- search (🔍)
- analytics (📊)
- smart_toy (🤖)
- check_circle (✅)
- gps_fixed (🎯)
- refresh (🔄)
- description (📄)
- place (📍)
- delete (🗑️)
- visibility (👁️)
- timeline (📉)
- tune (🎛️)
- play_arrow (▶️)
- stop (⏹️)
- auto_awesome (✨)
"""

import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Icon mapping: (emoji/description, material_icon_name)
ICONS_TO_COPY = {
    # Main tabs
    "settings": "settings",  # ⚙️ Backtest Setup, Parameter Configuration
    "trending_up": "trending_up",  # 📈 Backtest Results
    "build": "build",  # 🔧 Indicator Optimization
    "search": "search",  # 🔍 Pattern Recognition
    "analytics": "analytics",  # 📊 Visible Range, Results
    "smart_toy": "smart_toy",  # 🤖 AI Copilot
    "check_circle": "check_circle",  # ✅ Validation, apply
    "gps_fixed": "gps_fixed",  # 🎯 Target/Entry

    # Actions
    "refresh": "refresh",  # 🔄 Analyze
    "description": "description",  # 📄 Report
    "place": "place",  # 📍 Draw/Place markers
    "delete": "delete",  # 🗑️ Clear
    "visibility": "visibility",  # 👁️ Show/View
    "timeline": "timeline",  # 📉 Chart data
    "tune": "tune",  # 🎛️ Optimize/Tune
    "play_arrow": "play_arrow",  # ▶️ Run/Execute
    "stop": "stop_circle",  # ⏹️ Stop
    "auto_awesome": "auto_awesome",  # ✨ AI/Auto features
    "show_chart": "show_chart",  # 📈 Charts
    "assessment": "assessment",  # 📊 Assessment
    "insights": "insights",  # 💡 Insights
    "whatshot": "whatshot",  # 🔥 Hot/Active
    "psychology": "psychology",  # 🧠 AI/Pattern
    "extension": "extension",  # 🧩 Indicators
    "bar_chart": "bar_chart",  # 📊 Bar charts
    "candlestick_chart": "candlestick_chart",  # 📊 Candlestick
    "filter_alt": "filter_alt",  # 🔽 Filter
    "folder_open": "folder_open",  # 📂 Open file
    "save": "save",  # 💾 Save
    "download": "download",  # ⬇️ Download
    "upload": "upload",  # ⬆️ Upload
}


def find_icon_file(source_dir: Path, icon_name: str, size: str = "24dp") -> Path | None:
    """Find Material Design icon file.

    Args:
        source_dir: Root directory of Material Design icons
        icon_name: Name of the icon (e.g., 'settings')
        size: Icon size (24dp recommended for UI)

    Returns:
        Path to icon file or None if not found
    """
    # Try different categories
    categories = ["action", "content", "navigation", "editor", "image", "av",
                  "device", "communication", "file", "hardware", "maps", "notification",
                  "places", "social", "toggle", "alert"]

    for category in categories:
        # Try baseline (filled) style first at 24dp/1x
        icon_path = (
            source_dir / category / icon_name / "materialicons" / size / "1x"
            / f"baseline_{icon_name}_black_{size}.png"
        )
        if icon_path.exists():
            return icon_path

    return None


def copy_icons(source_dir: Path, target_dir: Path) -> dict[str, Path]:
    """Copy Material Design icons to target directory.

    Args:
        source_dir: Source directory containing Material Design icons
        target_dir: Target directory in project workspace

    Returns:
        Dictionary mapping icon names to target paths
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = {}

    logger.info(f"Searching for icons in: {source_dir}")
    logger.info(f"Target directory: {target_dir}")

    for dest_name, icon_name in ICONS_TO_COPY.items():
        source_file = find_icon_file(source_dir, icon_name)

        if source_file:
            target_file = target_dir / f"{dest_name}.png"
            shutil.copy2(source_file, target_file)
            copied[dest_name] = target_file
            logger.info(f"✅ Copied: {dest_name}.png from {source_file.parent.parent.parent.parent.name}")
        else:
            logger.warning(f"❌ Not found: {icon_name}")

    logger.info(f"\n✅ Successfully copied {len(copied)}/{len(ICONS_TO_COPY)} icons")
    return copied


def main():
    """Main execution function."""
    # Paths
    source_dir = Path("/mnt/d/03_Git/01_Global/01_GlobalDoku/google_material-design-icons-master/png")
    project_root = Path(__file__).parent.parent
    target_dir = project_root / "src" / "ui" / "assets" / "icons"

    logger.info("=" * 60)
    logger.info("Google Material Design Icons Copy Script")
    logger.info("=" * 60)

    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        return 1

    # Copy icons
    copied = copy_icons(source_dir, target_dir)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Summary")
    logger.info("=" * 60)
    logger.info(f"Total icons to copy: {len(ICONS_TO_COPY)}")
    logger.info(f"Successfully copied: {len(copied)}")
    logger.info(f"Target directory: {target_dir}")
    logger.info("\nNote: Icons will be automatically converted to white with")
    logger.info("transparent background by the IconProvider when loaded.")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
