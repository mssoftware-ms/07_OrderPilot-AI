"""AI-Powered Strategy Generation using LLMs.

Generates trading bot JSON configurations from detected market patterns
and user requirements using Large Language Models.

Phase 6: AI Analysis Integration
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

from src.core.tradingbot.config.models import (
    ConditionGroup,
    ConditionOperator,
    ConfigMetadata,
    ConstantValue,
    IndicatorDefinition,
    IndicatorRef,
    IndicatorType,
    RegimeDefinition,
    RegimeScope,
    RiskSettings,
    RoutingMatch,
    RoutingRule,
    StrategyDefinition,
    StrategyReference,
    StrategySetDefinition,
    TradingBotConfig,
)

from .pattern_recognizer import (
    MarketStructure,
    Pattern,
    PatternRecognizer,
    VolatilityAnalysis,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Generation Request Models
# ─────────────────────────────────────────────────────────────────


class GenerationConstraints(BaseModel):
    """Constraints for strategy generation."""

    max_indicators: int = Field(default=10, ge=1, le=20, description="Maximum indicators to use")
    max_regimes: int = Field(default=5, ge=1, le=10, description="Maximum regimes")
    max_strategies: int = Field(default=5, ge=1, le=10, description="Maximum strategies")
    timeframes: list[str] = Field(default=["1h", "4h"], description="Allowed timeframes")
    risk_tolerance: str = Field(default="medium", description="Risk tolerance: low, medium, high")
    style: str = Field(default="balanced", description="Trading style: conservative, balanced, aggressive")
    focus: str = Field(default="all", description="Focus: trend, range, momentum, all")


class GenerationResult(BaseModel):
    """Result of strategy generation."""

    config: TradingBotConfig = Field(description="Generated trading bot configuration")
    generation_notes: str = Field(description="Notes about generation process")
    warnings: list[str] = Field(default_factory=list, description="Warnings about generated config")
    recommendations: list[str] = Field(default_factory=list, description="Usage recommendations")


# ─────────────────────────────────────────────────────────────────
# Strategy Generator
# ─────────────────────────────────────────────────────────────────


class StrategyGenerator:
    """Generate trading strategies using LLM.

    Usage:
        generator = StrategyGenerator()
        await generator.initialize()
        result = await generator.generate_from_patterns(patterns, structure, constraints)
    """

    def __init__(self) -> None:
        """Initialize strategy generator."""
        self._service = None
        self._initialized = False
        self._pattern_recognizer = PatternRecognizer()

    async def initialize(self) -> bool:
        """Initialize AI service.

        Returns:
            True if successful, False otherwise.
        """
        if self._initialized:
            return True

        try:
            from src.ai.ai_provider_factory import AIProviderFactory

            if not AIProviderFactory.is_ai_enabled():
                logger.warning("AI features disabled in settings")
                return False

            self._service = AIProviderFactory.create_service()
            await self._service.initialize()
            self._initialized = True

            provider = AIProviderFactory.get_provider()
            model = AIProviderFactory.get_model(provider)
            logger.info("StrategyGenerator initialized: %s / %s", provider, model)

            return True

        except Exception as e:
            logger.error("Failed to initialize StrategyGenerator: %s", e)
            return False

    async def close(self) -> None:
        """Close AI service."""
        if self._service:
            await self._service.close()
            self._service = None
            self._initialized = False

    async def generate_from_patterns(
        self,
        patterns: list[Pattern],
        market_structure: MarketStructure,
        volatility: VolatilityAnalysis,
        constraints: GenerationConstraints | None = None,
        symbol: str = "BTC/USD",
    ) -> GenerationResult | None:
        """Generate trading bot config from detected patterns.

        Args:
            patterns: Detected chart patterns.
            market_structure: Market structure analysis.
            volatility: Volatility regime analysis.
            constraints: Generation constraints.
            symbol: Trading symbol for context.

        Returns:
            GenerationResult with config and notes.
        """
        if not self._initialized:
            if not await self.initialize():
                return None

        constraints = constraints or GenerationConstraints()

        # Build prompt for LLM
        prompt = self._build_generation_prompt(
            patterns, market_structure, volatility, constraints, symbol
        )

        try:
            # Request JSON config from LLM
            response_text = await self._service.completion(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for structured output
                use_cache=False,  # Always fresh for generation
            )

            # Parse JSON response
            config_dict = self._extract_json_from_response(response_text)

            # Validate with Pydantic
            config = TradingBotConfig(**config_dict)

            # Generate metadata and recommendations
            generation_notes = self._create_generation_notes(patterns, market_structure, volatility)
            warnings = self._validate_config_safety(config)
            recommendations = self._create_recommendations(config, market_structure, volatility)

            result = GenerationResult(
                config=config,
                generation_notes=generation_notes,
                warnings=warnings,
                recommendations=recommendations,
            )

            logger.info(
                "Generated config: %d indicators, %d regimes, %d strategies",
                len(config.indicators),
                len(config.regimes),
                len(config.strategies),
            )

            return result

        except ValidationError as e:
            logger.error("Generated config validation failed: %s", e)
            return None
        except Exception as e:
            logger.error("Strategy generation failed: %s", e)
            return None

    async def generate_from_data(
        self,
        df: pd.DataFrame,
        constraints: GenerationConstraints | None = None,
        symbol: str = "BTC/USD",
    ) -> GenerationResult | None:
        """Generate strategy from OHLCV data.

        Args:
            df: DataFrame with OHLCV data.
            constraints: Generation constraints.
            symbol: Trading symbol.

        Returns:
            GenerationResult or None.
        """
        if not self._initialized:
            if not await self.initialize():
                return None

        # Detect patterns
        patterns = self._pattern_recognizer.detect_chart_patterns(df)
        structure = self._pattern_recognizer.detect_market_structure(df)
        volatility = self._pattern_recognizer.classify_volatility_regime(df)

        return await self.generate_from_patterns(patterns, structure, volatility, constraints, symbol)

    async def enhance_existing_config(
        self,
        config: TradingBotConfig,
        df: pd.DataFrame,
        focus: str = "optimization",
    ) -> GenerationResult | None:
        """Enhance existing configuration based on market data.

        Args:
            config: Existing configuration to enhance.
            df: Recent market data.
            focus: Enhancement focus: optimization, risk, diversification.

        Returns:
            Enhanced configuration or None.
        """
        if not self._initialized:
            if not await self.initialize():
                return None

        # Analyze current market
        structure = self._pattern_recognizer.detect_market_structure(df)
        volatility = self._pattern_recognizer.classify_volatility_regime(df)

        # Build enhancement prompt
        prompt = self._build_enhancement_prompt(config, structure, volatility, focus)

        try:
            response_text = await self._service.completion(prompt=prompt, temperature=0.3)
            enhanced_dict = self._extract_json_from_response(response_text)
            enhanced_config = TradingBotConfig(**enhanced_dict)

            notes = f"Enhanced existing config with focus on: {focus}"
            warnings = self._validate_config_safety(enhanced_config)
            recommendations = self._create_recommendations(enhanced_config, structure, volatility)

            return GenerationResult(
                config=enhanced_config,
                generation_notes=notes,
                warnings=warnings,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error("Config enhancement failed: %s", e)
            return None

    # ─────────────────────────────────────────────────────────────────
    # Prompt Builders
    # ─────────────────────────────────────────────────────────────────

    def _build_generation_prompt(
        self,
        patterns: list[Pattern],
        structure: MarketStructure,
        volatility: VolatilityAnalysis,
        constraints: GenerationConstraints,
        symbol: str,
    ) -> str:
        """Build prompt for config generation."""
        patterns_desc = self._format_patterns(patterns)
        structure_desc = self._format_market_structure(structure)
        volatility_desc = self._format_volatility(volatility)

        return f"""You are an expert trading strategy architect. Generate a complete trading bot configuration in JSON format.

