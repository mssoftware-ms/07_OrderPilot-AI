# Code-Inventur Bericht

**Erstellt:** 2025-12-14T15:00:23.487478

**Projekt:** /mnt/d/03_GIT/02_Python/07_OrderPilot-AI


## Übersicht

| Metrik | Wert |
|--------|------|
| Dateien | 141 |
| Gesamte Zeilen | 47,788 |
| Code-Zeilen | 35,878 |
| Funktionen | 1549 |
| Klassen | 325 |
| UI-Komponenten | 18 |
| Event-Handler | 139 |
| Imports | 1047 |

## Datei-Details

### examples/alpaca_realtime_demo.py

- **Zeilen:** 377 (Code: 281)
- **Checksum:** `7746a4f1b2d35e70457f85848e50bb5b`
- **Funktionen:** 12
- **Klassen:** 1

**Klassen:**
- `AlpacaDemo` (Zeile 44-302)
  - Methoden: __init__, setup, on_market_bar, on_market_tick, on_connected, on_disconnected, demo_broker_info, demo_realtime_streaming, demo_place_order, demo_historical_data... (+1)

**Top-Level Funktionen:**
- `async main()` (Zeile 305)

---

### examples/chart_state_persistence_demo.py

- **Zeilen:** 302 (Code: 214)
- **Checksum:** `3204cba2a044dc6bdde566cba0f610a3`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `ChartStateDemoWindow` (Zeile 34-260) 🖥️
  - Methoden: __init__, _setup_ui, _connect_signals, open_chart, create_demo_states, show_saved_states, clear_all_states, _on_state_saved, _on_state_loaded

**Top-Level Funktionen:**
- `main()` (Zeile 263)

---

### examples/realtime_indicators_demo.py

- **Zeilen:** 309 (Code: 226)
- **Checksum:** `f50d5265345cc964bfb9e221e9dc9700`
- **Funktionen:** 12
- **Klassen:** 1

**Klassen:**
- `RealtimeDemo` (Zeile 46-273)
  - Methoden: __init__, setup, on_market_tick, on_indicator_update, on_stream_connected, on_stream_disconnected, demo_historical_indicators, demo_realtime_indicators, demo_streaming, run_all_demos... (+1)

**Top-Level Funktionen:**
- `async main()` (Zeile 276)

---

### main.py

- **Zeilen:** 23 (Code: 15)
- **Checksum:** `bea6708d1d30e0579a2c5bf0196cbf1d`
- **Funktionen:** 0
- **Klassen:** 0

---

### refactoring_inventory.py

- **Zeilen:** 693 (Code: 555)
- **Checksum:** `99ff1d59973c03a2385c1954c6a40373`
- **Funktionen:** 22
- **Klassen:** 8

**Klassen:**
- `FunctionInfo` (Zeile 28-38)
- `ClassInfo` (Zeile 42-52)
- `ImportInfo` (Zeile 56-62)
- `EventHandlerInfo` (Zeile 66-72)
- `UIComponentInfo` (Zeile 76-85)
- `FileInventory` (Zeile 89-101)
- `ProjectInventory` (Zeile 105-117)
- `InventoryAnalyzer` (Zeile 120-407)
  - Methoden: __init__, get_decorator_names, _get_full_name, _get_signature, _get_docstring, _get_end_line, visit_FunctionDef, visit_AsyncFunctionDef, visit_ClassDef, visit_Import... (+3)

**Top-Level Funktionen:**
- `calculate_file_checksum(file_path: str) -> str` (Zeile 410)
- `count_code_lines(source_code: str) -> int` (Zeile 416)
- `analyze_file(file_path: str) -> Optional[FileInventory]` (Zeile 442)
- `find_python_files(root_dir: str, exclude_patterns: List[str]) -> List[str]` (Zeile 474)
- `create_inventory(project_root: str, output_file: str) -> ProjectInventory` (Zeile 490)
- `save_inventory(inventory: ProjectInventory, output_file: str)` (Zeile 543)
- `convert_to_dict(obj)` (Zeile 545)
- `print_summary(inventory: ProjectInventory)` (Zeile 566)
- `create_detailed_report(inventory: ProjectInventory, output_file: str)` (Zeile 610)

---

### run_app.py

- **Zeilen:** 19 (Code: 8)
- **Checksum:** `53f93a642d101c33e68ff53d480b2695`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/__init__.py

- **Zeilen:** 5 (Code: 4)
- **Checksum:** `3a2735f279c8978cff9511733cf4d7b7`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ai/__init__.py

- **Zeilen:** 87 (Code: 64)
- **Checksum:** `890e38404e8a8d5f2c94c19cdf8f3f19`
- **Funktionen:** 2
- **Klassen:** 0

**Top-Level Funktionen:**
- `async get_ai_service(telemetry_callback)` (Zeile 27)
- `reset_ai_service()` (Zeile 54)

---

### src/ai/ai_provider_factory.py

- **Zeilen:** 198 (Code: 145)
- **Checksum:** `6bcb8229aa5c7d6415c9367cf9c5c73a`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `AIProviderFactory` (Zeile 17-197)
  - Methoden: get_provider, is_ai_enabled, get_api_key, get_model, create_service, get_monthly_budget

---

### src/ai/anthropic_service.py

- **Zeilen:** 357 (Code: 259)
- **Checksum:** `f9920914ed6b52d502f7d7ebbc5abe94`
- **Funktionen:** 12
- **Klassen:** 1

**Klassen:**
- `AnthropicService` (Zeile 48-356)
  - Methoden: __init__, __aenter__, __aexit__, initialize, close, structured_completion, analyze_order, triage_alert, review_backtest, get_cost_summary... (+2)

---

### src/ai/openai_service.py

- **Zeilen:** 740 (Code: 542)
- **Checksum:** `8ccb357592dc8a57d62e0bbebcba6db6`
- **Funktionen:** 21
- **Klassen:** 11

**Klassen:**
- `OpenAIError` (Zeile 39-41)
- `RateLimitError` (Zeile 44-46)
- `QuotaExceededError` (Zeile 49-51)
- `SchemaValidationError` (Zeile 54-56)
- `OrderAnalysis` (Zeile 61-79)
- `AlertTriageResult` (Zeile 82-97)
- `BacktestReview` (Zeile 100-119)
- `StrategySignalAnalysis` (Zeile 122-137)
- `CostTracker` (Zeile 142-215)
  - Methoden: __init__, track_usage
- `CacheManager` (Zeile 220-298)
  - Methoden: __init__, _generate_key, get, set, _cleanup_expired
- `OpenAIService` (Zeile 303-713)
  - Methoden: __init__, __aenter__, __aexit__, initialize, close, structured_completion, analyze_order, triage_alert, review_backtest, analyze_signal... (+3)

**Top-Level Funktionen:**
- `async get_openai_service(config: AIConfig, api_key: str) -> OpenAIService` (Zeile 721)

---

### src/ai/prompts.py

- **Zeilen:** 563 (Code: 479)
- **Checksum:** `9a73cae4cf83dbc109b26854596be6b2`
- **Funktionen:** 11
- **Klassen:** 5

**Klassen:**
- `PromptTemplates` (Zeile 10-128)
- `JSONSchemas` (Zeile 133-383)
- `PromptBuilder` (Zeile 388-474)
  - Methoden: build_order_prompt, build_alert_prompt, build_backtest_prompt, build_signal_prompt, _format_dict
- `SchemaValidator` (Zeile 479-524)
  - Methoden: validate_order_analysis, validate_alert_triage, validate_backtest_review, validate_signal_analysis, _validate_against_schema
- `PromptVersion` (Zeile 529-563)
  - Methoden: get_prompt

---

### src/ai/providers.py

- **Zeilen:** 497 (Code: 384)
- **Checksum:** `3254e0007dde39db1a5dea5b81243dbe`
- **Funktionen:** 15
- **Klassen:** 6

**Klassen:**
- `AIProvider` (Zeile 25-28)
- `ReasoningMode` (Zeile 31-37)
- `ProviderConfig` (Zeile 40-49)
- `AIProviderBase` (Zeile 52-110)
  - Methoden: __init__, initialize, close, structured_completion, stream_completion
- `OpenAIProvider` (Zeile 113-250)
  - Methoden: __init__, structured_completion, stream_completion
- `AnthropicProvider` (Zeile 253-392)
  - Methoden: __init__, structured_completion, stream_completion

**Top-Level Funktionen:**
- `create_provider(provider: AIProvider, model: str, **kwargs) -> AIProviderBase` (Zeile 397)
- `async get_openai_gpt51_thinking(**kwargs) -> OpenAIProvider` (Zeile 449)
- `async get_openai_gpt51_instant(**kwargs) -> OpenAIProvider` (Zeile 466)
- `async get_anthropic_sonnet45(**kwargs) -> AnthropicProvider` (Zeile 483)

---

### src/backtesting/__init__.py

- **Zeilen:** 2 (Code: 1)
- **Checksum:** `1e4937aeb447e9c20c2ab9ad45e1500f`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/common/__init__.py

- **Zeilen:** 20 (Code: 17)
- **Checksum:** `8509ae449a8cc5b9f4f1563f598a6924`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/common/event_bus.py

- **Zeilen:** 257 (Code: 190)
- **Checksum:** `8f7735b59fc05ad27b71b310bd1d9c6a`
- **Funktionen:** 9
- **Klassen:** 5

**Klassen:**
- `EventType` (Zeile 21-84)
- `Event` (Zeile 88-94)
- `OrderEvent` (Zeile 98-119)
  - Methoden: __post_init__
- `ExecutionEvent` (Zeile 123-144)
  - Methoden: __post_init__
- `EventBus` (Zeile 147-247)
  - Methoden: __init__, get_signal, emit, subscribe, unsubscribe, get_history, clear_history

---

### src/common/logging_setup.py

- **Zeilen:** 293 (Code: 226)
- **Checksum:** `6088b7becc4ffab22fba3ef03a9efcc8`
- **Funktionen:** 10
- **Klassen:** 2

**Klassen:**
- `AITelemetryFilter` (Zeile 26-42)
  - Methoden: filter
- `TradingJsonFormatter` (Zeile 45-66)
  - Methoden: add_fields

**Top-Level Funktionen:**
- `configure_logging(level: str, log_dir: Path | None, enable_console: bool, enable_file: bool, enable_json: bool, max_bytes: int, backup_count: int) -> None` (Zeile 69)
- `configure_module_loggers()` (Zeile 163)
- `log_order_action(action: str, order_id: str, symbol: str, details: dict[str, Any], logger_name: str) -> None` (Zeile 176)
- `log_security_action(action: Any, user_id: str, session_id: str, ip_address: str, details: dict[str, Any], success: bool) -> None` (Zeile 202)
- `get_audit_logger() -> logging.Logger` (Zeile 238)
- `get_security_audit_logger() -> logging.Logger` (Zeile 243)
- `log_ai_request(model: str, tokens: int, cost: float, latency: float, prompt_version: str, request_type: str, details: dict[str, Any] | None) -> None` (Zeile 248)
- `get_logger(name: str) -> logging.Logger` (Zeile 283)

