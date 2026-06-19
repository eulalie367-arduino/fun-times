"""Vector quantization for memory-efficient storage and retrieval.

Implements 8-bit quantization for ~4x compression with minimal accuracy loss.
"""

import numpy as np
from typing import Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)


class VectorQuantizer:
    """Quantize vectors to 8-bit representation for 4x compression."""

    def __init__(self, dimension: int = 768):
        """Initialize quantizer.

        Args:
            dimension: Vector dimension (default 768 for most embeddings)
        """
        self.dimension = dimension
        self.scale_factors: Optional[np.ndarray] = None
        self.min_values: Optional[np.ndarray] = None

    def calibrate(self, vectors: np.ndarray) -> None:
        """Calibrate quantizer from a sample of vectors.

        Args:
            vectors: Array of shape (n_vectors, dimension)
        """
        self.min_values = vectors.min(axis=0)
        max_values = vectors.max(axis=0)

        # Compute scale factors for uint8 range [0, 255]
        self.scale_factors = (max_values - self.min_values) / 255.0

        # Avoid division by zero
        self.scale_factors[self.scale_factors == 0] = 1.0

        logger.info(f"Quantizer calibrated on {vectors.shape[0]} vectors")

    def quantize(self, vectors: np.ndarray) -> np.ndarray:
        """Quantize float vectors to uint8.

        Args:
            vectors: Array of shape (n_vectors, dimension) with float values

        Returns:
            Quantized vectors as uint8 array
        """
        if self.min_values is None or self.scale_factors is None:
            raise ValueError("Quantizer not calibrated. Call calibrate() first.")

        # Normalize to [0, 255] range
        normalized = (vectors - self.min_values) / self.scale_factors
        normalized = np.clip(normalized, 0, 255)

        return normalized.astype(np.uint8)

    def dequantize(self, quantized: np.ndarray) -> np.ndarray:
        """Convert quantized vectors back to float.

        Args:
            quantized: Array of uint8 vectors

        Returns:
            Reconstructed float vectors
        """
        if self.min_values is None or self.scale_factors is None:
            raise ValueError("Quantizer not calibrated.")

        dequantized = quantized.astype(np.float32) * self.scale_factors + self.min_values
        return dequantized

    def memory_savings(self, n_vectors: int) -> Tuple[float, float, float]:
        """Calculate memory savings from quantization.

        Args:
            n_vectors: Number of vectors

        Returns:
            (original_mb, quantized_mb, compression_ratio)
        """
        original_bytes = n_vectors * self.dimension * 4  # float32
        quantized_bytes = n_vectors * self.dimension * 1  # uint8

        original_mb = original_bytes / (1024 * 1024)
        quantized_mb = quantized_bytes / (1024 * 1024)
        ratio = original_mb / quantized_mb if quantized_mb > 0 else 0

        return original_mb, quantized_mb, ratio

    @staticmethod
    def calculate_accuracy_loss(original: np.ndarray, quantized: np.ndarray) -> float:
        """Calculate MSE between original and quantized vectors.

        Args:
            original: Original float vectors
            quantized: Reconstructed float vectors

        Returns:
            Mean squared error
        """
        mse = np.mean((original - quantized) ** 2)
        return float(mse)


class AdaptiveQuantizer(VectorQuantizer):
    """Adaptive quantizer that maintains per-dimension scale factors."""

    def __init__(self, dimension: int = 768, bits: int = 8):
        """Initialize adaptive quantizer.

        Args:
            dimension: Vector dimension
            bits: Quantization bits (8 for uint8, 4 for uint4, etc.)
        """
        super().__init__(dimension)
        self.bits = bits
        self.max_value = (1 << bits) - 1

    def quantize(self, vectors: np.ndarray) -> np.ndarray:
        """Quantize with bit-depth awareness."""
        if self.min_values is None or self.scale_factors is None:
            raise ValueError("Quantizer not calibrated.")

        # Scale to [0, max_value] range
        normalized = (vectors - self.min_values) / self.scale_factors
        normalized = np.clip(normalized, 0, self.max_value)

        return normalized.astype(np.uint8)

    def dequantize(self, quantized: np.ndarray) -> np.ndarray:
        """Dequantize with bit-depth awareness."""
        if self.min_values is None or self.scale_factors is None:
            raise ValueError("Quantizer not calibrated.")

        dequantized = quantized.astype(np.float32) * self.scale_factors + self.min_values
        return dequantized
