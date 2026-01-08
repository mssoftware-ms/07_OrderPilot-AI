"""AI-Powered Chart Analyzer.

Uses configured AI provider to analyze charts and answer questions.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from .context_builder import ChartContext
from .models import (
    ChatMessage,
    ChartAnalysisResult,
    EntryExitRecommendation,
    MessageRole,
    PatternInfo,
    QuickAnswerResult,
    RiskAssessment,
    SignalStrength,
    SupportResistanceLevel,
    TrendDirection,
)
from .chart_markings import CompactAnalysisResponse
from .prompts import (
    STRUCTURED_OUTPUT_INSTRUCTIONS,
    build_analysis_prompt,
    build_compact_question_prompt,
    build_conversation_prompt,
    format_conversation_history,
    get_chart_analysis_system_prompt,
    get_compact_system_prompt,
    get_conversational_system_prompt,
)

if TYPE_CHECKING:
    from src.ai.providers import AnthropicProvider, OpenAIProvider

logger = logging.getLogger(__name__)


class ChartAnalyzer:
    """AI-powered chart analysis service.

    Performs comprehensive chart analysis and answers conversational
    questions about the chart using the configured AI provider.
    """

    def __init__(self, ai_service: "OpenAIProvider | AnthropicProvider | Any"):
        """Initialize analyzer with AI service.

        Args:
            ai_service: AI provider instance from AIProviderFactory
        """
        self.ai_service = ai_service

    async def analyze_chart(self, context: ChartContext) -> ChartAnalysisResult:
        """Perform comprehensive chart analysis.

        Uses LIVE data from the currently displayed chart:
        - Current symbol, timeframe, and price
        - Last N bars of OHLCV data (default: 100)
        - All active indicator values
        - Real-time derived metrics

        Args:
            context: Chart context with OHLCV and indicator data

        Returns:
            Structured analysis result
        """
        logger.info(
            f"📊 Analyzing {context.symbol} {context.timeframe} | "
            f"Price: {context.current_price:.4f} | "
            f"Active Indicators: {list(context.indicators.keys())} | "
            f"Bars: {context.bars_available}"
        )

        prompt_data = context.to_prompt_context()

        user_prompt = build_analysis_prompt(
            symbol=prompt_data["symbol"],
            timeframe=prompt_data["timeframe"],
            current_price=prompt_data["current_price"],
            ohlcv_summary=prompt_data["ohlcv_summary"],
            indicators=prompt_data["indicators"],
            price_change_pct=prompt_data["price_change_pct"],
            volatility_atr=prompt_data["volatility_atr"],
            volume_trend=prompt_data["volume_trend"],
            recent_high=prompt_data["recent_high"],
            recent_low=prompt_data["recent_low"],
            lookback=prompt_data["lookback"],
        )

        # Add structured output instructions
        full_prompt = user_prompt + "\n\n" + STRUCTURED_OUTPUT_INSTRUCTIONS

        try:
            # Try structured completion first
            if hasattr(self.ai_service, "structured_completion"):
                # Combine system prompt with user prompt for structured completion
                combined_prompt = (
                    f"{get_chart_analysis_system_prompt()}\n\n"
                    f"User Request:\n{full_prompt}"
                )
                result = await self.ai_service.structured_completion(
                    prompt=combined_prompt,
                    response_model=ChartAnalysisResult,
                    use_cache=False,  # Always use fresh data for chart analysis
                )
                result.symbol = context.symbol
                result.timeframe = context.timeframe
                return result

            # Fall back to text completion with JSON parsing
            response = await self._get_text_completion(
                system_prompt=get_chart_analysis_system_prompt(),
                user_prompt=full_prompt,
            )

            return self._parse_analysis_response(response, context)

        except Exception as e:
            import traceback
            error_msg = str(e) if str(e) else type(e).__name__
            logger.error("Chart analysis failed: %s\n%s", error_msg, traceback.format_exc())
            return self._create_error_result(context, error_msg)

    async def answer_question(
        self,
        question: str,
        context: ChartContext,
        conversation_history: list[ChatMessage],
    ) -> QuickAnswerResult:
        """Answer a specific question about the chart.

        Uses LIVE data from the currently displayed chart including
        current price, active indicators, and recent price action.

        Args:
            question: User's question
            context: Chart context
            conversation_history: Previous messages in conversation

        Returns:
            Answer result with confidence and follow-ups
        """
        logger.info(
            f"💬 Question: '{question}' | "
            f"{context.symbol} {context.timeframe} @ {context.current_price:.4f} | "
            f"Indicators: {list(context.indicators.keys())}"
        )

        prompt_data = context.to_prompt_context()

        # Format conversation history
        history_str = format_conversation_history(conversation_history)

        user_prompt = build_conversation_prompt(
            symbol=prompt_data["symbol"],
            timeframe=prompt_data["timeframe"],
            current_price=prompt_data["current_price"],
            indicators=prompt_data["indicators"],
            history=history_str,
            question=question,
        )

        try:
            response = await self._get_text_completion(
                system_prompt=get_conversational_system_prompt(),
                user_prompt=user_prompt,
            )

            return QuickAnswerResult(
                answer=response,
                confidence=0.8,
                follow_up_suggestions=self._generate_follow_ups(question),
            )

        except Exception as e:
            logger.error("Question answering failed: %s", e)
            return QuickAnswerResult(
                answer=f"Entschuldigung, ich konnte die Frage nicht beantworten: {e}",
                confidence=0.0,
                follow_up_suggestions=[],
            )

    async def answer_question_with_markings(
        self,
        question: str,
        context: ChartContext,
        conversation_history: list[ChatMessage],
    ) -> QuickAnswerResult:
        """Answer question with compact format and marking updates.

        Uses the compact analysis prompt that includes current markings
        and expects variable-format responses.

        Args:
            question: User's question
            context: Chart context including markings
            conversation_history: Previous messages in conversation

        Returns:
            Answer result with markings response
        """
        logger.info(
            f"💬 Compact Question: '{question}' | "
            f"{context.symbol} {context.timeframe} @ {context.current_price:.4f} | "
            f"Markings: {len(context.markings.markings)}"
        )

        prompt_data = context.to_prompt_context()

        # Build compact prompt
        user_prompt = build_compact_question_prompt(
            symbol=prompt_data["symbol"],
            timeframe=prompt_data["timeframe"],
            current_price=prompt_data["current_price"],
            indicators=prompt_data["indicators"],
            markings=prompt_data["markings"],
            question=question,
            price_change_pct=prompt_data["price_change_pct"],
            volatility_atr=prompt_data["volatility_atr"],
            volume_trend=prompt_data["volume_trend"],
            recent_high=prompt_data["recent_high"],
            recent_low=prompt_data["recent_low"],
        )

        try:
            response = await self._get_text_completion(
                system_prompt=get_compact_system_prompt(),
                user_prompt=user_prompt,
            )

            # Parse markings from response
            markings_response = CompactAnalysisResponse.from_ai_text(response)

            # Create result with markings
            result = QuickAnswerResult(
                answer=response,  # Full response for display
                confidence=0.8,
                follow_up_suggestions=self._generate_follow_ups(question),
            )

            # Attach markings response for service to apply
            result.markings_response = markings_response  # type: ignore

            return result

        except Exception as e:
            logger.error("Compact question answering failed: %s", e)
            return QuickAnswerResult(
                answer=f"Entschuldigung, ich konnte die Frage nicht beantworten: {e}",
                confidence=0.0,
                follow_up_suggestions=[],
            )

    async def _get_text_completion(
        self, system_prompt: str, user_prompt: str
    ) -> str:
        """Get text completion from AI service.

        Args:
            system_prompt: System context
            user_prompt: User message

        Returns:
            AI response text
        """
        # Try different completion methods based on service type
        if hasattr(self.ai_service, "complete"):
            # Anthropic-style
            response = await self.ai_service.complete(
                prompt=f"{system_prompt}\n\n{user_prompt}",
            )
            return response

        elif hasattr(self.ai_service, "chat_completion"):
            # OpenAI-style
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = await self.ai_service.chat_completion(messages=messages)
            return response

        elif hasattr(self.ai_service, "generate"):
            # Generic
            response = await self.ai_service.generate(
                prompt=f"{system_prompt}\n\n{user_prompt}",
            )
            return response

        else:
            raise ValueError("AI service does not support any known completion method")

    def _parse_analysis_response(
        self, response: str, context: ChartContext
    ) -> ChartAnalysisResult:
        """Parse AI response into structured result.

        Args:
            response: Raw AI response text
            context: Original chart context

        Returns:
            Parsed analysis result
        """
        try:
            # Try to extract JSON from response
            json_str = self._extract_json(response)
            if json_str:
                data = json.loads(json_str)
                return self._dict_to_analysis_result(data, context)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Failed to parse JSON response: %s", e)

        # Fall back to text-based result
        return ChartAnalysisResult(
            trend_direction=TrendDirection.NEUTRAL,
            trend_strength=SignalStrength.MODERATE,
            trend_description=response[:500] if response else "Analyse fehlgeschlagen",
            recommendation=EntryExitRecommendation(
                action="hold",
                confidence=0.5,
                reasoning="Automatische Analyse konnte nicht strukturiert werden.",
            ),
            risk_assessment=RiskAssessment(),
            indicator_summary="Siehe Beschreibung oben.",
            overall_sentiment=response[:200] if response else "",
            confidence_score=0.5,
            warnings=["Analyse war nicht vollständig strukturierbar."],
            symbol=context.symbol,
            timeframe=context.timeframe,
        )

    def _extract_json(self, text: str) -> str | None:
        """Extract JSON object from text response.

        Args:
            text: Raw text that may contain JSON

        Returns:
            Extracted JSON string or None
        """
        # Look for JSON block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Look for JSON object
        start = text.find("{")
        if start >= 0:
            # Find matching closing brace
            depth = 0
            for i, char in enumerate(text[start:], start):
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]

        return None

    def _dict_to_analysis_result(
        self, data: dict[str, Any], context: ChartContext
    ) -> ChartAnalysisResult:
        """Convert dictionary to ChartAnalysisResult.

        Args:
            data: Parsed JSON data
            context: Original chart context

        Returns:
            Structured analysis result
        """
        # Parse trend
        trend_dir = data.get("trend_direction", "neutral")
        if isinstance(trend_dir, str):
            trend_dir = TrendDirection(trend_dir.lower())

        trend_str = data.get("trend_strength", "moderate")
        if isinstance(trend_str, str):
            trend_str = SignalStrength(trend_str.lower())

        # Parse support/resistance levels
        support_levels = [
            SupportResistanceLevel(
                price=level.get("price", 0),
                strength=SignalStrength(level.get("strength", "moderate").lower()),
                level_type="support",
                touches=level.get("touches", 0),
            )
            for level in data.get("support_levels", [])
        ]

        resistance_levels = [
            SupportResistanceLevel(
                price=level.get("price", 0),
                strength=SignalStrength(level.get("strength", "moderate").lower()),
                level_type="resistance",
                touches=level.get("touches", 0),
            )
            for level in data.get("resistance_levels", [])
        ]

        # Parse recommendation
        rec_data = data.get("recommendation", {})
        recommendation = EntryExitRecommendation(
            action=rec_data.get("action", "hold"),
            price=rec_data.get("price"),
            confidence=rec_data.get("confidence", 0.5),
            reasoning=rec_data.get("reasoning", ""),
            urgency=rec_data.get("urgency", "normal"),
        )

        # Parse risk assessment
        risk_data = data.get("risk_assessment", {})
        risk_assessment = RiskAssessment(
            stop_loss=risk_data.get("stop_loss"),
            take_profit=risk_data.get("take_profit"),
            risk_reward_ratio=risk_data.get("risk_reward_ratio"),
            warnings=risk_data.get("warnings", []),
        )

        # Parse patterns
        patterns = [
            PatternInfo(
                name=p.get("name", ""),
                confidence=p.get("confidence", 0.5),
                implication=p.get("implication", "neutral"),
            )
            for p in data.get("patterns_identified", [])
        ]

        return ChartAnalysisResult(
            trend_direction=trend_dir,
            trend_strength=trend_str,
            trend_description=data.get("trend_description", ""),
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            recommendation=recommendation,
            risk_assessment=risk_assessment,
            patterns_identified=patterns,
            indicator_summary=data.get("indicator_summary", ""),
            overall_sentiment=data.get("overall_sentiment", ""),
            confidence_score=data.get("confidence_score", 0.5),
            warnings=data.get("warnings", []),
            symbol=context.symbol,
            timeframe=context.timeframe,
        )

    def _create_error_result(
        self, context: ChartContext, error: str
    ) -> ChartAnalysisResult:
        """Create error result when analysis fails."""
        return ChartAnalysisResult(
            trend_direction=TrendDirection.NEUTRAL,
            trend_strength=SignalStrength.WEAK,
            trend_description=f"Analyse fehlgeschlagen: {error}",
            recommendation=EntryExitRecommendation(
                action="hold",
                confidence=0.0,
                reasoning="Fehler bei der Analyse.",
            ),
            risk_assessment=RiskAssessment(warnings=[error]),
            indicator_summary="Nicht verfügbar.",
            overall_sentiment="Fehler",
            confidence_score=0.0,
            warnings=[f"Analyse-Fehler: {error}"],
            symbol=context.symbol,
            timeframe=context.timeframe,
        )

    def _generate_follow_ups(self, question: str) -> list[str]:
        """Generate follow-up question suggestions.

        Args:
            question: Original user question

        Returns:
            List of suggested follow-up questions
        """
        # Simple keyword-based suggestions
        question_lower = question.lower()

        suggestions = []

        if "trend" in question_lower:
            suggestions.append("Wie stark ist der aktuelle Trend?")
            suggestions.append("Wann könnte der Trend drehen?")
        elif "support" in question_lower or "resistance" in question_lower:
            suggestions.append("Welche Levels sind am wichtigsten?")
            suggestions.append("Wie wahrscheinlich ist ein Durchbruch?")
        elif "rsi" in question_lower or "macd" in question_lower:
            suggestions.append("Gibt es Divergenzen?")
            suggestions.append("Was sagen andere Indikatoren?")
        elif "entry" in question_lower or "einstieg" in question_lower:
            suggestions.append("Wo sollte der Stop-Loss liegen?")
            suggestions.append("Was ist das Risiko-Ertrags-Verhältnis?")
        else:
            suggestions = [
                "Was ist der aktuelle Trend?",
                "Wo liegen wichtige Support-Levels?",
                "Sollte ich jetzt einsteigen?",
            ]

        return suggestions[:3]
