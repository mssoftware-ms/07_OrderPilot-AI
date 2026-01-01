# Code-Inventur Bericht

**Erstellt:** 2026-01-01T15:13:25.169456

**Projekt:** /mnt/d/03_GIT/02_Python/07_OrderPilot-AI


**Scope (excluded):** .git, .venv, .wsl_env, .wsl_venv, __pycache__, docs, node_modules, venv


## Übersicht

| Metrik | Wert |
|--------|------|
| Dateien | 405 |
| Gesamte Zeilen | 92,641 |
| Code-Zeilen | 70,895 |
| Funktionen | 2926 |
| Klassen | 646 |
| UI-Komponenten | 28 |
| Event-Handler | 66 |
| Imports | 2502 |

## Datei-Details

### 01_Projectplan/Bitunix_API/open-api-main/Demo/Python/config.py

- **Zeilen:** 83 (Code: 68)
- **Checksum:** `0f65d340e4a4057f553799f84748e76f`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `Config` (Zeile 5-83)

---

### 01_Projectplan/Bitunix_API/open-api-main/Demo/Python/error_codes.py

- **Zeilen:** 99 (Code: 88)
- **Checksum:** `20606ed8384e2ea587006c7df8c0bbf3`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `ErrorCode` (Zeile 3-99)

---

### 01_Projectplan/Bitunix_API/open-api-main/Demo/Python/open_api_http_future_private.py

- **Zeilen:** 261 (Code: 183)
- **Checksum:** `f675177125a340a9ed48336cff989f00`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `OpenApiHttpFuturePrivate` (Zeile 13-204)

**Top-Level Funktionen:**
- `async main()` (Zeile 206)

---

### 01_Projectplan/Bitunix_API/open-api-main/Demo/Python/open_api_http_future_public.py

- **Zeilen:** 172 (Code: 129)
- **Checksum:** `88657ae108ed2ebaf6c5010b361b2066`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `OpenApiHttpFuturePublic` (Zeile 13-139)

**Top-Level Funktionen:**
- `async main()` (Zeile 141)

---

### 01_Projectplan/Bitunix_API/open-api-main/Demo/Python/open_api_http_sign.py

- **Zeilen:** 101 (Code: 86)
- **Checksum:** `2483cfe9eb6dce64a7d157a708be0c89`
- **Funktionen:** 5
- **Klassen:** 0

**Top-Level Funktionen:**
- `get_nonce() -> str` (Zeile 6)
- `get_timestamp() -> str` (Zeile 15)
- `generate_signature(api_key: str, secret_key: str, nonce: str, timestamp: str, query_params: str, body: str) -> str` (Zeile 24)
- `get_auth_headers(api_key: str, secret_key: str, query_params: str, body: str) -> Dict[str, str]` (Zeile 50)
- `sort_params(params: Dict[str, str]) -> str` (Zeile 87)

---

### 01_Projectplan/Bitunix_API/open-api-main/Demo/Python/open_api_ws_future_private.py

- **Zeilen:** 305 (Code: 251)
- **Checksum:** `59e718f816f255ca12231513fb686b11`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `OpenApiWsFuturePrivate` (Zeile 14-276)

**Top-Level Funktionen:**
- `async main()` (Zeile 278)

---

### 01_Projectplan/Bitunix_API/open-api-main/Demo/Python/open_api_ws_future_public.py

- **Zeilen:** 227 (Code: 180)
- **Checksum:** `b64c5171545dc9344e652c92a8263c6b`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `OpenApiWsFuturePublic` (Zeile 13-198)

**Top-Level Funktionen:**
- `async main()` (Zeile 200)

---

### 01_Projectplan/Bitunix_API/open-api-main/Demo/Python/open_api_ws_sign.py

- **Zeilen:** 40 (Code: 32)
- **Checksum:** `58d2c5ae07f3637af7537922659edf88`
- **Funktionen:** 5
- **Klassen:** 0

**Top-Level Funktionen:**
- `generate_nonce()` (Zeile 8)
- `generate_timestamp()` (Zeile 12)
- `sha256_hex(input_string)` (Zeile 16)
- `generate_sign(nonce, timestamp, api_key, secret_key)` (Zeile 20)
- `get_auth_ws_future(api_key, secret_key)` (Zeile 28)

---

### 01_Projectplan/pyOnvista-master/sample.py

- **Zeilen:** 31 (Code: 24)
- **Checksum:** `db9ab8517741da1f5d306ed6cf098980`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `async main()` (Zeile 11)

---

### 01_Projectplan/pyOnvista-master/src/pyonvista/__init__.py

- **Zeilen:** 6 (Code: 4)
- **Checksum:** `e91db84973fdc8e023eae501d6cfbeac`
- **Funktionen:** 0
- **Klassen:** 0

---

### 01_Projectplan/pyOnvista-master/src/pyonvista/api.py

- **Zeilen:** 303 (Code: 257)
- **Checksum:** `6f517e20917ed0fe85e283bdc23e8788`
- **Funktionen:** 13
- **Klassen:** 5

**Klassen:**
- `Quote` (Zeile 33-68)
- `Market` (Zeile 72-75)
- `Notation` (Zeile 79-81)
- `Instrument` (Zeile 85-128)
- `PyOnVista` (Zeile 166-302)

**Top-Level Funktionen:**
- `_update_instrument(instrument: Instrument, data: dict, quote: dict)` (Zeile 131)
- `_add_notation(instrument: Instrument, notations: dict)` (Zeile 153)

---

### 01_Projectplan/pyOnvista-master/src/pyonvista/util.py

- **Zeilen:** 12 (Code: 11)
- **Checksum:** `74c3a4a97592990759abee7b5844a2be`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `make_url(base_url, *res, **params)` (Zeile 6)

---

### 01_Projectplan/pyOnvista-master/test/conftest.py

- **Zeilen:** 35 (Code: 24)
- **Checksum:** `5df777b5c48e237505746d3bf305b7d9`
- **Funktionen:** 4
- **Klassen:** 0

**Top-Level Funktionen:**
- `async aio_client() -> aiohttp.ClientSession` (Zeile 12)
- `async onvista_api(aio_client) -> PyOnVista` (Zeile 19)
- `instrument_vw() -> Instrument` (Zeile 26)
- `instrument_etf() -> Instrument` (Zeile 32)

---

### 01_Projectplan/pyOnvista-master/test/run_coverage.py

- **Zeilen:** 16 (Code: 12)
- **Checksum:** `09c73244d1627705bf2587ec1efe0808`
- **Funktionen:** 0
- **Klassen:** 0

---

### 01_Projectplan/pyOnvista-master/test/test_api.py

- **Zeilen:** 55 (Code: 42)
- **Checksum:** `42b3925fecb5d99a3f43223e80694927`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `TestPyOnVista` (Zeile 9-54)

---

### 01_Projectplan/pyOnvista-master/test/test_instrument.py

- **Zeilen:** 9 (Code: 5)
- **Checksum:** `dce072ac9ac53f57960f522d7ff9137f`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `TestInstrument` (Zeile 5-8)

---

### analyze_loc.py

- **Zeilen:** 155 (Code: 127)
- **Checksum:** `778aeaff6f9ad72fe9038e375202584a`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `FileAnalysis` (Zeile 12-22)

**Top-Level Funktionen:**
- `count_productive_loc(filepath: str) -> FileAnalysis` (Zeile 24)
- `main()` (Zeile 91)

---

### examples/alpaca_realtime_demo.py

- **Zeilen:** 377 (Code: 281)
- **Checksum:** `2c2aae6b63e35743b1da18528bbc9beb`
- **Funktionen:** 12
- **Klassen:** 1

**Klassen:**
- `AlpacaDemo` (Zeile 44-302)

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

**Top-Level Funktionen:**
- `main()` (Zeile 263)

---

### examples/realtime_indicators_demo.py

- **Zeilen:** 309 (Code: 226)
- **Checksum:** `80efaa45fde385ba63de20c4cb0e213b`
- **Funktionen:** 12
- **Klassen:** 1

**Klassen:**
- `RealtimeDemo` (Zeile 46-273)

**Top-Level Funktionen:**
- `async main()` (Zeile 276)

---

### main.py

- **Zeilen:** 23 (Code: 15)
- **Checksum:** `6d7c3489ca57f9549b9f329788be1d32`
- **Funktionen:** 0
- **Klassen:** 0

---

### refactoring_inventory.py

- **Zeilen:** 272 (Code: 215)
- **Checksum:** `46c151e0a529615ccd891b23cfc70ee7`
- **Funktionen:** 9
- **Klassen:** 0

**Top-Level Funktionen:**
- `calculate_file_checksum(file_path: str) -> str` (Zeile 20)
- `count_code_lines(source_code: str) -> int` (Zeile 25)
- `analyze_file(file_path: str) -> Optional[FileInventory]` (Zeile 50)
- `find_python_files(root_dir: str, exclude_patterns: List[str]) -> List[str]` (Zeile 81)
- `create_inventory(project_root: str, output_file: str) -> ProjectInventory` (Zeile 96)
- `save_inventory(inventory: ProjectInventory, output_file: str)` (Zeile 148)
- `print_summary(inventory: ProjectInventory)` (Zeile 170)
- `create_detailed_report(inventory: ProjectInventory, output_file: str)` (Zeile 213)
- `convert_to_dict(obj)` (Zeile 150)

---

### refactoring_inventory_analyzer.py

- **Zeilen:** 303 (Code: 252)
- **Checksum:** `b884e28be01ab72d2d525ebd9f612e12`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `InventoryAnalyzer` (Zeile 15-302)

---

### refactoring_inventory_models.py

- **Zeilen:** 84 (Code: 75)
- **Checksum:** `074b74625066f1f0a58cc1ad6b6ac1b3`
- **Funktionen:** 0
- **Klassen:** 7

**Klassen:**
- `FunctionInfo` (Zeile 6-16)
- `ClassInfo` (Zeile 18-28)
- `ImportInfo` (Zeile 30-36)
- `EventHandlerInfo` (Zeile 38-44)
- `UIComponentInfo` (Zeile 46-55)
- `FileInventory` (Zeile 57-69)
- `ProjectInventory` (Zeile 71-83)

---

### run_app.py

- **Zeilen:** 19 (Code: 8)
- **Checksum:** `73df03840a3544cb6bde571ae965f106`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/__init__.py

- **Zeilen:** 5 (Code: 4)
- **Checksum:** `df35880aad0e0fc8690e709d6c55e656`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ai/__init__.py

- **Zeilen:** 90 (Code: 67)
- **Checksum:** `0b94cd0d656ae64872042d68e071feb4`
- **Funktionen:** 2
- **Klassen:** 0

**Top-Level Funktionen:**
- `async get_ai_service(telemetry_callback)` (Zeile 29)
- `reset_ai_service()` (Zeile 56)

---

### src/ai/ai_provider_factory.py

- **Zeilen:** 362 (Code: 266)
- **Checksum:** `108bbce06828b7090186475c08170200`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `AIProviderFactory` (Zeile 29-361)

---

### src/ai/anthropic_service.py

- **Zeilen:** 357 (Code: 259)
- **Checksum:** `d825471756339b6c93a6568186983d7f`
- **Funktionen:** 12
- **Klassen:** 1

**Klassen:**
- `AnthropicService` (Zeile 48-356)

---

### src/ai/gemini_service.py

- **Zeilen:** 430 (Code: 310)
- **Checksum:** `1a90770b4e47cbaf9fbb9262fbe57b52`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `GeminiService` (Zeile 52-429)

---

### src/ai/openai_models.py

- **Zeilen:** 143 (Code: 79)
- **Checksum:** `c4cdd7857098808adf1517fbe13b32b7`
- **Funktionen:** 0
- **Klassen:** 9

**Klassen:**
- `OpenAIError` (Zeile 16-18)
- `RateLimitError` (Zeile 21-23)
- `QuotaExceededError` (Zeile 26-28)
- `SchemaValidationError` (Zeile 31-33)
- `OrderAnalysis` (Zeile 38-56)
- `AlertTriageResult` (Zeile 59-74)
- `BacktestReview` (Zeile 77-96)
- `StrategySignalAnalysis` (Zeile 99-114)
- `StrategyTradeAnalysis` (Zeile 117-142)

---

### src/ai/openai_service.py

- **Zeilen:** 113 (Code: 87)
- **Checksum:** `44d8e1a20f31a5770d14d5a217bcb2b0`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `OpenAIService` (Zeile 46-90)

**Top-Level Funktionen:**
- `async get_openai_service(config: AIConfig, api_key: str) -> OpenAIService` (Zeile 93)

---

### src/ai/openai_service_analysis_mixin.py

- **Zeilen:** 172 (Code: 150)
- **Checksum:** `9533d58d6da601d24f36b9da954d1568`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `OpenAIServiceAnalysisMixin` (Zeile 41-171)

---

### src/ai/openai_service_client_mixin.py

- **Zeilen:** 344 (Code: 263)
- **Checksum:** `f119a9549a89ccb0c0ed6ba880b084c7`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `OpenAIServiceClientMixin` (Zeile 41-343)

---

### src/ai/openai_service_prompt_mixin.py

- **Zeilen:** 157 (Code: 130)
- **Checksum:** `14f4203f71440077d6b44efb67694eba`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `OpenAIServicePromptMixin` (Zeile 41-156)

---

### src/ai/openai_utils.py

- **Zeilen:** 180 (Code: 132)
- **Checksum:** `355563252205343621132b3d297f3000`
- **Funktionen:** 7
- **Klassen:** 2

**Klassen:**
- `CostTracker` (Zeile 23-96)
- `CacheManager` (Zeile 101-179)

---

### src/ai/prompts.py

- **Zeilen:** 563 (Code: 479)
- **Checksum:** `4be9bca2b2a349653847c037f0dc62fc`
- **Funktionen:** 11
- **Klassen:** 5

**Klassen:**
- `PromptTemplates` (Zeile 10-128)
- `JSONSchemas` (Zeile 133-383)
- `PromptBuilder` (Zeile 388-474)
- `SchemaValidator` (Zeile 479-524)
- `PromptVersion` (Zeile 529-563)

---

### src/ai/provider_base.py

- **Zeilen:** 109 (Code: 85)
- **Checksum:** `82183aac63f90afed802c973d2d05673`
- **Funktionen:** 5
- **Klassen:** 4

**Klassen:**
- `AIProvider` (Zeile 22-26)
- `ReasoningMode` (Zeile 29-35)
- `ProviderConfig` (Zeile 38-47)
- `AIProviderBase` (Zeile 50-108)

---

### src/ai/provider_gemini.py

- **Zeilen:** 172 (Code: 126)
- **Checksum:** `7f0082f7f7ad48f28cad2753a7108a67`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `GeminiProvider` (Zeile 25-171)

---

### src/ai/providers.py

- **Zeilen:** 432 (Code: 333)
- **Checksum:** `6e0a092048c7e06aba2aea8baab2e786`
- **Funktionen:** 12
- **Klassen:** 2

**Klassen:**
- `OpenAIProvider` (Zeile 56-193)
- `AnthropicProvider` (Zeile 196-335)

**Top-Level Funktionen:**
- `create_provider(provider: AIProvider, model: str, **kwargs) -> AIProviderBase` (Zeile 340)
- `async get_openai_gpt51_thinking(**kwargs) -> OpenAIProvider` (Zeile 387)
- `async get_openai_gpt51_instant(**kwargs) -> OpenAIProvider` (Zeile 397)
- `async get_anthropic_sonnet45(**kwargs) -> AnthropicProvider` (Zeile 407)
- `async get_gemini_flash(**kwargs) -> GeminiProvider` (Zeile 416)
- `async get_gemini_pro(**kwargs) -> GeminiProvider` (Zeile 425)

---

### src/backtesting/__init__.py

- **Zeilen:** 2 (Code: 1)
- **Checksum:** `7e816b25502188912a5ea444b8a5b6ca`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/chart_chat/__init__.py

- **Zeilen:** 62 (Code: 52)
- **Checksum:** `2b0d910d301c6799e9dcbfa5ebbd6e89`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/chart_chat/analyzer.py

- **Zeilen:** 439 (Code: 353)
- **Checksum:** `8293244e8b7da3ece67188d71ab04977`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `ChartAnalyzer` (Zeile 40-438)

---

### src/chart_chat/chart_chat_actions_mixin.py

- **Zeilen:** 132 (Code: 111)
- **Checksum:** `ee15bf7c2cf93fa26a629569a07e1c31`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `ChartChatActionsMixin` (Zeile 36-131)

---

### src/chart_chat/chart_chat_events_mixin.py

- **Zeilen:** 96 (Code: 78)
- **Checksum:** `93672227b8c5f575dbdf01e69512b688`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `ChartChatEventsMixin` (Zeile 36-95)

---

### src/chart_chat/chart_chat_export_mixin.py

- **Zeilen:** 83 (Code: 71)
- **Checksum:** `98e053466e29a69942d789336c368842`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `ChartChatExportMixin` (Zeile 36-82)

---

### src/chart_chat/chart_chat_history_mixin.py

- **Zeilen:** 87 (Code: 69)
- **Checksum:** `8d8c8cb0c96feec36f1f86247e92662d`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `ChartChatHistoryMixin` (Zeile 36-86)

