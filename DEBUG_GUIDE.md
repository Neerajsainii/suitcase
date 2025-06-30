# RAG System Debug Guide

This guide explains how to use the comprehensive debug statements added to the RAG system to verify each step of the document processing pipeline.

## 🎯 Overview

The RAG system now includes detailed debug output that will help you verify:
- ✅ File upload to MinIO
- ✅ Text extraction from PDFs
- ✅ Text chunking with metadata
- ✅ Embedding generation
- ✅ Vector storage in ChromaDB
- ✅ Database storage of chunks
- ✅ Query processing and search

## 🚀 Getting Started

### 1. Run the Debug Test Script

First, test your system with the debug test script:

```bash
python test_rag_debug.py
```

This will test all components and show you detailed debug output for each step.

### 2. Start the Django Server

```bash
python manage.py runserver
```

### 3. Upload a Document

Go to the upload page and upload a PDF document. You'll see detailed debug output in the console showing:

```
==================================================
🌐 UPLOAD VIEW CALLED
📋 Method: POST
👤 User: your_username
==================================================
📤 Processing POST request
📋 Request FILES: ['file']
📋 Request POST: ['title', 'csrfmiddlewaretoken']
📁 File object: <InMemoryUploadedFile: document.pdf>
📝 Title: My Legal Document
✅ File received: document.pdf, Size: 123456, Type: application/pdf
🔧 Initializing RAG pipeline...
✅ RAG pipeline initialized in 2.345s
📤 Uploading to MinIO...
✅ MinIO upload successful: abc123-def456/document.pdf
⏱️ MinIO upload time: 1.234s
💾 Creating document record...
✅ Document created with ID: 1
⏱️ Database creation time: 0.123s
🔄 Starting background processing...
✅ Background processing thread started
✅ Upload view completed successfully in 3.789s
📊 Summary:
   - Pipeline init: 2.345s
   - MinIO upload: 1.234s
   - DB creation: 0.123s
   - Total: 3.789s
```

### 4. Monitor Document Processing

In the background thread, you'll see the complete processing pipeline:

```
============================================================
📄 STARTING DOCUMENT PROCESSING: My Legal Document
📁 File: document.pdf
🆔 Document ID: 1
📊 File size: 123456 bytes
============================================================
🔄 Updating document status to 'processing'...
✅ Document status updated

📥 STEP 1: Downloading document from MinIO...
📥 Starting file download: abc123-def456/document.pdf -> /tmp/tmp123.pdf
🔍 Checking if object 'abc123-def456/document.pdf' exists...
📊 Object info: Size=123456 bytes, Last modified=2024-01-01 12:00:00
📥 Downloading from MinIO bucket 'documents'...
✅ File downloaded successfully in 0.567s
📊 Download summary: abc123-def456/document.pdf -> /tmp/tmp123.pdf
✅ Download verified: 123456 bytes saved
✅ Download completed in 0.567s
📁 Temporary file: /tmp/tmp123.pdf

📝 STEP 2: Extracting text from PDF...
📄 Starting PDF text extraction: /tmp/tmp123.pdf
📖 Opening PDF file: /tmp/tmp123.pdf
✅ PDF opened successfully, 5 pages found
📋 Extracting PDF metadata...
📋 Metadata extracted: {'num_pages': 5, 'title': 'Legal Document', ...}
📝 Extracting text from pages...
📄 Processing page 1/5
✅ Page 1: 1234 characters extracted
📄 Processing page 2/5
✅ Page 2: 2345 characters extracted
...
✅ Text extraction completed in 1.234s
📊 Summary: 5 pages with text, 12345 total characters

📋 STEP 3: Updating document metadata...
✅ Document metadata updated: 5 pages

✂️ STEP 4: Chunking text...
🔗 Combining text from all pages...
✅ Combined text from 5 pages, total length: 12345 characters
✂️ Starting text chunking process...
📊 Input text length: 12345 characters
📋 Metadata: {'document_id': 1, 'document_title': 'My Legal Document', ...}
🧹 Cleaning and normalizing text...
✅ Text cleaned, new length: 12340 characters
🔤 Splitting text into sentences...
✅ Split into 45 sentences
🔀 Processing sentences with chunk size: 1000
📦 Created chunk 1: 987 characters, sentences 0-12
🔄 Starting new chunk with 200 characters overlap
📦 Created chunk 2: 1023 characters, sentences 10-25
...
✅ Chunking completed in 0.345s
📊 Summary: 12 chunks created, 12340 total characters
  Chunk 1: 987 chars, metadata keys: ['text', 'chunk_id', 'document_id', ...]
  Chunk 2: 1023 chars, metadata keys: ['text', 'chunk_id', 'document_id', ...]
  ...

🧠 STEP 5: Generating embeddings...
🧠 Starting chunk embedding generation for 12 chunks...
📝 Extracted 12 texts from chunks
⚡ Generating embeddings...
🧠 Generating embeddings for 12 texts...
⚡ Processing 12 texts through model...
✅ Generated 12 embeddings in 2.345s
📊 Embedding dimension: 768
📈 Average embedding norm: 0.9876
🔗 Adding embeddings to chunks...
✅ Chunk 1: Added 768-dim embedding
✅ Chunk 2: Added 768-dim embedding
...
✅ Chunk embedding generation completed in 2.456s
📊 Summary: 12/12 chunks successfully embedded

💾 STEP 6: Storing in vector database...
💾 Starting to add 12 chunks to vector store...
📋 Preparing chunk data for ChromaDB...
📦 Prepared chunk 1: ID=abc12345..., text=987 chars, embedding=768 dims, metadata keys=['chunk_id', 'document_id', ...]
📦 Prepared chunk 2: ID=def67890..., text=1023 chars, embedding=768 dims, metadata keys=['chunk_id', 'document_id', ...]
...
✅ Prepared 12 chunks for storage
📊 Data summary: 12 texts, 12 embeddings, 12 metadata objects
💾 Adding chunks to ChromaDB collection...
✅ Successfully added 12 chunks to vector store in 0.234s
📊 Vector store now contains 12 total documents
✅ Vector storage completed in 0.234s
📊 Stored 12 chunks in vector database

💾 STEP 7: Saving chunks to database...
💾 Saving 12 chunks to database...
📦 Saving chunk 1/12: ID=0, Vector ID=abc12345...
✅ Chunk 1 saved successfully
📦 Saving chunk 2/12: ID=1, Vector ID=def67890...
✅ Chunk 2 saved successfully
...
✅ Successfully saved 12/12 chunks to database in 0.123s

✅ FINALIZING: Updating document status...
============================================================
🎉 DOCUMENT PROCESSING COMPLETED SUCCESSFULLY!
📄 Document: My Legal Document
⏱️ Total processing time: 4.567s
📊 Summary:
   - Pages: 5
   - Chunks: 12
   - Text length: 12345 characters
   - Vector IDs: 12
============================================================

🧹 Cleaning up temporary file...
✅ Temporary file cleaned: /tmp/tmp123.pdf
```

