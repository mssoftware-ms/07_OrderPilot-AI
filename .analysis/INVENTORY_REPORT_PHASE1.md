# 📋 CODE-INVENTUR REPORT - PHASE 1

**Projekt:** OrderPilot-AI  
**Timestamp:** 2026-01-06T08:27:26.484644  
**Analysierte Dateien:** 371

---

## 📊 ÜBERSICHT

| Metrik | Wert |
|--------|------|
| **Gesamt-Dateien** | 371 |
| **LOC Gesamt** | 87,213 |
| **LOC Produktiv** | 28,851 |
| **LOC Kommentare/Docstrings** | 43,484 |
| **LOC Leerzeilen** | 14,878 |
| **Funktionen Total** | 2840 |
| **Klassen Total** | 584 |
| **UI-Komponenten** | 35 |
| **Imports Total** | 2710 |

---

## ✅ DATEIGROSSEN-STATUS

### Produktive LOC pro Datei:
- **Limit:** 600 produktive LOC
- **Dateien über Limit:** 0 
- **Status:** ✅ ALLE DATEIEN UNTER LIMIT

### Top 15 größte Dateien (nach produktiven LOC):

| # | Datei | LOC Total | LOC Produktiv | Funktionen | Klassen |
|---|-------|-----------|---------------|------------|----------|
| 1 | `ui/widgets/chart_window_mixins/bot_callbacks_signal_mixin.py` | 573 | 405 | 25 | 1 |
| 2 | `chart_chat/chart_chat_actions_mixin.py` | 642 | 372 | 27 | 2 |
| 3 | `core/tradingbot/bot_state_handlers.py` | 604 | 368 | 11 | 1 |
| 4 | `core/simulator/optimization_bayesian.py` | 555 | 353 | 25 | 3 |
| 5 | `ui/widgets/chart_window_mixins/bot_ui_control_mixin.py` | 421 | 351 | 9 | 1 |
| 6 | `core/market_data/history_provider.py` | 566 | 313 | 10 | 1 |
| 7 | `ui/widgets/chart_mixins/indicator_mixin.py` | 676 | 293 | 29 | 2 |
| 8 | `core/tradingbot/strategy_templates.py` | 577 | 284 | 8 | 1 |
| 9 | `ui/widgets/watchlist.py` | 588 | 283 | 26 | 1 |
| 10 | `ui/widgets/chart_window_mixins/strategy_simulator_run_mixin.py` | 446 | 283 | 29 | 1 |
| 11 | `ui/widgets/chart_window_mixins/bot_display_signals_mixin.py` | 348 | 277 | 9 | 1 |
| 12 | `chart_chat/analyzer.py` | 512 | 276 | 6 | 1 |
| 13 | `ai/prompts.py` | 563 | 274 | 11 | 5 |
| 14 | `core/backtesting/result_converter.py` | 489 | 264 | 13 | 0 |
| 15 | `core/pattern_db/qdrant_client.py` | 473 | 257 | 4 | 2 |

---

## 🔧 TOP 10 DATEIEN MIT MEISTEN FUNKTIONEN

| # | Datei | Funktionen | LOC Produktiv |
|---|-------|------------|---------------|
| 1 | `chart_marking/mixin/chart_marking_mixin.py` | 48 | 154 |
| 2 | `ui/widgets/chart_window.py` | 45 | 199 |
| 3 | `ui/widgets/chart_window_mixins/bot_display_position_mixin.py` | 33 | 62 |
| 4 | `ui/widgets/chart_window_mixins/strategy_simulator_results_mixin.py` | 30 | 191 |
| 5 | `ui/widgets/chart_interface.py` | 29 | 52 |
| 6 | `ui/widgets/chart_mixins/indicator_mixin.py` | 29 | 293 |
| 7 | `ui/widgets/chart_window_mixins/strategy_simulator_run_mixin.py` | 29 | 283 |
| 8 | `core/simulator/simulation_engine.py` | 28 | 184 |
| 9 | `core/tradingbot/state_machine.py` | 28 | 106 |
| 10 | `chart_chat/chart_chat_actions_mixin.py` | 27 | 372 |

---

## 🏗️ TOP 10 DATEIEN MIT MEISTEN KLASSEN

