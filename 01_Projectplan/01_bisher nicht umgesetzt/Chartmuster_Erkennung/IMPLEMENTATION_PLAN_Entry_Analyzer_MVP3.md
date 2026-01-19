## 🚀 MVP 3: Export API for CEL System (4-6h)

**Ziel:** Patterns als JSON/CSV exportieren für Verwendung im CEL-basierten Trading-System.

**Wichtig:** Dieses Modul ist NUR für Pattern Detection - Trading Rules werden im separaten CEL-System implementiert!

**Export-Formate:**
1. **JSON:** Strukturiertes Format mit vollständigen Pattern-Daten
2. **Marktanalyse.json:** Integration mit bestehendem Marktanalyse-Format (wie in `Chartmuster_Erkennung_BestPractice_Plan.md` spezifiziert)

---

### ✅ Schritt 3.1: Pattern Exporter Module (2-3h)

**Datei:** `src/analysis/patterns/pattern_exporter.py`

```python
"""Pattern Exporter - Export detected patterns to JSON/CSV for CEL system.

Exports patterns in standardized format for consumption by CEL-based trading rules.
"""

from __future__ import annotations

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

from src.analysis.patterns.base_detector import Pattern, Pivot

logger = logging.getLogger(__name__)


class PatternExporter:
    """Export patterns to JSON/CSV for CEL system integration."""

    def export_to_json(
        self,
        patterns: List[Pattern],
        output_path: str,
        include_metadata: bool = True
    ) -> None:
        """Export patterns to JSON file.

        Args:
            patterns: List of Pattern objects
            output_path: Output file path
            include_metadata: Include export metadata (timestamp, counts)
        """
        try:
            export_data = self._prepare_json_export(patterns, include_metadata)

            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported {len(patterns)} patterns to {output_path}")

        except Exception as e:
            logger.exception(f"Failed to export patterns to JSON: {e}")
            raise

    def export_to_marktanalyse_json(
        self,
        patterns: List[Pattern],
        output_path: str,
        timeframe: str = "1D",
        symbol: str = "BTCUSDT"
    ) -> None:
        """Export patterns to Marktanalyse.json format (compatible with existing system).

        Format matches specification in Chartmuster_Erkennung_BestPractice_Plan.md.

        Args:
            patterns: List of Pattern objects
            output_path: Output file path
            timeframe: Chart timeframe (e.g., "1D", "4H", "1H")
            symbol: Trading symbol
        """
        try:
            marktanalyse_data = {
                "metadata": {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "pattern_count": len(patterns)
                },
                "patterns": {
                    "reversal": self._filter_by_category(patterns, "REVERSAL"),
                    "continuation": self._filter_by_category(patterns, "CONTINUATION"),
                    "smart_money": self._filter_by_category(patterns, "SMART_MONEY"),
                    "trend_following": self._filter_by_category(patterns, "TREND_FOLLOWING")
                }
            }

            with open(output_path, 'w') as f:
                json.dump(marktanalyse_data, f, indent=2)

            logger.info(f"Exported patterns to Marktanalyse.json: {output_path}")

        except Exception as e:
            logger.exception(f"Failed to export to Marktanalyse.json: {e}")
            raise

    def export_to_csv(
        self,
        patterns: List[Pattern],
        output_path: str
    ) -> None:
        """Export patterns to CSV file (simplified format for spreadsheet analysis).

        Args:
            patterns: List of Pattern objects
            output_path: Output file path
        """
        try:
            rows = []

            for p in patterns:
                rows.append({
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "category": p.category,
                    "state": p.state.value,
                    "score": p.score,
                    "direction_bias": p.direction_bias.value,
                    "start_index": p.start_index,
                    "end_index": p.end_index,
                    "pivot_count": len(p.pivots),
                    "geometry_score": p.scoring_breakdown.get("geometry", 0),
                    "context_score": p.scoring_breakdown.get("context", 0),
                    "confirmation_score": p.scoring_breakdown.get("confirmation", 0)
                })

            df = pd.DataFrame(rows)
            df.to_csv(output_path, index=False)

            logger.info(f"Exported {len(patterns)} patterns to CSV: {output_path}")

        except Exception as e:
            logger.exception(f"Failed to export patterns to CSV: {e}")
            raise

    def _prepare_json_export(
        self,
        patterns: List[Pattern],
        include_metadata: bool
    ) -> Dict[str, Any]:
        """Prepare data for JSON export.

        Args:
            patterns: List of Pattern objects
            include_metadata: Include export metadata

        Returns:
            Dictionary ready for JSON serialization
        """
        export_data = {}

        if include_metadata:
            export_data["metadata"] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pattern_count": len(patterns),
                "categories": self._get_category_counts(patterns)
            }

        export_data["patterns"] = [
            self._pattern_to_dict(p) for p in patterns
        ]

        return export_data

    def _pattern_to_dict(self, pattern: Pattern) -> Dict[str, Any]:
        """Convert Pattern object to dictionary for JSON serialization.

        Args:
            pattern: Pattern object

        Returns:
            Dictionary representation
        """
        return {
            "pattern_id": pattern.pattern_id,
            "pattern_type": pattern.pattern_type,
            "category": pattern.category,
            "state": pattern.state.value,
            "score": pattern.score,
            "direction_bias": pattern.direction_bias.value,
            "start_index": pattern.start_index,
            "end_index": pattern.end_index,
            "pivots": [
                {
                    "index": pivot.index,
                    "type": pivot.pivot_type.value,
                    "price": pivot.price,
                    "timestamp": pivot.timestamp.isoformat()
                }
                for pivot in pattern.pivots
            ],
            "lines": {
                line_type: [
                    {"timestamp": ts.isoformat(), "price": price}
                    for ts, price in points
                ]
                for line_type, points in pattern.lines.items()
            },
            "scoring_breakdown": pattern.scoring_breakdown
        }

    def _filter_by_category(
        self,
        patterns: List[Pattern],
        category: str
    ) -> List[Dict[str, Any]]:
        """Filter patterns by category and convert to dict.

        Args:
            patterns: List of Pattern objects
            category: Category to filter by

        Returns:
            List of pattern dictionaries
        """
        filtered = [p for p in patterns if p.category == category]
        return [self._pattern_to_dict(p) for p in filtered]

    def _get_category_counts(self, patterns: List[Pattern]) -> Dict[str, int]:
        """Count patterns by category.

        Args:
            patterns: List of Pattern objects

        Returns:
            Dictionary with category counts
        """
        counts = {}
        for p in patterns:
            counts[p.category] = counts.get(p.category, 0) + 1
        return counts
```

