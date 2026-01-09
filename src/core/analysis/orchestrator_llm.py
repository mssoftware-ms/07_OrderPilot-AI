"""Orchestrator LLM - LLM integration and prompt formatting.

Refactored from 666 LOC monolith using composition pattern.

Module 4/6 of orchestrator.py split.

Contains:
- call_llm(): Call configured LLM for analysis
- format_features_for_prompt(): Format features for prompt
- format_sr_levels_for_prompt(): Format support/resistance for prompt
- get_tf_role(): Map timeframe to analysis role
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class OrchestratorLLM:
    """Helper für AnalysisWorker LLM integration."""

    def __init__(self, parent):
        """
        Args:
            parent: AnalysisWorker Instanz
        """
        self.parent = parent

    async def call_llm(self, strategy: str, symbol: str, features: dict) -> str | None:
        """Call the configured LLM for deep market analysis.

        Args:
            strategy: Strategy name
            symbol: Trading symbol
            features: Dict of timeframe -> feature data

        Returns:
            LLM analysis as markdown string, or None if failed
        """
        try:
            from src.ai.ai_provider_factory import AIProviderFactory
            from src.ai.prompts import PromptTemplates
            from src.config.loader import config_manager

            # Check if AI is enabled
            if not AIProviderFactory.is_ai_enabled():
                logger.info("AI features are disabled in settings")
                return None

            # First try direct API call (same as ai_chat_tab.py) for consistency
            api_key = config_manager.get_credential("openai_api_key")
            if api_key:
                logger.info("Using direct OpenAI API call (via config_manager)")
                try:
                    import openai
                    client = openai.AsyncOpenAI(api_key=api_key)

                    technical_data = self.format_features_for_prompt(features)
                    sr_levels = self.format_sr_levels_for_prompt(features)

                    prompt = PromptTemplates.DEEP_ANALYSIS.format(
                        symbol=symbol,
                        strategy=strategy,
                        technical_data=technical_data,
                        sr_levels=sr_levels
                    )

                    response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Du bist ein erfahrener Trading-Analyst für Kryptowährungen. Antworte auf Deutsch im Markdown-Format."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=4000,
                    )
                    return response.choices[0].message.content
                except Exception as e:
                    logger.warning(f"Direct OpenAI call failed: {e}, falling back to AIProviderFactory")

            # Fallback: Use AIProviderFactory
            logger.info("Creating AI service for deep analysis via AIProviderFactory...")
            self.parent._ai_service = AIProviderFactory.create_service()
            await self.parent._ai_service.initialize()

            # Build the prompt
            technical_data = self.format_features_for_prompt(features)
            sr_levels = self.format_sr_levels_for_prompt(features)

            prompt = PromptTemplates.DEEP_ANALYSIS.format(
                symbol=symbol,
                strategy=strategy,
                technical_data=technical_data,
                sr_levels=sr_levels
            )

            # Call LLM
            logger.info(f"Calling LLM for deep analysis ({symbol})...")
            messages = [
                {"role": "system", "content": "Du bist ein erfahrener Trading-Analyst für Kryptowährungen. Antworte auf Deutsch im Markdown-Format."},
                {"role": "user", "content": prompt}
            ]

            response = await self.parent._ai_service.chat_completion(
                messages=messages,
                temperature=0.3  # Lower temperature for more focused analysis
            )

            # Cleanup
            await self.parent._ai_service.close()
            self.parent._ai_service = None

            logger.info(f"LLM response received ({len(response)} chars)")
            return response

        except ValueError as e:
            # AI disabled or no API key
            logger.warning(f"AI service not available: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM call failed: {e}", exc_info=True)
            if self.parent._ai_service:
                try:
                    await self.parent._ai_service.close()
                except Exception:
                    pass
                self.parent._ai_service = None
            return None

    def format_features_for_prompt(self, features: dict) -> str:
        """Format feature data for LLM prompt.

        Args:
            features: Dict of timeframe -> feature data

        Returns:
            Formatted markdown string
        """
        lines = []

        # Sort timeframes by duration (smallest first)
        tf_order = {"1m": 1, "5m": 2, "15m": 3, "30m": 4, "1h": 5, "4h": 6, "1D": 7, "1W": 8, "1M": 9}
        sorted_tfs = sorted(features.keys(), key=lambda x: tf_order.get(x, 99))

        for tf in sorted_tfs:
            data = features[tf]
            role = self.get_tf_role(tf)

            lines.append(f"### {tf} ({role})")
            lines.append(f"- **Anzahl Bars:** {data.get('bars', 'N/A')}")
            lines.append(f"- **Letzter Preis:** {data.get('last_price', 'N/A')}")
            lines.append(f"- **Periode Änderung:** {data.get('period_change_pct', 0)}%")
            lines.append(f"- **Trend:** {data.get('trend_state', 'Neutral')}")
            lines.append(f"- **EMA(20):** {data.get('ema20', 'N/A')} (Distanz: {data.get('ema20_distance_pct', 0)}%)")
            lines.append(f"- **RSI(14):** {data.get('rsi', 50)} - {data.get('rsi_state', 'Neutral')}")
            lines.append(f"- **BB %B:** {data.get('bb_percent', 50)}%")
            lines.append(f"- **ATR(14):** {data.get('atr', 0)} ({data.get('atr_pct', 0)}% des Preises)")
            lines.append(f"- **ADX(14):** {data.get('adx', 0)} (Trendstärke)")
            lines.append("")

        return "\n".join(lines)

    def format_sr_levels_for_prompt(self, features: dict) -> str:
        """Format support/resistance levels for LLM prompt.

        Args:
            features: Dict of timeframe -> feature data

        Returns:
            Formatted markdown string
        """
        all_support = []
        all_resistance = []

        for tf, data in features.items():
            support = data.get('support_levels', [])
            resistance = data.get('resistance_levels', [])

            if support:
                all_support.extend([(tf, level) for level in support])
            if resistance:
                all_resistance.extend([(tf, level) for level in resistance])

        lines = []

        if all_resistance:
            lines.append("**Resistance:**")
            for tf, level in sorted(all_resistance, key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {level} ({tf})")
            lines.append("")

        if all_support:
            lines.append("**Support:**")
            for tf, level in sorted(all_support, key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"- {level} ({tf})")

        if not lines:
            lines.append("*Keine signifikanten Support/Resistance Levels erkannt.*")

        return "\n".join(lines)

    @staticmethod
    def get_tf_role(tf: str) -> str:
        """Map timeframe to analysis role.

        Args:
            tf: Timeframe string (1m, 5m, 1h, etc.)

        Returns:
            Role string (EXECUTION, CONTEXT, TREND, MACRO)
        """
        role_map = {
            "1m": "EXECUTION",
            "5m": "EXECUTION",
            "15m": "CONTEXT",
            "30m": "CONTEXT",
            "1h": "TREND",
            "4h": "TREND",
            "1D": "MACRO",
            "1W": "MACRO",
            "1M": "MACRO"
        }
        return role_map.get(tf, "CONTEXT")
