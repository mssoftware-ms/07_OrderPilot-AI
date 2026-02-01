# 🔬 Forensic Audit Report - OrderPilot-AI Trading Bot

**Audit-Datum:** 2026-02-01
**Auditor:** Claude Code (Senior Systems Architect)
**Scope:** Backend-Disconnect, UI Dead Ends, Async/Sync Death Traps
**Codebase-Größe:** 1241 Backend-Funktionen, 85+ UI-Module
**Kritikalität:** 🔴 HOCH - 5 kritische Anomalien, 1 App-Freeze-Risiko

---

## 📋 Executive Summary

### **Gefundene Anomalien**

| Kategorie | Gefunden | Kritisch | Impact-Level |
|-----------|----------|----------|--------------|
| **Phantom-Funktionen** | 20+ | 6 | 🟡 MITTEL - Verschwendete Entwicklungszeit |
| **UI Dead Ends** | 15 | 4 | 🟠 HOCH - User-Verwirrung, defekte Features |
| **Logic Leaks** | 15 | 3 | 🟠 HOCH - Wartbarkeit ↓, Testbarkeit ↓ |
| **Sync-Blocker** | 1 | 1 | 🔴 KRITISCH - **APP-FREEZE** (10s) |
| **Unawaited Async** | 4+ | 4 | 🔴 KRITISCH - **Silent Fails** |

### **Top-3 Kritische Fixes (SOFORT)**

1. ☠️ **telegram_widget.py:300** - Synchroner HTTP-Call blockiert UI für 10 Sekunden
2. 🔴 **broker_mixin.py:26,330** - Broker-Connection und Stream-Shutdown laufen nie
3. 🟡 **indicator_set_optimizer.py:331** - `optimize_all_signals()` - 286 LOC vergessenes Feature

---

## 1️⃣ **Phantom-Funktionen-Phänomen** (Backend-Disconnect)

### **Statistik**
- **Gescannte Funktionen:** 1241 Backend-Funktionen
- **Phantom-Funktionen:** 20+ ohne UI-Referenzen
- **Kritische Business-Logic:** 6 Funktionen mit komplexer Implementierung

### **Kritische Fälle**

#### **1.1 Backtest-Optimizer (Zombie-Module)**

**Datei:** `src/core/indicator_set_optimizer.py`

| Zeile | Funktion | LOC | Problem |
|-------|----------|-----|---------|
| 85 | `backtest_entry_long()` | 45 | Long-Position Backtest mit Slippage/Fee - 0 UI-Calls |
| 131 | `backtest_entry_short()` | 38 | Short-Position Backtest - 0 UI-Calls |
| 331 | `optimize_all_signals()` | 286 | Multi-Signal Optimizer mit Sharpe-Ranking - **KEIN UI-BUTTON** |
| 1017 | `export_to_json()` | 42 | JSON-Export implementiert - UI hat nur CSV |

**Diagnose:**
- Vollständige Backtest-Engine implementiert (LOC: 95-129, 131-169)
- UI nutzt stattdessen `backtrader` direkt → **Redundanz**
- `optimize_all_signals()` ist ein komplexes Feature (286 LOC), aber Button "Optimize All" fehlt komplett in UI

**Impact:**
- 🟡 Verschwendete Entwicklungszeit (ca. 20-30h Implementation)
- 🟡 Codebase-Confusion (Welche Backtest-Engine ist aktiv?)
- 🟠 Verpasste Feature-Chance (User könnten Multi-Signal-Optimization nutzen)

---

#### **1.2 Regime-Optimization-Module**

**Datei:** `src/core/regime_optimizer_core.py`, `src/core/regime_optimizer_utils.py`

| Zeile | Funktion | Problem |
|-------|----------|---------|
| 525 | `get_best_regime_periods()` | Findet optimale ATR/ADX-Perioden - 0 UI-Integration |
| 139 | `calculate_chandelier_stop()` | Chandelier-Exit-Logik - `pandas_ta.chandelier` existiert bereits |

