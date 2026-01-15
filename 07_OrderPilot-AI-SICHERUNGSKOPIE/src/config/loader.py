"""Configuration management for OrderPilot-AI Trading Application.

Manages trading profiles, broker credentials, API keys, and runtime settings.
Uses Pydantic for validation and supports YAML/JSON file formats.

REFACTORED: Split into multiple files to meet 600 LOC limit.
- config_types.py: Enums and sub-configuration models
- profile_config.py: ProfileConfig with validators and factory methods
- loader.py: ConfigManager and AppSettings (this file)
"""

import json
import logging
import os
from pathlib import Path

import keyring
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings

# Re-export all types for backward compatibility
from .config_types import (
    AIConfig,
    AlertConfig,
    BacktestConfig,
    BrokerConfig,
    BrokerType,
    DatabaseConfig,
    ExecutionConfig,
    MarketDataProviderConfig,
    MonitoringConfig,
    TradingConfig,
    TradingEnvironment,
    TradingMode,
    UIConfig,
)
from .profile_config import ProfileConfig

logger = logging.getLogger(__name__)

# Re-export all for backward compatibility
__all__ = [
    # Enums
    "TradingEnvironment",
    "TradingMode",
    "BrokerType",
    # Config models
    "BrokerConfig",
    "DatabaseConfig",
    "MarketDataProviderConfig",
    "AIConfig",
    "TradingConfig",
    "BacktestConfig",
    "AlertConfig",
    "UIConfig",
    "MonitoringConfig",
    "ExecutionConfig",
    "ProfileConfig",
    # Settings and manager
    "AppSettings",
    "ConfigManager",
    "config_manager",
]


class AppSettings(BaseSettings):
    """Application-wide settings from environment variables."""
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",  # Allow additional fields like watchlist
    }

    app_env: str = Field(default="dev", alias="TRADING_ENV")
    app_log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    profile: str = Field(default="paper", alias="TRADING_PROFILE")
    config_dir: str = Field(default="./config", alias="CONFIG_DIR")
    watchlist: list[str] = Field(default_factory=list)


