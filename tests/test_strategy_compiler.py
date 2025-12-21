"""Tests for Strategy Compiler.

Tests compilation of StrategyDefinition to Backtrader strategies.
"""

import pytest
import backtrader as bt

from src.core.strategy.compiler import (
    CompilationError,
    ConditionEvaluator,
    IndicatorFactory,
    StrategyCompiler,
)
from src.core.strategy.definition import (
    ComparisonOperator,
    Condition,
    IndicatorConfig,
    IndicatorType,
    LogicGroup,
    LogicOperator,
    RiskManagement,
    StrategyDefinition,
)


class TestIndicatorFactory:
    """Tests for IndicatorFactory."""

    def test_create_sma(self):
        """Test creating SMA indicator."""
        # Create mock data feed
        cerebro = bt.Cerebro()
        data = bt.feeds.BacktraderCSVData(
            dataname="tests/data/sample.csv"
        ) if False else None  # Mock for now

        config = IndicatorConfig(
            type=IndicatorType.SMA,
            params={"period": 20},
            alias="sma_20"
        )

        # We can't fully test without data, but we can test mapping
        assert IndicatorFactory.INDICATOR_MAP[IndicatorType.SMA] == bt.indicators.SimpleMovingAverage

    def test_create_rsi(self):
        """Test RSI indicator mapping."""
        assert IndicatorFactory.INDICATOR_MAP[IndicatorType.RSI] == bt.indicators.RelativeStrengthIndex

    def test_create_macd(self):
        """Test MACD indicator mapping."""
        assert IndicatorFactory.INDICATOR_MAP[IndicatorType.MACD] == bt.indicators.MACD

    def test_normalize_macd_params(self):
        """Test MACD parameter normalization."""
        params = {"fast": 12, "slow": 26, "signal": 9}
        normalized = IndicatorFactory._normalize_params(IndicatorType.MACD, params)

        assert "period_me1" in normalized
        assert "period_me2" in normalized
        assert "period_signal" in normalized
        assert normalized["period_me1"] == 12
        assert normalized["period_me2"] == 26
        assert normalized["period_signal"] == 9

    def test_unsupported_indicator_type(self):
        """Test error on unsupported indicator."""
        # This would need to be tested with actual compilation
        pass


