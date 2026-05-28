"""Document ingestion system for RAG pipeline."""
from src.ingestion.file_types import FileType, FileTypeDetector
from src.ingestion.parsers.base import (
    DocumentParser,
    DocumentMetadata,
    ParsedDocument,
)
from src.ingestion.parsers.pdf import PDFParser
from src.ingestion.parsers.docx import DOCXParser
from src.ingestion.parsers.txt import TextParser
from src.ingestion.parsers.md import MarkdownParser
from src.ingestion.parsers.json import JSONParser
from src.ingestion.engine import DocumentIngestionEngine, IngestionResult

__all__ = [
    'FileType',
    'FileTypeDetector',
    'DocumentParser',
    'DocumentMetadata',
    'ParsedDocument',
    'PDFParser',
    'DOCXParser',
    'TextParser',
    'MarkdownParser',
    'JSONParser',
    'DocumentIngestionEngine',
    'IngestionResult',
]
