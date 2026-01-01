# Onvista Scraping - Technische Dokumentation & Rechtliche Hinweise

**Stand:** 2025-12-18
**Modul:** `src/derivatives/ko_finder/`

---

## 1. Nicht verhandelbare Regeln (Onvista-only Contract)

### 1.1 Einzige Datenquelle
- **Onvista ist die EINZIGE erlaubte Datenquelle** für KO-Produkt-Daten
- Keine alternativen APIs/Provider:
  - Keine Emittenten-Feeds
  - Keine Börsen-APIs
  - Keine Drittanbieter
  - Keine Broker-APIs für Derivate

### 1.2 Fehlende Daten
Wenn Onvista ein Feld nicht liefert:
- **NICHT ergänzen** aus anderen Quellen
- **NICHT raten** oder interpolieren
- **NICHT rekonstruieren** aus Fremddaten

Stattdessen:
- `missing_fields` Flag setzen
- `stale_quote` Flag bei veralteten Daten
- Produkt ausschließen wenn kritische Felder fehlen

### 1.3 Code-Guards
```python
# Jeder Datenzugriff MUSS diese Quelle haben:
assert product.source == "onvista", "Only Onvista data allowed"

# Keine Fallbacks erlaubt:
# VERBOTEN: if not onvista_data: return other_source_data
```

---

## 2. Rechtliche Hinweise & ToS

### 2.1 robots.txt Analyse
- URL: https://www.onvista.de/robots.txt
- Status: Prüfen vor Produktiveinsatz
- Derivate-Seiten: `/derivate/` - Crawl-Status verifizieren

### 2.2 Nutzungsbedingungen
- Onvista ToS unter: https://www.onvista.de/info/nutzungsbedingungen
- Kommerzielle Nutzung: Ggf. eingeschränkt
- Automatisierte Zugriffe: Können eingeschränkt sein

### 2.3 Risikominimierung
1. **Frequenz begrenzen**: Max 1 Request/Sekunde, keine Massenscans
2. **Kein Polling**: Nur manuelle Refreshes (Button-Klick)
3. **Caching**: Ergebnisse cachen, unnötige Requests vermeiden
4. **User-Agent**: Browser-ähnlicher User-Agent
5. **Quellenangabe**: "Quelle: Onvista" in UI sichtbar

### 2.4 Disclaimer in UI
```
HINWEIS: Die angezeigten Daten stammen von Onvista und können
verzögert sein. Dies stellt keine Anlageberatung dar.
Bitte verifizieren Sie alle Daten vor Handelsentscheidungen.
```

---

## 3. Technische Architektur

### 3.1 Modulstruktur (max 600 LOC/Datei)
```
src/derivatives/ko_finder/
├── __init__.py              # Public API exports
├── models.py                # Pydantic/Dataclass Modelle (~150 LOC)
├── config.py                # KOFilterConfig (~100 LOC)
├── constants.py             # Issuer-IDs, Base-URLs (~50 LOC)
├── adapter/
│   ├── __init__.py
│   ├── url_builder.py       # URL-Generierung (~100 LOC)
│   ├── fetcher.py           # HTTP-Client mit Rate-Limit (~200 LOC)
│   ├── parser.py            # HTML→Modelle (~300 LOC)
│   └── normalizer.py        # Zahlen/Währungen (~150 LOC)
├── engine/
│   ├── __init__.py
│   ├── filters.py           # Hard Filters (~150 LOC)
│   ├── ranking.py           # Score-Berechnung (~200 LOC)
│   └── cache.py             # SWR Cache (~150 LOC)
└── service.py               # Orchestrierung (~200 LOC)
```

### 3.2 UI-Komponenten
```
src/ui/widgets/
├── chart_window_mixins/
│   └── ko_finder_mixin.py   # Tab-Integration (~300 LOC)
└── ko_finder/
    ├── __init__.py
    ├── table_model.py       # QAbstractTableModel (~200 LOC)
    ├── filter_panel.py      # Filter-Controls (~200 LOC)
    └── result_panel.py      # Ergebnis-Tabelle (~200 LOC)
```

### 3.3 Datenfluss
```
User klickt "Aktualisieren"
    │
    ▼
KOFinderService.refresh()
    │
    ├─► OnvistaFetcher.fetch_list(LONG)  ─┐
    │                                      ├─► parallel
    └─► OnvistaFetcher.fetch_list(SHORT) ─┘
            │
            ▼
    OnvistaParser.parse_table()
            │
            ▼
    Normalizer.normalize()
            │
            ▼
    HardFilters.apply()
            │
            ▼
    RankingEngine.score()
            │
            ▼
    SearchResponse → UI Update
```

