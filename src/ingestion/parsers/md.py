"""Markdown document parser."""
import logging
from pathlib import Path
from typing import List
import re

from .base import DocumentParser, ParsedDocument, DocumentMetadata


class MarkdownParser(DocumentParser):
    """
    Parse Markdown documents while preserving structure.

    Extracts headers, sections, and metadata from markdown files.
    """

    def __init__(self):
        """Initialize the markdown parser."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            ParsedDocument with extracted content and metadata

        Raises:
            IOError: If file cannot be read
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise IOError(f"Markdown file not found: {file_path}")

        try:
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            metadata = self._extract_metadata_from_md(file_path, content)
            sections = self._extract_sections(content)

            self.logger.info(
                f"Successfully parsed markdown: {file_path.name}",
                extra={'sections': len(sections)}
            )

            return ParsedDocument(
                content=content,
                metadata=metadata,
                sections=sections,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to parse markdown {file_path}: {str(e)}"
            )
            raise IOError(f"Cannot read markdown file: {file_path}") from e

    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract metadata from a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            DocumentMetadata with extracted metadata
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self._extract_metadata_from_md(file_path, content)

        except Exception as e:
            self.logger.warning(
                f"Could not extract metadata from {file_path}: {e}"
            )
            return DocumentMetadata(file_path=str(file_path))

    def _extract_sections(self, content: str) -> List[str]:
        """
        Extract markdown headers as sections.

        Args:
            content: Markdown content

        Returns:
            List of section headers
        """
        sections = []

        # Match markdown headers (# through ######)
        header_pattern = r'^(#{1,6})\s+(.+)$'

        for match in re.finditer(header_pattern, content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()

            if title:
                # Add indentation based on header level
                indent = "  " * (level - 1)
                sections.append(f"{indent}{title}")

        return sections[:50]  # Limit to first 50 sections

    @staticmethod
    def _extract_metadata_from_md(
        file_path: Path, content: str
    ) -> DocumentMetadata:
        """
        Extract metadata from markdown file.

        Tries to extract YAML front matter and basic info from content.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            DocumentMetadata with extracted metadata
        """
        # Extract YAML front matter if present
        yaml_meta = {}
        yaml_pattern = r'^---\n(.*?)\n---\n'
        yaml_match = re.match(yaml_pattern, content, re.DOTALL)

        if yaml_match:
            yaml_content = yaml_match.group(1)
            # Simple YAML parsing (not full YAML parser)
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    yaml_meta[key.strip()] = value.strip()

        # Extract title from first H1 header or front matter
        title = yaml_meta.get('title')

        if not title:
            h1_pattern = r'^#\s+(.+)$'
            for match in re.finditer(h1_pattern, content, re.MULTILINE):
                title = match.group(1).strip()
                break

        # Get file stats
        file_size = file_path.stat().st_size if file_path.exists() else None
        word_count = len(content.split()) if content else 0

        # Count headers
        header_count = len(re.findall(r'^#+\s+', content, re.MULTILINE))

        # Extract author from front matter
        author = yaml_meta.get('author')

        # Build extra metadata
        extra_meta = {}
        extra_meta['header_count'] = header_count

        # Add other front matter items
        for key, value in yaml_meta.items():
            if key not in ['title', 'author']:
                extra_meta[f'frontmatter_{key}'] = value

        return DocumentMetadata(
            title=title,
            author=author,
            word_count=word_count,
            file_size=file_size,
            file_path=str(file_path),
            extra=extra_meta,
        )