---

### src/chart_chat/chart_chat_ui_mixin.py

- **Zeilen:** 391 (Code: 327)
- **Checksum:** `dda7840eadb9e7bc4584ee9b6198008c`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `ChartChatUIMixin` (Zeile 36-390)

---

### src/chart_chat/chart_chat_worker.py

- **Zeilen:** 76 (Code: 63)
- **Checksum:** `5ec57ace14f81c0e54387e216f0c143e`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `AnalysisWorker` (Zeile 35-75)

---

### src/chart_chat/chat_service.py

- **Zeilen:** 301 (Code: 225)
- **Checksum:** `862241eb05dfff8a51cc1108c3370cc2`
- **Funktionen:** 16
- **Klassen:** 1

**Klassen:**
- `ChartChatService` (Zeile 30-300)

---

### src/chart_chat/context_builder.py

- **Zeilen:** 392 (Code: 288)
- **Checksum:** `adc118ce31bb7d298bd5414a5d113915`
- **Funktionen:** 14
- **Klassen:** 2

**Klassen:**
- `ChartContext` (Zeile 21-108)
- `ChartContextBuilder` (Zeile 111-391)

---

### src/chart_chat/history_store.py

- **Zeilen:** 236 (Code: 182)
- **Checksum:** `d192d11c9ea3b600555ba7382da14b8f`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `HistoryStore` (Zeile 22-235)

---

### src/chart_chat/mixin.py

- **Zeilen:** 262 (Code: 194)
- **Checksum:** `011e70812183bbc0a6825fbf4670c1af`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `ChartChatMixin` (Zeile 19-261)

---

### src/chart_chat/models.py

- **Zeilen:** 205 (Code: 144)
- **Checksum:** `af7b19630c0b82ff42a07803dced1651`
- **Funktionen:** 1
- **Klassen:** 11

**Klassen:**
- `MessageRole` (Zeile 17-22)
- `ChatMessage` (Zeile 25-35)
- `TrendDirection` (Zeile 38-43)
- `SignalStrength` (Zeile 46-51)
- `SupportResistanceLevel` (Zeile 54-61)
- `EntryExitRecommendation` (Zeile 64-71)
- `RiskAssessment` (Zeile 74-82)
- `PatternInfo` (Zeile 85-91)
- `ChartAnalysisResult` (Zeile 94-196)
- `QuickAnswerResult` (Zeile 199-204)
- `Config` (Zeile 34-35)

---

### src/chart_chat/prompts.py

- **Zeilen:** 198 (Code: 152)
- **Checksum:** `4ebaacc96db11f7d4311281812b14e2d`
- **Funktionen:** 3
- **Klassen:** 0

**Top-Level Funktionen:**
- `build_analysis_prompt(symbol: str, timeframe: str, current_price: float, ohlcv_summary: str, indicators: str, price_change_pct: float, volatility_atr: float | None, volume_trend: str, recent_high: float, recent_low: float, lookback: int) -> str` (Zeile 129)
- `build_conversation_prompt(symbol: str, timeframe: str, current_price: float, indicators: str, history: str, question: str) -> str` (Zeile 158)
- `format_conversation_history(messages: list, max_messages: int) -> str` (Zeile 177)

---

### src/chart_chat/widget.py

- **Zeilen:** 60 (Code: 44)
- **Checksum:** `3578f1bc4fd8f993421b34f96611b207`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `ChartChatWidget` (Zeile 25-59) 🖥️

---

### src/chart_marking/__init__.py

- **Zeilen:** 82 (Code: 65)
- **Checksum:** `28ecd0baadc59847cbbe4abe6b5a16fb`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/chart_marking/constants.py

- **Zeilen:** 104 (Code: 68)
- **Checksum:** `20c842d52d888df9ca2778b3eacee607`
- **Funktionen:** 0
- **Klassen:** 5

**Klassen:**
- `Colors` (Zeile 9-42)
- `LineStyles` (Zeile 45-55)
- `MarkerSizes` (Zeile 58-68)
- `ZoneDefaults` (Zeile 71-76)
- `LayoutDefaults` (Zeile 79-85)

---

### src/chart_marking/lines/__init__.py

- **Zeilen:** 6 (Code: 3)
- **Checksum:** `6b6a6839e990ba1379712a7f960fa436`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/chart_marking/lines/stop_loss_line.py

- **Zeilen:** 329 (Code: 271)
- **Checksum:** `a6cfcd8ce9ad3207739c357ae199af29`
- **Funktionen:** 17
- **Klassen:** 1

**Klassen:**
- `StopLossLineManager` (Zeile 17-328)

---

### src/chart_marking/markers/__init__.py

- **Zeilen:** 7 (Code: 4)
- **Checksum:** `fe2dfd870ee4260d90cb48d97ec891ba`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/chart_marking/markers/entry_markers.py

- **Zeilen:** 200 (Code: 158)
- **Checksum:** `821de147a3d881d603420159c97a9d37`
- **Funktionen:** 14
- **Klassen:** 1

**Klassen:**
- `EntryMarkerManager` (Zeile 17-199)

---

### src/chart_marking/markers/structure_markers.py

- **Zeilen:** 253 (Code: 202)
- **Checksum:** `a880595f2b708d2632b551353ccdabe6`
- **Funktionen:** 17
- **Klassen:** 1

**Klassen:**
- `StructureMarkerManager` (Zeile 17-252)

---

### src/chart_marking/mixin/__init__.py

- **Zeilen:** 6 (Code: 3)
- **Checksum:** `240bcf3af253b0cde200a417dbfaa493`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/chart_marking/mixin/chart_marking_mixin.py

- **Zeilen:** 558 (Code: 446)
- **Checksum:** `9b788c60504a2b9c315f756e34b92825`
- **Funktionen:** 46
- **Klassen:** 1

**Klassen:**
- `ChartMarkingMixin` (Zeile 28-557)

---

### src/chart_marking/models.py

- **Zeilen:** 463 (Code: 387)
- **Checksum:** `8b2d6086b20f7620538f070dc535fd5d`
- **Funktionen:** 19
- **Klassen:** 12

**Klassen:**
- `MarkerShape` (Zeile 19-27)
- `MarkerPosition` (Zeile 30-35)
- `Direction` (Zeile 38-44)
- `ZoneType` (Zeile 47-53)
- `StructureBreakType` (Zeile 56-61)
- `LineStyle` (Zeile 64-69)
- `EntryMarker` (Zeile 80-139)
- `Zone` (Zeile 143-234)
- `StructureBreakMarker` (Zeile 238-304)
- `StopLossLine` (Zeile 308-378)
- `ChartConfig` (Zeile 382-414)
- `MultiChartLayout` (Zeile 418-462)

**Top-Level Funktionen:**
- `_normalize_timestamp(ts: int | datetime) -> int` (Zeile 72)

---

### src/chart_marking/multi_chart/__init__.py

- **Zeilen:** 18 (Code: 13)
- **Checksum:** `a5c15cde27535d1e5b11571b5320e81f`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/chart_marking/multi_chart/crosshair_sync.py

- **Zeilen:** 222 (Code: 178)
- **Checksum:** `3aa91525c69179d043aacf0d7209aaaa`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `CrosshairSyncManager` (Zeile 19-153)

**Top-Level Funktionen:**
- `get_crosshair_sync_javascript() -> str` (Zeile 215)

---

### src/chart_marking/multi_chart/layout_manager.py

- **Zeilen:** 309 (Code: 251)
- **Checksum:** `213e46497559bba814f3b304dd5340c7`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `LayoutManager` (Zeile 27-308)

---

### src/chart_marking/multi_chart/multi_monitor_manager.py

- **Zeilen:** 363 (Code: 272)
- **Checksum:** `fb71459e0d59dbefc9f44a3fe607f6b8`
- **Funktionen:** 15
- **Klassen:** 1

**Klassen:**
- `MultiMonitorChartManager` (Zeile 22-362)

---

### src/chart_marking/zones/__init__.py

- **Zeilen:** 6 (Code: 3)
- **Checksum:** `4a51fa881001e84e3b18984537309fd6`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/chart_marking/zones/support_resistance.py

- **Zeilen:** 428 (Code: 349)
- **Checksum:** `08d40bdab3187c0ec2b9b3deeb85ec08`
- **Funktionen:** 24
- **Klassen:** 1

**Klassen:**
- `ZoneManager` (Zeile 17-427)

---

### src/chart_marking/zones/zone_primitive_js.py

- **Zeilen:** 396 (Code: 336)
- **Checksum:** `23a4754f58be7fbf4f8d5f254cb4f6cc`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `get_zone_javascript() -> str` (Zeile 389)

---

### src/common/__init__.py

- **Zeilen:** 20 (Code: 17)
- **Checksum:** `4ac0ad1554f52b9f35ca92ef4e05b436`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/common/event_bus.py

- **Zeilen:** 258 (Code: 191)
- **Checksum:** `a2290a033d4f721b4bac406f33626197`
- **Funktionen:** 9
- **Klassen:** 5

**Klassen:**
- `EventType` (Zeile 21-85)
- `Event` (Zeile 89-95)
- `OrderEvent` (Zeile 99-120)
- `ExecutionEvent` (Zeile 124-145)
- `EventBus` (Zeile 148-248)

---

### src/common/logging_setup.py

- **Zeilen:** 293 (Code: 226)
- **Checksum:** `6088b7becc4ffab22fba3ef03a9efcc8`
- **Funktionen:** 10
- **Klassen:** 2

**Klassen:**
- `AITelemetryFilter` (Zeile 26-42)
- `TradingJsonFormatter` (Zeile 45-66)

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
- **Checksum:** `7c34b6a0403f028568b030050f75e9d4`
- **Funktionen:** 21
- **Klassen:** 2

**Klassen:**
- `PerformanceMonitor` (Zeile 17-135)
- `PerformanceTimer` (Zeile 228-271)

**Top-Level Funktionen:**
- `monitor_performance(operation: str | None)` (Zeile 142)
- `log_performance(operation: str, threshold_ms: float) -> Callable` (Zeile 176)
- `decorator(func: Callable) -> Callable` (Zeile 153)
- `decorator(func: Callable) -> Callable` (Zeile 188)
- `async async_wrapper(*args, **kwargs) -> Any` (Zeile 157)
- `sync_wrapper(*args, **kwargs) -> Any` (Zeile 162)
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

- **Zeilen:** 288 (Code: 208)
- **Checksum:** `d55dc4d6f7da110aaa3af5278fa8f438`
- **Funktionen:** 16
- **Klassen:** 4

**Klassen:**
- `SecurityLevel` (Zeile 22-27)
- `SecurityAction` (Zeile 30-43)
- `SecurityContext` (Zeile 47-60)
- `RateLimiter` (Zeile 63-145)

**Top-Level Funktionen:**
- `hash_password(password: str, salt: Optional[str]) -> tuple[str, str]` (Zeile 148)
- `verify_password(password: str, stored_hash: str, salt: str) -> bool` (Zeile 172)
- `generate_api_key() -> str` (Zeile 187)
- `validate_api_key(api_key: str) -> bool` (Zeile 196)
- `rate_limit(key: str, max_requests: int, window_seconds: int) -> Callable` (Zeile 221)
- `is_strong_password(password: str) -> bool` (Zeile 248)
- `sanitize_input(value: str, max_length: int) -> str` (Zeile 268)
- `decorator(func)` (Zeile 234)
- `wrapper(*args, **kwargs)` (Zeile 235)

---

### src/common/security_manager.py

- **Zeilen:** 425 (Code: 308)
- **Checksum:** `b4840057171bd012cc183d2d8d17e744`
- **Funktionen:** 21
- **Klassen:** 3

**Klassen:**
- `EncryptionManager` (Zeile 37-162)
- `CredentialManager` (Zeile 165-326)
- `SessionManager` (Zeile 329-392)

**Top-Level Funktionen:**
- `require_auth(security_level: SecurityLevel)` (Zeile 397)
- `decorator(func)` (Zeile 403)
- `wrapper(*args, **kwargs)` (Zeile 405)

---

### src/config/__init__.py

- **Zeilen:** 49 (Code: 42)
- **Checksum:** `f212c22abc6af11a7b5ab78443e651e6`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/config/config_types.py

- **Zeilen:** 207 (Code: 169)
- **Checksum:** `cb22d50c207061d6346dc34caf88ce3b`
- **Funktionen:** 0
- **Klassen:** 13

**Klassen:**
- `TradingEnvironment` (Zeile 12-16)
- `TradingMode` (Zeile 19-28)
- `BrokerType` (Zeile 31-39)
- `BrokerConfig` (Zeile 44-55)
- `DatabaseConfig` (Zeile 58-71)
- `MarketDataProviderConfig` (Zeile 74-80)
- `AIConfig` (Zeile 83-100)
- `TradingConfig` (Zeile 103-117)
- `BacktestConfig` (Zeile 120-131)
- `AlertConfig` (Zeile 134-149)
- `UIConfig` (Zeile 152-167)
- `MonitoringConfig` (Zeile 170-182)
- `ExecutionConfig` (Zeile 185-199)

---

### src/config/loader.py

- **Zeilen:** 291 (Code: 223)
- **Checksum:** `9d98c70203f7847be8269d41b0401b18`
- **Funktionen:** 10
- **Klassen:** 2

**Klassen:**
- `AppSettings` (Zeile 66-79)
- `ConfigManager` (Zeile 82-286)

---

### src/config/profile_config.py

- **Zeilen:** 290 (Code: 242)
- **Checksum:** `e63583d12c52627482009c010e7528b5`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `ProfileConfig` (Zeile 33-289)

---

### src/core/__init__.py

- **Zeilen:** 10 (Code: 8)
- **Checksum:** `8af395c5e5b643487ef2e035226d6734`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/alerts/__init__.py

- **Zeilen:** 2 (Code: 1)
- **Checksum:** `7e816b25502188912a5ea444b8a5b6ca`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/backtesting/__init__.py

- **Zeilen:** 43 (Code: 30)
- **Checksum:** `6edd69969f826324e26caee64329fc1e`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/backtesting/backtrader_integration.py

- **Zeilen:** 536 (Code: 407)
- **Checksum:** `cd791f12cb4f7fa3fde706baddca86ac`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `BacktestEngine` (Zeile 52-535)

---

### src/core/backtesting/backtrader_strategy.py

- **Zeilen:** 239 (Code: 172)
- **Checksum:** `7714ea100a77ffe3acbaf2fa4dbc81a4`
- **Funktionen:** 9
- **Klassen:** 2

**Klassen:**
- `OrderPilotStrategy` (Zeile 28-231)
- `OrderPilotStrategy` (Zeile 235-238)

---

### src/core/backtesting/backtrader_types.py

- **Zeilen:** 62 (Code: 51)
- **Checksum:** `b44c8dd4ce23d51638b8bd96dc0adfd8`
- **Funktionen:** 1
- **Klassen:** 2

**Klassen:**
- `BacktestConfig` (Zeile 18-35)
- `BacktestResultLegacy` (Zeile 39-61)

---

### src/core/backtesting/optimization.py

- **Zeilen:** 561 (Code: 406)
- **Checksum:** `e3b91764362f3fc53b16c23b5fee080b`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `ParameterOptimizer` (Zeile 44-516)

**Top-Level Funktionen:**
- `async quick_optimize(backtest_runner: Callable, parameter_ranges: dict[str, list[Any]], base_params: dict[str, Any] | None, primary_metric: str) -> OptimizationResult` (Zeile 521)

---

### src/core/backtesting/optimization_types.py

- **Zeilen:** 88 (Code: 70)
- **Checksum:** `4bba09f6715625ee289d607da0336bd5`
- **Funktionen:** 0
- **Klassen:** 6

**Klassen:**
- `ParameterRange` (Zeile 16-20)
- `OptimizationMetric` (Zeile 23-27)
- `ParameterTest` (Zeile 30-36)
- `OptimizationResult` (Zeile 39-51)
- `AIOptimizationInsight` (Zeile 54-74)
- `OptimizerConfig` (Zeile 78-87)

---

### src/core/backtesting/result_converter.py

- **Zeilen:** 471 (Code: 324)
- **Checksum:** `b719db5f5a878b4ff5d6741318e9d6ba`
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
- **Checksum:** `11f29f267e6f89e1e8f99b39d1b45cd0`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/broker/alpaca_adapter.py

- **Zeilen:** 494 (Code: 402)
- **Checksum:** `e21eb9d0e6734aa916494864f1dcb61f`
- **Funktionen:** 14
- **Klassen:** 1

**Klassen:**
- `AlpacaAdapter` (Zeile 40-493)

---

### src/core/broker/base.py

- **Zeilen:** 407 (Code: 290)
- **Checksum:** `6e01342bba1cce3552420be736aa34f9`
- **Funktionen:** 23
- **Klassen:** 1

**Klassen:**
- `BrokerAdapter` (Zeile 58-407)

---

### src/core/broker/broker_types.py

- **Zeilen:** 316 (Code: 202)
- **Checksum:** `90e0f0d0b5ce2b6c47dc4dd5b0dee321`
- **Funktionen:** 9
- **Klassen:** 13

