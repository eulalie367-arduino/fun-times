"""DOCX document parser."""
from typing import Dict, Any
from src.ingestion.parsers.base import DocumentParser
from src.logger import get_logger
from src.exceptions import IngestError

logger = get_logger(__name__)

class DOCXDocumentParser(DocumentParser):
    """Parser for DOCX documents."""
    def parse(self) -> Dict[str, Any]:
        try:
            from docx import Document
        except ImportError:
            return self._simple_parse()
        
        try:
            doc = Document(self.file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            for table in doc.tables:
                for row in table.rows:
                    text += " | ".join(cell.text for cell in row.cells) + "\n"
            
            metadata = self._extract_metadata()
            metadata.update({
                "num_paragraphs": len(doc.paragraphs),
                "num_tables": len(doc.tables),
                "format": "docx"
            })
            logger.msg("docx_parsed", paragraphs=len(doc.paragraphs))
            return {"content": text, "metadata": metadata}
        except Exception as e:
            logger.msg("docx_error", error=str(e))
            raise IngestError(f"DOCX parsing failed: {e}")
    
    def _simple_parse(self) -> Dict[str, Any]:
        metadata = self._extract_metadata()
        metadata["format"] = "docx"
        return {"content": "[DOCX - extract requires python-docx]", "metadata": metadata}
