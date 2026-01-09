"""Prompt Versioning for OrderPilot-AI Trading Application.

Refactored from prompts.py monolith.

Module 5/5 of prompts.py split.

Contains:
- PromptVersion class for managing prompt versions
"""

from .prompts_templates import PromptTemplates


class PromptVersion:
    """Manages prompt versions for A/B testing and improvements."""

    VERSIONS = {
        "order_analysis": {
            "v1.0": PromptTemplates.ORDER_ANALYSIS,
            "current": "v1.0"
        },
        "alert_triage": {
            "v1.0": PromptTemplates.ALERT_TRIAGE,
            "current": "v1.0"
        },
        "backtest_review": {
            "v1.0": PromptTemplates.BACKTEST_REVIEW,
            "current": "v1.0"
        },
        "signal_analysis": {
            "v1.0": PromptTemplates.SIGNAL_ANALYSIS,
            "current": "v1.0"
        }
    }

    @classmethod
    def get_prompt(cls, prompt_type: str, version: str = None) -> str:
        """Get a specific version of a prompt."""
        if prompt_type not in cls.VERSIONS:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

        prompt_versions = cls.VERSIONS[prompt_type]
        version = version or prompt_versions["current"]

        if version not in prompt_versions:
            raise ValueError(f"Unknown version {version} for {prompt_type}")

        return prompt_versions[version]
