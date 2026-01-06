# Complete List: CC 11-20 Warnings

**Total:** 117 Funktionen
**Generiert:** 2026-01-06

---

## By Complexity (Highest First)

### CC=20 (7 Funktionen)

- `calculate_bb` - core/indicators/volatility.py:28
- `select_strategy` - core/tradingbot/strategy_selector.py:133
- `_validate_product` - derivatives/ko_finder/adapter/normalizer.py:153
- `_convert_macd_data_to_chart_format` - ui/widgets/chart_mixins/indicator_mixin.py:143
- `_check_stops_on_candle_close` - ui/widgets/chart_window_mixins/bot_callbacks_candle_mixin.py:82
- `_update_current_position_display` - ui/widgets/chart_window_mixins/bot_panels_mixin.py:220
- `_on_chart_stop_line_moved` - ui/widgets/chart_window_mixins/bot_position_persistence_chart_mixin.py:15
### CC=19 (4 Funktionen)

- `from_variable_string` - chart_chat/chart_markings.py:61
- `detect_regime` - core/ai_analysis/regime.py:19
- `combine_signals` - core/strategy/engine.py:321
- `calculate_metrics` - core/tradingbot/strategy_evaluator.py:69
### CC=18 (3 Funktionen)

- `run` - chart_chat/chart_chat_worker.py:52
- `_load_ui_settings` - ui/dialogs/pattern_db_settings_mixin.py:34
- `_update_signals_pnl` - ui/widgets/chart_window_mixins/bot_display_signals_mixin.py:13
### CC=17 (7 Funktionen)

- `_should_reselect` - core/tradingbot/strategy_selector.py:229
- `validate_chart_data` - ui/chart/chart_adapter.py:397
- `_place_order` - ui/widgets/bitunix_trading/bitunix_trading_widget.py:556
- `_update_derivative_section` - ui/widgets/chart_window_mixins/bot_display_position_mixin.py:424
- `_sell_signal` - ui/widgets/chart_window_mixins/bot_position_persistence_context_mixin.py:41
- `_load_window_state` - ui/widgets/chart_window_mixins/state_mixin.py:26
- `_calculate_metrics` - ui/widgets/performance_dashboard.py:205
### CC=16 (10 Funktionen)

- `get_pattern_statistics` - core/pattern_db/qdrant_client.py:399
- `on_bar` - core/tradingbot/bot_controller.py:392
- `_update_regime` - core/tradingbot/bot_helpers.py:133
- `_check_macd_exit` - core/tradingbot/bot_state_handlers.py:575
- `_classify_volatility` - core/tradingbot/regime_engine.py:198
- `BotMarker` - ui/widgets/chart_mixins/bot_overlay_types.py:25
- `_convert_js_to_chart_state` - ui/widgets/chart_state_integration.py:187
- `_add_test_zone` - ui/widgets/embedded_tradingview_chart_marking_mixin.py:59
- `_add_test_structure` - ui/widgets/embedded_tradingview_chart_marking_mixin.py:122
- `_get_display_value` - ui/widgets/ko_finder/table_model.py:129
### CC=15 (6 Funktionen)

- `get_api_key` - ai/ai_provider_factory.py:81
- `_update_position_on_fill` - core/broker/bitunix_paper_adapter.py:176
- `add_trades_sheet` - core/simulator/excel_export.py:397
- `_calculate_trade_metrics` - core/simulator/simulation_engine.py:403
- `_save_market_data_settings` - ui/dialogs/settings_dialog.py:394
- `to_chart_marker` - ui/widgets/chart_mixins/bot_overlay_types.py:34
### CC=14 (12 Funktionen)

- `_store_ticks` - core/market_data/stream_client.py:333
- `add_summary_sheet` - core/simulator/excel_export.py:239
- `MomentumStrategy` - core/strategy/strategies/momentum.py:16
- `validate_candles` - core/tradingbot/candle_preprocessing.py:188
- `_calculate_derived_features` - core/tradingbot/feature_engine.py:425
- `_stop_live_data_streams` - ui/app_components/broker_mixin.py:318
- `_filter_markings` - ui/dialogs/chart_markings_manager_dialog.py:337
- `_delete_selected` - ui/dialogs/chart_markings_manager_dialog.py:473
- `convert_bars_to_dataframe` - ui/widgets/chart_shared/data_conversion.py:23
- `BotCallbacksCandleMixin` - ui/widgets/chart_window_mixins/bot_callbacks_candle_mixin.py:9
- `_update_derivative_display` - ui/widgets/chart_window_mixins/bot_panels_mixin.py:272
- `_on_candle_closed` - ui/widgets/chart_window_mixins/bot_tr_lock_mixin.py:68
### CC=13 (22 Funktionen)

