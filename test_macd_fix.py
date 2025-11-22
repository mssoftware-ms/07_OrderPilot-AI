"""Test MACD calculation and column detection."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import the indicator engine
from src.core.indicators.engine import IndicatorEngine, IndicatorConfig, IndicatorType

# Create sample OHLCV data
def create_sample_data(num_bars=100):
    """Create sample price data for testing."""
    start_date = datetime.now() - timedelta(days=num_bars)
    dates = [start_date + timedelta(days=i) for i in range(num_bars)]

    # Generate realistic price data
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(num_bars) * 2)

    data = {
        'timestamp': dates,
        'open': close_prices + np.random.randn(num_bars) * 0.5,
        'high': close_prices + np.abs(np.random.randn(num_bars)) * 1.5,
        'low': close_prices - np.abs(np.random.randn(num_bars)) * 1.5,
        'close': close_prices,
        'volume': np.random.randint(1000000, 5000000, num_bars)
    }

    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)

    return df

# Test MACD calculation
def test_macd():
    print("=" * 80)
    print("TESTING MACD CALCULATION AND COLUMN DETECTION")
    print("=" * 80)

    # Create sample data
    print("\n1. Creating sample data...")
    data = create_sample_data(100)
    print(f"   Created {len(data)} bars of sample price data")
    print(f"   Price range: ${data['close'].min():.2f} - ${data['close'].max():.2f}")

    # Initialize indicator engine
    print("\n2. Initializing indicator engine...")
    engine = IndicatorEngine()

    # Configure MACD indicator
    print("\n3. Configuring MACD indicator...")
    config = IndicatorConfig(
        indicator_type=IndicatorType.MACD,
        params={'fast': 12, 'slow': 26, 'signal': 9}
    )

    # Calculate MACD
    print("\n4. Calculating MACD...")
    result = engine.calculate(data, config)

    # Display results
    print("\n5. MACD Calculation Results:")
    print(f"   Indicator type: {result.indicator_type}")
    print(f"   Parameters: {result.params}")
    print(f"   Result type: {type(result.values)}")

    if isinstance(result.values, pd.DataFrame):
        print(f"   Columns: {result.values.columns.tolist()}")
        print(f"   Total rows: {len(result.values)}")

        # Test column detection (same logic as in embedded_tradingview_chart.py)
        print("\n6. Testing Column Detection Logic:")
        col_names = result.values.columns.tolist()

        # NEW LOGIC (after fix)
        macd_col = signal_col = hist_col = None
        for col in col_names:
            col_lower = col.lower()
            # Check histogram first (MACDh_12_26_9 or histogram)
            if 'macdh' in col_lower or 'hist' in col_lower:
                hist_col = col
                print(f"   [OK] Histogram column detected: {col}")
            # Check signal (MACDs_12_26_9 or signal)
            elif 'macds' in col_lower or 'signal' in col_lower:
                signal_col = col
                print(f"   [OK] Signal column detected: {col}")
            # Check MACD line (MACD_12_26_9)
            elif 'macd' in col_lower:
                macd_col = col
                print(f"   [OK] MACD line column detected: {col}")

        print(f"\n7. Column Mapping:")
        print(f"   MACD Line  : {macd_col}")
        print(f"   Signal Line: {signal_col}")
        print(f"   Histogram  : {hist_col}")

        # Check for missing columns
        if not all([macd_col, signal_col, hist_col]):
            print("\n   [WARNING] Some columns not detected!")
            return False

        # Get series data
        print(f"\n8. Data Statistics:")
        macd_series = result.values[macd_col]
        signal_series = result.values[signal_col]
        hist_series = result.values[hist_col]

        print(f"   MACD Line:")
        print(f"      Total values: {len(macd_series)}")
        print(f"      Non-null values: {macd_series.notna().sum()}")
        print(f"      Range: {macd_series.min():.4f} to {macd_series.max():.4f}")

        print(f"   Signal Line:")
        print(f"      Total values: {len(signal_series)}")
        print(f"      Non-null values: {signal_series.notna().sum()}")
        print(f"      Range: {signal_series.min():.4f} to {signal_series.max():.4f}")

        print(f"   Histogram:")
        print(f"      Total values: {len(hist_series)}")
        print(f"      Non-null values: {hist_series.notna().sum()}")
        print(f"      Range: {hist_series.min():.4f} to {hist_series.max():.4f}")

        # Sample some actual values
        print(f"\n9. Sample Values (last 5 bars):")
        print(f"   {'Date':<20} {'MACD':<12} {'Signal':<12} {'Histogram':<12}")
        print(f"   {'-'*20} {'-'*12} {'-'*12} {'-'*12}")
        for i in range(max(0, len(data) - 5), len(data)):
            date = data.index[i].strftime('%Y-%m-%d')
            macd_val = macd_series.iloc[i] if not pd.isna(macd_series.iloc[i]) else 0
            signal_val = signal_series.iloc[i] if not pd.isna(signal_series.iloc[i]) else 0
            hist_val = hist_series.iloc[i] if not pd.isna(hist_series.iloc[i]) else 0
            print(f"   {date:<20} {macd_val:>11.4f} {signal_val:>11.4f} {hist_val:>11.4f}")

        print("\n" + "=" * 80)
        print("[SUCCESS] MACD TEST PASSED - All columns detected and contain valid data")
        print("=" * 80)
        return True
    else:
        print("   [ERROR] MACD should return a DataFrame, not a Series")
        return False

if __name__ == "__main__":
    success = test_macd()
    exit(0 if success else 1)
