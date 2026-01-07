"""
AI Signal Validator - LLM-basierte Signal-Validierung

Verwendet OpenAI/Anthropic/Gemini APIs zur Validierung von Trading-Signalen.
Optional: Kann deaktiviert werden für rein technische Strategie.

Features:
- Multi-Provider Support (OpenAI, Anthropic, Gemini)
- Hierarchische Validierung (Quick -> Deep)
- Confidence Score (0-100)
- Setup-Typ Erkennung
- Reasoning für Nachvollziehbarkeit
- Fallback zu technischer Analyse bei API-Fehlern
- Models werden aus QSettings geladen (AI Analysis Einstellungen)

Hierarchische Validierung (Option A):
1. Confluence >= 4 -> Quick AI Overview (Model aus Settings)
2. Confidence >= 70% -> Trade ausführen
3. Confidence 50-70% -> Deep Analysis (Model aus Settings)
4. Confidence < 50% -> Signal überspringen
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from .signal_generator import TradeSignal
    from .trade_logger import IndicatorSnapshot, MarketContext

logger = logging.getLogger(__name__)


def get_model_from_settings(provider: str) -> str:
    """
    Holt das konfigurierte Model aus den QSettings basierend auf Provider.

    Die Models werden in der AI Analysis UI konfiguriert und entsprechen
    den in src/ai/model_constants.py definierten Modellen:
    - OpenAI: gpt-5.2, gpt-5.1, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano
    - Anthropic: claude-sonnet-4-5-20250929, claude-sonnet-4-5
    - Gemini: gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash

    Args:
        provider: "openai", "anthropic", oder "gemini"

    Returns:
        Model ID (z.B. "gpt-4.1-mini", "claude-sonnet-4-5")
    """
    try:
        from PyQt6.QtCore import QSettings
        settings = QSettings("OrderPilot", "OrderPilot-AI")

        # Settings Keys pro Provider
        model_keys = {
            "openai": "openai_model",
            "anthropic": "anthropic_model",
            "gemini": "gemini_model",
        }

        # Defaults müssen mit model_constants.py übereinstimmen!
        # KEINE hardcodierten alten Modelle wie gpt-4o!
        defaults = {
            "openai": "gpt-4.1-mini",      # Schnell und günstig
            "anthropic": "claude-sonnet-4-5",  # Aktuelles Modell
            "gemini": "gemini-1.5-flash",  # Schnelles Modell
        }

        provider_lower = provider.lower()
        key = model_keys.get(provider_lower, "openai_model")
        default = defaults.get(provider_lower, "gpt-4.1-mini")

        # Settings Wert holen (Format: "gpt-5.1 (GPT-5.1 Full)" oder "claude-sonnet-4-5 (Latest)")
        model_display = settings.value(key, default)

        if model_display:
            # Extract model ID from display name (before space or parenthesis)
            model_id = model_display.split(" ")[0].split("(")[0].strip()
            if model_id:
                logger.debug(f"Model from settings for {provider}: {model_id}")
                return model_id

        logger.debug(f"Using default model for {provider}: {default}")
        return default

    except Exception as e:
        logger.warning(f"Could not load model from settings: {e}, using default")
        # Fallback defaults
        defaults = {
            "openai": "gpt-4.1-mini",
            "anthropic": "claude-sonnet-4-5",
            "gemini": "gemini-1.5-flash",
        }
        return defaults.get(provider.lower(), "gpt-4.1-mini")


def get_provider_from_settings() -> str:
    """
    Holt den konfigurierten AI Provider aus den QSettings.

    Returns:
        Provider name ("openai", "anthropic", "gemini")
    """
    try:
        from PyQt6.QtCore import QSettings
        settings = QSettings("OrderPilot", "OrderPilot-AI")
        provider = settings.value("ai_provider", "OpenAI")
        # Normalize to lowercase
        return provider.lower() if provider else "openai"
    except Exception as e:
        logger.warning(f"Could not load provider from settings: {e}, using openai")
        return "openai"


class ValidationLevel(str, Enum):
    """Validierungsstufe."""
    QUICK = "quick"      # Schnelle Validierung (Model aus Settings)
    DEEP = "deep"        # Tiefe Analyse (Model aus Settings)
    TECHNICAL = "technical"  # Nur technisch (keine AI)
    BYPASS = "bypass"    # Übersprungen


@dataclass
class AIValidation:
    """Ergebnis der AI-Validierung."""

    approved: bool
    confidence_score: int  # 0-100
    setup_type: str | None  # z.B. "PULLBACK_EMA20", "BREAKOUT", "MEAN_REVERSION"
    reasoning: str
    provider: str
    model: str
    timestamp: datetime
    validation_level: ValidationLevel = ValidationLevel.QUICK
    deep_analysis_triggered: bool = False
    error: str | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "approved": self.approved,
            "confidence_score": self.confidence_score,
            "setup_type": self.setup_type,
            "reasoning": self.reasoning,
            "provider": self.provider,
            "model": self.model,
            "timestamp": self.timestamp.isoformat(),
            "validation_level": self.validation_level.value,
            "deep_analysis_triggered": self.deep_analysis_triggered,
            "error": self.error,
        }


class AISignalValidator:
    """
    Validiert Trading-Signale mittels LLM mit hierarchischer Validierung.

    Unterstützt:
    - OpenAI (GPT-5.x, GPT-4.1)
    - Anthropic (Claude Sonnet 4.5)
    - Google (Gemini 2.0, 1.5)

    WICHTIG: Modelle werden NICHT hardcodiert!
    Sie werden aus den QSettings geladen (File -> Settings -> AI).

    Hierarchische Validierung:
    1. Quick Validation bei Confluence >= 4
    2. Confidence >= 70% -> Trade
    3. Confidence 50-70% -> Deep Analysis
    4. Confidence < 50% -> Skip
    """

    # Setup-Typen die erkannt werden können
    SETUP_TYPES = [
        "PULLBACK_EMA20",
        "PULLBACK_EMA50",
        "BREAKOUT",
        "BREAKDOWN",
        "MEAN_REVERSION",
        "TREND_CONTINUATION",
        "SWING_FAILURE",
        "ABSORPTION",
        "DIVERGENCE",
        "NO_SETUP",
    ]

    def __init__(
        self,
        enabled: bool = True,
        confidence_threshold_trade: int = 70,
        confidence_threshold_deep: int = 50,
        deep_analysis_enabled: bool = True,
        fallback_to_technical: bool = True,
        timeout_seconds: int = 30,
    ):
        """
        Args:
            enabled: AI-Validierung aktiviert
            confidence_threshold_trade: Minimum Confidence für Trade (>=70%)
            confidence_threshold_deep: Minimum Confidence für Deep Analysis (>=50%)
            deep_analysis_enabled: Deep Analysis bei unsicheren Signalen
            fallback_to_technical: Bei API-Fehler technisches Signal verwenden
            timeout_seconds: API Timeout

        HINWEIS: Provider und Model werden aus QSettings geladen!
                 Einstellbar über: File -> Settings -> AI
        """
        self.enabled = enabled
        self.confidence_threshold_trade = confidence_threshold_trade
        self.confidence_threshold_deep = confidence_threshold_deep
        self.confidence_threshold = confidence_threshold_trade  # Backwards compatibility
        self.deep_analysis_enabled = deep_analysis_enabled
        self.fallback_to_technical = fallback_to_technical
        self.timeout_seconds = timeout_seconds

        # API Clients (lazy initialization)
        self._openai_client = None
        self._anthropic_client = None

        # AI Analysis Engine für Deep Analysis (lazy init)
        self._ai_analysis_engine = None

        # Log current settings
        provider = self.provider
        model = self.model
        logger.info(
            f"AISignalValidator initialized (Hierarchical). "
            f"Enabled: {enabled}, Provider: {provider}, Model: {model}, "
            f"Trade >= {confidence_threshold_trade}%, Deep >= {confidence_threshold_deep}%"
        )

    @property
    def provider(self) -> str:
        """Holt den aktuellen Provider aus den QSettings."""
        return get_provider_from_settings()

    @property
    def model(self) -> str:
        """Holt das aktuelle Model aus den QSettings basierend auf Provider."""
        return get_model_from_settings(self.provider)

    async def validate_signal(
        self,
        signal: "TradeSignal",
        indicators: "IndicatorSnapshot | None" = None,
        market_context: "MarketContext | None" = None,
    ) -> AIValidation:
        """
        Validiert ein Trading-Signal mittels LLM.

        Args:
            signal: Das zu validierende Signal
            indicators: Indikator-Snapshot
            market_context: Marktkontext

        Returns:
            AIValidation mit Confidence Score und Reasoning
        """
        if not self.enabled:
            return self._create_bypass_validation("AI validation disabled")

        try:
            # Prompt erstellen
            prompt = self._build_prompt(signal, indicators, market_context)

            # LLM aufrufen
            response = await self._call_llm(prompt)

            # Response parsen
            validation = self._parse_response(response)

            logger.info(
                f"AI validation complete: "
                f"Approved={validation.approved}, "
                f"Confidence={validation.confidence_score}%, "
                f"Setup={validation.setup_type}"
            )

            return validation

        except Exception as e:
            logger.error(f"AI validation failed: {e}")

            if self.fallback_to_technical:
                logger.info("Falling back to technical signal (AI error)")
                return self._create_fallback_validation(str(e))
            else:
                return AIValidation(
                    approved=False,
                    confidence_score=0,
                    setup_type=None,
                    reasoning="AI validation failed",
                    provider=self.provider,
                    model=self.model,
                    timestamp=datetime.now(timezone.utc),
                    error=str(e),
                )

    def _build_prompt(
        self,
        signal: "TradeSignal",
        indicators: "IndicatorSnapshot | None",
        market_context: "MarketContext | None",
    ) -> str:
        """Erstellt den LLM-Prompt."""
        # Signal Info
        signal_info = {
            "direction": signal.direction.value,
            "confluence_score": signal.confluence_score,
            "strength": signal.strength.value if hasattr(signal, "strength") else "UNKNOWN",
            "current_price": signal.current_price,
            "regime": signal.regime,
        }

        # Conditions
        conditions_met = [
            {"name": c.name, "description": c.description}
            for c in signal.conditions_met
        ]
        conditions_failed = [
            {"name": c.name, "description": c.description}
            for c in signal.conditions_failed
        ]

        # Indicators
        indicator_data = {}
        if indicators:
            indicator_data = {
                "rsi": indicators.rsi_14,
                "rsi_state": indicators.rsi_state,
                "ema_20": indicators.ema_20,
                "ema_50": indicators.ema_50,
                "ema_200": indicators.ema_200,
                "ema_20_distance_pct": indicators.ema_20_distance_pct,
                "macd_line": indicators.macd_line,
                "macd_signal": indicators.macd_signal,
                "macd_crossover": indicators.macd_crossover,
                "atr": indicators.atr_14,
                "atr_percent": indicators.atr_percent,
                "adx": indicators.adx_14,
                "bb_pct_b": indicators.bb_pct_b,
            }

        # Market Context
        context_data = {}
        if market_context:
            context_data = {
                "regime": market_context.regime,
                "trend_1d": market_context.trend_1d,
                "trend_4h": market_context.trend_4h,
                "trend_1h": market_context.trend_1h,
                "nearest_support": market_context.nearest_support,
                "nearest_resistance": market_context.nearest_resistance,
            }

        prompt = f"""Du bist ein erfahrener Crypto-Trading-Analyst. Analysiere dieses Trading-Signal und gib eine Bewertung ab.

