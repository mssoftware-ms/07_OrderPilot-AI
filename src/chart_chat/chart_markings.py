"""Chart Markings - Bidirectional chart annotation models.

Manages chart markings that can be sent to AI and received back for updates.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MarkingType(str, Enum):
    """Type of chart marking."""

    SUPPORT_ZONE = "support_zone"
    RESISTANCE_ZONE = "resistance_zone"
    DEMAND_ZONE = "demand_zone"
    SUPPLY_ZONE = "supply_zone"
    ENTRY_LONG = "entry_long"
    ENTRY_SHORT = "entry_short"
    EXIT_POINT = "exit_point"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


class ChartMarking(BaseModel):
    """Single chart marking with price level(s)."""

    id: str  # Unique identifier for this marking
    type: MarkingType
    price: float | None = None  # For single-point markings (entry, stop, etc.)
    price_top: float | None = None  # For zones
    price_bottom: float | None = None  # For zones
    label: str = ""
    is_active: bool = True
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    reasoning: str = ""

    def to_variable_string(self) -> str:
        """Convert to variable format: [#Label; Value]

        Returns:
            String like "[#Stop Loss; 45678.50]" or "[#Support Zone; 45000-46000]"
        """
        label = self.label or self.type.value.replace("_", " ").title()

        if self.price is not None:
            # Single price point
            return f"[#{label}; {self.price:.2f}]"
        elif self.price_top is not None and self.price_bottom is not None:
            # Price zone
            return f"[#{label}; {self.price_bottom:.2f}-{self.price_top:.2f}]"
        else:
            return f"[#{label}; N/A]"

    @classmethod
    def from_variable_string(cls, var_str: str, marking_id: str) -> ChartMarking | None:
        """Parse variable format back to ChartMarking.

        Args:
            var_str: String like "[#Stop Loss; 45678.50]"
            marking_id: Unique ID for this marking

        Returns:
            ChartMarking instance or None if parsing fails
        """
        import re

        # Match pattern: [#Label; Value]
        pattern = r'\[#([^;]+);\s*([^\]]+)\]'
        match = re.match(pattern, var_str.strip())

        if not match:
            return None

        label = match.group(1).strip()
        value = match.group(2).strip()

        # Determine marking type from label
        label_lower = label.lower()
        marking_type = MarkingType.STOP_LOSS  # Default

        if "support" in label_lower:
            marking_type = MarkingType.SUPPORT_ZONE
        elif "resistance" in label_lower:
            marking_type = MarkingType.RESISTANCE_ZONE
        elif "demand" in label_lower:
            marking_type = MarkingType.DEMAND_ZONE
        elif "supply" in label_lower:
            marking_type = MarkingType.SUPPLY_ZONE
        elif "entry" in label_lower and "long" in label_lower:
            marking_type = MarkingType.ENTRY_LONG
        elif "entry" in label_lower and "short" in label_lower:
            marking_type = MarkingType.ENTRY_SHORT
        elif "exit" in label_lower:
            marking_type = MarkingType.EXIT_POINT
        elif "stop" in label_lower:
            marking_type = MarkingType.STOP_LOSS
        elif "take profit" in label_lower or "target" in label_lower:
            marking_type = MarkingType.TAKE_PROFIT
        elif "trailing" in label_lower:
            marking_type = MarkingType.TRAILING_STOP

        # Parse value (can be single price or range)
        if '-' in value and not value.startswith('-'):
            # Range format: "45000-46000"
            try:
                parts = value.split('-')
                price_bottom = float(parts[0].strip())
                price_top = float(parts[1].strip())
                return cls(
                    id=marking_id,
                    type=marking_type,
                    price_top=price_top,
                    price_bottom=price_bottom,
                    label=label,
                )
            except ValueError:
                return None
        else:
            # Single price
            try:
                price = float(value.replace(',', ''))
                return cls(
                    id=marking_id,
                    type=marking_type,
                    price=price,
                    label=label,
                )
            except ValueError:
                return None


class ChartMarkingsState(BaseModel):
    """Complete state of all chart markings."""

    markings: list[ChartMarking] = Field(default_factory=list)
    symbol: str = ""
    timeframe: str = ""

    def to_prompt_text(self) -> str:
        """Convert markings to prompt text for AI.

        Returns:
            Formatted text describing current markings
        """
        if not self.markings:
            return "Keine aktuellen Markierungen im Chart."

        lines = ["**Aktuelle Chart-Markierungen:**"]
        for marking in self.markings:
            if marking.is_active:
                lines.append(f"  {marking.to_variable_string()}")
                if marking.reasoning:
                    lines.append(f"    → {marking.reasoning}")

        return "\n".join(lines)

    def find_marking(self, marking_id: str) -> ChartMarking | None:
        """Find marking by ID."""
        for marking in self.markings:
            if marking.id == marking_id:
                return marking
        return None

    def update_or_add(self, marking: ChartMarking) -> None:
        """Update existing marking or add new one."""
        existing = self.find_marking(marking.id)
        if existing:
            # Update existing
            existing.price = marking.price
            existing.price_top = marking.price_top
            existing.price_bottom = marking.price_bottom
            existing.label = marking.label
            existing.is_active = marking.is_active
            existing.confidence = marking.confidence
            existing.reasoning = marking.reasoning
        else:
            # Add new
            self.markings.append(marking)

    def remove_marking(self, marking_id: str) -> bool:
        """Remove marking by ID.

        Returns:
            True if removed, False if not found
        """
        for i, marking in enumerate(self.markings):
            if marking.id == marking_id:
                self.markings.pop(i)
                return True
        return False


class CompactAnalysisResponse(BaseModel):
    """Compact AI response with variables and brief reasoning."""

    markings_updated: list[str] = Field(default_factory=list)  # Variable strings like "[#Stop Loss; 123.45]"
    markings_removed: list[str] = Field(default_factory=list)  # IDs of markings to remove
    summary: str = ""  # Brief 2-3 sentence summary
    reasoning_bullets: list[str] = Field(default_factory=list)  # Short bullet points

    @classmethod
    def from_ai_text(cls, text: str) -> CompactAnalysisResponse:
        """Parse AI response text into structured format.

        Looks for variable patterns like [#Label; Value] and bullet points.

        Args:
            text: AI response text

        Returns:
            Parsed response
        """
        import re

        # Extract variable markings: [#Label; Value]
        var_pattern = r'\[#[^;]+;\s*[^\]]+\]'
        markings = re.findall(var_pattern, text)

        # Extract bullet points (lines starting with -, *, or •)
        bullet_pattern = r'^[\s]*[-*•]\s+(.+)$'
        bullets = []
        for line in text.split('\n'):
            match = re.match(bullet_pattern, line.strip())
            if match:
                bullets.append(match.group(1).strip())

        # Extract summary (first paragraph that's not a variable or bullet)
        summary_lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line and not re.match(var_pattern, line) and not re.match(bullet_pattern, line):
                summary_lines.append(line)
                if len(summary_lines) >= 3:  # Max 3 lines for summary
                    break

        summary = ' '.join(summary_lines)

        return cls(
            markings_updated=markings,
            markings_removed=[],  # TODO: Detect removal keywords
            summary=summary,
            reasoning_bullets=bullets,
        )
