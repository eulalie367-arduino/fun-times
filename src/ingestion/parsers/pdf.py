"""PDF document parser."""
from typing import Dict, Any
from pathlib import Path
from src.ingestion.parsers.base import DocumentParser
from src.logger import get_logger
from src.exceptions import IngestError

logger = get_logger(__name__)

class PDFDocumentParser(DocumentParser):
    """Parser for PDF documents."""
    def parse(self) -> Dict[str, Any]:
        try:
            import PyPDF2
        except ImportError:
            logger.msg("pdf_fallback")
            return self._simple_parse()
        
        try:
            with open(self.file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
                text = ""
                for page in pdf_reader.pages:
                    try:
                        text += page.extract_text()
                    except:
                        pass
                
                metadata = self._extract_metadata()
                metadata.update({"num_pages": num_pages, "format": "pdf"})
                logger.msg("pdf_parsed", pages=num_pages)
                
                return {"content": text, "metadata": metadata}
        except Exception as e:
            logger.msg("pdf_error", error=str(e))
            raise IngestError(f"PDF parsing failed: {e}")
    
    def _simple_parse(self) -> Dict[str, Any]:
        metadata = self._extract_metadata()
        metadata["format"] = "pdf"
        return {"content": "[PDF - extract requires PyPDF2]", "metadata": metadata}
