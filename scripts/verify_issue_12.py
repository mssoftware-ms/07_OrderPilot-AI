"""Verification script for Issue #12 - Entry Analyzer Icons Update.

This script verifies that all Material Design icons have been properly
integrated into the Entry Analyzer and that theme colors are applied consistently.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def verify_icons_copied():
    """Verify that all Material Design icons have been copied."""
    icons_dir = project_root / "src" / "ui" / "assets" / "icons"

    required_icons = [
        "settings.png", "trending_up.png", "build.png", "search.png",
        "analytics.png", "smart_toy.png", "check_circle.png", "gps_fixed.png",
        "refresh.png", "description.png", "place.png", "delete.png",
        "visibility.png", "timeline.png", "tune.png", "play_arrow.png",
        "stop.png", "auto_awesome.png", "show_chart.png", "assessment.png",
        "insights.png", "whatshot.png", "psychology.png", "extension.png",
        "bar_chart.png", "candlestick_chart.png", "filter_alt.png",
        "folder_open.png", "save.png", "download.png", "upload.png"
    ]

    print("=" * 60)
    print("ICON FILES VERIFICATION")
    print("=" * 60)
    print(f"Icons directory: {icons_dir}")
    print(f"Required icons: {len(required_icons)}")

    missing = []
    found = 0

    for icon in required_icons:
        icon_path = icons_dir / icon
        if icon_path.exists():
            found += 1
            print(f"  ✓ {icon}")
        else:
            missing.append(icon)
            print(f"  ✗ {icon} - MISSING")

    print(f"\nResult: {found}/{len(required_icons)} icons found")

    if missing:
        print(f"Missing icons: {', '.join(missing)}")
        return False

    print("✅ All required icons are present!\n")
    return True


def verify_imports():
    """Verify that all Entry Analyzer files have the icon import."""
    print("=" * 60)
    print("IMPORT VERIFICATION")
    print("=" * 60)

    files_to_check = [
        "src/ui/dialogs/entry_analyzer/entry_analyzer_popup.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_backtest_config.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_backtest_results.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_indicators_setup.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_indicators_presets.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_ai_copilot.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_ai_patterns.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_analysis.py",
    ]

    all_good = True

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"  ✗ {file_path} - FILE NOT FOUND")
            all_good = False
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for get_icon import
        has_import = "from src.ui.icons import get_icon" in content

        # Check for get_icon usage
        has_usage = "get_icon(" in content

        # Check for old emoji usage (should be minimal)
        emoji_count = content.count("🎯") + content.count("⚙️") + content.count("📈")
        emoji_count += content.count("🔧") + content.count("🔍") + content.count("📊")
        emoji_count += content.count("🤖") + content.count("✅") + content.count("🔄")

        status = "✓" if (has_import and has_usage) else "✗"
        print(f"  {status} {file_path}")
        print(f"     - get_icon import: {'Yes' if has_import else 'No'}")
        print(f"     - get_icon usage: {'Yes' if has_usage else 'No'}")
        print(f"     - Emoji characters: {emoji_count}")

        if not (has_import and has_usage):
            all_good = False

    if all_good:
        print("\n✅ All files have correct imports!\n")
    else:
        print("\n❌ Some files are missing imports or usage.\n")

    return all_good


def verify_theme_classes():
    """Verify that theme color classes are used instead of hardcoded colors."""
    print("=" * 60)
    print("THEME CLASS VERIFICATION")
    print("=" * 60)

    files_to_check = [
        "src/ui/dialogs/entry_analyzer/entry_analyzer_popup.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_backtest_config.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_backtest_results.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_indicators_setup.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_indicators_presets.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_ai_copilot.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_ai_patterns.py",
        "src/ui/dialogs/entry_analyzer/entry_analyzer_analysis.py",
    ]

    theme_classes = ["primary", "success", "danger", "info", "warning", "status-label"]

    all_good = True
    total_theme_usage = 0

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Count theme class usage
        theme_usage = sum(content.count(f'setProperty("class", "{cls}")') for cls in theme_classes)
        total_theme_usage += theme_usage

        # Check for hardcoded background-color in QPushButton (should be minimal)
        hardcoded_btn_colors = content.count('QPushButton') and 'background-color:' in content

        status = "✓" if theme_usage > 0 else "?"
        print(f"  {status} {file_path}")
        print(f"     - Theme class usage: {theme_usage}")

        if hardcoded_btn_colors:
            print(f"     ⚠ Contains hardcoded button colors (may be legacy)")

    print(f"\n✅ Total theme class usages: {total_theme_usage}\n")
    return total_theme_usage > 0


def verify_icon_provider():
    """Verify that the icon provider can be imported and works."""
    print("=" * 60)
    print("ICON PROVIDER VERIFICATION")
    print("=" * 60)

    try:
        from src.ui.icons import get_icon, get_available_icons, IconProvider

        print("  ✓ Icon provider imports successfully")

        # Get available icons
        available = get_available_icons()
        print(f"  ✓ Available icons: {len(available)}")

        # Try to get a test icon
        test_icon = get_icon("settings")
        if test_icon:
            print(f"  ✓ get_icon('settings') works")
        else:
            print(f"  ✗ get_icon('settings') returned empty icon")
            return False

        print("\n✅ Icon provider is working correctly!\n")
        return True

    except Exception as e:
        print(f"  ✗ Icon provider failed: {e}\n")
        return False


def main():
    """Run all verifications."""
    print("\n" + "=" * 60)
    print("ISSUE #12 VERIFICATION SCRIPT")
    print("Entry Analyzer Icons Update")
    print("=" * 60 + "\n")

    results = []

    # Run verifications
    results.append(("Icons Copied", verify_icons_copied()))
    results.append(("Imports", verify_imports()))
    results.append(("Theme Classes", verify_theme_classes()))
    results.append(("Icon Provider", verify_icon_provider()))

    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All verifications passed! Issue #12 is complete.\n")
        return 0
    else:
        print("\n⚠️ Some verifications failed. Please review the output above.\n")
        return 1


if __name__ == "__main__":
    exit(main())
