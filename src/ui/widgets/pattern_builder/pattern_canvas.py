"""Pattern Builder Canvas - Main canvas for visual pattern creation.

QGraphicsView-based canvas with grid, draggable candles, and relation lines.
Supports undo/redo, zoom, and pattern serialization.
"""

from typing import Optional, List
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QColor, QPainter, QWheelEvent, QUndoStack, QUndoCommand, QMouseEvent, QCursor

from src.ui.windows.cel_editor.theme import (
    BACKGROUND_PRIMARY, GRID_MAJOR, GRID_MINOR
)
from .candle_item import CandleItem
from .relation_line import RelationLine


class AddCandleCommand(QUndoCommand):
    """Undo command for adding a candle."""

    def __init__(self, canvas: 'PatternBuilderCanvas', candle: CandleItem):
        super().__init__("Add Candle")
        self.canvas = canvas
        self.candle = candle

    def redo(self):
        """Add candle to canvas."""
        self.canvas.scene.addItem(self.candle)
        self.canvas.candles.append(self.candle)
        self.canvas.pattern_changed.emit()

    def undo(self):
        """Remove candle from canvas."""
        self.canvas.scene.removeItem(self.candle)
        self.canvas.candles.remove(self.candle)
        self.canvas.pattern_changed.emit()


class RemoveCandleCommand(QUndoCommand):
    """Undo command for removing a candle."""

    def __init__(self, canvas: 'PatternBuilderCanvas', candle: CandleItem):
        super().__init__("Remove Candle")
        self.canvas = canvas
        self.candle = candle

    def redo(self):
        """Remove candle from canvas."""
        self.canvas.scene.removeItem(self.candle)
        if self.candle in self.canvas.candles:
            self.canvas.candles.remove(self.candle)
        self.canvas.pattern_changed.emit()

    def undo(self):
        """Add candle back to canvas."""
        self.canvas.scene.addItem(self.candle)
        self.canvas.candles.append(self.candle)
        self.canvas.pattern_changed.emit()


