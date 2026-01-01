# Technischer Umsetzungsplan: KO‑Produkt‑Suchfunktion (Onvista als einzige Datenquelle)

**Projekt:** OrderPilot‑AI – Onvista‑only KO‑Finder (Long/Short)  
**Stand:** 2025‑12‑18  
**Scope:** Technische Datenintegration + Filter/Ranking + UI‑Tabelle + Refresh‑Flow (manuell per Button)  
**Nicht‑Ziel:** Anlageberatung / Trading‑Empfehlungen

---

## 0. Nicht verhandelbare Regeln (Onvista‑only)

1. **Einzige Datenquelle ist Onvista.**  
   Keine alternativen APIs/Provider (keine Emittenten‑Feeds, keine Börsen‑APIs, keine Drittanbieter, keine Broker‑APIs für Derivate).
2. **Wenn Onvista ein Feld nicht liefert:**  
   **nicht ergänzen**, nicht raten, nicht aus Fremddaten rekonstruieren.  
   Stattdessen: **Flag setzen** (missing/stale/unknown) **oder Produkt ausschließen**.
3. **Scraping ist der Weg** (Webzugriff/Parsing) – aber **gekapselt** (Ports & Adapters), wartbar, testbar, austauschbar.
4. **Refresh nur auf Klick**, kein Polling. Dennoch: Datenstand beim Klick **so aktuell wie technisch möglich** (innerhalb der Onvista‑Limitierungen).

---

## 1) Anforderungs‑Checkliste (Inputs & Constraints)

### 1.1 User‑Inputs (UI‑Parameter)
- **Underlying** (z. B. „NASDAQ 100“)
- **Richtung**: Long & Short (in der UI getrennt oder Tabs)
- **Emittenten**: HSBC, Société Générale, UBS, Vontobel (Standard: alle aktiv)
- **Min. Hebel** (float, z. B. 5.0)
- **Max. Spread** (float, i. d. R. Prozent, z. B. 2.0 %)
- **Top‑N je Richtung** (int, z. B. 10)
- *(optional)* Feature‑Filter (z. B. „mit Stop‑Loss“), sofern Onvista‑Filter stabil verfügbar

### 1.2 Pflichtdaten pro KO‑Produkt (aus Onvista ableitbar)
- WKN (und idealerweise ISIN, falls Onvista zugänglich)
- Emittent
- Long/Short
- KO‑Level (Knock‑Out‑Schwelle)
- Underlying‑Preis (Referenzkurs) **oder** ausreichend Daten zur Ableitung (KO‑Abstand)
- Bid/Ask (Geld/Brief) **oder** Spread% (mindestens eins muss verfügbar sein, sonst Ausschluss)
- Hebel
- Produktstatus / Handelbarkeit (mind. „Quote vorhanden“; sonst Ausschluss)
- Zeitstempel/Meta (fetched_at, as_of, source_url)

### 1.3 Constraints (harte Regeln)
- Nur Emittenten: **HSBC, Société Générale, UBS, Vontobel**
- Nur **handelbare** Produkte:
  - Bid & Ask vorhanden (oder Onvista‑Quote eindeutig valide)
  - Keine „kein aktueller Kurs“/Platzhalter
- Filter:
  - Hebel ≥ min_leverage
  - Spread% ≤ max_spread_pct
- Bei fehlenden Feldern: Flag/Exclude; **kein Fallback auf andere Quellen**

---

## 2) Onvista‑Datenzugriff (Scraping/Parsing) – Onvista‑only

### 2.1 Benötigte Seitentypen (typisch)
1. **KO‑Liste** (gefiltert nach Underlying, Emittenten, Richtung, Sortierung)  
2. *(optional)* **Produkt‑Detailseite** (nur für Top‑N), falls ISIN/Handelszeit/weitere Felder gebraucht werden  
3. *(optional)* **Underlying‑Suche** (Onvista‑Suche) zur stabilen Auflösung von Underlying→Slug/ID

> Ziel: möglichst wenig Requests, stabil und schnell.

### 2.2 Beispiel‑Listen‑URLs (gegeben)
- Long:  
  `https://www.onvista.de/derivate/Knock-Outs?brokerId=8260&feature=STOP_LOSS&idIssuer=53159,54101,53882,53163&order=ASC&sort=spreadAskPct`
