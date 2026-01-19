# Strategy Concept Window - Implementation Plan

**Ziel:** Separates Fenster für Chart-Pattern-basierte Trading-Strategien mit nachgewiesenen Erfolgsraten.

**Architektur:** Eigenständiges QDialog-Fenster mit 2 Tabs:
1. **Mustererkennung** (Pattern Recognition) - Detection & Visualisierung
2. **Pattern Integration** (Strategy Mapping) - Verknüpfung Pattern → Trading-Strategie → Erfolgsrate

**Daten-Basis:** `Chartmuster_Strategien_Erfolgsraten.md` (Research 2020-2025)

---

## 🎯 Übersicht

### Was ist Strategy Concept?

**Strategy Concept** ist ein eigenständiges Analyse-Fenster, das:
- Chart-Patterns erkennt (Phase 1: Top 5 nach Erfolgsrate)
- Patterns mit erprobten Trading-Strategien verknüpft
- Erfolgsraten und Best Practices anzeigt
- CEL-kompatible Exports für Trading-Rules generiert

**Unterschied zu Entry Analyzer:**
- Entry Analyzer: Echtzeit-Entry-Bewertung für OFFENEN Trade
- Strategy Concept: Historische Pattern-Analyse für STRATEGIE-ENTWICKLUNG

---

## 📋 Feature-Übersicht

### Tab 1: Mustererkennung
- Pattern Detection für Phase 1 Patterns:
  - Cup and Handle (95% Erfolgsrate)
  - Head & Shoulders (89-93%)
  - Double Top/Bottom (88%)
  - Triple Bottom (87%)
  - Ascending Triangle (83% in Bull-Markets)
- Pivot Engine (ZigZag/ATR) - **wiederverwendet aus Entry Analyzer Plan**
- Pattern-Liste mit Scores
- Chart-Overlay für Visualisierung
- Export zu JSON/CSV

### Tab 2: Pattern Integration
- Pattern → Strategy Mapping Tabelle
- Erfolgsraten-Anzeige (Research-basiert)
- Best Practices pro Pattern
- Risk-Reward-Berechnung
- Trade-Setup-Generierung (für CEL-System)

---

## 🏗️ Architektur

### Projekt-Struktur

```
src/
├── analysis/patterns/
│   ├── __init__.py
│   ├── pivot_engine.py              # Wiederverwendet
│   ├── base_detector.py              # Wiederverwendet
│   ├── reversal_patterns.py         # Erweitert (Cup & Handle, Triple Bottom)
│   ├── continuation_patterns.py     # NEU (Ascending Triangle)
│   └── pattern_exporter.py          # Wiederverwendet
│
├── strategies/
│   ├── __init__.py
│   ├── pattern_strategy_mapper.py   # NEU - Pattern → Strategy Mapping
│   └── strategy_models.py           # NEU - Pydantic Models für Strategien
│
└── ui/
    ├── dialogs/
    │   └── strategy_concept_window.py  # NEU - Hauptfenster
    └── widgets/
        ├── pattern_recognition_widget.py  # NEU - Tab 1
        └── pattern_integration_widget.py  # NEU - Tab 2

tests/
├── patterns/
│   ├── test_continuation_patterns.py  # NEU
│   └── test_reversal_patterns.py      # Erweitert
└── strategies/
    └── test_pattern_strategy_mapper.py  # NEU
```

---

## ♻️ Code-Wiederverwendung aus Entry Analyzer

**Siehe:** `CODE_REUSE_ANALYSIS.md` für vollständige Analyse.

### Wiederverwendbare Komponenten

**1. Shared Widgets erstellen (`src/ui/widgets/pattern_analysis_widgets.py`):**
- `PatternAnalysisSettings` - Pattern-Analyse-Einstellungen (Window Size, Similarity Threshold, etc.)
- `PatternResultsDisplay` - Statistik-Anzeige (Win Rate, Avg Return, Confidence)
- `PatternMatchesTable` - Tabelle für Pattern-Matches (8 Spalten)

**2. Chart Data Helper (`src/ui/utils/chart_data_helper.py`):**
- `ChartDataHelper.get_bars_from_chart()` - Extrahiert HistoricalBar-Objekte aus Chart Widget

**3. Direkt wiederverwendbar:**
- `PatternService` (src/core/pattern_db/pattern_service.py) - Async Pattern-Analyse
- Pattern Detection Base Classes aus IMPLEMENTATION_PLAN_Entry_Analyzer.md

### Vorteile

✅ **~500 Zeilen** UI-Code wiederverwendet statt dupliziert
✅ **Konsistente UX** zwischen Entry Analyzer und Strategy Concept
✅ **Single Source of Truth** für Pattern-Analyse-UI
✅ **Einfacheres Testing** - Test Widget einmal, nutze überall

### Implementierungs-Strategie

1. **Phase 0 (neu):** Shared Widgets erstellen (vor Phase 1)
2. **Tab 1 (Mustererkennung):** Nutzt alle Shared Widgets
3. **Entry Analyzer Refactor (optional):** Nach Strategy Concept funktioniert

---

## 🚀 Phase 0: Shared Widgets (2-3h) **NEU**

### ✅ Schritt 0.1: Pattern Analysis Widgets (1-1.5h)

**Datei:** `src/ui/widgets/pattern_analysis_widgets.py`

```python
"""Reusable widgets for pattern analysis (shared between Entry Analyzer and Strategy Concept)."""

from __future__ import annotations

from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import pyqtSignal, Qt
import logging

logger = logging.getLogger(__name__)


class PatternAnalysisSettings(QWidget):
    """Reusable pattern analysis settings panel."""

    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup all settings widgets."""
        layout = QFormLayout(self)

        # Window size for pattern matching
        self.window_spin = QSpinBox()
        self.window_spin.setRange(10, 100)
        self.window_spin.setValue(20)
        self.window_spin.setSuffix(" bars")
        self.window_spin.valueChanged.connect(self._on_settings_changed)
        layout.addRow("Window Size:", self.window_spin)

        # Similarity threshold (0.5-0.99)
        self.similarity_spin = QDoubleSpinBox()
        self.similarity_spin.setRange(0.5, 0.99)
        self.similarity_spin.setValue(0.80)
        self.similarity_spin.setSingleStep(0.05)
        self.similarity_spin.setDecimals(2)
        self.similarity_spin.valueChanged.connect(self._on_settings_changed)
        layout.addRow("Similarity Threshold:", self.similarity_spin)

        # Minimum matches
        self.min_matches_spin = QSpinBox()
        self.min_matches_spin.setRange(3, 50)
        self.min_matches_spin.setValue(10)
        self.min_matches_spin.valueChanged.connect(self._on_settings_changed)
        layout.addRow("Min Matches:", self.min_matches_spin)

        # Signal direction
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["LONG", "SHORT"])
        self.direction_combo.currentTextChanged.connect(self._on_settings_changed)
        layout.addRow("Signal Direction:", self.direction_combo)

        # Cross-symbol search
        self.cross_symbol_cb = QCheckBox("Search across symbols")
        self.cross_symbol_cb.stateChanged.connect(self._on_settings_changed)
        layout.addRow("", self.cross_symbol_cb)

    def _on_settings_changed(self):
        """Emit settings_changed signal when any setting changes."""
        self.settings_changed.emit(self.get_settings())

    def get_settings(self) -> dict:
        """Return current settings as dict."""
        return {
            'window_size': self.window_spin.value(),
            'similarity_threshold': self.similarity_spin.value(),
            'min_matches': self.min_matches_spin.value(),
            'signal_direction': self.direction_combo.currentText().lower(),
            'cross_symbol': self.cross_symbol_cb.isChecked()
        }


class PatternResultsDisplay(QWidget):
    """Reusable pattern analysis results display."""

    # Recommendation color scheme
    RECOMMENDATION_COLORS = {
        "strong_buy": "#4caf50",
        "buy": "#8bc34a",
        "neutral": "#ffeb3b",
        "avoid": "#ff9800",
        "strong_avoid": "#f44336"
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Setup results display widgets."""
        layout = QVBoxLayout(self)

        # Summary label
        self.summary_label = QLabel("No analysis yet")
        self.summary_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 10px; "
            "background-color: #f5f5f5; border-radius: 5px;"
        )
        layout.addWidget(self.summary_label)

        # Statistics group
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)

        self.matches_count_label = QLabel("0")
        stats_layout.addRow("Matches Found:", self.matches_count_label)

        self.win_rate_label = QLabel("0%")
        stats_layout.addRow("Win Rate:", self.win_rate_label)

        self.avg_return_label = QLabel("0%")
        stats_layout.addRow("Avg Return:", self.avg_return_label)

        self.confidence_label = QLabel("0%")
        stats_layout.addRow("Confidence:", self.confidence_label)

        self.avg_similarity_label = QLabel("0.00")
        stats_layout.addRow("Avg Similarity:", self.avg_similarity_label)

        self.recommendation_label = QLabel("-")
        stats_layout.addRow("Recommendation:", self.recommendation_label)

        layout.addWidget(stats_group)

    def update_from_analysis(self, analysis) -> None:
        """
        Update display with analysis results.

        Args:
            analysis: PatternAnalysis object or None
        """
        if analysis is None:
            self.summary_label.setText("❌ Analysis failed - not enough data")
            self.summary_label.setStyleSheet(
                "font-size: 14px; font-weight: bold; padding: 10px; "
                "background-color: #ffebee; border-radius: 5px;"
            )
            return

        # Update summary with color coding
        bg_color = self.RECOMMENDATION_COLORS.get(analysis.recommendation, "#f5f5f5")
        self.summary_label.setText(
            f"✓ Analysis Complete: {analysis.recommendation.upper().replace('_', ' ')}"
        )
        self.summary_label.setStyleSheet(
            f"font-size: 14px; font-weight: bold; padding: 10px; "
            f"background-color: {bg_color}; border-radius: 5px; color: white;"
        )

        # Update statistics
        self.matches_count_label.setText(str(analysis.similar_patterns_count))
        self.win_rate_label.setText(f"{analysis.win_rate:.1%}")
        self.avg_return_label.setText(f"{analysis.avg_return:+.2f}%")
        self.confidence_label.setText(f"{analysis.confidence:.1%}")
        self.avg_similarity_label.setText(f"{analysis.avg_similarity_score:.2f}")
        self.recommendation_label.setText(analysis.recommendation.replace('_', ' ').title())

        logger.info(
            f"Pattern analysis displayed: {analysis.similar_patterns_count} matches, "
            f"{analysis.win_rate:.1%} win rate"
        )

    def clear(self) -> None:
        """Clear all displayed results."""
        self.summary_label.setText("No analysis yet")
        self.summary_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; padding: 10px; "
            "background-color: #f5f5f5; border-radius: 5px;"
        )
        self.matches_count_label.setText("0")
        self.win_rate_label.setText("0%")
        self.avg_return_label.setText("0%")
        self.confidence_label.setText("0%")
        self.avg_similarity_label.setText("0.00")
        self.recommendation_label.setText("-")


class PatternMatchesTable(QTableWidget):
    """Reusable table for displaying pattern matches."""

    pattern_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_table()

    def _setup_table(self):
        """Setup table structure."""
        self.setColumnCount(8)
        self.setHorizontalHeaderLabels([
            "Symbol",
            "Timeframe",
            "Date",
            "Similarity",
            "Trend",
            "Profitable",
            "Return %",
            "Outcome"
        ])

        # Table styling
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)

    def populate_from_matches(self, matches: list, max_rows: int = 20) -> None:
        """
        Populate table with pattern matches.

        Args:
            matches: List of match objects with attributes (symbol, timeframe, timestamp, etc.)
            max_rows: Maximum number of rows to display
        """
        self.setRowCount(0)

        for match in matches[:max_rows]:
            row = self.rowCount()
            self.insertRow(row)

            # Column 0: Symbol
            self.setItem(row, 0, QTableWidgetItem(match.symbol))

            # Column 1: Timeframe
            self.setItem(row, 1, QTableWidgetItem(match.timeframe))

            # Column 2: Date
            date_str = (
                match.timestamp.strftime("%Y-%m-%d %H:%M")
                if hasattr(match.timestamp, 'strftime')
                else str(match.timestamp)
            )
            self.setItem(row, 2, QTableWidgetItem(date_str))

            # Column 3: Similarity
            self.setItem(row, 3, QTableWidgetItem(f"{match.score:.3f}"))

            # Column 4: Trend
            self.setItem(row, 4, QTableWidgetItem(match.trend_direction.upper()))

            # Column 5: Profitable (checkmark/X)
            profitable_str = "✓" if match.was_profitable else "✗"
            self.setItem(row, 5, QTableWidgetItem(profitable_str))

            # Column 6: Return %
            self.setItem(row, 6, QTableWidgetItem(f"{match.return_pct:+.2f}%"))

            # Column 7: Outcome (colored)
            outcome = "PROFIT" if match.was_profitable else "LOSS"
            outcome_item = QTableWidgetItem(outcome)
            outcome_item.setForeground(
                Qt.GlobalColor.green if match.was_profitable else Qt.GlobalColor.red
            )
            self.setItem(row, 7, outcome_item)

    def clear_table(self) -> None:
        """Clear all rows from table."""
        self.setRowCount(0)
```

