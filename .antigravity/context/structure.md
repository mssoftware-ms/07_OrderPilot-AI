# Code Structure

*Generated from `/mnt/d/03_Git/02_Python/07_OrderPilot-AI/src` - Signatures only (no code bodies)*

**Modules:** 952
**Classes:** 1610
**Methods:** 7890

---

## `src/ai/__init__.py`

### Module Functions
- async `get_ai_service(telemetry_callback)`  *Get AI service instance based on settings (OpenAI or Anthropic).*
- `reset_ai_service()`  *Reset the AI service instance (e.g., when settings change).*

## `src/ai/ai_provider_factory.py`

### `AIProviderFactory(object)`
*Factory for creating AI service instances based on configuration.*

- @staticmethod `get_provider()` → `str`  *Get the configured AI provider from QSettings.*
- @staticmethod `is_ai_enabled()` → `bool`  *Check if AI features are enabled.*
- @staticmethod `get_api_key(provider)` → `Optional[str]`  *Get API key for the specified provider.*
- @staticmethod `get_model(provider)` → `str`  *Get the configured model for the provider.*
- @staticmethod `create_service(telemetry_callback)`  *Create an AI service instance based on current settings.*
- @staticmethod `get_monthly_budget()` → `float`  *Get the configured monthly AI budget.*
- *...1 private methods*

## `src/ai/anthropic_service.py`

### `AnthropicService(BaseAIService)`
*Anthropic Claude service implementation.*

- *...6 private methods*
- `__init__(config, api_key, telemetry_callback)`  *Initialize Anthropic service.*

## `src/ai/base_service.py`

### `BaseAIService(ABC)`
*Abstract base class for AI provider services.*

- async `initialize()` → `None`  *Initialize the service.*
- async `close()` → `None`  *Close the service.*
- async `structured_completion(prompt, response_model, model, temperature, use_cache, context)` → `T`  *Get structured completion from AI provider.*
- async `analyze_order(order_data)` → `OrderAnalysis`  *Analyze an order for risk and approval.*
- async `triage_alert(alert_data)` → `AlertTriageResult`  *Triage an alert to determine priority and actions.*
- async `review_backtest(backtest_data)` → `BacktestReview`  *Review backtest results and provide insights.*
- `get_cost_summary()` → `dict[str, Any]`  *Get cost tracking summary.*
- `reset_costs()` → `None`  *Reset cost tracking (e.g., at start of new month).*
- `clear_cache()` → `None`  *Clear the response cache.*
- *...12 private methods*
- `__init__(config, api_key, telemetry_callback)`  *Initialize base AI service.*
- async `__aenter__()`  *Async context manager entry.*
- async `__aexit__(_exc_type, _exc_val, _exc_tb)`  *Async context manager exit.*

## `src/ai/gemini_service.py`

### `GeminiService(BaseAIService)`
*Google Gemini service implementation.*

- *...6 private methods*
- `__init__(config, api_key, telemetry_callback)`  *Initialize Gemini service.*

## `src/ai/openai_models.py`

### `OpenAIError(Exception)`
*Base exception for OpenAI service errors.*


### `RateLimitError(OpenAIError)`
*Raised when rate limit is exceeded.*


### `QuotaExceededError(OpenAIError)`
*Raised when monthly budget is exceeded.*


### `SchemaValidationError(OpenAIError)`
*Raised when response doesn't match schema.*


### `OrderAnalysis(BaseModel)`
*Structured output for order analysis.*


### `AlertTriageResult(BaseModel)`
*Structured output for alert triage.*


### `BacktestReview(BaseModel)`
*Structured output for backtest review.*


### `StrategySignalAnalysis(BaseModel)`
*Structured output for strategy signal post-analysis.*


### `StrategyTradeAnalysis(BaseModel)`
*Structured output for strategy trade analysis after Apply Strategy.*


## `src/ai/openai_service.py`

### `OpenAIService(OpenAIServiceClientMixin, OpenAIServicePromptMixin, OpenAIServiceAnalysisMixin, BaseAIService)`
*OpenAI service implementation.*

- *...6 private methods*
- `__init__(config, api_key, telemetry_callback)`  *Initialize OpenAI service.*

### Module Functions
- async `get_openai_service(config, api_key)` → `OpenAIService`  *Get or create OpenAI service instance (singleton pattern).*

## `src/ai/openai_service_analysis_mixin.py`

### `OpenAIServiceAnalysisMixin(object)`
*OpenAIServiceAnalysisMixin extracted from OpenAIService.*

- async `analyze_order(order_details, market_context)` → `OrderAnalysis`  *Analyze an order before placement.*
- async `triage_alert(alert, portfolio_context)` → `AlertTriageResult`  *Triage an alert for priority and action.*
- async `review_backtest(result)` → `BacktestReview`  *Review backtest results with AI analysis.*
- async `analyze_signal(signal, indicators)` → `StrategySignalAnalysis`  *Analyze a strategy signal.*
- async `analyze_strategy_trades(strategy_name, symbol, trades, stats, strategy_params)` → `StrategyTradeAnalysis`  *Analyze strategy trades and provide improvement suggestions.*

## `src/ai/openai_service_client_mixin.py`

### `OpenAIServiceClientMixin(object)`
*OpenAIServiceClientMixin extracted from OpenAIService.*

- async `initialize()` → `None`  *Initialize the service.*
- async `close()` → `None`  *Close the service.*
- async `structured_completion(prompt, response_model, model, temperature, use_cache, context)` → `T`  *Get structured completion from OpenAI.*
- async `chat_completion(messages, model, temperature)` → `str`  *Get chat completion from OpenAI (for conversational responses).*
- *...7 private methods*
- async `__aenter__()`  *Async context manager entry.*
- async `__aexit__(_exc_type, _exc_val, _exc_tb)`  *Async context manager exit.*

## `src/ai/openai_service_prompt_mixin.py`

### `OpenAIServicePromptMixin(object)`
*OpenAIServicePromptMixin extracted from OpenAIService.*

- *...4 private methods*

## `src/ai/openai_utils.py`

### `CostTracker(object)`
*Tracks AI API costs and enforces budget limits.*

- async `track_usage(model, input_tokens, output_tokens)` → `float`  *Track API usage and calculate cost.*
- `__init__(monthly_budget, warn_threshold)`  *Initialize cost tracker.*

### `CacheManager(object)`
*Manages caching of AI responses.*

- async `get(prompt, model, schema)` → `dict[str, Any] | None`  *Get cached response if available.*
- async `set(prompt, model, schema, response)` → `None`  *Cache a response.*
- *...2 private methods*
- `__init__(ttl_seconds)`  *Initialize cache manager.*

## `src/ai/parameter_optimizer.py`

### `OptimizationMethod(str, Enum)`
*Optimization methods.*


### `OptimizationObjective(str, Enum)`
*Optimization objectives.*


### `ParameterRange(object)`
*Parameter optimization range.*


### `OptimizationConfig(BaseModel)`
*Configuration for parameter optimization.*


### `OptimizationResult(BaseModel)`
*Result of parameter optimization.*


### `ParameterOptimizer(object)`
*Optimize strategy parameters using various algorithms.*

- `optimize_regime_thresholds(config, data, param_ranges, objective_fn)` → `OptimizationResult`  *Optimize regime threshold parameters.*
- `optimize_indicator_params(config, data, indicator_id, param_ranges)` → `OptimizationResult`  *Optimize parameters for a specific indicator.*
- `optimize_risk_params(config, data, strategy_id)` → `OptimizationResult`  *Optimize risk parameters for a specific strategy.*
- `apply_best_params(config, params, target_type, target_id)` → `TradingBotConfig`  *Apply optimized parameters to configuration.*
- *...17 private methods*
- `__init__(config)` → `None`  *Initialize parameter optimizer.*

## `src/ai/pattern_recognizer.py`

### `PatternType(str, Enum)`
*Chart pattern types.*


### `MarketPhase(str, Enum)`
*Market structure phases.*


### `VolatilityRegime(str, Enum)`
*Volatility regimes.*


### `Pattern(object)`
*Detected chart pattern.*


### `MarketStructure(BaseModel)`
*Market structure analysis.*


### `VolatilityAnalysis(BaseModel)`
*Volatility regime analysis.*


### `PatternRecognizer(object)`
*Detect market patterns for regime classification.*

- `detect_chart_patterns(df)` → `list[Pattern]`  *Detect chart patterns in OHLCV data.*
- `detect_market_structure(df)` → `MarketStructure`  *Detect market structure and phase.*
- `classify_volatility_regime(df)` → `VolatilityAnalysis`  *Classify volatility regime.*
- *...13 private methods*
- `__init__(lookback_periods)` → `None`  *Initialize pattern recognizer.*

## `src/ai/prompts_schemas.py`

### `JSONSchemas(object)`
*JSON schemas for structured outputs.*


## `src/ai/prompts_templates.py`

### `PromptTemplates(object)`
*Collection of prompt templates for different AI tasks.*


## `src/ai/prompts_validator.py`

### `SchemaValidator(object)`
*Utility for validating AI responses against schemas.*

- @staticmethod `validate_order_analysis(response)` → `bool`  *Validate order analysis response.*
- @staticmethod `validate_alert_triage(response)` → `bool`  *Validate alert triage response.*
- @staticmethod `validate_backtest_review(response)` → `bool`  *Validate backtest review response.*
- @staticmethod `validate_signal_analysis(response)` → `bool`  *Validate signal analysis response.*
- *...1 private methods*

## `src/ai/prompts_versioning.py`

### `PromptVersion(object)`
*Manages prompt versions for A/B testing and improvements.*

- @classmethod `get_prompt(prompt_type, version)` → `str`  *Get a specific version of a prompt.*

## `src/ai/provider_base.py`

### `AIProvider(str, Enum)`
*Supported AI providers.*


### `ReasoningMode(str, Enum)`
*Reasoning modes for AI models.*


### `ProviderConfig(BaseModel)`
*Configuration for an AI provider.*


### `AIProviderBase(ABC)`
*Abstract base class for AI providers.*

- async `initialize()` → `None`  *Initialize the provider.*
- async `close()` → `None`  *Close the provider.*
- async `structured_completion(prompt, response_model)` → `T`  *Get structured completion from the AI model.*
- async `stream_completion(prompt)` → `AsyncIterator[str]`  *Stream completion from the AI model.*
- `__init__(config)`  *Initialize provider.*

## `src/ai/provider_gemini.py`

### `GeminiProvider(AIProviderBase)`
*Google Gemini AI provider.*

- async `structured_completion(prompt, response_model)` → `T`  *Get structured completion from Gemini.*
- async `stream_completion(prompt)` → `AsyncIterator[str]`  *Stream completion from Gemini.*
- `__init__(config)`  *Initialize Gemini provider.*

## `src/ai/providers.py`

### `OpenAIProvider(AIProviderBase)`
*OpenAI API provider supporting GPT-5.1 and thinking modes.*

- async `structured_completion(prompt, response_model)` → `T`  *Get structured completion from OpenAI.*
- async `stream_completion(prompt)` → `AsyncIterator[str]`  *Stream completion from OpenAI.*
- *...1 private methods*
- `__init__(config)`  *Initialize OpenAI provider.*

### `AnthropicProvider(AIProviderBase)`
*Anthropic API provider supporting Claude Sonnet 4.5.*

- async `structured_completion(prompt, response_model)` → `T`  *Get structured completion from Anthropic.*
- async `stream_completion(prompt)` → `AsyncIterator[str]`  *Stream completion from Anthropic.*
- `__init__(config)`  *Initialize Anthropic provider.*

### Module Functions
- `create_provider(provider, model)` → `AIProviderBase`  *Create an AI provider instance.*
- async `get_openai_gpt51_thinking()` → `OpenAIProvider`  *Get OpenAI GPT-5.1 with thinking mode.*
- async `get_openai_gpt51_instant()` → `OpenAIProvider`  *Get OpenAI GPT-5.1 Instant (no thinking).*
- async `get_anthropic_sonnet45()` → `AnthropicProvider`  *Get Anthropic Claude Sonnet 4.5.*
- async `get_gemini_flash()` → `GeminiProvider`  *Get Google Gemini 2.0 Flash (experimental).*
- async `get_gemini_pro()` → `GeminiProvider`  *Get Google Gemini 1.5 Pro.*

## `src/ai/strategy_generator.py`

### `GenerationConstraints(BaseModel)`
*Constraints for strategy generation.*


### `GenerationResult(BaseModel)`
*Result of strategy generation.*


### `StrategyGenerator(object)`
*Generate trading strategies using LLM.*

- async `initialize()` → `bool`  *Initialize AI service.*
- async `close()` → `None`  *Close AI service.*
- async `generate_from_patterns(patterns, market_structure, volatility, constraints, symbol)` → `GenerationResult | None`  *Generate trading bot config from detected patterns.*
- async `generate_from_data(df, constraints, symbol)` → `GenerationResult | None`  *Generate strategy from OHLCV data.*
- async `enhance_existing_config(config, df, focus)` → `GenerationResult | None`  *Enhance existing configuration based on market data.*
- *...11 private methods*
- `__init__()` → `None`  *Initialize strategy generator.*

## `src/analysis/basic_bad_tick_detector.py`

### `BadTickDetector(object)`
*Detects and removes bad ticks from market data using threshold-based methods.*

- `detect_bad_ticks(df)` → `pd.Series`  *Detect bad ticks in DataFrame.*
- `clean_data(df, method)` → `tuple[pd.DataFrame, CleaningStats]`  *Clean bad ticks from DataFrame.*
- *...5 private methods*
- `__init__(max_price_deviation_pct, min_volume, max_volume_multiplier, ma_window, check_ohlc_consistency, check_price_spikes, check_volume_anomalies, check_duplicates)`  *Initialize bad tick detector.*

## `src/analysis/cleaning_types.py`

### `CleaningStats(object)`
*Statistics from data cleaning operation.*


## `src/analysis/data_cleaning.py`

### Module Functions
- `clean_historical_data(symbol, source, db_path, method, save_cleaned)` → `CleaningStats`  *Clean historical data from database.*

## `src/analysis/entry_signals/entry_signal_engine_core.py`

### `RegimeType(str, Enum)`
*Market regime classification (unified v2.0 naming).*


### `EntrySide(str, Enum)`
*Entry direction (compatible with existing types).*


### `EntryEvent(object)`
*A detected entry signal.*

- `to_chart_marker()` → `dict[str, Any]`  *Convert to TradingView Lightweight Charts marker format.*

### `OptimParams(object)`
*Optimizable parameters for the entry signal engine.*


### Module Functions
- `calculate_features(candles, params)` → `dict[str, list[float]]`  *Calculate technical features from candles.*
- `_init_entry_registry()`  *Initialize entry generator registry (singleton pattern).*
- `generate_entries(candles, features, regime, params)` → `list[EntryEvent]`  *Generate entry signals using Rule Type Pattern.*
- `_postprocess_entries(entries, cooldown_bars, cluster_window_bars)` → `list[EntryEvent]`  *Postprocess entries: cluster and cooldown.*
- `debug_summary(features)` → `dict[str, float]`  *Generate debug summary of features.*

## `src/analysis/entry_signals/entry_signal_engine_indicators.py`

### Module Functions
- `_safe_float(x, default)` → `float`  *Safely convert to float.*
- `_clamp(x, lo, hi)` → `float`  *Clamp value to range.*
- `_sma(values, period)` → `list[float]`  *Simple moving average.*
- `_ema(values, period)` → `list[float]`  *Exponential moving average.*
- `_rsi(closes, period)` → `list[float]`  *Relative Strength Index.*
- `_atr(highs, lows, closes, period)` → `list[float]`  *Average True Range.*
- `_bollinger(closes, period, std_mult)` → `tuple[list[float], list[float], list[float], list[float], list[float]]`  *Bollinger Bands.*
- `_adx(highs, lows, closes, period)` → `list[float]`  *Average Directional Index (returns only ADX for backward compatibility).*
- `_adx_full(highs, lows, closes, period)` → `tuple[list[float], list[float], list[float]]`  *Average Directional Index with DI+ and DI-.*
- `_wick_ratios(candles)` → `tuple[list[float], list[float]]`  *Calculate upper and lower wick ratios.*
- `_pivots(highs, lows, lookback)` → `tuple[list[bool], list[bool]]`  *Detect pivot highs and lows.*

## `src/analysis/entry_signals/entry_signal_engine_regime.py`

### Module Functions
- `detect_regime(features, params)` → `'RegimeType'`  *Detect market regime from features.*
- `detect_regime_v2(features, regime_config)` → `str`  *Detect market regime dynamically from JSON config.*
- `_extract_regimes_from_config(config)` → `list[dict]`  *Extract regimes list from config (supports multiple formats).*
- `_is_bullish_regime(regime_id)` → `bool`  *Check if regime is bullish based on ID (dynamic pattern matching).*
- `_is_bearish_regime(regime_id)` → `bool`  *Check if regime is bearish based on ID (dynamic pattern matching).*
- `_evaluate_threshold(threshold_name, threshold_value, feature_values)` → `bool`  *Evaluate a single threshold dynamically based on naming pattern.*

## `src/analysis/entry_signals/generators/base_generator.py`

### `BaseEntryGenerator(ABC)`
*Abstract base class for entry signal generators.*

- `can_generate(regime)` → `bool`  *Check if this generator handles the given regime type.*
- `generate(candles, features, params)` → `list[EntryEvent]`  *Generate entry signals for this regime type.*
- *...2 private methods*
- `__init__(regime)`  *Initialize generator.*

## `src/analysis/entry_signals/generators/highvol_generator.py`

### `HighVolGenerator(BaseEntryGenerator)`
*Generator for HIGH_VOL regime entries.*

- `can_generate(regime)` → `bool`  *Check if this generator handles HIGH_VOL.*
- `generate(candles, features, params)` → `list[EntryEvent]`  *Generate conservative entries for HIGH_VOL regime.*
- *...1 private methods*
- `__init__()`  *Initialize HIGH_VOL generator.*

## `src/analysis/entry_signals/generators/range_generator.py`

### `RangeGenerator(BaseEntryGenerator)`
*Generator for RANGE (sideways) mean-reversion entries.*

- `can_generate(regime)` → `bool`  *Check if this generator handles RANGE.*
- `generate(candles, features, params)` → `list[EntryEvent]`  *Generate mean-reversion entries for RANGE regime.*
- *...1 private methods*
- `__init__()`  *Initialize RANGE generator.*

## `src/analysis/entry_signals/generators/registry.py`

### `EntryGeneratorRegistry(object)`
*Registry for entry signal generators.*

- `register(generator)` → `None`  *Register a new generator.*
- `generate(candles, features, regime, params)` → `list[EntryEvent]`  *Generate entries using the appropriate generator.*
- `has_generator_for(regime)` → `bool`  *Check if a generator exists for the given regime.*
- `__init__()`  *Initialize empty registry.*

## `src/analysis/entry_signals/generators/squeeze_generator.py`

### `SqueezeGenerator(BaseEntryGenerator)`
*Generator for SQUEEZE breakout entries.*

- `can_generate(regime)` → `bool`  *Check if this generator handles SQUEEZE.*
- `generate(candles, features, params)` → `list[EntryEvent]`  *Generate breakout entries for SQUEEZE regime.*
- *...1 private methods*
- `__init__()`  *Initialize SQUEEZE generator.*

## `src/analysis/entry_signals/generators/trend_generator.py`

### `TrendUpGenerator(BaseEntryGenerator)`
*Generator for TREND_UP (bullish) pullback entries.*

- `can_generate(regime)` → `bool`  *Check if this generator handles TREND_UP.*
- `generate(candles, features, params)` → `list[EntryEvent]`  *Generate LONG entries for TREND_UP regime.*
- *...1 private methods*
- `__init__()`  *Initialize TREND_UP generator.*

### `TrendDownGenerator(BaseEntryGenerator)`
*Generator for TREND_DOWN (bearish) pullback entries.*

- `can_generate(regime)` → `bool`  *Check if this generator handles TREND_DOWN.*
- `generate(candles, features, params)` → `list[EntryEvent]`  *Generate SHORT entries for TREND_DOWN regime.*
- *...1 private methods*
- `__init__()`  *Initialize TREND_DOWN generator.*

## `src/analysis/entry_signals/params_loader.py`

### Module Functions
- `load_optim_params_from_json(json_path)` → `OptimParams`  *Load OptimParams from entry_analyzer_regime.json format (v2.0 support).*
- `_flatten_v2_params(indicators, regimes)` → `dict[str, Any]`  *Flatten v2.0 nested params structure to v1.0 flattened format.*
- `_map_v2_indicator_name_to_v1_id(name, ind_type)` → `str`  *Map v2.0 indicator name to v1.0 indicator ID.*
- `_build_optim_params_from_opt_result(params, config)` → `OptimParams`  *Build OptimParams from optimization_results.params.*
- `_build_optim_params_from_indicators(config)` → `OptimParams`  *Build OptimParams from indicators array.*
- `_get_entry_params(config)` → `dict`  *Extract entry_params from config.*
- `_convert_bb_width_percentile(percentile, default)` → `float`  *Convert BB width percentile (0-100) to squeeze ratio.*
- `get_default_json_path()` → `Path`  *Get the default path for entry_analyzer_regime.json.*

## `src/analysis/hampel_bad_tick_detector.py`

### `HampelBadTickDetector(object)`
*Advanced bad tick detector using Hampel Filter with Volume Confirmation.*

- `detect_outliers_mad(df, col)` → `pd.Series`  *Detect price outliers using Median Absolute Deviation (MAD).*
- `detect_bad_ticks(df)` → `pd.Series`  *Detect bad ticks using Hampel Filter + Volume Confirmation.*
- `clean_data(df, method)` → `tuple[pd.DataFrame, CleaningStats]`  *Clean bad ticks from DataFrame using Hampel Filter.*
- *...2 private methods*
- `__init__(window, threshold, vol_filter_mult)`  *Initialize Hampel Filter with Volume Confirmation.*

## `src/analysis/indicator_optimization/candidate_space.py`

### `ParameterRange(object)`
*Defines a range or set of choices for a parameter.*

- `sample()` → `Any`  *Sample a value from this range.*

### `CandidateSpace(object)`
*Defines the search space for optimization.*

- `sample_params(base_params)` → `OptimParams`  *Sample a new set of parameters based on the defined ranges.*
- `__init__()` → `None`  *Initialize the candidate space with default ranges.*

## `src/analysis/indicator_optimization/optimizer.py`

### `FastOptimizer(object)`
*Fast random search optimizer.*

- `optimize(candles, base_params, budget_ms, seed)` → `OptimParams`  *Run fast optimization.*
- *...1 private methods*
- `__init__(candidate_space)` → `None`  *Initialize the optimizer.*

## `src/analysis/patterns/ascending_triangle.py`

### `AscendingTriangleDetector(BaseDetector)`
*Detector for Ascending Triangle pattern.*

- `detect(df)` → `List[Pattern]`  *Detect Ascending Triangle patterns.*
- *...5 private methods*
- `__init__(min_pattern_bars, min_score, pivot_window, max_resistance_variance_pct)`  *Initialize Ascending Triangle detector.*

### Module Functions
- `_simple_linregress(x, y)` → `Tuple[float, float]`  *Simple linear regression without scipy.*

## `src/analysis/patterns/base_detector.py`

### `DirectionBias(str, Enum)`
*Pattern direction bias.*


### `Pivot(object)`
*Price pivot point (swing high/low).*


### `Pattern(object)`
*Detected chart pattern.*


### `BaseDetector(ABC)`
*Abstract base class for pattern detectors.*

- `detect(df)` → `List[Pattern]`  *Detect patterns in price data.*
- `detect_pivots(df, window)` → `List[Pivot]`  *Detect swing highs and lows (pivot points).*
- *...6 private methods*
- `__init__(min_pattern_bars, min_score, pivot_window)`  *Initialize detector.*

## `src/analysis/patterns/continuation_patterns.py`

### `TriangleParams(object)`


### `TriangleDetector(PatternDetector)`
*Detects contracting triangles from alternating pivots.*

- `detect(pivots)` → `List[Pattern]`
- `score_raw(upper_slope, lower_slope)` → `float`
- `score(pattern)` → `float`
- `lines(pattern)` → `Dict[str, list]`
- `__init__(params)`

### `FlagParams(object)`


### `FlagDetector(PatternDetector)`
*Detect simple flags: impulsive move followed by small channel pullback.*

- `detect(pivots)` → `List[Pattern]`
- `score_raw(move, pull, slope)` → `float`
- `score(pattern)` → `float`
- `lines(pattern)` → `Dict[str, list]`
- `__init__(params)`

## `src/analysis/patterns/cup_and_handle.py`

### `CupAndHandleDetector(BaseDetector)`
*Detector for Cup and Handle pattern.*

- `detect(df)` → `List[Pattern]`  *Detect Cup and Handle patterns.*
- *...4 private methods*
- `__init__(min_pattern_bars, min_score, pivot_window, min_cup_depth_pct, max_cup_depth_pct, max_handle_depth_pct)`  *Initialize Cup and Handle detector.*

## `src/analysis/patterns/named_patterns.py`

### `Pattern(object)`


### `PatternDetector(Protocol)`

- `detect(pivots)` → `List[Pattern]`
- `score(pattern)` → `float`
- `lines(pattern)` → `Dict[str, list]`

## `src/analysis/patterns/pattern_visualizer.py`

### Module Functions
- `pattern_to_lines(pattern)` → `Dict[str, List[Tuple[int, float]]]`
- `pattern_to_boxes(pattern)` → `Dict[str, Tuple[int, int, float, float]]`  *Convert pattern metadata (e.g., order blocks/FVG) to drawable boxes.*

## `src/analysis/patterns/pivot_engine.py`

### `Pivot(object)`


### Module Functions
- `_ensure_series(data)` → `pd.Series`
- `detect_pivots_percent(prices, threshold_pct)` → `List[Pivot]`  *Percent-basierte ZigZag-Pivots.*
- `_true_range(df)` → `pd.Series`
- `detect_pivots_atr(df, atr_mult, atr_period)` → `List[Pivot]`  *ATR-basierte Pivot-Erkennung auf Basis von OHLC.*
- `validate_swing_point(prices, pivot_idx, lookback_left, lookback_right)` → `bool`  *Check if pivot_idx is local extrema in window.*
- `filter_minor_pivots(pivots, min_distance_bars)` → `List[Pivot]`  *Remove pivots that are too close; keep more extreme.*

## `src/analysis/patterns/reversal_patterns.py`

### `HSParams(object)`


### `HeadAndShouldersDetector(PatternDetector)`
*Detect classical Head & Shoulders (and inverse) using pivots.*

- `detect(pivots)` → `List[Pattern]`
- `score_raw(head_prom, neckline_slope)` → `float`
- `score(pattern)` → `float`
- `lines(pattern)` → `Dict[str, list]`
- *...1 private methods*
- `__init__(params)`

### `DoubleTopBottomDetector(PatternDetector)`
*Double Top / Double Bottom.*

- `detect(pivots)` → `List[Pattern]`
- `score_raw(p1, p3, mid, is_top)` → `float`
- `score(pattern)` → `float`
- `lines(pattern)` → `Dict[str, list]`
- *...1 private methods*
- `__init__(tolerance, min_separation)`

### Module Functions
- `within_ratio(a, b, tol)` → `bool`

## `src/analysis/patterns/smart_money.py`

### Module Functions
- `detect_order_blocks(df, lookback)` → `List[Pattern]`  *Detect bullish order blocks: last down candle before close breaks prior high.*
- `detect_fvg(df)` → `List[Pattern]`  *Detect fair value gaps (simple 3-candle gap).*

## `src/analysis/patterns/triple_bottom.py`

### `TripleBottomDetector(BaseDetector)`
*Detector for Triple Bottom pattern.*

- `detect(df)` → `List[Pattern]`  *Detect Triple Bottom patterns.*
- *...4 private methods*
- `__init__(min_pattern_bars, min_score, pivot_window, max_bottom_variance_pct)`  *Initialize Triple Bottom detector.*

## `src/analysis/stream_bad_tick_filter.py`

### `StreamBadTickFilter(object)`
*Real-time bad tick filter for streaming data.*

- `filter_bar(bar)` → `tuple[bool, str | None]`  *Filter a single incoming bar.*
- *...1 private methods*
- `__init__(detector, window_size)`  *Initialize stream filter.*

## `src/analysis/visible_chart/analyzer.py`

### `VisibleChartAnalyzer(object)`
*Analyzes visible chart range and generates entry signals.*

- `set_json_config_path(json_path)` → `None`  *Set or update the JSON config path.*
- `analyze(visible_range, symbol, timeframe)` → `AnalysisResult`  *Analyze the visible chart range (loads candles from database).*
- `analyze_with_candles(visible_range, symbol, timeframe, candles)` → `AnalysisResult`  *Analyze with pre-loaded candle data.*
- *...12 private methods*
- `__init__(use_optimizer, use_cache, cache, json_config_path)` → `None`  *Initialize the analyzer.*

## `src/analysis/visible_chart/background_runner.py`

### `TaskType(str, Enum)`
*Types of background tasks.*


### `AnalysisTask(object)`
*A task to be executed by the background worker.*

- `__lt__(other)` → `bool`  *Compare tasks by priority for queue ordering.*

### `RunnerConfig(object)`
*Configuration for the background runner.*


### `PerformanceMetrics(object)`
*Performance metrics for the background runner.*

- `record_analysis(time_ms)` → `None`  *Record an analysis duration.*

### `BackgroundRunner(object)`
*Runs entry analysis in a background thread.*

- `start()` → `None`  *Start the background worker and scheduler.*
- `stop()` → `None`  *Stop the background worker and scheduler.*
- `request_analysis(visible_range, symbol, timeframe, force)` → `bool`  *Request a full analysis of the visible range.*
- `push_new_candles(candles, visible_range, symbol, timeframe)` → `bool`  *Push new candles for incremental update.*
- `get_metrics()` → `PerformanceMetrics`  *Get performance metrics.*
- `get_last_result()` → `AnalysisResult | None`  *Get the last analysis result.*
- *...10 private methods*
- `__init__(config)` → `None`  *Initialize the background runner.*

## `src/analysis/visible_chart/cache.py`

### `CacheEntry(object)`
*A cached value with metadata.*

- `is_expired()` → `bool`  *Check if entry has expired.*
- `increment_hits()` → `None`  *Increment hit counter.*

### `CacheStats(object)`
*Cache performance statistics.*

- @property `hit_rate()` → `float`  *Calculate overall hit rate.*

### `AnalyzerCache(object)`
*Thread-safe cache for analyzer computations.*

- `get_features(symbol, timeframe, visible_range)` → `dict[str, list[float]] | None`  *Get cached features if available.*
- `set_features(symbol, timeframe, visible_range, features)` → `None`  *Cache calculated features.*
- `get_regime(symbol, timeframe, visible_range)` → `RegimeType | None`  *Get cached regime if available.*
- `set_regime(symbol, timeframe, visible_range, regime)` → `None`  *Cache detected regime.*
- `get_optimizer_result(symbol, timeframe, visible_range, regime)` → `dict[str, Any] | None`  *Get cached optimizer result if available.*
- `set_optimizer_result(symbol, timeframe, visible_range, regime, result)` → `None`  *Cache optimizer result.*
- `invalidate_all()` → `None`  *Clear all caches.*
- `invalidate_symbol(symbol)` → `int`  *Invalidate all caches for a symbol.*
- `get_stats()` → `CacheStats`  *Get cache statistics.*
- `get_size()` → `dict[str, int]`  *Get current cache sizes.*
- *...6 private methods*
- `__init__(feature_ttl, regime_ttl, optimizer_ttl)` → `None`  *Initialize the cache.*

### Module Functions
- `get_analyzer_cache()` → `AnalyzerCache`  *Get or create the global analyzer cache.*
- `reset_analyzer_cache()` → `None`  *Reset the global cache (for testing).*

## `src/analysis/visible_chart/candle_loader.py`

### `CandleLoader(object)`
*Loads candle data for the visible chart range.*

- `load(symbol, from_ts, to_ts, timeframe)` → `list[dict]`  *Load candle data for the visible range.*
- *...4 private methods*

## `src/analysis/visible_chart/debug_logger.py`

### Module Functions
- `setup_entry_analyzer_logger()` → `logging.Logger`  *Setup dedicated logger for Entry Analyzer debugging.*

## `src/analysis/visible_chart/entry_copilot.py`

### `SignalQuality(str, Enum)`
*Quality rating for entry signals.*


### `EntryAssessment(BaseModel)`
*AI assessment of a single entry signal.*


### `AnalysisSummary(BaseModel)`
*AI summary of the overall analysis.*


### `CopilotResponse(BaseModel)`
*Complete copilot response for entry analysis.*


### `ValidationReview(BaseModel)`
*AI review of validation results.*


### `CopilotConfig(object)`
*Configuration for the Entry Copilot.*


### `EntryCopilot(object)`
*AI-powered copilot for entry signal analysis.*

- async `initialize()` → `bool`  *Initialize the AI service.*
- async `close()` → `None`  *Close the AI service.*
- async `analyze_entries(analysis, symbol, timeframe, validation, candles)` → `CopilotResponse | None`  *Analyze entries and provide AI recommendations.*
- async `review_validation(validation, symbol)` → `ValidationReview | None`  *Review validation results for reliability.*
- async `get_quick_assessment(entry, regime, symbol)` → `EntryAssessment | None`  *Get quick assessment of a single entry.*
- *...7 private methods*
- `__init__(config)` → `None`  *Initialize the copilot.*

### Module Functions
- async `get_entry_analysis(analysis, symbol, timeframe, validation)` → `CopilotResponse | None`  *Convenience function for getting entry analysis.*
- `run_entry_analysis_sync(analysis, symbol, timeframe, validation)` → `CopilotResponse | None`  *Synchronous wrapper for entry analysis.*

## `src/analysis/visible_chart/indicator_families.py`

### `IndicatorFamily(str, Enum)`
*Available indicator families.*


### `ParameterRange(object)`
*Defines a parameter's valid range for optimization.*

- `sample_values(n_samples)` → `list[float]`  *Generate sample values within range.*
- `random_value()` → `float`  *Generate random value within range.*

### `IndicatorConfig(object)`
*Configuration for a single indicator.*

- `get_default_params()` → `dict[str, float]`  *Get default parameter values.*
- `randomize_params()` → `dict[str, float]`  *Generate random parameter values.*

### `OptimizableSet(object)`
*A complete set of indicators for optimization.*

- `to_indicator_set(name, regime, score)`  *Convert to IndicatorSet for display.*

### Module Functions
- `get_candidates_for_regime(regime)` → `list[IndicatorConfig]`  *Get suitable indicator candidates for a given regime.*
- `get_all_indicators()` → `dict[IndicatorFamily, list[IndicatorConfig]]`  *Get all available indicators grouped by family.*

## `src/analysis/visible_chart/objective.py`

### `ObjectiveConfig(object)`
*Configuration for objective function.*


### `ObjectiveResult(object)`
*Result of objective function evaluation.*

- @classmethod `invalid(reason)` → `ObjectiveResult`  *Create an invalid result with score = -inf.*

### `ObjectiveFunction(object)`
*Evaluates indicator sets based on trade simulation results.*

- `evaluate(sim_result, n_indicators, hours_analyzed)` → `ObjectiveResult`  *Evaluate simulation result and return score.*
- `compare(result_a, result_b)` → `int`  *Compare two objective results.*
- *...1 private methods*
- `__init__(config)` → `None`  *Initialize the objective function.*

### Module Functions
- `create_objective_for_regime(regime)` → `ObjectiveFunction`  *Create objective function tuned for specific regime.*

## `src/analysis/visible_chart/optimizer.py`

### `OptimizerConfig(object)`
*Configuration for the optimizer.*


### `OptimizationResult(object)`
*Result of optimization run.*


### `FastOptimizer(object)`
*Fast optimizer using random search with early stopping.*

- `optimize(candles, regime, features)` → `OptimizationResult`  *Run optimization to find best indicator set.*
- `clear_cache()` → `None`  *Clear the feature cache.*
- *...5 private methods*
- `__init__(config)` → `None`  *Initialize the optimizer.*

## `src/analysis/visible_chart/report_generator.py`

### `ReportConfig(object)`
*Configuration for report generation.*


### `ReportData(object)`
*Consolidated data for report generation.*


### `ReportGenerator(object)`
*Generates analysis reports in multiple formats.*

- `generate_markdown(data)` → `str`  *Generate markdown report.*
- `generate_json(data)` → `dict[str, Any]`  *Generate JSON report.*
- `save_report(data, base_name, formats)` → `dict[str, Path]`  *Save report to files.*
- `__init__(config)` → `None`  *Initialize the generator.*

### Module Functions
- `create_report_from_analysis(analysis, symbol, timeframe, simulation, validation, filter_stats)` → `ReportData`  *Create ReportData from an AnalysisResult.*

## `src/analysis/visible_chart/trade_filters.py`

### `FilterReason(str, Enum)`
*Reasons for filtering an entry.*


### `FilterResult(object)`
*Result of applying a filter to an entry.*


### `FilterConfig(object)`
*Configuration for trade filters.*


### `FilterStats(object)`
*Statistics from filter application.*

- @property `pass_rate()` → `float`  *Calculate pass rate.*

### `TradeFilter(object)`
*Filters entries based on market conditions.*

- `filter_entries(entries, candles, spreads)` → `tuple[list[EntryEvent], FilterStats]`  *Filter entries based on market conditions.*
- `get_stats()` → `FilterStats`  *Get filter statistics.*
- `reset_stats()` → `None`  *Reset filter statistics.*
- *...4 private methods*
- `__init__(config)` → `None`  *Initialize the filter.*

### Module Functions
- `create_default_filter()` → `TradeFilter`  *Create a trade filter with sensible defaults.*
- `create_crypto_filter()` → `TradeFilter`  *Create a trade filter tuned for crypto markets.*

## `src/analysis/visible_chart/trade_simulator.py`

### `TradeResult(object)`
*Result of a single simulated trade.*

- @property `side()` → `EntrySide`  *Trade side.*

### `SimulationConfig(object)`
*Configuration for trade simulation.*


### `SimulationResult(object)`
*Aggregated results of trade simulation.*

- @classmethod `from_trades(trades)` → `SimulationResult`  *Calculate statistics from trade list.*

### `TradeSimulator(object)`
*Simulates trades based on entry signals over candle data.*

- `simulate(entries, candles, features)` → `SimulationResult`  *Simulate trades for given entries.*
- *...2 private methods*
- `__init__(config)` → `None`  *Initialize the simulator.*

## `src/analysis/visible_chart/types.py`

### `EntrySide(str, Enum)`
*Entry direction.*


### `RegimeType(str, Enum)`
*Market regime classification.*

- @classmethod `from_string(regime_id)` → `'RegimeType'`  *Convert string regime ID to RegimeType enum.*

### `EntryEvent(object)`
*A detected entry signal in the visible chart.*

- `to_chart_marker()` → `dict[str, Any]`  *Convert to TradingView Lightweight Charts marker format.*

### `VisibleRange(object)`
*Visible chart time range.*

- @property `duration_seconds()` → `int`  *Duration of visible range in seconds.*
- @property `duration_minutes()` → `int`  *Duration of visible range in minutes.*

### `IndicatorSet(object)`
*Optimized indicator configuration.*

- `to_display_dict()` → `dict[str, Any]`  *Convert to display format for UI.*

### `AnalysisResult(object)`
*Result of visible chart analysis.*

- @property `long_count()` → `int`  *Number of LONG entries.*
- @property `short_count()` → `int`  *Number of SHORT entries.*
- @property `signal_rate_per_hour()` → `float`  *Signals per hour based on visible range.*

## `src/analysis/visible_chart/validation.py`

### `ValidationConfig(object)`
*Configuration for walk-forward validation.*


### `FoldResult(object)`
*Result from a single validation fold.*

- @property `is_overfit()` → `bool`  *Check if fold shows signs of overfitting.*
- @property `train_test_ratio()` → `float`  *Ratio of train to test performance.*

### `ValidationResult(object)`
*Aggregated results from walk-forward validation.*

- @classmethod `from_folds(folds, config, seed_used, total_time_ms)` → `ValidationResult`  *Calculate aggregated metrics from fold results.*

### `WalkForwardValidator(object)`
*Walk-forward validation for entry optimization.*

- `validate(candles, regime, features)` → `ValidationResult`  *Run walk-forward validation.*
- *...4 private methods*
- `__init__(config)` → `None`  *Initialize the validator.*

### Module Functions
- `validate_with_walkforward(candles, regime, features, config)` → `ValidationResult`  *Convenience function for walk-forward validation.*

## `src/analysis/zscore_volatility_filter.py`

### `ZScoreVolatilityFilter(object)`
*Z-Score based filter that REPLACES bad tick values inline.*

- `clean_data_inline(df)` → `pd.DataFrame`  *Clean bad ticks by REPLACING extreme High/Low values inline.*
- `filter_single_bar(bar_dict, recent_bars)` → `tuple[dict, bool]`  *Filter a single incoming bar in real-time.*
- `__init__(volatility_window, z_threshold, median_window, min_volume)`  *Initialize Z-Score Volatility Filter.*

## `src/backtesting/advanced_validation.py`

### `WalkForwardWindow(object)`


### `ValidationResult(object)`


### `MarketPhase(object)`


### `OutOfSampleValidator(object)`

- `validate()` → `ValidationResult`
- `__init__(df, split_ratio, scorer)`

### `MarketPhaseAnalyzer(object)`

- `detect_phases(window_days)` → `List[MarketPhase]`
- `analyze(params)` → `Dict[str, Dict[str, float]]`
- *...1 private methods*
- `__init__(df, scorer)`

### `WalkForwardAnalyzer(object)`

- `run()` → `Dict`
- *...1 private methods*
- `__init__(df, train_days, test_days, step_days, max_trials, scorer)`

### Module Functions
- `_compute_score(candles)` → `float`  *Simple, deterministic score based on EMA/RSI profile.*

## `src/backtesting/config_adapter.py`

### `BacktestConfigAdapter(object)`
*Adapter to convert between config formats.*

- @staticmethod `from_file(config_path)`  *Load config from JSON file using main ConfigLoader.*
- @staticmethod `from_main_config(main_config)`  *Convert main TradingBotConfig to BacktestEngine format.*
- *...3 private methods*

### Module Functions
- `load_config_for_backtest(config_path)`  *Load JSON config for backtesting.*

## `src/backtesting/data_loader.py`

### `DataLoader(object)`

- `load_data(symbol, start_date, end_date, source)` → `pd.DataFrame`  *Load market data from SQLite.*
- `resample_data(df, timeframe)` → `pd.DataFrame`  *Resample 1m data to target timeframe.*
- `__init__(db_path)`

### Module Functions
- `_get_api_client()`  *Lazy initialization of Bitunix API client*

## `src/backtesting/engine.py`

### `BacktestEngine(object)`

- `run(config, symbol, start_date, end_date, initial_capital, chart_data, data_timeframe)` → `Dict[str, Any]`  *Run the backtest using phase-based execution.*
- *...7 private methods*
- `__init__(enable_caching, cache_max_size)`  *Initialize BacktestEngine.*

## `src/backtesting/engine_run_refactored.py`

### Module Functions
- `run_refactored(config, symbol, start_date, end_date, initial_capital, chart_data, data_timeframe)` → `Dict[str, Any]`  *Run the backtest using phase-based execution.*

## `src/backtesting/errors.py`

### `BacktestError(Exception)`
*Base exception for backtesting errors.*

- `format_error()` → `str`  *Format error message with details and suggestions.*
- `__init__(message, details, suggestions)`  *Initialize backtestexception.*

### `DataLoadError(BacktestError)`
*Error loading market data.*

- @classmethod `no_data_found(symbol, start_date, end_date, db_path)` → `'DataLoadError'`  *Create error for missing data.*
- @classmethod `timeframe_incompatible(chart_tf, required_tf)` → `'DataLoadError'`  *Create error for incompatible timeframes.*

### `ConfigurationError(BacktestError)`
*Error in strategy configuration.*

- @classmethod `invalid_config(error_details)` → `'ConfigurationError'`  *Create error for invalid configuration.*
- @classmethod `missing_indicator(indicator_id, referenced_by)` → `'ConfigurationError'`  *Create error for missing indicator reference.*
- @classmethod `no_strategy_matched(active_regimes)` → `'ConfigurationError'`  *Create error when no strategy matches current regime.*

### `IndicatorError(BacktestError)`
*Error calculating indicators.*

- @classmethod `calculation_failed(indicator_id, indicator_type, error_msg)` → `'IndicatorError'`  *Create error for indicator calculation failure.*

### `ExecutionError(BacktestError)`
*Error during backtest execution.*

- @classmethod `insufficient_data(required, available)` → `'ExecutionError'`  *Create error for insufficient data.*

### Module Functions
- `format_error_for_ui(error)` → `str`  *Format any exception for UI display.*

## `src/backtesting/phases/setup_phase.py`

### `SetupPhase(object)`
*Setup phase for backtest execution.*

- `execute(config, symbol, start_date, end_date, chart_data, data_timeframe)` → `Dict[str, Any]`  *Execute setup phase.*
- *...5 private methods*
- `__init__(data_loader, indicator_calculator)`  *Initialize setup phase.*

## `src/backtesting/phases/simulation_phase.py`

### `SimulationPhase(object)`
*Simulation phase for backtest execution.*

- `execute(datasets, config, symbol, initial_capital, perf_counters)` → `Dict[str, Any]`  *Execute simulation phase.*
- *...6 private methods*
- `__init__(regime_evaluator, strategy_evaluator)`  *Initialize simulation phase.*

## `src/backtesting/phases/teardown_phase.py`

### `TeardownPhase(object)`
*Teardown phase for backtest execution.*

- `execute(trades, initial_capital, final_equity, regime_history, datasets, combined_df, perf_timings, perf_counters, mem_start, cache_hits, cache_misses, cache_size, cache_max_size, enable_caching, data_timeframe, start_date, end_date, total_candles)` → `Dict[str, Any]`  *Execute teardown phase.*
- `__init__(stats_calculator)`  *Initialize teardown phase.*

## `src/backtesting/schema_types.py`

### `ConditionLeftRight(BaseModel)`


### `Condition(BaseModel)`


### `ConditionGroup(BaseModel)`


### `Metadata(BaseModel)`


### `IndicatorDef(BaseModel)`


### `RegimeDef(BaseModel)`


### `RiskSettings(BaseModel)`


### `StrategyDef(BaseModel)`


### `StrategyOverride(BaseModel)`


### `StrategyRef(BaseModel)`


### `IndicatorOverride(BaseModel)`


### `StrategySet(BaseModel)`


### `RoutingMatch(BaseModel)`


### `RoutingRule(BaseModel)`


### `TradingBotConfig(BaseModel)`


## `src/backtesting/types.py`

### `Trade(object)`
*Trade record for backtest results.*


## `src/brokers/bitunix/api_client.py`

### `BitunixAPIClient(object)`
*Client for Bitunix Futures API*

- `get_klines(symbol, interval, limit, start_time, end_time)` → `List[Dict]`  *Fetch kline/candlestick data from Bitunix API.*
- `get_klines_range(symbol, interval, start_date, end_date)` → `pd.DataFrame`  *Fetch klines for a date range (handles pagination for >200 candles).*
- *...1 private methods*
- `__init__()`

## `src/chart_chat/analyzer.py`

### `ChartAnalyzer(object)`
*AI-powered chart analysis service.*

- async `analyze_chart(context)` → `ChartAnalysisResult`  *Perform comprehensive chart analysis.*
- async `answer_question(question, context, conversation_history)` → `QuickAnswerResult`  *Answer a specific question about the chart.*
- async `answer_question_with_markings(question, context, conversation_history)` → `QuickAnswerResult`  *Answer question with compact format and marking updates.*
- *...6 private methods*
- `__init__(ai_service)`  *Initialize analyzer with AI service.*

## `src/chart_chat/chart_chat_actions_mixin.py`

### `ColorCellDelegate(QStyledItemDelegate)`
*Custom delegate for color cells that doesn't show selection highlight.*

- `paint(painter, option, index)`  *Paint the color cell without selection highlight.*

### `ChartChatActionsMixin(object)`
*ChartChatActionsMixin extracted from ChartChatWidget.*

- *...9 private methods*

## `src/chart_chat/chart_chat_events_mixin.py`

### `ChartChatEventsMixin(object)`
*ChartChatEventsMixin extracted from ChartChatWidget.*

- `on_chart_changed()` → `None`  *Handle chart symbol/timeframe change.*
- `closeEvent(event)` → `None`  *Handle widget close.*
- *...3 private methods*

## `src/chart_chat/chart_chat_export_mixin.py`

### `ChartChatExportMixin(object)`
*ChartChatExportMixin extracted from ChartChatWidget.*

- *...2 private methods*

## `src/chart_chat/chart_chat_history_mixin.py`

### `ChartChatHistoryMixin(object)`
*ChartChatHistoryMixin extracted from ChartChatWidget.*

- *...4 private methods*

## `src/chart_chat/chart_chat_ui_mixin.py`

### `ChartChatUIMixin(object)`
*ChartChatUIMixin extracted from ChartChatWidget.*

- *...19 private methods*

## `src/chart_chat/chart_chat_worker.py`

### `AnalysisWorker(QThread)`
*Background worker for AI analysis calls.*

- `run()` → `None`  *Execute the AI call in background.*
- `__init__(service, action, question)`

## `src/chart_chat/chart_markings.py`

### `MarkingType(str, Enum)`
*Type of chart marking.*


### `ChartMarking(BaseModel)`
*Single chart marking with price level(s).*

- `to_variable_string()` → `str`  *Convert to variable format: [#Label; Value]*
- @classmethod `from_variable_string(var_str, marking_id)` → `ChartMarking | None`  *Parse variable format back to ChartMarking.*

### `ChartMarkingsState(BaseModel)`
*Complete state of all chart markings.*

- `to_prompt_text()` → `str`  *Convert markings to prompt text for AI.*
- `find_marking(marking_id)` → `ChartMarking | None`  *Find marking by ID.*
- `update_or_add(marking)` → `None`  *Update existing marking or add new one.*
- `remove_marking(marking_id)` → `bool`  *Remove marking by ID.*

### `CompactAnalysisResponse(BaseModel)`
*Compact AI response with variables and brief reasoning.*

- @classmethod `from_ai_text(text)` → `CompactAnalysisResponse`  *Parse AI response text into structured format.*

## `src/chart_chat/chat_service.py`

### `ChartChatService(object)`
*Main service for chart analysis chatbot.*

- @property `current_symbol()` → `str`  *Get current symbol.*
- @property `current_timeframe()` → `str`  *Get current timeframe.*
- @property `model_name()` → `str`  *Return the underlying AI model name, if available.*
- @property `conversation_history()` → `list[ChatMessage]`  *Get current conversation history.*
- `get_chart_context(lookback_bars)` → `ChartContext`  *Get current chart context.*
- `set_lookback_bars(bars)` → `None`  *Set the number of bars for analysis.*
- async `analyze_chart()` → `ChartAnalysisResult`  *Perform comprehensive chart analysis.*
- async `ask_question(question)` → `QuickAnswerResult`  *Ask a question about the current chart.*
- `clear_history()` → `bool`  *Clear conversation history for current chart.*
- `get_quick_actions()` → `list[dict[str, str]]`  *Get list of quick action buttons for the UI.*
- `get_session_info()` → `dict[str, Any]`  *Get information about the current chat session.*
- `on_chart_changed()` → `None`  *Handle chart symbol/timeframe change.*
- `shutdown()` → `None`  *Clean up resources and save state.*
- *...3 private methods*
- `__init__(chart_widget, ai_service, history_store)`  *Initialize the chat service.*

## `src/chart_chat/history_store.py`

### `HistoryStore(object)`
*Manages chat history persistence per chart window.*

- `save_history(symbol, timeframe, messages)` → `None`  *Save chat history for a chart window.*
- `load_history(symbol, timeframe)` → `list[ChatMessage]`  *Load chat history for a chart window.*
- `clear_history(symbol, timeframe)` → `bool`  *Clear chat history for a chart window.*
- `list_charts_with_history()` → `list[tuple[str, str]]`  *List all chart windows that have saved history.*
- `get_history_info(symbol, timeframe)` → `dict[str, Any] | None`  *Get metadata about stored history without loading all messages.*
- *...4 private methods*
- `__init__(storage_dir, max_messages)`  *Initialize history store.*

## `src/chart_chat/markings_manager.py`

### `MarkingsManager(object)`
*Manages chart markings for AI analysis.*

- `get_current_markings()` → `ChartMarkingsState`  *Get current state of all chart markings.*
- `apply_ai_response(response)` → `None`  *Apply AI response updates to chart markings.*
- `add_manual_marking(marking_type, price, price_top, price_bottom, label, reasoning)` → `ChartMarking`  *Manually add a marking (for user-created markings).*
- *...14 private methods*
- `__init__(chart_widget)`  *Initialize markings manager.*

## `src/chart_chat/mixin.py`

### `ChartChatMixin(TradingMixinBase)`
*Mixin that adds chart chat functionality to a window.*

- `setup_chart_chat(chart_widget, ai_service)` → `bool`  *Set up the chart chat functionality.*
- `toggle_chat_widget()` → `None`  *Toggle visibility of the chat widget.*
- `show_chat_widget()` → `None`  *Show the chat widget.*
- `hide_chat_widget()` → `None`  *Hide the chat widget.*
- @property `chat_widget()` → `Any`  *Get the chat widget.*
- @property `chat_service()` → `Any`  *Get the chat service.*
- `request_chart_analysis()` → `None`  *Request a full chart analysis.*
- `cleanup_chart_chat()` → `None`  *Clean up chat resources.*
- *...6 private methods*

## `src/chart_chat/models.py`

### `MessageRole(Enum)`
*Role of a chat message sender.*


### `ChatMessage(BaseModel)`
*Single chat message in the conversation.*


### `TrendDirection(Enum)`
*Direction of the current trend.*


### `SignalStrength(Enum)`
*Strength of a signal or level.*


### `SupportResistanceLevel(BaseModel)`
*Support or Resistance price level.*


### `EntryExitRecommendation(BaseModel)`
*Entry or Exit recommendation from AI analysis.*


### `RiskAssessment(BaseModel)`
*Risk assessment for a potential trade.*


### `PatternInfo(BaseModel)`
*Identified chart pattern.*


### `ChartAnalysisResult(BaseModel)`
*Comprehensive chart analysis result from AI.*

- `to_markdown()` → `str`  *Convert analysis result to readable Markdown (refactored).*
- *...10 private methods*

### `QuickAnswerResult(BaseModel)`
*Quick answer for conversational queries.*


## `src/chart_chat/prompts.py`

### Module Functions
- `build_compact_question_prompt(symbol, timeframe, current_price, indicators, markings, question, price_change_pct, volatility_atr, volume_trend, recent_high, recent_low)` → `str`  *Build compact question prompt with markings.*
- `_get_override(key, default)` → `str`  *Return QSettings override or default if empty.*
- `get_chart_analysis_system_prompt()` → `str`
- `get_conversational_system_prompt()` → `str`
- `get_compact_system_prompt()` → `str`
- `get_chart_analysis_user_template()` → `str`
- `get_conversational_user_template()` → `str`
- `get_compact_user_template()` → `str`
- `build_analysis_prompt(symbol, timeframe, current_price, ohlcv_summary, indicators, price_change_pct, volatility_atr, volume_trend, recent_high, recent_low, lookback)` → `str`  *Build the user prompt for full chart analysis.*
- `build_conversation_prompt(symbol, timeframe, current_price, indicators, history, question)` → `str`  *Build the user prompt for conversational Q&A.*
- `format_conversation_history(messages, max_messages)` → `str`  *Format conversation history for inclusion in prompt.*

## `src/chart_chat/prompts_editor_dialog.py`

### `PromptsEditorDialog(QDialog)`
*Popup dialog to edit all chatbot prompts (system + user templates).*

- *...7 private methods*
- `__init__(parent)`

## `src/chart_chat/widget.py`

### `ChartChatWidget(ChartChatUIMixin, ChartChatHistoryMixin, ChartChatActionsMixin, ChartChatExportMixin, ChartChatEventsMixin, QDockWidget)`
*Dockable chat widget for chart analysis.*

- `__init__(service, parent)`  *Initialize the chat widget.*

## `src/chart_marking/base_manager.py`

### `BaseChartElementManager(ABC, Generic[T])`
*Base class for all chart element managers.*

- `remove(item_id)` → `bool`  *Remove an item by ID.*
- `clear()` → `None`  *Remove all items.*
- `set_locked(item_id, is_locked)` → `bool`  *Set item lock status.*
- `toggle_locked(item_id)` → `bool | None`  *Toggle item lock status.*
- `get(item_id)` → `Optional[T]`  *Get an item by ID.*
- `get_all()` → `list[T]`  *Get all items.*
- `to_state()` → `list[dict[str, Any]]`  *Export state for persistence.*
- `restore_state(state)` → `None`  *Restore state from persistence.*
- *...4 private methods*
- `__init__(on_update)`  *Initialize the manager.*
- `__len__()` → `int`  *Return number of items.*
- `__contains__(item_id)` → `bool`  *Check if item exists.*

## `src/chart_marking/constants.py`

### `Colors(object)`
*Color constants for chart markings.*


### `LineStyles(object)`
*Line style constants.*


### `MarkerSizes(object)`
*Marker size constants.*


### `ZoneDefaults(object)`
*Default values for zones.*


### `LayoutDefaults(object)`
*Default values for multi-chart layouts.*


## `src/chart_marking/lines/stop_loss_line.py`

### `StopLossLineManager(BaseChartElementManager[StopLossLine])`
*Manages stop-loss and price lines on the chart.*

- `add(line_id, price, entry_price, direction, color, line_style, label, show_risk, risk_percent)` → `str`  *Add a stop-loss line.*
- `add_stop_loss(line_id, price, entry_price, is_long, label)` → `str`  *Add a stop-loss line with risk display (convenience method).*
- `add_take_profit(line_id, price, entry_price, is_long, label)` → `str`  *Add a take-profit line (convenience method).*
- `add_entry_line(line_id, price, is_long, label)` → `str`  *Add an entry price line (convenience method).*
- `add_trailing_stop(line_id, price, entry_price, is_long, label)` → `str`  *Add a trailing stop line (convenience method).*
- `update(line_id, price, entry_price)` → `bool`  *Update a line's price levels.*
- `update_trailing_stop(line_id, new_price)` → `bool`  *Update a trailing stop price (convenience method).*
- `get_chart_lines()` → `list[dict[str, Any]]`  *Get all lines in chart format for JavaScript.*
- *...3 private methods*

## `src/chart_marking/markers/entry_markers.py`

### `EntryMarkerManager(BaseChartElementManager[EntryMarker])`
*Manages entry markers (Long/Short arrows) on the chart.*

- `add(marker_id, timestamp, price, direction, text, tooltip, score)` → `str`  *Add an entry marker.*
- `add_long(timestamp, price, text, marker_id, score)` → `str`  *Add a long entry marker (convenience method).*
- `add_short(timestamp, price, text, marker_id, score)` → `str`  *Add a short entry marker (convenience method).*
- `get_chart_markers()` → `list[dict[str, Any]]`  *Get all markers in Lightweight Charts format.*
- *...3 private methods*

## `src/chart_marking/markers/structure_markers.py`

### `StructureMarkerManager(BaseChartElementManager[StructureBreakMarker])`
*Manages structure break markers (BoS/CHoCH) on the chart.*

- `add(marker_id, timestamp, price, break_type, direction, text)` → `str`  *Add a structure break marker.*
- `add_bos(timestamp, price, is_bullish, marker_id, text)` → `str`  *Add a Break of Structure marker (convenience method).*
- `add_choch(timestamp, price, is_bullish, marker_id, text)` → `str`  *Add a Change of Character marker (convenience method).*
- `add_msb(timestamp, price, is_bullish, marker_id, text)` → `str`  *Add a Market Structure Break marker (convenience method).*
- `clear_by_type(break_type)` → `int`  *Remove all markers of a specific type.*
- `get_by_type(break_type)` → `list[StructureBreakMarker]`  *Get all markers of a specific type.*
- `get_chart_markers()` → `list[dict[str, Any]]`  *Get all markers in Lightweight Charts format.*
- *...4 private methods*

## `src/chart_marking/mixin/chart_marking_base.py`

### `ChartMarkingBase(object)`
*Base class for all chart marking mixin helpers.*

- `__init__(parent)`  *Initialize base mixin helper.*

## `src/chart_marking/mixin/chart_marking_entry_methods.py`

### `ChartMarkingEntryMethods(ChartMarkingBase)`
*Helper für ChartMarkingMixin entry marker methods.*

- `add_entry_marker(marker_id, timestamp, price, direction, text, tooltip, score)` → `str`  *Add an entry marker (arrow).*
- `add_long_entry(timestamp, price, text, marker_id, score)` → `str`  *Add a long entry marker (convenience method).*
- `add_short_entry(timestamp, price, text, marker_id, score)` → `str`  *Add a short entry marker (convenience method).*
- `remove_entry_marker(marker_id)` → `bool`  *Remove an entry marker.*
- `clear_entry_markers()` → `None`  *Remove all entry markers.*

## `src/chart_marking/mixin/chart_marking_internal.py`

### `ChartMarkingInternal(ChartMarkingBase)`
*Helper für ChartMarkingMixin internal state & JS communication.*

- `get_marking_state()` → `dict[str, Any]`  *Get complete marking state for persistence.*
- `restore_marking_state(state)` → `None`  *Restore marking state from persistence.*
- `clear_all_markings()` → `None`  *Remove all markings from the chart.*
- `on_markers_changed()` → `None`  *Called when entry or structure markers change.*
- `on_zones_changed()` → `None`  *Called when zones change.*
- `on_lines_changed()` → `None`  *Called when stop-loss lines change.*
- @property `entry_marker_count()` → `int`  *Number of entry markers.*
- @property `structure_marker_count()` → `int`  *Number of structure break markers.*
- @property `zone_count()` → `int`  *Number of zones.*
- @property `stop_loss_line_count()` → `int`  *Number of stop-loss lines.*
- @property `total_marking_count()` → `int`  *Total number of all markings.*
- *...4 private methods*

## `src/chart_marking/mixin/chart_marking_line_methods.py`

### `ChartMarkingLineMethods(ChartMarkingBase)`
*Helper für ChartMarkingMixin stop-loss line methods.*

- `add_line(line_id, price, color, label, line_style, show_risk)` → `str`  *Add a generic horizontal line.*
- `add_stop_loss_line(line_id, price, entry_price, is_long, label, show_risk)` → `str`  *Add a stop-loss line with optional risk display.*
- `add_take_profit_line(line_id, price, entry_price, is_long, label)` → `str`  *Add a take-profit line (convenience method).*
- `add_entry_line(line_id, price, is_long, label)` → `str`  *Add an entry price line (convenience method).*
- `add_trailing_stop_line(line_id, price, entry_price, is_long, label)` → `str`  *Add a trailing stop line (convenience method).*
- `update_stop_loss_line(line_id, price, entry_price)` → `bool`  *Update a stop-loss line's price levels.*
- `update_trailing_stop(line_id, new_price)` → `bool`  *Update a trailing stop price.*
- `remove_stop_loss_line(line_id)` → `bool`  *Remove a stop-loss line.*
- `clear_stop_loss_lines()` → `None`  *Remove all stop-loss lines.*

## `src/chart_marking/mixin/chart_marking_mixin.py`

### `ChartMarkingMixin(object)`
*Mixin that adds chart marking capabilities to EmbeddedTradingViewChart (REFACTORED).*

- `add_entry_marker(marker_id, timestamp, price, direction, text, tooltip, score)` → `str`  *Add an entry marker (arrow).*
- `add_long_entry(timestamp, price, text, marker_id, score)` → `str`  *Add a long entry marker.*
- `add_short_entry(timestamp, price, text, marker_id, score)` → `str`  *Add a short entry marker.*
- `remove_entry_marker(marker_id)` → `bool`  *Remove an entry marker.*
- `clear_entry_markers()` → `None`  *Remove all entry markers.*
- `add_structure_break(marker_id, timestamp, price, break_type, direction, text)` → `str`  *Add a structure break marker.*
- `add_bos(timestamp, price, is_bullish, marker_id, text)` → `str`  *Add a Break of Structure marker.*
- `add_choch(timestamp, price, is_bullish, marker_id, text)` → `str`  *Add a Change of Character marker.*
- `add_msb(timestamp, price, is_bullish, marker_id, text)` → `str`  *Add a Market Structure Break marker.*
- `remove_structure_break(marker_id)` → `bool`  *Remove a structure break marker.*
- `clear_structure_breaks()` → `None`  *Remove all structure break markers.*
- `clear_structure_breaks_by_type(break_type)` → `int`  *Remove all structure breaks of a specific type.*
- `add_zone(zone_id, zone_type, start_time, end_time, top_price, bottom_price, opacity, label, color)` → `str`  *Add a support/resistance zone.*
- `add_support_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a support zone.*
- `add_resistance_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a resistance zone.*
- `add_demand_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a demand zone.*
- `add_supply_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a supply zone.*
- `update_zone(zone_id, start_time, end_time, top_price, bottom_price)` → `bool`  *Update a zone's dimensions.*
- `extend_zone(zone_id, new_end_time)` → `bool`  *Extend a zone's end time.*
- `remove_zone(zone_id)` → `bool`  *Remove a zone.*
- `clear_zones()` → `None`  *Remove all zones.*
- `clear_zones_by_type(zone_type)` → `int`  *Remove all zones of a specific type.*
- `add_line(line_id, price, color, label, line_style, show_risk)` → `str`  *Add a generic horizontal line.*
- `add_stop_loss_line(line_id, price, entry_price, is_long, label, show_risk)` → `str`  *Add a stop-loss line.*
- `add_take_profit_line(line_id, price, entry_price, is_long, label)` → `str`  *Add a take-profit line.*
- `add_entry_line(line_id, price, is_long, label)` → `str`  *Add an entry price line.*
- `add_trailing_stop_line(line_id, price, entry_price, is_long, label)` → `str`  *Add a trailing stop line.*
- `update_stop_loss_line(line_id, price, entry_price)` → `bool`  *Update a stop-loss line's price levels.*
- `update_trailing_stop(line_id, new_price)` → `bool`  *Update a trailing stop price.*
- `remove_stop_loss_line(line_id)` → `bool`  *Remove a stop-loss line.*
- `clear_stop_loss_lines()` → `None`  *Remove all stop-loss lines.*
- `get_marking_state()` → `dict[str, Any]`  *Get complete marking state for persistence.*
- `restore_marking_state(state)` → `None`  *Restore marking state from persistence.*
- `clear_all_markings()` → `None`  *Remove all markings from the chart.*
- @property `entry_marker_count()` → `int`  *Number of entry markers.*
- @property `structure_marker_count()` → `int`  *Number of structure break markers.*
- @property `zone_count()` → `int`  *Number of zones.*
- @property `stop_loss_line_count()` → `int`  *Number of stop-loss lines.*
- @property `total_marking_count()` → `int`  *Total number of all markings.*
- *...4 private methods*

## `src/chart_marking/mixin/chart_marking_structure_methods.py`

### `ChartMarkingStructureMethods(ChartMarkingBase)`
*Helper für ChartMarkingMixin structure break marker methods.*

- `add_structure_break(marker_id, timestamp, price, break_type, direction, text)` → `str`  *Add a structure break marker.*
- `add_bos(timestamp, price, is_bullish, marker_id, text)` → `str`  *Add a Break of Structure marker (convenience method).*
- `add_choch(timestamp, price, is_bullish, marker_id, text)` → `str`  *Add a Change of Character marker (convenience method).*
- `add_msb(timestamp, price, is_bullish, marker_id, text)` → `str`  *Add a Market Structure Break marker (convenience method).*
- `remove_structure_break(marker_id)` → `bool`  *Remove a structure break marker.*
- `clear_structure_breaks()` → `None`  *Remove all structure break markers.*
- `clear_structure_breaks_by_type(break_type)` → `int`  *Remove all structure breaks of a specific type.*

## `src/chart_marking/mixin/chart_marking_zone_methods.py`

### `ChartMarkingZoneMethods(ChartMarkingBase)`
*Helper für ChartMarkingMixin zone methods.*

- `add_zone(zone_id, zone_type, start_time, end_time, top_price, bottom_price, opacity, label, color)` → `str`  *Add a support/resistance zone.*
- `add_support_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a support zone (convenience method).*
- `add_resistance_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a resistance zone (convenience method).*
- `add_demand_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a demand zone (convenience method).*
- `add_supply_zone(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a supply zone (convenience method).*
- `update_zone(zone_id, start_time, end_time, top_price, bottom_price)` → `bool`  *Update a zone's dimensions.*
- `extend_zone(zone_id, new_end_time)` → `bool`  *Extend a zone's end time.*
- `remove_zone(zone_id)` → `bool`  *Remove a zone.*
- `clear_zones()` → `None`  *Remove all zones.*
- `clear_zones_by_type(zone_type)` → `int`  *Remove all zones of a specific type.*

## `src/chart_marking/models.py`

### `MarkerShape(str, Enum)`
*Available marker shapes in Lightweight Charts.*


### `MarkerPosition(str, Enum)`
*Marker position relative to bar.*


### `Direction(str, Enum)`
*Trade/signal direction.*


### `ZoneType(str, Enum)`
*Support/Resistance zone type.*


### `StructureBreakType(str, Enum)`
*Market structure break types.*


### `LineStyle(str, Enum)`
*Line style options.*


### `EntryMarker(object)`
*Entry arrow marker for Long/Short signals.*

- `to_chart_marker()` → `dict[str, Any]`  *Convert to Lightweight Charts marker format.*
- `to_dict()` → `dict[str, Any]`  *Convert to dictionary for persistence.*
- @classmethod `from_dict(data)` → `'EntryMarker'`  *Create from dictionary.*

### `Zone(object)`
*Support/Resistance zone rectangle.*

- @property `fill_color()` → `str`  *Get fill color with opacity.*
- @property `border_color()` → `str`  *Get solid border color.*
- `to_dict()` → `dict[str, Any]`  *Convert to dictionary for persistence.*
- @classmethod `from_dict(data)` → `'Zone'`  *Create from dictionary.*

### `StructureBreakMarker(object)`
*BoS/CHoCH market structure marker.*

- `to_chart_marker()` → `dict[str, Any]`  *Convert to Lightweight Charts marker format.*
- `to_dict()` → `dict[str, Any]`  *Convert to dictionary for persistence.*
- @classmethod `from_dict(data)` → `'StructureBreakMarker'`  *Create from dictionary.*

### `StopLossLine(object)`
*Stop-loss line with label and optional risk display.*

- @property `calculated_risk_pct()` → `Optional[float]`  *Calculate risk percentage from entry to SL.*
- @property `display_label()` → `str`  *Generate label with optional risk percentage.*
- `to_dict()` → `dict[str, Any]`  *Convert to dictionary for persistence.*
- @classmethod `from_dict(data)` → `'StopLossLine'`  *Create from dictionary.*

### `ChartConfig(object)`
*Configuration for a single chart in a layout.*

- `to_dict()` → `dict[str, Any]`  *Convert to dictionary.*
- @classmethod `from_dict(data)` → `'ChartConfig'`  *Create from dictionary.*

### `MultiChartLayout(object)`
*Layout preset for multi-chart/multi-monitor configuration.*

- `to_dict()` → `dict[str, Any]`  *Convert to dictionary for persistence.*
- @classmethod `from_dict(data)` → `'MultiChartLayout'`  *Create from dictionary.*

### Module Functions
- `_normalize_timestamp(ts)` → `int`  *Convert timestamp to Unix seconds.*

## `src/chart_marking/multi_chart/crosshair_sync.py`

### `CrosshairSyncManager(object)`
*Manages crosshair synchronization across multiple charts.*

- @property `enabled()` → `bool`  *Check if sync is enabled.*
- `set_enabled(enabled)` → `None`  *Enable or disable crosshair sync.*
- `register_window(window_id, window, on_crosshair_update)` → `None`  *Register a chart window for crosshair sync.*
- `unregister_window(window_id)` → `None`  *Unregister a window from crosshair sync.*
- `on_crosshair_move(source_window_id, timestamp, price)` → `None`  *Handle crosshair movement from a source window.*
- `broadcast_position(timestamp, price)` → `None`  *Broadcast a crosshair position to all windows.*
- `get_registered_count()` → `int`  *Get the number of registered windows.*
- `clear()` → `None`  *Clear all registered windows.*
- `__init__(enabled)` → `None`  *Initialize the sync manager.*

### Module Functions
- `get_crosshair_sync_javascript()` → `str`  *Get the JavaScript code for crosshair sync.*

## `src/chart_marking/multi_chart/layout_manager.py`

### `LayoutManager(object)`
*Manages multi-chart layout presets.*

- `save_layout(name, charts, sync_crosshair, layout_id)` → `MultiChartLayout`  *Save a layout preset.*
- `load_layout(layout_id)` → `Optional[MultiChartLayout]`  *Load a layout by ID.*
- `delete_layout(layout_id)` → `bool`  *Delete a layout.*
- `list_layouts()` → `list[MultiChartLayout]`  *List all available layouts.*
- `get_layout_names()` → `dict[str, str]`  *Get a mapping of layout IDs to names.*
- `capture_current_layout(windows, name)` → `MultiChartLayout`  *Capture the current window arrangement as a layout.*
- `get_available_monitors()` → `list[dict[str, Any]]`  *Get information about available monitors.*
- `create_default_layouts()` → `None`  *Create some default layout presets if none exist.*
- *...1 private methods*
- `__init__(layouts_dir, on_layout_changed)` → `None`  *Initialize the layout manager.*

## `src/chart_marking/multi_chart/multi_monitor_manager.py`

### `MultiMonitorChartManager(object)`
*Manages multiple chart windows across monitors.*

- `set_chart_factory(factory)` → `None`  *Set the chart factory function.*
- `open_chart(symbol, timeframe, monitor, position, window_id)` → `Optional['QWidget']`  *Open a new chart window.*
- `close_chart(window_id)` → `bool`  *Close a chart window.*
- `close_all()` → `None`  *Close all chart windows.*
- `apply_layout(layout)` → `bool`  *Apply a layout preset.*
- `apply_layout_by_id(layout_id)` → `bool`  *Apply a layout by its ID.*
- `save_current_layout(name)` → `Optional[MultiChartLayout]`  *Save the current window arrangement as a layout.*
- `tile_on_monitor(monitor, symbols, timeframe)` → `None`  *Tile multiple charts on a monitor.*
- `get_window_count()` → `int`  *Get the number of open windows.*
- `get_open_symbols()` → `list[str]`  *Get list of symbols in open windows.*
- *...3 private methods*
- `__init__(chart_factory, on_window_opened, on_window_closed)` → `None`  *Initialize the multi-monitor chart manager.*

## `src/chart_marking/zones/support_resistance.py`

### `ZoneManager(BaseChartElementManager[Zone])`
*Manages support/resistance zones on the chart.*

- `add(zone_id, zone_type, start_time, end_time, top_price, bottom_price, opacity, label, color)` → `str`  *Add a zone.*
- `add_support(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a support zone (convenience method).*
- `add_resistance(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a resistance zone (convenience method).*
- `add_demand(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a demand zone (convenience method).*
- `add_supply(start_time, end_time, top_price, bottom_price, label, zone_id, opacity)` → `str`  *Add a supply zone (convenience method).*
- `update(zone_id, start_time, end_time, top_price, bottom_price)` → `bool`  *Update a zone's dimensions.*
- `extend_zone(zone_id, new_end_time)` → `bool`  *Extend a zone's end time.*
- `set_active(zone_id, is_active)` → `bool`  *Set zone active status.*
- `clear_by_type(zone_type)` → `int`  *Remove all zones of a specific type.*
- `get_active()` → `list[Zone]`  *Get all active zones.*
- `get_by_type(zone_type)` → `list[Zone]`  *Get all zones of a specific type.*
- `get_zones_at_price(price)` → `list[Zone]`  *Get all zones that contain a given price.*
- `get_chart_zones()` → `list[dict[str, Any]]`  *Get all zones in chart format for JavaScript.*
- *...5 private methods*

## `src/chart_marking/zones/zone_primitive_js.py`

### Module Functions
- `get_zone_javascript()` → `str`  *Get complete JavaScript code for zone functionality.*

## `src/common/event_bus.py`

### `EventType(Enum)`
*Enumeration of all event types in the system.*


### `Event(object)`
*Base event data structure.*


### `OrderEvent(Event)`
*Order-specific event with chart-relevant information.*

- `__post_init__()`  *Ensure data dict contains chart-relevant info.*

### `ExecutionEvent(Event)`
*Execution event for chart markers (entry/exit points).*

- `__post_init__()`  *Ensure data dict contains chart-relevant info.*

### `EventBus(object)`
*Centralized event bus for the trading application.*

- `get_signal(event_type)`  *Get or create a signal for the given event type.*
- `emit(event)` → `None`  *Emit an event to all registered listeners.*
- `subscribe(event_type, handler, filter)` → `None`  *Subscribe to an event type with optional filtering.*
- `unsubscribe(event_type, handler)` → `None`  *Unsubscribe from an event type.*
- `get_history(event_type, limit)` → `list[Event]`  *Get event history, optionally filtered by type.*
- `clear_history()` → `None`  *Clear the event history.*
- `__init__()`  *Initialize the event bus with namespaced signals.*

## `src/common/logging_setup.py`

### `ConsoleLevelFilter(logging.Filter)`
*Filter console output by level regardless of logger configuration.*

- `set_level(level)` → `None`
- `filter(record)` → `bool`
- `__init__(level)` → `None`

### `AITelemetryFilter(logging.Filter)`
*Custom filter to add AI telemetry data to log records.*

- `filter(record)`  *Add AI-specific fields to the log record if present.*

### `TradingJsonFormatter(JsonFormatter)`
*Custom JSON formatter for trading application logs.*

- `add_fields(log_record, record, message_dict)`  *Add custom fields to the JSON log output.*

### Module Functions
- `_ensure_console_filter(handler, level)` → `None`  *Attach/update console level filter on a handler.*
- `apply_console_log_level(level_str)` → `int`  *Apply console log level to root and console handlers.*
- `configure_logging(level, log_dir, enable_console, enable_file, enable_json, max_bytes, backup_count)` → `None`  *Configure comprehensive logging for the trading application.*
- `configure_module_loggers()`  *Configure logging levels for specific modules.*
- `log_order_action(action, order_id, symbol, details, logger_name)` → `None`  *Log order-related actions to the audit log.*
- `log_security_action(action, user_id, session_id, ip_address, details, success)` → `None`  *Log security-relevant actions.*
- `get_audit_logger()` → `logging.Logger`  *Get the audit logger instance.*
- `get_security_audit_logger()` → `logging.Logger`  *Get the security audit logger instance.*
- `log_ai_request(model, tokens, cost, latency, prompt_version, request_type, details)` → `None`  *Log AI API requests for telemetry and cost tracking.*
- `get_logger(name)` → `logging.Logger`  *Get a logger instance with the given name.*

## `src/common/performance.py`

### `PerformanceMonitor(object)`
*Monitor performance metrics for trading operations.*

- `record_latency(operation, latency_ms)` → `None`  *Record latency for an operation.*
- `increment_counter(counter)` → `None`  *Increment a counter.*
- `get_stats(operation)` → `dict[str, float]`  *Get statistics for an operation.*
- `get_all_stats()` → `dict[str, dict[str, float]]`  *Get all performance statistics.*
- `reset()` → `None`  *Reset all metrics.*
- `measure(operation)`  *Context manager to measure operation duration.*
- `report()` → `str`  *Generate performance report.*
- `__init__()`  *Initialize performance monitor.*

### `PerformanceTimer(object)`
*Simple timer for manual performance tracking.*

- `start()` → `None`  *Start the timer.*
- `stop()` → `float`  *Stop the timer and return elapsed time.*
- `__init__(name, auto_log)`  *Initialize timer.*
- `__enter__()`  *Enter context manager.*
- `__exit__(_exc_type, _exc_val, _exc_tb)`  *Exit context manager.*

### Module Functions
- `monitor_performance(operation)`  *Decorator to monitor function performance.*
- `log_performance(operation, threshold_ms)` → `Callable`  *Decorator to log slow operations.*

## `src/common/security.py`

### Module Functions
- `audit_action(action, context, details, success)`  *Backward compatibility wrapper for audit logging.*

## `src/common/security_core.py`

### `SecurityLevel(Enum)`
*Security levels for operations.*


### `SecurityAction(Enum)`
*Security-relevant actions.*


### `SecurityContext(object)`
*Security context for operations.*

- `__post_init__()`

### `RateLimiter(object)`
*Rate limiting implementation with sliding window.*

- `is_allowed(key)` → `bool`  *Check if request is allowed.*
- `set_limit(name, max_requests, time_window)` → `None`  *Set a named rate limit configuration.*
- `check_limit(name, identifier)` → `bool`  *Check a named rate limit for a specific identifier.*
- `get_remaining(key)` → `int`  *Get remaining requests in current window.*
- *...1 private methods*
- `__init__(max_requests, window_seconds)`  *Initialize rate limiter.*

### Module Functions
- `hash_password(password, salt)` → `tuple[str, str]`  *Hash password with salt.*
- `verify_password(password, stored_hash, salt)` → `bool`  *Verify password against stored hash.*
- `generate_api_key()` → `str`  *Generate a secure API key.*
- `validate_api_key(api_key)` → `bool`  *Validate API key format.*
- `rate_limit(key, max_requests, window_seconds)` → `Callable`  *Rate limiting decorator.*
- `is_strong_password(password)` → `bool`  *Check if password meets strength requirements.*
- `sanitize_input(value, max_length)` → `str`  *Sanitize user input.*

## `src/common/security_manager.py`

### `EncryptionManager(object)`
*Manages encryption and decryption of sensitive data.*

- `encrypt(data)` → `str`  *Encrypt sensitive data.*
- `decrypt(encrypted_data)` → `str`  *Decrypt sensitive data.*
- `encrypt_dict(data)` → `str`  *Encrypt dictionary data.*
- `decrypt_dict(encrypted_data)` → `dict[str, Any]`  *Decrypt dictionary data.*
- `rotate_key(new_password)` → `bool`  *Rotate encryption key.*
- *...1 private methods*
- `__init__(master_password)`  *Initialize encryption manager.*

### `CredentialManager(object)`
*Manages secure storage of credentials.*

- `store_credential(key, value, encrypt)` → `bool`  *Store credential securely.*
- `retrieve_credential(key, decrypt)` → `str | None`  *Retrieve credential.*
- `delete_credential(key)` → `bool`  *Delete credential.*
- *...3 private methods*
- `__init__(encryption_manager)`  *Initialize credential manager.*

### `SessionManager(object)`
*Manages user sessions.*

- `create_session(user_id, ip_address)` → `str`  *Create new session.*
- `validate_session(session_id)` → `SecurityContext | None`  *Validate session.*
- `terminate_session(session_id)`  *Terminate session.*
- `__init__()`  *Initialize session manager.*

### Module Functions
- `require_auth(security_level)`  *Decorator requiring authentication.*

## `src/config/config_types.py`

### `TradingEnvironment(str, Enum)`
*Trading environment modes.*


### `TradingMode(str, Enum)`
*Trading execution modes.*


### `BrokerType(str, Enum)`
*Supported broker types.*


### `BrokerConfig(BaseModel)`
*Broker connection configuration.*


### `DatabaseConfig(BaseModel)`
*Database configuration.*


### `MarketDataProviderConfig(BaseModel)`
*Market data provider configuration and toggles.*


### `AIConfig(BaseModel)`
*OpenAI API configuration.*


### `TradingConfig(BaseModel)`
*Trading parameters and risk management.*


### `BacktestConfig(BaseModel)`
*Backtesting configuration.*


### `AlertConfig(BaseModel)`
*Alert and notification settings.*


### `UIConfig(BaseModel)`
*User interface configuration.*


### `MonitoringConfig(BaseModel)`
*Performance monitoring and metrics.*


### `ExecutionConfig(BaseModel)`
*Order execution settings.*


## `src/config/loader.py`

### `AppSettings(BaseSettings)`
*Application-wide settings from environment variables.*


### `ConfigManager(object)`
*Manages application configuration and profiles.*

- `load_profile(profile_name)` → `ProfileConfig`  *Load a configuration profile.*
- `save_profile(profile)` → `None`  *Save the current profile to disk.*
- `get_credential(key, service)` → `str | None`  *Retrieve a credential from environment variables, .env file or Windows Credentia...*
- `set_credential(key, value, service)` → `None`  *Store a credential in Windows Credential Manager.*
- `list_profiles()` → `list[str]`  *List available configuration profiles.*
- `export_config(path)` → `None`  *Export current configuration (without secrets).*
- `save_watchlist()` → `None`  *Save watchlist to persistent storage.*
- `load_watchlist()` → `list[str]`  *Load watchlist from persistent storage.*
- `get_setting(key, default)`  *Return a setting from profile.market_data or AppSettings (compat layer).*
- @property `profile()` → `ProfileConfig`  *Get the current profile configuration.*
- *...3 private methods*
- `__init__(config_dir)`  *Initialize the configuration manager.*

## `src/config/profile_config.py`

### `ProfileConfig(BaseModel)`
*Complete trading profile configuration.*

- @classmethod `validate_environment(v, info)` → `TradingEnvironment`  *Ensure production environment has proper safeguards.*
- @classmethod `validate_trading_mode_field(v)` → `TradingMode`  *Convert string to enum if needed.*
- `validate_trading_mode_config()` → `ProfileConfig`  *Ensure trading mode has appropriate safety settings.*
- `is_safe_for_mode(mode)` → `tuple[bool, list[str]]`  *Check if current configuration is safe for specified mode.*
- `switch_to_mode(mode, validate)` → `None`  *Switch to specified trading mode with safety checks.*
- @staticmethod `create_backtest_profile(name, initial_capital)` → `ProfileConfig`  *Create a profile optimized for backtesting.*
- @staticmethod `create_paper_profile(name, broker_type)` → `ProfileConfig`  *Create a profile for paper trading.*
- @staticmethod `create_live_profile(name, broker_type)` → `ProfileConfig`  *Create a profile for live trading with maximum safety.*

## `src/core/ai_analysis/engine.py`

### `AIAnalysisEngine(object)`
*Orchestrator for the AI Analysis Workflow.*

- `apply_prompt_overrides(system_prompt, tasks_prompt)` → `None`  *Inject UI-provided prompt overrides into the composer.*
- async `run_analysis(symbol, timeframe, df, model, strategy_configs)` → `Optional[AIAnalysisOutput]`  *Main entry point.*
- *...1 private methods*
- `__init__(api_key)`

## `src/core/ai_analysis/features.py`

### `FeatureEngineer(object)`
*Transforms raw OHLCV data into semantic features for the AI.*

- `extract_technicals(df)` → `TechnicalFeatures`  *Extracts single-point technical metrics from the latest candle.*
- `extract_structure(df, lookback)` → `MarketStructure`  *Identifies key pivot points (Highs/Lows) in the lookback period.*
- `summarize_candles(df, count)` → `List[Dict[str, Any]]`  *Returns a simplified list of the last N candles for the prompt.*
- *...2 private methods*
- `__init__()`

## `src/core/ai_analysis/openai_client.py`

### `OpenAIClient(object)`
*Wrapper around OpenAI API to send prompts and receive JSON.*

- async `analyze(system_prompt, user_prompt, model)` → `Optional[AIAnalysisOutput]`  *Sends the request to the LLM and parses the response into the Pydantic model.*
- *...2 private methods*
- `__init__(api_key, model)`

## `src/core/ai_analysis/prompt.py`

### `PromptComposer(object)`
*Constructs the prompt for the LLM.*

- `set_overrides(system_prompt, tasks_prompt)` → `None`  *Update prompt overrides (empty/None resets to defaults).*
- `compose_system_prompt()` → `str`  *Return the system prompt (override if provided).*
- `compose_user_prompt(input_data)` → `str`  *Serializes the input data into the user prompt, inserting the tasks block*
- `__init__(system_prompt_override, tasks_prompt_override)`

## `src/core/ai_analysis/regime.py`

### `RegimeDetector(object)`
*Determines the market regime (Trend, Range, Volatility) using deterministic logic.*

- `detect_regime(df)` → `MarketRegime`  *Calculates indicators and applies regime matrix logic (refactored).*
- *...7 private methods*
- `__init__()`

## `src/core/ai_analysis/types.py`

### `MarketRegime(str, Enum)`


### `RSIState(str, Enum)`


### `TechnicalFeatures(BaseModel)`
*Core technical indicators passed to the AI.*


### `MarketStructure(BaseModel)`
*Simplified structure data (Pivots).*


### `StrategyConfig(BaseModel)`
*Strategy configuration from Strategy Simulator tab.*


### `AIAnalysisInput(BaseModel)`
*The full context payload sent to the LLM.*


### `SetupType(str, Enum)`


### `AIAnalysisOutput(BaseModel)`
*The structured decision returned by the LLM.*


## `src/core/ai_analysis/validators.py`

### `DataValidator(object)`
*Validates market data before analysis to prevent GIGO (Garbage In, Garbage Out).*

- `validate_data(df, interval_minutes)` → `Tuple[bool, str]`  *Runs all validation checks on the provided DataFrame.*
- `clean_data(df)` → `pd.DataFrame`  *Returns a cleaned copy of the DataFrame.*
- *...2 private methods*
- `__init__(max_lag_multiplier)`

## `src/core/analysis/config_store.py`

### `AnalysisConfigStore(object)`
*Static store for analysis configurations.*

- @staticmethod `get_default_strategies()` → `list[AnalysisStrategyConfig]`  *Returns the list of built-in strategy configurations.*
- @staticmethod `get_default_presets()` → `list[IndicatorPreset]`  *Returns the list of built-in indicator presets.*

## `src/core/analysis/context.py`

### `AnalysisContext(QObject)`
*Shared state for the AI Analysis module.*

- `set_market_context(history_manager, symbol, asset_class, data_source)`  *Injects dependencies required for data fetching.*
- `set_initial_analysis(result)`  *Updates context from Tab 0 result.*
- `set_symbol(symbol)`
- `get_regime()` → `str`
- `set_strategy(strategy_name)`  *Sets the active strategy by name.*
- `apply_auto_config()`  *Applies defaults from the selected strategy to timeframes and presets.*
- `get_selected_strategy()` → `Optional[AnalysisStrategyConfig]`
- `get_active_timeframes()` → `list[TimeframeConfig]`
- `get_active_preset()` → `Optional[IndicatorPreset]`
- `__init__()`

## `src/core/analysis/models.py`

### `InitialAnalysisResult(BaseModel)`
*Represents the JSON output from the initial analysis (Tab 0).*

- `extract_regime()` → `str`  *Extracts the market regime from the reasoning string.*
- `extract_metric(key)` → `Optional[float]`  *Extracts a specific numerical metric from reasoning tags.*

### `TimeframeConfig(BaseModel)`
*Configuration for a single timeframe in the analysis.*


### `IndicatorSpec(BaseModel)`
*Specification for a single indicator.*


### `IndicatorPreset(BaseModel)`
*A named collection of indicators.*


### `AnalysisStrategyConfig(BaseModel)`
*Configuration for a trading strategy analysis.*


### `DeepAnalysisPayload(BaseModel)`
*Payload sent to the LLM for the deep analysis run.*


## `src/core/analysis/orchestrator_data.py`

### `OrchestratorData(object)`
*Helper für AnalysisWorker data collection.*

- async `collect_data(tfs, symbol, hm)` → `dict[str, pd.DataFrame]`  *Collect data for all configured timeframes.*
- @staticmethod `bars_to_dataframe(bars)` → `pd.DataFrame`  *Convert bars to DataFrame.*
- @staticmethod `map_timeframe(tf_str)` → `'Timeframe'`  *Maps config string (1m, 1h) to Timeframe enum.*
- @staticmethod `get_duration_minutes(tf_str)` → `int`  *Helper to calculate lookback duration.*
- `__init__(parent)`  *Args:*

## `src/core/analysis/orchestrator_features.py`

### `OrchestratorFeatures(object)`
*Helper für AnalysisWorker feature calculation.*

- `calculate_features(data_map)` → `dict`  *Extract technical analysis features for each timeframe.*
- `__init__(parent)`  *Args:*

## `src/core/analysis/orchestrator_llm.py`

### `OrchestratorLLM(object)`
*Helper für AnalysisWorker LLM integration.*

- async `call_llm(strategy, symbol, features)` → `str | None`  *Call the configured LLM for deep market analysis.*
- `format_features_for_prompt(features)` → `str`  *Format feature data for LLM prompt.*
- `format_sr_levels_for_prompt(features)` → `str`  *Format support/resistance levels for LLM prompt.*
- @staticmethod `get_tf_role(tf)` → `str`  *Map timeframe to analysis role.*
- `__init__(parent)`  *Args:*

## `src/core/analysis/orchestrator_report.py`

### `OrchestratorReport(object)`
*Helper für AnalysisWorker report generation.*

- `generate_report(strategy, symbol, features)` → `str`  *Generate comprehensive markdown report.*
- `format_technical_summary(tf, feature_data)` → `list[str]`  *Format technical indicators for a timeframe.*
- `format_levels_summary(features, symbol)` → `list[str]`  *Aggregate support/resistance levels across timeframes.*
- `generate_trading_setup(features, symbol)` → `list[str]`  *Generate preliminary trading setup based on technical analysis.*
- `__init__(parent)`  *Args:*

## `src/core/analysis/orchestrator_worker.py`

### `AnalysisWorker(QThread)`
*Background worker for the analysis process.*

- `run()`  *Main workflow execution.*
- `__init__(context)`

## `src/core/auth/bitunix_signer.py`

### `BitunixSigner(object)`
*Signer for Bitunix API requests.*

- `generate_signature(nonce, timestamp, query_params, body)` → `str`  *Generate double SHA256 signature for Bitunix API.*
- `build_headers(query_params, body)` → `Dict[str, str]`  *Build request headers with API key and signature.*
- `__init__(api_key, api_secret)`  *Initialize signer.*

## `src/core/backtesting/backtest_runner.py`

### `BacktestRunner(object)`
*Core Engine für Single-Run Backtesting.*

- `set_progress_callback(callback)` → `None`  *Setzt Callback für Progress-Updates (0-100, message).*
- `set_signal_callback(callback)` → `None`  *Setzt Callback für Signal-Generierung.*
- async `run()` → `'BacktestResult'`  *Führt den Backtest durch (delegiert zu loop_helper).*
- `stop()` → `None`  *Stoppt den laufenden Backtest.*
- *...3 private methods*
- `__init__(config, replay_provider, mtf_resampler, execution_sim)`  *Initialize BacktestRunner.*

## `src/core/backtesting/backtest_runner_loop.py`

### `BacktestRunnerLoop(object)`
*Helper für Main Execution Loop.*

- async `run()` → `'BacktestResult'`  *Führt den Backtest durch.*
- *...5 private methods*
- `__init__(parent)`  *Args:*

## `src/core/backtesting/backtest_runner_metrics.py`

### `BacktestRunnerMetrics(object)`
*Helper für Metrics Calculation.*

- *...5 private methods*
- `__init__(parent)`  *Args:*

## `src/core/backtesting/backtest_runner_positions.py`

### `BacktestRunnerPositions(object)`
*Helper für Position Management.*

- *...5 private methods*
- `__init__(parent)`  *Args:*

## `src/core/backtesting/backtest_runner_signals.py`

### `BacktestRunnerSignals(object)`
*Helper für Signal Generation und Execution.*

- *...3 private methods*
- `__init__(parent)`  *Args:*

## `src/core/backtesting/backtest_runner_state.py`

### `TradeStatus(Enum)`
*Status eines Trades.*


### `OpenPosition(object)`
*Offene Position während des Backtests.*

- @property `trade_side()` → `str`  *Gibt 'long' oder 'short' zurück.*

### `BacktestState(object)`
*Zustand während des Backtests.*


## `src/core/backtesting/backtrader_integration.py`

### `BacktestEngine(object)`
*Engine for running backtests with Backtrader.*

- async `run_backtest(config)` → `BacktestResult`  *Run a backtest.*
- async `run_backtest_with_definition(strategy_def, symbol, start_date, end_date, initial_cash, commission, timeframe, data_feed)` → `BacktestResult`  *Run backtest with StrategyDefinition (YAML/JSON strategy).*
- async `optimize_strategy(config)` → `list[tuple[dict[str, Any], BacktestResult]]`  *Optimize strategy parameters.*
- `plot_results(result, show)`  *Plot backtest results.*
- *...8 private methods*
- `__init__(history_manager)`  *Initialize backtest engine.*

## `src/core/backtesting/backtrader_types.py`

### `BacktestConfig(object)`
*Configuration for backtesting.*

- `__post_init__()`

### `BacktestResultLegacy(object)`
*Legacy results from backtesting (deprecated, use BacktestResult from models).*


## `src/core/backtesting/batch_runner.py`

### `BatchRunResult(object)`
*Ergebnis eines einzelnen Batch-Runs.*

- @property `target_value()` → `float`  *Zielmetrik-Wert für Ranking.*
- `to_dict()` → `dict`  *Konvertiert zu Dictionary für Export.*

### `BatchSummary(object)`
*Zusammenfassung eines Batch-Runs.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary für Export.*

### `BatchRunner(object)`
*Batch-Runner für Parameter-Optimierung.*

- `set_progress_callback(callback)` → `None`  *Setzt Callback für Progress-Updates.*
- `generate_parameter_combinations()` → `list[dict[str, Any]]`  *Generiert Parameter-Kombinationen basierend auf Search Method.*
- async `run()` → `BatchSummary`  *Führt den Batch-Run durch.*
- `stop()` → `None`  *Stoppt den laufenden Batch.*
- async `export_results(output_dir, export_all_runs)` → `dict[str, Path]`  *Exportiert Ergebnisse.*
- @property `results()` → `list[BatchRunResult]`  *Gibt alle Ergebnisse zurück (gerankt).*
- @property `best_result()` → `BatchRunResult | None`  *Gibt bestes Ergebnis zurück.*
- *...8 private methods*
- `__init__(config, signal_callback, save_full_results, initial_data)`  *Initialisiert den Batch-Runner.*

## `src/core/backtesting/batch_runner_v2.py`

### `ConfigV2Converter(object)`
*Konvertiert BacktestConfigV2 zu BacktestConfig (V1).*

- @staticmethod `to_v1_config(v2_config, parameter_overrides)` → `BacktestConfig`  *Konvertiert V2-Config zu V1-Config.*
- *...1 private methods*

### `BatchRunnerV2(object)`
*Batch-Runner mit voller V2-Config Unterstuetzung.*

- @classmethod `from_template(template_name, base_path, overrides)` → `'BatchRunnerV2'`  *Erstellt BatchRunnerV2 aus einem Template.*
- @classmethod `from_file(path)` → `'BatchRunnerV2'`  *Erstellt BatchRunnerV2 aus einer JSON-Datei.*
- `set_progress_callback(callback)` → `None`  *Setzt Callback fuer Progress-Updates.*
- `get_grid_count()` → `int`  *Gibt Anzahl der Grid-Kombinationen zurueck.*
- async `run()` → `BatchSummary`  *Fuehrt den Batch-Run durch.*
- `stop()` → `None`  *Stoppt den laufenden Batch.*
- @property `results()` → `list[BatchRunResult]`  *Gibt alle Ergebnisse zurueck (gerankt).*
- @property `best_result()` → `Optional[BatchRunResult]`  *Gibt bestes Ergebnis zurueck.*
- *...5 private methods*
- `__init__(config, signal_callback, save_full_results)`  *Initialisiert den BatchRunnerV2.*

### Module Functions
- async `run_batch_from_template(template_name, overrides, progress_callback)` → `BatchSummary`  *Fuehrt Batch-Run aus einem Template durch.*
- `preview_grid(template_name)` → `dict[str, Any]`  *Zeigt Vorschau des Grid-Spaces ohne Ausfuehrung.*

## `src/core/backtesting/config.py`

### `SearchMethod(Enum)`
*Suchmethode für Batch-Tests.*


### `SlippageMethod(Enum)`
*Slippage-Berechnungsmethode.*


### `ExecutionConfig(object)`
*Konfiguration für realistische Trade-Ausführung.*


### `BacktestConfig(object)`
*Konfiguration für einen einzelnen Backtest.*

- `__post_init__()`

### `BatchConfig(object)`
*Konfiguration für Batch-Tests (Parameter-Sweeps).*


### `WalkForwardConfig(object)`
*Konfiguration für Walk-Forward Analyse.*


### `UIConfig(object)`
*UI-spezifische Konfiguration für Backtesting Tab.*


## `src/core/backtesting/config_loader.py`

### `ConfigLoader(object)`
*Laedt BacktestConfigV2 Konfigurationen mit Vererbungs-Support.*

- `load(path)` → `BacktestConfigV2`  *Laedt eine Konfigurationsdatei mit Vererbungs-Support.*
- *...4 private methods*
- `__init__(base_path, validate, resolve_conditionals)`  *Initialisiert den ConfigLoader.*

### `ParameterGroupExpander(object)`
*Expandiert Parameter-Gruppen zu Grid-Search-Kombinationen.*

- @staticmethod `expand_groups(config)` → `List[Dict[str, Any]]`  *Expandiert alle Parameter-Gruppen zu Konfigurations-Varianten.*
- *...1 private methods*

### `GridSpaceGenerator(object)`
*Generiert den vollstaendigen Suchraum fuer Optimierung.*

- @staticmethod `generate(config)` → `List[Dict[str, Any]]`  *Generiert alle Konfigurations-Varianten fuer Grid-Search.*
- *...2 private methods*

### Module Functions
- `load_config(path, base_path, validate)` → `BacktestConfigV2`  *Schnelles Laden einer Konfigurationsdatei.*
- `load_and_expand(path, base_path)` → `List[BacktestConfigV2]`  *Laedt eine Konfiguration und expandiert alle Varianten.*
- `count_grid_combinations(config)` → `int`  *Zaehlt die Anzahl der Grid-Kombinationen ohne sie zu generieren.*
- `list_templates(base_path, pattern)` → `List[Path]`  *Listet alle verfuegbaren Template-Dateien.*
- `create_from_preset(preset, overrides)` → `BacktestConfigV2`  *Erstellt eine Konfiguration aus einem benannten Preset.*

## `src/core/backtesting/config_v2.py`

### `StrategyType(str, Enum)`
*Strategie-Typen.*


### `WeightPresetName(str, Enum)`
*Vordefinierte Weight-Presets.*


### `DirectionBias(str, Enum)`
*Handelsrichtungs-Bias.*


### `ScenarioType(str, Enum)`
*Szenario-Typ.*


### `AssetClass(str, Enum)`
*Asset-Klassen.*


### `StopLossType(str, Enum)`
*Stop-Loss Typen.*


### `TakeProfitType(str, Enum)`
*Take-Profit Typen.*


### `TrailingType(str, Enum)`
*Trailing Stop Typen.*


### `SlippageMethod(str, Enum)`
*Slippage-Berechnungsmethoden.*


### `OptimizationMethod(str, Enum)`
*Optimierungsmethoden.*


### `TargetMetric(str, Enum)`
*Ziel-Metriken fuer Optimierung.*


### `OptimizableFloat(object)`
*Float-Parameter der optimiert werden kann.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'OptimizableFloat'`
- `get_search_space()` → `List[float]`  *Gibt den Suchraum fuer Optimierung zurueck.*

### `OptimizableInt(object)`
*Integer-Parameter der optimiert werden kann.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'OptimizableInt'`
- `get_search_space()` → `List[int]`  *Gibt den Suchraum fuer Optimierung zurueck.*

### `WeightPreset(object)`
*Vordefinierte Weight-Kombination.*

- `to_dict()` → `Dict[str, float]`
- @classmethod `from_dict(data)` → `'WeightPreset'`
- `validate()` → `bool`  *Prueft ob Weights zu 1.0 summieren.*

### `MetaSection(object)`
*Meta-Informationen zur Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'MetaSection'`

### `StrategyProfileSection(object)`
*Strategie-Profil-Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'StrategyProfileSection'`

### `EntryScoreGates(object)`
*Gate-Einstellungen fuer Entry Score.*

- `to_dict()` → `Dict[str, bool]`
- @classmethod `from_dict(data)` → `'EntryScoreGates'`

### `IndicatorParams(object)`
*Indikator-Parameter.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'IndicatorParams'`

### `EntryScoreSection(object)`
*Entry Score Konfiguration.*

- `get_weights()` → `WeightPreset`  *Gibt die aktiven Weights zurueck.*
- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'EntryScoreSection'`

### `BreakoutTrigger(object)`
*Breakout Trigger Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'BreakoutTrigger'`

### `PullbackTrigger(object)`
*Pullback Trigger Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'PullbackTrigger'`

### `SfpTrigger(object)`
*SFP (Swing Failure Pattern) Trigger Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'SfpTrigger'`

### `EntryTriggersSection(object)`
*Entry Triggers Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'EntryTriggersSection'`

### `StopLossConfig(object)`
*Stop-Loss Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'StopLossConfig'`

### `TakeProfitConfig(object)`
*Take-Profit Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'TakeProfitConfig'`

### `TrailingStopConfig(object)`
*Trailing Stop Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'TrailingStopConfig'`

### `PartialTPConfig(object)`
*Partial Take-Profit Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'PartialTPConfig'`

### `TimeStopConfig(object)`
*Time Stop Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'TimeStopConfig'`

### `ExitManagementSection(object)`
*Exit Management Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'ExitManagementSection'`

### `RiskLeverageSection(object)`
*Risk & Leverage Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'RiskLeverageSection'`

### `ExecutionSimulationSection(object)`
*Execution Simulation Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'ExecutionSimulationSection'`

### `OptimizationSection(object)`
*Optimierungs-Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'OptimizationSection'`

### `WalkForwardSection(object)`
*Walk-Forward Analyse Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'WalkForwardSection'`

### `ParameterGroup(object)`
*Parameter-Gruppe fuer gemeinsames Testen.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'ParameterGroup'`

### `Conditional(object)`
*Bedingte Parameter-Anpassung.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'Conditional'`

### `ConstraintsSection(object)`
*Constraints fuer Backtesting-Ergebnisse.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'ConstraintsSection'`

### `BacktestConfigV2(object)`
*Einheitliche Backtesting-Konfiguration V2.*

- `to_dict()` → `Dict[str, Any]`  *Konvertiert zu Dictionary (JSON-serialisierbar).*
- @classmethod `from_dict(data)` → `'BacktestConfigV2'`  *Erstellt aus Dictionary.*
- `to_json(indent)` → `str`  *Serialisiert zu JSON-String.*
- @classmethod `from_json(json_str)` → `'BacktestConfigV2'`  *Erstellt aus JSON-String.*
- `save(path)` → `bool`  *Speichert Konfiguration als JSON-Datei.*
- @classmethod `load(path)` → `'BacktestConfigV2'`  *Laedt Konfiguration aus JSON-Datei.*
- `get_optimizable_parameters()` → `Dict[str, List[Any]]`  *Sammelt alle Parameter mit optimize=True und gibt deren Suchraum zurueck.*
- `__str__()` → `str`
- `__repr__()` → `str`

## `src/core/backtesting/config_v2_modules/base.py`

### `StrategyType(str, Enum)`
*Strategie-Typen.*


### `WeightPresetName(str, Enum)`
*Vordefinierte Weight-Presets.*


### `DirectionBias(str, Enum)`
*Handelsrichtungs-Bias.*


### `ScenarioType(str, Enum)`
*Szenario-Typ.*


### `AssetClass(str, Enum)`
*Asset-Klassen.*


### `StopLossType(str, Enum)`
*Stop-Loss Typen.*


### `TakeProfitType(str, Enum)`
*Take-Profit Typen.*


### `TrailingType(str, Enum)`
*Trailing Stop Typen.*


### `SlippageMethod(str, Enum)`
*Slippage-Berechnungsmethoden.*


### `OptimizationMethod(str, Enum)`
*Optimierungsmethoden.*


### `TargetMetric(str, Enum)`
*Ziel-Metriken fuer Optimierung.*


### `OptimizableFloat(object)`
*Float-Parameter der optimiert werden kann.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'OptimizableFloat'`  *Create OptimizableFloat from dict or number.*
- `get_search_space()` → `List[float]`  *Gibt den Suchraum fuer Optimierung zurueck.*

### `OptimizableInt(object)`
*Integer-Parameter der optimiert werden kann.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'OptimizableInt'`  *Create OptimizableInt from dict or number.*
- `get_search_space()` → `List[int]`  *Gibt den Suchraum fuer Optimierung zurueck.*

## `src/core/backtesting/config_v2_modules/entry.py`

### `WeightPreset(object)`
*Vordefinierte Weight-Kombination.*

- `to_dict()` → `Dict[str, float]`
- @classmethod `from_dict(data)` → `'WeightPreset'`
- `validate()` → `bool`  *Prueft ob Weights zu 1.0 summieren.*

### `MetaSection(object)`
*Meta-Informationen zur Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'MetaSection'`

### `StrategyProfileSection(object)`
*Strategie-Profil-Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'StrategyProfileSection'`

### `EntryScoreGates(object)`
*Gate-Einstellungen fuer Entry Score.*

- `to_dict()` → `Dict[str, bool]`
- @classmethod `from_dict(data)` → `'EntryScoreGates'`

### `IndicatorParams(object)`
*Indikator-Parameter.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'IndicatorParams'`

### `EntryScoreSection(object)`
*Entry Score Konfiguration.*

- `get_weights()` → `WeightPreset`  *Gibt die aktiven Weights zurueck.*
- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'EntryScoreSection'`

### `BreakoutTrigger(object)`
*Breakout Trigger Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'BreakoutTrigger'`

### `PullbackTrigger(object)`
*Pullback Trigger Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'PullbackTrigger'`

### `SfpTrigger(object)`
*SFP (Swing Failure Pattern) Trigger Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'SfpTrigger'`

### `EntryTriggersSection(object)`
*Entry Triggers Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'EntryTriggersSection'`

## `src/core/backtesting/config_v2_modules/exit.py`

### `StopLossConfig(object)`
*Stop-Loss Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'StopLossConfig'`

### `TakeProfitConfig(object)`
*Take-Profit Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'TakeProfitConfig'`

### `TrailingStopConfig(object)`
*Trailing Stop Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'TrailingStopConfig'`

### `PartialTPConfig(object)`
*Partial Take-Profit Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'PartialTPConfig'`

### `TimeStopConfig(object)`
*Time Stop Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'TimeStopConfig'`

### `ExitManagementSection(object)`
*Exit Management Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'ExitManagementSection'`

## `src/core/backtesting/config_v2_modules/main.py`

### `BacktestConfigV2(object)`
*Einheitliche Backtesting-Konfiguration V2.*

- `to_dict()` → `Dict[str, Any]`  *Konvertiert zu Dictionary (JSON-serialisierbar).*
- @classmethod `from_dict(data)` → `'BacktestConfigV2'`  *Erstellt aus Dictionary.*
- `to_json(indent)` → `str`  *Serialisiert zu JSON-String.*
- @classmethod `from_json(json_str)` → `'BacktestConfigV2'`  *Erstellt aus JSON-String.*
- `save(path)` → `bool`  *Speichert Konfiguration als JSON-Datei.*
- @classmethod `load(path)` → `'BacktestConfigV2'`  *Laedt Konfiguration aus JSON-Datei.*
- `get_optimizable_parameters()` → `Dict[str, List[Any]]`  *Sammelt alle Parameter mit optimize=True und gibt deren Suchraum zurueck.*
- `__str__()` → `str`
- `__repr__()` → `str`

## `src/core/backtesting/config_v2_modules/optimization.py`

### `RiskLeverageSection(object)`
*Risk & Leverage Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'RiskLeverageSection'`

### `ExecutionSimulationSection(object)`
*Execution Simulation Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'ExecutionSimulationSection'`

### `OptimizationSection(object)`
*Optimierungs-Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'OptimizationSection'`

### `WalkForwardSection(object)`
*Walk-Forward Analyse Konfiguration.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'WalkForwardSection'`

### `ParameterGroup(object)`
*Parameter-Gruppe fuer gemeinsames Testen.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'ParameterGroup'`

### `Conditional(object)`
*Bedingte Parameter-Anpassung.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'Conditional'`

### `ConstraintsSection(object)`
*Constraints fuer Backtesting-Ergebnisse.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'ConstraintsSection'`

## `src/core/backtesting/config_validator.py`

### `ValidationError(object)`
*Ein einzelner Validierungsfehler.*

- `__str__()` → `str`

### `ValidationResult(object)`
*Ergebnis einer Validierung.*

- @property `has_errors()` → `bool`
- @property `has_warnings()` → `bool`
- `to_dict()` → `Dict[str, Any]`
- `__str__()` → `str`

### `ConfigValidator(object)`
*Validator fuer BacktestConfigV2.*

- `validate(config)` → `ValidationResult`  *Fuehrt vollstaendige Validierung durch.*
- `validate_file(path)` → `ValidationResult`  *Validiert eine JSON-Datei.*
- *...6 private methods*
- `__init__(schema_path)`  *Initialisiert den Validator.*

### `ConditionalEvaluator(object)`
*Evaluiert und wendet Conditionals auf Konfigurationen an.*

- @staticmethod `evaluate_condition(config, condition)` → `bool`  *Evaluiert eine Bedingung gegen die Konfiguration.*
- @staticmethod `apply_actions(config_dict, actions)` → `Dict[str, Any]`  *Wendet Aktionen auf ein Config-Dictionary an.*
- @classmethod `process_conditionals(config)` → `BacktestConfigV2`  *Evaluiert und wendet alle Conditionals an.*
- *...2 private methods*

### Module Functions
- `validate_config(config)` → `ValidationResult`  *Schnelle Validierung einer Konfiguration.*
- `validate_config_file(path)` → `ValidationResult`  *Schnelle Validierung einer JSON-Datei.*
- `apply_conditionals(config)` → `BacktestConfigV2`  *Wendet alle Conditionals auf eine Konfiguration an.*

## `src/core/backtesting/execution_simulator.py`

### `OrderSide(Enum)`
*Order-Seite.*


### `OrderType(Enum)`
*Order-Typ.*


### `FillStatus(Enum)`
*Fill-Status.*


### `SimulatedOrder(object)`
*Eine simulierte Order.*

- `__post_init__()`

### `SimulatedFill(object)`
*Ergebnis einer simulierten Order-Ausführung.*

- @property `total_cost()` → `float`  *Gesamtkosten inkl. Fees.*
- @property `effective_price()` → `float`  *Effektiver Preis inkl. Slippage und Fees pro Einheit.*
- `__post_init__()`

### `FeeModel(object)`
*Fee-Berechnungsmodell.*

- `calculate_fee(notional, is_taker)` → `tuple[float, float]`  *Berechnet die Fee.*
- `__init__(maker_rate, taker_rate)`  *Initialisiert das Fee-Modell.*

### `SlippageModel(object)`
*Slippage-Berechnungsmodell.*

- `calculate_slippage(price, side, atr, volume_ratio)` → `tuple[float, float]`  *Berechnet Slippage.*
- `__init__(method, fixed_bps, atr_mult)`  *Initialisiert das Slippage-Modell.*

### `ExecutionSimulator(object)`
*Simuliert realistische Order-Ausführung für Backtesting.*

- `execute_order(order, market_price, atr, available_margin, volume_ratio)` → `SimulatedFill`  *Führt eine Order aus.*
- `check_liquidation(position_side, entry_price, current_price, leverage)` → `tuple[bool, float]`  *Prüft, ob eine Position liquidiert werden würde.*
- `calculate_pnl(entry_price, exit_price, quantity, side, leverage, include_fees, entry_fee, exit_fee)` → `dict`  *Berechnet den PnL für einen Trade.*
- `get_statistics()` → `dict`  *Gibt Ausführungsstatistiken zurück.*
- `reset()` → `None`  *Setzt den Simulator zurück.*
- *...1 private methods*
- `__init__(config)`  *Initialisiert den Simulator.*

## `src/core/backtesting/mtf_resampler.py`

### `ResampledBar(object)`
*Eine resampelte Bar.*

- @property `datetime()` → `datetime`  *Start-Timestamp als datetime.*
- @property `datetime_end()` → `datetime`  *End-Timestamp als datetime.*

### `MTFResampler(object)`
*Multi-Timeframe Resampler mit No-Leak-Garantie.*

- `get_timeframe_minutes(timeframe)` → `int`  *Gibt die Anzahl Minuten für einen Timeframe zurück.*
- `get_bar_start_timestamp(timestamp_ms, timeframe)` → `int`  *Berechnet den Start-Timestamp einer Bar.*
- `get_bar_end_timestamp(timestamp_ms, timeframe)` → `int`  *Berechnet den End-Timestamp einer Bar.*
- `is_bar_complete(current_1m_timestamp, bar_start_timestamp, timeframe)` → `bool`  *Prüft, ob eine Higher-TF Bar vollständig ist.*
- `resample_history(history_1m, current_timestamp, timeframe)` → `pd.DataFrame`  *Resampled 1m History zu einem Higher-TF.*
- `update(current_candle_ts, history_1m)` → `dict[str, pd.DataFrame]`  *Update mit neuer 1m Candle, gibt alle MTF Daten zurück.*
- `get_latest_complete_bar(timeframe)` → `ResampledBar | None`  *Gibt die letzte vollständige Bar für einen TF zurück.*
- `get_all_bars(timeframe)` → `list[ResampledBar]`  *Gibt alle gecachten Bars für einen TF zurück.*
- `clear_cache()` → `None`  *Leert den Cache.*
- `get_cache_statistics()` → `dict[str, int]`  *Gibt Cache-Statistiken zurück.*
- `get_current_timeframes(bar_index)` → `dict[str, pd.DataFrame]`  *Gibt die aktuellen gecachten MTF-Daten zurück.*
- *...1 private methods*
- `__init__(timeframes, history_bars_per_tf)`  *Initialisiert den Resampler.*

### Module Functions
- `_safe_timestamp_to_int(value)` → `int`  *Konvertiert verschiedene Timestamp-Typen sicher zu int (Millisekunden).*

## `src/core/backtesting/optimization.py`

### `ParameterOptimizer(object)`
*AI-guided parameter optimizer for trading strategies.*

- async `grid_search(parameter_ranges, base_params)` → `OptimizationResult`  *Perform grid search optimization.*
- async `optimize_with_ai(parameter_ranges, base_params, max_iterations)` → `tuple[OptimizationResult, AIOptimizationInsight]`  *Perform AI-guided optimization with iterative refinement.*
- *...10 private methods*
- `__init__(backtest_runner, config)`  *Initialize parameter optimizer.*

### Module Functions
- async `quick_optimize(backtest_runner, parameter_ranges, base_params, primary_metric)` → `OptimizationResult`  *Quick parameter optimization with default settings.*

## `src/core/backtesting/optimization_types.py`

### `ParameterRange(BaseModel)`
*Parameter range for optimization.*


### `OptimizationMetric(BaseModel)`
*Metric for optimization.*


### `ParameterTest(BaseModel)`
*Single parameter test result.*


### `OptimizationResult(BaseModel)`
*Complete optimization result.*


### `AIOptimizationInsight(BaseModel)`
*AI-generated optimization insights.*


### `OptimizerConfig(object)`
*Configuration for parameter optimizer.*


## `src/core/backtesting/replay_provider.py`

### `CandleSnapshot(object)`
*Einzelne Candle mit Metadaten.*

- @property `datetime()` → `datetime`  *Timestamp als datetime.*
- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

### `CandleIteratorState(object)`
*State für den Candle Iterator.*


### `CandleIterator(object)`
*Iterator für Candle-by-Candle Replay.*

- @property `progress()` → `float`  *Fortschritt in Prozent (0-100).*
- `reset()` → `None`  *Setzt Iterator auf Anfang zurück.*
- `peek()` → `CandleSnapshot | None`  *Zeigt nächste Candle ohne weiterzugehen.*
- *...1 private methods*
- *...4 dunder methods*

### `ReplayMarketDataProvider(object)`
*Provider für historische Marktdaten im Replay-Modus.*

- async `load_data(symbol, start_date, end_date, validate)` → `int`  *Lädt historische Daten aus der Datenbank.*
- `load_from_dataframe(df)` → `int`  *Lädt Daten direkt aus einem DataFrame.*
- `iterate()` → `CandleIterator`  *Gibt Iterator für Candle-by-Candle Replay zurück.*
- async `replay_iter(yield_every)` → `AsyncIterator[tuple[CandleSnapshot, pd.DataFrame]]`  *Async-Iterator für Candle-by-Candle Replay.*
- @property `data()` → `pd.DataFrame | None`  *Rohes DataFrame (für Analyse/Debug).*
- @property `bar_count()` → `int`  *Anzahl geladener Bars.*
- @property `date_range()` → `tuple[datetime | None, datetime | None]`  *Datum-Bereich der geladenen Daten.*
- `get_statistics()` → `dict`  *Gibt Statistiken über die geladenen Daten zurück.*
- *...4 private methods*
- `__init__(history_window)`  *Initialisiert den Provider.*

### Module Functions
- `_safe_timestamp_to_int(value)` → `int`  *Konvertiert verschiedene Timestamp-Typen sicher zu int (Millisekunden).*

## `src/core/backtesting/result_converter.py`

### Module Functions
- `backtrader_to_backtest_result(strategy, cerebro, initial_value, final_value, symbol, timeframe, start_date, end_date, strategy_name, strategy_params)` → `BacktestResult`  *Convert Backtrader results to comprehensive BacktestResult.*
- `_extract_bars_from_strategy(strategy, symbol)` → `list[Bar]`  *Extract OHLCV bars from Backtrader strategy data feed.*
- `_extract_trades_from_strategy(strategy, symbol)` → `list[Trade]`  *Extract trades from Backtrader strategy.*
- `_extract_equity_curve(strategy, initial_value)` → `list[EquityPoint]`  *Extract equity curve from Backtrader strategy.*
- `_calculate_metrics(trades, equity_curve, initial_capital, final_capital, start_date, end_date, strategy_analyzers)` → `BacktestMetrics`  *Calculate comprehensive backtest metrics.*
- `_trade_stats(trades)` → `tuple[int, int, int, float]`
- `_pnl_stats(trades, win_rate)` → `tuple[float, float, float, float, float, float | None]`
- `_r_multiple_stats(trades)` → `tuple[float | None, float | None, float | None]`
- `_return_stats(initial_capital, final_capital, start_date, end_date)` → `tuple[float, float]`
- `_analyzer_risk_metrics(strategy_analyzers)` → `tuple[float | None, float | None, float, int | None]`
- `_avg_trade_duration_minutes(trades)` → `float | None`
- `_calculate_max_consecutive(trades, is_winner)` → `int`  *Calculate maximum consecutive wins or losses.*
- `_extract_indicators(strategy)` → `dict[str, list[tuple[datetime, float]]]`  *Extract indicator values from Backtrader strategy.*

## `src/core/backtesting/walk_forward_executor.py`

### `WalkForwardExecutor(object)`
*Helper für WalkForwardRunner main execution.*

- async `run()`  *Führt die Walk-Forward Analyse durch.*
- `stop()` → `None`  *Stoppt die laufende Analyse.*
- `__init__(parent)`  *Args:*

## `src/core/backtesting/walk_forward_export.py`

### `WalkForwardExport(object)`
*Helper für WalkForwardRunner results export.*

- async `export_results(output_dir)` → `dict[str, Path]`  *Exportiert Ergebnisse.*
- `__init__(parent)`  *Args:*

## `src/core/backtesting/walk_forward_fold_calculator.py`

### `WalkForwardFoldCalculator(object)`
*Helper für WalkForwardRunner fold period calculation.*

- `calculate_folds()` → `list[tuple[datetime, datetime, datetime, datetime]]`  *Berechnet die Fold-Zeiträume.*
- `__init__(parent)`  *Args:*

## `src/core/backtesting/walk_forward_fold_runner.py`

### `WalkForwardFoldRunner(object)`
*Helper für WalkForwardRunner individual fold execution.*

- async `run_fold(fold_index, train_start, train_end, test_start, test_end)`  *Führt einen einzelnen Fold durch.*
- `__init__(parent)`  *Args:*

## `src/core/backtesting/walk_forward_metrics.py`

### `WalkForwardMetrics(object)`
*Helper für WalkForwardRunner metrics aggregation.*

- `calculate_aggregated_metrics()` → `dict[str, float]`  *Berechnet aggregierte OOS-Metriken über alle Folds.*
- `calculate_stability_metrics()` → `dict[str, float]`  *Berechnet Stabilitätsmetriken über alle Folds.*
- `__init__(parent)`  *Args:*

## `src/core/backtesting/walk_forward_progress.py`

### `WalkForwardProgress(object)`
*Helper für WalkForwardRunner progress management.*

- `set_progress_callback(callback)` → `None`  *Setzt Callback für Progress-Updates.*
- `emit_progress(progress, message)` → `None`  *Emittiert Progress-Update.*
- `__init__(parent)`  *Args:*

## `src/core/backtesting/walk_forward_runner.py`

### `FoldResult(object)`
*Ergebnis eines einzelnen Walk-Forward Folds.*

- @property `is_successful()` → `bool`  *True wenn Fold erfolgreich.*
- @property `oos_expectancy()` → `float | None`  *Out-of-Sample Expectancy.*
- @property `oos_profit_factor()` → `float | None`  *Out-of-Sample Profit Factor.*
- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

### `WalkForwardSummary(object)`
*Zusammenfassung der Walk-Forward Analyse.*

- @property `success_rate()` → `float`  *Erfolgsrate der Folds.*
- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

### `WalkForwardRunner(object)`
*Walk-Forward Analyse Runner.*

- `set_progress_callback(callback)` → `None`  *Setzt Callback für Progress-Updates.*
- `calculate_folds()` → `list[tuple[datetime, datetime, datetime, datetime]]`  *Berechnet die Fold-Zeiträume.*
- async `run()` → `WalkForwardSummary`  *Führt die Walk-Forward Analyse durch.*
- `stop()` → `None`  *Stoppt die laufende Analyse.*
- async `export_results(output_dir)` → `dict[str, Path]`  *Exportiert Ergebnisse.*
- @property `folds()` → `list[FoldResult]`  *Gibt alle Fold-Ergebnisse zurück.*
- `__init__(config, signal_callback)`  *Initialisiert den Walk-Forward Runner.*

## `src/core/broker/alpaca_adapter.py`

### `AlpacaAdapter(BrokerAdapter)`
*Alpaca broker adapter.*

- async `is_connected()` → `bool`  *Check if connected to Alpaca.*
- async `cancel_order(order_id)` → `bool`  *Cancel order on Alpaca.*
- async `get_order_status(order_id)` → `OrderResponse`  *Get order status from Alpaca.*
- async `get_positions()` → `list[Position]`  *Get current positions from Alpaca.*
- async `get_balance()` → `Balance`  *Get account balance from Alpaca.*
- async `get_quote(symbol)` → `dict[str, Any] | None`  *Get latest quote for symbol.*
- *...10 private methods*
- `__init__(api_key, api_secret, paper)`  *Initialize Alpaca adapter.*

## `src/core/broker/base.py`

### `BrokerAdapter(ABC)`
*Abstract base class for broker integrations with template methods.*

- async `connect()` → `None`  *Establish connection to broker using template method pattern.*
- async `disconnect()` → `None`  *Disconnect from broker using template method pattern.*
- async `is_connected()` → `bool`  *Check if connected to broker.*
- async `is_available()` → `bool`  *Check if broker API is available.*
- async `place_order(order)` → `OrderResponse`  *Place an order with the broker.*
- async `cancel_order(order_id)` → `bool`  *Cancel an order.*
- async `get_order_status(order_id)` → `OrderResponse`  *Get current order status.*
- async `get_positions()` → `list[Position]`  *Get all current positions.*
- async `get_balance()` → `Balance`  *Get account balance.*
- async `get_quote(symbol)` → `dict[str, Any] | None`  *Get current quote for symbol (if supported).*
- `calculate_fee(order)` → `Decimal`  *Calculate estimated fee for order.*
- `activate_kill_switch()` → `None`  *Activate the kill switch to halt all trading.*
- `deactivate_kill_switch()` → `None`  *Deactivate the kill switch.*
- *...9 private methods*
- `__init__(name, fee_model, rate_limit, ai_hook)`  *Initialize broker adapter.*

## `src/core/broker/bitunix_adapter.py`

### `BitunixAdapter(BrokerAdapter)`
*Bitunix Futures trading adapter.*

- @property `connected()` → `bool`
- async `cancel_order(order_id)` → `bool`  *Cancel an order.*
- async `get_order_status(order_id)` → `OrderResponse`  *Get current order status.*
- async `get_positions()` → `list[Position]`  *Get all current positions.*
- async `get_balance(margin_coin)` → `Balance | None`  *Get account balance.*
- *...13 private methods*
- `__init__(api_key, api_secret, use_testnet, fee_model)`  *Initialize Bitunix adapter.*

## `src/core/broker/bitunix_paper_adapter.py`

### `BitunixPaperAdapter(BrokerAdapter)`
*Paper trading adapter for Bitunix Futures.*

- @property `connected()` → `bool`
- async `get_balance()` → `Balance`  *Get simulated balance.*
- async `get_positions()` → `list[Position]`  *Get current open positions.*
- async `place_order(order)` → `OrderResponse`  *Validate and place order via base template method.*
- async `cancel_order(order_id)` → `bool`  *Mark an order as cancelled if it exists.*
- async `get_order_status(order_id)` → `OrderResponse`  *Return current status of an order.*
- `reset_account(amount)`  *Reset paper account.*
- async `get_historical_bars(symbol, timeframe, limit)` → `list[dict] | None`  *Get historical bars for the given symbol.*
- `set_history_manager(history_manager)` → `None`  *Set or update the HistoryManager for market data access.*
- *...5 private methods*
- `__init__(start_balance, history_manager)`

## `src/core/broker/broker_service.py`

### `BrokerService(object)`
*Singleton service for centralized broker management.*

- @classmethod `instance()` → `'BrokerService'`  *Get the singleton instance.*
- @classmethod `reset_instance()` → `None`  *Reset the singleton instance (for testing only).*
- @property `broker()` → `Optional['BrokerAdapter']`  *Get the current broker adapter.*
- @property `broker_type()` → `str`  *Get the current broker type name.*
- @property `is_connected()` → `bool`  *Check if broker is connected.*
- @property `is_connecting()` → `bool`  *Check if connection is in progress.*
- @property `last_error()` → `Optional[Exception]`  *Get the last connection error.*
- async `connect(broker_type)` → `bool`  *Connect to a broker (thread-safe).*
- async `disconnect()` → `None`  *Disconnect from current broker (thread-safe).*
- *...3 private methods*
- `__init__()`  *Initialize the BrokerService.*

### Module Functions
- `get_broker_service()` → `BrokerService`  *Get the global BrokerService instance.*

## `src/core/broker/broker_types.py`

### `BrokerError(Exception)`
*Base exception for broker-related errors.*

- `__init__(code, message, details)`

### `BrokerConnectionError(BrokerError)`
*Raised when broker connection fails.*


### `OrderValidationError(BrokerError)`
*Raised when order validation fails.*


### `InsufficientFundsError(BrokerError)`
*Raised when account has insufficient funds.*


### `RateLimitError(BrokerError)`
*Raised when rate limit is exceeded.*


### `OrderRequest(BaseModel)`
*Standardized order request.*

- @classmethod `validate_limit_price(v, info)` → `Decimal | None`  *Ensure limit price is set for limit orders.*
- @classmethod `validate_stop_price(v, info)` → `Decimal | None`  *Ensure stop price is set for stop orders.*

### `OrderResponse(BaseModel)`
*Standardized order response.*


### `Position(BaseModel)`
*Current position information.*

- @property `is_long()` → `bool`
- @property `is_short()` → `bool`

### `Balance(BaseModel)`
*Account balance information.*


### `FeeModel(BaseModel)`
*Fee calculation model.*

- `calculate(order_value, quantity)` → `Decimal`  *Calculate total fee for an order.*

### `AIAnalysisRequest(BaseModel)`
*Request for AI analysis before order placement.*


### `AIAnalysisResult(BaseModel)`
*Result from AI analysis.*


### `TokenBucketRateLimiter(object)`
*Token bucket rate limiter for API calls.*

- async `acquire(tokens)` → `None`  *Acquire tokens, blocking if necessary.*
- `try_acquire(tokens)` → `bool`  *Try to acquire tokens without blocking.*
- `__init__(rate, burst)`  *Initialize rate limiter.*

## `src/core/broker/ibkr_adapter.py`

### `IBKRWrapper(EWrapper)`
*IB API Wrapper for handling callbacks.*

- `nextValidId(orderId)`  *Callback for next valid order ID.*
- `connectionClosed()`  *Callback when connection is closed.*
- `error(reqId, errorCode, errorString)`  *Error callback.*
- `orderStatus(orderId, status, filled, _remaining, avgFillPrice, _permId, _parentId, _lastFillPrice, _clientId, _whyHeld, _mktCapPrice)`  *Order status update callback.*
- `position(account, contract, position, avgCost)`  *Position update callback.*
- `accountSummary(reqId, account, tag, value, currency)`  *Account summary callback.*
- `historicalData(reqId, bar)`  *Historical data callback.*
- `tickPrice(reqId, tickType, price, _attrib)`  *Tick price callback.*
- *...1 private methods*
- `__init__()`

### `IBKRClient(EClient)`
*IB API Client.*

- `__init__(wrapper)`

### `IBKRAdapter(BrokerAdapter)`
*Interactive Brokers adapter using official TWS/Gateway API.*

- async `is_connected()` → `bool`  *Check if connected to IBKR.*
- async `cancel_order(order_id)` → `bool`  *Cancel an order.*
- async `get_order_status(order_id)` → `OrderResponse`  *Get current order status.*
- async `get_positions()` → `list[Position]`  *Get all current positions.*
- async `get_balance()` → `Balance`  *Get account balance.*
- async `get_quote(symbol)` → `dict[str, Any] | None`  *Get current quote for symbol.*
- async `get_historical_bars(symbol, duration, bar_size)` → `list[dict[str, Any]]`  *Get historical bars for symbol.*
- *...8 private methods*
- `__init__(host, port, client_id, paper_trading)`  *Initialize IBKR adapter.*

## `src/core/broker/mock_broker.py`

### `MockBroker(BrokerAdapter)`
*Mock broker for testing and development.*

- async `cancel_order(order_id)` → `bool`  *Cancel an order.*
- async `get_order_status(order_id)` → `OrderResponse`  *Get order status.*
- async `get_positions()` → `list[Position]`  *Get all positions.*
- async `get_balance()` → `Balance`  *Get account balance.*
- async `get_quote(symbol)` → `dict[str, Any] | None`  *Get current quote for symbol.*
- `set_market_price(symbol, price)` → `None`  *Set market price for testing.*
- *...6 private methods*
- `__init__(initial_cash)`  *Initialize mock broker.*

## `src/core/broker/trade_republic_adapter.py`

### `TradeRepublicAdapter(BrokerAdapter)`
*Trade Republic broker adapter using unofficial API.*

- async `is_connected()` → `bool`  *Check if connected to Trade Republic.*
- async `cancel_order(order_id)` → `bool`  *Cancel an order.*
- async `get_order_status(order_id)` → `OrderResponse`  *Get current order status.*
- async `get_positions()` → `list[Position]`  *Get all current positions.*
- async `get_balance()` → `Balance`  *Get account balance.*
- *...17 private methods*
- `__init__(phone_number, pin)`  *Initialize Trade Republic adapter.*

## `src/core/execution/engine.py`

### `ExecutionState(Enum)`
*Execution engine states.*


### `ExecutionTask(object)`
*Represents a task in the execution queue.*

- `__post_init__()`

### `ExecutionEngine(object)`
*Manages order execution with safety controls.*

- async `start()` → `None`  *Start the execution engine.*
- async `stop()` → `None`  *Stop the execution engine.*
- `pause()` → `None`  *Pause execution engine.*
- `resume()` → `None`  *Resume execution engine.*
- `activate_kill_switch(reason)` → `None`  *Activate kill switch to halt all trading.*
- `deactivate_kill_switch()` → `None`  *Deactivate kill switch.*
- async `submit_order(order_request, broker, priority, manual_approval, ai_analysis)` → `str`  *Submit an order for execution.*
- `get_status()` → `dict[str, Any]`  *Get execution engine status.*
- async `update_metrics(pnl, equity)` → `None`  *Update risk metrics.*
- `__init__(max_pending_orders, order_timeout_seconds, manual_approval_default, kill_switch_enabled, max_loss_per_day, max_drawdown_percent)`  *Initialize execution engine.*

## `src/core/execution/engine_approval.py`

### `EngineApproval(object)`
*Helper für ExecutionEngine approval & cancellation.*

- async `get_manual_approval(task)` → `bool`  *Get manual approval for order.*
- async `cancel_order(task)` → `None`  *Cancel an active order.*
- `__init__(parent)`  *Args:*

## `src/core/execution/engine_events.py`

### `EngineEvents(object)`
*Helper für ExecutionEngine event emission.*

- `emit_order_submitted(task, response)` → `None`
- `emit_filled_events(task, response)` → `None`
- `emit_trade_entry_exit(task, response, side_str, avg_price)` → `None`
- `order_side_str(task)` → `str`
- `order_type_str(task)` → `str`
- `__init__(parent)`  *Args:*

## `src/core/execution/engine_execution.py`

### `EngineExecution(object)`
*Helper für ExecutionEngine task execution.*

- async `execute_task(task)` → `None`  *Execute a single task.*
- `is_task_timed_out(task)` → `bool`
- async `execute_and_record(task)` → `None`
- async `handle_execution_retry(task)` → `None`
- `__init__(parent)`  *Args:*

## `src/core/execution/engine_kill_switch.py`

### `EngineKillSwitch(object)`
*Helper für ExecutionEngine kill switch.*

- `activate_kill_switch(reason)` → `None`  *Activate kill switch to halt all trading.*
- `deactivate_kill_switch()` → `None`  *Deactivate kill switch.*
- `__init__(parent)`  *Args:*

## `src/core/execution/engine_lifecycle.py`

### `EngineLifecycle(object)`
*Helper für ExecutionEngine lifecycle management.*

- async `start()` → `None`  *Start the execution engine.*
- async `stop()` → `None`  *Stop the execution engine.*
- `pause()` → `None`  *Pause execution engine.*
- `resume()` → `None`  *Resume execution engine.*
- async `process_queue()` → `None`  *Process orders from the queue.*
- `__init__(parent)`  *Args:*

## `src/core/execution/engine_persistence.py`

### `EnginePersistence(object)`
*Helper für ExecutionEngine persistence & status.*

- async `store_order(task, response)` → `None`  *Store order in database.*
- `get_status()` → `dict[str, Any]`  *Get execution engine status.*
- async `update_metrics(pnl, equity)` → `None`  *Update risk metrics.*
- `__init__(parent)`  *Args:*

## `src/core/execution/engine_submission.py`

### `EngineSubmission(object)`
*Helper für ExecutionEngine order submission.*

- `set_risk_manager(risk_manager)` → `None`  *Set risk manager for pre-trade validation.*
- async `submit_order(order_request, broker, priority, manual_approval, ai_analysis)` → `str`  *Submit an order for execution.*
- async `check_risk_limits(order)` → `bool`  *Check if order passes risk limits.*
- *...2 private methods*
- `__init__(parent)`  *Args:*

## `src/core/execution/events.py`

### `OrderEventEmitter(object)`
*Emits order events to the event bus for chart markers and UI updates.*

- `emit_order_created(order_id, order_type, side, quantity, price)` → `None`  *Emit ORDER_CREATED event.*
- `emit_order_submitted(order_id)` → `None`  *Emit ORDER_SUBMITTED event.*
- `emit_order_filled(order_id, filled_quantity, avg_fill_price)` → `None`  *Emit ORDER_FILLED event.*
- `emit_order_partial_fill(order_id, filled_quantity, remaining_quantity, avg_fill_price)` → `None`  *Emit ORDER_PARTIAL_FILL event.*
- `emit_order_cancelled(order_id, reason)` → `None`  *Emit ORDER_CANCELLED event.*
- `emit_order_rejected(order_id, reason)` → `None`  *Emit ORDER_REJECTED event.*
- `__init__(symbol, source)`  *Initialize the order event emitter.*

### `ExecutionEventEmitter(object)`
*Emits execution events (trade entry/exit) for chart markers.*

- `emit_trade_entry(trade_id, side, quantity, price)` → `None`  *Emit TRADE_ENTRY event for chart marker.*
- `emit_trade_exit(trade_id, side, quantity, price, pnl, pnl_pct, reason)` → `None`  *Emit TRADE_EXIT event for chart marker.*
- `emit_stop_loss_hit(trade_id, side, quantity, price, pnl, pnl_pct)` → `None`  *Emit STOP_LOSS_HIT event.*
- `emit_take_profit_hit(trade_id, side, quantity, price, pnl, pnl_pct)` → `None`  *Emit TAKE_PROFIT_HIT event.*
- `emit_position_opened(position_id, side, quantity, price)` → `None`  *Emit POSITION_OPENED event.*
- `emit_position_closed(position_id, pnl, pnl_pct)` → `None`  *Emit POSITION_CLOSED event.*
- `__init__(symbol, source)`  *Initialize the execution event emitter.*

### `BacktraderEventAdapter(object)`
*Adapter to emit events from Backtrader strategy execution.*

- `on_order_created(order)` → `None`  *Handle order created by Backtrader.*
- `on_order_submitted(order)` → `None`  *Handle order submitted.*
- `on_order_filled(order, execution)` → `None`  *Handle order filled and emit appropriate events.*
- `on_order_cancelled(order)` → `None`  *Handle order cancelled.*
- `on_order_rejected(order)` → `None`  *Handle order rejected.*
- *...2 private methods*
- `__init__(symbol, source)`  *Initialize the Backtrader event adapter.*

## `src/core/indicator_set_optimizer.py`

### `SignalMetrics(object)`
*Metrics from signal backtest.*


### `OptimizationResult(object)`
*Result from indicator optimization.*


### `SignalBacktest(object)`
*Simulates trades from signals with realistic slippage and fees.*

- `backtest_entry_long(signal, hold_bars)` → `SignalMetrics`  *Backtest entry long signals.*
- `backtest_entry_short(signal, hold_bars)` → `SignalMetrics`  *Backtest entry short signals.*
- `backtest_exit_timing(signal, direction)` → `SignalMetrics`  *Evaluate exit signal timing quality.*
- *...2 private methods*
- `__init__(df, slippage_pct, fee_pct)`  *Initialize backtest.*

### `IndicatorSetOptimizer(object)`
*Optimizes indicator sets for entry/exit signals per regime.*

- `optimize_all_signals(n_trials_per_indicator)` → `dict[str, OptimizationResult]`  *Optimize all 4 signal types.*
- `export_to_json(results, output_dir)` → `str`  *Export results to JSON.*
- *...13 private methods*
- `__init__(df, regime, regime_indices, symbol, timeframe, regime_config_path)`  *Initialize optimizer.*

## `src/core/indicators/base.py`

### `BaseIndicatorCalculator(object)`
*Base class for indicator calculators.*

- @staticmethod `validate_data(data, config)` → `bool`  *Validate input data.*
- @staticmethod `create_result(indicator_type, values, params, metadata)` → `IndicatorResult`  *Create indicator result.*

## `src/core/indicators/custom.py`

### `CustomIndicators(BaseIndicatorCalculator)`
*Calculator for custom indicators.*

- @staticmethod `calculate_pivots(data, params, use_talib)` → `IndicatorResult`  *Calculate Pivot Points.*
- @staticmethod `calculate_support_resistance(data, params, use_talib)` → `IndicatorResult`  *Calculate Support and Resistance levels.*
- @staticmethod `calculate_patterns(data, params, use_talib)` → `IndicatorResult`  *Detect price patterns.*

## `src/core/indicators/engine.py`

### `IndicatorEngine(object)`
*Engine for calculating technical indicators.*

- `calculate(data, config)` → `IndicatorResult`  *Calculate indicator for given data.*
- `calculate_multiple(data, configs)` → `dict[IndicatorType, IndicatorResult]`  *Calculate multiple indicators.*
- `clear_cache()` → `None`  *Clear indicator cache.*
- *...1 private methods*
- `__init__(cache_size)`  *Initialize indicator engine.*

## `src/core/indicators/momentum.py`

### `MomentumIndicators(BaseIndicatorCalculator)`
*Calculator for momentum indicators.*

- @staticmethod `calculate_rsi(data, params, use_talib)` → `IndicatorResult`  *Calculate RSI.*
- @staticmethod `calculate_stoch(data, params, use_talib)` → `IndicatorResult`  *Calculate Stochastic Oscillator.*
- @staticmethod `calculate_mom(data, params, use_talib)` → `IndicatorResult`  *Calculate Momentum.*
- @staticmethod `calculate_roc(data, params, use_talib)` → `IndicatorResult`  *Calculate Rate of Change.*
- @staticmethod `calculate_willr(data, params, use_talib)` → `IndicatorResult`  *Calculate Williams %R.*
- @staticmethod `calculate_cci(data, params, use_talib)` → `IndicatorResult`  *Calculate CCI.*
- @staticmethod `calculate_mfi(data, params, use_talib)` → `IndicatorResult`  *Calculate Money Flow Index.*

## `src/core/indicators/regime.py`

### `RegimeIndicators(BaseIndicatorCalculator)`
*Calculators for regime detection indicators.*

- @staticmethod `calculate_momentum_score(data, params, use_talib)` → `IndicatorResult`  *Calculate momentum score from SMA crossovers and price position.*
- @staticmethod `calculate_volume_ratio(data, params, use_talib)` → `IndicatorResult`  *Calculate volume ratio relative to moving average.*
- @staticmethod `calculate_price_strength(data, params, use_talib)` → `IndicatorResult`  *Calculate combined price strength indicator.*

## `src/core/indicators/registry.py`

### `IndicatorDefinition(object)`
*Definition of a UI-accessible indicator.*


### Module Functions
- `get_overlay_configs()` → `Dict[str, Tuple[IndicatorType, Dict, str, None, None]]`  *Get overlay configs in legacy format for compatibility.*
- `get_oscillator_configs()` → `Dict[str, Tuple[IndicatorType, Dict, str, Optional[float], Optional[float]]]`  *Get oscillator configs in legacy format for compatibility.*

## `src/core/indicators/trend.py`

### `TrendIndicators(BaseIndicatorCalculator)`
*Calculator for trend indicators.*

- @staticmethod `calculate_sma(data, params, use_talib)` → `IndicatorResult`  *Calculate Simple Moving Average.*
- @staticmethod `calculate_ema(data, params, use_talib)` → `IndicatorResult`  *Calculate Exponential Moving Average.*
- @staticmethod `calculate_wma(data, params, use_talib)` → `IndicatorResult`  *Calculate Weighted Moving Average.*
- @staticmethod `calculate_vwma(data, params, use_talib)` → `IndicatorResult`  *Calculate Volume Weighted Moving Average.*
- @staticmethod `calculate_macd(data, params, use_talib)` → `IndicatorResult`  *Calculate MACD.*
- @staticmethod `calculate_adx(data, params, use_talib)` → `IndicatorResult`  *Calculate ADX.*
- @staticmethod `calculate_psar(data, params, use_talib)` → `IndicatorResult`  *Calculate Parabolic SAR.*
- @staticmethod `calculate_ichimoku(data, params, use_talib)` → `IndicatorResult`  *Calculate Ichimoku Cloud.*

## `src/core/indicators/types.py`

### `IndicatorType(Enum)`
*Types of technical indicators.*


### `IndicatorConfig(object)`
*Configuration for an indicator.*


### `IndicatorResult(object)`
*Result from indicator calculation.*


## `src/core/indicators/volatility.py`

### `VolatilityIndicators(BaseIndicatorCalculator)`
*Calculator for volatility indicators.*

- @staticmethod `calculate_bb(data, params, use_talib)` → `IndicatorResult`  *Calculate Bollinger Bands (refactored).*
- @staticmethod `calculate_bb_width(data, params, use_talib)` → `IndicatorResult`  *Calculate Bollinger Bandwidth.*
- @staticmethod `calculate_bb_percent(data, params, use_talib)` → `IndicatorResult`  *Calculate Bollinger %B.*
- @staticmethod `calculate_kc(data, params, use_talib)` → `IndicatorResult`  *Calculate Keltner Channels.*
- @staticmethod `calculate_atr(data, params, use_talib)` → `IndicatorResult`  *Calculate Average True Range.*
- @staticmethod `calculate_natr(data, params, use_talib)` → `IndicatorResult`  *Calculate Normalized ATR.*
- @staticmethod `calculate_std(data, params, use_talib)` → `IndicatorResult`  *Calculate Standard Deviation.*
- @staticmethod `calculate_chop(data, params, use_talib)` → `IndicatorResult`  *Calculate Choppiness Index (CHOP).*
- *...4 private methods*

## `src/core/indicators/volume.py`

### `VolumeIndicators(BaseIndicatorCalculator)`
*Calculator for volume indicators.*

- @staticmethod `calculate_obv(data, params, use_talib)` → `IndicatorResult`  *Calculate On-Balance Volume.*
- @staticmethod `calculate_cmf(data, params, use_talib)` → `IndicatorResult`  *Calculate Chaikin Money Flow.*
- @staticmethod `calculate_ad(data, params, use_talib)` → `IndicatorResult`  *Calculate Accumulation/Distribution.*
- @staticmethod `calculate_fi(data, params, use_talib)` → `IndicatorResult`  *Calculate Force Index.*
- @staticmethod `calculate_vwap(data, params, use_talib)` → `IndicatorResult`  *Calculate VWAP.*

## `src/core/jokes/trading_jokes_service.py`

### `TradingJokesService(object)`
*Service für Trading-Witze aus SQLite-Datenbank.*

- `get_random_joke(language, exclude_ids)` → `tuple[str, int]`  *Get a random trading joke.*
- `get_random_joke_with_category(language)` → `tuple[str, str]`  *Get a random trading joke with its category.*
- `get_joke_count()` → `int`  *Get total number of jokes in database.*
- *...4 private methods*
- `__new__()` → `TradingJokesService`  *Singleton pattern.*
- `__init__()`  *Initialize the jokes service.*

### Module Functions
- `get_random_trading_joke(language, exclude_ids)` → `tuple[str, int]`  *Get a random trading joke (convenience function).*
- `get_random_trading_joke_simple(language)` → `str`  *Get a random trading joke - simple version without ID tracking.*

## `src/core/market_data/alpaca_bad_tick_detector.py`

### `BadTickDetector(BaseBadTickDetector[FilterConfig, FilterStats, object])`
*Alpaca-specific bad tick detector.*

- *...3 private methods*

## `src/core/market_data/alpaca_crypto_provider.py`

### `AlpacaCryptoProvider(HistoricalDataProvider)`
*Alpaca cryptocurrency historical data provider.*

- async `fetch_bars(symbol, start_date, end_date, timeframe, progress_callback)` → `list[HistoricalBar]`  *Fetch historical crypto bars from Alpaca.*
- async `is_available()` → `bool`  *Check if Alpaca crypto provider is available.*
- *...3 private methods*
- `__init__(api_key, api_secret)`  *Initialize Alpaca crypto provider.*

## `src/core/market_data/alpaca_crypto_stream.py`

### `AlpacaCryptoStreamClient(StreamClient)`
*Real-time cryptocurrency market data client for Alpaca using WebSocket.*

- async `connect()` → `bool`  *Connect to Alpaca Crypto WebSocket stream.*
- async `disconnect()`  *Disconnect from Alpaca crypto stream.*
- async `subscribe(symbols)`  *Subscribe to crypto symbols.*
- async `unsubscribe(symbols)`  *Unsubscribe from crypto symbols.*
- `get_latest_tick(symbol)` → `MarketTick | None`  *Get the latest tick for a crypto symbol.*
- `get_metrics()` → `dict`  *Get crypto stream metrics.*
- *...7 private methods*
- `__init__(api_key, api_secret, paper, buffer_size)`  *Initialize Alpaca crypto stream client.*

## `src/core/market_data/alpaca_historical_data_config.py`

### `FilterConfig(object)`
*Configuration for bad tick filtering.*


### `FilterStats(object)`
*Statistics from bad tick filtering operation.*


## `src/core/market_data/alpaca_historical_data_db.py`

### `HistoricalDataDB(object)`
*Database handler for historical data operations.*

- async `delete_symbol_data(db_symbol)` → `None`  *Delete all data for a symbol (async).*
- async `save_bars_batched(bars, db_symbol, source, batch_size)` → `None`  *Save bars to database in batches (async).*
- async `get_data_coverage(db_symbol)` → `dict | None`  *Get data coverage info for a symbol (async).*
- async `verify_data_integrity(db_symbol)` → `dict`  *Verify data integrity for a symbol (async).*
- *...4 private methods*
- `__init__(db)`  *Initialize database handler.*

## `src/core/market_data/alpaca_historical_data_manager.py`

### `AlpacaHistoricalDataManager(object)`
*Manages bulk downloading and caching of historical market data for ALPACA ONLY.*

- async `bulk_download(provider, symbols, days_back, timeframe, source, batch_size, filter_config, replace_existing, progress_callback)` → `dict[str, int]`  *Download historical data for multiple Alpaca symbols in bulk.*
- async `sync_history_to_now(provider, symbols, timeframe, source, batch_size, filter_config, progress_callback)` → `dict[str, int]`  *Sync Alpaca historical data up to now without re-downloading everything.*
- `get_last_filter_stats()` → `FilterStats | None`  *Get statistics from the last Alpaca filtering operation.*
- async `get_data_coverage(symbol, source)` → `dict`  *Get coverage information for an Alpaca symbol (delegated to DB handler).*
- async `verify_data_integrity(symbol, source, expected_timeframe)` → `dict`  *Verify Alpaca data integrity and find gaps (delegated to DB handler).*
- `__init__(filter_config)`  *Initialize the Alpaca historical data manager.*

## `src/core/market_data/alpaca_stream.py`

### `AlpacaStreamClient(StreamClient)`
*Real-time market data client for Alpaca using WebSocket.*

- async `connect()` → `bool`  *Connect to Alpaca WebSocket stream.*
- async `disconnect()`  *Disconnect from Alpaca stream.*
- async `subscribe(symbols)`  *Subscribe to symbols.*
- async `unsubscribe(symbols)`  *Unsubscribe from symbols.*
- `get_latest_tick(symbol)` → `MarketTick | None`  *Get the latest tick for a symbol.*
- async `get_latest_bar(symbol)` → `dict | None`  *Get the latest bar from Alpaca REST API.*
- `get_metrics()` → `dict`  *Get stream metrics.*
- *...7 private methods*
- `__init__(api_key, api_secret, paper, buffer_size, feed)`  *Initialize Alpaca stream client.*

## `src/core/market_data/alpha_vantage_stream.py`

### `AlphaVantageStreamClient(StreamClient)`
*Real-time market data client for Alpha Vantage using polling.*

- async `connect()` → `bool`  *Start the polling loop.*
- async `disconnect()`  *Stop the polling loop.*
- async `subscribe(symbols)`  *Subscribe to symbols.*
- async `unsubscribe(symbols)`  *Unsubscribe from symbols.*
- `get_latest_tick(symbol)` → `MarketTick | None`  *Get the latest tick for a symbol.*
- `get_metrics()` → `dict`  *Get stream metrics.*
- *...6 private methods*
- `__init__(api_key, poll_interval, buffer_size, enable_indicators)`  *Initialize Alpha Vantage stream client.*

## `src/core/market_data/bar_validator.py`

### `BarValidator(object)`
*Stateful validator for OHLCV bars.*

- `seed(symbol, close, timestamp)` → `None`  *Prime the validator with a known last close to avoid loose first-bar passes.*
- `validate_stream_bar(symbol, timestamp, open_, high, low, close, volume, extra)` → `dict[str, Any] | None`  *Validate a single bar coming from a live stream.*
- `validate_historical_bars(symbol, bars, getter, builder)` → `list[Any]`  *Validate a sequence of historical bars.*
- *...14 private methods*
- `__init__()`

## `src/core/market_data/base_bad_tick_detector.py`

### `BaseBadTickDetector(ABC, Generic[TFilterConfig, TFilterStats, TBar])`
*Base class for provider-specific bad tick detection.*

- async `filter_bad_ticks(bars, symbol)` → `tuple[list[TBar], TFilterStats]`  *Apply bad tick filtering to bars.*
- *...9 private methods*
- `__init__(config)`  *Initialize detector with configuration.*

## `src/core/market_data/base_provider.py`

### `HistoricalDataProvider(ABC)`
*Abstract base class for historical data providers with template methods.*

- async `fetch_bars(symbol, start_date, end_date, timeframe)` → `list[HistoricalBar]`  *Fetch historical bars.*
- async `is_available()` → `bool`  *Check if provider is available.*
- async `fetch_bars_with_cache(symbol, start_date, end_date, timeframe)` → `list[HistoricalBar]`  *Fetch bars with caching support (template method).*
- *...5 private methods*
- `__init__(name, enable_cache)`  *Initialize provider.*

## `src/core/market_data/bitunix_bad_tick_detector.py`

### `BadTickDetector(BaseBadTickDetector[FilterConfig, FilterStats, HistoricalBar])`
*Bitunix-specific bad tick detector.*

- *...3 private methods*

## `src/core/market_data/bitunix_historical_data_config.py`

### `FilterConfig(object)`
*Configuration for bad tick filtering.*


### `FilterStats(object)`
*Statistics from bad tick filtering operation.*


## `src/core/market_data/bitunix_historical_data_db.py`

### `HistoricalDataDB(object)`
*Database handler for historical data operations.*

- async `delete_symbol_data(db_symbol)` → `int`  *Delete all data for a symbol (async).*
- async `save_bars_batched(bars, db_symbol, source, batch_size)` → `None`  *Save bars to database in batches (async).*
- async `get_data_coverage(db_symbol)` → `dict | None`  *Get data coverage info for a symbol (async).*
- async `verify_data_integrity(db_symbol)` → `dict`  *Verify data integrity for a symbol (async).*
- *...4 private methods*
- `__init__(db)`  *Initialize database handler.*

## `src/core/market_data/bitunix_historical_data_manager.py`

### `BitunixHistoricalDataManager(object)`
*Manages bulk downloading and caching of historical market data for BITUNIX ONLY.*

- async `bulk_download(provider, symbols, days_back, timeframe, source, batch_size, filter_config, replace_existing, progress_callback)` → `dict[str, int]`  *Download historical data for multiple Bitunix symbols in bulk.*
- async `sync_history_to_now(provider, symbols, timeframe, source, batch_size, filter_config, progress_callback)` → `dict[str, int]`  *Sync Bitunix historical data up to now without re-downloading everything.*
- `get_last_filter_stats()` → `FilterStats | None`  *Get statistics from the last Bitunix filtering operation.*
- async `get_data_coverage(symbol, source)` → `dict`  *Get coverage information for a Bitunix symbol (delegated to DB handler).*
- async `verify_data_integrity(symbol, source, expected_timeframe)` → `dict`  *Verify Bitunix data integrity and find gaps (delegated to DB handler).*
- `__init__(filter_config)`  *Initialize the Bitunix historical data manager.*

## `src/core/market_data/bitunix_stream.py`

### `BitunixStreamClient(StreamClient)`
*Bitunix WebSocket stream client for real-time market data (REFACTORED).*

- async `connect()` → `bool`  *Establish WebSocket connection via supervisor task.*
- async `disconnect()` → `None`  *Disconnect from Bitunix WebSocket and stop supervisor.*
- `get_latest_tick(symbol)` → `MarketTick | None`  *Get latest tick for symbol.*
- `get_metrics()` → `dict`  *Get stream metrics.*
- *...4 private methods*
- `__init__(use_testnet, buffer_size, heartbeat_interval, reconnect_attempts, max_lag_ms)`  *Initialize Bitunix stream client.*

## `src/core/market_data/bitunix_stream_connection.py`

### `BitunixStreamConnection(object)`
*Helper für BitunixStreamClient connection lifecycle.*

- async `connect()` → `bool`  *Establish WebSocket connection via supervisor task.*
- async `disconnect()` → `None`  *Disconnect from Bitunix WebSocket and stop supervisor.*
- *...4 private methods*
- `__init__(parent)`  *Args:*

## `src/core/market_data/bitunix_stream_handlers.py`

### `BitunixStreamHandlers(object)`
*Helper für BitunixStreamClient channel handlers.*

- async `handle_ticker(data)` → `None`  *Handle ticker updates.*
- async `handle_kline(data)` → `None`  *Handle kline (candlestick) updates.*
- async `handle_depth(data)` → `None`  *Handle order book depth updates.*
- async `handle_trade(data)` → `None`  *Handle trade feed updates.*
- `__init__(parent)`  *Args:*

## `src/core/market_data/bitunix_stream_messages.py`

### `BitunixStreamMessages(object)`
*Helper für BitunixStreamClient message processing.*

- async `on_message(message)` → `None`  *Parse and handle incoming WebSocket messages.*
- `__init__(parent)`  *Args:*

## `src/core/market_data/bitunix_stream_subscription.py`

### `BitunixStreamSubscription(object)`
*Helper für BitunixStreamClient subscription management.*

- @staticmethod `normalize_symbol(symbol)` → `str`  *Normalize symbols to Bitunix format (uppercase, no separators).*
- `build_subscription_args(symbols)` → `list[dict[str, str]]`  *Build subscription args for ticker + 1m kline channels.*
- async `handle_subscription(symbols)` → `None`  *Send subscription request for given symbols.*
- async `handle_unsubscription(symbols)` → `None`  *Send unsubscription request for given symbols.*
- `__init__(parent)`  *Args:*

## `src/core/market_data/errors.py`

### `MarketDataAccessBlocked(Exception)`
*Raised when a market data endpoint blocks access (e.g., 403/Cloudflare).*

- `details()` → `str`  *Return a human-readable detail string.*
- `__init__(provider, status_code, reason, body_snippet)`

## `src/core/market_data/history_provider.py`

### `HistoryManager(object)`
*Manager for historical data with fallback support.*

- `register_provider(source, provider)` → `None`  *Register a data provider.*
- `set_ibkr_adapter(adapter)` → `None`  *Register or update the IBKR provider on-demand.*
- async `fetch_data(request)` → `tuple[list[HistoricalBar], str]`  *Fetch historical data with fallback.*
- async `get_latest_price(symbol)` → `Decimal | None`  *Get latest price for symbol.*
- `get_available_sources()` → `list[str]`  *Get list of available data sources.*
- async `start_realtime_stream(symbols, enable_indicators)` → `bool`  *Start real-time market data streaming.*
- async `stop_realtime_stream()`  *Stop real-time market data streaming.*
- async `start_crypto_realtime_stream(crypto_symbols)` → `bool`  *Start real-time cryptocurrency market data streaming.*
- async `stop_crypto_realtime_stream()`  *Stop real-time cryptocurrency market data streaming.*
- async `start_bitunix_stream(bitunix_symbols)` → `bool`  *Start real-time Bitunix WebSocket streaming for crypto futures.*
- async `stop_bitunix_stream()`  *Stop real-time Bitunix WebSocket streaming.*
- `get_realtime_tick(symbol)`  *Get latest real-time tick for a symbol.*
- `get_stream_metrics()` → `dict | None`  *Get real-time stream metrics.*
- async `fetch_realtime_indicators(symbol, interval)` → `dict`  *Fetch real-time technical indicators.*
- async `get_historical_data(symbol, timeframe, limit)`  *Convenience method to get historical data as DataFrame.*
- `__init__(ibkr_adapter)`  *Initialize history manager.*

## `src/core/market_data/history_provider_config.py`

### `HistoryProviderConfig(object)`
*Helper für HistoryManager Config (Priority, Provider Initialization).*

- `configure_priority()` → `None`  *Configure provider priority order from settings.*
- `initialize_providers_from_config(ibkr_adapter)` → `None`  *Register providers according to configuration and credentials.*
- `__init__(parent)`  *Args:*

## `src/core/market_data/history_provider_fetching.py`

### `HistoryProviderFetching(object)`
*Helper für HistoryManager Fetching (Data Fetch, Fallback, Caching).*

- async `fetch_data(request)` → `tuple[list[HistoricalBar], str]`  *Fetch historical data with fallback.*
- async `get_latest_price(symbol)` → `Decimal | None`  *Get latest price for symbol.*
- `get_available_sources()` → `list[str]`  *Get list of available data sources.*
- *...6 private methods*
- `__init__(parent)`  *Args:*

## `src/core/market_data/history_provider_streaming.py`

### `HistoryProviderStreaming(object)`
*Helper für HistoryManager Streaming (Stock, Crypto, Bitunix).*

- async `start_realtime_stream(symbols, enable_indicators)` → `bool`  *Start real-time market data streaming.*
- async `stop_realtime_stream()`  *Stop real-time market data streaming.*
- async `start_crypto_realtime_stream(crypto_symbols)` → `bool`  *Start real-time cryptocurrency market data streaming.*
- async `stop_crypto_realtime_stream()`  *Stop real-time cryptocurrency market data streaming.*
- async `start_bitunix_stream(bitunix_symbols)` → `bool`  *Start real-time Bitunix WebSocket streaming for crypto futures.*
- async `stop_bitunix_stream()`  *Stop real-time Bitunix WebSocket streaming.*
- `get_realtime_tick(symbol)`  *Get latest real-time tick for a symbol.*
- `get_stream_metrics()` → `dict | None`  *Get real-time stream metrics.*
- async `fetch_realtime_indicators(symbol, interval)` → `dict`  *Fetch real-time technical indicators.*
- `__init__(parent)`  *Args:*

## `src/core/market_data/market_hours.py`

### `MarketSession(object)`
*Represents a market trading session.*

- @property `tz()`
- `is_active(current_dt)` → `bool`  *Check if session is currently active.*
- `time_until_open(current_dt)` → `timedelta`  *Time until next open.*
- `time_until_close(current_dt)` → `timedelta`  *Time until close (if active).*

### Module Functions
- `get_active_sessions(current_dt)` → `List[MarketSession]`  *Get list of currently active sessions.*
- `get_next_event(current_dt)` → `str`  *Get description of next major event.*

## `src/core/market_data/providers/alpaca_stock_provider.py`

### `AlpacaProvider(HistoricalDataProvider)`
*Alpaca historical data provider for stocks.*

- async `fetch_bars(symbol, start_date, end_date, timeframe)` → `list[HistoricalBar]`  *Fetch historical bars from Alpaca.*
- async `is_available()` → `bool`  *Check if Alpaca is available.*
- *...2 private methods*
- `__init__(api_key, api_secret)`  *Initialize Alpaca provider.*

## `src/core/market_data/providers/alpha_vantage_provider.py`

### `AlphaVantageProvider(HistoricalDataProvider)`
*Alpha Vantage historical data provider.*

- async `fetch_bars(symbol, start_date, end_date, timeframe)` → `list[HistoricalBar]`  *Fetch historical bars from Alpha Vantage.*
- async `is_available()` → `bool`  *Check if Alpha Vantage is available.*
- async `fetch_technical_indicator(symbol, indicator, interval, time_period, series_type)` → `dict`  *Fetch technical indicator from Alpha Vantage.*
- async `fetch_rsi(symbol, interval, time_period, series_type)` → `pd.Series`  *Fetch RSI (Relative Strength Index) from Alpha Vantage.*
- async `fetch_macd(symbol, interval, fast_period, slow_period, signal_period, series_type)` → `pd.DataFrame`  *Fetch MACD from Alpha Vantage.*
- *...1 private methods*
- `__init__(api_key)`  *Initialize Alpha Vantage provider.*

## `src/core/market_data/providers/base.py`

### `HistoricalDataProvider(ABC)`
*Abstract base class for historical data providers with template methods.*

- async `fetch_bars(symbol, start_date, end_date, timeframe)` → `list[HistoricalBar]`  *Fetch historical bars.*
- async `is_available()` → `bool`  *Check if provider is available.*
- async `fetch_bars_with_cache(symbol, start_date, end_date, timeframe)` → `list[HistoricalBar]`  *Fetch bars with caching support (template method).*
- *...5 private methods*
- `__init__(name, enable_cache)`  *Initialize provider.*

## `src/core/market_data/providers/bitunix_provider.py`

### `BitunixProvider(HistoricalDataProvider)`
*Bitunix Futures historical data provider.*

- async `fetch_bars(symbol, start_date, end_date, timeframe, progress_callback)` → `list[HistoricalBar]`  *Fetch historical klines from Bitunix.*
- async `is_available()` → `bool`  *Check if Bitunix provider is available.*
- *...6 private methods*
- `__init__(api_key, api_secret, use_testnet, enable_cache, max_bars, max_batches, validate_ohlc)`  *Initialize Bitunix provider.*

## `src/core/market_data/providers/database_provider.py`

### `DatabaseProvider(HistoricalDataProvider)`
*Database historical data provider (local cache).*

- async `fetch_bars(symbol, start_date, end_date, timeframe)` → `list[HistoricalBar]`  *Fetch historical bars from database.*
- async `is_available()` → `bool`  *Check if database is available.*
- *...2 private methods*
- `__init__()`  *Initialize database provider.*

## `src/core/market_data/providers/finnhub_provider.py`

### `FinnhubProvider(HistoricalDataProvider)`
*Finnhub historical data provider.*

- async `fetch_bars(symbol, start_date, end_date, timeframe)` → `list[HistoricalBar]`  *Fetch historical bars from Finnhub.*
- async `is_available()` → `bool`  *Check if Finnhub is available.*
- *...1 private methods*
- `__init__(api_key)`  *Initialize Finnhub provider.*

## `src/core/market_data/providers/ibkr_provider.py`

### `IBKRHistoricalProvider(HistoricalDataProvider)`
*IBKR historical data provider.*

- async `fetch_bars(symbol, start_date, end_date, timeframe)` → `list[HistoricalBar]`  *Fetch historical bars from IBKR.*
- async `is_available()` → `bool`  *Check if IBKR is available.*
- *...2 private methods*
- `__init__(ibkr_adapter)`  *Initialize IBKR provider.*

## `src/core/market_data/providers/yahoo_provider.py`

### `YahooFinanceProvider(HistoricalDataProvider)`
*Yahoo Finance historical data provider.*

- async `fetch_bars(symbol, start_date, end_date, timeframe)` → `list[HistoricalBar]`  *Fetch historical bars from Yahoo Finance.*
- async `is_available()` → `bool`  *Yahoo Finance is always available (no API key required).*
- *...8 private methods*
- `__init__()`

## `src/core/market_data/resampler.py`

### `OHLCV(object)`
*OHLC data with volume.*


### `NoiseFilter(object)`
*Base class for noise filters.*

- `filter(values)` → `Decimal`  *Apply filter to values.*

### `MedianFilter(NoiseFilter)`
*Median filter for noise reduction.*

- `filter(values)` → `Decimal`  *Apply median filter.*
- `__init__(window_size)`  *Initialize median filter.*

### `MovingAverageFilter(NoiseFilter)`
*Moving average filter for noise reduction.*

- `filter(values)` → `Decimal`  *Apply moving average filter.*
- `__init__(window_size, alpha)`  *Initialize MA filter.*

### `KalmanFilter(NoiseFilter)`
*Kalman filter for advanced noise reduction.*

- `filter(values)` → `Decimal`  *Apply Kalman filter.*
- `__init__(process_variance, measurement_variance)`  *Initialize Kalman filter.*

### `MarketDataResampler(object)`
*Resamples market data to specified intervals with noise reduction.*

- `add_tick(symbol, price, volume, timestamp)` → `OHLCV | None`  *Add a tick and return resampled bar if ready.*
- `get_bars(symbol, count)` → `list[OHLCV]`  *Get recent bars for symbol.*
- `get_latest_bar(symbol)` → `OHLCV | None`  *Get latest bar for symbol.*
- `resample_dataframe(df, interval)` → `pd.DataFrame`  *Resample a DataFrame of tick data.*
- `detect_anomalies(symbol, threshold)` → `list[datetime]`  *Detect anomalous price movements.*
- `get_statistics(symbol)` → `dict[str, float]`  *Get statistics for symbol.*
- *...3 private methods*
- `__init__(resample_interval, filter_type, filter_window, buffer_size)`  *Initialize resampler.*

## `src/core/market_data/stream_client.py`

### `StreamStatus(Enum)`
*Stream connection status.*


### `StreamMetrics(object)`
*Metrics for stream performance.*

- `update_latency(latency_ms)`  *Update average latency.*

### `MarketTick(object)`
*Market data tick.*


### `StreamClient(object)`
*Base class for market data stream clients.*

- async `connect()` → `None`  *Connect to data stream.*
- async `disconnect()` → `None`  *Disconnect from data stream.*
- async `subscribe(symbols, callback)` → `None`  *Subscribe to market data for symbols.*
- async `unsubscribe(symbols)` → `None`  *Unsubscribe from market data.*
- `process_tick(tick)` → `None`  *Process incoming market tick.*
- `get_latest_tick(symbol)` → `MarketTick | None`  *Get latest tick for symbol.*
- `get_metrics()` → `dict[str, Any]`  *Get stream metrics.*
- *...10 private methods*
- `__init__(name, buffer_size, heartbeat_interval, reconnect_attempts, max_lag_ms)`  *Initialize stream client.*

### `IBKRStreamClient(StreamClient)`
*IBKR-specific stream client implementation.*

- async `connect()` → `None`  *Connect to IBKR data stream.*
- *...2 private methods*
- `__init__(ibkr_client)`  *Initialize IBKR stream client.*

### `TradeRepublicStreamClient(StreamClient)`
*Trade Republic-specific stream client implementation.*

- async `connect()` → `None`  *Connect to Trade Republic data stream.*
- *...4 private methods*
- `__init__(ws_connection)`  *Initialize Trade Republic stream client.*

## `src/core/market_data/types.py`

### `AssetClass(Enum)`
*Asset class types supported by the platform.*


### `DataSource(Enum)`
*Available data sources.*


### `Timeframe(Enum)`
*Market data timeframes.*


### `HistoricalBar(object)`
*Historical market bar data.*


### `DataRequest(object)`
*Request for historical data.*


### Module Functions
- `format_symbol_with_source(symbol, source)` → `str`  *Return symbol without prefix (source is stored in separate 'source' column).*
- `parse_symbol_with_source(formatted_symbol)` → `tuple[str, str]`  *Parse symbol and extract source prefix if present.*

## `src/core/models/backtest_models.py`

### `TradeSide(str, Enum)`
*Trade direction.*


### `Bar(BaseModel)`
*OHLCV bar data.*


### `Trade(BaseModel)`
*Represents a completed or active trade.*

- @property `duration()` → `float | None`  *Trade duration in seconds.*
- @property `r_multiple()` → `float | None`  *Risk-reward multiple (R-multiple).*
- @property `is_winner()` → `bool`  *Check if trade was profitable.*

### `EquityPoint(BaseModel)`
*Point on the equity curve.*


### `BacktestMetrics(BaseModel)`
*Comprehensive backtest performance metrics.*

- @property `recovery_factor()` → `float | None`  *Recovery factor: Net profit / Max drawdown.*

### `BacktestResult(BaseModel)`
*Complete backtest result with all data and metrics.*

- @property `duration_days()` → `float`  *Backtest duration in days.*
- @property `total_pnl()` → `float`  *Total profit/loss.*
- @property `total_pnl_pct()` → `float`  *Total return percentage.*

### Module Functions
- `from_historical_bar(bar, symbol)` → `Bar`  *Convert HistoricalBar (from market_data.types) to Bar.*
- `to_historical_bars(bars, symbol)` → `list['HistoricalBar']`  *Convert Bar list to HistoricalBar list.*

## `src/core/notifications/telegram_service.py`

### `TelegramService(object)`
*Service zum Senden von Telegram-Nachrichten.*

- @property `bot_token()` → `str`
- `bot_token(value)` → `None`
- @property `chat_id()` → `str`
- `chat_id(value)` → `None`
- @property `enabled()` → `bool`
- `enabled(value)` → `None`
- @property `is_available()` → `bool`
- @property `is_configured()` → `bool`  *Prüft ob Bot-Token und Chat-ID konfiguriert sind.*
- `set_status_callback(callback)` → `None`  *Setzt Callback für Status-Updates.*
- `set_error_callback(callback)` → `None`  *Setzt Callback für Fehler.*
- `send_message(message, chat_id)` → `bool`  *Sendet eine Telegram-Nachricht.*
- `send_trade_notification(notification)` → `bool`  *Sendet eine Trade-Benachrichtigung.*
- `notify_position_opened(symbol, side, quantity, entry_price, leverage)` → `bool`  *Sendet Benachrichtigung bei Position-Eröffnung.*
- `notify_position_closed(symbol, side, quantity, entry_price, exit_price, pnl, pnl_percent, reason)` → `bool`  *Sendet Benachrichtigung bei Position-Schließung.*
- *...4 private methods*
- `__init__(bot_token, chat_id)`

### Module Functions
- `get_telegram_service()` → `TelegramService`  *Gibt die Singleton-Instanz des Telegram-Service zurück.*

## `src/core/notifications/whatsapp_service.py`

### `TradeNotification(object)`
*Datenstruktur für Trade-Benachrichtigungen.*

- `format_message()` → `str`  *Formatiert die Benachrichtigung als WhatsApp-Nachricht.*

### `WhatsAppService(object)`
*Service zum Senden von WhatsApp-Nachrichten.*

- @property `phone_number()` → `str`
- `phone_number(value)` → `None`
- @property `enabled()` → `bool`
- `enabled(value)` → `None`
- @property `is_available()` → `bool`
- `set_status_callback(callback)` → `None`  *Setzt Callback für Status-Updates.*
- `set_error_callback(callback)` → `None`  *Setzt Callback für Fehler.*
- `send_message(message, phone_number)` → `bool`  *Sendet eine WhatsApp-Nachricht.*
- `send_trade_notification(notification)` → `bool`  *Sendet eine Trade-Benachrichtigung.*
- `notify_position_opened(symbol, side, quantity, entry_price, leverage)` → `bool`  *Sendet Benachrichtigung bei Position-Eröffnung.*
- `notify_position_closed(symbol, side, quantity, entry_price, exit_price, pnl, pnl_percent, reason)` → `bool`  *Sendet Benachrichtigung bei Position-Schließung.*
- *...4 private methods*
- `__init__(phone_number)`

### Module Functions
- `get_whatsapp_service()` → `WhatsAppService`  *Gibt die Singleton-Instanz des WhatsApp-Service zurück.*

## `src/core/pattern_db/embedder.py`

### `PatternEmbedder(object)`
*Converts trading patterns to vector embeddings.*

- `embed(pattern)` → `np.ndarray`  *Convert pattern to vector embedding.*
- `embed_batch(patterns)` → `np.ndarray`  *Embed multiple patterns.*
- `get_embedding_dim()` → `int`  *Get embedding dimension.*
- *...11 private methods*
- `__init__(window_size, include_volume)`  *Initialize embedder.*

## `src/core/pattern_db/extractor.py`

### `Pattern(object)`
*A trading pattern extracted from OHLC data.*

- `to_dict()` → `dict`  *Convert pattern to dictionary for storage.*

### `PatternExtractor(object)`
*Extracts trading patterns from OHLC data using sliding windows.*

- `extract_patterns(bars, symbol, timeframe)` → `Iterator[Pattern]`  *Extract patterns from a list of bars.*
- `extract_current_pattern(bars, symbol, timeframe)` → `Pattern | None`  *Extract the most recent pattern (for live matching).*
- *...9 private methods*
- `__init__(window_size, step_size, outcome_bars, min_volatility)`  *Initialize pattern extractor.*

## `src/core/pattern_db/fetcher.py`

### `FetchConfig(object)`
*Configuration for data fetching.*


### `PatternDataFetcher(object)`
*Fetches historical data for pattern database construction.*

- `get_default_stock_config(days_back)` → `FetchConfig`  *Get default config for NASDAQ-100 stocks.*
- `get_default_crypto_config(days_back)` → `FetchConfig`  *Get default config for crypto (BTC, ETH).*
- async `fetch_symbol_data(symbol, timeframe, days_back, asset_class)` → `list[HistoricalBar]`  *Fetch historical data for a single symbol.*
- async `fetch_batch(config, progress_callback)` → `AsyncIterator[tuple[str, Timeframe, list[HistoricalBar]]]`  *Fetch data for multiple symbols with progress tracking.*
- async `fetch_all(config, progress_callback)` → `dict[str, dict[str, list[HistoricalBar]]]`  *Fetch all data according to config.*
- *...1 private methods*
- `__init__()`  *Initialize the fetcher.*

### Module Functions
- `resolve_symbol(symbol, asset_class)` → `str`  *Resolve symbol to a provider-supported proxy when needed.*
- async `fetch_daytrading_data(include_stocks, include_crypto, days_back, progress_callback)` → `dict[str, dict[str, list[HistoricalBar]]]`  *Fetch all daytrading data for pattern database.*

## `src/core/pattern_db/gap_detector.py`

### `DataGap(object)`
*Represents a data gap that needs to be filled.*

- @property `duration_hours()` → `float`  *Return gap duration in hours.*
- @property `duration_minutes()` → `int`  *Return gap duration in minutes.*

### `GapDetector(object)`
*Detects data gaps in pattern database for incremental updates.*

- async `initialize()` → `bool`  *Initialize Qdrant connection.*
- async `detect_gaps(symbol, timeframe, max_history_days)` → `list[DataGap]`  *Detect all data gaps for a symbol/timeframe combination.*
- async `get_latest_pattern_time(symbol, timeframe)` → `datetime | None`  *Get timestamp of latest pattern in database.*
- async `needs_update(symbol, timeframe, threshold_minutes)` → `bool`  *Check if database needs update (quick check).*
- *...4 private methods*
- `__init__(db)`  *Initialize gap detector.*

## `src/core/pattern_db/gap_filler.py`

### `GapFiller(object)`
*Fills data gaps in pattern database using Bitunix API.*

- async `initialize()` → `bool`  *Initialize database connection.*
- async `fill_gap(gap, progress_callback)` → `int`  *Fill a single data gap.*
- async `fill_all_gaps(symbol, timeframe, max_history_days, progress_callback)` → `int`  *Detect and fill all gaps for a symbol/timeframe.*
- async `update_to_now(symbol, timeframe, progress_callback)` → `int`  *Quick update: Fill gap from latest pattern to now.*
- async `estimate_fill_time(gap)` → `tuple[int, str]`  *Estimate time required to fill a gap.*
- *...1 private methods*
- `__init__(provider, extractor, db)`  *Initialize gap filler.*

## `src/core/pattern_db/partial_matcher.py`

### `PartialPatternAnalysis(object)`
*Analysis result from partial pattern matching.*


### `PartialPatternMatcher(object)`
*Matches partial/incomplete patterns against completed historical patterns.*

- async `initialize()` → `bool`  *Initialize database connection.*
- async `analyze_partial_signal(bars, symbol, timeframe, signal_direction, cross_symbol_search, similarity_threshold)` → `Optional[PartialPatternAnalysis]`  *Analyze a trading signal using partial pattern matching.*
- *...6 private methods*
- `__init__(full_window_size, min_bars_required, confidence_penalty_alpha, projection_method)`  *Initialize partial pattern matcher.*

## `src/core/pattern_db/pattern_service.py`

### `PatternAnalysis(object)`
*Analysis result from pattern matching.*


### `PatternService(object)`
*Service for pattern-based signal validation.*

- async `initialize()` → `bool`  *Initialize the service (connect to Qdrant).*
- async `analyze_signal(bars, symbol, timeframe, signal_direction, cross_symbol_search, target_timeframe)` → `Optional[PatternAnalysis]`  *Analyze a trading signal using pattern matching.*
- async `get_quick_validation(bars, symbol, timeframe, signal_direction)` → `tuple[float, str]`  *Quick validation returning just boost and recommendation.*
- async `analyze_partial_signal(bars, symbol, timeframe, signal_direction, cross_symbol_search, target_timeframe)` → `Optional[PartialPatternAnalysis]`  *Analyze a signal using partial pattern matching (Phase 3).*
- *...1 private methods*
- `__init__(window_size, min_similar_patterns, min_win_rate_boost, similarity_threshold)`  *Initialize pattern service.*

### Module Functions
- async `get_pattern_service()` → `PatternService`  *Get or create the global pattern service instance.*

## `src/core/pattern_db/pattern_update_worker.py`

### `PatternUpdateWorker(QThread)`
*Background worker for automatic pattern database updates.*

- `run()`  *Main worker loop - runs in background thread.*
- `stop()`  *Stop the worker gracefully.*
- `pause()`  *Pause gap scanning (worker keeps running).*
- `resume()`  *Resume gap scanning.*
- `trigger_immediate_scan()`  *Trigger immediate gap scan (doesn't wait for interval).*
- *...4 private methods*
- `__init__(symbols, timeframes, scan_interval, max_history_days)`  *Initialize pattern update worker.*

### `PatternUpdateManager(object)`
*Manager for Pattern Update Worker lifecycle.*

- `start(symbols, timeframes, scan_interval)` → `bool`  *Start pattern update worker.*
- `stop()`  *Stop pattern update worker.*
- `pause()`  *Pause worker (keeps thread running).*
- `resume()`  *Resume worker.*
- `trigger_scan()`  *Trigger immediate scan.*
- *...2 private methods*
- `__init__()`  *Initialize manager.*

## `src/core/pattern_db/qdrant_client.py`

### `PatternMatch(object)`
*A matched pattern from similarity search.*


### `TradingPatternDB(object)`
*Qdrant-based trading pattern database.*

- `get_last_error()` → `str | None`  *Return last connection error (if any).*
- async `initialize()` → `bool`  *Initialize the collection if it doesn't exist.*
- async `insert_pattern(pattern)` → `str`  *Insert a single pattern into the database.*
- async `insert_patterns_batch(patterns, batch_size, progress_callback)` → `int`  *Insert multiple patterns in batches.*
- async `search_similar(pattern, limit, symbol_filter, timeframe_filter, trend_filter, outcome_filter, score_threshold)` → `list[PatternMatch]`  *Search for similar patterns.*
- async `get_pattern_statistics(matches)` → `dict`  *Calculate statistics from matched patterns.*
- async `get_collection_info()` → `dict`  *Get information about the collection.*
- async `delete_collection()` → `bool`  *Delete the entire collection.*
- *...2 private methods*
- `__init__(host, port, collection_name, embedding_dim)`  *Initialize Qdrant client.*

## `src/core/pattern_db/timeframe_converter.py`

### `TimeframeConverter(object)`
*Converts bars between different timeframes.*

- @classmethod `resample_bars(bars, from_timeframe, to_timeframe)` → `List[HistoricalBar]`  *Resample bars from one timeframe to another.*
- @classmethod `can_convert(from_timeframe, to_timeframe)` → `tuple[bool, str]`  *Check if conversion is possible.*
- @classmethod `get_supported_conversions(from_timeframe)` → `List[str]`  *Get list of supported target timeframes for given source.*
- @classmethod `estimate_bar_count(source_bar_count, from_timeframe, to_timeframe)` → `int`  *Estimate resulting bar count after resampling.*
- *...2 private methods*

### Module Functions
- `resample_to_5min(bars_1min)` → `List[HistoricalBar]`  *Quick helper: Resample 1min bars to 5min.*
- `resample_to_15min(bars_1min)` → `List[HistoricalBar]`  *Quick helper: Resample 1min bars to 15min.*
- `resample_to_1hour(bars_1min)` → `List[HistoricalBar]`  *Quick helper: Resample 1min bars to 1hour.*

## `src/core/regime_optimizer.py`

### `RegimeType(str, Enum)`
*Regime types for classification.*


### `OptimizationMode(str, Enum)`
*Optimization execution modes.*


### `OptimizationMethod(str, Enum)`
*Optimization methods.*


### `PrunerType(str, Enum)`
*Early stopping pruner types.*


### `ParamRange(BaseModel)`
*Parameter range for optimization.*


### `ADXParamRanges(BaseModel)`
*ADX parameter ranges for trend strength and direction detection.*

- *...1 private methods*

### `RSIParamRanges(BaseModel)`
*RSI parameter ranges.*


### `ATRParamRanges(BaseModel)`
*ATR parameter ranges for volatility-based moves.*


### `SMAParamRanges(BaseModel)`
*SMA parameter ranges (simple mode).*


### `BBParamRanges(BaseModel)`
*Bollinger Band parameter ranges (simple mode).*


### `AllParamRanges(BaseModel)`
*All parameter ranges for Stage 1 (ADX/DI-based regime detection).*


### `EarlyStoppingConfig(BaseModel)`
*Early stopping configuration.*


### `OptimizationConfig(BaseModel)`
*Optimization configuration.*

- @classmethod `validate_max_trials(v, info)` → `int`  *Validate max_trials based on mode.*

### `RegimeParams(BaseModel)`
*Optimized regime detection parameters (ADX/DI-based like original).*

- *...1 private methods*

### `RegimeMetrics(BaseModel)`
*Metrics for a regime optimization result.*


### `OptimizationResult(BaseModel)`
*Single optimization trial result.*


### `RegimePeriod(BaseModel)`
*Regime period for bar index tracking.*

- @classmethod `validate_bars(v, info)` → `int`  *Validate bars matches indices.*

### `RegimeOptimizer(object)`
*Regime detection parameter optimizer using Optuna TPE.*

- `optimize(study_name, n_trials, callbacks)` → `list[OptimizationResult]`  *Run optimization.*
- `get_best_regime_periods()` → `list[RegimePeriod]`  *Get regime periods for best parameters.*
- `export_results(results, output_path)` → `None`  *Export results to JSON file.*
- *...20 private methods*
- `__post_init__()`  *Validate data and setup storage.*

## `src/core/regime_optimizer_BACKUP.py`

### `RegimeType(str, Enum)`
*Regime types for classification.*


### `OptimizationMode(str, Enum)`
*Optimization execution modes.*


### `OptimizationMethod(str, Enum)`
*Optimization methods.*


### `PrunerType(str, Enum)`
*Early stopping pruner types.*


### `ParamRange(BaseModel)`
*Parameter range for optimization.*


### `ADXParamRanges(BaseModel)`
*ADX parameter ranges for trend strength and direction detection.*

- *...1 private methods*

### `RSIParamRanges(BaseModel)`
*RSI parameter ranges.*


### `ATRParamRanges(BaseModel)`
*ATR parameter ranges for volatility-based moves.*


### `SMAParamRanges(BaseModel)`
*SMA parameter ranges (simple mode).*


### `BBParamRanges(BaseModel)`
*Bollinger Band parameter ranges (simple mode).*


### `AllParamRanges(BaseModel)`
*All parameter ranges for Stage 1 (ADX/DI-based regime detection).*


### `EarlyStoppingConfig(BaseModel)`
*Early stopping configuration.*


### `OptimizationConfig(BaseModel)`
*Optimization configuration.*

- @classmethod `validate_max_trials(v, info)` → `int`  *Validate max_trials based on mode.*

### `RegimeParams(BaseModel)`
*Optimized regime detection parameters (ADX/DI-based like original).*

- *...1 private methods*

### `RegimeMetrics(BaseModel)`
*Metrics for a regime optimization result.*


### `OptimizationResult(BaseModel)`
*Single optimization trial result.*


### `RegimePeriod(BaseModel)`
*Regime period for bar index tracking.*

- @classmethod `validate_bars(v, info)` → `int`  *Validate bars matches indices.*

### `RegimeOptimizer(object)`
*Regime detection parameter optimizer using Optuna TPE.*

- `optimize(study_name, n_trials, callbacks)` → `list[OptimizationResult]`  *Run optimization.*
- `get_best_regime_periods()` → `list[RegimePeriod]`  *Get regime periods for best parameters.*
- `export_results(results, output_path)` → `None`  *Export results to JSON file.*
- *...20 private methods*
- `__post_init__()`  *Validate data and setup storage.*

## `src/core/regime_optimizer_core.py`

### `RegimeType(str, Enum)`
*Regime types for classification.*


### `OptimizationMode(str, Enum)`
*Optimization execution modes.*


### `OptimizationMethod(str, Enum)`
*Optimization methods.*


### `PrunerType(str, Enum)`
*Early stopping pruner types.*


### `ParamRange(BaseModel)`
*Parameter range for optimization.*


### `ADXParamRanges(BaseModel)`
*ADX parameter ranges for trend strength and direction detection.*

- *...1 private methods*

### `RSIParamRanges(BaseModel)`
*RSI parameter ranges.*


### `ATRParamRanges(BaseModel)`
*ATR parameter ranges for volatility-based moves.*


### `SMAParamRanges(BaseModel)`
*SMA parameter ranges (simple mode).*


### `BBParamRanges(BaseModel)`
*Bollinger Band parameter ranges (simple mode).*


### `AllParamRanges(BaseModel)`
*All parameter ranges for Stage 1 (ADX/DI-based regime detection).*


### `EarlyStoppingConfig(BaseModel)`
*Early stopping configuration.*


### `OptimizationConfig(BaseModel)`
*Optimization configuration.*

- @classmethod `validate_max_trials(v, info)` → `int`  *Validate max_trials based on mode.*

### `RegimeParams(BaseModel)`
*Optimized regime detection parameters (ADX/DI-based like original).*

- *...1 private methods*

### `RegimeMetrics(BaseModel)`
*Metrics for a regime optimization result.*


### `OptimizationResult(BaseModel)`
*Single optimization trial result.*


### `RegimePeriod(BaseModel)`
*Regime period for bar index tracking.*

- @classmethod `validate_bars(v, info)` → `int`  *Validate bars matches indices.*

### `RegimeOptimizer(object)`
*Regime detection parameter optimizer using Optuna TPE.*

- `optimize(study_name, n_trials, callbacks)` → `list[OptimizationResult]`  *Run optimization.*
- `get_best_regime_periods()` → `list[RegimePeriod]`  *Get regime periods for best parameters.*
- `export_results(results, output_path)` → `None`  *Export results to JSON file.*
- *...3 private methods*
- `__post_init__()`  *Validate data and setup storage.*

## `src/core/regime_results_manager.py`

### `RegimeResult(object)`
*Single regime optimization result.*

- `to_dict()` → `dict[str, Any]`  *Convert to dictionary format matching schema.*
- @classmethod `from_dict(data)` → `RegimeResult`  *Create from dictionary.*
- `__init__(score, params, metrics, timestamp, rank, selected, exported)`  *Initialize regime result.*

### `RegimeResultsManager(object)`
*Manages regime optimization results (Stufe 1).*

- `add_result(score, params, metrics, timestamp)` → `RegimeResult`  *Add optimization result.*
- `rank_results()` → `None`  *Sort results by score (descending) and assign ranks.*
- `select_result(rank)` → `RegimeResult`  *Select a result by rank.*
- `get_selected_result()` → `RegimeResult | None`  *Get currently selected result.*
- `export_optimization_results(output_path, meta, optimization_config, param_ranges, validate)` → `Path`  *Export all optimization results to JSON.*
- `export_optimized_regime(output_path, symbol, timeframe, bars, data_range, regime_periods, validate)` → `Path`  *Export selected regime configuration.*
- `load_optimization_results(input_path, validate)` → `dict[str, Any]`  *Load optimization results from JSON file.*
- `get_statistics()` → `dict[str, Any]`  *Get statistics about current results.*
- `clear()` → `None`  *Clear all results.*
- *...2 private methods*
- `__init__(schemas_dir)`  *Initialize results manager.*

## `src/core/scoring/regime_score.py`

### `RegimeScoreConfig(object)`
*Configuration for Regime Scoring System.*

- @classmethod `from_json_config(json_config)` → `'RegimeScoreConfig'`  *Create RegimeScoreConfig from JSON v2.0 evaluation_params.*

### `SeparabilityScore(object)`
*Cluster separability metrics.*


### `CoherenceScore(object)`
*Temporal coherence metrics.*


### `FidelityScore(object)`
*Regime fidelity metrics (behavior matches label).*


### `BoundaryScore(object)`
*Regime boundary quality metrics.*


### `CoverageScore(object)`
*Coverage and balance metrics.*


### `RegimeScoreResult(object)`
*Complete regime scoring result.*


### Module Functions
- `_clamp01(x)` → `float`  *Clamp value to [0, 1].*
- `_silhouette_to_score(sil)` → `float`  *Map Silhouette [-1, 1] to [0, 1].*
- `_db_to_score(db)` → `float`  *Map Davies-Bouldin [0, inf) lower=better to [0, 1].*
- `_ch_to_score(ch)` → `float`  *Map Calinski-Harabasz [0, inf) higher=better to [0, 1].*
- `_compute_hurst(series, max_k)` → `float`  *Compute Hurst exponent using R/S analysis.*
- `_compute_mahalanobis_safe(x, mean, cov, reg_lambda)` → `float`  *Compute Mahalanobis distance with regularization and fallback.*
- `_calculate_separability(features, labels, config)` → `SeparabilityScore`  *Calculate cluster separability score.*
- `_calculate_coherence(regimes, config)` → `CoherenceScore`  *Calculate temporal coherence score.*
- `_calculate_fidelity(data, regimes, config)` → `FidelityScore`  *Calculate regime fidelity score.*
- `_calculate_boundary(features, regimes, config)` → `BoundaryScore`  *Calculate boundary strength score using Mahalanobis distance.*
- `_calculate_coverage(regimes, config)` → `CoverageScore`  *Calculate coverage and balance score.*
- `calculate_regime_score(data, regimes, features, config)` → `RegimeScoreResult`  *Calculate comprehensive regime quality score.*
- `_build_default_features(data)` → `pd.DataFrame`  *Build default feature set from OHLCV data.*

## `src/core/simulator/excel_export.py`

### `StrategySimulatorExport(object)`
*Export strategy simulation results to Excel (REFACTORED).*

- `add_results(results)` → `None`  *Add simulation results to export.*
- `add_optimization_run(opt_run)` → `None`  *Add optimization run to export.*
- `add_ui_table_data(table_data)` → `None`  *Add UI table data for export as first sheet.*
- `add_ui_table_sheet()` → `None`  *Add UI table as first sheet (delegiert).*
- `add_summary_sheet()` → `None`  *Add summary sheet with all results (delegiert).*
- `add_optimization_sheet()` → `None`  *Add optimization results sheet (delegiert).*
- `add_trades_sheet(result, sheet_name)` → `None`  *Add detailed trades sheet for a specific result (delegiert).*
- `add_parameters_sheet()` → `None`  *Add sheet documenting parameter definitions (delegiert).*
- `save()` → `Path`  *Save workbook and return path (delegiert).*
- *...1 private methods*
- `__init__(filepath)`  *Initialize exporter.*

### Module Functions
- `export_simulation_results(results, filepath, optimization_run, ui_table_data)` → `Path`  *Convenience function to export simulation results.*

## `src/core/simulator/excel_export_optimization.py`

### `ExcelExportOptimization(object)`
*Helper for optimization sheet creation.*

- `add_optimization_sheet()` → `None`  *Add optimization results sheet.*
- `__init__(parent)`

## `src/core/simulator/excel_export_parameters.py`

### `ExcelExportParameters(object)`
*Helper for parameters sheet creation.*

- `add_parameters_sheet()` → `None`  *Add sheet documenting parameter definitions.*
- `__init__(parent)`

## `src/core/simulator/excel_export_save.py`

### `ExcelExportSave(object)`
*Helper for save orchestration.*

- `save()` → `Path`  *Save workbook and return path.*
- `__init__(parent)`

## `src/core/simulator/excel_export_styles.py`

### Module Functions
- `check_openpyxl_available()`  *Check if openpyxl is available.*
- `create_header_font()` → `Font`  *Create header font style.*
- `create_header_fill()` → `PatternFill`  *Create header fill style.*
- `create_positive_fill()` → `PatternFill`  *Create positive value fill style (green).*
- `create_negative_fill()` → `PatternFill`  *Create negative value fill style (red).*
- `create_border()` → `Border`  *Create cell border style.*
- `create_workbook()`  *Create new openpyxl workbook.*

## `src/core/simulator/excel_export_summary.py`

### `ExcelExportSummary(object)`
*Helper for summary sheet creation.*

- `add_summary_sheet()` → `None`  *Add summary sheet with all results, sorted by Score.*
- `__init__(parent)`

## `src/core/simulator/excel_export_trades.py`

### `ExcelExportTrades(object)`
*Helper for trades sheet creation.*

- `add_trades_sheet(result, sheet_name)` → `None`  *Add detailed trades sheet for a specific result.*
- `__init__(parent)`

## `src/core/simulator/excel_export_ui_table.py`

### `ExcelExportUITable(object)`
*Helper for UI table sheet creation.*

- `add_ui_table_sheet()` → `None`  *Add UI table as first sheet (exact copy of displayed table).*
- `add_parameter_legend(ws, start_row)` → `None`  *Add parameter legend below the results table.*
- `__init__(parent)`

## `src/core/simulator/optimization_bayesian.py`

### `OptimizationConfig(object)`
*Configuration for optimization run.*


### `BayesianOptimizer(object)`
*Bayesian optimization using optuna TPE sampler.*

- `cancel()` → `None`  *Cancel running optimization.*
- `optimize(progress_callback)` → `OptimizationRun`  *Run Bayesian optimization (synchronous).*
- *...8 private methods*
- `__init__(data, symbol, config)`  *Initialize optimizer.*

### `GridSearchOptimizer(object)`
*Grid search optimizer for exhaustive parameter exploration.*

- `cancel()` → `None`  *Cancel running optimization.*
- `optimize(progress_callback, max_combinations)` → `OptimizationRun`  *Run grid search optimization (synchronous).*
- `estimate_combinations()` → `int`  *Estimate total number of parameter combinations.*
- *...16 private methods*
- `__init__(data, symbol, config)`  *Initialize optimizer.*

## `src/core/simulator/result_types.py`

### `TradeRecord(object)`
*Single trade record from simulation.*

- @property `duration_seconds()` → `float`  *Duration of trade in seconds.*
- @property `is_winner()` → `bool`  *Check if trade was profitable.*
- @property `r_multiple()` → `float | None`  *Calculate R-multiple if stop loss was set.*

### `SimulationResult(object)`
*Result of a single simulation run.*

- @property `expectancy()` → `float | None`  *Calculate expectancy (avg P&L per trade).*
- @property `recovery_factor()` → `float | None`  *Calculate recovery factor (Net Profit / Max Drawdown).*
- `to_summary_dict()` → `dict[str, Any]`  *Convert to summary dictionary for table display.*

### `OptimizationTrial(object)`
*Single trial in an optimization run.*


### `OptimizationRun(object)`
*Result of an optimization run (Grid Search or Bayesian).*

- `get_top_n_trials(n)` → `list[OptimizationTrial]`  *Get top N trials sorted by score (descending).*
- `to_dataframe_rows()` → `list[dict[str, Any]]`  *Convert all trials to list of dicts for DataFrame/Excel export.*

## `src/core/simulator/simulation_engine.py`

### `SimulationConfig(object)`
*Configuration for a simulation run.*


### `StrategySimulator(object)`
*Simulator for running strategies with configurable parameters.*

- async `run_simulation(strategy_name, parameters, initial_capital, position_size_pct, slippage_pct, commission_pct, stop_loss_pct, take_profit_pct, progress_callback, entry_only, entry_side, entry_lookahead_mode, entry_lookahead_bars, sl_atr_multiplier, tp_atr_multiplier, atr_period, trailing_stop_enabled, trailing_stop_atr_multiplier, trailing_stop_mode, trailing_pct_distance, trailing_activation_pct, regime_adaptive, atr_trending_mult, atr_ranging_mult, maker_fee_pct, taker_fee_pct, trade_direction, leverage)` → `SimulationResult`  *Run a single simulation with given parameters.*
- `get_entry_exit_points(result)` → `list[dict[str, Any]]`  *Extract entry/exit points for chart visualization.*
- *...32 private methods*
- `__init__(data, symbol)`  *Initialize simulator with chart data.*

## `src/core/simulator/simulation_signal_utils.py`

### Module Functions
- `true_range(df)` → `pd.Series`  *Calculate True Range.*
- `calculate_rsi(prices, period)` → `pd.Series`  *Calculate RSI using Wilder's Smoothing Method.*
- `calculate_obv(df)` → `pd.Series`  *Calculate On-Balance Volume.*

## `src/core/simulator/simulation_signals.py`

### `StrategySignalGenerator(object)`
*Generates trading signals for supported strategies.*

- `generate(strategy_name, parameters)` → `pd.DataFrame`  *Generate trading signals based on strategy logic.*
- *...14 private methods*
- `__init__(data)`

## `src/core/simulator/simulation_signals_bollinger_squeeze.py`

### Module Functions
- `bollinger_squeeze_signals(df, params, true_range)` → `pd.Series`  *Generate Bollinger Squeeze Breakout signals.*

## `src/core/simulator/simulation_signals_breakout.py`

### Module Functions
- `breakout_signals(df, params, true_range)` → `pd.Series`  *Generate breakout strategy signals.*

## `src/core/simulator/simulation_signals_mean_reversion.py`

### Module Functions
- `mean_reversion_signals(df, params, calculate_rsi)` → `pd.Series`  *Generate mean reversion strategy signals.*

## `src/core/simulator/simulation_signals_momentum.py`

### Module Functions
- `momentum_signals(df, params, calculate_rsi, calculate_obv)` → `pd.Series`  *Generate momentum strategy signals.*

## `src/core/simulator/simulation_signals_opening_range.py`

### Module Functions
- `opening_range_signals(df, params, true_range)` → `pd.Series`  *Generate Opening Range Breakout signals.*

## `src/core/simulator/simulation_signals_regime_hybrid.py`

### Module Functions
- `regime_hybrid_signals(df, params, calculate_rsi, calculate_obv, true_range)` → `pd.Series`  *Generate Regime Switching Hybrid signals.*

## `src/core/simulator/simulation_signals_scalping.py`

### Module Functions
- `scalping_signals(df, params, calculate_rsi)` → `pd.Series`  *Generate scalping strategy signals.*

## `src/core/simulator/simulation_signals_sideways_range.py`

### Module Functions
- `sideways_range_signals(df, params, calculate_rsi)` → `pd.Series`  *Generate sideways range market strategy signals.*
- `_calculate_adx(df, period)` → `pd.Series`  *Calculate Average Directional Index (ADX).*

## `src/core/simulator/simulation_signals_trend_following.py`

### Module Functions
- `trend_following_signals(df, params, calculate_rsi)` → `pd.Series`  *Generate trend following strategy signals.*

## `src/core/simulator/simulation_signals_trend_pullback.py`

### Module Functions
- `trend_pullback_signals(df, params, calculate_rsi)` → `pd.Series`  *Generate Trend Pullback signals.*

## `src/core/simulator/strategy_params.py`

### Module Functions
- `get_strategy_parameters(strategy)` → `StrategyParameterConfig`  *Get parameter configuration for a strategy.*
- `get_default_parameters(strategy)` → `dict[str, Any]`  *Get default parameter values for a strategy.*
- `_is_exit_parameter(param_def)` → `bool`
- `filter_entry_only_param_config(param_config)` → `StrategyParameterConfig`  *Return a param config without exit-related parameters.*
- `filter_entry_only_params(strategy, params)` → `dict[str, Any]`  *Filter a params dict to entry-only parameters (no exit params).*

## `src/core/simulator/strategy_params_base.py`

### `StrategyName(str, Enum)`
*Available strategy names.*

- @classmethod `display_names()` → `dict[str, str]`  *Get mapping of enum values to display names.*

### `ParameterDefinition(object)`
*Definition of a single configurable parameter.*

- `validate(value)` → `bool`  *Validate a value against this parameter definition.*
- `get_range_values()` → `list[Any]`  *Get list of values for grid search.*

### `StrategyParameterConfig(object)`
*Configuration for a strategy's parameters.*

- `get_defaults()` → `dict[str, Any]`  *Get default values for all parameters.*
- `get_parameter(name)` → `ParameterDefinition | None`  *Get a specific parameter by name.*

## `src/core/simulator/strategy_persistence.py`

### Module Functions
- `get_params_file(strategy_name, params_dir)` → `Path`  *Get path to parameter file for a strategy.*
- `save_strategy_params(strategy_name, params, symbol, score, params_dir)` → `Path`  *Save optimized strategy parameters.*
- `save_strategy_params_to_path(filepath, strategy_name, params, symbol, score)` → `Path`  *Save optimized strategy parameters to a specific file path.*
- `load_strategy_params(strategy_name, params_dir)` → `dict[str, Any] | None`  *Load saved strategy parameters.*
- `get_all_saved_strategies(params_dir)` → `list[str]`  *Get list of strategies with saved parameters.*
- `delete_strategy_params(strategy_name, params_dir)` → `bool`  *Delete saved strategy parameters.*
- `get_params_metadata(strategy_name, params_dir)` → `dict[str, Any] | None`  *Get metadata for saved parameters.*

## `src/core/strategy/compiled_strategy.py`

### `CompiledStrategy(bt.Strategy)`
*Dynamically compiled strategy from StrategyDefinition.*

- `next()`  *Execute strategy logic on each bar.*
- `notify_order(order)`  *Handle order notifications.*
- *...12 private methods*
- `__init__(definition)`  *Initialize strategy with definition.*

## `src/core/strategy/compiler.py`

### `CompilationError(Exception)`
*Exception raised when strategy compilation fails.*


### `IndicatorFactory(object)`
*Factory for creating Backtrader indicators from IndicatorConfig.*

- @classmethod `create_indicator(config, data)` → `bt.Indicator`  *Create Backtrader indicator from configuration.*
- *...3 private methods*

### `ConditionEvaluator(object)`
*Evaluates Condition and LogicGroup expressions.*

- `evaluate(logic)` → `bool`  *Evaluate condition or logic group.*
- *...8 private methods*
- `__init__(strategy)`  *Initialize evaluator.*

### `StrategyCompiler(object)`
*Compiles StrategyDefinition into executable Backtrader strategies.*

- `compile(definition)` → `type[bt.Strategy]`  *Compile strategy definition to Backtrader Strategy class.*
- *...1 private methods*

## `src/core/strategy/definition.py`

### `IndicatorType(str, Enum)`
*Supported technical indicator types.*


### `ComparisonOperator(str, Enum)`
*Comparison operators for conditions.*


### `LogicOperator(str, Enum)`
*Logic operators for combining conditions.*


### `IndicatorConfig(BaseModel)`
*Configuration for a technical indicator.*

- @classmethod `validate_alias(v)` → `str`  *Validate alias format (alphanumeric + underscore).*

### `Condition(BaseModel)`
*Single condition for strategy logic.*

- `validate_range_operators()` → `Condition`  *Validate that conditions have a usable right operand.*

### `LogicGroup(BaseModel)`
*Group of conditions combined with logic operators.*

- @classmethod `validate_conditions_not_empty(v)` → `list`  *Validate that conditions list is not empty.*
- @classmethod `normalize_group_type(v)` → `str`  *Normalize legacy 'composite' type to 'group'.*
- `validate_not_operator()` → `LogicGroup`  *Validate that NOT operator has exactly one condition.*

### `RiskManagement(BaseModel)`
*Risk management parameters for the strategy.*

- `validate_stop_loss_methods()` → `RiskManagement`  *Validate that only one stop loss method is used.*
- `validate_take_profit_methods()` → `RiskManagement`  *Validate that only one take profit method is used.*

### `StrategyDefinition(BaseModel)`
*Complete trading strategy definition.*

- @classmethod `validate_unique_aliases(v)` → `list[IndicatorConfig]`  *Validate that all indicator aliases are unique.*
- `validate_condition_references()` → `StrategyDefinition`  *Validate that all condition references point to valid indicators.*
- `get_indicator_by_alias(alias)` → `IndicatorConfig | None`  *Get indicator configuration by alias.*
- `to_yaml()` → `str`  *Export strategy definition as YAML string.*
- @classmethod `from_yaml(yaml_str)` → `StrategyDefinition`  *Load strategy definition from YAML string.*
- `to_json_file(filepath)` → `None`  *Save strategy definition to JSON file.*
- @classmethod `from_json_file(filepath)` → `StrategyDefinition`  *Load strategy definition from JSON file.*

### Module Functions
- `_get_condition_type(v)` → `str`  *Get discriminator value for Condition | LogicGroup union.*

## `src/core/strategy/engine.py`

### `SignalType(Enum)`
*Types of trading signals.*


### `StrategyType(Enum)`
*Types of trading strategies.*


### `Signal(object)`
*Trading signal generated by strategy.*


### `StrategyConfig(object)`
*Configuration for a trading strategy.*


### `StrategyState(object)`
*Current state of a strategy.*


### `BaseStrategy(ABC)`
*Abstract base class for trading strategies.*

- async `evaluate(data)` → `Signal | None`  *Evaluate strategy and generate signal.*
- `update_position(symbol, quantity)` → `None`  *Update position tracking.*
- `get_position(symbol)` → `int`  *Get current position.*
- `has_position(symbol)` → `bool`  *Check if strategy has position.*
- `calculate_position_size(symbol, signal_confidence, account_equity, current_price)` → `int`  *Calculate position size.*
- `__init__(config, indicator_engine)`  *Initialize strategy.*

### `StrategyEngine(object)`
*Engine for managing multiple trading strategies.*

- `create_strategy(config)` → `BaseStrategy`  *Create a strategy instance.*
- `enable_strategy(name)` → `None`  *Enable a strategy.*
- `disable_strategy(name)` → `None`  *Disable a strategy.*
- async `evaluate_all(market_data)` → `list[Signal]`  *Evaluate all active strategies.*
- `combine_signals(signals)` → `Signal | None`  *Combine multiple signals into consensus (refactored).*
- `get_strategy_stats(name)` → `dict[str, Any]`  *Get strategy statistics.*
- `signal_to_order(signal)` → `OrderRequest`  *Convert signal to order request.*
- *...6 private methods*
- `__init__()`  *Initialize strategy engine.*

## `src/core/strategy/evaluation.py`

### `ConditionEvaluator(object)`
*Evaluates trading strategy conditions.*

- `evaluate(condition)` → `bool`  *Evaluate a condition.*
- *...14 private methods*
- `__init__(strategy)`  *Initialize evaluator with strategy context.*

## `src/core/strategy/loader.py`

### `StrategyLoader(object)`
*Loads and manages strategy definitions from YAML files.*

- `discover_strategies()` → `List[str]`  *Discover all available strategy YAML files.*
- `load_strategy(name)` → `Optional[StrategyDefinition]`  *Load a strategy by name.*
- `load_strategy_from_file(file_path)` → `Optional[StrategyDefinition]`  *Load a strategy directly from a YAML file path.*
- `load_all_strategies()` → `Dict[str, StrategyDefinition]`  *Load all discovered strategies.*
- `get_strategy_info(name)` → `Optional[Dict]`  *Get metadata about a strategy without fully loading it.*
- `__init__(strategy_dirs)`  *Initialize strategy loader.*

### Module Functions
- `get_strategy_loader()` → `StrategyLoader`  *Get the global strategy loader instance.*

## `src/core/strategy/strategies/breakout.py`

### `BreakoutStrategy(BaseStrategy)`
*Breakout strategy using support/resistance and volume.*

- async `evaluate(data)` → `Signal | None`  *Evaluate breakout strategy.*

## `src/core/strategy/strategies/mean_reversion.py`

### `MeanReversionStrategy(BaseStrategy)`
*Mean reversion strategy using Bollinger Bands.*

- async `evaluate(data)` → `Signal | None`  *Evaluate mean reversion strategy.*
- *...7 private methods*

## `src/core/strategy/strategies/momentum.py`

### `MomentumStrategy(BaseStrategy)`
*Momentum strategy using rate of change and volume.*

- async `evaluate(data)` → `Signal | None`  *Evaluate momentum strategy.*

## `src/core/strategy/strategies/scalping.py`

### `ScalpingStrategy(BaseStrategy)`
*High-frequency scalping strategy.*

- async `evaluate(data)` → `Signal | None`  *Evaluate scalping strategy.*

## `src/core/strategy/strategies/trend_following.py`

### `TrendFollowingStrategy(BaseStrategy)`
*Trend following strategy using moving averages.*

- async `evaluate(data)` → `Signal | None`  *Evaluate trend following strategy.*
- *...5 private methods*

## `src/core/trading_bot/ai_validator.py`

### `AISignalValidator(object)`
*Validiert Trading-Signale mittels LLM mit hierarchischer Validierung.*

- @property `provider()` → `str`  *Holt den aktuellen Provider aus den QSettings.*
- @property `model()` → `str`  *Holt das aktuelle Model aus den QSettings basierend auf Provider.*
- async `validate_signal(signal, indicators, market_context)` → `AIValidation`  *Validiert ein Trading-Signal mittels LLM (Quick Validation).*
- async `validate_signal_hierarchical(signal, indicators, market_context, ohlcv_data)` → `AIValidation`  *Hierarchische Signal-Validierung (Option A).*
- `update_config(enabled, confidence_threshold, confidence_threshold_trade, confidence_threshold_deep, deep_analysis_enabled)` → `None`  *Aktualisiert Konfiguration zur Laufzeit.*
- `__init__(enabled, confidence_threshold_trade, confidence_threshold_deep, deep_analysis_enabled, fallback_to_technical, timeout_seconds)`  *Args:*

## `src/core/trading_bot/ai_validator_config.py`

### `ValidationLevel(str, Enum)`
*Validierungsstufe.*


### `AIValidation(object)`
*Ergebnis der AI-Validierung.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

### Module Functions
- `get_model_from_settings(provider)` → `str`  *Holt das konfigurierte Model aus den QSettings basierend auf Provider.*
- `get_provider_from_settings()` → `str`  *Holt den konfigurierten AI Provider aus den QSettings.*

## `src/core/trading_bot/ai_validator_prompts.py`

### `AIValidatorPrompts(object)`
*Prompt-Builder für AI-Validierung.*

- `build_prompt(signal, indicators, market_context)` → `str`  *Erstellt den LLM-Prompt für Quick Validation.*
- `build_deep_prompt(signal, indicators, market_context, ohlcv_data)` → `str`  *Erstellt ausführlichen Deep Analysis Prompt.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/ai_validator_providers.py`

### `AIValidatorProviders(object)`
*API-Provider-Integrationen für AI-Validierung.*

- async `call_llm(prompt)` → `dict[str, Any]`  *Ruft das LLM auf (Router zu Provider-spezifischen Methoden).*
- async `call_openai(prompt)` → `dict[str, Any]`  *OpenAI API Call.*
- async `call_anthropic(prompt)` → `dict[str, Any]`  *Anthropic API Call.*
- async `call_gemini(prompt)` → `dict[str, Any]`  *Google Gemini API Call.*
- `reset_clients()` → `None`  *Reset all API clients (called when config changes).*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/ai_validator_validation.py`

### `AIValidatorValidation(object)`
*Validierungs-Flows für AI Signal Validator.*

- async `validate_signal(signal, indicators, market_context)` → `AIValidation`  *Validiert ein Trading-Signal mittels LLM (Quick Validation).*
- async `validate_signal_hierarchical(signal, indicators, market_context, ohlcv_data)` → `AIValidation`  *Hierarchische Signal-Validierung (Option A).*
- async `run_deep_analysis(signal, indicators, market_context, ohlcv_data)` → `AIValidation`  *Führt Deep Analysis durch.*
- `parse_response(response)` → `AIValidation`  *Parst die LLM-Antwort.*
- `create_bypass_validation(reason)` → `AIValidation`  *Erstellt Bypass-Validation (AI deaktiviert).*
- `create_fallback_validation(error)` → `AIValidation`  *Erstellt Fallback-Validation (API-Fehler, aber Technical OK).*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/bot_config.py`

### `SessionConfig(object)`
*Konfiguration für Trading-Sessions (optional für Daytrading-Grenzen).*


### `AIConfig(object)`
*Konfiguration für AI-basierte Signal-Validierung.*


### `LoggingConfig(object)`
*Konfiguration für Trade-Logging.*


### `BotConfig(object)`
*Zentrale Bot-Konfiguration.*

- @property `paper_mode()` → `bool`  *Paper-Mode ist IMMER True - keine Ausnahmen!*
- `to_dict()` → `dict`  *Konvertiert Config zu Dictionary (für Logging).*
- @classmethod `from_dict(data)` → `BotConfig`  *Erstellt Config aus Dictionary.*
- `__post_init__()` → `None`  *Validierung nach Initialisierung.*

## `src/core/trading_bot/bot_engine.py`

### `TradingBotEngine(object)`
*Haupt-Engine des Trading Bots (REFACTORED via Composition).*

- @property `state()` → `BotState`  *Aktueller Bot-Zustand.*
- @property `is_running()` → `bool`  *Bot läuft?*
- @property `has_position()` → `bool`  *Position offen?*
- @property `statistics()` → `BotStatistics`  *Aktuelle Statistiken.*
- `set_chart_data(data, symbol, timeframe)` → `None`  *Setzt Chart-Daten (delegiert).*
- `clear_chart_data()` → `None`  *Löscht Chart-Daten (delegiert).*
- @property `has_chart_data()` → `bool`  *Sind Chart-Daten verfügbar? (delegiert).*
- async `start()` → `None`  *Startet den Bot (delegiert).*
- async `stop(close_position)` → `None`  *Stoppt den Bot (delegiert).*
- `get_current_status()` → `dict`  *Gibt aktuellen Bot-Status zurück (delegiert).*
- `set_state_callback(callback)` → `None`  *Setzt Callback für State-Änderungen (delegiert).*
- `set_signal_callback(callback)` → `None`  *Setzt Callback für neue Signale (delegiert).*
- `set_position_opened_callback(callback)` → `None`  *Setzt Callback für Position-Öffnung (delegiert).*
- `set_position_closed_callback(callback)` → `None`  *Setzt Callback für Position-Schließung (delegiert).*
- `set_error_callback(callback)` → `None`  *Setzt Callback für Fehler (delegiert).*
- `set_log_callback(callback)` → `None`  *Setzt Callback für Log-Nachrichten (delegiert).*
- async `manual_close_position()` → `None`  *Schließt Position manuell (delegiert).*
- async `on_price_update(price)` → `None`  *Preis-Update von außen (delegiert).*
- `update_config(config)` → `None`  *Aktualisiert die Bot-Konfiguration.*
- `update_indicator_config(indicator_updates, save)` → `None`  *Aktualisiert Indikator-Konfiguration (für Strategy Bridge).*
- `__init__(adapter, config, strategy_config_path)`  *Args:*

## `src/core/trading_bot/bot_engine_callbacks.py`

### `BotEngineCallbacks(object)`
*Helper for callback management.*

- `set_state_callback(callback)` → `None`  *Setzt Callback für State-Änderungen.*
- `set_signal_callback(callback)` → `None`  *Setzt Callback für neue Signale.*
- `set_position_opened_callback(callback)` → `None`  *Setzt Callback für Position-Öffnung.*
- `set_position_closed_callback(callback)` → `None`  *Setzt Callback für Position-Schließung.*
- `set_error_callback(callback)` → `None`  *Setzt Callback für Fehler.*
- `set_log_callback(callback)` → `None`  *Setzt Callback für Log-Nachrichten.*
- *...2 private methods*
- `__init__(parent)`

## `src/core/trading_bot/bot_engine_lifecycle.py`

### `BotEngineLifecycle(object)`
*Helper for bot lifecycle management.*

- async `start()` → `None`  *Startet den Bot.*
- async `stop(close_position)` → `None`  *Stoppt den Bot.*
- *...4 private methods*
- `__init__(parent)`

## `src/core/trading_bot/bot_engine_persistence.py`

### `BotEnginePersistence(object)`
*Helper for position persistence.*

- `save_position()` → `bool`  *Speichert aktive Position in Datei.*
- `load_position()` → `bool`  *Lädt gespeicherte Position aus Datei.*
- `__init__(parent)`

## `src/core/trading_bot/bot_engine_statistics.py`

### `BotEngineStatistics(object)`
*Helper for statistics management.*

- *...2 private methods*
- `__init__(parent)`

## `src/core/trading_bot/bot_engine_status.py`

### `BotEngineStatus(object)`
*Helper for status queries.*

- @property `state()` → `BotState`  *Aktueller Bot-Zustand.*
- @property `is_running()` → `bool`  *Bot läuft?*
- @property `has_position()` → `bool`  *Position offen?*
- @property `statistics()` → `BotStatistics`  *Aktuelle Statistiken.*
- `get_current_status()` → `dict`  *Gibt aktuellen Bot-Status zurück.*
- `__init__(parent)`

## `src/core/trading_bot/bot_market_analyzer.py`

### `BotMarketAnalyzer(object)`
*Verwaltet Marktdaten-Fetching und technische Analyse.*

- `set_chart_data(data, symbol, timeframe)` → `None`  *Setzt Chart-Daten für die Analyse.*
- `clear_chart_data()` → `None`  *Löscht die Chart-Daten (z.B. bei Symbol-Wechsel).*
- @property `has_chart_data()` → `bool`  *Sind Chart-Daten verfügbar?*
- async `fetch_market_data()` → `pd.DataFrame | None`  *Holt Marktdaten mit Indikatoren.*
- `calculate_indicators(df)` → `pd.DataFrame`  *Berechnet technische Indikatoren.*
- `detect_regime(df)` → `str`  *Erkennt Markt-Regime (Trending/Choppy).*
- `extract_market_context(df, regime)` → `'MarketContext'`  *Extrahiert Markt-Kontext für Trade Logging.*
- *...3 private methods*
- `__init__(parent_engine)`  *Args:*

## `src/core/trading_bot/bot_trade_handler.py`

### `BotTradeHandler(object)`
*Verwaltet Trade-Ausführung und Position-Management.*

- async `execute_trade(signal, indicators, market_context)` → `None`  *Führt Trade aus (öffnet Position).*
- async `close_position(exit_result)` → `None`  *Schließt Position.*
- async `on_exit_triggered(position, exit_result)` → `None`  *Callback wenn Exit getriggert wird.*
- async `on_trailing_updated(position, old_sl, new_sl)` → `None`  *Callback bei Trailing-Stop Update.*
- async `on_price_updated(position)` → `None`  *Callback bei Preis-Update.*
- async `on_price_update(price)` → `None`  *Wird von außen aufgerufen bei Preis-Updates (Streaming).*
- async `manual_close_position()` → `None`  *Schließt Position manuell.*
- `__init__(parent_engine)`  *Args:*

## `src/core/trading_bot/bot_types.py`

### `BotState(str, Enum)`
*Bot-Zustände.*


### `BotStatistics(object)`
*Tagesstatistiken des Bots.*

- @property `win_rate()` → `float`  *Gewinnrate in %.*
- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

## `src/core/trading_bot/data_preflight.py`

### `DataPreflightService(object)`
*Zentraler Service für Datenqualitätsprüfung.*

- `run_preflight(df, symbol, timeframe, clean_data)` → `PreflightResult`  *Führt vollständige Preflight-Prüfung durch.*
- *...8 private methods*
- `__init__(config)`

### Module Functions
- `run_preflight(df, symbol, timeframe, config)` → `PreflightResult`  *Convenience-Funktion für Preflight-Check.*
- `quick_validate(df, symbol, min_rows)` → `tuple[bool, str]`  *Schnelle Validierung ohne volles Preflight.*

## `src/core/trading_bot/data_preflight_basic_checks.py`

### `DataPreflightBasicChecks(object)`
*Helper für Basic Preflight Checks (Index, Min Data, Freshness).*

- `check_index(df)` → `list[PreflightIssue]`  *Prüft Index-Validität.*
- `check_minimum_data(df)` → `list[PreflightIssue]`  *Prüft ob genug Daten für Indikatoren vorhanden sind.*
- `check_freshness(df, interval_minutes)` → `tuple[list[PreflightIssue], int]`  *Prüft Daten-Freshness.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/data_preflight_price_volume.py`

### `DataPreflightPriceVolume(object)`
*Helper für Price & Volume Checks.*

- `check_prices(df)` → `list[PreflightIssue]`  *Prüft auf negative/null Preise.*
- `check_volume(df)` → `tuple[list[PreflightIssue], int]`  *Prüft Volume-Daten.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/data_preflight_quality.py`

### `DataPreflightQuality(object)`
*Helper für Quality Checks (Outliers, Gaps, Cleaning).*

- `check_outliers(df)` → `tuple[list[PreflightIssue], int]`  *Prüft auf Outliers mittels Z-Score.*
- `check_gaps(df, interval_minutes)` → `tuple[list[PreflightIssue], int]`  *Prüft auf Zeitlücken.*
- `clean_data(df)` → `pd.DataFrame`  *Bereinigt Daten (Outlier-Korrektur).*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/data_preflight_state.py`

### `PreflightStatus(str, Enum)`
*Status der Preflight-Prüfung.*


### `IssueType(str, Enum)`
*Typen von erkannten Problemen.*


### `IssueSeverity(str, Enum)`
*Schweregrad eines Problems.*


### `PreflightIssue(object)`
*Einzelnes erkanntes Problem.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

### `PreflightResult(object)`
*Ergebnis der Preflight-Prüfung.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*
- @property `is_tradeable()` → `bool`  *Prüft ob Daten für Trading geeignet sind.*
- @property `critical_issues()` → `list[PreflightIssue]`  *Gibt nur kritische Issues zurück.*
- @property `warning_issues()` → `list[PreflightIssue]`  *Gibt nur Warnungen zurück.*
- `get_summary()` → `str`  *Erzeugt Zusammenfassung als String.*

### `PreflightConfig(object)`
*Konfiguration für Preflight-Checks.*


## `src/core/trading_bot/entry_score_calculators.py`

### `EntryScoreCalculators(object)`
*Collection of component score calculation methods.*

- `calculate_long_components(df, current)` → `List[ComponentScore]`  *Calculate all component scores for LONG direction.*
- `calc_trend_alignment_long(current)` → `ComponentScore`  *Calculate EMA stack alignment for LONG.*
- `calc_rsi_momentum_long(current)` → `ComponentScore`  *Calculate RSI score for LONG.*
- `calc_macd_momentum_long(current)` → `ComponentScore`  *Calculate MACD score for LONG.*
- `calculate_short_components(df, current)` → `List[ComponentScore]`  *Calculate all component scores for SHORT direction.*
- `calc_trend_alignment_short(current)` → `ComponentScore`  *Calculate EMA stack alignment for SHORT.*
- `calc_rsi_momentum_short(current)` → `ComponentScore`  *Calculate RSI score for SHORT.*
- `calc_macd_momentum_short(current)` → `ComponentScore`  *Calculate MACD score for SHORT.*
- `calc_trend_strength(current, direction)` → `ComponentScore`  *Calculate ADX-based trend strength score.*
- `calc_volatility(current)` → `ComponentScore`  *Calculate volatility component score.*
- `calc_volume(current)` → `ComponentScore`  *Calculate volume confirmation score.*
- *...1 private methods*
- `__init__(config)`  *Initialize calculators.*

## `src/core/trading_bot/entry_score_config.py`

### `EntryScoreConfig(object)`
*Configuration for Entry Score calculation.*

- `validate()` → `bool`  *Validate config - weights must sum to ~1.0.*
- `to_dict()` → `Dict[str, Any]`  *Convert to dictionary.*
- @classmethod `from_dict(data)` → `'EntryScoreConfig'`  *Create from dictionary.*

### Module Functions
- `load_entry_score_config(path)` → `EntryScoreConfig`  *Load entry score config from JSON file.*
- `save_entry_score_config(config, path)` → `bool`  *Save entry score config to JSON file.*

## `src/core/trading_bot/entry_score_engine.py`

### `EntryScoreResult(object)`
*Complete result of entry score calculation.*

- @property `is_valid_for_entry()` → `bool`  *Check if score is valid for entry.*
- @property `long_score()` → `float`  *Get score if direction is LONG.*
- @property `short_score()` → `float`  *Get score if direction is SHORT.*
- `get_components_summary()` → `Dict[str, Dict[str, Any]]`  *Get summary of all component scores.*
- `to_dict()` → `Dict[str, Any]`  *Convert to dictionary.*
- `get_reasoning()` → `str`  *Generate human-readable reasoning for the score.*

### `EntryScoreEngine(object)`
*Calculates normalized entry scores (0.0 - 1.0) from market data.*

- `calculate(df, regime_result, symbol, timeframe)` → `EntryScoreResult`  *Calculate entry score from OHLCV DataFrame.*
- *...3 private methods*
- `__init__(config)`  *Initialize Entry Score Engine.*

### Module Functions
- `get_entry_score_engine(config)` → `EntryScoreEngine`  *Get global EntryScoreEngine singleton.*
- `calculate_entry_score(df, regime_result, symbol, timeframe)` → `EntryScoreResult`  *Convenience function to calculate entry score.*

## `src/core/trading_bot/entry_score_types.py`

### `ScoreDirection(str, Enum)`
*Signal direction for entry.*


### `ScoreQuality(str, Enum)`
*Quality tier based on final score.*


### `GateStatus(str, Enum)`
*Status of regime gates.*


### `ComponentScore(object)`
*Score from a single component.*

- @property `contribution_pct()` → `float`  *Contribution percentage to final score.*

### `GateResult(object)`
*Result of gate evaluation.*

- @classmethod `passed()` → `'GateResult'`
- @classmethod `blocked(reason)` → `'GateResult'`
- @classmethod `reduced(reason, penalty)` → `'GateResult'`
- @classmethod `boosted(reason, boost)` → `'GateResult'`

## `src/core/trading_bot/entry_trigger_evaluators.py`

### `EntryTriggerEvaluators(object)`
*Evaluates entry triggers: Breakout, Pullback, SFP.*

- `evaluate_breakout_trigger(df, level, direction)` → `TriggerResult`  *Evaluate breakout trigger for a level.*
- `evaluate_pullback_trigger(df, level, direction, atr)` → `TriggerResult`  *Evaluate pullback trigger to a level.*
- `evaluate_sfp_trigger(df, level, direction)` → `TriggerResult`  *Evaluate Swing Failure Pattern (SFP) trigger.*
- `find_best_trigger(df, levels_result, entry_score, atr)` → `Optional[TriggerResult]`  *Find the best entry trigger from available levels and entry score.*
- *...1 private methods*
- `__init__(config)`  *Initialize Entry Trigger Evaluators.*

## `src/core/trading_bot/exit_level_calculator.py`

### `ExitLevelCalculator(object)`
*Calculates SL/TP levels, trailing stops, and structure stops.*

- `calculate_exit_levels(entry_price, direction, atr, levels_result)` → `ExitLevels`  *Calculate all exit levels for a position.*
- *...6 private methods*
- `__init__(config)`  *Initialize Exit Level Calculator.*

## `src/core/trading_bot/indicator_calculator.py`

### `IndicatorCalculator(object)`
*Calculates technical indicators for MarketContextBuilder.*

- `calculate_indicators(df)` → `pd.DataFrame`  *Calculate all indicators required by MarketContext.*
- `__init__(config)`  *Initialize indicator calculator.*

## `src/core/trading_bot/level_engine.py`

### `LevelEngine(object)`
*Level Detection Engine v2.*

- `detect_levels(df, symbol, timeframe, current_price)` → `LevelsResult`  *Erkennt Levels aus DataFrame.*
- *...1 private methods*
- `__init__(config)`

### Module Functions
- `get_level_engine(config)` → `LevelEngine`  *Gibt globale LevelEngine-Instanz zurück (Singleton).*
- `reset_level_engine()` → `None`  *Setzt globale Engine zurück.*
- `detect_levels(df, symbol, timeframe, current_price)` → `LevelsResult`  *Convenience-Funktion für Level-Erkennung.*

## `src/core/trading_bot/level_engine_detection.py`

### `LevelEngineDetection(object)`
*Helper für Level Detection Methods.*

- `calculate_atr(df, period)` → `float`  *Berechnet ATR für Zone-Breite.*
- `detect_swing_levels(df, timeframe, atr)` → `List[Level]`  *Erkennt Swing Highs und Swing Lows.*
- `calculate_pivot_points(df, timeframe)` → `List[Level]`  *Berechnet Pivot Points (PP, R1, R2, S1, S2).*
- `detect_clusters(df, timeframe, atr)` → `List[Level]`  *Erkennt Preis-Cluster (Konsolidierungszonen).*
- `detect_daily_hl(df, timeframe)` → `List[Level]`  *Erkennt tägliche Hochs und Tiefs.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/level_engine_processing.py`

### `LevelEngineProcessing(object)`
*Helper für Level Processing (Merge, Strength, Classify, Select).*

- `merge_overlapping_levels(levels)` → `List[Level]`  *Merged überlappende Levels.*
- `calculate_level_strength(levels, df)` → `List[Level]`  *Berechnet Stärke basierend auf Touches.*
- `classify_levels(levels, current_price)` → `List[Level]`  *Klassifiziert Levels als Support oder Resistance.*
- `select_top_levels(levels, current_price)` → `List[Level]`  *Wählt die wichtigsten Levels aus.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/level_engine_state.py`

### `LevelType(Enum)`
*Typ des Levels.*


### `LevelStrength(Enum)`
*Stärke des Levels.*


### `DetectionMethod(Enum)`
*Methode zur Level-Erkennung.*


### `Level(object)`
*Einzelnes Level (Support/Resistance/Pivot etc.).*

- @property `price_mid()` → `float`  *Mittelpunkt der Zone.*
- @property `zone_width()` → `float`  *Breite der Zone in absoluten Zahlen.*
- @property `zone_width_pct()` → `float`  *Breite der Zone in Prozent des Mittelpreises.*
- `contains_price(price)` → `bool`  *Prüft ob ein Preis in der Zone liegt.*
- `is_near(price, tolerance_pct)` → `bool`  *Prüft ob ein Preis in der Nähe der Zone liegt.*
- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

### `LevelsResult(object)`
*Ergebnis der Level-Analyse.*

- @property `support_levels()` → `List[Level]`  *Nur Support-Levels (unter aktuellem Preis).*
- @property `resistance_levels()` → `List[Level]`  *Nur Resistance-Levels (über aktuellem Preis).*
- @property `key_levels()` → `List[Level]`  *Nur Key Levels (strength=KEY).*
- `get_nearest_support(price)` → `Optional[Level]`  *Findet nächstes Support-Level unter dem Preis.*
- `get_nearest_resistance(price)` → `Optional[Level]`  *Findet nächstes Resistance-Level über dem Preis.*
- `get_top_n(n, sort_by)` → `List[Level]`  *Gibt die Top-N wichtigsten Levels zurück.*
- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*
- `to_tag_format()` → `str`  *Konvertiert zu Tag-Format für Chatbot.*

### `LevelEngineConfig(object)`
*Konfiguration für LevelEngine.*


## `src/core/trading_bot/leverage_rules.py`

### `LeverageRulesEngine(object)`
*Dynamic leverage calculation with multiple safety checks.*

- `calculate_leverage(symbol, entry_price, regime_result, atr, requested_leverage, account_balance, current_exposure)` → `LeverageResult`  *Calculate recommended leverage for a trade.*
- `validate_leverage(leverage, symbol, entry_price, sl_price, direction)` → `tuple[bool, str, List[str]]`  *Validate that a specific leverage is safe for the trade.*
- `get_safe_leverage_for_sl(entry_price, sl_price, symbol)` → `int`  *Calculate safe leverage based on stop loss distance.*
- `update_config(config)` → `None`  *Update engine configuration.*
- `__init__(config)`  *Initialize Leverage Rules Engine.*

### Module Functions
- `get_leverage_rules_engine(config)` → `LeverageRulesEngine`  *Get global LeverageRulesEngine singleton.*
- `calculate_leverage(symbol, entry_price, regime_result, atr)` → `LeverageResult`  *Convenience function to calculate leverage.*
- `load_leverage_config(path)` → `LeverageRulesConfig`  *Load config from JSON file.*
- `save_leverage_config(config, path)` → `bool`  *Save config to JSON file.*

## `src/core/trading_bot/leverage_rules_calculation.py`

### `LeverageRulesCalculation(object)`
*Helper für LeverageRulesEngine calculation methods.*

- `calculate_leverage(symbol, entry_price, regime_result, atr, requested_leverage, account_balance, current_exposure)` → `'LeverageResult'`  *Calculate recommended leverage for a trade.*
- `validate_leverage(leverage, symbol, entry_price, sl_price, direction)` → `tuple[bool, str, List[str]]`  *Validate that a specific leverage is safe for the trade.*
- `get_safe_leverage_for_sl(entry_price, sl_price, symbol)` → `int`  *Calculate safe leverage based on stop loss distance.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/leverage_rules_helpers.py`

### `LeverageRulesHelpers(object)`
*Helper für LeverageRulesEngine private methods.*

- `get_asset_tier(symbol)` → `'AssetTier'`  *Determine asset tier for symbol.*
- `get_tier_max_leverage(tier)` → `int`  *Get max leverage for tier.*
- `get_regime_multiplier(regime_str)` → `float`  *Get regime-based leverage multiplier.*
- `get_volatility_multiplier(atr_percent)` → `float`  *Get volatility-based leverage multiplier.*
- `calculate_liquidation_prices(entry_price, leverage)` → `tuple[float, float]`  *Calculate liquidation prices for long and short positions.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/leverage_rules_state.py`

### `AssetTier(str, Enum)`
*Asset risk tier based on liquidity and volatility.*


### `LeverageAction(str, Enum)`
*Action taken by leverage calculation.*


### `LeverageRulesConfig(object)`
*Configuration for Leverage Rules Engine.*

- `to_dict()` → `Dict[str, Any]`  *Convert to dictionary.*
- @classmethod `from_dict(data)` → `'LeverageRulesConfig'`  *Create from dictionary.*

### `LeverageResult(object)`
*Result of leverage calculation.*

- @property `is_safe()` → `bool`  *Check if leverage is within safe limits.*
- `to_dict()` → `Dict[str, Any]`

## `src/core/trading_bot/llm_validation_prompt.py`

### `LLMValidationPrompt(object)`
*Helper für Prompt Building aus MarketContext.*

- `build_context_prompt(context, entry_score, levels_result)` → `str`  *Build optimized prompt from MarketContext.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/llm_validation_router.py`

### `LLMValidationRouter(object)`
*Helper für LLM Validation Routing (Quick→Deep) und Result Building.*

- async `run_quick_validation(prompt)` → `Dict[str, Any]`  *Run quick validation.*
- async `run_deep_validation(prompt, context)` → `Dict[str, Any]`  *Run deep validation with more thorough analysis.*
- `build_result(action, llm_response, tier, prompt_hash, latency_ms, entry_score, deep_triggered)` → `LLMValidationResult`  *Build validation result from LLM response.*
- `create_bypass_result(reason)` → `LLMValidationResult`  *Create bypass result when LLM is disabled.*
- `create_technical_fallback(error, entry_score)` → `LLMValidationResult`  *Create fallback result using technical analysis.*
- `create_error_result(error)` → `LLMValidationResult`  *Create error result when LLM fails and no fallback.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/llm_validation_service.py`

### `LLMValidationService(object)`
*Unified LLM Validation Service.*

- async `validate(context, entry_score, levels_result)` → `LLMValidationResult`  *Validate a trading signal using LLM.*
- `update_config(config)` → `None`  *Update service configuration.*
- *...1 private methods*
- `__init__(config)`  *Initialize LLM Validation Service.*

### Module Functions
- `get_llm_validation_service(config)` → `LLMValidationService`  *Get global LLMValidationService singleton.*
- async `validate_signal(context, entry_score)` → `LLMValidationResult`  *Convenience function to validate a signal.*
- `load_llm_validation_config(path)` → `LLMValidationConfig`  *Load config from JSON file.*
- `save_llm_validation_config(config, path)` → `bool`  *Save config to JSON file.*

## `src/core/trading_bot/llm_validation_state.py`

### `LLMAction(str, Enum)`
*Action taken by LLM validation.*


### `ValidationTier(str, Enum)`
*Validation tier used.*


### `LLMValidationConfig(object)`
*Configuration for LLM Validation Service.*

- `to_dict()` → `Dict[str, Any]`
- @classmethod `from_dict(data)` → `'LLMValidationConfig'`

### `LLMValidationResult(object)`
*Result of LLM validation.*

- @property `allows_entry()` → `bool`  *Check if validation allows entry.*
- @property `is_boost()` → `bool`
- @property `is_veto()` → `bool`
- `to_dict()` → `Dict[str, Any]`
- `get_summary()` → `str`  *Get human-readable summary.*

## `src/core/trading_bot/market_context_cache.py`

### `CacheEntry(object)`
*Einzelner Cache-Eintrag.*

- @property `is_expired()` → `bool`  *Prüft ob Eintrag abgelaufen ist.*
- @property `age_seconds()` → `int`  *Alter des Eintrags in Sekunden.*
- `touch()` → `None`  *Aktualisiert Zugriffszeitpunkt.*

### `CacheStats(object)`
*Statistiken über Cache-Nutzung.*

- @property `hit_rate()` → `float`  *Hit-Rate als Prozent.*
- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

### `CacheConfig(object)`
*Konfiguration für den Cache.*


### `MarketContextCache(object)`
*Thread-sicherer Cache für MarketContext.*

- `get_or_build(df, symbol, timeframe, force_rebuild, builder)` → `MarketContext`  *Holt Context aus Cache oder baut neu.*
- `get(symbol, timeframe)` → `MarketContext | None`  *Holt Context aus Cache ohne zu bauen.*
- `store(context, df)` → `None`  *Speichert Context manuell im Cache.*
- `invalidate(symbol, timeframe)` → `int`  *Invalidiert Cache-Einträge.*
- `clear()` → `int`  *Leert den gesamten Cache.*
- @property `stats()` → `CacheStats`  *Gibt Cache-Statistiken zurück.*
- @property `size()` → `int`  *Aktuelle Anzahl Einträge im Cache.*
- `get_entries_info()` → `list[dict]`  *Gibt Info über alle Cache-Einträge zurück.*
- *...7 private methods*
- `__init__(config, builder_config)`
- `__del__()`  *Cleanup bei Zerstörung.*

### Module Functions
- `get_global_cache(config, builder_config)` → `MarketContextCache`  *Gibt globale Cache-Instanz zurück (Singleton).*
- `reset_global_cache()` → `None`  *Setzt globalen Cache zurück.*
- `get_cached_context(df, symbol, timeframe, force_rebuild)` → `MarketContext`  *Convenience-Funktion für Cache-Zugriff.*

## `src/core/trading_bot/market_context_candles.py`

### `CandleSummary(object)`
*Zusammenfassung der letzten Candle(s) für Context.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*
- `__post_init__()` → `None`  *Berechne abgeleitete Metriken.*

## `src/core/trading_bot/market_context_config.py`

### `MarketContextBuilderConfig(object)`
*Konfiguration für den MarketContext Builder.*

- `__init__(preflight_enabled, preflight_config, ema_periods, rsi_period, macd_fast, macd_slow, macd_signal, bb_period, bb_std, atr_period, adx_period, adx_strong_threshold, adx_weak_threshold, volatility_high_atr_pct, volatility_extreme_atr_pct, pivot_lookback, level_min_touches, level_zone_atr_mult, top_n_levels)`

## `src/core/trading_bot/market_context_detectors.py`

### `RegimeDetector(object)`
*Detects market regime (trend strength + direction).*

- `detect_regime(df)` → `tuple[RegimeType, float, str]`  *Erkennt das Marktregime.*
- `detect_trend(df)` → `TrendDirection`  *Erkennt Trend-Richtung aus EMAs.*
- `calculate_mtf_alignment(trends)` → `float`  *Berechnet Multi-Timeframe Alignment Score.*
- `determine_volatility_state(atr_pct)` → `str`  *Bestimmt Volatilitäts-Zustand.*
- *...1 private methods*
- `__init__(config)`  *Initialize regime detector.*

### `LevelDetector(object)`
*Detects Support/Resistance levels.*

- `detect_levels(df, symbol, current_price, timeframe)` → `LevelsSnapshot`  *Erkennt Support/Resistance Levels.*
- `__init__(config)`  *Initialize level detector.*

## `src/core/trading_bot/market_context_enums.py`

### `RegimeType(str, Enum)`
*Marktregime-Typen für Regime-Gates.*


### `TrendDirection(str, Enum)`
*Trend-Richtung für Multi-Timeframe Analyse.*


### `LevelType(str, Enum)`
*Typ eines Support/Resistance Levels.*


### `LevelStrength(str, Enum)`
*Stärke eines Levels basierend auf Touches/Confluence.*


### `SignalStrength(str, Enum)`
*Signal-Stärke für Entry/Exit.*


### `SetupType(str, Enum)`
*Erkannte Setup-Typen.*


## `src/core/trading_bot/market_context_factories.py`

### Module Functions
- `create_empty_context(symbol, timeframe)` → `MarketContext`  *Erzeugt leeren MarketContext.*
- `create_indicator_snapshot_from_df(df, timeframe)` → `IndicatorSnapshot | None`  *Erzeugt IndicatorSnapshot aus DataFrame.*

## `src/core/trading_bot/market_context_indicators.py`

### `IndicatorSnapshot(object)`
*Snapshot aller Indikator-Werte zu einem Zeitpunkt.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*
- `get_momentum_score()` → `float`  *Berechnet einen Momentum-Score von -1 (bearish) bis +1 (bullish).*

## `src/core/trading_bot/market_context_levels.py`

### `Level(object)`
*Einzelnes Support/Resistance Level.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*
- `to_chat_tag()` → `str`  *Erzeugt Chatbot-Tag Format.*
- @property `midpoint()` → `float`  *Mittelpunkt der Zone.*

### `LevelsSnapshot(object)`
*Snapshot aller erkannten Levels zu einem Zeitpunkt.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*
- `get_chat_tags()` → `list[str]`  *Erzeugt alle Chatbot-Tags für die Key Levels.*

## `src/core/trading_bot/market_context_main.py`

### `MarketContext(object)`
*Kanonischer MarketContext - Single Source of Truth.*

- `to_dict()` → `dict[str, Any]`  *Konvertiert zu Dictionary (für JSON Export/AI Prompts).*
- `to_json(indent)` → `str`  *Konvertiert zu JSON String.*
- `to_ai_prompt_context()` → `dict`  *Erzeugt kompaktes Context-Dict für AI Prompts.*
- `is_valid_for_trading()` → `tuple[bool, list[str]]`  *Prüft ob Context für Trading geeignet ist.*
- @property `is_bullish_regime()` → `bool`  *Prüft ob bullishes Regime.*
- @property `is_bearish_regime()` → `bool`  *Prüft ob bearishes Regime.*
- @property `is_ranging_regime()` → `bool`  *Prüft ob Range/Chop Regime.*
- *...3 private methods*
- `__post_init__()` → `None`  *Generiere Context-ID falls nicht gesetzt.*

## `src/core/trading_bot/market_context_signals.py`

### `SignalSnapshot(object)`
*Snapshot eines Trading-Signals.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*
- @property `is_tradeable()` → `bool`  *Prüft ob Signal tradeable ist (alle Gates passiert).*
- `get_final_score()` → `float`  *Berechnet finalen Score inkl. AI-Boost.*

## `src/core/trading_bot/position_monitor.py`

### `PositionMonitor(object)`
*Überwacht offene Positionen und triggert Exits (REFACTORED).*

- @property `has_position()` → `bool`  *Gibt True zurück wenn eine Position überwacht wird.*
- @property `position()` → `MonitoredPosition | None`  *Gibt aktuelle überwachte Position zurück.*
- `set_position(symbol, side, entry_price, quantity, stop_loss, take_profit, trailing_atr, trade_log)` → `MonitoredPosition`  *Setzt neue zu überwachende Position (delegiert).*
- `clear_position()` → `None`  *Löscht überwachte Position (delegiert).*
- `restore_position(position_data)` → `MonitoredPosition | None`  *Stellt Position aus gespeicherten Daten wieder her (delegiert).*
- async `on_price_update(price)` → `ExitResult | None`  *Wird bei jedem Preis-Update aufgerufen (delegiert).*
- `trigger_manual_exit(reason)` → `ExitResult`  *Triggert manuellen Exit (delegiert).*
- `trigger_session_end_exit()` → `ExitResult`  *Triggert Session-Ende Exit (delegiert).*
- `trigger_signal_exit(signal_reason)` → `ExitResult`  *Triggert Exit durch Signal-Umkehr (delegiert).*
- `set_exit_callback(callback)` → `None`  *Setzt Callback für Exit-Events (delegiert).*
- `set_trailing_callback(callback)` → `None`  *Setzt Callback für Trailing-Stop Updates (delegiert).*
- `set_price_callback(callback)` → `None`  *Setzt Callback für Preis-Updates (delegiert).*
- `get_position_status()` → `dict | None`  *Gibt aktuellen Position-Status zurück (delegiert).*
- `get_sl_tp_distance()` → `tuple[Decimal, Decimal] | None`  *Gibt aktuelle Distanz zu SL und TP zurück (delegiert).*
- `__init__(risk_manager, check_interval_ms)`  *Args:*

### `PositionMonitorService(object)`
*Service-Wrapper für PositionMonitor mit asyncio-Support.*

- async `start()` → `None`  *Startet den Monitor-Service.*
- async `stop()` → `None`  *Stoppt den Monitor-Service.*
- *...1 private methods*
- `__init__(monitor, price_provider)`  *Args:*

## `src/core/trading_bot/position_monitor_exit_checks.py`

### `PositionMonitorExitChecks(object)`
*Helper for exit condition checking.*

- `check_exit_conditions(price)` → `ExitResult`  *Prüft alle Exit-Bedingungen.*
- `trigger_manual_exit(reason)` → `ExitResult`  *Triggert manuellen Exit.*
- `trigger_session_end_exit()` → `ExitResult`  *Triggert Session-Ende Exit.*
- `trigger_signal_exit(signal_reason)` → `ExitResult`  *Triggert Exit durch Signal-Umkehr.*
- `__init__(parent)`

## `src/core/trading_bot/position_monitor_management.py`

### `PositionMonitorManagement(object)`
*Helper for position management.*

- `set_position(symbol, side, entry_price, quantity, stop_loss, take_profit, trailing_atr, trade_log)` → `MonitoredPosition`  *Setzt neue zu überwachende Position.*
- `clear_position()` → `None`  *Löscht überwachte Position.*
- `restore_position(position_data)` → `MonitoredPosition | None`  *Stellt Position aus gespeicherten Daten wieder her.*
- `__init__(parent)`

## `src/core/trading_bot/position_monitor_price.py`

### `PositionMonitorPrice(object)`
*Helper for price update handling.*

- async `on_price_update(price)` → `ExitResult | None`  *Wird bei jedem Preis-Update aufgerufen.*
- `__init__(parent)`

## `src/core/trading_bot/position_monitor_status.py`

### `PositionMonitorStatus(object)`
*Helper for callbacks and status queries.*

- `set_exit_callback(callback)` → `None`  *Setzt Callback für Exit-Events.*
- `set_trailing_callback(callback)` → `None`  *Setzt Callback für Trailing-Stop Updates.*
- `set_price_callback(callback)` → `None`  *Setzt Callback für Preis-Updates.*
- `get_position_status()` → `dict | None`  *Gibt aktuellen Position-Status zurück.*
- `get_sl_tp_distance()` → `tuple[Decimal, Decimal] | None`  *Gibt aktuelle Distanz zu SL und TP zurück.*
- `__init__(parent)`

## `src/core/trading_bot/position_monitor_trailing.py`

### `PositionMonitorTrailing(object)`
*Helper for trailing stop logic.*

- async `update_trailing_stop(price)` → `None`  *Aktualisiert Trailing Stop wenn nötig.*
- `__init__(parent)`

## `src/core/trading_bot/position_monitor_types.py`

### `ExitTrigger(str, Enum)`
*Grund für Position-Exit.*


### `MonitoredPosition(object)`
*Position mit Überwachungs-Details.*

- `update_price(price)` → `None`  *Aktualisiert Preis und berechnet PnL.*
- `to_dict()` → `dict`  *Serialisiert Position zu Dictionary für Persistenz.*
- @classmethod `from_dict(data)` → `'MonitoredPosition'`  *Deserialisiert Position aus Dictionary.*

### `ExitResult(object)`
*Ergebnis einer Exit-Prüfung.*


## `src/core/trading_bot/regime_detector.py`

### `RegimeDetectorService(object)`
*Shared Service für Marktregime-Erkennung (REFACTORED).*

- `detect(df)` → `RegimeResult`  *Erkennt Marktregime aus DataFrame.*
- `detect_from_values(ema_20, ema_50, adx, atr_pct, rsi, close)` → `RegimeResult`  *Erkennt Regime aus einzelnen Werten (ohne DataFrame).*
- `get_regime_gate_info(result)` → `dict`  *Gibt detaillierte Gate-Info für UI zurück (delegiert).*
- `__init__(config)`

### Module Functions
- `get_regime_detector(config)` → `RegimeDetectorService`  *Gibt globale Detector-Instanz zurück (Singleton).*
- `detect_regime(df)` → `RegimeResult`  *Convenience-Funktion für Regime-Erkennung.*
- `is_trending(df)` → `bool`  *Quick-Check ob Markt im Trend ist.*
- `is_ranging(df)` → `bool`  *Quick-Check ob Markt in Range/Chop ist.*

## `src/core/trading_bot/regime_detector_calculation.py`

### `RegimeDetectorCalculation(object)`
*Helper for regime calculation.*

- `calculate_regime(ema_alignment, adx_strength, volatility_state, momentum_state)` → `tuple[RegimeType, float, list[str]]`  *Berechnet finales Regime aus Komponenten.*
- `__init__(parent)`

## `src/core/trading_bot/regime_detector_components.py`

### `RegimeDetectorComponents(object)`
*Helper for component detection methods.*

- `determine_volatility_state(atr_pct)` → `str`  *Bestimmt Volatilitäts-Zustand.*
- `determine_ema_alignment(ema_20, ema_50, close)` → `str`  *Bestimmt EMA-Alignment.*
- `determine_adx_strength(adx)` → `str`  *Bestimmt ADX-Stärke.*
- `determine_momentum_state(rsi)` → `str`  *Bestimmt Momentum-Zustand.*
- `__init__(parent)`

## `src/core/trading_bot/regime_detector_gate_info.py`

### `RegimeDetectorGateInfo(object)`
*Helper for gate information.*

- `get_regime_gate_info(result)` → `dict`  *Gibt detaillierte Gate-Info für UI zurück.*
- `__init__(parent)`

## `src/core/trading_bot/regime_result.py`

### `RegimeResult(object)`
*Ergebnis der Regime-Erkennung.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*
- @property `allows_market_entry()` → `bool`  *Shortcut für Regime-Check.*
- @property `gate_reason()` → `str | None`  *Gibt Grund zurück, warum Market-Entry blockiert ist.*

### `RegimeConfig(object)`
*Konfiguration für Regime-Erkennung.*


## `src/core/trading_bot/regime_types.py`

### `RegimeType(str, Enum)`
*Marktregime-Typen.*

- @property `is_bullish()` → `bool`  *Prüft ob bullish.*
- @property `is_bearish()` → `bool`  *Prüft ob bearish.*
- @property `is_trending()` → `bool`  *Prüft ob Trend-Regime.*
- @property `is_ranging()` → `bool`  *Prüft ob Range/Chop.*
- @property `allows_market_entry()` → `bool`  *Prüft ob Market-Entries erlaubt sind.*

## `src/core/trading_bot/risk_calculation.py`

### `RiskCalculation(object)`
*Ergebnis einer Risiko-Berechnung.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

## `src/core/trading_bot/risk_manager.py`

### `RiskManager(object)`
*Verwaltet Risiko-Berechnungen und Position Sizing (REFACTORED).*

- `calculate_sl_tp(entry_price, side, atr)` → `tuple[Decimal, Decimal]`  *Berechnet Stop Loss und Take Profit (delegiert).*
- `calculate_position_size(balance, entry_price, stop_loss, risk_percent)` → `Decimal`  *Berechnet Position Size basierend auf Risiko (delegiert).*
- `calculate_full_risk(balance, entry_price, side, atr)` → `RiskCalculation`  *Berechnet vollständige Risiko-Analyse (delegiert).*
- `check_daily_loss_limit(balance)` → `tuple[bool, str]`  *Prüft ob Daily Loss Limit erreicht ist (delegiert).*
- `record_trade_result(pnl)` → `None`  *Zeichnet Trade-Ergebnis auf (delegiert).*
- `get_daily_stats()` → `dict`  *Gibt tägliche Statistiken zurück (delegiert).*
- `validate_trade(balance, entry_price, side, atr)` → `tuple[bool, str, RiskCalculation | None]`  *Validiert ob Trade durchgeführt werden darf (delegiert).*
- `adjust_sl_for_trailing(current_price, current_sl, entry_price, side, atr, activation_percent)` → `tuple[Decimal, bool]`  *Berechnet neuen Trailing Stop (delegiert).*
- `update_config(config)` → `None`  *Aktualisiert die Konfiguration zur Laufzeit (delegiert).*
- `update_strategy_config(strategy_config)` → `None`  *Aktualisiert die Strategie-Konfiguration zur Laufzeit (delegiert).*
- `__init__(config, strategy_config)`  *Args:*

## `src/core/trading_bot/risk_manager_config.py`

### `RiskManagerConfig(object)`
*Helper for config updates.*

- `update_config(config)` → `None`  *Aktualisiert die Konfiguration zur Laufzeit.*
- `update_strategy_config(strategy_config)` → `None`  *Aktualisiert die Strategie-Konfiguration zur Laufzeit.*
- `__init__(parent)`

## `src/core/trading_bot/risk_manager_daily_tracking.py`

### `RiskManagerDailyTracking(object)`
*Helper for daily loss tracking.*

- `check_daily_loss_limit(balance)` → `tuple[bool, str]`  *Prüft ob Daily Loss Limit erreicht ist.*
- `record_trade_result(pnl)` → `None`  *Zeichnet Trade-Ergebnis auf.*
- `get_daily_stats()` → `dict`  *Gibt tägliche Statistiken zurück.*
- *...1 private methods*
- `__init__(parent)`

## `src/core/trading_bot/risk_manager_init.py`

### `RiskManagerInit(object)`
*Helper for RiskManager initialization.*

- `initialize_config(config, strategy_config)` → `None`  *Initialize config from either strategy_config, config, or hardcoded defaults.*
- *...3 private methods*
- `__init__(parent)`

## `src/core/trading_bot/risk_manager_position_sizing.py`

### `RiskManagerPositionSizing(object)`
*Helper for position size calculation.*

- `calculate_position_size(balance, entry_price, stop_loss, risk_percent)` → `Decimal`  *Berechnet Position Size basierend auf Risiko.*
- `__init__(parent)`

## `src/core/trading_bot/risk_manager_risk_analysis.py`

### `RiskManagerRiskAnalysis(object)`
*Helper for full risk analysis.*

- `calculate_full_risk(balance, entry_price, side, atr)` → `RiskCalculation`  *Berechnet vollständige Risiko-Analyse.*
- `__init__(parent)`

## `src/core/trading_bot/risk_manager_sl_tp.py`

### `RiskManagerSLTP(object)`
*Helper for SL/TP calculation.*

- `calculate_sl_tp(entry_price, side, atr)` → `tuple[Decimal, Decimal]`  *Berechnet Stop Loss und Take Profit.*
- `__init__(parent)`

## `src/core/trading_bot/risk_manager_trade_validation.py`

### `RiskManagerTradeValidation(object)`
*Helper for trade validation.*

- `validate_trade(balance, entry_price, side, atr)` → `tuple[bool, str, RiskCalculation | None]`  *Validiert ob Trade durchgeführt werden darf.*
- `__init__(parent)`

## `src/core/trading_bot/risk_manager_trailing.py`

### `RiskManagerTrailing(object)`
*Helper for trailing stop calculation.*

- `adjust_sl_for_trailing(current_price, current_sl, entry_price, side, atr, activation_percent)` → `tuple[Decimal, bool]`  *Berechnet neuen Trailing Stop.*
- `__init__(parent)`

## `src/core/trading_bot/signal_generator.py`

### `SignalGenerator(object)`
*Generiert Trading-Signale basierend auf technischer Analyse (REFACTORED).*

- `generate_signal(df, regime, require_regime_alignment)` → `TradeSignal`  *Generiert Trading-Signal aus OHLCV DataFrame.*
- `check_exit_signal(df, current_position_side)` → `tuple[bool, str]`  *Prüft ob Exit-Signal für bestehende Position vorliegt (delegiert).*
- `extract_indicator_snapshot(df)` → `'IndicatorSnapshot'`  *Extrahiert Indikator-Snapshot aus DataFrame (delegiert).*
- *...2 private methods*
- `__init__(min_confluence)`  *Args:*

## `src/core/trading_bot/signal_generator_exit_signal.py`

### `SignalGeneratorExitSignal(object)`
*Helper for exit signal logic.*

- `check_exit_signal(df, current_position_side)` → `tuple[bool, str]`  *Prüft ob Exit-Signal für bestehende Position vorliegt.*
- `__init__(parent)`

## `src/core/trading_bot/signal_generator_indicator_snapshot.py`

### `SignalGeneratorIndicatorSnapshot(object)`
*Helper for indicator snapshot extraction using Field Extractor Pattern.*

- `extract_indicator_snapshot(df)` → `'IndicatorSnapshot'`  *Extrahiert Indikator-Snapshot aus DataFrame using Field Extractor Pattern.*
- *...1 private methods*
- `__init__(parent)`

## `src/core/trading_bot/signal_generator_long_conditions.py`

### `SignalGeneratorLongConditions(object)`
*Helper for long condition checks.*

- `check_long_conditions(df, current)` → `list[ConditionResult]`  *Prüft alle LONG Entry-Bedingungen.*
- `__init__(parent)`

## `src/core/trading_bot/signal_generator_short_conditions.py`

### `SignalGeneratorShortConditions(object)`
*Helper for short condition checks.*

- `check_short_conditions(df, current)` → `list[ConditionResult]`  *Prüft alle SHORT Entry-Bedingungen.*
- `__init__(parent)`

## `src/core/trading_bot/signal_types.py`

### `SignalDirection(str, Enum)`
*Signalrichtung.*


### `SignalStrength(str, Enum)`
*Signalstärke basierend auf Confluence.*


### `ConditionResult(object)`
*Ergebnis einer einzelnen Bedingungsprüfung.*


### `TradeSignal(object)`
*Trading-Signal mit allen Details.*

- @property `is_valid()` → `bool`  *Signal ist valid wenn confluence_score >= 3.*
- `get_conditions_summary()` → `dict[str, list[str]]`  *Gibt Zusammenfassung der Bedingungen zurück.*

## `src/core/trading_bot/snapshot_extractors/adx_extractor.py`

### `ADXExtractor(BaseFieldExtractor)`
*Extracts ADX indicator fields.*

- `extract(current, df)` → `Dict[str, Any]`  *Extract ADX fields.*

## `src/core/trading_bot/snapshot_extractors/atr_extractor.py`

### `ATRExtractor(BaseFieldExtractor)`
*Extracts ATR indicator fields.*

- `extract(current, df)` → `Dict[str, Any]`  *Extract ATR fields.*

## `src/core/trading_bot/snapshot_extractors/base_extractor.py`

### `BaseFieldExtractor(ABC)`
*Base class for indicator field extraction.*

- `extract(current, df)` → `Dict[str, Any]`  *Extract fields from current DataFrame row.*
- *...2 private methods*

## `src/core/trading_bot/snapshot_extractors/bollinger_extractor.py`

### `BollingerExtractor(BaseFieldExtractor)`
*Extracts Bollinger Bands indicator fields.*

- `extract(current, df)` → `Dict[str, Any]`  *Extract Bollinger Bands fields.*
- *...1 private methods*

## `src/core/trading_bot/snapshot_extractors/ema_extractor.py`

### `EMAExtractor(BaseFieldExtractor)`
*Extracts EMA indicator fields.*

- `extract(current, df)` → `Dict[str, Any]`  *Extract EMA fields.*

## `src/core/trading_bot/snapshot_extractors/extractor_registry.py`

### `FieldExtractorRegistry(object)`
*Registry for field extractors.*

- `register(extractor)` → `None`  *Register a field extractor.*
- `extract_all(df)` → `Dict[str, Any]`  *Extract all fields from DataFrame using registered extractors.*
- `__init__()`  *Initialize empty registry.*

## `src/core/trading_bot/snapshot_extractors/macd_extractor.py`

### `MACDExtractor(BaseFieldExtractor)`
*Extracts MACD indicator fields.*

- `extract(current, df)` → `Dict[str, Any]`  *Extract MACD fields.*
- *...1 private methods*

## `src/core/trading_bot/snapshot_extractors/price_extractor.py`

### `PriceTimestampExtractor(BaseFieldExtractor)`
*Extracts price and timestamp fields.*

- `extract(current, df)` → `Dict[str, Any]`  *Extract price and timestamp fields.*
- *...1 private methods*

## `src/core/trading_bot/snapshot_extractors/rsi_extractor.py`

### `RSIExtractor(BaseFieldExtractor)`
*Extracts RSI indicator fields.*

- `extract(current, df)` → `Dict[str, Any]`  *Extract RSI fields.*
- *...1 private methods*

## `src/core/trading_bot/snapshot_extractors/volume_extractor.py`

### `VolumeExtractor(BaseFieldExtractor)`
*Extracts volume indicator fields.*

- `extract(current, df)` → `Dict[str, Any]`  *Extract volume fields.*

## `src/core/trading_bot/strategy_config.py`

### `StrategyConfig(object)`
*Lädt und verwaltet Trading-Strategie aus JSON-Datei (REFACTORED).*

- `reload()` → `None`  *Lädt Konfiguration neu (für Hot-Reload).*
- `save(path)` → `None`  *Speichert aktuelle Konfiguration.*
- @property `strategy_name()` → `str`  *Name der Strategie.*
- @property `symbol()` → `str`  *Trading Symbol.*
- @property `enabled()` → `bool`  *Strategie aktiviert?*
- @property `exit_config()`  *Exit-Konfiguration.*
- @property `sl_type()` → `str`  *Stop Loss Type.*
- @property `sl_atr_multiplier()` → `float`  *Stop Loss ATR Multiplier.*
- @property `sl_percent()` → `float`  *Stop Loss Prozent.*
- @property `tp_type()` → `str`  *Take Profit Type.*
- @property `tp_atr_multiplier()` → `float`  *Take Profit ATR Multiplier.*
- @property `tp_percent()` → `float`  *Take Profit Prozent.*
- @property `trailing_stop_enabled()` → `bool`  *Trailing Stop aktiviert?*
- @property `trailing_stop_type()` → `str`  *Trailing Stop Type.*
- @property `trailing_stop_atr_multiplier()` → `float`  *Trailing Stop ATR Multiplier.*
- @property `trailing_stop_percent()` → `float`  *Trailing Stop Prozent.*
- @property `trailing_stop_activation_percent()` → `float`  *Trailing Stop Aktivierung.*
- @property `risk_config()`  *Risiko-Konfiguration.*
- @property `ai_config()`  *AI-Validation Konfiguration.*
- @property `filters()`  *Filter-Konfiguration.*
- @property `analysis_interval_seconds()` → `int`  *Analyse-Intervall.*
- @property `position_check_interval_ms()` → `int`  *Position-Check Intervall.*
- `get_timeframe(role)` → `TimeframeConfig | None`  *Gibt Timeframe-Config für Rolle zurück (macro, trend, context, execution).*
- @property `all_timeframes()` → `dict[str, TimeframeConfig]`  *Alle Timeframe-Konfigurationen.*
- `get_indicator_config(name)` → `IndicatorConfig | None`  *Gibt Indikator-Konfiguration zurück.*
- @property `enabled_indicators()` → `list[str]`  *Liste aktivierter Indikatoren.*
- `update_indicator_config(indicator_updates, save)` → `None`  *Update indicator configuration with new parameters.*
- `get_entry_conditions(direction)` → `EntryConditions`  *Gibt Entry-Bedingungen für Richtung zurück.*
- @property `min_confluence_long()` → `int`  *Minimum Confluence für Long Entry.*
- @property `min_confluence_short()` → `int`  *Minimum Confluence für Short Entry.*
- `evaluate_condition(condition, data, regime)` → `tuple[bool, str]`  *Evaluiert eine einzelne Bedingung.*
- `to_dict()` → `dict`  *Gibt gesamte Konfiguration als Dictionary zurück.*
- `update_parameter(path, value)` → `None`  *Aktualisiert einen Parameter.*
- *...2 private methods*
- `__init__(config_path)`  *Args:*

### Module Functions
- `get_strategy_config(config_path)` → `StrategyConfig`  *Gibt Singleton-Instanz der StrategyConfig zurück.*

## `src/core/trading_bot/strategy_config_dataclasses.py`

### `TimeframeConfig(object)`
*Konfiguration für einen Timeframe.*


### `IndicatorConfig(object)`
*Konfiguration für einen Indikator.*


### `ConditionRule(object)`
*Regel für eine Bedingung.*


### `EntryConditions(object)`
*Entry-Bedingungen für eine Richtung.*

- `get_enabled_conditions()` → `list[ConditionRule]`  *Gibt nur aktivierte Bedingungen zurück.*

### `ExitConfig(object)`
*Exit-Konfiguration.*


### `RiskConfig(object)`
*Risiko-Konfiguration.*


### `AIValidationConfig(object)`
*AI-Validation Konfiguration mit hierarchischer Validierung.*


### `FilterConfig(object)`
*Filter-Konfiguration.*


## `src/core/trading_bot/strategy_config_evaluation.py`

### `StrategyConfigEvaluation(object)`
*Helper für StrategyConfig condition evaluation.*

- `evaluate_condition(condition, data, regime)` → `tuple[bool, str]`  *Evaluiert eine einzelne Bedingung.*
- *...6 private methods*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/strategy_config_properties.py`

### `StrategyConfigProperties(object)`
*Helper für StrategyConfig @property methods.*

- @property `strategy_name()` → `str`  *Name der Strategie.*
- @property `symbol()` → `str`  *Trading Symbol.*
- @property `enabled()` → `bool`  *Strategie aktiviert?*
- @property `exit_config()` → `ExitConfig`  *Exit-Konfiguration.*
- @property `sl_type()` → `str`  *Stop Loss Type: 'atr_based' oder 'percent_based'.*
- @property `sl_atr_multiplier()` → `float`  *Stop Loss ATR Multiplier (nur für atr_based).*
- @property `sl_percent()` → `float`  *Stop Loss Prozent vom Entry (nur für percent_based).*
- @property `tp_type()` → `str`  *Take Profit Type: 'atr_based' oder 'percent_based'.*
- @property `tp_atr_multiplier()` → `float`  *Take Profit ATR Multiplier (nur für atr_based).*
- @property `tp_percent()` → `float`  *Take Profit Prozent vom Entry (nur für percent_based).*
- @property `trailing_stop_enabled()` → `bool`  *Trailing Stop aktiviert?*
- @property `trailing_stop_type()` → `str`  *Trailing Stop Type.*
- @property `trailing_stop_atr_multiplier()` → `float`  *Trailing Stop ATR Multiplier.*
- @property `trailing_stop_percent()` → `float`  *Trailing Stop Prozent Abstand (für percent_based).*
- @property `trailing_stop_activation_percent()` → `float`  *Trailing Stop Aktivierungsschwelle in Prozent.*
- @property `risk_config()` → `RiskConfig`  *Risiko-Konfiguration.*
- @property `ai_config()` → `AIValidationConfig`  *AI-Validation Konfiguration.*
- @property `filters()` → `FilterConfig`  *Filter-Konfiguration.*
- @property `analysis_interval_seconds()` → `int`  *Analyse-Intervall in Sekunden.*
- @property `position_check_interval_ms()` → `int`  *Position-Check Intervall in Millisekunden.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/trade_logger.py`

### `TradeLogger(object)`
*Manager für Trade-Logging.*

- `create_trade_log(symbol, bot_config)` → `TradeLogEntry`  *Erstellt einen neuen Trade-Log-Eintrag.*
- `save_trade_log(trade_log)` → `Path`  *Speichert Trade-Log auf Disk.*
- `update_trade_log(trade_log)` → `None`  *Aktualisiert existierenden Trade-Log.*
- `get_daily_summary(date)` → `dict`  *Erstellt Zusammenfassung für einen Tag.*
- `cleanup_old_logs(retention_days)` → `int`  *Löscht Logs älter als retention_days.*
- *...2 private methods*
- `__init__(log_directory, log_format)`

## `src/core/trading_bot/trade_logger_entry.py`

### `TradeLogEntry(object)`
*Vollständiger Log-Eintrag für einen Trade.*

- `add_note(note)` → `None`  *Fügt eine Notiz hinzu.*
- `record_trailing_stop_update(old_sl, new_sl, trigger_price)` → `None`  *Zeichnet Trailing-Stop Anpassung auf.*
- `calculate_pnl()` → `None`  *Berechnet P&L nach Trade-Schließung.*
- `calculate_duration()` → `None`  *Berechnet Trade-Dauer.*
- `to_dict()` → `dict`  *Konvertiert zu Dictionary (für JSON Export).*
- `to_markdown()` → `str`  *Generiert Markdown-Report für den Trade.*
- *...13 private methods*

## `src/core/trading_bot/trade_logger_state.py`

### `TradeOutcome(str, Enum)`
*Ergebnis eines Trades.*


### `ExitReason(str, Enum)`
*Grund für Trade-Exit.*


### `IndicatorSnapshot(object)`
*Snapshot aller Indikator-Werte zu einem Zeitpunkt.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

### `MarketContext(object)`
*Marktkontext zum Zeitpunkt des Trades.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

### `SignalDetails(object)`
*Details zur Signal-Generierung.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

### `TrailingStopHistory(object)`
*Historie der Trailing-Stop Anpassungen.*

- `to_dict()` → `dict`  *Konvertiert zu Dictionary.*

## `src/core/trading_bot/trade_logger_storage.py`

### `TradeLoggerStorage(object)`
*Helper für Trade-Log Storage (JSON/Markdown Persistence).*

- `save_trade_log(trade_log)` → `Path`  *Speichert Trade-Log auf Disk.*
- `update_trade_log(trade_log)` → `None`  *Aktualisiert existierenden Trade-Log.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/trade_logger_summary.py`

### `TradeLoggerSummary(object)`
*Helper für Daily Summary und Log Cleanup.*

- `get_daily_summary(date)` → `dict`  *Erstellt Zusammenfassung für einen Tag.*
- `cleanup_old_logs(retention_days)` → `int`  *Löscht Logs älter als retention_days.*
- `__init__(parent)`  *Args:*

## `src/core/trading_bot/trigger_exit_config.py`

### `TriggerExitConfig(object)`
*Configuration for Trigger and Exit Engine.*

- `to_dict()` → `Dict[str, Any]`  *Convert to dictionary.*
- @classmethod `from_dict(data)` → `'TriggerExitConfig'`  *Create from dictionary.*

### Module Functions
- `load_trigger_exit_config(path)` → `TriggerExitConfig`  *Load config from JSON file.*
- `save_trigger_exit_config(config, path)` → `bool`  *Save config to JSON file.*

## `src/core/trading_bot/trigger_exit_engine.py`

### `TriggerExitEngine(object)`
*Unified engine for entry triggers and exit management.*

- `evaluate_breakout_trigger(df, level, direction)` → `TriggerResult`  *Evaluate breakout trigger (delegated).*
- `evaluate_pullback_trigger(df, level, direction, atr)` → `TriggerResult`  *Evaluate pullback trigger (delegated).*
- `evaluate_sfp_trigger(df, level, direction)` → `TriggerResult`  *Evaluate SFP trigger (delegated).*
- `find_best_trigger(df, levels_result, entry_score, atr)` → `Optional[TriggerResult]`  *Find best trigger from available levels (delegated).*
- `calculate_exit_levels(entry_price, direction, atr, levels_result)` → `ExitLevels`  *Calculate all exit levels for a position (delegated).*
- `check_exit_conditions(current_price, exit_levels, entry_time, current_sl, entry_score)` → `ExitSignal`  *Check all exit conditions for a position.*
- `calculate_trailing_stop(current_price, current_sl, entry_price, direction, atr)` → `tuple[float, bool]`  *Calculate new trailing stop level.*
- `update_config(config)` → `None`  *Update engine configuration.*
- *...6 private methods*
- `__init__(config)`  *Initialize Trigger & Exit Engine.*

### Module Functions
- `get_trigger_exit_engine(config)` → `TriggerExitEngine`  *Get global TriggerExitEngine singleton.*

## `src/core/trading_bot/trigger_exit_types.py`

### `TriggerType(str, Enum)`
*Type of entry trigger.*


### `ExitType(str, Enum)`
*Type of exit.*


### `TriggerStatus(str, Enum)`
*Status of trigger evaluation.*


### `TriggerResult(object)`
*Result of trigger evaluation.*

- @property `is_triggered()` → `bool`
- `to_dict()` → `Dict[str, Any]`

### `ExitLevels(object)`
*Calculated exit levels for a position.*

- `to_dict()` → `Dict[str, Any]`

### `ExitSignal(object)`
*Signal to exit a position.*

- `to_dict()` → `Dict[str, Any]`

## `src/core/tradingbot/backtest_harness.py`

### `BacktestHarness(object)`
*Main backtest harness for tradingbot (REFACTORED).*

- `load_data()` → `pd.DataFrame`  *Load historical data for backtest (delegiert).*
- `run()` → `BacktestResult`  *Run the backtest (delegiert).*
- *...1 private methods*
- `__init__(bot_config, backtest_config, data_provider)`  *Initialize backtest harness.*

## `src/core/tradingbot/backtest_harness_bar_processor.py`

### `BacktestHarnessBarProcessor(object)`
*Helper for bar processing and state machine.*

- `process_bar(bar_idx)` → `None`  *Process a single bar.*
- *...3 private methods*
- `__init__(parent)`

## `src/core/tradingbot/backtest_harness_data_loader.py`

### `BacktestHarnessDataLoader(object)`
*Helper for loading historical data.*

- `load_data()` → `pd.DataFrame`  *Load historical data for backtest.*
- `__init__(parent)`

## `src/core/tradingbot/backtest_harness_execution.py`

### `BacktestHarnessExecution(object)`
*Helper for order execution and position management.*

- `execute_entry(signal, features)` → `None`  *Execute entry order.*
- `close_position(reason, exit_price)` → `None`  *Close current position.*
- `__init__(parent)`

## `src/core/tradingbot/backtest_harness_helpers.py`

### `BacktestHarnessHelpers(object)`
*Helper for calculation utilities.*

- `calculate_initial_stop(features, side, regime)` → `float`  *Calculate initial stop-loss price.*
- `calculate_equity()` → `float`  *Calculate current equity.*
- `calculate_metrics()` → `PerformanceMetrics`  *Calculate performance metrics from trades.*
- `__init__(parent)`

## `src/core/tradingbot/backtest_harness_runner.py`

### `BacktestHarnessRunner(object)`
*Helper for running the main backtest loop.*

- `run()` → `BacktestResult`  *Run the backtest.*
- `__init__(parent)`

## `src/core/tradingbot/backtest_metrics_helpers.py`

### Module Functions
- `convert_trades_to_results(trades)` → `list[TradeResult]`  *Convert BacktestTrade objects to TradeResult objects.*
- `calculate_backtest_metrics(trades)` → `PerformanceMetrics`  *Calculate performance metrics from backtest trades.*

## `src/core/tradingbot/backtest_simulator.py`

### `BacktestSimulator(object)`
*Simulates order execution during backtest.*

- `simulate_fill(side, quantity, price, bar_high, bar_low)` → `tuple[float, float, float]`  *Simulate order fill with slippage.*
- `generate_order_id()` → `str`  *Generate unique order ID.*
- `__init__(slippage_pct, commission_pct, seed)`  *Initialize simulator.*

### `ReleaseGate(object)`
*Release gate checker for Paper → Live transition.*

- `check(result)` → `tuple[bool, list[str]]`  *Check if result passes release gate.*
- *...1 private methods*
- `__init__(min_trades, min_win_rate, min_profit_factor, max_drawdown_pct, min_sharpe, min_paper_days, max_consecutive_losses)`  *Initialize release gate.*

## `src/core/tradingbot/backtest_types.py`

### `BacktestMode(str, Enum)`
*Backtest execution modes.*


### `BacktestConfig(object)`
*Configuration for backtest run.*

- `get_seed()` → `int`  *Get deterministic seed based on config.*

### `BacktestTrade(object)`
*Record of a completed trade.*

- `to_dict()` → `dict[str, Any]`  *Convert to dict for serialization.*

### `BacktestState(object)`
*State tracking during backtest.*


### `BacktestResult(object)`
*Result of a backtest run.*

- `to_dict()` → `dict[str, Any]`  *Convert to dict for serialization.*
- `save(path)` → `None`  *Save result to JSON file.*

## `src/core/tradingbot/bot_controller.py`

### `BotController(BotControllerState, BotControllerEvents, BotControllerLogic, BotStateHandlersMixin, BotSignalLogicMixin, BotTrailingStopsMixin, BotHelpersMixin)`
*Main trading bot controller.*

- async `on_bar(bar)` → `BotDecision | None`  *Process a new bar (candle close).*

## `src/core/tradingbot/bot_controller_events.py`

### `BotControllerEvents(object)`
*Event handling and lifecycle management for bot controller.*

- `start()` → `None`  *Start the bot.*
- `stop()` → `None`  *Stop the bot.*
- `pause(reason)` → `None`  *Pause the bot.*
- `resume()` → `None`  *Resume the bot.*
- `reset()` → `None`  *Reset bot to initial state.*
- `warmup_from_history(bars)` → `int`  *Pre-fill bar buffer with historical data for instant warmup.*
- `set_ki_mode(mode)` → `None`  *Set KI mode dynamically.*
- *...1 private methods*

## `src/core/tradingbot/bot_controller_logic.py`

### `BotControllerLogic(object)`
*Business logic for bot controller.*

- `force_strategy_reselection()` → `None`  *Force strategy re-selection on next bar.*
- `force_strategy_reselection_now()` → `str | None`  *Force immediate strategy re-selection.*
- @property `current_strategy()` → `StrategyProfile | None`  *Get current active strategy.*
- `get_strategy_selection()`  *Get current strategy selection result (if any).*
- `reload_json_config()` → `bool`  *Reload JSON configuration (if JSON catalog active).*
- `enable_multi_timeframe(timeframes, auto_resample)` → `None`  *Enable multi-timeframe analysis.*
- `disable_multi_timeframe()` → `None`  *Disable multi-timeframe analysis.*
- `get_multi_timeframe_data(timeframe, n)` → `dict[str, Any] | None`  *Get multi-timeframe data.*
- `enable_json_config_auto_reload()` → `bool`  *Enable automatic JSON config reloading with file watching.*
- `disable_json_config_auto_reload()` → `bool`  *Disable automatic JSON config reloading.*
- `is_json_config_auto_reload_enabled()` → `bool`  *Check if JSON config auto-reload is enabled.*
- `get_strategy_score_rows()` → `list[dict]`  *Get strategy score rows for UI display.*
- `get_walk_forward_config()`  *Get walk-forward configuration for UI display.*
- @property `last_regime()` → `RegimeState`  *Get last detected regime.*
- `set_json_config(json_config)` → `None`  *Set JSON config for regime-based strategy routing.*
- `set_initial_strategy(matched_strategy_set)` → `None`  *Set initial strategy from matched strategy set.*
- `set_json_entry_config(json_entry_config)` → `None`  *Set JSON Entry config (Regime-based CEL entry_expression).*
- `load_rulepack(rulepack_path)` → `bool`  *Load CEL RulePack from JSON file.*
- `get_rule_stats()` → `dict[str, Any]`  *Get rule profiling statistics.*
- `get_most_triggered_rules(top_n)` → `list[tuple[str, int]]`  *Get most frequently triggered rules.*
- `clear_rule_stats()` → `None`  *Clear rule profiling statistics.*
- *...5 private methods*

## `src/core/tradingbot/bot_controller_state.py`

### `BotControllerState(object)`
*State management for bot controller.*

- @property `state()` → `BotState`  *Current bot state.*
- @property `position()` → `PositionState | None`  *Current position.*
- @property `regime()` → `RegimeState`  *Current market regime.*
- @property `active_strategy()` → `StrategyProfile | None`  *Active strategy profile.*
- @property `is_running()` → `bool`  *Check if bot is running.*
- @property `can_trade()` → `bool`  *Check if bot can enter new trades.*
- `__init__(config, event_bus, on_signal, on_decision, on_order, on_log, on_trading_blocked, on_macd_signal, json_config_path, chart_window)`  *Initialize bot controller state.*

## `src/core/tradingbot/bot_helpers.py`

### `BotHelpersMixin(object)`
*Mixin providing helper methods for feature/regime/order operations.*

- `simulate_fill(fill_price, fill_qty, order_id)` → `None`  *Simulate order fill (for paper trading).*
- `to_dict()` → `dict[str, Any]`  *Serialize controller state.*
- *...8 private methods*

## `src/core/tradingbot/bot_settings_manager.py`

### `BotSettingsManager(object)`
*Manages persistent bot settings per symbol.*

- `get_settings(symbol)` → `dict[str, Any]`  *Get settings for a symbol.*
- `save_settings(symbol, settings)` → `None`  *Save settings for a symbol.*
- `get_all_symbols()` → `list[str]`  *Get list of all symbols with saved settings.*
- `delete_settings(symbol)` → `bool`  *Delete settings for a symbol.*
- *...2 private methods*
- `__init__(settings_file)`  *Initialize settings manager.*

### Module Functions
- `get_bot_settings_manager()` → `BotSettingsManager`  *Get the singleton settings manager instance.*

## `src/core/tradingbot/bot_signal_logic.py`

### `BotSignalLogicMixin(object)`
*Mixin providing signal scoring and creation methods.*

- *...9 private methods*

## `src/core/tradingbot/bot_state_handlers.py`

### `BotStateHandlersMixin(object)`
*Mixin providing state processing methods (REFACTORED).*

- *...2 private methods*
- `__init_state_handlers__()`  *Initialize state handler helpers (composition pattern).*

## `src/core/tradingbot/bot_state_handlers_dispatcher.py`

### `BotStateHandlersDispatcher(object)`
*Helper for main state dispatching.*

- async `process_state(features, bar)` → `BotDecision | None`  *Process current state and generate decision.*
- `__init__(parent)`

## `src/core/tradingbot/bot_state_handlers_exit.py`

### `BotStateHandlersExit(object)`
*Helper for exit handling.*

- async `handle_stop_hit(features)` → `BotDecision`  *Handle stop-loss hit.*
- async `handle_exit_signal(features, reason)` → `BotDecision`  *Handle exit signal.*
- `check_exit_signals(features)` → `str | None`  *Check for exit signals.*
- *...2 private methods*
- `__init__(parent)`

## `src/core/tradingbot/bot_state_handlers_flat.py`

### `BotStateHandlersFlat(object)`
*Helper for FLAT state processing.*

- async `process_flat(features)` → `BotDecision | None`  *Process FLAT state - look for entry signals.*
- async `check_strategy_selection(features)` → `None`  *Check and update daily bias for daytrading mode.*
- *...7 private methods*
- `__init__(parent)`

## `src/core/tradingbot/bot_state_handlers_manage.py`

### `BotStateHandlersManage(object)`
*Helper for MANAGE state processing.*

- async `process_manage(features, bar)` → `BotDecision | None`  *Process MANAGE state - manage open position.*
- *...5 private methods*
- `__init__(parent)`

## `src/core/tradingbot/bot_state_handlers_signal.py`

### `BotStateHandlersSignal(object)`
*Helper for SIGNAL state processing.*

- async `process_signal(features)` → `BotDecision | None`  *Process SIGNAL state - confirm or expire signal.*
- `__init__(parent)`

## `src/core/tradingbot/bot_test_suites.py`

### `BotUnitTests(object)`
*Unit tests for bot components.*

- `run_all()` → `TestSuiteResult`  *Run all unit tests.*
- `test_feature_vector_normalization()` → `None`  *Test FeatureVector.to_dict_normalized() returns valid values.*
- `test_trailing_state_never_loosen()` → `None`  *Test TrailingState enforces 'never loosen stop' invariant.*
- `test_regime_classification()` → `None`  *Test RegimeEngine classifies correctly.*
- `test_entry_scoring()` → `None`  *Test EntryScorer produces valid scores.*
- `test_exit_signal_detection()` → `None`  *Test ExitSignalChecker detects exit conditions.*
- `test_position_sizing()` → `None`  *Test PositionSizer calculates correct sizes.*
- `test_risk_limits()` → `None`  *Test RiskManager enforces limits.*
- `test_llm_response_validation()` → `None`  *Test LLMResponseValidator handles various inputs.*
- `__init__()`  *Initialize test suite.*

### `BotIntegrationTests(object)`
*Integration tests for bot workflow.*

- `run_all()` → `TestSuiteResult`  *Run all integration tests.*
- `test_full_trade_cycle()` → `None`  *Test complete trade cycle: signal -> entry -> manage -> exit.*
- `test_no_ki_mode_stability()` → `None`  *Test that NO_KI mode runs without LLM calls.*
- `test_trailing_stop_modes()` → `None`  *Test all trailing stop modes produce valid results.*
- `test_strategy_selection_flow()` → `None`  *Test daily strategy selection workflow.*
- `__init__()`  *Initialize test suite.*

### `ChaosTests(object)`
*Chaos/failure tests for resilience.*

- `run_all()` → `TestSuiteResult`  *Run all chaos tests.*
- `test_missing_data_handling()` → `None`  *Test handling of missing/NaN data.*
- `test_invalid_prices()` → `None`  *Test handling of invalid price data.*
- `test_extreme_volatility()` → `None`  *Test handling of extreme volatility.*
- `test_llm_failure_fallback()` → `None`  *Test LLM failure triggers fallback.*
- `test_zero_volume()` → `None`  *Test handling of zero volume bars.*
- `__init__()`  *Initialize test suite.*

## `src/core/tradingbot/bot_test_types.py`

### `TestResult(str, Enum)`
*Test result status.*


### `TestCase(object)`
*Individual test case result.*


### `TestSuiteResult(object)`
*Result of a test suite run.*

- @property `success()` → `bool`
- `add_result(test_case)` → `None`  *Add a test case result.*
- `summary()` → `str`  *Get summary string.*

### Module Functions
- `generate_mock_features(symbol, close, trend, volatility)` → `FeatureVector`  *Generate mock feature vector for testing.*
- `generate_mock_regime(regime_type, volatility)` → `RegimeState`  *Generate mock regime state.*

## `src/core/tradingbot/bot_tests.py`

### Module Functions
- `run_all_tests()` → `dict[str, TestSuiteResult]`  *Run all test suites.*

## `src/core/tradingbot/bot_trailing_stops.py`

### `BotTrailingStopsMixin(object)`
*Mixin providing trailing stop calculation methods.*

- *...4 private methods*

## `src/core/tradingbot/candle_preprocessing.py`

### Module Functions
- `_ensure_datetime_index(df)` → `pd.DataFrame`
- `_normalize_timezone(df, target_tz)` → `pd.DataFrame`
- `_sanitize_prices(df, price_cols)` → `pd.DataFrame`
- `_infer_frequency(index)` → `str | None`
- `_fill_missing_candles(df, price_cols)` → `pd.DataFrame`
- `_filter_stock_sessions(df)` → `pd.DataFrame`
- `preprocess_candles(data, market_type, target_tz, fill_missing, filter_sessions)` → `pd.DataFrame`  *Preprocess candles for feature calculation.*
- `detect_missing_candles(data, expected_freq)` → `list[datetime]`  *Detect timestamps where candles are missing.*
- `validate_candles(data)` → `dict`  *Validate candle data quality.*

## `src/core/tradingbot/cel/cel_validator.py`

### `ValidationSeverity(str, Enum)`
*Severity levels for validation errors.*


### `ValidationError(object)`
*Validation error with position information.*

- `to_dict()` → `Dict[str, Any]`  *Convert to JSON-serializable dictionary.*

### `TokenType(str, Enum)`
*CEL token types for lexical analysis.*


### `Token(object)`
*Lexical token with position.*


### `CelValidator(object)`
*CEL Expression Validator with lexer-based validation.*

- `validate(expression)` → `List[ValidationError]`  *Validate CEL expression and return list of errors.*
- `is_valid(expression)` → `bool`  *Quick validation check - returns True if expression is valid.*
- *...3 private methods*
- `__init__(custom_functions)`  *Initialize validator with optional custom functions.*

## `src/core/tradingbot/cel/context.py`

### `RuleContextBuilder(object)`
*Builds CEL evaluation context from FeatureVector and Trade state.*

- @staticmethod `build(features, trade, config, timeframe, additional_context)` → `dict[str, Any]`  *Build CEL context from feature vector and trade state.*
- @staticmethod `build_minimal(close, indicators)` → `dict[str, Any]`  *Build minimal context for testing.*
- *...1 private methods*

## `src/core/tradingbot/cel/engine.py`

### `CELEngine(object)`
*CEL Expression Engine with custom trading functions.*

- `compile(expression)` → `Any`  *Compile CEL expression with caching.*
- `evaluate(expression, context)` → `Any`  *Evaluate CEL expression with given context.*
- `evaluate_safe(expression, context, default)` → `Any`  *Evaluate CEL expression with fallback to default on error.*
- `validate_expression(expression)` → `tuple[bool, str]`  *Validate CEL expression syntax.*
- `clear_cache()` → `None`  *Clear compiled expression cache.*
- `get_cache_info()` → `dict[str, Any]`  *Get cache statistics.*
- *...1 private methods*
- `__init__(cache_size)`  *Initialize CEL Engine.*

### Module Functions
- `pctl(array, percentile)` → `float`  *Calculate percentile of array.*
- `isnull(value)` → `bool`  *Check if value is None/null.*
- `nz(value, default)` → `Any`  *Return value or default if null.*
- `coalesce()` → `Any`  *Return first non-null value.*

## `src/core/tradingbot/cel/executor.py`

### `ExecutionResult(Enum)`
*Result of rule execution.*


### `RuleResult(object)`
*Result of single rule evaluation.*

- `__str__()` → `str`

### `PackResult(object)`
*Result of pack evaluation.*

- `__str__()` → `str`

### `ExecutionSummary(object)`
*Summary of complete RulePack execution.*

- `__str__()` → `str`

### `RulePackExecutor(object)`
*Executes RulePacks with correct ordering and stop enforcement.*

- `execute(rulepack, context, pack_types)` → `ExecutionSummary`  *Execute RulePack with correct ordering.*
- `get_rule_stats(rule_id)` → `dict[str, Any]`  *Get rule profiling statistics.*
- `get_most_triggered_rules(top_n)` → `list[tuple[str, int]]`  *Get most frequently triggered rules.*
- `clear_stats()` → `None`  *Clear all rule profiling statistics.*
- *...3 private methods*
- `__init__(engine)`  *Initialize RulePack executor.*

### Module Functions
- `enforce_monotonic_stop(direction, current_stop, new_stop)` → `float`  *Enforce monotonic stop-loss updates.*

## `src/core/tradingbot/cel/loader.py`

### `RulePackLoader(object)`
*Loads and validates RulePack JSON files.*

- `load(json_path)` → `RulePack`  *Load and validate RulePack from JSON file.*
- `load_from_dict(data)` → `RulePack`  *Load RulePack from dict (already validated).*
- `save(rulepack, json_path)` → `None`  *Save RulePack to JSON file.*
- `__init__(validator)`  *Initialize RulePack loader.*

## `src/core/tradingbot/cel/models.py`

### `Rule(BaseModel)`
*A single CEL rule within a pack.*

- @classmethod `validate_expression_not_empty(v)` → `str`  *Ensure expression is not just whitespace.*

### `Pack(BaseModel)`
*A collection of rules for a specific purpose.*

- @classmethod `validate_rules_not_empty(v)` → `list[Rule]`  *Ensure at least one rule is present.*

### `RulePackMetadata(BaseModel)`
*Metadata for a RulePack.*


### `RulePack(BaseModel)`
*Complete RulePack with metadata and packs.*

- @classmethod `validate_packs_not_empty(v)` → `list[Pack]`  *Ensure at least one pack is present.*
- `get_pack(pack_type)` → `Optional[Pack]`  *Get pack by type.*
- `get_enabled_rules(pack_type)` → `list[Rule]`  *Get all enabled rules, optionally filtered by pack type.*
- `get_rules_by_severity(severity)` → `list[Rule]`  *Get all enabled rules with specific severity.*

## `src/core/tradingbot/cel_engine_ORIGINAL.py`

### `CELEngine(object)`
*CEL expression engine with custom trading functions.*

- `evaluate(expression, context, default)` → `Any`  *Evaluate CEL expression with context.*
- `evaluate_with_sources(expression, chart_window, bot_config, project_vars_path, indicators, regime, default, context_builder)` → `Any`  *Evaluate CEL expression with automatic context building from multiple sources.*
- `clear_cache()` → `None`  *Clear program compilation cache.*
- `get_cache_info()` → `dict[str, int] | None`  *Get cache statistics.*
- `validate_expression(expression)` → `tuple[bool, str | None]`  *Validate CEL expression syntax.*
- *...97 private methods*
- `__init__(enable_cache, cache_size)`  *Initialize CEL engine.*

### Module Functions
- `get_cel_engine()` → `CELEngine`  *Get or create default CEL engine instance.*

## `src/core/tradingbot/cel_engine_core.py`

### `CELEngine(object)`
*CEL expression engine with custom trading functions.*

- `evaluate(expression, context, default)` → `Any`  *Evaluate CEL expression with context.*
- `evaluate_with_sources(expression, chart_window, bot_config, project_vars_path, indicators, regime, default, context_builder)` → `Any`  *Evaluate CEL expression with automatic context building from multiple sources.*
- `clear_cache()` → `None`  *Clear program compilation cache.*
- `get_cache_info()` → `dict[str, int] | None`  *Get cache statistics.*
- `validate_expression(expression)` → `tuple[bool, str | None]`  *Validate CEL expression syntax.*
- *...4 private methods*
- `__init__(enable_cache, cache_size)`  *Initialize CEL engine.*

## `src/core/tradingbot/cel_engine_functions.py`

### `CELFunctions(object)`
*Container for all CEL custom functions.*

- *...95 private methods*
- `__init__(engine_instance)`  *Initialize CEL functions container.*

## `src/core/tradingbot/cel_engine_utils.py`

### `CELContextHelper(object)`
*Helper methods for CEL context value resolution.*

- `get_context_value(key)` → `Any`  *Resolve a value from the last evaluation context.*
- `context_flag()` → `bool`  *Return boolean flag for the first available key.*
- `__init__(engine_instance)`  *Initialize context helper.*

### Module Functions
- `get_cel_engine()` → `CELEngine`  *Get or create default CEL engine instance.*
- `reset_cel_engine()` → `None`  *Reset singleton CEL engine instance (primarily for testing).*

## `src/core/tradingbot/config/cli.py`

### Module Functions
- `cli()`  *TradingBot JSON Configuration CLI Tool.*
- `validate(config_path, verbose)`  *Validate a JSON configuration file.*
- `list_strategies(format)`  *List all available hardcoded strategies.*
- `convert(strategy_name, output, include_regime, include_set, pretty)`  *Convert a hardcoded strategy to JSON configuration.*
- `convert_multiple(strategy_names, output, pretty)`  *Convert multiple hardcoded strategies to a single JSON config.*
- `compare(config_path, strategy_name, strategy_id, verbose)`  *Compare JSON config against hardcoded strategy.*
- `_display_comparison_result(result, verbose)` → `None`  *Display comparison result with rich formatting.*
- `list_configs(directory, recursive)`  *List all JSON config files in a directory.*

## `src/core/tradingbot/config/detector.py`

### `ActiveRegime(object)`
*An active market regime with metadata.*

- @property `id()` → `str`  *Regime ID.*
- @property `name()` → `str`  *Regime name.*
- @property `priority()` → `int`  *Regime priority.*
- @property `scope()` → `RegimeScope | None`  *Regime scope.*
- `__post_init__()`  *Set activation timestamp if not provided.*
- `__repr__()` → `str`

### `RegimeDetector(object)`
*Detects active market regimes from indicator values.*

- `detect_active_regimes(indicator_values, scope)` → `list[ActiveRegime]`  *Detect all active regimes for current market conditions.*
- `get_highest_priority_regime(indicator_values, scope)` → `ActiveRegime | None`  *Get the single highest-priority active regime.*
- `is_regime_active(regime_id, indicator_values)` → `bool`  *Check if a specific regime is currently active.*
- `get_active_regimes_by_scope(indicator_values)` → `dict[str, list[ActiveRegime]]`  *Get active regimes grouped by scope.*
- `get_regime_definition(regime_id)` → `RegimeDefinition | None`  *Get regime definition by ID.*
- `__init__(regime_definitions)`  *Initialize detector with regime definitions.*

## `src/core/tradingbot/config/evaluator.py`

### `ConditionEvaluationError(Exception)`
*Exception raised when condition evaluation fails.*


### `ConditionEvaluator(object)`
*Evaluates conditions against indicator values.*

- `evaluate_condition(condition)` → `bool`  *Evaluate single comparison condition.*
- `evaluate_group(group)` → `bool`  *Evaluate condition group (all/any logic).*
- `evaluate_multiple_groups(groups, mode)` → `bool`  *Evaluate multiple condition groups.*
- *...1 private methods*
- `__init__(indicator_values, enable_cel)`  *Initialize evaluator with indicator values.*

## `src/core/tradingbot/config/executor.py`

### `ExecutionContext(object)`
*Context for strategy set execution.*

- `__repr__()` → `str`

### `StrategySetExecutor(object)`
*Executes strategy sets with parameter overrides.*

- `prepare_execution(matched_strategy_set)` → `ExecutionContext`  *Prepare strategy set for execution with overrides.*
- `restore_state(context)` → `None`  *Restore original state after execution.*
- `get_current_indicator(indicator_id)` → `IndicatorDefinition | None`  *Get current indicator definition (with overrides applied).*
- `get_current_strategy(strategy_id)` → `StrategyDefinition | None`  *Get current strategy definition (with overrides applied).*
- `get_strategy_ids_from_set(strategy_set)` → `list[str]`  *Extract strategy IDs from strategy set.*
- `reset_to_original()` → `None`  *Reset all state to original (remove all overrides).*
- *...2 private methods*
- `__init__(indicators, strategies)`  *Initialize executor with original indicators and strategies.*

## `src/core/tradingbot/config/loader.py`

### `ConfigLoadError(Exception)`
*Exception raised when config loading fails.*


### `ConfigLoader(object)`
*Loads and validates JSON strategy configurations.*

- `load_config(config_path)` → `TradingBotConfig`  *Load and validate configuration from JSON file.*
- `validate_config_data(config_data)` → `TradingBotConfig`  *Validate raw config dict (without file I/O).*
- `list_configs(directory)` → `list[Path]`  *List all JSON config files in directory.*
- `load_all_configs(directory)` → `dict[str, TradingBotConfig]`  *Load all valid configs from directory.*
- `save_config(config, output_path, indent, validate)` → `None`  *Save configuration to JSON file.*
- *...1 private methods*
- `__init__(schema_path)`  *Initialize ConfigLoader with JSON Schema.*

### Module Functions
- `_prune_nones(data)` → `Any`  *Remove None-valued keys from dictionaries recursively.*

## `src/core/tradingbot/config/models.py`

### `ConditionOperator(str, Enum)`
*Comparison operators for condition evaluation.*


### `RegimeScope(str, Enum)`
*Scope of regime applicability.*


### `IndicatorType(str, Enum)`
*Supported technical indicator types.*

- *...1 private methods*

### `IndicatorDefinition(BaseModel)`
*Technical indicator definition with parameters.*

- @classmethod `validate_params(v)` → `dict[str, Any]`  *Validate that params is not empty.*

### `IndicatorRef(BaseModel)`
*Reference to an indicator output field.*


### `ConditionLeft(IndicatorRef)`
*Backward-compatible left operand wrapper used by older tests/configs.*


### `ConstantValue(BaseModel)`
*Constant numeric value.*


### `BetweenRange(BaseModel)`
*Range for 'between' operator.*

- @classmethod `validate_range(v, info)` → `float`  *Ensure max > min.*

### `ConditionRight(BaseModel)`
*Backward-compatible right operand wrapper.*

- `validate_payload()` → `'ConditionRight'`  *Ensure one operand mode is provided.*

### `Condition(BaseModel)`
*Single comparison condition.*

- `validate_condition_mode()` → `'Condition'`  *Ensure either operator-based OR CEL expression is provided, not both.*
- @classmethod `validate_right_operand(v, info)` → `IndicatorRef | ConstantValue | BetweenRange | None`  *Ensure right operand matches operator type.*

### `ConditionGroup(BaseModel)`
*Group of conditions with AND/OR logic. Supports recursive nesting.*

- `validate_group()` → `'ConditionGroup'`  *Ensure at least one of 'all' or 'any' is specified (but not both).*
- `__getitem__(item)`
- `__setitem__(key, value)`

### `RegimeDefinition(BaseModel)`
*Market regime definition with activation conditions.*


### `RiskSettings(BaseModel)`
*Risk management parameters.*


### `StrategyDefinition(BaseModel)`
*Trading strategy definition with entry/exit rules.*


### `StrategyReference(BaseModel)`
*Reference to a strategy with optional overrides.*


### `IndicatorOverride(BaseModel)`
*Indicator parameter override for strategy set.*


### `StrategySetDefinition(BaseModel)`
*Strategy set (bundle of strategies) with overrides.*

- @classmethod `validate_strategies(v)` → `list[StrategyReference]`  *Ensure at least one strategy in set.*

### `RoutingMatch(BaseModel)`
*Regime matching criteria for routing.*

- `validate_match()` → `'RoutingMatch'`  *Ensure at least one matching criterion is specified.*

### `RoutingRule(BaseModel)`
*Routing rule mapping regimes to strategy set.*


### `ConfigMetadata(BaseModel)`
*Configuration metadata.*


### `TradingBotConfig(BaseModel)`
*Root configuration model for Regime-Based JSON Strategy System.*

- @classmethod `validate_indicators(v)` → `list[IndicatorDefinition]`  *Ensure indicator IDs are unique.*
- @classmethod `validate_regimes(v)` → `list[RegimeDefinition]`  *Ensure regime IDs are unique.*
- @classmethod `validate_strategies(v)` → `list[StrategyDefinition]`  *Ensure strategy IDs are unique.*
- @classmethod `validate_strategy_sets(v)` → `list[StrategySetDefinition]`  *Ensure strategy set IDs are unique.*

## `src/core/tradingbot/config/regime_loader_v2.py`

### `RegimeConfigLoadError(Exception)`
*Exception raised when regime config loading fails.*


### `RegimeConfigLoaderV2(object)`
*Loads and validates v2.0 Regime configuration files.*

- `load_config(config_path)` → `dict[str, Any]`  *Load and validate v2.0 regime configuration from JSON file.*
- `validate_config_data(config_data)` → `dict[str, Any]`  *Validate raw config dict (without file I/O).*
- `save_config(config_data, output_path, indent, validate)` → `None`  *Save configuration to JSON file.*
- `get_applied_result(config_data)` → `dict[str, Any] | None`  *Get the currently applied optimization result.*
- `get_indicators(config_data)` → `list[dict[str, Any]]`  *Get indicators from the applied optimization result.*
- `get_regimes(config_data)` → `list[dict[str, Any]]`  *Get regimes from the applied optimization result.*
- *...1 private methods*
- `__init__(schema_path)`  *Initialize RegimeConfigLoaderV2 with JSON Schema.*

### Module Functions
- `_prune_nones(data)` → `Any`  *Remove None-valued keys from dictionaries recursively.*

## `src/core/tradingbot/config/router.py`

### `MatchedStrategySet(object)`
*A strategy set matched by routing rules.*

- @property `id()` → `str`  *Strategy set ID.*
- @property `name()` → `str`  *Strategy set name.*
- `__repr__()` → `str`

### `StrategyRouter(object)`
*Routes active regimes to strategy sets based on routing rules.*

- `route_regimes(active_regimes)` → `list[MatchedStrategySet]`  *Route active regimes to strategy sets.*
- `get_strategy_set(strategy_set_id)` → `StrategySetDefinition | None`  *Get strategy set definition by ID.*
- `get_all_strategy_sets()` → `list[StrategySetDefinition]`  *Get all registered strategy sets.*
- `get_routing_rules_for_regime(regime_id)` → `list[RoutingRule]`  *Get all routing rules that reference a specific regime.*
- `validate_routing_rules()` → `list[str]`  *Validate all routing rules.*
- *...1 private methods*
- `__init__(routing_rules, strategy_sets)`  *Initialize router with routing rules and strategy sets.*

## `src/core/tradingbot/config/validator.py`

### `ValidationError(Exception)`
*Custom validation error with detailed information.*

- `__init__(message, json_path, schema_rule, original_error)`
- `__str__()` → `str`

### `SchemaValidator(object)`
*Validates JSON data against JSON Schema specifications.*

- `validate_data(data, schema_name)` → `None`  *Validate data against JSON schema.*
- `validate_file(json_path, schema_name)` → `dict[str, Any]`  *Validate JSON file against schema.*
- `list_available_schemas()` → `list[str]`  *List all available schema names.*
- *...1 private methods*
- `__init__(schemas_dir)`  *Initialize validator.*

### Module Functions
- `validate_json_file(json_path, schema_name)` → `dict[str, Any]`  *Convenience function to validate a JSON file.*

## `src/core/tradingbot/config.py`

### `MarketType(str, Enum)`
*Supported market types.*


### `KIMode(str, Enum)`
*KI operation modes.*


### `TrailingMode(str, Enum)`
*Trailing stop modes.*


### `TradingEnvironment(str, Enum)`
*Trading environment.*


### `BotConfig(BaseModel)`
*Main bot configuration.*

- @classmethod `validate_symbol(v)` → `str`  *Normalize symbol to uppercase.*

### `RiskConfig(BaseModel)`
*Risk management configuration.*

- @classmethod `crypto_defaults()` → `'RiskConfig'`  *Get conservative defaults for crypto trading.*
- @classmethod `nasdaq_defaults()` → `'RiskConfig'`  *Get conservative defaults for NASDAQ trading.*

### `LLMPolicyConfig(BaseModel)`
*LLM/KI call policy configuration.*


### `FullBotConfig(BaseModel)`
*Complete bot configuration combining all config types.*

- @classmethod `create_default(symbol, market_type)` → `'FullBotConfig'`  *Create default configuration for a symbol.*

## `src/core/tradingbot/config_integration_bridge.py`

### `IndicatorValueCalculator(object)`
*Calculates indicator values from FeatureVector for condition evaluation.*

- @classmethod `calculate_indicator_values(feature_vector)` → `dict[str, dict[str, float]]`  *Calculate indicator values from FeatureVector.*

### `RegimeDetectorBridge(object)`
*Bridge between JSON-based RegimeDetector and existing RegimeState.*

- `detect_regime_from_features(feature_vector)` → `RegimeState`  *Detect market regime from feature vector.*
- `__init__(regime_detector)`  *Initialize bridge with JSON-based regime detector.*

### `ConfigBasedStrategyCatalog(object)`
*Alternative to hardcoded StrategyCatalog using JSON config.*

- `get_active_strategy_sets(feature_vector)` → `list[MatchedStrategySet]`  *Get active strategy sets for current market conditions.*
- `get_current_regime(feature_vector)` → `RegimeState`  *Get current market regime as RegimeState.*
- `get_strategy_ids_from_sets(matched_sets)` → `list[str]`  *Extract strategy IDs from matched strategy sets.*
- `get_strategy(strategy_id)` → `StrategyDefinition | None`  *Get strategy by ID (for compatibility).*
- `get_all_strategies()` → `list[StrategyDefinition]`  *Get all strategies (for compatibility).*
- `list_strategies()` → `list[str]`  *List all strategy IDs.*
- `list_strategy_sets()` → `list[str]`  *List all strategy set IDs.*
- `list_regimes()` → `list[str]`  *List all regime IDs.*
- `reload_config(new_config)` → `None`  *Reload configuration (thread-safe).*
- `enable_auto_reload(config_path, schema_path, event_bus)` → `None`  *Enable automatic config reloading with file watching.*
- `disable_auto_reload()` → `None`  *Disable automatic config reloading.*
- `__init__(config, feature_vector, config_reloader)`  *Initialize catalog from JSON config.*

### Module Functions
- `load_json_config_if_available(config_path)` → `TradingBotConfig | None`  *Load JSON config if available, otherwise return None.*
- `create_strategy_catalog(feature_vector, json_config_path)` → `ConfigBasedStrategyCatalog | None`  *Factory function: Create strategy catalog from JSON or fallback to hardcoded.*

## `src/core/tradingbot/config_reloader.py`

### `ConfigReloadError(Exception)`
*Exception raised when config reload fails.*


### `ConfigFileHandler(FileSystemEventHandler)`
*File system event handler for config file changes.*

- `on_modified(event)` → `None`  *Handle file modification event.*
- `__init__(config_path, reload_callback, debounce_seconds)`  *Initialize file handler.*

### `ConfigReloader(object)`
*Thread-safe configuration reloader with file watching.*

- @property `current_config()` → `TradingBotConfig`  *Get current configuration (thread-safe).*
- `reload_config(notify)` → `TradingBotConfig`  *Reload configuration from file (thread-safe).*
- `start_watching()` → `None`  *Start automatic file watching.*
- `stop_watching()` → `None`  *Stop automatic file watching.*
- `is_watching()` → `bool`  *Check if file watching is active.*
- *...2 private methods*
- `__init__(config_path, schema_path, on_reload, event_bus, auto_reload, debounce_seconds)`  *Initialize config reloader.*
- `__enter__()` → `'ConfigReloader'`  *Context manager entry.*
- `__exit__(exc_type, exc_val, exc_tb)` → `None`  *Context manager exit.*

## `src/core/tradingbot/entry_exit_engine.py`

### `TrailingStopResult(object)`
*Result of trailing stop calculation.*


### `TrailingStopManager(object)`
*Manages trailing stop updates for positions.*

- `calculate_trailing_stop(features, position, regime, current_bar)` → `TrailingStopResult`  *Calculate new trailing stop price.*
- *...3 private methods*
- `__init__(min_step_pct, update_cooldown_bars, activation_pct)`  *Initialize trailing stop manager.*

### `EntryExitEngine(object)`
*Unified engine for entry/exit decisions.*

- `evaluate_entry(features, regime, strategy)` → `tuple[EntryScoreResult, EntryScoreResult]`  *Evaluate entry scores for both sides.*
- `check_exit(features, position, regime, previous_regime, strategy)` → `ExitSignalResult`  *Check for exit signals.*
- `update_trailing_stop(features, position, regime, current_bar)` → `TrailingStopResult`  *Update trailing stop.*
- `__init__(entry_scorer, exit_checker, trailing_manager)`  *Initialize entry/exit engine.*

## `src/core/tradingbot/entry_scorer.py`

### `EntryScoreResult(object)`
*Result of entry score calculation.*


### `EntryScorer(object)`
*Calculates entry scores based on strategy rules and indicators.*

- `calculate_score(features, side, regime, strategy)` → `EntryScoreResult`  *Calculate entry score for a side.*
- *...14 private methods*
- `__init__(weights)`  *Initialize entry scorer.*

## `src/core/tradingbot/evaluator_aggregation.py`

### `EvaluatorAggregation(object)`
*Helper für StrategyEvaluator metrics aggregation.*

- `aggregate_metrics(metrics_list)` → `PerformanceMetrics`  *Aggregate metrics from multiple periods.*
- `sum_trade_totals(agg, metrics_list)` → `None`  *Sum total trades and profits/losses.*
- `calculate_derived_metrics(agg)` → `None`  *Calculate win rate, profit factor, averages, and expectancy.*
- `aggregate_drawdowns_and_streaks(agg, metrics_list)` → `None`  *Aggregate drawdowns, streaks, and average bars held.*
- `aggregate_date_range(agg, metrics_list)` → `None`  *Aggregate start and end dates.*
- `__init__(parent)`  *Args:*

## `src/core/tradingbot/evaluator_comparison.py`

### `EvaluatorComparison(object)`
*Helper für StrategyEvaluator strategy comparison.*

- `compare_strategies(results)` → `list[tuple[str, float]]`  *Rank strategies by composite score.*
- `__init__(parent)`  *Args:*

## `src/core/tradingbot/evaluator_metrics.py`

### `EvaluatorMetrics(object)`
*Helper für StrategyEvaluator metrics calculation.*

- `calculate_metrics(trades, initial_capital, sample_type)` → `PerformanceMetrics`  *Calculate performance metrics from trade results.*
- `calculate_drawdown(trades, initial_capital, metrics)` → `None`  *Calculate maximum drawdown.*
- `calculate_consecutive_streaks(trades, metrics)` → `None`  *Calculate consecutive win/loss streaks.*
- `calculate_risk_ratios(trades, metrics)` → `None`  *Calculate Sharpe, Sortino, Calmar ratios.*
- `__init__(parent)`  *Args:*

## `src/core/tradingbot/evaluator_periods.py`

### `EvaluatorPeriods(object)`
*Helper für StrategyEvaluator period generation.*

- `generate_rolling_periods(start_date, end_date, config)` → `list[tuple[datetime, datetime, datetime, datetime]]`  *Generate rolling window periods.*
- `generate_anchored_periods(start_date, end_date, config)` → `list[tuple[datetime, datetime, datetime, datetime]]`  *Generate anchored (expanding) window periods.*
- `calculate_oos_degradation(is_metrics, oos_metrics)` → `float`  *Calculate performance degradation from IS to OOS.*
- `__init__(parent)`  *Args:*

## `src/core/tradingbot/evaluator_types.py`

### `TradeResult(object)`
*Result of a single trade.*


### `PerformanceMetrics(object)`
*Performance metrics for a strategy evaluation period.*

- `is_robust(min_trades, min_profit_factor, max_drawdown_pct, min_win_rate)` → `bool`  *Check if metrics meet robustness criteria.*

### `RobustnessGate(BaseModel)`
*Configuration for robustness validation.*


### `WalkForwardConfig(BaseModel)`
*Configuration for walk-forward analysis.*


### `WalkForwardResult(object)`
*Result of walk-forward analysis.*

- `get_degradation_pct()` → `float`  *Calculate performance degradation from IS to OOS.*

### `RobustnessReport(object)`
*Robustness validation report for strategy walk-forward analysis.*

- `get_status_summary()` → `str`  *Get human-readable status summary.*
- `get_recommendation()` → `str`  *Get trading recommendation based on validation.*

## `src/core/tradingbot/evaluator_validation.py`

### `EvaluatorValidation(object)`
*Helper für StrategyEvaluator robustness validation.*

- `validate_robustness(metrics, gate)` → `tuple[bool, list[str]]`  *Validate metrics against robustness criteria.*
- `validate_strategy_robustness(walk_forward_result, min_trades, max_drawdown_threshold, min_sharpe, max_degradation_pct)` → `RobustnessReport`  *Validate strategy robustness using walk-forward results.*
- `__init__(parent)`  *Args:*

## `src/core/tradingbot/evaluator_visualization.py`

### `EvaluatorVisualization(object)`
*Helper for StrategyEvaluator visualization.*

- `create_walk_forward_charts(walk_forward_result, robustness_report)` → `Figure`  *Create comprehensive walk-forward validation charts.*
- `save_chart_to_bytes(fig)` → `bytes`  *Save matplotlib figure to bytes (PNG format).*
- `save_chart_to_file(fig, path)` → `None`  *Save matplotlib figure to file.*
- *...4 private methods*
- `__init__(parent)`  *Args:*

## `src/core/tradingbot/evaluator_walk_forward.py`

### `EvaluatorWalkForward(object)`
*Helper für StrategyEvaluator walk-forward analysis.*

- `run_walk_forward(strategy, all_trades, config)` → `WalkForwardResult`  *Run walk-forward analysis on strategy.*
- `empty_walk_forward_result(strategy, config)` → `WalkForwardResult`
- `trade_date_range(trades)` → `tuple[datetime, datetime, int]`
- `insufficient_history(total_days, config)` → `bool`
- `get_walk_forward_periods(start_date, end_date, config)` → `list[tuple[datetime, datetime, datetime, datetime]]`
- `slice_trades_for_period(trades, train_start, train_end, test_start, test_end)` → `tuple[list[TradeResult], list[TradeResult]]`
- `period_passed(is_metrics, oos_metrics)` → `bool`
- `is_overall_robust(agg_is_metrics, agg_oos_metrics)` → `bool`
- `simple_train_test_split(strategy, trades, config)` → `WalkForwardResult`  *Simple 70/30 train/test split when not enough history.*
- `__init__(parent)`  *Args:*

## `src/core/tradingbot/execution.py`

### `PaperExecutor(object)`
*Paper trading executor with slippage simulation.*

- `execute(order, current_price)` → `OrderResult`  *Execute an order (paper).*
- `cancel(order_id)` → `OrderResult`  *Cancel an order.*
- `get_order(order_id)` → `OrderResult | None`  *Get order result by ID.*
- `__init__(slippage_pct, fill_probability, partial_fill_probability, latency_ms, fee_pct)`  *Initialize paper executor.*

### `ExecutionGuardrails(object)`
*Safety guardrails for order execution.*

- `validate(order, current_price)` → `tuple[bool, list[str]]`  *Validate an order before execution.*
- `record_order(order)` → `None`  *Record an executed order for tracking.*
- `clear_signal(signal_id)` → `None`  *Clear a signal from pending.*
- *...1 private methods*
- `__init__(max_order_value, max_order_quantity, min_order_value, rate_limit_per_minute, require_stop_loss, prevent_duplicates)`  *Initialize guardrails.*

### `OrderExecutor(object)`
*Unified order executor supporting paper and live modes.*

- `execute_entry(signal, current_price, atr)` → `OrderResult`  *Execute an entry order.*
- `execute_exit(symbol, side, quantity, current_price, reason)` → `OrderResult`  *Execute an exit order.*
- `record_trade_pnl(pnl)` → `None`  *Record trade P&L for risk tracking.*
- `update_account_value(value)` → `None`  *Update account value.*
- `get_risk_stats()` → `dict[str, Any]`  *Get current risk statistics.*
- `is_trading_allowed()` → `bool`  *Check if trading is allowed.*
- `__init__(environment, account_value, risk_limits, guardrails, on_fill)`  *Initialize order executor.*

## `src/core/tradingbot/execution_types.py`

### `OrderStatus(str, Enum)`
*Order status.*


### `OrderType(str, Enum)`
*Order types.*


### `OrderResult(object)`
*Result of order execution.*

- @property `is_filled()` → `bool`
- @property `is_rejected()` → `bool`

### `PositionSizeResult(object)`
*Result of position size calculation.*


### `RiskLimits(BaseModel)`
*Risk limit configuration.*


### `RiskState(BaseModel)`
*Current risk tracking state.*


## `src/core/tradingbot/exit_checker.py`

### `ExitReason(str, Enum)`
*Exit signal reasons.*


### `ExitSignalResult(object)`
*Result of exit signal check.*


### `ExitSignalChecker(object)`
*Checks for exit signals based on multiple criteria.*

- `check_exit(features, position, regime, previous_regime, strategy)` → `ExitSignalResult`  *Check all exit conditions.*
- *...7 private methods*
- `__init__(max_bars_held, rsi_extreme_threshold, enable_time_stop)`  *Initialize exit signal checker.*

## `src/core/tradingbot/feature_engine.py`

### `FeatureEngine(object)`
*Engine for calculating features from market data.*

- `calculate_features(data, symbol, timestamp)` → `FeatureVector | None`  *Calculate feature vector from OHLCV data.*
- `preprocess_candles(data)` → `pd.DataFrame`  *Preprocess candles for feature calculation. Delegates to module function.*
- `detect_missing_candles(data, expected_freq)` → `list[datetime]`  *Detect missing candles. Delegates to module function.*
- `validate_candles(data)` → `dict`  *Validate candle data. Delegates to module function.*
- `get_required_bars()` → `int`  *Get minimum bars required for feature calculation.*
- `clear_cache()` → `None`  *Clear indicator cache.*
- *...14 private methods*
- `__init__(indicator_engine, periods)`  *Initialize feature engine.*

## `src/core/tradingbot/indicator_config_generator.py`

### `IndicatorConfigGenerator(object)`
*Generates JSON configs from optimization results.*

- `generate_regime_config(regime_id, optimization_results, output_path, strategy_name)` → `dict[str, Any]`  *Generate complete JSON config for a specific regime.*
- `save_config(config, output_path)` → `None`  *Save config to JSON file.*
- `generate_batch_configs(optimization_results_by_regime, output_dir)` → `dict[str, str]`  *Generate configs for multiple regimes.*
- *...9 private methods*
- `__init__()`  *Initialize config generator.*

## `src/core/tradingbot/indicator_grid_search.py`

### `ParameterCombination(object)`
*Single parameter combination for an indicator.*


### `GridSearchConfig(object)`
*Configuration for grid search.*


### `IndicatorGridSearch(object)`
*Generates parameter combinations for indicator optimization.*

- `load_catalog(path)` → `None`  *Load indicator catalog from YAML file.*
- `get_indicator_definition(indicator_type)` → `dict | None`  *Get indicator definition from catalog.*
- `generate_combinations(indicator_type, config)` → `list[ParameterCombination]`  *Generate all parameter combinations for an indicator.*
- `generate_batch(indicator_types, config)` → `dict[str, list[ParameterCombination]]`  *Generate combinations for multiple indicators.*
- `get_regime_compatible_indicators(regime_id, min_score)` → `list[str]`  *Get list of indicators compatible with a regime.*
- `get_recommended_indicators(regime_id)` → `dict[str, list[str]]`  *Get recommended indicators for a regime.*
- *...2 private methods*
- `__init__(catalog_path)`  *Initialize grid search engine.*

## `src/core/tradingbot/indicator_optimizer.py`

### `IndicatorScore(object)`
*Performance score for an indicator parameter combination.*


### `IndicatorOptimizer(object)`
*Optimizes indicator parameters using backtest-based scoring.*

- `set_data(data, regime_labels)` → `None`  *Set OHLCV data for backtesting.*
- `optimize_indicator(indicator_type, regime_id, config)` → `list[IndicatorScore]`  *Optimize parameters for a single indicator.*
- `select_best(scores, top_n, min_trades, max_drawdown_threshold)` → `list[IndicatorScore]`  *Select best parameter combinations based on criteria.*
- `optimize_batch(indicator_types, regime_id, config, top_n_per_indicator)` → `dict[str, list[IndicatorScore]]`  *Optimize multiple indicators in batch.*
- `generate_optimization_report(scores)` → `str`  *Generate human-readable optimization report.*
- *...5 private methods*
- `__init__(catalog_path)`  *Initialize optimizer.*

## `src/core/tradingbot/json_entry_loader.py`

### `JsonEntryConfigError(Exception)`
*Exception raised when JSON Entry Config loading fails.*


### `JsonEntryConfig(object)`
*Configuration für JSON-basiertes Entry.*

- @classmethod `from_files(regime_json_path, indicator_json_path, entry_expression_override)` → `'JsonEntryConfig'`  *Lädt Regime + Indicator JSON und erstellt Entry-Config.*
- `validate()` → `list[str]`  *Validiere Config und gebe Warnings zurück.*
- `get_indicator_ids()` → `list[str]`  *Gibt Liste aller Indicator-IDs zurück.*
- `get_regime_ids()` → `list[str]`  *Gibt Liste aller Regime-IDs zurück.*
- `__str__()` → `str`  *String representation für Logging.*
- `__repr__()` → `str`  *Detailed representation für Debugging.*

## `src/core/tradingbot/json_entry_scorer.py`

### `JsonEntryScorer(object)`
*Evaluiert Entry via CEL Expression aus JSON.*

- `should_enter_long(features, regime, chart_window, prev_regime)` → `tuple[bool, float, list[str]]`  *Prüfe Long Entry via CEL Expression.*
- `should_enter_short(features, regime, chart_window, prev_regime)` → `tuple[bool, float, list[str]]`  *Prüfe Short Entry via CEL Expression.*
- `get_expression_summary()` → `str`  *Gibt kurze Zusammenfassung der Expression zurück.*
- *...4 private methods*
- `__init__(json_config, cel_engine)`  *Initialize JSON Entry Scorer.*
- `__str__()` → `str`  *String representation für Logging.*
- `__repr__()` → `str`  *Detailed representation für Debugging.*

## `src/core/tradingbot/llm_integration.py`

### `LLMIntegration(object)`
*Main LLM integration class for tradingbot.*

- `can_call(call_type)` → `tuple[bool, str]`  *Check if an LLM call is allowed.*
- `call_for_strategy_selection(features, regime, strategies)` → `dict | None`  *Make LLM call for daily strategy selection.*
- `call_for_trade_decision(features, regime, position, state, strategy, call_type)` → `LLMBotResponse`  *Make LLM call for trade decision.*
- `get_stats()` → `dict[str, Any]`  *Get current LLM usage statistics.*
- `get_audit_trail(limit, call_type)` → `list[dict]`  *Get audit trail of LLM calls.*
- *...5 private methods*
- `__init__(config, api_key, on_call)`  *Initialize LLM integration.*

### Module Functions
- `_get_model_from_settings()` → `str`  *Holt das Model aus den QSettings.*

## `src/core/tradingbot/llm_prompts.py`

### `LLMPromptBuilder(object)`
*Builds structured prompts for LLM calls.*

- @staticmethod `build_daily_strategy_prompt(features, regime, strategies, constraints)` → `str`  *Build prompt for daily strategy selection.*
- @staticmethod `build_trade_decision_prompt(features, regime, position, state, strategy, constraints)` → `str`  *Build prompt for trade decision.*

## `src/core/tradingbot/llm_types.py`

### `LLMCallType(str, Enum)`
*Types of LLM calls.*


### `LLMCallRecord(object)`
*Record of an LLM call for audit trail.*


### `LLMBudgetState(object)`
*Budget tracking state.*


## `src/core/tradingbot/llm_validators.py`

### `LLMResponseValidator(object)`
*Validates LLM responses against expected schema.*

- @staticmethod `validate_trade_decision(response, allow_repair)` → `tuple[LLMBotResponse | None, list[str]]`  *Validate trade decision response.*
- @staticmethod `get_fallback_response(state, features)` → `LLMBotResponse`  *Get rule-based fallback response.*
- *...1 private methods*

## `src/core/tradingbot/migration/json_generator.py`

### `JSONConfigGenerator(object)`
*Generates JSON config from strategy analysis.*

- `generate_from_analysis(analysis, include_regime, include_strategy_set)` → `dict[str, Any]`  *Generate JSON config from strategy analysis.*
- `generate_from_multiple_analyses(analyses)` → `dict[str, Any]`  *Generate combined JSON config from multiple strategies.*
- `save_config(config, output_path)` → `None`  *Save JSON config to file.*
- `generate_and_save(analysis, output_path, include_regime, include_strategy_set)` → `None`  *Generate and save JSON config in one step.*
- *...9 private methods*
- `__init__(schema_version)`  *Initialize generator.*

## `src/core/tradingbot/migration/strategy_analyzer.py`

### `IndicatorDependency(object)`
*Indicator used by a strategy.*


### `ConditionInfo(object)`
*Extracted condition information.*


### `StrategyAnalysis(object)`
*Complete analysis of a hardcoded strategy.*


### `StrategyAnalyzer(object)`
*Analyzes hardcoded strategy definitions.*

- `analyze_strategy_class(strategy_class)` → `StrategyAnalysis`  *Analyze a strategy class definition.*
- `analyze_strategy_definition(strategy_def)` → `StrategyAnalysis`  *Analyze a StrategyDefinition object.*
- `list_analyses()` → `list[str]`  *List all analyzed strategy names.*
- `get_analysis(strategy_name)` → `StrategyAnalysis | None`  *Get analysis for a specific strategy.*
- `print_analysis(strategy_name)` → `None`  *Print analysis in human-readable format.*
- *...10 private methods*
- `__init__()`  *Initialize analyzer.*

## `src/core/tradingbot/migration/strategy_comparator.py`

### `ConditionDiff(object)`
*Difference in a single condition.*


### `ParameterDiff(object)`
*Difference in a parameter.*


### `ComparisonResult(object)`
*Complete comparison result.*

- `has_major_differences()` → `bool`  *Check if there are major differences that affect behavior.*
- `has_minor_differences()` → `bool`  *Check if there are minor differences (cosmetic or non-critical).*

### `StrategyComparator(object)`
*Compares JSON configurations against hardcoded strategies.*

- `compare_json_to_hardcoded(json_config, strategy_id, hardcoded_strategy_name)` → `ComparisonResult`  *Compare JSON config strategy against hardcoded strategy.*
- *...10 private methods*
- `__init__()`  *Initialize comparator.*

## `src/core/tradingbot/models.py`

### `TradeSide(str, Enum)`
*Trade direction.*


### `BotAction(str, Enum)`
*Bot decision actions.*


### `RegimeType(str, Enum)`
*Market regime types (unified v2.0 naming).*


### `RegimeID(str, Enum)`
*Extended 6-regime classification (R0-R5).*


### `Direction(str, Enum)`
*Directional bias within a regime.*


### `VolatilityLevel(str, Enum)`
*Volatility classification.*


### `DirectionalBias(str, Enum)`
*Daily directional bias (long/short tendency).*


### `SignalType(str, Enum)`
*Signal confirmation level.*


### `FeatureVector(BaseModel)`
*Feature vector for bot decision making.*

- @property `rsi()` → `float | None`  *Alias for 14-period RSI (compatibility).*
- @property `sma_fast()` → `float | None`  *Alias for SMA 20 (compatibility).*
- @property `sma_slow()` → `float | None`  *Alias for SMA 50 (compatibility).*
- @property `ema_fast()` → `float | None`  *Alias for EMA 12 (compatibility).*
- @property `ema_slow()` → `float | None`  *Alias for EMA 26 (compatibility).*
- @property `atr()` → `float | None`  *Alias for ATR 14 (compatibility).*
- @property `macd_histogram()` → `float | None`  *Alias for MACD histogram (compatibility).*
- `to_dict_normalized()` → `dict[str, float]`  *Export as normalized dict for LLM input.*
- `compute_hash()` → `str`  *Compute hash of feature vector for audit trail.*

### `RegimeState(BaseModel)`
*Current market regime classification.*

- @property `adx()` → `float | None`  *Alias for ADX value (legacy consumers expect .adx).*
- @property `is_trending()` → `bool`  *Check if market is trending.*
- @property `regime_label()` → `str`  *Human-readable regime label.*
- *...1 private methods*

### `ExtendedRegimeState(BaseModel)`
*Extended 6-regime classification state (R0-R5).*

- @property `regime_label()` → `str`  *Human-readable regime label.*
- `to_legacy_regime_state()` → `RegimeState`  *Convert to legacy RegimeState for backward compatibility.*

### `Signal(BaseModel)`
*Trading signal with entry details.*

- @property `risk_reward_potential()` → `float | None`  *Estimated risk-reward based on ATR.*
- `to_marker_data()` → `dict[str, Any]`  *Convert to chart marker data format.*

### `OrderIntent(BaseModel)`
*Intent to place an order.*


### `TrailingState(BaseModel)`
*Trailing stop state tracking.*

- `update_stop(new_stop, current_bar, timestamp, is_long)` → `bool`  *Update stop price if valid (never loosens).*

### `PositionState(BaseModel)`
*Current position state.*

- `update_price(price)` → `None`  *Update current price and recalculate P&L.*
- `is_stopped_out()` → `bool`  *Check if position hit stop-loss.*

### `BotDecision(BaseModel)`
*Bot decision record.*


### `LLMBotResponse(BaseModel)`
*Structured LLM response for bot decisions.*

- @classmethod `validate_reason_codes(v)` → `list[str]`  *Ensure reason codes are uppercase.*

### `StrategyProfile(BaseModel)`
*Strategy profile for daily selection.*

- `is_applicable(regime)` → `bool`  *Check if strategy is applicable for current regime.*

## `src/core/tradingbot/no_trade_filter.py`

### `FilterReason(str, Enum)`
*Reasons for filtering a trade.*


### `FilterResult(object)`
*Result of trade filter check.*

- `add_block(reason, detail)` → `None`  *Add a blocking reason.*
- `__bool__()` → `bool`  *Returns True if trade is allowed.*

### `TradingSession(object)`
*Track daily trading session metrics.*

- `record_trade(pnl)` → `None`  *Record a completed trade.*

### `NoTradeFilter(object)`
*Filter engine to block trades under unfavorable conditions.*

- @property `session()` → `TradingSession`  *Get current trading session, creating new one if needed.*
- `check(features, regime, timestamp)` → `FilterResult`  *Check all filters for current market conditions.*
- `record_trade(pnl)` → `None`  *Record a completed trade result.*
- `reset_session()` → `None`  *Force reset trading session.*
- `update_account_value(value)` → `None`  *Update account value for risk calculations.*
- `add_news_blackout(start, end)` → `None`  *Add a news blackout window.*
- `clear_news_blackouts()` → `None`  *Clear all news blackout windows.*
- `is_trading_allowed()` → `bool`  *Quick check if trading is generally allowed.*
- `get_session_stats()` → `dict`  *Get current session statistics.*
- `get_filter_config()` → `dict`  *Get current filter configuration.*
- *...6 private methods*
- `__init__(market_type, account_value, config)`  *Initialize no-trade filter.*

## `src/core/tradingbot/pattern_strategy_converter.py`

### `PatternStrategyConverter(object)`
*Converts pattern-based strategies to BotController configuration.*

- `convert_to_strategy_profile(pattern_type, strategy_data)` → `StrategyProfile`  *Convert pattern strategy to StrategyProfile for BotController.*
- `extract_fixed_levels(strategy_data)` → `tuple[float | None, float | None, float | None]`  *Extract fixed entry/stop/target levels from pattern strategy.*
- `validate_strategy_data(strategy_data)` → `tuple[bool, str]`  *Validate pattern strategy data has required fields.*
- *...1 private methods*

## `src/core/tradingbot/position_sizer.py`

### `PositionSizer(object)`
*Calculates position sizes based on risk parameters.*

- `calculate_size(signal, current_price, atr, risk_pct)` → `PositionSizeResult`  *Calculate position size for a signal.*
- `calculate_size_atr(signal, current_price, atr, atr_multiple, risk_pct)` → `PositionSizeResult`  *Calculate position size using ATR-based stop distance.*
- `update_account_value(value)` → `None`  *Update account value.*
- `__init__(account_value, risk_limits, default_risk_pct, include_fees, fee_pct)`  *Initialize position sizer.*

## `src/core/tradingbot/regime_calculator_adapter.py`

### `RegimeCalculatorAdapter(object)`
*Adapter for using IndicatorCalculatorFactory in regime_engine_json.*

- `calculate_indicator(df, indicator_type, params)` → `Dict[str, float]`  *Calculate indicator using IndicatorCalculatorFactory.*
- *...4 private methods*
- `__init__()`  *Initialize adapter with lazy factory creation.*

## `src/core/tradingbot/regime_engine.py`

### `RegimeEngine(object)`
*Engine for market regime classification.*

- `classify(features)` → `RegimeState`  *Classify current market regime from features.*
- `classify_extended(features)` → `ExtendedRegimeState`  *Classify market regime using extended R0-R5 system.*
- `is_favorable_for_trend(state)` → `bool`  *Check if regime is favorable for trend-following strategies.*
- `is_favorable_for_range(state)` → `bool`  *Check if regime is favorable for range/mean-reversion strategies.*
- `get_risk_multiplier(state)` → `float`  *Get risk adjustment multiplier based on volatility.*
- `get_trailing_multiplier(state)` → `float`  *Get trailing stop distance multiplier based on volatility.*
- `detect_regime_change(current, previous)` → `dict[str, bool]`  *Detect if regime has changed significantly.*
- *...10 private methods*
- `__init__(adx_trending, vol_high_pct, use_rsi_confirmation)`  *Initialize regime engine.*

### `RegimeTracker(object)`
*Anti-flap regime tracker with confirmation and cooldown logic.*

- `update(detected_regime, current_time)` → `ExtendedRegimeState`  *Update tracker with newly detected regime.*
- `reset(initial_regime)` → `None`  *Reset tracker to a specific regime state.*
- *...1 private methods*
- `__init__(confirm_bars, cooldown_bars, min_segment_bars)`  *Initialize regime tracker.*

## `src/core/tradingbot/regime_engine_json.py`

### `RegimeEngineJSON(object)`
*JSON-based regime engine using IndicatorEngine + RegimeDetector.*

- `classify_from_config(data, config_path, scope)` → `RegimeState`  *Classify market regime using JSON configuration.*
- `classify_from_features(features, config_path, scope)` → `RegimeState`  *Classify regime from pre-calculated FeatureVector.*
- `get_regime_descriptions(config_path)` → `dict[str, str]`  *Get descriptions of all regimes in config.*
- `list_required_indicators(config_path)` → `list[str]`  *List all indicators required by config.*
- *...9 private methods*
- `__init__()`  *Initialize JSON-based regime engine.*

## `src/core/tradingbot/regime_stability.py`

### `RegimeChange(object)`
*Single regime change event.*

- `__post_init__()` → `None`

### `RegimeStabilityMetrics(object)`
*Aggregated stability metrics for a lookback window.*


### `RegimeStabilityTracker(object)`
*Tracks regime changes and computes stability metrics.*

- `record_change(change)` → `None`  *Record a new regime change and prune old history.*
- `detect_oscillation(window_minutes, threshold)` → `bool`  *Detect whether oscillations exceed a threshold in a window.*
- `get_metrics(lookback_minutes)` → `RegimeStabilityMetrics`  *Compute stability metrics for the recent window.*
- *...3 private methods*
- `__init__(window_minutes)`

## `src/core/tradingbot/risk_manager.py`

### `RiskManager(object)`
*Manages trading risk limits and tracking.*

- @property `state()` → `RiskState`  *Current risk state.*
- `can_trade()` → `tuple[bool, list[str]]`  *Check if trading is allowed.*
- `record_trade_start()` → `None`  *Record start of a new trade.*
- `record_trade_end(pnl)` → `None`  *Record end of a trade.*
- `update_account_value(value)` → `None`  *Update account value.*
- `get_stats()` → `dict[str, Any]`  *Get current risk stats.*
- *...3 private methods*
- `__init__(limits, account_value)`  *Initialize risk manager.*

## `src/core/tradingbot/state_machine.py`

### `BotState(str, Enum)`
*Bot operation states.*


### `BotTrigger(str, Enum)`
*State transition triggers.*


### `StateTransition(BaseModel)`
*Record of a state transition.*


### `StateMachineError(Exception)`
*State machine operation error.*


### `InvalidTransitionError(StateMachineError)`
*Invalid state transition attempted.*


### `BotStateMachine(object)`
*Finite state machine for trading bot operation.*

- @property `state()` → `BotState`  *Current state.*
- @property `history()` → `list[StateTransition]`  *Transition history.*
- @property `context()` → `dict[str, Any]`  *State context data.*
- `can_transition(trigger)` → `bool`  *Check if transition is valid from current state.*
- `get_valid_triggers()` → `list[BotTrigger]`  *Get all valid triggers from current state.*
- `trigger(trigger, data, force)` → `BotState`  *Execute a state transition.*
- `reset(clear_history)` → `None`  *Reset state machine to FLAT.*
- `set_context(key, value)` → `None`  *Set context value.*
- `get_context(key, default)` → `Any`  *Get context value.*
- `is_flat()` → `bool`  *Check if no position.*
- `is_in_trade()` → `bool`  *Check if in active trade.*
- `is_waiting_fill()` → `bool`  *Check if waiting for order fill.*
- `is_managing()` → `bool`  *Check if actively managing position.*
- `is_paused()` → `bool`  *Check if paused.*
- `is_error()` → `bool`  *Check if in error state.*
- `can_enter_trade()` → `bool`  *Check if can enter new trade.*
- `on_candle_close(bar_data)` → `BotState`  *Handle candle close event.*
- `on_signal(signal, confirmed)` → `BotState`  *Handle signal event.*
- `on_order_fill(fill_price, fill_qty, order_id)` → `BotState`  *Handle order fill event.*
- `on_stop_hit(exit_price)` → `BotState`  *Handle stop-loss hit event.*
- `on_exit_signal(reason)` → `BotState`  *Handle exit signal event.*
- `pause(reason)` → `BotState`  *Pause the bot.*
- `resume()` → `BotState`  *Resume the bot.*
- `error(error_msg)` → `BotState`  *Transition to error state.*
- `clear_error()` → `BotState`  *Clear error and return to FLAT.*
- `to_dict()` → `dict[str, Any]`  *Serialize state machine to dict.*
- @classmethod `from_dict(data, on_transition)` → `'BotStateMachine'`  *Deserialize state machine from dict.*
- `__init__(symbol, initial_state, on_transition)`  *Initialize state machine.*

## `src/core/tradingbot/strategy_bridge.py`

### `BridgedParameters(object)`
*Container for bridged parameters between systems.*


### `StrategyBridge(object)`
*Bridge between Strategy Simulator and Strategy Catalog.*

- `get_catalog_strategies(simulator_strategy)` → `list[str]`  *Get catalog strategies that correspond to a simulator strategy.*
- `get_simulator_strategy(catalog_strategy)` → `str | None`  *Get simulator strategy that corresponds to a catalog strategy.*
- `get_primary_catalog_strategy(simulator_strategy)` → `str | None`  *Get the primary (first) catalog strategy for a simulator strategy.*
- `bridge_parameters(simulator_strategy, simulator_params, target_catalog_strategy)` → `BridgedParameters`  *Bridge simulator parameters to catalog format.*
- `save_bridged_params(simulator_strategy, simulator_params, catalog_strategy, symbol)` → `Path`  *Save bridged parameters for production use.*
- `load_bridged_params(catalog_strategy)` → `dict[str, Any] | None`  *Load bridged parameters for a catalog strategy.*
- `get_indicator_config_for_strategy(catalog_strategy)` → `dict[str, Any]`  *Get indicator configuration for a catalog strategy.*
- `is_catalog_strategy(strategy_name)` → `bool`  *Check if strategy_name is a catalog strategy name.*
- `apply_to_active_strategy(bot_controller, simulator_strategy, simulator_params)` → `bool`  *Apply simulator parameters to the active trading strategy.*
- *...2 private methods*
- `__init__()`  *Initialize the strategy bridge.*

### Module Functions
- `get_strategy_bridge()` → `StrategyBridge`  *Get singleton StrategyBridge instance.*
- `get_catalog_strategies_for_simulator(simulator_strategy)` → `list[str]`  *Get catalog strategies for a simulator strategy.*
- `get_simulator_strategy_for_catalog(catalog_strategy)` → `str | None`  *Get simulator strategy for a catalog strategy.*
- `apply_simulator_params_to_bot(bot_controller, simulator_strategy, simulator_params)` → `bool`  *Apply simulator parameters to active bot strategy.*

## `src/core/tradingbot/strategy_catalog.py`

### `StrategyCatalog(StrategyTemplatesMixin)`
*Catalog of pre-built trading strategies.*

- `get_strategy(name)` → `StrategyDefinition | None`  *Get strategy by name.*
- `get_all_strategies()` → `list[StrategyDefinition]`  *Get all registered strategies.*
- `get_strategies_for_regime(regime)` → `list[StrategyDefinition]`  *Get strategies applicable for current regime.*
- `get_strategies_by_type(strategy_type)` → `list[StrategyDefinition]`  *Get strategies of a specific type.*
- `register_strategy(name, strategy)` → `None`  *Register a custom strategy.*
- `list_strategies()` → `list[str]`  *List all strategy names.*
- *...1 private methods*
- `__init__()`  *Initialize strategy catalog with built-in strategies.*

## `src/core/tradingbot/strategy_definitions.py`

### `StrategyType(str, Enum)`
*Built-in strategy types.*


### `EntryRule(BaseModel)`
*Entry rule configuration.*


### `ExitRule(BaseModel)`
*Exit rule configuration.*


### `StrategyDefinition(BaseModel)`
*Complete strategy definition with rules.*

- `is_applicable(regime)` → `bool`  *Check if strategy is applicable for current regime.*

## `src/core/tradingbot/strategy_evaluator.py`

### `StrategyEvaluator(object)`
*Evaluator for strategy performance.*

- `calculate_metrics(trades, initial_capital, sample_type)` → `PerformanceMetrics`  *Calculate performance metrics from trade results.*
- `validate_robustness(metrics, gate)` → `tuple[bool, list[str]]`  *Validate metrics against robustness criteria.*
- `run_walk_forward(strategy, all_trades, config)` → `WalkForwardResult`  *Run walk-forward analysis on strategy.*
- `validate_strategy_robustness(walk_forward_result, min_trades, max_drawdown_threshold, min_sharpe, max_degradation_pct)` → `RobustnessReport`  *Validate strategy robustness using walk-forward results.*
- `compare_strategies(results)` → `list[tuple[str, float]]`  *Rank strategies by composite score.*
- `create_walk_forward_charts(walk_forward_result, robustness_report)`  *Create walk-forward validation charts.*
- `__init__(robustness_gate, walk_forward_config)`  *Initialize evaluator.*

## `src/core/tradingbot/strategy_selector.py`

### `StrategySelector(object)`
*Daily strategy selector (REFACTORED).*

- `select_strategy(regime, symbol, force)` → `SelectionResult`  *Select best strategy for current conditions.*
- `record_trade(strategy_name, trade)` → `None`  *Record a trade result for strategy evaluation (delegiert).*
- `load_trade_history(strategy_name, trades)` → `None`  *Load historical trades for a strategy (delegiert).*
- `get_trade_history(strategy_name)` → `list[TradeResult]`  *Get trade history for a strategy (delegiert).*
- `get_current_selection()` → `SelectionResult | None`  *Get current strategy selection (delegiert).*
- `get_current_strategy()`  *Get current selected strategy definition (delegiert).*
- `is_trading_allowed()` → `bool`  *Check if trading is allowed with current selection (delegiert).*
- `get_applicable_strategies(regime)` → `list[str]`  *Get strategies applicable for regime (delegiert).*
- `get_strategy_info(strategy_name)` → `dict | None`  *Get detailed info about a strategy (delegiert).*
- `get_regime_strategies()` → `dict[str, list[str]]`  *Get strategy mapping per regime (delegiert).*
- `suggest_strategy(regime)` → `str | None`  *Quick suggestion without full evaluation (delegiert).*
- `__init__(catalog, evaluator, snapshot_dir, allow_intraday_switch, require_regime_flip_for_switch)`  *Initialize strategy selector.*

## `src/core/tradingbot/strategy_selector_guards.py`

### `StrategySelectorGuards(object)`
*Helper for reselection guards and result creation.*

- `should_reselect(regime, now)` → `bool`  *Check if we should re-select strategy.*
- `create_selection_result(strategy, regime, wf_result, scores, candidates_count, passed_count)` → `SelectionResult`  *Create selection result.*
- `create_fallback_result(regime, reason)` → `SelectionResult`  *Create fallback selection result.*
- `save_selection(result, symbol)` → `None`  *Save selection snapshot.*
- `__init__(parent)`

## `src/core/tradingbot/strategy_selector_history.py`

### `StrategySelectorHistory(object)`
*Helper for trade history management.*

- `record_trade(strategy_name, trade)` → `None`  *Record a trade result for strategy evaluation.*
- `load_trade_history(strategy_name, trades)` → `None`  *Load historical trades for a strategy.*
- `get_trade_history(strategy_name)` → `list[TradeResult]`  *Get trade history for a strategy.*
- `__init__(parent)`

## `src/core/tradingbot/strategy_selector_models.py`

### `SelectionResult(BaseModel)`
*Result of strategy selection.*


### `SelectionSnapshot(BaseModel)`
*Snapshot of strategy selection for persistence.*


## `src/core/tradingbot/strategy_selector_query.py`

### `StrategySelectorQuery(object)`
*Helper for query methods.*

- `get_current_selection()` → `SelectionResult | None`  *Get current strategy selection.*
- `get_current_strategy()` → `StrategyDefinition | None`  *Get current selected strategy definition.*
- `is_trading_allowed()` → `bool`  *Check if trading is allowed with current selection.*
- `get_applicable_strategies(regime)` → `list[str]`  *Get strategies applicable for regime.*
- `get_strategy_info(strategy_name)` → `dict | None`  *Get detailed info about a strategy.*
- `get_regime_strategies()` → `dict[str, list[str]]`  *Get strategy mapping per regime.*
- `suggest_strategy(regime)` → `str | None`  *Quick suggestion without full evaluation.*
- `__init__(parent)`

## `src/core/tradingbot/strategy_selector_selection.py`

### `StrategySelectorSelection(object)`
*Helper for main selection logic.*

- `evaluate_candidates(candidates)` → `list[tuple]`  *Evaluate each candidate strategy with walk-forward analysis.*
- `filter_robust_strategies(evaluated)` → `list[tuple]`  *Filter to strategies that pass robustness validation.*
- `select_best_strategy(robust, regime, candidates, symbol)` → `SelectionResult | None`  *Select best strategy from robust list.*
- *...2 private methods*
- `__init__(parent)`

## `src/core/tradingbot/strategy_templates.py`

### `StrategyTemplatesMixin(object)`
*Mixin providing strategy template creation methods.*

- *...9 private methods*

## `src/core/tradingbot/timeframe_data_manager.py`

### `TimeframeBar(object)`
*Single OHLCV bar for a specific timeframe.*

- `to_dict()` → `dict[str, Any]`  *Convert to dictionary format.*

### `TimeframeData(object)`
*Data container for a single timeframe.*

- `add_bar(bar)` → `None`  *Add completed bar to history.*
- `get_last_n_bars(n)` → `list[TimeframeBar]`  *Get last N bars.*
- `get_dataframe(use_cache)` → `pd.DataFrame`  *Convert bars to DataFrame.*

### `TimeframeDataManager(object)`
*Manager for multi-timeframe OHLCV data.*

- `add_timeframe(timeframe)` → `None`  *Add a new timeframe to manage.*
- `add_bar(timeframe, bar_data)` → `None`  *Add a bar to the specified timeframe.*
- `get_bars(timeframe, n, as_dataframe)` → `list[TimeframeBar] | pd.DataFrame`  *Get bars for a specific timeframe.*
- `get_aligned_data(timeframes, n)` → `dict[str, pd.DataFrame]`  *Get aligned data across multiple timeframes.*
- `clear_timeframe(timeframe)` → `None`  *Clear all data for a specific timeframe.*
- `get_stats()` → `dict[str, int]`  *Get manager statistics.*
- `get_timeframes()` → `list[str]`  *Get list of registered timeframes (sorted smallest to largest).*
- `warmup_from_history(timeframe, historical_bars)` → `None`  *Warmup timeframe with historical data.*
- *...5 private methods*
- `__init__(base_timeframe, max_bars_per_tf, auto_resample)`  *Initialize TimeframeDataManager.*

### `MultiTimeframeFeatureEngine(object)`
*Feature engine that calculates indicators across multiple timeframes.*

- `process_bar(bar_data)` → `dict[str, Any]`  *Process a base timeframe bar and calculate features across all TFs.*
- `__init__(timeframes, base_timeframe, indicator_periods)`  *Initialize multi-timeframe feature engine.*

## `src/core/variables/bot_config_provider.py`

### `BotConfigProvider(object)`
*Provides bot configuration for CEL expressions via bot.* namespace.*

- `get_context(bot_config)` → `Dict[str, Any]`  *Extract bot configuration and return CEL context.*
- `get_variable_names()` → `list[str]`  *Get list of all available variable names.*
- `get_variable_info()` → `Dict[str, Dict[str, str]]`  *Get metadata for all variables.*
- *...1 private methods*
- `__init__(namespace)`  *Initialize bot config provider.*

## `src/core/variables/chart_data_provider.py`

### `ChartDataProvider(object)`
*Provides chart data for CEL expressions via chart.* namespace.*

- `get_context(chart_window)` → `Dict[str, Any]`  *Extract chart data from ChartWindow and return CEL context.*
- `get_variable_names()` → `list[str]`  *Get list of all available variable names.*
- `get_available_variables()` → `Dict[str, Dict[str, str]]`  *Alias for get_variable_info to match interface expectation.*
- `get_variable_info()` → `Dict[str, Dict[str, str]]`  *Get metadata for all variables.*
- *...1 private methods*
- `__init__(namespace)`  *Initialize chart data provider.*

## `src/core/variables/variable_models.py`

### `VariableType(str, Enum)`
*Supported variable types for CEL expressions.*


### `ProjectVariable(BaseModel)`
*Single project variable with type, value, and metadata.*

- @classmethod `validate_value_type(v, info)` → `Any`  *Validate that value matches declared type.*
- @classmethod `validate_tags(v)` → `List[str]`  *Validate and normalize tags.*
- `get_cel_value()` → `Any`  *Get value formatted for CEL context.*
- `to_display_value()` → `str`  *Get human-readable display value with unit.*

### `ProjectVariables(BaseModel)`
*Container for all project variables loaded from .cel_variables.json.*

- @classmethod `validate_variable_names(v)` → `Dict[str, ProjectVariable]`  *Validate variable names follow naming conventions.*
- `validate_unique_combinations()` → `ProjectVariables`  *Validate that variable names are unique (case-insensitive).*
- `get_variable(name)` → `Optional[ProjectVariable]`  *Get variable by name.*
- `get_variables_by_category(category)` → `Dict[str, ProjectVariable]`  *Get all variables in a specific category.*
- `get_variables_by_tag(tag)` → `Dict[str, ProjectVariable]`  *Get all variables with a specific tag.*
- `get_categories()` → `List[str]`  *Get list of all categories.*
- `get_all_tags()` → `List[str]`  *Get list of all tags used across variables.*
- `to_cel_context()` → `Dict[str, Any]`  *Convert to CEL context dictionary.*
- `add_variable(name, variable)` → `None`  *Add or update a variable.*
- `remove_variable(name)` → `bool`  *Remove a variable.*
- `clear_all()` → `None`  *Remove all variables.*
- `count()` → `int`  *Get total number of variables.*
- `__len__()` → `int`  *Support len() function.*
- `__contains__(name)` → `bool`  *Support 'in' operator.*

## `src/core/variables/variable_storage.py`

### `VariableStorageError(Exception)`
*Base exception for variable storage errors.*


### `VariableFileNotFoundError(VariableStorageError)`
*Raised when variable file doesn't exist.*


### `VariableValidationError(VariableStorageError)`
*Raised when variable data fails validation.*


### `VariableStorage(object)`
*Storage layer for project variables with LRU caching.*

- `load(file_path, use_cache, create_if_missing)` → `ProjectVariables`  *Load project variables from JSON file.*
- `save(file_path, variables, update_timestamps)` → `None`  *Save project variables to JSON file.*
- `reload(file_path)` → `ProjectVariables`  *Force reload variables from file, bypassing cache.*
- `is_cached(file_path)` → `bool`  *Check if file is currently cached.*
- `clear_cache(file_path)` → `None`  *Clear cache for specific file or all files.*
- `get_cache_info()` → `Dict[str, any]`  *Get cache statistics.*
- `exists(file_path)` → `bool`  *Check if variable file exists.*
- `validate_file(file_path)` → `tuple[bool, Optional[str]]`  *Validate variable file without loading into cache.*
- `__init__(cache_size)`  *Initialize variable storage.*
- `__repr__()` → `str`  *String representation.*

## `src/database/database.py`

### `DatabaseManager(object)`
*Manages database connections and operations.*

- `initialize()` → `None`  *Initialize the database connection and create tables.*
- `create_tables()` → `None`  *Create all database tables.*
- `drop_tables()` → `None`  *Drop all database tables. USE WITH CAUTION!*
- `session()` → `Generator[Session, None, None]`  *Provide a transactional scope for database operations.*
- `get_connection()`  *Provide a raw DBAPI connection for direct SQL operations.*
- `get_session()` → `Session`  *Get a new database session.*
- `execute_raw(query, params)` → `Any`  *Execute a raw SQL query.*
- `backup(backup_path)` → `None`  *Create a database backup (SQLite only).*
- `vacuum()` → `None`  *Perform database maintenance (VACUUM for SQLite).*
- `get_table_stats()` → `dict`  *Get statistics about database tables.*
- `get_bars(symbol, start_ts, end_ts, limit)` → `list[MarketBar]`  *Get market bars from database.*
- async `run_in_executor(func)`  *Run a synchronous function in an executor.*
- async `get_bars_async(symbol, start_ts, end_ts, limit)` → `list[MarketBar]`  *Async wrapper for get_bars.*
- `cleanup_old_data(days_to_keep)` → `None`  *Clean up old data from the database.*
- `close()` → `None`  *Close the database connection.*
- *...1 private methods*
- `__init__(config)`  *Initialize the database manager.*

### Module Functions
- `initialize_database(config)` → `DatabaseManager`  *Initialize the global database manager.*
- `get_db_manager()` → `DatabaseManager`  *Get the global database manager.*

## `src/database/models.py`

### `OrderStatus(enum.Enum)`
*Order status enumeration.*


### `OrderSide(enum.Enum)`
*Order side (buy/sell).*


### `OrderType(enum.Enum)`
*Order type enumeration.*


### `TimeInForce(enum.Enum)`
*Time in force for orders.*


### `AlertPriority(enum.Enum)`
*Alert priority levels.*


### `MarketBar(Base)`
*1-second market data bars.*


### `Order(Base)`
*Trading orders.*


### `Execution(Base)`
*Order executions/fills.*


### `Position(Base)`
*Current positions.*


### `Alert(Base)`
*Trading alerts and notifications.*


### `Strategy(Base)`
*Strategy configurations and parameters.*


### `BacktestResult(Base)`
*Backtesting results.*


### `AITelemetry(Base)`
*AI API usage telemetry and cost tracking.*


### `AICache(Base)`
*Cache for AI responses to reduce API calls.*


### `AuditLog(Base)`
*Comprehensive audit trail for all trading activities.*


### `SystemMetrics(Base)`
*System performance and health metrics.*


## `src/database/ohlc_validator.py`

### `OHLCValidator(object)`
*Validates and fixes OHLC data inconsistencies.*

- `validate_and_fix(symbol, dry_run, progress_callback)` → `dict`  *Validate and fix OHLC data in database.*
- `get_validation_summary(symbol)` → `dict`  *Get summary of OHLC data quality without fixing.*
- `__init__()`  *Initialize validator.*

### Module Functions
- `validate_and_fix_ohlc(symbol, dry_run, progress_callback)` → `dict`  *Convenience function for OHLC validation.*

## `src/derivatives/ko_finder/adapter/fetcher.py`

### `CircuitState(Enum)`
*Zustände des Circuit-Breakers.*


### `FetchResult(object)`
*Ergebnis eines Fetch-Vorgangs.*


### `CircuitBreaker(object)`
*Circuit-Breaker zum Schutz vor Überlastung.*

- `record_failure()` → `None`  *Registriere einen Fehler.*
- `record_success()` → `None`  *Registriere einen Erfolg.*
- `can_execute()` → `bool`  *Prüfe ob Request ausgeführt werden darf.*

### `OnvistaFetcher(object)`
*HTTP-Client für Onvista mit Rate-Limiting und Fehlerbehandlung.*

- async `fetch(url, run_id)` → `FetchResult`  *Hole HTML von URL mit Rate-Limiting und Retry.*
- `reset_circuit_breaker()` → `None`  *Setze Circuit-Breaker manuell zurück.*
- async `close()` → `None`  *Schließe HTTP-Client und Session.*
- *...5 private methods*
- `__init__(min_delay, max_retries)` → `None`  *Initialisiere Fetcher.*

## `src/derivatives/ko_finder/adapter/normalizer.py`

### `OnvistaNormalizer(object)`
*Normalisierer für Onvista-Daten.*

- `normalize_products(products, underlying_price)` → `list[KnockoutProduct]`  *Normalisiere Liste von Produkten.*
- `normalize_product(product, underlying_price)` → `KnockoutProduct | None`  *Normalisiere einzelnes Produkt.*
- *...3 private methods*

### Module Functions
- `parse_german_number(text)` → `float | None`  *Parse Zahl mit deutscher Formatierung.*
- `parse_percentage(text)` → `float | None`  *Parse Prozentangabe.*

## `src/derivatives/ko_finder/adapter/parser.py`

### `ParseResult(object)`
*Ergebnis des Parsings.*


### `OnvistaParser(object)`
*Parser für Onvista KO-Listen HTML.*

- `parse(html, direction, source_url, run_id)` → `ParseResult`  *Parse HTML und extrahiere KO-Produkte.*
- *...6 private methods*
- `__init__()` → `None`  *Initialisiere Parser.*

## `src/derivatives/ko_finder/adapter/playwright_fetcher.py`

### `PlaywrightConfig(object)`
*Konfiguration für Playwright Browser.*


### `PlaywrightFetcher(object)`
*Headless-Browser Fetcher für Onvista.*

- async `fetch(url, run_id)` → `FetchResult`  *Hole HTML von URL mit Playwright.*
- `reset_circuit_breaker()` → `None`  *Setze Circuit-Breaker manuell zurück.*
- async `close()` → `None`  *Schließe Browser und Playwright.*
- *...10 private methods*
- `__init__(config, min_delay)` → `None`  *Initialisiere Fetcher.*

## `src/derivatives/ko_finder/config.py`

### `KOFilterConfig(object)`
*Konfiguration für KO-Produkt-Suche und -Filter.*

- @property `issuer_ids_str()` → `str`  *Kommaseparierte Issuer-IDs für URL.*
- `to_dict()` → `dict`  *Konvertiere zu Dictionary für Serialisierung.*
- @classmethod `from_dict(data)` → `KOFilterConfig`  *Erstelle Config aus Dictionary.*
- `save_to_qsettings(settings, prefix)` → `None`  *Speichere Config in QSettings.*
- @classmethod `load_from_qsettings(settings, prefix)` → `KOFilterConfig`  *Lade Config aus QSettings.*
- *...1 private methods*
- `__post_init__()` → `None`  *Validiere alle Parameter nach Initialisierung.*

## `src/derivatives/ko_finder/constants.py`

### `Issuer(Enum)`
*Unterstützte Emittenten mit Onvista-IDs.*

- @property `display_name()` → `str`  *Anzeigename für UI.*

### `Direction(Enum)`
*Handelsrichtung für KO-Produkte.*

- @property `exercise_right_param()` → `str | None`  *URL-Parameter für idExerciseRight.*

### `SortColumn(Enum)`
*Verfügbare Sortierspalten.*


### `SortOrder(Enum)`
*Sortierrichtung.*


## `src/derivatives/ko_finder/engine/cache.py`

### `CacheEntry(Generic[T])`
*Einzelner Cache-Eintrag.*

- @property `age_seconds()` → `float`  *Alter in Sekunden.*
- @property `is_expired()` → `bool`  *Prüft ob Eintrag abgelaufen ist.*
- @property `is_stale()` → `bool`  *Prüft ob Eintrag "stale" ist (alt aber noch nutzbar).*

### `CacheManager(object)`
*In-Memory Cache mit Stale-While-Revalidate.*

- `get(key)` → `CacheEntry | None`  *Hole Eintrag aus Cache.*
- `set(key, value, ttl_seconds)` → `CacheEntry`  *Setze Cache-Eintrag.*
- `invalidate(key)` → `bool`  *Invalidiere Cache-Eintrag.*
- `clear()` → `int`  *Lösche alle Einträge.*
- @staticmethod `build_key(underlying, direction, config)` → `str`  *Erstelle Cache-Key aus Parametern.*
- *...1 private methods*
- `__init__(ttl_seconds, max_size)` → `None`  *Initialisiere Cache.*

### `SWRCache(object)`
*Stale-While-Revalidate Cache Wrapper.*

- `get_with_status(key)` → `tuple[Any | None, bool, bool]`  *Hole Wert mit Status-Informationen.*
- `__init__(cache)` → `None`  *Initialisiere SWR Cache.*

## `src/derivatives/ko_finder/engine/filters.py`

### `FilterResult(object)`
*Ergebnis der Filterung.*

- `__post_init__()` → `None`

### `HardFilters(object)`
*Hard Filters für KO-Produkte.*

- `apply(products)` → `FilterResult`  *Wende alle Filter auf Produkte an.*
- *...6 private methods*
- `__init__(config)` → `None`  *Initialisiere Filter mit Konfiguration.*

### Module Functions
- `apply_hard_filters(products, config)` → `list[KnockoutProduct]`  *Convenience-Funktion für Filter-Anwendung.*

## `src/derivatives/ko_finder/engine/ranking.py`

### `ScoringParams(object)`
*Parameter für das KO-Scoring-System.*


### `ScoreBreakdown(object)`
*Detaillierte Aufschlüsselung des Scores.*


### `RankingEngine(object)`
*Ranking Engine für KO-Produkte.*

- `rank(products, top_n)` → `list[KnockoutProduct]`  *Ranke Produkte nach Score (absteigend).*
- `calculate_score(product)` → `float`  *Berechne Score für einzelnes Produkt.*
- *...7 private methods*
- `__init__(config, params, underlying_price)` → `None`  *Initialisiere Ranking Engine.*

### Module Functions
- `rank_products(products, config, top_n, underlying_price)` → `list[KnockoutProduct]`  *Convenience-Funktion für Ranking.*

## `src/derivatives/ko_finder/models.py`

### `ProductFlag(Enum)`
*Qualitäts-Flags für Produkte.*


### `Quote(object)`
*Kurs-Informationen (Bid/Ask/Spread).*

- @property `is_valid()` → `bool`  *Prüft ob Quote gültig ist (Bid und Ask vorhanden, nicht stale).*
- `calculate_spread_pct()` → `float | None`  *Berechnet Spread in Prozent aus Bid/Ask.*

### `UnderlyingSnapshot(object)`
*Snapshot des Basiswerts.*


### `KnockoutProduct(object)`
*Vollständiges Knock-Out Produkt.*

- @property `is_tradeable()` → `bool`  *Prüft ob Produkt handelbar erscheint.*
- @property `spread_pct()` → `float | None`  *Spread in Prozent (aus Quote oder berechnet).*
- `update_ko_distance(underlying_price)` → `None`  *Aktualisiere KO-Abstand mit neuem Underlying-Preis.*
- *...2 private methods*
- `__post_init__()` → `None`  *Berechne abgeleitete Werte.*

### `SearchMeta(object)`
*Meta-Informationen zur Suche.*


### `SearchRequest(object)`
*Suchanfrage für KO-Produkte.*


### `SearchResponse(object)`
*Vollständige Suchantwort mit Long/Short Ergebnissen.*

- @property `total_results()` → `int`  *Gesamtanzahl Ergebnisse.*
- @property `has_errors()` → `bool`  *Prüft ob Fehler aufgetreten sind.*

## `src/derivatives/ko_finder/pnl_calculator.py`

### `Direction(Enum)`
*Handelsrichtung.*


### `DerivativePnL(object)`
*Ergebnis der Derivat-P&L-Berechnung.*


### Module Functions
- `calculate_derivative_pnl(direction, leverage, spread_pct, u0, u1, capital, ask_entry)` → `DerivativePnL`  *Berechne Derivat-P&L.*

## `src/derivatives/ko_finder/service.py`

### `KOFinderService(object)`
*Haupt-Service für KO-Produkt-Suche.*

- async `search(underlying, config, underlying_price, force_refresh)` → `SearchResponse`  *Suche KO-Produkte für Underlying.*
- `reset_circuit_breaker()` → `None`  *Setze Circuit-Breaker zurück.*
- `clear_cache()` → `int`  *Lösche Cache und gib Anzahl gelöschter Einträge zurück.*
- *...9 private methods*
- `__init__(cache_enabled, cache_ttl, use_playwright)` → `None`  *Initialisiere Service.*

## `src/optimization/parameter_generator.py`

### `ParameterCombinationGenerator(object)`
*Generate parameter combinations using Iterator Pattern.*

- @classmethod `from_ui_format(indicator_type, ui_param_ranges, derived_params)` → `'ParameterCombinationGenerator'`  *Create generator from UI parameter format.*
- `generate()` → `Iterator[Dict[str, Any]]`  *Generate all parameter combinations using itertools.product.*
- `count()` → `int`  *Count total combinations without generating.*
- `__init__(indicator_type, param_ranges, derived_params)`  *Initialize generator with pre-expanded parameter ranges.*

### `IndicatorParameterFactory(object)`
*Factory for creating indicator-specific parameter generators.*

- @classmethod `create_generator(indicator_type, ui_param_ranges)` → `ParameterCombinationGenerator`  *Create parameter generator for specific indicator.*

## `src/strategies/indicator_calculators/base_calculator.py`

### `BaseIndicatorCalculator(ABC)`
*Abstract base class for indicator calculations.*

- `can_calculate(indicator_type)` → `bool`  *Check if this calculator can handle the indicator type.*
- `calculate(df, params)` → `pd.DataFrame`  *Calculate indicator values.*

## `src/strategies/indicator_calculators/calculator_factory.py`

### `IndicatorCalculatorFactory(object)`
*Factory for indicator calculators.*

- `register(calculator)` → `None`  *Register a calculator instance.*
- `calculate(indicator_type, df, params)` → `pd.DataFrame`  *Calculate indicator using registered calculators.*
- *...1 private methods*
- `__init__()`  *Initialize factory with empty calculator registry.*

## `src/strategies/indicator_calculators/momentum/cci_calculator.py`

### `CCICalculator(BaseIndicatorCalculator)`
*Calculator for Commodity Channel Index (CCI).*

- `can_calculate(indicator_type)` → `bool`  *Check if this calculator handles CCI.*
- `calculate(df, params)` → `pd.DataFrame`  *Calculate CCI with given period.*

## `src/strategies/indicator_calculators/momentum/macd_calculator.py`

### `MACDCalculator(BaseIndicatorCalculator)`
*Calculator for Moving Average Convergence Divergence (MACD).*

- `can_calculate(indicator_type)` → `bool`  *Check if this calculator handles MACD.*
- `calculate(df, params)` → `pd.DataFrame`  *Calculate MACD with given parameters.*

## `src/strategies/indicator_calculators/momentum/rsi_calculator.py`

### `RSICalculator(BaseIndicatorCalculator)`
*Calculator for Relative Strength Index (RSI).*

- `can_calculate(indicator_type)` → `bool`  *Check if this calculator handles RSI.*
- `calculate(df, params)` → `pd.DataFrame`  *Calculate RSI with given period.*

## `src/strategies/indicator_calculators/momentum/stochastic_calculator.py`

### `StochasticCalculator(BaseIndicatorCalculator)`
*Calculator for Stochastic Oscillator.*

- `can_calculate(indicator_type)` → `bool`  *Check if this calculator handles STOCH.*
- `calculate(df, params)` → `pd.DataFrame`  *Calculate Stochastic Oscillator.*

## `src/strategies/indicator_calculators/other/adx_calculator.py`

### `ADXCalculator(BaseIndicatorCalculator)`
*ADX calculator. CC=3*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/other/pivots_calculator.py`

### `PivotsCalculator(BaseIndicatorCalculator)`
*Pivot Points calculator. CC=3*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/trend/ema_calculator.py`

### `EMACalculator(BaseIndicatorCalculator)`
*Exponential Moving Average calculator. CC=2*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/trend/ichimoku_calculator.py`

### `IchimokuCalculator(BaseIndicatorCalculator)`
*Ichimoku Cloud calculator. CC=4*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/trend/sma_calculator.py`

### `SMACalculator(BaseIndicatorCalculator)`
*Simple Moving Average calculator. CC=2*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/trend/vwap_calculator.py`

### `VWAPCalculator(BaseIndicatorCalculator)`
*VWAP calculator. CC=2*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/volatility/atr_calculator.py`

### `ATRCalculator(BaseIndicatorCalculator)`
*ATR calculator. CC=2*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/volatility/bb_width_calculator.py`

### `BBWidthCalculator(BaseIndicatorCalculator)`
*BB Width calculator. CC=3*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/volatility/bollinger_calculator.py`

### `BollingerCalculator(BaseIndicatorCalculator)`
*Bollinger Bands calculator. CC=3*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/volatility/chop_calculator.py`

### `ChopCalculator(BaseIndicatorCalculator)`
*CHOP calculator. CC=2*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/volatility/keltner_calculator.py`

### `KeltnerCalculator(BaseIndicatorCalculator)`
*Keltner Channels calculator. CC=3*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/volatility/psar_calculator.py`

### `PSARCalculator(BaseIndicatorCalculator)`
*PSAR calculator. CC=3*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/volume/ad_calculator.py`

### `ADCalculator(BaseIndicatorCalculator)`
*Accumulation/Distribution Line calculator. CC=2*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/volume/cmf_calculator.py`

### `CMFCalculator(BaseIndicatorCalculator)`
*Chaikin Money Flow calculator. CC=2*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/volume/mfi_calculator.py`

### `MFICalculator(BaseIndicatorCalculator)`
*Money Flow Index calculator. CC=2*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/indicator_calculators/volume/obv_calculator.py`

### `OBVCalculator(BaseIndicatorCalculator)`
*On Balance Volume calculator. CC=2*

- `can_calculate(indicator_type)` → `bool`
- `calculate(df, params)` → `pd.DataFrame`

## `src/strategies/pattern_strategy_mapper.py`

### `TradeSetup(object)`
*Complete trade setup for a detected pattern.*


### `PatternStrategyMapper(object)`
*Map detected patterns to trading strategies with success rates.*

- `get_strategy(pattern_type)` → `Optional[PatternStrategyMapping]`  *Get trading strategy for a pattern type.*
- `map_pattern_to_strategy(pattern)` → `Optional[PatternStrategyMapping]`  *Map a detected Pattern to its trading strategy.*
- `generate_trade_setup(pattern, current_price)` → `Optional[TradeSetup]`  *Generate complete trade setup for a pattern.*
- `get_all_phase1_patterns()` → `List[str]`  *Get list of all Phase 1 pattern types.*
- *...5 private methods*
- `__init__()`  *Initialize mapper with pre-defined strategies.*

## `src/strategies/signal_generators/__init__.py`

### `SignalGeneratorRegistry(object)`
*Central registry for all signal generators.*

- `generate_signals(df, indicator_type, test_type, trade_side)`  *Generate signals using appropriate generator.*
- `__init__()`  *Initialize registry with all generators.*

## `src/strategies/signal_generators/adx_generator.py`

### `ADXSignalGenerator(BaseSignalGenerator)`
*Generate signals based on ADX trend strength.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate ADX trend strength signals.*

## `src/strategies/signal_generators/base_generator.py`

### `BaseSignalGenerator(ABC)`
*Base class for indicator-specific signal generation.*

- `can_handle(indicator_type)` → `bool`  *Check if this generator can handle the indicator type.*
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate trading signals based on indicator logic.*
- @property `supported_indicators()` → `List[str]`  *List of indicator types this generator supports.*

## `src/strategies/signal_generators/bollinger_generator.py`

### `BollingerSignalGenerator(BaseSignalGenerator)`
*Generate signals based on Bollinger Bands touches.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate Bollinger Bands signals.*

## `src/strategies/signal_generators/channel_generators.py`

### `KeltnerSignalGenerator(BaseSignalGenerator)`
*Keltner Channel signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate Keltner Channel breakout signals.*

## `src/strategies/signal_generators/ema_generator.py`

### `EMASignalGenerator(BaseSignalGenerator)`
*Generate signals based on price/EMA crossovers.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate EMA crossover signals.*

## `src/strategies/signal_generators/macd_generator.py`

### `MACDSignalGenerator(BaseSignalGenerator)`
*Generate signals based on MACD zero-line crossovers.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate MACD crossover signals.*

## `src/strategies/signal_generators/momentum_generators.py`

### `CCISignalGenerator(BaseSignalGenerator)`
*Commodity Channel Index signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate CCI signals.*

## `src/strategies/signal_generators/regime_generators.py`

### `CHOPSignalGenerator(BaseSignalGenerator)`
*Choppiness Index signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate Choppiness Index signals.*

## `src/strategies/signal_generators/rsi_generator.py`

### `RSISignalGenerator(BaseSignalGenerator)`
*Generate signals based on RSI overbought/oversold levels.*

- @property `supported_indicators()` → `List[str]`  *RSI indicator type.*
- `can_handle(indicator_type)` → `bool`  *Check if this is RSI indicator.*
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate RSI-based trading signals.*

## `src/strategies/signal_generators/sma_generator.py`

### `SMASignalGenerator(BaseSignalGenerator)`
*Generate signals based on price/SMA crossovers.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate SMA crossover signals.*

## `src/strategies/signal_generators/stochastic_generator.py`

### `StochasticSignalGenerator(BaseSignalGenerator)`
*Generate signals based on Stochastic crossovers.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate Stochastic signals.*

## `src/strategies/signal_generators/trend_generators.py`

### `IchimokuSignalGenerator(BaseSignalGenerator)`
*Ichimoku Cloud signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate Ichimoku cloud signals.*

### `PSARSignalGenerator(BaseSignalGenerator)`
*Parabolic SAR signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate PSAR reversal signals.*

### `VWAPSignalGenerator(BaseSignalGenerator)`
*VWAP signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate VWAP crossover signals.*

### `PivotsSignalGenerator(BaseSignalGenerator)`
*Pivot Points signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate pivot point signals.*

## `src/strategies/signal_generators/volatility_generators.py`

### `ATRSignalGenerator(BaseSignalGenerator)`
*Average True Range signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate ATR volatility signals.*

### `BBWidthSignalGenerator(BaseSignalGenerator)`
*Bollinger Band Width signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate BB Width signals.*

## `src/strategies/signal_generators/volume_generators.py`

### `OBVSignalGenerator(BaseSignalGenerator)`
*On-Balance Volume signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate OBV trend signals.*

### `MFISignalGenerator(BaseSignalGenerator)`
*Money Flow Index signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate MFI signals.*

### `ADSignalGenerator(BaseSignalGenerator)`
*Accumulation/Distribution signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate A/D signals.*

### `CMFSignalGenerator(BaseSignalGenerator)`
*Chaikin Money Flow signal generator.*

- @property `supported_indicators()` → `List[str]`
- `can_handle(indicator_type)` → `bool`
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate CMF signals.*

## `src/strategies/strategy_models.py`

### `PatternCategory(str, Enum)`
*Pattern category classification.*


### `StrategyType(str, Enum)`
*Trading strategy types.*


### `TradingStrategy(BaseModel)`
*Trading strategy with proven success metrics.*


### `PatternStrategyMapping(BaseModel)`
*Mapping between chart pattern and trading strategy.*


## `src/ui/ai_analysis_context.py`

### `AIAnalysisContext(object)`
*Helper für AIAnalysisWindow Context (Chat, Regime, Drawing).*

- `update_chat_context()` → `None`  *Update AI Chat Tab with MarketContext (Phase 5.8).*
- `connect_chat_draw_signal()` → `None`  *Connect AI Chat draw signal to chart widget (Phase 5.9).*
- `on_chat_draw_zone(zone_type, top, bottom, label)` → `None`  *Handle draw zone request from AI Chat (Phase 5.9).*
- `update_regime_info(result)` → `None`  *Update the regime info panel with detection results.*
- `detect_and_update_regime(df)` → `None`  *Detect regime from DataFrame and update panel.*
- `__init__(parent)`  *Args:*

## `src/ui/ai_analysis_handlers.py`

### `AIAnalysisHandlers(object)`
*Helper für AIAnalysisWindow Handlers (Analysis, Errors, UI Actions).*

- `show_error(title, message)`  *Show error message box popup.*
- `start_analysis()`  *Triggers the analysis engine in a separate thread.*
- `on_analysis_finished(result)`  *Handle analysis completion.*
- `on_analysis_error(error_msg)`  *Handle analysis error.*
- `copy_to_clipboard()`  *Copy analysis result to clipboard.*
- `open_analyse_log()`  *Open Analyse.log file in default text editor.*
- `open_prompt_editor()`  *Popup dialog allowing the user to edit system and task prompts.*
- `apply_prompt_overrides()`  *Read prompt overrides from settings and push into the engine.*
- `show_payload_popup()`  *Show a popup dialog with all data that was sent to the AI.*
- *...2 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/ai_analysis_prompt_editor.py`

### `PromptEditorDialog(QDialog)`
*Small dialog to edit analysis prompts.*

- `get_values()`
- *...2 private methods*
- `__init__(parent, system_prompt, tasks_prompt, default_system, default_tasks)`

## `src/ui/ai_analysis_ui.py`

### `AIAnalysisUI(object)`
*Helper für AIAnalysisWindow UI (Setup, Widgets, Tabs).*

- `init_ui()`  *Initialize main UI with tabs.*
- `init_overview_tab()`  *Initialize overview tab UI.*
- `setup_regime_info_panel(layout)` → `None`  *Setup the regime info panel (Phase 2.2).*
- `load_settings()`  *Load settings from QSettings.*
- `on_provider_changed(provider)`  *Populate model combo based on selected provider.*
- `__init__(parent)`  *Args:*

## `src/ui/ai_analysis_window.py`

### `AIAnalysisWindow(QDialog)`
*Popup window for AI Market Analysis.*

- `showEvent(event)`  *Refresh settings when window is shown.*
- `__init__(parent, symbol)`

## `src/ui/ai_analysis_worker.py`

### `AnalysisWorker(QThread)`
*Worker thread to run the AI analysis without freezing the UI.*

- `run()`
- `__init__(engine, symbol, timeframe, history_manager, asset_class, data_source, model, strategy_configs)`

## `src/ui/app.py`

### `TradingApplication(ActionsMixin, MenuMixin, ToolbarMixin, BrokerMixin, AppUIMixin, AppEventsMixin, AppTimersMixin, AppSettingsMixin, AppChartMixin, AppBrokerEventsMixin, AppRefreshMixin, AppLifecycleMixin, QMainWindow)`
*Main application window for OrderPilot-AI.*

- `closeEvent(event)`  *Handle application close event.*
- `start_in_chart_mode()`  *Start application with Workspace Manager hidden and one ChartWindow open.*
- `__init__(splash)`

### Module Functions
- `_apply_saved_debug_level(level_str)` → `None`  *Apply saved console debug level to all loggers.*
- async `main(app, splash)`  *Main application entry point.*

## `src/ui/app_components/actions_mixin.py`

### `ActionsMixin(object)`
*Mixin providing dialog and action methods for TradingApplication.*

- `show_order_dialog()`  *Show the order placement dialog.*
- `show_settings_dialog()`  *Show the settings dialog.*
- `show_backtest_dialog()`  *Show the backtest dialog.*
- `show_ai_backtest_dialog()`  *Show the AI-powered backtest analysis dialog.*
- `show_parameter_optimization_dialog()`  *Show the parameter optimization dialog.*
- `show_ai_monitor()`  *Show AI usage monitor.*
- `show_pattern_db_dialog()`  *Show the pattern database management dialog.*
- `reset_toolbars_and_docks()`  *Reset all toolbars and dock widgets to their default positions.*
- `show_about()`  *Show about dialog.*

## `src/ui/app_components/app_broker_events_mixin.py`

### `AppBrokerEventsMixin(object)`
*AppBrokerEventsMixin extracted from TradingApplication.*

- `on_order_placed(order_data)`  *Handle order placement.*
- `on_broker_connected(event)`  *Handle broker connection event.*
- `on_broker_disconnected(event)`  *Handle broker disconnection event.*
- `on_order_filled(event)`  *Handle order fill event.*
- `on_alert_triggered(event)`  *Handle alert trigger event.*

## `src/ui/app_components/app_chart_mixin.py`

### `AppChartMixin(object)`
*AppChartMixin extracted from TradingApplication.*

- `open_chart_popup(symbol)`  *Open a popup chart window for the symbol.*
- `on_watchlist_symbol_added(symbol)`  *Handle symbol added to watchlist.*
- *...1 private methods*

## `src/ui/app_components/app_events_mixin.py`

### `AppEventsMixin(object)`
*AppEventsMixin extracted from TradingApplication.*

- `setup_event_handlers()`  *Setup event bus handlers.*
- *...2 private methods*

## `src/ui/app_components/app_lifecycle_mixin.py`

### `AppLifecycleMixin(object)`
*AppLifecycleMixin extracted from TradingApplication.*

- async `initialize_services()` → `None`  *Initialize background services (AI, etc.).*
- `show_console_window()` → `None`  *Show the hidden console window.*
- `closeEvent(event)`  *Handle application close event.*
- *...10 private methods*

## `src/ui/app_components/app_refresh_mixin.py`

### `AppRefreshMixin(object)`
*AppRefreshMixin extracted from TradingApplication.*

- async `refresh_market_data()`  *Refresh market data for all visible widgets.*
- `update_dashboard()`  *Periodic dashboard refresh (timer callback).*

## `src/ui/app_components/app_settings_mixin.py`

### `AppSettingsMixin(object)`
*AppSettingsMixin extracted from TradingApplication.*

- `apply_theme(theme_name)`  *Apply a theme to the application.*
- `load_settings()`  *Load application settings.*
- `save_settings()`  *Save application settings.*
- *...1 private methods*

## `src/ui/app_components/app_timers_mixin.py`

### `AppTimersMixin(object)`
*AppTimersMixin extracted from TradingApplication.*

- `setup_timers()`  *Setup update timers.*
- `update_time()`  *Update time display.*

## `src/ui/app_components/app_ui_mixin.py`

### `AppUIMixin(object)`
*AppUIMixin for Workspace Manager UI.*

- `init_ui()`  *Initialize the Workspace Manager UI.*
- `create_central_widget()`  *Create the central widget with Watchlist.*
- `create_status_bar()`  *Create the status bar.*
- `create_dock_widgets()`  *Create dock widgets - REMOVED in Workspace Manager.*
- @property `dashboard_widget()`  *Removed - raises deprecation warning.*
- @property `positions_widget()`  *Removed - raises deprecation warning.*
- @property `orders_widget()`  *Removed - raises deprecation warning.*
- @property `performance_dashboard()`  *Removed - raises deprecation warning.*
- @property `indicators_widget()`  *Removed - raises deprecation warning.*
- @property `alerts_widget()`  *Removed - raises deprecation warning.*

## `src/ui/app_components/broker_mixin.py`

### `BrokerMixin(object)`
*Mixin providing broker connection functionality for TradingApplication.*

- async `connect_broker()`  *Connect to the selected broker.*
- async `disconnect_broker()`  *Disconnect from the broker.*
- async `initialize_realtime_streaming()`  *Initialize real-time market data streaming.*
- `toggle_live_data()`  *Toggle live market data on/off.*
- `analyze_order_with_ai(analysis_request)`  *AI hook for order analysis.*
- *...4 private methods*

## `src/ui/app_components/menu_mixin.py`

### `MenuMixin(object)`
*Mixin providing menu bar functionality for TradingApplication.*

- `create_menu_bar()`  *Create the application menu bar.*
- *...18 private methods*

## `src/ui/app_components/toolbar_mixin.py`

### `ToolbarMixin(object)`
*Mixin providing toolbar functionality for TradingApplication.*

- `create_toolbar()`  *Create the application toolbar (single row for Workspace Manager).*
- `update_data_provider_list()`  *Update the list of available market data providers (refactored).*
- `on_data_provider_changed(_provider_name)`  *Handle data provider selection changes.*
- *...18 private methods*

## `src/ui/app_console_utils.py`

### Module Functions
- `_is_windows()` → `bool`
- `_get_console_hwnd()` → `int`
- `_hide_console_window()` → `None`
- `_show_console_window()` → `None`

## `src/ui/app_icon.py`

### Module Functions
- `get_app_icon()` → `QIcon`  *Get the main application icon from marketing assets.*
- `set_window_icon(window)` → `None`  *Set the application icon for a window.*

## `src/ui/app_logging.py`

### `ConsoleOnErrorHandler(logging.Handler)`
*Show console window on errors.*

- `emit(record)` → `None`

### `LogStream(QObject)`
*Redirect stdout/stderr to Qt signal (optional mirror).*

- `write(text)` → `None`
- `flush()` → `None`
- `__init__(mirror)` → `None`

## `src/ui/app_resources.py`

### Module Functions
- `_load_app_icon()` → `QIcon`  *Load application icon from marketing assets.*
- `_get_startup_icon_path()` → `Path`

## `src/ui/app_startup_window.py`

### `StartupLogWindow(QWidget)`
*Frameless startup log window.*

- `enqueue_line(line)` → `None`
- *...1 private methods*
- `__init__(icon_path)`

## `src/ui/chart/chart_adapter.py`

### `ChartAdapter(object)`
*Adapter for converting BacktestResult to Lightweight Charts format.*

- @staticmethod `backtest_result_to_chart_data(result)` → `dict[str, Any]`  *Convert comprehensive BacktestResult to Lightweight Charts JSON format.*
- @staticmethod `bars_to_candlesticks(bars)` → `list[dict[str, Any]]`  *Convert Bar list to Lightweight Charts candlestick format.*
- @staticmethod `equity_to_line_series(equity_curve)` → `list[dict[str, Any]]`  *Convert EquityPoint list to Lightweight Charts line series format.*
- @staticmethod `build_markers_from_trades(trades, show_stop_loss, show_take_profit)` → `list[dict[str, Any]]`  *Build entry/exit markers from Trade list.*
- @staticmethod `indicators_to_series(indicators)` → `dict[str, list[dict[str, Any]]]`  *Convert indicator data to Lightweight Charts line series.*
- @staticmethod `to_json(chart_data, indent)` → `str`  *Convert chart data to JSON string.*
- @staticmethod `validate_chart_data(chart_data)` → `tuple[bool, list[str]]`  *Validate chart data structure.*
- *...4 private methods*

## `src/ui/chart/chart_bridge.py`

### `ChartBridge(QObject)`
*Qt WebChannel bridge for chart communication.*

- `loadBacktestResult(result_json)` → `None`  *Load and display backtest result from JSON.*
- `loadBacktestResultObject(result)` → `None`  *Load and display backtest result from Python object.*
- `loadLiveData(symbol)` → `None`  *Load and display live market data for a symbol.*
- `updateTrade(trade_json)` → `None`  *Update chart with new trade marker (for live trading).*
- `getCurrentSymbol()` → `str`  *Get currently displayed symbol.*
- `getMetricsSummary()` → `str`  *Get summary of current backtest metrics as JSON.*
- `clearChart()` → `None`  *Clear the current chart.*
- `toggleMarkers(show)` → `None`  *Toggle trade markers on/off.*
- `toggleIndicator(indicator_name, show)` → `None`  *Toggle specific indicator on/off.*
- *...1 private methods*
- `__init__(parent)`  *Initialize ChartBridge.*

## `src/ui/chart_window_manager.py`

### `ChartWindowManager(object)`
*Manages popup chart windows.*

- `open_or_focus_chart(symbol, data_provider, splash)`  *Open a chart window for the symbol, or focus if already open.*
- `close_window(symbol)`  *Close a chart window.*
- `close_all_windows()`  *Close all open chart windows.*
- `get_open_symbols()`  *Get list of symbols with open chart windows.*
- `has_open_window(symbol)` → `bool`  *Check if a window is open for the symbol.*
- `get_active_symbol()` → `Optional[str]`  *Get the symbol of the currently focused/active chart window.*
- `open_chart(symbol, chart_type)`  *Open a chart window (alias for open_or_focus_chart).*
- `close_all_charts()`  *Close all open chart windows (alias for close_all_windows).*
- `refresh_all_chart_colors()`  *Refresh colors for all open charts (Issues #34, #37).*
- *...1 private methods*
- `__init__(history_manager, parent)`  *Initialize chart window manager.*

### Module Functions
- `get_chart_window_manager(history_manager, parent)` → `ChartWindowManager`  *Get or create the singleton ChartWindowManager instance.*

## `src/ui/debug/ui_inspector.py`

### `UIInspectorOverlay(QLabel)`
*Floating overlay label that shows widget info.*

- `__init__(parent)`

### `UIInspectorEventFilter(QObject)`
*Event filter that intercepts mouse events for inspection.*

- `eventFilter(obj, event)` → `bool`
- *...2 private methods*
- `__init__(inspector)`

### `UIInspectorMixin(object)`
*Mixin für QMainWindow das F12 UI-Inspect-Mode hinzufügt.*

- `setup_ui_inspector()`  *Initialize the UI inspector. Call this in __init__ after super().__init__().*
- `toggle_inspect_mode()`  *Toggle the UI inspection mode on/off.*
- `resizeEvent(event)`  *Handle resize to reposition indicator.*
- *...3 private methods*

## `src/ui/design_system.py`

### `ColorPalette(object)`
*Defines a semantic color palette.*


### `Typography(object)`
*Defines font settings.*


### `Spacing(object)`
*Defines spacing tokens.*


## `src/ui/dialogs/ai_backtest_dialog.py`

### `AIBacktestDialog(QDialog)`
*Enhanced backtest dialog with AI analysis (REFACTORED).*

- `init_ui()`  *Initialize the UI.*
- async `run_backtest()`  *Run the backtest (delegiert).*
- async `run_ai_review()`  *Run AI analysis on backtest results (delegiert).*
- `__init__(parent, current_symbol)`  *Initialize AI Backtest Dialog.*

## `src/ui/dialogs/ai_backtest_dialog_ai_display.py`

### `AIBacktestDialogAIDisplay(object)`
*Helper for AI analysis display.*

- `display_ai_analysis(review)`  *Display AI analysis results.*
- *...4 private methods*
- `__init__(parent)`

## `src/ui/dialogs/ai_backtest_dialog_ai_review.py`

### `AIBacktestDialogAIReview(object)`
*Helper for AI review execution.*

- async `run_ai_review()`  *Run AI analysis on backtest results.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/dialogs/ai_backtest_dialog_display.py`

### `AIBacktestDialogDisplay(object)`
*Helper for results display.*

- `display_results(result)`  *Display backtest results.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/dialogs/ai_backtest_dialog_execution.py`

### `AIBacktestDialogExecution(object)`
*Helper for backtest execution.*

- async `run_backtest()`  *Run the backtest.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/dialogs/ai_backtest_dialog_ui_tabs.py`

### `AIBacktestDialogUITabs(object)`
*Helper for creating dialog tabs.*

- `create_config_tab()` → `QWidget`  *Create configuration tab.*
- `create_results_tab()` → `QWidget`  *Create results tab.*
- `create_ai_tab()` → `QWidget`  *Create AI analysis tab.*
- `create_chart_tab()` → `QWidget`  *Create chart visualization tab with BacktestChartWidget.*
- `__init__(parent)`

## `src/ui/dialogs/backtest_dialog.py`

### `BacktestDialog(QDialog)`
*Dialog for running backtests.*

- `init_ui()`  *Initialize the backtest dialog UI.*
- async `run_backtest()`  *Run the backtest.*
- `export_results()`  *Export backtest results.*
- *...1 private methods*
- `__init__(ai_service, parent)`

## `src/ui/dialogs/bot_start_strategy_dialog.py`

### `BotStartStrategyDialog(QDialog)`
*Dialog for JSON-based strategy selection before bot start.*

- `accept()` → `None`  *Handle accept - emit strategy applied signal.*
- *...22 private methods*
- `__init__(parent)`

## `src/ui/dialogs/chart_markings_manager_dialog.py`

### `ChartMarkingsManagerDialog(QDialog)`
*Dialog for managing all chart markings.*

- *...13 private methods*
- `__init__(chart_widget, parent)`

## `src/ui/dialogs/color_palette_dialog.py`

### `ColorPaletteDialog(QDialog)`
*Dialog for editing color assignment rules.*

- *...4 private methods*
- `__init__(parent, color_manager)`  *Initialize color palette dialog.*

## `src/ui/dialogs/entry_analyzer/backtest_config/__init__.py`

### `BacktestConfigMixin(BacktestConfigUIMixin, BacktestConfigPersistenceMixin, RegimeDetectionLogicMixin)`
*Combined backtest config mixin (backward compatible).*


## `src/ui/dialogs/entry_analyzer/backtest_config/backtest_config_persistence.py`

### `BacktestConfigPersistenceMixin(object)`
*Config file I/O and table data management.*

- *...12 private methods*

## `src/ui/dialogs/entry_analyzer/backtest_config/backtest_config_ui.py`

### `BacktestConfigUIMixin(object)`
*UI setup for regime analysis tab.*

- *...7 private methods*

## `src/ui/dialogs/entry_analyzer/backtest_config/regime_detection_logic.py`

### `RegimeDetectionLogicMixin(object)`
*Core regime detection algorithm.*

- *...4 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_advanced_validation_mixin.py`

### `AdvancedValidationMixin(object)`
*Advanced validation (OOS, Market Phases, Walk-Forward).*

- *...7 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_ai.py`

### `AIMixin(AICopilotMixin)`
*AI Copilot functionality for Entry Analyzer.*


## `src/ui/dialogs/entry_analyzer/entry_analyzer_ai_copilot.py`

### `AICopilotMixin(object)`
*AI Copilot functionality for entry analysis.*

- *...4 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_analysis.py`

### `AnalysisMixin(object)`
*Analysis and validation functionality.*

- `set_analyzing(analyzing)` → `None`  *Set analyzing state.*
- *...12 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_backtest.py`

### `BacktestMixin(BacktestConfigMixin, BacktestRegimeMixin, BacktestRegimeSetMixin)`
*Backtest and regime analysis functionality.*


## `src/ui/dialogs/entry_analyzer/entry_analyzer_backtest_config.py`

### `BacktestConfigMixin(object)`
*Backtest configuration and execution functionality.*

- *...23 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_backtest_regime.py`

### `BacktestRegimeMixin(object)`
*Regime analysis functionality.*

- *...3 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_backtest_regime_set.py`

### `BacktestRegimeSetMixin(object)`
*Regime set creation functionality.*

- *...5 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_compounding_mixin.py`

### `CompoundingMixin(object)`
*Mixin for Compounding/P&L calculator tab in Entry Analyzer.*

- *...1 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_indicator_optimization_v2_mixin.py`

### `IndicatorOptimizationV2Mixin(object)`
*Stage 2: Indicator Optimization Execution (Indicators only).*

- *...12 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_indicator_results_v2_mixin.py`

### `IndicatorResultsV2Mixin(object)`
*Stage 2: Indicator Results Display and Export (no Regime).*

- *...8 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_indicator_setup_v2_mixin.py`

### `IndicatorSetupV2Mixin(object)`
*Stage 2: Indicator Setup UI (neu, ohne Regime).*

- *...5 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_indicator_worker.py`

### `IndicatorOptimizationWorkerV2(QThread)`
*Background worker for indicator optimization (Stage 2).*

- `run()` → `None`
- `stop()` → `None`  *Request graceful stop of optimization.*
- *...3 private methods*
- `__init__(config, parent)` → `None`

## `src/ui/dialogs/entry_analyzer/entry_analyzer_indicators_presets.py`

### `IndicatorsPresetsMixin(object)`
*Indicator parameter presets functionality.*

- *...4 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_patterns_mixin.py`

### `PatternDetectionMixin(object)`

- *...4 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_popup.py`

### `EntryAnalyzerPopup(QDialog, BacktestMixin, IndicatorsPresetsMixin, AnalysisMixin, AIMixin, CompoundingMixin, RegimeSetupMixin, RegimeOptimizationMixin, RegimeResultsMixin, IndicatorSetupV2Mixin, IndicatorOptimizationV2Mixin, IndicatorResultsV2Mixin, AdvancedValidationMixin, PatternDetectionMixin)`
*Entry Analyzer main dialog with mixin composition.*

- `set_context(symbol, timeframe, candles)` → `None`  *Set context for AI/Validation.*
- `set_analyzing(analyzing)` → `None`  *Set analyzing state and update progress bar.*
- `set_result(result)` → `None`  *Update UI with analysis results.*
- *...4 private methods*
- `__init__(parent)` → `None`  *Initialize dialog with all UI components.*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_regime_optimization_mixin.py`

### `RegimeOptimizationMixin(object)`
*Mixin for Regime Optimization tab in Entry Analyzer.*

- *...26 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_regime_results_mixin.py`

### `RegimeResultsMixin(object)`
*Mixin for Regime Results tab in Entry Analyzer.*

- *...8 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_regime_setup_mixin.py`

### `RegimeSetupMixin(object)`
*Dynamic Regime Setup tab - generates UI from JSON.*

- *...12 private methods*

## `src/ui/dialogs/entry_analyzer/entry_analyzer_workers.py`

### `CopilotWorker(QThread)`
*Background worker for AI Copilot analysis.*

- `run()` → `None`  *Execute AI analysis in background thread.*
- `__init__(analysis, symbol, timeframe, validation, parent)` → `None`

### `ValidationWorker(QThread)`
*Background worker for walk-forward validation.*

- `run()` → `None`  *Execute validation in background thread.*
- `__init__(analysis, candles, parent)` → `None`

### `BacktestWorker(QThread)`
*Background worker for full history backtesting.*

- `run()` → `None`  *Execute backtest in background thread.*
- `__init__(config_path, symbol, start_date, end_date, initial_capital, chart_data, data_timeframe, parent)` → `None`

## `src/ui/dialogs/entry_analyzer/regime_optimization/__init__.py`

### `RegimeOptimizationMixin(RegimeOptimizationInitMixin, RegimeOptimizationEventsMixin, RegimeOptimizationActionsMixin, RegimeOptimizationUpdatesMixin, RegimeOptimizationRenderingMixin)`
*Combined mixin for Regime Optimization tab in Entry Analyzer.*


## `src/ui/dialogs/entry_analyzer/regime_optimization/regime_optimization_actions.py`

### `RegimeOptimizationActionsMixin(object)`
*User action handlers for regime optimization.*

- *...3 private methods*

## `src/ui/dialogs/entry_analyzer/regime_optimization/regime_optimization_events.py`

### `RegimeOptimizationEventsMixin(object)`
*Event handlers for optimization lifecycle.*

- *...8 private methods*

## `src/ui/dialogs/entry_analyzer/regime_optimization/regime_optimization_init.py`

### `RegimeOptimizationInitMixin(object)`
*Initialization and UI setup for regime optimization tab.*

- *...1 private methods*

## `src/ui/dialogs/entry_analyzer/regime_optimization/regime_optimization_rendering.py`

### `RegimeOptimizationRenderingMixin(object)`
*UI rendering and display updates.*

- *...3 private methods*

## `src/ui/dialogs/entry_analyzer/regime_optimization/regime_optimization_updates.py`

### `RegimeOptimizationUpdatesMixin(object)`
*Data transformation and config building logic.*

- *...11 private methods*

## `src/ui/dialogs/error_dialog.py`

### Module Functions
- `show_error_dialog(title, message, parent)`  *Show a critical error dialog to the user.*

## `src/ui/dialogs/evaluation_color_manager.py`

### `ColorManager(object)`
*Manage color rules and auto-assignment for evaluation entries.*

- `save_rules()` → `None`  *Save current rules to persistent settings.*
- `pick_color_for_label(label)` → `str`  *Auto-assign color based on label keywords.*
- @staticmethod `ensure_alpha(color)` → `str`  *Ensure color has alpha channel for semi-transparent chart drawing.*
- `get_all_rules()` → `dict[str, str]`  *Get all color rules.*
- `update_rule(keyword, color)` → `None`  *Update a single color rule.*
- `reset_to_defaults()` → `None`  *Reset all rules to default values.*
- *...1 private methods*
- `__init__()`  *Initialize ColorManager with settings.*

## `src/ui/dialogs/evaluation_dialog.py`

### `ColorCellDelegate(QStyledItemDelegate)`
*Custom delegate for color column to prevent selection highlight.*

- `paint(painter, option, index)`  *Paint cell without selection highlight.*

### `EvaluationDialog(QDialog)`
*Dialog for viewing and editing chart evaluation entries.*

- *...21 private methods*
- `__init__(parent, entries)`  *Initialize evaluation dialog.*

## `src/ui/dialogs/evaluation_models.py`

### `EvaluationEntry(object)`
*Single evaluation entry (Support, Resistance, Target, etc.).*

- `is_range()` → `bool`  *Check if value is a price range (e.g., '100-200').*
- `get_range()` → `tuple[float, float] | None`  *Parse range value into (low, high).*
- `get_price()` → `float | None`  *Parse single price value.*
- `to_tuple()` → `tuple[str, str, str, str]`  *Convert to tuple for backward compatibility.*
- @classmethod `from_tuple(data)` → `EvaluationEntry`  *Create entry from tuple.*

## `src/ui/dialogs/evaluation_parser.py`

### `EvaluationParser(object)`
*Parse evaluation entries from text or list.*

- @classmethod `parse_from_content(content)` → `tuple[list[EvaluationEntry], list[str]]`  *Parse entries from text content.*
- @classmethod `parse_from_list(entries_list)` → `list[EvaluationEntry]`  *Parse entries from list of tuples.*
- @classmethod `validate_value(value)` → `bool`  *Validate if value matches expected numeric pattern.*
- *...1 private methods*

## `src/ui/dialogs/layout_manager_dialog.py`

### `LayoutManagerDialog(QDialog)`
*Dialog for managing saved chart layouts.*

- *...6 private methods*
- `__init__(layout_manager, parent)`  *Initialize the layout manager dialog.*

## `src/ui/dialogs/market_context_inspector.py`

### `MarketContextInspector(QDialog)`
*Dialog zum Inspizieren des MarketContext.*

- `set_context(context)` → `None`  *Setzt neuen Context und aktualisiert Anzeige.*
- *...13 private methods*
- `__init__(context, refresh_callback, parent)`

### Module Functions
- `show_context_inspector(context, refresh_callback, parent)` → `MarketContextInspector`  *Convenience-Funktion zum Anzeigen des Inspectors.*

## `src/ui/dialogs/optimization_tabs_mixin.py`

### `OptimizationTabsMixin(object)`
*Mixin providing tab creation methods for ParameterOptimizationDialog.*

- *...13 private methods*

## `src/ui/dialogs/order_dialog.py`

### `OrderDialog(QDialog)`
*Dialog for placing orders with AI analysis.*

- `init_ui()`  *Initialize the order dialog UI.*
- `on_order_type_changed(order_type)`  *Handle order type changes.*
- async `analyze_order()`  *Analyze order with AI.*
- async `place_order()`  *Place the order via broker.*
- *...1 private methods*
- `__init__(broker, ai_service, parent)`

## `src/ui/dialogs/parameter_optimization_dialog.py`

### `ParameterOptimizationDialog(OptimizationTabsMixin, QDialog)`
*Dialog for AI-guided parameter optimization.*

- `init_ui()`  *Initialize UI.*
- async `start_optimization()`  *Start parameter optimization.*
- `log_progress(message)`  *Log progress message.*
- `stop_optimization()`  *Stop optimization.*
- *...8 private methods*
- `__init__(parent, current_symbol)`  *Initialize Parameter Optimization Dialog.*

## `src/ui/dialogs/pattern_db_dialog.py`

### `PatternDatabaseDialog(PatternDbTabsMixin, PatternDbUIMixin, PatternDbDockerMixin, PatternDbBuildMixin, PatternDbLogMixin, PatternDbSearchMixin, PatternDbLifecycleMixin, PatternDbSettingsMixin, QDialog)`
*Dialog for managing the pattern database.*

- `__init__(parent)`

## `src/ui/dialogs/pattern_db_docker_mixin.py`

### `PatternDbDockerMixin(object)`
*PatternDbDockerMixin extracted from PatternDatabaseDialog.*

- *...4 private methods*

## `src/ui/dialogs/pattern_db_lifecycle_mixin.py`

### `PatternDbLifecycleMixin(object)`
*PatternDbLifecycleMixin extracted from PatternDatabaseDialog.*

- `closeEvent(event)`  *Handle dialog close.*

## `src/ui/dialogs/pattern_db_log_mixin.py`

### `PatternDbLogMixin(object)`
*PatternDbLogMixin extracted from PatternDatabaseDialog.*

- *...2 private methods*

## `src/ui/dialogs/pattern_db_search_mixin.py`

### `PatternDbSearchMixin(object)`
*PatternDbSearchMixin extracted from PatternDatabaseDialog.*

- *...1 private methods*

## `src/ui/dialogs/pattern_db_settings_mixin.py`

### `PatternDbSettingsMixin(object)`
*PatternDbSettingsMixin extracted from PatternDatabaseDialog.*

- `closeEvent(event)`  *Persist settings on close.*
- *...2 private methods*

## `src/ui/dialogs/pattern_db_tabs_mixin.py`

### `PatternDbTabsMixin(object)`
*Mixin providing tab creation methods for PatternDatabaseDialog.*

- *...16 private methods*

## `src/ui/dialogs/pattern_db_ui_mixin.py`

### `PatternDbUIMixin(object)`
*PatternDbUIMixin extracted from PatternDatabaseDialog.*

- *...9 private methods*

## `src/ui/dialogs/pattern_db_worker.py`

### `DatabaseBuildWorker(QThread)`
*Worker thread for building the pattern database.*

- `cancel()`  *Cancel the build process.*
- `run()`  *Run the database build in a separate thread.*
- *...5 private methods*
- `__init__(symbols, timeframes, days_back, is_crypto, window_size, step_size)`

## `src/ui/dialogs/settings_dialog.py`

### `SettingsDialog(SettingsTabsMixin, QDialog)`
*Application settings dialog.*

- `init_ui()`  *Initialize the settings dialog UI.*
- `load_current_settings()`  *Load current settings from QSettings.*
- `save_settings()`  *Save settings to QSettings and configuration.*
- *...9 private methods*
- `__init__(parent)`

## `src/ui/dialogs/settings_tabs_ai.py`

### `SettingsTabsAI(object)`
*Helper für AI Provider Tabs (OpenAI, Anthropic, Gemini).*

- `create_ai_tab()` → `QWidget`  *Create AI settings tab with provider sub-tabs.*
- *...7 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/dialogs/settings_tabs_alpaca.py`

### `SettingsTabsAlpaca(object)`
*Helper für Alpaca Market Data Tab (inkl. Download-Worker).*

- `build_alpaca_tab()` → `QWidget`  *Build Alpaca market data settings tab with download functionality.*
- *...6 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/dialogs/settings_tabs_basic.py`

### `WheelEventFilter(QObject)`
*Event filter that blocks mouse wheel events (Issue #13).*

- `eventFilter(obj, event)` → `bool`  *Filter out wheel events to prevent unwanted value changes.*

### `SettingsTabsBasic(object)`
*Helper für Basic Settings Tabs (General, Trading, Broker).*

- `create_general_tab()` → `QWidget`  *Create general settings tab.*
- `create_theme_tab()` → `QWidget`  *Create theme and UI customization settings tab.*
- `create_trading_tab()` → `QWidget`  *Create trading settings tab.*
- `create_broker_tab()` → `QWidget`  *Create broker settings tab.*
- *...11 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/dialogs/settings_tabs_bitunix.py`

### `SettingsTabsBitunix(object)`
*Helper für Bitunix Market Data Tab (inkl. Download-Worker).*

- `build_bitunix_tab()` → `QWidget`  *Create Bitunix Futures settings tab with download functionality.*
- *...8 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/dialogs/settings_tabs_data_quality.py`

### `DataQualityVerificationWorker(QThread)`
*Worker thread for database verification.*

- `run()`  *Run verification in background.*
- `__init__(db_path, symbol, timeframe)`

### `SettingsTabsDataQuality(object)`
*Helper class for Data Quality tab creation.*

- `create_data_quality_tab()` → `QWidget`  *Create data quality tab.*
- *...9 private methods*
- `__init__(parent)`  *Initialize with parent SettingsDialog reference.*

## `src/ui/dialogs/settings_tabs_market_basic.py`

### `SettingsTabsMarketBasic(object)`
*Helper für Market Data Basic Tabs (Alpha, Finnhub, Yahoo).*

- `build_alpha_tab()` → `QWidget`  *Build Alpha Vantage settings tab.*
- `build_finnhub_tab()` → `QWidget`  *Build Finnhub settings tab.*
- `build_yahoo_tab()` → `QWidget`  *Build Yahoo Finance settings tab.*
- `__init__(parent)`  *Args:*

## `src/ui/dialogs/settings_tabs_market_main.py`

### `SettingsTabsMarketMain(object)`
*Helper für Market Data Main Tab mit Provider-Tabs.*

- `create_market_data_tab()` → `QWidget`  *Create market data settings tab with provider sub-tabs.*
- *...1 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/dialogs/settings_tabs_mixin.py`

### `SettingsTabsMixin(object)`
*Mixin providing tab creation methods for SettingsDialog.*

- *...10 private methods*
- `__init__()`  *Initialize all helper modules for tab creation.*

## `src/ui/dialogs/strategy_concept_window.py`

### `StrategyConceptWindow(QDialog)`
*Main window for Pattern-Based Strategy Development.*

- `show_pattern_recognition_tab()`  *Switch to Pattern Recognition tab (Tab 1).*
- `show_pattern_integration_tab()`  *Switch to Pattern Integration tab (Tab 2).*
- `show_cel_strategy_editor_tab()`  *Switch to CEL Strategy Editor tab (Tab 3).*
- `closeEvent(event)`  *Handle window close event.*
- *...6 private methods*
- `__init__(parent)`  *Initialize Strategy Concept Window.*

## `src/ui/dialogs/strategy_settings_dialog.py`

### `StrategySettingsDialog(QDialog)`
*Strategy Settings Popup-Dialog.*

- `set_current_regime(regime)` → `None`  *Set current regime (called from Bot).*
- `set_active_strategy_set(strategy_set_id)` → `None`  *Set active strategy set (called from Bot).*
- *...13 private methods*
- `__init__(parent)`

## `src/ui/dialogs/trading_bot_settings_tab.py`

### `TradingBotSettingsTab(QWidget)`
*Kompletter Settings-Tab für den Trading Bot.*

- `get_all_settings()` → `dict`  *Get all settings as a combined dict.*
- *...7 private methods*
- `__init__(parent)`

## `src/ui/dialogs/variables/variable_manager_dialog.py`

### `VariableManagerDialog(QDialog)`
*Variable Manager Dialog for CRUD operations on project variables.*

- `closeEvent(event)`  *Handle dialog close event.*
- *...28 private methods*
- `__init__(project_vars_path, parent)`  *Initialize Variable Manager Dialog.*

## `src/ui/dialogs/variables/variable_reference_dialog.py`

### `VariableReferenceDialog(QDialog)`
*Variable Reference Dialog - Read-only browser for all CEL variables.*

- `set_sources(chart_window, bot_config, project_vars_path, indicators, regime)`  *Update data sources and reload.*
- `closeEvent(event)`  *Handle close event.*
- *...15 private methods*
- `__init__(chart_window, bot_config, project_vars_path, indicators, regime, enable_live_updates, update_interval_ms, parent)`  *Initialize variable reference dialog.*

## `src/ui/dialogs/zone_edit_dialog.py`

### `ZoneEditDialog(QDialog)`
*Dialog for editing a chart zone.*

- `get_values()` → `dict`  *Get the edited values.*
- `has_changes()` → `bool`  *Check if any values were changed.*
- *...6 private methods*
- `__init__(zone, parent)`  *Initialize the zone edit dialog.*

## `src/ui/icons.py`

### `IconProvider(object)`
*Provides PNG-based icons for the application.*

- `configure(icons_dir, invert_to_white)`  *Update provider configuration.*
- `set_theme(theme)`  *Change theme.*
- `get_icon(name)` → `QIcon`  *Get icon by name from PNG assets.*
- `get_available_icons()` → `list[str]`  *Get list of available icon names based on files in assets.*
- `__init__(theme, invert_to_white, icons_dir)`  *Initialize icon provider.*

### Module Functions
- `invert_icon_to_white(icon_path)` → `QPixmap`  *Invertiert schwarze Icons zu weiß mit transparentem Hintergrund.*
- `get_icon(name)` → `QIcon`  *Get icon by name using global provider.*
- `set_icon_theme(theme)`  *Set global icon theme.*
- `refresh_icons()`  *Clear icon cache and force reload.*
- `configure_icon_provider(icons_dir, invert_to_white)`  *Configure the global icon provider.*
- `get_available_icons()` → `list[str]`  *Get available icon names.*

## `src/ui/mixins/trading_mixin_base.py`

### `TradingMixinBase(object)`
*Base class for trading-related UI mixins.*

- *...1 private methods*

## `src/ui/models/watchlist_model.py`

### `WatchlistItem(object)`
*Data structure for a watchlist item.*

- `to_dict()` → `dict[str, Any]`  *Convert to dictionary for serialization.*

### `WatchlistModel(QAbstractTableModel)`
*Singleton Qt Model for watchlist data.*

- @classmethod `instance()` → `'WatchlistModel'`  *Get the singleton instance.*
- @classmethod `reset_instance()` → `None`  *Reset the singleton instance (for testing only).*
- `rowCount(parent)` → `int`  *Return number of rows.*
- `columnCount(parent)` → `int`  *Return number of columns.*
- `data(index, role)` → `Any`  *Return data for the given index and role.*
- `headerData(section, orientation, role)` → `Any`  *Return header data.*
- `add_symbol(symbol_data)` → `bool`  *Add a symbol to the watchlist.*
- `remove_symbol(symbol)` → `bool`  *Remove a symbol from the watchlist.*
- `clear()` → `None`  *Remove all symbols from the watchlist.*
- `get_symbols()` → `list[str]`  *Get list of all symbols.*
- `get_item(symbol)` → `Optional[WatchlistItem]`  *Get watchlist item by symbol.*
- `contains(symbol)` → `bool`  *Check if symbol is in watchlist.*
- `update_price(symbol, price, change, change_pct, volume, high, low)` → `bool`  *Update price data for a symbol.*
- `to_list()` → `list[dict]`  *Serialize watchlist to list of dicts.*
- `from_list(data)` → `None`  *Load watchlist from list of dicts or strings.*
- *...1 private methods*
- `__init__(parent)`  *Initialize the WatchlistModel.*

### Module Functions
- `get_watchlist_model()` → `WatchlistModel`  *Get the global WatchlistModel instance.*

## `src/ui/multi_chart/chart_set_dialog.py`

### `ChartSetDialog(QDialog)`
*Dialog for opening and managing chart sets.*

- *...14 private methods*
- `__init__(layout_manager, parent)`

## `src/ui/multi_chart/layout_config_models.py`

### `ChartWindowConfig(object)`
*Configuration for a single chart window.*

- `to_dict()` → `dict`  *Convert to dictionary for JSON serialization.*
- @classmethod `from_dict(data)` → `'ChartWindowConfig'`  *Create from dictionary.*

### `ChartLayoutConfig(object)`
*Configuration for a complete chart layout (multiple windows).*

- `to_dict()` → `dict`  *Convert to dictionary for JSON serialization.*
- @classmethod `from_dict(data)` → `'ChartLayoutConfig'`  *Create from dictionary.*

## `src/ui/multi_chart/layout_default_templates.py`

### `LayoutDefaultTemplates(object)`
*Helper for creating default layout templates.*

- `create_default_layouts()` → `None`  *Create default layout templates if none exist.*
- *...4 private methods*
- `__init__(parent)`

## `src/ui/multi_chart/layout_manager.py`

### `ChartLayoutManager(QObject)`
*Manages multiple chart windows for pre-trade analysis (REFACTORED).*

- `set_history_manager(history_manager)` → `None`  *Set the history manager for data loading.*
- @property `active_windows()` → `list['ChartWindow']`  *Get list of active chart windows.*
- @property `current_layout()` → `ChartLayoutConfig | None`  *Get the current layout configuration.*
- `get_available_monitors()` → `list[dict]`  *Get list of available monitors with their geometry (delegiert).*
- `get_monitor_geometry(monitor_index)`  *Get the geometry of a specific monitor (delegiert).*
- `open_layout(layout, symbol)` → `list['ChartWindow']`  *Open a chart layout with multiple windows (delegiert).*
- `close_all_windows()` → `None`  *Close all active chart windows (delegiert).*
- `open_pre_trade_analysis(symbol)` → `list['ChartWindow']`  *Open pre-trade analysis charts for a symbol (delegiert).*
- `create_layout_from_current(name, description)` → `ChartLayoutConfig | None`  *Create a layout configuration from currently open windows (delegiert).*
- `save_layout(layout)` → `bool`  *Save a layout configuration to file (delegiert).*
- `load_layout(name)` → `ChartLayoutConfig | None`  *Load a layout configuration from file (delegiert).*
- `get_available_layouts()` → `list[str]`  *Get list of available layout names (delegiert).*
- `delete_layout(name)` → `bool`  *Delete a saved layout (delegiert).*
- `__init__(parent)`

## `src/ui/multi_chart/layout_monitor_manager.py`

### `LayoutMonitorManager(object)`
*Helper for monitor detection and geometry queries.*

- `get_available_monitors()` → `list[dict]`  *Get list of available monitors with their geometry.*
- `get_monitor_geometry(monitor_index)` → `QRect`  *Get the geometry of a specific monitor.*
- `__init__(parent)`

## `src/ui/multi_chart/layout_persistence.py`

### `LayoutPersistence(object)`
*Helper for layout file persistence.*

- `save_layout(layout)` → `bool`  *Save a layout configuration to file.*
- `load_layout(name)` → `'ChartLayoutConfig | None'`  *Load a layout configuration from file.*
- `get_available_layouts()` → `list[str]`  *Get list of available layout names.*
- `delete_layout(name)` → `bool`  *Delete a saved layout.*
- `__init__(parent)`

## `src/ui/multi_chart/layout_window_operations.py`

### `LayoutWindowOperations(object)`
*Helper for window operations and layout management.*

- `open_layout(layout, symbol)` → `list['ChartWindow']`  *Open a chart layout with multiple windows.*
- `close_all_windows()` → `None`  *Close all active chart windows.*
- `open_pre_trade_analysis(symbol)` → `list['ChartWindow']`  *Open pre-trade analysis charts for a symbol.*
- `create_layout_from_current(name, description)` → `'ChartLayoutConfig | None'`  *Create a layout configuration from currently open windows.*
- *...4 private methods*
- `__init__(parent)`

## `src/ui/splash_screen.py`

### `SplashScreen(QWidget)`
*Frameless splash screen with logo and progress bar.*

- `set_progress(value, status)` → `None`  *Set progress bar value (0-100) and optional status text.*
- `finish_and_close(delay_ms)` → `None`  *Finish progress, show terminal message, wait for delay and then close.*
- `keyPressEvent(event)` → `None`  *Handle keyboard events - Escape key triggers termination.*
- *...3 private methods*
- `__init__(icon_path, title)`

## `src/ui/themes.py`

### `ThemeManager(object)`
*Manages application themes using the central Design System.*

- `get_theme(theme_name, overrides)` → `str`  *Get the stylesheet for the specified theme name.*
- `get_dark_theme()` → `str`
- `get_light_theme()` → `str`
- *...1 private methods*
- `__init__()`  *Initialize theme manager.*

## `src/ui/threads/indicator_optimization_core.py`

### `IndicatorOptimizationThread(QThread)`
*Background thread for indicator parameter optimization.*

- `stop()`  *Request thread to stop.*
- `run()`  *Main optimization loop - runs in background thread.*
- `__init__(selected_indicators, param_ranges, json_config_path, symbol, start_date, end_date, initial_capital, test_type, trade_side, chart_data, data_timeframe, parent)`  *Initialize optimization thread.*

## `src/ui/threads/indicator_optimization_phases.py`

### `OptimizationPhaseHandler(object)`
*Handles optimization phases: regime detection, parameter generation, indicator calculation.*

- `detect_regimes(df)` → `pd.Series`  *Detect regime for each bar using JSON config if available.*
- `build_regime_history(df, regime_labels)` → `List[Dict[str, Any]]`  *Build regime history from regime labels for visualization.*
- `generate_parameter_combinations()` → `Dict[str, List[Dict[str, int]]]`  *Generate all parameter combinations using Iterator Pattern.*
- `calculate_indicator(df, indicator_type, params)` → `pd.DataFrame`  *Calculate indicator using Factory Pattern.*
- *...2 private methods*
- `__init__(thread)`  *Initialize with reference to parent thread.*

## `src/ui/threads/indicator_optimization_results.py`

### `OptimizationResultsProcessor(object)`
*Processes optimization results and calculates scores.*

- `score_indicator(df, indicator_type, params, regime)` → `Optional[Dict[str, any]]`  *Score indicator performance for given regime.*
- `generate_signals(df, indicator_type, test_type, trade_side)` → `pd.Series`  *Generate trading signals using Strategy Pattern.*
- `calculate_metrics(df, signals)` → `Dict[str, float]`  *Calculate performance metrics for signals.*
- `calculate_proximity_score(df, signals, trade_side)` → `float`  *Calculate proximity score based on distance to price extremes.*
- `calculate_composite_score(metrics)` → `float`  *Calculate composite score (0-100) from metrics.*
- `__init__(thread)`  *Initialize with reference to parent thread.*

## `src/ui/threads/indicator_optimization_thread.py`

### `IndicatorOptimizationThread(QThread)`
*Background thread for indicator parameter optimization.*

- `stop()`  *Request thread to stop.*
- `run()`  *Main optimization loop - runs in background thread.*
- *...11 private methods*
- `__init__(selected_indicators, param_ranges, json_config_path, symbol, start_date, end_date, initial_capital, test_type, trade_side, chart_data, data_timeframe, parent)`  *Initialize optimization thread.*

## `src/ui/threads/regime_optimization_thread.py`

### `RegimeOptimizationThread(QThread)`
*Background thread for Optuna TPE regime optimization.*

- `request_stop()`  *Request graceful stop of optimization.*
- `run()`  *Execute Optuna TPE regime optimization.*
- *...2 private methods*
- `__init__(df, config_template_path, param_grid, scope, max_trials, json_config)`  *Initialize regime optimization thread.*

## `src/ui/utils/chart_data_helper.py`

### `ChartDataHelper(object)`
*Helper for accessing chart data from parent widgets.*

- @staticmethod `get_bars_from_chart(widget, window_size, chart_window)` → `Tuple[Optional[List], Optional[str], Optional[str]]`  *Extract HistoricalBar objects from parent chart widget.*

## `src/ui/widgets/alerts.py`

### `AlertsWidget(QWidget)`
*Widget for displaying trading alerts.*

- `init_ui()`  *Initialize the alerts UI.*
- `setup_event_handlers()`  *Setup event bus handlers.*
- `on_alert_triggered(event)`  *Handle alert triggered event.*
- `on_order_rejected(event)`  *Handle order rejected event.*
- `on_app_error(event)`  *Handle application error event.*
- `add_alert(alert_data)`  *Add a new alert to the list.*
- `__init__()`

## `src/ui/widgets/alpaca_tradingview_chart.py`

### `AlpacaTradingViewChart(ChartAIMarkingsMixin, ChartMarkingMixin, LevelZonesMixin, EntryAnalyzerMixin, BotOverlayMixin, ToolbarMixin, IndicatorMixin, AlpacaStreamingMixin, DataLoadingMixin, ChartStateMixin, EmbeddedTradingViewChartUIMixin, EmbeddedTradingViewChartMarkingMixin, EmbeddedTradingViewChartJSMixin, EmbeddedTradingViewChartViewMixin, EmbeddedTradingViewChartLoadingMixin, EmbeddedTradingViewChartEventsMixin, QWidget)`
*Alpaca-only TradingView Lightweight Charts widget.*

- *...6 private methods*
- `__init__(history_manager)`  *Initialize Alpaca chart widget.*
- `__del__()`  *Cleanup event bus connections.*

## `src/ui/widgets/analysis_tabs/ai_chat_tab.py`

### `ChatWorker(QThread)`
*Background worker for AI chat requests.*

- `run()`  *Execute AI chat request.*
- *...1 private methods*
- `__init__(prompt, context_text, model)`

### `AIChatTab(QWidget)`
*AI Chat Tab with MarketContext integration (Phase 5.8-5.10).*

- `set_market_context(context)` → `None`  *Set the MarketContext for chat (Phase 5.8).*
- `draw_detected_level(index)` → `None`  *Draw a detected level on the chart.*
- *...14 private methods*
- `__init__(context)`

## `src/ui/widgets/analysis_tabs/data_overview_tab.py`

### `DataOverviewTab(QWidget)`
*Tab displaying all data sent to AI for analysis.*

- `set_market_context(context)` → `None`  *Set the MarketContext for data display.*
- `set_features(features)` → `None`  *Set the features data from Deep Analysis.*
- *...22 private methods*
- `__init__(context)`

## `src/ui/widgets/analysis_tabs/deep_run_tab.py`

### `DeepRunTab(QWidget)`
*UI for executing the analysis and viewing results.*

- *...4 private methods*
- `__init__(context)`

## `src/ui/widgets/analysis_tabs/indicators_tab.py`

### `IndicatorsTab(QWidget)`
*UI for viewing/editing the active indicator preset.*

- *...2 private methods*
- `__init__(context)`

## `src/ui/widgets/analysis_tabs/log_viewer_tab.py`

### `LogViewerTab(QWidget)`
*UI for viewing and managing the AI Analysis log file.*

- `closeEvent(event)`  *Stop timer when tab is closed.*
- *...5 private methods*
- `__init__(context)`

## `src/ui/widgets/analysis_tabs/strategy_tab.py`

### `StrategyTab(QWidget)`
*UI for selecting strategy, checking regime compatibility, and AI daily trend analysis.*

- `get_last_analysis()` → `dict | None`  *Get the last analysis result.*
- `set_chart_context(chart_widget)`  *Set chart context for analysis (called from parent window).*
- `get_last_analysis()` → `dict | None`  *Get the last analysis result.*
- `set_chart_context(chart_widget)`  *Set chart context for analysis (called from parent window).*
- *...28 private methods*
- `__init__(context)`

## `src/ui/widgets/analysis_tabs/timeframes_tab.py`

### `TimeframesTab(QWidget)`
*UI for configuring analysis timeframes.*

- *...3 private methods*
- `__init__(context)`

## `src/ui/widgets/backtest_chart_widget.py`

### `BacktestChartWidget(QWidget)`
*Chart widget for displaying backtest results.*

- `load_backtest_result(result)` → `None`  *Load and display backtest result.*
- `clear_chart()` → `None`  *Clear the current chart.*
- `toggle_markers(show)` → `None`  *Toggle trade markers visibility.*
- `closeEvent(event)` → `None`  *Handle widget close event.*
- *...10 private methods*
- `__init__(parent)`  *Initialize backtest chart widget.*

## `src/ui/widgets/base_chart_widget.py`

### `QWidgetABCMeta(type(QWidget), ABCMeta)`
*Combined metaclass to resolve conflict between QWidget and ABC.*


### `BaseChartWidget(QWidget)`
*Abstract base class for chart widgets.*

- `load_data(data)`  *Load OHLCV data into chart.*
- `update_indicators()`  *Update technical indicators on chart.*
- `clear()`  *Clear chart data.*
- *...2 private methods*
- `__init__(parent)`  *Initialize base chart widget.*

## `src/ui/widgets/bitunix_hedge_execution_widget.py`

### `BitunixHedgeExecutionWidget(QGroupBox)`
*Bitunix HEDGE Execution Widget.*

- `set_status_labels(state_label, order_id_label, position_id_label, adaptive_label, kill_btn)`  *Set external status labels from the Status Panel.*
- *...25 private methods*
- `__init__(parent)`

## `src/ui/widgets/bitunix_trading/backtest_callbacks_config_mixin.py`

### `BacktestCallbacksConfigMixin(object)`
*Configuration management callbacks*

- *...3 private methods*

## `src/ui/widgets/bitunix_trading/backtest_callbacks_template_mixin.py`

### `BacktestCallbacksTemplateMixin(object)`
*Template management callbacks*

- *...22 private methods*

## `src/ui/widgets/bitunix_trading/backtest_callbacks_testing_mixin.py`

### `BacktestCallbacksTestingMixin(object)`
*Backtest and optimization testing callbacks*

- *...4 private methods*

## `src/ui/widgets/bitunix_trading/backtest_config_collection.py`

### `BacktestConfigCollection(object)`
*Helper für Engine Config Collection aus UI Widgets.*

- `collect_engine_configs()` → `Dict[str, Any]`  *Sammelt alle Engine-Konfigurationen aus den Engine Settings Tabs.*
- `find_chart_window()` → `Optional['QWidget']`  *Sucht das ChartWindow in der Parent-Hierarchie.*
- `get_default_engine_configs()` → `Dict[str, Any]`  *Gibt Default-Engine-Konfigurationen zurück.*
- *...2 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/backtest_config_manager.py`

### `BacktestConfigManager(object)`
*Verwaltet Engine-Konfigurationen für Backtests.*

- `collect_engine_configs()` → `Dict[str, Any]`  *Sammelt alle Engine-Konfigurationen aus den Engine Settings Tabs.*
- `get_parameter_space_from_configs()` → `Dict[str, list]`  *Erstellt einen Parameter-Space für Batch-Tests basierend auf Engine-Configs.*
- `get_parameter_specification()` → `list[Dict[str, Any]]`  *Erstellt eine vollständige Parameter-Spezifikation als Tabelle.*
- `get_available_indicator_sets()` → `list[Dict[str, Any]]`  *Gibt die verfügbaren Indikator-Sets zurück.*
- `generate_ai_test_variants(base_spec, num_variants)` → `list[Dict[str, Any]]`  *Generiert intelligente Test-Varianten basierend auf der Parameter-Spezifikation.*
- `get_signal_callback()`  *Gibt den Signal-Callback für Backtests zurück.*
- `__init__(parent_widget)`  *Args:*

## `src/ui/widgets/bitunix_trading/backtest_config_param_space.py`

### `BacktestConfigParamSpace(object)`
*Helper für Parameter Space Generation.*

- `get_parameter_space_from_configs()` → `Dict[str, list]`  *Erstellt einen Parameter-Space für Batch-Tests basierend auf Engine-Configs.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/backtest_config_param_spec.py`

### `BacktestConfigParamSpec(object)`
*Helper für Parameter Specification (detaillierte Parameter-Tabelle).*

- `get_parameter_specification()` → `list[Dict[str, Any]]`  *Erstellt eine vollständige Parameter-Spezifikation als Tabelle.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/backtest_config_variants.py`

### `BacktestConfigVariants(object)`
*Helper für Indicator Sets und AI Variant Generation.*

- `get_available_indicator_sets()` → `list[Dict[str, Any]]`  *Gibt die verfügbaren Indikator-Sets zurück.*
- `generate_ai_test_variants(base_spec, num_variants)` → `list[Dict[str, Any]]`  *Generiert intelligente Test-Varianten basierend auf der Parameter-Spezifikation.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/backtest_results_display.py`

### `BacktestResultsDisplay(object)`
*Verwaltet die Anzeige von Backtest-Ergebnissen.*

- `on_backtest_finished(result)` → `None`  *Verarbeitet Backtest-Ergebnis und aktualisiert UI.*
- `update_metrics_table(metrics)` → `None`  *Aktualisiert die Metriken-Tabelle.*
- `update_trades_table(trades)` → `None`  *Aktualisiert die Trades-Tabelle.*
- `update_breakdown_table(trades)` → `None`  *Aktualisiert die Regime/Setup Breakdown Tabelle.*
- `update_batch_results_table(results)` → `None`  *Aktualisiert die Batch-Ergebnisse Tabelle.*
- `update_wf_results_table(fold_results)` → `None`  *Aktualisiert die Walk-Forward Ergebnisse Tabelle.*
- `__init__(parent_widget)`  *Initialisiert BacktestResultsDisplay.*

## `src/ui/widgets/bitunix_trading/backtest_tab.py`

### `BacktestTab(BacktestTabUISetupMixin, BacktestTabUIResultsMixin, BacktestTabUIBatchMixin, BacktestTabCallbacksMixin, BacktestTabConfigMixin, BacktestTabUpdateMixin, BacktestTabExportMixin, QWidget)`
*Backtest Tab - UI für historisches Strategietesting.*

- `get_available_indicator_sets()` → `list[Dict[str, Any]]`  *Delegate to BacktestConfigVariants.*
- `generate_ai_test_variants(base_spec, num_variants)` → `list[Dict[str, Any]]`  *Delegate to BacktestConfigVariants.*
- `set_history_manager(history_manager)` → `None`  *Setzt den History Manager.*
- *...16 private methods*
- `__init__(history_manager, parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/backtest_tab_batch_execution.py`

### `BacktestTabBatchExecution(object)`
*Helper for batch optimization and walk-forward execution.*

- async `on_batch_clicked()` → `None`  *Startet Batch-Test mit Parameter-Optimierung.*
- async `on_wf_clicked()` → `None`  *Startet Walk-Forward Analyse - delegiert an WalkForwardRunner.*
- `__init__(parent)`

## `src/ui/widgets/bitunix_trading/backtest_tab_callbacks_mixin.py`

### `BacktestTabCallbacksMixin(BacktestCallbacksTestingMixin, BacktestCallbacksTemplateMixin, BacktestCallbacksConfigMixin)`
*Backtest Tab Callbacks - Uses sub-mixin pattern for better modularity.*


## `src/ui/widgets/bitunix_trading/backtest_tab_config_mixin.py`

### `BacktestTabConfigMixin(object)`
*Configuration management and parameter handling*

- `collect_engine_configs()` → `Dict[str, Any]`  *Sammelt alle Engine-Konfigurationen aus den Engine Settings Tabs.*
- `get_parameter_specification()` → `list[Dict[str, Any]]`  *Erstellt eine vollständige Parameter-Spezifikation als Tabelle.*
- `get_parameter_space_from_configs()` → `Dict[str, list]`  *Erstellt einen Parameter-Space für Batch-Tests basierend auf Engine-Configs.*
- *...5 private methods*

## `src/ui/widgets/bitunix_trading/backtest_tab_execution.py`

### `BacktestTabExecution(object)`
*Helper for single backtest execution.*

- `build_backtest_config()`  *Erstellt BacktestConfig aus UI-Werten.*
- async `on_start_clicked()` → `None`  *Startet den Backtest.*
- `on_stop_clicked()` → `None`  *Stoppt den Backtest.*
- `__init__(parent)`

## `src/ui/widgets/bitunix_trading/backtest_tab_export_mixin.py`

### `BacktestTabExportMixin(object)`
*Export functions (CSV, JSON, batch results)*

- *...5 private methods*

## `src/ui/widgets/bitunix_trading/backtest_tab_handlers.py`

### `BacktestTabHandlers(object)`
*Helper for config and UI event handlers.*

- `on_load_configs_clicked()` → `None`  *Lädt Engine-Configs und zeigt sie im Config Inspector an.*
- `on_auto_generate_clicked()` → `None`  *Generiert automatisch Test-Varianten.*
- `on_indicator_set_changed(index)` → `None`  *Handler für Indikator-Set Auswahl.*
- `__init__(parent)`

## `src/ui/widgets/bitunix_trading/backtest_tab_logging.py`

### `BacktestTabLogging(object)`
*Helper for logging and progress display.*

- `on_progress_updated(progress, message)` → `None`  *Update Progress Bar.*
- `on_log_message(message)` → `None`  *Fügt Log-Nachricht hinzu.*
- `log(message)` → `None`  *Log-Nachricht (thread-safe).*
- `__init__(parent)`

## `src/ui/widgets/bitunix_trading/backtest_tab_main.py`

### `BacktestTab(QWidget)`
*Backtest Tab - Main Orchestrator (REFACTORED via Composition).*

- *...1 private methods*
- `__init__(history_manager, parent)`  *Initialisiert BacktestTab.*

## `src/ui/widgets/bitunix_trading/backtest_tab_settings.py`

### `BacktestTabSettings(object)`
*Helper for settings persistence.*

- `load_settings()` → `None`  *Lädt alle Einstellungen aus JSON und QSettings.*
- `save_settings()` → `None`  *Speichert alle Einstellungen in JSON und QSettings.*
- `__init__(parent)`

## `src/ui/widgets/bitunix_trading/backtest_tab_ui.py`

### `BacktestTabUI(object)`
*Main UI orchestrator for Backtest Tab using composition pattern.*

- `setup_ui()` → `None`  *Erstellt das UI Layout (delegates to helper builders).*
- `create_compact_button_row()`  *Create button toolbar (delegated to toolbar builder).*
- `create_setup_tab()`  *Create setup tab (delegated to setup builder).*
- `create_execution_tab()`  *Create execution tab (delegated to setup builder).*
- `create_results_tab()`  *Create results tab (delegated to results builder).*
- `create_batch_tab()`  *Create batch/WF tab (delegated to results builder).*
- `create_kpi_card(title, value, color)`  *Create KPI card (delegated to results builder).*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/backtest_tab_ui_batch_mixin.py`

### `BacktestTabUIBatchMixin(object)`
*UI creation and updates for Batch tab*

- *...3 private methods*

## `src/ui/widgets/bitunix_trading/backtest_tab_ui_results.py`

### `BacktestTabUIResults(object)`
*Results and Batch tabs builder for backtest tab.*

- `create_results_tab()` → `QWidget`  *Erstellt Results Tab.*
- `create_batch_tab()` → `QWidget`  *Erstellt Batch/Walk-Forward Tab mit Config Inspector.*
- `create_kpi_card(title, value, color)` → `QFrame`  *Erstellt eine KPI-Karte.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/backtest_tab_ui_results_mixin.py`

### `BacktestTabUIResultsMixin(object)`
*UI creation and updates for Results tab*

- *...4 private methods*

## `src/ui/widgets/bitunix_trading/backtest_tab_ui_setup.py`

### `BacktestTabUISetup(object)`
*Setup and Execution tabs builder for backtest tab.*

- `create_setup_tab()` → `QWidget`  *Erstellt Setup Tab.*
- `create_execution_tab()` → `QWidget`  *Erstellt Execution Settings Tab.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/backtest_tab_ui_setup_mixin.py`

### `BacktestTabUISetupMixin(object)`
*UI creation for Setup and Execution tabs*

- *...5 private methods*

## `src/ui/widgets/bitunix_trading/backtest_tab_ui_toolbar.py`

### `BacktestTabUIToolbar(object)`
*Toolbar builder for backtest tab.*

- `create_compact_button_row()` → `QVBoxLayout`  *Erstellt kompakte Button-Zeilen (2 Reihen für bessere Sichtbarkeit).*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/backtest_tab_update_mixin.py`

### `BacktestTabUpdateMixin(object)`
*UI update methods and progress tracking*

- *...3 private methods*

## `src/ui/widgets/bitunix_trading/backtest_tab_worker.py`

### `BatchTestWorker(QThread)`
*Worker thread to run batch tests without blocking the UI.*

- `run()` → `None`  *Execute batch test in background thread.*
- `__init__(batch_config)` → `None`  *Initialize batch test worker.*

## `src/ui/widgets/bitunix_trading/backtest_template_manager.py`

### `BacktestTemplateManager(object)`
*Verwaltet Template-Operationen für Backtest-Konfigurationen.*

- `on_save_template_clicked()` → `None`  *Speichert die aktuelle Basistabelle als JSON-Template.*
- `on_load_template_clicked()` → `None`  *Lädt ein gespeichertes JSON-Template.*
- `on_derive_variant_clicked()` → `None`  *Erstellt eine Variante basierend auf der aktuellen Basistabelle.*
- *...3 private methods*
- `__init__(parent_widget)`  *Initialisiert BacktestTemplateManager.*

## `src/ui/widgets/bitunix_trading/bitunix_api_widget_events.py`

### `BitunixAPIWidgetEvents(object)`
*Mixin providing event handlers for BitunixTradingAPIWidget.*

- *...23 private methods*

## `src/ui/widgets/bitunix_trading/bitunix_api_widget_logic.py`

### `BitunixAPIWidgetLogic(object)`
*Mixin providing API logic for BitunixTradingAPIWidget.*

- `set_adapter(adapter)`  *Set trading adapter.*
- `set_symbol(symbol)`  *Set trading symbol.*
- `set_price(price)`  *Update current price.*
- *...4 private methods*

## `src/ui/widgets/bitunix_trading/bitunix_api_widget_ui.py`

### `BitunixAPIWidgetUI(object)`
*Mixin providing UI construction methods for BitunixTradingAPIWidget.*

- *...12 private methods*

## `src/ui/widgets/bitunix_trading/bitunix_trading_mixin.py`

### `BitunixTradingMixin(TradingMixinBase)`
*Mixin that adds Bitunix trading functionality to a window.*

- `setup_bitunix_trading(chart_widget, adapter)` → `bool`  *Set up the Bitunix trading functionality.*
- `toggle_bitunix_widget()` → `None`  *Toggle visibility of the Bitunix trading widget.*
- `show_bitunix_widget()` → `None`  *Show the Bitunix trading widget.*
- `hide_bitunix_widget()` → `None`  *Hide the Bitunix trading widget.*
- @property `bitunix_widget()` → `Any`  *Get the Bitunix trading widget.*
- @property `bitunix_adapter()` → `Any`  *Get the Bitunix adapter.*
- `cleanup_bitunix_trading()` → `None`  *Clean up Bitunix resources.*
- *...8 private methods*

## `src/ui/widgets/bitunix_trading/bitunix_trading_mode_manager.py`

### `BitunixTradingModeManager(object)`
*Helper für Live/Paper Mode Switching.*

- `toggle_mode(is_paper)` → `None`  *Switch between Live and Paper adapters.*
- `update_mode_ui()` → `None`  *Update banner and colors based on mode.*
- `reset_paper_account()` → `None`  *Reset paper trading balance to 10,000 USDT.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bitunix_trading_order_handler.py`

### `BitunixTradingOrderHandler(object)`
*Helper für Order Entry und Execution Logic.*

- `on_direction_changed(index)` → `None`  *Handle position direction change.*
- `get_selected_direction()` → `str`  *Returns the selected position direction.*
- `on_order_type_changed(order_type)` → `None`  *Handle order type change.*
- `on_investment_changed(value)` → `None`  *When investment amount changes, calculate quantity.*
- `on_quantity_changed(value)` → `None`  *When quantity changes, calculate investment amount.*
- `on_price_changed(value)` → `None`  *When price changes, recalculate investment from quantity.*
- `on_leverage_changed(value)` → `None`  *Update leverage label when slider moves.*
- async `on_buy_clicked()` → `None`  *Handle BUY button click.*
- async `on_sell_clicked()` → `None`  *Handle SELL button click.*
- *...4 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bitunix_trading_positions_manager.py`

### `BitunixTradingPositionsManager(object)`
*Helper für Position Loading und Persistence.*

- `on_tick_price_updated(price)` → `None`  *Update current price in positions table in real-time.*
- `save_positions_to_file()` → `None`  *Save current positions table to JSON file.*
- `load_positions_from_file()` → `None`  *Load positions from JSON file into table.*
- `delete_selected_row()` → `None`  *Delete the selected row from positions table.*
- *...1 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bitunix_trading_ui.py`

### `BitunixTradingUI(object)`
*Verwaltet UI-Komponenten für Bitunix Trading Widget.*

- `build_account_section()` → `QGroupBox`  *Build account information display.*
- `build_order_entry_section()` → `QGroupBox`  *Build order entry panel.*
- `build_positions_section()` → `QGroupBox`  *Build positions table.*
- `__init__(parent_widget)`  *Initialisiert BitunixTradingUI.*

## `src/ui/widgets/bitunix_trading/bitunix_trading_widget.py`

### `BitunixTradingWidget(QDockWidget)`
*Dockable trading widget for Bitunix Futures.*

- `set_history_manager(history_manager)`  *Inject history manager into paper adapter for price feeds and bot data.*
- `set_adapter(adapter)` → `None`  *Set the Bitunix adapter.*
- `set_symbol(symbol)` → `None`  *Set the current trading symbol.*
- `closeEvent(event)` → `None`  *Handle widget close event.*
- *...16 private methods*
- `__init__(adapter, parent)`  *Initialize Bitunix trading widget.*

## `src/ui/widgets/bitunix_trading/bot_tab.py`

### `BotTab(BotTabUIMixin, BotTabControlsMixin, BotTabMonitoringMixin, BotTabLogsMixin, QWidget)`
*Bot Trading Tab - UI für automatischen Trading Bot.*

- `__init__(paper_adapter, history_manager, parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bot_tab_control.py`

### `BotTabControl(object)`
*Verwaltet Bot Control und Engine-Pipeline.*

- async `on_start_clicked()` → `None`  *Startet den Bot (neue Engine-Pipeline).*
- async `on_start_json_clicked()` → `None`  *Startet Bot mit JSON-basierter Entry-Logik (NEUE METHODE).*
- async `on_stop_clicked()` → `None`  *Stoppt den Bot (neue Engine-Pipeline).*
- async `on_close_position_clicked()` → `None`  *Schließt die aktuelle Position manuell (neue Pipeline).*
- `toggle_status_panel()` → `None`  *Togglet die Sichtbarkeit des Status Panels.*
- `on_status_panel_refresh()` → `None`  *Callback wenn Status Panel Refresh angefordert wird.*
- `toggle_journal()` → `None`  *Togglet die Sichtbarkeit des Trading Journals.*
- `update_engine_configs()` → `None`  *Aktualisiert die Konfiguration aller laufenden Engines.*
- `apply_config(config)` → `None`  *Wendet neue Konfiguration an.*
- `periodic_update()` → `None`  *Periodisches UI Update (Performance-Tuning).*
- `cleanup()` → `None`  *Cleanup bei Widget-Zerstörung (App schließt).*
- `restore_saved_position()` → `None`  *Stellt gespeicherte Position beim Start wieder her.*
- *...4 private methods*
- `__init__(parent_widget)`  *Initialisiert BotTabControl.*

## `src/ui/widgets/bitunix_trading/bot_tab_control_engine_init.py`

### `BotTabControlEngineInit(object)`
*Helper für Engine Initialization und Config Management.*

- `update_engine_configs()` → `None`  *Aktualisiert die Konfiguration aller laufenden Engines.*
- *...1 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bot_tab_control_persistence.py`

### `BotTabControlPersistence(object)`
*Helper für Settings und Position Persistence.*

- `apply_config(config)` → `None`  *Wendet neue Konfiguration an und speichert sie.*
- `cleanup()` → `None`  *Cleanup bei Widget-Zerstörung (App schließt).*
- `restore_saved_position()` → `None`  *Issue #20: Stellt gespeicherte Position beim Start wieder her.*
- *...4 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bot_tab_control_pipeline.py`

### `BotTabControlPipeline(object)`
*Helper für Main Engine Pipeline Execution.*

- async `process_market_data_through_engines(symbol, timeframe)` → `None`  *Holt Marktdaten und schickt sie durch die Engine-Pipeline.*
- *...4 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bot_tab_control_trade.py`

### `BotTabControlTrade(object)`
*Helper für Trade Execution und Position Monitoring.*

- *...12 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bot_tab_control_ui.py`

### `BotTabControlUI(object)`
*Helper für UI Updates und Visual Elements.*

- `toggle_status_panel()` → `None`  *Togglet die Sichtbarkeit des Status Panels.*
- `on_status_panel_refresh()` → `None`  *Callback wenn Status Panel Refresh angefordert wird.*
- `toggle_journal()` → `None`  *Togglet die Sichtbarkeit des Trading Journals.*
- *...4 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bot_tab_controls_mixin.py`

### `BotTabControlsMixin(object)`
*Bot control methods (settings, toggle, apply)*

- *...9 private methods*

## `src/ui/widgets/bitunix_trading/bot_tab_display_updates.py`

### `BotTabDisplayUpdates(object)`
*Helper für Thread-sichere UI Display Updates.*

- `update_status_display(state)` → `None`  *Aktualisiert Status-Anzeige.*
- `update_signal_display(signal)` → `None`  *Aktualisiert Signal-Anzeige.*
- `update_position_display(position)` → `None`  *Aktualisiert Position-Anzeige.*
- `update_stats_display(stats)` → `None`  *Aktualisiert Statistik-Anzeige.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bot_tab_logs_mixin.py`

### `BotTabLogsMixin(object)`
*Logging and journal methods*

- `set_history_manager(manager)` → `None`  *Setzt den History Manager und verbindet ihn mit dem Adapter.*
- *...16 private methods*

## `src/ui/widgets/bitunix_trading/bot_tab_main.py`

### `BotTab(QWidget)`
*Bot Trading Tab - Main Orchestrator.*

- `set_history_manager(manager)` → `None`  *Setzt den History Manager und verbindet ihn mit dem Adapter.*
- `set_chart_data(data, symbol, timeframe)` → `None`  *Übergibt Chart-Daten an den Bot Engine.*
- `clear_chart_data()` → `None`  *Löscht Chart-Daten im Engine (z.B. bei Symbol-Wechsel).*
- `on_tick_price_updated(price)` → `None`  *Empfängt Live-Tick-Preise vom Chart-Streaming.*
- `update_engine_configs()` → `None`  *Aktualisiert die Konfiguration aller laufenden Engines (delegate to control).*
- `cleanup()` → `None`  *Cleanup bei Widget-Zerstörung (App schließt).*
- *...9 private methods*
- `__init__(paper_adapter, history_manager, parent)`  *Args:*

## `src/ui/widgets/bitunix_trading/bot_tab_modules/bot_tab_settings.py`

### `BotSettingsDialog(QDialog)`
*Tab-basierter Dialog für Bot-Einstellungen.*

- `get_config()` → `BotConfig`  *Gibt die aktualisierten Einstellungen zurück.*
- *...4 private methods*
- `__init__(config, parent)`

## `src/ui/widgets/bitunix_trading/bot_tab_monitoring_mixin.py`

### `BotTabMonitoringMixin(object)`
*Position monitoring and display methods*

- `update_engine_configs()` → `None`  *Aktualisiert die Konfiguration aller laufenden Engines.*
- `set_chart_data(data, symbol, timeframe)` → `None`  *Übergibt Chart-Daten an den Bot Engine.*
- `clear_chart_data()` → `None`  *Löscht Chart-Daten im Engine (z.B. bei Symbol-Wechsel).*
- `on_tick_price_updated(price)` → `None`  *Empfängt Live-Tick-Preise vom Chart-Streaming.*
- `cleanup()` → `None`  *Cleanup bei Widget-Zerstörung (App schließt).*
- *...25 private methods*

## `src/ui/widgets/bitunix_trading/bot_tab_ui.py`

### `BotTabUI(object)`
*UI Manager for Bot Trading Tab.*

- `setup_ui()` → `None`  *Creates the complete UI layout.*
- `create_header_section()` → `QWidget`  *Creates header with status and buttons.*
- `create_signal_section()` → `QGroupBox`  *Creates signal display section.*
- `create_position_section()` → `QGroupBox`  *Creates position display section.*
- `create_stats_section()` → `QGroupBox`  *Creates statistics display.*
- `create_log_section()` → `QGroupBox`  *Creates log viewer.*
- *...1 private methods*
- `__init__(parent)`  *Initialize UI manager.*

## `src/ui/widgets/bitunix_trading/bot_tab_ui_mixin.py`

### `BotTabUIMixin(object)`
*UI creation methods for BotTab*

- *...9 private methods*

## `src/ui/widgets/bitunix_trading_api_widget.py`

### `BitunixTradingAPIWidget(BitunixAPIWidgetUI, BitunixAPIWidgetEvents, BitunixAPIWidgetLogic, QGroupBox)`
*Compact trading interface for Bitunix API.*

- `__init__(parent)`  *Initialize the Bitunix Trading API Widget.*
- `__repr__()` → `str`  *String representation for debugging.*

## `src/ui/widgets/bitunix_trading_api_widget_backup.py`

### `BitunixTradingAPIWidget(QGroupBox)`
*Compact trading interface for Bitunix API.*

- `set_adapter(adapter)`  *Set trading adapter.*
- `set_symbol(symbol)`  *Set trading symbol.*
- `set_price(price)`  *Update current price.*
- *...31 private methods*
- `__init__(parent)`

## `src/ui/widgets/bitunix_tradingview_chart.py`

### `BitunixTradingViewChart(ChartAIMarkingsMixin, ChartMarkingMixin, LevelZonesMixin, EntryAnalyzerMixin, BotOverlayMixin, ToolbarMixin, IndicatorMixin, BitunixStreamingMixin, DataLoadingMixin, ChartStateMixin, EmbeddedTradingViewChartUIMixin, EmbeddedTradingViewChartMarkingMixin, EmbeddedTradingViewChartJSMixin, EmbeddedTradingViewChartViewMixin, EmbeddedTradingViewChartLoadingMixin, EmbeddedTradingViewChartEventsMixin, QWidget)`
*Bitunix-only TradingView Lightweight Charts widget.*

- *...6 private methods*
- `__init__(history_manager)`  *Initialize Bitunix chart widget.*
- `__del__()`  *Cleanup event bus connections.*

## `src/ui/widgets/candlestick_item.py`

### `CandlestickItem(pg.GraphicsObject)`
*Custom GraphicsObject for drawing candlestick charts.*

- `set_data(data)`  *Set candlestick data.*
- `set_colors(up_color, down_color, wick_color)`  *Set custom colors for candlesticks.*
- `generatePicture()`  *Generate the candlestick picture.*
- `paint(p)`  *Paint the candlestick chart.*
- `boundingRect()`  *Return the bounding rectangle of the candlestick data.*
- `clear()`  *Clear all candlestick data.*
- `get_data_count()` → `int`  *Get the number of candlesticks.*
- `is_empty()` → `bool`  *Check if the candlestick item has no data.*
- *...1 private methods*
- `__init__()`  *Initialize candlestick item.*

### Module Functions
- `create_candlestick_item()` → `CandlestickItem`  *Create a new CandlestickItem instance.*

## `src/ui/widgets/cel_ai_assistant_panel.py`

### `_CelAIWorker(QThread)`
*Background worker for AI calls.*

- `run()` → `None`
- `__init__(mode, helper)`

### `CelAIAssistantPanel(QWidget)`
*Dockable AI assistant for CEL workflows.*

- `set_workflow(workflow_type)` → `None`
- `set_pattern_context(pattern_name, description)` → `None`
- `set_explain_code(code)` → `None`
- *...11 private methods*
- `__init__(parent)`

## `src/ui/widgets/cel_ai_helper.py`

### `CelAIHelper(object)`
*AI-Helper für CEL Code-Generierung.*

- `get_current_provider_config()` → `Dict[str, Any]`  *Hole aktuelle Provider-Konfiguration.*
- async `generate_cel_code(workflow_type, pattern_name, strategy_description, context)` → `Optional[str]`  *Generiere CEL Code mit AI.*
- async `explain_cel_code(cel_code, context)` → `Optional[str]`  *Explain a CEL expression with AI.*
- *...8 private methods*
- `__init__()`  *Initialisiere AI-Helper mit aktuellen Settings.*

## `src/ui/widgets/cel_editor_variables_autocomplete.py`

### `CelEditorVariablesAutocomplete(object)`
*Variables Autocomplete extension for CEL Editor.*

- `load_all_variables(chart_window, bot_config, project_vars_path, indicators, regime)` → `Dict[str, Dict[str, Any]]`  *Load all available variables from all sources.*
- `add_to_autocomplete(variables)` → `int`  *Add variables to QScintilla autocomplete.*
- `refresh_autocomplete(chart_window, bot_config, project_vars_path, indicators, regime)` → `int`  *Refresh autocomplete with updated variables.*
- `get_variable_tooltip(var_name)` → `Optional[str]`  *Get tooltip text for a variable.*
- `get_variables_by_prefix(prefix)` → `List[str]`  *Get variable names matching a prefix.*
- `get_variable_categories()` → `List[str]`  *Get list of all variable categories.*
- `__init__(api)`  *Initialize Variables Autocomplete.*

## `src/ui/widgets/cel_editor_widget.py`

### `CelEditorWidget(QWidget)`
*CEL Script Editor with syntax highlighting and autocomplete.*

- `refresh_variables_autocomplete(chart_window, bot_config, project_vars_path, indicators, regime)`  *Refresh variables autocomplete with updated data (Phase 3.3).*
- `set_code(code)`  *Set code in editor.*
- `get_code()` → `str`  *Get code from editor.*
- `clear_error_markers()`  *Clear all error markers.*
- `add_error_marker(line)`  *Add error marker at line.*
- `set_readonly(readonly)`  *Set editor readonly status.*
- `insert_text(text)`  *Insert text at current cursor position.*
- *...17 private methods*
- `__init__(parent, workflow_type)`

## `src/ui/widgets/cel_function_palette.py`

### `CelFunctionPalette(QWidget)`
*Draggable palette of CEL functions and indicators.*

- *...6 private methods*
- `__init__(parent)`

## `src/ui/widgets/cel_lexer.py`

### `CelLexer(QsciLexerCustom)`
*Custom lexer for CEL expression language.*

- `description(style)` → `str`  *Return description for each style.*
- `defaultColor(style)` → `QColor`  *Return default color for each style.*
- `defaultFont(style)` → `QFont`  *Return default font for each style.*
- `styleText(start, end)`  *Perform syntax highlighting using Token Handler Pattern.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/widgets/cel_rulepack_panel.py`

### `CelRulePackPanel(QWidget)`
*UI panel for editing RulePack rules and metadata.*

- `load_rulepack(rulepack)` → `None`  *Load rulepack into UI.*
- `select_first_rule()` → `None`  *Select first available rule and emit selection signal.*
- `add_rule(pack_type)` → `None`
- `remove_selected_rule(pack_type)` → `None`
- `move_rule(pack_type, direction)` → `None`
- `set_rule_expression(pack_type, rule_id, expression)` → `None`  *Update rule expression from editor.*
- *...10 private methods*
- `__init__(parent)`

## `src/ui/widgets/cel_strategy_editor_widget.py`

### `CelCommandReference(QWidget)`
*CEL Command Reference Browser - displays commands from CEL_Befehle_Liste_v2.md.*

- *...6 private methods*
- `__init__(parent)`

### `CelStrategyEditorWidget(QWidget)`
*Main CEL Strategy Editor Widget - separate tab for CEL development.*

- *...15 private methods*
- `__init__(parent)`

## `src/ui/widgets/cel_validator.py`

### `ValidationError(object)`
*CEL validation error.*

- `__str__()` → `str`

### `CelValidator(object)`
*Validator for CEL expressions with trading-specific knowledge.*

- `validate(code)` → `List[ValidationError]`  *Validate CEL code and return list of errors.*
- `validate_and_format_errors(code)` → `str`  *Validate code and return formatted error message.*
- *...5 private methods*
- `__init__()`  *Initialize validator.*

## `src/ui/widgets/chart_ai_markings_mixin.py`

### `ChartAIMarkingsMixin(object)`
*Mixin for AI-driven chart markings via ChartMarkingMixin.*

- `add_horizontal_line(price, label, color)` → `str`  *Add a horizontal line at specified price.*
- `add_zone(start_time, end_time, top_price, bottom_price, fill_color, border_color, label)` → `str`  *Add a price zone (rectangle) to the chart.*
- `add_support_zone(start_time, end_time, top_price, bottom_price, label)` → `str`  *Add a support zone (green).*
- `add_resistance_zone(start_time, end_time, top_price, bottom_price, label)` → `str`  *Add a resistance zone (red).*
- `add_demand_zone(start_time, end_time, top_price, bottom_price, label)` → `str`  *Add a demand zone (blue).*
- `add_supply_zone(start_time, end_time, top_price, bottom_price, label)` → `str`  *Add a supply zone (orange).*
- `add_long_entry(timestamp, price, label)` → `str`  *Add a long entry marker (green arrow up).*
- `add_short_entry(timestamp, price, label)` → `str`  *Add a short entry marker (red arrow down).*

## `src/ui/widgets/chart_factory.py`

### `ChartType(Enum)`
*Available chart types.*


### `ChartFactory(object)`
*Factory for creating chart widgets.*

- @staticmethod `create_chart(chart_type, symbol, history_manager)` → `QWidget`  *Create a chart widget.*
- @staticmethod `get_available_chart_types()` → `Dict[ChartType, bool]`  *Get information about available chart types.*
- @staticmethod `get_chart_features(chart_type)` → `Dict[str, Any]`  *Get features supported by chart implementation.*
- *...2 private methods*

### Module Functions
- `create_chart(symbol, chart_type, history_manager)` → `QWidget`  *Create a chart widget with simplified interface.*
- `get_recommended_chart_type()` → `ChartType`  *Get the recommended chart type.*

## `src/ui/widgets/chart_interface.py`

### `IChartWidget(ABC)`
*Interface that all chart widgets should implement.*

- `set_symbol(symbol)` → `None`  *Set the trading symbol for the chart.*
- `set_timeframe(timeframe)` → `None`  *Set the chart timeframe.*
- `update_data(bars_data, append)` → `None`  *Update chart with new bar data.*
- `add_indicator(indicator_type)` → `None`  *Add a technical indicator to the chart.*
- `remove_indicator(indicator_id)` → `None`  *Remove a technical indicator from the chart.*
- `clear_data()` → `None`  *Clear all chart data.*
- `set_theme(theme)` → `None`  *Set the chart theme.*
- `zoom_to_fit()` → `None`  *Zoom chart to fit all data (optional implementation).*
- `get_visible_range()` → `Optional[Tuple[int, int]]`  *Get the currently visible data range (optional implementation).*

### `ChartSignals(QObject)`
*Common signals that chart widgets can emit.*


### `BaseChartWidget(IChartWidget)`
*Base implementation of chart widget interface.*

- @property `symbol()` → `str`  *Get current symbol.*
- @property `timeframe()` → `str`  *Get current timeframe.*
- @property `theme()` → `str`  *Get current theme.*
- `set_symbol(symbol)` → `None`  *Set trading symbol.*
- `set_timeframe(timeframe)` → `None`  *Set timeframe.*
- `set_theme(theme)` → `None`  *Set theme.*
- `clear_data()` → `None`  *Clear chart data.*
- `get_data_count()` → `int`  *Get number of data points.*
- `is_empty()` → `bool`  *Check if chart has no data.*
- *...6 private methods*
- `__init__()`  *Initialize base chart widget.*

### `ChartCapabilities(object)`
*Describes capabilities of a chart implementation.*

- `to_dict()` → `Dict[str, Any]`  *Convert capabilities to dictionary.*
- `__init__(supports_real_time, supports_indicators, supports_drawing_tools, supports_themes, supports_zoom, max_data_points, performance_rating)`  *Initialize chart capabilities.*

### Module Functions
- `register_chart_adapter(widget_class, capabilities)` → `None`  *Register a chart widget with its capabilities.*
- `get_chart_capabilities(widget_class)` → `Optional[ChartCapabilities]`  *Get capabilities of a chart widget class.*

## `src/ui/widgets/chart_js_template.py`

### Module Functions
- `_load_chart_template()` → `str`  *Load the HTML/JS template from disk.*
- `get_background_image_style()` → `str`  *Get background image CSS style from QSettings (Issue #35).*
- `get_chart_colors_config()` → `dict`  *Get chart colors from QSettings for JavaScript injection (Issues #34, #37).*
- `get_chart_html_template()` → `str`  *Get the complete chart HTML template with zone primitives injected.*

## `src/ui/widgets/chart_mixins/alpaca_streaming_mixin.py`

### `AlpacaStreamingMixin(object)`
*Mixin providing Alpaca-ONLY streaming functionality.*

- *...23 private methods*

## `src/ui/widgets/chart_mixins/bitunix_streaming_mixin.py`

### `BitunixStreamingMixin(object)`
*Mixin providing Bitunix-ONLY streaming functionality.*

- *...22 private methods*

## `src/ui/widgets/chart_mixins/bot_overlay_mixin.py`

### `BotOverlayMixin(object)`
*Mixin providing bot overlay functionality for chart widgets.*

- `add_bot_marker(timestamp, price, marker_type, side, text, score)` → `None`  *Add a bot marker to the chart.*
- `add_entry_candidate(timestamp, price, side, score)` → `None`  *Add entry candidate marker.*
- `add_entry_confirmed(timestamp, price, side, score)` → `None`  *Add confirmed entry marker.*
- `add_exit_marker(timestamp, price, side, reason)` → `None`  *Add exit signal marker.*
- `add_stop_triggered_marker(timestamp, price, side)` → `None`  *Add stop-triggered marker.*
- `add_macd_marker(timestamp, price, is_bearish)` → `None`  *Add MACD cross marker (info only, no exit triggered).*
- `clear_bot_markers()` → `None`  *Clear all bot markers from chart.*
- `add_stop_line(line_id, price, line_type, color, label)` → `None`  *Add or update a stop-loss line on the chart.*
- `update_stop_line(line_id, new_price, label)` → `bool`  *Update an existing stop line.*
- `remove_stop_line(line_id)` → `bool`  *Remove a stop line from the chart.*
- `clear_stop_lines()` → `None`  *Clear all stop lines from chart.*
- `add_regime_line(line_id, timestamp, regime_name, color, label)` → `None`  *Add a vertical regime boundary line on the chart.*
- `clear_regime_lines()` → `None`  *Clear all regime lines from chart.*
- `set_debug_hud_visible(visible)` → `None`  *Set debug HUD visibility.*
- `update_debug_info(regime, strategy, ki_mode, trailing_mode, confidence, state, extra)` → `None`  *Update debug HUD information.*
- `display_position(position)` → `None`  *Display position information on chart.*
- `clear_position_display()` → `None`  *Clear position display elements.*
- `display_signal(signal)` → `None`  *Display a signal on the chart.*
- `clear_signal_display(signal_id)` → `None`  *Clear signal display.*
- `clear_bot_overlay()` → `None`  *Clear all bot overlay elements.*
- `restore_state_from_dict(state_dict)` → `None`  *Restore bot overlay state from chart state dictionary.*
- *...5 private methods*

## `src/ui/widgets/chart_mixins/bot_overlay_types.py`

### `MarkerType(str, Enum)`
*Marker types for chart display.*


### `BotMarker(object)`
*Marker data for chart display.*

- `to_chart_marker()` → `dict[str, Any]`  *Convert to Lightweight Charts marker format.*

### `StopLine(object)`
*Stop-loss line data.*


### `RegimeLine(object)`
*Regime boundary line data.*


### `BotOverlayState(object)`
*State tracking for bot overlay elements.*


### Module Functions
- `build_hud_content(state, regime, strategy, trailing_mode, ki_mode, confidence, extra)` → `str`  *Build HTML content for debug HUD.*

## `src/ui/widgets/chart_mixins/chart_calculator_adapter.py`

### `ChartCalculatorAdapter(object)`
*Adapter for using IndicatorCalculatorFactory in chart display mixins.*

- `compute_indicator_series(df, indicators_def)` → `dict[str, dict[str, pd.Series]]`  *Compute indicator series for chart display from JSON optimizer format.*
- *...3 private methods*
- `__init__()`  *Initialize adapter with registered calculators.*

## `src/ui/widgets/chart_mixins/chart_stats_labels_mixin.py`

### `ChartStatsLabelsMixin(object)`
*Mixin for updating chart statistics labels (OHLC, DB status, Price).*

- `update_ohlc_label(data)` → `None`  *Update OHLC info label with latest candle data.*
- `update_db_status_label()` → `None`  *Update DB status label with record count and symbol/interval.*
- `update_last_price_label(price)` → `None`  *Update 'Last Price:' label with current price only.*
- `update_price_label(price, reference_price)` → `None`  *Update price info label with current price and daily change since 0 Uhr.*
- `update_all_stats_labels(data, price)` → `None`  *Update all statistics labels (convenience method).*
- *...1 private methods*

## `src/ui/widgets/chart_mixins/data_loading_cleaning.py`

### `DataLoadingCleaning(object)`
*Helper für DataLoadingMixin bad tick cleaning.*

- `clean_bad_ticks(data)` → `'pd.DataFrame'`  *Bereinige Bad Ticks in historischen OHLCV-Daten.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/data_loading_mixin.py`

### `DataLoadingMixin(object)`
*Mixin providing data loading functionality for EmbeddedTradingViewChart.*

- `load_data(data)`  *Load market data into chart.*
- async `load_symbol(symbol, data_provider)`  *Delegate to symbol loader helper.*
- async `refresh_data()`  *Public method to refresh chart data (called by main app).*
- *...7 private methods*

## `src/ui/widgets/chart_mixins/data_loading_resolution.py`

### `DataLoadingResolution(object)`
*Helper für DataLoadingMixin resolution methods.*

- `resolve_asset_class(symbol)` → `AssetClass`  *Determine asset class from symbol format.*
- `resolve_timeframe()` → `Timeframe`  *Map timeframe string to Timeframe enum.*
- `resolve_provider_source(data_provider, asset_class)` → `Optional[DataSource]`  *Map provider string to DataSource enum.*
- `resolve_lookback_days()` → `int`  *Map period string to days.*
- `calculate_date_range(asset_class, lookback_days)` → `tuple[datetime, datetime]`  *Calculate start/end dates with market hours logic.*
- @staticmethod `bars_to_dataframe(bars)` → `pd.DataFrame`  *Convert bars to DataFrame.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/data_loading_series.py`

### `DataLoadingSeries(object)`
*Helper für DataLoadingMixin chart series building.*

- `prepare_chart_data(data)` → `'pd.DataFrame'`  *Prepare and store data for chart display.*
- `build_chart_series(data)` → `tuple[list[dict], list[dict]]`  *Convert DataFrame to candle + volume series.*
- `update_chart_series(candle_data, volume_data)` → `None`  *Send candle and volume data to JavaScript chart.*
- `finalize_chart_load(data, candle_data)` → `None`  *Update UI and emit signals after chart load.*
- *...2 private methods*
- `__init__(parent)`  *Args:*

### Module Functions
- `_get_volume_colors()` → `dict[str, str]`  *Get volume colors from QSettings (Issue #40).*

## `src/ui/widgets/chart_mixins/data_loading_symbol.py`

### `DataLoadingSymbol(object)`
*Helper für DataLoadingMixin load_symbol orchestration.*

- async `load_symbol(symbol, data_provider)`  *Load symbol data and display chart.*
- `log_request_details(symbol, start_date, end_date, asset_class, provider_source)` → `None`  *Log data request details.*
- `set_loaded_status(source_used)` → `None`  *Update status label after successful load.*
- async `restart_live_stream(symbol)` → `None`  *Restart live stream after symbol change.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/data_loading_utils.py`

### Module Functions
- `get_local_timezone_offset_seconds()` → `int`  *Get local timezone offset in seconds (positive for east of UTC).*

## `src/ui/widgets/chart_mixins/entry_analyzer/__init__.py`

### `EntryAnalyzerMixin(EntryAnalyzerLogicMixin, EntryAnalyzerEventsMixin, EntryAnalyzerUIMixin)`
*Combined mixin for Entry Analyzer functionality in Chart Widget.*


## `src/ui/widgets/chart_mixins/entry_analyzer/entry_analyzer_events_mixin.py`

### `AnalysisWorker(QThread)`
*Background worker for running analysis without blocking UI.*

- `run()` → `None`  *Execute the analysis in background thread.*
- `__init__(visible_range, symbol, timeframe, candles, use_optimizer, json_config_path, parent)` → `None`  *Initialize the analysis worker.*

### `EntryAnalyzerEventsMixin(object)`
*Mixin for Entry Analyzer event handling.*

- `start_live_entry_analysis(reanalyze_interval_sec, use_optimizer, auto_draw)` → `None`  *Start continuous live entry analysis.*
- `stop_live_entry_analysis()` → `None`  *Stop continuous live entry analysis.*
- `is_live_analysis_running()` → `bool`  *Check if live analysis is running.*
- `on_new_candle_received(candle)` → `None`  *Handle new candle data for incremental update.*
- `get_live_metrics()` → `dict`  *Get live analysis performance metrics.*
- `get_selected_items()` → `list[str]`  *Get selected items (implemented in UI mixin).*
- *...16 private methods*

## `src/ui/widgets/chart_mixins/entry_analyzer/entry_analyzer_logic_mixin.py`

### `EntryAnalyzerLogicMixin(object)`
*Mixin for Entry Analyzer business logic and drawing.*

- `get_selected_items()` → `list[str]`  *Get selected items (implemented in UI mixin).*
- *...10 private methods*

## `src/ui/widgets/chart_mixins/entry_analyzer/entry_analyzer_ui_mixin.py`

### `EntryAnalyzerUIMixin(object)`
*Mixin for Entry Analyzer UI components.*

- `create_regime_filter_widget()` → `QWidget`  *Create the regime filter widget for toolbar integration.*
- `get_selected_items()` → `list[str]`  *Get list of selected regime IDs.*
- `select_all_regimes()` → `None`  *Select all regimes in the filter.*
- `deselect_all_regimes()` → `None`  *Deselect all regimes in the filter.*
- `set_regime_filter_visible(regime_ids)` → `None`  *Set which regimes are visible via the filter.*
- `show_entry_analyzer()` → `None`  *Show the Entry Analyzer popup dialog.*
- `hide_entry_analyzer()` → `None`  *Hide the Entry Analyzer popup dialog if it exists.*
- *...16 private methods*

## `src/ui/widgets/chart_mixins/entry_analyzer/live_analysis_bridge.py`

### `LiveAnalysisBridge(QObject)`
*Bridge between BackgroundRunner (threading) and Qt signals.*

- `start_live_analysis(reanalyze_interval_sec, use_optimizer, json_config_path)` → `None`  *Start the background runner for live analysis.*
- `stop_live_analysis()` → `None`  *Stop the background runner.*
- `request_analysis(visible_range_dict, symbol, timeframe)` → `bool`  *Request analysis of visible range.*
- `push_new_candle(candle, visible_range_dict, symbol, timeframe)` → `bool`  *Push a new candle for incremental update.*
- `is_running()` → `bool`  *Check if live analysis is running.*
- `get_metrics()` → `dict`  *Get performance metrics.*
- *...4 private methods*
- `__init__(parent)` → `None`  *Initialize the bridge.*

## `src/ui/widgets/chart_mixins/indicator_chart_ops.py`

### `IndicatorChartOps(object)`
*Helper für IndicatorMixin chart operations.*

- `create_overlay_indicator(display_name, color)`  *Create overlay indicator on price chart.*
- `create_oscillator_panel(panel_id, display_name, color, min_val, max_val)`  *Create oscillator panel with indicator-specific reference lines.*
- `add_oscillator_reference_lines(ind_display_name, panel_id)`  *Add indicator-specific reference lines to oscillator panel.*
- `update_overlay_data(display_name, ind_data)`  *Update overlay indicator data on price chart.*
- `update_oscillator_data(panel_id, ind_data)`  *Update oscillator panel data.*
- `remove_indicator_from_chart(panel_or_id, display_name, is_overlay)`  *Remove indicator from chart.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/indicator_conversion.py`

### `IndicatorConversion(object)`
*Helper für IndicatorMixin data conversion.*

- `convert_indicator_result(ind_id, result)`  *Dispatch to appropriate conversion method based on result type.*
- `convert_macd_data_to_chart_format(result)`  *Convert MACD indicator result to chart format.*
- `convert_multi_series_data_to_chart_format(result, ind_id)`  *Convert multi-series indicator result to chart format.*
- `convert_single_series_data_to_chart_format(result)`  *Convert single-series indicator result to chart format.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/indicator_instance.py`

### `IndicatorInstanceManager(object)`
*Helper für IndicatorMixin instance management.*

- `add_indicator_instance(ind_id, params, color)` → `None`  *Create a new indicator instance (may be multiple per type).*
- `remove_indicator_instance(instance_id)` → `None`  *Remove indicator instance from chart and active dict.*
- `add_indicator_instance_to_chart(inst)` → `None`  *Calculate + render a specific instance.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/indicator_mixin.py`

### `IndicatorMixin(object)`
*Mixin providing indicator functionality for EmbeddedTradingViewChart.*

- *...10 private methods*

## `src/ui/widgets/chart_mixins/indicator_realtime.py`

### `IndicatorRealtime(object)`
*Helper für IndicatorMixin real-time updates.*

- `update_indicators_realtime(candle)`  *Update indicators in real-time with new candle data.*
- `should_skip_realtime_update()` → `bool`  *Check if realtime update should be skipped.*
- `build_realtime_row(candle)` → `pd.DataFrame`  *Build new DataFrame row from candle data.*
- `update_realtime_row(new_row)` → `None`  *Update data with new row (update or append).*
- `update_indicator_realtime(inst)` → `None`  *Update single indicator in realtime.*
- `update_macd_realtime(instance_id, result)` → `None`  *Update MACD indicator in realtime (all 3 series).*
- `update_multi_series_realtime(instance_id, is_overlay, display_name, result)` → `None`  *Update multi-series indicator in realtime.*
- `update_single_series_realtime(instance_id, is_overlay, display_name, result)` → `None`  *Update single-series indicator in realtime.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/indicator_update.py`

### `IndicatorUpdate(object)`
*Helper für IndicatorMixin update orchestration.*

- `update_indicators()`  *Update technical indicators on chart.*
- `should_skip_full_update()` → `bool`  *Check if indicator update should be skipped.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/indicator_utils.py`

### `IndicatorInstance(object)`
*Instance of an indicator (multi-add support).*


### Module Functions
- `_ts_to_local_unix(ts)` → `int`  *Convert timestamp to Unix seconds (UTC).*
- `get_indicator_configs()`  *Get indicator configuration dictionaries.*

## `src/ui/widgets/chart_mixins/level_zones_interactions.py`

### `LevelZonesInteractions(object)`
*Helper für Level Zones Interactions (Click Detection, Context Menu).*

- `register_zone_for_click(zone_id, top, bottom, label)` → `None`  *Register a zone for click detection in JavaScript.*
- `unregister_zone_from_click(zone_id)` → `None`  *Unregister a zone from click detection.*
- `setup_zone_click_handler()` → `None`  *Setup zone click handler by connecting to bridge signal.*
- `on_zone_clicked(zone_id, price, top, bottom, label)` → `None`  *Handle zone click event - show context menu.*
- `get_level_by_zone_id(zone_id)` → `Optional['Level']`  *Get Level object by zone ID.*
- `copy_level_price(price)` → `None`  *Copy level price to clipboard.*
- `copy_level_range(bottom, top)` → `None`  *Copy level range to clipboard.*
- `suggest_set_level_as(target_type, price)` → `None`  *Suggest setting level as TP/SL/Entry.*
- `remove_single_level_zone(zone_id)` → `None`  *Remove a single level zone.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/level_zones_mixin.py`

### `LevelZonesMixin(object)`
*Mixin für Level-Zonen-Rendering in Chart-Widgets.*

- `detect_and_render_levels(df, symbol, timeframe, current_price)` → `None`  *Detect levels from DataFrame and render as zones.*
- `set_levels_result(result)` → `None`  *Set levels result directly.*
- `get_levels_for_chatbot()` → `str`  *Get levels in tag format for chatbot.*
- `get_nearest_support(price)` → `Optional['Level']`  *Get nearest support level.*
- `get_nearest_resistance(price)` → `Optional['Level']`  *Get nearest resistance level.*
- *...3 private methods*

## `src/ui/widgets/chart_mixins/level_zones_rendering.py`

### `LevelZonesRendering(object)`
*Helper für Level Zones Rendering (Detection, Conversion, Rendering).*

- `detect_and_render_levels(df, symbol, timeframe, current_price)` → `None`  *Detect levels from DataFrame and render as zones.*
- `set_levels_result(result)` → `None`  *Set levels result directly.*
- `render_level_zones()` → `None`  *Render level zones in the chart.*
- `level_to_zone(level, start_time, end_time)` → `Optional[str]`  *Convert a Level to a chart Zone and render it.*
- `render_zone_on_chart(zone)` → `None`  *Render zone on JavaScript chart.*
- `get_chart_time_range()` → `tuple[int, int]`  *Get current chart time range.*
- `show_level_zones()` → `None`  *Show all level zones.*
- `hide_level_zones()` → `None`  *Hide all level zones (without removing).*
- `clear_level_zones()` → `None`  *Remove all level zones from chart.*
- `refresh_level_zones()` → `None`  *Refresh level zones (re-detect and render).*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/level_zones_toolbar.py`

### `LevelZonesToolbar(object)`
*Helper für Level Zones Toolbar und Menu.*

- `add_levels_toggle_to_toolbar(toolbar)` → `None`  *Add levels toggle button to toolbar.*
- `build_levels_menu(menu)` → `None`  *Build the levels dropdown menu.*
- `on_levels_toggle(checked)` → `None`  *Handle levels toggle button click.*
- `on_level_type_toggle(level_type, checked)` → `None`  *Handle level type toggle.*
- `on_key_levels_only(checked)` → `None`  *Handle key levels only toggle.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_mixins/live_analysis_bridge.py`

### `LiveAnalysisBridge(QObject)`
*Bridge between BackgroundRunner (threading) and Qt signals.*

- `start_live_analysis(reanalyze_interval_sec, use_optimizer, json_config_path)` → `None`  *Start the background runner for live analysis.*
- `stop_live_analysis()` → `None`  *Stop the background runner.*
- `request_analysis(visible_range_dict, symbol, timeframe)` → `bool`  *Request analysis of visible range.*
- `push_new_candle(candle, visible_range_dict, symbol, timeframe)` → `bool`  *Push a new candle for incremental update.*
- `is_running()` → `bool`  *Check if live analysis is running.*
- `get_metrics()` → `dict`  *Get performance metrics.*
- *...4 private methods*
- `__init__(parent)` → `None`  *Initialize the bridge.*

## `src/ui/widgets/chart_mixins/regime_display_mixin.py`

### `RegimeDisplayMixin(object)`
*Mixin für Regime-Anzeige in Chart-Widgets.*

- `trigger_regime_update(debounce_ms, force)` → `None`  *Trigger regime update with debounce.*
- `set_regime_manually(regime, adx, gate_reason, allows_entry)` → `None`  *Set regime manually (e.g., from MarketContext).*
- `set_regime_from_context(context)` → `None`  *Set regime from MarketContext.*
- `get_current_regime()` → `str | None`  *Get current regime type.*
- `get_regime_badge_widget()`  *Get the regime badge widget for external use.*
- *...14 private methods*

## `src/ui/widgets/chart_mixins/state_mixin.py`

### `ChartStateMixin(object)`
*Mixin providing state management for EmbeddedTradingViewChart.*

- `get_visible_range(callback)`  *Asynchronously get the current visible logical range.*
- `set_visible_range(range_data)`  *Restore visible logical range.*
- `get_pane_layout(callback)`  *Asynchronously get the current pane layout (stretch factors).*
- `set_pane_layout(layout)`  *Restore pane layout (stretch factors).*
- `get_chart_state(callback)`  *Get comprehensive chart state including panes, zoom, and indicators.*
- `set_chart_state(state)`  *Restore comprehensive chart state.*

## `src/ui/widgets/chart_mixins/strategy_concept_mixin.py`

### `StrategyConceptMixin(object)`
*Mixin for Strategy Concept window management.*

- `show_strategy_concept()` → `None`  *Show the Strategy Concept window.*
- `close_strategy_concept()` → `None`  *Close Strategy Concept window.*
- `apply_strategy_to_bot(pattern_type, strategy_data, bot_controller)` → `bool`  *Apply pattern strategy to BotController for automated trading.*
- `show_bot_integration_dialog()` → `None`  *Show dialog to apply current strategy to bot.*
- *...16 private methods*

## `src/ui/widgets/chart_mixins/streaming_mixin.py`

### `StreamingMixin(object)`
*Mixin providing streaming functionality for EmbeddedTradingViewChart.*

- *...23 private methods*

## `src/ui/widgets/chart_mixins/toolbar_mixin.py`

### `ToolbarMixin(object)`
*Mixin providing toolbar functionality for EmbeddedTradingViewChart.*

- `update_regime_badge(regime, adx, gate_reason, allows_entry)` → `None`  *Update regime badge (delegated to row2 helper).*
- `update_regime_from_result(result)` → `None`  *Update regime from result (delegated to row2 helper).*
- *...13 private methods*
- `__init__()`  *Initialize mixin (called by parent class).*

## `src/ui/widgets/chart_mixins/toolbar_mixin_features.py`

### `ToolbarMixinFeatures(object)`
*Phase 5.5 feature buttons (Levels + Export Context).*

- `add_levels_button(toolbar)` → `None`  *Add levels toggle button to toolbar (Phase 5.5).*
- `on_detect_levels()` → `None`  *Trigger level detection.*
- `on_level_type_toggle(level_type, checked)` → `None`  *Handle level type toggle.*
- `on_clear_levels()` → `None`  *Clear all level zones from chart.*
- `add_export_context_button(toolbar)` → `None`  *Add export context button to toolbar (Phase 5.5).*
- `on_open_context_inspector()` → `None`  *Open the MarketContext Inspector dialog.*
- `on_copy_context_json()` → `None`  *Copy MarketContext as JSON to clipboard.*
- `on_copy_context_prompt()` → `None`  *Copy MarketContext as AI prompt to clipboard.*
- `on_export_context_file()` → `None`  *Export MarketContext to JSON file.*
- `on_refresh_context()` → `None`  *Refresh MarketContext.*
- *...2 private methods*
- `__init__(parent)`

## `src/ui/widgets/chart_mixins/toolbar_mixin_row1.py`

### `ToolbarMixinRow1(ToolbarRow1ActionsMixin, ToolbarRow1EventsMixin, ToolbarRow1SetupMixin)`
*Row 1 toolbar composite mixin (timeframe, period, indicators, primary actions).*

- `__init__(parent)`  *Initialize toolbar row 1 mixin.*

## `src/ui/widgets/chart_mixins/toolbar_mixin_row2.py`

### `ToolbarMixinRow2(object)`
*Row 2 toolbar builders (live stream, regime, chart marking, AI, bot, market status).*

- `build_toolbar_row2(toolbar)` → `None`  *Build toolbar row 2.*
- `add_regime_badge_to_toolbar(toolbar)` → `None`  *Add regime button to toolbar (Issue #18 - als Button implementiert).*
- `add_regime_filter_to_toolbar(toolbar)` → `None`  *Add regime filter dropdown to toolbar (Phase 4: Regime Filtering).*
- `on_regime_button_clicked()` → `None`  *Handle regime button click - ermittle aktuelles Regime (Issue #18).*
- `update_regime_badge(regime, adx, gate_reason, allows_entry)` → `None`  *Update the regime button display (Issue #18 - angepasst für Button).*
- `update_regime_from_result(result)` → `None`  *Update regime button from RegimeResult (Issue #18 - angepasst für Button).*
- `add_live_stream_toggle(toolbar)` → `None`
- `add_chart_marking_button(toolbar)` → `None`
- `add_entry_analyzer_button(toolbar)` → `None`  *Add Entry Analyzer button to toolbar (Phase 5).*
- `add_strategy_concept_button(toolbar)` → `None`  *Add Strategy Concept button to toolbar (Phase 6).*
- `add_cel_editor_button(toolbar)` → `None`  *Add CEL Editor button to toolbar (Phase 7).*
- `add_ai_chat_button(toolbar)` → `None`
- `add_ai_analysis_button(toolbar)` → `None`
- `add_settings_button(toolbar)` → `None`  *Add settings button (gear icon) to toolbar.*
- `add_bot_toggle_button(toolbar)` → `None`
- `add_market_status(toolbar)` → `None`
- `clear_all_markers()` → `None`  *Clear all entry and structure markers.*
- `clear_zones_with_js()` → `None`  *Clear all zones (Python-managed and JS-side).*
- `clear_lines_with_js()` → `None`  *Clear all lines (Python-managed and JS-side hlines).*
- `clear_all_drawings()` → `None`  *Clear only the JavaScript-side drawings (from drawing tools).*
- `clear_all_markings()` → `None`  *Clear all chart markings (both Python-managed and JS drawings).*
- *...5 private methods*
- `__init__(parent)`

## `src/ui/widgets/chart_mixins/toolbar_row1/toolbar_row1_actions_mixin.py`

### `ToolbarRow1ActionsMixin(object)`
*Row 1 toolbar actions - action methods and toolbar operations.*

- `on_zoom_all()`  *Zoom chart to show all data with sane pane heights.*
- `on_zoom_back()`  *Restore previous view (visible range + pane heights).*
- `on_load_chart()` → `None`  *Handle load chart button - reload current symbol.*
- `on_refresh()` → `None`  *Handle refresh button - same as load chart.*
- `on_indicator_add(ind_id, params, color)` → `None`  *Add indicator instance to chart.*
- `on_indicator_remove(instance_id)` → `None`  *Remove indicator instance from chart.*
- `on_reset_indicators()` → `None`  *Completely clear all indicators from the chart.*
- `refresh_active_indicator_menu()` → `None`  *Show active indicators as remove-actions directly in main menu.*
- `prompt_custom_period(ind_id, color)` → `None`  *Show custom period dialog for indicator.*
- `prompt_generic_params(ind_id, color)` → `None`  *Show generic parameter dialog for indicator.*

## `src/ui/widgets/chart_mixins/toolbar_row1/toolbar_row1_events_mixin.py`

### `ToolbarRow1EventsMixin(object)`
*Row 1 toolbar events - event handlers and UI state updates.*

- *...6 private methods*

## `src/ui/widgets/chart_mixins/toolbar_row1/toolbar_row1_setup_mixin.py`

### `ToolbarRow1SetupMixin(object)`
*Row 1 toolbar setup - widget creation and layout.*

- `build_toolbar_row1(toolbar)` → `None`  *Build toolbar row 1.*
- `add_broker_mirror_controls(toolbar)` → `None`  *Add broker mirror controls (Phase 2: Workspace Manager).*
- `add_watchlist_toggle(toolbar)` → `None`  *Add watchlist toggle button to toolbar.*
- `add_timeframe_selector(toolbar)` → `None`  *Add timeframe selector combo box.*
- `add_period_selector(toolbar)` → `None`  *Add period selector combo box.*
- `add_indicators_menu(toolbar)` → `None`  *Add indicators menu button.*
- `add_primary_actions(toolbar)` → `None`  *Add primary action buttons (Load, Refresh, Zoom, etc.).*
- *...1 private methods*

## `src/ui/widgets/chart_shared/data_conversion.py`

### Module Functions
- `convert_bars_to_dataframe(bars, timestamp_column)` → `pd.DataFrame`  *Convert bar objects to a pandas DataFrame.*
- `convert_dict_bars_to_dataframe(bars, timestamp_key)` → `pd.DataFrame`  *Convert dictionary-format bars to a pandas DataFrame.*
- `validate_ohlcv_data(df)` → `bool`  *Validate that a DataFrame contains valid OHLCV data.*
- `convert_dataframe_to_ohlcv_list(df, use_unix_timestamp)` → `List[Tuple[Union[int, datetime], float, float, float, float, float]]`  *Convert a DataFrame back to a list of OHLCV tuples.*
- `convert_dataframe_to_js_format(df, include_volume)` → `List[dict]`  *Convert DataFrame to JavaScript-compatible format for TradingView charts.*
- `resample_ohlcv(df, target_timeframe)` → `pd.DataFrame`  *Resample OHLCV data to a different timeframe.*

## `src/ui/widgets/chart_shared/theme_utils.py`

### Module Functions
- `load_custom_colors()` → `Dict[str, str]`  *Load custom chart colors from QSettings (Issue #34).*
- `clear_custom_colors_cache()` → `None`  *Clear custom colors cache (Issue #34).*
- `get_theme_colors(theme)` → `Dict[str, str]`  *Get color palette for a specific theme.*
- `get_candle_colors(theme)` → `Dict[str, str]`  *Get candlestick colors for a specific theme.*
- `get_volume_colors(theme)` → `Dict[str, str]`  *Get volume bar colors for a specific theme.*
- `apply_theme_to_chart(chart_options, theme)` → `Dict[str, Any]`  *Apply theme colors to chart options dictionary.*
- `get_pyqtgraph_theme(theme)` → `Dict[str, Any]`  *Get PyQtGraph-specific theme configuration.*
- `get_tradingview_chart_options(theme)` → `Dict[str, Any]`  *Get complete TradingView Lightweight Charts configuration.*
- `get_candlestick_series_options(theme)` → `Dict[str, Any]`  *Get TradingView candlestick series options.*
- `get_volume_series_options(theme)` → `Dict[str, Any]`  *Get TradingView volume series options.*
- `generate_indicator_color(indicator_type, index)` → `str`  *Generate a color for an indicator.*

## `src/ui/widgets/chart_shared/wheel_event_filter.py`

### `WheelEventFilter(QObject)`
*Event filter that blocks wheel events for combo boxes and spinboxes.*

- `eventFilter(obj, event)` → `bool`  *Block wheel events while passing through other events.*

## `src/ui/widgets/chart_state_integration.py`

### `TradingViewChartStateMixin(object)`
*Mixin for TradingView Lightweight Charts state persistence.*

- `save_chart_state_now(include_window_state)`  *Immediately save current chart state.*
- `load_chart_state_now()` → `bool`  *Load saved chart state for current symbol.*
- `enable_auto_save_state(enabled)`  *Enable or disable automatic state saving.*
- `clear_saved_state()`  *Clear saved state for current symbol.*
- *...16 private methods*
- `__init_chart_state__()`  *Initialize chart state management. Call this in your chart's __init__.*

### `PyQtGraphChartStateMixin(object)`
*Mixin for PyQtGraph chart state persistence.*

- `save_chart_state_now()`  *Save current PyQtGraph chart state.*
- `load_chart_state_now()` → `bool`  *Load saved PyQtGraph chart state.*
- `__init_chart_state__()`  *Initialize chart state management for PyQtGraph.*

### Module Functions
- `install_chart_state_persistence(chart_widget, chart_type)`  *Install state persistence on an existing chart widget.*

## `src/ui/widgets/chart_state_manager.py`

### `IndicatorState(object)`
*State of a single indicator.*


### `PaneLayout(object)`
*Layout configuration for chart panes.*


### `ViewRange(object)`
*Visible range of the chart (zoom/pan state).*


### `ChartState(object)`
*Complete chart state configuration.*

- `__post_init__()`

### `ChartStateManager(QObject)`
*Advanced state manager for chart persistence.*

- `save_chart_state(symbol, chart_state, auto_save)`  *Save complete chart state to persistent storage.*
- `load_chart_state(symbol, chart_type)` → `Optional[ChartState]`  *Load chart state from persistent storage.*
- `save_indicator_state(symbol, indicator)`  *Save or update a single indicator state.*
- `save_view_range(symbol, view_range)`  *Save view range (zoom/pan state) for quick updates.*
- `save_pane_layout(symbol, pane_layout)`  *Save pane layout (row heights) for quick updates.*
- `remove_chart_state(symbol)`  *Remove all saved state for a symbol.*
- `list_saved_symbols()` → `List[str]`  *Get list of symbols with saved states.*
- `clear_all_states()`  *Clear all saved chart states.*
- *...4 private methods*
- `__init__(organization, application)`  *Initialize the state manager.*

### `TradingViewChartStateHelper(object)`
*Helper for TradingView Lightweight Charts state persistence.*

- @staticmethod `create_js_set_visible_range(range_dict)` → `str`  *Create JavaScript code to set visible range.*
- @staticmethod `create_js_get_visible_range()` → `str`  *Create JavaScript code to get visible range.*
- @staticmethod `create_js_set_pane_layout(layout)` → `str`  *Create JavaScript code to set pane layout.*
- @staticmethod `create_js_get_pane_layout()` → `str`  *Create JavaScript code to get current pane layout.*

### `PyQtGraphChartStateHelper(object)`
*Helper for PyQtGraph chart state persistence.*

- @staticmethod `save_viewbox_state(viewbox)` → `Dict[str, Any]`  *Save PyQtGraph ViewBox state.*
- @staticmethod `restore_viewbox_state(viewbox, state_dict)`  *Restore PyQtGraph ViewBox state.*

### Module Functions
- `get_chart_state_manager()` → `ChartStateManager`  *Get global chart state manager instance.*

## `src/ui/widgets/chart_window.py`

### `ChartWindow(UIInspectorMixin, VariablesMixin, CelEditorMixin, BotPanelsMixin, KOFinderMixin, StrategySimulatorMixin, LevelsContextMixin, PanelsMixin, EventBusMixin, StateMixin, ChartChatMixin, BitunixTradingMixin, QMainWindow)`
*Popup window for displaying a single chart.*

- `open_main_settings_dialog()` → `None`  *Open main settings dialog (Issue #19 - called from toolbar).*
- `closeEvent(event)`  *Handle window close event with async state saving.*
- async `load_chart(data_provider)`  *Load chart data for the symbol.*
- `trigger_regime_update(debounce_ms, force)` → `None`  *Delegate regime update trigger to chart widget.*
- *...6 private methods*
- `__init__(symbol, history_manager, parent, splash)`  *Initialize chart window.*

## `src/ui/widgets/chart_window_dock_control.py`

### `ChartWindowDockControl(object)`
*Helper für ChartWindow Window Control (Layout Reset, TradingBotWindow toggle).*

- `minimize_dock()`  *Legacy method - minimize dock (no-op for TradingBotWindow).*
- `toggle_dock_maximized()`  *Legacy method - toggle dock maximize (no-op for TradingBotWindow).*
- `reset_layout()`  *Reset window layout to default state.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_window_dock_titlebar.py`

### `DockTitleBar(QWidget)`
*Custom title bar for dock widget with minimize/maximize buttons.*

- `set_maximized(maximized)`  *Update button state without emitting signal.*
- *...1 private methods*
- `__init__(title, parent)`

## `src/ui/widgets/chart_window_handlers.py`

### `ChartWindowHandlers(object)`
*Helper für ChartWindow Event Handlers (Button clicks, visibility changes).*

- `on_ai_chat_button_clicked(checked)`  *Handle AI Chat toolbar button click.*
- `on_bitunix_trading_button_clicked(checked)`  *Handle Bitunix Trading toolbar button click.*
- `on_ai_analysis_button_clicked(checked)` → `None`  *Open or focus the AI Analysis Popup.*
- `on_chart_live_data_toggle_clicked(checked)` → `None`  *Handle chart window live data toggle.*
- `on_main_live_data_toggled(checked)` → `None`  *Sync chart toggle with main window live data state.*
- `on_chart_stream_button_toggled(checked)` → `None`  *Sync chart toggle with chart stream state (fallback without main window).*
- `on_analysis_window_closed(result)` → `None`  *Handle analysis window close event to uncheck the button.*
- `on_dock_visibility_changed(visible)` → `None`  *Handle dock visibility change.*
- `on_bitunix_visibility_changed(visible)` → `None`  *Handle Bitunix widget visibility change.*
- `sync_bitunix_trading_button_state()` → `None`  *Ensure the toolbar toggle reflects the Bitunix widget visibility.*
- `update_chart_live_data_toggle(checked)` → `None`  *Update chart window live data toggle state and styling.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_window_lifecycle.py`

### `ChartWindowLifecycle(object)`
*Helper für ChartWindow Lifecycle (Close event, Cleanup, State saving).*

- `handle_close_event(event)`  *Handle window close event with async state saving.*
- `cleanup_simulation_on_close()` → `None`  *Stop simulation worker if running.*
- `finalize_close(event)` → `None`  *Finalize window close - cleanup and emit signal.*
- `save_enhanced_session_state()` → `None`  *Save enhanced session state (Phase 6: UI Refactoring).*
- `stop_live_stream_on_close()` → `None`  *Disconnect live stream if active.*
- `save_optional_state()` → `None`  *Save optional state (signal history, simulator state).*
- `cleanup_chat()` → `None`  *Cleanup chart chat resources.*
- `cleanup_bitunix_trading()` → `None`  *Clean up Bitunix trading resources.*
- `cleanup_trading_bot_window()` → `None`  *Clean up Trading Bot window resources.*
- `save_chart_state_snapshot()` → `None`  *Save current chart state (like on close) without closing the window.*
- `request_close_state(event)` → `None`  *Request chart state before closing.*
- async `load_chart(data_provider)`  *Load chart data for the symbol.*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/chart_window_mixins/bot_callbacks.py`

### `BotCallbacksMixin(BotCallbacksLifecycleMixin, BotCallbacksSignalMixin, BotCallbacksLogOrderMixin, BotCallbacksCandleMixin)`
*Mixin providing bot callback handlers.*


## `src/ui/widgets/chart_window_mixins/bot_callbacks_candle_mixin.py`

### `BotCallbacksCandleMixin(object)`
*BotCallbacksCandleMixin extracted from BotCallbacksMixin.*

- *...8 private methods*

## `src/ui/widgets/chart_window_mixins/bot_callbacks_lifecycle_mixin.py`

### `BotCallbacksLifecycleMixin(object)`
*BotCallbacksLifecycleMixin extracted from BotCallbacksMixin.*

- *...10 private methods*

## `src/ui/widgets/chart_window_mixins/bot_callbacks_log_order_mixin.py`

### `BotCallbacksLogOrderMixin(object)`
*BotCallbacksLogOrderMixin extracted from BotCallbacksMixin.*

- *...9 private methods*

## `src/ui/widgets/chart_window_mixins/bot_callbacks_position_lifecycle_mixin.py`

### `BotCallbacksPositionLifecycleMixin(object)`
*Position lifecycle callbacks (enter, exit, adjust)*

- *...5 private methods*

## `src/ui/widgets/chart_window_mixins/bot_callbacks_signal_mixin.py`

### `BotCallbacksSignalMixin(object)`
*BotCallbacksSignalMixin extracted from BotCallbacksMixin.*

- *...29 private methods*

## `src/ui/widgets/chart_window_mixins/bot_derivative_mixin.py`

### `BotDerivativeMixin(object)`
*Mixin providing derivative trading integration for ChartWindow.*

- *...13 private methods*

## `src/ui/widgets/chart_window_mixins/bot_display_logging_mixin.py`

### `BotDisplayLoggingMixin(object)`
*BotDisplayLoggingMixin extracted from BotDisplayManagerMixin.*

- `log_ki_request(request, response)` → `None`  *Log a KI request/response pair.*
- *...2 private methods*

## `src/ui/widgets/chart_window_mixins/bot_display_manager.py`

### `BotDisplayManagerMixin(BotDisplaySelectionMixin, BotDisplayPositionMixin, BotDisplaySignalsMixin, BotDisplayLoggingMixin, BotDisplayMetricsMixin)`
*Mixin providing bot display update methods.*


## `src/ui/widgets/chart_window_mixins/bot_display_metrics_mixin.py`

### `BotDisplayMetricsMixin(object)`
*BotDisplayMetricsMixin extracted from BotDisplayManagerMixin.*

- `update_strategy_scores(scores)` → `None`  *Update strategy scores table.*
- `update_walk_forward_results(results)` → `None`  *Update walk-forward results display.*
- `update_strategy_indicators(strategy_name)` → `None`  *Issue #2: Update strategy indicators display.*

## `src/ui/widgets/chart_window_mixins/bot_display_position_mixin.py`

### `BotDisplayPositionMixin(object)`
*BotDisplayPositionMixin extracted from BotDisplayManagerMixin.*

- *...36 private methods*

## `src/ui/widgets/chart_window_mixins/bot_display_selection_mixin.py`

### `BotDisplaySelectionMixin(object)`
*BotDisplaySelectionMixin extracted from BotDisplayManagerMixin.*

- *...4 private methods*

## `src/ui/widgets/chart_window_mixins/bot_display_signals_mixin.py`

### `BotDisplaySignalsMixin(object)`
*BotDisplaySignalsMixin extracted from BotDisplayManagerMixin.*

- *...18 private methods*

## `src/ui/widgets/chart_window_mixins/bot_event_handlers.py`

### `BotEventHandlersMixin(object)`
*Mixin providing bot event handlers and settings management.*

- `update_bot_symbol(symbol)` → `None`  *Update the bot panel with current symbol and load its settings.*
- *...23 private methods*

## `src/ui/widgets/chart_window_mixins/bot_panels_mixin.py`

### `BotPanelsMixin(BotUIPanelsMixin, BotEventHandlersMixin, BotCallbacksMixin, BotDisplayManagerMixin, BotPositionPersistenceMixin, BotDerivativeMixin)`
*Mixin providing bot control and monitoring panels.*

- *...17 private methods*

## `src/ui/widgets/chart_window_mixins/bot_position_persistence.py`

### `BotPositionPersistenceMixin(BotTRLockMixin, BotPositionPersistenceStorageMixin, BotPositionPersistenceRestoreMixin, BotPositionPersistencePnlMixin, BotPositionPersistenceContextMixin, BotPositionPersistenceChartMixin)`
*Mixin providing position persistence and chart integration.*


## `src/ui/widgets/chart_window_mixins/bot_position_persistence_chart_mixin.py`

### `BotPositionPersistenceChartMixin(object)`
*BotPositionPersistenceChartMixin extracted from BotPositionPersistenceMixin.*

- *...14 private methods*

## `src/ui/widgets/chart_window_mixins/bot_position_persistence_context_mixin.py`

### `BotPositionPersistenceContextMixin(object)`
*BotPositionPersistenceContextMixin extracted from BotPositionPersistenceMixin.*

- *...3 private methods*

## `src/ui/widgets/chart_window_mixins/bot_position_persistence_pnl_mixin.py`

### `BotPositionPersistencePnlMixin(object)`
*BotPositionPersistencePnlMixin extracted from BotPositionPersistenceMixin.*

- *...7 private methods*

## `src/ui/widgets/chart_window_mixins/bot_position_persistence_restore_mixin.py`

### `BotPositionPersistenceRestoreMixin(object)`
*BotPositionPersistenceRestoreMixin extracted from BotPositionPersistenceMixin.*

- *...11 private methods*

## `src/ui/widgets/chart_window_mixins/bot_position_persistence_storage_mixin.py`

### `BotPositionPersistenceStorageMixin(object)`
*BotPositionPersistenceStorageMixin extracted from BotPositionPersistenceMixin.*

- *...4 private methods*

## `src/ui/widgets/chart_window_mixins/bot_settings_manager.py`

### `BotSettingsManager(object)`
*Settings manager for bot configuration persistence.*

- `get_bot_settings()` → `dict`  *Sammelt alle Bot-Einstellungen in einem Dict.*
- `apply_bot_settings(settings)` → `None`  *Wendet gespeicherte Bot-Einstellungen an.*
- `on_save_defaults_clicked()` → `None`  *Speichert aktuelle Einstellungen als Standard.*
- `on_load_defaults_clicked()` → `None`  *Lädt gespeicherte Standard-Einstellungen.*
- `on_reset_defaults_clicked()` → `None`  *Setzt alle Einstellungen auf Factory-Defaults zurück.*
- *...1 private methods*
- `__init__(parent)`  *Initialize settings manager.*

## `src/ui/widgets/chart_window_mixins/bot_tr_lock_mixin.py`

### `BotTRLockMixin(object)`
*Mixin providing TR% lock feature for trailing stop management.*

- *...3 private methods*

## `src/ui/widgets/chart_window_mixins/bot_ui_control_handlers.py`

### `BotUIControlHandlers(object)`
*Event handlers for bot control UI interactions.*

- `on_open_help_clicked()` → `None`  *Open the trading bot help documentation.*
- `on_leverage_override_changed(state)` → `None`  *Handler für Leverage Override Checkbox.*
- `on_leverage_slider_changed(value)` → `None`  *Handler für Leverage Slider Wertänderung.*
- `on_trade_direction_changed(direction)` → `None`  *Handler für Trade Direction Änderung.*
- `__init__(parent)`  *Initialize event handlers.*

## `src/ui/widgets/chart_window_mixins/bot_ui_control_mixin.py`

### `BotUIControlMixin(object)`
*Bot UI Control Mixin - Main orchestrator using helper classes.*

- `get_leverage_override()` → `tuple[bool, int]`  *Get current leverage override status.*
- `get_bitunix_fees()` → `tuple[float, float]`  *Get current BitUnix fee settings (Issue #3).*
- `get_trade_direction()` → `str`  *Get current trade direction.*
- `set_trade_direction_from_backtest(direction)` → `None`  *Set trade direction based on backtesting result.*
- *...26 private methods*
- `__init__()`  *Initialize mixin (called by parent class).*

## `src/ui/widgets/chart_window_mixins/bot_ui_control_widgets.py`

### `BotUIControlWidgets(object)`
*Widget builder for bot control UI elements.*

- `build_control_group()` → `QGroupBox`  *Create bot control group with Start/Stop/Pause buttons.*
- `build_settings_group()` → `QGroupBox`  *Create bot settings group with all configuration options.*
- `build_quick_toggles_group()` → `QGroupBox`  *Create Quick Toggles group (Issue #43).*
- `build_leverage_override_group()` → `QGroupBox`  *Create Leverage Override group (Issue #43).*
- `build_bitunix_fees_group()` → `QGroupBox`  *Create BitUnix Fees group (Issue #3).*
- `build_trailing_group()` → `QGroupBox`  *Create trailing stop settings group.*
- `build_pattern_group()` → `QGroupBox`  *Create pattern validation settings group.*
- `build_display_group()` → `QGroupBox`  *Create chart display options group.*
- `build_help_button()` → `QPushButton`  *Create help button.*
- `__init__(parent)`  *Initialize widget builder.*

## `src/ui/widgets/chart_window_mixins/bot_ui_engine_settings_mixin.py`

### `BotUIEngineSettingsMixin(object)`
*Mixin providing Engine Settings tab for the Trading Bot panel.*

- *...9 private methods*

## `src/ui/widgets/chart_window_mixins/bot_ui_ki_logs_mixin.py`

### `BotUIKILogsMixin(object)`
*BotUIKILogsMixin extracted from BotUIPanelsMixin.*

- *...1 private methods*

## `src/ui/widgets/chart_window_mixins/bot_ui_panels.py`

### `BotUIPanelsMixin(BotUIControlMixin, BotUIStrategyMixin, BotUISignalsMixin, BotUIKILogsMixin, BotUIEngineSettingsMixin)`
*Mixin providing bot panel tab creation methods.*


## `src/ui/widgets/chart_window_mixins/bot_ui_signals_log_mixin.py`

### `BotUISignalsLogMixin(object)`
*Bot log management*

- *...11 private methods*

## `src/ui/widgets/chart_window_mixins/bot_ui_signals_mixin.py`

### `BotUISignalsMixin(BotSignalsEntryMixin, BotSignalsExitMixin, BotSignalsStatusMixin, BotSignalsBaseMixin)`
*Composite mixin for bot UI signals handling.*


## `src/ui/widgets/chart_window_mixins/bot_ui_strategy_mixin.py`

### `BotUIStrategyMixin(object)`
*BotUIStrategyMixin extracted from BotUIPanelsMixin.*

- *...10 private methods*

## `src/ui/widgets/chart_window_mixins/cel_editor_mixin.py`

### `CelEditorMixin(object)`
*Mixin for CEL Editor window integration.*

- `show_cel_editor()` → `None`  *Show the CEL Editor window.*
- `hide_cel_editor()` → `None`  *Hide the CEL Editor window.*
- *...7 private methods*

## `src/ui/widgets/chart_window_mixins/event_bus_mixin.py`

### `EventBusMixin(object)`
*Mixin providing event bus integration for ChartWindow.*

- *...12 private methods*

### Module Functions
- `_ts_to_chart_time(timestamp)` → `int`  *Convert timestamp to chart time (UTC).*

## `src/ui/widgets/chart_window_mixins/ko_finder_mixin.py`

### `KOFinderWorker(QThread)`
*Worker Thread für KO-Finder Suche.*

- `run()`  *Führe Suche in separatem Thread aus.*
- `__init__(underlying, config, underlying_price)`

### `KOFinderMixin(object)`
*Mixin providing KO-Finder tab for ChartWindow.*

- *...14 private methods*

## `src/ui/widgets/chart_window_mixins/levels_context_mixin.py`

### `LevelsContextMixin(object)`
*Mixin for Levels & Context functionality in ChartWindow.*

- *...15 private methods*

## `src/ui/widgets/chart_window_mixins/panels_mixin.py`

### `PanelsMixin(object)`
*Mixin providing panel/tab creation for ChartWindow.*

- `update_ai_chat_context(market_context)` → `None`  *Update AI Chat tab with current MarketContext (Issue #36).*
- *...7 private methods*

## `src/ui/widgets/chart_window_mixins/signals/bot_signals_base.py`

### `BotSignalsBaseMixin(object)`
*Base mixin providing shared infrastructure for signal handling.*

- *...14 private methods*

## `src/ui/widgets/chart_window_mixins/signals/bot_signals_entry.py`

### `BotSignalsEntryMixin(object)`
*Mixin for entry signal handling and order placement.*

- *...7 private methods*

## `src/ui/widgets/chart_window_mixins/signals/bot_signals_exit.py`

### `BotSignalsExitMixin(object)`
*Mixin for exit signal handling and position closing.*

- *...6 private methods*

## `src/ui/widgets/chart_window_mixins/signals/bot_signals_status.py`

### `BotSignalsStatusMixin(object)`
*Mixin for status display and signal table management.*

- *...7 private methods*

## `src/ui/widgets/chart_window_mixins/signals/widgets/sltp_progress_bar.py`

### `SLTPProgressBar(QProgressBar)`
*Custom progress bar showing price position between SL and TP.*

- `set_prices(entry, sl, tp, current, side)`  *Update the bar with new prices.*
- `paintEvent(event)`  *Custom paint for gradient background.*
- `reset_bar()`  *Reset bar to default state.*
- `__init__(parent)`  *Initialize SLTPProgressBar.*

## `src/ui/widgets/chart_window_mixins/state_mixin.py`

### `StateMixin(object)`
*Mixin providing state save/restore for ChartWindow.*

- `load_backtest_result(result)`  *Load and display backtest result in chart window.*
- *...11 private methods*

## `src/ui/widgets/chart_window_mixins/strategy_simulator_mixin.py`

### `StrategySimulatorMixin(StrategySimulatorUIMixin, StrategySimulatorParamsMixin, StrategySimulatorRunMixin, StrategySimulatorResultsMixin)`
*Mixin providing Strategy Simulator tab for ChartWindow.*


## `src/ui/widgets/chart_window_mixins/strategy_simulator_params_dialog.py`

### `TestParametersDialog(QDialog)`
*Dialog showing all current test/simulation parameters.*

- *...10 private methods*
- `__init__(parent, parameters)`  *Initialize the dialog.*

### Module Functions
- `create_test_parameters_dialog(parent, parameters)` → `TestParametersDialog`  *Factory function to create and show the test parameters dialog.*

## `src/ui/widgets/chart_window_mixins/strategy_simulator_params_mixin.py`

### `StrategySimulatorParamsMixin(object)`
*StrategySimulatorParamsMixin extracted from StrategySimulatorMixin.*

- *...28 private methods*

## `src/ui/widgets/chart_window_mixins/strategy_simulator_results_mixin.py`

### `StrategySimulatorResultsMixin(object)`
*StrategySimulatorResultsMixin extracted from StrategySimulatorMixin.*

- *...32 private methods*

## `src/ui/widgets/chart_window_mixins/strategy_simulator_run_mixin.py`

### `StrategySimulatorRunMixin(object)`
*StrategySimulatorRunMixin extracted from StrategySimulatorMixin.*

- *...40 private methods*

## `src/ui/widgets/chart_window_mixins/strategy_simulator_ui_mixin.py`

### `StrategySimulatorUIMixin(object)`
*StrategySimulatorUIMixin extracted from StrategySimulatorMixin.*

- *...20 private methods*

## `src/ui/widgets/chart_window_mixins/strategy_simulator_worker.py`

### `SimulationWorker(QThread)`
*Worker thread for running simulations.*

- `cancel()`  *Cancel running simulation.*
- `run()`  *Run simulation in separate thread.*
- *...7 private methods*
- `__init__(data, symbol, strategy_name, parameters, mode, opt_trials, objective_metric, entry_only, auto_strategy, sl_atr_multiplier, tp_atr_multiplier, atr_period, trailing_stop_enabled, trailing_stop_atr_multiplier, trailing_stop_mode, trailing_pct_distance, trailing_activation_pct, regime_adaptive, atr_trending_mult, atr_ranging_mult, maker_fee_pct, taker_fee_pct, trade_direction, initial_capital, position_size_pct, leverage)`

## `src/ui/widgets/chart_window_mixins/variables_mixin.py`

### `VariablesMixin(object)`
*Mixin for ChartWindow to integrate Variable Reference and Manager dialogs.*

- `setup_variables_integration()` → `None`  *Setup Variable dialogs integration.*
- `cleanup_variables()` → `None`  *Cleanup Variable dialogs on ChartWindow close.*
- *...8 private methods*

## `src/ui/widgets/chart_window_setup.py`

### `ChartWindowSetup(object)`
*Helper für ChartWindow Setup und Initialization.*

- `setup_window()` → `None`  *Configure main window properties.*
- `setup_chart_widget()` → `None`  *Setup central chart widget.*
- `setup_dock()` → `None`  *Setup Trading Bot window (standalone window, not a dock).*
- `restore_after_state_load()` → `None`  *Restore UI after state load.*
- `setup_shortcuts()` → `None`  *Setup keyboard shortcuts.*
- `open_strategy_concept()` → `None`  *Open Strategy Concept window (keyboard shortcut handler).*
- `connect_dock_signals()` → `None`  *Connect dock/window signals.*
- `setup_chat()` → `None`  *Setup chart chat integration.*
- `setup_bitunix_trading()` → `None`  *Set up Bitunix trading widget integration.*
- `setup_ai_analysis()` → `None`  *Setup the AI Analysis Popup.*
- `connect_data_loaded_signals()` → `None`  *Connect data loaded signals.*
- `activate_live_stream()`  *Activate live streaming when chart data is loaded.*
- `ensure_chat_docked_right()` → `None`  *Dock the chat widget to the right if it is not floating.*
- `sync_ai_chat_button_state()` → `None`  *Ensure the toolbar toggle reflects the dock visibility.*
- `schedule_chart_resize(delay_ms)` → `None`  *Throttle resize requests after dock/undock/visibility changes.*
- `on_chat_visibility_changed(visible)` → `None`
- `on_chat_top_level_changed(floating)` → `None`
- `on_chat_dock_location_changed(_area)` → `None`
- `open_trailing_stop_help()`  *Open the trailing stop help documentation in browser.*
- `setup_watchlist_dock()` → `None`  *Setup Watchlist as Left Dock (Phase 3: UI Refactoring).*
- `toggle_watchlist_dock()` → `None`  *Toggle watchlist dock visibility.*
- `setup_activity_log_dock()` → `None`  *Setup Activity Log as Bottom Dock (Phase 4: UI Refactoring).*
- `toggle_activity_log_dock()` → `None`  *Toggle activity log dock visibility.*
- *...5 private methods*
- `__init__(parent)`  *Args:*

## `src/ui/widgets/collapsible_section.py`

### `CollapsibleSection(QFrame)`
*A collapsible section with clickable header.*

- `toggle()` → `None`  *Toggle expanded/collapsed state.*
- `expand()` → `None`  *Expand the section.*
- `collapse()` → `None`  *Collapse the section.*
- `is_expanded()` → `bool`  *Check if section is expanded.*
- `set_content(widget)` → `None`  *Set the content widget.*
- `content_layout()` → `QVBoxLayout`  *Get the content layout to add widgets directly.*
- `set_title(title)` → `None`  *Update the section title.*
- *...2 private methods*
- `__init__(title, parent, expanded, icon)`

### `AccordionWidget(QWidget)`
*Container that manages multiple CollapsibleSections as an accordion.*

- `add_section(section)` → `None`  *Add a section to the accordion.*
- `add_stretch()` → `None`  *Add stretch at the end.*
- `collapse_all()` → `None`  *Collapse all sections.*
- `expand_first()` → `None`  *Expand the first section.*
- *...1 private methods*
- `__init__(parent, allow_all_collapsed)`

## `src/ui/widgets/column_updaters/base_updater.py`

### `BaseColumnUpdater(ABC)`
*Base class for table column updaters.*

- `can_update(column_index)` → `bool`  *Check if this updater handles the given column index.*
- `update(table, row, column, signal, context)` → `None`  *Update column value with formatting.*

## `src/ui/widgets/column_updaters/fees_updater.py`

### `FeesPercentUpdater(BaseColumnUpdater)`
*Updates Trading fees % column (column 14).*

- `can_update(column_index)` → `bool`  *Check if this is the fees % column.*
- `update(table, row, column, signal, context)` → `None`  *Update trading fees percentage with tooltip.*

### `FeesCurrencyUpdater(BaseColumnUpdater)`
*Updates Trading fees USDT column (column 15).*

- `can_update(column_index)` → `bool`  *Check if this is the fees USDT column.*
- `update(table, row, column, signal, context)` → `None`  *Update trading fees in USDT with breakdown tooltip.*

## `src/ui/widgets/column_updaters/pnl_updater.py`

### `PnLPercentUpdater(BaseColumnUpdater)`
*Updates P&L % column (column 12).*

- `can_update(column_index)` → `bool`  *Check if this is the P&L % column.*
- `update(table, row, column, signal, context)` → `None`  *Update P&L percentage with color and tooltip.*

### `PnLCurrencyUpdater(BaseColumnUpdater)`
*Updates P&L USDT column (column 13).*

- `can_update(column_index)` → `bool`  *Check if this is the P&L USDT column.*
- `update(table, row, column, signal, context)` → `None`  *Update P&L currency with color and tooltip.*

## `src/ui/widgets/column_updaters/position_updater.py`

### `InvestUpdater(BaseColumnUpdater)`
*Updates Invest USDT column (column 16).*

- `can_update(column_index)` → `bool`  *Check if this is the invest column.*
- `update(table, row, column, signal, context)` → `None`  *Update invested amount with tooltip.*

### `QuantityUpdater(BaseColumnUpdater)`
*Updates quantity/Stück column (column 17).*

- `can_update(column_index)` → `bool`  *Check if this is the quantity column.*
- `update(table, row, column, signal, context)` → `None`  *Update quantity with calculation tooltip.*

### `LiquidationUpdater(BaseColumnUpdater)`
*Updates liquidation price column (column 24).*

- `can_update(column_index)` → `bool`  *Check if this is the liquidation column.*
- `update(table, row, column, signal, context)` → `None`  *Update liquidation price with detailed tooltip.*

## `src/ui/widgets/column_updaters/price_updater.py`

### `CurrentPriceUpdater(BaseColumnUpdater)`
*Updates current/exit price column (column 11).*

- `can_update(column_index)` → `bool`  *Check if this is the current price column.*
- `update(table, row, column, signal, context)` → `None`  *Update current price or exit price for closed positions.*

## `src/ui/widgets/column_updaters/registry.py`

### `ColumnUpdaterRegistry(object)`
*Registry for column updaters following Strategy Pattern.*

- `register(updater)` → `None`  *Register a column updater.*
- `update(table, row, column, signal, context)` → `None`  *Dispatch column update to appropriate updater.*
- `__init__()` → `None`  *Initialize empty registry.*

## `src/ui/widgets/compact_chart_widget.py`

### `CompactChartWidget(QWidget)`
*Compact chart widget for Trading tab using Lightweight Charts.*

- `resizeEvent(event)` → `None`  *Handle resize event to ensure chart fits.*
- `fit_chart()`  *Fit chart to view.*
- `update_symbol(symbol)` → `None`  *Update displayed symbol.*
- `update_chart_data(df)` → `None`  *Update chart with OHLCV DataFrame.*
- `update_price(price)` → `None`  *Update current price display.*
- `clear_data()` → `None`  *Clear chart data.*
- *...12 private methods*
- `__init__(parent_chart)`  *Initialize compact chart widget.*

### `EnlargedChartDialog(QDialog)`
*Pop-up dialog showing enlarged chart with Lightweight Charts.*

- *...1 private methods*
- `__init__(chart_data, symbol, parent)`

## `src/ui/widgets/compounding_component/calculator.py`

### `Params(object)`

- `validate()` → `None`

### `DayResult(object)`


### `MonthKpis(object)`


### `SolveStatus(object)`


### Module Functions
- `_d(x)` → `Decimal`  *Sichere Decimal-Konvertierung (UI kann floats liefern).*
- `money(x)` → `Decimal`  *Rundet auf Cent (ROUND_HALF_UP).*
- `pct(x)` → `Decimal`  *Rundet Prozentwerte intern moderat (6 Nachkommastellen).*
- `simulate(params)` → `Tuple[List[DayResult], MonthKpis]`  *Simuliert params.days Tage. Alle Geldwerte Cent-genau gerundet.*
- `monthly_net_for_daily_pct(base_params, daily_profit_pct)` → `Decimal`
- `solve_daily_profit_pct_for_target(base_params, target_monthly_net, lo, hi, tol_eur, max_iter)` → `SolveStatus`
- `to_csv_rows(days)` → `List[List[str]]`

## `src/ui/widgets/compounding_component/compounding_ui_events.py`

### `CompoundingUIEventsMixin(object)`
*Mixin for event handling and user interactions.*

- `recompute(origin)` → `None`  *Main calculation trigger.*
- `closeEvent(event)` → `None`  *Save settings when widget is closed.*
- *...10 private methods*

### Module Functions
- `_to_dec(x)` → `Decimal`  *Convert float to Decimal.*

## `src/ui/widgets/compounding_component/compounding_ui_plots.py`

### `CompoundingUIPlotsMixin(object)`
*Mixin for chart rendering and visualization.*

- *...7 private methods*

## `src/ui/widgets/compounding_component/compounding_ui_setup.py`

### `MplCanvas(FigureCanvas)`
*Modern matplotlib canvas with dark theme and gradient support.*

- `apply_qt_palette(widget)` → `None`  *Apply Qt palette colors to matplotlib figure.*
- *...1 private methods*
- `__init__(parent)`

### `CompoundingUISetupMixin(object)`
*Mixin for UI widget creation and layout.*

- *...5 private methods*

## `src/ui/widgets/compounding_component/ui.py`

### `CompoundingPanel(CompoundingUISetupMixin, CompoundingUIEventsMixin, CompoundingUIPlotsMixin, QWidget)`
*Compounding/P&L Calculator Panel with settings persistence.*

- `__init__(parent)`

## `src/ui/widgets/dashboard.py`

### `DashboardWidget(QWidget)`
*Main dashboard widget displaying account overview.*

- `init_ui()`  *Initialize the dashboard UI.*
- `setup_event_handlers()`  *Setup event bus handlers.*
- `on_order_filled(event)`  *Handle order filled event.*
- `on_market_connected(event)`  *Handle market connected event.*
- `update_balance(balance)`  *Update balance display.*
- `update_pnl(pnl)`  *Update P&L display.*
- `update_positions_count(count)`  *Update open positions count.*
- `refresh_stats()`  *Refresh dashboard statistics from database or broker.*
- *...1 private methods*
- `__init__()`

## `src/ui/widgets/dashboard_metrics.py`

### `PerformanceMetrics(object)`
*Performance metrics data.*


### `MetricCard(QWidget)`
*Widget for displaying a single metric.*

- `update_value(value, suffix)`  *Update the metric value.*
- `__init__(title, value, suffix, color)`  *Initialize metric card.*

## `src/ui/widgets/dashboard_tabs_mixin.py`

### `DashboardTabsMixin(object)`
*Mixin providing tab creation methods for PerformanceDashboard.*

- *...6 private methods*

## `src/ui/widgets/deep_analysis_window.py`

### `DeepAnalysisWidget(QWidget)`
*Container for the advanced analysis workflow.*

- `update_from_initial_analysis(result_json)`  *Updates the context with the result from Tab 0.*
- `set_market_context(context)` → `None`  *Set MarketContext for AI Chat Tab and Data Overview (Phase 5.8).*
- `get_draw_zone_signal()`  *Get the draw_zone_requested signal from AI Chat Tab (Phase 5.9).*
- *...1 private methods*
- `__init__()`

## `src/ui/widgets/embedded_tradingview_bridge.py`

### `ChartBridge(QObject)`
*Bridge object for JavaScript to Python communication.*

- `onStopLineMoved(line_id, new_price)`  *Called from JavaScript when a stop line is dragged.*
- `onCrosshairMove(time, price)`  *Called from JavaScript when crosshair moves.*
- `get_crosshair_position()` → `tuple[float | None, float | None]`  *Get the last known crosshair position.*
- `onZoneDeleted(zone_id)`  *Called from JavaScript when a zone is deleted via the delete tool.*
- `onZoneClicked(zone_id, price, top, bottom, label)`  *Called from JavaScript when a zone is clicked (Phase 5.7).*
- `onLineDrawRequest(line_id, price, color, line_type)`  *Called from JavaScript when user draws a horizontal line (Issue #24).*
- `onVLineDrawRequest(line_id, timestamp, color)`  *Called from JavaScript when user draws a vertical line.*
- `pickColor(current_color)` → `str`  *Open QColorDialog and return the chosen color in CSS rgba format.*
- `__init__(parent)`

## `src/ui/widgets/embedded_tradingview_chart.py`

### `EmbeddedTradingViewChart(RegimeDisplayMixin, EntryAnalyzerMixin, StrategyConceptMixin, ChartAIMarkingsMixin, ChartMarkingMixin, LevelZonesMixin, ChartStatsLabelsMixin, BotOverlayMixin, ToolbarMixin, IndicatorMixin, StreamingMixin, DataLoadingMixin, ChartStateMixin, EmbeddedTradingViewChartUIMixin, EmbeddedTradingViewChartMarkingMixin, EmbeddedTradingViewChartJSMixin, EmbeddedTradingViewChartViewMixin, EmbeddedTradingViewChartLoadingMixin, EmbeddedTradingViewChartEventsMixin, QWidget)`
*Embedded TradingView Lightweight Charts widget.*

- `add_rect_range(low, high, label, color)` → `None`  *Draw a full-width rectangle between low/high prices.*
- `open_main_settings_dialog()` → `None`  *Open the main Settings dialog by walking up the parent chain.*
- `add_horizontal_line(price, label, color)` → `None`  *Draw a horizontal line at given price.*
- `refresh_chart_colors()` → `None`  *Refresh chart colors and background image from QSettings (Issues #34, #35, #37, ...*
- `resizeEvent(event)`  *Keep JS chart canvas in sync with Qt resize events (docks, chat, splitter).*
- *...4 private methods*
- `__init__(history_manager)`  *Initialize embedded chart widget.*

## `src/ui/widgets/embedded_tradingview_chart_events_mixin.py`

### `EmbeddedTradingViewChartEventsMixin(object)`
*EmbeddedTradingViewChartEventsMixin extracted from EmbeddedTradingViewChart.*

- *...8 private methods*

## `src/ui/widgets/embedded_tradingview_chart_js_mixin.py`

### `EmbeddedTradingViewChartJSMixin(object)`
*EmbeddedTradingViewChartJSMixin extracted from EmbeddedTradingViewChart.*

- *...2 private methods*

## `src/ui/widgets/embedded_tradingview_chart_loading_mixin.py`

### `EmbeddedTradingViewChartLoadingMixin(object)`
*EmbeddedTradingViewChartLoadingMixin extracted from EmbeddedTradingViewChart.*

- *...4 private methods*

## `src/ui/widgets/embedded_tradingview_chart_marking_mixin.py`

### `EmbeddedTradingViewChartMarkingMixin(object)`
*EmbeddedTradingViewChartMarkingMixin extracted from EmbeddedTradingViewChart.*

- *...12 private methods*

## `src/ui/widgets/embedded_tradingview_chart_ui_mixin.py`

### `EmbeddedTradingViewChartUIMixin(object)`
*EmbeddedTradingViewChartUIMixin extracted from EmbeddedTradingViewChart.*

- *...24 private methods*

## `src/ui/widgets/embedded_tradingview_chart_view_mixin.py`

### `EmbeddedTradingViewChartViewMixin(object)`
*EmbeddedTradingViewChartViewMixin extracted from EmbeddedTradingViewChart.*

- `zoom_to_fit_all()`  *Zoom to full data range and normalize pane heights.*
- `zoom_back_to_previous_view()` → `bool`  *Restore the previous zoom/layout state (one-step undo).*
- `request_chart_resize()` → `None`  *Force the JS chart to match the current Qt container size.*

## `src/ui/widgets/entry_expression_generator.py`

### `StrategyTemplate(Enum)`
*Vorgefertigte Strategy Templates.*


### `EntryExpressionGenerator(object)`
*Generiert CEL Entry Expressions aus Regime-Auswahl.*

- @staticmethod `generate(long_regimes, short_regimes, add_trigger, add_side_check, add_indicators, pretty)` → `str`  *Generiert entry_expression für Regime JSON.*
- @staticmethod `generate_from_template(template, available_regimes)` → `tuple[list[str], list[str]]`  *Generiert Regime-Auswahl basierend auf Template.*
- @staticmethod `get_template_description(template)` → `str`  *Gibt Beschreibung des Templates zurück.*
- *...1 private methods*

### Module Functions
- `quick_generate(long_regimes, short_regimes)` → `str`  *Quick-Generate mit Standard-Einstellungen.*
- `generate_conservative(available_regimes)` → `str`  *Generiert Conservative Strategy.*
- `generate_moderate(available_regimes)` → `str`  *Generiert Moderate Strategy.*
- `generate_aggressive(available_regimes)` → `str`  *Generiert Aggressive Strategy.*

## `src/ui/widgets/equity_curve_widget.py`

### `EquityCurveBridge(QObject)`
*Bridge für Python ↔ JavaScript Kommunikation.*

- `setEquityData(json_str)` → `None`  *Setzt Equity-Daten für JavaScript.*
- `getData()` → `str`  *Gibt aktuelle Daten als JSON zurück.*
- `__init__(parent)`

### `EquityCurveWidget(QWidget)`
*Widget für Equity Curve Visualisierung.*

- `load_equity_curve(equity_curve, trades, initial_capital)` → `None`  *Lädt Equity Curve und Trades in den Chart.*
- `load_from_result(result)` → `None`  *Lädt Daten aus einem BacktestResult.*
- `clear()` → `None`  *Leert den Chart.*
- *...5 private methods*
- `__init__(parent)`  *Initialisiert das Widget.*

## `src/ui/widgets/indicators.py`

### `IndicatorsWidget(QWidget)`
*Widget for managing technical indicators.*

- *...8 private methods*
- `__init__()`  *Initialize indicators widget.*

## `src/ui/widgets/ko_finder/filter_panel.py`

### `KOFilterPanel(QWidget)`
*Filter-Panel mit Controls für KO-Suche.*

- `get_config()` → `KOFilterConfig`  *Erstelle KOFilterConfig aus aktuellen UI-Werten.*
- `set_config(config)` → `None`  *Setze UI-Werte aus Konfiguration.*
- `set_loading(loading)` → `None`  *Setze Ladezustand.*
- *...6 private methods*
- `__init__(parent)` → `None`  *Initialisiere Panel.*

## `src/ui/widgets/ko_finder/result_panel.py`

### `KOResultPanel(QWidget)`
*Ergebnis-Panel mit Tabellen und Meta-Infos.*

- `set_response(response)` → `None`  *Setze Suchergebnis.*
- `clear()` → `None`  *Lösche alle Daten.*
- `set_status(message, status_type)` → `None`  *Setze kurze Status-Meldung.*
- `update_ko_distance(underlying_price)` → `None`  *Aktualisiere KO-Abstand für alle Produkte mit neuem Kurs.*
- `highlight_product(wkn)` → `bool`  *Highlight a product by WKN in the tables.*
- *...8 private methods*
- `__init__(parent)` → `None`  *Initialisiere Panel.*

## `src/ui/widgets/ko_finder/settings_dialog.py`

### `KOSettingsDialog(QDialog)`
*Einstellungs-Dialog für KO-Finder Score-Parameter.*

- @staticmethod `get_scoring_params()`  *Hole ScoringParams aus QSettings.*
- @staticmethod `get_top_n()` → `int`  *Hole Top-N Einstellung aus QSettings.*
- *...9 private methods*
- `__init__(parent)` → `None`  *Initialisiere Dialog.*

## `src/ui/widgets/ko_finder/table_model.py`

### `KOProductTableModel(QAbstractTableModel)`
*TableModel für KO-Produkte.*

- `set_products(products)` → `None`  *Setze Produktliste.*
- `clear()` → `None`  *Lösche alle Produkte.*
- `get_product(row)` → `KnockoutProduct | None`  *Hole Produkt für Zeile.*
- `rowCount(parent)` → `int`  *Anzahl Zeilen.*
- `columnCount(parent)` → `int`  *Anzahl Spalten.*
- `headerData(section, orientation, role)` → `Any`  *Header-Daten.*
- `data(index, role)` → `Any`  *Zellen-Daten.*
- `sort(column, order)` → `None`  *Sortiere nach Spalte.*
- *...4 private methods*
- `__init__(parent)` → `None`  *Initialisiere Model.*

## `src/ui/widgets/market_sessions_overlay.py`

### `MarketSessionsOverlay(QWidget)`
*Semi-transparent overlay for market session info.*

- `init_ui()`  *Initialize the UI components.*
- `update_price(price)`  *Update current price display.*
- `set_symbol_info(symbol, prev_close)`  *Update symbol and previous close data.*
- `update_sessions()`  *Update active session badges and next event text.*
- `__init__(parent)`

## `src/ui/widgets/notification_widget.py`

### `NotificationWidget(QWidget)`
*Kombiniertes Widget für WhatsApp und Telegram Benachrichtigungen.*

- `get_current_service()` → `str`  *Gibt den aktuell ausgewählten Service zurück ('telegram' oder 'whatsapp').*
- `get_telegram_widget()` → `TelegramWidget`  *Gibt das Telegram-Widget zurück.*
- `get_whatsapp_widget()` → `WhatsAppWidget`  *Gibt das WhatsApp-Widget zurück.*
- `send_trade_notification(message)` → `bool`  *Sendet eine Trade-Benachrichtigung über den aktuell ausgewählten Service.*
- `is_enabled()` → `bool`  *Gibt zurück ob Benachrichtigungen im aktuellen Service aktiviert sind.*
- *...5 private methods*
- `__init__(parent)`

## `src/ui/widgets/optimization_waiting_dialog.py`

### `SpinnerWidget(QWidget)`
*Animated spinner widget with rotating logo in center.*

- `paintEvent(event)`
- `stop()`  *Stop the spinner animation.*
- *...1 private methods*
- `__init__(parent, logo_path)`

### `OptimizationWaitingDialog(QDialog)`
*Dialog shown while processing optimization results.*

- `set_status(status)`  *Update the status text and keep animation running.*
- `close_with_delay(delay_ms)`  *Close dialog after ensuring minimum joke display time.*
- `closeEvent(event)`  *Clean up on close.*
- *...3 private methods*
- `__init__(parent)`

### Module Functions
- `_get_app_icon_path()` → `Path`  *Get the app icon path for the spinner logo.*

## `src/ui/widgets/orders.py`

### `OrdersWidget(BaseTableWidget)`
*Widget for displaying orders.*

- `on_order_created(event)`  *Handle order created event.*
- `on_order_updated(event)`  *Handle order update events.*
- `add_order(order_data)`  *Add a new order to the table.*
- `update_order(order_data)`  *Update an existing order in the table.*
- *...3 private methods*
- `__init__(parent)`

## `src/ui/widgets/pattern_analysis_widgets.py`

### `PatternAnalysisSettings(QWidget)`
*Reusable pattern analysis settings panel.*

- `get_settings()` → `dict`  *Return current settings as dict.*
- *...3 private methods*
- `__init__(parent)`

### `PatternResultsDisplay(QWidget)`
*Reusable pattern analysis results display.*

- `update_from_analysis(analysis)` → `None`  *Update display with analysis results.*
- `clear()` → `None`  *Clear all displayed results.*
- *...1 private methods*
- `__init__(parent)`

### `PatternMatchesTable(QTableWidget)`
*Reusable table for displaying pattern matches.*

- `populate_from_matches(matches, max_rows)` → `None`  *Populate table with pattern matches.*
- `clear_table()` → `None`  *Clear all rows from table.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/widgets/pattern_integration_widget.py`

### `PatternIntegrationWidget(QWidget)`
*Tab 2: Pattern-to-Strategy Integration with success rates.*

- `update_patterns(patterns)`  *Update widget with detected patterns (called from Tab 1).*
- *...9 private methods*
- `__init__(parent)`

## `src/ui/widgets/pattern_recognition_widget.py`

### `PatternAnalysisThread(QThread)`
*Background thread for running async pattern analysis.*

- `run()`  *Run pattern analysis in background thread with its own event loop.*
- *...1 private methods*
- `__init__(bars, symbol, timeframe, settings)`

### `PatternRecognitionWidget(QWidget)`
*Tab 1: Pattern Recognition using existing PatternService and shared widgets.*

- `closeEvent(event)`  *Clean up resources when widget is closed.*
- `enable_auto_update(enabled)`  *Enable or disable automatic pattern DB updates.*
- `set_auto_update_interval(minutes)`  *Set the auto-update interval in minutes.*
- `set_pending_bars_threshold(bars)`  *Set the threshold for triggering updates based on new bars.*
- *...25 private methods*
- `__init__(parent, chart_window)`

## `src/ui/widgets/performance_dashboard.py`

### `PerformanceDashboard(DashboardTabsMixin, QWidget)`
*Performance dashboard widget.*

- *...13 private methods*
- `__init__()`  *Initialize performance dashboard.*

## `src/ui/widgets/performance_monitor_widget.py`

### `PerformanceMonitorWidget(QWidget)`
*Real-time performance monitoring widget for regime-based trading.*

- `set_stability_tracker(tracker)`  *Set the regime stability tracker to monitor.*
- `start_monitoring(update_interval_ms)`  *Start real-time monitoring.*
- `stop_monitoring()`  *Stop real-time monitoring.*
- `is_monitoring()` → `bool`  *Check if monitoring is active.*
- *...15 private methods*
- `__init__(parent)`  *Initialize performance monitor widget.*

## `src/ui/widgets/positions.py`

### `PositionsWidget(BaseTableWidget)`
*Widget for displaying current positions.*

- `update_positions(positions)`  *Update positions table.*
- `on_order_filled(event)`  *Handle order filled event - refresh positions.*
- `on_market_tick(event)`  *Handle market tick - update prices if needed.*
- `refresh()`  *Refresh positions display from database.*
- *...4 private methods*

## `src/ui/widgets/regime_badge_widget.py`

### `RegimeBadgeWidget(QFrame)`
*Kompaktes Badge-Widget zur Anzeige des Markt-Regimes.*

- `set_regime(regime, adx, gate_reason, allows_entry)` → `None`  *Update the displayed regime.*
- `set_regime_from_result(result)` → `None`  *Update from a RegimeResult object.*
- `get_regime()` → `str`  *Return current regime type.*
- `mousePressEvent(event)` → `None`  *Handle mouse click.*
- *...4 private methods*
- `__init__(compact, show_icon, parent)`  *Initialize the Regime Badge Widget.*

### `RegimeInfoPanel(QFrame)`
*Erweitertes Panel für Regime-Informationen.*

- `set_regime_result(result)` → `None`  *Update panel from RegimeResult.*
- `set_regime_from_data(regime, adx, di_plus, di_minus, atr, allows_entry, gate_reason)` → `None`  *Update panel from individual values.*
- *...1 private methods*
- `__init__(parent)`

### Module Functions
- `create_regime_badge(compact, show_icon)` → `RegimeBadgeWidget`  *Factory function to create a RegimeBadgeWidget.*
- `create_regime_info_panel()` → `RegimeInfoPanel`  *Factory function to create a RegimeInfoPanel.*

## `src/ui/widgets/regime_editor_widget.py`

### `JsonTreeItem(QTreeWidgetItem)`
*Tree item with JSON data tracking.*

- *...1 private methods*
- `__init__(key, value, parent, json_path)`

### `RegimeEditorWidget(QWidget)`
*Generic JSON Editor Widget.*

- `load_config(file_path)`  *Load any JSON file and populate tree.*
- `has_unsaved_changes()` → `bool`  *Check if there are unsaved changes.*
- *...32 private methods*
- `__init__(parent)`

## `src/ui/widgets/regime_entry_expression_editor.py`

### `RegimeEntryExpressionEditor(QWidget)`
*Editor für Regime JSON Entry Expressions.*

- `load_json_path(json_path)`  *Lädt JSON programmatisch (für externe Aufrufe).*
- `get_current_expression()` → `str`  *Gibt aktuelle generierte Expression zurück.*
- *...19 private methods*
- `__init__(parent)`

## `src/ui/widgets/regime_json_parser.py`

### `RegimeInfo(object)`
*Information über ein einzelnes Regime.*

- @property `display_name()` → `str`  *Display-Name für UI.*
- `__str__()` → `str`

### `RegimeJsonData(object)`
*Geparste Daten aus Regime JSON.*

- @property `regime_ids()` → `list[str]`  *Liste aller Regime-IDs.*
- @property `regime_by_id()` → `dict[str, RegimeInfo]`  *Dict mit Regime-ID als Key.*
- `get_bull_regimes()` → `list[RegimeInfo]`  *Gibt alle Bull-Regimes zurück (heuristisch).*
- `get_bear_regimes()` → `list[RegimeInfo]`  *Gibt alle Bear-Regimes zurück (heuristisch).*
- `get_neutral_regimes()` → `list[RegimeInfo]`  *Gibt neutrale Regimes zurück (heuristisch).*

### `RegimeJsonParser(object)`
*Parser für Entry Analyzer Regime JSON Dateien.*

- @staticmethod `parse(json_path)` → `RegimeJsonData`  *Parst Regime JSON und extrahiert relevante Daten.*
- @staticmethod `validate_json_structure(json_path)` → `tuple[bool, str]`  *Validiert JSON-Struktur ohne vollständiges Parsing.*

### Module Functions
- `load_regime_json(json_path)` → `RegimeJsonData`  *Convenience-Funktion zum Laden von Regime JSON.*
- `get_regime_names(json_path)` → `list[str]`  *Extrahiert nur Regime-Namen aus JSON.*

## `src/ui/widgets/regime_json_writer.py`

### `RegimeJsonWriter(object)`
*Schreibt entry_expression in Regime JSON Dateien.*

- @staticmethod `write_entry_expression(json_path, entry_expression, create_backup, add_comments)` → `tuple[bool, str]`  *Fügt entry_expression zu Regime JSON hinzu.*
- @staticmethod `save_as_new(json_path, entry_expression, new_name)` → `tuple[bool, str, Optional[Path]]`  *Speichert JSON mit entry_expression als neue Datei.*
- @staticmethod `remove_entry_expression(json_path, create_backup)` → `tuple[bool, str]`  *Entfernt entry_expression aus JSON.*
- *...1 private methods*

### Module Functions
- `quick_save(json_path, entry_expression)` → `bool`  *Quick-Save mit Standard-Einstellungen.*

## `src/ui/widgets/settings/entry_score_persistence.py`

### `EntryScorePersistence(object)`
*Helper for settings persistence operations.*

- `get_settings()` → `dict`  *Get current settings as dict.*
- `set_settings(settings)` → `None`  *Set settings from dict.*
- `load_settings()` → `None`  *Load settings from config file.*
- `apply_settings()` → `None`  *Apply settings to engine.*
- `save_settings()` → `None`  *Save settings to config file.*
- `reset_to_defaults()` → `None`  *Reset to default settings (Micro-Account optimiert).*
- `__init__(parent)`

## `src/ui/widgets/settings/entry_score_settings.py`

### `EntryScoreSettingsWidget(QWidget)`
*Settings widget for Entry Score Engine.*

- `load_settings()` → `None`  *Load settings from config file.*
- `apply_settings()` → `None`  *Apply settings (in-memory only, does not save to file).*
- `save_settings()` → `None`  *Save settings to config file.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/widgets/settings/entry_score_settings_widget.py`

### `EntryScoreSettingsWidget(QWidget)`
*Widget für EntryScoreEngine-Einstellungen.*

- `get_settings()` → `dict`  *Get current settings as dict.*
- `set_settings(settings)` → `None`  *Set settings from dict.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/widgets/settings/entry_score_signals.py`

### `EntryScoreSignals(object)`
*Helper for connecting widget signals.*

- `connect_signals()` → `None`  *Connect change signals.*
- `__init__(parent)`

## `src/ui/widgets/settings/entry_score_ui_entry.py`

### `EntryScoreUIEntry(object)`
*Helper for creating entry requirements UI group.*

- `create_entry_group()` → `QGroupBox`  *Create entry requirements group.*
- `__init__(parent)`

## `src/ui/widgets/settings/entry_score_ui_gates.py`

### `EntryScoreUIGates(object)`
*Helper for creating regime gates UI group.*

- `create_gates_group()` → `QGroupBox`  *Create regime gate settings group.*
- `__init__(parent)`

## `src/ui/widgets/settings/entry_score_ui_thresholds.py`

### `EntryScoreUIThresholds(object)`
*Helper for creating quality thresholds UI group.*

- `create_thresholds_group()` → `QGroupBox`  *Create quality threshold settings group.*
- `__init__(parent)`

## `src/ui/widgets/settings/entry_score_ui_weights.py`

### `EntryScoreUIWeights(object)`
*Helper for creating component weights UI group.*

- `create_weights_group()` → `QGroupBox`  *Create component weights settings group.*
- `__init__(parent)`

## `src/ui/widgets/settings/entry_score_validation.py`

### `EntryScoreValidation(object)`
*Helper for weight validation logic.*

- `on_weight_changed()` → `None`  *Update weight sum display.*
- `emit_settings_changed()` → `None`  *Emit settings changed signal.*
- `__init__(parent)`

## `src/ui/widgets/settings/level_settings.py`

### `LevelSettingsWidget(QWidget)`
*Settings widget for Level Engine.*

- `load_settings()` → `None`  *Load settings from config file.*
- `apply_settings()` → `None`  *Apply settings.*
- `save_settings()` → `None`  *Save settings to config file.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/widgets/settings/level_settings_widget.py`

### `LevelSettingsWidget(QWidget)`
*Widget für LevelEngine-Einstellungen.*

- `get_config()` → `dict`  *Get current configuration as dictionary.*
- `set_config(config)` → `None`  *Set configuration from dictionary.*
- *...12 private methods*
- `__init__(parent)`

### Module Functions
- `create_level_settings_tab()` → `QWidget`  *Factory function to create a Level Settings Tab.*

## `src/ui/widgets/settings/leverage_settings.py`

### `LeverageSettingsWidget(QWidget)`
*Settings widget for Leverage Rules Engine.*

- `load_settings()` → `None`  *Load settings from config file.*
- `apply_settings()` → `None`  *Apply settings.*
- `save_settings()` → `None`  *Save settings to config file.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/widgets/settings/leverage_settings_widget.py`

### `LeverageSettingsWidget(QWidget)`
*Widget für LeverageRulesEngine-Einstellungen.*

- `get_settings()` → `dict`  *Get current settings as dict.*
- `set_settings(settings)` → `None`  *Set settings from dict.*
- *...11 private methods*
- `__init__(parent)`

## `src/ui/widgets/settings/llm_validation_settings.py`

### `LLMValidationSettingsWidget(QWidget)`
*Settings widget for LLM Validation Service.*

- `load_settings()` → `None`  *Load settings from config file.*
- `apply_settings()` → `None`  *Apply settings.*
- `save_settings()` → `None`  *Save settings to config file.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/widgets/settings/llm_validation_settings_widget.py`

### `LLMValidationSettingsWidget(QWidget)`
*Widget für LLMValidationService-Einstellungen.*

- `get_settings()` → `dict`  *Get current settings as dict.*
- `set_settings(settings)` → `None`  *Set settings from dict.*
- *...11 private methods*
- `__init__(parent)`

## `src/ui/widgets/settings/trigger_exit_settings.py`

### `TriggerExitSettingsWidget(QWidget)`
*Settings widget for Trigger & Exit Engine.*

- `load_settings()` → `None`  *Load settings from config file.*
- `apply_settings()` → `None`  *Apply settings.*
- `save_settings()` → `None`  *Save settings to config file.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/widgets/settings/trigger_exit_settings_management.py`

### `TriggerExitSettingsManagement(object)`
*Helper for settings management.*

- `connect_signals()` → `None`  *Connect change signals.*
- `emit_settings_changed()` → `None`  *Emit settings changed signal.*
- `get_settings()` → `dict`  *Get current settings as dict.*
- `set_settings(settings)` → `None`  *Set settings from dict.*
- `__init__(parent)`

## `src/ui/widgets/settings/trigger_exit_settings_persistence.py`

### `TriggerExitSettingsPersistence(object)`
*Helper for settings persistence.*

- `load_settings()` → `None`  *Load settings from config file.*
- `apply_settings()` → `None`  *Apply settings to engine.*
- `save_settings()` → `None`  *Save settings to config file.*
- `reset_to_defaults()` → `None`  *Reset to default settings (Micro-Account optimiert).*
- `__init__(parent)`

## `src/ui/widgets/settings/trigger_exit_settings_ui_groups.py`

### `TriggerExitSettingsUIGroups(object)`
*Helper for UI group creation.*

- `create_breakout_group()` → `QGroupBox`  *Create breakout trigger settings.*
- `create_pullback_group()` → `QGroupBox`  *Create pullback trigger settings.*
- `create_sfp_group()` → `QGroupBox`  *Create SFP trigger settings.*
- `create_sl_group()` → `QGroupBox`  *Create stop loss settings.*
- `create_tp_group()` → `QGroupBox`  *Create take profit settings.*
- `create_trailing_group()` → `QGroupBox`  *Create trailing stop settings.*
- `create_time_group()` → `QGroupBox`  *Create time stop settings.*
- `create_partial_tp_group()` → `QGroupBox`  *Create partial take profit settings.*
- `__init__(parent)`

## `src/ui/widgets/settings/trigger_exit_settings_widget.py`

### `TriggerExitSettingsWidget(QWidget)`
*Widget für TriggerExitEngine-Einstellungen (REFACTORED).*

- `get_settings()` → `dict`  *Get current settings as dict (delegiert).*
- `set_settings(settings)` → `None`  *Set settings from dict (delegiert).*
- *...7 private methods*
- `__init__(parent)`

## `src/ui/widgets/syntax_handlers/base_handler.py`

### `TokenMatch(object)`
*Result of token matching.*


### `BaseTokenHandler(ABC)`
*Base class for syntax token handlers.*

- `try_match(text, position)` → `TokenMatch`  *Try to match a token at the given position.*
- `get_priority()` → `int`  *Get handler priority (lower = higher priority).*

## `src/ui/widgets/syntax_handlers/comment_handler.py`

### `CommentHandler(BaseTokenHandler)`
*Handles // style comments.*

- `try_match(text, position)` → `TokenMatch`  *Match comment at position.*
- `get_priority()` → `int`  *Comments have high priority (must match before operators).*
- `__init__(comment_style)`  *Initialize comment handler.*

## `src/ui/widgets/syntax_handlers/default_handler.py`

### `DefaultHandler(BaseTokenHandler)`
*Fallback handler for unrecognized characters.*

- `try_match(text, position)` → `TokenMatch`  *Match any character.*
- `get_priority()` → `int`  *Default handler has lowest priority (last resort).*
- `__init__(default_style)`  *Initialize default handler.*

## `src/ui/widgets/syntax_handlers/handler_registry.py`

### `HandlerRegistry(object)`
*Registry that coordinates multiple token handlers.*

- `register(handler)`  *Register a new token handler.*
- `try_match(text, position)` → `TokenMatch`  *Try to match a token using registered handlers.*
- `clear()`  *Remove all registered handlers.*
- `get_handler_count()` → `int`  *Get number of registered handlers.*
- *...1 private methods*
- `__init__()`  *Initialize empty registry.*

## `src/ui/widgets/syntax_handlers/identifier_handler.py`

### `IdentifierHandler(BaseTokenHandler)`
*Handles identifiers and classifies them as keywords, functions, etc.*

- `try_match(text, position)` → `TokenMatch`  *Match identifier at position.*
- `get_priority()` → `int`  *Identifiers have low priority (matched after everything else).*
- *...1 private methods*
- `__init__(keywords, trading_keywords, functions, variables, keyword_style, function_style, variable_style, indicator_style, identifier_style)`  *Initialize identifier handler.*

## `src/ui/widgets/syntax_handlers/number_handler.py`

### `NumberHandler(BaseTokenHandler)`
*Handles numeric literals (integers and floats).*

- `try_match(text, position)` → `TokenMatch`  *Match number at position.*
- `get_priority()` → `int`  *Numbers have medium-high priority.*
- `__init__(number_style)`  *Initialize number handler.*

## `src/ui/widgets/syntax_handlers/operator_handler.py`

### `OperatorHandler(BaseTokenHandler)`
*Handles operators (both single and multi-character).*

- `try_match(text, position)` → `TokenMatch`  *Match operator at position.*
- `get_priority()` → `int`  *Operators have medium priority.*
- `__init__(operator_style, multi_char_ops, single_char_ops)`  *Initialize operator handler.*

## `src/ui/widgets/syntax_handlers/string_handler.py`

### `StringHandler(BaseTokenHandler)`
*Handles string literals (both single and double quotes).*

- `try_match(text, position)` → `TokenMatch`  *Match string literal at position.*
- `get_priority()` → `int`  *Strings have high priority.*
- `__init__(string_style)`  *Initialize string handler.*

## `src/ui/widgets/syntax_handlers/whitespace_handler.py`

### `WhitespaceHandler(BaseTokenHandler)`
*Handles whitespace characters.*

- `try_match(text, position)` → `TokenMatch`  *Match whitespace at position.*
- `get_priority()` → `int`  *Whitespace has lowest priority.*
- `__init__(default_style)`  *Initialize whitespace handler.*

## `src/ui/widgets/telegram_widget.py`

### `TelegramWidget(QWidget)`
*Widget für Telegram-Benachrichtigungen im Trading Bot.*

- `set_chat_id(chat_id)` → `None`  *Setzt die Chat-ID.*
- `set_enabled(enabled)` → `None`  *Aktiviert/Deaktiviert Benachrichtigungen.*
- `is_enabled()` → `bool`  *Gibt zurück ob Benachrichtigungen aktiviert sind.*
- `get_service()`  *Gibt den Telegram-Service zurück.*
- `send_trade_notification(message)` → `bool`  *Sendet eine Trade-Benachrichtigung über das UI-Formular.*
- *...11 private methods*
- `__init__(parent)`

## `src/ui/widgets/trading_bot_window.py`

### `TradingBotWindow(QMainWindow)`
*Standalone window for Trading Bot panel.*

- `showEvent(event)` → `None`  *Handle show event - restore maximized state if needed.*
- `resizeEvent(event)` → `None`  *Track geometry changes for save/restore.*
- `moveEvent(event)` → `None`  *Track position changes for save/restore.*
- `hideEvent(event)` → `None`  *Handle hide event - save state before hiding.*
- `changeEvent(event)` → `None`  *Track window state changes (maximize/restore).*
- `closeEvent(event)` → `None`  *Handle window close event.*
- `toggle_visibility()` → `None`  *Toggle window visibility with state restoration.*
- `update_symbol(symbol)` → `None`  *Update window title with new symbol.*
- *...4 private methods*
- `__init__(parent_chart, panel_content)`  *Initialize Trading Bot window.*

## `src/ui/widgets/trading_journal_errors_tab.py`

### `ErrorsTab(QWidget)`
*Tab für Bot-Fehler.*

- `add_error(error_data)` → `None`  *Fügt einen Fehler hinzu.*
- `clear()` → `None`  *Löscht alle Fehler.*
- `get_errors()` → `list[dict]`  *Gibt alle gespeicherten Fehler zurück.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/widgets/trading_journal_llm_tab.py`

### `LLMOutputsTab(QWidget)`
*Tab für LLM-Validierungsausgaben.*

- `add_output(output_data)` → `None`  *Fügt eine LLM-Ausgabe hinzu.*
- `clear()` → `None`  *Löscht alle LLM-Ausgaben.*
- `get_outputs()` → `list[dict]`  *Gibt alle gespeicherten LLM-Ausgaben zurück.*
- *...2 private methods*
- `__init__(parent)`

## `src/ui/widgets/trading_journal_signals_tab.py`

### `SignalsTab(QWidget)`
*Tab für Signal-Historie (Entry-Signale des Bots) + Trading Bot Log.*

- `add_signal(signal_data)` → `None`  *Fügt ein Signal zur Historie hinzu.*
- `clear()` → `None`  *Löscht alle Signale.*
- `get_signals()` → `list[dict]`  *Gibt alle gespeicherten Signale zurück.*
- `append_log(log_type, message)` → `None`  *Fügt einen Log-Eintrag hinzu.*
- `set_current_task(task)` → `None`  *Setzt die aktuelle Bot-Aufgabe.*
- `set_bot_running(is_running)` → `None`  *Aktualisiert den Running-Status.*
- `clear_log()` → `None`  *Löscht alle Log-Einträge.*
- `save_log()` → `None`  *Speichert Log in eine Datei.*
- `get_log_entries()` → `list[str]`  *Gibt alle Log-Einträge zurück.*
- `is_bot_running()` → `bool`  *Gibt zurück ob der Bot läuft.*
- *...3 private methods*
- `__init__(parent)`

## `src/ui/widgets/trading_journal_trades_tab.py`

### `TradesTab(QWidget)`
*Tab für abgeschlossene Trades (aus logs/trades/*.json).*

- *...8 private methods*
- `__init__(parent)`

## `src/ui/widgets/trading_journal_widget.py`

### `TradingJournalWidget(QWidget)`
*Main Widget für Trading-Journal mit Tabs für Signals, Trades, LLM-Outputs, Errors.*

- `add_signal(signal_data)` → `None`  *Fügt ein Signal zur Historie hinzu.*
- `add_llm_output(output_data)` → `None`  *Fügt eine LLM-Ausgabe hinzu.*
- `add_error(error_data)` → `None`  *Fügt einen Fehler hinzu.*
- `append_bot_log(log_type, message)` → `None`  *Fügt einen Bot-Log-Eintrag hinzu.*
- `set_bot_running(is_running)` → `None`  *Setzt den Bot-Running-Status.*
- `set_bot_current_task(task)` → `None`  *Setzt die aktuelle Bot-Aufgabe.*
- `clear_bot_log()` → `None`  *Löscht alle Bot-Log-Einträge.*
- `get_bot_log_entries()` → `list[str]`  *Gibt alle Bot-Log-Einträge zurück.*
- `is_bot_running()` → `bool`  *Gibt zurück ob der Bot läuft.*
- *...4 private methods*
- `__init__(parent)`

## `src/ui/widgets/trading_status_panel.py`

### `StatusCard(QFrame)`
*Reusable status card component.*

- `set_value(value, color)` → `None`  *Set the main value.*
- `set_subtitle(text)` → `None`  *Set the subtitle text.*
- `__init__(title, parent)`

### `ScoreBar(QWidget)`
*Visual score bar with colored segments.*

- `set_score(score, quality)` → `None`  *Set the score value with quality-based coloring.*
- `__init__(parent)`

### `TradingStatusPanel(QWidget)`
*Comprehensive trading status panel.*

- `update_regime(regime_result)` → `None`  *Update regime display.*
- `update_entry_score(score_result)` → `None`  *Update entry score display.*
- `update_llm_validation(llm_result)` → `None`  *Update LLM validation display.*
- `update_trigger(trigger_result)` → `None`  *Update trigger info display.*
- `update_leverage(leverage_result)` → `None`  *Update leverage display.*
- `update_all(regime_result, score_result, llm_result, trigger_result, leverage_result)` → `None`  *Update all status displays at once.*
- `start_auto_refresh(interval_ms)` → `None`  *Start auto-refresh timer.*
- `stop_auto_refresh()` → `None`  *Stop auto-refresh timer.*
- *...2 private methods*
- `__init__(parent)`

## `src/ui/widgets/watchlist.py`

### `WatchlistWidget(QWidget)`
*Widget displaying watchlist with real-time updates (REFACTORED).*

- `init_ui()`  *Initialize user interface.*
- `setup_event_handlers()`  *Setup event bus handlers (delegiert).*
- `update_prices()`  *Update prices in the table (delegiert).*
- `format_volume(volume)` → `str`  *Format volume for display (delegiert).*
- `add_symbol_from_input()`  *Add symbol from input field (delegiert).*
- `add_symbol(symbol_data, save)`  *Add symbol to watchlist (delegiert).*
- `remove_symbol(symbol)`  *Remove symbol from watchlist (delegiert).*
- `clear_watchlist()`  *Clear all symbols from watchlist (delegiert).*
- `add_indices()`  *Add major market indices (delegiert).*
- `add_tech_stocks()`  *Add major tech stocks (delegiert).*
- `add_crypto_pairs()`  *Add major cryptocurrency trading pairs (delegiert).*
- `on_symbol_double_clicked(item)`  *Handle symbol double-click (delegiert).*
- `show_context_menu(position)`  *Show context menu for table (delegiert).*
- `create_order(symbol)`  *Create order for symbol (delegiert).*
- `load_default_watchlist()`  *Load default watchlist on startup (delegiert).*
- `save_watchlist()`  *Save watchlist to settings (delegiert).*
- `save_column_state()`  *Save column widths and order to settings (delegiert).*
- `load_column_state()`  *Load column widths and order from settings (delegiert).*
- `get_symbols()` → `list[str]`  *Get list of watched symbols.*
- `closeEvent(event)`  *Handle widget close event - save column state.*
- `__init__(parent)`  *Initialize watchlist widget.*

## `src/ui/widgets/watchlist_events.py`

### `WatchlistEvents(object)`
*Helper for event handling.*

- `setup_event_handlers()`  *Setup event bus handlers.*
- async `on_market_tick(event)`  *Handle market tick events.*
- async `on_market_bar(event)`  *Handle market bar events.*
- `__init__(parent)`

## `src/ui/widgets/watchlist_interactions.py`

### `WatchlistInteractions(object)`
*Helper for user interactions.*

- `on_symbol_double_clicked(item)`  *Handle symbol double-click.*
- `show_context_menu(position)`  *Show context menu for table.*
- `create_order(symbol)`  *Create order for symbol.*
- `__init__(parent)`

## `src/ui/widgets/watchlist_persistence.py`

### `WatchlistPersistence(object)`
*Helper for save/load functionality.*

- `load_default_watchlist()`  *Load default watchlist on startup.*
- `save_watchlist()`  *Save watchlist to settings.*
- `save_column_state()`  *Save column widths and order to settings.*
- `load_column_state()`  *Load column widths and order from settings.*
- `__init__(parent)`

## `src/ui/widgets/watchlist_presets.py`

### `SymbolInfo(TypedDict)`
*Type definition for symbol information.*


### Module Functions
- `format_volume(volume)` → `str`  *Format volume for display.*

## `src/ui/widgets/watchlist_symbol_manager.py`

### `WatchlistSymbolManager(object)`
*Helper for symbol add/remove operations.*

- `add_symbol_from_input()`  *Add symbol from input field.*
- `add_symbol(symbol_data, save)`  *Add symbol to watchlist.*
- `remove_symbol(symbol)`  *Remove symbol from watchlist.*
- `clear_watchlist()`  *Clear all symbols from watchlist.*
- `add_indices()`  *Add major market indices.*
- `add_tech_stocks()`  *Add major tech stocks.*
- `add_crypto_pairs()`  *Add major cryptocurrency trading pairs.*
- *...1 private methods*
- `__init__(parent)`

## `src/ui/widgets/watchlist_table_updater.py`

### `WatchlistTableUpdater(object)`
*Helper for table price updates.*

- `update_prices()`  *Update prices in the table with market status.*
- `format_volume(volume)` → `str`  *Format volume for display. Delegates to module function.*
- *...5 private methods*
- `__init__(parent)`

## `src/ui/widgets/whatsapp_widget.py`

### `WhatsAppWidget(QWidget)`
*Widget für WhatsApp-Benachrichtigungen im Trading Bot.*

- `set_phone_number(phone)` → `None`  *Setzt die Telefonnummer.*
- `set_enabled(enabled)` → `None`  *Aktiviert/Deaktiviert Benachrichtigungen.*
- `is_enabled()` → `bool`  *Gibt zurück ob Benachrichtigungen aktiviert sind.*
- `get_service()`  *Gibt den WhatsApp-Service zurück.*
- `send_trade_notification(message)` → `bool`  *Sendet eine Trade-Benachrichtigung über das UI-Formular.*
- *...9 private methods*
- `__init__(parent)`

## `src/ui/widgets/widget_helpers.py`

### `EventBusWidget(QWidget)`
*Base widget with event bus integration.*

- `closeEvent(event)`  *Clean up event subscriptions on close.*
- *...2 private methods*
- `__init__(parent)`  *Initialize event bus widget.*

### `BaseTableWidget(EventBusWidget)`
*Base class for table-based widgets with common setup pattern.*

- `update_row(row, data)` → `None`  *Update a table row with data.*
- *...7 private methods*
- `__init__(parent)`  *Initialize base table widget.*

### Module Functions
- `create_table_widget(columns, stretch_columns, selection_behavior, selection_mode, editable, alternating_colors, sortable)` → `QTableWidget`  *Create a configured QTableWidget with common settings.*
- `setup_table_row(table, row, data, column_keys, format_funcs)` → `None`  *Set up a table row with data.*
- `create_vbox_layout(parent, spacing, margins)` → `QVBoxLayout`  *Create a QVBoxLayout with common settings.*
- `create_hbox_layout(parent, spacing, margins)` → `QHBoxLayout`  *Create a QHBoxLayout with common settings.*
- `create_grid_layout(parent, spacing, margins)` → `QGridLayout`  *Create a QGridLayout with common settings.*

## `src/ui/windows/cel_editor/icons.py`

### `MaterialIconLoader(object)`
*Loader for Google Material Design Icons.*

- `get_icon(category, name, variant, color, size, density)` → `QIcon`  *Load Material Design Icon.*
- `get_pixmap(category, name, variant, color, size, density, scaled_size)` → `QPixmap`  *Load Material Design Icon as QPixmap.*
- `list_available_icons(category)` → `list[str]`  *List all available icons in a category.*
- `list_categories()` → `list[str]`  *List all available icon categories.*
- *...1 private methods*
- `__init__(base_path)`  *Initialize icon loader.*

### `CelEditorIcons(object)`
*Pre-defined Material Icons for CEL Editor UI.*

- @property `new_file()` → `QIcon`
- @property `open_file()` → `QIcon`
- @property `save()` → `QIcon`
- @property `undo()` → `QIcon`
- @property `redo()` → `QIcon`
- @property `view_pattern()` → `QIcon`
- @property `view_code()` → `QIcon`
- @property `view_chart()` → `QIcon`
- @property `view_split()` → `QIcon`
- @property `add_candle()` → `QIcon`
- @property `delete_candle()` → `QIcon`
- @property `clear_all()` → `QIcon`
- @property `zoom_in()` → `QIcon`
- @property `zoom_out()` → `QIcon`
- @property `zoom_fit()` → `QIcon`
- @property `back()` → `QIcon`
- @property `ai_generate()` → `QIcon`
- @property `ai_suggest()` → `QIcon`
- @property `variables()` → `QIcon`
- @property `regime()` → `QIcon`
- @property `settings()` → `QIcon`
- @property `help()` → `QIcon`
- *...1 private methods*
- `__init__(loader)`  *Initialize with optional custom loader.*

## `src/ui/windows/cel_editor/main_window.py`

### `CelEditorWindow(CelEditorWindowUIMixin, CelEditorWindowEventsMixin, CelEditorWindowLogicMixin, QMainWindow)`
*Main window for CEL Editor - Interactive Pattern Builder.*

- `__init__(parent, strategy_name)`  *Initialize CEL Editor window.*

## `src/ui/windows/cel_editor/main_window_backup.py`

### `CelEditorWindow(QMainWindow)`
*Main window for CEL Editor - Interactive Pattern Builder.*

- `closeEvent(event)`  *Handle window close event.*
- *...61 private methods*
- `__init__(parent, strategy_name)`  *Initialize CEL Editor window.*

## `src/ui/windows/cel_editor/main_window_events.py`

### `CelEditorWindowEventsMixin(object)`
*Mixin for CEL Editor window event handlers.*

- `closeEvent(event)`  *Handle window close event.*
- *...44 private methods*

## `src/ui/windows/cel_editor/main_window_logic.py`

### `CelEditorWindowLogicMixin(object)`
*Mixin for CEL Editor window business logic.*

- *...8 private methods*

## `src/ui/windows/cel_editor/main_window_ui.py`

### `CelEditorWindowUIMixin(object)`
*Mixin for CEL Editor window UI setup methods.*

- *...9 private methods*

## `src/ui/windows/cel_editor/theme.py`

### Module Functions
- `get_qss_stylesheet()` → `str`  *Generate complete QSS stylesheet for CEL Editor.*

## `src/ui/workers/base_worker.py`

### `QABCMeta(type(QObject), ABCMeta)`
*Metaclass combining Qt's metaclass and Python's ABCMeta.*


### `BaseWorker(QObject)`
*Abstract base class for background workers.*

- `cancel()`  *Request cancellation of the worker.*
- `is_cancelled()` → `bool`  *Check if cancellation was requested.*
- `emit_cancellation_result(message)` → `None`  *Emit cancellation result with standard format.*
- `run()`  *Execute the worker in background thread.*
- *...1 private methods*
- `__init__()`  *Initialize base worker.*

### `WorkerThread(QThread)`
*Generic thread wrapper for BaseWorker instances.*

- `run()`  *Run the worker.*
- `__init__(worker)`  *Initialize thread wrapper.*

### `AsyncBaseWorker(BaseWorker)`
*Base worker with asyncio support.*

- `run()`  *Execute async worker with event loop management.*
- *...2 private methods*

## `src/ui/workers/historical_download_worker.py`

### `HistoricalDownloadWorker(AsyncBaseWorker)`
*Worker for downloading historical market data in background.*

- *...4 private methods*
- `__init__(provider_type, symbols, days, timeframe, mode, enable_bad_tick_filter, enable_ohlc_validation)`  *Initialize download worker.*

## `src/ui/workers/ohlc_validation_worker.py`

### `OHLCValidationWorker(BaseWorker)`
*Worker for validating and fixing OHLC data in background.*

- *...1 private methods*
- `__init__(symbol, dry_run)`  *Initialize validation worker.*