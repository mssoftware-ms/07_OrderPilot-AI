"""Backtest Config Manager - Engine Configuration Collection (Refactored).

Refactored from 764 LOC monolith using composition pattern.

Main Orchestrator (Module 5/5).

Delegates to 4 specialized helper modules:
- BacktestConfigCollection: Config collection from UI widgets
- BacktestConfigParamSpace: Parameter space generation
- BacktestConfigParamSpec: Detailed parameter specification
- BacktestConfigVariants: Indicator sets and AI variant generation

Provides:
- BacktestConfigManager: Main orchestration class with delegation
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

from src.ui.widgets.bitunix_trading.backtest_config_collection import (
    BacktestConfigCollection,
)
from src.ui.widgets.bitunix_trading.backtest_config_param_space import (
    BacktestConfigParamSpace,
)
from src.ui.widgets.bitunix_trading.backtest_config_param_spec import (
    BacktestConfigParamSpec,
)
from src.ui.widgets.bitunix_trading.backtest_config_variants import (
    BacktestConfigVariants,
)

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class BacktestConfigManager:
    """Verwaltet Engine-Konfigurationen für Backtests."""

    def __init__(self, parent_widget: "QWidget"):
        """
        Args:
            parent_widget: BacktestTab Widget
        """
        self.parent = parent_widget

        # Instantiate helper modules (composition pattern)
        self._collection = BacktestConfigCollection(parent=self)
        self._param_space = BacktestConfigParamSpace(parent=self)
        self._param_spec = BacktestConfigParamSpec(parent=self)
        self._variants = BacktestConfigVariants(parent=self)

    def collect_engine_configs(self) -> Dict[str, Any]:
        """
        Sammelt alle Engine-Konfigurationen aus den Engine Settings Tabs.

        Delegates to BacktestConfigCollection.collect_engine_configs().

        Returns:
            Dict mit allen Engine-Konfigurationen
        """
        return self._collection.collect_engine_configs()

    def get_parameter_space_from_configs(self) -> Dict[str, list]:
        """
        Erstellt einen Parameter-Space für Batch-Tests basierend auf Engine-Configs.

        Delegates to BacktestConfigParamSpace.get_parameter_space_from_configs().

        Returns:
            Dict mit Parameter-Namen und möglichen Werten
        """
        return self._param_space.get_parameter_space_from_configs()

    def get_parameter_specification(self) -> list[Dict[str, Any]]:
        """
        Erstellt eine vollständige Parameter-Spezifikation als Tabelle.

        Delegates to BacktestConfigParamSpec.get_parameter_specification().

        Returns:
            Liste von Dicts mit Parameter-Spezifikationen
        """
        return self._param_spec.get_parameter_specification()

    def get_available_indicator_sets(self) -> list[Dict[str, Any]]:
        """
        Gibt die verfügbaren Indikator-Sets zurück.

        Delegates to BacktestConfigVariants.get_available_indicator_sets().

        Returns:
            Liste von Indikator-Set Definitionen
        """
        return self._variants.get_available_indicator_sets()

    def generate_ai_test_variants(self, base_spec: list[Dict], num_variants: int = 10) -> list[Dict[str, Any]]:
        """
        Generiert intelligente Test-Varianten basierend auf der Parameter-Spezifikation.

        Delegates to BacktestConfigVariants.generate_ai_test_variants().

        Args:
            base_spec: Parameter-Spezifikation
            num_variants: Anzahl der zu generierenden Varianten

        Returns:
            Liste von Test-Varianten
        """
        return self._variants.generate_ai_test_variants(base_spec, num_variants)


# Re-export für backward compatibility
__all__ = [
    "BacktestConfigManager",
    "BacktestConfigCollection",
    "BacktestConfigParamSpace",
    "BacktestConfigParamSpec",
    "BacktestConfigVariants",
]