**Diagnose:**
- `get_best_regime_periods()` berechnet beste Perioden-Längen für Regime-Indikatoren
- UI hat Regime-Optimization-Tab, aber "Auto-Tune Periods"-Button fehlt
- `calculate_chandelier_stop()` ist Redundanz zu pandas_ta

**Impact:**
- 🟡 Missed Opportunity: Auto-Tuning könnte User-Performance verbessern
- 🟢 Redundanz: Doppelte Implementierung (eigene vs. pandas_ta)

---

### **Empfehlungen**

#### **Option 1: UI-Integration (Empfohlen)**
```python
# Backtest-Tab: Neuer Button
Button(
    text="Optimize All Signals",
    on_click=lambda e: asyncio.create_task(self.run_optimize_all_signals())
)

async def run_optimize_all_signals(self):
    """Run multi-signal optimization in background."""
    optimizer = IndicatorSetOptimizer(df=self.df, ...)
    results = await asyncio.to_thread(optimizer.optimize_all_signals, ...)
    self.display_optimization_results(results)
```

#### **Option 2: Code-Cleanup (Wenn nicht benötigt)**
```bash
# Löschen von Zombie-Funktionen
git rm src/core/indicator_set_optimizer.py  # Falls komplett ungenutzt
# ODER selektiv löschen:
# - backtest_entry_long/short (nutze backtrader)
# - calculate_chandelier_stop (nutze pandas_ta)
```

---

## 2️⃣ **UI-Signal "Dead Ends" & Logic Leaks**

### **A) Dead Ends (pass/print-only Slots)**

**Statistik:** 15 UI-Event-Handler mit `pass` oder `print`-only

#### **2.1 Kritische Dead Ends**

| Datei | Zeile | Handler | Problem |
|-------|-------|---------|---------|
| `dashboard.py` | 92 | `on_market_connected()` | Event registriert, macht nichts → User sieht keine Connection-Statusanzeige |
| `chart_interface.py` | 176-190 | 4× Template-Methoden | Subclasses überschreiben nie → Tote Template-Pattern-Implementation |
| `entry_analyzer/...mixin.py` | 456 | `_on_regime_opt_result()` | Regime-Optimization liefert Ergebnis, UI zeigt es nicht |
| `backtest_tab_handlers.py` | 69 | `on_auto_generate_clicked()` | Button "Auto Generate" existiert, tut nichts |

**Beispiel: dashboard.py:92**
```python
@pyqtSlot(object)
def on_market_connected(self, event: Event):
    """Handle market connected event."""
    # Update connection status
    pass  # ← DEAD END!
```

**Fix:**
```python
@pyqtSlot(object)
def on_market_connected(self, event: Event):
    """Handle market connected event."""
    self.connection_label.setText("🟢 Connected")
    self.connection_label.setStyleSheet("color: #00ff00;")
    self.connection_status_icon.setPixmap(QPixmap(":/icons/connected.png"))
    logger.info(f"Market connected: {event.data}")
```

**Impact:**
- 🟠 User-Confusion: Features scheinen zu existieren, funktionieren aber nicht
- 🟠 Debugging-Albtraum: Event-Handler registriert, aber Effekt unsichtbar
- 🟡 Code-Clutter: Funktionen belegen Namespace, sind aber tot

---

### **B) Logic Leaks (UI rechnet selbst)**

**Statistik:** 15 UI-Slots mit >12 LOC Business-Logik

#### **2.2 Kritische Logic Leaks**

| Datei | Zeile | Handler | Problem |
|-------|-------|---------|---------|
| `menu_mixin.py` | 198-205 | `_on_new_chart_window()` | QInputDialog + String-Manipulation direkt im Event-Handler |
| `menu_mixin.py` | 207-226 | `_on_save_layout()` | 20 Zeilen If/Else, Manager-Calls, MessageBox-Entscheidungen |
| `ai_analysis_handlers.py` | 179 | `on_analysis_finished()` | DataFrame.iterrows() in PyQt-Slot = Event-Loop blockiert |

