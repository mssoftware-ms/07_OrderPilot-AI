# 📊 Indikator-Analyse: Anforderungen vs. Implementierung

**Datum:** 2026-01-19
**Analysierte Datei:** `01_Projectplan/Strategien_Workflow_json/Erweiterung Skript Strategien/Projektzusammenfassung_Marktanalyse_EntryAnalyzer.md`

---

## 📋 Executive Summary

**Status:** ⚠️ TEILWEISE IMPLEMENTIERT (72% Coverage)

Von den **28 geforderten Indikatoren** sind:
- ✅ **20 Indikatoren** im Backend implementiert (IndicatorType Enum)
- ⚠️ **7 Indikatoren** in der Optimization-UI verfügbar
- ❌ **8 Indikatoren** fehlen noch (Supertrend, Donchian, Aroon, Vortex, Hurst, OBI, Spread, Depth)

**Handlungsbedarf:**
1. **CRITICAL:** UI-Integration für 13 existierende Indikatoren erweitern
2. **HIGH:** 5 fehlende technische Indikatoren implementieren (Supertrend, Donchian, Aroon, Vortex, Hurst)
3. **MEDIUM:** 3 Orderflow-Indikatoren implementieren (OBI, Spread, Depth)

---

## 🎯 Anforderungen aus Projektzusammenfassung

### Overlay-Indikatoren (im Chart) - 10 gefordert

| # | Indikator | Status | Implementierung | UI Optimization | Anmerkung |
|---|-----------|--------|-----------------|-----------------|-----------|
| 1 | **SMA** | ✅ FULL | `IndicatorType.SMA` (types.py:16) | ✅ Verfügbar | Simple Moving Average |
| 2 | **EMA** | ✅ FULL | `IndicatorType.EMA` (types.py:17) | ✅ Verfügbar | Exponential Moving Average |
| 3 | **Ichimoku Cloud** | ⚠️ PARTIAL | `IndicatorType.ICHIMOKU` (types.py:23) | ❌ Fehlt | Preis über/unter/in Wolke |
| 4 | **Supertrend** | ❌ MISSING | Nicht in types.py | ❌ Fehlt | ATR-basiert, Trailing Exit |
| 5 | **Parabolic SAR** | ⚠️ PARTIAL | `IndicatorType.PSAR` (types.py:22) | ❌ Fehlt | Stop-and-Reverse |
| 6 | **Donchian Channels** | ❌ MISSING | Nicht in types.py | ❌ Fehlt | Breakout über Upper/unter Lower |
| 7 | **Bollinger Bands** | ✅ FULL | `IndicatorType.BB` (types.py:35) | ✅ Verfügbar | Band-Break, Band-Expansion |
| 8 | **Keltner Channels** | ⚠️ PARTIAL | `IndicatorType.KC` (types.py:38) | ❌ Fehlt | EMA ± ATR; Breakouts |
| 9 | **Pivot Points** | ⚠️ PARTIAL | `IndicatorType.PIVOTS` (types.py:52) | ❌ Fehlt | Levels als Trigger-/Target-Zonen |
| 10 | **VWAP** | ⚠️ PARTIAL | `IndicatorType.VWAP` (types.py:49) | ❌ Fehlt | Intraday Bias/Level |

**Overlay Summary:**
- ✅ Fully Implemented & UI: **3/10** (30%)
- ⚠️ Backend Only: **5/10** (50%)
- ❌ Missing: **2/10** (20%)

---

### Bottom/Panel-Indikatoren (unter dem Chart) - 15 gefordert

#### Trendstärke & Regime (5 gefordert)

