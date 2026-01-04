# ✅ Checkliste: KI-Analysemodul (Popup) in bestehender Trading-Software (PyQt6)

**Ziel:** Implementierung eines **reinen Analyse-Moduls** (keine Orderausführung) als **Popup**, das von jeder Chartseite aus geöffnet werden kann und **bestehende Module** (ChartWindowManager, Provider-Logik, EventBus, Indikator-Engine, Settings) wiederverwendet.

---

## 🛠️ CODE-QUALITÄTS-STANDARDS (vor jedem Task lesen!)

### ✅ ERFORDERLICH (für jeden Task)
- [ ] Vollständige Implementation (keine TODOs/Platzhalter)
- [ ] Robustes Error Handling (keine „silent fails“)
- [ ] Input Validation (alle Eingaben & API-Antworten validieren)
- [ ] Type Hints (alle neuen Funktionen/Klassen)
- [ ] Docstrings (public API)
- [ ] Logging (DEBUG/INFO/WARN/ERROR sauber)
- [ ] Tests (Unit-Tests für neue Module)
- [ ] Integration ohne Regression (Chart/Streaming/Indikatoren dürfen nicht leiden)

### ❌ VERBOTEN
- [ ] `# TODO: ...` im finalen Code
- [ ] Auskommentierter Altcode
- [ ] `except: pass`
- [ ] Hardcoded Keys/URLs/Model-IDs (gehört in Settings)
- [ ] Vage Exceptions ohne Kontext

---

## 📊 Status-Legende
- ⬜ Offen / Nicht begonnen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Fehler / Blockiert
- ⭐ Übersprungen / Nicht benötigt

---

## 🧾 Tracking-Format (PFLICHT)

### Erfolgreicher Task
```markdown
- [ ] **X.Y.Z Task Name**
  Status: ✅ Abgeschlossen (YYYY-MM-DD HH:MM) → Kurzbeschreibung
  Code: `dateipfad:zeilen` (wo implementiert)
  Tests: `test_datei:TestClass/TestFunc` (welche Tests)
  Nachweis: Screenshot/Log-Ausgabe/Beispiel-JSON
```

### Fehlgeschlagener Task
```markdown
- [ ] **X.Y.Z Task Name**
  Status: ❌ Fehler (YYYY-MM-DD HH:MM) → Fehlerbeschreibung
  Fehler: Exakte Error Message
  Ursache: Root Cause
  Lösung: Fix-Plan
  Retry: Geplant für YYYY-MM-DD HH:MM
```

---

# Phase 0: Architektur-Fixierung & Minimal-Schnittstellen (Pflicht)

- [ ] **0.1 Analyse-Popup Zieldefinition (nur Analyse, keine Orders)**  
  Status: ⬜ → Ergebnisformat (JSON), UI-Anforderungen, Trigger-Button je Chartseite.

- [ ] **0.2 Modul-Schnittstellen festlegen (sauber & testbar)**  
  Status: ⬜ → Definiere Klassen/Interfaces:
  - `AIAnalysisEngine` (Orchestrator)
  - `DataValidator`
  - `RegimeDetector`
  - `FeatureEngineer`
  - `PromptComposer`
  - `OpenAIClient`
  - `AIResultParser` (optional getrennt)

- [ ] **0.3 Dateistruktur in bestehender Repo-Struktur planen**  
  Status: ⬜ → Vorschlag (anpassbar an deine Struktur):
  - `src/ui/ai_analysis_window.py`
  - `src/core/ai_analysis/engine.py`
  - `src/core/ai_analysis/validators.py`
  - `src/core/ai_analysis/regime.py`
  - `src/core/ai_analysis/features.py`
  - `src/core/ai_analysis/prompt.py`
  - `src/core/ai_analysis/openai_client.py`
  - `src/core/ai_analysis/types.py` (Pydantic Models für Input/Output)
  - `tests/test_ai_analysis_*.py`

---

# Phase 1: UI-Integration (Popup pro Chartseite)

## 1.1 Einstiegspunkt im Chart (Toolbar/Buttons)
- [ ] **1.1.1 „AI Analyse“-Button in bestehender Toolbar hinzufügen**  
  Status: ⬜ → Integration in `toolbar_mixin` / ChartWindow Toolbar.  
  **DoD:** Button sichtbar, klickbar, löst Popup-Open aus.

