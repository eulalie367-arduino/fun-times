"""Document ingestion engine with batch processing."""
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

from src.ingestion.file_types import FileTypeDetector, FileType
from src.logger import get_logger
from src.exceptions import IngestError

logger = get_logger(__name__)


class DocumentIngestionEngine:
    """Orchestrate document ingestion with batch processing."""
    
    def __init__(self, max_workers: int = 4, batch_size: int = 10):
        """Initialize ingestion engine.
        
        Args:
            max_workers: Number of parallel workers
            batch_size: Documents per batch
        """
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
        }
        self.lock = threading.Lock()
        logger.msg("ingestion_engine_init", workers=max_workers, batch_size=batch_size)
    
    def ingest_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Ingest a single document file."""
        file_path = Path(file_path)
        
        try:
            # Detect file type
            file_type = FileTypeDetector.detect_from_path(file_path)
            
            if not FileTypeDetector.is_supported(file_type):
                logger.msg("unsupported_file_type", path=str(file_path), type=file_type.value)
                self._update_stats("skipped")
                return None
            
            # Get parser
            parser_class = FileTypeDetector.get_parser_class(file_type)
            parser = parser_class(file_path)
            
            # Parse document
            result = parser.parse()
            self._update_stats("successful")
            
            logger.msg("file_ingested", path=str(file_path), type=file_type.value)
            return result
            
        except Exception as e:
            logger.msg("ingest_error", path=str(file_path), error=str(e))
            self._update_stats("failed")
            raise IngestError(f"Failed to ingest {file_path}: {e}")
    
    def ingest_batch(self, file_paths: List[Path]) -> List[Dict[str, Any]]:
        """Ingest multiple documents in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.ingest_file, path): path 
                for path in file_paths
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.msg("batch_item_error", error=str(e))
        
        logger.msg("batch_ingestion_complete", total=len(file_paths), successful=len(results))
        return results
    
    def ingest_directory(self, directory: Path, recursive: bool = True) -> List[Dict[str, Any]]:
        """Ingest all documents in a directory."""
        directory = Path(directory)
        
        if not directory.is_dir():
            raise IngestError(f"Not a directory: {directory}")
        
        # Find all documents
        if recursive:
            files = list(directory.rglob("*"))
        else:
            files = list(directory.glob("*"))
        
        files = [f for f in files if f.is_file()]
        logger.msg("directory_scan", path=str(directory), files=len(files))
        
        # Ingest in batches
        results = []
        for i in range(0, len(files), self.batch_size):
            batch = files[i:i + self.batch_size]
            logger.msg("processing_batch", batch=i // self.batch_size + 1, size=len(batch))
            batch_results = self.ingest_batch(batch)
            results.extend(batch_results)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics."""
        with self.lock:
            total = self.stats["total_processed"]
            success_rate = (self.stats["successful"] / total * 100) if total > 0 else 0
            
            return {
                "total_processed": self.stats["total_processed"],
                "successful": self.stats["successful"],
                "failed": self.stats["failed"],
                "skipped": self.stats["skipped"],
                "success_rate": f"{success_rate:.1f}%",
            }
    
    def _update_stats(self, status: str):
        """Update statistics thread-safely."""
        with self.lock:
            self.stats["total_processed"] += 1
            if status in self.stats:
                self.stats[status] += 1
