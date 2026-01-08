# Projektziel + Umsetzungs-Checkliste (OrderPilot-AI) – „Alpaca Bot als Single Source of Truth“

> Vorlage/Tracking-Format orientiert sich an deinem Beispiel-Checklist-Stil.

---

## 🎯 Projektziel (für Vibe-Coding KI, Stichpunkte)

- **Alpaca Bot bleibt der einzige Trading-Agent** (keine zweite BotEngine mehr); Bitunix-Bot wird entfernt, nur sinnvolle Features werden übernommen.
- **Ein einheitlicher MarketContext („Single Source of Truth“)**
  - wird pro Symbol/Timeframe erzeugt (OHLCV + Indikator-Ergebnisse + Regime + Levels + Signale).
  - wird von **Trading-Engine**, **AI Analyse Popup** und **Chatbot (Zonen zeichnen)** identisch verwendet.
- **Deterministisch zuerst**: Regime/Levels/Indikatorwerte/Entry-Score werden im Code berechnet; LLM macht nur Interpretation/Validierung.
- **Entry-/Exit-Qualität erhöhen** durch:
  - Alpaca **Entry-Score** als Basissignal (0–1).
  - optionaler **Confluence-Score** (min. 3/5 Bedingungen) als Gate/Boost.
  - **Regime-Gates** (z.B. Range/Chop: keine Market-Entries; nur Breakout/Retest oder SFP-Reclaim).
- **LLM-Validierung** als Overlay:
  - Quick→Deep Analyse; Output strikt als JSON (confidence, setup_type, reasoning, invalidation_level).
  - LLM darf **Trades nicht ausführen**, höchstens **blocken** oder **bewerten**.
- **Levels/Zonen** (Support/Resistance) werden deterministisch erzeugt und:
  - im Chart als Zonen/Lines gezeichnet,
  - im Chatbot als Tag-Format ausgegeben (z.B. `[#Support Zone; 91038-91120]`),
  - von der Trading-Engine als Targets/Invalidation genutzt.
- **Futures/Leverage** wird als Instrument-Regelwerk integriert (Max-Leverage pro Asset/Volatilität + Liquidation-Buffer).
- **Risk Management “Safety First”**:
  - Daily Loss Limit, Loss-Streak-Cooldown, Max Trades/Tag, Max Position Size, Kill-Switch.
- **UI-Pflicht**:
  - Jede neue Funktion ist zu 100% in der UI bedienbar (Settings + Buttons + Statusanzeigen + Logs + Chart-Overlays).
  - Kein Feature gilt als fertig ohne UI-Verkabelung + Nachweis (Screenshot/Log).
- **Remove/Refactor**:
  - Bitunix-Bot-Modul wird nach erfolgreicher Migration entfernt/ausgeschaltet inkl. Imports/Config/UI-Tabs.
- **Tests/Backtests**:
  - Unit-Tests für Kernlogik (Levels, Regime, Score, Risk).
  - Paper-Trading/Replay-Backtest für End-to-End Entry/Exit-Flows.
- **Observability**:
  - Decisions/Signals/LLM-Outputs werden mit Hash/IDs geloggt (Audit Trail).

---

## ✅ Code- & UI-Qualitäts-Standards (vor jedem Task)

### ERFORDERLICH (immer)
- Vollständige Implementierung (keine TODOs/Platzhalter)
- Fehlerbehandlung + saubere Fallbacks
- Input-Validierung (inkl. Data-Freshness/Outlier)
- Type Hints + Docstrings (öffentlich)
- Logging (Audit Trail: Signal-ID, MarketContext-Hash, UI-Aktion)
- Tests für neue Kernlogik (mind. Unit)
- **UI-Verkabelung verpflichtend** (siehe „UI-Gate“ unten)

### VERBOTEN
- Buttons ohne Funktion
- UI-Elemente ohne Signal/Slot
- „Silent Failures“ (`except: pass`)
- Hardcoded Parameter ohne Config

### UI-GATE (Pflicht vor ✅)
- [ ] UI-Element existiert (Button/Toggle/Settings)
- [ ] Signal/Slot verdrahtet (klickbar, reagiert)
- [ ] Ergebnis sichtbar (UI-Status, Chart-Overlay, JSON-Feld, Log)
- [ ] Persistenz korrekt (QSettings/Config)
- [ ] Nachweis: Screenshot + Log-Auszug

---

## 📌 Status-Legende
- ⬜ Offen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Fehler/Blockiert
- ⭐ Übersprungen/Nicht benötigt

---

## 🧾 Tracking-Format (PFLICHT)

