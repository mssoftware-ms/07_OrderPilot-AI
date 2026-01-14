"""
Intensity Normalization Functions

Provides different normalization strategies for heatmap intensity scaling.
"""

import math
from enum import Enum
from typing import List, Tuple

import numpy as np


class NormalizationType(str, Enum):
    """Supported normalization types."""

    LINEAR = "linear"
    SQRT = "sqrt"
    LOG = "log"
    LOG10 = "log10"


def normalize_intensity(
    values: np.ndarray,
    norm_type: NormalizationType = NormalizationType.SQRT,
    clip_min: float = 0.0,
    clip_max: float = 1.0,
    epsilon: float = 1e-10,
) -> np.ndarray:
    """
    Normalize intensity values to [clip_min, clip_max] range.

    Args:
        values: Input array of intensity values
        norm_type: Normalization method
        clip_min: Minimum output value
        clip_max: Maximum output value
        epsilon: Small value to avoid log(0)

    Returns:
        Normalized array with same shape as input
    """
    if values.size == 0:
        return values

    # Handle all-zero case
    if np.all(values == 0):
        return np.zeros_like(values, dtype=float)

    # Apply transformation
    if norm_type == NormalizationType.LINEAR:
        transformed = values
    elif norm_type == NormalizationType.SQRT:
        transformed = np.sqrt(values + epsilon)
    elif norm_type == NormalizationType.LOG:
        transformed = np.log(values + epsilon)
    elif norm_type == NormalizationType.LOG10:
        transformed = np.log10(values + epsilon)
    else:
        raise ValueError(f"Unknown normalization type: {norm_type}")

    # Min-max scaling to [clip_min, clip_max]
    min_val = transformed.min()
    max_val = transformed.max()

    if max_val - min_val < epsilon:
        # All values are the same after transformation
        return np.full_like(values, clip_min, dtype=float)

    normalized = (transformed - min_val) / (max_val - min_val)
    scaled = normalized * (clip_max - clip_min) + clip_min

    return scaled


def apply_time_decay(
    values: np.ndarray,
    timestamps_ms: np.ndarray,
    current_time_ms: int,
    decay_half_life_ms: int,
) -> np.ndarray:
    """
    Apply exponential time decay to intensity values.

    Intensity decays exponentially: intensity * exp(-λ * age)
    where λ = ln(2) / half_life

    Args:
        values: Intensity values
        timestamps_ms: Event timestamps in milliseconds
        current_time_ms: Current time in milliseconds
        decay_half_life_ms: Half-life for decay in milliseconds

    Returns:
        Decayed intensity values
    """
    if decay_half_life_ms <= 0:
        return values

    # Calculate age in milliseconds
    ages_ms = current_time_ms - timestamps_ms

    # Decay constant
    lambda_decay = math.log(2) / decay_half_life_ms

    # Apply exponential decay
    decay_factor = np.exp(-lambda_decay * ages_ms)

    return values * decay_factor


def smooth_grid(
    grid: np.ndarray,
    kernel_size: int = 3,
    sigma: float = 1.0,
) -> np.ndarray:
    """
    Apply Gaussian smoothing to grid (optional post-processing).

    Args:
        grid: 2D grid array (rows × cols)
        kernel_size: Size of Gaussian kernel (odd number)
        sigma: Standard deviation for Gaussian

    Returns:
        Smoothed grid
    """
    try:
        from scipy.ndimage import gaussian_filter
        return gaussian_filter(grid, sigma=sigma, truncate=kernel_size)
    except ImportError:
        # Fallback to simple box blur if scipy not available
        return _box_blur(grid, kernel_size)


def _box_blur(grid: np.ndarray, size: int) -> np.ndarray:
    """Simple box blur as scipy fallback."""
    from numpy.lib.stride_tricks import sliding_window_view

    if size <= 1:
        return grid

    # Pad edges
    pad_width = size // 2
    padded = np.pad(grid, pad_width, mode="edge")

    # Apply sliding window average
    windows = sliding_window_view(padded, (size, size))
    blurred = windows.mean(axis=(2, 3))

    return blurred


def create_color_palette(
    name: str = "hot",
    levels: int = 256,
) -> List[Tuple[int, int, int, int]]:
    """
    Create color palette for heatmap rendering.

    Args:
        name: Palette name ('hot', 'cool', 'viridis', 'plasma')
        levels: Number of color levels

    Returns:
        List of (r, g, b, a) tuples, where each component is 0-255
    """
    if name == "hot":
        # Red → Orange → Yellow
        palette = []
        for i in range(levels):
            t = i / (levels - 1)
            if t < 0.33:
                # Dark red → red
                r = int(255 * (t / 0.33))
                g = 0
                b = 0
            elif t < 0.66:
                # Red → orange
                r = 255
                g = int(255 * ((t - 0.33) / 0.33))
                b = 0
            else:
                # Orange → yellow
                r = 255
                g = 255
                b = int(255 * ((t - 0.66) / 0.34))

            a = int(255 * min(1.0, t * 1.5))  # Alpha ramps up
            palette.append((r, g, b, a))

        return palette

    elif name == "cool":
        # Blue → Cyan → White
        palette = []
        for i in range(levels):
            t = i / (levels - 1)
            r = int(255 * t)
            g = int(255 * t)
            b = 255
            a = int(255 * min(1.0, t * 1.5))
            palette.append((r, g, b, a))

        return palette

    elif name == "viridis":
        # Perceptually uniform palette (approximation)
        palette = []
        for i in range(levels):
            t = i / (levels - 1)
            r = int(255 * (0.267 + 0.575 * t))
            g = int(255 * (0.005 + 0.907 * t))
            b = int(255 * (0.329 - 0.180 * t))
            a = int(255 * min(1.0, t * 1.5))
            palette.append((r, g, b, a))

        return palette

    elif name == "plasma":
        # Another perceptually uniform palette (approximation)
        palette = []
        for i in range(levels):
            t = i / (levels - 1)
            r = int(255 * (0.050 + 0.950 * t))
            g = int(255 * (0.030 + 0.790 * t - 0.360 * t * t))
            b = int(255 * (0.528 - 0.530 * t))
            a = int(255 * min(1.0, t * 1.5))
            palette.append((r, g, b, a))

        return palette

    else:
        raise ValueError(f"Unknown palette: {name}")


# Example usage
if __name__ == "__main__":
    # Test normalization
    values = np.array([0, 1, 4, 9, 16, 25, 100])

    print("Linear:", normalize_intensity(values, NormalizationType.LINEAR))
    print("Sqrt:", normalize_intensity(values, NormalizationType.SQRT))
    print("Log:", normalize_intensity(values, NormalizationType.LOG))

    # Test decay
    timestamps = np.array([1000, 2000, 3000, 4000, 5000])
    intensities = np.array([10.0, 10.0, 10.0, 10.0, 10.0])
    current_time = 5000
    half_life = 1000  # 1 second

    decayed = apply_time_decay(intensities, timestamps, current_time, half_life)
    print("\nTime decay:", decayed)

    # Test palette
    palette = create_color_palette("hot", levels=10)
    print("\nHot palette (first 10):")
    for color in palette:
        print(f"  rgba{color}")
