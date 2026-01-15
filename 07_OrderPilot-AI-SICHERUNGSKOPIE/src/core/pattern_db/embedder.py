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
        closes, opens, highs, lows, volumes = self._pattern_arrays(pattern)
        features: list[float] = []

        features.append(pattern.price_change_pct / 10)
        features.append(pattern.volatility * 100)

        ranges, bodies = self._ranges_and_bodies(highs, lows, closes, opens)
        features.append(np.mean(np.where(ranges > 0, bodies / ranges, 0)))

        upper_shadows, lower_shadows = self._shadows(highs, lows, closes, opens)
        features.append(np.mean(np.where(ranges > 0, upper_shadows / ranges, 0)))
        features.append(np.mean(np.where(ranges > 0, lower_shadows / ranges, 0)))

        features.append(self._trend_consistency(pattern.trend_direction, closes, opens))

        half = len(closes) // 2
        features.append(self._momentum(closes, half) * 10)
        features.append(self._range_expansion(highs, lows, half))

        features.extend(self._volume_features(volumes, closes, half))

        features.extend(self._shape_features(pattern.ohlc_normalized))
        features.append(self._trend_linearity(closes))
        features.append(self._trend_encoding(pattern.trend_direction))

        while len(features) < self.num_features:
            features.append(0)

        return np.array(features[:self.num_features], dtype=np.float32)

    def _pattern_arrays(self, pattern: Pattern):
        closes = np.array(pattern.close_prices)
        opens = np.array(pattern.open_prices)
        highs = np.array(pattern.high_prices)
        lows = np.array(pattern.low_prices)
        volumes = np.array(pattern.volumes)
        return closes, opens, highs, lows, volumes

    def _ranges_and_bodies(self, highs, lows, closes, opens):
        ranges = highs - lows
        bodies = np.abs(closes - opens)
        return ranges, bodies

    def _shadows(self, highs, lows, closes, opens):
        upper_shadows = highs - np.maximum(closes, opens)
        lower_shadows = np.minimum(closes, opens) - lows
        return upper_shadows, lower_shadows

    def _trend_consistency(self, trend_direction: str, closes, opens) -> float:
        if trend_direction == "up":
            return np.sum(closes > opens) / len(closes)
        if trend_direction == "down":
            return np.sum(closes < opens) / len(closes)
        return 0.5

    def _momentum(self, closes, half: int) -> float:
        if half <= 0:
            return 0
        first_change = (closes[half] - closes[0]) / closes[0] if closes[0] > 0 else 0
        second_change = (closes[-1] - closes[half]) / closes[half] if closes[half] > 0 else 0
        return second_change - first_change

    def _range_expansion(self, highs, lows, half: int) -> float:
        if half <= 0:
            return 0
        range_first = np.mean(highs[:half] - lows[:half])
        range_second = np.mean(highs[half:] - lows[half:])
        return (range_second - range_first) / range_first if range_first > 0 else 0

    def _volume_features(self, volumes, closes, half: int) -> list[float]:
        if not self.include_volume or np.sum(volumes) <= 0:
            return [0, 0]
        if half > 0:
            vol_first = np.mean(volumes[:half])
            vol_second = np.mean(volumes[half:])
            vol_change = (vol_second - vol_first) / vol_first if vol_first > 0 else 0
        else:
            vol_change = 0
        vol_normalized = (volumes - np.mean(volumes)) / (np.std(volumes) + 1e-8)
        price_normalized = (closes - np.mean(closes)) / (np.std(closes) + 1e-8)
        vol_price_corr = np.corrcoef(vol_normalized, price_normalized)[0, 1]
        return [vol_change, vol_price_corr if not np.isnan(vol_price_corr) else 0]

    def _shape_features(self, ohlc_norm: np.ndarray) -> list[float]:
        return [
            np.mean(ohlc_norm),
            np.std(ohlc_norm),
            np.max(ohlc_norm) - np.min(ohlc_norm),
        ]

    def _trend_linearity(self, closes) -> float:
        x = np.arange(len(closes))
        try:
            coeffs = np.polyfit(x, closes, 1)
            predicted = np.polyval(coeffs, x)
            ss_res = np.sum((closes - predicted) ** 2)
            ss_tot = np.sum((closes - np.mean(closes)) ** 2)
            return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        except Exception:
            return 0

    def _trend_encoding(self, trend_direction: str) -> float:
        trend_encoding = {"up": 1.0, "down": -1.0, "sideways": 0.0}
        return trend_encoding.get(trend_direction, 0)

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
