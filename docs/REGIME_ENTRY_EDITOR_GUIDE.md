# 📊 Regime Entry Expression Editor - Benutzerhandbuch

**Version:** 1.0  
**Datum:** 2026-01-29  
**Autor:** Claude Code

---

## Überblick

Der **Regime Entry Expression Editor** ist ein neues Tool im CEL Strategy Editor, das es ermöglicht, **CEL Entry Expressions** für Regime JSON Dateien zu erstellen.

### Problem gelöst:
- Entry Analyzer generiert JSON **OHNE** `entry_expression`
- Manuelles Schreiben von CEL Expressions ist fehleranfällig
- Regime-Namen sind dynamisch aus `regimes[].id`

### Lösung:
- Grafisches Tool zum Erstellen von Entry Expressions
- Template-basierte Generierung
- Automatische Validierung
- Direkt in JSON speichern

---

## Workflow

### 1. Öffnen des Editors

1. Starte **OrderPilot-AI**
2. Öffne den **CEL Strategy Editor** Tab (oben in der Toolbar)
3. Wechsle zum Tab **"📊 Regime Entry"**

### 2. Regime JSON laden

1. Klicke auf **"📂 Regime JSON laden"**
2. Navigiere zu `03_JSON/Entry_Analyzer/Regime/`
3. Wähle eine Regime JSON Datei (z.B. `260124_hardcodet_defaults_v2.json`)
4. Die Regimes werden automatisch extrahiert und angezeigt

**Info:** Wenn die JSON bereits eine `entry_expression` enthält, wird sie unter **"💾 Existing Expression in JSON"** angezeigt.

### 3. Strategy Template wählen (optional)

Im Bereich **"📋 Strategy Template"**:

1. Wähle ein Template aus dem Dropdown:
   - **Conservative**: Nur extremste Trends (STRONG_TF)
   - **Moderate**: Strong Bull/Bear + Strong TF
   - **Aggressive**: Alle Trend-Regimes außer Range
   - **Mean Reversion**: Entry bei Trend-Erschöpfung
   - **Custom**: Manuelle Regime-Auswahl

2. Klicke auf **"✨ Template anwenden"**
3. Die Checkboxen werden automatisch gesetzt

### 4. Manuelle Regime-Auswahl (Custom)

Im Bereich **"🔹 Regime Selection"**:

- **🟢 Long Entry Regimes:** Setze Checkboxen für Long-Entry Bedingungen
- **🔴 Short Entry Regimes:** Setze Checkboxen für Short-Entry Bedingungen

**Tipp:** Du kannst beliebig viele Regimes auswählen. Sie werden mit `||` (ODER) verknüpft.

### 5. Entry Direction wählen

Im Bereich **"🎯 Entry Direction"**:

- **Long + Short:** Beide Richtungen erlaubt
- **Long only:** Nur Long-Entries
- **Short only:** Nur Short-Entries

### 6. Expression generieren

1. Klicke auf **"⚡ Generate Expression"**
2. Die CEL Expression erscheint im **"📝 Generated Expression Preview"**
3. Überprüfe die Expression auf Korrektheit

**Beispiel:**
```javascript
trigger_regime_analysis() && (
  (side == 'long' && (
    last_closed_regime() == 'STRONG_BULL' ||
    last_closed_regime() == 'STRONG_TF'
  )) ||
  (side == 'short' && last_closed_regime() == 'STRONG_BEAR')
)
```

### 7. Expression validieren (optional)

1. Klicke auf **"✓ Validate"**
2. Die Expression wird mit CELEngine getestet
3. Bei Erfolg: **"✅ Validation Success"**
4. Bei Fehler: **"❌ Validation Failed"** mit Fehlerbeschreibung

### 8. In JSON speichern

**Option A: Überschreiben (mit Backup)**
1. Klicke auf **"💾 Save to JSON"**
2. Bestätige die Aktion
3. Die Expression wird in die Original-JSON geschrieben
4. Ein Backup wird automatisch erstellt (`.json.backup.<timestamp>`)

**Option B: Als neue Datei speichern**
1. Klicke auf **"💾 Save As..."**
2. Wähle Speicherort und Dateinamen
3. Eine neue JSON mit `entry_expression` wird erstellt
4. Die Original-Datei bleibt unverändert

### 9. Im Trading Bot verwenden

1. Öffne den **Bot Tab**
2. Klicke auf **"▶ Start Bot (JSON Entry)"**
3. Wähle die gespeicherte Regime JSON
4. Der Bot lädt die Expression und startet

---

## CEL Expression Struktur

### Komponenten

