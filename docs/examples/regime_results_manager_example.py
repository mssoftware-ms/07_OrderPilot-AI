"""Example usage of RegimeResultsManager.

This script demonstrates how to use RegimeResultsManager for:
1. Managing regime optimization results
2. Ranking and selecting results
3. Exporting to regime_optimization_results.json
4. Exporting to optimized_regime.json
"""

from datetime import datetime
from pathlib import Path

from src.core.regime_results_manager import RegimeResultsManager


def main():
    """Example workflow."""

    # 1. Initialize manager
    print("=" * 80)
    print("RegimeResultsManager Example")
    print("=" * 80)

    manager = RegimeResultsManager()
    print(f"✅ Manager initialized with schemas_dir: {manager.schemas_dir}")

    # 2. Add optimization results
    print("\n" + "=" * 80)
    print("Adding Optimization Results")
    print("=" * 80)

    # Result 1: Best configuration
    result1 = manager.add_result(
        score=78.5,
        params={
            "adx_period": 14,
            "adx_threshold": 25.0,
            "sma_fast_period": 50,
            "sma_slow_period": 200,
            "rsi_period": 14,
            "rsi_sideways_low": 40,
            "rsi_sideways_high": 60,
            "bb_period": 20,
            "bb_std_dev": 2.0,
            "bb_width_percentile": 0.20,
        },
        metrics={
            "regime_count": 15,
            "avg_duration_bars": 26.7,
            "switch_count": 14,
            "stability_score": 0.73,
            "coverage": 1.0,
            "f1_bull": 0.82,
            "f1_bear": 0.79,
            "f1_sideways": 0.71,
            "bull_bars": 180,
            "bear_bars": 101,
            "sideways_bars": 120,
        },
    )
    print(f"✅ Added result 1: score={result1.score:.2f}")

    # Result 2: Second best
    result2 = manager.add_result(
        score=65.2,
        params={
            "adx_period": 12,
            "adx_threshold": 22.0,
            "sma_fast_period": 30,
            "sma_slow_period": 150,
            "rsi_period": 14,
            "rsi_sideways_low": 35,
            "rsi_sideways_high": 65,
            "bb_period": 20,
            "bb_std_dev": 2.0,
            "bb_width_percentile": 0.25,
        },
        metrics={
            "regime_count": 18,
            "avg_duration_bars": 22.3,
            "switch_count": 17,
            "stability_score": 0.65,
            "coverage": 1.0,
            "f1_bull": 0.75,
            "f1_bear": 0.72,
            "f1_sideways": 0.68,
            "bull_bars": 165,
            "bear_bars": 115,
            "sideways_bars": 121,
        },
    )
    print(f"✅ Added result 2: score={result2.score:.2f}")

    # Result 3: Third
    result3 = manager.add_result(
        score=42.1,
        params={
            "adx_period": 16,
            "adx_threshold": 28.0,
            "sma_fast_period": 40,
            "sma_slow_period": 175,
            "rsi_period": 12,
            "rsi_sideways_low": 42,
            "rsi_sideways_high": 58,
            "bb_period": 15,
            "bb_std_dev": 1.5,
            "bb_width_percentile": 0.18,
        },
        metrics={
            "regime_count": 22,
            "avg_duration_bars": 18.2,
            "switch_count": 21,
            "stability_score": 0.51,
            "coverage": 0.98,
            "f1_bull": 0.68,
            "f1_bear": 0.65,
            "f1_sideways": 0.62,
            "bull_bars": 150,
            "bear_bars": 130,
            "sideways_bars": 121,
        },
    )
    print(f"✅ Added result 3: score={result3.score:.2f}")

    # 3. Rank results
    print("\n" + "=" * 80)
    print("Ranking Results")
    print("=" * 80)

    manager.rank_results()

    for result in manager.results:
        print(f"  Rank {result.rank}: Score {result.score:.2f}")

    # 4. Get statistics
    print("\n" + "=" * 80)
    print("Statistics")
    print("=" * 80)

    stats = manager.get_statistics()
    print(f"  Total results: {stats['count']}")
    print(f"  Score range: {stats['score_min']:.2f} - {stats['score_max']:.2f}")
    print(f"  Average score: {stats['score_avg']:.2f}")
    print(f"  Median score: {stats['score_median']:.2f}")

    # 5. Select best result
    print("\n" + "=" * 80)
    print("Selecting Best Result")
    print("=" * 80)

    selected = manager.select_result(rank=1)
    print(f"✅ Selected rank {selected.rank}: score={selected.score:.2f}")

    # 6. Export optimization results
    print("\n" + "=" * 80)
    print("Exporting Optimization Results")
    print("=" * 80)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    results_path = manager.export_optimization_results(
        output_path=output_dir / "regime_optimization_results_BTCUSDT_5m.json",
        meta={
            "stage": "regime_optimization",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "optimization_id": "regime_opt_BTCUSDT_5m_example",
            "total_combinations": 3,
            "completed": 3,
            "duration_seconds": 1.5,
            "method": "tpe_multivariate",
            "mode": "standard",
            "source": {
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "bars": 401,
                "data_range": {
                    "start": "2026-01-22T12:10:00Z",
                    "end": "2026-01-23T21:30:00Z",
                },
            },
            "statistics": stats,
        },
        optimization_config={
            "mode": "standard",
            "method": "tpe_multivariate",
            "max_trials": 150,
            "n_startup_trials": 20,
            "early_stopping": {
                "enabled": True,
                "pruner": "hyperband",
                "min_fidelity": 0.1,
                "reduction_factor": 3,
            },
            "sequential_phases": {
                "enabled": True,
                "phases": [
                    {"name": "adx", "params": ["adx_period", "adx_threshold"], "trials": 40},
                    {"name": "sma", "params": ["sma_fast_period", "sma_slow_period"], "trials": 35},
                ],
            },
            "parallel": {
                "n_jobs": -1,
                "storage": "sqlite:///optuna_regime.db",
            },
            "actual_performance": {
                "total_combinations_if_grid": 1000,
                "actual_trials_run": 3,
                "speedup_factor": 333,
            },
        },
        param_ranges={
            "adx": {
                "period": {"min": 10, "max": 18, "step": 2},
                "threshold": {"min": 20, "max": 30, "step": 2},
            },
            "sma_fast": {
                "period": {"min": 20, "max": 50, "step": 10},
            },
            "sma_slow": {
                "period": {"min": 100, "max": 200, "step": 25},
            },
            "rsi": {
                "period": {"min": 9, "max": 21, "step": 3},
                "sideways_low": {"min": 35, "max": 45, "step": 5},
                "sideways_high": {"min": 55, "max": 65, "step": 5},
            },
            "bb": {
                "period": {"min": 15, "max": 25, "step": 5},
                "std_dev": {"min": 1.5, "max": 2.5, "step": 0.5},
                "width_percentile": {"min": 0.15, "max": 0.25, "step": 0.05},
            },
        },
        validate=False,  # Skip validation for demo
    )

    print(f"✅ Exported optimization results: {results_path}")

    # 7. Export optimized regime configuration
    print("\n" + "=" * 80)
    print("Exporting Optimized Regime Config")
    print("=" * 80)

    regime_path = manager.export_optimized_regime(
        output_path=output_dir / "optimized_regime_BTCUSDT_5m.json",
        symbol="BTCUSDT",
        timeframe="5m",
        bars=401,
        data_range={
            "start": "2026-01-22T12:10:00Z",
            "end": "2026-01-23T21:30:00Z",
        },
        regime_periods=[
            {
                "regime": "BULL",
                "start_idx": 0,
                "end_idx": 179,
                "start_timestamp": "2026-01-22T12:10:00Z",
                "end_timestamp": "2026-01-22T21:05:00Z",
                "bars": 180,
            },
            {
                "regime": "BEAR",
                "start_idx": 180,
                "end_idx": 280,
                "start_timestamp": "2026-01-22T21:10:00Z",
                "end_timestamp": "2026-01-23T05:35:00Z",
                "bars": 101,
            },
            {
                "regime": "SIDEWAYS",
                "start_idx": 281,
                "end_idx": 400,
                "start_timestamp": "2026-01-23T05:40:00Z",
                "end_timestamp": "2026-01-23T21:30:00Z",
                "bars": 120,
            },
        ],
        validate=False,  # Skip validation for demo
    )

    print(f"✅ Exported optimized regime: {regime_path}")
    print(f"   Score: {selected.score:.2f}")
    print(f"   Rank: {selected.rank}")

    # 8. Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"✅ Created 3 regime optimization results")
    print(f"✅ Ranked results by composite score")
    print(f"✅ Selected best result (rank 1, score {selected.score:.2f})")
    print(f"✅ Exported optimization results to: {results_path}")
    print(f"✅ Exported optimized regime config to: {regime_path}")
    print()
    print("Next steps:")
    print("  1. Review exported JSON files in 'output/' directory")
    print("  2. Use optimized_regime.json for Stufe 2 (Indicator Optimization)")
    print("  3. Integrate with trading bot configuration")


if __name__ == "__main__":
    main()
