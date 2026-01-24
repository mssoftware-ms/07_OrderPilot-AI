# Projektzielbeschreibung – Compounding-/Zinseszins-Rechner (PyQt6-Komponente)

## Kontext
Ein **einbettbares PyQt6-Widget** für deine Trading-Software (Integration im Fenster **„Entry Analyzer“**).  
Es berechnet Compounding (Zinseszins) mit **Gebühren, Hebel, Steuern** und **Reinvestitionsquote** und visualisiert die Ergebnisse für einen konfigurierbaren Monatszeitraum (Default: 30 Tage).

## Ziele (Definition of Done)
- Engine ist **UI-unabhängig** (`calculator.py` ohne Qt-Imports).
- UI ist **einbettbar** (`CompoundingPanel(QWidget)`) und nutzt 2 Tabs.
- **Live-Updates** bei jeder Änderung; keine Signal-Endlosschleifen (QSignalBlocker/Guard).  
- **Theme-kompatibel**: keine hardcodierten Farben; Standard-Qt-Palette/Styles werden übernommen.  
- Matplotlib ist **eingebettet** (FigureCanvasQTAgg) gemäß offizieller Patterns.  
- Tages-Tabelle + Plot (Tag 1..N, Y=Netto) inkl. optional „kumuliert“.
- Solver: „Ziel netto im Monat“ passt `daily_profit_pct` robust an (Binärsuche) und liefert Status/Fehler.
- Tests (pytest) mit mind. 5 Fällen inkl. Edge-Cases.
- Optional: CSV-Export + Copy-to-Clipboard.

## Versionen (gegeben)
- PyQt6 6.10.0
- matplotlib 3.10.7
