# 🧪 RAG System Testing Guide

## 🚀 Quick Start

### 1. **Start MinIO Server**
```bash
# Option A: Docker (Recommended)
docker run -p 9000:9000 -p 9001:9001 --name minio \
  -e "MINIO_ROOT_USER=admin" \
  -e "MINIO_ROOT_PASSWORD=password123" \
  -v minio_data:/data \
  quay.io/minio/minio server /data --console-address ":9001"

# Option B: Binary
./minio server /data --console-address ":9001"
```

### 2. **Activate Virtual Environment**
```bash
.\rag_env\Scripts\Activate.ps1
```

### 3. **Run Django Server**
```bash
python manage.py runserver
```

### 4. **Access the System**
- **Web Interface**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **MinIO Console**: http://localhost:9001 (admin/password123)

---

## 📋 Testing Checklist

### ✅ **Prerequisites Check**
- [ ] MinIO server is running
- [ ] Virtual environment is activated
- [ ] Django server is running
- [ ] All tests pass (`python test_installation.py`)

### ✅ **Admin Setup**
- [ ] Create superuser account
- [ ] Log in to admin panel
- [ ] Verify all models are visible

### ✅ **Document Upload Test**
- [ ] Upload a PDF document
- [ ] Verify document appears in list
- [ ] Check processing status
- [ ] Confirm chunks are created

### ✅ **Query System Test**
- [ ] Search for legal terms
- [ ] Verify results are returned
- [ ] Check similarity scores
- [ ] Test document filtering

---

## 🔍 **Detailed Testing Steps**

### **Step 1: Initial Setup**

1. **Create Environment File**
   ```bash
   copy env_example.txt .env
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Database**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

### **Step 2: Test System Components**

1. **Run Installation Test**
   ```bash
   python test_installation.py
   ```
   - Should show all tests passing

2. **Start MinIO**
   - Access MinIO console at http://localhost:9001
   - Login: admin / password123
   - Verify bucket "law-cases" exists

3. **Start Django Server**
   ```bash
   python manage.py runserver
   ```

### **Step 3: Web Interface Testing**

#### **Home Page Test**
1. Visit http://localhost:8000
2. Verify statistics are displayed
3. Check navigation links work
4. Confirm responsive design

#### **Upload Test**
1. Go to Upload page
2. Try drag-and-drop functionality
3. Upload a PDF file
4. Verify upload progress modal
5. Check document appears in list

#### **Documents Management Test**
1. Go to Documents page
2. Verify uploaded documents are listed
3. Check status badges (Uploaded, Processing, Processed)
4. Test view chunks functionality
5. Test reprocess functionality
6. Test delete functionality

#### **Query Test**
1. Go to Query page
2. Enter a legal question
3. Adjust number of results
4. Test document filtering
5. Verify results display
6. Check similarity scores

### **Step 4: API Testing**

#### **Document Upload API**
```bash
curl -X POST http://localhost:8000/api/documents/upload/ \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_document.pdf" \
  -F "title=Test Document"
```

#### **Query API**
```bash
curl -X POST http://localhost:8000/api/queries/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is breach of contract?",
    "num_results": 5
  }'
```

#### **Documents List API**
```bash
curl -X GET http://localhost:8000/api/documents/
```

### **Step 5: Sample Data Testing**

#### **Create Test PDF**
1. Convert the provided `sample_legal_document.txt` to PDF
2. Or use any legal PDF document
3. Upload through the web interface

#### **Test Queries**
Try these sample queries:
- "What is breach of contract?"
- "Explain material breach"
- "What are the types of damages?"
- "Define specific performance"
- "What is the statute of limitations?"

#### **Expected Results**
- Relevant text chunks should be returned
- Similarity scores should be displayed
- Source document information should be shown
- Page numbers should be included (if available)

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **MinIO Connection Error**
```
Error: Failed to connect to MinIO
```
**Solution:**
- Ensure MinIO server is running
- Check endpoint in .env file
- Verify credentials are correct

#### **Document Processing Failed**
```
Error: Text extraction failed
```
**Solution:**
- Ensure PDF is not corrupted
- Check if PDF contains extractable text
- Verify PyPDF2 is installed correctly

#### **Embedding Generation Error**
```
Error: Failed to generate embeddings
```
**Solution:**
- Check internet connection (for model download)
- Verify sentence-transformers is installed
- Check available memory

#### **Vector Store Error**
```
Error: ChromaDB connection failed
```
**Solution:**
- Ensure vector_db directory exists
- Check write permissions
- Verify ChromaDB is installed

### **Debug Commands**

#### **Check System Status**
```bash
python manage.py shell
```
```python
from rag_system.rag_pipeline import RAGPipeline
pipeline = RAGPipeline()
info = pipeline.get_system_info()
print(info)
```

#### **Test Individual Components**
```python
# Test MinIO
from rag_system.rag_components.minio_client import MinIOClient
client = MinIOClient()
print("MinIO connected:", client.client.bucket_exists("law-cases"))

# Test Text Extraction
from rag_system.rag_components.text_extractor import TextExtractor
extractor = TextExtractor()
# Test with a file path

# Test Embeddings
from rag_system.rag_components.embeddings import EmbeddingGenerator
generator = EmbeddingGenerator()
embedding = generator.generate_embedding("test text")
print("Embedding dimension:", len(embedding))
```

---

## 📊 **Performance Testing**

### **Upload Performance**
- Test with different file sizes (1MB, 10MB, 50MB)
- Monitor processing time
- Check memory usage

### **Query Performance**
- Test with different query lengths
- Measure response times
- Test concurrent queries

### **Scalability Testing**
- Upload multiple documents
- Test with large document collections
- Monitor system resources

---

## 🎯 **Success Criteria**

### **Functional Requirements**
- [ ] PDF upload and processing works
- [ ] Text extraction is accurate
- [ ] Document chunking is appropriate
- [ ] Embeddings are generated correctly
- [ ] Vector search returns relevant results
- [ ] Web interface is responsive
- [ ] API endpoints work correctly

### **Performance Requirements**
- [ ] Upload processing time < 5 minutes for 10MB PDF
- [ ] Query response time < 3 seconds
- [ ] System handles multiple concurrent users
- [ ] Memory usage remains stable

### **User Experience**
- [ ] Intuitive web interface
- [ ] Clear error messages
- [ ] Progress indicators
- [ ] Responsive design
- [ ] Fast page loads

---

## 🚀 **Next Steps After Testing**

1. **Production Deployment**
   - Configure production settings
   - Set up proper database
   - Configure MinIO for production
   - Set up monitoring

2. **Feature Enhancements**
   - Add user authentication
   - Implement document versioning
   - Add advanced search filters
   - Create document annotations

3. **Integration**
   - Connect to external legal databases
   - Add OCR for scanned documents
   - Integrate with legal research tools
   - Add export functionality

---

## 📞 **Support**

If you encounter issues during testing:

1. Check the troubleshooting section above
2. Review Django logs for errors
3. Verify all prerequisites are met
4. Test individual components
5. Check system resources

For additional help, refer to the README.md file or create an issue in the project repository. 