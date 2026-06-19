"""Phase 4A: LEAN optimization modules.

Memory profiling, quantization, cache optimization, batch processing, and index compression.
"""

from .memory_profiler import MemoryProfiler, get_profiler, profile_memory
from .quantizer import VectorQuantizer, AdaptiveQuantizer
from .cache_optimizer import SmartCache, CacheEntry
from .batch_processor import BatchProcessor, BatchJob
from .index_compressor import IndexCompressor, AdaptiveCompressor

__all__ = [
    'MemoryProfiler',
    'get_profiler',
    'profile_memory',
    'VectorQuantizer',
    'AdaptiveQuantizer',
    'SmartCache',
    'CacheEntry',
    'BatchProcessor',
    'BatchJob',
    'IndexCompressor',
    'AdaptiveCompressor',
]