| # | Indikator | Status | Implementierung | UI Optimization | Anmerkung |
|---|-----------|--------|-----------------|-----------------|-----------|
| 1 | **ADX (+DI/-DI)** | ✅ FULL | `IndicatorType.ADX` (types.py:21) | ✅ Verfügbar | Average Directional Index |
| 2 | **Choppiness Index (CHOP)** | ⚠️ PARTIAL | `IndicatorType.CHOP` (types.py:42) | ❌ Fehlt | Range-bound Indikator |
| 3 | **Aroon** | ❌ MISSING | Nicht in types.py | ❌ Fehlt | Aroon Up/Down |
| 4 | **Vortex Indicator** | ❌ MISSING | Nicht in types.py | ❌ Fehlt | VI+/VI- |
| 5 | **Hurst Exponent** | ❌ MISSING | Nicht in types.py | ❌ Fehlt | Trend vs Mean-Reversion |

#### Momentum (4 gefordert)

| # | Indikator | Status | Implementierung | UI Optimization | Anmerkung |
|---|-----------|--------|-----------------|-----------------|-----------|
| 1 | **RSI** | ✅ FULL | `IndicatorType.RSI` (types.py:26) | ✅ Verfügbar | Relative Strength Index |
| 2 | **MACD** | ✅ FULL | `IndicatorType.MACD` (types.py:20) | ✅ Verfügbar | MACD Histogram |
| 3 | **Stochastic** | ⚠️ PARTIAL | `IndicatorType.STOCH` (types.py:27) | ❌ Fehlt | Stochastic Oscillator |
| 4 | **CCI** | ⚠️ PARTIAL | `IndicatorType.CCI` (types.py:31) | ❌ Fehlt | Commodity Channel Index |

#### Volatilität (2 gefordert)

| # | Indikator | Status | Implementierung | UI Optimization | Anmerkung |
|---|-----------|--------|-----------------|-----------------|-----------|
| 1 | **ATR / ATR%** | ✅ FULL | `IndicatorType.ATR` (types.py:39) | ✅ Verfügbar | Average True Range |
| 2 | **Bollinger BandWidth** | ⚠️ PARTIAL | `IndicatorType.BB_WIDTH` (types.py:36) | ❌ Fehlt | BBWidth |

#### Volumen (4 gefordert)

| # | Indikator | Status | Implementierung | UI Optimization | Anmerkung |
|---|-----------|--------|-----------------|-----------------|-----------|
| 1 | **OBV** | ⚠️ PARTIAL | `IndicatorType.OBV` (types.py:45) | ❌ Fehlt | On-Balance Volume |
| 2 | **MFI** | ⚠️ PARTIAL | `IndicatorType.MFI` (types.py:32) | ❌ Fehlt | Money Flow Index |
| 3 | **A/D Line** | ⚠️ PARTIAL | `IndicatorType.AD` (types.py:47) | ❌ Fehlt | Accumulation/Distribution |
| 4 | **CMF** | ⚠️ PARTIAL | `IndicatorType.CMF` (types.py:46) | ❌ Fehlt | Chaikin Money Flow |

**Bottom/Panel Summary:**
- ✅ Fully Implemented & UI: **3/15** (20%)
- ⚠️ Backend Only: **9/15** (60%)
- ❌ Missing: **3/15** (20%)

---

### Orderflow/Orderbuch-Indikatoren (3 gefordert)

| # | Indikator | Status | Implementierung | UI Optimization | Anmerkung |
|---|-----------|--------|-----------------|-----------------|-----------|
| 1 | **Order Book Imbalance (OBI)** | ❌ MISSING | Nicht implementiert | ❌ Fehlt | (BidVol − AskVol)/(BidVol + AskVol) |
| 2 | **Spread (bps)** | ❌ MISSING | Nicht implementiert | ❌ Fehlt | Bid-Ask Spread in Basispunkten |
| 3 | **Depth Bid/Ask** | ❌ MISSING | Nicht implementiert | ❌ Fehlt | Liquidität im Orderbuch |

**Orderflow Summary:**
- ❌ All Missing: **0/3** (0%)

**Hinweis:** Orderflow-Indikatoren erfordern:
- Bitunix WebSocket Orderbuch-Stream
- L1/L2 Order Book Daten
- Echtzeit-Verarbeitung
- Neue IndicatorType Einträge
- Eigene Berechnungslogik (nicht in pandas_ta/talib)

