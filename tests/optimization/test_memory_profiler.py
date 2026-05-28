"""Tests for memory profiler module."""

import pytest
from src.optimization.memory_profiler import MemoryProfiler, get_profiler, profile_memory


class TestMemoryProfiler:
    """Test memory profiling functionality."""

    def test_profiler_initialization(self):
        """Test profiler initialization."""
        profiler = MemoryProfiler()
        assert profiler.process is not None
        assert len(profiler.metrics_history) == 0
        assert profiler.baseline is None

    def test_capture_baseline(self):
        """Test baseline capture."""
        profiler = MemoryProfiler()
        baseline = profiler.capture_baseline()

        assert baseline is not None
        assert baseline.rss_memory_mb > 0
        assert baseline.vms_memory_mb > 0
        assert profiler.baseline is not None

    def test_record_component_size(self):
        """Test component size recording."""
        profiler = MemoryProfiler()

        profiler.record_component_size("cache", 100.5)
        profiler.record_component_size("vectors", 200.3)

        components = profiler.get_component_breakdown()
        assert "cache" in components
        assert components["cache"] == 100.5
        assert components["vectors"] == 200.3

    def test_measure_improvement(self):
        """Test improvement measurement."""
        profiler = MemoryProfiler()
        profiler.capture_baseline()

        improvement = profiler.measure_improvement()

        assert "baseline_mb" in improvement
        assert "current_mb" in improvement
        assert improvement["baseline_mb"] > 0

    def test_get_profiler_singleton(self):
        """Test profiler singleton behavior."""
        p1 = get_profiler()
        p2 = get_profiler()

        assert p1 is p2

    def test_profile_memory_decorator(self):
        """Test profile_memory decorator."""
        @profile_memory
        def dummy_function():
            return 42

        result = dummy_function()
        assert result == 42

    def test_export_metrics(self, tmp_path):
        """Test metrics export."""
        profiler = MemoryProfiler()
        profiler.capture_baseline()
        profiler.record_component_size("test", 50.0)

        export_file = tmp_path / "metrics.json"
        profiler.export_metrics(str(export_file))

        assert export_file.exists()
