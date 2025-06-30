"""
Document Chunker for segmenting text into chunks with metadata
"""
import re
from typing import List, Dict, Any
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

class DocumentChunker:
    """Chunk documents into smaller segments with metadata"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        print(f"🔧 DocumentChunker initialized - Chunk size: {self.chunk_size}, Overlap: {self.chunk_overlap}")
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller segments
        
        Args:
            text: Text to chunk
            metadata: Additional metadata to include with chunks
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        print(f"✂️ Starting text chunking process...")
        start_time = time.time()
        print(f"📊 Input text length: {len(text)} characters")
        print(f"📋 Metadata: {metadata}")
        
        if not text.strip():
            print("⚠️ Empty text provided, returning empty chunks")
            return []
        
        # Clean and normalize text
        print("🧹 Cleaning and normalizing text...")
        text = self._clean_text(text)
        print(f"✅ Text cleaned, new length: {len(text)} characters")
        
        # Split text into sentences first
        print("🔤 Splitting text into sentences...")
        sentences = self._split_into_sentences(text)
        print(f"✅ Split into {len(sentences)} sentences")
        
        chunks = []
        current_chunk = ""
        chunk_start = 0
        
        print(f"🔀 Processing sentences with chunk size: {self.chunk_size}")
        
        for i, sentence in enumerate(sentences):
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_data = {
                    'text': current_chunk.strip(),
                    'chunk_id': len(chunks),
                    'start_sentence': chunk_start,
                    'end_sentence': i - 1,
                    'char_start': text.find(current_chunk.strip()),
                    'char_end': text.find(current_chunk.strip()) + len(current_chunk.strip()),
                }
                
                # Add metadata
                if metadata:
                    chunk_data.update(metadata)
                
                chunks.append(chunk_data)
                print(f"📦 Created chunk {len(chunks)}: {len(current_chunk.strip())} characters, sentences {chunk_start}-{i-1}")
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + sentence
                chunk_start = i - len(overlap_text.split('.')) if overlap_text else i
                print(f"🔄 Starting new chunk with {len(overlap_text)} characters overlap")
            else:
                current_chunk += sentence
        
        # Add final chunk
        if current_chunk.strip():
            chunk_data = {
                'text': current_chunk.strip(),
                'chunk_id': len(chunks),
                'start_sentence': chunk_start,
                'end_sentence': len(sentences) - 1,
                'char_start': text.find(current_chunk.strip()),
                'char_end': text.find(current_chunk.strip()) + len(current_chunk.strip()),
            }
            
            if metadata:
                chunk_data.update(metadata)
            
            chunks.append(chunk_data)
            print(f"📦 Created final chunk {len(chunks)}: {len(current_chunk.strip())} characters, sentences {chunk_start}-{len(sentences)-1}")
        
        chunking_time = time.time() - start_time
        total_chunk_text = sum(len(chunk['text']) for chunk in chunks)
        print(f"✅ Chunking completed in {chunking_time:.3f}s")
        print(f"📊 Summary: {len(chunks)} chunks created, {total_chunk_text} total characters")
        
        # Print chunk details
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}: {len(chunk['text'])} chars, metadata keys: {list(chunk.keys())}")
            
            # Show actual chunk content
            chunk_text = chunk['text']
            if len(chunk_text) > 150:
                chunk_text = chunk_text[:150] + "..."
            print(f"    📄 Content: '{chunk_text}'")
            
            # Show metadata
            metadata = {k: v for k, v in chunk.items() if k != 'text'}
            print(f"    📋 Metadata: {metadata}")
            print()
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep legal terms
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}\"\']+', ' ', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Split by sentence endings, but be careful with legal citations
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _get_overlap_text(self, chunk_text: str) -> str:
        """Get overlap text from the end of a chunk"""
        if not chunk_text or len(chunk_text) <= self.chunk_overlap:
            return ""
        
        # Get the last few sentences for overlap
        sentences = self._split_into_sentences(chunk_text)
        
        overlap_sentences = []
        current_length = 0
        
        for sentence in reversed(sentences):
            if current_length + len(sentence) <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                current_length += len(sentence)
            else:
                break
        
        return ' '.join(overlap_sentences)
    
    def chunk_by_paragraphs(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk text by paragraphs
        
        Args:
            text: Text to chunk
            metadata: Additional metadata
            
        Returns:
            List of chunk dictionaries
        """
        paragraphs = text.split('\n\n')
        chunks = []
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                chunk_data = {
                    'text': paragraph.strip(),
                    'chunk_id': i,
                    'paragraph_id': i,
                    'chunk_type': 'paragraph'
                }
                
                if metadata:
                    chunk_data.update(metadata)
                
                chunks.append(chunk_data)
        
        return chunks
    
    def chunk_by_pages(self, page_content: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk text by pages (for PDF content)
        
        Args:
            page_content: List of page dictionaries with text
            metadata: Additional metadata
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        for page_data in page_content:
            page_text = page_data.get('text', '')
            page_num = page_data.get('page', 0)
            
            if page_text.strip():
                # Further chunk the page text if it's too long
                page_chunks = self.chunk_text(page_text, {
                    'page_number': page_num,
                    'chunk_type': 'page'
                })
                
                for chunk in page_chunks:
                    chunk['page_number'] = page_num
                
                chunks.extend(page_chunks)
        
        return chunks 