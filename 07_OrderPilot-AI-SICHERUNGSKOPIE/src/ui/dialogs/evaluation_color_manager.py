"""Color Manager for Evaluation Entries.

Manages color rules and auto-assignment for evaluation entries.
"""

from __future__ import annotations

from PyQt6.QtCore import QSettings


class ColorManager:
    """Manage color rules and auto-assignment for evaluation entries."""

    # Default color rules (keyword -> color mapping)
    DEFAULT_RULES = {
        "stop": "#ef5350",
        "stop loss": "#ef5350",
        "sl": "#ef5350",
        "take profit": "#26a69a",
        "target": "#26a69a",
        "tp": "#26a69a",
        "support": "#2ca8b1",
        "demand": "#2ca8b1",
        "resistance": "#f39c12",
        "supply": "#f39c12",
        "entry long": "#0d6efd",
        "long": "#0d6efd",
        "entry short": "#c2185b",
        "short": "#c2185b",
        "sma": "#9e9e9e",
        "ema": "#9e9e9e",
        "vwap": "#9e9e9e",
        "ma": "#9e9e9e",
    }

    # Fallback color palette for unknown keywords
    FALLBACK_PALETTE = ["#7e57c2", "#ffca28", "#00897b", "#5c6bc0"]

    def __init__(self):
        """Initialize ColorManager with settings."""
        self.settings = QSettings("OrderPilot", "TradingApp")
        self.rules = self._load_rules()

    def _load_rules(self) -> dict[str, str]:
        """Load color rules from settings.

        Returns:
            Dictionary mapping keywords to color codes
        """
        stored = self.settings.value("eval_color_rules", None)
        if isinstance(stored, dict):
            # Merge stored rules with defaults (stored takes precedence)
            return {**self.DEFAULT_RULES, **stored}
        return self.DEFAULT_RULES.copy()

    def save_rules(self) -> None:
        """Save current rules to persistent settings."""
        self.settings.setValue("eval_color_rules", self.rules)
        self.settings.sync()

    def pick_color_for_label(self, label: str) -> str:
        """Auto-assign color based on label keywords.

        Args:
            label: Entry label (e.g., "Support Zone", "Target 1")

        Returns:
            Hex color code (e.g., "#2ca8b1")
        """
        lbl = label.lower()

        # Check rules (first match wins)
        for keyword, color in self.rules.items():
            if keyword in lbl:
                return color

        # Fallback: use hash-based palette for consistent colors
        return self.FALLBACK_PALETTE[hash(lbl) % len(self.FALLBACK_PALETTE)]

    @staticmethod
    def ensure_alpha(color: str) -> str:
        """Ensure color has alpha channel for semi-transparent chart drawing.

        Args:
            color: Color code (hex or rgba)

        Returns:
            Color code with alpha channel
        """
        color = color.strip()

        # Already has alpha or is rgba
        if color.lower().startswith("rgba"):
            return color

        # Hex color
        if color.startswith("#"):
            if len(color) == 7:  # #RRGGBB -> add alpha 55 (33% opacity)
                return color + "55"
            elif len(color) == 9:  # #RRGGBBAA -> already has alpha
                return color
            # Invalid format, use default
            return "#0d6efd55"

        # Unknown format, use default
        return "#0d6efd55"

    def get_all_rules(self) -> dict[str, str]:
        """Get all color rules.

        Returns:
            Dictionary of all rules (keyword -> color)
        """
        return self.rules.copy()

    def update_rule(self, keyword: str, color: str) -> None:
        """Update a single color rule.

        Args:
            keyword: Keyword to update
            color: New color code
        """
        self.rules[keyword] = color

    def reset_to_defaults(self) -> None:
        """Reset all rules to default values."""
        self.rules = self.DEFAULT_RULES.copy()
        self.save_rules()
