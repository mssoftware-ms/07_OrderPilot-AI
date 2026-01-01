# ✅ Checkliste: OrderPilot‑AI – Onvista‑only KO‑Finder (Long/Short) + UI‑Tabelle

**Start:** 2025-12-18
**Letzte Aktualisierung:** 2025-12-18
**Gesamtfortschritt:** 85% 🔄 (Phase 0-6 abgeschlossen, Phase 7-8 pending)

---

## 🛠️ CODE‑QUALITÄTS‑STANDARDS (vor jedem Task lesen!)

### ✅ ERFORDERLICH (Pflicht)
1. **Vollständige Implementierung** – keine TODOs/Platzhalter in produktivem Code
2. **Error Handling** – try/except für alle kritischen Operationen (HTTP, Parsing, IO, UI‑Signals)
3. **Input Validation** – alle User‑Inputs strikt validieren (Ranges, None, NaN, Prozentwerte)
4. **Type Hints** – alle Public APIs typisiert
5. **Docstrings** – alle Public Klassen/Functions dokumentiert (inkl. Side‑Effects)
6. **Logging** – strukturierte Logs (underlying, direction, run_id, url, http_status, parse_version)
7. **Tests** – Unit‑Tests für Parser/Ranking + Integration‑Smoke (optional) für Live‑Fetch
8. **Clean Code** – toter Code raus, keine auskommentierten Blöcke
9. **Dateigrößenlimit** – keine Python‑Datei > 600 Zeilen (bei Bedarf modularisieren)

### ❌ VERBOTEN
- Platzhalter‑Code (`TODO`, Dummy Returns)
- Silent Failures (`except: pass`)
- **Alternative Datenquellen** (keine Emittenten‑Feeds, keine Börsen‑APIs, keine Drittanbieter, keine Broker‑APIs für Derivate)
- „Daten ergänzen“ außerhalb Onvista (keine Heuristiken mit Fremddaten; fehlende Felder ⇒ **Flag** oder **Exclude**)
- UI‑Controls ohne Wirkung / ohne Validierung
- Aggressives Scraping (keine high‑freq Loops, keine parallelen Massenscans, kein unkontrolliertes Paging)

### 🔍 BEFORE MARKING COMPLETE
- [ ] **Onvista‑only garantiert**: Keine Codepfade, die auf andere Provider zugreifen
- [ ] **Refresh‑Flow stabil**: Long+Short parallel, Timeouts/Retry/Circuit‑Breaker aktiv
- [ ] **Parser robust**: HTML‑Änderungen führen zu klaren Fehlermeldungen + Tests schlagen deterministisch an
- [ ] **Ranking reproduzierbar**: Score‑Berechnung deterministisch, parametrierbar, getestet
- [ ] **UI zuverlässig**: Tabellen‑Update, Filter (min Hebel / max Spread), Ladezustände, Fehlerbanner
- [ ] **Meta‑Infos sichtbar**: Datenalter, Fetch‑Zeit, Fehlercodes, Parser‑Confidence
- [ ] **Compliance‑Hinweis**: Disclaimer + Hinweis „Quelle: Onvista“ sichtbar

---

## 📊 Status‑Legende
- ⬜ Offen / Nicht begonnen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Fehler / Blockiert
- ⭐ Übersprungen / Nicht benötigt

---

## 🧾 TRACKING‑FORMAT (PFLICHT)

### Erfolgreicher Task
```markdown
- [ ] **1.2.3 Task Name**
  Status: ✅ Abgeschlossen (YYYY‑MM‑DD HH:MM) → *Was wurde implementiert*
  Code: `src/.../datei.py:zeilen`
  Tests: `tests/.../test_x.py::TestClass::test_name`
  Nachweis: Log‑Ausgabe / Screenshot / JSON‑Response Beispiel (Pfad)
```

### Fehlgeschlagener Task
```markdown
- [ ] **1.2.3 Task Name**
  Status: ❌ Fehler (YYYY‑MM‑DD HH:MM) → *Fehlerbeschreibung*
  Fehler: `Exakte Error Message hier`
  Ursache: *Warum ist es passiert*
  Lösung: *Wie wird es behoben*
  Retry: Geplant für YYYY‑MM‑DD HH:MM
```