- [ ] **1.1.2 Popup-Open über ChartWindowManager-Semantik (pro Symbol genau 1 Popup)**  
  Status: ⬜ → Analog zu „ein Fenster pro Symbol“: Beim Öffnen existierendes AI-Popup fokussieren.  
  **DoD:** Kein Popup-Spam, sauberes Fokussieren.

## 1.2 AIAnalysisWindow (UI)
- [ ] **1.2.1 `AIAnalysisWindow` erstellen (PyQt6 Dialog/Window)**  
  Status: ⬜ → UI-Elemente:
  - Dropdown: Provider (über vorhandene Provider-Settings)
  - Dropdown: Modell (aus Settings)
  - Button: „Analyse starten“
  - Status/Spinner
  - Ergebnis-Panel (formatiert + Raw JSON)

- [ ] **1.2.2 Signal/Slot: „Analyse starten“ → Engine-Call (non-blocking)**  
  Status: ⬜ → UI darf nicht einfrieren (QThread/async + Qt Signals).

- [ ] **1.2.3 Ergebnisanzeige + Copy-Button (JSON kopieren)**  
  Status: ⬜ → Praktisch für Debugging/Iteration.

- [ ] **1.2.4 Fehleranzeige (Popup/Inline) + Logging-Verweis**  
  Status: ⬜ → Saubere Meldungen bei fehlendem API-Key, Timeout etc.

---

# Phase 2: Datenzugriff & Preflight (Wiederverwendung bestehender Provider/Streams)

## 2.1 Datenbeschaffung (OHLCV)
- [ ] **2.1.1 Zugriff auf „aktuell geöffneten Chart DataFrame“ definieren**  
  Status: ⬜ → Nutze vorhandene Datenhaltung (Pandas OHLCV) aus Chart-Modul / HistoryProvider / Cache.

- [ ] **2.1.2 Provider-Selection aus Settings übernehmen**  
  Status: ⬜ → Provider pro Fenster ist bereits persistiert: für Analyse-Popup übernehmen/anzeigen.

- [ ] **2.1.3 Lookback/Timeframe übernehmen**  
  Status: ⬜ → Nutze bestehende Period/Timeframe Logik (z.B. `data_loading_mixin._calculate_date_range`).

## 2.2 DataValidator (Preflight + Cleaning)
- [ ] **2.2.1 Timestamp-Check (Lag/Disconnect Erkennung)**  
  Status: ⬜ → Abbruch, wenn letzte Kerze zu alt ist (Interval*1.5 Regel).

- [ ] **2.2.2 Bad Tick Detection (Z-Score) + Bereinigung**  
  Status: ⬜ → Extreme High/Low Werte ersetzen (Median last 3) vor Indicator-Compute.

- [ ] **2.2.3 Null-Volumen Check (Abort)**  
  Status: ⬜ → Volume==0: Analyse abbrechen.

- [ ] **2.2.4 Integration: Validierung vor jedem AI-Call (hart)**  
  Status: ⬜ → Wenn Validator scheitert: kein Prompt, kein API Call.

---

# Phase 3: Deterministische Regime-Erkennung (Python, nicht LLM)

## 3.1 RegimeDetector
- [ ] **3.1.1 Regime-Matrix implementieren (Bull/Bear/Range/Volatility)**  
  Status: ⬜ → Regeln (Beispiel):
  - Bull: `Close > EMA20 > EMA50 > EMA200` AND `ADX14 > 25`
  - Bear: `Close < EMA20 < EMA50 < EMA200` AND `ADX14 > 25`
  - Range: `ADX14 < 20` AND stabile BB-Width
  - Explosive: `ATR14 > SMA(ATR,20)*1.5`

- [ ] **3.1.2 Indikatoren aus bestehender IndicatorEngine wiederverwenden**  
  Status: ⬜ → Keine Doppelimplementierung, vorhandene Indikatorberechnung nutzen.

