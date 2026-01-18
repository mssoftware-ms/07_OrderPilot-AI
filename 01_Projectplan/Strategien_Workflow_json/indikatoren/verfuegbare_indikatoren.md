# Verfügbare Indikatoren im OrderPilot-AI Chartfenster

Diese Liste enthält alle technischen Indikatoren, die im Chartfenster verfügbar sind.

## Overlay-Indikatoren
Diese Indikatoren werden direkt auf dem Preischart angezeigt.

### 1. Moving Averages (Gleitende Durchschnitte)

#### SMA - Simple Moving Average
- **Beschreibung**: Einfacher gleitender Durchschnitt
- **Standard-Parameter**: `period: 20`
- **Anzeige**: SMA(20)
- **Kategorie**: Trend

#### EMA - Exponential Moving Average
- **Beschreibung**: Exponentieller gleitender Durchschnitt (stärkere Gewichtung aktueller Preise)
- **Standard-Parameter**: `period: 20`
- **Anzeige**: EMA(20)
- **Kategorie**: Trend

#### WMA - Weighted Moving Average
- **Beschreibung**: Gewichteter gleitender Durchschnitt
- **Standard-Parameter**: `period: 20`
- **Anzeige**: WMA(20)
- **Kategorie**: Trend

#### VWMA - Volume Weighted Moving Average
- **Beschreibung**: Volumengewichteter gleitender Durchschnitt
- **Standard-Parameter**: `period: 20`
- **Anzeige**: VWMA(20)
- **Kategorie**: Trend/Volume

### 2. Bands & Channels (Bänder & Kanäle)

#### BB - Bollinger Bands
- **Beschreibung**: Bollinger-Bänder (Volatilitätsindikator)
- **Standard-Parameter**:
  - `period: 20`
  - `std: 2`
- **Anzeige**: BB(20,2)
- **Komponenten**: Upper Band, Middle Band (SMA), Lower Band
- **Kategorie**: Volatilität

#### KC - Keltner Channels
- **Beschreibung**: Keltner-Kanäle (ATR-basierte Bänder)
- **Standard-Parameter**:
  - `period: 20`
  - `mult: 1.5`
- **Anzeige**: KC(20,1.5)
- **Komponenten**: Upper Channel, Middle Line (EMA), Lower Channel
- **Kategorie**: Volatilität

### 3. Trend Following

#### PSAR - Parabolic SAR
- **Beschreibung**: Parabolic Stop and Reverse (Trend-Umkehr-Indikator)
- **Standard-Parameter**:
  - `af: 0.02`
  - `max_af: 0.2`
- **Anzeige**: PSAR
- **Kategorie**: Trend

#### ICHIMOKU - Ichimoku Cloud
- **Beschreibung**: Ichimoku Kinko Hyo (Cloud-Indikator)
- **Standard-Parameter**:
  - `tenkan: 9`
  - `kijun: 26`
  - `senkou: 52`
- **Anzeige**: Ichimoku
- **Komponenten**: Tenkan-sen, Kijun-sen, Senkou Span A, Senkou Span B, Chikou Span
- **Kategorie**: Trend

### 4. Volume Overlay

#### VWAP - Volume Weighted Average Price
- **Beschreibung**: Volumengewichteter Durchschnittspreis
- **Standard-Parameter**: Keine
- **Anzeige**: VWAP
- **Kategorie**: Volume

---

## Oszillator-Indikatoren
Diese Indikatoren werden in separaten Panels unter dem Preischart angezeigt.

### 1. Momentum-Indikatoren

#### RSI - Relative Strength Index
- **Beschreibung**: Relative-Stärke-Index (Momentum-Oszillator)
- **Standard-Parameter**: `period: 14`
- **Anzeige**: RSI(14)
- **Wertebereich**: 0-100
- **Kategorie**: Momentum

#### MACD - Moving Average Convergence Divergence
- **Beschreibung**: MACD-Indikator
- **Standard-Parameter**:
  - `fast: 12`
  - `slow: 26`
  - `signal: 9`
- **Anzeige**: MACD(12,26,9)
- **Komponenten**: MACD-Linie, Signal-Linie, Histogramm
- **Kategorie**: Trend/Momentum

#### STOCH - Stochastic Oscillator
- **Beschreibung**: Stochastischer Oszillator
- **Standard-Parameter**:
  - `k_period: 14`
  - `d_period: 3`
- **Anzeige**: STOCH(14,3)
- **Wertebereich**: 0-100
- **Komponenten**: %K-Linie, %D-Linie
- **Kategorie**: Momentum

#### CCI - Commodity Channel Index
- **Beschreibung**: Rohstoff-Kanal-Index
- **Standard-Parameter**: `period: 20`
- **Anzeige**: CCI(20)
- **Wertebereich**: -200 bis +200
- **Kategorie**: Momentum

#### MFI - Money Flow Index
- **Beschreibung**: Geldfluss-Index (volumengewichteter RSI)
- **Standard-Parameter**: `period: 14`
- **Anzeige**: MFI(14)
- **Wertebereich**: 0-100
- **Kategorie**: Momentum/Volume

