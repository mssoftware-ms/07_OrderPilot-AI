# OrderPilot-AI – Projektkontext für Claude Code

Dieses Dokument definiert, wie du (Gemini CLI) in diesem Repository arbeiten sollst:
- Ziel: stabile Trading-Plattform mit Alpaca (Trading + Market Data + Streaming, inkl. Crypto, News).
- Fokus: saubere Architektur, nachvollziehbare Änderungen, kein gefährlicher Live-Handel ohne ausdrückliche Anweisung.

---

## 1. Projektüberblick

**OrderPilot-AI** ist eine Python-basierte Trading-Anwendung mit folgenden Zielen:

- Live-Marktdaten (Aktien, Crypto, ggf. weitere Assetklassen) über Alpaca Market Data API.
- Orderaufgabe, Positions- und Kontoverwaltung über Alpaca Trading API.
- Streaming (WebSockets / SSE) für Markt- und Kontoevents, später Strategie-Signale.
- Mittelfristig: Skript-/Strategie-Engine, Backtesting, Visualisierung.

Du sollst primär unterstützen bei:

- Architektur- und API-Design (Alpaca-Connectoren, Streaming-Clients, interne Services).
- Implementierung und Refactoring von Python-Code.
- Stabilisierung (Fehlerbehebung, Logging, Tests).
- Erzeugen von technischer Dokumentation (README, Modul-Docs, Entwickler-Guides).

---

## 2. Technischer Rahmen

- Sprache: **Python** (aktuelle Projektversion den Konfigurationsdateien entnehmen, z. B. `pyproject.toml` oder `requirements.txt`).
- Stil: **PEP 8**, konsequente Typannotationen.
- Architektur: Schichtenmodell, keine direkten API-Calls aus der UI.
- Eventuell vorhandene Frameworks (UI, Web, etc.) aus dem bestehenden Code ableiten und respektieren.
- Virtuelle Umgebung: vorhandene `.venv` / Setup-Anweisungen im Repo verwenden, nicht frei erfinden.

Wenn du Bibliotheken vorschlägst:
- Bevorzuge etablierte, gut gepflegte Pakete.
- Prüfe zuerst, ob im Repo bereits ein Paket genutzt wird (z. B. `alpaca-py`, `websockets`, `httpx`, `requests`) und halte dich daran.

---

## 3. Wichtige Verzeichnisse (relativ zum Projekt-Root)

Diese Pfade können bereits existieren oder sollen von dir konsistent genutzt/angelegt werden:

- `src/`  
  - Kernanwendung (Module, Services, Domain-Logik).
- `src/brokers/alpaca/`  
  - Alpaca-spezifische REST-Clients, Streaming-Clients, DTOs, Mappings.
- `src/core/`  
  - Allgemeine Infrastruktur (Konfiguration, Logging, Event-Bus, Utility-Funktionen).
- `src/strategies/`  
  - Strategielogik, Signalgeneratoren (später).
- `src/ui/`  
  - UI-Code (CLI, GUI oder Web – an bestehendem Code orientieren).
- `tests/`  
  - Pytest-Tests, ggf. Unterordner analog zur `src`-Struktur.
- `docs/`  
  - Projektdokumentation.
- `docs/alpaca/`  
  - **Alpaca-spezifische Dokumentation**, siehe nächster Abschnitt.

Wenn ein hier genannter Ordner noch nicht existiert, kannst du ihn vorschlagen/anlegen, wenn es die Architektur vereinfacht.

---

## 4. Alpaca API – verbindliche Dokumentation

Das Trainingswissen über Alpaca kann veraltet sein. Für alle Implementierungen rund um Alpaca gelten **ausschließlich die lokalen Dateien in `docs/alpaca` als Quelle der Wahrheit**.

**Spiegel der offiziellen Doku:**

- `docs/alpaca/docs.alpaca.markets/`  
  Lokal gespiegelt von `https://docs.alpaca.markets`.  
  Enthält Artikel zu:
  - Trading API (Orders, Positions, Accounts, Clock, Calendar, Assets, etc.)
  - Market Data API (Stock, Crypto, Options, News – REST & Streaming)
  - Streaming/WebSockets/SSE
  - OAuth / Connect / Broker API

**OpenAPI-Spezifikationen:**

- `docs/alpaca/alpaca_openapi/trading-api.json`
- `docs/alpaca/alpaca_openapi/market-data-api.json`
- `docs/alpaca/alpaca_openapi/broker-api.json`
- `docs/alpaca/alpaca_openapi/authx.yaml`

