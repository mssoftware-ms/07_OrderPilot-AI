"""
BatchRunner V2 - Parameter Optimization with ConfigV2 Support

Erweitert den BatchRunner um Unterstuetzung fuer BacktestConfigV2:
- Laedt V2-Templates mit Extends-Support
- Expandiert Parameter-Gruppen und optimierbare Parameter
- Konvertiert V2-Config zu V1-Config fuer bestehende Runner
- Unterstuetzt alle V2-Features (Conditionals, Groups, etc.)

Usage:
    # Direkt aus V2-Template
    runner = BatchRunnerV2.from_template("trendfollowing_conservative")
    summary = await runner.run()

    # Aus V2-Config-Objekt
    config = load_config("config/backtest_templates/my_config.json")
    runner = BatchRunnerV2(config)
    summary = await runner.run()
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Union

from .config import BacktestConfig, BatchConfig, ExecutionConfig, SearchMethod
from .config_v2 import BacktestConfigV2, OptimizableFloat, OptimizableInt
from .config_loader import (
    ConfigLoader,
    GridSpaceGenerator,
    load_config,
    count_grid_combinations,
)
from .config_validator import ConfigValidator, ValidationResult
from .batch_runner import BatchRunner, BatchSummary, BatchRunResult

logger = logging.getLogger(__name__)


class ConfigV2Converter:
    """
    Konvertiert BacktestConfigV2 zu BacktestConfig (V1).

    Ermoeglicht die Nutzung der neuen V2-Konfigurationsstruktur mit
    dem bestehenden BacktestRunner.
    """

    @staticmethod
    def to_v1_config(
        v2_config: BacktestConfigV2,
        parameter_overrides: Optional[dict[str, Any]] = None
    ) -> BacktestConfig:
        """
        Konvertiert V2-Config zu V1-Config.

        Args:
            v2_config: V2-Konfiguration
            parameter_overrides: Optionale Parameter-Ueberschreibungen

        Returns:
            V1-kompatible BacktestConfig
        """
        # Basis-Werte aus V2 extrahieren
        v2_dict = v2_config.to_dict()

        # Parameter-Overrides anwenden
        if parameter_overrides:
            for path, value in parameter_overrides.items():
                ConfigV2Converter._set_nested_value(v2_dict, path, value)

        # Entry Score Weights extrahieren
        weights = v2_config.entry_score.get_weights()

        # V1-Config erstellen
        execution = ExecutionConfig(
            initial_capital=v2_config.execution_simulation.initial_capital,
            fee_maker_pct=v2_config.execution_simulation.fee_maker_pct,
            fee_taker_pct=v2_config.execution_simulation.fee_taker_pct,
            assume_taker=v2_config.execution_simulation.assume_taker,
            slippage_bps=v2_config.execution_simulation.slippage_bps,
        )

        # Entry Score Gates
        gates = v2_config.entry_score.gates

        # Risk/Leverage
        risk = v2_config.risk_leverage

        # Exit Management
        exit_mgmt = v2_config.exit_management

        v1_config = BacktestConfig(
            # Meta
            name=v2_config.meta.name,
            description=v2_config.meta.description,

            # Entry Score
            weight_trend_alignment=weights.trend,
            weight_rsi=weights.rsi,
            weight_macd=weights.macd,
            weight_adx=weights.adx,
            weight_volatility=weights.vol,
            weight_volume=weights.volume,
            min_score_for_entry=v2_config.entry_score.thresholds.min_score_for_entry.value,

            # Gates
            gate_block_in_chop=gates.block_in_chop,
            gate_block_against_strong_trend=gates.block_against_strong_trend,
            gate_allow_counter_trend_sfp=gates.allow_counter_trend_sfp,

            # Risk/Leverage
            risk_per_trade_pct=risk.risk_per_trade_pct.value,
            base_leverage=risk.base_leverage.value,
            max_leverage=risk.max_leverage,
            min_liquidation_distance_pct=risk.min_liquidation_distance_pct,
            max_daily_loss_pct=risk.max_daily_loss_pct,
            max_trades_per_day=risk.max_trades_per_day,

            # Stop Loss
            sl_type=exit_mgmt.stop_loss.type,
            sl_atr_multiplier=exit_mgmt.stop_loss.atr_multiplier.value,
            sl_percent=exit_mgmt.stop_loss.percent.value,

            # Take Profit
            tp_atr_multiplier=exit_mgmt.take_profit.atr_multiplier.value,
            tp_use_level=exit_mgmt.take_profit.use_level,

            # Trailing Stop
            trailing_enabled=exit_mgmt.trailing_stop.enabled,
            trailing_activation_atr=exit_mgmt.trailing_stop.activation_atr.value,
            trailing_distance_atr=exit_mgmt.trailing_stop.distance_atr.value,
            trailing_step_pct=exit_mgmt.trailing_stop.step_percent.value,
            trailing_move_to_be=exit_mgmt.trailing_stop.move_to_breakeven,

            # Execution
            execution=execution,

            # Parameter Overrides
            parameter_overrides=parameter_overrides or {},
        )

        return v1_config

    @staticmethod
    def _set_nested_value(data: dict, path: str, value: Any) -> None:
        """Setzt Wert in verschachteltem Dict."""
        keys = path.split(".")
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Handle OptimizableFloat/Int Struktur
        final_key = keys[-1]
        if isinstance(current.get(final_key), dict) and "value" in current[final_key]:
            current[final_key]["value"] = value
        else:
            current[final_key] = value


class BatchRunnerV2:
    """
    Batch-Runner mit voller V2-Config Unterstuetzung.

    Laedt V2-Templates, expandiert Parameter-Gruppen und optimierbare
    Parameter, und fuehrt Batch-Runs mit dem bestehenden BacktestRunner durch.

    Features:
    - Extends/Vererbungs-Support
    - Parameter-Gruppen-Expansion
    - Conditional-Aufloesung
    - Automatische V2 -> V1 Konvertierung
    """

    def __init__(
        self,
        config: BacktestConfigV2,
        signal_callback: Optional[Callable] = None,
        save_full_results: bool = False,
    ):
        """
        Initialisiert den BatchRunnerV2.

        Args:
            config: BacktestConfigV2-Konfiguration
            signal_callback: Signal-Callback fuer Backtests
            save_full_results: Vollstaendige Results speichern
        """
        self.config = config
        self.signal_callback = signal_callback
        self.save_full_results = save_full_results

        # Validierung
        self.validator = ConfigValidator()
        validation = self.validator.validate(config)
        if validation.has_warnings:
            for w in validation.warnings:
                logger.warning(f"Config warning: {w}")

        # Batch-ID
        self.batch_id = f"batch_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # State
        self._results: list[BatchRunResult] = []
        self._is_running = False
        self._should_stop = False
        self._progress_callback: Optional[Callable[[int, str], None]] = None

        # Grid-Info
        self._grid_count = count_grid_combinations(config)
        logger.info(f"BatchRunnerV2 initialized: {self._grid_count} potential combinations")

    @classmethod
    def from_template(
        cls,
        template_name: str,
        base_path: Optional[Path] = None,
        overrides: Optional[dict[str, Any]] = None,
        **kwargs
    ) -> "BatchRunnerV2":
        """
        Erstellt BatchRunnerV2 aus einem Template.

        Args:
            template_name: Template-Name (ohne .json)
            base_path: Basis-Pfad fuer Templates
            overrides: Optionale Ueberschreibungen
            **kwargs: Weitere Argumente fuer BatchRunnerV2

        Returns:
            BatchRunnerV2-Instanz
        """
        base_path = base_path or Path("config/backtest_templates")
        template_path = base_path / f"{template_name}.json"

        loader = ConfigLoader(base_path=base_path)
        config = loader.load(template_path)

        # Overrides anwenden
        if overrides:
            config_dict = config.to_dict()
            for path, value in overrides.items():
                ConfigV2Converter._set_nested_value(config_dict, path, value)
            config = BacktestConfigV2.from_dict(config_dict)

        return cls(config, **kwargs)

    @classmethod
    def from_file(
        cls,
        path: Union[str, Path],
        **kwargs
    ) -> "BatchRunnerV2":
        """
        Erstellt BatchRunnerV2 aus einer JSON-Datei.

        Args:
            path: Pfad zur JSON-Datei
            **kwargs: Weitere Argumente fuer BatchRunnerV2

        Returns:
            BatchRunnerV2-Instanz
        """
        config = load_config(Path(path))
        return cls(config, **kwargs)

    def set_progress_callback(self, callback: Callable[[int, str], None]) -> None:
        """Setzt Callback fuer Progress-Updates."""
        self._progress_callback = callback

    def _emit_progress(self, progress: int, message: str) -> None:
        """Emittiert Progress-Update."""
        if self._progress_callback:
            self._progress_callback(progress, message)

    def get_grid_count(self) -> int:
        """Gibt Anzahl der Grid-Kombinationen zurueck."""
        return self._grid_count

    async def run(self) -> BatchSummary:
        """
        Fuehrt den Batch-Run durch.

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
            # 1. Grid expandieren
            self._emit_progress(0, "Expandiere Parameter-Space...")
            variants = GridSpaceGenerator.generate(self.config)

            # Limit anwenden
            max_iter = self.config.optimization.max_iterations
            if len(variants) > max_iter:
                logger.info(f"Limiting {len(variants)} variants to {max_iter}")
                import random
                random.seed(self.config.optimization.seed)
                variants = random.sample(variants, max_iter)

            total_runs = len(variants)
            logger.info(f"Starting V2 batch run with {total_runs} variants")

            # 2. Runs ausfuehren
            successful = 0
            failed = 0

            for i, variant_dict in enumerate(variants):
                if self._should_stop:
                    logger.info("Batch stopped by user")
                    break

                progress = int((i / total_runs) * 90) + 5
                params_str = self._variant_to_string(variant_dict)
                self._emit_progress(progress, f"Run {i+1}/{total_runs}: {params_str}")

                try:
                    result = await self._run_single_variant(variant_dict, i)
                    self._results.append(result)

                    if result.error:
                        failed += 1
                    else:
                        successful += 1

                except Exception as e:
                    logger.exception(f"Run {i+1} failed")
                    self._results.append(BatchRunResult(
                        run_id=f"{self.batch_id}_run_{i:04d}",
                        parameters=self._extract_params(variant_dict),
                        error=str(e),
                    ))
                    failed += 1

            # 3. Ranking
            self._emit_progress(95, "Erstelle Ranking...")
            self._rank_results()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            summary = BatchSummary(
                batch_id=self.batch_id,
                config_summary={
                    "template": self.config.meta.name,
                    "strategy_type": self.config.strategy_profile.type,
                    "search_method": self.config.optimization.method,
                    "target_metric": self.config.optimization.target_metric,
                    "total_variants": total_runs,
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
            logger.info(f"V2 Batch completed: {successful} successful, {failed} failed in {duration:.1f}s")

            return summary

        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stoppt den laufenden Batch."""
        self._should_stop = True

    async def _run_single_variant(
        self,
        variant_dict: dict[str, Any],
        index: int
    ) -> BatchRunResult:
        """Fuehrt einen einzelnen Run mit einer Variante durch."""
        run_id = f"{self.batch_id}_run_{index:04d}"

        # V2-Config aus Variante erstellen
        v2_config = BacktestConfigV2.from_dict(variant_dict)

        # Parameter extrahieren (fuer Tracking)
        params = self._extract_params(variant_dict)

        # V1-Config erstellen
        v1_config = ConfigV2Converter.to_v1_config(v2_config, params)

        # V1-Batch-Config erstellen
        batch_config = BatchConfig(
            base_config=v1_config,
            search_method=SearchMethod.GRID,
            parameter_space={},  # Keine weitere Expansion
            target_metric=self.config.optimization.target_metric,
            minimize=self.config.optimization.minimize,
            max_iterations=1,
            seed=self.config.optimization.seed,
        )

        # Runner erstellen und ausfuehren
        from .backtest_runner import BacktestRunner

        runner = BacktestRunner(v1_config, signal_callback=self.signal_callback)

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

    def _extract_params(self, variant_dict: dict[str, Any]) -> dict[str, Any]:
        """Extrahiert relevante Parameter aus Variante fuer Tracking."""
        params = {}

        # Optimierbare Parameter extrahieren
        v2_config = BacktestConfigV2.from_dict(variant_dict)

        params["min_score"] = v2_config.entry_score.thresholds.min_score_for_entry.value
        params["sl_atr"] = v2_config.exit_management.stop_loss.atr_multiplier.value
        params["tp_atr"] = v2_config.exit_management.take_profit.atr_multiplier.value
        params["trail_act"] = v2_config.exit_management.trailing_stop.activation_atr.value
        params["trail_dist"] = v2_config.exit_management.trailing_stop.distance_atr.value
        params["risk_pct"] = v2_config.risk_leverage.risk_per_trade_pct.value
        params["leverage"] = v2_config.risk_leverage.base_leverage.value

        return params

    def _variant_to_string(self, variant_dict: dict[str, Any]) -> str:
        """Konvertiert Variante zu kurzem String."""
        params = self._extract_params(variant_dict)
        parts = [f"{k}={v}" for k, v in list(params.items())[:4]]
        return ", ".join(parts)

    def _rank_results(self) -> None:
        """Rankt Ergebnisse nach Zielmetrik."""
        target = self.config.optimization.target_metric
        minimize = self.config.optimization.minimize

        def get_metric_value(run: BatchRunResult) -> float:
            if run.metrics is None:
                return float('inf') if minimize else float('-inf')

            value = getattr(run.metrics, target, None)
            if value is None:
                return float('inf') if minimize else float('-inf')

            return float(value)

        self._results.sort(key=get_metric_value, reverse=not minimize)

    @property
    def results(self) -> list[BatchRunResult]:
        """Gibt alle Ergebnisse zurueck (gerankt)."""
        return self._results.copy()

    @property
    def best_result(self) -> Optional[BatchRunResult]:
        """Gibt bestes Ergebnis zurueck."""
        return self._results[0] if self._results else None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


async def run_batch_from_template(
    template_name: str,
    overrides: Optional[dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> BatchSummary:
    """
    Fuehrt Batch-Run aus einem Template durch.

    Args:
        template_name: Template-Name
        overrides: Optionale Ueberschreibungen
        progress_callback: Progress-Callback

    Returns:
        BatchSummary
    """
    runner = BatchRunnerV2.from_template(template_name, overrides=overrides)

    if progress_callback:
        runner.set_progress_callback(progress_callback)

    return await runner.run()


def preview_grid(template_name: str) -> dict[str, Any]:
    """
    Zeigt Vorschau des Grid-Spaces ohne Ausfuehrung.

    Args:
        template_name: Template-Name

    Returns:
        Dictionary mit Grid-Informationen
    """
    runner = BatchRunnerV2.from_template(template_name)

    return {
        "template": runner.config.meta.name,
        "strategy_type": runner.config.strategy_profile.type,
        "total_combinations": runner.get_grid_count(),
        "max_iterations": runner.config.optimization.max_iterations,
        "optimizable_params": list(runner.config.get_optimizable_parameters().keys()),
        "parameter_groups": [g.name for g in runner.config.parameter_groups],
    }
