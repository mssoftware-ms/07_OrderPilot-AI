# Alpaca Trading Bot (BotController) - Technische Dokumentation

**Version:** 1.0
**Stand:** Januar 2026
**Lokation:** `src/core/tradingbot/`

---

## 1. Übersicht

Der Alpaca Trading Bot (auch "BotController" genannt) ist ein regelbasierter Trading Bot für den Handel über die **Alpaca Trading API**. Er unterstützt sowohl **Crypto** als auch **NASDAQ/Aktien** Märkte und kann optional mit **KI-Unterstützung** (LLM-basiert) betrieben werden.

### Hauptmerkmale

- **Multi-Market Support**: Crypto (BTC/USD, ETH/USD) und NASDAQ (AAPL, TSLA, etc.)
- **Drei KI-Modi**: NO_KI (rein regelbasiert), LOW_KI (täglich), FULL_KI (kontinuierlich)
- **Pydantic-basierte Konfiguration**: Typsichere, validierte Einstellungen
- **Trailing Stop Management**: PCT, ATR und SWING Modi
- **Regime-Erkennung**: Automatische Marktphasen-Erkennung
- **Paper/Live Trading**: Sicherer Switch zwischen Umgebungen

---

## 2. Architektur

```
src/core/tradingbot/
├── __init__.py
├── bot_controller.py    # Hauptsteuerung des Bots
├── config.py            # Pydantic Konfigurationsmodelle
├── models.py            # Domain Models (Signals, Positions, etc.)
├── indicators.py        # Technische Indikatoren
├── strategies/          # Handelsstrategien
│   ├── base.py
│   ├── trend_following.py
│   └── mean_reversion.py
└── utils/               # Hilfsfunktionen
```

### Schichtenmodell

```
┌─────────────────────────────────────────────────────┐
│                    UI Layer                          │
│              (PyQt6 Trading Tabs)                    │
├─────────────────────────────────────────────────────┤
│                 BotController                        │
│         (Orchestrierung & Entscheidungen)            │
├─────────────────────────────────────────────────────┤
│     ┌─────────────┐  ┌──────────────┐  ┌─────────┐  │
│     │  Strategies │  │   Indicators │  │ Models  │  │
│     └─────────────┘  └──────────────┘  └─────────┘  │
├─────────────────────────────────────────────────────┤
│              Broker Adapter (Alpaca)                 │
│      REST Client + WebSocket Streaming               │
└─────────────────────────────────────────────────────┘
```

---

## 3. Konfiguration

### 3.1 BotConfig

Die Hauptkonfiguration des Bots:

```python
class BotConfig(BaseModel):
    # Market Settings
    market_type: MarketType         # CRYPTO oder NASDAQ
    symbol: str                     # z.B. "BTC/USD", "AAPL"
    timeframe: str                  # z.B. "1m", "5m", "1h"

    # Umgebung
    environment: TradingEnvironment # PAPER oder LIVE

    # KI-Modus
    ki_mode: KIMode                 # NO_KI, LOW_KI, FULL_KI

    # Trailing Stop
    trailing_mode: TrailingMode     # PCT, ATR, SWING

    # Feature Flags
    daily_strategy_selection: bool  # Tägliche Strategie-Auswahl
    auto_trade: bool                # Automatische Ausführung
    entry_score_threshold: float    # Min. Score für Entry (0-1)
```

### 3.2 RiskConfig

Risikomanagement-Einstellungen:

```python
class RiskConfig(BaseModel):
    # Position Sizing
    risk_per_trade_pct: float      # Risiko pro Trade (% des Kontos)
    max_position_size_pct: float   # Max Position (% des Kontos)

    # Stop-Loss
    initial_stop_loss_pct: float   # Initialer SL in %

    # Trailing Stop Parameter
    trailing_activation_pct: float # Min. Profit für Aktivierung
    trailing_pct_distance: float   # Trailing-Distanz (PCT Modus)
    trailing_atr_multiple: float   # ATR-Multiplikator (ATR Modus)

    # Regime-Adaptive Trailing
    regime_adaptive_trailing: bool
    trailing_atr_trending: float   # ATR für Trending Märkte
    trailing_atr_ranging: float    # ATR für Ranging Märkte

    # Limits
    max_trades_per_day: int
    max_daily_loss_pct: float      # Kill-Switch
    loss_streak_cooldown: int      # Pause nach N Verlusten
```

### 3.3 LLMPolicyConfig

KI-Integration (optional):

```python
class LLMPolicyConfig(BaseModel):
    # Call Triggers (für FULL_KI)
    call_on_regime_flip: bool      # LLM bei Regime-Wechsel
    call_on_exit_candidate: bool   # LLM bei Exit-Signal
    call_on_signal_change: bool    # LLM bei neuen Signalen

    # Modell-Settings (aus QSettings geladen)
    temperature: float             # 0.1 für deterministische Ausgaben
    max_tokens: int                # Max. Response-Tokens

    # Fallback
    fallback_on_failure: bool      # Regelbasiert bei LLM-Fehler
```

---

## 4. Domain Models