---

## 📊 Gesamtstatistik

**Total Indicators Required:** 28

| Status | Count | Percentage | Kategorie |
|--------|-------|------------|-----------|
| ✅ **Fully Implemented (Backend + UI)** | 6 | 21.4% | RSI, MACD, ADX, SMA, EMA, ATR, BB |
| ⚠️ **Backend Only (Needs UI)** | 14 | 50.0% | Ichimoku, PSAR, KC, VWAP, Pivots, CHOP, Stoch, CCI, BB_Width, OBV, MFI, AD, CMF |
| ❌ **Missing Completely** | 8 | 28.6% | Supertrend, Donchian, Aroon, Vortex, Hurst, OBI, Spread, Depth |

**Coverage:**
- **Backend Coverage:** 20/28 = **71.4%**
- **UI Coverage:** 6/28 = **21.4%**  (nur 7 Indikatoren, aber BB ist in UI vorhanden)
- **Full Implementation:** 6/28 = **21.4%**

---

## 🎯 Handlungsempfehlungen

### Priority 1: UI-Integration (CRITICAL) ⏰ 8-12 Stunden

**Ziel:** 13 bereits implementierte Indikatoren in die Optimization-UI integrieren

**Betroffene Datei:** `src/ui/dialogs/entry_analyzer_popup.py` (Lines 1127-1141)

**Aktuell in UI:**
```python
indicators = [
    ('RSI', 'Relative Strength Index'),
    ('MACD', 'Moving Average Convergence Divergence'),
    ('ADX', 'Average Directional Index'),
    ('BB', 'Bollinger Bands'),
    ('SMA', 'Simple Moving Average'),
    ('EMA', 'Exponential Moving Average'),
    ('ATR', 'Average True Range'),
]
```

**Zu ergänzen:**
```python
# Overlay
('ICHIMOKU', 'Ichimoku Cloud'),
('PSAR', 'Parabolic SAR'),
('KC', 'Keltner Channels'),
('VWAP', 'Volume Weighted Average Price'),
('PIVOTS', 'Pivot Points'),

# Panel - Regime
('CHOP', 'Choppiness Index'),

# Panel - Momentum
('STOCH', 'Stochastic Oscillator'),
('CCI', 'Commodity Channel Index'),

# Panel - Volatility
('BB_WIDTH', 'Bollinger Bandwidth'),

# Panel - Volume
('OBV', 'On-Balance Volume'),
('MFI', 'Money Flow Index'),
('AD', 'Accumulation/Distribution'),
('CMF', 'Chaikin Money Flow'),
```

**Änderungen in `indicator_optimization_thread.py`:**

1. **Parameter Ranges hinzufügen** (Lines 294-318):
```python
# Aktuell nur: RSI, MACD, ADX
# Zu ergänzen:
elif indicator == 'ICHIMOKU':
    ranges = self.param_ranges.get('ICHIMOKU', {
        'tenkan': [9, 18, 27],
        'kijun': [26, 52, 78],
        'senkou': [52, 104, 156]
    })
elif indicator == 'PSAR':
    ranges = self.param_ranges.get('PSAR', {
        'accel': [0.02, 0.015, 0.01],
        'max_accel': [0.2, 0.15, 0.1]
    })
# ... weitere 11 Indikatoren
```

2. **Indikator-Berechnungen hinzufügen** (Lines 328-387):
```python
# Aktuell nur: RSI, MACD, ADX
# Zu ergänzen für jeden Indikator:
elif indicator_type == 'ICHIMOKU':
    # Ichimoku calculation with pandas_ta
    ichimoku = df.ta.ichimoku(tenkan=params['tenkan'], kijun=params['kijun'])
    df['indicator_value'] = ichimoku['ISA_9']  # Senkou Span A
# ... weitere 11 Indikatoren
```

