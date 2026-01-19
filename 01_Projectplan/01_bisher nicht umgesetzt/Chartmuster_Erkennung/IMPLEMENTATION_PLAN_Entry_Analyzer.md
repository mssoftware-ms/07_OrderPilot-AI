# 🚀 Implementation Plan: Pattern Recognition im Entry Analyzer

**Erstellt:** 2026-01-19 16:30
**Ziel:** Chartmuster-Erkennung in **Entry Analyzer** integrieren
**Strategie:** Kompakter Tab + Detailliertes Popup für komplexe Ansichten
**Fokus:** Schnelle Implementierung mit iterativer Erweiterung

---

## 📋 Executive Summary

### Was wird implementiert?
1. **Pattern Recognition Tab** im Entry Analyzer (`src/ui/dialogs/entry_analyzer_popup.py`)
2. **Pattern Detection Engine** (Backend: `src/analysis/patterns/`)
3. **Pattern Details Popup** für komplexe Pattern-Analyse (optional, bei Bedarf)
4. **Chart Overlay Integration** für visuelle Pattern-Darstellung

### Integration im Entry Analyzer
- **Bestehendes Modul:** `src/ui/dialogs/entry_analyzer_popup.py` (Zeilen 1-958)
- **Neuer Tab:** "📊 Pattern Recognition" nach "Validation" Tab (Zeile ~250)
- **Layout:** 2-Spalten (kompakt) mit "Details"-Button für Popup

### Warum kein separates Modul?
- ✅ Entry Analyzer hat bereits Chart-Anbindung
- ✅ Tabs sind vorhanden und erweiterbar
- ✅ Konsistente UI mit anderen Analysis-Features
- ✅ Popup nur bei Bedarf (komplexe Pattern-Details)

---

## 🎯 Delivery Phasen (Iterativ)

### MVP 1: Foundation (2-3 Tage)
**Deliverable:** Pivot Engine + Top 3 Patterns erkennbar
- ✅ Pivot Detection (ZigZag/ATR)
- ✅ Head & Shoulders (Top/Bottom)
- ✅ Double Top/Bottom
- ✅ Basic UI Tab (Pattern-Liste)
- ✅ Chart Overlay (Necklines zeichnen)

**Erfolg:** User kann H&S und Double Tops im Chart sehen

### MVP 2: Smart Money + UI Polish (2-3 Tage)
**Deliverable:** SMC Patterns + Pattern Details Popup
- ✅ Order Blocks Detection
- ✅ Fair Value Gaps
- ✅ Pattern Details Popup (bei Click auf Pattern)
- ✅ Pattern Scoring System (0-100)

**Erfolg:** User kann Order Blocks + FVGs identifizieren und Details ansehen

### MVP 3: Export + Backtesting (1-2 Tage)
**Deliverable:** CEL-Integration vorbereitet
- ✅ JSON/CSV Export für CEL-System
- ✅ Forward Return Analysis
- ✅ Pattern Accuracy Backtests

**Erfolg:** Patterns können exportiert und in CEL-Regeln verwendet werden

### Optional: Advanced Features (nach MVP 3)
- ⏳ Triangle Patterns (Ascending, Descending, Symmetric)
- ⏳ Similarity Search (DTW-basiert)
- ⏳ Trend Following Patterns (Channels, Breakouts)
- ⏳ Flags & Pennants

---

## 🏗️ Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                  Entry Analyzer Dialog                       │
│  (src/ui/dialogs/entry_analyzer_popup.py)                   │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ Backtest     │ Visible      │ Backtest     │ AI Copilot     │
│ Setup        │ Range        │ Results      │                │
│              │ Analysis     │              │                │
├──────────────┴──────────────┴──────────────┴────────────────┤
│ Validation                                                   │
├──────────────────────────────────────────────────────────────┤
│ 📊 Pattern Recognition ⭐ NEU                                │
│ ┌────────────────────────┬─────────────────────────────────┐│
│ │ Pattern Categories     │ Detected Patterns              ││
│ │ (Tree with Counts)     │ (Table with Quick-Actions)     ││
│ │                        │                                ││
│ │ ↩️ Reversal (8)        │ Pattern Type | State | Score  ││
│ │  ├ H&S Top (3)        │ H&S Top      | 🟢    | 89     ││
│ │  └ Double Top (5)     │ Double Top   | 🔴    | 72     ││
│ │                        │ Order Block  | 🟢    | 95     ││
│ │ 💰 Smart Money (12)    │                                ││
│ │  ├ Order Blocks (8)   │ [Detect] [Details] [Export]    ││
│ │  └ FVG (4)            │                                ││
│ └────────────────────────┴─────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
                           │
                           │ On "Details" Button Click
                           ▼
┌──────────────────────────────────────────────────────────────┐
│         Pattern Details Popup (Optional)                     │
│  (src/ui/dialogs/pattern_details_dialog.py) ⭐ NEU           │
├──────────────────────────────────────────────────────────────┤
│ Pattern: Head & Shoulders Top                                │
│ Score: 89/100 | State: 🟢 CONFIRMED                          │
│                                                              │
│ ┌─────────────────────┬────────────────────────────────────┐│
│ │ Geometry Details    │ Chart Preview                      ││
│ │                     │ [Mini-Chart with Pattern]          ││
│ │ Left Shoulder:  123 │                                    ││
│ │ Head:           145 │                                    ││
│ │ Right Shoulder: 167 │                                    ││
│ │ Neckline: y=0.98x   │                                    ││
│ └─────────────────────┴────────────────────────────────────┘│
│                                                              │
│ Scoring Breakdown:                                           │
│ - Geometry:      52/60 [████████████░░░░]                   │
│ - Context:       18/20 [█████████░]                         │
│ - Confirmation:  19/20 [█████████░]                         │
│                                                              │
│ Forward Returns (Historical Similar Patterns):               │
│ - +5 Days:  -2.3% avg (Win Rate: 89%)                      │
│ - +10 Days: -4.5% avg (Win Rate: 91%)                      │
│ - +20 Days: -6.8% avg (Win Rate: 87%)                      │
│                                                              │
│ [Export JSON] [Export CSV] [Draw on Chart] [Close]          │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 Neue Dateien (Übersicht)

### Backend (Pattern Detection)
```
src/analysis/patterns/
├── __init__.py                      # NEW: Package init mit exports
├── pivot_engine.py                  # NEW: ZigZag/ATR Pivot Detection
├── base_detector.py                 # NEW: Abstract PatternDetector Base Class
├── reversal_patterns.py             # NEW: H&S, Double Top/Bottom
├── smart_money.py                   # NEW: Order Blocks, FVG
├── pattern_scorer.py                # NEW: Scoring System (0-100)
└── pattern_exporter.py              # NEW: JSON/CSV Export für CEL
```

### UI (Entry Analyzer Integration)
```
src/ui/dialogs/
├── entry_analyzer_popup.py          # MODIFY: Add Pattern Recognition Tab
└── pattern_details_dialog.py        # NEW: Optional Details Popup

src/ui/widgets/chart_mixins/
└── pattern_overlay_mixin.py         # NEW: Chart Pattern Visualization
```

### Tests
```
tests/patterns/
├── test_pivot_engine.py             # NEW: Pivot Detection Tests
├── test_reversal_patterns.py        # NEW: H&S, Double Top Tests
├── test_smart_money.py              # NEW: Order Blocks, FVG Tests
└── fixtures/
    └── btcusdt_1d_sample.csv        # NEW: Test Data (1000 Bars)
```

---

## 🔧 Phase-by-Phase Implementation

---

## 🚀 MVP 1: Foundation (2-3 Tage, ~16-24h)

### ✅ Schritt 1.1: Git Branch & Setup (30 Min)

**Ziel:** Entwicklungsumgebung vorbereiten

```bash
# Git Branch
git checkout -b feature/pattern-recognition-entry-analyzer
git push -u origin feature/pattern-recognition-entry-analyzer

# Dependencies (prüfen ob bereits vorhanden)
pip install scipy>=1.11.0
pip install ta-lib>=0.4.28
pip install scikit-learn>=1.3.0
```

**Checklist:**
- [ ] Git Branch erstellt und gepusht
- [ ] Dependencies installiert (scipy, ta-lib, scikit-learn)
- [ ] Test-Run: `pytest tests/` läuft ohne Fehler

---

### ✅ Schritt 1.2: Ordnerstruktur erstellen (15 Min)

**Dateien erstellen:**

```bash
# Backend Pattern Detection
mkdir -p src/analysis/patterns
touch src/analysis/patterns/__init__.py
touch src/analysis/patterns/pivot_engine.py
touch src/analysis/patterns/base_detector.py
touch src/analysis/patterns/reversal_patterns.py
touch src/analysis/patterns/pattern_scorer.py

# Tests
mkdir -p tests/patterns
mkdir -p tests/patterns/fixtures
touch tests/patterns/__init__.py
touch tests/patterns/test_pivot_engine.py
touch tests/patterns/test_reversal_patterns.py
```

**Checklist:**
- [ ] Ordnerstruktur `src/analysis/patterns/` erstellt
- [ ] Ordnerstruktur `tests/patterns/` erstellt
- [ ] Alle `__init__.py` Dateien vorhanden

---

### ✅ Schritt 1.3: Pivot Engine implementieren (3-4h)

**Datei:** `src/analysis/patterns/pivot_engine.py`

**Code:**
```python
"""Pivot Detection Engine für Chart Pattern Recognition.

Implementiert ZigZag-basierte Pivot Detection mit ATR-Anpassung.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PivotType(Enum):
    """Pivot-Typen."""
    HIGH = "HIGH"
    LOW = "LOW"


@dataclass
class Pivot:
    """Ein Swing High oder Swing Low Punkt."""
    index: int
    type: PivotType
    price: float
    timestamp: pd.Timestamp

    def __repr__(self) -> str:
        return f"Pivot({self.type.value}, idx={self.index}, price={self.price:.2f})"


class PivotEngine:
    """Pivot Detection Engine mit ZigZag & ATR."""

    def __init__(
        self,
        threshold_pct: float = 2.0,
        atr_period: int = 14,
        atr_multiplier: float = 1.5,
        min_pivot_distance: int = 3,
        use_atr: bool = True
    ):
        """
        Args:
            threshold_pct: Prozent-Threshold für ZigZag (wenn use_atr=False)
            atr_period: ATR-Periode für adaptive Threshold
            atr_multiplier: Multiplier für ATR-basierte Threshold
            min_pivot_distance: Mindestabstand zwischen Pivots (Bars)
            use_atr: True = ATR-basiert, False = Prozent-basiert
        """
        self.threshold_pct = threshold_pct
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.min_pivot_distance = min_pivot_distance
        self.use_atr = use_atr

    def detect_pivots(self, data: pd.DataFrame) -> List[Pivot]:
        """Detektiere Swing Highs und Swing Lows.

        Args:
            data: DataFrame mit OHLC Daten (Index = Timestamp)

        Returns:
            Liste von Pivot-Objekten (chronologisch sortiert)
        """
        if len(data) < self.min_pivot_distance * 2:
            logger.warning(f"Zu wenig Daten für Pivot Detection: {len(data)} Bars")
            return []

        # ATR berechnen falls aktiviert
        if self.use_atr:
            atr = self._calculate_atr(data)
            threshold = atr * self.atr_multiplier
        else:
            threshold = data['close'].iloc[-1] * (self.threshold_pct / 100.0)

        logger.debug(f"Pivot Detection: threshold={threshold:.2f}, use_atr={self.use_atr}")

        # ZigZag Algorithm
        pivots = []
        direction = 0  # 0=unbekannt, 1=up, -1=down
        last_pivot_idx = 0
        last_pivot_price = data['close'].iloc[0]

        for i in range(1, len(data)):
            high = data['high'].iloc[i]
            low = data['low'].iloc[i]

            if direction == 0:
                # Initiale Richtung finden
                if high > last_pivot_price + threshold:
                    direction = 1
                    last_pivot_idx = i
                    last_pivot_price = high
                elif low < last_pivot_price - threshold:
                    direction = -1
                    last_pivot_idx = i
                    last_pivot_price = low

            elif direction == 1:
                # Uptrend: Suche höheren High oder Reversal
                if high > last_pivot_price:
                    last_pivot_idx = i
                    last_pivot_price = high
                elif low < last_pivot_price - threshold:
                    # Pivot High gefunden
                    if i - last_pivot_idx >= self.min_pivot_distance:
                        pivot = Pivot(
                            index=last_pivot_idx,
                            type=PivotType.HIGH,
                            price=last_pivot_price,
                            timestamp=data.index[last_pivot_idx]
                        )
                        pivots.append(pivot)
                        logger.debug(f"Pivot HIGH @ {pivot.index}: {pivot.price:.2f}")

                    # Reversal zu Downtrend
                    direction = -1
                    last_pivot_idx = i
                    last_pivot_price = low

            elif direction == -1:
                # Downtrend: Suche tieferen Low oder Reversal
                if low < last_pivot_price:
                    last_pivot_idx = i
                    last_pivot_price = low
                elif high > last_pivot_price + threshold:
                    # Pivot Low gefunden
                    if i - last_pivot_idx >= self.min_pivot_distance:
                        pivot = Pivot(
                            index=last_pivot_idx,
                            type=PivotType.LOW,
                            price=last_pivot_price,
                            timestamp=data.index[last_pivot_idx]
                        )
                        pivots.append(pivot)
                        logger.debug(f"Pivot LOW @ {pivot.index}: {pivot.price:.2f}")

                    # Reversal zu Uptrend
                    direction = 1
                    last_pivot_idx = i
                    last_pivot_price = high

        logger.info(f"Detected {len(pivots)} pivots from {len(data)} bars")
        return pivots

    def _calculate_atr(self, data: pd.DataFrame, period: int = None) -> float:
        """Berechne Average True Range.

        Args:
            data: DataFrame mit OHLC
            period: ATR Periode (default: self.atr_period)

        Returns:
            ATR Wert (aktueller)
        """
        if period is None:
            period = self.atr_period

        high = data['high']
        low = data['low']
        close = data['close']

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR (Exponential Moving Average)
        atr = tr.ewm(span=period, adjust=False).mean()

        return float(atr.iloc[-1])
```