class ConfigManager:
    """Manages application configuration and profiles."""

    def __init__(self, config_dir: Path | None = None):
        """Initialize the configuration manager.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path("./config")
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.settings = AppSettings()
        self._profile_config: ProfileConfig | None = None
        self._credentials: dict[str, str] = {}

    def load_profile(self, profile_name: str | None = None) -> ProfileConfig:
        """Load a configuration profile.

        Args:
            profile_name: Name of the profile to load

        Returns:
            Loaded profile configuration
        """
        profile_name = profile_name or self.settings.profile
        profile_path = self.config_dir / f"{profile_name}.yaml"

        if profile_path.exists():
            logger.info(f"Loading profile from {profile_path}")
            with open(profile_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self._profile_config = ProfileConfig(**data)
        else:
            logger.info(f"Profile {profile_name} not found, using defaults")
            self._profile_config = ProfileConfig(profile_name=profile_name)
            self.save_profile()

        return self._profile_config

    def save_profile(self, profile: ProfileConfig | None = None) -> None:
        """Save the current profile to disk.

        Args:
            profile: Profile to save (uses current if not provided)
        """
        profile = profile or self._profile_config
        if not profile:
            raise ValueError("No profile to save")

        profile_path = self.config_dir / f"{profile.profile_name}.yaml"

        # Convert to dict for YAML serialization (enums to values)
        config_dict = profile.model_dump(mode='json')

        with open(profile_path, "w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Profile saved to {profile_path}")

    def get_credential(self, key: str, service: str = "OrderPilot-AI") -> str | None:
        """Retrieve a credential from environment variables, .env file or Windows Credential Manager.

        Priority:
        1. Check in-memory cache
        2. Check system environment variables (os.environ)
        3. Check .env file in config/secrets/
        4. Check Windows Credential Manager

        Args:
            key: Credential key (e.g., 'openai_api_key', 'alpaca_api_key')
            service: Service name for keyring

        Returns:
            Credential value or None if not found
        """
        cached = self._get_cached_credential(key)
        if cached is not None:
            return cached

        # Check system env vars (uppercase)
        env_val = os.environ.get(key.upper())
        if env_val:
            self._credentials[key] = env_val
            return env_val

        env_value = self._get_env_credential(key)
        if env_value is not None:
            return env_value

        return self._get_keyring_credential(key, service)

    def _get_cached_credential(self, key: str) -> str | None:
        return self._credentials.get(key)

    def _get_env_credential(self, key: str) -> str | None:
        env_file = self.config_dir / "secrets" / ".env"
        if not env_file.exists():
            return None

        try:
            env_key = key.upper()
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k.strip() != env_key:
                        continue
                    value = v.strip()
                    if value and not value.startswith("YOUR_") and not value.endswith("_HERE"):
                        self._credentials[key] = value
                        logger.debug(f"Credential {key} loaded from .env")
                        return value
        except Exception as e:
            logger.warning(f"Failed to read .env file: {e}")
        return None

    def _get_keyring_credential(self, key: str, service: str) -> str | None:
        try:
            value = keyring.get_password(service, key)
            if value:
                self._credentials[key] = value
                logger.debug(f"Credential {key} loaded from keyring")
            return value
        except Exception as e:
            logger.error(f"Failed to get credential {key}: {e}")
            return None

    def set_credential(self, key: str, value: str, service: str = "OrderPilot-AI") -> None:
        """Store a credential in Windows Credential Manager.

        Args:
            key: Credential key
            value: Credential value
            service: Service name for keyring
        """
        try:
            keyring.set_password(service, key, value)
            self._credentials[key] = value
            logger.info(f"Credential {key} saved to keyring")
        except Exception as e:
            logger.error(f"Failed to set credential {key}: {e}")
            raise

    def list_profiles(self) -> list[str]:
        """List available configuration profiles.

        Returns:
            List of profile names
        """
        profiles = []

        # Get all YAML and JSON files in config directory
        for file in self.config_dir.glob("*.yaml"):
            profiles.append(file.stem)
        for file in self.config_dir.glob("*.json"):
            profiles.append(file.stem)

        # Remove duplicates and return sorted list
        return sorted(list(set(profiles)))

    def export_config(self, path: Path) -> None:
        """Export current configuration (without secrets).

        Args:
            path: Path to export configuration to
        """
        from datetime import datetime

        if not self._profile_config:
            raise ValueError("No profile loaded")

        config_dict = self._profile_config.model_dump(mode='json')
        config_dict['exported_at'] = datetime.utcnow().isoformat()
        config_dict['version'] = "1.0.0"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, default=str)

        logger.info(f"Configuration exported to {path}")

    def save_watchlist(self) -> None:
        """Save watchlist to persistent storage."""
        watchlist_path = self.config_dir / "watchlist.json"

        try:
            with open(watchlist_path, "w", encoding="utf-8") as f:
                json.dump({"watchlist": self.settings.watchlist}, f, indent=2)
            logger.debug(f"Watchlist saved to {watchlist_path}")
        except Exception as e:
            logger.error(f"Failed to save watchlist: {e}")
            raise

    def load_watchlist(self) -> list[str]:
        """Load watchlist from persistent storage.

        Returns:
            List of symbols in watchlist
        """
        watchlist_path = self.config_dir / "watchlist.json"

        if not watchlist_path.exists():
            return []

        try:
            with open(watchlist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                watchlist = data.get("watchlist", [])
                self.settings.watchlist = watchlist
                logger.debug(f"Loaded {len(watchlist)} symbols from watchlist")
                return watchlist
        except Exception as e:
            logger.error(f"Failed to load watchlist: {e}")
            return []

    # --- Compatibility helpers ------------------------------------------
    def get_setting(self, key: str, default=None):
        """Return a setting from profile.market_data or AppSettings (compat layer)."""
        profile = self._profile_config or self.load_profile()
        if hasattr(profile.market_data, key):
            return getattr(profile.market_data, key)
        if hasattr(self.settings, key):
            return getattr(self.settings, key)
        return default

    @property
    def profile(self) -> ProfileConfig:
        """Get the current profile configuration."""
        if not self._profile_config:
            self.load_profile()
        return self._profile_config


# Global configuration instance
config_manager = ConfigManager()
