# UI Layout Change - Bitunix Execution & Current Position

**Datum**: 2026-01-13
**Status**: ✅ IMPLEMENTIERT
**Betroffene Dateien**: 2

---

## Änderungs-Übersicht

Die Bitunix Execution GroupBox und Current Position GroupBox werden jetzt **horizontal nebeneinander** angezeigt statt vertikal gestapelt.

### Vorher (Vertikal):
```
┌─────────────────────────────────────┐
│  Bitunix Execution (HEDGE)          │
│  [gesamte Breite]                   │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│  Current Position                   │
│  [gesamte Breite]                   │
└─────────────────────────────────────┘
```

### Nachher (Horizontal):
```
┌────────────────────────────┬─────────────────┐
│  Bitunix Execution (HEDGE) │ Current Position│
│  [nimmt Rest der Breite]   │    [420px]      │
└────────────────────────────┴─────────────────┘
```

---

## Technische Details

### Layout-Struktur

**Datei**: `src/ui/widgets/chart_window_mixins/bot_ui_signals_mixin.py`

**Methode**: `_create_signals_tab()` (Zeilen 131-162)

```python
# Top row: Horizontal Layout
top_row_layout = QHBoxLayout()
top_row_layout.setSpacing(8)

# Bitunix HEDGE Execution Panel - takes remaining space
bitunix_widget = self._build_bitunix_hedge_execution_widget()
top_row_layout.addWidget(bitunix_widget, stretch=1)  # stretch=1 → nimmt Rest

# Current Position - fixed 420px width
position_widget = self._build_current_position_widget()
position_widget.setMaximumWidth(420)
position_widget.setMinimumWidth(420)
top_row_layout.addWidget(position_widget, stretch=0)  # stretch=0 → fixiert
```

### Widget-Dimensionen

#### Bitunix Execution Widget

**Datei**: `src/ui/widgets/bitunix_hedge_execution_widget.py`

**Gesamt-Widget:**
- **Höhe**: 220px (maximal, identisch mit Current Position)
- **Breite**: Flexibel, nimmt verbleibenden Platz (stretch=1)

**Spalten-Breiten:**
| Spalte | Breite | Inhalt |
|:-------|-------:|:-------|
| Connection & Risk | 200px | Status, Symbol, Leverage, Qty |
| Entry | 260px | Direction, Mode, Type, Price, Offset, Actions |
| TP/SL & Trailing | 240px | TP, SL, Trailing, Exchange SL, Exit |
| **Gesamt** | **700px** | + ~24px Spacing = **724px** |

**Footer:**
- Höhe: ~30px
- Breite: Volle Widget-Breite
- Inhalt: State, Order ID, Position ID, Kill Switch

#### Current Position Widget

**Dimensionen:**
- **Breite**: 420px (fixiert)
- **Höhe**: 220px (maximal)

**Inhalt:**
- SL/TP Progress Bar
- Position Details (2 Spalten)
  - Links: Side, Strategy, Entry, Size, Stop, Current, P&L, Bars
  - Rechts: Score, TR Price, Derivat-Details

---

## Schriftgrößen

### Synchronisierung

Beide Widgets verwenden **identische Schriftgrößen**:
- **GroupBox-Titel**: Standard Qt-Schriftgröße (automatisch)
- **Labels & Controls**: Standard Qt-Schriftgröße (automatisch)
- **Hinweis-Texte**: 9pt (Limits, Exchange SL)

**Keine expliziten Font-Anpassungen nötig**, da beide Widgets von `QGroupBox` erben und die Standard-Qt-Schriftgröße verwenden.

---

## Vorher/Nachher Vergleich

### Vorher

**Vertikale Anordnung:**
- Bitunix Widget: 100% Breite, ~250px Höhe
- Current Position: 100% Breite, 220px Höhe
- **Gesamthöhe**: ~470px

**Probleme:**
- Viel vertikaler Platz verbraucht
- Weniger Platz für Recent Signals
- Horizontaler Platz nicht optimal genutzt

### Nachher

**Horizontale Anordnung:**
- Bitunix Widget: ~60-70% Breite (mindestens 724px), 220px Höhe
- Current Position: 420px Breite, 220px Höhe
- **Gesamthöhe**: 220px (+ Footer ~30px)

**Vorteile:**
- ✅ 50% weniger vertikaler Platz
- ✅ Mehr Platz für Recent Signals Tabelle
- ✅ Effizientere horizontale Platznutzung
- ✅ Beide Widgets auf gleicher Höhe (220px)
- ✅ Identische Schriftgrößen

---

## Responsive Verhalten

### Mindest-Fensterbreite

**Empfohlene Mindestbreite**: 1200px

**Berechnung:**
- Bitunix Widget Spalten: 724px
- Current Position: 420px
- Spacing: 8px
- Margins: ~8px (links + rechts)
- **Gesamt**: ~1160px

**Bei kleineren Fenstergrößen:**
- Bitunix Widget komprimiert sich auf Mindestbreite (724px)
- Horizontales Scrolling erscheint
- Alternative: Responsive Breakpoint bei <1200px → vertikale Anordnung

### Stretch-Verhalten

**stretch=1 für Bitunix Widget:**
```python
top_row_layout.addWidget(bitunix_widget, stretch=1)
```

- Bei Fensterbreite >1160px: Bitunix Widget expandiert
- Bei Fensterbreite =1160px: Beide Widgets auf Mindestbreite
- Bei Fensterbreite <1160px: Horizontal scrolling