**Checklist:**
- [ ] Create file `src/ui/widgets/pattern_analysis_widgets.py`
- [ ] Implement `PatternAnalysisSettings` class
- [ ] Implement `PatternResultsDisplay` class
- [ ] Implement `PatternMatchesTable` class
- [ ] Test widgets independently

---

### ✅ Schritt 0.2: Chart Data Helper (30min)

**Datei:** `src/ui/utils/chart_data_helper.py`

```python
"""Helper utilities for accessing chart data from parent widgets."""

from __future__ import annotations

from typing import Optional, List, Tuple
from PyQt6.QtWidgets import QWidget
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class ChartDataHelper:
    """Helper for accessing chart data from parent widgets."""

    @staticmethod
    def get_bars_from_chart(
        widget: QWidget,
        window_size: int = 100
    ) -> Tuple[Optional[List], Optional[str], Optional[str]]:
        """
        Extract HistoricalBar objects from parent chart widget.

        Args:
            widget: Widget with parent().chart_widget attribute
            window_size: Number of bars to include (plus buffer of 50)

        Returns:
            Tuple of (bars, symbol, timeframe) or (None, None, None) if data unavailable

        Example:
            >>> bars, symbol, timeframe = ChartDataHelper.get_bars_from_chart(self, window_size=20)
            >>> if bars is None:
            ...     QMessageBox.warning(self, "No Data", "No chart data available")
            ...     return
        """
        # Check for chart widget
        if not hasattr(widget.parent(), 'chart_widget'):
            logger.warning("Parent widget has no chart_widget attribute")
            return None, None, None

        chart_widget = widget.parent().chart_widget

        if not hasattr(chart_widget, 'data') or chart_widget.data is None:
            logger.warning("Chart widget has no data")
            return None, None, None

        chart_data = chart_widget.data
        if len(chart_data) == 0:
            logger.warning("Chart data is empty")
            return None, None, None

        # Import here to avoid circular imports
        from src.core.market_data.types import HistoricalBar

        # Convert to HistoricalBar objects
        bars = []
        try:
            for timestamp, row in chart_data.tail(window_size + 50).iterrows():
                bar = HistoricalBar(
                    timestamp=timestamp,
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=float(row.get('volume', 0))
                )
                bars.append(bar)
        except Exception as e:
            logger.exception(f"Failed to convert chart data to HistoricalBar objects: {e}")
            return None, None, None

        # Get symbol and timeframe
        symbol = getattr(chart_widget, 'current_symbol', 'UNKNOWN')
        timeframe = getattr(chart_widget, 'timeframe', '1m')

        logger.info(f"Extracted {len(bars)} bars for {symbol} ({timeframe})")
        return bars, symbol, timeframe
```

**Checklist:**
- [ ] Create directory `src/ui/utils/` (if not exists)
- [ ] Create file `src/ui/utils/chart_data_helper.py`
- [ ] Implement `ChartDataHelper.get_bars_from_chart()` static method
- [ ] Add error handling and logging
- [ ] Write unit tests

---

### ✅ Schritt 0.3: Unit Tests für Shared Widgets (1h)

**Datei:** `tests/ui/widgets/test_pattern_analysis_widgets.py`

```python
"""Unit tests for reusable pattern analysis widgets."""

import pytest
from PyQt6.QtWidgets import QApplication
from src.ui.widgets.pattern_analysis_widgets import (
    PatternAnalysisSettings,
    PatternResultsDisplay,
    PatternMatchesTable
)


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_pattern_analysis_settings_defaults(qapp):
    """Test PatternAnalysisSettings default values."""
    widget = PatternAnalysisSettings()

    settings = widget.get_settings()
    assert settings['window_size'] == 20
    assert settings['similarity_threshold'] == 0.80
    assert settings['min_matches'] == 10
    assert settings['signal_direction'] == 'long'
    assert settings['cross_symbol'] is False


def test_pattern_analysis_settings_changes(qapp, qtbot):
    """Test PatternAnalysisSettings emits signals on changes."""
    widget = PatternAnalysisSettings()

    with qtbot.waitSignal(widget.settings_changed, timeout=1000) as blocker:
        widget.window_spin.setValue(30)

    emitted_settings = blocker.args[0]
    assert emitted_settings['window_size'] == 30


def test_pattern_results_display_clear(qapp):
    """Test PatternResultsDisplay clear method."""
    widget = PatternResultsDisplay()

    # Set some values
    widget.matches_count_label.setText("50")
    widget.win_rate_label.setText("75%")

    # Clear
    widget.clear()

    assert widget.matches_count_label.text() == "0"
    assert widget.win_rate_label.text() == "0%"


def test_pattern_matches_table_populate(qapp):
    """Test PatternMatchesTable population."""
    from dataclasses import dataclass
    from datetime import datetime

    @dataclass
    class MockMatch:
        symbol: str
        timeframe: str
        timestamp: datetime
        score: float
        trend_direction: str
        was_profitable: bool
        return_pct: float

    table = PatternMatchesTable()

    matches = [
        MockMatch("BTCUSDT", "1h", datetime.now(), 0.85, "up", True, 5.2),
        MockMatch("ETHUSDT", "1h", datetime.now(), 0.78, "down", False, -2.1)
    ]

    table.populate_from_matches(matches)

    assert table.rowCount() == 2
    assert table.item(0, 0).text() == "BTCUSDT"
    assert table.item(1, 0).text() == "ETHUSDT"
```

**Checklist:**
- [ ] Create directory `tests/ui/widgets/` (if not exists)
- [ ] Create file `test_pattern_analysis_widgets.py`
- [ ] Test PatternAnalysisSettings (defaults, changes, signals)
- [ ] Test PatternResultsDisplay (clear, update)
- [ ] Test PatternMatchesTable (populate, clear)
- [ ] Run tests: `pytest tests/ui/widgets/test_pattern_analysis_widgets.py`

---

## 🚀 Phase 1: Core Infrastructure (4-6h)

### ✅ Schritt 1.1: Strategy Models (Pydantic) (1-2h)

**Datei:** `src/strategies/strategy_models.py`

```python
"""Pydantic models for trading strategies and pattern integration."""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PatternCategory(str, Enum):
    """Pattern category classification."""
    REVERSAL = "REVERSAL"
    CONTINUATION = "CONTINUATION"
    SMART_MONEY = "SMART_MONEY"
    BREAKOUT = "BREAKOUT"
    HARMONIC = "HARMONIC"


class StrategyType(str, Enum):
    """Trading strategy types."""
    BREAKOUT_LONG = "BREAKOUT_LONG"
    BREAKOUT_SHORT = "BREAKOUT_SHORT"
    BREAKDOWN_SHORT = "BREAKDOWN_SHORT"
    RETEST_LONG = "RETEST_LONG"
    RETEST_SHORT = "RETEST_SHORT"
    REVERSAL_LONG = "REVERSAL_LONG"
    REVERSAL_SHORT = "REVERSAL_SHORT"


class TradingStrategy(BaseModel):
    """Trading strategy with proven success metrics."""

    strategy_type: StrategyType
    description: str = Field(..., description="Strategy description in German")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate in percent")
    avg_profit: str = Field(..., description="Average profit range (e.g., '35-50%')")

    # Best Practices
    best_practices: List[str] = Field(default_factory=list, description="List of best practices")

    # Risk Management
    stop_loss_placement: str = Field(..., description="Stop loss placement rule")
    target_calculation: str = Field(..., description="Target price calculation")
    risk_reward_ratio: str = Field(default="1:2", description="Minimum risk-reward ratio")

    # Confirmation Indicators
    volume_confirmation: bool = Field(default=True, description="Requires volume confirmation")
    rsi_condition: Optional[str] = Field(None, description="RSI condition (e.g., '>50')")
    macd_confirmation: bool = Field(default=False, description="MACD crossover confirmation")

    # Additional Filters
    trend_direction: Optional[str] = Field(None, description="Required trend direction")
    timeframe_preference: Optional[str] = Field(None, description="Preferred timeframe")


class PatternStrategyMapping(BaseModel):
    """Mapping between chart pattern and trading strategy."""

    pattern_type: str = Field(..., description="Pattern type (e.g., 'cup_and_handle')")
    pattern_name: str = Field(..., description="Human-readable pattern name")
    category: PatternCategory

    # Strategy
    strategy: TradingStrategy

    # Research Data
    research_period: str = Field(default="2020-2025", description="Research time period")
    study_references: List[str] = Field(default_factory=list, description="Research sources")

    # Phase Classification (for implementation priority)
    implementation_phase: int = Field(default=1, ge=1, le=3, description="Implementation priority (1=highest)")


# Pre-defined strategies from research data
PATTERN_STRATEGIES: Dict[str, PatternStrategyMapping] = {
    "cup_and_handle": PatternStrategyMapping(
        pattern_type="cup_and_handle",
        pattern_name="Cup and Handle",
        category=PatternCategory.REVERSAL,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Breakout-Long nach Handle",
            success_rate=95.0,
            avg_profit="35-50%",
            best_practices=[
                "Höchste Erfolgsrate aller Patterns",
                "U-förmiger Cup (keine V-Form)",
                "Handle: 1/3 der Cup-Tiefe",
                "Mindest-Formation: 7 Wochen"
            ],
            stop_loss_placement="Unterhalb Handle-Low",
            target_calculation="Cup-Tiefe vom Breakout-Punkt addieren",
            risk_reward_ratio="1:3",
            volume_confirmation=True,
            rsi_condition=">50",
            trend_direction="BULL"
        ),
        study_references=[
            "VT Markets Chart Patterns Guide 2025",
            "Liberated Stock Trader - 12 Data-Proven Chart Patterns"
        ]
    ),

    "head_and_shoulders_top": PatternStrategyMapping(
        pattern_type="head_and_shoulders_top",
        pattern_name="Head & Shoulders (Top)",
        category=PatternCategory.REVERSAL,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKDOWN_SHORT,
            description="Breakdown-Short nach Neckline-Bruch",
            success_rate=91.0,  # Average of 89-93%
            avg_profit="23%",
            best_practices=[
                "Warte auf komplette Formation",
                "Volumen-Bestätigung am Bruch",
                "MACD Crossover erhöht Rate auf 81%",
                "Target: Höhe der Schulter abgetragen"
            ],
            stop_loss_placement="Oberhalb rechter Schulter",
            target_calculation="Abstand Head zu Neckline vom Breakpoint subtrahieren",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            macd_confirmation=True,
            trend_direction="BEAR"
        ),
        study_references=[
            "Quantified Strategies - Head and Shoulders Backtest",
            "Trader Vue - H&S Complete Guide"
        ]
    ),

    "double_top": PatternStrategyMapping(
        pattern_type="double_top",
        pattern_name="Double Top",
        category=PatternCategory.REVERSAL,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKDOWN_SHORT,
            description="Short bei Neckline-Break + Retest",
            success_rate=88.0,
            avg_profit="15-20%",
            best_practices=[
                "Beide Tops auf gleichem Level (±2%)",
                "Volumen am 2. Top niedriger",
                "Bearish Divergence (RSI) verstärkt Signal",
                "Target: Höhe des Patterns"
            ],
            stop_loss_placement="Oberhalb höheres Top",
            target_calculation="Abstand Tops zu Neckline vom Breakpoint subtrahieren",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            rsi_condition="Bearish Divergence",
            trend_direction="BEAR"
        )
    ),

    "double_bottom": PatternStrategyMapping(
        pattern_type="double_bottom",
        pattern_name="Double Bottom",
        category=PatternCategory.REVERSAL,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Long bei Neckline-Break + Retest",
            success_rate=88.0,
            avg_profit="18-25%",
            best_practices=[
                "Beide Bottoms auf gleichem Level (±2%)",
                "Volumen am 2. Bottom höher",
                "Bullish Divergence verstärkt",
                "Mit Retest-Filter: Höhere Win-Rate"
            ],
            stop_loss_placement="Unterhalb tieferes Bottom",
            target_calculation="Abstand Bottoms zu Neckline vom Breakpoint addieren",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            rsi_condition="Bullish Divergence",
            trend_direction="BULL"
        )
    ),

    "triple_bottom": PatternStrategyMapping(
        pattern_type="triple_bottom",
        pattern_name="Triple Bottom",
        category=PatternCategory.REVERSAL,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Long bei Widerstandsbruch",
            success_rate=87.0,
            avg_profit="20-28%",
            best_practices=[
                "Drei Tests auf gleichem Support",
                "Abnehmendes Volumen bei Tests",
                "Explosion am Breakout",
                "Sehr seltenes, aber zuverlässiges Pattern"
            ],
            stop_loss_placement="Unterhalb Triple-Bottom-Low",
            target_calculation="Abstand Bottom zu Resistance vom Breakpoint addieren",
            risk_reward_ratio="1:2.5",
            volume_confirmation=True,
            rsi_condition=">50",
            trend_direction="BULL"
        )
    ),

    "ascending_triangle": PatternStrategyMapping(
        pattern_type="ascending_triangle",
        pattern_name="Ascending Triangle",
        category=PatternCategory.CONTINUATION,
        implementation_phase=1,
        strategy=TradingStrategy(
            strategy_type=StrategyType.BREAKOUT_LONG,
            description="Long-Breakout über Resistance",
            success_rate=83.0,  # In bull markets
            avg_profit="25-35%",
            best_practices=[
                "Höchste Rate in Bull-Märkten (83%)",
                "Flacher Widerstand + steigende Lows",
                "Volumen-Bestätigung zwingend",
                "Mit Retest: Weniger Trades, höhere Win-Rate"
            ],
            stop_loss_placement="Unterhalb letzter steigender Low",
            target_calculation="Triangle-Höhe vom Breakpoint addieren",
            risk_reward_ratio="1:2",
            volume_confirmation=True,
            trend_direction="BULL",
            timeframe_preference="Bull Market"
        ),
        study_references=[
            "Liberated Stock Trader - Ascending Triangle 83% Win Rate",
            "Quantified Strategies - Breakout Triangle Strategy"
        ]
    )
}
```

