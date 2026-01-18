"""Configuration Reloader with File Watching.

Provides thread-safe live reloading of JSON strategy configurations
with automatic file watching and event notification.

Features:
- Thread-safe config reloading
- File system monitoring with watchdog
- Debouncing for rapid file changes
- Graceful error handling (keeps old config on reload failure)
- Event emission on successful reloads
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .config import ConfigLoader, TradingBotConfig

if TYPE_CHECKING:
    from src.common.event_bus import EventBus

logger = logging.getLogger(__name__)


class ConfigReloadError(Exception):
    """Exception raised when config reload fails."""
    pass


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for config file changes."""

    def __init__(
        self,
        config_path: Path,
        reload_callback: Callable[[], None],
        debounce_seconds: float = 1.0
    ):
        """Initialize file handler.

        Args:
            config_path: Path to config file to watch
            reload_callback: Function to call on file change
            debounce_seconds: Debounce interval for rapid changes
        """
        super().__init__()
        self.config_path = config_path.resolve()
        self.reload_callback = reload_callback
        self.debounce_seconds = debounce_seconds
        self._last_reload_time = 0.0
        self._reload_lock = threading.Lock()

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        # Check if this is our config file
        event_path = Path(event.src_path).resolve()
        if event_path != self.config_path:
            return

        # Debounce: ignore rapid consecutive changes
        current_time = time.time()
        with self._reload_lock:
            if (current_time - self._last_reload_time) < self.debounce_seconds:
                logger.debug(f"Debouncing config reload (too soon after last reload)")
                return

            self._last_reload_time = current_time

        logger.info(f"Config file modified: {self.config_path.name}")
        try:
            self.reload_callback()
        except Exception as e:
            logger.error(f"Config reload callback failed: {e}", exc_info=True)