## Signal Details
{json.dumps(signal_info, indent=2)}

## Erfüllte Bedingungen ({len(conditions_met)}/{len(conditions_met) + len(conditions_failed)})
{json.dumps(conditions_met, indent=2)}

## Nicht erfüllte Bedingungen
{json.dumps(conditions_failed, indent=2)}

## Technische Indikatoren
{json.dumps(indicator_data, indent=2)}

## Marktkontext
{json.dumps(context_data, indent=2)}

## Deine Aufgabe
1. Bewerte die Qualität dieses {signal.direction.value} Signals
2. Identifiziere den Setup-Typ
3. Gib einen Confidence Score (0-100)
4. Erkläre kurz dein Reasoning

## Antwort-Format (JSON)
{{
    "confidence_score": <0-100>,
    "setup_type": "<einer von: {', '.join(self.SETUP_TYPES)}>",
    "approved": <true/false>,
    "reasoning": "<kurze Erklärung>"
}}

Antworte NUR mit dem JSON, ohne weitere Erklärung."""

        return prompt

    async def _call_llm(self, prompt: str) -> dict[str, Any]:
        """Ruft das LLM auf."""
        if self.provider == "openai":
            return await self._call_openai(prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(prompt)
        elif self.provider == "gemini":
            return await self._call_gemini(prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    async def _call_openai(self, prompt: str) -> dict[str, Any]:
        """OpenAI API Call."""
        try:
            import openai

            if self._openai_client is None:
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                self._openai_client = openai.AsyncOpenAI(api_key=api_key)

            # Model aus Settings holen
            model = self.model
            logger.info(f"[OpenAI] Using model: {model}")

            # Basis-Parameter
            params = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional crypto trading analyst. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": 500,
                "timeout": self.timeout_seconds,
            }

            # GPT-5.x sind Reasoning Models - setze reasoning_effort für schnelle Antworten
            # GPT-5.2 und GPT-5.1 unterstützen: none, low, medium, high, xhigh
            # Für JSON-Responses brauchen wir kein Reasoning -> "none" für Geschwindigkeit
            if model.startswith("gpt-5"):
                params["reasoning_effort"] = "none"
                logger.info(f"[OpenAI] Reasoning model detected, setting reasoning_effort=none")
            else:
                # Non-reasoning models (gpt-4.1, etc.) use temperature
                params["temperature"] = 0.3

            response = await self._openai_client.chat.completions.create(**params)

            content = response.choices[0].message.content
            logger.debug(f"[OpenAI] Response: {content[:200] if content else 'EMPTY'}...")

            if not content:
                raise ValueError(f"OpenAI returned empty response for model '{model}'")

            # JSON aus Response extrahieren (falls Markdown-Wrapping)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except openai.BadRequestError as e:
            logger.error(f"[OpenAI] BadRequest for model '{model}': {e}")
            raise ValueError(f"OpenAI model '{model}' error: {e}")
        except openai.AuthenticationError as e:
            logger.error(f"[OpenAI] Authentication error: {e}")
            raise ValueError("OPENAI_API_KEY is invalid")
        except openai.NotFoundError as e:
            logger.error(f"[OpenAI] Model '{model}' not found: {e}")
            raise ValueError(f"Model '{model}' does not exist at OpenAI")
        except json.JSONDecodeError as e:
            logger.error(f"[OpenAI] JSON parse error: {e}. Content was: {content[:500] if content else 'None'}")
            raise ValueError(f"Could not parse OpenAI response as JSON: {e}")
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    async def _call_anthropic(self, prompt: str) -> dict[str, Any]:
        """Anthropic API Call."""
        try:
            import anthropic

            if self._anthropic_client is None:
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                self._anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)

            model = self.model
            logger.info(f"[Anthropic] Using model: {model}")

            response = await self._anthropic_client.messages.create(
                model=model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text
            logger.debug(f"[Anthropic] Response: {content[:200] if content else 'EMPTY'}...")

            if not content:
                raise ValueError(f"Anthropic returned empty response for model '{model}'")

            # JSON aus Response extrahieren (falls Markdown-Wrapping)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except anthropic.BadRequestError as e:
            logger.error(f"[Anthropic] BadRequest for model '{model}': {e}")
            raise ValueError(f"Anthropic model '{model}' error: {e}")
        except anthropic.AuthenticationError as e:
            logger.error(f"[Anthropic] Authentication error: {e}")
            raise ValueError("ANTHROPIC_API_KEY is invalid")
        except anthropic.NotFoundError as e:
            logger.error(f"[Anthropic] Model '{model}' not found: {e}")
            raise ValueError(f"Model '{model}' does not exist at Anthropic")
        except json.JSONDecodeError as e:
            logger.error(f"[Anthropic] JSON parse error: {e}. Content was: {content[:500] if content else 'None'}")
            raise ValueError(f"Could not parse Anthropic response as JSON: {e}")
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            )

    async def _call_gemini(self, prompt: str) -> dict[str, Any]:
        """Google Gemini API Call."""
        try:
            import google.generativeai as genai

            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get(
                "GEMINI_API_KEY"
            )
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set")

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.model)

            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=500,
                ),
            )

            content = response.text
            # Gemini kann Markdown zurückgeben, extrahiere JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            )

    def _parse_response(self, response: dict[str, Any]) -> AIValidation:
        """Parst die LLM-Antwort."""
        confidence = int(response.get("confidence_score", 0))
        approved = response.get("approved", False)

        # Wenn approved nicht explizit gesetzt, basierend auf Threshold entscheiden
        if "approved" not in response:
            approved = confidence >= self.confidence_threshold

        setup_type = response.get("setup_type", "UNKNOWN")
        if setup_type not in self.SETUP_TYPES:
            setup_type = "NO_SETUP"

        reasoning = response.get("reasoning", "No reasoning provided")

        return AIValidation(
            approved=approved,
            confidence_score=confidence,
            setup_type=setup_type,
            reasoning=reasoning,
            provider=self.provider,
            model=self.model,
            timestamp=datetime.now(timezone.utc),
        )

    async def validate_signal_hierarchical(
        self,
        signal: "TradeSignal",
        indicators: "IndicatorSnapshot | None" = None,
        market_context: "MarketContext | None" = None,
        ohlcv_data: pd.DataFrame | None = None,
    ) -> AIValidation:
        """
        Hierarchische Signal-Validierung (Option A).

        Flow:
        1. Quick AI Overview (Model aus QSettings)
        2. Confidence >= 70% -> Trade genehmigt
        3. Confidence 50-70% -> Deep Analysis (Model aus QSettings)
        4. Confidence < 50% -> Signal abgelehnt

        Args:
            signal: Das zu validierende Signal
            indicators: Indikator-Snapshot
            market_context: Marktkontext
            ohlcv_data: OHLCV DataFrame für Deep Analysis

        Returns:
            AIValidation mit finaler Entscheidung
        """
        if not self.enabled:
            return self._create_bypass_validation("AI validation disabled")

        # Step 1: Quick Validation
        logger.info(
            f"[Hierarchical] Step 1: Quick validation for {signal.direction.value} "
            f"(Confluence: {signal.confluence_score})"
        )

        quick_result = await self.validate_signal(signal, indicators, market_context)
        quick_result.validation_level = ValidationLevel.QUICK

        # Step 2: Evaluate Quick Result
        if quick_result.confidence_score >= self.confidence_threshold_trade:
            # High confidence -> Trade
            logger.info(
                f"[Hierarchical] Quick confidence {quick_result.confidence_score}% "
                f">= {self.confidence_threshold_trade}% -> TRADE APPROVED"
            )
            quick_result.approved = True
            return quick_result

        elif quick_result.confidence_score >= self.confidence_threshold_deep:
            # Medium confidence -> Deep Analysis
            if not self.deep_analysis_enabled:
                logger.info(
                    f"[Hierarchical] Confidence {quick_result.confidence_score}% in range "
                    f"[{self.confidence_threshold_deep}-{self.confidence_threshold_trade}], "
                    f"but Deep Analysis disabled -> Using quick result"
                )
                quick_result.approved = quick_result.confidence_score >= self.confidence_threshold_trade
                return quick_result

            logger.info(
                f"[Hierarchical] Step 2: Deep Analysis triggered "
                f"(Confidence {quick_result.confidence_score}% in range "
                f"[{self.confidence_threshold_deep}-{self.confidence_threshold_trade}])"
            )

            # Deep Analysis durchführen
            deep_result = await self._run_deep_analysis(
                signal, indicators, market_context, ohlcv_data
            )
            deep_result.deep_analysis_triggered = True
            deep_result.validation_level = ValidationLevel.DEEP

            # Deep Result entscheidet
            if deep_result.confidence_score >= self.confidence_threshold_trade:
                logger.info(
                    f"[Hierarchical] Deep confidence {deep_result.confidence_score}% "
                    f">= {self.confidence_threshold_trade}% -> TRADE APPROVED"
                )
                deep_result.approved = True
            else:
                logger.info(
                    f"[Hierarchical] Deep confidence {deep_result.confidence_score}% "
                    f"< {self.confidence_threshold_trade}% -> TRADE REJECTED"
                )
                deep_result.approved = False

            return deep_result

        else:
            # Low confidence -> Skip
            logger.info(
                f"[Hierarchical] Quick confidence {quick_result.confidence_score}% "
                f"< {self.confidence_threshold_deep}% -> SIGNAL SKIPPED"
            )
            quick_result.approved = False
            quick_result.reasoning = (
                f"Signal skipped: Confidence {quick_result.confidence_score}% "
                f"below threshold {self.confidence_threshold_deep}%. "
                f"Original: {quick_result.reasoning}"
            )
            return quick_result

    async def _run_deep_analysis(
        self,
        signal: "TradeSignal",
        indicators: "IndicatorSnapshot | None",
        market_context: "MarketContext | None",
        ohlcv_data: pd.DataFrame | None,
    ) -> AIValidation:
        """
        Führt Deep Analysis durch.

        Verwendet einen ausführlicheren Prompt mit mehr Kontext.
        Das Model wird aus den QSettings geholt.
        """
        # Model aus Settings holen (gleiche wie Quick, Settings entscheiden)
        current_model = self.model
        current_provider = self.provider

        try:
            # Detaillierterer Prompt für Deep Analysis
            prompt = self._build_deep_prompt(signal, indicators, market_context, ohlcv_data)

            response = await self._call_llm(prompt)
            validation = self._parse_response(response)
            validation.model = current_model

            logger.info(
                f"[Deep Analysis] Complete: Confidence={validation.confidence_score}%, "
                f"Setup={validation.setup_type}, Model={current_model}"
            )

            return validation

        except Exception as e:
            logger.error(f"Deep analysis failed: {e}")
            # Fallback: Signal abgelehnt
            return AIValidation(
                approved=False,
                confidence_score=40,
                setup_type=None,
                reasoning=f"Deep analysis failed: {e}. Signal rejected for safety.",
                provider=current_provider,
                model=current_model,
                timestamp=datetime.now(timezone.utc),
                validation_level=ValidationLevel.DEEP,
                error=str(e),
            )

    def _build_deep_prompt(
        self,
        signal: "TradeSignal",
        indicators: "IndicatorSnapshot | None",
        market_context: "MarketContext | None",
        ohlcv_data: pd.DataFrame | None,
    ) -> str:
        """Erstellt ausführlichen Deep Analysis Prompt."""
        # Basis-Prompt
        base_prompt = self._build_prompt(signal, indicators, market_context)

        # Zusätzliche OHLCV-Analyse
        ohlcv_analysis = ""
        if ohlcv_data is not None and len(ohlcv_data) > 0:
            last_10 = ohlcv_data.tail(10)
            candle_data = []
            for idx, row in last_10.iterrows():
                candle_data.append({
                    "time": str(idx),
                    "open": round(row.get("open", 0), 2),
                    "high": round(row.get("high", 0), 2),
                    "low": round(row.get("low", 0), 2),
                    "close": round(row.get("close", 0), 2),
                    "volume": round(row.get("volume", 0), 2) if "volume" in row else 0,
                })

            ohlcv_analysis = f"""