---

## 4. HTTP-Stabilität

### 4.1 Rate Limiting
- **Global**: Min. 1 Sekunde zwischen Requests
- **Circuit Breaker**: Nach 3 Fehlern → 60s Pause
- **Timeout**: Connect 5s, Read 10s

### 4.2 Retry-Strategie
```python
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5  # Exponential: 1s, 1.5s, 2.25s
JITTER = 0.5  # ±500ms Randomisierung
```

### 4.3 Headers
```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    "Accept": "text/html,application/xhtml+xml,...",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}
```

---

## 5. Parser-Robustheit

### 5.1 Schema-Versionierung
- Aktuelle Version: `v1.0.0`
- Bei HTML-Änderungen: Version erhöhen
- Tests müssen bei Schema-Änderung fehlschlagen

### 5.2 Header-basiertes Mapping
```python
# RICHTIG: Spalten per Header-Text finden
columns = {header.text.strip(): idx for idx, header in enumerate(headers)}
leverage_idx = columns.get("Hebel")

# FALSCH: Feste Indizes
leverage = row[5]  # Bricht bei Spaltenänderung!
```

### 5.3 Parser-Confidence
- 1.0: Alle Pflichtfelder sauber erkannt
- 0.8-0.99: Optionale Felder fehlen
- <0.8: Produkt ausschließen oder stark flaggen

---

## 6. Issuer-Mapping

| Emittent | Onvista ID | Aktiv |
|----------|------------|-------|
| HSBC | 53159 | ✓ |
| Société Générale | 54101 | ✓ |
| UBS | 53882 | ✓ |
| Vontobel | 53163 | ✓ |

---

## 7. URL-Struktur

### 7.1 Basis-URL
```
https://www.onvista.de/derivate/Knock-Outs
```

### 7.2 Parameter
| Parameter | Beschreibung | Beispiel |
|-----------|--------------|----------|
| brokerId | Broker-Filter | 8260 |
| feature | Produktmerkmal | STOP_LOSS |
| idExerciseRight | 0=Long, 1=Short | 1 |
| idIssuer | Emittenten (kommasepariert) | 53159,54101 |
| order | Sortierrichtung | ASC, DESC |
| sort | Sortierspalte | spreadAskPct |

### 7.3 Beispiel-URLs
```
# Long (kein idExerciseRight oder idExerciseRight=0)
https://www.onvista.de/derivate/Knock-Outs?brokerId=8260&feature=STOP_LOSS&idIssuer=53159,54101,53882,53163&order=ASC&sort=spreadAskPct

# Short (idExerciseRight=1)
https://www.onvista.de/derivate/Knock-Outs?brokerId=8260&feature=STOP_LOSS&idExerciseRight=1&idIssuer=53159,54101,53882,53163&order=ASC&sort=spreadAskPct
```

---

## 8. Wartung & Debugging

### 8.1 HTML-Snapshots
Bei Parser-Fehlern:
1. HTML automatisch speichern in `logs/onvista_debug/`
2. Dateiname: `{run_id}_{timestamp}_{direction}.html`
3. Max. 10 Snapshots behalten (älteste löschen)

### 8.2 Logging
```python
logger.info("KO fetch started", extra={
    "run_id": run_id,
    "underlying": underlying,
    "direction": direction,
    "url": url,
})
```

### 8.3 Parser-Update-Prozess
1. Neuen HTML-Snapshot als Fixture speichern
2. Parser-Code anpassen
3. Schema-Version erhöhen
4. Alle Tests grün
5. `parse_schema_version` in Produktion erhöhen

---

## 9. Bekannte Limitierungen

1. **Keine Echtzeit-Daten**: Onvista-Daten können verzögert sein
2. **Marktzeiten**: Außerhalb Handelszeiten ggf. keine/veraltete Quotes
3. **HTML-Änderungen**: Parser kann bei Onvista-Updates brechen
4. **Rate-Limits**: Zu viele Requests können zu Blocks führen
5. **Underlying-Mapping**: Manuelles Mapping Symbol→Onvista-Filter nötig

---

## 10. Changelog

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0.0 | 2025-12-18 | Initiale Dokumentation |