class ConfigReloader:
    """Thread-safe configuration reloader with file watching.

    Provides live reloading of JSON strategy configurations without
    restarting the bot. Monitors config file for changes and automatically
    reloads with validation.

    Example:
        >>> reloader = ConfigReloader(
        ...     config_path="configs/production.json",
        ...     on_reload=lambda config: print(f"Reloaded: {config.schema_version}")
        ... )
        >>> reloader.start_watching()
        >>> # ... config file changes detected automatically
        >>> reloader.stop_watching()
    """

    def __init__(
        self,
        config_path: Path | str,
        schema_path: Path | str | None = None,
        on_reload: Callable[[TradingBotConfig], None] | None = None,
        event_bus: "EventBus | None" = None,
        auto_reload: bool = True,
        debounce_seconds: float = 1.0
    ):
        """Initialize config reloader.

        Args:
            config_path: Path to JSON config file
            schema_path: Path to JSON schema (uses default if None)
            on_reload: Callback for successful reloads (receives new config)
            event_bus: Event bus for publishing reload events
            auto_reload: Enable automatic file watching
            debounce_seconds: Debounce interval for file changes
        """
        self.config_path = Path(config_path)
        self.schema_path = Path(schema_path) if schema_path else None
        self.on_reload = on_reload
        self.event_bus = event_bus
        self.auto_reload = auto_reload
        self.debounce_seconds = debounce_seconds

        # Config loader
        self.loader = ConfigLoader(schema_path=self.schema_path)

        # Current config (protected by lock)
        self._config: TradingBotConfig | None = None
        self._config_lock = threading.RLock()

        # File watching
        self._observer: Observer | None = None
        self._file_handler: ConfigFileHandler | None = None
        self._watching = False

        # Load initial config
        try:
            self._config = self.loader.load_config(self.config_path)
            logger.info(
                f"Initial config loaded: {len(self._config.strategies)} strategies, "
                f"{len(self._config.regimes)} regimes"
            )
        except Exception as e:
            logger.error(f"Failed to load initial config from {self.config_path}: {e}")
            raise ConfigReloadError(f"Initial config load failed: {e}") from e

    @property
    def current_config(self) -> TradingBotConfig:
        """Get current configuration (thread-safe).

        Returns:
            Current TradingBotConfig instance
        """
        with self._config_lock:
            if self._config is None:
                raise ConfigReloadError("No config loaded")
            return self._config

    def reload_config(self, notify: bool = True) -> TradingBotConfig:
        """Reload configuration from file (thread-safe).

        Args:
            notify: Emit reload event if successful

        Returns:
            Newly loaded config

        Raises:
            ConfigReloadError: If reload fails (old config retained)
        """
        logger.info(f"Reloading config from {self.config_path}")

        try:
            # Load new config (with validation)
            new_config = self.loader.load_config(self.config_path)

            # Update atomically
            with self._config_lock:
                old_config = self._config
                self._config = new_config

            logger.info(
                f"Config reloaded successfully: "
                f"{len(new_config.strategies)} strategies, "
                f"{len(new_config.regimes)} regimes, "
                f"{len(new_config.strategy_sets)} strategy sets"
            )

            # Notify callback
            if self.on_reload:
                try:
                    self.on_reload(new_config)
                except Exception as e:
                    logger.error(f"Reload callback failed: {e}", exc_info=True)

            # Emit event
            if notify and self.event_bus:
                self._emit_reload_event(old_config, new_config)

            return new_config

        except Exception as e:
            logger.error(f"Config reload failed: {e}. Keeping old config.", exc_info=True)
            raise ConfigReloadError(f"Config reload failed: {e}") from e

    def start_watching(self) -> None:
        """Start automatic file watching.

        Monitors config file for changes and reloads automatically.

        Raises:
            ConfigReloadError: If watching already started
        """
        if not self.auto_reload:
            logger.warning("Auto-reload disabled, not starting file watcher")
            return

        if self._watching:
            raise ConfigReloadError("File watching already started")

        if not self.config_path.exists():
            raise ConfigReloadError(f"Config file not found: {self.config_path}")

        # Create file handler
        self._file_handler = ConfigFileHandler(
            config_path=self.config_path,
            reload_callback=self._on_file_change,
            debounce_seconds=self.debounce_seconds
        )

        # Create observer
        self._observer = Observer()
        self._observer.schedule(
            self._file_handler,
            path=str(self.config_path.parent),
            recursive=False
        )
        self._observer.start()
        self._watching = True

        logger.info(f"Started watching config file: {self.config_path}")

    def stop_watching(self) -> None:
        """Stop automatic file watching."""
        if not self._watching:
            logger.debug("File watching not active")
            return

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2.0)
            self._observer = None

        self._file_handler = None
        self._watching = False

        logger.info("Stopped watching config file")

    def is_watching(self) -> bool:
        """Check if file watching is active.

        Returns:
            True if watching, False otherwise
        """
        return self._watching

    def _on_file_change(self) -> None:
        """Internal callback for file changes."""
        try:
            self.reload_config(notify=True)
        except ConfigReloadError as e:
            logger.error(f"Auto-reload failed: {e}")

    def _emit_reload_event(
        self,
        old_config: TradingBotConfig | None,
        new_config: TradingBotConfig
    ) -> None:
        """Emit config reload event.

        Args:
            old_config: Previous config (or None if initial load)
            new_config: Newly loaded config
        """
        if not self.event_bus:
            return

        try:
            from datetime import datetime
            from src.common.event_bus import Event, EventType

            event = Event(
                type=EventType.CONFIG_CHANGED,
                timestamp=datetime.utcnow(),
                data={
                    "config_path": str(self.config_path),
                    "old_strategy_count": len(old_config.strategies) if old_config else 0,
                    "new_strategy_count": len(new_config.strategies),
                    "old_regime_count": len(old_config.regimes) if old_config else 0,
                    "new_regime_count": len(new_config.regimes),
                    "schema_version": new_config.schema_version,
                },
                source="ConfigReloader",
                metadata={"auto_reload": self.auto_reload}
            )

            self.event_bus.emit(EventType.CONFIG_CHANGED, event)
            logger.debug(f"Emitted CONFIG_CHANGED event")

        except Exception as e:
            logger.error(f"Failed to emit reload event: {e}", exc_info=True)

    def __enter__(self) -> "ConfigReloader":
        """Context manager entry."""
        if self.auto_reload:
            self.start_watching()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop_watching()
