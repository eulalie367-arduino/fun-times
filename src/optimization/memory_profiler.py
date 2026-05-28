"""Memory profiling and optimization analysis for RAG pipeline.

Tracks memory usage across components and identifies optimization opportunities.
"""

import psutil
import os
from dataclasses import dataclass
from typing import Dict, List, Optional
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemoryMetrics:
    """Container for memory usage metrics."""
    timestamp: str
    total_memory_mb: float
    rss_memory_mb: float
    vms_memory_mb: float
    components: Dict[str, float]  # Component name -> size in MB
    peak_memory_mb: Optional[float] = None


class MemoryProfiler:
    """Profile memory usage across RAG pipeline components."""

    def __init__(self):
        """Initialize memory profiler."""
        self.process = psutil.Process(os.getpid())
        self.metrics_history: List[MemoryMetrics] = []
        self.component_sizes: Dict[str, float] = {}
        self.baseline: Optional[MemoryMetrics] = None

    def capture_baseline(self) -> MemoryMetrics:
        """Capture baseline memory usage."""
        metrics = self._measure_memory()
        self.baseline = metrics
        logger.info(f"Memory baseline captured: {metrics.rss_memory_mb:.1f} MB")
        return metrics

    def _measure_memory(self) -> MemoryMetrics:
        """Measure current memory usage."""
        mem_info = self.process.memory_info()
        rss_mb = mem_info.rss / (1024 * 1024)
        vms_mb = mem_info.vms / (1024 * 1024)

        # Estimate total system memory used
        try:
            total_mb = psutil.virtual_memory().used / (1024 * 1024)
        except:
            total_mb = rss_mb

        metrics = MemoryMetrics(
            timestamp=datetime.now().isoformat(),
            total_memory_mb=total_mb,
            rss_memory_mb=rss_mb,
            vms_memory_mb=vms_mb,
            components=self.component_sizes.copy()
        )

        return metrics

    def record_component_size(self, component_name: str, size_mb: float):
        """Record size of a specific component."""
        self.component_sizes[component_name] = size_mb
        logger.debug(f"Component {component_name}: {size_mb:.1f} MB")

    def measure_improvement(self) -> Dict[str, float]:
        """Calculate memory improvement from baseline."""
        if not self.baseline:
            return {}

        current = self._measure_memory()
        self.metrics_history.append(current)

        improvement = {
            'baseline_mb': self.baseline.rss_memory_mb,
            'current_mb': current.rss_memory_mb,
            'reduction_mb': self.baseline.rss_memory_mb - current.rss_memory_mb,
            'reduction_percent': (
                (self.baseline.rss_memory_mb - current.rss_memory_mb)
                / self.baseline.rss_memory_mb * 100
            )
        }

        logger.info(
            f"Memory improvement: {improvement['reduction_percent']:.1f}% "
            f"({improvement['reduction_mb']:.1f} MB)"
        )

        return improvement

    def get_component_breakdown(self) -> Dict[str, float]:
        """Get memory breakdown by component."""
        return self.component_sizes.copy()

    def export_metrics(self, filepath: str):
        """Export metrics to JSON file."""
        data = {
            'baseline': self.baseline.__dict__ if self.baseline else None,
            'components': self.component_sizes,
            'history': [m.__dict__ for m in self.metrics_history]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Metrics exported to {filepath}")


# Global profiler instance
_profiler: Optional[MemoryProfiler] = None


def get_profiler() -> MemoryProfiler:
    """Get or create global memory profiler."""
    global _profiler
    if _profiler is None:
        _profiler = MemoryProfiler()
    return _profiler


def profile_memory(func):
    """Decorator to profile memory usage of a function."""
    def wrapper(*args, **kwargs):
        profiler = get_profiler()
        profiler.capture_baseline()

        result = func(*args, **kwargs)

        improvement = profiler.measure_improvement()
        logger.info(
            f"Function {func.__name__} memory delta: "
            f"{improvement.get('reduction_percent', 0):.1f}%"
        )

        return result

    return wrapper
