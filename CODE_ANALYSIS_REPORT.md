# 🔍 CODE-ANALYSE REPORT (PHASE 2)

## Projekt-Übersicht
- **Projekt:** OrderPilot-AI
- **Timestamp:** 2026-01-06T07:59:45.541969
- **Total Funktionen:** 3,183

---

## 1. DEAD CODE (Kandidaten zur Entfernung)

### ✅ Sicher zu entfernen (318 Funktionen)

**Funktionen ohne externe Referenzen:**

| # | Funktion | Datei | Zeilen | Signatur |
|---|----------|-------|--------|----------|
| 1 | `get_monthly_budget()` | `src/ai/ai_provider_factory.py` | 354-363 | `get_monthly_budget() -> float` |
| 2 | `validate_order_analysis()` | `src/ai/prompts.py` | 483-488 | `validate_order_analysis(response: dict[str, Any]) -> bool` |
| 3 | `validate_alert_triage()` | `src/ai/prompts.py` | 491-496 | `validate_alert_triage(response: dict[str, Any]) -> bool` |
| 4 | `validate_backtest_review()` | `src/ai/prompts.py` | 499-504 | `validate_backtest_review(response: dict[str, Any]) -> bool` |
| 5 | `validate_signal_analysis()` | `src/ai/prompts.py` | 507-512 | `validate_signal_analysis(response: dict[str, Any]) -> bool` |
| 6 | `get_prompt()` | `src/ai/prompts.py` | 552-563 | `get_prompt(cls, prompt_type: str, version: str) -> str` |
| 7 | `auto_assign_colors()` | `src/chart_chat/chart_chat_actions_mixin.py` | 416-434 | `auto_assign_colors()` |
| 8 | `open_palette_dialog()` | `src/chart_chat/chart_chat_actions_mixin.py` | 436-468 | `open_palette_dialog()` |
| 9 | `draw_selected()` | `src/chart_chat/chart_chat_actions_mixin.py` | 503-571 | `draw_selected()` |
| 10 | `delete_selected()` | `src/chart_chat/chart_chat_actions_mixin.py` | 573-578 | `delete_selected()` |
| 11 | `clear_all()` | `src/chart_chat/chart_chat_actions_mixin.py` | 580-583 | `clear_all()` |
| 12 | `save_and_close()` | `src/chart_chat/chart_chat_actions_mixin.py` | 462-465 | `save_and_close()` |
| 13 | `current_symbol()` | `src/chart_chat/chat_service.py` | 68-70 | `current_symbol(self) -> str` |
| 14 | `current_timeframe()` | `src/chart_chat/chat_service.py` | 73-75 | `current_timeframe(self) -> str` |
| 15 | `model_name()` | `src/chart_chat/chat_service.py` | 78-82 | `model_name(self) -> str` |
| 16 | `conversation_history()` | `src/chart_chat/chat_service.py` | 85-87 | `conversation_history(self) -> list[ChatMessage]` |
| 17 | `get_chart_context()` | `src/chart_chat/chat_service.py` | 144-154 | `get_chart_context(self, lookback_bars: int) -> ChartContext` |
| 18 | `get_session_info()` | `src/chart_chat/chat_service.py` | 281-299 | `get_session_info(self) -> dict[str, Any]` |
| 19 | `list_charts_with_history()` | `src/chart_chat/history_store.py` | 162-181 | `list_charts_with_history(self) -> list[tuple[str, str]]` |
| 20 | `apply_ai_response()` | `src/chart_chat/markings_manager.py` | 45-65 | `apply_ai_response(self, response: CompactAnalysisResponse) -` |

*... und 298 weitere*

---

### ⚠️ Manuell prüfen (536 Funktionen)

**Diese Funktionen könnten false-positives sein (Event-Handler, Framework-Hooks, etc.):**

