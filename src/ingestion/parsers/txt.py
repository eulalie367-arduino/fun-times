"""Plain text document parser."""
import logging
from pathlib import Path
from typing import Optional
import chardet

from .base import DocumentParser, ParsedDocument, DocumentMetadata


class TextParser(DocumentParser):
    """
    Parse plain text files with encoding detection.

    Automatically detects file encoding and extracts content.
    """

    def __init__(self):
        """Initialize the text parser."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a plain text file.

        Args:
            file_path: Path to the text file

        Returns:
            ParsedDocument with extracted content and metadata

        Raises:
            IOError: If file cannot be read
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise IOError(f"Text file not found: {file_path}")

        try:
            # Detect encoding
            encoding = self._detect_encoding(file_path)

            # Read file with detected encoding
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()

            metadata = self._extract_metadata_from_text(
                file_path, content, encoding
            )

            self.logger.info(
                f"Successfully parsed text file: {file_path.name}",
                extra={'encoding': encoding, 'size': len(content)}
            )

            return ParsedDocument(
                content=content,
                metadata=metadata,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to parse text file {file_path}: {str(e)}"
            )
            raise IOError(f"Cannot read text file: {file_path}") from e

    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract metadata from a text file.

        Args:
            file_path: Path to the text file

        Returns:
            DocumentMetadata with extracted metadata
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        try:
            encoding = self._detect_encoding(file_path)

            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()

            return self._extract_metadata_from_text(
                file_path, content, encoding
            )

        except Exception as e:
            self.logger.warning(
                f"Could not extract metadata from {file_path}: {e}"
            )
            return DocumentMetadata(file_path=str(file_path))

    def _detect_encoding(self, file_path: Path) -> str:
        """
        Detect file encoding using chardet.

        Args:
            file_path: Path to the file

        Returns:
            Detected encoding (default: utf-8)
        """
        try:
            # Read first chunk of file for detection
            with open(file_path, 'rb') as f:
                raw_data = f.read(100000)  # Read up to 100KB

            # Detect encoding
            detected = chardet.detect(raw_data)

            if detected and detected.get('encoding'):
                encoding = detected['encoding']
                # Handle some encoding aliases
                if encoding.lower().startswith('iso-8859'):
                    encoding = 'latin-1'
                elif encoding.lower() in ['ascii', 'utf-8']:
                    encoding = encoding.lower()

                self.logger.debug(
                    f"Detected encoding: {encoding} "
                    f"(confidence: {detected.get('confidence')})"
                )
                return encoding

        except Exception as e:
            self.logger.debug(f"Encoding detection failed: {e}")

        return 'utf-8'  # Default to UTF-8

    @staticmethod
    def _extract_metadata_from_text(
        file_path: Path, content: str, encoding: str
    ) -> DocumentMetadata:
        """
        Extract metadata from plain text file.

        Args:
            file_path: Path to file
            content: File content
            encoding: Detected encoding

        Returns:
            DocumentMetadata with extracted metadata
        """
        # Basic metadata
        file_size = file_path.stat().st_size if file_path.exists() else None
        word_count = len(content.split()) if content else 0
        line_count = len(content.split('\n')) if content else 0

        # Try to extract title from first non-empty line
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        title = lines[0][:100] if lines else None  # First 100 chars

        return DocumentMetadata(
            title=title,
            file_size=file_size,
            word_count=word_count,
            file_path=str(file_path),
            extra={
                'encoding': encoding,
                'line_count': line_count,
            },
        )
