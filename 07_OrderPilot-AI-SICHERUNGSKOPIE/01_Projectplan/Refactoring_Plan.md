# Kombinierte Code-Analyse & Sicheres Refactoring Task V1.0

> **Zweck:** Systematische Identifikation von totem, redundantem und überkompliziertem Code MIT anschließendem sicheren Refactoring.  
> **OBERSTES PRINZIP:** **100% Funktionserhalt - KEINE Funktion darf verloren gehen, JEDE Löschung muss nachweisbar begründet sein.**

---

## ⚠️ KRITISCHE SICHERHEITSREGELN (ABSOLUTE PRIORITÄT)

### **REGEL 1: Analyse VOR Aktion**
- **ERST vollständige Inventur aller Funktionen/Klassen/UI-Elemente**
- **DANN Duplikate und Dead Code identifizieren**
- **ERST NACH Bestätigung: Refactoring durchführen**

### **REGEL 2: Vollständigkeitsgarantie**
- **JEDE Funktion, Methode, Klasse MUSS erhalten bleiben (außer nachweisliche Duplikate)**
- **JEDES UI-Element MUSS weiterhin existieren und funktionieren**
- **Bei Unsicherheit: Code IMMER behalten**

### **REGEL 3: Dokumentationspflicht**
```text
Für JEDE Änderung MUSS dokumentiert werden:
- WAS wurde geändert (Datei, Zeilen, Funktion)
- WARUM wurde es geändert (Duplikat, Dead Code, Komplexität)
- WO ist der Code jetzt (bei Verschiebungen)
- TEST-Nachweis dass Funktionalität erhalten ist
```

---

# 🔄 WORKFLOW: 4 Phasen

## ═══════════════════════════════════════════════════════════════
## PHASE 1: VOLLSTÄNDIGE INVENTUR (MANDATORY FIRST STEP)
## ═══════════════════════════════════════════════════════════════

### 1.1 Code-Inventur erstellen

**BEVOR irgendwelche Änderungen gemacht werden:**

```python
# Inventur-Template (MUSS ausgefüllt werden)
INVENTORY_BEFORE = {
    "projekt": "[PROJEKTNAME]",
    "timestamp": "[DATUM/UHRZEIT]",
    
    "dateien": {
        "total": 0,
        "liste": [],  # Alle Dateien mit Pfad
        "groessen": []  # Format: {"datei": "path", "loc": 0, "loc_produktiv": 0}
    },
    
    "dateien_ueber_600_loc": {
        "total": 0,
        "liste": []  # Dateien die gesplittet werden müssen
    },
    
    "funktionen": {
        "total": 0,
        "liste": []  # Format: {"name": "func_name", "datei": "path", "zeilen": [start, end], "signatur": "..."}
    },
    
    "klassen": {
        "total": 0,
        "liste": []  # Format: {"name": "ClassName", "datei": "path", "methoden": [...]}
    },
    
    "ui_komponenten": {
        "total": 0,
        "liste": []  # Alle UI-Elemente (Buttons, Forms, Tabs, etc.)
    },
    
    "imports": {
        "total": 0,
        "liste": []  # Alle verwendeten Imports
    },
    
    "event_handler": {
        "total": 0,
        "liste": []  # Alle Event-Handler und Callbacks
    },
    
    "api_endpoints": {
        "total": 0,
        "liste": []  # REST/GraphQL Endpoints
    },
    
    "lines_of_code": {
        "total": 0,
        "produktiv": 0,  # Ohne Kommentare/Leerzeilen
        "kommentare": 0,
        "leerzeilen": 0
    }
}
```

### 1.2 Ausgabe der Inventur

```markdown
# 📋 CODE-INVENTUR REPORT

## Übersicht
- Projekt: [NAME]
- Analysierte Dateien: [X]
- Gesamte LOC: [X]

## Funktionen ([X] total)
| # | Funktion | Datei | Zeilen | Parameter |
|---|----------|-------|--------|-----------|
| 1 | func_a() | app.py | 10-25 | (x, y) |
| 2 | func_b() | utils.py | 5-45 | (data) |
| ... | ... | ... | ... | ... |

## Klassen ([X] total)
| # | Klasse | Datei | Methoden | LOC |
|---|--------|-------|----------|-----|
| 1 | MyClass | app.py | 5 | 120 |
| ... | ... | ... | ... | ... |

## UI-Komponenten ([X] total)
| # | Komponente | Typ | Datei |
|---|------------|-----|-------|
| 1 | login_btn | Button | ui.py |
| ... | ... | ... | ... |
```

