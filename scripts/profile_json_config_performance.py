"""Performance Profiling Script for JSON Config System.

Profiles key operations:
1. Config loading and validation
2. Regime detection
3. Strategy routing
4. Parameter override application
5. State restoration
6. End-to-end pipeline

Generates performance report with bottleneck analysis.
"""

import cProfile
import io
import json
import pstats
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.core.tradingbot.config import ConfigLoader, TradingBotConfig
from src.core.tradingbot.config_integration_bridge import (
    ConfigBasedStrategyCatalog,
    IndicatorValueCalculator,
)
from src.core.tradingbot.models import FeatureVector


def generate_sample_config() -> dict:
    """Generate sample production-like config."""
    return {
        "schema_version": "1.0.0",
        "indicators": [
            {"id": "rsi14", "type": "rsi", "params": {"period": 14}},
            {"id": "adx14", "type": "adx", "params": {"period": 14}},
            {"id": "sma20", "type": "sma", "params": {"period": 20}},
            {"id": "sma50", "type": "sma", "params": {"period": 50}},
            {"id": "macd", "type": "macd", "params": {"fast": 12, "slow": 26, "signal": 9}},
            {"id": "bb20", "type": "bb", "params": {"period": 20, "std": 2}},
        ],
        "regimes": [
            {
                "id": "strong_uptrend",
                "name": "Strong Uptrend",
                "conditions": {
                    "all": [
                        {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 30}},
                        {"left": {"indicator_id": "sma20", "field": "value"}, "op": "gt", "right": {"indicator_id": "sma50", "field": "value"}},
                    ]
                },
                "priority": 10,
            },
            {
                "id": "weak_trend",
                "name": "Weak Trend",
                "conditions": {
                    "all": [
                        {"left": {"indicator_id": "adx14", "field": "value"}, "op": "between", "right": {"min": 20, "max": 30}},
                    ]
                },
                "priority": 8,
            },
            {
                "id": "ranging",
                "name": "Ranging",
                "conditions": {
                    "all": [
                        {"left": {"indicator_id": "adx14", "field": "value"}, "op": "lt", "right": {"value": 20}},
                    ]
                },
                "priority": 6,
            },
        ],
        "strategies": [
            {
                "id": "trend_momentum",
                "name": "Trend + Momentum",
                "entry": {
                    "all": [
                        {"left": {"indicator_id": "adx14", "field": "value"}, "op": "gt", "right": {"value": 25}},
                        {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "between", "right": {"min": 50, "max": 70}},
                    ]
                },
                "exit": {
                    "any": [
                        {"left": {"indicator_id": "adx14", "field": "value"}, "op": "lt", "right": {"value": 20}},
                        {"left": {"indicator_id": "rsi14", "field": "value"}, "op": "gt", "right": {"value": 75}},
                    ]
                },
                "risk": {"position_size": 0.02, "stop_loss": 0.015, "take_profit": 0.045},
            },
            {
                "id": "breakout",
                "name": "Breakout",
                "entry": {"all": []},
                "exit": {"all": []},
                "risk": {"position_size": 0.015, "stop_loss": 0.02, "take_profit": 0.06},
            },
            {
                "id": "mean_reversion",
                "name": "Mean Reversion",
                "entry": {"all": []},
                "exit": {"all": []},
                "risk": {"position_size": 0.025, "stop_loss": 0.01, "take_profit": 0.03},
            },
        ],
        "strategy_sets": [
            {
                "id": "strong_trend_set",
                "name": "Strong Trend Set",
                "strategies": [
                    {
                        "strategy_id": "trend_momentum",
                        "strategy_overrides": {"risk": {"position_size": 0.03}},
                    }
                ],
                "indicator_overrides": [{"indicator_id": "adx14", "params": {"period": 21}}],
            },
            {
                "id": "weak_trend_set",
                "name": "Weak Trend Set",
                "strategies": [{"strategy_id": "trend_momentum"}, {"strategy_id": "breakout"}],
            },
            {
                "id": "range_set",
                "name": "Range Set",
                "strategies": [{"strategy_id": "mean_reversion"}],
            },
        ],
        "routing": [
            {"strategy_set_id": "strong_trend_set", "match": {"all_of": ["strong_uptrend"]}},
            {"strategy_set_id": "weak_trend_set", "match": {"all_of": ["weak_trend"]}},
            {"strategy_set_id": "range_set", "match": {"all_of": ["ranging"]}},
        ],
    }