| # | Funktion | Datei | Zeilen | Warnung |
|---|----------|-------|--------|---------|
| 1 | `build_order_prompt()` | `src/ai/prompts.py` | 392-406 | Könnte Framework-Hook/Event-Handler sein |
| 2 | `build_alert_prompt()` | `src/ai/prompts.py` | 409-419 | Könnte Framework-Hook/Event-Handler sein |
| 3 | `build_signal_prompt()` | `src/ai/prompts.py` | 439-451 | Könnte Framework-Hook/Event-Handler sein |
| 4 | `_on_quick_action()` | `src/chart_chat/chart_chat_actions_mixin.py` | 65-78 | Könnte Framework-Hook/Event-Handler sein |
| 5 | `_on_analysis_complete()` | `src/chart_chat/chart_chat_actions_mixin.py` | 155-194 | Könnte Framework-Hook/Event-Handler sein |
| 6 | `_on_open_evaluation_popup()` | `src/chart_chat/chart_chat_actions_mixin.py` | 224-229 | Könnte Framework-Hook/Event-Handler sein |
| 7 | `on_color_double_click()` | `src/chart_chat/chart_chat_actions_mixin.py` | 391-402 | Könnte Framework-Hook/Event-Handler sein |
| 8 | `on_close()` | `src/chart_chat/chart_chat_actions_mixin.py` | 611-624 | Könnte Framework-Hook/Event-Handler sein |
| 9 | `_on_bars_changed()` | `src/chart_chat/chart_chat_events_mixin.py` | 40-48 | Könnte Framework-Hook/Event-Handler sein |
| 10 | `_on_all_bars_toggled()` | `src/chart_chat/chart_chat_events_mixin.py` | 49-71 | Könnte Framework-Hook/Event-Handler sein |
| 11 | `_on_export()` | `src/chart_chat/chart_chat_export_mixin.py` | 36-48 | Könnte Framework-Hook/Event-Handler sein |
| 12 | `_on_clear_history()` | `src/chart_chat/chart_chat_history_mixin.py` | 81-90 | Könnte Framework-Hook/Event-Handler sein |
| 13 | `_on_open_prompts_editor()` | `src/chart_chat/chart_chat_ui_mixin.py` | 203-208 | Könnte Framework-Hook/Event-Handler sein |
| 14 | `_build_toolbar_separator()` | `src/chart_chat/chart_chat_ui_mixin.py` | 210-215 | Private Funktion - könnte via Reflection aufgerufen werden |
| 15 | `_save()` | `src/chart_chat/prompts_editor_dialog.py` | 103-111 | Private Funktion - könnte via Reflection aufgerufen werden |
| 16 | `__enter__()` | `src/common/performance.py` | 264-267 | Könnte Framework-Hook/Event-Handler sein |
| 17 | `__exit__()` | `src/common/performance.py` | 269-271 | Könnte Framework-Hook/Event-Handler sein |
| 18 | `_on_analysis_finished()` | `src/ui/ai_analysis_window.py` | 381-399 | Könnte Framework-Hook/Event-Handler sein |
| 19 | `_open_prompt_editor()` | `src/ui/ai_analysis_window.py` | 416-444 | Private Funktion - könnte via Reflection aufgerufen werden |
| 20 | `_excepthook()` | `src/ui/app.py` | 127-130 | Private Funktion - könnte via Reflection aufgerufen werden |

*... und 516 weitere*

---

### 📦 Ungenutzte Imports (2453 total)