---

## ═══════════════════════════════════════════════════════════════
## PHASE 2: ANALYSE (Dead Code, Duplikate, Komplexität)
## ═══════════════════════════════════════════════════════════════

### 2.1 Dead Code Analyse

**Erkennungsmuster:**

```yaml
dead_code_indicators:
  unreachable_code:
    - "Code nach return/throw ohne Bedingung"
    - "Else nach return in if-Block"
    - "Code nach sys.exit()"
  
  unused_functions:
    - "Private Funktionen ohne interne Referenzen"
    - "Funktionen ohne Aufrufe im gesamten Projekt"
    - "Überschriebene Methoden die nie aufgerufen werden"
  
  unused_variables:
    - "Deklarierte aber nie gelesene Variablen"
    - "Zugewiesene aber nie verwendete Werte"
    - "Import ohne Verwendung"
  
  unused_imports:
    - "Importierte Module die nie genutzt werden"
```

**⚠️ FALSCH-POSITIVE VERMEIDEN - NICHT als Dead Code markieren:**

```yaml
false_positives_ausnahmen:
  reflection_usage:
    - "getattr(), eval(), exec()"
    - "Dynamische Imports"
    - "Factory-Patterns"
  
  framework_hooks:
    - "Lifecycle-Methoden (__init__, __del__, etc.)"
    - "Event-Handler (on_click, on_change, etc.)"
    - "Decorators (@property, @staticmethod, etc.)"
    - "Tkinter/PyQt Callbacks"
  
  serialization:
    - "JSON/XML Methoden"
    - "ORM Model-Felder"
    - "API Endpoints"
  
  external_contracts:
    - "Public API Funktionen"
    - "Plugin-Schnittstellen"
    - "CLI-Commands"
```

### 2.2 Duplikat-Analyse

**Erkennungstypen:**

```yaml
duplikat_typen:
  exact_duplicate:
    beschreibung: "100% identischer Code"
    min_zeilen: 5
    aktion: "Zu gemeinsamer Funktion extrahieren"
  
  type_2_clone:
    beschreibung: "Identisch bis auf Variablennamen"
    similarity: ">= 90%"
    aktion: "Parametrisierte Funktion erstellen"
  
  type_3_clone:
    beschreibung: "Ähnliche Struktur mit Variationen"
    similarity: ">= 80%"
    aktion: "Template-Method oder Strategy-Pattern"
```

### 2.3 Komplexitäts-Analyse

**Schwellwerte:**

```yaml
komplexitaets_metriken:
  cyclomatic_complexity:
    optimal: "< 5"
    akzeptabel: "5-10"
    warnung: "11-20"
    kritisch: "> 20"
  
  nesting_depth:
    optimal: "< 3"
    akzeptabel: "3-4"
    kritisch: "> 6"
  
  method_length:
    optimal: "< 20 Zeilen"
    akzeptabel: "20-50 Zeilen"
    kritisch: "> 100 Zeilen"
  
  parameter_count:
    optimal: "< 3"
    akzeptabel: "3-4"
    kritisch: "> 6"
```

### 2.4 Dateigrößen-Analyse (MAX 600 LOC)

**⚠️ REGEL: Keine Codedatei darf mehr als 600 Zeilen produktiven Code haben!**

```yaml
dateigroessen_regel:
  max_lines_of_code: 600
  zaehlung: "Nur produktiver Code (ohne Kommentare, Docstrings, Leerzeilen)"
  
  bei_ueberschreitung:
    aktion: "Datei nach Funktionsbereichen splitten"
    strategie: "Logische Gruppierung nach Verantwortlichkeit"
    
  splitting_kriterien:
    - "Funktionen die zusammengehören in eigenes Modul"
    - "UI-Code getrennt von Business-Logic"
    - "Utilities/Helper in eigene Datei"
    - "Konstanten/Config in eigene Datei"
    - "Klassen mit >200 LOC in eigene Datei"
```

**Splitting-Strategien für große Dateien:**

