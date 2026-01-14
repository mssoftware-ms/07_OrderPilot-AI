"""
Backtesting Configuration - Entry score configs and triggers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .enums import WeightPresetName, DirectionBias
from .optimizable import OptimizableFloat, OptimizableInt, WeightPreset
from .indicators import IndicatorParams

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

