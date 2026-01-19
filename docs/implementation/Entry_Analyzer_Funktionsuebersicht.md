# Entry Analyzer - Detaillierte Funktionsübersicht (Umgestzt in der APP Orderpilot-AI)

**Version:** 1.0
**Stand:** 2026-01-19
**Autor:** OrderPilot-AI Development Team

---

## Inhaltsverzeichnis

1. [Workflow-Übersicht](#1-workflow-übersicht)
2. [Regime-Erkennung](#2-regime-erkennung)
3. [Indikator-Testing](#3-indikator-testing)
4. [Strategie-Testing und -Erstellung](#4-strategie-testing-und--erstellung)
5. [Trading Bot Integration](#5-trading-bot-integration)
6. [CEL Skript Implementierung - Aktueller Stand](#6-cel-skript-implementierung---aktueller-stand)

---

## 1. Workflow-Übersicht

### 1.1 Entry Analyzer Hauptfunktion

**Zweck:** Analyse von Marktdaten zur optimalen Entry-Punkt-Identifikation

**Hauptkomponenten:**
- **UI-Dialog:** `src/ui/dialogs/entry_analyzer_popup.py`
- **Analyse-Engine:** `src/analysis/visible_chart/`
- **Regime-Engine (Legacy):** `src/core/tradingbot/regime_engine.py` ⚠️ DEPRECATED
- **Regime-Engine (JSON):** `src/core/tradingbot/regime_engine_json.py` ✅ AKTIV
- **Indikator-Engine:** `src/core/indicators/engine.py`

### 1.2 Workflow-Ablauf (Workflow-Diagramm)

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. DATENBESCHAFFUNG                                              │
│    ├─ Sichtbarer Chart-Bereich (Zeitraum/Timeframe)            │
│    ├─ OHLCV-Daten aus Datenbank laden                          │
│    └─ Optional: Erweiterte Zeiträume für Backtesting           │
└──────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ 2. INDIKATOR-BERECHNUNG                                         │
│    ├─ Basis-Indikatoren (SMA, EMA, RSI, MACD, ADX, ATR, etc.)  │
│    ├─ Composite-Indikatoren (MOMENTUM_SCORE, VOLUME_RATIO,     │
│    │                           PRICE_STRENGTH)                   │
│    └─ Feature-Vector Erstellung                                 │
└──────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ 3. REGIME-ERKENNUNG (JSON-basiert)                              │
│    ├─ JSON-Config laden (z.B. regime_based_comprehensive.json) │
│    ├─ Bedingungen evaluieren (ConditionEvaluator)              │
│    ├─ Aktive Regimes identifizieren                            │
│    │   • Extreme Uptrend/Downtrend                             │
│    │   • Strong Uptrend/Downtrend                              │
│    │   • Moderate Uptrend/Downtrend                            │
│    │   • Range-Bound Market                                    │
│    │   • High/Low Volatility                                   │
│    └─ Regime-State zurückgeben (mit Confidence-Scores)         │
└──────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ 4. STRATEGIE-ROUTING                                            │
│    ├─ StrategyRouter: Regime → Strategy Set Mapping            │
│    │   • all_of: Alle Regimes müssen aktiv sein               │
│    │   • any_of: Mindestens ein Regime aktiv                  │
│    │   • none_of: Regimes dürfen NICHT aktiv sein             │
│    ├─ Strategy Set Selection                                    │
│    └─ Parameter-Overrides anwenden (falls definiert)           │
└──────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ 5. ENTRY-SIGNAL-GENERIERUNG                                     │
│    ├─ Entry-Bedingungen evaluieren (pro Strategie)             │
│    ├─ Exit-Bedingungen evaluieren                              │
│    ├─ Risk-Management Parameter anwenden                        │
│    │   • Position Size                                          │
│    │   • Stop Loss %                                            │
│    │   • Take Profit %                                          │
│    │   • Trailing Stop Settings                                │
│    └─ Entry-Score berechnen (EntryScorer)                      │
└──────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ 6. BACKTESTING (Optional)                                        │
│    ├─ BacktestEngine: Multi-Timeframe Simulation               │
│    ├─ Trade-Simulation mit Entry/Exit-Logik                    │
│    ├─ Performance-Metriken berechnen                           │
│    │   • Net Profit                                             │
│    │   • Win Rate                                               │
│    │   • Profit Factor                                          │
│    │   • Sharpe Ratio                                           │
│    │   • Max Drawdown                                           │
│    └─ Walk-Forward Validation (für Robustness)                 │
└──────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ 7. AI COPILOT ANALYSE (Optional)                                │
│    ├─ LLM-basierte Entry-Analyse (via Claude API)              │
│    ├─ Natürlichsprachige Empfehlungen                          │
│    ├─ Risiko-Assessment                                         │
│    └─ Trade-Rationale Erklärung                                │
└──────────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│ 8. VISUALISIERUNG & REPORTING                                   │
│    ├─ Entry-Signale auf Chart zeichnen                         │
│    ├─ Regime-Boundaries als vertikale Linien                   │
│    ├─ Performance-Tabellen                                      │
│    ├─ Trade-Liste mit Details                                  │
│    └─ PDF-Report Export (optional)                             │
└──────────────────────────────────────────────────────────────────┘
```

### 1.3 Tab-Struktur im Entry Analyzer Dialog

**Tab 1: Backtest Setup**
- JSON Strategy Config Loader
- Symbol Selection (Dropdown)
- Date Range Picker (Start/End Date)
- Initial Capital Input (Spinbox)
- "Run Backtest" Button

**Tab 2: Visible Range Analysis**
- Aktuelle Chart-Bereich Analyse
- Entry-Signale für sichtbaren Zeitraum
- Real-time Regime Display
- Quick Action Buttons

**Tab 3: Backtest Results**
- Performance Summary (Net Profit, Win Rate, etc.)
- Trade List (Tabelle mit allen Trades)
- Equity Curve (optional)
- Regime Distribution Chart

**Tab 4: AI Copilot**
- LLM-basierte Analyse des aktuellen Marktregimes
- Entry-Empfehlungen mit Rationale
- Risk Assessment
- Alternative Strategien-Vorschläge

**Tab 5: Validation**
- Walk-Forward Validation Ergebnisse
- Out-of-Sample Performance
- Robustness Metrics
- Overfitting Detection

### 1.4 Footer Actions

- **🔄 Analyze Visible Range:** Analysiere aktuellen Chart-Bereich
- **📄 Generate Report:** PDF-Report mit allen Analysen
- **📍 Draw on Chart:** Zeichne Regime-Grenzen und Entry-Signale
- **🗑️ Clear Entries:** Lösche alle Chart-Markierungen
- **Close:** Dialog schließen

---

## 2. Regime-Erkennung

### 2.1 Architektur-Überblick

**Legacy Regime Engine (⚠️ DEPRECATED):**
- Hardcodierte Schwellenwerte in `regime_engine.py`
- Fest definierte Regime-Typen (TREND_UP, TREND_DOWN, RANGE)
- Fest definierte Volatilitäts-Level (LOW, NORMAL, HIGH, EXTREME)
- Nicht konfigurierbar → wird ersetzt

**JSON-basierte Regime Engine (✅ AKTIV):**
- Vollständig konfigurierbar via JSON-Dateien
- Beliebige Anzahl von Regimes definierbar
- Flexible Bedingungslogik (AND/OR/NESTED)
- Prioritäts-basierte Regime-Auswahl
- Scope-basierte Filterung (entry/exit/in_trade)

### 2.2 JSON Regime Configuration Schema

**Datei:** `03_JSON/schema/strategy_config_schema.json`

**Struktur:**
```json
{
  "schema_version": "1.0.0",
  "indicators": [
    {
      "id": "momentum_score",
      "type": "MOMENTUM_SCORE",
      "params": { "sma_fast": 20, "sma_slow": 50 }
    },
    {
      "id": "volume_ratio",
      "type": "VOLUME_RATIO",
      "params": { "period": 20 }
    }
  ],
  "regimes": [
    {
      "id": "extreme_downtrend",
      "name": "Extreme Downtrend",
      "priority": 100,
      "scope": "entry",
      "conditions": {
        "all": [
          {
            "left": { "indicator_id": "price_strength", "field": "value" },
            "op": "lt",
            "right": { "value": -4.0 }
          },
          {
            "left": { "indicator_id": "volume_ratio", "field": "value" },
            "op": "gt",
            "right": { "value": 2.0 }
          }
        ]
      }
    }
  ],
  "strategies": [...],
  "strategy_sets": [...],
  "routing": [...]
}
```

### 2.3 Verfügbare Regime-Typen (Beispiele aus regime_based_comprehensive.json)

**Trend-Regimes:**
1. **Extreme Uptrend**
   - Bedingung: `PRICE_STRENGTH > 4.0 AND VOLUME_RATIO > 2.0`
   - Priority: 100
   - Typische Strategie: Momentum Long (aggressive Entry)

2. **Strong Uptrend**
   - Bedingung: `PRICE_STRENGTH between 2.0 and 4.0 AND MOMENTUM_SCORE > 2.0`
   - Priority: 80
   - Typische Strategie: Trend Following Long

3. **Moderate Uptrend**
   - Bedingung: `MOMENTUM_SCORE between 0.5 and 2.0 AND RSI > 50`
   - Priority: 60
   - Typische Strategie: Conservative Trend Following

4. **Extreme Downtrend**
   - Bedingung: `PRICE_STRENGTH < -4.0 AND VOLUME_RATIO > 2.0`
   - Priority: 100
   - Typische Strategie: Momentum Short (aggressive Entry)

5. **Strong Downtrend**
   - Bedingung: `PRICE_STRENGTH between -4.0 and -2.0 AND MOMENTUM_SCORE < -2.0`
   - Priority: 80
   - Typische Strategie: Trend Following Short

6. **Moderate Downtrend**
   - Bedingung: `MOMENTUM_SCORE between -2.0 and -0.5 AND RSI < 50`
   - Priority: 60
   - Typische Strategie: Conservative Trend Following Short

**Range-Regimes:**
7. **Range-Bound Market**
   - Bedingung: `MOMENTUM_SCORE between -0.5 and 0.5 AND CHOP > 61.8 AND VOLUME_RATIO < 1.2`
   - Priority: 50
   - Typische Strategie: Mean Reversion (RSI/BB-based)

**Volatilitäts-Regimes:**
8. **High Volatility**
   - Bedingung: `VOLUME_RATIO > 2.5 OR BB_WIDTH > 0.15`
   - Priority: 70
   - Anpassung: Weitere Stops, kleinere Positionen

9. **Low Volatility**
   - Bedingung: `VOLUME_RATIO < 0.8 AND BB_WIDTH < 0.05`
   - Priority: 40
   - Anpassung: Engere Stops, potentiell größere Positionen

### 2.4 Composite Indicators für Regime-Detection

**MOMENTUM_SCORE:**
- Berechnung: `(SMA_fast - SMA_slow) / SMA_slow * 100 * 0.6 + (Close - SMA_fast) / SMA_fast * 100 * 0.4`
- Interpretation:
  - `> 2.0`: Starker Aufwärtstrend
  - `0.5 to 2.0`: Moderater Aufwärtstrend
  - `-0.5 to 0.5`: Seitwärtsmarkt
  - `-2.0 to -0.5`: Moderater Abwärtstrend
  - `< -2.0`: Starker Abwärtstrend

**VOLUME_RATIO:**
- Berechnung: `Current_Volume / SMA(Volume, 20)`
- Interpretation:
  - `> 2.0`: Sehr hohes Volumen (Breakout-Kandidat)
  - `1.2 to 2.0`: Erhöhtes Volumen
  - `0.8 to 1.2`: Normales Volumen
  - `< 0.8`: Niedriges Volumen (Range-Phase)

**PRICE_STRENGTH:**
- Composite aus:
  - Momentum Score (Gewichtung: 0.35)
  - Volume Ratio (Gewichtung: 0.30)
  - RSI Position (Gewichtung: 0.20)
  - Bollinger Band Position (Gewichtung: 0.15)
- Interpretation:
  - `> 4.0`: Extreme Stärke (Euphorie-Phase)
  - `2.0 to 4.0`: Starke Bewegung
  - `-2.0 to 2.0`: Neutrale Phase
  - `-4.0 to -2.0`: Starke Schwäche
  - `< -4.0`: Extreme Schwäche (Panik-Phase)

### 2.5 Regime-Detection Workflow (Technisch)

**Implementierung:** `src/core/tradingbot/regime_engine_json.py`

**Ablauf:**
```python
# 1. Config laden
config = ConfigLoader().load_config("regime_based_comprehensive.json")

# 2. Indikatoren berechnen (aus DataFrame)
indicator_values = self._calculate_indicators(data, config)
# Ergebnis: {"momentum_score": {"value": 1.5}, "volume_ratio": {"value": 1.3}, ...}

# 3. Regimes evaluieren
detector = RegimeDetector(config.regimes)
active_regimes = detector.detect_active_regimes(indicator_values, scope="entry")
# Ergebnis: [RegimeMatch(regime_id="moderate_uptrend", confidence=0.85, priority=60)]

# 4. Zu RegimeState konvertieren (für Legacy-Kompatibilität)
regime_state = self._convert_to_regime_state(active_regimes, indicator_values)
# Ergebnis: RegimeState(regime=RegimeType.TREND_UP, volatility=VolatilityLevel.NORMAL, ...)
```

**Condition Evaluation (rekursiv):**
```python
# Beispiel: "all" Condition Group
{
  "all": [
    {"left": {"indicator_id": "rsi", "field": "value"}, "op": "gt", "right": {"value": 50}},
    {"left": {"indicator_id": "macd", "field": "histogram"}, "op": "gt", "right": {"value": 0}},
    {
      "any": [  # Nested condition group!
        {"left": {"indicator_id": "volume_ratio", "field": "value"}, "op": "gt", "right": {"value": 1.5}},
        {"left": {"indicator_id": "atr_pct", "field": "value"}, "op": "gt", "right": {"value": 1.0}}
      ]
    }
  ]
}
```

### 2.6 Regime-Change Detection

**Zweck:** Erkennung signifikanter Regime-Wechsel für Position-Anpassungen

**Implementierung:** `RegimeEngine.detect_regime_change()`

**Kriterien:**
- Regime-Typ-Wechsel (z.B. TREND_UP → RANGE)
- Volatilitäts-Level-Wechsel (z.B. NORMAL → HIGH)
- Confidence-Score-Abfall > 30%

**Use Case:** Trading Bot stoppt aktive Strategie und wechselt zu neuer

---

## 3. Indikator-Testing

### 3.1 Verfügbare Indikatoren

#### 3.1.1 Overlay-Indikatoren (auf Preis-Chart)

**Moving Averages:**
- **SMA** (Simple Moving Average)
  - Parameter: `period` (default: 20)
  - Display: `SMA(20)`
  - Use Case: Trend-Identifikation, Support/Resistance

- **EMA** (Exponential Moving Average)
  - Parameter: `period` (default: 20)
  - Display: `EMA(20)`
  - Use Case: Schnellere Trend-Reaktion als SMA

- **WMA** (Weighted Moving Average)
  - Parameter: `period` (default: 20)
  - Display: `WMA(20)`
  - Use Case: Gewichtung aktueller Preise

- **VWMA** (Volume Weighted Moving Average)
  - Parameter: `period` (default: 20)
  - Display: `VWMA(20)`
  - Use Case: Volumen-gewichteter Durchschnitt

**Bands & Channels:**
- **BB** (Bollinger Bands)
  - Parameter: `period` (default: 20), `std` (default: 2)
  - Display: `BB(20,2)`
  - Felder: `upper`, `middle`, `lower`, `width`, `percent`
  - Use Case: Volatilitäts-Bänder, Überkauft/Überverkauft

- **KC** (Keltner Channel)
  - Parameter: `period` (default: 20), `mult` (default: 1.5)
  - Display: `KC(20,1.5)`
  - Use Case: Trend-Kanal mit ATR-basierter Breite

**Trend-Following:**
- **PSAR** (Parabolic SAR)
  - Parameter: `af` (default: 0.02), `max_af` (default: 0.2)
  - Display: `PSAR`
  - Use Case: Stop-and-Reverse Signale

- **ICHIMOKU** (Ichimoku Cloud)
  - Parameter: `tenkan` (9), `kijun` (26), `senkou` (52)
  - Display: `Ichimoku`
  - Use Case: Trend, Momentum, Support/Resistance

**Volume Overlay:**
- **VWAP** (Volume Weighted Average Price)
  - Parameter: keine
  - Display: `VWAP`
  - Use Case: Intraday Fair-Value-Referenz

#### 3.1.2 Oscillator-Indikatoren (separate Panels)

**Momentum:**
- **RSI** (Relative Strength Index)
  - Parameter: `period` (default: 14)
  - Display: `RSI(14)`
  - Range: 0-100
  - Referenzlinien: 30 (Oversold), 50 (Neutral), 70 (Overbought)
  - Use Case: Überkauft/Überverkauft, Divergenzen

- **MACD** (Moving Average Convergence Divergence)
  - Parameter: `fast` (12), `slow` (26), `signal` (9)
  - Display: `MACD(12,26,9)`
  - Felder: `macd`, `signal`, `histogram`
  - Use Case: Trend-Momentum, Crossovers

- **STOCH** (Stochastic Oscillator)
  - Parameter: `k_period` (14), `d_period` (3)
  - Display: `STOCH(14,3)`
  - Range: 0-100
  - Referenzlinien: 20 (Oversold), 80 (Overbought)
  - Use Case: Überkauft/Überverkauft

- **CCI** (Commodity Channel Index)
  - Parameter: `period` (default: 20)
  - Display: `CCI(20)`
  - Range: -200 bis +200
  - Referenzlinien: -100, 0, +100
  - Use Case: Trend-Stärke, Überkauft/Überverkauft

- **MFI** (Money Flow Index)
  - Parameter: `period` (default: 14)
  - Display: `MFI(14)`
  - Range: 0-100
  - Use Case: Volumen-gewichtete RSI-Alternative

- **MOM** (Momentum)
  - Parameter: `period` (default: 10)
  - Display: `MOM(10)`
  - Use Case: Rate-of-Change Messung

- **ROC** (Rate of Change)
  - Parameter: `period` (default: 10)
  - Display: `ROC(10)`
  - Use Case: Prozentuale Preis-Änderung

- **WILLR** (Williams %R)
  - Parameter: `period` (default: 14)
  - Display: `Williams %R(14)`
  - Range: -100 bis 0
  - Use Case: Überkauft/Überverkauft

**Trend-Stärke:**
- **ADX** (Average Directional Index)
  - Parameter: `period` (default: 14)
  - Display: `ADX(14)`
  - Range: 0-100
  - Interpretation:
    - `> 40`: Starker Trend
    - `25-40`: Trend etabliert
    - `< 20`: Range/Choppy
  - Use Case: Trend-Stärke (ohne Richtung)

**Volatilität:**
- **ATR** (Average True Range)
  - Parameter: `period` (default: 14)
  - Display: `ATR(14)`
  - Use Case: Absolute Volatilitäts-Messung

- **NATR** (Normalized ATR)
  - Parameter: `period` (default: 14)
  - Display: `NATR(14)`
  - Use Case: ATR als % vom Preis

- **STD** (Standard Deviation)
  - Parameter: `period` (default: 20)
  - Display: `StdDev(20)`
  - Use Case: Statistische Volatilität

- **BB_WIDTH** (Bollinger Band Width)
  - Parameter: `period` (20), `std` (2)
  - Display: `BB Width`
  - Use Case: Squeeze/Expansion Detection

- **BB_PERCENT** (%B)
  - Parameter: `period` (20), `std` (2)
  - Display: `%B`
  - Range: 0-1.2
  - Use Case: Position innerhalb der BB-Bänder

**Volumen:**
- **OBV** (On-Balance Volume)
  - Parameter: keine
  - Display: `OBV`
  - Use Case: Volumen-Flow-Analyse

- **CMF** (Chaikin Money Flow)
  - Parameter: `period` (default: 20)
  - Display: `CMF(20)`
  - Range: -1 bis +1
  - Use Case: Kauf-/Verkaufsdruck

- **AD** (Accumulation/Distribution Line)
  - Parameter: keine
  - Display: `A/D Line`
  - Use Case: Volumen-gewichtete Akkumulation

- **FI** (Force Index)
  - Parameter: `period` (default: 13)
  - Display: `Force Index(13)`
  - Use Case: Kauf-/Verkaufs-Kraft

#### 3.1.3 Composite Indicators (JSON-basiert)

**MOMENTUM_SCORE:**
- Berechnung: Gewichteter Durchschnitt aus SMA-Crossover und Price-Distance
- Parameter: `sma_fast`, `sma_slow`, `use_price_distance`
- Use Case: Regime-Detection, Entry-Filtering

**VOLUME_RATIO:**
- Berechnung: `Volume / SMA(Volume, period)`
- Parameter: `period`, `smoothing`
- Use Case: Volumen-Anomalien, Breakout-Bestätigung

**PRICE_STRENGTH:**
- Berechnung: Composite aus Momentum, Volume, RSI, BB
- Parameter: `sma_fast`, `sma_slow`, `volume_period`, `rsi_period`, `bb_period`, Gewichtungen
- Use Case: Comprehensive Market Strength Assessment

### 3.2 Indikator-Testing Workflow (Geplant)

**Phase 1: Single Indicator Testing**
- Parameter-Range-Testing (z.B. RSI(10), RSI(12), RSI(14), RSI(16), RSI(18), RSI(20))
- Backtest pro Parameter-Set
- Score-Berechnung (Win Rate, Profit Factor, Sharpe)
- Ranking nach Performance

**Phase 2: Multi-Indicator Optimization**
- Kombination bester Indikatoren pro Regime
- Gewichtungs-Optimierung
- Overfitting-Prevention (Walk-Forward Validation)

**Phase 3: Regime-Set Creation**
- Bündeln optimaler Indikatoren pro Regime
- JSON-Config-Generierung
- Backtest des kompletten Regime-Sets

**Status:** ⚠️ NICHT IMPLEMENTIERT - UI-Verdrahtung fehlt (siehe Plan in Plan-Datei)

---

## 4. Strategie-Testing und -Erstellung

### 4.1 JSON Strategy Configuration

**Hauptkomponenten:**
1. **Indicators:** Liste aller verwendeten Indikatoren mit Parametern
2. **Regimes:** Definitionen der Marktphasen mit Aktivierungsbedingungen
3. **Strategies:** Entry/Exit-Regeln und Risikoparameter
4. **Strategy Sets:** Bündel von Strategien mit Overrides
5. **Routing:** Zuordnung von Regime-Kombinationen zu Strategy Sets

### 4.2 Beispiel: Trend Following Strategy (JSON)

```json
{
  "id": "trend_following_long",
  "name": "Trend Following Long",
  "entry": {
    "all": [
      {
        "left": {"indicator_id": "momentum_score", "field": "value"},
        "op": "gt",
        "right": {"value": 2.0}
      },
      {
        "left": {"indicator_id": "volume_ratio", "field": "value"},
        "op": "gt",
        "right": {"value": 1.2}
      }
    ]
  },
  "exit": {
    "any": [
      {
        "left": {"indicator_id": "momentum_score", "field": "value"},
        "op": "lt",
        "right": {"value": 0.5}
      }
    ]
  },
  "risk": {
    "position_size": 0.025,
    "stop_loss_pct": 2.5,
    "take_profit_pct": 5.0,
    "trailing_mode": "atr",
    "trailing_multiplier": 2.0
  }
}
```

### 4.3 Strategy Testing Workflow

**1. Backtest Setup (Tab 1)**
- JSON-Config auswählen (File-Picker)
- Symbol wählen (z.B. BTCUSDT)
- Zeitraum festlegen (Start/End Date)
- Initial Capital (default: 10000 USDT)
- "Run Backtest" Button → BacktestEngine starten

**2. Backtest Execution**
- Thread-basierte Ausführung (nicht blockierend)
- Progress-Bar zeigt Fortschritt
- Multi-Timeframe-Daten werden geladen
- Indikatoren werden berechnet (IndicatorEngine)
- Regimes werden evaluiert (RegimeDetector)
- Strategies werden geroutet (StrategyRouter)
- Trades werden simuliert (Entry/Exit-Logik)

**3. Performance-Metriken (Tab 3)**
- **Net Profit:** Gesamtgewinn in USDT und %
- **Win Rate:** Prozentsatz gewinnender Trades
- **Profit Factor:** Gross Profit / Gross Loss
- **Sharpe Ratio:** Risk-adjusted Return
- **Max Drawdown:** Größter Rückgang vom Peak
- **Total Trades:** Anzahl ausgeführter Trades
- **Average Trade:** Durchschnittlicher Gewinn/Verlust pro Trade

**4. Trade-Liste (Tab 3)**
- Tabellarische Auflistung aller Trades
- Spalten:
  - Entry Date/Time
  - Exit Date/Time
  - Side (LONG/SHORT)
  - Entry Price
  - Exit Price
  - P&L (USDT)
  - P&L (%)
  - Strategy Used
  - Regime at Entry

### 4.4 Strategy Set Builder (Geplant)

**Funktion:** Automatische Erstellung optimaler Strategy Sets pro Regime

**Workflow:**
1. Indikator-Optimization ausführen
2. Top N Indikatoren pro Regime identifizieren
3. Gewichtungen berechnen (Score-basiert)
4. JSON-Config generieren
5. Backtest des kompletten Regime-Sets
6. Vergleich mit Single-Indicator-Performance

**Status:** ⚠️ NICHT IMPLEMENTIERT - UI-Verdrahtung fehlt

### 4.5 Walk-Forward Validation (Tab 5)

**Zweck:** Overfitting-Detection und Out-of-Sample Performance

**Methode:**
1. Training Window: 70% der Daten
2. Testing Window: 30% der Daten
3. Rolling-Window-Ansatz (z.B. monatlich)
4. Performance-Vergleich In-Sample vs. Out-of-Sample

**Metriken:**
- In-Sample Performance
- Out-of-Sample Performance
- Degradation Factor (Out-of-Sample / In-Sample)
- Robustness Score (0-100)

**Status:** ✅ IMPLEMENTIERT (aber UI-Anbindung pending)

---

## 5. Trading Bot Integration

### 5.1 BotController JSON Integration

**Implementierung:** `src/core/tradingbot/bot_controller.py`

**Hauptfunktionen:**
```python
class BotController:
    def _load_json_config(self, config_path: str) -> TradingBotConfig:
        """Load and validate JSON strategy configuration."""
        return ConfigLoader().load_config(config_path)

    def _on_new_bar(self, bar_data: dict):
        """Process new bar and check for regime changes."""
        # 1. Calculate indicators
        features = self.feature_engine.process_bar(bar_data)

        # 2. Detect current regime (JSON-based)
        indicator_values = IndicatorValueCalculator().calculate(features)
        active_regimes = self.regime_detector.detect_active_regimes(indicator_values)

        # 3. Route to strategy
        matched_set = self.strategy_router.route(active_regimes)

        # 4. Check for regime change
        if self._has_regime_changed(active_regimes):
            self._switch_strategy(matched_set)

        # 5. Evaluate entry/exit conditions
        if matched_set:
            entry_signal = self._evaluate_entry_conditions(matched_set, indicator_values)
            exit_signal = self._evaluate_exit_conditions(matched_set, indicator_values)
```

### 5.2 Start Bot Workflow (UI)

**Schritt 1: Strategy Selection Dialog**
- "Start Bot" Button → StrategySettingsDialog öffnen
- JSON-Config auswählen (File-Picker)
- "Analyze Current Market" Button → Aktuelles Regime erkennen
- Display: Matched Strategy mit Entry/Exit-Conditions
- "Apply Strategy" Button → Bot startet mit gewählter Config

**Schritt 2: Bot Initialization**
```python
# In bot_ui_control_widgets.py
def _on_bot_start_clicked(self):
    dialog = StrategySettingsDialog(self)
    if dialog.exec_() == QDialog.Accepted:
        config_path = dialog.config_file_input.text()
        matched_set = dialog.matched_strategy_set

        self.bot_controller.set_json_config(config_path)
        self.bot_controller.set_initial_strategy(matched_set)
        self.bot_controller.start()
```

**Schritt 3: Dynamic Strategy Switching**
- Bot überwacht Regime-Änderungen in Echtzeit
- Bei Regime-Wechsel: Automatische Umschaltung zu neuer Strategy
- UI-Benachrichtigung: Popup/Status-Label mit neuer Strategy
- Logging: Alle Regime-Wechsel und Strategy-Switches

### 5.3 Entry Scoring Integration

**Entry Scorer:** `src/core/tradingbot/entry_scorer.py`

**Komponenten:**
```python
class EntryScorer:
    def calculate_score(self, features: FeatureVector, strategy: str) -> EntryScore:
        """Calculate entry quality score (0-1)."""
        components = {
            'trend_alignment': self._score_trend_alignment(features),
            'rsi_momentum': self._score_rsi_momentum(features),
            'macd_momentum': self._score_macd_momentum(features),
            'trend_strength': self._score_trend_strength(features),
            'mean_reversion': self._score_mean_reversion(features),
            'volume': self._score_volume(features),
            'regime_match': self._score_regime_match(features, strategy)
        }

        total_score = sum(
            components[key] * DEFAULT_WEIGHTS[key]
            for key in components
        )

        return EntryScore(
            score=total_score,
            components=components,
            confidence=self._calculate_confidence(components)
        )
```

**Integration im Bot:**
- Entry-Score wird für jedes Signal berechnet
- Threshold-basierte Filterung (z.B. nur Entries mit Score > 0.7)
- Score-Components werden geloggt für Analyse

### 5.4 Risk Management Integration

**Risiko-Parameter aus JSON:**
- `position_size`: Positionsgröße als Anteil der Equity (0-1)
- `stop_loss_pct`: Stop Loss in % vom Entry
- `take_profit_pct`: Take Profit in % vom Entry
- `trailing_mode`: "percent" oder "atr"
- `trailing_multiplier`: Faktor für Trailing Stop
- `risk_per_trade_pct`: Max. Risiko pro Trade (% der Equity)

**Dynamische Anpassung:**
- Bei Volatilitäts-Änderung: Automatische Stop-Anpassung
- Bei Regime-Wechsel: Position-Sizing-Anpassung
- Bei hohem ADX: Trailing Stop aktivieren

---

## 6. CEL Skript Implementierung - Aktueller Stand

### 6.1 Überblick

**CEL (Common Expression Language):** Sichere, nicht-Turing-complete Ausdruckssprache für Trading-Regeln

**Implementierung:** `src/core/tradingbot/cel_engine.py`

**Status:** ✅ VOLLSTÄNDIG IMPLEMENTIERT (aber noch nicht in Entry Analyzer integriert)

### 6.2 CEL Engine Features

**Hauptklasse:** `CELEngine`

**Features:**
- ✅ Compilation Caching (LRU-Cache für Performance)
- ✅ Custom Trading Functions (`pctl`, `crossover`, `isnull`, `nz`, `coalesce`)
- ✅ Safe Evaluation (bounded execution, keine loops)
- ✅ Type-Safe Context Handling (celpy types ↔ Python native types)
- ✅ Expression Validation
- ✅ Error Handling mit Default-Values

**Verfügbare Custom Functions:**

1. **pctl(series, percentile, window=None)** - Percentile Berechnung
   ```cel
   pctl(volume_history, 80, 20)  # 80th percentile of last 20 bars
   ```

2. **crossover(series1, series2)** - Bullish Crossover Detection
   ```cel
   crossover([sma20, sma20_prev], [sma50, sma50_prev])  # SMA20 crossed above SMA50
   ```

3. **isnull(value)** - Null/NaN Check
   ```cel
   isnull(obi)  # True if orderbook imbalance is null
   ```

4. **nz(value, default)** - Null-Coalescing
   ```cel
   nz(spread_bps, 50)  # Use 50 if spread_bps is null
   ```

5. **coalesce(*args)** - First Non-Null Value
   ```cel
   coalesce(depth_bid, backup_depth, 1000)  # Use first non-null value
   ```

### 6.3 CEL Rule Context (Variablenmodell)

**Dokumentation:** `01_Projectplan/Strategien_Workflow_json/Erweiterung Skript Strategien/CEL_Rules_Doku_TradingBot_Analyzer.md`

**Top-Level Variablen:**

**Markt-Features:**
```cel
tf == "5m" && regime == "R3" && direction == "UP"
close > open && volume > 1000000
atrp > 0.5 && bbwidth > 0.03
```

**Trade-Variablen (nested unter `trade`):**
```cel
trade.side == "long" && trade.pnl_pct > 1.0
trade.stop_price < close && trade.tr_lock_pct > 0.5
trade.leverage <= 20 && trade.fees_pct < 0.1
```

**Config-Variablen (nested unter `cfg`):**
```cel
atrp > cfg.min_atrp_pct && volume > pctl(volume_history, cfg.min_volume_pctl, cfg.min_volume_window)
spread_bps < cfg.max_spread_bps && depth_bid > cfg.min_depth
```

### 6.4 CEL Rule Packs (JSON-basiert)

**Struktur:**
```json
{
  "version": "1.0",
  "description": "Comprehensive Trading Rules",
  "rules": {
    "no_trade": [
      {
        "id": "no_trade_low_volume",
        "expression": "volume < pctl(volume_history, cfg.min_volume_pctl, cfg.min_volume_window)",
        "description": "Block trades when volume is below percentile threshold"
      },
      {
        "id": "no_trade_low_volatility",
        "expression": "atrp < cfg.min_atrp_pct",
        "description": "Block trades when ATR% is too low"
      }
    ],
    "entry": [
      {
        "id": "entry_trend_confirmation",
        "expression": "regime in ['R3', 'R4', 'R5'] && direction == 'UP' && crossover([close, close_prev], [sma20, sma20_prev])",
        "description": "Entry on bullish crossover in uptrend regimes"
      }
    ],
    "exit": [
      {
        "id": "exit_stop_loss",
        "expression": "trade.side == 'long' && close < trade.stop_price",
        "description": "Hard stop loss exit for long positions"
      }
    ],
    "update_stop": [
      {
        "id": "trailing_stop_activation",
        "expression": "trade.pnl_pct > trade.tra_pct ? (trade.side == 'long' ? close - (close * trade.tr_pct / 100) : close + (close * trade.tr_pct / 100)) : null",
        "description": "Activate trailing stop when profit exceeds activation threshold"
      }
    ],
    "risk": [
      {
        "id": "max_leverage_check",
        "expression": "trade.leverage > cfg.max_leverage",
        "description": "Block/exit if leverage exceeds maximum"
      }
    ]
  },
  "execution_order": ["exit", "update_stop", "risk", "no_trade", "entry"],
  "config_defaults": {
    "min_volume_pctl": 50,
    "min_volume_window": 20,
    "min_atrp_pct": 0.2,
    "max_spread_bps": 10,
    "min_depth": 100000,
    "max_leverage": 20
  }
}
```

### 6.5 Integration Status

**✅ Implementiert:**
- CEL Engine vollständig funktional
- Custom Trading Functions verfügbar
- Expression Compilation mit Caching
- Type-Safe Context Handling
- Validation und Error Handling

**⚠️ Nicht integriert:**
- CEL Rules NICHT im Entry Analyzer verwendet
- CEL Rules NICHT im Trading Bot verwendet
- Keine UI für CEL Rule Editing
- Keine CEL Rule Pack Verwaltung

**Geplante Integration:**
1. **Entry Analyzer:** CEL Rules für Custom Entry-Filters
2. **Trading Bot:** CEL Rules für No-Trade Gates, Exit Conditions, Stop Updates
3. **Strategy Settings Dialog:** CEL Rule Pack Editor
4. **Backtest Engine:** CEL-basierte Strategy Evaluation

### 6.6 CEL vs. JSON Conditions

**Unterschied:**

**JSON Conditions (aktuell verwendet):**
```json
{
  "all": [
    {"left": {"indicator_id": "rsi", "field": "value"}, "op": "gt", "right": {"value": 50}},
    {"left": {"indicator_id": "volume_ratio", "field": "value"}, "op": "gt", "right": {"value": 1.5}}
  ]
}
```

**CEL Expressions (zukünftig geplant):**
```cel
rsi.value > 50 && volume_ratio.value > 1.5 && pctl(volume_history, 80, 20) > volume
```

**Vorteile CEL:**
- Kompaktere Syntax
- Bessere Lesbarkeit
- Mehr Ausdruckskraft (Funktionen, Berechnungen)
- Einfachere Verschachtelung
- Standard-Operators (`&&`, `||`, `!`)

**Aktueller Stand:** JSON Conditions haben Priorität, CEL ist opt-in für fortgeschrittene User

### 6.7 Beispiel: CEL Rule Evaluation

```python
from src.core.tradingbot.cel_engine import get_cel_engine

# 1. Engine holen (Singleton)
engine = get_cel_engine()

# 2. Context erstellen
context = {
    "atrp": 0.6,
    "volume": 1500000,
    "regime": "R3",
    "direction": "UP",
    "close": 45000,
    "sma20": 44500,
    "cfg": {
        "min_atrp_pct": 0.2,
        "min_volume_pctl": 50
    },
    "volume_history": [1200000, 1300000, 1400000, 1500000, 1600000]
}

# 3. No-Trade Rule evaluieren
no_trade_expr = "atrp < cfg.min_atrp_pct || volume < pctl(volume_history, cfg.min_volume_pctl, 5)"
no_trade = engine.evaluate(no_trade_expr, context)
# Result: False (Trade erlaubt)

# 4. Entry Rule evaluieren
entry_expr = "regime == 'R3' && direction == 'UP' && close > sma20"
entry_signal = engine.evaluate(entry_expr, context)
# Result: True (Entry-Signal)

# 5. Validation
is_valid, error = engine.validate_expression("rsi > 50 && macd.histogram > 0")
# Result: (True, None)

# 6. Cache-Statistiken
cache_info = engine.get_cache_info()
# Result: {'hits': 145, 'misses': 12, 'size': 12, 'maxsize': 128}
```

---

## Anhang A: Dateien-Referenz

**Entry Analyzer:**
- `src/ui/dialogs/entry_analyzer_popup.py` - Haupt-Dialog
- `src/analysis/visible_chart/` - Analyse-Logik

**Regime-Erkennung:**
- `src/core/tradingbot/regime_engine.py` - Legacy (deprecated)
- `src/core/tradingbot/regime_engine_json.py` - JSON-basiert (aktiv)
- `src/core/tradingbot/config/detector.py` - RegimeDetector
- `src/core/tradingbot/config/evaluator.py` - ConditionEvaluator

**Indikatoren:**
- `src/core/indicators/engine.py` - IndicatorEngine
- `src/core/indicators/registry.py` - Indikator-Definitionen
- `src/core/indicators/calculators/` - Berechnungs-Logik

**Strategien:**
- `src/core/tradingbot/config/router.py` - StrategyRouter
- `src/core/tradingbot/config/executor.py` - StrategySetExecutor
- `src/core/tradingbot/entry_scorer.py` - EntryScorer

**Backtesting:**
- `src/backtesting/engine.py` - BacktestEngine
- `src/core/tradingbot/backtest_harness.py` - BacktestHarness

**Bot Integration:**
- `src/core/tradingbot/bot_controller.py` - BotController
- `src/ui/widgets/chart_window_mixins/bot_ui_control_widgets.py` - UI Controls
- `src/ui/dialogs/trading_bot_settings_tab.py` - Bot Settings

**CEL Engine:**
- `src/core/tradingbot/cel_engine.py` - CEL Engine Implementation
- `01_Projectplan/Strategien_Workflow_json/Erweiterung Skript Strategien/CEL_Rules_Doku_TradingBot_Analyzer.md` - Dokumentation

**JSON Schemas:**
- `03_JSON/schema/strategy_config_schema.json` - Strategy Config Schema
- `03_JSON/Trading_Bot/regime_based_comprehensive.json` - Beispiel-Config

---

## Anhang B: Migration Path (Legacy → JSON)

**Legacy (Hardcoded):**
```python
from src.core.tradingbot.regime_engine import RegimeEngine

engine = RegimeEngine()
regime_state = engine.classify(features)  # RegimeState mit hardcoded Schwellenwerten
```

**JSON-basiert (Konfigurierbar):**
```python
from src.core.tradingbot.regime_engine_json import RegimeEngineJSON

engine = RegimeEngineJSON()
regime_state = engine.classify_from_config(
    data=df,
    config_path="03_JSON/Trading_Bot/regime_based_comprehensive.json",
    scope="entry"
)
```

**Vorteile JSON:**
- ✅ Keine Hardcoded-Werte
- ✅ Mehrere Regimes gleichzeitig aktiv
- ✅ Prioritäts-basierte Auswahl
- ✅ Scope-Filterung (entry/exit/in_trade)
- ✅ Besser testbar (Config als Test-Fixture)
- ✅ Versionierbar (Git-History)

---

**Ende der Dokumentation**
