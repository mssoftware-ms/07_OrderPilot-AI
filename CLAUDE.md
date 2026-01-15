# OrderPilot-AI – Projektkontext für Claude Code

Dieses Dokument definiert, wie du (Claude Code) in diesem Repository arbeiten sollst:
- Ziel: stabile Trading-Plattform mit Alpaca (Trading + Market Data + Streaming, inkl. Crypto, News).
- Fokus: saubere Architektur, nachvollziehbare Änderungen, kein gefährlicher Live-Handel ohne ausdrückliche Anweisung.

---

## 0. Arbeitsmodus für Änderungen in großen Repos (≈35k+ LOC)
WICHTIG: Wenn du nach 2 Iterationen vom gleichen Fehler nicht zu einer Lösung gekommen bist, suche im web nach einer Lösung für das Problem!
Für alle Änderungen/Erweiterungen gilt: **arbeite nach dem Runbook**:

- `docs/ai/change-workflow.md` (voller Prozess)
- `docs/ai/context-packet-template.md` (Template, das du von mir anforderst)

**Regeln (Kurzform):**
- Max. **5 Rückfragen** pro Iteration; fehlende Infos als **„Annahme:"** markieren.
- Erst **Project Map**, dann **Plan (3–7 Schritte)**, dann **Patch 1**.
- **Kleine, testbare Patches**: Patch → Checks → nächster Patch (rückrollbar, minimal).
- **Search-Driven Development**: erst `rg/grep`, dann ändern (keine Bauchentscheidungen).
- Immer liefern: **Unified Diff**, **Verifikations-Commands**, **Erwartetes Ergebnis** + **welche Logs** ich bei Fehlern liefern soll.

### Architektur-Dokumentation (ARCHITECTURE.md)

**Vor jeder strukturellen Änderung:**
1. Lies `ARCHITECTURE.md` im Projekt-Root, um die aktuelle Architektur zu verstehen.
2. Prüfe, welche Schichten, Mixins und Provider betroffen sind.
3. Beachte die dokumentierten Datenflüsse und Event-Bus-Patterns.

**Nach jeder strukturellen Änderung:**
- **Aktualisiere `ARCHITECTURE.md`** wenn du:
  - Neue Module, Klassen oder Mixins hinzufügst
  - Bestehende Schichten oder Datenflüsse änderst
  - Provider oder Strategien hinzufügst/entfernst
  - Event-Typen oder Interfaces änderst
- Halte die Diagramme und Verzeichnisstruktur synchron mit dem Code.

**Strukturelle Änderungen umfassen:**
- Neue Dateien/Module anlegen
- Klassen zwischen Dateien verschieben
- Mixin-Hierarchien ändern
- Provider/Strategien hinzufügen
- Event-Bus-Kanäle erweitern


## 1. Projektüberblick

**OrderPilot-AI** ist eine Python-basierte Trading-Anwendung mit folgenden Zielen:

- Live-Marktdaten (Aktien, Crypto, ggf. weitere Assetklassen) über Alpaca Market Data API.
- Orderaufgabe, Positions- und Kontoverwaltung über Alpaca Trading API.
- Streaming (WebSockets / SSE) für Markt- und Kontoevents, später Strategie-Signale.
- Mittelfristig: Skript-/Strategie-Engine, Backtesting, Visualisierung.

Du sollst primär unterstützen bei:

- Architektur- und API-Design (Alpaca-Connectoren, Streaming-Clients, interne Services).
- Implementierung und Refactoring von Python-Code.
- Stabilisierung (Fehlerbehebung, Logging, Tests).
- Erzeugen von technischer Dokumentation (README, Modul-Docs, Entwickler-Guides).

---

## 2. Technischer Rahmen

- Sprache: **Python** (aktuelle Projektversion den Konfigurationsdateien entnehmen, z. B. `pyproject.toml` oder `requirements.txt`).
- Stil: **PEP 8**, konsequente Typannotationen.
- Architektur: Schichtenmodell, keine direkten API-Calls aus der UI.
- Eventuell vorhandene Frameworks (UI, Web, etc.) aus dem bestehenden Code ableiten und respektieren.
- Virtuelle Umgebung: vorhandene `.venv` / Setup-Anweisungen im Repo verwenden, nicht frei erfinden.

