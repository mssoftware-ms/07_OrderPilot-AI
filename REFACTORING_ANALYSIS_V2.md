# 🔍 ANALYSE-REPORT (Regen)

**Erstellt:** 2026-01-01
**Inventur-Zeitstempel:** 2026-01-01T15:20:08.987373

---

## 1. DEAD CODE (Kandidaten zur Entfernung)

### ✅ Sicher zu entfernen (mit Begründung):
Keine sicheren Kandidaten gefunden.


### ⚠️ Manuell prüfen (unsicher):
| Funktion | Datei:Zeile | Warnung |
|----------|-------------|---------|
| `create_inventory()` | `refactoring_inventory.py:96` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `print_summary()` | `refactoring_inventory.py:170` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `create_detailed_report()` | `refactoring_inventory.py:213` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_crosshair_sync_javascript()` | `src/chart_marking/multi_chart/crosshair_sync.py:215` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_logger()` | `src/common/logging_setup.py:283` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `from_historical_bar()` | `src/core/models/backtest_models.py:246` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `to_historical_bars()` | `src/core/models/backtest_models.py:269` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `fetch_daytrading_data()` | `src/core/pattern_db/fetcher.py:241` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `filter_entry_only_param_config()` | `src/core/simulator/strategy_params.py:52` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_strategy_loader()` | `src/core/strategy/loader.py:185` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `parse_percentage()` | `src/derivatives/ko_finder/adapter/normalizer.py:230` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `create_candlestick_item()` | `src/ui/widgets/candlestick_item.py:190` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_recommended_chart_type()` | `src/ui/widgets/chart_factory.py:202` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `register_chart_adapter()` | `src/ui/widgets/chart_interface.py:246` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_chart_capabilities()` | `src/ui/widgets/chart_interface.py:258` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `convert_dict_bars_to_dataframe()` | `src/ui/widgets/chart_shared/data_conversion.py:96` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `convert_dataframe_to_js_format()` | `src/ui/widgets/chart_shared/data_conversion.py:238` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `resample_ohlcv()` | `src/ui/widgets/chart_shared/data_conversion.py:283` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_candle_colors()` | `src/ui/widgets/chart_shared/theme_utils.py:38` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_volume_colors()` | `src/ui/widgets/chart_shared/theme_utils.py:56` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_pyqtgraph_theme()` | `src/ui/widgets/chart_shared/theme_utils.py:135` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_tradingview_chart_options()` | `src/ui/widgets/chart_shared/theme_utils.py:157` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_candlestick_series_options()` | `src/ui/widgets/chart_shared/theme_utils.py:221` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `get_volume_series_options()` | `src/ui/widgets/chart_shared/theme_utils.py:241` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `generate_indicator_color()` | `src/ui/widgets/chart_shared/theme_utils.py:265` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `install_chart_state_persistence()` | `src/ui/widgets/chart_state_integration.py:494` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `create_hbox_layout()` | `src/ui/widgets/widget_helpers.py:126` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `create_grid_layout()` | `src/ui/widgets/widget_helpers.py:146` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `clear_event_history()` | `tests/test_execution_events.py:19` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `test_skeleton_imports()` | `tests/test_skeleton.py:1` | Public API könnte extern genutzt werden (Vorkommen: 1) |
| `test_integration_with_backtrader()` | `tests/test_strategy_compiler.py:481` | Public API könnte extern genutzt werden (Vorkommen: 1) |

### Unreachable Code (heuristisch):
Keine klaren Unreachable-Stellen gefunden.


---

## 2. DUPLIKATE

Keine exakten Duplikate (Top-Level Funktionen) gefunden.

---

## 3. KOMPLEXITÄT

| Funktion | Datei:Zeile | CC | Nesting | LOC | Empfehlung |
|----------|-------------|----|---------|-----|-----------|
| `main()` | `tools/manage_watchlist.py:171` | 28 | 10 | 96 | Splitten/Extrahieren |
| `preprocess_candles()` | `src/core/tradingbot/candle_preprocessing.py:30` | 21 | 4 | 97 | Splitten/Extrahieren |
| `_calculate_metrics()` | `src/core/backtesting/result_converter.py:285` | 18 | 2 | 134 | Splitten/Extrahieren |
| `run_yaml_strategy_backtest()` | `tools/demo_yaml_to_backtest.py:96` | 17 | 2 | 122 | Splitten/Extrahieren |
| `build_database()` | `src/core/pattern_db/build_database.py:33` | 10 | 2 | 112 | Splitten/Extrahieren |
| `create_sample_backtest_result()` | `tools/test_backtest_chart_adapter.py:42` | 7 | 4 | 205 | Splitten/Extrahieren |
| `demo_ai_backtest_review()` | `tools/demo_ai_backtest_review.py:121` | 7 | 2 | 187 | Splitten/Extrahieren |
| `create_demo_backtest_result()` | `tools/demo_chart_widget.py:38` | 6 | 3 | 186 | Splitten/Extrahieren |
| `test_tradingbot_imports()` | `tests/test_post_refactoring.py:19` | 1 | 0 | 103 | Splitten/Extrahieren |
| `test_split_modules_direct()` | `tests/test_post_refactoring.py:195` | 1 | 0 | 103 | Splitten/Extrahieren |
---

## 4. DATEIGRÖSSEN-ANALYSE (600 LOC)

**Ergebnis:** Keine Python-Datei überschreitet 600 produktive LOC (Scope ohne venv/docs).


---

## 5. ZUSAMMENFASSUNG

- Dead Code (sicher): 0 Funktionen (Top-Level, private)
- Dead Code (unsicher): 31 Funktionen (Top-Level, public)
- Duplikate (exakt): 0 Funktionsgruppen
- Überkomplex: 10 Funktionen
- Dateien >600 LOC: 0

**WARTE AUF BESTÄTIGUNG VOR PHASE 3!**
