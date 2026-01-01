"""Strategy Parameter Definitions.

Defines configurable parameters for the base strategies.
Each parameter has a name, type, default value, range, and description.
"""

from typing import Any

from .strategy_params_base import (
    ParameterDefinition,
    StrategyName,
    StrategyParameterConfig,
)
from .strategy_params_registry import STRATEGY_PARAMETER_REGISTRY


def get_strategy_parameters(strategy: StrategyName | str) -> StrategyParameterConfig:
    """Get parameter configuration for a strategy.

    Args:
        strategy: Strategy name (enum or string)

    Returns:
        StrategyParameterConfig for the strategy

    Raises:
        KeyError: If strategy not found
    """
    if isinstance(strategy, str):
        strategy = StrategyName(strategy)
    return STRATEGY_PARAMETER_REGISTRY[strategy]


def get_default_parameters(strategy: StrategyName | str) -> dict[str, Any]:
    """Get default parameter values for a strategy.

    Args:
        strategy: Strategy name (enum or string)

    Returns:
        Dictionary of parameter names to default values
    """
    config = get_strategy_parameters(strategy)
    return config.get_defaults()


def _is_exit_parameter(param_def: ParameterDefinition) -> bool:
    text = f"{param_def.name} {param_def.display_name} {param_def.description}".lower()
    return "exit" in text


def filter_entry_only_param_config(
    param_config: StrategyParameterConfig,
) -> StrategyParameterConfig:
    """Return a param config without exit-related parameters."""
    entry_params = [p for p in param_config.parameters if not _is_exit_parameter(p)]
    return StrategyParameterConfig(
        strategy_name=param_config.strategy_name,
        display_name=param_config.display_name,
        description=param_config.description,
        parameters=entry_params,
    )


def filter_entry_only_params(
    strategy: StrategyName | str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Filter a params dict to entry-only parameters (no exit params)."""
    config = get_strategy_parameters(strategy)
    entry_param_names = {
        p.name for p in config.parameters if not _is_exit_parameter(p)
    }
    return {k: v for k, v in params.items() if k in entry_param_names}
