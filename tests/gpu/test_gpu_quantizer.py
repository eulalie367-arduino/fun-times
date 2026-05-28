"""Tests for GPU quantization."""

import numpy as np
import pytest
from src.optimization.gpu_quantizer import GPUQuantizer, GPUQuantizationBench


class TestGPUQuantizer:
    """Test GPU quantization."""

    def test_initialization(self):
        """Test quantizer initialization."""
        quantizer = GPUQuantizer(bit_depth=8, use_gpu=False)
        assert quantizer.bit_depth == 8
        assert not quantizer.use_gpu or not quantizer.gpu_available

    def test_calibration(self):
        """Test quantizer calibration."""
        quantizer = GPUQuantizer(bit_depth=8, use_gpu=False)
        vectors = np.random.randn(1000, 128)
        quantizer.calibrate(vectors)

        assert quantizer.scale_factors is not None
        assert len(quantizer.scale_factors) == 128

    def test_quantization_cpu(self):
        """Test CPU quantization."""
        quantizer = GPUQuantizer(bit_depth=8, use_gpu=False)
        vectors = np.random.randn(100, 64)
        quantizer.calibrate(vectors)

        quantized = quantizer.quantize(vectors)
        assert quantized.shape == vectors.shape

    def test_dequantization(self):
        """Test dequantization."""
        quantizer = GPUQuantizer(bit_depth=8, use_gpu=False)
        vectors = np.random.randn(50, 32)
        quantizer.calibrate(vectors)

        quantized = quantizer.quantize(vectors)
        dequantized = quantizer.dequantize(quantized)

        # Should be close to original
        assert dequantized.shape == vectors.shape

    def test_compression_ratio(self):
        """Test compression ratio calculation."""
        quantizer = GPUQuantizer(bit_depth=8)
        ratio = quantizer.get_compression_ratio()
        assert ratio == 4.0  # 32-bit to 8-bit

    def test_4bit_quantization(self):
        """Test 4-bit quantization."""
        quantizer = GPUQuantizer(bit_depth=4, use_gpu=False)
        vectors = np.random.randn(100, 64)
        quantizer.calibrate(vectors)

        quantized = quantizer.quantize(vectors)
        assert quantized.shape == vectors.shape

    def test_benchmark(self):
        """Test benchmarking."""
        vectors = np.random.randn(10000, 128)
        results = GPUQuantizationBench.benchmark(vectors, iterations=5)

        assert 'cpu_time_ms' in results
        assert results['cpu_time_ms'] > 0
