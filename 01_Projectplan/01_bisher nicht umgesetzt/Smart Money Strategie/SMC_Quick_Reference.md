# Smart Money Concepts (SMC) für BTC Perpetual Futures
## Quick Reference Guide & Trading Plan Template

**Version 1.0 | Pädagogisch | Keine Finanzberatung**

---

## I. QUICK START (5-Minuten-Einstieg)

### Was ist SMC?
SMC = Handelsrahmen, um zu verstehen, wie große institutionelle Spieler (Banks, Hedge Funds) Märkte bewegen.
- Sie suchen **Liquidität** (Cluster von Retail-Stops)
- Sie **manipulieren Preise** mit Fakes-Outs (Liquidity Sweeps)
- Sie handeln in **definierten Strukturen** (HH/HL, LL/LH)

### 3-Schritt Basis-Logik
1. **Bestimme Bias** (Daily: Bull/Bear/Range?)
2. **Finde POI** (Order Block, FVG, Equal Level)
3. **Warte auf Trigger** (Liquidity Sweep + BOS/CHOCH)
4. **Risiko = 1%**, Trade nur wenn R:R ≥ 1:2

---

## II. KERN-KONZEPTE (Definitions)

| Begriff | = | Beispiel |
|---------|---|---------|
| **HH/HL** | Höhere Highs/Lows | Uptrend: 40k → 41k → 40.5k → 42k |
| **LL/LH** | Niedrigere Lows/Highs | Downtrend: 45k → 43k → 44k → 42k |
| **BOS** | Break of Structure = Trendfortsetzung | Preis bricht über voriges High |
| **CHOCH** | Change of Character = Potenzielle Reversal | Preis bricht unter HL (wenn Bull) |
| **OB** | Order Block = Institutions-Kauf/Verkauf Zone | Nach großem Candle, dann Schwäche |
| **FVG** | Fair Value Gap = Preis-Lücke (Magnet) | 3 Candles ohne Overlap |
| **Liquidity** | Retail-Stops, Liquidität-Cluster | Equal Highs bei 45k (2x getestet) |
| **Sweep** | Preis über/unter Level, dann Reversal | Over 45k → triggert Stops → Reversal |

---

## III. TOP-DOWN WORKFLOW (Daily-Routine)

```
1. Daily-Chart öffnen
   ├─ Struktur? (HH/HL oder LL/LH oder Range?)
   ├─ Wenn Struktur = 3+ Candles ✓ BIAS = klar
   └─ Wenn <3 = WARTEN oder Range-Setup

2. 4H-Chart checken
   ├─ 4H-Struktur = Daily-Bias aligned? ✓ CONFLUENZ
   └─ Wenn nicht = Setup schwächer

3. Liquiditäts-Ziele finden (Daily)
   ├─ Equal Highs/Lows unter/über aktuellem Preis?
   ├─ Alte Session-Highs/-Lows?
   └─ Schwung-Highs/-Lows?

4. Premium/Discount Zone (Daily)
   ├─ Range High - Range Low finden
   ├─ 0.5 Fibonacci = Equilibrium
   └─ Oben = Premium, Unten = Discount

5. POI markieren
   ├─ Order Blocks (validiert?)
   ├─ FVGs (perfekt?)
   └─ Equal Levels

6. Warten auf Trigger (1H/15M)
   ├─ Liquidity Sweep passiert?
   ├─ CHOCH/BOS auf 4H?
   └─ Preis testet POI?

7. Entry planen
   ├─ 1% Risk berechnet?
   ├─ Position-Size = Risk ÷ Stop-Distance
   └─ R:R ≥ 1:2?

8. Trade platzieren
   ├─ Entry-Order (Limit oder Market)
   ├─ Stop-Loss setzen
   └─ TP-Levels notieren
```

---

## IV. DIE 3 ENTRY-MODELLE

### MODELL A: LIQUIDITY SWEEP → MSS → RETEST POI
**Szenarien:** Trending Markets (klarer Bias)

