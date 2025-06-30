"""
Embeddings generator using sentence transformers
"""
import numpy as np
from typing import List, Dict, Any, Union
from sentence_transformers import SentenceTransformer
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generate embeddings for text chunks"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self.model = None
        print(f"🔧 EmbeddingGenerator initializing with model: {self.model_name}")
        self._load_model()
    
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            print(f"📥 Loading embedding model: {self.model_name}")
            start_time = time.time()
            self.model = SentenceTransformer(self.model_name)
            load_time = time.time() - start_time
            print(f"✅ Model loaded successfully in {load_time:.3f}s")
            print(f"📊 Model info: {self.get_model_info()}")
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            logger.error(f"Error loading embedding model {self.model_name}: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        print(f"🧠 Generating embeddings for {len(texts)} texts...")
        start_time = time.time()
        
        try:
            if not texts:
                print("⚠️ No texts provided, returning empty embeddings")
                return []
            
            # Generate embeddings
            print(f"⚡ Processing {len(texts)} texts through model...")
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            
            # Convert to list of lists
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            
            generation_time = time.time() - start_time
            print(f"✅ Generated {len(embeddings)} embeddings in {generation_time:.3f}s")
            
            # Print embedding details
            if embeddings:
                embedding_dim = len(embeddings[0])
                print(f"📊 Embedding dimension: {embedding_dim}")
                print(f"📈 Average embedding norm: {np.mean([np.linalg.norm(emb) for emb in embeddings]):.4f}")
                
                # Show sample embedding vector (first 10 values)
                if embeddings:
                    sample_embedding = embeddings[0][:10]
                    print(f"🧠 Sample embedding (first 10 values): {[f'{x:.4f}' for x in sample_embedding]}")
            
            return embeddings
            
        except Exception as e:
            generation_time = time.time() - start_time
            print(f"❌ Embedding generation failed after {generation_time:.3f}s: {e}")
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string
            
        Returns:
            Embedding vector
        """
        print(f"🧠 Generating embedding for text: '{text[:50]}...'")
        start_time = time.time()
        
        embeddings = self.generate_embeddings([text])
        embedding = embeddings[0] if embeddings else []
        
        generation_time = time.time() - start_time
        print(f"✅ Single embedding generated in {generation_time:.3f}s")
        
        if embedding:
            print(f"📊 Embedding dimension: {len(embedding)}")
            print(f"📈 Embedding norm: {np.linalg.norm(embedding):.4f}")
        
        return embedding
    
    def generate_chunk_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for document chunks
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
            
        Returns:
            List of chunk dictionaries with added 'embedding' field
        """
        print(f"🧠 Starting chunk embedding generation for {len(chunks)} chunks...")
        start_time = time.time()
        
        try:
            # Extract texts from chunks
            texts = [chunk.get('text', '') for chunk in chunks]
            print(f"📝 Extracted {len(texts)} texts from chunks")
            
            # Check for empty texts
            empty_texts = sum(1 for text in texts if not text.strip())
            if empty_texts > 0:
                print(f"⚠️ Found {empty_texts} chunks with empty text")
            
            # Generate embeddings
            print("⚡ Generating embeddings...")
            embeddings = self.generate_embeddings(texts)
            
            # Add embeddings to chunks
            print("🔗 Adding embeddings to chunks...")
            successful_embeddings = 0
            
            for i, chunk in enumerate(chunks):
                if i < len(embeddings):
                    chunk['embedding'] = embeddings[i]
                    chunk['embedding_dim'] = len(embeddings[i])
                    successful_embeddings += 1
                    print(f"✅ Chunk {i+1}: Added {len(embeddings[i])}-dim embedding")
                    
                    # Show chunk text and sample embedding
                    chunk_text = chunk.get('text', '')[:100]
                    if len(chunk.get('text', '')) > 100:
                        chunk_text += "..."
                    print(f"   📄 Text: '{chunk_text}'")
                    
                    # Show first 5 embedding values
                    sample_emb = embeddings[i][:5]
                    print(f"   🧠 Embedding sample: {[f'{x:.4f}' for x in sample_emb]}...")
                else:
                    chunk['embedding'] = []
                    chunk['embedding_dim'] = 0
                    print(f"❌ Chunk {i+1}: No embedding available")
            
            total_time = time.time() - start_time
            print(f"✅ Chunk embedding generation completed in {total_time:.3f}s")
            print(f"📊 Summary: {successful_embeddings}/{len(chunks)} chunks successfully embedded")
            
            return chunks
            
        except Exception as e:
            total_time = time.time() - start_time
            print(f"❌ Chunk embedding generation failed after {total_time:.3f}s: {e}")
            logger.error(f"Error generating chunk embeddings: {e}")
            return chunks
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            float: Similarity score between 0 and 1
        """
        try:
            if not embedding1 or not embedding2:
                return 0.0
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def find_similar_chunks(self, query_embedding: List[float], 
                          chunk_embeddings: List[Dict[str, Any]], 
                          top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find most similar chunks to a query embedding
        
        Args:
            query_embedding: Query embedding vector
            chunk_embeddings: List of chunk dictionaries with embeddings
            top_k: Number of top similar chunks to return
            
        Returns:
            List of top similar chunks with similarity scores
        """
        try:
            similarities = []
            
            for chunk in chunk_embeddings:
                chunk_embedding = chunk.get('embedding', [])
                if chunk_embedding:
                    similarity = self.similarity(query_embedding, chunk_embedding)
                    similarities.append({
                        'chunk': chunk,
                        'similarity': similarity
                    })
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Return top_k results
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar chunks: {e}")
            return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            'model_name': self.model_name,
            'max_seq_length': getattr(self.model, 'max_seq_length', None),
            'embedding_dimension': self.model.get_sentence_embedding_dimension() if self.model else None
        } 