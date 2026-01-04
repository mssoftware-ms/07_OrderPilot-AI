import pytest
import pandas as pd
import numpy as np

@pytest.fixture
def sample_df():
    """
    Creates a sample OHLCV DataFrame with some trend structure.
    """
    n = 300
    dates = pd.date_range(start="2025-01-01", periods=n, freq="1h")
    
    # Create a synthetic trend
    # Price goes up
    close = np.linspace(100, 150, n) + np.random.normal(0, 1, n)
    open_ = close - np.random.normal(0, 0.5, n)
    high = np.maximum(close, open_) + np.random.uniform(0, 2, n)
    low = np.minimum(close, open_) - np.random.uniform(0, 2, n)
    volume = np.random.randint(100, 1000, n)

    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume
    }, index=dates)
    
    return df