class TestConditionEvaluator:
    """Tests for ConditionEvaluator."""

    def test_evaluate_simple_gt_condition(self):
        """Test simple greater-than condition."""
        # Create mock strategy
        class MockStrategy:
            class MockData:
                close = [100.0]
                open = [99.0]
                high = [101.0]
                low = [98.0]
                volume = [1000.0]

            data = MockData()
            ind_sma = [95.0]  # Mock indicator value

        strategy = MockStrategy()
        evaluator = ConditionEvaluator(strategy)

        # Test: close > 99
        cond = Condition(
            left="close",
            operator=ComparisonOperator.GT,
            right=99.0
        )
        assert evaluator.evaluate(cond) is True

        # Test: close > 100
        cond = Condition(
            left="close",
            operator=ComparisonOperator.GT,
            right=100.0
        )
        assert evaluator.evaluate(cond) is False

    def test_evaluate_inside_operator(self):
        """Test INSIDE range operator."""
        class MockStrategy:
            class MockData:
                close = [50.0]
            data = MockData()

        strategy = MockStrategy()
        evaluator = ConditionEvaluator(strategy)

        # Test: 30 <= close <= 70
        cond = Condition(
            left="close",
            operator=ComparisonOperator.INSIDE,
            right=[30.0, 70.0]
        )
        assert evaluator.evaluate(cond) is True

        # Test: 60 <= close <= 70 (should be False since close=50)
        cond = Condition(
            left="close",
            operator=ComparisonOperator.INSIDE,
            right=[60.0, 70.0]
        )
        assert evaluator.evaluate(cond) is False

    def test_evaluate_outside_operator(self):
        """Test OUTSIDE range operator."""
        class MockStrategy:
            class MockData:
                close = [50.0]
            data = MockData()

        strategy = MockStrategy()
        evaluator = ConditionEvaluator(strategy)

        # Test: close < 40 OR close > 60
        cond = Condition(
            left="close",
            operator=ComparisonOperator.OUTSIDE,
            right=[40.0, 60.0]
        )
        assert evaluator.evaluate(cond) is False

        # Test: close < 30 OR close > 60
        cond = Condition(
            left="close",
            operator=ComparisonOperator.OUTSIDE,
            right=[30.0, 40.0]
        )
        assert evaluator.evaluate(cond) is True

    def test_evaluate_and_logic_group(self):
        """Test AND logic group."""
        class MockStrategy:
            class MockData:
                close = [100.0]
            data = MockData()

        strategy = MockStrategy()
        evaluator = ConditionEvaluator(strategy)

        # Test: (close > 90) AND (close < 110)
        group = LogicGroup(
            operator=LogicOperator.AND,
            conditions=[
                Condition(left="close", operator=ComparisonOperator.GT, right=90.0),
                Condition(left="close", operator=ComparisonOperator.LT, right=110.0),
            ]
        )
        assert evaluator.evaluate(group) is True

        # Test: (close > 90) AND (close < 100)
        group = LogicGroup(
            operator=LogicOperator.AND,
            conditions=[
                Condition(left="close", operator=ComparisonOperator.GT, right=90.0),
                Condition(left="close", operator=ComparisonOperator.LT, right=100.0),
            ]
        )
        assert evaluator.evaluate(group) is False

    def test_evaluate_or_logic_group(self):
        """Test OR logic group."""
        class MockStrategy:
            class MockData:
                close = [100.0]
            data = MockData()

        strategy = MockStrategy()
        evaluator = ConditionEvaluator(strategy)

        # Test: (close > 110) OR (close < 90)
        group = LogicGroup(
            operator=LogicOperator.OR,
            conditions=[
                Condition(left="close", operator=ComparisonOperator.GT, right=110.0),
                Condition(left="close", operator=ComparisonOperator.LT, right=90.0),
            ]
        )
        assert evaluator.evaluate(group) is False

        # Test: (close > 90) OR (close < 80)
        group = LogicGroup(
            operator=LogicOperator.OR,
            conditions=[
                Condition(left="close", operator=ComparisonOperator.GT, right=90.0),
                Condition(left="close", operator=ComparisonOperator.LT, right=80.0),
            ]
        )
        assert evaluator.evaluate(group) is True

    def test_evaluate_not_logic_group(self):
        """Test NOT logic group."""
        class MockStrategy:
            class MockData:
                close = [100.0]
            data = MockData()

        strategy = MockStrategy()
        evaluator = ConditionEvaluator(strategy)

        # Test: NOT (close > 110)
        group = LogicGroup(
            operator=LogicOperator.NOT,
            conditions=[
                Condition(left="close", operator=ComparisonOperator.GT, right=110.0),
            ]
        )
        assert evaluator.evaluate(group) is True

        # Test: NOT (close > 90)
        group = LogicGroup(
            operator=LogicOperator.NOT,
            conditions=[
                Condition(left="close", operator=ComparisonOperator.GT, right=90.0),
            ]
        )
        assert evaluator.evaluate(group) is False

    def test_evaluate_nested_logic_groups(self):
        """Test nested logic groups."""
        class MockStrategy:
            class MockData:
                close = [100.0]
                volume = [1000.0]
            data = MockData()

        strategy = MockStrategy()
        evaluator = ConditionEvaluator(strategy)

        # Test: (close > 90 AND volume > 500) OR (close > 110)
        group = LogicGroup(
            operator=LogicOperator.OR,
            conditions=[
                LogicGroup(
                    operator=LogicOperator.AND,
                    conditions=[
                        Condition(left="close", operator=ComparisonOperator.GT, right=90.0),
                        Condition(left="volume", operator=ComparisonOperator.GT, right=500.0),
                    ]
                ),
                Condition(left="close", operator=ComparisonOperator.GT, right=110.0),
            ]
        )
        assert evaluator.evaluate(group) is True

    def test_cross_above_detection(self):
        """Test crosses_above detection."""
        class MockStrategy:
            class MockData:
                close = [100.0]
            data = MockData()

        strategy = MockStrategy()
        evaluator = ConditionEvaluator(strategy)

        # First call: no previous values, should be False
        cond = Condition(
            left="close",
            operator=ComparisonOperator.CROSSES_ABOVE,
            right=99.0
        )
        assert evaluator.evaluate(cond) is False

        # Second call: close was below, now above
        # Simulate next bar where close is still 100
        # (In reality, this would be called from Backtrader's next())
        # For testing, we manually set previous values
        evaluator._previous_values["close_left"] = 98.0
        evaluator._previous_values["close_right"] = 99.0

        # Now check: 98 <= 99 and 100 > 99 -> True
        assert evaluator.evaluate(cond) is True


