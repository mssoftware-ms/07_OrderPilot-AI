# ✅ Checkliste: Chartmuster-Erkennung (Pattern Recognition) Implementation

**Start:** 2026-01-19
**Letzte Aktualisierung:** 2026-01-19 16:30
**Gesamtfortschritt:** 0% (0/98 Tasks)
**UPDATE:** Plan aktualisiert für konkrete Implementation und Integration im **Entry Analyzer**

---

## 🎯 **PROJEKT-ÜBERBLICK**

### Ziele
1. **Regelbasierte Pattern Detection** - Named Patterns (Head & Shoulders, Double Tops/Bottoms, Triangles, Flags)
2. **Similarity Search** - DTW-basiertes historisches Pattern Matching
3. **Smart Money Concepts** - Order Blocks, Fair Value Gaps, Market Structure Shifts
4. **Trend Following Patterns** - Breakouts, Channels, Momentum-basierte Muster
5. **UI Integration** - Neuer Tab im **Entry Analyzer** mit Visualisierung (+ Pattern Details Popup für komplexe Ansichten)
6. **Standardisierter Export** - JSON/CSV für externe CEL-basierte Trading-Systeme

**WICHTIG:** Dieses Modul ist **NUR für Pattern Detection**. Trading Rules & CEL-Integration erfolgen in separatem System!

### Technologie-Stack
- **Core:** Python 3.12, pandas, numpy, scipy
- **Pattern Libraries:** PatternPy, TA-Lib
- **ML/DTW:** scikit-learn, fastdtw
- **Pivot Detection:** ZigZag-Algorithm (ATR-based)
- **UI:** PyQt6 (Entry Analyzer Integration)
- **Visualization:** TradingView Lightweight Charts (Chart Overlay)

### Performance-Ziele
- **Pattern Detection:** <500ms für 1000 Bars
- **Similarity Search:** <2s für DTW-Matching
- **Pivot Detection:** <200ms Real-time
- **UI Responsiveness:** <100ms

---

## 🛠️ **CODE-QUALITÄTS-STANDARDS (vor jedem Task lesen!)**

### **✅ ERFORDERLICH für jeden Task:**
1. **Vollständige Implementation** - Keine TODO/Platzhalter
2. **Error Handling** - try/catch für alle kritischen Operationen
3. **Input Validation** - Alle Parameter validieren (Bar-Count, Toleranzen, ATR-Multiplier)
4. **Type Hints** - Alle Function Signatures typisiert
5. **Docstrings** - Alle public Functions dokumentiert (mit Geometrie-Kriterien)
6. **Logging** - Pattern Detection Events loggen (Debug-Level für Geometrie)
7. **Tests** - Unit Tests für Pattern-Kriterien + Backtests für Forward Returns
8. **Clean Code** - Alter Code vollständig entfernt

### **❌ VERBOTEN:**
1. **Platzhalter-Code:** `# TODO: Implement Triangle Detection`
2. **Auskommentierte Blöcke:** `# def old_pattern_detector():`
3. **Silent Failures:** `except: pass` (Pattern nicht erkannt = Silent Bug)
4. **Hardcoded Values:** `zigzag_threshold = 5.0` (muss konfigurierbar sein)
5. **Vague Errors:** `raise Exception("Pattern invalid")` (welches Pattern? welche Regel?)
6. **Missing Validation:** Keine Input-Checks für Bar-Daten (NaN, leer, zu kurz)
7. **Dummy Returns:** `return {"pattern": "not_implemented"}`
8. **Incomplete UI:** Buttons ohne Pattern-Visualisierung

### **🔍 BEFORE MARKING COMPLETE:**
- [ ] Pattern funktioniert (getestet mit realen BTCUSDT-Daten)
- [ ] Keine TODOs im Code
- [ ] Error Handling implementiert (fehlende Daten, zu kurze Historie)
- [ ] Tests geschrieben (positive + negative Cases)
- [ ] Alter Code entfernt
- [ ] Logging hinzugefügt (Pattern State Changes)
- [ ] Input Validation vorhanden (Bar-Count, Parameter-Ranges)
- [ ] Type Hints vollständig
- [ ] **Pattern Score berechnet** (0-100, Komponenten dokumentiert)
- [ ] **Geometrie-Linien** für Chart-Overlay generiert
- [ ] **Backtest** durchgeführt (Forward Return Statistik)

---

## 📊 Status-Legende
- ⬜ Offen / Nicht begonnen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Fehler / Blockiert
- ⭐ Übersprungen / Nicht benötigt

---

## 🛠️ **TRACKING-FORMAT (PFLICHT)**

### **Erfolgreicher Task:**
```markdown
- [ ] **1.2.3 Task Name**
  Status: ✅ Abgeschlossen (2026-01-19 14:30) → *Head & Shoulders Detector implementiert*
  Code: `src/analysis/patterns/reversal_patterns.py:123-456` (wo implementiert)
  Tests: `tests/patterns/test_head_and_shoulders.py:TestHnSPattern` (welche Tests)
  Backtest: Accuracy: 89%, Forward +5D: +2.3%, Forward +10D: +4.1%
  Nachweis: Screenshot der Pattern-Visualisierung im Entry Analyzer
```

### **Fehlgeschlagener Task:**
```markdown
- [ ] **1.2.3 Task Name**
  Status: ❌ Fehler (2026-01-19 14:30) → *ZigZag findet keine Pivots bei volatilen Märkten*
  Fehler: `ValueError: No pivots found with threshold=5.0 ATR`
  Ursache: Threshold zu hoch für Crypto-Märkte (hohe Volatilität)
  Lösung: Adaptive Threshold basierend auf BB-Width implementieren
  Retry: Geplant für 2026-01-20 10:00
```

---

## Phase 0: Vorbereitung & Setup (2 Stunden)

- [ ] **0.1 Entwicklungsumgebung Setup**
  Status: ⬜ → *Python 3.12, VS Code, Git Branch erstellen*

- [ ] **0.2 Abhängigkeiten-Analyse**
  Status: ⬜ → *PatternPy, TA-Lib, fastdtw, scipy kompatibel prüfen*

- [ ] **0.3 Projektstruktur erstellen**
  Status: ⬜ → *Ordner-Struktur für Pattern-Module*
  ```
  src/analysis/patterns/
  ├── __init__.py
  ├── pivot_engine.py          # ZigZag/Swing Detection
  ├── named_patterns.py        # Base Class für Named Patterns
  ├── reversal_patterns.py     # H&S, Double Top/Bottom
  ├── continuation_patterns.py # Triangles, Flags, Pennants
  ├── smart_money.py           # Order Blocks, FVG, MSS
  ├── trend_following.py       # Breakouts, Channels
  ├── similarity_search.py     # DTW-basiertes Matching
  ├── pattern_scorer.py        # Scoring-Algorithmus
  └── pattern_visualizer.py    # Chart-Overlay Geometrie

  tests/patterns/
  ├── test_pivot_engine.py
  ├── test_reversal_patterns.py
  ├── test_continuation_patterns.py
  ├── test_smart_money.py
  ├── test_similarity_search.py
  └── fixtures/
      └── btcusdt_1d_sample.csv  # Test-Daten
  ```

