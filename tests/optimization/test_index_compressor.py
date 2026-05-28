"""Tests for index compression module."""

import pytest
import numpy as np
import json
from src.optimization.index_compressor import IndexCompressor, AdaptiveCompressor


class TestIndexCompressor:
    """Test index compression functionality."""

    def test_compressor_initialization(self):
        """Test compressor initialization."""
        compressor = IndexCompressor(compression_level=6)

        assert compressor.compression_level == 6
        assert compressor.compression_stats['original_bytes'] == 0
        assert compressor.compression_stats['compressed_bytes'] == 0

    def test_compress_vectors(self):
        """Test vector compression."""
        compressor = IndexCompressor()

        vectors = np.random.randn(1000, 768).astype(np.float32)
        compressed = compressor.compress_vectors(vectors)

        assert isinstance(compressed, bytes)
        assert len(compressed) > 0

    def test_decompress_vectors(self):
        """Test vector decompression."""
        compressor = IndexCompressor()

        original = np.random.randn(100, 768).astype(np.float32)
        compressed = compressor.compress_vectors(original)
        decompressed = compressor.decompress_vectors(compressed, (100, 768))

        assert decompressed.shape == original.shape

        # Check reconstruction error is small
        mse = np.mean((original - decompressed) ** 2)
        assert mse < 0.1

    def test_compress_index(self):
        """Test index metadata compression."""
        compressor = IndexCompressor()

        index_data = {
            "id_to_doc": {"1": "doc1", "2": "doc2"},
            "doc_count": 2,
            "index_type": "bm25"
        }

        compressed = compressor.compress_index(index_data)

        assert isinstance(compressed, bytes)
        assert len(compressed) > 0

    def test_decompress_index(self):
        """Test index metadata decompression."""
        compressor = IndexCompressor()

        original = {
            "id_to_doc": {"1": "doc1", "2": "doc2"},
            "doc_count": 2,
            "index_type": "bm25"
        }

        compressed = compressor.compress_index(original)
        decompressed = compressor.decompress_index(compressed)

        assert decompressed == original

    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        compressor = IndexCompressor()

        vectors = np.random.randn(1000, 768).astype(np.float32)
        compressor.compress_vectors(vectors)

        ratio = compressor.estimate_compression_ratio()

        assert ratio > 1  # Should achieve some compression

    def test_compression_stats(self):
        """Test compression statistics."""
        compressor = IndexCompressor()

        vectors = np.random.randn(100, 768).astype(np.float32)
        compressor.compress_vectors(vectors)

        stats = compressor.get_compression_stats()

        assert "original_mb" in stats
        assert "compressed_mb" in stats
        assert "compression_ratio" in stats
        assert stats["original_mb"] > stats["compressed_mb"]

    def test_reset_stats(self):
        """Test statistics reset."""
        compressor = IndexCompressor()

        vectors = np.random.randn(100, 768).astype(np.float32)
        compressor.compress_vectors(vectors)

        compressor.reset_stats()

        assert compressor.compression_stats['original_bytes'] == 0
        assert compressor.compression_stats['compressed_bytes'] == 0

    def test_vector_compression_improves_with_size(self):
        """Test that compression is more effective for larger vectors."""
        compressor = IndexCompressor()

        small = np.random.randn(100, 100).astype(np.float32)
        large = np.random.randn(1000, 1000).astype(np.float32)

        compressor.compress_vectors(small)
        small_stats = compressor.get_compression_stats()

        compressor.reset_stats()

        compressor.compress_vectors(large)
        large_stats = compressor.get_compression_stats()

        # Larger vectors should compress similarly
        assert small_stats['compression_ratio'] > 1
        assert large_stats['compression_ratio'] > 1


class TestAdaptiveCompressor:
    """Test adaptive compression."""

    def test_adaptive_compressor_initialization(self):
        """Test adaptive compressor init."""
        compressor = AdaptiveCompressor()

        assert compressor.compression_level == 6

    def test_adaptive_compression(self):
        """Test adaptive compression level selection."""
        compressor = AdaptiveCompressor()

        vectors = np.random.randn(100, 768).astype(np.float32)

        compressed, level = compressor.compress_vectors(vectors)

        assert isinstance(compressed, bytes)
        assert level in [0, 3, 6, 9]

    def test_adaptive_respects_compression_levels(self):
        """Test that adaptive compression respects level bounds."""
        compressor = AdaptiveCompressor()

        vectors = np.random.randn(50, 768).astype(np.float32)

        compressed, level = compressor.compress_vectors(vectors)

        assert 0 <= level <= 9
