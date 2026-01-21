# CEL Editor - Pattern Builder API Reference

**Version**: 1.0
**Date**: 2026-01-20
**Module**: `src.ui.widgets.pattern_builder`

---

## Table of Contents

1. [Overview](#overview)
2. [Module Structure](#module-structure)
3. [PatternBuilderCanvas](#patternbuildercanvas)
4. [CandleToolbar](#candletoolbar)
5. [PropertiesPanel](#propertiespanel)
6. [CandleGraphicsItem](#candlegraphicsitem)
7. [RelationLine](#relationline)
8. [Data Models](#data-models)
9. [Signals & Slots](#signals--slots)
10. [Example Usage](#example-usage)

---

## Overview

The **Pattern Builder API** provides programmatic access to the visual candlestick pattern designer. It consists of five main components:

| Component | Purpose | File |
|-----------|---------|------|
| `PatternBuilderCanvas` | Main canvas for pattern design | `pattern_canvas.py` |
| `CandleToolbar` | Candle type selection toolbar | `candle_toolbar.py` |
| `PropertiesPanel` | Candle properties editor | `properties_panel.py` |
| `CandleGraphicsItem` | Individual candle visual item | `candle_graphics_item.py` |
| `RelationLine` | Relation line between candles | `relation_line.py` |

### Architecture

```
CelEditorWindow
├── CandleToolbar (top)
├── PatternBuilderCanvas (center)
│   ├── QGraphicsScene
│   │   ├── CandleGraphicsItem (multiple)
│   │   └── RelationLine (multiple)
│   └── QUndoStack
└── PropertiesPanel (right)
```

### Signal Flow

```
Toolbar → Canvas:   candle type selection
Canvas → Properties: candle_selected, selection_cleared
Properties → Canvas: values_changed
Canvas → All:       pattern_changed
```

---

## Module Structure

### Import Paths

```python
from ui.widgets.pattern_builder.pattern_canvas import PatternBuilderCanvas
from ui.widgets.pattern_builder.candle_toolbar import CandleToolbar
from ui.widgets.pattern_builder.properties_panel import PropertiesPanel
from ui.widgets.pattern_builder.candle_graphics_item import CandleGraphicsItem
from ui.widgets.pattern_builder.relation_line import RelationLine
```

### Dependencies

```python
# Required PyQt6 modules
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QToolBar, QWidget, QUndoStack
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter
```

---

## PatternBuilderCanvas

**File**: `src/ui/widgets/pattern_builder/pattern_canvas.py`

**Class**: `PatternBuilderCanvas(QGraphicsView)`

Main canvas widget for visual pattern design. Manages candles, relations, undo/redo, and pattern serialization.

### Constructor

```python
def __init__(self, theme_manager: ThemeManager, parent=None):
    """Initialize Pattern Builder Canvas.

    Args:
        theme_manager: Theme manager for colors and styling
        parent: Parent widget (optional)
    """
```

**Example:**
```python
from ui.themes import ThemeManager
theme = ThemeManager()
canvas = PatternBuilderCanvas(theme)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `candles` | `List[CandleGraphicsItem]` | List of all candles on canvas |
| `relations` | `List[RelationLine]` | List of all relation lines |
| `scene` | `QGraphicsScene` | Underlying graphics scene |
| `undo_stack` | `QUndoStack` | Undo/redo command stack |
| `next_candle_index` | `int` | Auto-incrementing candle index |

### Signals

```python
class PatternBuilderCanvas(QGraphicsView):
    # Emitted when pattern structure changes
    pattern_changed = pyqtSignal()

    # Emitted when candle is selected (passes candle)
    candle_selected = pyqtSignal(object)

    # Emitted when selection is cleared
    selection_cleared = pyqtSignal()
```

### Methods

#### Candle Management

##### `add_candle()`

```python
def add_candle(
    self,
    candle_type: str = "bullish",
    x: float = None,
    y: float = None,
    ohlc: Dict[str, float] = None
) -> CandleGraphicsItem:
    """Add a candle to the canvas.

    Args:
        candle_type: "bullish", "bearish", or "doji"
        x: X position (auto-calculated if None)
        y: Y position (default: 0)
        ohlc: OHLC values dict (uses defaults if None)
            {
                "open": float,
                "high": float,
                "low": float,
                "close": float
            }

    Returns:
        CandleGraphicsItem: The created candle item

    Emits:
        pattern_changed signal

    Example:
        # Add default bullish candle
        candle = canvas.add_candle()

        # Add bearish candle at specific position
        candle = canvas.add_candle(
            candle_type="bearish",
            x=100, y=50
        )

        # Add candle with custom OHLC
        candle = canvas.add_candle(
            candle_type="doji",
            ohlc={
                "open": 50.0,
                "high": 90.0,
                "low": 30.0,
                "close": 50.0
            }
        )
    """
```

##### `remove_candle()`

```python
def remove_candle(self, candle: CandleGraphicsItem):
    """Remove a candle from the canvas.

    Args:
        candle: CandleGraphicsItem to remove

    Side Effects:
        - Removes all relations connected to this candle
        - Updates remaining candle indices
        - Pushes command to undo stack

    Emits:
        pattern_changed signal

    Example:
        candle = canvas.candles[0]
        canvas.remove_candle(candle)
    """
```

##### `get_selected_candles()`

```python
def get_selected_candles(self) -> List[CandleGraphicsItem]:
    """Get all selected candles.

    Returns:
        List of selected CandleGraphicsItem objects

    Example:
        selected = canvas.get_selected_candles()
        if len(selected) == 1:
            print(f"Selected candle: {selected[0].candle_type}")
        elif len(selected) > 1:
            print(f"{len(selected)} candles selected")
    """
```

##### `update_candle_properties()`

```python
def update_candle_properties(
    self,
    candle: CandleGraphicsItem,
    candle_type: str,
    ohlc: Dict[str, float]
):
    """Update candle properties from Properties Panel.

    Args:
        candle: CandleGraphicsItem to update
        candle_type: New candle type
        ohlc: New OHLC values dict

    Side Effects:
        - Updates candle visual appearance
        - Pushes command to undo stack

    Emits:
        pattern_changed signal

    Example:
        canvas.update_candle_properties(
            candle=canvas.candles[0],
            candle_type="bearish",
            ohlc={
                "open": 60.0,
                "high": 95.0,
                "low": 35.0,
                "close": 40.0
            }
        )
    """
```

#### Relation Management

##### `add_relation()`

```python
def add_relation(
    self,
    source: CandleGraphicsItem,
    target: CandleGraphicsItem,
    relation_type: str
) -> RelationLine:
    """Add a relation line between two candles.

    Args:
        source: Source candle (left side of relation)
        target: Target candle (right side of relation)
        relation_type: "greater", "less", or "equal"

    Returns:
        RelationLine: The created relation line

    Raises:
        ValueError: If source == target or relation already exists

    Emits:
        pattern_changed signal

    Example:
        candle1 = canvas.candles[0]
        candle2 = canvas.candles[1]

        # Add "greater than" relation
        relation = canvas.add_relation(
            source=candle1,
            target=candle2,
            relation_type="greater"
        )
    """
```

##### `remove_relation()`

```python
def remove_relation(self, relation: RelationLine):
    """Remove a relation line.

    Args:
        relation: RelationLine to remove

    Side Effects:
        - Removes line from scene
        - Pushes command to undo stack

    Emits:
        pattern_changed signal

    Example:
        relation = canvas.relations[0]
        canvas.remove_relation(relation)
    """
```

#### Pattern Serialization

##### `get_pattern_data()`

```python
def get_pattern_data(self) -> Dict[str, Any]:
    """Get pattern data for saving.

    Returns:
        Dict containing pattern data:
        {
            "candles": [
                {
                    "type": "bullish",
                    "ohlc": {"open": 50, "high": 90, ...},
                    "index": 0,
                    "x": 50, "y": 0
                },
                ...
            ],
            "relations": [
                {
                    "source_index": 0,
                    "target_index": 1,
                    "relation_type": "greater"
                },
                ...
            ]
        }

    Example:
        import json

        # Save pattern to file
        pattern_data = canvas.get_pattern_data()
        with open("pattern.json", "w") as f:
            json.dump(pattern_data, f, indent=2)
    """
```

##### `load_pattern_data()`

```python
def load_pattern_data(self, data: Dict[str, Any]):
    """Load pattern from data.

    Args:
        data: Pattern data dict (from get_pattern_data())

    Side Effects:
        - Clears existing pattern
        - Recreates candles and relations
        - Does NOT populate undo stack (intentional)

    Emits:
        pattern_changed signal

    Example:
        import json

        # Load pattern from file
        with open("pattern.json", "r") as f:
            pattern_data = json.load(f)

        canvas.load_pattern_data(pattern_data)
    """
```

##### `clear_pattern()`

```python
def clear_pattern(self):
    """Clear all candles and relations.

    Side Effects:
        - Removes all items from scene
        - Resets candle index counter
        - Pushes command to undo stack

    Emits:
        pattern_changed signal

    Example:
        canvas.clear_pattern()
        assert len(canvas.candles) == 0
        assert len(canvas.relations) == 0
    """
```

#### Undo/Redo

##### `undo()`

```python
def undo(self):
    """Undo last operation.

    Example:
        candle = canvas.add_candle()
        canvas.undo()  # Candle removed
    """
```

##### `redo()`

```python
def redo(self):
    """Redo last undone operation.

    Example:
        canvas.undo()
        canvas.redo()  # Candle restored
    """
```

##### `can_undo()`

```python
def can_undo(self) -> bool:
    """Check if undo is available.

    Returns:
        True if undo stack has operations, False otherwise

    Example:
        if canvas.can_undo():
            canvas.undo()
    """
```

##### `can_redo()`

```python
def can_redo(self) -> bool:
    """Check if redo is available.

    Returns:
        True if redo stack has operations, False otherwise

    Example:
        if canvas.can_redo():
            canvas.redo()
    """
```

#### Zoom Operations

##### `zoom_in()`

```python
def zoom_in(self):
    """Zoom in (1.2x scale factor).

    Example:
        canvas.zoom_in()
    """
```

##### `zoom_out()`

```python
def zoom_out(self):
    """Zoom out (1/1.2x scale factor).

    Example:
        canvas.zoom_out()
    """
```

##### `zoom_fit()`

```python
def zoom_fit(self):
    """Zoom to fit all candles in view.

    Example:
        # After adding many candles
        canvas.zoom_fit()  # Shows all candles
    """
```

#### Statistics

##### `get_statistics()`

```python
def get_statistics(self) -> Dict[str, Any]:
    """Get pattern statistics.

    Returns:
        Dict containing:
        {
            "total_candles": int,
            "total_relations": int,
            "candle_types": {
                "bullish": int,
                "bearish": int,
                "doji": int
            },
            "avg_ohlc": {
                "open": float,
                "high": float,
                "low": float,
                "close": float
            }
        }

    Example:
        stats = canvas.get_statistics()
        print(f"Total candles: {stats['total_candles']}")
        print(f"Bullish: {stats['candle_types']['bullish']}")
    """
```

---

## CandleToolbar

**File**: `src/ui/widgets/pattern_builder/candle_toolbar.py`

**Class**: `CandleToolbar(QToolBar)`

Toolbar for selecting candle types to add to canvas.

### Constructor

```python
def __init__(self, parent=None):
    """Initialize Candle Toolbar.

    Args:
        parent: Parent widget (optional)
    """
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `candle_buttons` | `Dict[str, QToolButton]` | Dictionary of candle type buttons |
| `candle_button_group` | `QButtonGroup` | Button group for exclusive selection |
| `active_candle_type` | `Optional[str]` | Currently selected candle type |

### Methods

##### `get_active_candle_type()`

```python
def get_active_candle_type(self) -> Optional[str]:
    """Get currently selected candle type.

    Returns:
        "bullish", "bearish", "doji", or None if no selection

    Example:
        candle_type = toolbar.get_active_candle_type()
        if candle_type:
            canvas.add_candle(candle_type=candle_type)
    """
```

##### `set_active_candle_type()`

```python
def set_active_candle_type(self, candle_type: str):
    """Set active candle type programmatically.

    Args:
        candle_type: "bullish", "bearish", or "doji"

    Example:
        toolbar.set_active_candle_type("bullish")
        toolbar.candle_buttons["bullish"].setChecked(True)
    """
```

---

## PropertiesPanel

**File**: `src/ui/widgets/pattern_builder/properties_panel.py`

**Class**: `PropertiesPanel(QWidget)`

Panel for editing selected candle properties.

### Constructor

```python
def __init__(self, parent=None):
    """Initialize Properties Panel.

    Args:
        parent: Parent widget (optional)
    """
```

### Signals

```python
class PropertiesPanel(QWidget):
    # Emitted when user clicks "Apply Changes"
    values_changed = pyqtSignal(object, str, dict)
    # Args: (candle, candle_type, ohlc)
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `selected_candle` | `Optional[CandleGraphicsItem]` | Currently editing candle |
| `open_spin` | `QDoubleSpinBox` | Open price editor |
| `high_spin` | `QDoubleSpinBox` | High price editor |
| `low_spin` | `QDoubleSpinBox` | Low price editor |
| `close_spin` | `QDoubleSpinBox` | Close price editor |
| `type_combo` | `QComboBox` | Candle type selector |
| `index_spin` | `QSpinBox` | Candle index (read-only) |

### Methods

##### `on_canvas_selection_changed()`

```python
def on_canvas_selection_changed(self, selected_candles: List[CandleGraphicsItem]):
    """Update panel when canvas selection changes.

    Args:
        selected_candles: List of selected candles from canvas

    Side Effects:
        - Enables panel if single candle selected
        - Disables panel if 0 or multiple candles selected
        - Populates spin boxes with candle values

    Example:
        # Connect to canvas signal
        canvas.candle_selected.connect(
            lambda candle: properties.on_canvas_selection_changed([candle])
        )
        canvas.selection_cleared.connect(
            lambda: properties.on_canvas_selection_changed([])
        )
    """
```

##### `_validate_ohlc()`

```python
def _validate_ohlc(self, ohlc: Dict[str, float]) -> Tuple[bool, str]:
    """Validate OHLC values.

    Args:
        ohlc: Dict with "open", "high", "low", "close" keys

    Returns:
        Tuple of (is_valid: bool, error_message: str)

    Validation Rules:
        - high >= max(open, close)
        - low <= min(open, close)
        - all values >= 0

    Example:
        is_valid, error = properties._validate_ohlc({
            "open": 50.0,
            "high": 90.0,  # Must be >= open and close
            "low": 30.0,   # Must be <= open and close
            "close": 85.0
        })

        if not is_valid:
            print(f"Validation error: {error}")
    """
```

---

## CandleGraphicsItem

**File**: `src/ui/widgets/pattern_builder/candle_graphics_item.py`

**Class**: `CandleGraphicsItem(QGraphicsItem)`

Individual candle visual item on canvas.

### Constructor

```python
def __init__(
    self,
    candle_type: str,
    ohlc: Dict[str, float],
    index: int,
    theme_manager: ThemeManager
):
    """Initialize Candle Graphics Item.

    Args:
        candle_type: "bullish", "bearish", or "doji"
        ohlc: OHLC values dict
        index: Candle position in pattern
        theme_manager: Theme manager for colors
    """
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `candle_type` | `str` | "bullish", "bearish", or "doji" |
| `ohlc` | `Dict[str, float]` | OHLC values |
| `index` | `int` | Candle position in pattern |
| `width` | `float` | Candle body width (default: 20) |
| `wick_width` | `float` | Wick line width (default: 2) |

### Methods

##### `boundingRect()`

```python
def boundingRect(self) -> QRectF:
    """Get bounding rectangle for collision detection.

    Returns:
        QRectF: Bounding rectangle
    """
```

##### `paint()`

```python
def paint(self, painter: QPainter, option, widget):
    """Paint candle on canvas.

    Args:
        painter: QPainter object
        option: Style option
        widget: Widget being painted on

    Visual Rendering:
        - Bullish: Green body, black wick
        - Bearish: Red body, black wick
        - Doji: Gray small body, black wick
    """
```

---

## RelationLine

**File**: `src/ui/widgets/pattern_builder/relation_line.py`

**Class**: `RelationLine(QGraphicsLineItem)`

Visual line connecting two candles with relation type label.

### Constructor

```python
def __init__(
    self,
    source: CandleGraphicsItem,
    target: CandleGraphicsItem,
    relation_type: str,
    theme_manager: ThemeManager
):
    """Initialize Relation Line.

    Args:
        source: Source candle
        target: Target candle
        relation_type: "greater", "less", or "equal"
        theme_manager: Theme manager for colors
    """
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `source` | `CandleGraphicsItem` | Source candle |
| `target` | `CandleGraphicsItem` | Target candle |
| `relation_type` | `str` | "greater", "less", or "equal" |
| `label` | `QGraphicsTextItem` | Text label (>, <, =) |

### Methods

##### `update_position()`

```python
def update_position(self):
    """Update line position when candles move.

    Called automatically when source or target candle moves.
    """
```

---

## Data Models

### Pattern Data Format

```python
pattern_data = {
    "candles": [
        {
            "type": "bullish",  # or "bearish", "doji"
            "ohlc": {
                "open": 50.0,
                "high": 90.0,
                "low": 30.0,
                "close": 85.0
            },
            "index": 0,
            "x": 50.0,
            "y": 0.0
        },
        # ... more candles
    ],
    "relations": [
        {
            "source_index": 0,
            "target_index": 1,
            "relation_type": "greater"  # or "less", "equal"
        },
        # ... more relations
    ]
}
```

### OHLC Data Format

```python
ohlc = {
    "open": float,   # Opening price
    "high": float,   # Highest price (must be >= open, close)
    "low": float,    # Lowest price (must be <= open, close)
    "close": float   # Closing price
}
```

---

## Signals & Slots

### Canvas Signals

```python
# Pattern structure changed (candle added/removed/modified)
pattern_changed = pyqtSignal()

# Single candle selected
candle_selected = pyqtSignal(object)  # Args: CandleGraphicsItem

# Selection cleared
selection_cleared = pyqtSignal()
```

### Properties Panel Signals

```python
# User clicked "Apply Changes"
values_changed = pyqtSignal(object, str, dict)
# Args: (candle, candle_type, ohlc)
```

### Connection Example

```python
# Connect canvas to properties panel
canvas.candle_selected.connect(
    lambda candle: properties.on_canvas_selection_changed([candle])
)
canvas.selection_cleared.connect(
    lambda: properties.on_canvas_selection_changed([])
)

# Connect properties panel to canvas
properties.values_changed.connect(
    lambda candle, ctype, ohlc: canvas.update_candle_properties(candle, ctype, ohlc)
)

# Connect canvas to external handler
canvas.pattern_changed.connect(on_pattern_changed)

def on_pattern_changed():
    stats = canvas.get_statistics()
    print(f"Pattern updated: {stats['total_candles']} candles")
```

---

## Example Usage

### Basic Pattern Creation

```python
from PyQt6.QtWidgets import QApplication
from ui.windows.cel_editor.main_window import CelEditorWindow

# Create application
app = QApplication(sys.argv)

# Create CEL Editor window
window = CelEditorWindow(strategy_name="My Strategy")

# Access components
toolbar = window.candle_toolbar
canvas = window.pattern_canvas
properties = window.properties_panel

# Add candles
toolbar.set_active_candle_type("bullish")
candle1 = canvas.add_candle()

toolbar.set_active_candle_type("bearish")
candle2 = canvas.add_candle()

# Add relation
relation = canvas.add_relation(candle1, candle2, "greater")

# Show window
window.show()
app.exec()
```

### Programmatic Pattern Building

```python
def create_bullish_engulfing_pattern(canvas):
    """Create a bullish engulfing pattern programmatically."""

    # Candle 0: Small bearish
    candle0 = canvas.add_candle(
        candle_type="bearish",
        ohlc={
            "open": 55.0,
            "high": 60.0,
            "low": 45.0,
            "close": 48.0
        }
    )

    # Candle 1: Large bullish (engulfs candle 0)
    candle1 = canvas.add_candle(
        candle_type="bullish",
        ohlc={
            "open": 40.0,   # Below candle0.low
            "high": 95.0,   # Above candle0.high
            "low": 35.0,
            "close": 90.0
        }
    )

    # Relation: candle1 engulfs candle0
    relation = canvas.add_relation(candle0, candle1, "less")

    return {
        "candles": [candle0, candle1],
        "relation": relation
    }

# Usage
pattern = create_bullish_engulfing_pattern(canvas)
canvas.zoom_fit()
```

### Pattern Save/Load

```python
import json

def save_pattern(canvas, filename):
    """Save pattern to JSON file."""
    pattern_data = canvas.get_pattern_data()
    with open(filename, "w") as f:
        json.dump(pattern_data, f, indent=2)
    print(f"Pattern saved to {filename}")

def load_pattern(canvas, filename):
    """Load pattern from JSON file."""
    with open(filename, "r") as f:
        pattern_data = json.load(f)
    canvas.load_pattern_data(pattern_data)
    canvas.zoom_fit()
    print(f"Pattern loaded from {filename}")

# Usage
save_pattern(canvas, "patterns/bullish_reversal.json")
load_pattern(canvas, "patterns/bullish_reversal.json")
```

### Pattern Validation

```python
def validate_pattern(canvas) -> Tuple[bool, List[str]]:
    """Validate pattern for consistency.

    Returns:
        Tuple of (is_valid, error_list)
    """
    errors = []

    # Check minimum candles
    if len(canvas.candles) < 2:
        errors.append("Pattern must have at least 2 candles")

    # Validate OHLC for each candle
    for candle in canvas.candles:
        ohlc = candle.ohlc
        if ohlc["high"] < max(ohlc["open"], ohlc["close"]):
            errors.append(f"Candle {candle.index}: High < max(Open, Close)")
        if ohlc["low"] > min(ohlc["open"], ohlc["close"]):
            errors.append(f"Candle {candle.index}: Low > min(Open, Close)")

    # Check orphaned candles (no relations)
    candles_in_relations = set()
    for relation in canvas.relations:
        candles_in_relations.add(relation.source)
        candles_in_relations.add(relation.target)

    orphaned = [c for c in canvas.candles if c not in candles_in_relations]
    if orphaned:
        indices = [c.index for c in orphaned]
        errors.append(f"Orphaned candles (no relations): {indices}")

    return (len(errors) == 0, errors)

# Usage
is_valid, errors = validate_pattern(canvas)
if not is_valid:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ Pattern is valid")
```

### Batch Operations

```python
def scale_all_ohlc(canvas, factor: float):
    """Scale all OHLC values by a factor.

    Args:
        canvas: PatternBuilderCanvas
        factor: Scaling factor (e.g., 1.5 for 50% increase)
    """
    for candle in canvas.candles:
        scaled_ohlc = {
            key: value * factor
            for key, value in candle.ohlc.items()
        }
        canvas.update_candle_properties(
            candle=candle,
            candle_type=candle.candle_type,
            ohlc=scaled_ohlc
        )

# Usage
scale_all_ohlc(canvas, factor=1.2)  # Increase all prices by 20%
```

### Event Handling

```python
class PatternEventHandler:
    """Custom event handler for pattern changes."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.connect_signals()

    def connect_signals(self):
        """Connect to canvas signals."""
        self.canvas.pattern_changed.connect(self.on_pattern_changed)
        self.canvas.candle_selected.connect(self.on_candle_selected)
        self.canvas.selection_cleared.connect(self.on_selection_cleared)

    def on_pattern_changed(self):
        """Handle pattern structure change."""
        stats = self.canvas.get_statistics()
        print(f"Pattern changed: {stats['total_candles']} candles, "
              f"{stats['total_relations']} relations")

    def on_candle_selected(self, candle):
        """Handle candle selection."""
        print(f"Candle selected: {candle.candle_type} at index {candle.index}")
        print(f"OHLC: {candle.ohlc}")

    def on_selection_cleared(self):
        """Handle selection clear."""
        print("Selection cleared")

# Usage
handler = PatternEventHandler(canvas)
```

---

## Performance Considerations

### Tested Performance (Phase 2.7.3)

| Operation | 100 Items | 500 Items (Projected) | 1000 Items (Projected) |
|-----------|-----------|----------------------|------------------------|
| Add candles | 24ms | 120ms | 240ms |
| Zoom operations | 214ms | 214ms* | 214ms* |
| Selection | 106ms | 530ms | 1060ms |
| Serialization | <1ms | 3ms | 6ms |
| Load pattern | 20ms | 100ms | 200ms |
| Memory usage | 4.2 MB | 21 MB | 42 MB |

*Zoom performance is constant (view-based, not item-based)

### Best Practices

1. **Batch Operations**: Use undo stack for multiple changes
   ```python
   canvas.undo_stack.beginMacro("Batch Add")
   for i in range(10):
       canvas.add_candle()
   canvas.undo_stack.endMacro()  # Single undo operation
   ```

2. **Signal Blocking**: Block signals during bulk operations
   ```python
   canvas.blockSignals(True)
   for candle in candles_to_update:
       canvas.update_candle_properties(candle, ...)
   canvas.blockSignals(False)
   canvas.pattern_changed.emit()  # Single emission
   ```

3. **Memory Management**: Clear large patterns when done
   ```python
   canvas.clear_pattern()
   canvas.scene.clear()  # Force cleanup
   ```

---

## Error Handling

### Common Exceptions

```python
# ValueError: Invalid candle type
try:
    canvas.add_candle(candle_type="invalid")
except ValueError as e:
    print(f"Error: {e}")

# ValueError: Invalid relation (same source/target)
try:
    canvas.add_relation(candle1, candle1, "greater")
except ValueError as e:
    print(f"Error: {e}")

# IndexError: Candle not found
try:
    candle = canvas.candles[100]  # Only 10 candles exist
except IndexError as e:
    print(f"Error: {e}")
```

### Defensive Coding

```python
def safe_add_relation(canvas, source_index, target_index, relation_type):
    """Safely add relation with error handling."""
    try:
        if source_index >= len(canvas.candles):
            raise IndexError(f"Source index {source_index} out of range")
        if target_index >= len(canvas.candles):
            raise IndexError(f"Target index {target_index} out of range")

        source = canvas.candles[source_index]
        target = canvas.candles[target_index]

        relation = canvas.add_relation(source, target, relation_type)
        return relation

    except (ValueError, IndexError) as e:
        print(f"Failed to add relation: {e}")
        return None
```

---

## Testing

### Unit Testing Example

```python
import pytest
from PyQt6.QtWidgets import QApplication
from ui.windows.cel_editor.main_window import CelEditorWindow

@pytest.fixture
def app():
    """Create QApplication fixture."""
    return QApplication([])

@pytest.fixture
def canvas(app):
    """Create PatternBuilderCanvas fixture."""
    window = CelEditorWindow(strategy_name="Test")
    return window.pattern_canvas

def test_add_candle(canvas):
    """Test adding candle to canvas."""
    candle = canvas.add_candle(candle_type="bullish")
    assert len(canvas.candles) == 1
    assert candle.candle_type == "bullish"

def test_add_relation(canvas):
    """Test adding relation between candles."""
    candle1 = canvas.add_candle()
    candle2 = canvas.add_candle()

    relation = canvas.add_relation(candle1, candle2, "greater")
    assert len(canvas.relations) == 1
    assert relation.source == candle1
    assert relation.target == candle2

def test_undo_redo(canvas):
    """Test undo/redo operations."""
    candle = canvas.add_candle()
    assert len(canvas.candles) == 1

    canvas.undo()
    assert len(canvas.candles) == 0

    canvas.redo()
    assert len(canvas.candles) == 1
```

---

## Changelog

**Version 1.0 (2026-01-20)**
- Initial API documentation
- Covers all Pattern Builder components
- Performance benchmarks included
- Comprehensive examples provided

---

## See Also

- **User Guide**: `docs/user_guides/CEL_Editor_Pattern_Builder_Guide.md`
- **Tutorial**: `docs/tutorials/CEL_Editor_Tutorial.md`
- **Test Results**: `docs/testing/CEL_Editor_Phase_2_7_*.md`
- **Source Code**: `src/ui/widgets/pattern_builder/`

---

**End of API Reference**