- `ChartMarking` - chart_chat/chart_markings.py:29
- `_on_message` - core/market_data/bitunix_stream.py:293
- `fetch_bars` - core/market_data/providers/bitunix_provider.py:172
- `_create_bar` - core/market_data/resampler.py:288
- `add_ui_table_sheet` - core/simulator/excel_export.py:111
- `_select_best_result` - core/simulator/optimization_bayesian.py:378
- `_resolve_operand` - core/strategy/compiler.py:338
- `_resolve_indicator` - core/strategy/evaluation.py:201
- `BreakoutStrategy` - core/strategy/strategies/breakout.py:16
- `evaluate` - core/strategy/strategies/momentum.py:19
- `ScalpingStrategy` - core/strategy/strategies/scalping.py:17
- `run` - core/tradingbot/backtest_harness.py:157
- `build_hud_content` - ui/widgets/chart_mixins/bot_overlay_types.py:106
- `_convert_multi_series_data_to_chart_format` - ui/widgets/chart_mixins/indicator_mixin.py:203
- `_update_or_add_candidate` - ui/widgets/chart_window_mixins/bot_callbacks_signal_mixin.py:207
- `_log_bot_diagnostics` - ui/widgets/chart_window_mixins/bot_display_logging_mixin.py:18
- `_set_stop_columns` - ui/widgets/chart_window_mixins/bot_display_signals_mixin.py:176
- `_set_status_and_pnl_columns` - ui/widgets/chart_window_mixins/bot_display_signals_mixin.py:264
- `_load_signal_history` - ui/widgets/chart_window_mixins/bot_position_persistence_storage_mixin.py:32
- `_add_test_entry_marker` - ui/widgets/embedded_tradingview_chart_marking_mixin.py:11
- `_add_test_line` - ui/widgets/embedded_tradingview_chart_marking_mixin.py:173
- `update_prices` - ui/widgets/watchlist.py:226
### CC=12 (22 Funktionen)

- `chat_completion` - ai/openai_service_client_mixin.py:297
- `stream_completion` - ai/provider_gemini.py:122
- `stream_completion` - ai/providers.py:140
- `extract_technicals` - core/ai_analysis/features.py:20
- `_analyze_sensitivity` - core/backtesting/optimization.py:308
- `fetch_bars` - core/market_data/alpaca_crypto_provider.py:49
- `_run_supervisor` - core/market_data/bitunix_stream.py:133
- `_map_invalid_status` - core/market_data/bitunix_stream.py:240
- `start_realtime_stream` - core/market_data/history_provider.py:382
- `_calculate_analysis` - core/pattern_db/pattern_service.py:168
- `evaluate` - core/strategy/strategies/breakout.py:19
- `evaluate` - core/strategy/strategies/scalping.py:20
- `_score_condition` - core/tradingbot/entry_scorer.py:215
- `validate` - core/tradingbot/execution.py:226
- `_handle_fetch_result` - derivatives/ko_finder/service.py:235
- `toggle_live_data` - ui/app_components/broker_mixin.py:275
- `_load_markings` - ui/dialogs/chart_markings_manager_dialog.py:126
- `_calculate_date_range` - ui/widgets/chart_mixins/data_loading_mixin.py:332
- `_add_indicator_instance` - ui/widgets/chart_mixins/indicator_mixin.py:57
- `_populate_simulator_parameter_widgets` - ui/widgets/chart_window_mixins/strategy_simulator_params_mixin.py:37
- `add_rect_range` - ui/widgets/embedded_tradingview_chart.py:152
- `_get_background_color` - ui/widgets/ko_finder/table_model.py:166
### CC=11 (24 Funktionen)

