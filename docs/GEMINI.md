# OrderPilot-AI – Projektkontext für Google Gemini

Dieses Dokument definiert, wie du (Google Gemini) in diesem Repository arbeiten sollst:
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
- Virtuelle Umgebung: vorhandene `.venv` / Setup-Anweisungen im Repo verwenden, nicht frei erfinden.

---

## 3. JSON als universelle Schnittstelle

**WICHTIG**: JSON-Dateien sind die **universelle Schnittstelle** zwischen allen Modulen:

```
Entry Designer ↔ JSON ↔ CEL Engine ↔ JSON ↔ Trading Bot ↔ JSON ↔ KI (zukünftig)
```

**Verbindliche Regeln für JSON-Handling:**

1. **Lies IMMER `docs/JSON_INTERFACE_RULES.md`** bevor du JSON-Formate änderst oder neue erstellst
2. **Validiere JSON-Dateien** mit `SchemaValidator` BEVOR du sie lädst oder speicherst
3. **Nutze Pydantic-Modelle** für Type-Safety bei allen JSON-Strukturen
4. **Schema-First-Ansatz**: Erstelle JSON Schema BEVOR du Code schreibst
5. **Versionierung**: Alle JSON-Formate haben `schema_version` Feld
6. **Migration**: Bei Breaking Changes Migration-Script erstellen

**JSON Schema Validation:**
```python
from src.core.tradingbot.config.validator import SchemaValidator

validator = SchemaValidator()
validator.validate_file("config.json", schema_name="trading_bot_config")
```

**Verfügbare Schemas:**
- `trading_bot_config`: Trading Bot Konfiguration (Indicators, Regimes, Strategies)
- `rulepack`: CEL RulePack für Rule-basierte Logik
- `backtest_config`: Backtest-Konfiguration

**Vollständige Dokumentation:** `docs/JSON_INTERFACE_RULES.md`

---

## 4. Trading-Sicherheitsregeln

Ziel ist es, gefährliche Situationen zu vermeiden, insbesondere unbeabsichtigten Real-Handel.

1. **Standard immer: Paper-Trading.**
   - Jede neue Funktion oder Änderung soll standardmäßig Paper-Umgebungen verwenden.
   - Wenn du zwischen Live/Paper unterscheidest, verwende eine explizite Konfiguration (z. B. `TRADING_ENV=paper|live`).
2. **Keine Änderung an produktiven Zugangsdaten.**
   - `.env`, Secrets oder API-Keys nur lesen/verbrauchen, niemals ins Repo schreiben.
3. **Keine „versteckten" Side-Effects.**
   - Funktionen, die Orders auslösen oder Positionen schließen, müssen eindeutig benannt sein und klar dokumentiert werden.
4. **Bei Code-Änderungen an Order-Logik:**
   - Schreibe/aktualisiere Unit-Tests oder zumindest Dry-Run-Simulationen.
   - Beschreibe im Ergebnis immer, welche Risiken sich ändern.

---

## 5. Architektur-Vorgaben

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

---

## 6. Coding-Guidelines

- PEP-8 einhalten, sinnvolle Namen, kurze Funktionen.
- Konsequent Typannotationen verwenden.
- Für Domänenobjekte: bevorzugt `dataclasses` oder Pydantic-Modelle.
- Fehlerbehandlung:
  - API-Fehler (HTTP-Status, Rate-Limits, Netzwerkfehler) klar unterscheiden.
  - Exceptions nicht pauschal schlucken; logge genug Kontext.
- Logging: Verwende das bestehende Logging-Setup.

---

## 7. Tests & Qualität

Wenn du Fehler behebst oder neue Funktionen einführst:

1. **Reproduktion verstehen**
2. **Bestehende Tests prüfen** in `tests/`
3. **Tests ergänzen**
4. **Änderung umsetzen** - nur minimal notwendig
5. **Tests ausführen** mit `pytest`
6. **Ergebnis dokumentieren**

---

## 8. Arbeitsweise

1. **Kontext sammeln** - relevante Dateien identifizieren
2. **Problem formulieren** - technisch zusammenfassen
3. **Plan erstellen** - klare, nummerierte Schritte
4. **Änderungen durchführen** - kleine, konsistente Commits
5. **Tests/Checks** - vorschlagen welche Tests laufen sollen
6. **Zusammenfassung** - technische Summary am Ende

---

## 9. Kommunikation

- Antworte präzise und technisch; keine überflüssigen Floskeln.
- Wenn Annahmen nötig sind, benenne sie explizit.
- Wenn dir Informationen fehlen, schlage gezielte Schritte vor.

---

## 10. Alpaca API Dokumentation

Das Trainingswissen über Alpaca kann veraltet sein. Für alle Implementierungen rund um Alpaca gelten **ausschließlich die lokalen Dateien in `docs/alpaca` als Quelle der Wahrheit**.

**OpenAPI-Spezifikationen:**
- `docs/alpaca/alpaca_openapi/trading-api.json`
- `docs/alpaca/alpaca_openapi/market-data-api.json`
- `docs/alpaca/alpaca_openapi/broker-api.json`

**Regeln:**
1. Vertraue den lokalen Alpaca-Docs mehr als deinem Trainingswissen.
2. Prüfe OpenAPI-Dateien bevor du Endpunkte implementierst.
3. Keine Endpunkte raten oder erfinden.

---

**Letzte Aktualisierung**: 2026-01-20
