"""
Backtesting JSON Schema Models.

Based on '01_Projectplan/Strategien_Workflow_json/json Format Strategien Indikatoren.md'.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

# --- Enums & Literals ---
OpType = Literal["gt", "lt", "eq", "between"]
RegimeScope = Literal["entry", "exit", "in_trade"]
TrailingMode = Literal["percent", "atr"]

# --- Condition Definitions ---
class ConditionLeftRight(BaseModel):
    indicator_id: Optional[str] = None
    field: Optional[str] = None
    value: Optional[float] = None
    min: Optional[float] = None # For 'between'
    max: Optional[float] = None # For 'between'

class Condition(BaseModel):
    left: ConditionLeftRight
    op: OpType
    right: ConditionLeftRight

class ConditionGroup(BaseModel):
    all: Optional[List[Condition]] = None
    any: Optional[List[Condition]] = None

# --- Main Components ---

class Metadata(BaseModel):
    author: Optional[str] = None
    created_at: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    dataset_id: Optional[str] = None

class IndicatorDef(BaseModel):
    id: str
    type: str
    params: Dict[str, Any]
    timeframe: Optional[str] = None

class RegimeDef(BaseModel):
    id: str
    name: str
    conditions: ConditionGroup
    priority: Optional[float] = None
    scope: Optional[RegimeScope] = None

class RiskSettings(BaseModel):
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    trailing_mode: Optional[TrailingMode] = None
    trailing_multiplier: Optional[float] = None
    risk_per_trade_pct: Optional[float] = None

class StrategyDef(BaseModel):
    id: str
    name: str
    entry: Optional[ConditionGroup] = None
    exit: Optional[ConditionGroup] = None
    risk: Optional[RiskSettings] = None

class StrategyOverride(BaseModel):
    entry: Optional[ConditionGroup] = None
    exit: Optional[ConditionGroup] = None
    risk: Optional[RiskSettings] = None

class StrategyRef(BaseModel):
    strategy_id: str
    strategy_overrides: Optional[StrategyOverride] = None

class IndicatorOverride(BaseModel):
    indicator_id: str
    params: Dict[str, Any]

class StrategySet(BaseModel):
    id: str
    name: str
    strategies: List[StrategyRef]
    indicator_overrides: Optional[List[IndicatorOverride]] = None

class RoutingMatch(BaseModel):
    all_of: Optional[List[str]] = None
    any_of: Optional[List[str]] = None
    none_of: Optional[List[str]] = None

class RoutingRule(BaseModel):
    strategy_set_id: str
    match: RoutingMatch

class TradingBotConfig(BaseModel):
    schema_version: str
    metadata: Optional[Metadata] = None
    indicators: List[IndicatorDef]
    regimes: List[RegimeDef]
    strategies: List[StrategyDef]
    strategy_sets: List[StrategySet]
    routing: List[RoutingRule]
