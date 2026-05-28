"""Comprehensive tests for document ingestion system."""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from src.ingestion.file_types import FileType, FileTypeDetector
from src.ingestion.parsers.base import DocumentMetadata, ParsedDocument
from src.ingestion.parsers.pdf import PDFParser
from src.ingestion.parsers.docx import DOCXParser
from src.ingestion.parsers.txt import TextParser
from src.ingestion.parsers.md import MarkdownParser
from src.ingestion.parsers.json import JSONParser
from src.ingestion.engine import DocumentIngestionEngine, IngestionResult


class TestFileTypeDetector:
    """Test FileTypeDetector class."""

    def setup_method(self):
        """Setup for each test."""
        self.detector = FileTypeDetector()

    def test_detect_pdf_by_magic_bytes(self):
        """Test PDF detection by magic bytes."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\n%test content')
            temp_path = f.name

        try:
            file_type = self.detector.detect(temp_path)
            assert file_type == FileType.PDF
        finally:
            Path(temp_path).unlink()

    def test_detect_txt_by_extension(self):
        """Test TXT detection by extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'Plain text content')
            temp_path = f.name

        try:
            file_type = self.detector.detect(temp_path)
            assert file_type == FileType.TXT
        finally:
            Path(temp_path).unlink()

    def test_detect_json_by_magic_bytes(self):
        """Test JSON detection by magic bytes."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            f.write(b'{"key": "value"}')
            temp_path = f.name

        try:
            file_type = self.detector.detect(temp_path)
            assert file_type == FileType.JSON
        finally:
            Path(temp_path).unlink()

    def test_detect_md_by_extension(self):
        """Test Markdown detection by extension."""
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            f.write(b'# Heading\nContent')
            temp_path = f.name

        try:
            file_type = self.detector.detect(temp_path)
            assert file_type == FileType.MD
        finally:
            Path(temp_path).unlink()

    def test_detect_unknown_type(self):
        """Test detection of unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'Unknown content')
            temp_path = f.name

        try:
            file_type = self.detector.detect(temp_path)
            assert file_type == FileType.UNKNOWN
        finally:
            Path(temp_path).unlink()

    def test_detect_nonexistent_file(self):
        """Test detection of nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            self.detector.detect('/nonexistent/path/file.txt')

    def test_is_supported(self):
        """Test is_supported method."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'content')
            temp_path = f.name

        try:
            assert self.detector.is_supported(temp_path) is True
        finally:
            Path(temp_path).unlink()

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        extensions = self.detector.get_supported_extensions()
        assert '.txt' in extensions
        assert '.json' in extensions
        assert '.md' in extensions
        assert '.pdf' in extensions
        assert '.docx' in extensions


