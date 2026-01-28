# OrderPilot-AI Knowledge Base

Zentrale Wissenssammlung für Entwickler, Best Practices, häufige Probleme und deren Lösungen.

## 📚 Inhalt

### 1. Entwicklungs-Guides
- [Development Setup](development-setup.md) - Entwicklungsumgebung einrichten
- [Git Workflow](git-workflow.md) - Branching, Commits, PRs
- [Testing Strategy](testing-strategy.md) - Unit, Integration, E2E Tests

### 2. Fehlerbehandlung & Debugging
- [Error Patterns](error-patterns.md) - Häufige Fehler und Lösungen
- [Debugging Guide](debugging-guide.md) - Debugging-Techniken
- [Troubleshooting](troubleshooting.md) - Systematische Problemlösung

### 3. Architektur & Design
- [System Architecture](system-architecture.md) - Gesamtarchitektur
- [API Design](api-design.md) - REST API Konventionen
- [Database Schema](database-schema.md) - Datenbankdesign

### 4. Alpaca Integration
- [Alpaca API Guide](alpaca-api-guide.md) - Trading & Market Data API
- [Streaming Best Practices](streaming-best-practices.md) - WebSocket/SSE
- [Paper vs Live Trading](paper-vs-live.md) - Sicher testen

### 5. Python Best Practices
- [Code Style](code-style.md) - PEP 8, Type Hints
- [Performance Tips](performance-tips.md) - Optimierungen
- [Security Guidelines](security-guidelines.md) - Sichere Entwicklung

### 6. Tools & Workflow
- [Claude Code Usage](claude-code-usage.md) - AI-assistierte Entwicklung
- [Moltbot Integration](moltbot-integration.md) - Agent-basierte Workflows
- [Pre-commit Hooks](pre-commit-hooks.md) - Automatische Code-Qualität

## 🎯 Schnellzugriff

### Neu im Projekt?
1. Lies [Development Setup](development-setup.md)
2. Verstehe die [System Architecture](system-architecture.md)
3. Folge dem [Git Workflow](git-workflow.md)
4. Schau dir [Error Patterns](error-patterns.md) an

### Problem beim Entwickeln?
1. Prüfe [Error Patterns](error-patterns.md)
2. Nutze den [Debugging Guide](debugging-guide.md)
3. Konsultiere [Troubleshooting](troubleshooting.md)
4. Suche in den ADRs (`../adr/`)

### Neue Feature implementieren?
1. Prüfe relevante ADRs
2. Folge [Code Style](code-style.md)
3. Implementiere [Testing Strategy](testing-strategy.md)
4. Dokumentiere deine Entscheidung (neuer ADR wenn nötig)

## 📖 Dokumentations-Prinzipien

### 1. Living Documentation
- Dokumentation wird MIT dem Code aktualisiert
- Veraltete Docs sind schlimmer als keine Docs
- Jedes Teammitglied ist verantwortlich

### 2. Problem-Orientiert
- Dokumente erklären WARUM, nicht nur WAS
- Use Cases und Beispiele wichtiger als Theorie
- Häufige Fehler prominent platzieren

### 3. Suchbar & Verlinkbar
- Klare Dateinamen
- Interne Links zwischen Dokumenten
- Tags/Keywords für schnelle Suche

### 4. Verschiedene Zielgruppen
- **Neue Entwickler:** Setup, Basics, FAQs
- **Erfahrene Entwickler:** Deep Dives, Performance, Edge Cases
- **Reviewer:** Code Style, Best Practices, Security

## 🔄 Aktualisierungs-Workflow

### Wann dokumentieren?

1. **Sofort bei neuer Entscheidung:**
   - Erstelle ADR für wichtige Architektur-Entscheidungen
   - Dokumentiere neue Patterns/Approaches

2. **Nach Bugfix:**
   - Füge zu `error-patterns.md` hinzu
   - Update Troubleshooting Guide
   - Ergänze Tests

3. **Bei neuem Feature:**
   - API-Dokumentation aktualisieren
   - Integration Guide erweitern
   - Beispiele hinzufügen

4. **Wöchentlich:**
   - Review aller TODOs in Dokumentation
   - Veraltete Inhalte aktualisieren
   - Links prüfen

## 🤝 Beitragen

### Neue Dokumentation hinzufügen

1. **Prüfe ob bereits vorhanden:**
   - Durchsuche bestehende Docs
   - Vermeide Duplikate

2. **Wähle richtigen Ort:**
   - `/docs/adr/` für Architektur-Entscheidungen
   - `/docs/knowledge/` für Guides & Best Practices
   - `/docs/api/` für API-Dokumentation

3. **Nutze Vorlagen:**
   - ADR Template (siehe `/docs/adr/README.md`)
   - Guide Template (siehe unten)

4. **Update Index:**
   - Verlinke in dieser README
   - Füge zu relevanten Kategorien hinzu

### Guide Template

```markdown
# [Titel]

**Zielgruppe:** [Anfänger | Fortgeschritten | Experte]
**Geschätzter Lesezeit:** [X Minuten]
**Letzte Aktualisierung:** YYYY-MM-DD

## Überblick

[Kurze Zusammenfassung - 2-3 Sätze]

## Voraussetzungen

- [Voraussetzung 1]
- [Voraussetzung 2]

## Schritt-für-Schritt

### 1. [Erster Schritt]

[Beschreibung]

```bash
# Code-Beispiel
```

### 2. [Zweiter Schritt]

[Beschreibung]

## Häufige Probleme

### Problem: [Beschreibung]

**Symptom:** [Was sieht man?]
**Ursache:** [Warum passiert es?]
**Lösung:** [Wie behebt man es?]

## Best Practices

- [Practice 1]
- [Practice 2]

## Weiterführende Ressourcen

- [Link zu verwandten Docs]
- [Externe Ressourcen]

---

**Fragen oder Feedback?** Öffne ein Issue im Projekt-Repository.
```

## 📊 Dokumentations-Metriken

### Aktuelle Abdeckung

- **ADRs:** 1 (WSL2 Migration)
- **Guides:** In Entwicklung
- **API Docs:** Siehe `/docs/alpaca/`
- **Error Patterns:** 0 (wird erstellt)

### Ziele

- [ ] Minimum 5 ADRs bis Ende Q1 2026
- [ ] Alle Haupt-Features dokumentiert
- [ ] Error Patterns für Top 20 Fehler
- [ ] Setup-Zeit für neue Entwickler < 1 Tag

---

**Letzte Aktualisierung:** 2026-01-28
**Maintainer:** OrderPilot-AI Team
