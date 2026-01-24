# Umsetzungsplan & Checkliste – Compounding-Komponente (Entry Analyzer)

## 0. Projekt-Setup
- [ ] Ordner `compounding_component/` anlegen
- [ ] Dateien: `calculator.py`, `ui.py`, `tests/`
- [ ] Abhängigkeiten prüfen: PyQt6, matplotlib, pytest

## 1. Engine (calculator.py)
- [ ] Dataclasses: Params/DayResult/MonthKpis
- [ ] Tageslogik exakt nach Definition
- [ ] Monats-KPIs
- [ ] Flag `apply_losses_to_capital` (Default False)
- [ ] CSV-Formatter

## 2. Solver „Ziel netto im Monat“
- [ ] Grenzen -99%..+1000%
- [ ] Toleranz (0.01€)
- [ ] Binärsuche + Erreichbarkeitsprüfung
- [ ] Status/Fehlertext

## 3. UI Tab 1
- [ ] Eingaben + KPIs
- [ ] „daily_profit_pct“ <-> „target_month_net“ Interaktion
- [ ] Signal-Blocking/Guard

## 4. UI Tab 2
- [ ] Tages-Tabelle
- [ ] Matplotlib Plot (daily vs cumulative)
- [ ] CSV Export + Copy to Clipboard

## 5. Tests
- [ ] 5 Tests inkl. 0% Gewinn, hohe Gebühren, negative pbt, Solver, Rundung

## 6. Integration Entry Analyzer
- [ ] `CompoundingPanel` importieren
- [ ] In Layout einhängen
- [ ] Smoke-Test Dark/Light Host-Theme