- [ ] **3.1.3 Regime-Output standardisieren**  
  Status: ⬜ → Enum/String IDs:
  - `STRONG_TREND_BULL`, `STRONG_TREND_BEAR`, `CHOP_RANGE`, `VOLATILITY_EXPLOSIVE`, `NEUTRAL`

---

# Phase 4: Feature Engineering (Token-sparsam, stabil)

## 4.1 FeatureEngineer
- [ ] **4.1.1 EMA-Distance (% zu EMA20 & EMA200)**  
  Status: ⬜ → Als Prozentwert, inkl. „overextended“ Flag.

- [ ] **4.1.2 RSI-State (Overbought/Oversold/Neutral)**  
  Status: ⬜ → Nicht nur Wert, sondern Zustand.

- [ ] **4.1.3 Bollinger %B + Bandwidth**  
  Status: ⬜ → Für Range/Breakout Kontext.

- [ ] **4.1.4 ATR + Volatilitäts-Flags**  
  Status: ⬜ → Für „Explosive“ Regime und Risk-Hinweise.

- [ ] **4.1.5 Struktur-Daten vorbereiten (Pivots/Swings)**  
  Status: ⬜ → Pivots der letzten N Kerzen (HH/HL/LH/LL grob), z.B. per lokaler Extremum-Logik.
  **DoD:** LLM bekommt keine Rohdatenlawine, sondern strukturierte Punkte.

- [ ] **4.1.6 Optional Bitunix-Specials (wenn API verfügbar): Funding/OI Change**  
  Status: ⬜ → Nur wenn ohne Aufwand abrufbar; ansonsten sauber weglassen.

---

# Phase 5: Prompting & Output-Vertrag (JSON rein/raus, strikt)

## 5.1 Pydantic Typen (stabiler Vertrag)
- [ ] **5.1.1 `AIAnalysisInput` Pydantic Model**  
  Status: ⬜ → Felder: Symbol, Timeframe, Period, Regime, Technicals, Structure, LastCandlesSummary.

- [ ] **5.1.2 `AIAnalysisOutput` Pydantic Model**  
  Status: ⬜ → Felder (Pflicht):
  - `setup_detected: bool`
  - `setup_type: str | None`
  - `confidence_score: int` (0–100)
  - `reasoning: str`
  - `invalidation_level: float | None`
  - `notes: list[str]` (optional)

## 5.2 PromptComposer
- [ ] **5.2.1 Prompt-Template definieren (System + User)**  
  Status: ⬜ → System: Rolle/Constraints, Output zwingend JSON, keine Orders.
  User: Input JSON + konkrete Aufgaben:
  - Struktur prüfen (SFP/Absorption)
  - Divergenzen (RSI vs Preis)
  - Regime plausibilisieren
  - Invalidation Level (strukturorientiert)

- [ ] **5.2.2 Token-Budget erzwingen**  
  Status: ⬜ → Nur Features + komprimierte Candle Summary, keine ganzen OHLCV Listen.

- [ ] **5.2.3 Beispiel-Prompts in Repo ablegen (für Regression)**  
  Status: ⬜ → `docs/ai/prompts/` oder ähnlich.

---

# Phase 6: OpenAI-API Integration (neu, robust)

## 6.1 OpenAIClient
- [ ] **6.1.1 Client implementieren (Timeouts, Retries, Rate Limits)**  
  Status: ⬜ → Netzwerkfehler abfangen, Retry mit Backoff.

- [ ] **6.1.2 Settings-Anbindung (AIConfig) nutzen**  
  Status: ⬜ → API-Key, Model, Temperature, MaxTokens aus bestehendem Settings-System.

- [ ] **6.1.3 Response Validierung**  
  Status: ⬜ → Antwort muss JSON sein; invalid → Fehler + log + UI-Message.

- [ ] **6.1.4 Telemetrie/Logging**  
  Status: ⬜ → Logge Request-Metadaten (ohne Key), Latenz, Tokenusage (falls verfügbar).

## 6.2 Ergebnis-Parser
- [ ] **6.2.1 Strict JSON Parser (kein Freitext akzeptieren)**  
  Status: ⬜ → Wenn Modell „labert“: sofort Fehler und „Bitte JSON-only“ (Prompt nachschärfen).