- [ ] **0.4 Git Branch & Versionierung**
  Status: ⬜ → *Branch: feature/pattern-recognition*

- [ ] **0.5 Dependencies Installation**
  Status: ⬜ → *pip install patternpy ta-lib fastdtw scikit-learn*

---

## Phase 1: Foundation - Pivot Engine & Base Classes (8 Stunden)

### 1.1 Pivot Detection Engine (4 Stunden)

- [ ] **1.1.1 ZigZag Implementation (Prozent-basiert)**
  Status: ⬜ → *Datei: src/analysis/patterns/pivot_engine.py*
  - [ ] Funktion: `detect_pivots_percent(data, threshold_pct)`
  - [ ] High/Low Pivot Detection mit konfigurierbarem Threshold
  - [ ] Ausgabe: Liste von (index, type, price) Tupeln

- [ ] **1.1.2 ZigZag Implementation (ATR-basiert)**
  Status: ⬜ → *Datei: src/analysis/patterns/pivot_engine.py*
  - [ ] Funktion: `detect_pivots_atr(data, atr_mult, atr_period=14)`
  - [ ] Adaptive Pivot Detection basierend auf ATR
  - [ ] Vorteil: Automatische Anpassung an Marktvolatilität

- [ ] **1.1.3 Swing Point Validation**
  Status: ⬜ → *Datei: src/analysis/patterns/pivot_engine.py*
  - [ ] Funktion: `validate_swing_point(pivot, lookback_left, lookback_right)`
  - [ ] Prüfung: Ist Pivot lokales Maximum/Minimum?
  - [ ] Konfigurierbarer Lookback-Bereich

- [ ] **1.1.4 Pivot Filtering & Cleanup**
  Status: ⬜ → *Datei: src/analysis/patterns/pivot_engine.py*
  - [ ] Funktion: `filter_minor_pivots(pivots, min_distance_bars)`
  - [ ] Entfernung redundanter Pivots (zu dicht beieinander)
  - [ ] Merge benachbarter Pivots innerhalb Toleranzband

- [ ] **1.1.5 Pivot Engine Tests**
  Status: ⬜ → *Datei: tests/patterns/test_pivot_engine.py*
  - [ ] Test: ZigZag mit bekannten Swing-Punkten
  - [ ] Test: ATR-basiert vs. Prozent-basiert Vergleich
  - [ ] Test: Edge Cases (flache Märkte, Gaps, extreme Volatilität)

### 1.2 Base Classes & Pattern Interface (4 Stunden)

- [ ] **1.2.1 PatternDetector Base Class**
  Status: ⬜ → *Datei: src/analysis/patterns/named_patterns.py*
  ```python
  class PatternDetector(ABC):
      @abstractmethod
      def detect(self, pivots: List[Pivot]) -> List[Pattern]:
          """Detect patterns from pivot points."""
          pass

      @abstractmethod
      def score(self, pattern: Pattern) -> float:
          """Calculate pattern score (0-100)."""
          pass

      @abstractmethod
      def get_lines(self, pattern: Pattern) -> Dict[str, List[Point]]:
          """Generate geometry for chart overlay."""
          pass
  ```

- [ ] **1.2.2 Pattern Data Models**
  Status: ⬜ → *Datei: src/analysis/patterns/models.py*
  - [ ] `Pattern` (id, type, state, score, direction_bias, start_idx, end_idx)
  - [ ] `Pivot` (index, type, price, timestamp)
  - [ ] `PatternState` (FORMING, CONFIRMED, FAILED, INVALIDATED)
  - [ ] `DirectionBias` (UP, DOWN, NONE)

- [ ] **1.2.3 Pattern Scoring System**
  Status: ⬜ → *Datei: src/analysis/patterns/pattern_scorer.py*
  - [ ] Komponente 1: **Geometrie** (0-60) - Symmetrie, Trendlinien-Fit, Verhältnisse
  - [ ] Komponente 2: **Kontext** (0-20) - Trendumfeld, ADX, Volume
  - [ ] Komponente 3: **Confirmation** (0-20) - Breakout bestätigt, Volume-Spike
  - [ ] Funktion: `calculate_pattern_score(pattern, market_context)`

- [ ] **1.2.4 Pattern Visualizer Interface**
  Status: ⬜ → *Datei: src/analysis/patterns/pattern_visualizer.py*
  - [ ] Funktion: `generate_lines(pattern) -> Dict[str, List[Point]]`
  - [ ] Necklines, Trendlines, Support/Resistance als (timestamp, price) Paare
  - [ ] Format kompatibel mit TradingView Lightweight Charts API

---

## Phase 2: Named Patterns - Reversal (12 Stunden)

### 2.1 Head & Shoulders (Top/Bottom) (4 Stunden)

- [ ] **2.1.1 H&S Geometry Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/reversal_patterns.py*
  - [ ] Funktion: `detect_head_and_shoulders(pivots, tolerance_pct=2.0)`
  - [ ] 5-Pivot Struktur: LS – Trough1 – Head – Trough2 – RS
  - [ ] Kriterien:
    - Head höher als beide Shoulders (Top) oder tiefer (Bottom)
    - Shoulders im Toleranzband (z.B. ±2%)
    - Troughs bilden Neckline (ähnliches Niveau)

- [ ] **2.1.2 Neckline Calculation**
  Status: ⬜ → *Datei: src/analysis/patterns/reversal_patterns.py*
  - [ ] Funktion: `calculate_neckline(trough1, trough2)`
  - [ ] Lineare Regression durch beide Troughs
  - [ ] Projektion für Breakout-Bestätigung

- [ ] **2.1.3 H&S Confirmation Logic**
  Status: ⬜ → *Datei: src/analysis/patterns/reversal_patterns.py*
  - [ ] Funktion: `check_hs_confirmation(pattern, current_bar)`
  - [ ] Breakout: Close unter/über Neckline
  - [ ] Optional: Volume-Bestätigung (Spike bei Breakout)
  - [ ] State-Update: FORMING → CONFIRMED oder FAILED

- [ ] **2.1.4 H&S Scoring Implementation**
  Status: ⬜ → *Datei: src/analysis/patterns/reversal_patterns.py*
  - [ ] Score-Komponenten:
    - Shoulder-Symmetrie (0-30): `score = 30 * (1 - abs(LS-RS)/Head)`
    - Trough-Alignment (0-15): Neckline-Fit (R² Wert)
    - Head-Prominence (0-15): Head deutlich höher/tiefer
    - Context (0-20): Nach Uptrend/Downtrend?
    - Confirmation (0-20): Breakout bestätigt?

- [ ] **2.1.5 H&S Tests & Backtests**
  Status: ⬜ → *Datei: tests/patterns/test_head_and_shoulders.py*
  - [ ] Test: Perfekte H&S Struktur → Score >80
  - [ ] Test: Asymmetrische Shoulders → Score <60
  - [ ] Backtest: Forward Returns nach H&S Confirmation
  - [ ] Erwartung: 89-93% Accuracy (laut Research)

