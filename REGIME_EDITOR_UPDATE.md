# Regime Entry Expression Editor - Update

**Datum:** 2026-01-29  
**Version:** 2.1 - Expression Editing

---

## ✨ Neue Features

### 1. **Automatisches Laden bestehender Expression** ✅

Wenn eine Regime JSON bereits eine `entry_expression` enthält:

- ✅ **Expression wird automatisch im Preview angezeigt**
- ✅ **Checkboxen werden automatisch gesetzt** (wenn möglich)
- ✅ **Validate/Save Buttons werden aktiviert**
- ✅ **Expression ist sofort editierbar**

**Vorher:**
```
JSON laden → Unten: "✅ Vorhanden: ..."
             Preview: Leer
             Checkboxen: Leer
```

**Jetzt:**
```
JSON laden → Unten: "✅ Vorhanden: ..."
             Preview: Expression angezeigt! ✨
             Checkboxen: Automatisch gesetzt! ✨
             Status: "📂 Expression geladen & geparst"
```

---

### 2. **Direktes Bearbeiten im Preview** ✅

Das Preview Feld ist jetzt **editierbar**!

**Workflow:**
1. JSON laden (Expression erscheint im Preview)
2. Expression direkt im Editor anpassen
3. Klicke "✏️ Übernehme Änderungen aus Editor"
4. Expression ist übernommen → Validate/Save möglich

**Neuer Button:**
```
[✏️ Übernehme Änderungen aus Editor]
  └─ Wird aktiviert sobald Text geändert wird
  └─ Übernimmt die bearbeitete Expression
```

---

### 3. **Intelligentes Expression Parsing** ✅

Der Editor versucht die Expression zu parsen und:

- Findet Regime-Namen: `last_closed_regime() == 'REGIME_NAME'`
- Erkennt Long/Short: `side == 'long'` vs `side == 'short'`
- Setzt Checkboxen automatisch

**Beispiel:**
```javascript
// Expression in JSON:
trigger_regime_analysis() && (
  (side == 'long' && last_closed_regime() == 'STRONG_BULL') ||
  (side == 'short' && last_closed_regime() == 'STRONG_BEAR')
)

// Editor setzt automatisch:
Long Regimes:  ☑ STRONG_BULL
Short Regimes: ☑ STRONG_BEAR
```

**Fallback-Heuristik:**
- Regimes mit "BULL" oder "TF" → Long
- Regimes mit "BEAR" → Short

---

## 📖 Verwendung

### Szenario 1: JSON mit Expression bearbeiten

```bash
# 1. Öffne Regime Entry Expression Editor
CEL Editor → JSON Editor → Tab "📊 Regime Entry"

# 2. Klicke "📂 Regime JSON laden"
Wähle: regime_with_expression.json

# 3. Expression erscheint automatisch!
Preview: [Deine Expression wird angezeigt]
Checkboxen: [Automatisch gesetzt]
Status: "📂 Expression geladen & geparst"

# 4. Bearbeiten (optional)
Ändere Expression direkt im Preview
Klicke "✏️ Übernehme Änderungen aus Editor"

# 5. Validieren
Klicke "✓ Validate"

# 6. Speichern
Klicke "💾 Save to JSON"
```

---

### Szenario 2: JSON ohne Expression

```bash
# 1. Lade JSON ohne entry_expression
Status: "❌ Keine entry_expression vorhanden"
Preview: Leer

# 2. Wähle Template oder Regimes
# 3. Klicke "⚡ Generate Expression"
# 4. Expression wird generiert
# 5. Speichern
```

---

## 🎯 Status Labels

### Unten rechts (Existing Expression):
```
❌ Keine entry_expression vorhanden (muss hinzugefügt werden)
  → Orange (FF9800)

✅ Vorhanden: trigger_regime_analysis() && ...
  → Grün (4CAF50)
```

### Im Preview Panel (Info Label):
```
📂 Expression aus JSON geladen | Länge: 234 Zeichen
  → Blau (2196F3)

📂 Expression geladen & geparst | Long: 2 | Short: 1
  → Grün (4CAF50)

✅ Expression generiert | Long Regimes: 2 | Short Regimes: 1
  → Grün (4CAF50)

✏️ Expression aus Editor übernommen | Länge: 234 Zeichen
  → Lila (9C27B0)
```

---

## 🔧 Technische Details

### Neue Methoden

#### `_load_existing_expression()`
```python
# Wird nach JSON-Laden aufgerufen
# - Zeigt Expression im Preview
# - Aktiviert Buttons
# - Ruft _parse_expression_and_set_checkboxes() auf
```

