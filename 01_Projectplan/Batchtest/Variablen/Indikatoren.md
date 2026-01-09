# Indikatoren - OrderPilot-AI

## Übersicht

Diese Dokumentation listet alle verfügbaren technischen Indikatoren in der OrderPilot-AI Anwendung auf.

**Gesamt: 27 Indikatoren** (9 Overlay + 18 Oszillatoren)

---

## 1. Overlay-Indikatoren (auf Preischart)

Overlay-Indikatoren werden direkt auf dem Preischart dargestellt.

| # | Indikator | Typ | Standard-Parameter | Beschreibung |
|---|-----------|-----|-------------------|--------------|
| 1 | **SMA** | IndicatorType.SMA | `period: 20` | Simple Moving Average - Einfacher gleitender Durchschnitt |
| 2 | **EMA** | IndicatorType.EMA | `period: 20` | Exponential Moving Average - Exponentieller gleitender Durchschnitt |
| 3 | **WMA** | IndicatorType.WMA | `period: 20` | Weighted Moving Average - Gewichteter gleitender Durchschnitt |
| 4 | **VWMA** | IndicatorType.VWMA | `period: 20` | Volume Weighted Moving Average - Volumengewichteter Durchschnitt |
| 5 | **BB** | IndicatorType.BB | `period: 20, std: 2` | Bollinger Bands - Volatilitätsbänder |
| 6 | **KC** | IndicatorType.KC | `period: 20, mult: 1.5` | Keltner Channel - Keltner-Kanal |
| 7 | **PSAR** | IndicatorType.PSAR | `af: 0.02, max_af: 0.2` | Parabolic SAR - Trend-Trailing-Indikator |
| 8 | **ICHIMOKU** | IndicatorType.ICHIMOKU | `tenkan: 9, kijun: 26, senkou: 52` | Ichimoku Cloud - Ichimoku-Wolke |
| 9 | **VWAP** | IndicatorType.VWAP | (keine) | Volume Weighted Average Price - Volumengewichteter Durchschnittspreis |

---

## 2. Oszillator-Indikatoren (separate Panels)

Oszillatoren werden in separaten Panels unterhalb des Preischarts dargestellt.

### 2.1 Momentum-Indikatoren

| # | Indikator | Typ | Standard-Parameter | Min | Max | Beschreibung |
|---|-----------|-----|-------------------|-----|-----|--------------|
| 1 | **RSI** | IndicatorType.RSI | `period: 14` | 0 | 100 | Relative Strength Index - Relative-Stärke-Index |
| 2 | **MACD** | IndicatorType.MACD | `fast: 12, slow: 26, signal: 9` | - | - | Moving Average Convergence Divergence |
| 3 | **STOCH** | IndicatorType.STOCH | `k_period: 14, d_period: 3` | 0 | 100 | Stochastic Oscillator - Stochastik |
| 4 | **CCI** | IndicatorType.CCI | `period: 20` | -200 | 200 | Commodity Channel Index |
| 5 | **MFI** | IndicatorType.MFI | `period: 14` | 0 | 100 | Money Flow Index - Geldflussindex |
| 6 | **MOM** | IndicatorType.MOM | `period: 10` | - | - | Momentum |
| 7 | **ROC** | IndicatorType.ROC | `period: 10` | - | - | Rate of Change - Änderungsrate |
| 8 | **WILLR** | IndicatorType.WILLR | `period: 14` | -100 | 0 | Williams %R |

### 2.2 Trendstärke-Indikatoren

| # | Indikator | Typ | Standard-Parameter | Min | Max | Beschreibung |
|---|-----------|-----|-------------------|-----|-----|--------------|
| 9 | **ADX** | IndicatorType.ADX | `period: 14` | 0 | 100 | Average Directional Index - Trendstärke |

### 2.3 Volatilitäts-Indikatoren

| # | Indikator | Typ | Standard-Parameter | Min | Max | Beschreibung |
|---|-----------|-----|-------------------|-----|-----|--------------|
| 10 | **ATR** | IndicatorType.ATR | `period: 14` | 0 | - | Average True Range - Durchschnittliche wahre Schwankungsbreite |
| 11 | **NATR** | IndicatorType.NATR | `period: 14` | 0 | - | Normalized ATR - Normalisierte ATR |
| 12 | **STD** | IndicatorType.STD | `period: 20` | 0 | - | Standard Deviation - Standardabweichung |
| 13 | **BB_WIDTH** | IndicatorType.BB_WIDTH | `period: 20, std: 2` | 0 | - | Bollinger Band Width - BB-Breite |
| 14 | **BB_PERCENT** | IndicatorType.BB_PERCENT | `period: 20, std: 2` | 0 | 1.2 | %B - Bollinger %B |

### 2.4 Volumen-Indikatoren

| # | Indikator | Typ | Standard-Parameter | Min | Max | Beschreibung |
|---|-----------|-----|-------------------|-----|-----|--------------|
| 15 | **OBV** | IndicatorType.OBV | (keine) | - | - | On-Balance Volume |
| 16 | **CMF** | IndicatorType.CMF | `period: 20` | -1 | 1 | Chaikin Money Flow |
| 17 | **AD** | IndicatorType.AD | (keine) | - | - | Accumulation/Distribution Line |
| 18 | **FI** | IndicatorType.FI | `period: 13` | - | - | Force Index - Kraftindex |

---

## 3. Trading Bot Indikatoren

Der Trading Bot verwendet intern folgende Indikatoren für die Signalgenerierung:

| Indikator | Perioden | Verwendung |
|-----------|----------|------------|
| **EMA-Stack** | 9, 21, 50, 200 | Trend-Erkennung, EMA-Alignment |
| **RSI** | 14 | Momentum, Überkauft/Überverkauft |
| **MACD** | 12/26/9 | Crossover-Signale, Momentum |
| **Stochastic** | 14/3 | Momentum, Überkauft/Überverkauft |
| **Bollinger Bands** | 20, std=2 | Volatilität, Price-Position |
| **ATR** | 14 | Stop-Loss/Take-Profit Berechnung |
| **ADX** | 14 | Trendstärke |
| **Volume MA** | 20 | Volumenbestätigung |

---

## 4. Quelldateien

- `src/core/indicators/registry.py` - Zentrale Indikator-Registry
- `src/core/indicators/engine.py` - Indikator-Engine mit IndicatorType-Enum
- `src/core/trading_bot/indicator_calculator.py` - Trading Bot Indikator-Berechnungen
- `src/ui/widgets/indicators.py` - UI-Indikator-Widget

---

*Dokument erstellt: 2026-01-09*