## Market Analysis

**Symbol:** {symbol}
**Current Market Phase:** {structure.phase.value}
**Trend Strength:** {structure.trend_strength:.2f}
**Volatility Regime:** {volatility.regime.value} (ATR percentile: {volatility.atr_percentile:.0f})

### Detected Patterns ({len(patterns)} patterns)
{patterns_desc}

### Market Structure
{structure_desc}

### Volatility Analysis
{volatility_desc}

## Generation Constraints

- Max Indicators: {constraints.max_indicators}
- Max Regimes: {constraints.max_regimes}
- Max Strategies: {constraints.max_strategies}
- Allowed Timeframes: {', '.join(constraints.timeframes)}
- Risk Tolerance: {constraints.risk_tolerance}
- Trading Style: {constraints.style}
- Focus: {constraints.focus}

## Required Output Format

Generate a JSON configuration following this exact structure:

```json
{{
  "schema_version": "1.0",
  "metadata": {{
    "author": "AI Strategy Generator",
    "created_at": "{datetime.utcnow().isoformat()}Z",
    "tags": ["ai_generated", "{symbol.lower()}", "{structure.phase.value}"],
    "notes": "Generated from pattern analysis"
  }},
  "indicators": [
    {{
      "id": "rsi14_1h",
      "type": "RSI",
      "params": {{"period": 14}},
      "timeframe": "1h"
    }}
    // Add {constraints.max_indicators - 1} more relevant indicators
  ],
  "regimes": [
    {{
      "id": "trending_up",
      "name": "Trending Market (Bullish)",
      "conditions": {{
        "all": [
          {{
            "left": {{"indicator_id": "adx14_1h", "field": "value"}},
            "op": "gt",
            "right": {{"value": 25}}
          }}
          // Add more conditions
        ]
      }},
      "priority": 10,
      "scope": "entry"
    }}
    // Add {constraints.max_regimes - 1} more regimes
  ],
  "strategies": [
    {{
      "id": "trend_follow",
      "name": "Trend Following",
      "entry": {{
        "all": [
          // Entry conditions
        ]
      }},
      "exit": {{
        "any": [
          // Exit conditions
        ]
      }},
      "risk": {{
        "position_size": 0.02,
        "stop_loss": 0.02,
        "take_profit": 0.06
      }}
    }}
    // Add {constraints.max_strategies - 1} more strategies
  ],
  "strategy_sets": [
    {{
      "id": "set_trend",
      "name": "Trending Strategies",
      "strategies": [
        {{"strategy_id": "trend_follow"}}
      ]
    }}
    // Add more strategy sets
  ],
  "routing": [
    {{
      "strategy_set_id": "set_trend",
      "match": {{
        "all_of": ["trending_up"]
      }}
    }}
    // Add more routing rules
  ]
}}
```

