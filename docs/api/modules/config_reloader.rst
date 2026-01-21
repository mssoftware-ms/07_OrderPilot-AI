config_reloader
===============

.. module:: src.core.tradingbot.config_reloader
   :synopsis: Thread-safe configuration reloader with file watching and debouncing

Overview
--------

The ``config_reloader`` module provides thread-safe, automatic reloading of JSON configuration files with file system monitoring. It enables live strategy updates without restarting the trading bot, essential for production environments where downtime must be minimized.

**Key Features:**

* **Watchdog File Monitoring**: Detects config file changes in real-time using watchdog library
* **Debouncing**: Ignores rapid consecutive changes (configurable delay, default 1.0s)
* **Thread-Safe Reloading**: Uses RLock for atomic config replacement
* **Event-Bus Integration**: Emits "config_reloaded" events for bot-wide notification
* **Callback Support**: Custom callbacks for reload notifications
* **Graceful Shutdown**: Clean observer termination with timeout
* **Validation**: Automatic validation on every reload (JSON Schema + Pydantic)
* **Error Resilience**: Failed reloads don't affect current config (rollback on error)

**Use Cases:**

* Live strategy parameter tuning in production
* A/B testing different configurations
* Emergency strategy changes during volatile markets
* Development with instant config feedback
* Multi-instance coordination (shared config file)

Usage Example
-------------

**Basic Auto-Reload Setup:**

.. code-block:: python

    from src.core.tradingbot.config_reloader import ConfigReloader
    from pathlib import Path

    # Initialize with auto-reload enabled
    reloader = ConfigReloader(
        config_path=Path("03_JSON/Trading_Bot/trend_following.json"),
        schema_path=Path("schemas/trading_bot_config_schema.json"),
        auto_reload=True,  # Start watching immediately
        debounce_seconds=1.0  # Ignore changes within 1 second
    )

    # Get current config
    current_config = reloader.config
    print(f"Loaded {len(current_config.strategies)} strategies")

    # Config automatically reloads when file changes
    # (edit trend_following.json in editor)
    # Observer detects change → debounced → reloaded → callback fired

    # Cleanup when done
    reloader.stop_watching()

**Manual Reload with Callback:**

.. code-block:: python

    def on_config_reloaded(new_config, old_config):
        """Called after successful reload"""
        print(f"Config reloaded!")
        print(f"Strategies: {len(old_config.strategies)} → {len(new_config.strategies)}")

        # Update bot components
        bot.update_strategies(new_config.strategies)
        bot.update_regimes(new_config.regimes)

    # Initialize without auto-reload
    reloader = ConfigReloader(
        config_path=Path("config.json"),
        on_reload=on_config_reloaded,
        auto_reload=False  # Manual control
    )

    # Manually trigger reload
    try:
        new_config = reloader.reload_config(notify=True)
        print("Reload successful!")
    except Exception as e:
        print(f"Reload failed: {e}")
        # Current config unchanged (rollback on error)

**Event-Bus Integration:**

.. code-block:: python

    from src.core.event_bus import EventBus

    # Create event bus for bot-wide notifications
    event_bus = EventBus()

    # Initialize reloader with event bus
    reloader = ConfigReloader(
        config_path=Path("config.json"),
        event_bus=event_bus,
        auto_reload=True
    )

    # Subscribe to reload events in other components
    def update_regime_engine(event):
        new_config = event["new_config"]
        regime_engine.update_regimes(new_config.regimes)

    event_bus.subscribe("config_reloaded", update_regime_engine)

    # Reload automatically fires event to all subscribers

**Production Setup with Error Handling:**