Wenn du Bibliotheken vorschlägst:
- Bevorzuge etablierte, gut gepflegte Pakete.
- Prüfe zuerst, ob im Repo bereits ein Paket genutzt wird (z. B. `alpaca-py`, `websockets`, `httpx`, `requests`) und halte dich daran.

---

## 3. Wichtige Verzeichnisse (relativ zum Projekt-Root)

Diese Pfade können bereits existieren oder sollen von dir konsistent genutzt/angelegt werden:

- `src/`  
  - Kernanwendung (Module, Services, Domain-Logik).
- `src/brokers/alpaca/`  
  - Alpaca-spezifische REST-Clients, Streaming-Clients, DTOs, Mappings.
- `src/core/`  
  - Allgemeine Infrastruktur (Konfiguration, Logging, Event-Bus, Utility-Funktionen).
- `src/strategies/`  
  - Strategielogik, Signalgeneratoren (später).
- `src/ui/`  
  - UI-Code (CLI, GUI oder Web – an bestehendem Code orientieren).
- `tests/`  
  - Pytest-Tests, ggf. Unterordner analog zur `src`-Struktur.
- `docs/`  
  - Projektdokumentation.
- `docs/alpaca/`  
  - **Alpaca-spezifische Dokumentation**, siehe nächster Abschnitt.

Wenn ein hier genannter Ordner noch nicht existiert, kannst du ihn vorschlagen/anlegen, wenn es die Architektur vereinfacht.

---

## 4. Alpaca API – verbindliche Dokumentation

Das Trainingswissen über Alpaca kann veraltet sein. Für alle Implementierungen rund um Alpaca gelten **ausschließlich die lokalen Dateien in `docs/alpaca` als Quelle der Wahrheit**.

**Spiegel der offiziellen Doku:**

- `docs/alpaca/docs.alpaca.markets/`  
  Lokal gespiegelt von `https://docs.alpaca.markets`.  
  Enthält Artikel zu:
  - Trading API (Orders, Positions, Accounts, Clock, Calendar, Assets, etc.)
  - Market Data API (Stock, Crypto, Options, News – REST & Streaming)
  - Streaming/WebSockets/SSE
  - OAuth / Connect / Broker API

**OpenAPI-Spezifikationen:**

- `docs/alpaca/alpaca_openapi/trading-api.json`
- `docs/alpaca/alpaca_openapi/market-data-api.json`
- `docs/alpaca/alpaca_openapi/broker-api.json`
- `docs/alpaca/alpaca_openapi/authx.yaml`

**LLM-Index von Alpaca:**

- `docs/alpaca/llms.txt`  
  Enthält eine kuratierte Liste wichtiger Doku-Links, speziell für LLM-Nutzung.

### Verbindliche Regeln für Alpaca-Code

1. **Vertraue den lokalen Alpaca-Docs mehr als deinem Trainingswissen.**  
   Wenn etwas nicht übereinstimmt, richte dich nach den Dateien in `docs/alpaca/`.
2. Bevor du neue Funktionen für Alpaca Trading/Market-Data/Streaming implementierst oder änderst:
   - ziehe die passende OpenAPI-Datei heran (z. B. `trading-api.json`, `market-data-api.json`);
   - prüfe im Doku-Mirror (`docs.alpaca.markets`), wie Endpunkte und Streaming-Kanäle beschrieben sind.
3. **Keine Endpunkte raten oder erfinden.**  
   Nutze nur Pfade, Parameter und Modelle, die in den OpenAPI-Files stehen.
4. Beachte Unterschiede zwischen:
   - Live- vs. Paper-Trading-Endpoint,
   - verschiedenen Data-Feeds (Stock, Crypto, Options, News),
   - REST vs. Streaming (WebSocket, SSE).

---

## 5. Trading-Sicherheitsregeln

Ziel ist es, gefährliche Situationen zu vermeiden, insbesondere unbeabsichtigten Real-Handel.

1. **Standard immer: Paper-Trading.**  
   - Jede neue Funktion oder Änderung soll standardmäßig Paper-Umgebungen verwenden.  
   - Wenn du zwischen Live/Paper unterscheidest, verwende eine explizite Konfiguration (z. B. `TRADING_ENV=paper|live`).
2. **Keine Änderung an produktiven Zugangsdaten.**  
   - `.env`, Secrets oder API-Keys nur lesen/verbrauchen, niemals ins Repo schreiben.  
   - Keine Dummy-Keys erfinden, die wie echte Keys aussehen.