---

### src/common/performance.py

- **Zeilen:** 272 (Code: 209)
- **Checksum:** `717c609c023047ec362e809b837e3147`
- **Funktionen:** 21
- **Klassen:** 2

**Klassen:**
- `PerformanceMonitor` (Zeile 17-135)
  - Methoden: __init__, record_latency, increment_counter, get_stats, get_all_stats, reset, measure, report
- `PerformanceTimer` (Zeile 228-271)
  - Methoden: __init__, start, stop, __enter__, __exit__

**Top-Level Funktionen:**
- `monitor_performance(operation: str | None)` (Zeile 142)
- `decorator(func: Callable) -> Callable` (Zeile 153)
- `async async_wrapper(*args, **kwargs) -> Any` (Zeile 157)
- `sync_wrapper(*args, **kwargs) -> Any` (Zeile 162)
- `log_performance(operation: str, threshold_ms: float) -> Callable` (Zeile 176)
- `decorator(func: Callable) -> Callable` (Zeile 188)
- `async async_wrapper(*args, **kwargs) -> Any` (Zeile 190)
- `sync_wrapper(*args, **kwargs) -> Any` (Zeile 205)

---

### src/common/security.py

- **Zeilen:** 99 (Code: 75)
- **Checksum:** `4272c0bd7f2d5b1b0080b375f2504344`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `audit_action(action, context, details, success)` (Zeile 49)

---

### src/common/security_core.py

- **Zeilen:** 253 (Code: 181)
- **Checksum:** `2fe6c514bff3b6afa8c60cd84ba8c1bd`
- **Funktionen:** 13
- **Klassen:** 4

**Klassen:**
- `SecurityLevel` (Zeile 22-27)
- `SecurityAction` (Zeile 30-43)
- `SecurityContext` (Zeile 47-60)
  - Methoden: __post_init__
- `RateLimiter` (Zeile 63-111)
  - Methoden: __init__, is_allowed, get_remaining

**Top-Level Funktionen:**
- `hash_password(password: str, salt: Optional[str]) -> tuple[str, str]` (Zeile 114)
- `verify_password(password: str, stored_hash: str, salt: str) -> bool` (Zeile 138)
- `generate_api_key() -> str` (Zeile 153)
- `validate_api_key(api_key: str) -> bool` (Zeile 162)
- `rate_limit(key: str, max_requests: int, window_seconds: int) -> Callable` (Zeile 187)
- `decorator(func)` (Zeile 200)
- `wrapper(*args, **kwargs)` (Zeile 201)
- `is_strong_password(password: str) -> bool` (Zeile 214)
- `sanitize_input(value: str, max_length: int) -> str` (Zeile 234)

---

### src/common/security_manager.py

- **Zeilen:** 425 (Code: 308)
- **Checksum:** `48b5a04c806a873bda5e42720764a43a`
- **Funktionen:** 21
- **Klassen:** 3

**Klassen:**
- `EncryptionManager` (Zeile 37-162)
  - Methoden: __init__, _initialize_encryption, encrypt, decrypt, encrypt_dict, decrypt_dict, rotate_key
- `CredentialManager` (Zeile 165-326)
  - Methoden: __init__, store_credential, retrieve_credential, delete_credential, _get_credential_file, _load_credentials_file, _save_credentials_file
- `SessionManager` (Zeile 329-392)
  - Methoden: __init__, create_session, validate_session, terminate_session

**Top-Level Funktionen:**
- `require_auth(security_level: SecurityLevel)` (Zeile 397)
- `decorator(func)` (Zeile 403)
- `wrapper(*args, **kwargs)` (Zeile 405)

---

### src/config/__init__.py

- **Zeilen:** 49 (Code: 42)
- **Checksum:** `5abbc0ba52aa1e72e4447996d0813127`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/config/loader.py

- **Zeilen:** 696 (Code: 567)
- **Checksum:** `f1a9b32d5534dfaeea75281fe57be36a`
- **Funktionen:** 18
- **Klassen:** 16

**Klassen:**
- `TradingEnvironment` (Zeile 24-28)
- `TradingMode` (Zeile 31-40)
- `BrokerType` (Zeile 43-51)
- `BrokerConfig` (Zeile 56-67)
- `DatabaseConfig` (Zeile 70-83)
- `MarketDataProviderConfig` (Zeile 86-92)
- `AIConfig` (Zeile 95-112)
- `TradingConfig` (Zeile 115-129)
- `BacktestConfig` (Zeile 132-143)
- `AlertConfig` (Zeile 146-161)
- `UIConfig` (Zeile 164-179)
- `MonitoringConfig` (Zeile 182-194)
- `ExecutionConfig` (Zeile 197-211)
- `ProfileConfig` (Zeile 214-470)
  - Methoden: validate_environment, validate_trading_mode_field, validate_trading_mode_config, is_safe_for_mode, switch_to_mode, create_backtest_profile, create_paper_profile, create_live_profile
- `AppSettings` (Zeile 473-486)
- `ConfigManager` (Zeile 489-691)
  - Methoden: __init__, load_profile, save_profile, get_credential, set_credential, list_profiles, export_config, save_watchlist, load_watchlist, profile

---

### src/core/__init__.py

- **Zeilen:** 10 (Code: 8)
- **Checksum:** `231f4ff3c84a885079e3edd3976f6f26`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/alerts/__init__.py

- **Zeilen:** 2 (Code: 1)
- **Checksum:** `1e4937aeb447e9c20c2ab9ad45e1500f`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/backtesting/__init__.py

- **Zeilen:** 43 (Code: 30)
- **Checksum:** `49c2b3b82640d90abb7d1e90f6c97a22`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/backtesting/backtrader_integration.py

- **Zeilen:** 842 (Code: 641)
- **Checksum:** `d9fbaf573c30d2d15a7e6f894e064024`
- **Funktionen:** 17
- **Klassen:** 4

**Klassen:**
- `BacktestConfig` (Zeile 40-57)
  - Methoden: __post_init__
- `BacktestResultLegacy` (Zeile 61-83)
- `OrderPilotStrategy` (Zeile 86-289)
  - Methoden: __init__, notify_order, notify_trade, next, _get_dataframe, _execute_signal, _calculate_size, log
- `BacktestEngine` (Zeile 292-842)
  - Methoden: __init__, run_backtest, _get_data_feed, _process_results, run_backtest_with_definition, optimize_strategy, _generate_param_combinations, plot_results

---

### src/core/backtesting/optimization.py

- **Zeilen:** 626 (Code: 452)
- **Checksum:** `4d20fe9890b4f21432d0331973a4c3aa`
- **Funktionen:** 11
- **Klassen:** 7

**Klassen:**
- `ParameterRange` (Zeile 26-30)
- `OptimizationMetric` (Zeile 33-37)
- `ParameterTest` (Zeile 40-46)
- `OptimizationResult` (Zeile 49-61)
- `AIOptimizationInsight` (Zeile 64-84)
- `OptimizerConfig` (Zeile 90-106)
- `ParameterOptimizer` (Zeile 109-581)
  - Methoden: __init__, grid_search, optimize_with_ai, _calculate_score, _get_metric_value, _extract_metrics, _analyze_sensitivity, _get_ai_insights, _build_optimization_prompt, _refine_ranges

**Top-Level Funktionen:**
- `async quick_optimize(backtest_runner: Callable, parameter_ranges: dict[str, list[Any]], base_params: dict[str, Any] | None, primary_metric: str) -> OptimizationResult` (Zeile 586)

---

### src/core/backtesting/result_converter.py

- **Zeilen:** 471 (Code: 324)
- **Checksum:** `dcd82e6fcd53b27b41d649c251060be7`
- **Funktionen:** 7
- **Klassen:** 0

**Top-Level Funktionen:**
- `backtrader_to_backtest_result(strategy, cerebro, initial_value: float, final_value: float, symbol: str, timeframe: str, start_date: datetime, end_date: datetime, strategy_name: str | None, strategy_params: dict | None) -> BacktestResult` (Zeile 34)
- `_extract_bars_from_strategy(strategy, symbol: str) -> list[Bar]` (Zeile 126)
- `_extract_trades_from_strategy(strategy, symbol: str) -> list[Trade]` (Zeile 175)
- `_extract_equity_curve(strategy, initial_value: float) -> list[EquityPoint]` (Zeile 238)
- `_calculate_metrics(trades: list[Trade], equity_curve: list[EquityPoint], initial_capital: float, final_capital: float, start_date: datetime, end_date: datetime, strategy_analyzers) -> BacktestMetrics` (Zeile 285)
- `_calculate_max_consecutive(trades: list[Trade], is_winner: bool) -> int` (Zeile 421)
- `_extract_indicators(strategy) -> dict[str, list[tuple[datetime, float]]]` (Zeile 447)

---

### src/core/broker/__init__.py

- **Zeilen:** 43 (Code: 35)
- **Checksum:** `4d4c2f2d7632bee19c8d53b9bdfe0af9`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/broker/alpaca_adapter.py

- **Zeilen:** 494 (Code: 402)
- **Checksum:** `5141ff0ef1cdc520b3fa0c8f2d17446d`
- **Funktionen:** 14
- **Klassen:** 1

**Klassen:**
- `AlpacaAdapter` (Zeile 40-493)
  - Methoden: __init__, _establish_connection, _verify_connection, _cleanup_resources, is_connected, _map_order_side, _map_time_in_force, _map_order_status, _place_order_impl, cancel_order... (+4)

---

### src/core/broker/base.py

- **Zeilen:** 671 (Code: 452)
- **Checksum:** `0d88f0ec9d2b6a31d9f63a17a9b17f5a`
- **Funktionen:** 32
- **Klassen:** 14

**Klassen:**
- `BrokerError` (Zeile 25-31)
  - Methoden: __init__
- `BrokerConnectionError` (Zeile 34-36)
- `OrderValidationError` (Zeile 39-41)
- `InsufficientFundsError` (Zeile 44-46)
- `RateLimitError` (Zeile 49-51)
- `OrderRequest` (Zeile 54-99)
  - Methoden: validate_limit_price, validate_stop_price
- `OrderResponse` (Zeile 102-129)
- `Position` (Zeile 132-157)
  - Methoden: is_long, is_short
- `Balance` (Zeile 160-181)
- `FeeModel` (Zeile 184-215)
  - Methoden: calculate
- `AIAnalysisRequest` (Zeile 220-242)
- `AIAnalysisResult` (Zeile 245-271)
- `TokenBucketRateLimiter` (Zeile 276-317)
  - Methoden: __init__, acquire, try_acquire
- `BrokerAdapter` (Zeile 322-671)
  - Methoden: __init__, connect, disconnect, is_connected, _validate_credentials, _establish_connection, _verify_connection, _setup_initial_state, _cleanup_resources, _ensure_connected... (+13)

---

### src/core/broker/ibkr_adapter.py

- **Zeilen:** 524 (Code: 394)
- **Checksum:** `26fca7e7663edc1667fe0522f60a616d`
- **Funktionen:** 27
- **Klassen:** 3

