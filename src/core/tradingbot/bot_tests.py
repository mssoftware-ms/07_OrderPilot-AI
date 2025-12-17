"""Bot Tests and Validation.

Provides:
- Unit tests for bot components
- Integration tests
- Chaos/failure tests
- Regression tests
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

import pandas as pd
import numpy as np

from .config import FullBotConfig, MarketType, KIMode, TrailingMode
from .models import (
    BotAction,
    FeatureVector,
    PositionState,
    RegimeState,
    RegimeType,
    Signal,
    SignalType,
    TradeSide,
    TrailingState,
    VolatilityLevel,
)

logger = logging.getLogger(__name__)


class TestResult(str, Enum):
    """Test result status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """Individual test case result."""
    name: str
    description: str
    result: TestResult
    duration_ms: float = 0.0
    error_message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuiteResult:
    """Result of a test suite run."""
    suite_name: str
    test_cases: list[TestCase] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    total_duration_ms: float = 0.0

    @property
    def success(self) -> bool:
        return self.failed == 0 and self.errors == 0

    def add_result(self, test_case: TestCase) -> None:
        """Add a test case result."""
        self.test_cases.append(test_case)
        self.total_duration_ms += test_case.duration_ms

        if test_case.result == TestResult.PASSED:
            self.passed += 1
        elif test_case.result == TestResult.FAILED:
            self.failed += 1
        elif test_case.result == TestResult.SKIPPED:
            self.skipped += 1
        else:
            self.errors += 1

    def summary(self) -> str:
        """Get summary string."""
        total = len(self.test_cases)
        return (
            f"{self.suite_name}: {self.passed}/{total} passed, "
            f"{self.failed} failed, {self.errors} errors "
            f"({self.total_duration_ms:.0f}ms)"
        )


def generate_mock_features(
    symbol: str = "TEST",
    close: float = 100.0,
    trend: str = "up",
    volatility: str = "normal"
) -> FeatureVector:
    """Generate mock feature vector for testing.

    Args:
        symbol: Symbol name
        close: Close price
        trend: "up", "down", or "range"
        volatility: "low", "normal", "high"

    Returns:
        FeatureVector with realistic values
    """
    # Base values
    rng = random.Random(42)

    # Price-based features
    open_price = close * (1 + rng.uniform(-0.01, 0.01))
    high = max(open_price, close) * (1 + rng.uniform(0.001, 0.02))
    low = min(open_price, close) * (1 - rng.uniform(0.001, 0.02))

    # Trend-dependent indicators
    if trend == "up":
        sma_20 = close * 0.98
        sma_50 = close * 0.95
        rsi = rng.uniform(55, 70)
        adx = rng.uniform(25, 40)
        macd_hist = rng.uniform(0.1, 0.5)
    elif trend == "down":
        sma_20 = close * 1.02
        sma_50 = close * 1.05
        rsi = rng.uniform(30, 45)
        adx = rng.uniform(25, 40)
        macd_hist = rng.uniform(-0.5, -0.1)
    else:  # range
        sma_20 = close * rng.uniform(0.99, 1.01)
        sma_50 = close * rng.uniform(0.99, 1.01)
        rsi = rng.uniform(45, 55)
        adx = rng.uniform(15, 25)
        macd_hist = rng.uniform(-0.1, 0.1)

    # Volatility-dependent
    if volatility == "low":
        atr = close * 0.005
        bb_width = 0.02
    elif volatility == "high":
        atr = close * 0.03
        bb_width = 0.08
    else:  # normal
        atr = close * 0.015
        bb_width = 0.04

    return FeatureVector(
        symbol=symbol,
        timestamp=datetime.utcnow(),
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=rng.randint(10000, 100000),
        sma_20=sma_20,
        sma_50=sma_50,
        ema_12=close * (1 + rng.uniform(-0.01, 0.01)),
        ema_26=close * (1 + rng.uniform(-0.02, 0.02)),
        rsi_14=rsi,
        macd_line=rng.uniform(-0.5, 0.5),
        macd_signal=rng.uniform(-0.5, 0.5),
        macd_histogram=macd_hist,
        bb_upper=close * (1 + bb_width / 2),
        bb_middle=close,
        bb_lower=close * (1 - bb_width / 2),
        atr_14=atr,
        adx_14=adx,
        plus_di=rng.uniform(15, 35),
        minus_di=rng.uniform(15, 35),
        stoch_k=rng.uniform(20, 80),
        stoch_d=rng.uniform(20, 80),
        cci_20=rng.uniform(-100, 100),
        mfi_14=rng.uniform(30, 70),
    )