3. **Keine „versteckten“ Side-Effects.**  
   - Funktionen, die Orders auslösen oder Positionen schließen, müssen eindeutig benannt sein und klar dokumentiert werden.
4. **Bei Code-Änderungen an Order-Logik:**  
   - Schreibe/aktualisiere Unit-Tests oder zumindest Dry-Run-Simulationen.  
   - Beschreibe im Ergebnis immer, welche Risiken sich ändern (z. B. doppelte Order, Fehlausführung, Time-in-Force).

Wenn ich (der menschliche Entwickler) ausdrücklich Live-Trading möchte, wird das klar im Prompt erwähnt. Ohne diese explizite Anweisung sollst du immer auf Sicherheit und Paper-Umgebung optimieren.

---

## 6. Architektur-Vorgaben

### Schichten

Bevorzuge eine klare Trennung:

1. **Adapter / Connectors (`src/brokers/alpaca/…`)**
   - Dünne Wrapper um Alpaca-REST/WS/SSE-Endpunkte.
   - Keine Geschäftslogik, nur Übersetzung: Python ↔ HTTP/JSON/WebSocket-Frames.
2. **Domain-Services (`src/core/…` / `src/services/…`)**
   - Handelslogik, Positionsverwaltung, Portfolio-Berechnungen.
   - Arbeiten gegen Interfaces / abstrakte Klassen, nicht direkt gegen HTTP.
3. **Strategien (`src/strategies/…`)**
   - Regeln, Signale, Einstiegs-/Ausstiegskriterien.
4. **UI / API (`src/ui/…`)**
   - Anzeige, Interaktion, keine direkten REST-Aufrufe an Alpaca.  
   - UI ruft Domain-Services auf, nicht Broker-Adapter direkt.

### Async / Streaming

- Nutze konsistent `asyncio`, wenn Streaming/WebSockets implementiert werden.
- Entweder:
  - **Async-Client** + Event-Loop zentral verwalten, oder
  - klare Hintergrund-Worker-Prozesse/Threads, die Streams konsumieren.
- Keine verschachtelten Event-Loops starten; wenn ein Framework (z. B. qasync, FastAPI) bereits einen Loop kontrolliert, hänge dich daran.

---

## 7. Coding-Guidelines

- PEP-8 einhalten, sinnvolle Namen, kurze Funktionen.
- Konsequent Typannotationen verwenden (`from __future__ import annotations` bei Bedarf).
- Für Domänenobjekte: bevorzugt `dataclasses` oder Pydantic-Modelle, wenn bereits im Projekt genutzt.
- Fehlerbehandlung:
  - API-Fehler (HTTP-Status, Rate-Limits, Netzwerkfehler) klar unterscheiden.
  - Exceptions nicht pauschal schlucken; logge genug Kontext (Endpoint, Status, Payload).
- Logging:
  - Verwende das bestehende Logging-Setup; falls keines vorhanden ist, schlage ein standardisiertes `logging`-Setup vor (`src/core/logging.py`).

---

## 8. Tests & Qualität

Wenn du Fehler behebst oder neue Funktionen einführst:

1. **Reproduktion verstehen**
   - Beschreibe in deinen Notizen, wie der Fehler sich äußert.
2. **Bestehende Tests prüfen**
   - Suche in `tests/` nach relevanten Dateien (z. B. `test_alpaca_*.py`).
3. **Tests ergänzen**
   - Schreibe neue Unit-Tests oder passe bestehende an, um den Fehler zu reproduzieren.
4. **Änderung umsetzen**
   - Nur die minimal notwendige Änderung im Code ausführen, keine unbeteiligten Teile umformatieren.
5. **Tests ausführen**
   - Wenn möglich, Test-Befehle angeben (`pytest tests/...`) und im Ergebnis zusammenfassen, welche Tests nun erfolgreich sind.
6. **Ergebnis dokumentieren**
   - In deiner Antwort klar beschreiben:
     - welche Dateien geändert wurden,
     - welche neuen Tests existieren,
     - wie sich das Verhalten geändert hat.

---

## 9. Arbeitsweise von Claude in diesem Repo

Wenn du eine Aufgabe erhältst (Bugfix, Feature, Refactoring), gehe i. d. R. so vor:

1. **Kontext sammeln**
   - Relevante Dateien und Module identifizieren (z. B. durch Suche nach Klassennamen, Funktionsnamen, Pfaden).
   - Bei Alpaca-Themen: zuerst die passende Doku in `docs/alpaca/` prüfen.
2. **Problem formulieren**
   - Kurz in eigenen Worten zusammenfassen, was technisch erreicht werden soll.
3. **Plan erstellen**
   - Eine klare, nummerierte Liste von Schritten schreiben (Dateien, Klassen, Funktionen, die du ändern willst).
   - Plan zuerst darstellen, bevor du große Änderungen vornimmst.
4. **Änderungen durchführen**
   - Fokus auf kleine, konsistente Commits/Änderungsblöcke.
   - Keine nicht benötigten Stil-/Format-Änderungen in vielen Dateien.
5. **Tests/Checks**
   - Vorschlagen, welche Tests oder Checks lokal laufen sollten.
6. **Zusammenfassung**
   - Am Ende deiner Antwort eine kurze technische Zusammenfassung (Was wurde geändert? Warum? Welche Risiken bleiben?).

---

## 10. Bekannte Fehlertypen & worauf du achten sollst

- **Veraltete Alpaca-Endpunkte**  
  → Immer gegen OpenAPI-Specs aus `docs/alpaca/alpaca_openapi/` prüfen, bevor du neue REST-Calls oder Streaming-Subscriptions einbaust.
- **Verwechslung Live/Paper**  
  → Bei neuen Configs immer klar zwischen Live- und Paper-Base-URLs trennen, Standard = Paper.
- **Fehlerhafte Streaming-Implementierung**
  → Achte darauf:
    - Reconnect-Logik bei Verbindungsabbrüchen,
    - sauberes Schließen von Verbindungen,
    - keine Blockierung des Event-Loops durch CPU-intensive Arbeit.

Wenn du erkennst, dass du wiederholt denselben Fehler machst (z. B. einen bestimmten Alpaca-Endpoint falsch verwendest), ergänze die relevanten Hinweise in dieser `CLAUDE.md`.

---

## 11. Kommunikation

- Antworte präzise und technisch; keine überflüssigen Floskeln.
- Wenn Annahmen nötig sind (z. B. zu Frameworks oder Projektstruktur), benenne sie explizit.
- Wenn dir Informationen fehlen, schlage gezielte Schritte vor (z. B. „Bitte gib mir die aktuelle `pyproject.toml`, damit ich die Laufzeitumgebung sehe"), statt ins Blaue zu implementieren.

---

## 12. Projektplan & Dokumentation

### .kipj-Datei (Projekt-Snapshot)

Die Datei `01_Projectplan/orderpilot-ai.kipj` (sowie `docs/ai/07_orderpilot-ai.kipj`) enthält einen vollständigen Snapshot der aktuellen Softwarestruktur inkl. aller Klassen, Funktionen und Kommentare.

**Regeln:**
1. **Nach jeder strukturellen Änderung** (neue Module, Klassen, Funktionen hinzugefügt/entfernt) soll die `.kipj`-Datei aktualisiert werden.
2. Die `.kipj`-Datei dient als Referenz für den aktuellen Softwarestand und sollte immer synchron mit dem Code gehalten werden.
3. Bei der Analyse neuer Anforderungen sollte diese Datei als Ausgangspunkt verwendet werden.
4. Alle API Keys sind in den Systemvariabeln von Windows.
5. Die code Entwicklung findet unter WSL statt (CLI Tools wie Claude-Code, Codex CLI), aber die App wird ausschließlich unter windows 11 gestartet

#####################################################################################################################

# Claude Code Configuration - SPARC Development Environment

## 🚨 CRITICAL: CONCURRENT EXECUTION & FILE MANAGEMENT

**ABSOLUTE RULES**:
1. ALL operations MUST be concurrent/parallel in a single message
2. **NEVER save working files, text/mds and tests to the root folder**
3. ALWAYS organize files in appropriate subdirectories
4. **USE CLAUDE CODE'S TASK TOOL** for spawning agents concurrently, not just MCP

### ⚡ GOLDEN RULE: "1 MESSAGE = ALL RELATED OPERATIONS"

**MANDATORY PATTERNS:**
- **TodoWrite**: ALWAYS batch ALL todos in ONE call (5-10+ todos minimum)
- **Task tool (Claude Code)**: ALWAYS spawn ALL agents in ONE message with full instructions
- **File operations**: ALWAYS batch ALL reads/writes/edits in ONE message
- **Bash commands**: ALWAYS batch ALL terminal operations in ONE message
- **Memory operations**: ALWAYS batch ALL memory store/retrieve in ONE message

### 🎯 CRITICAL: Claude Code Task Tool for Agent Execution

**Claude Code's Task tool is the PRIMARY way to spawn agents:**
```javascript
// ✅ CORRECT: Use Claude Code's Task tool for parallel agent execution
[Single Message]:
  Task("Research agent", "Analyze requirements and patterns...", "researcher")
  Task("Coder agent", "Implement core features...", "coder")
  Task("Tester agent", "Create comprehensive tests...", "tester")
  Task("Reviewer agent", "Review code quality...", "reviewer")
  Task("Architect agent", "Design system architecture...", "system-architect")
```

**MCP tools are ONLY for coordination setup:**
- `mcp__claude-flow__swarm_init` - Initialize coordination topology
- `mcp__claude-flow__agent_spawn` - Define agent types for coordination
- `mcp__claude-flow__task_orchestrate` - Orchestrate high-level workflows

### 📁 File Organization Rules

**NEVER save to root folder. Use these directories:**
- `/src` - Source code files
- `/tests` - Test files
- `/docs` - Documentation and markdown files
- `/config` - Configuration files
- `/scripts` - Utility scripts
- `/examples` - Example code

## Project Overview

This project uses SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) methodology with Claude-Flow orchestration for systematic Test-Driven Development.

