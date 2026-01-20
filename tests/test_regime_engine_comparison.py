"""Test script comparing legacy RegimeEngine vs new RegimeEngineJSON.

Demonstrates:
1. Both engines classify the same market data
2. JSON-based approach is configurable
3. Results are comparable but JSON version uses exact thresholds from config
"""

import logging
from pathlib import Path

import pandas as pd
import numpy as np

from src.core.tradingbot.regime_engine import RegimeEngine
from src.core.tradingbot.regime_engine_json import RegimeEngineJSON
from src.core.tradingbot.models import FeatureVector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_data(scenario: str = "extreme_downtrend") -> pd.DataFrame:
    """Create sample OHLCV data for different market scenarios.

    Args:
        scenario: Market scenario to simulate
            - "extreme_downtrend": 4% drop with high volume
            - "strong_uptrend": 3% rally with volume spike
            - "range_bound": Sideways with low volume

    Returns:
        DataFrame with OHLCV data (100 bars)
    """
    np.random.seed(42)
    n = 100
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n, freq='5min')

    if scenario == "extreme_downtrend":
        # Simulate 4% drop over last 20 bars
        base_price = 100.0
        trend = np.linspace(0, -4, n)  # -4% over period
        noise = np.random.randn(n) * 0.3
        close = base_price + trend + noise

        # High volume in drop
        volume = 1000 + np.random.randint(200, 800, n)
        volume = volume.astype(float)  # Convert to float for multiplication
        volume[-20:] *= 2.5  # 2.5x volume spike

    elif scenario == "strong_uptrend":
        # Simulate 3% rally over last 20 bars
        base_price = 100.0
        trend = np.linspace(0, 3, n)  # +3% over period
        noise = np.random.randn(n) * 0.2
        close = base_price + trend + noise

        # Volume spike in rally
        volume = 1000 + np.random.randint(200, 600, n)
        volume = volume.astype(float)  # Convert to float for multiplication
        volume[-20:] *= 1.8  # 1.8x volume spike

    elif scenario == "range_bound":
        # Sideways with low volume
        base_price = 100.0
        noise = np.random.randn(n) * 0.4
        close = base_price + noise

        # Low volume
        volume = 800 + np.random.randint(100, 400, n)

    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    # Generate OHLCV
    high = close * 1.005 + np.abs(np.random.randn(n) * 0.1)
    low = close * 0.995 - np.abs(np.random.randn(n) * 0.1)
    open_ = close + np.random.randn(n) * 0.2

    df = pd.DataFrame({
        'timestamp': dates,
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })

    return df


def create_feature_vector_from_data(df: pd.DataFrame) -> FeatureVector:
    """Create FeatureVector from DataFrame (simplified).

    Args:
        df: OHLCV DataFrame

    Returns:
        FeatureVector with basic indicators
    """
    close = df['close']
    volume = df['volume']

    # Calculate SMAs
    sma_20 = close.rolling(20).mean().iloc[-1]
    sma_50 = close.rolling(50).mean().iloc[-1]

    # Simple ADX approximation (not accurate but sufficient for demo)
    high_low = df['high'] - df['low']
    atr = high_low.rolling(14).mean().iloc[-1]

    # Fake ADX calculation (normally would use proper ADX algorithm)
    price_change_pct = abs(close.pct_change().rolling(14).mean().iloc[-1] * 100)
    adx = min(60, max(10, price_change_pct * 10))  # Scale to ADX-like range

    # +DI/-DI approximation
    if close.iloc[-1] > close.iloc[-20]:
        plus_di = 25 + (close.iloc[-1] / close.iloc[-20] - 1) * 500
        minus_di = 15
    else:
        plus_di = 15
        minus_di = 25 + (1 - close.iloc[-1] / close.iloc[-20]) * 500

    # RSI approximation
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] > 0 else 1.0
    rsi = 100 - (100 / (1 + rs))

    # Bollinger Bands
    bb_ma = close.rolling(20).mean().iloc[-1]
    bb_std = close.rolling(20).std().iloc[-1]
    bb_upper = bb_ma + (2 * bb_std)
    bb_lower = bb_ma - (2 * bb_std)
    bb_width = (bb_upper - bb_lower) / bb_ma if bb_ma > 0 else 0

    # Volume
    volume_sma = volume.rolling(20).mean().iloc[-1]

    return FeatureVector(
        timestamp=df['timestamp'].iloc[-1],
        open=df['open'].iloc[-1],
        high=df['high'].iloc[-1],
        low=df['low'].iloc[-1],
        close=df['close'].iloc[-1],
        volume=df['volume'].iloc[-1],
        sma_20=sma_20,
        sma_50=sma_50,
        adx=adx,
        plus_di=plus_di,
        minus_di=minus_di,
        atr_14=atr,
        rsi_14=rsi,
        bb_upper=bb_upper,
        bb_lower=bb_lower,
        bb_width=bb_width,
        volume_sma=volume_sma
    )