**Tests:** `tests/patterns/test_pivot_engine.py`
```python
"""Tests für Pivot Engine."""

import pandas as pd
import pytest
from src.analysis.patterns.pivot_engine import PivotEngine, PivotType


def test_pivot_detection_simple():
    """Test: ZigZag findet einfache Swing-Punkte."""
    # Einfache Daten: Up-Down-Up
    data = pd.DataFrame({
        'open': [100, 101, 102, 101, 100],
        'high': [101, 103, 104, 102, 101],
        'low': [99, 100, 101, 99, 98],
        'close': [100.5, 102, 103, 100, 99]
    }, index=pd.date_range('2024-01-01', periods=5, freq='1D'))

    engine = PivotEngine(threshold_pct=1.5, use_atr=False)
    pivots = engine.detect_pivots(data)

    assert len(pivots) >= 2  # Mind. 1 HIGH und 1 LOW
    assert any(p.type == PivotType.HIGH for p in pivots)
    assert any(p.type == PivotType.LOW for p in pivots)


def test_atr_based_pivot_detection():
    """Test: ATR-basierte Pivot Detection passt sich an Volatilität an."""
    # Volatile Daten erstellen
    data = pd.DataFrame({
        'open': range(100, 120),
        'high': [i + 5 for i in range(100, 120)],
        'low': [i - 5 for i in range(100, 120)],
        'close': [i + 2 for i in range(100, 120)]
    }, index=pd.date_range('2024-01-01', periods=20, freq='1D'))

    engine = PivotEngine(atr_multiplier=2.0, use_atr=True)
    pivots = engine.detect_pivots(data)

    assert len(pivots) > 0  # Sollte Pivots finden


def test_min_pivot_distance():
    """Test: Mindestabstand zwischen Pivots wird respektiert."""
    data = pd.DataFrame({
        'open': [100, 102, 101, 103, 102, 104],
        'high': [101, 103, 102, 104, 103, 105],
        'low': [99, 101, 100, 102, 101, 103],
        'close': [100, 102, 101, 103, 102, 104]
    }, index=pd.date_range('2024-01-01', periods=6, freq='1D'))

    engine = PivotEngine(threshold_pct=1.0, min_pivot_distance=2, use_atr=False)
    pivots = engine.detect_pivots(data)

    # Prüfe Abstände
    for i in range(1, len(pivots)):
        distance = pivots[i].index - pivots[i-1].index
        assert distance >= 2  # min_pivot_distance
```

**Checklist:**
- [ ] `pivot_engine.py` implementiert (ZigZag + ATR)
- [ ] Tests in `test_pivot_engine.py` geschrieben (3+ Test Cases)
- [ ] Tests laufen durch: `pytest tests/patterns/test_pivot_engine.py -v`
- [ ] Performance-Test: <200ms für 1000 Bars

---

### ✅ Schritt 1.4: Base Detector Class (1h)

**Datei:** `src/analysis/patterns/base_detector.py`

```python
"""Base Class für Pattern Detectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from src.analysis.patterns.pivot_engine import Pivot


class PatternState(Enum):
    """Pattern Status."""
    FORMING = "FORMING"        # Pattern bildet sich
    CONFIRMED = "CONFIRMED"    # Pattern bestätigt (Breakout)
    FAILED = "FAILED"          # Pattern fehlgeschlagen
    INVALIDATED = "INVALIDATED"  # Pattern ungültig geworden


class DirectionBias(Enum):
    """Richtungs-Tendenz des Patterns."""
    UP = "UP"
    DOWN = "DOWN"
    NONE = "NONE"


@dataclass
class Pattern:
    """Erkanntes Chart-Pattern."""
    pattern_id: str
    pattern_type: str
    category: str  # "REVERSAL", "CONTINUATION", "SMART_MONEY", "TREND_FOLLOWING"
    state: PatternState
    score: float  # 0-100
    direction_bias: DirectionBias
    start_index: int
    end_index: int
    pivots: List[Pivot]
    lines: Dict[str, List[tuple]]  # {"neckline": [(timestamp, price), ...]}
    scoring_breakdown: Dict[str, float]  # {"geometry": 52.0, "context": 18.0, ...}

    def __repr__(self) -> str:
        return (f"Pattern({self.pattern_type}, score={self.score:.1f}, "
                f"state={self.state.value}, bias={self.direction_bias.value})")


class PatternDetector(ABC):
    """Abstract Base Class für Pattern Detection."""

    @abstractmethod
    def detect(self, pivots: List[Pivot], data=None) -> List[Pattern]:
        """Detektiere Patterns aus Pivot-Punkten.

        Args:
            pivots: Liste von Swing Highs/Lows
            data: Optional OHLC DataFrame für Kontext (Volume, etc.)

        Returns:
            Liste erkannter Patterns
        """
        pass

    @abstractmethod
    def calculate_score(self, pattern: Pattern, data=None) -> float:
        """Berechne Pattern Score (0-100).

        Args:
            pattern: Pattern-Objekt
            data: Optional OHLC DataFrame für Kontext

        Returns:
            Score zwischen 0-100
        """
        pass

    @abstractmethod
    def generate_lines(self, pattern: Pattern) -> Dict[str, List[tuple]]:
        """Generiere Geometrie-Linien für Chart-Overlay.

        Args:
            pattern: Pattern-Objekt

        Returns:
            Dict mit Line-Namen und Koordinaten
            z.B. {"neckline": [(timestamp, price), ...]}
        """
        pass
```

**Checklist:**
- [ ] `base_detector.py` implementiert (ABC Pattern)
- [ ] `Pattern`, `PatternState`, `DirectionBias` Dataclasses/Enums
- [ ] Keine Tests nötig (Abstract Class)

---

### ✅ Schritt 1.5: Head & Shoulders Detector (4-5h)

**Datei:** `src/analysis/patterns/reversal_patterns.py`

