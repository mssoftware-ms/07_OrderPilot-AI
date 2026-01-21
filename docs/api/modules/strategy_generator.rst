Strategy Generator
==================

.. automodule:: src.ai.strategy_generator
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``StrategyGenerator`` uses LLMs to automatically generate trading bot JSON configurations:

* **Pattern-Based Generation**: Creates strategies from detected chart patterns and market structure
* **Data-Driven Generation**: Analyzes historical data to identify profitable conditions
* **Config Enhancement**: Improves existing strategies with AI insights
* **Safety Validation**: Ensures generated configs meet risk and quality standards
* **Multi-Provider Support**: Works with OpenAI, Anthropic, Google AI via AIProviderFactory

Key Features
------------

**Intelligent Strategy Creation:**
   LLM analyzes market context and generates complete JSON configs with indicators, regimes, strategies, and routing.

**Safety Validation:**
   Automatic checks for excessive risk, missing indicators, unused indicators, invalid references.

**Flexible Constraints:**
   Control max indicators, max regimes, timeframes, risk tolerance, strategy style, and focus areas.

**Async Operation:**
   Fully async with proper initialization and cleanup using context managers.

**Comprehensive Results:**
   Returns success status, generated config, reasoning, warnings, and validation errors.

Usage Example
-------------

.. code-block:: python

    from src.ai.strategy_generator import StrategyGenerator, GenerationConstraints
    from src.ai.pattern_recognizer import PatternRecognizer
    import pandas as pd
    import asyncio

    async def generate_strategy_example():
        # 1. Analyze market with PatternRecognizer
        recognizer = PatternRecognizer()
        patterns = recognizer.detect_chart_patterns(df)
        structure = recognizer.detect_market_structure(df)
        volatility = recognizer.classify_volatility_regime(df)

        # 2. Initialize StrategyGenerator
        async with StrategyGenerator() as generator:

            # 3. Define generation constraints
            constraints = GenerationConstraints(
                max_indicators=8,
                max_regimes=4,
                max_strategies=3,
                timeframes=['1h', '4h'],
                risk_tolerance='medium',  # low, medium, high
                style='balanced',  # conservative, balanced, aggressive
                focus='trend'  # trend, range, momentum, all
            )

            # 4. Generate strategy from patterns
            result = await generator.generate_from_patterns(
                patterns=patterns,
                market_structure=structure,
                volatility_analysis=volatility,
                constraints=constraints
            )

            # 5. Check result
            if result.success:
                config = result.config
                print(f"✓ Generated strategy: {config.metadata.get('strategy_name')}")
                print(f"Indicators: {len(config.indicators)}")
                print(f"Regimes: {len(config.regimes)}")
                print(f"Strategies: {len(config.strategies)}")
                print(f"\nReasoning:\n{result.reasoning}")

                # Save to file
                with open('generated_strategy.json', 'w') as f:
                    json.dump(config.dict(), f, indent=2)
            else:
                print(f"✗ Generation failed:")
                for error in result.errors:
                    print(f"  - {error}")

            # Check warnings
            for warning in result.warnings:
                print(f"⚠ {warning}")

    # Run async function
    asyncio.run(generate_strategy_example())

Classes
-------

.. autoclass:: src.ai.strategy_generator.StrategyGenerator
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __aenter__, __aexit__

Key Methods
-----------

async generate_from_patterns(patterns, market_structure, volatility_analysis, constraints)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.strategy_generator.StrategyGenerator.generate_from_patterns

Generate strategy from detected patterns and market analysis.

**Parameters:**

* ``patterns`` (list[Pattern]): Detected chart patterns
* ``market_structure`` (MarketStructure): Market structure analysis
* ``volatility_analysis`` (VolatilityAnalysis): Volatility regime classification
* ``constraints`` (GenerationConstraints): Generation constraints

**Returns:**

* ``GenerationResult``: Result with config, reasoning, warnings, errors

