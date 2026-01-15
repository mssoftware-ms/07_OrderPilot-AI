# ✅ Checkliste: Chart-Markierungen & Multi-Chart in OrderPilo-AI

**Start:** 2026-01-01  
**Letzte Aktualisierung:** 2026-01-01  
**Gesamtfortschritt:** 0% (0/52 Tasks)

---

## 🛠️ CODE-QUALITÄTS-STANDARDS (vor jedem Task lesen!)

### ✅ ERFORDERLICH für jeden Task
1. **Vollständige Implementierung** – keine halbfertigen Flows
2. **Robustes Error Handling** – keine Silent Failures (Python *und* JS)
3. **Input Validation** – jede Nachricht/Option vom Backend ans Frontend validieren
4. **Type Hints** – Python: vollständig, JS/TS: soweit möglich (JSDoc/TS)
5. **Logging** – nachvollziehbare Logs (Backend + Frontend Console-Bridge)
6. **Deterministische Render-Pipeline** – Idempotenz: State → Render ohne Nebenwirkungen
7. **Tests** – Unit + Integration (mind. Smoke-Test je Overlay-Typ)
8. **Performance-Regeln** – Marker/Zonen gebündelt rendern, keine per-Tick Neuberechnung

### ❌ VERBOTEN
1. **Platzhalter im Produktivpfad** (z. B. „TODO später“)  
2. **`except: pass` / verschluckte Promise-Rejections**  
3. **Hardcoded UI-Werte ohne Settings** (Farben/Opacity/Shapes nur als Defaults)  
4. **UI ohne Bedien- oder Abschaltmöglichkeit** (jede Overlay-Kategorie muss toggelbar sein)  
5. **State-Divergenz** (Backend- und Frontend-State dürfen nicht auseinanderlaufen)

### 🔍 BEFORE MARKING COMPLETE
- [ ] Feature läuft end-to-end (Backend → Frontend → Chart sichtbar)
- [ ] Keine offenen TODOs im relevanten Pfad
- [ ] Error Handling + Logging vorhanden
- [ ] Validierung greift (invalid payload wird sauber abgewiesen)
- [ ] Tests vorhanden und grün
- [ ] Performance geprüft (Batching statt Einzel-Calls)

---

## 📊 Status-Legende
- ⬜ Offen / Nicht begonnen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Fehler / Blockiert
- ⭐ Übersprungen / Nicht benötigt

---

## 🛠️ TRACKING-FORMAT (PFLICHT)

### Erfolgreicher Task
```markdown
- [ ] **1.2.3 Task Name**  
  Status: ✅ Abgeschlossen (YYYY-MM-DD HH:MM) → *Was wurde implementiert*
  Code: `dateipfad:zeilen` (wo implementiert)
  Tests: `test_datei:TestClass/TestFn` (welche Tests)
  Nachweis: Screenshot/Log-Ausgabe der Funktionalität
```

### Fehlgeschlagener Task
```markdown
- [ ] **1.2.3 Task Name**  
  Status: ❌ Fehler (YYYY-MM-DD HH:MM) → *Fehlerbeschreibung*
  Fehler: `Exakte Error Message hier`
  Ursache: Was war das Problem
  Lösung: Wie wird es behoben
  Retry: Geplant für YYYY-MM-DD HH:MM
```

### Task in Arbeit
```markdown
- [ ] **1.2.3 Task Name**  
  Status: 🔄 In Arbeit (Start: YYYY-MM-DD HH:MM) → *Aktueller Fortschritt*
  Fortschritt: 60% – Backend-DTOs fertig, Frontend-Rendering ausstehend
  Blocker: Keine / <Beschreibung>
```

---

## Phase 0: Vorbereitung & Architektur (MVP-fähig machen)

- [ ] **0.1 Anforderungen finalisieren (Overlay-Katalog & UX-Regeln)**  
  Status: ⬜ → *Shapes, Farben, Positionen, Tooltip-Regeln, Toggle-Logik fixieren*
- [ ] **0.2 Frontend-Integration klären (QWebEngine + LWC Build/Bundle)**  
  Status: ⬜ → *Wie JS/TS ausgeliefert wird, Versionierung, Cache-Busting*
- [ ] **0.3 Backend↔Frontend Message-Contract definieren (JSON Schema)**  
  Status: ⬜ → *Einheitliche Events: entry_markers, zones, structure_breaks, stop_loss, layout*
- [ ] **0.4 „Chart Overlay Store“ entwerfen (Single Source of Truth)**  
  Status: ⬜ → *State-Objekt + Reducer/Updater, Idempotenz-Rendering*
- [ ] **0.5 Telemetrie/Logging-Brücke**  
  Status: ⬜ → *JS console → Python logger (optional), saubere Fehlermeldungen*
- [ ] **0.6 Test-Daten & Smoke-Test Harness**  
  Status: ⬜ → *Fixture-Kerzen + Beispiel-Events, automatisierbarer Start*

---