---

# Phase 0: Projekt‑Alignment & Nicht‑Verhandelbares (Pflicht)

- [x] **0.1 Onvista‑only Contract festnageln (Hard Rule)**
  Status: ✅ Abgeschlossen (2025-12-18) → *Regelwerk dokumentiert + Code-Guards implementiert*
  Code: `docs/ONVISTA_SCRAPING_NOTES.md`, `src/derivatives/ko_finder/constants.py:DATA_SOURCE`
  - Alle Modelle haben `source="onvista"` Feld
  - Assertions und Flags bei fehlenden Feldern

- [x] **0.2 ToS/Robots/Legal‑Notiz erstellen (Risiko dokumentieren)**
  Status: ✅ Abgeschlossen (2025-12-18) → *ONVISTA_SCRAPING_NOTES.md erstellt*
  Code: `docs/ONVISTA_SCRAPING_NOTES.md`
  - Rate-Limiting dokumentiert (1 req/sec)
  - Disclaimer in UI integriert

- [x] **0.3 Integrationspunkte im aktuellen Codebase‑Stand identifizieren**
  Status: ✅ Abgeschlossen (2025-12-18) → *UI-Ort: ChartWindow "Analysis & Strategy" Dock*
  Code: `src/ui/widgets/chart_window_mixins/ko_finder_mixin.py`
  - Neuer Tab "KO-Finder" in PanelsMixin integriert
  - QSettings für Filter-Persistenz

- [x] **0.4 Definition‑of‑Done (DoD) für „KO‑Finder v1"**
  Status: ✅ Abgeschlossen (2025-12-18) → *MVP definiert in Technischem Umsetzungsplan*
  Code: `01_Projectplan/Technischer_Umsetzungsplan_Onvista_KO_Finder.md:336-346`

---

# Phase 1: Domain‑Modelle + Konfiguration (Onvista‑only)

## 1.1 Datenmodelle (Pydantic/Dataclasses)
- [x] **1.1.1 KOFilterConfig (User‑Parameter)**
  Status: ✅ Abgeschlossen (2025-12-18) → *Dataclass mit Validierung + QSettings*
  Code: `src/derivatives/ko_finder/config.py:1-150`
  Tests: `tests/derivatives/ko_finder/test_models.py::TestKOFilterConfig`

- [x] **1.1.2 KnockoutProduct + Quote + UnderlyingSnapshot**
  Status: ✅ Abgeschlossen (2025-12-18) → *Vollständige Modelle mit Flags*
  Code: `src/derivatives/ko_finder/models.py:1-200`
  Tests: `tests/derivatives/ko_finder/test_models.py::TestKnockoutProduct`

- [x] **1.1.3 Ergebnis‑Schema für UI/API (SearchResponse)**
  Status: ✅ Abgeschlossen (2025-12-18) → *SearchResponse + SearchMeta*
  Code: `src/derivatives/ko_finder/models.py:150-220`
  Tests: `tests/derivatives/ko_finder/test_models.py::TestSearchResponse`

## 1.2 Konfig & Defaults
- [x] **1.2.1 Default‑Filterwerte definieren**
  Status: ✅ Abgeschlossen (2025-12-18) → *DEFAULT_* Konstanten*
  Code: `src/derivatives/ko_finder/constants.py:60-75`

- [x] **1.2.2 Issuer‑Mapping (Name → Onvista ID)**
  Status: ✅ Abgeschlossen (2025-12-18) → *Issuer Enum mit IDs*
  Code: `src/derivatives/ko_finder/constants.py:20-40`

---

# Phase 2: Onvista‑Adapter (Fetcher + Parser + Anti‑Fragilität)

