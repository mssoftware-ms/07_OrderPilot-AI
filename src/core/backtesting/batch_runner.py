"""
BatchRunner - Parameter Optimization via Grid/Random Search

Führt mehrere Backtests mit verschiedenen Parameter-Kombinationen durch:
- Grid Search: Alle Kombinationen aus Parameter-Space
- Random Search: Zufällige Stichprobe aus Parameter-Space
- Ranking nach Zielmetrik (Expectancy, Profit Factor, etc.)
- Export der Top-N Ergebnisse

Features:
- Reproduzierbar via Seed
- Parallel-Execution Option (optional)
- Progress Tracking
- Result Aggregation und Ranking
"""

from __future__ import annotations

import asyncio
import csv
import itertools
import json
import logging
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .config import BacktestConfig, BatchConfig, SearchMethod
from .backtest_runner import BacktestRunner
from src.core.models.backtest_models import BacktestResult, BacktestMetrics

logger = logging.getLogger(__name__)


@dataclass
class BatchRunResult:
    """Ergebnis eines einzelnen Batch-Runs.

    Attributes:
        run_id: Eindeutige Run-ID
        parameters: Verwendete Parameter
        metrics: Performance-Metriken
        result: Vollständiges BacktestResult (optional, bei save_full_results)
        error: Fehlermeldung wenn Run fehlgeschlagen
    """
    run_id: str
    parameters: dict[str, Any]
    metrics: BacktestMetrics | None = None
    result: BacktestResult | None = None
    error: str | None = None

    @property
    def target_value(self) -> float:
        """Zielmetrik-Wert für Ranking."""
        if self.metrics is None:
            return float('-inf')
        return 0.0  # Wird vom BatchRunner gesetzt

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary für Export."""
        return {
            "run_id": self.run_id,
            "parameters": self.parameters,
            "metrics": self.metrics.model_dump() if self.metrics else None,
            "error": self.error,
        }


@dataclass
class BatchSummary:
    """Zusammenfassung eines Batch-Runs.

    Attributes:
        batch_id: Eindeutige Batch-ID
        config: Batch-Konfiguration
        total_runs: Gesamtanzahl Runs
        successful_runs: Erfolgreiche Runs
        failed_runs: Fehlgeschlagene Runs
        best_run: Bester Run
        top_runs: Top-N Runs
        start_time: Startzeit
        end_time: Endzeit
        duration_seconds: Laufzeit in Sekunden
    """
    batch_id: str
    config_summary: dict[str, Any]
    total_runs: int
    successful_runs: int
    failed_runs: int
    best_run: BatchRunResult | None
    top_runs: list[BatchRunResult]
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary für Export."""
        return {
            "batch_id": self.batch_id,
            "config_summary": self.config_summary,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "best_run": self.best_run.to_dict() if self.best_run else None,
            "top_runs_count": len(self.top_runs),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
        }


