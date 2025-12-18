"""Strategy Definitions for Tradingbot.

Contains type definitions for strategy configuration:
- StrategyType: Enum of built-in strategy types
- EntryRule: Entry rule configuration
- ExitRule: Exit rule configuration
- StrategyDefinition: Complete strategy definition
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from .config import TrailingMode
from .models import StrategyProfile

if TYPE_CHECKING:
    from .models import RegimeState


class StrategyType(str, Enum):
    """Built-in strategy types."""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    MOMENTUM = "momentum"
    SCALPING = "scalping"


class EntryRule(BaseModel):
    """Entry rule configuration."""
    name: str
    description: str
    weight: float = Field(default=1.0, ge=0.0, le=2.0)
    enabled: bool = True

    # Indicator thresholds
    indicator: str | None = None
    condition: str | None = None  # "above", "below", "crosses_above", "crosses_below"
    threshold: float | None = None


class ExitRule(BaseModel):
    """Exit rule configuration."""
    name: str
    description: str
    priority: int = Field(default=1, ge=1, le=10)
    enabled: bool = True

    # Rule type
    rule_type: str  # "indicator", "time", "profit", "trailing"
    params: dict = Field(default_factory=dict)


class StrategyDefinition(BaseModel):
    """Complete strategy definition with rules."""
    profile: StrategyProfile
    strategy_type: StrategyType

    # Entry rules
    entry_rules: list[EntryRule] = Field(default_factory=list)
    min_entry_score: float = Field(default=0.6, ge=0.0, le=1.0)

    # Exit rules
    exit_rules: list[ExitRule] = Field(default_factory=list)

    # Trailing stop configuration
    trailing_mode: TrailingMode = TrailingMode.ATR
    trailing_params: dict = Field(default_factory=dict)

    # Risk parameters
    stop_loss_pct: float = Field(default=2.0, gt=0, le=10)
    position_size_pct: float = Field(default=2.0, gt=0, le=100)

    def is_applicable(self, regime: "RegimeState") -> bool:
        """Check if strategy is applicable for current regime."""
        return self.profile.is_applicable(regime)
