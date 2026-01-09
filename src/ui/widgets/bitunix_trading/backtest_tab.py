"""
Backtest Tab - UI Widget für Backtesting im Trading Bot Fenster

Integriert die Backtesting-Funktionalität in das Trading Bot Panel (ChartWindow).

Features:
- Datenauswahl (Symbol, Zeitraum)
- Single Run Backtest
- Batch-Tests (Grid/Random Search)
- Walk-Forward Analyse
- Ergebnis-Dashboard (Equity, KPIs, Trades)
- Export-Funktionen
- **Engine Settings Integration**: Verwendet Configs aus allen Engine Tabs

Sub-Tabs:
1. Setup: Datenquelle, Symbol, Zeitraum, Strategy
2. Execution: Fees, Slippage, Leverage Settings
3. Results: Equity Curve, Metriken, Trade-Liste
4. Batch/WF: Batch-Tests und Walk-Forward

Engine Config Integration:
- EntryScoreConfig (Entry Score Tab)
- TriggerExitConfig (Trigger/Exit Tab)
- LeverageRulesConfig (Leverage Tab)
- LLMValidationConfig (LLM Validation Tab)
- LevelEngineConfig (Level Detection Tab)
- RegimeConfig (Regime Detection)
"""

from __future__ import annotations

print(">>> BACKTEST_TAB.PY LOADED (2026-01-09 FIX) <<<", flush=True)

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Callable

import qasync
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QThread
from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QFrame,
    QProgressBar,
    QSplitter,
    QHeaderView,
    QDateEdit,
    QTabWidget,
    QLineEdit,
    QScrollArea,
    QFileDialog,
)

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)


