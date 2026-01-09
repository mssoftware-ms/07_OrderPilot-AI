"""Strategy Config - Dataclasses and Type Definitions.

Refactored from strategy_config.py monolith.

Module 1/4 of strategy_config.py split.

Contains:
- TimeframeConfig: Single timeframe configuration
- IndicatorConfig: Indicator parameters
- ConditionRule: Single entry condition rule
- EntryConditions: Entry conditions for long/short
- ExitConfig: Exit strategy configuration
- RiskConfig: Risk management parameters
- AIValidationConfig: AI validation settings
- FilterConfig: Market filters
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class TimeframeConfig:
    """Konfiguration für einen Timeframe."""

    interval: str
    source: Literal["alpaca", "bitunix"]
    lookback_bars: int
    update_interval_minutes: int
    purpose: str


@dataclass
class IndicatorConfig:
    """Konfiguration für einen Indikator."""

    enabled: bool
    params: dict[str, Any]


@dataclass
class ConditionRule:
    """Regel für eine Bedingung."""

    id: str
    name: str
    condition_type: str
    enabled: bool
    weight: int
    rule: dict[str, Any]
    description: str


@dataclass
class EntryConditions:
    """Entry-Bedingungen für eine Richtung."""

    min_confluence: int
    max_confluence: int
    conditions: list[ConditionRule]

    def get_enabled_conditions(self) -> list[ConditionRule]:
        """Gibt nur aktivierte Bedingungen zurück."""
        return [c for c in self.conditions if c.enabled]


@dataclass
class ExitConfig:
    """Exit-Konfiguration."""

    stop_loss: dict[str, Any]
    take_profit: dict[str, Any]
    trailing_stop: dict[str, Any]
    signal_reversal: dict[str, Any]
    rsi_extreme: dict[str, Any]
    session_end: dict[str, Any]


@dataclass
class RiskConfig:
    """Risiko-Konfiguration."""

    max_position_risk_percent: float
    max_daily_loss_percent: float
    max_position_size_btc: float
    leverage: int
    single_position_only: bool


@dataclass
class AIValidationConfig:
    """
    AI-Validation Konfiguration mit hierarchischer Validierung.

    WICHTIG: Provider und Model werden aus QSettings geladen!
             Einstellbar über: File -> Settings -> AI
             KEINE hardcodierten Modelle!
    """

    enabled: bool
    confidence_threshold: int  # Backwards compatibility
    confidence_threshold_trade: int  # >= Trade ausführen
    confidence_threshold_deep: int  # >= Deep Analysis
    deep_analysis_enabled: bool
    fallback_to_technical: bool
    timeout_seconds: int
    min_confluence_for_ai: int  # KOSTENOPTIMIERUNG: AI nur bei starken Signalen


@dataclass
class FilterConfig:
    """Filter-Konfiguration."""

    volume: dict[str, Any]
    spread: dict[str, Any]
    volatility: dict[str, Any]