**LLM-Index von Alpaca:**

- `docs/alpaca/llms.txt`  
  Enthält eine kuratierte Liste wichtiger Doku-Links, speziell für LLM-Nutzung.

### Verbindliche Regeln für Alpaca-Code

1. **Vertraue den lokalen Alpaca-Docs mehr als deinem Trainingswissen.**  
   Wenn etwas nicht übereinstimmt, richte dich nach den Dateien in `docs/alpaca/`.
2. Bevor du neue Funktionen für Alpaca Trading/Market-Data/Streaming implementierst oder änderst:
   - ziehe die passende OpenAPI-Datei heran (z. B. `trading-api.json`, `market-data-api.json`);
   - prüfe im Doku-Mirror (`docs.alpaca.markets`), wie Endpunkte und Streaming-Kanäle beschrieben sind.
3. **Keine Endpunkte raten oder erfinden.**  
   Nutze nur Pfade, Parameter und Modelle, die in den OpenAPI-Files stehen.
4. Beachte Unterschiede zwischen:
   - Live- vs. Paper-Trading-Endpoint,
   - verschiedenen Data-Feeds (Stock, Crypto, Options, News),
   - REST vs. Streaming (WebSocket, SSE).

---

## 5. Trading-Sicherheitsregeln

Ziel ist es, gefährliche Situationen zu vermeiden, insbesondere unbeabsichtigten Real-Handel.

1. **Standard immer: Paper-Trading.**  
   - Jede neue Funktion oder Änderung soll standardmäßig Paper-Umgebungen verwenden.  
   - Wenn du zwischen Live/Paper unterscheidest, verwende eine explizite Konfiguration (z. B. `TRADING_ENV=paper|live`).
2. **Keine Änderung an produktiven Zugangsdaten.**  
   - `.env`, Secrets oder API-Keys nur lesen/verbrauchen, niemals ins Repo schreiben.  
   - Keine Dummy-Keys erfinden, die wie echte Keys aussehen.
3. **Keine „versteckten“ Side-Effects.**  
   - Funktionen, die Orders auslösen oder Positionen schließen, müssen eindeutig benannt sein und klar dokumentiert werden.
4. **Bei Code-Änderungen an Order-Logik:**  
   - Schreibe/aktualisiere Unit-Tests oder zumindest Dry-Run-Simulationen.  
   - Beschreibe im Ergebnis immer, welche Risiken sich ändern (z. B. doppelte Order, Fehlausführung, Time-in-Force).

Wenn ich (der menschliche Entwickler) ausdrücklich Live-Trading möchte, wird das klar im Prompt erwähnt. Ohne diese explizite Anweisung sollst du immer auf Sicherheit und Paper-Umgebung optimieren.

---

## 6. Architektur-Vorgaben

### Schichten

Bevorzuge eine klare Trennung:

1. **Adapter / Connectors (`src/brokers/alpaca/…`)**
   - Dünne Wrapper um Alpaca-REST/WS/SSE-Endpunkte.
   - Keine Geschäftslogik, nur Übersetzung: Python ↔ HTTP/JSON/WebSocket-Frames.
2. **Domain-Services (`src/core/…` / `src/services/…`)**
   - Handelslogik, Positionsverwaltung, Portfolio-Berechnungen.
   - Arbeiten gegen Interfaces / abstrakte Klassen, nicht direkt gegen HTTP.
3. **Strategien (`src/strategies/…`)**
   - Regeln, Signale, Einstiegs-/Ausstiegskriterien.
4. **UI / API (`src/ui/…`)**
   - Anzeige, Interaktion, keine direkten REST-Aufrufe an Alpaca.  
   - UI ruft Domain-Services auf, nicht Broker-Adapter direkt.

### Async / Streaming

- Nutze konsistent `asyncio`, wenn Streaming/WebSockets implementiert werden.
- Entweder:
  - **Async-Client** + Event-Loop zentral verwalten, oder
  - klare Hintergrund-Worker-Prozesse/Threads, die Streams konsumieren.
- Keine verschachtelten Event-Loops starten; wenn ein Framework (z. B. qasync, FastAPI) bereits einen Loop kontrolliert, hänge dich daran.

---

## 7. Coding-Guidelines