#### MOM - Momentum
- **Beschreibung**: Momentum-Indikator (Preisänderung)
- **Standard-Parameter**: `period: 10`
- **Anzeige**: MOM(10)
- **Kategorie**: Momentum

#### ROC - Rate of Change
- **Beschreibung**: Änderungsrate (prozentuale Preisänderung)
- **Standard-Parameter**: `period: 10`
- **Anzeige**: ROC(10)
- **Kategorie**: Momentum

#### WILLR - Williams %R
- **Beschreibung**: Williams Prozent Range
- **Standard-Parameter**: `period: 14`
- **Anzeige**: Williams %R(14)
- **Wertebereich**: -100 bis 0
- **Kategorie**: Momentum

### 2. Trend Strength (Trendstärke)

#### ADX - Average Directional Index
- **Beschreibung**: Durchschnittlicher Richtungsindex (Trendstärke)
- **Standard-Parameter**: `period: 14`
- **Anzeige**: ADX(14)
- **Wertebereich**: 0-100
- **Kategorie**: Trend

### 3. Volatilitäts-Indikatoren

#### ATR - Average True Range
- **Beschreibung**: Durchschnittliche wahre Handelsspanne (Volatilität)
- **Standard-Parameter**: `period: 14`
- **Anzeige**: ATR(14)
- **Wertebereich**: ≥ 0
- **Kategorie**: Volatilität

#### NATR - Normalized ATR
- **Beschreibung**: Normalisierte ATR (prozentual)
- **Standard-Parameter**: `period: 14`
- **Anzeige**: NATR(14)
- **Wertebereich**: ≥ 0
- **Kategorie**: Volatilität

#### STD - Standard Deviation
- **Beschreibung**: Standardabweichung (Volatilität)
- **Standard-Parameter**: `period: 20`
- **Anzeige**: StdDev(20)
- **Wertebereich**: ≥ 0
- **Kategorie**: Volatilität

#### BB_WIDTH - Bollinger Band Width
- **Beschreibung**: Breite der Bollinger-Bänder
- **Standard-Parameter**:
  - `period: 20`
  - `std: 2`
- **Anzeige**: BB Width
- **Wertebereich**: ≥ 0
- **Kategorie**: Volatilität

#### BB_PERCENT - Bollinger %B
- **Beschreibung**: Position des Preises innerhalb der Bollinger-Bänder
- **Standard-Parameter**:
  - `period: 20`
  - `std: 2`
- **Anzeige**: %B
- **Wertebereich**: 0-1.2
- **Kategorie**: Volatilität

### 4. Volume-Indikatoren

#### OBV - On-Balance Volume
- **Beschreibung**: Bilanz-Volumen (kumuliertes Volumen)
- **Standard-Parameter**: Keine
- **Anzeige**: OBV
- **Kategorie**: Volume

#### CMF - Chaikin Money Flow
- **Beschreibung**: Chaikin Geldfluss
- **Standard-Parameter**: `period: 20`
- **Anzeige**: CMF(20)
- **Wertebereich**: -1 bis +1
- **Kategorie**: Volume

#### AD - Accumulation/Distribution Line
- **Beschreibung**: Akkumulations-/Distributions-Linie
- **Standard-Parameter**: Keine
- **Anzeige**: A/D Line
- **Kategorie**: Volume

#### FI - Force Index
- **Beschreibung**: Kraft-Index (Preis × Volumen)
- **Standard-Parameter**: `period: 13`
- **Anzeige**: Force Index(13)
- **Kategorie**: Volume

---

## Zusammenfassung

**Gesamt**: 27 Indikatoren

**Overlay-Indikatoren** (9):
- Moving Averages: SMA, EMA, WMA, VWMA
- Bands & Channels: BB, KC
- Trend: PSAR, ICHIMOKU
- Volume: VWAP

**Oszillator-Indikatoren** (18):
- Momentum: RSI, MACD, STOCH, CCI, MFI, MOM, ROC, WILLR
- Trend Strength: ADX
- Volatilität: ATR, NATR, STD, BB_WIDTH, BB_PERCENT
- Volume: OBV, CMF, AD, FI

## Implementierungs-Details

Die Indikatoren werden berechnet durch:
- **TA-Lib** (bevorzugt, falls verfügbar)
- **pandas_ta** (Alternative)
- **Manuelle Berechnung** (Fallback)

Alle Indikatoren sind in folgenden Modulen implementiert:
- `src/core/indicators/trend.py` - Trend-Indikatoren
- `src/core/indicators/momentum.py` - Momentum-Indikatoren
- `src/core/indicators/volatility.py` - Volatilitäts-Indikatoren
- `src/core/indicators/volume.py` - Volume-Indikatoren
- `src/core/indicators/registry.py` - Zentrale Registry

---

*Generiert am: 2026-01-17*
*Projekt: OrderPilot-AI*
