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
        self.minio_client = MinIOClient()
        self.text_extractor = TextExtractor()
        self.chunker = DocumentChunker()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStore()
    
    def process_document(self, document: Document) -> bool:
        """
        Process a document through the complete RAG pipeline
        
        Args:
            document: Document model instance
            
        Returns:
            bool: True if successful
        """
        try:
            # Update status to processing
            document.status = 'processing'
            document.processing_started = timezone.now()
            document.save()
            
            # Step 1: Download file from MinIO
            temp_file = self._download_document(document)
            if not temp_file:
                raise Exception("Failed to download document from MinIO")
            
            try:
                # Step 2: Extract text from PDF
                extraction_result = self.text_extractor.extract_text(temp_file.name)
                if not extraction_result.get('success'):
                    raise Exception(f"Text extraction failed: {extraction_result.get('error')}")
                
                # Step 3: Update document metadata
                document.metadata = extraction_result['metadata']
                document.num_pages = extraction_result['total_pages']
                document.save()
                
                # Step 4: Chunk the text
                full_text = self.text_extractor.get_full_text(extraction_result)
                chunks = self.chunker.chunk_text(full_text, {
                    'document_id': document.id,
                    'document_title': document.title,
                    'file_name': document.file_name,
                    'uploaded_by': document.uploaded_by.username
                })
                
                if not chunks:
                    raise Exception("No chunks generated from document")
                
                # Step 5: Generate embeddings
                chunks_with_embeddings = self.embedding_generator.generate_chunk_embeddings(chunks)
                
                # Step 6: Store in vector database
                vector_ids = self.vector_store.add_chunks(chunks_with_embeddings)
                
                # Step 7: Save chunks to database
                self._save_chunks_to_db(document, chunks_with_embeddings, vector_ids)
                
                # Update document status
                document.status = 'processed'
                document.processing_completed = timezone.now()
                document.total_chunks = len(chunks)
                document.save()
                
                logger.info(f"Successfully processed document: {document.title}")
                return True
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                    
        except Exception as e:
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
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_embedding(query_text)
            
            if not query_embedding:
                raise Exception("Failed to generate query embedding")
            
            # Search vector store
            search_start = time.time()
            results = self.vector_store.search(
                query_embedding, 
                n_results=num_results,
                filter_metadata=filter_metadata
            )
            search_time = time.time() - search_start
            
            # Calculate similarity scores
            for result in results:
                if result.get('distance') is not None:
                    # Convert distance to similarity score (1 - distance)
                    result['similarity_score'] = 1 - result['distance']
                else:
                    result['similarity_score'] = 0.0
            
            total_time = time.time() - start_time
            
            return {
                'query': query_text,
                'results': results,
                'total_results': len(results),
                'search_time': search_time,
                'total_time': total_time,
                'model_info': self.embedding_generator.get_model_info()
            }
            
        except Exception as e:
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
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            success = self.minio_client.download_file(
                document.minio_object_name, 
                temp_file.name
            )
            
            if success:
                return temp_file
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error downloading document {document.title}: {e}")
            return None
    
    def _save_chunks_to_db(self, document: Document, chunks: List[Dict[str, Any]], 
                          vector_ids: List[str]) -> None:
        """Save chunks to database"""
        try:
            for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
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
            
            logger.info(f"Saved {len(chunks)} chunks to database for document {document.title}")
            
        except Exception as e:
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