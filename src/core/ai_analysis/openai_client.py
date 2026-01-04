import json
import logging
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
        self.api_key = api_key
        self.model = model
        if not api_key:
            logger.warning("OpenAIClient initialized without API Key.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIError))
    )
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
        if not self.client:
            logger.error("Analysis requested but no API Key configured.")
            return None

        target_model = model or self.model

        try:
            logger.info(f"Sending analysis request to {target_model}...")
            
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0, # Deterministic
                max_tokens=500,
                response_format={"type": "json_object"} # Force JSON mode
            )
            
            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response from OpenAI.")
                return None

            return self._parse_response(content)

        except Exception as e:
            logger.error(f"OpenAI API Call failed: {e}")
            raise # Trigger retry if valid exception, else fail

    def _parse_response(self, raw_json_str: str) -> AIAnalysisOutput:
        """
        Validates and parses the raw JSON response.
        """
        try:
            data = json.loads(raw_json_str)
            return AIAnalysisOutput(**data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from LLM: {e}")
            logger.debug(f"Raw content: {raw_json_str}")
            raise
        except ValidationError as e:
            logger.error(f"Response validation failed (Schema mismatch): {e}")
            raise