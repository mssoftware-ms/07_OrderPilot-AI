# Trading Bot Code Flow Documentation
## From "Start Bot" to "Entered" Signal

This document details the code execution flow from clicking the "Start Bot" button in the Chart Window to the point where a signal status updates to "entered" in the "Recent Signals" table.

### 1. UI Interaction: "Start Bot" Button
**File:** `src/ui/widgets/chart_window_mixins/bot_ui_control_widgets.py`
**Class:** `BotUIControlWidgets`
**Method:** `build_control_group`

The "Start Bot" button is created and connected to the handler.
```python
self.parent.bot_start_btn = QPushButton("Start Bot")
# ... styling ...
self.parent.bot_start_btn.clicked.connect(self.parent._on_bot_start_clicked)
```

### 2. Event Handler: Starting the Process
**File:** `src/ui/widgets/chart_window_mixins/bot_event_handlers.py`
**Class:** `BotEventHandlersMixin`
**Method:** `_on_bot_start_clicked`

Handles the click event, updates UI status, and initiates the bot startup sequence.
```python
def _on_bot_start_clicked(self) -> None:
    logger.info("Bot start requested")
    self._update_bot_status("STARTING", "#ffeb3b")
    try:
        self._start_bot_with_config() # Delegates to lifecycle mixin
    except Exception as e:
        # ... error handling ...
```

### 3. Lifecycle Management: Configuration & Initialization
**File:** `src/ui/widgets/chart_window_mixins/bot_callbacks_lifecycle_mixin.py`
**Class:** `BotCallbacksLifecycleMixin`
**Method:** `_start_bot_with_config`

Gather settings from UI, create the configuration, and initialize the `BotController`. Crucially, it wires the UI callbacks to the controller.
```python
def _start_bot_with_config(self) -> None:
    # ... resolve symbol and create config ...
    
    self._bot_controller = BotController(
        config,
        on_signal=self._on_bot_signal, # WIRE: Connects engine signals to UI handler
        on_decision=self._on_bot_decision,
        # ... other callbacks ...
    )
    
    # ... warmup ...
    self._bot_controller.start() # Starts the controller/engine
```

### 4. Engine Lifecycle: The Analysis Loop
**File:** `src/core/trading_bot/bot_engine_lifecycle.py`
**Class:** `BotEngineLifecycle`
**Method:** `start` -> `_run_analysis_loop` -> `_run_analysis_cycle`

The engine starts an async task that runs the analysis cycle periodically.
```python
async def _run_analysis_cycle(self) -> None:
    # 1. Fetch Market Data
    df = await self.parent.market_analyzer.fetch_market_data()
    
    # 2. Generate Signal
    signal = self.parent.signal_generator.generate_signal(df, ...)
    
    # 3. Notify Listeners (UI) - "Candidate" Signal
    if self.parent._on_signal_generated:
        self.parent._on_signal_generated(signal) # Triggers _on_bot_signal in UI
        
    # 4. AI Validation
    # ... ai_validator checks ...
    
    # 5. Execution (if valid and approved)
    await self.parent.trade_handler.execute_trade(signal, indicators, market_context)
```

### 5. Signal Generation Logic
**File:** `src/core/trading_bot/signal_generator.py`
**Class:** `SignalGenerator`
**Method:** `generate_signal`

Analyzes technical indicators and confluence to produce a `TradeSignal`.
```python
def generate_signal(self, df: pd.DataFrame, ...) -> TradeSignal:
    # ... validate data ...
    # ... check long/short conditions ...
    # ... calculate confluence ...
    
    signal = TradeSignal(
        direction=direction,
        strength=strength,
        confluence_score=confluence,
        # ...
    )
    return signal
```

### 6. UI Update (Phase 1): Candidate Signal
**File:** `src/ui/widgets/chart_window_mixins/bot_callbacks_signal_handling_mixin.py`
**Class:** `BotCallbacksSignalHandlingMixin`
**Method:** `_on_bot_signal`

Receives the signal (via the callback wired in step 3). Initially, it's a candidate.
```python
def _on_bot_signal(self, signal: Any) -> None:
    # ... extract fields ...
    
    if signal_type == "confirmed":
        # ... logic for confirmed (see Phase 2) ...
    else:
        # Add as PENDING candidate
        self._update_or_add_candidate(
            signal_type, side, score, strategy_name, entry_price, status
        )
    
    self._update_signals_table() # Updates the QTableWidget
```

### 7. Trade Execution: Opening the Position
**File:** `src/core/trading_bot/bot_trade_handler.py`
**Class:** `BotTradeHandler`
**Method:** `execute_trade`

If the signal passed validation in `_run_analysis_cycle`, this method is called.
```python
async def execute_trade(self, signal, ...) -> None:
    # ... risk calculation ...
    # ... create order ...
    response = await self.engine.adapter.place_order(order)
    
    if response and response.status == "FILLED":
        # ... create trade log ...
        
        # Trigger Position Opened Callback
        if self.engine._on_position_opened:
            self.engine._on_position_opened(monitored_pos)
```

### 8. UI Update (Phase 2): Signal "Entered"
**Mechanism:** 
The `_on_position_opened` callback (wired through `BotController`) triggers an update that eventually calls `_on_bot_signal` with `signal_type="confirmed"`.

**File:** `src/ui/widgets/chart_window_mixins/bot_callbacks_signal_handling_mixin.py`
**Method:** `_on_bot_signal` -> `_update_candidate_to_confirmed`

```python
def _on_bot_signal(self, signal: Any) -> None:
    if signal_type == "confirmed":
        # Updates the existing candidate in _signal_history
        updated = self._update_candidate_to_confirmed(...)
        
        # Sets status to "ENTERED"
        # Sets is_open = True
        
        self._update_signals_table() # Refreshes table to show "ENTERED"
```

### 9. Table Rendering
**File:** `src/ui/widgets/chart_window_mixins/bot_display_signals_mixin.py`
**Class:** `BotDisplaySignalsMixin`
**Method:** `_update_signals_table`

Reads from `self._signal_history` and populates the `QTableWidget`.
```python
def _update_signals_table(self) -> None:
    # ... iterate history ...
    for row, signal in enumerate(recent_signals):
        # ...
        # Column 10: Status
        self.signals_table.setItem(row, 10, QTableWidgetItem(signal["status"])) # Displays "ENTERED"
```
