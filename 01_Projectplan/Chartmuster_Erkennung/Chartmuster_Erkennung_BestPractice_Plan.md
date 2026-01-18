# Chartmuster-Erkennung (Pattern Recognition) für Tageschart + „letzte XX Bars“
**Best-Practice Recherche + konkreter Architektur-/Algorithmus-Plan (BTCUSDT, Bitunix)**

> Fokus: **Tageschart** (Swing) sowie „**aktuelle XX Bars**“ (Sliding Window) gegen Historie matchen.  
> Ziel: Muster **deterministisch** und **reproduzierbar** erkennen, im Chart markieren und als Features in `Marktanalyse.json` / RegimeSet einspeisen.

---

## 1) Warum Chartmuster-Erkennung schwierig ist (und wie man es sauber macht)
Klassische Chartmuster sind oft **subjektiv** („im Auge des Betrachters“). Best Practice ist daher:
1) Muster **formal definieren** (Pivots, Trendlinien, Toleranzen)  
2) robuste **Glättung/Feature-Extraktion** (nicht überglätten)  
3) **strenges Out-of-Sample** / Walk-forward Backtesting (Leakage vermeiden)

Lo/Mamaysky/Wang adressieren diese Subjektivität explizit und schlagen einen systematischen, algorithmischen Ansatz vor.

---

## 2) Zwei praxistaugliche Ansätze (die du kombinierst)
Am stabilsten ist ein **Hybrid**:

### A) Regelbasierte „Named Patterns“ (interpretierbar)
- Erkennung über **Swing-Points/Pivots** (ZigZag / Pivot-Detection)
- geometrische Kriterien (Toleranzen, Symmetrie, Trend-Kontext)
- Vorteil: transparent, debugbar, UI-friendly

### B) Similarity Search („finde ähnliche historische Situationen“)
- letzte **XX Bars** normalisieren, in Historie nach ähnlichen Fenstern suchen
- Distanz: Korrelation/Euclid als Filter, **DTW** als robuster Feinschritt
- Vorteil: findet Muster auch dann, wenn sie nicht perfekt einer Schablone entsprechen

DTW-basierte Pattern-Matching-Systeme im Finanzkontext sind publiziert; Sliding-Window Vorgehen ist Standard.

---

## 3) Best Practice Pipeline (Daily + „XX Bars aktuell“)

### Schritt 1: Preprocessing (Tagesbars)
- Resampling auf `1D` (falls Quelle intraday)
- `log(close)` oder Renditen verwenden
- optional: leichte Glättung (EMA/Savitzky-Golay), aber sparsam

### Schritt 2: Swing-Points / Marktstruktur (ZigZag/Pivots)
- ZigZag mit Parametern:
  - `zigzag_pct` (Prozent-Reversal)
  - oder ATR-basiert: `zigzag_atr_mult`
- Ergebnis: Sequenz signifikanter Swing High/Low Punkte (Preis-“Skelett”)

### Schritt 3: Named Patterns v1 (auf Pivots)
Implementiere wenige Muster sehr sauber:
- **Double Top / Double Bottom**
- **Triangles** (symmetrisch/ascending/descending)
- **Head & Shoulders** (Top/Bottom)
- optional: **Flags/Pennants** (Continuation)

### Schritt 4: Similarity Search v1 (XX Bars)
1) `W = close[-XX:]`
2) normalisieren (z-score oder min-max)
3) Kandidaten via schnellem Metric (Korrelation) vorfiltern
4) Top-K Kandidaten mit DTW fein bewerten (optional)
5) Match-Output + Forward-Return Statistik (z.B. +5/+10/+20 Tage)

### Schritt 5: Scoring & Status
Jedes Pattern bekommt:
- `score` (0–100)
- `direction_bias` (UP/DOWN/NONE)
- `state` (forming / confirmed / failed)
- Linien/Geometrie für UI (Neckline, Trendlines, Box)

---

## 4) Muster-Katalog (Daily) + formale Kriterien (Kurz)
### 4.1 Reversal
**Head & Shoulders (Top/Bottom)**  
- 5-Pivot Struktur: LS–Trough–Head–Trough–RS  
- Head höher (Top) bzw. tiefer (Bottom) als Schultern  
- Schultern ähnlich (Toleranzband)  
- Neckline = Verbindung der beiden Troughs  
- Confirmation: Close unter/über Neckline

