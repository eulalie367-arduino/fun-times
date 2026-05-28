"""PDF document parser."""
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .base import DocumentParser, ParsedDocument, DocumentMetadata


class PDFParser(DocumentParser):
    """
    Parse PDF documents and extract text and metadata.

    Uses PyPDF2 or pdfplumber for robust PDF text extraction.
    Preserves document structure when possible.
    """

    def __init__(self):
        """Initialize the PDF parser."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a PDF file and extract content and metadata.

        Args:
            file_path: Path to the PDF file

        Returns:
            ParsedDocument with extracted content and metadata

        Raises:
            IOError: If file cannot be read
            ValueError: If PDF is invalid
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise IOError(f"PDF file not found: {file_path}")

        try:
            import pdfplumber
        except ImportError:
            try:
                import PyPDF2 as pdfplumber
            except ImportError:
                raise ImportError(
                    "Neither pdfplumber nor PyPDF2 available. "
                    "Install one: pip install pdfplumber"
                )

        try:
            with pdfplumber.open(file_path) as pdf:
                content = self._extract_text(pdf)
                metadata = self._extract_metadata_from_pdf(pdf, file_path)
                sections = self._extract_sections(pdf)

                self.logger.info(
                    f"Successfully parsed PDF: {file_path.name}",
                    extra={'pages': len(pdf.pages)}
                )

                return ParsedDocument(
                    content=content,
                    metadata=metadata,
                    sections=sections,
                )

        except Exception as e:
            self.logger.error(
                f"Failed to parse PDF {file_path}: {str(e)}"
            )
            raise ValueError(f"Invalid or corrupted PDF file: {file_path}") from e

    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract metadata from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            DocumentMetadata with extracted metadata
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        try:
            import pdfplumber
        except ImportError:
            try:
                import PyPDF2 as pdfplumber
            except ImportError:
                return DocumentMetadata(file_path=str(file_path))

        try:
            with pdfplumber.open(file_path) as pdf:
                return self._extract_metadata_from_pdf(pdf, file_path)
        except Exception as e:
            self.logger.warning(
                f"Could not extract metadata from {file_path}: {e}"
            )
            return DocumentMetadata(file_path=str(file_path))

    def _extract_text(self, pdf) -> str:
        """
        Extract all text from PDF while preserving structure.

        Args:
            pdf: PDF object from pdfplumber

        Returns:
            Extracted text
        """
        text_parts = []

        for page_num, page in enumerate(pdf.pages, 1):
            try:
                # Extract text from page
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                self.logger.warning(
                    f"Could not extract text from page {page_num}: {e}"
                )

        return "\n\n".join(text_parts)

    def _extract_metadata_from_pdf(
        self, pdf, file_path: Path
    ) -> DocumentMetadata:
        """
        Extract metadata from PDF document properties.

        Args:
            pdf: PDF object from pdfplumber
            file_path: Path to PDF file

        Returns:
            DocumentMetadata with extracted metadata
        """
        try:
            # Try to get metadata from PDF
            pdf_meta = pdf.metadata or {}
        except Exception:
            pdf_meta = {}

        # Extract metadata fields
        title = self._extract_string(pdf_meta.get('Title'))
        author = self._extract_string(pdf_meta.get('Author'))

        # Extract dates
        created_date = self._extract_date(pdf_meta.get('CreationDate'))
        modified_date = self._extract_date(pdf_meta.get('ModDate'))

        # File info
        file_size = file_path.stat().st_size if file_path.exists() else None
        page_count = len(pdf.pages) if hasattr(pdf, 'pages') else None

        # Calculate word count from extracted text
        try:
            full_text = pdf.pages[0].extract_text() if pdf.pages else ""
            word_count = len(full_text.split()) * page_count if page_count else None
        except Exception:
            word_count = None

        extra_meta = {}
        if pdf_meta.get('Subject'):
            extra_meta['subject'] = self._extract_string(pdf_meta['Subject'])
        if pdf_meta.get('Keywords'):
            extra_meta['keywords'] = self._extract_string(pdf_meta['Keywords'])
        if pdf_meta.get('Producer'):
            extra_meta['producer'] = self._extract_string(pdf_meta['Producer'])

        return DocumentMetadata(
            title=title,
            author=author,
            created_date=created_date,
            modified_date=modified_date,
            page_count=page_count,
            word_count=word_count,
            file_size=file_size,
            file_path=str(file_path),
            extra=extra_meta,
        )

    def _extract_sections(self, pdf) -> List[str]:
        """
        Extract sections from PDF based on text structure.

        Args:
            pdf: PDF object from pdfplumber

        Returns:
            List of section titles/headers
        """
        sections = []

        try:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Simple heuristic: lines that are relatively short
                    # and appear at start of page might be headers
                    lines = text.split('\n')[:5]
                    for line in lines:
                        if len(line) < 100 and len(line) > 5:
                            sections.append(line.strip())
        except Exception as e:
            self.logger.debug(f"Could not extract sections: {e}")

        return sections[:10]  # Limit to first 10 sections

    @staticmethod
    def _extract_string(value) -> Optional[str]:
        """Extract string from PDF metadata value."""
        if value is None:
            return None

        if isinstance(value, bytes):
            try:
                return value.decode('utf-8', errors='ignore')
            except Exception:
                return None

        return str(value) if value else None

    @staticmethod
    def _extract_date(value) -> Optional[datetime]:
        """Extract date from PDF metadata value."""
        if not value:
            return None

        try:
            # PDF dates are often in format: D:YYYYMMDDHHmmSS
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='ignore')

            if isinstance(value, str):
                # Remove 'D:' prefix if present
                if value.startswith('D:'):
                    value = value[2:]

                # Parse datetime
                if len(value) >= 8:
                    year = int(value[0:4])
                    month = int(value[4:6])
                    day = int(value[6:8])
                    hour = int(value[8:10]) if len(value) > 8 else 0
                    minute = int(value[10:12]) if len(value) > 10 else 0
                    second = int(value[12:14]) if len(value) > 12 else 0

                    return datetime(year, month, day, hour, minute, second)
        except (ValueError, IndexError, TypeError):
            pass

        return None
