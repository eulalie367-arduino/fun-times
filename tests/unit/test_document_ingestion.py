"""Tests for document ingestion system."""
import pytest
import tempfile
import shutil
from pathlib import Path
import json

from src.ingestion.file_types import FileType, FileTypeDetector
from src.ingestion.engine import DocumentIngestionEngine
from src.exceptions import IngestError


class TestFileTypeDetector:
    """Test file type detection."""
    
    def test_pdf_detection(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF")
        assert FileTypeDetector.detect_from_path(pdf_file) == FileType.PDF
    
    def test_txt_detection(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello")
        assert FileTypeDetector.detect_from_path(txt_file) == FileType.TXT
    
    def test_md_detection(self, tmp_path):
        md_file = tmp_path / "test.md"
        md_file.write_text("# Header")
        assert FileTypeDetector.detect_from_path(md_file) == FileType.MARKDOWN
    
    def test_json_detection(self, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')
        assert FileTypeDetector.detect_from_path(json_file) == FileType.JSON
    
    def test_is_supported(self):
        assert FileTypeDetector.is_supported(FileType.PDF)
        assert not FileTypeDetector.is_supported(FileType.UNKNOWN)


class TestIngestionEngine:
    """Test ingestion engine."""
    
    def test_engine_init(self):
        engine = DocumentIngestionEngine(max_workers=2)
        assert engine.max_workers == 2
        stats = engine.get_stats()
        assert stats["total_processed"] == 0
    
    def test_ingest_text(self, tmp_path):
        engine = DocumentIngestionEngine()
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Content")
        
        result = engine.ingest_file(txt_file)
        assert result is not None
        assert "content" in result
        assert result["metadata"]["format"] == "txt"
    
    def test_ingest_json(self, tmp_path):
        engine = DocumentIngestionEngine()
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "val"}')
        
        result = engine.ingest_file(json_file)
        assert result["metadata"]["format"] == "json"
    
    def test_batch_ingest(self, tmp_path):
        engine = DocumentIngestionEngine(max_workers=2)
        files = []
        for i in range(3):
            f = tmp_path / f"test{i}.txt"
            f.write_text(f"Content {i}")
            files.append(f)
        
        results = engine.ingest_batch(files)
        assert len(results) == 3
    
    def test_statistics(self, tmp_path):
        engine = DocumentIngestionEngine()
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Test")
        
        engine.ingest_file(txt_file)
        stats = engine.get_stats()
        assert stats["successful"] >= 1
        assert "%" in stats["success_rate"]


class TestParsers:
    """Test individual parsers."""
    
    def test_text_parser(self, tmp_path):
        from src.ingestion.parsers.txt import TextDocumentParser
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Line1\nLine2")
        parser = TextDocumentParser(txt_file)
        result = parser.parse()
        assert "content" in result
        assert result["metadata"]["num_lines"] == 2
    
    def test_json_parser(self, tmp_path):
        from src.ingestion.parsers.json import JSONDocumentParser
        json_file = tmp_path / "test.json"
        json_file.write_text('{"a": 1}')
        parser = JSONDocumentParser(json_file)
        result = parser.parse()
        assert result["metadata"]["format"] == "json"
    
    def test_md_parser(self, tmp_path):
        from src.ingestion.parsers.md import MarkdownDocumentParser
        md_file = tmp_path / "test.md"
        md_file.write_text("# Title\nContent")
        parser = MarkdownDocumentParser(md_file)
        result = parser.parse()
        assert "# Title" in result["content"]


class TestIntegration:
    """Integration tests."""
    
    def test_mixed_documents(self, tmp_path):
        engine = DocumentIngestionEngine(max_workers=2)
        (tmp_path / "1.txt").write_text("Text")
        (tmp_path / "2.md").write_text("# MD")
        (tmp_path / "3.json").write_text('{}')
        
        files = list(tmp_path.glob("*"))
        results = engine.ingest_batch(files)
        assert len(results) >= 2
    
    def test_directory_ingest(self, tmp_path):
        engine = DocumentIngestionEngine()
        for i in range(3):
            (tmp_path / f"doc{i}.txt").write_text(f"Doc {i}")
        
        results = engine.ingest_directory(tmp_path)
        assert len(results) >= 2