**Klassen:**
- `BrokerError` (Zeile 21-27)
- `BrokerConnectionError` (Zeile 30-32)
- `OrderValidationError` (Zeile 35-37)
- `InsufficientFundsError` (Zeile 40-42)
- `RateLimitError` (Zeile 45-47)
- `OrderRequest` (Zeile 52-97)
- `OrderResponse` (Zeile 100-127)
- `Position` (Zeile 130-155)
- `Balance` (Zeile 158-179)
- `FeeModel` (Zeile 182-213)
- `AIAnalysisRequest` (Zeile 218-240)
- `AIAnalysisResult` (Zeile 243-269)
- `TokenBucketRateLimiter` (Zeile 274-315)

---

### src/core/broker/ibkr_adapter.py

- **Zeilen:** 524 (Code: 394)
- **Checksum:** `79e6585f297eea4b5276d3f558b0bb56`
- **Funktionen:** 27
- **Klassen:** 3

**Klassen:**
- `IBKRWrapper` (Zeile 35-145)
- `IBKRClient` (Zeile 148-152)
- `IBKRAdapter` (Zeile 155-524)

---

### src/core/broker/mock_broker.py

- **Zeilen:** 300 (Code: 234)
- **Checksum:** `3a70e9a819baeaec323dfec15abed87a`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `MockBroker` (Zeile 30-300)

---

### src/core/broker/trade_republic_adapter.py

- **Zeilen:** 488 (Code: 384)
- **Checksum:** `4dba5b45bf142ac98b35d35be09b9271`
- **Funktionen:** 23
- **Klassen:** 1

**Klassen:**
- `TradeRepublicAdapter` (Zeile 36-488)

---

### src/core/execution/__init__.py

- **Zeilen:** 18 (Code: 14)
- **Checksum:** `d822b4e9d596dffc5a4d9e4946b2125d`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/execution/engine.py

- **Zeilen:** 576 (Code: 444)
- **Checksum:** `60b503627a5e2922554acd03332f00c1`
- **Funktionen:** 17
- **Klassen:** 3

**Klassen:**
- `ExecutionState` (Zeile 26-32)
- `ExecutionTask` (Zeile 36-53)
- `ExecutionEngine` (Zeile 56-576)

---

### src/core/execution/events.py

- **Zeilen:** 459 (Code: 407)
- **Checksum:** `501f149b6e11165c0e82e28bbb240e57`
- **Funktionen:** 22
- **Klassen:** 3

**Klassen:**
- `OrderEventEmitter` (Zeile 24-161)
- `ExecutionEventEmitter` (Zeile 164-350)
- `BacktraderEventAdapter` (Zeile 353-458)

---

### src/core/indicators/__init__.py

- **Zeilen:** 42 (Code: 30)
- **Checksum:** `224bb45d1d76e9a18647173650de6b88`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/indicators/base.py

- **Zeilen:** 102 (Code: 73)
- **Checksum:** `eb7868214eabfe0e7797a2168a7cb3a0`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `BaseIndicatorCalculator` (Zeile 34-85)

---

### src/core/indicators/custom.py

- **Zeilen:** 159 (Code: 126)
- **Checksum:** `0031c563d4de9125c4817ec31607ac3a`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `CustomIndicators` (Zeile 21-158)

---

### src/core/indicators/engine.py

- **Zeilen:** 169 (Code: 123)
- **Checksum:** `73be09a729e9fa1f397cf212c647c208`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `IndicatorEngine` (Zeile 26-168)

---

### src/core/indicators/momentum.py

- **Zeilen:** 220 (Code: 180)
- **Checksum:** `04aafcb725d6c66b47c7bc9a8abd4f05`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `MomentumIndicators` (Zeile 24-219)

---

### src/core/indicators/trend.py

- **Zeilen:** 260 (Code: 215)
- **Checksum:** `bd003ce29399b5d16936e7dce82bfac2`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `TrendIndicators` (Zeile 24-259)

---

### src/core/indicators/types.py

- **Zeilen:** 73 (Code: 54)
- **Checksum:** `13f505de8226d5ee9611aa8bb801f0c4`
- **Funktionen:** 0
- **Klassen:** 3

**Klassen:**
- `IndicatorType` (Zeile 14-52)
- `IndicatorConfig` (Zeile 56-62)
- `IndicatorResult` (Zeile 66-72)

---

### src/core/indicators/volatility.py

- **Zeilen:** 174 (Code: 140)
- **Checksum:** `1efb8cc08fb1feb290dae6b62ee8004b`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `VolatilityIndicators` (Zeile 24-173)

---

### src/core/indicators/volume.py

- **Zeilen:** 152 (Code: 122)
- **Checksum:** `3895ce9aae3d6cd5b647de3614691d2e`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `VolumeIndicators` (Zeile 23-151)

---

### src/core/market_data/__init__.py

- **Zeilen:** 38 (Code: 31)
- **Checksum:** `23169a97b201d1a4fccdb301e88fd5e8`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/market_data/alpaca_crypto_provider.py

- **Zeilen:** 197 (Code: 153)
- **Checksum:** `c8878fea2a48a410c667b7c3bbe3dae6`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `AlpacaCryptoProvider` (Zeile 21-196)

---

### src/core/market_data/alpaca_crypto_stream.py

- **Zeilen:** 452 (Code: 349)
- **Checksum:** `ccfdf98e1757febf8c74639e50388f01`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `AlpacaCryptoStreamClient` (Zeile 21-451)

---

### src/core/market_data/alpaca_stream.py

- **Zeilen:** 451 (Code: 347)
- **Checksum:** `4068e2c3c3c94e523226f8b1f45555af`
- **Funktionen:** 14
- **Klassen:** 1

**Klassen:**
- `AlpacaStreamClient` (Zeile 24-450)

---

### src/core/market_data/alpha_vantage_stream.py

- **Zeilen:** 427 (Code: 322)
- **Checksum:** `be6c970ef656b9d11c267b19f774aeea`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `AlphaVantageStreamClient` (Zeile 21-426)

---

### src/core/market_data/base_provider.py

- **Zeilen:** 245 (Code: 189)
- **Checksum:** `267c1625ac84797d3e83a00738324cf0`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `HistoricalDataProvider` (Zeile 18-244)

---

### src/core/market_data/history_provider.py

- **Zeilen:** 529 (Code: 426)
- **Checksum:** `5c3ebdcb677b51a9dfe9a6fcc5f03175`
- **Funktionen:** 16
- **Klassen:** 1

**Klassen:**
- `HistoryManager` (Zeile 47-528)

---

### src/core/market_data/providers/__init__.py

- **Zeilen:** 26 (Code: 21)
- **Checksum:** `85400f906274e09810d156aef63f5d5a`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/market_data/providers/alpaca_stock_provider.py

- **Zeilen:** 162 (Code: 124)
- **Checksum:** `3291a9ccd4bb026385f6ce74689af1de`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `AlpacaProvider` (Zeile 19-161)

---

### src/core/market_data/providers/alpha_vantage_provider.py

- **Zeilen:** 253 (Code: 206)
- **Checksum:** `bb9e4e3d4053ce3e94a1b197a309ca7a`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `AlphaVantageProvider` (Zeile 20-252)

---

### src/core/market_data/providers/base.py

- **Zeilen:** 240 (Code: 189)
- **Checksum:** `120d358f369cf6ee195de121e654387d`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `HistoricalDataProvider` (Zeile 19-239)

---

### src/core/market_data/providers/database_provider.py

- **Zeilen:** 131 (Code: 104)
- **Checksum:** `573f90a45cb0cafdab082a6bfc74f9b1`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `DatabaseProvider` (Zeile 22-130)

---

### src/core/market_data/providers/finnhub_provider.py

- **Zeilen:** 108 (Code: 87)
- **Checksum:** `9b2aca66dd04cc4e95ba8939c126b364`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `FinnhubProvider` (Zeile 19-107)

---

### src/core/market_data/providers/ibkr_provider.py

- **Zeilen:** 129 (Code: 104)
- **Checksum:** `77b32745c5fccaff983d0405269dcbf4`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `IBKRHistoricalProvider` (Zeile 20-128)

---

### src/core/market_data/providers/yahoo_provider.py

- **Zeilen:** 236 (Code: 194)
- **Checksum:** `02de9ac4d11dc2dcefe7c3bbc29daa87`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `YahooFinanceProvider` (Zeile 20-235)

---

### src/core/market_data/resampler.py

- **Zeilen:** 483 (Code: 340)
- **Checksum:** `96cb9854f204699ca7933303ec3d1040`
- **Funktionen:** 17
- **Klassen:** 6

**Klassen:**
- `OHLCV` (Zeile 21-30)
- `NoiseFilter` (Zeile 33-45)
- `MedianFilter` (Zeile 48-82)
- `MovingAverageFilter` (Zeile 85-120)
- `KalmanFilter` (Zeile 123-168)
- `MarketDataResampler` (Zeile 171-483)

---

### src/core/market_data/stream_client.py

- **Zeilen:** 528 (Code: 397)
- **Checksum:** `e3ea0f0e3e11651b7a0f5d306806ecf7`
- **Funktionen:** 29
- **Klassen:** 6

**Klassen:**
- `StreamStatus` (Zeile 24-30)
- `StreamMetrics` (Zeile 34-55)
- `MarketTick` (Zeile 59-68)
- `StreamClient` (Zeile 71-394)
- `IBKRStreamClient` (Zeile 397-452)
- `TradeRepublicStreamClient` (Zeile 455-528)

---

### src/core/market_data/types.py

- **Zeilen:** 72 (Code: 59)
- **Checksum:** `57fbef19491c3a83db452d49994c7f5e`
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
- **Checksum:** `d2ac44f11dc4e9f0847c9006973eba82`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/models/backtest_models.py

- **Zeilen:** 294 (Code: 209)
- **Checksum:** `d685ee264913be64d148d9100e469009`
- **Funktionen:** 9
- **Klassen:** 10

**Klassen:**
- `TradeSide` (Zeile 16-19)
- `Bar` (Zeile 22-39)
- `Trade` (Zeile 42-110)
- `EquityPoint` (Zeile 113-124)
- `BacktestMetrics` (Zeile 127-175)
- `BacktestResult` (Zeile 178-241)
- `Config` (Zeile 35-39)
- `Config` (Zeile 106-110)
- `Config` (Zeile 121-124)
- `Config` (Zeile 237-241)

**Top-Level Funktionen:**
- `from_historical_bar(bar: 'HistoricalBar', symbol: str | None) -> Bar` (Zeile 246)
- `to_historical_bars(bars: list[Bar], symbol: str) -> list['HistoricalBar']` (Zeile 269)

---

### src/core/pattern_db/__init__.py

- **Zeilen:** 37 (Code: 29)
- **Checksum:** `73363ec0ac2ebde0a17481b20450c172`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/pattern_db/build_database.py

- **Zeilen:** 228 (Code: 171)
- **Checksum:** `5b3eb413f8de9add63132e2e283d78ae`
- **Funktionen:** 4
- **Klassen:** 0

**Top-Level Funktionen:**
- `async build_database(include_stocks: bool, include_crypto: bool, days_back: int, window_size: int, step_size: int, outcome_bars: int, stock_symbols: list[str], crypto_symbols: list[str])` (Zeile 33)
- `main()` (Zeile 147)
- `progress(symbol, tf, bars, done, total)` (Zeile 93)
- `progress(symbol, tf, bars, done, total)` (Zeile 117)

---

### src/core/pattern_db/embedder.py

- **Zeilen:** 213 (Code: 145)
- **Checksum:** `49d386f988f10c0742a3603d09fa097c`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `PatternEmbedder` (Zeile 17-212)

---

### src/core/pattern_db/extractor.py

- **Zeilen:** 289 (Code: 224)
- **Checksum:** `5745f49a89f27dd2ab4412a0449ccbb6`
- **Funktionen:** 5
- **Klassen:** 2

**Klassen:**
- `Pattern` (Zeile 20-74)
- `PatternExtractor` (Zeile 77-288)

---

### src/core/pattern_db/fetcher.py

- **Zeilen:** 272 (Code: 209)
- **Checksum:** `09f8935495f0c7e22c1ad6f519e7294d`
- **Funktionen:** 9
- **Klassen:** 2

**Klassen:**
- `FetchConfig` (Zeile 53-60)
- `PatternDataFetcher` (Zeile 63-237)

**Top-Level Funktionen:**
- `resolve_symbol(symbol: str, asset_class: AssetClass) -> str` (Zeile 38)
- `async fetch_daytrading_data(include_stocks: bool, include_crypto: bool, days_back: int, progress_callback: callable) -> dict[str, dict[str, list[HistoricalBar]]]` (Zeile 241)

---

### src/core/pattern_db/pattern_service.py

- **Zeilen:** 288 (Code: 214)
- **Checksum:** `b0fb6595ee7747b2951af36f8fd1cb35`
- **Funktionen:** 6
- **Klassen:** 2

**Klassen:**
- `PatternAnalysis` (Zeile 19-37)
- `PatternService` (Zeile 40-270)

**Top-Level Funktionen:**
- `async get_pattern_service() -> PatternService` (Zeile 277)

---

### src/core/pattern_db/qdrant_client.py

- **Zeilen:** 474 (Code: 384)
- **Checksum:** `1dc3de66295e196105acee4214d0904e`
- **Funktionen:** 11
- **Klassen:** 2

**Klassen:**
- `PatternMatch` (Zeile 28-40)
- `TradingPatternDB` (Zeile 43-473)

---

### src/core/simulator/__init__.py

- **Zeilen:** 75 (Code: 65)
- **Checksum:** `20fbd04d4c78bb193e4df9a116807c82`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/simulator/excel_export.py

- **Zeilen:** 579 (Code: 446)
- **Checksum:** `af88c47946ea63dc465689342c0bc3f7`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `StrategySimulatorExport` (Zeile 34-549)

**Top-Level Funktionen:**
- `export_simulation_results(results: list[SimulationResult], filepath: Path | str, optimization_run: OptimizationRun | None, ui_table_data: list[list[str]] | None) -> Path` (Zeile 552)

---

### src/core/simulator/optimization_bayesian.py

- **Zeilen:** 506 (Code: 403)
- **Checksum:** `83fd0d721078682fba735bc0a0aaa118`
- **Funktionen:** 11
- **Klassen:** 3

**Klassen:**
- `OptimizationConfig` (Zeile 27-43)
- `BayesianOptimizer` (Zeile 46-280)
- `GridSearchOptimizer` (Zeile 283-505)

---

### src/core/simulator/result_types.py

- **Zeilen:** 184 (Code: 144)
- **Checksum:** `a302deea720da3c5273eb10406c49f43`
- **Funktionen:** 8
- **Klassen:** 4

**Klassen:**
- `TradeRecord` (Zeile 14-49)
- `SimulationResult` (Zeile 53-128)
- `OptimizationTrial` (Zeile 132-141)
- `OptimizationRun` (Zeile 145-183)

---

### src/core/simulator/simulation_engine.py

- **Zeilen:** 476 (Code: 385)
- **Checksum:** `d005eb1802dcf8e9cf69100a89c4e88e`
- **Funktionen:** 19
- **Klassen:** 2

**Klassen:**
- `SimulationConfig` (Zeile 22-32)
- `StrategySimulator` (Zeile 35-475)

---

### src/core/simulator/simulation_signal_utils.py

- **Zeilen:** 34 (Code: 29)
- **Checksum:** `db0ed4e9357603572083e994c7405d05`
- **Funktionen:** 3
- **Klassen:** 0

**Top-Level Funktionen:**
- `true_range(df: pd.DataFrame) -> pd.Series` (Zeile 6)
- `calculate_rsi(prices: pd.Series, period: int) -> pd.Series` (Zeile 13)
- `calculate_obv(df: pd.DataFrame) -> pd.Series` (Zeile 22)

---

### src/core/simulator/simulation_signals.py

- **Zeilen:** 108 (Code: 83)
- **Checksum:** `5e6a2248a07739d376695a880dc471b9`
- **Funktionen:** 14
- **Klassen:** 1

**Klassen:**
- `StrategySignalGenerator` (Zeile 25-107)

---

### src/core/simulator/simulation_signals_bollinger_squeeze.py

- **Zeilen:** 74 (Code: 46)
- **Checksum:** `12bfdd52d1aeff2b77d81f8ec28395f5`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `bollinger_squeeze_signals(df: pd.DataFrame, params: dict[str, Any], true_range) -> pd.Series` (Zeile 11)

---

### src/core/simulator/simulation_signals_breakout.py

- **Zeilen:** 93 (Code: 55)
- **Checksum:** `cda6d49cf3a1504e5bbf2087d58bf03f`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `breakout_signals(df: pd.DataFrame, params: dict[str, Any], true_range) -> pd.Series` (Zeile 11)

---

### src/core/simulator/simulation_signals_mean_reversion.py

- **Zeilen:** 57 (Code: 36)
- **Checksum:** `4803b14d10718966d39e109ff1ea5a27`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `mean_reversion_signals(df: pd.DataFrame, params: dict[str, Any], calculate_rsi) -> pd.Series` (Zeile 11)

---

### src/core/simulator/simulation_signals_momentum.py

