"""Report Generator for Entry Analysis.

Generates comprehensive reports in multiple formats:
- Markdown: Human-readable with regime/signal timeline
- JSON: Machine-readable for further processing
- HTML: Styled report with charts (optional)

Phase 4.5: Report Generator (MD + JSON)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .trade_filters import FilterStats
from .trade_simulator import SimulationResult
from .types import AnalysisResult, EntryEvent, EntrySide, IndicatorSet, RegimeType
from .validation import FoldResult, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ReportConfig:
    """Configuration for report generation.

    Attributes:
        include_entries: Include entry details in report.
        include_trades: Include trade-by-trade breakdown.
        include_validation: Include validation fold details.
        include_filters: Include filter statistics.
        max_entries_detail: Maximum entries to show in detail.
        max_trades_detail: Maximum trades to show in detail.
        timestamp_format: Format for timestamps.
        float_precision: Decimal places for floats.
        output_dir: Directory for saving reports.
    """

    include_entries: bool = True
    include_trades: bool = True
    include_validation: bool = True
    include_filters: bool = True
    max_entries_detail: int = 50
    max_trades_detail: int = 30
    timestamp_format: str = "%Y-%m-%d %H:%M:%S UTC"
    float_precision: int = 3
    output_dir: str | None = None


@dataclass
class ReportData:
    """Consolidated data for report generation.

    Attributes:
        symbol: Trading symbol.
        timeframe: Chart timeframe.
        analysis_time: When analysis was performed.
        regime: Detected market regime.
        entries: Entry events.
        indicator_set: Best indicator set.
        alternatives: Alternative indicator sets.
        simulation: Simulation results.
        validation: Validation results.
        filter_stats: Filter statistics.
        metadata: Additional metadata.
    """

    symbol: str
    timeframe: str
    analysis_time: datetime
    regime: RegimeType
    entries: list[EntryEvent] = field(default_factory=list)
    indicator_set: IndicatorSet | None = None
    alternatives: list[IndicatorSet] = field(default_factory=list)
    simulation: SimulationResult | None = None
    validation: ValidationResult | None = None
    filter_stats: FilterStats | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ReportGenerator:
    """Generates analysis reports in multiple formats."""

    def __init__(self, config: ReportConfig | None = None) -> None:
        """Initialize the generator.

        Args:
            config: Report configuration.
        """
        self.config = config or ReportConfig()

    def generate_markdown(self, data: ReportData) -> str:
        """Generate markdown report.

        Args:
            data: Report data.

        Returns:
            Markdown string.
        """
        lines = []

        # Header
        lines.append(f"# Entry Analysis Report: {data.symbol}")
        lines.append("")
        lines.append(f"**Generated:** {data.analysis_time.strftime(self.config.timestamp_format)}")
        lines.append(f"**Timeframe:** {data.timeframe}")
        lines.append(f"**Regime:** {data.regime.value}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Entries Found:** {len(data.entries)}")

        if data.simulation:
            sim = data.simulation
            lines.append(f"- **Total Trades:** {sim.total_trades}")
            lines.append(f"- **Win Rate:** {sim.win_rate:.1%}")
            lines.append(f"- **Profit Factor:** {sim.profit_factor:.2f}")
            lines.append(f"- **Expectancy:** {sim.expectancy:.2f}R")
            lines.append(f"- **Max Drawdown:** {sim.max_drawdown_pct:.1f}R")

        if data.validation:
            val = data.validation
            status = "PASSED" if val.is_valid else "FAILED"
            lines.append(f"- **Validation:** {status}")
            lines.append(f"- **OOS Score:** {val.avg_test_score:.3f}")
            lines.append(f"- **OOS Win Rate:** {val.oos_win_rate:.1%}")

        lines.append("")

        # Indicator Set
        if data.indicator_set:
            lines.append("## Best Indicator Set")
            lines.append("")
            lines.append(f"**Name:** {data.indicator_set.name}")
            lines.append(f"**Score:** {data.indicator_set.score:.3f}")
            lines.append("")
            lines.append("### Indicators")
            lines.append("")

            for ind in data.indicator_set.indicators:
                lines.append(f"- **{ind.get('name', 'Unknown')}**")
                params = ind.get("params", {})
                if params:
                    param_str = ", ".join(f"{k}={v}" for k, v in params.items())
                    lines.append(f"  - Params: {param_str}")
                weight = ind.get("weight", 0)
                lines.append(f"  - Weight: {weight:.2f}")

            lines.append("")

        # Validation Details
        if self.config.include_validation and data.validation:
            lines.append("## Validation Results")
            lines.append("")

            val = data.validation

            if not val.is_valid:
                lines.append("### Failure Reasons")
                lines.append("")
                for reason in val.failure_reasons:
                    lines.append(f"- {reason}")
                lines.append("")

            lines.append("### Fold Summary")
            lines.append("")
            lines.append("| Fold | Train Score | Test Score | Ratio | Train WR | Test WR | Overfit |")
            lines.append("|------|-------------|------------|-------|----------|---------|---------|")

            for fold in val.folds:
                ratio = f"{fold.train_test_ratio:.2f}" if fold.test_score > 0 else "N/A"
                overfit = "Yes" if fold.is_overfit else "No"
                lines.append(
                    f"| {fold.fold_idx} | {fold.train_score:.3f} | {fold.test_score:.3f} | "
                    f"{ratio} | {fold.train_win_rate:.1%} | {fold.test_win_rate:.1%} | {overfit} |"
                )

            lines.append("")
            lines.append(f"**Seed Used:** {val.seed_used}")
            lines.append(f"**Total Time:** {val.total_time_ms:.1f}ms")
            lines.append("")

        # Filter Statistics
        if self.config.include_filters and data.filter_stats:
            lines.append("## Filter Statistics")
            lines.append("")

            stats = data.filter_stats
            lines.append(f"- **Total Entries:** {stats.total_entries}")
            lines.append(f"- **Filtered Out:** {stats.filtered_count}")
            lines.append(f"- **Pass Rate:** {stats.pass_rate:.1%}")
            lines.append("")

            if stats.by_reason:
                lines.append("### By Reason")
                lines.append("")
                for reason, count in sorted(stats.by_reason.items(), key=lambda x: -x[1]):
                    lines.append(f"- {reason}: {count}")
                lines.append("")

        # Entry Timeline
        if self.config.include_entries and data.entries:
            lines.append("## Entry Timeline")
            lines.append("")

            entries_to_show = data.entries[: self.config.max_entries_detail]

            lines.append("| Time | Side | Price | Confidence | Reasons |")
            lines.append("|------|------|-------|------------|---------|")

            for entry in entries_to_show:
                dt = datetime.fromtimestamp(entry.timestamp, tz=timezone.utc)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
                side = entry.side.value.upper()
                reasons = ", ".join(entry.reason_tags[:2]) if entry.reason_tags else "-"
                lines.append(
                    f"| {time_str} | {side} | {entry.price:.2f} | "
                    f"{entry.confidence:.1%} | {reasons} |"
                )

            if len(data.entries) > self.config.max_entries_detail:
                remaining = len(data.entries) - self.config.max_entries_detail
                lines.append(f"\n*... and {remaining} more entries*")

            lines.append("")

        # Trade Breakdown
        if self.config.include_trades and data.simulation and data.simulation.trades:
            lines.append("## Trade Breakdown")
            lines.append("")

            trades_to_show = data.simulation.trades[: self.config.max_trades_detail]

            lines.append("| Entry Time | Side | Entry | Exit | R | Result | Exit Reason |")
            lines.append("|------------|------|-------|------|---|--------|-------------|")

            for trade in trades_to_show:
                dt = datetime.fromtimestamp(trade.entry_event.timestamp, tz=timezone.utc)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
                side = trade.side.value.upper()
                result = "WIN" if trade.is_winner else "LOSS"
                lines.append(
                    f"| {time_str} | {side} | {trade.entry_price:.2f} | "
                    f"{trade.exit_price:.2f} | {trade.r_multiple:.2f} | {result} | "
                    f"{trade.exit_reason} |"
                )

            if len(data.simulation.trades) > self.config.max_trades_detail:
                remaining = len(data.simulation.trades) - self.config.max_trades_detail
                lines.append(f"\n*... and {remaining} more trades*")

            lines.append("")

        # Alternatives
        if data.alternatives:
            lines.append("## Alternative Sets")
            lines.append("")

            for i, alt in enumerate(data.alternatives[:3], 1):
                lines.append(f"### Alternative {i}: {alt.name}")
                lines.append(f"- Score: {alt.score:.3f}")
                ind_names = [ind.get("name", "?") for ind in alt.indicators]
                lines.append(f"- Indicators: {', '.join(ind_names)}")
                lines.append("")

        # Footer
        lines.append("---")
        lines.append("*Report generated by OrderPilot-AI Entry Analyzer*")

        return "\n".join(lines)

    def generate_json(self, data: ReportData) -> dict[str, Any]:
        """Generate JSON report.

        Args:
            data: Report data.

        Returns:
            JSON-serializable dictionary.
        """
        result: dict[str, Any] = {
            "meta": {
                "symbol": data.symbol,
                "timeframe": data.timeframe,
                "analysis_time": data.analysis_time.isoformat(),
                "regime": data.regime.value,
                "generator": "OrderPilot-AI Entry Analyzer",
            },
            "summary": {
                "entries_count": len(data.entries),
            },
        }

        # Simulation metrics
        if data.simulation:
            sim = data.simulation
            result["simulation"] = {
                "total_trades": sim.total_trades,
                "winners": sim.winners,
                "losers": sim.losers,
                "win_rate": round(sim.win_rate, 4),
                "profit_factor": round(sim.profit_factor, 4),
                "avg_r": round(sim.avg_r, 4),
                "expectancy": round(sim.expectancy, 4),
                "max_drawdown_r": round(sim.max_drawdown_pct, 4),
            }

        # Validation metrics
        if data.validation:
            val = data.validation
            result["validation"] = {
                "is_valid": val.is_valid,
                "failure_reasons": val.failure_reasons,
                "avg_train_score": round(val.avg_train_score, 4),
                "avg_test_score": round(val.avg_test_score, 4),
                "avg_train_test_ratio": round(val.avg_train_test_ratio, 4),
                "oos_win_rate": round(val.oos_win_rate, 4),
                "oos_profit_factor": round(val.oos_profit_factor, 4),
                "total_oos_trades": val.total_oos_trades,
                "seed_used": val.seed_used,
                "total_time_ms": round(val.total_time_ms, 2),
                "folds": [
                    {
                        "fold_idx": f.fold_idx,
                        "train_score": round(f.train_score, 4),
                        "test_score": round(f.test_score, 4),
                        "train_test_ratio": round(f.train_test_ratio, 4),
                        "train_trades": f.train_trades,
                        "test_trades": f.test_trades,
                        "train_win_rate": round(f.train_win_rate, 4),
                        "test_win_rate": round(f.test_win_rate, 4),
                        "is_overfit": f.is_overfit,
                    }
                    for f in val.folds
                ],
            }

        # Indicator set
        if data.indicator_set:
            result["indicator_set"] = {
                "name": data.indicator_set.name,
                "score": round(data.indicator_set.score, 4),
                "regime": data.indicator_set.regime,
                "indicators": data.indicator_set.indicators,
                "postprocess": data.indicator_set.postprocess,
                "stop_config": data.indicator_set.stop_config,
            }

        # Alternatives
        if data.alternatives:
            result["alternatives"] = [
                {
                    "name": alt.name,
                    "score": round(alt.score, 4),
                    "indicators": alt.indicators,
                }
                for alt in data.alternatives[:5]
            ]

        # Filter stats
        if data.filter_stats:
            stats = data.filter_stats
            result["filter_stats"] = {
                "total_entries": stats.total_entries,
                "filtered_count": stats.filtered_count,
                "pass_rate": round(stats.pass_rate, 4),
                "by_reason": stats.by_reason,
            }

        # Entries (limited)
        if self.config.include_entries:
            result["entries"] = [
                {
                    "timestamp": e.timestamp,
                    "side": e.side.value,
                    "price": round(e.price, 4),
                    "confidence": round(e.confidence, 4),
                    "reason_tags": e.reason_tags,
                    "regime": e.regime.value if e.regime else None,
                }
                for e in data.entries[: self.config.max_entries_detail]
            ]

        # Trades (limited)
        if self.config.include_trades and data.simulation:
            result["trades"] = [
                {
                    "entry_timestamp": t.entry_event.timestamp,
                    "side": t.side.value,
                    "entry_price": round(t.entry_price, 4),
                    "exit_price": round(t.exit_price, 4),
                    "pnl_pct": round(t.pnl_pct, 4),
                    "r_multiple": round(t.r_multiple, 4),
                    "is_winner": t.is_winner,
                    "exit_reason": t.exit_reason,
                    "bars_held": t.bars_held,
                }
                for t in data.simulation.trades[: self.config.max_trades_detail]
            ]

        # Metadata
        if data.metadata:
            result["metadata"] = data.metadata

        return result

    def save_report(
        self,
        data: ReportData,
        base_name: str | None = None,
        formats: list[str] | None = None,
    ) -> dict[str, Path]:
        """Save report to files.

        Args:
            data: Report data.
            base_name: Base filename (without extension).
            formats: List of formats to save ("md", "json").

        Returns:
            Dict mapping format to saved file path.
        """
        if formats is None:
            formats = ["md", "json"]

        if base_name is None:
            ts = data.analysis_time.strftime("%Y%m%d_%H%M%S")
            base_name = f"entry_analysis_{data.symbol}_{ts}"

        output_dir = Path(self.config.output_dir) if self.config.output_dir else Path.cwd()
        output_dir.mkdir(parents=True, exist_ok=True)

        saved: dict[str, Path] = {}

        if "md" in formats:
            md_path = output_dir / f"{base_name}.md"
            md_content = self.generate_markdown(data)
            md_path.write_text(md_content, encoding="utf-8")
            saved["md"] = md_path
            logger.info("Saved markdown report: %s", md_path)

        if "json" in formats:
            json_path = output_dir / f"{base_name}.json"
            json_content = self.generate_json(data)
            json_path.write_text(
                json.dumps(json_content, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            saved["json"] = json_path
            logger.info("Saved JSON report: %s", json_path)

        return saved


def create_report_from_analysis(
    analysis: AnalysisResult,
    symbol: str,
    timeframe: str,
    simulation: SimulationResult | None = None,
    validation: ValidationResult | None = None,
    filter_stats: FilterStats | None = None,
) -> ReportData:
    """Create ReportData from an AnalysisResult.

    Args:
        analysis: Analysis result.
        symbol: Trading symbol.
        timeframe: Chart timeframe.
        simulation: Optional simulation result.
        validation: Optional validation result.
        filter_stats: Optional filter statistics.

    Returns:
        ReportData for report generation.
    """
    return ReportData(
        symbol=symbol,
        timeframe=timeframe,
        analysis_time=datetime.now(timezone.utc),
        regime=analysis.regime,
        entries=analysis.entries,
        indicator_set=analysis.best_set,
        alternatives=analysis.alternatives,
        simulation=simulation,
        validation=validation,
        filter_stats=filter_stats,
        metadata={
            "analyzer_version": "1.0.0",
            "optimizer_used": analysis.best_set is not None,
        },
    )