#### `trigger_regime_analysis()`
- Triggert Regime-Update auf dem Chart (nur im Backtest)
- Im Bot Tab ohne Chart: Gibt `false` zurück
- **Empfohlen:** Immer am Anfang der Expression

#### `side == 'long'` / `side == 'short'`
- Prüft die Entry-Richtung
- **Wichtig:** Verhindert falsche Entry-Richtung (z.B. Short bei Bull-Regime)

#### `last_closed_regime() == 'REGIME_ID'`
- Gibt Regime der letzten **geschlossenen** Candle zurück
- Regime-Namen aus JSON `regimes[].id` (z.B. "STRONG_BULL", "STRONG_TF")
- **Nicht** das aktuelle Regime der offenen Candle!

### Beispiele

#### Conservative (Nur extremste Trends)
```javascript
trigger_regime_analysis() &&
side == 'long' &&
last_closed_regime() == 'STRONG_TF'
```

#### Moderate (Long + Short)
```javascript
trigger_regime_analysis() && (
  (side == 'long' && (
    last_closed_regime() == 'STRONG_BULL' ||
    last_closed_regime() == 'STRONG_TF'
  )) ||
  (side == 'short' && last_closed_regime() == 'STRONG_BEAR')
)
```

#### Mit Indicator-Filter
```javascript
trigger_regime_analysis() &&
side == 'long' &&
last_closed_regime() == 'STRONG_BULL' &&
rsi > 50 &&
adx > 25
```

---

## Häufige Fehler

### ❌ Fehler 1: Feste Regime-Namen verwenden

```javascript
// ❌ FALSCH
regime == 'EXTREME_BULL'
```

**Problem:** Regime-Namen sind NICHT fest! Sie kommen aus JSON `regimes[].id`.

**✅ Lösung:**
```javascript
last_closed_regime() == 'STRONG_BULL'  // Name aus JSON
```

---

### ❌ Fehler 2: `regime` statt `last_closed_regime()` verwenden

```javascript
// ❌ FALSCH
regime == 'STRONG_BULL'
```

**Problem:** `regime` ist das **aktuelle** Regime (open candle). Für Entry brauchst du das **letzte geschlossene** Regime.

**✅ Lösung:**
```javascript
last_closed_regime() == 'STRONG_BULL'
```

---

### ❌ Fehler 3: Kein `side` Check

```javascript
// ❌ FALSCH
last_closed_regime() == 'STRONG_BULL'
```

**Problem:** Entry würde auch für Short gelten.

**✅ Lösung:**
```javascript
side == 'long' && last_closed_regime() == 'STRONG_BULL'
```

---

### ❌ Fehler 4: Exit in JSON versuchen

```json
{
  "entry_expression": "...",
  "exit_expression": "..."    // ❌ NICHT UNTERSTÜTZT!
}
```

**Problem:** JSON kontrolliert **NUR Entry**! Exit/SL/TP sind im Trading Bot programmiert.

**✅ Lösung:** Nur `entry_expression` in JSON, Rest im Bot.

---

## Template-Beschreibungen

### Conservative
- **Regimes:** Nur STRONG_TF
- **Ziel:** Höchste Gewinnwahrscheinlichkeit
- **Trades:** Wenige, aber qualitativ hochwertig
- **Risiko:** Niedrig
- **Empfohlen für:** Konservative Trader, geringe Drawdowns

### Moderate
- **Regimes:** STRONG_BULL, STRONG_BEAR, STRONG_TF
- **Ziel:** Balance zwischen Trades und Qualität
- **Trades:** Mittel
- **Risiko:** Mittel
- **Empfohlen für:** Die meisten Trader

### Aggressive
- **Regimes:** Alle Trend-Regimes außer SIDEWAYS
- **Ziel:** Viele Trades, früher Entry
- **Trades:** Viele
- **Risiko:** Höher
- **Empfohlen für:** Erfahrene Trader, aktives Management

### Mean Reversion
- **Regimes:** BULL_EXHAUSTION (→ Long), BEAR_EXHAUSTION (→ Short)
- **Ziel:** Trendwenden fangen
- **Trades:** Mittel
- **Risiko:** Hoch (Gegen-Trend)
- **Empfohlen für:** Erfahrene Trader, Range-Markets

### Custom
- **Regimes:** Frei wählbar
- **Ziel:** Volle Kontrolle
- **Empfohlen für:** Fortgeschrittene Trader mit eigener Strategie

---

## Technische Details

### Module

1. **`regime_json_parser.py`**
   - Parst Regime JSON
   - Extrahiert Regime-Definitionen
   - Kategorisiert Bull/Bear/Neutral