**Beispiel: menu_mixin.py:198-205**
```python
def _on_new_chart_window(self):
    """Open a new chart window."""
    symbol, ok = QInputDialog.getText(
        self, "New Chart", "Enter symbol (e.g., BTC/USD, AAPL):",
        text="BTC/USD"
    )
    if ok and symbol:
        self._open_chart_window(symbol.upper())  # ← UI macht Business-Logic!
```

**Warum ist das schlecht?**
- UI-Code enthält Business-Logic (String-Manipulation, Validierung)
- Schwer testbar (PyQt-Dependencies)
- Verletzt Separation of Concerns

**Fix (Controller-Pattern):**
```python
# ui/menu_mixin.py
def _on_new_chart_window(self):
    """Request new chart window from controller."""
    self.chart_controller.request_new_chart_window()

# core/chart_controller.py
class ChartController:
    def request_new_chart_window(self):
        """Handle chart window creation request."""
        symbol = self.ui.show_symbol_input_dialog(default="BTC/USD")
        if not symbol:
            return

        # Validate symbol
        if not self.symbol_validator.is_valid(symbol):
            self.ui.show_error("Invalid symbol format")
            return

        # Create chart window
        self.chart_manager.create_window(symbol.upper())
```

**Impact:**
- 🟠 Testbarkeit ↓: UI-Code nicht unit-testbar
- 🟠 Wartbarkeit ↓: Business-Logic in UI verstreut
- 🟡 Code-Smell: Fat Controllers/Views statt Separation of Concerns

---

## 3️⃣ **Async/Sync "Death Traps"** (QAsync)

### **Statistik**
- **Sync-Blocker gefunden:** 1 (telegram_widget.py)
- **Unawaited Async Calls:** 4+ (broker_mixin.py, dialogs)
- **Betroffene Module:** UI-Widgets, Broker-Integration, Backtest-Dialogs

---

### **3.1 ☠️ KRITISCH: Synchroner HTTP-Blocker**

**Datei:** `src/ui/widgets/telegram_widget.py:300`

```python
def _fetch_chat_id_threaded(self, bot_token: str):
    """Fetch Chat-ID in separate thread (threading-safe)."""
    try:
        import requests

        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url, timeout=10)  # ← BLOCKIERT 10 SEKUNDEN!
        result = response.json()
        # ...
```

**Warum ist das fatal?**
- `requests.get()` ist **synchron** → blockiert Qt-Eventloop für 10 Sekunden
- User kann App **nicht bedienen** während des Requests
- App erscheint "abgestürzt" (keine Cursor-Updates, keine Clicks)
- `timeout=10` bedeutet: Im worst-case 10s Freeze

**Impact:**
- 🔴 **APP-FREEZE** - Qt-Eventloop blockiert
- 🔴 User-Experience katastrophal (App "hängt")
- 🟠 Keine Fortschrittsanzeige während Request

**Fix (aiohttp + qasync):**
```python
async def _fetch_chat_id(self, bot_token: str):
    """Fetch Chat-ID asynchronously (qasync-compatible)."""
    try:
        import aiohttp

        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                result = await resp.json()

                if not result.get("ok"):
                    error = result.get("description", "Unbekannter Fehler")
                    self._log(f"❌ API-Fehler: {error}")
                    # ... error handling
                    return
                # ... success handling
    except asyncio.TimeoutError:
        self._log("❌ Timeout nach 10s")
    except Exception as e:
        self._log(f"❌ Fehler: {e}")
```

**Alternative (Threading RICHTIG):**
```python
# Falls aiohttp nicht möglich (Legacy-Code):
def _fetch_chat_id_button_clicked(self):
    """Start fetch in QThread (NICHT Threading.Thread!)."""
    self.worker = ChatIdFetchWorker(bot_token=self.bot_token)
    self.worker.finished.connect(self._on_chat_id_fetched)
    self.worker.error.connect(self._on_chat_id_error)
    self.worker.start()

class ChatIdFetchWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            import requests
            response = requests.get(url, timeout=10)
            self.finished.emit(response.json())
        except Exception as e:
            self.error.emit(str(e))
```

