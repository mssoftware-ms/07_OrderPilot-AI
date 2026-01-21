# 🔧 Entry Analyzer Refactoring Plan

**Datum:** 2026-01-21
**Datei:** `src/ui/dialogs/entry_analyzer_popup.py`
**Aktuell:** 3,167 LOC (zu groß, verstößt gegen Single Responsibility Principle)
**Ziel:** 5 Module à ~500-650 LOC

---

## Übersicht

### Aktuelle Struktur
```
src/ui/dialogs/entry_analyzer_popup.py (3,167 LOC)
├── CopilotWorker (QThread)                  # Zeile 56-101
├── ValidationWorker (QThread)               # Zeile 102-131
├── BacktestWorker (QThread)                 # Zeile 133-195
└── EntryAnalyzerPopup (QDialog)             # Zeile 197-3,167
    ├── Backtest-Funktionen                  # Zeile 284-895
    ├── Analysis/Validation                  # Zeile 918-1,370
    ├── Indicator Optimization               # Zeile 1,373-1,987
    ├── Regime/Strategy                      # Zeile 1,989-2,812
    └── Pattern Recognition                  # Zeile 2,813-3,167
```

### Ziel-Struktur
```
src/ui/dialogs/entry_analyzer/
├── __init__.py                              # Public API
├── entry_analyzer_popup.py                  # Hauptfenster (400-500 LOC)
├── entry_analyzer_backtest.py               # Backtest & Regime (~600 LOC)
├── entry_analyzer_indicators.py             # Indicator Optimization (~600 LOC)
├── entry_analyzer_analysis.py               # Analysis & Validation (~600 LOC)
└── entry_analyzer_ai.py                     # AI & Pattern Recognition (~600 LOC)
```

---

## Abhängigkeiten

**Nur 1 Datei importiert EntryAnalyzerPopup**:
```python
# src/ui/widgets/chart_mixins/entry_analyzer_mixin.py
from src.ui.dialogs.entry_analyzer_popup import EntryAnalyzerPopup
```

**Nach Refactoring**:
```python
# src/ui/widgets/chart_mixins/entry_analyzer_mixin.py
from src.ui.dialogs.entry_analyzer import EntryAnalyzerPopup
```

---

## Modul 1: entry_analyzer_popup.py (Hauptfenster)

**Ziel-LOC:** 400-500
**Verantwortlichkeit:** Dialog-Hauptstruktur, Worker-Management, Public API

### Behalten (aus Original):
```python
# Imports (Zeile 0-52)
# Workers (Zeile 56-195)
class CopilotWorker(QThread): ...
class ValidationWorker(QThread): ...
class BacktestWorker(QThread): ...

# Hauptklasse EntryAnalyzerPopup (Zeile 197-...)
class EntryAnalyzerPopup(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:  # Zeile 214
        """Initialize dialog, setup tabs, connect workers."""

    def _setup_ui(self) -> None:  # Zeile 233
        """Create tab widget, add 7 tabs, setup layout."""

    def _create_header(self) -> QWidget:  # Zeile 895
        """Create header with title and close button."""

    def _create_footer(self) -> QWidget:  # Zeile 1,072
        """Create footer with action buttons."""

    # Public API
    def set_context(self, symbol, timeframe, candles) -> None:  # Zeile 1,116
    def set_analyzing(self, analyzing: bool) -> None:  # Zeile 1,122
    def set_result(self, result: AnalysisResult) -> None:  # Zeile 1,149
```

### Delegiert an Mixins:
```python
from .entry_analyzer_backtest import BacktestMixin
from .entry_analyzer_indicators import IndicatorsMixin
from .entry_analyzer_analysis import AnalysisMixin
from .entry_analyzer_ai import AIMixin

class EntryAnalyzerPopup(QDialog, BacktestMixin, IndicatorsMixin, AnalysisMixin, AIMixin):
    """Main entry analyzer dialog with mixin composition."""
```