## Phase 1: Automatische Einstiegspfeile (Long/Short)

- [ ] **1.1 DTO/Model: EntryMarker (time, price, type, label, color, position, id)**  
  Status: ⬜ → *Backend-Datenmodell + Validierung*
- [ ] **1.2 Backend: Signal→Marker-Mapper**  
  Status: ⬜ → *Strategie-/Signalmodul liefert Events, Mapper erzeugt Marker-Liste*
- [ ] **1.3 Transport: Event-Push an Frontend (Batch-fähig)**  
  Status: ⬜ → *Ein Aufruf pro Update, keine Einzelmarker-Spam*
- [ ] **1.4 Frontend: Render EntryMarker via `createSeriesMarkers`**  
  Status: ⬜ → *Marker setzen/ersetzen (State-Driven)*
- [ ] **1.5 Frontend: Tooltip/Label Verhalten**  
  Status: ⬜ → *Hover zeigt Zeit/Preis/Signalinfo – lesbar, ohne Chart zu überdecken*
- [ ] **1.6 Settings: Farben/Shapes/Ein-Aus (UI + Persistenz)**  
  Status: ⬜ → *Defaults + Nutzer-Konfiguration (z. B. QSettings/JSON)*
- [ ] **1.7 Performance: Marker-Batching & Diff-Update**  
  Status: ⬜ → *Nur Änderungen senden/rendern*
- [ ] **1.8 Tests: Validierung + Rendering-Smoke**  
  Status: ⬜ → *Backend-Unit + Frontend-Smoke (Headless falls möglich)*

---

## Phase 2: Strukturbrüche (BoS / CHoCH)

- [ ] **2.1 DTO/Model: StructureBreak (type, time, price, direction, id)**  
  Status: ⬜ → *Backend-Datenmodell + Validierung*
- [ ] **2.2 Backend: Swing-Point Provider anbinden (oder Stub/Manual-Mode)**  
  Status: ⬜ → *Saubere Schnittstelle: `ISwingProvider` / `IMarketStructureDetector`*
- [ ] **2.3 Backend: BoS/CHoCH-Detektion implementieren (konfigurierbar)**  
  Status: ⬜ → *Regeln + Parameter (min swing size, confirmation, etc.)*
- [ ] **2.4 Frontend: BoS/CHoCH als Marker (Shape + Text)**  
  Status: ⬜ → *Optisch klar unterscheidbar, farblich konsistent*
- [ ] **2.5 Legende/Overlay-Layer UI**  
  Status: ⬜ → *Legende im Chartfenster + Toggle*
- [ ] **2.6 Tests: Detektor-Unit-Tests + Rendering-Smoke**  
  Status: ⬜ → *Fälle: bullish/bearish, edge-cases, duplicate events*

---

## Phase 3: Stop-Loss-Linie (+ Risiko-Anzeige)

- [ ] **3.1 DTO/Model: StopLossState (price, label, show_risk, entry_price?)**  
  Status: ⬜ → *Backend-Datenmodell + Validierung*
- [ ] **3.2 Backend: Updates (Set/Update/Clear) inkl. Debounce**  
  Status: ⬜ → *Keine Flackerei bei schnellen Updates*
- [ ] **3.3 Frontend: `createPriceLine` Overlay (draw/update/remove)**  
  Status: ⬜ → *Referenz halten, sauber entfernen/neu zeichnen*
- [ ] **3.4 Risiko-Berechnung (Prozent / R-Multiple) und Anzeige-Regeln**  
  Status: ⬜ → *Saubere Rundung, optionales Label, keine UI-Überladung*
- [ ] **3.5 Optional: Risiko-Bereich visualisieren (zwischen Entry und SL)**  
  Status: ⬜ → *Nur wenn ohne Plugin sauber möglich – sonst später in Phase 4*
- [ ] **3.6 Settings: Stil (Farbe, Strich, Dicke, Label-Text)**  
  Status: ⬜ → *Persistenz + Theme-Kompatibilität*
- [ ] **3.7 Tests: StopLoss Update-Flow + Grenzfälle**  
  Status: ⬜ → *NaN/None, negative Preise, fehlender Entry*

---

## Phase 4: Support-/Resistance-Zonen (halbtransparente Rechtecke)

- [ ] **4.1 Technische Entscheidung: Primitive-Plugin vs. Workaround (LWC)**  
  Status: ⬜ → *Proof: läuft stabil im eingebetteten WebView*
- [ ] **4.2 Frontend: Rectangle Primitive integrieren (attachPrimitive)**  
  Status: ⬜ → *Build/Bundle, API kapseln*
- [ ] **4.3 DTO/Model: Zone (type, start/end time, top/bottom price, style, id)**  
  Status: ⬜ → *Backend-Datenmodell + Validierung*
- [ ] **4.4 Backend: CRUD für Zonen (Create/Update/Delete/List)**  
  Status: ⬜ → *Persistenz (QSettings/JSON-Datei), pro Symbol/Timeframe*