---

### ✅ Schritt 3.2: Entry Analyzer Export Integration (1-2h)

**Ergänzung zu `src/ui/dialogs/entry_analyzer_popup.py`:**

```python
def _on_export_patterns_clicked(self):
    """Event Handler: Export Patterns to JSON/CSV.

    User can choose format:
    - Standard JSON
    - Marktanalyse.json (for integration with existing system)
    - CSV (for spreadsheet analysis)
    """
    if not hasattr(self, 'detected_patterns') or not self.detected_patterns:
        QMessageBox.warning(self, "No Patterns", "Please detect patterns first.")
        return

    try:
        # Ask user for export format
        format_dialog = QMessageBox(self)
        format_dialog.setWindowTitle("Export Format")
        format_dialog.setText("Choose export format:")

        json_btn = format_dialog.addButton("JSON (Standard)", QMessageBox.AcceptRole)
        markt_btn = format_dialog.addButton("Marktanalyse.json", QMessageBox.AcceptRole)
        csv_btn = format_dialog.addButton("CSV (Spreadsheet)", QMessageBox.AcceptRole)
        format_dialog.addButton("Cancel", QMessageBox.RejectRole)

        format_dialog.exec_()
        clicked = format_dialog.clickedButton()

        if clicked == json_btn:
            self._export_standard_json()
        elif clicked == markt_btn:
            self._export_marktanalyse_json()
        elif clicked == csv_btn:
            self._export_csv()

    except Exception as e:
        logger.exception("Export failed")
        QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")


def _export_standard_json(self):
    """Export patterns to standard JSON format."""
    from PyQt6.QtWidgets import QFileDialog
    from src.analysis.patterns.pattern_exporter import PatternExporter

    filename, _ = QFileDialog.getSaveFileName(
        self,
        "Export Patterns (JSON)",
        f"patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "JSON Files (*.json)"
    )

    if not filename:
        return

    exporter = PatternExporter()
    exporter.export_to_json(self.detected_patterns, filename, include_metadata=True)

    QMessageBox.information(
        self,
        "Success",
        f"Exported {len(self.detected_patterns)} patterns to:\n{filename}"
    )


def _export_marktanalyse_json(self):
    """Export patterns to Marktanalyse.json format."""
    from PyQt6.QtWidgets import QFileDialog
    from src.analysis.patterns.pattern_exporter import PatternExporter

    # Default filename
    default_filename = "Marktanalyse.json"

    filename, _ = QFileDialog.getSaveFileName(
        self,
        "Export Patterns (Marktanalyse.json)",
        default_filename,
        "JSON Files (*.json)"
    )

    if not filename:
        return

    # Get current symbol and timeframe from parent ChartWindow
    chart_window = self.parent()
    symbol = getattr(chart_window, 'current_symbol', 'BTCUSDT')
    timeframe = getattr(chart_window, 'current_timeframe', '1D')

    exporter = PatternExporter()
    exporter.export_to_marktanalyse_json(
        self.detected_patterns,
        filename,
        timeframe=timeframe,
        symbol=symbol
    )

    QMessageBox.information(
        self,
        "Success",
        f"Exported patterns to Marktanalyse.json:\n{filename}\n\n"
        f"Symbol: {symbol}\n"
        f"Timeframe: {timeframe}\n"
        f"Patterns: {len(self.detected_patterns)}"
    )


def _export_csv(self):
    """Export patterns to CSV format."""
    from PyQt6.QtWidgets import QFileDialog
    from src.analysis.patterns.pattern_exporter import PatternExporter

    filename, _ = QFileDialog.getSaveFileName(
        self,
        "Export Patterns (CSV)",
        f"patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "CSV Files (*.csv)"
    )

    if not filename:
        return

    exporter = PatternExporter()
    exporter.export_to_csv(self.detected_patterns, filename)

    QMessageBox.information(
        self,
        "Success",
        f"Exported {len(self.detected_patterns)} patterns to CSV:\n{filename}"
    )
```