class PatternBuilderCanvas(QGraphicsView):
    """Main canvas for visual pattern building.

    Features:
    - Grid background (major 50px, minor 10px)
    - Draggable candles with snap-to-grid
    - Visual relation lines between candles
    - Zoom with mouse wheel (saves view history)
    - Pan with middle mouse button + drag
    - "Alles zoomen" button (fit all candles)
    - "Zurück" button (restore previous view)
    - Undo/Redo support
    - Pattern serialization to/from dict

    Viewer Controls (analog zu Chart-Modul):
    - Mouse Wheel: Zoom in/out (around mouse cursor)
    - Middle Mouse + Drag: Pan view
    - Toolbar "Alles zoomen": Fit all candles in view
    - Toolbar "Zurück": Go back to previous view

    Signals:
    - pattern_changed: Emitted when pattern is modified
    - candle_selected: Emitted when candle is selected (with candle data)
    - selection_cleared: Emitted when selection is cleared
    """

    # Signals
    pattern_changed = pyqtSignal()
    candle_selected = pyqtSignal(dict)  # Candle data
    selection_cleared = pyqtSignal()

    # Grid configuration
    GRID_SIZE_MAJOR = 50
    GRID_SIZE_MINOR = 10

    # Canvas size
    CANVAS_WIDTH = 2000
    CANVAS_HEIGHT = 1500

    def __init__(self, parent=None):
        """Initialize pattern builder canvas."""
        super().__init__(parent)

        # Scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Candles and relations
        self.candles: List[CandleItem] = []
        self.relations: List[RelationLine] = []

        # Undo/Redo stack
        self.undo_stack = QUndoStack(self)

        # Pan state
        self.is_panning = False
        self.last_pan_position = None

        # View history for zoom back (analog zu Chart: zoom_back_to_previous_view)
        self._view_history: list[tuple[float, float, float]] = []  # (scale_x, scale_y, center_x, center_y)
        self._max_history = 10  # Keep last 10 views

        # Setup canvas
        self._setup_canvas()
        self._draw_grid()

    def _setup_canvas(self):
        """Configure canvas properties."""
        # Set scene size
        self.scene.setSceneRect(-1000, -750, self.CANVAS_WIDTH, self.CANVAS_HEIGHT)

        # View configuration
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Background
        self.setBackgroundBrush(QColor(BACKGROUND_PRIMARY))

        # Connect scene selection changes
        self.scene.selectionChanged.connect(self._on_selection_changed)

    def _draw_grid(self):
        """Draw grid lines on canvas."""
        scene_rect = self.scene.sceneRect()

        # Minor grid lines (10px)
        minor_pen = QPen(QColor(GRID_MINOR), 1)
        for x in range(int(scene_rect.left()), int(scene_rect.right()), self.GRID_SIZE_MINOR):
            if x % self.GRID_SIZE_MAJOR != 0:  # Skip major grid positions
                self.scene.addLine(
                    x, scene_rect.top(),
                    x, scene_rect.bottom(),
                    minor_pen
                )

        for y in range(int(scene_rect.top()), int(scene_rect.bottom()), self.GRID_SIZE_MINOR):
            if y % self.GRID_SIZE_MAJOR != 0:
                self.scene.addLine(
                    scene_rect.left(), y,
                    scene_rect.right(), y,
                    minor_pen
                )

        # Major grid lines (50px)
        major_pen = QPen(QColor(GRID_MAJOR), 1)
        for x in range(int(scene_rect.left()), int(scene_rect.right()), self.GRID_SIZE_MAJOR):
            self.scene.addLine(
                x, scene_rect.top(),
                x, scene_rect.bottom(),
                major_pen
            )

        for y in range(int(scene_rect.top()), int(scene_rect.bottom()), self.GRID_SIZE_MAJOR):
            self.scene.addLine(
                scene_rect.left(), y,
                scene_rect.right(), y,
                major_pen
            )

    def add_candle(
        self,
        candle_type: str = "bullish",
        x: Optional[float] = None,
        y: Optional[float] = None,
        index: Optional[int] = None,
        use_undo: bool = True
    ) -> CandleItem:
        """Add a new candle to the canvas.

        Args:
            candle_type: Type of candle (bullish, bearish, doji, etc.)
            x: X position (or None for auto)
            y: Y position (or None for auto)
            index: Candle index (or None for auto)
            use_undo: Whether to add to undo stack

        Returns:
            Created CandleItem
        """
        # Auto-position if not specified
        if x is None:
            x = len(self.candles) * 100  # Space out candles
        if y is None:
            y = 0

        # Auto-index if not specified
        if index is None:
            index = -len(self.candles)  # 0, -1, -2, etc.

        # Create candle
        candle = CandleItem(x=x, y=y, candle_type=candle_type, index=index)

        # Add to scene
        if use_undo:
            command = AddCandleCommand(self, candle)
            self.undo_stack.push(command)
        else:
            self.scene.addItem(candle)
            self.candles.append(candle)
            self.pattern_changed.emit()

        return candle

    def remove_candle(self, candle: CandleItem, use_undo: bool = True):
        """Remove a candle from the canvas.

        Args:
            candle: Candle to remove
            use_undo: Whether to add to undo stack
        """
        if use_undo:
            command = RemoveCandleCommand(self, candle)
            self.undo_stack.push(command)
        else:
            self.scene.removeItem(candle)
            if candle in self.candles:
                self.candles.remove(candle)
            self.pattern_changed.emit()

    def get_selected_candles(self) -> list:
        """Get all currently selected candles.

        Returns:
            List of selected CandleItem objects
        """
        return [item for item in self.scene.selectedItems() if isinstance(item, CandleItem)]

    def remove_selected_candles(self):
        """Remove all selected candles."""
        selected = self.get_selected_candles()

        for candle in selected:
            self.remove_candle(candle, use_undo=True)

    def clear_pattern(self):
        """Clear all candles and relations from canvas."""
        # Clear candles
        for candle in list(self.candles):
            self.remove_candle(candle, use_undo=False)

        # Clear relations
        for relation in list(self.relations):
            self.remove_relation(relation)

        # Clear undo stack
        self.undo_stack.clear()

        self.pattern_changed.emit()

    def add_relation(
        self,
        start_candle: CandleItem,
        end_candle: CandleItem,
        relation_type: str = "greater"
    ) -> RelationLine:
        """Add a relation line between two candles.

        Args:
            start_candle: Source candle
            end_candle: Target candle
            relation_type: Type of relation (greater, less, equal, near)

        Returns:
            Created RelationLine
        """
        # Create relation
        relation = RelationLine(start_candle, end_candle, relation_type)

        # Add to scene
        self.scene.addItem(relation)

        # Add label to scene
        if relation.label:
            self.scene.addItem(relation.label)

        # Track relation
        self.relations.append(relation)

        self.pattern_changed.emit()

        return relation

    def remove_relation(self, relation: RelationLine):
        """Remove a relation line.

        Args:
            relation: Relation to remove
        """
        # Remove label
        relation.remove_label()

        # Remove from scene
        self.scene.removeItem(relation)

        # Remove from list
        if relation in self.relations:
            self.relations.remove(relation)

        self.pattern_changed.emit()

    def update_relation_positions(self):
        """Update all relation line positions (called when candles move)."""
        for relation in self.relations:
            relation.update_position()

    def _on_selection_changed(self):
        """Handle scene selection changes."""
        selected = self.scene.selectedItems()

        # Find selected candle
        selected_candles = [item for item in selected if isinstance(item, CandleItem)]

        if selected_candles:
            # Emit first selected candle data
            candle = selected_candles[0]
            self.candle_selected.emit(candle.get_data())
        else:
            # No candle selected
            self.selection_cleared.emit()

    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming.

        Args:
            event: Wheel event
        """
        # Save view state before zoom (so user can zoom back)
        self._save_view_state()

        # Zoom factor
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        # Get current scale
        old_pos = self.mapToScene(event.position().toPoint())

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

        # Get new position
        new_pos = self.mapToScene(event.position().toPoint())

        # Move scene to old position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def _save_view_state(self):
        """Save current view state to history (analog zu Chart: rememberViewState)."""
        # Get current transform
        transform = self.transform()
        scale_x = transform.m11()
        scale_y = transform.m22()

        # Get current center point
        center = self.mapToScene(self.viewport().rect().center())

        # Save to history
        view_state = (scale_x, scale_y, center.x(), center.y())
        self._view_history.append(view_state)

        # Keep only last N views
        if len(self._view_history) > self._max_history:
            self._view_history.pop(0)

    def zoom_to_fit_all(self):
        """Zoom to fit all candles in view (analog zu Chart: zoom_to_fit_all)."""
        if not self.candles:
            return

        # Save current view before changing
        self._save_view_state()

        # Get bounding rect of all candles
        bounding_rect = QRectF()
        for candle in self.candles:
            bounding_rect = bounding_rect.united(candle.sceneBoundingRect())

        # Add margin
        margin = 100
        bounding_rect.adjust(-margin, -margin, margin, margin)

        # Fit in view
        self.fitInView(bounding_rect, Qt.AspectRatioMode.KeepAspectRatio)

    def zoom_back_to_previous_view(self) -> bool:
        """Restore previous view state (analog zu Chart: zoom_back_to_previous_view).

        Returns:
            True if a previous state was restored, False otherwise.
        """
        if not self._view_history:
            return False

        # Pop last view state
        scale_x, scale_y, center_x, center_y = self._view_history.pop()

        # Reset transform
        self.resetTransform()

        # Apply saved scale
        self.scale(scale_x, scale_y)

        # Center on saved position
        self.centerOn(center_x, center_y)

        return True

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for pan start.

        Args:
            event: Mouse event
        """
        # Start panning with middle mouse button
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.last_pan_position = event.position().toPoint()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            event.accept()
        else:
            # Pass to parent for normal drag/select behavior
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for panning.

        Args:
            event: Mouse event
        """
        if self.is_panning and self.last_pan_position:
            # Calculate delta
            delta = event.position().toPoint() - self.last_pan_position
            self.last_pan_position = event.position().toPoint()

            # Pan the view by adjusting scrollbars
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            event.accept()
        else:
            # Pass to parent for normal drag behavior
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release for pan end.

        Args:
            event: Mouse event
        """
        # End panning
        if event.button() == Qt.MouseButton.MiddleButton and self.is_panning:
            self.is_panning = False
            self.last_pan_position = None
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
            event.accept()
        else:
            # Pass to parent for normal behavior
            super().mouseReleaseEvent(event)

    def undo(self):
        """Undo last action."""
        self.undo_stack.undo()

    def redo(self):
        """Redo last undone action."""
        self.undo_stack.redo()

    def can_undo(self) -> bool:
        """Check if undo is available.

        Returns:
            True if can undo
        """
        return self.undo_stack.canUndo()

    def can_redo(self) -> bool:
        """Check if redo is available.

        Returns:
            True if can redo
        """
        return self.undo_stack.canRedo()

    def get_pattern_data(self) -> dict:
        """Get complete pattern data for serialization.

        Returns:
            Dict with pattern data (candles, relations, metadata)
        """
        return {
            "candles": [candle.get_data() for candle in self.candles],
            "relations": [relation.get_data() for relation in self.relations],
            "metadata": {
                "version": "1.0.0",
                "candle_count": len(self.candles),
                "relation_count": len(self.relations)
            }
        }

    def load_pattern_data(self, data: dict):
        """Load pattern from serialized data.

        Args:
            data: Pattern data from get_pattern_data()
        """
        # Clear existing pattern
        self.clear_pattern()

        # Load candles
        candle_map = {}  # Map index to candle for relations
        for candle_data in data.get("candles", []):
            candle = CandleItem.from_data(candle_data)
            self.scene.addItem(candle)
            self.candles.append(candle)
            candle_map[candle.index] = candle

        # Load relations
        for relation_data in data.get("relations", []):
            if "start_candle_index" in relation_data and "end_candle_index" in relation_data:
                start_candle = candle_map.get(relation_data["start_candle_index"])
                end_candle = candle_map.get(relation_data["end_candle_index"])

                if start_candle and end_candle:
                    self.add_relation(
                        start_candle,
                        end_candle,
                        relation_data["relation_type"]
                    )

        self.pattern_changed.emit()

    def get_statistics(self) -> dict:
        """Get pattern statistics.

        Returns:
            Dict with pattern statistics
        """
        # Count candle types
        type_counts = {}
        for candle in self.candles:
            candle_type = candle.candle_type
            type_counts[candle_type] = type_counts.get(candle_type, 0) + 1

        # Count relation types
        relation_counts = {}
        for relation in self.relations:
            rel_type = relation.relation_type
            relation_counts[rel_type] = relation_counts.get(rel_type, 0) + 1

        return {
            "total_candles": len(self.candles),
            "candle_types": type_counts,
            "total_relations": len(self.relations),
            "relation_types": relation_counts
        }

    def update_candle_properties(self, candle: CandleItem, properties: dict):
        """Update candle properties from properties panel.

        Args:
            candle: Candle to update
            properties: Dict with keys: ohlc (dict), candle_type (str), index (int)
        """
        # Update OHLC (this also redraws the candle)
        if "ohlc" in properties:
            candle.update_ohlc(properties["ohlc"])

        # Update candle type (changes OHLC to defaults, so do this before OHLC if both are set)
        if "candle_type" in properties and properties["candle_type"] != candle.candle_type:
            # Only update OHLC if not explicitly provided
            if "ohlc" not in properties:
                candle.update_candle_type(properties["candle_type"])
            else:
                # Just change type without resetting OHLC
                candle.candle_type = properties["candle_type"]
                candle.update_ohlc(properties["ohlc"])

        # Update index
        if "index" in properties:
            candle.update_index(properties["index"])

        # Emit pattern changed
        self.pattern_changed.emit()
