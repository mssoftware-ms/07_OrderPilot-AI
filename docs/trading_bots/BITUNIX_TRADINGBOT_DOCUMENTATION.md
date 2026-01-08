# Bitunix Crypto Futures Trading Bot - Technische Dokumentation

**Version:** 1.0
**Stand:** Januar 2026
**Lokation:** `src/core/trading_bot/`

---

## 1. Übersicht

Der Bitunix Trading Bot ist ein spezialisierter Bot für den Handel von **Crypto Futures** über die **Bitunix Exchange API**. Er implementiert eine **Confluence-basierte Signalgenerierung** mit optionaler **AI-Validierung** und **client-seitigem SL/TP-Management**.

### Hauptmerkmale

- **Crypto Futures Spezialisierung**: Optimiert für BTC/USDT und andere Crypto-Futures
- **Confluence-basierte Signale**: Mindestens 3 von 5 Bedingungen müssen erfüllt sein
- **Hierarchische AI-Validierung**: Quick → Deep Analysis Flow
- **Client-seitiges SL/TP**: Echtzeit-Überwachung (Bitunix hat keine nativen Stop-Orders)
- **Trailing Stop**: ATR-basiert mit dynamischer Anpassung
- **Multi-Timeframe Analyse**: 1D, 4h, 1h, 5m Integration

---

## 2. Architektur

```
src/core/trading_bot/
├── __init__.py              # Modul-Exports
├── bot_engine.py            # Haupt-Bot-Engine
├── bot_config.py            # Dataclass-basierte Konfiguration
├── signal_generator.py      # Confluence Signal Generator
├── risk_manager.py          # SL/TP & Position Sizing
├── position_monitor.py      # Echtzeit Position Überwachung
├── ai_validator.py          # Hierarchische AI Validierung
├── trade_logger.py          # Trade Logging & Snapshots
└── strategy_config.py       # JSON-basierte Strategie-Konfiguration
```

### Komponenten-Übersicht

```
┌──────────────────────────────────────────────────────────────┐
│                      Bot Engine                               │
│            (Orchestrierung aller Komponenten)                 │
├──────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│ │ Signal Generator │  │   Risk Manager  │  │ AI Validator  │  │
│ │ (Confluence)     │  │  (SL/TP/Sizing) │  │ (Hierarchisch)│  │
│ └────────┬────────┘  └────────┬────────┘  └───────┬───────┘  │
│          │                    │                    │          │
│          ▼                    ▼                    ▼          │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │               Position Monitor                            │ │
│ │      (Echtzeit SL/TP/Trailing Überwachung)                │ │
│ └──────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│                    Bitunix Broker Adapter                     │
│              REST Client + WebSocket Streaming                │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Konfiguration

### 3.1 BotConfig (Dataclass)

```python
@dataclass
class BotConfig:
    # Symbol
    symbol: str = "BTCUSDT"

    # Leverage
    leverage: int = 10

    # Position Sizing
    risk_per_trade_percent: Decimal = Decimal("1.0")   # 1% Risiko pro Trade
    max_position_size_btc: Decimal = Decimal("0.1")    # Max 0.1 BTC

    # Stop Loss / Take Profit (ATR-basiert)
    sl_atr_multiplier: Decimal = Decimal("1.5")
    tp_atr_multiplier: Decimal = Decimal("2.0")

    # Trailing Stop
    trailing_stop_enabled: bool = True
    trailing_stop_atr_multiplier: Decimal = Decimal("1.0")
    trailing_stop_activation_percent: Decimal = Decimal("0.5")  # 0.5% Profit

    # Daily Loss Limit
    max_daily_loss_percent: Decimal = Decimal("3.0")

    # Timeframes
    primary_timeframe: str = "1m"
    analysis_timeframes: list = field(default_factory=lambda: ["1d", "4h", "1h"])
