"""Bitunix API Authentication Signer.

Handles Double SHA256 signature generation for Bitunix Futures API.
"""

import hashlib
import time
import uuid
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class BitunixSigner:
    """Signer for Bitunix API requests."""

    def __init__(self, api_key: str, api_secret: str):
        """Initialize signer.

        Args:
            api_key: Bitunix API key
            api_secret: Bitunix API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret

    def generate_signature(
        self,
        nonce: str,
        timestamp: str,
        query_params: str = "",
        body: str = ""
    ) -> str:
        """Generate double SHA256 signature for Bitunix API.

        Bitunix uses a two-step SHA256 process (NOT HMAC-SHA256):
        1. digest = SHA256(nonce + timestamp + api_key + query_params + body)
        2. sign = SHA256(digest + secret_key)

        Args:
            nonce: Random UUID string
            timestamp: Millisecond timestamp
            query_params: Sorted query parameters (no spaces)
            body: JSON body (no spaces)

        Returns:
            Hex-encoded signature string
        """
        # Step 1: Create digest from nonce + timestamp + api_key + query_params + body
        digest_input = nonce + timestamp + self.api_key + query_params + body
        digest = hashlib.sha256(digest_input.encode('utf-8')).hexdigest()

        # Step 2: Sign digest + secret_key
        sign_input = digest + self.api_secret
        sign = hashlib.sha256(sign_input.encode('utf-8')).hexdigest()

        return sign

    def build_headers(self, query_params: str = "", body: str = "") -> Dict[str, str]:
        """Build request headers with API key and signature.

        Args:
            query_params: Sorted query parameters as string (no spaces)
            body: JSON body as string (no spaces)

        Returns:
            Headers dictionary for HTTP request
        """
        # Generate nonce (random UUID without dashes)
        nonce = str(uuid.uuid4()).replace('-', '')

        # Generate timestamp in milliseconds
        timestamp = str(int(time.time() * 1000))

        # Generate signature using Bitunix double SHA256 method
        signature = self.generate_signature(nonce, timestamp, query_params, body)

        return {
            'api-key': self.api_key,
            'sign': signature,
            'nonce': nonce,
            'timestamp': timestamp,
            'Content-Type': 'application/json'
        }