---

### ✅ Schritt 1.2: Pattern-Strategy Mapper (1-2h)

**Datei:** `src/strategies/pattern_strategy_mapper.py`

```python
"""Pattern-Strategy Mapper - Link detected patterns to trading strategies."""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.analysis.patterns.base_detector import Pattern
from src.strategies.strategy_models import (
    PatternStrategyMapping,
    PATTERN_STRATEGIES,
    TradingStrategy
)

logger = logging.getLogger(__name__)


@dataclass
class TradeSetup:
    """Complete trade setup for a detected pattern."""

    # Pattern Info
    pattern: Pattern
    pattern_strategy: PatternStrategyMapping

    # Entry Details
    entry_price: float
    entry_condition: str

    # Exit Details
    stop_loss: float
    target_price: float
    risk_reward_ratio: float

    # Confirmation
    confirmation_pending: List[str]  # e.g., ["Volume spike", "RSI >50"]
    confidence_score: float  # 0-100

    # Additional Info
    notes: str


class PatternStrategyMapper:
    """Map detected patterns to trading strategies with success rates."""

    def __init__(self):
        """Initialize mapper with pre-defined strategies."""
        self.strategies = PATTERN_STRATEGIES

    def get_strategy(self, pattern_type: str) -> Optional[PatternStrategyMapping]:
        """Get trading strategy for a pattern type.

        Args:
            pattern_type: Pattern type string (e.g., "cup_and_handle")

        Returns:
            PatternStrategyMapping if found, else None
        """
        return self.strategies.get(pattern_type)

    def map_pattern_to_strategy(
        self,
        pattern: Pattern
    ) -> Optional[PatternStrategyMapping]:
        """Map a detected Pattern to its trading strategy.

        Args:
            pattern: Detected Pattern object

        Returns:
            PatternStrategyMapping if pattern has known strategy, else None
        """
        return self.get_strategy(pattern.pattern_type)

    def generate_trade_setup(
        self,
        pattern: Pattern,
        current_price: float
    ) -> Optional[TradeSetup]:
        """Generate complete trade setup for a pattern.

        Args:
            pattern: Detected Pattern object
            current_price: Current market price

        Returns:
            TradeSetup object if strategy exists, else None
        """
        strategy_mapping = self.map_pattern_to_strategy(pattern)

        if not strategy_mapping:
            logger.warning(f"No strategy found for pattern type: {pattern.pattern_type}")
            return None

        strategy = strategy_mapping.strategy

        # Calculate entry, stop, target based on pattern and strategy rules
        entry_price = self._calculate_entry_price(pattern, current_price, strategy)
        stop_loss = self._calculate_stop_loss(pattern, entry_price, strategy)
        target_price = self._calculate_target(pattern, entry_price, strategy)

        # Risk-Reward
        risk = abs(entry_price - stop_loss)
        reward = abs(target_price - entry_price)
        rr_ratio = reward / risk if risk > 0 else 0

        # Confirmation checks
        confirmation_pending = self._check_confirmations(pattern, strategy)

        # Confidence score (based on pattern score + confirmation status)
        confidence = self._calculate_confidence(pattern, confirmation_pending)

        return TradeSetup(
            pattern=pattern,
            pattern_strategy=strategy_mapping,
            entry_price=entry_price,
            entry_condition=strategy.description,
            stop_loss=stop_loss,
            target_price=target_price,
            risk_reward_ratio=rr_ratio,
            confirmation_pending=confirmation_pending,
            confidence_score=confidence,
            notes=f"Success Rate: {strategy.success_rate}% | Avg Profit: {strategy.avg_profit}"
        )

    def _calculate_entry_price(
        self,
        pattern: Pattern,
        current_price: float,
        strategy: TradingStrategy
    ) -> float:
        """Calculate entry price based on pattern and strategy.

        Simplified implementation - can be extended with more logic.
        """
        # For breakout strategies: Entry at breakout level
        if "BREAKOUT" in strategy.strategy_type.value:
            # Use pattern's end price (approximation)
            if pattern.pivots:
                return pattern.pivots[-1].price
            return current_price

        # For retest strategies: Entry at retest level
        elif "RETEST" in strategy.strategy_type.value:
            if pattern.pivots:
                return pattern.pivots[-2].price if len(pattern.pivots) > 1 else current_price
            return current_price

        # Default: Current price
        return current_price

    def _calculate_stop_loss(
        self,
        pattern: Pattern,
        entry_price: float,
        strategy: TradingStrategy
    ) -> float:
        """Calculate stop loss based on strategy rules.

        Uses pattern structure and strategy.stop_loss_placement.
        """
        # Simplified: Use pattern score as percentage distance
        # In production: Parse stop_loss_placement string and calculate exact level
        sl_distance_pct = (100 - pattern.score) / 100 * 0.05  # 0-5% based on score

        if pattern.direction_bias.value == "UP":
            return entry_price * (1 - sl_distance_pct)
        else:
            return entry_price * (1 + sl_distance_pct)

    def _calculate_target(
        self,
        pattern: Pattern,
        entry_price: float,
        strategy: TradingStrategy
    ) -> float:
        """Calculate target price based on strategy rules.

        Uses pattern height and strategy.target_calculation.
        """
        # Simplified: Use avg_profit midpoint
        avg_profit_str = strategy.avg_profit.replace("%", "")

        if "-" in avg_profit_str:
            low, high = avg_profit_str.split("-")
            avg_pct = (float(low) + float(high)) / 2 / 100
        else:
            avg_pct = float(avg_profit_str) / 100

        if pattern.direction_bias.value == "UP":
            return entry_price * (1 + avg_pct)
        else:
            return entry_price * (1 - avg_pct)

    def _check_confirmations(
        self,
        pattern: Pattern,
        strategy: TradingStrategy
    ) -> List[str]:
        """Check which confirmations are pending.

        Returns list of pending confirmations (empty if all confirmed).
        """
        pending = []

        if strategy.volume_confirmation:
            pending.append("Volume Spike (2x avg)")

        if strategy.rsi_condition:
            pending.append(f"RSI {strategy.rsi_condition}")

        if strategy.macd_confirmation:
            pending.append("MACD Crossover")

        return pending

    def _calculate_confidence(
        self,
        pattern: Pattern,
        confirmation_pending: List[str]
    ) -> float:
        """Calculate overall confidence score.

        Args:
            pattern: Pattern with score (0-100)
            confirmation_pending: List of pending confirmations

        Returns:
            Confidence score (0-100)
        """
        # Start with pattern score
        confidence = pattern.score

        # Reduce by 10% for each pending confirmation
        penalty = len(confirmation_pending) * 10
        confidence = max(0, confidence - penalty)

        return confidence

    def get_all_phase1_patterns(self) -> List[str]:
        """Get list of all Phase 1 pattern types.

        Returns:
            List of pattern type strings
        """
        return [
            pattern_type
            for pattern_type, mapping in self.strategies.items()
            if mapping.implementation_phase == 1
        ]
```

---

### ✅ Schritt 1.3: Strategy Concept Window (Hauptfenster) (2h)

**Datei:** `src/ui/dialogs/strategy_concept_window.py`

```python
"""Strategy Concept Window - Separate window for pattern-based trading strategies.

This window provides:
- Tab 1: Pattern Recognition (Detection & Visualization)
- Tab 2: Pattern Integration (Strategy Mapping & Success Rates)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

if TYPE_CHECKING:
    from src.analysis.patterns.base_detector import Pattern

logger = logging.getLogger(__name__)


class StrategyConceptWindow(QDialog):
    """Strategy Concept Window - Pattern-based trading strategies.

    Separate window with 2 tabs:
    - Mustererkennung (Pattern Recognition)
    - Pattern Integration (Strategy Mapping)
    """

    # Signals
    patterns_detected = pyqtSignal(list)  # List[Pattern]

    def __init__(self, parent=None, chart_window=None):
        """Initialize Strategy Concept Window.

        Args:
            parent: Parent widget
            chart_window: Reference to ChartWindow for data access
        """
        super().__init__(parent)

        self.chart_window = chart_window
        self.detected_patterns: List[Pattern] = []

        self._setup_ui()
        self._connect_signals()

        logger.info("Strategy Concept Window initialized")

    def _setup_ui(self):
        """Setup UI components."""
        self.setWindowTitle("Strategy Concept - Pattern-Based Trading Strategies")
        self.setMinimumSize(1200, 800)

        # Main layout
        layout = QVBoxLayout(self)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Tab Widget
        self.tabs = QTabWidget()

        # Import tab widgets (will be implemented in next steps)
        from src.ui.widgets.pattern_recognition_widget import PatternRecognitionWidget
        from src.ui.widgets.pattern_integration_widget import PatternIntegrationWidget

        # Tab 1: Mustererkennung
        self.pattern_recognition_tab = PatternRecognitionWidget(
            parent=self,
            chart_window=self.chart_window
        )
        self.tabs.addTab(self.pattern_recognition_tab, "📊 Mustererkennung")

        # Tab 2: Pattern Integration
        self.pattern_integration_tab = PatternIntegrationWidget(
            parent=self
        )
        self.tabs.addTab(self.pattern_integration_tab, "🎯 Pattern Integration")

        layout.addWidget(self.tabs)

        # Footer with action buttons
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QLabel:
        """Create header with title and info."""
        header = QLabel(
            "Strategy Concept\n"
            "Pattern-basierte Trading-Strategien mit nachgewiesenen Erfolgsraten (Research 2020-2025)"
        )
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        header.setFont(font)

        header.setStyleSheet(
            "background-color: #2e3440; "
            "color: #88c0d0; "
            "padding: 15px; "
            "border-radius: 5px; "
            "margin-bottom: 10px;"
        )

        return header

    def _create_footer(self) -> QHBoxLayout:
        """Create footer with action buttons."""
        footer_layout = QHBoxLayout()

        # Info button
        info_btn = QPushButton("ℹ️ Info")
        info_btn.clicked.connect(self._show_info)
        footer_layout.addWidget(info_btn)

        footer_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        footer_layout.addWidget(close_btn)

        return footer_layout

    def _connect_signals(self):
        """Connect internal signals."""
        # When patterns are detected in Tab 1, update Tab 2
        self.pattern_recognition_tab.patterns_detected.connect(
            self._on_patterns_detected
        )

    def _on_patterns_detected(self, patterns: List[Pattern]):
        """Handle patterns detected in Tab 1.

        Args:
            patterns: List of detected patterns
        """
        self.detected_patterns = patterns
        logger.info(f"Strategy Concept: {len(patterns)} patterns detected")

        # Update Pattern Integration tab with new patterns
        self.pattern_integration_tab.update_patterns(patterns)

        # Emit signal
        self.patterns_detected.emit(patterns)

    def _show_info(self):
        """Show info dialog about Strategy Concept."""
        QMessageBox.information(
            self,
            "Strategy Concept Info",
            "**Strategy Concept** ist ein Analyse-Tool für Pattern-basierte Trading-Strategien.\n\n"
            "**Tab 1 - Mustererkennung:**\n"
            "• Pattern Detection (Phase 1: Top 5 nach Erfolgsrate)\n"
            "• Chart-Overlay-Visualisierung\n"
            "• Export zu JSON/CSV\n\n"
            "**Tab 2 - Pattern Integration:**\n"
            "• Pattern → Trading-Strategie Mapping\n"
            "• Erfolgsraten aus Research (2020-2025)\n"
            "• Trade-Setup-Generierung\n"
            "• Best Practices pro Pattern\n\n"
            "**Daten-Basis:**\n"
            "Chartmuster_Strategien_Erfolgsraten.md\n"
            "(Quellen: VT Markets, Quantified Strategies, Liberated Stock Trader, u.a.)"
        )
```

