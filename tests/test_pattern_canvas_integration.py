"""Test Pattern Builder Canvas Integration into CEL Editor Main Window.

Phase 2.4: Verify canvas is integrated and all actions work correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui.windows.cel_editor import CelEditorWindow


def test_canvas_integration():
    """Test Pattern Builder Canvas integration."""
    print("\n" + "=" * 70)
    print("CEL Editor - Pattern Canvas Integration Test")
    print("Phase 2.4: Canvas Integration Verification")
    print("=" * 70)

    app = QApplication(sys.argv)

    # Create window
    print("\n✅ Creating CEL Editor window...")
    window = CelEditorWindow(strategy_name="Canvas Integration Test")

    # Verify canvas exists
    print("   Window title:", window.windowTitle())
    print("   Canvas exists:", hasattr(window, 'pattern_canvas'))

    if hasattr(window, 'pattern_canvas'):
        canvas = window.pattern_canvas
        print(f"   Canvas type: {type(canvas).__name__}")
        print(f"   Canvas scene: {canvas.scene}")
        print(f"   Canvas undo stack: {canvas.undo_stack}")

        # Test: Add candles
        print("\n✅ Testing candle operations...")
        print("   Adding bullish candle at (0, 0)...")
        candle1 = canvas.add_candle("bullish", x=0, y=0)
        print(f"   Candle 1 position: ({candle1.pos().x()}, {candle1.pos().y()})")
        print(f"   Total candles: {len(canvas.candles)}")

        print("   Adding bearish candle at (100, 50)...")
        candle2 = canvas.add_candle("bearish", x=100, y=50)
        print(f"   Candle 2 position: ({candle2.pos().x()}, {candle2.pos().y()})")
        print(f"   Total candles: {len(canvas.candles)}")

        # Test: Add relation
        print("\n✅ Testing relation operations...")
        print("   Adding 'greater' relation between candles...")
        relation = canvas.add_relation(candle1, candle2, "greater")
        print(f"   Relation type: {relation.relation_type}")
        print(f"   Total relations: {len(canvas.relations)}")

        # Test: Get statistics
        print("\n✅ Testing statistics...")
        stats = canvas.get_statistics()
        print(f"   Total candles: {stats['total_candles']}")
        print(f"   Candle types: {stats['candle_types']}")
        print(f"   Total relations: {stats['total_relations']}")
        print(f"   Relation types: {stats['relation_types']}")

        # Test: Undo/Redo
        print("\n✅ Testing undo/redo...")
        print(f"   Can undo: {canvas.can_undo()}")
        print(f"   Can redo: {canvas.can_redo()}")
        print(f"   Undo stack count: {canvas.undo_stack.count()}")

        if canvas.can_undo():
            print("   Performing undo...")
            canvas.undo()
            print(f"   Total candles after undo: {len(canvas.candles)}")
            print(f"   Can undo: {canvas.can_undo()}")
            print(f"   Can redo: {canvas.can_redo()}")

        # Test: Pattern serialization
        print("\n✅ Testing pattern serialization...")
        pattern_data = canvas.get_pattern_data()
        print(f"   Serialized candles: {len(pattern_data['candles'])}")
        print(f"   Serialized relations: {len(pattern_data['relations'])}")
        print(f"   Metadata: {pattern_data['metadata']}")

        # Test: Zoom
        print("\n✅ Testing zoom operations...")
        print("   Zoom in...")
        canvas.zoom_in()
        print("   Zoom out...")
        canvas.zoom_out()
        print("   Zoom to fit...")
        canvas.zoom_fit()

    # Verify action connections
    print("\n✅ Verifying action connections...")
    print(f"   Undo action enabled: {window.action_undo.isEnabled()}")
    print(f"   Redo action enabled: {window.action_redo.isEnabled()}")
    print(f"   Clear action exists: {window.action_clear is not None}")
    print(f"   Zoom in action exists: {window.action_zoom_in is not None}")
    print(f"   Zoom out action exists: {window.action_zoom_out is not None}")
    print(f"   Zoom fit action exists: {window.action_zoom_fit is not None}")

    # Show window
    print("\n✅ Showing window...")
    window.show()

    print("\n" + "=" * 70)
    print("Manual Testing Instructions:")
    print("=" * 70)
    print("1. Verify canvas is visible in center (no placeholder)")
    print("2. Verify grid is drawn (major 50px, minor 10px)")
    print("3. Verify 2 candles are displayed:")
    print("   - Bullish (green) candle at center")
    print("   - Bearish (red) candle at (100, 50)")
    print("4. Verify green relation line between candles with '>' symbol")
    print("5. Test toolbar actions:")
    print("   - Undo button should be enabled (click to undo last candle)")
    print("   - Redo button should become enabled after undo")
    print("   - Zoom In/Out/Fit buttons should work")
    print("6. Test menu actions:")
    print("   - Edit → Undo/Redo should work")
    print("   - Edit → Clear All should show confirmation dialog")
    print("   - View → Zoom In/Out/Fit should work")
    print("7. Test canvas interactions:")
    print("   - Click candle to select (teal border)")
    print("   - Drag candle (should snap to 50px grid)")
    print("   - Mouse wheel to zoom (centered on cursor)")
    print("8. Check status bar:")
    print("   - Should show '✅ 2 candles, 1 relations' (or after undo: '✅ 1 candles, 0 relations')")
    print("   - Should update on candle selection")
    print("\nClose the window when done testing.")
    print("=" * 70 + "\n")

    # Auto-close after 60 seconds for CI/CD
    def auto_close():
        print("\n⏱️ Auto-closing after 60 seconds...")
        window.close()

    QTimer.singleShot(60000, auto_close)

    return app.exec()


if __name__ == "__main__":
    sys.exit(test_canvas_integration())