2. **`entry_expression_generator.py`**
   - Generiert CEL Expressions
   - Template-basierte Generierung
   - Pretty-Print Formatierung

3. **`regime_json_writer.py`**
   - Schreibt `entry_expression` in JSON
   - Erstellt automatische Backups
   - Save-As Funktion

4. **`regime_entry_expression_editor.py`**
   - PyQt6 GUI Widget
   - Regime-Auswahl mit Checkboxen
   - Live-Preview
   - Validation

### JSON-Format (nach Speichern)

```json
{
  "schema_version": "2.0.0",
  "metadata": {
    "updated_at": "2026-01-29T12:00:00Z",
    "tags": ["cel-entry", ...]
  },
  "optimization_results": [
    {
      "regimes": [
        { "id": "STRONG_BULL", "name": "...", "priority": 95 },
        ...
      ],
      "indicators": [...]
    }
  ],
  "entry_expression": "trigger_regime_analysis() && ((side == 'long' && last_closed_regime() == 'STRONG_BULL') || (side == 'short' && last_closed_regime() == 'STRONG_BEAR'))",
  "_comment_entry_expression": "⚠️ WICHTIG: Die entry_expression wurde MANUELL im CEL-Editor hinzugefügt!",
  "_comment_entry_expression_edited": "2026-01-29T12:30:45"
}
```

---

## Backup-System

### Automatische Backups

Beim Speichern mit **"💾 Save to JSON"** wird automatisch ein Backup erstellt:

**Format:** `<original_name>.json.backup.<timestamp>`

**Beispiel:**
- Original: `regime.json`
- Backup: `regime.json.backup.20260129_123045`

### Backup wiederherstellen

1. Finde das Backup im gleichen Ordner wie die Original-Datei
2. Umbenennen: `regime.json.backup.20260129_123045` → `regime.json`
3. Fertig!

---

## Troubleshooting

### Problem: "Keine Regimes angezeigt"

**Lösung:**
1. Prüfe ob JSON geladen wurde (Anzeige oben)
2. Prüfe JSON-Format (Schema 2.0.0?)
3. Prüfe `optimization_results[0].regimes` existiert

### Problem: "Validation Failed"

**Lösung:**
1. Prüfe Regime-Namen (aus JSON `regimes[].id`)
2. Prüfe CEL-Syntax (`&&`, `||`, `==`)
3. Prüfe Klammern-Balance
4. Teste mit einfacherer Expression

### Problem: "Save Failed"

**Lösung:**
1. Prüfe Dateiberechtigungen
2. Prüfe ob JSON schreibbar
3. Prüfe ob genug Speicherplatz

### Problem: "Trading Bot erkennt Expression nicht"

**Lösung:**
1. Prüfe JSON hat `entry_expression` Feld
2. Prüfe JSON ist im richtigen Ordner
3. Prüfe JSON-Format ist valide
4. Restart Bot Tab

---

## Best Practices

### 1. Immer Backups nutzen
- ✅ Lasse "Create Backup" aktiviert
- ✅ Prüfe Backup-Datei nach dem Speichern

### 2. Validiere vor dem Speichern
- ✅ Klicke "✓ Validate" vor "💾 Save"
- ✅ Prüfe Expression in Preview

### 3. Teste im Backtest
- ✅ Entry Analyzer → Backtest mit neuer JSON
- ✅ Prüfe Entry-Signale sind korrekt

### 4. Dokumentiere deine Strategy
- ✅ Nutze Template-Namen in JSON-Metadaten
- ✅ Notiere welche Regimes aktiv sind

### 5. Versionierung
- ✅ Nutze "Save As" für verschiedene Varianten
- ✅ Benenne Dateien aussagekräftig (z.B. `regime_conservative_v1.json`)

---

## Weiterführende Dokumentation

- **Workflow-Korrektur:** `Help/entry_analyzer/WORKFLOW_KORREKTUR.md`
- **Complete Example:** `Help/entry_analyzer/COMPLETE_REGIME_EXAMPLE.json`
- **CEL Functions:** `04_Knowledgbase/CEL_Functions_Reference_v3.md`
- **JSON Workflow Update:** `04_Knowledgbase/JSON_ENTRY_WORKFLOW_UPDATE.md`

---

## Support

Bei Problemen oder Fragen:
1. Prüfe diese Dokumentation
2. Prüfe `WORKFLOW_KORREKTUR.md`
3. Prüfe Log-Dateien (`logs/orderpilot-entrie.log`)

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2026-01-29  
**Autor:** Claude Code
