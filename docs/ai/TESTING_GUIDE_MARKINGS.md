# Test-Guide: Bidirektionale Chart-Markierungen

## Schnelltest in der Anwendung

### Vorbereitung

1. **API-Key prüfen**
   ```bash
   # In .env oder Umgebung:
   echo $OPENAI_API_KEY
   # oder
   echo $ANTHROPIC_API_KEY
   # oder
   echo $GEMINI_API_KEY
   ```

   ⚠️ Mindestens einer muss gesetzt sein!

2. **Anwendung starten**
   ```bash
   python start_orderpilot.py
   ```

### Test 1: Einfache Markierung (Stop Loss)

1. Öffne einen Chart (z.B. BTC/USD, 1D)
2. Klicke auf Chat-Icon
3. Gib ein: **"Wo sollte mein Stop Loss liegen?"**
4. Erwarte:
   - KI antwortet mit `[#Stop Loss; PREIS]`
   - Kurze Begründung (2-3 Stichpunkte)
   - Rote horizontale Linie erscheint im Chart

**Erwartete Antwort-Struktur:**
```
[#Stop Loss; 87654.32]

- Support bei 87.6k ist kritischer Level
- RSI zeigt Überverkauft bei diesem Niveau

Stop auf 87654.32 angepasst.
```

### Test 2: Mehrere Markierungen

1. Selber Chart
2. Gib ein: **"Aktualisiere alle Levels"**
3. Erwarte:
   - Mehrere Variablen: `[#Stop Loss; ...]`, `[#Take Profit; ...]`, `[#Support Zone; ...-...]`
   - Stichpunkte zur Begründung
   - Mehrere Linien/Zonen im Chart

**Erwartete Antwort-Struktur:**
```
[#Stop Loss; 87000.00]
[#Take Profit; 92000.00]
[#Support Zone; 85000-86000]
[#Resistance Zone; 91000-92500]

- Trend weiterhin bullish
- Support bei 85-86k hält
- Resistance bei 91-92.5k

Levels aktualisiert.
```

### Test 3: Komplettes Setup

1. Gib ein: **"Gib mir ein Long-Setup für BTC"**
2. Erwarte:
   - Entry Long
   - Stop Loss
   - Take Profit
   - Support/Resistance Zonen
   - R/R-Ratio in Begründung

### Test 4: Follow-up Frage

1. Nach Test 2 oder 3, stelle Follow-up: **"Ist der Stop noch aktuell?"**
2. Erwarte:
   - KI sieht bestehende Markierungen im Prompt
   - Aktualisiert oder bestätigt Stop Loss
   - Kurze Antwort

---

## Log-Monitoring

Während du testest, beobachte die Logs:

```bash
tail -f logs/orderpilot.log | grep -E "Compact Question|Chart markings updated|Applying.*marking"
```

**Erwartete Log-Ausgaben:**

```
💬 Compact Question: 'Wo sollte mein Stop Loss liegen?' | BTC/USD 1D @ 88063.56 | Markings: 0
Applying 1 marking updates to chart
Chart markings updated successfully
```

Nach zweiter Frage:
```
💬 Compact Question: 'Ist der Stop noch aktuell?' | BTC/USD 1D @ 88100.00 | Markings: 3
```

---

## Fehlersuche

### Problem: "AI Service nicht verfügbar"

**Ursache:** Kein API-Key konfiguriert

**Lösung:**
```bash
# Setze einen API-Key in .env oder Umgebung
export OPENAI_API_KEY="sk-..."
# oder
export ANTHROPIC_API_KEY="sk-ant-..."
# oder
export GEMINI_API_KEY="..."
```

### Problem: Warteanimation läuft dauerhaft

**Ursache:** Netzwerkfehler oder API-Fehler