---

### ✅ Schritt 3.3: Marktanalyse.json Format Specification (1h)

**Beispiel:** `Marktanalyse.json` Output Format (wie in Best Practice Plan spezifiziert)

```json
{
  "metadata": {
    "symbol": "BTCUSDT",
    "timeframe": "1D",
    "timestamp": "2024-12-15T10:30:00Z",
    "pattern_count": 8
  },
  "patterns": {
    "reversal": [
      {
        "pattern_id": "hs_top_125",
        "pattern_type": "head_and_shoulders_top",
        "category": "REVERSAL",
        "state": "CONFIRMED",
        "score": 85.5,
        "direction_bias": "DOWN",
        "start_index": 125,
        "end_index": 135,
        "pivots": [
          {"index": 125, "type": "HIGH", "price": 95500.0, "timestamp": "2024-12-01T00:00:00Z"},
          {"index": 128, "type": "LOW", "price": 94200.0, "timestamp": "2024-12-04T00:00:00Z"},
          {"index": 131, "type": "HIGH", "price": 96800.0, "timestamp": "2024-12-07T00:00:00Z"},
          {"index": 133, "type": "LOW", "price": 94300.0, "timestamp": "2024-12-09T00:00:00Z"},
          {"index": 135, "type": "HIGH", "price": 95600.0, "timestamp": "2024-12-11T00:00:00Z"}
        ],
        "lines": {
          "neckline": [
            {"timestamp": "2024-12-04T00:00:00Z", "price": 94200.0},
            {"timestamp": "2024-12-09T00:00:00Z", "price": 94300.0}
          ]
        },
        "scoring_breakdown": {
          "geometry": 55,
          "context": 15,
          "confirmation": 15.5
        }
      }
    ],
    "continuation": [],
    "smart_money": [
      {
        "pattern_id": "ob_bullish_142",
        "pattern_type": "order_block_bullish",
        "category": "SMART_MONEY",
        "state": "CONFIRMED",
        "score": 72.0,
        "direction_bias": "UP",
        "start_index": 142,
        "end_index": 142,
        "pivots": [],
        "lines": {
          "support": [
            {"timestamp": "2024-12-14T00:00:00Z", "price": 93800.0}
          ]
        },
        "scoring_breakdown": {
          "strength": 72.0,
          "mitigated": 100
        }
      }
    ],
    "trend_following": []
  }
}
```

