"""Strategy Evaluator Types and Data Models.

Contains data classes and Pydantic models for strategy evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field


@dataclass
class TradeResult:
    """Result of a single trade."""
    entry_time: datetime
    exit_time: datetime
    side: str  # "long" or "short"
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    bars_held: int
    exit_reason: str
    strategy_name: str


@dataclass
class PerformanceMetrics:
    """Performance metrics for a strategy evaluation period."""
    # Core metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    # Profit metrics
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0
    profit_factor: float = 0.0

    # Average metrics
    avg_win: float = 0.0
    avg_loss: float = 0.0
    avg_trade: float = 0.0
    expectancy: float = 0.0

    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    max_consecutive_losses: int = 0
    max_consecutive_wins: int = 0

    # Time metrics
    avg_bars_held: float = 0.0
    avg_win_bars: float = 0.0
    avg_loss_bars: float = 0.0

    # Ratios
    sharpe_ratio: float | None = None
    sortino_ratio: float | None = None
    calmar_ratio: float | None = None

    # Period info
    start_date: datetime | None = None
    end_date: datetime | None = None
    sample_type: str = "in_sample"  # "in_sample" or "out_of_sample"

    def is_robust(
        self,
        min_trades: int = 30,
        min_profit_factor: float = 1.2,
        max_drawdown_pct: float = 15.0,
        min_win_rate: float = 0.35
    ) -> bool:
        """Check if metrics meet robustness criteria.

        Args:
            min_trades: Minimum number of trades
            min_profit_factor: Minimum profit factor
            max_drawdown_pct: Maximum allowed drawdown %
            min_win_rate: Minimum win rate

        Returns:
            True if all criteria met
        """
        return (
            self.total_trades >= min_trades and
            self.profit_factor >= min_profit_factor and
            abs(self.max_drawdown_pct) <= max_drawdown_pct and
            self.win_rate >= min_win_rate
        )


class RobustnessGate(BaseModel):
    """Configuration for robustness validation."""
    min_trades: int = Field(default=30, ge=10)
    min_profit_factor: float = Field(default=1.2, ge=1.0)
    max_drawdown_pct: float = Field(default=15.0, ge=1.0, le=50.0)
    min_win_rate: float = Field(default=0.35, ge=0.1, le=0.9)
    min_expectancy: float = Field(default=0.0)  # Minimum expected value per trade
    require_oos_validation: bool = Field(default=True)
    oos_degradation_max: float = Field(default=0.3)  # Max 30% worse in OOS


class WalkForwardConfig(BaseModel):
    """Configuration for walk-forward analysis."""
    training_window_days: int = Field(default=30, ge=7)
    test_window_days: int = Field(default=7, ge=1)
    min_training_trades: int = Field(default=20, ge=5)
    anchored: bool = Field(default=False)  # Anchored vs rolling window
    step_days: int = Field(default=7, ge=1)  # Step size for rolling


@dataclass
class WalkForwardResult:
    """Result of walk-forward analysis."""
    strategy_name: str
    config: WalkForwardConfig
    in_sample_metrics: PerformanceMetrics
    out_of_sample_metrics: PerformanceMetrics
    periods_evaluated: int = 0
    periods_passed: int = 0
    robustness_score: float = 0.0
    is_robust: bool = False
    evaluation_date: datetime = field(default_factory=datetime.utcnow)

    # Enhanced walk-forward metrics
    period_results: list[tuple[PerformanceMetrics, PerformanceMetrics]] = field(default_factory=list)
    rolling_sharpe: list[float] = field(default_factory=list)
    rolling_drawdown: list[float] = field(default_factory=list)
    period_dates: list[tuple[datetime, datetime]] = field(default_factory=list)

    def get_degradation_pct(self) -> float:
        """Calculate performance degradation from IS to OOS.

        Returns:
            Degradation percentage (negative = improvement)
        """
        if self.in_sample_metrics.profit_factor <= 0:
            return 100.0

        pf_diff = self.in_sample_metrics.profit_factor - self.out_of_sample_metrics.profit_factor
        return (pf_diff / self.in_sample_metrics.profit_factor) * 100.0


@dataclass
class RobustnessReport:
    """Robustness validation report for strategy walk-forward analysis."""
    strategy_name: str
    walk_forward_result: WalkForwardResult

    # Validation criteria
    min_trades_met: bool = False
    max_drawdown_met: bool = False
    min_sharpe_met: bool = False
    degradation_acceptable: bool = False

    # Detailed metrics
    total_trades: int = 0
    max_drawdown_pct: float = 0.0
    avg_sharpe_ratio: float = 0.0
    degradation_pct: float = 0.0

    # Pass/fail status
    is_robust: bool = False
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Generation timestamp
    report_date: datetime = field(default_factory=datetime.utcnow)

    def get_status_summary(self) -> str:
        """Get human-readable status summary.

        Returns:
            Status text (PASS/FAIL with reason)
        """
        if self.is_robust:
            return f"✅ ROBUST - Strategy passed {len([m for m in [self.min_trades_met, self.max_drawdown_met, self.min_sharpe_met, self.degradation_acceptable] if m])}/4 criteria"

        failed_count = len(self.failures)
        return f"❌ NOT ROBUST - {failed_count} critical failure(s)"

    def get_recommendation(self) -> str:
        """Get trading recommendation based on validation.

        Returns:
            Recommendation text
        """
        if self.is_robust:
            if len(self.warnings) == 0:
                return "Strong candidate for live trading"
            return f"Acceptable for live trading (monitor {len(self.warnings)} warnings)"

        if self.degradation_pct > 50:
            return "High overfitting risk - DO NOT USE in live trading"

        if not self.min_trades_met:
            return "Insufficient trade sample - gather more data before live trading"

        return "Failed robustness criteria - review and optimize before live trading"