---

**Checklist (Phase 1):**
- [ ] `strategy_models.py` implementiert (Pydantic Models)
- [ ] PATTERN_STRATEGIES Dictionary mit Phase 1 Patterns gefüllt
- [ ] `pattern_strategy_mapper.py` implementiert (TradeSetup-Generierung)
- [ ] `strategy_concept_window.py` implementiert (Hauptfenster)
- [ ] Tab 1 Widget-Skeleton erstellt
- [ ] Tab 2 Widget-Skeleton erstellt
- [ ] ChartWindow Integration (Menü/Button)

---

## 🚀 Phase 2: Tab 1 - Mustererkennung (6-8h)

**Ziel:** Pattern Recognition Widget mit Reuse der Shared Widgets aus Phase 0.

### ✅ Schritt 2.1: Pattern Recognition Widget (4-5h)

**Datei:** `src/ui/widgets/pattern_recognition_widget.py`

```python
"""Tab 1: Pattern Recognition Widget for Strategy Concept Window."""

from __future__ import annotations

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QProgressBar, QGroupBox, QLabel
)
from PyQt6.QtCore import pyqtSignal
import asyncio
import logging

from src.ui.widgets.pattern_analysis_widgets import (
    PatternAnalysisSettings,
    PatternResultsDisplay,
    PatternMatchesTable
)
from src.ui.utils.chart_data_helper import ChartDataHelper
from src.core.pattern_db.pattern_service import PatternService
from src.analysis.patterns.base_detector import Pattern

logger = logging.getLogger(__name__)


class PatternRecognitionWidget(QWidget):
    """Tab 1: Pattern Recognition using existing PatternService and shared widgets."""

    patterns_detected = pyqtSignal(list)  # Emits List[Pattern]
    analysis_completed = pyqtSignal(object)  # Emits PatternAnalysis

    def __init__(self, parent=None, chart_window=None):
        super().__init__(parent)
        self.chart_window = chart_window
        self.detected_patterns: List[Pattern] = []
        self.current_analysis = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup UI with reusable widgets."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("🔍 Pattern Recognition")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)

        # REUSED: Pattern analysis settings
        settings_group = QGroupBox("Analysis Settings")
        settings_layout = QVBoxLayout(settings_group)
        self.settings = PatternAnalysisSettings(parent=self)
        settings_layout.addWidget(self.settings)
        layout.addWidget(settings_group)

        # Analyze button + progress
        button_layout = QHBoxLayout()
        self.analyze_btn = QPushButton("🔍 Analyze Patterns")
        self.analyze_btn.setStyleSheet(
            "QPushButton { background-color: #1976d2; color: white; padding: 10px; "
            "border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #1565c0; }"
        )
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)
        button_layout.addWidget(self.analyze_btn)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        button_layout.addWidget(self.progress)

        layout.addLayout(button_layout)

        # REUSED: Results display
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        self.results = PatternResultsDisplay(parent=self)
        results_layout.addWidget(self.results)
        layout.addWidget(results_group)

        # REUSED: Matches table
        matches_group = QGroupBox("Similar Patterns (Historical)")
        matches_layout = QVBoxLayout(matches_group)
        self.matches_table = PatternMatchesTable(parent=self)
        self.matches_table.itemDoubleClicked.connect(self._on_pattern_double_clicked)
        matches_layout.addWidget(self.matches_table)
        layout.addWidget(matches_group)

        # Action buttons
        action_layout = QHBoxLayout()

        self.draw_btn = QPushButton("📍 Draw on Chart")
        self.draw_btn.clicked.connect(self._on_draw_patterns_clicked)
        self.draw_btn.setEnabled(False)
        action_layout.addWidget(self.draw_btn)

        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        action_layout.addWidget(self.clear_btn)

        self.export_btn = QPushButton("💾 Export Patterns")
        self.export_btn.clicked.connect(self._on_export_clicked)
        self.export_btn.setEnabled(False)
        action_layout.addWidget(self.export_btn)

        layout.addLayout(action_layout)

    def _on_analyze_clicked(self):
        """Run pattern analysis using reusable helper and PatternService."""
        try:
            # REUSED: Chart data access
            settings = self.settings.get_settings()
            bars, symbol, timeframe = ChartDataHelper.get_bars_from_chart(
                self,
                window_size=settings['window_size']
            )

            if bars is None:
                QMessageBox.warning(
                    self,
                    "No Data",
                    "No chart data available for pattern analysis."
                )
                return

            # Show progress
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)  # Indeterminate
            self.analyze_btn.setEnabled(False)

            # Run pattern analysis async
            async def run_analysis():
                service = PatternService(
                    window_size=settings['window_size'],
                    min_similar_patterns=settings['min_matches'],
                    similarity_threshold=settings['similarity_threshold']
                )
                await service.initialize()
                return await service.analyze_signal(
                    bars=bars,
                    symbol=symbol,
                    timeframe=timeframe,
                    signal_direction=settings['signal_direction'],
                    cross_symbol_search=settings['cross_symbol']
                )

            # Run in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                task = asyncio.create_task(run_analysis())
                loop.run_until_complete(task)
                analysis = task.result()
            else:
                analysis = loop.run_until_complete(run_analysis())

            # Store results
            self.current_analysis = analysis

            # REUSED: Display results
            self.results.update_from_analysis(analysis)
            self.matches_table.populate_from_matches(analysis.best_matches)

            # Enable action buttons
            self.draw_btn.setEnabled(True)
            self.export_btn.setEnabled(True)

            # Emit signal
            self.analysis_completed.emit(analysis)

            logger.info(f"Pattern analysis completed: {analysis.similar_patterns_count} matches")

        except Exception as e:
            logger.exception(f"Pattern analysis failed: {e}")
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"Pattern analysis failed:\n{e}"
            )
        finally:
            self.progress.setVisible(False)
            self.analyze_btn.setEnabled(True)

    def _on_pattern_double_clicked(self, item):
        """Show pattern details (Strategy Concept specific)."""
        row = item.row()
        symbol = self.matches_table.item(row, 0).text()
        date = self.matches_table.item(row, 2).text()
        similarity = self.matches_table.item(row, 3).text()
        trend = self.matches_table.item(row, 4).text()
        return_pct = self.matches_table.item(row, 6).text()

        # TODO: Show detailed pattern visualization dialog
        QMessageBox.information(
            self,
            "Pattern Details",
            f"Similar Pattern:\n\n"
            f"Symbol: {symbol}\n"
            f"Date: {date}\n"
            f"Similarity: {similarity}\n"
            f"Trend: {trend}\n"
            f"Return: {return_pct}\n\n"
            f"Detailed visualization coming in Phase 3..."
        )

    def _on_draw_patterns_clicked(self):
        """Draw detected patterns on chart."""
        if not self.detected_patterns:
            QMessageBox.information(
                self,
                "No Patterns",
                "No patterns detected yet. Run analysis first."
            )
            return

        # TODO: Integrate with chart overlay (from Entry Analyzer MVP)
        QMessageBox.information(
            self,
            "Draw Patterns",
            f"Drawing {len(self.detected_patterns)} patterns on chart...\n\n"
            f"Chart integration coming in Phase 5."
        )

    def _on_clear_clicked(self):
        """Clear all results."""
        self.detected_patterns.clear()
        self.current_analysis = None
        self.results.clear()
        self.matches_table.clear_table()
        self.draw_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

    def _on_export_clicked(self):
        """Export detected patterns."""
        if not self.current_analysis:
            QMessageBox.information(
                self,
                "No Analysis",
                "No analysis results to export. Run analysis first."
            )
            return

        # TODO: Implement pattern export (JSON/CSV)
        QMessageBox.information(
            self,
            "Export Patterns",
            f"Exporting {self.current_analysis.similar_patterns_count} pattern matches...\n\n"
            f"Export functionality coming in Phase 4."
        )
```

**Checklist:**
- [ ] Create file `src/ui/widgets/pattern_recognition_widget.py`
- [ ] Implement `PatternRecognitionWidget` class
- [ ] Use `PatternAnalysisSettings` from shared widgets
- [ ] Use `PatternResultsDisplay` from shared widgets
- [ ] Use `PatternMatchesTable` from shared widgets
- [ ] Use `ChartDataHelper.get_bars_from_chart()` for data access
- [ ] Integrate `PatternService` for analysis
- [ ] Add progress bar and error handling
- [ ] Connect signals: `patterns_detected`, `analysis_completed`
- [ ] Test widget standalone

---

### ✅ Schritt 2.2: Unit Tests für Pattern Recognition Widget (1-2h)

**Datei:** `tests/ui/widgets/test_pattern_recognition_widget.py`

```python
"""Unit tests for PatternRecognitionWidget."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from PyQt6.QtWidgets import QApplication
from src.ui.widgets.pattern_recognition_widget import PatternRecognitionWidget


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_chart_window():
    """Create mock chart window with data."""
    import pandas as pd
    from datetime import datetime, timedelta

    mock = Mock()
    mock.chart_widget = Mock()

    # Create sample chart data
    dates = [datetime.now() - timedelta(hours=i) for i in range(100, 0, -1)]
    mock.chart_widget.data = pd.DataFrame({
        'open': [100 + i * 0.1 for i in range(100)],
        'high': [100.5 + i * 0.1 for i in range(100)],
        'low': [99.5 + i * 0.1 for i in range(100)],
        'close': [100.2 + i * 0.1 for i in range(100)],
        'volume': [1000 + i * 10 for i in range(100)]
    }, index=dates)

    mock.chart_widget.current_symbol = 'BTCUSDT'
    mock.chart_widget.timeframe = '1h'

    return mock


def test_widget_initialization(qapp, mock_chart_window):
    """Test PatternRecognitionWidget initializes correctly."""
    widget = PatternRecognitionWidget(chart_window=mock_chart_window)

    assert widget.settings is not None
    assert widget.results is not None
    assert widget.matches_table is not None
    assert widget.analyze_btn.isEnabled()
    assert not widget.draw_btn.isEnabled()
    assert not widget.export_btn.isEnabled()


def test_clear_functionality(qapp, mock_chart_window):
    """Test clear button clears all data."""
    widget = PatternRecognitionWidget(chart_window=mock_chart_window)

    # Simulate some data
    widget.detected_patterns = [Mock(), Mock()]
    widget.current_analysis = Mock()
    widget.draw_btn.setEnabled(True)
    widget.export_btn.setEnabled(True)

    # Click clear
    widget._on_clear_clicked()

    assert len(widget.detected_patterns) == 0
    assert widget.current_analysis is None
    assert not widget.draw_btn.isEnabled()
    assert not widget.export_btn.isEnabled()


@patch('src.ui.widgets.pattern_recognition_widget.PatternService')
@patch('src.ui.widgets.pattern_recognition_widget.ChartDataHelper')
def test_analyze_with_mock_data(mock_helper, mock_service, qapp, mock_chart_window):
    """Test pattern analysis with mocked services."""
    # Mock ChartDataHelper
    mock_helper.get_bars_from_chart.return_value = ([Mock()] * 50, 'BTCUSDT', '1h')

    # Mock PatternService
    mock_analysis = Mock()
    mock_analysis.similar_patterns_count = 10
    mock_analysis.win_rate = 0.75
    mock_analysis.best_matches = []

    mock_service_instance = Mock()
    mock_service_instance.initialize = AsyncMock()
    mock_service_instance.analyze_signal = AsyncMock(return_value=mock_analysis)
    mock_service.return_value = mock_service_instance

    # Create widget with mocked parent
    widget = PatternRecognitionWidget()
    widget.parent = Mock(return_value=mock_chart_window)

    # Run analysis
    widget._on_analyze_clicked()

    # Verify
    assert widget.current_analysis == mock_analysis
    assert widget.draw_btn.isEnabled()
    assert widget.export_btn.isEnabled()
```

**Checklist:**
- [ ] Create file `tests/ui/widgets/test_pattern_recognition_widget.py`
- [ ] Test widget initialization
- [ ] Test clear functionality
- [ ] Test analyze with mocked PatternService
- [ ] Test error handling (no data)
- [ ] Run tests: `pytest tests/ui/widgets/test_pattern_recognition_widget.py`

---

## 🚀 Phase 3: Tab 2 - Pattern Integration (6-8h)

**Ziel:** Pattern-to-Strategy Mapping UI mit Trade Setup Anzeige.

### ✅ Schritt 3.1: Pattern Integration Widget (4-5h)

**Datei:** `src/ui/widgets/pattern_integration_widget.py`

