"""LLM Prompt Builder for Tradingbot.

Builds structured prompts for LLM calls.
"""

from __future__ import annotations

from .models import FeatureVector, RegimeState


class LLMPromptBuilder:
    """Builds structured prompts for LLM calls.

    Formats features, state, and constraints into a consistent
    prompt format that the LLM can process reliably.
    """

    # Prompt templates
    DAILY_STRATEGY_TEMPLATE = """# Daily Strategy Selection

## Current Market State
{market_state}

## Available Strategies
{strategies}

## Constraints
- Must select a strategy that matches the current regime
- Consider walk-forward validation results
- Optimize for risk-adjusted returns

## Task
Select the best strategy for today and provide reasoning.
Return a JSON response with the following structure:
- strategy_id: string (ID of selected strategy)
- confidence: float (0.0-1.0)
- reason_codes: array of strings (max 3)
- adjustments: object with optional parameter tweaks
"""

    TRADE_DECISION_TEMPLATE = """# Trade Decision Request

## Current State
{state}

## Features
{features}

## Position
{position}

## Regime
{regime}

## Constraints
{constraints}

## Task
Analyze the current situation and recommend an action.
Return a JSON response with:
- action: HOLD | EXIT | ADJUST_STOP
- confidence: float (0.0-1.0)
- reason_codes: array of strings (max 3)
- stop_adjustment: float | null (new stop price if adjusting)
"""

    @staticmethod
    def build_daily_strategy_prompt(
        features: FeatureVector,
        regime: RegimeState,
        strategies: list[dict],
        constraints: dict | None = None
    ) -> str:
        """Build prompt for daily strategy selection.

        Args:
            features: Current feature vector
            regime: Current regime state
            strategies: List of available strategies with scores
            constraints: Optional constraints dict

        Returns:
            Formatted prompt string
        """
        market_state = f"""- Symbol: {features.symbol}
- Timestamp: {features.timestamp}
- Price: {features.close:.4f}
- Regime: {regime.regime.value}
- Volatility: {regime.volatility.value}
- Regime Confidence: {regime.regime_confidence:.2f}
- RSI(14): {features.rsi_14:.2f}
- ADX(14): {features.adx_14:.2f}
- ATR%: {(features.atr_14 / features.close * 100):.2f}%"""

        strategies_text = ""
        for s in strategies:
            strategies_text += f"""
### {s['name']} (ID: {s['id']})
- Type: {s['type']}
- Applicable Regimes: {', '.join(s.get('regimes', []))}
- Walk-Forward PF: {s.get('oos_pf', 0):.2f}
- Win Rate: {s.get('win_rate', 0):.1%}
- Score: {s.get('score', 0):.2f}
"""

        prompt = LLMPromptBuilder.DAILY_STRATEGY_TEMPLATE.format(
            market_state=market_state,
            strategies=strategies_text
        )
        return prompt

    @staticmethod
    def build_trade_decision_prompt(
        features: FeatureVector,
        regime: RegimeState,
        position: dict | None,
        state: str,
        strategy: dict | None,
        constraints: dict | None = None
    ) -> str:
        """Build prompt for trade decision.

        Args:
            features: Current feature vector
            regime: Current regime state
            position: Current position dict or None
            state: Bot state (FLAT, SIGNAL, MANAGE, etc.)
            strategy: Active strategy dict
            constraints: Risk constraints

        Returns:
            Formatted prompt string
        """
        # Format features (normalized)
        features_dict = features.to_dict_normalized()
        features_text = "\n".join([
            f"- {k}: {v:.4f}" if isinstance(v, float) else f"- {k}: {v}"
            for k, v in features_dict.items()
        ])

        # Format position
        if position:
            position_text = f"""- Side: {position.get('side', 'N/A')}
- Entry Price: {position.get('entry_price', 0):.4f}
- Current Stop: {position.get('current_stop', 0):.4f}
- Bars Held: {position.get('bars_held', 0)}
- Unrealized P&L: {position.get('unrealized_pnl', 0):.2f}"""
        else:
            position_text = "No open position"

        # Format regime
        regime_text = f"""- Type: {regime.regime.value}
- Volatility: {regime.volatility.value}
- Confidence: {regime.regime_confidence:.2f}"""

        # Format constraints
        if constraints:
            constraints_text = "\n".join([
                f"- {k}: {v}" for k, v in constraints.items()
            ])
        else:
            constraints_text = "- Standard risk limits apply"

        prompt = LLMPromptBuilder.TRADE_DECISION_TEMPLATE.format(
            state=state,
            features=features_text,
            position=position_text,
            regime=regime_text,
            constraints=constraints_text
        )
        return prompt