---

### ✅ Schritt 3.4: Tests für Export (1h)

**Datei:** `tests/patterns/test_pattern_exporter.py`

```python
"""Tests for PatternExporter."""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from src.analysis.patterns.pattern_exporter import PatternExporter
from src.analysis.patterns.base_detector import (
    Pattern, Pivot, PatternState, DirectionBias, PivotType
)


@pytest.fixture
def sample_patterns():
    """Create sample patterns for testing."""
    pivots = [
        Pivot(0, PivotType.HIGH, 100.0, datetime(2024, 1, 1, tzinfo=timezone.utc)),
        Pivot(1, PivotType.LOW, 95.0, datetime(2024, 1, 2, tzinfo=timezone.utc)),
        Pivot(2, PivotType.HIGH, 105.0, datetime(2024, 1, 3, tzinfo=timezone.utc))
    ]

    lines = {
        "neckline": [
            (datetime(2024, 1, 2, tzinfo=timezone.utc), 95.0),
            (datetime(2024, 1, 4, tzinfo=timezone.utc), 96.0)
        ]
    }

    return [
        Pattern(
            pattern_id="hs_1",
            pattern_type="head_and_shoulders_top",
            category="REVERSAL",
            state=PatternState.CONFIRMED,
            score=85.0,
            direction_bias=DirectionBias.DOWN,
            start_index=0,
            end_index=2,
            pivots=pivots,
            lines=lines,
            scoring_breakdown={"geometry": 55, "context": 15, "confirmation": 15}
        ),
        Pattern(
            pattern_id="ob_1",
            pattern_type="order_block_bullish",
            category="SMART_MONEY",
            state=PatternState.CONFIRMED,
            score=72.0,
            direction_bias=DirectionBias.UP,
            start_index=5,
            end_index=5,
            pivots=[],
            lines={"support": [(datetime(2024, 1, 5, tzinfo=timezone.utc), 98.0)]},
            scoring_breakdown={"strength": 72.0}
        )
    ]


def test_export_to_json(sample_patterns):
    """Test JSON export."""
    exporter = PatternExporter()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "patterns.json"
        exporter.export_to_json(sample_patterns, str(output_path), include_metadata=True)

        # Verify file exists
        assert output_path.exists()

        # Verify content
        with open(output_path) as f:
            data = json.load(f)

        assert "metadata" in data
        assert data["metadata"]["pattern_count"] == 2
        assert "patterns" in data
        assert len(data["patterns"]) == 2


def test_export_to_marktanalyse_json(sample_patterns):
    """Test Marktanalyse.json export."""
    exporter = PatternExporter()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "Marktanalyse.json"
        exporter.export_to_marktanalyse_json(
            sample_patterns,
            str(output_path),
            timeframe="1D",
            symbol="BTCUSDT"
        )

        # Verify file exists
        assert output_path.exists()

        # Verify content
        with open(output_path) as f:
            data = json.load(f)

        assert data["metadata"]["symbol"] == "BTCUSDT"
        assert data["metadata"]["timeframe"] == "1D"
        assert "patterns" in data
        assert "reversal" in data["patterns"]
        assert "smart_money" in data["patterns"]
        assert len(data["patterns"]["reversal"]) == 1
        assert len(data["patterns"]["smart_money"]) == 1


def test_export_to_csv(sample_patterns):
    """Test CSV export."""
    exporter = PatternExporter()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "patterns.csv"
        exporter.export_to_csv(sample_patterns, str(output_path))

        # Verify file exists
        assert output_path.exists()

        # Verify content
        with open(output_path) as f:
            lines = f.readlines()

        # Header + 2 data rows
        assert len(lines) == 3
        assert "pattern_id" in lines[0]
        assert "hs_1" in lines[1]
        assert "ob_1" in lines[2]
```