```python
"""Reversal Pattern Detectors: Head & Shoulders, Double Top/Bottom."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.analysis.patterns.base_detector import (
    DirectionBias,
    Pattern,
    PatternDetector,
    PatternState,
)
from src.analysis.patterns.pivot_engine import Pivot, PivotType

logger = logging.getLogger(__name__)


class HeadAndShouldersDetector(PatternDetector):
    """Head & Shoulders (Top/Bottom) Pattern Detector."""

    def __init__(
        self,
        shoulder_tolerance_pct: float = 2.0,
        trough_tolerance_pct: float = 1.5,
        min_head_prominence: float = 0.03  # 3% höher/tiefer als Shoulders
    ):
        """
        Args:
            shoulder_tolerance_pct: Toleranz für Shoulder-Symmetrie (%)
            trough_tolerance_pct: Toleranz für Neckline-Alignment (%)
            min_head_prominence: Min. Höhe/Tiefe des Heads relativ zu Shoulders
        """
        self.shoulder_tolerance_pct = shoulder_tolerance_pct
        self.trough_tolerance_pct = trough_tolerance_pct
        self.min_head_prominence = min_head_prominence

    def detect(self, pivots: List[Pivot], data: pd.DataFrame = None) -> List[Pattern]:
        """Detektiere H&S Patterns.

        5-Pivot Struktur (Top):
        - LS (Pivot HIGH)
        - Trough1 (Pivot LOW)
        - Head (Pivot HIGH)
        - Trough2 (Pivot LOW)
        - RS (Pivot HIGH)

        Args:
            pivots: Liste von Pivots
            data: Optional OHLC DataFrame

        Returns:
            Liste erkannter H&S Patterns
        """
        patterns = []

        # Mind. 5 Pivots benötigt
        if len(pivots) < 5:
            return patterns

        # Sliding Window über Pivots (5er Gruppen)
        for i in range(len(pivots) - 4):
            p1, p2, p3, p4, p5 = pivots[i:i+5]

            # Prüfe auf H&S Top Pattern
            if self._is_hs_top(p1, p2, p3, p4, p5):
                pattern = self._create_hs_pattern(
                    pivots=[p1, p2, p3, p4, p5],
                    pattern_type="HEAD_AND_SHOULDERS_TOP",
                    direction_bias=DirectionBias.DOWN,
                    data=data
                )
                patterns.append(pattern)
                logger.info(f"H&S Top detected: {pattern}")

            # Prüfe auf H&S Bottom Pattern (Inverse)
            elif self._is_hs_bottom(p1, p2, p3, p4, p5):
                pattern = self._create_hs_pattern(
                    pivots=[p1, p2, p3, p4, p5],
                    pattern_type="HEAD_AND_SHOULDERS_BOTTOM",
                    direction_bias=DirectionBias.UP,
                    data=data
                )
                patterns.append(pattern)
                logger.info(f"H&S Bottom detected: {pattern}")

        return patterns

    def _is_hs_top(self, ls: Pivot, t1: Pivot, head: Pivot, t2: Pivot, rs: Pivot) -> bool:
        """Prüfe ob 5 Pivots ein H&S Top bilden.

        Kriterien:
        - LS, Head, RS müssen HIGH sein
        - T1, T2 müssen LOW sein
        - Head höher als beide Shoulders
        - Shoulders im Toleranzband
        - Troughs bilden Neckline (ähnliches Niveau)
        """
        # Pivot-Typen prüfen
        if not (ls.type == PivotType.HIGH and t1.type == PivotType.LOW and
                head.type == PivotType.HIGH and t2.type == PivotType.LOW and
                rs.type == PivotType.HIGH):
            return False

        # Head muss höher als Shoulders sein
        if not (head.price > ls.price and head.price > rs.price):
            return False

        # Min. Head-Prominence
        avg_shoulder = (ls.price + rs.price) / 2
        prominence = (head.price - avg_shoulder) / avg_shoulder
        if prominence < self.min_head_prominence:
            return False

        # Shoulder-Symmetrie prüfen
        shoulder_diff_pct = abs(ls.price - rs.price) / avg_shoulder * 100
        if shoulder_diff_pct > self.shoulder_tolerance_pct:
            return False

        # Trough-Alignment (Neckline)
        avg_trough = (t1.price + t2.price) / 2
        trough_diff_pct = abs(t1.price - t2.price) / avg_trough * 100
        if trough_diff_pct > self.trough_tolerance_pct:
            return False

        return True

    def _is_hs_bottom(self, ls: Pivot, t1: Pivot, head: Pivot, t2: Pivot, rs: Pivot) -> bool:
        """Prüfe ob 5 Pivots ein H&S Bottom bilden (inverse)."""
        # Pivot-Typen prüfen (inverse: LOW-HIGH-LOW-HIGH-LOW)
        if not (ls.type == PivotType.LOW and t1.type == PivotType.HIGH and
                head.type == PivotType.LOW and t2.type == PivotType.HIGH and
                rs.type == PivotType.LOW):
            return False

        # Head muss tiefer als Shoulders sein
        if not (head.price < ls.price and head.price < rs.price):
            return False

        # Min. Head-Prominence
        avg_shoulder = (ls.price + rs.price) / 2
        prominence = (avg_shoulder - head.price) / avg_shoulder
        if prominence < self.min_head_prominence:
            return False

        # Shoulder-Symmetrie
        shoulder_diff_pct = abs(ls.price - rs.price) / avg_shoulder * 100
        if shoulder_diff_pct > self.shoulder_tolerance_pct:
            return False

        # Trough-Alignment (Neckline, hier Peaks)
        avg_peak = (t1.price + t2.price) / 2
        peak_diff_pct = abs(t1.price - t2.price) / avg_peak * 100
        if peak_diff_pct > self.trough_tolerance_pct:
            return False

        return True

    def _create_hs_pattern(
        self,
        pivots: List[Pivot],
        pattern_type: str,
        direction_bias: DirectionBias,
        data: Optional[pd.DataFrame]
    ) -> Pattern:
        """Erstelle Pattern-Objekt für H&S."""
        ls, t1, head, t2, rs = pivots

        # Pattern ID
        pattern_id = f"{pattern_type}_{ls.index}"

        # State: FORMING (Breakout-Check später)
        state = PatternState.FORMING

        # Score berechnen
        score = self.calculate_score(
            Pattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                category="REVERSAL",
                state=state,
                score=0.0,  # Wird gleich berechnet
                direction_bias=direction_bias,
                start_index=ls.index,
                end_index=rs.index,
                pivots=pivots,
                lines={},
                scoring_breakdown={}
            ),
            data=data
        )

        # Geometrie-Linien
        lines = self.generate_lines(
            Pattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                category="REVERSAL",
                state=state,
                score=score,
                direction_bias=direction_bias,
                start_index=ls.index,
                end_index=rs.index,
                pivots=pivots,
                lines={},
                scoring_breakdown={}
            )
        )

        return Pattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            category="REVERSAL",
            state=state,
            score=score,
            direction_bias=direction_bias,
            start_index=ls.index,
            end_index=rs.index,
            pivots=pivots,
            lines=lines,
            scoring_breakdown={}  # Wird in calculate_score gefüllt
        )

    def calculate_score(self, pattern: Pattern, data: Optional[pd.DataFrame] = None) -> float:
        """Berechne H&S Score (0-100).

        Komponenten:
        - Geometry (0-60): Shoulder-Symmetrie, Trough-Alignment, Head-Prominence
        - Context (0-20): Trend vor Pattern, Volume
        - Confirmation (0-20): Breakout bestätigt
        """
        ls, t1, head, t2, rs = pattern.pivots

        # Geometry Score (0-60)
        geometry_score = 0.0

        # 1. Shoulder-Symmetrie (0-30)
        avg_shoulder = (ls.price + rs.price) / 2
        shoulder_diff_pct = abs(ls.price - rs.price) / avg_shoulder * 100
        shoulder_symmetry = max(0, 30 * (1 - shoulder_diff_pct / self.shoulder_tolerance_pct))
        geometry_score += shoulder_symmetry

        # 2. Trough-Alignment (0-15)
        if pattern.pattern_type.endswith("TOP"):
            avg_trough = (t1.price + t2.price) / 2
            trough_diff_pct = abs(t1.price - t2.price) / avg_trough * 100
        else:  # BOTTOM
            avg_trough = (t1.price + t2.price) / 2
            trough_diff_pct = abs(t1.price - t2.price) / avg_trough * 100

        trough_alignment = max(0, 15 * (1 - trough_diff_pct / self.trough_tolerance_pct))
        geometry_score += trough_alignment

        # 3. Head-Prominence (0-15)
        if pattern.pattern_type.endswith("TOP"):
            prominence = (head.price - avg_shoulder) / avg_shoulder
        else:
            prominence = (avg_shoulder - head.price) / avg_shoulder

        head_prominence = min(15, 15 * (prominence / self.min_head_prominence))
        geometry_score += head_prominence

        # Context Score (0-20)
        context_score = 10.0  # Default (kein Data verfügbar)
        if data is not None:
            # TODO: Trend-Analyse, Volume-Analyse
            pass

        # Confirmation Score (0-20)
        confirmation_score = 0.0
        if pattern.state == PatternState.CONFIRMED:
            confirmation_score = 20.0
        elif pattern.state == PatternState.FORMING:
            confirmation_score = 5.0  # Bonus für valide Formation

        # Total Score
        total_score = geometry_score + context_score + confirmation_score

        # Scoring Breakdown speichern
        pattern.scoring_breakdown = {
            "geometry": geometry_score,
            "context": context_score,
            "confirmation": confirmation_score,
            "total": total_score
        }

        return min(100.0, total_score)

    def generate_lines(self, pattern: Pattern) -> Dict[str, List[tuple]]:
        """Generiere Neckline für Chart-Overlay.

        Returns:
            {"neckline": [(timestamp1, price1), (timestamp2, price2)]}
        """
        ls, t1, head, t2, rs = pattern.pivots

        # Neckline = Linie durch beide Troughs/Peaks
        neckline = [
            (t1.timestamp, t1.price),
            (t2.timestamp, t2.price)
        ]

        return {"neckline": neckline}
```

**Checklist (Schritt 1.5):**
- [ ] `reversal_patterns.py` mit `HeadAndShouldersDetector` implementiert
- [ ] H&S Top + H&S Bottom Detection funktional
- [ ] Score Calculation (Geometry, Context, Confirmation)
- [ ] Generate Lines (Neckline) für Chart Overlay
- [ ] Tests in `test_reversal_patterns.py` geschrieben
- [ ] Test mit BTCUSDT 1D Daten (mind. 1 H&S Pattern gefunden)

**Tests:** `tests/patterns/test_reversal_patterns.py`
```python
"""Tests für Reversal Patterns (H&S, Double Top/Bottom)."""

import pandas as pd
import pytest
from src.analysis.patterns.reversal_patterns import HeadAndShouldersDetector
from src.analysis.patterns.pivot_engine import Pivot, PivotType, PivotEngine


def test_head_and_shoulders_top_detection():
    """Test: H&S Top wird korrekt erkannt."""
    # Erstelle Mock-Daten mit klarem H&S Top Pattern
    data = pd.DataFrame({
        'open': [100, 102, 101, 105, 104, 110, 108, 106, 105, 103],
        'high': [101, 104, 103, 108, 107, 115, 112, 108, 107, 105],  # Peak @ 115 (Head)
        'low': [99, 101, 99, 103, 102, 108, 104, 103, 102, 101],
        'close': [100, 103, 100, 106, 103, 112, 105, 104, 103, 102]
    }, index=pd.date_range('2024-01-01', periods=10, freq='1D'))

    # Pivots detektieren
    engine = PivotEngine(threshold_pct=2.0, use_atr=False)
    pivots = engine.detect_pivots(data)

    # H&S detektieren
    detector = HeadAndShouldersDetector(shoulder_tolerance_pct=3.0)
    patterns = detector.detect(pivots, data)

    # Assertions
    assert len(patterns) > 0, "Sollte mind. 1 H&S Top Pattern finden"
    hs_pattern = patterns[0]
    assert hs_pattern.pattern_type == "HEAD_AND_SHOULDERS_TOP"
    assert hs_pattern.score > 70  # Mind. 70/100 Score
    assert len(hs_pattern.pivots) == 5  # 5 Pivots (LS-T1-Head-T2-RS)
    assert "neckline" in hs_pattern.lines


def test_head_and_shoulders_scoring():
    """Test: Scoring-System funktioniert korrekt."""
    # Perfektes H&S Pattern sollte hohen Score haben
    # Asymmetrisches Pattern sollte niedrigen Score haben
    pass  # TODO: Implement


def test_shoulder_symmetry_validation():
    """Test: Asymmetrische Shoulders werden abgelehnt."""
    pass  # TODO: Implement
```

---

### ✅ Schritt 1.6: Double Top/Bottom Detector (3-4h)

**Datei:** Erweitere `src/analysis/patterns/reversal_patterns.py`

