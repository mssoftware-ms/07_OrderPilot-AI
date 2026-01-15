# KO-/Turbo-Score-System

Ziel: **KO-Derivate (Long/Short) bewerten** anhand der verfügbaren Felder (`Hebel`, `Bid/Ask` bzw. `Spread %`, `KO-Level`, `Richtung`) und eines festen Trading-Plans.

**Wichtige Erkenntnis:** Bei gleichem Risk/Reward-Verhältnis ist ein **niedrigerer Hebel mit niedrigerem Spread** oft besser, da der absolute Verlust bei Stop-Loss geringer ist.

---

## 1) Inputs (pro Produkt)
- Underlying-Kurs aktuell: `U0` (Realtime aus Chart-Feed)
- Richtung: `dir ∈ {LONG, SHORT}`
- Hebel: `L`
- KO-Level: `KO`
- Bid/Ask: `bid`, `ask` (oder `Spread%` wenn kein Bid/Ask verfügbar)

**Default-Parameter:**
- `dsl = 0.01` (Stop-Loss: -1%)
- `dtp = 0.02` (Take-Profit: +2%)
- `dgap = 0.005` (Gap-Puffer: 0.5%)

---

## 2) Beispielrechnung: Warum Spread wichtig ist

### Produkt A: Hebel 4, Spread 0.11%
**Einsatz: 1000€**

| Szenario | Brutto | Spread-Kosten | Netto | Ergebnis |
|----------|--------|---------------|-------|----------|
| SL bei -1% | -4% | ~0.11% | -4.11% | **-41.10€** |
| TP bei +2% | +8% | ~0.11% | +7.89% | **+78.90€** |

**Risk/Reward: 1.92**

### Produkt B: Hebel 6.5, Spread 0.27%
**Einsatz: 1000€**

| Szenario | Brutto | Spread-Kosten | Netto | Ergebnis |
|----------|--------|---------------|-------|----------|
| SL bei -1% | -6.5% | ~0.27% | -6.77% | **-67.70€** |
| TP bei +2% | +13% | ~0.27% | +12.70% | **+127.00€** |

**Risk/Reward: 1.88**

**Fazit:** Produkt A hat weniger absoluten Verlust bei gleichem R/R!

---

## 3) KO-Abstand und Gate (HART)

**KO-Abstand in % vom Underlying**
- **LONG:** `dko = (U0 - KO) / U0`
- **SHORT:** `dko = (KO - U0) / U0`

**Gate-Regel: KO muss UNTERHALB des Stop-Loss liegen**

Bei LONG mit `dsl=1%` und `dgap=0.5%`:
- Stop-Loss wird bei -1% ausgelöst (Kurs 100€ → SL bei 99€)
- KO muss mindestens 1.5% unter Kurs liegen (KO bei ≤98.50€)
- So hat man Puffer zwischen SL und KO (kein Overnight-Gap-Risiko)

**Gate-Prüfung:** `dko >= dsl + dgap`
- Falls nein → **Score = 0** (Produkt zu riskant)

**Margin hinter Stop (für Bonus):**
- `margin = dko - dsl`

---

## 4) Spread aus Bid/Ask (Execution-realistisch)

Wenn Bid/Ask vorhanden:
```
mid = (bid + ask) / 2
s = (ask - bid) / mid    # relativer Spread
h = s / 2                # Half-Spread (für Entry/Exit)
```

Wenn nur `Spread%` vorhanden:
```
s = SpreadPct / 100
h = s / 2
```

---

## 5) Netto-Rendite bei TP und SL (inkl. Spread-Drag)

**Brutto-Renditen:**
- `r_tp_gross = L * dtp`
- `r_sl_gross = -L * dsl`

**Netto-Renditen (Entry bei Ask, Exit bei Bid):**
```
f(x) = ((1 + x) * (1 - h) / (1 + h)) - 1

r_tp = f(r_tp_gross)
r_sl = f(r_sl_gross)
```

---

## 6) Expected Value (EV)

**Treffer-Wahrscheinlichkeit (driftlos):**
```
p_tp = dsl / (dsl + dtp)  → bei 1%/2%: p_tp = 0.333
p_sl = 1 - p_tp           → 0.667
```

**EV pro Produkt:**
```
EV = p_tp * r_tp + p_sl * r_sl
```

---

## 7) Teil-Scores (je 0..1)

### 7.1 Spread-Effizienz (45% Gewicht)
**Underlying-Equivalent-Spread:**
```
ues = s / L
```
Der UES normalisiert den Spread auf Underlying-Ebene. Hoher Hebel "verdünnt" den Spread.

**Score (Parameter `ues0 = 0.0005`):**
```
S_spread = 1 / (1 + (ues/ues0)²)
```

### 7.2 Hebel-Score (30% Gewicht)
Logarithmisch saturiert, damit nicht "max Hebel gewinnt".

**Parameter `L_cap = 10`:**
```
S_lev = log(1 + L) / log(1 + L_cap)
```
Bei L=10: S_lev=1.0, bei L=5: S_lev≈0.75

### 7.3 KO-Safety-Score (20% Gewicht)
Bonus für extra Puffer zwischen SL und KO.

**Parameter `m_good = 0.005` (0.5% extra):**
```
S_ko = clamp(margin / m_good, 0, 1)
```

### 7.4 EV-Score (5% Gewicht)
Feinschliff basierend auf Expected Value.

**Parameter `EV_ref = -0.01`:**
```
S_ev = clamp(1 + EV/|EV_ref|, 0, 1)
```

---

## 8) Final Score (0..100)

**Gewichte:**
- `w_spread = 0.45`
- `w_lev = 0.30`
- `w_ko = 0.20`
- `w_ev = 0.05`

**Wenn Gate fail → Score = 0**

Sonst:
```
Score = 100 * (w_spread*S_spread + w_lev*S_lev + w_ko*S_ko + w_ev*S_ev)
```

**Quality-Penalty:** Abzüge für Flags (PARSING_UNCERTAIN, LOW_CONFIDENCE, etc.)

---

## 9) Implementierung

**Datei:** `src/derivatives/ko_finder/engine/ranking.py`

**Klassen:**
- `ScoringParams` - Alle konfigurierbaren Parameter
- `ScoreBreakdown` - Detaillierte Score-Aufschlüsselung
- `RankingEngine` - Haupt-Scoring-Logik

**Verwendung:**
```python
from src.derivatives.ko_finder.engine.ranking import RankingEngine, ScoringParams

# Mit Default-Parametern
engine = RankingEngine(config, underlying_price=100.0)

# Mit Custom-Parametern
params = ScoringParams(dsl=0.015, dtp=0.03)  # 1.5% SL, 3% TP
engine = RankingEngine(config, params=params, underlying_price=100.0)

# Produkte ranken
ranked = engine.rank(products, top_n=10)
```

---

## 10) Helper-Funktionen

```python
def clamp(x, min_val, max_val):
    return max(min_val, min(max_val, x))

def net_return(r_gross, h):
    return ((1 + r_gross) * (1 - h) / (1 + h)) - 1
```