**stretch=0 für Current Position:**
```python
top_row_layout.addWidget(position_widget, stretch=0)
```

- Immer fixiert auf 420px
- Expandiert NICHT bei größeren Fenstern

---

## Code-Änderungen

### Datei 1: `src/ui/widgets/chart_window_mixins/bot_ui_signals_mixin.py`

**Methode**: `_create_signals_tab()` (Zeilen 131-162)

**Geändert:**
```python
# NEU: Horizontal Layout für Top Row
top_row_layout = QHBoxLayout()
top_row_layout.setSpacing(8)

# Bitunix Widget (stretch=1)
bitunix_widget = self._build_bitunix_hedge_execution_widget()
top_row_layout.addWidget(bitunix_widget, stretch=1)

# Current Position Widget (stretch=0, fixiert 420px)
position_widget = self._build_current_position_widget()
position_widget.setMaximumWidth(420)
position_widget.setMinimumWidth(420)
top_row_layout.addWidget(position_widget, stretch=0)

layout.addLayout(top_row_layout)
```

**Vorher:**
```python
# ALT: Vertikal gestapelt
layout.addWidget(self._build_bitunix_hedge_execution_widget())
layout.addWidget(self._build_current_position_widget())
```

### Datei 2: `src/ui/widgets/bitunix_hedge_execution_widget.py`

**Änderung 1**: Höhe angepasst (Zeile 55)
```python
# Match height with Current Position GroupBox
self.setMaximumHeight(220)
```

**Änderung 2**: Spaltenbreiten optimiert

| Spalte | Vorher | Nachher |
|:-------|-------:|--------:|
| Connection & Risk | 220px | 200px |
| Entry | 280px | 260px |
| TP/SL & Trailing | 260px | 240px |
| **Gesamt** | **760px** | **700px** |

**Code:**
```python
# Connection & Risk (Zeile 145)
widget.setMaximumWidth(200)  # vorher: 220

# Entry (Zeile 226)
widget.setMaximumWidth(260)  # vorher: 280

# TP/SL & Trailing (Zeile 279)
widget.setMaximumWidth(240)  # vorher: 260
```

---

## Testing

### Manuelle Tests

#### Test 1: Layout & Dimensionen
- [ ] Anwendung starten
- [ ] Trading Bot Tab öffnen
- [ ] Bitunix Widget links sichtbar
- [ ] Current Position rechts sichtbar (420px breit)
- [ ] Beide Widgets auf gleicher Höhe (220px)
- [ ] 8px Abstand zwischen Widgets

#### Test 2: Responsive Verhalten
- [ ] Fenster auf 1600px Breite
  - Bitunix Widget expandiert
  - Current Position bleibt 420px
- [ ] Fenster auf 1200px Breite
  - Beide Widgets sichtbar
  - Bitunix Widget komprimiert
- [ ] Fenster auf 1000px Breite
  - Horizontal Scrolling erscheint

#### Test 3: Schriftgröße
- [ ] Bitunix Widget Titel-Schriftgröße
- [ ] Current Position Titel-Schriftgröße
- [ ] Beide identisch (visueller Vergleich)
- [ ] Labels und Controls identische Größe

#### Test 4: Funktionalität
- [ ] Bitunix Widget Controls funktionieren
- [ ] Current Position Updates funktionieren
- [ ] Keine Layout-Fehler im Log
- [ ] Keine Qt-Warnings

---

## Visuelle Darstellung

### Layout-Hierarchie

```
QVBoxLayout (Signals Tab)
├─ QHBoxLayout (Top Row)
│  ├─ Bitunix Execution Widget (stretch=1)
│  │  ├─ QVBoxLayout
│  │  │  ├─ QHBoxLayout (3 Spalten)
│  │  │  │  ├─ Connection & Risk (200px)
│  │  │  │  ├─ Entry (260px)
│  │  │  │  └─ TP/SL & Trailing (240px)
│  │  │  └─ Status Footer
│  └─ Current Position Widget (420px, stretch=0)
│     └─ QVBoxLayout
│        ├─ SL/TP Progress Bar
│        └─ Position Details (2 Spalten)
├─ QSpacing (20px)
├─ Recent Signals Widget (stretch=1)
└─ Trading Bot Log Widget
```

---

## Zusammenfassung

### Was wurde geändert?

1. ✅ Layout von vertikal auf horizontal geändert
2. ✅ Current Position auf 420px Breite fixiert
3. ✅ Bitunix Widget nimmt verbleibenden Platz (stretch=1)
4. ✅ Beide Widgets auf gleiche Höhe (220px) angepasst
5. ✅ Spaltenbreiten optimiert (724px statt 760px)
6. ✅ Schriftgrößen automatisch synchronisiert

### Vorteile

- **Platzsparend**: 50% weniger vertikaler Platz
- **Effizienter**: Bessere horizontale Platznutzung
- **Konsistent**: Gleiche Höhe und Schriftgrößen
- **Responsive**: Bitunix Widget expandiert bei mehr Platz

### Nächste Schritte

1. Anwendung neu starten
2. Manuelle Tests durchführen
3. Bei Bedarf Spaltenbreiten feintunen
4. Responsive Breakpoints implementieren (optional)

---

**Status**: ✅ IMPLEMENTIERT
**Version**: 1.0.0
**Autor**: Claude Code
**Datum**: 2026-01-13