.. code-block:: python

    import logging

    logger = logging.getLogger(__name__)

    def on_reload_error(error: Exception):
        """Handle reload failures"""
        logger.error(f"Config reload failed: {error}", exc_info=True)

        # Send alert to monitoring system
        alert_system.send_alert(
            severity="HIGH",
            message=f"Trading bot config reload failed: {error}"
        )

        # Optionally: stop auto-reload after repeated failures
        if error_count > 3:
            reloader.stop_watching()

    # Production reloader
    reloader = ConfigReloader(
        config_path=Path("/etc/tradingbot/config.json"),
        schema_path=Path("/etc/tradingbot/schema.json"),
        auto_reload=True,
        debounce_seconds=2.0,  # Longer debounce in prod
        on_reload=lambda new, old: logger.info("Config reloaded successfully")
    )

    # Monitor health
    if not reloader.is_watching:
        logger.warning("Config auto-reload is not active!")

Classes
-------

.. autoclass:: src.core.tradingbot.config_reloader.ConfigFileHandler
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: src.core.tradingbot.config_reloader.ConfigReloader
   :members:
   :undoc-members:
   :show-inheritance:

Key Methods
-----------

**ConfigFileHandler.on_modified**

Handles file modification events with debouncing.

Algorithm:

1. **Check Event Type**:

   .. code-block:: python

       if event.is_directory:
           return  # Ignore directory events

       if event.src_path != str(self.config_path):
           return  # Ignore unrelated files

2. **Acquire Debounce Lock**:

   .. code-block:: python

       with self._reload_lock:

3. **Check Debounce Window**:

   .. code-block:: python

       current_time = time.time()
       time_since_last = current_time - self._last_reload_time

       if time_since_last < self.debounce_seconds:
           logger.debug(f"Ignoring rapid change ({time_since_last:.2f}s)")
           return

4. **Update Last Reload Time**:

   .. code-block:: python

       self._last_reload_time = current_time

5. **Trigger Reload Callback**:

   .. code-block:: python

       logger.info(f"Config file modified, reloading...")
       self.reload_callback()

**Parameters:**

* ``event`` (FileSystemEvent): Watchdog file system event

**Returns:**

* None

**ConfigReloader.reload_config**

Reloads configuration from disk with validation and atomicity.

Algorithm:

1. **Acquire Config Lock** (thread-safe):

   .. code-block:: python

       with self._config_lock:

2. **Load and Validate New Config**:

   .. code-block:: python

       try:
           new_config = self.loader.load_config(self.config_path)
       except Exception as e:
           logger.error(f"Config reload failed: {e}")
           raise  # Current config unchanged

3. **Store Old Config** (for callback):

   .. code-block:: python

       old_config = self._config

4. **Atomic Replacement**:

   .. code-block:: python

       self._config = new_config
       logger.info(f"Config reloaded from {self.config_path}")

5. **Call Reload Callback** (if notify=True):

   .. code-block:: python

       if notify and self.on_reload:
           try:
               self.on_reload(new_config, old_config)
           except Exception as e:
               logger.error(f"Reload callback failed: {e}")

6. **Emit Event-Bus Event** (if configured):

   .. code-block:: python

       if notify and self.event_bus:
           self.event_bus.emit("config_reloaded", {
               "new_config": new_config,
               "old_config": old_config,
               "timestamp": datetime.now()
           })

7. **Return New Config**:

   .. code-block:: python

       return new_config

**Parameters:**

* ``notify`` (bool): Whether to call callback and emit event (default: True)

**Returns:**

* ``TradingBotConfig``: Newly loaded configuration

**Raises:**

* ``FileNotFoundError``: Config file doesn't exist
* ``ValueError``: Invalid JSON syntax
* ``ValidationError``: Schema validation failed

**ConfigReloader.start_watching**

Starts file system watching for automatic reloads.

Algorithm:

1. **Check Already Watching**:

   .. code-block:: python

       if self._observer is not None:
           logger.warning("File watching already active")
           return

2. **Create Observer** (watchdog):

   .. code-block:: python

       self._observer = Observer()

3. **Create Event Handler**:

   .. code-block:: python

       handler = ConfigFileHandler(
           config_path=self.config_path,
           reload_callback=self._on_file_modified,
           debounce_seconds=self.debounce_seconds
       )