- Short:  
  `https://www.onvista.de/derivate/Knock-Outs?brokerId=8260&feature=STOP_LOSS&idExerciseRight=1&idIssuer=53159,54101,53882,53163&order=ASC&sort=spreadAskPct`

**Issuer‑IDs:**  
- HSBC = 53159  
- Société Générale = 54101  
- UBS = 53882  
- Vontobel = 53163

### 2.3 Adapter‑Design (Ports & Adapters)

#### Interface (Port)
```python
class KnockoutDataSource(Protocol):
    async def search_knockouts(self, req: SearchRequest) -> SearchResponse: ...
```

#### Onvista‑Adapter (Adapter)
- `OnvistaFetcher`: HTTP (Timeout/Retry/RateLimit/CircuitBreaker)
- `OnvistaParser`: HTML → Modelle (robust, versioniert)
- `OnvistaNormalizer`: Zahlen/Units/Locale → float, flags setzen
- Alles Onvista‑spezifische bleibt **hier**.

### 2.4 Robustheit gegen HTML‑Änderungen (Anti‑Fragilität)
- **Header‑basiertes Spaltenmapping**: Spalten nicht über feste Indizes, sondern per Tabellenkopf/Bezeichner ermitteln.
- **Schema‑Versioning**: Parser kennt `schema_version`; Änderungen erhöhen Version, Tests erzwingen Update.
- **Fallback‑Parser**: Wenn Standard‑Parser scheitert, zweiter Versuch (z. B. regex‑basierte Extraktion) → ggf. reduzierte Felder + niedriges `parser_confidence`.
- **Parser‑Confidence** pro Produkt und global:
  - z. B. 1.0 wenn alle Pflichtfelder sauber erkannt
  - <0.8 → Produkt automatisch **exclude** oder stark flaggen

### 2.5 HTTP‑Stabilität (Rate‑Limit, Backoff, Timeout)
- Timeout: connect/read (z. B. 5s/10s)
- Retry: max 2–3 Versuche, exponential backoff + jitter
- Circuit‑Breaker: nach n Fehlern → kurze Sperrzeit (z. B. 60s) um UI nicht zu „hämmern“
- Globaler Rate‑Limiter (Host‑basiert): minimaler Abstand zwischen Requests
- User‑Agent setzen (Browser‑ähnlich), Cookies/Session falls nötig

### 2.6 Caching (Refresh per Klick)
- Grundsatz: Klick ⇒ frisch laden.  
- Trotzdem sinnvoll:
  - **stale‑while‑revalidate (SWR)**: UI bekommt sofort letztes Ergebnis (wenn <TTL) + Hintergrundrefresh.
  - TTL kurz: z. B. 15–60s für KO‑Listen.
  - Underlying‑Mapping (Slug/ID) TTL lang: Stunden/Tage.

### 2.7 Legal/ToS/Robots
- Onvista‑Scraping kann ToS‑relevant sein. Vorgehen:
  - **Dokumentieren** (Risiko/Limitierung) in `ONVISTA_SCRAPING_NOTES.md`
  - Frequenz gering halten (kein Polling, keine Massenscans)
  - In UI/Meta: „Quelle: Onvista“ + Hinweis „Daten können verzögert sein“

---

## 3) Datenmodell (App‑Tabelle + Persistenz)

### 3.1 Kernmodelle

#### `KOFilterConfig`
- `min_leverage: float`
- `max_spread_pct: float`
- `issuers: list[str]`
- `top_n: int`
- `broker_id: int` (falls nötig)

#### `UnderlyingSnapshot`
- `symbol/name`
- `price: float | None`
- `currency: str | None`
- `as_of: datetime`
- `source: "onvista"`

#### `Quote`
- `bid: float | None`
- `ask: float | None`
- `spread_pct: float | None`
- `quote_as_of: datetime | None`
- Flags: `stale: bool`, `missing: bool`

#### `KnockoutProduct`
- Identifikation: `wkn`, optional `isin`
- `issuer`, `direction`
- `knockout_level: float | None`
- `leverage: float | None`
- `underlying: UnderlyingSnapshot`
- `quote: Quote`
- Derived:
  - `ko_distance_pct: float | None`
  - `score: float | None`