```
BEDINGUNGEN:
✓ Daily-Bias stabil (3+ HH/HL oder LL/LH)
✓ Liquidity-Pool bekannt
✓ Preis nähert sich Pool

TRIGGER:
1. Preis sweept Pool (über oder unter)
2. 4H zeigt BOS/CHOCH (Struktur-Shift)
3. Preis bounced
4. 15M retest eines POI (OB/FVG/Equal)

SETUP-BEISPIEL (LONG):
Entry: 41.300 (Retest Bullish OB)
Stop: 40.150 (unter Sweep-Low + Buffer)
Target 1: 42.000 (1:1 R:R)
Target 2: 43.600 (1:2 R:R)
Risk: 1% Account = $500
```

**Warum es funktioniert:**
- Sweep = Retail-Liquidation, gibt Momentum
- POI-Retest = Institutions-Käufer/Verkäufer reagiert dort

**Typische Fehler:**
- Zu früh einsteigen (vor Sweep)
- Falsche Liquiditäts-Ziele
- CHOCH auf Daily nicht erkannt

---

### MODELL B: TREND CONTINUATION MIT PULLBACK
**Szenarien:** Trending Markets mit interner Korrektur

```
BEDINGUNGEN:
✓ Daily-Bias stabil
✓ ABER: Kurz-fristiger CHOCH auf M15 (Korrektur)
✓ Daily-HL intakt! (nicht gebrochen)
✓ Preis im Discount (Bull) oder Premium (Bear)

TRIGGER:
1. 15M bildet höhere Low (wenn Bull)
2. 5M zeigt BOS zurück in Trend-Richtung
3. Retest eines OB/FVG in Discount/Premium

SETUP-BEISPIEL (LONG):
Entry: 41.250 (OTE Zone)
Stop: 40.800 (unter Discount)
Target 1: 41.700 (1:1)
Target 2: 42.150 (1:2)
Risk: $500 (1%)
```

**Warum es funktioniert:**
- Pullbacks in Trending Markets sind sehr häufig
- Discount = besserer Risk:Reward als bei Premium-Entry

**Typische Fehler:**
- Daily-CHOCH vs. 15M-CHOCH verwechseln
- Zu späte Entry (Setup vorbei)
- Discount-Zone falsch berechnet

---

### MODELL C: RANGE-TRADING (Konsolidierung)
**Szenarien:** Seitwärts-Märkte

```
BEDINGUNGEN:
✓ Daily = NO HH/HL oder LL/LH = RANGE!
✓ Preis oszilliert zwischen Support & Resistance
✓ Multiple Reaction am Boundary

TRIGGER:
1. Preis testet Support oder Resistance
2. Liquidity Sweep über/unter Boundary
3. Sofort: Rejection CHOCH/BOS zurück
4. Entry auf Bounce mit POI

SETUP-BEISPIEL (BOUNCE AM SUPPORT):
Entry: 40.600 (Bounce nach Sweep)
Stop: 39.800 (unter Support + Buffer)
Target: 43.000 (Range-Top) oder Midpoint
Risk: $500 (1%)
```

**Warum es funktioniert:**
- Range = Accumulation/Distribution Phase
- Bounces an Boundaries sind repetitiv

**Typische Fehler:**
- Range nicht korrekt identifiziert
- Zu lange halten (Range bricht plötzlich)
- Entry beim Peak statt nach Sweep

---

## V. RISK & FUTURES ESSENTIALS

### 1% REGEL (Non-Negotiable)

```
Schritt 1: 1% des Accounts = Max-Risk
  Account: $50.000
  1% = $500 pro Trade

Schritt 2: Stop-Distance berechnen
  Entry: 40.000
  Stop: 39.500
  Distance: 500 USD/BTC

Schritt 3: Position-Size
  Position = $500 Risk ÷ 500 USD/BTC = 1 BTC
  ABER: realistische = 0.01-0.1 BTC

Schritt 4: Leverage
  Position-Value = 0.01 BTC × $40.000 = $400
  Margin used = $400 ÷ desired_leverage
  z.B. 1x Leverage = $400 Margin benötigt

Schritt 5: Check Liquidation Price
  Muss ≥ 10% buffer haben vom Entry
  Wenn nicht → Leverage reduzieren
```