## Letzte 10 Kerzen (OHLCV)
{json.dumps(candle_data, indent=2)}

## Zusätzliche Analyse-Anforderungen (Deep Analysis)
1. Analysiere die Kerzenformationen der letzten 10 Kerzen
2. Identifiziere Unterstützungs- und Widerstandsniveaus
3. Bewerte das Momentum und die Volatilität
4. Prüfe auf Divergenzen zwischen Preis und Indikatoren
5. Gib eine detailliertere Einschätzung der Wahrscheinlichkeit
"""

        deep_prompt = f"""{base_prompt}
{ohlcv_analysis}

WICHTIG: Dies ist eine DEEP ANALYSIS. Sei besonders gründlich und konservativ.
Genehmige nur Signale mit hoher Überzeugung (>= 70% Confidence).
Bei Unsicherheit: Lieber ablehnen als ein schlechtes Signal durchlassen."""

        return deep_prompt

    def _create_bypass_validation(self, reason: str) -> AIValidation:
        """Erstellt Bypass-Validation (AI deaktiviert)."""
        return AIValidation(
            approved=True,
            confidence_score=100,
            setup_type=None,
            reasoning=reason,
            provider="bypass",
            model="none",
            timestamp=datetime.now(timezone.utc),
            validation_level=ValidationLevel.BYPASS,
        )

    def _create_fallback_validation(self, error: str) -> AIValidation:
        """Erstellt Fallback-Validation (API-Fehler, aber Technical OK)."""
        return AIValidation(
            approved=True,
            confidence_score=50,  # Neutral confidence
            setup_type=None,
            reasoning=f"Fallback to technical signal due to AI error: {error}",
            provider="fallback",
            model="technical",
            timestamp=datetime.now(timezone.utc),
            validation_level=ValidationLevel.TECHNICAL,
            error=error,
        )

    def update_config(
        self,
        enabled: bool | None = None,
        confidence_threshold: int | None = None,
        confidence_threshold_trade: int | None = None,
        confidence_threshold_deep: int | None = None,
        deep_analysis_enabled: bool | None = None,
    ) -> None:
        """
        Aktualisiert Konfiguration zur Laufzeit.

        HINWEIS: Provider und Model werden aus QSettings geladen!
                 Änderungen an Provider/Model erfolgen über: File -> Settings -> AI
        """
        if enabled is not None:
            self.enabled = enabled
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
            self.confidence_threshold_trade = confidence_threshold
        if confidence_threshold_trade is not None:
            self.confidence_threshold_trade = confidence_threshold_trade
            self.confidence_threshold = confidence_threshold_trade
        if confidence_threshold_deep is not None:
            self.confidence_threshold_deep = confidence_threshold_deep
        if deep_analysis_enabled is not None:
            self.deep_analysis_enabled = deep_analysis_enabled

        # Reset clients wenn Settings geändert wurden
        self._openai_client = None
        self._anthropic_client = None

        logger.info(
            f"AI validator config updated: "
            f"Enabled={self.enabled}, Provider={self.provider}, Model={self.model}, "
            f"Trade>={self.confidence_threshold_trade}%, Deep>={self.confidence_threshold_deep}%"
        )
