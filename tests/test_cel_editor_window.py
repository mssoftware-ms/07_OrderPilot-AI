"""Test CEL Editor Main Window.

Phase 1.1: Verify main window skeleton works correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
from ui.windows.cel_editor import CelEditorWindow


def test_main_window():
    """Test CEL Editor main window instantiation and display."""
    print("\n" + "=" * 60)
    print("CEL Editor Main Window Test")
    print("Phase 1.1: Window Skeleton Verification")
    print("=" * 60)

    app = QApplication(sys.argv)

    # Create window
    print("\n✅ Creating CEL Editor window...")
    window = CelEditorWindow(strategy_name="Test Strategy")

    # Verify window properties
    print(f"   Window title: {window.windowTitle()}")
    print(f"   Minimum size: {window.minimumWidth()}x{window.minimumHeight()}")
    print(f"   Size: {window.width()}x{window.height()}")

    # Verify dock widgets
    print(f"\n✅ Dock widgets:")
    print(f"   Left dock: {window.left_dock.windowTitle()}")
    print(f"   Right dock: {window.right_dock.windowTitle()}")

    # Verify toolbar
    print(f"\n✅ Toolbar:")
    toolbars = window.findChildren(type(window).ToolBar)
    if toolbars:
        print(f"   Found {len(toolbars)} toolbar(s)")

    # Verify menu bar
    print(f"\n✅ Menu bar:")
    menubar = window.menuBar()
    actions = menubar.actions()
    menus = [action.text() for action in actions if action.menu()]
    print(f"   Menus: {menus}")

    # Verify status bar
    print(f"\n✅ Status bar:")
    statusbar = window.statusBar()
    print(f"   Status message: {statusbar.currentMessage()}")

    # Show window
    print(f"\n✅ Showing window...")
    window.show()

    print("\n" + "=" * 60)
    print("Manual Testing Instructions:")
    print("=" * 60)
    print("1. Verify window title: 'CEL Editor - Test Strategy'")
    print("2. Check menu bar: File, Edit, View, Help")
    print("3. Check toolbar: Icons for New, Open, Save, Undo, Redo, Zoom")
    print("4. Check left dock: 'Pattern Library & Templates'")
    print("5. Check right dock: 'Properties & AI Assistant'")
    print("6. Check central placeholder: 'Pattern Builder Canvas (Phase 2)'")
    print("7. Check status bar: '✅ Ready' and 'Strategy: Test Strategy'")
    print("8. Test view mode switching:")
    print("   - View menu → Pattern Builder, Code Editor, Chart View, Split View")
    print("   - View combo box dropdown")
    print("9. Test menu actions (should show 'not yet implemented' messages)")
    print("10. Check dark theme applied correctly")
    print("\nClose the window when done testing.")
    print("=" * 60 + "\n")

    return app.exec()


if __name__ == "__main__":
    sys.exit(test_main_window())
