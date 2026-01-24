#!/usr/bin/env python
"""Quick verification that RegimeOptimizer callback support works.

This script tests the callback parameter fix for Error #9.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core.regime_optimizer import (
    RegimeOptimizer,
    AllParamRanges,
    ADXParamRanges,
    SMAParamRanges,
    RSIParamRanges,
    BBParamRanges,
    ParamRange,
    OptimizationConfig,
    OptimizationMode,
)


def generate_test_data(bars: int = 500) -> pd.DataFrame:
    """Generate minimal OHLCV test data."""
    np.random.seed(42)

    timestamps = pd.date_range(
        start=datetime.utcnow() - timedelta(minutes=bars * 5),
        periods=bars,
        freq="5min"
    )

    close_prices = 100 + np.cumsum(np.random.randn(bars) * 0.5)

    df = pd.DataFrame({
        'open': close_prices + np.random.randn(bars) * 0.2,
        'high': close_prices + abs(np.random.randn(bars) * 0.5),
        'low': close_prices - abs(np.random.randn(bars) * 0.5),
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, bars),
    }, index=timestamps)

    return df


def test_callback_functionality():
    """Test that callback parameter works."""
    print("=" * 70)
    print("CALLBACK FIX VERIFICATION TEST")
    print("=" * 70)

    # Generate test data
    print("\n1. Generating test data (500 bars)...")
    df = generate_test_data(500)
    print(f"   ✓ Generated {len(df)} bars")

    # Setup minimal param ranges
    print("\n2. Setting up parameter ranges...")
    param_ranges = AllParamRanges(
        adx=ADXParamRanges(
            period=ParamRange(min=10, max=15, step=1),
            threshold=ParamRange(min=20, max=25, step=1),
        ),
        sma_fast=SMAParamRanges(
            period=ParamRange(min=5, max=10, step=1)
        ),
        sma_slow=SMAParamRanges(
            period=ParamRange(min=20, max=30, step=2)
        ),
        rsi=RSIParamRanges(
            period=ParamRange(min=10, max=14, step=1),
            sideways_low=ParamRange(min=35, max=40, step=1),
            sideways_high=ParamRange(min=60, max=65, step=1),
        ),
        bb=BBParamRanges(
            period=ParamRange(min=15, max=20, step=1),
            std_dev=ParamRange(min=1.5, max=2.5, step=0.2),
            width_percentile=ParamRange(min=40, max=50, step=2),
        ),
    )
    print("   ✓ Parameter ranges configured")

    # Create optimizer with quick mode (10 trials)
    print("\n3. Creating optimizer (QUICK mode, 10 trials)...")
    config = OptimizationConfig(
        mode=OptimizationMode.QUICK,
        max_trials=10,
        n_startup_trials=5,
        seed=42,
    )

    optimizer = RegimeOptimizer(
        data=df,
        param_ranges=param_ranges,
        config=config,
    )
    print("   ✓ RegimeOptimizer created")

    # Define callback function
    callback_calls = []

    def progress_callback(study, trial):
        """Track optimization progress."""
        current = len(study.trials)
        best_score = study.best_value if study.best_trial else 0

        callback_calls.append({
            'trial': trial.number,
            'current': current,
            'best_score': best_score,
        })

        print(f"   • Trial {trial.number + 1}/10 | Best: {best_score:.1f}")
        return False  # Don't stop

    # Run optimization with callback
    print("\n4. Running optimization WITH callback...")
    results = optimizer.optimize(callbacks=[progress_callback])

    # Verify results
    print("\n5. Verifying results...")
    assert len(results) > 0, "No results returned"
    assert len(callback_calls) > 0, "Callback never called!"
    assert len(callback_calls) == 10, f"Expected 10 callbacks, got {len(callback_calls)}"

    print(f"   ✓ {len(results)} results returned")
    print(f"   ✓ {len(callback_calls)} callback invocations")
    print(f"   ✓ Best score: {results[0].score:.2f}")

    # Test without callback (backward compatibility)
    print("\n6. Testing WITHOUT callback (backward compatibility)...")
    results2 = optimizer.optimize(n_trials=5)
    assert len(results2) > 0, "No results without callback"
    print(f"   ✓ {len(results2)} results returned without callback")

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Callback fix verified!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        success = test_callback_functionality()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