- [ ] **6.2.2 Output Normalisierung**  
  Status: ⬜ → `confidence_score` clamp 0–100, `setup_type` auf Whitelist/Enum prüfen.

---

# Phase 7: Orchestrator (AIAnalysisEngine) & EventFlow

- [ ] **7.1 `AIAnalysisEngine.run(symbol, timeframe, period, provider)` implementieren**  
  Status: ⬜ → Ablauf:
  1) Daten holen (DataFrame)
  2) Validieren/Cleanen
  3) Indikatoren/Regime
  4) Features
  5) Prompt
  6) OpenAI Call
  7) Parse/Validate Output
  8) Signal an UI/EventBus

- [ ] **7.2 Concurrency Guard (pro Symbol nur 1 Analyse gleichzeitig)**  
  Status: ⬜ → Verhindert doppelte Requests.

- [ ] **7.3 Abbruch/Cancel (optional aber empfohlen)**  
  Status: ⬜ → UI kann Analyse abbrechen (wenn Request hängt).

---

# Phase 8: Settings & UX-Defaults

- [ ] **8.1 Defaults festlegen (praxisnah)**  
  Status: ⬜ → Modell-Default, Temperature moderat, MaxTokens begrenzt, Timeout.

- [ ] **8.2 Settings-UI Erweiterung (falls nötig)**  
  Status: ⬜ → API-Key Feld, Model Dropdown, Toggle „AI Analyse aktiv“.

- [ ] **8.3 „AI Ready“ Status in bestehende Statusbar integrieren**  
  Status: ⬜ → Analog zu vorhandenem „AI: Ready“ – aber für Analyse-Popup.

---

# Phase 9: Tests (Unit + Integration, Pflicht)

## 9.1 Unit-Tests
- [ ] **9.1.1 DataValidator Tests (Timestamp/Z-Score/NullVol)**  
  Status: ⬜
- [ ] **9.1.2 RegimeDetector Tests (Bull/Bear/Range/Explosive)**  
  Status: ⬜
- [ ] **9.1.3 FeatureEngineer Tests (EMA-Dist/RSI-State/%B)**  
  Status: ⬜
- [ ] **9.1.4 PromptComposer Tests (JSON-Struktur & Pflichtfelder)**  
  Status: ⬜
- [ ] **9.1.5 Output Parser Tests (valid/invalid JSON, missing fields)**  
  Status: ⬜

## 9.2 Integration-Tests (mit Mock OpenAI)
- [ ] **9.2.1 Engine End-to-End (Mock API Response)**  
  Status: ⬜ → Engine liefert `AIAnalysisOutput`, UI kann anzeigen.

- [ ] **9.2.2 Regression: Chart/Streaming läuft weiter bei geöffnetem Popup**  
  Status: ⬜ → Keine Blockaden, keine EventBus-Leaks.

---

# Phase 10: Abnahme / Definition of Done

- [ ] **10.1 Manuelle Abnahme (Live-Chart)**  
  Status: ⬜ → Popup öffnen, Analyse starten, Ergebnis kommt reproduzierbar.

- [ ] **10.2 Robustheit**  
  Status: ⬜ → Offline/Timeout/RateLimit sauber abgefangen, UI bleibt responsiv.

- [ ] **10.3 Keine Orders**  
  Status: ⬜ → Verifiziert: keine Broker/Order Calls aus Analyse-Pfad.

- [ ] **10.4 Dokumentation**  
  Status: ⬜ → Kurz-Doku:
  - Was wird an LLM geschickt (Features)
  - Output-Vertrag (JSON)
  - Troubleshooting (Keys/Timeouts)

---

## 📌 Integrationspflicht: vorhandene Module wiederverwenden

- **Provider-Auswahl & Persistenz:** vorhandene QSettings/Provider-Settings nutzen  
- **EventBus:** vorhandene MARKET_BAR / MARKET_DATA_TICK Events **nur lesen**, nicht verändern  
- **Indikatoren:** bestehende IndicatorEngine/`indicator_mixin` nutzen, nicht duplizieren  
- **Window-Handling:** analog zu ChartWindowManager „pro Symbol eine Instanz“  
- **UI-Pattern:** bestehende Dialog-/Popup-Konventionen der App übernehmen
