"""
Backtesting Configuration V2 - Dataclasses und Types

Einheitliches Konfigurationsformat fuer Backtesting mit:
- Optimierbare Parameter (OptimizableFloat, OptimizableInt)
- Strategie-Profile (Trendfollowing, Scalping, etc.)
- Entry Score mit Weight-Presets
- Exit Management (SL/TP, Trailing, Partial TP)
- Risk/Leverage Management
- Walk-Forward Analyse
- Parameter-Gruppen und Conditionals
- Vererbung/Extends Support

Basiert auf den Anforderungen aus:
- docs: Claude, GPT, Gemini Ausarbeitungen
- Online-Recherche: Freqtrade, Backtesting.py Best Practices
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# ENUMS
class StrategyType(str, Enum):
    """Strategie-Typen."""
    TRENDFOLLOWING = "trendfollowing"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    HYBRID = "hybrid"


class WeightPresetName(str, Enum):
    """Vordefinierte Weight-Presets."""
    W0 = "W0"  # Default/Balanced
    W1 = "W1"  # Trend/ADX-heavy
    W2 = "W2"  # Momentum/Volatility-heavy
    CUSTOM = "custom"


class DirectionBias(str, Enum):
    """Handelsrichtungs-Bias."""
    BOTH = "BOTH"
    LONG_ONLY = "LONG_ONLY"
    SHORT_ONLY = "SHORT_ONLY"


class ScenarioType(str, Enum):
    """Szenario-Typ."""
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"


class AssetClass(str, Enum):
    """Asset-Klassen."""
    CRYPTO = "crypto"
    STOCKS = "stocks"
    FOREX = "forex"
    FUTURES = "futures"


class StopLossType(str, Enum):
    """Stop-Loss Typen."""
    ATR_BASED = "atr_based"
    PERCENT_BASED = "percent_based"
    STRUCTURE_BASED = "structure_based"


class TakeProfitType(str, Enum):
    """Take-Profit Typen."""
    ATR_BASED = "atr_based"
    PERCENT_BASED = "percent_based"
    RR_RATIO = "rr_ratio"
    LEVEL_BASED = "level_based"


class TrailingType(str, Enum):
    """Trailing Stop Typen."""
    ATR_BASED = "atr_based"
    PERCENT_BASED = "percent_based"


class SlippageMethod(str, Enum):
    """Slippage-Berechnungsmethoden."""
    FIXED_BPS = "fixed_bps"
    ATR_BASED = "atr_based"
    VOLUME_ADJUSTED = "volume_adjusted"


class OptimizationMethod(str, Enum):
    """Optimierungsmethoden."""
    GRID = "grid"
    RANDOM = "random"
    BAYESIAN = "bayesian"


class TargetMetric(str, Enum):
    """Ziel-Metriken fuer Optimierung."""
    EXPECTANCY = "expectancy"
    PROFIT_FACTOR = "profit_factor"
    SHARPE = "sharpe"
    SORTINO = "sortino"
    CALMAR = "calmar"
    MAX_DD = "max_dd"


# OPTIMIZABLE TYPES
@dataclass
class OptimizableFloat:
    """Float-Parameter der optimiert werden kann."""
    value: float
    optimize: bool = False
    range: Optional[List[float]] = None  # Diskrete Werte
    min: Optional[float] = None          # Kontinuierlicher Bereich
    max: Optional[float] = None
    step: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {"value": self.value, "optimize": self.optimize}
        if self.range:
            result["range"] = self.range
        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max
        if self.step is not None:
            result["step"] = self.step
        return result

    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], float]) -> "OptimizableFloat":
        if isinstance(data, (int, float)):
            return cls(value=float(data))
        return cls(
            value=data.get("value", 0.0),
            optimize=data.get("optimize", False),
            range=data.get("range"),
            min=data.get("min"),
            max=data.get("max"),
            step=data.get("step")
        )

    def get_search_space(self) -> List[float]:
        """Gibt den Suchraum fuer Optimierung zurueck."""
        if not self.optimize:
            return [self.value]
        if self.range:
            return self.range
        if self.min is not None and self.max is not None:
            step = self.step or (self.max - self.min) / 10
            values = []
            v = self.min
            while v <= self.max:
                values.append(round(v, 6))
                v += step
            return values
        return [self.value]


@dataclass
class OptimizableInt:
    """Integer-Parameter der optimiert werden kann."""
    value: int
    optimize: bool = False
    range: Optional[List[int]] = None
    min: Optional[int] = None
    max: Optional[int] = None
    step: int = 1

    def to_dict(self) -> Dict[str, Any]:
        result = {"value": self.value, "optimize": self.optimize}
        if self.range:
            result["range"] = self.range
        if self.min is not None:
            result["min"] = self.min
        if self.max is not None:
            result["max"] = self.max
        if self.step != 1:
            result["step"] = self.step
        return result

    @classmethod
    def from_dict(cls, data: Union[Dict[str, Any], int]) -> "OptimizableInt":
        if isinstance(data, int):
            return cls(value=data)
        return cls(
            value=data.get("value", 0),
            optimize=data.get("optimize", False),
            range=data.get("range"),
            min=data.get("min"),
            max=data.get("max"),
            step=data.get("step", 1)
        )

    def get_search_space(self) -> List[int]:
        """Gibt den Suchraum fuer Optimierung zurueck."""
        if not self.optimize:
            return [self.value]
        if self.range:
            return self.range
        if self.min is not None and self.max is not None:
            return list(range(self.min, self.max + 1, self.step))
        return [self.value]


# WEIGHT PRESETS
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


# CONFIG SECTIONS
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


@dataclass
class StopLossConfig:
    """Stop-Loss Konfiguration."""
    type: StopLossType = StopLossType.ATR_BASED
    atr_multiplier: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=1.5))
    percent: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.5))
    structure_buffer_atr: float = 0.2

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "atr_multiplier": self.atr_multiplier.to_dict(),
            "percent": self.percent.to_dict(),
            "structure_buffer_atr": self.structure_buffer_atr
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StopLossConfig":
        return cls(
            type=StopLossType(data.get("type", "atr_based")),
            atr_multiplier=OptimizableFloat.from_dict(data.get("atr_multiplier", {"value": 1.5})),
            percent=OptimizableFloat.from_dict(data.get("percent", {"value": 0.5})),
            structure_buffer_atr=data.get("structure_buffer_atr", 0.2)
        )


@dataclass
class TakeProfitConfig:
    """Take-Profit Konfiguration."""
    type: TakeProfitType = TakeProfitType.ATR_BASED
    atr_multiplier: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=2.0))
    percent: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=1.5))
    rr_ratio: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=2.0))
    use_level: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "atr_multiplier": self.atr_multiplier.to_dict(),
            "percent": self.percent.to_dict(),
            "rr_ratio": self.rr_ratio.to_dict(),
            "use_level": self.use_level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TakeProfitConfig":
        return cls(
            type=TakeProfitType(data.get("type", "atr_based")),
            atr_multiplier=OptimizableFloat.from_dict(data.get("atr_multiplier", {"value": 2.0})),
            percent=OptimizableFloat.from_dict(data.get("percent", {"value": 1.5})),
            rr_ratio=OptimizableFloat.from_dict(data.get("rr_ratio", {"value": 2.0})),
            use_level=data.get("use_level", False)
        )


@dataclass
class TrailingStopConfig:
    """Trailing Stop Konfiguration."""
    enabled: bool = True
    type: TrailingType = TrailingType.ATR_BASED
    move_to_breakeven: bool = True
    activation_atr: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=1.0))
    activation_percent: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.5))
    distance_atr: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.6))
    distance_percent: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.3))
    step_percent: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=0.2))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "type": self.type.value,
            "move_to_breakeven": self.move_to_breakeven,
            "activation_atr": self.activation_atr.to_dict(),
            "activation_percent": self.activation_percent.to_dict(),
            "distance_atr": self.distance_atr.to_dict(),
            "distance_percent": self.distance_percent.to_dict(),
            "step_percent": self.step_percent.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrailingStopConfig":
        return cls(
            enabled=data.get("enabled", True),
            type=TrailingType(data.get("type", "atr_based")),
            move_to_breakeven=data.get("move_to_breakeven", True),
            activation_atr=OptimizableFloat.from_dict(data.get("activation_atr", {"value": 1.0})),
            activation_percent=OptimizableFloat.from_dict(data.get("activation_percent", {"value": 0.5})),
            distance_atr=OptimizableFloat.from_dict(data.get("distance_atr", {"value": 0.6})),
            distance_percent=OptimizableFloat.from_dict(data.get("distance_percent", {"value": 0.3})),
            step_percent=OptimizableFloat.from_dict(data.get("step_percent", {"value": 0.2}))
        )


@dataclass
class PartialTPConfig:
    """Partial Take-Profit Konfiguration."""
    enabled: bool = False
    tp1_percent: float = 50.0
    tp1_rr: float = 1.0
    move_sl_to_be: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "tp1_percent": self.tp1_percent,
            "tp1_rr": self.tp1_rr,
            "move_sl_to_be": self.move_sl_to_be
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PartialTPConfig":
        return cls(
            enabled=data.get("enabled", False),
            tp1_percent=data.get("tp1_percent", 50.0),
            tp1_rr=data.get("tp1_rr", 1.0),
            move_sl_to_be=data.get("move_sl_to_be", True)
        )


@dataclass
class TimeStopConfig:
    """Time Stop Konfiguration."""
    enabled: bool = False
    max_holding_minutes: int = 480

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "max_holding_minutes": self.max_holding_minutes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeStopConfig":
        return cls(
            enabled=data.get("enabled", False),
            max_holding_minutes=data.get("max_holding_minutes", 480)
        )


@dataclass
class ExitManagementSection:
    """Exit Management Konfiguration."""
    stop_loss: StopLossConfig = field(default_factory=StopLossConfig)
    take_profit: TakeProfitConfig = field(default_factory=TakeProfitConfig)
    trailing_stop: TrailingStopConfig = field(default_factory=TrailingStopConfig)
    partial_tp: PartialTPConfig = field(default_factory=PartialTPConfig)
    time_stop: TimeStopConfig = field(default_factory=TimeStopConfig)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stop_loss": self.stop_loss.to_dict(),
            "take_profit": self.take_profit.to_dict(),
            "trailing_stop": self.trailing_stop.to_dict(),
            "partial_tp": self.partial_tp.to_dict(),
            "time_stop": self.time_stop.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExitManagementSection":
        return cls(
            stop_loss=StopLossConfig.from_dict(data.get("stop_loss", {})),
            take_profit=TakeProfitConfig.from_dict(data.get("take_profit", {})),
            trailing_stop=TrailingStopConfig.from_dict(data.get("trailing_stop", {})),
            partial_tp=PartialTPConfig.from_dict(data.get("partial_tp", {})),
            time_stop=TimeStopConfig.from_dict(data.get("time_stop", {}))
        )


@dataclass
class RiskLeverageSection:
    """Risk & Leverage Konfiguration."""
    risk_per_trade_pct: OptimizableFloat = field(default_factory=lambda: OptimizableFloat(value=1.0))
    base_leverage: OptimizableInt = field(default_factory=lambda: OptimizableInt(value=5))
    max_leverage: int = 20
    min_liquidation_distance_pct: float = 5.0
    max_daily_loss_pct: float = 3.0
    max_trades_per_day: int = 10
    max_concurrent_positions: int = 1
    max_loss_streak: int = 3
    cooldown_after_streak_min: int = 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_per_trade_pct": self.risk_per_trade_pct.to_dict(),
            "base_leverage": self.base_leverage.to_dict(),
            "max_leverage": self.max_leverage,
            "min_liquidation_distance_pct": self.min_liquidation_distance_pct,
            "max_daily_loss_pct": self.max_daily_loss_pct,
            "max_trades_per_day": self.max_trades_per_day,
            "max_concurrent_positions": self.max_concurrent_positions,
            "max_loss_streak": self.max_loss_streak,
            "cooldown_after_streak_min": self.cooldown_after_streak_min
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskLeverageSection":
        return cls(
            risk_per_trade_pct=OptimizableFloat.from_dict(data.get("risk_per_trade_pct", {"value": 1.0})),
            base_leverage=OptimizableInt.from_dict(data.get("base_leverage", {"value": 5})),
            max_leverage=data.get("max_leverage", 20),
            min_liquidation_distance_pct=data.get("min_liquidation_distance_pct", 5.0),
            max_daily_loss_pct=data.get("max_daily_loss_pct", 3.0),
            max_trades_per_day=data.get("max_trades_per_day", 10),
            max_concurrent_positions=data.get("max_concurrent_positions", 1),
            max_loss_streak=data.get("max_loss_streak", 3),
            cooldown_after_streak_min=data.get("cooldown_after_streak_min", 60)
        )


@dataclass
class ExecutionSimulationSection:
    """Execution Simulation Konfiguration."""
    initial_capital: float = 10000.0
    symbol: str = "BTCUSDT"
    base_timeframe: str = "1m"
    mtf_timeframes: List[str] = field(default_factory=lambda: ["5m", "15m", "1h", "4h", "1D"])
    fee_maker_pct: float = 0.02
    fee_taker_pct: float = 0.06
    assume_taker: bool = True
    slippage_method: SlippageMethod = SlippageMethod.FIXED_BPS
    slippage_bps: float = 5.0
    slippage_atr_mult: float = 0.1
    funding_rate_8h: float = 0.01

    def to_dict(self) -> Dict[str, Any]:
        return {
            "initial_capital": self.initial_capital,
            "symbol": self.symbol,
            "base_timeframe": self.base_timeframe,
            "mtf_timeframes": self.mtf_timeframes,
            "fee_maker_pct": self.fee_maker_pct,
            "fee_taker_pct": self.fee_taker_pct,
            "assume_taker": self.assume_taker,
            "slippage_method": self.slippage_method.value,
            "slippage_bps": self.slippage_bps,
            "slippage_atr_mult": self.slippage_atr_mult,
            "funding_rate_8h": self.funding_rate_8h
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionSimulationSection":
        return cls(
            initial_capital=data.get("initial_capital", 10000.0),
            symbol=data.get("symbol", "BTCUSDT"),
            base_timeframe=data.get("base_timeframe", "1m"),
            mtf_timeframes=data.get("mtf_timeframes", ["5m", "15m", "1h", "4h", "1D"]),
            fee_maker_pct=data.get("fee_maker_pct", 0.02),
            fee_taker_pct=data.get("fee_taker_pct", 0.06),
            assume_taker=data.get("assume_taker", True),
            slippage_method=SlippageMethod(data.get("slippage_method", "fixed_bps")),
            slippage_bps=data.get("slippage_bps", 5.0),
            slippage_atr_mult=data.get("slippage_atr_mult", 0.1),
            funding_rate_8h=data.get("funding_rate_8h", 0.01)
        )


@dataclass
class OptimizationSection:
    """Optimierungs-Konfiguration."""
    method: OptimizationMethod = OptimizationMethod.RANDOM
    max_iterations: int = 300
    n_jobs: int = 1
    seed: int = 42
    target_metric: TargetMetric = TargetMetric.EXPECTANCY
    minimize: bool = False
    early_stopping_enabled: bool = False
    early_stopping_patience: int = 50
    early_stopping_min_improvement: float = 0.01
    parameter_space_override: Dict[str, List[Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method.value,
            "max_iterations": self.max_iterations,
            "n_jobs": self.n_jobs,
            "seed": self.seed,
            "target_metric": self.target_metric.value,
            "minimize": self.minimize,
            "early_stopping": {
                "enabled": self.early_stopping_enabled,
                "patience": self.early_stopping_patience,
                "min_improvement": self.early_stopping_min_improvement
            },
            "parameter_space_override": self.parameter_space_override
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OptimizationSection":
        early_stop = data.get("early_stopping", {})
        return cls(
            method=OptimizationMethod(data.get("method", "random")),
            max_iterations=data.get("max_iterations", 300),
            n_jobs=data.get("n_jobs", 1),
            seed=data.get("seed", 42),
            target_metric=TargetMetric(data.get("target_metric", "expectancy")),
            minimize=data.get("minimize", False),
            early_stopping_enabled=early_stop.get("enabled", False),
            early_stopping_patience=early_stop.get("patience", 50),
            early_stopping_min_improvement=early_stop.get("min_improvement", 0.01),
            parameter_space_override=data.get("parameter_space_override", {})
        )


@dataclass
class WalkForwardSection:
    """Walk-Forward Analyse Konfiguration."""
    enabled: bool = False
    train_window_days: int = 90
    test_window_days: int = 30
    step_size_days: int = 30
    min_folds: int = 4
    reoptimize_each_fold: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "train_window_days": self.train_window_days,
            "test_window_days": self.test_window_days,
            "step_size_days": self.step_size_days,
            "min_folds": self.min_folds,
            "reoptimize_each_fold": self.reoptimize_each_fold
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WalkForwardSection":
        return cls(
            enabled=data.get("enabled", False),
            train_window_days=data.get("train_window_days", 90),
            test_window_days=data.get("test_window_days", 30),
            step_size_days=data.get("step_size_days", 30),
            min_folds=data.get("min_folds", 4),
            reoptimize_each_fold=data.get("reoptimize_each_fold", True)
        )


@dataclass
class ParameterGroup:
    """Parameter-Gruppe fuer gemeinsames Testen."""
    name: str
    parameters: List[str]  # JSON-Pfade
    combinations: List[List[float]]
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "combinations": self.combinations
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParameterGroup":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            parameters=data.get("parameters", []),
            combinations=data.get("combinations", [])
        )


@dataclass
class Conditional:
    """Bedingte Parameter-Anpassung."""
    condition: Dict[str, Any]  # if-Bedingung
    actions: Dict[str, Any]    # then-Aktionen

    def to_dict(self) -> Dict[str, Any]:
        return {
            "if": self.condition,
            "then": self.actions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conditional":
        return cls(
            condition=data.get("if", {}),
            actions=data.get("then", {})
        )


@dataclass
class ConstraintsSection:
    """Constraints fuer Backtesting-Ergebnisse."""
    min_trades: int = 50
    max_drawdown_pct: float = 30.0
    min_win_rate: float = 0.40
    min_profit_factor: float = 1.2
    min_sharpe: Optional[float] = None
    min_sortino: Optional[float] = None
    max_consecutive_losses: Optional[int] = None
    weights_must_sum_to_one: bool = True

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "min_trades": self.min_trades,
            "max_drawdown_pct": self.max_drawdown_pct,
            "min_win_rate": self.min_win_rate,
            "min_profit_factor": self.min_profit_factor,
            "weights_must_sum_to_one": self.weights_must_sum_to_one
        }
        if self.min_sharpe is not None:
            result["min_sharpe"] = self.min_sharpe
        if self.min_sortino is not None:
            result["min_sortino"] = self.min_sortino
        if self.max_consecutive_losses is not None:
            result["max_consecutive_losses"] = self.max_consecutive_losses
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConstraintsSection":
        return cls(
            min_trades=data.get("min_trades", 50),
            max_drawdown_pct=data.get("max_drawdown_pct", 30.0),
            min_win_rate=data.get("min_win_rate", 0.40),
            min_profit_factor=data.get("min_profit_factor", 1.2),
            min_sharpe=data.get("min_sharpe"),
            min_sortino=data.get("min_sortino"),
            max_consecutive_losses=data.get("max_consecutive_losses"),
            weights_must_sum_to_one=data.get("weights_must_sum_to_one", True)
        )


# MAIN CONFIG CLASS
@dataclass
class BacktestConfigV2:
    """
    Einheitliche Backtesting-Konfiguration V2.

    Konsolidiert alle Parameter aus:
    - Entry Score (Weights, Gates, Thresholds)
    - Entry Triggers (Breakout, Pullback, SFP)
    - Exit Management (SL, TP, Trailing, Partial TP, Time Stop)
    - Risk/Leverage
    - Execution Simulation
    - Optimization
    - Walk-Forward
    - Parameter-Gruppen
    - Conditionals
    - Constraints
    """
    version: str = "2.0.0"
    extends: Optional[str] = None
    meta: MetaSection = field(default_factory=lambda: MetaSection(name="Unnamed Config"))
    strategy_profile: StrategyProfileSection = field(default_factory=StrategyProfileSection)
    entry_score: EntryScoreSection = field(default_factory=EntryScoreSection)
    entry_triggers: EntryTriggersSection = field(default_factory=EntryTriggersSection)
    exit_management: ExitManagementSection = field(default_factory=ExitManagementSection)
    risk_leverage: RiskLeverageSection = field(default_factory=RiskLeverageSection)
    execution_simulation: ExecutionSimulationSection = field(default_factory=ExecutionSimulationSection)
    optimization: OptimizationSection = field(default_factory=OptimizationSection)
    walk_forward: WalkForwardSection = field(default_factory=WalkForwardSection)
    parameter_groups: List[ParameterGroup] = field(default_factory=list)
    conditionals: List[Conditional] = field(default_factory=list)
    constraints: ConstraintsSection = field(default_factory=ConstraintsSection)
    overrides: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary (JSON-serialisierbar)."""
        result = {
            "$schema": "./schemas/backtest_config_v2.schema.json",
            "version": self.version,
            "meta": self.meta.to_dict(),
            "strategy_profile": self.strategy_profile.to_dict(),
            "entry_score": self.entry_score.to_dict(),
            "entry_triggers": self.entry_triggers.to_dict(),
            "exit_management": self.exit_management.to_dict(),
            "risk_leverage": self.risk_leverage.to_dict(),
            "execution_simulation": self.execution_simulation.to_dict(),
            "optimization": self.optimization.to_dict(),
            "walk_forward": self.walk_forward.to_dict(),
            "constraints": self.constraints.to_dict()
        }

        if self.extends:
            result["extends"] = self.extends
        if self.parameter_groups:
            result["parameter_groups"] = [pg.to_dict() for pg in self.parameter_groups]
        if self.conditionals:
            result["conditionals"] = [c.to_dict() for c in self.conditionals]
        if self.overrides:
            result["overrides"] = self.overrides

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BacktestConfigV2":
        """Erstellt aus Dictionary."""
        param_groups = [ParameterGroup.from_dict(pg) for pg in data.get("parameter_groups", [])]
        conditionals = [Conditional.from_dict(c) for c in data.get("conditionals", [])]

        return cls(
            version=data.get("version", "2.0.0"),
            extends=data.get("extends"),
            meta=MetaSection.from_dict(data.get("meta", {})),
            strategy_profile=StrategyProfileSection.from_dict(data.get("strategy_profile", {})),
            entry_score=EntryScoreSection.from_dict(data.get("entry_score", {})),
            entry_triggers=EntryTriggersSection.from_dict(data.get("entry_triggers", {})),
            exit_management=ExitManagementSection.from_dict(data.get("exit_management", {})),
            risk_leverage=RiskLeverageSection.from_dict(data.get("risk_leverage", {})),
            execution_simulation=ExecutionSimulationSection.from_dict(data.get("execution_simulation", {})),
            optimization=OptimizationSection.from_dict(data.get("optimization", {})),
            walk_forward=WalkForwardSection.from_dict(data.get("walk_forward", {})),
            parameter_groups=param_groups,
            conditionals=conditionals,
            constraints=ConstraintsSection.from_dict(data.get("constraints", {})),
            overrides=data.get("overrides", {})
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialisiert zu JSON-String."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "BacktestConfigV2":
        """Erstellt aus JSON-String."""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: Path) -> bool:
        """Speichert Konfiguration als JSON-Datei."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            logger.info(f"Config saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    @classmethod
    def load(cls, path: Path) -> "BacktestConfigV2":
        """Laedt Konfiguration aus JSON-Datei."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def get_optimizable_parameters(self) -> Dict[str, List[Any]]:
        """
        Sammelt alle Parameter mit optimize=True und gibt deren Suchraum zurueck.

        Returns:
            Dict mit Parameter-Pfaden und deren moeglichen Werten
        """
        params = {}

        # Entry Score
        if self.entry_score.min_score_for_entry.optimize:
            params["entry_score.min_score_for_entry"] = \
                self.entry_score.min_score_for_entry.get_search_space()

        # Entry Triggers - Breakout
        if self.entry_triggers.breakout.enabled:
            if self.entry_triggers.breakout.volume_multiplier.optimize:
                params["entry_triggers.breakout.volume_multiplier"] = \
                    self.entry_triggers.breakout.volume_multiplier.get_search_space()
            if self.entry_triggers.breakout.close_threshold.optimize:
                params["entry_triggers.breakout.close_threshold"] = \
                    self.entry_triggers.breakout.close_threshold.get_search_space()

        # Entry Triggers - Pullback
        if self.entry_triggers.pullback.enabled:
            if self.entry_triggers.pullback.max_distance_atr.optimize:
                params["entry_triggers.pullback.max_distance_atr"] = \
                    self.entry_triggers.pullback.max_distance_atr.get_search_space()

        # Exit Management - Stop Loss
        if self.exit_management.stop_loss.atr_multiplier.optimize:
            params["exit_management.stop_loss.atr_multiplier"] = \
                self.exit_management.stop_loss.atr_multiplier.get_search_space()

        # Exit Management - Take Profit
        if self.exit_management.take_profit.atr_multiplier.optimize:
            params["exit_management.take_profit.atr_multiplier"] = \
                self.exit_management.take_profit.atr_multiplier.get_search_space()

        # Exit Management - Trailing Stop
        if self.exit_management.trailing_stop.enabled:
            if self.exit_management.trailing_stop.activation_atr.optimize:
                params["exit_management.trailing_stop.activation_atr"] = \
                    self.exit_management.trailing_stop.activation_atr.get_search_space()
            if self.exit_management.trailing_stop.distance_atr.optimize:
                params["exit_management.trailing_stop.distance_atr"] = \
                    self.exit_management.trailing_stop.distance_atr.get_search_space()

        # Risk/Leverage
        if self.risk_leverage.risk_per_trade_pct.optimize:
            params["risk_leverage.risk_per_trade_pct"] = \
                self.risk_leverage.risk_per_trade_pct.get_search_space()
        if self.risk_leverage.base_leverage.optimize:
            params["risk_leverage.base_leverage"] = \
                self.risk_leverage.base_leverage.get_search_space()

        return params

    def __str__(self) -> str:
        return f"BacktestConfigV2(name={self.meta.name}, strategy={self.strategy_profile.type.value})"

    def __repr__(self) -> str:
        return self.__str__()