class BatchTestWorker(QThread):
    """Worker thread to run batch tests without blocking the UI."""

    progress = pyqtSignal(int, str)
    log = pyqtSignal(str)
    finished = pyqtSignal(object, list)
    error = pyqtSignal(str)

    def __init__(
        self,
        batch_config,
        *,
        signal_callback: Callable | None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._batch_config = batch_config
        self._signal_callback = signal_callback

    def run(self) -> None:
        try:
            self.log.emit("🧵 Batch-Worker gestartet (separater Thread)")
            from src.core.backtesting import BatchRunner

            runner = BatchRunner(
                self._batch_config,
                signal_callback=self._signal_callback,
            )
            runner.set_progress_callback(lambda p, m: self.progress.emit(p, m))

            summary = asyncio.run(runner.run())
            self.finished.emit(summary, runner.results)
        except Exception as exc:
            logger.exception("Batch worker failed")
            self.error.emit(str(exc))

# =============================================================================
# ENGINE CONFIG IMPORTS
# =============================================================================

try:
    from src.core.trading_bot import (
        EntryScoreConfig,
        get_entry_score_engine,
    )
    HAS_ENTRY_SCORE = True
except ImportError:
    HAS_ENTRY_SCORE = False
    logger.debug("EntryScoreConfig not available")

try:
    from src.core.trading_bot.trigger_exit_engine import TriggerExitConfig
    HAS_TRIGGER_EXIT = True
except ImportError:
    HAS_TRIGGER_EXIT = False
    logger.debug("TriggerExitConfig not available")

try:
    from src.core.trading_bot.leverage_rules import LeverageRulesConfig
    HAS_LEVERAGE = True
except ImportError:
    HAS_LEVERAGE = False
    logger.debug("LeverageRulesConfig not available")

try:
    from src.core.trading_bot.llm_validation_service import LLMValidationConfig
    HAS_LLM = True
except ImportError:
    HAS_LLM = False
    logger.debug("LLMValidationConfig not available")

try:
    from src.core.trading_bot.level_engine import LevelEngineConfig
    HAS_LEVELS = True
except ImportError:
    HAS_LEVELS = False
    logger.debug("LevelEngineConfig not available")

try:
    from src.core.trading_bot.regime_detector import RegimeConfig
    HAS_REGIME = True
except ImportError:
    HAS_REGIME = False
    logger.debug("RegimeConfig not available")

# Settings Path
BACKTEST_SETTINGS_FILE = Path("config/backtest_settings.json")


class BacktestTab(QWidget):
    """
    Backtest Tab - UI für historisches Strategietesting.

    Bietet:
    - Setup Panel (Symbol, Zeitraum, Strategy)
    - Execution Settings (Fees, Slippage, Leverage)
    - Ergebnis-Dashboard
    - Batch/Walk-Forward Tests
    """

    # Signals
    backtest_started = pyqtSignal()
    backtest_finished = pyqtSignal(object)  # BacktestResult
    progress_updated = pyqtSignal(int, str)  # progress_pct, message
    log_message = pyqtSignal(str)

    def __init__(
        self,
        history_manager: "HistoryManager | None" = None,
        parent: QWidget | None = None,
    ):
        """
        Args:
            history_manager: History Manager für Datenzugriff
            parent: Parent Widget
        """
        super().__init__(parent)

        self._history_manager = history_manager
        self._is_running = False
        self._current_result = None
        self._current_runner = None
        self._batch_worker: BatchTestWorker | None = None

        # Engine configs (collected from Engine Settings tabs)
        self._engine_configs: Dict[str, Any] = {}

        self._setup_ui()
        self._connect_signals()
        self._load_settings()

    # =========================================================================
    # ENGINE CONFIG COLLECTION
    # =========================================================================

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

    def _find_chart_window(self) -> Optional[QWidget]:
        """
        Sucht das ChartWindow in der Parent-Hierarchie.

        Returns:
            ChartWindow Widget oder None
        """
        widget = self.parent()
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

    def set_history_manager(self, history_manager: "HistoryManager") -> None:
        """Setzt den History Manager."""
        self._history_manager = history_manager

    def _setup_ui(self) -> None:
        """Erstellt das UI Layout."""
        # === COMPACT STYLESHEET für kleinere UI-Elemente ===
        self.setStyleSheet("""
            QGroupBox {
                font-size: 10px;
                font-weight: bold;
                padding-top: 12px;
                margin-top: 4px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
            }
            QLabel {
                font-size: 10px;
            }
            QPushButton {
                font-size: 10px;
                padding: 3px 8px;
                min-height: 20px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QLineEdit {
                font-size: 10px;
                min-height: 20px;
                max-height: 22px;
            }
            QTableWidget {
                font-size: 9px;
            }
            QTableWidget::item {
                padding: 2px;
            }
            QHeaderView::section {
                font-size: 9px;
                padding: 2px 4px;
                min-height: 18px;
            }
            QCheckBox {
                font-size: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # --- Kompakte Button-Leiste (alle Buttons in einer Zeile) ---
        button_row = self._create_compact_button_row()
        layout.addLayout(button_row)

        # --- Sub-Tabs ---
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2a2a2a;
                color: #888;
                padding: 6px 12px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #1a1a2e;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #333;
            }
        """)

        # Tab 1: Setup
        self.sub_tabs.addTab(self._create_setup_tab(), "📁 Setup")

        # Tab 2: Execution Settings
        self.sub_tabs.addTab(self._create_execution_tab(), "⚙️ Execution")

        # Tab 3: Results
        self.sub_tabs.addTab(self._create_results_tab(), "📊 Results")

        # Tab 4: Batch/Walk-Forward
        self.sub_tabs.addTab(self._create_batch_tab(), "🔄 Batch/WF")

        layout.addWidget(self.sub_tabs)

        # --- Log Section ---
        log_group = QGroupBox("📜 Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #aaa;
                font-family: monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)

    def _create_compact_button_row(self) -> QVBoxLayout:
        """Erstellt kompakte Button-Zeilen (2 Reihen für bessere Sichtbarkeit)."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # === ZEILE 1: Status + Hauptaktionen ===
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        # Status Icon + Label
        self.status_icon = QLabel("🧪")
        self.status_icon.setStyleSheet("font-size: 16px;")
        row1.addWidget(self.status_icon)

        self.status_label = QLabel("IDLE")
        self.status_label.setStyleSheet("font-size: 11px; font-weight: bold; color: #888;")
        row1.addWidget(self.status_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(100)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #222;
                text-align: center;
                color: white;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        row1.addWidget(self.progress_bar)

        row1.addSpacing(8)

        # === START BUTTON (grün, prominent) ===
        self.start_btn = QPushButton("▶ Start Backtest")
        self.start_btn.setMinimumWidth(110)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.start_btn.clicked.connect(self._on_start_btn_clicked)
        row1.addWidget(self.start_btn)

        # Stop Button
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setMinimumWidth(60)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 6px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        row1.addWidget(self.stop_btn)

        row1.addStretch()

        # Status Detail
        self.status_detail = QLabel("Bereit")
        self.status_detail.setStyleSheet("color: #666; font-size: 10px;")
        row1.addWidget(self.status_detail)

        main_layout.addLayout(row1)

        # === ZEILE 2: Config + Tools ===
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        # Load Engine Configs Button (GRÖSSER)
        self.load_config_btn = QPushButton("📥 Engine Configs laden")
        self.load_config_btn.setMinimumWidth(140)
        self.load_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 5px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.load_config_btn.setToolTip("Lädt alle Engine-Konfigurationen in die Config-Tabelle")
        self.load_config_btn.clicked.connect(self._on_load_configs_clicked)
        row2.addWidget(self.load_config_btn)

        # Auto-Generate Button
        self.auto_gen_btn = QPushButton("🤖 Auto-Generate")
        self.auto_gen_btn.setMinimumWidth(110)
        self.auto_gen_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.auto_gen_btn.setToolTip("Generiert automatisch Test-Varianten")
        self.auto_gen_btn.clicked.connect(self._on_auto_generate_clicked)
        row2.addWidget(self.auto_gen_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #444;")
        row2.addWidget(sep)

        # Template Buttons
        self.save_template_btn = QPushButton("💾 Save")
        self.save_template_btn.setMinimumWidth(60)
        self.save_template_btn.setToolTip("Template speichern")
        self.save_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.save_template_btn.clicked.connect(self._on_save_template_clicked)
        row2.addWidget(self.save_template_btn)

        self.load_template_btn = QPushButton("📂 Load")
        self.load_template_btn.setMinimumWidth(60)
        self.load_template_btn.setToolTip("Template laden")
        self.load_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.load_template_btn.clicked.connect(self._on_load_template_clicked)
        row2.addWidget(self.load_template_btn)

        self.derive_variant_btn = QPushButton("📝 Variant")
        self.derive_variant_btn.setMinimumWidth(65)
        self.derive_variant_btn.setToolTip("Variante ableiten")
        self.derive_variant_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                padding: 5px 8px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.derive_variant_btn.clicked.connect(self._on_derive_variant_clicked)
        row2.addWidget(self.derive_variant_btn)

        row2.addStretch()

        main_layout.addLayout(row2)

        return main_layout

    def _create_setup_tab(self) -> QWidget:
        """Erstellt Setup Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Datenquelle ---
        data_group = QGroupBox("📁 Datenquelle")
        data_layout = QFormLayout(data_group)

        self.symbol_combo = QComboBox()
        self.symbol_combo.setEditable(True)
        self.symbol_combo.addItems([
            "bitunix:BTCUSDT",
            "bitunix:ETHUSDT",
            "bitunix:SOLUSDT",
            "alpaca:BTC/USD",
            "alpaca:ETH/USD",
        ])
        data_layout.addRow("Symbol:", self.symbol_combo)

        # Timeframe
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems([
            "1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "1D"
        ])
        self.timeframe_combo.setCurrentText("5m")  # Default für Daytrading
        data_layout.addRow("Timeframe:", self.timeframe_combo)

        # Zeitraum
        date_layout = QHBoxLayout()
        self.start_date = QDateEdit()
        self.start_date.setDate(datetime.now().date() - timedelta(days=90))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("Von:"))
        date_layout.addWidget(self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDate(datetime.now().date())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(QLabel("Bis:"))
        date_layout.addWidget(self.end_date)

        data_layout.addRow("Zeitraum:", date_layout)

        # Quick-Select Buttons
        quick_layout = QHBoxLayout()
        for days, label in [(7, "1W"), (30, "1M"), (90, "3M"), (180, "6M"), (365, "1Y")]:
            btn = QPushButton(label)
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, d=days: self._set_date_range(d))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        data_layout.addRow("", quick_layout)

        layout.addWidget(data_group)

        # --- Strategy ---
        strategy_group = QGroupBox("🎯 Strategy")
        strategy_layout = QFormLayout(strategy_group)

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "Default (Confluence-Based)",
            "Trend Following",
            "Mean Reversion",
            "Breakout",
            "Custom...",
        ])
        strategy_layout.addRow("Strategy:", self.strategy_combo)

        self.initial_capital = QDoubleSpinBox()
        self.initial_capital.setRange(100, 10_000_000)
        self.initial_capital.setValue(10_000)
        self.initial_capital.setPrefix("$ ")
        self.initial_capital.setSingleStep(1000)
        strategy_layout.addRow("Startkapital:", self.initial_capital)

        layout.addWidget(strategy_group)

        # --- Risk Settings ---
        risk_group = QGroupBox("⚠️ Risk Management")
        risk_layout = QFormLayout(risk_group)

        self.risk_per_trade = QDoubleSpinBox()
        self.risk_per_trade.setRange(0.1, 10)
        self.risk_per_trade.setValue(1.0)
        self.risk_per_trade.setSuffix(" %")
        self.risk_per_trade.setSingleStep(0.5)
        risk_layout.addRow("Risiko/Trade:", self.risk_per_trade)

        self.max_daily_loss = QDoubleSpinBox()
        self.max_daily_loss.setRange(0.5, 20)
        self.max_daily_loss.setValue(3.0)
        self.max_daily_loss.setSuffix(" %")
        risk_layout.addRow("Max Daily Loss:", self.max_daily_loss)

        self.max_trades_day = QSpinBox()
        self.max_trades_day.setRange(1, 100)
        self.max_trades_day.setValue(10)
        risk_layout.addRow("Max Trades/Tag:", self.max_trades_day)

        layout.addWidget(risk_group)

        layout.addStretch()
        return widget

    def _create_execution_tab(self) -> QWidget:
        """Erstellt Execution Settings Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- Fees ---
        fee_group = QGroupBox("💰 Gebühren")
        fee_layout = QFormLayout(fee_group)

        self.fee_maker = QDoubleSpinBox()
        self.fee_maker.setRange(0, 1)
        self.fee_maker.setValue(0.02)
        self.fee_maker.setDecimals(3)
        self.fee_maker.setSuffix(" %")
        fee_layout.addRow("Maker Fee:", self.fee_maker)

        self.fee_taker = QDoubleSpinBox()
        self.fee_taker.setRange(0, 1)
        self.fee_taker.setValue(0.06)
        self.fee_taker.setDecimals(3)
        self.fee_taker.setSuffix(" %")
        fee_layout.addRow("Taker Fee:", self.fee_taker)

        layout.addWidget(fee_group)

        # --- Slippage ---
        slip_group = QGroupBox("📉 Slippage")
        slip_layout = QFormLayout(slip_group)

        self.slippage_method = QComboBox()
        self.slippage_method.addItems(["Fixed BPS", "ATR-Based", "Volume-Adjusted"])
        slip_layout.addRow("Methode:", self.slippage_method)

        self.slippage_bps = QDoubleSpinBox()
        self.slippage_bps.setRange(0, 100)
        self.slippage_bps.setValue(5)
        self.slippage_bps.setSuffix(" bps")
        slip_layout.addRow("Slippage:", self.slippage_bps)

        layout.addWidget(slip_group)

        # --- Leverage ---
        lev_group = QGroupBox("📈 Leverage")
        lev_layout = QFormLayout(lev_group)

        self.max_leverage = QSpinBox()
        self.max_leverage.setRange(1, 125)
        self.max_leverage.setValue(20)
        self.max_leverage.setSuffix("x")
        lev_layout.addRow("Max Leverage:", self.max_leverage)

        self.liq_buffer = QDoubleSpinBox()
        self.liq_buffer.setRange(0, 50)
        self.liq_buffer.setValue(5)
        self.liq_buffer.setSuffix(" %")
        lev_layout.addRow("Liquidation Buffer:", self.liq_buffer)

        layout.addWidget(lev_group)

        # --- Advanced ---
        adv_group = QGroupBox("🔧 Erweitert")
        adv_layout = QFormLayout(adv_group)

        self.assume_taker = QCheckBox()
        self.assume_taker.setChecked(True)
        adv_layout.addRow("Market = Taker:", self.assume_taker)

        self.include_funding = QCheckBox()
        self.include_funding.setChecked(False)
        adv_layout.addRow("Funding Rates:", self.include_funding)

        layout.addWidget(adv_group)

        layout.addStretch()
        return widget

    def _create_results_tab(self) -> QWidget:
        """Erstellt Results Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- KPI Cards ---
        kpi_layout = QHBoxLayout()

        self.kpi_pnl = self._create_kpi_card("💰 P&L", "—", "#4CAF50")
        kpi_layout.addWidget(self.kpi_pnl)

        self.kpi_winrate = self._create_kpi_card("🎯 Win Rate", "—", "#2196F3")
        kpi_layout.addWidget(self.kpi_winrate)

        self.kpi_pf = self._create_kpi_card("📊 Profit Factor", "—", "#FF9800")
        kpi_layout.addWidget(self.kpi_pf)

        self.kpi_dd = self._create_kpi_card("📉 Max DD", "—", "#f44336")
        kpi_layout.addWidget(self.kpi_dd)

        layout.addLayout(kpi_layout)

        # --- Equity Curve Chart ---
        equity_group = QGroupBox("📈 Equity Curve")
        equity_layout = QVBoxLayout(equity_group)

        try:
            from src.ui.widgets.equity_curve_widget import EquityCurveWidget
            self.equity_chart = EquityCurveWidget()
            self.equity_chart.setMinimumHeight(200)
            self.equity_chart.setMaximumHeight(300)
            equity_layout.addWidget(self.equity_chart)
        except ImportError as e:
            logger.warning(f"EquityCurveWidget not available: {e}")
            self.equity_chart = None
            placeholder = QLabel("Equity Chart nicht verfügbar")
            placeholder.setStyleSheet("color: #666;")
            equity_layout.addWidget(placeholder)

        layout.addWidget(equity_group)

        # --- Splitter für Metrics und Trades ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Metrics Table ---
        metrics_widget = QWidget()
        metrics_layout_inner = QVBoxLayout(metrics_widget)
        metrics_layout_inner.setContentsMargins(0, 0, 0, 0)

        metrics_label = QLabel("📊 Detaillierte Metriken")
        metrics_label.setStyleSheet("font-weight: bold; color: #aaa;")
        metrics_layout_inner.addWidget(metrics_label)

        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metrik", "Wert"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.setMaximumHeight(180)
        metrics_layout_inner.addWidget(self.metrics_table)

        splitter.addWidget(metrics_widget)

        # --- Trades Table ---
        trades_widget = QWidget()
        trades_layout_inner = QVBoxLayout(trades_widget)
        trades_layout_inner.setContentsMargins(0, 0, 0, 0)

        trades_header = QHBoxLayout()
        trades_label = QLabel("📋 Trades")
        trades_label.setStyleSheet("font-weight: bold; color: #aaa;")
        trades_header.addWidget(trades_label)

        trades_header.addStretch()

        self.export_csv_btn = QPushButton("📄 Trades CSV")
        self.export_csv_btn.setMaximumWidth(80)
        self.export_csv_btn.clicked.connect(self._export_csv)
        trades_header.addWidget(self.export_csv_btn)

        self.export_equity_btn = QPushButton("📈 Equity CSV")
        self.export_equity_btn.setMaximumWidth(80)
        self.export_equity_btn.clicked.connect(self._export_equity_csv)
        trades_header.addWidget(self.export_equity_btn)

        self.export_json_btn = QPushButton("📋 JSON")
        self.export_json_btn.setMaximumWidth(60)
        self.export_json_btn.clicked.connect(self._export_json)
        trades_header.addWidget(self.export_json_btn)

        trades_layout_inner.addLayout(trades_header)

        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(8)
        self.trades_table.setHorizontalHeaderLabels([
            "ID", "Symbol", "Side", "Entry", "Exit", "Size", "P&L", "R-Mult"
        ])
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        trades_layout_inner.addWidget(self.trades_table)

        splitter.addWidget(trades_widget)

        # --- Regime/Setup Breakdown Table ---
        breakdown_widget = QWidget()
        breakdown_layout = QVBoxLayout(breakdown_widget)
        breakdown_layout.setContentsMargins(0, 0, 0, 0)

        breakdown_label = QLabel("🎯 Regime/Setup Breakdown")
        breakdown_label.setStyleSheet("font-weight: bold; color: #aaa;")
        breakdown_layout.addWidget(breakdown_label)

        self.breakdown_table = QTableWidget()
        self.breakdown_table.setColumnCount(7)
        self.breakdown_table.setHorizontalHeaderLabels([
            "Regime/Setup", "Trades", "Win Rate", "Avg P&L", "Profit Factor", "Expectancy", "Anteil"
        ])
        self.breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.breakdown_table.setMaximumHeight(150)
        breakdown_layout.addWidget(self.breakdown_table)

        splitter.addWidget(breakdown_widget)

        layout.addWidget(splitter)

        return widget

    def _create_batch_tab(self) -> QWidget:
        """Erstellt Batch/Walk-Forward Tab mit Config Inspector."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)

        # --- Config Inspector Table (Read-Only Basistabelle) ---
        # Header Label
        config_label = QLabel("🔧 Parameter aus Engine Settings (Buttons oben in der Toolbar)")
        config_label.setStyleSheet("font-weight: bold; color: #666; font-size: 10px; margin-bottom: 4px;")
        layout.addWidget(config_label)

        # Table ---
        self.config_inspector_table = QTableWidget()
        self.config_inspector_table.setColumnCount(8)
        self.config_inspector_table.setHorizontalHeaderLabels([
            "Kategorie", "Parameter", "Wert", "UI-Tab", "Beschreibung", "Typ", "Min/Max", "Variationen"
        ])
        self.config_inspector_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.config_inspector_table.horizontalHeader().setStretchLastSection(True)
        self.config_inspector_table.setMaximumHeight(180)
        self.config_inspector_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only!
        self.config_inspector_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.config_inspector_table.setStyleSheet("""
            QTableWidget {
                font-size: 10px;
                background-color: #1a1a2e;
            }
            QTableWidget::item {
                padding: 2px;
            }
            QTableWidget::item:selected {
                background-color: #2a3a5e;
            }
            QHeaderView::section {
                background-color: #2a2a4a;
                color: #aaa;
                font-weight: bold;
                padding: 4px;
                border: 1px solid #333;
            }
        """)
        layout.addWidget(self.config_inspector_table)

        # --- Indicator Sets Quick-Select ---
        ind_set_layout = QHBoxLayout()
        ind_set_label = QLabel("📊 Indikator-Set:")
        ind_set_label.setStyleSheet("color: #888;")
        ind_set_layout.addWidget(ind_set_label)

        self.indicator_set_combo = QComboBox()
        self.indicator_set_combo.addItems([
            "-- Manuell --",
            "Trend Following",
            "Mean Reversion",
            "Breakout",
            "Conservative",
            "Aggressive",
            "Balanced (Default)",
        ])
        self.indicator_set_combo.setCurrentIndex(0)
        self.indicator_set_combo.currentIndexChanged.connect(self._on_indicator_set_changed)
        ind_set_layout.addWidget(self.indicator_set_combo)

        ind_set_layout.addStretch()
        layout.addLayout(ind_set_layout)

        # --- Batch & Walk-Forward nebeneinander ---
        batch_wf_row = QHBoxLayout()
        batch_wf_row.setSpacing(8)

        # --- Batch Settings (links) ---
        batch_group = QGroupBox("🔄 Batch Testing")
        batch_group.setMaximumHeight(150)  # Issue #36: Höhe begrenzen für Log-Sichtbarkeit
        batch_layout = QFormLayout(batch_group)
        batch_layout.setContentsMargins(6, 6, 6, 6)
        batch_layout.setSpacing(4)

        self.batch_method = QComboBox()
        self.batch_method.addItems(["Grid Search", "Random Search", "Bayesian (Optuna)"])
        batch_layout.addRow("Methode:", self.batch_method)

        self.batch_iterations = QSpinBox()
        self.batch_iterations.setRange(1, 1000)
        self.batch_iterations.setValue(50)
        batch_layout.addRow("Max Iterationen:", self.batch_iterations)

        self.batch_target = QComboBox()
        self.batch_target.addItems(["Expectancy", "Profit Factor", "Sharpe Ratio", "Min Drawdown"])
        batch_layout.addRow("Zielmetrik:", self.batch_target)

        # Parameter Space (simplified)
        self.param_space_text = QTextEdit()
        self.param_space_text.setMaximumHeight(40)  # Issue #36: Reduziert für mehr Platz
        self.param_space_text.setPlaceholderText(
            '{"risk_per_trade": [0.5, 1.0, 1.5, 2.0]}'
        )
        batch_layout.addRow("Params:", self.param_space_text)

        batch_wf_row.addWidget(batch_group)

        # --- Walk-Forward (rechts) ---
        wf_group = QGroupBox("🚶 Walk-Forward Analyse")
        wf_group.setMaximumHeight(150)  # Issue #36: Höhe begrenzen für Log-Sichtbarkeit
        wf_layout = QFormLayout(wf_group)
        wf_layout.setContentsMargins(6, 6, 6, 6)
        wf_layout.setSpacing(4)

        self.wf_train_days = QSpinBox()
        self.wf_train_days.setRange(7, 365)
        self.wf_train_days.setValue(90)
        self.wf_train_days.setSuffix(" Tage")
        wf_layout.addRow("Training:", self.wf_train_days)

        self.wf_test_days = QSpinBox()
        self.wf_test_days.setRange(7, 180)
        self.wf_test_days.setValue(30)
        self.wf_test_days.setSuffix(" Tage")
        wf_layout.addRow("Test:", self.wf_test_days)

        self.wf_step_days = QSpinBox()
        self.wf_step_days.setRange(7, 90)
        self.wf_step_days.setValue(30)
        self.wf_step_days.setSuffix(" Tage")
        wf_layout.addRow("Step:", self.wf_step_days)

        self.wf_reoptimize = QCheckBox()
        self.wf_reoptimize.setChecked(True)
        wf_layout.addRow("Re-Optimize:", self.wf_reoptimize)

        batch_wf_row.addWidget(wf_group)

        layout.addLayout(batch_wf_row)

        # --- Batch/WF Buttons ---
        btn_layout = QHBoxLayout()

        self.run_batch_btn = QPushButton("🔄 Run Batch Test")
        self.run_batch_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.run_batch_btn.clicked.connect(self._on_batch_btn_clicked)
        btn_layout.addWidget(self.run_batch_btn)

        self.run_wf_btn = QPushButton("🚶 Run Walk-Forward")
        self.run_wf_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.run_wf_btn.clicked.connect(self._on_wf_btn_clicked)
        btn_layout.addWidget(self.run_wf_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # --- Results Summary ---
        results_group = QGroupBox("📊 Batch/WF Ergebnisse")
        results_layout = QVBoxLayout(results_group)

        self.batch_results_table = QTableWidget()
        self.batch_results_table.setColumnCount(5)
        self.batch_results_table.setHorizontalHeaderLabels([
            "Run", "Parameters", "P&L", "Expectancy", "Max DD"
        ])
        self.batch_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.batch_results_table)

        # Issue #35: Removed addStretch() to make UI more compact
        layout.addWidget(results_group, stretch=1)  # Let results table expand

        return widget

    def _create_kpi_card(self, title: str, value: str, color: str) -> QFrame:
        """Erstellt eine KPI-Karte."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #1a1a2e;
                border-radius: 8px;
                border-left: 4px solid {color};
                padding: 8px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("kpi_value")
        value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        layout.addWidget(value_label)

        return card

    def _connect_signals(self) -> None:
        """Verbindet Signals und Slots."""
        self.progress_updated.connect(self._on_progress_updated)
        self.log_message.connect(self._on_log_message)
        self.backtest_finished.connect(self._on_backtest_finished)

    def _set_date_range(self, days: int) -> None:
        """Setzt den Datumsbereich."""
        end = datetime.now().date()
        start = end - timedelta(days=days)
        self.start_date.setDate(start)
        self.end_date.setDate(end)

    def _load_settings(self) -> None:
        """Lädt gespeicherte Einstellungen aus JSON und QSettings."""
        try:
            # Versuche zuerst JSON-Datei
            if BACKTEST_SETTINGS_FILE.exists():
                with open(BACKTEST_SETTINGS_FILE, "r") as f:
                    settings = json.load(f)

                # Setup Tab Settings
                if "symbol" in settings:
                    self.symbol_combo.setCurrentText(settings["symbol"])
                if "initial_capital" in settings:
                    self.initial_capital.setValue(settings["initial_capital"])
                if "risk_per_trade" in settings:
                    self.risk_per_trade.setValue(settings["risk_per_trade"])
                if "max_daily_loss" in settings:
                    self.max_daily_loss.setValue(settings["max_daily_loss"])
                if "max_trades_day" in settings:
                    self.max_trades_day.setValue(settings["max_trades_day"])

                # Execution Tab Settings
                if "fee_maker" in settings:
                    self.fee_maker.setValue(settings["fee_maker"])
                if "fee_taker" in settings:
                    self.fee_taker.setValue(settings["fee_taker"])
                if "slippage_bps" in settings:
                    self.slippage_bps.setValue(settings["slippage_bps"])
                if "slippage_method" in settings:
                    self.slippage_method.setCurrentIndex(settings["slippage_method"])
                if "max_leverage" in settings:
                    self.max_leverage.setValue(settings["max_leverage"])
                if "liq_buffer" in settings:
                    self.liq_buffer.setValue(settings["liq_buffer"])
                if "assume_taker" in settings:
                    self.assume_taker.setChecked(settings["assume_taker"])

                # Batch/WF Tab Settings
                if "batch_method" in settings:
                    self.batch_method.setCurrentIndex(settings["batch_method"])
                if "batch_iterations" in settings:
                    self.batch_iterations.setValue(settings["batch_iterations"])
                if "batch_target" in settings:
                    self.batch_target.setCurrentIndex(settings["batch_target"])
                if "wf_train_days" in settings:
                    self.wf_train_days.setValue(settings["wf_train_days"])
                if "wf_test_days" in settings:
                    self.wf_test_days.setValue(settings["wf_test_days"])
                if "wf_step_days" in settings:
                    self.wf_step_days.setValue(settings["wf_step_days"])
                if "wf_reoptimize" in settings:
                    self.wf_reoptimize.setChecked(settings["wf_reoptimize"])

                logger.info("Backtest settings loaded from JSON")

            # Fallback: QSettings
            else:
                from PyQt6.QtCore import QSettings
                qsettings = QSettings("OrderPilot-AI", "BacktestTab")

                if qsettings.contains("initial_capital"):
                    self.initial_capital.setValue(qsettings.value("initial_capital", 10000, type=float))
                if qsettings.contains("risk_per_trade"):
                    self.risk_per_trade.setValue(qsettings.value("risk_per_trade", 1.0, type=float))

                logger.info("Backtest settings loaded from QSettings")

        except Exception as e:
            logger.warning(f"Could not load backtest settings: {e}")

    def _save_settings(self) -> None:
        """Speichert alle Einstellungen in JSON und QSettings."""
        try:
            BACKTEST_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

            settings = {
                # Setup Tab
                "symbol": self.symbol_combo.currentText(),
                "initial_capital": self.initial_capital.value(),
                "risk_per_trade": self.risk_per_trade.value(),
                "max_daily_loss": self.max_daily_loss.value(),
                "max_trades_day": self.max_trades_day.value(),

                # Execution Tab
                "fee_maker": self.fee_maker.value(),
                "fee_taker": self.fee_taker.value(),
                "slippage_bps": self.slippage_bps.value(),
                "slippage_method": self.slippage_method.currentIndex(),
                "max_leverage": self.max_leverage.value(),
                "liq_buffer": self.liq_buffer.value(),
                "assume_taker": self.assume_taker.isChecked(),

                # Batch/WF Tab
                "batch_method": self.batch_method.currentIndex(),
                "batch_iterations": self.batch_iterations.value(),
                "batch_target": self.batch_target.currentIndex(),
                "wf_train_days": self.wf_train_days.value(),
                "wf_test_days": self.wf_test_days.value(),
                "wf_step_days": self.wf_step_days.value(),
                "wf_reoptimize": self.wf_reoptimize.isChecked(),
            }

            # Speichere als JSON
            with open(BACKTEST_SETTINGS_FILE, "w") as f:
                json.dump(settings, f, indent=2)

            # Backup in QSettings
            from PyQt6.QtCore import QSettings
            qsettings = QSettings("OrderPilot-AI", "BacktestTab")
            for key, value in settings.items():
                qsettings.setValue(key, value)
            qsettings.sync()

            logger.info("Backtest settings saved to JSON and QSettings")

        except Exception as e:
            logger.warning(f"Could not save backtest settings: {e}")

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

    @pyqtSlot()
    def _on_start_btn_clicked(self) -> None:
        """Synchroner Button-Handler, startet async Backtest."""
        logger.info("🚀 _on_start_btn_clicked() - scheduling async backtest")
        self._log("🚀 Backtest wird gestartet...")

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._on_start_clicked())
            else:
                logger.warning("Event loop not running, trying qasync")
                asyncio.ensure_future(self._on_start_clicked())
        except Exception as e:
            logger.exception(f"Failed to schedule backtest: {e}")
            self._log(f"❌ Fehler beim Starten des Backtests: {e}")

    async def _on_start_clicked(self) -> None:
        """Startet den Backtest (async)."""
        logger.info("🚀 _on_start_clicked() called")

        if self._is_running:
            logger.info("Already running, returning")
            return

        self._is_running = True
        self._current_runner = None
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("RUNNING")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
        self.status_detail.setText("Backtest läuft...")
        self.progress_bar.setValue(0)

        self._save_settings()
        self._log("🚀 Backtest läuft...")

        try:
            # Build config from UI
            config = self._build_backtest_config()

            self._log(f"Symbol: {config.symbol}")
            self._log(f"Zeitraum: {config.start_date.date()} bis {config.end_date.date()}")
            self._log(f"Kapital: ${config.initial_capital:,.2f}")

            # Import BacktestRunner
            from src.core.backtesting import BacktestRunner

            # Runner erstellen mit Signal-Callback
            self._current_runner = BacktestRunner(
                config,
                signal_callback=self._get_signal_callback(),
            )
            self._current_runner.set_progress_callback(
                lambda p, m: self.progress_updated.emit(p, m)
            )

            self._log("📊 Starte Replay-Backtest...")

            # Run backtest asynchron
            result = await self._current_runner.run()

            if self._current_runner._should_stop:
                self._log("⏹ Backtest abgebrochen")
                return

            self._log("✅ Backtest abgeschlossen!")
            self.progress_updated.emit(100, "Fertig!")

            self._current_result = result
            self.backtest_finished.emit(result)

        except Exception as e:
            logger.exception("Backtest failed")
            self._log(f"❌ Fehler: {e}")
            QMessageBox.critical(self, "Backtest Fehler", str(e))
        finally:
            self._is_running = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("IDLE")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")

    def _on_stop_clicked(self) -> None:
        """Stoppt den Backtest."""
        if self._current_runner:
            self._current_runner.stop()
        self._is_running = False
        self._log("⏹ Backtest wird gestoppt...")
        self.status_detail.setText("Abbrechen...")
        self.stop_btn.setEnabled(False)

    @pyqtSlot()
    def _on_batch_btn_clicked(self) -> None:
        """Synchroner Button-Handler, startet async Batch-Test."""
        logger.info("🔄 _on_batch_btn_clicked() - starting batch worker")
        self._log("🔄 Batch-Test wird gestartet...")

        if self._is_running:
            self._log("⚠️ Batch läuft bereits")
            return

        # Parse parameter space aus UI
        param_space_text = self.param_space_text.toPlainText().strip()
        if not param_space_text:
            param_space = {
                "risk_per_trade_pct": [0.5, 1.0, 1.5, 2.0],
                "max_leverage": [5, 10, 20],
            }
            self._log("⚠️ Kein Parameter Space angegeben, verwende Standard")
        else:
            try:
                param_space = json.loads(param_space_text)
            except json.JSONDecodeError as exc:
                self._log(f"❌ Ungültiges JSON: {exc}")
                QMessageBox.critical(self, "Fehler", f"Ungültiges JSON für Parameter Space:\n{exc}")
                return

        try:
            base_config = self._build_backtest_config()
        except Exception as exc:
            logger.exception("Failed to build backtest config")
            self._log(f"❌ Fehler beim Erstellen der Backtest-Config: {exc}")
            QMessageBox.critical(self, "Backtest Fehler", str(exc))
            return

        # Determine search method
        method_text = self.batch_method.currentText()
        from src.core.backtesting import BatchConfig, SearchMethod

        if "Grid" in method_text:
            search_method = SearchMethod.GRID
        elif "Random" in method_text:
            search_method = SearchMethod.RANDOM
        else:
            search_method = SearchMethod.BAYESIAN

        # Determine target metric
        target_text = self.batch_target.currentText()
        target_map = {
            "Expectancy": "expectancy",
            "Profit Factor": "profit_factor",
            "Sharpe Ratio": "sharpe_ratio",
            "Min Drawdown": "max_drawdown_pct",
        }
        target_metric = target_map.get(target_text, "expectancy")
        minimize = "Drawdown" in target_text

        batch_config = BatchConfig(
            base_config=base_config,
            parameter_space=param_space,
            search_method=search_method,
            target_metric=target_metric,
            minimize=minimize,
            max_iterations=self.batch_iterations.value(),
        )

        self._log("🧭 Batch-Konfiguration erstellt")
        self._log(f"🔄 Methode: {search_method.value}")
        self._log(f"📊 Zielmetrik: {target_metric}, Iterationen: {batch_config.max_iterations}")
        self._log(f"📋 Parameter Space: {list(param_space.keys()) or ['default']}")

        self._is_running = True
        self.run_batch_btn.setEnabled(False)
        self.run_wf_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.status_label.setText("BATCH")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")

        self._batch_worker = BatchTestWorker(
            batch_config,
            signal_callback=self._get_signal_callback(),
            parent=self,
        )
        self._batch_worker.progress.connect(self.progress_updated.emit)
        self._batch_worker.log.connect(self._log)
        self._batch_worker.finished.connect(self._on_batch_worker_finished)
        self._batch_worker.error.connect(self._on_batch_worker_error)
        self._batch_worker.finished.connect(self._batch_worker.deleteLater)
        self._batch_worker.error.connect(self._batch_worker.deleteLater)
        self._batch_worker.start()

    async def _on_batch_clicked(self) -> None:
        """Startet Batch-Test mit Parameter-Optimierung (async)."""
        logger.info("🔄 _on_batch_clicked() called")
        self._log("🔄 Batch-Test async gestartet...")

        if self._is_running:
            logger.info("Already running, returning")
            return

        self._is_running = True
        logger.info("Starting batch test...")
        self.run_batch_btn.setEnabled(False)
        self.run_wf_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.status_label.setText("BATCH")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")

        try:
            # Parse parameter space aus UI
            param_space_text = self.param_space_text.toPlainText().strip()
            if not param_space_text:
                param_space = {
                    "risk_per_trade_pct": [0.5, 1.0, 1.5, 2.0],
                    "max_leverage": [5, 10, 20],
                }
                self._log("⚠️ Kein Parameter Space angegeben, verwende Standard")
            else:
                try:
                    param_space = json.loads(param_space_text)
                except json.JSONDecodeError as e:
                    self._log(f"❌ Ungültiges JSON: {e}")
                    QMessageBox.critical(self, "Fehler", f"Ungültiges JSON für Parameter Space:\n{e}")
                    return

            # Build base config
            base_config = self._build_backtest_config()

            # Determine search method
            method_text = self.batch_method.currentText()
            from src.core.backtesting import BatchRunner, BatchConfig, SearchMethod

            if "Grid" in method_text:
                search_method = SearchMethod.GRID
            elif "Random" in method_text:
                search_method = SearchMethod.RANDOM
            else:
                search_method = SearchMethod.BAYESIAN

            # Determine target metric
            target_text = self.batch_target.currentText()
            target_map = {
                "Expectancy": "expectancy",
                "Profit Factor": "profit_factor",
                "Sharpe Ratio": "sharpe_ratio",
                "Min Drawdown": "max_drawdown_pct",
            }
            target_metric = target_map.get(target_text, "expectancy")
            minimize = "Drawdown" in target_text

            # Create BatchConfig
            batch_config = BatchConfig(
                base_config=base_config,
                parameter_space=param_space,
                search_method=search_method,
                target_metric=target_metric,
                minimize=minimize,
                max_iterations=self.batch_iterations.value(),
            )

            self._log(f"🔄 Starte Batch-Test: {search_method.value}")
            self._log(f"📊 Zielmetrik: {target_metric}, Iterationen: {batch_config.max_iterations}")
            self._log(f"📋 Parameter Space: {list(param_space.keys())}")

            # Create and run BatchRunner
            runner = BatchRunner(
                batch_config,
                signal_callback=self._get_signal_callback(),
            )
            runner.set_progress_callback(lambda p, m: self.progress_updated.emit(p, m))

            summary = await runner.run()

            # Update results table
            self._update_batch_results_table(runner.results)

            # Log summary
            self._log(f"✅ Batch abgeschlossen: {summary.successful_runs}/{summary.total_runs} erfolgreich")
            if summary.best_run and summary.best_run.metrics:
                best = summary.best_run
                self._log(f"🏆 Bester Run: {best.parameters}")
                self._log(f"   {target_metric}: {getattr(best.metrics, target_metric, 'N/A')}")

            # Offer export
            reply = QMessageBox.question(
                self, "Export",
                f"Batch abgeschlossen!\n\n{summary.successful_runs} erfolgreiche Runs.\n\nErgebnisse exportieren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                output_dir = Path("data/backtest_results") / summary.batch_id
                exports = await runner.export_results(output_dir)
                self._log(f"📁 Exportiert nach: {output_dir}")

        except Exception as e:
            logger.exception("Batch test failed")
            self._log(f"❌ Batch Fehler: {e}")
            QMessageBox.critical(self, "Batch Fehler", str(e))

        finally:
            self._is_running = False
            self.run_batch_btn.setEnabled(True)
            self.run_wf_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.status_label.setText("IDLE")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")

    @pyqtSlot(object, list)
    def _on_batch_worker_finished(self, summary, results: list) -> None:
        """Verarbeitet Abschluss des Batch-Workers."""
        self._update_batch_results_table(results)

        self._log(f"✅ Batch abgeschlossen: {summary.successful_runs}/{summary.total_runs} erfolgreich")
        if summary.best_run and summary.best_run.metrics:
            best = summary.best_run
            target_metric = summary.config_summary.get("target_metric", "expectancy")
            self._log(f"🏆 Bester Run: {best.parameters}")
            self._log(f"   {target_metric}: {getattr(best.metrics, target_metric, 'N/A')}")

        reply = QMessageBox.question(
            self, "Export",
            f"Batch abgeschlossen!\n\n{summary.successful_runs} erfolgreiche Runs.\n\nErgebnisse exportieren?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            output_dir = Path("data/backtest_results") / summary.batch_id
            self._export_batch_results(summary, results, output_dir)
            self._log(f"📁 Exportiert nach: {output_dir}")

        self._finalize_batch_ui()

    @pyqtSlot(str)
    def _on_batch_worker_error(self, message: str) -> None:
        """Verarbeitet Fehler im Batch-Worker."""
        self._log(f"❌ Batch Fehler: {message}")
        QMessageBox.critical(self, "Batch Fehler", message)
        self._finalize_batch_ui()

    def _finalize_batch_ui(self) -> None:
        """Setzt UI nach Batch-Run zurück."""
        self._is_running = False
        self.run_batch_btn.setEnabled(True)
        self.run_wf_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        self.status_label.setText("IDLE")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")
        self._batch_worker = None

    def _export_batch_results(self, summary, results: list, output_dir: Path) -> dict[str, Path]:
        """Exportiert Batch-Ergebnisse basierend auf Worker-Resultaten."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exports: dict[str, Path] = {}

        summary_path = output_dir / f"{summary.batch_id}_summary.json"
        summary_data = {
            "batch_id": summary.batch_id,
            "total_runs": summary.total_runs,
            "target_metric": summary.config_summary.get("target_metric"),
            "search_method": summary.config_summary.get("search_method"),
        }
        with open(summary_path, "w") as file:
            json.dump(summary_data, file, indent=2, default=str)
        exports["summary"] = summary_path

        results_path = output_dir / f"{summary.batch_id}_results.csv"
        runs_to_export = results[:20]
        with open(results_path, "w", newline="") as file:
            import csv

            writer = csv.writer(file)
            if runs_to_export:
                param_keys = list(runs_to_export[0].parameters.keys())
                metric_keys = [
                    "total_trades",
                    "win_rate",
                    "profit_factor",
                    "expectancy",
                    "max_drawdown_pct",
                    "total_return_pct",
                ]
                writer.writerow(["rank", "run_id"] + param_keys + metric_keys + ["error"])

                for rank, run in enumerate(runs_to_export, 1):
                    param_values = [run.parameters.get(k, "") for k in param_keys]
                    if run.metrics:
                        metric_values = [
                            run.metrics.total_trades,
                            f"{run.metrics.win_rate:.3f}",
                            f"{run.metrics.profit_factor:.2f}",
                            f"{run.metrics.expectancy:.2f}" if run.metrics.expectancy else "",
                            f"{run.metrics.max_drawdown_pct:.2f}",
                            f"{run.metrics.total_return_pct:.2f}",
                        ]
                    else:
                        metric_values = [""] * len(metric_keys)
                    writer.writerow([rank, run.run_id] + param_values + metric_values + [run.error or ""])
        exports["results"] = results_path

        if results:
            top_path = output_dir / f"{summary.batch_id}_top_params.json"
            top_data = []
            for run in results[:5]:
                if run.metrics:
                    top_data.append({
                        "parameters": run.parameters,
                        "expectancy": run.metrics.expectancy,
                        "profit_factor": run.metrics.profit_factor,
                        "win_rate": run.metrics.win_rate,
                        "total_return_pct": run.metrics.total_return_pct,
                    })
            with open(top_path, "w") as file:
                json.dump(top_data, file, indent=2)
            exports["top_params"] = top_path

        return exports

    @pyqtSlot()
    def _on_wf_btn_clicked(self) -> None:
        """Synchroner Button-Handler, startet async Walk-Forward Test."""
        logger.info("🚶 _on_wf_btn_clicked() - scheduling async walk-forward")
        self._log("🚶 Walk-Forward wird gestartet...")

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._on_wf_clicked())
            else:
                logger.warning("Event loop not running, trying qasync")
                asyncio.ensure_future(self._on_wf_clicked())
        except Exception as e:
            logger.exception(f"Failed to schedule walk-forward: {e}")
            self._log(f"❌ Fehler beim Starten des Walk-Forward: {e}")

    async def _on_wf_clicked(self) -> None:
        """Startet Walk-Forward Analyse mit Rolling Windows (async)."""
        logger.info("🚶 _on_wf_clicked() called")

        if self._is_running:
            logger.info("Already running, returning")
            return

        self._is_running = True
        self.run_batch_btn.setEnabled(False)
        self.run_wf_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.status_label.setText("WALK-FWD")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #9C27B0;")

        try:
            # Build base config
            base_config = self._build_backtest_config()

            # Parse parameter space für Re-Optimization
            param_space_text = self.param_space_text.toPlainText().strip()
            if param_space_text:
                try:
                    param_space = json.loads(param_space_text)
                except json.JSONDecodeError:
                    param_space = {}
            else:
                param_space = {}

            # Walk-Forward Config aus UI
            from src.core.backtesting import WalkForwardRunner, WalkForwardConfig, BatchConfig, SearchMethod

            # BatchConfig für Optimierung erstellen (falls Parameter Space vorhanden)
            batch_config = BatchConfig(
                base_config=base_config,
                search_method=SearchMethod.GRID if param_space else SearchMethod.GRID,
                parameter_space=param_space,
                target_metric="expectancy",
                minimize=False,
            )

            wf_config = WalkForwardConfig(
                base_config=base_config,
                batch_config=batch_config,
                train_window_days=self.wf_train_days.value(),
                test_window_days=self.wf_test_days.value(),
                step_size_days=self.wf_step_days.value(),
                reoptimize_each_fold=self.wf_reoptimize.isChecked(),
            )

            self._log(f"🚶 Starte Walk-Forward Analyse")
            self._log(f"📅 Train: {wf_config.train_window_days}d, Test: {wf_config.test_window_days}d, Step: {wf_config.step_size_days}d")
            self._log(f"🔄 Re-Optimize: {wf_config.reoptimize_each_fold}")

            # Create and run WalkForwardRunner
            runner = WalkForwardRunner(
                wf_config,
                signal_callback=self._get_signal_callback(),
            )
            runner.set_progress_callback(lambda p, m: self.progress_updated.emit(p, m))

            summary = await runner.run()

            # Update results table with fold results
            self._update_wf_results_table(summary.fold_results)

            # Log summary
            self._log(f"✅ Walk-Forward abgeschlossen: {summary.total_folds} Folds")
            self._log(f"📊 Aggregierte OOS-Performance:")
            if summary.aggregated_oos_metrics:
                agg = summary.aggregated_oos_metrics
                self._log(f"   Total Trades: {agg.total_trades}")
                self._log(f"   Win Rate: {agg.win_rate * 100:.1f}%")
                self._log(f"   Profit Factor: {agg.profit_factor:.2f}")
                self._log(f"   Max DD: {agg.max_drawdown_pct:.1f}%")

            # Stability info
            if summary.stable_parameters:
                self._log(f"🔒 Stabile Parameter: {len(summary.stable_parameters)}")
                for param, stability in list(summary.stable_parameters.items())[:3]:
                    self._log(f"   {param}: Stabilität {stability:.1%}")

            # Offer export
            reply = QMessageBox.question(
                self, "Export",
                f"Walk-Forward abgeschlossen!\n\n{summary.total_folds} Folds analysiert.\n\nErgebnisse exportieren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                output_dir = Path("data/backtest_results") / summary.wf_id
                exports = await runner.export_results(output_dir)
                self._log(f"📁 Exportiert nach: {output_dir}")

        except Exception as e:
            logger.exception("Walk-Forward failed")
            self._log(f"❌ Walk-Forward Fehler: {e}")
            QMessageBox.critical(self, "Walk-Forward Fehler", str(e))

        finally:
            self._is_running = False
            self.run_batch_btn.setEnabled(True)
            self.run_wf_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.status_label.setText("IDLE")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")

    @pyqtSlot(int, str)
    def _on_progress_updated(self, progress: int, message: str) -> None:
        """Update Progress Bar."""
        self.progress_bar.setValue(progress)
        self.status_detail.setText(message)

    @pyqtSlot(str)
    def _on_log_message(self, message: str) -> None:
        """Fügt Log-Nachricht hinzu."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def _log(self, message: str) -> None:
        """Log-Nachricht (thread-safe)."""
        self.log_message.emit(message)

    @pyqtSlot(object)
    def _on_backtest_finished(self, result) -> None:
        """Verarbeitet Backtest-Ergebnis."""
        if result is None:
            return

        try:
            # Update KPI Cards
            metrics = result.metrics if hasattr(result, 'metrics') else None

            if metrics:
                # P&L
                pnl = result.total_pnl if hasattr(result, 'total_pnl') else 0
                pnl_color = "#4CAF50" if pnl >= 0 else "#f44336"
                self.kpi_pnl.findChild(QLabel, "kpi_value").setText(f"${pnl:,.2f}")
                self.kpi_pnl.findChild(QLabel, "kpi_value").setStyleSheet(
                    f"color: {pnl_color}; font-size: 18px; font-weight: bold;"
                )

                # Win Rate
                win_rate = metrics.win_rate * 100 if metrics.win_rate else 0
                self.kpi_winrate.findChild(QLabel, "kpi_value").setText(f"{win_rate:.1f}%")

                # Profit Factor
                pf = metrics.profit_factor if metrics.profit_factor else 0
                self.kpi_pf.findChild(QLabel, "kpi_value").setText(f"{pf:.2f}")

                # Max DD
                dd = metrics.max_drawdown_pct if metrics.max_drawdown_pct else 0
                self.kpi_dd.findChild(QLabel, "kpi_value").setText(f"{dd:.1f}%")

                # Update Metrics Table
                self._update_metrics_table(metrics)

            # Update Trades Table
            if hasattr(result, 'trades') and result.trades:
                self._update_trades_table(result.trades)
                self._update_breakdown_table(result.trades)

            # Update Equity Curve Chart
            if self.equity_chart and hasattr(result, 'equity_curve') and result.equity_curve:
                try:
                    self.equity_chart.load_from_result(result)
                    self._log(f"📈 Equity Curve geladen: {len(result.equity_curve)} Punkte")
                except Exception as eq_err:
                    logger.warning(f"Could not load equity chart: {eq_err}")

            # Switch to Results tab
            self.tab_widget.setCurrentIndex(2)  # Results Tab

            self._log(f"📊 Ergebnisse geladen: {metrics.total_trades if metrics else 0} Trades")

        except Exception as e:
            logger.exception("Error updating results")
            self._log(f"❌ Fehler beim Anzeigen: {e}")

    def _update_metrics_table(self, metrics) -> None:
        """Aktualisiert die Metriken-Tabelle."""
        data = [
            ("Total Trades", str(metrics.total_trades)),
            ("Winning Trades", str(metrics.winning_trades)),
            ("Losing Trades", str(metrics.losing_trades)),
            ("Win Rate", f"{metrics.win_rate * 100:.1f}%"),
            ("Profit Factor", f"{metrics.profit_factor:.2f}"),
            ("Expectancy", f"${metrics.expectancy:.2f}" if metrics.expectancy else "—"),
            ("Max Drawdown", f"{metrics.max_drawdown_pct:.1f}%"),
            ("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}" if metrics.sharpe_ratio else "—"),
            ("Avg R-Multiple", f"{metrics.avg_r_multiple:.2f}" if metrics.avg_r_multiple else "—"),
        ]

        self.metrics_table.setRowCount(len(data))
        for row, (name, value) in enumerate(data):
            self.metrics_table.setItem(row, 0, QTableWidgetItem(name))
            self.metrics_table.setItem(row, 1, QTableWidgetItem(value))

    def _update_trades_table(self, trades: list) -> None:
        """Aktualisiert die Trades-Tabelle."""
        self.trades_table.setRowCount(len(trades))

        for row, trade in enumerate(trades):
            self.trades_table.setItem(row, 0, QTableWidgetItem(trade.id[:8] if trade.id else "—"))
            self.trades_table.setItem(row, 1, QTableWidgetItem(trade.symbol))
            self.trades_table.setItem(row, 2, QTableWidgetItem(trade.side.value.upper()))
            self.trades_table.setItem(row, 3, QTableWidgetItem(f"${trade.entry_price:.2f}"))
            self.trades_table.setItem(row, 4, QTableWidgetItem(
                f"${trade.exit_price:.2f}" if trade.exit_price else "—"
            ))
            self.trades_table.setItem(row, 5, QTableWidgetItem(f"{trade.size:.4f}"))

            # P&L mit Farbe
            pnl = trade.realized_pnl
            pnl_item = QTableWidgetItem(f"${pnl:.2f}")
            pnl_item.setForeground(QColor("#4CAF50" if pnl >= 0 else "#f44336"))
            self.trades_table.setItem(row, 6, pnl_item)

            # R-Multiple
            r_mult = trade.r_multiple if hasattr(trade, 'r_multiple') else None
            self.trades_table.setItem(row, 7, QTableWidgetItem(
                f"{r_mult:.2f}R" if r_mult else "—"
            ))

    def _update_breakdown_table(self, trades: list) -> None:
        """Aktualisiert die Regime/Setup Breakdown Tabelle.

        Gruppiert Trades nach Regime/Setup und berechnet Statistiken.

        Args:
            trades: Liste von Trade Objekten
        """
        if not trades:
            self.breakdown_table.setRowCount(0)
            return

        # Trades nach Regime/Setup gruppieren
        from collections import defaultdict

        breakdown = defaultdict(lambda: {
            "trades": [],
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
        })

        for trade in trades:
            # Bestimme Regime/Setup - verwende exit_reason oder regime falls vorhanden
            regime = "Unknown"
            if hasattr(trade, 'regime') and trade.regime:
                regime = trade.regime
            elif hasattr(trade, 'exit_reason') and trade.exit_reason:
                regime = trade.exit_reason
            elif hasattr(trade, 'setup_type') and trade.setup_type:
                regime = trade.setup_type
            elif hasattr(trade, 'side'):
                regime = f"{trade.side.value.upper()} Trade"

            pnl = trade.realized_pnl if hasattr(trade, 'realized_pnl') else 0

            breakdown[regime]["trades"].append(trade)
            breakdown[regime]["total_pnl"] += pnl

            if pnl >= 0:
                breakdown[regime]["wins"] += 1
                breakdown[regime]["gross_profit"] += pnl
            else:
                breakdown[regime]["losses"] += 1
                breakdown[regime]["gross_loss"] += abs(pnl)

        # Tabelle füllen
        total_trades = len(trades)
        self.breakdown_table.setRowCount(len(breakdown))

        for row, (regime, stats) in enumerate(sorted(breakdown.items(), key=lambda x: len(x[1]["trades"]), reverse=True)):
            num_trades = len(stats["trades"])
            wins = stats["wins"]
            losses = stats["losses"]
            total_pnl = stats["total_pnl"]
            gross_profit = stats["gross_profit"]
            gross_loss = stats["gross_loss"]

            # Win Rate
            win_rate = (wins / num_trades * 100) if num_trades > 0 else 0

            # Avg P&L
            avg_pnl = total_pnl / num_trades if num_trades > 0 else 0

            # Profit Factor
            pf = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0)

            # Expectancy
            expectancy = avg_pnl

            # Anteil
            share = (num_trades / total_trades * 100) if total_trades > 0 else 0

            # Zeile setzen
            self.breakdown_table.setItem(row, 0, QTableWidgetItem(regime))
            self.breakdown_table.setItem(row, 1, QTableWidgetItem(str(num_trades)))

            wr_item = QTableWidgetItem(f"{win_rate:.1f}%")
            wr_item.setForeground(QColor("#4CAF50" if win_rate >= 50 else "#FF9800" if win_rate >= 40 else "#f44336"))
            self.breakdown_table.setItem(row, 2, wr_item)

            avg_item = QTableWidgetItem(f"${avg_pnl:.2f}")
            avg_item.setForeground(QColor("#4CAF50" if avg_pnl >= 0 else "#f44336"))
            self.breakdown_table.setItem(row, 3, avg_item)

            pf_str = f"{pf:.2f}" if pf != float('inf') else "∞"
            pf_item = QTableWidgetItem(pf_str)
            pf_item.setForeground(QColor("#4CAF50" if pf >= 1.5 else "#FF9800" if pf >= 1 else "#f44336"))
            self.breakdown_table.setItem(row, 4, pf_item)

            exp_item = QTableWidgetItem(f"${expectancy:.2f}")
            exp_item.setForeground(QColor("#4CAF50" if expectancy >= 0 else "#f44336"))
            self.breakdown_table.setItem(row, 5, exp_item)

            self.breakdown_table.setItem(row, 6, QTableWidgetItem(f"{share:.1f}%"))

    def _update_batch_results_table(self, results: list) -> None:
        """Aktualisiert die Batch-Ergebnisse Tabelle.

        Args:
            results: Liste von BatchRunResult Objekten
        """
        self.batch_results_table.setRowCount(len(results))

        for row, run in enumerate(results):
            # Rank/Run
            self.batch_results_table.setItem(row, 0, QTableWidgetItem(f"#{row + 1}"))

            # Parameters (kurze Darstellung)
            params_str = ", ".join(f"{k}={v}" for k, v in list(run.parameters.items())[:2])
            if len(run.parameters) > 2:
                params_str += "..."
            self.batch_results_table.setItem(row, 1, QTableWidgetItem(params_str))

            if run.metrics:
                # P&L
                pnl = run.metrics.total_return_pct
                pnl_item = QTableWidgetItem(f"{pnl:.1f}%")
                pnl_item.setForeground(QColor("#4CAF50" if pnl >= 0 else "#f44336"))
                self.batch_results_table.setItem(row, 2, pnl_item)

                # Expectancy
                exp = run.metrics.expectancy if run.metrics.expectancy else 0
                self.batch_results_table.setItem(row, 3, QTableWidgetItem(f"${exp:.2f}"))

                # Max DD
                dd = run.metrics.max_drawdown_pct
                dd_item = QTableWidgetItem(f"{dd:.1f}%")
                dd_item.setForeground(QColor("#f44336" if dd > 10 else "#FF9800" if dd > 5 else "#4CAF50"))
                self.batch_results_table.setItem(row, 4, dd_item)
            else:
                # Error case
                error_item = QTableWidgetItem(run.error or "Fehler")
                error_item.setForeground(QColor("#f44336"))
                self.batch_results_table.setItem(row, 2, error_item)

    def _update_wf_results_table(self, fold_results: list) -> None:
        """Aktualisiert die Walk-Forward Ergebnisse Tabelle.

        Args:
            fold_results: Liste von FoldResult Objekten
        """
        self.batch_results_table.setRowCount(len(fold_results))

        for row, fold in enumerate(fold_results):
            # Fold Number
            self.batch_results_table.setItem(row, 0, QTableWidgetItem(f"Fold {fold.fold_number}"))

            # Parameters (optimierte)
            if fold.optimized_parameters:
                params_str = ", ".join(f"{k}={v}" for k, v in list(fold.optimized_parameters.items())[:2])
            else:
                params_str = "Standard"
            self.batch_results_table.setItem(row, 1, QTableWidgetItem(params_str))

            # OOS P&L
            if fold.oos_metrics:
                pnl = fold.oos_metrics.total_return_pct
                pnl_item = QTableWidgetItem(f"{pnl:.1f}%")
                pnl_item.setForeground(QColor("#4CAF50" if pnl >= 0 else "#f44336"))
                self.batch_results_table.setItem(row, 2, pnl_item)

                # OOS Expectancy
                exp = fold.oos_metrics.expectancy if fold.oos_metrics.expectancy else 0
                self.batch_results_table.setItem(row, 3, QTableWidgetItem(f"${exp:.2f}"))

                # OOS Max DD
                dd = fold.oos_metrics.max_drawdown_pct
                dd_item = QTableWidgetItem(f"{dd:.1f}%")
                dd_item.setForeground(QColor("#f44336" if dd > 10 else "#FF9800" if dd > 5 else "#4CAF50"))
                self.batch_results_table.setItem(row, 4, dd_item)
            else:
                error_item = QTableWidgetItem("Keine OOS-Daten")
                error_item.setForeground(QColor("#888"))
                self.batch_results_table.setItem(row, 2, error_item)

    def _get_signal_callback(self) -> Optional[Callable]:
        """
        Gibt den Signal-Callback für den Backtest zurück.

        Verwendet die Engine-Konfigurationen aus den Engine Settings Tabs.
        Verbindet den Backtest mit den Trading Bot Engines (SignalGenerator,
        EntryScoreEngine, LevelEngine, etc.)

        Returns:
            Callable: Signal-Callback Funktion oder None
        """
        # Sammle aktuelle Engine-Configs
        engine_configs = self.collect_engine_configs()

        # Prüfe ob parent (ChartWindow) eine signal_callback hat
        chart_window = self._find_chart_window()
        if chart_window and hasattr(chart_window, 'get_signal_callback'):
            callback = chart_window.get_signal_callback()
            if callback:
                logger.info("Using ChartWindow signal callback for backtest")
                return callback

        # Prüfe ob wir direkten Zugriff auf die Trading Bot Engines haben
        if hasattr(self, '_signal_generator'):
            return self._signal_generator.generate_signal

        # Erstelle Signal-Pipeline mit Engine-Configs
        try:
            from src.core.trading_bot import (
                LevelEngine,
                EntryScoreEngine,
                MarketContextBuilder,
            )

            # Entry Score Config aus Engine Settings
            entry_config = None
            if HAS_ENTRY_SCORE and 'entry_score' in engine_configs:
                try:
                    es = engine_configs['entry_score']
                    entry_config = EntryScoreConfig(
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
                    logger.info("EntryScoreConfig aus Engine Settings geladen")
                except Exception as e:
                    logger.warning(f"EntryScoreConfig Fehler: {e}")

            # Level Engine Config aus Engine Settings
            level_config = None
            if HAS_LEVELS and 'levels' in engine_configs:
                try:
                    lvl = engine_configs['levels']
                    level_config = LevelEngineConfig(
                        lookback_bars=lvl.get('lookback_bars', 100),
                        min_touches=lvl.get('min_touches', 2),
                        zone_width_atr=lvl.get('zone_width_atr', 0.5),
                        significance_threshold=lvl.get('significance_threshold', 0.7),
                    )
                    logger.info("LevelEngineConfig aus Engine Settings geladen")
                except Exception as e:
                    logger.warning(f"LevelEngineConfig Fehler: {e}")

            # Min-Score aus Entry Settings
            min_score_for_signal = 0.50
            if 'entry_score' in engine_configs:
                min_score_for_signal = engine_configs['entry_score'].get('min_score_for_entry', 0.50)

            # Trigger/Exit Settings
            tp_atr_mult = 2.0
            sl_atr_mult = 1.5
            if 'trigger_exit' in engine_configs:
                te = engine_configs['trigger_exit']
                tp_atr_mult = te.get('tp_atr_multiplier', 2.0)
                sl_atr_mult = te.get('sl_atr_multiplier', 1.5)

            # Erstelle konfigurierte Signal-Pipeline für Backtest
            def backtest_signal_callback(candles, symbol, timeframe):
                """
                Generiert Signal basierend auf Candle-Daten mit Engine-Configs.

                Verwendet die konfigurierten Engines aus Engine Settings.
                """
                if not candles or len(candles) < 50:
                    return None

                try:
                    # MarketContext aufbauen
                    context_builder = MarketContextBuilder()
                    context = context_builder.build_from_candles(candles, symbol)

                    # Levels berechnen mit Config
                    level_engine = LevelEngine(config=level_config) if level_config else LevelEngine()
                    levels = level_engine.detect_levels(candles)

                    # Entry Score berechnen mit Config
                    entry_engine = EntryScoreEngine(config=entry_config) if entry_config else EntryScoreEngine()
                    score_result = entry_engine.calculate_score(context, levels)

                    # Score normalisieren (0-100 -> 0-1)
                    if score_result:
                        total_score = score_result.total_score
                        if isinstance(total_score, (int, float)):
                            # Normalisieren falls Score > 1
                            if total_score > 1:
                                total_score = total_score / 100.0
                        else:
                            total_score = 0.0

                        # Signal generieren wenn Score hoch genug
                        if total_score >= min_score_for_signal:
                            # ATR für TP/SL berechnen
                            atr = context.atr if hasattr(context, 'atr') else None
                            if not atr and len(candles) > 14:
                                # Berechne ATR
                                import pandas as pd
                                df = pd.DataFrame([c.__dict__ for c in candles[-20:]])
                                if 'high' in df and 'low' in df and 'close' in df:
                                    df['tr'] = df[['high', 'low']].max(axis=1) - df[['high', 'low']].min(axis=1)
                                    atr = df['tr'].mean()

                            current_price = candles[-1].close
                            atr = atr or (current_price * 0.02)  # Fallback: 2%

                            # Bestimme Richtung
                            bias = getattr(score_result, 'bias', 'neutral')
                            if bias == 'bullish' or (hasattr(score_result, 'direction') and score_result.direction == 'LONG'):
                                signal_dir = "LONG"
                                sl = current_price - (atr * sl_atr_mult)
                                tp = current_price + (atr * tp_atr_mult)
                            elif bias == 'bearish' or (hasattr(score_result, 'direction') and score_result.direction == 'SHORT'):
                                signal_dir = "SHORT"
                                sl = current_price + (atr * sl_atr_mult)
                                tp = current_price - (atr * tp_atr_mult)
                            else:
                                return None

                            return {
                                "signal": signal_dir,
                                "confidence": total_score,
                                "entry_price": current_price,
                                "stop_loss": sl,
                                "take_profit": tp,
                                "atr": atr,
                                "score_quality": getattr(score_result, 'quality', 'UNKNOWN'),
                                "regime": getattr(context, 'regime', None),
                            }

                except Exception as e:
                    logger.warning(f"Signal generation error: {e}")

                return None

            config_sources = []
            if entry_config:
                config_sources.append("EntryScore")
            if level_config:
                config_sources.append("Levels")
            if 'trigger_exit' in engine_configs:
                config_sources.append("Trigger/Exit")

            logger.info(f"Signal callback mit Engine-Configs: {config_sources}")
            return backtest_signal_callback

        except ImportError as e:
            logger.warning(f"Could not create signal callback: {e}")
            return None

    # =========================================================================
    # CONFIG INSPECTOR UI HANDLERS
    # =========================================================================

    def _on_load_configs_clicked(self) -> None:
        """
        Lädt Engine-Configs und zeigt sie im Config Inspector an.

        Sammelt alle konfigurierbaren Parameter aus den Engine Settings Tabs
        und zeigt sie in der Tabelle an.
        """
        self._log("📥 Lade Engine Configs...")
        logger.info("Load Configs Button clicked - loading engine configurations")

        try:
            # Sammle Parameter-Spezifikation
            specs = self.get_parameter_specification()
            logger.info(f"Loaded {len(specs)} parameter specifications")

            # Tabelle aktualisieren
            self.config_inspector_table.setRowCount(len(specs))

            for row, spec in enumerate(specs):
                # Kategorie
                self.config_inspector_table.setItem(
                    row, 0, QTableWidgetItem(f"{spec['category']}/{spec['subcategory']}")
                )

                # Parameter
                self.config_inspector_table.setItem(
                    row, 1, QTableWidgetItem(spec['display_name'])
                )

                # Wert
                value_str = str(spec['current_value'])
                if spec['type'] == 'float':
                    value_str = f"{spec['current_value']:.2f}"
                value_item = QTableWidgetItem(value_str)
                value_item.setForeground(QColor("#4CAF50"))
                self.config_inspector_table.setItem(row, 2, value_item)

                # UI-Tab
                self.config_inspector_table.setItem(
                    row, 3, QTableWidgetItem(spec['ui_tab'])
                )

                # Beschreibung (neue Spalte)
                description = spec.get('description', '')
                desc_item = QTableWidgetItem(description[:40] + '...' if len(description) > 40 else description)
                desc_item.setToolTip(description)  # Volle Beschreibung als Tooltip
                self.config_inspector_table.setItem(row, 4, desc_item)

                # Typ
                self.config_inspector_table.setItem(
                    row, 5, QTableWidgetItem(spec['type'])
                )

                # Min/Max
                if spec['min'] is not None and spec['max'] is not None:
                    minmax_str = f"{spec['min']}-{spec['max']}"
                else:
                    minmax_str = "—"
                self.config_inspector_table.setItem(
                    row, 6, QTableWidgetItem(minmax_str)
                )

                # Variationen
                variations = spec.get('variations', [])
                if variations:
                    var_str = ", ".join([str(v)[:6] for v in variations[:4]])
                    if len(variations) > 4:
                        var_str += "..."
                else:
                    var_str = "—"
                self.config_inspector_table.setItem(
                    row, 7, QTableWidgetItem(var_str)
                )

            # Erstelle Parameter-Space aus Configs
            param_space = self.get_parameter_space_from_configs()

            if param_space:
                self.param_space_text.setText(json.dumps(param_space, indent=2))
                self._log(f"✅ {len(specs)} Parameter geladen, {len(param_space)} für Batch-Test")
            else:
                self._log("⚠️ Keine Parameter für Batch-Test verfügbar")

            # Wechsle automatisch zum Batch/WF Tab um die Config-Tabelle zu zeigen
            # Tab 3 ist "🔄 Batch/WF"
            self.sub_tabs.setCurrentIndex(3)
            logger.info("Switched to Batch/WF tab to show Config Inspector")

        except Exception as e:
            logger.exception("Failed to load configs")
            self._log(f"❌ Fehler: {e}")
            QMessageBox.critical(self, "Fehler", f"Config-Laden fehlgeschlagen:\n{e}")

    def _on_auto_generate_clicked(self) -> None:
        """
        Generiert automatisch Test-Varianten.

        Erstellt sinnvolle Kombinationen aus:
        - Vordefinierten Indikator-Sets
        - Algorithmisch variierten Parametern
        """
        self._log("🤖 Generiere Test-Varianten...")

        try:
            # Sammle Parameter-Spezifikation
            specs = self.get_parameter_specification()

            # Generiere Varianten
            num_variants = self.batch_iterations.value()
            num_variants = min(num_variants, 20)  # Max 20 für Auto-Generate

            variants = self.generate_ai_test_variants(specs, num_variants)

            # Zeige Dialog mit generierten Varianten
            dialog = QDialog(self)
            dialog.setWindowTitle("🤖 Generierte Test-Varianten")
            dialog.setMinimumSize(700, 500)

            dlg_layout = QVBoxLayout(dialog)

            # Info Label
            info = QLabel(f"✅ {len(variants)} Test-Varianten generiert:")
            info.setStyleSheet("font-weight: bold; color: #4CAF50;")
            dlg_layout.addWidget(info)

            # Varianten-Tabelle
            var_table = QTableWidget()
            var_table.setColumnCount(4)
            var_table.setHorizontalHeaderLabels(["ID", "Name", "Quelle", "Parameter"])
            var_table.horizontalHeader().setStretchLastSection(True)
            var_table.setRowCount(len(variants))

            for row, variant in enumerate(variants):
                var_table.setItem(row, 0, QTableWidgetItem(variant['id']))
                var_table.setItem(row, 1, QTableWidgetItem(variant['name']))
                var_table.setItem(row, 2, QTableWidgetItem(variant['source']))

                params_str = ", ".join([f"{k}={v}" for k, v in list(variant['parameters'].items())[:3]])
                if len(variant['parameters']) > 3:
                    params_str += "..."
                var_table.setItem(row, 3, QTableWidgetItem(params_str))

            dlg_layout.addWidget(var_table)

            # Buttons
            btn_box = QDialogButtonBox()

            use_btn = QPushButton("✅ Als Parameter Space verwenden")
            use_btn.clicked.connect(lambda: self._apply_variants_to_param_space(variants, dialog))
            btn_box.addButton(use_btn, QDialogButtonBox.ButtonRole.AcceptRole)

            export_btn = QPushButton("📄 Als JSON exportieren")
            export_btn.clicked.connect(lambda: self._export_variants_json(variants))
            btn_box.addButton(export_btn, QDialogButtonBox.ButtonRole.ActionRole)

            cancel_btn = QPushButton("Abbrechen")
            cancel_btn.clicked.connect(dialog.reject)
            btn_box.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

            dlg_layout.addWidget(btn_box)

            dialog.exec()

        except Exception as e:
            logger.exception("Failed to generate variants")
            self._log(f"❌ Fehler: {e}")
            QMessageBox.critical(self, "Fehler", f"Varianten-Generierung fehlgeschlagen:\n{e}")

    def _apply_variants_to_param_space(self, variants: list, dialog: QDialog) -> None:
        """Wendet generierte Varianten als Parameter Space an."""
        # Konvertiere Varianten zu Parameter-Space Format
        param_space = {}

        for variant in variants:
            for param_name, param_value in variant['parameters'].items():
                if param_name not in param_space:
                    param_space[param_name] = []
                if param_value not in param_space[param_name]:
                    param_space[param_name].append(param_value)

        # Sortiere Werte
        for key in param_space:
            try:
                param_space[key] = sorted(param_space[key])
            except TypeError:
                pass  # Kann nicht sortiert werden (mixed types)

        self.param_space_text.setText(json.dumps(param_space, indent=2))
        self._log(f"✅ {len(param_space)} Parameter mit Varianten übernommen")
        dialog.accept()

    def _export_variants_json(self, variants: list) -> None:
        """Exportiert Varianten als JSON-Datei."""
        try:
            output_dir = Path("data/backtest_results")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = output_dir / f"test_variants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(filename, 'w') as f:
                json.dump(variants, f, indent=2)

            self._log(f"📄 Varianten exportiert: {filename}")
            QMessageBox.information(self, "Export", f"Varianten exportiert nach:\n{filename}")

        except Exception as e:
            logger.exception("Failed to export variants")
            QMessageBox.critical(self, "Fehler", f"Export fehlgeschlagen:\n{e}")

    def _on_indicator_set_changed(self, index: int) -> None:
        """
        Handler für Indikator-Set Auswahl.

        Lädt ein vordefiniertes Indikator-Set und zeigt dessen Parameter an.
        """
        if index == 0:  # "-- Manuell --"
            return

        indicator_sets = self.get_available_indicator_sets()

        # Index anpassen (0 = Manuell, 1+ = Sets)
        set_index = index - 1

        if 0 <= set_index < len(indicator_sets):
            ind_set = indicator_sets[set_index]

            # Erstelle Parameter-Space aus Set
            param_space = {}

            # Weights
            for weight_name, weight_val in ind_set.get('weights', {}).items():
                param_space[f'weight_{weight_name}'] = [weight_val]

            # Andere Settings
            if 'min_score_for_entry' in ind_set:
                param_space['min_score_for_entry'] = [ind_set['min_score_for_entry']]
            if 'gates' in ind_set:
                for gate_name, gate_val in ind_set['gates'].items():
                    param_space[f'gate_{gate_name}'] = [gate_val]
            if 'leverage' in ind_set:
                for lev_name, lev_val in ind_set['leverage'].items():
                    param_space[lev_name] = [lev_val]
            if 'level_settings' in ind_set:
                for lvl_name, lvl_val in ind_set['level_settings'].items():
                    param_space[lvl_name] = [lvl_val]

            self.param_space_text.setText(json.dumps(param_space, indent=2))
            self._log(f"📊 Indikator-Set '{ind_set['name']}' geladen: {ind_set['description']}")

    # =========================================================================
    # TEMPLATE MANAGEMENT HANDLERS
    # =========================================================================

    def _on_save_template_clicked(self) -> None:
        """
        Speichert die aktuelle Basistabelle als JSON-Template.

        Das Template enthält:
        - Alle Parameter-Spezifikationen
        - Aktuelle Werte aus Engine Settings
        - Metadaten (Timestamp, Name, Beschreibung)
        """
        self._log("💾 Speichere Template...")

        try:
            # Sammle Parameter-Spezifikation
            specs = self.get_parameter_specification()

            if not specs:
                QMessageBox.warning(
                    self, "Keine Daten",
                    "Bitte zuerst Engine Configs laden (Button 'Lade Engine Configs')."
                )
                return

            # Template-Struktur erstellen
            template = {
                'meta': {
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'type': 'backtest_config_template',
                    'description': '',
                    'name': '',
                },
                'parameters': {},
                'full_specs': specs,  # Komplette Spezifikation für Wiederherstellung
            }

            # Extrahiere Parameter-Werte
            for spec in specs:
                param_key = spec['parameter']
                template['parameters'][param_key] = {
                    'value': spec['current_value'],
                    'type': spec['type'],
                    'category': spec['category'],
                    'subcategory': spec['subcategory'],
                    'description': spec.get('description', ''),
                    'min': spec['min'],
                    'max': spec['max'],
                    'variations': spec.get('variations', []),
                }

            # Dialog für Template-Name und Beschreibung
            dialog = QDialog(self)
            dialog.setWindowTitle("💾 Template speichern")
            dialog.setMinimumWidth(400)

            dlg_layout = QVBoxLayout(dialog)

            # Name Input
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("Name:"))
            name_input = QLineEdit()
            name_input.setPlaceholderText("z.B. 'Aggressive Trend Strategy'")
            name_layout.addWidget(name_input)
            dlg_layout.addLayout(name_layout)

            # Description Input
            desc_layout = QVBoxLayout()
            desc_layout.addWidget(QLabel("Beschreibung:"))
            desc_input = QTextEdit()
            desc_input.setMaximumHeight(80)
            desc_input.setPlaceholderText("Optionale Beschreibung des Templates...")
            desc_layout.addWidget(desc_input)
            dlg_layout.addLayout(desc_layout)

            # Info
            info_label = QLabel(f"📊 {len(specs)} Parameter werden gespeichert.")
            info_label.setStyleSheet("color: #888; font-size: 11px;")
            dlg_layout.addWidget(info_label)

            # Buttons
            btn_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
            )
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            dlg_layout.addWidget(btn_box)

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # Template-Metadaten aktualisieren
            template['meta']['name'] = name_input.text() or f"Template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            template['meta']['description'] = desc_input.toPlainText()

            # Speichern mit FileDialog
            default_filename = f"backtest_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Template speichern",
                str(Path("config/backtest_templates") / default_filename),
                "JSON Files (*.json);;All Files (*)"
            )

            if not filename:
                return

            # Verzeichnis erstellen falls nötig
            Path(filename).parent.mkdir(parents=True, exist_ok=True)

            # Speichern
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)

            self._log(f"✅ Template gespeichert: {filename}")
            QMessageBox.information(
                self, "Template gespeichert",
                f"Template '{template['meta']['name']}' wurde gespeichert.\n\nDatei: {filename}"
            )

        except Exception as e:
            logger.exception("Failed to save template")
            self._log(f"❌ Template-Speicherung fehlgeschlagen: {e}")
            QMessageBox.critical(self, "Fehler", f"Template-Speicherung fehlgeschlagen:\n{e}")

    def _on_load_template_clicked(self) -> None:
        """
        Lädt ein gespeichertes JSON-Template.

        Stellt alle Parameter-Werte aus dem Template wieder her und
        aktualisiert die Basistabelle.
        """
        self._log("📂 Lade Template...")

        try:
            # FileDialog zum Öffnen
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Template laden",
                str(Path("config/backtest_templates")),
                "JSON Files (*.json);;All Files (*)"
            )

            if not filename:
                return

            # Template laden
            with open(filename, 'r', encoding='utf-8') as f:
                template = json.load(f)

            # Validiere Template-Struktur
            if 'parameters' not in template:
                QMessageBox.warning(
                    self, "Ungültiges Template",
                    "Die ausgewählte Datei ist kein gültiges Backtest-Template."
                )
                return

            meta = template.get('meta', {})
            params = template.get('parameters', {})
            full_specs = template.get('full_specs', [])

            # Falls full_specs vorhanden, diese für Tabelle verwenden
            if full_specs:
                specs = full_specs
            else:
                # Rekonstruiere specs aus parameters
                specs = []
                for param_key, param_data in params.items():
                    specs.append({
                        'parameter': param_key,
                        'display_name': param_key.replace('_', ' ').title(),
                        'current_value': param_data.get('value'),
                        'type': param_data.get('type', 'float'),
                        'category': param_data.get('category', 'Unknown'),
                        'subcategory': param_data.get('subcategory', ''),
                        'ui_tab': param_data.get('category', 'Unknown'),
                        'description': param_data.get('description', ''),
                        'min': param_data.get('min'),
                        'max': param_data.get('max'),
                        'variations': param_data.get('variations', []),
                    })

            # Tabelle aktualisieren
            self.config_inspector_table.setRowCount(len(specs))

            for row, spec in enumerate(specs):
                # Kategorie
                self.config_inspector_table.setItem(
                    row, 0, QTableWidgetItem(f"{spec['category']}/{spec.get('subcategory', '')}")
                )

                # Parameter
                self.config_inspector_table.setItem(
                    row, 1, QTableWidgetItem(spec.get('display_name', spec.get('parameter', '')))
                )

                # Wert
                value = spec.get('current_value')
                if spec.get('type') == 'float' and value is not None:
                    value_str = f"{value:.2f}"
                else:
                    value_str = str(value)
                value_item = QTableWidgetItem(value_str)
                value_item.setForeground(QColor("#FF9800"))  # Orange für Template-Werte
                self.config_inspector_table.setItem(row, 2, value_item)

                # UI-Tab
                self.config_inspector_table.setItem(
                    row, 3, QTableWidgetItem(spec.get('ui_tab', ''))
                )

                # Beschreibung
                description = spec.get('description', '')
                desc_item = QTableWidgetItem(description[:40] + '...' if len(description) > 40 else description)
                desc_item.setToolTip(description)
                self.config_inspector_table.setItem(row, 4, desc_item)

                # Typ
                self.config_inspector_table.setItem(
                    row, 5, QTableWidgetItem(spec.get('type', ''))
                )

                # Min/Max
                min_val = spec.get('min')
                max_val = spec.get('max')
                if min_val is not None and max_val is not None:
                    minmax_str = f"{min_val}-{max_val}"
                else:
                    minmax_str = "—"
                self.config_inspector_table.setItem(row, 6, QTableWidgetItem(minmax_str))

                # Variationen
                variations = spec.get('variations', [])
                if variations:
                    var_str = ", ".join([str(v)[:6] for v in variations[:4]])
                    if len(variations) > 4:
                        var_str += "..."
                else:
                    var_str = "—"
                self.config_inspector_table.setItem(row, 7, QTableWidgetItem(var_str))

            # Parameter Space aus Template-Parametern erstellen
            param_space = {}
            for param_key, param_data in params.items():
                value = param_data.get('value')
                variations = param_data.get('variations', [])
                if variations:
                    param_space[param_key] = variations
                elif value is not None:
                    param_space[param_key] = [value]

            self.param_space_text.setText(json.dumps(param_space, indent=2))

            template_name = meta.get('name', 'Unbekannt')
            template_desc = meta.get('description', '')
            created_at = meta.get('created_at', '')

            self._log(f"✅ Template '{template_name}' geladen")
            self._log(f"   📅 Erstellt: {created_at[:10] if created_at else 'Unbekannt'}")
            self._log(f"   📊 {len(params)} Parameter")

            if template_desc:
                self._log(f"   📝 {template_desc[:50]}...")

        except Exception as e:
            logger.exception("Failed to load template")
            self._log(f"❌ Template-Laden fehlgeschlagen: {e}")
            QMessageBox.critical(self, "Fehler", f"Template-Laden fehlgeschlagen:\n{e}")

    def _on_derive_variant_clicked(self) -> None:
        """
        Erstellt eine Variante basierend auf der aktuellen Basistabelle.

        Öffnet einen Dialog zum Anpassen einzelner Parameter-Werte,
        wobei die Basis-Werte als Ausgangspunkt dienen.
        """
        self._log("📝 Variante ableiten...")

        # Prüfe ob Daten in Tabelle vorhanden
        if self.config_inspector_table.rowCount() == 0:
            QMessageBox.warning(
                self, "Keine Basisdaten",
                "Bitte zuerst Engine Configs laden oder ein Template öffnen."
            )
            return

        try:
            # Dialog für Varianten-Erstellung
            dialog = QDialog(self)
            dialog.setWindowTitle("📝 Variante aus Basis ableiten")
            dialog.setMinimumSize(600, 500)

            dlg_layout = QVBoxLayout(dialog)

            # Info
            info = QLabel(
                "Wähle Parameter aus der Basistabelle und passe deren Werte an.\n"
                "Nicht geänderte Werte werden von der Basis übernommen."
            )
            info.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 10px;")
            dlg_layout.addWidget(info)

            # Varianten-Name
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("Varianten-Name:"))
            variant_name_input = QLineEdit()
            variant_name_input.setPlaceholderText("z.B. 'Aggressive V1'")
            name_layout.addWidget(variant_name_input)
            dlg_layout.addLayout(name_layout)

            # Parameter-Editor Tabelle (editierbar!)
            param_table = QTableWidget()
            param_table.setColumnCount(4)
            param_table.setHorizontalHeaderLabels(["Parameter", "Basis-Wert", "Neuer Wert", "Ändern?"])
            param_table.horizontalHeader().setStretchLastSection(True)

            # Extrahiere Parameter aus Basistabelle
            base_params = []
            for row in range(self.config_inspector_table.rowCount()):
                param_item = self.config_inspector_table.item(row, 1)
                value_item = self.config_inspector_table.item(row, 2)
                type_item = self.config_inspector_table.item(row, 5)

                if param_item and value_item:
                    base_params.append({
                        'name': param_item.text(),
                        'value': value_item.text(),
                        'type': type_item.text() if type_item else 'float',
                    })

            param_table.setRowCount(len(base_params))

            for row, param in enumerate(base_params):
                # Parameter-Name (read-only)
                name_item = QTableWidgetItem(param['name'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                param_table.setItem(row, 0, name_item)

                # Basis-Wert (read-only)
                base_item = QTableWidgetItem(param['value'])
                base_item.setFlags(base_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                base_item.setForeground(QColor("#888"))
                param_table.setItem(row, 1, base_item)

                # Neuer Wert (editierbar)
                new_item = QTableWidgetItem(param['value'])
                new_item.setForeground(QColor("#4CAF50"))
                param_table.setItem(row, 2, new_item)

                # Checkbox "Ändern?"
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                checkbox = QCheckBox()
                checkbox_layout.addWidget(checkbox)
                param_table.setCellWidget(row, 3, checkbox_widget)

            dlg_layout.addWidget(param_table)

            # Quick-Actions
            quick_layout = QHBoxLayout()

            # "Alle auswählen" Button
            select_all_btn = QPushButton("Alle auswählen")
            select_all_btn.clicked.connect(
                lambda: self._select_all_variant_checkboxes(param_table, True)
            )
            quick_layout.addWidget(select_all_btn)

            # "Keine auswählen" Button
            select_none_btn = QPushButton("Keine auswählen")
            select_none_btn.clicked.connect(
                lambda: self._select_all_variant_checkboxes(param_table, False)
            )
            quick_layout.addWidget(select_none_btn)

            quick_layout.addStretch()
            dlg_layout.addLayout(quick_layout)

            # Buttons
            btn_box = QDialogButtonBox()

            create_btn = QPushButton("✅ Variante erstellen")
            create_btn.clicked.connect(dialog.accept)
            btn_box.addButton(create_btn, QDialogButtonBox.ButtonRole.AcceptRole)

            cancel_btn = QPushButton("Abbrechen")
            cancel_btn.clicked.connect(dialog.reject)
            btn_box.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

            dlg_layout.addWidget(btn_box)

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # Variante aus Dialog-Daten erstellen
            variant_name = variant_name_input.text() or f"Variante_{datetime.now().strftime('%H%M%S')}"
            variant_params = {}

            for row in range(param_table.rowCount()):
                checkbox_widget = param_table.cellWidget(row, 3)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        param_name = param_table.item(row, 0).text()
                        new_value = param_table.item(row, 2).text()

                        # Versuche Wert zu konvertieren
                        try:
                            if '.' in new_value:
                                variant_params[param_name] = float(new_value)
                            elif new_value.isdigit():
                                variant_params[param_name] = int(new_value)
                            elif new_value.lower() in ('true', 'false'):
                                variant_params[param_name] = new_value.lower() == 'true'
                            else:
                                variant_params[param_name] = new_value
                        except ValueError:
                            variant_params[param_name] = new_value

            if not variant_params:
                QMessageBox.warning(
                    self, "Keine Änderungen",
                    "Bitte wähle mindestens einen Parameter zum Ändern aus."
                )
                return

            # Variante zu Parameter-Space hinzufügen
            try:
                current_space_text = self.param_space_text.toPlainText()
                if current_space_text.strip():
                    current_space = json.loads(current_space_text)
                else:
                    current_space = {}
            except json.JSONDecodeError:
                current_space = {}

            # Merge Varianten-Parameter in Space
            for param_name, param_value in variant_params.items():
                if param_name not in current_space:
                    current_space[param_name] = []
                if param_value not in current_space[param_name]:
                    current_space[param_name].append(param_value)

            self.param_space_text.setText(json.dumps(current_space, indent=2))

            self._log(f"✅ Variante '{variant_name}' erstellt mit {len(variant_params)} geänderten Parametern")
            for param, value in list(variant_params.items())[:5]:
                self._log(f"   {param}: {value}")
            if len(variant_params) > 5:
                self._log(f"   ... und {len(variant_params) - 5} weitere")

        except Exception as e:
            logger.exception("Failed to derive variant")
            self._log(f"❌ Varianten-Erstellung fehlgeschlagen: {e}")
            QMessageBox.critical(self, "Fehler", f"Varianten-Erstellung fehlgeschlagen:\n{e}")

    def _select_all_variant_checkboxes(self, table: QTableWidget, checked: bool) -> None:
        """Hilfsfunktion zum Auswählen/Abwählen aller Checkboxen."""
        for row in range(table.rowCount()):
            checkbox_widget = table.cellWidget(row, 3)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(checked)

    def _export_csv(self) -> None:
        """Exportiert Trades als CSV."""
        if not self._current_result:
            QMessageBox.warning(self, "Kein Ergebnis", "Bitte erst einen Backtest durchführen.")
            return

        try:
            from pathlib import Path
            import csv

            output_dir = Path("data/backtest_results")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = output_dir / f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            if hasattr(self._current_result, 'trades'):
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "Symbol", "Side", "Entry Price", "Exit Price", "Size", "P&L", "R-Multiple"])

                    for trade in self._current_result.trades:
                        writer.writerow([
                            trade.id,
                            trade.symbol,
                            trade.side.value,
                            trade.entry_price,
                            trade.exit_price or "",
                            trade.size,
                            trade.realized_pnl,
                            trade.r_multiple or "",
                        ])

                self._log(f"✅ Exported: {filename}")
                QMessageBox.information(self, "Export", f"Trades exportiert nach:\n{filename}")
            else:
                QMessageBox.warning(self, "Keine Trades", "Keine Trades zum Exportieren.")

        except Exception as e:
            logger.exception("Export failed")
            QMessageBox.critical(self, "Export Fehler", str(e))

    def _export_equity_csv(self) -> None:
        """Exportiert Equity Curve als CSV."""
        if not self._current_result:
            QMessageBox.warning(self, "Kein Ergebnis", "Bitte erst einen Backtest durchführen.")
            return

        try:
            import csv

            output_dir = Path("data/backtest_results")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = output_dir / f"equity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            if hasattr(self._current_result, 'equity_curve') and self._current_result.equity_curve:
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Equity", "Drawdown %", "Drawdown $"])

                    peak = self._current_result.initial_capital
                    for point in self._current_result.equity_curve:
                        ts = point.time.isoformat() if hasattr(point.time, 'isoformat') else str(point.time)
                        equity = point.equity
                        peak = max(peak, equity)
                        dd_pct = ((equity - peak) / peak) * 100 if peak > 0 else 0
                        dd_abs = equity - peak

                        writer.writerow([ts, f"{equity:.2f}", f"{dd_pct:.2f}", f"{dd_abs:.2f}"])

                self._log(f"✅ Equity Exported: {filename}")
                QMessageBox.information(self, "Export", f"Equity Curve exportiert nach:\n{filename}")
            else:
                QMessageBox.warning(self, "Keine Equity Curve", "Keine Equity Curve zum Exportieren.")

        except Exception as e:
            logger.exception("Equity export failed")
            QMessageBox.critical(self, "Export Fehler", str(e))

    def _export_json(self) -> None:
        """Exportiert Ergebnis als JSON."""
        if not self._current_result:
            QMessageBox.warning(self, "Kein Ergebnis", "Bitte erst einen Backtest durchführen.")
            return

        try:
            from pathlib import Path

            output_dir = Path("data/backtest_results")
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = output_dir / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            if hasattr(self._current_result, 'model_dump'):
                data = self._current_result.model_dump(mode='json')
            elif hasattr(self._current_result, 'dict'):
                data = self._current_result.dict()
            else:
                data = {"error": "Cannot serialize result"}

            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            self._log(f"✅ Exported: {filename}")
            QMessageBox.information(self, "Export", f"Ergebnis exportiert nach:\n{filename}")

        except Exception as e:
            logger.exception("Export failed")
            QMessageBox.critical(self, "Export Fehler", str(e))