## SPARC Commands

### Core Commands
- `npx claude-flow sparc modes` - List available modes
- `npx claude-flow sparc run <mode> "<task>"` - Execute specific mode
- `npx claude-flow sparc tdd "<feature>"` - Run complete TDD workflow
- `npx claude-flow sparc info <mode>` - Get mode details

### Batchtools Commands
- `npx claude-flow sparc batch <modes> "<task>"` - Parallel execution
- `npx claude-flow sparc pipeline "<task>"` - Full pipeline processing
- `npx claude-flow sparc concurrent <mode> "<tasks-file>"` - Multi-task processing

### Build Commands
- `npm run build` - Build project
- `npm run test` - Run tests
- `npm run lint` - Linting
- `npm run typecheck` - Type checking

## SPARC Workflow Phases

1. **Specification** - Requirements analysis (`sparc run spec-pseudocode`)
2. **Pseudocode** - Algorithm design (`sparc run spec-pseudocode`)
3. **Architecture** - System design (`sparc run architect`)
4. **Refinement** - TDD implementation (`sparc tdd`)
5. **Completion** - Integration (`sparc run integration`)

## Code Style & Best Practices

- **Modular Design**: Files under 500 lines
- **Environment Safety**: Never hardcode secrets
- **Test-First**: Write tests before implementation
- **Clean Architecture**: Separate concerns
- **Documentation**: Keep updated

## 🚀 Available Agents (54 Total)

### Core Development
`coder`, `reviewer`, `tester`, `planner`, `researcher`

### Swarm Coordination
`hierarchical-coordinator`, `mesh-coordinator`, `adaptive-coordinator`, `collective-intelligence-coordinator`, `swarm-memory-manager`

### Consensus & Distributed
`byzantine-coordinator`, `raft-manager`, `gossip-coordinator`, `consensus-builder`, `crdt-synchronizer`, `quorum-manager`, `security-manager`

### Performance & Optimization
`perf-analyzer`, `performance-benchmarker`, `task-orchestrator`, `memory-coordinator`, `smart-agent`

### GitHub & Repository
`github-modes`, `pr-manager`, `code-review-swarm`, `issue-tracker`, `release-manager`, `workflow-automation`, `project-board-sync`, `repo-architect`, `multi-repo-swarm`

### SPARC Methodology
`sparc-coord`, `sparc-coder`, `specification`, `pseudocode`, `architecture`, `refinement`

### Specialized Development
`backend-dev`, `mobile-dev`, `ml-developer`, `cicd-engineer`, `api-docs`, `system-architect`, `code-analyzer`, `base-template-generator`

### Testing & Validation
`tdd-london-swarm`, `production-validator`

### Migration & Planning
`migration-planner`, `swarm-init`

## 🎯 Claude Code vs MCP Tools

