# UI Integration Gaps - Implementierungsplan

**Erstellt:** 2026-01-01
**Status:** Audit abgeschlossen, Implementierung ausstehend

---

## Zusammenfassung

Nach intensiver Analyse wurden folgende Module identifiziert, die zwar programmiert aber **nicht oder nur teilweise an die UI angebunden** sind:

| Modul | Integration | Fehlend |
|-------|-------------|---------|
| `chart_chat/` | 30% | Main Menu, Shortcuts, Multi-Window |
| `chart_marking/lines/` | 0% | Komplette UI fehlt |
| `chart_marking/zones/` | 50% | Demand/Supply, Update, Extend |
| `chart_marking/markers/` | 80% | MSB Marker |
| `chart_marking/multi_chart/` | 70% | Delete Layouts, Monitor-Selector |

---

## Phase 1: Chart Chat - Main Menu Integration

**Priorität:** HOCH
**Aufwand:** ~2h
**Dateien:**
- `src/ui/app_components/menu_mixin.py`
- `src/ui/widgets/chart_window.py`

### 1.1 Menu Einträge hinzufügen

**In `menu_mixin.py`:**

```python
# Tools Menu erweitern
tools_menu = menubar.addMenu("&Tools")

# --- Chart Analysis Section ---
tools_menu.addSeparator()
chart_analysis_action = tools_menu.addAction("📊 Chart Analysis...")
chart_analysis_action.setShortcut("Ctrl+Shift+A")
chart_analysis_action.triggered.connect(self._on_open_chart_analysis)

toggle_chat_action = tools_menu.addAction("💬 Toggle Chat Widget")
toggle_chat_action.setShortcut("Ctrl+Shift+C")
toggle_chat_action.triggered.connect(self._on_toggle_chat_widget)
```

### 1.2 Handler implementieren

```python
def _on_open_chart_analysis(self):
    """Öffnet Chart Analysis für aktives Chart Window."""
    active_chart = self._get_active_chart_window()
    if active_chart and hasattr(active_chart, 'request_chart_analysis'):
        active_chart.show_chat_widget()
        active_chart.request_chart_analysis()

def _on_toggle_chat_widget(self):
    """Toggled Chat Widget im aktiven Chart Window."""
    active_chart = self._get_active_chart_window()
    if active_chart and hasattr(active_chart, 'toggle_chat_widget'):
        active_chart.toggle_chat_widget()
```

### 1.3 Keyboard Shortcut in ChartWindow

**In `chart_window.py`:**

```python
# In __init__, nach anderen Shortcuts:
self._chat_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
self._chat_shortcut.activated.connect(self.toggle_chat_widget)

self._analysis_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
self._analysis_shortcut.activated.connect(self.request_chart_analysis)
```

---

## Phase 2: Stop Loss Lines - Komplette UI

**Priorität:** HOCH
**Aufwand:** ~4h
**Dateien:**
- `src/ui/widgets/embedded_tradingview_chart.py`
- `src/chart_marking/mixin/chart_marking_mixin.py`

### 2.1 Context Menu erweitern

**In `_show_marking_context_menu()`:**

```python
# Lines Submenu
lines_menu = menu.addMenu("📏 Lines")

sl_action = lines_menu.addAction("🔴 Stop Loss Line")
sl_action.triggered.connect(lambda: self._add_stop_loss_at_price(price))

tp_action = lines_menu.addAction("🟢 Take Profit Line")
tp_action.triggered.connect(lambda: self._add_take_profit_at_price(price))

entry_action = lines_menu.addAction("🔵 Entry Line")
entry_action.triggered.connect(lambda: self._add_entry_at_price(price))

trailing_action = lines_menu.addAction("🟡 Trailing Stop Line")
trailing_action.triggered.connect(lambda: self._add_trailing_stop_at_price(price))

lines_menu.addSeparator()

clear_lines_action = lines_menu.addAction("Clear All Lines")
clear_lines_action.triggered.connect(self.clear_stop_loss_lines)
```

### 2.2 Handler in ChartMarkingMixin