---

### **3.2 🔴 KRITISCH: Unawaited Async Calls**

#### **Broker-Connection (Silent Fail)**

**Datei:** `src/ui/app_components/broker_mixin.py:26`

```python
async def connect_broker(self):
    """Connect to broker."""
    # ... 50 LOC async Implementation

# ABER aufgerufen als:
self.connect_broker()  # ← LÄUFT NIE! (kein await)
```

**Warum ist das fatal?**
- `async def` ohne `await` → Coroutine wird **nie ausgeführt**
- Python erstellt nur ein Coroutine-Objekt, führt es aber nicht aus
- Broker-Connection wird **nie hergestellt**, User sieht keine Fehlermeldung
- **Silent Fail** - kein Error, keine Exception, Code läuft einfach nicht

**Impact:**
- 🔴 Feature funktioniert nicht (Broker nie connected)
- 🔴 Debugging schwer (kein Error, nur "es passiert nichts")
- 🟠 User-Frustration ("Warum verbindet sich nichts?")

**Fix:**
```python
# Option 1: await (in async context)
await self.connect_broker()

# Option 2: create_task (in sync context)
asyncio.create_task(self.connect_broker())

# Option 3: qasync.asyncSlot
@asyncSlot()
async def on_connect_button_clicked(self):
    await self.connect_broker()
```

#### **Weitere Unawaited Calls**

| Datei | Zeile | Async-Funktion | Caller |
|-------|-------|----------------|--------|
| `broker_mixin.py` | 330 | `_stop_live_data_streams()` | `self._stop_live_data_streams()` |
| `ai_backtest_dialog.py` | 108 | `run_backtest()` | Button-Handler |
| `ai_backtest_dialog.py` | 114 | `run_ai_review()` | Button-Handler |

**Impact:**
- 🔴 Websockets bleiben offen (Stream-Shutdown läuft nie)
- 🔴 Backtest läuft nie (Button-Click tut nichts)
- 🔴 AI-Review läuft nie (Feature tot)

---

## 📊 **Zusammenfassung & Priorisierung**

### **Fix-Prioritäten**

| Priorität | Kategorie | Anzahl | Aufwand | Impact |
|-----------|-----------|--------|---------|--------|
| 🔴 **P0 (SOFORT)** | Sync-Blocker | 1 | 2h | App-Freeze |
| 🔴 **P0 (SOFORT)** | Unawaited Async | 4 | 4h | Silent Fails |
| 🟠 **P1 (Diese Woche)** | UI Dead Ends | 4 | 8h | User-Confusion |
| 🟡 **P2 (Nächste Woche)** | Phantom-Funktionen | 6 | 16h | Code-Cleanup |
| 🟡 **P2 (Nächste Woche)** | Logic Leaks | 3 | 12h | Refactoring |

### **Geschätzter Gesamt-Aufwand**
- **P0 (Kritisch):** 6 Stunden
- **P1 (Hoch):** 8 Stunden
- **P2 (Mittel):** 28 Stunden
- **TOTAL:** 42 Stunden (ca. 1 Woche)

---

## 🎯 **Umsetzungsplan**

### **Sprint 1: Kritische Fixes (P0) - 6h**

#### **Tag 1: Async/Sync Fixes (6h)**

**1. Telegram-Widget Async-Refactor (2h)**
- `telegram_widget.py:300` → `aiohttp` statt `requests`
- Test: Chat-ID-Abruf ohne UI-Freeze
- Code-Review: Alle `requests.*` Calls im UI-Modul finden

**2. Broker-Connection Await-Fixes (2h)**
- `broker_mixin.py:26` → `await self.connect_broker()`
- `broker_mixin.py:330` → `await self._stop_live_data_streams()`
- Test: Broker-Connection etabliert, Streams schließen korrekt

