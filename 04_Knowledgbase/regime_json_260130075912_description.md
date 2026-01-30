# Regime-JSON 260130075912 – Feldübersicht & Verwendung

## Zweck & Einsatz
- Datei: `03_JSON/Entry_Analyzer/Regime/260130075912_regime_optimization_results_BTCUSDT_5m_#1.json`
- Wird geladen über **Entry Analyzer → Tab “Regime” → Button “Analyse Current Chart”** sowie beim **Bot-Start (JSON)**.  
- `RegimeDisplayMixin` und `RegimeEngineJSON` nutzen ausschließlich die IDs aus `regimes[].id` für Overlay-Beschriftungen und Entscheidungen.

## Top-Level-Keys
- `schema_version`  
  Version des Formats; aktuell `2.0.0`. Dient nur zur Kompatibilitätsprüfung.
- `metadata`  
  Kontext zur Optimierung (Autor, Zeitstempel, Tags, Beschreibung, Trading-Style). Keine Logik-Auswirkung.
- `optimization_results` (Liste)  
  Enthält Optimierungsläufe. Nur Einträge mit `"applied": true` werden verwendet (hier der erste Eintrag).
- `entry_expression`  
  CEL-Ausdruck, der nach der Regime-Erkennung entscheidet, ob ein Entry ausgelöst wird. Verweist auf Regime-IDs (z. B. `STRONG_BULL`, `STRONG_BEAR`).  
  Hinweis: Der Analyzer akzeptiert nur CEL-ähnliche Funktionen/Variablen; neue Felder müssen im CEL-Kontext existieren.
- `_comment_entry_expression`, `_comment_entry_expression_edited`  
  Freitext-Kommentare. Werden vor dem JSON-Schema-Check bereinigt, damit die Validierung nicht scheitert.

## Struktur eines Optimization-Results
Jedes Objekt unter `optimization_results[]` enthält:
- `timestamp`, `score`, `trial_number`, `applied` – reine Metadaten.
- `indicators` – Liste genutzter Indikatoren.
  - Felder pro Indikator:  
    - `name` (interne Kennung im Analyzer), `type` (z. B. `ADX`, `RSI`, `ATR`).  
    - `params[]`: Parameter mit `name`, `value` (aktueller Wert), `range` (Optimierungsraum: `min`, `max`, `step`).  
  - Laufzeit-Relevanz: Für die Regime-Logik zählt nur `value`; `range` dient Dokumentation/Optimizer.
- `regimes` – Liste der Regime-Definitionen (Priorität bestimmt Auswertungsreihenfolge).
  - Felder pro Regime:  
    - `id` – **entscheidend**: wird im Chart als Label verwendet und im CEL (`last_closed_regime()`) zurückgegeben.  
    - `name` – beschreibend für Menschen; aktuell nicht zur Steuerung genutzt.  
    - `thresholds[]`: Bedingungen für dieses Regime. Jedes Threshold hat `name`, `value`, `range` (wie oben). Die Engine prüft die `value`-Grenzen gegen die berechneten Indikatorwerte.  
    - `priority` – höhere Zahl = wird früher geprüft.  
    - `scope` – hier durchgehend `"entry"`; reserviert für spätere Trennung (z. B. exit/overlay).

## Regime-IDs in dieser Datei
- `STRONG_TF` – stärkster Trend (ADX/DI-Diff hoch).  
- `STRONG_BULL`, `STRONG_BEAR` – starker Auf-/Abwärtstrend mit RSI-Bestätigung.  
- `TF` – allgemeines Trend-Following.  
- `BULL_EXHAUSTION`, `BEAR_EXHAUSTION` – Trend-Erschöpfung (RSI-Grenzen invers).  
- `BULL`, `BEAR` – normale Trendzustände.  
- `SIDEWAYS` – Range/Chop bei niedrigem ADX.

### Schwellenwert-Namen (Auszug)
- `adx_min`, `adx_max` – Mindest- bzw. Höchstwert des ADX.  
- `di_diff_min` – Mindestabstand der DI-Linien (Trendstärke).  
- `rsi_confirm_bull` / `rsi_confirm_bear` – RSI-Bestätigung für bull/bear.  
- `rsi_exhaustion_max` / `rsi_exhaustion_min` – RSI-Schwellen für Erschöpfung.  
- ATR-Parameter (`strong_move_pct`, `extreme_move_pct`) fließen in Bewegungsstärke ein; thresholds nutzen die berechneten ATR-Derivate.

## Wie die Engine damit arbeitet
1) Indikatorwerte (ADX/DI, RSI, ATR) werden mit den `value`-Schwellen der Regime verglichen.  
2) Regime mit höchster `priority`, dessen Bedingungen erfüllt sind, wird gewählt.  
3) Chart-Overlay zeichnet eine vertikale Linie mit der **Regime-ID** als Label (nicht `name`).  
4) `entry_expression` wertet das zuletzt geschlossene Regime (`last_closed_regime()`) gegen `side` aus, um Signale zu erzeugen.

## Best Practices / Stolpersteine
- **Labels steuern über `id`**: Wenn auf dem Chart `STRONG_TREND_BEAR` erscheint, liegt es an der `id`; passe diese an (z. B. `STRONG_BEAR`).  
- **Keine zusätzlichen Top-Level-Felder** außer den oben genannten, sonst schlägt die Schema-Validierung fehl (Kommentare werden bereits bereinigt).  
- **Ranges sind optional für Laufzeit**, aber hilfreich zur Nachvollziehbarkeit.  
- Halte `schema_version` auf dem erwarteten Stand (2.0.0), damit kommende Validatoren kompatibel bleiben.

## Speicherort & Export
- Standard-Export für Chart-Snapshots (PNG/JSON) landet in `.AI_Exchange/export`.  
- Diese Regime-JSON liegt produktiv unter `03_JSON/Entry_Analyzer/Regime/`; Kopien für Dokumentation kannst du hier in `04_knowledgbase/` ablegen.
