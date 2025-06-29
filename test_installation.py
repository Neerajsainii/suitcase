#!/usr/bin/env python3
"""
Test script to verify RAG system installation
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'suitcase.settings')
django.setup()

def test_imports():
    """Test if all required packages can be imported"""
    print("🔄 Testing imports...")
    
    try:
        import minio
        print("✅ MinIO imported successfully")
    except ImportError as e:
        print(f"❌ MinIO import failed: {e}")
        return False
    
    try:
        import PyPDF2
        print("✅ PyPDF2 imported successfully")
    except ImportError as e:
        print(f"❌ PyPDF2 import failed: {e}")
        return False
    
    try:
        import sentence_transformers
        print("✅ Sentence Transformers imported successfully")
    except ImportError as e:
        print(f"❌ Sentence Transformers import failed: {e}")
        return False
    
    try:
        import chromadb
        print("✅ ChromaDB imported successfully")
    except ImportError as e:
        print(f"❌ ChromaDB import failed: {e}")
        return False
    
    try:
        import numpy
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    return True

def test_django_models():
    """Test Django models"""
    print("🔄 Testing Django models...")
    
    try:
        from rag_system.models import Document, DocumentChunk, QueryLog
        print("✅ Django models imported successfully")
        
        # Test model creation
        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com'}
        )
        
        # Test Document model
        doc = Document.objects.create(
            title='Test Document',
            file_name='test.pdf',
            minio_object_name='test/object',
            file_size=1024,
            file_type='application/pdf',
            uploaded_by=user
        )
        print("✅ Document model test passed")
        
        # Clean up
        doc.delete()
        if created:
            user.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Django models test failed: {e}")
        return False

def test_rag_components():
    """Test RAG components"""
    print("🔄 Testing RAG components...")
    
    try:
        from rag_system.rag_components.minio_client import MinIOClient
        print("✅ MinIO client imported successfully")
    except Exception as e:
        print(f"❌ MinIO client import failed: {e}")
        return False
    
    try:
        from rag_system.rag_components.text_extractor import TextExtractor
        print("✅ Text extractor imported successfully")
    except Exception as e:
        print(f"❌ Text extractor import failed: {e}")
        return False
    
    try:
        from rag_system.rag_components.chunker import DocumentChunker
        print("✅ Document chunker imported successfully")
    except Exception as e:
        print(f"❌ Document chunker import failed: {e}")
        return False
    
    try:
        from rag_system.rag_components.embeddings import EmbeddingGenerator
        print("✅ Embedding generator imported successfully")
    except Exception as e:
        print(f"❌ Embedding generator import failed: {e}")
        return False
    
    try:
        from rag_system.rag_components.vector_store import VectorStore
        print("✅ Vector store imported successfully")
    except Exception as e:
        print(f"❌ Vector store import failed: {e}")
        return False
    
    return True

def test_settings():
    """Test Django settings"""
    print("🔄 Testing Django settings...")
    
    try:
        from django.conf import settings
        
        # Test required settings
        required_settings = [
            'MINIO_ENDPOINT',
            'MINIO_ACCESS_KEY',
            'MINIO_SECRET_KEY',
            'MINIO_BUCKET_NAME',
            'EMBEDDING_MODEL_NAME',
            'CHUNK_SIZE',
            'CHUNK_OVERLAP'
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                print(f"✅ {setting} is configured")
            else:
                print(f"❌ {setting} is missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False

def test_directories():
    """Test if required directories exist"""
    print("🔄 Testing directories...")
    
    required_dirs = [
        'static/uploads',
        'media',
        'vector_db'
    ]
    
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            return False
    
    return True

def main():
    """Main test function"""
    print("🧪 Testing Law Case RAG System Installation")
    print("=" * 50)
    
    tests = [
        ("Package Imports", test_imports),
        ("Django Models", test_django_models),
        ("RAG Components", test_rag_components),
        ("Django Settings", test_settings),
        ("Directories", test_directories),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The RAG system is ready to use.")
        print("\nNext steps:")
        print("1. Start MinIO server")
        print("2. Run: python manage.py runserver")
        print("3. Access the system at: http://localhost:8000")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 