- **Zeilen:** 61 (Code: 36)
- **Checksum:** `1b199f2101b9412cf923b8c847263144`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `momentum_signals(df: pd.DataFrame, params: dict[str, Any], calculate_rsi, calculate_obv) -> pd.Series` (Zeile 11)

---

### src/core/simulator/simulation_signals_opening_range.py

- **Zeilen:** 66 (Code: 37)
- **Checksum:** `3c3b9acdb3503d53a6025a5d60a7c852`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `opening_range_signals(df: pd.DataFrame, params: dict[str, Any], true_range) -> pd.Series` (Zeile 11)

---

### src/core/simulator/simulation_signals_regime_hybrid.py

- **Zeilen:** 87 (Code: 58)
- **Checksum:** `d5acfbe0cc194050c0e0d292dca6ebab`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `regime_hybrid_signals(df: pd.DataFrame, params: dict[str, Any], calculate_rsi, calculate_obv, true_range) -> pd.Series` (Zeile 11)

---

### src/core/simulator/simulation_signals_scalping.py

- **Zeilen:** 61 (Code: 38)
- **Checksum:** `e879490492d5b3694e81b0574a2c39f5`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `scalping_signals(df: pd.DataFrame, params: dict[str, Any], calculate_rsi) -> pd.Series` (Zeile 11)

---

### src/core/simulator/simulation_signals_trend_following.py

- **Zeilen:** 65 (Code: 40)
- **Checksum:** `1bc4557d0837c0315d5176fc5e1137fe`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `trend_following_signals(df: pd.DataFrame, params: dict[str, Any], calculate_rsi) -> pd.Series` (Zeile 11)

---

### src/core/simulator/simulation_signals_trend_pullback.py

- **Zeilen:** 56 (Code: 30)
- **Checksum:** `df7c2037ed44109377552f390c319ba0`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `trend_pullback_signals(df: pd.DataFrame, params: dict[str, Any], calculate_rsi) -> pd.Series` (Zeile 11)

---

### src/core/simulator/strategy_params.py

- **Zeilen:** 75 (Code: 56)
- **Checksum:** `c8c29e943c2ea0cb423f2f123f2f7f52`
- **Funktionen:** 5
- **Klassen:** 0

**Top-Level Funktionen:**
- `get_strategy_parameters(strategy: StrategyName | str) -> StrategyParameterConfig` (Zeile 17)
- `get_default_parameters(strategy: StrategyName | str) -> dict[str, Any]` (Zeile 34)
- `_is_exit_parameter(param_def: ParameterDefinition) -> bool` (Zeile 47)
- `filter_entry_only_param_config(param_config: StrategyParameterConfig) -> StrategyParameterConfig` (Zeile 52)
- `filter_entry_only_params(strategy: StrategyName | str, params: dict[str, Any]) -> dict[str, Any]` (Zeile 65)

---

### src/core/simulator/strategy_params_base.py

- **Zeilen:** 113 (Code: 89)
- **Checksum:** `f6b9a7523a7963316e8c597dba1ed252`
- **Funktionen:** 5
- **Klassen:** 3

**Klassen:**
- `StrategyName` (Zeile 11-38)
- `ParameterDefinition` (Zeile 42-91)
- `StrategyParameterConfig` (Zeile 95-112)

---

### src/core/simulator/strategy_params_registry.py

- **Zeilen:** 504 (Code: 469)
- **Checksum:** `67d70e1510d438cc87e318ede4271e35`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/simulator/strategy_persistence.py

- **Zeilen:** 212 (Code: 160)
- **Checksum:** `128d5c502f4991fe719de20da018e9b9`
- **Funktionen:** 7
- **Klassen:** 0

**Top-Level Funktionen:**
- `get_params_file(strategy_name: str, params_dir: Path | None) -> Path` (Zeile 20)
- `save_strategy_params(strategy_name: str, params: dict[str, Any], symbol: str | None, score: float | None, params_dir: Path | None) -> Path` (Zeile 35)
- `save_strategy_params_to_path(filepath: Path, strategy_name: str, params: dict[str, Any], symbol: str | None, score: float | None) -> Path` (Zeile 73)
- `load_strategy_params(strategy_name: str, params_dir: Path | None) -> dict[str, Any] | None` (Zeile 112)
- `get_all_saved_strategies(params_dir: Path | None) -> list[str]` (Zeile 142)
- `delete_strategy_params(strategy_name: str, params_dir: Path | None) -> bool` (Zeile 165)
- `get_params_metadata(strategy_name: str, params_dir: Path | None) -> dict[str, Any] | None` (Zeile 188)

---

### src/core/strategy/__init__.py

- **Zeilen:** 44 (Code: 36)
- **Checksum:** `a053d903191db27774a324a4aaba249e`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/strategy/compiled_strategy.py

- **Zeilen:** 239 (Code: 177)
- **Checksum:** `b30871c5dcc695c1fdf20392bfdbc028`
- **Funktionen:** 15
- **Klassen:** 1

**Klassen:**
- `CompiledStrategy` (Zeile 19-238)

---

### src/core/strategy/compiler.py

- **Zeilen:** 521 (Code: 359)
- **Checksum:** `5219f93d315f4463259941ebf4284751`
- **Funktionen:** 12
- **Klassen:** 5

**Klassen:**
- `CompilationError` (Zeile 42-44)
- `IndicatorFactory` (Zeile 47-211)
- `ConditionEvaluator` (Zeile 214-447)
- `StrategyCompiler` (Zeile 450-520)
- `DynamicCompiledStrategy` (Zeile 509-514)

---

### src/core/strategy/definition.py

- **Zeilen:** 550 (Code: 428)
- **Checksum:** `e168a16791df74751999ea4159385c37`
- **Funktionen:** 17
- **Klassen:** 11

**Klassen:**
- `IndicatorType` (Zeile 36-74)
- `ComparisonOperator` (Zeile 77-92)
- `LogicOperator` (Zeile 95-100)
- `IndicatorConfig` (Zeile 103-141)
- `Condition` (Zeile 144-190)
- `LogicGroup` (Zeile 204-264)
- `RiskManagement` (Zeile 277-342)
- `StrategyDefinition` (Zeile 345-545)
- `Config` (Zeile 138-141)
- `Config` (Zeile 187-190)
- `Config` (Zeile 261-264)

**Top-Level Funktionen:**
- `_get_condition_type(v: Any) -> str` (Zeile 194)

---

### src/core/strategy/engine.py

- **Zeilen:** 460 (Code: 346)
- **Checksum:** `f7295ff69e996bd831b5cee9c52b95a8`
- **Funktionen:** 14
- **Klassen:** 7

**Klassen:**
- `SignalType` (Zeile 28-34)
- `StrategyType` (Zeile 37-47)
- `Signal` (Zeile 51-63)
- `StrategyConfig` (Zeile 67-78)
- `StrategyState` (Zeile 82-89)
- `BaseStrategy` (Zeile 92-207)
- `StrategyEngine` (Zeile 210-459)

---

### src/core/strategy/evaluation.py

- **Zeilen:** 277 (Code: 216)
- **Checksum:** `3097eb182fab4031883f2f222ee8d86d`
- **Funktionen:** 14
- **Klassen:** 1

**Klassen:**
- `ConditionEvaluator` (Zeile 22-276)

---

### src/core/strategy/loader.py

- **Zeilen:** 195 (Code: 143)
- **Checksum:** `99f8629cd977d4d70b53dad770883fb5`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `StrategyLoader` (Zeile 17-178)

**Top-Level Funktionen:**
- `get_strategy_loader() -> StrategyLoader` (Zeile 185)

---

### src/core/strategy/strategies/__init__.py

- **Zeilen:** 21 (Code: 17)
- **Checksum:** `a4ff3eafa7b00e29aa6ecd2c8bfcf081`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/strategy/strategies/breakout.py

- **Zeilen:** 107 (Code: 82)
- **Checksum:** `1a3f662e5d4580376827d4e6ee1fabab`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `BreakoutStrategy` (Zeile 16-106)

---

### src/core/strategy/strategies/mean_reversion.py

- **Zeilen:** 125 (Code: 97)
- **Checksum:** `250f2ed365437c66972bb78d76354d2c`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `MeanReversionStrategy` (Zeile 16-124)

---

### src/core/strategy/strategies/momentum.py

- **Zeilen:** 108 (Code: 84)
- **Checksum:** `fe94b0c63ee95ca829ef736fdcba3d56`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `MomentumStrategy` (Zeile 16-107)

---

### src/core/strategy/strategies/scalping.py

- **Zeilen:** 113 (Code: 87)
- **Checksum:** `0cc178557b223bf0290d5596bbb56935`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `ScalpingStrategy` (Zeile 17-112)

---

### src/core/strategy/strategies/trend_following.py

- **Zeilen:** 128 (Code: 99)
- **Checksum:** `b431b87ee7331523911d22c9f51d20e7`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `TrendFollowingStrategy` (Zeile 17-127)

---

### src/core/tradingbot/__init__.py

- **Zeilen:** 217 (Code: 196)
- **Checksum:** `f2fa8442b850bde6e9d35beeb0f38cc4`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/core/tradingbot/backtest_harness.py

- **Zeilen:** 579 (Code: 451)
- **Checksum:** `48fe4eff533b2036280689dc0f7c3daa`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `BacktestHarness` (Zeile 52-576)

---

### src/core/tradingbot/backtest_metrics_helpers.py

- **Zeilen:** 55 (Code: 39)
- **Checksum:** `5ebb7ba054f528e20b77c73a70c6383f`
- **Funktionen:** 2
- **Klassen:** 0

**Top-Level Funktionen:**
- `convert_trades_to_results(trades: list[BacktestTrade]) -> list[TradeResult]` (Zeile 16)
- `calculate_backtest_metrics(trades: list[BacktestTrade]) -> PerformanceMetrics` (Zeile 35)

---

### src/core/tradingbot/backtest_simulator.py

- **Zeilen:** 197 (Code: 152)
- **Checksum:** `e754feffe2af6a7272aba3d1f129118d`
- **Funktionen:** 6
- **Klassen:** 2

**Klassen:**
- `BacktestSimulator` (Zeile 18-82)
- `ReleaseGate` (Zeile 87-196)

---

### src/core/tradingbot/backtest_types.py

- **Zeilen:** 191 (Code: 157)
- **Checksum:** `bc36c1dd14d8349e21652c874bbc131e`
- **Funktionen:** 4
- **Klassen:** 5

**Klassen:**
- `BacktestMode` (Zeile 21-25)
- `BacktestConfig` (Zeile 29-59)
- `BacktestTrade` (Zeile 63-101)
- `BacktestState` (Zeile 105-124)
- `BacktestResult` (Zeile 128-188)

---

### src/core/tradingbot/bot_controller.py

- **Zeilen:** 477 (Code: 365)
- **Checksum:** `f219afcab5b9157346fc2eb7ff7e9549`
- **Funktionen:** 22
- **Klassen:** 1

**Klassen:**
- `BotController` (Zeile 46-476)

---

### src/core/tradingbot/bot_helpers.py

- **Zeilen:** 350 (Code: 285)
- **Checksum:** `7930f6de34f159b5a294c4a1d11c932f`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `BotHelpersMixin` (Zeile 41-349)

---

### src/core/tradingbot/bot_settings_manager.py

- **Zeilen:** 125 (Code: 92)
- **Checksum:** `3aba9e016cf485b1c66e3f7bbcd841a5`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `BotSettingsManager` (Zeile 20-108)

**Top-Level Funktionen:**
- `get_bot_settings_manager() -> BotSettingsManager` (Zeile 115)

---

### src/core/tradingbot/bot_signal_logic.py

- **Zeilen:** 211 (Code: 163)
- **Checksum:** `7149676ec00c09f1db4c207d2903245d`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `BotSignalLogicMixin` (Zeile 22-209)

---

### src/core/tradingbot/bot_state_handlers.py

- **Zeilen:** 569 (Code: 428)
- **Checksum:** `038bb09e45d499b52a9f6f3f8f7968c3`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `BotStateHandlersMixin` (Zeile 35-568)

---

### src/core/tradingbot/bot_test_suites.py

- **Zeilen:** 534 (Code: 406)
- **Checksum:** `14240fd5cbbfd43fdd3f5782ef84ca13`
- **Funktionen:** 23
- **Klassen:** 3

**Klassen:**
- `BotUnitTests` (Zeile 38-253)
- `BotIntegrationTests` (Zeile 256-414)
- `ChaosTests` (Zeile 417-532)

---

### src/core/tradingbot/bot_test_types.py

- **Zeilen:** 185 (Code: 154)
- **Checksum:** `f047dc9e3154ffc20a1f4eedc58106b2`
- **Funktionen:** 5
- **Klassen:** 3

**Klassen:**
- `TestResult` (Zeile 22-27)
- `TestCase` (Zeile 31-38)
- `TestSuiteResult` (Zeile 42-77)

**Top-Level Funktionen:**
- `generate_mock_features(symbol: str, close: float, trend: str, volatility: str) -> FeatureVector` (Zeile 80)
- `generate_mock_regime(regime_type: RegimeType, volatility: VolatilityLevel) -> RegimeState` (Zeile 166)

---

### src/core/tradingbot/bot_tests.py

- **Zeilen:** 84 (Code: 60)
- **Checksum:** `719c9bcc483e57cf24d4ff476b7858ac`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `run_all_tests() -> dict[str, TestSuiteResult]` (Zeile 50)

---

### src/core/tradingbot/bot_trailing_stops.py

- **Zeilen:** 277 (Code: 200)
- **Checksum:** `351a405e00bb570698d19fb4fe333b07`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `BotTrailingStopsMixin` (Zeile 20-276)

---

### src/core/tradingbot/candle_preprocessing.py

- **Zeilen:** 214 (Code: 156)
- **Checksum:** `e3ced3d619f1fbebc94d20413aa8bd40`
- **Funktionen:** 3
- **Klassen:** 0

**Top-Level Funktionen:**
- `preprocess_candles(data: pd.DataFrame, market_type: str, target_tz: str, fill_missing: bool, filter_sessions: bool) -> pd.DataFrame` (Zeile 30)
- `detect_missing_candles(data: pd.DataFrame, expected_freq: str) -> list[datetime]` (Zeile 129)
- `validate_candles(data: pd.DataFrame) -> dict` (Zeile 160)

---

### src/core/tradingbot/config.py

- **Zeilen:** 422 (Code: 358)
- **Checksum:** `b2bb77b13005706b2542888e90084873`
- **Funktionen:** 4
- **Klassen:** 8

**Klassen:**
- `MarketType` (Zeile 14-17)
- `KIMode` (Zeile 20-29)
- `TrailingMode` (Zeile 32-36)
- `TradingEnvironment` (Zeile 39-42)
- `BotConfig` (Zeile 45-139)
- `RiskConfig` (Zeile 142-296)
- `LLMPolicyConfig` (Zeile 299-380)
- `FullBotConfig` (Zeile 383-421)

---

### src/core/tradingbot/entry_exit_engine.py

- **Zeilen:** 337 (Code: 277)
- **Checksum:** `8b1c6071236da472f6aa516a4e279c3c`
- **Funktionen:** 9
- **Klassen:** 3

**Klassen:**
- `TrailingStopResult` (Zeile 34-38)
- `TrailingStopManager` (Zeile 40-240)
- `EntryExitEngine` (Zeile 242-336)

---

### src/core/tradingbot/entry_scorer.py

- **Zeilen:** 454 (Code: 380)
- **Checksum:** `72566ac0461a9bb468e868833876d9ff`
- **Funktionen:** 14
- **Klassen:** 2

**Klassen:**
- `EntryScoreResult` (Zeile 24-30)
- `EntryScorer` (Zeile 32-452)

---

### src/core/tradingbot/evaluator_types.py

- **Zeilen:** 130 (Code: 99)
- **Checksum:** `ac3d88452709808ccdb2719158004d31`
- **Funktionen:** 1
- **Klassen:** 5

**Klassen:**
- `TradeResult` (Zeile 15-27)
- `PerformanceMetrics` (Zeile 31-95)
- `RobustnessGate` (Zeile 98-106)
- `WalkForwardConfig` (Zeile 109-115)
- `WalkForwardResult` (Zeile 119-129)

---

### src/core/tradingbot/execution.py

- **Zeilen:** 509 (Code: 393)
- **Checksum:** `60ca611aa53c9c83fc4fa48b8284c494`
- **Funktionen:** 16
- **Klassen:** 3

**Klassen:**
- `PaperExecutor` (Zeile 51-181)
- `ExecutionGuardrails` (Zeile 184-305)
- `OrderExecutor` (Zeile 308-508)

---

### src/core/tradingbot/execution_types.py

- **Zeilen:** 103 (Code: 77)
- **Checksum:** `1d61fa9aae7320dd67447f3269465b11`
- **Funktionen:** 2
- **Klassen:** 6

**Klassen:**
- `OrderStatus` (Zeile 21-29)
- `OrderType` (Zeile 32-37)
- `OrderResult` (Zeile 41-58)
- `PositionSizeResult` (Zeile 62-69)
- `RiskLimits` (Zeile 72-90)
- `RiskState` (Zeile 93-102)