```python
"""Tab 2: Pattern Integration Widget - Pattern-to-Strategy Mapping UI."""

from __future__ import annotations

from typing import Optional, Dict, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QGroupBox, QLabel, QTextEdit, QPushButton, QHeaderView, QMessageBox,
    QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt
import logging

from src.strategies.strategy_models import (
    PATTERN_STRATEGIES,
    PatternStrategyMapping,
    StrategyType,
    PatternCategory
)
from src.strategies.pattern_strategy_mapper import (
    PatternStrategyMapper,
    TradeSetup
)

logger = logging.getLogger(__name__)


class PatternIntegrationWidget(QWidget):
    """Tab 2: Pattern-to-Strategy Integration with success rates."""

    strategy_selected = pyqtSignal(str, dict)  # (pattern_type, strategy_mapping)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mapper = PatternStrategyMapper()
        self.selected_pattern_type: Optional[str] = None
        self._setup_ui()
        self._populate_pattern_table()

    def _setup_ui(self):
        """Setup UI with pattern-strategy mapping table."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("🎯 Pattern-Strategy Integration")
        header.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(header)

        # Filter by category
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Category:"))
        self.category_filter = QComboBox()
        self.category_filter.addItems([
            "All",
            "REVERSAL",
            "CONTINUATION",
            "CONSOLIDATION",
            "BREAKOUT"
        ])
        self.category_filter.currentTextChanged.connect(self._on_category_changed)
        filter_layout.addWidget(self.category_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Pattern-Strategy Mapping Table
        table_group = QGroupBox("Pattern-Strategy Mappings (Phase 1)")
        table_layout = QVBoxLayout(table_group)

        self.pattern_table = QTableWidget()
        self.pattern_table.setColumnCount(6)
        self.pattern_table.setHorizontalHeaderLabels([
            "Pattern Name",
            "Category",
            "Success Rate",
            "Strategy Type",
            "Avg Profit",
            "Phase"
        ])
        self.pattern_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pattern_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pattern_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.pattern_table.setAlternatingRowColors(True)
        self.pattern_table.itemSelectionChanged.connect(self._on_pattern_selected)

        table_layout.addWidget(self.pattern_table)
        layout.addWidget(table_group)

        # Strategy Details
        details_group = QGroupBox("Strategy Details")
        details_layout = QVBoxLayout(details_group)

        self.strategy_details = QTextEdit()
        self.strategy_details.setReadOnly(True)
        self.strategy_details.setMaximumHeight(200)
        details_layout.addWidget(self.strategy_details)

        layout.addWidget(details_group)

        # Trade Setup Preview
        setup_group = QGroupBox("Trade Setup Preview")
        setup_layout = QVBoxLayout(setup_group)

        self.trade_setup_display = QTextEdit()
        self.trade_setup_display.setReadOnly(True)
        self.trade_setup_display.setMaximumHeight(150)
        setup_layout.addWidget(self.trade_setup_display)

        layout.addWidget(setup_group)

        # Action buttons
        action_layout = QHBoxLayout()

        self.apply_btn = QPushButton("✓ Apply Strategy")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._on_apply_strategy)
        action_layout.addWidget(self.apply_btn)

        self.export_btn = QPushButton("💾 Export to CEL")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._on_export_cel)
        action_layout.addWidget(self.export_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

    def _populate_pattern_table(self, category_filter: str = "All"):
        """Populate table with pattern-strategy mappings."""
        self.pattern_table.setRowCount(0)

        # Filter by implementation phase
        phase_1_patterns = {
            k: v for k, v in PATTERN_STRATEGIES.items()
            if v.implementation_phase == 1
        }

        for pattern_type, mapping in phase_1_patterns.items():
            # Apply category filter
            if category_filter != "All" and mapping.category.name != category_filter:
                continue

            row = self.pattern_table.rowCount()
            self.pattern_table.insertRow(row)

            # Pattern Name
            name_item = QTableWidgetItem(mapping.pattern_name)
            name_item.setData(Qt.ItemDataRole.UserRole, pattern_type)  # Store pattern_type
            self.pattern_table.setItem(row, 0, name_item)

            # Category
            category_item = QTableWidgetItem(mapping.category.name)
            category_color = self._get_category_color(mapping.category)
            category_item.setForeground(category_color)
            self.pattern_table.setItem(row, 1, category_item)

            # Success Rate
            success_item = QTableWidgetItem(f"{mapping.strategy.success_rate:.1f}%")
            if mapping.strategy.success_rate >= 90:
                success_item.setForeground(Qt.GlobalColor.darkGreen)
            elif mapping.strategy.success_rate >= 85:
                success_item.setForeground(Qt.GlobalColor.green)
            self.pattern_table.setItem(row, 2, success_item)

            # Strategy Type
            self.pattern_table.setItem(row, 3, QTableWidgetItem(mapping.strategy.strategy_type.value))

            # Avg Profit
            self.pattern_table.setItem(row, 4, QTableWidgetItem(mapping.strategy.avg_profit))

            # Phase
            self.pattern_table.setItem(row, 5, QTableWidgetItem(f"Phase {mapping.implementation_phase}"))

        logger.info(f"Populated pattern table with {self.pattern_table.rowCount()} patterns")

    def _get_category_color(self, category: PatternCategory):
        """Get color for pattern category."""
        colors = {
            PatternCategory.REVERSAL: Qt.GlobalColor.blue,
            PatternCategory.CONTINUATION: Qt.GlobalColor.darkGreen,
            PatternCategory.CONSOLIDATION: Qt.GlobalColor.darkYellow,
            PatternCategory.BREAKOUT: Qt.GlobalColor.magenta
        }
        return colors.get(category, Qt.GlobalColor.black)

    def _on_category_changed(self, category: str):
        """Handle category filter change."""
        self._populate_pattern_table(category)

    def _on_pattern_selected(self):
        """Handle pattern selection - show strategy details."""
        selected_rows = self.pattern_table.selectionModel().selectedRows()
        if not selected_rows:
            self.strategy_details.clear()
            self.trade_setup_display.clear()
            self.apply_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            return

        row = selected_rows[0].row()
        pattern_type = self.pattern_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.selected_pattern_type = pattern_type

        mapping = PATTERN_STRATEGIES[pattern_type]

        # Display strategy details
        details = self._format_strategy_details(mapping)
        self.strategy_details.setHtml(details)

        # Generate trade setup preview
        setup_preview = self._generate_trade_setup_preview(mapping)
        self.trade_setup_display.setHtml(setup_preview)

        # Enable action buttons
        self.apply_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        # Emit signal
        self.strategy_selected.emit(pattern_type, mapping.dict())

        logger.info(f"Selected pattern: {mapping.pattern_name}")

    def _format_strategy_details(self, mapping: PatternStrategyMapping) -> str:
        """Format strategy details as HTML."""
        strategy = mapping.strategy

        html = f"""
        <h3>{mapping.pattern_name}</h3>
        <p><b>Category:</b> {mapping.category.name}</p>
        <p><b>Success Rate:</b> <span style="color: green; font-weight: bold;">{strategy.success_rate:.1f}%</span></p>
        <p><b>Strategy:</b> {strategy.strategy_type.value}</p>
        <p><b>Average Profit:</b> {strategy.avg_profit}</p>
        <p><b>Risk-Reward:</b> {strategy.risk_reward_ratio}</p>

        <h4>Best Practices:</h4>
        <ul>
        """

        for practice in strategy.best_practices:
            html += f"<li>{practice}</li>"

        html += f"""
        </ul>

        <h4>Entry/Exit Rules:</h4>
        <p><b>Stop Loss:</b> {strategy.stop_loss_placement}</p>
        <p><b>Target:</b> {strategy.target_calculation}</p>
        """

        if strategy.volume_confirmation:
            html += "<p>✓ <b>Volume Confirmation Required</b></p>"

        if strategy.rsi_condition:
            html += f"<p>📊 <b>RSI Condition:</b> {strategy.rsi_condition}</p>"

        if strategy.macd_confirmation:
            html += "<p>📈 <b>MACD Confirmation Required</b></p>"

        return html

    def _generate_trade_setup_preview(self, mapping: PatternStrategyMapping) -> str:
        """Generate trade setup preview (simplified)."""
        html = f"""
        <h4>Trade Setup Template</h4>
        <p><i>Example for {mapping.pattern_name} pattern detected at current price:</i></p>
        <table border="1" cellpadding="5" style="border-collapse: collapse;">
        <tr>
            <td><b>Entry Price</b></td>
            <td>Breakout confirmation level</td>
        </tr>
        <tr>
            <td><b>Stop Loss</b></td>
            <td>{mapping.strategy.stop_loss_placement}</td>
        </tr>
        <tr>
            <td><b>Target Price</b></td>
            <td>{mapping.strategy.target_calculation}</td>
        </tr>
        <tr>
            <td><b>Risk-Reward</b></td>
            <td>{mapping.strategy.risk_reward_ratio}</td>
        </tr>
        <tr>
            <td><b>Expected Success</b></td>
            <td>{mapping.strategy.success_rate:.1f}%</td>
        </tr>
        </table>

        <p><i>Actual entry/stop/target levels require pattern geometry analysis.</i></p>
        """
        return html

    def _on_apply_strategy(self):
        """Apply selected strategy (integrate with bot/analyzer)."""
        if not self.selected_pattern_type:
            return

        mapping = PATTERN_STRATEGIES[self.selected_pattern_type]

        QMessageBox.information(
            self,
            "Apply Strategy",
            f"Applying {mapping.pattern_name} strategy...\n\n"
            f"Integration with Trading Bot coming in Phase 6."
        )

    def _on_export_cel(self):
        """Export strategy to CEL-compatible format."""
        if not self.selected_pattern_type:
            return

        mapping = PATTERN_STRATEGIES[self.selected_pattern_type]

        # TODO: Generate CEL rules from strategy
        QMessageBox.information(
            self,
            "Export to CEL",
            f"Exporting {mapping.pattern_name} to CEL format...\n\n"
            f"CEL export functionality coming in Phase 4."
        )
```

**Checklist:**
- [ ] Create file `src/ui/widgets/pattern_integration_widget.py`
- [ ] Implement `PatternIntegrationWidget` class
- [ ] Pattern-Strategy mapping table (6 columns)
- [ ] Category filter dropdown
- [ ] Strategy details display (HTML formatted)
- [ ] Trade setup preview (HTML table)
- [ ] Signal emission: `strategy_selected`
- [ ] Apply/Export button handlers (placeholders)
- [ ] Test widget standalone

---

### ✅ Schritt 3.2: Unit Tests für Pattern Integration Widget (1-2h)

**Datei:** `tests/ui/widgets/test_pattern_integration_widget.py`

```python
"""Unit tests for PatternIntegrationWidget."""

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.ui.widgets.pattern_integration_widget import PatternIntegrationWidget
from src.strategies.strategy_models import PATTERN_STRATEGIES


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_widget_initialization(qapp):
    """Test PatternIntegrationWidget initializes correctly."""
    widget = PatternIntegrationWidget()

    assert widget.pattern_table is not None
    assert widget.strategy_details is not None
    assert widget.trade_setup_display is not None
    assert widget.pattern_table.rowCount() > 0  # Phase 1 patterns loaded


def test_pattern_table_population(qapp):
    """Test pattern table is populated with Phase 1 patterns."""
    widget = PatternIntegrationWidget()

    # Should have 5 Phase 1 patterns
    phase_1_count = sum(
        1 for m in PATTERN_STRATEGIES.values()
        if m.implementation_phase == 1
    )

    assert widget.pattern_table.rowCount() == phase_1_count

    # Check first row has all columns filled
    assert widget.pattern_table.item(0, 0) is not None  # Pattern Name
    assert widget.pattern_table.item(0, 1) is not None  # Category
    assert widget.pattern_table.item(0, 2) is not None  # Success Rate


def test_pattern_selection(qapp, qtbot):
    """Test pattern selection updates details."""
    widget = PatternIntegrationWidget()

    # Select first pattern
    widget.pattern_table.selectRow(0)

    # Check details are populated
    assert widget.strategy_details.toPlainText() != ""
    assert widget.trade_setup_display.toPlainText() != ""
    assert widget.apply_btn.isEnabled()
    assert widget.export_btn.isEnabled()


def test_category_filter(qapp):
    """Test category filter works correctly."""
    widget = PatternIntegrationWidget()

    initial_count = widget.pattern_table.rowCount()

    # Filter by REVERSAL
    widget.category_filter.setCurrentText("REVERSAL")

    filtered_count = widget.pattern_table.rowCount()

    # Should have fewer rows (or same if all are REVERSAL)
    assert filtered_count <= initial_count

    # All visible rows should be REVERSAL
    for row in range(filtered_count):
        category = widget.pattern_table.item(row, 1).text()
        assert category == "REVERSAL"


def test_strategy_selected_signal(qapp, qtbot):
    """Test strategy_selected signal is emitted."""
    widget = PatternIntegrationWidget()

    with qtbot.waitSignal(widget.strategy_selected, timeout=1000) as blocker:
        widget.pattern_table.selectRow(0)

    pattern_type, mapping = blocker.args
    assert pattern_type is not None
    assert isinstance(mapping, dict)
```

