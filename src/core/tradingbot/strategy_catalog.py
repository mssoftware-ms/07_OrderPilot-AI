"""Strategy Catalog for Tradingbot.

Defines pre-built strategy profiles for daily selection.
Each strategy has specific entry/exit rules, applicable regimes,
and parameter ranges.

REFACTORED: Split into multiple files to meet 600 LOC limit.
- strategy_definitions.py: StrategyType, EntryRule, ExitRule, StrategyDefinition
- strategy_templates.py: StrategyTemplatesMixin with template creation methods
- strategy_catalog.py: Main StrategyCatalog class (this file)
"""

from __future__ import annotations

import logging
import json
from pathlib import Path
from typing import TYPE_CHECKING

# Re-export types for backward compatibility
from .strategy_definitions import (
    EntryRule,
    ExitRule,
    StrategyDefinition,
    StrategyType,
)

if TYPE_CHECKING:
    from .models import RegimeState

__all__ = [
    "StrategyType",
    "EntryRule",
    "ExitRule",
    "StrategyDefinition",
    "StrategyCatalog",
]

logger = logging.getLogger(__name__)


class StrategyCatalog:
    """Catalog of trading strategies loaded from JSON configuration.

    Strategies are loaded from 'config/strategies/*.json' on initialization.
    """

    def __init__(self, strategies_dir: str = "config/strategies"):
        """Initialize strategy catalog and load strategies.
        
        Args:
            strategies_dir: Directory containing strategy JSON files
        """
        self._strategies: dict[str, StrategyDefinition] = {}
        self._strategies_dir = Path(strategies_dir)
        self._load_strategies()
        logger.info(f"StrategyCatalog initialized with {len(self._strategies)} strategies")

    def _load_strategies(self) -> None:
        """Load strategies from JSON files."""
        if not self._strategies_dir.exists():
            logger.warning(f"Strategies directory not found: {self._strategies_dir}")
            return

        for file_path in self._strategies_dir.glob("*.json"):
            try:
                self._load_single_strategy(file_path)
            except Exception as e:
                logger.error(f"Failed to load strategy from {file_path}: {e}")
                # We do NOT silently fail - we log error and the user will see a missing strategy
                # For critical errors (invalid JSON syntax), this will show in logs.
                # If we want to crash the app, we could raise e, but for robustness
                # logging the error is usually better so the app can still start with valid strategies.
                raise ValueError(f"CRITICAL: Invalid strategy config in {file_path}: {e}") from e

    def _load_single_strategy(self, file_path: Path) -> None:
        """Load a single strategy file.
        
        Args:
            file_path: Path to JSON file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate and create object using Pydantic
            strategy = StrategyDefinition(**data)
            
            # Use filename stem or profile name as key? Profile name is safer.
            name = strategy.profile.name
            
            if name in self._strategies:
                logger.warning(f"Duplicate strategy name '{name}' in {file_path}. Overwriting.")
            
            self._strategies[name] = strategy
            logger.debug(f"Loaded strategy: {name}")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Invalid strategy definition in {file_path}: {e}")

    # ==================== Query Methods ====================

    def get_strategy(self, name: str) -> StrategyDefinition | None:
        """Get strategy by name.

        Args:
            name: Strategy name

        Returns:
            StrategyDefinition or None if not found
        """
        return self._strategies.get(name)

    def get_all_strategies(self) -> list[StrategyDefinition]:
        """Get all registered strategies.

        Returns:
            List of all strategy definitions
        """
        return list(self._strategies.values())

    def get_strategies_for_regime(
        self,
        regime: "RegimeState"
    ) -> list[StrategyDefinition]:
        """Get strategies applicable for current regime.

        Args:
            regime: Current regime state

        Returns:
            List of applicable strategies
        """
        return [
            s for s in self._strategies.values()
            if s.is_applicable(regime)
        ]

    def get_strategies_by_type(
        self,
        strategy_type: StrategyType
    ) -> list[StrategyDefinition]:
        """Get strategies of a specific type.

        Args:
            strategy_type: Strategy type

        Returns:
            List of matching strategies
        """
        return [
            s for s in self._strategies.values()
            if s.strategy_type == strategy_type
        ]

    def register_strategy(
        self,
        name: str,
        strategy: StrategyDefinition
    ) -> None:
        """Register a custom strategy.

        Args:
            name: Strategy name
            strategy: Strategy definition
        """
        self._strategies[name] = strategy
        logger.info(f"Registered custom strategy: {name}")

    def list_strategies(self) -> list[str]:
        """List all strategy names.

        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())
