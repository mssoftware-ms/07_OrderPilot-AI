"""Pytest configuration and fixtures for regime/indicator optimizer tests.

Provides reusable fixtures for:
- Sample OHLCV data generation
- Mock regime definitions
- Mock indicator engines
- Mock optimization configs
- Performance monitoring
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, MagicMock

from src.core.tradingbot.regime_engine_json import RegimeEngineJSON
from src.core.tradingbot.config.detector import RegimeDetector, ActiveRegime
from src.core.tradingbot.models import (
    RegimeState,
    RegimeType,
    VolatilityLevel,
    FeatureVector,
)
from src.core.tradingbot.config.models import RegimeDefinition, RegimeScope
from src.core.tradingbot.indicator_optimizer import IndicatorOptimizer, IndicatorScore
from src.core.tradingbot.indicator_grid_search import ParameterCombination


logger = logging.getLogger(__name__)


# ============================================================================
# OHLCV Data Fixtures
# ============================================================================

@pytest.fixture
def sample_ohlcv_data():
    """Generate realistic sample OHLCV data (100 bars, 1h timeframe)."""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')

    close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    open_prices = close_prices + np.random.randn(100) * 0.2
    high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(100) * 0.3)
    low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(100) * 0.3)
    volumes = 1000000 + np.random.randint(-200000, 200000, 100)

    return pd.DataFrame({
        'datetime': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    })


@pytest.fixture
def large_ohlcv_data():
    """Generate large OHLCV dataset (1000 bars) for realistic testing."""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=1000, freq='1h')

    close_prices = 100 + np.cumsum(np.random.randn(1000) * 0.3)
    open_prices = close_prices + np.random.randn(1000) * 0.2
    high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(1000) * 0.3)
    low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(1000) * 0.3)
    volumes = 1000000 + np.random.randint(-300000, 300000, 1000)

    return pd.DataFrame({
        'datetime': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    })


@pytest.fixture
def trending_data():
    """Generate uptrending data for bullish regime testing."""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')

    # Strong uptrend
    close_prices = 100 + np.cumsum(np.random.randn(100) * 0.3 + 0.5)
    open_prices = close_prices - 0.5 + np.random.randn(100) * 0.2
    high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(100) * 0.2)
    low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(100) * 0.2)
    volumes = 1200000 + np.random.randint(-100000, 100000, 100)

    return pd.DataFrame({
        'datetime': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    })


@pytest.fixture
def ranging_data():
    """Generate ranging data for sideways regime testing."""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')

    # Range between 98-102
    close_prices = 100 + np.random.randn(100) * 1.5
    close_prices = np.clip(close_prices, 98, 102)
    open_prices = close_prices + np.random.randn(100) * 0.5
    high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(100) * 0.3)
    low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(100) * 0.3)
    volumes = 800000 + np.random.randint(-100000, 100000, 100)

    return pd.DataFrame({
        'datetime': dates,
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    })


@pytest.fixture
def regime_labels():
    """Generate regime labels for data segmentation."""
    return pd.Series(['BULL'] * 40 + ['BEAR'] * 35 + ['SIDEWAYS'] * 25)


# ============================================================================
# FeatureVector Fixtures
# ============================================================================

@pytest.fixture
def bullish_features():
    """Create bullish FeatureVector."""
    return FeatureVector(
        timestamp=datetime.utcnow(),
        close=102.0,
        sma_20=101.0,
        sma_50=99.0,
        adx=28.0,
        rsi_14=65.0,
        atr_14=1.5,
        bb_upper=103.0,
        bb_lower=101.0,
        bb_width=2.0,
        volume=1200000,
        volume_sma=1000000
    )


@pytest.fixture
def bearish_features():
    """Create bearish FeatureVector."""
    return FeatureVector(
        timestamp=datetime.utcnow(),
        close=98.0,
        sma_20=99.0,
        sma_50=101.0,
        adx=26.0,
        rsi_14=35.0,
        atr_14=1.8,
        bb_upper=101.0,
        bb_lower=97.0,
        bb_width=4.0,
        volume=1100000,
        volume_sma=1000000
    )


@pytest.fixture
def ranging_features():
    """Create ranging market FeatureVector."""
    return FeatureVector(
        timestamp=datetime.utcnow(),
        close=100.0,
        sma_20=100.2,
        sma_50=100.1,
        adx=14.0,
        rsi_14=50.0,
        atr_14=0.8,
        bb_upper=101.5,
        bb_lower=98.5,
        bb_width=3.0,
        volume=900000,
        volume_sma=1000000
    )


# ============================================================================
# Regime Definition Fixtures
# ============================================================================

@pytest.fixture
def mock_regime_definitions():
    """Create mock regime definitions for testing."""
    from src.core.tradingbot.config.models import ConditionGroup

    return [
        RegimeDefinition(
            id="bull",
            name="Bull Regime",
            conditions=Mock(spec=ConditionGroup),
            priority=10,
            scope=RegimeScope.GLOBAL
        ),
        RegimeDefinition(
            id="bear",
            name="Bear Regime",
            conditions=Mock(spec=ConditionGroup),
            priority=9,
            scope=RegimeScope.GLOBAL
        ),
        RegimeDefinition(
            id="sideways",
            name="Sideways Regime",
            conditions=Mock(spec=ConditionGroup),
            priority=5,
            scope=RegimeScope.GLOBAL
        )
    ]


@pytest.fixture
def scoped_regime_definitions():
    """Create regime definitions with different scopes."""
    from src.core.tradingbot.config.models import ConditionGroup

    return [
        RegimeDefinition(
            id="entry_trend",
            name="Entry Trend",
            conditions=Mock(spec=ConditionGroup),
            priority=10,
            scope=RegimeScope.ENTRY
        ),
        RegimeDefinition(
            id="exit_trend",
            name="Exit Trend",
            conditions=Mock(spec=ConditionGroup),
            priority=8,
            scope=RegimeScope.EXIT
        ),
        RegimeDefinition(
            id="global_range",
            name="Global Range",
            conditions=Mock(spec=ConditionGroup),
            priority=5,
            scope=None
        )
    ]


# ============================================================================
# Indicator Optimizer Fixtures
# ============================================================================

@pytest.fixture
def indicator_combinations():
    """Create sample indicator parameter combinations."""
    return [
        ParameterCombination("RSI", {"period": 14}, "RSI_14_001"),
        ParameterCombination("RSI", {"period": 21}, "RSI_21_001"),
        ParameterCombination("MACD", {"fast": 12, "slow": 26}, "MACD_12_26_001"),
        ParameterCombination("BB", {"period": 20, "std_dev": 2.0}, "BB_20_2_001"),
        ParameterCombination("EMA", {"period": 9}, "EMA_9_001")
    ]


@pytest.fixture
def indicator_scores():
    """Create sample indicator scores for testing selection/ranking."""
    now = datetime.utcnow()

    return [
        IndicatorScore(
            indicator_type="RSI",
            params={"period": 14},
            combination_id="RSI_14_001",
            sharpe_ratio=2.1,
            win_rate=0.72,
            profit_factor=2.3,
            max_drawdown=0.08,
            total_trades=150,
            avg_trade_duration_bars=6.2,
            net_profit_pct=28.5,
            composite_score=0.88,
            optimization_timestamp=now
        ),
        IndicatorScore(
            indicator_type="RSI",
            params={"period": 21},
            combination_id="RSI_21_001",
            sharpe_ratio=1.8,
            win_rate=0.68,
            profit_factor=1.9,
            max_drawdown=0.12,
            total_trades=120,
            avg_trade_duration_bars=7.5,
            net_profit_pct=22.3,
            composite_score=0.78,
            optimization_timestamp=now
        ),
        IndicatorScore(
            indicator_type="MACD",
            params={"fast": 12, "slow": 26},
            combination_id="MACD_12_26_001",
            sharpe_ratio=1.5,
            win_rate=0.65,
            profit_factor=1.6,
            max_drawdown=0.15,
            total_trades=100,
            avg_trade_duration_bars=8.1,
            net_profit_pct=18.5,
            composite_score=0.68,
            optimization_timestamp=now
        ),
    ]


# ============================================================================
# RegimeState Fixtures
# ============================================================================

@pytest.fixture
def bull_regime_state():
    """Create bullish RegimeState."""
    return RegimeState(
        timestamp=datetime.utcnow(),
        regime=RegimeType.TREND_UP,
        volatility=VolatilityLevel.NORMAL,
        regime_confidence=0.85,
        volatility_confidence=0.75,
        adx_value=28.0,
        atr_pct=1.2,
        bb_width_pct=2.0
    )


@pytest.fixture
def bear_regime_state():
    """Create bearish RegimeState."""
    return RegimeState(
        timestamp=datetime.utcnow(),
        regime=RegimeType.TREND_DOWN,
        volatility=VolatilityLevel.HIGH,
        regime_confidence=0.80,
        volatility_confidence=0.70,
        adx_value=26.0,
        atr_pct=1.5,
        bb_width_pct=3.0
    )


@pytest.fixture
def range_regime_state():
    """Create ranging RegimeState."""
    return RegimeState(
        timestamp=datetime.utcnow(),
        regime=RegimeType.RANGE,
        volatility=VolatilityLevel.LOW,
        regime_confidence=0.65,
        volatility_confidence=0.60,
        adx_value=14.0,
        atr_pct=0.8,
        bb_width_pct=2.5
    )


# ============================================================================
# Mock Engine Fixtures
# ============================================================================

@pytest.fixture
def mock_indicator_engine():
    """Create mock IndicatorEngine."""
    engine = Mock()
    engine.calculate.return_value = Mock(values=pd.Series([50.0, 55.0, 52.0]))
    return engine


@pytest.fixture
def mock_config_loader():
    """Create mock ConfigLoader."""
    loader = Mock()
    config = Mock()
    config.regimes = []
    config.indicators = []
    loader.load_config.return_value = config
    return loader


# ============================================================================
# Performance Tracking Fixtures
# ============================================================================

@pytest.fixture
def performance_tracker():
    """Track test execution times."""
    class PerformanceTracker:
        def __init__(self):
            self.times: Dict[str, float] = {}
            self.start_time: Optional[float] = None

        def start(self):
            import time
            self.start_time = time.time()

        def end(self, name: str):
            import time
            if self.start_time:
                elapsed = time.time() - self.start_time
                self.times[name] = elapsed
                logger.info(f"{name}: {elapsed:.3f}s")

        def report(self):
            total = sum(self.times.values())
            logger.info(f"\n{'=' * 50}")
            logger.info("PERFORMANCE SUMMARY")
            logger.info(f"{'=' * 50}")
            for name, elapsed in sorted(self.times.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"{name:40s}: {elapsed:8.3f}s")
            logger.info(f"{'=' * 50}")
            logger.info(f"{'TOTAL':40s}: {total:8.3f}s")

    return PerformanceTracker()


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


@pytest.fixture(scope="session")
def test_session_info():
    """Log test session information."""
    logger.info("\n" + "=" * 80)
    logger.info("COMPREHENSIVE UNIT TESTS: REGIME OPTIMIZER & INDICATOR OPTIMIZATION")
    logger.info("=" * 80)
    logger.info(f"Start Time: {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
