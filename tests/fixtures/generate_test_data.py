"""Generate sample test data and expected outputs for E2E tests.

Produces:
- Sample OHLCV DataFrame (1000 bars of BTCUSDT 5m)
- Expected regime periods
- Expected indicator optimization results
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def generate_sample_ohlcv(symbol: str = "BTCUSDT", timeframe: str = "5m", bars: int = 1000) -> pd.DataFrame:
    """Generate realistic sample OHLCV data.

    Args:
        symbol: Trading pair
        timeframe: Timeframe
        bars: Number of bars

    Returns:
        DataFrame with [open, high, low, close, volume]
    """
    np.random.seed(42)

    # Generate realistic price movements
    start_price = 40000.0
    returns = np.random.normal(0.0001, 0.005, bars)
    prices = start_price * np.exp(np.cumsum(returns))

    # Generate OHLCV
    df = pd.DataFrame({
        'open': prices * (1 + np.random.uniform(-0.002, 0.002, bars)),
        'high': prices * (1 + np.abs(np.random.uniform(0.001, 0.005, bars))),
        'low': prices * (1 - np.abs(np.random.uniform(0.001, 0.005, bars))),
        'close': prices,
        'volume': np.random.uniform(1000, 5000, bars),
    })

    # Ensure OHLCV properties
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)

    # Add datetime index
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    time_delta = timedelta(minutes=5)
    df.index = pd.DatetimeIndex(
        [start_time + i * time_delta for i in range(len(df))],
        name='timestamp'
    )

    return df


def create_test_fixtures():
    """Create all test fixtures."""
    fixtures_dir = Path(__file__).parent

    # 1. Generate sample OHLCV data
    data = generate_sample_ohlcv("BTCUSDT", "5m", 1000)

    # 2. Create regime optimization results fixture
    regime_results = {
        "version": "2.0",
        "meta": {
            "stage": "regime_optimization",
            "created_at": datetime.utcnow().isoformat(),
            "total_combinations": 50,
            "completed": 50,
            "method": "tpe_multivariate",
            "symbol": "BTCUSDT",
            "timeframe": "5m",
        },
        "results": [
            {
                "rank": 1,
                "score": 75.5,
                "params": {
                    "adx_period": 14,
                    "adx_threshold": 25.0,
                    "sma_fast_period": 10,
                    "sma_slow_period": 30,
                    "rsi_period": 14,
                    "rsi_sideways_low": 35,
                    "rsi_sideways_high": 65,
                    "bb_period": 20,
                    "bb_std_dev": 2.0,
                    "bb_width_percentile": 50.0,
                },
                "metrics": {
                    "regime_count": 3,
                    "avg_duration_bars": 150.5,
                    "switch_count": 6,
                    "stability_score": 0.8,
                    "coverage": 1.0,
                    "f1_bull": 0.75,
                    "f1_bear": 0.72,
                    "f1_sideways": 0.68,
                    "bull_bars": 350,
                    "bear_bars": 300,
                    "sideways_bars": 350,
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "rank": 2,
                "score": 73.2,
                "params": {
                    "adx_period": 15,
                    "adx_threshold": 26.0,
                    "sma_fast_period": 11,
                    "sma_slow_period": 31,
                    "rsi_period": 15,
                    "rsi_sideways_low": 36,
                    "rsi_sideways_high": 64,
                    "bb_period": 21,
                    "bb_std_dev": 2.1,
                    "bb_width_percentile": 51.0,
                },
                "metrics": {
                    "regime_count": 3,
                    "avg_duration_bars": 148.2,
                    "switch_count": 7,
                    "stability_score": 0.78,
                    "coverage": 1.0,
                    "f1_bull": 0.73,
                    "f1_bear": 0.70,
                    "f1_sideways": 0.66,
                    "bull_bars": 340,
                    "bear_bars": 310,
                    "sideways_bars": 350,
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
        ],
    }

    # Save regime results
    regime_results_path = fixtures_dir / "regime_optimization" / "regime_optimization_results_BTCUSDT_5m.json"
    regime_results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(regime_results_path, "w") as f:
        json.dump(regime_results, f, indent=2)

    # 3. Create optimized regime config (with bar_indices)
    regime_periods = []

    # BULL periods (indices 0-350)
    regime_periods.append({
        "regime": "BULL",
        "start_idx": 0,
        "end_idx": 175,
        "start_timestamp": datetime(2024, 1, 1, 0, 0, 0).isoformat(),
        "end_timestamp": datetime(2024, 1, 1, 14, 35, 0).isoformat(),
        "bars": 176,
        "bar_indices": list(range(0, 176)),
    })

    regime_periods.append({
        "regime": "BULL",
        "start_idx": 300,
        "end_idx": 475,
        "start_timestamp": datetime(2024, 1, 2, 1, 0, 0).isoformat(),
        "end_timestamp": datetime(2024, 1, 2, 15, 35, 0).isoformat(),
        "bars": 176,
        "bar_indices": list(range(300, 476)),
    })

    # BEAR periods
    regime_periods.append({
        "regime": "BEAR",
        "start_idx": 176,
        "end_idx": 250,
        "start_timestamp": datetime(2024, 1, 1, 14, 40, 0).isoformat(),
        "end_timestamp": datetime(2024, 1, 1, 22, 50, 0).isoformat(),
        "bars": 75,
        "bar_indices": list(range(176, 251)),
    })

    regime_periods.append({
        "regime": "BEAR",
        "start_idx": 476,
        "end_idx": 550,
        "start_timestamp": datetime(2024, 1, 2, 15, 40, 0).isoformat(),
        "end_timestamp": datetime(2024, 1, 3, 6, 50, 0).isoformat(),
        "bars": 75,
        "bar_indices": list(range(476, 551)),
    })

    # SIDEWAYS periods
    regime_periods.append({
        "regime": "SIDEWAYS",
        "start_idx": 251,
        "end_idx": 299,
        "start_timestamp": datetime(2024, 1, 1, 22, 55, 0).isoformat(),
        "end_timestamp": datetime(2024, 1, 2, 0, 0, 0).isoformat(),
        "bars": 49,
        "bar_indices": list(range(251, 300)),
    })

    regime_periods.append({
        "regime": "SIDEWAYS",
        "start_idx": 551,
        "end_idx": 599,
        "start_timestamp": datetime(2024, 1, 3, 6, 55, 0).isoformat(),
        "end_timestamp": datetime(2024, 1, 3, 10, 0, 0).isoformat(),
        "bars": 49,
        "bar_indices": list(range(551, 600)),
    })

    optimized_regime = {
        "version": "2.0",
        "meta": {
            "stage": "regime_optimization_exported",
            "created_at": datetime.utcnow().isoformat(),
            "symbol": "BTCUSDT",
            "timeframe": "5m",
            "selected_rank": 1,
            "best_score": 75.5,
        },
        "parameters": {
            "adx_period": 14,
            "adx_threshold": 25.0,
            "sma_fast_period": 10,
            "sma_slow_period": 30,
            "rsi_period": 14,
            "rsi_sideways_low": 35,
            "rsi_sideways_high": 65,
            "bb_period": 20,
            "bb_std_dev": 2.0,
            "bb_width_percentile": 50.0,
        },
        "metrics": {
            "regime_count": 3,
            "avg_duration_bars": 150.5,
            "stability_score": 0.8,
            "f1_bull": 0.75,
            "f1_bear": 0.72,
            "f1_sideways": 0.68,
        },
        "regime_periods": regime_periods,
    }

    # Save optimized regime
    optimized_regime_path = fixtures_dir / "regime_optimization" / "optimized_regime_BTCUSDT_5m.json"
    with open(optimized_regime_path, "w") as f:
        json.dump(optimized_regime, f, indent=2)

    # 4. Create indicator optimization results for each regime
    for regime_type in ["BULL", "BEAR", "SIDEWAYS"]:
        indicator_results = {
            "version": "2.0",
            "meta": {
                "stage": "indicator_optimization",
                "created_at": datetime.utcnow().isoformat(),
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "regime": regime_type,
                "total_trials": 40,
                "completed": 40,
            },
            "results": [
                {
                    "rank": 1,
                    "signal_type": "entry_long",
                    "indicator": "RSI",
                    "score": 68.5,
                    "params": {
                        "period": 14,
                        "oversold": 30,
                    },
                    "conditions": {
                        "operator": "AND",
                        "conditions": [
                            {"field": "rsi", "operator": "<", "value": 30},
                        ],
                    },
                    "metrics": {
                        "signals": 25,
                        "trades": 20,
                        "win_rate": 0.65,
                        "profit_factor": 1.45,
                        "avg_win": 0.45,
                        "avg_loss": -0.35,
                        "max_drawdown": -0.15,
                        "sharpe_ratio": 1.2,
                        "expectancy": 0.08,
                        "total_return": 0.18,
                        "wins": 13,
                        "losses": 7,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                },
                {
                    "rank": 1,
                    "signal_type": "exit_long",
                    "indicator": "MACD",
                    "score": 62.3,
                    "params": {
                        "fast": 12,
                        "slow": 26,
                        "signal": 9,
                    },
                    "conditions": {
                        "operator": "OR",
                        "conditions": [
                            {"field": "macd_histogram", "operator": "<", "value": 0},
                        ],
                    },
                    "metrics": {
                        "signals": 23,
                        "trades": 20,
                        "win_rate": 0.55,
                        "profit_factor": 1.2,
                        "avg_win": 0.38,
                        "avg_loss": -0.32,
                        "max_drawdown": -0.12,
                        "sharpe_ratio": 0.9,
                        "expectancy": 0.05,
                        "total_return": 0.12,
                        "wins": 11,
                        "losses": 9,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ],
        }

        indicator_results_path = (
            fixtures_dir / "indicator_optimization"
            / f"indicator_optimization_results_{regime_type}_BTCUSDT_5m.json"
        )
        indicator_results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(indicator_results_path, "w") as f:
            json.dump(indicator_results, f, indent=2)

    # 5. Create indicator sets (optimized) for each regime
    for regime_type in ["BULL", "BEAR", "SIDEWAYS"]:
        indicator_sets = {
            "version": "2.0",
            "meta": {
                "stage": "indicator_optimization_exported",
                "created_at": datetime.utcnow().isoformat(),
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "regime": regime_type,
                "selected_rank": 1,
            },
            "signal_sets": {
                "entry_long": {
                    "indicator": "RSI",
                    "params": {
                        "period": 14,
                        "oversold": 30,
                    },
                    "score": 68.5,
                    "metrics": {
                        "win_rate": 0.65,
                        "profit_factor": 1.45,
                        "sharpe_ratio": 1.2,
                        "expectancy": 0.08,
                    },
                },
                "exit_long": {
                    "indicator": "MACD",
                    "params": {
                        "fast": 12,
                        "slow": 26,
                        "signal": 9,
                    },
                    "score": 62.3,
                    "metrics": {
                        "win_rate": 0.55,
                        "profit_factor": 1.2,
                        "sharpe_ratio": 0.9,
                        "expectancy": 0.05,
                    },
                },
            },
        }

        indicator_sets_path = (
            fixtures_dir / "indicator_optimization"
            / f"indicator_sets_{regime_type}_BTCUSDT_5m.json"
        )
        with open(indicator_sets_path, "w") as f:
            json.dump(indicator_sets, f, indent=2)

    print(f"✓ Test fixtures created in {fixtures_dir}")
    return data


if __name__ == "__main__":
    df = create_test_fixtures()
    print(f"✓ Generated sample data: {len(df)} bars")