class TestTextParser:
    """Test TextParser class."""

    def setup_method(self):
        """Setup for each test."""
        self.parser = TextParser()

    def test_parse_simple_text_file(self):
        """Test parsing simple text file."""
        with tempfile.NamedTemporaryFile(
            suffix='.txt', mode='w', delete=False, encoding='utf-8'
        ) as f:
            f.write("Hello World\nThis is a test")
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            assert result.content == "Hello World\nThis is a test"
            assert result.metadata.word_count > 0
        finally:
            Path(temp_path).unlink()

    def test_parse_text_with_different_encoding(self):
        """Test parsing text file with different encoding."""
        with tempfile.NamedTemporaryFile(
            suffix='.txt', mode='w', delete=False, encoding='latin-1'
        ) as f:
            f.write("Café content")
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            assert 'Caf' in result.content
        finally:
            Path(temp_path).unlink()

    def test_text_metadata_extraction(self):
        """Test metadata extraction from text file."""
        with tempfile.NamedTemporaryFile(
            suffix='.txt', mode='w', delete=False
        ) as f:
            f.write("First line\nSecond line")
            temp_path = f.name

        try:
            metadata = self.parser.extract_metadata(temp_path)
            assert metadata.file_path == temp_path
            assert metadata.word_count > 0
        finally:
            Path(temp_path).unlink()

    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file raises error."""
        with pytest.raises(IOError):
            self.parser.parse('/nonexistent/file.txt')


class TestMarkdownParser:
    """Test MarkdownParser class."""

    def setup_method(self):
        """Setup for each test."""
        self.parser = MarkdownParser()

    def test_parse_markdown_with_headers(self):
        """Test parsing markdown with headers."""
        with tempfile.NamedTemporaryFile(
            suffix='.md', mode='w', delete=False
        ) as f:
            f.write("# Main Title\n## Section 1\nContent here\n## Section 2\n")
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            assert "Main Title" in result.content
            assert len(result.sections) > 0
        finally:
            Path(temp_path).unlink()

    def test_extract_markdown_sections(self):
        """Test extracting sections from markdown."""
        with tempfile.NamedTemporaryFile(
            suffix='.md', mode='w', delete=False
        ) as f:
            f.write("# Title\n## Section A\n### Subsection\n## Section B\n")
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            assert len(result.sections) > 0
            # Should contain extracted headers
            assert any('Section' in s for s in result.sections)
        finally:
            Path(temp_path).unlink()

    def test_parse_markdown_with_frontmatter(self):
        """Test parsing markdown with YAML frontmatter."""
        with tempfile.NamedTemporaryFile(
            suffix='.md', mode='w', delete=False
        ) as f:
            f.write(
                "---\ntitle: Test Document\nauthor: Test Author\n---\n"
                "# Content\nBody"
            )
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            assert result.metadata.title == "Test Document"
            assert result.metadata.author == "Test Author"
        finally:
            Path(temp_path).unlink()


class TestJSONParser:
    """Test JSONParser class."""

    def setup_method(self):
        """Setup for each test."""
        self.parser = JSONParser()

    def test_parse_json_object(self):
        """Test parsing JSON object."""
        with tempfile.NamedTemporaryFile(
            suffix='.json', mode='w', delete=False
        ) as f:
            json.dump({"key": "value", "number": 42}, f)
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            assert result.content is not None
            assert result.raw_content is not None
            assert "key" in result.content or "key" in result.raw_content
        finally:
            Path(temp_path).unlink()

    def test_parse_json_array(self):
        """Test parsing JSON array."""
        with tempfile.NamedTemporaryFile(
            suffix='.json', mode='w', delete=False
        ) as f:
            json.dump([{"id": 1}, {"id": 2}], f)
            temp_path = f.name

        try:
            result = self.parser.parse(temp_path)
            assert result.metadata.extra.get('root_type') == 'array'
            assert result.metadata.extra.get('item_count') == 2
        finally:
            Path(temp_path).unlink()

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        with tempfile.NamedTemporaryFile(
            suffix='.json', mode='w', delete=False
        ) as f:
            f.write("{invalid json")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                self.parser.parse(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_json_metadata_extraction(self):
        """Test metadata extraction from JSON."""
        with tempfile.NamedTemporaryFile(
            suffix='.json', mode='w', delete=False
        ) as f:
            json.dump({"title": "Test", "data": [1, 2, 3]}, f)
            temp_path = f.name

        try:
            metadata = self.parser.extract_metadata(temp_path)
            assert metadata.title == "Test"
        finally:
            Path(temp_path).unlink()


class TestDocumentMetadata:
    """Test DocumentMetadata class."""

    def test_metadata_creation(self):
        """Test creating metadata object."""
        metadata = DocumentMetadata(
            title="Test",
            author="Author",
            word_count=100,
        )
        assert metadata.title == "Test"
        assert metadata.author == "Author"

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = DocumentMetadata(
            title="Test",
            word_count=50,
        )
        result_dict = metadata.to_dict()
        assert result_dict['title'] == "Test"
        assert result_dict['word_count'] == 50

    def test_metadata_with_dates(self):
        """Test metadata with date fields."""
        now = datetime.now()
        metadata = DocumentMetadata(
            created_date=now,
            modified_date=now,
        )
        result_dict = metadata.to_dict()
        assert 'created_date' in result_dict
        assert 'modified_date' in result_dict


class TestParsedDocument:
    """Test ParsedDocument class."""

    def test_parsed_document_creation(self):
        """Test creating ParsedDocument."""
        metadata = DocumentMetadata(title="Test")
        doc = ParsedDocument(content="Content", metadata=metadata)
        assert doc.content == "Content"
        assert doc.metadata.title == "Test"

    def test_parsed_document_summary(self):
        """Test getting summary from ParsedDocument."""
        metadata = DocumentMetadata(title="Test")
        doc = ParsedDocument(content="Test content", metadata=metadata)
        summary = doc.get_summary()
        assert 'content_length' in summary
        assert summary['content_length'] > 0


class TestIngestionResult:
    """Test IngestionResult class."""

    def test_successful_result(self):
        """Test creating successful ingestion result."""
        result = IngestionResult(
            file_path="/test/file.txt",
            file_type=FileType.TXT,
            success=True,
        )
        assert result.success is True
        assert result.file_type == FileType.TXT

    def test_failed_result(self):
        """Test creating failed ingestion result."""
        result = IngestionResult(
            file_path="/test/file.txt",
            file_type=FileType.UNKNOWN,
            success=False,
            error="File not found",
        )
        assert result.success is False
        assert result.error == "File not found"

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = IngestionResult(
            file_path="/test/file.txt",
            file_type=FileType.TXT,
            success=True,
            duration_seconds=1.23,
        )
        result_dict = result.to_dict()
        assert result_dict['file_path'] == "/test/file.txt"
        assert result_dict['success'] is True


class TestDocumentIngestionEngine:
    """Test DocumentIngestionEngine class."""

    def setup_method(self):
        """Setup for each test."""
        self.engine = DocumentIngestionEngine(num_workers=2)

    def test_engine_initialization(self):
        """Test engine initialization."""
        assert self.engine.num_workers == 2
        assert len(self.engine.parsers) == 5  # 5 parser types

    def test_ingest_single_text_file(self):
        """Test ingesting single text file."""
        with tempfile.NamedTemporaryFile(
            suffix='.txt', mode='w', delete=False
        ) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            result = self.engine.ingest_file(temp_path)
            assert result.success is True
            assert result.file_type == FileType.TXT
            assert result.parsed_document is not None
        finally:
            Path(temp_path).unlink()

    def test_ingest_unsupported_file(self):
        """Test ingesting unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'content')
            temp_path = f.name

        try:
            result = self.engine.ingest_file(temp_path)
            assert result.success is False
            assert result.error is not None
        finally:
            Path(temp_path).unlink()

    def test_ingest_batch_sequential(self):
        """Test batch ingestion sequentially."""
        files = []
        try:
            # Create test files
            for i in range(3):
                with tempfile.NamedTemporaryFile(
                    suffix='.txt', mode='w', delete=False
                ) as f:
                    f.write(f"Content {i}")
                    files.append(f.name)

            results = self.engine.ingest_batch(
                [Path(f) for f in files],
                use_threading=False
            )
            assert len(results) == 3
            assert all(r.success for r in results)

        finally:
            for f in files:
                Path(f).unlink()

    def test_ingest_batch_parallel(self):
        """Test batch ingestion in parallel."""
        files = []
        try:
            # Create test files
            for i in range(3):
                with tempfile.NamedTemporaryFile(
                    suffix='.txt', mode='w', delete=False
                ) as f:
                    f.write(f"Content {i}")
                    files.append(f.name)

            results = self.engine.ingest_batch(
                [Path(f) for f in files],
                use_threading=True
            )
            assert len(results) == 3
            assert all(r.success for r in results)

        finally:
            for f in files:
                Path(f).unlink()

    def test_ingest_directory(self):
        """Test ingesting entire directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)

            # Create test files
            for i in range(2):
                with open(temp_dir / f"file{i}.txt", 'w') as f:
                    f.write(f"Content {i}")

            results, stats = self.engine.ingest_directory(
                temp_dir,
                recursive=False
            )
            assert len(results) == 2
            assert stats['successful'] == 2
            assert stats['failed'] == 0

    def test_compute_statistics(self):
        """Test statistics computation."""
        results = [
            IngestionResult(
                file_path=f"/test/file{i}.txt",
                file_type=FileType.TXT,
                success=i > 0,
                error="Error" if i == 0 else None,
                duration_seconds=0.5,
            )
            for i in range(3)
        ]

        stats = self.engine._compute_statistics(results)
        assert stats['total'] == 3
        assert stats['successful'] == 2
        assert stats['failed'] == 1

    def test_get_successful_documents(self):
        """Test extracting successful documents."""
        with tempfile.NamedTemporaryFile(
            suffix='.txt', mode='w', delete=False
        ) as f:
            f.write("Content")
            temp_path = f.name

        try:
            results = self.engine.ingest_batch([Path(temp_path)])
            docs = self.engine.get_successful_documents(results)
            assert len(docs) == 1
            assert docs[0].content == "Content"
        finally:
            Path(temp_path).unlink()

    def test_get_errors(self):
        """Test extracting errors from results."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'content')
            temp_path = f.name

        try:
            results = self.engine.ingest_batch([Path(temp_path)])
            errors = self.engine.get_errors(results)
            assert len(errors) > 0
            assert temp_path in errors
        finally:
            Path(temp_path).unlink()


class TestIntegration:
    """Integration tests for document ingestion."""

    def test_full_ingestion_workflow(self):
        """Test complete ingestion workflow."""
        engine = DocumentIngestionEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)

            # Create various file types
            txt_file = temp_dir / "test.txt"
            txt_file.write_text("Plain text content")

            md_file = temp_dir / "test.md"
            md_file.write_text("# Markdown\nContent here")

            json_file = temp_dir / "test.json"
            json_file.write_text('{"key": "value"}')

            # Ingest directory
            results, stats = engine.ingest_directory(temp_dir)

            # Verify results
            assert stats['successful'] > 0
            assert stats['total'] == 3

    def test_error_recovery(self):
        """Test error handling and recovery."""
        engine = DocumentIngestionEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)

            # Create mix of valid and invalid files
            valid_file = temp_dir / "valid.txt"
            valid_file.write_text("Content")

            invalid_file = temp_dir / "invalid.xyz"
            invalid_file.write_bytes(b"content")

            # Ingest - should handle both
            results, stats = engine.ingest_directory(temp_dir)

            # Should process valid file successfully
            assert stats['successful'] >= 1
