Das ist ein exzellentes Setup. Da du bereits eine Python-Umgebung mit Live-Daten und API-Zugriff hast, sollten wir die **AI (LLM) von deterministischen Aufgaben entlasten**. LLMs sind teuer, langsam und halluzinieren bei Mathe. Python ist schnell, kostenlos und präzise bei Logik.

Wir bauen eine **hybride Architektur**:

1. **Python (Der Quant):** Berechnet Indikatoren, bestimmt das Marktregime (Regelbasiert), validiert Daten und berechnet Risiko.
2. **AI (Der Analyst):** Bewertet Nuancen (Struktur, Wicks, "Look & Feel"), bestätigt Setups und liefert die finale Trade-Entscheidung.

Hier ist der Implementierungsplan für deine Software.

---

### Modul 1: Data Engineering & Validierung (Python)

*Ziel: Die KI darf keine "schmutzigen" Daten sehen. Wir filtern Garbage-In sofort heraus.*

Implementiere diese **Pre-Flight-Checks** als Python-Funktion, die *vor* jedem AI-Call läuft.

**Checkliste für Python-Code:**

1. **Timestamp-Check (UTC):**
* Prüfe: Ist der Zeitstempel der letzten Kerze `Current_Time - Interval`?
* *Logik:* Wenn `Time_Delta > Interval * 1.5`, liegt ein API-Lag oder Websocket-Disconnect vor. -> **Abort Analysis**.


2. **Bad Tick Detection (Z-Score):**
* Berechne Z-Score für `High` und `Low` der letzten Kerze basierend auf der Volatilität der letzten 20 Kerzen.
* *Regel:* Wenn Z-Score > 4 (statistisch extrem unwahrscheinlich), ersetze den Wert durch den Median der letzten 3 Kerzen, bevor Indikatoren berechnet werden. Dies verhindert, dass EMAs durch "Fat Fingers" zerschossen werden.




3. **Null-Volumen-Check:**
* Hat die aktuelle Kerze `Volume == 0`? -> Datenleck. **Abort**.



---

### Modul 2: Deterministische Marktregime-Erkennung (Python)

*Ziel: Die KI muss nicht raten, ob wir im Trend sind. Python sagt es ihr basierend auf harter Mathematik.*

Integriere diese Logik fest in dein Skript. Das Ergebnis (Regime-ID) wird Teil des Prompts an die KI.

**Die Regime-Matrix (Hard-Coded):**

| Regime | Python-Bedingung (Pandas/Ta-Lib) | Strategie-Freigabe |
| --- | --- | --- |
| **Trend (Bull)** | `Close > EMA20 > EMA50 > EMA200` AND `ADX(14) > 25` | Nur Long-Pullbacks (Strategy C) |
| **Trend (Bear)** | `Close < EMA20 < EMA50 < EMA200` AND `ADX(14) > 25` | Nur Short-Pullbacks (Strategy C) |
| **Range (Chop)** | `ADX(14) < 20` AND `BB_Width` ist stabil | Scalping / SFP (Strategy A) |
| **Volatilität (Explosive)** | `ATR(14) > SMA(ATR, 20) * 1.5` | Breakout (Strategy B) oder No-Trade |

*Code-Snippet Logik (Pseudo-Python):*

```python
if adx > 25 and price > ema20 > ema50:
    regime = "STRONG_TREND_BULL"
elif adx < 20:
    regime = "CHOP_RANGE"
else:
    regime = "NEUTRAL"

```

---

### Modul 3: Feature Engineering (Der AI-Input)

*Ziel: Die KI erhält keine rohen OHLCV-Listen, sondern "Features".*

Erstelle ein JSON-Objekt, das du in den Prompt injizierst. Das spart Token und erhöht die Präzision.

**Berechne in Python und sende an KI:**

1. **EMA-Distance:** `% Abstand` des Preises zum EMA20 und EMA200 (ist der Preis überdehnt? -> Mean Reversion Hinweis).
2. **RSI-State:** Nicht nur der Wert (z.B. 65), sondern der Status: `Overbought (>70)`, `Oversold (<30)`, `Neutral`.
3. **Bollinger-%B:** Wo befindet sich der Preis im Band? (1.0 = Oberes Band, 0.0 = Unteres Band). 


4. **Bitunix-Specials (Via API):**
* **Funding Rate:** Aktuelle Rate. Ist sie > 0.01% (Crowded Longs)? 


