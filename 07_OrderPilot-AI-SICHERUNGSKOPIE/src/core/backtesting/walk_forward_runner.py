"""
WalkForwardRunner - Out-of-Sample Validation mit Rolling Windows

Walk-Forward Analyse mit Train/Test Split:
- Training Window: Parameter-Optimierung
- Test Window: Out-of-Sample Validation
- Rolling: Schrittweises Vorrücken

Features:
- Verhindert Overfitting durch OOS-Validation
- Stabilitätsmetriken über Folds
- Export von Fold-Reports
- Aggregierte Performance

REFACTORED: Split into focused helper modules.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.models.backtest_models import BacktestMetrics, BacktestResult

from .config import BacktestConfig, BatchConfig, SearchMethod, WalkForwardConfig

# Import helpers
from .walk_forward_executor import WalkForwardExecutor
from .walk_forward_export import WalkForwardExport
from .walk_forward_fold_calculator import WalkForwardFoldCalculator
from .walk_forward_fold_runner import WalkForwardFoldRunner
from .walk_forward_metrics import WalkForwardMetrics
from .walk_forward_progress import WalkForwardProgress

logger = logging.getLogger(__name__)


@dataclass
class FoldResult:
    """Ergebnis eines einzelnen Walk-Forward Folds.

    Attributes:
        fold_index: Fold-Nummer (0-basiert)
        train_start: Training Start-Datum
        train_end: Training End-Datum
        test_start: Test Start-Datum
        test_end: Test End-Datum
        best_params: Beste Parameter aus Training
        train_metrics: Metriken auf Trainingsdaten
        test_metrics: Metriken auf Testdaten (OOS)
        test_result: Vollständiges Test-Ergebnis
        optimization_runs: Anzahl Optimierungs-Runs
        error: Fehlermeldung wenn Fold fehlgeschlagen
    """
    fold_index: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    best_params: dict[str, Any] = field(default_factory=dict)
    train_metrics: BacktestMetrics | None = None
    test_metrics: BacktestMetrics | None = None
    test_result: BacktestResult | None = None
    optimization_runs: int = 0
    error: str | None = None

    @property
    def is_successful(self) -> bool:
        """True wenn Fold erfolgreich."""
        return self.error is None and self.test_metrics is not None

    @property
    def oos_expectancy(self) -> float | None:
        """Out-of-Sample Expectancy."""
        return self.test_metrics.expectancy if self.test_metrics else None

    @property
    def oos_profit_factor(self) -> float | None:
        """Out-of-Sample Profit Factor."""
        return self.test_metrics.profit_factor if self.test_metrics else None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "fold_index": self.fold_index,
            "train_period": f"{self.train_start.date()} - {self.train_end.date()}",
            "test_period": f"{self.test_start.date()} - {self.test_end.date()}",
            "best_params": self.best_params,
            "train_metrics": self.train_metrics.model_dump() if self.train_metrics else None,
            "test_metrics": self.test_metrics.model_dump() if self.test_metrics else None,
            "optimization_runs": self.optimization_runs,
            "error": self.error,
        }


@dataclass
class WalkForwardSummary:
    """Zusammenfassung der Walk-Forward Analyse.

    Attributes:
        wf_id: Walk-Forward ID
        folds: Liste aller Fold-Ergebnisse
        total_folds: Gesamtanzahl Folds
        successful_folds: Erfolgreiche Folds
        aggregated_metrics: Aggregierte OOS-Metriken
        stability_metrics: Stabilitätsmetriken
        start_time: Startzeit der Analyse
        end_time: Endzeit der Analyse
        duration_seconds: Gesamtlaufzeit
    """
    wf_id: str
    folds: list[FoldResult]
    total_folds: int
    successful_folds: int
    aggregated_metrics: dict[str, float] = field(default_factory=dict)
    stability_metrics: dict[str, float] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    duration_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        """Erfolgsrate der Folds."""
        return self.successful_folds / self.total_folds if self.total_folds > 0 else 0

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "wf_id": self.wf_id,
            "total_folds": self.total_folds,
            "successful_folds": self.successful_folds,
            "success_rate": f"{self.success_rate:.1%}",
            "aggregated_metrics": self.aggregated_metrics,
            "stability_metrics": self.stability_metrics,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
        }


class WalkForwardRunner:
    """Walk-Forward Analyse Runner.

    Führt Walk-Forward Analyse mit rollenden Train/Test Windows durch:
    1. Train Window: Optimiere Parameter via BatchRunner
    2. Test Window: Validiere beste Parameter out-of-sample
    3. Roll Forward: Verschiebe Windows und wiederhole

    Dies verhindert Overfitting und liefert realistische Performance-Schätzungen.

    Usage:
        config = WalkForwardConfig(
            base_config=backtest_config,
            batch_config=batch_config,
            train_window_days=90,
            test_window_days=30,
            step_size_days=30,
        )

        runner = WalkForwardRunner(config)
        summary = await runner.run()

        # Aggregierte OOS-Performance
        print(f"Avg OOS Expectancy: {summary.aggregated_metrics['expectancy']}")
        print(f"Stability: {summary.stability_metrics['expectancy_cv']}")  # Coefficient of Variation
    """

    def __init__(
        self,
        config: WalkForwardConfig,
        signal_callback: Callable | None = None,
    ):
        """Initialisiert den Walk-Forward Runner.

        Args:
            config: Walk-Forward Konfiguration
            signal_callback: Signal-Callback für Backtests
        """
        self.config = config
        self.signal_callback = signal_callback

        # State
        self._folds: list[FoldResult] = []
        self._is_running = False
        self._should_stop = False
        self._progress_callback: Callable[[int, str], None] | None = None

        # WF ID
        self.wf_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize helpers
        self._fold_calculator = WalkForwardFoldCalculator(parent=self)
        self._progress = WalkForwardProgress(parent=self)
        self._executor = WalkForwardExecutor(parent=self)
        self._fold_runner = WalkForwardFoldRunner(parent=self)
        self._metrics = WalkForwardMetrics(parent=self)
        self._export = WalkForwardExport(parent=self)

        logger.info(
            f"WalkForwardRunner initialized: train={config.train_window_days}d, "
            f"test={config.test_window_days}d, step={config.step_size_days}d"
        )

    def set_progress_callback(self, callback: Callable[[int, str], None]) -> None:
        """Setzt Callback für Progress-Updates."""
        self._progress.set_progress_callback(callback)

    def calculate_folds(self) -> list[tuple[datetime, datetime, datetime, datetime]]:
        """Berechnet die Fold-Zeiträume."""
        return self._fold_calculator.calculate_folds()

    async def run(self) -> WalkForwardSummary:
        """Führt die Walk-Forward Analyse durch."""
        return await self._executor.run()

    def stop(self) -> None:
        """Stoppt die laufende Analyse."""
        self._executor.stop()

    async def export_results(
        self,
        output_dir: Path | str,
    ) -> dict[str, Path]:
        """Exportiert Ergebnisse."""
        return await self._export.export_results(output_dir)

    @property
    def folds(self) -> list[FoldResult]:
        """Gibt alle Fold-Ergebnisse zurück."""
        return self._folds.copy()