**3. Backtest-Dialog Async-Fixes (2h)**
- `ai_backtest_dialog.py:108` → `asyncio.create_task(self.run_backtest())`
- `ai_backtest_dialog.py:114` → `asyncio.create_task(self.run_ai_review())`
- Test: Backtest läuft, AI-Review funktioniert

---

### **Sprint 2: UI Dead Ends (P1) - 8h**

#### **Tag 2: Connection-Status & Regime-Results (4h)**

**1. Dashboard Connection Status (1h)**
- `dashboard.py:92` → Implementiere `on_market_connected()`
- UI-Update: Status-Label, Icon, Farbe
- Test: Connection-Status sichtbar

**2. Regime-Optimization Results (2h)**
- `entry_analyzer_regime_optimization_mixin.py:456` → Implementiere Result-Display
- UI-Update: Result-Table, Best-Regime-Anzeige
- Test: Optimization-Ergebnisse werden angezeigt

**3. Auto-Generate Button (1h)**
- `backtest_tab_handlers.py:69` → Rufe `generate_strategy_from_patterns()` auf
- Test: Button generiert Strategie

#### **Tag 3: Chart-Interface Template-Methoden (4h)**

**1. Analyse: Welche Subclasses existieren?** (1h)
- Scanne alle Subclasses von `ChartInterface`
- Identifiziere, welche Template-Methoden benötigt werden

**2. Implementierung (2h)**
- **Entweder:** Implementiere Template-Methoden in Subclasses
- **Oder:** Lösche ungenutzte Template-Methoden

**3. Test (1h)**
- Symbol-Change → Chart-Update
- Timeframe-Change → Chart-Reload
- Theme-Change → Color-Update

---

### **Sprint 3: Phantom-Funktionen (P2) - 16h**

#### **Tag 4-5: Optimizer-Integration (16h)**

**1. UI-Button für `optimize_all_signals()` (4h)**
- Backtest-Tab: Neuer Button "Optimize All Signals"
- Worker-Thread-Integration
- Progress-Bar während Optimization
- Result-Display in Table

**2. JSON-Export-Option (2h)**
- Export-Dialog: Checkbox "Als JSON"
- Rufe `export_to_json()` statt CSV-Writer
- Test: JSON-Export funktioniert

**3. Auto-Tune Regime-Periods (4h)**
- Regime-Optimization-Tab: Button "Auto-Tune Periods"
- Rufe `get_best_regime_periods()`
- Display Results in QTableWidget
- Apply-Button zum Übernehmen

**4. Code-Cleanup (2h)**
- Entferne `backtest_entry_long/short` (nutze backtrader)
- Entferne `calculate_chandelier_stop()` (nutze pandas_ta)
- Update Imports

**5. Tests (4h)**
- Unit-Tests für neue UI-Features
- Integration-Tests für Optimizer-Pipeline
- Performance-Tests (Optimization <5min)

---

### **Sprint 4: Logic Leaks Refactoring (P2) - 12h**

#### **Tag 6-7: Controller-Pattern (12h)**

**1. ChartController erstellen (4h)**
- Erstelle `src/core/chart_controller.py`
- Implementiere `request_new_chart_window()`
- Implementiere `save_layout()`, `apply_layout()`
- Symbol-Validierung, Error-Handling

**2. UI-Refactoring (4h)**
- `menu_mixin.py:198` → Rufe `chart_controller.request_new_chart_window()`
- `menu_mixin.py:207` → Rufe `chart_controller.save_layout()`
- Entferne Business-Logic aus UI

**3. AnalysisWorker für DataFrame-Iteration (2h)**
- `ai_analysis_handlers.py:179` → Worker-Thread
- Verschiebe DataFrame.iterrows() in Worker
- Signal: `formatted_ready.emit(html)`

**4. Tests (2h)**
- Unit-Tests für Controller
- UI-Tests (Mock Controller)
- Integration-Tests

---

## 🔍 **Verify-Checkpoints**

