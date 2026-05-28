"""Index compression for space-efficient storage.

Implements compression strategies for vector indices and search indices.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import logging
import zlib
import json

logger = logging.getLogger(__name__)


class IndexCompressor:
    """Compress indices for reduced storage footprint."""

    def __init__(self, compression_level: int = 6):
        """Initialize compressor.

        Args:
            compression_level: zlib compression level (0-9, default 6)
        """
        self.compression_level = compression_level
        self.compression_stats = {
            'original_bytes': 0,
            'compressed_bytes': 0,
            'items_compressed': 0
        }

    def compress_vectors(self, vectors: np.ndarray) -> bytes:
        """Compress vector array using delta encoding + zlib.

        Args:
            vectors: Array of vectors to compress

        Returns:
            Compressed bytes
        """
        # Apply delta encoding for better compression
        if vectors.shape[0] > 1:
            deltas = np.diff(vectors.astype(np.float32), axis=0)
            # Prepend first vector
            encoded = np.vstack([vectors[0:1], deltas])
        else:
            encoded = vectors.astype(np.float32)

        # Convert to bytes
        data_bytes = encoded.tobytes()

        # Compress
        compressed = zlib.compress(data_bytes, self.compression_level)

        # Track stats
        self.compression_stats['original_bytes'] += len(data_bytes)
        self.compression_stats['compressed_bytes'] += len(compressed)
        self.compression_stats['items_compressed'] += 1

        return compressed

    def decompress_vectors(
        self,
        compressed: bytes,
        shape: Tuple[int, int],
        dtype: np.dtype = np.float32
    ) -> np.ndarray:
        """Decompress vector array.

        Args:
            compressed: Compressed bytes
            shape: Expected shape of decompressed array
            dtype: Data type

        Returns:
            Decompressed vector array
        """
        # Decompress
        data_bytes = zlib.decompress(compressed)

        # Convert from bytes
        decoded = np.frombuffer(data_bytes, dtype=dtype).reshape(shape)

        # Reverse delta encoding
        if decoded.shape[0] > 1:
            reconstructed = np.zeros_like(decoded)
            reconstructed[0] = decoded[0]
            for i in range(1, decoded.shape[0]):
                reconstructed[i] = reconstructed[i - 1] + decoded[i]
            return reconstructed
        else:
            return decoded

    def compress_index(self, index_data: Dict[str, Any]) -> bytes:
        """Compress index metadata dictionary.

        Args:
            index_data: Index dictionary

        Returns:
            Compressed JSON bytes
        """
        json_str = json.dumps(index_data)
        json_bytes = json_str.encode('utf-8')

        compressed = zlib.compress(json_bytes, self.compression_level)

        self.compression_stats['original_bytes'] += len(json_bytes)
        self.compression_stats['compressed_bytes'] += len(compressed)

        return compressed

    def decompress_index(self, compressed: bytes) -> Dict[str, Any]:
        """Decompress index metadata.

        Args:
            compressed: Compressed index bytes

        Returns:
            Index dictionary
        """
        json_bytes = zlib.decompress(compressed)
        json_str = json_bytes.decode('utf-8')
        return json.loads(json_str)

    def estimate_compression_ratio(self) -> float:
        """Get current compression ratio.

        Returns:
            Ratio of original to compressed size
        """
        if self.compression_stats['compressed_bytes'] == 0:
            return 1.0

        ratio = (
            self.compression_stats['original_bytes']
            / self.compression_stats['compressed_bytes']
        )

        return ratio

    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics.

        Returns:
            Dictionary with compression metrics
        """
        original_mb = self.compression_stats['original_bytes'] / (1024 * 1024)
        compressed_mb = self.compression_stats['compressed_bytes'] / (1024 * 1024)

        return {
            'original_mb': original_mb,
            'compressed_mb': compressed_mb,
            'items_compressed': self.compression_stats['items_compressed'],
            'compression_ratio': self.estimate_compression_ratio(),
            'savings_mb': original_mb - compressed_mb
        }

    def reset_stats(self):
        """Reset compression statistics."""
        self.compression_stats = {
            'original_bytes': 0,
            'compressed_bytes': 0,
            'items_compressed': 0
        }


class AdaptiveCompressor(IndexCompressor):
    """Adaptive compression that adjusts compression level per item."""

    def compress_vectors(self, vectors: np.ndarray) -> Tuple[bytes, int]:
        """Compress vectors with adaptive compression level.

        Args:
            vectors: Array of vectors

        Returns:
            (compressed_bytes, used_compression_level)
        """
        # Try different compression levels and pick best
        best_compressed = None
        best_level = 0
        best_size = float('inf')

        for level in [0, 3, 6, 9]:
            # Temporarily set level
            self.compression_level = level
            compressed = super().compress_vectors(vectors)

            if len(compressed) < best_size:
                best_size = len(compressed)
                best_compressed = compressed
                best_level = level

        # Reset to default
        self.compression_level = 6

        logger.debug(
            f"Adaptive compression selected level {best_level} "
            f"({best_size} bytes)"
        )

        return best_compressed, best_level