| # | Import | Datei | Zeile |
|---|--------|-------|-------|
| 1 | `__future__.annotations` | `src/ai/anthropic_service.py` | 7 |
| 2 | `asyncio` | `src/ai/anthropic_service.py` | 9 |
| 3 | `datetime.datetime` | `src/ai/anthropic_service.py` | 14 |
| 4 | `datetime.timedelta` | `src/ai/anthropic_service.py` | 14 |
| 5 | `typing.Any` | `src/ai/anthropic_service.py` | 15 |
| 6 | `pydantic.BaseModel` | `src/ai/anthropic_service.py` | 18 |
| 7 | `src.config.loader.AIConfig` | `src/ai/anthropic_service.py` | 28 |
| 8 | `src.ai.openai_service.OrderAnalysis` | `src/ai/anthropic_service.py` | 31 |
| 9 | `src.ai.openai_service.AlertTriageResult` | `src/ai/anthropic_service.py` | 31 |
| 10 | `src.ai.openai_service.BacktestReview` | `src/ai/anthropic_service.py` | 31 |
| 11 | `__future__.annotations` | `src/ai/gemini_service.py` | 12 |
| 12 | `typing.Any` | `src/ai/gemini_service.py` | 18 |
| 13 | `pydantic.BaseModel` | `src/ai/gemini_service.py` | 21 |
| 14 | `src.config.loader.AIConfig` | `src/ai/gemini_service.py` | 31 |
| 15 | `src.ai.openai_service.OrderAnalysis` | `src/ai/gemini_service.py` | 34 |
| 16 | `src.ai.openai_service.AlertTriageResult` | `src/ai/gemini_service.py` | 34 |
| 17 | `src.ai.openai_service.BacktestReview` | `src/ai/gemini_service.py` | 34 |
| 18 | `src.ai.openai_service.StrategyTradeAnalysis` | `src/ai/gemini_service.py` | 34 |
| 19 | `__future__.annotations` | `src/ai/openai_models.py` | 7 |
| 20 | `typing.Any` | `src/ai/openai_models.py` | 9 |

*... und 2433 weitere*

---

## 2. DUPLIKATE

### Exakte Duplikate

**Gefunden: 3986 Duplikat-Gruppen**


### Duplikat 1
- **Vorkommen:** 2x
- **Zeilen gespart:** 4 (bei Konsolidierung)

**Locations:**
- `src/ai/ai_provider_factory.py` (Zeilen 14-18)
- `src/core/simulator/excel_export.py` (Zeilen 14-18)

**Code-Vorschau:**
```python

logger = logging.getLogger(__name__)

# Load .env file if python-dotenv is available
try:

```


### Duplikat 2
- **Vorkommen:** 2x
- **Zeilen gespart:** 4 (bei Konsolidierung)

**Locations:**
- `src/ai/ai_provider_factory.py` (Zeilen 83-87)
- `src/ai/ai_provider_factory.py` (Zeilen 213-217)

**Code-Vorschau:**
```python

        Args:
            provider: Provider name ("OpenAI" or "Anthropic")

        Returns:

```


### Duplikat 3
- **Vorkommen:** 2x
- **Zeilen gespart:** 4 (bei Konsolidierung)

**Locations:**
- `src/ai/ai_provider_factory.py` (Zeilen 202-206)
- `src/ai/ai_provider_factory.py` (Zeilen 203-207)

**Code-Vorschau:**
```python

            # Unknown model - log warning but still try to use it
            # (OpenAI may have released new models)
            logger.warning(f"⚠️ Unknown model '{model}' for {provider}. Attemptin
```


### Duplikat 4
- **Vorkommen:** 2x
- **Zeilen gespart:** 4 (bei Konsolidierung)

**Locations:**
- `src/ai/ai_provider_factory.py` (Zeilen 257-261)
- `src/ai/__init__.py` (Zeilen 34-38)

**Code-Vorschau:**
```python

        Args:
            telemetry_callback: Optional callback for telemetry

        Returns:

```


### Duplikat 5
- **Vorkommen:** 2x
- **Zeilen gespart:** 4 (bei Konsolidierung)

**Locations:**
- `src/ai/ai_provider_factory.py` (Zeilen 258-262)
- `src/ai/__init__.py` (Zeilen 35-39)

**Code-Vorschau:**
```python
        Args:
            telemetry_callback: Optional callback for telemetry

        Returns:
            AI service instance (OpenAIService or AnthropicService)

```


### Duplikat 6
- **Vorkommen:** 2x
- **Zeilen gespart:** 4 (bei Konsolidierung)

**Locations:**
- `src/ai/ai_provider_factory.py` (Zeilen 259-263)
- `src/ai/__init__.py` (Zeilen 36-40)

**Code-Vorschau:**
```python
            telemetry_callback: Optional callback for telemetry

        Returns:
            AI service instance (OpenAIService or AnthropicService)


```