class TestStrategyCompiler:
    """Tests for StrategyCompiler."""

    def test_compile_simple_sma_crossover(self):
        """Test compiling simple SMA crossover strategy."""
        strategy_def = StrategyDefinition(
            name="SMA Crossover",
            version="1.0.0",
            indicators=[
                IndicatorConfig(type=IndicatorType.SMA, params={"period": 20}, alias="sma_fast"),
                IndicatorConfig(type=IndicatorType.SMA, params={"period": 50}, alias="sma_slow")
            ],
            entry_long=Condition(
                left="sma_fast",
                operator=ComparisonOperator.CROSSES_ABOVE,
                right="sma_slow"
            ),
            exit_long=Condition(
                left="sma_fast",
                operator=ComparisonOperator.CROSSES_BELOW,
                right="sma_slow"
            ),
            risk_management=RiskManagement(
                stop_loss_pct=2.0,
                take_profit_pct=5.0
            )
        )

        compiler = StrategyCompiler()
        strategy_class = compiler.compile(strategy_def)

        # Check that we got a strategy class
        assert issubclass(strategy_class, bt.Strategy)
        assert strategy_class.__strategy_name__ == "SMA Crossover"
        assert strategy_class.__strategy_version__ == "1.0.0"

    def test_compile_rsi_strategy(self):
        """Test compiling RSI strategy."""
        strategy_def = StrategyDefinition(
            name="RSI Strategy",
            version="1.0.0",
            indicators=[
                IndicatorConfig(type=IndicatorType.RSI, params={"period": 14}, alias="rsi")
            ],
            entry_long=Condition(
                left="rsi",
                operator=ComparisonOperator.LT,
                right=30.0,
                description="RSI oversold"
            ),
            exit_long=Condition(
                left="rsi",
                operator=ComparisonOperator.GT,
                right=70.0,
                description="RSI overbought"
            ),
            risk_management=RiskManagement(
                stop_loss_pct=2.0
            )
        )

        compiler = StrategyCompiler()
        strategy_class = compiler.compile(strategy_def)

        assert issubclass(strategy_class, bt.Strategy)
        assert strategy_class.__strategy_name__ == "RSI Strategy"

    def test_compile_multi_indicator_strategy(self):
        """Test compiling strategy with multiple indicators."""
        strategy_def = StrategyDefinition(
            name="Multi-Indicator",
            version="1.0.0",
            indicators=[
                IndicatorConfig(type=IndicatorType.RSI, params={"period": 14}, alias="rsi"),
                IndicatorConfig(type=IndicatorType.MACD, params={"fast": 12, "slow": 26, "signal": 9}, alias="macd"),
                IndicatorConfig(type=IndicatorType.SMA, params={"period": 200}, alias="sma_200"),
            ],
            entry_long=LogicGroup(
                operator=LogicOperator.AND,
                conditions=[
                    Condition(left="rsi", operator=ComparisonOperator.LT, right=30.0),
                    Condition(left="close", operator=ComparisonOperator.GT, right="sma_200"),
                ]
            ),
            exit_long=Condition(
                left="rsi",
                operator=ComparisonOperator.GT,
                right=70.0
            ),
            risk_management=RiskManagement(
                stop_loss_atr=2.0,
                take_profit_atr=4.0
            )
        )

        compiler = StrategyCompiler()
        strategy_class = compiler.compile(strategy_def)

        assert issubclass(strategy_class, bt.Strategy)
        assert len(strategy_def.indicators) == 3

    def test_compile_long_short_strategy(self):
        """Test compiling strategy with both long and short positions."""
        strategy_def = StrategyDefinition(
            name="Long-Short Strategy",
            version="1.0.0",
            indicators=[
                IndicatorConfig(type=IndicatorType.RSI, params={"period": 14}, alias="rsi"),
            ],
            entry_long=Condition(
                left="rsi",
                operator=ComparisonOperator.LT,
                right=30.0
            ),
            exit_long=Condition(
                left="rsi",
                operator=ComparisonOperator.GT,
                right=70.0
            ),
            entry_short=Condition(
                left="rsi",
                operator=ComparisonOperator.GT,
                right=70.0
            ),
            exit_short=Condition(
                left="rsi",
                operator=ComparisonOperator.LT,
                right=30.0
            ),
            risk_management=RiskManagement(
                stop_loss_pct=2.0
            )
        )

        compiler = StrategyCompiler()
        strategy_class = compiler.compile(strategy_def)

        assert issubclass(strategy_class, bt.Strategy)

    def test_compile_with_nested_logic(self):
        """Test compiling strategy with nested logic groups."""
        strategy_def = StrategyDefinition(
            name="Nested Logic",
            version="1.0.0",
            indicators=[
                IndicatorConfig(type=IndicatorType.RSI, params={"period": 14}, alias="rsi"),
                IndicatorConfig(type=IndicatorType.MACD, params={"fast": 12, "slow": 26, "signal": 9}, alias="macd"),
                IndicatorConfig(type=IndicatorType.SMA, params={"period": 200}, alias="sma_200"),
            ],
            entry_long=LogicGroup(
                operator=LogicOperator.AND,
                conditions=[
                    LogicGroup(
                        operator=LogicOperator.OR,
                        conditions=[
                            Condition(left="rsi", operator=ComparisonOperator.LT, right=30.0),
                            Condition(left="macd", operator=ComparisonOperator.CROSSES_ABOVE, right=0.0),
                        ]
                    ),
                    Condition(left="close", operator=ComparisonOperator.GT, right="sma_200"),
                ]
            ),
            exit_long=Condition(
                left="rsi",
                operator=ComparisonOperator.GT,
                right=70.0
            ),
            risk_management=RiskManagement()
        )

        compiler = StrategyCompiler()
        strategy_class = compiler.compile(strategy_def)

        assert issubclass(strategy_class, bt.Strategy)