def generate_sample_features() -> FeatureVector:
    """Generate sample feature vector."""
    return FeatureVector(
        timestamp=datetime.now(),
        close=100.0,
        open=99.5,
        high=101.0,
        low=99.0,
        volume=1000000.0,
        rsi=60.0,
        adx=32.0,
        sma_fast=99.8,
        sma_slow=98.5,
        ema_fast=99.9,
        ema_slow=98.7,
        macd=0.5,
        macd_signal=0.3,
        macd_histogram=0.2,
        bb_upper=102.0,
        bb_middle=100.0,
        bb_lower=98.0,
        bb_width=4.0,
        atr=2.0,
    )


def profile_config_loading(config_data: dict, iterations: int = 100) -> dict:
    """Profile config loading and validation."""
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f, indent=2)
        config_path = f.name

    try:
        loader = ConfigLoader()

        # Warmup
        for _ in range(10):
            loader.load_config(config_path)

        # Profile
        start = time.perf_counter()
        for _ in range(iterations):
            config = loader.load_config(config_path)
        elapsed = (time.perf_counter() - start) * 1000

        return {
            "operation": "Config Loading & Validation",
            "iterations": iterations,
            "total_ms": elapsed,
            "avg_ms": elapsed / iterations,
            "ops_per_sec": iterations / (elapsed / 1000),
        }
    finally:
        Path(config_path).unlink()


def profile_regime_detection(catalog: ConfigBasedStrategyCatalog, features: FeatureVector, iterations: int = 1000) -> dict:
    """Profile regime detection."""
    # Warmup
    for _ in range(10):
        catalog.get_current_regime(features)

    # Profile
    start = time.perf_counter()
    for _ in range(iterations):
        regime = catalog.get_current_regime(features)
    elapsed = (time.perf_counter() - start) * 1000

    return {
        "operation": "Regime Detection",
        "iterations": iterations,
        "total_ms": elapsed,
        "avg_ms": elapsed / iterations,
        "ops_per_sec": iterations / (elapsed / 1000),
    }


def profile_strategy_routing(catalog: ConfigBasedStrategyCatalog, features: FeatureVector, iterations: int = 1000) -> dict:
    """Profile strategy routing."""
    # Warmup
    for _ in range(10):
        catalog.get_active_strategy_sets(features)

    # Profile
    start = time.perf_counter()
    for _ in range(iterations):
        matched_sets = catalog.get_active_strategy_sets(features)
    elapsed = (time.perf_counter() - start) * 1000

    return {
        "operation": "Strategy Routing",
        "iterations": iterations,
        "total_ms": elapsed,
        "avg_ms": elapsed / iterations,
        "ops_per_sec": iterations / (elapsed / 1000),
    }


def profile_parameter_overrides(catalog: ConfigBasedStrategyCatalog, features: FeatureVector, iterations: int = 1000) -> dict:
    """Profile parameter override application and restoration."""
    # Warmup
    for _ in range(10):
        matched_sets = catalog.get_active_strategy_sets(features)
        for matched_set in matched_sets:
            context = catalog.strategy_executor.prepare_execution(matched_set)
            catalog.strategy_executor.restore_state(context)

    # Profile
    start = time.perf_counter()
    for _ in range(iterations):
        matched_sets = catalog.get_active_strategy_sets(features)
        for matched_set in matched_sets:
            context = catalog.strategy_executor.prepare_execution(matched_set)
            catalog.strategy_executor.restore_state(context)
    elapsed = (time.perf_counter() - start) * 1000

    return {
        "operation": "Parameter Override + Restore",
        "iterations": iterations,
        "total_ms": elapsed,
        "avg_ms": elapsed / iterations,
        "ops_per_sec": iterations / (elapsed / 1000),
    }


def profile_indicator_mapping(features: FeatureVector, iterations: int = 1000) -> dict:
    """Profile indicator value mapping."""
    # Warmup
    for _ in range(10):
        IndicatorValueCalculator.calculate_indicator_values(features)

    # Profile
    start = time.perf_counter()
    for _ in range(iterations):
        indicator_values = IndicatorValueCalculator.calculate_indicator_values(features)
    elapsed = (time.perf_counter() - start) * 1000

    return {
        "operation": "Indicator Value Mapping",
        "iterations": iterations,
        "total_ms": elapsed,
        "avg_ms": elapsed / iterations,
        "ops_per_sec": iterations / (elapsed / 1000),
    }


