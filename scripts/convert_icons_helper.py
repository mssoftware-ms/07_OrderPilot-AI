#!/usr/bin/env python3
"""
Icon Conversion Helper - Detects available methods and guides user.

This script checks what image processing tools are available and provides
step-by-step instructions for converting icons from black to white.

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_imagemagick():
    """Check if ImageMagick is installed."""
    for cmd in ["magick", "convert"]:
        if shutil.which(cmd):
            return True, cmd
    return False, None


def check_pillow():
    """Check if Pillow is installed."""
    try:
        import PIL
        return True
    except ImportError:
        return False


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def main():
    """Main conversion helper."""
    print_header("🎨 Icon Conversion Helper")

    icons_dir = Path("src/ui/icons")
    if not icons_dir.exists():
        print("❌ Error: src/ui/icons directory not found!")
        print(f"   Current directory: {Path.cwd()}")
        print("   Please run from project root.")
        sys.exit(1)

    # Check what's available
    print("🔍 Checking available conversion methods...\n")

    has_imagemagick, magick_cmd = check_imagemagick()
    has_pillow = check_pillow()

    print(f"{'✅' if has_imagemagick else '❌'} ImageMagick: {magick_cmd if has_imagemagick else 'Not found'}")
    print(f"{'✅' if has_pillow else '❌'} Pillow (Python): {'Installed' if has_pillow else 'Not installed'}")
    print()

    # Count icons
    black_icons = list(icons_dir.glob("*_black.png"))
    white_icons = list(icons_dir.glob("*_white.png"))

    print(f"📊 Icon Status:")
    print(f"   Black icons: {len(black_icons)}")
    print(f"   White icons: {len(white_icons)}")
    print()

    if len(white_icons) >= 20:
        print("✅ All icons already converted!")
        return

    # Provide instructions based on available tools
    print_header("📋 Conversion Options")

    if has_imagemagick:
        print("✅ RECOMMENDED: Use ImageMagick (Available)")
        print("\n   Run the conversion script:")
        print("   $ ./scripts/convert_icons_to_white.sh")
        print()
    else:
        print("⚠️  OPTION 1: Install ImageMagick (Recommended)")
        print("\n   WSL/Linux:")
        print("   $ sudo apt-get update")
        print("   $ sudo apt-get install imagemagick")
        print("   $ ./scripts/convert_icons_to_white.sh")
        print()
        print("   Windows:")
        print("   1. Download: https://imagemagick.org/script/download.php#windows")
        print("   2. Install ImageMagick")
        print("   3. Run: scripts\\convert_icons_to_white.bat")
        print()

    if has_pillow:
        print("✅ OPTION 2: Use Python + Pillow (Available)")
        print("\n   Run the Python conversion script:")
        print("   $ python3 scripts/convert_icons_to_white.py")
        print()
    else:
        print("⚠️  OPTION 2: Install Pillow for Python")
        print("\n   Try installing Pillow:")
        print("   $ pip3 install --user Pillow")
        print("   $ python3 scripts/convert_icons_to_white.py")
        print()

    print("⚠️  OPTION 3: Manual Conversion")
    print("\n   Use GIMP or Photoshop:")
    print("   1. Open icon in GIMP/Photoshop")
    print("   2. Colors → Invert (Ctrl+I)")
    print("   3. Colors → Color to Alpha → Select white background")
    print("   4. Export as PNG with alpha channel")
    print("   5. Save to: src/ui/icons/<name>_white.png")
    print()
    print("   See detailed guide:")
    print("   01_Projectplan/260128_Project_Variables_System/Icon_Setup_Guide.md")
    print()

    # Offer to run conversion if possible
    if has_imagemagick or has_pillow:
        print("─" * 70)
        response = input("\n🚀 Run automatic conversion now? (y/N): ").strip().lower()

        if response in ['y', 'yes']:
            if has_imagemagick:
                print("\n⚙️  Running ImageMagick conversion...")
                result = subprocess.run(
                    ["bash", "scripts/convert_icons_to_white.sh"],
                    capture_output=False
                )
                sys.exit(result.returncode)
            elif has_pillow:
                print("\n⚙️  Running Python/Pillow conversion...")
                result = subprocess.run(
                    ["python3", "scripts/convert_icons_to_white.py"],
                    capture_output=False
                )
                sys.exit(result.returncode)
        else:
            print("\n👍 Okay! Run conversion manually when ready.")
    else:
        print("⚠️  No automatic conversion tools available.")
        print("   Please install ImageMagick or Pillow, or convert manually.")

    print()


if __name__ == "__main__":
    main()
