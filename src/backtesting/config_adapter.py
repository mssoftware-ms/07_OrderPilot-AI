"""Config Adapter for BacktestEngine.

Bridges the gap between the main TradingBotConfig (config/models.py)
and BacktestEngine's schema_types.py models for seamless integration.

This allows BacktestEngine to accept either:
1. Direct schema_types.TradingBotConfig (legacy)
2. Main config/models.py TradingBotConfig (new standard)
3. JSON file path (auto-loads with ConfigLoader)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Union

logger = logging.getLogger(__name__)


class BacktestConfigAdapter:
    """Adapter to convert between config formats."""

    @staticmethod
    def from_file(config_path: str | Path):
        """Load config from JSON file using main ConfigLoader.

        Args:
            config_path: Path to JSON config file

        Returns:
            schema_types.TradingBotConfig instance for BacktestEngine
        """
        try:
            from src.core.tradingbot.config.loader import ConfigLoader

            # Load with main ConfigLoader (validates against JSON schema + Pydantic)
            config_loader = ConfigLoader()
            main_config = config_loader.load_config(config_path)

            # Convert to BacktestEngine format
            return BacktestConfigAdapter.from_main_config(main_config)

        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise

    @staticmethod
    def from_main_config(main_config):
        """Convert main TradingBotConfig to BacktestEngine format.

        Args:
            main_config: config.models.TradingBotConfig instance

        Returns:
            schema_types.TradingBotConfig instance
        """
        from src.backtesting.schema_types import (
            TradingBotConfig,
            IndicatorDef,
            RegimeDef,
            StrategyDef,
            StrategySet,
            RoutingRule,
            ConditionGroup,
            RiskSettings,
            Condition,
            ConditionLeftRight,
            RoutingMatch,
            StrategyRef,
            IndicatorOverride,
            StrategyOverride,
            Metadata,
        )

        # Convert indicators
        indicators = [
            IndicatorDef(
                id=ind.id,
                type=ind.type.value if hasattr(ind.type, 'value') else ind.type,
                params=ind.params or {},
                timeframe=ind.timeframe
            )
            for ind in main_config.indicators
        ]

        # Convert regimes
        regimes = [
            RegimeDef(
                id=reg.id,
                name=reg.name,
                conditions=BacktestConfigAdapter._convert_condition_group(reg.conditions),
                priority=reg.priority,
                scope=reg.scope.value if reg.scope and hasattr(reg.scope, 'value') else reg.scope
            )
            for reg in main_config.regimes
        ]

        # Convert strategies
        strategies = [
            StrategyDef(
                id=strat.id,
                name=strat.name,
                entry=BacktestConfigAdapter._convert_condition_group(strat.entry) if strat.entry else None,
                exit=BacktestConfigAdapter._convert_condition_group(strat.exit) if strat.exit else None,
                risk=BacktestConfigAdapter._convert_risk_settings(strat.risk) if strat.risk else None
            )
            for strat in main_config.strategies
        ]

        # Convert strategy sets
        strategy_sets = [
            StrategySet(
                id=ss.id,
                name=ss.name,
                strategies=[
                    StrategyRef(
                        strategy_id=ref.strategy_id,
                        strategy_overrides=BacktestConfigAdapter._convert_strategy_override(
                            ref.strategy_overrides
                        ) if ref.strategy_overrides else None
                    )
                    for ref in ss.strategies
                ],
                indicator_overrides=[
                    IndicatorOverride(
                        indicator_id=override.indicator_id,
                        params=override.params
                    )
                    for override in (ss.indicator_overrides or [])
                ]
            )
            for ss in main_config.strategy_sets
        ]

        # Convert routing rules
        routing = [
            RoutingRule(
                strategy_set_id=rule.strategy_set_id,
                match=RoutingMatch(
                    all_of=rule.match.all_of if rule.match else None,
                    any_of=rule.match.any_of if rule.match else None,
                    none_of=rule.match.none_of if rule.match else None
                )
            )
            for rule in main_config.routing
        ]

        # Convert metadata
        metadata = None
        if main_config.metadata:
            metadata = Metadata(
                author=main_config.metadata.author,
                created_at=main_config.metadata.created_at,
                tags=main_config.metadata.tags or [],
                notes=main_config.metadata.notes,
                dataset_id=main_config.metadata.dataset_id
            )

        # Build BacktestEngine config
        return TradingBotConfig(
            schema_version=main_config.schema_version,
            metadata=metadata,
            indicators=indicators,
            regimes=regimes,
            strategies=strategies,
            strategy_sets=strategy_sets,
            routing=routing
        )

    @staticmethod
    def _convert_condition_group(cond_group) -> dict[str, Any]:
        """Convert ConditionGroup to BacktestEngine format.

        Args:
            cond_group: config.models.ConditionGroup

        Returns:
            schema_types.ConditionGroup dict
        """
        if cond_group is None:
            return None

        from src.backtesting.schema_types import ConditionGroup, Condition, ConditionLeftRight

        result = {}

        if hasattr(cond_group, 'all') and cond_group.all:
            result['all'] = [
                Condition(
                    left=ConditionLeftRight(
                        indicator_id=c.left.indicator_id if c.left else None,
                        field=c.left.field if c.left else None,
                        value=c.left.value if c.left else None,
                        min=c.left.min if (c.left and hasattr(c.left, 'min')) else None,
                        max=c.left.max if (c.left and hasattr(c.left, 'max')) else None
                    ),
                    op=c.op.value if hasattr(c.op, 'value') else c.op,
                    right=ConditionLeftRight(
                        indicator_id=c.right.indicator_id if c.right else None,
                        field=c.right.field if c.right else None,
                        value=c.right.value if c.right else None,
                        min=c.right.min if (c.right and hasattr(c.right, 'min')) else None,
                        max=c.right.max if (c.right and hasattr(c.right, 'max')) else None
                    )
                )
                for c in cond_group.all
            ]

        if hasattr(cond_group, 'any') and cond_group.any:
            result['any'] = [
                Condition(
                    left=ConditionLeftRight(
                        indicator_id=c.left.indicator_id if c.left else None,
                        field=c.left.field if c.left else None,
                        value=c.left.value if c.left else None,
                        min=c.left.min if (c.left and hasattr(c.left, 'min')) else None,
                        max=c.left.max if (c.left and hasattr(c.left, 'max')) else None
                    ),
                    op=c.op.value if hasattr(c.op, 'value') else c.op,
                    right=ConditionLeftRight(
                        indicator_id=c.right.indicator_id if c.right else None,
                        field=c.right.field if c.right else None,
                        value=c.right.value if c.right else None,
                        min=c.right.min if (c.right and hasattr(c.right, 'min')) else None,
                        max=c.right.max if (c.right and hasattr(c.right, 'max')) else None
                    )
                )
                for c in cond_group.any
            ]

        return ConditionGroup(**result) if result else ConditionGroup()

    @staticmethod
    def _convert_risk_settings(risk) -> dict[str, Any]:
        """Convert RiskSettings to BacktestEngine format."""
        if risk is None:
            return None

        from src.backtesting.schema_types import RiskSettings

        return RiskSettings(
            stop_loss_pct=risk.stop_loss if hasattr(risk, 'stop_loss') else None,
            take_profit_pct=risk.take_profit if hasattr(risk, 'take_profit') else None,
            trailing_mode=risk.trailing_mode.value if (
                hasattr(risk, 'trailing_mode') and
                risk.trailing_mode and
                hasattr(risk.trailing_mode, 'value')
            ) else None,
            trailing_multiplier=risk.trailing_multiplier if hasattr(risk, 'trailing_multiplier') else None,
            risk_per_trade_pct=risk.position_size if hasattr(risk, 'position_size') else None
        )

    @staticmethod
    def _convert_strategy_override(override) -> dict[str, Any]:
        """Convert StrategyOverride to BacktestEngine format."""
        if override is None:
            return None

        from src.backtesting.schema_types import StrategyOverride

        return StrategyOverride(
            entry=BacktestConfigAdapter._convert_condition_group(override.entry) if hasattr(override, 'entry') else None,
            exit=BacktestConfigAdapter._convert_condition_group(override.exit) if hasattr(override, 'exit') else None,
            risk=BacktestConfigAdapter._convert_risk_settings(override.risk) if hasattr(override, 'risk') else None
        )


# ==================== Convenience Functions ====================


def load_config_for_backtest(config_path: str | Path):
    """Load JSON config for backtesting.

    Convenience function that loads config with main ConfigLoader
    and converts to BacktestEngine format.

    Args:
        config_path: Path to JSON strategy config

    Returns:
        schema_types.TradingBotConfig ready for BacktestEngine

    Example:
        >>> config = load_config_for_backtest("configs/strategy.json")
        >>> engine = BacktestEngine()
        >>> results = engine.run(config, "BTCUSDT", ...)
    """
    return BacktestConfigAdapter.from_file(config_path)