**Algorithm:**

1. **Build LLM Prompt:**

   .. code-block:: python

       prompt = f"""
       Generate a trading bot JSON configuration based on the following market analysis:

       PATTERNS DETECTED:
       {self._format_patterns(patterns)}

       MARKET STRUCTURE:
       - Phase: {market_structure.phase}
       - Trend: {market_structure.trend_direction} (strength: {market_structure.trend_strength:.2%})
       - Support Levels: {market_structure.support_levels}
       - Resistance Levels: {market_structure.resistance_levels}

       VOLATILITY:
       - Regime: {volatility_analysis.regime}
       - ATR%: {volatility_analysis.atr_pct:.2%}
       - Percentile: {volatility_analysis.percentile:.2%}

       CONSTRAINTS:
       - Max Indicators: {constraints.max_indicators}
       - Max Regimes: {constraints.max_regimes}
       - Timeframes: {constraints.timeframes}
       - Risk Tolerance: {constraints.risk_tolerance}
       - Style: {constraints.style}
       - Focus: {constraints.focus}

       Generate a complete JSON configuration with:
       1. Indicators appropriate for detected patterns
       2. Regimes matching market structure and volatility
       3. Strategies aligned with risk tolerance and style
       4. Routing rules connecting regimes to strategies

       Return ONLY valid JSON following the TradingBotConfig schema.
       """

2. **Call LLM:**

   .. code-block:: python

       # Use AIProviderFactory for multi-provider support
       response = await self.llm_client.generate(
           prompt=prompt,
           temperature=0.3,  # Low temperature for structured output
           max_tokens=4000
       )

       # Extract JSON from response
       json_str = self._extract_json_from_response(response.text)

3. **Parse and Validate:**

   .. code-block:: python

       # Parse JSON
       config_dict = json.loads(json_str)

       # Validate with Pydantic
       config = TradingBotConfig(**config_dict)

4. **Safety Validation:**

   .. code-block:: python

       warnings, errors = self._validate_generated_config(config, constraints)

       # Check for critical errors
       if errors:
           return GenerationResult(
               success=False,
               config=None,
               reasoning=response.reasoning,
               warnings=warnings,
               errors=errors
           )

5. **Return Result:**

   .. code-block:: python

       return GenerationResult(
           success=True,
           config=config,
           reasoning=response.reasoning,
           warnings=warnings,
           errors=[]
       )

**Example:**

.. code-block:: python

    # Generate from detected patterns
    result = await generator.generate_from_patterns(
        patterns=[
            Pattern(pattern_type='double_bottom', direction='bullish', confidence=0.8),
            Pattern(pattern_type='ascending_triangle', direction='bullish', confidence=0.7)
        ],
        market_structure=MarketStructure(
            phase=MarketPhase.TRENDING_UP,
            trend_direction='bullish',
            trend_strength=0.7
        ),
        volatility_analysis=VolatilityAnalysis(
            regime=VolatilityRegime.NORMAL,
            atr_pct=2.5,
            percentile=0.55
        ),
        constraints=GenerationConstraints(
            focus='trend',
            risk_tolerance='medium'
        )
    )

async generate_from_data(df, constraints, symbol)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.strategy_generator.StrategyGenerator.generate_from_data

Generate strategy by analyzing raw historical data.

**Parameters:**

* ``df`` (pd.DataFrame): Historical OHLCV data
* ``constraints`` (GenerationConstraints): Generation constraints
* ``symbol`` (str): Trading symbol (e.g., 'BTCUSD')

**Returns:**

* ``GenerationResult``: Result with config, reasoning, warnings, errors

**Algorithm:**

1. **Detect Patterns and Structure:**

   .. code-block:: python

       recognizer = PatternRecognizer()
       patterns = recognizer.detect_chart_patterns(df)
       structure = recognizer.detect_market_structure(df)
       volatility = recognizer.classify_volatility_regime(df)