```

### 3.2 StrategyConfig (JSON-basiert)

Die Strategie kann über eine JSON-Datei konfiguriert werden:

```json
{
  "strategy_name": "confluence_btc_futures",
  "version": "1.0",

  "sl_type": "percent_based",
  "tp_type": "percent_based",
  "sl_percent": 0.5,
  "tp_percent": 1.0,
  "sl_atr_multiplier": 1.5,
  "tp_atr_multiplier": 2.0,

  "trailing_stop_type": "atr_based",
  "trailing_stop_percent": 0.3,
  "trailing_stop_atr_multiplier": 1.0,
  "trailing_stop_activation_percent": 0.5,

  "risk_config": {
    "max_position_risk_percent": 1.0,
    "max_daily_loss_percent": 3.0,
    "max_position_size_btc": 0.1,
    "leverage": 10
  }
}
```

---

## 4. Signal Generator

### 4.1 Confluence-Logik

Der SignalGenerator verwendet eine **Confluence-basierte Logik**, bei der mindestens **3 von 5 Bedingungen** erfüllt sein müssen:

```python
class SignalGenerator:
    # Indikator-Parameter
    EMA_SHORT = 20
    EMA_MEDIUM = 50
    EMA_LONG = 200
    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    ADX_THRESHOLD = 20
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
```

### 4.2 LONG Entry-Bedingungen

| # | Bedingung | Beschreibung |
|---|-----------|--------------|
| 1 | **Regime Favorable** | Regime ist nicht STRONG_TREND_BEAR |
| 2 | **EMA Alignment** | Price > EMA20 > EMA50 (bullish alignment) |
| 3 | **RSI Favorable** | RSI zwischen 40-70 (nicht überkauft) |
| 4 | **MACD Bullish** | MACD Linie > Signal Linie |
| 5 | **ADX Trending** | ADX > 20 (Trend vorhanden) |

### 4.3 SHORT Entry-Bedingungen

| # | Bedingung | Beschreibung |
|---|-----------|--------------|
| 1 | **Regime Favorable** | Regime ist nicht STRONG_TREND_BULL |
| 2 | **EMA Alignment** | Price < EMA20 < EMA50 (bearish alignment) |
| 3 | **RSI Favorable** | RSI zwischen 30-60 (nicht überverkauft) |
| 4 | **MACD Bearish** | MACD Linie < Signal Linie |
| 5 | **ADX Trending** | ADX > 20 (Trend vorhanden) |

### 4.4 TradeSignal Dataclass

```python
@dataclass
class TradeSignal:
    direction: SignalDirection      # LONG, SHORT, NEUTRAL
    strength: SignalStrength        # STRONG (5/5), MODERATE (4/5), WEAK (3/5)
    confluence_score: int           # 0-5
    timestamp: datetime

    conditions_met: list[ConditionResult]
    conditions_failed: list[ConditionResult]

    current_price: float | None
    regime: str | None

    # Empfohlene Levels (von RiskManager)
    suggested_entry: float | None
    suggested_sl: float | None
    suggested_tp: float | None

    @property
    def is_valid(self) -> bool:
        return self.confluence_score >= 3 and self.direction != NEUTRAL
```

### 4.5 Signal-Stärken

| Score | Stärke | Bedeutung |
|-------|--------|-----------|
| 5/5 | STRONG | Alle Bedingungen erfüllt |
| 4/5 | MODERATE | Sehr gutes Signal |
| 3/5 | WEAK | Minimum für Trade |
| <3 | NONE | Kein Trade |

---

## 5. Risk Manager

### 5.1 SL/TP Berechnung

Der RiskManager unterstützt zwei Modi:

**Percent-Based**:
```python
def calculate_sl_tp(entry_price, side, sl_percent=0.5, tp_percent=1.0):
    sl_distance = entry_price * (sl_percent / 100)
    tp_distance = entry_price * (tp_percent / 100)

    if side == "BUY":
        stop_loss = entry_price - sl_distance
        take_profit = entry_price + tp_distance
    else:  # SELL
        stop_loss = entry_price + sl_distance
        take_profit = entry_price - tp_distance
```

**ATR-Based**:
```python
def calculate_sl_tp(entry_price, side, atr, sl_mult=1.5, tp_mult=2.0):
    sl_distance = atr * sl_mult
    tp_distance = atr * tp_mult

    if side == "BUY":
        stop_loss = entry_price - sl_distance
        take_profit = entry_price + tp_distance
    else:
        stop_loss = entry_price + sl_distance
        take_profit = entry_price - tp_distance