**Klassen:**
- `IBKRWrapper` (Zeile 35-145)
  - Methoden: __init__, nextValidId, connectionClosed, error, orderStatus, position, accountSummary, historicalData, tickPrice, _map_order_status
- `IBKRClient` (Zeile 148-152)
  - Methoden: __init__
- `IBKRAdapter` (Zeile 155-524)
  - Methoden: __init__, _get_next_req_id, _establish_connection, _verify_connection, _setup_initial_state, _cleanup_resources, is_connected, _place_order_impl, _create_contract, _create_ib_order... (+6)

---

### src/core/broker/mock_broker.py

- **Zeilen:** 300 (Code: 234)
- **Checksum:** `8afa4c52882f1912401980b30c9799c9`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `MockBroker` (Zeile 30-300)
  - Methoden: __init__, _establish_connection, _cleanup_resources, _place_order_impl, _simulate_fill, _update_position, cancel_order, get_order_status, get_positions, get_balance... (+3)

---

### src/core/broker/trade_republic_adapter.py

- **Zeilen:** 488 (Code: 384)
- **Checksum:** `64a60b2dad9f07b32aaf7379e1b6dd97`
- **Funktionen:** 23
- **Klassen:** 1

**Klassen:**
- `TradeRepublicAdapter` (Zeile 36-488)
  - Methoden: __init__, _establish_connection, _setup_initial_state, _authenticate, _connect_websocket, _listen_websocket, _handle_ws_message, _heartbeat_loop, _reconnect, _cleanup_resources... (+13)

---

### src/core/execution/__init__.py

- **Zeilen:** 18 (Code: 14)
- **Checksum:** `ea1d995e4d0a1b2d4cb568dcc7ce65f8`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/execution/engine.py

- **Zeilen:** 576 (Code: 444)
- **Checksum:** `d66be18e5f080ced5cf8c1e6595effd0`
- **Funktionen:** 17
- **Klassen:** 3

**Klassen:**
- `ExecutionState` (Zeile 26-32)
- `ExecutionTask` (Zeile 36-53)
  - Methoden: __post_init__
- `ExecutionEngine` (Zeile 56-576)
  - Methoden: __init__, start, stop, pause, resume, activate_kill_switch, deactivate_kill_switch, submit_order, _process_queue, _execute_task... (+6)

---

### src/core/execution/events.py

- **Zeilen:** 459 (Code: 407)
- **Checksum:** `ef0844d355f11c5617e5e62404adf26d`
- **Funktionen:** 22
- **Klassen:** 3

**Klassen:**
- `OrderEventEmitter` (Zeile 24-161)
  - Methoden: __init__, emit_order_created, emit_order_submitted, emit_order_filled, emit_order_partial_fill, emit_order_cancelled, emit_order_rejected
- `ExecutionEventEmitter` (Zeile 164-350)
  - Methoden: __init__, emit_trade_entry, emit_trade_exit, emit_stop_loss_hit, emit_take_profit_hit, emit_position_opened, emit_position_closed
- `BacktraderEventAdapter` (Zeile 353-458)
  - Methoden: __init__, on_order_created, on_order_submitted, on_order_filled, on_order_cancelled, on_order_rejected, _get_order_type, _get_order_side

---

### src/core/indicators/__init__.py

- **Zeilen:** 42 (Code: 30)
- **Checksum:** `8db61eb4305abe42bad4e69288672002`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/indicators/base.py

- **Zeilen:** 102 (Code: 73)
- **Checksum:** `92a4e61d219306d2ca9cfbe72ed3832f`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `BaseIndicatorCalculator` (Zeile 34-85)
  - Methoden: validate_data, create_result

---

### src/core/indicators/custom.py

- **Zeilen:** 159 (Code: 126)
- **Checksum:** `e897bab5cce326379e0325bdd59be6e8`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `CustomIndicators` (Zeile 21-158)
  - Methoden: calculate_pivots, calculate_support_resistance, calculate_patterns

---

### src/core/indicators/engine.py

- **Zeilen:** 169 (Code: 123)
- **Checksum:** `fdcccce5cf150fa9b4b22c4dc2eb29e8`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `IndicatorEngine` (Zeile 26-168)
  - Methoden: __init__, calculate, calculate_multiple, _get_cache_key, clear_cache

---

### src/core/indicators/momentum.py

- **Zeilen:** 220 (Code: 180)
- **Checksum:** `cef11ecbd79790c1061dbcb03dbc1e6a`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `MomentumIndicators` (Zeile 24-219)
  - Methoden: calculate_rsi, calculate_stoch, calculate_mom, calculate_roc, calculate_willr, calculate_cci, calculate_mfi

---

### src/core/indicators/trend.py

- **Zeilen:** 260 (Code: 215)
- **Checksum:** `51e4fd0eb93abacaafa4d41114479203`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `TrendIndicators` (Zeile 24-259)
  - Methoden: calculate_sma, calculate_ema, calculate_wma, calculate_vwma, calculate_macd, calculate_adx, calculate_psar, calculate_ichimoku

---

### src/core/indicators/types.py

- **Zeilen:** 73 (Code: 54)
- **Checksum:** `8bf322c2c99b161dd662852fa9840a17`
- **Funktionen:** 0
- **Klassen:** 3

**Klassen:**
- `IndicatorType` (Zeile 14-52)
- `IndicatorConfig` (Zeile 56-62)
- `IndicatorResult` (Zeile 66-72)

---

### src/core/indicators/volatility.py

- **Zeilen:** 174 (Code: 140)
- **Checksum:** `14422ac4160b843724a0e92191e6802a`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `VolatilityIndicators` (Zeile 24-173)
  - Methoden: calculate_bb, calculate_kc, calculate_atr, calculate_natr, calculate_std

---

### src/core/indicators/volume.py

- **Zeilen:** 152 (Code: 122)
- **Checksum:** `d7b5f820e3eba058d7911240a917d935`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `VolumeIndicators` (Zeile 23-151)
  - Methoden: calculate_obv, calculate_cmf, calculate_ad, calculate_fi, calculate_vwap

---

### src/core/market_data/__init__.py

- **Zeilen:** 38 (Code: 31)
- **Checksum:** `9cf21e58ea08617be482db3d7be053ac`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/market_data/alpaca_crypto_provider.py

- **Zeilen:** 190 (Code: 146)
- **Checksum:** `89ca675a12845bbcd9b7848d0b3cdabb`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `AlpacaCryptoProvider` (Zeile 20-189)
  - Methoden: __init__, fetch_bars, is_available, _ensure_utc_naive, _timeframe_to_alpaca, _check_sdk

---

### src/core/market_data/alpaca_crypto_stream.py

- **Zeilen:** 392 (Code: 298)
- **Checksum:** `056e88eb9dc161777d7adfe7efd65801`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `AlpacaCryptoStreamClient` (Zeile 21-391)
  - Methoden: __init__, connect, _run_stream, disconnect, subscribe, unsubscribe, _on_bar, _on_trade, _on_quote, get_latest_tick... (+1)

---

### src/core/market_data/alpaca_stream.py

- **Zeilen:** 407 (Code: 309)
- **Checksum:** `aa0667455753d7adfa3f338e529a43bb`
- **Funktionen:** 12
- **Klassen:** 1

**Klassen:**
- `AlpacaStreamClient` (Zeile 24-406)
  - Methoden: __init__, connect, _run_stream, disconnect, subscribe, unsubscribe, _on_bar, _on_trade, _on_quote, get_latest_tick... (+2)

---

### src/core/market_data/alpha_vantage_stream.py

- **Zeilen:** 427 (Code: 322)
- **Checksum:** `a17b59ca75021ef5132bd72141010480`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `AlphaVantageStreamClient` (Zeile 21-426)
  - Methoden: __init__, connect, disconnect, subscribe, unsubscribe, _poll_loop, _poll_symbol, _fetch_global_quote, _fetch_indicators, _fetch_rsi... (+3)

---

### src/core/market_data/base_provider.py

- **Zeilen:** 245 (Code: 189)
- **Checksum:** `87c3cbc2846b2f7144d4fdcf466d4f7d`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `HistoricalDataProvider` (Zeile 18-244)
  - Methoden: __init__, fetch_bars, is_available, fetch_bars_with_cache, _fetch_data_from_source, _cache_key, _df_to_bars, _to_unix_timestamp, _clamp_date_range

---

### src/core/market_data/history_provider.py

- **Zeilen:** 1893 (Code: 1503)
- **Checksum:** `047affcc5d65396e1951cbf8c94fb3b6`
- **Funktionen:** 60
- **Klassen:** 8

**Klassen:**
- `HistoricalDataProvider` (Zeile 29-255)
  - Methoden: __init__, fetch_bars, is_available, fetch_bars_with_cache, _fetch_data_from_source, _cache_key, _df_to_bars, _to_unix_timestamp, _clamp_date_range
- `IBKRHistoricalProvider` (Zeile 258-416)
  - Methoden: __init__, fetch_bars, is_available, _calculate_duration, _timeframe_to_ibkr, _df_to_bars
- `AlphaVantageProvider` (Zeile 419-724)
  - Methoden: __init__, fetch_bars, is_available, _timeframe_to_av, _df_to_bars, fetch_technical_indicator, fetch_rsi, fetch_macd
- `YahooFinanceProvider` (Zeile 727-971)
  - Methoden: __init__, fetch_bars, is_available, _timeframe_to_yahoo, _df_to_bars, _to_unix, _clamp_date_range, _get_lookback_limit
- `FinnhubProvider` (Zeile 974-1081)
  - Methoden: __init__, fetch_bars, is_available, _timeframe_to_finnhub
- `AlpacaProvider` (Zeile 1084-1229)
  - Methoden: __init__, fetch_bars, is_available, _timeframe_to_alpaca, _check_sdk
- `DatabaseProvider` (Zeile 1232-1346)
  - Methoden: __init__, fetch_bars, is_available, _resample_bars
- `HistoryManager` (Zeile 1349-1892)
  - Methoden: __init__, register_provider, set_ibkr_adapter, _configure_priority, _initialize_providers_from_config, fetch_data, _store_to_database, get_latest_price, get_available_sources, start_realtime_stream... (+6)

---

### src/core/market_data/resampler.py

- **Zeilen:** 483 (Code: 340)
- **Checksum:** `284ee025237f121a0968472c62b31868`
- **Funktionen:** 17
- **Klassen:** 6

**Klassen:**
- `OHLCV` (Zeile 21-30)
- `NoiseFilter` (Zeile 33-45)
  - Methoden: filter
- `MedianFilter` (Zeile 48-82)
  - Methoden: __init__, filter
- `MovingAverageFilter` (Zeile 85-120)
  - Methoden: __init__, filter
- `KalmanFilter` (Zeile 123-168)
  - Methoden: __init__, filter
- `MarketDataResampler` (Zeile 171-483)
  - Methoden: __init__, add_tick, _get_bar_time, _create_bar, _emit_bar_event, get_bars, get_latest_bar, resample_dataframe, detect_anomalies, get_statistics

---

### src/core/market_data/stream_client.py

