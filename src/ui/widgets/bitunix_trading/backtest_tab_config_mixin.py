from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QMessageBox, QFileDialog, QProgressBar, QTabWidget, QLineEdit,
    QHeaderView,
)

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)


class BacktestTabConfigMixin:
    """Configuration management and parameter handling"""

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
        chart_window = self._find_chart_window()

        if not chart_window:
            logger.warning("ChartWindow nicht gefunden - verwende Default-Configs")
            return self._get_default_engine_configs()

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

        self._engine_configs = configs
        logger.info(f"Engine Configs geladen: {list(configs.keys())}")
        return configs
    def _get_default_engine_configs(self) -> Dict[str, Any]:
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
    def _build_backtest_config(self):
        """Erstellt BacktestConfig aus UI-Werten."""
        from src.core.backtesting import ReplayBacktestConfig, ExecutionConfig, SlippageMethod

        symbol = self.symbol_combo.currentText()
        start = datetime.combine(self.start_date.date().toPyDate(), datetime.min.time(), tzinfo=timezone.utc)
        end = datetime.combine(self.end_date.date().toPyDate(), datetime.max.time(), tzinfo=timezone.utc)

        # Slippage Method Mapping
        slippage_map = {
            0: SlippageMethod.FIXED_BPS,
            1: SlippageMethod.ATR_BASED,
            2: SlippageMethod.VOLUME_ADJUSTED,
        }
        slippage_method = slippage_map.get(self.slippage_method.currentIndex(), SlippageMethod.FIXED_BPS)

        # ExecutionConfig erstellen
        exec_config = ExecutionConfig(
            fee_rate_maker=self.fee_maker.value(),
            fee_rate_taker=self.fee_taker.value(),
            slippage_method=slippage_method,
            slippage_bps=self.slippage_bps.value(),
            max_leverage=self.max_leverage.value(),
            liquidation_buffer_pct=self.liq_buffer.value(),
            assume_taker=self.assume_taker.isChecked(),
        )

        # Timeframe aus UI holen
        selected_tf = self.timeframe_combo.currentText()

        # MTF Timeframes: alle höher als der ausgewählte
        all_tfs = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1D"]
        try:
            selected_idx = all_tfs.index(selected_tf)
            mtf_timeframes = all_tfs[selected_idx + 1:] if selected_idx < len(all_tfs) - 1 else ["1D"]
        except ValueError:
            mtf_timeframes = ["5m", "15m", "1h", "4h", "1D"]

        # BacktestConfig erstellen
        config = ReplayBacktestConfig(
            symbol=symbol,
            start_date=start,
            end_date=end,
            initial_capital=self.initial_capital.value(),
            base_timeframe=selected_tf,  # Nutze ausgewählten Timeframe
            mtf_timeframes=mtf_timeframes,
            execution=exec_config,
            risk_per_trade_pct=self.risk_per_trade.value(),
            max_daily_loss_pct=self.max_daily_loss.value(),
            max_trades_per_day=self.max_trades_day.value(),
        )

        return config

    def _build_entry_config(self, engine_configs: dict):
        """Build EntryScoreConfig from engine settings."""
        from src.core.trading_bot import EntryScoreConfig

        if not HAS_ENTRY_SCORE or 'entry_score' not in engine_configs:
            return None

        try:
            es = engine_configs['entry_score']
            return EntryScoreConfig(
                weight_trend_alignment=es.get('weights', {}).get('trend_alignment', 0.25),
                weight_momentum_rsi=es.get('weights', {}).get('rsi', 0.15),
                weight_momentum_macd=es.get('weights', {}).get('macd', 0.20),
                weight_trend_strength=es.get('weights', {}).get('adx', 0.15),
                weight_volatility=es.get('weights', {}).get('volatility', 0.10),
                weight_volume=es.get('weights', {}).get('volume', 0.15),
                threshold_excellent=es.get('thresholds', {}).get('excellent', 0.80),
                threshold_good=es.get('thresholds', {}).get('good', 0.65),
                threshold_moderate=es.get('thresholds', {}).get('moderate', 0.50),
                threshold_weak=es.get('thresholds', {}).get('weak', 0.35),
                min_score_for_entry=es.get('min_score_for_entry', 0.50),
                block_in_chop_range=es.get('gates', {}).get('block_in_chop', True),
                block_against_strong_trend=es.get('gates', {}).get('block_against_strong_trend', True),
                allow_counter_trend_sfp=es.get('gates', {}).get('allow_counter_trend_sfp', True),
                regime_boost_strong_trend=es.get('gates', {}).get('trend_boost', 0.10),
                regime_penalty_chop=es.get('gates', {}).get('chop_penalty', -0.15),
                regime_penalty_volatile=es.get('gates', {}).get('volatile_penalty', -0.10),
            )
        except Exception as e:
            logger.warning(f"EntryScoreConfig error: {e}")
            return None
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
        configs = self.collect_engine_configs()
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
                'current_value': self.risk_per_trade.value(),
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
                'current_value': self.max_daily_loss.value(),
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
                'current_value': self.max_trades_day.value(),
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
    def get_parameter_space_from_configs(self) -> Dict[str, list]:
        """
        Erstellt einen Parameter-Space für Batch-Tests basierend auf Engine-Configs.

        Generiert sinnvolle Variationen aller konfigurierbaren Parameter.

        Returns:
            Dict mit Parameter-Namen und möglichen Werten
        """
        configs = self.collect_engine_configs()
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
    def _convert_v2_to_parameters(self, template: dict) -> dict:
        """Konvertiert V2-Format Template zu V1-kompatiblem parameters-Dict.

        V2-Format hat verschachtelte Struktur wie:
        - entry_score.weights, entry_score.thresholds, entry_score.gates
        - exit_management.stop_loss, exit_management.take_profit
        - risk_leverage.risk_per_trade_pct, risk_leverage.base_leverage

        Args:
            template: Das V2-Format Template

        Returns:
            Dict im V1-parameters-Format für die UI-Anzeige
        """
        params = {}

        # Mapping von V2-Pfaden zu V1-Parameter-Namen und Kategorien
        v2_mappings = [
            # Entry Score - Weights
            ('entry_score.weights.use_preset', 'weight_preset', 'Entry Score', 'Weights', 'Preset für Gewichtungen'),
            # Entry Score - Thresholds
            ('entry_score.thresholds.min_score_for_entry', 'min_score_for_entry', 'Entry Score', 'Thresholds', 'Minimum Entry Score'),
            # Entry Score - Gates
            ('entry_score.gates.block_in_chop', 'block_in_chop', 'Entry Score', 'Gates', 'Im Chop-Regime blocken'),
            ('entry_score.gates.block_against_strong_trend', 'block_against_strong_trend', 'Entry Score', 'Gates', 'Gegen starken Trend blocken'),
            ('entry_score.gates.allow_counter_trend_sfp', 'allow_counter_trend_sfp', 'Entry Score', 'Gates', 'Counter-Trend SFP erlauben'),
            # Entry Score - Indicator Params
            ('entry_score.indicator_params.ema_short', 'ema_short', 'Entry Score', 'Indicators', 'EMA Short Periode'),
            ('entry_score.indicator_params.ema_medium', 'ema_medium', 'Entry Score', 'Indicators', 'EMA Medium Periode'),
            ('entry_score.indicator_params.ema_long', 'ema_long', 'Entry Score', 'Indicators', 'EMA Long Periode'),
            ('entry_score.indicator_params.rsi_period', 'rsi_period', 'Entry Score', 'Indicators', 'RSI Periode'),
            ('entry_score.indicator_params.adx_strong_trend', 'adx_strong_trend', 'Entry Score', 'Indicators', 'ADX Schwelle für starken Trend'),
            # Entry Triggers
            ('entry_triggers.breakout.enabled', 'breakout_enabled', 'Entry Triggers', 'Breakout', 'Breakout-Trigger aktiv'),
            ('entry_triggers.breakout.volume_multiplier', 'breakout_volume_multiplier', 'Entry Triggers', 'Breakout', 'Volumen-Multiplikator'),
            ('entry_triggers.pullback.enabled', 'pullback_enabled', 'Entry Triggers', 'Pullback', 'Pullback-Trigger aktiv'),
            ('entry_triggers.pullback.max_distance_atr', 'pullback_max_distance_atr', 'Entry Triggers', 'Pullback', 'Max Distanz in ATR'),
            ('entry_triggers.sfp.enabled', 'sfp_enabled', 'Entry Triggers', 'SFP', 'SFP-Trigger aktiv'),
            # Exit Management - Stop Loss
            ('exit_management.stop_loss.type', 'sl_type', 'Exit Management', 'Stop Loss', 'Stop-Loss Typ'),
            ('exit_management.stop_loss.atr_multiplier', 'sl_atr_multiplier', 'Exit Management', 'Stop Loss', 'ATR-Multiplikator für SL'),
            # Exit Management - Take Profit
            ('exit_management.take_profit.type', 'tp_type', 'Exit Management', 'Take Profit', 'Take-Profit Typ'),
            ('exit_management.take_profit.atr_multiplier', 'tp_atr_multiplier', 'Exit Management', 'Take Profit', 'ATR-Multiplikator für TP'),
            ('exit_management.take_profit.use_level', 'tp_use_level', 'Exit Management', 'Take Profit', 'Level für TP verwenden'),
            # Exit Management - Trailing Stop
            ('exit_management.trailing_stop.enabled', 'trailing_enabled', 'Exit Management', 'Trailing', 'Trailing Stop aktiv'),
            ('exit_management.trailing_stop.move_to_breakeven', 'trailing_move_to_breakeven', 'Exit Management', 'Trailing', 'Move to Breakeven'),
            ('exit_management.trailing_stop.activation_atr', 'trailing_activation_atr', 'Exit Management', 'Trailing', 'Aktivierung in ATR'),
            ('exit_management.trailing_stop.distance_atr', 'trailing_distance_atr', 'Exit Management', 'Trailing', 'Trailing-Distanz in ATR'),
            # Risk & Leverage
            ('risk_leverage.risk_per_trade_pct', 'risk_per_trade_pct', 'Risk/Leverage', 'Risk', 'Risiko pro Trade in %'),
            ('risk_leverage.base_leverage', 'base_leverage', 'Risk/Leverage', 'Leverage', 'Basis-Hebel'),
            ('risk_leverage.max_leverage', 'max_leverage', 'Risk/Leverage', 'Leverage', 'Maximaler Hebel'),
            ('risk_leverage.min_liquidation_distance_pct', 'min_liquidation_distance_pct', 'Risk/Leverage', 'Risk', 'Min. Liquidations-Distanz %'),
            ('risk_leverage.max_daily_loss_pct', 'max_daily_loss_pct', 'Risk/Leverage', 'Risk', 'Max. täglicher Verlust %'),
            ('risk_leverage.max_trades_per_day', 'max_trades_per_day', 'Risk/Leverage', 'Limits', 'Max. Trades pro Tag'),
            ('risk_leverage.max_concurrent_positions', 'max_concurrent_positions', 'Risk/Leverage', 'Limits', 'Max. gleichzeitige Positionen'),
            # Execution Simulation
            ('execution_simulation.initial_capital', 'initial_capital', 'Simulation', 'Capital', 'Startkapital'),
            ('execution_simulation.fee_maker_pct', 'fee_maker_pct', 'Simulation', 'Fees', 'Maker-Fee %'),
            ('execution_simulation.fee_taker_pct', 'fee_taker_pct', 'Simulation', 'Fees', 'Taker-Fee %'),
            ('execution_simulation.slippage_bps', 'slippage_bps', 'Simulation', 'Slippage', 'Slippage in BPS'),
            # Strategy Profile
            ('strategy_profile.type', 'strategy_type', 'Strategy', 'Profile', 'Strategie-Typ'),
            ('strategy_profile.preset', 'strategy_preset', 'Strategy', 'Profile', 'Strategie-Preset'),
            ('strategy_profile.direction_bias', 'direction_bias', 'Strategy', 'Profile', 'Richtungs-Bias'),
            # Walk Forward
            ('walk_forward.enabled', 'wf_enabled', 'Walk Forward', 'Settings', 'Walk-Forward aktiv'),
            ('walk_forward.train_window_days', 'wf_train_window_days', 'Walk Forward', 'Settings', 'Training-Fenster (Tage)'),
            ('walk_forward.test_window_days', 'wf_test_window_days', 'Walk Forward', 'Settings', 'Test-Fenster (Tage)'),
        ]

        for v2_path, param_name, category, subcategory, description in v2_mappings:
            value = self._get_nested_value(template, v2_path)
            if value is not None:
                # Extrahiere optimize und range falls vorhanden (V2-Format für optimierbare Parameter)
                if isinstance(value, dict) and 'value' in value:
                    actual_value = value.get('value')
                    variations = value.get('range', [])
                    optimize = value.get('optimize', False)
                else:
                    actual_value = value
                    variations = []
                    optimize = False

                # Bestimme Typ
                if isinstance(actual_value, bool):
                    param_type = 'bool'
                elif isinstance(actual_value, int):
                    param_type = 'int'
                elif isinstance(actual_value, float):
                    param_type = 'float'
                elif isinstance(actual_value, str):
                    param_type = 'str'
                else:
                    param_type = 'unknown'

                params[param_name] = {
                    'value': actual_value,
                    'type': param_type,
                    'category': category,
                    'subcategory': subcategory,
                    'description': description,
                    'min': None,
                    'max': None,
                    'variations': variations if variations else [actual_value] if actual_value is not None else [],
                    'optimize': optimize,
                }

        return params
    def _get_nested_value(self, data: dict, path: str):
        """Holt einen verschachtelten Wert aus einem Dict via Punkt-Notation.

        Args:
            data: Das Source-Dictionary
            path: Punkt-separierter Pfad (z.B. 'entry_score.weights.use_preset')

        Returns:
            Der Wert am Pfad oder None wenn nicht gefunden
        """
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