## Important Guidelines

1. **Indicators**: Choose indicators that match the current market phase
2. **Regimes**: Define clear, non-overlapping market regimes
3. **Strategies**: Create strategies optimized for detected patterns
4. **Risk Management**: Adjust risk based on volatility regime and risk tolerance
5. **Validation**: Ensure all indicator IDs referenced in conditions exist
6. **Timeframes**: Use multi-timeframe analysis for confirmation

Generate the complete JSON configuration now. Return ONLY valid JSON, no additional text."""

    def _build_enhancement_prompt(
        self,
        config: TradingBotConfig,
        structure: MarketStructure,
        volatility: VolatilityAnalysis,
        focus: str,
    ) -> str:
        """Build prompt for config enhancement."""
        config_summary = self._summarize_config(config)

        return f"""You are an expert trading strategy optimizer. Enhance this existing trading configuration.

## Current Configuration Summary
{config_summary}

## Current Market Conditions

**Market Phase:** {structure.phase.value}
**Trend Strength:** {structure.trend_strength:.2f}
**Volatility:** {volatility.regime.value}

## Enhancement Focus

**Focus Area:** {focus}

### Enhancement Guidelines

**If focus = "optimization":**
- Optimize indicator parameters for current market
- Refine regime thresholds
- Improve entry/exit timing

**If focus = "risk":**
- Adjust position sizing based on volatility
- Add protective regimes
- Implement better stop-loss strategies

**If focus = "diversification":**
- Add complementary strategies
- Create regime-specific variations
- Implement multiple timeframe confirmations

## Required Output

Return the ENHANCED configuration as complete JSON (same format as original).
Preserve the original structure but improve based on focus area.

Return ONLY valid JSON, no additional text."""

    # ─────────────────────────────────────────────────────────────────
    # Formatters
    # ─────────────────────────────────────────────────────────────────

    def _format_patterns(self, patterns: list[Pattern]) -> str:
        """Format patterns for prompt."""
        if not patterns:
            return "No significant patterns detected"

        lines = []
        for p in patterns[:5]:  # Limit to top 5
            lines.append(
                f"- **{p.type.value}** (confidence: {p.confidence:.1%}): {p.description}"
            )

        return "\n".join(lines)

    def _format_market_structure(self, structure: MarketStructure) -> str:
        """Format market structure for prompt."""
        support = ", ".join(f"{s:.2f}" for s in structure.support_levels[:3])
        resistance = ", ".join(f"{r:.2f}" for r in structure.resistance_levels[:3])

        return f"""- **Phase:** {structure.phase.value} (confidence: {structure.confidence:.1%})
- **Trend Strength:** {structure.trend_strength:.2f}
- **Support Levels:** {support or "None detected"}
- **Resistance Levels:** {resistance or "None detected"}
- **Notes:** {structure.notes}"""

    def _format_volatility(self, volatility: VolatilityAnalysis) -> str:
        """Format volatility analysis for prompt."""
        return f"""- **Regime:** {volatility.regime.value}
- **ATR Percentile:** {volatility.atr_percentile:.0f}th
- **Recent Volatility:** {volatility.recent_volatility:.4f}
- **Trend:** {volatility.trend}"""

    def _summarize_config(self, config: TradingBotConfig) -> str:
        """Create summary of configuration."""
        return f"""- **Indicators:** {len(config.indicators)} defined