2. **Delegate to generate_from_patterns:**

   .. code-block:: python

       return await self.generate_from_patterns(
           patterns=patterns,
           market_structure=structure,
           volatility_analysis=volatility,
           constraints=constraints
       )

**Example:**

.. code-block:: python

    # Generate directly from data
    result = await generator.generate_from_data(
        df=btc_1h_data,
        constraints=GenerationConstraints(
            timeframes=['1h', '4h'],
            risk_tolerance='low',
            style='conservative',
            focus='all'
        ),
        symbol='BTCUSD'
    )

    if result.success:
        print(f"Generated {len(result.config.strategies)} strategies")
        print(f"Using {len(result.config.indicators)} indicators")

async enhance_existing_config(config, df, focus)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.strategy_generator.StrategyGenerator.enhance_existing_config

Enhance existing strategy config with AI insights.

**Parameters:**

* ``config`` (TradingBotConfig): Existing configuration to enhance
* ``df`` (pd.DataFrame): Recent historical data for analysis
* ``focus`` (str): Enhancement focus ('indicators', 'regimes', 'strategies', 'all')

**Returns:**

* ``GenerationResult``: Enhanced config with improvements

**Algorithm:**

1. **Analyze Current Config:**

   .. code-block:: python

       current_indicators = [ind.id for ind in config.indicators]
       current_regimes = [reg.id for reg in config.regimes]
       current_strategies = [strat.id for strat in config.strategies]

2. **Analyze Recent Market Data:**

   .. code-block:: python

       recognizer = PatternRecognizer()
       patterns = recognizer.detect_chart_patterns(df)
       structure = recognizer.detect_market_structure(df)
       volatility = recognizer.classify_volatility_regime(df)

3. **Build Enhancement Prompt:**

   .. code-block:: python

       prompt = f"""
       Enhance the following trading bot configuration based on recent market analysis:

       CURRENT CONFIG:
       - Indicators: {current_indicators}
       - Regimes: {current_regimes}
       - Strategies: {current_strategies}

       RECENT MARKET ANALYSIS:
       - Patterns: {self._format_patterns(patterns)}
       - Structure: {structure.phase}, Trend: {structure.trend_direction}
       - Volatility: {volatility.regime}

       ENHANCEMENT FOCUS: {focus}

       Suggest improvements to:
       {'- Add/modify indicators to better capture current market dynamics' if focus in ['indicators', 'all'] else ''}
       {'- Add/modify regimes to better classify market states' if focus in ['regimes', 'all'] else ''}
       {'- Add/modify strategies to improve performance in current conditions' if focus in ['strategies', 'all'] else ''}

       Return enhanced JSON configuration.
       """

4. **Generate and Merge:**

   .. code-block:: python

       # Get AI suggestions
       response = await self.llm_client.generate(prompt)
       enhanced_config = TradingBotConfig(**json.loads(response.text))

       # Merge with existing config
       merged_config = self._merge_configs(config, enhanced_config, focus)

5. **Validate and Return:**

   .. code-block:: python

       warnings, errors = self._validate_generated_config(merged_config, None)

       return GenerationResult(
           success=len(errors) == 0,
           config=merged_config,
           reasoning=response.reasoning,
           warnings=warnings,
           errors=errors
       )

**Example:**

.. code-block:: python

    # Enhance existing config with new indicators
    result = await generator.enhance_existing_config(
        config=existing_config,
        df=recent_market_data,
        focus='indicators'  # Only enhance indicators
    )

    if result.success:
        print("Enhanced config with new indicators:")
        new_indicators = set(ind.id for ind in result.config.indicators) - \
                        set(ind.id for ind in existing_config.indicators)
        for ind_id in new_indicators:
            print(f"  + {ind_id}")

_validate_generated_config(config, constraints)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.strategy_generator.StrategyGenerator._validate_generated_config