- [ ] **4.5 Frontend: Rendering Layer für Zonen (State-Driven)**  
  Status: ⬜ → *Mehrere Zonen, Reihenfolge, Re-Render ohne Doppelte*
- [ ] **4.6 UI: Manuelles Erstellen (2-Klick-Modus) + Abbrechen**  
  Status: ⬜ → *Startpunkt/Endpunkt, Snap optional, UX sauber*
- [ ] **4.7 UI: Editieren (Drag Handles) + Löschen (Context Menu)**  
  Status: ⬜ → *Nur wenn stabil; sonst in Phase 6 nachziehen*
- [ ] **4.8 Settings: Farben/Opacity je Zonentyp**  
  Status: ⬜ → *Theme-fähig, Defaults sinnvoll*
- [ ] **4.9 Tests: Zone-Serializer + Render-Smoke**  
  Status: ⬜ → *Roundtrip JSON, Mehrfachzonen, ungültige Werte*

---

## Phase 5: Multi-Chart & Multimonitor

- [ ] **5.1 ChartManager: Mehrere Chart-Instanzen verwalten (IDs, Lifecycle)**  
  Status: ⬜ → *Create/Destroy, Memory-Leaks vermeiden*
- [ ] **5.2 UI: Multi-Chart Layout (Tabs/Docks/Fenster) definieren**  
  Status: ⬜ → *Minimal: 2 Charts parallel, getrennte Overlays pro Chart*
- [ ] **5.3 Layout-State (timeframe, symbol, monitor, geometry) speichern/laden**  
  Status: ⬜ → *Persistenz + Fallback bei Monitorwechsel*
- [ ] **5.4 Multimonitor: Fensterpositionierung pro Screen**  
  Status: ⬜ → *Screen-Enumeration, DPI/Scaling berücksichtigen*
- [ ] **5.5 Optional: Synchronisation (Crosshair + VisibleRange)**  
  Status: ⬜ → *Togglebar, nicht erzwungen*
- [ ] **5.6 Backend: Routing von Events an richtige Chart-ID**  
  Status: ⬜ → *Kein Overlay-Leak auf falschen Chart*
- [ ] **5.7 Tests: Multi-Chart Smoke + Cleanup**  
  Status: ⬜ → *Fenster schließen/öffnen, State bleibt konsistent*

---

## Phase 6: Qualität, Doku, Release-Ready

- [ ] **6.1 End-to-End Demo-Szenario (Fixtures) + Screenshots**  
  Status: ⬜ → *Für jede Overlay-Kategorie ein reproduzierbares Beispiel*
- [ ] **6.2 Robustheit: Fehlerfälle (fehlende Daten, Zeitformat, None)**  
  Status: ⬜ → *Saubere Fehlermeldungen, keine Abstürze*
- [ ] **6.3 Performance-Profiling (Marker/Zonen bei großen Datenmengen)**  
  Status: ⬜ → *Ziel: keine UI-Lags, kein übermäßiger GC/CPU*
- [ ] **6.4 Dokumentation: Entwickler-Doku (Contract, State, Rendering)**  
  Status: ⬜ → *Wie neue Overlays ergänzt werden*
- [ ] **6.5 Benutzer-Doku: Bedienung (Toggle, Zone-Edit, Multi-Chart)**  
  Status: ⬜ → *Kurzanleitung + Screens*
- [ ] **6.6 Release Checklist (Version, Changelog, Migration von Settings)**  
  Status: ⬜ → *Wiederholbar und sauber*

---

## 📈 Fortschritts-Tracking

### Gesamt-Statistik
- **Total Tasks:** 52
- **Abgeschlossen:** 0 (0%)
- **In Arbeit:** 0 (0%)
- **Offen:** 52 (100%)

---

## 🔥 Kritische Pfade (Realistisch & hart)

1. **Contract + Store (Phase 0.3–0.4)** blockiert alles Weitere (sonst Chaos/State-Drift).  
2. **Zones (Phase 4.1–4.2)** hängt stark von der Plugin-Lauffähigkeit im WebView ab.  
3. **Multi-Chart (Phase 5.1–5.6)** ist ein Architekturthema – früh sauber lösen, sonst später teuer.

---

## 📝 Risiken & Gegenmaßnahmen

1. **LWC-Plugin läuft nicht stabil in QWebEngine** → *Gegenmaßnahme:* früh PoC (4.1), alternative Visualisierung/Layer-Ansatz vorbereiten.  
2. **Performance bei vielen Markern/Zonen** → *Gegenmaßnahme:* Batch-Updates, Diff-Rendering, Limits/Clustering.  
3. **State-Sync Fehler (Backend↔Frontend)** → *Gegenmaßnahme:* Contract-Validierung + Versionierung + idempotentes Rendern.  
4. **Multimonitor/DPI-Probleme** → *Gegenmaßnahme:* Screen-Abstraktion + robustes Geometry-Fallback.