### 4.1 FeatureVector

Enthält alle Indikatorwerte für Entscheidungen:

```python
class FeatureVector(BaseModel):
    timestamp: datetime
    symbol: str

    # Preisdaten
    open, high, low, close, volume: float

    # Trend-Indikatoren
    sma_20, sma_50: float
    ema_12, ema_26: float
    ma_slope_20: float

    # Momentum-Indikatoren
    rsi_14: float (0-100)
    macd, macd_signal, macd_hist: float
    stoch_k, stoch_d: float (0-100)

    # Volatilitäts-Indikatoren
    atr_14: float
    bb_upper, bb_middle, bb_lower: float
    bb_width, bb_pct: float

    # Trendstärke
    adx, plus_di, minus_di: float
```

### 4.2 RegimeState

Marktzustand-Klassifizierung:

```python
class RegimeType(str, Enum):
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    RANGE = "range"
    UNKNOWN = "unknown"

class VolatilityLevel(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"
```

### 4.3 Signal

Trading-Signal mit Entry-Details:

```python
class Signal(BaseModel):
    id: str
    timestamp: datetime
    symbol: str

    signal_type: SignalType        # CANDIDATE oder CONFIRMED
    side: TradeSide                # LONG, SHORT, NONE
    score: float                   # Entry-Score (0-1)

    entry_price: float
    stop_loss_price: float
    stop_loss_pct: float

    regime: RegimeType
    strategy_name: str
    reason_codes: list[str]
```

### 4.4 PositionState

Offene Position mit Trailing:

```python
class PositionState(BaseModel):
    id: str
    symbol: str
    side: TradeSide

    # Entry
    entry_time: datetime
    entry_price: float
    quantity: float

    # Aktuell
    current_price: float
    trailing: TrailingState

    # P&L
    unrealized_pnl: float
    unrealized_pnl_pct: float
    max_favorable_excursion: float
    max_adverse_excursion: float
```

---

## 5. Funktionsweise

### 5.1 Bot-Lifecycle

```
┌──────────────┐
│   STOPPED    │◄────────────────────────┐
└──────┬───────┘                         │
       │ start()                         │ stop()
       ▼                                 │
┌──────────────┐                         │
│  INITIALIZING│──────────────────────┐  │
└──────┬───────┘                      │  │
       │ erfolg                       │  │
       ▼                              │  │
┌──────────────┐                      │  │
│   RUNNING    │◄─────┐               │  │
└──────┬───────┘      │               │  │
       │              │ kein Exit     │  │
       ▼              │               │  │
┌──────────────┐      │               │  │
│ CHECKING     │──────┘               │  │
│ CONDITIONS   │                      │  │
└──────┬───────┘                      │  │
       │ Signal!                      │  │
       ▼                              │  │
┌──────────────┐                      │  │
│  IN_POSITION │──────────────────────┘  │
└──────────────┘                         │
       │ Exit                            │
       └─────────────────────────────────┘
```

### 5.2 Entscheidungslogik

1. **Feature Extraction**: Sammeln aller Indikatordaten
2. **Regime Detection**: Klassifizierung des Marktzustands
3. **Strategy Selection**: Auswahl der passenden Strategie
4. **Signal Generation**: Generierung von Entry/Exit Signalen
5. **LLM Validation** (optional): KI-Validierung bei LOW_KI/FULL_KI
6. **Risk Check**: Prüfung aller Risk-Limits
7. **Order Execution**: Ausführung über Alpaca API

### 5.3 Entry-Score Berechnung

Der Entry-Score (0-1) basiert auf:

```python
score = weighted_average([
    rsi_score * 0.2,           # RSI in günstiger Zone
    macd_score * 0.2,          # MACD-Momentum positiv
    trend_alignment * 0.25,    # Preis vs. MAs
    volatility_score * 0.15,   # BB-Position
    volume_score * 0.1,        # Volume Bestätigung
    regime_match * 0.1         # Regime passt zur Strategie
])
```

### 5.4 Trailing Stop Modi

**PCT (Prozent-basiert)**:
```python
# Trailing-Distanz = x% vom Preis
new_stop = current_price * (1 - trailing_pct / 100)  # Long
new_stop = current_price * (1 + trailing_pct / 100)  # Short
```

**ATR (Volatilitäts-basiert)**:
```python
# Trailing-Distanz = ATR * Multiplikator
trailing_distance = atr_14 * trailing_atr_multiple
new_stop = current_price - trailing_distance  # Long
```

**Regime-Adaptive ATR**:
```python
if regime.is_trending:
    atr_mult = trailing_atr_trending  # z.B. 2.0 (tighter)
else:
    atr_mult = trailing_atr_ranging   # z.B. 3.5 (wider)

if volatility == HIGH:
    atr_mult += trailing_volatility_bonus
```

---

## 6. KI-Modi im Detail

### 6.1 NO_KI Modus

- Rein regelbasierte Entscheidungen
- Keine LLM-API-Calls
- Schnellste Ausführung
- Verwendung: Backtesting, Performance-Tests

### 6.2 LOW_KI Modus

