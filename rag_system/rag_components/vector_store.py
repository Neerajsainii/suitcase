"""
Vector Store using ChromaDB for similarity search
"""
import os
import json
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store using ChromaDB for similarity search"""
    
    def __init__(self, collection_name: str = "law_cases"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create vector database directory
            os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.VECTOR_DB_PATH,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Law cases vector store"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    def add_chunks(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Add chunks to the vector store
        
        Args:
            chunks: List of chunk dictionaries with embeddings
            
        Returns:
            List of chunk IDs
        """
        try:
            if not chunks:
                return []
            
            # Prepare data for ChromaDB
            ids = []
            texts = []
            embeddings = []
            metadatas = []
            
            for chunk in chunks:
                # Generate unique ID
                chunk_id = str(uuid.uuid4())
                ids.append(chunk_id)
                
                # Extract text
                text = chunk.get('text', '')
                texts.append(text)
                
                # Extract embedding
                embedding = chunk.get('embedding', [])
                embeddings.append(embedding)
                
                # Prepare metadata (exclude text and embedding)
                metadata = {k: v for k, v in chunk.items() 
                          if k not in ['text', 'embedding'] and v is not None}
                metadatas.append(metadata)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            return []
    
    def search(self, query_embedding: List[float], 
              n_results: int = 5, 
              filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for similar chunks
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of similar chunks with metadata
        """
        print(f"🔍 Searching vector store for {n_results} results...")
        start_time = time.time()
        
        try:
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )
            
            search_time = time.time() - start_time
            print(f"✅ Vector search completed in {search_time:.3f}s")
            
            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    formatted_results.append(result)
            
            print(f"📊 Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            search_time = time.time() - start_time
            print(f"❌ Vector search failed after {search_time:.3f}s: {e}")
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def search_by_text(self, query_text: str, 
                      n_results: int = 5,
                      filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search by text (will be embedded automatically)
        
        Args:
            query_text: Query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of similar chunks with metadata
        """
        try:
            # Perform search by text
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching vector store by text: {e}")
            return []
    
    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific chunk by ID
        
        Args:
            chunk_id: ID of the chunk
            
        Returns:
            Chunk data or None if not found
        """
        try:
            results = self.collection.get(ids=[chunk_id])
            
            if results['ids']:
                return {
                    'id': results['ids'][0],
                    'text': results['documents'][0],
                    'metadata': results['metadatas'][0],
                    'embedding': results['embeddings'][0] if 'embeddings' in results else None
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting chunk {chunk_id}: {e}")
            return None
    
    def delete_chunks(self, chunk_ids: List[str]) -> bool:
        """
        Delete chunks by IDs
        
        Args:
            chunk_ids: List of chunk IDs to delete
            
        Returns:
            bool: True if successful
        """
        try:
            self.collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} chunks from vector store")
            return True
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            count = self.collection.count()
            return {
                'collection_name': self.collection_name,
                'total_chunks': count,
                'collection_metadata': self.collection.metadata
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def reset_collection(self) -> bool:
        """Reset the collection (delete all data)"""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Law cases vector store"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            return False 