def profile_end_to_end(catalog: ConfigBasedStrategyCatalog, features: FeatureVector, iterations: int = 1000) -> dict:
    """Profile complete end-to-end pipeline."""
    # Warmup
    for _ in range(10):
        regime = catalog.get_current_regime(features)
        matched_sets = catalog.get_active_strategy_sets(features)
        for matched_set in matched_sets:
            context = catalog.strategy_executor.prepare_execution(matched_set)
            catalog.strategy_executor.restore_state(context)

    # Profile
    start = time.perf_counter()
    for _ in range(iterations):
        # Complete pipeline
        regime = catalog.get_current_regime(features)
        matched_sets = catalog.get_active_strategy_sets(features)
        for matched_set in matched_sets:
            context = catalog.strategy_executor.prepare_execution(matched_set)
            catalog.strategy_executor.restore_state(context)
    elapsed = (time.perf_counter() - start) * 1000

    return {
        "operation": "End-to-End Pipeline",
        "iterations": iterations,
        "total_ms": elapsed,
        "avg_ms": elapsed / iterations,
        "ops_per_sec": iterations / (elapsed / 1000),
    }


def profile_with_cprofile(func, *args, **kwargs):
    """Profile function with cProfile."""
    profiler = cProfile.Profile()
    profiler.enable()

    result = func(*args, **kwargs)

    profiler.disable()

    # Get stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions

    return result, s.getvalue()


def main():
    """Run performance profiling."""
    print("=" * 80)
    print("JSON Config System Performance Profiling")
    print("=" * 80)
    print()

    # Generate test data
    print("Generating test data...")
    config_data = generate_sample_config()
    features = generate_sample_features()

    # Load config
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f, indent=2)
        config_path = f.name

    try:
        loader = ConfigLoader()
        config = loader.load_config(config_path)
        catalog = ConfigBasedStrategyCatalog(config)

        # Run profiles
        print("\nRunning performance tests...\n")

        results = []

        # 1. Config Loading
        print("1. Config Loading & Validation...")
        results.append(profile_config_loading(config_data, iterations=100))

        # 2. Indicator Mapping
        print("2. Indicator Value Mapping...")
        results.append(profile_indicator_mapping(features, iterations=1000))

        # 3. Regime Detection
        print("3. Regime Detection...")
        results.append(profile_regime_detection(catalog, features, iterations=1000))

        # 4. Strategy Routing
        print("4. Strategy Routing...")
        results.append(profile_strategy_routing(catalog, features, iterations=1000))

        # 5. Parameter Overrides
        print("5. Parameter Override + Restore...")
        results.append(profile_parameter_overrides(catalog, features, iterations=1000))

        # 6. End-to-End
        print("6. End-to-End Pipeline...")
        results.append(profile_end_to_end(catalog, features, iterations=1000))

        # Print results
        print("\n" + "=" * 80)
        print("PERFORMANCE RESULTS")
        print("=" * 80)
        print()
        print(f"{'Operation':<35} {'Avg Time':<15} {'Ops/Sec':<15} {'Target':<15}")
        print("-" * 80)

        targets = {
            "Config Loading & Validation": 50.0,
            "Indicator Value Mapping": 5.0,
            "Regime Detection": 20.0,
            "Strategy Routing": 30.0,
            "Parameter Override + Restore": 40.0,
            "End-to-End Pipeline": 50.0,
        }

        all_passed = True

        for result in results:
            op = result["operation"]
            avg_ms = result["avg_ms"]
            ops_per_sec = result["ops_per_sec"]
            target = targets.get(op, 0)

            status = "✅ PASS" if avg_ms < target else "❌ FAIL"
            if avg_ms >= target:
                all_passed = False

            print(f"{op:<35} {avg_ms:>8.3f} ms    {ops_per_sec:>10.0f}    < {target:.1f} ms {status}")

        print("-" * 80)
        print()

        if all_passed:
            print("✅ All performance targets met!")
        else:
            print("❌ Some performance targets not met. See details above.")

        print()

        # Detailed cProfile for bottleneck analysis
        print("=" * 80)
        print("DETAILED PROFILING (Top 20 Functions)")
        print("=" * 80)
        print()

        def run_pipeline():
            for _ in range(100):
                regime = catalog.get_current_regime(features)
                matched_sets = catalog.get_active_strategy_sets(features)
                for matched_set in matched_sets:
                    context = catalog.strategy_executor.prepare_execution(matched_set)
                    catalog.strategy_executor.restore_state(context)

        _, profile_output = profile_with_cprofile(run_pipeline)
        print(profile_output)

        # Summary
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print(f"Total operations profiled: {sum(r['iterations'] for r in results):,}")
        print(f"Total time: {sum(r['total_ms'] for r in results):.1f} ms")
        print()
        print("Key Metrics:")
        for result in results:
            if result["operation"] in ["Regime Detection", "End-to-End Pipeline"]:
                print(f"  - {result['operation']}: {result['avg_ms']:.2f} ms")
        print()

    finally:
        Path(config_path).unlink()


if __name__ == "__main__":
    main()
