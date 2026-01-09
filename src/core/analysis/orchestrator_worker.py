"""Orchestrator Worker - Main worker class with run workflow.

Refactored from 666 LOC monolith using composition pattern.

Module 6/6 of orchestrator.py split.

Contains:
- AnalysisWorker: QThread for background analysis
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QThread, pyqtSignal

if TYPE_CHECKING:
    from src.core.analysis.context import AnalysisContext

from src.core.indicators.engine import IndicatorEngine
from .orchestrator_data import OrchestratorData
from .orchestrator_features import OrchestratorFeatures
from .orchestrator_llm import OrchestratorLLM
from .orchestrator_report import OrchestratorReport

logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """Background worker for the analysis process."""

    status_update = pyqtSignal(str)  # "Loading data...", "Done"
    progress_update = pyqtSignal(int)  # 0-100
    result_ready = pyqtSignal(str)  # Markdown report
    error_occurred = pyqtSignal(str)

    def __init__(self, context: "AnalysisContext"):
        super().__init__()
        self.context = context
        self._loop = None
        self.indicator_engine = IndicatorEngine()
        self._ai_service = None
        self._llm_analysis: str | None = None  # Stores LLM response

        # Composition pattern
        self._data = OrchestratorData(parent=self)
        self._features = OrchestratorFeatures(parent=self)
        self._llm = OrchestratorLLM(parent=self)
        self._report = OrchestratorReport(parent=self)

    def run(self):
        """Main workflow execution."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            self.status_update.emit("Initialisierung...")
            self.progress_update.emit(5)

            # 1. Validation & Setup
            strat = self.context.get_selected_strategy()
            tfs = self.context.get_active_timeframes()
            hm = self.context.history_manager
            symbol = self.context._current_symbol

            if not strat or not tfs:
                raise ValueError("Strategie oder Timeframes nicht konfiguriert.")
            if not hm:
                raise ValueError("HistoryManager nicht verfügbar (Kontext fehlt).")

            # 2. Data Collection (Real)
            self.status_update.emit(f"Lade Marktdaten für {len(tfs)} Timeframes...")

            fetched_data = self._loop.run_until_complete(
                self._data.collect_data(tfs, symbol, hm)
            )

            if not fetched_data:
                raise ValueError("Keine Daten für die gewählten Timeframes empfangen.")

            # 3. Feature Engineering
            self.status_update.emit("Berechne Indikatoren & Features...")
            features = self._features.calculate_features(fetched_data)
            self.progress_update.emit(70)

            # 4. LLM Generation (Real AI Integration)
            self.status_update.emit("Generiere KI-Analyse (Deep Reasoning)...")
            try:
                self._llm_analysis = self._loop.run_until_complete(
                    self._llm.call_llm(strat.name, symbol, features)
                )
                if self._llm_analysis:
                    logger.info("LLM analysis completed successfully")
                else:
                    logger.warning("LLM returned empty response, using fallback report")
            except Exception as e:
                logger.error(f"LLM analysis failed: {e}", exc_info=True)
                self._llm_analysis = None
                self.status_update.emit(f"LLM-Analyse fehlgeschlagen: {e}")
            self.progress_update.emit(90)

            # 5. Finalize
            self.progress_update.emit(100)
            self.status_update.emit("Fertig.")

            # Generate Report based on REAL fetched metadata
            report = self._report.generate_report(strat.name, symbol, features)
            self.result_ready.emit(report)

            self._loop.close()

        except Exception as e:
            self.error_occurred.emit(str(e))
            if self._loop:
                self._loop.close()
