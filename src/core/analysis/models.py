"""Data models for the AI Analysis module.

Defines structures for:
- Parsing initial analysis results (from Tab 0)
- Configuration of strategies and timeframes
- Payloads for deep analysis runs
"""

import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class InitialAnalysisResult(BaseModel):
    """Represents the JSON output from the initial analysis (Tab 0)."""
    setup_detected: bool
    setup_type: str
    confidence_score: int
    reasoning: str
    invalidation_level: Optional[float] = None
    notes: List[str] = Field(default_factory=list)

    def extract_regime(self) -> str:
        """Extracts the market regime from the reasoning string.

        Looks for pattern: [#REGIME:; <REGIME_NAME>]
        Returns:
            Extracted regime string (e.g., "NEUTRAL", "TREND_BULL") or "UNKNOWN".
        """
        # Regex to find [#REGIME:; VALUE] or [#REGIME; VALUE]
        # Handles optional colon and varying whitespace
        match = re.search(r"\[#REGIME[:;]*\s*([A-Z_]+)\]", self.reasoning)
        if match:
            return match.group(1).strip()
        return "UNKNOWN"

    def extract_metric(self, key: str) -> Optional[float]:
        """Extracts a specific numerical metric from reasoning tags.

        Args:
            key: The tag name, e.g., "RSI", "PRICE", "BB_PCT_B".

        Returns:
            The float value if found, else None.
        """
        # Regex for [#KEY; VALUE]
        pattern = re.compile(rf"\[#{re.escape(key)}[:;]*\s*([-\d\.]+)\]")
        match = pattern.search(self.reasoning)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None


# --- Configuration Models ---

class TimeframeConfig(BaseModel):
    """Configuration for a single timeframe in the analysis."""
    role: Literal["EXECUTION", "CONTEXT", "TREND", "MACRO"]
    tf: str  # e.g., "1m", "15m", "4h", "1D"
    lookback: int = Field(..., description="Number of bars to load")
    provider: str = Field(default="CACHE", description="Data source: CACHE, API, DB")
    warmup_bars: int = Field(default=200, description="Additional bars for indicator warmup")


class IndicatorSpec(BaseModel):
    """Specification for a single indicator."""
    name: str  # e.g. "RSI", "EMA"
    params: Dict[str, Any] = Field(default_factory=dict)
    feature_flags: Dict[str, bool] = Field(default_factory=dict) # e.g. {"state": True}


class IndicatorPreset(BaseModel):
    """A named collection of indicators."""
    preset_id: str
    name: str
    indicators: List[IndicatorSpec]


class AnalysisStrategyConfig(BaseModel):
    """Configuration for a trading strategy analysis."""
    name: str  # "Scalping", "Daytrading", "Swingtrading"
    allowed_regimes: List[str]  # e.g., ["TREND_BULL", "TREND_BEAR"]
    timeframes: List[TimeframeConfig]
    indicator_preset_id: str
    description: str = ""


# --- Deep Analysis Payload Models ---

class DeepAnalysisPayload(BaseModel):
    """Payload sent to the LLM for the deep analysis run."""
    symbol: str
    timestamp_utc: str
    
    # Context from Tab 0
    initial_regime: str
    initial_analysis_summary: str
    
    # Configuration used
    strategy: str
    
    # Extracted Features per Timeframe
    # Structure: { "4h": { "trend": "bullish", "rsi": 60.5, ... }, "1D": ... }
    multi_tf_features: Dict[str, Dict[str, Any]]
    
    # Key Levels found across timeframes
    key_levels: Dict[str, List[float]]