class BatchRunner:
    """Batch-Runner für Parameter-Optimierung.

    Führt multiple Backtests mit verschiedenen Parameter-Kombinationen durch
    und rankt die Ergebnisse nach einer Zielmetrik.

    Usage:
        # Grid Search
        config = BatchConfig(
            base_config=backtest_config,
            search_method=SearchMethod.GRID,
            parameter_space={
                "risk_per_trade_pct": [0.5, 1.0, 1.5, 2.0],
                "max_leverage": [5, 10, 20],
            },
            target_metric="expectancy",
        )

        runner = BatchRunner(config)
        summary = await runner.run()

        # Top 10 Ergebnisse
        for run in summary.top_runs[:10]:
            print(f"Params: {run.parameters} -> {run.metrics.expectancy}")
    """

    def __init__(
        self,
        config: BatchConfig,
        signal_callback: Callable | None = None,
        save_full_results: bool = False,
    ):
        """Initialisiert den Batch-Runner.

        Args:
            config: Batch-Konfiguration
            signal_callback: Signal-Callback für Backtests
            save_full_results: Vollständige Results speichern (mehr Speicher)
        """
        self.config = config
        self.signal_callback = signal_callback
        self.save_full_results = save_full_results

        # State
        self._results: list[BatchRunResult] = []
        self._is_running = False
        self._should_stop = False
        self._progress_callback: Callable[[int, str], None] | None = None

        # Batch ID
        self.batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"BatchRunner initialized: method={config.search_method.value}, target={config.target_metric}")

    def set_progress_callback(self, callback: Callable[[int, str], None]) -> None:
        """Setzt Callback für Progress-Updates."""
        self._progress_callback = callback

    def _emit_progress(self, progress: int, message: str) -> None:
        """Emittiert Progress-Update."""
        if self._progress_callback:
            self._progress_callback(progress, message)

    def generate_parameter_combinations(self) -> list[dict[str, Any]]:
        """Generiert Parameter-Kombinationen basierend auf Search Method.

        Returns:
            Liste von Parameter-Dictionaries
        """
        param_space = self.config.parameter_space

        if not param_space:
            return [{}]  # Keine Parameter zum Variieren

        if self.config.search_method == SearchMethod.GRID:
            return self._generate_grid_combinations(param_space)
        elif self.config.search_method == SearchMethod.RANDOM:
            return self._generate_random_combinations(param_space)
        elif self.config.search_method == SearchMethod.BAYESIAN:
            # Bayesian wird Run-by-Run generiert, starte mit Random
            return self._generate_random_combinations(param_space)
        else:
            return self._generate_grid_combinations(param_space)

    def _generate_grid_combinations(self, param_space: dict[str, list[Any]]) -> list[dict[str, Any]]:
        """Generiert Grid-Kombinationen mit Speicherschutz.

        Bei zu vielen Kombinationen wird automatisch auf Random-Sampling umgeschaltet.
        """
        keys = list(param_space.keys())
        values = [param_space[k] for k in keys]

        # KRITISCH: Berechne theoretische Anzahl VORHER um MemoryError zu vermeiden
        import math
        theoretical_count = math.prod(len(v) for v in values)
        max_combinations = self.config.max_iterations

        logger.info(f"Grid search: {len(keys)} params, theoretical {theoretical_count:,} combinations, limit {max_combinations}")

        # Wenn theoretische Anzahl zu groß, verwende Random-Sampling statt volles Grid
        if theoretical_count > max_combinations * 10:  # 10x Buffer für Sicherheit
            logger.warning(
                f"⚠️ Grid würde {theoretical_count:,} Kombinationen erzeugen - "
                f"wechsle zu Random-Sampling mit {max_combinations} Iterationen"
            )
            return self._generate_random_combinations(param_space)

        # Generiere mit Limit - stoppe früh wenn max erreicht
        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo)))
            if len(combinations) >= max_combinations:
                logger.info(f"Grid generation stopped at limit: {max_combinations}")
                break

        logger.info(f"Generated {len(combinations)} grid combinations")
        return combinations

    def _generate_random_combinations(self, param_space: dict[str, list[Any]]) -> list[dict[str, Any]]:
        """Generiert Random-Kombinationen."""
        random.seed(self.config.seed)

        keys = list(param_space.keys())
        max_iter = self.config.max_iterations

        combinations = []
        for _ in range(max_iter):
            combo = {}
            for key in keys:
                combo[key] = random.choice(param_space[key])
            combinations.append(combo)

        logger.info(f"Generated {len(combinations)} random combinations")
        return combinations

    async def run(self) -> BatchSummary:
        """Führt den Batch-Run durch.

        Returns:
            BatchSummary mit allen Ergebnissen
        """
        if self._is_running:
            raise RuntimeError("Batch already running")

        self._is_running = True
        self._should_stop = False
        self._results.clear()

        start_time = datetime.now()

        try:
            # 1. Parameter-Kombinationen generieren
            self._emit_progress(0, "Generiere Parameter-Kombinationen...")
            combinations = self.generate_parameter_combinations()

            # Limitiere auf max_iterations
            if len(combinations) > self.config.max_iterations:
                combinations = combinations[:self.config.max_iterations]

            total_runs = len(combinations)
            logger.info(f"Starting batch run with {total_runs} combinations")

            # 2. Runs ausführen
            successful = 0
            failed = 0

            for i, params in enumerate(combinations):
                if self._should_stop:
                    logger.info("Batch stopped by user")
                    break

                progress = int((i / total_runs) * 90) + 5
                self._emit_progress(progress, f"Run {i+1}/{total_runs}: {self._params_to_string(params)}")

                try:
                    result = await self._run_single(params, i)
                    self._results.append(result)

                    if result.error:
                        failed += 1
                    else:
                        successful += 1

                except Exception as e:
                    logger.exception(f"Run {i+1} failed")
                    self._results.append(BatchRunResult(
                        run_id=f"{self.batch_id}_run_{i:04d}",
                        parameters=params,
                        error=str(e),
                    ))
                    failed += 1

            # 3. Ranking und Summary
            self._emit_progress(95, "Erstelle Ranking...")
            self._rank_results()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            summary = BatchSummary(
                batch_id=self.batch_id,
                config_summary={
                    "search_method": self.config.search_method.value,
                    "target_metric": self.config.target_metric,
                    "parameter_space": {k: str(v) for k, v in self.config.parameter_space.items()},
                    "seed": self.config.seed,
                },
                total_runs=len(self._results),
                successful_runs=successful,
                failed_runs=failed,
                best_run=self._results[0] if self._results else None,
                top_runs=self._results[:10],
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
            )

            self._emit_progress(100, f"Fertig! {successful} erfolgreiche Runs")
            logger.info(f"Batch completed: {successful} successful, {failed} failed in {duration:.1f}s")

            return summary

        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stoppt den laufenden Batch."""
        self._should_stop = True

    async def _run_single(self, params: dict[str, Any], index: int) -> BatchRunResult:
        """Führt einen einzelnen Run durch."""
        run_id = f"{self.batch_id}_run_{index:04d}"

        # Config mit Parameter-Overrides erstellen
        config = self._create_config_with_params(params)

        # Runner erstellen und ausführen
        runner = BacktestRunner(config, signal_callback=self.signal_callback)

        try:
            result = await runner.run()

            return BatchRunResult(
                run_id=run_id,
                parameters=params,
                metrics=result.metrics,
                result=result if self.save_full_results else None,
            )

        except Exception as e:
            logger.warning(f"Run {run_id} failed: {e}")
            return BatchRunResult(
                run_id=run_id,
                parameters=params,
                error=str(e),
            )

    def _create_config_with_params(self, params: dict[str, Any]) -> BacktestConfig:
        """Erstellt BacktestConfig mit Parameter-Overrides."""
        from dataclasses import replace

        config = self.config.base_config

        # Parameter auf Config anwenden
        updates = {}
        for key, value in params.items():
            if hasattr(config, key):
                updates[key] = value
            elif hasattr(config.execution, key):
                # Execution-Parameter separat behandeln
                pass

        if updates:
            config = replace(config, **updates)

        # Execution-Parameter
        exec_updates = {}
        for key, value in params.items():
            if hasattr(config.execution, key):
                exec_updates[key] = value

        if exec_updates:
            from .config import ExecutionConfig
            new_exec = replace(config.execution, **exec_updates)
            config = replace(config, execution=new_exec)

        # Parameter Overrides speichern
        config = replace(config, parameter_overrides=params)

        return config

    def _rank_results(self) -> None:
        """Rankt Ergebnisse nach Zielmetrik."""
        target = self.config.target_metric
        minimize = self.config.minimize

        def get_metric_value(run: BatchRunResult) -> float:
            if run.metrics is None:
                return float('inf') if minimize else float('-inf')

            value = getattr(run.metrics, target, None)
            if value is None:
                return float('inf') if minimize else float('-inf')

            return float(value)

        self._results.sort(key=get_metric_value, reverse=not minimize)

    def _params_to_string(self, params: dict[str, Any]) -> str:
        """Konvertiert Parameter zu kurzem String."""
        if not params:
            return "default"
        parts = [f"{k}={v}" for k, v in list(params.items())[:3]]
        return ", ".join(parts)

    async def export_results(
        self,
        output_dir: Path | str,
        export_all_runs: bool = False,
    ) -> dict[str, Path]:
        """Exportiert Ergebnisse.

        Args:
            output_dir: Ausgabeverzeichnis
            export_all_runs: Alle Runs exportieren (nicht nur Top-N)

        Returns:
            Dictionary mit Export-Pfaden
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exports = {}

        # 1. Summary JSON
        summary_path = output_dir / f"{self.batch_id}_summary.json"
        summary_data = {
            "batch_id": self.batch_id,
            "total_runs": len(self._results),
            "target_metric": self.config.target_metric,
            "search_method": self.config.search_method.value,
        }
        with open(summary_path, "w") as f:
            json.dump(summary_data, f, indent=2, default=str)
        exports["summary"] = summary_path

        # 2. Results CSV
        results_path = output_dir / f"{self.batch_id}_results.csv"
        runs_to_export = self._results if export_all_runs else self._results[:20]

        with open(results_path, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            if runs_to_export:
                param_keys = list(runs_to_export[0].parameters.keys())
                metric_keys = ["total_trades", "win_rate", "profit_factor", "expectancy",
                              "max_drawdown_pct", "total_return_pct"]
                writer.writerow(["rank", "run_id"] + param_keys + metric_keys + ["error"])

                # Data
                for rank, run in enumerate(runs_to_export, 1):
                    param_values = [run.parameters.get(k, "") for k in param_keys]

                    if run.metrics:
                        metric_values = [
                            run.metrics.total_trades,
                            f"{run.metrics.win_rate:.3f}",
                            f"{run.metrics.profit_factor:.2f}",
                            f"{run.metrics.expectancy:.2f}" if run.metrics.expectancy else "",
                            f"{run.metrics.max_drawdown_pct:.2f}",
                            f"{run.metrics.total_return_pct:.2f}",
                        ]
                    else:
                        metric_values = [""] * len(metric_keys)

                    writer.writerow([rank, run.run_id] + param_values + metric_values + [run.error or ""])

        exports["results"] = results_path

        # 3. Top Params JSON
        if self._results:
            top_path = output_dir / f"{self.batch_id}_top_params.json"
            top_data = []
            for run in self._results[:5]:
                if run.metrics:
                    top_data.append({
                        "parameters": run.parameters,
                        "expectancy": run.metrics.expectancy,
                        "profit_factor": run.metrics.profit_factor,
                        "win_rate": run.metrics.win_rate,
                        "total_return_pct": run.metrics.total_return_pct,
                    })

            with open(top_path, "w") as f:
                json.dump(top_data, f, indent=2)
            exports["top_params"] = top_path

        logger.info(f"Exported batch results to {output_dir}")
        return exports

    @property
    def results(self) -> list[BatchRunResult]:
        """Gibt alle Ergebnisse zurück (gerankt)."""
        return self._results.copy()

    @property
    def best_result(self) -> BatchRunResult | None:
        """Gibt bestes Ergebnis zurück."""
        return self._results[0] if self._results else None