```python
# Am Ende von reversal_patterns.py hinzufügen:

class DoubleTopBottomDetector(PatternDetector):
    """Double Top/Bottom Pattern Detector."""

    def __init__(
        self,
        peak_tolerance_pct: float = 1.5,
        min_trough_depth_pct: float = 3.0
    ):
        """
        Args:
            peak_tolerance_pct: Toleranz für Peak-Symmetrie (%)
            min_trough_depth_pct: Min. Tiefe des Troughs (%)
        """
        self.peak_tolerance_pct = peak_tolerance_pct
        self.min_trough_depth_pct = min_trough_depth_pct

    def detect(self, pivots: List[Pivot], data: pd.DataFrame = None) -> List[Pattern]:
        """Detektiere Double Top/Bottom Patterns.

        3-Pivot Struktur (Double Top):
        - Peak1 (Pivot HIGH)
        - Trough (Pivot LOW)
        - Peak2 (Pivot HIGH)

        Args:
            pivots: Liste von Pivots
            data: Optional OHLC DataFrame

        Returns:
            Liste erkannter Double Top/Bottom Patterns
        """
        patterns = []

        # Mind. 3 Pivots benötigt
        if len(pivots) < 3:
            return patterns

        # Sliding Window über Pivots (3er Gruppen)
        for i in range(len(pivots) - 2):
            p1, p2, p3 = pivots[i:i+3]

            # Prüfe auf Double Top
            if self._is_double_top(p1, p2, p3):
                pattern = self._create_double_pattern(
                    pivots=[p1, p2, p3],
                    pattern_type="DOUBLE_TOP",
                    direction_bias=DirectionBias.DOWN,
                    data=data
                )
                patterns.append(pattern)
                logger.info(f"Double Top detected: {pattern}")

            # Prüfe auf Double Bottom
            elif self._is_double_bottom(p1, p2, p3):
                pattern = self._create_double_pattern(
                    pivots=[p1, p2, p3],
                    pattern_type="DOUBLE_BOTTOM",
                    direction_bias=DirectionBias.UP,
                    data=data
                )
                patterns.append(pattern)
                logger.info(f"Double Bottom detected: {pattern}")

        return patterns

    def _is_double_top(self, peak1: Pivot, trough: Pivot, peak2: Pivot) -> bool:
        """Prüfe ob 3 Pivots ein Double Top bilden.

        Kriterien:
        - Peak1, Peak2 müssen HIGH sein
        - Trough muss LOW sein
        - Peaks im Toleranzband (±1.5%)
        - Trough signifikant tiefer (mind. 3%)
        """
        # Pivot-Typen prüfen
        if not (peak1.type == PivotType.HIGH and trough.type == PivotType.LOW and
                peak2.type == PivotType.HIGH):
            return False

        # Peaks im Toleranzband
        avg_peak = (peak1.price + peak2.price) / 2
        peak_diff_pct = abs(peak1.price - peak2.price) / avg_peak * 100
        if peak_diff_pct > self.peak_tolerance_pct:
            return False

        # Trough-Tiefe prüfen
        trough_depth_pct = (avg_peak - trough.price) / avg_peak * 100
        if trough_depth_pct < self.min_trough_depth_pct:
            return False

        return True

    def _is_double_bottom(self, bottom1: Pivot, peak: Pivot, bottom2: Pivot) -> bool:
        """Prüfe ob 3 Pivots ein Double Bottom bilden (inverse)."""
        # Pivot-Typen prüfen
        if not (bottom1.type == PivotType.LOW and peak.type == PivotType.HIGH and
                bottom2.type == PivotType.LOW):
            return False

        # Bottoms im Toleranzband
        avg_bottom = (bottom1.price + bottom2.price) / 2
        bottom_diff_pct = abs(bottom1.price - bottom2.price) / avg_bottom * 100
        if bottom_diff_pct > self.peak_tolerance_pct:
            return False

        # Peak-Höhe prüfen
        peak_height_pct = (peak.price - avg_bottom) / avg_bottom * 100
        if peak_height_pct < self.min_trough_depth_pct:
            return False

        return True

    def _create_double_pattern(
        self,
        pivots: List[Pivot],
        pattern_type: str,
        direction_bias: DirectionBias,
        data: Optional[pd.DataFrame]
    ) -> Pattern:
        """Erstelle Pattern-Objekt für Double Top/Bottom."""
        p1, p2, p3 = pivots

        pattern_id = f"{pattern_type}_{p1.index}"
        state = PatternState.FORMING

        # Score berechnen (später)
        score = self.calculate_score(
            Pattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                category="REVERSAL",
                state=state,
                score=0.0,
                direction_bias=direction_bias,
                start_index=p1.index,
                end_index=p3.index,
                pivots=pivots,
                lines={},
                scoring_breakdown={}
            ),
            data=data
        )

        # Geometrie-Linien
        lines = self.generate_lines(
            Pattern(
                pattern_id=pattern_id,
                pattern_type=pattern_type,
                category="REVERSAL",
                state=state,
                score=score,
                direction_bias=direction_bias,
                start_index=p1.index,
                end_index=p3.index,
                pivots=pivots,
                lines={},
                scoring_breakdown={}
            )
        )

        return Pattern(
            pattern_id=pattern_id,
            pattern_type=pattern_type,
            category="REVERSAL",
            state=state,
            score=score,
            direction_bias=direction_bias,
            start_index=p1.index,
            end_index=p3.index,
            pivots=pivots,
            lines=lines,
            scoring_breakdown={}
        )

    def calculate_score(self, pattern: Pattern, data: Optional[pd.DataFrame] = None) -> float:
        """Berechne Double Top/Bottom Score (0-100)."""
        p1, p2, p3 = pattern.pivots

        # Geometry Score (0-60)
        geometry_score = 0.0

        # 1. Peak-Symmetrie (0-30)
        avg_peak = (p1.price + p3.price) / 2
        peak_diff_pct = abs(p1.price - p3.price) / avg_peak * 100
        peak_symmetry = max(0, 30 * (1 - peak_diff_pct / self.peak_tolerance_pct))
        geometry_score += peak_symmetry

        # 2. Trough-Tiefe (0-15)
        if pattern.pattern_type == "DOUBLE_TOP":
            trough_depth_pct = (avg_peak - p2.price) / avg_peak * 100
        else:  # DOUBLE_BOTTOM
            trough_depth_pct = (p2.price - avg_peak) / avg_peak * 100

        trough_depth = min(15, 15 * (trough_depth_pct / self.min_trough_depth_pct))
        geometry_score += trough_depth

        # 3. Zeitliche Symmetrie (0-15)
        time_dist1 = p2.index - p1.index
        time_dist2 = p3.index - p2.index
        time_diff_pct = abs(time_dist1 - time_dist2) / max(time_dist1, time_dist2) * 100
        time_symmetry = max(0, 15 * (1 - time_diff_pct / 50))  # 50% Toleranz
        geometry_score += time_symmetry

        # Context Score (0-20)
        context_score = 10.0  # Default

        # Confirmation Score (0-20)
        confirmation_score = 5.0 if pattern.state == PatternState.FORMING else 20.0

        # Total Score
        total_score = geometry_score + context_score + confirmation_score

        pattern.scoring_breakdown = {
            "geometry": geometry_score,
            "context": context_score,
            "confirmation": confirmation_score,
            "total": total_score
        }

        return min(100.0, total_score)

    def generate_lines(self, pattern: Pattern) -> Dict[str, List[tuple]]:
        """Generiere Support/Resistance Linie für Chart-Overlay."""
        p1, p2, p3 = pattern.pivots

        # Support/Resistance = Trough/Peak Level (horizontal)
        sr_level = p2.price
        sr_line = [
            (p1.timestamp, sr_level),
            (p3.timestamp, sr_level)
        ]

        return {"support_resistance": sr_line}
```

**Checklist (Schritt 1.6):**
- [ ] `DoubleTopBottomDetector` in `reversal_patterns.py` hinzugefügt
- [ ] Double Top + Double Bottom Detection funktional
- [ ] Score Calculation (Peak-Symmetrie, Trough-Tiefe, Zeit-Symmetrie)
- [ ] Generate Lines (Support/Resistance horizontal)
- [ ] Tests in `test_reversal_patterns.py` erweitert
- [ ] Test mit BTCUSDT 1D Daten (mind. 1 Double Top/Bottom gefunden)

---

### ✅ Schritt 1.7: Entry Analyzer UI Tab erstellen (4-5h)

**Datei:** Modifiziere `src/ui/dialogs/entry_analyzer_popup.py`

**Schritt 1.7.1: Neuen Tab hinzufügen (Zeile ~250)**

```python
# In EntryAnalyzerPopup.__init__() nach dem Validation Tab:

# Nach Zeile ~250 (nach self.validation_tab = ...)
self.pattern_tab = self._create_pattern_recognition_tab()
self.tabs.addTab(self.pattern_tab, "📊 Patterns")
```

**Schritt 1.7.2: Tab-Layout implementieren**

```python
# Neue Methode in EntryAnalyzerPopup Klasse:

def _create_pattern_recognition_tab(self) -> QWidget:
    """Pattern Recognition Tab - 2-Spalten Layout.

    Layout:
    - Links (40%): Pattern-Kategorien Tree mit Count-Badges
    - Rechts (60%): Erkannte Patterns Table + Actions
    """
    tab = QWidget()
    main_layout = QHBoxLayout(tab)

    # ===== Linke Spalte: Pattern Categories =====
    categories_group = QGroupBox("Pattern Categories")
    categories_layout = QVBoxLayout(categories_group)

    # Pattern Tree Widget
    from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
    self.pattern_tree = QTreeWidget()
    self.pattern_tree.setHeaderLabel("Categories (Count)")
    self.pattern_tree.setMaximumWidth(300)

    # Tree Items
    reversal_item = QTreeWidgetItem(["↩️ Reversal Patterns (0)"])
    reversal_item.addChild(QTreeWidgetItem(["Head & Shoulders (0)"]))
    reversal_item.addChild(QTreeWidgetItem(["Double Top/Bottom (0)"]))
    reversal_item.addChild(QTreeWidgetItem(["Triple Top/Bottom (0)"]))

    continuation_item = QTreeWidgetItem(["↪️ Continuation Patterns (0)"]))
    continuation_item.addChild(QTreeWidgetItem(["Triangles (0)"]))
    continuation_item.addChild(QTreeWidgetItem(["Flags/Pennants (0)"]))

    smart_money_item = QTreeWidgetItem(["💰 Smart Money (0)"]))
    smart_money_item.addChild(QTreeWidgetItem(["Order Blocks (0)"]))
    smart_money_item.addChild(QTreeWidgetItem(["Fair Value Gaps (0)"]))
    smart_money_item.addChild(QTreeWidgetItem(["Market Structure (0)"]))

    trend_following_item = QTreeWidgetItem(["📈 Trend Following (0)"]))
    trend_following_item.addChild(QTreeWidgetItem(["Channels (0)"]))
    trend_following_item.addChild(QTreeWidgetItem(["Breakouts (0)"]))

    self.pattern_tree.addTopLevelItem(reversal_item)
    self.pattern_tree.addTopLevelItem(continuation_item)
    self.pattern_tree.addTopLevelItem(smart_money_item)
    self.pattern_tree.addTopLevelItem(trend_following_item)
    self.pattern_tree.expandAll()

    categories_layout.addWidget(self.pattern_tree)

    # Detection Settings (collapsible)
    settings_group = QGroupBox("⚙️ Detection Settings")
    settings_group.setCheckable(True)
    settings_group.setChecked(False)  # Initially collapsed
    settings_layout = QFormLayout(settings_group)

    self.zigzag_threshold_spin = QDoubleSpinBox()
    self.zigzag_threshold_spin.setRange(0.5, 10.0)
    self.zigzag_threshold_spin.setValue(2.0)
    self.zigzag_threshold_spin.setSuffix(" %")
    settings_layout.addRow("ZigZag Threshold:", self.zigzag_threshold_spin)

    self.use_atr_checkbox = QCheckBox("Use ATR-based detection")
    self.use_atr_checkbox.setChecked(True)
    settings_layout.addRow("", self.use_atr_checkbox)

    categories_layout.addWidget(settings_group)

    # Spacer
    categories_layout.addStretch()

    # ===== Rechte Spalte: Detected Patterns =====
    patterns_group = QGroupBox("Detected Patterns")
    patterns_layout = QVBoxLayout(patterns_group)

    # Patterns Table
    self.patterns_table = QTableWidget()
    self.patterns_table.setColumnCount(6)
    self.patterns_table.setHorizontalHeaderLabels([
        "Type", "State", "Score", "Direction", "Start Time", "Actions"
    ])
    self.patterns_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    self.patterns_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    self.patterns_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    patterns_layout.addWidget(self.patterns_table)

    # Action Buttons
    actions_layout = QHBoxLayout()

    self.detect_patterns_btn = QPushButton("🔍 Detect Patterns")
    self.detect_patterns_btn.setStyleSheet("background-color: #26a69a; color: white; font-weight: bold;")
    self.detect_patterns_btn.clicked.connect(self._on_detect_patterns_clicked)

    self.draw_patterns_btn = QPushButton("📊 Draw on Chart")
    self.draw_patterns_btn.setEnabled(False)  # Initially disabled
    self.draw_patterns_btn.clicked.connect(self._on_draw_patterns_clicked)

    self.clear_patterns_btn = QPushButton("🗑️ Clear Patterns")
    self.clear_patterns_btn.clicked.connect(self._on_clear_patterns_clicked)

    self.export_patterns_btn = QPushButton("📄 Export JSON")
    self.export_patterns_btn.setEnabled(False)
    self.export_patterns_btn.clicked.connect(self._on_export_patterns_clicked)

    actions_layout.addWidget(self.detect_patterns_btn)
    actions_layout.addWidget(self.draw_patterns_btn)
    actions_layout.addWidget(self.clear_patterns_btn)
    actions_layout.addWidget(self.export_patterns_btn)
    actions_layout.addStretch()

    patterns_layout.addLayout(actions_layout)

    # ===== Splitter für resizable Spalten =====
    splitter = QSplitter(Qt.Orientation.Horizontal)
    splitter.addWidget(categories_group)
    splitter.addWidget(patterns_group)
    splitter.setStretchFactor(0, 2)  # 40%
    splitter.setStretchFactor(1, 3)  # 60%

    main_layout.addWidget(splitter)

    return tab
```