---

**Checklist (MVP 3):**
- [ ] `PatternExporter` implementiert (`pattern_exporter.py`)
- [ ] JSON Export (Standard-Format) funktioniert
- [ ] Marktanalyse.json Export (CEL-kompatibel) funktioniert
- [ ] CSV Export für Spreadsheet-Analyse
- [ ] Entry Analyzer "Export" Button integriert
- [ ] Format-Auswahl-Dialog (JSON / Marktanalyse / CSV)
- [ ] Tests für alle Export-Formate
- [ ] Test: Pattern exportieren → JSON mit allen Feldern korrekt
- [ ] Test: Marktanalyse.json hat korrekte Struktur (metadata + patterns by category)

---

## 📚 Optional: Advanced Features (bei Bedarf)

Die folgenden Features können nach MVP 1-3 hinzugefügt werden, sind aber NICHT required für Core-Funktionalität:

### Optional 1: Triangle Patterns (3-4h)
- Ascending Triangle
- Descending Triangle
- Symmetrical Triangle

### Optional 2: Similarity Search mit DTW (4-6h)
- Dynamic Time Warping für historische Pattern-Suche
- Sliding Window über vergangene Bars
- Top-K ähnlichste Patterns mit Score

### Optional 3: Trend Following Patterns (3-4h)
- Flags
- Pennants
- Rectangles

### Optional 4: Pattern Details Popup (2-3h)
- Separate Dialog für komplexe Pattern-Ansicht
- Chart Preview mit Pattern-Overlay
- Scoring-Breakdown Visualisierung

---

## ✅ Final Checklist (Gesamtes Projekt)

### Setup (Phase 0):
- [ ] Git Branch erstellt (`feature/chartmuster-erkennung`)
- [ ] Dependencies installiert (`scipy`, `PatternPy`, `fastdtw`, etc.)
- [ ] Projektstruktur angelegt (`src/analysis/patterns/`, `tests/patterns/`)

### MVP 1 - Foundation:
- [ ] Pivot Engine (ZigZag + ATR) implementiert und getestet
- [ ] Base Detector (ABC) implementiert
- [ ] Head & Shoulders Detector (Top + Bottom)
- [ ] Double Top/Bottom Detector
- [ ] Entry Analyzer Pattern Tab (2-Spalten Layout)
- [ ] Chart Overlay Mixin (Pattern-Visualisierung)

### MVP 2 - Smart Money Concepts:
- [ ] Order Block Detector (Bullish + Bearish)
- [ ] Fair Value Gap Detector
- [ ] Integration in Entry Analyzer
- [ ] Pattern Tree "Smart Money" Kategorie

