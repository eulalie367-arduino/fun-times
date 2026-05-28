# Document Ingestion System

The Document Ingestion System is a comprehensive solution for parsing and extracting content from multiple document formats. It provides automatic file type detection, format-specific parsers, batch processing, and detailed metadata extraction.

## Features

- **Multi-Format Support**: PDF, DOCX, TXT, Markdown (MD), and JSON
- **Automatic File Type Detection**: Uses magic bytes and file extensions
- **Structured Parsing**: Format-specific parsers preserve document structure
- **Metadata Extraction**: Extract titles, authors, dates, word counts, etc.
- **Batch Processing**: Multi-threaded parallel document ingestion
- **Error Handling**: Graceful error handling with detailed error messages
- **Progress Tracking**: Monitor ingestion progress and statistics
- **Directory Ingestion**: Process entire directories recursively

## Supported File Formats

### PDF (.pdf)
- Text extraction from all pages
- Metadata extraction (title, author, creation/modification dates)
- Page count tracking
- Section/heading detection

Requires: `pdfplumber` or `PyPDF2`

```bash
pip install pdfplumber
```

### DOCX (.docx)
- Text extraction from paragraphs
- Table extraction and preservation
- Header/footer extraction
- Heading-based section detection
- Format metadata (styles, comments, categories)

Requires: `python-docx`

```bash
pip install python-docx
```

### Text (.txt)
- Plain text file parsing
- Automatic encoding detection (UTF-8, Latin-1, ASCII, etc.)
- Word and line count
- File size tracking

### Markdown (.md, .markdown)
- Markdown structure preservation
- Header extraction and hierarchy
- YAML frontmatter parsing
- Section detection

### JSON (.json)
- JSON object and array support
- Nested structure handling
- Metadata extraction from common fields
- Nesting depth calculation

## Installation

The document ingestion system is part of the RAG pipeline. Install all dependencies:

```bash
pip install pdfplumber python-docx chardet
```

## Usage

### Basic File Ingestion

```python
from src.ingestion.engine import DocumentIngestionEngine
from pathlib import Path

# Initialize engine
engine = DocumentIngestionEngine(num_workers=4)

# Ingest a single file
result = engine.ingest_file(Path("document.pdf"))

if result.success:
    print(f"Document ingested: {result.file_path}")
    print(f"Content length: {len(result.parsed_document.content)} chars")
    print(f"Metadata: {result.parsed_document.metadata.to_dict()}")
else:
    print(f"Error: {result.error}")
```

### Batch Ingestion

```python
from pathlib import Path

# Ingest multiple files
file_paths = [
    Path("doc1.pdf"),
    Path("doc2.docx"),
    Path("doc3.txt"),
]

results = engine.ingest_batch(file_paths, use_threading=True)

# Process results
successful_docs = engine.get_successful_documents(results)
errors = engine.get_errors(results)

for doc in successful_docs:
    print(f"Title: {doc.metadata.title}")
    print(f"Author: {doc.metadata.author}")
```

### Directory Ingestion

```python
from pathlib import Path

# Ingest all documents in directory
results, stats = engine.ingest_directory(
    Path("documents/"),
    recursive=True,
    pattern="*.{pdf,docx,txt}"
)

# View statistics
print(f"Total processed: {stats['total']}")
print(f"Successful: {stats['successful']}")
print(f"Failed: {stats['failed']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Processing time: {stats['total_processing_time_seconds']:.2f}s")
print(f"Average time per file: {stats['average_processing_time_seconds']:.2f}s")
```

## File Type Detection

The `FileTypeDetector` automatically detects document format:

```python
from src.ingestion.file_types import FileTypeDetector, FileType

detector = FileTypeDetector()

# Detect file type
file_type = detector.detect(Path("document.pdf"))
print(f"Detected type: {file_type.value}")

# Check if supported
if detector.is_supported(Path("document.txt")):
    print("File is supported")

# Get all supported extensions
extensions = detector.get_supported_extensions()
print(f"Supported: {extensions}")
```

## Metadata Extraction

Each parser extracts format-specific metadata:

```python
from src.ingestion.parsers.pdf import PDFParser

parser = PDFParser()
metadata = parser.extract_metadata(Path("document.pdf"))

print(f"Title: {metadata.title}")
print(f"Author: {metadata.author}")
print(f"Created: {metadata.created_date}")
print(f"Pages: {metadata.page_count}")
print(f"Words: {metadata.word_count}")
print(f"Extra: {metadata.extra}")
```

## Custom Parser Implementation

Create custom parsers by extending the `DocumentParser` base class:

```python
from src.ingestion.parsers.base import DocumentParser, ParsedDocument, DocumentMetadata
from pathlib import Path

class CustomParser(DocumentParser):
    """Custom parser for proprietary format."""

    def parse(self, file_path: Path) -> ParsedDocument:
        """Parse custom format."""
        # Parse logic here
        content = "extracted content"
        metadata = DocumentMetadata(
            title="Document Title",
            word_count=len(content.split())
        )
        return ParsedDocument(content=content, metadata=metadata)

    def extract_metadata(self, file_path: Path) -> DocumentMetadata:
        """Extract metadata."""
        # Metadata extraction logic
        return DocumentMetadata()
```

## Error Handling

The system provides detailed error information:

```python
result = engine.ingest_file(Path("document.pdf"))

if not result.success:
    print(f"Ingestion failed: {result.error}")
    print(f"Duration: {result.duration_seconds}s")
    print(f"File: {result.file_path}")
    print(f"File type detected: {result.file_type.value}")
```

## Configuration

Configure the ingestion engine through application settings:

```python
from src.config import get_settings

settings = get_settings()

# Relevant settings
batch_processing = settings.batch_processing  # Enable/disable batch
thread_pool_size = settings.thread_pool_size  # Worker threads
chunk_size = settings.chunk_size  # For chunking parsed content
```

## Performance Tuning

### Number of Workers

```python
# For CPU-bound parsing (4-8 workers typical)
engine = DocumentIngestionEngine(num_workers=4)

# For I/O-bound operations (more workers acceptable)
engine = DocumentIngestionEngine(num_workers=8)
```

### Sequential vs Parallel Processing

```python
# Sequential processing - useful for limited memory
results = engine.ingest_batch(files, use_threading=False)

# Parallel processing - faster for many files
results = engine.ingest_batch(files, use_threading=True)
```

## Logging

The system uses structured logging:

```python
from src.logger import get_logger

logger = get_logger("document_ingestion")

# Logs are written to:
# - Console (default)
# - Log file (configured in settings)
# - Structured JSON format for parsing
```

Example log output:

```json
{
  "event": "ingest_success",
  "file": "document.pdf",
  "file_type": "pdf",
  "duration_seconds": 2.34,
  "content_length": 15234
}
```

## Troubleshooting

### "ImportError: Neither pdfplumber nor PyPDF2 available"

Install PDF parser:
```bash
pip install pdfplumber
```

### "ImportError: python-docx not available"

Install DOCX parser:
```bash
pip install python-docx
```

### "File encoding detection failed"

The system falls back to UTF-8. For files with unusual encoding, manually specify:

```python
# Create a text file with explicit encoding
from src.ingestion.parsers.txt import TextParser

parser = TextParser()
# Internally detects encoding automatically
result = parser.parse(Path("file.txt"))
```

### "Unsupported file type"

Check file extension and magic bytes. Ensure file is not corrupted:

```python
from src.ingestion.file_types import FileTypeDetector

detector = FileTypeDetector()
file_type = detector.detect(Path("file.xyz"))

if file_type == FileType.UNKNOWN:
    print("File type not supported")
    print(f"Supported types: {detector.get_supported_extensions()}")
```

## API Reference

### DocumentIngestionEngine

Main orchestrator class.

**Methods:**

- `ingest_file(file_path: Path) -> IngestionResult`
  - Ingest a single document

- `ingest_batch(file_paths: List[Path], use_threading: bool = True) -> List[IngestionResult]`
  - Ingest multiple documents with optional parallelization

- `ingest_directory(directory: Path, recursive: bool = True, pattern: str = "*") -> Tuple[List[IngestionResult], Dict[str, int]]`
  - Ingest all documents in a directory

- `get_successful_documents(results: List[IngestionResult]) -> List[ParsedDocument]`
  - Extract successfully parsed documents from results

- `get_errors(results: List[IngestionResult]) -> Dict[str, str]`
  - Extract errors from results

### FileTypeDetector

Automatic file type detection.

**Methods:**

- `detect(file_path: Path) -> FileType`
  - Detect file type using magic bytes and extensions

- `is_supported(file_path: Path) -> bool`
  - Check if file type is supported

- `get_supported_extensions() -> List[str]`
  - Get list of supported file extensions

### DocumentParser

Abstract base class for all parsers.

**Methods:**

- `parse(file_path: Path) -> ParsedDocument`
  - Parse document and extract content and metadata (abstract)

- `extract_metadata(file_path: Path) -> DocumentMetadata`
  - Extract metadata from document (abstract)

- `validate(file_path: Path) -> bool`
  - Validate file can be parsed

- `get_parser_info() -> Dict[str, Any]`
  - Get information about parser

### ParsedDocument

Result of parsing a document.

**Attributes:**

- `content: str` - Extracted text content
- `metadata: DocumentMetadata` - Document metadata
- `sections: List[str]` - Document sections/structure
- `raw_content: Optional[str]` - Raw format-specific content

**Methods:**

- `get_summary() -> Dict[str, Any]`
  - Get summary of parsed document

### DocumentMetadata

Extracted document metadata.

**Attributes:**

