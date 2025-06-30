# Changelog

## [1.0.0] - 2025-06-30

### Added
- **OCR Support**: Integrated Tesseract OCR for scanned document processing
- **Bulk Upload**: Enhanced upload system to handle multiple files at once
- **Comprehensive Debugging**: Added detailed logging throughout the pipeline
- **Vector Store Fixes**: Resolved ChromaDB filter metadata issues
- **Frontend Improvements**: Fixed data extraction and display issues

### Fixed
- **MinIO Download Issues**: Fixed file locking problems in document download
- **Vector Search**: Resolved "no results found" issue caused by empty filter metadata
- **Frontend Data Parsing**: Fixed nested data structure access in query results
- **ChromaDB Integration**: Ensured proper embedding storage and retrieval

### Technical Improvements
- **Text Extraction**: Enhanced with OCR fallback for scanned documents
- **Embedding Generation**: Consistent model usage across chunking and querying
- **Error Handling**: Better error messages and debugging information
- **Performance**: Optimized pipeline initialization and query execution

### Files Modified
- `rag_system/rag_pipeline.py`: Fixed document download and processing
- `rag_system/rag_components/vector_store.py`: Fixed filter metadata handling
- `rag_system/rag_components/text_extractor.py`: Added OCR capabilities
- `rag_system/views.py`: Enhanced bulk upload and query debugging
- `templates/rag_system/upload.html`: Added bulk upload UI
- `templates/rag_system/query.html`: Fixed frontend data extraction

### Dependencies Added
- `pytesseract`: OCR text extraction
- `pdf2image`: PDF to image conversion for OCR
- `Poppler`: Required for pdf2image (system dependency)

### System Requirements
- Tesseract OCR engine installed
- Poppler utilities installed
- MinIO running on port 9000

### Status
✅ **FULLY FUNCTIONAL**: RAG system now successfully processes and searches legal documents 