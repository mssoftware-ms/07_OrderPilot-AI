from __future__ import annotations

import json
import logging
from typing import Any, TYPE_CHECKING, TypeVar

from pydantic import BaseModel

from .openai_models import (
    AlertTriageResult,
    BacktestReview,
    OrderAnalysis,
    StrategySignalAnalysis,
    StrategyTradeAnalysis,
)

if TYPE_CHECKING:
    from src.core.tradingbot.backtest_types import BacktestResult

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class OpenAIServiceAnalysisMixin:
    """OpenAIServiceAnalysisMixin extracted from OpenAIService."""
    async def analyze_order(
        self,
        order_details: dict[str, Any],
        market_context: dict[str, Any] | None = None
    ) -> OrderAnalysis:
        """Analyze an order before placement."""
        prompt = self._build_order_analysis_prompt(order_details, market_context or {})

        return await self.structured_completion(
            prompt=prompt,
            response_model=OrderAnalysis,
            model=getattr(self.config, "model_critical", None) or getattr(self.config, "model", None),
            context={"type": "order_analysis", **order_details}
        )

    async def triage_alert(
        self,
        alert: dict[str, Any],
        portfolio_context: dict[str, Any] | None = None
    ) -> AlertTriageResult:
        """Triage an alert for priority and action."""
        prompt = self._build_alert_triage_prompt(alert, portfolio_context or {})

        return await self.structured_completion(
            prompt=prompt,
            response_model=AlertTriageResult,
            model=self.config.model,
            context={"type": "alert_triage", "alert_type": alert.get("type")}
        )

    async def review_backtest(
        self,
        result: BacktestResult | dict[str, Any]
    ) -> BacktestReview:
        """Review backtest results with AI analysis."""
        from src.ai.prompts import PromptBuilder

        if isinstance(result, dict):
            prompt = (
                "Review these backtest results:\n\n"
                f"Backtest Data:\n{json.dumps(result, indent=2)}\n\n"
                "Provide structured review and insights."
            )
            return await self.structured_completion(
                prompt=prompt,
                response_model=BacktestReview,
                model=getattr(self.config, "model", None),
                context={"type": "backtest_review"},
            )

        # Extract strategy info
        strategy_name = result.strategy_name or "Unnamed Strategy"
        test_period = f"{result.start.strftime('%Y-%m-%d')} to {result.end.strftime('%Y-%m-%d')}"
        market_conditions = f"{result.duration_days:.1f} days, {result.symbol} on {result.timeframe} timeframe"

        # Build performance metrics dict
        performance_metrics = {
            "total_return": f"{result.metrics.total_return_pct:.2f}%",
            "sharpe_ratio": f"{result.metrics.sharpe_ratio:.2f}" if result.metrics.sharpe_ratio else "N/A",
            "sortino_ratio": f"{result.metrics.sortino_ratio:.2f}" if result.metrics.sortino_ratio else "N/A",
            "max_drawdown": f"{result.metrics.max_drawdown_pct:.2f}%",
            "annual_return": f"{result.metrics.annual_return_pct:.2f}%" if result.metrics.annual_return_pct else "N/A",
            "profit_factor": f"{result.metrics.profit_factor:.2f}",
            "recovery_factor": f"{result.metrics.recovery_factor:.2f}" if result.metrics.recovery_factor else "N/A",
            "initial_capital": f"${result.initial_capital:,.2f}",
            "final_capital": f"${result.final_capital:,.2f}",
            "total_pnl": f"${result.total_pnl:,.2f}"
        }

        # Build trade statistics dict
        trade_statistics = {
            "total_trades": result.metrics.total_trades,
            "winning_trades": result.metrics.winning_trades,
            "losing_trades": result.metrics.losing_trades,
            "win_rate": f"{result.metrics.win_rate * 100:.1f}%",
            "avg_win": f"${result.metrics.avg_win:,.2f}",
            "avg_loss": f"${result.metrics.avg_loss:,.2f}",
            "largest_win": f"${result.metrics.largest_win:,.2f}",
            "largest_loss": f"${result.metrics.largest_loss:,.2f}",
            "avg_r_multiple": f"{result.metrics.avg_r_multiple:.2f}" if result.metrics.avg_r_multiple else "N/A",
            "avg_trade_duration": f"{result.metrics.avg_trade_duration_minutes:.1f} minutes" if result.metrics.avg_trade_duration_minutes else "N/A",
            "max_consecutive_wins": result.metrics.max_consecutive_wins,
            "max_consecutive_losses": result.metrics.max_consecutive_losses,
            "expectancy": f"${result.metrics.expectancy:.2f}" if result.metrics.expectancy else "N/A"
        }

        # Build prompt using PromptBuilder
        prompt = PromptBuilder.build_backtest_prompt(
            strategy_name=strategy_name,
            test_period=test_period,
            market_conditions=market_conditions,
            performance_metrics=performance_metrics,
            trade_statistics=trade_statistics
        )

        return await self.structured_completion(
            prompt=prompt,
            response_model=BacktestReview,
            model=self.config.model,
            context={
                "type": "backtest_review",
                "strategy": strategy_name,
                "symbol": result.symbol,
                "total_return": result.metrics.total_return_pct
            }
        )

    async def analyze_signal(
        self,
        signal: dict[str, Any],
        indicators: dict[str, Any]
    ) -> StrategySignalAnalysis:
        """Analyze a strategy signal."""
        prompt = self._build_signal_analysis_prompt(signal, indicators)

        return await self.structured_completion(
            prompt=prompt,
            response_model=StrategySignalAnalysis,
            model=self.config.model,
            context={"type": "signal_analysis", "signal_type": signal.get("type")}
        )

    async def analyze_strategy_trades(
        self,
        strategy_name: str,
        symbol: str,
        trades: list[dict[str, Any]],
        stats: dict[str, Any],
        strategy_params: dict[str, Any]
    ) -> StrategyTradeAnalysis:
        """Analyze strategy trades and provide improvement suggestions."""
        prompt = self._build_strategy_trade_analysis_prompt(
            strategy_name, symbol, trades, stats, strategy_params
        )

        return await self.structured_completion(
            prompt=prompt,
            response_model=StrategyTradeAnalysis,
            model=self.config.model,
            context={
                "type": "strategy_trade_analysis",
                "strategy": strategy_name,
                "symbol": symbol,
                "total_trades": len(trades)
            }
        )