def test_regime_comparison(scenario: str):
    """Compare legacy vs JSON engine for a market scenario.

    Args:
        scenario: Market scenario to test
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing scenario: {scenario.upper()}")
    logger.info(f"{'='*80}\n")

    # 1. Create sample data
    df = create_sample_data(scenario)
    features = create_feature_vector_from_data(df)

    logger.info(f"Sample data: {len(df)} bars")
    logger.info(f"Close prices: {df['close'].iloc[0]:.2f} → {df['close'].iloc[-1]:.2f} "
                f"({(df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100:+.2f}%)")
    logger.info(f"Volume: avg={df['volume'].mean():.0f}, last={df['volume'].iloc[-1]:.0f}\n")

    # 2. Test legacy RegimeEngine
    logger.info("--- LEGACY RegimeEngine (hardcoded) ---")
    legacy_engine = RegimeEngine()
    legacy_state = legacy_engine.classify(features)

    logger.info(f"Result: {legacy_state.regime_label}")
    logger.info(f"  Regime: {legacy_state.regime.name} (confidence: {legacy_state.regime_confidence:.2f})")
    logger.info(f"  Volatility: {legacy_state.volatility.name} (confidence: {legacy_state.volatility_confidence:.2f})")
    logger.info(f"  ADX: {legacy_state.adx_value:.2f}" if legacy_state.adx_value else "  ADX: N/A")
    logger.info(f"  ATR%: {legacy_state.atr_pct:.2f}%" if legacy_state.atr_pct else "  ATR%: N/A")

    # 3. Test new RegimeEngineJSON
    logger.info("\n--- NEW RegimeEngineJSON (JSON-based) ---")

    # Determine config based on scenario
    if "downtrend" in scenario:
        config_path = "03_JSON/Trading_Bot/momentum_downtrend.json"
    elif "uptrend" in scenario:
        config_path = "03_JSON/Trading_Bot/momentum_uptrend.json"
    else:
        config_path = "03_JSON/Trading_Bot/regime_based_comprehensive.json"

    logger.info(f"Using config: {config_path}")

    json_engine = RegimeEngineJSON()

    try:
        # Method 1: From DataFrame
        json_state = json_engine.classify_from_config(df, config_path, scope="entry")

        logger.info(f"Result: {json_state.regime_label}")
        logger.info(f"  Regime: {json_state.regime.name} (confidence: {json_state.regime_confidence:.2f})")
        logger.info(f"  Volatility: {json_state.volatility.name} (confidence: {json_state.volatility_confidence:.2f})")
        logger.info(f"  ADX: {json_state.adx_value:.2f}" if json_state.adx_value else "  ADX: N/A")
        logger.info(f"  ATR%: {json_state.atr_pct:.2f}%" if json_state.atr_pct else "  ATR%: N/A")

        # Method 2: From FeatureVector (for compatibility)
        logger.info("\n  Alternative: classify_from_features()")
        json_state_alt = json_engine.classify_from_features(features, config_path, scope="entry")
        logger.info(f"  Result: {json_state_alt.regime_label}")

    except Exception as e:
        logger.error(f"Error with JSON engine: {e}", exc_info=True)

    # 4. Comparison
    logger.info("\n--- COMPARISON ---")
    if legacy_state.regime == json_state.regime:
        logger.info("✓ Regime classification MATCHES")
    else:
        logger.info(f"✗ Regime classification DIFFERS: {legacy_state.regime.name} vs {json_state.regime.name}")

    if legacy_state.volatility == json_state.volatility:
        logger.info("✓ Volatility classification MATCHES")
    else:
        logger.info(f"✗ Volatility classification DIFFERS: {legacy_state.volatility.name} vs {json_state.volatility.name}")

    logger.info(f"\nConfidence delta: regime={abs(legacy_state.regime_confidence - json_state.regime_confidence):.2f}, "
                f"volatility={abs(legacy_state.volatility_confidence - json_state.volatility_confidence):.2f}")


def main():
    """Run comparison tests for all scenarios."""
    scenarios = [
        "extreme_downtrend",
        "strong_uptrend",
        "range_bound"
    ]

    for scenario in scenarios:
        try:
            test_regime_comparison(scenario)
        except Exception as e:
            logger.error(f"Error testing {scenario}: {e}", exc_info=True)

    logger.info(f"\n{'='*80}")
    logger.info("All tests completed!")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    main()