### MVP 3 - Export API:
- [ ] Pattern Exporter Modul
- [ ] JSON Export (Standard + Marktanalyse.json)
- [ ] CSV Export
- [ ] Entry Analyzer Export-Integration

### Tests & Validation:
- [ ] Unit Tests für alle Detektoren (>80% Coverage)
- [ ] Integration Tests (Entry Analyzer → Pattern Detection → Chart Overlay)
- [ ] Manual Test: BTCUSDT 1D Chart → Mindestens 10 Patterns verschiedener Typen
- [ ] Performance Test: 1000 Bars in <5 Sekunden

### Documentation:
- [ ] README.md mit Nutzungsanleitung
- [ ] Modul-Docstrings vollständig
- [ ] Beispiel-Notebooks (optional)

---

## 🎯 Erfolgskriterien

**Minimum Viable Product (MVP 1-3) erfüllt wenn:**
1. ✅ Pivot Engine detektiert Swing Highs/Lows korrekt (>95% Genauigkeit auf Test-Daten)
2. ✅ Head & Shoulders Pattern werden erkannt (Score >80 für klare Patterns)
3. ✅ Double Top/Bottom Pattern werden erkannt
4. ✅ Order Blocks und Fair Value Gaps werden detektiert
5. ✅ Entry Analyzer Tab zeigt Patterns in Tabelle
6. ✅ "Draw on Chart" Button zeigt Patterns im Chart (Necklines, Pivots, Labels)
7. ✅ Export zu JSON/CSV funktioniert fehlerfrei
8. ✅ Marktanalyse.json hat korrektes Format (CEL-kompatibel)

**Performance-Ziele:**
- Pivot Detection: <200ms für 1000 Bars
- Pattern Detection (alle Typen): <1s für 1000 Bars
- Chart Overlay Rendering: <200ms

**Qualitätsziele:**
- Unit Test Coverage: >80%
- No pylint/flake8 warnings
- Type hints überall vorhanden
- Logging auf INFO/DEBUG level korrekt

---

## 🚀 Next Steps nach Fertigstellung

1. **Integration Testing:** Vollständiger Test mit echten BTCUSDT-Daten (1 Monat)
2. **Parameter Tuning:** Optimierung der Detection-Parameter (Thresholds, Toleranzen)
3. **Performance Profiling:** cProfile für Bottleneck-Identifikation
4. **Optional Features:** Triangle Patterns, DTW Similarity Search
5. **CEL Integration:** Übergabe an CEL-Team für Trading Rules Implementation

---

## 📝 Hinweise für Entwickler

### Code-Style:
- PEP 8 konform
- Type hints überall
- Docstrings (Google-Style)
- Logging statt print()

### Testing:
- Pytest für Unit Tests
- Fixtures für Sample-Data
- Mocking für UI-Tests (ChartWindow)

### Git Workflow:
- Feature Branch: `feature/chartmuster-erkennung`
- Commits: `git commit -m "feat: Add Head & Shoulders Detector"`
- Pull Request mit vollständiger Beschreibung

### Performance:
- Pandas Vectorization statt Loops
- Caching für teure Berechnungen (ATR)
- Profiling bei Performance-Problemen

---

**🎉 ENDE DES IMPLEMENTATION PLANS**

Dieser Plan ist nun VOLLSTÄNDIG und enthält:
- ✅ MVP 1: Foundation (Pivot Engine, H&S, Double Top/Bottom, Entry Analyzer UI, Chart Overlay)
- ✅ MVP 2: Smart Money Concepts (Order Blocks, Fair Value Gaps)
- ✅ MVP 3: Export API (JSON/CSV/Marktanalyse.json)
- ✅ Complete Code für alle Module (>2500 Lines)
- ✅ Tests für alle Komponenten
- ✅ Checklists für jede Phase
- ✅ Optional Features (für später)
- ✅ Final Checklist & Erfolgskriterien

**Ready für Implementation! 🚀**
