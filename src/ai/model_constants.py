"""Constants for AI Models and Providers."""

AI_PROVIDERS = ["Anthropic", "OpenAI", "Gemini"]

OPENAI_MODELS = [
    "gpt-5.2 (GPT-5.2 Latest)",
    "gpt-5.2-chat-latest (ChatGPT Alias)",
    "gpt-5.1 (GPT-5.1)",
    "gpt-5.1-chat-latest (ChatGPT Alias)",
    "gpt-4.1 (GPT-4.1 Full)",
    "gpt-4.1-mini (GPT-4.1 Mini)",
    "gpt-4.1-nano (GPT-4.1 Nano - Fastest)",
]

# Reasoning effort options per model
OPENAI_REASONING_EFFORTS = {
    "gpt-5.2": ["none", "low", "medium", "high", "xhigh"],
    "gpt-5.2-chat-latest": ["none", "low", "medium", "high", "xhigh"],
    "gpt-5.1": ["none", "low", "medium", "high"],
    "gpt-5.1-chat-latest": ["none", "low", "medium", "high"],
    "gpt-4.1": [],  # Non-reasoning
    "gpt-4.1-mini": [],  # Non-reasoning
    "gpt-4.1-nano": [],  # Non-reasoning
}

ANTHROPIC_MODELS = [
    "claude-sonnet-4-5-20250929 (Recommended)",
    "claude-sonnet-4-5 (Latest)",
]

GEMINI_MODELS = [
    "gemini-2.0-flash-exp (Latest)",
    "gemini-1.5-pro (Most Capable)",
    "gemini-1.5-flash (Fast)",
]
