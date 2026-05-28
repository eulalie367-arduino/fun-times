"""Markdown document parser."""
from typing import Dict, Any
from src.ingestion.parsers.base import DocumentParser
from src.logger import get_logger
from src.exceptions import IngestError

logger = get_logger(__name__)

class MarkdownDocumentParser(DocumentParser):
    """Parser for Markdown files."""
    def parse(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            lines = text.split('\n')
            headers = [l for l in lines if l.startswith('#')]
            
            metadata = self._extract_metadata()
            metadata.update({
                "num_lines": len(lines),
                "num_headers": len(headers),
                "format": "md"
            })
            logger.msg("md_parsed", lines=len(lines))
            return {"content": text, "metadata": metadata}
        except Exception as e:
            logger.msg("md_error", error=str(e))
            raise IngestError(f"Markdown parsing failed: {e}")