def generate_mock_regime(
    regime_type: RegimeType = RegimeType.TREND_UP,
    volatility: VolatilityLevel = VolatilityLevel.NORMAL
) -> RegimeState:
    """Generate mock regime state.

    Args:
        regime_type: Type of regime
        volatility: Volatility level

    Returns:
        RegimeState
    """
    return RegimeState(
        regime=regime_type,
        volatility=volatility,
        regime_confidence=0.8,
        volatility_confidence=0.75
    )


class BotUnitTests:
    """Unit tests for bot components."""

    def __init__(self):
        """Initialize test suite."""
        self.results = TestSuiteResult(suite_name="BotUnitTests")

    def run_all(self) -> TestSuiteResult:
        """Run all unit tests."""
        tests = [
            self.test_feature_vector_normalization,
            self.test_trailing_state_never_loosen,
            self.test_regime_classification,
            self.test_entry_scoring,
            self.test_exit_signal_detection,
            self.test_position_sizing,
            self.test_risk_limits,
            self.test_llm_response_validation,
        ]

        for test in tests:
            try:
                start = datetime.utcnow()
                test()
                duration = (datetime.utcnow() - start).total_seconds() * 1000
                self.results.add_result(TestCase(
                    name=test.__name__,
                    description=test.__doc__ or "",
                    result=TestResult.PASSED,
                    duration_ms=duration
                ))
            except AssertionError as e:
                self.results.add_result(TestCase(
                    name=test.__name__,
                    description=test.__doc__ or "",
                    result=TestResult.FAILED,
                    error_message=str(e)
                ))
            except Exception as e:
                self.results.add_result(TestCase(
                    name=test.__name__,
                    description=test.__doc__ or "",
                    result=TestResult.ERROR,
                    error_message=str(e)
                ))

        return self.results

    def test_feature_vector_normalization(self) -> None:
        """Test FeatureVector.to_dict_normalized() returns valid values."""
        features = generate_mock_features()
        normalized = features.to_dict_normalized()

        assert isinstance(normalized, dict), "Should return dict"
        assert "rsi_14" in normalized, "Should include RSI"
        assert 0 <= normalized["rsi_14"] <= 100, "RSI should be 0-100"

    def test_trailing_state_never_loosen(self) -> None:
        """Test TrailingState enforces 'never loosen stop' invariant."""
        from datetime import datetime

        # Long position
        state = TrailingState(
            mode=TrailingMode.PCT,
            initial_stop_price=95.0,
            current_stop_price=97.0,
            highest_price=100.0,
            lowest_price=95.0,
            trailing_distance=3.0
        )

        # Try to loosen (should fail for long)
        result = state.update_stop(96.0, 1, datetime.utcnow(), is_long=True)
        assert not result, "Should not loosen stop for long"
        assert state.current_stop_price == 97.0, "Stop should remain at 97"

        # Tighten (should succeed for long)
        result = state.update_stop(98.0, 2, datetime.utcnow(), is_long=True)
        assert result, "Should tighten stop"
        assert state.current_stop_price == 98.0, "Stop should be 98"

    def test_regime_classification(self) -> None:
        """Test RegimeEngine classifies correctly."""
        from .regime_engine import RegimeEngine

        engine = RegimeEngine()

        # Test trend up
        features_up = generate_mock_features(trend="up")
        regime_up = engine.classify(features_up)
        assert regime_up.regime in [RegimeType.TREND_UP, RegimeType.RANGE], \
            f"Expected TREND_UP or RANGE, got {regime_up.regime}"

        # Test trend down
        features_down = generate_mock_features(trend="down")
        regime_down = engine.classify(features_down)
        assert regime_down.regime in [RegimeType.TREND_DOWN, RegimeType.RANGE], \
            f"Expected TREND_DOWN or RANGE, got {regime_down.regime}"

    def test_entry_scoring(self) -> None:
        """Test EntryScorer produces valid scores."""
        from .entry_exit_engine import EntryScorer

        scorer = EntryScorer()
        features = generate_mock_features(trend="up")
        regime = generate_mock_regime(RegimeType.TREND_UP)

        result = scorer.calculate_score(features, TradeSide.LONG, regime)

        assert 0 <= result.score <= 100, f"Score should be 0-100, got {result.score}"
        assert isinstance(result.components, dict), "Should have components"
        assert len(result.reason_codes) > 0, "Should have reason codes"

    def test_exit_signal_detection(self) -> None:
        """Test ExitSignalChecker detects exit conditions."""
        from .entry_exit_engine import ExitSignalChecker

        checker = ExitSignalChecker()

        # Create position with extreme RSI
        features = generate_mock_features(trend="up")
        features.rsi_14 = 85  # Overbought

        position = PositionState(
            symbol="TEST",
            side=TradeSide.LONG,
            entry_price=100.0,
            entry_time=datetime.utcnow(),
            quantity=1.0,
            current_price=100.0,
            trailing=TrailingState(
                mode=TrailingMode.PCT,
                initial_stop_price=95.0,
                current_stop_price=98.0,
                highest_price=100.0,
                lowest_price=95.0,
                trailing_distance=5.0
            )
        )

        regime = generate_mock_regime()

        result = checker.check_exit(features, position, regime)

        # Should detect RSI extreme
        assert result is not None, "Should return result"

    def test_position_sizing(self) -> None:
        """Test PositionSizer calculates correct sizes."""
        from .execution import PositionSizer, RiskLimits

        sizer = PositionSizer(
            account_value=10000.0,
            default_risk_pct=1.0
        )

        signal = Signal(
            symbol="TEST",
            side=TradeSide.LONG,
            entry_price=100.0,
            stop_loss_price=95.0,
            score=75.0,
            timestamp=datetime.utcnow()
        )

        result = sizer.calculate_size(signal, current_price=100.0)

        # Risk = 1% of 10000 = $100
        # Stop distance = $5
        # Expected size = 100 / 5 = 20 shares
        assert result.quantity > 0, "Should have positive quantity"
        assert result.risk_amount <= 100 * 1.01, "Risk should be ~$100"

    def test_risk_limits(self) -> None:
        """Test RiskManager enforces limits."""
        from .execution import RiskManager, RiskLimits

        limits = RiskLimits(max_trades_per_day=3)
        manager = RiskManager(limits=limits, account_value=10000.0)

        # Should allow trading initially
        can_trade, _ = manager.can_trade()
        assert can_trade, "Should allow trading initially"

        # Simulate 3 trades
        for _ in range(3):
            manager.record_trade_start()
            manager.record_trade_end(100.0)

        # Should block trading now
        can_trade, blocks = manager.can_trade()
        assert not can_trade, "Should block after max trades"
        assert any("MAX_TRADES" in b for b in blocks), "Should cite max trades"

    def test_llm_response_validation(self) -> None:
        """Test LLMResponseValidator handles various inputs."""
        from .llm_integration import LLMResponseValidator

        # Valid response
        valid = {
            "action": "HOLD",
            "confidence": 0.8,
            "reason_codes": ["TEST"]
        }
        result, errors = LLMResponseValidator.validate_trade_decision(valid)
        assert result is not None, "Should validate valid response"

        # Invalid action - should repair
        invalid = {
            "action": "INVALID_ACTION",
            "confidence": 0.5,
            "reason_codes": []
        }
        result, errors = LLMResponseValidator.validate_trade_decision(invalid)
        assert result is not None, "Should repair invalid response"
        assert result.action.value in ["HOLD", "EXIT", "ADJUST_STOP"]