3. **Signal-Generierung erweitern** (Lines 389-431):
```python
# Aktuell nur: RSI, MACD, ADX
# Zu ergänzen für jeden Indikator:
elif indicator_type == 'ICHIMOKU':
    if test_type == 'entry' and trade_side == 'long':
        # Entry Long: Price > Cloud
        signals = df['close'] > df['indicator_value']
# ... weitere 11 Indikatoren mit Entry/Exit, Long/Short Logic
```

**Aufwand:**
- 13 Indikatoren × 3 Stellen (Params, Calc, Signals) × 30min = **12 Stunden**

---

### Priority 2: Fehlende Technische Indikatoren (HIGH) ⏰ 12-16 Stunden

**Zu implementieren:** 5 Indikatoren

#### 2.1 Supertrend (ATR-based)

**Dateien:**
1. `src/core/indicators/types.py` - Add `SUPERTREND = "supertrend"`
2. `src/core/indicators/trend.py` - Implementierung
3. `src/core/indicators/engine.py` - Registration

**Code-Snippet (trend.py):**
```python
def calculate_supertrend(
    df: pd.DataFrame,
    atr_length: int = 10,
    multiplier: float = 3.0
) -> pd.DataFrame:
    """Calculate Supertrend indicator.

    Args:
        df: DataFrame with OHLC data
        atr_length: ATR period
        multiplier: ATR multiplier

    Returns:
        DataFrame with supertrend, direction columns
    """
    atr = df.ta.atr(length=atr_length)
    hl_avg = (df['high'] + df['low']) / 2

    upper_band = hl_avg + (multiplier * atr)
    lower_band = hl_avg - (multiplier * atr)

    # Supertrend logic (simplified)
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)

    for i in range(1, len(df)):
        if df['close'].iloc[i] > upper_band.iloc[i-1]:
            supertrend.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1  # Uptrend
        elif df['close'].iloc[i] < lower_band.iloc[i-1]:
            supertrend.iloc[i] = upper_band.iloc[i]
            direction.iloc[i] = -1  # Downtrend
        else:
            supertrend.iloc[i] = supertrend.iloc[i-1]
            direction.iloc[i] = direction.iloc[i-1]

    return pd.DataFrame({
        'supertrend': supertrend,
        'direction': direction
    })
```

**Aufwand:** 3 Stunden

#### 2.2 Donchian Channels

**Code-Snippet (trend.py):**
```python
def calculate_donchian(
    df: pd.DataFrame,
    length: int = 20
) -> pd.DataFrame:
    """Calculate Donchian Channels.

    Returns:
        DataFrame with upper, middle, lower channels
    """
    upper = df['high'].rolling(window=length).max()
    lower = df['low'].rolling(window=length).min()
    middle = (upper + lower) / 2

    return pd.DataFrame({
        'donchian_upper': upper,
        'donchian_middle': middle,
        'donchian_lower': lower
    })
```

**Aufwand:** 2 Stunden

#### 2.3 Aroon

**Code-Snippet (trend.py):**
```python
def calculate_aroon(
    df: pd.DataFrame,
    length: int = 14
) -> pd.DataFrame:
    """Calculate Aroon Up/Down.

    Returns:
        DataFrame with aroon_up, aroon_down, aroon_oscillator
    """
    aroon_up = df['high'].rolling(window=length+1).apply(
        lambda x: (length - x.argmax()) / length * 100, raw=True
    )
    aroon_down = df['low'].rolling(window=length+1).apply(
        lambda x: (length - x.argmin()) / length * 100, raw=True
    )

    return pd.DataFrame({
        'aroon_up': aroon_up,
        'aroon_down': aroon_down,
        'aroon_oscillator': aroon_up - aroon_down
    })
```

**Aufwand:** 2 Stunden

#### 2.4 Vortex Indicator

