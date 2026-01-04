import json
import logging
import re
from typing import Optional, Dict, Any
from openai import AsyncOpenAI, APIError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pydantic import ValidationError

from src.core.ai_analysis.types import AIAnalysisOutput

logger = logging.getLogger(__name__)

class OpenAIClient:
    """
    Wrapper around OpenAI API to send prompts and receive JSON.
    Handles authentication, retries, and raw response parsing.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        if not api_key:
            raise ValueError("OpenAIClient requires a valid API key")
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError))
    )
    def _clean_model_name(self, model: str) -> str:
        """Remove descriptive text in parentheses from model name.

        Args:
            model: Model name possibly with description (e.g. "gpt-4o (Recommended)")

        Returns:
            Clean model ID (e.g. "gpt-4o")
        """
        # Remove everything in parentheses and trailing whitespace
        return re.sub(r'\s*\(.*?\)\s*', '', model).strip()

    async def analyze(self, system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Optional[AIAnalysisOutput]:
        """
        Sends the request to the LLM and parses the response into the Pydantic model.

        Args:
            system_prompt: The system prompt.
            user_prompt: The user prompt.
            model: Optional model override.

        Returns:
            AIAnalysisOutput if successful, None if failed.
        """
        target_model = self._clean_model_name(model or self.model)

        try:
            logger.info(f"Sending analysis request to {target_model}...")

            # Check if this is a reasoning model (gpt-5.x supports reasoning_effort)
            is_reasoning_model = target_model.startswith("gpt-5")

            # Reasoning models don't support structured outputs / JSON mode
            supports_structured = not is_reasoning_model

            request_kwargs: Dict[str, Any] = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }

            # Reasoning models use max_completion_tokens instead of max_tokens
            # and don't support custom temperature (always use default 1)
            if is_reasoning_model:
                request_kwargs["max_completion_tokens"] = 3000  # Reasoning + actual response
                request_kwargs["reasoning_effort"] = "medium"
                # Temperature is NOT set for reasoning models (default=1)
                logger.info(f"Using reasoning_effort=medium with max_completion_tokens=3000")
            else:
                request_kwargs["max_tokens"] = 1000  # Increased for better analysis
                request_kwargs["temperature"] = 0.1  # For non-reasoning models

            if supports_structured:
                request_kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**request_kwargs)

            # Debug: Log full response for reasoning models
            if is_reasoning_model:
                logger.info(f"Reasoning model response: {response}")
                logger.info(f"Response choices: {response.choices}")
                if response.choices:
                    logger.info(f"Message: {response.choices[0].message}")

            content = response.choices[0].message.content
            if not content:
                logger.error(f"Empty response from OpenAI. Full response: {response}")
                logger.error(f"Response model dump: {response.model_dump()}")
                return None

            return self._parse_response(content)

        except Exception as e:
            msg = str(e)
            # Fallback: retry without response_format if the model doesn't support it.
            if "response_format" in msg or "json_object" in msg:
                logger.warning("Model/API rejected response_format; retrying without structured outputs")
                response = await self.client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,
                    max_tokens=500,
                )
                content = response.choices[0].message.content
                if not content:
                    logger.error("Empty response from OpenAI (fallback).")
                    return None
                return self._parse_response(content)

            logger.error(f"OpenAI API Call failed: {e}")
            raise

    def _parse_response(self, raw_json_str: str) -> AIAnalysisOutput:
        """
        Validates and parses the raw JSON response.
        """
        try:
            cleaned = raw_json_str.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            data = json.loads(cleaned)
            return AIAnalysisOutput(**data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from LLM: {e}")
            logger.debug(f"Raw content: {raw_json_str}")
            raise
        except ValidationError as e:
            logger.error(f"Response validation failed (Schema mismatch): {e}")
            raise