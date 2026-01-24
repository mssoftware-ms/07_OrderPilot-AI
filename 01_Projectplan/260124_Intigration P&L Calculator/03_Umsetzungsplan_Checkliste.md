# Umsetzungsplan & Checkliste – Compounding-Komponente (Entry Analyzer)

## 0. Projekt-Setup
- [x] Ordner `compounding_component/` anlegen
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Paket unter `src/ui/widgets/compounding_component/` angelegt*
  Code: `src/ui/widgets/compounding_component/`
  Tests: `tests/compounding_component/test_calculator.py::test_zero_profit_generates_negative_net_due_to_fees_when_no_loss_applied`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`
- [x] Dateien: `calculator.py`, `ui.py`, `tests/`
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Engine + UI + Tests in Zielstruktur abgelegt*
  Code: `src/ui/widgets/compounding_component/calculator.py`
  Tests: `tests/compounding_component/test_calculator.py::test_rounding_cent_half_up`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`
- [x] Abhängigkeiten prüfen: PyQt6, matplotlib, pytest
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *PyQt6 & matplotlib in `requirements.txt`, pytest in dev-Extras*
  Code: `requirements.txt`
  Tests: `tests/compounding_component/test_calculator.py::test_solver_reaches_target_within_tolerance`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`

## 1. Engine (calculator.py)
- [x] Dataclasses: Params/DayResult/MonthKpis
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Dataclasses für Parameter, Tages- und Monatswerte implementiert*
  Code: `src/ui/widgets/compounding_component/calculator.py`
  Tests: `tests/compounding_component/test_calculator.py::test_rounding_cent_half_up`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`
- [x] Tageslogik exakt nach Definition
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Tagesberechnung inkl. Fees/Steuern/Reinvest umgesetzt*
  Code: `src/ui/widgets/compounding_component/calculator.py`
  Tests: `tests/compounding_component/test_calculator.py::test_zero_profit_generates_negative_net_due_to_fees_when_no_loss_applied`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`
- [x] Monats-KPIs
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Aggregierte Monats-KPIs (Summen, ROI) berechnet*
  Code: `src/ui/widgets/compounding_component/calculator.py`
  Tests: `tests/compounding_component/test_calculator.py::test_zero_profit_generates_negative_net_due_to_fees_when_no_loss_applied`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`
- [x] Flag `apply_losses_to_capital` (Default False)
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Optionaler Verlust-Abzug auf Kapitalfluss umgesetzt*
  Code: `src/ui/widgets/compounding_component/calculator.py`
  Tests: `tests/compounding_component/test_calculator.py::test_losses_reduce_capital_when_apply_losses_enabled`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`
- [x] CSV-Formatter
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *CSV-Zeilen-Formatter für Export/Clipboard vorhanden*
  Code: `src/ui/widgets/compounding_component/calculator.py`
  Tests: `tests/compounding_component/test_calculator.py::test_rounding_cent_half_up`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`

## 2. Solver „Ziel netto im Monat“
- [x] Grenzen -99%..+1000%
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Solver-Grenzen mit Validation und Default-Werten gesetzt*
  Code: `src/ui/widgets/compounding_component/calculator.py`
  Tests: `tests/compounding_component/test_calculator.py::test_solver_reaches_target_within_tolerance`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`
- [x] Toleranz (0.01€)
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Toleranz standardmäßig 0.01€*
  Code: `src/ui/widgets/compounding_component/calculator.py`
  Tests: `tests/compounding_component/test_calculator.py::test_solver_reaches_target_within_tolerance`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`
- [x] Binärsuche + Erreichbarkeitsprüfung
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Binärsuche mit monotonicity-check und Range-Prüfung*
  Code: `src/ui/widgets/compounding_component/calculator.py`
  Tests: `tests/compounding_component/test_calculator.py::test_solver_reaches_target_within_tolerance`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`
- [x] Status/Fehlertext
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *SolveStatus mit ok/message/iter info*
  Code: `src/ui/widgets/compounding_component/calculator.py`
  Tests: `tests/compounding_component/test_calculator.py::test_solver_reaches_target_within_tolerance`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`

## 3. UI Tab 1
- [x] Eingaben + KPIs
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Eingabe-Controls + KPI-Labels in Tab 1*
  Code: `src/ui/widgets/compounding_component/ui.py`
  Tests: — (UI)
  Nachweis: Manuell im Entry Analyzer prüfen
- [x] „daily_profit_pct“ <-> „target_month_net“ Interaktion
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Bidirektionale Solver-/KPI-Aktualisierung*
  Code: `src/ui/widgets/compounding_component/ui.py`
  Tests: — (UI)
  Nachweis: Manuell im Entry Analyzer prüfen
- [x] Signal-Blocking/Guard
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *QSignalBlocker + Guard gegen Endlosschleifen*
  Code: `src/ui/widgets/compounding_component/ui.py`
  Tests: — (UI)
  Nachweis: Manuell im Entry Analyzer prüfen

## 4. UI Tab 2
- [x] Tages-Tabelle
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Tages-Tabelle mit 11 Spalten*
  Code: `src/ui/widgets/compounding_component/ui.py`
  Tests: — (UI)
  Nachweis: Manuell im Entry Analyzer prüfen
- [x] Matplotlib Plot (daily vs cumulative)
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Matplotlib-Plot mit Umschaltmodus*
  Code: `src/ui/widgets/compounding_component/ui.py`
  Tests: — (UI)
  Nachweis: Manuell im Entry Analyzer prüfen
- [x] CSV Export + Copy to Clipboard
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *CSV-Export und Clipboard-Export implementiert*
  Code: `src/ui/widgets/compounding_component/ui.py`
  Tests: — (UI)
  Nachweis: Manuell im Entry Analyzer prüfen

## 5. Tests
- [x] 5 Tests inkl. 0% Gewinn, hohe Gebühren, negative pbt, Solver, Rundung
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *5 Pytest-Cases für Engine & Solver*
  Code: `tests/compounding_component/test_calculator.py`
  Tests: `tests/compounding_component/test_calculator.py`
  Nachweis: `01_Projectplan/260124_Intigration P&L Calculator/pytest_compounding_20260124.log`

## 6. Integration Entry Analyzer
- [x] `CompoundingPanel` importieren
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *CompoundingPanel im Entry Analyzer Mix-in eingebunden*
  Code: `src/ui/dialogs/entry_analyzer/entry_analyzer_compounding_mixin.py`
  Tests: — (UI)
  Nachweis: Manuell im Entry Analyzer prüfen
- [x] In Layout einhängen
  Status: ✅ Abgeschlossen (2026-01-24 13:11) → *Tab "P&L Calculator" im Entry Analyzer hinzugefügt*
  Code: `src/ui/dialogs/entry_analyzer/entry_analyzer_popup.py`
  Tests: — (UI)
  Nachweis: Manuell im Entry Analyzer prüfen
- [ ] Smoke-Test Dark/Light Host-Theme
  Status: ⏳ Offen → *Bitte manuell im UI testen (Dark/Light Themes)*
  Code: `src/ui/dialogs/entry_analyzer/entry_analyzer_popup.py`
  Tests: — (UI)
  Nachweis: Screenshot/Log nach manuellem Test