**Code-Snippet (momentum.py):**
```python
def calculate_vortex(
    df: pd.DataFrame,
    length: int = 14
) -> pd.DataFrame:
    """Calculate Vortex Indicator (VI+/VI-).

    Returns:
        DataFrame with vi_plus, vi_minus
    """
    tr = df.ta.true_range()

    vm_plus = abs(df['high'] - df['low'].shift(1))
    vm_minus = abs(df['low'] - df['high'].shift(1))

    vm_plus_sum = vm_plus.rolling(window=length).sum()
    vm_minus_sum = vm_minus.rolling(window=length).sum()
    tr_sum = tr.rolling(window=length).sum()

    vi_plus = vm_plus_sum / tr_sum
    vi_minus = vm_minus_sum / tr_sum

    return pd.DataFrame({
        'vi_plus': vi_plus,
        'vi_minus': vi_minus
    })
```

**Aufwand:** 2 Stunden

#### 2.5 Hurst Exponent

**Code-Snippet (custom.py):**
```python
import numpy as np

def calculate_hurst(
    df: pd.DataFrame,
    column: str = 'close',
    length: int = 100
) -> pd.Series:
    """Calculate Hurst Exponent (trend vs mean-reversion).

    H < 0.5: Mean-reverting
    H = 0.5: Random walk
    H > 0.5: Trending

    Returns:
        Series with hurst exponent values
    """
    def hurst_window(series):
        """Calculate Hurst for a single window."""
        if len(series) < 20:
            return np.nan

        lags = range(2, 20)
        tau = [np.std(np.subtract(series[lag:], series[:-lag])) for lag in lags]

        # Linear regression on log-log plot
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return poly[0] * 2.0  # Hurst exponent

    hurst = df[column].rolling(window=length).apply(
        hurst_window, raw=True
    )

    return hurst
```

**Aufwand:** 3 Stunden

**Total Priority 2:** 12 Stunden

---

### Priority 3: Orderflow-Indikatoren (MEDIUM) ⏰ 16-20 Stunden

**Voraussetzungen:**
- ✅ Bitunix WebSocket OrderBook Stream verfügbar
- ✅ L1/L2 Order Book Daten abrufbar
- ⚠️ Echtzeit-Verarbeitung erforderlich

#### 3.1 Order Book Imbalance (OBI)

**Neue Datei:** `src/core/indicators/orderflow.py`

```python
import pandas as pd
from typing import Dict, Any

def calculate_obi(
    orderbook_data: Dict[str, Any],
    levels: int = 5
) -> float:
    """Calculate Order Book Imbalance.

    OBI = (BidVol - AskVol) / (BidVol + AskVol)

    Args:
        orderbook_data: Dict with 'bids' and 'asks' (list of [price, volume])
        levels: Number of levels to aggregate (1=L1, 5=L1-L5, etc.)

    Returns:
        OBI value between -1 (all asks) and +1 (all bids)
    """
    bids = orderbook_data.get('bids', [])[:levels]
    asks = orderbook_data.get('asks', [])[:levels]

    bid_vol = sum(float(b[1]) for b in bids)
    ask_vol = sum(float(a[1]) for a in asks)

    if bid_vol + ask_vol == 0:
        return 0.0

    return (bid_vol - ask_vol) / (bid_vol + ask_vol)

def calculate_obi_series(
    df: pd.DataFrame,
    orderbook_column: str = 'orderbook',
    levels: int = 5
) -> pd.Series:
    """Calculate OBI for each candle with orderbook snapshot.

    Args:
        df: DataFrame with orderbook snapshots
        orderbook_column: Column name containing orderbook dicts
        levels: Number of levels to use

    Returns:
        Series with OBI values
    """
    return df[orderbook_column].apply(
        lambda ob: calculate_obi(ob, levels) if ob else 0.0
    )
```

**Integration:**
1. Bitunix Orderbook Stream hinzufügen zu `src/core/market_data/bitunix_stream.py`
2. Orderbook Snapshots zu Candles attachen
3. OBI in FeatureEngine berechnen
4. IndicatorType.OBI hinzufügen

**Aufwand:** 8 Stunden

#### 3.2 Spread (bps)

