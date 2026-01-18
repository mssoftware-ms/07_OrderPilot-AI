"""Grid Search Engine for Indicator Parameter Optimization.

Generates parameter combinations for indicators based on catalog definitions
and performs exhaustive or sampled search across parameter space.
"""

from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ParameterCombination:
    """Single parameter combination for an indicator."""
    indicator_type: str
    params: dict[str, Any]
    combination_id: str  # Unique identifier


@dataclass
class GridSearchConfig:
    """Configuration for grid search."""
    preset: str = "balanced"  # quick_scan, balanced, exhaustive, regime_optimized
    filter_by_regime: str | None = None  # R1, R2, R3, R4, R5
    min_compatibility_score: float = 0.7
    max_combinations_per_indicator: int = 10


class IndicatorGridSearch:
    """Generates parameter combinations for indicator optimization.

    Reads indicator catalog and generates all possible parameter combinations
    for grid search optimization.

    Example:
        >>> search = IndicatorGridSearch()
        >>> search.load_catalog("config/indicator_catalog.yaml")
        >>> combos = search.generate_combinations("RSI", preset="balanced")
        >>> for combo in combos:
        ...     print(combo.params)  # {'period': 7}, {'period': 9}, ...
    """

    def __init__(self, catalog_path: str | None = None):
        """Initialize grid search engine.

        Args:
            catalog_path: Path to indicator catalog YAML file
        """
        self.catalog_path = catalog_path
        self.catalog: dict = {}

        if catalog_path:
            self.load_catalog(catalog_path)

    def load_catalog(self, path: str) -> None:
        """Load indicator catalog from YAML file.

        Args:
            path: Path to catalog YAML file
        """
        try:
            with open(path, 'r') as f:
                self.catalog = yaml.safe_load(f)
            logger.info(f"Loaded indicator catalog from {path}")
            logger.info(f"Total indicators: {self.catalog['metadata']['total_indicators']}")
        except FileNotFoundError:
            logger.error(f"Catalog file not found: {path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML catalog: {e}")
            raise

    def get_indicator_definition(self, indicator_type: str) -> dict | None:
        """Get indicator definition from catalog.

        Args:
            indicator_type: Indicator type (e.g., "RSI", "MACD")

        Returns:
            Indicator definition dict or None if not found
        """
        # Search across all categories
        for category_key in ['trend_indicators', 'momentum_indicators',
                             'volatility_indicators', 'volume_indicators']:
            if category_key not in self.catalog:
                continue

            category = self.catalog[category_key]
            indicator_key = indicator_type.lower()

            if indicator_key in category:
                definition = category[indicator_key].copy()
                definition['type'] = indicator_type.upper()
                return definition

        logger.warning(f"Indicator type '{indicator_type}' not found in catalog")
        return None

    def generate_combinations(
        self,
        indicator_type: str,
        config: GridSearchConfig | None = None
    ) -> list[ParameterCombination]:
        """Generate all parameter combinations for an indicator.

        Args:
            indicator_type: Indicator type (e.g., "RSI", "MACD")
            config: Grid search configuration (uses defaults if None)

        Returns:
            List of parameter combinations
        """
        if config is None:
            config = GridSearchConfig()

        definition = self.get_indicator_definition(indicator_type)
        if not definition:
            return []

        # Check regime compatibility if filtering
        if config.filter_by_regime:
            compatibility = definition.get('regime_compatibility', {})
            regime_score = compatibility.get(config.filter_by_regime, 0.0)

            if regime_score < config.min_compatibility_score:
                logger.debug(
                    f"Skipping {indicator_type} for {config.filter_by_regime} "
                    f"(compatibility: {regime_score:.2f} < {config.min_compatibility_score:.2f})"
                )
                return []

        # Get parameter definitions
        parameters = definition.get('parameters', {})
        if not parameters:
            # No parameters - return single combination with empty params
            return [
                ParameterCombination(
                    indicator_type=indicator_type.upper(),
                    params={},
                    combination_id=f"{indicator_type}_default"
                )
            ]

        # Generate combinations based on preset
        preset_config = self.catalog['grid_search_presets'][config.preset]
        max_combinations = min(
            preset_config['max_combinations_per_indicator'],
            config.max_combinations_per_indicator
        )

        # Build parameter value lists
        param_value_lists = {}
        for param_name, param_def in parameters.items():
            if 'grid_search_values' in param_def:
                # Use predefined grid search values
                values = param_def['grid_search_values'][:max_combinations]
            elif 'options' in param_def:
                # Use predefined options (e.g., for string parameters)
                values = param_def['options']
            elif param_def['type'] in ['int', 'float']:
                # Generate values from range
                range_min, range_max = param_def['range']
                values = self._generate_range_values(
                    range_min, range_max,
                    max_combinations,
                    param_def['type']
                )
            else:
                # Use default value only
                values = [param_def['default']]

            param_value_lists[param_name] = values

        # Generate all combinations
        param_names = list(param_value_lists.keys())
        param_values_product = itertools.product(*[param_value_lists[name] for name in param_names])

        combinations = []
        for idx, values_tuple in enumerate(param_values_product):
            params = dict(zip(param_names, values_tuple))

            # Validate constraints
            if not self._validate_constraints(params, definition.get('constraints', [])):
                continue

            combo = ParameterCombination(
                indicator_type=indicator_type.upper(),
                params=params,
                combination_id=f"{indicator_type}_{idx:04d}"
            )
            combinations.append(combo)

        logger.info(
            f"Generated {len(combinations)} parameter combinations for {indicator_type} "
            f"(preset: {config.preset})"
        )

        return combinations

    def _generate_range_values(
        self,
        range_min: int | float,
        range_max: int | float,
        max_values: int,
        value_type: str
    ) -> list[int | float]:
        """Generate values within a range.

        Args:
            range_min: Minimum value
            range_max: Maximum value
            max_values: Maximum number of values to generate
            value_type: "int" or "float"

        Returns:
            List of values
        """
        if value_type == 'int':
            # Integer range
            step = max(1, (range_max - range_min) // (max_values - 1))
            values = list(range(range_min, range_max + 1, step))[:max_values]
        else:
            # Float range
            step = (range_max - range_min) / (max_values - 1)
            values = [range_min + i * step for i in range(max_values)]

        return values

    def _validate_constraints(self, params: dict, constraints: list[str]) -> bool:
        """Validate parameter combination against constraints.

        Args:
            params: Parameter dictionary
            constraints: List of constraint expressions (e.g., "fast < slow")

        Returns:
            True if all constraints satisfied, False otherwise
        """
        if not constraints:
            return True

        for constraint in constraints:
            try:
                # Evaluate constraint in context of params
                # Note: Using eval is safe here since constraints come from YAML config
                if not eval(constraint, {"__builtins__": {}}, params):
                    return False
            except Exception as e:
                logger.warning(f"Failed to evaluate constraint '{constraint}': {e}")
                return False

        return True

    def generate_batch(
        self,
        indicator_types: list[str],
        config: GridSearchConfig | None = None
    ) -> dict[str, list[ParameterCombination]]:
        """Generate combinations for multiple indicators.

        Args:
            indicator_types: List of indicator types
            config: Grid search configuration

        Returns:
            Dictionary mapping indicator type to list of combinations
        """
        if config is None:
            config = GridSearchConfig()

        results = {}
        for indicator_type in indicator_types:
            combinations = self.generate_combinations(indicator_type, config)
            if combinations:
                results[indicator_type] = combinations

        total_combinations = sum(len(combos) for combos in results.values())
        logger.info(
            f"Generated {total_combinations} total combinations "
            f"for {len(results)} indicators"
        )

        return results

    def get_regime_compatible_indicators(
        self,
        regime_id: str,
        min_score: float = 0.7
    ) -> list[str]:
        """Get list of indicators compatible with a regime.

        Args:
            regime_id: Regime ID (R1, R2, R3, R4, R5)
            min_score: Minimum compatibility score

        Returns:
            List of compatible indicator types
        """
        compatible = []

        for category_key in ['trend_indicators', 'momentum_indicators',
                             'volatility_indicators', 'volume_indicators']:
            if category_key not in self.catalog:
                continue

            category = self.catalog[category_key]
            for indicator_key, definition in category.items():
                compatibility = definition.get('regime_compatibility', {})
                score = compatibility.get(regime_id, 0.0)

                if score >= min_score:
                    indicator_type = definition.get('type', indicator_key.upper())
                    compatible.append(indicator_type)

        logger.info(
            f"Found {len(compatible)} indicators compatible with {regime_id} "
            f"(min_score: {min_score:.2f})"
        )

        return compatible

    def get_recommended_indicators(self, regime_id: str) -> dict[str, list[str]]:
        """Get recommended indicators for a regime.

        Args:
            regime_id: Regime ID (R1_trend, R2_range, etc.)

        Returns:
            Dictionary with 'primary', 'secondary', 'avoid' lists
        """
        recommendations = self.catalog.get('regime_recommendations', {})
        regime_rec = recommendations.get(regime_id, {})

        return {
            'primary': regime_rec.get('primary', []),
            'secondary': regime_rec.get('secondary', []),
            'avoid': regime_rec.get('avoid', [])
        }