```yaml
splitting_patterns:
  
  nach_verantwortlichkeit:
    beschreibung: "Single Responsibility Principle"
    beispiel:
      vorher: "app.py (1200 LOC)"
      nachher:
        - "app.py (150 LOC) - Haupteinstieg, Initialisierung"
        - "ui_components.py (300 LOC) - UI-Elemente"
        - "business_logic.py (400 LOC) - Kernlogik"
        - "data_handlers.py (250 LOC) - Datenverarbeitung"
        - "utils.py (100 LOC) - Hilfsfunktionen"
  
  nach_feature:
    beschreibung: "Feature-basierte Module"
    beispiel:
      vorher: "handlers.py (900 LOC)"
      nachher:
        - "handlers/user_handlers.py (250 LOC)"
        - "handlers/file_handlers.py (300 LOC)"
        - "handlers/api_handlers.py (350 LOC)"
        - "handlers/__init__.py - Re-exports"
  
  nach_layer:
    beschreibung: "Schichten-Architektur"
    beispiel:
      vorher: "service.py (800 LOC)"
      nachher:
        - "services/service_base.py (100 LOC)"
        - "services/data_service.py (250 LOC)"
        - "services/validation_service.py (200 LOC)"
        - "services/export_service.py (250 LOC)"
```

**⚠️ WICHTIG beim Splitting:**

```text
1. ALLE Funktionen müssen erhalten bleiben (Inventur-Check!)
2. Imports korrekt aktualisieren (alte Importpfade → neue Pfade)
3. Zirkuläre Imports vermeiden
4. __init__.py für Re-Exports nutzen (Abwärtskompatibilität)
5. Nach Splitting: ALLE Tests ausführen
```

**Ausgabe im Analyse-Report:**

```markdown
## 5. DATEIGRÖSSEN-ANALYSE

### Dateien über 600 LOC (SPLITTING ERFORDERLICH):
| Datei | LOC | Funktionen | Empfohlenes Splitting |
|-------|-----|------------|----------------------|
| app.py | 1,234 | 45 | → app.py, ui.py, logic.py, utils.py |
| handlers.py | 890 | 32 | → handlers/user.py, handlers/file.py, handlers/api.py |

### Splitting-Plan für [DATEI]:
```
VORHER: app.py (1,234 LOC, 45 Funktionen)

NACHHER:
├── app.py (180 LOC)
│   └── main(), init_app(), run()
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py (250 LOC)
│   │   └── MainWindow, create_menu(), create_toolbar()
│   ├── dialogs.py (200 LOC)
│   │   └── SettingsDialog, AboutDialog, FileDialog
│   └── widgets.py (180 LOC)
│       └── CustomButton, StatusBar, ProgressPanel
│
├── core/
│   ├── __init__.py
│   ├── business_logic.py (300 LOC)
│   │   └── process_data(), validate(), calculate()
│   └── data_handlers.py (200 LOC)
│       └── load_data(), save_data(), export()
│
└── utils.py (120 LOC)
    └── helper functions, constants

SUMME: 1,234 LOC (identisch!) ✅
FUNKTIONEN: 45 (identisch!) ✅
```
```

### 2.5 Analyse-Report ausgeben

```markdown
# 🔍 ANALYSE-REPORT

## 1. DEAD CODE (Kandidaten zur Entfernung)

### ✅ Sicher zu entfernen (mit Begründung):
| Funktion | Datei:Zeile | Grund | Letzte Nutzung |
|----------|-------------|-------|----------------|
| old_func() | app.py:234 | Keine Referenzen, ersetzt durch new_func() | Nie aufgerufen |

### ⚠️ Manuell prüfen (unsicher):
| Funktion | Datei:Zeile | Warnung |
|----------|-------------|---------|
| special_handler() | utils.py:67 | Könnte via Reflection aufgerufen werden |

---

## 2. DUPLIKATE

### Exakte Duplikate:
```
Datei A: module_a.py (Zeilen 45-89)
Datei B: module_b.py (Zeilen 123-167)
Identisch: 44 Zeilen
→ EMPFEHLUNG: Extract to shared function in utils.py
```

### Strukturelle Duplikate:
```
Pattern: Validation-Logic
Vorkommen: 5 Dateien
→ EMPFEHLUNG: Zentraler Validator
```

---

## 3. KOMPLEXITÄT

### Kritische Funktionen (Komplexität > 20):
| Funktion | Komplexität | Nesting | LOC | Empfehlung |
|----------|-------------|---------|-----|------------|
| process_data() | 34 | 7 | 234 | In 5-6 Funktionen splitten |

---

## 4. ZUSAMMENFASSUNG

- Dead Code (sicher): X Funktionen, Y Zeilen
- Dead Code (unsicher): X Funktionen, Y Zeilen
- Duplikate: X Blöcke, Y Zeilen gesamt
- Überkomplex: X Funktionen
- Dateien >600 LOC: X Dateien (Splitting erforderlich!)

**WARTE AUF BESTÄTIGUNG VOR PHASE 3!**
```