### Duplikat 7
- **Vorkommen:** 2x
- **Zeilen gespart:** 4 (bei Konsolidierung)

**Locations:**
- `src/ai/ai_provider_factory.py` (Zeilen 260-264)
- `src/ai/__init__.py` (Zeilen 37-41)

**Code-Vorschau:**
```python

        Returns:
            AI service instance (OpenAIService or AnthropicService)

        Raises:

```


### Duplikat 8
- **Vorkommen:** 2x
- **Zeilen gespart:** 4 (bei Konsolidierung)

**Locations:**
- `src/ai/ai_provider_factory.py` (Zeilen 277-281)
- `src/ai/ai_provider_factory.py` (Zeilen 278-282)

**Code-Vorschau:**
```python

        # Get provider
        provider = AIProviderFactory.get_provider()
        logger.info(f"Step 2: Provider = {provider}")


```


### Duplikat 9
- **Vorkommen:** 2x
- **Zeilen gespart:** 4 (bei Konsolidierung)

**Locations:**
- `src/ai/ai_provider_factory.py` (Zeilen 290-294)
- `src/ai/ai_provider_factory.py` (Zeilen 291-295)

**Code-Vorschau:**
```python

        # Get model
        model = AIProviderFactory.get_model(provider)
        logger.info(f"Step 4: Model = {model}")


```


### Duplikat 10
- **Vorkommen:** 3x
- **Zeilen gespart:** 8 (bei Konsolidierung)

**Locations:**
- `src/ai/ai_provider_factory.py` (Zeilen 314-318)
- `src/ai/ai_provider_factory.py` (Zeilen 330-334)
- `src/ai/ai_provider_factory.py` (Zeilen 342-346)

**Code-Vorschau:**
```python
                    config=ai_config,
                    api_key=api_key,
                    telemetry_callback=telemetry_callback
                )
                # Override default model if speci
```


---

## 3. KOMPLEXITÄT


### ⚠️ KRITISCHE Funktionen (Komplexität > 20)

**Anzahl:** 4

| # | Funktion | Datei | Komplexität | Verschachtelung | LOC | Empfehlung |
|---|----------|-------|-------------|-----------------|-----|------------|
| 1 | `_show_evaluation_popup()` | `src/chart_chat/chart_chat_actions_mixin.py` | **58** | 4 | 412 | In 3-5 Funktionen splitten |
| 2 | `update_data_provider_list()` | `src/ui/app_components/toolbar_mixin.py` | **25** | 3 | 111 | In 3-5 Funktionen splitten |
| 3 | `_apply_marking_to_chart()` | `src/chart_chat/markings_manager.py` | **24** | 9 | 53 | In 3-5 Funktionen splitten |
| 4 | `_aggregate_metrics()` | `src/core/tradingbot/strategy_evaluator.py` | **22** | 1 | 59 | In 3-5 Funktionen splitten |

---

### ⚠️ HOHE Komplexität (11-20)

**Anzahl:** 79

