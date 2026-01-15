"""Backtest Config Parameter Specification - Detailed Parameter Specifications.

Refactored from 764 LOC monolith using composition pattern.

Module 3/4 of backtest_config_manager.py split.

Contains:
- get_parameter_specification(): Erstellt vollständige Parameter-Tabelle
"""

from __future__ import annotations

from typing import Any, Dict


class BacktestConfigParamSpec:
    """Helper für Parameter Specification (detaillierte Parameter-Tabelle)."""

    def __init__(self, parent):
        """
        Args:
            parent: BacktestConfigManager Instanz
        """
        self.parent = parent

    def get_parameter_specification(self) -> list[Dict[str, Any]]:
        """
        Erstellt eine vollständige Parameter-Spezifikation als Tabelle.

        Zeigt alle konfigurierbaren Parameter mit:
        - Parameter-Name
        - Aktueller Wert
        - UI-Element/Tab
        - Beschreibung
        - Typ
        - Min/Max
        - Standard-Variationen

        Returns:
            Liste von Dicts mit Parameter-Spezifikationen
        """
        configs = self.parent._collection.collect_engine_configs()
        specs = []

        # =================================================================
        # ENTRY SCORE PARAMETERS
        # =================================================================
        es = configs.get('entry_score', {})

        # Weights
        weights = es.get('weights', {})
        weight_params = [
            ('trend_alignment', 'Trend EMA-Stack Gewichtung', 0.0, 0.5),
            ('rsi', 'RSI Momentum Gewichtung', 0.0, 0.5),
            ('macd', 'MACD Crossover Gewichtung', 0.0, 0.5),
            ('adx', 'ADX Trendstärke Gewichtung', 0.0, 0.5),
            ('volatility', 'ATR/BB Volatilität Gewichtung', 0.0, 0.5),
            ('volume', 'Volumen Confirmation Gewichtung', 0.0, 0.5),
        ]

        for name, desc, min_v, max_v in weight_params:
            current = weights.get(name, 0.15)
            specs.append({
                'category': 'Entry Score',
                'subcategory': 'Weights',
                'parameter': f'weight_{name}',
                'display_name': name.replace('_', ' ').title(),
                'current_value': current,
                'ui_tab': 'Engine Settings → Entry Score',
                'description': desc,
                'type': 'float',
                'min': min_v,
                'max': max_v,
                'step': 0.05,
                'variations': [max(min_v, current - 0.1), current, min(max_v, current + 0.1)],
            })

        # Thresholds
        thresholds = es.get('thresholds', {})
        threshold_params = [
            ('excellent', 'Score für EXCELLENT Quality', 0.5, 1.0, 0.80),
            ('good', 'Score für GOOD Quality', 0.4, 0.9, 0.65),
            ('moderate', 'Score für MODERATE Quality', 0.3, 0.8, 0.50),
            ('weak', 'Score für WEAK Quality', 0.1, 0.6, 0.35),
        ]

        for name, desc, min_v, max_v, default in threshold_params:
            current = thresholds.get(name, default)
            specs.append({
                'category': 'Entry Score',
                'subcategory': 'Thresholds',
                'parameter': f'threshold_{name}',
                'display_name': f'{name.upper()} Threshold',
                'current_value': current,
                'ui_tab': 'Engine Settings → Entry Score',
                'description': desc,
                'type': 'float',
                'min': min_v,
                'max': max_v,
                'step': 0.05,
                'variations': [current - 0.05, current, current + 0.05],
            })

        # Min Score for Entry
        specs.append({
            'category': 'Entry Score',
            'subcategory': 'Requirements',
            'parameter': 'min_score_for_entry',
            'display_name': 'Min Entry Score',
            'current_value': es.get('min_score_for_entry', 0.50),
            'ui_tab': 'Engine Settings → Entry Score',
            'description': 'Minimum Score für gültiges Signal',
            'type': 'float',
            'min': 0.1,
            'max': 0.9,
            'step': 0.05,
            'variations': [0.40, 0.50, 0.60, 0.70],
        })

        # Gates
        gates = es.get('gates', {})
        gate_params = [
            ('block_in_chop', 'bool', 'Block bei Seitwärtsbewegung', True),
            ('block_against_strong_trend', 'bool', 'Block gegen starken Trend', True),
            ('allow_counter_trend_sfp', 'bool', 'SFP Counter-Trend erlauben', True),
            ('trend_boost', 'float', 'Score-Bonus bei aligned Trend', 0.10),
            ('chop_penalty', 'float', 'Score-Penalty bei CHOP', 0.15),
            ('volatile_penalty', 'float', 'Score-Penalty bei Volatilität', 0.10),
        ]

        for name, ptype, desc, default in gate_params:
            current = gates.get(name, default)
            if ptype == 'bool':
                variations = [True, False]
            else:
                variations = [max(0, current - 0.05), current, min(0.3, current + 0.05)]

            specs.append({
                'category': 'Entry Score',
                'subcategory': 'Gates',
                'parameter': f'gate_{name}',
                'display_name': name.replace('_', ' ').title(),
                'current_value': current,
                'ui_tab': 'Engine Settings → Entry Score',
                'description': desc,
                'type': ptype,
                'min': 0 if ptype == 'float' else None,
                'max': 0.5 if ptype == 'float' else None,
                'step': 0.05 if ptype == 'float' else None,
                'variations': variations,
            })

        # =================================================================
        # TRIGGER/EXIT PARAMETERS
        # =================================================================
        te = configs.get('trigger_exit', {})

        trigger_params = [
            ('tp_atr_multiplier', 'Take Profit ATR Multiplikator', 1.0, 5.0, 2.0),
            ('sl_atr_multiplier', 'Stop Loss ATR Multiplikator', 0.5, 3.0, 1.5),
            ('trailing_activation_r', 'Trailing Aktivierung (R)', 0.5, 3.0, 1.0),
            ('trailing_distance_r', 'Trailing Distanz (R)', 0.2, 1.5, 0.5),
        ]

        for name, desc, min_v, max_v, default in trigger_params:
            current = te.get(name, default)
            specs.append({
                'category': 'Trigger/Exit',
                'subcategory': 'TP/SL',
                'parameter': name,
                'display_name': name.replace('_', ' ').title(),
                'current_value': current,
                'ui_tab': 'Engine Settings → Trigger/Exit',
                'description': desc,
                'type': 'float',
                'min': min_v,
                'max': max_v,
                'step': 0.25,
                'variations': [min_v, (min_v + max_v) / 2, max_v],
            })

        specs.append({
            'category': 'Trigger/Exit',
            'subcategory': 'Trailing',
            'parameter': 'trailing_enabled',
            'display_name': 'Trailing Stop',
            'current_value': te.get('trailing_enabled', True),
            'ui_tab': 'Engine Settings → Trigger/Exit',
            'description': 'Trailing Stop aktivieren',
            'type': 'bool',
            'min': None,
            'max': None,
            'step': None,
            'variations': [True, False],
        })

        # =================================================================
        # LEVERAGE PARAMETERS
        # =================================================================
        lev = configs.get('leverage', {})

        leverage_params = [
            ('base_leverage', 'int', 'Basis-Leverage', 1, 50, 5),
            ('max_leverage', 'int', 'Maximum Leverage', 5, 125, 20),
        ]

        for name, ptype, desc, min_v, max_v, default in leverage_params:
            current = lev.get(name, default)
            specs.append({
                'category': 'Leverage',
                'subcategory': 'Limits',
                'parameter': name,
                'display_name': name.replace('_', ' ').title(),
                'current_value': current,
                'ui_tab': 'Engine Settings → Leverage',
                'description': desc,
                'type': ptype,
                'min': min_v,
                'max': max_v,
                'step': 1,
                'variations': [3, 5, 10, 15, 20],
            })

        specs.append({
            'category': 'Leverage',
            'subcategory': 'Adjustments',
            'parameter': 'regime_adjustment',
            'display_name': 'Regime Adjustment',
            'current_value': lev.get('regime_adjustment', True),
            'ui_tab': 'Engine Settings → Leverage',
            'description': 'Leverage nach Regime anpassen',
            'type': 'bool',
            'min': None,
            'max': None,
            'step': None,
            'variations': [True, False],
        })

        # =================================================================
        # LEVEL DETECTION PARAMETERS
        # =================================================================
        lvl = configs.get('levels', {})

        level_params = [
            ('lookback_bars', 'int', 'Lookback für Level-Erkennung', 20, 500, 100),
            ('min_touches', 'int', 'Min. Touches für Level', 1, 10, 2),
            ('zone_width_atr', 'float', 'Zone-Breite (ATR)', 0.1, 2.0, 0.5),
            ('significance_threshold', 'float', 'Signifikanz-Schwelle', 0.3, 1.0, 0.7),
        ]

        for name, ptype, desc, min_v, max_v, default in level_params:
            current = lvl.get(name, default)
            if ptype == 'int':
                step = max(1, (max_v - min_v) // 5)
                variations = list(range(min_v, max_v + 1, step))[:5]
            else:
                step = (max_v - min_v) / 5
                variations = [min_v + step * i for i in range(5)]

            specs.append({
                'category': 'Level Detection',
                'subcategory': 'Settings',
                'parameter': name,
                'display_name': name.replace('_', ' ').title(),
                'current_value': current,
                'ui_tab': 'Engine Settings → Levels',
                'description': desc,
                'type': ptype,
                'min': min_v,
                'max': max_v,
                'step': step,
                'variations': variations,
            })

        # =================================================================
        # RISK MANAGEMENT (from Setup Tab)
        # =================================================================
        specs.extend([
            {
                'category': 'Risk Management',
                'subcategory': 'Per Trade',
                'parameter': 'risk_per_trade_pct',
                'display_name': 'Risk Per Trade %',
                'current_value': self.parent.parent.risk_per_trade.value() if hasattr(self.parent.parent, 'risk_per_trade') else 1.0,
                'ui_tab': 'Backtesting → Setup',
                'description': 'Prozent des Kapitals pro Trade',
                'type': 'float',
                'min': 0.1,
                'max': 10.0,
                'step': 0.5,
                'variations': [0.5, 1.0, 1.5, 2.0, 3.0],
            },
            {
                'category': 'Risk Management',
                'subcategory': 'Daily',
                'parameter': 'max_daily_loss_pct',
                'display_name': 'Max Daily Loss %',
                'current_value': self.parent.parent.max_daily_loss.value() if hasattr(self.parent.parent, 'max_daily_loss') else 3.0,
                'ui_tab': 'Backtesting → Setup',
                'description': 'Maximaler täglicher Verlust',
                'type': 'float',
                'min': 0.5,
                'max': 20.0,
                'step': 0.5,
                'variations': [2.0, 3.0, 5.0, 7.0, 10.0],
            },
            {
                'category': 'Risk Management',
                'subcategory': 'Limits',
                'parameter': 'max_trades_per_day',
                'display_name': 'Max Trades/Tag',
                'current_value': self.parent.parent.max_trades_day.value() if hasattr(self.parent.parent, 'max_trades_day') else 10,
                'ui_tab': 'Backtesting → Setup',
                'description': 'Maximale Trades pro Tag',
                'type': 'int',
                'min': 1,
                'max': 100,
                'step': 5,
                'variations': [5, 10, 15, 20, 30],
            },
        ])

        return specs