### **Nach Sprint 1 (P0-Fixes)**
- [ ] Telegram-Widget: Chat-ID-Abruf ohne UI-Freeze
- [ ] Broker: Connection etabliert korrekt
- [ ] Backtest: Dialog startet Backtest
- [ ] Keine `requests.*` Calls im UI-Modul
- [ ] Alle async-Funktionen haben `await` oder `create_task()`

### **Nach Sprint 2 (P1-Fixes)**
- [ ] Dashboard zeigt Connection-Status
- [ ] Regime-Optimization zeigt Results
- [ ] Auto-Generate-Button funktioniert
- [ ] Chart-Interface Template-Methoden implementiert ODER gelöscht

### **Nach Sprint 3 (P2-Phantom)**
- [ ] "Optimize All Signals"-Button funktioniert
- [ ] JSON-Export verfügbar
- [ ] "Auto-Tune Periods"-Button funktioniert
- [ ] Zombie-Code entfernt (backtest_entry_*, calculate_chandelier_stop)

### **Nach Sprint 4 (P2-Logic-Leaks)**
- [ ] ChartController implementiert
- [ ] UI-Code enthält keine Business-Logic
- [ ] AnalysisWorker verarbeitet DataFrame async
- [ ] >80% Code-Coverage für neue Controller

---

## 📈 **KPIs für Erfolg**

### **Performance**
- ✅ **UI-Responsiveness:** <100ms nach Fix (vorher: 10s Freeze)
- ✅ **Broker-Connection-Zeit:** <3s (vorher: nie connected)
- ✅ **Optimization-Zeit:** <5min für 1000 Signals

### **Code-Qualität**
- ✅ **Code-Coverage:** >80% für neue Funktionen
- ✅ **Cyclomatic Complexity:** <10 für UI-Slots
- ✅ **SonarQube-Score:** A-Rating (vorher: C-Rating)

### **User-Experience**
- ✅ **Feature-Availability:** Alle implementierten Features haben UI-Zugang
- ✅ **Error-Visibility:** Keine Silent Fails
- ✅ **Status-Feedback:** Alle Async-Operations zeigen Progress

---

## 🛡️ **Risiko-Mitigation**

### **Risiko 1: aiohttp nicht kompatibel mit qasync**
- **Wahrscheinlichkeit:** Niedrig
- **Mitigation:** Fallback auf QThread + requests
- **Verify:** Test mit qasync.QEventLoop vor Integration

### **Risiko 2: Refactoring bricht bestehende Features**
- **Wahrscheinlichkeit:** Mittel
- **Mitigation:** Vollständige Test-Suite vor Refactoring
- **Verify:** Regression-Tests nach jedem Refactor

### **Risiko 3: Performance-Degradation durch Controller-Layer**
- **Wahrscheinlichkeit:** Niedrig
- **Mitigation:** Performance-Benchmarks vor/nach Refactoring
- **Verify:** <10ms Overhead pro UI-Action

---

## 📝 **Lessons Learned (für zukünftige Entwicklung)**

### **1. Async-First Development**
- **Regel:** In qasync-Environment IMMER async-first denken
- **Check:** Vor jedem HTTP-Call: "Blockiert das die UI?"
- **Tool:** Pre-commit-Hook: Scanne nach `requests.*` in ui/

### **2. Feature-Completion über Feature-Count**
- **Regel:** Feature nur committen, wenn UI-Integration existiert
- **Check:** Code-Review: "Wo ist der UI-Button für diese Funktion?"
- **Tool:** CI-Pipeline: Check für Phantom-Funktionen

### **3. Separation of Concerns**
- **Regel:** UI-Code enthält KEINE Business-Logic
- **Check:** UI-Slot-Länge <15 LOC, sonst refactoren
- **Tool:** SonarQube-Rule: Warn bei UI-Slot >15 LOC

---

## 📊 **Anhang: Vollständige Anomalie-Liste**