---

## ═══════════════════════════════════════════════════════════════
## PHASE 3: SICHERES REFACTORING (NUR NACH BESTÄTIGUNG!)
## ═══════════════════════════════════════════════════════════════

### 3.1 Refactoring-Plan erstellen

**Für JEDE geplante Änderung:**

```yaml
refactoring_plan:
  - id: "REF-001"
    typ: "Dead Code Entfernung"
    ziel: "old_func() entfernen"
    quelldatei: "app.py"
    zeilen: [234, 267]
    begründung: "Keine Referenzen, ersetzt durch new_func() in commit abc123"
    risiko: "NIEDRIG"
    test_strategie: "Suche nach String 'old_func' im gesamten Projekt"
    
  - id: "REF-002"
    typ: "Duplikat-Extraktion"
    ziel: "Gemeinsame validate() Funktion"
    quellen:
      - datei: "form_a.py"
        zeilen: [45, 89]
      - datei: "form_b.py"
        zeilen: [23, 67]
    zieldatei: "utils/validation.py"
    risiko: "MITTEL"
    test_strategie: "Alle Forms testen nach Änderung"
```

### 3.2 Sichere Durchführung

**SCHRITT-FÜR-SCHRITT für jede Änderung:**

```text
1. BACKUP erstellen (git commit oder Kopie)
2. Code KOPIEREN (nicht verschieben!) in neue Struktur
3. Imports/Referenzen aktualisieren
4. VERIFIZIEREN dass alle Aufrufe funktionieren
5. TESTEN der betroffenen Funktionalität
6. ERST DANN: Alten Code entfernen/auskommentieren
7. ERNEUT TESTEN
```

### 3.3 Code-Bewegungs-Protokoll

```yaml
movement_log:
  - id: "MOVE_001"
    von:
      datei: "app.py"
      zeilen: [100, 150]
      funktion: "validate_input()"
    nach:
      datei: "utils/validation.py"
      zeilen: [1, 51]
    checksum_vorher: "abc123..."
    checksum_nachher: "abc123..."  # MUSS identisch sein!
    status: "✅ Verifiziert"
```

---

## ═══════════════════════════════════════════════════════════════
## PHASE 4: VERIFIKATION & VOLLSTÄNDIGKEITSPRÜFUNG
## ═══════════════════════════════════════════════════════════════

### 4.1 Inventur NACHHER erstellen

```python
INVENTORY_AFTER = {
    # Exakt gleiche Struktur wie INVENTORY_BEFORE
}
```

### 4.2 Vollständigkeitsvergleich

```python
# MUSS ausgeführt werden:
def verify_completeness():
    """Vergleicht Inventur vorher/nachher"""
    
    # Funktionen (minus bewusst entfernte)
    expected_functions = INVENTORY_BEFORE["funktionen"]["total"] - len(APPROVED_DELETIONS)
    actual_functions = INVENTORY_AFTER["funktionen"]["total"]
    assert actual_functions == expected_functions, f"FEHLER: {expected_functions - actual_functions} Funktionen fehlen!"
    
    # UI-Komponenten (dürfen NIE weniger werden)
    assert INVENTORY_AFTER["ui_komponenten"]["total"] >= INVENTORY_BEFORE["ui_komponenten"]["total"]
    
    # Klassen
    expected_classes = INVENTORY_BEFORE["klassen"]["total"] - len(APPROVED_CLASS_DELETIONS)
    actual_classes = INVENTORY_AFTER["klassen"]["total"]
    assert actual_classes == expected_classes
    
    print("✅ Vollständigkeitsprüfung bestanden!")
```

### 4.3 Test-Protokoll

```bash
# MUSS ausgeführt werden:

# 1. Syntax-Check
python -m py_compile *.py

# 2. Import-Test
python -c "from main import *"

# 3. Unit-Tests (falls vorhanden)
pytest tests/ -v

# 4. Anwendung starten
python main.py --test-mode

# 5. Manuelle UI-Prüfung
# - Alle Buttons klickbar?
# - Alle Menüs funktional?
# - Alle Tabs vorhanden?
```

### 4.4 Finaler Report

