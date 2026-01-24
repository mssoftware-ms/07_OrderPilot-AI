# Architektur, Code & Tests – Compounding-Komponente

## Struktur
```
compounding_component/
  calculator.py
  ui.py
  tests/
    test_calculator.py
```

## Kurzbeschreibung
- `calculator.py`: Reine Engine (Decimal, Cent-Rundung, Tageslogik, Solver)
- `ui.py`: `CompoundingPanel(QWidget)` mit Tabs, Tabelle, Plot, CSV/Clipboard
- `tests/`: pytest Edge-Cases inkl. Solver & Rundung

## Tests
```bash
pytest -q
```
