# 📋 CODE-INVENTUR REPORT

## Projekt-Übersicht
- **Projekt:** OrderPilot-AI
- **Timestamp:** 2026-01-06T07:57:21.974189
- **Root:** `/mnt/d/03_GIT/02_Python/07_OrderPilot-AI`
- **Analysierte Dateien:** 416

---

## Lines of Code (LOC)

| Metrik | Anzahl |
|--------|--------|
| **Gesamt** | 95,657 |
| **Produktiv** | 74,331 |
| **Kommentare** | 4,580 |
| **Leerzeilen** | 16,746 |

---

## Funktionen (3,183 total)

**Top 10 Dateien nach Funktionsanzahl:**

| Datei | Funktionen |
|-------|------------|
| `src/chart_marking/mixin/chart_marking_mixin.py` | 48 |
| `src/ui/widgets/chart_window.py` | 45 |
| `tests/test_strategy_definition.py` | 34 |
| `src/ui/widgets/chart_window_mixins/bot_display_position_mixin.py` | 33 |
| `src/ui/widgets/chart_window_mixins/strategy_simulator_results_mixin.py` | 30 |
| `src/ui/widgets/chart_interface.py` | 29 |
| `src/ui/widgets/chart_mixins/indicator_mixin.py` | 29 |
| `src/ui/widgets/chart_window_mixins/strategy_simulator_run_mixin.py` | 29 |
| `src/core/simulator/simulation_engine.py` | 28 |
| `src/core/tradingbot/state_machine.py` | 28 |

---

## Klassen (675 total)

**Top 10 Klassen nach Methodenanzahl:**

| Klasse | Datei | Methoden | LOC |
|--------|-------|----------|-----|
| `ChartMarkingMixin` | `src/chart_marking/mixin/chart_marking_mixin.py` | 47 | 615 |
| `ChartWindow` | `src/ui/widgets/chart_window.py` | 37 | 507 |
| `BotDisplayPositionMixin` | `src/ui/widgets/chart_window_mixins/bot_display_position_mixin.py` | 33 | 470 |
| `StrategySimulatorResultsMixin` | `src/ui/widgets/chart_window_mixins/strategy_simulator_results_mixin.py` | 30 | 507 |
| `StrategySimulator` | `src/core/simulator/simulation_engine.py` | 29 | 506 |
| `StrategySimulatorRunMixin` | `src/ui/widgets/chart_window_mixins/strategy_simulator_run_mixin.py` | 29 | 437 |
| `BotStateMachine` | `src/core/tradingbot/state_machine.py` | 28 | 420 |
| `WatchlistWidget` | `src/ui/widgets/watchlist.py` | 28 | 546 |
| `IndicatorMixin` | `src/ui/widgets/chart_mixins/indicator_mixin.py` | 28 | 645 |
| `ZoneManager` | `src/chart_marking/zones/support_resistance.py` | 26 | 455 |

---

## UI-Komponenten (2,548 total)

**Typ-Verteilung:**

| UI-Typ | Anzahl |
|--------|--------|
| `Frame` | 392 |
| `Button` | 362 |
| `Label` | 286 |
| `Entry` | 277 |
| `QLabel` | 251 |
| `QPushButton` | 235 |
| `QWidget` | 220 |
| `QTableWidget` | 155 |
| `QCheckBox` | 78 |
| `QComboBox` | 77 |
| `QDialog` | 56 |
| `QLineEdit` | 51 |
| `QTabWidget` | 41 |
| `QToolBar` | 38 |
| `QMainWindow` | 20 |
| `QMenuBar` | 4 |
| `QRadioButton` | 4 |
| `Canvas` | 1 |

---

## Event-Handler (223 total)

**Beispiele:**

| Event-Handler | Datei | Zeilen |
|---------------|-------|--------|
| `_on_quick_action()` | `src/chart_chat/chart_chat_actions_mixin.py` | 65-78 |
| `_on_send()` | `src/chart_chat/chart_chat_actions_mixin.py` | 79-87 |
| `_on_full_analysis()` | `src/chart_chat/chart_chat_actions_mixin.py` | 88-97 |
| `_on_analysis_complete()` | `src/chart_chat/chart_chat_actions_mixin.py` | 155-194 |
| `_on_analysis_error()` | `src/chart_chat/chart_chat_actions_mixin.py` | 195-211 |
| `_on_open_evaluation_popup()` | `src/chart_chat/chart_chat_actions_mixin.py` | 224-229 |
| `_on_bars_changed()` | `src/chart_chat/chart_chat_events_mixin.py` | 40-48 |
| `_on_all_bars_toggled()` | `src/chart_chat/chart_chat_events_mixin.py` | 49-71 |
| `on_chart_changed()` | `src/chart_chat/chart_chat_events_mixin.py` | 72-90 |
| `_on_export()` | `src/chart_chat/chart_chat_export_mixin.py` | 36-48 |
| `_on_clear_history()` | `src/chart_chat/chart_chat_history_mixin.py` | 81-90 |
| `_on_open_prompts_editor()` | `src/chart_chat/chart_chat_ui_mixin.py` | 203-208 |
| `on_chart_changed()` | `src/chart_chat/chat_service.py` | 301-306 |
| `_on_chart_symbol_changed()` | `src/chart_chat/mixin.py` | 216-219 |
| `_on_provider_changed()` | `src/ui/ai_analysis_window.py` | 274-300 |

