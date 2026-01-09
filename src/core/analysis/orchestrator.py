"""Orchestrator for the Deep Analysis Run.

Coordinates:
1. Data Collection (Multi-TF) using HistoryManager
2. Feature Calculation
3. Payload Assembly
4. LLM Request (real AI integration)

REFACTORED: Split into 6 helper modules using composition pattern:
- orchestrator_data.py: Data collection and conversion
- orchestrator_features.py: Feature calculation with indicators
- orchestrator_llm.py: LLM integration and prompt formatting
- orchestrator_report.py: Report formatting and generation
- orchestrator_worker.py: Main worker class with run workflow
- orchestrator.py: Main export
"""

from .orchestrator_worker import AnalysisWorker

__all__ = ["AnalysisWorker"]