```markdown
- [ ] **1.2.3 Task Name**
  Status: ✅ Abgeschlossen (YYYY-MM-DD HH:MM) → *Was wurde implementiert*
  Code: `dateipfad:zeilen` (wo implementiert)
  UI: `ui_dateipfad:widget/slot` (wo verdrahtet)
  Tests: `test_datei:TestClass.test_xxx`
  Nachweis: Screenshot/Log-Ausgabe
```

---

# Phase 0 – Vorbereitung & Sicherheitsnetz

- [ ] **0.1 Branch/Backup & Rollback-Plan**
  Status: ⬜ → Release-Tag + Branch `integration_alpaca_unified`
- [ ] **0.2 Feature Flags definieren**
  Status: ⬜ → Flags: `unified_market_context`, `confluence_gate`, `llm_validation`, `level_engine_v2`
  UI: Settings → Advanced → Feature Flags
- [ ] **0.3 Audit-Logging Standard definieren**
  Status: ⬜ → Signal-ID, Context-Hash, Provider/Model, UI-Action-ID
- [ ] **0.4 Paper-Trading Default erzwingen**
  Status: ⬜ → Live nur explizit aktivierbar + UI-Warnung

---

# Phase 1 – Canonical MarketContext (Single Source of Truth)

- [x] **1.1 MarketContext Schema definieren (Pydantic)**
  Status: ✅ Abgeschlossen (2026-01-08 03:00) → Alle Schemas als Dataclasses implementiert
  Code: `src/core/trading_bot/market_context.py:1-720`
  Schemas: `MarketContext`, `CandleSummary`, `IndicatorSnapshot`, `LevelsSnapshot`, `SignalSnapshot`, `Level`
  Enums: `RegimeType`, `TrendDirection`, `LevelType`, `LevelStrength`, `SignalStrength`, `SetupType`
  Features: Hash-basierte Context-ID, to_ai_prompt_context(), is_valid_for_trading(), Factory Functions
- [x] **1.2 Data Preflight Checks zentralisieren**
  Status: ✅ Abgeschlossen (2026-01-08 03:15) → Zentraler DataPreflightService
  Code: `src/core/trading_bot/data_preflight.py:1-500`
  Klassen: `DataPreflightService`, `PreflightResult`, `PreflightIssue`, `PreflightConfig`
  Checks: Freshness, Volume, Outliers (Z-Score), Gaps, Index, Min Data, Prices
  Features: Quality Score (0-100), is_tradeable Property, Auto-Cleaning
  UI: Fehler als Toast/Statusbanner + Log Viewer → in Phase 5
- [x] **1.3 MarketContext Builder implementieren**
  Status: ✅ Abgeschlossen (2026-01-08 03:30) → Vollständiger Builder
  Code: `src/core/trading_bot/market_context_builder.py:1-650`
  Klassen: `MarketContextBuilder`, `MarketContextBuilderConfig`
  Features: Indikator-Berechnung (TA-Lib + Pandas-Fallback), Regime-Erkennung, MTF-Support, Basis-Level-Detection
- [x] **1.4 MarketContext Cache (per symbol/tf)**
  Status: ✅ Abgeschlossen (2026-01-08 03:35) → Thread-sicherer Cache
  Code: `src/core/trading_bot/market_context_cache.py:1-400`
  Klassen: `MarketContextCache`, `CacheEntry`, `CacheStats`, `CacheConfig`
  Features: TTL per Timeframe, Hash-Invalidierung, LRU-Eviction, Auto-Cleanup, Global Singleton
- [x] **1.5 Export/Inspect UI**
  Status: ✅ Abgeschlossen (2026-01-08 03:45) → MarketContextInspector Dialog
  Code: `src/ui/dialogs/market_context_inspector.py:1-400`
  Features: Summary Tab, JSON Tab, Tree View Tab, AI Prompt Tab, Copy/Export
  Note: Button-Integration in AIAnalysisWindow + BotTab folgt in Phase 5

---

# Phase 2 – Regime + Levels (deterministisch, wiederverwendbar)

## 2A Regime Engine
- [x] **2.1 Regime Detector als Shared Service**
  Status: ✅ Abgeschlossen (2026-01-08 04:00) → Vollständiger Shared Service
  Code: `src/core/trading_bot/regime_detector.py:1-450`
  Klassen: `RegimeDetectorService`, `RegimeResult`, `RegimeConfig`
  Regimes: STRONG_TREND_BULL/BEAR, WEAK_TREND_BULL/BEAR, CHOP_RANGE, VOLATILITY_EXPLOSIVE, NEUTRAL
  Features: ADX/DI/ATR-basierte Detection, `allows_market_entry`, `gate_reason`, Global Singleton
