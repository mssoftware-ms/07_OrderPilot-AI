"""Score Calculation Worker Thread.

Calculates scores for all strategies in background without blocking UI.
Emits progress signals and supports cancellation.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from src.core.tradingbot.strategy_settings_pipeline import StrategySettingsPipeline

logger = logging.getLogger(__name__)


class ScoreCalculationWorker(QThread):
    """Background worker for strategy score calculation.

    Signals:
        progress: (current, total, strategy_name) - Progress update
        score_calculated: (row, score_data) - Single strategy scored
        finished_all: (success_count, error_count) - All strategies completed
        error: (error_message) - Fatal error occurred
    """

    progress = pyqtSignal(int, int, str)  # current, total, name
    score_calculated = pyqtSignal(int, dict)  # row, score_data
    finished_all = pyqtSignal(int, int)  # success_count, error_count
    error = pyqtSignal(str)  # error_message

    def __init__(
        self,
        pipeline: StrategySettingsPipeline,
        strategies: dict,
        candles: list[dict],
        features: any,
        chart_window: any,
        json_dir: Path,
        row_mapping: dict[int, str]  # row -> strategy_id
    ):
        super().__init__()
        self.pipeline = pipeline
        self.strategies = strategies
        self.candles = candles
        self.features = features
        self.chart_window = chart_window
        self.json_dir = json_dir
        self.row_mapping = row_mapping
        self._is_cancelled = False

    def run(self) -> None:
        """Execute score calculation for all strategies."""
        success_count = 0
        error_count = 0
        total = len(self.row_mapping)

        for idx, (row, strategy_id) in enumerate(self.row_mapping.items(), 1):
            if self._is_cancelled:
                logger.info("Score calculation cancelled by user")
                self.finished_all.emit(success_count, error_count)
                return

            # Get strategy name for progress
            config = self.strategies.get(strategy_id, {})
            strat = config.get("strategies", [{}])[0]
            strategy_name = strat.get("name", strategy_id)

            # Emit progress
            self.progress.emit(idx, total, strategy_name)

            json_path = self.json_dir / f"{strategy_id}.json"

            try:
                # Run pipeline
                result = self.pipeline.run(
                    json_path=json_path,
                    candles=self.candles,
                    features=self.features,
                    chart_window=self.chart_window
                )

                # Prepare score data
                score_data = {
                    "total_score": result.score.total_score,
                    "regime_match_score": result.score.regime_match_score,
                    "entry_signal_score": result.score.entry_signal_score,
                    "data_quality_score": result.score.data_quality_score,
                    "explain": result.score.explain
                }

                # Emit result
                self.score_calculated.emit(row, score_data)
                success_count += 1

            except Exception as e:
                logger.error(f"Score calculation failed for {strategy_name}: {e}")
                error_count += 1
                continue

        self.finished_all.emit(success_count, error_count)

    def cancel(self) -> None:
        """Request cancellation of the calculation."""
        self._is_cancelled = True