## 2.1 URL‑Builder (Listen‑Seiten)
- [ ] **2.1.1 URL‑Builder für Knock‑Out Liste**
  Status: ⬜ Offen → *Parametrisierbar (underlying, direction, issuer_ids, sort, brokerId)*
  - Long‑Beispiel:  
    `https://www.onvista.de/derivate/Knock-Outs?brokerId=8260&feature=STOP_LOSS&idIssuer=53159,54101,53882,53163&order=ASC&sort=spreadAskPct`
  - Short‑Beispiel:  
    `https://www.onvista.de/derivate/Knock-Outs?brokerId=8260&feature=STOP_LOSS&idExerciseRight=1&idIssuer=53159,54101,53882,53163&order=ASC&sort=spreadAskPct`

- [ ] **2.1.2 Underlying‑Routing festlegen**
  Status: ⬜ Offen → *Wie wird vom Chart‑Symbol auf Onvista‑Underlying gefiltert?*
  - Variante A: Onvista‑Underlying‑Slug/Seite + Query‑Parameter
  - Variante B: Onvista‑Suche (nur Onvista!) → ID/Slug ermitteln und cachen
  - Ergebnis: deterministisches Mapping in `config/` (kein Raten im Code)

## 2.2 HTTP‑Fetcher (wartbar, testbar)
- [ ] **2.2.1 OnvistaFetcher implementieren**
  Status: ⬜ Offen → *requests/httpx, definierte Header, Timeout, Retry*
  - Timeouts (connect/read), Retry mit Backoff, max attempts
  - Circuit‑Breaker bei wiederholten Failures
  - Rate‑Limiter global (z. B. min. Abstand zwischen Requests pro Host)

- [ ] **2.2.2 Response‑Capture (Debug‑Modus)**
  Status: ⬜ Offen → *Option: HTML‑Snapshots speichern, aber datensparsam*
  - Nur bei Parser‑Fehlern, mit run_id und timestamp

## 2.3 Parser (HTML → Modelle)
- [ ] **2.3.1 Tabellenparser für KO‑Listen**
  Status: ⬜ Offen → *Robust gegen Spaltenverschiebung*
  - Header‑basierte Spaltenzuordnung (nicht „harte“ Indizes)
  - Extraktion: WKN, Emittent, Bid/Ask, Spread, Hebel, KO‑Level, Laufzeit, Underlying‑Kurs (sofern vorhanden)
  - Normalisierung: Zahlen (Komma/Punkt), Währungen, Prozent

- [ ] **2.3.2 Qualitätslogik: „kein aktueller Kurs“ erkennen**
  Status: ⬜ Offen → *Heuristik nur aus Onvista‑Signalen*
  - Kriterien: fehlender Ask/Bid/Spread, Placeholder „–“, KO‑Verdacht → Flag/Exclude

- [ ] **2.3.3 Parser‑Versionierung + Fallback‑Parser**
  Status: ⬜ Offen → *Schema‑Version + defensive Fallbacks*
  - ParserConfidence (0..1) pro Produkt + global
  - Bei Low‑Confidence: Produkt ausschließen oder deutlich flaggen

## 2.4 Parser‑Tests (Fixtures)
- [ ] **2.4.1 HTML‑Fixtures anlegen (Long/Short)**
  Status: ⬜ Offen → *2–4 realistische Snapshots*
- [ ] **2.4.2 Unit‑Tests: Parser liefert erwartete Felder**
  Status: ⬜ Offen → *Testet Spaltenmapping, Normalisierung, Flags*
- [ ] **2.4.3 Regression‑Test bei HTML‑Änderung**
  Status: ⬜ Offen → *Fail fast + klare Fehlermeldung*

---

# Phase 3: Normalisierung, Hard‑Filter, Ranking/Scoring

## 3.1 Normalizer/Validator
- [ ] **3.1.1 KO‑Abstand berechnen (pct)**
  Status: ⬜ Offen → *Direction‑aware Berechnung, Validierung*
- [ ] **3.1.2 Spread berechnen, falls Onvista‑Feld fehlt**
  Status: ⬜ Offen → *Nur aus Bid/Ask (Onvista), sonst missing_fields*
- [ ] **3.1.3 Produktstatus ableiten (active/inactive)**
  Status: ⬜ Offen → *Regeln dokumentieren + unit tests*

## 3.2 Hard Filters
- [ ] **3.2.1 Filter: min Hebel**
  Status: ⬜ Offen
