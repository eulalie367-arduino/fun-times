"""Batch query processing for parallel optimization.

Enables processing multiple queries in parallel for improved throughput.
"""

from typing import List, Dict, Any, Callable, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class BatchJob:
    """Represents a single job in a batch."""
    job_id: str
    input_data: Any
    function: Callable
    result: Optional[Any] = None
    error: Optional[Exception] = None
    execution_time: float = 0.0


class BatchProcessor:
    """Process queries in batches with parallel execution."""

    def __init__(self, max_workers: int = 4, batch_size: int = 10):
        """Initialize batch processor.

        Args:
            max_workers: Maximum parallel workers
            batch_size: Target batch size for grouping
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.stats = {
            'total_jobs': 0,
            'successful_jobs': 0,
            'failed_jobs': 0,
            'total_time': 0.0
        }

    def process_batch(
        self,
        jobs: List[Tuple[str, Any, Callable]],
        timeout_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process a batch of jobs in parallel.

        Args:
            jobs: List of (job_id, input_data, function) tuples
            timeout_seconds: Optional timeout per job

        Returns:
            Dictionary mapping job_id to result
        """
        start_time = time.time()
        results = {}
        futures = {}

        # Submit all jobs
        for job_id, input_data, func in jobs:
            future = self.executor.submit(func, input_data)
            futures[future] = job_id
            self.stats['total_jobs'] += 1

        # Collect results as they complete
        for future in as_completed(futures, timeout=timeout_seconds):
            job_id = futures[future]

            try:
                result = future.result()
                results[job_id] = result
                self.stats['successful_jobs'] += 1
                logger.debug(f"Job {job_id} completed successfully")

            except Exception as e:
                results[job_id] = None
                self.stats['failed_jobs'] += 1
                logger.error(f"Job {job_id} failed: {str(e)}")

        elapsed = time.time() - start_time
        self.stats['total_time'] += elapsed

        logger.info(
            f"Batch processed: {self.stats['successful_jobs']} successful, "
            f"{self.stats['failed_jobs']} failed in {elapsed:.2f}s"
        )

        return results

    def process_queries(
        self,
        queries: List[str],
        query_func: Callable[[str], Any],
        group_by_similarity: bool = False
    ) -> Dict[str, Any]:
        """Process multiple queries in optimized batches.

        Args:
            queries: List of query strings
            query_func: Function to apply to each query
            group_by_similarity: If True, group similar queries together

        Returns:
            Dictionary mapping query to result
        """
        if group_by_similarity:
            batches = self._group_similar_queries(queries)
        else:
            batches = [
                queries[i:i + self.batch_size]
                for i in range(0, len(queries), self.batch_size)
            ]

        all_results = {}

        for batch in batches:
            jobs = [(q, q, query_func) for q in batch]
            batch_results = self.process_batch(jobs)
            all_results.update(batch_results)

        return all_results

    def _group_similar_queries(self, queries: List[str]) -> List[List[str]]:
        """Group queries by similarity for better cache locality.

        Args:
            queries: List of query strings

        Returns:
            List of grouped queries
        """
        # Simple grouping by query prefix/length
        # Can be enhanced with semantic similarity
        grouped = {}

        for query in queries:
            # Use first word as grouping key
            key = query.split()[0].lower() if query else "default"

            if key not in grouped:
                grouped[key] = []

            grouped[key].append(query)

        return list(grouped.values())

    def get_stats(self) -> Dict[str, Any]:
        """Get processor statistics.

        Returns:
            Dictionary with performance metrics
        """
        success_rate = (
            self.stats['successful_jobs'] / self.stats['total_jobs']
            if self.stats['total_jobs'] > 0 else 0.0
        )

        avg_time = (
            self.stats['total_time'] / self.stats['total_jobs']
            if self.stats['total_jobs'] > 0 else 0.0
        )

        return {
            'total_jobs': self.stats['total_jobs'],
            'successful': self.stats['successful_jobs'],
            'failed': self.stats['failed_jobs'],
            'success_rate': success_rate,
            'total_time': self.stats['total_time'],
            'avg_time_per_job': avg_time,
            'workers': self.max_workers
        }

    def shutdown(self):
        """Shutdown executor."""
        self.executor.shutdown(wait=True)
        logger.info("Batch processor shutdown complete")
