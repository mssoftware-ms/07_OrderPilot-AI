"""Backtest Config Collection - Engine Settings Collection.

Refactored from 764 LOC monolith using composition pattern.

Module 1/4 of backtest_config_manager.py split.

Contains:
- collect_engine_configs(): Collects configs from ChartWindow UI widgets
- _find_chart_window(): Helper to find ChartWindow in parent chain
- _get_default_engine_configs(): Returns default engine configurations
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class BacktestConfigCollection:
    """Helper für Engine Config Collection aus UI Widgets."""

    def __init__(self, parent):
        """
        Args:
            parent: BacktestConfigManager Instanz
        """
        self.parent = parent

    def collect_engine_configs(self) -> Dict[str, Any]:
        """
        Sammelt alle Engine-Konfigurationen aus den Engine Settings Tabs.

        Sucht nach den Settings-Widgets im Parent (ChartWindow) und
        liest deren aktuelle Einstellungen.

        Returns:
            Dict mit allen Engine-Konfigurationen
        """
        chart_window = self.find_chart_window()

        if not chart_window:
            logger.warning("ChartWindow nicht gefunden - verwende Default-Configs")
            return self.get_default_engine_configs()

        # Collect all settings using DRY helper
        configs = self._collect_all_settings(chart_window)

        logger.info(f"Engine Configs geladen: {list(configs.keys())}")
        return configs

    def _collect_all_settings(self, chart_window) -> Dict[str, Any]:
        """Collect all engine settings from chart window.

        Args:
            chart_window: ChartWindow widget containing settings.

        Returns:
            Dictionary of all collected settings.
        """
        # Define settings to collect: (attribute_name, config_key, display_name)
        settings_specs = [
            ('entry_score_settings', 'entry_score', 'Entry Score'),
            ('trigger_exit_settings', 'trigger_exit', 'Trigger/Exit'),
            ('leverage_settings', 'leverage', 'Leverage'),
            ('llm_validation_settings', 'llm_validation', 'LLM Validation'),
            ('level_settings', 'levels', 'Level Detection'),
            ('bot_control_tab', 'bot_control', 'Bot Control'),
            ('bot_strategy_tab', 'daily_strategy', 'Daily Strategy'),
        ]

        configs = {}
        for attr_name, config_key, display_name in settings_specs:
            config = self._collect_single_setting(
                chart_window, attr_name, config_key, display_name
            )
            if config is not None:
                configs[config_key] = config

        return configs

    def _collect_single_setting(
        self, chart_window, attr_name: str, config_key: str, display_name: str
    ) -> Dict[str, Any] | None:
        """Collect a single setting from chart window widget.

        Args:
            chart_window: ChartWindow widget.
            attr_name: Attribute name to look for.
            config_key: Key for configs dictionary.
            display_name: Display name for logging.

        Returns:
            Settings dictionary or None if not found/error.
        """
        if not hasattr(chart_window, attr_name):
            return None

        try:
            widget = getattr(chart_window, attr_name)
            if hasattr(widget, 'get_settings'):
                settings = widget.get_settings()
                logger.debug(f"{display_name} Config geladen")
                return settings
        except Exception as e:
            logger.warning(f"{display_name} Config Fehler: {e}")

        return None

    def find_chart_window(self) -> Optional["QWidget"]:
        """
        Sucht das ChartWindow in der Parent-Hierarchie.

        Returns:
            ChartWindow Widget oder None
        """
        widget = self.parent.parent.parent()
        max_depth = 10

        for _ in range(max_depth):
            if widget is None:
                break

            # Prüfe ob es ein ChartWindow ist (anhand der Engine Settings)
            if hasattr(widget, 'entry_score_settings') or hasattr(widget, 'engine_settings_tabs'):
                return widget

            # Prüfe nach typischen ChartWindow Attributen
            if hasattr(widget, 'chart_widget') and hasattr(widget, 'panel_tabs'):
                return widget

            widget = widget.parent()

        return None

    def get_default_engine_configs(self) -> Dict[str, Any]:
        """
        Gibt Default-Engine-Konfigurationen zurück.

        Returns:
            Dict mit Standard-Konfigurationen
        """
        return {
            'entry_score': {
                'weights': {
                    'trend_alignment': 0.25,
                    'rsi': 0.15,
                    'macd': 0.20,
                    'adx': 0.15,
                    'volatility': 0.10,
                    'volume': 0.15,
                },
                'thresholds': {
                    'excellent': 0.80,
                    'good': 0.65,
                    'moderate': 0.50,
                    'weak': 0.35,
                },
                'gates': {
                    'block_in_chop': True,
                    'block_against_strong_trend': True,
                    'allow_counter_trend_sfp': True,
                    'trend_boost': 0.10,
                    'chop_penalty': 0.15,
                    'volatile_penalty': 0.10,
                },
                'min_score_for_entry': 0.50,
            },
            'trigger_exit': {
                'tp_atr_multiplier': 2.0,
                'sl_atr_multiplier': 1.5,
                'trailing_enabled': True,
                'trailing_activation_r': 1.0,
                'trailing_distance_r': 0.5,
            },
            'leverage': {
                'base_leverage': 5,
                'max_leverage': 20,
                'regime_adjustment': True,
                'volatility_scaling': True,
            },
            'levels': {
                'lookback_bars': 100,
                'min_touches': 2,
                'zone_width_atr': 0.5,
                'significance_threshold': 0.7,
            },
        }
