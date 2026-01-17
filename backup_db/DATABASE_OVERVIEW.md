# Database Backup Overview - OrderPilot-AI

**Backup erstellt**: 2026-01-17
**Anzahl Datenbanken**: 3
**Gesamtanzahl Tabellen**: 24

---

## 📁 Backup-Struktur

```
backup_db/
├── .hive-mind/
│   ├── hive.db          (11 Tabellen)
│   └── memory.db        (2 Tabellen)
├── data/
│   └── orderpilot.db    (11 Tabellen)
└── DATABASE_OVERVIEW.md (diese Datei)
```

---

## 🗄️ Datenbankdetails

### 1. `.hive-mind/hive.db`
**Beschreibung**: Hive-Mind Coordination Database
**Ursprungspfad**: `.hive-mind/hive.db`
**Tabellen**: 11

| Tabelle | Zweck |
|---------|-------|
| `agents` | Agent-Konfigurationen und Status |
| `collective_memory` | Gemeinsamer Wissenspool aller Agents |
| `consensus_decisions` | Konsensentscheidungen der Agenten |
| `session_checkpoints` | Sitzungs-Checkpoints für Wiederherstellung |
| `session_logs` | Detaillierte Sitzungsprotokolle |
| `sessions` | Aktive und historische Sitzungen |
| `swarms` | Swarm-Konfigurationen und Topologien |
| `tasks` | Verteilte Task-Verwaltung |
| `sqlite_sequence` | SQLite-interne Sequenzen |
| `sqlite_stat1` | SQLite-Statistiken (Query Optimizer) |
| `sqlite_stat4` | SQLite-Histogramme (Query Optimizer) |

---

### 2. `.hive-mind/memory.db`
**Beschreibung**: Hive-Mind Memory Database
**Ursprungspfad**: `.hive-mind/memory.db`
**Tabellen**: 2

| Tabelle | Zweck |
|---------|-------|
| `memories` | Persistente Agent-Erinnerungen und Kontext |
| `sqlite_sequence` | SQLite-interne Sequenzen |

---

### 3. `data/orderpilot.db`
**Beschreibung**: OrderPilot Main Database
**Ursprungspfad**: `data/orderpilot.db`
**Tabellen**: 11

| Tabelle | Zweck |
|---------|-------|
| `ai_cache` | Cache für AI-Anfragen (Kostenoptimierung) |
| `ai_telemetry` | AI-Nutzungsstatistiken (Tokens, Latenz, Kosten) |
| `alerts` | Trading-Alerts und Benachrichtigungen |
| `audit_log` | Audit-Trail für Compliance und Nachvollziehbarkeit |
| `backtest_results` | Backtest-Ergebnisse und Performance-Metriken |
| `executions` | Ausgeführte Trades und Order-Fills |
| `market_bars` | Historische Marktdaten (OHLCV) |
| `orders` | Order-Historie (offen, ausgeführt, storniert) |
| `positions` | Aktuelle und historische Positionen |
| `strategies` | Strategie-Konfigurationen und -Parameter |
| `system_metrics` | System-Performance und Health-Checks |

---

## 📊 Statistik

### Tabellen nach Kategorie

**Hive-Mind System** (13 Tabellen):
- Coordination: `agents`, `swarms`, `tasks`, `consensus_decisions`
- Sessions: `sessions`, `session_logs`, `session_checkpoints`
- Memory: `collective_memory`, `memories`
- System: `sqlite_sequence`, `sqlite_stat1`, `sqlite_stat4`

**Trading System** (11 Tabellen):
- Core: `orders`, `executions`, `positions`
- Market Data: `market_bars`
- Strategy: `strategies`, `backtest_results`
- AI/Analytics: `ai_cache`, `ai_telemetry`
- Monitoring: `alerts`, `audit_log`, `system_metrics`

---

## 🔄 Wiederherstellung

### Einzelne Datenbank wiederherstellen:
```bash
# Hive-Mind
cp backup_db/.hive-mind/hive.db .hive-mind/hive.db
cp backup_db/.hive-mind/memory.db .hive-mind/memory.db

# OrderPilot Main
cp backup_db/data/orderpilot.db data/orderpilot.db
```

### Alle Datenbanken wiederherstellen:
```bash
cp -r backup_db/.hive-mind/* .hive-mind/
cp -r backup_db/data/* data/
```

---

## ⚠️ Wichtige Hinweise

1. **Vor Wiederherstellung**: Stoppe die Anwendung komplett
2. **Backup vor Restore**: Erstelle ein Backup der aktuellen Dateien
3. **Konsistenz prüfen**: Nach Restore mit `python test_database.py` testen
4. **AI Cache**: `ai_cache` kann gelöscht werden (wird neu aufgebaut)
5. **Audit Log**: `audit_log` niemals löschen (Compliance!)

---

## 🛠️ Wartung

### Datenbank-Integrität prüfen:
```bash
# Hive DBs
sqlite3 .hive-mind/hive.db "PRAGMA integrity_check;"
sqlite3 .hive-mind/memory.db "PRAGMA integrity_check;"

# OrderPilot DB
sqlite3 data/orderpilot.db "PRAGMA integrity_check;"
```

### Datenbank komprimieren (Vacuum):
```bash
sqlite3 data/orderpilot.db "VACUUM;"
```

### Tabellen-Schema anzeigen:
```bash
sqlite3 data/orderpilot.db ".schema orders"
```

---

*Generiert am: 2026-01-17*
*OrderPilot-AI v1.0*