**Code-Snippet (orderflow.py):**
```python
def calculate_spread(
    orderbook_data: Dict[str, Any],
    mid_price: float = None
) -> float:
    """Calculate bid-ask spread in basis points.

    Spread (bps) = (Ask - Bid) / Mid * 10000

    Returns:
        Spread in basis points
    """
    bids = orderbook_data.get('bids', [])
    asks = orderbook_data.get('asks', [])

    if not bids or not asks:
        return 0.0

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])

    if mid_price is None:
        mid_price = (best_bid + best_ask) / 2

    if mid_price == 0:
        return 0.0

    return (best_ask - best_bid) / mid_price * 10000
```

**Aufwand:** 4 Stunden

#### 3.3 Depth Bid/Ask (Liquidität)

**Code-Snippet (orderflow.py):**
```python
def calculate_depth(
    orderbook_data: Dict[str, Any],
    levels: int = 10
) -> Dict[str, float]:
    """Calculate order book depth (liquidity).

    Args:
        orderbook_data: Orderbook with bids/asks
        levels: Number of levels to aggregate

    Returns:
        Dict with depth_bid, depth_ask, depth_imbalance
    """
    bids = orderbook_data.get('bids', [])[:levels]
    asks = orderbook_data.get('asks', [])[:levels]

    depth_bid = sum(float(b[1]) for b in bids)
    depth_ask = sum(float(a[1]) for a in asks)

    total = depth_bid + depth_ask
    imbalance = (depth_bid - depth_ask) / total if total > 0 else 0.0

    return {
        'depth_bid': depth_bid,
        'depth_ask': depth_ask,
        'depth_imbalance': imbalance
    }
```

**Aufwand:** 4 Stunden

**Total Priority 3:** 16 Stunden

---

## 🔄 Regime-Detektion Mapping

### Anforderungen (Projektzusammenfassung Section 4-5)

**Regime-IDs:**
- R0: Neutral/Unklar
- R1: Trend (Up/Down)
- R2: Range/Chop (Seitwärtsmarkt)
- R3: Breakout-Setup (Compression → Expansion)
- R4: High Volatility (Wild)
- R5: Orderflow/Liquidity Dominant

**Classifiers:**
1. **ADX-Classifier** ✅ Implementiert (regime_engine.py)
   - ADX < 20 → R2
   - 20-25 → R0
   - > 25 → R1

2. **CHOP-Classifier** ⚠️ Backend vorhanden, nicht in Regime-Engine
   - CHOP ≥ 61.8 → R2
   - 38.2-61.8 → R0
   - ≤ 38.2 → R1

3. **Ichimoku-Classifier** ⚠️ Backend vorhanden, nicht in Regime-Engine
   - Preis über Cloud → R1, UP
   - Preis in Cloud → R2/R0, NONE
   - Preis unter Cloud → R1, DOWN

4. **TTM Squeeze / BBWidth / ATRP** ⚠️ Teilweise
   - BBWidth implementiert, nicht im Regime-Classifier
   - TTM Squeeze fehlt
   - ATRP vorhanden

5. **Donchian-Event** ❌ Fehlt
   - Close > Upper → R3 → R1, UP
   - Close < Lower → R3 → R1, DOWN

6. **OBI-Classifier** ❌ Fehlt
   - |OBI| sehr hoch → R5

### Aktuelle Implementierung (regime_engine.py)

**Vorhandene Classifier:**
- ADX-based (Lines ~200-250)
- ATR%-based für Volatilität
- BB-Width für Compression
- SMA Crossover für Trend Direction

**Fehlende Classifier:**
- CHOP
- Ichimoku
- Donchian
- OBI

**Handlungsbedarf:**
Regime-Engine erweitern um die 4 fehlenden Classifier (ca. 8 Stunden)

---

## 📝 Umsetzungsplan (Summary)

### Phase 1: UI-Integration bestehender Indikatoren (CRITICAL)
**Aufwand:** 12 Stunden
**Dateien:**
- `src/ui/dialogs/entry_analyzer_popup.py` (Indicator List erweitern)
- `src/ui/threads/indicator_optimization_thread.py` (13× Params, Calc, Signals)