**Schritt 1.7.3: Event Handler implementieren**

```python
# Neue Methoden in EntryAnalyzerPopup Klasse:

def _on_detect_patterns_clicked(self):
    """Detect Patterns Button Handler."""
    try:
        # Get chart data
        if not hasattr(self.parent(), 'data') or self.parent().data is None:
            QMessageBox.warning(self, "No Data", "Please load chart data first.")
            return

        data = self.parent().data

        logger.info(f"Starting pattern detection on {len(data)} bars...")

        # Import pattern modules
        from src.analysis.patterns.pivot_engine import PivotEngine
        from src.analysis.patterns.reversal_patterns import (
            HeadAndShouldersDetector,
            DoubleTopBottomDetector
        )

        # 1. Detect Pivots
        threshold = self.zigzag_threshold_spin.value()
        use_atr = self.use_atr_checkbox.isChecked()

        pivot_engine = PivotEngine(
            threshold_pct=threshold,
            use_atr=use_atr,
            atr_period=14,
            atr_multiplier=1.5
        )
        pivots = pivot_engine.detect_pivots(data)

        logger.info(f"Detected {len(pivots)} pivots")

        if len(pivots) < 3:
            QMessageBox.information(
                self,
                "No Pivots Found",
                f"Only {len(pivots)} pivots detected. Try adjusting ZigZag threshold."
            )
            return

        # 2. Detect Patterns
        all_patterns = []

        # Head & Shoulders
        hs_detector = HeadAndShouldersDetector()
        hs_patterns = hs_detector.detect(pivots, data)
        all_patterns.extend(hs_patterns)
        logger.info(f"Detected {len(hs_patterns)} H&S patterns")

        # Double Top/Bottom
        double_detector = DoubleTopBottomDetector()
        double_patterns = double_detector.detect(pivots, data)
        all_patterns.extend(double_patterns)
        logger.info(f"Detected {len(double_patterns)} Double Top/Bottom patterns")

        # 3. Update UI
        self._update_patterns_table(all_patterns)
        self._update_pattern_tree_counts(all_patterns)

        # Enable buttons
        self.draw_patterns_btn.setEnabled(len(all_patterns) > 0)
        self.export_patterns_btn.setEnabled(len(all_patterns) > 0)

        # Store patterns for later use
        self.detected_patterns = all_patterns

        QMessageBox.information(
            self,
            "Detection Complete",
            f"Detected {len(all_patterns)} patterns:\n"
            f"- Head & Shoulders: {len(hs_patterns)}\n"
            f"- Double Top/Bottom: {len(double_patterns)}"
        )

    except Exception as e:
        logger.exception("Pattern detection failed")
        QMessageBox.critical(self, "Error", f"Pattern detection failed: {str(e)}")


def _update_patterns_table(self, patterns: List):
    """Update patterns table with detected patterns."""
    self.patterns_table.setRowCount(0)

    for pattern in patterns:
        row = self.patterns_table.rowCount()
        self.patterns_table.insertRow(row)

        # Type
        type_item = QTableWidgetItem(pattern.pattern_type.replace("_", " ").title())
        self.patterns_table.setItem(row, 0, type_item)

        # State (with emoji)
        state_emoji = {
            "FORMING": "🔴",
            "CONFIRMED": "🟢",
            "FAILED": "⚫",
            "INVALIDATED": "❌"
        }
        state_text = f"{state_emoji.get(pattern.state.value, '')} {pattern.state.value}"
        state_item = QTableWidgetItem(state_text)
        self.patterns_table.setItem(row, 1, state_item)

        # Score (with progress bar effect)
        score_item = QTableWidgetItem(f"{pattern.score:.1f}/100")
        if pattern.score >= 80:
            score_item.setBackground(QBrush(QColor(38, 166, 154, 50)))  # Green
        elif pattern.score >= 60:
            score_item.setBackground(QBrush(QColor(255, 167, 38, 50)))  # Orange
        else:
            score_item.setBackground(QBrush(QColor(239, 83, 80, 50)))  # Red
        self.patterns_table.setItem(row, 2, score_item)

        # Direction
        direction_emoji = {
            "UP": "↗️",
            "DOWN": "↘️",
            "NONE": "↔️"
        }
        direction_item = QTableWidgetItem(
            f"{direction_emoji.get(pattern.direction_bias.value, '')} {pattern.direction_bias.value}"
        )
        self.patterns_table.setItem(row, 3, direction_item)

        # Start Time
        start_time = pattern.pivots[0].timestamp.strftime("%Y-%m-%d %H:%M")
        time_item = QTableWidgetItem(start_time)
        self.patterns_table.setItem(row, 4, time_item)

        # Actions (Details Button)
        details_btn = QPushButton("Details")
        details_btn.clicked.connect(lambda checked, p=pattern: self._show_pattern_details(p))
        self.patterns_table.setCellWidget(row, 5, details_btn)


def _update_pattern_tree_counts(self, patterns: List):
    """Update pattern tree counts."""
    # Count patterns by type
    counts = {
        "hs": 0,
        "double": 0,
        "triple": 0,
        "triangles": 0,
        "flags": 0,
        "order_blocks": 0,
        "fvg": 0,
        "mss": 0,
        "channels": 0,
        "breakouts": 0
    }

    for pattern in patterns:
        if "HEAD_AND_SHOULDERS" in pattern.pattern_type:
            counts["hs"] += 1
        elif "DOUBLE" in pattern.pattern_type:
            counts["double"] += 1
        # ... weitere Patterns

    # Update Tree
    reversal_item = self.pattern_tree.topLevelItem(0)
    reversal_item.setText(0, f"↩️ Reversal Patterns ({counts['hs'] + counts['double'] + counts['triple']})")
    reversal_item.child(0).setText(0, f"Head & Shoulders ({counts['hs']})")
    reversal_item.child(1).setText(0, f"Double Top/Bottom ({counts['double']})")
    reversal_item.child(2).setText(0, f"Triple Top/Bottom ({counts['triple']})")

    # ... weitere Updates


def _show_pattern_details(self, pattern):
    """Show detailed pattern information (Optional: Open Popup)."""
    # Option 1: Simple Message Box
    details = (
        f"Pattern: {pattern.pattern_type}\n"
        f"Score: {pattern.score:.1f}/100\n"
        f"State: {pattern.state.value}\n"
        f"Direction: {pattern.direction_bias.value}\n\n"
        f"Scoring Breakdown:\n"
    )
    for key, value in pattern.scoring_breakdown.items():
        details += f"- {key.capitalize()}: {value:.1f}\n"

    QMessageBox.information(self, "Pattern Details", details)

    # Option 2: Open Pattern Details Dialog (TODO: MVP 2)
    # from src.ui.dialogs.pattern_details_dialog import PatternDetailsDialog
    # dialog = PatternDetailsDialog(pattern, parent=self)
    # dialog.exec()


def _on_draw_patterns_clicked(self):
    """Draw patterns on chart."""
    if not hasattr(self, 'detected_patterns'):
        return

    try:
        # Get chart window
        chart_window = self.parent()

        # Draw patterns via mixin
        if hasattr(chart_window, 'draw_pattern_overlays'):
            chart_window.draw_pattern_overlays(self.detected_patterns)
            QMessageBox.information(self, "Success", f"Drew {len(self.detected_patterns)} patterns on chart")
        else:
            QMessageBox.warning(self, "Not Implemented", "Chart overlay not yet available")

    except Exception as e:
        logger.exception("Drawing patterns failed")
        QMessageBox.critical(self, "Error", f"Failed to draw patterns: {str(e)}")


def _on_clear_patterns_clicked(self):
    """Clear patterns from table and chart."""
    self.patterns_table.setRowCount(0)
    self.detected_patterns = []
    self.draw_patterns_btn.setEnabled(False)
    self.export_patterns_btn.setEnabled(False)

    # Clear pattern tree counts
    self._update_pattern_tree_counts([])

    # Clear from chart
    chart_window = self.parent()
    if hasattr(chart_window, 'clear_pattern_overlays'):
        chart_window.clear_pattern_overlays()


def _on_export_patterns_clicked(self):
    """Export patterns to JSON."""
    if not hasattr(self, 'detected_patterns') or not self.detected_patterns:
        return

    try:
        # File dialog
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Patterns",
            f"patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )

        if not filename:
            return

        # Export (TODO: Use PatternExporter from MVP 3)
        import json
        patterns_data = []
        for p in self.detected_patterns:
            patterns_data.append({
                "pattern_id": p.pattern_id,
                "pattern_type": p.pattern_type,
                "score": p.score,
                "state": p.state.value,
                "direction_bias": p.direction_bias.value,
                "start_index": p.start_index,
                "end_index": p.end_index,
                "scoring_breakdown": p.scoring_breakdown
            })

        with open(filename, 'w') as f:
            json.dump({
                "export_metadata": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "pattern_count": len(patterns_data)
                },
                "patterns": patterns_data
            }, f, indent=2)

        QMessageBox.information(self, "Success", f"Exported {len(patterns_data)} patterns to {filename}")

    except Exception as e:
        logger.exception("Export failed")
        QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
```

**Checklist (Schritt 1.7):**
- [ ] Pattern Recognition Tab in Entry Analyzer hinzugefügt (Zeile ~250)
- [ ] 2-Spalten Layout implementiert (Categories Tree + Patterns Table)
- [ ] Detection Settings (ZigZag Threshold, ATR Toggle)
- [ ] "Detect Patterns" Button funktional
- [ ] Patterns Table zeigt erkannte Patterns (Type, State, Score, Direction)
- [ ] "Details" Button für jedes Pattern
- [ ] "Draw on Chart", "Clear", "Export" Buttons vorhanden (Funktionalität in Schritt 1.8/MVP 3)
- [ ] Pattern Tree Counts werden aktualisiert
- [ ] Test: Entry Analyzer öffnen → Pattern Tab → Patterns detektieren

---

### ✅ Schritt 1.8: Chart Overlay Integration (3-4h)

**Ziel:** Patterns im Chart visualisieren (Linien für Necklines/Trendlines/Support/Resistance, Marker für Pivots, interaktive Tooltips).

**Architektur:** Mixin-Pattern für saubere Trennung der Chart-Overlay-Funktionalität.

---

#### 📄 Datei: `src/ui/widgets/chart_mixins/pattern_overlay_mixin.py`

