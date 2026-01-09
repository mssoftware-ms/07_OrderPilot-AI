"""Walk-Forward Runner - Individual Fold Execution.

Refactored from walk_forward_runner.py monolith.

Module 4/6 of walk_forward_runner.py split.

Contains:
- Individual fold execution (train phase + test phase)
"""

from __future__ import annotations

import logging
from datetime import datetime

from .batch_runner import BatchRunner
from .backtest_runner import BacktestRunner

logger = logging.getLogger(__name__)


class WalkForwardFoldRunner:
    """Helper für WalkForwardRunner individual fold execution."""

    def __init__(self, parent):
        """
        Args:
            parent: WalkForwardRunner Instanz
        """
        self.parent = parent

    async def run_fold(
        self,
        fold_index: int,
        train_start: datetime,
        train_end: datetime,
        test_start: datetime,
        test_end: datetime,
    ):
        """Führt einen einzelnen Fold durch."""
        from dataclasses import replace
        from .walk_forward_runner import FoldResult

        logger.info(f"Running fold {fold_index}: train={train_start.date()}-{train_end.date()}, test={test_start.date()}-{test_end.date()}")

        best_params = {}
        train_metrics = None
        optimization_runs = 0

        # 1. Training Phase (Optimierung)
        if self.parent.config.reoptimize_each_fold:
            # Erstelle Training-Config
            train_config = replace(
                self.parent.config.base_config,
                start_date=train_start,
                end_date=train_end,
            )

            # Batch-Config für Training
            batch_config = replace(
                self.parent.config.batch_config,
                base_config=train_config,
            )

            # Optimierung durchführen
            batch_runner = BatchRunner(
                config=batch_config,
                signal_callback=self.parent.signal_callback,
            )

            batch_summary = await batch_runner.run()
            optimization_runs = batch_summary.total_runs

            if batch_summary.best_run and batch_summary.best_run.metrics:
                best_params = batch_summary.best_run.parameters
                train_metrics = batch_summary.best_run.metrics
            else:
                # Kein erfolgreicher Run - verwende Default
                best_params = {}
                logger.warning(f"Fold {fold_index}: No successful optimization run")

        else:
            # Keine Re-Optimierung - verwende Parameter-Overrides aus Base-Config
            best_params = self.parent.config.base_config.parameter_overrides.copy()

        # 2. Test Phase (Out-of-Sample)
        test_config = replace(
            self.parent.config.base_config,
            start_date=test_start,
            end_date=test_end,
            parameter_overrides=best_params,
        )

        # Parameter anwenden
        for key, value in best_params.items():
            if hasattr(test_config, key):
                test_config = replace(test_config, **{key: value})

        test_runner = BacktestRunner(
            config=test_config,
            signal_callback=self.parent.signal_callback,
        )

        test_result = await test_runner.run()

        return FoldResult(
            fold_index=fold_index,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
            best_params=best_params,
            train_metrics=train_metrics,
            test_metrics=test_result.metrics,
            test_result=test_result,
            optimization_runs=optimization_runs,
        )