```markdown
# ✅ REFACTORING ABSCHLUSS-REPORT

## Durchgeführte Änderungen

### Dead Code entfernt:
| Funktion | Datei | Zeilen | Begründung |
|----------|-------|--------|------------|
| old_func() | app.py | 34 | Keine Referenzen seit 2023 |

### Duplikate konsolidiert:
| Ursprung | Neue Stelle | Zeilen gespart |
|----------|-------------|----------------|
| form_a.py, form_b.py | utils/validation.py | 44 |

### Große Dateien gesplittet (>600 LOC):
| Original | LOC | Neue Module | Status |
|----------|-----|-------------|--------|
| app.py | 1,234 | app.py, ui.py, logic.py, utils.py | ✅ Alle Funktionen erhalten |
| handlers.py | 890 | handlers/user.py, handlers/file.py, handlers/api.py | ✅ Alle Funktionen erhalten |

### Komplexität reduziert:
| Funktion | Vorher | Nachher | Methode |
|----------|--------|---------|---------|
| process_data() | CC=34 | CC=8 | In 5 Funktionen gesplittet |

---

## Vollständigkeits-Nachweis

| Metrik | Vorher | Nachher | Status |
|--------|--------|---------|--------|
| Funktionen | 245 | 243 (-2 Dead Code) | ✅ |
| Klassen | 34 | 34 | ✅ |
| UI-Komponenten | 67 | 67 | ✅ |
| LOC (produktiv) | 12,450 | 12,100 (-350 Duplikate) | ✅ |
| Dateien >600 LOC | 3 | 0 | ✅ Alle gesplittet |
| Max. Dateigröße | 1,234 LOC | 580 LOC | ✅ Unter Limit |

---

## Test-Ergebnisse

| Test | Ergebnis |
|------|----------|
| Syntax-Check | ✅ PASSED |
| Import-Test | ✅ PASSED |
| Unit-Tests | ✅ 156/156 PASSED |
| UI-Start | ✅ PASSED |
| Manuelle Prüfung | ✅ PASSED |

---

## Rollback-Info

Falls Probleme auftreten:
- Git-Commit vor Refactoring: [COMMIT_HASH]
- Backup-Ordner: ./backup_[TIMESTAMP]/
```

---

## ⚠️ WICHTIGE WARNUNGEN

### NIEMALS automatisch löschen bei:
- ❌ Reflection/Dynamic Loading Verdacht
- ❌ Framework-Konventionen (Tkinter, PyQt, etc.)
- ❌ Public APIs
- ❌ Event-Handler und Callbacks
- ❌ Serialization-Code
- ❌ Test-Utilities

### Vor JEDER Löschung:
1. ✅ Globale Suche nach String-Referenzen
2. ✅ Git-History prüfen (wann/warum hinzugefügt)
3. ✅ Test-Coverage prüfen
4. ✅ Staging-Test durchführen

### Bei Unsicherheit:
**→ Code BEHALTEN, nicht löschen!**
**→ Als Kommentar markieren: `# TODO: Review - möglicherweise ungenutzt`**

---

## 📋 KURZÜBERSICHT: Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: INVENTUR                                          │
│  → Alle Funktionen, Klassen, UI-Elemente zählen            │
│  → Dateigrößen erfassen (LOC pro Datei)                    │
│  → INVENTORY_BEFORE erstellen                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: ANALYSE                                           │
│  → Dead Code identifizieren                                 │
│  → Duplikate finden                                         │
│  → Komplexität messen                                       │
│  → Dateien >600 LOC markieren (Splitting erforderlich)     │
│  → Report ausgeben                                          │
│  → ⏸️ WARTE AUF BESTÄTIGUNG                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: REFACTORING (nur nach Bestätigung!)              │
│  → Backup erstellen                                         │
│  → Große Dateien splitten (>600 LOC)                       │
│  → Duplikate konsolidieren                                  │
│  → Dead Code entfernen                                      │
│  → Imports aktualisieren                                    │
│  → Nach JEDER Änderung: Testen!                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: VERIFIKATION                                      │
│  → INVENTORY_AFTER erstellen                                │
│  → Vergleich: Vorher vs. Nachher                           │
│  → Prüfen: Alle Dateien unter 600 LOC?                     │
│  → Vollständigkeitsprüfung                                  │
│  → Test-Suite ausführen                                     │
│  → Finalen Report erstellen                                 │
└─────────────────────────────────────────────────────────────┘
```

---

**Ende der kombinierten Analyse & Refactoring Anweisung V1.0**
