"""AI Validator Providers - API-Integrationen für OpenAI, Anthropic, Gemini.

Refactored from 852 LOC monolith using composition pattern.

Module 3/5 of ai_validator.py split.

Contains:
- _call_llm(): Router zu Provider-spezifischen Methoden
- _call_openai(): OpenAI API Integration (GPT-5.x, GPT-4.1)
- _call_anthropic(): Anthropic API Integration (Claude Sonnet 4.5)
- _call_gemini(): Google Gemini API Integration (Gemini 2.0, 1.5)
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class AIValidatorProviders:
    """API-Provider-Integrationen für AI-Validierung."""

    def __init__(self, parent):
        """
        Args:
            parent: AISignalValidator Instanz
        """
        self.parent = parent

        # API Clients (lazy initialization)
        self._openai_client = None
        self._anthropic_client = None

    async def call_llm(self, prompt: str) -> dict[str, Any]:
        """Ruft das LLM auf (Router zu Provider-spezifischen Methoden)."""
        provider = self.parent.provider

        if provider == "openai":
            return await self.call_openai(prompt)
        elif provider == "anthropic":
            return await self.call_anthropic(prompt)
        elif provider == "gemini":
            return await self.call_gemini(prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def call_openai(self, prompt: str) -> dict[str, Any]:
        """OpenAI API Call."""
        try:
            import openai

            if self._openai_client is None:
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                self._openai_client = openai.AsyncOpenAI(api_key=api_key)

            # Model aus Settings holen
            model = self.parent.model
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
                "timeout": self.parent.timeout_seconds,
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

    async def call_anthropic(self, prompt: str) -> dict[str, Any]:
        """Anthropic API Call."""
        try:
            import anthropic

            if self._anthropic_client is None:
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                self._anthropic_client = anthropic.AsyncAnthropic(api_key=api_key)

            model = self.parent.model
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

    async def call_gemini(self, prompt: str) -> dict[str, Any]:
        """Google Gemini API Call."""
        try:
            import google.generativeai as genai

            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get(
                "GEMINI_API_KEY"
            )
            if not api_key:
                raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set")

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.parent.model)

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

    def reset_clients(self) -> None:
        """Reset all API clients (called when config changes)."""
        self._openai_client = None
        self._anthropic_client = None
