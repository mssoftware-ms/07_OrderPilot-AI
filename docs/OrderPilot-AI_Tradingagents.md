# OrderPilot-AI Trading Agents - Vollständige Dokumentation

**Version:** 1.0.0
**Stand:** Januar 2026
**Projekt:** OrderPilot-AI

---

## Inhaltsverzeichnis

1. [Einführung](#1-einführung)
2. [Systemarchitektur](#2-systemarchitektur)
3. [Alpaca Trading Bot (BotController)](#3-alpaca-trading-bot-botcontroller)
4. [Bitunix Crypto Futures Bot (BotEngine)](#4-bitunix-crypto-futures-bot-botengine)
5. [Signalgenerierung](#5-signalgenerierung)
6. [Risk Management](#6-risk-management)
7. [AI/KI-Integration](#7-aiki-integration)
8. [Position Monitoring](#8-position-monitoring)
9. [Konfiguration](#9-konfiguration)
10. [Vergleich der Trading Agents](#10-vergleich-der-trading-agents)
11. [API-Integration](#11-api-integration)
12. [Sicherheit & Best Practices](#12-sicherheit--best-practices)
13. [Troubleshooting](#13-troubleshooting)
14. [Glossar](#14-glossar)

---

## 1. Einführung

### 1.1 Was ist OrderPilot-AI?

OrderPilot-AI ist eine Python-basierte Trading-Plattform, die zwei spezialisierte Trading Agents implementiert:

1. **Alpaca Trading Bot** - Für Crypto und NASDAQ/Aktien über die Alpaca API
2. **Bitunix Trading Bot** - Für Crypto Futures über die Bitunix Exchange

Beide Agents verwenden technische Analyse, regelbasierte Entscheidungen und optionale KI-Validierung für Trading-Entscheidungen.

### 1.2 Designprinzipien

- **Safety First**: Paper-Trading als Standard, Live-Trading nur explizit
- **Modulare Architektur**: Klare Trennung von Signalgenerierung, Risikomanagement und Ausführung
- **Konfigurierbarkeit**: Alle Parameter über Config-Dateien oder UI anpassbar
- **Transparenz**: Vollständiges Logging aller Entscheidungen für Audit-Trail
- **Optional AI**: KI-Validierung kann aktiviert oder deaktiviert werden

### 1.3 Technologie-Stack

| Komponente | Technologie |
|------------|-------------|
| Sprache | Python 3.11+ |
| UI Framework | PyQt6 |
| Datenmodelle | Pydantic / Dataclasses |
| Async | asyncio |
| Indikatoren | pandas, ta-lib |
| AI Provider | OpenAI, Anthropic, Google Gemini |

---

## 2. Systemarchitektur

### 2.1 Gesamtübersicht

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           OrderPilot-AI                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐     │
│  │     Alpaca Trading Bot      │    │   Bitunix Trading Bot       │     │
│  │    (src/core/tradingbot/)   │    │  (src/core/trading_bot/)    │     │
│  ├─────────────────────────────┤    ├─────────────────────────────┤     │
│  │ • BotController             │    │ • BotEngine                 │     │
│  │ • Score-based Signals       │    │ • Confluence Signals        │     │
│  │ • 3 KI-Modi                 │    │ • Hierarchische AI          │     │
│  │ • Native SL/TP              │    │ • Client-side SL/TP         │     │
│  │ • Crypto + NASDAQ           │    │ • Crypto Futures only       │     │
│  └──────────────┬──────────────┘    └──────────────┬──────────────┘     │
│                 │                                   │                    │
│  ┌──────────────┴───────────────────────────────────┴──────────────┐    │
│  │                     Shared Components                            │    │
│  ├──────────────────────────────────────────────────────────────────┤    │
│  │  • Technical Indicators    • Risk Calculations                   │    │
│  │  • Market Data Streaming   • Trade Logging                       │    │
│  │  • AI Provider Abstraction • Configuration Management            │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │                      Broker Adapters                              │    │
│  ├─────────────────────────────┬────────────────────────────────────┤    │
│  │     Alpaca Adapter          │       Bitunix Adapter              │    │
│  │  • REST API Client          │    • REST API Client               │    │
│  │  • WebSocket Streaming      │    • WebSocket Streaming           │    │
│  │  • Native Order Types       │    • Futures Order Types           │    │
│  └─────────────────────────────┴────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Verzeichnisstruktur

```
src/
├── core/
│   ├── tradingbot/                    # Alpaca Trading Bot
│   │   ├── __init__.py
│   │   ├── bot_controller.py          # Hauptsteuerung
│   │   ├── config.py                  # Pydantic Konfiguration
│   │   ├── models.py                  # Domain Models
│   │   ├── indicators.py              # Technische Indikatoren
│   │   └── strategies/                # Handelsstrategien
│   │
│   ├── trading_bot/                   # Bitunix Trading Bot
│   │   ├── __init__.py
│   │   ├── bot_engine.py              # Haupt-Engine
│   │   ├── bot_config.py              # Dataclass Konfiguration
│   │   ├── signal_generator.py        # Confluence Signale
│   │   ├── risk_manager.py            # SL/TP/Sizing
│   │   ├── position_monitor.py        # Echtzeit-Überwachung
│   │   ├── ai_validator.py            # Hierarchische AI
│   │   ├── trade_logger.py            # Logging
│   │   └── strategy_config.py         # JSON-Strategie
│   │
│   └── broker/                        # Broker Abstraktion
│       ├── base.py
│       ├── alpaca/
│       └── bitunix/
│
├── ui/
│   └── widgets/
│       ├── alpaca_trading/            # Alpaca UI
│       └── bitunix_trading/           # Bitunix UI
│
└── config/
    └── trading_bot/
        └── strategy_config.json       # Strategie-Konfiguration
```

### 2.3 Datenfluss

```
                    ┌─────────────┐
                    │ Market Data │
                    │  (Stream)   │
                    └──────┬──────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    OHLCV DataFrame                            │
│          (open, high, low, close, volume + indicators)        │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                   Signal Generator                            │
│         (Confluence / Score-based Analysis)                   │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    AI Validator (optional)                    │
│              (Quick → Deep Analysis Flow)                     │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     Risk Manager                              │
│          (Position Sizing, SL/TP Calculation)                 │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Order Execution                            │
│               (via Broker Adapter)                            │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                   Position Monitor                            │
│         (Real-time SL/TP/Trailing Surveillance)               │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Alpaca Trading Bot (BotController)

### 3.1 Übersicht

| Eigenschaft | Wert |
|-------------|------|
| **Lokation** | `src/core/tradingbot/` |
| **Hauptklasse** | `BotController` |
| **Märkte** | Crypto, NASDAQ/Aktien |
| **Konfiguration** | Pydantic Models |
| **SL/TP** | Native Alpaca Orders |

### 3.2 Unterstützte Märkte

#### Crypto
- BTC/USD, ETH/USD, SOL/USD, etc.
- 24/7 Trading
- Höhere Volatilität, entsprechend angepasste Parameter

#### NASDAQ/Aktien
- AAPL, TSLA, NVDA, etc.
- Market Hours: 9:30-16:00 ET
- Geringere Volatilität, engere Stops

### 3.3 KI-Modi

```python
class KIMode(str, Enum):
    NO_KI = "no_ki"      # Rein regelbasiert
    LOW_KI = "low_ki"    # 1x täglich (Strategie-Auswahl)
    FULL_KI = "full_ki"  # Kontinuierlich (Events)
```

#### NO_KI Modus
- Keine LLM-API-Aufrufe
- Rein technische Analyse
- Schnellste Ausführung
- Ideal für Backtesting

#### LOW_KI Modus
- **Ein Aufruf pro Tag** zur Strategie-Auswahl
- LLM analysiert: Regime, Volatilität, letzte Performance
- Gibt Empfehlung für Tagesstrategie
- Ressourcenschonend

#### FULL_KI Modus
LLM wird aufgerufen bei:
- **Regime Flip**: Marktphase wechselt
- **Exit Candidate**: Potentielles Exit-Signal
- **Signal Change**: Neues Entry-Signal

### 3.4 Entry-Score System

Der Alpaca Bot verwendet ein Score-System (0-1):

```python
def calculate_entry_score(features: FeatureVector) -> float:
    components = [
        rsi_score * 0.20,        # RSI in günstiger Zone
        macd_score * 0.20,       # MACD-Momentum
        trend_alignment * 0.25,  # Preis vs. MAs
        volatility_score * 0.15, # BB-Position
        volume_score * 0.10,     # Volume Confirmation
        regime_match * 0.10      # Regime passt
    ]
    return sum(components)

# Trade nur wenn: score >= entry_score_threshold (default: 0.6)
```

### 3.5 Trailing Stop Modi

```python
class TrailingMode(str, Enum):
    PCT = "pct"      # Prozent-basiert
    ATR = "atr"      # ATR-basiert
    SWING = "swing"  # Struktur-basiert
```

#### PCT Modus
```python
# Feste Prozent-Distanz
trailing_distance = current_price * trailing_pct_distance / 100
```

#### ATR Modus
```python
# Volatilitätsbasiert
trailing_distance = atr_14 * trailing_atr_multiple
```

#### Regime-Adaptive ATR
```python
if regime.is_trending:
    atr_mult = trailing_atr_trending   # 2.0 (tighter)
else:
    atr_mult = trailing_atr_ranging    # 3.5 (wider)

if volatility == HIGH:
    atr_mult += trailing_volatility_bonus  # +0.5
```

### 3.6 Strategie-Profile

```python
class StrategyProfile(BaseModel):
    name: str                          # z.B. "trend_following_v2"
    regimes: list[RegimeType]          # [TREND_UP, TREND_DOWN]
    volatility_levels: list[VolatilityLevel]
    entry_threshold: float             # 0.6
    trailing_mode: TrailingMode        # ATR
    trailing_multiplier: float         # 1.0

    # Performance
    win_rate: float
    profit_factor: float
    expectancy: float
```

### 3.7 Konfiguration

```python
class FullBotConfig(BaseModel):
    bot: BotConfig           # Markt, Symbol, Timeframe
    risk: RiskConfig         # Position Sizing, Limits
    llm_policy: LLMPolicyConfig  # KI-Einstellungen
```

---

## 4. Bitunix Crypto Futures Bot (BotEngine)

### 4.1 Übersicht

| Eigenschaft | Wert |
|-------------|------|
| **Lokation** | `src/core/trading_bot/` |
| **Hauptklasse** | `BotEngine` |
| **Märkte** | Crypto Futures (BTCUSDT, etc.) |
| **Konfiguration** | Dataclass + JSON |
| **SL/TP** | Client-seitig (Echtzeit-Monitor) |
| **Leverage** | Bis 125x |

### 4.2 Warum Client-seitiges SL/TP?

**Wichtig:** Bitunix unterstützt keine nativen Stop-Orders für Futures. Der Bot implementiert daher:

1. **PositionMonitor**: Überwacht Preis in Echtzeit
2. **Exit-Trigger**: Bei SL/TP-Berührung wird Market-Order gesendet
3. **Trailing Stop**: Dynamische SL-Anpassung im Profit

### 4.3 Confluence-basierte Signale

Der Bitunix Bot verwendet **Confluence-Logik** (min. 3/5 Bedingungen):

#### LONG Entry-Bedingungen

| # | Bedingung | Beschreibung |
|---|-----------|--------------|
| 1 | Regime Favorable | Nicht STRONG_TREND_BEAR |
| 2 | EMA Alignment | Price > EMA20 > EMA50 |
| 3 | RSI Favorable | RSI zwischen 40-70 |
| 4 | MACD Bullish | MACD > Signal Line |
| 5 | ADX Trending | ADX > 20 |

#### SHORT Entry-Bedingungen

| # | Bedingung | Beschreibung |
|---|-----------|--------------|
| 1 | Regime Favorable | Nicht STRONG_TREND_BULL |
| 2 | EMA Alignment | Price < EMA20 < EMA50 |
| 3 | RSI Favorable | RSI zwischen 30-60 |
| 4 | MACD Bearish | MACD < Signal Line |
| 5 | ADX Trending | ADX > 20 |

### 4.4 Signal-Stärken

| Confluence Score | Stärke | Empfehlung |
|------------------|--------|------------|
| 5/5 | STRONG | Trade mit vollem Size |
| 4/5 | MODERATE | Trade mit normalem Size |
| 3/5 | WEAK | Trade mit reduziertem Size |
| <3/5 | NONE | Kein Trade |

### 4.5 Hierarchische AI-Validierung

```
Signal (Confluence >= 3)
         │
         ▼
┌─────────────────────┐
│  Quick AI Analysis  │  ← Model aus QSettings
└──────────┬──────────┘
           │
   ┌───────┴───────┬───────────────┐
   │               │               │
Conf >= 70%    50-70%          < 50%
   │               │               │
   ▼               ▼               ▼
 TRADE        Deep Analysis      SKIP
              ┌────┴────┐
          >= 70%     < 70%
              │          │
              ▼          ▼
           TRADE      REJECT
```

### 4.6 Erkannte Setup-Typen

Die AI kann folgende Setup-Typen identifizieren:

- `PULLBACK_EMA20` - Pullback zur EMA20 in Trend
- `PULLBACK_EMA50` - Pullback zur EMA50 in Trend
- `BREAKOUT` - Ausbruch über Widerstand
- `BREAKDOWN` - Durchbruch unter Unterstützung
- `MEAN_REVERSION` - Rückkehr zum Mittelwert
- `TREND_CONTINUATION` - Trendfortsetzung
- `SWING_FAILURE` - Fehlgeschlagener Swing
- `ABSORPTION` - Volumen-Absorption
- `DIVERGENCE` - Preis/Indikator Divergenz
- `NO_SETUP` - Kein erkennbares Setup

### 4.7 Konfiguration

```python
@dataclass
class BotConfig:
    symbol: str = "BTCUSDT"
    leverage: int = 10
    risk_per_trade_percent: Decimal = Decimal("1.0")
    max_position_size_btc: Decimal = Decimal("0.1")

    # SL/TP
    sl_atr_multiplier: Decimal = Decimal("1.5")
    tp_atr_multiplier: Decimal = Decimal("2.0")

    # Trailing
    trailing_stop_enabled: bool = True
    trailing_stop_atr_multiplier: Decimal = Decimal("1.0")
    trailing_stop_activation_percent: Decimal = Decimal("0.5")

    # Limits
    max_daily_loss_percent: Decimal = Decimal("3.0")
```

---

## 5. Signalgenerierung

### 5.1 Technische Indikatoren

Beide Bots verwenden folgende Indikatoren:

#### Trend-Indikatoren
| Indikator | Parameter | Verwendung |
|-----------|-----------|------------|
| SMA | 20, 50 | Trend-Richtung |
| EMA | 12, 20, 26, 50, 200 | Trend + Crossovers |
| MA Slope | 20 | Trend-Stärke |

#### Momentum-Indikatoren
| Indikator | Parameter | Verwendung |
|-----------|-----------|------------|
| RSI | 14 | Überkauft/Überverkauft |
| MACD | 12, 26, 9 | Momentum + Crossovers |
| Stochastic | 14, 3, 3 | Entry-Timing |
| CCI | 20 | Trendstärke |
| MFI | 14 | Volume + Price |

#### Volatilitäts-Indikatoren
| Indikator | Parameter | Verwendung |
|-----------|-----------|------------|
| ATR | 14 | SL/TP Berechnung |
| Bollinger Bands | 20, 2 | Volatilität + Levels |
| BB Width | - | Volatilitäts-Indikator |
| BB %B | - | Position in Bands |

#### Trendstärke
| Indikator | Parameter | Verwendung |
|-----------|-----------|------------|
| ADX | 14 | Trendstärke (>20 = Trend) |
| +DI / -DI | 14 | Trend-Richtung |

### 5.2 Regime-Erkennung

```python
class RegimeType(str, Enum):
    TREND_UP = "trend_up"      # ADX > 25, +DI > -DI
    TREND_DOWN = "trend_down"  # ADX > 25, -DI > +DI
    RANGE = "range"            # ADX < 20
    UNKNOWN = "unknown"

class VolatilityLevel(str, Enum):
    LOW = "low"        # ATR% < 1%
    NORMAL = "normal"  # ATR% 1-3%
    HIGH = "high"      # ATR% 3-5%
    EXTREME = "extreme" # ATR% > 5%
```

### 5.3 FeatureVector

```python
class FeatureVector(BaseModel):
    timestamp: datetime
    symbol: str

    # OHLCV
    open, high, low, close, volume: float

    # Alle Indikatoren
    sma_20, sma_50: float | None
    ema_12, ema_26: float | None
    rsi_14: float | None  # 0-100
    macd, macd_signal, macd_hist: float | None
    atr_14: float | None
    bb_upper, bb_middle, bb_lower: float | None
    adx, plus_di, minus_di: float | None

    def compute_hash(self) -> str:
        """Für Audit-Trail"""
        return sha256(json.dumps(self.to_dict_normalized()))
```

---

## 6. Risk Management

### 6.1 Position Sizing

#### Risiko-basiertes Sizing

```python
def calculate_position_size(balance, entry_price, stop_loss, risk_percent):
    """
    Position Size = Risk Amount / SL Distance

    Beispiel:
    - Balance: $10,000
    - Risk: 1% = $100
    - Entry: $50,000
    - SL: $49,500 (1%)
    - SL Distance: $500

    Position Size = $100 / $500 = 0.2 BTC
    Position Value = 0.2 * $50,000 = $10,000
    """
    risk_amount = balance * (risk_percent / 100)
    sl_distance = abs(entry_price - stop_loss)
    quantity = risk_amount / sl_distance
    return min(quantity, max_position_size)
```

### 6.2 SL/TP Berechnung

#### Percent-Based
```python
def calculate_sl_tp_percent(entry, side, sl_pct=0.5, tp_pct=1.0):
    if side == "BUY":
        sl = entry * (1 - sl_pct/100)
        tp = entry * (1 + tp_pct/100)
    else:
        sl = entry * (1 + sl_pct/100)
        tp = entry * (1 - tp_pct/100)
    return sl, tp
```

#### ATR-Based
```python
def calculate_sl_tp_atr(entry, side, atr, sl_mult=1.5, tp_mult=2.0):
    if side == "BUY":
        sl = entry - (atr * sl_mult)
        tp = entry + (atr * tp_mult)
    else:
        sl = entry + (atr * sl_mult)
        tp = entry - (atr * tp_mult)
    return sl, tp
```

### 6.3 Risk:Reward Ratio

```python
@dataclass
class RiskCalculation:
    entry_price: Decimal
    stop_loss: Decimal
    take_profit: Decimal

    @property
    def risk_reward_ratio(self) -> float:
        sl_distance = abs(self.entry_price - self.stop_loss)
        tp_distance = abs(self.take_profit - self.entry_price)
        return float(tp_distance / sl_distance)  # z.B. 1.33
```

### 6.4 Daily Loss Limit

```python
def check_daily_loss_limit(balance, daily_pnl, max_loss_percent):
    """
    Kill-Switch bei Erreichen des Daily Loss Limits.

    Beispiel:
    - Balance: $10,000
    - Max Loss: 3% = $300
    - Daily PnL: -$280 → OK, weitermachen
    - Daily PnL: -$320 → STOP, keine neuen Trades
    """
    max_loss = balance * (max_loss_percent / 100)

    if daily_pnl < 0 and abs(daily_pnl) >= max_loss:
        return False, "Daily loss limit reached"

    return True, "OK"
```

### 6.5 Loss Streak Cooldown

```python
def check_loss_streak(consecutive_losses, cooldown_threshold=3):
    """
    Pause nach N aufeinanderfolgenden Verlusten.

    Beispiel:
    - loss_streak_cooldown = 3
    - 3 Verluste in Folge → Pause für X Trades
    """
    if consecutive_losses >= cooldown_threshold:
        return False, f"Loss streak cooldown after {consecutive_losses} losses"
    return True, "OK"
```

---

## 7. AI/KI-Integration

### 7.1 Unterstützte Provider

| Provider | Modelle | API Key Env Var |
|----------|---------|-----------------|
| **OpenAI** | gpt-5.2, gpt-5.1, gpt-4.1, gpt-4.1-mini | `OPENAI_API_KEY` |
| **Anthropic** | claude-sonnet-4-5-20250929, claude-sonnet-4-5 | `ANTHROPIC_API_KEY` |
| **Gemini** | gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash | `GOOGLE_API_KEY` |

### 7.2 Konfiguration

Die AI-Einstellungen werden aus QSettings geladen:

```
File → Settings → AI

├── Provider: OpenAI / Anthropic / Gemini
├── Model: [Dropdown aus verfügbaren Modellen]
├── Enabled: true/false
├── Confidence Threshold (Trade): 70%
└── Confidence Threshold (Deep): 50%
```

### 7.3 AI Validation Response

```python
@dataclass
class AIValidation:
    approved: bool                 # Trade genehmigt?
    confidence_score: int          # 0-100
    setup_type: str | None         # z.B. "PULLBACK_EMA20"
    reasoning: str                 # Erklärung
    provider: str                  # "openai", "anthropic", etc.
    model: str                     # "gpt-4.1-mini", etc.
    timestamp: datetime
    validation_level: ValidationLevel  # QUICK, DEEP, BYPASS
    deep_analysis_triggered: bool
    error: str | None
```

### 7.4 Prompt-Struktur

```python
prompt = f"""
Du bist ein erfahrener Crypto-Trading-Analyst.

## Signal Details
{signal_info}

## Erfüllte Bedingungen
{conditions_met}

## Technische Indikatoren
{indicators}

## Marktkontext
{market_context}

## Antwort-Format (JSON)
{{
    "confidence_score": 0-100,
    "setup_type": "PULLBACK_EMA20",
    "approved": true/false,
    "reasoning": "kurze Erklärung"
}}
"""
```

### 7.5 Fallback-Strategie

```python
class AISignalValidator:
    fallback_to_technical: bool = True  # Bei API-Fehler

    async def validate_signal(self, signal):
        try:
            return await self._call_llm(prompt)
        except Exception as e:
            if self.fallback_to_technical:
                # Signal als "neutral" durchlassen
                return AIValidation(
                    approved=True,
                    confidence_score=50,
                    reasoning=f"Fallback due to: {e}"
                )
            else:
                return AIValidation(approved=False, ...)
```

---

## 8. Position Monitoring

### 8.1 MonitoredPosition

```python
@dataclass
class MonitoredPosition:
    symbol: str
    side: str                      # "BUY" oder "SELL"
    entry_price: Decimal
    quantity: Decimal
    entry_time: datetime

    # Stop Levels
    stop_loss: Decimal
    take_profit: Decimal
    initial_stop_loss: Decimal     # Original (vor Trailing)

    # Trailing State
    trailing_enabled: bool
    trailing_activated: bool
    trailing_atr: Decimal | None

    # Current State
    current_price: Decimal | None
    unrealized_pnl: Decimal
    unrealized_pnl_percent: float

    # Extrema für Trailing
    highest_price: Decimal | None  # Long
    lowest_price: Decimal | None   # Short
```

### 8.2 Exit-Trigger

```python
class ExitTrigger(str, Enum):
    STOP_LOSS = "STOP_LOSS"           # SL getriggert
    TAKE_PROFIT = "TAKE_PROFIT"       # TP getriggert
    TRAILING_STOP = "TRAILING_STOP"   # Trailing SL getriggert
    SIGNAL_EXIT = "SIGNAL_EXIT"       # Signal-Umkehr
    MANUAL = "MANUAL"                 # Manueller Exit
    SESSION_END = "SESSION_END"       # Session beendet
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"  # Limit erreicht
    BOT_STOPPED = "BOT_STOPPED"       # Bot gestoppt
```

### 8.3 Echtzeit-Überwachung

```python
async def on_price_update(self, price: Decimal) -> ExitResult | None:
    if not self._position:
        return None

    # 1. Position aktualisieren
    self._position.update_price(price)

    # 2. Exit-Bedingungen prüfen
    exit_result = self._check_exit_conditions(price)

    if exit_result.should_exit:
        await self._on_exit_triggered(self._position, exit_result)
        return exit_result

    # 3. Trailing Stop aktualisieren
    if self._position.trailing_enabled:
        await self._update_trailing_stop(price)

    return None
```

### 8.4 Trailing Stop Logik

```python
def adjust_sl_for_trailing(current_price, current_sl, entry_price, side, atr):
    # Aktivierungsprüfung
    if side == "BUY":
        profit_pct = (current_price - entry_price) / entry_price * 100
    else:
        profit_pct = (entry_price - current_price) / entry_price * 100

    if profit_pct < activation_percent:
        return current_sl, False  # Nicht aktiviert

    # Neue SL berechnen
    trailing_distance = atr * trailing_atr_multiplier

    if side == "BUY":
        new_sl = current_price - trailing_distance
        # SL darf nur STEIGEN (nie lockern)
        if new_sl > current_sl:
            return new_sl, True
    else:  # SHORT
        new_sl = current_price + trailing_distance
        # SL darf nur SINKEN (nie lockern)
        if new_sl < current_sl:
            return new_sl, True

    return current_sl, False
```

---

## 9. Konfiguration

### 9.1 Alpaca Bot Konfiguration (Pydantic)

```python
# Vollständige Konfiguration
config = FullBotConfig(
    bot=BotConfig(
        market_type=MarketType.CRYPTO,
        symbol="BTC/USD",
        timeframe="1m",
        environment=TradingEnvironment.PAPER,
        ki_mode=KIMode.NO_KI,
        trailing_mode=TrailingMode.ATR,
        auto_trade=False,
        entry_score_threshold=0.6,
    ),
    risk=RiskConfig(
        risk_per_trade_pct=1.0,
        max_position_size_pct=20.0,
        initial_stop_loss_pct=2.0,
        trailing_activation_pct=0.5,
        trailing_atr_multiple=2.5,
        max_trades_per_day=10,
        max_daily_loss_pct=5.0,
    ),
    llm_policy=LLMPolicyConfig(
        call_on_regime_flip=True,
        call_on_exit_candidate=True,
        temperature=0.1,
        fallback_on_failure=True,
    )
)
```

### 9.2 Bitunix Bot Konfiguration (Dataclass)

```python
config = BotConfig(
    symbol="BTCUSDT",
    leverage=10,
    risk_per_trade_percent=Decimal("1.0"),
    max_position_size_btc=Decimal("0.1"),
    sl_atr_multiplier=Decimal("1.5"),
    tp_atr_multiplier=Decimal("2.0"),
    trailing_stop_enabled=True,
    trailing_stop_atr_multiplier=Decimal("1.0"),
    trailing_stop_activation_percent=Decimal("0.5"),
    max_daily_loss_percent=Decimal("3.0"),
    primary_timeframe="1m",
    analysis_timeframes=["1d", "4h", "1h"],
)
```

### 9.3 JSON-Strategie-Konfiguration

`config/trading_bot/strategy_config.json`:

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

### 9.4 Markt-spezifische Defaults

#### Crypto Defaults

```python
RiskConfig.crypto_defaults() = {
    "initial_stop_loss_pct": 3.0,
    "trailing_pct_distance": 2.0,
    "trailing_atr_multiple": 2.5,
    "trailing_atr_trending": 2.0,
    "trailing_atr_ranging": 3.5,
    "expected_slippage_pct": 0.1,
    "commission_pct": 0.1,
}
```

#### NASDAQ Defaults

```python
RiskConfig.nasdaq_defaults() = {
    "initial_stop_loss_pct": 1.5,
    "trailing_pct_distance": 1.0,
    "trailing_atr_multiple": 1.5,
    "trailing_atr_trending": 1.5,
    "trailing_atr_ranging": 2.5,
    "expected_slippage_pct": 0.02,
    "commission_pct": 0.0,  # Commission-free
}
```

---

## 10. Vergleich der Trading Agents

### 10.1 Feature-Matrix

| Feature | Alpaca Bot | Bitunix Bot |
|---------|------------|-------------|
| **Lokation** | `src/core/tradingbot/` | `src/core/trading_bot/` |
| **Hauptklasse** | `BotController` | `BotEngine` |
| **Märkte** | Crypto + NASDAQ | Crypto Futures |
| **Config-Typ** | Pydantic Models | Dataclass + JSON |
| **Signal-Methode** | Score-based (0-1) | Confluence (3/5) |
| **AI Integration** | 3 Modi (NO/LOW/FULL) | Hierarchisch (Quick→Deep) |
| **SL/TP** | Native Exchange Orders | Client-seitig |
| **Trailing Modi** | PCT, ATR, SWING | ATR-based |
| **Leverage** | Nein (Spot) | Ja (bis 125x) |
| **Regime-Erkennung** | Integriert | Extern |
| **Logging** | Decision Logging | Indicator Snapshots |

### 10.2 Entscheidungslogik-Vergleich

#### Alpaca Bot (Score-based)
```python
# Score 0-1, Threshold für Entry
if entry_score >= 0.6:
    execute_trade()
```

#### Bitunix Bot (Confluence)
```python
# Mindestens 3 von 5 Bedingungen
if confluence_score >= 3:
    execute_trade()
```

### 10.3 AI-Validierung-Vergleich

#### Alpaca Bot
```
Signal → [KI-Modus?] → Trade
         NO_KI: direkt
         LOW_KI: täglich
         FULL_KI: bei Events
```

#### Bitunix Bot
```
Signal → Quick AI (Conf >= 3)
         │
         ├─ >= 70%: Trade
         ├─ 50-70%: Deep Analysis → Trade/Reject
         └─ < 50%: Skip
```

### 10.4 Wann welchen Bot verwenden?

| Anwendungsfall | Empfohlener Bot |
|----------------|-----------------|
| Crypto Spot Trading | Alpaca Bot |
| Aktien/NASDAQ Trading | Alpaca Bot |
| Crypto Futures/Leverage | Bitunix Bot |
| Backtesting (schnell) | Alpaca Bot (NO_KI) |
| Maximale AI-Validierung | Bitunix Bot (Hierarchisch) |
| Multi-Asset Portfolio | Alpaca Bot |
| Hohes Risiko/Reward | Bitunix Bot (Leverage) |

---

## 11. API-Integration

### 11.1 Alpaca API

```python
# REST Client
from alpaca.trading.client import TradingClient

client = TradingClient(api_key, secret_key, paper=True)

# Order erstellen
order = client.submit_order(
    symbol="BTC/USD",
    side="buy",
    type="market",
    qty=0.01,
    time_in_force="gtc"
)

# WebSocket Streaming
from alpaca.data.live import CryptoDataStream

stream = CryptoDataStream(api_key, secret_key)

@stream.on_quote
async def handle_quote(quote):
    process_quote(quote)

await stream.subscribe_quotes(["BTC/USD"])
```

### 11.2 Bitunix API

```python
# REST Client
from src.brokers.bitunix import BitunixClient

client = BitunixClient(api_key, secret_key)

# Order erstellen
order = await client.create_order(
    symbol="BTCUSDT",
    side="BUY",
    type="MARKET",
    quantity=0.01,
    leverage=10
)

# WebSocket Streaming
async for tick in client.subscribe_ticker("BTCUSDT"):
    process_tick(tick)
```

### 11.3 API Keys

Alle API Keys werden aus Umgebungsvariablen gelesen:

```bash
# Alpaca
ALPACA_API_KEY=xxx
ALPACA_SECRET_KEY=xxx
ALPACA_PAPER=true

# Bitunix
BITUNIX_API_KEY=xxx
BITUNIX_SECRET_KEY=xxx

# AI Providers
OPENAI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
GOOGLE_API_KEY=xxx
```

---

## 12. Sicherheit & Best Practices

### 12.1 Trading-Sicherheit

1. **Paper-First Prinzip**
   - Standard ist IMMER Paper-Trading
   - Live-Trading nur durch explizite Konfiguration
   - Separate API Keys für Paper/Live

2. **Daily Loss Limit**
   - Kill-Switch bei Erreichen des Limits
   - Keine neuen Trades bis Reset (neuer Tag)
   - Bestehende Positionen werden NICHT automatisch geschlossen

3. **Loss Streak Cooldown**
   - Pause nach N aufeinanderfolgenden Verlusten
   - Verhindert emotionales "Revenge Trading"

4. **Max Position Limits**
   - Absolute Grenzen für Position Size
   - Unabhängig von berechneter Größe

### 12.2 API-Sicherheit

1. **Keine API Keys im Code**
   - Nur über Umgebungsvariablen
   - Niemals in Git committen

2. **Rate Limiting**
   - Respektiere API-Limits
   - Implementiere Backoff-Strategien

3. **Error Handling**
   - Graceful Degradation bei API-Fehlern
   - Fallback-Strategien

### 12.3 AI-Sicherheit

1. **Fallback bei Fehlern**
   - Regelbasiert bei API-Ausfall
   - Keine Trades bei unbekanntem Zustand

2. **Confidence Thresholds**
   - Nur Trades bei hoher Confidence
   - Deep Analysis bei Unsicherheit

3. **Audit Trail**
   - Alle AI-Entscheidungen geloggt
   - Feature-Hashing für Reproduzierbarkeit

### 12.4 Checkliste vor Live-Trading

- [ ] Ausreichend Paper-Trading durchgeführt
- [ ] Risk-Parameter validiert
- [ ] Daily Loss Limit gesetzt
- [ ] API Keys korrekt konfiguriert
- [ ] Logging aktiviert
- [ ] Notfall-Prozedur bekannt (Bot stoppen)
- [ ] Monitoring eingerichtet

---

## 13. Troubleshooting

### 13.1 Signal wird nicht generiert

**Alpaca Bot:**
```python
# Prüfe Entry Score
if entry_score < entry_score_threshold:
    logger.info(f"Score {entry_score} < Threshold {threshold}")

# Prüfe Regime
if not strategy.is_applicable(regime):
    logger.info(f"Strategy not applicable for regime {regime}")
```

**Bitunix Bot:**
```python
# Prüfe Confluence
if confluence_score < 3:
    logger.info(f"Confluence {confluence_score}/5 < 3")

# Prüfe Datenmenge
if len(df) < 200:
    logger.warning("Need at least 200 bars for EMA200")
```

### 13.2 AI lehnt ab

```python
# Prüfe Confidence
if ai_result.confidence_score < confidence_threshold_trade:
    logger.info(f"AI confidence {ai_result.confidence_score}% too low")

# Prüfe API Key
if "API key" in ai_result.error:
    logger.error("Check AI provider API key configuration")

# Prüfe Model
if "model not found" in ai_result.error:
    logger.error(f"Model {ai_result.model} not available")
```

### 13.3 SL/TP wird nicht getriggert (Bitunix)

```python
# Prüfe ob PositionMonitor läuft
if not position_monitor._running:
    logger.error("PositionMonitor not running!")

# Prüfe WebSocket-Verbindung
if not websocket.is_connected:
    logger.error("WebSocket disconnected")

# Prüfe Preis-Updates
logger.debug(f"Last price update: {position.current_price}")
```

### 13.4 Order wird abgelehnt

```python
# Prüfe Balance
if position_value > available_balance * leverage:
    logger.error("Insufficient margin")

# Prüfe Min Order Size
if quantity < min_order_size:
    logger.error(f"Quantity {quantity} < min {min_order_size}")

# Prüfe Symbol
if not exchange.supports_symbol(symbol):
    logger.error(f"Symbol {symbol} not supported")
```

### 13.5 Logging aktivieren

```python
import logging

# Verbose Logging
logging.getLogger("src.core.trading_bot").setLevel(logging.DEBUG)
logging.getLogger("src.core.tradingbot").setLevel(logging.DEBUG)

# AI Logging
logging.getLogger("src.core.trading_bot.ai_validator").setLevel(logging.DEBUG)
```

---

## 14. Glossar

| Begriff | Erklärung |
|---------|-----------|
| **ATR** | Average True Range - Volatilitätsindikator |
| **Confluence** | Übereinstimmung mehrerer Signale |
| **EMA** | Exponential Moving Average |
| **Entry Score** | Bewertung der Entry-Qualität (0-1) |
| **Leverage** | Hebel für Futures-Trading |
| **MACD** | Moving Average Convergence Divergence |
| **Paper Trading** | Simuliertes Trading ohne echtes Geld |
| **Position Sizing** | Berechnung der Trade-Größe basierend auf Risiko |
| **Regime** | Marktphase (Trend/Range) |
| **RSI** | Relative Strength Index |
| **SL** | Stop Loss |
| **TP** | Take Profit |
| **Trailing Stop** | Dynamischer SL der dem Preis folgt |
| **Volatility** | Schwankungsbreite des Preises |

---

## Anhang: Quick Reference

### A. Bot starten

```python
# Alpaca Bot
from src.core.tradingbot import BotController, FullBotConfig

config = FullBotConfig.create_default("BTC/USD", MarketType.CRYPTO)
controller = BotController(config)
await controller.start()

# Bitunix Bot
from src.core.trading_bot import BotEngine, BotConfig

config = BotConfig(symbol="BTCUSDT", leverage=10)
engine = BotEngine(config)
await engine.start()
```

### B. Konfiguration ändern

```python
# Alpaca Bot
controller.update_config(auto_trade=True)
controller.set_ki_mode(KIMode.FULL_KI)

# Bitunix Bot
engine.risk_manager.update_config(new_config)
engine.ai_validator.update_config(enabled=True)
```

### C. Bot stoppen

```python
# Alpaca Bot
await controller.stop()

# Bitunix Bot
await engine.stop()
```

---

*Dokumentation erstellt für OrderPilot-AI | Version 1.0.0 | Januar 2026*