```python
def _add_stop_loss_at_price(self, price: float):
    """Fügt Stop Loss Line bei gegebenem Preis hinzu."""
    # Für SL brauchen wir Entry Price - Dialog oder letzte Position
    entry_price = getattr(self, '_last_entry_price', price * 1.02)  # Default 2% drüber
    is_long = price < entry_price  # SL unter Entry = Long

    line_id = f"sl_{int(time.time()*1000)}"
    self.add_stop_loss_line(
        line_id=line_id,
        price=price,
        entry_price=entry_price,
        is_long=is_long,
        label=f"SL @ {price:.2f}",
        show_risk=True
    )

def _add_take_profit_at_price(self, price: float):
    """Fügt Take Profit Line bei gegebenem Preis hinzu."""
    entry_price = getattr(self, '_last_entry_price', price * 0.98)
    is_long = price > entry_price

    line_id = f"tp_{int(time.time()*1000)}"
    self.add_take_profit_line(
        line_id=line_id,
        price=price,
        entry_price=entry_price,
        is_long=is_long,
        label=f"TP @ {price:.2f}"
    )
```

### 2.3 Entry Price Dialog (optional)

Für präzise SL/TP Berechnung einen kleinen Dialog:

```python
class EntryPriceDialog(QDialog):
    """Dialog zur Eingabe des Entry-Preises für SL/TP Berechnung."""

    def __init__(self, current_price: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Entry Price")
        # ... Input Field, OK/Cancel
```

---

## Phase 3: Demand/Supply Zones

**Priorität:** MITTEL
**Aufwand:** ~1h
**Dateien:**
- `src/ui/widgets/embedded_tradingview_chart.py`

### 3.1 Context Menu erweitern

```python
# In zones_menu (bereits existierend):
zones_menu.addSeparator()

demand_action = zones_menu.addAction("🟢 Demand Zone (Bullish)")
demand_action.triggered.connect(lambda: self._add_demand_zone_interactive())

supply_action = zones_menu.addAction("🔴 Supply Zone (Bearish)")
supply_action.triggered.connect(lambda: self._add_supply_zone_interactive())
```

### 3.2 Handler

```python
def _add_demand_zone_interactive(self):
    """Fügt Demand Zone an aktueller Position hinzu."""
    # Ähnlich wie add_support_zone, aber mit demand_zone API
    price = self._get_clicked_price()
    zone_height = price * 0.005  # 0.5% Zone height

    self.add_demand_zone(
        start_time=self._get_visible_start_time(),
        end_time=self._get_visible_end_time(),
        top_price=price,
        bottom_price=price - zone_height,
        label="Demand"
    )
```

---

## Phase 4: MSB Marker

**Priorität:** NIEDRIG
**Aufwand:** ~30min
**Dateien:**
- `src/ui/widgets/embedded_tradingview_chart.py`

### 4.1 Context Menu erweitern

```python
# In structure_menu (bereits existierend):
structure_menu.addSeparator()

msb_bull_action = structure_menu.addAction("⬆️ MSB Bullish")
msb_bull_action.triggered.connect(lambda: self._add_msb_at_price(price, True))

msb_bear_action = structure_menu.addAction("⬇️ MSB Bearish")
msb_bear_action.triggered.connect(lambda: self._add_msb_at_price(price, False))
```

---

## Phase 5: Zone Management (Update/Extend)

**Priorität:** NIEDRIG
**Aufwand:** ~3h (komplexer)
**Dateien:**
- `src/ui/widgets/embedded_tradingview_chart.py`
- `src/chart_marking/mixin/chart_marking_mixin.py`

### 5.1 Zone Selection System

Benötigt JavaScript-Integration für:
- Zone Hover Detection
- Zone Click Selection
- Selected Zone Highlight

### 5.2 Context Menu für ausgewählte Zone

```python
def _show_zone_context_menu(self, zone_id: str, pos: QPoint):
    """Zeigt Context Menu für eine ausgewählte Zone."""
    menu = QMenu(self)

    extend_action = menu.addAction("Extend Zone")
    extend_action.triggered.connect(lambda: self._extend_zone_dialog(zone_id))

    edit_action = menu.addAction("Edit Zone...")
    edit_action.triggered.connect(lambda: self._edit_zone_dialog(zone_id))

    delete_action = menu.addAction("Delete Zone")
    delete_action.triggered.connect(lambda: self.remove_zone(zone_id))

    menu.exec(pos)
```

**Hinweis:** Diese Phase erfordert erweiterte JavaScript-Integration und ist komplexer.

---

## Phase 6: Layout Management Dialog

**Priorität:** MITTEL
**Aufwand:** ~2h
**Dateien:**
- Neue Datei: `src/ui/dialogs/layout_manager_dialog.py`
- `src/ui/app_components/menu_mixin.py`