**Checklist:**
- [ ] Create file `tests/ui/widgets/test_pattern_integration_widget.py`
- [ ] Test widget initialization
- [ ] Test pattern table population (Phase 1 patterns)
- [ ] Test pattern selection updates details
- [ ] Test category filter
- [ ] Test `strategy_selected` signal emission
- [ ] Run tests: `pytest tests/ui/widgets/test_pattern_integration_widget.py`

---

## 🚀 Phase 4: Pattern Detectors (8-10h)

**Ziel:** Implementierung der 3 fehlenden Phase 1 Pattern Detectors.

### ✅ Schritt 4.1: Cup and Handle Detector (3-4h)

**Datei:** Erweitern von `src/analysis/patterns/reversal_patterns.py`

```python
# Add to existing reversal_patterns.py

@dataclass
class CupAndHandle(Pattern):
    """Cup and Handle pattern (95% success rate in bull markets)."""

    cup_left_pivot: Pivot
    cup_bottom_pivot: Pivot
    cup_right_pivot: Pivot
    handle_high_pivot: Pivot
    handle_low_pivot: Pivot

    cup_depth_pct: float  # Depth of cup as % of left pivot high
    handle_depth_pct: float  # Depth of handle as % of cup right high
    cup_symmetry_score: float  # How symmetric is the cup (0-1)

    min_cup_duration_bars: int = 35  # Minimum 7 weeks (5 bars/week)
    max_handle_depth_pct: float = 33.3  # Handle should not exceed 1/3 of cup depth


class CupAndHandleDetector(PatternDetector):
    """
    Cup and Handle Pattern Detector.

    Success Rate: 95% (highest of all patterns)
    Optimal for: Bull markets, continuation patterns
    Min Formation: 7 weeks (35 daily bars)

    Criteria:
    - U-shaped cup (not V-shaped)
    - Cup depth: 12-33% correction
    - Handle: 1/8 to 1/3 of cup depth
    - Volume: decreasing in handle, surge on breakout
    - Breakout above handle high = entry
    """

    def __init__(self):
        super().__init__(
            pattern_name="Cup and Handle",
            pattern_type="cup_and_handle",
            category=PatternCategory.CONTINUATION
        )
        self.min_cup_bars = 35  # 7 weeks minimum
        self.max_cup_bars = 150  # ~30 weeks maximum
        self.min_handle_bars = 5  # At least 1 week
        self.max_handle_depth_pct = 33.3

    def detect(self, data: pd.DataFrame, pivots: List[Pivot]) -> List[Pattern]:
        """Detect Cup and Handle patterns."""
        patterns = []

        # Need at least 5 pivots (cup left, bottom, right, handle high, low)
        if len(pivots) < 5:
            return patterns

        for i in range(len(pivots) - 4):
            # Potential cup: High -> Low -> High
            cup_left = pivots[i]
            cup_bottom = pivots[i + 1]
            cup_right = pivots[i + 2]

            # Must be High-Low-High sequence
            if not (cup_left.is_high and not cup_bottom.is_high and cup_right.is_high):
                continue

            # Check cup duration
            cup_duration = cup_right.index - cup_left.index
            if cup_duration < self.min_cup_bars or cup_duration > self.max_cup_bars:
                continue

            # Check cup depth (12-33% correction)
            cup_depth_pct = ((cup_left.price - cup_bottom.price) / cup_left.price) * 100
            if cup_depth_pct < 12 or cup_depth_pct > 33:
                continue

            # Check cup symmetry (U-shape, not V-shape)
            left_duration = cup_bottom.index - cup_left.index
            right_duration = cup_right.index - cup_bottom.index
            symmetry_ratio = min(left_duration, right_duration) / max(left_duration, right_duration)

            if symmetry_ratio < 0.6:  # Too asymmetric
                continue

            # Check cup right is close to cup left (within 5%)
            cup_right_vs_left_pct = abs((cup_right.price - cup_left.price) / cup_left.price) * 100
            if cup_right_vs_left_pct > 5:
                continue

            # Look for handle after cup
            handle_pivots = [p for p in pivots[i+2:i+7] if p.index > cup_right.index]

            if len(handle_pivots) < 2:
                continue

            # Handle: High -> Low pattern
            handle_high = None
            handle_low = None

            for j in range(len(handle_pivots) - 1):
                if handle_pivots[j].is_high and not handle_pivots[j+1].is_high:
                    handle_high = handle_pivots[j]
                    handle_low = handle_pivots[j+1]
                    break

            if not handle_high or not handle_low:
                continue

            # Check handle duration
            handle_duration = handle_low.index - handle_high.index
            if handle_duration < self.min_handle_bars:
                continue

            # Check handle depth (max 1/3 of cup depth)
            handle_depth_pct = ((handle_high.price - handle_low.price) / handle_high.price) * 100

            if handle_depth_pct > self.max_handle_depth_pct:
                continue

            # Handle should not drop below cup bottom
            if handle_low.price < cup_bottom.price:
                continue

            # Check volume pattern (decreasing in handle)
            handle_data = data.iloc[handle_high.index:handle_low.index+1]
            if len(handle_data) > 0 and 'volume' in handle_data.columns:
                volume_trend = handle_data['volume'].iloc[-1] / handle_data['volume'].iloc[0]
                if volume_trend > 1.2:  # Volume increased in handle (bearish)
                    continue

            # Calculate geometry score
            geometry_score = self._score_cup_and_handle_geometry(
                cup_depth_pct, handle_depth_pct, symmetry_ratio, cup_right_vs_left_pct
            )

            # Context score (trend before cup)
            context_score = self._score_context(data, cup_left.index)

            # Confirmation score
            confirmation_score = self._score_confirmation(data, handle_low.index)

            total_score = geometry_score + context_score + confirmation_score

            pattern = CupAndHandle(
                pattern_type="cup_and_handle",
                pattern_name="Cup and Handle",
                category=PatternCategory.CONTINUATION,
                start_index=cup_left.index,
                end_index=handle_low.index,
                key_pivots=[cup_left, cup_bottom, cup_right, handle_high, handle_low],
                score=total_score,
                geometry_score=geometry_score,
                context_score=context_score,
                confirmation_score=confirmation_score,

                # Cup and Handle specific
                cup_left_pivot=cup_left,
                cup_bottom_pivot=cup_bottom,
                cup_right_pivot=cup_right,
                handle_high_pivot=handle_high,
                handle_low_pivot=handle_low,
                cup_depth_pct=cup_depth_pct,
                handle_depth_pct=handle_depth_pct,
                cup_symmetry_score=symmetry_ratio,

                # Lines for visualization
                lines={
                    'cup': [(cup_left.index, cup_left.price), (cup_bottom.index, cup_bottom.price),
                           (cup_right.index, cup_right.price)],
                    'handle': [(handle_high.index, handle_high.price), (handle_low.index, handle_low.price)],
                    'breakout': [(handle_low.index, handle_high.price), (handle_low.index + 10, handle_high.price)]
                }
            )

            patterns.append(pattern)
            logger.info(
                f"Cup and Handle detected at {cup_left.index}: "
                f"score={total_score:.1f}, cup_depth={cup_depth_pct:.1f}%, "
                f"handle_depth={handle_depth_pct:.1f}%"
            )

        return patterns

    def _score_cup_and_handle_geometry(
        self,
        cup_depth_pct: float,
        handle_depth_pct: float,
        symmetry_ratio: float,
        cup_right_vs_left_pct: float
    ) -> float:
        """Score Cup and Handle geometry (0-60)."""
        score = 0.0

        # Cup depth score (0-20): ideal 15-25%
        if 15 <= cup_depth_pct <= 25:
            score += 20
        elif 12 <= cup_depth_pct < 15 or 25 < cup_depth_pct <= 30:
            score += 15
        else:
            score += 10

        # Handle depth score (0-15): ideal <20% of cup depth
        handle_to_cup_ratio = (handle_depth_pct / cup_depth_pct) * 100
        if handle_to_cup_ratio < 20:
            score += 15
        elif handle_to_cup_ratio < 30:
            score += 10
        else:
            score += 5

        # Symmetry score (0-15): ideal >0.8
        score += symmetry_ratio * 15

        # Cup right vs left score (0-10): ideal <2%
        if cup_right_vs_left_pct < 2:
            score += 10
        elif cup_right_vs_left_pct < 5:
            score += 7
        else:
            score += 4

        return score
```

**Checklist:**
- [ ] Add `CupAndHandle` dataclass to `reversal_patterns.py`
- [ ] Implement `CupAndHandleDetector` class
- [ ] Cup detection (U-shaped, 12-33% depth, 7+ weeks)
- [ ] Handle detection (1/8 to 1/3 of cup depth, <1/3 max)
- [ ] Symmetry validation (U-shape, not V-shape)
- [ ] Volume pattern validation
- [ ] Geometry scoring (0-60)
- [ ] Context + Confirmation scoring (0-40)
- [ ] Unit tests: `tests/patterns/test_cup_and_handle.py`
- [ ] Verify 95% success rate alignment with research

---

### ✅ Schritt 4.2: Triple Bottom Detector (2-3h)

**Datei:** Erweitern von `src/analysis/patterns/reversal_patterns.py`

```python
# Add to existing reversal_patterns.py

@dataclass
class TripleBottom(Pattern):
    """Triple Bottom pattern (87% success rate)."""

    bottom1_pivot: Pivot
    bottom2_pivot: Pivot
    bottom3_pivot: Pivot
    peak1_pivot: Pivot  # Between bottom1 and bottom2
    peak2_pivot: Pivot  # Between bottom2 and bottom3

    resistance_level: float  # Level to break for confirmation
    bottom_consistency_score: float  # How consistent are the 3 bottoms (0-1)


class TripleBottomDetector(PatternDetector):
    """
    Triple Bottom Pattern Detector.

    Success Rate: 87%
    Type: Reversal (bullish)

    Criteria:
    - 3 distinct bottoms at similar price levels (within 2-3%)
    - 2 peaks between bottoms
    - Resistance line at peak levels
    - Breakout above resistance = entry
    - Volume increasing on 3rd bottom
    """

    def __init__(self):
        super().__init__(
            pattern_name="Triple Bottom",
            pattern_type="triple_bottom",
            category=PatternCategory.REVERSAL
        )
        self.max_bottom_variance_pct = 3.0  # Bottoms within 3% of each other

    def detect(self, data: pd.DataFrame, pivots: List[Pivot]) -> List[Pattern]:
        """Detect Triple Bottom patterns."""
        patterns = []

        # Need at least 5 pivots: Low-High-Low-High-Low
        if len(pivots) < 5:
            return patterns

        for i in range(len(pivots) - 4):
            # Check for Low-High-Low-High-Low sequence
            bottom1 = pivots[i]
            peak1 = pivots[i + 1]
            bottom2 = pivots[i + 2]
            peak2 = pivots[i + 3]
            bottom3 = pivots[i + 4]

            # Must be Low-High-Low-High-Low
            if not (not bottom1.is_high and peak1.is_high and
                   not bottom2.is_high and peak2.is_high and
                   not bottom3.is_high):
                continue

            # Check bottom consistency (all bottoms within 3% of each other)
            avg_bottom = (bottom1.price + bottom2.price + bottom3.price) / 3

            bottom1_var = abs((bottom1.price - avg_bottom) / avg_bottom) * 100
            bottom2_var = abs((bottom2.price - avg_bottom) / avg_bottom) * 100
            bottom3_var = abs((bottom3.price - avg_bottom) / avg_bottom) * 100

            if max(bottom1_var, bottom2_var, bottom3_var) > self.max_bottom_variance_pct:
                continue

            # Calculate resistance level (average of peaks)
            resistance = (peak1.price + peak2.price) / 2

            # Check peaks are above bottoms by at least 5%
            min_peak_height_pct = ((resistance - avg_bottom) / avg_bottom) * 100
            if min_peak_height_pct < 5:
                continue

            # Check volume increasing on 3rd bottom (bullish)
            if 'volume' in data.columns:
                vol1 = data.iloc[bottom1.index]['volume']
                vol2 = data.iloc[bottom2.index]['volume']
                vol3 = data.iloc[bottom3.index]['volume']

                if vol3 < vol2 or vol3 < vol1 * 0.8:  # Volume not increasing
                    continue

            # Calculate bottom consistency score
            consistency_score = 1.0 - (max(bottom1_var, bottom2_var, bottom3_var) / self.max_bottom_variance_pct)

            # Geometry score
            geometry_score = self._score_triple_bottom_geometry(
                bottom1_var, bottom2_var, bottom3_var, min_peak_height_pct, consistency_score
            )

            # Context score
            context_score = self._score_context(data, bottom1.index)

            # Confirmation score
            confirmation_score = self._score_confirmation(data, bottom3.index)

            total_score = geometry_score + context_score + confirmation_score

            pattern = TripleBottom(
                pattern_type="triple_bottom",
                pattern_name="Triple Bottom",
                category=PatternCategory.REVERSAL,
                start_index=bottom1.index,
                end_index=bottom3.index,
                key_pivots=[bottom1, peak1, bottom2, peak2, bottom3],
                score=total_score,
                geometry_score=geometry_score,
                context_score=context_score,
                confirmation_score=confirmation_score,

                # Triple Bottom specific
                bottom1_pivot=bottom1,
                bottom2_pivot=bottom2,
                bottom3_pivot=bottom3,
                peak1_pivot=peak1,
                peak2_pivot=peak2,
                resistance_level=resistance,
                bottom_consistency_score=consistency_score,

                # Lines for visualization
                lines={
                    'bottoms': [(bottom1.index, bottom1.price), (bottom2.index, bottom2.price),
                               (bottom3.index, bottom3.price)],
                    'resistance': [(peak1.index, resistance), (bottom3.index + 10, resistance)]
                }
            )

            patterns.append(pattern)
            logger.info(
                f"Triple Bottom detected at {bottom1.index}: "
                f"score={total_score:.1f}, consistency={consistency_score:.2f}"
            )

        return patterns

    def _score_triple_bottom_geometry(
        self,
        bottom1_var: float,
        bottom2_var: float,
        bottom3_var: float,
        peak_height_pct: float,
        consistency_score: float
    ) -> float:
        """Score Triple Bottom geometry (0-60)."""
        score = 0.0

        # Bottom consistency (0-30): closer to 0% variance = better
        score += consistency_score * 30

        # Peak height (0-20): ideal >8%
        if peak_height_pct >= 8:
            score += 20
        elif peak_height_pct >= 6:
            score += 15
        else:
            score += 10

        # Third bottom should be cleanest (0-10)
        if bottom3_var <= 1.0:
            score += 10
        elif bottom3_var <= 2.0:
            score += 7
        else:
            score += 4

        return score
```

