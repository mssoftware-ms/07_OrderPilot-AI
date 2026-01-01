"""Data Models for Chart Marking System.

Provides dataclasses and enums for all chart marking types:
- EntryMarker: Long/Short entry arrows
- Zone: Support/Resistance rectangles
- StructureBreakMarker: BoS/CHoCH markers
- StopLossLine: SL lines with risk display
- MultiChartLayout: Multi-monitor configuration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class MarkerShape(str, Enum):
    """Available marker shapes in Lightweight Charts."""

    ARROW_UP = "arrowUp"
    ARROW_DOWN = "arrowDown"
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE_UP = "triangleUp"
    TRIANGLE_DOWN = "triangleDown"


class MarkerPosition(str, Enum):
    """Marker position relative to bar."""

    ABOVE_BAR = "aboveBar"
    BELOW_BAR = "belowBar"
    IN_BAR = "inBar"


class Direction(str, Enum):
    """Trade/signal direction."""

    LONG = "long"
    SHORT = "short"
    BULLISH = "bullish"
    BEARISH = "bearish"


class ZoneType(str, Enum):
    """Support/Resistance zone type."""

    SUPPORT = "support"
    RESISTANCE = "resistance"
    DEMAND = "demand"
    SUPPLY = "supply"


class StructureBreakType(str, Enum):
    """Market structure break types."""

    BOS = "BoS"  # Break of Structure
    CHOCH = "CHoCH"  # Change of Character
    MSB = "MSB"  # Market Structure Break


class LineStyle(str, Enum):
    """Line style options."""

    SOLID = "solid"
    DASHED = "dashed"
    DOTTED = "dotted"


def _normalize_timestamp(ts: int | datetime) -> int:
    """Convert timestamp to Unix seconds."""
    if isinstance(ts, datetime):
        return int(ts.timestamp())
    return ts


@dataclass
class EntryMarker:
    """Entry arrow marker for Long/Short signals.

    Attributes:
        id: Unique identifier
        timestamp: Bar timestamp (Unix seconds or datetime)
        price: Entry price level
        direction: Long/Short or Bullish/Bearish
        text: Display text on marker
        tooltip: Hover tooltip text
        score: Optional signal confidence score (0-100)
    """

    id: str
    timestamp: int | datetime
    price: float
    direction: Direction
    text: str = ""
    tooltip: str = ""
    score: Optional[float] = None

    def to_chart_marker(self) -> dict[str, Any]:
        """Convert to Lightweight Charts marker format."""
        from .constants import Colors

        is_long = self.direction in (Direction.LONG, Direction.BULLISH)
        return {
            "time": _normalize_timestamp(self.timestamp),
            "position": MarkerPosition.BELOW_BAR.value if is_long else MarkerPosition.ABOVE_BAR.value,
            "color": Colors.LONG_ENTRY if is_long else Colors.SHORT_ENTRY,
            "shape": MarkerShape.ARROW_UP.value if is_long else MarkerShape.ARROW_DOWN.value,
            "text": self.text or ("Long Entry" if is_long else "Short Entry"),
            "id": self.id,
            "size": 2,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": self.id,
            "timestamp": _normalize_timestamp(self.timestamp),
            "price": self.price,
            "direction": self.direction.value,
            "text": self.text,
            "tooltip": self.tooltip,
            "score": self.score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EntryMarker":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            price=data["price"],
            direction=Direction(data["direction"]),
            text=data.get("text", ""),
            tooltip=data.get("tooltip", ""),
            score=data.get("score"),
        )


@dataclass
class Zone:
    """Support/Resistance zone rectangle.

    Attributes:
        id: Unique identifier
        zone_type: Type (support/resistance/demand/supply)
        start_time: Zone start timestamp
        end_time: Zone end timestamp
        top_price: Upper price boundary
        bottom_price: Lower price boundary
        color: Optional custom fill color
        opacity: Fill opacity (0-1)
        label: Zone label text
        is_active: Whether zone is currently active
    """

    id: str
    zone_type: ZoneType
    start_time: int | datetime
    end_time: int | datetime
    top_price: float
    bottom_price: float
    color: Optional[str] = None
    opacity: float = 0.3
    label: str = ""
    is_active: bool = True

    @property
    def fill_color(self) -> str:
        """Get fill color with opacity."""
        if self.color:
            return self.color

        from .constants import Colors

        colors = {
            ZoneType.SUPPORT: Colors.SUPPORT_FILL,
            ZoneType.RESISTANCE: Colors.RESISTANCE_FILL,
            ZoneType.DEMAND: Colors.DEMAND_FILL,
            ZoneType.SUPPLY: Colors.SUPPLY_FILL,
        }
        base = colors.get(self.zone_type, Colors.SUPPORT_FILL)

        # If custom opacity, rebuild rgba
        if self.opacity != 0.3 and base.startswith("rgba"):
            parts = base.rsplit(",", 1)
            return f"{parts[0]}, {self.opacity})"
        return base

    @property
    def border_color(self) -> str:
        """Get solid border color."""
        from .constants import Colors

        colors = {
            ZoneType.SUPPORT: Colors.SUPPORT_BORDER,
            ZoneType.RESISTANCE: Colors.RESISTANCE_BORDER,
            ZoneType.DEMAND: Colors.DEMAND_BORDER,
            ZoneType.SUPPLY: Colors.SUPPLY_BORDER,
        }
        return colors.get(self.zone_type, Colors.SUPPORT_BORDER)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": self.id,
            "zone_type": self.zone_type.value,
            "start_time": _normalize_timestamp(self.start_time),
            "end_time": _normalize_timestamp(self.end_time),
            "top_price": self.top_price,
            "bottom_price": self.bottom_price,
            "color": self.color,
            "opacity": self.opacity,
            "label": self.label,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Zone":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            zone_type=ZoneType(data["zone_type"]),
            start_time=data["start_time"],
            end_time=data["end_time"],
            top_price=data["top_price"],
            bottom_price=data["bottom_price"],
            color=data.get("color"),
            opacity=data.get("opacity", 0.3),
            label=data.get("label", ""),
            is_active=data.get("is_active", True),
        )


@dataclass
class StructureBreakMarker:
    """BoS/CHoCH market structure marker.

    Attributes:
        id: Unique identifier
        timestamp: Break timestamp
        price: Break price level
        break_type: BoS or CHoCH
        direction: Bullish or Bearish
        text: Display text
    """

    id: str
    timestamp: int | datetime
    price: float
    break_type: StructureBreakType
    direction: Direction
    text: str = ""

    def to_chart_marker(self) -> dict[str, Any]:
        """Convert to Lightweight Charts marker format."""
        from .constants import Colors

        is_bullish = self.direction in (Direction.LONG, Direction.BULLISH)

        if self.break_type == StructureBreakType.BOS:
            color = Colors.BOS_BULLISH if is_bullish else Colors.BOS_BEARISH
            shape = MarkerShape.TRIANGLE_UP if is_bullish else MarkerShape.TRIANGLE_DOWN
        elif self.break_type == StructureBreakType.CHOCH:
            color = Colors.CHOCH_BULLISH if is_bullish else Colors.CHOCH_BEARISH
            shape = MarkerShape.TRIANGLE_DOWN if is_bullish else MarkerShape.TRIANGLE_UP
        else:  # MSB
            color = Colors.MSB
            shape = MarkerShape.SQUARE

        return {
            "time": _normalize_timestamp(self.timestamp),
            "position": MarkerPosition.BELOW_BAR.value if is_bullish else MarkerPosition.ABOVE_BAR.value,
            "color": color,
            "shape": shape.value,
            "text": self.text or self.break_type.value,
            "id": self.id,
            "size": 2,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": self.id,
            "timestamp": _normalize_timestamp(self.timestamp),
            "price": self.price,
            "break_type": self.break_type.value,
            "direction": self.direction.value,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StructureBreakMarker":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            price=data["price"],
            break_type=StructureBreakType(data["break_type"]),
            direction=Direction(data["direction"]),
            text=data.get("text", ""),
        )


@dataclass
class StopLossLine:
    """Stop-loss line with label and optional risk display.

    Attributes:
        id: Unique identifier
        price: Stop-loss price level
        entry_price: Entry price for risk calculation
        direction: Position direction (affects risk calculation)
        color: Line color
        line_style: Solid/dashed/dotted
        label: Line label text
        show_risk: Whether to show risk percentage
        risk_percent: Pre-calculated risk (overrides calculation)
    """

    id: str
    price: float
    entry_price: Optional[float] = None
    direction: Direction = Direction.LONG
    color: str = "#ef5350"
    line_style: LineStyle = LineStyle.DASHED
    label: str = "SL"
    show_risk: bool = True
    risk_percent: Optional[float] = None

    @property
    def calculated_risk_pct(self) -> Optional[float]:
        """Calculate risk percentage from entry to SL."""
        if self.risk_percent is not None:
            return self.risk_percent
        if self.entry_price and self.entry_price > 0:
            return abs(self.entry_price - self.price) / self.entry_price * 100
        return None

    @property
    def display_label(self) -> str:
        """Generate label with optional risk percentage."""
        base = f"{self.label} @ {self.price:.2f}"
        risk = self.calculated_risk_pct
        if self.show_risk and risk is not None:
            base += f" ({risk:.1f}%)"
        return base

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": self.id,
            "price": self.price,
            "entry_price": self.entry_price,
            "direction": self.direction.value,
            "color": self.color,
            "line_style": self.line_style.value,
            "label": self.label,
            "show_risk": self.show_risk,
            "risk_percent": self.risk_percent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StopLossLine":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            price=data["price"],
            entry_price=data.get("entry_price"),
            direction=Direction(data.get("direction", "long")),
            color=data.get("color", "#ef5350"),
            line_style=LineStyle(data.get("line_style", "dashed")),
            label=data.get("label", "SL"),
            show_risk=data.get("show_risk", True),
            risk_percent=data.get("risk_percent"),
        )


@dataclass
class ChartConfig:
    """Configuration for a single chart in a layout.

    Attributes:
        symbol: Trading symbol
        timeframe: Chart timeframe (e.g., "1T", "5T", "1H", "1D")
        monitor: Monitor index (0 = primary)
        position: Window position {x, y, width, height}
    """

    symbol: str
    timeframe: str = "1T"
    monitor: int = 0
    position: dict = field(default_factory=lambda: {"x": 0, "y": 0, "width": 800, "height": 600})

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "monitor": self.monitor,
            "position": self.position,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChartConfig":
        """Create from dictionary."""
        return cls(
            symbol=data["symbol"],
            timeframe=data.get("timeframe", "1T"),
            monitor=data.get("monitor", 0),
            position=data.get("position", {"x": 0, "y": 0, "width": 800, "height": 600}),
        )


@dataclass
class MultiChartLayout:
    """Layout preset for multi-chart/multi-monitor configuration.

    Attributes:
        id: Unique identifier
        name: Layout display name
        charts: List of chart configurations
        sync_crosshair: Whether to sync crosshairs across charts
        created_at: Layout creation timestamp
    """

    id: str
    name: str
    charts: list[ChartConfig] = field(default_factory=list)
    sync_crosshair: bool = False
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "id": self.id,
            "name": self.name,
            "charts": [c.to_dict() for c in self.charts],
            "sync_crosshair": self.sync_crosshair,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MultiChartLayout":
        """Create from dictionary."""
        charts = [ChartConfig.from_dict(c) for c in data.get("charts", [])]
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass

        return cls(
            id=data["id"],
            name=data["name"],
            charts=charts,
            sync_crosshair=data.get("sync_crosshair", False),
            created_at=created_at,
        )
