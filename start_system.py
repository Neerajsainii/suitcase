#!/usr/bin/env python3
"""
Startup script for the Law Case RAG System
This script helps you quickly start the system with proper checks.
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def print_banner():
    """Print the system banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    Law Case RAG System                       ║
    ║                                                              ║
    ║  🧠 AI-Powered Legal Document Search & Analysis              ║
    ║  📚 Upload PDFs • Extract Text • Generate Embeddings        ║
    ║  🔍 Semantic Search • Intelligent Querying                  ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def check_environment():
    """Check if the environment is properly set up"""
    print("🔍 Checking environment...")
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ Virtual environment not detected!")
        print("   Please activate your virtual environment first:")
        print("   .\\rag_env\\Scripts\\Activate.ps1")
        return False
    
    print("✅ Virtual environment is active")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("   Please create .env file from env_example.txt")
        return False
    
    print("✅ Environment file found")
    
    # Check if required directories exist
    required_dirs = ['media', 'vector_db', 'static/uploads']
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"❌ Required directory missing: {dir_path}")
            return False
    
    print("✅ Required directories exist")
    return True

def run_tests():
    """Run the installation tests"""
    print("\n🧪 Running system tests...")
    
    try:
        result = subprocess.run([sys.executable, 'test_installation.py'], 
                              capture_output=True, text=True, check=True)
        print("✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Tests failed!")
        print(e.stdout)
        print(e.stderr)
        return False

def check_minio():
    """Check if MinIO is running"""
    print("\n🔍 Checking MinIO connection...")
    
    try:
        import os
        from minio import Minio
        
        client = Minio(
            os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'admin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'password123'),
            secure=False
        )
        
        # Try to list buckets
        buckets = list(client.list_buckets())
        print("✅ MinIO is running and accessible")
        return True
        
    except Exception as e:
        print("❌ MinIO connection failed!")
        print(f"   Error: {e}")
        print("\n   Please start MinIO server:")
        print("   docker run -p 9000:9000 -p 9001:9001 --name minio \\")
        print("     -e \"MINIO_ROOT_USER=admin\" \\")
        print("     -e \"MINIO_ROOT_PASSWORD=password123\" \\")
        print("     -v minio_data:/data \\")
        print("     quay.io/minio/minio server /data --console-address \":9001\"")
        return False

def start_django():
    """Start the Django development server"""
    print("\n🚀 Starting Django server...")
    
    try:
        # Start Django server in background
        process = subprocess.Popen([
            sys.executable, 'manage.py', 'runserver'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ Django server started successfully!")
            print("   Server running at: http://localhost:8000")
            return process
        else:
            stdout, stderr = process.communicate()
            print("❌ Django server failed to start!")
            print(f"   Error: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting Django server: {e}")
        return None

def open_browser():
    """Open the web browser to the application"""
    print("\n🌐 Opening web browser...")
    
    try:
        webbrowser.open('http://localhost:8000')
        print("✅ Browser opened to application")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print("   Please manually navigate to: http://localhost:8000")

def main():
    """Main startup function"""
    print_banner()
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        return
    
    # Run tests
    if not run_tests():
        print("\n❌ System tests failed. Please fix the issues above.")
        return
    
    # Check MinIO
    if not check_minio():
        print("\n❌ MinIO check failed. Please start MinIO server.")
        return
    
    # Start Django
    django_process = start_django()
    if not django_process:
        print("\n❌ Failed to start Django server.")
        return
    
    # Open browser
    open_browser()
    
    print("\n" + "="*60)
    print("🎉 Law Case RAG System is now running!")
    print("="*60)
    print("\n📋 Quick Access:")
    print("   • Web Interface: http://localhost:8000")
    print("   • Admin Panel: http://localhost:8000/admin")
    print("   • MinIO Console: http://localhost:9001")
    print("\n📚 Next Steps:")
    print("   1. Create a superuser account (if not done)")
    print("   2. Upload legal documents via the web interface")
    print("   3. Query your documents using the search feature")
    print("   4. Check the TESTING_GUIDE.md for detailed instructions")
    print("\n⚠️  Press Ctrl+C to stop the server")
    
    try:
        # Keep the script running
        django_process.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping server...")
        django_process.terminate()
        print("✅ Server stopped")

if __name__ == "__main__":
    main() 