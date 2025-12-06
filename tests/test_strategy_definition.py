"""Unit tests for Strategy Definition models.

Tests the Pydantic models for declarative strategy definition.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

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


class TestIndicatorConfig:
    """Test suite for IndicatorConfig model."""

    def test_basic_indicator_config(self):
        """Test basic indicator configuration."""
        ind = IndicatorConfig(
            type=IndicatorType.SMA,
            params={"period": 20},
            alias="sma_20"
        )

        assert ind.type == "SMA"
        assert ind.params == {"period": 20}
        assert ind.alias == "sma_20"
        assert ind.source == "close"
        assert ind.plot is True

    def test_indicator_with_custom_source(self):
        """Test indicator with custom data source."""
        ind = IndicatorConfig(
            type=IndicatorType.EMA,
            params={"period": 50},
            alias="ema_50_high",
            source="high"
        )

        assert ind.source == "high"

    def test_invalid_alias_with_spaces(self):
        """Test that alias with spaces is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            IndicatorConfig(
                type=IndicatorType.RSI,
                params={"period": 14},
                alias="my rsi"
            )

        assert "alphanumeric" in str(exc_info.value).lower()

    def test_invalid_alias_with_special_chars(self):
        """Test that alias with special characters is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            IndicatorConfig(
                type=IndicatorType.MACD,
                params={},
                alias="macd@signal"
            )

        assert "alphanumeric" in str(exc_info.value).lower()

    def test_valid_alias_with_underscore(self):
        """Test that alias with underscores is valid."""
        ind = IndicatorConfig(
            type=IndicatorType.ATR,
            params={"period": 14},
            alias="atr_14_period"
        )

        assert ind.alias == "atr_14_period"


class TestCondition:
    """Test suite for Condition model."""

    def test_simple_comparison(self):
        """Test simple comparison condition."""
        cond = Condition(
            left="rsi",
            operator=ComparisonOperator.LT,
            right=30.0,
            description="RSI below 30 (oversold)"
        )

        assert cond.left == "rsi"
        assert cond.operator == "<"
        assert cond.right == 30.0
        assert "oversold" in cond.description

    def test_indicator_comparison(self):
        """Test comparison between two indicators."""
        cond = Condition(
            left="sma_fast",
            operator=ComparisonOperator.GT,
            right="sma_slow"
        )

        assert cond.left == "sma_fast"
        assert cond.operator == ">"
        assert cond.right == "sma_slow"

    def test_crosses_above_operator(self):
        """Test crosses_above special operator."""
        cond = Condition(
            left="ema_20",
            operator=ComparisonOperator.CROSSES_ABOVE,
            right="ema_50"
        )

        assert cond.operator == "crosses_above"

    def test_inside_range_operator(self):
        """Test inside range operator."""
        cond = Condition(
            left="rsi",
            operator=ComparisonOperator.INSIDE,
            right=[40.0, 60.0]
        )

        assert cond.operator == "inside"
        assert cond.right == [40.0, 60.0]

    def test_invalid_inside_operator_single_value(self):
        """Test that inside operator requires list of 2 values."""
        with pytest.raises(ValidationError) as exc_info:
            Condition(
                left="rsi",
                operator=ComparisonOperator.INSIDE,
                right=50.0
            )

        assert "list of 2 floats" in str(exc_info.value)

    def test_invalid_inside_operator_wrong_length(self):
        """Test that inside operator requires exactly 2 values."""
        with pytest.raises(ValidationError) as exc_info:
            Condition(
                left="rsi",
                operator=ComparisonOperator.INSIDE,
                right=[40.0, 50.0, 60.0]
            )

        assert "list of 2 floats" in str(exc_info.value)


class TestLogicGroup:
    """Test suite for LogicGroup model."""

    def test_and_logic_group(self):
        """Test AND logic group."""
        group = LogicGroup(
            operator=LogicOperator.AND,
            conditions=[
                Condition(left="rsi", operator=ComparisonOperator.LT, right=30),
                Condition(left="macd", operator=ComparisonOperator.GT, right=0)
            ],
            description="RSI oversold AND MACD positive"
        )

        assert group.operator == "AND"
        assert len(group.conditions) == 2
        assert isinstance(group.conditions[0], Condition)

    def test_or_logic_group(self):
        """Test OR logic group."""
        group = LogicGroup(
            operator=LogicOperator.OR,
            conditions=[
                Condition(left="rsi", operator=ComparisonOperator.GT, right=70),
                Condition(left="rsi", operator=ComparisonOperator.LT, right=30)
            ]
        )

        assert group.operator == "OR"

    def test_nested_logic_groups(self):
        """Test nested logic groups (recursive)."""
        group = LogicGroup(
            operator=LogicOperator.AND,
            conditions=[
                # First sub-group (OR)
                LogicGroup(
                    operator=LogicOperator.OR,
                    conditions=[
                        Condition(left="rsi", operator=ComparisonOperator.LT, right=30),
                        Condition(left="cci", operator=ComparisonOperator.LT, right=-100)
                    ]
                ),
                # Second condition
                Condition(left="sma_fast", operator=ComparisonOperator.GT, right="sma_slow")
            ],
            description="(RSI or CCI oversold) AND bullish SMA crossover"
        )

        assert group.operator == "AND"
        assert len(group.conditions) == 2
        assert isinstance(group.conditions[0], LogicGroup)
        assert isinstance(group.conditions[1], Condition)

    def test_empty_conditions_rejected(self):
        """Test that empty conditions list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LogicGroup(
                operator=LogicOperator.AND,
                conditions=[]
            )

        assert "at least one condition" in str(exc_info.value).lower()

    def test_not_operator_single_condition(self):
        """Test NOT operator with single condition."""
        group = LogicGroup(
            operator=LogicOperator.NOT,
            conditions=[
                Condition(left="rsi", operator=ComparisonOperator.GT, right=70)
            ]
        )

        assert group.operator == "NOT"
        assert len(group.conditions) == 1

    def test_not_operator_multiple_conditions_rejected(self):
        """Test that NOT operator with multiple conditions is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LogicGroup(
                operator=LogicOperator.NOT,
                conditions=[
                    Condition(left="rsi", operator=ComparisonOperator.GT, right=70),
                    Condition(left="macd", operator=ComparisonOperator.LT, right=0)
                ]
            )

        assert "exactly one condition" in str(exc_info.value).lower()


class TestRiskManagement:
    """Test suite for RiskManagement model."""

    def test_basic_risk_management(self):
        """Test basic risk management configuration."""
        rm = RiskManagement(
            stop_loss_pct=2.0,
            take_profit_pct=5.0,
            max_risk_per_trade_pct=1.0
        )

        assert rm.stop_loss_pct == 2.0
        assert rm.take_profit_pct == 5.0
        assert rm.max_risk_per_trade_pct == 1.0

    def test_atr_based_risk_management(self):
        """Test ATR-based risk management."""
        rm = RiskManagement(
            stop_loss_atr=2.0,
            take_profit_atr=4.0
        )

        assert rm.stop_loss_atr == 2.0
        assert rm.take_profit_atr == 4.0

    def test_trailing_stop(self):
        """Test trailing stop configuration."""
        rm = RiskManagement(
            trailing_stop_pct=3.0
        )

        assert rm.trailing_stop_pct == 3.0

    def test_multiple_stop_loss_methods_rejected(self):
        """Test that multiple stop loss methods are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RiskManagement(
                stop_loss_pct=2.0,
                stop_loss_atr=1.5
            )

        assert "only one stop loss method" in str(exc_info.value).lower()

    def test_multiple_take_profit_methods_rejected(self):
        """Test that multiple take profit methods are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RiskManagement(
                take_profit_pct=5.0,
                take_profit_atr=3.0
            )

        assert "only one take profit method" in str(exc_info.value).lower()

    def test_invalid_stop_loss_pct(self):
        """Test that invalid stop loss percentage is rejected."""
        with pytest.raises(ValidationError):
            RiskManagement(stop_loss_pct=0.0)

        with pytest.raises(ValidationError):
            RiskManagement(stop_loss_pct=-1.0)

        with pytest.raises(ValidationError):
            RiskManagement(stop_loss_pct=150.0)


class TestStrategyDefinition:
    """Test suite for StrategyDefinition model."""

    def test_simple_sma_crossover_strategy(self):
        """Test simple SMA crossover strategy."""
        strategy = StrategyDefinition(
            name="SMA Crossover",
            version="1.0.0",
            description="Simple SMA 20/50 crossover strategy",
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

        assert strategy.name == "SMA Crossover"
        assert strategy.version == "1.0.0"
        assert len(strategy.indicators) == 2
        assert strategy.entry_short is None
        assert strategy.exit_short is None

    def test_rsi_oversold_strategy_with_logic_group(self):
        """Test RSI oversold strategy with logic group."""
        strategy = StrategyDefinition(
            name="RSI Oversold",
            version="2.1.0",
            indicators=[
                IndicatorConfig(type=IndicatorType.RSI, params={"period": 14}, alias="rsi"),
                IndicatorConfig(type=IndicatorType.SMA, params={"period": 200}, alias="sma_200")
            ],
            entry_long=LogicGroup(
                operator=LogicOperator.AND,
                conditions=[
                    Condition(left="rsi", operator=ComparisonOperator.LT, right=30),
                    Condition(left="close", operator=ComparisonOperator.GT, right="sma_200")
                ],
                description="RSI oversold AND price above 200 SMA"
            ),
            exit_long=Condition(left="rsi", operator=ComparisonOperator.GT, right=70)
        )

        assert strategy.name == "RSI Oversold"
        assert isinstance(strategy.entry_long, LogicGroup)
        assert isinstance(strategy.exit_long, Condition)

    def test_long_short_strategy(self):
        """Test strategy with both long and short entries."""
        strategy = StrategyDefinition(
            name="MACD Long/Short",
            version="1.0.0",
            indicators=[
                IndicatorConfig(type=IndicatorType.MACD, params={}, alias="macd")
            ],
            entry_long=Condition(
                left="macd",
                operator=ComparisonOperator.CROSSES_ABOVE,
                right=0.0
            ),
            exit_long=Condition(
                left="macd",
                operator=ComparisonOperator.CROSSES_BELOW,
                right=0.0
            ),
            entry_short=Condition(
                left="macd",
                operator=ComparisonOperator.CROSSES_BELOW,
                right=0.0
            ),
            exit_short=Condition(
                left="macd",
                operator=ComparisonOperator.CROSSES_ABOVE,
                right=0.0
            )
        )

        assert strategy.entry_short is not None
        assert strategy.exit_short is not None

    def test_duplicate_indicator_aliases_rejected(self):
        """Test that duplicate indicator aliases are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StrategyDefinition(
                name="Duplicate Test",
                version="1.0.0",
                indicators=[
                    IndicatorConfig(type=IndicatorType.SMA, params={"period": 20}, alias="sma"),
                    IndicatorConfig(type=IndicatorType.EMA, params={"period": 20}, alias="sma")
                ],
                entry_long=Condition(left="sma", operator=ComparisonOperator.GT, right=100),
                exit_long=Condition(left="sma", operator=ComparisonOperator.LT, right=100)
            )

        assert "duplicate" in str(exc_info.value).lower()

    def test_invalid_indicator_reference_rejected(self):
        """Test that invalid indicator reference in condition is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            StrategyDefinition(
                name="Invalid Ref Test",
                version="1.0.0",
                indicators=[
                    IndicatorConfig(type=IndicatorType.SMA, params={"period": 20}, alias="sma_20")
                ],
                entry_long=Condition(
                    left="rsi_14",  # Not defined
                    operator=ComparisonOperator.LT,
                    right=30
                ),
                exit_long=Condition(left="sma_20", operator=ComparisonOperator.LT, right=100)
            )

        assert "invalid indicator references" in str(exc_info.value).lower()

    def test_built_in_references_valid(self):
        """Test that built-in references (close, open, etc.) are valid."""
        strategy = StrategyDefinition(
            name="Price Breakout",
            version="1.0.0",
            indicators=[
                IndicatorConfig(type=IndicatorType.SMA, params={"period": 50}, alias="sma_50")
            ],
            entry_long=Condition(
                left="close",
                operator=ComparisonOperator.CROSSES_ABOVE,
                right="sma_50"
            ),
            exit_long=Condition(
                left="close",
                operator=ComparisonOperator.CROSSES_BELOW,
                right="sma_50"
            )
        )

        assert strategy.name == "Price Breakout"

    def test_get_indicator_by_alias(self):
        """Test getting indicator by alias."""
        strategy = StrategyDefinition(
            name="Test",
            version="1.0.0",
            indicators=[
                IndicatorConfig(type=IndicatorType.SMA, params={"period": 20}, alias="sma_20"),
                IndicatorConfig(type=IndicatorType.RSI, params={"period": 14}, alias="rsi_14")
            ],
            entry_long=Condition(left="sma_20", operator=ComparisonOperator.GT, right=100),
            exit_long=Condition(left="sma_20", operator=ComparisonOperator.LT, right=100)
        )

        sma = strategy.get_indicator_by_alias("sma_20")
        assert sma is not None
        assert sma.type == "SMA"
        assert sma.params["period"] == 20

        rsi = strategy.get_indicator_by_alias("rsi_14")
        assert rsi is not None
        assert rsi.type == "RSI"

        none_ind = strategy.get_indicator_by_alias("nonexistent")
        assert none_ind is None

    def test_invalid_version_format(self):
        """Test that invalid version format is rejected."""
        with pytest.raises(ValidationError):
            StrategyDefinition(
                name="Test",
                version="1.0",  # Invalid format
                indicators=[],
                entry_long=Condition(left="close", operator=ComparisonOperator.GT, right=100),
                exit_long=Condition(left="close", operator=ComparisonOperator.LT, right=100)
            )

    def test_json_serialization(self):
        """Test JSON serialization."""
        strategy = StrategyDefinition(
            name="Test Strategy",
            version="1.0.0",
            indicators=[
                IndicatorConfig(type=IndicatorType.SMA, params={"period": 20}, alias="sma_20")
            ],
            entry_long=Condition(
                left="close",
                operator=ComparisonOperator.CROSSES_ABOVE,
                right="sma_20"
            ),
            exit_long=Condition(
                left="close",
                operator=ComparisonOperator.CROSSES_BELOW,
                right="sma_20"
            )
        )

        # Serialize to JSON
        json_str = strategy.model_dump_json(indent=2)
        assert "Test Strategy" in json_str
        assert "1.0.0" in json_str

        # Deserialize from JSON
        strategy2 = StrategyDefinition.model_validate_json(json_str)
        assert strategy2.name == strategy.name
        assert strategy2.version == strategy.version
        assert len(strategy2.indicators) == len(strategy.indicators)

    def test_yaml_export_import(self):
        """Test YAML export and import."""
        strategy = StrategyDefinition(
            name="YAML Test",
            version="1.2.3",
            indicators=[
                IndicatorConfig(type=IndicatorType.RSI, params={"period": 14}, alias="rsi")
            ],
            entry_long=Condition(left="rsi", operator=ComparisonOperator.LT, right=30),
            exit_long=Condition(left="rsi", operator=ComparisonOperator.GT, right=70)
        )

        # Export to YAML
        yaml_str = strategy.to_yaml()
        assert "YAML Test" in yaml_str
        assert "1.2.3" in yaml_str

        # Import from YAML
        strategy2 = StrategyDefinition.from_yaml(yaml_str)
        assert strategy2.name == strategy.name
        assert strategy2.version == strategy.version

    def test_json_file_export_import(self, tmp_path):
        """Test JSON file export and import."""
        strategy = StrategyDefinition(
            name="File Test",
            version="3.2.1",
            indicators=[
                IndicatorConfig(type=IndicatorType.EMA, params={"period": 50}, alias="ema_50")
            ],
            entry_long=Condition(left="close", operator=ComparisonOperator.GT, right="ema_50"),
            exit_long=Condition(left="close", operator=ComparisonOperator.LT, right="ema_50")
        )

        # Export to JSON file
        json_file = tmp_path / "strategy.json"
        strategy.to_json_file(str(json_file))

        assert json_file.exists()

        # Import from JSON file
        strategy2 = StrategyDefinition.from_json_file(str(json_file))
        assert strategy2.name == strategy.name
        assert strategy2.version == strategy.version


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