#### `_parse_expression_and_set_checkboxes(expression)`
```python
# Parst die Expression mit Regex
# - Pattern: last_closed_regime() == 'REGIME_NAME'
# - Pattern: side == 'long' && ... REGIME
# - Pattern: side == 'short' && ... REGIME
# - Setzt Checkboxen automatisch
```

#### `_on_expression_text_changed()`
```python
# Aktiviert "Übernehme Änderungen" Button
# Wenn Text im Editor geändert wurde
```

#### `_on_update_from_edit_clicked()`
```python
# Übernimmt bearbeitete Expression
# - Hole Text aus Editor
# - Update _current_expression
# - Aktiviere Validate/Save Buttons
```

---

## 🎨 UI Änderungen

### Preview Feld
```python
# Vorher:
self.expression_preview.setReadOnly(True)

# Jetzt:
self.expression_preview.setReadOnly(False)  # Editierbar!
```

### Neuer Button
```python
self.update_from_edit_btn = QPushButton("✏️ Übernehme Änderungen aus Editor")
# Lila (9C27B0)
# Enabled wenn Text geändert wurde
```

### Placeholder Text
```
Expression wird hier angezeigt...

1. Lade eine Regime JSON
2. Wähle Template oder Regimes
3. Klicke 'Generate'

Du kannst die Expression auch direkt hier bearbeiten!
```

---

## ✅ Vorteile

1. **Schnelleres Bearbeiten**: Bestehende Expressions können direkt geladen und bearbeitet werden
2. **Kein manuelles Copy-Paste**: Expression ist automatisch im Editor
3. **Intelligente Checkboxen**: Werden automatisch gesetzt basierend auf Expression
4. **Visuelles Feedback**: Klare Status-Labels zeigen was geladen wurde
5. **Flexible Bearbeitung**: Direktes Editieren im Preview + Button zum Übernehmen

---

## 📝 Beispiel-Flow

### Flow 1: Bestehende Expression bearbeiten
```
1. Lade regime_moderate.json
   → Expression erscheint: "trigger_regime_analysis() && ..."
   → Checkboxen: STRONG_BULL ☑, STRONG_BEAR ☑

2. Editiere im Preview: Füge "adx > 25" hinzu
   → Button "✏️ Übernehme Änderungen" wird aktiviert

3. Klicke "✏️ Übernehme Änderungen"
   → Info: "✏️ Expression aus Editor übernommen"

4. Klicke "✓ Validate"
   → Dialog: "✅ Validation Success"

5. Klicke "💾 Save to JSON"
   → Backup erstellt, JSON gespeichert
```

### Flow 2: Expression von Grund auf erstellen
```
1. Lade regime_neu.json (ohne expression)
   → Status: "❌ Keine entry_expression vorhanden"

2. Wähle Template: Moderate
3. Klicke "✨ Template anwenden"
   → Checkboxen werden gesetzt

4. Klicke "⚡ Generate Expression"
   → Expression wird generiert

5. Editiere im Preview (optional)
6. Klicke "✏️ Übernehme Änderungen"

7. Klicke "💾 Save to JSON"
```

---

## 🐛 Edge Cases

### Expression ohne last_closed_regime()
```javascript
// Expression:
side == 'long' && rsi > 50

// Parsing:
Keine Regime-Namen gefunden
Checkboxen: Nicht automatisch gesetzt
Info: "Konnte keine Regime-Namen finden"
```

### Unbekannte Regime-Namen
```javascript
// Expression enthält:
last_closed_regime() == 'CUSTOM_REGIME'

// Parsing:
Regime gefunden: CUSTOM_REGIME
Aber: Nicht in _long_checkboxes oder _short_checkboxes
→ Checkbox wird nicht gesetzt (existiert nicht)
```

### Komplexe Expression
```javascript
// Mehrere Regimes mit || und &&
trigger_regime_analysis() && (
  (side == 'long' && (
    last_closed_regime() == 'A' ||
    last_closed_regime() == 'B' ||
    last_closed_regime() == 'C'
  )) ||
  (side == 'short' && last_closed_regime() == 'D')
)

// Parsing:
Long: A, B, C (alle gefunden ✅)
Short: D (gefunden ✅)
```

---

## 📖 Siehe auch

- `docs/REGIME_ENTRY_EDITOR_GUIDE.md` - Vollständige Anleitung
- `JSON_ENTRY_COMPLETE.md` - JSON Entry System Dokumentation
- `Help/entry_analyzer/WORKFLOW_KORREKTUR.md` - Workflow-Korrektur

---

**Version:** 2.1 - Expression Editing  
**Autor:** Claude Code  
**Datum:** 2026-01-29