```python
"""Pattern Overlay Mixin - Visualize detected patterns on chart.

This mixin adds pattern visualization capabilities to ChartWindow:
- Draw pattern lines (necklines, trendlines, support/resistance)
- Add pivot markers
- Interactive tooltips on hover
- Clear overlays
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, List, Dict, Any, Optional
from datetime import datetime

if TYPE_CHECKING:
    from src.analysis.patterns.base_detector import Pattern, Pivot

logger = logging.getLogger(__name__)


class PatternOverlayMixin:
    """Mixin for ChartWindow to add pattern visualization.

    This mixin provides methods to:
    - Draw pattern overlays (lines, markers, labels)
    - Clear pattern overlays
    - Handle pattern hover events
    - Show/hide pattern details
    """

    def __init__(self):
        """Initialize pattern overlay state."""
        self._pattern_overlays = []
        self._pattern_markers = []
        self._pattern_labels = []

    def draw_pattern_overlays(self, patterns: List['Pattern']) -> None:
        """Draw all patterns on chart.

        Args:
            patterns: List of Pattern objects to visualize
        """
        try:
            # Clear existing overlays
            self.clear_pattern_overlays()

            logger.info(f"Drawing {len(patterns)} patterns on chart")

            for pattern in patterns:
                self._draw_single_pattern(pattern)

            logger.info("Pattern overlays drawn successfully")

        except Exception as e:
            logger.exception(f"Failed to draw pattern overlays: {e}")

    def _draw_single_pattern(self, pattern: 'Pattern') -> None:
        """Draw a single pattern's visualization elements.

        Args:
            pattern: Pattern object to visualize
        """
        # 1. Draw pattern lines (necklines, trendlines, etc.)
        if pattern.lines:
            self._draw_pattern_lines(pattern)

        # 2. Draw pivot markers
        if pattern.pivots:
            self._draw_pivot_markers(pattern)

        # 3. Draw pattern label
        self._draw_pattern_label(pattern)

    def _draw_pattern_lines(self, pattern: 'Pattern') -> None:
        """Draw pattern lines (necklines, trendlines, support/resistance).

        Args:
            pattern: Pattern object with lines dict
        """
        color = self._get_pattern_color(pattern)

        for line_type, points in pattern.lines.items():
            if len(points) < 2:
                continue

            # Convert points to JavaScript format
            js_points = json.dumps([
                {"time": int(p[0].timestamp()), "price": float(p[1])}
                for p in points
            ])

            # Line style based on type
            line_style = self._get_line_style(line_type)
            width = 2 if line_type == "neckline" else 1

            # Draw line via JavaScript API
            js_code = f"""
            window.chartAPI.drawLine(
                {js_points},
                '{color}',
                {width},
                '{line_style}',
                '{pattern.pattern_id}_{line_type}'
            );
            """
            self._execute_js(js_code)

            self._pattern_overlays.append({
                "id": f"{pattern.pattern_id}_{line_type}",
                "type": "line",
                "pattern_id": pattern.pattern_id
            })

    def _draw_pivot_markers(self, pattern: 'Pattern') -> None:
        """Draw markers for pivot points.

        Args:
            pattern: Pattern object with pivots list
        """
        color = self._get_pattern_color(pattern)

        for pivot in pattern.pivots:
            # Marker shape based on pivot type
            shape = "circle" if pivot.pivot_type == "HIGH" else "circle"
            marker_color = color

            # Draw marker via JavaScript API
            js_code = f"""
            window.chartAPI.addMarker({{
                time: {int(pivot.timestamp.timestamp())},
                price: {float(pivot.price)},
                shape: '{shape}',
                color: '{marker_color}',
                text: '{pivot.pivot_type[0]}',
                id: '{pattern.pattern_id}_pivot_{pivot.index}'
            }});
            """
            self._execute_js(js_code)

            self._pattern_markers.append({
                "id": f"{pattern.pattern_id}_pivot_{pivot.index}",
                "type": "marker",
                "pattern_id": pattern.pattern_id
            })

    def _draw_pattern_label(self, pattern: 'Pattern') -> None:
        """Draw pattern label with name and score.

        Args:
            pattern: Pattern object
        """
        # Position label at pattern start
        start_pivot = pattern.pivots[0]
        label_time = int(start_pivot.timestamp.timestamp())
        label_price = float(start_pivot.price)

        # Label text
        pattern_name = pattern.pattern_type.replace("_", " ").title()
        score_color = self._get_score_color(pattern.score)
        label_text = f"{pattern_name} ({pattern.score:.0f})"

        # State emoji
        state_emoji = {
            "FORMING": "🔴",
            "CONFIRMED": "🟢",
            "FAILED": "⚫",
            "INVALIDATED": "❌"
        }
        emoji = state_emoji.get(pattern.state.value, "")

        # Draw label via JavaScript API
        js_code = f"""
        window.chartAPI.addLabel({{
            time: {label_time},
            price: {label_price},
            text: '{emoji} {label_text}',
            backgroundColor: '{score_color}',
            textColor: '#FFFFFF',
            id: '{pattern.pattern_id}_label'
        }});
        """
        self._execute_js(js_code)

        self._pattern_labels.append({
            "id": f"{pattern.pattern_id}_label",
            "type": "label",
            "pattern_id": pattern.pattern_id
        })

    def clear_pattern_overlays(self) -> None:
        """Remove all pattern overlays from chart."""
        try:
            # Clear lines
            for overlay in self._pattern_overlays:
                js_code = f"window.chartAPI.removeLine('{overlay['id']}');"
                self._execute_js(js_code)

            # Clear markers
            for marker in self._pattern_markers:
                js_code = f"window.chartAPI.removeMarker('{marker['id']}');"
                self._execute_js(js_code)

            # Clear labels
            for label in self._pattern_labels:
                js_code = f"window.chartAPI.removeLabel('{label['id']}');"
                self._execute_js(js_code)

            # Reset state
            self._pattern_overlays.clear()
            self._pattern_markers.clear()
            self._pattern_labels.clear()

            logger.info("Pattern overlays cleared")

        except Exception as e:
            logger.exception(f"Failed to clear pattern overlays: {e}")

    def _get_pattern_color(self, pattern: 'Pattern') -> str:
        """Get color for pattern based on direction bias.

        Args:
            pattern: Pattern object

        Returns:
            Hex color string
        """
        if pattern.direction_bias.value == "UP":
            return "#26a69a"  # Green (bullish)
        elif pattern.direction_bias.value == "DOWN":
            return "#ef5350"  # Red (bearish)
        else:
            return "#ffa726"  # Orange (neutral)

    def _get_score_color(self, score: float) -> str:
        """Get background color based on pattern score.

        Args:
            score: Pattern score (0-100)

        Returns:
            Hex color string
        """
        if score >= 80:
            return "#2e7d32"  # Dark green
        elif score >= 60:
            return "#558b2f"  # Green
        elif score >= 40:
            return "#f57c00"  # Orange
        else:
            return "#c62828"  # Red

    def _get_line_style(self, line_type: str) -> str:
        """Get line style for pattern line type.

        Args:
            line_type: Type of line (neckline, trendline, support, resistance)

        Returns:
            Line style string (solid, dashed, dotted)
        """
        line_styles = {
            "neckline": "solid",
            "trendline": "dashed",
            "support": "dotted",
            "resistance": "dotted"
        }
        return line_styles.get(line_type, "solid")

    def get_pattern_at_position(self, timestamp: datetime, price: float, tolerance: float = 0.01) -> Optional['Pattern']:
        """Find pattern near given chart position (for hover/click events).

        Args:
            timestamp: Chart timestamp
            price: Chart price level
            tolerance: Price tolerance for hit detection (as percentage)

        Returns:
            Pattern object if found, else None
        """
        # This method would be used for interactive hover tooltips
        # Implementation depends on how patterns are stored in ChartWindow
        # For now, return None (can be implemented when needed)
        return None
```

---

#### 📄 Integration: ChartWindow Modification

**Datei:** `src/ui/widgets/chart_window_setup.py` (oder `chart_window.py`)

**Add Mixin to ChartWindow class:**

```python
# At top of file
from src.ui.widgets.chart_mixins.pattern_overlay_mixin import PatternOverlayMixin

# Modify class definition
class ChartWindow(
    QMainWindow,
    # ... existing mixins ...
    PatternOverlayMixin  # Add this
):
    def __init__(self):
        super().__init__()
        # ... existing init code ...

        # Initialize pattern overlay mixin
        PatternOverlayMixin.__init__(self)
```

---

#### 📄 JavaScript API Extensions

**Datei:** `src/ui/templates/chart.html` (or wherever TradingView Lightweight Charts is initialized)

**Add these functions to `window.chartAPI`:**

```javascript
// Pattern Overlay API Extensions
window.chartAPI = {
    // ... existing methods ...

    /**
     * Draw a line on the chart (necklines, trendlines, etc.)
     * @param {Array} points - Array of {time, price} objects
     * @param {string} color - Hex color
     * @param {number} width - Line width
     * @param {string} style - 'solid', 'dashed', 'dotted'
     * @param {string} id - Unique line identifier
     */
    drawLine: function(points, color, width, style, id) {
        if (points.length < 2) return;

        // Create line series
        const lineSeries = chart.addLineSeries({
            color: color,
            lineWidth: width,
            lineStyle: this._getLineStyle(style),
            crosshairMarkerVisible: false,
            lastValueVisible: false,
            priceLineVisible: false
        });

        lineSeries.setData(points);

        // Store reference
        this._patternLines = this._patternLines || {};
        this._patternLines[id] = lineSeries;
    },

    /**
     * Remove a line from the chart
     * @param {string} id - Line identifier
     */
    removeLine: function(id) {
        if (this._patternLines && this._patternLines[id]) {
            chart.removeSeries(this._patternLines[id]);
            delete this._patternLines[id];
        }
    },

    /**
     * Add a marker (pivot point, breakout point, etc.)
     * @param {Object} marker - {time, price, shape, color, text, id}
     */
    addMarker: function(marker) {
        const candleSeries = this._getCandleSeries();
        if (!candleSeries) return;

        const markerData = {
            time: marker.time,
            position: marker.price > candleSeries.data[candleSeries.data.length - 1].close ? 'aboveBar' : 'belowBar',
            color: marker.color,
            shape: marker.shape || 'circle',
            text: marker.text || '',
            size: 1
        };

        // Store marker reference
        this._patternMarkers = this._patternMarkers || {};
        this._patternMarkers[marker.id] = markerData;

        // Update series markers
        this._updateMarkers();
    },

    /**
     * Remove a marker from the chart
     * @param {string} id - Marker identifier
     */
    removeMarker: function(id) {
        if (this._patternMarkers && this._patternMarkers[id]) {
            delete this._patternMarkers[id];
            this._updateMarkers();
        }
    },

    /**
     * Add a text label on the chart
     * @param {Object} label - {time, price, text, backgroundColor, textColor, id}
     */
    addLabel: function(label) {
        // Create price line with label
        const candleSeries = this._getCandleSeries();
        if (!candleSeries) return;

        const priceLine = {
            price: label.price,
            color: label.backgroundColor,
            lineWidth: 0,
            lineStyle: 2, // Hidden
            axisLabelVisible: false,
            title: label.text
        };

        const priceLineId = candleSeries.createPriceLine(priceLine);

        // Store reference
        this._patternLabels = this._patternLabels || {};
        this._patternLabels[label.id] = { series: candleSeries, priceLineId: priceLineId };
    },

    /**
     * Remove a label from the chart
     * @param {string} id - Label identifier
     */
    removeLabel: function(id) {
        if (this._patternLabels && this._patternLabels[id]) {
            const labelData = this._patternLabels[id];
            labelData.series.removePriceLine(labelData.priceLineId);
            delete this._patternLabels[id];
        }
    },

    // Helper methods
    _getLineStyle: function(style) {
        const styles = {
            'solid': 0,
            'dashed': 1,
            'dotted': 2,
            'large-dashed': 3
        };
        return styles[style] || 0;
    },

    _getCandleSeries: function() {
        // Return main candlestick series (implementation depends on your setup)
        return this._candleSeries || null;
    },

    _updateMarkers: function() {
        const candleSeries = this._getCandleSeries();
        if (!candleSeries) return;

        const allMarkers = Object.values(this._patternMarkers || {});
        candleSeries.setMarkers(allMarkers);
    }
};
```

---

#### 📄 Entry Analyzer: "Draw on Chart" Button Handler

**Datei:** `src/ui/dialogs/entry_analyzer_popup.py`

**Add handler for "Draw on Chart" button:**

```python
def _on_draw_patterns_clicked(self):
    """Draw detected patterns on chart."""
    if not hasattr(self, 'detected_patterns') or not self.detected_patterns:
        QMessageBox.warning(self, "No Patterns", "Please detect patterns first.")
        return

    try:
        # Get parent ChartWindow
        chart_window = self.parent()

        if not hasattr(chart_window, 'draw_pattern_overlays'):
            QMessageBox.critical(
                self,
                "Error",
                "Chart window does not support pattern overlays. "
                "Please ensure PatternOverlayMixin is added to ChartWindow."
            )
            return

        # Draw patterns on chart
        chart_window.draw_pattern_overlays(self.detected_patterns)

        QMessageBox.information(
            self,
            "Success",
            f"Drew {len(self.detected_patterns)} patterns on chart"
        )

    except Exception as e:
        logger.exception("Failed to draw patterns on chart")
        QMessageBox.critical(self, "Error", f"Failed to draw patterns: {str(e)}")


def _on_clear_patterns_clicked(self):
    """Clear pattern overlays from chart."""
    try:
        # Get parent ChartWindow
        chart_window = self.parent()

        if hasattr(chart_window, 'clear_pattern_overlays'):
            chart_window.clear_pattern_overlays()
            QMessageBox.information(self, "Success", "Pattern overlays cleared")

    except Exception as e:
        logger.exception("Failed to clear patterns")
        QMessageBox.critical(self, "Error", f"Failed to clear patterns: {str(e)}")
```

