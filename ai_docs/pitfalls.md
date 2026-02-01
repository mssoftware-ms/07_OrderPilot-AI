# ⚠️ Bekannte Pitfalls & Patterns

## 1. Race Conditions bei UI-Updates

**Problem:** Mehrere Stellen setzen dasselbe Label → Flackern, inkonsistente Werte

**Lösung:**
- EIN zentraler Signal-Handler pro UI-Element
- Alle Updates über diesen Handler routen

```python
# FALSCH (Race Condition)
self.lbl_price.setText(str(price_from_stream))
self.lbl_price.setText(str(price_from_calculation))

# RICHTIG (Zentralisiert)
self.price_updated.connect(self._on_price_update)
def _on_price_update(self, price: float):
    self.lbl_price.setText(f"${price:,.2f}")
```

## 2. Event-Loop Blocking

**Problem:** Lange Berechnungen blockieren UI

**Lösung:**
- `QThread` oder `asyncio` für langlaufende Operationen
- `QTimer.singleShot()` für verzögerte Updates

## 3. Doppelte Initialisierung

**Problem:** Widget wird zweimal erstellt

**Prüfen:**
- Suche nach mehreren `__init__` Aufrufen
- Prüfe Mixin-Reihenfolge (MRO)

## 4. Timezone-Chaos

**Problem:** Chart zeigt falsche Zeit

**Regel:**
- Intern: IMMER UTC Unix-Timestamps
- Display: Erst bei Anzeige in Lokalzeit konvertieren
- Niemals: Lokale Zeit in Berechnungen verwenden

## 5. Alpaca API Gotchas

- Paper vs Live: Unterschiedliche Base-URLs
- Rate Limits: Max 200 requests/min
- Streaming: Reconnect-Logik erforderlich