### 2.2 Double Top / Double Bottom (4 Stunden)

- [ ] **2.2.1 Double Top/Bottom Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/reversal_patterns.py*
  - [ ] Funktion: `detect_double_top(pivots, tolerance_pct=1.5)`
  - [ ] 3-Pivot Struktur: Peak1 – Trough – Peak2
  - [ ] Kriterien:
    - Peaks im Toleranzband (z.B. ±1.5%)
    - Trough signifikant tiefer (min. 3% oder 2*ATR)
    - Symmetrie der Peaks (ähnlicher Abstand zu Trough)

- [ ] **2.2.2 Support/Resistance Level Calculation**
  Status: ⬜ → *Datei: src/analysis/patterns/reversal_patterns.py*
  - [ ] Funktion: `calculate_sr_level(trough)`
  - [ ] Confirmation-Level = Trough-Preis (für Breakout)
  - [ ] Target-Projektion: Abstand Peak-Trough projiziert

- [ ] **2.2.3 Double Top/Bottom Confirmation**
  Status: ⬜ → *Datei: src/analysis/patterns/reversal_patterns.py*
  - [ ] Funktion: `check_double_confirmation(pattern, current_bar)`
  - [ ] Breakout unter Trough (Top) oder über Peak (Bottom)
  - [ ] Volume-Analyse: Höheres Volume bei Breakout

- [ ] **2.2.4 Double Top/Bottom Scoring**
  Status: ⬜ → *Datei: src/analysis/patterns/reversal_patterns.py*
  - [ ] Score-Komponenten:
    - Peak-Symmetrie (0-30): Abweichung der Peaks
    - Trough-Tiefe (0-15): Signifikanz des Rückgangs
    - Zeitliche Symmetrie (0-15): Ähnlicher Abstand
    - Context (0-20): Nach Trend
    - Confirmation (0-20): Breakout bestätigt

- [ ] **2.2.5 Tests & Backtests**
  Status: ⬜ → *Datei: tests/patterns/test_double_tops.py*
  - [ ] Test: Perfekte Double Top → Score >85
  - [ ] Test: Ungleiche Peaks → Score <50
  - [ ] Backtest: Erfolgsrate bei bestätigten Patterns

### 2.3 Triple Top / Triple Bottom (4 Stunden)

- [ ] **2.3.1 Triple Top/Bottom Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/reversal_patterns.py*
  - [ ] Funktion: `detect_triple_top(pivots, tolerance_pct=2.0)`
  - [ ] 5-Pivot Struktur: Peak1 – Trough1 – Peak2 – Trough2 – Peak3
  - [ ] Kriterien: Alle Peaks im Toleranzband, Troughs ähnlich

- [ ] **2.3.2 Triple Pattern Scoring**
  Status: ⬜ → *Datei: src/analysis/patterns/reversal_patterns.py*
  - [ ] Ähnlich Double Top/Bottom
  - [ ] Zusatz-Bonus: 3 Peaks = stärkeres Signal (+10 Punkte)

- [ ] **2.3.3 Tests & Backtests**
  Status: ⬜ → *Datei: tests/patterns/test_triple_tops.py*

---

## Phase 3: Named Patterns - Continuation (10 Stunden)

### 3.1 Triangle Patterns (6 Stunden)

- [ ] **3.1.1 Triangle Base Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/continuation_patterns.py*
  - [ ] Funktion: `detect_triangles(pivots, min_touches=4)`
  - [ ] Trendlinien-Berechnung: Upper & Lower Trendline
  - [ ] Konvergenz-Check: Linien schneiden sich in Zukunft (Apex)

- [ ] **3.1.2 Symmetrisches Triangle**
  Status: ⬜ → *Datei: src/analysis/patterns/continuation_patterns.py*
  - [ ] Funktion: `classify_symmetric_triangle(upper_line, lower_line)`
  - [ ] Kriterien:
    - Lower Highs (Upper Trendline fallend)
    - Higher Lows (Lower Trendline steigend)
    - Ähnliche Konvergenzrate

- [ ] **3.1.3 Ascending Triangle**
  Status: ⬜ → *Datei: src/analysis/patterns/continuation_patterns.py*
  - [ ] Funktion: `classify_ascending_triangle(upper_line, lower_line)`
  - [ ] Kriterien:
    - Upper Trendline horizontal (Resistance)
    - Lower Trendline steigend (Higher Lows)

- [ ] **3.1.4 Descending Triangle**
  Status: ⬜ → *Datei: src/analysis/patterns/continuation_patterns.py*
  - [ ] Funktion: `classify_descending_triangle(upper_line, lower_line)`
  - [ ] Kriterien:
    - Upper Trendline fallend (Lower Highs)
    - Lower Trendline horizontal (Support)

- [ ] **3.1.5 Triangle Breakout Detection**
  Status: ⬜ → *Datei: src/analysis/patterns/continuation_patterns.py*
  - [ ] Funktion: `detect_triangle_breakout(pattern, current_bar)`
  - [ ] Breakout-Richtung: Up (bullish) oder Down (bearish)
  - [ ] Volume-Confirmation: Spike bei Breakout

- [ ] **3.1.6 Tests & Backtests**
  Status: ⬜ → *Datei: tests/patterns/test_triangles.py*
  - [ ] Test: Alle 3 Triangle-Typen erkennen
  - [ ] Backtest: Breakout-Erfolgsrate

### 3.2 Flags & Pennants (4 Stunden)

- [ ] **3.2.1 Flag Pattern Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/continuation_patterns.py*
  - [ ] Funktion: `detect_flag(pivots, impulse_leg)`
  - [ ] Kriterien:
    - Starker Impulse-Move (>5% in <5 Bars)
    - Parallele Konsolidierung (Counter-Trend)
    - Kleine Range (< 40% des Impulse)

- [ ] **3.2.2 Pennant Pattern Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/continuation_patterns.py*
  - [ ] Funktion: `detect_pennant(pivots, impulse_leg)`
  - [ ] Kriterien:
    - Starker Impulse-Move
    - Konvergierende Trendlinien (Mini-Triangle)
    - Sehr kleine Range

- [ ] **3.2.3 Flag/Pennant Breakout**
  Status: ⬜ → *Datei: src/analysis/patterns/continuation_patterns.py*
  - [ ] Breakout in Impulse-Richtung erwartet
  - [ ] Target: Impulse-Länge projiziert

- [ ] **3.2.4 Tests & Backtests**
  Status: ⬜ → *Datei: tests/patterns/test_flags_pennants.py*

---

## Phase 4: Smart Money Concepts (SMC) (12 Stunden)

### 4.1 Order Blocks (4 Stunden)

- [ ] **4.1.1 Order Block Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/smart_money.py*
  - [ ] Funktion: `detect_order_blocks(data, lookback=20)`
  - [ ] Kriterien:
    - Starker Move weg von Level (>3% in <3 Bars)
    - Hoher Turnover (Volume-Spike)
    - Level = Open/Close der letzten Kerze vor Breakout

