#!/usr/bin/env python3
"""
Verification Script for Issue #23 Fix

Demonstrates that the MACD field name fix resolves the regime detection issue.
Shows before/after behavior with clear output.

Run with: python scripts/verify_issue_23_fix.py
"""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pandas as pd
from datetime import datetime, timedelta

# Import required modules
from core.tradingbot.regime_engine_json import RegimeEngineJSON
from core.tradingbot.config.detector import RegimeDetector
from core.tradingbot.config.loader import ConfigLoader
from core.indicators.types import IndicatorConfig, IndicatorType


def create_uptrend_candles(bars: int = 100) -> pd.DataFrame:
    """Create sample candle data with uptrend pattern."""
    base_time = datetime(2026, 1, 22, 9, 0, 0)
    candles = []

    for i in range(bars):
        candles.append({
            'timestamp': base_time + timedelta(minutes=i),
            'open': 100.0 + i * 0.5,
            'high': 101.0 + i * 0.5,
            'low': 99.0 + i * 0.5,
            'close': 100.5 + i * 0.5,
            'volume': 1000000 + i * 1000
        })

    return pd.DataFrame(candles)


def verify_pandas_ta_output():
    """Verify pandas_ta MACD field names."""
    print("=" * 80)
    print("STEP 1: Verify pandas_ta MACD Output Format")
    print("=" * 80)

    try:
        import pandas_ta as ta
    except ImportError:
        print("❌ pandas_ta not installed. Cannot verify field names.")
        return False

    df = pd.DataFrame({
        'close': [100, 101, 102, 103, 104, 105, 106] * 10
    })

    macd_result = ta.macd(df['close'], fast=12, slow=26, signal=9)

    print("\nMACD Result Columns:")
    for col in macd_result.columns:
        print(f"  - {col}")

    expected_cols = ['MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9']
    has_all = all(col in macd_result.columns for col in expected_cols)

    if has_all:
        print("\n✅ pandas_ta returns uppercase parameterized field names")
        print("   (e.g., 'MACD_12_26_9', not 'macd')")
    else:
        print(f"\n❌ Expected columns {expected_cols}")
        print(f"   Got: {list(macd_result.columns)}")

    return has_all


def verify_config_field_names():
    """Verify config file uses correct field names."""
    print("\n" + "=" * 80)
    print("STEP 2: Verify Config File Field Names")
    print("=" * 80)

    config_path = Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json")

    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return False

    with open(config_path, 'r') as f:
        config = json.load(f)

    print(f"\nChecking: {config_path}")

    issues = []
    correct = []

    for regime in config.get('regimes', []):
        regime_id = regime.get('id')

        for condition in regime.get('conditions', {}).get('all', []):
            left = condition.get('left', {})
            indicator_id = left.get('indicator_id')
            field = left.get('field')

            if indicator_id and 'macd' in indicator_id.lower():
                if field == 'MACD_12_26_9':
                    correct.append(f"  ✅ {regime_id}: field='{field}' (CORRECT)")
                elif field.lower() == 'macd':
                    issues.append(f"  ❌ {regime_id}: field='{field}' (WRONG - should be 'MACD_12_26_9')")

    if issues:
        print("\n❌ Found Issues:")
        for issue in issues:
            print(issue)
        return False
    elif correct:
        print("\n✅ All MACD Field Names Correct:")
        for item in correct:
            print(item)
        return True
    else:
        print("\n⚠️  No MACD conditions found in config")
        return False