**Lösung:**
1. Prüfe Logs: `tail -100 logs/orderpilot.log`
2. Suche nach Fehlern: `grep ERROR logs/orderpilot.log`
3. Prüfe Netzwerkverbindung
4. Prüfe API-Key Gültigkeit

### Problem: Keine Markierungen im Chart sichtbar

**Ursache:** Chart-Widget hat benötigte Methoden nicht

**Lösung:**
1. Prüfe Logs nach "Chart markings updated"
2. Prüfe ob Chart-Widget diese Methoden hat:
   - `add_long_entry()`
   - `add_short_entry()`
   - `add_support_zone()`
   - `add_resistance_zone()`

### Problem: Variablen werden nicht erkannt

**Ursache:** Format nicht korrekt

**Debug:**
```bash
# Prüfe AI-Antwort im Log
grep "answer.*\[#" logs/orderpilot.log
```

**Korrekte Formate:**
- ✅ `[#Stop Loss; 87654.32]`
- ✅ `[#Support Zone; 85000-86000]`
- ❌ `[Stop Loss: 87654.32]` (falsches Trennzeichen)
- ❌ `[#StopLoss;87654.32]` (fehlendes Leerzeichen nach ;)

---

## Test-Checkliste

- [ ] API-Key ist konfiguriert
- [ ] Anwendung startet ohne Fehler
- [ ] Chart öffnet sich
- [ ] Chat-Widget öffnet sich
- [ ] Erste Frage funktioniert (Stop Loss)
- [ ] Markierung erscheint im Chart
- [ ] Zweite Frage funktioniert (bestehende Markierungen sichtbar)
- [ ] Mehrere Markierungen funktionieren
- [ ] Logs zeigen "Compact Question" und "Chart markings updated"
- [ ] Keine Fehler in den Logs

---

## Erweiterte Tests

### Test 5: Chart-Wechsel

1. Erstelle Markierungen in BTC/USD 1D
2. Wechsle Chart zu ETH/USD 1H
3. Stelle Frage → sollte KEINE BTC-Markierungen sehen
4. Wechsle zurück zu BTC/USD 1D
5. Markierungen sollten noch da sein

### Test 6: Vollanalyse mit Markierungen

1. Klicke "📊 Vollanalyse" Button
2. Erwarte:
   - Support/Resistance Levels als Zonen
   - Stop Loss aus Risk Assessment
   - Take Profit aus Risk Assessment
   - Alle im Chart eingezeichnet

### Test 7: Stress-Test

1. Stelle 5 Fragen hintereinander
2. Prüfe ob Event-Loop stabil bleibt
3. Logs sollten keine "Event loop is closed" Fehler zeigen

---

## Performance-Check

Typische Antwortzeiten:
- Einfache Frage (Stop Loss): 2-5 Sekunden
- Komplettes Setup: 3-8 Sekunden
- Vollanalyse: 5-12 Sekunden

Falls länger:
- Prüfe API-Geschwindigkeit
- Prüfe Netzwerklatenz
- Prüfe ob `timeout=30.0` ausreicht

---

## Erfolgs-Kriterien

✅ **System funktioniert wenn:**

1. KI antwortet auf Fragen
2. Antworten enthalten Variablen-Format `[#Label; Wert]`
3. Antworten sind kurz und stichpunktartig (nicht lange Fließtexte)
4. Markierungen erscheinen automatisch im Chart
5. Bei Follow-up sieht KI bestehende Markierungen
6. Keine Event-Loop-Fehler
7. Logs zeigen erfolgreiche Updates

---

## Support

Bei Problemen:
1. Sammle Logs: `logs/orderpilot.log`
2. Notiere exakte Fehlermeldung
3. Notiere welche Frage gestellt wurde
4. Screenshot vom Chat-Widget
5. Screenshot vom Chart (ob Markierungen sichtbar)

**Test-Ablauf dokumentieren:**
- Was wurde gefragt?
- Was war die Antwort?
- Was erschien im Chart?
- Gab es Fehler?
