"""File type detection for document ingestion."""
from enum import Enum
from pathlib import Path
from typing import Optional
import logging


class FileType(Enum):
    """Supported document file types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    JSON = "json"
    UNKNOWN = "unknown"


class FileTypeDetector:
    """
    Detect document file type using magic bytes and file extensions.

    Supports detection of PDF, DOCX, TXT, MD, and JSON files.
    Uses magic bytes (file headers) for reliable type detection.
    """

    # Magic bytes for different file types
    MAGIC_BYTES = {
        FileType.PDF: b'%PDF',
        FileType.DOCX: b'PK\x03\x04',  # ZIP signature (DOCX is ZIP)
        FileType.JSON: b'{',
    }

    # File extensions as fallback
    EXTENSION_MAP = {
        '.pdf': FileType.PDF,
        '.docx': FileType.DOCX,
        '.txt': FileType.TXT,
        '.md': FileType.MD,
        '.markdown': FileType.MD,
        '.json': FileType.JSON,
    }

    def __init__(self):
        """Initialize the file type detector."""
        self.logger = logging.getLogger(__name__)

    def detect(self, file_path: Path) -> FileType:
        """
        Detect file type using magic bytes or extension.

        Args:
            file_path: Path to the file to detect

        Returns:
            FileType enum value

        Raises:
            FileNotFoundError: If file does not exist
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Try magic bytes detection first
        file_type = self._detect_by_magic_bytes(file_path)
        if file_type != FileType.UNKNOWN:
            return file_type

        # Fallback to extension detection
        file_type = self._detect_by_extension(file_path)
        if file_type != FileType.UNKNOWN:
            return file_type

        self.logger.warning(
            f"Could not detect file type for {file_path}, "
            "defaulting to UNKNOWN"
        )
        return FileType.UNKNOWN

    def _detect_by_magic_bytes(self, file_path: Path) -> FileType:
        """
        Detect file type by reading magic bytes from file header.

        Args:
            file_path: Path to the file

        Returns:
            FileType if detected, FileType.UNKNOWN otherwise
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)

            # Check PDF
            if header.startswith(self.MAGIC_BYTES[FileType.PDF]):
                return FileType.PDF

            # Check DOCX (ZIP format)
            if header.startswith(self.MAGIC_BYTES[FileType.DOCX]):
                # DOCX files are ZIP archives with specific structure
                # Additional validation could check for [Content_Types].xml
                if self._is_valid_docx(file_path):
                    return FileType.DOCX

            # Check JSON (can start with { or [)
            if header.startswith(b'{') or header.startswith(b'['):
                try:
                    # Verify it's valid JSON
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f.read(1)  # Try to read first char
                    return FileType.JSON
                except (UnicodeDecodeError, IOError):
                    pass

        except (IOError, OSError) as e:
            self.logger.debug(f"Error reading file header: {e}")

        return FileType.UNKNOWN

    def _is_valid_docx(self, file_path: Path) -> bool:
        """
        Validate that a ZIP file is a DOCX document.

        DOCX files must contain [Content_Types].xml file.

        Args:
            file_path: Path to the file

        Returns:
            True if valid DOCX, False otherwise
        """
        try:
            import zipfile
            with zipfile.ZipFile(file_path, 'r') as zf:
                # Check for required DOCX files
                return '[Content_Types].xml' in zf.namelist()
        except (zipfile.BadZipFile, IOError):
            return False

    def _detect_by_extension(self, file_path: Path) -> FileType:
        """
        Detect file type by file extension.

        Args:
            file_path: Path to the file

        Returns:
            FileType if matched, FileType.UNKNOWN otherwise
        """
        extension = file_path.suffix.lower()
        return self.EXTENSION_MAP.get(extension, FileType.UNKNOWN)

    def is_supported(self, file_path: Path) -> bool:
        """
        Check if file type is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if file type is supported, False otherwise
        """
        file_type = self.detect(file_path)
        return file_type != FileType.UNKNOWN

    def get_supported_extensions(self) -> list[str]:
        """
        Get list of supported file extensions.

        Returns:
            List of supported extensions
        """
        return list(self.EXTENSION_MAP.keys())