### LIQUIDATIONS-BUFFER
```
Faustregel für Anfänger:
- Leverage ≤ 5x
- Liquidation-Preis ≥ 10% weg von Entry
- Isolated Margin (nicht Cross!)
- Buffer = 2-5% des Accounts ungenutzt halten
```

### FUNDING RATE CHECK
```
Bevor Long eingehen:
- Wenn Funding Rate > +0.15% → Kosten zu hoch
- Check: Binance/Bybit Funding-Sektion
- Kostet ~$10-50/Tag für 0.1-0.5 BTC bei +0.3%
```

---

## VI. PRE-TRADE CHECKLIST

**Bevor Order platziert wird:**

- [ ] Daily-Struktur klar (3+ Candles)? 
- [ ] 4H-Struktur aligned mit Daily?
- [ ] Liquidity-Pool identifiziert?
- [ ] POI vorhanden (OB, FVG, Equal)?
- [ ] POI validiert (nicht mitigiert)?
- [ ] Sweep + BOS/CHOCH + LTF-Confirmation?
- [ ] Entry-Preis exakt?
- [ ] Stop-Preis logisch?
- [ ] Risk = 1% genau?
- [ ] Position-Size berechnet?
- [ ] R:R ≥ 1:2?
- [ ] Liq-Buffer ≥ 10%?
- [ ] Funding-Rate OK?

**Wenn irgendein Punkt = NEIN → SETUP SKIPPPEN**

---

## VII. HÄUFIGE FEHLER

1. **Zu viele POIs sehen** → Filter: Nur Daily/4H Confluence
2. **FVG überall** → Perfect-FVG rule: strict 3-Candle, NO overlap
3. **Bias fehlt** → Daily MUSS 3+ Candles HH/HL oder LL/LH sein
4. **Confirmation Chasing** → Entry 5-20min nach Signal, nicht später
5. **Breite Stops** → Stop logisch unter Liquidity-Pool, nicht arbitrary
6. **Keine Unterscheidung Setup-Qualität** → A/B/C bewerten, C skippen
7. **Range-Break nicht erkannt** → Täglich prüfen: ist noch in Range?
8. **Funding ignoriert** → +0.3% = ~$40/Tag für 0.1 BTC Kosten
9. **Zu große Position** → Leverage-Gier, Liquidation droht
10. **Kein Journaling** → Keine Lernung, gleiche Fehler wiederholt

---

## VIII. TRADE-MANAGEMENT-REGELN

**Während Position offen:**

```
Frühe Phase (0-30 min):
- +25% Gewinn? → 50% schließen, Stop Breakeven
- -20% Verlust? → Check Stop-Logik, oder Exit planen

Mid Phase (30 min - 4h):
- +50% Gewinn? → 70% schließen, Trail remaining
- Hoffen auf Target-Levels

Spät Phase (4h+):
- Trail Stop bei neuen Struktur-Levels (HL wenn Bull)
- Daily-Bias geändert? → Close sofort

Täglich-Check:
- Daily-Bias noch intact?
- Funding-Rate zu hoch?
- Neue CHOCH-Warnung?
```

---

## IX. SESSION-SPEZIFISCHE TIPPS

### LONDON SESSION (08:00-16:00 GMT)
```
Erstes Stunde = SWEEP-STUNDE (Asian Range)
- Nicht traden, nur beobachten
- Nach Sweep: Beste Setup-Qualität

Mid-London (10:00-13:00)
- New Range oder Trend gebildet?
- Order Blocks formieren sich
- Gutes Setup-Window
```

### NEW YORK SESSION (13:00-21:00 GMT)
```
NY-Open = Oft Extension oder Reversal der London-Range
- Wenn Range breakout → Trend-Setups
- Wenn Range-Konsolidierung → Bounce-Setups

Spät NY (17:00+)
- Volatilität sinkt
- Keine neuen Setups anhaltbar
- Profit-Taking phase
```

**Regel: Bias-Alignment über Sessions = höhere Erfolgsquote**

---

## X. TEMPLATE: TÄGLICHER TRADING-PLAN

