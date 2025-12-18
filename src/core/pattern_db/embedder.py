"""Pattern Embedder for Vector Representation.

Converts OHLC patterns to fixed-size vectors for Qdrant storage and similarity search.
Uses a simple but effective approach: normalized OHLC flattened + statistical features.
"""

import logging
from typing import Optional

import numpy as np

from .extractor import Pattern

logger = logging.getLogger(__name__)


class PatternEmbedder:
    """Converts trading patterns to vector embeddings.

    Uses a combination of:
    1. Flattened normalized OHLC data (captures pattern shape)
    2. Statistical features (volatility, trend, momentum)
    3. Volume features

    Total vector dimension = window_size * 4 + num_features
    For window_size=20: 20*4 + 16 = 96 dimensions
    """

    def __init__(self, window_size: int = 20, include_volume: bool = True):
        """Initialize embedder.

        Args:
            window_size: Expected window size of patterns
            include_volume: Whether to include volume features
        """
        self.window_size = window_size
        self.include_volume = include_volume

        # Calculate embedding dimension
        # OHLC: window_size * 4
        # Features: 16 statistical features
        self.num_features = 16
        self.embedding_dim = window_size * 4 + self.num_features

        logger.info(f"PatternEmbedder initialized: dim={self.embedding_dim}")

    def embed(self, pattern: Pattern) -> np.ndarray:
        """Convert pattern to vector embedding.

        Args:
            pattern: Pattern object

        Returns:
            Vector embedding of shape (embedding_dim,)
        """
        if pattern.window_size != self.window_size:
            logger.warning(
                f"Pattern window size mismatch: {pattern.window_size} != {self.window_size}"
            )

        # 1. Flatten normalized OHLC (shape: window_size * 4)
        ohlc_flat = pattern.ohlc_normalized.flatten()

        # Pad or truncate if needed
        expected_ohlc_dim = self.window_size * 4
        if len(ohlc_flat) < expected_ohlc_dim:
            ohlc_flat = np.pad(ohlc_flat, (0, expected_ohlc_dim - len(ohlc_flat)))
        elif len(ohlc_flat) > expected_ohlc_dim:
            ohlc_flat = ohlc_flat[:expected_ohlc_dim]

        # 2. Extract statistical features
        features = self._extract_features(pattern)

        # 3. Combine into single vector
        embedding = np.concatenate([ohlc_flat, features])

        # 4. L2 normalize for cosine similarity
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding.astype(np.float32)

    def _extract_features(self, pattern: Pattern) -> np.ndarray:
        """Extract statistical features from pattern.

        Args:
            pattern: Pattern object

        Returns:
            Feature vector of shape (num_features,)
        """
        closes = np.array(pattern.close_prices)
        opens = np.array(pattern.open_prices)
        highs = np.array(pattern.high_prices)
        lows = np.array(pattern.low_prices)
        volumes = np.array(pattern.volumes)

        features = []

        # 1. Price change (overall trend)
        features.append(pattern.price_change_pct / 10)  # Scale down

        # 2. Volatility
        features.append(pattern.volatility * 100)  # Scale up

        # 3. Body ratio (close-open vs high-low range)
        ranges = highs - lows
        bodies = np.abs(closes - opens)
        body_ratios = np.where(ranges > 0, bodies / ranges, 0)
        features.append(np.mean(body_ratios))

        # 4. Upper/lower shadow ratios
        upper_shadows = highs - np.maximum(closes, opens)
        lower_shadows = np.minimum(closes, opens) - lows
        features.append(np.mean(np.where(ranges > 0, upper_shadows / ranges, 0)))
        features.append(np.mean(np.where(ranges > 0, lower_shadows / ranges, 0)))

        # 5. Trend consistency (% of bars in trend direction)
        if pattern.trend_direction == "up":
            trend_consistent = np.sum(closes > opens) / len(closes)
        elif pattern.trend_direction == "down":
            trend_consistent = np.sum(closes < opens) / len(closes)
        else:
            trend_consistent = 0.5
        features.append(trend_consistent)

        # 6. Momentum (rate of change in second half vs first half)
        half = len(closes) // 2
        if half > 0:
            first_change = (closes[half] - closes[0]) / closes[0] if closes[0] > 0 else 0
            second_change = (closes[-1] - closes[half]) / closes[half] if closes[half] > 0 else 0
            momentum = second_change - first_change
        else:
            momentum = 0
        features.append(momentum * 10)

        # 7. High-low range expansion (increasing volatility?)
        if half > 0:
            range_first = np.mean(highs[:half] - lows[:half])
            range_second = np.mean(highs[half:] - lows[half:])
            range_expansion = (range_second - range_first) / range_first if range_first > 0 else 0
        else:
            range_expansion = 0
        features.append(range_expansion)

        # 8. Volume features
        if self.include_volume and np.sum(volumes) > 0:
            # Volume trend
            if half > 0:
                vol_first = np.mean(volumes[:half])
                vol_second = np.mean(volumes[half:])
                vol_change = (vol_second - vol_first) / vol_first if vol_first > 0 else 0
            else:
                vol_change = 0
            features.append(vol_change)

            # Volume-price correlation
            vol_normalized = (volumes - np.mean(volumes)) / (np.std(volumes) + 1e-8)
            price_normalized = (closes - np.mean(closes)) / (np.std(closes) + 1e-8)
            vol_price_corr = np.corrcoef(vol_normalized, price_normalized)[0, 1]
            features.append(vol_price_corr if not np.isnan(vol_price_corr) else 0)
        else:
            features.extend([0, 0])

        # 9. Pattern shape features (using simple statistics on normalized data)
        ohlc_norm = pattern.ohlc_normalized
        features.append(np.mean(ohlc_norm))  # Mean level
        features.append(np.std(ohlc_norm))  # Dispersion
        features.append(np.max(ohlc_norm) - np.min(ohlc_norm))  # Range

        # 10. Trend linearity (R² of linear fit)
        x = np.arange(len(closes))
        try:
            coeffs = np.polyfit(x, closes, 1)
            predicted = np.polyval(coeffs, x)
            ss_res = np.sum((closes - predicted) ** 2)
            ss_tot = np.sum((closes - np.mean(closes)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        except:
            r_squared = 0
        features.append(r_squared)

        # 11. Trend direction encoding
        trend_encoding = {"up": 1.0, "down": -1.0, "sideways": 0.0}
        features.append(trend_encoding.get(pattern.trend_direction, 0))

        # Ensure we have exactly num_features
        while len(features) < self.num_features:
            features.append(0)

        return np.array(features[:self.num_features], dtype=np.float32)

    def embed_batch(self, patterns: list[Pattern]) -> np.ndarray:
        """Embed multiple patterns.

        Args:
            patterns: List of Pattern objects

        Returns:
            Array of shape (n_patterns, embedding_dim)
        """
        embeddings = [self.embed(p) for p in patterns]
        return np.array(embeddings)

    def get_embedding_dim(self) -> int:
        """Get embedding dimension.

        Returns:
            Embedding dimension
        """
        return self.embedding_dim