* **Open Interest (OI) Change:** `% Änderung` in der letzten Stunde. (Steigendes OI + Preisänderung = Trendbestätigung).



---

### Modul 4: AI-Analyse & Entscheidung (Der Prompt)

*Ziel: Die KI sucht nur noch nach **Struktur** und **Kontext**, die Python schwer fällt.*

Da du GPT-5.1 nutzt, kannst du sehr spezifisch sein. Dein Prompt sollte folgende Struktur haben:

**Prompt-Struktur (Template):**

1. **Rolle:** "Du bist Senior Crypto Analyst."
2. **Input Daten (JSON):**
* `Regime`: "STRONG_TREND_BULL" (von Python berechnet)
* `Technicals`: {RSI: 65, EMA_Dist: 2%, Funding: 0.005%}
* `Structure`: Liste der letzten 3 Pivot-Points (Highs/Lows) - *Python kann `scipy.signal.argrelextrema` nutzen, um diese vorzuberechnen.*


3. **Aufgabe:**
* "Analysiere die Kerzenstruktur der letzten 5 Kerzen auf **SFP (Swing Failure Pattern)** oder **Absorption** an den Pivot-Punkten."
* "Bestätige, ob das Python-Regime visuell Sinn ergibt."
* "Prüfe auf **Divergenzen** zwischen RSI und Preisstruktur (Python liefert Werte, KI sieht das Muster)."


4. **Output Format (Zwingend JSON für deine Software):**

```json
{
  "setup_detected": true,
  "setup_type": "PULLBACK_EMA20",
  "confidence_score": 85,
  "reasoning": "Python meldet Bull-Trend. Preis testet EMA20. Letzte Kerze ist ein Hammer mit langem Docht (Absorption).",
  "invalidation_level": 94500.50
}

```

---

### Modul 5: Execution & Risk Management (Python)

*Ziel: Geldmanagement macht NIEMALS die KI. Das sind harte mathematische Regeln.*

Sobald die KI `setup_detected: true` sendet, übernimmt dein Python-Skript die Exekution.

**Der Execution-Workflow:**

1. **Hard-Stop-Loss (ATR-Basiert):**
* Hole aktuellen `ATR(14)` Wert.
* *Scalping:* SL = Entry - (2.0 * ATR).
* *Swing:* SL = Entry - (3.0 * ATR). 


* *Check:* Wenn KI-Invalidation-Level < ATR-SL, nutze das KI-Level (da strukturell sinnvoller), sonst ATR.


2. **Position Sizing (2% Regel):**
* Hole `Account_Balance` (z.B. 10.000 USDT).
* Max Risk = 200 USDT.
* Distanz zum SL = `|Entry - SL|`.
* `Size = Max_Risk / Distanz`.
* *Bitunix-Check:* Prüfe, ob `Size` > Max Leverage erlaubt.


3. **Order-Typ:**
* Limit-Order (Post-Only) am Entry-Preis, um 0.02% Maker-Fee zu nutzen.


* Wenn nach x Minuten nicht gefüllt -> Cancel oder Market (je nach Dringlichkeit).



---

### Zusammenfassung: Der Code-Plan für deine Software

Hier ist die konkrete Checkliste für deine Integration:

| Modul | Python (Lokal) | AI (API) |
| --- | --- | --- |
| **1. Daten** | Fetch OHLCV + OI + Funding. Validierung (Gaps/Z-Score). | - |
| **2. Indikatoren** | Berechne RSI, EMA, ATR, ADX, Bollinger. | - |
| **3. Regime** | `if/else` Logik für Trend/Range Bestimmung. | - |
| **4. Analyse** | Erstelle JSON-Payload. | Empfängt Payload. Prüft Candlestick-Muster, SFP, Divergenzen. Gibt JSON-Decision zurück. |
| **5. Risiko** | Berechne Positionsgröße (2% Risk / ATR). | Liefert invalides Level (strukturell). |
| **6. Order** | Sendet Order an Bitunix API. Setzt SL/TP Hard im System. | - |

**Nächster Schritt:**
Soll ich dir ein **Python-Code-Gerüst** (Dummy-Klasse) erstellen, das zeigt, wie du die Indikatoren-Bibliothek (`pandas-ta`) mit der Regime-Logik verknüpfst und den JSON-Payload für die KI generierst?