**Double Top/Bottom**  
- Peak–Trough–Peak (oder umgekehrt)  
- Peaks im Toleranzband  
- Trough signifikant (X% oder Y*ATR)  
- Confirmation: Break des Zwischenlevels

### 4.2 Continuation
**Triangles**  
- Konvergierende Trendlinien (Lower Highs / Higher Lows)  
- Apex in Zukunft, abnehmende Range  
- Confirmation: Breakout/Breakdown

**Flags/Pennants**  
- Impulse Leg + kurze, enge Konsolidierung  
- Breakout in Trendrichtung

---

## 5) Muster-Scoring (0–100) – robust & backtestbar
Empfohlen: Komponenten-Score statt „ein magischer Wert“:

1) **Geometrie (0–60)**  
   Symmetrie, Verhältnis, Trendlinien-Fit (R²), saubere Swings

2) **Kontext (0–20)**  
   z.B. H&S Top nur nach Uptrend; Triangle nach Kompression

3) **Confirmation (0–20)**  
   Close jenseits der Linie (und optional Volumen-Confirm)

---

## 6) Integration in `Marktanalyse.json`
Erweitere um:
```json
"patterns": [
  {
    "pattern_id": "HNS_TOP",
    "timeframe": "1D",
    "start_index": 123,
    "end_index": 167,
    "state": "confirmed",
    "direction_bias": "DOWN",
    "score": 82.4,
    "lines": {
      "neckline": [{"t": "...", "p": ...}, {"t": "...", "p": ...}]
    },
    "notes": ["LS≈RS within 1.8%", "breakdown below neckline confirmed"]
  }
]
```

Zusätzlich für Similarity Search:
```json
"similarity_matches": [
  {
    "timeframe": "1D",
    "window_len": 60,
    "query_end_time": "...",
    "metric": "dtw",
    "top_matches": [
      {"start_time": "...", "end_time": "...", "distance": 0.37}
    ]
  }
]
```

---

## 7) Pattern als Features für CEL-Regeln (sehr empfehlenswert)
Wenn du im Bot/Analyzer die Pattern-Ergebnisse als Feature-API bereitstellst, kannst du in CEL z.B. schreiben:
- `pat.has("HNS_TOP")`
- `pat.score("TRIANGLE") >= 75`
- `pat.state("FLAG_BULL") == "forming"`

Damit sind Regeln *so* flexibel wie deine No-Trade Beispiele, ohne Codeänderungen.

---

## 8) Umsetzungsplan (kompakt, aber vollständig)
1) Pivot Engine (ZigZag/ATR-Pivots) + Tests  
2) Named Pattern Detektoren v1 + Score + UI-Linien  
3) Similarity Search v1 (corr filter -> optional DTW)  
4) Export in Marktanalyse.json  
5) UI Overlay + Tabelle im Entry Analyzer  
6) Backtest: Pattern als Feature/Signal evaluieren (Walk-forward)

---

## 9) Quellen (Primär / hochwertig)
- Lo, Mamaysky, Wang (2000): *Foundations of Technical Analysis* (Pattern Recognition, Subjektivität, Algorithmik)  
  https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf

- CFA Institute Digest (Zusammenfassung/Einordnung)  
  https://rpc.cfainstitute.org/sites/default/files/-/media/documents/article/cfa-digest/2001/dig-v31-n1-811-pdf.pdf

- New York Fed Staff Report: formale Kriterien Head-and-Shoulders  
  https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr4.pdf

- DTW Pattern Matching Trading System (Kim et al., 2018; Sliding Window)  
  https://www.preprints.org/manuscript/201810.0660/v1/download

- DTW Similarity Search & Normalisierung (Streaming-Kontext)  
  https://link.springer.com/article/10.1007/s40595-016-0062-4

- Deep Learning Pattern Recognition (CNN/LSTM)  
  https://arxiv.org/pdf/1808.00418

- Interpretable image-based DL lernt TA-ähnliche Muster (Zhang et al., 2023)  
  https://ruixunzhang.com/paper/2023_EJF_ImageML.pdf

- ZigZag Grundidee (Swing-Filter; praktikabel für Pattern-Detektion)  
  https://www.investopedia.com/terms/z/zig_zag_indicator.asp
