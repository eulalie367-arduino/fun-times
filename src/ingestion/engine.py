"""Document ingestion engine for RAG pipeline."""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from threading import Thread, Lock
from queue import Queue
from dataclasses import dataclass, field
from datetime import datetime
import time

from src.ingestion.file_types import FileType, FileTypeDetector
from src.ingestion.parsers.base import ParsedDocument, DocumentParser
from src.ingestion.parsers.pdf import PDFParser
from src.ingestion.parsers.docx import DOCXParser
from src.ingestion.parsers.txt import TextParser
from src.ingestion.parsers.md import MarkdownParser
from src.ingestion.parsers.json import JSONParser
from src.config import get_settings
from src.logger import get_logger


@dataclass
class IngestionResult:
    """Result of ingesting a single document."""
    file_path: str
    file_type: FileType
    success: bool
    parsed_document: Optional[ParsedDocument] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'file_path': self.file_path,
            'file_type': self.file_type.value,
            'success': self.success,
            'error': self.error,
            'duration_seconds': self.duration_seconds,
            'timestamp': self.timestamp.isoformat(),
            'document_size': len(self.parsed_document.content)
            if self.parsed_document else 0,
        }


class DocumentIngestionEngine:
    """
    Orchestrate document parsing and ingestion.

    Features:
    - Multi-threaded batch processing
    - Automatic file type detection
    - Error handling and recovery
    - Progress tracking
    - Metadata extraction
    """

    def __init__(self, num_workers: int = 4):
        """
        Initialize the ingestion engine.

        Args:
            num_workers: Number of worker threads for parallel processing
        """
        self.logger = get_logger(__name__)
        self.num_workers = num_workers

        # Initialize components
        self.file_detector = FileTypeDetector()
        self.parsers = self._initialize_parsers()

        # Thread safety
        self.results_lock = Lock()
        self.results: List[IngestionResult] = []

        # Worker queue
        self.work_queue: Queue = Queue()
        self.workers: List[Thread] = []

        self.logger.msg(
            "engine_initialized",
            num_workers=num_workers,
            supported_types=[ft.value for ft in FileType]
        )

    def _initialize_parsers(self) -> Dict[FileType, DocumentParser]:
        """
        Initialize all document parsers.

        Returns:
            Dictionary mapping FileType to parser instance
        """
        return {
            FileType.PDF: PDFParser(),
            FileType.DOCX: DOCXParser(),
            FileType.TXT: TextParser(),
            FileType.MD: MarkdownParser(),
            FileType.JSON: JSONParser(),
        }

    def ingest_file(self, file_path: Path) -> IngestionResult:
        """
        Ingest a single document file.

        Args:
            file_path: Path to document file

        Returns:
            IngestionResult with status and parsed document
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        start_time = time.time()

        try:
            # Detect file type
            file_type = self.file_detector.detect(file_path)

            if file_type == FileType.UNKNOWN:
                error_msg = f"Unsupported file type: {file_path.suffix}"
                self.logger.msg(
                    "ingest_error",
                    file=str(file_path),
                    error=error_msg
                )
                return IngestionResult(
                    file_path=str(file_path),
                    file_type=file_type,
                    success=False,
                    error=error_msg,
                    duration_seconds=time.time() - start_time,
                )

            # Get appropriate parser
            parser = self.parsers.get(file_type)
            if not parser:
                error_msg = f"No parser available for {file_type.value}"
                return IngestionResult(
                    file_path=str(file_path),
                    file_type=file_type,
                    success=False,
                    error=error_msg,
                    duration_seconds=time.time() - start_time,
                )

            # Parse document
            parsed_doc = parser.parse(file_path)

            duration = time.time() - start_time
            self.logger.msg(
                "ingest_success",
                file=file_path.name,
                file_type=file_type.value,
                duration_seconds=duration,
                content_length=len(parsed_doc.content)
            )

            return IngestionResult(
                file_path=str(file_path),
                file_type=file_type,
                success=True,
                parsed_document=parsed_doc,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            self.logger.msg(
                "ingest_error",
                file=str(file_path),
                error=error_msg,
                duration_seconds=duration
            )

            return IngestionResult(
                file_path=str(file_path),
                file_type=FileType.UNKNOWN,
                success=False,
                error=error_msg,
                duration_seconds=duration,
            )

    def ingest_batch(
        self, file_paths: List[Path], use_threading: bool = True
    ) -> List[IngestionResult]:
        """
        Ingest multiple documents (batch processing).

        Args:
            file_paths: List of paths to document files
            use_threading: Whether to use multi-threaded processing

        Returns:
            List of IngestionResult objects
        """
        if isinstance(file_paths, list) and file_paths:
            if isinstance(file_paths[0], str):
                file_paths = [Path(p) for p in file_paths]

        self.logger.msg(
            "batch_ingest_start",
            file_count=len(file_paths),
            use_threading=use_threading
        )

        # Reset results
        with self.results_lock:
            self.results = []

        if not use_threading:
            # Sequential processing
            return self._ingest_batch_sequential(file_paths)
        else:
            # Parallel processing
            return self._ingest_batch_parallel(file_paths)

    def _ingest_batch_sequential(
        self, file_paths: List[Path]
    ) -> List[IngestionResult]:
        """
        Ingest files sequentially.

        Args:
            file_paths: List of file paths

        Returns:
            List of ingestion results
        """
        results = []

        for i, file_path in enumerate(file_paths, 1):
            result = self.ingest_file(file_path)
            results.append(result)

            self.logger.msg(
                "batch_progress",
                completed=i,
                total=len(file_paths),
                success_count=sum(1 for r in results if r.success)
            )

        return results

    def _ingest_batch_parallel(
        self, file_paths: List[Path]
    ) -> List[IngestionResult]:
        """
        Ingest files in parallel using worker threads.

        Args:
            file_paths: List of file paths

        Returns:
            List of ingestion results
        """
        # Queue all work
        for file_path in file_paths:
            self.work_queue.put(file_path)

        # Start worker threads
        self.workers = []
        for _ in range(min(self.num_workers, len(file_paths))):
            worker = Thread(target=self._worker_process, daemon=False)
            worker.start()
            self.workers.append(worker)

        # Wait for all workers to complete
        for worker in self.workers:
            worker.join()

        # Return collected results
        with self.results_lock:
            return self.results.copy()

    def _worker_process(self):
        """Worker thread process for parallel ingestion."""
        while True:
            try:
                file_path = self.work_queue.get_nowait()
            except Exception:
                # Queue is empty
                break

            try:
                result = self.ingest_file(file_path)

                with self.results_lock:
                    self.results.append(result)

            except Exception as e:
                self.logger.msg(
                    "worker_error",
                    error=str(e)
                )

            finally:
                self.work_queue.task_done()

    def ingest_directory(
        self,
        directory: Path,
        recursive: bool = True,
        pattern: str = "*",
    ) -> Tuple[List[IngestionResult], Dict[str, int]]:
        """
        Ingest all documents in a directory.

        Args:
            directory: Path to directory
            recursive: Whether to search recursively
            pattern: File pattern to match

        Returns:
            Tuple of (results list, summary statistics)
        """
        if isinstance(directory, str):
            directory = Path(directory)

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        # Find all files matching pattern
        if recursive:
            files = list(directory.glob(f"**/{pattern}"))
        else:
            files = list(directory.glob(pattern))

        # Filter to supported types
        supported_files = [
            f for f in files
            if self.file_detector.is_supported(f)
        ]

        self.logger.msg(
            "directory_ingest_start",
            directory=str(directory),
            total_files=len(supported_files),
            recursive=recursive
        )

        # Ingest all files
        results = self.ingest_batch(supported_files, use_threading=True)

        # Compute statistics
        stats = self._compute_statistics(results)

        self.logger.msg(
            "directory_ingest_complete",
            directory=str(directory),
            total_results=len(results),
            successful=stats['successful'],
            failed=stats['failed'],
        )

        return results, stats

    @staticmethod
    def _compute_statistics(
        results: List[IngestionResult]
    ) -> Dict[str, Any]:
        """
        Compute statistics from ingestion results.

        Args:
            results: List of ingestion results

        Returns:
            Dictionary with statistics
        """
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        by_type = {}
        for result in results:
            file_type = result.file_type.value
            by_type.setdefault(file_type, {'successful': 0, 'failed': 0})

            if result.success:
                by_type[file_type]['successful'] += 1
            else:
                by_type[file_type]['failed'] += 1

        total_time = sum(r.duration_seconds for r in results)
        avg_time = total_time / len(results) if results else 0

        return {
            'total': len(results),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(results) if results else 0,
            'by_type': by_type,
            'total_processing_time_seconds': total_time,
            'average_processing_time_seconds': avg_time,
        }

    def get_successful_documents(
        self, results: List[IngestionResult]
    ) -> List[ParsedDocument]:
        """
        Extract successfully parsed documents from results.

        Args:
            results: List of ingestion results

        Returns:
            List of ParsedDocument objects
        """
        return [
            r.parsed_document
            for r in results
            if r.success and r.parsed_document
        ]

    def get_errors(
        self, results: List[IngestionResult]
    ) -> Dict[str, str]:
        """
        Extract errors from results.

        Args:
            results: List of ingestion results

        Returns:
            Dictionary mapping file path to error message
        """
        return {
            r.file_path: r.error
            for r in results
            if not r.success
        }
