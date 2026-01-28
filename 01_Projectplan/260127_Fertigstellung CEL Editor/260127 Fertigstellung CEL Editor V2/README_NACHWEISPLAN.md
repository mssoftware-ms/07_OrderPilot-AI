# CEL Editor V2 – Nachweis‑Plan

**Speicherort (Root):**  
`01_Projectplan/260127_Fertigstellung CEL Editor/260127 Fertigstellung CEL Editor V2/`

---

## Ordnerstruktur
- `logs/` – Test‑ und Lauf‑Logs  
- `screenshots/` – UI‑Nachweise  
- `reports/` – Zusammenfassungen

**Konventionen:**
- `logs/`  
  - `2026-01-27_integration_4-2-1_pattern_to_cel.log`  
  - `2026-01-27_integration_4-2-2_ai_to_validation.log`  
  - `2026-01-27_integration_4-2-3_fileops.log`
- `screenshots/`  
  - `2026-01-27_4-2-1_validation_ok.png`  
  - `2026-01-27_4-2-2_ai_generated.png`  
  - `2026-01-27_4-2-3_rulepack_roundtrip.png`
- `reports/`  
  - `2026-01-27_v2_summary.md`

---

## Test‑Befehle (Nachweis)
1. CEL Engine Unit Tests  
   `pytest tests/unit/test_cel_engine_phase1_functions.py -v`

2. CEL Validator Unit Tests  
   `pytest tests/unit/test_cel_validator.py -v`

3. Pattern → CEL Tests  
   `pytest tests/unit/test_pattern_to_cel.py -v`

4. Performance Tests  
   `pytest tests/performance/test_cel_performance.py -v`

**Nachweisformat:**  
Log‑Ausgabe in `logs/` + ggf. Screenshot in `screenshots/`

---

## Integration‑Nachweise (manuell)
**4.2.1 Pattern → CEL → Evaluation**  
1) Pattern erstellen → Generate CEL → Validator ok  
2) Log + Screenshot speichern

**4.2.2 AI Code Generation → Validation**  
1) Prompt → Generate → Auto‑Validation ok  
2) Log + Screenshot speichern

**4.2.3 File Operations → UI Update**  
1) Save RulePack → Reopen → Inhalte korrekt  
2) Log + Screenshot speichern