- [ ] **4.1.2 Bullish Order Block**
  Status: ⬜ → *Datei: src/analysis/patterns/smart_money.py*
  - [ ] Down-Candle gefolgt von starkem Uptrend
  - [ ] Order Block = High-Low Range der Down-Candle

- [ ] **4.1.3 Bearish Order Block**
  Status: ⬜ → *Datei: src/analysis/patterns/smart_money.py*
  - [ ] Up-Candle gefolgt von starkem Downtrend
  - [ ] Order Block = High-Low Range der Up-Candle

- [ ] **4.1.4 Order Block Validation**
  Status: ⬜ → *Datei: src/analysis/patterns/smart_money.py*
  - [ ] Funktion: `validate_order_block(block, current_price)`
  - [ ] Retest: Preis kehrt zu Block zurück
  - [ ] Bounce: Preis respektiert Block (Support/Resistance)

- [ ] **4.1.5 Tests**
  Status: ⬜ → *Datei: tests/patterns/test_order_blocks.py*

### 4.2 Fair Value Gaps (FVG) (4 Stunden)

- [ ] **4.2.1 FVG Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/smart_money.py*
  - [ ] Funktion: `detect_fair_value_gaps(data)`
  - [ ] 3-Candle Pattern:
    - Candle 1 High < Candle 3 Low (Bullish FVG)
    - Candle 1 Low > Candle 3 High (Bearish FVG)
  - [ ] Gap = Imbalance-Zone

- [ ] **4.2.2 FVG Scoring**
  Status: ⬜ → *Datei: src/analysis/patterns/smart_money.py*
  - [ ] Gap-Größe relativ zu ATR
  - [ ] Volume während Gap-Bildung
  - [ ] FVG in Trend-Richtung = höherer Score

- [ ] **4.2.3 FVG Retest & Fill**
  Status: ⬜ → *Datei: src/analysis/patterns/smart_money.py*
  - [ ] Funktion: `check_fvg_retest(fvg, current_bar)`
  - [ ] Partial Fill vs. Full Fill
  - [ ] Retest = Entry-Chance

- [ ] **4.2.4 Tests & Backtests**
  Status: ⬜ → *Datei: tests/patterns/test_fair_value_gaps.py*
  - [ ] Test: FVG Erkennung
  - [ ] Backtest: Erfolgsrate bei FVG-Retest-Entries

### 4.3 Market Structure Shifts (MSS) (4 Stunden)

- [ ] **4.3.1 Break of Structure (BOS) Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/smart_money.py*
  - [ ] Funktion: `detect_break_of_structure(pivots)`
  - [ ] Bullish BOS: Preis bricht über letzten Swing High
  - [ ] Bearish BOS: Preis bricht unter letzten Swing Low

- [ ] **4.3.2 Change of Character (CHoCH) Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/smart_money.py*
  - [ ] Funktion: `detect_change_of_character(pivots)`
  - [ ] CHoCH = Erste Anzeichen von Trend-Umkehr
  - [ ] Bearish CHoCH in Uptrend: Lower High gebildet
  - [ ] Bullish CHoCH in Downtrend: Higher Low gebildet

- [ ] **4.3.3 Market Structure Shift (MSS) Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/smart_money.py*
  - [ ] Funktion: `detect_market_structure_shift(pivots)`
  - [ ] MSS = Stärkere Form von CHoCH
  - [ ] Kombination: CHoCH + BOS in neue Richtung

- [ ] **4.3.4 Tests**
  Status: ⬜ → *Datei: tests/patterns/test_market_structure.py*

---

## Phase 5: Trend Following Patterns (10 Stunden)

### 5.1 Channel & Trendline Detection (6 Stunden)

- [ ] **5.1.1 Trendline Calculation**
  Status: ⬜ → *Datei: src/analysis/patterns/trend_following.py*
  - [ ] Funktion: `calculate_trendline(pivots, min_touches=3)`
  - [ ] Linear Regression durch Pivots
  - [ ] R² Wert als Fit-Quality

- [ ] **5.1.2 Uptrend Channel Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/trend_following.py*
  - [ ] Funktion: `detect_uptrend_channel(pivots)`
  - [ ] Lower Trendline durch Swing Lows (Support)
  - [ ] Upper Trendline parallel dazu (Resistance)
  - [ ] Kriterien: Min. 3 Touches pro Line

- [ ] **5.1.3 Downtrend Channel Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/trend_following.py*
  - [ ] Funktion: `detect_downtrend_channel(pivots)`
  - [ ] Upper Trendline durch Swing Highs (Resistance)
  - [ ] Lower Trendline parallel (Support)

- [ ] **5.1.4 Channel Breakout Detection**
  Status: ⬜ → *Datei: src/analysis/patterns/trend_following.py*
  - [ ] Funktion: `detect_channel_breakout(channel, current_bar)`
  - [ ] Breakout über Upper Trendline = Bullish Acceleration
  - [ ] Breakdown unter Lower Trendline = Trend Reversal

- [ ] **5.1.5 Tests**
  Status: ⬜ → *Datei: tests/patterns/test_channels.py*

### 5.2 Breakout Patterns (4 Stunden)

- [ ] **5.2.1 Range Breakout Detector**
  Status: ⬜ → *Datei: src/analysis/patterns/trend_following.py*
  - [ ] Funktion: `detect_range_breakout(data, lookback=20)`
  - [ ] Kriterien:
    - Range = Max(High) - Min(Low) über Lookback
    - Breakout wenn Close > Range High oder < Range Low
    - Confirmation: Volume Spike (>150% Avg)

- [ ] **5.2.2 ATR Channel Breakout**
  Status: ⬜ → *Datei: src/analysis/patterns/trend_following.py*
  - [ ] Funktion: `detect_atr_breakout(data, atr_mult=2.0, period=14)`
  - [ ] Channel = MA ± ATR * Multiplier
  - [ ] Breakout über Upper Channel = Strong Trend

- [ ] **5.2.3 Donchian Channel Breakout**
  Status: ⬜ → *Datei: src/analysis/patterns/trend_following.py*
  - [ ] Funktion: `detect_donchian_breakout(data, period=20)`
  - [ ] Upper Band = Highest High über Period
  - [ ] Lower Band = Lowest Low über Period
  - [ ] Breakout = Neues High/Low

- [ ] **5.2.4 Tests & Backtests**
  Status: ⬜ → *Datei: tests/patterns/test_breakouts.py*
  - [ ] Backtest: Donchian Breakout Turtle Trading Style

---

## Phase 6: Similarity Search & DTW (8 Stunden)

### 6.1 Historical Pattern Matching (8 Stunden)

- [ ] **6.1.1 Window Normalization**
  Status: ⬜ → *Datei: src/analysis/patterns/similarity_search.py*
  - [ ] Funktion: `normalize_window(window, method='zscore')`
  - [ ] Z-Score: `(x - mean) / std`
  - [ ] Min-Max: `(x - min) / (max - min)`
  - [ ] Log Returns: `log(close[i] / close[i-1])`