### 6.1 Layout Manager Dialog

```python
class LayoutManagerDialog(QDialog):
    """Dialog zur Verwaltung gespeicherter Chart-Layouts."""

    def __init__(self, layout_manager: LayoutManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Layout Manager")
        self.layout_manager = layout_manager

        # Layout
        layout = QVBoxLayout(self)

        # Liste der Layouts
        self.layout_list = QListWidget()
        self._populate_layouts()
        layout.addWidget(self.layout_list)

        # Buttons
        btn_layout = QHBoxLayout()

        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self._on_apply)
        btn_layout.addWidget(self.apply_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(self.delete_btn)

        self.rename_btn = QPushButton("Rename...")
        self.rename_btn.clicked.connect(self._on_rename)
        btn_layout.addWidget(self.rename_btn)

        layout.addLayout(btn_layout)
```

### 6.2 Menu Eintrag

```python
# In Charts > Layouts Submenu:
layouts_menu.addSeparator()
manage_layouts_action = layouts_menu.addAction("Manage Layouts...")
manage_layouts_action.triggered.connect(self._on_manage_layouts)
```

---

## Implementierungs-Reihenfolge

| Phase | Beschreibung | Priorität | Status |
|-------|--------------|-----------|--------|
| **1** | Chart Chat Menu Integration | HOCH | ✅ Abgeschlossen |
| **2** | Stop Loss Lines UI | HOCH | ✅ Abgeschlossen |
| **3** | Demand/Supply Zones | MITTEL | ✅ Abgeschlossen |
| **4** | MSB Marker | NIEDRIG | ✅ Abgeschlossen |
| **5** | Zone Management | NIEDRIG | ✅ Abgeschlossen |
| **6** | Layout Manager Dialog | MITTEL | ✅ Abgeschlossen |

---

## Zusammenfassung der Änderungen

### Dateien zu modifizieren:

1. **`src/ui/app_components/menu_mixin.py`**
   - Tools Menu: Chart Analysis, Toggle Chat Widget
   - Charts > Layouts: Manage Layouts...

2. **`src/ui/widgets/chart_window.py`**
   - Keyboard Shortcuts für Chat (Ctrl+Shift+C, Ctrl+Shift+A)

3. **`src/ui/widgets/embedded_tradingview_chart.py`**
   - Context Menu erweitern:
     - Lines Submenu (SL, TP, Entry, Trailing)
     - Zones: Demand, Supply
     - Structure: MSB Bullish/Bearish

4. **`src/chart_marking/mixin/chart_marking_mixin.py`**
   - Handler für neue Context Menu Actions
   - Entry Price Tracking

### Neue Dateien:

5. **`src/ui/dialogs/layout_manager_dialog.py`** (NEU)
   - LayoutManagerDialog Klasse

---

## Verifikation

Nach Implementierung prüfen:

```bash
# Syntax Check
python3 -m py_compile src/ui/app_components/menu_mixin.py
python3 -m py_compile src/ui/widgets/chart_window.py
python3 -m py_compile src/ui/widgets/embedded_tradingview_chart.py

# App starten und manuell testen:
# 1. Chart öffnen (Doppelklick auf Symbol)
# 2. Rechtsklick auf Chart → alle Menüs prüfen
# 3. Tools → Chart Analysis → Chat Widget erscheint
# 4. Ctrl+Shift+C → Chat Widget toggled
# 5. Charts → Layouts → Manage Layouts... → Dialog öffnet
```

---

## Risiken

1. **JavaScript Integration für Zone Selection** - Phase 5 erfordert erweiterte JS-Kommunikation
2. **Entry Price Tracking** - Benötigt möglicherweise Position-Kontext vom Broker
3. **Multi-Window Chat** - Chat History Sync zwischen Windows

---

## Nächste Schritte

1. ✅ Audit abgeschlossen
2. ✅ Phase 1 implementiert (Chart Chat Menu)
3. ✅ Phase 2 implementiert (Stop Loss Lines)
4. ✅ Phase 3 implementiert (Demand/Supply Zones)
5. ✅ Phase 4 implementiert (MSB Marker)
6. ✅ Phase 5 implementiert (Zone Management - Edit/Delete/Extend)
7. ✅ Phase 6 implementiert (Layout Manager Dialog)

**Alle Phasen abgeschlossen am 2026-01-01**