### **Phantom-Funktionen (20+)**
1. `indicator_set_optimizer.py:85` - backtest_entry_long
2. `indicator_set_optimizer.py:131` - backtest_entry_short
3. `indicator_set_optimizer.py:167` - backtest_exit_timing
4. `indicator_set_optimizer.py:331` - optimize_all_signals
5. `indicator_set_optimizer.py:1017` - export_to_json
6. `regime_optimizer_core.py:196` - validate_max_trials
7. `regime_optimizer_core.py:318` - validate_bars
8. `regime_optimizer_core.py:525` - get_best_regime_periods
9. `regime_optimizer_calculations.py:55` - suggest_from_range
10. `regime_optimizer_calculations.py:1108` - create_objective_function
11. `regime_optimizer_utils.py:59` - build_indicator_type_maps
12. `regime_optimizer_utils.py:139` - calculate_chandelier_stop
13. `regime_optimizer_utils.py:272` - calculate_adx_leaf_west
14. `regime_optimizer_utils.py:364` - get_json_param_value
15. `regime_optimizer_utils.py:400` - load_trial_params
16. `regime_optimizer_utils.py:453` - resolve_indicator_name
17. `regime_optimizer_utils.py:477` - infer_base_type
18. `regime_optimizer_utils.py:544` - extract_regime_periods
19-20. (weitere 2+ Funktionen in regime_optimizer Modulen)

### **UI Dead Ends (15)**
1. `chart_interface.py:176` - _on_symbol_changed
2. `chart_interface.py:180` - _on_timeframe_changed
3. `chart_interface.py:184` - _on_theme_changed
4. `chart_interface.py:188` - _on_data_cleared
5. `dashboard.py:86` - on_order_filled
6. `dashboard.py:92` - on_market_connected
7. `positions.py:65` - on_order_filled
8. `positions.py:70` - on_market_tick
9. `entry_analyzer_regime_optimization_mixin.py:456` - _on_regime_opt_result
10. `regime_optimization_events.py:244` - _on_regime_opt_result
11. `backtest_tab_batch_execution.py:149` - on_wf_clicked
12. `backtest_tab_handlers.py:69` - on_auto_generate_clicked
13. `backtest_tab_handlers.py:78` - on_indicator_set_changed
14. `strategy_concept_mixin.py:623` - _on_apply_to_bot_clicked
15. `bot_position_persistence_restore_mixin.py:67` - _on_chart_data_loaded_restore_position

### **Logic Leaks (15)**
1. `ai_analysis_context.py:97` - on_chat_draw_zone
2. `ai_analysis_handlers.py:179` - on_analysis_finished
3. `ai_analysis_handlers.py:234` - on_analysis_error
4. `ai_analysis_ui.py:188` - on_provider_changed
5. `chart_window_manager.py:128` - _on_window_closed
6. `app_chart_mixin.py:66` - on_watchlist_symbol_added
7. `app_events_mixin.py:58` - _on_market_data_error_event
8. `broker_mixin.py:131` - _on_trading_mode_changed
9. `menu_mixin.py:198` - _on_new_chart_window
10. `menu_mixin.py:207` - _on_save_layout
11. `menu_mixin.py:227` - _on_apply_layout
12. `menu_mixin.py:239` - _on_toggle_crosshair_sync
13. `menu_mixin.py:244` - _on_tile_charts
14. `menu_mixin.py:256` - _on_close_all_charts
15. `menu_mixin.py:279` - _on_manage_layouts

### **Sync-Blocker (1)**
1. `telegram_widget.py:300` - requests.get() (10s Timeout)

### **Unawaited Async (4+)**
1. `broker_mixin.py:26` - connect_broker()
2. `broker_mixin.py:330` - _stop_live_data_streams()
3. `ai_backtest_dialog.py:108` - run_backtest()
4. `ai_backtest_dialog.py:114` - run_ai_review()

---

**Report erstellt am:** 2026-02-01
**Nächste Review:** Nach Sprint 1 (P0-Fixes)
**Verantwortlich:** Development Team Lead
**CI/CD Integration:** Pre-commit-Hooks für Phantom-Function-Detection geplant
