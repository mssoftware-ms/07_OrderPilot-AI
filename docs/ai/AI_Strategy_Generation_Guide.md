# AI Strategy Generation Guide

**Phase 6: AI Analysis Integration**

This guide explains how to use AI-powered strategy generation in OrderPilot-AI.

## Table of Contents

1. [Overview](#overview)
2. [Components](#components)
3. [Quick Start](#quick-start)
4. [Pattern Recognition](#pattern-recognition)
5. [Strategy Generation](#strategy-generation)
6. [Parameter Optimization](#parameter-optimization)
7. [Integration with Entry Analyzer](#integration-with-entry-analyzer)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The AI Strategy Generation system provides three main capabilities:

1. **Pattern Recognition**: Detect chart patterns, market structure, and volatility regimes
2. **Strategy Generation**: Generate complete trading bot configurations using LLMs
3. **Parameter Optimization**: Auto-tune parameters using genetic algorithms or Bayesian optimization

## Components

### 1. PatternRecognizer

Detects technical patterns and analyzes market structure:

- Chart patterns (double tops/bottoms, triangles, flags, candlestick patterns)
- Market phases (trending, ranging, choppy, transition)
- Volatility regimes (low, normal, high, extreme)
- Support/resistance levels

### 2. StrategyGenerator

Generates trading strategies using Large Language Models:

- Analyzes detected patterns
- Creates indicator definitions
- Defines market regimes
- Generates entry/exit strategies
- Sets appropriate risk parameters

### 3. ParameterOptimizer

Optimizes strategy parameters:

- Genetic algorithm optimization
- Bayesian optimization
- Grid search
- Random search
- Multi-objective optimization

---

## Quick Start

### Installation

Ensure AI dependencies are installed:

```bash
pip install numpy pandas pydantic
# AI providers (choose one or more)
pip install openai anthropic google-generativeai
```

### Configuration

Set your AI API keys in environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="your-key-here"

# Anthropic
export ANTHROPIC_API_KEY="your-key-here"

# Google Gemini
export GEMINI_API_KEY="your-key-here"
```

Configure AI provider in settings (see `src/ai/ai_provider_factory.py`).

---

## Pattern Recognition

### Basic Usage

```python
from src.ai import PatternRecognizer
import pandas as pd

# Load your OHLCV data
df = pd.read_csv("btc_1h.csv")  # Must have: open, high, low, close, volume

# Initialize recognizer
recognizer = PatternRecognizer(lookback_periods=50)

# Detect patterns
patterns = recognizer.detect_chart_patterns(df)
for pattern in patterns:
    print(f"{pattern.type.value}: {pattern.description} (conf: {pattern.confidence:.1%})")

# Analyze market structure
structure = recognizer.detect_market_structure(df)
print(f"Market Phase: {structure.phase.value}")
print(f"Trend Strength: {structure.trend_strength:.2f}")
print(f"Support: {structure.support_levels}")
print(f"Resistance: {structure.resistance_levels}")

# Classify volatility
volatility = recognizer.classify_volatility_regime(df)
print(f"Volatility: {volatility.regime.value}")
print(f"ATR Percentile: {volatility.atr_percentile:.0f}th")
```

### Detected Pattern Types

**Reversal Patterns:**
- Head and Shoulders / Inverse H&S
- Double Top / Double Bottom
- Triple Top / Triple Bottom

**Continuation Patterns:**
- Bull Flag / Bear Flag
- Ascending / Descending / Symmetrical Triangle
- Rising / Falling Wedge

**Candlestick Patterns:**
- Hammer
- Shooting Star
- Doji
- Bullish / Bearish Engulfing

### Market Phases

- `TRENDING_UP`: Strong uptrend
- `TRENDING_DOWN`: Strong downtrend
- `RANGING`: Sideways movement within tight range
- `CHOPPY`: Frequent direction changes
- `TRANSITION`: Moving between phases

### Volatility Regimes

- `LOW`: ATR below 25th percentile
- `NORMAL`: ATR between 25th-75th percentile
- `HIGH`: ATR between 75th-90th percentile
- `EXTREME`: ATR above 90th percentile

---

## Strategy Generation

### Basic Usage

```python
from src.ai import StrategyGenerator, GenerationConstraints
import asyncio

async def generate_strategy():
    generator = StrategyGenerator()

    # Initialize AI service
    if not await generator.initialize():
        print("AI service not available")
        return

    try:
        # Define constraints
        constraints = GenerationConstraints(
            max_indicators=8,
            max_regimes=4,
            max_strategies=4,
            timeframes=["1h", "4h"],
            risk_tolerance="medium",  # low, medium, high
            style="balanced",  # conservative, balanced, aggressive
            focus="all"  # trend, range, momentum, all
        )

        # Generate from OHLCV data
        result = await generator.generate_from_data(
            df=df,
            constraints=constraints,
            symbol="BTC/USD"
        )

        if result:
            # Access generated config
            config = result.config

            # Review generation notes
            print(result.generation_notes)

            # Check warnings
            for warning in result.warnings:
                print(f"⚠️  {warning}")

            # View recommendations
            for rec in result.recommendations:
                print(f"💡 {rec}")

            # Save to file
            import json
            with open("generated_config.json", "w") as f:
                json.dump(config.model_dump(), f, indent=2)

    finally:
        await generator.close()

# Run
asyncio.run(generate_strategy())
```

### Advanced: Generate from Detected Patterns

```python
# First, detect patterns
patterns = recognizer.detect_chart_patterns(df)
structure = recognizer.detect_market_structure(df)
volatility = recognizer.classify_volatility_regime(df)

# Generate strategy from patterns
result = await generator.generate_from_patterns(
    patterns=patterns,
    market_structure=structure,
    volatility=volatility,
    constraints=constraints,
    symbol="BTC/USD"
)
```

### Enhance Existing Configuration

```python
# Load existing config
from src.core.tradingbot.config.models import TradingBotConfig
import json

with open("current_config.json") as f:
    config = TradingBotConfig(**json.load(f))

# Enhance with AI
result = await generator.enhance_existing_config(
    config=config,
    df=recent_market_data,
    focus="optimization"  # optimization, risk, diversification
)
```

### Generation Constraints

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_indicators` | 10 | Maximum indicators to create |
| `max_regimes` | 5 | Maximum market regimes |
| `max_strategies` | 5 | Maximum strategies |
| `timeframes` | ["1h", "4h"] | Allowed timeframes |
| `risk_tolerance` | "medium" | Risk level: low, medium, high |
| `style` | "balanced" | Style: conservative, balanced, aggressive |
| `focus` | "all" | Focus: trend, range, momentum, all |

---

## Parameter Optimization

### Basic Usage

```python
from src.ai import ParameterOptimizer, OptimizationConfig, OptimizationMethod, ParameterRange

# Configure optimization
opt_config = OptimizationConfig(
    method=OptimizationMethod.GENETIC,
    max_iterations=50,
    population_size=20,
    early_stopping_patience=10,
    random_seed=42  # For reproducibility
)

optimizer = ParameterOptimizer(opt_config)

# Define parameter ranges
param_ranges = [
    ParameterRange(name="adx_threshold", min_value=15.0, max_value=35.0, step=5.0),
    ParameterRange(name="rsi_upper", min_value=60.0, max_value=80.0, step=5.0),
    ParameterRange(name="rsi_lower", min_value=20.0, max_value=40.0, step=5.0),
]

# Optimize
result = optimizer.optimize_regime_thresholds(
    config=config,
    data=df,
    param_ranges=param_ranges
)

# View results
print(f"Best Score: {result.best_score:.4f}")
print(f"Best Params: {result.best_params}")
print(f"Total Trials: {result.total_trials}")

# Apply optimized parameters
optimized_config = optimizer.apply_best_params(
    config=config,
    params=result.best_params,
    target_type="regime",
    target_id="trending"
)
```

### Optimization Methods

**1. Genetic Algorithm** (recommended for most cases)
```python
OptimizationConfig(method=OptimizationMethod.GENETIC)
```
- Pros: Handles non-linear problems well, global optimization
- Cons: May need many iterations

**2. Bayesian Optimization** (for expensive objective functions)
```python
OptimizationConfig(method=OptimizationMethod.BAYESIAN)
```
- Pros: Sample-efficient, good for expensive evaluations
- Cons: Simplified implementation (no full Gaussian processes)

**3. Grid Search** (for thorough exploration)
```python
OptimizationConfig(method=OptimizationMethod.GRID)
```
- Pros: Guaranteed to find best in grid
- Cons: Exponential growth with parameters

**4. Random Search** (baseline)
```python
OptimizationConfig(method=OptimizationMethod.RANDOM)
```
- Pros: Simple, parallelizable
- Cons: Inefficient sampling

### Optimize Specific Components

**Indicator Parameters:**
```python
result = optimizer.optimize_indicator_params(
    config=config,
    data=df,
    indicator_id="rsi14_1h",
    param_ranges=[
        ParameterRange(name="period", min_value=10, max_value=30, is_integer=True)
    ]
)
```

**Risk Parameters:**
```python
result = optimizer.optimize_risk_params(
    config=config,
    data=df,
    strategy_id="trend_follow"
)
# Optimizes: position_size, stop_loss, take_profit
```

### Convergence Monitoring

```python
import matplotlib.pyplot as plt

# Plot convergence
plt.plot(result.convergence_history)
plt.xlabel("Iteration")
plt.ylabel("Best Score")
plt.title("Optimization Convergence")
plt.show()
```

---

## Integration with Entry Analyzer

The AI Copilot tab in Entry Analyzer provides a UI for strategy generation.

### Using the AI Copilot Tab

1. **Open Entry Analyzer** (from main menu or toolbar)
2. **Navigate to "🤖 AI Copilot" tab**
3. **Click "Generate Strategy" button**
4. **Configure generation settings:**
   - Risk tolerance (Low/Medium/High)
   - Trading style (Conservative/Balanced/Aggressive)
   - Focus area (Trend/Range/Momentum/All)
5. **Review generated configuration**
6. **Save or apply to bot**

### Programmatic Access

```python
from src.ui.dialogs.entry_analyzer_popup import EntryAnalyzerPopup

# Entry Analyzer automatically integrates with AI components
# See entry_analyzer_popup.py for implementation details
```

---

## Best Practices

### 1. Data Quality

- **Minimum data**: At least 100 periods for pattern detection
- **Timeframe**: Match timeframe to trading strategy (1h for intraday, 4h/1d for swing)
- **Clean data**: Ensure no gaps or missing values

### 2. Pattern Recognition

- **Validate patterns**: Don't rely solely on AI detection
- **Combine with other analysis**: Use patterns as confirmation, not sole signal
- **Context matters**: Consider broader market context

### 3. Strategy Generation

- **Always backtest**: AI-generated strategies MUST be backtested before live use
- **Start conservative**: Use "low" risk tolerance initially
- **Iterate**: Refine generated strategies based on backtest results
- **Human review**: Review all generated rules for logical consistency

### 4. Parameter Optimization

- **Avoid overfitting**: Use walk-forward validation
- **Limit parameters**: Optimize 3-5 parameters at a time max
- **Multiple runs**: Run optimization multiple times with different seeds
- **Out-of-sample testing**: Always test on unseen data

### 5. Risk Management

- **Never skip validation**: All AI-generated configs should pass validation
- **Review warnings**: Address all warnings before live trading
- **Start small**: Begin with smaller position sizes
- **Monitor closely**: Watch AI-generated strategies more carefully initially

---

## Troubleshooting

### AI Service Not Available

**Problem**: `AI service not available` or initialization fails

**Solutions**:
1. Check API keys are set correctly:
   ```bash
   echo $OPENAI_API_KEY  # Should show your key
   ```
2. Verify AI is enabled in settings (see `src/ai/ai_provider_factory.py`)
3. Check internet connectivity
4. Verify API key has sufficient credits/quota

### Poor Pattern Detection

**Problem**: No patterns detected or low confidence

**Solutions**:
1. Increase data size (need at least 100 periods)
2. Adjust `lookback_periods` parameter
3. Try different timeframes (patterns clearer on higher timeframes)
4. Check data quality (no gaps, correct OHLCV format)

### Invalid Generated Configuration

**Problem**: Generated config fails validation

**Solutions**:
1. Check `warnings` in GenerationResult
2. Reduce constraint limits (fewer indicators/regimes/strategies)
3. Try different AI provider or model
4. Review prompt in `strategy_generator.py` for clarity

### Optimization Not Converging

**Problem**: Optimization doesn't improve over iterations

**Solutions**:
1. Increase `max_iterations`
2. Try different optimization method
3. Expand parameter ranges
4. Check objective function is working correctly
5. Add more training data

### Memory/Performance Issues

**Problem**: AI generation is slow or runs out of memory

**Solutions**:
1. Reduce data size (use last N periods only)
2. Lower `max_iterations` in optimization
3. Reduce `population_size` in genetic algorithm
4. Use simpler optimization method (RANDOM instead of GENETIC)

---

## Examples

See `tests/ai/test_strategy_generator.py` for comprehensive examples.

### Example 1: Complete Workflow

```python
import asyncio
import pandas as pd
from src.ai import PatternRecognizer, StrategyGenerator, ParameterOptimizer
from src.ai import GenerationConstraints, OptimizationConfig, OptimizationMethod

async def full_ai_workflow(df: pd.DataFrame):
    # Step 1: Detect patterns
    recognizer = PatternRecognizer()
    patterns = recognizer.detect_chart_patterns(df)
    structure = recognizer.detect_market_structure(df)
    volatility = recognizer.classify_volatility_regime(df)

    print(f"Detected {len(patterns)} patterns")
    print(f"Market: {structure.phase.value}, Volatility: {volatility.regime.value}")

    # Step 2: Generate strategy
    generator = StrategyGenerator()
    await generator.initialize()

    try:
        constraints = GenerationConstraints(
            max_indicators=6,
            max_regimes=3,
            max_strategies=3,
            risk_tolerance="medium"
        )

        gen_result = await generator.generate_from_patterns(
            patterns, structure, volatility, constraints, symbol="BTC/USD"
        )

        if not gen_result:
            print("Strategy generation failed")
            return

        config = gen_result.config

        # Step 3: Optimize parameters
        opt_config = OptimizationConfig(
            method=OptimizationMethod.GENETIC,
            max_iterations=30,
            random_seed=42
        )

        optimizer = ParameterOptimizer(opt_config)
        opt_result = optimizer.optimize_regime_thresholds(config, df)

        print(f"Optimized score: {opt_result.best_score:.4f}")

        # Step 4: Apply and save
        final_config = optimizer.apply_best_params(
            config, opt_result.best_params
        )

        import json
        with open("final_strategy.json", "w") as f:
            json.dump(final_config.model_dump(), f, indent=2)

        print("✅ Strategy generated and optimized successfully")

    finally:
        await generator.close()

# Run
df = pd.read_csv("market_data.csv")
asyncio.run(full_ai_workflow(df))
```

---

## API Reference

See module docstrings for detailed API documentation:

- `src/ai/pattern_recognizer.py`
- `src/ai/strategy_generator.py`
- `src/ai/parameter_optimizer.py`

---

## Future Enhancements

Planned features for future releases:

- [ ] Multi-objective optimization (Sharpe + Win Rate + Drawdown)
- [ ] Ensemble strategy generation (multiple LLMs voting)
- [ ] Real-time pattern detection with alerts
- [ ] AutoML-style hyperparameter tuning
- [ ] Transfer learning from successful strategies
- [ ] Explainable AI (XAI) for strategy decisions

---

## Support

For issues or questions:

1. Check this documentation
2. Review test cases in `tests/ai/`
3. Search existing issues in project repository
4. Create new issue with detailed description

---

**Remember**: AI-generated strategies are tools to assist trading decisions, not a substitute for human judgment. Always validate, backtest, and monitor carefully before live deployment.
