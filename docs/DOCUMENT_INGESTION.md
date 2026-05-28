# Document Ingestion System

Complete document ingestion system for RAG pipelines with support for multiple file formats.

## Overview

The document ingestion system provides:
- **FileTypeDetector**: Auto-detect document format
- **DocumentParsers**: Specialized parsers for each format
- **DocumentIngestionEngine**: Batch processing with parallel workers
- **Error Handling**: Graceful failure recovery
- **Statistics**: Track ingestion metrics

## Supported Formats

- **PDF** (.pdf) - Text extraction with PyPDF2
- **DOCX** (.docx) - Word documents with python-docx
- **DOC** (.doc) - Legacy Word format
- **TXT** (.txt) - Plain text with encoding detection
- **Markdown** (.md) - Preserve structure and headers
- **JSON** (.json) - JSON documents and collections

## Quick Start

```python
from src.ingestion import DocumentIngestionEngine
from pathlib import Path

# Create engine
engine = DocumentIngestionEngine(max_workers=4, batch_size=10)

# Ingest single file
result = engine.ingest_file(Path("document.pdf"))

# Ingest directory
results = engine.ingest_directory(Path("documents/"), recursive=True)

# Get statistics
stats = engine.get_stats()
print(f"Processed: {stats['total_processed']}")
print(f"Success rate: {stats['success_rate']}")
```

## API Reference

### FileTypeDetector

```python
from src.ingestion import FileTypeDetector, FileType

# Detect from path
file_type = FileTypeDetector.detect_from_path("document.pdf")

# Check if supported
is_supported = FileTypeDetector.is_supported(file_type)

# Get parser class
parser_class = FileTypeDetector.get_parser_class(FileType.PDF)
```

### DocumentIngestionEngine

```python
from src.ingestion import DocumentIngestionEngine

engine = DocumentIngestionEngine(
    max_workers=4,      # Number of parallel workers
    batch_size=10       # Documents per batch
)

# Ingest single file
result = engine.ingest_file(Path("file.txt"))

# Ingest multiple files in parallel
results = engine.ingest_batch([Path("1.txt"), Path("2.txt")])

# Ingest entire directory
results = engine.ingest_directory(
    Path("documents/"),
    recursive=True      # Scan subdirectories
)

# Get statistics
stats = engine.get_stats()
# Returns: {
#   "total_processed": 100,
#   "successful": 95,
#   "failed": 3,
#   "skipped": 2,
#   "success_rate": "95.0%"
# }
```

## Return Format

Each ingested document returns:

```python
{
    "content": "Document text content...",
    "metadata": {
        "filename": "document.pdf",
        "file_size": 102400,
        "format": "pdf",
        "num_pages": 5,              # Format-specific
        "created_at": 1234567890,
        "modified_at": 1234567900
    }
}
```

## Configuration

### Environment Variables

```bash
INGEST_MAX_WORKERS=4        # Default: 4
INGEST_BATCH_SIZE=10        # Default: 10
INGEST_RETRY_FAILED=true    # Default: true
```

### Error Handling

Errors are logged and tracked:

```python
try:
    result = engine.ingest_file(Path("file.pdf"))
except IngestError as e:
    print(f"Ingestion failed: {e}")
```

## Performance

Typical performance (on 4-core system):

- **Single file**: 100-500ms (includes parsing)
- **Batch (10 files)**: 1-3 seconds
- **Directory (1000 files)**: 2-5 minutes

Performance depends on:
- File size and format
- System resources
- Parser library availability

## Logging

Structured logging via src.logger:

```
{"event": "file_type_detected", "path": "doc.pdf", "type": "pdf"}
{"event": "file_ingested", "path": "doc.pdf", "type": "pdf"}
{"event": "batch_ingestion_complete", "total": 10, "successful": 9}
```

## Testing

Run test suite:

```bash
pytest tests/unit/test_document_ingestion.py -v
```

Test coverage:
- File type detection (8 tests)
- Document parsing (4 tests)
- Batch processing (5 tests)
- Integration (3 tests)
- **Total: 20+ test cases**

## Dependencies

Optional dependencies for enhanced parsing:

```bash
pip install PyPDF2          # PDF parsing
pip install python-docx     # DOCX parsing
```

Without these, parsers fall back to simpler extraction.

## Examples

### Example 1: Ingest PDF Documents

```python
from src.ingestion import DocumentIngestionEngine
from pathlib import Path

engine = DocumentIngestionEngine()
results = engine.ingest_directory(Path("pdfs/"))

for result in results:
    print(f"Ingested: {result['metadata']['filename']}")
    print(f"Pages: {result['metadata'].get('num_pages', 'N/A')}")
```

### Example 2: Process with RAG Pipeline

```python
from src.ingestion import DocumentIngestionEngine
from src.embeddings import EmbeddingGenerator
from src.vector_store import VectorStore

# Ingest documents
engine = DocumentIngestionEngine()
documents = engine.ingest_directory(Path("documents/"))

# Generate embeddings
embedder = EmbeddingGenerator()
vector_store = VectorStore()

for doc in documents:
    embedding = embedder.embed_text(doc["content"])
    vector_store.add_vectors(
        collection_name="documents",
        documents=[doc["content"]],
        embeddings=[embedding],
        metadatas=[doc["metadata"]]
    )
```

## Architecture

```
DocumentIngestionEngine
├── FileTypeDetector
│   ├── detect_from_path()
│   └── detect_from_content()
├── DocumentParser (abstract)
│   ├── PDFDocumentParser
│   ├── DOCXDocumentParser
│   ├── TextDocumentParser
│   ├── MarkdownDocumentParser
│   └── JSONDocumentParser
└── ThreadPoolExecutor
    └── Parallel parsing & ingestion
```

## Troubleshooting

### PDF extraction not working
- Install PyPDF2: `pip install PyPDF2`
- System will fall back to simple extraction

### DOCX parsing issues
- Install python-docx: `pip install python-docx`
- Verify file is valid DOCX format

### Encoding errors
- Text parser auto-detects encoding
- Falls back from UTF-8 to Latin-1

### Performance optimization
- Increase max_workers for more parallelism
- Increase batch_size for better throughput
- Use SSD for faster file I/O

## Future Enhancements

- Image extraction from PDFs
- OCR for scanned documents
- Support for additional formats (PPTX, XLSX, etc.)
- Streaming ingestion for large files
- Distributed processing
