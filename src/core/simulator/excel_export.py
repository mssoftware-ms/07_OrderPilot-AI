"""Excel Export Utilities for Strategy Simulation.

Exports simulation results to Excel (.xlsx) files with multiple sheets.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .result_types import SimulationResult, OptimizationRun, TradeRecord

logger = logging.getLogger(__name__)

# Import openpyxl components (optional dependency)
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    openpyxl = None
    Font = None
    PatternFill = None
    Alignment = None
    Border = None
    Side = None
    get_column_letter = None


class StrategySimulatorExport:
    """Export strategy simulation results to Excel.

    Creates a multi-sheet Excel file with:
    - Summary: Overview of all simulation results
    - Optimization: All optimization trials (if applicable)
    - Trades_{Strategy}: Detailed trades for each result
    - Parameters: Parameter definitions and ranges
    """

    def __init__(self, filepath: Path | str):
        """Initialize exporter.

        Args:
            filepath: Path to save the Excel file
        """
        if not OPENPYXL_AVAILABLE:
            raise ImportError(
                "openpyxl is required for Excel export. "
                "Install with: pip install openpyxl"
            )

        self.filepath = Path(filepath)
        self.workbook = openpyxl.Workbook()
        self._results: list[SimulationResult] = []
        self._optimization_run: OptimizationRun | None = None

        # Styles
        self._header_font = Font(bold=True, color="FFFFFF")
        self._header_fill = PatternFill(
            start_color="4472C4", end_color="4472C4", fill_type="solid"
        )
        self._positive_fill = PatternFill(
            start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"
        )
        self._negative_fill = PatternFill(
            start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"
        )
        self._border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

    def add_results(self, results: list[SimulationResult]) -> None:
        """Add simulation results to export.

        Args:
            results: List of SimulationResult objects
        """
        self._results.extend(results)

    def add_optimization_run(self, opt_run: OptimizationRun) -> None:
        """Add optimization run to export.

        Args:
            opt_run: OptimizationRun with all trials
        """
        self._optimization_run = opt_run

    def _calculate_score(self, result) -> int:
        """Calculate performance score from -1000 to +1000."""
        pnl_pct = result.total_pnl_pct
        return int(max(-1000, min(1000, pnl_pct * 10)))

    def add_summary_sheet(self) -> None:
        """Add summary sheet with all results, sorted by Score."""
        ws = self.workbook.active
        ws.title = "Summary"

        headers = [
            "Strategy",
            "Symbol",
            "Trades",
            "Win %",
            "PF",
            "P&L €",
            "P&L %",
            "DD %",
            "Score",
            "Parameters",
        ]

        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = self._header_font
            cell.fill = self._header_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = self._border

        # Sort results by Score (descending)
        sorted_results = sorted(
            self._results,
            key=lambda r: self._calculate_score(r),
            reverse=True
        )

        # Write data
        for row_idx, result in enumerate(sorted_results, 2):
            # Show ALL parameters
            params_str = ", ".join(
                f"{k}={v}" for k, v in result.parameters.items()
            )

            score = self._calculate_score(result)

            data = [
                result.strategy_name,
                result.symbol,
                result.total_trades,
                f"{result.win_rate * 100:.1f}",
                f"{result.profit_factor:.2f}",
                f"{result.total_pnl:.2f}",
                f"{result.total_pnl_pct:.2f}",
                f"{result.max_drawdown_pct:.2f}",
                score,
                params_str,
            ]

            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                cell.border = self._border

                # Color P&L cells
                if col == 6:  # P&L €
                    try:
                        pnl_val = float(str(value).replace(",", ""))
                        if pnl_val > 0:
                            cell.fill = self._positive_fill
                        elif pnl_val < 0:
                            cell.fill = self._negative_fill
                    except (ValueError, TypeError):
                        pass

                # Color Score cells
                if col == 9:  # Score
                    try:
                        score_val = int(value)
                        if score_val > 0:
                            cell.fill = self._positive_fill
                        elif score_val < 0:
                            cell.fill = self._negative_fill
                    except (ValueError, TypeError):
                        pass

        # Adjust column widths
        ws.column_dimensions["A"].width = 16  # Strategy
        ws.column_dimensions["B"].width = 12  # Symbol
        ws.column_dimensions["C"].width = 8   # Trades
        ws.column_dimensions["D"].width = 8   # Win %
        ws.column_dimensions["E"].width = 8   # PF
        ws.column_dimensions["F"].width = 12  # P&L €
        ws.column_dimensions["G"].width = 10  # P&L %
        ws.column_dimensions["H"].width = 8   # DD %
        ws.column_dimensions["I"].width = 10  # Score
        ws.column_dimensions["J"].width = 100 # Parameters (wide for all params)

    def add_optimization_sheet(self) -> None:
        """Add optimization results sheet."""
        if not self._optimization_run:
            return

        ws = self.workbook.create_sheet("Optimization")
        opt = self._optimization_run

        # Header info
        ws.cell(row=1, column=1, value="Optimization Results")
        ws.cell(row=1, column=1).font = Font(bold=True, size=14)
        ws.cell(row=2, column=1, value=f"Strategy: {opt.strategy_name}")
        ws.cell(row=3, column=1, value=f"Type: {opt.optimization_type}")
        ws.cell(row=4, column=1, value=f"Objective: {opt.objective_metric}")
        ws.cell(row=5, column=1, value=f"Total Trials: {opt.total_trials}")
        ws.cell(row=6, column=1, value=f"Elapsed: {opt.elapsed_seconds:.1f}s")
        ws.cell(row=7, column=1, value=f"Best Score: {opt.best_score:.4f}")

        # Best params
        ws.cell(row=8, column=1, value="Best Parameters:")
        for i, (k, v) in enumerate(opt.best_params.items()):
            ws.cell(row=8, column=2 + i, value=f"{k}={v}")

        # Trials table
        start_row = 10

        # Get all param names from first trial
        if opt.all_trials:
            param_names = list(opt.all_trials[0].parameters.keys())
            metric_names = list(opt.all_trials[0].metrics.keys())

            headers = ["Trial", "Score"] + param_names + metric_names

            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=start_row, column=col, value=header)
                cell.font = self._header_font
                cell.fill = self._header_fill
                cell.border = self._border

            # Write trials
            for row_idx, trial in enumerate(opt.all_trials, start_row + 1):
                ws.cell(row=row_idx, column=1, value=trial.trial_number)
                ws.cell(row=row_idx, column=2, value=f"{trial.score:.4f}")

                col = 3
                for param_name in param_names:
                    value = trial.parameters.get(param_name, "")
                    ws.cell(row=row_idx, column=col, value=value)
                    col += 1

                for metric_name in metric_names:
                    value = trial.metrics.get(metric_name, "")
                    if isinstance(value, float):
                        value = f"{value:.4f}"
                    ws.cell(row=row_idx, column=col, value=value)
                    col += 1

            # Adjust widths
            for col in range(1, len(headers) + 1):
                ws.column_dimensions[get_column_letter(col)].width = 12

    def add_trades_sheet(self, result: SimulationResult, sheet_name: str = None) -> None:
        """Add detailed trades sheet for a specific result.

        Args:
            result: SimulationResult with trades
            sheet_name: Optional custom sheet name
        """
        name = sheet_name or f"Trades_{result.strategy_name[:20]}"
        # Ensure unique sheet name
        existing = [ws.title for ws in self.workbook.worksheets]
        if name in existing:
            name = f"{name}_{len(existing)}"

        ws = self.workbook.create_sheet(name)

        headers = [
            "Entry Time",
            "Exit Time",
            "Side",
            "Size",
            "Entry Price",
            "Exit Price",
            "Stop Loss",
            "Take Profit",
            "P&L",
            "P&L %",
            "Exit Reason",
            "Duration (min)",
            "Commission",
        ]

        # Write headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = self._header_font
            cell.fill = self._header_fill
            cell.border = self._border

        # Write trades
        for row_idx, trade in enumerate(result.trades, 2):
            duration_min = trade.duration_seconds / 60 if trade.duration_seconds else 0

            data = [
                trade.entry_time.strftime("%Y-%m-%d %H:%M"),
                trade.exit_time.strftime("%Y-%m-%d %H:%M"),
                trade.side,
                f"{trade.size:.4f}",
                f"{trade.entry_price:.4f}",
                f"{trade.exit_price:.4f}",
                f"{trade.stop_loss:.4f}" if trade.stop_loss else "N/A",
                f"{trade.take_profit:.4f}" if trade.take_profit else "N/A",
                f"{trade.pnl:.2f}",
                f"{trade.pnl_pct * 100:.2f}",
                trade.exit_reason,
                f"{duration_min:.1f}",
                f"{trade.commission:.4f}",
            ]

            for col, value in enumerate(data, 1):
                cell = ws.cell(row=row_idx, column=col, value=value)
                cell.border = self._border

                # Color P&L cells
                if col == 9:  # P&L column
                    try:
                        pnl_val = float(str(value).replace(",", ""))
                        if pnl_val > 0:
                            cell.fill = self._positive_fill
                        elif pnl_val < 0:
                            cell.fill = self._negative_fill
                    except ValueError:
                        pass

        # Adjust column widths
        widths = [18, 18, 8, 10, 12, 12, 12, 12, 10, 10, 14, 12, 10]
        for col, width in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

    def add_parameters_sheet(self) -> None:
        """Add sheet documenting parameter definitions."""
        from .strategy_params import STRATEGY_PARAMETER_REGISTRY

        ws = self.workbook.create_sheet("Parameters")

        headers = [
            "Strategy",
            "Parameter",
            "Display Name",
            "Type",
            "Default",
            "Min",
            "Max",
            "Step",
            "Description",
        ]

        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = self._header_font
            cell.fill = self._header_fill
            cell.border = self._border

        row = 2
        for strategy_name, config in STRATEGY_PARAMETER_REGISTRY.items():
            for param in config.parameters:
                data = [
                    strategy_name.value,
                    param.name,
                    param.display_name,
                    param.param_type,
                    param.default,
                    param.min_value,
                    param.max_value,
                    param.step,
                    param.description,
                ]
                for col, value in enumerate(data, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    cell.border = self._border
                row += 1

        # Adjust widths
        widths = [16, 18, 16, 8, 10, 8, 8, 8, 40]
        for col, width in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

    def save(self) -> Path:
        """Save workbook and return path.

        Returns:
            Path to saved file
        """
        # Build sheets
        self.add_summary_sheet()

        if self._optimization_run:
            self.add_optimization_sheet()

        # Add trades sheets for top results (max 5)
        for result in self._results[:5]:
            if result.trades:
                self.add_trades_sheet(result)

        self.add_parameters_sheet()

        # Save
        self.workbook.save(self.filepath)
        logger.info(f"Saved simulation results to {self.filepath}")

        return self.filepath


def export_simulation_results(
    results: list[SimulationResult],
    filepath: Path | str,
    optimization_run: OptimizationRun | None = None,
) -> Path:
    """Convenience function to export simulation results.

    Args:
        results: List of simulation results
        filepath: Path to save Excel file
        optimization_run: Optional optimization run with all trials

    Returns:
        Path to saved file
    """
    exporter = StrategySimulatorExport(filepath)
    exporter.add_results(results)

    if optimization_run:
        exporter.add_optimization_run(optimization_run)

    return exporter.save()
