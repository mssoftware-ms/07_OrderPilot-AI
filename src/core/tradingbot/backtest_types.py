"""Backtest Types for Tradingbot.

Contains dataclasses and enums for backtesting:
- BacktestMode: Simulation mode enum
- BacktestConfig: Configuration settings
- BacktestTrade: Individual trade record
- BacktestState: Backtest state tracking
- BacktestResult: Complete backtest results
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .config import TrailingMode
from .models import TradeSide

class BacktestMode(str, Enum):
    """Backtest execution modes."""
    FAST = "fast"  # Skip some calculations for speed
    FULL = "full"  # Full simulation with all features
    DEBUG = "debug"  # Extra logging and validation


@dataclass
class BacktestConfig:
    """Configuration for backtest run."""
    # Data range
    start_date: datetime
    end_date: datetime
    symbol: str
    timeframe: str = "1T"  # 1 minute default

    # Simulation parameters
    initial_capital: float = 10000.0
    slippage_pct: float = 0.05
    commission_pct: float = 0.1  # Per side
    seed: int | None = None  # Random seed for reproducibility

    # Execution
    mode: BacktestMode = BacktestMode.FULL
    warmup_bars: int = 50  # Bars needed for indicators

    # Output
    save_trades: bool = True
    save_equity_curve: bool = True
    save_decisions: bool = False  # Can be large
    output_dir: Path | None = None

    def get_seed(self) -> int:
        """Get deterministic seed based on config."""
        if self.seed is not None:
            return self.seed
        # Generate seed from config hash
        config_str = f"{self.symbol}{self.start_date}{self.end_date}{self.timeframe}"
        return int(hashlib.sha256(config_str.encode()).hexdigest()[:8], 16)


@dataclass
class BacktestTrade:
    """Record of a completed trade."""
    trade_id: str
    symbol: str
    side: TradeSide
    entry_time: datetime
    entry_price: float
    entry_size: float
    exit_time: datetime
    exit_price: float
    exit_reason: str
    pnl: float
    pnl_pct: float
    bars_held: int
    max_favorable_excursion: float
    max_adverse_excursion: float
    fees: float
    slippage: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "entry_time": self.entry_time.isoformat(),
            "entry_price": self.entry_price,
            "entry_size": self.entry_size,
            "exit_time": self.exit_time.isoformat(),
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "bars_held": self.bars_held,
            "mfe": self.max_favorable_excursion,
            "mae": self.max_adverse_excursion,
            "fees": self.fees,
            "slippage": self.slippage,
        }


@dataclass
class BacktestState:
    """State tracking during backtest."""
    bar_index: int = 0
    current_time: datetime | None = None
    capital: float = 10000.0
    position: PositionState | None = None
    pending_signal: Signal | None = None

    # Tracking
    equity_curve: list[tuple[datetime, float]] = field(default_factory=list)
    trades: list[BacktestTrade] = field(default_factory=list)
    decisions: list[BotDecision] = field(default_factory=list)
    signals_generated: int = 0
    signals_confirmed: int = 0
    orders_executed: int = 0

    # Current bar data
    current_bar: dict | None = None
    features: FeatureVector | None = None
    regime: RegimeState | None = None


@dataclass
class BacktestResult:
    """Result of a backtest run."""
    config: BacktestConfig
    metrics: PerformanceMetrics
    trades: list[BacktestTrade]
    equity_curve: list[tuple[datetime, float]]
    run_time_seconds: float
    total_bars: int
    seed_used: int

    # Summary stats
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    total_fees: float = 0.0
    max_drawdown_pct: float = 0.0
    final_capital: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "config": {
                "symbol": self.config.symbol,
                "start_date": self.config.start_date.isoformat(),
                "end_date": self.config.end_date.isoformat(),
                "timeframe": self.config.timeframe,
                "initial_capital": self.config.initial_capital,
                "slippage_pct": self.config.slippage_pct,
                "commission_pct": self.config.commission_pct,
                "seed": self.seed_used,
            },
            "metrics": {
                "profit_factor": self.metrics.profit_factor,
                "max_drawdown_pct": self.metrics.max_drawdown_pct,
                "win_rate": self.metrics.win_rate,
                "expectancy": self.metrics.expectancy,
                "sharpe_ratio": self.metrics.sharpe_ratio,
                "sortino_ratio": self.metrics.sortino_ratio,
                "calmar_ratio": self.metrics.calmar_ratio,
            },
            "summary": {
                "total_trades": self.total_trades,
                "winning_trades": self.winning_trades,
                "losing_trades": self.losing_trades,
                "total_pnl": self.total_pnl,
                "total_fees": self.total_fees,
                "max_drawdown_pct": self.max_drawdown_pct,
                "final_capital": self.final_capital,
                "run_time_seconds": self.run_time_seconds,
                "total_bars": self.total_bars,
            },
            "trades": [t.to_dict() for t in self.trades],
        }

    def save(self, path: Path) -> None:
        """Save result to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Backtest result saved to {path}")


