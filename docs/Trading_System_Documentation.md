# Trading System Documentation

> **Version:** 2.0.0
> **Erstellt:** 2025-01-07
> **Projekt:** OrderPilot-AI
> **Format:** Markdown (KI-optimiert)

---

## Inhaltsverzeichnis

1. [Chart-Analyse](#1-chart-analyse)
   - [AI-Analyse-Funktionen](#11-ai-analyse-funktionen)
   - [Technische Indikatoren](#12-technische-indikatoren)
   - [Signal-Generierung](#13-signal-generierung)
   - [Regime-Erkennung](#14-regime-erkennung)
2. [AI-Chat Funktionen und Prompts](#2-ai-chat-funktionen-und-prompts)
   - [Prompt-Templates](#21-prompt-templates)
   - [Setup-Typen](#23-setup-typen-ai-erkennbar)
   - [AI-Validation Konfiguration](#24-ai-validation-konfiguration)
   - [AI Provider](#25-ai-provider)
3. [Trading Bot Funktionen](#3-trading-bot-funktionen)
   - [Bot Engine (State Machine)](#31-bot-engine-state-machine)
   - [Entry-Bedingungen](#33-entry-bedingungen-long)
   - [Exit-Bedingungen](#35-exit-bedingungen)
   - [Risk Manager](#36-risk-manager-funktionen)
   - [Position Monitor](#38-position-monitor-funktionen)
4. [JSON-Konfiguration für Bot-Workflow](#4-json-konfiguration-für-bot-workflow)
5. [Einstellungsseiten-Variablen](#5-einstellungsseiten-variablen)
6. [Verfügbare Chart-Indikatoren](#6-verfügbare-chart-indikatoren-dropdown-im-chart-fenster)
   - [Overlay-Indikatoren](#61-overlay-indikatoren-im-preis-chart)
   - [Oszillator-Indikatoren](#62-oszillator-indikatoren-separate-panels)
   - [Alle Engine-Indikatoren](#63-alle-implementierten-indikatoren-engine)

---

## 1. Chart-Analyse

### 1.1 AI-Analyse-Funktionen

| Funktion | Klasse/Datei | Beschreibung | Konfigurierbare Parameter |
|----------|--------------|--------------|---------------------------|
| `validate_signal()` | `AISignalValidator` (ai_validator.py:251) | Validiert Trading-Signal mittels LLM | `enabled`, `confidence_threshold_trade`, `timeout_seconds` |
| `validate_signal_hierarchical()` | `AISignalValidator` (ai_validator.py:594) | Hierarchische Validierung: Quick → Deep Analysis | `confidence_threshold_trade` (>=70%), `confidence_threshold_deep` (>=50%), `deep_analysis_enabled` |
| `_run_deep_analysis()` | `AISignalValidator` (ai_validator.py:695) | Tiefe Analyse bei unsicheren Signalen | `ohlcv_data`, Model aus QSettings |
| `_build_prompt()` | `AISignalValidator` (ai_validator.py:308) | Erstellt LLM-Prompt für Signal-Validierung | Signal-Details, Indikatoren, Marktkontext |
| `_call_openai()` | `AISignalValidator` (ai_validator.py:411) | OpenAI API Call (GPT-4.1, GPT-5.x) | `model`, `temperature`, `reasoning_effort` |
| `_call_anthropic()` | `AISignalValidator` (ai_validator.py:481) | Anthropic API Call (Claude Sonnet 4.5) | `model`, `max_tokens` |
| `_call_gemini()` | `AISignalValidator` (ai_validator.py:532) | Google Gemini API Call | `model`, `temperature` |

### 1.2 Technische Indikatoren

| Indikator | Datei/Funktion | Beschreibung | Parameter |
|-----------|----------------|--------------|-----------|
| `EMA (20, 50, 200)` | signal_generator.py:100-108 | Exponential Moving Average | `periods: [20, 50, 200]`, `source: close` |
| `RSI (14)` | signal_generator.py:103-105 | Relative Strength Index | `period: 14`, `overbought: 70`, `oversold: 30` |
| `MACD` | signal_generator.py:107-109 | Moving Average Convergence Divergence | `fast_period: 12`, `slow_period: 26`, `signal_period: 9` |
| `Bollinger Bands` | strategy_config.json:64-69 | Volatilitätsbänder | `period: 20`, `std_dev: 2.0` |
| `ATR (14)` | signal_generator.py | Average True Range | `period: 14` |
| `ADX (14)` | signal_generator.py:106 | Average Directional Index | `period: 14`, `trend_threshold: 20` |

### 1.3 Signal-Generierung

| Funktion | Klasse/Datei | Beschreibung | Parameter |
|----------|--------------|--------------|-----------|
| `generate_signal()` | `SignalGenerator` (signal_generator.py:119) | Generiert Trading-Signal aus OHLCV DataFrame | `df`, `regime`, `require_regime_alignment` |
| `_check_long_conditions()` | `SignalGenerator` (signal_generator.py:204) | Prüft alle LONG Entry-Bedingungen | 5 Bedingungen mit Gewichtung |
| `_check_short_conditions()` | `SignalGenerator` (signal_generator.py:316) | Prüft alle SHORT Entry-Bedingungen | 5 Bedingungen mit Gewichtung |
| `check_exit_signal()` | `SignalGenerator` (signal_generator.py:452) | Prüft Exit-Signal bei Reversal/RSI-Extreme | `current_position_side` |
| `extract_indicator_snapshot()` | `SignalGenerator` (signal_generator.py:493) | Extrahiert Indikator-Snapshot für Logging | Alle Indikatoren |

### 1.4 Regime-Erkennung

| Funktion | Klasse/Datei | Beschreibung | Mögliche Werte |
|----------|--------------|--------------|----------------|
| `_detect_regime()` | `TradingBotEngine` (bot_engine.py:833) | Erkennt Market Regime | `STRONG_TREND_BULL`, `WEAK_TREND_BULL`, `STRONG_TREND_BEAR`, `WEAK_TREND_BEAR`, `CHOP_RANGE`, `NEUTRAL` |

---

## 2. AI-Chat Funktionen und Prompts

### 2.1 Prompt-Templates

| Prompt-Typ | Datei/Funktion | Beschreibung | Verwendung |
|------------|----------------|--------------|------------|
| **Quick Validation Prompt** | ai_validator.py:365-396 | Signal-Bewertung mit Indikatoren | Confluence >= 4 |
| **Deep Analysis Prompt** | ai_validator.py:742-787 | Erweitert um OHLCV-Kerzen + detaillierte Analyse | Bei Confidence 50-70% |

### 2.2 Prompt-Inhalt (Quick Validation)

```text
## Signal Details
- direction: LONG/SHORT
- confluence_score: 0-5
- strength: STRONG/MODERATE/WEAK
- current_price: Decimal
- regime: Market Regime

## Erfüllte Bedingungen (x/5)
## Nicht erfüllte Bedingungen
## Technische Indikatoren (RSI, EMA, MACD, ATR, ADX, BB)
## Marktkontext (Regime, Trends)

## Aufgabe:
1. Bewerte die Qualität dieses Signals
2. Identifiziere den Setup-Typ
3. Gib einen Confidence Score (0-100)
4. Erkläre kurz dein Reasoning
```

### 2.3 Setup-Typen (AI erkennbar)

| Setup-Typ | Beschreibung |
|-----------|--------------|
| `PULLBACK_EMA20` | Pullback zur EMA20 |
| `PULLBACK_EMA50` | Pullback zur EMA50 |
| `BREAKOUT` | Ausbruch über Widerstand |
| `BREAKDOWN` | Durchbruch unter Support |
| `MEAN_REVERSION` | Rückkehr zum Mittelwert |
| `TREND_CONTINUATION` | Trendfortsetzung |
| `SWING_FAILURE` | Swing-Fehlausbruch |
| `ABSORPTION` | Volumen-Absorption |
| `DIVERGENCE` | Preis-Indikator Divergenz |
| `NO_SETUP` | Kein erkennbares Setup |

### 2.4 AI-Validation Konfiguration

| Parameter | Datei | Beschreibung | Standardwert |
|-----------|-------|--------------|--------------|
| `enabled` | strategy_config.json:314 | AI-Validierung aktivieren | `true` |
| `min_confluence_for_ai` | strategy_config.json:319 | Min. Confluence für AI-Call | `4` |
| `confidence_threshold_trade` | strategy_config.json:322 | Trade ausführen bei >= | `70%` |
| `confidence_threshold_deep` | strategy_config.json:325 | Deep Analysis bei >= | `50%` |
| `deep_analysis_enabled` | strategy_config.json:331 | Deep Analysis aktivieren | `true` |
| `fallback_to_technical` | strategy_config.json:334 | Fallback bei API-Fehler | `true` |
| `timeout_seconds` | strategy_config.json:335 | API Timeout | `30` |

### 2.5 AI Provider (aus QSettings)

| Provider | Model-Keys | Standardmodelle |
|----------|------------|-----------------|
| `openai` | `openai_model` | `gpt-4.1-mini`, `gpt-5.1`, `gpt-5.2` |
| `anthropic` | `anthropic_model` | `claude-sonnet-4-5` |
| `gemini` | `gemini_model` | `gemini-1.5-flash`, `gemini-2.0-flash-exp` |

---

## 3. Trading Bot Funktionen

### 3.1 Bot Engine (State Machine)

| Funktion | Klasse/Datei | Beschreibung | States |
|----------|--------------|--------------|--------|
| `start()` | `TradingBotEngine` (bot_engine.py:303) | Startet den Bot | IDLE → STARTING → ANALYZING |
| `stop()` | `TradingBotEngine` (bot_engine.py:339) | Stoppt den Bot | → STOPPING → IDLE |
| `_run_analysis_cycle()` | `TradingBotEngine` (bot_engine.py:397) | Ein Analyse-Zyklus | ANALYZING ↔ WAITING_SIGNAL |
| `_execute_trade()` | `TradingBotEngine` (bot_engine.py:513) | Führt Trade aus | → OPENING_POSITION → IN_POSITION |
| `_close_position()` | `TradingBotEngine` (bot_engine.py:632) | Schließt Position | → CLOSING_POSITION → WAITING_SIGNAL |

### 3.2 Bot States

| State | Beschreibung |
|-------|--------------|
| `IDLE` | Bot gestoppt |
| `STARTING` | Bot startet |
| `ANALYZING` | Markt wird analysiert |
| `WAITING_SIGNAL` | Warte auf Signal |
| `VALIDATING` | Signal wird validiert (AI) |
| `OPENING_POSITION` | Order wird platziert |
| `IN_POSITION` | Position offen |
| `CLOSING_POSITION` | Position wird geschlossen |
| `STOPPING` | Bot stoppt |
| `ERROR` | Fehler-Zustand |

### 3.3 Entry-Bedingungen (Long)

| ID | Name | Typ | Regel | Gewicht |
|----|------|-----|-------|---------|
| `regime_check` | Regime Bullish | `regime` | in: `[STRONG_TREND_BULL, TREND_BULL, NEUTRAL]` | 1 |
| `ema_alignment` | EMA Alignment | `indicator_comparison` | price > EMA20 > EMA50 | 1 |
| `rsi_range` | RSI Not Overbought | `indicator_range` | RSI: 35-60 | 1 |
| `macd_bullish` | MACD Bullish | `indicator_comparison` | MACD > Signal AND Hist > 0 | 1 |
| `adx_trending` | ADX Trending | `indicator_threshold` | ADX > 20 | 1 |
| `bb_position` | Not at Upper Band | `indicator_comparison` | price < BB_upper AND price > BB_middle | 1 |

### 3.4 Entry-Bedingungen (Short)

| ID | Name | Typ | Regel | Gewicht |
|----|------|-----|-------|---------|
| `regime_check` | Regime Bearish | `regime` | in: `[STRONG_TREND_BEAR, TREND_BEAR, NEUTRAL]` | 1 |
| `ema_alignment` | EMA Alignment | `indicator_comparison` | price < EMA20 < EMA50 | 1 |
| `rsi_range` | RSI Not Oversold | `indicator_range` | RSI: 40-65 | 1 |
| `macd_bearish` | MACD Bearish | `indicator_comparison` | MACD < Signal AND Hist < 0 | 1 |
| `adx_trending` | ADX Trending | `indicator_threshold` | ADX > 20 | 1 |
| `bb_position` | Not at Lower Band | `indicator_comparison` | price > BB_lower AND price < BB_middle | 1 |

### 3.5 Exit-Bedingungen

| Trigger | Datei/Klasse | Beschreibung | Parameter |
|---------|--------------|--------------|-----------|
| `STOP_LOSS` | position_monitor.py:37 | Preis erreicht SL | `percent: 0.5%` oder `atr_multiplier: 1.5` |
| `TAKE_PROFIT` | position_monitor.py:38 | Preis erreicht TP | `percent: 1.0%` oder `atr_multiplier: 2.0` |
| `TRAILING_STOP` | position_monitor.py:39 | Trailing Stop ausgelöst | `trail_percent: 0.3%`, `activation_percent: 0.5%` |
| `SIGNAL_EXIT` | position_monitor.py:40 | Gegensignal erkannt | `min_confluence: 3` |
| `RSI_EXTREME` | strategy_config.json:291-295 | RSI > 80 (Long) oder < 20 (Short) | `long_exit_above: 80`, `short_exit_below: 20` |
| `SESSION_END` | strategy_config.json:297-300 | Session-Ende | `close_time_utc: "22:00"` (deaktiviert) |
| `MANUAL` | position_monitor.py:41 | Manueller Exit | - |
| `BOT_STOPPED` | position_monitor.py:44 | Bot gestoppt | - |

### 3.6 Risk Manager Funktionen

| Funktion | Klasse/Datei | Beschreibung | Parameter |
|----------|--------------|--------------|-----------|
| `calculate_sl_tp()` | `RiskManager` (risk_manager.py:150) | Berechnet SL/TP | `entry_price`, `side`, `atr` |
| `calculate_position_size()` | `RiskManager` (risk_manager.py:212) | Position Sizing | `balance`, `entry_price`, `stop_loss`, `risk_percent` |
| `calculate_full_risk()` | `RiskManager` (risk_manager.py:271) | Vollständige Risikoanalyse | Alle Parameter |
| `check_daily_loss_limit()` | `RiskManager` (risk_manager.py:339) | Daily Loss Limit Check | `balance`, `max_daily_loss_percent` |
| `adjust_sl_for_trailing()` | `RiskManager` (risk_manager.py:461) | Trailing Stop Anpassung | `current_price`, `atr`, `activation_percent` |
| `validate_trade()` | `RiskManager` (risk_manager.py:407) | Trade-Validierung | Alle Risk-Parameter |

### 3.7 Risk Management Parameter

| Parameter | Datei | Beschreibung | Standardwert |
|-----------|-------|--------------|--------------|
| `max_position_risk_percent` | strategy_config.json:305 | Max. Risiko pro Trade | `1.0%` |
| `max_daily_loss_percent` | strategy_config.json:306 | Max. täglicher Verlust | `100%` (deaktiviert) |
| `max_position_size_btc` | strategy_config.json:308 | Max. Position Size | `0.1 BTC` |
| `leverage` | strategy_config.json:309 | Hebel | `10x` |
| `single_position_only` | strategy_config.json:310 | Nur eine Position | `true` |

### 3.8 Position Monitor Funktionen

| Funktion | Klasse/Datei | Beschreibung |
|----------|--------------|--------------|
| `set_position()` | `PositionMonitor` (position_monitor.py:202) | Setzt neue Position |
| `on_price_update()` | `PositionMonitor` (position_monitor.py:288) | Preis-Update Handler |
| `_check_exit_conditions()` | `PositionMonitor` (position_monitor.py:328) | Prüft SL/TP |
| `_update_trailing_stop()` | `PositionMonitor` (position_monitor.py:376) | Trailing Stop Update |
| `trigger_manual_exit()` | `PositionMonitor` (position_monitor.py:412) | Manueller Exit |
| `trigger_signal_exit()` | `PositionMonitor` (position_monitor.py:446) | Signal-basierter Exit |

### 3.9 Timeframe-Konfiguration

| Rolle | Interval | Source | Lookback | Update-Interval | Zweck |
|-------|----------|--------|----------|-----------------|-------|
| `macro` | 1D | alpaca | 200 Bars | 60 min | Langfristiger Trend |
| `trend` | 4h | alpaca | 100 Bars | 15 min | Mittelfristiger Trend |
| `context` | 1h | bitunix | 100 Bars | 5 min | Tageskontext |
| `execution` | 5m | bitunix | 200 Bars | 1 min | Entry/Exit Timing |

### 3.10 Timing-Konfiguration

| Parameter | Datei | Beschreibung | Standardwert |
|-----------|-------|--------------|--------------|
| `analysis_interval_seconds` | strategy_config.json:339 | Analyse-Intervall | `60` Sekunden |
| `position_check_interval_ms` | strategy_config.json:340 | Position-Check | `1000` ms |
| `macro_update_minutes` | strategy_config.json:341 | Macro TF Update | `60` min |
| `trend_update_minutes` | strategy_config.json:342 | Trend TF Update | `15` min |
| `context_update_minutes` | strategy_config.json:343 | Context TF Update | `5` min |

---

## 4. JSON-Konfiguration für Bot-Workflow

Die folgende JSON-Struktur ermöglicht die vollständige Konfiguration des Trading-Bot-Workflows:

```json
{
  "_version": "2.0.0",
  "_description": "Modularer Trading Bot Workflow - Alle Komponenten konfigurierbar",

  "workflow": {
    "name": "Custom Trading Strategy",
    "enabled": true,
    "mode": "paper",

    "phases": {
      "data_acquisition": {
        "enabled": true,
        "source": "bitunix",
        "timeframes": ["5m", "1h", "4h", "1D"],
        "lookback_bars": 200
      },

      "signal_generation": {
        "enabled": true,
        "min_confluence": 4,
        "use_regime_filter": true,
        "conditions": {
          "long": ["ema_alignment", "rsi_range", "macd_bullish", "adx_trending", "bb_position", "regime_check"],
          "short": ["ema_alignment", "rsi_range", "macd_bearish", "adx_trending", "bb_position", "regime_check"]
        }
      },

      "ai_validation": {
        "enabled": true,
        "provider": "from_settings",
        "model": "from_settings",
        "hierarchical_enabled": true,
        "quick_threshold": 70,
        "deep_threshold": 50,
        "skip_below": 50,
        "timeout_seconds": 30
      },

      "trade_execution": {
        "enabled": true,
        "order_type": "market",
        "leverage": 10,
        "position_sizing": "risk_based"
      },

      "position_monitoring": {
        "enabled": true,
        "check_interval_ms": 1000,
        "exit_triggers": ["stop_loss", "take_profit", "trailing_stop", "signal_reversal", "rsi_extreme"]
      }
    }
  },

  "components": {
    "indicators": {
      "ema": { "enabled": true, "periods": [20, 50, 200] },
      "rsi": { "enabled": true, "period": 14, "overbought": 70, "oversold": 30 },
      "macd": { "enabled": true, "fast": 12, "slow": 26, "signal": 9 },
      "bollinger": { "enabled": true, "period": 20, "std_dev": 2.0 },
      "atr": { "enabled": true, "period": 14 },
      "adx": { "enabled": true, "period": 14, "threshold": 20 }
    },

    "risk_management": {
      "stop_loss": { "type": "percent_based", "percent": 0.5 },
      "take_profit": { "type": "percent_based", "percent": 1.0 },
      "trailing_stop": { "enabled": true, "trail_percent": 0.3, "activation_percent": 0.5 },
      "max_risk_per_trade": 1.0,
      "max_daily_loss": 100.0,
      "max_position_size_btc": 0.1
    },

    "filters": {
      "volume": { "enabled": true, "min_ratio": 0.5 },
      "spread": { "enabled": false, "max_percent": 0.1 },
      "volatility": { "enabled": true, "min_atr_percent": 0.5, "max_atr_percent": 5.0 }
    }
  },

  "chatbot_integration": {
    "enabled": true,
    "use_cases": {
      "signal_validation": {
        "trigger": "on_signal_generated",
        "action": "validate_with_ai"
      },
      "deep_analysis": {
        "trigger": "confidence_50_to_70",
        "action": "run_deep_analysis"
      },
      "trade_notification": {
        "trigger": "on_position_opened",
        "action": "log_trade_details"
      }
    }
  }
}
```

---

## 5. Einstellungsseiten-Variablen

### 5.1 Bot-Einstellungen (UI)

| Kategorie | Variable | Typ | Beschreibung | UI-Element |
|-----------|----------|-----|--------------|------------|
| **Allgemein** | `enabled` | bool | Bot aktivieren | Checkbox |
| **Allgemein** | `symbol` | string | Trading-Paar | Dropdown |
| **Allgemein** | `analysis_interval` | int | Analyse-Intervall (s) | Spinbox |
| **Signal** | `min_confluence` | int | Min. Confluence | Slider (1-5) |
| **Signal** | `use_regime_filter` | bool | Regime-Filter | Checkbox |
| **AI** | `ai_enabled` | bool | AI-Validierung | Checkbox |
| **AI** | `ai_provider` | enum | OpenAI/Anthropic/Gemini | Dropdown |
| **AI** | `ai_model` | string | Modell-ID | Dropdown |
| **AI** | `confidence_trade` | int | Trade-Threshold | Slider (0-100) |
| **AI** | `confidence_deep` | int | Deep-Analysis-Threshold | Slider (0-100) |
| **AI** | `deep_enabled` | bool | Deep Analysis aktivieren | Checkbox |
| **Risk** | `max_risk_percent` | float | Max. Risiko pro Trade | Spinbox |
| **Risk** | `max_daily_loss` | float | Max. Daily Loss | Spinbox |
| **Risk** | `leverage` | int | Hebel | Spinbox (1-125) |
| **Risk** | `max_position_btc` | float | Max. Position BTC | Spinbox |
| **SL/TP** | `sl_type` | enum | percent/atr | Radio |
| **SL/TP** | `sl_percent` | float | SL Prozent | Spinbox |
| **SL/TP** | `sl_atr_mult` | float | SL ATR Multiplier | Spinbox |
| **SL/TP** | `tp_percent` | float | TP Prozent | Spinbox |
| **SL/TP** | `tp_atr_mult` | float | TP ATR Multiplier | Spinbox |
| **Trailing** | `trailing_enabled` | bool | Trailing aktivieren | Checkbox |
| **Trailing** | `trail_percent` | float | Trail-Abstand | Spinbox |
| **Trailing** | `activation_percent` | float | Aktivierungsschwelle | Spinbox |

### 5.2 Indikator-Einstellungen

| Indikator | Parameter | Typ | Bereich | Standard |
|-----------|-----------|-----|---------|----------|
| **EMA** | `periods` | int[] | 1-500 | [20, 50, 200] |
| **RSI** | `period` | int | 2-50 | 14 |
| **RSI** | `overbought` | int | 50-100 | 70 |
| **RSI** | `oversold` | int | 0-50 | 30 |
| **MACD** | `fast_period` | int | 2-50 | 12 |
| **MACD** | `slow_period` | int | 10-100 | 26 |
| **MACD** | `signal_period` | int | 2-50 | 9 |
| **BB** | `period` | int | 5-100 | 20 |
| **BB** | `std_dev` | float | 0.5-5.0 | 2.0 |
| **ATR** | `period` | int | 2-50 | 14 |
| **ADX** | `period` | int | 2-50 | 14 |
| **ADX** | `threshold` | int | 10-50 | 20 |

---

## 6. Verfügbare Chart-Indikatoren (Dropdown im Chart-Fenster)

### 6.1 Overlay-Indikatoren (im Preis-Chart)

Diese Indikatoren werden direkt über dem Preis-Chart angezeigt:

| ID | Name | Beschreibung | Standard-Parameter | Farbe |
|----|------|--------------|-------------------|-------|
| `SMA` | Simple Moving Average | Einfacher gleitender Durchschnitt | `period=20` | Blau |
| `EMA` | Exponential Moving Average | Exponentiell gewichteter Durchschnitt | `period=20` | Orange |
| `BB` | Bollinger Bands | Volatilitätsbänder um SMA | `period=20`, `std=2` | Grau |

### 6.2 Oszillator-Indikatoren (separate Panels)

Diese Indikatoren werden in eigenen Panels unter dem Preis-Chart angezeigt:

| ID | Name | Beschreibung | Standard-Parameter | Min | Max |
|----|------|--------------|-------------------|-----|-----|
| `RSI` | Relative Strength Index | Momentum-Oszillator (Überkauft/Überverkauft) | `period=14` | 0 | 100 |
| `MACD` | Moving Average Convergence Divergence | Trend-Momentum mit Histogramm | `fast=12`, `slow=26`, `signal=9` | - | - |
| `STOCH` | Stochastic Oscillator | Kurs-Position im Bereich | `k_period=14`, `d_period=3` | 0 | 100 |
| `ATR` | Average True Range | Volatilitätsindikator | `period=14` | 0 | - |
| `ADX` | Average Directional Index | Trendstärke | `period=14` | 0 | 100 |
| `CCI` | Commodity Channel Index | Zyklischer Oszillator | `period=20` | -100 | 100 |
| `MFI` | Money Flow Index | Volumengewichteter RSI | `period=14` | 0 | 100 |
| `BB_WIDTH` | Bollinger Bandwidth | Breite der Bollinger Bänder | `period=20`, `std=2` | 0 | - |
| `BB_PERCENT` | Bollinger %B | Position innerhalb der Bänder | `period=20`, `std=2` | 0 | 1.2 |

### 6.3 Alle implementierten Indikatoren (Engine)

Die Indicator Engine unterstützt insgesamt **28 Indikatoren** in 5 Kategorien:

#### 6.3.1 Trend-Indikatoren (8)

| Type | ID | Name | Beschreibung | Parameter |
|------|-----|------|--------------|-----------|
| `IndicatorType.SMA` | `sma` | Simple Moving Average | Einfacher gleitender Durchschnitt | `period: int` |
| `IndicatorType.EMA` | `ema` | Exponential Moving Average | Exponentiell gewichteter Durchschnitt | `period: int` |
| `IndicatorType.WMA` | `wma` | Weighted Moving Average | Linear gewichteter Durchschnitt | `period: int` |
| `IndicatorType.VWMA` | `vwma` | Volume Weighted Moving Average | Volumengewichteter Durchschnitt | `period: int` |
| `IndicatorType.MACD` | `macd` | Moving Average Convergence Divergence | Trend-Momentum-Indikator | `fast: int`, `slow: int`, `signal: int` |
| `IndicatorType.ADX` | `adx` | Average Directional Index | Trendstärke (0-100) | `period: int` |
| `IndicatorType.PSAR` | `psar` | Parabolic SAR | Trend-Umkehr-Punkte | `af: float`, `max_af: float` |
| `IndicatorType.ICHIMOKU` | `ichimoku` | Ichimoku Cloud | Komplex-Trend-System | `tenkan: int`, `kijun: int`, `senkou: int` |

#### 6.3.2 Momentum-Indikatoren (7)

| Type | ID | Name | Beschreibung | Parameter |
|------|-----|------|--------------|-----------|
| `IndicatorType.RSI` | `rsi` | Relative Strength Index | Momentum (0-100) | `period: int` |
| `IndicatorType.STOCH` | `stoch` | Stochastic Oscillator | %K und %D Linien | `k_period: int`, `d_period: int` |
| `IndicatorType.MOM` | `mom` | Momentum | Preisänderung über N Perioden | `period: int` |
| `IndicatorType.ROC` | `roc` | Rate of Change | Prozentuale Preisänderung | `period: int` |
| `IndicatorType.WILLR` | `willr` | Williams %R | Überkauft/Überverkauft (-100 bis 0) | `period: int` |
| `IndicatorType.CCI` | `cci` | Commodity Channel Index | Zyklus-Indikator | `period: int` |
| `IndicatorType.MFI` | `mfi` | Money Flow Index | Volumen-RSI (0-100) | `period: int` |

#### 6.3.3 Volatilitäts-Indikatoren (7)

| Type | ID | Name | Beschreibung | Parameter |
|------|-----|------|--------------|-----------|
| `IndicatorType.BB` | `bb` | Bollinger Bands | Oberes/Mittleres/Unteres Band | `period: int`, `std: float` |
| `IndicatorType.BB_WIDTH` | `bb_width` | Bollinger Bandwidth | Bandbreite (Volatilität) | `period: int`, `std: float` |
| `IndicatorType.BB_PERCENT` | `bb_percent` | Bollinger %B | Position im Band (0-1) | `period: int`, `std: float` |
| `IndicatorType.KC` | `kc` | Keltner Channels | ATR-basierte Kanäle | `period: int`, `atr_mult: float` |
| `IndicatorType.ATR` | `atr` | Average True Range | Volatilitätsmaß | `period: int` |
| `IndicatorType.NATR` | `natr` | Normalized ATR | ATR in Prozent | `period: int` |
| `IndicatorType.STD` | `std` | Standard Deviation | Standardabweichung | `period: int` |

#### 6.3.4 Volumen-Indikatoren (5)

| Type | ID | Name | Beschreibung | Parameter |
|------|-----|------|--------------|-----------|
| `IndicatorType.OBV` | `obv` | On-Balance Volume | Kumuliertes Volumen nach Richtung | - |
| `IndicatorType.CMF` | `cmf` | Chaikin Money Flow | Geldfluss-Indikator | `period: int` |
| `IndicatorType.AD` | `ad` | Accumulation/Distribution | Akkumulation/Distribution | - |
| `IndicatorType.FI` | `fi` | Force Index | Preis × Volumen-Änderung | `period: int` |
| `IndicatorType.VWAP` | `vwap` | Volume Weighted Average Price | Volumengewichteter Durchschnittspreis | - |

#### 6.3.5 Custom-Indikatoren (3)

| Type | ID | Name | Beschreibung | Parameter |
|------|-----|------|--------------|-----------|
| `IndicatorType.PIVOTS` | `pivots` | Pivot Points | Unterstützung/Widerstand aus HLC | `type: str` (classic/fibonacci) |
| `IndicatorType.SUPPORT_RESISTANCE` | `sup_res` | Support/Resistance Levels | Auto-erkannte Levels | `lookback: int`, `sensitivity: float` |
| `IndicatorType.PATTERN` | `pattern` | Price Patterns | Chartmuster-Erkennung | `patterns: list` |

### 6.4 Referenzlinien in Oszillatoren

| Indikator | Linien | Bedeutung |
|-----------|--------|-----------|
| **RSI** | 30 (rot), 50 (grau), 70 (grün) | Überverkauft, Neutral, Überkauft |
| **STOCH** | 20 (rot), 80 (grün) | Überverkauft, Überkauft |
| **CCI** | -100 (rot), 0 (grau), +100 (grün) | Untere/Mittel/Obere Grenze |
| **MACD** | 0 (grau) | Nulllinie für Histogramm |

### 6.5 MACD-Komponenten

Der MACD wird mit 3 Serien angezeigt:

| Serie | Farbe | Beschreibung |
|-------|-------|--------------|
| `macd` (Line) | #2962FF (Blau) | MACD-Linie (Fast EMA - Slow EMA) |
| `signal` (Line) | #FF6D00 (Orange) | Signal-Linie (EMA des MACD) |
| `histogram` (Bars) | #26a69a / #ef5350 | Histogramm (Grün positiv, Rot negativ) |

### 6.6 Indikator-Konfiguration (JSON-Schema für Einstellungsseite)

```json
{
  "indicators": {
    "overlay": {
      "SMA": {
        "enabled": false,
        "instances": [
          { "period": 20, "color": "#2196F3" },
          { "period": 50, "color": "#FF9800" },
          { "period": 200, "color": "#9C27B0" }
        ]
      },
      "EMA": {
        "enabled": true,
        "instances": [
          { "period": 20, "color": "#4CAF50" }
        ]
      },
      "BB": {
        "enabled": false,
        "period": 20,
        "std_dev": 2.0,
        "color": "#607D8B"
      }
    },
    "oscillator": {
      "RSI": {
        "enabled": true,
        "period": 14,
        "overbought": 70,
        "oversold": 30,
        "color": "#9C27B0"
      },
      "MACD": {
        "enabled": true,
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
        "macd_color": "#2962FF",
        "signal_color": "#FF6D00",
        "histogram_pos_color": "#26a69a",
        "histogram_neg_color": "#ef5350"
      },
      "STOCH": {
        "enabled": false,
        "k_period": 14,
        "d_period": 3,
        "color": "#00BCD4"
      },
      "ATR": {
        "enabled": false,
        "period": 14,
        "color": "#795548"
      },
      "ADX": {
        "enabled": false,
        "period": 14,
        "trend_threshold": 20,
        "color": "#E91E63"
      },
      "CCI": {
        "enabled": false,
        "period": 20,
        "color": "#3F51B5"
      },
      "MFI": {
        "enabled": false,
        "period": 14,
        "color": "#009688"
      }
    }
  }
}
```

### 6.7 Verwendung im UI (Dropdown-Menü)

Das Indikator-Dropdown im Chart-Fenster ermöglicht:

| Aktion | Beschreibung |
|--------|--------------|
| **Hinzufügen** | Klick auf Indikator-Name aktiviert ihn |
| **Entfernen** | Erneuter Klick deaktiviert ihn |
| **Mehrfach-Instanzen** | Gleicher Indikator mit verschiedenen Parametern |
| **Badge-Anzeige** | Button zeigt Anzahl aktiver Indikatoren |
| **Aktive Liste** | Separate Menüsektion für aktive Indikatoren |

---

## 7. Datei-Referenzen

| Komponente | Datei | Zeilen |
|------------|-------|--------|
| Bot Engine | `src/core/trading_bot/bot_engine.py` | 1-1100 |
| Signal Generator | `src/core/trading_bot/signal_generator.py` | 1-550 |
| AI Validator | `src/core/trading_bot/ai_validator.py` | 1-850 |
| Risk Manager | `src/core/trading_bot/risk_manager.py` | 1-607 |
| Position Monitor | `src/core/trading_bot/position_monitor.py` | 1-591 |
| Strategy Config | `src/core/trading_bot/strategy_config.py` | 1-400 |
| Trade Logger | `src/core/trading_bot/trade_logger.py` | 1-300 |
| Indicator Registry | `src/core/indicators/registry.py` | 1-77 |
| Indicator Engine | `src/core/indicators/engine.py` | 1-171 |
| Indicator Types | `src/core/indicators/types.py` | 1-75 |
| Indicator Mixin | `src/ui/widgets/chart_mixins/indicator_mixin.py` | 1-677 |
| Strategy Config JSON | `config/trading_bot/strategy_config.json` | 1-380 |

---

## 8. Zusammenfassung

| Kategorie | Anzahl |
|-----------|--------|
| AI-Analyse-Funktionen | 7 |
| Technische Indikatoren (Bot) | 6 |
| Signal-Generierungs-Funktionen | 5 |
| Regime-Typen | 6 |
| Prompt-Templates | 2 |
| Setup-Typen (AI) | 10 |
| AI-Konfigurationsparameter | 7 |
| AI Provider | 3 |
| Bot States | 10 |
| Entry-Bedingungen (Long) | 6 |
| Entry-Bedingungen (Short) | 6 |
| Exit-Trigger | 8 |
| Risk-Manager-Funktionen | 6 |
| Position-Monitor-Funktionen | 6 |
| Timeframes | 4 |
| **Chart-Indikatoren (Engine)** | **28** |
| Overlay-Indikatoren (Dropdown) | 3 |
| Oszillator-Indikatoren (Dropdown) | 9 |
| UI-Einstellungsvariablen | 22 |

---

> **Hinweis für KI-Systeme:** Diese Dokumentation verwendet konsistentes Markdown-Format mit Tabellen, Code-Blöcken und hierarchischer Struktur. Alle Funktionen sind mit Datei-Pfaden und Zeilennummern referenziert. JSON-Schemas sind vollständig und validierbar.