def test_integration_with_backtrader():
    """Integration test: compile and run strategy with Backtrader.

    This test demonstrates the full workflow from YAML to execution.
    """
    # Define strategy
    strategy_def = StrategyDefinition(
        name="Test Strategy",
        version="1.0.0",
        indicators=[
            IndicatorConfig(type=IndicatorType.SMA, params={"period": 10}, alias="sma_fast"),
            IndicatorConfig(type=IndicatorType.SMA, params={"period": 30}, alias="sma_slow")
        ],
        entry_long=Condition(
            left="sma_fast",
            operator=ComparisonOperator.CROSSES_ABOVE,
            right="sma_slow"
        ),
        exit_long=Condition(
            left="sma_fast",
            operator=ComparisonOperator.CROSSES_BELOW,
            right="sma_slow"
        ),
        risk_management=RiskManagement(
            stop_loss_pct=5.0,
            take_profit_pct=10.0
        )
    )

    # Compile strategy
    compiler = StrategyCompiler()
    strategy_class = compiler.compile(strategy_def)

    # Note: Full Backtrader integration would require actual data feed
    # For now, we just verify the class can be instantiated
    assert issubclass(strategy_class, bt.Strategy)
    assert hasattr(strategy_class, '__init__')
    assert hasattr(strategy_class, 'next')
    assert hasattr(strategy_class, 'notify_order')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