- **Regimes:** {len(config.regimes)} regimes
- **Strategies:** {len(config.strategies)} strategies
- **Strategy Sets:** {len(config.strategy_sets)} sets
- **Routing Rules:** {len(config.routing)} rules"""

    # ─────────────────────────────────────────────────────────────────
    # Validation & Safety
    # ─────────────────────────────────────────────────────────────────

    def _extract_json_from_response(self, response: str) -> dict[str, Any]:
        """Extract JSON from LLM response.

        Args:
            response: Raw LLM response.

        Returns:
            Parsed JSON dictionary.

        Raises:
            ValueError: If JSON cannot be extracted.
        """
        # Try to find JSON in response (handle markdown code blocks)
        response = response.strip()

        # Remove markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

        # Parse JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from response: %s", e)
            logger.debug("Response content: %s", response[:500])
            raise ValueError(f"Invalid JSON in response: {e}") from e

    def _validate_config_safety(self, config: TradingBotConfig) -> list[str]:
        """Validate config for safety issues.

        Args:
            config: Configuration to validate.

        Returns:
            List of warnings.
        """
        warnings = []

        # Check for excessive risk
        for strategy in config.strategies:
            if strategy.risk:
                if strategy.risk.position_size and strategy.risk.position_size > 0.1:
                    warnings.append(
                        f"Strategy '{strategy.id}' has high position size: {strategy.risk.position_size:.1%}"
                    )

                if strategy.risk.stop_loss and strategy.risk.stop_loss > 0.05:
                    warnings.append(
                        f"Strategy '{strategy.id}' has wide stop loss: {strategy.risk.stop_loss:.1%}"
                    )

        # Check for missing indicators
        indicator_ids = {ind.id for ind in config.indicators}
        referenced_ids = set()

        for regime in config.regimes:
            self._collect_indicator_refs(regime.conditions, referenced_ids)

        for strategy in config.strategies:
            if strategy.entry:
                self._collect_indicator_refs(strategy.entry, referenced_ids)
            if strategy.exit:
                self._collect_indicator_refs(strategy.exit, referenced_ids)

        missing = referenced_ids - indicator_ids
        if missing:
            warnings.append(f"Missing indicator definitions: {missing}")

        # Check for unused indicators
        unused = indicator_ids - referenced_ids
        if unused:
            warnings.append(f"Unused indicators: {unused}")

        return warnings

    def _collect_indicator_refs(
        self, group: ConditionGroup, refs: set[str]
    ) -> None:
        """Recursively collect indicator references from condition group."""
        conditions = group.all or group.any or []

        for condition in conditions:
            if isinstance(condition, ConditionGroup):
                self._collect_indicator_refs(condition, refs)
            else:
                # Extract indicator IDs from condition
                if hasattr(condition, "left") and isinstance(condition.left, IndicatorRef):
                    refs.add(condition.left.indicator_id)
                if hasattr(condition, "right") and isinstance(condition.right, IndicatorRef):
                    refs.add(condition.right.indicator_id)

    def _create_generation_notes(
        self,
        patterns: list[Pattern],
        structure: MarketStructure,
        volatility: VolatilityAnalysis,
    ) -> str:
        """Create notes about generation process."""
        return f"""Configuration generated based on:
- Market Phase: {structure.phase.value} (confidence: {structure.confidence:.1%})
- Detected Patterns: {len(patterns)} patterns
- Volatility Regime: {volatility.regime.value}
- Generation Time: {datetime.utcnow().isoformat()}Z

This configuration is AI-generated and should be thoroughly backtested before live use."""

    def _create_recommendations(
        self,
        config: TradingBotConfig,
        structure: MarketStructure,
        volatility: VolatilityAnalysis,
    ) -> list[str]:
        """Create usage recommendations."""
        recs = []

        # Volatility-based recommendations
        if volatility.regime in ["high", "extreme"]:
            recs.append(
                "High volatility detected - consider reducing position sizes or widening stop losses"
            )

        # Market phase recommendations
        if structure.phase == "ranging":
            recs.append(
                "Ranging market detected - mean reversion strategies may perform better than trend-following"
            )
        elif structure.phase == "choppy":
            recs.append(
                "Choppy market detected - consider waiting for clearer directional movement"
            )

        # Configuration-specific recommendations
        if len(config.strategies) < 3:
            recs.append("Consider adding more strategies for better diversification")

        if len(config.regimes) < 3:
            recs.append("Consider adding more regime definitions for better market coverage")

        recs.append("Always backtest thoroughly before live trading")
        recs.append("Monitor performance and adjust parameters as market conditions change")

        return recs
