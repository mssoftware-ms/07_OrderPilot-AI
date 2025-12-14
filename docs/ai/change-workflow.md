# Change-Workflow für große Projekte (Runbook)

Dieses Runbook ist **modell- und tool-agnostisch** (Claude Code, Codex CLI, Gemini CLI, etc.).  
Ziel: In großen Codebases zuverlässig Änderungen umsetzen – **ohne Raten**, in **kleinen, verifizierbaren Patches**.

---

## Ziel

- Wiederholbarer Workflow für Änderungen/Erweiterungen/Refactorings in großen Repos (≈35k+ LOC)
- Fokus auf: Build-/Test-Stabilität, minimale Seiteneffekte, klare Rückrollbarkeit, nachvollziehbare Diffs

---

## Arbeitsprinzipien

- **Maximal 5 Rückfragen pro Iteration.** Fehlende Infos als **„Annahme:“** markieren.
- **Kleine, testbare Patches**: Patch-Plan → Patch → Checks → nächster Patch.
- **Search-Driven Development**: erst `rg/grep`, dann ändern (keine Bauchentscheidungen).
- **Single Source of Truth** respektieren (Docs/Schema/Config im Repo > Trainingswissen).
- **Terminal-/Agentenfreundlich**: kurze Schritte, Commands, Diffs, klare “Next action”.

---

## Output-Standard (immer so liefern)

### 1) Project Map (aktualisiert)
- Module, Entry Points, Daten-/Event-Flows
- Build/Test-Pipeline
- Risiken / Couplings (Config, Flags, DI, IPC/Eventbus, Codegen, Build-Skripte)

### 2) Plan in 3–7 Schritten
Klein, verifizierbar, mit klarer Reihenfolge.

### 3) Patch N
- **Änderungserklärung (1–2 Sätze)**: warum hier / warum minimal  
- **Unified Diff** (bevorzugt)  
  - Falls Diff nicht möglich: Datei → kompletter Codeblock (klar markieren, was ersetzt wird)
- **Befehle zum Verifizieren** (Build/Test/Lint/Typecheck/Run)
- **Erwartetes Ergebnis** + **„Wenn es fehlschlägt, sammle diese Logs:“**
- **QA-Minimaltests**: mind. welche Tests laufen müssen + ggf. 1–2 neue Minimaltests
- **CI/DevOps-Checks**: Lockfiles, Versionen, Build-Artefakte, typische CI-Fallen

---

## Workflow (wie du vorgehst)

1. **Triagieren**
   - Scope, Risiko, angrenzende Systeme
   - Source of Truth lokalisieren (Docs/Schemas/Config)

2. **Project Map bauen**
   - Aus Context Packet + 1–2 Hypothesen (wo sitzt die Änderung wirklich?)

3. **Minimaler Eingriff**
   - Kleinster Patch, der das Ziel erfüllt (keine Nebenbaustellen)

4. **Verifikation**
   - Lokale Checks + gezielte Tests
   - Wenn nötig: 1–2 neue Minimaltests (Unit/Integration/E2E)

5. **Folgepatches**
   - Call-Sites, Typen, Docs, Config, CI-Änderungen sauber nachziehen

6. **Regression-Absicherung**
   - “Was könnte noch betroffen sein?” + kurze Checkliste

7. **Abschluss**
   - PR-Notizen: Was/Warum/Wie getestet
   - Rollback-Hinweise (falls relevant)

---

## Spezial-Regeln für große Codebases (Anti-Konterfehler)

- Fordere nie „mehr Code“, sondern nur **minimal nötige Dateien/Abschnitte**
  (Entry Points, Interfaces, betroffene Module + Call-Sites).
- Wenn mehrere Orte plausibel sind: **2–3 Kandidaten nennen** und dann anhand **1–2 Snippets/Logs** entscheiden.
- Achte auf verdeckte Kopplung:
  - Configs, Feature-Flags, Env Vars
  - DI/Container
  - Event-Bus/IPC
  - Codegen, Build-/Bundler-Skripte, migrations/seed
- Trenne **Hypothese** vs. **Beweis** (Logs/rg-Treffer).

---

## Format für Rückfragen (max. 5)

Jede Frage enthält:
- **Warum ich das brauche**
- **Wie du es lieferst** (Command / Datei / Log)

---

## Agenten-Runbook-Version (Copy/Paste für CLI-Tools)

> Du arbeitest strikt nach folgendem Prozess:  
> (1) Project Map, (2) Plan (3–7 Schritte), (3) Patch 1 (Unified Diff), (4) Verifikations-Commands, (5) Erwartetes Ergebnis + welche Logs ich bei Fehlern liefern soll.  
> Maximal 5 Rückfragen pro Iteration. Wenn Infos fehlen, markiere Annahmen.  
> Hier ist mein Context Packet:  
> **[PASTE: Repo-Überblick, Build/Test/Run, Akzeptanzkriterien, Repro/Logs, relevante Dateien/Snippets]**  
> Mein Ziel: **[PASTE: Änderung/Erweiterung in 3–8 Bullets]**  
> Gib mir zuerst Project Map + Plan + Patch 1.