### Claude Code Handles ALL EXECUTION:
- **Task tool**: Spawn and run agents concurrently for actual work
- File operations (Read, Write, Edit, MultiEdit, Glob, Grep)
- Code generation and programming
- Bash commands and system operations
- Implementation work
- Project navigation and analysis
- TodoWrite and task management
- Git operations
- Package management
- Testing and debugging

### MCP Tools ONLY COORDINATE:
- Swarm initialization (topology setup)
- Agent type definitions (coordination patterns)
- Task orchestration (high-level planning)
- Memory management
- Neural features
- Performance tracking
- GitHub integration

**KEY**: MCP coordinates the strategy, Claude Code's Task tool executes with real agents.

## 🚀 Quick Setup

```bash
# Add MCP servers (Claude Flow required, others optional)
claude mcp add claude-flow npx claude-flow@alpha mcp start
claude mcp add ruv-swarm npx ruv-swarm mcp start  # Optional: Enhanced coordination
claude mcp add flow-nexus npx flow-nexus@latest mcp start  # Optional: Cloud features
```

## MCP Tool Categories

### Coordination
`swarm_init`, `agent_spawn`, `task_orchestrate`

### Monitoring
`swarm_status`, `agent_list`, `agent_metrics`, `task_status`, `task_results`

### Memory & Neural
`memory_usage`, `neural_status`, `neural_train`, `neural_patterns`

### GitHub Integration
`github_swarm`, `repo_analyze`, `pr_enhance`, `issue_triage`, `code_review`

### System
`benchmark_run`, `features_detect`, `swarm_monitor`

### Flow-Nexus MCP Tools (Optional Advanced Features)
Flow-Nexus extends MCP capabilities with 70+ cloud-based orchestration tools:

**Key MCP Tool Categories:**
- **Swarm & Agents**: `swarm_init`, `swarm_scale`, `agent_spawn`, `task_orchestrate`
- **Sandboxes**: `sandbox_create`, `sandbox_execute`, `sandbox_upload` (cloud execution)
- **Templates**: `template_list`, `template_deploy` (pre-built project templates)
- **Neural AI**: `neural_train`, `neural_patterns`, `seraphina_chat` (AI assistant)
- **GitHub**: `github_repo_analyze`, `github_pr_manage` (repository management)
- **Real-time**: `execution_stream_subscribe`, `realtime_subscribe` (live monitoring)
- **Storage**: `storage_upload`, `storage_list` (cloud file management)

**Authentication Required:**
- Register: `mcp__flow-nexus__user_register` or `npx flow-nexus@latest register`
- Login: `mcp__flow-nexus__user_login` or `npx flow-nexus@latest login`
- Access 70+ specialized MCP tools for advanced orchestration

## 🚀 Agent Execution Flow with Claude Code

### The Correct Pattern:

1. **Optional**: Use MCP tools to set up coordination topology
2. **REQUIRED**: Use Claude Code's Task tool to spawn agents that do actual work
3. **REQUIRED**: Each agent runs hooks for coordination
4. **REQUIRED**: Batch all operations in single messages

### Example Full-Stack Development:

```javascript
// Single message with all agent spawning via Claude Code's Task tool
[Parallel Agent Execution]:
  Task("Backend Developer", "Build REST API with Express. Use hooks for coordination.", "backend-dev")
  Task("Frontend Developer", "Create React UI. Coordinate with backend via memory.", "coder")
  Task("Database Architect", "Design PostgreSQL schema. Store schema in memory.", "code-analyzer")
  Task("Test Engineer", "Write Jest tests. Check memory for API contracts.", "tester")
  Task("DevOps Engineer", "Setup Docker and CI/CD. Document in memory.", "cicd-engineer")
  Task("Security Auditor", "Review authentication. Report findings via hooks.", "reviewer")
  
  // All todos batched together
  TodoWrite { todos: [...8-10 todos...] }
  
  // All file operations together
  Write "backend/server.js"
  Write "frontend/App.jsx"
  Write "database/schema.sql"
```

## 📋 Agent Coordination Protocol

### Every Agent Spawned via Task Tool MUST:

**1️⃣ BEFORE Work:**
```bash
npx claude-flow@alpha hooks pre-task --description "[task]"
npx claude-flow@alpha hooks session-restore --session-id "swarm-[id]"
```

**2️⃣ DURING Work:**
```bash
npx claude-flow@alpha hooks post-edit --file "[file]" --memory-key "swarm/[agent]/[step]"
npx claude-flow@alpha hooks notify --message "[what was done]"
```

