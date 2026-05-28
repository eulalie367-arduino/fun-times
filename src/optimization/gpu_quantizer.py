"""GPU-accelerated vector quantization using CUDA."""

from typing import Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class GPUQuantizer:
    """CUDA-accelerated 8-bit and 4-bit vector quantization."""

    def __init__(self, bit_depth: int = 8, use_gpu: bool = True):
        """Initialize GPU quantizer.

        Args:
            bit_depth: 8 or 4 bits
            use_gpu: Whether to use GPU acceleration
        """
        self.bit_depth = bit_depth
        self.use_gpu = use_gpu
        self.scale_factors = None
        self.min_values = None
        self.gpu_available = self._check_gpu()

    def _check_gpu(self) -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def calibrate(self, vectors: np.ndarray, sample_size: int = 10000) -> None:
        """Calibrate quantizer on sample vectors.

        Args:
            vectors: Input vectors (n_vectors, dim)
            sample_size: Number of vectors to sample for calibration
        """
        if len(vectors) > sample_size:
            indices = np.random.choice(len(vectors), sample_size, replace=False)
            sample = vectors[indices]
        else:
            sample = vectors

        if self.use_gpu and self.gpu_available:
            self._calibrate_gpu(sample)
        else:
            self._calibrate_cpu(sample)

    def _calibrate_cpu(self, vectors: np.ndarray) -> None:
        """Calibrate on CPU."""
        self.min_values = np.min(vectors, axis=0)
        max_values = np.max(vectors, axis=0)
        self.scale_factors = (max_values - self.min_values) / (2 ** self.bit_depth - 1)
        logger.info("Calibrated quantizer on CPU")

    def _calibrate_gpu(self, vectors: np.ndarray) -> None:
        """Calibrate on GPU."""
        try:
            import torch
            vectors_gpu = torch.tensor(vectors, dtype=torch.float32, device='cuda')
            self.min_values = torch.min(vectors_gpu, dim=0)[0].cpu().numpy()
            max_values = torch.max(vectors_gpu, dim=0)[0].cpu().numpy()
            self.scale_factors = (max_values - self.min_values) / (2 ** self.bit_depth - 1)
            logger.info(f"Calibrated quantizer on GPU")
        except ImportError:
            self._calibrate_cpu(vectors)

    def quantize(self, vectors: np.ndarray) -> np.ndarray:
        """Quantize vectors to lower precision.

        Args:
            vectors: Input vectors (n_vectors, dim)

        Returns:
            Quantized vectors
        """
        if self.scale_factors is None:
            self.calibrate(vectors)

        if self.use_gpu and self.gpu_available:
            return self._quantize_gpu(vectors)
        else:
            return self._quantize_cpu(vectors)

    def _quantize_cpu(self, vectors: np.ndarray) -> np.ndarray:
        """Quantize on CPU."""
        normalized = (vectors - self.min_values) / (self.scale_factors + 1e-8)
        normalized = np.clip(normalized, 0, 2 ** self.bit_depth - 1)
        return normalized.astype(np.uint8 if self.bit_depth == 8 else np.uint4)

    def _quantize_gpu(self, vectors: np.ndarray) -> np.ndarray:
        """Quantize on GPU."""
        try:
            import torch
            vectors_gpu = torch.tensor(vectors, dtype=torch.float32, device='cuda')
            min_gpu = torch.tensor(self.min_values, device='cuda')
            scale_gpu = torch.tensor(self.scale_factors, device='cuda')

            normalized = (vectors_gpu - min_gpu) / (scale_gpu + 1e-8)
            normalized = torch.clamp(normalized, 0, 2 ** self.bit_depth - 1)
            dtype = torch.uint8 if self.bit_depth == 8 else torch.int8
            quantized = normalized.to(dtype).cpu().numpy()
            return quantized
        except ImportError:
            return self._quantize_cpu(vectors)

    def dequantize(self, quantized: np.ndarray) -> np.ndarray:
        """Dequantize vectors back to float.

        Args:
            quantized: Quantized vectors

        Returns:
            Float vectors
        """
        return quantized.astype(np.float32) * self.scale_factors + self.min_values

    def get_compression_ratio(self) -> float:
        """Get compression ratio vs float32."""
        if self.bit_depth == 8:
            return 4.0  # 32-bit float -> 8-bit
        else:
            return 8.0  # 32-bit float -> 4-bit


class GPUQuantizationBench:
    """Benchmark GPU vs CPU quantization."""

    @staticmethod
    def benchmark(vectors: np.ndarray, iterations: int = 100) -> dict:
        """Benchmark quantization performance.

        Args:
            vectors: Test vectors
            iterations: Number of iterations

        Returns:
            Benchmark results
        """
        import time

        results = {}

        # CPU benchmark
        quantizer_cpu = GPUQuantizer(use_gpu=False)
        start = time.time()
        for _ in range(iterations):
            quantizer_cpu.quantize(vectors)
        cpu_time = time.time() - start
        results['cpu_time_ms'] = (cpu_time / iterations) * 1000

        # GPU benchmark (if available)
        quantizer_gpu = GPUQuantizer(use_gpu=True)
        if quantizer_gpu.gpu_available:
            start = time.time()
            for _ in range(iterations):
                quantizer_gpu.quantize(vectors)
            gpu_time = time.time() - start
            results['gpu_time_ms'] = (gpu_time / iterations) * 1000
            results['speedup'] = cpu_time / gpu_time
        else:
            results['gpu_available'] = False

        return results
