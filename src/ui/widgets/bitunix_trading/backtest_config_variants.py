"""Backtest Config Variants - Indicator Sets & AI Variant Generation.

Refactored from 764 LOC monolith using composition pattern.

Module 4/4 of backtest_config_manager.py split.

Contains:
- get_available_indicator_sets(): Liefert vordefinierte Indikator-Sets
- generate_ai_test_variants(): Erstellt intelligente Test-Varianten
"""

from __future__ import annotations

from typing import Any, Dict


class BacktestConfigVariants:
    """Helper für Indicator Sets und AI Variant Generation."""

    def __init__(self, parent):
        """
        Args:
            parent: BacktestConfigManager Instanz
        """
        self.parent = parent

    def get_available_indicator_sets(self) -> list[Dict[str, Any]]:
        """
        Gibt die verfügbaren Indikator-Sets zurück.

        Returns:
            Liste von Indikator-Set Definitionen
        """
        return [
            {
                'name': 'Trend Following',
                'description': 'Fokus auf EMA-Stack, ADX, MACD für Trendfolge',
                'weights': {
                    'trend_alignment': 0.35,
                    'rsi': 0.10,
                    'macd': 0.25,
                    'adx': 0.20,
                    'volatility': 0.05,
                    'volume': 0.05,
                },
                'gates': {'block_in_chop': True, 'block_against_strong_trend': False},
            },
            {
                'name': 'Mean Reversion',
                'description': 'RSI Extremwerte, BB-Berührungen für Gegenbewegungen',
                'weights': {
                    'trend_alignment': 0.10,
                    'rsi': 0.35,
                    'macd': 0.10,
                    'adx': 0.10,
                    'volatility': 0.20,
                    'volume': 0.15,
                },
                'gates': {'block_in_chop': False, 'allow_counter_trend_sfp': True},
            },
            {
                'name': 'Breakout',
                'description': 'Level-Breaks, Volume-Spikes, Volatilitäts-Expansion',
                'weights': {
                    'trend_alignment': 0.15,
                    'rsi': 0.10,
                    'macd': 0.15,
                    'adx': 0.15,
                    'volatility': 0.20,
                    'volume': 0.25,
                },
                'level_settings': {'min_touches': 3, 'significance_threshold': 0.8},
            },
            {
                'name': 'Conservative',
                'description': 'Hohe Score-Anforderungen, niedriger Leverage',
                'weights': {
                    'trend_alignment': 0.20,
                    'rsi': 0.15,
                    'macd': 0.20,
                    'adx': 0.20,
                    'volatility': 0.10,
                    'volume': 0.15,
                },
                'min_score_for_entry': 0.70,
                'leverage': {'base_leverage': 3, 'max_leverage': 10},
            },
            {
                'name': 'Aggressive',
                'description': 'Niedrigere Score-Anforderungen, höherer Leverage',
                'weights': {
                    'trend_alignment': 0.25,
                    'rsi': 0.15,
                    'macd': 0.20,
                    'adx': 0.15,
                    'volatility': 0.10,
                    'volume': 0.15,
                },
                'min_score_for_entry': 0.40,
                'leverage': {'base_leverage': 10, 'max_leverage': 30},
            },
            {
                'name': 'Balanced (Default)',
                'description': 'Ausgewogene Gewichtung aller Faktoren',
                'weights': {
                    'trend_alignment': 0.25,
                    'rsi': 0.15,
                    'macd': 0.20,
                    'adx': 0.15,
                    'volatility': 0.10,
                    'volume': 0.15,
                },
                'min_score_for_entry': 0.50,
            },
        ]

    def generate_ai_test_variants(self, base_spec: list[Dict], num_variants: int = 10) -> list[Dict[str, Any]]:
        """
        Generiert intelligente Test-Varianten basierend auf der Parameter-Spezifikation.

        Erstellt sinnvolle Kombinationen unter Berücksichtigung von:
        - Parameter-Abhängigkeiten
        - Typische Trading-Strategien
        - Extreme vs. konservative Einstellungen

        Args:
            base_spec: Parameter-Spezifikation
            num_variants: Anzahl der zu generierenden Varianten

        Returns:
            Liste von Test-Varianten
        """
        variants = []
        indicator_sets = self.get_available_indicator_sets()

        # Variante 1-5: Basierend auf vordefinierten Indikator-Sets
        for i, ind_set in enumerate(indicator_sets[:min(5, num_variants)]):
            variant = {
                'id': f'V{i+1:02d}',
                'name': ind_set['name'],
                'description': ind_set['description'],
                'source': 'indicator_set',
                'parameters': {}
            }

            # Weights übernehmen
            for weight_name, weight_val in ind_set.get('weights', {}).items():
                variant['parameters'][f'weight_{weight_name}'] = weight_val

            # Andere Settings übernehmen
            if 'min_score_for_entry' in ind_set:
                variant['parameters']['min_score_for_entry'] = ind_set['min_score_for_entry']
            if 'gates' in ind_set:
                for gate_name, gate_val in ind_set['gates'].items():
                    variant['parameters'][f'gate_{gate_name}'] = gate_val
            if 'leverage' in ind_set:
                for lev_name, lev_val in ind_set['leverage'].items():
                    variant['parameters'][lev_name] = lev_val
            if 'level_settings' in ind_set:
                for lvl_name, lvl_val in ind_set['level_settings'].items():
                    variant['parameters'][lvl_name] = lvl_val

            variants.append(variant)

        # Variante 6+: Algorithmisch generierte Varianten
        import random
        remaining = num_variants - len(variants)

        strategy_types = ['trend_focused', 'momentum_focused', 'risk_averse', 'aggressive', 'balanced']

        for i in range(remaining):
            strategy = strategy_types[i % len(strategy_types)]
            variant = {
                'id': f'V{len(variants)+1:02d}',
                'name': f'Auto-{strategy.replace("_", " ").title()}',
                'description': f'Automatisch generiert: {strategy}',
                'source': 'auto_generated',
                'parameters': {}
            }

            # Generiere Parameter basierend auf Strategie-Typ
            if strategy == 'trend_focused':
                variant['parameters'] = {
                    'weight_trend_alignment': random.uniform(0.30, 0.40),
                    'weight_adx': random.uniform(0.20, 0.25),
                    'weight_macd': random.uniform(0.15, 0.25),
                    'min_score_for_entry': random.uniform(0.55, 0.65),
                    'gate_block_in_chop': True,
                }
            elif strategy == 'momentum_focused':
                variant['parameters'] = {
                    'weight_rsi': random.uniform(0.25, 0.35),
                    'weight_macd': random.uniform(0.25, 0.30),
                    'min_score_for_entry': random.uniform(0.45, 0.55),
                    'tp_atr_multiplier': random.uniform(2.5, 3.5),
                }
            elif strategy == 'risk_averse':
                variant['parameters'] = {
                    'min_score_for_entry': random.uniform(0.65, 0.75),
                    'risk_per_trade_pct': random.uniform(0.5, 1.0),
                    'base_leverage': random.randint(2, 5),
                    'max_leverage': random.randint(5, 10),
                    'sl_atr_multiplier': random.uniform(1.0, 1.5),
                }
            elif strategy == 'aggressive':
                variant['parameters'] = {
                    'min_score_for_entry': random.uniform(0.35, 0.45),
                    'risk_per_trade_pct': random.uniform(2.0, 3.0),
                    'base_leverage': random.randint(10, 20),
                    'max_leverage': random.randint(20, 40),
                    'tp_atr_multiplier': random.uniform(3.0, 4.0),
                }
            else:  # balanced
                variant['parameters'] = {
                    'weight_trend_alignment': random.uniform(0.20, 0.30),
                    'weight_rsi': random.uniform(0.12, 0.18),
                    'weight_macd': random.uniform(0.18, 0.22),
                    'min_score_for_entry': random.uniform(0.48, 0.55),
                    'risk_per_trade_pct': random.uniform(1.0, 1.5),
                }

            # Runde Werte
            for key, val in variant['parameters'].items():
                if isinstance(val, float):
                    variant['parameters'][key] = round(val, 2)

            variants.append(variant)

        return variants