**Internal method** - Validate generated config for safety and quality.

**Safety Checks:**

.. code-block:: python

    warnings = []
    errors = []

    # 1. Check for excessive risk
    for strategy in config.strategies:
        if strategy.risk.position_size_pct > 20.0:
            errors.append(f"Excessive position size in {strategy.id}: {strategy.risk.position_size_pct}%")

        if strategy.risk.stop_loss_pct < 0.5:
            warnings.append(f"Very tight stop loss in {strategy.id}: {strategy.risk.stop_loss_pct}%")

        if strategy.risk.stop_loss_pct > 10.0:
            warnings.append(f"Very wide stop loss in {strategy.id}: {strategy.risk.stop_loss_pct}%")

    # 2. Check for missing indicators
    referenced_indicators = set()
    for regime in config.regimes:
        for condition in regime.conditions:
            if condition.left.indicator:
                referenced_indicators.add(condition.left.indicator)
            if condition.right and condition.right.indicator:
                referenced_indicators.add(condition.right.indicator)

    defined_indicators = {ind.id for ind in config.indicators}
    missing = referenced_indicators - defined_indicators

    if missing:
        errors.append(f"Referenced indicators not defined: {missing}")

    # 3. Check for unused indicators
    unused = defined_indicators - referenced_indicators
    if unused:
        warnings.append(f"Defined but unused indicators: {unused}")

    # 4. Check constraint compliance
    if constraints:
        if len(config.indicators) > constraints.max_indicators:
            errors.append(f"Too many indicators: {len(config.indicators)} > {constraints.max_indicators}")

        if len(config.regimes) > constraints.max_regimes:
            errors.append(f"Too many regimes: {len(config.regimes)} > {constraints.max_regimes}")

    return warnings, errors

Common Patterns
---------------

**Pattern 1: Generate Strategy for New Market**

.. code-block:: python

    async def create_strategy_for_market(symbol: str, timeframe: str):
        # 1. Load historical data
        df = load_market_data(symbol, timeframe, lookback_days=180)

        # 2. Generate strategy
        async with StrategyGenerator() as generator:
            result = await generator.generate_from_data(
                df=df,
                constraints=GenerationConstraints(
                    timeframes=[timeframe, '4h'],
                    risk_tolerance='medium',
                    style='balanced',
                    focus='all'
                ),
                symbol=symbol
            )

            if result.success:
                # 3. Save and backtest
                save_config(result.config, f"{symbol}_{timeframe}_strategy.json")
                backtest_result = run_backtest(result.config, df)

                print(f"Generated strategy for {symbol}")
                print(f"Backtest Sharpe: {backtest_result.sharpe:.2f}")
                print(f"Win Rate: {backtest_result.win_rate:.2%}")

                return result.config
            else:
                print(f"Generation failed: {result.errors}")
                return None

**Pattern 2: Enhance Underperforming Strategy**

.. code-block:: python

    async def improve_strategy(config_path: str):
        # 1. Load existing config
        config = ConfigLoader().load_config(config_path)

        # 2. Run backtest to identify issues
        df = load_recent_data(lookback_days=90)
        backtest_result = run_backtest(config, df)

        # 3. Determine focus area
        if backtest_result.sharpe < 1.0:
            focus = 'strategies'  # Poor performance - adjust strategies
        elif backtest_result.win_rate < 0.45:
            focus = 'indicators'  # Bad signals - improve indicators
        else:
            focus = 'regimes'  # Bad regime detection

        # 4. Enhance config
        async with StrategyGenerator() as generator:
            result = await generator.enhance_existing_config(
                config=config,
                df=df,
                focus=focus
            )

            if result.success:
                # 5. Compare before/after
                new_backtest = run_backtest(result.config, df)

                print(f"Enhancement Focus: {focus}")
                print(f"Sharpe: {backtest_result.sharpe:.2f} → {new_backtest.sharpe:.2f}")
                print(f"Win Rate: {backtest_result.win_rate:.2%} → {new_backtest.win_rate:.2%}")

                if new_backtest.sharpe > backtest_result.sharpe:
                    save_config(result.config, config_path)
                    print("✓ Enhanced config saved")
                else:
                    print("✗ Enhancement didn't improve performance")

