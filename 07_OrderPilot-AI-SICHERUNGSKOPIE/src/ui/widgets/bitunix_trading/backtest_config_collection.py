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
        configs = {}

        # Finde das ChartWindow (parent chain durchsuchen)
        chart_window = self.find_chart_window()

        if not chart_window:
            logger.warning("ChartWindow nicht gefunden - verwende Default-Configs")
            return self.get_default_engine_configs()

        # Entry Score Settings
        if hasattr(chart_window, 'entry_score_settings'):
            try:
                widget = chart_window.entry_score_settings
                if hasattr(widget, 'get_settings'):
                    configs['entry_score'] = widget.get_settings()
                    logger.debug("Entry Score Config geladen")
            except Exception as e:
                logger.warning(f"Entry Score Config Fehler: {e}")

        # Trigger/Exit Settings
        if hasattr(chart_window, 'trigger_exit_settings'):
            try:
                widget = chart_window.trigger_exit_settings
                if hasattr(widget, 'get_settings'):
                    configs['trigger_exit'] = widget.get_settings()
                    logger.debug("Trigger/Exit Config geladen")
            except Exception as e:
                logger.warning(f"Trigger/Exit Config Fehler: {e}")

        # Leverage Settings
        if hasattr(chart_window, 'leverage_settings'):
            try:
                widget = chart_window.leverage_settings
                if hasattr(widget, 'get_settings'):
                    configs['leverage'] = widget.get_settings()
                    logger.debug("Leverage Config geladen")
            except Exception as e:
                logger.warning(f"Leverage Config Fehler: {e}")

        # LLM Validation Settings
        if hasattr(chart_window, 'llm_validation_settings'):
            try:
                widget = chart_window.llm_validation_settings
                if hasattr(widget, 'get_settings'):
                    configs['llm_validation'] = widget.get_settings()
                    logger.debug("LLM Validation Config geladen")
            except Exception as e:
                logger.warning(f"LLM Validation Config Fehler: {e}")

        # Level Detection Settings
        if hasattr(chart_window, 'level_settings'):
            try:
                widget = chart_window.level_settings
                if hasattr(widget, 'get_settings'):
                    configs['levels'] = widget.get_settings()
                    logger.debug("Level Detection Config geladen")
            except Exception as e:
                logger.warning(f"Level Detection Config Fehler: {e}")

        # Bot Control Settings (Regime, Risk, etc.)
        if hasattr(chart_window, 'bot_control_tab'):
            try:
                # Sammle Regime-relevante Einstellungen
                tab = chart_window.bot_control_tab
                if hasattr(tab, 'get_settings'):
                    configs['bot_control'] = tab.get_settings()
                    logger.debug("Bot Control Config geladen")
            except Exception as e:
                logger.warning(f"Bot Control Config Fehler: {e}")

        # Daily Strategy Settings
        if hasattr(chart_window, 'bot_strategy_tab'):
            try:
                tab = chart_window.bot_strategy_tab
                if hasattr(tab, 'get_settings'):
                    configs['daily_strategy'] = tab.get_settings()
                    logger.debug("Daily Strategy Config geladen")
            except Exception as e:
                logger.warning(f"Daily Strategy Config Fehler: {e}")

        logger.info(f"Engine Configs geladen: {list(configs.keys())}")
        return configs

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