- **Zeilen:** 528 (Code: 397)
- **Checksum:** `8ab5b4fc97f41c741245e6a2bfc9b121`
- **Funktionen:** 29
- **Klassen:** 6

**Klassen:**
- `StreamStatus` (Zeile 24-30)
- `StreamMetrics` (Zeile 34-55)
  - Methoden: update_latency
- `MarketTick` (Zeile 59-68)
- `StreamClient` (Zeile 71-394)
  - Methoden: __init__, connect, disconnect, subscribe, unsubscribe, _handle_subscription, _handle_unsubscription, process_tick, _safe_callback, _heartbeat_loop... (+8)
- `IBKRStreamClient` (Zeile 397-452)
  - Methoden: __init__, connect, _handle_subscription, _get_next_req_id
- `TradeRepublicStreamClient` (Zeile 455-528)
  - Methoden: __init__, connect, _listen, _handle_message, _handle_subscription, _send_heartbeat

---

### src/core/market_data/types.py

- **Zeilen:** 72 (Code: 59)
- **Checksum:** `198008bb2f7a2a82e9dd58bf27734397`
- **Funktionen:** 0
- **Klassen:** 5

**Klassen:**
- `AssetClass` (Zeile 12-17)
- `DataSource` (Zeile 20-28)
- `Timeframe` (Zeile 31-44)
- `HistoricalBar` (Zeile 48-58)
- `DataRequest` (Zeile 62-71)

---

### src/core/models/__init__.py

- **Zeilen:** 23 (Code: 19)
- **Checksum:** `205b457dd64450be2342cbcccafcd774`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/models/backtest_models.py

- **Zeilen:** 294 (Code: 209)
- **Checksum:** `7091c8186b8cf9b22f5d7147a544628f`
- **Funktionen:** 9
- **Klassen:** 10

**Klassen:**
- `TradeSide` (Zeile 16-19)
- `Bar` (Zeile 22-39)
- `Config` (Zeile 35-39)
- `Trade` (Zeile 42-110)
  - Methoden: duration, r_multiple, is_winner
- `Config` (Zeile 106-110)
- `EquityPoint` (Zeile 113-124)
- `Config` (Zeile 121-124)
- `BacktestMetrics` (Zeile 127-175)
  - Methoden: recovery_factor
- `BacktestResult` (Zeile 178-241)
  - Methoden: duration_days, total_pnl, total_pnl_pct
- `Config` (Zeile 237-241)

**Top-Level Funktionen:**
- `from_historical_bar(bar: 'HistoricalBar', symbol: str | None) -> Bar` (Zeile 246)
- `to_historical_bars(bars: list[Bar], symbol: str) -> list['HistoricalBar']` (Zeile 269)

---

### src/core/strategy/__init__.py

- **Zeilen:** 44 (Code: 36)
- **Checksum:** `cc3d55537af7acfaa25dbf7f6cc250ef`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/strategy/compiled_strategy.py

- **Zeilen:** 238 (Code: 177)
- **Checksum:** `a0765904642c4954e8dc7e8337b1c698`
- **Funktionen:** 15
- **Klassen:** 1

**Klassen:**
- `CompiledStrategy` (Zeile 19-238)
  - Methoden: __init__, _setup_indicators, _setup_evaluators, _setup_risk_management, next, _check_entry_signals, _check_exit_signals, _enter_long, _enter_short, _exit_position... (+5)

---

### src/core/strategy/compiler.py

- **Zeilen:** 521 (Code: 359)
- **Checksum:** `5219f93d315f4463259941ebf4284751`
- **Funktionen:** 12
- **Klassen:** 5

**Klassen:**
- `CompilationError` (Zeile 42-44)
- `IndicatorFactory` (Zeile 47-211)
  - Methoden: create_indicator, _normalize_params
- `ConditionEvaluator` (Zeile 214-447)
  - Methoden: __init__, evaluate, _evaluate_condition, _evaluate_logic_group, _resolve_operand, _check_cross_above, _check_cross_below
- `StrategyCompiler` (Zeile 450-520)
  - Methoden: compile, _create_strategy_class
- `DynamicCompiledStrategy` (Zeile 509-514)
  - Methoden: __init__

---

### src/core/strategy/definition.py

- **Zeilen:** 503 (Code: 385)
- **Checksum:** `dc0234899d30f1726ab6dcb9cb160381`
- **Funktionen:** 15
- **Klassen:** 11

**Klassen:**
- `IndicatorType` (Zeile 35-73)
- `ComparisonOperator` (Zeile 76-91)
- `LogicOperator` (Zeile 94-99)
- `IndicatorConfig` (Zeile 102-140)
  - Methoden: validate_alias
- `Config` (Zeile 137-140)
- `Condition` (Zeile 143-182)
  - Methoden: validate_range_operators
- `Config` (Zeile 179-182)
- `LogicGroup` (Zeile 193-245)
  - Methoden: validate_conditions_not_empty, validate_not_operator
- `Config` (Zeile 242-245)
- `RiskManagement` (Zeile 258-319)
  - Methoden: validate_stop_loss_methods, validate_take_profit_methods
- `StrategyDefinition` (Zeile 322-498)
  - Methoden: validate_unique_aliases, validate_condition_references, get_indicator_by_alias, to_yaml, from_yaml, to_json_file, from_json_file

**Top-Level Funktionen:**
- `_get_condition_type(v: Any) -> str` (Zeile 186)

---

### src/core/strategy/engine.py

- **Zeilen:** 957 (Code: 745)
- **Checksum:** `901fe69fee7066a31b46058667558d87`
- **Funktionen:** 19
- **Klassen:** 12

**Klassen:**
- `SignalType` (Zeile 26-32)
- `StrategyType` (Zeile 35-45)
- `Signal` (Zeile 49-61)
- `StrategyConfig` (Zeile 65-76)
- `StrategyState` (Zeile 80-87)
- `BaseStrategy` (Zeile 90-205)
  - Methoden: __init__, evaluate, update_position, get_position, has_position, calculate_position_size
- `TrendFollowingStrategy` (Zeile 208-318)
  - Methoden: evaluate
- `MeanReversionStrategy` (Zeile 321-429)
  - Methoden: evaluate
- `MomentumStrategy` (Zeile 432-523)
  - Methoden: evaluate
- `BreakoutStrategy` (Zeile 526-616)
  - Methoden: evaluate
- `ScalpingStrategy` (Zeile 619-714)
  - Methoden: evaluate
- `StrategyEngine` (Zeile 717-957)
  - Methoden: __init__, create_strategy, enable_strategy, disable_strategy, evaluate_all, combine_signals, get_strategy_stats, signal_to_order

---

### src/core/strategy/evaluation.py

- **Zeilen:** 239 (Code: 185)
- **Checksum:** `9157d7d8a133327d1b3974d8c8bbb01d`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `ConditionEvaluator` (Zeile 21-239)
  - Methoden: __init__, evaluate, _evaluate_comparison, _apply_comparison_operator, _evaluate_logic_group, _resolve_operand, _is_numeric_string, _resolve_data_field, _resolve_indicator, _check_cross_above... (+3)

---

### src/core/strategy/loader.py

- **Zeilen:** 166 (Code: 120)
- **Checksum:** `23343cadc6901f7a674dc510891a125c`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `StrategyLoader` (Zeile 17-149)
  - Methoden: __init__, discover_strategies, load_strategy, load_all_strategies, get_strategy_info

**Top-Level Funktionen:**
- `get_strategy_loader() -> StrategyLoader` (Zeile 156)

---

### src/database/__init__.py

- **Zeilen:** 47 (Code: 43)
- **Checksum:** `78882ebac12a8a6d04e1e8d7eab9a633`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/database/database.py

- **Zeilen:** 312 (Code: 235)
- **Checksum:** `458778eee45fb6171a53a317ddd9350e`
- **Funktionen:** 16
- **Klassen:** 1

**Klassen:**
- `DatabaseManager` (Zeile 24-279)
  - Methoden: __init__, initialize, create_tables, _create_timescale_hypertables, drop_tables, session, get_session, execute_raw, backup, vacuum... (+3)

**Top-Level Funktionen:**
- `initialize_database(config: DatabaseConfig) -> DatabaseManager` (Zeile 286)
- `get_db_manager() -> DatabaseManager` (Zeile 301)

---

### src/database/models.py

- **Zeilen:** 508 (Code: 328)
- **Checksum:** `d02b2667d36e5df07d188a2444143bf4`
- **Funktionen:** 0
- **Klassen:** 16

**Klassen:**
- `OrderStatus` (Zeile 30-38)
- `OrderSide` (Zeile 41-44)
- `OrderType` (Zeile 47-52)
- `TimeInForce` (Zeile 55-60)
- `AlertPriority` (Zeile 63-68)
- `MarketBar` (Zeile 71-99)
- `Order` (Zeile 102-157)
- `Execution` (Zeile 160-192)
- `Position` (Zeile 195-225)
- `Alert` (Zeile 228-267)
- `Strategy` (Zeile 270-299)
- `BacktestResult` (Zeile 302-355)
- `AITelemetry` (Zeile 358-401)
- `AICache` (Zeile 404-429)
- `AuditLog` (Zeile 432-469)
- `SystemMetrics` (Zeile 472-508)

---

### src/ui/__init__.py

- **Zeilen:** 2 (Code: 1)
- **Checksum:** `1e4937aeb447e9c20c2ab9ad45e1500f`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/app.py

- **Zeilen:** 1479 (Code: 1058)
- **Checksum:** `b95f580a8ede7929f7e70b0a4ef1fc5e`
- **Funktionen:** 44
- **Klassen:** 1

**Klassen:**
- `TradingApplication` (Zeile 71-1447) 🖥️
  - Methoden: __init__, init_ui, create_menu_bar, create_toolbar, create_central_widget, create_dock_widgets, create_status_bar, setup_event_handlers, setup_timers, initialize_services... (+33)

**Top-Level Funktionen:**
- `async main()` (Zeile 1450)

---

### src/ui/chart/__init__.py

- **Zeilen:** 14 (Code: 10)
- **Checksum:** `2020d310644d7fdffa9810b7a49e9163`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/chart/chart_adapter.py

- **Zeilen:** 457 (Code: 346)
- **Checksum:** `9e7c40937deb9c674e583f94ee9fa0d6`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `ChartAdapter` (Zeile 17-456)
  - Methoden: backtest_result_to_chart_data, bars_to_candlesticks, equity_to_line_series, build_markers_from_trades, _build_entry_marker, _build_exit_marker, _build_sl_tp_marker, indicators_to_series, _format_time, to_json... (+1)

---

### src/ui/chart/chart_bridge.py

- **Zeilen:** 384 (Code: 281)
- **Checksum:** `4bfa940d942d5e7fd7e9a0d54feada7f`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `ChartBridge` (Zeile 19-383)
  - Methoden: __init__, loadBacktestResult, loadBacktestResultObject, loadLiveData, updateTrade, getCurrentSymbol, getMetricsSummary, clearChart, toggleMarkers, toggleIndicator... (+1)

---

### src/ui/chart_window_manager.py

