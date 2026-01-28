# Architecture Decision Records (ADR)

Diese Verzeichnis enthält alle wichtigen Architektur-Entscheidungen für das OrderPilot-AI Projekt.

## Was ist ein ADR?

Architecture Decision Records (ADRs) dokumentieren wichtige technische Entscheidungen im Projekt:
- **Kontext:** Welches Problem wird gelöst?
- **Entscheidung:** Welche Lösung wurde gewählt?
- **Konsequenzen:** Was sind die Auswirkungen?
- **Alternativen:** Welche Optionen wurden erwogen?

## Format

Jede ADR folgt diesem Namensschema:
```
ADR-NNNN-kurzer-titel.md
```

Beispiel: `ADR-0001-wsl2-migration.md`

## Template

```markdown
# ADR-NNNN: [Titel]

**Status:** [Proposed | Accepted | Deprecated | Superseded]
**Datum:** YYYY-MM-DD
**Autor:** [Name]
**Entscheidung:** [ID der ersetzten ADR, falls zutreffend]

## Kontext

[Beschreibung des Problems/der Situation]

## Entscheidung

[Gewählte Lösung mit Begründung]

## Konsequenzen

### Positiv
- [Vorteil 1]
- [Vorteil 2]

### Negativ
- [Nachteil 1]
- [Nachteil 2]

## Alternativen

### Option 1: [Name]
- **Pro:** [Vorteile]
- **Contra:** [Nachteile]
- **Grund für Ablehnung:** [Warum nicht gewählt]

### Option 2: [Name]
- **Pro:** [Vorteile]
- **Contra:** [Nachteile]
- **Grund für Ablehnung:** [Warum nicht gewählt]

## Implementierung

- [Schritt 1]
- [Schritt 2]

## Referenzen

- [Link zu relevanten Dokumenten]
- [Link zu Issues/PRs]
```

## Index

| ADR | Titel | Status | Datum |
|-----|-------|--------|-------|
| [0001](ADR-0001-wsl2-migration.md) | WSL2 Migration für OrderPilot-AI | Accepted | 2026-01-28 |

## Kategorien

### Infrastruktur
- ADR-0001: WSL2 Migration

### Entwicklungs-Workflow
- [Noch keine]

### Datenbank & Persistenz
- [Noch keine]

### API & Integration
- [Noch keine]

### Security & Authentication
- [Noch keine]

---

**Letzte Aktualisierung:** 2026-01-28
