 Eine KI Hat mir diesen Plan umgesetzt:
  "\01_Projectplan\Strategien_Workflow_json\CHECKLISTE_RegimeBasedJSON_Implementation.md"
  Alle Projektplanungsdateien: "\01_Projectplan\Strategien_Workflow_json\"
  Die KI hat sehr viele funktionen in das Programm eingebunden aber leider ohne zu beachten das
  diese auch mit UI
  Hilfe zu den programmierten Funktionen: "\Help\index.html"
  Funktionen verbunden werden müssen, diese "Verdrahtung" zur UI fehlt im wesentlichen jetzt in:
  1. Chartfenster->Button 'Entry Analyzer' (öffnende UI)
  2. Im Fenster 'Trading Bot'->Tab Bot->Button 'Start Bot' (benötigt json Datei 'Marktanalyse'
  und je nach Trendrichtung ein angepasstes Indikatorenset/Strategy

  1a. Der Entry Analyzer soll das Backtesting übernehmen um im ersten schritt den geöffneten
  Chart zu analysieren und diesen in REgime aufteilen (visuelle Darstellung mit vertikalen Linien
  im Chart) Aufteilung in Bereiche wie trend_following, Seitwärtsmarkt usw.
  1b. Dann die geeigneten verfügbaren Indikatoren einzelnt simulieren und je nach regime (heisst
  das so?) die Ergebnisse in eine Tabelle schreiben inkl einer spalte mit den verwendeten
  Indikatorenparametern.
  1c. Der Indikator soll dann mit unterschiedlichen einstellungen z.b. RSI(14) -> RSI(12)usw
  getestet werden, mit möglichst vielen aber sinnvollen Parametern. Dafür muss ein scoring system
  entwickelt werden, da jeder Durchlauf einen score bekommen soll von 0 bis 100 für das
  jeweilige Regime.
  1d. Die besten pro Regime werden dann zu einem Regimeset zusammengefasst mit gewichtungen der
  einzelnen Indikatoren. Das Regimeset soll dann auch noch im backtest ausgeführt werden.

  Nun meine Aufgabe, gehe in den Plan Modus und recherchiere die von der KI erstellten
  Funktionen, erstelle dann eine Tabelle mit Funktionsname, Datei in der sie enthalten ist,
  Aufgabe(n) die die Funktion erledigt.

  Und dann noch einen Umsetzungsplan (Entscheidung ob ui vom 'Entry Analyzer' weiter verwendet
  werden kann oder sinnvoller einmal neu erstellen und ersetzen)

● Ich werde jetzt in den Plan-Modus gehen, um die implementierten Funktionen zu recherchieren und
  einen Umsetzungsplan für die UI-Verdrahtung zu erstellen.

● Entered plan mode
  Claude is now exploring and designing an implementation approach.

● Ich starte jetzt mit Phase 1 und erkunde die Codebase parallel mit mehreren Explore-Agenten, um die
  implementierten Funktionen und die bestehende UI-Struktur zu verstehen.

● 3 Explore agents finished (ctrl+o to expand)
   ├─ Explore implementation plan files · 17 tool uses · 103.2k tokens
   │  ⎿  Done
   ├─ Explore UI structure and components · 16 tool uses · 96.8k tokens
   │  ⎿  Done
   └─ Find backend functions implementation · 27 tool uses · 111.4k tokens
      ⎿  Done

● Ausgezeichnet! Ich habe jetzt umfassende Informationen über die Implementierung. Lassen Sie mich nun
   die Hilfe-Dokumentation lesen und dann einen detaillierten Plan erstellen.

● Read(Help/index.html)
  ⎿  Read 516 lines

● Jetzt lese ich einige kritische Dateien, um die Details zu verstehen, bevor ich den finalen Plan
  erstelle.

● Read(src/backtesting/engine.py)
  ⎿  Read 100 lines

● Read(src/core/tradingbot/regime_engine.py)
  ⎿  Read 100 lines

● Read(src/core/tradingbot/entry_scorer.py)
  ⎿  Read 80 lines

● Jetzt erstelle ich die Plan-Datei mit der vollständigen Analyse und dem Umsetzungsplan.

● Updated plan
  ⎿  Wrote 1007 lines to ../../../../../home/maik/.claude/plans/cryptic-munching-gem.md
      1 # UI-Verdrahtung für Regime-Based JSON Strategy System
      2 ## Zusammenfassung
      3 Eine andere KI hat ein umfassendes Regime-basiertes JSON-Strategy-System implementiert
        (siehe `01_Projectplan/Strategien_Workflow_json/CHECKLISTE_RegimeBasedJSON_Implementati
        on.md`). Die Backend-Funktionen sind vollständig implementiert, aber die **UI-Verdrahtu
        ng fehlt** für:
      4 1. **Entry Analyzer Button** → Regime-basiertes Backtesting mit visueller Chart-Darstel
        lung
      5 2. **Start Bot Button** → JSON-basierte Strategy-Auswahl basierend auf Marktanalyse
      6 ---
     … +997 lines (ctrl+o to expand)

● Perfekt! Ich habe einen umfassenden Plan erstellt. Lassen Sie mich diesen jetzt mit ExitPlanMode zur
   Genehmigung vorlegen.

──────────────────────────────────────────────────────────────────────────────────────────────────────
 Ready to code?

 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 UI-Verdrahtung für Regime-Based JSON Strategy System

 Zusammenfassung

 Eine andere KI hat ein umfassendes Regime-basiertes JSON-Strategy-System implementiert (siehe
 01_Projectplan/Strategien_Workflow_json/CHECKLISTE_RegimeBasedJSON_Implementation.md). Die
 Backend-Funktionen sind vollständig implementiert, aber die UI-Verdrahtung fehlt für:

 1. Entry Analyzer Button → Regime-basiertes Backtesting mit visueller Chart-Darstellung
 2. Start Bot Button → JSON-basierte Strategy-Auswahl basierend auf Marktanalyse

 ---
 1. FUNKTIONSÜBERSICHT (Backend)

 Tabelle: Implementierte Funktionen
 Funktionsname: Regime Detection
 Datei:
 Aufgabe(n):
 ────────────────────────────────────────
 Funktionsname: RegimeEngine.classify()
 Datei: src/core/tradingbot/regime_engine.py
 Aufgabe(n): Klassifiziert Marktregime (Trend/Range) und Volatilität basierend auf ADX, ATR,
 BB-Width,
    RSI
 ────────────────────────────────────────
 Funktionsname: RegimeEngine._classify_regime()
 Datei: src/core/tradingbot/regime_engine.py
 Aufgabe(n): Bestimmt Trendrichtung (UP/DOWN/RANGE) mit ADX und ±DI
 ────────────────────────────────────────
 Funktionsname: RegimeEngine._classify_volatility()
 Datei: src/core/tradingbot/regime_engine.py
 Aufgabe(n): Klassifiziert Volatilität (LOW/NORMAL/HIGH/EXTREME) mit ATR% und BB-Width
 ────────────────────────────────────────
 Funktionsname: RegimeEngine.detect_regime_change()
 Datei: src/core/tradingbot/regime_engine.py
 Aufgabe(n): Erkennt signifikante Regime-Wechsel für Position-Anpassungen
 ────────────────────────────────────────
 Funktionsname: RegimeDetector.detect_active_regimes()
 Datei: src/core/tradingbot/config/detector.py
 Aufgabe(n): Erkennt aktive Regimes aus JSON-Config mit Condition-Evaluation
 ────────────────────────────────────────
 Funktionsname: JSON Config System
 Datei:
 Aufgabe(n):
 ────────────────────────────────────────
 Funktionsname: ConfigLoader.load_config()
 Datei: src/core/tradingbot/config/loader.py
 Aufgabe(n): Lädt und validiert JSON-Configs (JSON Schema + Pydantic)
 ────────────────────────────────────────
 Funktionsname: ConfigLoader.validate_config_data()
 Datei: src/core/tradingbot/config/loader.py
 Aufgabe(n): Validiert Config-Struktur und Business-Logik
 ────────────────────────────────────────
 Funktionsname: ConfigLoader.list_configs()
 Datei: src/core/tradingbot/config/loader.py
 Aufgabe(n): Listet alle JSON-Configs in einem Verzeichnis
 ────────────────────────────────────────
 Funktionsname: TradingBotConfig (Pydantic Model)
 Datei: src/core/tradingbot/config/models.py
 Aufgabe(n): Typ-sichere Config-Modelle für Indicators, Regimes, Strategies, Strategy Sets, Routing
 ────────────────────────────────────────
 Funktionsname: Condition Evaluation
 Datei:
 Aufgabe(n):
 ────────────────────────────────────────
 Funktionsname: ConditionEvaluator.evaluate_condition()
 Datei: src/core/tradingbot/config/evaluator.py
 Aufgabe(n): Evaluiert Single Conditions (gt, lt, eq, between)
 ────────────────────────────────────────
 Funktionsname: ConditionEvaluator.evaluate_group()
 Datei: src/core/tradingbot/config/evaluator.py
 Aufgabe(n): Evaluiert AND/OR Logic Groups
 ────────────────────────────────────────
 Funktionsname: ConditionEvaluator._resolve_operand()
 Datei: src/core/tradingbot/config/evaluator.py
 Aufgabe(n): Löst Indicator-Referenzen oder Konstanten auf
 ────────────────────────────────────────
 Funktionsname: Strategy Routing
 Datei:
 Aufgabe(n):
 ────────────────────────────────────────
 Funktionsname: StrategyRouter.route()
 Datei: src/core/tradingbot/config/router.py
 Aufgabe(n): Routet Regime-Kombinationen zu Strategy Sets (all_of/any_of/none_of)
 ────────────────────────────────────────
 Funktionsname: StrategySetExecutor.prepare_execution()
 Datei: src/core/tradingbot/config/executor.py
 Aufgabe(n): Wendet Parameter-Overrides an (Indicators + Strategies)
 ────────────────────────────────────────
 Funktionsname: StrategySetExecutor.restore_state()
 Datei: src/core/tradingbot/config/executor.py
 Aufgabe(n): Stellt Original-Parameter nach Execution wieder her
 ────────────────────────────────────────
 Funktionsname: Backtesting
 Datei:
 Aufgabe(n):
 ────────────────────────────────────────
 Funktionsname: BacktestEngine.run()
 Datei: src/backtesting/engine.py
 Aufgabe(n): Hauptloop: Multi-Timeframe-Daten laden, Indikatoren berechnen, Regimes evaluieren,
 Trades
    simulieren
 ────────────────────────────────────────
 Funktionsname: BacktestEngine._calculate_indicators()
 Datei: src/backtesting/engine.py
 Aufgabe(n): Berechnet Indikatoren mit pandas_ta für alle Timeframes
 ────────────────────────────────────────
 Funktionsname: BacktestEngine._evaluate_regimes()
 Datei: src/backtesting/engine.py
 Aufgabe(n): Bestimmt aktive Regimes pro Bar
 ────────────────────────────────────────
 Funktionsname: BacktestEngine._route_regimes()
 Datei: src/backtesting/engine.py
 Aufgabe(n): Routet Regimes zu Strategy Sets
 ────────────────────────────────────────
 Funktionsname: BacktestEngine._evaluate_conditions()
 Datei: src/backtesting/engine.py
 Aufgabe(n): Prüft Entry/Exit-Conditions
 ────────────────────────────────────────
 Funktionsname: BacktestEngine._calculate_stats()
 Datei: src/backtesting/engine.py
 Aufgabe(n): Berechnet Performance-Metriken (Net Profit, Win Rate, Profit Factor, Sharpe, Max DD)
 ────────────────────────────────────────
 Funktionsname: BacktestHarness.run_backtest()
 Datei: src/core/tradingbot/backtest_harness.py
 Aufgabe(n): Full Bot Backtest mit FeatureEngine, RegimeEngine, EntryScorer, ExitChecker
 ────────────────────────────────────────
 Funktionsname: Entry Scoring
 Datei:
 Aufgabe(n):
 ────────────────────────────────────────
 Funktionsname: EntryScorer.calculate_score()
 Datei: src/core/tradingbot/entry_scorer.py
 Aufgabe(n): Berechnet Entry-Score (0-1) mit Komponenten-Breakdown
 ────────────────────────────────────────
 Funktionsname: EntryScorer._score_generic()
 Datei: src/core/tradingbot/entry_scorer.py
 Aufgabe(n): Generisches Weighted Scoring mit DEFAULT_WEIGHTS
 ────────────────────────────────────────
 Funktionsname: EntryScorer._score_with_rules()
 Datei: src/core/tradingbot/entry_scorer.py
 Aufgabe(n): Strategy-spezifisches Rule-Evaluation
 ────────────────────────────────────────
 Funktionsname: EntryScorer._score_trend_alignment()
 Datei: src/core/tradingbot/entry_scorer.py
 Aufgabe(n): Score für SMA-Alignment (Fast > Slow für LONG)
 ────────────────────────────────────────
 Funktionsname: EntryScorer._score_rsi_momentum()
 Datei: src/core/tradingbot/entry_scorer.py
 Aufgabe(n): Score für RSI-Favorability (>50 für LONG, <50 für SHORT)
 ────────────────────────────────────────
 Funktionsname: EntryScorer._score_macd_momentum()
 Datei: src/core/tradingbot/entry_scorer.py
 Aufgabe(n): Score für MACD-Signal-Strength
 ────────────────────────────────────────
 Funktionsname: EntryScorer._score_trend_strength()
 Datei: src/core/tradingbot/entry_scorer.py
 Aufgabe(n): Score für ADX-basierte Trendstärke
 ────────────────────────────────────────
 Funktionsname: EntryScorer._score_mean_reversion()
 Datei: src/core/tradingbot/entry_scorer.py
 Aufgabe(n): Score für BB-Position (Reversion-Setup)
 ────────────────────────────────────────
 Funktionsname: EntryScorer._score_volume()
 Datei: src/core/tradingbot/entry_scorer.py
 Aufgabe(n): Score für Volume-Confirmation
 ────────────────────────────────────────
 Funktionsname: EntryScorer._score_regime_match()
 Datei: src/core/tradingbot/entry_scorer.py
 Aufgabe(n): Score für Regime-Kompatibilität
 ────────────────────────────────────────
 Funktionsname: Integration Bridge
 Datei:
 Aufgabe(n):
 ────────────────────────────────────────
 Funktionsname: IndicatorValueCalculator.calculate()
 Datei: src/core/tradingbot/config_integration_bridge.py
 Aufgabe(n): Mappt FeatureVector → indicator_values dict für Condition-Evaluation
 ────────────────────────────────────────
 Funktionsname: RegimeDetectorBridge.detect()
 Datei: src/core/tradingbot/config_integration_bridge.py
 Aufgabe(n): Bridged JSON-Regimes mit existierendem RegimeState
 ────────────────────────────────────────
 Funktionsname: StrategySetAdapter.adapt()
 Datei: src/core/tradingbot/config_integration_bridge.py
 Aufgabe(n): Konvertiert MatchedStrategySet → StrategyDefinition
 ────────────────────────────────────────
 Funktionsname: Migration & Code Generation
 Datei:
 Aufgabe(n):
 ────────────────────────────────────────
 Funktionsname: JSONConfigGenerator.generate_from_analysis()
 Datei: src/core/tradingbot/migration/json_generator.py
 Aufgabe(n): Konvertiert Hardcoded-Strategy zu JSON-Config
 ────────────────────────────────────────
 Funktionsname: JSONConfigGenerator.generate_from_multiple_analyses()
 Datei: src/core/tradingbot/migration/json_generator.py
 Aufgabe(n): Batch-Conversion von mehreren Strategies
 ────────────────────────────────────────
 Funktionsname: StrategyComparator.compare_json_to_hardcoded()
 Datei: src/core/tradingbot/migration/strategy_comparator.py
 Aufgabe(n): Verifiziert Äquivalenz zwischen JSON und Hardcoded (Similarity-Score)
 ────────────────────────────────────────
 Funktionsname: StrategyComparator.calculate_similarity()
 Datei: src/core/tradingbot/migration/strategy_comparator.py
 Aufgabe(n): Berechnet gewichteten Similarity-Score (Entry, Exit, Risk, Indicators)
 ────────────────────────────────────────
 Funktionsname: Strategy Evaluation
 Datei:
 Aufgabe(n):
 ────────────────────────────────────────
 Funktionsname: StrategyEvaluator.calculate_metrics()
 Datei: src/core/tradingbot/strategy_evaluator.py
 Aufgabe(n): Berechnet Performance-Metriken (Total Return, Sharpe, Max DD, Win Rate, Profit Factor)
 ────────────────────────────────────────
 Funktionsname: StrategyEvaluator.validate_robustness()
 Datei: src/core/tradingbot/strategy_evaluator.py
 Aufgabe(n): Prüft Robustness-Kriterien (Min Trades, Max DD, Sharpe Threshold)
 ────────────────────────────────────────
 Funktionsname: StrategyEvaluator.run_walk_forward()
 Datei: src/core/tradingbot/strategy_evaluator.py
 Aufgabe(n): Walk-Forward-Analyse für Out-of-Sample Validation
 ────────────────────────────────────────
 Funktionsname: StrategyEvaluator.compare_strategies()
 Datei: src/core/tradingbot/strategy_evaluator.py
 Aufgabe(n): Rankt Strategies nach Composite-Score
 ────────────────────────────────────────
 Funktionsname: Config Reloading
 Datei:
 Aufgabe(n):
 ────────────────────────────────────────
 Funktionsname: ConfigReloader.start_watching()
 Datei: src/core/tradingbot/config_reloader.py
 Aufgabe(n): Startet File-Watching mit watchdog (auto-reload bei Änderungen)
 ────────────────────────────────────────
 Funktionsname: ConfigReloader.reload_config()
 Datei: src/core/tradingbot/config_reloader.py
 Aufgabe(n): Manuelles Reload mit Validation und Event-Emission
 ────────────────────────────────────────
 Funktionsname: ConfigReloader.stop_watching()
 Datei: src/core/tradingbot/config_reloader.py
 Aufgabe(n): Stoppt File-Watching gracefully
 Total: 40+ Kern-Funktionen implementiert

 ---
 2. BESTEHENDE UI-STRUKTUR

 Entry Analyzer Popup

 Datei: src/ui/dialogs/entry_analyzer_popup.py
 Klasse: EntryAnalyzerPopup (Lines 182-958)

 Struktur:
 - Header: Regime-Display, Signal-Counts
 - Tab-Widget mit 5 Tabs:
   a. Backtest Setup (LINES 228-231): Load Strategy JSON, Date Range, Capital, Symbol, "Run Backtest"
  Button
   b. Visible Range Analysis (LINES 233-236): Current Entry Analysis
   c. Backtest Results (LINES 238-241): Performance Summary, Trade List
   d. AI Copilot (LINES 243-246): AI Entry Recommendations
   e. Validation (LINES 248-251): Walk-Forward Validation

 Footer Actions:
 - "🔄 Analyze Visible Range" Button
 - "📄 Generate Report" Button
 - "📍 Draw on Chart" Button
 - "🗑️ Clear Entries" Butto
 - Close Button

 WICHTIG: Die UI ist VOLLSTÄNDIG vorhanden mit Backtest-Tab, JSON-Loader, Ergebnis-Anzeige!

 Trading Bot Settings Tab

 Datei: src/ui/dialogs/trading_bot_settings_tab.py
 Klasse: TradingBotSettingsTab (Lines 34-280)

 Neue Elemente:
 - "⚙️ Settings Bot" Button (Lines 135-146): Öffnet Strategy Settings Dialog für JSON-basierte
 Strategy-Management
 - Sub-Tabs: Entry Score, Trigger/Exit, Leverage, LLM Validation, Levels

 Bot Control Buttons

 Datei: src/ui/widgets/chart_window_mixins/bot_ui_control_widgets.py

 Bot Control Group (Lines 49-86):
 - Status Label: "Status: STOPPED"
 - Start Bot Button: Green (#26a69a), Line 62-68
 - Stop Bot Button: Red (#ef5350), Line 70-77
 - Pause Button: Line 79-83

 Zusätzlicher Start Button im Trading Tab:
 Datei: src/ui/widgets/chart_window_mixins/bot_ui_signals_mixin.py (Lines 494-506)

 ---
 3. FEHLENDE UI-VERDRAHTUNG

 Problem 1: Entry Analyzer → Backtesting

 Ist-Zustand:
 - Entry Analyzer UI ist vollständig vorhanden (Backtest Setup Tab, JSON-Loader)
 - Backend-Funktionen sind vollständig implementiert (BacktestEngine, RegimeDetector, StrategyRouter)

 Fehlende Verdrahtung:
 1. "Run Backtest" Button ist nicht mit BacktestEngine.run() verbunden
 2. Regime-Visualisierung im Chart fehlt:
   - Vertikale Linien für Regime-Grenzen
   - Farbcodierung für verschiedene Regimes (Trend/Range/Volatility)
 3. Indicator-Scoring-Tabelle fehlt:
   - Einzelne Indikatoren mit verschiedenen Parametern testen
   - Score pro Regime berechnen (0-100)
   - Beste Indikatoren pro Regime identifizieren
 4. Regime-Set-Backtesting fehlt:
   - Beste Indikatoren pro Regime zusammenfassen
   - Gewichtungen der Indikatoren
   - Backtest des kompletten Regime-Sets

 Problem 2: Start Bot → JSON Strategy Selection

 Ist-Zustand:
 - Start Bot Buttons sind vorhanden (Bot Tab + Trading Tab)
 - BotController hat bereits _load_json_config() implementiert (Phase 4.1)

 Fehlende Verdrahtung:
 1. JSON-Config-Auswahl vor Bot-Start:
   - UI-Dialog zur Auswahl der JSON-Strategy-Datei
   - Vorschau der Config (Regimes, Strategies)
 2. Marktanalyse-Integration:
   - Aktuelles Regime vor Bot-Start analysieren
   - Passende Strategy aus JSON auswählen
   - Anzeige der gewählten Strategy mit Entry/Exit-Conditions
 3. Dynamic Strategy Switching:
   - Regime-Änderungen während Laufzeit erkennen
   - Automatische Strategy-Umschaltung
   - UI-Benachrichtigung bei Strategy-Wechsel

 ---
 4. UMSETZUNGSPLAN

 Phase 1: Entry Analyzer - Regime-basiertes Backtesting

 1.1 Backtest-Button Verdrahtung (KRITISCH)

 Ziel: "Run Backtest" Button mit BacktestEngine verbinden

 Schritte:
 1. Signal/Slot Connection:
   - In EntryAnalyzerPopup.__init__(): Connect run_backtest_btn.clicked → _on_run_backtest_clicked()
 2. Handler-Implementierung:
 def _on_run_backtest_clicked(self):
     # 1. Validate Inputs
     config_path = self.json_file_input.text()
     symbol = self.symbol_combo.currentText()
     start_date = self.start_date_edit.date().toPyDate()
     end_date = self.end_date_edit.date().toPyDate()
     capital = self.capital_spin.value()

     # 2. Load JSON Config
     config = ConfigLoader().load_config(config_path)

     # 3. Run Backtest in Background Thread
     self._run_backtest_async(config, symbol, start_date, end_date, capital)

 def _run_backtest_async(self, config, symbol, start_date, end_date, capital):
     # QThread or ThreadPoolExecutor
     self.backtest_thread = BacktestThread(config, symbol, start_date, end_date, capital)
     self.backtest_thread.finished.connect(self._on_backtest_finished)
     self.backtest_thread.progress.connect(self._on_backtest_progress)
     self.backtest_thread.start()

 def _on_backtest_finished(self, results):
     # Update Results Tab
     self._update_results_tab(results)
     # Draw Regime Boundaries on Chart
     self._draw_regime_boundaries(results['regime_changes'])
 3. BacktestThread erstellen:
 class BacktestThread(QThread):
     finished = pyqtSignal(dict)
     progress = pyqtSignal(int, str)

     def __init__(self, config, symbol, start_date, end_date, capital):
         super().__init__()
         self.config = config
         self.symbol = symbol
         self.start_date = start_date
         self.end_date = end_date
         self.capital = capital

     def run(self):
         engine = BacktestEngine()
         results = engine.run(
             self.config,
             self.symbol,
             self.start_date,
             self.end_date,
             self.capital
         )
         self.finished.emit(results)

 Dateien:
 - src/ui/dialogs/entry_analyzer_popup.py (modify)
 - src/ui/threads/backtest_thread.py (new)

 ---
 1.2 Regime-Visualisierung im Chart (KRITISCH)

 Ziel: Vertikale Linien für Regime-Grenzen zeichnen

 Schritte:
 1. Regime-Daten aus Backtest extrahieren:
 def _extract_regime_changes(self, backtest_results):
     regime_changes = []
     prev_regime = None
     for timestamp, regime in backtest_results['regime_history']:
         if regime != prev_regime:
             regime_changes.append({
                 'timestamp': timestamp,
                 'regime': regime,
                 'type': regime.regime,  # TREND_UP, TREND_DOWN, RANGE
                 'volatility': regime.volatility
             })
             prev_regime = regime
     return regime_changes
 2. Chart-Overlay für Regime-Grenzen:
 def _draw_regime_boundaries(self, regime_changes):
     # Get ChartWindow instance
     chart_window = self.parent  # or self.parent()

     # Clear existing regime lines
     chart_window.clear_regime_lines()

     # Draw vertical lines for each regime change
     for change in regime_changes:
         color = self._get_regime_color(change['type'])
         chart_window.add_vertical_line(
             timestamp=change['timestamp'],
             color=color,
             width=2,
             label=f"{change['type'].name} ({change['volatility'].name})"
         )

 def _get_regime_color(self, regime_type):
     colors = {
         RegimeType.TREND_UP: '#26a69a',      # Green
         RegimeType.TREND_DOWN: '#ef5350',    # Red
         RegimeType.RANGE: '#ffa726',         # Orange
     }
     return colors.get(regime_type, '#9e9e9e')
 3. Chart-Mixin erweitern:
   - In src/ui/widgets/chart_window_setup.py oder einem Mixin:
 def add_vertical_line(self, timestamp, color, width, label):
     # Convert timestamp to x-coordinate
     x_pos = self._timestamp_to_x(timestamp)

     # Draw vertical line
     line = pg.InfiniteLine(
         pos=x_pos,
         angle=90,
         pen=pg.mkPen(color=color, width=width),
         label=label,
         labelOpts={'position': 0.95}
     )
     self.chart_widget.addItem(line)
     self.regime_lines.append(line)

 def clear_regime_lines(self):
     for line in self.regime_lines:
         self.chart_widget.removeItem(line)
     self.regime_lines.clear()

 Dateien:
 - src/ui/dialogs/entry_analyzer_popup.py (modify)
 - src/ui/widgets/chart_window_mixins/regime_visualization_mixin.py (new)

 ---
 1.3 Indicator-Scoring-System (ERWEITERT)

 Ziel: Einzelne Indikatoren mit verschiedenen Parametern testen, Score pro Regime

 Schritte:
 1. Neuer Tab "Indicator Optimization":
 def _create_indicator_optimization_tab(self):
     tab = QWidget()
     layout = QVBoxLayout(tab)

     # Indicator Selection
     indicator_group = QGroupBox("Indicator Selection")
     indicator_layout = QVBoxLayout(indicator_group)

     self.indicator_checkboxes = {}
     for ind_type in ['RSI', 'MACD', 'ADX', 'BB', 'SMA', 'EMA']:
         cb = QCheckBox(ind_type)
         cb.setChecked(True)
         self.indicator_checkboxes[ind_type] = cb
         indicator_layout.addWidget(cb)

     # Parameter Ranges
     param_group = QGroupBox("Parameter Ranges")
     param_layout = QFormLayout(param_group)

     self.rsi_range = QSpinBoxRange(min=10, max=20, step=2)  # RSI(10), RSI(12), RSI(14), ...
     self.macd_fast_range = QSpinBoxRange(min=8, max=16, step=2)
     # ... weitere Parameter

     param_layout.addRow("RSI Period Range:", self.rsi_range)
     param_layout.addRow("MACD Fast Range:", self.macd_fast_range)

     # Run Optimization Button
     self.optimize_btn = QPushButton("🚀 Optimize Indicators")
     self.optimize_btn.clicked.connect(self._on_optimize_indicators_clicked)

     # Results Table
     self.optimization_results_table = QTableWidget()
     self.optimization_results_table.setColumnCount(6)
     self.optimization_results_table.setHorizontalHeaderLabels([
         "Indicator", "Parameters", "Regime", "Score (0-100)", "Win Rate", "Profit Factor"
     ])

     layout.addWidget(indicator_group)
     layout.addWidget(param_group)
     layout.addWidget(self.optimize_btn)
     layout.addWidget(self.optimization_results_table)

     return tab
 2. Indicator-Optimization-Engine:
 def _on_optimize_indicators_clicked(self):
     # 1. Get selected indicators
     selected_indicators = [
         ind_type for ind_type, cb in self.indicator_checkboxes.items()
         if cb.isChecked()
     ]

     # 2. Get parameter ranges
     param_ranges = {
         'RSI': range(self.rsi_range.min_value, self.rsi_range.max_value, self.rsi_range.step),
         'MACD_fast': range(self.macd_fast_range.min_value, self.macd_fast_range.max_value,
 self.macd_fast_range.step),
         # ...
     }

     # 3. Run optimization in background
     self.optimization_thread = IndicatorOptimizationThread(
         selected_indicators, param_ranges, self.symbol, self.start_date, self.end_date
     )
     self.optimization_thread.finished.connect(self._on_optimization_finished)
     self.optimization_thread.progress.connect(self._update_progress)
     self.optimization_thread.start()

 def _on_optimization_finished(self, results):
     # Update table with results
     self.optimization_results_table.setRowCount(0)

     for result in results:
         row = self.optimization_results_table.rowCount()
         self.optimization_results_table.insertRow(row)

         self.optimization_results_table.setItem(row, 0, QTableWidgetItem(result['indicator']))
         self.optimization_results_table.setItem(row, 1, QTableWidgetItem(str(result['params'])))
         self.optimization_results_table.setItem(row, 2, QTableWidgetItem(result['regime']))
         self.optimization_results_table.setItem(row, 3, QTableWidgetItem(f"{result['score']:.2f}"))
         self.optimization_results_table.setItem(row, 4,
 QTableWidgetItem(f"{result['win_rate']:.2%}"))
         self.optimization_results_table.setItem(row, 5,
 QTableWidgetItem(f"{result['profit_factor']:.2f}"))
 3. IndicatorOptimizationThread:
 class IndicatorOptimizationThread(QThread):
     finished = pyqtSignal(list)
     progress = pyqtSignal(int, str)

     def run(self):
         results = []
         total_iterations = self._calculate_total_iterations()
         current = 0

         for ind_type in self.selected_indicators:
             for params in self._generate_param_combinations(ind_type):
                 # 1. Run backtest with single indicator
                 config = self._create_single_indicator_config(ind_type, params)
                 backtest_results = BacktestEngine().run(config, ...)

                 # 2. Calculate score per regime
                 regime_scores = self._calculate_regime_scores(backtest_results)

                 # 3. Store results
                 for regime, score_data in regime_scores.items():
                     results.append({
                         'indicator': ind_type,
                         'params': params,
                         'regime': regime,
                         'score': score_data['score'],
                         'win_rate': score_data['win_rate'],
                         'profit_factor': score_data['profit_factor']
                     })

                 current += 1
                 self.progress.emit(int(current / total_iterations * 100), f"Testing
 {ind_type}{params}...")

         self.finished.emit(results)

 Dateien:
 - src/ui/dialogs/entry_analyzer_popup.py (modify - add tab)
 - src/ui/threads/indicator_optimization_thread.py (new)
 - src/core/tradingbot/indicator_optimizer.py (new)

 ---
 1.4 Regime-Set Backtesting (ERWEITERT)

 Ziel: Beste Indikatoren pro Regime kombinieren, gewichten, backtesten

 Schritte:
 1. "Create Regime Set" Button:
 def _create_regime_set_from_optimization_results(self):
     # 1. Group results by regime
     regime_groups = self._group_results_by_regime(self.optimization_results)

     # 2. Select top N indicators per regime (e.g., top 3)
     regime_set = {}
     for regime, indicators in regime_groups.items():
         # Sort by score
         sorted_indicators = sorted(indicators, key=lambda x: x['score'], reverse=True)
         top_indicators = sorted_indicators[:3]

         # Calculate weights (normalize scores)
         total_score = sum(ind['score'] for ind in top_indicators)
         weights = {
             ind['indicator']: ind['score'] / total_score
             for ind in top_indicators
         }

         regime_set[regime] = {
             'indicators': top_indicators,
             'weights': weights
         }

     return regime_set

 def _create_json_config_from_regime_set(self, regime_set):
     # Generate JSON config with regime-based routing
     config = {
         "schema_version": "1.0.0",
         "indicators": [],
         "regimes": [],
         "strategies": [],
         "strategy_sets": [],
         "routing": []
     }

     for regime, data in regime_set.items():
         # Add indicators
         for ind in data['indicators']:
             config['indicators'].append({
                 "id": f"{ind['indicator'].lower()}_{ind['params']}",
                 "type": ind['indicator'],
                 "params": ind['params']
             })

         # Add regime definition
         config['regimes'].append({
             "id": f"regime_{regime}",
             "name": regime,
             "conditions": self._generate_regime_conditions(regime)
         })

         # Add strategy for this regime
         config['strategies'].append({
             "id": f"strategy_{regime}",
             "entry_conditions": self._generate_entry_conditions(data),
             "exit_conditions": {...},
             "risk": {...}
         })

         # Add strategy set
         config['strategy_sets'].append({
             "id": f"set_{regime}",
             "strategies": [f"strategy_{regime}"]
         })

         # Add routing rule
         config['routing'].append({
             "regimes": {"all_of": [f"regime_{regime}"]},
             "strategy_set_id": f"set_{regime}"
         })

     return config
 2. Regime-Set Backtest:
 def _on_backtest_regime_set_clicked(self):
     # 1. Create regime set from optimization results
     regime_set = self._create_regime_set_from_optimization_results()

     # 2. Generate JSON config
     config_dict = self._create_json_config_from_regime_set(regime_set)
     config = TradingBotConfig(**config_dict)

     # 3. Run backtest
     results = BacktestEngine().run(config, self.symbol, self.start_date, self.end_date,
 self.capital)

     # 4. Compare with single-indicator results
     comparison = self._compare_regime_set_vs_single_indicators(results)

     # 5. Display results
     self._display_regime_set_results(results, comparison)

 Dateien:
 - src/ui/dialogs/entry_analyzer_popup.py (modify)
 - src/core/tradingbot/regime_set_builder.py (new)

 ---
 Phase 2: Start Bot - JSON Strategy Integration

 2.1 JSON Strategy Selection Dialog (KRITISCH)

 Ziel: UI-Dialog zur Auswahl der JSON-Strategy vor Bot-Start

 Schritte:
 1. Strategy Settings Dialog erstellen:
 class StrategySettingsDialog(QDialog):
     def __init__(self, parent=None):
         super().__init__(parent)
         self.setWindowTitle("Strategy Settings")
         self.setMinimumSize(800, 600)

         layout = QVBoxLayout(self)

         # JSON Config Selection
         config_group = QGroupBox("JSON Strategy Configuration")
         config_layout = QFormLayout(config_group)

         self.config_file_input = QLineEdit()
         self.browse_btn = QPushButton("Browse...")
         self.browse_btn.clicked.connect(self._on_browse_clicked)

         config_file_layout = QHBoxLayout()
         config_file_layout.addWidget(self.config_file_input)
         config_file_layout.addWidget(self.browse_btn)

         config_layout.addRow("Config File:", config_file_layout)

         # Config Preview
         self.config_preview = QTextEdit()
         self.config_preview.setReadOnly(True)
         config_layout.addRow("Preview:", self.config_preview)

         layout.addWidget(config_group)

         # Current Regime Display
         regime_group = QGroupBox("Current Market Regime")
         regime_layout = QVBoxLayout(regime_group)

         self.current_regime_label = QLabel("Detecting...")
         self.current_regime_label.setStyleSheet("font-size: 16px; font-weight: bold;")
         regime_layout.addWidget(self.current_regime_label)

         self.regime_details = QTextEdit()
         self.regime_details.setReadOnly(True)
         self.regime_details.setMaximumHeight(100)
         regime_layout.addWidget(self.regime_details)

         layout.addWidget(regime_group)

         # Matched Strategy Display
         strategy_group = QGroupBox("Matched Strategy")
         strategy_layout = QVBoxLayout(strategy_group)

         self.matched_strategy_label = QLabel("No strategy matched")
         self.matched_strategy_label.setStyleSheet("font-size: 14px;")
         strategy_layout.addWidget(self.matched_strategy_label)

         self.strategy_conditions = QTextEdit()
         self.strategy_conditions.setReadOnly(True)
         strategy_layout.addWidget(self.strategy_conditions)

         layout.addWidget(strategy_group)

         # Buttons
         button_layout = QHBoxLayout()
         self.analyze_btn = QPushButton("🔍 Analyze Current Market")
         self.analyze_btn.clicked.connect(self._on_analyze_clicked)

         self.apply_btn = QPushButton("✓ Apply Strategy")
         self.apply_btn.clicked.connect(self.accept)
         self.apply_btn.setEnabled(False)

         self.cancel_btn = QPushButton("Cancel")
         self.cancel_btn.clicked.connect(self.reject)

         button_layout.addWidget(self.analyze_btn)
         button_layout.addStretch()
         button_layout.addWidget(self.apply_btn)
         button_layout.addWidget(self.cancel_btn)

         layout.addLayout(button_layout)
 2. Marktanalyse-Integration:
 def _on_analyze_clicked(self):
     # 1. Load JSON config
     config_path = self.config_file_input.text()
     if not config_path or not os.path.exists(config_path):
         QMessageBox.warning(self, "Error", "Please select a valid config file")
         return

     config = ConfigLoader().load_config(config_path)

     # 2. Get current market data
     symbol = self.parent().get_current_symbol()
     features = self.parent().get_current_features()  # Latest FeatureVector

     # 3. Detect current regime
     regime_engine = RegimeEngine()
     current_regime = regime_engine.classify(features)

     # Update regime display
     self.current_regime_label.setText(
         f"{current_regime.regime.name} - {current_regime.volatility.name}"
     )
     self.regime_details.setText(
         f"ADX: {current_regime.adx:.2f}\n"
         f"ATR%: {current_regime.atr_pct:.2f}%\n"
         f"Confidence: {current_regime.regime_confidence:.2%}"
     )

     # 4. Route to strategy
     indicator_values = IndicatorValueCalculator().calculate(features)
     detector = RegimeDetector(config.regimes)
     active_regimes = detector.detect_active_regimes(indicator_values, scope='entry')

     router = StrategyRouter(config.routing, config.strategy_sets)
     matched_set = router.route(active_regimes)

     if matched_set:
         # Update matched strategy display
         self.matched_strategy_label.setText(f"✓ Matched: {matched_set.strategy_set.name}")

         # Display entry/exit conditions
         conditions_text = self._format_strategy_conditions(matched_set)
         self.strategy_conditions.setText(conditions_text)

         # Enable apply button
         self.apply_btn.setEnabled(True)

         # Store matched set
         self.matched_strategy_set = matched_set
     else:
         self.matched_strategy_label.setText("⚠ No strategy matched current regime")
         self.apply_btn.setEnabled(False)
 3. Integration mit Start Bot Button:
 # In bot_ui_control_widgets.py oder bot_ui_signals_mixin.py
 def _on_bot_start_clicked(self):
     # 1. Show Strategy Settings Dialog
     dialog = StrategySettingsDialog(self)
     if dialog.exec_() == QDialog.Accepted:
         # 2. Get selected config and matched strategy
         config_path = dialog.config_file_input.text()
         matched_set = dialog.matched_strategy_set

         # 3. Pass to BotController
         self.bot_controller.set_json_config(config_path)
         self.bot_controller.set_initial_strategy(matched_set)

         # 4. Start bot
         self.bot_controller.start()

         # 5. Update UI
         self.bot_status_label.setText("Status: RUNNING")
         self.bot_start_btn.setEnabled(False)
         self.bot_stop_btn.setEnabled(True)

 Dateien:
 - src/ui/dialogs/strategy_settings_dialog.py (modify existing or create new)
 - src/ui/widgets/chart_window_mixins/bot_ui_control_widgets.py (modify)
 - src/ui/widgets/chart_window_mixins/bot_ui_signals_mixin.py (modify)

 ---
 2.2 Dynamic Strategy Switching (ERWEITERT)

 Ziel: Automatische Strategy-Umschaltung bei Regime-Änderungen während Bot-Laufzeit

 Schritte:
 1. Regime-Monitor im BotController:
 # In src/core/tradingbot/bot_controller.py

 def _on_new_bar(self, bar_data):
     # Existing bar processing...

     # Check for regime change
     if self.json_config:
         current_features = self.feature_engine.process_bar(bar_data)
         new_regime = self.regime_engine.classify(current_features)

         if self._has_regime_changed(new_regime):
             logger.info(f"Regime changed: {self.current_regime.regime} → {new_regime.regime}")

             # Route to new strategy
             indicator_values = IndicatorValueCalculator().calculate(current_features)
             active_regimes = self.regime_detector.detect_active_regimes(indicator_values,
 scope='entry')
             matched_set = self.strategy_router.route(active_regimes)

             if matched_set:
                 # Switch strategy
                 self._switch_strategy(matched_set)

                 # Emit event
                 self.event_bus.emit('regime_changed', {
                     'old_regime': self.current_regime,
                     'new_regime': new_regime,
                     'new_strategy': matched_set.strategy_set.name
                 })

             self.current_regime = new_regime

 def _has_regime_changed(self, new_regime):
     if not self.current_regime:
         return True
     return (
         new_regime.regime != self.current_regime.regime or
         new_regime.volatility != self.current_regime.volatility
     )

 def _switch_strategy(self, matched_set):
     logger.info(f"Switching to strategy: {matched_set.strategy_set.name}")

     # Apply parameter overrides
     self.strategy_executor.prepare_execution(matched_set)

     # Update internal strategy reference
     self.current_strategy_set = matched_set

     # Adjust open positions if needed
     self._adjust_positions_for_new_regime()
 2. UI-Benachrichtigung bei Strategy-Wechsel:
 # In bot_ui_control_widgets.py

 def _on_regime_changed(self, event_data):
     old_regime = event_data['old_regime']
     new_regime = event_data['new_regime']
     new_strategy = event_data['new_strategy']

     # Update regime label
     self.regime_label.setText(
         f"Regime: {new_regime.regime.name} ({new_regime.volatility.name})"
     )

     # Update strategy label
     self.strategy_label.setText(f"Strategy: {new_strategy}")

     # Show notification
     notification = QLabel(
         f"⚠ Regime changed to {new_regime.regime.name}. "
         f"Switched to strategy: {new_strategy}"
     )
     notification.setStyleSheet(
         "background-color: #ffa726; padding: 10px; border-radius: 5px;"
     )

     # Add to notification area (e.g., status bar or dedicated widget)
     self.notification_area.add_notification(notification)

     # Auto-hide after 10 seconds
     QTimer.singleShot(10000, lambda: self.notification_area.remove_notification(notification))

 Dateien:
 - src/core/tradingbot/bot_controller.py (modify)
 - src/ui/widgets/chart_window_mixins/bot_ui_control_widgets.py (modify)

 ---
 5. ENTSCHEIDUNG: ENTRY ANALYZER UI

 Analyse der bestehenden UI

 Vorteile:
 - ✅ Vollständig implementiert mit allen 5 Tabs
 - ✅ Backtest Setup Tab vorhanden (JSON-Loader, Date Range, Capital)
 - ✅ Results Tab vorhanden (Performance Summary, Trade List)
 - ✅ Footer mit Actions (Draw on Chart, Clear, Report)
 - ✅ Saubere Struktur mit Tabs

 Nachteile:
 - ❌ Kein "Indicator Optimization" Tab
 - ❌ Kein "Regime Set Creation" Tab
 - ❌ Keine Regime-Visualisierung im Chart

 Empfehlung: ERWEITERN (nicht neu erstellen)

 Begründung:
 1. Bestehende Struktur ist solide: Tab-basiertes Design ist skalierbar
 2. Zeitersparnis: Keine Duplikation von bestehendem Code
 3. Konsistenz: Gleiche UI-Patterns wie bisher
 4. Geringes Risiko: Nur neue Tabs hinzufügen, keine Breaking Changes

 Konkrete Erweiterungen:
 1. Neuer Tab: "Indicator Optimization" (zwischen "Backtest Setup" und "Visible Range Analysis")
 2. Neuer Tab: "Regime Set Builder" (nach "Backtest Results")
 3. Chart-Integration: Regime-Visualisierung über neues Mixin
 4. Backtest-Button Verdrahtung: Signal/Slot Connection

 ---
 6. PRIORISIERUNG

 KRITISCHE PFADE (MUST-HAVE)

 Priority 1: Entry Analyzer Backtesting (Highest Impact)
 1. Backtest-Button Verdrahtung → BacktestEngine (1.1)
 2. Regime-Visualisierung im Chart (1.2)

 Priority 2: Start Bot JSON Integration (User Workflow)
 3. JSON Strategy Selection Dialog (2.1)
 4. Marktanalyse-Integration vor Bot-Start (2.1)

 ERWEITERTE FEATURES (NICE-TO-HAVE)

 Priority 3: Advanced Optimization
 5. Indicator-Scoring-System mit Parameter-Ranges (1.3)
 6. Regime-Set Backtesting (1.4)

 Priority 4: Runtime Features
 7. Dynamic Strategy Switching bei Regime-Änderungen (2.2)
 8. UI-Benachrichtigung bei Strategy-Wechsel (2.2)

 ---
 7. KRITISCHE DATEIEN

 Zu modifizierende Dateien:

 1. Entry Analyzer Popup:
   - src/ui/dialogs/entry_analyzer_popup.py (add signal/slot, tabs)
 2. Chart Window:
   - src/ui/widgets/chart_window_setup.py (add regime visualization methods)
   - NEW: src/ui/widgets/chart_window_mixins/regime_visualization_mixin.py
 3. Bot Controller:
   - src/core/tradingbot/bot_controller.py (add regime monitoring, strategy switching)
 4. Bot UI Control:
   - src/ui/widgets/chart_window_mixins/bot_ui_control_widgets.py (connect to strategy dialog)
   - src/ui/widgets/chart_window_mixins/bot_ui_signals_mixin.py (connect to strategy dialog)

 Zu erstellende Dateien:

 1. Threads:
   - src/ui/threads/backtest_thread.py (background backtesting)
   - src/ui/threads/indicator_optimization_thread.py (parameter optimization)
 2. Dialogs:
   - src/ui/dialogs/strategy_settings_dialog.py (modify existing if present, or create)
 3. Backend:
   - src/core/tradingbot/indicator_optimizer.py (indicator parameter optimization logic)
   - src/core/tradingbot/regime_set_builder.py (regime set creation & JSON generation)

 ---
 8. VERIFIKATION

 Nach jeder Phase:

 Phase 1.1 (Backtest-Button):
 # Test: Run Backtest Button
 1. Öffne Entry Analyzer
 2. Wähle JSON-Config: "03_JSON/Trading_Bot/trend_following_conservative.json"
 3. Setze Date Range: 2024-01-01 bis 2024-12-31
 4. Klicke "Run Backtest"
 5. Erwartung: Progress-Bar → Results Tab mit Performance-Metriken

 Phase 1.2 (Regime-Visualisierung):
 # Test: Regime Lines im Chart
 1. Nach Backtest abgeschlossen
 2. Klicke "Draw on Chart"
 3. Erwartung: Vertikale Linien im Chart (grün=Trend Up, rot=Trend Down, orange=Range)

 Phase 2.1 (Start Bot JSON Integration):
 # Test: JSON Strategy Selection
 1. Klicke "Start Bot" Button
 2. Erwartung: Strategy Settings Dialog öffnet sich
 3. Wähle JSON-Config
 4. Klicke "Analyze Current Market"
 5. Erwartung: Current Regime angezeigt + Matched Strategy
 6. Klicke "Apply Strategy"
 7. Erwartung: Bot startet mit JSON-basierter Strategy

 ---
 9. RISIKEN & MITIGATION

 Risiko 1: Thread-Safety

 Problem: UI-Updates aus Background-Threads können zu Crashes führen
 Mitigation: Verwende pyqtSignal für alle Thread-UI-Kommunikation

 Risiko 2: Performance

 Problem: Indicator-Optimization mit vielen Parameter-Kombinationen kann lange dauern
 Mitigation:
 - Progress-Bar mit Cancel-Button
 - Caching von Indicator-Berechnungen
 - Batch-Processing mit multiprocessing

 Risiko 3: Config-Synchronisation

 Problem: Config-Änderungen während Bot-Laufzeit können zu Inkonsistenzen führen
 Mitigation:
 - Config-Reloading nur bei Bot-Pause oder zwischen Trades
 - Validation vor jeder Config-Anwendung
 - Rollback bei Validation-Fehler

 ---
 10. NÄCHSTE SCHRITTE

 1. User-Feedback einholen:
   - Priorisierung bestätigen (kritische vs. erweiterte Features)
   - UI-Design für neue Tabs besprechen
 2. Implementation starten:
   - Phase 1.1: Backtest-Button Verdrahtung (2-3 Stunden)
   - Phase 1.2: Regime-Visualisierung (3-4 Stunden)
   - Phase 2.1: JSON Strategy Selection Dialog (4-5 Stunden)
 3. Testing & Iteration:
   - Unit-Tests für neue Funktionen
   - Integration-Tests für UI-Flows
   - User Acceptance Testing

 Geschätzter Gesamtaufwand:
 - Kritische Pfade (P1+P2): 12-15 Stunden
 - Erweiterte Features (P3+P4): 20-25 Stunden
 - Total: 32-40 Stunden (4-5 Arbeitstage)