- **Zeilen:** 218 (Code: 150)
- **Checksum:** `568ff2cd39f7fda05cdd4995d70ced66`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `ChartWindowManager` (Zeile 16-188)
  - Methoden: __init__, open_or_focus_chart, _on_window_closed, close_window, close_all_windows, get_open_symbols, has_open_window, get_active_symbol, open_chart, close_all_charts

**Top-Level Funktionen:**
- `get_chart_window_manager(history_manager, parent) -> ChartWindowManager` (Zeile 195)

---

### src/ui/dialogs/__init__.py

- **Zeilen:** 15 (Code: 13)
- **Checksum:** `e06f1eafbebe43236e17ab6e7566a95d`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/dialogs/ai_backtest_dialog.py

- **Zeilen:** 603 (Code: 423)
- **Checksum:** `3d05ff3aeb0d5802f35ae504cabc9619`
- **Funktionen:** 17
- **Klassen:** 1

**Klassen:**
- `AIBacktestDialog` (Zeile 37-602) 🖥️
  - Methoden: __init__, init_ui, _create_config_tab, _create_results_tab, _create_ai_tab, _create_chart_tab, run_backtest, _create_mock_result, _display_results, run_ai_review... (+7)

---

### src/ui/dialogs/backtest_dialog.py

- **Zeilen:** 258 (Code: 192)
- **Checksum:** `080e0dfe34662d2e6ab2ac2ef5428243`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `BacktestDialog` (Zeile 22-257) 🖥️
  - Methoden: __init__, init_ui, run_backtest, _run_backtest_simulation, export_results

---

### src/ui/dialogs/order_dialog.py

- **Zeilen:** 286 (Code: 211)
- **Checksum:** `431aae63205cfdbaee0e885dcc9ad710`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `OrderDialog` (Zeile 27-285) 🖥️
  - Methoden: __init__, init_ui, on_order_type_changed, analyze_order, _get_ai_analysis, place_order

---

### src/ui/dialogs/parameter_optimization_dialog.py

- **Zeilen:** 679 (Code: 490)
- **Checksum:** `d190be7af188e6659217f73eda2e4be5`
- **Funktionen:** 16
- **Klassen:** 1

**Klassen:**
- `ParameterOptimizationDialog` (Zeile 42-678) 🖥️
  - Methoden: __init__, init_ui, _create_config_tab, _update_combination_count, _create_progress_tab, _create_results_tab, _create_ai_tab, _create_chart_tab, start_optimization, _run_real_backtest... (+5)

---

### src/ui/dialogs/settings_dialog.py

- **Zeilen:** 669 (Code: 485)
- **Checksum:** `458ed33fdc448dd10b6eaa29c6cef2ee`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `SettingsDialog` (Zeile 28-668) 🖥️
  - Methoden: __init__, init_ui, load_current_settings, save_settings

---

### src/ui/icons.py

- **Zeilen:** 243 (Code: 187)
- **Checksum:** `9cf8c84c3fc47f3c8c1c0473fd7ca3ee`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `IconProvider` (Zeile 145-208)
  - Methoden: __init__, _update_colors, set_theme, get_icon, get_available_icons

**Top-Level Funktionen:**
- `_svg_to_icon(svg_data: str, primary_color: str, secondary_color: str) -> QIcon` (Zeile 11)
- `get_icon(name: str) -> QIcon` (Zeile 215)
- `set_icon_theme(theme: str)` (Zeile 227)
- `get_available_icons() -> list[str]` (Zeile 236)

---

### src/ui/themes.py

- **Zeilen:** 359 (Code: 298)
- **Checksum:** `0602a38204bfef0205177ee41a304e39`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `ThemeManager` (Zeile 7-359)
  - Methoden: __init__, _create_dark_theme, _create_light_theme, get_dark_theme, get_light_theme, get_theme

---

### src/ui/widgets/__init__.py

- **Zeilen:** 1 (Code: 1)
- **Checksum:** `64862d097cae28ae0b0339c020945d52`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/widgets/alerts.py

- **Zeilen:** 80 (Code: 60)
- **Checksum:** `b07a8595dc0a5addc1d8e291c2236bed`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `AlertsWidget` (Zeile 12-80) 🖥️
  - Methoden: __init__, init_ui, setup_event_handlers, on_alert_triggered, on_order_rejected, on_app_error, add_alert

---

### src/ui/widgets/backtest_chart_widget.py

- **Zeilen:** 288 (Code: 205)
- **Checksum:** `847c87f52f4798e14c72402ad7d71678`
- **Funktionen:** 15
- **Klassen:** 1

**Klassen:**
- `BacktestChartWidget` (Zeile 29-287) 🖥️
  - Methoden: __init__, _setup_ui, _create_toolbar, _setup_webchannel, _setup_connections, _load_html, load_backtest_result, clear_chart, toggle_markers, _on_toggle_markers... (+5)

---

### src/ui/widgets/base_chart_widget.py

- **Zeilen:** 97 (Code: 74)
- **Checksum:** `110208f91199c6a5543222e609d077b9`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `BaseChartWidget` (Zeile 17-96) 🖥️
  - Methoden: __init__, load_data, update_indicators, _validate_ohlcv_data, _convert_bars_to_dataframe, clear

---

### src/ui/widgets/candlestick_item.py

- **Zeilen:** 199 (Code: 147)
- **Checksum:** `b7824488c0187a9a43dcebd6edd8da35`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `CandlestickItem` (Zeile 20-186)
  - Methoden: __init__, set_data, set_colors, generatePicture, _draw_candlestick, paint, boundingRect, clear, get_data_count, is_empty

**Top-Level Funktionen:**
- `create_candlestick_item() -> CandlestickItem` (Zeile 190)

---

### src/ui/widgets/chart_factory.py

- **Zeilen:** 209 (Code: 159)
- **Checksum:** `51ddf3af6136e63675aa29ce23b89639`
- **Funktionen:** 7
- **Klassen:** 2

**Klassen:**
- `ChartType` (Zeile 25-38)
- `ChartFactory` (Zeile 41-176)
  - Methoden: create_chart, _create_tradingview_chart, get_available_chart_types, get_chart_features, _determine_best_chart_type

**Top-Level Funktionen:**
- `create_chart(symbol: str, chart_type: str, history_manager) -> QWidget` (Zeile 180)
- `get_recommended_chart_type() -> ChartType` (Zeile 202)

---

### src/ui/widgets/chart_interface.py

- **Zeilen:** 267 (Code: 202)
- **Checksum:** `b8f80827a91de5dd183ef1b5ae183b9b`
- **Funktionen:** 29
- **Klassen:** 4

**Klassen:**
- `IChartWidget` (Zeile 13-87)
  - Methoden: set_symbol, set_timeframe, update_data, add_indicator, remove_indicator, clear_data, set_theme, zoom_to_fit, get_visible_range
- `ChartSignals` (Zeile 90-108)
- `BaseChartWidget` (Zeile 111-198)
  - Methoden: __init__, symbol, timeframe, theme, set_symbol, set_timeframe, set_theme, clear_data, get_data_count, is_empty... (+6)
- `ChartCapabilities` (Zeile 201-243)
  - Methoden: __init__, to_dict

**Top-Level Funktionen:**
- `register_chart_adapter(widget_class, capabilities: ChartCapabilities) -> None` (Zeile 246)
- `get_chart_capabilities(widget_class) -> Optional[ChartCapabilities]` (Zeile 258)

---

### src/ui/widgets/chart_shared/__init__.py

- **Zeilen:** 37 (Code: 30)
- **Checksum:** `f60e8c901da478fc72f05e0a752c14ce`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/widgets/chart_shared/constants.py

- **Zeilen:** 292 (Code: 190)
- **Checksum:** `16843f8d1f8b9afe4b487a1602fc0463`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/widgets/chart_shared/data_conversion.py

- **Zeilen:** 313 (Code: 236)
- **Checksum:** `a11be6f2e504c2591bbd40cff57319a5`
- **Funktionen:** 6
- **Klassen:** 0

**Top-Level Funktionen:**
- `convert_bars_to_dataframe(bars: List[Any], timestamp_column: str) -> pd.DataFrame` (Zeile 23)
- `convert_dict_bars_to_dataframe(bars: List[dict], timestamp_key: str) -> pd.DataFrame` (Zeile 96)
- `validate_ohlcv_data(df: pd.DataFrame) -> bool` (Zeile 146)
- `convert_dataframe_to_ohlcv_list(df: pd.DataFrame, use_unix_timestamp: bool) -> List[Tuple[Union[int, datetime], float, float, float, float, float]]` (Zeile 200)
- `convert_dataframe_to_js_format(df: pd.DataFrame, include_volume: bool) -> List[dict]` (Zeile 238)
- `resample_ohlcv(df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame` (Zeile 283)

---

### src/ui/widgets/chart_shared/theme_utils.py

- **Zeilen:** 304 (Code: 231)
- **Checksum:** `f1ab597c04e04c085f7bc68a24f102da`
- **Funktionen:** 9
- **Klassen:** 0

**Top-Level Funktionen:**
- `get_theme_colors(theme: str) -> Dict[str, str]` (Zeile 17)
- `get_candle_colors(theme: str) -> Dict[str, str]` (Zeile 38)
- `get_volume_colors(theme: str) -> Dict[str, str]` (Zeile 56)
- `apply_theme_to_chart(chart_options: Dict[str, Any], theme: str) -> Dict[str, Any]` (Zeile 72)
- `get_pyqtgraph_theme(theme: str) -> Dict[str, Any]` (Zeile 135)
- `get_tradingview_chart_options(theme: str) -> Dict[str, Any]` (Zeile 157)
- `get_candlestick_series_options(theme: str) -> Dict[str, Any]` (Zeile 221)
- `get_volume_series_options(theme: str) -> Dict[str, Any]` (Zeile 241)
- `generate_indicator_color(indicator_type: str, index: int) -> str` (Zeile 265)

---

### src/ui/widgets/chart_state_integration.py

- **Zeilen:** 540 (Code: 401)
- **Checksum:** `cde875aa70696bda352fa4bf9e6ccebe`
- **Funktionen:** 26
- **Klassen:** 2

**Klassen:**
- `TradingViewChartStateMixin` (Zeile 22-416)
  - Methoden: __init_chart_state__, save_chart_state_now, load_chart_state_now, enable_auto_save_state, clear_saved_state, _schedule_state_save, _save_current_state, _get_chart_state_async, _save_chart_state_callback, _convert_js_to_chart_state... (+11)
- `PyQtGraphChartStateMixin` (Zeile 419-491)
  - Methoden: __init_chart_state__, save_chart_state_now, load_chart_state_now

**Top-Level Funktionen:**
- `install_chart_state_persistence(chart_widget, chart_type: str)` (Zeile 494)

---

### src/ui/widgets/chart_state_manager.py

- **Zeilen:** 511 (Code: 373)
- **Checksum:** `cd6c065ff4f69db3da90ca162c50bf37`
- **Funktionen:** 21
- **Klassen:** 7

