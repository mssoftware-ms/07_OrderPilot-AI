# AI Analyse Popup - Detaillierte Funktionsdokumentation

**Version:** 1.0
**Letzte Aktualisierung:** Januar 2026
**Modul:** `src/ui/ai_analysis_window.py`

---

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Architektur](#architektur)
3. [Funktionen im Detail](#funktionen-im-detail)
4. [Vorteile der AI Chartanalyse](#vorteile-der-ai-chartanalyse)
5. [Nachteile und Limitierungen](#nachteile-und-limitierungen)
6. [Mehrwert zur Marktanalyse](#mehrwert-zur-marktanalyse)
7. [Technische Spezifikation](#technische-spezifikation)
8. [Verwendung](#verwendung)

---

## Übersicht

Das **AI Analyse Popup** ist ein integriertes Analysemodul innerhalb von OrderPilot-AI, das künstliche Intelligenz nutzt, um technische Chartanalysen durchzuführen. Es kombiniert deterministische Indikatoren mit LLM-basierter Interpretation, um Trading-Setups zu identifizieren.

### Kernfunktion

Das Popup analysiert aktuelle Marktdaten und liefert:
- **Setup-Erkennung** (Ja/Nein)
- **Setup-Typ** (z.B. Pullback, Breakout, Mean Reversion)
- **Konfidenz-Score** (0-100%)
- **Reasoning** (Begründung der Analyse)
- **Invalidation Level** (Stop-Loss-Bereich)

### Zugriff

Über die Chart-Toolbar: **🧠 AI Analyse** Button (violett)

---

## Architektur

### Komponenten-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                     AIAnalysisWindow (UI)                       │
│  ┌──────────────────┐  ┌──────────────────────────────────────┐ │
│  │   Overview Tab   │  │         Deep Analysis Tab            │ │
│  │  - Provider Sel. │  │  ┌────────────┐ ┌────────────────┐   │ │
│  │  - Model Select  │  │  │ Strategie  │ │   Timeframes   │   │ │
│  │  - Start Button  │  │  ├────────────┤ ├────────────────┤   │ │
│  │  - JSON Output   │  │  │ Indikatoren│ │   Deep Run     │   │ │
│  │  - Prompt Editor │  │  └────────────┘ └────────────────┘   │ │
│  └──────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AIAnalysisEngine (Core)                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐  │
│  │   Data     │ │  Regime    │ │  Feature   │ │   Prompt     │  │
│  │ Validator  │→│  Detector  │→│  Engineer  │→│   Composer   │  │
│  └────────────┘ └────────────┘ └────────────┘ └──────────────┘  │
│                                                      │          │
│                                                      ▼          │
│                                              ┌──────────────┐   │
│                                              │ OpenAI Client│   │
│                                              └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Datenfluss

1. **Datenbeschaffung**: Holt OHLCV-Daten vom aktuellen Chart (History Manager)
2. **Validierung**: Prüft Datenqualität (Timestamp, Volume, Outliers)
3. **Regime-Erkennung**: Bestimmt Marktregime (Bull/Bear/Range/Explosiv)
4. **Feature Engineering**: Extrahiert technische Kennzahlen
5. **Prompt-Komposition**: Erstellt strukturierten LLM-Prompt
6. **LLM-Analyse**: Sendet an OpenAI/Anthropic/Gemini
7. **Ergebnis-Parsing**: Validiert und normalisiert JSON-Output

---

## Funktionen im Detail

### 1. Overview Tab (Hauptanalyse)

#### Provider-Auswahl
- **OpenAI** (GPT-4, GPT-4-Turbo, GPT-3.5-Turbo)
- **Anthropic** (Claude 3 Opus, Sonnet, Haiku)
- **Gemini** (Pro, Ultra)

#### Model-Auswahl
Dynamisch basierend auf Provider - Standard aus Einstellungen geladen.

#### Start Analysis Button
- Fetcht frische Daten aus dem aktiven Chart
- Validiert und bereinigt Daten
- Führt vollständigen Analyse-Workflow aus
- Zeigt Progress-Indikator während der Analyse

#### JSON Output
- Strukturiertes Ergebnis im JSON-Format
- Copy-Button für Zwischenablage
- Pretty-Print mit Einrückung

#### Prompt Editor
- Anpassbare System- und Task-Prompts
- Reset auf Defaults möglich
- Persistierung über QSettings

### 2. Deep Analysis Tab

#### Strategie-Tab
- Zeigt erkanntes Marktregime
- Integriert mit Initial-Analyse

#### Timeframes-Tab
- Multi-Timeframe-Analyse
- Konfluenz-Erkennung über Zeitebenen

#### Indikatoren-Tab
- Detaillierte Indikator-Werte
- Technische Daten aus der Analyse

#### Deep Run-Tab
- Erweiterte Analyse-Workflows
- Mehrstufige Analyse-Pipelines

#### Log Viewer
- Echtzeit-Logging der Analyse
- Debug-Informationen
- Performance-Metriken

### 3. Data Validator (Datenqualität)

| Check | Beschreibung | Aktion bei Fehler |
|-------|--------------|-------------------|
| **Timestamp-Check** | Prüft ob letzte Kerze aktuell ist | Analyse abgebrochen |
| **Volume-Check** | Prüft auf Null-Volumen (letzte 5 Kerzen) | Analyse abgebrochen |
| **Outlier-Detection** | Z-Score > 4 bei High/Low | Automatische Bereinigung |
| **DataFrame-Validation** | Prüft DatetimeIndex | Analyse abgebrochen |

### 4. Regime Detector (Deterministisch)

| Regime | Bedingung |
|--------|-----------|
| **STRONG_TREND_BULL** | Close > EMA20 > EMA50 > EMA200 AND ADX > 25 |
| **STRONG_TREND_BEAR** | Close < EMA20 < EMA50 < EMA200 AND ADX > 25 |
| **CHOP_RANGE** | ADX < 20 |
| **VOLATILITY_EXPLOSIVE** | ATR > SMA(ATR,20) * 1.5 |
| **NEUTRAL** | Alle anderen Fälle |

### 5. Feature Engineering

#### Technische Features
| Feature | Beschreibung |
|---------|--------------|
| `rsi_value` | RSI(14) Wert (0-100) |
| `rsi_state` | OVERBOUGHT/OVERSOLD/NEUTRAL |
| `ema_20_dist_pct` | Distanz zum EMA20 in % |
| `ema_200_dist_pct` | Distanz zum EMA200 in % |
| `bb_pct_b` | Bollinger %B (Position innerhalb Bänder) |
| `bb_width` | Bollinger Bandwidth (Volatilität) |
| `atr_14` | Average True Range |
| `adx_14` | Average Directional Index |

#### Struktur-Analyse
- **Recent Highs**: Letzte 3 Pivot-Hochs
- **Recent Lows**: Letzte 3 Pivot-Tiefs
- **Current Price**: Aktueller Schlusskurs

#### Candle Summary
Letzte 5 Kerzen mit OHLCV für Musteranalyse.

### 6. Setup-Typen (LLM Output)

| Setup | Beschreibung |
|-------|--------------|
| `PULLBACK_EMA20` | Rücksetzer zum EMA20 im Trend |
| `BREAKOUT` | Ausbruch aus Range/Struktur |
| `MEAN_REVERSION` | Rückkehr zum Mittelwert nach Übertreibung |
| `SFP_SWING_FAILURE` | Swing Failure Pattern |
| `ABSORPTION` | Absorption von Verkaufs-/Kaufdruck |
| `NO_SETUP` | Kein valides Setup erkannt |

---

## Vorteile der AI Chartanalyse

### 1. Objektivität & Konsistenz

| Aspekt | Vorteil |
|--------|---------|
| **Emotionsfreie Analyse** | KI analysiert ohne Angst, Gier oder FOMO |
| **Konsistente Regeln** | Gleiche Bedingungen führen zu gleichen Ergebnissen |
| **Wiederholbarkeit** | Analyse ist nachvollziehbar und dokumentiert |

### 2. Geschwindigkeit & Effizienz

| Aspekt | Vorteil |
|--------|---------|
| **Multi-Indikator-Analyse** | 8+ Indikatoren in Sekunden ausgewertet |
| **Sofortige Regime-Erkennung** | Marktumfeld in <1 Sekunde bestimmt |
| **Automatische Strukturanalyse** | Pivots und Levels automatisch identifiziert |

### 3. Strukturierte Entscheidungshilfe

| Aspekt | Vorteil |
|--------|---------|
| **Klare Setup-Klassifikation** | 6 definierte Setup-Typen |
| **Quantifizierte Konfidenz** | 0-100 Score für Entscheidungssicherheit |
| **Begründung** | Transparente Reasoning-Ausgabe |
| **Invalidation Level** | Klarer Stop-Loss-Bereich definiert |

### 4. Integration & Workflow

| Aspekt | Vorteil |
|--------|---------|
| **Chart-Integration** | Direkt aus dem Charting-Tool aufrufbar |
| **Multi-Provider** | Wahl zwischen OpenAI, Anthropic, Gemini |
| **Anpassbare Prompts** | Personalisierbare Analyse-Anweisungen |
| **JSON-Export** | Maschinell verarbeitbares Ergebnis |

### 5. Datenqualitätssicherung

| Aspekt | Vorteil |
|--------|---------|
| **Preflight-Checks** | Verhindert Analyse mit fehlerhaften Daten |
| **Outlier-Bereinigung** | Automatische Korrektur von Bad Ticks |
| **Freshness-Check** | Nur aktuelle Daten werden analysiert |

---

## Nachteile und Limitierungen

### 1. Technische Einschränkungen

| Einschränkung | Beschreibung | Auswirkung |
|---------------|--------------|------------|
| **API-Abhängigkeit** | Benötigt aktive Internetverbindung | Offline-Nutzung nicht möglich |
| **Latenz** | LLM-Calls benötigen 2-10 Sekunden | Nicht für Hochfrequenz-Trading geeignet |
| **Rate Limits** | API-Provider haben Anfrage-Limits | Batch-Analysen können gedrosselt werden |
| **Kosten** | Token-basierte Abrechnung | Jede Analyse verursacht API-Kosten |

### 2. Analytische Limitierungen

| Einschränkung | Beschreibung | Auswirkung |
|---------------|--------------|------------|
| **Keine Orderausführung** | Reines Analyse-Tool | Manueller Trade-Eintrag erforderlich |
| **Single-Timeframe** | Analysiert nur aktiven Chart-Timeframe | Multi-Timeframe-Konfluenz eingeschränkt |
| **Keine Fundamentalanalyse** | Nur technische Daten | News/Events nicht berücksichtigt |
| **Lookback begrenzt** | 7 Tage Datenfenster | Langfristige Zyklen nicht erfasst |

### 3. LLM-spezifische Risiken

| Risiko | Beschreibung | Mitigation |
|--------|--------------|------------|
| **Halluzinationen** | LLM kann falsche Muster "sehen" | Deterministische Preflight-Checks |
| **Inkonsistenz** | Temperatur > 0 führt zu Varianz | Prompt-Stabilisierung |
| **Schema-Verletzung** | LLM antwortet nicht immer JSON | Strict Parsing mit Fallback |
| **Bias** | Training-Bias kann Analyse beeinflussen | Diversifizierte Provider-Wahl |

### 4. Datenbezogene Einschränkungen

| Einschränkung | Beschreibung | Auswirkung |
|---------------|--------------|------------|
| **Datenquelle abhängig** | Qualität variiert je Provider | Unterschiedliche Ergebnisse möglich |
| **Keine Real-time Ticks** | Basiert auf abgeschlossenen Kerzen | Intrabar-Bewegungen nicht erfasst |
| **Weekend Gaps** | Stock-Märkte am Wochenende geschlossen | Timestamp-Validation kann fehlschlagen |

### 5. Benutzerfreundlichkeit

| Einschränkung | Beschreibung | Auswirkung |
|---------------|--------------|------------|
| **API-Key erforderlich** | Externe Registrierung nötig | Setup-Hürde für neue Nutzer |
| **Keine Echtzeit-Updates** | Manuelle Analyse-Auslösung | Keine automatischen Alerts |
| **JSON-Output** | Technisches Format | Weniger intuitiv für Einsteiger |

---

## Mehrwert zur Marktanalyse

### 1. Ergänzung zur manuellen Analyse

```
┌────────────────────────────────────────────────────────────────┐
│                    ANALYSE-WORKFLOW                            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  MANUELLE ANALYSE          +       AI ANALYSE                  │
│  ──────────────────              ─────────────                 │
│  • Erfahrung                     • Objektive Metriken          │
│  • Intuition                     • Konsistente Checks          │
│  • Fundamentale Faktoren         • Strukturierte Output        │
│  • News-Berücksichtigung         • Quantifizierte Konfidenz    │
│                                                                │
│                    ↓           ↓                               │
│              ┌─────────────────────────────┐                   │
│              │   INFORMIERTE ENTSCHEIDUNG  │                   │
│              └─────────────────────────────┘                   │
└────────────────────────────────────────────────────────────────┘
```

### 2. Zweite Meinung / Confirmation

| Szenario | AI-Mehrwert |
|----------|-------------|
| **Setup identifiziert** | AI bestätigt/widerlegt die Einschätzung |
| **Unsicherheit** | AI gibt quantifizierten Konfidenz-Score |
| **Regime unklar** | AI klassifiziert objektiv Bull/Bear/Range |
| **Stop-Loss Placement** | AI schlägt strukturbasiertes Level vor |

### 3. Lernwerkzeug

| Anwendung | Nutzen |
|-----------|--------|
| **Reasoning analysieren** | Verstehen, warum ein Setup valide/invalide ist |
| **Muster-Erkennung** | Neue Pattern durch AI-Klassifikation lernen |
| **Fehler-Analyse** | Post-Trade-Review mit AI-Einschätzung vergleichen |

### 4. Zeitersparnis

| Task | Ohne AI | Mit AI |
|------|---------|--------|
| Multi-Indikator-Check | 5-10 Min | < 10 Sek |
| Regime-Bestimmung | 2-5 Min | Instant |
| Strukturanalyse (Pivots) | 3-5 Min | Instant |
| Setup-Dokumentation | 5-10 Min | Auto-JSON |

### 5. Risikomanagement-Unterstützung

| Feature | Risiko-Benefit |
|---------|----------------|
| **Invalidation Level** | Klarer Stop-Loss definiert → Max Drawdown begrenzt |
| **Konfidenz-Score** | Position-Sizing an Wahrscheinlichkeit anpassen |
| **Regime-Erkennung** | Strategie an Marktumfeld anpassen |
| **No-Setup-Erkennung** | Verhindert Overtrading in schlechten Bedingungen |

### 6. Dokumentation & Compliance

| Aspekt | Vorteil |
|--------|---------|
| **JSON-Log** | Vollständige Analyse-Dokumentation |
| **Timestamp** | Exakter Analysezeitpunkt dokumentiert |
| **Reasoning** | Begründung für Audit/Review verfügbar |
| **Reproducibility** | Gleiche Inputs = Gleiche Analyse (bei T=0) |

---

## Technische Spezifikation

### Unterstützte Datenquellen

| Quelle | Asset-Klasse | Status |
|--------|--------------|--------|
| Alpaca | Stocks, ETFs | ✅ Unterstützt |
| Alpaca Crypto | BTC, ETH, etc. | ✅ Unterstützt |
| Bitunix | Crypto Futures | ✅ Unterstützt |
| Yahoo Finance | Stocks, ETFs | ✅ Unterstützt |

### Timeframes

| Timeframe | Code | Unterstützt |
|-----------|------|-------------|
| 1 Minute | `1T` | ✅ |
| 5 Minuten | `5T` | ✅ |
| 15 Minuten | `15T` | ✅ |
| 1 Stunde | `1H` | ✅ |
| 1 Tag | `1D` | ✅ |

### Output-Schema

```json
{
  "setup_detected": true,
  "setup_type": "PULLBACK_EMA20",
  "confidence_score": 75,
  "reasoning": "Price pulled back to EMA20 in strong uptrend...",
  "invalidation_level": 42500.50,
  "notes": ["RSI showing bullish divergence", "Volume increasing"]
}
```

### Systemanforderungen

| Komponente | Anforderung |
|------------|-------------|
| Python | 3.10+ |
| PyQt6 | 6.4+ |
| API Key | OpenAI/Anthropic/Gemini |
| Netzwerk | Stabile Internetverbindung |
| RAM | 4GB+ empfohlen |

---

## Verwendung

### 1. Popup öffnen

1. Chart für gewünschtes Symbol laden
2. Klick auf **🧠 AI Analyse** Button in Toolbar
3. Popup öffnet sich über dem Chart

### 2. Analyse starten

1. Provider auswählen (OpenAI/Anthropic/Gemini)
2. Modell auswählen
3. Klick auf **Start Analysis**
4. Warten auf Ergebnis (2-10 Sek)

### 3. Ergebnis interpretieren

```
setup_detected: true      → Es wurde ein Setup identifiziert
setup_type: PULLBACK_EMA20 → Typ des Setups
confidence_score: 75      → 75% Konfidenz (moderat-hoch)
reasoning: "..."          → Begründung lesen
invalidation_level: 42500 → Stop-Loss unter diesem Level
notes: [...]              → Zusätzliche Hinweise beachten
```

### 4. Prompts anpassen (optional)

1. Klick auf **Edit Prompt**
2. System Prompt (Rolle/Constraints) anpassen
3. Task Prompt (Analyse-Aufgaben) anpassen
4. Speichern

### 5. Log einsehen

1. Klick auf **Logdatei öffnen**
2. Öffnet `logs/Analyse.log`
3. Enthält detaillierte Analyse-Schritte

---

## Fazit

Das AI Analyse Popup ist ein leistungsstarkes Tool zur Unterstützung der technischen Analyse. Es kombiniert deterministische Indikatoren mit LLM-basierter Interpretation und bietet:

**Stärken:**
- Objektive, konsistente Analyse
- Schnelle Multi-Indikator-Auswertung
- Strukturierte, quantifizierte Ergebnisse
- Flexible Provider-Wahl

**Zu beachten:**
- Als Entscheidungsunterstützung, nicht als alleinige Grundlage nutzen
- API-Kosten und Latenz berücksichtigen
- Regelmäßige Ergebnis-Validierung empfohlen

Die beste Nutzung erfolgt in Kombination mit eigener Analyse als "zweite Meinung" und zur Objektivierung von Trading-Entscheidungen.