**Indikatoren:**
ICHIMOKU, PSAR, KC, VWAP, PIVOTS, CHOP, STOCH, CCI, BB_WIDTH, OBV, MFI, AD, CMF

### Phase 2: Fehlende Technische Indikatoren (HIGH)
**Aufwand:** 12 Stunden
**Dateien:**
- `src/core/indicators/types.py` (5× neue IndicatorType)
- `src/core/indicators/trend.py` (Supertrend, Donchian, Aroon)
- `src/core/indicators/momentum.py` (Vortex)
- `src/core/indicators/custom.py` (Hurst)
- `src/core/indicators/engine.py` (5× Registrierung)

**Indikatoren:**
SUPERTREND, DONCHIAN, AROON, VORTEX, HURST

### Phase 3: Regime-Engine Erweiterung (HIGH)
**Aufwand:** 8 Stunden
**Dateien:**
- `src/core/tradingbot/regime_engine.py` (4× neue Classifier)

**Classifier:**
CHOP, Ichimoku, Donchian, (OBI später)

### Phase 4: Orderflow-Indikatoren (MEDIUM)
**Aufwand:** 16 Stunden
**Dateien:**
- `src/core/indicators/orderflow.py` (neu erstellen)
- `src/core/market_data/bitunix_stream.py` (Orderbook Stream)
- `src/core/indicators/types.py` (OBI, SPREAD, DEPTH)
- `src/core/tradingbot/feature_engine.py` (Orderflow Integration)
- `src/core/tradingbot/regime_engine.py` (OBI-Classifier)

**Indikatoren:**
OBI, SPREAD, DEPTH

---

## ✅ Akzeptanzkriterien

Nach Abschluss aller Phasen:

1. ✅ **Entry Analyzer UI** zeigt alle 28 Indikatoren in Checkbox-Liste
2. ✅ **Indicator Optimization** kann alle 28 Indikatoren mit Parameter-Ranges testen
3. ✅ **Entry/Exit × Long/Short** funktioniert für alle Indikatoren
4. ✅ **Regime-Detection** nutzt alle 6 geforderten Classifier (ADX, CHOP, Ichimoku, BBWidth, Donchian, OBI)
5. ✅ **Composite Regime Engine** priorisiert Regimes gemäß Section 5 (R5 > R3 > R4 > R1 > R2 > R0)
6. ✅ **Orderflow-Features** (OBI, Spread, Depth) verfügbar für R5-Regime
7. ✅ **Results Table** zeigt Scores pro Indikator, Regime, Test Type, Trade Side
8. ✅ **Regime Set Builder** generiert JSON mit allen Indikatoren

---

## 🎯 Finale Empfehlung

**Minimale Implementierung (MVP):**
- ✅ Phase 1 (UI-Integration) - **MUST HAVE**
- ✅ Phase 3 (Regime-Engine) - **MUST HAVE**

→ **Aufwand:** 20 Stunden
→ **Ergebnis:** 20/28 Indikatoren voll nutzbar (71.4% Coverage)

**Vollständige Implementierung:**
- ✅ Phase 1 + Phase 2 + Phase 3 + Phase 4

→ **Aufwand:** 48 Stunden (6 Arbeitstage)
→ **Ergebnis:** 28/28 Indikatoren voll nutzbar (100% Coverage)

**Priorisierung nach Business Value:**
1. Phase 1 (UI) - **HIGHEST** - Sofort nutzbarer Mehrwert
2. Phase 3 (Regime) - **HIGH** - Kernfunktion für Regime-basierte Strategie
3. Phase 2 (Tech Indicators) - **MEDIUM** - Nice-to-have, erweitert Toolset
4. Phase 4 (Orderflow) - **LOW** - Spezialisiert, nur für HFT/Scalping relevant

---

**Erstellt:** 2026-01-19
**Nächste Aktualisierung:** Nach Phase 1 Implementierung
