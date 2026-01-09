"""Walk-Forward Runner - Results Export.

Refactored from walk_forward_runner.py monolith.

Module 6/6 of walk_forward_runner.py split.

Contains:
- Results export to JSON/CSV
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class WalkForwardExport:
    """Helper für WalkForwardRunner results export."""

    def __init__(self, parent):
        """
        Args:
            parent: WalkForwardRunner Instanz
        """
        self.parent = parent

    async def export_results(
        self,
        output_dir: Path | str,
    ) -> dict[str, Path]:
        """Exportiert Ergebnisse.

        Args:
            output_dir: Ausgabeverzeichnis

        Returns:
            Dictionary mit Export-Pfaden
        """
        from .walk_forward_runner import WalkForwardSummary

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exports = {}

        # 1. Summary JSON
        summary = WalkForwardSummary(
            wf_id=self.parent.wf_id,
            folds=self.parent._folds,
            total_folds=len(self.parent._folds),
            successful_folds=sum(1 for f in self.parent._folds if f.is_successful),
            aggregated_metrics=self.parent._metrics.calculate_aggregated_metrics(),
            stability_metrics=self.parent._metrics.calculate_stability_metrics(),
        )

        summary_path = output_dir / f"{self.parent.wf_id}_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary.to_dict(), f, indent=2, default=str)
        exports["summary"] = summary_path

        # 2. Folds CSV
        folds_path = output_dir / f"{self.parent.wf_id}_folds.csv"
        with open(folds_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "fold", "train_period", "test_period",
                "oos_trades", "oos_win_rate", "oos_pf", "oos_expectancy",
                "oos_return_pct", "oos_max_dd", "opt_runs", "error"
            ])

            # Data
            for fold in self.parent._folds:
                train_period = f"{fold.train_start.date()} - {fold.train_end.date()}"
                test_period = f"{fold.test_start.date()} - {fold.test_end.date()}"

                if fold.test_metrics:
                    m = fold.test_metrics
                    row = [
                        fold.fold_index,
                        train_period,
                        test_period,
                        m.total_trades,
                        f"{m.win_rate:.3f}",
                        f"{m.profit_factor:.2f}" if m.profit_factor < 100 else "inf",
                        f"{m.expectancy:.2f}" if m.expectancy else "",
                        f"{m.total_return_pct:.2f}",
                        f"{m.max_drawdown_pct:.2f}",
                        fold.optimization_runs,
                        fold.error or "",
                    ]
                else:
                    row = [
                        fold.fold_index,
                        train_period,
                        test_period,
                        "", "", "", "", "", "",
                        fold.optimization_runs,
                        fold.error or "",
                    ]

                writer.writerow(row)

        exports["folds"] = folds_path

        # 3. Individual Fold Reports (Unterordner)
        folds_dir = output_dir / f"{self.parent.wf_id}_folds"
        folds_dir.mkdir(exist_ok=True)

        for fold in self.parent._folds:
            fold_path = folds_dir / f"fold_{fold.fold_index:02d}.json"
            with open(fold_path, "w") as f:
                json.dump(fold.to_dict(), f, indent=2, default=str)

        exports["folds_dir"] = folds_dir

        logger.info(f"Exported Walk-Forward results to {output_dir}")
        return exports