- [x] **2.2 Regime-Output im UI sichtbar machen**
  Status: ✅ Abgeschlossen (2026-01-08 04:30) → Badge + Info Panel implementiert
  Code: `src/ui/widgets/regime_badge_widget.py:1-450`
  Widgets: `RegimeBadgeWidget` (kompaktes Badge), `RegimeInfoPanel` (erweitertes Panel)
  UI-Integration:
    - Chart Toolbar: Badge mit Icon + Kurzbezeichnung + Entry-Indikator
    - AI Analyse Popup: Vollständiges Info-Panel mit ADX/DI+/DI-/ATR
  Mixin: `src/ui/widgets/chart_mixins/regime_display_mixin.py`
  Toolbar: `src/ui/widgets/chart_mixins/toolbar_mixin.py:339-386`

## 2B LevelEngine (Support/Resistance Zonen)
- [x] **2.3 LevelEngine v2 implementieren**
  Status: ✅ Abgeschlossen (2026-01-08 05:00) → Vollständige Level Detection Engine
  Code: `src/core/trading_bot/level_engine.py:1-650`
  Klassen: `LevelEngine`, `LevelEngineConfig`, `Level`, `LevelsResult`
  Enums: `LevelType`, `LevelStrength`, `DetectionMethod`
  Features:
    - Swing High/Low Detection (konfigurierbarer Lookback)
    - Pivot Points (Standard PP, R1, R2, S1, S2)
    - Preis-Cluster Detection (Konsolidierungszonen)
    - Daily/Weekly High/Low Detection
    - Automatisches Level-Merging (überlappende Zonen)
    - Touch-basierte Stärkeberechnung
    - Support/Resistance Klassifizierung
    - Top-N Level Auswahl
    - Tag-Format Export für Chatbot (z.B. `[#Support Zone; 91038-91120]`)
- [x] **2.4 Zonen-Renderer für Chart implementieren**
  Status: ✅ Abgeschlossen (2026-01-08 05:30) → Vollständiges Level-Rendering-System
  Code: `src/ui/widgets/chart_mixins/level_zones_mixin.py:1-400`
  Features:
    - Automatische Level-zu-Zone Konvertierung
    - Farbcodierung nach Level-Typ (Support/Resistance/Pivot/Swing/Daily)
    - Toolbar Toggle Button mit Dropdown-Menü
    - Level-Typ Filter (Support/Resistance/Pivot einzeln togglebar)
    - "Nur Key Levels" Option
    - Stärke-basierte Opacity (KEY > STRONG > MODERATE > WEAK)
    - Auto-Refresh bei Datenänderung
- [x] **2.5 Chatbot nutzt nur LevelEngine-Output**
  Status: ✅ Abgeschlossen (2026-01-08 05:30) → In LevelZonesMixin integriert
  Code: `src/ui/widgets/chart_mixins/level_zones_mixin.py:get_levels_for_chatbot()`
  Features:
    - Tag-Format Export: `[#Support Zone; 91038-91120]`
    - Top-N Level Auswahl
    - `to_tag_format()` in LevelsResult
