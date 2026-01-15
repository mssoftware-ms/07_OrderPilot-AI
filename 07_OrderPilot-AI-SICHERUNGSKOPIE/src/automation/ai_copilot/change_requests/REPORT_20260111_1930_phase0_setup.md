# Report: Phase 0 Setup - Entry Analyzer

**Datum:** 2026-01-11 19:30
**Branch:** ai/entry-analyzer-20260111-visible-chart
**Status:** ✅ Abgeschlossen

---

## Ziel des Tasks

Phase 0: Reset, Struktur & Guardrails gemäß Projektplan einrichten.

---

## Betroffene Dateien

### Neu erstellt
| Datei | Zweck |
|-------|-------|
| `scripts/check_line_limit.py` | Line-Limit Gate (≤600 Zeilen pro .py) |
| `scripts/quality_gate.sh` | Kombinierter Quality-Check (ruff + pytest + line-limit) |
| `src/analysis/visible_chart/__init__.py` | Modul-Init für Visible-Chart-Analyse |
| `src/analysis/entry_signals/__init__.py` | Modul-Init für Entry-Signale |
| `src/analysis/regime/__init__.py` | Modul-Init für Regime-Erkennung |
| `src/runtime/__init__.py` | Modul-Init für Background-Worker |
| `src/automation/ai_copilot/__init__.py` | Modul-Init für KI-Copilot |

### Neue Ordnerstruktur
```
src/
├── analysis/
│   ├── visible_chart/        # Visible-Chart Analyzer
│   ├── entry_signals/        # Entry-Scoring + Postprocess
│   ├── regime/               # Regime-Erkennung
│   ├── features/families/    # Feature-Familien
│   └── indicator_optimization/
├── runtime/                  # Background-Worker
└── automation/ai_copilot/
    └── change_requests/      # CLI-KI Anweisungen
```

---

## Was geändert wurde

1. **Line-Limit Gate** implementiert:
   - Script `check_line_limit.py` prüft alle .py unter src/
   - Exit Code 1 bei Verstoß (≤600 Zeilen)
   - 20 bestehende Legacy-Dateien überschreiten aktuell das Limit (dokumentiert)

2. **Quality Gate Script** erstellt:
   - Kombiniert: `ruff format --check`, `ruff check`, `pytest -q`, line-limit
   - Muss vor jedem Merge grün sein

3. **Modul-Layout** angelegt:
   - Alle neuen Module gemäß Projektplan unter `src/`
   - Klare `__init__.py` mit Docstrings

---

## Risiko/Regressionen

- **Niedrig**: Keine bestehende Funktionalität geändert
- **Legacy-Dateien**: 20 Dateien mit >600 Zeilen bleiben unverändert (bekanntes Tech-Debt)
- Die Legacy-Dateien enden größtenteils auf `_old`, `_ORIGINAL`, `_backup`

---

## Tests/Commands

```bash
# Line-Limit Check
python3 scripts/check_line_limit.py
# Ergebnis: 20 violations (Legacy, erwartet)

# Quality Gate (erwartet: fail wegen Legacy)
bash scripts/quality_gate.sh
```

---

## Nächster Schritt

**Phase 1.1:** Popup-Skeleton `EntryAnalyzerPopup` in Chartansicht integrieren
- Integrationspunkt: `embedded_tradingview_chart_ui_mixin.py:_show_marking_context_menu()`
- Neuer Menüeintrag: "Analyze Visible Range"