4. **Schedule Watching** (monitor parent directory):

   .. code-block:: python

       watch_path = self.config_path.parent
       self._observer.schedule(handler, str(watch_path), recursive=False)

5. **Start Observer Thread**:

   .. code-block:: python

       self._observer.start()
       logger.info(f"Started watching {self.config_path}")

**Parameters:**

* None

**Returns:**

* None

**ConfigReloader.stop_watching**

Stops file system watching gracefully.

Algorithm:

1. **Check Observer Exists**:

   .. code-block:: python

       if self._observer is None:
           return  # Already stopped

2. **Stop Observer**:

   .. code-block:: python

       self._observer.stop()

3. **Wait for Thread** (with timeout):

   .. code-block:: python

       self._observer.join(timeout=2.0)

4. **Clear Reference**:

   .. code-block:: python

       self._observer = None
       logger.info("Stopped config file watching")

**Parameters:**

* None

**Returns:**

* None

**ConfigReloader._on_file_modified**

Internal callback for file modification events.

Algorithm:

1. **Log Event**:

   .. code-block:: python

       logger.info(f"Config file {self.config_path} modified, reloading...")

2. **Reload Config**:

   .. code-block:: python

       try:
           self.reload_config(notify=True)
       except Exception as e:
           logger.error(f"Auto-reload failed: {e}", exc_info=True)

**Parameters:**

* None

**Returns:**

* None

Common Patterns
---------------

**Pattern 1: Development with Instant Feedback**

Use auto-reload for rapid iteration during strategy development:

.. code-block:: python

    # Initialize with very responsive debounce
    reloader = ConfigReloader(
        config_path=Path("dev_config.json"),
        auto_reload=True,
        debounce_seconds=0.5  # Faster feedback in dev
    )

    # Run bot in development mode
    while developing:
        # 1. Edit dev_config.json in IDE
        # 2. Save file
        # 3. Observer detects change
        # 4. Config auto-reloads (0.5s delay)
        # 5. Bot uses new config immediately

        feature_vector = feature_engine.process_bar(bar_data)
        strategies = catalog.get_active_strategy_sets(feature_vector)
        # Uses latest config parameters

**Pattern 2: Production with Health Monitoring**

Monitor reload health and alert on failures:

.. code-block:: python

    class ConfigHealthMonitor:
        def __init__(self, reloader):
            self.reloader = reloader
            self.reload_count = 0
            self.error_count = 0
            self.last_reload = None

        def on_reload_success(self, new_config, old_config):
            self.reload_count += 1
            self.last_reload = datetime.now()
            self.error_count = 0  # Reset error counter

            logger.info(f"Config reload #{self.reload_count} successful")

            # Log changes
            if len(new_config.strategies) != len(old_config.strategies):
                logger.warning(
                    f"Strategy count changed: "
                    f"{len(old_config.strategies)} → {len(new_config.strategies)}"
                )

        def on_reload_error(self, error):
            self.error_count += 1

            logger.error(f"Config reload error #{self.error_count}: {error}")

            # Alert after 3 consecutive failures
            if self.error_count >= 3:
                alert_system.send_critical_alert(
                    "Config auto-reload failing repeatedly!"
                )

                # Stop watching to prevent spam
                self.reloader.stop_watching()

    # Setup monitoring
    monitor = ConfigHealthMonitor(reloader)
    reloader.on_reload = monitor.on_reload_success

**Pattern 3: Multi-Instance Coordination**

Multiple bot instances sharing the same config file:

.. code-block:: python

    # Instance 1: BTC trading bot
    btc_reloader = ConfigReloader(
        config_path=Path("/shared/configs/crypto_strategy.json"),
        auto_reload=True,
        debounce_seconds=2.0
    )

    # Instance 2: ETH trading bot (same config)
    eth_reloader = ConfigReloader(
        config_path=Path("/shared/configs/crypto_strategy.json"),
        auto_reload=True,
        debounce_seconds=2.0
    )

    # Single config update propagates to all instances:
    # 1. Admin edits /shared/configs/crypto_strategy.json
    # 2. Both observers detect change
    # 3. Both reload independently (2s debounce)
    # 4. Both bots use new parameters

**Pattern 4: Conditional Reloading**

Only reload if certain conditions are met:

.. code-block:: python

    def conditional_reload_callback(new_config, old_config):
        # Only reload during off-market hours
        if not market_is_open():
            logger.info("Market closed, applying new config")
            bot.update_config(new_config)
        else:
            logger.warning("Market open, deferring config reload")
            # Schedule reload for market close
            scheduler.schedule_at(market_close_time, bot.update_config, new_config)

    reloader = ConfigReloader(
        config_path=config_path,
        on_reload=conditional_reload_callback,
        auto_reload=True
    )

**Pattern 5: Config Versioning with Rollback**

Track config versions and support rollback:

.. code-block:: python

    class VersionedConfigReloader:
        def __init__(self, reloader):
            self.reloader = reloader
            self.config_history = []
            self.max_history = 10

        def on_reload(self, new_config, old_config):
            # Store old config in history
            self.config_history.append({
                "config": old_config,
                "timestamp": datetime.now(),
                "version": len(self.config_history) + 1
            })

            # Trim history
            if len(self.config_history) > self.max_history:
                self.config_history.pop(0)

            logger.info(f"Config version {len(self.config_history)} loaded")

        def rollback(self, versions=1):
            """Rollback to previous config"""
            if len(self.config_history) < versions:
                raise ValueError("Not enough history for rollback")

            # Get previous config
            previous = self.config_history[-(versions)]

            logger.warning(f"Rolling back to version {previous['version']}")

            # Write to disk and reload
            with open(self.reloader.config_path, 'w') as f:
                json.dump(previous['config'].dict(), f, indent=2)

            # Manual reload (triggers observer)
            self.reloader.reload_config()

    versioned = VersionedConfigReloader(reloader)
    reloader.on_reload = versioned.on_reload

    # Rollback if needed
    if bad_performance_detected():
        versioned.rollback(versions=1)  # Go back 1 version

Data Models
-----------

**ConfigFileHandler**

Watchdog event handler for config file changes.

.. code-block:: python

    class ConfigFileHandler(FileSystemEventHandler):
        def __init__(
            self,
            config_path: Path,
            reload_callback: Callable[[], None],
            debounce_seconds: float = 1.0
        ):
            self.config_path = config_path
            self.reload_callback = reload_callback
            self.debounce_seconds = debounce_seconds
            self._last_reload_time = 0.0
            self._reload_lock = threading.Lock()

**ConfigReloader**

Thread-safe configuration reloader with file watching.

.. code-block:: python

    class ConfigReloader:
        def __init__(
            self,
            config_path: Path,
            schema_path: Path | None = None,
            on_reload: Callable[[TradingBotConfig, TradingBotConfig], None] | None = None,
            event_bus: EventBus | None = None,
            auto_reload: bool = True,
            debounce_seconds: float = 1.0
        ):
            self.config_path = config_path
            self.loader = ConfigLoader(schema_path=schema_path)
            self.on_reload = on_reload
            self.event_bus = event_bus
            self.debounce_seconds = debounce_seconds

            # Thread-safe config access
            self._config_lock = threading.RLock()
            self._config = self.loader.load_config(config_path)

            # Watchdog observer
            self._observer: Observer | None = None

            # Auto-start watching
            if auto_reload:
                self.start_watching()

Best Practices
--------------

**✅ DO:**

