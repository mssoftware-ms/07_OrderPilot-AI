"""Backtest Config Parameter Space - Parameter Space Generation.

Refactored from 764 LOC monolith using composition pattern.

Module 2/4 of backtest_config_manager.py split.

Contains:
- get_parameter_space_from_configs(): Generiert Parameter-Space für Batch-Tests
"""

from __future__ import annotations

from typing import Any, Dict


class BacktestConfigParamSpace:
    """Helper für Parameter Space Generation."""

    def __init__(self, parent):
        """
        Args:
            parent: BacktestConfigManager Instanz
        """
        self.parent = parent

    def get_parameter_space_from_configs(self) -> Dict[str, list]:
        """
        Erstellt einen Parameter-Space für Batch-Tests basierend auf Engine-Configs.

        Generiert sinnvolle Variationen aller konfigurierbaren Parameter.

        Returns:
            Dict mit Parameter-Namen und möglichen Werten
        """
        configs = self.parent._collection.collect_engine_configs()
        param_space = {}

        # Entry Score Weights
        if 'entry_score' in configs:
            es = configs['entry_score']
            if 'weights' in es:
                # Variere Trend-Weight
                base_trend = es['weights'].get('trend_alignment', 0.25)
                param_space['entry_trend_weight'] = [
                    max(0.1, base_trend - 0.10),
                    base_trend,
                    min(0.4, base_trend + 0.10),
                ]

            if 'min_score_for_entry' in es:
                base_score = es.get('min_score_for_entry', 0.50)
                param_space['min_entry_score'] = [0.40, 0.50, 0.60, 0.70]

        # Trigger/Exit Settings
        if 'trigger_exit' in configs:
            te = configs['trigger_exit']
            if 'tp_atr_multiplier' in te:
                param_space['tp_atr_mult'] = [1.5, 2.0, 2.5, 3.0]
            if 'sl_atr_multiplier' in te:
                param_space['sl_atr_mult'] = [1.0, 1.5, 2.0]

        # Leverage Settings
        if 'leverage' in configs:
            lev = configs['leverage']
            if 'base_leverage' in lev:
                param_space['base_leverage'] = [3, 5, 10, 15]
            if 'max_leverage' in lev:
                param_space['max_leverage'] = [10, 20, 30]

        # Level Detection Settings
        if 'levels' in configs:
            lvl = configs['levels']
            if 'lookback_bars' in lvl:
                param_space['level_lookback'] = [50, 100, 150, 200]
            if 'min_touches' in lvl:
                param_space['level_min_touches'] = [2, 3, 4]

        return param_space