*... und 208 weitere*

---

## ⚠️ DATEIEN ÜBER 600 LOC (SPLITTING ERFORDERLICH!)

**Anzahl:** 0

| # | Datei | LOC (produktiv) | Funktionen | Klassen | Empfehlung |
|---|-------|-----------------|------------|---------|------------|

---

## Top 20 Größte Dateien

| # | Datei | LOC (produktiv) | LOC (total) |
|---|-------|-----------------|-------------|
| 1 | `src/ui/widgets/chart_mixins/indicator_mixin.py` | **556** | 677 |
| 2 | `src/core/tradingbot/strategy_templates.py` | **554** | 578 |
| 3 | `src/chart_chat/chart_chat_actions_mixin.py` | **543** | 643 |
| 4 | `src/ui/widgets/chart_window.py` | **539** | 665 |
| 5 | `src/ui/widgets/bitunix_trading/bitunix_trading_widget.py` | **527** | 660 |
| 6 | `src/ui/widgets/chart_mixins/toolbar_mixin.py` | **524** | 607 |
| 7 | `src/chart_marking/mixin/chart_marking_mixin.py` | **521** | 645 |
| 8 | `src/ui/widgets/chart_window_mixins/bot_callbacks_signal_mixin.py` | **503** | 574 |
| 9 | `src/core/execution/engine.py` | **490** | 618 |
| 10 | `src/ai/prompts.py` | **479** | 563 |
| 11 | `tests/test_strategy_definition.py` | **478** | 577 |
| 12 | `src/core/simulator/optimization_bayesian.py` | **472** | 556 |
| 13 | `src/core/tradingbot/bot_state_handlers.py` | **471** | 605 |
| 14 | `src/core/simulator/strategy_params_registry.py` | **469** | 504 |
| 15 | `src/core/market_data/history_provider.py` | **467** | 567 |
| 16 | `src/core/tradingbot/strategy_evaluator.py` | **460** | 610 |
| 17 | `src/core/simulator/simulation_engine.py` | **458** | 541 |
| 18 | `src/core/tradingbot/backtest_harness.py` | **451** | 579 |
| 19 | `src/ui/widgets/chart_mixins/bot_overlay_mixin.py` | **450** | 563 |
| 20 | `src/ui/widgets/watchlist.py` | **449** | 589 |

---

## API-Endpoints (219 total)

**Gefundene Endpoint-Patterns:**

| Pattern | Datei | Zeile |
|---------|-------|-------|
| `def get_` | `src/ai/ai_provider_factory.py` | 33 |
| `def get_` | `src/ai/ai_provider_factory.py` | 81 |
| `def get_` | `src/ai/ai_provider_factory.py` | 211 |
| `def get_` | `src/ai/ai_provider_factory.py` | 354 |
| `def get_` | `src/ai/anthropic_service.py` | 377 |
| `def get_` | `src/ai/gemini_service.py` | 436 |
| `def get_` | `src/ai/openai_service.py` | 98 |
| `def get_` | `src/ai/prompts.py` | 552 |
| `def get_` | `src/ai/providers.py` | 387 |
| `def get_` | `src/ai/providers.py` | 397 |
| `def get_` | `src/ai/providers.py` | 407 |
| `def get_` | `src/ai/providers.py` | 416 |
| `def get_` | `src/ai/providers.py` | 425 |
| `def get_` | `src/ai/__init__.py` | 29 |
| `def delete_` | `src/chart_chat/chart_chat_actions_mixin.py` | 573 |
| `def get_` | `src/chart_chat/chat_service.py` | 144 |
| `def get_` | `src/chart_chat/chat_service.py` | 243 |
| `def get_` | `src/chart_chat/chat_service.py` | 281 |
| `def get_` | `src/chart_chat/history_store.py` | 183 |
| `def get_` | `src/chart_chat/markings_manager.py` | 33 |

*... und 199 weitere*

---

## Zusammenfassung

✅ Inventur erfolgreich abgeschlossen!

**Nächste Schritte:**
1. ✅ Phase 1 abgeschlossen: Inventur erstellt
2. ⏭️ Phase 2: Analyse starten (Dead Code, Duplikate, Komplexität)
3. ⏸️ Phase 3: Warten auf Bestätigung vor Refactoring
4. ⏸️ Phase 4: Verifikation nach Refactoring

---

*Report generiert am {self.inventory["timestamp"]}*