**Klassen:**
- `IndicatorState` (Zeile 18-25)
- `PaneLayout` (Zeile 29-33)
- `ViewRange` (Zeile 37-44)
- `ChartState` (Zeile 48-80)
  - Methoden: __post_init__
- `ChartStateManager` (Zeile 83-361)
  - Methoden: __init__, save_chart_state, load_chart_state, save_indicator_state, save_view_range, save_pane_layout, remove_chart_state, list_saved_symbols, clear_all_states, _save_state_immediate... (+3)
- `TradingViewChartStateHelper` (Zeile 364-433)
  - Methoden: create_js_set_visible_range, create_js_get_visible_range, create_js_set_pane_layout, create_js_get_pane_layout
- `PyQtGraphChartStateHelper` (Zeile 436-500)
  - Methoden: save_viewbox_state, restore_viewbox_state

**Top-Level Funktionen:**
- `get_chart_state_manager() -> ChartStateManager` (Zeile 506)

---

### src/ui/widgets/chart_window.py

- **Zeilen:** 1873 (Code: 1305)
- **Checksum:** `c43b16c9f6ffdb18536abf012d0778d4`
- **Funktionen:** 47
- **Klassen:** 1

**Klassen:**
- `ChartWindow` (Zeile 27-1872) 🖥️
  - Methoden: __init__, _create_bottom_panel, _toggle_bottom_panel, _on_dock_visibility_changed, _update_toggle_button_text, _create_strategy_tab, _create_backtest_tab, _create_optimization_tab, _create_results_tab, _on_strategy_selected... (+28)

---

### src/ui/widgets/dashboard.py

- **Zeilen:** 167 (Code: 114)
- **Checksum:** `53209cd7d41a5b0213b21322cdef6ca6`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `DashboardWidget` (Zeile 10-167) 🖥️
  - Methoden: __init__, init_ui, _create_stat_widget, setup_event_handlers, on_order_filled, on_market_connected, update_balance, update_pnl, update_positions_count, refresh_stats

---

### src/ui/widgets/embedded_tradingview_chart.py

- **Zeilen:** 2296 (Code: 1798)
- **Checksum:** `364e9a0215718b02890872ea05b69304`
- **Funktionen:** 47
- **Klassen:** 1

**Klassen:**
- `EmbeddedTradingViewChart` (Zeile 600-2295) 🖥️
  - Methoden: __init__, _show_error_ui, _setup_ui, _create_toolbar, _execute_js, _flush_pending_js, _on_page_loaded, _start_chart_ready_poll, _poll_chart_ready, _on_chart_ready_result... (+34)

---

### src/ui/widgets/indicators.py

- **Zeilen:** 166 (Code: 124)
- **Checksum:** `aae7780d0597257a7ffab7265dacfe26`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `IndicatorsWidget` (Zeile 27-165) 🖥️
  - Methoden: __init__, _setup_ui, _add_indicator, _remove_indicator

---

### src/ui/widgets/orders.py

- **Zeilen:** 76 (Code: 53)
- **Checksum:** `8a2fad69bfcde799637818b78612d50a`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `OrdersWidget` (Zeile 9-76)
  - Methoden: __init__, _get_table_columns, _get_column_keys, _setup_event_subscriptions, on_order_created, on_order_updated, add_order, update_order

---

### src/ui/widgets/performance_dashboard.py

- **Zeilen:** 804 (Code: 573)
- **Checksum:** `e1b64dbb90da6b2ccfaee84be9df26d7`
- **Funktionen:** 22
- **Klassen:** 3

**Klassen:**
- `PerformanceMetrics` (Zeile 48-68)
- `MetricCard` (Zeile 71-115) 🖥️
  - Methoden: __init__, update_value
- `PerformanceDashboard` (Zeile 118-804) 🖥️
  - Methoden: __init__, _setup_ui, _create_overview_tab, _create_returns_tab, _create_trades_tab, _create_positions_tab, _create_ai_tab, _create_reports_tab, _setup_timers, _load_performance_data... (+10)

---

### src/ui/widgets/positions.py

- **Zeilen:** 91 (Code: 67)
- **Checksum:** `5b46dfb9df77cb13dd3c0573a104020c`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `PositionsWidget` (Zeile 12-91)
  - Methoden: _get_table_columns, _get_column_keys, _get_format_functions, update_positions, _setup_event_subscriptions, on_order_filled, on_market_tick, refresh

---

### src/ui/widgets/watchlist.py

- **Zeilen:** 664 (Code: 484)
- **Checksum:** `da75fc7913d815d225f172d257514861`
- **Funktionen:** 23
- **Klassen:** 1

**Klassen:**
- `WatchlistWidget` (Zeile 31-663) 🖥️
  - Methoden: __init__, init_ui, setup_event_handlers, on_market_tick, on_market_bar, update_prices, format_volume, add_symbol_from_input, add_symbol, remove_symbol... (+13)

---

### src/ui/widgets/widget_helpers.py

- **Zeilen:** 349 (Code: 249)
- **Checksum:** `bb84debea688203bb1cb603bf2acdb15`
- **Funktionen:** 18
- **Klassen:** 2

**Klassen:**
- `EventBusWidget` (Zeile 168-215) 🖥️
  - Methoden: __init__, _subscribe_event, _setup_event_subscriptions, closeEvent
- `BaseTableWidget` (Zeile 220-348)
  - Methoden: __init__, _init_ui, _get_table_columns, _get_table_config, _configure_table, _add_additional_widgets, update_row, _get_column_keys, _get_format_functions

**Top-Level Funktionen:**
- `create_table_widget(columns: list[str], stretch_columns: bool, selection_behavior: QTableWidget.SelectionBehavior, selection_mode: QTableWidget.SelectionMode, editable: bool, alternating_colors: bool, sortable: bool) -> QTableWidget` (Zeile 23)
- `setup_table_row(table: QTableWidget, row: int, data: dict[str, Any], column_keys: list[str], format_funcs: dict[str, Any] | None) -> None` (Zeile 72)
- `create_vbox_layout(parent: QWidget | None, spacing: int, margins: tuple[int, int, int, int] | None) -> QVBoxLayout` (Zeile 106)
- `create_hbox_layout(parent: QWidget | None, spacing: int, margins: tuple[int, int, int, int] | None) -> QHBoxLayout` (Zeile 126)
- `create_grid_layout(parent: QWidget | None, spacing: int, margins: tuple[int, int, int, int] | None) -> QGridLayout` (Zeile 146)

---

### start_orderpilot.py

- **Zeilen:** 238 (Code: 178)
- **Checksum:** `0be003b607dc0d1e13ec4ebfca79afed`
- **Funktionen:** 8
- **Klassen:** 0

**Top-Level Funktionen:**
- `setup_logging(log_level: str) -> None` (Zeile 19)
- `check_dependencies() -> bool` (Zeile 38)
- `check_database() -> None` (Zeile 70)
- `print_startup_banner() -> None` (Zeile 87)
- `async main_with_args(args: argparse.Namespace) -> None` (Zeile 106)
- `create_parser() -> argparse.ArgumentParser` (Zeile 122)
- `main() -> int` (Zeile 178)
- `global_exception_handler(exc_type, exc_value, exc_traceback)` (Zeile 181)

---

### tests/__init__.py

- **Zeilen:** 1 (Code: 1)
- **Checksum:** `a430661beaca7a0373c6a67c9023928e`
- **Funktionen:** 0
- **Klassen:** 0

---

### tests/test_ai_backtest_review.py

- **Zeilen:** 443 (Code: 383)
- **Checksum:** `f32fc739870f5d986d2f35d447f4b491`
- **Funktionen:** 11
- **Klassen:** 4

**Klassen:**
- `TestBacktestReviewModel` (Zeile 126-185)
  - Methoden: test_backtest_review_creation, test_backtest_review_validation
- `TestReviewBacktestMethod` (Zeile 188-319)
  - Methoden: test_review_backtest_with_result, test_review_backtest_prompt_building, test_review_backtest_context_data
- `TestPromptBuilderIntegration` (Zeile 322-354)
  - Methoden: test_build_backtest_prompt_with_metrics
- `TestEndToEndIntegration` (Zeile 357-438)
  - Methoden: test_full_backtest_review_workflow

**Top-Level Funktionen:**
- `ai_config()` (Zeile 26)
- `sample_backtest_result()` (Zeile 38)

---

### tests/test_backtest_converter.py

- **Zeilen:** 206 (Code: 171)
- **Checksum:** `7955b0c06fea26a1b2ebd9d759a641ab`
- **Funktionen:** 6
- **Klassen:** 2

**Klassen:**
- `TestBacktestConverter` (Zeile 15-169)
  - Methoden: test_backtest_result_creation, test_trade_model, test_trade_json_serialization, test_backtest_result_json_serialization
- `TestConverterFunctions` (Zeile 172-201)
  - Methoden: test_converter_import, test_backtest_models_import

---

### tests/test_broker_adapter.py

- **Zeilen:** 244 (Code: 174)
- **Checksum:** `5fb40da7068b49ea71e9de0d42d8286a`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `TestMockBrokerAdapter` (Zeile 12-244)
  - Methoden: setup_method, test_connect_disconnect, test_place_order, test_place_limit_order, test_cancel_order, test_get_positions, test_get_balance, test_order_validation, test_fee_calculation, test_get_quote... (+1)

---

### tests/test_chart_adapter.py

- **Zeilen:** 373 (Code: 281)
- **Checksum:** `a4d1dcc534925cacac4954fe3f8cb397`
- **Funktionen:** 16
- **Klassen:** 1

**Klassen:**
- `TestChartAdapter` (Zeile 23-368)
  - Methoden: sample_bars, sample_trades, sample_equity_curve, sample_backtest_result, test_bars_to_candlesticks, test_bars_to_candlesticks_empty, test_equity_to_line_series, test_build_markers_from_trades, test_build_markers_with_sl_tp, test_indicators_to_series... (+6)

---

### tests/test_chart_bridge.py

- **Zeilen:** 280 (Code: 200)
- **Checksum:** `d45ca6c8f3fa12e55517514481debbe8`
- **Funktionen:** 12
- **Klassen:** 1

**Klassen:**
- `TestChartBridge` (Zeile 24-275)
  - Methoden: sample_result, test_bridge_initialization, test_load_backtest_result_object, test_load_backtest_result_json, test_load_invalid_json, test_get_current_symbol, test_get_metrics_summary, test_clear_chart, test_toggle_markers, test_update_trade... (+2)

---

### tests/test_chart_persistence.py

- **Zeilen:** 94 (Code: 56)
- **Checksum:** `89bb293202f05ce7857a132aebcc826d`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `TestChartPersistence` (Zeile 10-93)
  - Methoden: chart_window, test_settings_key_sanitization, test_save_chart_state, test_restore_chart_state, test_restore_chart_state_empty

---

### tests/test_config.py

- **Zeilen:** 171 (Code: 125)
- **Checksum:** `490c7e957cb61793add76a136735eca9`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `TestConfiguration` (Zeile 19-170)
  - Methoden: setup_method, test_default_config_creation, test_profile_loading, test_save_config, test_config_validation, test_environment_specific_settings, test_broker_config, test_ai_config, test_list_profiles, test_export_config

