"""CEL AI Helper - AI-gestützte CEL Code-Generierung.

Verwendet die konfigurierten AI-Settings aus dem Hauptfenster.
API-Keys werden aus Windows Systemvariablen geladen.
"""

from __future__ import annotations

import os
import re
import logging
from typing import Optional, Dict, Any
from PyQt6.QtCore import QSettings

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

logger = logging.getLogger(__name__)


class CelAIHelper:
    """AI-Helper für CEL Code-Generierung."""

    def __init__(self):
        """Initialisiere AI-Helper mit aktuellen Settings."""
        self.settings = QSettings("OrderPilot", "TradingApp")
        self._load_ai_settings()
        self._openai_client: Optional[AsyncOpenAI] = None
        self._anthropic_client: Optional[anthropic.AsyncAnthropic] = None

    def _load_ai_settings(self) -> None:
        """Lade AI-Settings aus QSettings."""
        # AI aktiviert?
        self.ai_enabled = self.settings.value("ai_enabled", True, type=bool)

        # Default Provider (Anthropic, OpenAI, Gemini)
        self.default_provider = self.settings.value("ai_default_provider", "Anthropic")

        # Modell-Auswahl (mit Display-Text)
        self.openai_model_display = self.settings.value("openai_model", "gpt-5.1 (GPT-5.1)")
        self.anthropic_model_display = self.settings.value(
            "anthropic_model",
            "claude-sonnet-4-5-20250929 (Recommended)"
        )
        self.gemini_model_display = self.settings.value(
            "gemini_model",
            "gemini-2.0-flash-exp (Latest)"
        )

        # Extrahiere Modell-IDs (ohne Display-Text in Klammern)
        self.openai_model = self._extract_model_id(self.openai_model_display)
        self.anthropic_model = self._extract_model_id(self.anthropic_model_display)
        self.gemini_model = self._extract_model_id(self.gemini_model_display)

        # API-Keys aus Windows Systemvariablen
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")

        logger.info(
            f"AI Settings loaded: Provider={self.default_provider}, "
            f"OpenAI={self.openai_model}, "
            f"Anthropic={self.anthropic_model}, "
            f"Gemini={self.gemini_model}"
        )

    def _extract_model_id(self, display_text: str) -> str:
        """Extrahiere Modell-ID aus Display-Text.

        Args:
            display_text: z.B. "gpt-5.1 (GPT-5.1)" oder "claude-sonnet-4-5-20250929 (Recommended)"

        Returns:
            Modell-ID ohne Klammern, z.B. "gpt-5.1" oder "claude-sonnet-4-5-20250929"
        """
        # Entferne Text in Klammern
        model_id = re.sub(r'\s*\(.*?\)\s*', '', display_text).strip()
        return model_id

    def _get_available_variables_list(self) -> str:
        """Erstelle Liste aller verfügbaren Variablen für AI Prompt.

        Diese Liste basiert auf:
        - ChartDataProvider (chart.*)
        - BotConfigProvider (bot.*)
        - ProjectVariables (project.* - aus .cel_variables.json)

        Returns:
            Formatierte Liste mit Variablen-Kategorien
        """
        return """
AVAILABLE VARIABLES (organized by namespace):

1. BOT VARIABLES (bot.*):
   Trading Configuration:
   - bot.symbol: Trading symbol (e.g., "BTCUSDT")
   - bot.leverage: Trading leverage (e.g., 10)
   - bot.paper_mode: Is paper trading? (always True)

   Risk Management:
   - bot.risk_per_trade_pct: Risk per trade in % (e.g., 2.0)
   - bot.max_daily_loss_pct: Max daily loss in % (e.g., 10.0)
   - bot.max_position_size_btc: Max position size in BTC

   Stop Loss & Take Profit:
   - bot.sl_atr_multiplier: Stop Loss ATR multiplier (e.g., 2.0)
   - bot.tp_atr_multiplier: Take Profit ATR multiplier (e.g., 3.0)
   - bot.trailing_stop_enabled: Trailing stop enabled (true/false)
   - bot.trailing_stop_atr_mult: Trailing stop ATR multiplier
   - bot.trailing_stop_activation_pct: Trailing stop activation % (e.g., 2.0)

   Signal Generation:
   - bot.min_confluence_score: Minimum confluence score (e.g., 3)
   - bot.require_regime_alignment: Require regime alignment (true/false)

   Timing:
   - bot.analysis_interval_sec: Analysis interval in seconds
   - bot.position_check_interval_ms: Position check interval in ms
   - bot.macro_update_interval_min: Macro update interval in minutes
   - bot.trend_update_interval_min: Trend update interval in minutes

   Session Management:
   - bot.session.enabled: Session management enabled (true/false)
   - bot.session.start_utc: Session start time (UTC, e.g., "08:00")
   - bot.session.end_utc: Session end time (UTC, e.g., "16:00")
   - bot.session.close_at_end: Close positions at session end (true/false)

   AI Configuration:
   - bot.ai.enabled: AI validation enabled (true/false)
   - bot.ai.confidence_threshold: AI confidence threshold (0-100)
   - bot.ai.min_confluence_for_ai: Min confluence to trigger AI (e.g., 3)
   - bot.ai.fallback_to_technical: Fallback to technical analysis (true/false)

2. CHART VARIABLES (chart.*):
   Current Candle (OHLCV):
   - chart.price: Current close price (USD)
   - chart.open: Current open price (USD)
   - chart.high: Current high price (USD)
   - chart.low: Current low price (USD)
   - chart.volume: Current volume (BTC)

   Chart Info:
   - chart.symbol: Trading symbol (e.g., "BTCUSDT")
   - chart.timeframe: Chart timeframe (e.g., "1h", "4h", "1d")
   - chart.candle_count: Number of loaded candles (int)

   Candle Analysis:
   - chart.range: High-Low range (USD)
   - chart.body: Absolute candle body size (USD)
   - chart.is_bullish: Is current candle bullish? (bool)
   - chart.is_bearish: Is current candle bearish? (bool)
   - chart.upper_wick: Upper wick size (USD)
   - chart.lower_wick: Lower wick size (USD)

   Previous Candle:
   - chart.prev_close: Previous candle close (USD)
   - chart.prev_high: Previous candle high (USD)
   - chart.prev_low: Previous candle low (USD)
   - chart.change: Price change from previous candle (USD)
   - chart.change_pct: Price change percentage (%)

3. MARKET VARIABLES (current candle):
   Price & Volume:
   - close: Current close price
   - open: Current open price
   - high: Current high price
   - low: Current low price
   - volume: Current volume

   Volatility & Regime:
   - atrp: ATR in percent (volatility measure)
   - regime: Current market regime (string, e.g., "R0", "R1", "R2", "R3", "R4")
   - direction: Trend direction (UP/DOWN/NONE)
   - squeeze_on: Bollinger squeeze active (bool)

4. TRADE VARIABLES (trade.*):
   Position Info:
   - trade.entry_price: Entry price
   - trade.current_price: Current market price
   - trade.stop_price: Current stop loss price
   - trade.side: Trade side (long/short)
   - trade.leverage: Trade leverage

   Performance:
   - trade.pnl_pct: Profit/Loss in %
   - trade.pnl_usdt: Profit/Loss in USDT
   - trade.fees_pct: Fees in %

   Duration:
   - trade.bars_in_trade: Bars since entry

5. CONFIG VARIABLES (cfg.*):
   Trading Rules:
   - cfg.min_volume_pctl: Minimum volume percentile (e.g., 20.0)
   - cfg.min_atrp_pct: Minimum ATR % (e.g., 0.5)
   - cfg.max_atrp_pct: Maximum ATR % (e.g., 5.0)
   - cfg.max_leverage: Maximum allowed leverage (e.g., 10)
   - cfg.max_fees_pct: Maximum fee % (e.g., 0.2)
   - cfg.no_trade_regimes: Array of blocked regimes (e.g., ["R0", "R4"])

6. PROJECT VARIABLES (project.*):
   Custom Variables from .cel_variables.json:
   - project.*: User-defined variables with custom values
   - Define in Variables UI to create project-specific constants
   - Example: project.entry_min_price, project.max_drawdown_pct

IMPORTANT NOTES:
- Use chart.* for current market data (OHLCV)
- Use bot.* for bot configuration and risk management
- Use trade.* for active position information
- Use cfg.* for strategy-level configuration
- Use project.* for custom project-specific constants
- All percentages are in decimal form (e.g., 2.0 = 2%)
- Use null-safe operators when accessing potentially missing values
"""

    def get_current_provider_config(self) -> Dict[str, Any]:
        """Hole aktuelle Provider-Konfiguration.

        Returns:
            Dict mit provider, model, api_key
        """
        # Reload settings on each call to honor latest user selection
        self._load_ai_settings()

        if not self.ai_enabled:
            logger.warning("AI features disabled in settings")
            return {
                "enabled": False,
                "provider": None,
                "model": None,
                "api_key": None
            }

        # Bestimme aktiven Provider und Model
        if self.default_provider == "Anthropic":
            provider = "anthropic"
            model = self.anthropic_model
            api_key = self.anthropic_api_key
        elif self.default_provider == "OpenAI":
            provider = "openai"
            model = self.openai_model
            api_key = self.openai_api_key
        elif self.default_provider == "Gemini":
            provider = "gemini"
            model = self.gemini_model
            api_key = self.gemini_api_key
        else:
            logger.error(f"Unknown provider: {self.default_provider}")
            return {
                "enabled": False,
                "provider": None,
                "model": None,
                "api_key": None
            }

        # Prüfe API-Key
        if not api_key:
            logger.warning(
                f"{provider.upper()}_API_KEY not found in environment variables"
            )

        return {
            "enabled": True,
            "provider": provider,
            "model": model,
            "api_key": api_key,
            "display_name": f"{provider.title()} {model}"
        }

    async def generate_cel_code(
        self,
        workflow_type: str,
        pattern_name: str,
        strategy_description: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """Generiere CEL Code mit AI.

        Args:
            workflow_type: "entry", "exit", "before_exit", "update_stop"
            pattern_name: Pattern-Name (z.B. "Pin Bar (Bullish)")
            strategy_description: Strategie-Beschreibung aus PatternStrategyMapping
            context: Zusätzlicher Kontext (optional)

        Returns:
            Generierter CEL Code oder None bei Fehler
        """
        config = self.get_current_provider_config()

        if not config["enabled"]:
            logger.error("AI features disabled, cannot generate CEL code")
            return None

        if not config["api_key"]:
            logger.error(f"API key missing for {config['provider']}")
            return None

        # Baue Prompt
        prompt = self._build_cel_generation_prompt(
            workflow_type,
            pattern_name,
            strategy_description,
            context
        )

        # Rufe entsprechenden AI-Provider auf
        try:
            if config["provider"] == "anthropic":
                return await self._generate_with_anthropic(prompt, config)
            elif config["provider"] == "openai":
                return await self._generate_with_openai(prompt, config)
            elif config["provider"] == "gemini":
                return await self._generate_with_gemini(prompt, config)
            else:
                logger.error(f"Unknown provider: {config['provider']}")
                return None

        except Exception as e:
            logger.error(f"CEL generation failed: {e}")
            return None

    async def explain_cel_code(
        self,
        cel_code: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """Explain a CEL expression with AI.

        Args:
            cel_code: CEL expression to explain
            context: Optional additional context

        Returns:
            Explanation text or None on error
        """
        config = self.get_current_provider_config()

        if not config["enabled"]:
            logger.error("AI features disabled, cannot explain CEL code")
            return None

        if not config["api_key"]:
            logger.error(f"API key missing for {config['provider']}")
            return None

        prompt = self._build_cel_explain_prompt(cel_code, context)
        system_message = (
            "You are a CEL (Common Expression Language) assistant for trading strategies. "
            "Explain the expression in plain language, highlight key conditions, and "
            "mention potential pitfalls (e.g., missing guard conditions). "
            "Be concise and structured."
        )

        try:
            if config["provider"] == "anthropic":
                return await self._generate_with_anthropic(prompt, config, system_message)
            elif config["provider"] == "openai":
                return await self._generate_with_openai(prompt, config, system_message)
            elif config["provider"] == "gemini":
                return await self._generate_with_gemini(prompt, config, system_message)
            else:
                logger.error(f"Unknown provider: {config['provider']}")
                return None
        except Exception as e:
            logger.error(f"CEL explanation failed: {e}")
            return None

    def _build_cel_generation_prompt(
        self,
        workflow_type: str,
        pattern_name: str,
        strategy_description: str,
        context: Optional[str]
    ) -> str:
        """Baue Prompt für CEL Code-Generierung.

        Args:
            workflow_type: "entry", "exit", "before_exit", "update_stop"
            pattern_name: Pattern-Name
            strategy_description: Strategie-Beschreibung
            context: Zusätzlicher Kontext

        Returns:
            Vollständiger Prompt für AI
        """
        workflow_descriptions = {
            "entry": "ENTRY CONDITIONS: When to enter a trade (buy/sell signal)",
            "exit": "EXIT CONDITIONS: When to close an open trade (take profit or stop loss)",
            "before_exit": "BEFORE EXIT LOGIC: Actions before closing (e.g., partial close, warnings)",
            "update_stop": "STOP UPDATE LOGIC: When to move trailing stop loss",
            "no_entry": "NO ENTRY FILTER: Conditions that prevent trade entries (blackout periods, high volatility, news events, bad market conditions)"
        }

        prompt = f"""You are a CEL (Common Expression Language) code generator for trading strategies.

TASK: Generate a CEL expression for a {workflow_type.upper()} workflow.

WORKFLOW TYPE: {workflow_descriptions.get(workflow_type, workflow_type)}
PATTERN: {pattern_name}
STRATEGY: {strategy_description}

{self._get_available_variables_list()}

AVAILABLE CEL FUNCTIONS AND SYNTAX:

1. INDICATORS (18 types):
   - RSI: rsi5.value, rsi7.value, rsi14.value, rsi21.value
   - EMA: ema8.value, ema21.value, ema34.value, ema50.value, ema89.value, ema200.value
   - SMA: sma20.value, sma50.value, sma100.value, sma200.value
   - MACD: macd_12_26_9.value, macd_12_26_9.signal, macd_12_26_9.histogram
   - Stochastic: stoch_5_3_3.k, stoch_5_3_3.d, stoch_14_3_3.k, stoch_14_3_3.d
   - ADX: adx14.value, adx14.plus_di, adx14.minus_di
   - ATR: atr14.value
   - Bollinger Bands: bb_20_2.upper, bb_20_2.middle, bb_20_2.lower, bb_20_2.width
   - CCI: cci20.value
   - MFI: mfi14.value
   - Volume: volume_ratio_20.value
   - Momentum: momentum_score_14.value, price_strength_14.value
   - CHOP: chop14.value

2. TRADING FUNCTIONS:
   - is_trade_open(trade): Check if trade is currently open
   - is_long(trade): Check if current trade is LONG
   - is_short(trade): Check if current trade is SHORT
   - is_bullish_signal(strategy): Bullish bias check
   - is_bearish_signal(strategy): Bearish bias check
   - in_regime(regime, 'R1'): Regime match
   - stop_hit_long(trade, current_price): Long stop loss hit
   - stop_hit_short(trade, current_price): Short stop loss hit
   - tp_hit(trade, current_price): Take profit hit
   - price_above_ema(price, ema_value): Price > EMA
   - price_below_ema(price, ema_value): Price < EMA
   - price_above_level(price, level): Price > level
   - price_below_level(price, level): Price < level
   - pct_change(old, new): Percent change
   - pct_from_level(price, level): Percent distance to level
   - level_at_pct(entry, pct, side): Level at percent
   - retracement(from, to, pct): Retracement level
   - extension(from, to, pct): Extension level
   - pctl(series, percentile): Series percentile
   - crossover(series1, series2): Cross-over
   - highest(series, period): Highest over period
   - lowest(series, period): Lowest over period
   - sma(series, period): Simple moving average
   - pin_bar_bullish(), pin_bar_bearish(), inside_bar(), inverted_hammer()
   - bull_flag(), bear_flag(), cup_and_handle(), double_bottom(), double_top()
   - ascending_triangle(), descending_triangle()
   - breakout_above(), breakdown_below(), false_breakout(), break_of_structure()
   - liquidity_swept(), fvg_exists(), order_block_retest(), harmonic_pattern_detected()

3. MATH FUNCTIONS:
   - abs(value): Absolute value
   - min(a, b): Minimum of two values
   - max(a, b): Maximum of two values
   - round(value, decimals): Round to decimals
   - floor(value): Round down
   - ceil(value): Round up
   - sqrt(value): Square root
   - pow(x, y): x to the power of y
   - exp(value): e^x

4. TYPE/NULL FUNCTIONS:
   - type(value): Type name
   - string(value): Convert to string
   - int(value): Convert to int
   - double(value): Convert to float
   - bool(value): Convert to bool
   - isnull(value): Check if null
   - nz(value, default): Replace null with default
   - coalesce(a, b, c): First non-null value
   - clamp(value, min, max): Constrain value to range

5. ARRAY FUNCTIONS:
   - has(array, element): Array contains element
   - size(array) / length(array): Array length
   - all(array, condition): All elements match (truthy list)
   - any(array, condition): Any element matches (truthy list)
   - map(array, expr): Transform array (limited)
   - filter(array, condition): Filter array (limited)
   - first(array), last(array): First/last element
   - indexOf(array, element): Index of element
   - slice(array, start, end): Slice array
   - distinct(array), sort(array), reverse(array)
   - sum(array), avg(array), average(array)

6. LOGIC OPERATORS:
   - Comparison: ==, !=, <, >, <=, >=
   - Boolean: && (AND), || (OR), ! (NOT)
   - Ternary: condition ? value_if_true : value_if_false

7. TRADE VARIABLES:
   - trade.entry_price: Entry price of current trade
   - trade.current_price: Current market price
   - trade.stop_price: Current stop loss price
   - trade.pnl_pct: Profit/Loss in percent
   - trade.pnl_usdt: Profit/Loss in USDT
   - trade.side: Trade side (long/short)
   - trade.leverage: Trade leverage
   - trade.fees_pct: Fees in percent
   - trade.bars_in_trade: Bars since entry

8. MARKET VARIABLES:
   - close: Current close price
   - open: Current open price
   - high: Current high price
   - low: Current low price
   - volume: Current volume
   - atrp: ATR in percent
   - regime: Market regime (R0, R1, R2, R3, R4)
   - direction: Trend direction (UP/DOWN/NONE)
   - squeeze_on: Bollinger squeeze active

9. CONFIG VARIABLES:
   - cfg.min_volume_pctl: Minimum volume percentile
   - cfg.min_atrp_pct: Minimum ATR percent
   - cfg.max_atrp_pct: Maximum ATR percent
   - cfg.max_leverage: Maximum allowed leverage
   - cfg.max_fees_pct: Maximum fee percent
   - cfg.no_trade_regimes: Blocked regimes array

EXAMPLES:

Entry (Trend Following):
rsi14.value > 50 && ema34.value > ema89.value && macd_12_26_9.value > macd_12_26_9.signal && volume_ratio_20.value > 1.2

Entry (Mean Reversion):
rsi14.value < 30 && close < bb_20_2.lower && volume_ratio_20.value > 1.5

Entry (Regime-based):
!is_trade_open(trade) && (regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR')

No Entry (Volatility Filter):
atrp > cfg.max_atrp_pct || has(cfg.no_trade_regimes, regime)

Exit (Take Profit):
rsi14.value > 70 || trade.pnl_pct > 3.0

Exit (Stop Loss):
stop_hit_long(trade, close) || stop_hit_short(trade, close)

Before Exit (Partial Close):
trade.pnl_pct > 2.0 && is_trade_open(trade)

Update Stop (Breakeven):
trade.pnl_pct > 1.0

Update Stop (Trailing):
trade.pnl_pct > 2.0 && ema34.value > ema89.value

CRITICAL REQUIREMENTS:
1. Return ONLY a single CEL boolean expression - NO JSON objects, NO dictionaries
2. DO NOT return: {{ 'enter': ..., 'side': ..., 'stop_price': ... }} - This is WRONG
3. DO return: regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR' - This is CORRECT
4. Use correct CEL syntax (&&, ||, !, ==, etc.) - NOT Python/JSON syntax
5. Use available indicators and functions ONLY
6. Make expression specific to the pattern and workflow type
7. Keep expression readable (use line breaks if complex, but still a single expression)

WRONG EXAMPLES (DO NOT DO THIS):
❌ {{ 'enter': regime == 'EXTREME_BULL', 'side': 'long' }}
❌ return {{ enter: true, side: 'long' }}
❌ {{ enter: ..., stop_price: ... }}

CORRECT EXAMPLES (DO THIS):
✅ regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR'
✅ !is_trade_open(trade) && rsi14.value > 50
✅ (regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR') && !has(cfg.no_trade_regimes, regime)

GENERATE CEL EXPRESSION NOW:"""

        if context:
            prompt += f"\n\nADDITIONAL CONTEXT: {context}"

        return prompt

    def _build_cel_explain_prompt(self, cel_code: str, context: Optional[str]) -> str:
        """Build prompt for explaining CEL code."""
        prompt = (
            "Explain the following CEL expression used in a trading strategy. "
            "Use short bullet points and clarify what each clause does.\n\n"
            f"CEL EXPRESSION:\n{cel_code.strip()}"
        )
        if context:
            prompt += f"\n\nADDITIONAL CONTEXT: {context}"
        return prompt

    async def _generate_with_anthropic(
        self,
        prompt: str,
        config: Dict[str, Any],
        system_message: Optional[str] = None
    ) -> Optional[str]:
        """Generiere CEL Code mit Anthropic Claude.

        Args:
            prompt: Generation-Prompt
            config: Provider-Konfiguration

        Returns:
            Generierter CEL Code
        """
        if not ANTHROPIC_AVAILABLE:
            logger.error("Anthropic package not installed. Run: pip install anthropic")
            return None

        try:
            # Initialisiere Anthropic Client (lazy)
            if not self._anthropic_client:
                self._anthropic_client = anthropic.AsyncAnthropic(
                    api_key=config["api_key"]
                )

            model = config["model"]

            logger.info(f"Generating CEL code with Anthropic {model}")

            # API-Call mit Claude
            response = await self._anthropic_client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_message
                or (
                    "You are a CEL (Common Expression Language) code generator "
                    "specialized in trading strategy expressions. "
                    "Return ONLY a single CEL boolean expression, no explanations, no markdown, "
                    "and absolutely NO JSON objects or dictionaries. "
                    "DO NOT return structures like { 'enter': ..., 'side': ... }. "
                    "Return ONLY the expression itself."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extrahiere generierten Code
            cel_code = response.content[0].text.strip()

            # Entferne Markdown-Formatierung falls vorhanden
            if cel_code.startswith("```"):
                cel_code = cel_code.split("\n", 1)[1] if "\n" in cel_code else cel_code
                if cel_code.endswith("```"):
                    cel_code = cel_code.rsplit("```", 1)[0]
                cel_code = cel_code.strip()

            logger.info(
                f"Generated {len(cel_code)} chars CEL code "
                f"(input tokens: {response.usage.input_tokens}, "
                f"output tokens: {response.usage.output_tokens})"
            )

            return cel_code

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None

    async def _generate_with_openai(
        self,
        prompt: str,
        config: Dict[str, Any],
        system_message: Optional[str] = None
    ) -> Optional[str]:
        """Generiere CEL Code mit OpenAI GPT-5.2.

        Args:
            prompt: Generation-Prompt
            config: Provider-Konfiguration

        Returns:
            Generierter CEL Code
        """
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI package not installed. Run: pip install openai")
            return None

        try:
            # Initialisiere OpenAI Client (lazy)
            if not self._openai_client:
                self._openai_client = AsyncOpenAI(api_key=config["api_key"])

            # Hole Reasoning Effort aus Settings (für GPT-5.x)
            reasoning_effort = self.settings.value("openai_reasoning_effort", "medium")

            # Extrahiere nur Effort-Wert (ohne Display-Text)
            if "(" in reasoning_effort:
                reasoning_effort = reasoning_effort.split()[0]

            # Für GPT-5.x: reasoning_effort Parameter
            # Für GPT-4.1: temperature/top_p Parameter
            model = config["model"]

            logger.info(
                f"Generating CEL code with OpenAI {model} "
                f"(reasoning_effort={reasoning_effort})"
            )

            # API-Call mit GPT-5.2
            system_message = system_message or (
                "You are a CEL (Common Expression Language) code generator "
                "specialized in trading strategy expressions. "
                "Return ONLY a single CEL boolean expression, no explanations, no markdown, "
                "and absolutely NO JSON objects or dictionaries. "
                "DO NOT return structures like { 'enter': ..., 'side': ... }. "
                "Return ONLY the expression itself."
            )

            if model.startswith("gpt-5"):
                # GPT-5.x: reasoning_effort
                response = await self._openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_message
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_completion_tokens=2000,
                    reasoning_effort=reasoning_effort if reasoning_effort != "none" else None,
                    temperature=None if reasoning_effort != "none" else 0.1,
                    top_p=None if reasoning_effort != "none" else 1.0
                )
            else:
                # GPT-4.1: temperature/top_p
                temperature = self.settings.value("openai_temperature", 0.1, type=float)
                top_p = self.settings.value("openai_top_p", 1.0, type=float)

                response = await self._openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_message
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=2000,
                    temperature=temperature,
                    top_p=top_p
                )

            # Extrahiere generierten Code
            cel_code = response.choices[0].message.content.strip()

            # Entferne Markdown-Formatierung falls vorhanden
            if cel_code.startswith("```"):
                # Entferne ```cel oder ``` am Anfang und Ende
                cel_code = cel_code.split("\n", 1)[1] if "\n" in cel_code else cel_code
                if cel_code.endswith("```"):
                    cel_code = cel_code.rsplit("```", 1)[0]
                cel_code = cel_code.strip()

            logger.info(
                f"Generated {len(cel_code)} chars CEL code "
                f"(tokens: {response.usage.total_tokens})"
            )

            return cel_code

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    async def _generate_with_gemini(
        self,
        prompt: str,
        config: Dict[str, Any],
        system_message: Optional[str] = None
    ) -> Optional[str]:
        """Generiere CEL Code mit Google Gemini.

        Args:
            prompt: Generation-Prompt
            config: Provider-Konfiguration

        Returns:
            Generierter CEL Code
        """
        if not GEMINI_AVAILABLE:
            logger.error("Google Generative AI package not installed. Run: pip install google-generativeai")
            return None

        try:
            # Konfiguriere Gemini API
            genai.configure(api_key=config["api_key"])

            model = config["model"]

            logger.info(f"Generating CEL code with Google Gemini {model}")

            # Erstelle Model-Instanz
            gemini_model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_message
                or (
                    "You are a CEL (Common Expression Language) code generator "
                    "specialized in trading strategy expressions. "
                    "Return ONLY a single CEL boolean expression, no explanations, no markdown, "
                    "and absolutely NO JSON objects or dictionaries. "
                    "DO NOT return structures like { 'enter': ..., 'side': ... }. "
                    "Return ONLY the expression itself."
                )
            )

            # API-Call mit Gemini (synchron, da Gemini SDK kein async unterstützt)
            # Wir verwenden asyncio.to_thread für non-blocking Execution
            import asyncio
            response = await asyncio.to_thread(
                gemini_model.generate_content,
                prompt
            )

            # Extrahiere generierten Code
            cel_code = response.text.strip()

            # Entferne Markdown-Formatierung falls vorhanden
            if cel_code.startswith("```"):
                cel_code = cel_code.split("\n", 1)[1] if "\n" in cel_code else cel_code
                if cel_code.endswith("```"):
                    cel_code = cel_code.rsplit("```", 1)[0]
                cel_code = cel_code.strip()

            logger.info(f"Generated {len(cel_code)} chars CEL code with Gemini")

            return cel_code

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return None