- `AnalysisWorker` - chart_chat/chart_chat_worker.py:35
- `_get_env_credential` - config/loader.py:178
- `analyze` - core/ai_analysis/openai_client.py:43
- `_pnl_stats` - core/backtesting/result_converter.py:370
- `fetch_bars` - core/market_data/providers/alpha_vantage_provider.py:34
- `_prepare_data` - core/simulator/simulation_engine.py:58
- `get_strategy_score_rows` - core/tradingbot/bot_controller.py:364
- `_trailing_atr` - core/tradingbot/entry_exit_engine.py:154
- `_check_direction_match` - core/tradingbot/entry_scorer.py:274
- `_score_rsi_momentum` - core/tradingbot/entry_scorer.py:325
- `check_exit` - core/tradingbot/exit_checker.py:67
- `_apply_rsi_confirmation` - core/tradingbot/regime_engine.py:180
- `detect_regime_change` - core/tradingbot/regime_engine.py:343
- `_parse_row` - derivatives/ko_finder/adapter/parser.py:243
- `_check_flags` - derivatives/ko_finder/models.py:139
- `initialize_realtime_streaming` - ui/app_components/broker_mixin.py:216
- `_collect_symbols` - ui/dialogs/pattern_db_build_mixin.py:83
- `_create_chart_window` - ui/multi_chart/layout_manager.py:207
- `_update_macd_realtime` - ui/widgets/chart_mixins/indicator_mixin.py:553
- `_apply_chart_state` - ui/widgets/chart_state_integration.py:271
- `_update_walk_forward_panel` - ui/widgets/chart_window_mixins/bot_display_position_mixin.py:239
- `_resolve_signal_pnl` - ui/widgets/chart_window_mixins/bot_display_position_mixin.py:333
- `_set_derivative_columns` - ui/widgets/chart_window_mixins/bot_display_signals_mixin.py:308
- `update_balance` - ui/widgets/dashboard.py:97

---

## By Module

### ai/ (4 Funktionen)

- CC=15 | `get_api_key` - ai/ai_provider_factory.py:81
- CC=12 | `chat_completion` - ai/openai_service_client_mixin.py:297
- CC=12 | `stream_completion` - ai/provider_gemini.py:122
- CC=12 | `stream_completion` - ai/providers.py:140

### chart_chat/ (4 Funktionen)

- CC=19 | `from_variable_string` - chart_chat/chart_markings.py:61
- CC=18 | `run` - chart_chat/chart_chat_worker.py:52
- CC=13 | `ChartMarking` - chart_chat/chart_markings.py:29
- CC=11 | `AnalysisWorker` - chart_chat/chart_chat_worker.py:35

### config/ (1 Funktionen)

- CC=11 | `_get_env_credential` - config/loader.py:178

### core/ (52 Funktionen)

