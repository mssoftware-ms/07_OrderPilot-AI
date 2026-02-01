#!/usr/bin/env python3
"""
Antigravity AI Toolkit - Initial Setup Script

Run this script ONCE in a new project to set up the complete AI agent system.

Usage:
    python setup-antigravity.py

Or download and run:
    curl -sL https://your-url/setup-antigravity.py | python3
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

# Embedded file contents
AGENTS = {
    "orchestrator.md": """# 🎯 Orchestrator Agent

> **Rolle:** Du bist der Central Coordinator. Deine Aufgabe ist es, die Mission zu planen und zwischen Developer und QA zu vermitteln.

> **Gesetze:** Du handelst strikt nach §1 (Planungsgebot) und §7 (Gewaltenteilung).

> **Prozess:**
> 1. Erstelle die Project Map und den 3–7 Schritte Plan.
> 2. Delegiere Teilschritte an den `developer`.
> 3. Sende die Ergebnisse zur Abnahme an den `qa-expert`.
> 4. Gib erst nach QA-Freigabe den Code an den User zurück.
""",
    "developer.md": """# 💻 Developer Agent

> **Rolle:** Du bist ein präziser Software-Engineer.

> **Fokus:** Implementierung von kleinen, testbaren Patches (§3).

> **Arbeitsweise:** Nutze Search-Driven Development (§2). Ändere nur, was im Plan steht. Liefere immer einen Unified Diff.
""",
    "qa-expert.md": """# 🔍 QA Expert Agent

> **Rolle:** Du bist ein skeptischer Senior QA Engineer.

> **Mission:** Finde Fehler im Code des Developers und achte auf Seiteneffekte.

> **Aktion:** Führe zwingend `.antigravity/scripts/ai-verify.py` aus. Akzeptiere einen Patch nur, wenn alle Tests grün sind und keine Architektur-Regeln verletzt wurden.
""",
    "architect.md": """# 📐 Architect Agent

> **Rolle:** Du bist ein erfahrener Software-Architekt.

> **Mission:** Verstehe bestehende Architektur-Patterns, erkenne Abhängigkeiten und prüfe ob Änderungen die Schichtenarchitektur verletzen.

> **Werkzeuge:** Nutze ARCHITECTURE.md, Dependency-Graphen, und Import-Analysen.
""",
    "researcher.md": """# 🔎 Researcher Agent

> **Rolle:** Du bist ein Code-Archäologe.

> **Mission:** Sammle alle relevanten Kontext-Informationen BEVOR Änderungen geplant werden.

> **Arbeitsweise:** Erstelle Context-Packets mit: betroffene Dateien, Abhängigkeiten, bestehende Tests, ähnliche Patterns.
""",
}

TEMPLATES = {
    "bug-report.md": """# Bug Report Template

## UI-Element (falls relevant)
- **Path:** `{window}.{tab}.{group}.{element}`
- **objectName:** `{name}`

## Aktuelles Verhalten
{beschreibung}

## Erwartetes Verhalten
{beschreibung}

## Reproduktion
1. {schritt}
2. {schritt}

## Logs (falls vorhanden)
```
{logs}
```
""",
    "crisp-prompt.md": """# CRISP Prompt Template

**C**ontext: In welchem Modul/Feature befindet sich das Problem?

**R**equirements: Was genau soll geändert werden?

**I**nput: Welche Dateien/UI-Elemente sind betroffen?

**S**pecifications: Welche Constraints gelten (keine Breaking Changes, etc.)?

**P**urpose: Warum ist diese Änderung wichtig?
""",
}

RULES = """# ⚖️ Das Grundgesetz der Code-Integrität

§1 [Planung]: Erst Plan (3-7 Schritte), dann Code.
§2 [Search]: Erst `rg`/`grep`, dann Änderung. Keine Bauchentscheidungen.
§3 [Atomic]: Patches müssen klein und einzeln testbar sein.
§4 [Kommunikation]: Max. 5 Fragen. Annahmen explizit markieren.
§5 [QA]: Kein Merge ohne Verify-Script Durchlauf.
§6 [Safety]: Keine Secrets, keine destruktiven Aktionen ohne Erlaubnis.
§7 [Hierarchie]: Orchestrator plant, Dev codet, QA prüft.
"""

README = """# 🚀 Antigravity AI Toolkit

Dieses Verzeichnis enthält das AI Agent System für strukturiertes Coding.

## Verwendung

### Verify-Script (Auto-Detection)
```bash
python .antigravity/scripts/ai-verify.py
python .antigravity/scripts/ai-verify.py tests/specific_test.py  # Scoped
```

Unterstützte Projekttypen:
- **Python**: flake8, mypy, pytest
- **Rust/Tauri**: cargo clippy, cargo check, cargo test
- **Node.js/TypeScript**: npm lint, tsc, npm test
- **Next.js**: npm lint, tsc, npm run build

### Agenten
- `orchestrator.md` - Koordiniert den Workflow
- `developer.md` - Implementiert Code
- `qa-expert.md` - Verifiziert Änderungen
- `architect.md` - Prüft Architektur
- `researcher.md` - Sammelt Kontext

### Templates
- `bug-report.md` - Strukturierte Bug-Reports
- `crisp-prompt.md` - Bessere Prompts schreiben

### Rules
Das Grundgesetz mit 7 Paragraphen für Code-Integrität.
"""


def setup_antigravity():
    """Set up the complete Antigravity toolkit."""
    root = Path.cwd()
    ag_dir = root / ".antigravity"

    print("🚀 Antigravity AI Toolkit Setup")
    print("=" * 50)

    # Create directories
    dirs = [
        ag_dir / "agents",
        ag_dir / "scripts",
        ag_dir / "templates",
        ag_dir / "context",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created: {d.relative_to(root)}")

    # Create agents
    for name, content in AGENTS.items():
        path = ag_dir / "agents" / name
        path.write_text(content, encoding="utf-8")
        print(f"📄 Created: {path.relative_to(root)}")

    # Create templates
    for name, content in TEMPLATES.items():
        path = ag_dir / "templates" / name
        path.write_text(content, encoding="utf-8")
        print(f"📄 Created: {path.relative_to(root)}")

    # Create rules
    rules_path = ag_dir / "rules"
    rules_path.write_text(RULES, encoding="utf-8")
    print(f"📄 Created: {rules_path.relative_to(root)}")

    # Create README
    readme_path = ag_dir / "README.md"
    readme_path.write_text(README, encoding="utf-8")
    print(f"📄 Created: {readme_path.relative_to(root)}")

    # Copy verify script (if running from existing setup)
    verify_src = Path(__file__).parent / "scripts" / "ai-verify.py"
    verify_dst = ag_dir / "scripts" / "ai-verify.py"
    if verify_src.exists() and not verify_dst.exists():
        shutil.copy(verify_src, verify_dst)
        print(f"📄 Copied: {verify_dst.relative_to(root)}")

    print("\n" + "=" * 50)
    print("✅ Antigravity AI Toolkit installed!")
    print(f"📍 Location: {ag_dir}")
    print("\nNext steps:")
    print("  1. Run: python .antigravity/scripts/ai-verify.py")
    print("  2. Press F12 in your app for UI Inspector (if PyQt)")


if __name__ == "__main__":
    setup_antigravity()
