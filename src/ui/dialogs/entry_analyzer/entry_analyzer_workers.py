"""Entry Analyzer Background Workers.

Extracted from entry_analyzer_popup.py to keep files under 550 LOC.
Contains QThread workers for long-running operations:
- CopilotWorker: AI analysis
- ValidationWorker: K-fold validation
- BacktestWorker: Full history backtesting

Date: 2026-01-21
LOC: ~200
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class CopilotWorker(QThread):
    """Background worker for AI Copilot analysis.

    Original: entry_analyzer_popup.py:56-101

    Runs async entry analysis using GPT/Claude models to assess
    entry quality, risk/reward, and provide recommendations.
    """

    finished = pyqtSignal(object)  # CopilotResponse
    error = pyqtSignal(str)

    def __init__(
        self,
        analysis: Any,
        symbol: str,
        timeframe: str,
        validation: Any = None,
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._analysis = analysis
        self._symbol = symbol
        self._timeframe = timeframe
        self._validation = validation

    def run(self) -> None:
        """Execute AI analysis in background thread."""
        try:
            from src.analysis.visible_chart.entry_copilot import get_entry_analysis

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    get_entry_analysis(
                        self._analysis,
                        self._symbol,
                        self._timeframe,
                        self._validation,
                    )
                )
                if result:
                    self.finished.emit(result)
                else:
                    self.error.emit("AI analysis returned no result")
            finally:
                loop.close()
        except Exception as e:
            logger.exception("Copilot analysis failed")
            self.error.emit(str(e))


class ValidationWorker(QThread):
    """Background worker for walk-forward validation.

    Original: entry_analyzer_popup.py:102-131

    Runs k-fold cross-validation on entry signals to compute
    out-of-sample performance metrics and detect overfitting.
    """

    finished = pyqtSignal(object)  # ValidationResult
    error = pyqtSignal(str)

    def __init__(
        self,
        analysis: Any,
        candles: list[dict],
        parent: Any = None,
    ) -> None:
        super().__init__(parent)
        self._analysis = analysis
        self._candles = candles

    def run(self) -> None:
        """Execute validation in background thread."""
        try:
            from src.analysis.visible_chart.validation import validate_with_walkforward

            result = validate_with_walkforward(
                entries=self._analysis.entries,
                candles=self._candles,
                indicator_set=self._analysis.best_set,
            )
            self.finished.emit(result)
        except Exception as e:
            logger.exception("Validation failed")
            self.error.emit(str(e))


class BacktestWorker(QThread):
    """Background worker for full history backtesting.

    Original: entry_analyzer_popup.py:133-195

    Runs complete backtest simulation using BacktestEngine with
    strategy config, executes orders, tracks P&L, and emits results.
    """

    finished = pyqtSignal(object)  # Dict[str, Any] stats
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(
        self,
        config_path: str,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        chart_data: pd.DataFrame = None,
        data_timeframe: str = None,
        parent: Any = None
    ) -> None:
        super().__init__(parent)
        self.config_path = config_path
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.chart_data = chart_data
        self.data_timeframe = data_timeframe

    def run(self) -> None:
        """Execute backtest in background thread."""
        try:
            from src.backtesting.engine import BacktestEngine
            from src.backtesting.schema_types import TradingBotConfig

            self.progress.emit("Loading strategy configuration...")
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            config = TradingBotConfig(**config_data)

            engine = BacktestEngine()

            if self.chart_data is not None and not self.chart_data.empty:
                self.progress.emit(
                    f"Using chart data ({self.data_timeframe}, {len(self.chart_data)} candles)..."
                )
            else:
                self.progress.emit(f"Loading data for {self.symbol}...")

            self.progress.emit("Running backtest simulation...")
            results = engine.run(
                config=config,
                symbol=self.symbol,
                start_date=self.start_date,
                end_date=self.end_date,
                initial_capital=self.initial_capital,
                chart_data=self.chart_data,
                data_timeframe=self.data_timeframe
            )

            self.finished.emit(results)

        except Exception as e:
            logger.exception("Backtest failed")
            self.error.emit(str(e))