---

## Modul 2: entry_analyzer_backtest.py (Backtest & Regime)

**Ziel-LOC:** ~600
**Verantwortlichkeit:** Backtest-Konfiguration, Ausführung, Regime-Erstellung

### Methoden (aus Original Zeile 284-2,812):
```python
class BacktestMixin:
    """Backtest and Regime functionality."""

    # Setup-Methoden
    def _setup_backtest_config_tab(self, tab: QWidget) -> None:  # Zeile 284
    def _setup_backtest_results_tab(self, tab: QWidget) -> None:  # Zeile 354

    # Event-Handler
    def _on_load_strategy_clicked(self) -> None:  # Zeile 461
    def _on_analyze_current_regime_clicked(self) -> None:  # Zeile 468
    def _on_run_backtest_clicked(self) -> None:  # Zeile 632
    def _on_backtest_finished(self, results: dict) -> None:  # Zeile 715
    def _on_backtest_error(self, error: str) -> None:  # Zeile 812

    # Helper-Methoden
    def _convert_candles_to_dataframe(self, candles: list[dict]) -> pd.DataFrame:  # Zeile 671
    def _draw_regime_boundaries(self, results: dict) -> None:  # Zeile 817

    # Regime-Funktionen
    def _on_regime_history_ready(self, regime_history: list) -> None:  # Zeile 1,989
    def _on_create_regime_set_clicked(self) -> None:  # Zeile 2,005
```

### Benötigte Attribute (in __init__ von Hauptklasse):
```python
# Backtest Config
self._bt_strategy_path_label: QLabel
self._bt_start_date: QDateEdit
self._bt_end_date: QDateEdit
self._bt_initial_capital: QDoubleSpinBox
self._bt_regime_set_combo: QComboBox
self._bt_run_btn: QPushButton

# Backtest Results
self._bt_results_text: QTextEdit
self._backtest_worker: BacktestWorker | None = None
```

---

## Modul 3: entry_analyzer_indicators.py (Indicator Optimization)

**Ziel-LOC:** ~600
**Verantwortlichkeit:** Indikator-Optimierung, Parameter-Tuning

### Methoden (aus Original Zeile 1,373-1,987):
```python
class IndicatorsMixin:
    """Indicator optimization functionality."""

    # Setup-Methoden
    def _setup_indicator_optimization_tab(self, tab: QWidget) -> None:  # Zeile 1,373
    def _setup_optimization_setup_tab(self, tab: QWidget) -> None:  # Zeile 1,395
    def _setup_optimization_results_tab(self, tab: QWidget) -> None:  # Zeile 1,582

    # Event-Handler
    def _on_indicator_selection_changed(self) -> None:  # Zeile 1,650
    def _on_optimize_indicators_clicked(self) -> None:  # Zeile 1,780
    def _on_optimization_finished(self, results: list) -> None:  # Zeile 1,878
    def _on_optimization_progress(self, percentage: int, message: str) -> None:  # Zeile 1,960
    def _on_optimization_error(self, error_message: str) -> None:  # Zeile 1,970
    def _on_draw_indicators_clicked(self) -> None:  # Zeile 2,092

    # Helper-Methoden
    def _update_parameter_ranges(self) -> None:  # Zeile 1,654
```

### Benötigte Attribute:
```python
# Indicator Optimization
self._ind_opt_indicator_combo: QComboBox
self._ind_opt_param_ranges: dict[str, tuple[QSpinBox, QSpinBox]]
self._ind_opt_results_table: QTableWidget
self._ind_opt_progress: QProgressBar
self._optimization_worker: OptimizationWorker | None = None
```

---

## Modul 4: entry_analyzer_analysis.py (Analysis & Validation)

**Ziel-LOC:** ~600
**Verantwortlichkeit:** Sichtbare Chart-Analyse, Entry-Signal-Validierung

