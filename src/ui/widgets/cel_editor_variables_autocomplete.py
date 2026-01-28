"""
CEL Editor Variables Autocomplete Extension.

This module extends the CEL Editor with variable autocomplete functionality.
Integrates with the Variable System to provide context-aware suggestions.

Author: OrderPilot-AI Development Team
Created: 2026-01-28
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    try:
        from PyQt6.Qsci import QsciAPIs
    except ImportError:
        QsciAPIs = None

logger = logging.getLogger(__name__)


class CelEditorVariablesAutocomplete:
    """
    Variables Autocomplete extension for CEL Editor.

    Provides:
        - Load variables from all sources (Chart, Bot, Project, Indicators, Regime)
        - Add variables to QScintilla autocomplete
        - Refresh autocomplete when variables change
        - Type hints in tooltips
    """

    def __init__(self, api: Optional[QsciAPIs] = None):
        """
        Initialize Variables Autocomplete.

        Args:
            api: QsciAPIs instance for autocomplete (optional)
        """
        self.api = api
        self._cached_variables: Dict[str, Dict[str, Any]] = {}

    def load_all_variables(
        self,
        chart_window: Optional[any] = None,
        bot_config: Optional[any] = None,
        project_vars_path: Optional[str | Path] = None,
        indicators: Optional[Dict[str, Any]] = None,
        regime: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Load all available variables from all sources.

        Args:
            chart_window: ChartWindow instance for chart.* variables
            bot_config: BotConfig instance for bot.* variables
            project_vars_path: Path to .cel_variables.json for project.*
            indicators: Dictionary of indicator values for indicators.*
            regime: Dictionary of regime values for regime.*

        Returns:
            Dictionary mapping variable names to their metadata:
            {
                "chart.price": {
                    "type": "float",
                    "description": "Current price",
                    "category": "Chart"
                },
                ...
            }
        """
        variables = {}

        # 1. Chart variables
        if chart_window:
            try:
                from src.core.variables import ChartDataProvider

                provider = ChartDataProvider()
                available = provider.get_available_variables()
                for var_name, var_info in available.items():
                    variables[var_name] = {
                        "type": var_info.get("type", "unknown"),
                        "description": var_info.get("description", ""),
                        "category": "Chart",
                    }
            except Exception as e:
                logger.warning(f"Failed to load chart variables: {e}")

        # 2. Bot variables
        if bot_config:
            try:
                from src.core.variables import BotConfigProvider

                provider = BotConfigProvider()
                available = provider.get_available_variables()
                for var_name, var_info in available.items():
                    variables[var_name] = {
                        "type": var_info.get("type", "unknown"),
                        "description": var_info.get("description", ""),
                        "category": "Bot",
                    }
            except Exception as e:
                logger.warning(f"Failed to load bot variables: {e}")

        # 3. Project variables
        if project_vars_path:
            try:
                from src.core.variables import VariableStorage

                storage = VariableStorage()
                project_vars = storage.load(
                    Path(project_vars_path), create_if_missing=False
                )

                for var_name, var in project_vars.variables.items():
                    full_name = f"project.{var_name}"
                    variables[full_name] = {
                        "type": var.type.value,
                        "description": var.description,
                        "category": var.category,
                    }
            except Exception as e:
                logger.warning(f"Failed to load project variables: {e}")

        # 4. Indicator variables
        if indicators:
            for indicator_name in indicators.keys():
                var_name = f"indicators.{indicator_name}"
                variables[var_name] = {
                    "type": "float",
                    "description": f"Indicator: {indicator_name}",
                    "category": "Indicators",
                }

        # 5. Regime variables
        if regime:
            for regime_key in regime.keys():
                var_name = f"regime.{regime_key}"
                variables[var_name] = {
                    "type": "string",
                    "description": f"Regime: {regime_key}",
                    "category": "Regime",
                }

        self._cached_variables = variables
        logger.info(f"Loaded {len(variables)} variables for autocomplete")
        return variables

    def add_to_autocomplete(self, variables: Optional[Dict[str, Dict[str, Any]]] = None) -> int:
        """
        Add variables to QScintilla autocomplete.

        Args:
            variables: Dictionary of variables (uses cached if None)

        Returns:
            Number of variables added
        """
        if self.api is None:
            logger.warning("QsciAPIs not available, autocomplete disabled")
            return 0

        if variables is None:
            variables = self._cached_variables

        if not variables:
            logger.warning("No variables to add to autocomplete")
            return 0

        count = 0
        for var_name, var_info in variables.items():
            try:
                # Format: variable_name(type) - description
                var_type = var_info.get("type", "unknown")
                description = var_info.get("description", "")

                # Create autocomplete entry
                # QScintilla format: "variable_name?1" where 1 is the type number
                # For CEL, we just use the variable name
                autocomplete_entry = f"{var_name}"

                self.api.add(autocomplete_entry)
                count += 1
            except Exception as e:
                logger.error(f"Failed to add variable {var_name} to autocomplete: {e}")

        logger.info(f"Added {count} variables to autocomplete")
        return count

    def refresh_autocomplete(
        self,
        chart_window: Optional[any] = None,
        bot_config: Optional[any] = None,
        project_vars_path: Optional[str | Path] = None,
        indicators: Optional[Dict[str, Any]] = None,
        regime: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Refresh autocomplete with updated variables.

        Reloads all variables and updates autocomplete.

        Args:
            chart_window: ChartWindow instance
            bot_config: BotConfig instance
            project_vars_path: Path to .cel_variables.json
            indicators: Dictionary of indicator values
            regime: Dictionary of regime values

        Returns:
            Number of variables added
        """
        if self.api is None:
            return 0

        # Load updated variables
        variables = self.load_all_variables(
            chart_window=chart_window,
            bot_config=bot_config,
            project_vars_path=project_vars_path,
            indicators=indicators,
            regime=regime,
        )

        # Clear existing autocomplete (recreate API)
        # Note: QsciAPIs doesn't have a clear() method, so we need to recreate it
        # This is handled by the caller (CEL Editor) which will create a new API instance

        # Add variables
        count = self.add_to_autocomplete(variables)

        # Prepare autocomplete
        if self.api:
            self.api.prepare()

        logger.info(f"Autocomplete refreshed with {count} variables")
        return count

    def get_variable_tooltip(self, var_name: str) -> Optional[str]:
        """
        Get tooltip text for a variable.

        Args:
            var_name: Variable name (e.g., "chart.price")

        Returns:
            Tooltip text or None if variable not found
        """
        if var_name not in self._cached_variables:
            return None

        var_info = self._cached_variables[var_name]
        var_type = var_info.get("type", "unknown")
        description = var_info.get("description", "No description")
        category = var_info.get("category", "Unknown")

        tooltip = f"<b>{var_name}</b><br>"
        tooltip += f"Type: <i>{var_type}</i><br>"
        tooltip += f"Category: {category}<br>"
        tooltip += f"{description}"

        return tooltip

    def get_variables_by_prefix(self, prefix: str) -> List[str]:
        """
        Get variable names matching a prefix.

        Args:
            prefix: Prefix to match (e.g., "chart.")

        Returns:
            List of matching variable names
        """
        return [
            var_name
            for var_name in self._cached_variables.keys()
            if var_name.startswith(prefix)
        ]

    def get_variable_categories(self) -> List[str]:
        """
        Get list of all variable categories.

        Returns:
            List of category names
        """
        categories = set()
        for var_info in self._cached_variables.values():
            category = var_info.get("category")
            if category:
                categories.add(category)
        return sorted(categories)