---

### tests/test_crypto_integration.py

- **Zeilen:** 282 (Code: 204)
- **Checksum:** `8a1813e4b6a6724f4e5f5ad2f71738fa`
- **Funktionen:** 16
- **Klassen:** 4

**Klassen:**
- `TestAlpacaCryptoProvider` (Zeile 58-119)
  - Methoden: test_provider_initialization, test_fetch_btc_bars, test_fetch_eth_bars, test_fetch_multiple_crypto_pairs
- `TestAlpacaCryptoStreamClient` (Zeile 122-164)
  - Methoden: test_stream_initialization, test_connect_disconnect, test_subscribe_to_crypto
- `TestHistoryManagerCrypto` (Zeile 167-233)
  - Methoden: history_manager, test_fetch_crypto_data, test_asset_class_filtering, test_start_crypto_stream
- `TestCryptoDataValidation` (Zeile 236-277)
  - Methoden: test_crypto_price_ranges, test_crypto_timestamp_ordering

**Top-Level Funktionen:**
- `alpaca_credentials()` (Zeile 32)
- `crypto_provider(alpaca_credentials)` (Zeile 41)
- `crypto_stream_client(alpaca_credentials)` (Zeile 50)

---

### tests/test_crypto_strategies.py

- **Zeilen:** 287 (Code: 196)
- **Checksum:** `9755703942ff923f18970bea976aee42`
- **Funktionen:** 13
- **Klassen:** 4

**Klassen:**
- `TestCryptoStrategyLoading` (Zeile 25-110)
  - Methoden: test_load_volatility_breakout_strategy, test_load_mean_reversion_strategy, test_load_momentum_combo_strategy
- `TestCryptoStrategyValidation` (Zeile 113-179)
  - Methoden: test_all_strategies_have_asset_class, test_all_strategies_have_recommended_symbols, test_all_strategies_have_risk_management
- `TestCryptoStrategyCompilation` (Zeile 182-242)
  - Methoden: test_compile_volatility_breakout, test_compile_mean_reversion, test_compile_momentum_combo
- `TestCryptoStrategyMetadata` (Zeile 245-282)
  - Methoden: test_all_strategies_have_description, test_all_strategies_have_notes

**Top-Level Funktionen:**
- `strategy_loader()` (Zeile 14)
- `strategies_dir()` (Zeile 20)

---

### tests/test_database.py

- **Zeilen:** 405 (Code: 308)
- **Checksum:** `aae68263bd7c8cf89041b1001fd8062d`
- **Funktionen:** 18
- **Klassen:** 1

**Klassen:**
- `TestDatabaseOperations` (Zeile 19-405)
  - Methoden: setup_method, teardown_method, test_create_order, test_create_position, test_create_market_bar, test_update_order_status, test_query_orders_by_status, test_delete_old_market_bars, test_cascade_delete, test_transaction_rollback... (+8)

---

### tests/test_event_bus.py

- **Zeilen:** 135 (Code: 89)
- **Checksum:** `b8bcf90506f8676ac7af5c67782b7965`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `TestEventBus` (Zeile 8-135)
  - Methoden: setup_method, test_event_creation, test_subscribe_and_emit, test_unsubscribe, test_multiple_subscribers, test_event_filter

---

### tests/test_execution_engine.py

- **Zeilen:** 322 (Code: 233)
- **Checksum:** `97a6433019bbc2fc66c001af1ffaf1da`
- **Funktionen:** 14
- **Klassen:** 2

**Klassen:**
- `TestExecutionEngine` (Zeile 13-266)
  - Methoden: setup_method, test_engine_start_stop, test_engine_pause_resume, test_kill_switch_activation, test_submit_order, test_get_status, test_update_metrics, test_kill_switch_on_max_loss, test_queue_priority, test_max_pending_orders... (+2)
- `TestExecutionTask` (Zeile 269-321)
  - Methoden: test_task_creation, test_task_auto_id_generation

---

### tests/test_execution_events.py

- **Zeilen:** 469 (Code: 348)
- **Checksum:** `fc1d52c2dadbe8e426e3c5908ab26b5f`
- **Funktionen:** 20
- **Klassen:** 6

**Klassen:**
- `TestOrderEvent` (Zeile 26-65)
  - Methoden: test_order_event_creation, test_order_event_data_sync
- `TestExecutionEvent` (Zeile 68-109)
  - Methoden: test_execution_event_creation, test_execution_event_with_pnl
- `TestOrderEventEmitter` (Zeile 112-177)
  - Methoden: test_emit_order_created, test_emit_order_filled, test_emit_order_cancelled, test_emit_order_rejected
- `TestExecutionEventEmitter` (Zeile 180-263)
  - Methoden: test_emit_trade_entry, test_emit_trade_exit, test_emit_stop_loss_hit, test_emit_take_profit_hit
- `TestBacktraderEventAdapter` (Zeile 266-398)
  - Methoden: test_adapter_initialization, test_on_order_created, test_on_order_filled_with_entry, test_on_order_filled_with_exit, test_get_order_type
- `TestEventIntegration` (Zeile 401-468)
  - Methoden: test_full_order_lifecycle, test_full_trade_lifecycle

**Top-Level Funktionen:**
- `clear_event_history()` (Zeile 19)

---

### tests/test_integration.py

- **Zeilen:** 245 (Code: 170)
- **Checksum:** `633c13e594ca5a259fa014659605e593`
- **Funktionen:** 10
- **Klassen:** 3

**Klassen:**
- `TestEndToEndWorkflow` (Zeile 20-157)
  - Methoden: setup_method, test_complete_trade_lifecycle, test_order_rejection_workflow, test_multiple_symbols_portfolio, test_balance_tracking_accuracy
- `TestConfigurationIntegration` (Zeile 160-205)
  - Methoden: setup_method, test_profile_workflow, test_multiple_profiles
- `TestDatabaseIntegration` (Zeile 208-244)
  - Methoden: setup_method, test_order_persistence

---

### tests/test_parameter_optimization.py

- **Zeilen:** 423 (Code: 335)
- **Checksum:** `7df2dc92d394d92656c2f64ba8f0c25c`
- **Funktionen:** 22
- **Klassen:** 6

**Klassen:**
- `TestParameterRange` (Zeile 59-72)
  - Methoden: test_parameter_range_creation
- `TestOptimizerConfig` (Zeile 75-97)
  - Methoden: test_default_config, test_custom_config
- `TestParameterOptimizer` (Zeile 100-320)
  - Methoden: test_optimizer_initialization, test_grid_search_simple, test_grid_search_with_failures, test_calculate_score, test_calculate_score_with_constraints, test_extract_metrics, test_sensitivity_analysis
- `TestAIOptimizationInsight` (Zeile 323-341)
  - Methoden: test_insight_creation
- `TestQuickOptimize` (Zeile 344-381)
  - Methoden: test_quick_optimize
- `TestOptimizationResult` (Zeile 384-418)
  - Methoden: test_optimization_result_creation

**Top-Level Funktionen:**
- `sample_backtest_result()` (Zeile 30)

---

### tests/test_performance.py

- **Zeilen:** 201 (Code: 151)
- **Checksum:** `5dbf7286cb335c9ed17a64174476a6b2`
- **Funktionen:** 21
- **Klassen:** 3

**Klassen:**
- `TestPerformanceMonitor` (Zeile 17-98)
  - Methoden: setup_method, test_record_latency, test_increment_counter, test_context_manager, test_get_all_stats, test_reset, test_percentiles, test_report_generation
- `TestPerformanceDecorators` (Zeile 101-160)
  - Methoden: setup_method, test_monitor_performance_sync, test_monitor_performance_async, test_log_performance_sync, test_log_performance_async
- `TestPerformanceTimer` (Zeile 163-200)
  - Methoden: test_manual_timer, test_timer_context_manager, test_timer_not_started_error, test_timer_records_to_global_monitor

---

### tests/test_security.py

- **Zeilen:** 259 (Code: 163)
- **Checksum:** `401356892378d19f074f76a30a81f06d`
- **Funktionen:** 21
- **Klassen:** 6

**Klassen:**
- `TestEncryption` (Zeile 18-58)
  - Methoden: setup_method, test_encrypt_decrypt_string, test_encrypt_decrypt_dict, test_encryption_without_key
- `TestCredentialManager` (Zeile 61-96)
  - Methoden: setup_method, test_store_retrieve_credential, test_delete_credential
- `TestSessionManager` (Zeile 99-153)
  - Methoden: setup_method, test_create_session, test_validate_session, test_invalid_session, test_session_timeout, test_terminate_session
- `TestRateLimiter` (Zeile 156-196)
  - Methoden: setup_method, test_rate_limit_within_bounds, test_rate_limit_exceeded, test_rate_limit_different_users
- `TestPasswordUtils` (Zeile 199-232)
  - Methoden: test_hash_and_verify_password, test_different_salts_produce_different_hashes
- `TestAPIKey` (Zeile 235-259)
  - Methoden: test_generate_api_key, test_validate_api_key

---

### tests/test_skeleton.py

- **Zeilen:** 5 (Code: 4)
- **Checksum:** `506ff91ee0da37d094abd01ba85071ff`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `test_skeleton_imports()` (Zeile 1)

---

### tests/test_strategy_compiler.py

- **Zeilen:** 524 (Code: 423)
- **Checksum:** `60adcb44357980e44c2c3a1c48e6427d`
- **Funktionen:** 19
- **Klassen:** 19

**Klassen:**
- `TestIndicatorFactory` (Zeile 27-70)
  - Methoden: test_create_sma, test_create_rsi, test_create_macd, test_normalize_macd_params, test_unsupported_indicator_type
- `TestConditionEvaluator` (Zeile 73-302)
  - Methoden: test_evaluate_simple_gt_condition, test_evaluate_inside_operator, test_evaluate_outside_operator, test_evaluate_and_logic_group, test_evaluate_or_logic_group, test_evaluate_not_logic_group, test_evaluate_nested_logic_groups, test_cross_above_detection
- `MockStrategy` (Zeile 79-88)
- `MockData` (Zeile 80-85)
- `MockStrategy` (Zeile 111-114)
- `MockData` (Zeile 112-113)
- `MockStrategy` (Zeile 137-140)
- `MockData` (Zeile 138-139)
- `MockStrategy` (Zeile 163-166)
- `MockData` (Zeile 164-165)
- `MockStrategy` (Zeile 193-196)
- `MockData` (Zeile 194-195)
- `MockStrategy` (Zeile 223-226)
- `MockData` (Zeile 224-225)
- `MockStrategy` (Zeile 251-255)
- `MockData` (Zeile 252-254)
- `MockStrategy` (Zeile 278-281)
- `MockData` (Zeile 279-280)
- `TestStrategyCompiler` (Zeile 305-478)
  - Methoden: test_compile_simple_sma_crossover, test_compile_rsi_strategy, test_compile_multi_indicator_strategy, test_compile_long_short_strategy, test_compile_with_nested_logic

**Top-Level Funktionen:**
- `test_integration_with_backtrader()` (Zeile 481)

