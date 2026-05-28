"""JSON document parser."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from .base import DocumentParser, ParsedDocument, DocumentMetadata


class JSONParser(DocumentParser):
    """
    Parse JSON documents and collections.

    Handles JSON objects, arrays, and nested structures.
    Converts JSON to readable text format.
    """

    def __init__(self):
        """Initialize the JSON parser."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def parse(self, file_path: Path) -> ParsedDocument:
        """
        Parse a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            ParsedDocument with extracted content and metadata

        Raises:
            IOError: If file cannot be read
            ValueError: If JSON is invalid
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        if not file_path.exists():
            raise IOError(f"JSON file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            content = self._convert_json_to_text(data)
            metadata = self._extract_metadata_from_json(
                file_path, data, content
            )

            self.logger.info(
                f"Successfully parsed JSON: {file_path.name}",
                extra={'root_type': type(data).__name__}
            )

            return ParsedDocument(
                content=content,
                metadata=metadata,
                raw_content=json.dumps(data, indent=2),
            )

        except json.JSONDecodeError as e:
            self.logger.error(
                f"Invalid JSON in {file_path}: {str(e)}"
            )
            raise ValueError(f"Invalid JSON file: {file_path}") from e
        except Exception as e:
            self.logger.error(
                f"Failed to parse JSON {file_path}: {str(e)}"
            )
            raise IOError(f"Cannot read JSON file: {file_path}") from e

    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """
        Extract metadata from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            DocumentMetadata with extracted metadata
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            content = self._convert_json_to_text(data)
            return self._extract_metadata_from_json(file_path, data, content)

        except Exception as e:
            self.logger.warning(
                f"Could not extract metadata from {file_path}: {e}"
            )
            return DocumentMetadata(file_path=str(file_path))

    def _convert_json_to_text(self, data: Any, depth: int = 0) -> str:
        """
        Convert JSON structure to readable text format.

        Args:
            data: JSON data to convert
            depth: Current nesting depth

        Returns:
            Text representation of JSON
        """
        lines = []
        indent = "  " * depth

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{indent}{key}:")
                    lines.append(self._convert_json_to_text(value, depth + 1))
                else:
                    lines.append(f"{indent}{key}: {self._format_value(value)}")

        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent}[{i}]:")
                    lines.append(self._convert_json_to_text(item, depth + 1))
                else:
                    lines.append(f"{indent}[{i}] {self._format_value(item)}")

        else:
            return self._format_value(data)

        return "\n".join(lines)

    @staticmethod
    def _format_value(value: Any) -> str:
        """
        Format a JSON value as readable string.

        Args:
            value: Value to format

        Returns:
            Formatted string
        """
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return str(value)

    @staticmethod
    def _extract_metadata_from_json(
        file_path: Path, data: Any, content: str
    ) -> DocumentMetadata:
        """
        Extract metadata from JSON data.

        Args:
            file_path: Path to file
            data: Parsed JSON data
            content: Text representation of JSON

        Returns:
            DocumentMetadata with extracted metadata
        """
        # File stats
        file_size = file_path.stat().st_size if file_path.exists() else None
        word_count = len(content.split()) if content else 0

        # Analyze JSON structure
        extra_meta: Dict[str, Any] = {}

        if isinstance(data, dict):
            extra_meta['root_type'] = 'object'
            extra_meta['top_level_keys'] = list(data.keys())[:20]
            extra_meta['key_count'] = len(data.keys())

            # Try to extract title and description from common fields
            title = None
            if 'title' in data:
                title = str(data['title'])[:100]
            elif 'name' in data:
                title = str(data['name'])[:100]

        elif isinstance(data, list):
            extra_meta['root_type'] = 'array'
            extra_meta['item_count'] = len(data)

            # Check first item for structure
            if data and isinstance(data[0], dict):
                extra_meta['first_item_keys'] = list(data[0].keys())[:20]

            title = f"Array with {len(data)} items"

        else:
            extra_meta['root_type'] = type(data).__name__
            title = str(data)[:100]

        # Count nesting depth
        depth = JSONParser._calculate_depth(data)
        extra_meta['max_nesting_depth'] = depth

        return DocumentMetadata(
            title=title,
            word_count=word_count,
            file_size=file_size,
            file_path=str(file_path),
            extra=extra_meta,
        )

    @staticmethod
    def _calculate_depth(data: Any, current_depth: int = 0) -> int:
        """
        Calculate maximum nesting depth of JSON structure.

        Args:
            data: JSON data
            current_depth: Current depth level

        Returns:
            Maximum depth
        """
        if isinstance(data, dict):
            if not data:
                return current_depth
            return max(
                JSONParser._calculate_depth(v, current_depth + 1)
                for v in data.values()
            )

        elif isinstance(data, list):
            if not data:
                return current_depth
            return max(
                JSONParser._calculate_depth(item, current_depth + 1)
                for item in data
            )

        else:
            return current_depth
