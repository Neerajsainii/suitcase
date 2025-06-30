"""
Main RAG Pipeline Service
"""
import os
import time
import tempfile
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from .rag_components.minio_client import MinIOClient
from .rag_components.text_extractor import TextExtractor
from .rag_components.chunker import DocumentChunker
from .rag_components.embeddings import EmbeddingGenerator
from .rag_components.vector_store import VectorStore
from .models import Document, DocumentChunk
import logging

logger = logging.getLogger(__name__)

class RAGPipeline:
    """Main RAG pipeline for processing documents and handling queries"""
    
    def __init__(self):
        print("🚀 Initializing RAG Pipeline...")
        start_time = time.time()
        
        self.minio_client = MinIOClient()
        self.text_extractor = TextExtractor()
        self.chunker = DocumentChunker()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
        
        init_time = time.time() - start_time
        print(f"✅ RAG Pipeline initialized in {init_time:.3f}s")
    
    def process_document(self, document: Document) -> bool:
        """
        Process a document through the complete RAG pipeline
        
        Args:
            document: Document model instance
            
        Returns:
            bool: True if successful
        """
        print(f"\n{'='*60}")
        print(f"📄 STARTING DOCUMENT PROCESSING: {document.title}")
        print(f"📁 File: {document.file_name}")
        print(f"🆔 Document ID: {document.id}")
        print(f"📊 File size: {document.file_size} bytes")
        print(f"{'='*60}")
        
        pipeline_start_time = time.time()
        
        try:
            # Update status to processing
            print("🔄 Updating document status to 'processing'...")
            document.status = 'processing'
            document.processing_started = timezone.now()
            document.save()
            print("✅ Document status updated")
            
            # Step 1: Download file from MinIO
            print(f"\n📥 STEP 1: Downloading document from MinIO...")
            download_start = time.time()
            temp_file = self._download_document(document)
            if not temp_file:
                raise Exception("Failed to download document from MinIO")
            download_time = time.time() - download_start
            print(f"✅ Download completed in {download_time:.3f}s")
            print(f"📁 Temporary file: {temp_file.name}")
            
            try:
                # Step 2: Extract text from PDF
                print(f"\n📝 STEP 2: Extracting text from PDF...")
                extraction_start = time.time()
                extraction_result = self.text_extractor.extract_text(temp_file.name)
                extraction_time = time.time() - extraction_start
                
                if not extraction_result.get('success'):
                    raise Exception(f"Text extraction failed: {extraction_result.get('error')}")
                
                print(f"✅ Text extraction completed in {extraction_time:.3f}s")
                print(f"📊 Extraction summary: {extraction_result.get('total_pages', 0)} pages, {extraction_result.get('total_text_length', 0)} characters")
                
                # Step 3: Update document metadata
                print(f"\n📋 STEP 3: Updating document metadata...")
                document.metadata = extraction_result['metadata']
                document.num_pages = extraction_result['total_pages']
                document.save()
                print(f"✅ Document metadata updated: {document.num_pages} pages")
                
                # Step 4: Chunk the text
                print(f"\n✂️ STEP 4: Chunking text...")
                chunking_start = time.time()
                full_text = self.text_extractor.get_full_text(extraction_result)
                print(f"📝 Full text length: {len(full_text)} characters")
                
                chunks = self.chunker.chunk_text(full_text, {
                    'document_id': document.id,
                    'document_title': document.title,
                    'file_name': document.file_name,
                    'uploaded_by': document.uploaded_by.username if document.uploaded_by else 'anonymous'
                })
                
                if not chunks:
                    raise Exception("No chunks generated from document")
                
                chunking_time = time.time() - chunking_start
                print(f"✅ Chunking completed in {chunking_time:.3f}s")
                print(f"📊 Generated {len(chunks)} chunks")
                
                # Step 5: Generate embeddings
                print(f"\n🧠 STEP 5: Generating embeddings...")
                embedding_start = time.time()
                chunks_with_embeddings = self.embedding_generator.generate_chunk_embeddings(chunks)
                embedding_time = time.time() - embedding_start
                print(f"✅ Embedding generation completed in {embedding_time:.3f}s")
                
                # Step 6: Store in vector database
                print(f"\n💾 STEP 6: Storing in vector database...")
                vector_start = time.time()
                vector_ids = self.vector_store.add_chunks(chunks_with_embeddings)
                vector_time = time.time() - vector_start
                print(f"✅ Vector storage completed in {vector_time:.3f}s")
                print(f"📊 Stored {len(vector_ids)} chunks in vector database")
                
                # Step 7: Save chunks to database
                print(f"\n💾 STEP 7: Saving chunks to database...")
                db_start = time.time()
                self._save_chunks_to_db(document, chunks_with_embeddings, vector_ids)
                db_time = time.time() - db_start
                print(f"✅ Database storage completed in {db_time:.3f}s")
                
                # Update document status
                print(f"\n✅ FINALIZING: Updating document status...")
                document.status = 'processed'
                document.processing_completed = timezone.now()
                document.total_chunks = len(chunks)
                document.save()
                
                total_time = time.time() - pipeline_start_time
                print(f"\n{'='*60}")
                print(f"🎉 DOCUMENT PROCESSING COMPLETED SUCCESSFULLY!")
                print(f"📄 Document: {document.title}")
                print(f"⏱️ Total processing time: {total_time:.3f}s")
                print(f"📊 Summary:")
                print(f"   - Pages: {document.num_pages}")
                print(f"   - Chunks: {document.total_chunks}")
                print(f"   - Text length: {len(full_text)} characters")
                print(f"   - Vector IDs: {len(vector_ids)}")
                print(f"{'='*60}")
                
                logger.info(f"Successfully processed document: {document.title}")
                return True
                
            finally:
                # Clean up temporary file
                print(f"\n🧹 Cleaning up temporary file...")
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                    print(f"✅ Temporary file cleaned: {temp_file.name}")
                    
        except Exception as e:
            total_time = time.time() - pipeline_start_time
            print(f"\n{'='*60}")
            print(f"❌ DOCUMENT PROCESSING FAILED!")
            print(f"📄 Document: {document.title}")
            print(f"⏱️ Failed after: {total_time:.3f}s")
            print(f"💥 Error: {e}")
            print(f"{'='*60}")
            
            logger.error(f"Error processing document {document.title}: {e}")
            document.status = 'failed'
            document.error_message = str(e)
            document.processing_completed = timezone.now()
            document.save()
            return False
    
    def query(self, query_text: str, num_results: int = 5, 
              filter_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Query the RAG system
        
        Args:
            query_text: Query text
            num_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            Dict with search results and metadata
        """
        print(f"\n🔍 STARTING RAG QUERY")
        print(f"📝 Query: '{query_text}'")
        print(f"📊 Requesting {num_results} results")
        if filter_metadata:
            print(f"🔍 Filter: {filter_metadata}")
        
        start_time = time.time()
        
        try:
            # Generate query embedding
            print(f"\n🧠 Generating query embedding...")
            embedding_start = time.time()
            query_embedding = self.embedding_generator.generate_embedding(query_text)
            embedding_time = time.time() - embedding_start
            
            if not query_embedding:
                raise Exception("Failed to generate query embedding")
            
            print(f"✅ Query embedding generated in {embedding_time:.3f}s")
            print(f"📊 Embedding dimension: {len(query_embedding)}")
            
            # Search vector store
            print(f"\n🔍 Searching vector store...")
            search_start = time.time()
            results = self.vector_store.search(
                query_embedding, 
                n_results=num_results,
                filter_metadata=filter_metadata
            )
            search_time = time.time() - search_start
            
            print(f"✅ Vector search completed in {search_time:.3f}s")
            print(f"📊 Found {len(results)} results")
            
            # Calculate similarity scores
            print(f"\n📊 Calculating similarity scores...")
            for i, result in enumerate(results):
                if result.get('distance') is not None:
                    # Convert distance to similarity score (1 - distance)
                    result['similarity_score'] = 1 - result['distance']
                    print(f"  Result {i+1}: Similarity = {result['similarity_score']:.4f}, Distance = {result['distance']:.4f}")
                else:
                    result['similarity_score'] = 0.0
                    print(f"  Result {i+1}: No distance available")
            
            total_time = time.time() - start_time
            print(f"\n✅ QUERY COMPLETED in {total_time:.3f}s")
            print(f"📊 Summary: {len(results)} results, {total_time:.3f}s total time")
            
            return {
                'query': query_text,
                'results': results,
                'total_results': len(results),
                'search_time': search_time,
                'total_time': total_time,
                'model_info': self.embedding_generator.get_model_info()
            }
            
        except Exception as e:
            total_time = time.time() - start_time
            print(f"\n❌ QUERY FAILED after {total_time:.3f}s: {e}")
            logger.error(f"Error querying RAG system: {e}")
            return {
                'query': query_text,
                'results': [],
                'total_results': 0,
                'search_time': 0.0,
                'total_time': time.time() - start_time,
                'error': str(e)
            }
    
    def _download_document(self, document: Document) -> Optional[tempfile.NamedTemporaryFile]:
        """Download document from MinIO to temporary file"""
        try:
            # Create temporary file and close it immediately to avoid locking
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()
            
            success = self.minio_client.download_file(
                document.minio_object_name, 
                temp_file.name
            )
            
            if success:
                return temp_file
            else:
                # Clean up if download failed
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                return None
                
        except Exception as e:
            logger.error(f"Error downloading document {document.title}: {e}")
            # Clean up on error
            if 'temp_file' in locals() and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            return None
    
    def _save_chunks_to_db(self, document: Document, chunks: List[Dict[str, Any]], 
                          vector_ids: List[str]) -> None:
        """Save chunks to database"""
        print(f"💾 Saving {len(chunks)} chunks to database...")
        start_time = time.time()
        
        try:
            saved_count = 0
            for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
                print(f"📦 Saving chunk {i+1}/{len(chunks)}: ID={chunk.get('chunk_id', str(i))}, Vector ID={vector_id[:8]}...")
                
                DocumentChunk.objects.create(
                    document=document,
                    chunk_id=chunk.get('chunk_id', str(i)),
                    text=chunk.get('text', ''),
                    chunk_index=i,
                    page_number=chunk.get('page_number'),
                    start_char=chunk.get('char_start'),
                    end_char=chunk.get('char_end'),
                    metadata=chunk.get('metadata', {}),
                    vector_store_id=vector_id,
                    embedding_dim=chunk.get('embedding_dim', 0)
                )
                saved_count += 1
                print(f"✅ Chunk {i+1} saved successfully")
            
            save_time = time.time() - start_time
            print(f"✅ Successfully saved {saved_count}/{len(chunks)} chunks to database in {save_time:.3f}s")
            logger.info(f"Saved {len(chunks)} chunks to database for document {document.title}")
            
        except Exception as e:
            save_time = time.time() - start_time
            print(f"❌ Failed to save chunks after {save_time:.3f}s: {e}")
            logger.error(f"Error saving chunks to database: {e}")
            raise
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the RAG system"""
        try:
            vector_info = self.vector_store.get_collection_info()
            embedding_info = self.embedding_generator.get_model_info()
            
            return {
                'vector_store': vector_info,
                'embedding_model': embedding_info,
                'chunk_size': self.chunker.chunk_size,
                'chunk_overlap': self.chunker.chunk_overlap
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {}
    
    def delete_document(self, document: Document) -> bool:
        """Delete a document and all its chunks"""
        try:
            # Delete from MinIO
            self.minio_client.delete_file(document.minio_object_name)
            
            # Delete chunks from vector store
            chunk_ids = list(document.chunks.values_list('vector_store_id', flat=True))
            if chunk_ids:
                self.vector_store.delete_chunks(chunk_ids)
            
            # Delete from database (cascades to chunks)
            document.delete()
            
            logger.info(f"Deleted document: {document.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document.title}: {e}")
            return False 