- CC=20 | `calculate_bb` - core/indicators/volatility.py:28
- CC=20 | `select_strategy` - core/tradingbot/strategy_selector.py:133
- CC=19 | `detect_regime` - core/ai_analysis/regime.py:19
- CC=19 | `combine_signals` - core/strategy/engine.py:321
- CC=19 | `calculate_metrics` - core/tradingbot/strategy_evaluator.py:69
- CC=17 | `_should_reselect` - core/tradingbot/strategy_selector.py:229
- CC=16 | `get_pattern_statistics` - core/pattern_db/qdrant_client.py:399
- CC=16 | `on_bar` - core/tradingbot/bot_controller.py:392
- CC=16 | `_update_regime` - core/tradingbot/bot_helpers.py:133
- CC=16 | `_check_macd_exit` - core/tradingbot/bot_state_handlers.py:575
- CC=16 | `_classify_volatility` - core/tradingbot/regime_engine.py:198
- CC=15 | `_update_position_on_fill` - core/broker/bitunix_paper_adapter.py:176
- CC=15 | `add_trades_sheet` - core/simulator/excel_export.py:397
- CC=15 | `_calculate_trade_metrics` - core/simulator/simulation_engine.py:403
- CC=14 | `_store_ticks` - core/market_data/stream_client.py:333
- CC=14 | `add_summary_sheet` - core/simulator/excel_export.py:239
- CC=14 | `MomentumStrategy` - core/strategy/strategies/momentum.py:16
- CC=14 | `validate_candles` - core/tradingbot/candle_preprocessing.py:188
- CC=14 | `_calculate_derived_features` - core/tradingbot/feature_engine.py:425
- CC=13 | `_on_message` - core/market_data/bitunix_stream.py:293
- CC=13 | `fetch_bars` - core/market_data/providers/bitunix_provider.py:172
- CC=13 | `_create_bar` - core/market_data/resampler.py:288
- CC=13 | `add_ui_table_sheet` - core/simulator/excel_export.py:111
- CC=13 | `_select_best_result` - core/simulator/optimization_bayesian.py:378
- CC=13 | `_resolve_operand` - core/strategy/compiler.py:338
- CC=13 | `_resolve_indicator` - core/strategy/evaluation.py:201
- CC=13 | `BreakoutStrategy` - core/strategy/strategies/breakout.py:16
- CC=13 | `evaluate` - core/strategy/strategies/momentum.py:19
- CC=13 | `ScalpingStrategy` - core/strategy/strategies/scalping.py:17
- CC=13 | `run` - core/tradingbot/backtest_harness.py:157
- CC=12 | `extract_technicals` - core/ai_analysis/features.py:20
- CC=12 | `_analyze_sensitivity` - core/backtesting/optimization.py:308
- CC=12 | `fetch_bars` - core/market_data/alpaca_crypto_provider.py:49
- CC=12 | `_run_supervisor` - core/market_data/bitunix_stream.py:133
- CC=12 | `_map_invalid_status` - core/market_data/bitunix_stream.py:240
- CC=12 | `start_realtime_stream` - core/market_data/history_provider.py:382
- CC=12 | `_calculate_analysis` - core/pattern_db/pattern_service.py:168
- CC=12 | `evaluate` - core/strategy/strategies/breakout.py:19
- CC=12 | `evaluate` - core/strategy/strategies/scalping.py:20
- CC=12 | `_score_condition` - core/tradingbot/entry_scorer.py:215
- CC=12 | `validate` - core/tradingbot/execution.py:226
- CC=11 | `analyze` - core/ai_analysis/openai_client.py:43
- CC=11 | `_pnl_stats` - core/backtesting/result_converter.py:370
- CC=11 | `fetch_bars` - core/market_data/providers/alpha_vantage_provider.py:34
- CC=11 | `_prepare_data` - core/simulator/simulation_engine.py:58
- CC=11 | `get_strategy_score_rows` - core/tradingbot/bot_controller.py:364
- CC=11 | `_trailing_atr` - core/tradingbot/entry_exit_engine.py:154
- CC=11 | `_check_direction_match` - core/tradingbot/entry_scorer.py:274
- CC=11 | `_score_rsi_momentum` - core/tradingbot/entry_scorer.py:325
- CC=11 | `check_exit` - core/tradingbot/exit_checker.py:67
- CC=11 | `_apply_rsi_confirmation` - core/tradingbot/regime_engine.py:180
- CC=11 | `detect_regime_change` - core/tradingbot/regime_engine.py:343

### derivatives/ (4 Funktionen)

- CC=20 | `_validate_product` - derivatives/ko_finder/adapter/normalizer.py:153
- CC=12 | `_handle_fetch_result` - derivatives/ko_finder/service.py:235
- CC=11 | `_parse_row` - derivatives/ko_finder/adapter/parser.py:243
- CC=11 | `_check_flags` - derivatives/ko_finder/models.py:139

### ui/ (52 Funktionen)

