"""
Heatmap Settings Model

Configuration model for heatmap feature with validation and persistence.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple
import json


class WindowDuration(str, Enum):
    """Supported time window durations."""

    TWO_HOURS = "2h"
    EIGHT_HOURS = "8h"
    TWO_DAYS = "2d"

    def to_hours(self) -> float:
        """Convert duration to hours."""
        if self == WindowDuration.TWO_HOURS:
            return 2.0
        elif self == WindowDuration.EIGHT_HOURS:
            return 8.0
        elif self == WindowDuration.TWO_DAYS:
            return 48.0
        return 2.0

    def to_milliseconds(self) -> int:
        """Convert duration to milliseconds."""
        return int(self.to_hours() * 3600 * 1000)


class ColorPalette(str, Enum):
    """Supported color palettes."""

    HOT = "hot"
    COOL = "cool"
    VIRIDIS = "viridis"
    PLASMA = "plasma"


class NormalizationMode(str, Enum):
    """Intensity normalization modes."""

    LINEAR = "linear"
    SQRT = "sqrt"
    LOG = "log"
    LOG10 = "log10"


class DecayMode(str, Enum):
    """Time decay modes."""

    OFF = "off"
    TWENTY_MIN = "20m"
    SIXTY_MIN = "60m"
    SIX_HOURS = "6h"

    def to_milliseconds(self) -> int:
        """Convert decay half-life to milliseconds."""
        if self == DecayMode.TWENTY_MIN:
            return 20 * 60 * 1000
        elif self == DecayMode.SIXTY_MIN:
            return 60 * 60 * 1000
        elif self == DecayMode.SIX_HOURS:
            return 6 * 3600 * 1000
        return 0  # OFF


class ResolutionMode(str, Enum):
    """Grid resolution modes."""

    AUTO = "auto"
    MANUAL = "manual"


@dataclass
class HeatmapSettings:
    """
    Configuration settings for liquidation heatmap.

    All settings are persisted and can be saved/loaded from JSON.
    """

    # Core settings
    enabled: bool = False
    symbol: str = "BTCUSDT"
    source: str = "Binance USD-M Futures"

    # Time window
    window: WindowDuration = WindowDuration.TWO_HOURS

    # Visual settings
    opacity: float = 0.5  # 0.0 - 1.0
    palette: ColorPalette = ColorPalette.HOT
    normalization: NormalizationMode = NormalizationMode.SQRT
    decay: DecayMode = DecayMode.OFF

    # Resolution settings
    resolution_mode: ResolutionMode = ResolutionMode.AUTO
    manual_rows: int = 200  # Only used when resolution_mode = MANUAL
    manual_cols: int = 1000  # Only used when resolution_mode = MANUAL

    # Database settings
    db_path: str = "data/heatmap/liquidations.db"
    batch_size: int = 100
    flush_interval_ms: int = 1000
    retention_days: int = 14

    # WebSocket settings
    ws_url: str = "wss://fstream.binance.com/ws"
    reconnect_delay_ms: int = 1000
    max_reconnect_delay_ms: int = 60000

    # Performance settings
    update_rate_limit_ms: int = 500  # Minimum time between UI updates
    max_grid_cells: int = 100000  # Safety limit

    def __post_init__(self):
        """Validate settings after initialization."""
        self._validate()

    def _validate(self):
        """Validate setting values."""
        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError(f"opacity must be 0-1, got {self.opacity}")

        if self.manual_rows <= 0:
            raise ValueError(f"manual_rows must be positive, got {self.manual_rows}")

        if self.manual_cols <= 0:
            raise ValueError(f"manual_cols must be positive, got {self.manual_cols}")

        if self.batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {self.batch_size}")

        if self.retention_days < 0:
            raise ValueError(f"retention_days must be non-negative, got {self.retention_days}")

    def to_dict(self) -> dict:
        """Convert settings to dictionary (for JSON serialization)."""
        data = asdict(self)

        # Convert enums to strings
        data["window"] = self.window.value
        data["palette"] = self.palette.value
        data["normalization"] = self.normalization.value
        data["decay"] = self.decay.value
        data["resolution_mode"] = self.resolution_mode.value

        return data

    @classmethod
    def from_dict(cls, data: dict) -> "HeatmapSettings":
        """Create settings from dictionary."""
        # Convert string values back to enums
        if "window" in data:
            data["window"] = WindowDuration(data["window"])
        if "palette" in data:
            data["palette"] = ColorPalette(data["palette"])
        if "normalization" in data:
            data["normalization"] = NormalizationMode(data["normalization"])
        if "decay" in data:
            data["decay"] = DecayMode(data["decay"])
        if "resolution_mode" in data:
            data["resolution_mode"] = ResolutionMode(data["resolution_mode"])

        return cls(**data)

    def save(self, path: str | Path) -> None:
        """Save settings to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "HeatmapSettings":
        """Load settings from JSON file."""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Settings file not found: {path}")

        with open(path, "r") as f:
            data = json.load(f)

        return cls.from_dict(data)

    @classmethod
    def get_default_path(cls) -> Path:
        """Get default settings file path."""
        return Path("data/heatmap/settings.json")

    def clone(self) -> "HeatmapSettings":
        """Create a deep copy of settings."""
        return HeatmapSettings.from_dict(self.to_dict())

    def get_grid_resolution(
        self,
        window_width: int,
        window_height: int,
        target_px_per_bin: float = 2.3
    ) -> Tuple[int, int]:
        """
        Get grid resolution (rows, cols) based on mode.

        Args:
            window_width: Chart window width in pixels
            window_height: Chart window height in pixels
            target_px_per_bin: Target pixels per grid cell (for AUTO mode)

        Returns:
            (rows, cols) tuple
        """
        if self.resolution_mode == ResolutionMode.MANUAL:
            return (self.manual_rows, self.manual_cols)

        # AUTO mode
        rows = max(1, min(round(window_height / target_px_per_bin), 380))
        cols = max(1, min(round(window_width / (target_px_per_bin / 2)), 1700))

        return (rows, cols)


# Example usage
if __name__ == "__main__":
    # Create default settings
    settings = HeatmapSettings()
    print("Default settings:")
    print(f"  Enabled: {settings.enabled}")
    print(f"  Window: {settings.window.value} ({settings.window.to_hours()}h)")
    print(f"  Opacity: {settings.opacity}")
    print(f"  Palette: {settings.palette.value}")

    # Save to file
    settings.save("test_settings.json")
    print("\nSaved to test_settings.json")

    # Load from file
    loaded = HeatmapSettings.load("test_settings.json")
    print(f"\nLoaded settings: {loaded.window.value}")

    # Test grid resolution
    rows, cols = settings.get_grid_resolution(1060, 550)
    print(f"\nAuto resolution for 1060x550: {rows} rows × {cols} cols")

    # Clone
    cloned = settings.clone()
    cloned.enabled = True
    print(f"\nOriginal enabled: {settings.enabled}")
    print(f"Cloned enabled: {cloned.enabled}")
