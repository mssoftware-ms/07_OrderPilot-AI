from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MarketRegime(str, Enum):
    STRONG_TREND_BULL = "STRONG_TREND_BULL"
    STRONG_TREND_BEAR = "STRONG_TREND_BEAR"
    CHOP_RANGE = "CHOP_RANGE"
    VOLATILITY_EXPLOSIVE = "VOLATILITY_EXPLOSIVE"
    NEUTRAL = "NEUTRAL"

class RSIState(str, Enum):
    OVERBOUGHT = "OVERBOUGHT"
    OVERSOLD = "OVERSOLD"
    NEUTRAL = "NEUTRAL"

class TechnicalFeatures(BaseModel):
    """Core technical indicators passed to the AI."""
    rsi_value: float
    rsi_state: RSIState
    ema_20_dist_pct: float
    ema_200_dist_pct: float
    bb_pct_b: float
    bb_width: float
    atr_14: float
    adx_14: float
    volume_z_score: Optional[float] = None

class MarketStructure(BaseModel):
    """Simplified structure data (Pivots)."""
    recent_highs: List[float] = Field(default_factory=list)
    recent_lows: List[float] = Field(default_factory=list)
    current_price: float

class AIAnalysisInput(BaseModel):
    """The full context payload sent to the LLM."""
    symbol: str
    timeframe: str
    timestamp: str  # ISO string
    regime: MarketRegime
    technicals: TechnicalFeatures
    structure: MarketStructure
    last_candles_summary: List[Dict[str, Any]] = Field(
        description="Simplified list of last N candles: {'time', 'open', 'high', 'low', 'close', 'vol'}"
    )
    # Optional Bitunix/Advanced data
    funding_rate: Optional[float] = None
    open_interest_change_pct: Optional[float] = None

class SetupType(str, Enum):
    PULLBACK_EMA20 = "PULLBACK_EMA20"
    BREAKOUT = "BREAKOUT"
    MEAN_REVERSION = "MEAN_REVERSION"
    SFP_SWING_FAILURE = "SFP_SWING_FAILURE"
    ABSORPTION = "ABSORPTION"
    NO_SETUP = "NO_SETUP"

class AIAnalysisOutput(BaseModel):
    """The structured decision returned by the LLM."""
    setup_detected: bool
    setup_type: SetupType
    confidence_score: int = Field(ge=0, le=100)
    reasoning: str
    invalidation_level: Optional[float] = None
    notes: List[str] = Field(default_factory=list)