- CC=20 | `_convert_macd_data_to_chart_format` - ui/widgets/chart_mixins/indicator_mixin.py:143
- CC=20 | `_check_stops_on_candle_close` - ui/widgets/chart_window_mixins/bot_callbacks_candle_mixin.py:82
- CC=20 | `_update_current_position_display` - ui/widgets/chart_window_mixins/bot_panels_mixin.py:220
- CC=20 | `_on_chart_stop_line_moved` - ui/widgets/chart_window_mixins/bot_position_persistence_chart_mixin.py:15
- CC=18 | `_load_ui_settings` - ui/dialogs/pattern_db_settings_mixin.py:34
- CC=18 | `_update_signals_pnl` - ui/widgets/chart_window_mixins/bot_display_signals_mixin.py:13
- CC=17 | `validate_chart_data` - ui/chart/chart_adapter.py:397
- CC=17 | `_place_order` - ui/widgets/bitunix_trading/bitunix_trading_widget.py:556
- CC=17 | `_update_derivative_section` - ui/widgets/chart_window_mixins/bot_display_position_mixin.py:424
- CC=17 | `_sell_signal` - ui/widgets/chart_window_mixins/bot_position_persistence_context_mixin.py:41
- CC=17 | `_load_window_state` - ui/widgets/chart_window_mixins/state_mixin.py:26
- CC=17 | `_calculate_metrics` - ui/widgets/performance_dashboard.py:205
- CC=16 | `BotMarker` - ui/widgets/chart_mixins/bot_overlay_types.py:25
- CC=16 | `_convert_js_to_chart_state` - ui/widgets/chart_state_integration.py:187
- CC=16 | `_add_test_zone` - ui/widgets/embedded_tradingview_chart_marking_mixin.py:59
- CC=16 | `_add_test_structure` - ui/widgets/embedded_tradingview_chart_marking_mixin.py:122
- CC=16 | `_get_display_value` - ui/widgets/ko_finder/table_model.py:129
- CC=15 | `_save_market_data_settings` - ui/dialogs/settings_dialog.py:394
- CC=15 | `to_chart_marker` - ui/widgets/chart_mixins/bot_overlay_types.py:34
- CC=14 | `_stop_live_data_streams` - ui/app_components/broker_mixin.py:318
- CC=14 | `_filter_markings` - ui/dialogs/chart_markings_manager_dialog.py:337
- CC=14 | `_delete_selected` - ui/dialogs/chart_markings_manager_dialog.py:473
- CC=14 | `convert_bars_to_dataframe` - ui/widgets/chart_shared/data_conversion.py:23
- CC=14 | `BotCallbacksCandleMixin` - ui/widgets/chart_window_mixins/bot_callbacks_candle_mixin.py:9
- CC=14 | `_update_derivative_display` - ui/widgets/chart_window_mixins/bot_panels_mixin.py:272
- CC=14 | `_on_candle_closed` - ui/widgets/chart_window_mixins/bot_tr_lock_mixin.py:68
- CC=13 | `build_hud_content` - ui/widgets/chart_mixins/bot_overlay_types.py:106
- CC=13 | `_convert_multi_series_data_to_chart_format` - ui/widgets/chart_mixins/indicator_mixin.py:203
- CC=13 | `_update_or_add_candidate` - ui/widgets/chart_window_mixins/bot_callbacks_signal_mixin.py:207
- CC=13 | `_log_bot_diagnostics` - ui/widgets/chart_window_mixins/bot_display_logging_mixin.py:18
- CC=13 | `_set_stop_columns` - ui/widgets/chart_window_mixins/bot_display_signals_mixin.py:176
- CC=13 | `_set_status_and_pnl_columns` - ui/widgets/chart_window_mixins/bot_display_signals_mixin.py:264
- CC=13 | `_load_signal_history` - ui/widgets/chart_window_mixins/bot_position_persistence_storage_mixin.py:32
- CC=13 | `_add_test_entry_marker` - ui/widgets/embedded_tradingview_chart_marking_mixin.py:11
- CC=13 | `_add_test_line` - ui/widgets/embedded_tradingview_chart_marking_mixin.py:173
- CC=13 | `update_prices` - ui/widgets/watchlist.py:226
- CC=12 | `toggle_live_data` - ui/app_components/broker_mixin.py:275
- CC=12 | `_load_markings` - ui/dialogs/chart_markings_manager_dialog.py:126
- CC=12 | `_calculate_date_range` - ui/widgets/chart_mixins/data_loading_mixin.py:332
- CC=12 | `_add_indicator_instance` - ui/widgets/chart_mixins/indicator_mixin.py:57
- CC=12 | `_populate_simulator_parameter_widgets` - ui/widgets/chart_window_mixins/strategy_simulator_params_mixin.py:37
- CC=12 | `add_rect_range` - ui/widgets/embedded_tradingview_chart.py:152
- CC=12 | `_get_background_color` - ui/widgets/ko_finder/table_model.py:166
- CC=11 | `initialize_realtime_streaming` - ui/app_components/broker_mixin.py:216
- CC=11 | `_collect_symbols` - ui/dialogs/pattern_db_build_mixin.py:83
- CC=11 | `_create_chart_window` - ui/multi_chart/layout_manager.py:207
- CC=11 | `_update_macd_realtime` - ui/widgets/chart_mixins/indicator_mixin.py:553
- CC=11 | `_apply_chart_state` - ui/widgets/chart_state_integration.py:271
- CC=11 | `_update_walk_forward_panel` - ui/widgets/chart_window_mixins/bot_display_position_mixin.py:239
- CC=11 | `_resolve_signal_pnl` - ui/widgets/chart_window_mixins/bot_display_position_mixin.py:333
- CC=11 | `_set_derivative_columns` - ui/widgets/chart_window_mixins/bot_display_signals_mixin.py:308
- CC=11 | `update_balance` - ui/widgets/dashboard.py:97