- **Einmal täglich**: LLM wählt Tagesstrategie
- Prompt enthält: Regime, Volatilität, letzte Performance
- LLM gibt zurück: Strategie-Empfehlung, Parameter-Anpassungen
- Verwendung: Ressourcenschonende KI-Unterstützung

### 6.3 FULL_KI Modus

LLM-Calls bei:
- **Regime Flip**: Marktphase wechselt
- **Exit Candidate**: Signal deutet auf Exit hin
- **Signal Change**: Neues Entry-Signal erscheint

```python
class LLMBotResponse(BaseModel):
    action: BotAction          # NO_TRADE, ENTER, HOLD, EXIT
    side: TradeSide
    confidence: float          # 0-1
    reason_codes: list[str]
    entry: dict | None         # {ok: bool, price_hint: float}
    stop: dict | None          # {mode: str, new_stop_price: float}
```

---

## 7. Broker-Integration (Alpaca)

### 7.1 REST Client

```python
# Order Execution
await alpaca_client.create_order(
    symbol="BTC/USD",
    side="buy",
    qty=0.01,
    type="market",
    time_in_force="gtc"
)

# Position Query
positions = await alpaca_client.get_positions()

# Account Info
account = await alpaca_client.get_account()
```

### 7.2 WebSocket Streaming

```python
# Market Data Stream
async for quote in alpaca_ws.subscribe_quotes(["BTC/USD"]):
    process_quote(quote)

# Trade Updates
async for update in alpaca_ws.subscribe_trade_updates():
    handle_fill(update)
```

---

## 8. Markt-spezifische Unterschiede

### Crypto (market_type = CRYPTO)

| Parameter | Wert |
|-----------|------|
| initial_stop_loss_pct | 3.0% |
| trailing_pct_distance | 2.0% |
| trailing_atr_multiple | 2.5x |
| expected_slippage_pct | 0.1% |
| commission_pct | 0.1% |
| trading_hours | 24/7 |

### NASDAQ (market_type = NASDAQ)

| Parameter | Wert |
|-----------|------|
| initial_stop_loss_pct | 1.5% |
| trailing_pct_distance | 1.0% |
| trailing_atr_multiple | 1.5x |
| expected_slippage_pct | 0.02% |
| commission_pct | 0.0% |
| trading_hours | 9:30-16:00 ET |

---

## 9. Strategie-Profile

Jede Strategie definiert:

```python
class StrategyProfile(BaseModel):
    name: str                      # z.B. "trend_following_v2"
    description: str

    # Anwendbare Bedingungen
    regimes: list[RegimeType]      # z.B. [TREND_UP, TREND_DOWN]
    volatility_levels: list[VolatilityLevel]

    # Parameter
    entry_threshold: float         # Min. Score für Entry
    trailing_mode: TrailingMode
    trailing_multiplier: float

    # Historische Performance
    win_rate: float
    profit_factor: float
    expectancy: float
```

---

## 10. Logging & Audit

### Decision Logging

Jede Entscheidung wird protokolliert:

```python
class BotDecision(BaseModel):
    id: str
    timestamp: datetime
    symbol: str
    action: BotAction
    side: TradeSide
    confidence: float

    features_hash: str             # Audit-Trail
    regime: RegimeType
    strategy_name: str

    reason_codes: list[str]
    source: "rule_based" | "llm" | "manual"
    llm_response_id: str | None
```

### Performance Metrics

- Win Rate
- Profit Factor
- Max Drawdown
- Sharpe Ratio
- Trade Duration Average
- Slippage Analysis

---

## 11. Sicherheitsfeatures

1. **Paper-First**: Standard ist immer Paper-Trading
2. **Daily Loss Limit**: Kill-Switch bei max_daily_loss_pct
3. **Loss Streak Cooldown**: Pause nach Verlustserie
4. **Max Position Limits**: Absolute Positionsgrößen-Limits
5. **LLM Fallback**: Regelbasiert bei API-Fehlern
6. **Feature Hashing**: Audit-Trail für Reproduzierbarkeit

---

## 12. Verwendung

### Initialisierung

```python
from src.core.tradingbot.config import FullBotConfig, MarketType
from src.core.tradingbot.bot_controller import BotController

# Konfiguration erstellen
config = FullBotConfig.create_default(
    symbol="BTC/USD",
    market_type=MarketType.CRYPTO
)

# Bot starten
controller = BotController(config)
await controller.start()
```

### Konfiguration ändern

```python
# Zur Laufzeit
controller.update_config(
    auto_trade=True,
    entry_score_threshold=0.7
)

# KI-Modus wechseln
controller.set_ki_mode(KIMode.FULL_KI)
```

---

## 13. Bekannte Limitierungen

1. **Single Position**: Aktuell nur eine Position pro Symbol gleichzeitig
2. **No Hedging**: Kein gleichzeitiges Long/Short
3. **Market Orders**: Primär Market Orders, Limit Orders in Entwicklung
4. **Backtesting**: Separates Modul erforderlich

---

*Dokumentation erstellt vom Hive Mind System | Januar 2026*
