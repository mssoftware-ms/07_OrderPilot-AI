# Bitunix Trading API Widget - Layout Update

## Datum: 2026-01-16

## Übersicht
Komplette Neustrukturierung des Bitunix Trading API Widgets im Signals Tab des Trading Bot Fensters basierend auf dem Referenz-Mockup (`.AI_Exchange/image.png`).

## Neue 3-Spalten-Struktur

### Linke Spalte (Control Inputs)
- **Symbol ComboBox**: 180px Breite
  - BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT
- **Direction Buttons**: Long (87px) / Short (87px)
  - Long: türkis (#26a69a) wenn ausgewählt
  - Short: dunkelgrau (#3a3a3a) wenn ausgewählt
- **Order Type Buttons**: Market (87px) / Limit (87px)
  - Market: grün (#4CAF50) wenn ausgewählt
  - Limit: dunkelgrau (#3a3a3a) wenn ausgewählt
- **Limit Price**: 180px Breite (nur sichtbar bei Limit Order)

### Mittlere Spalte (Quantity & Price Info)
- **Stückzahl (Quantity)**: 150px Breite
  - Range: 0.001 - 10,000
  - 3 Dezimalstellen
  - Suffix: " BTC" (dynamisch je nach Symbol)
- **Volumen**: 150px Breite
  - Range: 1.0 - 1,000,000 USDT
  - 2 Dezimalstellen
  - Suffix: " USDT"
- **Leverage**: 150px Breite
  - Range: 1x - 125x
  - Suffix: "x"
  - Synchronisiert mit Slider
- **Last Price**: Dynamische Anzeige
  - Anzeige: "—" wenn kein Preis verfügbar
  - Format: "123.45 USDT"

### Rechte Spalte (Trading Controls)
- **BUY Button**: 80px × 32px
  - Farbe: dunkelgrau (#3a3a3a)
  - Hover: hellgrau (#4a4a4a)
- **SELL Button**: 80px × 32px
  - Farbe: dunkelgrau (#3a3a3a)
  - Hover: hellgrau (#4a4a4a)
- **Paper Trading Button**: volle Breite × 32px
  - Paper Mode: türkis (#26a69a)
  - Live Mode: rot (#ef5350)
- **Leverage Slider**: horizontal
  - Range: 10 - 200
  - Schritte: 10
  - Handle: orange (#ffa726)
  - Sub-page: orange (#ffa726)
- **Preset Buttons**: 2 Reihen × 10 Spalten
  - Werte: 10, 20, 30, ..., 190
  - Größe: 22px × 16px
  - Farbe: dunkelgrau (#3a3a3a)
  - Font: 8px

## Layout-Parameter

### Abstände
- Hauptlayout Margins: 8, 12, 8, 8
- Hauptlayout Spacing: 6px
- Horizontaler Spaltenabstand: 12px
- Grid Horizontal Spacing: 8px
- Grid Vertical Spacing: 6px
- Preset Button Spacing: 3px (horizontal & vertikal)

### Widget-Größen
- Gruppenhöhe (maximal): 230px
- Gruppenbreite (minimal): 700px
- Symbol ComboBox: 180px
- Direction/Order Type Buttons: 87px × 26px
- Quantity/Volume/Leverage SpinBoxes: 150px
- BUY/SELL Buttons: 80px × 32px
- Paper Trading Button: volle Breite × 32px
- Leverage Slider: 16px Handle
- Preset Buttons: 22px × 16px

## Entfernte Features
- ❌ "Last" Button für Limit Price (automatische Synchronisation)
- ❌ "Adapter:" Label (nur Status-Text)
- ❌ Exposure Label (ersetzt durch Slider-Wert)
- ❌ `_sync_order_type_button_widths()` Methode

## Neue Features
- ✅ Kompaktes 3-Spalten-Layout
- ✅ Preset-Buttons für schnelle Leverage-Auswahl (10-190)
- ✅ Visueller Orange-Indikator am Leverage-Slider
- ✅ Automatische Synchronisation Slider ↔ SpinBox
- ✅ Dynamischer Adapter-Status unten rechts (klein, 9px Font)

## Status-Anzeige (unten rechts)
- **disconnected**: grau (#888)
- **connecting/disconnecting**: orange (#ffa726)
- **missing/error**: rot (#f44336)
- Font-Größe: 9px

## Farbschema
- Background: dunkel (#1a1a2e, #2a2a2a, #3a3a3a)
- Primary Action: türkis (#26a69a)
- Danger: rot (#ef5350)
- Warning: orange (#ffa726, #ff9800)
- Success: grün (#4CAF50)
- Disabled: grau (#444, #666, #888)

## Verhaltensänderungen

### Order Type Wechsel
- Market → Limit: Limit Price Feld wird eingeblendet
- Limit → Market: Limit Price Feld wird ausgeblendet

### Leverage-Steuerung
- SpinBox-Änderung → Slider wird synchronisiert
- Slider-Änderung → SpinBox wird synchronisiert
- Preset-Button → Beide werden auf Wert gesetzt

### Quantity ↔ Volume
- Quantity-Änderung → Volume wird berechnet (Qty × Price)
- Volume-Änderung → Quantity wird berechnet (Vol / Price)
- Preis-Quelle: Limit Price (wenn Limit Order) oder Last Price

## Implementierte Methoden

### Neue Methoden
```python
_build_left_column() -> QWidget
_build_middle_column() -> QWidget
_build_right_column() -> QWidget
_on_leverage_changed_spinbox(value: int)
_on_preset_clicked(value: int)
```

### Geänderte Methoden
```python
_setup_ui()  # Komplett neu strukturiert
_on_order_type_changed()  # Label-Visibility hinzugefügt
_connect_adapter_for_live_mode()  # Status-Updates angepasst
_disconnect_adapter_for_paper_mode()  # Status-Updates angepasst
```

### Entfernte Methoden
```python
_sync_order_type_button_widths()  # Feste Breiten
_on_use_last_price()  # Button entfernt
```

## Dateien
- **Hauptdatei**: `src/ui/widgets/bitunix_trading_api_widget.py`
- **Integration**: `src/ui/widgets/chart_window_mixins/bot_ui_signals_widgets_mixin.py`
- **Referenz-Mockup**: `.AI_Exchange/image.png`

## Testing Checklist
- [ ] Widget wird korrekt im Signals Tab angezeigt
- [ ] Spaltenbreiten entsprechen Mockup
- [ ] Direction Buttons (Long/Short) funktionieren
- [ ] Order Type Buttons (Market/Limit) funktionieren
- [ ] Limit Price erscheint nur bei Limit Order
- [ ] Quantity ↔ Volume Synchronisation funktioniert
- [ ] Leverage SpinBox ↔ Slider Synchronisation funktioniert
- [ ] Preset-Buttons setzen Leverage korrekt
- [ ] BUY/SELL Buttons sind disabled ohne Adapter
- [ ] Paper Trading Button wechselt Mode korrekt
- [ ] Adapter-Status wird unten rechts angezeigt
- [ ] Responsive Layout bei verschiedenen Fenstergrößen

## Bekannte Einschränkungen
- Limit Price hat keinen "Last" Button mehr (automatische Synchronisation)
- Minimale Gruppenbreite: 700px (nicht für sehr schmale Fenster geeignet)
- Preset-Buttons sind klein (22×16px) - für Touch-Screens ggf. zu klein

## Nächste Schritte
1. Integration in Chart Window testen
2. Adapter-Verbindung testen (Live & Paper)
3. Order-Platzierung testen
4. Responsive Behavior bei Fenstergrößenänderung testen
5. Benutzer-Feedback einholen
