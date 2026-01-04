import json
from src.core.ai_analysis.types import AIAnalysisInput

class PromptComposer:
    """
    Constructs the prompt for the LLM.
    Enforces JSON output format and injects the context.
    """

    def compose_system_prompt(self) -> str:
        """
        Returns the static system prompt with role definition and constraints.
        """
        return (
            "You are a Senior Crypto/Stock Technical Analyst specializing in Price Action and Market Structure.\n"
            "Your Goal: Provide a high-precision analysis of the provided market data to identify setups.\n"
            "Constraints:\n"
            "1. You DO NOT execute trades. You only provide analysis.\n"
            "2. You MUST reply with valid JSON only, adhering to the specified schema.\n"
            "3. Do not include markdown formatting (like ```json) in your response, just the raw JSON string.\n"
            "4. Be objective. If the data is ambiguous, output 'setup_detected': false.\n"
            "5. Focus on Structure (SFP, Sweeps, MSB) and Confluence (RSI Divergence, EMA touches)."
        )

    def compose_user_prompt(self, input_data: AIAnalysisInput) -> str:
        """
        Serializes the input data into the user prompt.
        """
        # Convert Pydantic model to JSON string
        data_json = input_data.model_dump_json(indent=2)
        
        return (
            f"Analyze the following market context and determine if a valid setup exists.\n\n"
            f"=== MARKET DATA ===\n{data_json}\n\n"
            "=== TASKS ===\n"
            "1. Analyze candle structure of the 'last_candles_summary'. Look for Wicks, SFP (Swing Failure Pattern), or Absorption.\n"
            "2. Validate if the Python-detected 'regime' matches the visual structure.\n"
            "3. Check for Divergences between Price and RSI/Momentum.\n"
            "4. Determine a structural 'invalidation_level' (Stop Loss area).\n"
            "5. Assign a 'confidence_score' (0-100) based on confluence.\n\n"
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