* **Use debounce >= 1.0s in production**: Prevents reload storms from rapid file saves
* **Monitor reload health**: Track reload count, errors, and last reload time
* **Test reload under load**: Verify RLock doesn't cause contention during high-frequency trading
* **Stop watching on shutdown**: Call ``stop_watching()`` before process exit
* **Use event-bus for coordination**: Notify all bot components about config changes
* **Validate before saving**: Only write valid configs to disk

.. code-block:: python

    # ✅ GOOD: Production setup with monitoring
    reloader = ConfigReloader(
        config_path=Path("/etc/bot/config.json"),
        schema_path=Path("/etc/bot/schema.json"),
        auto_reload=True,
        debounce_seconds=2.0,  # Reasonable debounce
        on_reload=lambda new, old: health_monitor.log_reload(new, old)
    )

    # Cleanup on exit
    atexit.register(reloader.stop_watching)

**❌ DON'T:**

* **Don't use very low debounce (<0.5s)**: Causes unnecessary reloads from editor auto-save
* **Don't reload during active trades**: Can cause inconsistent state
* **Don't ignore reload errors**: Always log and alert on failures
* **Don't share observer across reloaders**: Each reloader needs its own observer
* **Don't modify config while reloading**: RLock acquisition can cause brief delays
* **Don't forget to stop watching**: Observer threads prevent clean shutdown

.. code-block:: python

    # ❌ BAD: Very low debounce causes reload spam
    reloader = ConfigReloader(
        config_path=config_path,
        auto_reload=True,
        debounce_seconds=0.1  # Too fast! Editor auto-save triggers multiple reloads
    )

    # ✅ GOOD: Reasonable debounce
    reloader = ConfigReloader(
        config_path=config_path,
        auto_reload=True,
        debounce_seconds=1.0
    )

    # ❌ BAD: Ignoring errors
    try:
        reloader.reload_config()
    except Exception:
        pass  # Silent failure!

    # ✅ GOOD: Proper error handling
    try:
        reloader.reload_config()
    except Exception as e:
        logger.error(f"Reload failed: {e}", exc_info=True)
        alert_system.send_alert(f"Config reload error: {e}")

**Performance Considerations:**

* **Reload latency**: ~50-100ms (JSON parse + validation + Pydantic instantiation)
* **Observer overhead**: Watchdog uses ~5-10 MB memory, negligible CPU when idle
* **Lock contention**: RLock acquisition is <1ms, but can delay concurrent reads during reload
* **File I/O**: Reading config file from disk takes ~5-10ms for typical 50 KB files
* **Debounce accuracy**: ±10ms variation due to Python threading and OS scheduling

**Testing Strategy:**

.. code-block:: python

    # Unit test: Debouncing
    def test_debounce():
        reloader = ConfigReloader(config_path, auto_reload=False, debounce_seconds=1.0)
        handler = ConfigFileHandler(config_path, reloader.reload_config, debounce_seconds=1.0)

        # Simulate rapid changes
        handler.on_modified(FileModifiedEvent(config_path))
        time.sleep(0.5)  # Within debounce window
        handler.on_modified(FileModifiedEvent(config_path))  # Should be ignored

        assert reload_count == 1  # Only first reload triggered

    # Integration test: Auto-reload
    def test_auto_reload():
        reloader = ConfigReloader(config_path, auto_reload=True)

        # Modify config file
        with open(config_path, 'w') as f:
            json.dump(new_config_dict, f)

        # Wait for observer to detect change
        time.sleep(2.0)

        # Verify reload
        assert reloader.config == new_config

**Security Considerations:**

* **File permissions**: Config file should be readable only by bot user (chmod 600)
* **Validation on reload**: Always validate to prevent injection of malicious configs
* **Audit logging**: Log all reloads with timestamp, user, and changes
* **Rollback capability**: Maintain config history for emergency rollback

See Also
--------

* :doc:`config_loader` - Loads and validates JSON configs with schema validation
* :doc:`config_integration_bridge` - Integration bridge for gradual migration to JSON configs
* :doc:`config_executor` - Applies parameter overrides during strategy execution
