"""
Backtesting Configuration - Zentrale Konfigurationsklassen

Alle Parameter für Backtesting, Execution Simulation, Batch-Tests und Walk-Forward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any


class SearchMethod(Enum):
    """Suchmethode für Batch-Tests."""
    GRID = "grid"
    RANDOM = "random"
    BAYESIAN = "bayesian"  # Optional: Optuna


class SlippageMethod(Enum):
    """Slippage-Berechnungsmethode."""
    FIXED_BPS = "fixed_bps"  # Fixe Basis-Punkte
    ATR_BASED = "atr_based"  # ATR-Anteil
    VOLUME_ADJUSTED = "volume_adjusted"  # Volumen-abhängig


@dataclass
class ExecutionConfig:
    """Konfiguration für realistische Trade-Ausführung.

    Attributes:
        fee_rate_maker: Maker-Fee in Prozent (z.B. 0.02 = 0.02%)
        fee_rate_taker: Taker-Fee in Prozent (z.B. 0.06 = 0.06%)
        slippage_method: Slippage-Berechnungsmethode
        slippage_bps: Slippage in Basis-Punkten (für FIXED_BPS)
        slippage_atr_mult: ATR-Multiplikator für Slippage (für ATR_BASED)
        max_leverage: Maximaler Hebel erlaubt
        liquidation_buffer_pct: Sicherheitspuffer vor Liquidation
        funding_rate_8h: 8h Funding Rate für Perpetuals (optional)
    """
    fee_rate_maker: float = 0.02  # 0.02% = 2bps
    fee_rate_taker: float = 0.06  # 0.06% = 6bps
    slippage_method: SlippageMethod = SlippageMethod.FIXED_BPS
    slippage_bps: float = 5.0  # 5 Basis-Punkte
    slippage_atr_mult: float = 0.1  # 10% des ATR
    max_leverage: int = 20
    liquidation_buffer_pct: float = 5.0  # 5% Puffer
    funding_rate_8h: float = 0.01  # 0.01% alle 8h (optional)
    assume_taker: bool = True  # Market Orders = Taker


@dataclass
class BacktestConfig:
    """Konfiguration für einen einzelnen Backtest.

    Attributes:
        symbol: Trading-Symbol (z.B. "BTCUSDT")
        start_date: Startdatum für Backtest
        end_date: Enddatum für Backtest
        initial_capital: Startkapital in USDT
        base_timeframe: Basis-Timeframe (meist "1m")
        mtf_timeframes: Multi-Timeframe Liste
        execution: Execution-Konfiguration
        risk_per_trade_pct: Risiko pro Trade in %
        max_daily_loss_pct: Maximaler Tagesverlust in %
        max_trades_per_day: Maximale Trades pro Tag
        strategy_preset: Name des Strategy-Presets
        parameter_overrides: Parameter-Überschreibungen
        seed: Random Seed für Reproduzierbarkeit
        run_id: Eindeutige Run-ID
    """
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10_000.0
    base_timeframe: str = "1m"
    mtf_timeframes: list[str] = field(default_factory=lambda: ["5m", "15m", "1h", "4h", "1D"])
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    risk_per_trade_pct: float = 1.0
    max_daily_loss_pct: float = 3.0
    max_trades_per_day: int = 10
    max_loss_streak: int = 3
    cooldown_after_streak_min: int = 60
    strategy_preset: str = "default"
    parameter_overrides: dict[str, Any] = field(default_factory=dict)
    seed: int | None = None
    run_id: str = ""

    def __post_init__(self):
        if not self.run_id:
            import uuid
            self.run_id = f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


@dataclass
class BatchConfig:
    """Konfiguration für Batch-Tests (Parameter-Sweeps).

    Attributes:
        base_config: Basis-Backtest-Konfiguration
        search_method: Grid, Random, oder Bayesian
        parameter_space: Dictionary mit Parameter-Ranges
        max_iterations: Maximale Anzahl Iterationen (für Random/Bayesian)
        n_jobs: Parallele Jobs (-1 = alle CPUs)
        seed: Random Seed für Reproduzierbarkeit
        target_metric: Zielmetrik für Optimierung
        minimize: True = minimieren, False = maximieren
    """
    base_config: BacktestConfig
    search_method: SearchMethod = SearchMethod.GRID
    parameter_space: dict[str, list[Any]] = field(default_factory=dict)
    max_iterations: int = 100
    n_jobs: int = 1  # Default: single-threaded für Stabilität
    seed: int = 42
    target_metric: str = "expectancy"  # Alternativen: profit_factor, sharpe, max_dd
    minimize: bool = False


@dataclass
class WalkForwardConfig:
    """Konfiguration für Walk-Forward Analyse.

    Attributes:
        base_config: Basis-Backtest-Konfiguration
        batch_config: Batch-Konfiguration für Optimierung
        train_window_days: Trainings-Zeitraum in Tagen
        test_window_days: Test-Zeitraum in Tagen
        step_size_days: Schrittweite zwischen Folds
        min_folds: Minimale Anzahl Folds
        reoptimize_each_fold: Neu-Optimieren pro Fold
    """
    base_config: BacktestConfig
    batch_config: BatchConfig
    train_window_days: int = 90  # 3 Monate Training
    test_window_days: int = 30   # 1 Monat Test
    step_size_days: int = 30     # Rolling um 1 Monat
    min_folds: int = 4
    reoptimize_each_fold: bool = True


@dataclass
class UIConfig:
    """UI-spezifische Konfiguration für Backtesting Tab.

    Attributes:
        auto_save_results: Automatisch Ergebnisse speichern
        output_dir: Ausgabeverzeichnis für Reports
        show_progress: Progress-Bar anzeigen
        update_interval_ms: UI-Update-Intervall
    """
    auto_save_results: bool = True
    output_dir: Path = field(default_factory=lambda: Path("data/backtest_results"))
    show_progress: bool = True
    update_interval_ms: int = 100
    max_log_lines: int = 1000