**Pattern 3: Multi-Regime Strategy Generation**

.. code-block:: python

    async def generate_multi_regime_strategy():
        # 1. Analyze different market periods
        df_bull = load_data('BTCUSD', '2023-01-01', '2023-06-30')  # Bull market
        df_bear = load_data('BTCUSD', '2022-01-01', '2022-06-30')  # Bear market
        df_range = load_data('BTCUSD', '2021-06-01', '2021-12-31')  # Range-bound

        async with StrategyGenerator() as generator:
            # 2. Generate strategies for each regime
            bull_result = await generator.generate_from_data(
                df=df_bull,
                constraints=GenerationConstraints(focus='trend', style='aggressive'),
                symbol='BTCUSD'
            )

            bear_result = await generator.generate_from_data(
                df=df_bear,
                constraints=GenerationConstraints(focus='trend', style='defensive'),
                symbol='BTCUSD'
            )

            range_result = await generator.generate_from_data(
                df=df_range,
                constraints=GenerationConstraints(focus='range', style='balanced'),
                symbol='BTCUSD'
            )

            # 3. Merge into comprehensive config
            merged_config = merge_regime_configs(
                bull_result.config,
                bear_result.config,
                range_result.config
            )

            # 4. Validate merged config
            warnings, errors = generator._validate_generated_config(merged_config, None)

            if not errors:
                save_config(merged_config, 'btc_multi_regime_strategy.json')
                print("✓ Multi-regime strategy created")
            else:
                print(f"✗ Merge validation failed: {errors}")

**Pattern 4: Batch Strategy Generation**

.. code-block:: python

    async def generate_strategies_for_portfolio(symbols: list[str]):
        results = {}

        async with StrategyGenerator() as generator:
            for symbol in symbols:
                # Load data
                df = load_market_data(symbol, '1h', lookback_days=180)

                # Generate strategy
                result = await generator.generate_from_data(
                    df=df,
                    constraints=GenerationConstraints(
                        risk_tolerance='medium',
                        style='balanced',
                        focus='all'
                    ),
                    symbol=symbol
                )

                if result.success:
                    # Backtest
                    bt_result = run_backtest(result.config, df)

                    results[symbol] = {
                        'config': result.config,
                        'sharpe': bt_result.sharpe,
                        'win_rate': bt_result.win_rate
                    }

                    print(f"✓ {symbol}: Sharpe={bt_result.sharpe:.2f}, WR={bt_result.win_rate:.2%}")
                else:
                    print(f"✗ {symbol}: {result.errors}")

        # Save best strategies
        for symbol, data in results.items():
            if data['sharpe'] >= 1.5:  # Only save high-quality strategies
                save_config(data['config'], f"{symbol}_strategy.json")

Data Models
-----------

GenerationConstraints
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class GenerationConstraints(BaseModel):
        max_indicators: int = 10
        max_regimes: int = 5
        max_strategies: int = 5
        timeframes: list[str] = ["1h", "4h"]
        risk_tolerance: str = "medium"  # low, medium, high
        style: str = "balanced"  # conservative, balanced, aggressive
        focus: str = "all"  # trend, range, momentum, all

**Fields:**

* ``max_indicators``: Maximum number of indicators in generated config
* ``max_regimes``: Maximum number of regime definitions
* ``max_strategies``: Maximum number of strategy definitions
* ``timeframes``: Allowed timeframes for indicators
* ``risk_tolerance``: Risk tolerance level (affects stop loss, position size)
* ``style``: Trading style (affects aggressiveness of entry/exit)
* ``focus``: Strategic focus area

