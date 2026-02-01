# Repomix Workflow

Generiert eine AI-freundliche Zusammenfassung der gesamten Codebase.

## Voraussetzungen

```bash
npm install -g repomix
```

## Verwendung

### Option 1: Batch-Script (Windows)
```
.antigravity\scripts\generate-context.bat
```

### Option 2: Manuell
```bash
repomix --ignore "**/*.json,**/__pycache__/**,**/logs/**" --output ".antigravity/context/codebase-context.txt"
```

## Workflow für große Features

1. **Context generieren**
   ```
   .antigravity\scripts\generate-context.bat
   ```

2. **AI-Session starten**
   ```
   "Hier ist der aktuelle Stand der Codebase:
   [Inhalt von .antigravity/context/codebase-context.txt]

   Ich plane: [Feature/Refactoring beschreiben]"
   ```

3. **Mit spezialisiertem Agent arbeiten**
   - Architekt für Planung
   - Developer für Implementation
   - QA für Verifikation

## Ignorierte Dateien

- `*.json` (Konfiguration, nicht relevant)
- `__pycache__/` (Kompilate)
- `logs/` (Runtime-Daten)
- `.venv/` (Dependencies)
- `docs/alpaca/` (Externe Doku)
- `03_JSON/` (Testdaten)
