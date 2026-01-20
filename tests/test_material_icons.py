"""Test Material Design Icons loading for CEL Editor.

Phase 0.3.3: Verify icon loader and availability.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSize
from ui.windows.cel_editor.icons import (
    MaterialIconLoader,
    CelEditorIcons,
    MATERIAL_ICONS_BASE
)


def test_icon_base_path():
    """Test 1: Verify Material Icons base path exists."""
    print("\n🧪 Test 1: Material Icons Base Path")
    print("=" * 60)

    print(f"Base Path: {MATERIAL_ICONS_BASE}")

    if MATERIAL_ICONS_BASE.exists():
        print(f"✅ Base path exists")

        # List some categories
        categories = list(MATERIAL_ICONS_BASE.iterdir())[:5]
        print(f"   Sample categories: {[c.name for c in categories]}")
        return True
    else:
        print(f"❌ Base path does not exist")
        return False


def test_icon_loader_list_categories():
    """Test 2: List icon categories."""
    print("\n🧪 Test 2: List Icon Categories")
    print("=" * 60)

    loader = MaterialIconLoader()
    categories = loader.list_categories()

    if categories:
        print(f"✅ Found {len(categories)} categories")
        print(f"   First 10: {categories[:10]}")
        return True
    else:
        print(f"❌ No categories found")
        return False


def test_icon_loader_list_icons():
    """Test 3: List icons in 'action' category."""
    print("\n🧪 Test 3: List Icons in 'action' Category")
    print("=" * 60)

    loader = MaterialIconLoader()
    icons = loader.list_available_icons('action')

    if icons:
        print(f"✅ Found {len(icons)} icons in 'action' category")
        print(f"   Sample icons: {icons[:10]}")
        return True
    else:
        print(f"❌ No icons found in 'action' category")
        return False


def test_icon_loader_load_icon():
    """Test 4: Load specific icon."""
    print("\n🧪 Test 4: Load Specific Icon (action/settings)")
    print("=" * 60)

    loader = MaterialIconLoader()

    # Test loading settings icon
    icon = loader.get_icon('action', 'settings')

    if not icon.isNull():
        print(f"✅ Icon loaded successfully")

        # Get pixmap to verify
        pixmap = icon.pixmap(QSize(24, 24))
        print(f"   Size: {pixmap.width()}x{pixmap.height()}")
        print(f"   Is null: {pixmap.isNull()}")
        return True
    else:
        print(f"❌ Icon is null (failed to load)")
        return False


def test_cel_editor_icons():
    """Test 5: CelEditorIcons pre-defined icons."""
    print("\n🧪 Test 5: CEL Editor Pre-defined Icons")
    print("=" * 60)

    icons = CelEditorIcons()

    # Test various pre-defined icons
    icon_tests = [
        ('new_file', icons.new_file),
        ('save', icons.save),
        ('undo', icons.undo),
        ('view_pattern', icons.view_pattern),
        ('view_code', icons.view_code),
        ('add_candle', icons.add_candle),
        ('ai_generate', icons.ai_generate),
        ('settings', icons.settings),
    ]

    passed = 0
    for name, icon in icon_tests:
        if not icon.isNull():
            print(f"   ✅ {name}")
            passed += 1
        else:
            print(f"   ❌ {name} (null)")

    print(f"\nResult: {passed}/{len(icon_tests)} icons loaded")

    return passed == len(icon_tests)


def test_icon_variants():
    """Test 6: Load icon with different variants."""
    print("\n🧪 Test 6: Icon Variants and Sizes")
    print("=" * 60)

    loader = MaterialIconLoader()

    # Test different variants of 'add' icon
    variants = ['baseline', 'outline', 'round', 'sharp']
    sizes = ['18dp', '24dp', '36dp', '48dp']

    passed = 0
    total = len(variants)

    for variant in variants:
        icon = loader.get_icon('content', 'add', variant=variant)
        if not icon.isNull():
            print(f"   ✅ Variant '{variant}' loaded")
            passed += 1
        else:
            print(f"   ❌ Variant '{variant}' failed")

    print(f"\nVariants: {passed}/{total} loaded")

    # Test different sizes
    passed_sizes = 0
    for size in sizes:
        icon = loader.get_icon('content', 'add', size=size)
        if not icon.isNull():
            print(f"   ✅ Size '{size}' loaded")
            passed_sizes += 1
        else:
            print(f"   ⚠️  Size '{size}' not available")

    print(f"Sizes: {passed_sizes}/{len(sizes)} loaded")

    return passed >= 2  # At least 2 variants should work


def test_icon_caching():
    """Test 7: Icon caching performance."""
    print("\n🧪 Test 7: Icon Caching")
    print("=" * 60)

    import time

    loader = MaterialIconLoader()

    # First load (no cache)
    start = time.time()
    icon1 = loader.get_icon('action', 'settings')
    time1 = time.time() - start

    # Second load (cached)
    start = time.time()
    icon2 = loader.get_icon('action', 'settings')
    time2 = time.time() - start

    print(f"   First load: {time1*1000:.2f}ms")
    print(f"   Second load (cached): {time2*1000:.2f}ms")

    if time2 < time1 / 10:  # Should be at least 10x faster
        print(f"   ✅ Caching working (speedup: {time1/time2:.1f}x)")
        return True
    else:
        print(f"   ⚠️  Caching might not be working properly")
        return False


def main():
    """Run all Material Icons tests."""
    print("\n" + "=" * 60)
    print("Material Design Icons Test Suite")
    print("Phase 0.3.3: Icon Loader Verification")
    print("=" * 60)

    # Create QApplication for QIcon/QPixmap tests
    app = QApplication(sys.argv)

    results = []

    # Run all tests
    results.append(test_icon_base_path())
    results.append(test_icon_loader_list_categories())
    results.append(test_icon_loader_list_icons())
    results.append(test_icon_loader_load_icon())
    results.append(test_cel_editor_icons())
    results.append(test_icon_variants())
    results.append(test_icon_caching())

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed - Icon system ready for Phase 1")
    elif passed >= 4:
        print("⚠️  Partial success - Core functionality working")
    else:
        print("❌ Critical failures - Check Material Icons path")

    print("\n💡 Icon Usage Example:")
    print("   from ui.windows.cel_editor.icons import cel_icons")
    print("   button.setIcon(cel_icons.save)")
    print("   action.setIcon(cel_icons.ai_generate)")
    print("=" * 60 + "\n")

    return 0 if passed >= 4 else 1


if __name__ == "__main__":
    sys.exit(main())