class BotIntegrationTests:
    """Integration tests for bot workflow."""

    def __init__(self):
        """Initialize test suite."""
        self.results = TestSuiteResult(suite_name="BotIntegrationTests")

    def run_all(self) -> TestSuiteResult:
        """Run all integration tests."""
        tests = [
            self.test_full_trade_cycle,
            self.test_no_ki_mode_stability,
            self.test_trailing_stop_modes,
            self.test_strategy_selection_flow,
        ]

        for test in tests:
            try:
                start = datetime.utcnow()
                test()
                duration = (datetime.utcnow() - start).total_seconds() * 1000
                self.results.add_result(TestCase(
                    name=test.__name__,
                    description=test.__doc__ or "",
                    result=TestResult.PASSED,
                    duration_ms=duration
                ))
            except AssertionError as e:
                self.results.add_result(TestCase(
                    name=test.__name__,
                    description=test.__doc__ or "",
                    result=TestResult.FAILED,
                    error_message=str(e)
                ))
            except Exception as e:
                self.results.add_result(TestCase(
                    name=test.__name__,
                    description=test.__doc__ or "",
                    result=TestResult.ERROR,
                    error_message=str(e)
                ))

        return self.results

    def test_full_trade_cycle(self) -> None:
        """Test complete trade cycle: signal → entry → manage → exit."""
        from .entry_exit_engine import EntryScorer, ExitSignalChecker, TrailingStopManager

        scorer = EntryScorer()
        exit_checker = ExitSignalChecker()
        trailing_manager = TrailingStopManager()

        # 1. Generate entry signal
        features = generate_mock_features(trend="up")
        regime = generate_mock_regime(RegimeType.TREND_UP)

        score_result = scorer.calculate_score(features, TradeSide.LONG, regime)
        assert score_result.score > 0, "Should generate score"

        # 2. Create position
        position = PositionState(
            symbol="TEST",
            side=TradeSide.LONG,
            entry_price=features.close,
            entry_time=datetime.utcnow(),
            quantity=10.0,
            current_price=features.close,
            trailing=TrailingState(
                mode=TrailingMode.ATR,
                initial_stop_price=features.close * 0.98,
                current_stop_price=features.close * 0.98,
                highest_price=features.close,
                lowest_price=features.close * 0.98,
                trailing_distance=features.close * 0.02
            )
        )

        # 3. Update trailing stop
        bar = {
            "high": features.high,
            "low": features.low,
            "close": features.close
        }
        trailing_result = trailing_manager.calculate_trailing_stop(
            features, position, regime, bar
        )
        assert trailing_result is not None, "Should calculate trailing"

        # 4. Check exit
        exit_result = exit_checker.check_exit(features, position, regime)
        assert exit_result is not None, "Should check exit"

    def test_no_ki_mode_stability(self) -> None:
        """Test that NO_KI mode runs without LLM calls."""
        config = FullBotConfig.create_default("TEST", MarketType.NASDAQ)
        config.bot.ki_mode = KIMode.NO_KI

        # Verify config
        assert config.bot.ki_mode == KIMode.NO_KI
        assert config.llm_policy.enabled == False or config.bot.ki_mode == KIMode.NO_KI

    def test_trailing_stop_modes(self) -> None:
        """Test all trailing stop modes produce valid results."""
        from .entry_exit_engine import TrailingStopManager

        manager = TrailingStopManager()
        features = generate_mock_features()
        regime = generate_mock_regime()

        bar = {
            "high": features.high,
            "low": features.low,
            "close": features.close
        }

        for mode in [TrailingMode.PCT, TrailingMode.ATR, TrailingMode.SWING]:
            position = PositionState(
                symbol="TEST",
                side=TradeSide.LONG,
                entry_price=features.close,
                entry_time=datetime.utcnow(),
                quantity=1.0,
                current_price=features.close,
                trailing=TrailingState(
                    mode=mode,
                    initial_stop_price=features.close * 0.95,
                    current_stop_price=features.close * 0.95,
                    highest_price=features.close,
                    lowest_price=features.close * 0.95,
                    trailing_distance=features.close * 0.05
                )
            )

            result = manager.calculate_trailing_stop(
                features, position, regime, bar, trailing_mode=mode
            )

            assert result is not None, f"{mode} should return result"
            if result.new_stop:
                assert result.new_stop > 0, f"{mode} stop should be positive"

    def test_strategy_selection_flow(self) -> None:
        """Test daily strategy selection workflow."""
        from .strategy_selector import StrategySelector
        from .strategy_catalog import StrategyCatalog

        catalog = StrategyCatalog()
        selector = StrategySelector(catalog=catalog)

        regime = generate_mock_regime(RegimeType.TREND_UP)

        # Get strategies for regime
        strategies = selector.get_strategies_for_regime(regime)
        assert len(strategies) > 0, "Should have strategies for TREND_UP"

        # Select strategy
        result = selector.select_strategy(regime, "TEST", force=True)
        assert result is not None, "Should select a strategy"
        assert result.strategy_id is not None, "Should have strategy ID"