---

### tests/test_strategy_definition.py

- **Zeilen:** 577 (Code: 478)
- **Checksum:** `54b2a2b163987a64b4ebd66207e38fa8`
- **Funktionen:** 34
- **Klassen:** 5

**Klassen:**
- `TestIndicatorConfig` (Zeile 24-82)
  - Methoden: test_basic_indicator_config, test_indicator_with_custom_source, test_invalid_alias_with_spaces, test_invalid_alias_with_special_chars, test_valid_alias_with_underscore
- `TestCondition` (Zeile 85-155)
  - Methoden: test_simple_comparison, test_indicator_comparison, test_crosses_above_operator, test_inside_range_operator, test_invalid_inside_operator_single_value, test_invalid_inside_operator_wrong_length
- `TestLogicGroup` (Zeile 158-245)
  - Methoden: test_and_logic_group, test_or_logic_group, test_nested_logic_groups, test_empty_conditions_rejected, test_not_operator_single_condition, test_not_operator_multiple_conditions_rejected
- `TestRiskManagement` (Zeile 248-310)
  - Methoden: test_basic_risk_management, test_atr_based_risk_management, test_trailing_stop, test_multiple_stop_loss_methods_rejected, test_multiple_take_profit_methods_rejected, test_invalid_stop_loss_pct
- `TestStrategyDefinition` (Zeile 313-572)
  - Methoden: test_simple_sma_crossover_strategy, test_rsi_oversold_strategy_with_logic_group, test_long_short_strategy, test_duplicate_indicator_aliases_rejected, test_invalid_indicator_reference_rejected, test_built_in_references_valid, test_get_indicator_by_alias, test_invalid_version_format, test_json_serialization, test_yaml_export_import... (+1)

---

### tests/test_trading_modes.py

- **Zeilen:** 403 (Code: 330)
- **Checksum:** `5b04e3f3984664b3ab7427e9a6e52e49`
- **Funktionen:** 26
- **Klassen:** 8

**Klassen:**
- `TestTradingModeEnum` (Zeile 23-36)
  - Methoden: test_trading_mode_values, test_trading_mode_from_string
- `TestProfileConfigTradingMode` (Zeile 39-67)
  - Methoden: test_default_profile_has_paper_mode, test_profile_with_backtest_mode, test_profile_mode_serialization
- `TestBacktestModeValidation` (Zeile 70-102)
  - Methoden: test_backtest_mode_with_mock_broker, test_backtest_mode_warns_on_real_broker, test_backtest_profile_safety_check
- `TestPaperModeValidation` (Zeile 105-146)
  - Methoden: test_paper_mode_with_paper_trading, test_paper_mode_warns_without_paper_trading, test_paper_profile_safety_check
- `TestLiveModeValidation` (Zeile 149-214)
  - Methoden: test_live_mode_requires_manual_approval, test_live_mode_rejects_paper_trading, test_live_mode_with_correct_settings, test_live_profile_safety_check_all_issues
- `TestModeSwitching` (Zeile 217-272)
  - Methoden: test_switch_from_paper_to_backtest, test_switch_to_live_fails_validation, test_switch_to_live_succeeds_with_valid_config, test_switch_without_validation
- `TestProfileFactoryMethods` (Zeile 275-331)
  - Methoden: test_create_backtest_profile, test_create_paper_profile, test_create_live_profile, test_all_factory_profiles_are_valid
- `TestModeConfigIntegration` (Zeile 334-402)
  - Methoden: test_backtest_profile_loads_from_yaml, test_paper_profile_loads_from_yaml, test_mode_validation_in_loaded_profile

---

### tools/demo_ai_backtest_review.py

- **Zeilen:** 322 (Code: 267)
- **Checksum:** `84c4818b8b261b9f8e59b10ebfaa5471`
- **Funktionen:** 3
- **Klassen:** 0

**Top-Level Funktionen:**
- `create_sample_backtest_result() -> BacktestResult` (Zeile 39)
- `async demo_ai_backtest_review()` (Zeile 121)
- `async main()` (Zeile 310)

---

### tools/demo_ai_providers.py

- **Zeilen:** 361 (Code: 265)
- **Checksum:** `17101891f07f944440c19c6be2139f0a`
- **Funktionen:** 6
- **Klassen:** 2

**Klassen:**
- `TradingRecommendation` (Zeile 50-58)
- `MarketAnalysis` (Zeile 61-67)

**Top-Level Funktionen:**
- `async demo_openai_thinking()` (Zeile 72)
- `async demo_openai_instant()` (Zeile 128)
- `async demo_anthropic_sonnet()` (Zeile 165)
- `async demo_reasoning_comparison()` (Zeile 215)
- `async demo_multi_provider()` (Zeile 259)
- `async main()` (Zeile 308)

---

### tools/demo_chart_widget.py

- **Zeilen:** 283 (Code: 226)
- **Checksum:** `ea94e14fe094cccd1f608c005ac9c13c`
- **Funktionen:** 2
- **Klassen:** 0

**Top-Level Funktionen:**
- `create_demo_backtest_result() -> BacktestResult` (Zeile 38)
- `main()` (Zeile 226)

---

### tools/demo_crypto_integration.py

- **Zeilen:** 280 (Code: 195)
- **Checksum:** `6c356e38f892c4e8330919a9d8b57f0e`
- **Funktionen:** 5
- **Klassen:** 0

**Top-Level Funktionen:**
- `async demo_crypto_historical_data()` (Zeile 31)
- `async demo_crypto_streaming()` (Zeile 94)
- `async demo_history_manager_crypto()` (Zeile 153)
- `async demo_multiple_crypto_pairs()` (Zeile 202)
- `async main()` (Zeile 251)

---

### tools/demo_crypto_strategies.py

- **Zeilen:** 367 (Code: 247)
- **Checksum:** `f178c9967b804fb5082c7dc9aff3f940`
- **Funktionen:** 6
- **Klassen:** 0

**Top-Level Funktionen:**
- `demo_load_strategies()` (Zeile 23)
- `demo_inspect_strategy_details()` (Zeile 69)
- `demo_compile_strategies()` (Zeile 128)
- `demo_compare_strategies()` (Zeile 172)
- `async demo_backtest_strategy()` (Zeile 242)
- `main()` (Zeile 334)

---

### tools/demo_execution_events.py

- **Zeilen:** 283 (Code: 211)
- **Checksum:** `84a63d56a475dc1b40acf8a46d68e3a5`
- **Funktionen:** 9
- **Klassen:** 0

**Top-Level Funktionen:**
- `demo_order_events()` (Zeile 32)
- `demo_execution_events()` (Zeile 72)
- `demo_event_listener()` (Zeile 130)
- `on_trade_entry(event)` (Zeile 137)
- `on_trade_exit(event)` (Zeile 144)
- `on_stop_loss(event)` (Zeile 152)
- `on_take_profit(event)` (Zeile 159)
- `demo_event_history()` (Zeile 221)
- `main()` (Zeile 243)

---

### tools/demo_parameter_optimization.py

- **Zeilen:** 422 (Code: 311)
- **Checksum:** `f6137c7a81a22daeed3463671e19ea59`
- **Funktionen:** 7
- **Klassen:** 0

**Top-Level Funktionen:**
- `async mock_backtest_runner(params: dict) -> BacktestResult` (Zeile 47)
- `async demo_simple_grid_search()` (Zeile 145)
- `async demo_advanced_grid_search()` (Zeile 200)
- `async demo_ai_guided_optimization()` (Zeile 246)
- `async demo_quick_optimize()` (Zeile 305)
- `async demo_sensitivity_visualization()` (Zeile 339)
- `async main()` (Zeile 374)

---

### tools/demo_strategy_compiler.py

- **Zeilen:** 259 (Code: 186)
- **Checksum:** `5f15bf55a72107922191753d1c984aa2`
- **Funktionen:** 3
- **Klassen:** 0

**Top-Level Funktionen:**
- `create_sample_data() -> bt.feeds.DataBase` (Zeile 29)
- `run_backtest_with_strategy(strategy_def: StrategyDefinition, data: bt.feeds.DataBase, initial_cash: float) -> dict` (Zeile 82)
- `main()` (Zeile 177)

---

### tools/demo_trading_modes.py

- **Zeilen:** 276 (Code: 213)
- **Checksum:** `4f1e32c9e688020cd8c9913e9a530378`
- **Funktionen:** 6
- **Klassen:** 0

**Top-Level Funktionen:**
- `demo_factory_methods()` (Zeile 36)
- `demo_safety_validation()` (Zeile 86)
- `demo_mode_switching()` (Zeile 120)
- `demo_config_manager()` (Zeile 154)
- `demo_validation_errors()` (Zeile 194)
- `main()` (Zeile 239)

---

### tools/demo_yaml_to_backtest.py

- **Zeilen:** 270 (Code: 203)
- **Checksum:** `f97c3f3e8103acc9bbaf26d229b36ec5`
- **Funktionen:** 3
- **Klassen:** 0

**Top-Level Funktionen:**
- `create_synthetic_data(days: int, start_price: float, volatility: float) -> bt.feeds.DataBase` (Zeile 38)
- `async run_yaml_strategy_backtest(yaml_file: Path, symbol: str, initial_cash: float) -> None` (Zeile 96)
- `async main()` (Zeile 220)

---

### tools/manage_watchlist.py

- **Zeilen:** 271 (Code: 208)
- **Checksum:** `74b3eb245365c337131aa5b7ec1ef34b`
- **Funktionen:** 8
- **Klassen:** 0

**Top-Level Funktionen:**
- `print_header()` (Zeile 18)
- `load_watchlist() -> list[str]` (Zeile 25)
- `save_watchlist(symbols: list[str])` (Zeile 39)
- `show_watchlist(symbols: list[str])` (Zeile 54)
- `add_symbol(symbols: list[str], symbol: str) -> list[str]` (Zeile 70)
- `remove_symbol(symbols: list[str], symbol: str) -> list[str]` (Zeile 95)
- `add_preset(symbols: list[str], preset: str) -> list[str]` (Zeile 116)
- `main()` (Zeile 171)

---

### tools/test_backtest_chart_adapter.py

- **Zeilen:** 338 (Code: 270)
- **Checksum:** `35569fb80572aa1bfd221f8644caad2f`
- **Funktionen:** 2
- **Klassen:** 0

**Top-Level Funktionen:**
- `create_sample_backtest_result() -> BacktestResult` (Zeile 42)
- `test_chart_adapter_pipeline()` (Zeile 249)

---

### tools/test_strategy_yaml.py

- **Zeilen:** 198 (Code: 142)
- **Checksum:** `16bfc9cd4e13db192753afcbde67aedf`
- **Funktionen:** 4
- **Klassen:** 0

**Top-Level Funktionen:**
- `load_and_validate_strategy(yaml_file: Path) -> StrategyDefinition` (Zeile 26)
- `print_strategy_details(strategy: StrategyDefinition) -> None` (Zeile 55)
- `_format_condition(cond, indent) -> str` (Zeile 114)
- `main()` (Zeile 142)

---
