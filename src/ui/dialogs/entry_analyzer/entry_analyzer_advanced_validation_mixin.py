"""Entry Analyzer - Advanced Validation Mixin.

Implements:
- Out-of-Sample Split Validation
- Market Phase Analysis (bull/bear/sideways)
- Walk-Forward Analysis (simplified)

Uses lightweight helpers in `src/backtesting/advanced_validation.py`.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Dict

import pandas as pd
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QLineEdit,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.backtesting.advanced_validation import (
    OutOfSampleValidator,
    MarketPhaseAnalyzer,
    WalkForwardAnalyzer,
)
from src.backtesting.engine import BacktestEngine
from src.backtesting.config_adapter import BacktestConfigAdapter
from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AdvancedValidationMixin:
    """Advanced validation (OOS, Market Phases, Walk-Forward)."""

    _candles: List[Dict]
    _symbol: str
    _timeframe: str
    _adv_bt_config_path: str | None

    def _setup_advanced_validation_tab(self, tab: QWidget) -> None:
        layout = QVBoxLayout(tab)

        # ----- OOS -----
        oos_group = QGroupBox("Out-of-Sample Validation")
        oos_layout = QHBoxLayout(oos_group)
        self._oos_split_spin = QSpinBox()
        self._oos_split_spin.setRange(50, 90)
        self._oos_split_spin.setValue(70)
        self._oos_split_spin.setSuffix(" % train")
        oos_layout.addWidget(QLabel("Train Split"))
        oos_layout.addWidget(self._oos_split_spin)
        self._oos_run_btn = QPushButton(get_icon("play_arrow"), "Run OOS")
        self._oos_run_btn.clicked.connect(self._on_run_oos)
        oos_layout.addWidget(self._oos_run_btn)
        self._oos_result_label = QLabel("Train/Test: n/a")
        oos_layout.addWidget(self._oos_result_label)
        oos_layout.addStretch()
        layout.addWidget(oos_group)

        # ----- Market Phases -----
        phase_group = QGroupBox("Market Phase Analysis")
        phase_layout = QVBoxLayout(phase_group)
        controls = QHBoxLayout()
        self._phase_window_spin = QSpinBox()
        self._phase_window_spin.setRange(15, 120)
        self._phase_window_spin.setValue(30)
        self._phase_window_spin.setSuffix(" days")
        controls.addWidget(QLabel("Window"))
        controls.addWidget(self._phase_window_spin)
        self._phase_run_btn = QPushButton(get_icon("play_arrow"), "Detect Phases")
        self._phase_run_btn.clicked.connect(self._on_run_phases)
        controls.addWidget(self._phase_run_btn)
        controls.addStretch()
        phase_layout.addLayout(controls)

        self._phase_table = QTableWidget()
        self._phase_table.setColumnCount(4)
        self._phase_table.setHorizontalHeaderLabels(["Phase", "Start", "End", "Confidence"])
        phase_layout.addWidget(self._phase_table)
        layout.addWidget(phase_group)

        # ----- Walk Forward -----
        wf_group = QGroupBox("Walk-Forward Analysis")
        wf_layout = QHBoxLayout(wf_group)
        self._wf_train_spin = QSpinBox()
        self._wf_train_spin.setRange(30, 180)
        self._wf_train_spin.setValue(60)
        self._wf_train_spin.setSuffix(" days")
        self._wf_test_spin = QSpinBox()
        self._wf_test_spin.setRange(7, 60)
        self._wf_test_spin.setValue(15)
        self._wf_test_spin.setSuffix(" days")
        self._wf_step_spin = QSpinBox()
        self._wf_step_spin.setRange(5, 60)
        self._wf_step_spin.setValue(15)
        self._wf_step_spin.setSuffix(" days")
        self._wf_run_btn = QPushButton(get_icon("play_arrow"), "Run Walk-Forward")
        self._wf_run_btn.clicked.connect(self._on_run_wf)
        self._wf_summary_label = QLabel("WFE: n/a")

        wf_layout.addWidget(QLabel("Train"))
        wf_layout.addWidget(self._wf_train_spin)
        wf_layout.addWidget(QLabel("Test"))
        wf_layout.addWidget(self._wf_test_spin)
        wf_layout.addWidget(QLabel("Step"))
        wf_layout.addWidget(self._wf_step_spin)
        wf_layout.addWidget(self._wf_run_btn)
        wf_layout.addWidget(self._wf_summary_label)
        wf_layout.addStretch()
        layout.addWidget(wf_group)

        self._wf_table = QTableWidget()
        self._wf_table.setColumnCount(5)
        self._wf_table.setHorizontalHeaderLabels(
            ["Window", "Period", "Train Score", "Test Score", "WFE"]
        )
        layout.addWidget(self._wf_table)

        # ----- Backtest Config selection -----
        cfg_group = QGroupBox("Backtest Config (optional, uses BacktestEngine)")
        cfg_layout = QHBoxLayout(cfg_group)
        self._adv_bt_path_edit = QLineEdit()
        self._adv_bt_path_edit.setPlaceholderText("03_JSON/Trading_Bot/your_config.json")
        browse_btn = QPushButton(get_icon("folder_open"), "Browse")
        browse_btn.clicked.connect(self._on_browse_bt_config)
        cfg_layout.addWidget(self._adv_bt_path_edit)
        cfg_layout.addWidget(browse_btn)
        layout.addWidget(cfg_group)

        layout.addStretch()

    def _on_browse_bt_config(self) -> None:
        project_root = Path(__file__).parents[4]
        default_dir = project_root / "03_JSON" / "Trading_Bot"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backtest Config JSON",
            str(default_dir),
            "JSON Files (*.json);;All Files (*)",
        )
        if file_path:
            self._adv_bt_path_edit.setText(file_path)
            self._adv_bt_config_path = file_path

    # ------------------------------------------------------------------ actions
    def _on_run_oos(self) -> None:
        df = self._get_current_df()
        if df is None:
            return
        split = self._oos_split_spin.value() / 100.0
        try:
            res = OutOfSampleValidator(df, split_ratio=split).validate()
            self._oos_result_label.setText(
                f"Train {res.train_score:.1f} | Test {res.test_score:.1f} | Degradation {res.degradation_pct:.1f}%"
            )
        except Exception as e:
            QMessageBox.critical(self, "OOS failed", str(e))
            logger.exception("OOS validation failed")

    def _on_run_phases(self) -> None:
        df = self._get_current_df()
        if df is None:
            return
        window = self._phase_window_spin.value()
        try:
            analyzer = MarketPhaseAnalyzer(df)
            phases = analyzer.detect_phases(window_days=window)
            self._phase_table.setRowCount(0)
            for phase in phases:
                row = self._phase_table.rowCount()
                self._phase_table.insertRow(row)
                self._phase_table.setItem(row, 0, QTableWidgetItem(phase.phase))
                self._phase_table.setItem(row, 1, QTableWidgetItem(str(phase.start.date())))
                self._phase_table.setItem(row, 2, QTableWidgetItem(str(phase.end.date())))
                self._phase_table.setItem(row, 3, QTableWidgetItem(f"{phase.confidence:.2f}"))
        except Exception as e:
            QMessageBox.critical(self, "Phase detection failed", str(e))
            logger.exception("Phase detection failed")

    def _on_run_wf(self) -> None:
        df = self._get_current_df()
        if df is None:
            return
        train = self._wf_train_spin.value()
        test = self._wf_test_spin.value()
        step = self._wf_step_spin.value()
        try:
            wf = WalkForwardAnalyzer(df, train_days=train, test_days=test, step_days=step)
            res = wf.run()
            self._wf_summary_label.setText(
                f"WFE {res['wfe']:.2f} | Consistency {res['consistency']:.2f} | Robust {res['robustness']*100:.1f}%"
            )
            self._wf_table.setRowCount(0)
            for win in res["windows"]:
                row = self._wf_table.rowCount()
                self._wf_table.insertRow(row)
                self._wf_table.setItem(row, 0, QTableWidgetItem(str(win["window"])))
                period = f"{win['period'][0].date()} → {win['period'][1].date()}"
                self._wf_table.setItem(row, 1, QTableWidgetItem(period))
                self._wf_table.setItem(row, 2, QTableWidgetItem(f"{win['train_score']:.1f}"))
                self._wf_table.setItem(row, 3, QTableWidgetItem(f"{win['test_score']:.1f}"))
                self._wf_table.setItem(row, 4, QTableWidgetItem(f"{win['wfe']:.2f}"))
        except Exception as e:
            QMessageBox.critical(self, "Walk-Forward failed", str(e))
            logger.exception("Walk-Forward failed")

    # ------------------------------------------------------------------ helpers
    def _get_current_df(self) -> pd.DataFrame | None:
        """Return candles as DataFrame; fallback to historical if live empty."""
        candles = getattr(self, "_candles", None) or []
        if not candles:
            try:
                from src.ui.dialogs.entry_analyzer.entry_analyzer_indicator_optimization_v2_mixin import (
                    IndicatorOptimizationV2Mixin,
                )
                if isinstance(self, IndicatorOptimizationV2Mixin):
                    candles = self._load_indicator_hist_candles()
            except Exception:
                candles = []

        if not candles:
            QMessageBox.warning(
                self,
                "No Data",
                "Es sind keine Candles geladen (weder Live noch Historical).",
            )
            return None
        df = pd.DataFrame(candles)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp").sort_index()
        return df

    # ------------------------------------------------------------------ scoring helper
    def _score_df(self, df: pd.DataFrame) -> float:
        """Try BacktestEngine if config provided; fallback to heuristic."""
        cfg_path = getattr(self, "_adv_bt_config_path", None) or self._adv_bt_path_edit.text().strip()
        if cfg_path:
            try:
                cfg = BacktestConfigAdapter.from_file(cfg_path)
                engine = BacktestEngine()
                res = engine.run(
                    cfg,
                    symbol=getattr(self, "_symbol", "BTCUSDT"),
                    chart_data=df,
                    data_timeframe=getattr(self, "_timeframe", "1m"),
                )
                perf = res.get("performance") or res.get("metrics") or {}
                # fallback heuristic on result structure
                score = float(perf.get("score", perf.get("sharpe", 0))) if isinstance(perf, dict) else 0.0
                if score:
                    return score
            except Exception as e:
                logger.warning("BacktestEngine scoring failed, fallback to heuristic: %s", e)
        # Fallback heuristic
        from src.backtesting.advanced_validation import _compute_score

        return _compute_score(df)
