"""File type detection for document ingestion."""
from enum import Enum
from pathlib import Path
from typing import Optional

from src.logger import get_logger
from src.exceptions import IngestError


logger = get_logger(__name__)


class FileType(Enum):
    """Supported file types for document ingestion."""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    MARKDOWN = "md"
    JSON = "json"
    UNKNOWN = "unknown"


class FileTypeDetector:
    """Detect document file types by extension and magic bytes."""

    MAGIC_BYTES = {
        b'%PDF': FileType.PDF,
        b'PK\x03\x04': FileType.DOCX,
        b'\xd0\xcf\x11\xe0': FileType.DOC,
    }

    EXTENSION_MAP = {
        '.pdf': FileType.PDF,
        '.docx': FileType.DOCX,
        '.doc': FileType.DOC,
        '.txt': FileType.TXT,
        '.md': FileType.MARKDOWN,
        '.markdown': FileType.MARKDOWN,
        '.json': FileType.JSON,
    }

    @classmethod
    def detect_from_path(cls, file_path: Path) -> FileType:
        """Detect file type from file path."""
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        extension = file_path.suffix.lower()
        if extension in cls.EXTENSION_MAP:
            file_type = cls.EXTENSION_MAP[extension]
            logger.msg("file_type_detected", path=str(file_path), type=file_type.value)
            return file_type

        try:
            file_type = cls.detect_from_content(file_path)
            if file_type != FileType.UNKNOWN:
                return file_type
        except Exception as e:
            logger.msg("file_type_detection_error", path=str(file_path), error=str(e))

        return FileType.UNKNOWN

    @classmethod
    def detect_from_content(cls, file_path: Path, bytes_to_read: int = 512) -> FileType:
        """Detect file type from file content magic bytes."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(bytes_to_read)

            for magic_bytes, file_type in cls.MAGIC_BYTES.items():
                if header.startswith(magic_bytes):
                    return file_type

            try:
                header.decode('utf-8')
                if header.strip().startswith(b'{') or header.strip().startswith(b'['):
                    return FileType.JSON
                return FileType.TXT
            except UnicodeDecodeError:
                pass

        except Exception as e:
            logger.msg("content_detection_error", error=str(e))

        return FileType.UNKNOWN

    @classmethod
    def is_supported(cls, file_type: FileType) -> bool:
        """Check if file type is supported."""
        return file_type != FileType.UNKNOWN

    @classmethod
    def get_parser_class(cls, file_type: FileType):
        """Get appropriate parser class for file type."""
        from src.ingestion.parsers.pdf import PDFDocumentParser
        from src.ingestion.parsers.docx import DOCXDocumentParser
        from src.ingestion.parsers.txt import TextDocumentParser
        from src.ingestion.parsers.md import MarkdownDocumentParser
        from src.ingestion.parsers.json import JSONDocumentParser

        parsers = {
            FileType.PDF: PDFDocumentParser,
            FileType.DOCX: DOCXDocumentParser,
            FileType.DOC: DOCXDocumentParser,
            FileType.TXT: TextDocumentParser,
            FileType.MARKDOWN: MarkdownDocumentParser,
            FileType.JSON: JSONDocumentParser,
        }

        parser_class = parsers.get(file_type)
        if not parser_class:
            raise IngestError(f"No parser available for: {file_type.value}")

        return parser_class