```
=== TÄGLICHER PLAN ===
Datum: [TT.MM.JJJJ]

MARKET ANALYSE (vor Market-Open):
Daily Bias: [ ] Bull / [ ] Bear / [ ] Range
Konfidenz: ___/10
Warnung (CHOCH): [ ] Ja [ ] Nein

LIQUIDITÄT-ZIELE:
Pool 1: _______ (Entfernung: __%)
Pool 2: _______ (Entfernung: __%)

PREMIUM/DISCOUNT:
Range High: _____ Range Low: _____
Equilibrium: _____ 
Premium-Zone: _____ - _____
Discount-Zone: _____ - _____

PUNKTE OF INTEREST (POI):
POI 1: _____ Type: [ ] OB [ ] FVG [ ] Equal
POI 2: _____ Type: [ ] OB [ ] FVG [ ] Equal

SETUP #1:
Modell: [ ] A / [ ] B / [ ] C
Entry-Preis: _____
Stop-Preis: _____
Risk-Distance: _____
Position-Size: _____
Target 1 (1:1): _____
Target 2 (1:2): _____
Invalidierung: _____

SETUP #2:
[same]

TRADE-ERGEBNISSE:
Setup #1: [Gewinn/Verlust/Nicht getraden]
Setup #2: [Gewinn/Verlust/Nicht getraden]
Daily P&L: _____ USD
Tages-Notizen: _____
```

---

## XI. 2-WOCHEN-TRAININGSPLAN

**Woche 1 (Theorie + Chart-Analyse):**
- Tag 1-2: Market Structure (HH/HL, LL/LH) finden
- Tag 3-4: OB & FVG identifizieren (10x je Typ)
- Tag 5-7: Top-Down Workflow durchlaufen (5x täglich)

**Woche 2 (Backtesting):**
- Tag 1-3: TradingView Replay (täglich 1-2 Wochen zurück)
- Tag 4-5: 5 hypothetische Trades dokumentieren
- Tag 6-7: Metriken tracken & Erfolgsquote berechnen

**Ziel:** 60%+ der hyp. Trades hätten funktioniert

---

## XII. WICHTIGSTE FORMELN

```
Bias-Confidence = (HH/HL Candles) / 10  (Max 1.0 = 100%)

Risk-Distance = Entry-Price - Stop-Loss-Price

Position-Size = (Account × 1%) / Risk-Distance

Leverage = (Position-Size × Entry-Price) / Margin-Used

Liquidation-Price (Long) ≈ Entry × (1 - 1/Leverage - Fees)

R:R Ratio = (Target - Entry) / (Entry - Stop)

Profit-Factor = (Total Wins) / (Total Losses)
```

---

## XIII. KONTROLL-FRAGEN (Selbst-Check)

```
[ ] Kann ich HH/HL vs LL/LH auf Daily unterscheiden?
[ ] Weiß ich, wann Daily-Bias intact ist vs. CHOCH?
[ ] Kann ich Liquidity-Pools 3+ finden?
[ ] Kann ich Perfect-FVG von Rauschen unterscheiden?
[ ] Verstehe ich Premium/Discount Fib-Logik?
[ ] Kann ich OB validieren vs. unvalidiert bestimmen?
[ ] Kann ich BOS/CHOCH signalisieren erkennen?
[ ] Kann ich 1% Risk-Regel korrekt anwenden?
[ ] Kann ich Position-Size berechnen?
[ ] Verstehe ich Liquidations-Risiko + Buffer?
[ ] Kann ich alle 3 Entry-Modelle durchführen?

Wenn < 8/11 JA → Noch mehr üben vor Live-Trading!
```

---

## XIV. FINAL REMINDERS

✓ **Edukativ, nicht Finanzberatung**
✓ **Crypto = hochvolatil, Leverage = Risiko**
✓ **Starte mit Demo oder Klein-Account**
✓ **1% Rule = nicht optional**
✓ **Discipline > Genie**
✓ **Journaling = dein Lernfreund**
✓ **2 Wochen Backtest vor Live**
✓ **Losses sind Teil des Spiels**

---

**Viel Erfolg beim Traden!**

*Smart Money Concepts Guide v1.0 - Educational Use Only*

