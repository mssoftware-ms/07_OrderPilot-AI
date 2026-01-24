# Integration – Entry Analyzer (Host-App)

## Minimal
```python
from compounding_component.ui import CompoundingPanel

self.compounding_panel = CompoundingPanel(parent=self)
entry_analyzer_layout.addWidget(self.compounding_panel)
```

## Hinweise
- Keine fixen Farben; Theme kommt vom Host (Qt-Palette).
- `simulate()` ist O(days) und sehr schnell.