- PEP-8 einhalten, sinnvolle Namen, kurze Funktionen.
- Konsequent Typannotationen verwenden (`from __future__ import annotations` bei Bedarf).
- Für Domänenobjekte: bevorzugt `dataclasses` oder Pydantic-Modelle, wenn bereits im Projekt genutzt.
- Fehlerbehandlung:
  - API-Fehler (HTTP-Status, Rate-Limits, Netzwerkfehler) klar unterscheiden.
  - Exceptions nicht pauschal schlucken; logge genug Kontext (Endpoint, Status, Payload).
- Logging:
  - Verwende das bestehende Logging-Setup; falls keines vorhanden ist, schlage ein standardisiertes `logging`-Setup vor (`src/core/logging.py`).

---

## 8. Tests & Qualität

Wenn du Fehler behebst oder neue Funktionen einführst:

1. **Reproduktion verstehen**
   - Beschreibe in deinen Notizen, wie der Fehler sich äußert.
2. **Bestehende Tests prüfen**
   - Suche in `tests/` nach relevanten Dateien (z. B. `test_alpaca_*.py`).
3. **Tests ergänzen**
   - Schreibe neue Unit-Tests oder passe bestehende an, um den Fehler zu reproduzieren.
4. **Änderung umsetzen**
   - Nur die minimal notwendige Änderung im Code ausführen, keine unbeteiligten Teile umformatieren.
5. **Tests ausführen**
   - Wenn möglich, Test-Befehle angeben (`pytest tests/...`) und im Ergebnis zusammenfassen, welche Tests nun erfolgreich sind.
6. **Ergebnis dokumentieren**
   - In deiner Antwort klar beschreiben:
     - welche Dateien geändert wurden,
     - welche neuen Tests existieren,
     - wie sich das Verhalten geändert hat.

---

## 9. Arbeitsweise von Claude in diesem Repo

Wenn du eine Aufgabe erhältst (Bugfix, Feature, Refactoring), gehe i. d. R. so vor:

1. **Kontext sammeln**
   - Relevante Dateien und Module identifizieren (z. B. durch Suche nach Klassennamen, Funktionsnamen, Pfaden).
   - Bei Alpaca-Themen: zuerst die passende Doku in `docs/alpaca/` prüfen.
2. **Problem formulieren**
   - Kurz in eigenen Worten zusammenfassen, was technisch erreicht werden soll.
3. **Plan erstellen**
   - Eine klare, nummerierte Liste von Schritten schreiben (Dateien, Klassen, Funktionen, die du ändern willst).
   - Plan zuerst darstellen, bevor du große Änderungen vornimmst.
4. **Änderungen durchführen**
   - Fokus auf kleine, konsistente Commits/Änderungsblöcke.
   - Keine nicht benötigten Stil-/Format-Änderungen in vielen Dateien.
5. **Tests/Checks**
   - Vorschlagen, welche Tests oder Checks lokal laufen sollten.
6. **Zusammenfassung**
   - Am Ende deiner Antwort eine kurze technische Zusammenfassung (Was wurde geändert? Warum? Welche Risiken bleiben?).

---

## 10. Bekannte Fehlertypen & worauf du achten sollst

- **Veraltete Alpaca-Endpunkte**  
  → Immer gegen OpenAPI-Specs aus `docs/alpaca/alpaca_openapi/` prüfen, bevor du neue REST-Calls oder Streaming-Subscriptions einbaust.
- **Verwechslung Live/Paper**  
  → Bei neuen Configs immer klar zwischen Live- und Paper-Base-URLs trennen, Standard = Paper.
- **Fehlerhafte Streaming-Implementierung**
  → Achte darauf:
    - Reconnect-Logik bei Verbindungsabbrüchen,
    - sauberes Schließen von Verbindungen,
    - keine Blockierung des Event-Loops durch CPU-intensive Arbeit.

Wenn du erkennst, dass du wiederholt denselben Fehler machst (z. B. einen bestimmten Alpaca-Endpoint falsch verwendest), ergänze die relevanten Hinweise in dieser `CLAUDE.md`.

---

## 11. Kommunikation

- Antworte präzise und technisch; keine überflüssigen Floskeln.
- Wenn Annahmen nötig sind (z. B. zu Frameworks oder Projektstruktur), benenne sie explizit.
- Wenn dir Informationen fehlen, schlage gezielte Schritte vor (z. B. „Bitte gib mir die aktuelle `pyproject.toml`, damit ich die Laufzeitumgebung sehe“), statt ins Blaue zu implementieren.
