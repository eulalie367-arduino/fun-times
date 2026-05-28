"""Plain text document parser."""
from typing import Dict, Any
from src.ingestion.parsers.base import DocumentParser
from src.logger import get_logger
from src.exceptions import IngestError

logger = get_logger(__name__)

class TextDocumentParser(DocumentParser):
    """Parser for plain text files."""
    def parse(self) -> Dict[str, Any]:
        try:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(self.file_path, 'r', encoding='latin-1') as f:
                    text = f.read()
            
            metadata = self._extract_metadata()
            metadata.update({
                "num_lines": len(text.split('\n')),
                "format": "txt"
            })
            logger.msg("txt_parsed", lines=metadata["num_lines"])
            return {"content": text, "metadata": metadata}
        except Exception as e:
            logger.msg("txt_error", error=str(e))
            raise IngestError(f"Text parsing failed: {e}")