- `title: Optional[str]` - Document title
- `author: Optional[str]` - Document author
- `created_date: Optional[datetime]` - Creation date
- `modified_date: Optional[datetime]` - Last modified date
- `language: Optional[str]` - Document language
- `page_count: Optional[int]` - Number of pages (for paginated formats)
- `word_count: Optional[int]` - Total word count
- `file_size: Optional[int]` - File size in bytes
- `file_path: Optional[str]` - Original file path
- `extra: Dict[str, Any]` - Format-specific metadata

**Methods:**

- `to_dict() -> Dict[str, Any]`
  - Convert metadata to dictionary

### IngestionResult

Result of ingesting a single document.

**Attributes:**

- `file_path: str` - Path to ingested file
- `file_type: FileType` - Detected file type
- `success: bool` - Whether ingestion was successful
- `parsed_document: Optional[ParsedDocument]` - Parsed document (if successful)
- `error: Optional[str]` - Error message (if failed)
- `duration_seconds: float` - Processing duration
- `timestamp: datetime` - When ingestion occurred

**Methods:**

- `to_dict() -> Dict[str, Any]`
  - Convert result to dictionary

## Examples

### Example 1: Process Document Folder

```python
from src.ingestion.engine import DocumentIngestionEngine
from pathlib import Path

engine = DocumentIngestionEngine(num_workers=4)

# Process all documents in folder
results, stats = engine.ingest_directory(
    Path("documents"),
    recursive=True
)

print(f"Processed {stats['successful']} documents successfully")
print(f"Failed: {stats['failed']}")
print(f"Time: {stats['total_processing_time_seconds']:.1f}s")

# Get successful documents
documents = engine.get_successful_documents(results)

for doc in documents:
    print(f"\n{doc.metadata.title}")
    print(f"Author: {doc.metadata.author}")
    print(f"Words: {doc.metadata.word_count}")
    print(f"Sections: {len(doc.sections)}")
```

### Example 2: Extract Metadata Only

```python
from src.ingestion.parsers.pdf import PDFParser
from pathlib import Path

parser = PDFParser()

# Extract metadata without processing full content
metadata = parser.extract_metadata(Path("document.pdf"))

# Use metadata for indexing
index_entry = {
    "title": metadata.title,
    "author": metadata.author,
    "date": metadata.created_date,
    "pages": metadata.page_count,
}
```

### Example 3: Selective Ingestion with Error Handling

```python
from src.ingestion.engine import DocumentIngestionEngine
from pathlib import Path

engine = DocumentIngestionEngine()

files = list(Path("documents").glob("*.pdf"))

results = engine.ingest_batch(files, use_threading=True)

# Separate successful and failed
successful = engine.get_successful_documents(results)
errors = engine.get_errors(results)

print(f"Successfully ingested: {len(successful)}")
for file_path, error in errors.items():
    print(f"Failed {file_path}: {error}")

# Process successful documents
for doc in successful:
    # Index document
    # Extract sections
    # Create chunks
    pass
```

## Best Practices

1. **Use batch processing** for multiple files to leverage parallelization
2. **Configure appropriate worker count** based on system resources
3. **Handle errors gracefully** - check result.success before accessing parsed_document
4. **Extract metadata first** if you only need document information
5. **Monitor logs** for ingestion progress and errors
6. **Test with sample files** before processing large batches
7. **Validate file integrity** before ingestion (check file size, modification date)
8. **Clean up temporary files** after processing if needed

## Integration with RAG Pipeline

The Document Ingestion System integrates with the RAG pipeline:

```python
from src.ingestion.engine import DocumentIngestionEngine
from src.chunking import create_chunks  # Future component
from src.embeddings import EmbeddingGenerator

# 1. Ingest documents
engine = DocumentIngestionEngine()
results = engine.ingest_batch(document_paths)
documents = engine.get_successful_documents(results)

# 2. Create chunks (next step in pipeline)
chunks = []
for doc in documents:
    doc_chunks = create_chunks(
        doc.content,
        metadata=doc.metadata.to_dict()
    )
    chunks.extend(doc_chunks)

# 3. Generate embeddings (existing component)
embedder = EmbeddingGenerator()
embeddings = embedder.generate_batch([c.text for c in chunks])

# 4. Store in vector database (existing component)
# ... store embeddings and chunks
```

## Performance Metrics

Typical ingestion performance (varies by system and document complexity):

- **Plain text**: ~100-500 files/second per worker
- **Markdown**: ~50-200 files/second per worker
- **JSON**: ~50-200 files/second per worker
- **PDF**: ~1-10 files/second per worker (varies by page count)
- **DOCX**: ~5-20 files/second per worker

## Future Enhancements

Potential future additions:

- OCR for image-heavy PDFs
- Multi-language support
- Audio/video metadata extraction
- Database document parsing
- Cloud storage integration
- Streaming document processing
- Format conversion
- Document fingerprinting