- [ ] **6.1.2 Fast Correlation Filter**
  Status: ⬜ → *Datei: src/analysis/patterns/similarity_search.py*
  - [ ] Funktion: `prefilter_candidates(query_window, historical_data, top_k=100)`
  - [ ] Pearson Correlation als schneller Pre-Filter
  - [ ] Nur Top-K Kandidaten für DTW weiterleiten

- [ ] **6.1.3 DTW Distance Calculation**
  Status: ⬜ → *Datei: src/analysis/patterns/similarity_search.py*
  - [ ] Funktion: `calculate_dtw_distance(query, candidate, window_constraint=10)`
  - [ ] fastdtw Library verwenden
  - [ ] Window Constraint für Performance (Sakoe-Chiba Band)

- [ ] **6.1.4 Top-K Matches Retrieval**
  Status: ⬜ → *Datei: src/analysis/patterns/similarity_search.py*
  - [ ] Funktion: `find_similar_patterns(query_window, historical_data, top_k=10)`
  - [ ] Return: Liste von (timestamp, distance, window_data)

- [ ] **6.1.5 Forward Return Analysis**
  Status: ⬜ → *Datei: src/analysis/patterns/similarity_search.py*
  - [ ] Funktion: `analyze_forward_returns(matches, horizons=[5, 10, 20])`
  - [ ] Berechne Return nach +5/+10/+20 Tagen für alle Matches
  - [ ] Statistik: Mean, Median, Win Rate, Best/Worst Case

- [ ] **6.1.6 Similarity Search UI Integration**
  Status: ⬜ → *Datei: src/ui/dialogs/entry_analyzer_popup.py*
  - [ ] Neuer Sub-Tab: "Similar Patterns"
  - [ ] Input: Window Size (default: 60 Bars)
  - [ ] Output: Top-10 Matches mit Chart-Overlay
  - [ ] Forward Returns Table

- [ ] **6.1.7 Tests & Performance Benchmarks**
  Status: ⬜ → *Datei: tests/patterns/test_similarity_search.py*
  - [ ] Test: DTW findet identische Patterns (distance ≈ 0)
  - [ ] Performance: <2s für 1000 historische Fenster

---

## Phase 7: Integration im Entry Analyzer (12 Stunden)

**WICHTIG:** Integration erfolgt im **Entry Analyzer** (`src/ui/dialogs/entry_analyzer_popup.py`)
**Strategie:** Kompakter Tab + Detailliertes Popup für komplexe Pattern-Ansichten

### 7.1 Pattern Recognition Tab im Entry Analyzer (6 Stunden)

- [ ] **7.1.1 Neuen Tab "Pattern Recognition" hinzufügen**
  Status: ⬜ → *Datei: src/ui/dialogs/entry_analyzer_popup.py (Zeile ~240)*
  - [ ] Tab nach "Validation" Tab einfügen
  - [ ] Tab-Icon: 📊
  - [ ] **Kompaktes 2-Spalten Layout** (nicht 3-spaltig):
    - Links (40%): Pattern-Kategorien mit Count-Badges
    - Rechts (60%): Erkannte Patterns-Liste mit Quick-Actions

  ```python
  # In EntryAnalyzerPopup.__init__() nach Zeile ~250
  self.pattern_tab = self._create_pattern_recognition_tab()
  self.tabs.addTab(self.pattern_tab, "📊 Patterns")
  ```

- [ ] **7.1.2 Pattern-Kategorien Tree**
  Status: ⬜ → *Datei: src/ui/dialogs/entry_analyzer_popup.py*
  ```
  📊 Pattern Recognition
  ├── ↩️ Reversal Patterns
  │   ├── Head & Shoulders (3 detected)
  │   ├── Double Tops/Bottoms (5 detected)
  │   └── Triple Tops/Bottoms (1 detected)
  ├── ↪️ Continuation Patterns
  │   ├── Triangles (2 detected)
  │   └── Flags/Pennants (4 detected)
  ├── 💰 Smart Money Concepts
  │   ├── Order Blocks (12 detected)
  │   ├── Fair Value Gaps (8 detected)
  │   └── Market Structure Shifts (3 detected)
  ├── 📈 Trend Following
  │   ├── Channels (1 detected)
  │   └── Breakouts (6 detected)
  └── 🔍 Similar Patterns
      └── Historical Matches (10 found)
  ```

- [ ] **7.1.3 Detected Patterns Table**
  Status: ⬜ → *Datei: src/ui/dialogs/entry_analyzer_popup.py*
  - [ ] Spalten:
    - Pattern Type (mit Icon)
    - State (🔴 Forming, 🟢 Confirmed, ⚫ Failed)
    - Score (0-100 mit Progress Bar)
    - Direction (↗️ UP, ↘️ DOWN, ↔️ NONE)
    - Timeframe (1D, 4H, 1H)
    - Start Time
    - End Time

- [ ] **7.1.4 Pattern-Details Panel**
  Status: ⬜ → *Datei: src/ui/dialogs/entry_analyzer_popup.py*
  - [ ] Geometrie-Details:
    - Pivot-Punkte (Tabellarisch)
    - Trendlinien-Parameter (Slope, Intercept, R²)
    - Toleranzen & Kriterien
  - [ ] Scoring-Breakdown:
    - Geometrie: XX/60
    - Kontext: XX/20
    - Confirmation: XX/20
  - [ ] Forward Returns (bei Similarity Search):
    - +5D: X.X%
    - +10D: X.X%
    - +20D: X.X%

- [ ] **7.1.5 Pattern Configuration Panel**
  Status: ⬜ → *Datei: src/ui/dialogs/entry_analyzer_popup.py*
  - [ ] Collapsible Section: "⚙️ Detection Settings"
  - [ ] Pivot Engine:
    - ZigZag Threshold (Prozent/ATR)
    - ATR Period
    - Min Pivot Distance
  - [ ] Pattern-spezifisch:
    - Tolerance %
    - Min Touches
    - Volume Confirmation
  - [ ] Similarity Search:
    - Window Size
    - Top-K Matches
    - Distance Metric

- [ ] **7.1.6 Action Buttons**
  Status: ⬜ → *Datei: src/ui/dialogs/entry_analyzer_popup.py*
  - [ ] "🔍 Detect Patterns" Button
  - [ ] "📊 Draw on Chart" Button (Overlay aktivieren)
  - [ ] "🗑️ Clear Patterns" Button
  - [ ] "📄 Export Patterns" Button (JSON/CSV)

### 7.2 Chart Overlay Integration (6 Stunden)

- [ ] **7.2.1 JavaScript API Extensions**
  Status: ⬜ → *Datei: src/ui/widgets/chart_js_template.html*
  - [ ] Funktion: `addPatternOverlay(pattern_data)`
  - [ ] Pattern-Linien zeichnen (Neckline, Trendlines, Channels)
  - [ ] Pattern-Labels (mit Score, State)
  - [ ] Farbcodierung: Forming (gelb), Confirmed (grün), Failed (rot)