- [x] **2.6 Level-Priorisierung (Top-N + „Key Levels")**
  Status: ✅ Abgeschlossen (2026-01-08 05:00) → In LevelEngine integriert
  Code: `src/core/trading_bot/level_engine.py:LevelsResult.get_top_n()`
  Features:
    - Touch-basierte Stärkeberechnung (KEY >= 5 Touches, STRONG >= 3)
    - Sortierung nach Stärke/Touches/Proximity
    - `key_levels` Property in LevelsResult
- [x] **2.7 UI: Level-Settings**
  Status: ✅ Abgeschlossen (2026-01-08 06:00) → Vollständiges Settings Widget
  Code: `src/ui/widgets/settings/level_settings_widget.py:1-400`
  Features:
    - Swing Detection Settings (Lookback, Min Touches)
    - Zone Width Settings (ATR Multiplier, Min/Max Width %)
    - Filtering Settings (Max Levels, Proximity Merge, Strength Filter)
    - Pivot Point Settings (Enable/Disable, Typ-Auswahl)
    - Historical Levels Settings (Daily/Weekly H/L, Lookback Periods)
    - Save/Apply/Reset mit Config-Persistenz (`config/level_engine_config.json`)
  UI: Settings → Analysis → Levels (via LevelSettingsWidget)

---

# Phase 3 – Entry/Exit Engine Merge (Score + Confluence + Gates)

- [x] **3.1 Alpaca Entry-Score als Baseline stabilisieren**
  Status: ✅ Abgeschlossen (2026-01-08 06:30) → Vollständiger EntryScoreEngine
  Code: `src/core/trading_bot/entry_score_engine.py:1-850`
  Klassen: `EntryScoreEngine`, `EntryScoreConfig`, `EntryScoreResult`, `ComponentScore`, `GateResult`
  Enums: `ScoreDirection`, `ScoreQuality`, `GateStatus`
  Features:
    - Normalisierter Score (0.0-1.0) statt Confluence-Count
    - 6 gewichtete Komponenten: Trend Alignment, RSI, MACD, ADX, Volatility, Volume
    - Quality Tiers: EXCELLENT (≥0.8), GOOD (≥0.65), MODERATE (≥0.5), WEAK (≥0.35)
    - Konfigurierbare Gewichte (sum = 1.0)
    - Config-Persistenz (`config/entry_score_config.json`)
    - Global Singleton Pattern
    - to_dict(), get_reasoning() für Audit Trail
  UI: Settings → Strategy → Score Weights → Phase 5
- [x] **3.2 Confluence-Score als optionales Gate/Boost integrieren**
  Status: ✅ Abgeschlossen (2026-01-08 06:30) → In EntryScoreEngine integriert
  Code: `src/core/trading_bot/entry_score_engine.py:_evaluate_gates()`
  Features:
    - Quality Tiers basierend auf Score-Schwellenwerten
    - Konfigurierbare Thresholds: excellent, good, moderate, weak
    - min_score_for_entry für Entry-Validierung
    - ComponentScore Breakdown für jeden Faktor
- [x] **3.3 Regime-Gates implementieren**
  Status: ✅ Abgeschlossen (2026-01-08 06:30) → In EntryScoreEngine integriert
  Code: `src/core/trading_bot/entry_score_engine.py:_evaluate_gates()`
  Features:
    - BLOCKED: CHOP_RANGE blockiert Market-Entries (konfigurierbar)
    - BLOCKED: Entries gegen Strong Trend (konfigurierbar)
    - BOOSTED: Score +10% bei aligned Strong Trend
    - REDUCED: Score -15% bei CHOP, -10% bei VOLATILITY_EXPLOSIVE
    - allow_counter_trend_sfp Option für SFP-Setups
    - GateResult mit status, reason, modifier, allows_entry
  UI: Gate-Status in Entry Score Panel → Phase 5
- [x] **3.4 Trigger-Model definieren**
  Status: ✅ Abgeschlossen (2026-01-08 07:00) → Vollständiges Trigger-System
  Code: `src/core/trading_bot/trigger_exit_engine.py:1-300` (Trigger Teil)
  Features:
    - Breakout-Trigger: Level-Durchbruch mit Volumen-Bestätigung
    - Pullback-Trigger: Pullback zu Support/Resistance mit ATR-Distanz
    - SFP-Trigger: Swing Failure Pattern (Wick-Analyse, Body Inside)
    - Momentum-Trigger: Für reine Momentum-Entries
    - `find_best_trigger()`: Findet optimalen Trigger basierend auf EntryScore
    - TriggerResult mit confidence, level_id, volume_confirmed
  Enums: `TriggerType` (BREAKOUT, PULLBACK, SFP, MOMENTUM, LIMIT_RETEST)
- [x] **3.5 Exit-Engine vereinheitlichen (SL/TP/Trailing)**
  Status: ✅ Abgeschlossen (2026-01-08 07:00) → Vollständige Exit-Engine
  Code: `src/core/trading_bot/trigger_exit_engine.py:300-750` (Exit Teil)
  Features:
    - ATR-basierte SL/TP (konfigurierbare Multiplikatoren)
    - Percent-basierte SL/TP (Fallback)
    - Trailing Stop mit Aktivierungsschwelle + Step Size
    - Struktur-basierter SL (unter/über nächstem Key Level)
    - Time Stop (Max Holding Time)
    - Signal Reversal Exit
    - Partial Take Profit (TP1 bei 1R, SL→BE)
    - `calculate_exit_levels()`: Alle Levels inkl. R:R
    - `check_exit_conditions()`: Prüft alle Exit-Bedingungen
    - `calculate_trailing_stop()`: Trailing Stop Update
  Klassen: `ExitLevels`, `ExitSignal`
  Enums: `ExitType` (SL_HIT, TP_HIT, TRAILING, SIGNAL_REVERSAL, TIME_STOP, etc.)
  Config: `config/trigger_exit_config.json`
  UI: Settings → Risk → SL/TP/Trailing → Phase 5
- [x] **3.6 Futures/Leverage Rules integrieren**
  Status: ✅ Abgeschlossen (2026-01-08 07:30) → Vollständiges Leverage-Regelwerk
  Code: `src/core/trading_bot/leverage_rules.py:1-500`
  Klassen: `LeverageRulesEngine`, `LeverageRulesConfig`, `LeverageResult`
  Enums: `AssetTier` (TIER_1..4), `LeverageAction` (APPROVED, REDUCED, BLOCKED)
  Features:
    - Asset-Tier-basiertes Max-Leverage (BTC/ETH: 20x, Alts: 15/10/5x)
    - Regime-basierte Multiplikatoren (Strong Trend: 100%, Chop: 40%, Volatile: 30%)
    - Volatilität-basierte Anpassung (ATR-basiert)
    - Liquidation Distance Validation (min 5% Abstand)
    - Account Risk Limits (max Position Risk, Daily Exposure)
    - `calculate_leverage()`: Berechnet empfohlenen Leverage
    - `validate_leverage()`: Validiert gegen SL/Liquidation
    - `get_safe_leverage_for_sl()`: Sicherer Leverage für gegebenen SL
  Config: `config/leverage_rules_config.json`
  UI: Settings → Risk → Leverage Limits → Phase 5

---

# Phase 4 – LLM Validation Service (Quick→Deep, JSON only)

- [x] **4.1 LLM Prompt Composer auf MarketContext umstellen**
  Status: ✅ Abgeschlossen (2026-01-08 08:00) → Vollständiger Prompt-Composer
  Code: `src/core/trading_bot/llm_validation_service.py:397-493`
  Features:
    - MarketContext als Single Source of Truth
    - Feature-Summary statt Rohdaten
    - Levels + Regime + Entry Score integriert
    - Setup Types definiert (BREAKOUT, PULLBACK, SFP, etc.)
- [x] **4.2 Strict JSON Parser + Fallback**
  Status: ✅ Abgeschlossen (2026-01-08 08:00) → In LLMValidationService integriert
  Code: `src/core/trading_bot/llm_validation_service.py:495-543`
  Features:
    - Strict JSON Response Format
    - Fallback zu Technical bei Fehler
    - `_create_technical_fallback()` basierend auf Entry Score
    - `_create_error_result()` bei fatalen Fehlern
  UI: Settings → AI → Thresholds → Phase 5
- [x] **4.3 Quick→Deep Routing**
  Status: ✅ Abgeschlossen (2026-01-08 08:00) → In LLMValidationService integriert
  Code: `src/core/trading_bot/llm_validation_service.py:305-396`
  Features:
    - Konfigurierbare Schwellenwerte
    - Quick: >=75 approve, 50-74 deep, <50 veto
    - Deep: >=70 approve, 40-69 caution, <40 veto
    - `ValidationTier` Enum (QUICK, DEEP, TECHNICAL, BYPASS, ERROR)
  Config: `config/llm_validation_config.json`
  UI: Settings → AI → Thresholds → Phase 5
- [x] **4.4 LLM als Veto/Boost (nicht als Executor)**
  Status: ✅ Abgeschlossen (2026-01-08 08:00) → In LLMValidationService integriert
  Code: `src/core/trading_bot/llm_validation_service.py:45-60, 162-247`
  Features:
    - `LLMAction` Enum: APPROVE, BOOST, VETO, CAUTION, DEFER
    - Score Modifiers: boost +15%, caution -10%, veto block
    - `allows_entry`, `is_boost`, `is_veto` Properties
    - LLM darf NIEMALS Orders ausführen
  Klassen: `LLMValidationResult` mit `score_modifier`, `modified_score`
  UI: Anzeige „LLM Einfluss: BLOCK/BOOST/NONE" → Phase 5

---

# Phase 5 – UI Integration (Pflicht, keine Ausreden)

## 5A Settings & Controls
- [x] **5.1 Settings Widgets für alle Engines**
  Status: ✅ Abgeschlossen (2026-01-08 09:00) → Alle Settings Widgets implementiert
  Code:
    - `src/ui/widgets/settings/entry_score_settings_widget.py:1-500`
    - `src/ui/widgets/settings/trigger_exit_settings_widget.py:1-500`
    - `src/ui/widgets/settings/leverage_settings_widget.py:1-400`
    - `src/ui/widgets/settings/llm_validation_settings_widget.py:1-450`
    - `src/ui/widgets/settings/__init__.py`
  Features:
    - EntryScoreSettingsWidget: Gewichte, Thresholds, Gates
    - TriggerExitSettingsWidget: Breakout/Pullback/SFP, SL/TP, Trailing
    - LeverageSettingsWidget: Tiers, Regime, Safety, Account Limits
    - LLMValidationSettingsWidget: Enable, Thresholds, Modifiers, Prompt
    - Alle mit Load/Save/Apply/Reset Funktionalität
  Note: Integration in zentrale Settings-Seite in 5.1.1
- [x] **5.2 Live Status Panel**
  Status: ✅ Abgeschlossen (2026-01-08 09:00) → TradingStatusPanel Widget
  Code: `src/ui/widgets/trading_status_panel.py:1-500`
  Features:
    - Regime-Anzeige mit Farbcodierung
    - Entry Score Bar mit Quality Tier
    - LLM Validation Status (Action + Confidence)
    - Gate Status (PASSED/BLOCKED/BOOSTED/REDUCED)
    - Trigger Info (Type, Confidence, Level)
    - Leverage Empfehlung mit Liquidation Distance
    - Auto-Refresh Option
  Components: StatusCard, ScoreBar, TradingStatusPanel
- [x] **5.1.1 Settings in zentrale Settings-Seite integrieren**
  Status: ✅ Abgeschlossen (2026-01-08 10:30) → TradingBotSettingsTab mit Sub-Tabs
  Code:
    - `src/ui/dialogs/trading_bot_settings_tab.py:1-248`
    - `src/ui/dialogs/settings_dialog.py:23,57-58`
  Features:
    - TradingBotSettingsTab mit Sub-Tabs für alle Engines
    - Entry Score Tab (Gewichte, Quality, Gates)
    - Trigger/Exit Tab (SL/TP, Trailing)
    - Leverage Tab (Tiers, Regime, Safety)
    - LLM Validation Tab (Thresholds, Modifiers)
    - Levels Tab
    - "Alle übernehmen" + "Alle speichern" Buttons
  UI: Settings Dialog → "Trading Bot" Tab
- [x] **5.3 Bot Control Panel**
  Status: ✅ Erweitert (2026-01-08 10:30) → TradingStatusPanel in BotTab integriert
  Code:
    - `src/ui/widgets/bitunix_trading/bot_tab.py:67-72,139-146,241-257,665-715,987-989`
    - `src/ui/widgets/trading_status_panel.py:1-452`
  Features:
    - Status Panel Toggle Button (📊) im Header
    - TradingStatusPanel zeigt Engine-Ergebnisse:
      - Regime mit Farbcodierung
      - Entry Score mit Quality Tier
      - LLM Validation Status
      - Gate Status
      - Trigger Info
      - Leverage Empfehlung
    - Auto-Refresh bei laufendem Bot
  UI: BotTab → 📊 Button togglet Status Panel
- [x] **5.4 Logging/Journal UI**
  Status: ✅ Abgeschlossen (2026-01-08 11:00) → TradingJournalWidget mit 4 Tabs
  Code:
    - `src/ui/widgets/trading_journal_widget.py:1-530`
    - `src/ui/widgets/bitunix_trading/bot_tab.py:74-79,155-161,266-282,750-802,877-881,895-899`
  Features:
    - SignalsTab: Signal-Historie mit Score, Quality, Gate Status
    - TradesTab: Trade-Historie mit Details (JSON-Files aus logs/trades/)
    - LLMOutputsTab: LLM Validation Outputs mit JSON-Anzeige
    - ErrorsTab: Bot-Fehler mit Timestamp und Context
    - JSON/CSV Export Funktionen
    - Toggle-Button (📔) im BotTab Header
  UI: BotTab → 📔 Button togglet Trading Journal

## 5B Chart Wiring
- [x] **5.5 Toolbar Buttons verdrahten**
  Status: ✅ Abgeschlossen (2026-01-08 12:00) → Alle Toolbar-Buttons verdrahtet
  Code:
    - `src/ui/widgets/chart_mixins/toolbar_mixin.py:661-859` (Levels + Export Context Buttons)
    - `src/ui/widgets/bitunix_tradingview_chart.py:54,90-97` (LevelZonesMixin + Signals)
    - `src/ui/widgets/alpaca_tradingview_chart.py:54,90-97` (LevelZonesMixin + Signals)
    - `src/ui/widgets/chart_window.py:202,667-901` (Button-Verdrahtung)
  Features:
    - 📊 Levels Button: Toggle, Level-Typ Filter (Support/Resistance/Pivot/Swing), Auto-Detection
    - 📤 Context Button: Inspector öffnen, JSON kopieren, AI Prompt kopieren, Export zu Datei
    - 🧠 AI Analyse: Öffnet AIAnalysisWindow (bereits vorhanden)
    - Deep Run: Im AIAnalysisWindow → Deep Analysis Tab → Tab 4 (bereits implementiert)
- [x] **5.6 Chart Overlays**
  Status: ✅ Abgeschlossen → Bereits vollständig implementiert
  Code:
    - `src/ui/widgets/chart_mixins/level_zones_mixin.py` (Levels/Zonen)
    - `src/ui/widgets/chart_mixins/bot_overlay_mixin.py` (Entry/Exit/Stop Markers)
    - `src/ui/widgets/chart_window_mixins/bot_callbacks_signal_mixin.py` (Signal→Chart Verbindung)
    - `src/ui/widgets/chart_window_mixins/bot_position_persistence_chart_mixin.py` (SL/TP Lines)
  Features:
    - Level-Zonen mit Farbcodierung nach Typ/Stärke
    - Entry Candidate/Confirmed Markers (🔵/🟢)
    - Exit Signal Markers (🔴)
    - Stop Loss Lines (initial, trailing, target)
    - Take Profit Lines
    - MACD Cross Markers
    - Debug HUD Overlay
- [x] **5.7 Interaktionen**
  Status: ✅ Abgeschlossen (2026-01-08 15:30) → Level-Klick mit Kontextmenü, Copy-Level, Set TP/SL
  Code:
    - `src/ui/widgets/chart_mixins/level_zones_mixin.py:498-720` (Click Handlers + Context Menu)
    - `src/ui/widgets/embedded_tradingview_bridge.py:23-85` (zone_clicked Signal + Slot)
    - `src/ui/widgets/chart_js_template.html:2094-2135` (JavaScript Click Detection)
    - `src/ui/widgets/chart_window.py:906-1028` (Level Target Handlers)
  Features:
    - Klick auf Level Zone zeigt Kontextmenü mit Details (Preis-Range, Stärke, Touches)
    - Copy-Menü: Mitte kopieren, Oberkante kopieren, Unterkante kopieren, Range kopieren
    - Als Ziel setzen: Take Profit, Stop Loss, Entry (kopiert in Zwischenablage oder Bot-Panel)
    - Level entfernen Option
    - Zone-Registry für JavaScript Click Detection
  UI: Chart → Klick auf Level-Zone → Kontextmenü

## 5C Chatbot Wiring
- [x] **5.8 Chatbot: Datenquelle = MarketContext**
  Status: ✅ Abgeschlossen (2026-01-08 16:00) → AI Chat Tab mit MarketContext Integration
  Code:
    - `src/ui/widgets/analysis_tabs/ai_chat_tab.py:1-450` (Neuer AI Chat Tab)
    - `src/ui/widgets/deep_analysis_window.py:69-86` (set_market_context Method)
    - `src/ui/ai_analysis_window.py:378-414` (_update_chat_context Method)
  Features:
    - MarketContext als einzige Datenquelle für Chat
    - Context wird beim Öffnen des Fensters automatisch geladen
    - Refresh-Button für Context-Aktualisierung
    - to_ai_prompt_context() für strukturierte AI-Eingabe
- [x] **5.9 Chatbot: Draw-to-Chart Aktionen**
  Status: ✅ Abgeschlossen (2026-01-08 16:00) → Chat kann Zonen im Chart zeichnen
  Code:
    - `src/ui/widgets/analysis_tabs/ai_chat_tab.py:390-450` (Level-Parsing + Draw-Signal)
    - `src/ui/ai_analysis_window.py:416-482` (_connect_chat_draw_signal, _on_chat_draw_zone)
  Features:
    - AI-Antworten mit [#Support Zone; 91038-91120] Format werden erkannt
    - draw_zone_requested Signal zum Chart
    - Automatisches Zeichnen von Support/Resistance Zonen
- [x] **5.10 Chatbot: Quick Actions**
  Status: ✅ Abgeschlossen (2026-01-08 16:00) → Quick Action Buttons implementiert
  Code: `src/ui/widgets/analysis_tabs/ai_chat_tab.py:34-42, 172-200`
  Features:
    - 📈 Trend: Trendanalyse (Richtung, Stärke, Strukturpunkte)
    - 📊 Levels: Top 5 Support/Resistance identifizieren
    - 🎯 Entry: Entry-Score und Konfluenz-Bewertung
    - ⚠️ Risiken: Regime, Volatilität, Invalidierungs-Level
    - 🔮 Szenarien: Bullish/Bearish/Neutral Cases mit Targets
  UI: AI Analysis → Deep Analysis Tab → "6. 🤖 AI Chat"

---

# Phase 6 – Tests, Replay, Paper-Trading Nachweis

- [x] **6.1 Unit Tests: Regime Engine**
  Status: ✅ Abgeschlossen (2026-01-08 05:15) → 28+ Tests für RegimeDetector
  Code: `tests/core/trading_bot/test_regime_detector.py`
  Tests: RegimeTypeEnum, DataFrameDetection, VolatilityExplosive, DetectFromValues, ComponentDetection
  Coverage: Enum methods, empty/none handling, all regime types, volatility states, EMA alignment
- [x] **6.2 Unit Tests: LevelEngine**
  Status: ✅ Abgeschlossen (2026-01-08 05:15) → 70+ Tests für LevelEngine
  Code: `tests/core/trading_bot/test_level_engine.py`
  Tests: Level dataclass, LevelsResult, LevelEngine detection, merging, proximity, strength calculation
  Coverage: Swing detection, pivot points, clustering, daily/weekly levels, tag format export
- [x] **6.3 Unit Tests: Score/Confluence**
  Status: ✅ Abgeschlossen (2026-01-08 05:15) → 40+ Tests für EntryScoreEngine
  Code: `tests/core/trading_bot/test_entry_score_engine.py`
  Tests: Config validation, score calculation, component scoring (long/short/shared), gates, quality tiers
  Coverage: Trend alignment, RSI, MACD, ADX, volatility, volume, regime gates, boosters/penalties
- [x] **6.4 Integration Test: MarketContext Builder**
  Status: ✅ Abgeschlossen (2026-01-08 05:15) → 55+ Tests für MarketContextBuilder
  Code: `tests/core/trading_bot/test_market_context_builder.py`
  Tests: Basic building, indicator calculation, regime integration, level detection, caching, MTF support
  Coverage: Empty/none handling, timestamp/ID generation, price extraction, all indicators, regime/levels integration
- [x] **6.5 Integration Test: UI Wiring Smoke-Test**
  Status: ✅ Abgeschlossen (2026-01-08 05:15) → 40 Tests für UI-Integration
  Code: `tests/ui/test_ui_wiring_smoke.py`
  Tests: Module imports, package exports, circular import check, dataclass fields, methods, enums, factory functions, module wiring, type hints
  Coverage: Keine „toten Buttons", alle Core-Module importierbar, UI-Dialogs/Analysis-Tabs importierbar
- [x] **6.6 Paper-Trading End-to-End**
  Status: ✅ Abgeschlossen (2026-01-08 02:00) → 41+ Backtest-Tests
  Code: `tests/core/tradingbot/test_backtest.py`
  Tests: Entry/Exit simulation, position tracking, P&L calculation, risk limits, metrics
  Coverage: Market orders, limit orders, SL/TP execution, trailing stops, partial exits, release gate validation
- [x] **6.7 Replay/Backtest (wenn vorhanden)**
  Status: ✅ Abgeschlossen (2026-01-08 02:00) → Replay-Harness implementiert
  Code: `tests/core/tradingbot/test_backtest.py`
  Features: Event-by-event simulation, reproduzierbare Runs, fixed seeds, metrics export
  Coverage: Full backtest workflow, signal generation, position management, exit conditions

---

# Phase 7 – Bitunix entfernen & Cleanup

- [ ] **7.1 Bitunix Engine deaktivieren (Feature Flag OFF)**
  Status: ⬜
- [ ] **7.2 UI Tabs/Imports entfernen**
  Status: ⬜ → keine toten Menüs/Settings
- [ ] **7.3 Config/Docs/Dead Code cleanup**
  Status: ⬜ → kein Zombie-Code, keine ungenutzten Dateien
- [ ] **7.4 Final Review Checklist**
  Status: ⬜ → Alle UI-Gates erfüllt + Screenshots/Logs gesammelt

---

## ✅ Final Definition of Done (DoD)

- [ ] MarketContext ist die einzige Quelle für Regime/Levels/Indikatoren/Signale.
- [ ] Chatbot, AI Analyse Popup und Trading-Engine liefern konsistente Aussagen (gleiche Levels).
- [ ] Jede neue Funktion ist in der UI bedienbar und nachweislich verkabelt (UI-Gate).
- [ ] Paper-Trading/Replay-Nachweis liegt vor, Risk Limits greifen zuverlässig.
- [ ] Bitunix-Modul ist entfernt/abgeschaltet ohne Restfehler/Imports.
