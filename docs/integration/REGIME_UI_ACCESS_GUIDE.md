# Regime-System UI - Wo finde ich die Funktionen?

## 📍 Übersicht: 3 Hauptzugangspunkte

Das Regime-basierte Trading-System ist über 3 UI-Bereiche zugänglich:

1. **🎯 Entry Analyzer Dialog** - Backtesting & Indicator Optimization
2. **⚙️ Strategy Settings Dialog** - Market Analysis & JSON Management
3. **🤖 Bot Control Panel** - Bot Start & Runtime Monitoring

---

## 1. 🎯 Entry Analyzer Dialog

### Wo finde ich es?

**Chart Toolbar** → **"🎯 Entry Analyzer" Button** (rechts in der zweiten Toolbar-Zeile)

![Entry Analyzer Button Location](toolbar_entry_analyzer.png)

**Alternativ:**
- Menü → Tools → Entry Analyzer
- Tastenkombination: `Ctrl+E` (falls konfiguriert)

### Was ist drin?

Der Entry Analyzer hat **7 Tabs**:

#### Tab 1: ⚙️ Backtest Setup
**Regime-Feature: Backtest mit Regime-Detection**

```
Funktionen:
├── Strategy JSON laden
├── Symbol & Zeitraum wählen
├── Kapital festlegen
└── 🚀 Run Backtest Button
    └── Startet Backtest mit Regime-Detection
```

**Ergebnis:**
- Backtest Results Tab mit Performance-Metriken
- **Regime-Linien im Chart** (vertikale farbige Linien für Regime-Grenzen)
  - Grün = TREND_UP
  - Rot = TREND_DOWN
  - Orange = RANGE

#### Tab 2: 📈 Backtest Results
**Regime-Feature: Performance-Analyse**

```
Funktionen:
├── Performance Summary (Net Profit, Sharpe, Max DD)
├── Trade List mit Regime-Zuordnung
└── Equity Curve
```

#### Tab 3: 🔧 Indicator Optimization
**Regime-Feature: Multi-Regime Indicator Testing**

##### Sub-Tab: ⚙️ Setup
```
Workflow:
1. Indikator-Auswahl (3-spaltig, 6 Kategorien, 20 Indikatoren)
   ├── TREND & OVERLAY: SMA, EMA, ICHIMOKU, PSAR, VWAP, PIVOTS
   ├── BREAKOUT & CHANNELS: BB, KC
   ├── REGIME & TREND: ADX, CHOP
   ├── MOMENTUM: RSI, MACD, STOCH, CCI
   ├── VOLATILITY: ATR, BB_WIDTH
   └── VOLUME: OBV, MFI, AD, CMF

2. Parameter Ranges (dynamisch, nur für gewählte Indikatoren)
   Beispiel RSI:
   └── period: Min [10] Max [20] Step [2]
       → Testet RSI(10), RSI(12), RSI(14), RSI(16), RSI(18), RSI(20)

3. Test Mode wählen
   ├── Entry / Exit
   └── Long / Short

4. 🚀 Optimize Indicators Button klicken
```

**Was passiert:**
- Jeder Indikator wird mit allen Parameter-Kombinationen getestet
- **Pro Regime** wird ein Score (0-100) berechnet
- Ergebnisse: Indicator × Parameters × Regime

**Beispiel:**
```
RSI(14) in TREND_UP: Score 78.5, Win Rate 65%, Profit Factor 2.1
RSI(14) in RANGE: Score 42.3, Win Rate 48%, Profit Factor 1.2
```

##### Sub-Tab: 📊 Results
```
Results Table:
├── Sortiert nach Score (höchster zuerst)
├── Farbcodierung:
│   ├── Grün: Score ≥ 70 (gut)
│   ├── Orange: Score 40-70 (mittel)
│   └── Rot: Score < 40 (schlecht)
└── Spalten:
    ├── Indicator
    ├── Parameters
    ├── Regime (TREND_UP, TREND_DOWN, RANGE, etc.)
    ├── Test Type (ENTRY/EXIT)
    ├── Trade Side (LONG/SHORT)
    ├── Score (0-100)
    ├── Win Rate
    ├── Profit Factor
    └── Total Trades
```