### 5. Test Querying

When you perform a query, you'll see:

```
==================================================
🔍 QUERY API VIEW CALLED
👤 User: your_username
==================================================
📝 Query: 'legal contract terms'
📊 Requesting 5 results
🔧 Initializing RAG pipeline for query...
✅ RAG pipeline initialized in 1.234s
🔍 Performing RAG query...

🔍 STARTING RAG QUERY
📝 Query: 'legal contract terms'
📊 Requesting 5 results

🧠 Generating query embedding...
🧠 Generating embedding for text: 'legal contract terms'...
✅ Single embedding generated in 0.123s
📊 Embedding dimension: 768
📈 Embedding norm: 0.9876
✅ Query embedding generated in 0.123s
📊 Embedding dimension: 768

🔍 Searching vector store...
🔍 Searching vector store for 5 results...
✅ Vector search completed in 0.045s
📊 Found 5 results

📊 Calculating similarity scores...
  Result 1: Similarity = 0.8765, Distance = 0.1235
  Result 2: Similarity = 0.7654, Distance = 0.2346
  Result 3: Similarity = 0.6543, Distance = 0.3457
  Result 4: Similarity = 0.5432, Distance = 0.4568
  Result 5: Similarity = 0.4321, Distance = 0.5679

✅ QUERY COMPLETED in 0.234s
📊 Summary: 5 results, 0.234s total time
✅ Query completed in 0.234s
💾 Logging query...
✅ Query logged in 0.012s
🔗 Linking retrieved chunks to log...
✅ Linked 5 chunks to query log in 0.023s
✅ Query API completed successfully in 1.456s
📊 Summary:
   - Pipeline init: 1.234s
   - Query execution: 0.234s
   - Query logging: 0.012s
   - Chunk linking: 0.023s
   - Total: 1.456s
   - Results: 5
```

## 🔍 Debug Output Categories

### 📤 Upload Process
- File validation and metadata
- MinIO upload progress
- Database record creation
- Background processing initiation

### 📄 Document Processing
- **Step 1**: MinIO download verification
- **Step 2**: PDF text extraction with page-by-page details
- **Step 3**: Metadata extraction and storage
- **Step 4**: Text chunking with sentence analysis
- **Step 5**: Embedding generation with model details
- **Step 6**: Vector storage in ChromaDB
- **Step 7**: Database storage of chunks

### 🔍 Query Process
- Query embedding generation
- Vector search execution
- Similarity score calculation
- Result logging and linking

## 🛠️ Troubleshooting

### Common Issues and Debug Output

1. **MinIO Connection Issues**
   ```
   ❌ MinIO upload failed after 5.234s: Connection refused
   ```
   - Check MinIO server status
   - Verify connection settings in settings.py

2. **PDF Extraction Issues**
   ```
   ❌ PDF extraction failed after 2.345s: PDF is encrypted
   ```
   - Check if PDF is password protected
   - Verify PDF file integrity

3. **Embedding Model Issues**
   ```
   ❌ Failed to load model: Model 'all-MiniLM-L6-v2' not found
   ```
   - Check internet connection for model download
   - Verify model name in settings.py

4. **Vector Store Issues**
   ```
   ❌ Failed to add chunks after 1.234s: Collection already exists
   ```
   - Check ChromaDB configuration
   - Verify vector database path

## 📊 Performance Monitoring

The debug output includes timing information for each step:

- **Pipeline Initialization**: Time to load all components
- **MinIO Operations**: Upload/download times
- **Text Processing**: Extraction and chunking times
- **Embedding Generation**: Model processing times
- **Vector Storage**: ChromaDB operation times
- **Database Operations**: Django ORM operation times

## 🎯 Next Steps

After verifying all components work correctly:

1. **Upload multiple documents** to test batch processing
2. **Test different query types** to verify search functionality
3. **Monitor performance** using the timing information
4. **Check database growth** as you add more documents

## 📝 Notes

- Debug output is sent to console (stdout)
- All timing information is in seconds
- File sizes are in bytes
- Embedding dimensions depend on your model
- Similarity scores range from 0.0 to 1.0

The comprehensive debug output will help you identify exactly where any issues occur in the RAG pipeline and verify that each step is working correctly. 