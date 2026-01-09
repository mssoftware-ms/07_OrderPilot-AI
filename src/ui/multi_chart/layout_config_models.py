"""Layout Configuration Models - Dataclasses for Chart Layouts.

Refactored from layout_manager.py.

Contains:
- ChartWindowConfig: Single window configuration with serialization
- ChartLayoutConfig: Multiple windows configuration with serialization
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class ChartWindowConfig:
    """Configuration for a single chart window."""

    symbol: str
    timeframe: str  # e.g., "1T", "5T", "1H", "1D"
    period: str = "1M"  # How far back to load data
    monitor: int = 0  # Monitor index (0 = primary)
    x: int = 0
    y: int = 0
    width: int = 800
    height: int = 600
    indicators: list[str] = field(default_factory=list)
    auto_stream: bool = False  # Auto-start live streaming

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ChartWindowConfig":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ChartLayoutConfig:
    """Configuration for a complete chart layout (multiple windows)."""

    name: str
    description: str = ""
    windows: list[ChartWindowConfig] = field(default_factory=list)
    sync_crosshair: bool = True
    sync_time_range: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "windows": [w.to_dict() for w in self.windows],
            "sync_crosshair": self.sync_crosshair,
            "sync_time_range": self.sync_time_range,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChartLayoutConfig":
        """Create from dictionary."""
        windows = [ChartWindowConfig.from_dict(w) for w in data.get("windows", [])]
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            windows=windows,
            sync_crosshair=data.get("sync_crosshair", True),
            sync_time_range=data.get("sync_time_range", False),
        )