**Nach Optimization verfügbar:**
```
📦 Create Regime Set from Results Button
```

**Was macht dieser Button?**
1. Dialog öffnet sich:
   - Name für Regime Set eingeben
   - Top N Indikatoren pro Regime wählen (Standard: 3)

2. Automatische Verarbeitung:
   - Gruppiert Results nach Regime
   - Wählt beste N Indikatoren pro Regime
   - Berechnet Gewichtungen (normalisierte Scores)
   - Generiert JSON-Config mit Routing-Rules

3. Backtest-Frage:
   - "Do you want to backtest this regime set?"
   - Bei JA: Automatischer Backtest des kompletten Sets

4. JSON-Datei gespeichert:
   ```
   03_JSON/Trading_Bot/regime_sets/RegimeSet_20260119_142035.json
   ```

5. Anzeige:
   - Backtest Results Tab zeigt Performance
   - Chart zeigt Regime-Linien

---

## 2. ⚙️ Strategy Settings Dialog

### Wo finde ich es?

**Trading Bot Tab** → **"⚙️ Settings Bot" Button** (oben im Bot Tab)

![Strategy Settings Button](bot_tab_settings.png)

**Pfad:**
1. Hauptfenster → **"Trading Bot" Tab** öffnen
2. Tab Header → **"⚙️ Settings Bot"** Button klicken

### Was ist drin?

#### Section 1: 📊 Live Markt-Regime
```
Anzeige:
├── Aktuelles Regime: TREND_UP - NORMAL
│   └── (Auto-Update alle 5 Sekunden)
├── Aktives Strategy Set: Trend Following Set
└── Indikatorenset: RSI, MACD, ADX, SMA_Fast, SMA_Slow
```

#### Section 2: 🎯 Matched Strategy (from Analysis)
```
Initial: "No analysis performed yet"

Nach Analyze:
├── ✓ Matched: Trend Following Set
│   Regimes: regime_trend_up, regime_normal_volatility
oder
└── ⚠ No match for current regime: RANGE - LOW
    Active Regimes: regime_range, regime_low_volatility
```

#### Section 3: 📋 Verfügbare Strategien
```
Tabelle:
├── Name
├── Typ (Trend Following, Mean Reversion, etc.)
├── Indikatoren (Anzahl)
├── Entry Conditions (Anzahl)
├── Exit Conditions (Anzahl)
└── Aktiv (Checkbox)
```

#### Buttons:

##### 🔍 Analyze Current Market **← NEUE FUNKTION!**

**Was macht dieser Button?**

```
Workflow:
1. Holt aktuelle Marktdaten vom Chart
   └── FeatureVector (Indikatoren, Preise, Volumen)

2. Regime Detection
   ├── RegimeEngine.classify()
   ├── Berechnet: ADX, ATR%, BB-Width, RSI
   └── Ergebnis: TREND_UP - NORMAL (Confidence: 87%)

3. Indicator Values Calculation
   └── Mappt FeatureVector → indicator_values dict

4. Regime Detection (JSON-based)
   └── Evaluiert Regime-Conditions aus gewählter Strategy

5. Strategy Routing
   └── Matched Strategy Set oder "No match"

6. Ergebnis-Anzeige:
   ├── Popup mit Details:
   │   ├── Current Regime: TREND_UP - NORMAL
   │   ├── ADX: 32.5
   │   ├── ATR%: 2.1%
   │   ├── Confidence: 87%
   │   ├── Active Regimes: regime_trend_up
   │   ├── Matched Set: Trend Following Set
   │   ├── Strategies in Set: Aggressive Trend, Conservative Trend
   │   └── Entry/Exit Conditions (Kurzinfo)
   └── UI-Label wird aktualisiert (grün oder orange)
```

**Voraussetzung:**
- Chart muss Marktdaten haben (Candles geladen)
- Strategy aus Tabelle wählen BEVOR Analyze klicken

**Ergebnis:**
- Weißt du, ob aktuelle Strategy zum Markt passt
- Siehst du, welche Regimes aktiv sind
- Kannst du entscheiden: Bot starten oder andere Strategy wählen

##### Weitere Buttons:
```
📁 Laden - JSON-Strategy aus Datei laden
🗑️ Löschen - Ausgewählte Strategy löschen
➕ Neu erstellen - Neue JSON-Strategy erstellen (in Entwicklung)
✏️ Bearbeiten - Ausgewählte Strategy bearbeiten (in Entwicklung)
🔄 Aktualisieren - Strategy-Liste neu laden
```

---

## 3. 🤖 Bot Control Panel

### Wo finde ich es?

**Chart Window** → **Bot Control Widget** (meist rechts oder im Trading Tab)

oder

**Trading Bot Tab** → Bot Control Section

### Was ist drin?

#### Bot Status Display
```
├── Status: STOPPED / RUNNING / PAUSED
├── Current Regime: TREND_UP - NORMAL (Live-Update)
└── Active Strategy: Trend Following Set
```

#### Buttons:

##### ▶️ Start Bot
**Workflow:**
1. Klick auf "Start Bot"
2. **Optional:** Strategy Settings Dialog öffnet sich automatisch
   - Wähle Strategy aus Tabelle
   - Klicke "🔍 Analyze Current Market"
   - Prüfe Matched Strategy
   - Bestätige mit Dialog-Close
3. Bot startet mit gewählter Strategy
4. **Dynamic Strategy Switching aktiviert:**
   - Bei Regime-Wechsel → automatische Strategy-Umschaltung
   - UI-Notification bei Wechsel

##### ⏸️ Pause Bot
- Pausiert Trading
- Behält offene Positionen
- Regime-Monitoring läuft weiter

##### ⏹️ Stop Bot
- Stoppt Trading
- Schließt offene Positionen (optional)
- Regime-Monitoring stoppt

---

## 🎬 Kompletter Workflow: Entry → Bot Start

### Szenario: "Ich will die beste Strategie für aktuelles Markt-Regime finden und Bot starten"

#### Schritt 1: Indicator Optimization (Entry Analyzer)
```bash
1. Chart öffnen mit Symbol (z.B. BTCUSDT)
2. Toolbar → "🎯 Entry Analyzer" klicken
3. Tab "🔧 Indicator Optimization" öffnen
4. Sub-Tab "⚙️ Setup":
   a) Indikatoren wählen: RSI, MACD, ADX, SMA, EMA
   b) Parameter Ranges prüfen (Standard ist OK)
   c) Test Mode: Entry × Long
   d) "🚀 Optimize Indicators" klicken
5. Warten (~30-60 Sekunden für 5 Indikatoren)
6. Sub-Tab "📊 Results":
   a) Sortiert nach Score
   b) Siehst du beste Indikatoren pro Regime
   c) Notiere Top 3 pro Regime
```

#### Schritt 2: Regime Set Creation
```bash
7. "📦 Create Regime Set from Results" klicken
8. Dialog:
   a) Name: "MyOptimizedSet_BTCUSDT"
   b) Top N: 3
   c) Bestätigen
9. "Backtest Regime Set?" → JA
10. Warten auf Backtest-Ergebnis
11. Prüfe Performance-Metriken
12. Dialog schließen
```

#### Schritt 3: Market Analysis (Strategy Settings)
```bash
13. Wechsel zu "Trading Bot" Tab
14. "⚙️ Settings Bot" klicken
15. Strategy Settings Dialog:
    a) Tabelle: "MyOptimizedSet_BTCUSDT" auswählen
    b) "🔍 Analyze Current Market" klicken
    c) Popup prüfen:
       - Current Regime: Z.B. TREND_UP - NORMAL
       - Matched: ✓ oder ⚠
    d) Wenn ✓ Matched → alles gut
    e) Wenn ⚠ No match → andere Strategy wählen oder warten
16. Dialog schließen
```

#### Schritt 4: Bot Start
```bash
17. Bot Control Panel:
    a) "▶️ Start Bot" klicken
    b) Bot startet mit "MyOptimizedSet_BTCUSDT"
18. Beobachte:
    - Status: RUNNING
    - Current Regime: Live-Update
    - Dynamic Strategy Switching: Bei Regime-Wechsel wird automatisch umgeschaltet
```

---

## 📊 UI-Hierarchie (Schnellreferenz)

```
Hauptfenster
│
├── Chart Toolbar (Row 2)
│   └── 🎯 Entry Analyzer Button
│       │
│       └── Entry Analyzer Dialog
│           ├── Tab 1: ⚙️ Backtest Setup
│           │   └── 🚀 Run Backtest
│           │       └── Regime-Linien im Chart
│           │
│           ├── Tab 2: 📈 Backtest Results
│           │
│           ├── Tab 3: 🔧 Indicator Optimization
│           │   ├── Sub-Tab: ⚙️ Setup
│           │   │   └── 🚀 Optimize Indicators
│           │   │
│           │   └── Sub-Tab: 📊 Results
│           │       └── 📦 Create Regime Set
│           │           └── Auto-Backtest
│           │
│           └── Tab 4-7: Andere Features
│
└── Trading Bot Tab
    │
    ├── ⚙️ Settings Bot Button
    │   │
    │   └── Strategy Settings Dialog
    │       ├── 📊 Live Markt-Regime
    │       ├── 🎯 Matched Strategy
    │       ├── 📋 Verfügbare Strategien
    │       └── 🔍 Analyze Current Market
    │
    └── Bot Control Panel
        ├── Status Display
        └── ▶️ Start Bot / ⏸️ Pause / ⏹️ Stop
```

---

## 🔍 Quick-Find: "Ich will..."

| Ich will... | Wo finde ich es? |
|-------------|------------------|
| **Regime-Linien im Chart sehen** | Entry Analyzer → Backtest Setup → Run Backtest |
| **Beste Indikatoren pro Regime finden** | Entry Analyzer → Indicator Optimization → Optimize |
| **Regime Set erstellen** | Entry Analyzer → Indicator Optimization → Results → Create Regime Set |
| **Prüfen ob Strategy zum Markt passt** | Trading Bot Tab → Settings Bot → Analyze Current Market |
| **Bot mit Regime-basierter Strategy starten** | Trading Bot Tab → Start Bot |
| **Live Regime anzeigen** | Trading Bot Tab → Settings Bot (Live Markt-Regime Section) |
| **Regime-Wechsel beobachten** | Bot Control Panel (während Bot läuft) |

---

## 🐛 Troubleshooting

### "Entry Analyzer Button ist grau"
**Lösung:** Chart muss Marktdaten haben (Symbol laden)

### "Analyze Current Market zeigt Fehler"
**Lösung:**
1. Prüfe: Chart hat Candles geladen
2. Prüfe: Strategy aus Tabelle ausgewählt
3. Prüfe: JSON-Config valide (keine Syntax-Fehler)

### "Regime-Linien werden nicht angezeigt"
**Lösung:**
1. Backtest muss erfolgreich durchgelaufen sein
2. Chart muss sichtbar sein (nicht minimiert)
3. Prüfe Logs: `logs/entry_analyzer.log`

### "Create Regime Set Button ist deaktiviert"
**Lösung:** Erst "Optimize Indicators" laufen lassen, dann wird Button aktiviert

### "Bot startet nicht mit Regime-Strategy"
**Lösung:**
1. Strategy Settings Dialog öffnen
2. Strategy aus Tabelle wählen
3. "Analyze Current Market" → Prüfen ob matched
4. Dialog schließen, dann Bot starten

---

**Hinweis:** Alle Buttons und Dialoge sind funktional und production-ready! 🚀

**Letzte Aktualisierung:** 2026-01-19
**Version:** 2.0
