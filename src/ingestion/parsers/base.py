"""Abstract base parser for document ingestion."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime


@dataclass
class DocumentMetadata:
    """Metadata extracted from a document."""
    title: Optional[str] = None
    author: Optional[str] = None
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    file_size: Optional[int] = None
    file_path: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        result = {
            'title': self.title,
            'author': self.author,
            'language': self.language,
            'page_count': self.page_count,
            'word_count': self.word_count,
            'file_size': self.file_size,
            'file_path': self.file_path,
        }

        if self.created_date:
            result['created_date'] = self.created_date.isoformat()
        if self.modified_date:
            result['modified_date'] = self.modified_date.isoformat()

        result.update(self.extra)
        return result


@dataclass
class ParsedDocument:
    """Result of parsing a document."""
    content: str
    metadata: DocumentMetadata
    sections: List[str] = field(default_factory=list)
    raw_content: Optional[str] = None

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of parsed document."""
        return {
            'content_length': len(self.content),
            'section_count': len(self.sections),
            'metadata': self.metadata.to_dict(),
        }


class DocumentParser(ABC):
    """
    Abstract base class for document parsers.

    Defines the interface that all document parsers must implement.
    """

    def __init__(self):
        """Initialize the parser."""
        self.logger = None

    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a document and extract content and metadata.

        Args:
            file_path: Path to the document file

        Returns:
            ParsedDocument containing extracted content and metadata

        Raises:
            IOError: If file cannot be read
            ValueError: If file format is invalid
        """
        pass

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract metadata from document.

        Args:
            file_path: Path to the document file

        Returns:
            DocumentMetadata with extracted metadata

        Raises:
            IOError: If file cannot be read
        """
        pass

    def validate(self, file_path: Path) -> bool:
        """
        Validate that file can be parsed by this parser.

        Args:
            file_path: Path to the document file

        Returns:
            True if file is valid for this parser, False otherwise
        """
        try:
            if not file_path.exists():
                return False
            return True
        except Exception:
            return False

    def get_parser_info(self) -> Dict[str, Any]:
        """
        Get information about this parser.

        Returns:
            Dictionary with parser information
        """
        return {
            'parser_class': self.__class__.__name__,
            'module': self.__class__.__module__,
        }