```

### 5.2 Position Sizing

Risiko-basiertes Position Sizing:

```python
def calculate_position_size(balance, entry_price, stop_loss, risk_percent=1.0):
    # Risiko-Betrag
    risk_amount = balance * (risk_percent / 100)

    # SL-Distanz
    sl_distance = abs(entry_price - stop_loss)

    # Position Size = Risk Amount / SL Distance
    quantity = risk_amount / sl_distance

    # Cap bei max_position_size
    quantity = min(quantity, max_position_size_btc)

    return quantity
```

### 5.3 Vollständige Risiko-Analyse

```python
@dataclass
class RiskCalculation:
    entry_price: Decimal
    side: str

    stop_loss: Decimal
    take_profit: Decimal
    sl_distance: Decimal
    tp_distance: Decimal
    sl_percent: float
    tp_percent: float

    quantity: Decimal
    position_value_usd: Decimal
    risk_amount_usd: Decimal
    risk_percent: float

    atr_value: Decimal
    atr_percent: float

    risk_reward_ratio: float  # z.B. 1.33 (TP/SL)
```

### 5.4 Daily Loss Tracking

```python
def check_daily_loss_limit(balance):
    max_loss = balance * (max_daily_loss_percent / 100)

    if daily_realized_pnl < 0 and abs(daily_realized_pnl) >= max_loss:
        return False, "Daily loss limit reached"

    return True, "OK"
```

---

## 6. Position Monitor

### 6.1 Warum Client-seitiges Monitoring?

**Wichtig:** Bitunix unterstützt keine nativen Stop-Orders. Der PositionMonitor überwacht daher den Preis in Echtzeit und löst Market-Orders zum Schließen aus.

### 6.2 MonitoredPosition

```python
@dataclass
class MonitoredPosition:
    symbol: str
    side: str                      # "BUY" (Long) oder "SELL" (Short)
    entry_price: Decimal
    quantity: Decimal
    entry_time: datetime

    stop_loss: Decimal
    take_profit: Decimal
    initial_stop_loss: Decimal     # Original SL (vor Trailing)

    trailing_enabled: bool
    trailing_activated: bool
    trailing_atr: Decimal | None

    current_price: Decimal | None
    unrealized_pnl: Decimal
    unrealized_pnl_percent: float

    highest_price: Decimal | None  # Für Long Trailing
    lowest_price: Decimal | None   # Für Short Trailing
```

### 6.3 Exit-Trigger

```python
class ExitTrigger(str, Enum):
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    SIGNAL_EXIT = "SIGNAL_EXIT"
    MANUAL = "MANUAL"
    SESSION_END = "SESSION_END"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    BOT_STOPPED = "BOT_STOPPED"
```

### 6.4 Exit-Logik

```python
async def on_price_update(price):
    position.update_price(price)

    # Stop Loss Check
    if side == "BUY" and price <= stop_loss:
        return ExitResult(should_exit=True, trigger=STOP_LOSS)
    elif side == "SELL" and price >= stop_loss:
        return ExitResult(should_exit=True, trigger=STOP_LOSS)

    # Take Profit Check
    if side == "BUY" and price >= take_profit:
        return ExitResult(should_exit=True, trigger=TAKE_PROFIT)
    elif side == "SELL" and price <= take_profit:
        return ExitResult(should_exit=True, trigger=TAKE_PROFIT)

    # Trailing Stop Update
    if trailing_enabled:
        update_trailing_stop(price)

    return None
```

### 6.5 Trailing Stop Logik

```python
def adjust_sl_for_trailing(current_price, current_sl, entry_price, side, atr):
    # Aktivierungsschwelle prüfen
    if side == "BUY":
        profit_percent = (current_price - entry_price) / entry_price * 100
    else:
        profit_percent = (entry_price - current_price) / entry_price * 100

    if profit_percent < activation_percent:
        return current_sl, False  # Nicht aktiviert

    # Neue SL berechnen
    trailing_distance = atr * trailing_atr_multiplier

    if side == "BUY":
        new_sl = current_price - trailing_distance
        if new_sl > current_sl:  # SL darf nur steigen
            return new_sl, True
    else:
        new_sl = current_price + trailing_distance
        if new_sl < current_sl:  # SL darf nur sinken
            return new_sl, True

    return current_sl, False
