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

logger = logging.getLogger(__name__)


class CelAIHelper:
    """AI-Helper für CEL Code-Generierung."""

    def __init__(self):
        """Initialisiere AI-Helper mit aktuellen Settings."""
        self.settings = QSettings("OrderPilot-AI", "OrderPilot-AI")
        self._load_ai_settings()
        self._openai_client: Optional[AsyncOpenAI] = None

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

    def get_current_provider_config(self) -> Dict[str, Any]:
        """Hole aktuelle Provider-Konfiguration.

        Returns:
            Dict mit provider, model, api_key
        """
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
            "update_stop": "STOP UPDATE LOGIC: When to move trailing stop loss"
        }

        prompt = f"""You are a CEL (Common Expression Language) code generator for trading strategies.

TASK: Generate a CEL expression for a {workflow_type.upper()} workflow.

WORKFLOW TYPE: {workflow_descriptions.get(workflow_type, workflow_type)}
PATTERN: {pattern_name}
STRATEGY: {strategy_description}

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
   - is_trade_open(): Check if trade is currently open
   - is_long(): Check if current trade is LONG
   - is_short(): Check if current trade is SHORT
   - stop_hit_long(): Check if long stop loss was hit
   - stop_hit_short(): Check if short stop loss was hit
   - tp_hit(): Check if take profit was hit
   - price_above_ema(period): Check if price > EMA
   - price_below_ema(period): Check if price < EMA

3. MATH FUNCTIONS:
   - abs(value): Absolute value
   - min(a, b): Minimum of two values
   - max(a, b): Maximum of two values
   - round(value): Round to nearest integer
   - sqrt(value): Square root
   - pow(x, y): x to the power of y

4. TYPE/NULL FUNCTIONS:
   - isnull(value): Check if null
   - isnotnull(value): Check if not null
   - nz(value, default): Replace null with default
   - coalesce(a, b, c): First non-null value
   - clamp(value, min, max): Constrain value to range

5. ARRAY FUNCTIONS:
   - has(array, element): Array contains element
   - size(array): Array length
   - all(array, condition): All elements match
   - any(array, condition): Any element matches

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

Exit (Take Profit):
rsi14.value > 70 || trade.pnl_pct > 3.0

Exit (Stop Loss):
stop_hit_long() || stop_hit_short()

Before Exit (Partial Close):
trade.pnl_pct > 2.0 && is_trade_open()

Update Stop (Breakeven):
trade.pnl_pct > 1.0

Update Stop (Trailing):
trade.pnl_pct > 2.0 && ema34.value > ema89.value

REQUIREMENTS:
1. Return ONLY the CEL expression, NO explanation or markdown
2. Use correct syntax (&&, ||, !, ==, etc.)
3. Use available indicators and functions ONLY
4. Make expression specific to the pattern and workflow type
5. Consider strategy description and best practices
6. Keep expression readable (use line breaks if complex)

GENERATE CEL EXPRESSION NOW:"""

        if context:
            prompt += f"\n\nADDITIONAL CONTEXT: {context}"

        return prompt

    async def _generate_with_anthropic(
        self,
        prompt: str,
        config: Dict[str, Any]
    ) -> Optional[str]:
        """Generiere CEL Code mit Anthropic Claude.

        Args:
            prompt: Generation-Prompt
            config: Provider-Konfiguration

        Returns:
            Generierter CEL Code
        """
        # TODO: Implementierung in Phase 2
        # Verwendet anthropic Python SDK
        logger.warning("Anthropic CEL generation not yet implemented (Phase 2)")
        return None

    async def _generate_with_openai(
        self,
        prompt: str,
        config: Dict[str, Any]
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
            if model.startswith("gpt-5"):
                # GPT-5.x: reasoning_effort
                response = await self._openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a CEL (Common Expression Language) code generator "
                                     "specialized in trading strategy expressions. "
                                     "Return ONLY valid CEL code, no explanations."
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
                            "content": "You are a CEL (Common Expression Language) code generator "
                                     "specialized in trading strategy expressions. "
                                     "Return ONLY valid CEL code, no explanations."
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
        config: Dict[str, Any]
    ) -> Optional[str]:
        """Generiere CEL Code mit Google Gemini.

        Args:
            prompt: Generation-Prompt
            config: Provider-Konfiguration

        Returns:
            Generierter CEL Code
        """
        # TODO: Implementierung in Phase 2
        # Verwendet google-generativeai Python SDK
        logger.warning("Gemini CEL generation not yet implemented (Phase 2)")
        return None
