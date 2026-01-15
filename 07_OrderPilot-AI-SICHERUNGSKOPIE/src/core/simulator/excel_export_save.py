"""Excel Export Save - Save Orchestration.

Refactored from excel_export.py.

Contains:
- save: Orchestrate building all sheets and saving workbook
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .excel_export import StrategySimulatorExport

logger = logging.getLogger(__name__)


class ExcelExportSave:
    """Helper for save orchestration."""

    def __init__(self, parent: StrategySimulatorExport):
        self.parent = parent

    def save(self) -> Path:
        """Save workbook and return path.

        Returns:
            Path to saved file
        """
        # Build sheets - UI table first if available
        if self.parent._ui_table_data:
            self.parent.add_ui_table_sheet()

        self.parent.add_summary_sheet()

        if self.parent._optimization_run:
            self.parent.add_optimization_sheet()

        # Add trades sheets for top results (max 5)
        for result in self.parent._results[:5]:
            if result.trades:
                self.parent.add_trades_sheet(result)

        self.parent.add_parameters_sheet()

        # Save
        self.parent.workbook.save(self.parent.filepath)
        logger.info(f"Saved simulation results to {self.parent.filepath}")

        return self.parent.filepath