```

---

## 7. AI Validator (Hierarchische Validierung)

### 7.1 Validierungsstufen

```python
class ValidationLevel(str, Enum):
    QUICK = "quick"       # Schnelle Validierung
    DEEP = "deep"         # Tiefe Analyse
    TECHNICAL = "technical"  # Nur technisch (Fallback)
    BYPASS = "bypass"     # AI deaktiviert
```

### 7.2 Hierarchischer Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  Signal (Confluence >= 3)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Quick AI Validation                             │
│         (Model aus QSettings, schnelle Analyse)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
     Confidence           Confidence      Confidence
       >= 70%           50% - 70%          < 50%
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌─────────────┐   ┌───────────┐
    │  TRADE   │    │Deep Analysis│   │   SKIP    │
    │ APPROVED │    │  (detailiert)│   │  Signal   │
    └──────────┘    └──────┬──────┘   └───────────┘
                           │
                   ┌───────┴───────┐
                   │               │
             Confidence >= 70   < 70
                   │               │
                   ▼               ▼
            ┌──────────┐    ┌───────────┐
            │  TRADE   │    │  REJECT   │
            │ APPROVED │    │   Trade   │
            └──────────┘    └───────────┘
```

### 7.3 AI Provider

Unterstützte Provider (Einstellung über QSettings):

| Provider | Modelle |
|----------|---------|
| **OpenAI** | gpt-5.2, gpt-5.1, gpt-4.1, gpt-4.1-mini |
| **Anthropic** | claude-sonnet-4-5, claude-sonnet-4-5-20250929 |
| **Gemini** | gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash |

### 7.4 AIValidation Response

```python
@dataclass
class AIValidation:
    approved: bool
    confidence_score: int           # 0-100
    setup_type: str | None          # z.B. "PULLBACK_EMA20"
    reasoning: str
    provider: str
    model: str
    timestamp: datetime
    validation_level: ValidationLevel
    deep_analysis_triggered: bool
    error: str | None
```

### 7.5 Erkannte Setup-Typen

- PULLBACK_EMA20
- PULLBACK_EMA50
- BREAKOUT
- BREAKDOWN
- MEAN_REVERSION
- TREND_CONTINUATION
- SWING_FAILURE
- ABSORPTION
- DIVERGENCE
- NO_SETUP

---

## 8. Bot Engine

### 8.1 Hauptkomponenten-Integration

```python
class BotEngine:
    def __init__(self, config: BotConfig):
        self.config = config
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager(config)
        self.position_monitor = PositionMonitor(risk_manager)
        self.ai_validator = AISignalValidator()
        self.trade_logger = TradeLogger()
```

### 8.2 Haupt-Trading-Loop

```python
async def run_trading_cycle(df: pd.DataFrame, current_price: Decimal):
    # 1. Prüfe bestehende Position
    if position_monitor.has_position:
        exit_result = await position_monitor.on_price_update(current_price)
        if exit_result and exit_result.should_exit:
            await close_position(exit_result)
            return

    # 2. Generiere Signal
    signal = signal_generator.generate_signal(df, regime)

    if not signal.is_valid:
        return

    # 3. AI Validierung (optional)
    if ai_validator.enabled:
        ai_result = await ai_validator.validate_signal_hierarchical(
            signal, indicators, market_context, df
        )
        if not ai_result.approved:
            logger.info(f"AI rejected signal: {ai_result.reasoning}")
            return

    # 4. Risiko-Berechnung
    risk_calc = risk_manager.calculate_full_risk(
        balance, current_price, signal.direction.value, atr
    )

    # 5. Trade Validierung
    is_valid, reason, risk = risk_manager.validate_trade(
        balance, current_price, signal.direction.value, atr
    )

    if not is_valid:
        logger.warning(f"Trade rejected: {reason}")
        return

    # 6. Order ausführen
    await execute_entry(signal, risk_calc)
```

---

## 9. Trade Logging

### 9.1 IndicatorSnapshot

