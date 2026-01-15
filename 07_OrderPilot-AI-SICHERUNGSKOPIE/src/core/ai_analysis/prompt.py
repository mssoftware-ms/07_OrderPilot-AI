import json
from src.core.ai_analysis.types import AIAnalysisInput


class PromptComposer:
    """
    Constructs the prompt for the LLM.
    Supports optional overrides (system prompt and task section) so the UI can customize wording.
    """

    DEFAULT_SYSTEM_PROMPT = (
        "You are a Senior Crypto/Stock Technical Analyst specializing in Price Action and Market Structure.\n"
        "Your Goal: Provide a high-precision analysis of the provided market data to identify setups.\n"
        "Constraints:\n"
        "1. You DO NOT execute trades. You only provide analysis.\n"
        "2. You MUST reply with valid JSON only, adhering to the specified schema.\n"
        "3. Do not include markdown formatting (like ```json) in your response, just the raw JSON string.\n"
        "4. Be objective. If the data is ambiguous, output 'setup_detected': false.\n"
        "5. Focus on Structure (SFP, Sweeps, MSB) and Confluence (RSI Divergence, EMA touches)."
    )

    DEFAULT_TASKS_PROMPT = (
        "Analyze the following market context and determine if a valid setup exists.\n\n"
        "=== TASKS ===\n"
        "1. Analyze candle structure of the 'last_candles_summary'. Look for Wicks, SFP (Swing Failure Pattern), or Absorption.\n"
        "2. Validate if the Python-detected 'regime' matches the visual structure.\n"
        "3. Check for Divergences between Price and RSI/Momentum.\n"
        "4. Determine a structural 'invalidation_level' (Stop Loss area).\n"
        "5. Assign a 'confidence_score' (0-100) based on confluence.\n"
        "6. If 'strategy_configs' is provided, evaluate which strategy (and its parameters) best fits the current market conditions.\n"
    )

    def __init__(
        self,
        system_prompt_override: str | None = None,
        tasks_prompt_override: str | None = None,
    ):
        self.system_prompt_override = (system_prompt_override or "").strip() or None
        self.tasks_prompt_override = (tasks_prompt_override or "").strip() or None

    def set_overrides(
        self,
        system_prompt: str | None = None,
        tasks_prompt: str | None = None,
    ) -> None:
        """Update prompt overrides (empty/None resets to defaults)."""
        self.system_prompt_override = (system_prompt or "").strip() or None
        self.tasks_prompt_override = (tasks_prompt or "").strip() or None

    def compose_system_prompt(self) -> str:
        """Return the system prompt (override if provided)."""
        return self.system_prompt_override or self.DEFAULT_SYSTEM_PROMPT

    def compose_user_prompt(self, input_data: AIAnalysisInput) -> str:
        """
        Serializes the input data into the user prompt, inserting the tasks block
        (override if provided) and the JSON schema instructions.
        """
        data_json = input_data.model_dump_json(indent=2)
        tasks_block = self.tasks_prompt_override or self.DEFAULT_TASKS_PROMPT

        return (
            f"{tasks_block}\n"
            f"=== MARKET DATA ===\n{data_json}\n\n"
            "=== OUTPUT ===\n"
            "Provide your output strictly in the required JSON format matching this schema:\n"
            "{\n"
            "  \"setup_detected\": bool,\n"
            "  \"setup_type\": \"PULLBACK_EMA20\" | \"BREAKOUT\" | \"MEAN_REVERSION\" | \"SFP_SWING_FAILURE\" | \"ABSORPTION\" | \"NO_SETUP\",\n"
            "  \"confidence_score\": int,\n"
            "  \"reasoning\": \"string\",\n"
            "  \"invalidation_level\": float,\n"
            "  \"notes\": [\"string\"]\n"
            "}"
        )