- [ ] **3.2.2 Filter: max Spread %**
  Status: ⬜ Offen
- [ ] **3.2.3 Filter: Quotes vorhanden + nicht stale**
  Status: ⬜ Offen
- [ ] **3.2.4 Filter: KO plausibel (Abstand > minimaler Schwellenwert)**
  Status: ⬜ Offen

## 3.3 RankingEngine (Score)
- [ ] **3.3.1 Scoring‑Faktoren definieren & dokumentieren**
  Status: ⬜ Offen → *Spread, Hebel‑Nähe, KO‑Abstand‑Band, Quote‑Qualität*
- [ ] **3.3.2 Score implementieren (deterministisch)**
  Status: ⬜ Offen → *Keine Zufallsanteile*
- [ ] **3.3.3 Tie‑Break Regeln**
  Status: ⬜ Offen → *Spread asc, Leverage desc, KO‑Abstand desc*
- [ ] **3.3.4 Unit‑Tests: Ranking ordnet korrekt**
  Status: ⬜ Offen → *Edge‑Cases: missing fields, extreme leverage*

---

# Phase 4: Cache + Refresh‑Flow (maximal aktuell, aber sicher)

## 4.1 Cache (stale‑while‑revalidate)
- [ ] **4.1.1 In‑Memory Cache Struktur**
  Status: ⬜ Offen → *Key: (underlying, direction, filterhash)*
- [ ] **4.1.2 TTL je Datentyp**
  Status: ⬜ Offen → *KO‑Listen kurz (z. B. 15–60s), Underlying‑Mapping länger*
- [ ] **4.1.3 SWR‑Modus implementieren**
  Status: ⬜ Offen → *UI bekommt sofort letztes Ergebnis + Refresh läuft parallel*
  - Optional: „Force Refresh“ ignoriert Cache

## 4.2 Refresh‑Orchestrierung
- [ ] **4.2.1 Long+Short parallel abrufen**
  Status: ⬜ Offen → *asyncio/Threadpool, klare Timeouts*
- [ ] **4.2.2 Partial Results erlauben**
  Status: ⬜ Offen → *Long OK, Short Error ⇒ trotzdem anzeigen + Fehlbanner*
- [ ] **4.2.3 Meta‑Objekt füllen**
  Status: ⬜ Offen → *fetch_time_ms, asOf, errors[], parser_confidence, counts*

---

# Phase 5: UI‑Integration (Tabelle + Filter + Bedienung)

## 5.1 UI‑Widget: KO‑Finder Panel
- [ ] **5.1.1 Neues Panel/Tab designen**
  Status: ⬜ Offen → *Ort festlegen: ChartWindow (Analyse/Strategy) oder Dashboard Dock*
  - UI‑Elemente: Refresh‑Button, Min‑Hebel, Max‑Spread, Issuer‑Chips, Top‑N
  - Statuszeile: „Stand“, „Dauer“, „Quelle: Onvista“, Fehlerhinweise

- [ ] **5.1.2 KO‑Tabelle implementieren**
  Status: ⬜ Offen → *QTableView/QTableWidget, sortierbar*
  - Spalten: WKN, Emittent, Long/Short, Hebel, Spread %, KO‑Level, KO‑Abstand %, Bid/Ask, Score, Flags

- [ ] **5.1.3 Row‑Actions**
  Status: ⬜ Offen → *Usability*
  - Copy WKN/ISIN
  - Open Onvista‑Detailseite im Embedded Browser (QWebEngine)
  - Optional: „In Order‑Dialog übernehmen“ (nur wenn sinnvoll ohne TR‑API)

## 5.2 UI‑Flow: „Aktualisieren“
- [ ] **5.2.1 Ladezustand + Cancel**
  Status: ⬜ Offen → *Spinner, disable controls, optional cancel token*
- [ ] **5.2.2 Fehler‑Banner + Details**
  Status: ⬜ Offen → *HTTP Error, Parsing Error, Rate‑Limit → klare Meldung*
- [ ] **5.2.3 Persistenz der Filter (QSettings)**
  Status: ⬜ Offen → *Filterwerte bleiben nach Neustart erhalten*

