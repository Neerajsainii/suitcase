"""
Enhanced Text Extractor for processing PDF documents with OCR support
"""
import PyPDF2
import os
import tempfile
from typing import Dict, Any, Optional, List
import logging
import time

# OCR imports
try:
    import pytesseract
    from PIL import Image
    import pdf2image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

logger = logging.getLogger(__name__)

class TextExtractor:
    """Extract text from PDF documents with OCR support for scanned documents"""
    
    def __init__(self, tesseract_path: Optional[str] = None):
        self.supported_extensions = ['.pdf']
        self.ocr_available = OCR_AVAILABLE
        print("🔧 TextExtractor initializing...")
        
        # Configure Tesseract path for Windows
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif os.name == 'nt':  # Windows
            # Common Tesseract installation paths on Windows
            possible_paths = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME', ''))
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    print(f"✅ Tesseract found at: {path}")
                    break
            else:
                print("⚠️ Tesseract not found in common locations")
        
        # Check OCR availability
        if self.ocr_available:
            try:
                version = pytesseract.get_tesseract_version()
                print(f"✅ OCR capabilities available - Tesseract version: {version}")
            except Exception as e:
                print(f"⚠️ OCR libraries available but Tesseract not accessible: {e}")
                self.ocr_available = False
        else:
            print("❌ OCR libraries not available - install pytesseract, pillow, pdf2image")
        
        print("✅ TextExtractor initialized")
    
    def extract_from_pdf_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF using OCR (for scanned documents)
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict containing extracted text and metadata
        """
        print(f"🔍 Starting OCR text extraction: {file_path}")
        start_time = time.time()
        
        try:
            if not self.ocr_available:
                raise Exception("OCR libraries not available")
            
            # Convert PDF to images
            print("🖼️ Converting PDF pages to images...")
            images = pdf2image.convert_from_path(file_path, dpi=300)
            print(f"✅ Converted {len(images)} pages to images")
            
            # Extract text from each image using OCR
            print("🔍 Performing OCR on images...")
            text_content = []
            total_text_length = 0
            
            for page_num, image in enumerate(images):
                print(f"📄 Processing page {page_num + 1}/{len(images)} with OCR...")
                
                # Perform OCR
                page_text = pytesseract.image_to_string(image, lang='eng')
                page_text = page_text.strip()
                page_text_length = len(page_text)
                total_text_length += page_text_length
                
                if page_text:
                    text_content.append({
                        'page': page_num + 1,
                        'text': page_text,
                        'extraction_method': 'ocr'
                    })
                    print(f"✅ Page {page_num + 1}: {page_text_length} characters extracted via OCR")
                    
                    # Show first 200 characters of extracted text
                    preview_text = page_text[:200]
                    if len(page_text) > 200:
                        preview_text += "..."
                    print(f"📄 OCR Text preview: '{preview_text}'")
                else:
                    print(f"⚠️ Page {page_num + 1}: No text found via OCR")
            
            extraction_time = time.time() - start_time
            print(f"✅ OCR text extraction completed in {extraction_time:.3f}s")
            print(f"📊 Summary: {len(text_content)} pages with text, {total_text_length} total characters")
            
            # Show sample of extracted text from first page
            if text_content:
                print(f"\n📄 SAMPLE OCR EXTRACTED TEXT (First page):")
                print(f"{'='*60}")
                sample_text = text_content[0]['text'][:500]
                if len(text_content[0]['text']) > 500:
                    sample_text += "\n... (truncated)"
                print(sample_text)
                print(f"{'='*60}")
            
            return {
                'success': True,
                'metadata': {
                    'num_pages': len(images),
                    'extraction_method': 'ocr',
                    'ocr_engine': 'tesseract'
                },
                'content': text_content,
                'total_pages': len(images),
                'pages_with_text': len(text_content),
                'total_text_length': total_text_length,
                'extraction_time': extraction_time
            }
            
        except Exception as e:
            extraction_time = time.time() - start_time
            print(f"❌ OCR extraction failed after {extraction_time:.3f}s: {e}")
            logger.error(f"Error extracting text with OCR from PDF {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {},
                'content': [],
                'extraction_time': extraction_time
            }
    
    def extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF file using PyPDF2 (original method)
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dict containing extracted text and metadata
        """
        print(f"📄 Starting PyPDF2 text extraction: {file_path}")
        start_time = time.time()
        
        try:
            print(f"📖 Opening PDF file: {file_path}")
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                print(f"✅ PDF opened successfully, {len(pdf_reader.pages)} pages found")
                
                # Extract metadata
                print("📋 Extracting PDF metadata...")
                metadata = {
                    'num_pages': len(pdf_reader.pages),
                    'title': pdf_reader.metadata.get('/Title', ''),
                    'author': pdf_reader.metadata.get('/Author', ''),
                    'subject': pdf_reader.metadata.get('/Subject', ''),
                    'creator': pdf_reader.metadata.get('/Creator', ''),
                    'producer': pdf_reader.metadata.get('/Producer', ''),
                    'extraction_method': 'pypdf2'
                }
                print(f"📋 Metadata extracted: {metadata}")
                
                # Extract text from all pages
                print("📝 Extracting text from pages...")
                text_content = []
                total_text_length = 0
                
                for page_num, page in enumerate(pdf_reader.pages):
                    print(f"📄 Processing page {page_num + 1}/{len(pdf_reader.pages)}")
                    page_text = page.extract_text()
                    page_text_length = len(page_text.strip())
                    total_text_length += page_text_length
                    
                    if page_text.strip():
                        text_content.append({
                            'page': page_num + 1,
                            'text': page_text.strip(),
                            'extraction_method': 'pypdf2'
                        })
                        print(f"✅ Page {page_num + 1}: {page_text_length} characters extracted")
                        
                        # Show first 200 characters of extracted text
                        preview_text = page_text.strip()[:200]
                        if len(page_text.strip()) > 200:
                            preview_text += "..."
                        print(f"📄 Text preview: '{preview_text}'")
                    else:
                        print(f"⚠️ Page {page_num + 1}: No text content found")
                
                extraction_time = time.time() - start_time
                print(f"✅ PyPDF2 text extraction completed in {extraction_time:.3f}s")
                print(f"📊 Summary: {len(text_content)} pages with text, {total_text_length} total characters")
                
                # Show sample of extracted text from first page
                if text_content:
                    print(f"\n📄 SAMPLE PyPDF2 EXTRACTED TEXT (First page):")
                    print(f"{'='*60}")
                    sample_text = text_content[0]['text'][:500]
                    if len(text_content[0]['text']) > 500:
                        sample_text += "\n... (truncated)"
                    print(sample_text)
                    print(f"{'='*60}")
                
                return {
                    'success': True,
                    'metadata': metadata,
                    'content': text_content,
                    'total_pages': len(pdf_reader.pages),
                    'pages_with_text': len(text_content),
                    'total_text_length': total_text_length,
                    'extraction_time': extraction_time
                }
                
        except Exception as e:
            extraction_time = time.time() - start_time
            print(f"❌ PyPDF2 extraction failed after {extraction_time:.3f}s: {e}")
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'metadata': {},
                'content': [],
                'extraction_time': extraction_time
            }
    
    def extract_text(self, file_path: str, force_ocr: bool = False) -> Dict[str, Any]:
        """
        Extract text from file with intelligent fallback to OCR
        
        Args:
            file_path: Path to the file
            force_ocr: Force OCR extraction even if PyPDF2 succeeds
            
        Returns:
            Dict containing extracted text and metadata
        """
        print(f"🔍 Starting intelligent text extraction for: {file_path}")
        file_ext = os.path.splitext(file_path)[1].lower()
        print(f"📁 File extension: {file_ext}")
        
        if file_ext != '.pdf':
            print(f"❌ Unsupported file type: {file_ext}")
            return {
                'success': False,
                'error': f'Unsupported file type: {file_ext}',
                'metadata': {},
                'content': []
            }
        
        # Try PyPDF2 first (fast)
        print("🔄 Step 1: Trying PyPDF2 extraction...")
        pypdf2_result = self.extract_from_pdf(file_path)
        
        # Check if PyPDF2 found any text
        has_text = pypdf2_result.get('success') and pypdf2_result.get('total_text_length', 0) > 0
        
        if has_text and not force_ocr:
            print("✅ PyPDF2 extraction successful - using regular text extraction")
            return pypdf2_result
        
        # If PyPDF2 failed or found no text, try OCR
        if self.ocr_available:
            print("🔄 Step 2: PyPDF2 found no text, trying OCR...")
            ocr_result = self.extract_from_pdf_with_ocr(file_path)
            
            if ocr_result.get('success') and ocr_result.get('total_text_length', 0) > 0:
                print("✅ OCR extraction successful - using OCR text")
                return ocr_result
            else:
                print("❌ OCR extraction also failed")
                # Return PyPDF2 result even if empty, for consistency
                return pypdf2_result
        else:
            print("❌ OCR not available - returning PyPDF2 result")
            return pypdf2_result
    
    def get_full_text(self, extraction_result: Dict[str, Any]) -> str:
        """
        Get full text from extraction result
        
        Args:
            extraction_result: Result from extract_text method
            
        Returns:
            str: Combined text from all pages
        """
        print("🔗 Combining text from all pages...")
        
        if not extraction_result.get('success'):
            print("❌ Extraction was not successful, returning empty string")
            return ""
        
        full_text = ""
        page_count = 0
        extraction_method = extraction_result.get('metadata', {}).get('extraction_method', 'unknown')
        
        for page_content in extraction_result['content']:
            full_text += page_content['text'] + "\n\n"
            page_count += 1
        
        final_text = full_text.strip()
        print(f"✅ Combined text from {page_count} pages, total length: {len(final_text)} characters")
        print(f"📊 Extraction method used: {extraction_method}")
        
        # Show sample of combined text
        print(f"\n📄 COMBINED TEXT SAMPLE (First 800 characters):")
        print(f"{'='*60}")
        sample_text = final_text[:800]
        if len(final_text) > 800:
            sample_text += "\n... (truncated)"
        print(sample_text)
        print(f"{'='*60}")
        
        return final_text 