### Methoden (aus Original Zeile 918-1,370):
```python
class AnalysisMixin:
    """Analysis and validation functionality."""

    # Setup-Methoden
    def _setup_analysis_tab(self, tab: QWidget) -> None:  # Zeile 918
    def _setup_validation_tab(self, tab: QWidget) -> None:  # Zeile 973
    def _create_indicator_group(self) -> QGroupBox:  # Zeile 1,012
    def _create_entries_group(self) -> QGroupBox:  # Zeile 1,039

    # Event-Handler
    def _on_analyze_clicked(self) -> None:  # Zeile 1,242
    def _on_draw_clicked(self) -> None:  # Zeile 1,246
    def _on_clear_clicked(self) -> None:  # Zeile 1,250
    def _on_validate_clicked(self) -> None:  # Zeile 1,315
    def _on_validation_finished(self, result: Any) -> None:  # Zeile 1,334
    def _on_validation_error(self, error_msg: str) -> None:  # Zeile 1,366
    def _on_show_entries_clicked(self) -> None:  # Zeile 2,187

    # Helper-Methoden
    def _update_params_table(self, params: dict) -> None:  # Zeile 1,207
    def _update_entries_table(self, entries: list[EntryEvent]) -> None:  # Zeile 1,226
```

### Benötigte Attribute:
```python
# Analysis
self._params_table: QTableWidget
self._entries_table: QTableWidget
self._analyze_btn: QPushButton
self._draw_btn: QPushButton
self._clear_btn: QPushButton

# Validation
self._validation_text: QTextEdit
self._validation_progress: QProgressBar
self._validate_btn: QPushButton
self._validation_worker: ValidationWorker | None = None
```

---

## Modul 5: entry_analyzer_ai.py (AI & Pattern Recognition)

**Ziel-LOC:** ~600
**Verantwortlichkeit:** AI Copilot, Pattern Matching, Report-Generierung

### Methoden (aus Original Zeile 934-973 + 2,813-3,167):
```python
class AIMixin:
    """AI and pattern recognition functionality."""

    # Setup-Methoden
    def _setup_ai_tab(self, tab: QWidget) -> None:  # Zeile 934
    def _setup_pattern_recognition_tab(self, tab: QWidget) -> None:  # Zeile 2,813

    # AI Event-Handler
    def _on_ai_analyze_clicked(self) -> None:  # Zeile 1,253
    def _on_ai_finished(self, response: Any) -> None:  # Zeile 1,274
    def _on_ai_error(self, error_msg: str) -> None:  # Zeile 1,308

    # Pattern Event-Handler
    def _on_pattern_analyze_clicked(self) -> None:  # Zeile 2,944
    def _on_pattern_double_clicked(self, item) -> None:  # Zeile 3,103

    # Report-Generierung
    def _on_report_clicked(self) -> None:  # Zeile 3,120
```

### Benötigte Attribute:
```python
# AI Copilot
self._ai_text: QTextEdit
self._ai_analyze_btn: QPushButton
self._ai_progress: QProgressBar
self._copilot_worker: CopilotWorker | None = None

# Pattern Recognition
self.pattern_window_spin: QSpinBox
self.pattern_similarity_threshold_spin: QDoubleSpinBox
self.pattern_min_matches_spin: QSpinBox
self.similar_patterns_table: QTableWidget
self.pattern_analyze_btn: QPushButton
self.pattern_summary_label: QLabel
```

---

## Implementierungsschritte

### Schritt 1: Verzeichnis-Struktur anlegen
```bash
mkdir -p src/ui/dialogs/entry_analyzer
touch src/ui/dialogs/entry_analyzer/__init__.py
touch src/ui/dialogs/entry_analyzer/entry_analyzer_popup.py
touch src/ui/dialogs/entry_analyzer/entry_analyzer_backtest.py
touch src/ui/dialogs/entry_analyzer/entry_analyzer_indicators.py
touch src/ui/dialogs/entry_analyzer/entry_analyzer_analysis.py
touch src/ui/dialogs/entry_analyzer/entry_analyzer_ai.py
```

