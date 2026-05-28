"""Base class for document parsers."""
from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path

from src.logger import get_logger

logger = get_logger(__name__)


class DocumentParser(ABC):
    """Abstract base class for document parsers."""

    def __init__(self, file_path: Path):
        """Initialize parser with file path."""
        self.file_path = Path(file_path)

    @abstractmethod
    def parse(self) -> Dict[str, Any]:
        """Parse document and return content with metadata."""
        pass

    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract file metadata."""
        stat = self.file_path.stat()
        return {
            "filename": self.file_path.name,
            "file_size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
        }
