"""Strategy Parameter Persistence.

Saves and loads optimized strategy parameters for use in production trading.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default path for strategy parameters
DEFAULT_PARAMS_DIR = Path("config/strategy_params")


def get_params_file(strategy_name: str, params_dir: Path | None = None) -> Path:
    """Get path to parameter file for a strategy.

    Args:
        strategy_name: Name of the strategy
        params_dir: Optional custom directory

    Returns:
        Path to the JSON parameter file
    """
    directory = params_dir or DEFAULT_PARAMS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{strategy_name}_params.json"


def save_strategy_params(
    strategy_name: str,
    params: dict[str, Any],
    symbol: str | None = None,
    score: float | None = None,
    params_dir: Path | None = None,
) -> Path:
    """Save optimized strategy parameters.

    Args:
        strategy_name: Name of the strategy (e.g., "breakout", "momentum")
        params: Dictionary of parameter values
        symbol: Optional symbol the parameters were optimized for
        score: Optional optimization score achieved
        params_dir: Optional custom directory

    Returns:
        Path to saved file
    """
    filepath = get_params_file(strategy_name, params_dir)

    data = {
        "strategy": strategy_name,
        "parameters": params,
        "metadata": {
            "saved_at": datetime.now().isoformat(),
            "symbol": symbol,
            "optimization_score": score,
        }
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved strategy parameters to {filepath}")
    return filepath


def load_strategy_params(
    strategy_name: str,
    params_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Load saved strategy parameters.

    Args:
        strategy_name: Name of the strategy
        params_dir: Optional custom directory

    Returns:
        Parameter dictionary or None if not found
    """
    filepath = get_params_file(strategy_name, params_dir)

    if not filepath.exists():
        logger.debug(f"No saved parameters found for {strategy_name}")
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Loaded parameters for {strategy_name} from {filepath}")
        return data.get("parameters", {})
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Failed to load parameters for {strategy_name}: {e}")
        return None


def get_all_saved_strategies(params_dir: Path | None = None) -> list[str]:
    """Get list of strategies with saved parameters.

    Args:
        params_dir: Optional custom directory

    Returns:
        List of strategy names
    """
    directory = params_dir or DEFAULT_PARAMS_DIR

    if not directory.exists():
        return []

    strategies = []
    for filepath in directory.glob("*_params.json"):
        # Extract strategy name from filename
        name = filepath.stem.replace("_params", "")
        strategies.append(name)

    return strategies


def delete_strategy_params(
    strategy_name: str,
    params_dir: Path | None = None,
) -> bool:
    """Delete saved strategy parameters.

    Args:
        strategy_name: Name of the strategy
        params_dir: Optional custom directory

    Returns:
        True if deleted, False if not found
    """
    filepath = get_params_file(strategy_name, params_dir)

    if filepath.exists():
        filepath.unlink()
        logger.info(f"Deleted parameters for {strategy_name}")
        return True

    return False


def get_params_metadata(
    strategy_name: str,
    params_dir: Path | None = None,
) -> dict[str, Any] | None:
    """Get metadata for saved parameters.

    Args:
        strategy_name: Name of the strategy
        params_dir: Optional custom directory

    Returns:
        Metadata dictionary or None
    """
    filepath = get_params_file(strategy_name, params_dir)

    if not filepath.exists():
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("metadata", {})
    except (json.JSONDecodeError, IOError):
        return None
