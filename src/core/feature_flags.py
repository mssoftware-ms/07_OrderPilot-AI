"""Feature Flags Manager for OrderPilot-AI.

Task 5.24: Release with feature flags and safe defaults.

Manages feature enablement across the application with safe defaults.
All features disabled by default for safety.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FeatureFlags:
    """Feature flags manager.

    Loads feature flags from config/feature_flags.json and provides
    safe access with default-off behavior.
    """

    _instance: Optional['FeatureFlags'] = None
    _flags: Dict[str, Any] = {}

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_flags()
        return cls._instance

    def _load_flags(self):
        """Load feature flags from JSON file."""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "feature_flags.json"

            if not config_path.exists():
                logger.warning(
                    f"Feature flags file not found: {config_path}. "
                    f"All features will be DISABLED by default."
                )
                self._flags = {}
                return

            with open(config_path, 'r') as f:
                self._flags = json.load(f)

            logger.info(f"Feature flags loaded from {config_path}")

        except Exception as e:
            logger.error(f"Failed to load feature flags: {e}. All features DISABLED.")
            self._flags = {}

    def is_enabled(self, feature_path: str, default: bool = False) -> bool:
        """Check if a feature is enabled.

        Args:
            feature_path: Dot-separated path to feature (e.g., "bitunix_hedge.enabled")
            default: Default value if feature not found (default: False for safety)

        Returns:
            True if feature enabled, False otherwise

        Example:
            >>> flags = FeatureFlags()
            >>> flags.is_enabled("bitunix_hedge.enabled")
            False  # Safe default
            >>> flags.is_enabled("bitunix_hedge.sub_features.kill_switch.enabled")
            True  # If configured in JSON
        """
        parts = feature_path.split('.')
        current = self._flags

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                logger.debug(
                    f"Feature flag not found: {feature_path}, "
                    f"using default: {default}"
                )
                return default

        if isinstance(current, bool):
            return current
        else:
            logger.warning(
                f"Feature flag {feature_path} is not a boolean: {current}, "
                f"using default: {default}"
            )
            return default

    def get_value(self, feature_path: str, default: Any = None) -> Any:
        """Get feature flag value (for non-boolean flags).

        Args:
            feature_path: Dot-separated path to feature
            default: Default value if not found

        Returns:
            Feature value or default

        Example:
            >>> flags.get_value("bitunix_hedge.safety_limits.max_leverage", 20)
            20
        """
        parts = feature_path.split('.')
        current = self._flags

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default

        return current if current is not None else default

    def require_enabled(self, feature_path: str, feature_name: str = None):
        """Require feature to be enabled (raises exception if not).

        Args:
            feature_path: Dot-separated path to feature
            feature_name: Human-readable feature name (for error message)

        Raises:
            RuntimeError: If feature is not enabled
        """
        if not self.is_enabled(feature_path):
            name = feature_name or feature_path
            raise RuntimeError(
                f"Feature '{name}' is not enabled. "
                f"Enable it in config/feature_flags.json to use this functionality."
            )

    def get_safety_limits(self) -> Dict[str, Any]:
        """Get Bitunix HEDGE safety limits.

        Returns:
            Dictionary with safety limits (max_notional_usd, max_leverage, etc.)
        """
        return self.get_value("bitunix_hedge.safety_limits", {
            "max_notional_usd": 10000.0,
            "max_leverage": 20,
            "max_position_size": 1.0
        })

    def get_rate_limits(self) -> Dict[str, float]:
        """Get Bitunix HEDGE rate limits.

        Returns:
            Dictionary with rate limits (per second)
        """
        return self.get_value("bitunix_hedge.rate_limits", {
            "place_order_per_sec": 8.0,
            "modify_order_per_sec": 4.0,
            "cancel_order_per_sec": 4.0,
            "tpsl_modify_per_sec": 2.0
        })

    def is_bitunix_hedge_enabled(self) -> bool:
        """Check if Bitunix HEDGE feature is enabled.

        Returns:
            True if enabled, False otherwise (safe default)
        """
        return self.is_enabled("bitunix_hedge.enabled", default=False)

    def is_adaptive_limit_enabled(self) -> bool:
        """Check if adaptive limit entry is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self.is_enabled(
            "bitunix_hedge.sub_features.adaptive_limit_entry.enabled",
            default=False
        )

    def is_trailing_stop_enabled(self) -> bool:
        """Check if trailing stop is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self.is_enabled(
            "bitunix_hedge.sub_features.trailing_stop.enabled",
            default=False
        )


# Global instance
feature_flags = FeatureFlags()