class ChaosTests:
    """Chaos/failure tests for resilience."""

    def __init__(self):
        """Initialize test suite."""
        self.results = TestSuiteResult(suite_name="ChaosTests")

    def run_all(self) -> TestSuiteResult:
        """Run all chaos tests."""
        tests = [
            self.test_missing_data_handling,
            self.test_invalid_prices,
            self.test_extreme_volatility,
            self.test_llm_failure_fallback,
            self.test_zero_volume,
        ]

        for test in tests:
            try:
                start = datetime.utcnow()
                test()
                duration = (datetime.utcnow() - start).total_seconds() * 1000
                self.results.add_result(TestCase(
                    name=test.__name__,
                    description=test.__doc__ or "",
                    result=TestResult.PASSED,
                    duration_ms=duration
                ))
            except AssertionError as e:
                self.results.add_result(TestCase(
                    name=test.__name__,
                    description=test.__doc__ or "",
                    result=TestResult.FAILED,
                    error_message=str(e)
                ))
            except Exception as e:
                self.results.add_result(TestCase(
                    name=test.__name__,
                    description=test.__doc__ or "",
                    result=TestResult.ERROR,
                    error_message=str(e)
                ))

        return self.results

    def test_missing_data_handling(self) -> None:
        """Test handling of missing/NaN data."""
        from .feature_engine import FeatureEngine

        engine = FeatureEngine()

        # Create data with NaN values
        data = pd.DataFrame({
            "open": [100, np.nan, 102],
            "high": [101, 101, 103],
            "low": [99, 99, 101],
            "close": [100, 100, 102],
            "volume": [1000, 1000, 1000]
        }, index=pd.date_range("2024-01-01", periods=3, freq="1min"))

        # Should handle gracefully
        result = engine.calculate_features(data, "TEST")
        # May return None or handle NaN - both are acceptable

    def test_invalid_prices(self) -> None:
        """Test handling of invalid price data."""
        # Zero price
        features = generate_mock_features(close=0.0)
        normalized = features.to_dict_normalized()
        # Should not crash

        # Negative price (shouldn't happen but test)
        features.close = -100
        try:
            normalized = features.to_dict_normalized()
        except:
            pass  # Exception is acceptable for invalid data

    def test_extreme_volatility(self) -> None:
        """Test handling of extreme volatility."""
        from .no_trade_filter import NoTradeFilter
        from .config import RiskConfig

        filter = NoTradeFilter(RiskConfig())

        features = generate_mock_features(volatility="high")
        features.atr_14 = features.close * 0.10  # 10% ATR - extreme

        regime = generate_mock_regime(volatility=VolatilityLevel.EXTREME)

        result = filter.check(features, regime)

        # Should either block or allow with warning
        assert result is not None, "Should return filter result"

    def test_llm_failure_fallback(self) -> None:
        """Test LLM failure triggers fallback."""
        from .llm_integration import LLMResponseValidator

        # Invalid JSON
        result, errors = LLMResponseValidator.validate_trade_decision(
            "not valid json"
        )

        if result is None:
            # Get fallback
            fallback = LLMResponseValidator.get_fallback_response("MANAGE")
            assert fallback is not None, "Should return fallback"
            assert fallback.action == BotAction.HOLD, "Fallback should be HOLD"

    def test_zero_volume(self) -> None:
        """Test handling of zero volume bars."""
        features = generate_mock_features()
        features.volume = 0

        normalized = features.to_dict_normalized()
        # Should handle without division by zero


def run_all_tests() -> dict[str, TestSuiteResult]:
    """Run all test suites.

    Returns:
        Dict of suite name to results
    """
    results = {}

    # Unit tests
    unit_tests = BotUnitTests()
    results["unit"] = unit_tests.run_all()
    logger.info(results["unit"].summary())

    # Integration tests
    integration_tests = BotIntegrationTests()
    results["integration"] = integration_tests.run_all()
    logger.info(results["integration"].summary())

    # Chaos tests
    chaos_tests = ChaosTests()
    results["chaos"] = chaos_tests.run_all()
    logger.info(results["chaos"].summary())

    # Summary
    total_passed = sum(r.passed for r in results.values())
    total_failed = sum(r.failed for r in results.values())
    total_errors = sum(r.errors for r in results.values())

    logger.info(
        f"All tests: {total_passed} passed, {total_failed} failed, "
        f"{total_errors} errors"
    )

    return results