---

### src/core/tradingbot/exit_checker.py

- **Zeilen:** 317 (Code: 258)
- **Checksum:** `d57d7f98209edfe1423305abdd007f1d`
- **Funktionen:** 9
- **Klassen:** 3

**Klassen:**
- `ExitReason` (Zeile 24-36)
- `ExitSignalResult` (Zeile 40-45)
- `ExitSignalChecker` (Zeile 47-315)

---

### src/core/tradingbot/feature_engine.py

- **Zeilen:** 479 (Code: 375)
- **Checksum:** `8292a196e219449625c340b68023cf1f`
- **Funktionen:** 15
- **Klassen:** 1

**Klassen:**
- `FeatureEngine` (Zeile 34-478)

---

### src/core/tradingbot/llm_integration.py

- **Zeilen:** 445 (Code: 347)
- **Checksum:** `1a95cd6705bed24a9e776aae14ad06f3`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `LLMIntegration` (Zeile 49-444)

---

### src/core/tradingbot/llm_prompts.py

- **Zeilen:** 172 (Code: 125)
- **Checksum:** `0fc3262bb0eb042ce1f816650927b3f5`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `LLMPromptBuilder` (Zeile 11-171)

---

### src/core/tradingbot/llm_types.py

- **Zeilen:** 52 (Code: 42)
- **Checksum:** `328087644c6ef9f545075fc5ff994724`
- **Funktionen:** 0
- **Klassen:** 3

**Klassen:**
- `LLMCallType` (Zeile 16-22)
- `LLMCallRecord` (Zeile 26-39)
- `LLMBudgetState` (Zeile 43-51)

---

### src/core/tradingbot/llm_validators.py

- **Zeilen:** 128 (Code: 93)
- **Checksum:** `e1459ce86a9d5f38fef68c77a6a2707c`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `LLMResponseValidator` (Zeile 18-127)

---

### src/core/tradingbot/models.py

- **Zeilen:** 520 (Code: 367)
- **Checksum:** `c9153f675767081c356fa7eee0206e83`
- **Funktionen:** 11
- **Klassen:** 14

**Klassen:**
- `TradeSide` (Zeile 23-27)
- `BotAction` (Zeile 30-36)
- `RegimeType` (Zeile 39-44)
- `VolatilityLevel` (Zeile 47-52)
- `SignalType` (Zeile 55-58)
- `FeatureVector` (Zeile 63-129)
- `RegimeState` (Zeile 132-171)
- `Signal` (Zeile 176-222)
- `OrderIntent` (Zeile 225-255)
- `TrailingState` (Zeile 260-318)
- `PositionState` (Zeile 321-378)
- `BotDecision` (Zeile 383-413)
- `LLMBotResponse` (Zeile 418-463)
- `StrategyProfile` (Zeile 468-519)

---

### src/core/tradingbot/no_trade_filter.py

- **Zeilen:** 465 (Code: 349)
- **Checksum:** `a4fe6f3bfa351787c90ca888e7d682b8`
- **Funktionen:** 20
- **Klassen:** 4

**Klassen:**
- `FilterReason` (Zeile 20-32)
- `FilterResult` (Zeile 36-51)
- `TradingSession` (Zeile 55-74)
- `NoTradeFilter` (Zeile 77-464)

---

### src/core/tradingbot/position_sizer.py

- **Zeilen:** 211 (Code: 160)
- **Checksum:** `ef6531f7c6c363dfe0056bc47b1729b8`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `PositionSizer` (Zeile 20-210)

---

### src/core/tradingbot/regime_engine.py

- **Zeilen:** 372 (Code: 284)
- **Checksum:** `e08bafdec468688c672a6b6ffa91d0e2`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `RegimeEngine` (Zeile 22-371)

---

### src/core/tradingbot/risk_manager.py

- **Zeilen:** 165 (Code: 126)
- **Checksum:** `8165c200fa88b6d7096a4a229f1ba492`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `RiskManager` (Zeile 19-164)

---

### src/core/tradingbot/state_machine.py

- **Zeilen:** 518 (Code: 399)
- **Checksum:** `9511f2a61ad2396bee6a7d43d43035a9`
- **Funktionen:** 28
- **Klassen:** 6

**Klassen:**
- `BotState` (Zeile 31-39)
- `BotTrigger` (Zeile 42-76)
- `StateTransition` (Zeile 79-85)
- `StateMachineError` (Zeile 88-90)
- `InvalidTransitionError` (Zeile 93-95)
- `BotStateMachine` (Zeile 98-517)

---

### src/core/tradingbot/strategy_catalog.py

- **Zeilen:** 150 (Code: 109)
- **Checksum:** `90320799f58d0bf088b4afd0f7937e8f`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `StrategyCatalog` (Zeile 41-149)

---

### src/core/tradingbot/strategy_definitions.py

- **Zeilen:** 81 (Code: 53)
- **Checksum:** `6e71c1485822daa50fef9e32aa50247c`
- **Funktionen:** 1
- **Klassen:** 4

**Klassen:**
- `StrategyType` (Zeile 24-30)
- `EntryRule` (Zeile 33-43)
- `ExitRule` (Zeile 46-55)
- `StrategyDefinition` (Zeile 58-80)

---

### src/core/tradingbot/strategy_evaluator.py

- **Zeilen:** 577 (Code: 426)
- **Checksum:** `9fa8914a9faa547154caabdabfc06b6e`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `StrategyEvaluator` (Zeile 42-576)

---

### src/core/tradingbot/strategy_selector.py

- **Zeilen:** 562 (Code: 427)
- **Checksum:** `30ae4d44222aadd054c48d22f3448e72`
- **Funktionen:** 16
- **Klassen:** 3

**Klassen:**
- `SelectionResult` (Zeile 30-52)
- `SelectionSnapshot` (Zeile 55-74)
- `StrategySelector` (Zeile 77-561)

---

### src/core/tradingbot/strategy_templates.py

- **Zeilen:** 578 (Code: 554)
- **Checksum:** `0021301ca12d82a4e40713c1d4f99599`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `StrategyTemplatesMixin` (Zeile 18-577)

---

### src/database/__init__.py

- **Zeilen:** 47 (Code: 43)
- **Checksum:** `880d5427dcea575490a7f52055e2c681`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/database/database.py

- **Zeilen:** 312 (Code: 235)
- **Checksum:** `1224ca75d9ff0b7436bddb4bbce465d6`
- **Funktionen:** 16
- **Klassen:** 1

**Klassen:**
- `DatabaseManager` (Zeile 24-279)

**Top-Level Funktionen:**
- `initialize_database(config: DatabaseConfig) -> DatabaseManager` (Zeile 286)
- `get_db_manager() -> DatabaseManager` (Zeile 301)

---

### src/database/models.py

- **Zeilen:** 508 (Code: 328)
- **Checksum:** `249fd58f5d8b479012ec2b36dc994e18`
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

### src/derivatives/__init__.py

- **Zeilen:** 23 (Code: 19)
- **Checksum:** `e2d157bc286be48235bb4274e3645f79`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/derivatives/ko_finder/__init__.py

- **Zeilen:** 59 (Code: 50)
- **Checksum:** `1a540c1f1c73f0689bf8ea57e5aca352`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/derivatives/ko_finder/adapter/__init__.py

- **Zeilen:** 25 (Code: 21)
- **Checksum:** `f0b9e21aa491414b39cf9348c8decf02`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/derivatives/ko_finder/adapter/fetcher.py

- **Zeilen:** 325 (Code: 253)
- **Checksum:** `e09c1978050ee91138f2e11ecf989a78`
- **Funktionen:** 12
- **Klassen:** 4

**Klassen:**
- `CircuitState` (Zeile 42-47)
- `FetchResult` (Zeile 51-61)
- `CircuitBreaker` (Zeile 65-110)
- `OnvistaFetcher` (Zeile 113-324)

---

### src/derivatives/ko_finder/adapter/normalizer.py

- **Zeilen:** 245 (Code: 169)
- **Checksum:** `af6e393106424128ba7c804b4c64afc4`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `OnvistaNormalizer` (Zeile 27-198)

**Top-Level Funktionen:**
- `parse_german_number(text: str) -> float | None` (Zeile 201)
- `parse_percentage(text: str) -> float | None` (Zeile 230)

---

### src/derivatives/ko_finder/adapter/parser.py

- **Zeilen:** 368 (Code: 270)
- **Checksum:** `7a00fa51509f365ffa4aaa482deba2c1`
- **Funktionen:** 10
- **Klassen:** 2

**Klassen:**
- `ParseResult` (Zeile 30-39)
- `OnvistaParser` (Zeile 42-367)

---

### src/derivatives/ko_finder/adapter/playwright_fetcher.py

- **Zeilen:** 320 (Code: 240)
- **Checksum:** `05c1960a7b7a97f8669eece2568bf0bf`
- **Funktionen:** 7
- **Klassen:** 2

**Klassen:**
- `PlaywrightConfig` (Zeile 30-38)
- `PlaywrightFetcher` (Zeile 41-319)

---

### src/derivatives/ko_finder/adapter/url_builder.py

- **Zeilen:** 207 (Code: 152)
- **Checksum:** `057e209627a073a7a6307d0703163fc6`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `OnvistaURLBuilder` (Zeile 33-206)

---

### src/derivatives/ko_finder/config.py

- **Zeilen:** 163 (Code: 124)
- **Checksum:** `98eeab9bec5caa1ccb85a32a4b9f9f9d`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `KOFilterConfig` (Zeile 29-162)

---

### src/derivatives/ko_finder/constants.py

- **Zeilen:** 249 (Code: 163)
- **Checksum:** `e315ed691a5ec048d990112ff4a7aa69`
- **Funktionen:** 2
- **Klassen:** 4

**Klassen:**
- `Issuer` (Zeile 21-38)
- `Direction` (Zeile 58-69)
- `SortColumn` (Zeile 72-77)
- `SortOrder` (Zeile 80-84)

---

### src/derivatives/ko_finder/engine/__init__.py

- **Zeilen:** 20 (Code: 16)
- **Checksum:** `63bf27917e00eb6727b5905c034b4691`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/derivatives/ko_finder/engine/cache.py

- **Zeilen:** 245 (Code: 189)
- **Checksum:** `de076291d59bb5269983104ee8f5e108`
- **Funktionen:** 12
- **Klassen:** 3

**Klassen:**
- `CacheEntry` (Zeile 32-55)
- `CacheManager` (Zeile 58-200)
- `SWRCache` (Zeile 203-244)

---

### src/derivatives/ko_finder/engine/filters.py

- **Zeilen:** 204 (Code: 140)
- **Checksum:** `de1833ac399ef649d8c32f8bbf5605e6`
- **Funktionen:** 10
- **Klassen:** 2

**Klassen:**
- `FilterResult` (Zeile 27-36)
- `HardFilters` (Zeile 39-184)

**Top-Level Funktionen:**
- `apply_hard_filters(products: list[KnockoutProduct], config: KOFilterConfig) -> list[KnockoutProduct]` (Zeile 187)

---

### src/derivatives/ko_finder/engine/ranking.py

- **Zeilen:** 383 (Code: 262)
- **Checksum:** `e419c667196114991b215dd5ddc09f26`
- **Funktionen:** 12
- **Klassen:** 3

**Klassen:**
- `ScoringParams` (Zeile 31-54)
- `ScoreBreakdown` (Zeile 58-75)
- `RankingEngine` (Zeile 78-360)

**Top-Level Funktionen:**
- `rank_products(products: list[KnockoutProduct], config: KOFilterConfig, top_n: int | None, underlying_price: float | None) -> list[KnockoutProduct]` (Zeile 363)

---

### src/derivatives/ko_finder/models.py

- **Zeilen:** 283 (Code: 202)
- **Checksum:** `22f09e016114ba052a2ea4317cc0f706`
- **Funktionen:** 10
- **Klassen:** 7

**Klassen:**
- `ProductFlag` (Zeile 21-29)
- `Quote` (Zeile 33-57)
- `UnderlyingSnapshot` (Zeile 61-69)
- `KnockoutProduct` (Zeile 73-209)
- `SearchMeta` (Zeile 213-240)
- `SearchRequest` (Zeile 244-249)
- `SearchResponse` (Zeile 253-282)

---

### src/derivatives/ko_finder/pnl_calculator.py

- **Zeilen:** 110 (Code: 82)
- **Checksum:** `85ec6431611015b9327c6967fa700277`
- **Funktionen:** 1
- **Klassen:** 2

**Klassen:**
- `Direction` (Zeile 23-27)
- `DerivativePnL` (Zeile 31-38)

**Top-Level Funktionen:**
- `calculate_derivative_pnl(direction: Direction, leverage: float, spread_pct: float, u0: float, u1: float, capital: float, ask_entry: float) -> DerivativePnL` (Zeile 41)

---

### src/derivatives/ko_finder/service.py

- **Zeilen:** 436 (Code: 364)
- **Checksum:** `0860d7f408a78197d87a5adee7dba4f2`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `KOFinderService` (Zeile 37-435)

---

### src/ui/__init__.py

- **Zeilen:** 2 (Code: 1)
- **Checksum:** `7e816b25502188912a5ea444b8a5b6ca`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/app.py

- **Zeilen:** 140 (Code: 102)
- **Checksum:** `515ac21aea390af183b48e6f4db0221f`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `TradingApplication` (Zeile 33-88) 🖥️

**Top-Level Funktionen:**
- `async main()` (Zeile 91)
- `_excepthook(exc_type, exc_value, exc_tb)` (Zeile 120)

---

### src/ui/app_components/__init__.py

- **Zeilen:** 34 (Code: 30)
- **Checksum:** `d221661f124f2bf4100980c546d7fd92`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/app_components/actions_mixin.py

- **Zeilen:** 160 (Code: 125)
- **Checksum:** `ca5ccd71d73b8bea01b4d3aa3b71ad8a`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `ActionsMixin` (Zeile 24-159)

---

### src/ui/app_components/app_broker_events_mixin.py

- **Zeilen:** 80 (Code: 70)
- **Checksum:** `51445838f348d0fe280447800b632a77`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `AppBrokerEventsMixin` (Zeile 51-79)

---

### src/ui/app_components/app_chart_mixin.py

- **Zeilen:** 93 (Code: 78)
- **Checksum:** `4c5835dec28499cc0c7dae44c14a7f21`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `AppChartMixin` (Zeile 51-92)

---

### src/ui/app_components/app_events_mixin.py

- **Zeilen:** 87 (Code: 74)
- **Checksum:** `95bcdd1378e37d9ee3292c599b05e9d2`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `AppEventsMixin` (Zeile 51-86)

---

### src/ui/app_components/app_lifecycle_mixin.py

- **Zeilen:** 134 (Code: 111)
- **Checksum:** `93c34b2e999714c27ce3a2639c537e0c`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `AppLifecycleMixin` (Zeile 51-133)

---

### src/ui/app_components/app_refresh_mixin.py

- **Zeilen:** 70 (Code: 57)
- **Checksum:** `e1d094f3baffb1d6bb29d954bffd946c`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `AppRefreshMixin` (Zeile 51-69)

---

### src/ui/app_components/app_settings_mixin.py

- **Zeilen:** 98 (Code: 79)
- **Checksum:** `0832f0dc733fe3e150e1c2879ccf8c04`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `AppSettingsMixin` (Zeile 51-97)

---

### src/ui/app_components/app_timers_mixin.py

- **Zeilen:** 68 (Code: 56)
- **Checksum:** `45e9ea33c4014bc0fd57442906c01ae9`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `AppTimersMixin` (Zeile 51-67)

---

### src/ui/app_components/app_ui_mixin.py

- **Zeilen:** 151 (Code: 102)
- **Checksum:** `1a6535cae46f7a1b9c60a4947f2f408e`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `AppUIMixin` (Zeile 51-150)

---

### src/ui/app_components/broker_mixin.py

- **Zeilen:** 384 (Code: 309)
- **Checksum:** `16543799d55b4923e528c39a40fdc4bb`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `BrokerMixin` (Zeile 23-383)

---

### src/ui/app_components/menu_mixin.py

- **Zeilen:** 372 (Code: 273)
- **Checksum:** `bbb686193473d92ea65e1890675087a9`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `MenuMixin` (Zeile 10-371)

---

### src/ui/app_components/toolbar_mixin.py

- **Zeilen:** 281 (Code: 214)
- **Checksum:** `493cc944e37dc4c0f164d770d91cbed4`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `ToolbarMixin` (Zeile 24-280)

---

### src/ui/app_console_utils.py

- **Zeilen:** 30 (Code: 24)
- **Checksum:** `0e48dd559a9efe42308f0eb99b49f805`
- **Funktionen:** 4
- **Klassen:** 0

**Top-Level Funktionen:**
- `_is_windows() -> bool` (Zeile 6)
- `_get_console_hwnd() -> int` (Zeile 9)
- `_hide_console_window() -> None` (Zeile 14)
- `_show_console_window() -> None` (Zeile 21)

---

### src/ui/app_logging.py

- **Zeilen:** 50 (Code: 39)
- **Checksum:** `c9848e1d86a41957d775db9934ccd692`
- **Funktionen:** 4
- **Klassen:** 2

