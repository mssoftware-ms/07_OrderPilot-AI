"""
Project Variables System for CEL Expressions.

This package provides project-specific variable management for use in
CEL (Common Expression Language) expressions throughout the application.

Key Components:
    - variable_models: Pydantic models for variables
    - variable_storage: Storage layer with LRU caching
    - chart_data_provider: Provider for chart.* namespace
    - bot_config_provider: Provider for bot.* namespace

Usage:
    >>> from src.core.variables import ProjectVariables, VariableStorage
    >>> from src.core.variables import ChartDataProvider, BotConfigProvider
    >>>
    >>> # Load project variables
    >>> storage = VariableStorage()
    >>> variables = storage.load(".cel_variables.json")
    >>>
    >>> # Get chart and bot data
    >>> chart_provider = ChartDataProvider()
    >>> bot_provider = BotConfigProvider()
    >>>
    >>> # Build CEL context
    >>> context = {}
    >>> context.update(variables.to_cel_context())
    >>> context.update(chart_provider.get_context(chart_window))
    >>> context.update(bot_provider.get_context(bot_config))

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from .variable_models import (
    ProjectVariable,
    ProjectVariables,
    VariableType,
)
from .variable_storage import (
    VariableStorage,
    VariableStorageError,
    VariableFileNotFoundError,
    VariableValidationError,
)
from .chart_data_provider import ChartDataProvider
from .bot_config_provider import BotConfigProvider
from .cel_context_builder import CELContextBuilder

__all__ = [
    # Models
    "ProjectVariable",
    "ProjectVariables",
    "VariableType",
    # Storage
    "VariableStorage",
    "VariableStorageError",
    "VariableFileNotFoundError",
    "VariableValidationError",
    # Providers
    "ChartDataProvider",
    "BotConfigProvider",
    # Context Builder
    "CELContextBuilder",
]

__version__ = "1.0.0"