**Checklist:**
- [ ] Add `TripleBottom` dataclass
- [ ] Implement `TripleBottomDetector` class
- [ ] Detect Low-High-Low-High-Low sequence
- [ ] Validate bottom consistency (within 3%)
- [ ] Check resistance level (peak average)
- [ ] Volume validation (increasing on 3rd bottom)
- [ ] Geometry scoring (0-60)
- [ ] Unit tests: `tests/patterns/test_triple_bottom.py`

---

### ✅ Schritt 4.3: Ascending Triangle Detector (3-4h)

**Datei:** Neu erstellen `src/analysis/patterns/continuation_patterns.py`

```python
"""Continuation pattern detectors (Ascending Triangle, etc.)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
import numpy as np
from scipy import stats
import logging

from src.analysis.patterns.base_detector import (
    Pattern,
    PatternDetector,
    Pivot,
    PatternCategory
)

logger = logging.getLogger(__name__)


@dataclass
class AscendingTriangle(Pattern):
    """Ascending Triangle pattern (83% success rate in bull markets)."""

    resistance_pivots: List[Pivot]  # Horizontal resistance line pivots
    support_pivots: List[Pivot]  # Ascending support line pivots

    resistance_level: float  # Horizontal resistance price
    support_slope: float  # Slope of ascending support line
    support_r_squared: float  # How well support fits a line (0-1)

    compression_ratio: float  # Width at end / width at start


class AscendingTriangleDetector(PatternDetector):
    """
    Ascending Triangle Pattern Detector.

    Success Rate: 83% (in bull markets)
    Type: Continuation (bullish)

    Criteria:
    - Flat resistance (horizontal line at highs)
    - Ascending support (higher lows)
    - Minimum 2 touches on each line
    - Breakout above resistance = entry
    - Volume decreasing during formation
    """

    def __init__(self):
        super().__init__(
            pattern_name="Ascending Triangle",
            pattern_type="ascending_triangle",
            category=PatternCategory.CONTINUATION
        )
        self.min_touches_per_line = 2
        self.resistance_tolerance_pct = 1.5  # Resistance within 1.5%

    def detect(self, data: pd.DataFrame, pivots: List[Pivot]) -> List[Pattern]:
        """Detect Ascending Triangle patterns."""
        patterns = []

        if len(pivots) < 4:  # Need at least 2 highs + 2 lows
            return patterns

        # Separate highs and lows
        highs = [p for p in pivots if p.is_high]
        lows = [p for p in pivots if not p.is_high]

        # Find potential resistance lines (flat horizontal)
        for i in range(len(highs) - 1):
            resistance_candidates = [highs[i]]
            resistance_level = highs[i].price

            # Find other highs near this level
            for j in range(i + 1, len(highs)):
                variance_pct = abs((highs[j].price - resistance_level) / resistance_level) * 100

                if variance_pct <= self.resistance_tolerance_pct:
                    resistance_candidates.append(highs[j])

            # Need at least 2 touches on resistance
            if len(resistance_candidates) < self.min_touches_per_line:
                continue

            # Find lows between first and last resistance touch
            start_idx = resistance_candidates[0].index
            end_idx = resistance_candidates[-1].index

            support_candidates = [
                l for l in lows
                if start_idx < l.index < end_idx
            ]

            if len(support_candidates) < self.min_touches_per_line:
                continue

            # Check if support lows are ascending (higher lows)
            support_prices = [l.price for l in support_candidates]
            support_indices = [l.index for l in support_candidates]

            # Fit linear regression to support lows
            slope, intercept, r_value, _, _ = stats.linregress(support_indices, support_prices)
            r_squared = r_value ** 2

            # Support must be ascending (positive slope)
            if slope <= 0:
                continue

            # R-squared should be high (good fit to line)
            if r_squared < 0.7:
                continue

            # Calculate compression ratio (triangle narrowing)
            first_low = support_candidates[0].price
            last_low = support_candidates[-1].price

            first_width = resistance_level - first_low
            last_width = resistance_level - last_low

            if first_width <= 0 or last_width <= 0:
                continue

            compression_ratio = last_width / first_width

            # Triangle should be compressing (ratio < 1)
            if compression_ratio >= 1.0:
                continue

            # Check volume pattern (decreasing during formation)
            triangle_data = data.iloc[start_idx:end_idx+1]
            volume_trend_ok = self._check_volume_decrease(triangle_data)

            # Calculate geometry score
            geometry_score = self._score_ascending_triangle_geometry(
                len(resistance_candidates), len(support_candidates),
                r_squared, compression_ratio, slope
            )

            # Context score
            context_score = self._score_context(data, start_idx)

            # Confirmation score
            confirmation_score = self._score_confirmation(data, end_idx)

            # Bonus for volume pattern
            if volume_trend_ok:
                confirmation_score += 5

            total_score = geometry_score + context_score + confirmation_score

            pattern = AscendingTriangle(
                pattern_type="ascending_triangle",
                pattern_name="Ascending Triangle",
                category=PatternCategory.CONTINUATION,
                start_index=start_idx,
                end_index=end_idx,
                key_pivots=resistance_candidates + support_candidates,
                score=total_score,
                geometry_score=geometry_score,
                context_score=context_score,
                confirmation_score=confirmation_score,

                # Ascending Triangle specific
                resistance_pivots=resistance_candidates,
                support_pivots=support_candidates,
                resistance_level=resistance_level,
                support_slope=slope,
                support_r_squared=r_squared,
                compression_ratio=compression_ratio,

                # Lines for visualization
                lines={
                    'resistance': [(start_idx, resistance_level), (end_idx + 10, resistance_level)],
                    'support': [
                        (start_idx, intercept + slope * start_idx),
                        (end_idx, intercept + slope * end_idx)
                    ]
                }
            )

            patterns.append(pattern)
            logger.info(
                f"Ascending Triangle detected at {start_idx}: "
                f"score={total_score:.1f}, r²={r_squared:.2f}, "
                f"compression={compression_ratio:.2f}"
            )

        return patterns

    def _check_volume_decrease(self, data: pd.DataFrame) -> bool:
        """Check if volume is decreasing during triangle formation."""
        if 'volume' not in data.columns or len(data) < 3:
            return False

        # Compare first third vs last third
        first_third_vol = data['volume'].iloc[:len(data)//3].mean()
        last_third_vol = data['volume'].iloc[-len(data)//3:].mean()

        return last_third_vol < first_third_vol * 0.8  # 20% decrease

    def _score_ascending_triangle_geometry(
        self,
        resistance_touches: int,
        support_touches: int,
        r_squared: float,
        compression_ratio: float,
        slope: float
    ) -> float:
        """Score Ascending Triangle geometry (0-60)."""
        score = 0.0

        # Resistance touches (0-15): more = better
        score += min(resistance_touches * 5, 15)

        # Support touches (0-15): more = better
        score += min(support_touches * 5, 15)

        # Support line fit (0-15): R² closer to 1 = better
        score += r_squared * 15

        # Compression ratio (0-10): ideal 0.3-0.7
        if 0.3 <= compression_ratio <= 0.7:
            score += 10
        elif 0.2 <= compression_ratio < 0.3 or 0.7 < compression_ratio <= 0.8:
            score += 7
        else:
            score += 4

        # Support slope (0-5): moderate slope is best
        slope_pct = slope / data.iloc[start_idx]['close'] * 100  # Normalize
        if 0.1 <= slope_pct <= 0.5:
            score += 5
        elif 0.05 <= slope_pct < 0.1 or 0.5 < slope_pct <= 1.0:
            score += 3
        else:
            score += 1

        return score
```

**Checklist:**
- [ ] Create file `src/analysis/patterns/continuation_patterns.py`
- [ ] Add `AscendingTriangle` dataclass
- [ ] Implement `AscendingTriangleDetector` class
- [ ] Detect flat resistance line (horizontal highs within 1.5%)
- [ ] Detect ascending support line (linear regression on lows, positive slope)
- [ ] R-squared validation (>0.7 for good fit)
- [ ] Compression ratio calculation
- [ ] Volume pattern check (decreasing)
- [ ] Geometry scoring (0-60)
- [ ] Unit tests: `tests/patterns/test_ascending_triangle.py`

---

## 🚀 Phase 5: Strategy Concept Window (4-5h)

**Ziel:** Haupt-Dialog mit Tab-Verwaltung und Integration der Widgets.

### ✅ Schritt 5.1: Strategy Concept Window Dialog (3-4h)

**Datei:** `src/ui/dialogs/strategy_concept_window.py`

```python
"""Strategy Concept Window - Main Dialog for pattern-strategy integration."""

from __future__ import annotations

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout,
    QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
import logging

from src.ui.widgets.pattern_recognition_widget import PatternRecognitionWidget
from src.ui.widgets.pattern_integration_widget import PatternIntegrationWidget

logger = logging.getLogger(__name__)


class StrategyConceptWindow(QDialog):
    """
    Strategy Concept Window - Separate window for pattern-based trading strategies.

    Features:
    - Tab 1: Pattern Recognition (detection & analysis)
    - Tab 2: Pattern Integration (strategy mapping & success rates)
    - Pattern-to-Strategy workflows
    - CEL export capabilities
    """

    # Signals
    patterns_detected = pyqtSignal(list)  # Emitted when patterns detected in Tab 1
    strategy_selected = pyqtSignal(str, dict)  # Emitted when strategy selected in Tab 2
    window_closed = pyqtSignal()  # Emitted on close

    def __init__(self, parent=None, chart_window=None):
        super().__init__(parent)
        self.chart_window = chart_window
        self.setWindowTitle("Strategy Concept - Pattern-Based Trading Strategies")
        self.setMinimumSize(1200, 800)
        self.setWindowFlags(Qt.WindowType.Window)  # Separate window, not modal

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup main UI with tabs."""
        layout = QVBoxLayout(self)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Tab 1: Pattern Recognition
        self.pattern_recognition_tab = PatternRecognitionWidget(
            parent=self,
            chart_window=self.chart_window
        )
        self.tabs.addTab(self.pattern_recognition_tab, "📊 Mustererkennung")

        # Tab 2: Pattern Integration
        self.pattern_integration_tab = PatternIntegrationWidget(parent=self)
        self.tabs.addTab(self.pattern_integration_tab, "🎯 Pattern Integration")

        layout.addWidget(self.tabs)

        # Footer buttons
        footer_layout = QHBoxLayout()

        self.help_btn = QPushButton("❓ Help")
        self.help_btn.clicked.connect(self._on_help_clicked)
        footer_layout.addWidget(self.help_btn)

        footer_layout.addStretch()

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        footer_layout.addWidget(self.close_btn)

        layout.addLayout(footer_layout)

    def _connect_signals(self):
        """Connect inter-tab signals."""
        # Forward signals from tabs to parent
        self.pattern_recognition_tab.patterns_detected.connect(self.patterns_detected.emit)
        self.pattern_recognition_tab.analysis_completed.connect(self._on_analysis_completed)

        self.pattern_integration_tab.strategy_selected.connect(self.strategy_selected.emit)

    def _on_analysis_completed(self, analysis):
        """Handle analysis completion from Tab 1."""
        logger.info(f"Pattern analysis completed: {analysis.similar_patterns_count} matches")

        # Optional: Switch to Tab 2 to show strategies
        # self.tabs.setCurrentIndex(1)

    def _on_help_clicked(self):
        """Show help dialog."""
        help_text = """
        <h2>Strategy Concept Window</h2>

        <h3>📊 Tab 1: Mustererkennung</h3>
        <p>Analyze chart patterns using historical similarity matching:</p>
        <ul>
            <li>Configure analysis settings (window size, similarity threshold)</li>
            <li>Click "Analyze Patterns" to find similar historical patterns</li>
            <li>Review results: win rate, avg return, confidence</li>
            <li>Draw patterns on chart for visualization</li>
        </ul>

        <h3>🎯 Tab 2: Pattern Integration</h3>
        <p>Explore pattern-strategy mappings with research-backed success rates:</p>
        <ul>
            <li><b>Phase 1 Patterns</b>: Cup & Handle (95%), Head & Shoulders (89-93%), etc.</li>
            <li>Select pattern to view strategy details</li>
            <li>See trade setup preview (entry, stop loss, target)</li>
            <li>Export to CEL for Trading Bot integration</li>
        </ul>

        <h3>🎓 Best Practices</h3>
        <ul>
            <li>Use Tab 1 for historical pattern validation</li>
            <li>Use Tab 2 for strategy selection based on current market pattern</li>
            <li>Combine pattern detection with strategy success rates</li>
            <li>Always validate with volume and context indicators</li>
        </ul>
        """

        QMessageBox.information(self, "Strategy Concept Help", help_text)

    def closeEvent(self, event):
        """Handle window close event."""
        self.window_closed.emit()
        super().closeEvent(event)

    # Public API for parent ChartWindow

    def get_detected_patterns(self):
        """Get currently detected patterns from Tab 1."""
        return self.pattern_recognition_tab.detected_patterns

    def get_selected_strategy(self):
        """Get currently selected strategy from Tab 2."""
        return self.pattern_integration_tab.selected_pattern_type

    def trigger_analysis(self):
        """Programmatically trigger pattern analysis (Tab 1)."""
        self.tabs.setCurrentIndex(0)  # Switch to Tab 1
        self.pattern_recognition_tab._on_analyze_clicked()

    def select_pattern(self, pattern_type: str):
        """Programmatically select a pattern in Tab 2."""
        self.tabs.setCurrentIndex(1)  # Switch to Tab 2

        # Find pattern in table
        for row in range(self.pattern_integration_tab.pattern_table.rowCount()):
            item = self.pattern_integration_tab.pattern_table.item(row, 0)
            if item.data(Qt.ItemDataRole.UserRole) == pattern_type:
                self.pattern_integration_tab.pattern_table.selectRow(row)
                break
```