- Meta/Qualität:
  - `source: "onvista"`
  - `fetched_at: datetime`
  - `source_url: str`
  - `parse_schema_version: str`
  - `parser_confidence: float`
  - `flags: list[str]` (missing_fields, stale_quote, parsing_uncertain, etc.)

### 3.2 Persistenz (optional)
- In‑Memory Cache reicht für v1.  
- Optional SQLite (nur für Debug/History):
  - `knockout_products` + `fetch_runs` (run_id, underlying, criteria, fetch_time, status)

---

## 4) Auswahl‑Algorithmus (Hard Filters + Ranking/Scoring)

### 4.1 Hard Filters (Ausschlusskriterien)
- Issuer in erlaubter Liste
- `quote.bid` & `quote.ask` vorhanden (oder Onvista liefert eindeutigen Spread + Preis)
- `quote.stale == False`
- `leverage >= min_leverage`
- `spread_pct <= max_spread_pct`
- KO plausibel:
  - Long: `knockout_level < underlying_price` (wenn beide vorhanden)
  - Short: `knockout_level > underlying_price`
- KO‑Abstand Mindestschwelle (z. B. > 0.2%) um KO‑„Quasi‑Treffer“ zu meiden
- Wenn Pflichtfeld fehlt → **exclude** (oder je nach Feld: flag + Score‑Malus, aber nur wenn UI es akzeptiert)

### 4.2 Ranking/Scoring (deterministisch, parametrierbar)
**Ziel:** niedriger Spread + guter Hebel + ausreichender KO‑Abstand + gute Quotequalität.

Empfohlene Score‑Komponenten (Beispiel):
- `S_spread`: je kleiner, desto besser (stark gewichtet)
- `S_leverage`: Nähe zu Zielband (z. B. min_leverage..min_leverage*3)
- `S_distance`: bevorzugtes KO‑Abstandsband (z. B. 5–15%)
- `S_quality`: Parser‑Confidence, missing‑flags, stale‑Hinweise
- Optional: Emittenten‑Präferenz (nur wenn Nutzer explizit)

Beispiel‑Formel (nur zur Illustration):
```text
score = 100
score -= spread_pct * 8
score -= abs(leverage - target_leverage) * 1.5
score -= distance_penalty(ko_distance_pct)
score -= quality_penalty(flags, parser_confidence)
```

Tie‑Break:
1) Spread asc, 2) KO‑Abstand desc (mehr Puffer), 3) Hebel desc

### 4.3 Edge Cases
- fehlende Quotes → exclude
- extrem naher KO‑Abstand → exclude oder massiver Score‑Malus
- verzögerte Daten/Markt geschlossen → Meta zeigt „as_of“, UI zeigt Warnhinweis

---

## 5) Systemdesign „Refresh“ (maximal aktuell, Onvista‑only)

### 5.1 Komponenten
- `OnvistaFetcher`
- `OnvistaParser`
- `Normalizer/Validator`
- `RankingEngine`
- `Cache/Store`
- `App Controller` (UI‑Trigger)

### 5.2 Ablaufkette beim Klick
1. UI sammelt Inputs → `SearchRequest`
2. Orchestrator startet parallel:
   - Fetch Long‑Liste
   - Fetch Short‑Liste
3. Parser → Normalizer → Filter → Ranking
4. Top‑N Long/Short + Meta zurück an UI
5. Cache aktualisieren (optional SWR)

### 5.3 Parallelisierung/Timeouts/Fehler
- Long/Short parallel (asyncio/ThreadPool)
- Partial Results erlaubt (Long OK, Short Error)
- Circuit‑Breaker schützt Onvista & UI

### 5.4 Meta‑Infos im Ergebnis
- `as_of`, `fetch_time_ms`, `run_id`
- `counts`: found/filtered/out
- `errors[]`: http_error, parse_error, rate_limit
- `parser_confidence` global + min/avg
- `cache`: hit/miss, age_s

---

## 6) Konkrete Output‑Formate

### 6.1 Beispiel‑Endpoint (lokal, wenn sinnvoll)
`GET /derivatives/ko/search?underlying=NASDAQ100&min_leverage=5&max_spread=2&top_n=10`

