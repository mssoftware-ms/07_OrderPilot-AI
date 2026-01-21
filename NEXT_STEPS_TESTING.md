# ✅ QScintilla Installation Erfolgreich - Nächste Schritte

**Status:** PyQt6-QScintilla 2.14.1 erfolgreich in Windows .venv installiert
**Datum:** 2026-01-20

---

## 🎯 JETZT: Anwendung testen

### Schritt 1: Verifikation (Optional, empfohlen)

Prüfe, ob der Import funktioniert:

```powershell
# In PowerShell (mit aktivierter .venv)
python -c "from PyQt6.Qsci import QsciScintilla, QsciAPIs; print('✅ QScintilla import successful')"
```

**Erwartete Ausgabe:**
```
✅ QScintilla import successful
```

---

### Schritt 2: Anwendung starten

```powershell
# Starte die Hauptanwendung
python main.py
```

**Erwartung:**
- Anwendung startet normal
- KEIN `ModuleNotFoundError` mehr
- Chart-Fenster öffnet sich

---

### Schritt 3: Strategy Concept Window öffnen

**Im laufenden Programm:**

1. **Klicke auf "Strategy Concept" Button** in der Toolbar (oben im Chart-Fenster)

2. **Erwartetes Verhalten:**
   ```
   ✅ Strategy Concept Window öffnet sich
   ✅ KEIN Traceback in Console
   ✅ Fenster zeigt 2 Tabs:
      - Tab 1: Entry Analysis
      - Tab 2: Pattern Integration  ← HIER ist der CEL Editor
   ```

3. **Falls Fehler auftreten:**
   - Screenshot der Fehlermeldung machen
   - Console-Output kopieren
   - Melden für weitere Diagnose

---

### Schritt 4: CEL Editor Komponenten prüfen

**Wechsle zu Tab 2: Pattern Integration**

**Erwartete UI-Komponenten:**

```
┌─────────────────────────────────────────────────────────────┐
│ Pattern Integration Widget                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [Patterns Table - Links]    [Strategy Details - Rechts]    │
│                                                             │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ CEL Workflow Scripts:                                       │
│                                                             │
│ [Workflow Selector: Entry ▼]                                │
│                                                             │
│ ┌────────────────────────┬──────────────────────────────┐  │
│ │ CEL Editor             │ Function Palette              │  │
│ │ (70% width)            │ (30% width)                   │  │
│ │                        │                               │  │
│ │ Toolbar:               │ Categories:                   │  │
│ │ [🤖 Generate]          │ ▼ Indicators                  │  │
│ │ [✓ Validate]           │ ▼ Math Functions              │  │
│ │ [🔧 Format]            │ ▼ Trading Functions           │  │
│ │ [🗑️ Clear]             │ ▼ Logic & Comparison          │  │
│ │                        │ ...                           │  │
│ │ [Editor mit Syntax     │                               │  │
│ │  Highlighting]         │ [Search: ____________]        │  │
│ │                        │                               │  │
│ │ [Line numbers]         │ [↑ Insert at Cursor]          │  │
│ │                        │                               │  │
│ └────────────────────────┴──────────────────────────────┘  │
│                                                             │
│ Status: Ready                                               │
│                                                             │
│ [💾 Export to CEL]                                          │
└─────────────────────────────────────────────────────────────┘
```

**Verifiziere diese Elemente:**
- ✅ Workflow Selector (Dropdown mit 4 Optionen)
- ✅ CEL Editor mit dunklem Theme (schwarz/grau Hintergrund)
- ✅ Toolbar mit 4 Buttons (🤖 Generate ist BLAU)
- ✅ Function Palette rechts mit Suchfeld
- ✅ "💾 Export to CEL" Button unten

---

### Schritt 5: Basis-Funktionalität testen

#### Test 5.1: Syntax Highlighting

1. Klicke in den CEL Editor
2. Tippe ein: `rsi14.value > 50`
3. **Erwartung:**
   - `rsi14.value` erscheint in **Cyan** (Indicator-Farbe)
   - `>` erscheint in **Weiß** (Operator-Farbe)
   - `50` erscheint in **Grün** (Number-Farbe)

**Screenshot:** Sollte so aussehen (dunkles Theme mit Farbcoding)

#### Test 5.2: Autocomplete

1. Tippe: `rs` (2 Buchstaben)
2. **Erwartung:** Autocomplete-Popup erscheint nach 0.5 Sekunden
3. Zeigt: `rsi5.value`, `rsi7.value`, `rsi14.value`, `rsi21.value`
4. Drücke **Enter** um zu übernehmen

#### Test 5.3: Function Palette

1. In Function Palette, klicke auf "Indicators" Kategorie
2. **Erwartung:** Liste erweitert sich, zeigt 15+ Indikatoren
3. Klicke auf "RSI"
4. **Erwartung:** Description Panel unten zeigt:
   ```
   RSI
   rsi14.value
   Relative Strength Index (0-100)
   ```
