"""Backtesting Configuration V2 - Entry Configuration

Entry-related configuration classes:
- Weight presets for entry scoring
- Meta information (name, description, timestamps)
- Strategy profile (type, preset, direction bias)
- Entry score configuration (weights, thresholds, gates)
- Entry triggers (breakout, pullback, SFP)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import (
    AssetClass,
    DirectionBias,
    OptimizableFloat,
    ScenarioType,
    StrategyType,
    WeightPresetName,
)


# ==================== WEIGHT PRESETS ====================

@dataclass
class WeightPreset:
    """Vordefinierte Weight-Kombination."""
    trend: float = 0.25
    rsi: float = 0.15
    macd: float = 0.20
    adx: float = 0.15
    vol: float = 0.10
    volume: float = 0.15

    def to_dict(self) -> Dict[str, float]:
        return {
            "trend": self.trend,
            "rsi": self.rsi,
            "macd": self.macd,
            "adx": self.adx,
            "vol": self.vol,
            "volume": self.volume
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "WeightPreset":
        return cls(
            trend=data.get("trend", 0.25),
            rsi=data.get("rsi", 0.15),
            macd=data.get("macd", 0.20),
            adx=data.get("adx", 0.15),
            vol=data.get("vol", 0.10),
            volume=data.get("volume", 0.15)
        )

    def validate(self) -> bool:
        """Prueft ob Weights zu 1.0 summieren."""
        total = self.trend + self.rsi + self.macd + self.adx + self.vol + self.volume
        return 0.99 <= total <= 1.01


# Default Weight Presets
DEFAULT_WEIGHT_PRESETS = {
    "W0": WeightPreset(trend=0.25, rsi=0.15, macd=0.20, adx=0.15, vol=0.10, volume=0.15),
    "W1": WeightPreset(trend=0.35, rsi=0.10, macd=0.15, adx=0.20, vol=0.10, volume=0.10),
    "W2": WeightPreset(trend=0.25, rsi=0.20, macd=0.20, adx=0.10, vol=0.15, volume=0.10),
}


# ==================== CONFIG SECTIONS ====================

@dataclass
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


@dataclass
class StrategyProfileSection:
    """Strategie-Profil-Konfiguration."""
    type: StrategyType = StrategyType.TRENDFOLLOWING
    preset: WeightPresetName = WeightPresetName.W0
    direction_bias: DirectionBias = DirectionBias.BOTH

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "preset": self.preset.value,
            "direction_bias": self.direction_bias.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyProfileSection":
        return cls(
            type=StrategyType(data.get("type", "trendfollowing")),
            preset=WeightPresetName(data.get("preset", "W0")),
            direction_bias=DirectionBias(data.get("direction_bias", "BOTH"))
        )


@dataclass
class EntryScoreGates:
    """Gate-Einstellungen fuer Entry Score."""
    block_in_chop: bool = True
    block_against_strong_trend: bool = True
    allow_counter_trend_sfp: bool = False

    def to_dict(self) -> Dict[str, bool]:
        return {
            "block_in_chop": self.block_in_chop,
            "block_against_strong_trend": self.block_against_strong_trend,
            "allow_counter_trend_sfp": self.allow_counter_trend_sfp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntryScoreGates":
        return cls(
            block_in_chop=data.get("block_in_chop", True),
            block_against_strong_trend=data.get("block_against_strong_trend", True),
            allow_counter_trend_sfp=data.get("allow_counter_trend_sfp", False)
        )


@dataclass
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


@dataclass
class EntryScoreSection:
    """Entry Score Konfiguration."""
    use_preset: Optional[WeightPresetName] = WeightPresetName.W0
    custom_weights: Optional[Dict[str, OptimizableFloat]] = None
    weight_presets: Dict[str, WeightPreset] = field(default_factory=lambda: DEFAULT_WEIGHT_PRESETS.copy())
    min_score_for_entry: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.60))
    threshold_excellent: float = 0.80
    threshold_good: float = 0.65
    threshold_moderate: float = 0.50
    threshold_weak: float = 0.35
    gates: EntryScoreGates = field(default_factory=EntryScoreGates)
    indicator_params: IndicatorParams = field(default_factory=IndicatorParams)
    regime_boost_strong_trend: float = 0.10
    regime_penalty_chop: float = -0.15
    regime_penalty_volatile: float = -0.10

    def get_weights(self) -> WeightPreset:
        """Gibt die aktiven Weights zurueck."""
        if self.use_preset and self.use_preset != WeightPresetName.CUSTOM:
            return self.weight_presets.get(self.use_preset.value, DEFAULT_WEIGHT_PRESETS["W0"])
        # TODO: Custom weights implementieren
        return DEFAULT_WEIGHT_PRESETS["W0"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": {
                "use_preset": self.use_preset.value if self.use_preset else None,
                "custom": None  # TODO: Custom weights
            },
            "weight_presets": {k: v.to_dict() for k, v in self.weight_presets.items()},
            "thresholds": {
                "min_score_for_entry": self.min_score_for_entry.to_dict(),
                "excellent": self.threshold_excellent,
                "good": self.threshold_good,
                "moderate": self.threshold_moderate,
                "weak": self.threshold_weak
            },
            "gates": self.gates.to_dict(),
            "indicator_params": self.indicator_params.to_dict(),
            "regime_modifiers": {
                "boost_strong_trend": self.regime_boost_strong_trend,
                "penalty_chop": self.regime_penalty_chop,
                "penalty_volatile": self.regime_penalty_volatile
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntryScoreSection":
        weights = data.get("weights", {})
        thresholds = data.get("thresholds", {})
        regime_mod = data.get("regime_modifiers", {})

        use_preset = None
        if weights.get("use_preset"):
            use_preset = WeightPresetName(weights["use_preset"])

        return cls(
            use_preset=use_preset,
            min_score_for_entry=OptimizableFloat.from_dict(
                thresholds.get("min_score_for_entry", {"value": 0.60})
            ),
            threshold_excellent=thresholds.get("excellent", 0.80),
            threshold_good=thresholds.get("good", 0.65),
            threshold_moderate=thresholds.get("moderate", 0.50),
            threshold_weak=thresholds.get("weak", 0.35),
            gates=EntryScoreGates.from_dict(data.get("gates", {})),
            indicator_params=IndicatorParams.from_dict(data.get("indicator_params", {})),
            regime_boost_strong_trend=regime_mod.get("boost_strong_trend", 0.10),
            regime_penalty_chop=regime_mod.get("penalty_chop", -0.15),
            regime_penalty_volatile=regime_mod.get("penalty_volatile", -0.10)
        )


# ==================== ENTRY TRIGGERS ====================

@dataclass
class BreakoutTrigger:
    """Breakout Trigger Konfiguration."""
    enabled: bool = True
    volume_multiplier: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=1.5))
    close_threshold: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.4))
    confirmation_candles: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "volume_multiplier": self.volume_multiplier.to_dict(),
            "close_threshold": self.close_threshold.to_dict(),
            "confirmation_candles": self.confirmation_candles
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BreakoutTrigger":
        return cls(
            enabled=data.get("enabled", True),
            volume_multiplier=OptimizableFloat.from_dict(data.get("volume_multiplier", {"value": 1.5})),
            close_threshold=OptimizableFloat.from_dict(data.get("close_threshold", {"value": 0.4})),
            confirmation_candles=data.get("confirmation_candles", 1)
        )


@dataclass
class PullbackTrigger:
    """Pullback Trigger Konfiguration."""
    enabled: bool = True
    max_distance_atr: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=1.2))
    min_strength: float = 0.3
    patience_candles: int = 5
    rejection_wick_pct: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.3))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_distance_atr": self.max_distance_atr.to_dict(),
            "min_strength": self.min_strength,
            "patience_candles": self.patience_candles,
            "rejection_wick_pct": self.rejection_wick_pct.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PullbackTrigger":
        return cls(
            enabled=data.get("enabled", True),
            max_distance_atr=OptimizableFloat.from_dict(data.get("max_distance_atr", {"value": 1.2})),
            min_strength=data.get("min_strength", 0.3),
            patience_candles=data.get("patience_candles", 5),
            rejection_wick_pct=OptimizableFloat.from_dict(data.get("rejection_wick_pct", {"value": 0.3}))
        )


@dataclass
class SfpTrigger:
    """SFP (Swing Failure Pattern) Trigger Konfiguration."""
    enabled: bool = False
    wick_body_ratio: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=2.0))
    penetration_pct: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.3))
    quick_reversal_candles: int = 2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "wick_body_ratio": self.wick_body_ratio.to_dict(),
            "penetration_pct": self.penetration_pct.to_dict(),
            "quick_reversal_candles": self.quick_reversal_candles
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SfpTrigger":
        return cls(
            enabled=data.get("enabled", False),
            wick_body_ratio=OptimizableFloat.from_dict(data.get("wick_body_ratio", {"value": 2.0})),
            penetration_pct=OptimizableFloat.from_dict(data.get("penetration_pct", {"value": 0.3})),
            quick_reversal_candles=data.get("quick_reversal_candles", 2)
        )


@dataclass
class EntryTriggersSection:
    """Entry Triggers Konfiguration."""
    breakout: BreakoutTrigger = field(default_factory=BreakoutTrigger)
    pullback: PullbackTrigger = field(default_factory=PullbackTrigger)
    sfp: SfpTrigger = field(default_factory=SfpTrigger)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "breakout": self.breakout.to_dict(),
            "pullback": self.pullback.to_dict(),
            "sfp": self.sfp.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntryTriggersSection":
        return cls(
            breakout=BreakoutTrigger.from_dict(data.get("breakout", {})),
            pullback=PullbackTrigger.from_dict(data.get("pullback", {})),
            sfp=SfpTrigger.from_dict(data.get("sfp", {}))
        )
