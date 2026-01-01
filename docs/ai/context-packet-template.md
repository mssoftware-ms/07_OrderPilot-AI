# Context Packet Template (für Änderungen in großen Repos)

> Fülle dieses Template aus und liefere es bei jeder Change-Request-Iteration mit.

---

## A) Repo-Überblick

- Zweck (1–2 Sätze):
- Repo-Typ: (Mono-Repo / Single-Repo)
- Relevante Ordner/Module:

```bash
tree -L 4
# oder:
ls -la
```

- Wichtige Entry Points (falls bekannt):

---

## B) Build / Test / Run

- OS/Runtime:
- Node/Python Version:
- Package Manager:
- Install:
- Start:
- Tests/Lint/Typecheck/Build:

---

## C) Änderungsscope

### Akzeptanzkriterien (3–8 Bullets)

- [ ] …
- [ ] …

### Darf nicht kaputt gehen (1–5 Bullets)

- [ ] …
- [ ] …

---

## D) Repro / Logs

### Repro Steps
1. …
2. …

### Ist / Erwartet
- Ist:
- Erwartet:

### Logs (gekürzt, aber vollständig um die Stelle)
```text
PASTE LOGS HERE
```

---

## E) Schnittstellen / Flows (falls relevant)

- Types/Models:
- Entry Points / Call-Sites:
- Events/IPC:
- Persistenz/Storage:
- Config/Flags/Env Vars:
- Security/Permissions:

---

## F) Relevante Dateien & Snippets

- `path/to/file.py` (Zeilen …–…)
- `path/to/file.ts` (Zeilen …–…)
