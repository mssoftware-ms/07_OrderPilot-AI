"""
CEL Context Builder - Merges all variable sources for CEL expressions.

This module provides a unified context builder that merges variables from
multiple sources into a single dictionary for CEL expression evaluation.

Data Sources:
    1. Project Variables - from .cel_variables.json (project.*)
    2. Chart Data - from ChartWindow (chart.*)
    3. Bot Configuration - from BotConfig (bot.*)
    4. Indicators - from IndicatorManager (indicators.*)
    5. Regime - from RegimeDetector (regime.*)

Architecture:
    CELContextBuilder is the single entry point for building CEL contexts.
    It coordinates all providers and handles errors gracefully.

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from .bot_config_provider import BotConfigProvider
from .chart_data_provider import ChartDataProvider
from .variable_storage import VariableStorage

if TYPE_CHECKING:
    from src.core.trading_bot.bot_config import BotConfig
    from src.ui.widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)


class CELContextBuilder:
    """
    Unified context builder for CEL expressions.

    This class coordinates all data providers to build a complete CEL
    evaluation context with variables from multiple sources.

    Attributes:
        storage: VariableStorage for project variables
        chart_provider: ChartDataProvider for chart data
        bot_provider: BotConfigProvider for bot configuration
        enable_cache: Whether to cache contexts (default: True)

    Examples:
        >>> builder = CELContextBuilder()
        >>> context = builder.build(
        ...     chart_window=chart_window,
        ...     bot_config=bot_config,
        ...     project_vars_path="project/.cel_variables.json"
        ... )
        >>> print(len(context))
        65  # All variables from all sources

    Usage with CEL Engine:
        >>> from src.core.tradingbot.cel_engine import CELEngine
        >>>
        >>> cel = CELEngine()
        >>> builder = CELContextBuilder()
        >>>
        >>> context = builder.build(chart, bot, "project/.cel_variables.json")
        >>> result = cel.evaluate("chart.price > project.entry_min_price", context)
    """

    def __init__(
        self,
        storage: Optional[VariableStorage] = None,
        chart_provider: Optional[ChartDataProvider] = None,
        bot_provider: Optional[BotConfigProvider] = None,
        enable_cache: bool = True,
    ):
        """
        Initialize CEL context builder.

        Args:
            storage: VariableStorage instance (creates new if None)
            chart_provider: ChartDataProvider (creates new if None)
            bot_provider: BotConfigProvider (creates new if None)
            enable_cache: Enable LRU caching of contexts
        """
        self.storage = storage or VariableStorage()
        self.chart_provider = chart_provider or ChartDataProvider()
        self.bot_provider = bot_provider or BotConfigProvider()
        self.enable_cache = enable_cache

        # Statistics
        self._build_count = 0
        self._cache_hits = 0
        self._cache_misses = 0

    def build(
        self,
        chart_window: Optional[ChartWindow] = None,
        bot_config: Optional[BotConfig] = None,
        project_vars_path: Optional[str | Path] = None,
        indicators: Optional[Dict[str, Any]] = None,
        regime: Optional[Dict[str, Any]] = None,
        include_empty_namespaces: bool = True,
    ) -> Dict[str, Any]:
        """
        Build complete CEL context from all sources.

        Args:
            chart_window: ChartWindow instance (optional)
            bot_config: BotConfig instance (optional)
            project_vars_path: Path to .cel_variables.json (optional)
            indicators: Indicator values dict (optional, future use)
            regime: Regime detection values dict (optional, future use)
            include_empty_namespaces: Include None values when source unavailable

        Returns:
            Dictionary with all variables for CEL evaluation

        Examples:
            >>> # Minimal - only project variables
            >>> context = builder.build(
            ...     project_vars_path="project/.cel_variables.json"
            ... )
            >>>
            >>> # Full - all sources
            >>> context = builder.build(
            ...     chart_window=chart_window,
            ...     bot_config=bot_config,
            ...     project_vars_path="project/.cel_variables.json",
            ...     indicators={"sma_50": 94500.0},
            ...     regime={"current": "bullish"}
            ... )
        """
        self._build_count += 1
        context = {}

        try:
            # 1. Project Variables (highest priority - user defined)
            if project_vars_path:
                try:
                    project_vars = self.storage.load(
                        project_vars_path,
                        use_cache=self.enable_cache,
                        create_if_missing=False
                    )
                    project_context = project_vars.to_cel_context()
                    context.update(project_context)

                    logger.debug(
                        f"Loaded {len(project_context)} project variables "
                        f"from {project_vars_path}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not load project variables from {project_vars_path}: {e}"
                    )

            # 2. Chart Data
            if chart_window:
                try:
                    chart_context = self.chart_provider.get_context(chart_window)
                    context.update(chart_context)

                    logger.debug(
                        f"Added {len(chart_context)} chart variables "
                        f"for {chart_window.symbol}"
                    )
                except Exception as e:
                    logger.warning(f"Could not get chart context: {e}")
                    if include_empty_namespaces:
                        context.update(self.chart_provider._get_empty_context())

            elif include_empty_namespaces:
                context.update(self.chart_provider._get_empty_context())

            # 3. Bot Configuration
            if bot_config:
                try:
                    bot_context = self.bot_provider.get_context(bot_config)
                    context.update(bot_context)

                    logger.debug(
                        f"Added {len(bot_context)} bot config variables "
                        f"for {bot_config.symbol}"
                    )
                except Exception as e:
                    logger.warning(f"Could not get bot config context: {e}")
                    if include_empty_namespaces:
                        context.update(self.bot_provider._get_empty_context())

            elif include_empty_namespaces:
                context.update(self.bot_provider._get_empty_context())

            # 4. Indicators (placeholder for future implementation)
            if indicators:
                try:
                    indicators_context = self._build_indicators_context(indicators)
                    context.update(indicators_context)

                    logger.debug(
                        f"Added {len(indicators_context)} indicator variables"
                    )
                except Exception as e:
                    logger.warning(f"Could not get indicators context: {e}")

            # 5. Regime (placeholder for future implementation)
            if regime:
                try:
                    regime_context = self._build_regime_context(regime)
                    context.update(regime_context)

                    logger.debug(
                        f"Added {len(regime_context)} regime variables"
                    )
                except Exception as e:
                    logger.warning(f"Could not get regime context: {e}")

            logger.info(
                f"Built CEL context with {len(context)} total variables "
                f"(build #{self._build_count})"
            )

            return context

        except Exception as e:
            logger.error(f"Error building CEL context: {e}", exc_info=True)
            return {}

    def _build_indicators_context(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build indicators.* namespace from indicator values.

        Args:
            indicators: Dictionary of indicator_name -> value

        Returns:
            Dictionary with indicators.* prefixed keys

        Examples:
            >>> indicators = {"sma_50": 94500.0, "rsi": 65.0}
            >>> context = builder._build_indicators_context(indicators)
            >>> print(context)
            {'indicators.sma_50': 94500.0, 'indicators.rsi': 65.0}
        """
        return {f"indicators.{key}": value for key, value in indicators.items()}

    def _build_regime_context(self, regime: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build regime.* namespace from regime detection values.

        Args:
            regime: Dictionary of regime attributes

        Returns:
            Dictionary with regime.* prefixed keys

        Examples:
            >>> regime = {"current": "bullish", "strength": 0.8}
            >>> context = builder._build_regime_context(regime)
            >>> print(context)
            {'regime.current': 'bullish', 'regime.strength': 0.8}
        """
        return {f"regime.{key}": value for key, value in regime.items()}

    def get_available_variables(
        self,
        chart_window: Optional[ChartWindow] = None,
        bot_config: Optional[BotConfig] = None,
        project_vars_path: Optional[str | Path] = None,
    ) -> Dict[str, Dict[str, str]]:
        """
        Get metadata for all available variables.

        Returns a dictionary of variable_name -> metadata with
        description, type, unit, category, and current value.

        Args:
            chart_window: ChartWindow (to get current chart values)
            bot_config: BotConfig (to get current bot values)
            project_vars_path: Path to project variables

        Returns:
            Dictionary of variable_name -> {description, type, unit, category, value}

        Examples:
            >>> variables = builder.get_available_variables(
            ...     chart_window=chart,
            ...     bot_config=bot,
            ...     project_vars_path="project/.cel_variables.json"
            ... )
            >>> print(variables['chart.price'])
            {
                'description': 'Current close price',
                'type': 'float',
                'unit': 'USD',
                'category': 'Chart',
                'value': 95234.50
            }
        """
        variables = {}

        # Get current context for values (build with actual data sources)
        context = self.build(
            chart_window=chart_window,
            bot_config=bot_config,
            project_vars_path=project_vars_path,
            include_empty_namespaces=False  # Don't include None values
        )

        logger.debug(f"Built context with {len(context)} variables for get_available_variables")

        # Chart variables - get live values from context
        chart_info = self.chart_provider.get_variable_info()
        for var_name, meta in chart_info.items():
            value = context.get(var_name)
            variables[var_name] = {
                **meta,
                "category": "Chart",
                "value": value,
                "label": meta.get("description", var_name),  # Add label for UI
            }
            if value is not None:
                logger.debug(f"Chart variable {var_name} = {value}")

        # Bot variables - get live values from context
        bot_info = self.bot_provider.get_variable_info()
        for var_name, meta in bot_info.items():
            value = context.get(var_name)
            variables[var_name] = {
                **meta,
                "category": "Bot",
                "value": value,
                "label": meta.get("description", var_name),  # Add label for UI
            }
            if value is not None:
                logger.debug(f"Bot variable {var_name} = {value}")

        # Project variables - get values from storage
        if project_vars_path:
            try:
                project_vars = self.storage.load(
                    project_vars_path,
                    create_if_missing=False
                )
                for var_name, var in project_vars.variables.items():
                    variables[var_name] = {
                        "description": var.description,
                        "type": var.type.value,
                        "unit": var.unit,
                        "category": var.category,
                        "value": var.value,  # Use value from ProjectVariable
                        "label": var.description,  # Add label for UI
                    }
                logger.debug(f"Loaded {len(project_vars.variables)} project variables")
            except Exception as e:
                logger.warning(f"Could not load project variables: {e}")

        logger.info(f"get_available_variables returning {len(variables)} total variables")
        return variables

    def get_statistics(self) -> Dict[str, int]:
        """
        Get builder statistics.

        Returns:
            Dictionary with build_count, cache_hits, cache_misses

        Examples:
            >>> stats = builder.get_statistics()
            >>> print(stats)
            {'build_count': 42, 'cache_hits': 28, 'cache_misses': 14}
        """
        return {
            "build_count": self._build_count,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "cache_info": self.storage.get_cache_info(),
        }

    def clear_cache(self) -> None:
        """Clear all caches."""
        self.storage.clear_cache()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Cleared all CEL context caches")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CELContextBuilder(builds={self._build_count}, "
            f"cache={self.enable_cache})"
        )
