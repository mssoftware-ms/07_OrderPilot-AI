# JSON Entry Implementation - Status

**Datum:** 2026-01-29  
**Version:** 1.0 - MVP Implementation

---

## ✅ Was ist implementiert?

### 1. **UI - Button & File Picker**
- ✅ Button "Start Bot (JSON)" im Bot Tab (Chart → Trading Bot → Bot Tab)
- ✅ File Picker für Regime JSON (03_JSON/Entry_Analyzer/Regime/)
- ✅ JSON Validierung (prüft ob entry_expression vorhanden ist)
- ✅ Info-Dialoge (erfolgreich geladen / Fehler)

**Location:** 
- `src/ui/widgets/chart_window_mixins/bot_ui_control_widgets.py` (Button)
- `src/ui/widgets/chart_window_mixins/bot_event_handlers.py` (Handler)

---

### 2. **Bot Start Logik**
- ✅ `_start_bot_with_json_entry()` Methode erstellt
- ✅ Lädt JsonEntryConfig
- ✅ Startet BotController
- ✅ Gleiche UI-Updates wie normaler Bot
- ✅ Status "RUNNING (JSON Entry)"

**Location:** 
- `src/ui/widgets/chart_window_mixins/bot_callbacks_lifecycle_mixin.py`

---

### 3. **Nach Entry: Komplette Pipeline**
- ✅ `_on_bot_signal()` wird aufgerufen (existiert schon)
- ✅ Tabelle im Trading Tab wird gefüllt (existiert schon)
- ✅ Chart-Marker werden gezeichnet (existiert schon)
- ✅ Stop-Loss wird gesetzt (existiert schon)
- ✅ Trailing Stop wird initialisiert (existiert schon)
- ✅ Exit-Logik funktioniert (existiert schon)

**Location:** 
- `src/ui/widgets/chart_window_mixins/bot_callbacks_signal_mixin.py`

---

## ⚠️ Was fehlt noch?

### 1. **BotController Integration** (KRITISCH!)

Der BotController muss erweitert werden um:

#### A) JsonEntryScorer nutzen
```python
# In BotController.__init__ oder set_json_entry_config:
from src.core.tradingbot.json_entry_scorer import JsonEntryScorer
from src.core.tradingbot.cel_engine import CELEngine

cel_engine = CELEngine()
self._json_entry_scorer = JsonEntryScorer(json_entry_config, cel_engine)
```

#### B) Nach jeder Candle: CEL evaluieren
```python
# Im BotController Update-Loop (z.B. in _process_candle oder ähnlich):

# 1. Regime-Analyse triggern (Entry Analyzer)
regime_state = self._trigger_regime_analysis()

# 2. CEL Expression evaluieren
should_enter_long, score, reasons = self._json_entry_scorer.should_enter_long(
    features=current_features,
    regime=regime_state,
    chart_window=None,  # Im Bot gibt es kein Chart Window
    prev_regime=self._prev_regime
)

should_enter_short, score_short, reasons_short = self._json_entry_scorer.should_enter_short(
    features=current_features,
    regime=regime_state,
    chart_window=None,
    prev_regime=self._prev_regime
)

# 3. Bei Entry-Signal: Signal generieren
if should_enter_long or should_enter_short:
    signal = self._create_entry_signal(
        side="long" if should_enter_long else "short",
        score=score if should_enter_long else score_short,
        reasons=reasons if should_enter_long else reasons_short
    )
    
    # Signal an UI senden (ruft _on_bot_signal auf)
    if self._on_signal:
        self._on_signal(signal)
```

#### C) Regime-Analyse triggern
```python
def _trigger_regime_analysis(self):
    """Triggert Regime-Analyse wie im Entry Analyzer.
    
    Muss die gleiche Logik nutzen wie:
    Entry Analyzer → Tab Regime → Button "Analyse visible chart"
    """
    # TODO: Entry Analyzer Regime-Logik aufrufen
    # Gibt RegimeState zurück mit aktuellen Regimes
    pass
```

---

### 2. **Entry Analyzer: JSON mit entry_expression**

Aktuell generiert der Entry Analyzer JSON **OHNE** entry_expression.

**Lösung:** 
- ✅ Mein **Regime Entry Expression Editor** ist fertig
- ✅ Aber: Er ist im CEL Editor versteckt (zu umständlich)

**TODO:** Button im Entry Analyzer hinzufügen:
```
Entry Analyzer → Tab Regime
  └─ Nach "Save" Button
     └─ [📝 Add Entry Expression] Button
        └─ Öffnet meinen Editor als Dialog
           └─ Speichert JSON mit entry_expression
```