**Risk Tolerance Effects:**

.. code-block:: python

    # LOW risk tolerance
    - Position size: 3-5%
    - Stop loss: 1.5-2.5%
    - Take profit: 3-5%

    # MEDIUM risk tolerance
    - Position size: 5-10%
    - Stop loss: 2-3.5%
    - Take profit: 4-7%

    # HIGH risk tolerance
    - Position size: 8-15%
    - Stop loss: 3-5%
    - Take profit: 6-12%

**Style Effects:**

.. code-block:: python

    # CONSERVATIVE style
    - Fewer trades, higher quality entries
    - Multiple confirmation indicators
    - Wider profit targets

    # BALANCED style
    - Moderate trade frequency
    - Balance between signals and filters
    - Standard profit targets

    # AGGRESSIVE style
    - More trades, looser entry criteria
    - Fewer confirmation requirements
    - Closer profit targets

GenerationResult
~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class GenerationResult:
        success: bool
        config: TradingBotConfig | None
        reasoning: str
        warnings: list[str]
        errors: list[str]

**Fields:**

* ``success``: Whether generation succeeded without critical errors
* ``config``: Generated configuration (None if failed)
* ``reasoning``: LLM's reasoning for design choices
* ``warnings``: Non-critical issues (e.g., unused indicators)
* ``errors``: Critical issues that prevented generation

Best Practices
--------------

**1. Always Use Constraints:**

.. code-block:: python

    # ✅ Good: Define constraints to control generation
    constraints = GenerationConstraints(
        max_indicators=8,
        max_regimes=4,
        risk_tolerance='medium',
        style='balanced'
    )
    result = await generator.generate_from_data(df, constraints, 'BTCUSD')

    # ❌ Bad: No constraints (may generate overly complex config)
    result = await generator.generate_from_data(df, None, 'BTCUSD')

**2. Validate Generated Configs:**

.. code-block:: python

    # ✅ Good: Check warnings and errors
    result = await generator.generate_from_data(df, constraints, 'BTCUSD')

    if result.success:
        if result.warnings:
            print("⚠ Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")

        # Backtest before using
        bt_result = run_backtest(result.config, df)
        if bt_result.sharpe >= 1.0:
            save_config(result.config, 'strategy.json')
    else:
        print("✗ Generation failed")

    # ❌ Bad: Use config without validation
    result = await generator.generate_from_data(df, constraints, 'BTCUSD')
    save_config(result.config, 'strategy.json')  # May be invalid!

**3. Use Context Manager:**

.. code-block:: python

    # ✅ Good: Use async context manager for proper cleanup
    async with StrategyGenerator() as generator:
        result = await generator.generate_from_data(df, constraints, 'BTCUSD')
    # AIProviderFactory client is properly closed

    # ❌ Bad: Manual initialization/cleanup
    generator = StrategyGenerator()
    await generator._initialize_llm()
    result = await generator.generate_from_data(df, constraints, 'BTCUSD')
    # May leak resources!

**4. Provide Sufficient Data:**

.. code-block:: python

    # ✅ Good: Use 3-6 months of data for pattern detection
    df = load_market_data('BTCUSD', '1h', lookback_days=180)
    result = await generator.generate_from_data(df, constraints, 'BTCUSD')

    # ❌ Bad: Insufficient data
    df = load_market_data('BTCUSD', '1h', lookback_days=30)  # Only 1 month
    result = await generator.generate_from_data(df, constraints, 'BTCUSD')
    # May miss important patterns

See Also
--------

* :doc:`pattern_recognizer` - Detects patterns and structure for strategy generation
* :doc:`parameter_optimizer` - Optimizes generated strategy parameters
* :doc:`config_loader` - Loads and validates generated JSON configs
* :doc:`config_models` - JSON configuration models (TradingBotConfig)
* :doc:`backtest_engine` - Backtests generated strategies
