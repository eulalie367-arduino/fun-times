"""Tests for batch processor module."""

import pytest
import time
from src.optimization.batch_processor import BatchProcessor, BatchJob


class TestBatchProcessor:
    """Test batch processing functionality."""

    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = BatchProcessor(max_workers=4, batch_size=10)

        assert processor.max_workers == 4
        assert processor.batch_size == 10
        assert processor.executor is not None

    def test_process_single_batch(self):
        """Test processing a single batch."""
        processor = BatchProcessor(max_workers=2, batch_size=5)

        def simple_func(x):
            return x * 2

        jobs = [
            ("job1", 5, simple_func),
            ("job2", 10, simple_func),
            ("job3", 15, simple_func)
        ]

        results = processor.process_batch(jobs)

        assert results["job1"] == 10
        assert results["job2"] == 20
        assert results["job3"] == 30
        assert processor.stats['successful_jobs'] == 3

    def test_process_batch_with_failure(self):
        """Test batch processing with failure."""
        processor = BatchProcessor(max_workers=2, batch_size=5)

        def failing_func(x):
            if x < 10:
                raise ValueError("Too small")
            return x * 2

        jobs = [
            ("job1", 5, failing_func),
            ("job2", 15, failing_func)
        ]

        results = processor.process_batch(jobs)

        assert results["job1"] is None
        assert results["job2"] == 30
        assert processor.stats['failed_jobs'] == 1

    def test_process_queries(self):
        """Test query processing."""
        processor = BatchProcessor(max_workers=2, batch_size=2)

        def query_func(q):
            return f"result_{q}"

        queries = ["query1", "query2", "query3"]

        results = processor.process_queries(queries, query_func)

        assert results["query1"] == "result_query1"
        assert results["query2"] == "result_query2"
        assert results["query3"] == "result_query3"

    def test_group_similar_queries(self):
        """Test query grouping by similarity."""
        processor = BatchProcessor(max_workers=2, batch_size=2)

        queries = [
            "what is the movie?",
            "what is the song?",
            "where is the location?",
            "what is the actor?"
        ]

        groups = processor._group_similar_queries(queries)

        assert len(groups) > 0
        assert any(len(group) > 0 for group in groups)

    def test_get_stats(self):
        """Test statistics retrieval."""
        processor = BatchProcessor(max_workers=2, batch_size=5)

        def dummy_func(x):
            return x

        jobs = [("job1", 1, dummy_func), ("job2", 2, dummy_func)]

        processor.process_batch(jobs)

        stats = processor.get_stats()

        assert "success_rate" in stats
        assert "total_jobs" in stats
        assert stats["total_jobs"] == 2
        assert stats["workers"] == 2

    def test_processor_shutdown(self):
        """Test processor shutdown."""
        processor = BatchProcessor(max_workers=2)

        processor.shutdown()

        # Executor should be shutdown
        assert processor.executor._shutdown is True

    def test_batch_job_dataclass(self):
        """Test BatchJob dataclass."""
        def dummy_func(x):
            return x * 2

        job = BatchJob(
            job_id="test",
            input_data=5,
            function=dummy_func
        )

        assert job.job_id == "test"
        assert job.input_data == 5
        assert job.function is dummy_func
        assert job.result is None
        assert job.error is None