def verify_regime_detection():
    """Verify regime detection works end-to-end."""
    print("\n" + "=" * 80)
    print("STEP 3: Verify Regime Detection Works")
    print("=" * 80)

    config_path = Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json")
    candles = create_uptrend_candles(100)

    print(f"\nTesting with {len(candles)} candles (uptrend pattern)")

    # Load config and engine
    engine = RegimeEngineJSON()
    config = ConfigLoader().load_config(str(config_path))

    print(f"Loaded {len(config.indicators)} indicators")
    print(f"Loaded {len(config.regimes)} regime definitions")

    # Calculate indicators
    indicator_results = {}
    for ind_def in config.indicators:
        ind_config = IndicatorConfig(
            indicator_type=IndicatorType(ind_def.type.lower()),
            params=ind_def.params,
            use_talib=False,
            cache_results=True
        )
        result = engine.indicator_engine.calculate(candles, ind_config)
        indicator_results[ind_def.id] = result.values

    # Create detector
    detector = RegimeDetector(config.regimes)

    # Test detection at bar 60
    test_bar = 60
    indicator_values = {}

    print(f"\nIndicator values at bar {test_bar}:")
    for ind_id, values_df in indicator_results.items():
        row = values_df.iloc[test_bar]
        indicator_values[ind_id] = {
            col: row[col] for col in values_df.columns
        }

        # Show indicator values
        if ind_id == 'macd_12_26_9':
            print(f"  {ind_id}:")
            for field, value in indicator_values[ind_id].items():
                print(f"    {field}: {value:.4f}")
        elif isinstance(indicator_values[ind_id], dict) and len(indicator_values[ind_id]) == 1:
            field, value = next(iter(indicator_values[ind_id].items()))
            print(f"  {ind_id}.{field}: {value:.4f}")

    # Detect regimes
    print("\nDetecting active regimes...")
    active_regimes = detector.detect_active_regimes(indicator_values, scope="entry")

    if not active_regimes:
        print("\n❌ ISSUE NOT FIXED: No regimes detected (expected 1+)")
        print("   This means the field name mismatch still exists.")
        return False

    print(f"\n✅ ISSUE FIXED: Found {len(active_regimes)} active regime(s):")
    for regime in active_regimes:
        print(f"  - {regime.id} (priority: {regime.priority})")

    # Verify uptrend regime is detected
    has_uptrend = any('uptrend' in r.id.lower() for r in active_regimes)

    if has_uptrend:
        print("\n✅ Uptrend regime correctly detected (expected for uptrend data)")
        return True
    else:
        print("\n⚠️  No uptrend regime detected (unexpected for uptrend data)")
        return False


def verify_manual_values():
    """Test with manually crafted indicator values."""
    print("\n" + "=" * 80)
    print("STEP 4: Verify with Manual Test Values")
    print("=" * 80)

    config_path = Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json")
    config = ConfigLoader().load_config(str(config_path))
    detector = RegimeDetector(config.regimes)

    test_cases = [
        {
            'name': 'Strong Uptrend',
            'values': {
                'adx14': {'value': 35.0},
                'macd_12_26_9': {'MACD_12_26_9': 1.5, 'MACDh_12_26_9': 0.2, 'MACDs_12_26_9': 1.3},
                'rsi14': {'value': 65.0},
                'atr14': {'value': 2.0},
                'bb20': {'upper': 105.0, 'middle': 100.0, 'lower': 95.0}
            },
            'expected': 'strong_uptrend'
        },
        {
            'name': 'Strong Downtrend',
            'values': {
                'adx14': {'value': 35.0},
                'macd_12_26_9': {'MACD_12_26_9': -1.5, 'MACDh_12_26_9': -0.2, 'MACDs_12_26_9': -1.3},
                'rsi14': {'value': 35.0},
                'atr14': {'value': 2.0},
                'bb20': {'upper': 105.0, 'middle': 100.0, 'lower': 95.0}
            },
            'expected': 'strong_downtrend'
        },
        {
            'name': 'Range Overbought',
            'values': {
                'adx14': {'value': 15.0},
                'macd_12_26_9': {'MACD_12_26_9': 0.0, 'MACDh_12_26_9': 0.0, 'MACDs_12_26_9': 0.0},
                'rsi14': {'value': 75.0},
                'atr14': {'value': 1.5},
                'bb20': {'upper': 105.0, 'middle': 100.0, 'lower': 95.0}
            },
            'expected': 'range_overbought'
        }
    ]

    all_passed = True

    for test in test_cases:
        print(f"\nTest Case: {test['name']}")
        active = detector.detect_active_regimes(test['values'], scope="entry")
        active_ids = [r.id for r in active]

        if test['expected'] in active_ids:
            print(f"  ✅ Correctly detected: {test['expected']}")
        else:
            print(f"  ❌ Failed to detect: {test['expected']}")
            print(f"     Got: {active_ids}")
            all_passed = False

    return all_passed


def main():
    """Run all verification steps."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Issue #23 Fix Verification" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")

    results = {
        'pandas_ta_output': verify_pandas_ta_output(),
        'config_field_names': verify_config_field_names(),
        'regime_detection': verify_regime_detection(),
        'manual_values': verify_manual_values()
    }

    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    for step, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {step.replace('_', ' ').title()}")

    all_passed = all(results.values())

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL CHECKS PASSED - Issue #23 is FIXED!")
        print("=" * 80)
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Issue #23 may not be fully resolved")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    sys.exit(main())
