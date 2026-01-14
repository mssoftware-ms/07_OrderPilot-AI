"""
Backtesting Configuration - Risk/Leverage and execution/simulation configs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from .enums import SlippageMethod
from .optimizable import OptimizableFloat, OptimizableInt

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