**Checklist:**
- [ ] Create file `src/ui/dialogs/strategy_concept_window.py`
- [ ] Implement `StrategyConceptWindow` class
- [ ] 2-Tab layout: Mustererkennung, Pattern Integration
- [ ] Signal forwarding: `patterns_detected`, `strategy_selected`, `window_closed`
- [ ] Help button with comprehensive guide
- [ ] Public API: `get_detected_patterns()`, `trigger_analysis()`, `select_pattern()`
- [ ] Test window standalone

---

### ✅ Schritt 5.2: Unit Tests für Strategy Concept Window (1h)

**Datei:** `tests/ui/dialogs/test_strategy_concept_window.py`

```python
"""Unit tests for StrategyConceptWindow."""

import pytest
from unittest.mock import Mock
from PyQt6.QtWidgets import QApplication
from src.ui.dialogs.strategy_concept_window import StrategyConceptWindow


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_chart_window():
    """Create mock chart window."""
    mock = Mock()
    mock.chart_widget = Mock()
    return mock


def test_window_initialization(qapp, mock_chart_window):
    """Test StrategyConceptWindow initializes correctly."""
    window = StrategyConceptWindow(chart_window=mock_chart_window)

    assert window.tabs.count() == 2
    assert window.pattern_recognition_tab is not None
    assert window.pattern_integration_tab is not None
    assert window.windowTitle() == "Strategy Concept - Pattern-Based Trading Strategies"


def test_tab_switching(qapp, mock_chart_window):
    """Test tab switching works correctly."""
    window = StrategyConceptWindow(chart_window=mock_chart_window)

    # Start on Tab 1
    assert window.tabs.currentIndex() == 0

    # Switch to Tab 2
    window.tabs.setCurrentIndex(1)
    assert window.tabs.currentIndex() == 1


def test_signal_forwarding(qapp, mock_chart_window, qtbot):
    """Test signals are forwarded from tabs to window."""
    window = StrategyConceptWindow(chart_window=mock_chart_window)

    # Test patterns_detected signal forwarding
    with qtbot.waitSignal(window.patterns_detected, timeout=1000):
        window.pattern_recognition_tab.patterns_detected.emit([Mock(), Mock()])


def test_public_api(qapp, mock_chart_window):
    """Test public API methods."""
    window = StrategyConceptWindow(chart_window=mock_chart_window)

    # Test get_detected_patterns
    patterns = window.get_detected_patterns()
    assert isinstance(patterns, list)

    # Test get_selected_strategy
    strategy = window.get_selected_strategy()
    # Should be None initially

    # Test select_pattern
    window.select_pattern("cup_and_handle")
    assert window.tabs.currentIndex() == 1  # Switched to Tab 2


def test_window_close_signal(qapp, mock_chart_window, qtbot):
    """Test window_closed signal is emitted."""
    window = StrategyConceptWindow(chart_window=mock_chart_window)

    with qtbot.waitSignal(window.window_closed, timeout=1000):
        window.close()
```

**Checklist:**
- [ ] Create file `tests/ui/dialogs/test_strategy_concept_window.py`
- [ ] Test window initialization
- [ ] Test tab switching
- [ ] Test signal forwarding (patterns_detected, strategy_selected)
- [ ] Test public API (get_detected_patterns, trigger_analysis, select_pattern)
- [ ] Test window close signal
- [ ] Run tests: `pytest tests/ui/dialogs/test_strategy_concept_window.py`

---

## 🚀 Phase 6: Chart Integration (2-3h)

**Ziel:** Menü-Eintrag und Button im ChartWindow für Strategy Concept.

### ✅ Schritt 6.1: ChartWindow Integration (2-3h)

**Dateien zu modifizieren:**
- `src/ui/widgets/chart_window_setup.py` (oder ähnlich)
- `src/ui/widgets/chart_window_mixins/...` (je nach Struktur)

**Code-Ergänzungen:**

```python
# In ChartWindow oder entsprechendem Mixin

from src.ui.dialogs.strategy_concept_window import StrategyConceptWindow

class ChartWindow(QMainWindow):  # oder entsprechende Basisklasse

    def __init__(self, ...):
        super().__init__(...)
        self.strategy_concept_window: Optional[StrategyConceptWindow] = None
        # ... existing code ...

    def _create_menus(self):
        """Create menu bar."""
        # ... existing menus ...

        # Analysis menu (oder neues "Strategy" Menu)
        analysis_menu = self.menuBar().addMenu("Analysis")

        # Add Strategy Concept action
        strategy_concept_action = QAction("📊 Strategy Concept", self)
        strategy_concept_action.setShortcut("Ctrl+Shift+S")
        strategy_concept_action.setStatusTip("Open Strategy Concept Window")
        strategy_concept_action.triggered.connect(self._on_strategy_concept_clicked)
        analysis_menu.addAction(strategy_concept_action)

    def _create_toolbar(self):
        """Create toolbar."""
        # ... existing toolbar ...

        # Add Strategy Concept button
        strategy_concept_btn = QPushButton("📊 Strategy Concept")
        strategy_concept_btn.setToolTip("Open Strategy Concept Window (Ctrl+Shift+S)")
        strategy_concept_btn.setStyleSheet(
            "QPushButton { background-color: #9c27b0; color: white; padding: 8px; "
            "border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #7b1fa2; }"
        )
        strategy_concept_btn.clicked.connect(self._on_strategy_concept_clicked)
        toolbar.addWidget(strategy_concept_btn)

    def _on_strategy_concept_clicked(self):
        """Open or focus Strategy Concept Window."""
        if self.strategy_concept_window is None:
            # Create new window
            self.strategy_concept_window = StrategyConceptWindow(
                parent=self,
                chart_window=self
            )
            self.strategy_concept_window.window_closed.connect(
                self._on_strategy_concept_closed
            )
            self.strategy_concept_window.patterns_detected.connect(
                self._on_patterns_detected
            )
            self.strategy_concept_window.strategy_selected.connect(
                self._on_strategy_selected
            )

        # Show and raise window
        self.strategy_concept_window.show()
        self.strategy_concept_window.raise_()
        self.strategy_concept_window.activateWindow()

        logger.info("Strategy Concept Window opened")

    def _on_strategy_concept_closed(self):
        """Handle Strategy Concept Window close."""
        logger.info("Strategy Concept Window closed")
        self.strategy_concept_window = None

    def _on_patterns_detected(self, patterns):
        """Handle patterns detected in Strategy Concept Window."""
        logger.info(f"Patterns detected: {len(patterns)}")

        # Optional: Draw patterns on chart
        # if hasattr(self, 'draw_patterns'):
        #     self.draw_patterns(patterns)

    def _on_strategy_selected(self, pattern_type, strategy_mapping):
        """Handle strategy selected in Strategy Concept Window."""
        logger.info(f"Strategy selected: {pattern_type}")

        # Optional: Apply strategy to Trading Bot
        # if hasattr(self, 'apply_strategy'):
        #     self.apply_strategy(pattern_type, strategy_mapping)
```

**Checklist:**
- [ ] Add "Strategy Concept" menu item to Analysis menu
- [ ] Add keyboard shortcut: Ctrl+Shift+S
- [ ] Add "Strategy Concept" button to toolbar (purple/magenta color)
- [ ] Implement `_on_strategy_concept_clicked()` handler
- [ ] Window lifecycle management (singleton pattern)
- [ ] Connect signals: `window_closed`, `patterns_detected`, `strategy_selected`
- [ ] Optional: Pattern drawing integration
- [ ] Optional: Trading Bot strategy integration
- [ ] Test: Menu item opens window
- [ ] Test: Button opens window
- [ ] Test: Shortcut works
- [ ] Test: Window singleton (only one instance)

---

## ✅ Gesamt-Checklist

### Phase 0: Shared Widgets
- [ ] `pattern_analysis_widgets.py` (PatternAnalysisSettings, PatternResultsDisplay, PatternMatchesTable)
- [ ] `chart_data_helper.py` (ChartDataHelper.get_bars_from_chart)
- [ ] Unit tests für Shared Widgets

### Phase 1: Core Infrastructure
- [ ] `strategy_models.py` (Pydantic Models, PATTERN_STRATEGIES)
- [ ] `pattern_strategy_mapper.py` (TradeSetup-Generierung)

### Phase 2: Tab 1 - Mustererkennung
- [ ] `pattern_recognition_widget.py` (nutzt Shared Widgets)
- [ ] Unit tests für Pattern Recognition Widget

### Phase 3: Tab 2 - Pattern Integration
- [ ] `pattern_integration_widget.py` (Strategy Mapping UI)
- [ ] Unit tests für Pattern Integration Widget

### Phase 4: Pattern Detectors
- [ ] Cup and Handle Detector (reversal_patterns.py)
- [ ] Triple Bottom Detector (reversal_patterns.py)
- [ ] Ascending Triangle Detector (continuation_patterns.py)
- [ ] Unit tests für alle 3 Detectors

### Phase 5: Strategy Concept Window
- [ ] `strategy_concept_window.py` (Haupt-Dialog, Tabs)
- [ ] Unit tests für Strategy Concept Window

### Phase 6: Chart Integration
- [ ] Menü-Eintrag "Strategy Concept"
- [ ] Toolbar-Button
- [ ] Keyboard-Shortcut (Ctrl+Shift+S)
- [ ] Signal-Handling (patterns_detected, strategy_selected)

---

## 📊 Zeitschätzung

| Phase | Zeitaufwand | Kumuliert |
|-------|-------------|-----------|
| Phase 0: Shared Widgets | 2-3h | 2-3h |
| Phase 1: Core Infrastructure | 4-6h | 6-9h |
| Phase 2: Tab 1 - Mustererkennung | 6-8h | 12-17h |
| Phase 3: Tab 2 - Pattern Integration | 6-8h | 18-25h |
| Phase 4: Pattern Detectors | 8-10h | 26-35h |
| Phase 5: Strategy Concept Window | 4-5h | 30-40h |
| Phase 6: Chart Integration | 2-3h | 32-43h |
| **GESAMT** | **32-43h** | **(4-5 Arbeitstage)** |

---

## 🎯 Nächste Schritte

1. **Phase 0 starten:** Shared Widgets erstellen (höchste Priorität)
2. **Iterativ implementieren:** Phase für Phase durcharbeiten
3. **Tests schreiben:** Jede Phase mit Unit Tests absichern
4. **Integration testen:** ChartWindow → Strategy Concept → Pattern Detection → Strategy Mapping