- [ ] **7.2.2 Pattern-Linien Rendering**
  Status: ⬜ → *Datei: src/ui/widgets/chart_mixins/pattern_visualization_mixin.py*
  - [ ] Funktion: `draw_pattern_lines(pattern)`
  - [ ] Trendlinien als LineSeries
  - [ ] Support/Resistance als horizontale Linien
  - [ ] Neckline als gestrichelte Linie

- [ ] **7.2.3 Pattern-Marker**
  Status: ⬜ → *Datei: src/ui/widgets/chart_mixins/pattern_visualization_mixin.py*
  - [ ] Pivot-Punkte als Marker (Kreise/Dreiecke)
  - [ ] Breakout-Punkte als vertikale Linien
  - [ ] Pattern-Bounding-Box (semi-transparent)

- [ ] **7.2.4 Interaktive Pattern-Tooltips**
  Status: ⬜ → *Datei: src/ui/widgets/chart_js_template.html*
  - [ ] Hover über Pattern zeigt Details:
    - Pattern Type & Score
    - Geometrie-Kriterien
    - Confirmation Status
  - [ ] Click auf Pattern scrollt zu Details im Tab

- [ ] **7.2.5 Pattern Layer Management**
  Status: ⬜ → *Datei: src/ui/widgets/chart_mixins/pattern_visualization_mixin.py*
  - [ ] Funktion: `toggle_pattern_layer(pattern_type, visible)`
  - [ ] Einzelne Pattern-Kategorien ein/ausblenden
  - [ ] Cleanup: `remove_all_patterns()`

- [ ] **7.2.6 Tests**
  Status: ⬜ → *Datei: tests/ui/test_pattern_visualization.py*
  - [ ] Test: Pattern-Overlay wird korrekt gezeichnet
  - [ ] Test: Pattern-Update bei State-Change

---

## Phase 8: Pattern-Export für externe Systeme (4 Stunden)

**WICHTIG:** Dieses Modul liefert NUR Pattern-Daten. Trading Rules werden im separaten CEL-System implementiert!

### 8.1 Standardisierter Pattern-Export (4 Stunden)

- [ ] **8.1.1 JSON Export (CEL-kompatibel)**
  Status: ⬜ → *Datei: src/analysis/patterns/pattern_exporter.py*
  - [ ] Funktion: `export_patterns_json(patterns, filepath)`
  - [ ] **Standardisiertes Format für CEL-System:**
  ```json
  {
    "export_metadata": {
      "timestamp": "2026-01-19T14:30:00Z",
      "timeframe": "1D",
      "symbol": "BTCUSDT",
      "export_version": "1.0.0",
      "pattern_count": 42
    },
    "patterns": [
      {
        "pattern_id": "HNS_TOP_001",
        "type": "HEAD_AND_SHOULDERS_TOP",
        "category": "REVERSAL",
        "state": "CONFIRMED",
        "score": 87.5,
        "direction_bias": "DOWN",
        "start_time": "2026-01-10T00:00:00Z",
        "end_time": "2026-01-19T14:30:00Z",
        "start_index": 123,
        "end_index": 167,
        "pivots": [
          {"index": 123, "type": "HIGH", "price": 50000.0},
          {"index": 135, "type": "LOW", "price": 48000.0},
          {"index": 145, "type": "HIGH", "price": 52000.0},
          {"index": 155, "type": "LOW", "price": 47800.0},
          {"index": 167, "type": "HIGH", "price": 49900.0}
        ],
        "lines": {
          "neckline": [
            {"timestamp": "2026-01-12T00:00:00Z", "price": 48000.0},
            {"timestamp": "2026-01-17T00:00:00Z", "price": 47800.0}
          ],
          "support": [...],
          "resistance": [...]
        },
        "scoring_breakdown": {
          "geometry": 52.0,
          "context": 18.0,
          "confirmation": 17.5,
          "total": 87.5
        },
        "confirmation_details": {
          "breakout_confirmed": true,
          "volume_spike": true,
          "neckline_broken": true
        },
        "target_projection": {
          "downside_target": 45000.0,
          "target_distance_pct": 6.5
        }
      }
    ]
  }
  ```

- [ ] **8.1.2 Marktanalyse.json Integration (intern)**
  Status: ⬜ → *Datei: src/core/tradingbot/market_analyzer.py*
  - [ ] Erweitere `Marktanalyse.json` Schema (interne Verwendung):
  ```json
  "patterns": {
    "last_update": "2026-01-19T14:30:00Z",
    "pattern_count_by_category": {
      "reversal": 15,
      "continuation": 8,
      "smart_money": 12,
      "trend_following": 7
    },
    "active_patterns": [
      {
        "pattern_id": "HNS_TOP_001",
        "type": "HEAD_AND_SHOULDERS_TOP",
        "score": 87.5,
        "state": "CONFIRMED",
        "direction_bias": "DOWN"
      }
    ],
    "export_path": "exports/patterns/btcusdt_1d_20260119.json"
  }
  ```

- [ ] **8.1.3 CSV Export für Backtesting & Analysis**
  Status: ⬜ → *Datei: src/analysis/patterns/pattern_exporter.py*
  - [ ] Funktion: `export_patterns_csv(patterns, filepath)`
  - [ ] Spalten:
    ```
    timestamp, pattern_id, pattern_type, category, state, score,
    direction_bias, start_time, end_time, geometry_score, context_score,
    confirmation_score, breakout_confirmed, volume_spike,
    forward_5d_return, forward_10d_return, forward_20d_return
    ```

- [ ] **8.1.4 Real-time Pattern Stream (Optional)**
  Status: ⬜ → *Datei: src/analysis/patterns/pattern_streamer.py*
  - [ ] Funktion: `stream_pattern_updates(callback)`
  - [ ] WebSocket/Event-basiert für Live-Updates an externes CEL-System
  - [ ] Pattern State Changes (FORMING → CONFIRMED → FAILED)

- [ ] **8.1.5 Export API für externe Systeme**
  Status: ⬜ → *Datei: src/api/endpoints/patterns.py*
  - [ ] REST Endpoint: `GET /api/v1/patterns?symbol=BTCUSDT&timeframe=1D`
  - [ ] Response: JSON mit allen aktiven Patterns
  - [ ] Filter: `state=CONFIRMED`, `score_min=75`, `category=REVERSAL`

- [ ] **8.1.6 Export Validation & Schema**
  Status: ⬜ → *Datei: src/analysis/patterns/pattern_schema.py*
  - [ ] JSON Schema für Pattern-Export (Validation für CEL-System)
  - [ ] Pydantic Models für Type-Safety
  - [ ] Backward Compatibility (Versionierung)

---

## Phase 9: Testing & Optimization (10 Stunden)

### 9.1 Unit Tests (4 Stunden)

- [ ] **9.1.1 Pivot Engine Tests**
  Status: ⬜ → *Tests für alle Pivot-Detection-Funktionen*

