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
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
import statistics

from .config import BacktestConfig, BatchConfig, WalkForwardConfig, SearchMethod
from .batch_runner import BatchRunner, BatchRunResult
from .backtest_runner import BacktestRunner
from src.core.models.backtest_models import BacktestResult, BacktestMetrics

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

        logger.info(
            f"WalkForwardRunner initialized: train={config.train_window_days}d, "
            f"test={config.test_window_days}d, step={config.step_size_days}d"
        )

    def set_progress_callback(self, callback: Callable[[int, str], None]) -> None:
        """Setzt Callback für Progress-Updates."""
        self._progress_callback = callback

    def _emit_progress(self, progress: int, message: str) -> None:
        """Emittiert Progress-Update."""
        if self._progress_callback:
            self._progress_callback(progress, message)

    def calculate_folds(self) -> list[tuple[datetime, datetime, datetime, datetime]]:
        """Berechnet die Fold-Zeiträume.

        Returns:
            Liste von (train_start, train_end, test_start, test_end) Tuples
        """
        base_config = self.config.base_config
        total_start = base_config.start_date
        total_end = base_config.end_date

        train_days = self.config.train_window_days
        test_days = self.config.test_window_days
        step_days = self.config.step_size_days

        folds = []
        current_start = total_start

        while True:
            train_start = current_start
            train_end = train_start + timedelta(days=train_days)
            test_start = train_end
            test_end = test_start + timedelta(days=test_days)

            # Prüfe ob Test-End noch innerhalb des Gesamtzeitraums liegt
            if test_end > total_end:
                # Letzter Fold - passe an
                if test_start < total_end:
                    test_end = total_end
                    folds.append((train_start, train_end, test_start, test_end))
                break

            folds.append((train_start, train_end, test_start, test_end))

            # Nächster Fold
            current_start = current_start + timedelta(days=step_days)

            # Stoppe wenn nicht genug Platz für Training
            if current_start + timedelta(days=train_days) > total_end:
                break

        # Mindest-Folds prüfen
        if len(folds) < self.config.min_folds:
            logger.warning(
                f"Only {len(folds)} folds possible (min: {self.config.min_folds}). "
                f"Consider shorter windows or longer data period."
            )

        return folds

    async def run(self) -> WalkForwardSummary:
        """Führt die Walk-Forward Analyse durch.

        Returns:
            WalkForwardSummary mit allen Fold-Ergebnissen
        """
        if self._is_running:
            raise RuntimeError("Walk-Forward already running")

        self._is_running = True
        self._should_stop = False
        self._folds.clear()

        start_time = datetime.now()

        try:
            # 1. Folds berechnen
            self._emit_progress(0, "Berechne Folds...")
            fold_periods = self.calculate_folds()
            total_folds = len(fold_periods)

            if total_folds == 0:
                raise ValueError("Keine Folds möglich mit den gegebenen Parametern")

            logger.info(f"Starting Walk-Forward with {total_folds} folds")

            # 2. Folds ausführen
            successful = 0

            for i, (train_start, train_end, test_start, test_end) in enumerate(fold_periods):
                if self._should_stop:
                    logger.info("Walk-Forward stopped by user")
                    break

                progress = int((i / total_folds) * 90) + 5
                self._emit_progress(
                    progress,
                    f"Fold {i+1}/{total_folds}: Train {train_start.date()} - {train_end.date()}"
                )

                try:
                    fold_result = await self._run_fold(
                        fold_index=i,
                        train_start=train_start,
                        train_end=train_end,
                        test_start=test_start,
                        test_end=test_end,
                    )
                    self._folds.append(fold_result)

                    if fold_result.is_successful:
                        successful += 1

                except Exception as e:
                    logger.exception(f"Fold {i+1} failed")
                    self._folds.append(FoldResult(
                        fold_index=i,
                        train_start=train_start,
                        train_end=train_end,
                        test_start=test_start,
                        test_end=test_end,
                        error=str(e),
                    ))

            # 3. Aggregation
            self._emit_progress(95, "Berechne aggregierte Metriken...")
            aggregated = self._calculate_aggregated_metrics()
            stability = self._calculate_stability_metrics()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            summary = WalkForwardSummary(
                wf_id=self.wf_id,
                folds=self._folds,
                total_folds=total_folds,
                successful_folds=successful,
                aggregated_metrics=aggregated,
                stability_metrics=stability,
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
            )

            self._emit_progress(100, f"Fertig! {successful}/{total_folds} Folds erfolgreich")
            logger.info(f"Walk-Forward completed: {successful}/{total_folds} folds in {duration:.1f}s")

            return summary

        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stoppt die laufende Analyse."""
        self._should_stop = True

    async def _run_fold(
        self,
        fold_index: int,
        train_start: datetime,
        train_end: datetime,
        test_start: datetime,
        test_end: datetime,
    ) -> FoldResult:
        """Führt einen einzelnen Fold durch."""
        from dataclasses import replace

        logger.info(f"Running fold {fold_index}: train={train_start.date()}-{train_end.date()}, test={test_start.date()}-{test_end.date()}")

        best_params = {}
        train_metrics = None
        optimization_runs = 0

        # 1. Training Phase (Optimierung)
        if self.config.reoptimize_each_fold:
            # Erstelle Training-Config
            train_config = replace(
                self.config.base_config,
                start_date=train_start,
                end_date=train_end,
            )

            # Batch-Config für Training
            batch_config = replace(
                self.config.batch_config,
                base_config=train_config,
            )

            # Optimierung durchführen
            batch_runner = BatchRunner(
                config=batch_config,
                signal_callback=self.signal_callback,
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
            best_params = self.config.base_config.parameter_overrides.copy()

        # 2. Test Phase (Out-of-Sample)
        test_config = replace(
            self.config.base_config,
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
            signal_callback=self.signal_callback,
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

    def _calculate_aggregated_metrics(self) -> dict[str, float]:
        """Berechnet aggregierte OOS-Metriken über alle Folds."""
        successful_folds = [f for f in self._folds if f.is_successful]

        if not successful_folds:
            return {}

        # Sammle Metriken
        metrics_lists: dict[str, list[float]] = {
            "expectancy": [],
            "profit_factor": [],
            "win_rate": [],
            "max_drawdown_pct": [],
            "total_return_pct": [],
            "sharpe_ratio": [],
            "total_trades": [],
        }

        for fold in successful_folds:
            m = fold.test_metrics
            if m.expectancy is not None:
                metrics_lists["expectancy"].append(m.expectancy)
            if m.profit_factor is not None and m.profit_factor < float('inf'):
                metrics_lists["profit_factor"].append(m.profit_factor)
            metrics_lists["win_rate"].append(m.win_rate)
            metrics_lists["max_drawdown_pct"].append(m.max_drawdown_pct)
            metrics_lists["total_return_pct"].append(m.total_return_pct)
            if m.sharpe_ratio is not None:
                metrics_lists["sharpe_ratio"].append(m.sharpe_ratio)
            metrics_lists["total_trades"].append(float(m.total_trades))

        # Aggregieren (Mittelwert)
        aggregated = {}
        for metric, values in metrics_lists.items():
            if values:
                aggregated[f"avg_{metric}"] = statistics.mean(values)
                aggregated[f"min_{metric}"] = min(values)
                aggregated[f"max_{metric}"] = max(values)

        # Gesamte OOS-Performance
        total_trades = sum(int(f.test_metrics.total_trades) for f in successful_folds)
        total_winners = sum(f.test_metrics.winning_trades for f in successful_folds)
        aggregated["combined_win_rate"] = total_winners / total_trades if total_trades > 0 else 0

        return aggregated

    def _calculate_stability_metrics(self) -> dict[str, float]:
        """Berechnet Stabilitätsmetriken über alle Folds.

        Niedrigere Werte = stabilere Performance.
        """
        successful_folds = [f for f in self._folds if f.is_successful]

        if len(successful_folds) < 2:
            return {}

        stability = {}

        # Coefficient of Variation für wichtige Metriken
        metrics_to_check = ["expectancy", "profit_factor", "total_return_pct"]

        for metric in metrics_to_check:
            values = []
            for fold in successful_folds:
                m = fold.test_metrics
                val = getattr(m, metric, None)
                if val is not None and val != float('inf') and val != float('-inf'):
                    values.append(val)

            if len(values) >= 2:
                mean = statistics.mean(values)
                std = statistics.stdev(values)

                # Coefficient of Variation (CV)
                cv = (std / abs(mean)) if mean != 0 else float('inf')
                stability[f"{metric}_cv"] = cv
                stability[f"{metric}_std"] = std

        # Worst Fold Performance
        worst_fold_return = min(f.test_metrics.total_return_pct for f in successful_folds)
        stability["worst_fold_return_pct"] = worst_fold_return

        # Profitable Folds Ratio
        profitable_folds = sum(1 for f in successful_folds if f.test_metrics.total_return_pct > 0)
        stability["profitable_folds_ratio"] = profitable_folds / len(successful_folds)

        return stability

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
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exports = {}

        # 1. Summary JSON
        summary = WalkForwardSummary(
            wf_id=self.wf_id,
            folds=self._folds,
            total_folds=len(self._folds),
            successful_folds=sum(1 for f in self._folds if f.is_successful),
            aggregated_metrics=self._calculate_aggregated_metrics(),
            stability_metrics=self._calculate_stability_metrics(),
        )

        summary_path = output_dir / f"{self.wf_id}_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary.to_dict(), f, indent=2, default=str)
        exports["summary"] = summary_path

        # 2. Folds CSV
        folds_path = output_dir / f"{self.wf_id}_folds.csv"
        with open(folds_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "fold", "train_period", "test_period",
                "oos_trades", "oos_win_rate", "oos_pf", "oos_expectancy",
                "oos_return_pct", "oos_max_dd", "opt_runs", "error"
            ])

            # Data
            for fold in self._folds:
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
        folds_dir = output_dir / f"{self.wf_id}_folds"
        folds_dir.mkdir(exist_ok=True)

        for fold in self._folds:
            fold_path = folds_dir / f"fold_{fold.fold_index:02d}.json"
            with open(fold_path, "w") as f:
                json.dump(fold.to_dict(), f, indent=2, default=str)

        exports["folds_dir"] = folds_dir

        logger.info(f"Exported Walk-Forward results to {output_dir}")
        return exports

    @property
    def folds(self) -> list[FoldResult]:
        """Gibt alle Fold-Ergebnisse zurück."""
        return self._folds.copy()