---

#### 📄 Tests: `tests/ui/test_pattern_overlay_mixin.py`

```python
"""Tests for PatternOverlayMixin."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from src.ui.widgets.chart_mixins.pattern_overlay_mixin import PatternOverlayMixin
from src.analysis.patterns.base_detector import Pattern, Pivot, PatternState, DirectionBias, PivotType


@pytest.fixture
def overlay_mixin():
    """Create PatternOverlayMixin instance with mock _execute_js."""
    mixin = PatternOverlayMixin()
    mixin._execute_js = Mock()
    return mixin


@pytest.fixture
def sample_pattern():
    """Create sample Head & Shoulders pattern for testing."""
    pivots = [
        Pivot(0, PivotType.HIGH, 100.0, datetime(2024, 1, 1, tzinfo=timezone.utc)),
        Pivot(1, PivotType.LOW, 95.0, datetime(2024, 1, 2, tzinfo=timezone.utc)),
        Pivot(2, PivotType.HIGH, 105.0, datetime(2024, 1, 3, tzinfo=timezone.utc)),
        Pivot(3, PivotType.LOW, 96.0, datetime(2024, 1, 4, tzinfo=timezone.utc)),
        Pivot(4, PivotType.HIGH, 101.0, datetime(2024, 1, 5, tzinfo=timezone.utc))
    ]

    lines = {
        "neckline": [
            (datetime(2024, 1, 2, tzinfo=timezone.utc), 95.0),
            (datetime(2024, 1, 4, tzinfo=timezone.utc), 96.0)
        ]
    }

    return Pattern(
        pattern_id="hs_1",
        pattern_type="head_and_shoulders_top",
        category="REVERSAL",
        state=PatternState.CONFIRMED,
        score=85.0,
        direction_bias=DirectionBias.DOWN,
        start_index=0,
        end_index=4,
        pivots=pivots,
        lines=lines,
        scoring_breakdown={"geometry": 55, "context": 15, "confirmation": 15}
    )


def test_draw_pattern_overlays_success(overlay_mixin, sample_pattern):
    """Test successful pattern overlay drawing."""
    patterns = [sample_pattern]

    overlay_mixin.draw_pattern_overlays(patterns)

    # Verify JavaScript was called
    assert overlay_mixin._execute_js.call_count > 0

    # Verify overlays were stored
    assert len(overlay_mixin._pattern_overlays) > 0
    assert len(overlay_mixin._pattern_markers) > 0
    assert len(overlay_mixin._pattern_labels) > 0


def test_clear_pattern_overlays(overlay_mixin, sample_pattern):
    """Test clearing pattern overlays."""
    patterns = [sample_pattern]

    # Draw patterns first
    overlay_mixin.draw_pattern_overlays(patterns)
    assert len(overlay_mixin._pattern_overlays) > 0

    # Clear overlays
    overlay_mixin.clear_pattern_overlays()

    # Verify all overlays cleared
    assert len(overlay_mixin._pattern_overlays) == 0
    assert len(overlay_mixin._pattern_markers) == 0
    assert len(overlay_mixin._pattern_labels) == 0


def test_get_pattern_color_bullish(overlay_mixin, sample_pattern):
    """Test pattern color for bullish pattern."""
    sample_pattern.direction_bias = DirectionBias.UP

    color = overlay_mixin._get_pattern_color(sample_pattern)

    assert color == "#26a69a"  # Green


def test_get_pattern_color_bearish(overlay_mixin, sample_pattern):
    """Test pattern color for bearish pattern."""
    sample_pattern.direction_bias = DirectionBias.DOWN

    color = overlay_mixin._get_pattern_color(sample_pattern)

    assert color == "#ef5350"  # Red


def test_get_score_color_high_score(overlay_mixin):
    """Test score color for high-quality pattern."""
    color = overlay_mixin._get_score_color(85.0)
    assert color == "#2e7d32"  # Dark green


def test_get_score_color_low_score(overlay_mixin):
    """Test score color for low-quality pattern."""
    color = overlay_mixin._get_score_color(30.0)
    assert color == "#c62828"  # Red


def test_get_line_style(overlay_mixin):
    """Test line style mapping."""
    assert overlay_mixin._get_line_style("neckline") == "solid"
    assert overlay_mixin._get_line_style("trendline") == "dashed"
    assert overlay_mixin._get_line_style("support") == "dotted"
    assert overlay_mixin._get_line_style("unknown") == "solid"  # Default
```

---

**Checklist (Schritt 1.8):**
- [ ] `PatternOverlayMixin` implementiert (`pattern_overlay_mixin.py`)
- [ ] Mixin zu `ChartWindow` hinzugefügt
- [ ] JavaScript API Extensions hinzugefügt (`drawLine`, `addMarker`, `addLabel`, etc.)
- [ ] Entry Analyzer "Draw on Chart" Button Handler implementiert
- [ ] Entry Analyzer "Clear Patterns" Button Handler implementiert
- [ ] Tests für `PatternOverlayMixin` erstellt
- [ ] Test: Pattern auf Chart zeichnen → Necklines/Pivots/Labels sichtbar
- [ ] Test: Pattern löschen → Overlays verschwinden
- [ ] Test: Verschiedene Pattern-Typen (bullish/bearish) haben unterschiedliche Farben

---

## 🚀 MVP 2: Smart Money Concepts (8-10h)

Smart Money Concepts (SMC) sind in 2025 sehr populär für Intraday-Trading. Diese Phase implementiert:
- **Order Blocks (OB):** Bereiche mit hohem institutionellem Interesse
- **Fair Value Gaps (FVG):** Unausgewogene Bereiche (Imbalance/Inefficiency)
- **Market Structure Shifts (MSS):** Trendwechsel-Signale (Break of Structure)

**Hinweis:** SMC sind subjektiver als klassische Patterns und erfordern sorgfältiges Tuning der Parameter.

---

### ✅ Schritt 2.1: Order Block Detector (3-4h)

**Order Blocks** sind Preis-Bereiche, in denen institutionelle Orders platziert wurden (identifizierbar durch starke Impulse).

**Erkennungskriterien:**
1. **Impulsive Move:** Starke Preisbewegung (z.B. 3+ Candles in eine Richtung mit wenig Dochten)
2. **Consolidation Zone:** Candle VOR dem Impuls = Order Block (High-Low des letzten ruhigen Candles)
3. **Mitigation:** OB wird "verbraucht" wenn Preis zurückkehrt und Zone durchdringt

---

#### 📄 Datei: `src/analysis/patterns/smart_money.py`

```python
"""Smart Money Concepts Detectors.

Implements:
- Order Blocks (OB)
- Fair Value Gaps (FVG) / Imbalance
- Market Structure Shifts (MSS) / Break of Structure (BOS)
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from src.analysis.patterns.base_detector import (
    PatternDetector, Pattern, PatternState, DirectionBias, Pivot
)

logger = logging.getLogger(__name__)


@dataclass
class OrderBlock:
    """Order Block data structure."""
    start_index: int
    end_index: int
    high: float
    low: float
    direction: str  # "BULLISH" or "BEARISH"
    strength: float  # 0-100 (based on impulse magnitude)
    mitigated: bool = False
    mitigation_index: Optional[int] = None


class OrderBlockDetector(PatternDetector):
    """Detect Order Blocks (OB) - Areas of institutional interest.

    An Order Block is the last consolidation candle before a strong impulse move.
    """

    def __init__(
        self,
        min_impulse_candles: int = 3,
        min_impulse_pct: float = 1.5,
        max_wick_ratio: float = 0.3
    ):
        """
        Args:
            min_impulse_candles: Minimum candles in impulse move
            min_impulse_pct: Minimum price move percentage for impulse
            max_wick_ratio: Maximum wick-to-body ratio for clean impulse candles
        """
        self.min_impulse_candles = min_impulse_candles
        self.min_impulse_pct = min_impulse_pct
        self.max_wick_ratio = max_wick_ratio

    def detect(self, pivots: List[Pivot], data: pd.DataFrame = None) -> List[Pattern]:
        """Detect Order Blocks in price data.

        Args:
            pivots: List of Pivot objects (not used for OB, but required by interface)
            data: OHLC DataFrame with columns ['open', 'high', 'low', 'close']

        Returns:
            List of Pattern objects representing Order Blocks
        """
        if data is None or len(data) < self.min_impulse_candles + 2:
            return []

        order_blocks = []
        i = 1  # Start from second candle

        while i < len(data) - self.min_impulse_candles:
            # Check for bullish impulse
            bullish_ob = self._detect_bullish_order_block(data, i)
            if bullish_ob:
                pattern = self._create_ob_pattern(bullish_ob, data)
                order_blocks.append(pattern)
                i = bullish_ob.end_index + 1
                continue

            # Check for bearish impulse
            bearish_ob = self._detect_bearish_order_block(data, i)
            if bearish_ob:
                pattern = self._create_ob_pattern(bearish_ob, data)
                order_blocks.append(pattern)
                i = bearish_ob.end_index + 1
                continue

            i += 1

        logger.info(f"Detected {len(order_blocks)} Order Blocks")
        return order_blocks

    def _detect_bullish_order_block(self, data: pd.DataFrame, start_idx: int) -> Optional[OrderBlock]:
        """Detect bullish Order Block (last down/consolidation candle before bullish impulse).

        Args:
            data: OHLC DataFrame
            start_idx: Starting index for detection

        Returns:
            OrderBlock object if found, else None
        """
        # Look for consolidation/down candle followed by strong bullish impulse
        ob_candle = data.iloc[start_idx]

        # Check if this candle is consolidation or bearish
        if ob_candle['close'] > ob_candle['open'] * 1.005:  # Allow small bullish consolidation
            return None

        # Check for bullish impulse starting from next candle
        impulse_start = start_idx + 1
        impulse_candles = 0
        impulse_end = impulse_start

        for i in range(impulse_start, min(impulse_start + self.min_impulse_candles + 3, len(data))):
            candle = data.iloc[i]

            # Check if candle is bullish and clean (small wicks)
            body = candle['close'] - candle['open']
            upper_wick = candle['high'] - candle['close']
            lower_wick = candle['open'] - candle['low']

            if body <= 0:  # Not bullish
                break

            wick_ratio = (upper_wick + lower_wick) / body if body > 0 else 999
            if wick_ratio > self.max_wick_ratio:
                break

            impulse_candles += 1
            impulse_end = i

            if impulse_candles >= self.min_impulse_candles:
                break

        # Validate impulse magnitude
        if impulse_candles < self.min_impulse_candles:
            return None

        impulse_move_pct = (
            (data.iloc[impulse_end]['close'] - data.iloc[impulse_start]['open'])
            / data.iloc[impulse_start]['open'] * 100
        )

        if impulse_move_pct < self.min_impulse_pct:
            return None

        # Create Order Block
        return OrderBlock(
            start_index=start_idx,
            end_index=start_idx,  # OB is single candle
            high=float(ob_candle['high']),
            low=float(ob_candle['low']),
            direction="BULLISH",
            strength=min(100.0, impulse_move_pct * 20)  # Scale to 0-100
        )

    def _detect_bearish_order_block(self, data: pd.DataFrame, start_idx: int) -> Optional[OrderBlock]:
        """Detect bearish Order Block (last up/consolidation candle before bearish impulse).

        Args:
            data: OHLC DataFrame
            start_idx: Starting index for detection

        Returns:
            OrderBlock object if found, else None
        """
        # Look for consolidation/up candle followed by strong bearish impulse
        ob_candle = data.iloc[start_idx]

        # Check if this candle is consolidation or bullish
        if ob_candle['close'] < ob_candle['open'] * 0.995:  # Allow small bearish consolidation
            return None

        # Check for bearish impulse starting from next candle
        impulse_start = start_idx + 1
        impulse_candles = 0
        impulse_end = impulse_start

        for i in range(impulse_start, min(impulse_start + self.min_impulse_candles + 3, len(data))):
            candle = data.iloc[i]

            # Check if candle is bearish and clean (small wicks)
            body = candle['open'] - candle['close']
            upper_wick = candle['high'] - candle['open']
            lower_wick = candle['close'] - candle['low']

            if body <= 0:  # Not bearish
                break

            wick_ratio = (upper_wick + lower_wick) / body if body > 0 else 999
            if wick_ratio > self.max_wick_ratio:
                break

            impulse_candles += 1
            impulse_end = i

            if impulse_candles >= self.min_impulse_candles:
                break

        # Validate impulse magnitude
        if impulse_candles < self.min_impulse_candles:
            return None

        impulse_move_pct = abs(
            (data.iloc[impulse_end]['close'] - data.iloc[impulse_start]['open'])
            / data.iloc[impulse_start]['open'] * 100
        )

        if impulse_move_pct < self.min_impulse_pct:
            return None

        # Create Order Block
        return OrderBlock(
            start_index=start_idx,
            end_index=start_idx,
            high=float(ob_candle['high']),
            low=float(ob_candle['low']),
            direction="BEARISH",
            strength=min(100.0, impulse_move_pct * 20)
        )

    def _create_ob_pattern(self, ob: OrderBlock, data: pd.DataFrame) -> Pattern:
        """Convert OrderBlock to Pattern object.

        Args:
            ob: OrderBlock object
            data: OHLC DataFrame (for timestamps)

        Returns:
            Pattern object
        """
        # Create pattern lines (support/resistance box)
        timestamp = data.index[ob.start_index]
        lines = {
            "support": [(timestamp, ob.low)] if ob.direction == "BULLISH" else [],
            "resistance": [(timestamp, ob.high)] if ob.direction == "BEARISH" else []
        }

        direction_bias = DirectionBias.UP if ob.direction == "BULLISH" else DirectionBias.DOWN

        return Pattern(
            pattern_id=f"ob_{ob.direction.lower()}_{ob.start_index}",
            pattern_type=f"order_block_{ob.direction.lower()}",
            category="SMART_MONEY",
            state=PatternState.CONFIRMED if not ob.mitigated else PatternState.INVALIDATED,
            score=ob.strength,
            direction_bias=direction_bias,
            start_index=ob.start_index,
            end_index=ob.end_index,
            pivots=[],  # OB doesn't use pivots
            lines=lines,
            scoring_breakdown={
                "strength": ob.strength,
                "mitigated": 0 if ob.mitigated else 100
            }
        )

    def calculate_score(self, pattern: Pattern, data: Optional[pd.DataFrame] = None) -> float:
        """Calculate Order Block quality score.

        Args:
            pattern: Pattern object
            data: Optional OHLC data

        Returns:
            Score (0-100)
        """
        # Score is already calculated during detection (impulse strength)
        return pattern.scoring_breakdown.get("strength", 50.0)

    def generate_lines(self, pattern: Pattern) -> dict:
        """Generate visualization lines for Order Block.

        Args:
            pattern: Pattern object

        Returns:
            Dictionary of lines
        """
        # Lines already generated in _create_ob_pattern
        return pattern.lines
```