| # | Funktion | Datei | Komplexität | Verschachtelung | LOC |
|---|----------|-------|-------------|-----------------|-----|
| 1 | `validate_condition_references()` | `src/core/strategy/definition.py` | **20** | 3 | 63 |
| 2 | `_validate_product()` | `src/derivatives/ko_finder/adapter/normalizer.py` | **20** | 4 | 46 |
| 3 | `draw_selected()` | `src/chart_chat/chart_chat_actions_mixin.py` | **19** | 3 | 69 |
| 4 | `from_variable_string()` | `src/chart_chat/chart_markings.py` | **19** | 10 | 75 |
| 5 | `_on_chart_stop_line_moved()` | `src/ui/widgets/chart_window_mixins/bot_position_persistence_chart_mixin.py` | **19** | 6 | 72 |
| 6 | `_on_signals_table_cell_changed()` | `src/ui/widgets/chart_window_mixins/bot_position_persistence_chart_mixin.py` | **19** | 3 | 84 |
| 7 | `run()` | `src/chart_chat/chart_chat_worker.py` | **18** | 5 | 90 |
| 8 | `_load_ui_settings()` | `src/ui/dialogs/pattern_db_settings_mixin.py` | **18** | 3 | 81 |
| 9 | `_check_stops_on_candle_close()` | `src/ui/widgets/chart_window_mixins/bot_callbacks_candle_mixin.py` | **18** | 4 | 88 |
| 10 | `_restore_chart_state()` | `src/ui/widgets/chart_window_mixins/state_mixin.py` | **18** | 3 | 73 |
| 11 | `select_strategy()` | `src/core/tradingbot/strategy_selector.py` | **17** | 4 | 95 |
| 12 | `validate_chart_data()` | `src/ui/chart/chart_adapter.py` | **17** | 5 | 60 |
| 13 | `_update_signals_pnl()` | `src/ui/widgets/chart_window_mixins/bot_display_signals_mixin.py` | **17** | 5 | 53 |
| 14 | `_load_window_state()` | `src/ui/widgets/chart_window_mixins/state_mixin.py` | **17** | 4 | 66 |
| 15 | `draw_row()` | `src/chart_chat/chart_chat_actions_mixin.py` | **16** | 3 | 57 |
| 16 | `to_markdown()` | `src/chart_chat/models.py` | **16** | 2 | 94 |
| 17 | `_validate_bar()` | `src/core/market_data/bar_validator.py` | **16** | 3 | 111 |
| 18 | `_classify_volatility()` | `src/core/tradingbot/regime_engine.py` | **16** | 4 | 74 |
| 19 | `_parse_row()` | `src/derivatives/ko_finder/adapter/parser.py` | **16** | 2 | 80 |
| 20 | `_add_test_zone()` | `src/ui/widgets/embedded_tradingview_chart_marking_mixin.py` | **16** | 4 | 63 |

*... und 59 weitere*

---

### 🔁 Stark verschachtelte Funktionen (Nesting > 6)

**Anzahl:** 2

| # | Funktion | Datei | Verschachtelung | Komplexität | LOC |
|---|----------|-------|-----------------|-------------|-----|
| 1 | `from_variable_string()` | `src/chart_chat/chart_markings.py` | **10** | 19 | 75 |
| 2 | `_apply_marking_to_chart()` | `src/chart_chat/markings_manager.py` | **9** | 24 | 53 |

---

## 4. ZUSAMMENFASSUNG & EMPFEHLUNGEN

### Statistiken

| Kategorie | Anzahl | Status |
|-----------|--------|--------|
| **Dead Code (sicher)** | 318 | ⚠️ Zu entfernen |
| **Dead Code (unsicher)** | 536 | 🔍 Zu prüfen |
| **Ungenutzte Imports** | 2453 | 🧹 Zu entfernen |
| **Duplikat-Gruppen** | 3986 | ♻️ Zu konsolidieren |
| **Kritische Komplexität** | 4 | ⚠️ Zu refactoren |
| **Hohe Komplexität** | 79 | 🔍 Zu überwachen |
| **Stark verschachtelt** | 2 | 🔁 Zu vereinfachen |

---

### Empfohlene Aktionen (Priorität)

1. **HOCH: Dead Code entfernen**
   - 318 ungenutzte Funktionen löschen
   - 2453 ungenutzte Imports entfernen

2. **HOCH: Komplexität reduzieren**
   - 4 kritische Funktionen in kleinere Funktionen splitten

3. **MITTEL: Duplikate konsolidieren**
   - 3986 Duplikat-Gruppen zu gemeinsamen Funktionen extrahieren

4. **NIEDRIG: Verschachtelung reduzieren**
   - 2 Funktionen mit zu tiefer Verschachtelung vereinfachen

---

## ⏸️ WARTE AUF BESTÄTIGUNG

**Vor Phase 3 (Refactoring):**
- Prüfe die Analyse-Ergebnisse
- Bestätige welche Änderungen durchgeführt werden sollen
- Erstelle Backup (git commit)

**WICHTIG:** Keine Änderungen ohne explizite Bestätigung!

---

*Report generiert am 2026-01-06T07:59:45.541969*