- [ ] **9.1.2 Named Pattern Tests**
  Status: ⬜ → *Tests für H&S, Double Top, Triangles, Flags*

- [ ] **9.1.3 Smart Money Tests**
  Status: ⬜ → *Tests für Order Blocks, FVG, MSS*

- [ ] **9.1.4 Similarity Search Tests**
  Status: ⬜ → *Tests für DTW, Normalization, Forward Returns*

### 9.2 Integration Tests (3 Stunden)

- [ ] **9.2.1 End-to-End Pattern Detection**
  Status: ⬜ → *Test: BTCUSDT 1D Daten → Patterns → UI anzeigen*

- [ ] **9.2.2 Chart Overlay Tests**
  Status: ⬜ → *Test: Pattern-Linien werden korrekt gezeichnet*

- [ ] **9.2.3 CEL Integration Tests**
  Status: ⬜ → *Test: Pattern-Features in CEL-Regeln funktionieren*

### 9.3 Backtesting & Validation (3 Stunden)

- [ ] **9.3.1 Pattern Accuracy Backtest**
  Status: ⬜ → *Backtest: Forward Returns nach Pattern-Confirmation*
  - [ ] Head & Shoulders: Erwartung 89-93% Accuracy
  - [ ] Double Tops/Bottoms: Erwartung 85%+
  - [ ] Triangles: Erwartung 70-80%
  - [ ] Flags/Pennants: Erwartung 75-85%

- [ ] **9.3.2 Smart Money Backtest**
  Status: ⬜ → *Backtest: Order Block Retests, FVG Fills*

- [ ] **9.3.3 Similarity Search Validation**
  Status: ⬜ → *Walk-forward Test: Predictive Power von Similar Patterns*

---

## Phase 10: Documentation & Deployment (4 Stunden)

### 10.1 Documentation (2 Stunden)

- [ ] **10.1.1 Pattern Detection Guide**
  Status: ⬜ → *Datei: docs/analysis/Pattern_Detection_Guide.md*
  - [ ] Alle Pattern-Typen dokumentieren
  - [ ] Geometrie-Kriterien
  - [ ] Scoring-Komponenten
  - [ ] Beispiel-Charts

- [ ] **10.1.2 API Documentation**
  Status: ⬜ → *Datei: docs/api/Pattern_API.md*
  - [ ] Alle Public Functions
  - [ ] Parameter & Return Values
  - [ ] Code-Beispiele

- [ ] **10.1.3 User Guide**
  Status: ⬜ → *Datei: docs/user/Pattern_Recognition_User_Guide.md*
  - [ ] Entry Analyzer Tab nutzen
  - [ ] Pattern-Settings konfigurieren
  - [ ] Chart-Overlay interpretieren

### 10.2 Deployment (2 Stunden)

- [ ] **10.2.1 Merge to Main**
  Status: ⬜ → *Branch: feature/pattern-recognition → main*

- [ ] **10.2.2 Version Tag**
  Status: ⬜ → *Git Tag: v1.4.0-pattern-recognition*

- [ ] **10.2.3 Changelog**
  Status: ⬜ → *CHANGELOG.md Update*

- [ ] **10.2.4 Release Notes**
  Status: ⬜ → *GitHub Release mit Screenshots*

---

## 📈 Fortschritts-Tracking

### Gesamt-Statistik
- **Total Tasks:** 101
- **Abgeschlossen:** 0 (0%)
- **In Arbeit:** 0 (0%)
- **Offen:** 101 (100%)

### Phase-Statistik
| Phase | Tasks | Abgeschlossen | Fortschritt |
|-------|-------|---------------|-------------|
| Phase 0: Setup | 5 | 0 | ⬜ 0% |
| Phase 1: Foundation | 9 | 0 | ⬜ 0% |
| Phase 2: Reversal Patterns | 15 | 0 | ⬜ 0% |
| Phase 3: Continuation Patterns | 10 | 0 | ⬜ 0% |
| Phase 4: Smart Money | 12 | 0 | ⬜ 0% |
| Phase 5: Trend Following | 10 | 0 | ⬜ 0% |
| Phase 6: Similarity Search | 7 | 0 | ⬜ 0% |
| Phase 7: UI Integration | 12 | 0 | ⬜ 0% |
| Phase 8: Export API | 6 | 0 | ⬜ 0% |
| Phase 9: Testing | 10 | 0 | ⬜ 0% |
| Phase 10: Documentation | 6 | 0 | ⬜ 0% |

### Zeitschätzung
- **Geschätzte Gesamtzeit:** 92 Stunden (≈11.5 Arbeitstage à 8h)
- **Bereits investiert:** 0 Stunden
- **Verbleibend:** 92 Stunden

**Zeitersparnis durch Scope-Reduktion:** -2h (CEL-Integration entfällt, nur Export-API)

---

## 🔥 Kritische Pfade

### Woche 1 (Foundation)
1. **Pivot Engine** muss zuerst fertig sein (blockiert alle Pattern-Detektoren)
2. **Base Classes** parallel zu Pivot Engine entwickelbar
3. **Kritisch:** ZigZag-Performance (<200ms für Real-time)

### Woche 2 (Named Patterns)
1. **Reversal Patterns** vor Continuation Patterns
2. H&S und Double Top/Bottom priorisieren (höchste Accuracy)
3. **Kritisch:** Scoring-System muss kalibriert werden (Backtests!)

### Woche 3 (Smart Money & Trend Following)
1. **Smart Money** und **Trend Following** parallel entwickelbar
2. **Kritisch:** Order Block Validation = Key für SMC Trading

### Woche 4 (Similarity Search & UI)
1. **DTW Performance** optimieren (<2s für 1000 Fenster)
2. **UI Integration** parallel zu DTW-Entwicklung
3. **Kritisch:** Chart-Overlay muss ohne Performance-Einbruch laufen

---

## 📝 Notizen & Risiken

### Aktuelle Blocker
- Keine bekannten Blocker

### Identifizierte Risiken
1. **ZigZag False Positives** - Zu viele oder zu wenige Pivots bei extremer Volatilität
2. **Pattern Over-Fitting** - Zu strikte Kriterien = kaum Detections
3. **DTW Performance** - Langsam bei großen Datensets (>10.000 Bars)
4. **UI Rendering** - Zu viele Pattern-Overlays = Chart-Lag
5. **False Signals** - Patterns ohne Forward Returns = Trading-Verluste

### Mitigation Strategies
1. **Adaptive ZigZag** - ATR-basiert statt fixer Prozent-Threshold
2. **Scoring Calibration** - Backtests für Threshold-Tuning (Score >75 = Trade-worthy)
3. **DTW Pre-Filter** - Correlation vor DTW (99% Kandidaten ausfiltern)
4. **Lazy Rendering** - Nur sichtbarer Chart-Bereich mit Patterns
5. **Walk-Forward Validation** - Out-of-Sample Testing vor Live-Deployment

---

## 🎯 Qualitätsziele