## 5.3 Integration in bestehende Fensterstruktur
- [ ] **5.3.1 Wiring in ChartWindow Mixins**
  Status: ⬜ Offen → *Panel registrieren, Signale verbinden*
- [ ] **5.3.2 Event‑Bus optional: „ko.search.completed“**
  Status: ⬜ Offen → *Telemetrie/Logging/Debugging*

---

# Phase 6: Observability, Robustheit, Compliance

- [ ] **6.1 Strukturierte Logs + run_id**
  Status: ⬜ Offen → *Jeder Refresh hat run_id, URLs & Zeiten loggen*
- [ ] **6.2 Schutz vor HTML‑Änderungen (Fail‑Fast)**
  Status: ⬜ Offen → *Fehlermeldung enthält Parser‑Version + erwartete Header*
- [ ] **6.3 Rate‑Limiter zentral**
  Status: ⬜ Offen → *Keine Überlastung, keine Spam‑Refreshes*
- [ ] **6.4 Disclaimer im UI**
  Status: ⬜ Offen → *„Keine Anlageberatung“, „Quelle: Onvista“, Daten können verzögert sein*
- [ ] **6.5 Security: keine sensiblen Daten im Log**
  Status: ⬜ Offen → *Nur URLs/Parameter, keine Tokens/Accounts (sollten ohnehin nicht existieren)*

---

# Phase 7: Tests, QA, Release‑Gates

## 7.1 Unit Tests (Pflicht)
- [ ] **7.1.1 URL‑Builder Tests**
  Status: ⬜ Offen
- [ ] **7.1.2 Parser Tests (Fixtures)**
  Status: ⬜ Offen
- [ ] **7.1.3 Filter/Ranking Tests**
  Status: ⬜ Offen
- [ ] **7.1.4 Cache Tests (TTL/SWR)**
  Status: ⬜ Offen

## 7.2 Integration / Smoke (empfohlen, aber optional)
- [ ] **7.2.1 Live‑Fetch Smoke Test (manuell ausführbar)**
  Status: ⬜ Offen → *Nur als dev‑tool, nicht CI‑pflichtig*

## 7.3 Manual QA (Pflicht vor „fertig“)
- [ ] **7.3.1 Vergleich mit Onvista im Browser**
  Status: ⬜ Offen → *3 Stichproben: WKN/Spread/Hebel stimmen*
- [ ] **7.3.2 Edge‑Cases**
  Status: ⬜ Offen → *Markt geschlossen, Onvista langsam, fehlende Quotes*
- [ ] **7.3.3 UI‑Stabilität**
  Status: ⬜ Offen → *Mehrfach Refresh, Filterwechsel, Fensterwechsel*

---

# Phase 8: Dokumentation & Wartbarkeit

- [ ] **8.1 ARCHITECTURE.md ergänzen (Derivate/KOs)**
  Status: ⬜ Offen → *Ports/Adapters, Datenfluss, Error‑Strategie*
- [ ] **8.2 Developer‑Notes: Onvista Parser Maintenance**
  Status: ⬜ Offen → *Wie Fixtures aktualisieren, wie Parser‑Version bumpen*
- [ ] **8.3 User‑Docs / Tooltips**
  Status: ⬜ Offen → *Was bedeuten Spread/Hebel/KO‑Abstand/Flags*

---

# 🎯 Review‑Checkpoints (hart)

- [ ] **R0: Adapter + Parser liefern valide Modelle (ohne UI)**
- [ ] **R1: Hard‑Filter + Ranking funktionieren (mit Unit‑Tests)**
- [ ] **R2: UI‑Tabelle + Refresh‑Flow stabil**
- [ ] **R3: Cache/Rate‑Limit/Fehlerhandling robust**
- [ ] **R4: Dokumentation + Disclaimer vollständig**

---

## 📝 Notizen / Entscheidungen (wird gepflegt)
- Underlying‑Mapping‑Strategie:
- TTL‑Werte:
- Top‑N Default:
- Minimale KO‑Abstands‑Schwelle:
- Parser‑Schema‑Version:

