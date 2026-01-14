"""
Backtesting Configuration - Indicator parameters and meta sections
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .enums import StrategyType, AssetClass
from .optimizable import OptimizableFloat, OptimizableInt

class MetaSection:
    """Meta-Informationen zur Konfiguration."""
    name: str
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: str = "OrderPilot-AI"
    tags: List[str] = field(default_factory=list)
    target_asset_class: AssetClass = AssetClass.CRYPTO
    target_timeframe: str = "5m"
    scenario_type: ScenarioType = ScenarioType.BALANCED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "author": self.author,
            "tags": self.tags,
            "target_asset_class": self.target_asset_class.value,
            "target_timeframe": self.target_timeframe,
            "scenario_type": self.scenario_type.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetaSection":
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        return cls(
            name=data.get("name", "Unnamed"),
            description=data.get("description", ""),
            created_at=created_at,
            author=data.get("author", "OrderPilot-AI"),
            tags=data.get("tags", []),
            target_asset_class=AssetClass(data.get("target_asset_class", "crypto")),
            target_timeframe=data.get("target_timeframe", "5m"),
            scenario_type=ScenarioType(data.get("scenario_type", "balanced"))
        )

class IndicatorParams:
    """Indikator-Parameter."""
    ema_short: int = 20
    ema_medium: int = 50
    ema_long: int = 200
    rsi_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    adx_period: int = 14
    adx_strong_trend: float = 25.0
    adx_weak_trend: float = 15.0
    atr_period: int = 14

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ema_short": self.ema_short,
            "ema_medium": self.ema_medium,
            "ema_long": self.ema_long,
            "rsi_period": self.rsi_period,
            "rsi_overbought": self.rsi_overbought,
            "rsi_oversold": self.rsi_oversold,
            "adx_period": self.adx_period,
            "adx_strong_trend": self.adx_strong_trend,
            "adx_weak_trend": self.adx_weak_trend,
            "atr_period": self.atr_period
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IndicatorParams":
        return cls(
            ema_short=data.get("ema_short", 20),
            ema_medium=data.get("ema_medium", 50),
            ema_long=data.get("ema_long", 200),
            rsi_period=data.get("rsi_period", 14),
            rsi_overbought=data.get("rsi_overbought", 70),
            rsi_oversold=data.get("rsi_oversold", 30),
            adx_period=data.get("adx_period", 14),
            adx_strong_trend=data.get("adx_strong_trend", 25.0),
            adx_weak_trend=data.get("adx_weak_trend", 15.0),
            atr_period=data.get("atr_period", 14)
        )