---

### ✅ Schritt 2.2: Fair Value Gap (FVG) Detector (2-3h)

**Fair Value Gaps** (auch Imbalance oder Inefficiency) sind Bereiche, in denen Preis zu schnell gesprungen ist und eine Lücke hinterlassen hat.

**Erkennungskriterien:**
1. 3-Candle-Pattern
2. High von Candle 1 < Low von Candle 3 (Bullish FVG)
3. Low von Candle 1 > High von Candle 3 (Bearish FVG)
4. Gap-Size mindestens X% des mittleren Candles

---

#### 📄 Ergänzung zu `src/analysis/patterns/smart_money.py`

```python
@dataclass
class FairValueGap:
    """Fair Value Gap data structure."""
    start_index: int
    end_index: int
    gap_high: float
    gap_low: float
    direction: str  # "BULLISH" or "BEARISH"
    gap_size_pct: float
    filled: bool = False
    fill_index: Optional[int] = None


class FairValueGapDetector(PatternDetector):
    """Detect Fair Value Gaps (FVG) / Imbalance / Inefficiency.

    FVG occurs when price moves so fast that it leaves an imbalance
    (gap between candle 1 high and candle 3 low, or vice versa).
    """

    def __init__(
        self,
        min_gap_pct: float = 0.5
    ):
        """
        Args:
            min_gap_pct: Minimum gap size as percentage of candle 2 range
        """
        self.min_gap_pct = min_gap_pct

    def detect(self, pivots: List[Pivot], data: pd.DataFrame = None) -> List[Pattern]:
        """Detect Fair Value Gaps in price data.

        Args:
            pivots: List of Pivot objects (not used, but required by interface)
            data: OHLC DataFrame

        Returns:
            List of Pattern objects representing FVGs
        """
        if data is None or len(data) < 3:
            return []

        fvgs = []

        for i in range(len(data) - 2):
            candle1 = data.iloc[i]
            candle2 = data.iloc[i + 1]
            candle3 = data.iloc[i + 2]

            # Check for Bullish FVG (high of c1 < low of c3)
            if candle1['high'] < candle3['low']:
                gap_low = candle1['high']
                gap_high = candle3['low']
                gap_size_pct = ((gap_high - gap_low) / (candle2['high'] - candle2['low'])) * 100

                if gap_size_pct >= self.min_gap_pct:
                    fvg = FairValueGap(
                        start_index=i,
                        end_index=i + 2,
                        gap_high=float(gap_high),
                        gap_low=float(gap_low),
                        direction="BULLISH",
                        gap_size_pct=gap_size_pct
                    )
                    pattern = self._create_fvg_pattern(fvg, data)
                    fvgs.append(pattern)

            # Check for Bearish FVG (low of c1 > high of c3)
            elif candle1['low'] > candle3['high']:
                gap_high = candle1['low']
                gap_low = candle3['high']
                gap_size_pct = ((gap_high - gap_low) / (candle2['high'] - candle2['low'])) * 100

                if gap_size_pct >= self.min_gap_pct:
                    fvg = FairValueGap(
                        start_index=i,
                        end_index=i + 2,
                        gap_high=float(gap_high),
                        gap_low=float(gap_low),
                        direction="BEARISH",
                        gap_size_pct=gap_size_pct
                    )
                    pattern = self._create_fvg_pattern(fvg, data)
                    fvgs.append(pattern)

        logger.info(f"Detected {len(fvgs)} Fair Value Gaps")
        return fvgs

    def _create_fvg_pattern(self, fvg: FairValueGap, data: pd.DataFrame) -> Pattern:
        """Convert FairValueGap to Pattern object.

        Args:
            fvg: FairValueGap object
            data: OHLC DataFrame

        Returns:
            Pattern object
        """
        # Create pattern lines (gap box)
        start_time = data.index[fvg.start_index]
        end_time = data.index[fvg.end_index]

        lines = {
            "gap_zone": [
                (start_time, fvg.gap_high),
                (end_time, fvg.gap_high),
                (end_time, fvg.gap_low),
                (start_time, fvg.gap_low)
            ]
        }

        direction_bias = DirectionBias.UP if fvg.direction == "BULLISH" else DirectionBias.DOWN

        # Score based on gap size
        score = min(100.0, fvg.gap_size_pct * 15)

        return Pattern(
            pattern_id=f"fvg_{fvg.direction.lower()}_{fvg.start_index}",
            pattern_type=f"fair_value_gap_{fvg.direction.lower()}",
            category="SMART_MONEY",
            state=PatternState.CONFIRMED if not fvg.filled else PatternState.INVALIDATED,
            score=score,
            direction_bias=direction_bias,
            start_index=fvg.start_index,
            end_index=fvg.end_index,
            pivots=[],
            lines=lines,
            scoring_breakdown={
                "gap_size_pct": fvg.gap_size_pct,
                "filled": 0 if fvg.filled else 100
            }
        )

    def calculate_score(self, pattern: Pattern, data: Optional[pd.DataFrame] = None) -> float:
        """Calculate FVG quality score.

        Args:
            pattern: Pattern object
            data: Optional OHLC data

        Returns:
            Score (0-100)
        """
        gap_size = pattern.scoring_breakdown.get("gap_size_pct", 0)
        return min(100.0, gap_size * 15)

    def generate_lines(self, pattern: Pattern) -> dict:
        """Generate visualization lines for FVG.

        Args:
            pattern: Pattern object

        Returns:
            Dictionary of lines
        """
        return pattern.lines
```

---

### ✅ Schritt 2.3: Entry Analyzer Integration (SMC Tab) (2-3h)

**Erweiterung des Pattern Recognition Tabs:** Neue Kategorie "Smart Money" mit OB, FVG, MSS.

---

#### 📄 Ergänzung zu `src/ui/dialogs/entry_analyzer_popup.py`

```python
def _on_detect_patterns_clicked(self):
    """Event Handler: Detect Patterns (INCLUDING Smart Money Concepts)."""
    try:
        # ... existing code for H&S and Double Top/Bottom ...

        # 3. Detect Smart Money Concepts
        from src.analysis.patterns.smart_money import (
            OrderBlockDetector,
            FairValueGapDetector
        )

        # Order Blocks
        ob_detector = OrderBlockDetector()
        ob_patterns = ob_detector.detect(pivots=[], data=data)
        all_patterns.extend(ob_patterns)
        logger.info(f"Detected {len(ob_patterns)} Order Blocks")

        # Fair Value Gaps
        fvg_detector = FairValueGapDetector()
        fvg_patterns = fvg_detector.detect(pivots=[], data=data)
        all_patterns.extend(fvg_patterns)
        logger.info(f"Detected {len(fvg_patterns)} Fair Value Gaps")

        # 4. Update UI
        self._update_patterns_table(all_patterns)
        self._update_pattern_tree_counts(all_patterns)

        # ... rest of existing code ...

        QMessageBox.information(
            self,
            "Detection Complete",
            f"Detected {len(all_patterns)} patterns:\n"
            f"- Head & Shoulders: {len(hs_patterns)}\n"
            f"- Double Top/Bottom: {len(double_patterns)}\n"
            f"- Order Blocks: {len(ob_patterns)}\n"
            f"- Fair Value Gaps: {len(fvg_patterns)}"
        )

    except Exception as e:
        logger.exception("Pattern detection failed")
        QMessageBox.critical(self, "Error", f"Pattern detection failed: {str(e)}")
```

**Pattern Tree Update:** Add "Smart Money" category node in `_create_pattern_categories_tree()`.

---

**Checklist (MVP 2):**
- [ ] Order Block Detector implementiert (`OrderBlockDetector` in `smart_money.py`)
- [ ] Bullish & Bearish Order Blocks erkennung
- [ ] Fair Value Gap Detector implementiert (`FairValueGapDetector`)
- [ ] Bullish & Bearish FVG Erkennung
- [ ] Entry Analyzer Pattern Tab integriert SMC-Patterns
- [ ] Pattern Tree hat "Smart Money" Kategorie
- [ ] Tests für Order Block Detection
- [ ] Tests für FVG Detection
- [ ] Test: BTCUSDT 5m Chart → Mindestens 5 Order Blocks + 10 FVGs detektiert

---

