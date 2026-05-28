"""JSON document parser."""
import json
from typing import Dict, Any
from src.ingestion.parsers.base import DocumentParser
from src.logger import get_logger
from src.exceptions import IngestError

logger = get_logger(__name__)

class JSONDocumentParser(DocumentParser):
    """Parser for JSON files."""
    def parse(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            text = json.dumps(data, indent=2)
            metadata = self._extract_metadata()
            metadata.update({
                "format": "json",
                "is_array": isinstance(data, list),
                "size": len(data) if isinstance(data, (list, dict)) else 0
            })
            logger.msg("json_parsed")
            return {"content": text, "metadata": metadata}
        except json.JSONDecodeError as e:
            raise IngestError(f"Invalid JSON: {e}")
        except Exception as e:
            logger.msg("json_error", error=str(e))
            raise IngestError(f"JSON parsing failed: {e}")
