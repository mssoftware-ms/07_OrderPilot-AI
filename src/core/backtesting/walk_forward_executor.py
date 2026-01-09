"""Walk-Forward Runner - Main Execution.

Refactored from walk_forward_runner.py monolith.

Module 3/6 of walk_forward_runner.py split.

Contains:
- Main run orchestration
- Stop control
"""

from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WalkForwardExecutor:
    """Helper für WalkForwardRunner main execution."""

    def __init__(self, parent):
        """
        Args:
            parent: WalkForwardRunner Instanz
        """
        self.parent = parent

    async def run(self):
        """Führt die Walk-Forward Analyse durch.

        Returns:
            WalkForwardSummary mit allen Fold-Ergebnissen
        """
        from .walk_forward_runner import WalkForwardSummary

        if self.parent._is_running:
            raise RuntimeError("Walk-Forward already running")

        self.parent._is_running = True
        self.parent._should_stop = False
        self.parent._folds.clear()

        start_time = datetime.now()

        try:
            # 1. Folds berechnen
            self.parent._progress.emit_progress(0, "Berechne Folds...")
            fold_periods = self.parent._fold_calculator.calculate_folds()
            total_folds = len(fold_periods)

            if total_folds == 0:
                raise ValueError("Keine Folds möglich mit den gegebenen Parametern")

            logger.info(f"Starting Walk-Forward with {total_folds} folds")

            # 2. Folds ausführen
            successful = 0

            for i, (train_start, train_end, test_start, test_end) in enumerate(fold_periods):
                if self.parent._should_stop:
                    logger.info("Walk-Forward stopped by user")
                    break

                progress = int((i / total_folds) * 90) + 5
                self.parent._progress.emit_progress(
                    progress,
                    f"Fold {i+1}/{total_folds}: Train {train_start.date()} - {train_end.date()}"
                )

                try:
                    fold_result = await self.parent._fold_runner.run_fold(
                        fold_index=i,
                        train_start=train_start,
                        train_end=train_end,
                        test_start=test_start,
                        test_end=test_end,
                    )
                    self.parent._folds.append(fold_result)

                    if fold_result.is_successful:
                        successful += 1

                except Exception as e:
                    from .walk_forward_runner import FoldResult
                    logger.exception(f"Fold {i+1} failed")
                    self.parent._folds.append(FoldResult(
                        fold_index=i,
                        train_start=train_start,
                        train_end=train_end,
                        test_start=test_start,
                        test_end=test_end,
                        error=str(e),
                    ))

            # 3. Aggregation
            self.parent._progress.emit_progress(95, "Berechne aggregierte Metriken...")
            aggregated = self.parent._metrics.calculate_aggregated_metrics()
            stability = self.parent._metrics.calculate_stability_metrics()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            summary = WalkForwardSummary(
                wf_id=self.parent.wf_id,
                folds=self.parent._folds,
                total_folds=total_folds,
                successful_folds=successful,
                aggregated_metrics=aggregated,
                stability_metrics=stability,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
            )

            self.parent._progress.emit_progress(100, f"Fertig! {successful}/{total_folds} Folds erfolgreich")
            logger.info(f"Walk-Forward completed: {successful}/{total_folds} folds in {duration:.1f}s")

            return summary

        finally:
            self.parent._is_running = False

    def stop(self) -> None:
        """Stoppt die laufende Analyse."""
        self.parent._should_stop = True