**Klassen:**
- `ConsoleOnErrorHandler` (Zeile 10-15)
- `LogStream` (Zeile 17-49)

---

### src/ui/app_resources.py

- **Zeilen:** 25 (Code: 18)
- **Checksum:** `616314f78712fa3f54fbd8e919840993`
- **Funktionen:** 2
- **Klassen:** 0

**Top-Level Funktionen:**
- `_load_app_icon() -> QIcon` (Zeile 7)
- `_get_startup_icon_path() -> Path` (Zeile 22)

---

### src/ui/app_startup_window.py

- **Zeilen:** 76 (Code: 63)
- **Checksum:** `47be052265f1a450af2ae2d0ffa084a6`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `StartupLogWindow` (Zeile 10-75) 🖥️

---

### src/ui/chart/__init__.py

- **Zeilen:** 14 (Code: 10)
- **Checksum:** `b470e40845a31f541f33ee37e874087c`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/chart/chart_adapter.py

- **Zeilen:** 457 (Code: 346)
- **Checksum:** `1a237abdd3ab21e9fa1cfe3ae1cb86d1`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `ChartAdapter` (Zeile 17-456)

---

### src/ui/chart/chart_bridge.py

- **Zeilen:** 384 (Code: 281)
- **Checksum:** `4bfa940d942d5e7fd7e9a0d54feada7f`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `ChartBridge` (Zeile 19-383)

---

### src/ui/chart_window_manager.py

- **Zeilen:** 218 (Code: 150)
- **Checksum:** `19f05b993f819686a4e1d01dc4e37296`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `ChartWindowManager` (Zeile 16-188)

**Top-Level Funktionen:**
- `get_chart_window_manager(history_manager, parent) -> ChartWindowManager` (Zeile 195)

---

### src/ui/dialogs/__init__.py

- **Zeilen:** 66 (Code: 54)
- **Checksum:** `feabc65be33aecdce56538dcce9ccf1c`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/dialogs/ai_backtest_dialog.py

- **Zeilen:** 582 (Code: 409)
- **Checksum:** `6271abee0a177c6ee65d4dddf43d1fa6`
- **Funktionen:** 17
- **Klassen:** 1

**Klassen:**
- `AIBacktestDialog` (Zeile 40-581) 🖥️

---

### src/ui/dialogs/backtest_dialog.py

- **Zeilen:** 258 (Code: 192)
- **Checksum:** `6a76980b4473ffc846e2babff5ec467d`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `BacktestDialog` (Zeile 22-257) 🖥️

---

### src/ui/dialogs/layout_manager_dialog.py

- **Zeilen:** 217 (Code: 163)
- **Checksum:** `4ce8ada63ba1f54db1dee4f811f6583d`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `LayoutManagerDialog` (Zeile 30-216) 🖥️

---

### src/ui/dialogs/optimization_tabs_mixin.py

- **Zeilen:** 292 (Code: 216)
- **Checksum:** `0100dfcb5a719bc6d3bd040d4403a71c`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `OptimizationTabsMixin` (Zeile 27-291)

---

### src/ui/dialogs/order_dialog.py

- **Zeilen:** 286 (Code: 211)
- **Checksum:** `5603961ba9f31f3138974cfc11bdf4c8`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `OrderDialog` (Zeile 27-285) 🖥️

---

### src/ui/dialogs/parameter_optimization_dialog.py

- **Zeilen:** 412 (Code: 290)
- **Checksum:** `e896f0ec99b49b2e06ca6c48fc6b8663`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `ParameterOptimizationDialog` (Zeile 36-411) 🖥️

---

### src/ui/dialogs/pattern_db_build_mixin.py

- **Zeilen:** 201 (Code: 164)
- **Checksum:** `94ba9defa12bef63e2b1a2c828622b92`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `PatternDbBuildMixin` (Zeile 32-200)

---

### src/ui/dialogs/pattern_db_dialog.py

- **Zeilen:** 53 (Code: 42)
- **Checksum:** `c8cb77e31cab077734caf0ab72c6c9c7`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `PatternDatabaseDialog` (Zeile 18-52) 🖥️

---

### src/ui/dialogs/pattern_db_docker_mixin.py

- **Zeilen:** 109 (Code: 96)
- **Checksum:** `580d146aafffd43548a3df4f841413b6`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `PatternDbDockerMixin` (Zeile 32-108)

---

### src/ui/dialogs/pattern_db_lifecycle_mixin.py

- **Zeilen:** 41 (Code: 33)
- **Checksum:** `7da2266a1f6b569e5a6ef1fe76988b65`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `PatternDbLifecycleMixin` (Zeile 32-40)

---

### src/ui/dialogs/pattern_db_log_mixin.py

- **Zeilen:** 77 (Code: 62)
- **Checksum:** `33e2ff0e6cfba67d1a3fea6723ada2b6`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `PatternDbLogMixin` (Zeile 32-76)

---

### src/ui/dialogs/pattern_db_search_mixin.py

- **Zeilen:** 131 (Code: 100)
- **Checksum:** `492f10171e7448e0f95785883c913359`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `PatternDbSearchMixin` (Zeile 32-130)

---

### src/ui/dialogs/pattern_db_settings_mixin.py

- **Zeilen:** 154 (Code: 123)
- **Checksum:** `47d4c53eb5cdf68e248693cdda390afa`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `PatternDbSettingsMixin` (Zeile 32-153)

---

### src/ui/dialogs/pattern_db_tabs_mixin.py

- **Zeilen:** 377 (Code: 284)
- **Checksum:** `d219b9f49d78b23499178d189e67661c`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `PatternDbTabsMixin` (Zeile 41-376)

---

### src/ui/dialogs/pattern_db_ui_mixin.py

- **Zeilen:** 109 (Code: 90)
- **Checksum:** `df8e84fd540c9a24075f321c7be59565`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `PatternDbUIMixin` (Zeile 32-108)

---

### src/ui/dialogs/pattern_db_worker.py

- **Zeilen:** 158 (Code: 121)
- **Checksum:** `143475b5e65c7fd22929aa4cb573541f`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `DatabaseBuildWorker` (Zeile 15-157)

---

### src/ui/dialogs/settings_dialog.py

- **Zeilen:** 402 (Code: 302)
- **Checksum:** `778825824768358941c53c63775d3a18`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `SettingsDialog` (Zeile 27-401) 🖥️

---

### src/ui/dialogs/settings_tabs_mixin.py

- **Zeilen:** 362 (Code: 260)
- **Checksum:** `2796abd14ed21f57f587632a44aa8a59`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `SettingsTabsMixin` (Zeile 19-361)

---

### src/ui/dialogs/zone_edit_dialog.py

- **Zeilen:** 218 (Code: 159)
- **Checksum:** `5fa021a33b07ec90b05b49a69895b7ed`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `ZoneEditDialog` (Zeile 32-217) 🖥️

---

### src/ui/icons.py

- **Zeilen:** 243 (Code: 187)
- **Checksum:** `bdb7e86c7e881d6f540a59c5d966f928`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `IconProvider` (Zeile 145-208)

**Top-Level Funktionen:**
- `_svg_to_icon(svg_data: str, primary_color: str, secondary_color: str) -> QIcon` (Zeile 11)
- `get_icon(name: str) -> QIcon` (Zeile 215)
- `set_icon_theme(theme: str)` (Zeile 227)
- `get_available_icons() -> list[str]` (Zeile 236)

---

### src/ui/multi_chart/__init__.py

- **Zeilen:** 15 (Code: 11)
- **Checksum:** `57170f9c3c00e662deac082b20ebe10d`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/multi_chart/chart_set_dialog.py

- **Zeilen:** 359 (Code: 285)
- **Checksum:** `1dfdce686f97d0d76b57f7c28f139fde`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `ChartSetDialog` (Zeile 38-358) 🖥️

---

### src/ui/multi_chart/layout_manager.py

- **Zeilen:** 566 (Code: 446)
- **Checksum:** `210319f4ee5c40d5b86b17326577f105`
- **Funktionen:** 23
- **Klassen:** 3

**Klassen:**
- `ChartWindowConfig` (Zeile 29-50)
- `ChartLayoutConfig` (Zeile 54-83)
- `ChartLayoutManager` (Zeile 86-565)

---

### src/ui/themes.py

- **Zeilen:** 359 (Code: 298)
- **Checksum:** `0b788cc0109511c7094bf88359196ae8`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `ThemeManager` (Zeile 7-359)

---

### src/ui/widgets/__init__.py

- **Zeilen:** 1 (Code: 1)
- **Checksum:** `64862d097cae28ae0b0339c020945d52`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/widgets/alerts.py

- **Zeilen:** 80 (Code: 60)
- **Checksum:** `2aca5a23a536921b09f95d803bbd8150`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `AlertsWidget` (Zeile 12-80) 🖥️

---

### src/ui/widgets/backtest_chart_widget.py

- **Zeilen:** 289 (Code: 206)
- **Checksum:** `eaa5251b570269e6a7b9cfaf2e2897b8`
- **Funktionen:** 15
- **Klassen:** 1

**Klassen:**
- `BacktestChartWidget` (Zeile 29-288) 🖥️

---

### src/ui/widgets/base_chart_widget.py

- **Zeilen:** 97 (Code: 74)
- **Checksum:** `e4dfca3a908a8c6e376316deac11d8e8`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `BaseChartWidget` (Zeile 17-96) 🖥️

---

### src/ui/widgets/candlestick_item.py

- **Zeilen:** 199 (Code: 147)
- **Checksum:** `b7824488c0187a9a43dcebd6edd8da35`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `CandlestickItem` (Zeile 20-186)

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
- `ChartSignals` (Zeile 90-108)
- `BaseChartWidget` (Zeile 111-198)
- `ChartCapabilities` (Zeile 201-243)

**Top-Level Funktionen:**
- `register_chart_adapter(widget_class, capabilities: ChartCapabilities) -> None` (Zeile 246)
- `get_chart_capabilities(widget_class) -> Optional[ChartCapabilities]` (Zeile 258)

---

### src/ui/widgets/chart_js_template.py

- **Zeilen:** 33 (Code: 21)
- **Checksum:** `cef80730742983313f2875cf5f38dc43`
- **Funktionen:** 2
- **Klassen:** 0

**Top-Level Funktionen:**
- `_load_chart_template() -> str` (Zeile 14)
- `get_chart_html_template() -> str` (Zeile 22)

---

### src/ui/widgets/chart_mixins/__init__.py

- **Zeilen:** 22 (Code: 18)
- **Checksum:** `1046a084ea72d6857ae591fec237d953`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/widgets/chart_mixins/bot_overlay_mixin.py

- **Zeilen:** 562 (Code: 449)
- **Checksum:** `73159b0a32a23a7a68c3a71d5054182e`
- **Funktionen:** 22
- **Klassen:** 1

**Klassen:**
- `BotOverlayMixin` (Zeile 40-561)

---

### src/ui/widgets/chart_mixins/bot_overlay_types.py

- **Zeilen:** 132 (Code: 111)
- **Checksum:** `f04b86f3bb70ed52d9c5d71c6f0bd8ac`
- **Funktionen:** 2
- **Klassen:** 4

**Klassen:**
- `MarkerType` (Zeile 13-21)
- `BotMarker` (Zeile 25-74)
- `StopLine` (Zeile 78-85)
- `BotOverlayState` (Zeile 89-96)

**Top-Level Funktionen:**
- `build_hud_content(state: str, regime: str, strategy: str, trailing_mode: str, ki_mode: str, confidence: float, extra: dict[str, Any] | None) -> str` (Zeile 106)

---

### src/ui/widgets/chart_mixins/data_loading_mixin.py

- **Zeilen:** 453 (Code: 319)
- **Checksum:** `24acc90cfcade874adbc05556c6b9d45`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `DataLoadingMixin` (Zeile 31-452)

**Top-Level Funktionen:**
- `get_local_timezone_offset_seconds() -> int` (Zeile 19)

---

### src/ui/widgets/chart_mixins/indicator_mixin.py

- **Zeilen:** 567 (Code: 429)
- **Checksum:** `d9c4cf1e19c5588f446c3d51068ae7be`
- **Funktionen:** 15
- **Klassen:** 1

**Klassen:**
- `IndicatorMixin` (Zeile 23-566)

**Top-Level Funktionen:**
- `_ts_to_local_unix(ts) -> int` (Zeile 18)

---

### src/ui/widgets/chart_mixins/state_mixin.py

- **Zeilen:** 151 (Code: 118)
- **Checksum:** `5421152c487425c8ed9365f036b97d22`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `ChartStateMixin` (Zeile 12-150)

---

### src/ui/widgets/chart_mixins/streaming_mixin.py

- **Zeilen:** 418 (Code: 296)
- **Checksum:** `25196dff863ed948016f21c3765bc7fe`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `StreamingMixin` (Zeile 20-417)

---

### src/ui/widgets/chart_mixins/toolbar_mixin.py

- **Zeilen:** 400 (Code: 324)
- **Checksum:** `04dc2eafdebcc2e8b4142a936f4997c4`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `ToolbarMixin` (Zeile 20-399)

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
- `PyQtGraphChartStateMixin` (Zeile 419-491)

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
- `ChartStateManager` (Zeile 83-361)
- `TradingViewChartStateHelper` (Zeile 364-433)
- `PyQtGraphChartStateHelper` (Zeile 436-500)

**Top-Level Funktionen:**
- `get_chart_state_manager() -> ChartStateManager` (Zeile 506)

---

### src/ui/widgets/chart_window.py

- **Zeilen:** 558 (Code: 404)
- **Checksum:** `5bd150e17bde22b4c180a8785fa5309f`
- **Funktionen:** 17
- **Klassen:** 2

**Klassen:**
- `DockTitleBar` (Zeile 38-153) 🖥️
- `ChartWindow` (Zeile 156-557) 🖥️

---

### src/ui/widgets/chart_window_mixins/__init__.py

- **Zeilen:** 21 (Code: 17)
- **Checksum:** `73cecff2a7fb1b9e2d248e1fb1ca39d3`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/widgets/chart_window_mixins/bot_callbacks.py

- **Zeilen:** 16 (Code: 12)
- **Checksum:** `19d527edbda93663c28676eb16e80d09`
- **Funktionen:** 0
- **Klassen:** 1

**Klassen:**
- `BotCallbacksMixin` (Zeile 9-15)

---

### src/ui/widgets/chart_window_mixins/bot_callbacks_candle_mixin.py

- **Zeilen:** 233 (Code: 175)
- **Checksum:** `f7ebf230745afde2f09415c19c89a05d`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `BotCallbacksCandleMixin` (Zeile 9-232)

---

### src/ui/widgets/chart_window_mixins/bot_callbacks_lifecycle_mixin.py

- **Zeilen:** 124 (Code: 90)
- **Checksum:** `10773c0c372d5f4fa657adda3169653c`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `BotCallbacksLifecycleMixin` (Zeile 9-123)

---

### src/ui/widgets/chart_window_mixins/bot_callbacks_log_order_mixin.py

- **Zeilen:** 100 (Code: 78)
- **Checksum:** `65b2dd7f8d3e2fbe5fe11c2d73bd49fc`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `BotCallbacksLogOrderMixin` (Zeile 10-99)

---

### src/ui/widgets/chart_window_mixins/bot_callbacks_signal_mixin.py

- **Zeilen:** 474 (Code: 380)
- **Checksum:** `877c0aa3011d383d3ea5b89e25384d2d`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `BotCallbacksSignalMixin` (Zeile 10-473)

---

### src/ui/widgets/chart_window_mixins/bot_derivative_mixin.py

- **Zeilen:** 302 (Code: 235)
- **Checksum:** `0786206561e6a8adfa788c9c140ce69d`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `BotDerivativeMixin` (Zeile 20-301)

---

### src/ui/widgets/chart_window_mixins/bot_display_logging_mixin.py

- **Zeilen:** 81 (Code: 67)
- **Checksum:** `70a939643cdc54a11782572c1d84ce29`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `BotDisplayLoggingMixin` (Zeile 6-80)

---

### src/ui/widgets/chart_window_mixins/bot_display_manager.py

- **Zeilen:** 18 (Code: 14)
- **Checksum:** `550060740f8301645bb3ab0ffd4d3745`
- **Funktionen:** 0
- **Klassen:** 1

**Klassen:**
- `BotDisplayManagerMixin` (Zeile 10-17)

---

### src/ui/widgets/chart_window_mixins/bot_display_metrics_mixin.py

- **Zeilen:** 46 (Code: 40)
- **Checksum:** `0ac84a8f71449901235cb49d78bd1c94`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `BotDisplayMetricsMixin` (Zeile 6-45)

---

### src/ui/widgets/chart_window_mixins/bot_display_position_mixin.py

- **Zeilen:** 496 (Code: 400)
- **Checksum:** `10af085fdcf3b3d008b4b851e76e78ef`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `BotDisplayPositionMixin` (Zeile 5-495)

---

### src/ui/widgets/chart_window_mixins/bot_display_selection_mixin.py

- **Zeilen:** 48 (Code: 42)
- **Checksum:** `5ad1dddbc6d55823073e34df4a31eddd`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `BotDisplaySelectionMixin` (Zeile 5-47)