### Performance Targets
- **Pivot Detection:** <200ms für 1000 Bars (Real-time fähig)
- **Pattern Detection:** <500ms für alle Named Patterns
- **Similarity Search:** <2s für DTW auf 1000 historischen Fenstern
- **Chart Overlay:** <100ms Rendering (keine sichtbare Verzögerung)

### Accuracy Targets (basierend auf Research)
- **Head & Shoulders:** >89% Accuracy bei Confirmation
- **Double Tops/Bottoms:** >85% Accuracy
- **Triangles:** >70% Breakout Success Rate
- **Flags/Pennants:** >75% Continuation Rate
- **Smart Money:** >60% Order Block Retest Success

### Code Quality Targets
- **Code Coverage:** >85%
- **Dokumentation:** 100% Public API dokumentiert
- **Tests:** Alle Pattern-Detektoren + Edge Cases

---

## 📄 Review Checkpoints

### End of Week 1 (Foundation Complete)
- [ ] Pivot Engine funktional & getestet
- [ ] Base Classes & Pattern Interface vollständig
- [ ] Erste Pattern-Detektoren (H&S, Double Top) prototypisch funktionsfähig

### End of Week 2 (Named Patterns Complete)
- [ ] Alle Reversal Patterns (H&S, Double Top/Bottom, Triple Top/Bottom)
- [ ] Alle Continuation Patterns (Triangles, Flags, Pennants)
- [ ] Backtest-Ergebnisse für Reversal Patterns vorliegen

### End of Week 3 (SMC & Trend Following Complete)
- [ ] Smart Money Concepts vollständig (Order Blocks, FVG, MSS)
- [ ] Trend Following Patterns vollständig (Channels, Breakouts)
- [ ] Integration in Marktanalyse.json

### End of Week 4 (UI & Export Complete)
- [ ] Similarity Search funktional
- [ ] Entry Analyzer Tab vollständig
- [ ] Chart Overlay funktioniert
- [ ] Export-API funktional (JSON/CSV/WebSocket)
- [ ] Alle Tests passed (>85% Coverage)
- [ ] **Schnittstelle zu CEL-System dokumentiert**

---

## 📚 Quellen & Best Practices (Websearch 2026-01-19)

### Chart Pattern Recognition

**Best Practice Artikel 2025:**
- [VT Markets: Chart Patterns Cheat Sheet 2025](https://www.vtmarkets.com/discover/chart-patterns-cheat-sheet-2025-stock-trading-patterns-guide/)
- [VT Markets: Chart Patterns Guide 2025](https://www.vtmarkets.com/discover/chart-patterns-guide-2025/)
- [VPFX: 45 Must-Know Chart Patterns](https://www.vpfx.net/chart-patterns-for-trader/)
- [PipTrend: 10 Best Trading Chart Patterns](https://piptrend.com/trading-chart-pattern/)

**Key Insights:**
- Head & Shoulders: **89-93% Accuracy** bei Volume-Bestätigung
- Hybrid Approach (ML + Rules) = optimal für 2025
- AI/ML verbessert Accuracy durch kontinuierliches Lernen

**Pattern Recognition Tools:**
- [Liberated Stock Trader: Top 5 Pattern Recognition Tools 2025](https://www.liberatedstocktrader.com/candlestick-pattern-analysis-recognition-software/)
- TradingView, FinViz, TrendSpider haben leistungsstarke Algorithmen
- TrendSpider: Automatische Erkennung von 150+ Candlestick Patterns

### Smart Money Concepts (SMC)

**ICT Trading Guides:**
- [XS: Smart Money Concepts Complete Guide](https://www.xs.com/en/blog/smart-money-concept/)
- [ATAS: What Is Smart Money Concept](https://atas.net/technical-analysis/what-is-the-smart-money-concept-and-how-does-the-ict-trading-strategy-work/)
- [GitHub: Smart Money Concepts Python Package](https://github.com/joshyattridge/smart-money-concepts)
- [Liquidity Provider: ICT Trading Explained](https://liquidity-provider.com/articles/ict-tradingexplained/)

**Key Concepts:**
- **Order Blocks:** Regionen mit hohen institutionellen Orders
- **Fair Value Gaps (FVG):** 3-Candle Pattern für Market Imbalance
- **Market Structure Shift (MSS):** BOS, CHoCH als Trend-Umkehr-Signale

### Trend Following & Breakouts

**Algorithmic Implementation:**
- [TrendSpider: Breakout Detection](https://help.trendspider.com/kb/automated-technical-analysis/breakout-detection)
- [TradingView: Algorithmic Pattern Identification](https://www.tradingview.com/chart/US100/oDKIENQa-Algorithmic-Identification-and-Classification-of-Chart-Patterns/)
- [uTrade Algos: Chart Patterns for Breakouts](https://www.utradealgos.com/blog/how-to-use-chart-patterns-to-identify-breakouts-and-breakdowns)

**Key Strategies:**
- **ATR Channel Breakout:** Dynamische Channels basierend auf ATR
- **Donchian Breakout:** Turtle Trading Style (Highest High/Lowest Low)
- **Bollinger Breakout:** Volatility-basierte Squeeze & Expansion

### Python Libraries

**Recommended Libraries:**
- [GitHub: PatternPy](https://github.com/keithorange/PatternPy) - High-Speed Pattern Recognition mit Pandas/Numpy
- [Medium: Algorithmically Detecting Chart Patterns](https://medium.com/automation-generation/algorithmically-detecting-and-trading-technical-chart-patterns-with-python-c577b3a396ed)
- [GitHub: stock-pattern CLI Tool](https://github.com/BennyThadikaran/stock-pattern)

**Key Approaches:**
- **Scipy-based:** `scipy.signal.argrelextrema` für Pivot Detection
- **TA-Lib:** 200+ Technical Indicators, 60+ Candlestick Patterns
- **Deep Learning:** YOLOv8 für Chart Pattern Detection (ChartScanAI)

---

## 🚀 Nächste Schritte

1. **User-Feedback einholen:**
   - Priorisierung bestätigen (welche Patterns zuerst?)
   - UI-Design für Entry Analyzer Tab besprechen
   - Smart Money Concepts: Wie wichtig? (Order Blocks vs. klassische Patterns)

2. **Implementation starten:**
   - Phase 0: Setup (2h)
   - Phase 1: Pivot Engine (4h)
   - Phase 2: Head & Shoulders (4h) → First Milestone!

3. **Testing & Iteration:**
   - Unit-Tests für Pivot Engine
   - Backtest für H&S mit BTCUSDT 1D Daten
   - Forward Returns validieren (89%+ Accuracy?)

**Geschätzter Aufwand bis First Milestone (H&S funktional):**
- Setup + Pivot Engine + H&S = **10 Stunden** (1.5 Arbeitstage)
- **Deliverable:** H&S Pattern im Entry Analyzer sichtbar, Score >85, Chart-Overlay

---

**Letzte Aktualisierung:** 2026-01-19
**Nächste Review:** Nach Phase 1 Completion (Pivot Engine & Base Classes)
