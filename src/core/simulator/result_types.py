"""Result Types for Strategy Simulation.

Contains dataclasses for simulation results, trades, and optimization runs.
"""

<<<<<<< HEAD
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

EntryPoint = tuple[float, datetime] | tuple[float, datetime, float]
=======
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268


@dataclass
class TradeRecord:
    """Single trade record from simulation."""

    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    side: str  # "long" or "short"
    size: float
    pnl: float
    pnl_pct: float
    exit_reason: str
    stop_loss: float | None = None
    take_profit: float | None = None
    commission: float = 0.0
    slippage: float = 0.0

    @property
    def duration_seconds(self) -> float:
        """Duration of trade in seconds."""
        return (self.exit_time - self.entry_time).total_seconds()

    @property
    def is_winner(self) -> bool:
        """Check if trade was profitable."""
        return self.pnl > 0

    @property
    def r_multiple(self) -> float | None:
        """Calculate R-multiple if stop loss was set."""
        if self.stop_loss is None or self.stop_loss == 0:
            return None
        risk = abs(self.entry_price - self.stop_loss)
        if risk == 0:
            return None
        return self.pnl / (self.size * risk)


<<<<<<< HEAD
@dataclass
class SimulationResult:
    """Result of a single simulation run."""

    strategy_name: str
    parameters: dict[str, Any]
    symbol: str
    trades: list[TradeRecord]
=======
@dataclass
class SimulationResult:
    """Result of a single simulation run."""

    strategy_name: str
    parameters: dict[str, Any]
    symbol: str
    trades: list[TradeRecord]
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268

    # Performance metrics
    total_pnl: float
    total_pnl_pct: float
    win_rate: float
    profit_factor: float
    max_drawdown_pct: float
    sharpe_ratio: float | None
    sortino_ratio: float | None

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_trade_duration_seconds: float
    max_consecutive_wins: int
    max_consecutive_losses: int

    # Capital tracking
    initial_capital: float
    final_capital: float

<<<<<<< HEAD
    # Metadata
    run_timestamp: datetime = field(default_factory=datetime.utcnow)
    data_start: datetime | None = None
    data_end: datetime | None = None
    bars_processed: int = 0

    # Entry-only simulation metadata
    entry_only: bool = False
    entry_side: str = "long"
    entry_count: int = 0
    entry_score: float | None = None
    entry_avg_offset_pct: float | None = None
    entry_best_price: float | None = None
    entry_best_time: datetime | None = None
    entry_points: list[EntryPoint] = field(default_factory=list)
=======
    # Metadata
    run_timestamp: datetime = field(default_factory=datetime.utcnow)
    data_start: datetime | None = None
    data_end: datetime | None = None
    bars_processed: int = 0
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268

    @property
    def expectancy(self) -> float | None:
        """Calculate expectancy (avg P&L per trade)."""
        if self.total_trades == 0:
            return None
        return self.total_pnl / self.total_trades

    @property
    def recovery_factor(self) -> float | None:
        """Calculate recovery factor (Net Profit / Max Drawdown)."""
        if self.max_drawdown_pct == 0:
            return None
        return self.total_pnl_pct / self.max_drawdown_pct

    def to_summary_dict(self) -> dict[str, Any]:
        """Convert to summary dictionary for table display."""
        return {
            "strategy": self.strategy_name,
            "parameters": self.parameters,
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "total_pnl": self.total_pnl,
            "total_pnl_pct": self.total_pnl_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "sharpe_ratio": self.sharpe_ratio,
        }


<<<<<<< HEAD
@dataclass
class OptimizationTrial:
    """Single trial in an optimization run."""

    trial_number: int
    parameters: dict[str, Any]
    score: float
    metrics: dict[str, Any]
    entry_points: list[EntryPoint] = field(default_factory=list)
    entry_side: str = "long"
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OptimizationRun:
    """Result of an optimization run (Grid Search or Bayesian)."""
=======
@dataclass
class OptimizationTrial:
    """Single trial in an optimization run."""

    trial_number: int
    parameters: dict[str, Any]
    score: float
    metrics: dict[str, float]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OptimizationRun:
    """Result of an optimization run (Grid Search or Bayesian)."""
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268

    strategy_name: str
    optimization_type: str  # "grid" or "bayesian"
    objective_metric: str  # "sharpe_ratio", "profit_factor", etc.
    best_params: dict[str, Any]
    best_score: float
    all_trials: list[OptimizationTrial]
    total_trials: int
    elapsed_seconds: float
<<<<<<< HEAD
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Best result details
    best_result: SimulationResult | None = None

    # Error tracking (for failed trials)
    errors: list[str] | None = None

    # Entry-only metadata
    entry_only: bool = False
    entry_side: str = "long"
=======
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Best result details
    best_result: SimulationResult | None = None

    # Error tracking (for failed trials)
    errors: list[str] | None = None
>>>>>>> ccb6b2434020b7970fad355a264b322ac9e7b268

    def get_top_n_trials(self, n: int = 10) -> list[OptimizationTrial]:
        """Get top N trials sorted by score (descending)."""
        return sorted(self.all_trials, key=lambda t: t.score, reverse=True)[:n]

    def to_dataframe_rows(self) -> list[dict[str, Any]]:
        """Convert all trials to list of dicts for DataFrame/Excel export."""
        rows = []
        for trial in self.all_trials:
            row = {
                "trial": trial.trial_number,
                "score": trial.score,
                **trial.parameters,
                **trial.metrics,
            }
            rows.append(row)
        return rows