---

### src/ui/widgets/chart_window_mixins/bot_display_signals_mixin.py

- **Zeilen:** 345 (Code: 265)
- **Checksum:** `489247d26ee2577ef3493cc1c9cef250`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `BotDisplaySignalsMixin` (Zeile 11-344)

---

### src/ui/widgets/chart_window_mixins/bot_event_handlers.py

- **Zeilen:** 346 (Code: 249)
- **Checksum:** `16405b5295ce7fac8bdb01058f3373b1`
- **Funktionen:** 14
- **Klassen:** 1

**Klassen:**
- `BotEventHandlersMixin` (Zeile 22-345)

---

### src/ui/widgets/chart_window_mixins/bot_panels_mixin.py

- **Zeilen:** 299 (Code: 213)
- **Checksum:** `70f86720f5151caeaf67469b94cda6e0`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `BotPanelsMixin` (Zeile 38-298)

---

### src/ui/widgets/chart_window_mixins/bot_position_persistence.py

- **Zeilen:** 20 (Code: 16)
- **Checksum:** `20bcec9e5505a006abcf31d7ca17f22f`
- **Funktionen:** 0
- **Klassen:** 1

**Klassen:**
- `BotPositionPersistenceMixin` (Zeile 11-19)

---

### src/ui/widgets/chart_window_mixins/bot_position_persistence_chart_mixin.py

- **Zeilen:** 192 (Code: 149)
- **Checksum:** `28d6966f257eed1c5e9227d52a3e184e`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `BotPositionPersistenceChartMixin` (Zeile 8-191)

---

### src/ui/widgets/chart_window_mixins/bot_position_persistence_context_mixin.py

- **Zeilen:** 134 (Code: 99)
- **Checksum:** `80407ddebeb14efb4c14bc0a31f6e074`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `BotPositionPersistenceContextMixin` (Zeile 11-133)

---

### src/ui/widgets/chart_window_mixins/bot_position_persistence_pnl_mixin.py

- **Zeilen:** 91 (Code: 68)
- **Checksum:** `5333bdf572de85ae3589216a829f80b7`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `BotPositionPersistencePnlMixin` (Zeile 9-90)

---

### src/ui/widgets/chart_window_mixins/bot_position_persistence_restore_mixin.py

- **Zeilen:** 137 (Code: 106)
- **Checksum:** `c25dda4eed8c1c7bcdf3a4a10e4ac214`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `BotPositionPersistenceRestoreMixin` (Zeile 11-136)

---

### src/ui/widgets/chart_window_mixins/bot_position_persistence_storage_mixin.py

- **Zeilen:** 64 (Code: 51)
- **Checksum:** `b48a931b29b5f55acce95954be663e06`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `BotPositionPersistenceStorageMixin` (Zeile 10-63)

---

### src/ui/widgets/chart_window_mixins/bot_tr_lock_mixin.py

- **Zeilen:** 150 (Code: 113)
- **Checksum:** `1d3b93c7405c2d2eb1326204be15580c`
- **Funktionen:** 3
- **Klassen:** 1

**Klassen:**
- `BotTRLockMixin` (Zeile 22-149)

---

### src/ui/widgets/chart_window_mixins/bot_ui_control_mixin.py

- **Zeilen:** 435 (Code: 348)
- **Checksum:** `a68f3552ecbc2fbacb5d85dab845e83d`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `BotUIControlMixin` (Zeile 12-434)

---

### src/ui/widgets/chart_window_mixins/bot_ui_ki_logs_mixin.py

- **Zeilen:** 56 (Code: 38)
- **Checksum:** `03076d34ff539ecb72d41537493cf1ae`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `BotUIKILogsMixin` (Zeile 6-55)

---

### src/ui/widgets/chart_window_mixins/bot_ui_panels.py

- **Zeilen:** 16 (Code: 12)
- **Checksum:** `ea7bb17f0650c6dd8b1f6322ec9679a5`
- **Funktionen:** 0
- **Klassen:** 1

**Klassen:**
- `BotUIPanelsMixin` (Zeile 9-15)

---

### src/ui/widgets/chart_window_mixins/bot_ui_signals_mixin.py

- **Zeilen:** 157 (Code: 108)
- **Checksum:** `b761d0f9275cf02823f8df5673480727`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `BotUISignalsMixin` (Zeile 7-156)

---

### src/ui/widgets/chart_window_mixins/bot_ui_strategy_mixin.py

- **Zeilen:** 82 (Code: 59)
- **Checksum:** `9f7105b0397768c432c3df28fda602f8`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `BotUIStrategyMixin` (Zeile 6-81)

---

### src/ui/widgets/chart_window_mixins/event_bus_mixin.py

- **Zeilen:** 263 (Code: 187)
- **Checksum:** `e02babd08659e6e073d9d615e1e1388d`
- **Funktionen:** 13
- **Klassen:** 1

**Klassen:**
- `EventBusMixin` (Zeile 20-262)

**Top-Level Funktionen:**
- `_ts_to_chart_time(timestamp) -> int` (Zeile 15)

---

### src/ui/widgets/chart_window_mixins/ko_finder_mixin.py

- **Zeilen:** 358 (Code: 253)
- **Checksum:** `7103ab264e07b3bd5f0a7260acf23119`
- **Funktionen:** 13
- **Klassen:** 2

**Klassen:**
- `KOFinderWorker` (Zeile 28-68)
- `KOFinderMixin` (Zeile 71-357)

---

### src/ui/widgets/chart_window_mixins/panels_mixin.py

- **Zeilen:** 89 (Code: 59)
- **Checksum:** `10385d3f14873531bd3f6616d682cd15`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `PanelsMixin` (Zeile 18-88)

---

### src/ui/widgets/chart_window_mixins/state_mixin.py

- **Zeilen:** 371 (Code: 278)
- **Checksum:** `2e0db75720f7daa53c3b10d38e0b3a67`
- **Funktionen:** 16
- **Klassen:** 1

**Klassen:**
- `StateMixin` (Zeile 15-370)

---

### src/ui/widgets/chart_window_mixins/strategy_simulator_mixin.py

- **Zeilen:** 35 (Code: 28)
- **Checksum:** `60ff30afbe113011d6ede2821e1e0f58`
- **Funktionen:** 0
- **Klassen:** 1

**Klassen:**
- `StrategySimulatorMixin` (Zeile 12-34)

---

### src/ui/widgets/chart_window_mixins/strategy_simulator_params_mixin.py

- **Zeilen:** 370 (Code: 334)
- **Checksum:** `83e1b93529eb329b3434953193a3771e`
- **Funktionen:** 22
- **Klassen:** 1

**Klassen:**
- `StrategySimulatorParamsMixin` (Zeile 8-369)

---

### src/ui/widgets/chart_window_mixins/strategy_simulator_results_mixin.py

- **Zeilen:** 471 (Code: 406)
- **Checksum:** `0761f673decd466dd3d20320e564d156`
- **Funktionen:** 16
- **Klassen:** 1

**Klassen:**
- `StrategySimulatorResultsMixin` (Zeile 8-470)

---

### src/ui/widgets/chart_window_mixins/strategy_simulator_run_mixin.py

- **Zeilen:** 377 (Code: 327)
- **Checksum:** `e15f4525338133421265101ab92ec5d2`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `StrategySimulatorRunMixin` (Zeile 10-376)

---

### src/ui/widgets/chart_window_mixins/strategy_simulator_ui_mixin.py

- **Zeilen:** 357 (Code: 278)
- **Checksum:** `d6d5e6f70eef95a9b5aa18531c59b4aa`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `StrategySimulatorUIMixin` (Zeile 10-356)

---

### src/ui/widgets/chart_window_mixins/strategy_simulator_worker.py

- **Zeilen:** 188 (Code: 162)
- **Checksum:** `f1a0d9229ef9f4eaae78279f93c38983`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `SimulationWorker` (Zeile 16-187)

---

### src/ui/widgets/dashboard.py

- **Zeilen:** 167 (Code: 114)
- **Checksum:** `3a48f200365ac00068d075b8b580bb8b`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `DashboardWidget` (Zeile 10-167) 🖥️

---

### src/ui/widgets/dashboard_metrics.py

- **Zeilen:** 82 (Code: 62)
- **Checksum:** `650628a74230475acb8a911580853dd9`
- **Funktionen:** 2
- **Klassen:** 2

**Klassen:**
- `PerformanceMetrics` (Zeile 14-34)
- `MetricCard` (Zeile 37-81) 🖥️

---

### src/ui/widgets/dashboard_tabs_mixin.py

- **Zeilen:** 359 (Code: 262)
- **Checksum:** `6b0fdf1073be0e5e04dd5ebd2d1b34c7`
- **Funktionen:** 6
- **Klassen:** 1

**Klassen:**
- `DashboardTabsMixin` (Zeile 31-358)

---

### src/ui/widgets/embedded_tradingview_bridge.py

- **Zeilen:** 56 (Code: 40)
- **Checksum:** `4226cd769e20d18744bd500c1a89fcd1`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `ChartBridge` (Zeile 8-55)

---

### src/ui/widgets/embedded_tradingview_chart.py

- **Zeilen:** 146 (Code: 105)
- **Checksum:** `400e9785bb9f72b77bc04d7f4b5476e0`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `EmbeddedTradingViewChart` (Zeile 45-145) 🖥️

---

### src/ui/widgets/embedded_tradingview_chart_events_mixin.py

- **Zeilen:** 31 (Code: 23)
- **Checksum:** `a0a571dd7b710023dfac95ce84e91b32`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `EmbeddedTradingViewChartEventsMixin` (Zeile 8-30)

---

### src/ui/widgets/embedded_tradingview_chart_js_mixin.py

- **Zeilen:** 29 (Code: 24)
- **Checksum:** `3f74734077e0e8ec0fc099ae20aa00bd`
- **Funktionen:** 2
- **Klassen:** 1

**Klassen:**
- `EmbeddedTradingViewChartJSMixin` (Zeile 8-28)

---

### src/ui/widgets/embedded_tradingview_chart_loading_mixin.py

- **Zeilen:** 57 (Code: 46)
- **Checksum:** `abce2c3b54ea0c9627b8fb6c1f8c044c`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `EmbeddedTradingViewChartLoadingMixin` (Zeile 9-56)

---

### src/ui/widgets/embedded_tradingview_chart_marking_mixin.py

- **Zeilen:** 325 (Code: 257)
- **Checksum:** `414ad0c5720c331ef5d38c3cd3bc05de`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `EmbeddedTradingViewChartMarkingMixin` (Zeile 9-324)

---

### src/ui/widgets/embedded_tradingview_chart_ui_mixin.py

- **Zeilen:** 224 (Code: 157)
- **Checksum:** `7f33ac588d5c1c35c0518eb86dbd8f72`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `EmbeddedTradingViewChartUIMixin` (Zeile 10-223)

---

### src/ui/widgets/embedded_tradingview_chart_view_mixin.py

- **Zeilen:** 65 (Code: 45)
- **Checksum:** `681f9359afe4598864488e710ddce9ba`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `EmbeddedTradingViewChartViewMixin` (Zeile 8-64)

---

### src/ui/widgets/indicators.py

- **Zeilen:** 166 (Code: 124)
- **Checksum:** `4954d840f6c2ef89c57a80e79a0be4d4`
- **Funktionen:** 4
- **Klassen:** 1

**Klassen:**
- `IndicatorsWidget` (Zeile 27-165) 🖥️

---

### src/ui/widgets/ko_finder/__init__.py

- **Zeilen:** 22 (Code: 18)
- **Checksum:** `6fa82c10be9bedd624b1bba6a0b5270e`
- **Funktionen:** 0
- **Klassen:** 0

---

### src/ui/widgets/ko_finder/filter_panel.py

- **Zeilen:** 239 (Code: 176)
- **Checksum:** `4dd2e1c0e5c8858da40a462a6f5eccaa`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `KOFilterPanel` (Zeile 37-238) 🖥️

---

### src/ui/widgets/ko_finder/result_panel.py

- **Zeilen:** 358 (Code: 266)
- **Checksum:** `3bb981bc3c5e7e83e5d69cb80888315a`
- **Funktionen:** 14
- **Klassen:** 1

**Klassen:**
- `KOResultPanel` (Zeile 41-357) 🖥️

---

### src/ui/widgets/ko_finder/settings_dialog.py

- **Zeilen:** 327 (Code: 245)
- **Checksum:** `5589a422add28d29e81717007d656a5a`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `KOSettingsDialog` (Zeile 35-326) 🖥️

---

### src/ui/widgets/ko_finder/table_model.py

- **Zeilen:** 270 (Code: 204)
- **Checksum:** `15a2ac417162117f50e5c7219ef8baaa`
- **Funktionen:** 14
- **Klassen:** 1

**Klassen:**
- `KOProductTableModel` (Zeile 19-269)

---

### src/ui/widgets/orders.py

- **Zeilen:** 76 (Code: 53)
- **Checksum:** `3925b4d4f17baa08f6b7a6c226684d25`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `OrdersWidget` (Zeile 9-76)

---

### src/ui/widgets/performance_dashboard.py

- **Zeilen:** 376 (Code: 257)
- **Checksum:** `77ebdd3526e90ee37ece402f28b7105a`
- **Funktionen:** 14
- **Klassen:** 1

**Klassen:**
- `PerformanceDashboard` (Zeile 47-375) 🖥️

---

### src/ui/widgets/positions.py

- **Zeilen:** 91 (Code: 67)
- **Checksum:** `e67fdb94d66cf6b817df2937bdec4e07`
- **Funktionen:** 8
- **Klassen:** 1

**Klassen:**
- `PositionsWidget` (Zeile 12-91)

---

### src/ui/widgets/watchlist.py

- **Zeilen:** 588 (Code: 435)
- **Checksum:** `1814740b31d1d827bbae48461a65e471`
- **Funktionen:** 23
- **Klassen:** 1

**Klassen:**
- `WatchlistWidget` (Zeile 43-587) 🖥️

---

### src/ui/widgets/watchlist_presets.py

- **Zeilen:** 79 (Code: 59)
- **Checksum:** `2bf956a54d55a2acecf20678d25ab963`
- **Funktionen:** 1
- **Klassen:** 1

**Klassen:**
- `SymbolInfo` (Zeile 11-15)

**Top-Level Funktionen:**
- `format_volume(volume: int) -> str` (Zeile 57)

---

### src/ui/widgets/widget_helpers.py

- **Zeilen:** 349 (Code: 249)
- **Checksum:** `80aad622d4eaf0f35cce4202f70f67b9`
- **Funktionen:** 18
- **Klassen:** 2

**Klassen:**
- `EventBusWidget` (Zeile 168-215) 🖥️
- `BaseTableWidget` (Zeile 220-348)

**Top-Level Funktionen:**
- `create_table_widget(columns: list[str], stretch_columns: bool, selection_behavior: QTableWidget.SelectionBehavior, selection_mode: QTableWidget.SelectionMode, editable: bool, alternating_colors: bool, sortable: bool) -> QTableWidget` (Zeile 23)
- `setup_table_row(table: QTableWidget, row: int, data: dict[str, Any], column_keys: list[str], format_funcs: dict[str, Any] | None) -> None` (Zeile 72)
- `create_vbox_layout(parent: QWidget | None, spacing: int, margins: tuple[int, int, int, int] | None) -> QVBoxLayout` (Zeile 106)
- `create_hbox_layout(parent: QWidget | None, spacing: int, margins: tuple[int, int, int, int] | None) -> QHBoxLayout` (Zeile 126)
- `create_grid_layout(parent: QWidget | None, spacing: int, margins: tuple[int, int, int, int] | None) -> QGridLayout` (Zeile 146)

---

### start_orderpilot.py

- **Zeilen:** 272 (Code: 203)
- **Checksum:** `d588372ecf74c1192b9ce2e5b430c936`
- **Funktionen:** 9
- **Klassen:** 0

**Top-Level Funktionen:**
- `check_ai_api_keys() -> None` (Zeile 19)
- `setup_logging(log_level: str) -> None` (Zeile 50)
- `check_dependencies() -> bool` (Zeile 69)
- `check_database() -> None` (Zeile 101)
- `print_startup_banner() -> None` (Zeile 118)
- `async main_with_args(args: argparse.Namespace) -> None` (Zeile 137)
- `create_parser() -> argparse.ArgumentParser` (Zeile 153)
- `main() -> int` (Zeile 209)
- `global_exception_handler(exc_type, exc_value, exc_traceback)` (Zeile 212)

---

### tests/__init__.py

- **Zeilen:** 1 (Code: 1)
- **Checksum:** `a430661beaca7a0373c6a67c9023928e`
- **Funktionen:** 0
- **Klassen:** 0

---

### tests/derivatives/__init__.py

- **Zeilen:** 2 (Code: 1)
- **Checksum:** `d637b080e8c3426b43b880078baaf302`
- **Funktionen:** 0
- **Klassen:** 0

---

### tests/derivatives/ko_finder/__init__.py

- **Zeilen:** 2 (Code: 1)
- **Checksum:** `8b36ff806998891efb8db04a03f2f6dd`
- **Funktionen:** 0
- **Klassen:** 0

