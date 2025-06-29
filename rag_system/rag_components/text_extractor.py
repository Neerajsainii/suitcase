"""
Text Extractor for processing PDF documents
"""
import PyPDF2
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class TextExtractor:
    """Extract text from PDF documents"""
    
    def __init__(self):
        self.supported_extensions = ['.pdf']
    
    def extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract metadata
                metadata = {
                    'num_pages': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.get('/Title', ''),
                    'author': pdf_reader.metadata.get('/Author', ''),
                    'subject': pdf_reader.metadata.get('/Subject', ''),
                    'creator': pdf_reader.metadata.get('/Creator', ''),
                    'producer': pdf_reader.metadata.get('/Producer', ''),
                }
                
                # Extract text from all pages
                text_content = []
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append({
                            'page': page_num + 1,
                            'text': page_text.strip()
                        })
                
                return {
                    'success': True,
                    'metadata': metadata,
                    'content': text_content,
                    'total_pages': len(pdf_reader.pages),
                    'pages_with_text': len(text_content)
                }
                
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {},
                'content': []
            }
    
    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from file based on file extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict containing extracted text and metadata
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_from_pdf(file_path)
        else:
            return {
                'success': False,
                'error': f'Unsupported file type: {file_ext}',
                'metadata': {},
                'content': []
            }
    
    def get_full_text(self, extraction_result: Dict[str, Any]) -> str:
        """
        Get full text from extraction result
        
        Args:
            extraction_result: Result from extract_text method
            
        Returns:
            str: Combined text from all pages
        """
        if not extraction_result.get('success'):
            return ""
        
        full_text = ""
        for page_content in extraction_result['content']:
            full_text += page_content['text'] + "\n\n"
        
        return full_text.strip() 