"""Excel Export Utilities for Strategy Simulation (REFACTORED).

Exports simulation results to Excel (.xlsx) files with multiple sheets.

REFACTORED: Split into focused helper modules using composition pattern.
- excel_export_styles.py: Style definitions and openpyxl dependency check
- excel_export_ui_table.py: UI table sheet creation + parameter legend
- excel_export_summary.py: Summary sheet creation
- excel_export_optimization.py: Optimization sheet creation
- excel_export_trades.py: Trades sheet creation
- excel_export_parameters.py: Parameters sheet creation
- excel_export_save.py: Save orchestration
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .result_types import SimulationResult, OptimizationRun, TradeRecord

# Import style helpers and check availability
from .excel_export_styles import (
    check_openpyxl_available,
    create_workbook,
    create_header_font,
    create_header_fill,
    create_positive_fill,
    create_negative_fill,
    create_border,
    OPENPYXL_AVAILABLE,
)

# Import sheet creation helpers
from .excel_export_ui_table import ExcelExportUITable
from .excel_export_summary import ExcelExportSummary
from .excel_export_optimization import ExcelExportOptimization
from .excel_export_trades import ExcelExportTrades
from .excel_export_parameters import ExcelExportParameters
from .excel_export_save import ExcelExportSave

logger = logging.getLogger(__name__)


class StrategySimulatorExport:
    """Export strategy simulation results to Excel (REFACTORED).

    Creates a multi-sheet Excel file with:
    - UI Table: Exact copy of UI results table (first sheet)
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
        check_openpyxl_available()

        self.filepath = Path(filepath)
        self.workbook = create_workbook()
        self._results: list[SimulationResult] = []
        self._optimization_run: OptimizationRun | None = None
        self._ui_table_data: list[list[str]] | None = None

        # Styles
        self._header_font = create_header_font()
        self._header_fill = create_header_fill()
        self._positive_fill = create_positive_fill()
        self._negative_fill = create_negative_fill()
        self._border = create_border()

        # Create helpers (composition pattern)
        self._ui_table = ExcelExportUITable(self)
        self._summary = ExcelExportSummary(self)
        self._optimization = ExcelExportOptimization(self)
        self._trades = ExcelExportTrades(self)
        self._parameters = ExcelExportParameters(self)
        self._save_helper = ExcelExportSave(self)

    # === Data Addition ===

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

    def add_ui_table_data(self, table_data: list[list[str]]) -> None:
        """Add UI table data for export as first sheet.

        Args:
            table_data: List of rows, each row is a list of cell values.
                        First row should be headers.
        """
        self._ui_table_data = table_data

    # === Helper Method (used by multiple sheet creators) ===

    def _calculate_score(self, result) -> int:
        """Calculate performance score from -1000 to +1000."""
        pnl_pct = result.total_pnl_pct
        return int(max(-1000, min(1000, pnl_pct * 10)))

    # === Sheet Creation (Delegiert) ===

    def add_ui_table_sheet(self) -> None:
        """Add UI table as first sheet (delegiert)."""
        return self._ui_table.add_ui_table_sheet()

    def add_summary_sheet(self) -> None:
        """Add summary sheet with all results (delegiert)."""
        return self._summary.add_summary_sheet()

    def add_optimization_sheet(self) -> None:
        """Add optimization results sheet (delegiert)."""
        return self._optimization.add_optimization_sheet()

    def add_trades_sheet(self, result: SimulationResult, sheet_name: str = None) -> None:
        """Add detailed trades sheet for a specific result (delegiert).

        Args:
            result: SimulationResult with trades
            sheet_name: Optional custom sheet name
        """
        return self._trades.add_trades_sheet(result, sheet_name)

    def add_parameters_sheet(self) -> None:
        """Add sheet documenting parameter definitions (delegiert)."""
        return self._parameters.add_parameters_sheet()

    # === Save (Delegiert) ===

    def save(self) -> Path:
        """Save workbook and return path (delegiert).

        Returns:
            Path to saved file
        """
        return self._save_helper.save()


def export_simulation_results(
    results: list[SimulationResult],
    filepath: Path | str,
    optimization_run: OptimizationRun | None = None,
    ui_table_data: list[list[str]] | None = None,
) -> Path:
    """Convenience function to export simulation results.

    Args:
        results: List of simulation results
        filepath: Path to save Excel file
        optimization_run: Optional optimization run with all trials
        ui_table_data: Optional list of table rows from UI (exported as first sheet)

    Returns:
        Path to saved file
    """
    exporter = StrategySimulatorExport(filepath)
    exporter.add_results(results)

    if optimization_run:
        exporter.add_optimization_run(optimization_run)

    if ui_table_data:
        exporter.add_ui_table_data(ui_table_data)

    return exporter.save()
