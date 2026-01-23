#!/usr/bin/env python
"""
Quick verification script for splash screen setup.
Checks all requirements without launching the full application.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

def verify_image_exists():
    """Check if image2.png exists"""
    image_path = project_root / ".AI_Exchange" / "image2.png"
    if image_path.exists():
        print(f"✓ Image found: {image_path}")
        print(f"  Size: {image_path.stat().st_size / 1024:.1f} KB")
        return True
    else:
        print(f"✗ Image NOT found: {image_path}")
        return False

def verify_dependencies():
    """Check required dependencies"""
    deps = {
        "PyQt6": {"required": True, "installed": False},
        "Pillow": {"required": False, "installed": False}  # Optional, for tests only
    }

    for dep, info in deps.items():
        try:
            __import__(dep)
            info["installed"] = True
            if info["required"]:
                print(f"✓ {dep} installed")
            else:
                print(f"✓ {dep} installed (optional)")
        except ImportError:
            if info["required"]:
                print(f"✗ {dep} NOT installed - REQUIRED")
            else:
                print(f"⚠ {dep} NOT installed - optional (only needed for tests)")

    # Only check required dependencies
    return all(info["installed"] for info in deps.values() if info["required"])

def verify_app_resources():
    """Check app_resources.py returns correct path"""
    try:
        from ui.app_resources import _get_startup_icon_path

        path = _get_startup_icon_path()
        if path.exists() and path.name == "image2.png":
            print(f"✓ _get_startup_icon_path() works correctly")
            print(f"  Returns: {path}")
            return True
        else:
            print(f"✗ _get_startup_icon_path() issue:")
            print(f"  Returns: {path}")
            print(f"  Exists: {path.exists()}")
            return False
    except Exception as e:
        print(f"✗ Error checking app_resources: {e}")
        return False

def verify_splash_screen_class():
    """Check SplashScreen class can be imported"""
    try:
        from ui.splash_screen import SplashScreen
        print("✓ SplashScreen class can be imported")
        return True
    except Exception as e:
        print(f"✗ Cannot import SplashScreen: {e}")
        return False

def main():
    print("=" * 70)
    print("Splash Screen Setup Verification")
    print("=" * 70)
    print()

    checks = [
        ("Image file", verify_image_exists),
        ("Dependencies", verify_dependencies),
        ("app_resources.py", verify_app_resources),
        ("SplashScreen class", verify_splash_screen_class),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        result = check_func()
        results.append(result)
        print()

    print("=" * 70)
    if all(results):
        print("✓ ALL CHECKS PASSED - Splash screen ready to use!")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME CHECKS FAILED - Review errors above")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