---

### tests/derivatives/ko_finder/test_filters.py

- **Zeilen:** 135 (Code: 103)
- **Checksum:** `c78ca4b15d81a79e47d3c0efb5834597`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `TestHardFilters` (Zeile 34-134)

**Top-Level Funktionen:**
- `create_test_product(wkn: str, leverage: float, spread_pct: float, ko_distance_pct: float, issuer: str, bid: float, ask: float, direction: Direction) -> KnockoutProduct` (Zeile 12)

---

### tests/derivatives/ko_finder/test_models.py

- **Zeilen:** 180 (Code: 137)
- **Checksum:** `7132fab994145496b3ef7196a68e8b60`
- **Funktionen:** 15
- **Klassen:** 4

**Klassen:**
- `TestQuote` (Zeile 18-45)
- `TestKnockoutProduct` (Zeile 48-109)
- `TestKOFilterConfig` (Zeile 112-156)
- `TestSearchResponse` (Zeile 159-179)

---

### tests/derivatives/ko_finder/test_ranking.py

- **Zeilen:** 140 (Code: 101)
- **Checksum:** `2fdd67957d536f75bc78bf763dd13351`
- **Funktionen:** 9
- **Klassen:** 1

**Klassen:**
- `TestRankingEngine` (Zeile 31-139)

**Top-Level Funktionen:**
- `create_test_product(wkn: str, leverage: float, spread_pct: float, ko_distance_pct: float, parser_confidence: float) -> KnockoutProduct` (Zeile 11)

---

### tests/derivatives/ko_finder/test_url_builder.py

- **Zeilen:** 77 (Code: 54)
- **Checksum:** `c98472e8c352d5b3afbaec87129593ba`
- **Funktionen:** 7
- **Klassen:** 1

**Klassen:**
- `TestOnvistaURLBuilder` (Zeile 10-76)

---

### tests/test_ai_backtest_review.py

- **Zeilen:** 443 (Code: 383)
- **Checksum:** `a2c6ff6476be0807868db61bc61f3cbd`
- **Funktionen:** 11
- **Klassen:** 4

**Klassen:**
- `TestBacktestReviewModel` (Zeile 126-185)
- `TestReviewBacktestMethod` (Zeile 188-319)
- `TestPromptBuilderIntegration` (Zeile 322-354)
- `TestEndToEndIntegration` (Zeile 357-438)

**Top-Level Funktionen:**
- `ai_config()` (Zeile 26)
- `sample_backtest_result()` (Zeile 38)

---

### tests/test_backtest_converter.py

- **Zeilen:** 206 (Code: 171)
- **Checksum:** `357895d9a0d384eb879d533e2d854250`
- **Funktionen:** 6
- **Klassen:** 2

**Klassen:**
- `TestBacktestConverter` (Zeile 15-169)
- `TestConverterFunctions` (Zeile 172-201)

---

### tests/test_broker_adapter.py

- **Zeilen:** 244 (Code: 174)
- **Checksum:** `0384f0a48950860cc70da2c9a4a40430`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `TestMockBrokerAdapter` (Zeile 12-244)

---

### tests/test_chart_adapter.py

- **Zeilen:** 373 (Code: 281)
- **Checksum:** `1935a3a2ab15c64bbca24a17a6b1fe3b`
- **Funktionen:** 16
- **Klassen:** 1

**Klassen:**
- `TestChartAdapter` (Zeile 23-368)

---

### tests/test_chart_bridge.py

- **Zeilen:** 280 (Code: 200)
- **Checksum:** `77d5f9b8e3d236f0e6f8db72027c5ac1`
- **Funktionen:** 12
- **Klassen:** 1

**Klassen:**
- `TestChartBridge` (Zeile 24-275)

---

### tests/test_chart_persistence.py

- **Zeilen:** 95 (Code: 57)
- **Checksum:** `c0b1c2657836223af4a6d89eb732e21e`
- **Funktionen:** 5
- **Klassen:** 1

**Klassen:**
- `TestChartPersistence` (Zeile 10-94)

---

### tests/test_config.py

- **Zeilen:** 171 (Code: 125)
- **Checksum:** `92590ce3f8dd09da58e8fe6514413ac5`
- **Funktionen:** 10
- **Klassen:** 1

**Klassen:**
- `TestConfiguration` (Zeile 19-170)

---

### tests/test_crypto_integration.py

- **Zeilen:** 305 (Code: 223)
- **Checksum:** `da6a4f9f6573c853563fcd648cf75ca0`
- **Funktionen:** 16
- **Klassen:** 4

**Klassen:**
- `TestAlpacaCryptoProvider` (Zeile 61-130)
- `TestAlpacaCryptoStreamClient` (Zeile 133-175)
- `TestHistoryManagerCrypto` (Zeile 178-256)
- `TestCryptoDataValidation` (Zeile 259-300)

**Top-Level Funktionen:**
- `alpaca_credentials()` (Zeile 35)
- `crypto_provider(alpaca_credentials)` (Zeile 44)
- `crypto_stream_client(alpaca_credentials)` (Zeile 53)

---

### tests/test_crypto_strategies.py

- **Zeilen:** 287 (Code: 196)
- **Checksum:** `b4730d371e10280a8d569f866db7d72f`
- **Funktionen:** 13
- **Klassen:** 4

**Klassen:**
- `TestCryptoStrategyLoading` (Zeile 25-110)
- `TestCryptoStrategyValidation` (Zeile 113-179)
- `TestCryptoStrategyCompilation` (Zeile 182-242)
- `TestCryptoStrategyMetadata` (Zeile 245-282)

**Top-Level Funktionen:**
- `strategy_loader()` (Zeile 14)
- `strategies_dir()` (Zeile 20)

---

### tests/test_database.py

- **Zeilen:** 405 (Code: 308)
- **Checksum:** `3d47d0f4f2fbe293fee282783325c751`
- **Funktionen:** 18
- **Klassen:** 1

**Klassen:**
- `TestDatabaseOperations` (Zeile 19-405)

---

### tests/test_event_bus.py

- **Zeilen:** 135 (Code: 89)
- **Checksum:** `90a1f8711ca4cf48deb10b392fc68698`
- **Funktionen:** 11
- **Klassen:** 1

**Klassen:**
- `TestEventBus` (Zeile 8-135)

---

### tests/test_execution_engine.py

- **Zeilen:** 322 (Code: 233)
- **Checksum:** `045e431050e2d9b66e386d9037c6204a`
- **Funktionen:** 14
- **Klassen:** 2

**Klassen:**
- `TestExecutionEngine` (Zeile 13-266)
- `TestExecutionTask` (Zeile 269-321)

---

### tests/test_execution_events.py

- **Zeilen:** 469 (Code: 348)
- **Checksum:** `0a1f33a9c7fff6dfaa688bf0a8b37c7a`
- **Funktionen:** 20
- **Klassen:** 6

**Klassen:**
- `TestOrderEvent` (Zeile 26-65)
- `TestExecutionEvent` (Zeile 68-109)
- `TestOrderEventEmitter` (Zeile 112-177)
- `TestExecutionEventEmitter` (Zeile 180-263)
- `TestBacktraderEventAdapter` (Zeile 266-398)
- `TestEventIntegration` (Zeile 401-468)

**Top-Level Funktionen:**
- `clear_event_history()` (Zeile 19)

---

### tests/test_integration.py

- **Zeilen:** 245 (Code: 170)
- **Checksum:** `76012417ec45430b5d1e6cb057b2cfe1`
- **Funktionen:** 10
- **Klassen:** 3

**Klassen:**
- `TestEndToEndWorkflow` (Zeile 20-157)
- `TestConfigurationIntegration` (Zeile 160-205)
- `TestDatabaseIntegration` (Zeile 208-244)

---

### tests/test_ko_finder_playwright.py

- **Zeilen:** 164 (Code: 121)
- **Checksum:** `1f9397838bb184b8c486cca6dd35e351`
- **Funktionen:** 2
- **Klassen:** 0

**Top-Level Funktionen:**
- `async test_playwright_fetch()` (Zeile 21)
- `async test_full_search()` (Zeile 87)

---

### tests/test_parameter_optimization.py

- **Zeilen:** 423 (Code: 335)
- **Checksum:** `7968d7c0b71147fb3f8145836f277918`
- **Funktionen:** 22
- **Klassen:** 6

**Klassen:**
- `TestParameterRange` (Zeile 59-72)
- `TestOptimizerConfig` (Zeile 75-97)
- `TestParameterOptimizer` (Zeile 100-320)
- `TestAIOptimizationInsight` (Zeile 323-341)
- `TestQuickOptimize` (Zeile 344-381)
- `TestOptimizationResult` (Zeile 384-418)

**Top-Level Funktionen:**
- `sample_backtest_result()` (Zeile 30)

---

### tests/test_performance.py

- **Zeilen:** 201 (Code: 151)
- **Checksum:** `f67da8c98cd0d1a5299f444c61b39a8a`
- **Funktionen:** 21
- **Klassen:** 3

**Klassen:**
- `TestPerformanceMonitor` (Zeile 17-98)
- `TestPerformanceDecorators` (Zeile 101-160)
- `TestPerformanceTimer` (Zeile 163-200)

---

### tests/test_post_refactoring.py

- **Zeilen:** 409 (Code: 318)
- **Checksum:** `f35b088ef3fd56de95eb079e461e9987`
- **Funktionen:** 7
- **Klassen:** 0

**Top-Level Funktionen:**
- `test_tradingbot_imports()` (Zeile 19)
- `test_broker_imports()` (Zeile 124)
- `test_optimization_imports()` (Zeile 150)
- `test_ui_imports()` (Zeile 169)
- `test_split_modules_direct()` (Zeile 195)
- `test_class_instantiation()` (Zeile 300)
- `run_all_tests()` (Zeile 341)

---

### tests/test_security.py

- **Zeilen:** 259 (Code: 163)
- **Checksum:** `2d15fe00c4231ed37bb71aef11fb306f`
- **Funktionen:** 21
- **Klassen:** 6

**Klassen:**
- `TestEncryption` (Zeile 18-58)
- `TestCredentialManager` (Zeile 61-96)
- `TestSessionManager` (Zeile 99-153)
- `TestRateLimiter` (Zeile 156-196)
- `TestPasswordUtils` (Zeile 199-232)
- `TestAPIKey` (Zeile 235-259)

---

### tests/test_skeleton.py

- **Zeilen:** 5 (Code: 4)
- **Checksum:** `5ce2a42490b9c732f3742d952ddcd178`
- **Funktionen:** 1
- **Klassen:** 0

**Top-Level Funktionen:**
- `test_skeleton_imports()` (Zeile 1)

---

### tests/test_strategy_compiler.py

- **Zeilen:** 524 (Code: 423)
- **Checksum:** `e2062063ef04e97df48cb2937c4ab05e`
- **Funktionen:** 19
- **Klassen:** 19

**Klassen:**
- `TestIndicatorFactory` (Zeile 27-70)
- `TestConditionEvaluator` (Zeile 73-302)
- `TestStrategyCompiler` (Zeile 305-478)
- `MockStrategy` (Zeile 79-88)
- `MockStrategy` (Zeile 111-114)
- `MockStrategy` (Zeile 137-140)
- `MockStrategy` (Zeile 163-166)
- `MockStrategy` (Zeile 193-196)
- `MockStrategy` (Zeile 223-226)
- `MockStrategy` (Zeile 251-255)
- `MockStrategy` (Zeile 278-281)
- `MockData` (Zeile 80-85)
- `MockData` (Zeile 112-113)
- `MockData` (Zeile 138-139)
- `MockData` (Zeile 164-165)
- `MockData` (Zeile 194-195)
- `MockData` (Zeile 224-225)
- `MockData` (Zeile 252-254)
- `MockData` (Zeile 279-280)

**Top-Level Funktionen:**
- `test_integration_with_backtrader()` (Zeile 481)

---

### tests/test_strategy_definition.py

- **Zeilen:** 577 (Code: 478)
- **Checksum:** `e22b5ae10f90b9973007fd10f98d4c22`
- **Funktionen:** 34
- **Klassen:** 5

**Klassen:**
- `TestIndicatorConfig` (Zeile 24-82)
- `TestCondition` (Zeile 85-155)
- `TestLogicGroup` (Zeile 158-245)
- `TestRiskManagement` (Zeile 248-310)
- `TestStrategyDefinition` (Zeile 313-572)

---

### tests/test_trading_modes.py

- **Zeilen:** 403 (Code: 330)
- **Checksum:** `f39b78136e492b78d6a25590340a22ba`
- **Funktionen:** 26
- **Klassen:** 8

**Klassen:**
- `TestTradingModeEnum` (Zeile 23-36)
- `TestProfileConfigTradingMode` (Zeile 39-67)
- `TestBacktestModeValidation` (Zeile 70-102)
- `TestPaperModeValidation` (Zeile 105-146)
- `TestLiveModeValidation` (Zeile 149-214)
- `TestModeSwitching` (Zeile 217-272)
- `TestProfileFactoryMethods` (Zeile 275-331)
- `TestModeConfigIntegration` (Zeile 334-402)

---

### tools/demo_ai_backtest_review.py

- **Zeilen:** 322 (Code: 267)
- **Checksum:** `dab650bbda5cf79fa21309379823a7fc`
- **Funktionen:** 3
- **Klassen:** 0

**Top-Level Funktionen:**
- `create_sample_backtest_result() -> BacktestResult` (Zeile 39)
- `async demo_ai_backtest_review()` (Zeile 121)
- `async main()` (Zeile 310)

---

### tools/demo_ai_providers.py

- **Zeilen:** 361 (Code: 265)
- **Checksum:** `f3bba9dabd2e5463e17f1ca96ace06ad`
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
- **Checksum:** `917e243588d86884f721ab524df118f1`
- **Funktionen:** 2
- **Klassen:** 0

**Top-Level Funktionen:**
- `create_demo_backtest_result() -> BacktestResult` (Zeile 38)
- `main()` (Zeile 226)

---

### tools/demo_crypto_integration.py

- **Zeilen:** 280 (Code: 195)
- **Checksum:** `cf0c0bf136c6b8d4532d74193ec4bcb5`
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
- **Checksum:** `cf6557a6f51f7044c4bb3f800aee134d`
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
- **Checksum:** `5cacaba4ebe5076da2fd3f6e80887ae6`
- **Funktionen:** 9
- **Klassen:** 0

**Top-Level Funktionen:**
- `demo_order_events()` (Zeile 32)
- `demo_execution_events()` (Zeile 72)
- `demo_event_listener()` (Zeile 130)
- `demo_event_history()` (Zeile 221)
- `main()` (Zeile 243)
- `on_trade_entry(event)` (Zeile 137)
- `on_trade_exit(event)` (Zeile 144)
- `on_stop_loss(event)` (Zeile 152)
- `on_take_profit(event)` (Zeile 159)

---

### tools/demo_parameter_optimization.py

- **Zeilen:** 422 (Code: 311)
- **Checksum:** `4b24bc7e21d138c4c65f1ac81f13cd81`
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
- **Checksum:** `0ac051f66ccd41fb4b46fbdd173c86fc`
- **Funktionen:** 3
- **Klassen:** 0

**Top-Level Funktionen:**
- `create_sample_data() -> bt.feeds.DataBase` (Zeile 29)
- `run_backtest_with_strategy(strategy_def: StrategyDefinition, data: bt.feeds.DataBase, initial_cash: float) -> dict` (Zeile 82)
- `main()` (Zeile 177)

---

### tools/demo_trading_modes.py

- **Zeilen:** 276 (Code: 213)
- **Checksum:** `87e127226d4c84287766117b5e23906a`
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
- **Checksum:** `ba09983f1b80963ee9df0ca238a40797`
- **Funktionen:** 3
- **Klassen:** 0

**Top-Level Funktionen:**
- `create_synthetic_data(days: int, start_price: float, volatility: float) -> bt.feeds.DataBase` (Zeile 38)
- `async run_yaml_strategy_backtest(yaml_file: Path, symbol: str, initial_cash: float) -> None` (Zeile 96)
- `async main()` (Zeile 220)

---

### tools/manage_watchlist.py

- **Zeilen:** 271 (Code: 208)
- **Checksum:** `94c2e9264a723195d992ac999212d93b`
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
- **Checksum:** `a58e5652af99e6d11d16a80c2ea98c84`
- **Funktionen:** 2
- **Klassen:** 0

**Top-Level Funktionen:**
- `create_sample_backtest_result() -> BacktestResult` (Zeile 42)
- `test_chart_adapter_pipeline()` (Zeile 249)

---

### tools/test_strategy_yaml.py

- **Zeilen:** 198 (Code: 142)
- **Checksum:** `8e3a42d7564d111f87a940cf4b79c474`
- **Funktionen:** 4
- **Klassen:** 0

**Top-Level Funktionen:**
- `load_and_validate_strategy(yaml_file: Path) -> StrategyDefinition` (Zeile 26)
- `print_strategy_details(strategy: StrategyDefinition) -> None` (Zeile 55)
- `_format_condition(cond, indent) -> str` (Zeile 114)
- `main()` (Zeile 142)

---