| # | Datei | Klassen | LOC Produktiv |
|---|-------|---------|---------------|
| 1 | `database/models.py` | 16 | 111 |
| 2 | `core/tradingbot/models.py` | 14 | 159 |
| 3 | `config/config_types.py` | 13 | 72 |
| 4 | `core/broker/broker_types.py` | 13 | 50 |
| 5 | `chart_marking/models.py` | 12 | 126 |
| 6 | `chart_chat/models.py` | 11 | 21 |
| 7 | `core/strategy/definition.py` | 11 | 172 |
| 8 | `core/models/backtest_models.py` | 10 | 31 |
| 9 | `ai/openai_models.py` | 9 | 5 |
| 10 | `core/tradingbot/config.py` | 8 | 192 |

---

## 🖼️ UI-KOMPONENTEN (35 total)

| # | Komponente | Datei |
|---|------------|-------|
| 1 | `PromptsEditorDialog` | `src/chart_chat/prompts_editor_dialog.py` |
| 2 | `AIAnalysisWindow` | `src/ui/ai_analysis_window.py` |
| 3 | `PromptEditorDialog` | `src/ui/ai_analysis_window.py` |
| 4 | `TradingApplication` | `src/ui/app.py` |
| 5 | `StartupLogWindow` | `src/ui/app_startup_window.py` |
| 6 | `AIBacktestDialog` | `src/ui/dialogs/ai_backtest_dialog.py` |
| 7 | `BacktestDialog` | `src/ui/dialogs/backtest_dialog.py` |
| 8 | `ChartMarkingsManagerDialog` | `src/ui/dialogs/chart_markings_manager_dialog.py` |
| 9 | `LayoutManagerDialog` | `src/ui/dialogs/layout_manager_dialog.py` |
| 10 | `OrderDialog` | `src/ui/dialogs/order_dialog.py` |
| 11 | `ParameterOptimizationDialog` | `src/ui/dialogs/parameter_optimization_dialog.py` |
| 12 | `PatternDatabaseDialog` | `src/ui/dialogs/pattern_db_dialog.py` |
| 13 | `SettingsDialog` | `src/ui/dialogs/settings_dialog.py` |
| 14 | `ZoneEditDialog` | `src/ui/dialogs/zone_edit_dialog.py` |
| 15 | `ChartSetDialog` | `src/ui/multi_chart/chart_set_dialog.py` |
| 16 | `AlertsWidget` | `src/ui/widgets/alerts.py` |
| 17 | `BacktestChartWidget` | `src/ui/widgets/backtest_chart_widget.py` |
| 18 | `BaseChartWidget` | `src/ui/widgets/base_chart_widget.py` |
| 19 | `DockTitleBar` | `src/ui/widgets/chart_window.py` |
| 20 | `ChartWindow` | `src/ui/widgets/chart_window.py` |

*... und 15 weitere UI-Komponenten*

---

## 📁 MODULE-VERTEILUNG

| Modul | Dateien | LOC Produktiv | Funktionen | Klassen |
|-------|---------|---------------|------------|----------|
| `core` | 146 | 11,600 | 952 | 266 |
| `ui` | 142 | 10,911 | 1273 | 150 |
| `chart_chat` | 18 | 1,924 | 158 | 31 |
| `ai` | 15 | 1,248 | 61 | 30 |
| `chart_marking` | 17 | 1,248 | 183 | 25 |
| `derivatives` | 17 | 1,022 | 99 | 33 |
| `config` | 4 | 386 | 22 | 16 |
| `common` | 7 | 293 | 76 | 16 |
| `database` | 3 | 220 | 16 | 17 |
| `backtesting` | 1 | 0 | 0 | 0 |
| `__init__.py` | 1 | -1 | 0 | 0 |

---

## 📊 ZUSAMMENFASSUNG PHASE 1

✅ **Inventur erfolgreich abgeschlossen**

- 371 Python-Dateien analysiert
- 2840 Funktionen erfasst
- 584 Klassen erfasst
- 35 UI-Komponenten identifiziert
- 28,851 produktive LOC
- 0 Dateien über 600 LOC Limit

**Status:** ✅ Bereit für Phase 2 (Analyse)

---

*Generiert am: 2026-01-06 08:29:19*