---

## 🧪 Wie testen?

### Test 1: Button ist sichtbar
1. Starte OrderPilot-AI
2. Öffne Chart (z.B. BTCUSDT)
3. Klicke "Trading Bot" Button (oben rechts)
4. Wechsle zu "Bot" Tab
5. ✅ Button "Start Bot (JSON)" sollte sichtbar sein (blau, zwischen Start Bot und Stop Bot)

### Test 2: File Picker funktioniert
1. Klicke "Start Bot (JSON)"
2. ✅ File Picker öffnet sich
3. ✅ Pfad: `03_JSON/Entry_Analyzer/Regime/`
4. Wähle eine JSON **MIT** entry_expression
5. ✅ Info-Dialog: "JSON geladen"

### Test 3: JSON ohne entry_expression
1. Klicke "Start Bot (JSON)"
2. Wähle JSON **OHNE** entry_expression
3. ✅ Fehler-Dialog: "Keine entry_expression vorhanden"

### Test 4: Bot startet (noch ohne Entry-Logik!)
1. Wähle JSON MIT entry_expression
2. ✅ Bot Status: "RUNNING (JSON Entry)"
3. ✅ Start Bot Button disabled
4. ✅ Stop Bot Button enabled
5. ⚠️ Entry-Signale werden NOCH NICHT generiert (BotController fehlt)

---

## 📋 TODO-Liste für vollständige Integration

### Phase 1: BotController (KRITISCH!)
- [ ] `BotController.set_json_entry_config()` implementieren
- [ ] JsonEntryScorer initialisieren
- [ ] CEL Expression evaluieren nach jeder Candle
- [ ] Regime-Analyse triggern
- [ ] Entry-Signal generieren bei CEL match
- [ ] Signal an UI senden (_on_bot_signal)

### Phase 2: Entry Analyzer Integration (UX)
- [ ] Button "Add Entry Expression" im Entry Analyzer Regime Tab
- [ ] Öffnet Regime Entry Expression Editor als Dialog
- [ ] Speichert JSON mit entry_expression direkt

### Phase 3: Testing & Validation
- [ ] Backtest mit JSON Entry
- [ ] Paper Mode Trading
- [ ] Live Mode Trading (vorsichtig!)
- [ ] Vergleich: Normaler Bot vs JSON Entry Bot

---

## 🎯 Nächster Schritt

**OPTION 1:** Ich implementiere die BotController Integration
- Pro: Komplettes Feature
- Con: Braucht Verständnis der BotController-Architektur
- Zeit: ~2-3h

**OPTION 2:** Du testest erstmal den Button & UI
- Pro: Siehst dass Button funktioniert
- Con: Entry-Logik fehlt noch
- Zeit: 5 Min

**OPTION 3:** Ich integriere den Editor in Entry Analyzer
- Pro: Bessere UX
- Con: Entry-Logik fehlt trotzdem
- Zeit: ~1h

---

## 📖 Code-Locations

### UI & Button
```
src/ui/widgets/chart_window_mixins/
  ├─ bot_ui_control_widgets.py        # Button erstellt
  ├─ bot_event_handlers.py            # _on_bot_start_json_clicked
  └─ bot_callbacks_lifecycle_mixin.py # _start_bot_with_json_entry
```

### Bot Pipeline (schon fertig!)
```
src/ui/widgets/chart_window_mixins/
  └─ bot_callbacks_signal_mixin.py    # _on_bot_signal (füllt Tabelle, etc.)
```

### JSON Entry System (fertig!)
```
src/ui/widgets/
  ├─ regime_json_parser.py            # JSON Parser
  ├─ entry_expression_generator.py    # Expression Generator
  ├─ regime_json_writer.py            # JSON Writer
  └─ regime_entry_expression_editor.py # GUI Editor

src/core/tradingbot/
  ├─ json_entry_loader.py             # JsonEntryConfig
  ├─ json_entry_scorer.py             # JsonEntryScorer
  └─ cel_engine.py                     # CEL Evaluation
```

---

## ❓ Fragen?

Wenn etwas unklar ist, schau in:
- `docs/WHERE_TO_FIND_REGIME_ENTRY_EDITOR.md`
- `docs/REGIME_ENTRY_EDITOR_GUIDE.md`
- `Help/entry_analyzer/WORKFLOW_KORREKTUR.md`

---

**Status:** 🟡 MVP - UI fertig, BotController Integration fehlt  
**Autor:** Claude Code  
**Letzte Änderung:** 2026-01-29