**3️⃣ AFTER Work:**
```bash
npx claude-flow@alpha hooks post-task --task-id "[task]"
npx claude-flow@alpha hooks session-end --export-metrics true
```

## 🎯 Concurrent Execution Examples

### ✅ CORRECT WORKFLOW: MCP Coordinates, Claude Code Executes

```javascript
// Step 1: MCP tools set up coordination (optional, for complex tasks)
[Single Message - Coordination Setup]:
  mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 6 }
  mcp__claude-flow__agent_spawn { type: "researcher" }
  mcp__claude-flow__agent_spawn { type: "coder" }
  mcp__claude-flow__agent_spawn { type: "tester" }

// Step 2: Claude Code Task tool spawns ACTUAL agents that do the work
[Single Message - Parallel Agent Execution]:
  // Claude Code's Task tool spawns real agents concurrently
  Task("Research agent", "Analyze API requirements and best practices. Check memory for prior decisions.", "researcher")
  Task("Coder agent", "Implement REST endpoints with authentication. Coordinate via hooks.", "coder")
  Task("Database agent", "Design and implement database schema. Store decisions in memory.", "code-analyzer")
  Task("Tester agent", "Create comprehensive test suite with 90% coverage.", "tester")
  Task("Reviewer agent", "Review code quality and security. Document findings.", "reviewer")
  
  // Batch ALL todos in ONE call
  TodoWrite { todos: [
    {id: "1", content: "Research API patterns", status: "in_progress", priority: "high"},
    {id: "2", content: "Design database schema", status: "in_progress", priority: "high"},
    {id: "3", content: "Implement authentication", status: "pending", priority: "high"},
    {id: "4", content: "Build REST endpoints", status: "pending", priority: "high"},
    {id: "5", content: "Write unit tests", status: "pending", priority: "medium"},
    {id: "6", content: "Integration tests", status: "pending", priority: "medium"},
    {id: "7", content: "API documentation", status: "pending", priority: "low"},
    {id: "8", content: "Performance optimization", status: "pending", priority: "low"}
  ]}
  
  // Parallel file operations
  Bash "mkdir -p app/{src,tests,docs,config}"
  Write "app/package.json"
  Write "app/src/server.js"
  Write "app/tests/server.test.js"
  Write "app/docs/API.md"
```

### ❌ WRONG (Multiple Messages):
```javascript
Message 1: mcp__claude-flow__swarm_init
Message 2: Task("agent 1")
Message 3: TodoWrite { todos: [single todo] }
Message 4: Write "file.js"
// This breaks parallel coordination!
```

## Performance Benefits

- **84.8% SWE-Bench solve rate**
- **32.3% token reduction**
- **2.8-4.4x speed improvement**
- **27+ neural models**

## Hooks Integration

### Pre-Operation
- Auto-assign agents by file type
- Validate commands for safety
- Prepare resources automatically
- Optimize topology by complexity
- Cache searches

### Post-Operation
- Auto-format code
- Train neural patterns
- Update memory
- Analyze performance
- Track token usage

### Session Management
- Generate summaries
- Persist state
- Track metrics
- Restore context
- Export workflows

## Advanced Features (v2.0.0)

- 🚀 Automatic Topology Selection
- ⚡ Parallel Execution (2.8-4.4x speed)
- 🧠 Neural Training
- 📊 Bottleneck Analysis
- 🤖 Smart Auto-Spawning
- 🛡️ Self-Healing Workflows
- 💾 Cross-Session Memory
- 🔗 GitHub Integration

## Integration Tips

1. Start with basic swarm init
2. Scale agents gradually
3. Use memory for context
4. Monitor progress regularly
5. Train patterns from success
6. Enable hooks automation
7. Use GitHub tools first
WICHTIG: Wenn du nach 2 Iterationen vom gleichen Fehler nicht zu einer Lösung gekommen bist, suche im web nach einer Lösung für das Problem!
## Support

- Documentation: https://github.com/ruvnet/claude-flow
- Issues: https://github.com/ruvnet/claude-flow/issues
- Flow-Nexus Platform: https://flow-nexus.ruv.io (registration required for cloud features)

---

Remember: **Claude Flow coordinates, Claude Code creates!**

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
Never save working files, text/mds and tests to the root folder.






