"""Bitunix HEDGE Configuration Manager.

Loads and validates API credentials and endpoints from environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class BitunixHedgeConfig:
    """Configuration for Bitunix HEDGE trading.

    Attributes:
        api_key: Bitunix API key
        api_secret: Bitunix API secret
        use_testnet: Whether to use testnet (default: True for safety)
        rest_base_url: REST API base URL
        ws_base_url: WebSocket base URL
    """
    api_key: str
    api_secret: str
    use_testnet: bool = True
    rest_base_url: str = "https://fapi.bitunix.com"
    ws_base_url: str = "wss://fapi.bitunix.com/ws"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.api_key or len(self.api_key) < 10:
            raise ValueError("Invalid Bitunix API key: must be at least 10 characters")

        if not self.api_secret or len(self.api_secret) < 10:
            raise ValueError("Invalid Bitunix API secret: must be at least 10 characters")

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate configuration settings.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate REST URL uses HTTPS
        if not self.rest_base_url.startswith("https://"):
            return False, "Invalid REST base URL: must use HTTPS"

        # Validate WebSocket URL uses WSS
        if not self.ws_base_url.startswith("wss://"):
            return False, "Invalid WebSocket base URL: must use WSS"

        return True, None

    def get_rest_url(self, endpoint: str) -> str:
        """Construct full REST API URL.

        Args:
            endpoint: API endpoint path (with or without leading slash)

        Returns:
            Complete URL
        """
        # Normalize endpoint (remove leading slash if present)
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]

        return f"{self.rest_base_url}/{endpoint}"

    def get_ws_url(self) -> str:
        """Get WebSocket URL.

        Returns:
            WebSocket URL
        """
        return self.ws_base_url

    def mask_credentials(self) -> dict:
        """Get configuration with masked credentials for logging.

        Returns:
            Dictionary with masked sensitive data
        """
        # Show first 8 and last 4 characters of API key
        masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}"

        return {
            "api_key": masked_key,
            "api_secret": "***MASKED***",
            "use_testnet": self.use_testnet,
            "rest_base_url": self.rest_base_url,
            "ws_base_url": self.ws_base_url
        }

    @classmethod
    def from_env(cls) -> "BitunixHedgeConfig":
        """Load configuration from environment variables.

        Required environment variables:
            BITUNIX_API_KEY: API key
            BITUNIX_API_SECRET: API secret

        Optional environment variables:
            BITUNIX_USE_TESTNET: Whether to use testnet (default: true)

        Returns:
            BitunixHedgeConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        api_key = os.getenv("BITUNIX_API_KEY")
        api_secret = os.getenv("BITUNIX_API_SECRET")

        if not api_key:
            raise ValueError("BITUNIX_API_KEY environment variable not set")

        if not api_secret:
            raise ValueError("BITUNIX_API_SECRET environment variable not set")

        # Parse testnet flag (default True for safety)
        use_testnet_str = os.getenv("BITUNIX_USE_TESTNET", "true").lower()
        use_testnet = use_testnet_str in ("true", "1", "yes", "on")

        return cls(
            api_key=api_key,
            api_secret=api_secret,
            use_testnet=use_testnet
        )