### 6.2 Beispiel‑JSON Response (gekürzt)
```json
{
  "underlying": "NASDAQ 100",
  "asOf": "2025-12-18T10:57:30Z",
  "criteria": {
    "minLeverage": 5.0,
    "maxSpreadPct": 2.0,
    "issuers": ["HSBC","Societe Generale","UBS","Vontobel"],
    "topN": 10
  },
  "long": [{ "wkn":"...", "issuer":"HSBC", "leverage":12.3, "spreadPct":1.1, "koDistancePct":8.4, "bid":8.10, "ask":8.19, "score":88.2, "flags":[] }],
  "short": [{ "wkn":"...", "issuer":"UBS", "leverage":10.7, "spreadPct":1.3, "koDistancePct":9.9, "bid":7.50, "ask":7.60, "score":86.0, "flags":[] }],
  "meta": {
    "runId":"...",
    "fetchTimeMs": 1420,
    "longStatus":"OK",
    "shortStatus":"OK",
    "parserConfidence": { "avg": 0.96, "min": 0.90 },
    "counts": { "longFound": 120, "longKept": 34, "shortFound": 110, "shortKept": 29 },
    "source":"onvista"
  }
}
```

### 6.3 UI‑Tabellenspalten (Empfehlung)
- WKN, Emittent, Richtung, Hebel, Spread%, KO‑Level, KO‑Abstand%, Bid/Ask, Score, Flags
- Default‑Sort: Score desc
- Filter‑Chips/Controls: Issuer, min Hebel, max Spread, Top‑N, Refresh

---

## 7) Onvista‑Adapter austauschbar kapseln (ohne Fremdquellen)

### 7.1 Klare Grenzen
- UI/Ranking/Filter dürfen **niemals** HTML parsen oder Onvista‑URLs kennen.
- Nur der Adapter kennt:
  - Onvista‑URL‑Parameternamen
  - Issuer‑IDs
  - HTML‑Struktur
  - Parser‑Schema‑Versionen

### 7.2 Vorteile
- Wenn Onvista HTML ändert: nur Adapter + Parser‑Tests anfassen.
- Wenn später andere Quelle erlaubt wäre: neue Adapter‑Implementierung, Ranking bleibt unverändert.

---

## 8) Pseudocode: End‑to‑End Refresh

```python
async def refresh_knockouts(underlying: str, cfg: KOFilterConfig) -> SearchResponse:
    run_id = new_run_id()
    t0 = now()

    # parallel fetch
    long_task = asyncio.create_task(onvista.search_list(underlying, "LONG", cfg))
    short_task = asyncio.create_task(onvista.search_list(underlying, "SHORT", cfg))

    long_raw, short_raw = await gather_with_timeouts(long_task, short_task)

    long_products = normalize_and_validate(long_raw)
    short_products = normalize_and_validate(short_raw)

    long_kept = apply_hard_filters(long_products, cfg)
    short_kept = apply_hard_filters(short_products, cfg)

    long_ranked = rank(long_kept, cfg)[:cfg.top_n]
    short_ranked = rank(short_kept, cfg)[:cfg.top_n]

    meta = build_meta(run_id, t0, now(), long_raw, short_raw, long_kept, short_kept)

    return SearchResponse(
        underlying=underlying,
        as_of=now(),
        criteria=cfg,
        long=long_ranked,
        short=short_ranked,
        meta=meta
    )
```

---

## 9) Definition of Done (KO‑Finder v1)

- Long/Short Top‑N je Underlying, Onvista‑only
- UI‑Panel mit Refresh‑Button
- Filter: min Hebel, max Spread, Emittenten, Top‑N
- Hard‑Filter + deterministisches Ranking
- Meta‑Infos sichtbar (Stand, Fetch‑Zeit, Fehler, Confidence)
- Parser‑Unit‑Tests + Ranking‑Tests
- Robustheit: Retry/Backoff/CircuitBreaker/RateLimit
- Disclaimer + Quellenhinweis „Onvista“ in UI

---

## Anhang: Gegebene URLs

```text
Long:
https://www.onvista.de/derivate/Knock-Outs?brokerId=8260&feature=STOP_LOSS&idIssuer=53159,54101,53882,53163&order=ASC&sort=spreadAskPct

Short:
https://www.onvista.de/derivate/Knock-Outs?brokerId=8260&feature=STOP_LOSS&idExerciseRight=1&idIssuer=53159,54101,53882,53163&order=ASC&sort=spreadAskPct
```
