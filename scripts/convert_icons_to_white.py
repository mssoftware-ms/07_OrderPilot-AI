#!/usr/bin/env python3
"""
Icon Converter - Material Design Icons zu Weiß mit transparentem Hintergrund

Kopiert relevante Icons aus dem Google Material Design Icons Repository,
konvertiert sie zu Weiß mit transparentem Hintergrund und speichert sie
im src/ui/icons/ Verzeichnis.

Usage:
    python scripts/convert_icons_to_white.py
"""

import os
import shutil
from pathlib import Path
from PIL import Image, ImageOps

# Pfade
ICONS_SOURCE = Path("/mnt/d/03_Git/01_Global/01_GlobalDoku/google_material-design-icons-master/png")
ICONS_DEST = Path("src/ui/icons")

# Icons die wir brauchen (Icon-Name → Material Icon Name)
REQUIRED_ICONS = {
    # Variable Reference Popup
    "search_white": "action/search/materialicons/24dp/1x/baseline_search_black_24dp.png",
    "copy_white": "content/content_copy/materialicons/24dp/1x/baseline_content_copy_black_24dp.png",
    "refresh_white": "navigation/refresh/materialicons/24dp/1x/baseline_refresh_black_24dp.png",
    "save_white": "content/save/materialicons/24dp/1x/baseline_save_black_24dp.png",
    "download_white": "file/file_download/materialicons/24dp/1x/baseline_file_download_black_24dp.png",
    "chevron_down_white": "navigation/expand_more/materialicons/24dp/1x/baseline_expand_more_black_24dp.png",
    "chevron_up_white": "navigation/expand_less/materialicons/24dp/1x/baseline_expand_less_black_24dp.png",
    "close_white": "navigation/close/materialicons/24dp/1x/baseline_close_black_24dp.png",
    "filter_white": "content/filter_list/materialicons/24dp/1x/baseline_filter_list_black_24dp.png",

    # Variable Manager
    "add_white": "content/add/materialicons/24dp/1x/baseline_add_black_24dp.png",
    "edit_white": "image/edit/materialicons/24dp/1x/baseline_edit_black_24dp.png",
    "delete_white": "action/delete/materialicons/24dp/1x/baseline_delete_black_24dp.png",
    "import_white": "file/upload/materialicons/24dp/1x/baseline_upload_black_24dp.png",
    "export_white": "file/file_download/materialicons/24dp/1x/baseline_file_download_black_24dp.png",

    # CEL Editor
    "code_white": "action/code/materialicons/24dp/1x/baseline_code_black_24dp.png",
    "play_white": "av/play_arrow/materialicons/24dp/1x/baseline_play_arrow_black_24dp.png",
    "check_white": "navigation/check/materialicons/24dp/1x/baseline_check_black_24dp.png",
    "error_white": "alert/error/materialicons/24dp/1x/baseline_error_black_24dp.png",
    "warning_white": "alert/warning/materialicons/24dp/1x/baseline_warning_black_24dp.png",
    "info_white": "action/info/materialicons/24dp/1x/baseline_info_black_24dp.png",
}


def convert_to_white_transparent(input_path: Path, output_path: Path):
    """
    Konvertiert ein schwarzes Icon zu Weiß mit transparentem Hintergrund.

    Args:
        input_path: Quell-PNG-Datei (schwarz)
        output_path: Ziel-PNG-Datei (weiß + transparent)
    """
    try:
        # Öffne Bild
        img = Image.open(input_path)

        # Konvertiere zu RGBA (mit Alpha-Kanal)
        img = img.convert("RGBA")

        # Hol pixel data
        data = img.getdata()

        # Neue Pixel-Liste
        new_data = []

        for item in data:
            # item = (R, G, B, A)
            # Wenn Pixel schwarz/dunkel (alle RGB < 128): Mache weiß
            # Wenn Pixel hell (alle RGB > 127): Mache transparent
            r, g, b, a = item

            # Durchschnitt von RGB
            avg = (r + g + b) / 3

            if avg < 128:  # Dunkles Pixel (Icon-Bereich)
                # Mache weiß, behalte Alpha
                new_data.append((255, 255, 255, a))
            else:  # Helles Pixel (Hintergrund)
                # Mache komplett transparent
                new_data.append((255, 255, 255, 0))

        # Update image data
        img.putdata(new_data)

        # Speichere als PNG mit Alpha
        img.save(output_path, "PNG")

        print(f"✅ Converted: {output_path.name}")
        return True

    except Exception as e:
        print(f"❌ Error converting {input_path.name}: {e}")
        return False


def main():
    """Main conversion function."""
    print("=" * 60)
    print("Icon Converter - Material Design → White + Transparent")
    print("=" * 60)
    print()

    # Erstelle Ziel-Verzeichnis
    ICONS_DEST.mkdir(parents=True, exist_ok=True)
    print(f"📁 Destination: {ICONS_DEST}")
    print()

    # Konvertiere alle Icons
    success_count = 0
    fail_count = 0

    for icon_name, source_relative_path in REQUIRED_ICONS.items():
        source_path = ICONS_SOURCE / source_relative_path
        dest_path = ICONS_DEST / f"{icon_name}.png"

        print(f"🔧 Processing: {icon_name}")
        print(f"   Source: {source_relative_path}")

        if not source_path.exists():
            print(f"   ⚠️  Source not found: {source_path}")
            fail_count += 1
            continue

        # Konvertiere zu Weiß + Transparent
        if convert_to_white_transparent(source_path, dest_path):
            success_count += 1
        else:
            fail_count += 1

        print()

    # Summary
    print("=" * 60)
    print("Summary:")
    print(f"  ✅ Success: {success_count}/{len(REQUIRED_ICONS)}")
    print(f"  ❌ Failed:  {fail_count}/{len(REQUIRED_ICONS)}")
    print("=" * 60)

    if fail_count > 0:
        print()
        print("⚠️  Some icons failed to convert. Check paths above.")
        return 1
    else:
        print()
        print("🎉 All icons converted successfully!")
        return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
