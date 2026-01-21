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

# Import worker from separate module
from .backtest_tab_worker import BatchTestWorker

# ENGINE CONFIG IMPORTS
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



# Import mixins
from .backtest_tab_ui_setup_mixin import BacktestTabUISetupMixin
from .backtest_tab_ui_results_mixin import BacktestTabUIResultsMixin
from .backtest_tab_ui_batch_mixin import BacktestTabUIBatchMixin
from .backtest_tab_callbacks_mixin import BacktestTabCallbacksMixin
from .backtest_tab_config_mixin import BacktestTabConfigMixin
from .backtest_tab_update_mixin import BacktestTabUpdateMixin
from .backtest_tab_export_mixin import BacktestTabExportMixin

class BacktestTab(
    BacktestTabUISetupMixin,
    BacktestTabUIResultsMixin,
    BacktestTabUIBatchMixin,
    BacktestTabCallbacksMixin,
    BacktestTabConfigMixin,
    BacktestTabUpdateMixin,
    BacktestTabExportMixin,
    QWidget
):
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


    def get_available_indicator_sets(self) -> list[Dict[str, Any]]:
        """Delegate to BacktestConfigVariants."""
        from .backtest_config_variants import BacktestConfigVariants
        variants = BacktestConfigVariants(self)
        return variants.get_available_indicator_sets()


    def generate_ai_test_variants(self, base_spec: list[Dict], num_variants: int = 10) -> list[Dict[str, Any]]:
        """Delegate to BacktestConfigVariants."""
        from .backtest_config_variants import BacktestConfigVariants
        variants = BacktestConfigVariants(self)
        return variants.generate_ai_test_variants(base_spec, num_variants)


    def set_history_manager(self, history_manager: "HistoryManager") -> None:
        """Setzt den History Manager."""
        self._history_manager = history_manager


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


    def _get_signal_callback(self) -> Optional[Callable]:
        """
        Erstellt Signal-Callback für Backtest.

        Simplified: Nutzt IndicatorEngine Cache (kein eigenes Pre-Calculation nötig).

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
            from src.core.trading_bot import EntryScoreEngine
            from src.core.indicators import IndicatorEngine, IndicatorConfig, IndicatorType
            import pandas as pd

            # Build Entry Config from engine settings
            entry_config = self._build_entry_config(engine_configs)

            # Engine Settings
            min_score_for_signal = engine_configs.get('entry_score', {}).get('min_score_for_entry', 0.50)
            tp_atr_mult = engine_configs.get('trigger_exit', {}).get('tp_atr_multiplier', 2.0)
            sl_atr_mult = engine_configs.get('trigger_exit', {}).get('sl_atr_multiplier', 1.5)

            # Create engines (IndicatorEngine has built-in cache!)
            indicator_engine = IndicatorEngine(cache_size=500)
            entry_engine = EntryScoreEngine(config=entry_config) if entry_config else EntryScoreEngine()

            def backtest_signal_callback(candle, history_1m, mtf_data):
                """Simplified signal callback for backtest."""
                if history_1m is None or len(history_1m) < 50:
                    return None

                try:
                    # Calculate indicators (IndicatorEngine caches automatically!)
                    df = self._calculate_indicators(history_1m, indicator_engine)

                    # Calculate entry score
                    score_result = entry_engine.calculate(
                        df,
                        regime_result=None,  # Skip regime for speed
                        symbol="BTCUSDT",
                        timeframe="1m"
                    )

                    if not score_result or score_result.final_score < min_score_for_signal:
                        return None

                    # Get ATR for SL/TP
                    atr = df['atr_14'].iloc[-1] if 'atr_14' in df.columns else (candle.close * 0.02)
                    current_price = candle.close
                    direction_str = score_result.direction.value if hasattr(score_result.direction, 'value') else str(score_result.direction)

                    # Generate signal
                    if direction_str == "LONG":
                        return {
                            "action": "buy",
                            "stop_loss": current_price - (atr * sl_atr_mult),
                            "take_profit": current_price + (atr * tp_atr_mult),
                            "sl_distance": atr * sl_atr_mult,
                            "leverage": 1,
                            "reason": f"Score: {score_result.final_score:.2f}",
                            "confidence": score_result.final_score,
                            "atr": atr,
                        }
                    elif direction_str == "SHORT":
                        return {
                            "action": "sell",
                            "stop_loss": current_price + (atr * sl_atr_mult),
                            "take_profit": current_price - (atr * tp_atr_mult),
                            "sl_distance": atr * sl_atr_mult,
                            "leverage": 1,
                            "reason": f"Score: {score_result.final_score:.2f}",
                            "confidence": score_result.final_score,
                            "atr": atr,
                        }

                except Exception as e:
                    logger.warning(f"Signal generation error: {e}")

                return None

            logger.info("Signal callback created with simplified logic")
            return backtest_signal_callback

        except ImportError as e:
            logger.warning(f"Could not create signal callback: {e}")
            return None


            def backtest_signal_callback(candle, history_1m, mtf_data):
                """Simplified signal callback for backtest."""
                if history_1m is None or len(history_1m) < 50:
                    return None

                try:
                    # Calculate indicators (IndicatorEngine caches automatically!)
                    df = self._calculate_indicators(history_1m, indicator_engine)

                    # Calculate entry score
                    score_result = entry_engine.calculate(
                        df,
                        regime_result=None,  # Skip regime for speed
                        symbol="BTCUSDT",
                        timeframe="1m"
                    )

                    if not score_result or score_result.final_score < min_score_for_signal:
                        return None

                    # Get ATR for SL/TP
                    atr = df['atr_14'].iloc[-1] if 'atr_14' in df.columns else (candle.close * 0.02)
                    current_price = candle.close
                    direction_str = score_result.direction.value if hasattr(score_result.direction, 'value') else str(score_result.direction)

                    # Generate signal
                    if direction_str == "LONG":
                        return {
                            "action": "buy",
                            "stop_loss": current_price - (atr * sl_atr_mult),
                            "take_profit": current_price + (atr * tp_atr_mult),
                            "sl_distance": atr * sl_atr_mult,
                            "leverage": 1,
                            "reason": f"Score: {score_result.final_score:.2f}",
                            "confidence": score_result.final_score,
                            "atr": atr,
                        }
                    elif direction_str == "SHORT":
                        return {
                            "action": "sell",
                            "stop_loss": current_price + (atr * sl_atr_mult),
                            "take_profit": current_price - (atr * tp_atr_mult),
                            "sl_distance": atr * sl_atr_mult,
                            "leverage": 1,
                            "reason": f"Score: {score_result.final_score:.2f}",
                            "confidence": score_result.final_score,
                            "atr": atr,
                        }

                except Exception as e:
                    logger.warning(f"Signal generation error: {e}")

                return None

            logger.info("Signal callback created with simplified logic")
            return backtest_signal_callback

        except ImportError as e:
            logger.warning(f"Could not create signal callback: {e}")
            return None


    def _calculate_indicators(self, df, indicator_engine):
        """
        Calculate indicators with IndicatorEngine (uses internal cache).

        Simplified: No custom cache logic needed!
        """
        from src.core.indicators import IndicatorConfig, IndicatorType
        import pandas as pd

        result = df.copy()

        try:
            # EMA 20, 50
            for period in [20, 50]:
                config = IndicatorConfig(IndicatorType.EMA, {"period": period, "price": "close"}, use_talib=True)
                result[f"ema_{period}"] = indicator_engine.calculate(result, config).values

            # RSI 14
            config = IndicatorConfig(IndicatorType.RSI, {"period": 14}, use_talib=True)
            result["rsi_14"] = indicator_engine.calculate(result, config).values

            # ADX 14
            config = IndicatorConfig(IndicatorType.ADX, {"period": 14}, use_talib=True)
            adx_result = indicator_engine.calculate(result, config)
            if isinstance(adx_result.values, pd.DataFrame):
                result["adx_14"] = adx_result.values["adx"]
                result["plus_di"] = adx_result.values.get("plus_di", 0)
                result["minus_di"] = adx_result.values.get("minus_di", 0)

            # ATR 14
            config = IndicatorConfig(IndicatorType.ATR, {"period": 14}, use_talib=True)
            result["atr_14"] = indicator_engine.calculate(result, config).values

        except Exception as e:
            logger.warning(f"Indicator calculation error: {e}")

        return result


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


    def _select_all_variant_checkboxes(self, table: QTableWidget, checked: bool) -> None:
        """Hilfsfunktion zum Auswählen/Abwählen aller Checkboxen."""
        for row in range(table.rowCount()):
            checkbox_widget = table.cellWidget(row, 3)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(checked)


