"""Tests for vector quantizer module."""

import pytest
import numpy as np
from src.optimization.quantizer import VectorQuantizer, AdaptiveQuantizer


class TestVectorQuantizer:
    """Test vector quantization."""

    def test_quantizer_initialization(self):
        """Test quantizer initialization."""
        quantizer = VectorQuantizer(dimension=768)
        assert quantizer.dimension == 768
        assert quantizer.scale_factors is None
        assert quantizer.min_values is None

    def test_calibrate_quantizer(self):
        """Test quantizer calibration."""
        quantizer = VectorQuantizer(dimension=4)
        vectors = np.array([
            [1.0, 2.0, 3.0, 4.0],
            [2.0, 3.0, 4.0, 5.0],
            [3.0, 4.0, 5.0, 6.0]
        ], dtype=np.float32)

        quantizer.calibrate(vectors)

        assert quantizer.min_values is not None
        assert quantizer.scale_factors is not None
        assert len(quantizer.min_values) == 4
        assert len(quantizer.scale_factors) == 4

    def test_quantize_vectors(self):
        """Test vector quantization."""
        quantizer = VectorQuantizer(dimension=4)
        vectors = np.array([
            [0.0, 1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0, 4.0],
            [2.0, 3.0, 4.0, 5.0]
        ], dtype=np.float32)

        quantizer.calibrate(vectors)
        quantized = quantizer.quantize(vectors)

        assert quantized.dtype == np.uint8
        assert quantized.shape == vectors.shape
        assert np.all(quantized >= 0)
        assert np.all(quantized <= 255)

    def test_dequantize_vectors(self):
        """Test vector dequantization."""
        quantizer = VectorQuantizer(dimension=4)
        original = np.array([
            [0.0, 1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0, 4.0]
        ], dtype=np.float32)

        quantizer.calibrate(original)
        quantized = quantizer.quantize(original)
        dequantized = quantizer.dequantize(quantized)

        # Allow small reconstruction error
        mse = np.mean((original - dequantized) ** 2)
        assert mse < 0.1

    def test_memory_savings(self):
        """Test memory savings calculation."""
        quantizer = VectorQuantizer(dimension=768)

        original_mb, quantized_mb, ratio = quantizer.memory_savings(100000)

        assert original_mb > quantized_mb
        assert ratio > 3  # Should be ~4x compression
        assert quantized_mb < 100  # Should fit in small memory

    def test_accuracy_loss(self):
        """Test accuracy loss calculation."""
        quantizer = VectorQuantizer(dimension=4)
        original = np.array([
            [1.0, 2.0, 3.0, 4.0],
            [2.0, 3.0, 4.0, 5.0]
        ], dtype=np.float32)

        quantizer.calibrate(original)
        quantized = quantizer.quantize(original)
        dequantized = quantizer.dequantize(quantized)

        mse = VectorQuantizer.calculate_accuracy_loss(original, dequantized)

        assert mse >= 0
        assert mse < 1.0  # Reasonable reconstruction error

    def test_quantizer_error_handling(self):
        """Test quantizer error handling."""
        quantizer = VectorQuantizer(dimension=4)
        vectors = np.array([[1.0, 2.0, 3.0, 4.0]])

        # Should raise error if not calibrated
        with pytest.raises(ValueError):
            quantizer.quantize(vectors)

        # Should raise error if not calibrated
        with pytest.raises(ValueError):
            quantizer.dequantize(np.array([[1, 2, 3, 4]], dtype=np.uint8))


class TestAdaptiveQuantizer:
    """Test adaptive quantizer."""

    def test_adaptive_quantizer_initialization(self):
        """Test adaptive quantizer init."""
        quantizer = AdaptiveQuantizer(dimension=768, bits=8)
        assert quantizer.bits == 8
        assert quantizer.max_value == 255

    def test_adaptive_4bit_quantization(self):
        """Test 4-bit quantization."""
        quantizer = AdaptiveQuantizer(dimension=4, bits=4)
        vectors = np.array([
            [0.0, 5.0, 10.0, 15.0],
            [1.0, 6.0, 11.0, 16.0]
        ], dtype=np.float32)

        quantizer.calibrate(vectors)
        quantized = quantizer.quantize(vectors)

        assert np.all(quantized <= 15)  # 4-bit max value