5. Doppelklick auf "RSI"
6. **Erwartung:** `rsi14.value` wird im Editor eingefügt

---

### Schritt 6: AI Generation testen (KRITISCH!)

**Voraussetzung:** OPENAI_API_KEY muss in Windows-Systemvariablen gesetzt sein

#### Prüfe API Key:

```powershell
# In PowerShell
$env:OPENAI_API_KEY
```

**Sollte zeigen:** `sk-proj-...` (dein API Key)
**Falls leer:** Siehe [API Key Setup](#api-key-setup) unten

#### Test AI Generation:

1. **Pattern auswählen:**
   - In Pattern Table links, klicke auf: **"Pin Bar (Bullish)"**
   - Strategy Details rechts sollten sich füllen

2. **Workflow wählen:**
   - Workflow Selector: Wähle **"Entry"**

3. **AI Generation starten:**
   - Klicke **"🤖 Generate"** Button (blau)

4. **Erwartetes Verhalten:**
   ```
   [Progress Dialog erscheint]
   🤖 Generating ENTRY CEL code with OpenAI GPT-5.2...
   [Indeterminate Progress Bar]
   [5-30 Sekunden warten]

   [Success Dialog]
   ✓ Generated 87 characters!

   Please review and validate.
   ```

5. **Im Editor erscheint generierter Code:**
   ```cel
   rsi14.value < 30 && close < bb_20_2.lower && volume_ratio_20.value > 1.2
   ```
   (Beispiel - tatsächlicher Code kann variieren)

6. **Console Log prüfen:**
   ```json
   {"timestamp": "...", "name": "ui.widgets.cel_ai_helper", "message": "Generating CEL code with OpenAI gpt-5.2 (reasoning_effort=medium)"}
   {"timestamp": "...", "name": "ui.widgets.cel_ai_helper", "message": "Generated 87 chars CEL code (tokens: 1523)"}
   ```

#### Mögliche Fehler:

**Fehler 1: "AI Generation Failed - Check API Key"**
```
❌ AI Generation Failed

Check:
• AI enabled in Settings
• OPENAI_API_KEY set
• Internet connection
```
→ Siehe [API Key Setup](#api-key-setup)

**Fehler 2: Timeout/Network Error**
```
asyncio.TimeoutError: OpenAI API request timed out
```
→ Prüfe Internetverbindung:
```powershell
Test-NetConnection -ComputerName api.openai.com -Port 443
```

**Fehler 3: "Insufficient Credits"**
```
openai.error.RateLimitError: You exceeded your current quota
```
→ Prüfe OpenAI Account: https://platform.openai.com/usage

---

### Schritt 7: JSON Export testen

1. **Generiere Code für alle 4 Workflows:**
   - Entry: `rsi14.value < 30 && close < bb_20_2.lower`
   - Exit: `rsi14.value > 70 || trade.pnl_pct > 3.0`
   - Before Exit: `trade.pnl_pct > 2.0`
   - Update Stop: `trade.pnl_pct > 1.5`

2. **Klicke "💾 Export to CEL" Button**

3. **Erwarteter Success Dialog:**
   ```
   ✓ Exported to: D:\03_Git\02_Python\07_OrderPilot-AI\03_JSON\Trading_Bot\ptrn_pin_bar_bullish.json
   ```

4. **Öffne exportierte Datei:**
   ```
   D:\03_Git\02_Python\07_OrderPilot-AI\03_JSON\Trading_Bot\ptrn_pin_bar_bullish.json
   ```

5. **Verifiziere JSON-Struktur:**
   ```json
   {
     "schema_version": "1.0.0",
     "strategy_type": "PATTERN_BASED",
     "name": "ptrn_pin_bar_bullish",
     "patterns": [
       {
         "id": "PIN_BAR_BULLISH",
         "name": "Pin Bar (Bullish)",
         "category": "REVERSAL"
       }
     ],
     "workflow": {
       "entry": {
         "language": "CEL",
         "expression": "rsi14.value < 30 && close < bb_20_2.lower",
         "enabled": true
       },
       "exit": {
         "language": "CEL",
         "expression": "rsi14.value > 70 || trade.pnl_pct > 3.0",
         "enabled": true
       },
       "before_exit": {
         "language": "CEL",
         "expression": "trade.pnl_pct > 2.0",
         "enabled": true
       },
       "update_stop": {
         "language": "CEL",
         "expression": "trade.pnl_pct > 1.5",
         "enabled": true
       }
     },
     "metadata": {
       "strategy_type": "TREND_REVERSAL",
       "risk_reward_ratio": "1:2",
       "success_rate": 65.0,
       ...
     }
   }
   ```

---

## 📊 Erfolgs-Kriterien

**Phase 1 + Phase 2 ist ERFOLGREICH wenn:**

- ✅ Strategy Concept Window öffnet ohne Fehler
- ✅ CEL Editor zeigt Syntax Highlighting
- ✅ Autocomplete funktioniert (zeigt 100+ Funktionen)
- ✅ Function Palette kann Code einfügen
- ✅ AI Generation erzeugt validen CEL Code
- ✅ JSON Export erstellt gültige Datei
- ✅ Keine Console-Errors während Nutzung

---

## 🐛 Troubleshooting

### Problem: Strategy Concept Window öffnet nicht

**Check:**
```powershell
# Teste direkten Import
python -c "import sys; sys.path.insert(0, 'src'); from ui.dialogs.strategy_concept_window import StrategyConceptWindow; print('✅ Import OK')"
```

**Falls Fehler:**
- Screenshot der Fehlermeldung
- Console-Output kopieren

---

### Problem: Syntax Highlighting nicht sichtbar

**Symptome:**
- Aller Text ist weiß/grau (keine Farben)

**Check:**
1. Editor-Hintergrund dunkel? (sollte #1e1e1e sein)
2. In Console nach Lexer-Fehlern suchen

---

### Problem: AI Generation funktioniert nicht

**Diagnose-Schritte:**

1. **Prüfe Settings → AI Tab:**
   ```
   - AI Features: Enabled ✅
   - Default Provider: OpenAI ✅
   - Model: gpt-5.2 (GPT-5.2 Latest) ✅
   ```

2. **Prüfe API Key:**
   ```powershell
   $env:OPENAI_API_KEY
   # Sollte: sk-proj-...
   ```

3. **Prüfe Console für Errors:**
   ```json
   {"level": "ERROR", "name": "cel_ai_helper", "message": "..."}
   ```

---

## 🔧 API Key Setup

**Falls OPENAI_API_KEY fehlt:**

### Methode 1: Systemvariable (dauerhaft)

1. **Win + X** → **System**
2. **Advanced system settings**
3. **Environment Variables**
4. **System variables** → **New**
   - Variable name: `OPENAI_API_KEY`
   - Variable value: `sk-proj-...` (dein Key)
5. **OK** → **OK**
6. **Neustart der Anwendung** (wichtig!)

### Methode 2: PowerShell (temporär, nur aktuelle Session)

```powershell
# Setze für aktuelle PowerShell-Session
$env:OPENAI_API_KEY = "sk-proj-..."

# Starte Anwendung in gleicher Session
python main.py
```

### Verifiziere API Key:

```powershell
# Zeige Key (maskiert)
$key = $env:OPENAI_API_KEY
if ($key) {
    $masked = $key.Substring(0, 7) + "..." + $key.Substring($key.Length - 4)
    Write-Host "✅ API Key set: $masked"
} else {
    Write-Host "❌ API Key NOT set"
}
```

---

## 📞 Support

**Bei Problemen:**

1. **Screenshot der UI** (zeige was fehlt/falsch ist)
2. **Console-Output** (alle Logs kopieren)
3. **Fehlermeldungen** (vollständiger Traceback)

**Dokumentation:**
- Vollständige Test-Anleitung: `docs/testing/CEL_Integration_Test_Guide.md`
- Installation-Guide: `INSTALL_QSCINTILLA_WINDOWS.md`
- Implementierungs-Details: `docs/integration/CEL_Phase1_Phase2_Complete.md`

---

## ✅ Nach erfolgreichem Test

**Wenn alles funktioniert:**

1. **Dokumentiere Ergebnisse:**
   - Welche Tests erfolgreich?
   - Welche Fehler aufgetreten?
   - Screenshots von funktionierenden Features

2. **Teste weitere Patterns:**
   - Engulfing Bullish
   - Hammer
   - Morning Star
   - Etc.

3. **Experimentiere mit AI:**
   - Verschiedene Patterns
   - Verschiedene Workflows (Entry/Exit/etc.)
   - Reasoning Effort ändern (Settings → AI → OpenAI)

4. **Erstelle eigene Strategien:**
   - Kombiniere mehrere Patterns
   - Teste verschiedene Indikatoren
   - Exportiere als JSON

---

## 🎯 Nächste Schritte (nach erfolgreichem Test)

**Phase 3 (geplant):**
- Pattern Library Integration (50+ Patterns aus Chartmuster_Erweitert_2026.md)
- Anthropic Claude Sonnet 4.5 Integration
- Google Gemini Integration
- Advanced CEL Functions (Pattern Detection)

**Phase 4 (geplant):**
- Bot Integration (CEL Strategies im Trading Bot)
- Real-time CEL Evaluation
- Backtest mit CEL Conditions

---

**Viel Erfolg beim Testen! 🚀**

Bei Fragen oder Problemen einfach melden.