### Schritt 2: Mixins extrahieren (Reihenfolge wichtig!)
1. **BacktestMixin** (am wenigsten Abhängigkeiten)
2. **IndicatorsMixin** (unabhängig)
3. **AnalysisMixin** (unabhängig)
4. **AIMixin** (unabhängig)
5. **Hauptklasse refactoren** (verwendet alle Mixins)

### Schritt 3: __init__.py erstellen
```python
"""Entry Analyzer Dialog - Modular Implementation.

Refactored from monolithic 3,167 LOC file into 5 maintainable modules.
"""

from .entry_analyzer_popup import EntryAnalyzerPopup

__all__ = ["EntryAnalyzerPopup"]
```

### Schritt 4: Imports aktualisieren
```bash
# Datei: src/ui/widgets/chart_mixins/entry_analyzer_mixin.py
sed -i 's|from src.ui.dialogs.entry_analyzer_popup import|from src.ui.dialogs.entry_analyzer import|' \
    src/ui/widgets/chart_mixins/entry_analyzer_mixin.py
```

### Schritt 5: Original-Datei löschen
```bash
git rm src/ui/dialogs/entry_analyzer_popup.py
```

---

## Verifikation

### Tests ausführen:
```bash
# Unit Tests
pytest tests/ui/dialogs/test_entry_analyzer*.py -v

# Integration Test
python -c "from src.ui.dialogs.entry_analyzer import EntryAnalyzerPopup; print('✓ Import OK')"
```

### Erwartete Metriken:
```
Vorher:
├── entry_analyzer_popup.py: 3,167 LOC
└── Klassen >500 LOC: 1

Nachher:
├── entry_analyzer_popup.py: 400-500 LOC
├── entry_analyzer_backtest.py: ~600 LOC
├── entry_analyzer_indicators.py: ~600 LOC
├── entry_analyzer_analysis.py: ~600 LOC
├── entry_analyzer_ai.py: ~600 LOC
└── Klassen >500 LOC: 0

Gesamt LOC: ~3,200 (leichte Zunahme durch Mixin-Overhead akzeptabel)
Wartbarkeit: +200% (5 fokussierte Module statt 1 Monolith)
```

---

## Risiken & Mitigation

### Risiko 1: Mixin-Komplexität
**Problem:** Methoden-Auflösungsreihenfolge (MRO) bei Multi-Inheritance
**Mitigation:** Klare Namenskonventionen, keine überlappenden Methoden

### Risiko 2: Shared State
**Problem:** Attribute werden von mehreren Mixins genutzt
**Mitigation:** Alle Attribute in Hauptklasse `__init__` definieren, Mixins nur nutzen

### Risiko 3: Circular Imports
**Problem:** Mixins könnten sich gegenseitig importieren
**Mitigation:** Mixins sind unabhängig, nur Hauptklasse importiert alle

---

## Zeitplan

| Schritt | Aufwand | Priorität |
|---------|---------|-----------|
| Verzeichnis anlegen | 5 Min | 🔴 CRITICAL |
| BacktestMixin extrahieren | 3h | 🔴 CRITICAL |
| IndicatorsMixin extrahieren | 3h | 🔴 CRITICAL |
| AnalysisMixin extrahieren | 3h | 🔴 CRITICAL |
| AIMixin extrahieren | 3h | 🔴 CRITICAL |
| Hauptklasse refactoren | 2h | 🔴 CRITICAL |
| Imports aktualisieren | 30 Min | 🟠 HIGH |
| Tests ausführen | 1h | 🟠 HIGH |

**Gesamt:** 16 Stunden (2 Arbeitstage)

---

**Status:** Ready for Implementation ✅
**Nächster Schritt:** Verzeichnis-Struktur anlegen