```python
@dataclass
class IndicatorSnapshot:
    timestamp: datetime

    # EMAs
    ema_20: float | None
    ema_50: float | None
    ema_200: float | None
    ema_20_distance_pct: float | None

    # RSI
    rsi_14: float | None
    rsi_state: str | None  # OVERBOUGHT, OVERSOLD, NEUTRAL

    # MACD
    macd_line: float | None
    macd_signal: float | None
    macd_histogram: float | None
    macd_crossover: str | None  # BULLISH, BEARISH

    # Bollinger Bands
    bb_upper, bb_middle, bb_lower: float | None
    bb_pct_b: float | None
    bb_width: float | None

    # ATR
    atr_14: float | None
    atr_percent: float | None

    # ADX
    adx_14: float | None
    plus_di, minus_di: float | None

    # Volume
    volume: float | None
    volume_sma_20: float | None
    volume_ratio: float | None

    current_price: float | None
```

### 9.2 Trade Log Entry

Jeder Trade wird mit vollständigem Kontext geloggt:
- Entry/Exit Preise und Zeiten
- Alle Indikatoren bei Entry und Exit
- AI Validierung Details
- Trailing Stop Historie
- Realized PnL

---

## 10. Vergleich: Bitunix Bot vs Alpaca Bot

| Feature | Bitunix Bot | Alpaca Bot |
|---------|-------------|------------|
| **Markt** | Crypto Futures | Crypto + NASDAQ |
| **Architektur** | Dataclass + JSON Config | Pydantic Models |
| **Signale** | Confluence (3/5) | Score-based (0-1) |
| **AI Integration** | Hierarchisch (Quick→Deep) | Optional (3 Modi) |
| **SL/TP** | Client-seitig | Native Orders |
| **Trailing** | ATR-basiert | PCT/ATR/SWING |
| **Leverage** | Ja (bis 125x) | Nein (Spot) |
| **Regime** | Extern | Integriert |
| **Logging** | Indicator Snapshots | Decision Logging |

---

## 11. Verwendung

### Bot starten

```python
from src.core.trading_bot import BotEngine, BotConfig

# Konfiguration
config = BotConfig(
    symbol="BTCUSDT",
    leverage=10,
    risk_per_trade_percent=Decimal("1.0"),
    trailing_stop_enabled=True
)

# Engine erstellen
engine = BotEngine(config)

# Starten
await engine.start()
```

### Konfiguration zur Laufzeit ändern

```python
# Risk Manager aktualisieren
engine.risk_manager.update_config(new_config)

# AI Validator konfigurieren
engine.ai_validator.update_config(
    enabled=True,
    confidence_threshold_trade=70,
    confidence_threshold_deep=50
)
```

### Strategie aus JSON laden

```python
from src.core.trading_bot import StrategyConfig

strategy = StrategyConfig.load_from_file("config/strategies/btc_trend.json")
engine.risk_manager.update_strategy_config(strategy)
```

---

## 12. Sicherheitsfeatures

1. **Daily Loss Limit**: Automatischer Trading-Stop bei Erreichen
2. **Client-Side SL/TP**: Garantierte Überwachung (nicht von Exchange abhängig)
3. **AI Rejection**: Unsichere Signale werden abgelehnt
4. **Risk Validation**: Jeder Trade wird vor Ausführung validiert
5. **Trailing Stop**: Nie-Loosen-Invariante (SL kann nur in Gewinnrichtung wandern)
6. **Position Persistence**: Positionen werden serialisiert für Crash-Recovery

---

## 13. Bekannte Limitierungen

1. **Single Position**: Nur eine Position gleichzeitig
2. **No Partial Exits**: Immer volle Position schließen
3. **Latency Sensitivity**: Client-seitiges SL/TP abhängig von Verbindung
4. **AI Kosten**: Deep Analysis erhöht API-Kosten

---

## 14. Troubleshooting

### Signal wird nicht generiert
- Prüfe Confluence Score (minimum 3/5)
- Prüfe Regime-Alignment
- Prüfe ob genug Daten (min. 200 Bars für EMA200)

### AI lehnt ab
- Prüfe Confidence Thresholds
- Prüfe API Key Konfiguration
- Prüfe Model-Verfügbarkeit

### SL/TP wird nicht getriggert
- Prüfe ob PositionMonitor läuft
- Prüfe WebSocket-Verbindung
- Prüfe Preis-Update Interval

---

*Dokumentation erstellt vom Hive Mind System | Januar 2026*
