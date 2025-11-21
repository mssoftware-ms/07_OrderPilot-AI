# Chart Bugfix - Finale Lösung

## Datum: 2025-11-20

## Probleme behoben:

### 1. ✅ Chart-Initialisierung funktioniert wieder
**Problem**: JavaScript-Code wurde nicht ausgeführt, `window.chartAPI` war undefined

**Lösung**:
- Geändert von `DOMContentLoaded` Event zu `setTimeout(50ms)`
- `QWebEngineView.setHtml()` feuert keine DOM-Events
- Altes Volume-Chart-Code entfernt (Zeilen 177-218)

**Geänderte Datei**: `src/ui/widgets/embedded_tradingview_chart.py` (Zeile 598-603)

---

### 2. ✅ EventType Fehler behoben
**Probleme**:
- `type object 'EventType' has no attribute 'MARKET_DATA_CONNECTED'`
- `type object 'EventType' has no attribute 'MARKET_DATA_DISCONNECTED'`
- `type object 'EventType' has no attribute 'INDICATOR_CALCULATED'`

**Lösung**: Fehlende EventTypes hinzugefügt

**Geänderte Datei**: `src/common/event_bus.py`
```python
# Market Data Events
MARKET_DATA_CONNECTED = "market_data_connected"
MARKET_DATA_DISCONNECTED = "market_data_disconnected"

# Indicator Events
INDICATOR_CALCULATED = "indicator_calculated"
```

---

### 3. ✅ Alpaca Stream Fehler behoben
**Problem**: `'str' object has no attribute 'value'`

**Lösung**: `get_metrics()` prüft nun, ob `status` ein Enum oder String ist

**Geänderte Datei**: `src/core/market_data/alpaca_stream.py` (Zeile 371)
```python
status_value = self.metrics.status.value if hasattr(self.metrics.status, 'value') else self.metrics.status
```

---

### 4. ✅ Panel-Größen-Problem behoben
**Problem**: Neu erstellte Panels hatten `clientWidth` = 0

**Lösung**: Fallback auf Container-Breite und Mindesthöhe

**Geänderte Datei**: `src/ui/widgets/embedded_tradingview_chart.py`
- Price Chart: Zeile 137-139 (Fallback: 800x400)
- Indicator Panels: Zeile 366-367 (Fallback: Container-Breite, min 150px Höhe)

---

## Was jetzt funktioniert:

✅ Chart wird angezeigt
✅ `window.chartAPI` ist verfügbar
✅ Volume wird in separatem Panel angezeigt (dynamisch erstellt)
✅ Indikatoren (SMA, EMA, RSI) sollten jetzt funktionieren
✅ Live-Stream sollte sich verbinden können
✅ Panels haben korrekte Größen

---

## Bekannte Probleme, die noch bestehen könnten:

⚠️ **Zoom beim Verschieben**: Der User berichtet, dass beim Verschieben mit der linken Maustaste immer noch gezoomt wird. Dies erfordert weitere Untersuchung der TradingView Lightweight Charts Einstellungen.

**Aktuelle Einstellungen**:
```javascript
handleScroll: {
    pressedMouseMove: true,  // Pan mit Maus
},
handleScale: {
    axisPressedMouseMove: false,  // Kein Zoom auf Achse
    mouseWheel: true,  // Zoom mit Mausrad
}
```

**Mögliche Lösung**: `axisPressedMouseMove` wird möglicherweise nicht für den gesamten Chart angewendet, sondern nur für die Achsen. Evtl. müssen wir weitere Scale-Optionen deaktivieren.

---

## Nächste Schritte:

1. **Testen Sie die App**: Starten Sie OrderPilot-AI und wählen Sie ein Symbol
2. **Prüfen Sie Volume**: Das Volume-Panel sollte automatisch unter dem Price-Chart erscheinen
3. **Testen Sie Indikatoren**: Aktivieren Sie SMA, EMA, RSI - sie sollten ohne Fehler geladen werden
4. **Prüfen Sie Live-Stream**: Der Live-Button sollte sich verbinden (wenn Markt offen)

5. **Zoom-Problem**: Falls das Zoom-Problem weiterhin besteht, lassen Sie es mich wissen, dann schauen wir uns die Chart-Optionen genauer an.

---

## Technische Details:

### Chart-Container Struktur:
```html
<div id="chart-container">
    <div id="price-chart"></div>        <!-- flex: 3 (60% Platz) -->
    <div id="panel-volume"></div>       <!-- flex: 1 (dynamisch) -->
    <div id="panel-rsi"></div>          <!-- flex: 1 (dynamisch) -->
    <!-- Weitere Panels werden dynamisch hinzugefügt -->
</div>
```

### JavaScript API:
```javascript
window.chartAPI.createPanel(panelId, name, type, color, min, max);
window.chartAPI.setPanelData(panelId, data);
window.chartAPI.removePanel(panelId);
```

---

## Zusammenfassung:

Die Haupt-Probleme wurden behoben:
1. ✅ Chart-Initialisierung
2. ✅ EventType-Fehler
3. ✅ Alpaca Stream
4. ✅ Panel-Größen
5. ⚠️ Zoom-Verhalten (benötigt weitere Untersuchung)

Der Chart sollte jetzt funktionieren und Volume + Indikatoren in separaten Panels anzeigen!
