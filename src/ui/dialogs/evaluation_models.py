"""Data models for Evaluation Dialog.

Contains Pydantic/dataclass models for evaluation entries
(Support, Resistance, Targets, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EvaluationEntry:
    """Single evaluation entry (Support, Resistance, Target, etc.).

    Attributes:
        label: Entry label (e.g., "Support Zone", "Target 1")
        value: Price value (numeric or range like "100-200")
        info: Additional info/comment (optional)
        color: Color code for chart drawing (hex with alpha, e.g., "#0d6efd55")
    """

    label: str
    value: str  # numeric or range like "100-200"
    info: str = ""
    color: str = "#0d6efd55"

    def is_range(self) -> bool:
        """Check if value is a price range (e.g., '100-200')."""
        return "-" in self.value and not self.value.startswith("-")

    def get_range(self) -> tuple[float, float] | None:
        """Parse range value into (low, high).

        Returns:
            (low, high) tuple or None if not a valid range
        """
        if not self.is_range():
            return None
        try:
            parts = self.value.split("-")
            low = float(parts[0].strip())
            high = float(parts[1].strip())
            return (low, high)
        except (ValueError, IndexError):
            return None

    def get_price(self) -> float | None:
        """Parse single price value.

        Returns:
            Price as float or None if value is a range or invalid
        """
        if self.is_range():
            return None
        try:
            return float(self.value)
        except ValueError:
            return None

    def to_tuple(self) -> tuple[str, str, str, str]:
        """Convert to tuple for backward compatibility.

        Returns:
            (label, value, info, color) tuple
        """
        return (self.label, self.value, self.info, self.color)

    @classmethod
    def from_tuple(cls, data: tuple) -> EvaluationEntry:
        """Create entry from tuple.

        Args:
            data: Tuple of (label, value) or (label, value, info) or (label, value, info, color)

        Returns:
            EvaluationEntry instance
        """
        if len(data) >= 4:
            return cls(data[0], data[1], data[2], data[3])
        elif len(data) == 3:
            return cls(data[0], data[1], data[2])
        elif len(data) == 2:
            return cls(data[0], data[1])
        else:
            raise ValueError(f"Invalid tuple length: {len(data)}")
