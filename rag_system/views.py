"""
Views for the RAG system API and web interface
"""
import threading
import json
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from .models import Document, DocumentChunk, QueryLog
from .serializers import (
    DocumentSerializer, DocumentChunkSerializer, QueryLogSerializer,
    DocumentUploadSerializer, QuerySerializer, RAGResponseSerializer
)
from .rag_pipeline import RAGPipeline
import logging
import time

logger = logging.getLogger(__name__)

# Template-based views
@login_required
def home_view(request):
    """Home page view"""
    # Get statistics
    total_documents = Document.objects.filter(uploaded_by=request.user).count()
    processed_documents = Document.objects.filter(uploaded_by=request.user, status='processed').count()
    processing_documents = Document.objects.filter(uploaded_by=request.user, status='processing').count()
    total_queries = QueryLog.objects.filter(user=request.user).count()
    
    context = {
        'total_documents': total_documents,
        'processed_documents': processed_documents,
        'processing_documents': processing_documents,
        'total_queries': total_queries,
    }
    return render(request, 'rag_system/home.html', context)

# @login_required
def upload_view(request):
    """Upload page view with bulk file support"""
    print(f"\n{'='*50}")
    print(f"🌐 UPLOAD VIEW CALLED")
    print(f"📋 Method: {request.method}")
    print(f"👤 User: {request.user}")
    print(f"{'='*50}")
    
    if request.method == 'POST':
        print("📤 Processing POST request")
        try:
            print(f"📋 Request FILES: {list(request.FILES.keys())}")
            print(f"📋 Request POST: {list(request.POST.keys())}")
            
            # Handle both single and bulk file uploads
            files = request.FILES.getlist('files')  # For bulk upload
            single_file = request.FILES.get('file')  # For single file (backward compatibility)
            
            if single_file:
                files = [single_file]
            
            if not files:
                print("❌ No files provided")
                return JsonResponse({'success': False, 'error': 'No files provided'})
            
            print(f"📁 Processing {len(files)} file(s)")
            
            # Initialize RAG pipeline once for all files
            print("🔧 Initializing RAG pipeline...")
            pipeline_start = time.time()
            rag_pipeline = RAGPipeline()
            pipeline_init_time = time.time() - pipeline_start
            print(f"✅ RAG pipeline initialized in {pipeline_init_time:.3f}s")
            
            # Process each file
            uploaded_documents = []
            failed_files = []
            
            for i, file_obj in enumerate(files):
                print(f"\n📄 Processing file {i+1}/{len(files)}: {file_obj.name}")
                
                try:
                    # Validate file
                    if not file_obj.name.lower().endswith('.pdf'):
                        print(f"⚠️ Skipping non-PDF file: {file_obj.name}")
                        failed_files.append({
                            'name': file_obj.name,
                            'error': 'Only PDF files are supported'
                        })
                        continue
                    
                    if file_obj.size > 50 * 1024 * 1024:  # 50MB limit
                        print(f"⚠️ File too large: {file_obj.name} ({file_obj.size} bytes)")
                        failed_files.append({
                            'name': file_obj.name,
                            'error': 'File size exceeds 50MB limit'
                        })
                        continue
                    
                    # Generate title from filename
                    title = request.POST.get('title', '') or file_obj.name.replace('.pdf', '').replace('_', ' ')
                    
                    print(f"📝 Title: {title}")
                    print(f"✅ File validated: {file_obj.name}, Size: {file_obj.size}, Type: {file_obj.content_type}")
                    
                    # Upload to MinIO
                    print(f"📤 Uploading {file_obj.name} to MinIO...")
                    minio_start = time.time()
                    minio_object_name = rag_pipeline.minio_client.upload_file_object(file_obj, file_obj.name)
                    minio_time = time.time() - minio_start
                    print(f"✅ MinIO upload successful: {minio_object_name}")
                    print(f"⏱️ MinIO upload time: {minio_time:.3f}s")
                    
                    # Create document record
                    print(f"💾 Creating document record for {file_obj.name}...")
                    db_start = time.time()
                    document = Document.objects.create(
                        title=title,
                        file_name=file_obj.name,
                        minio_object_name=minio_object_name,
                        file_size=file_obj.size,
                        file_type=file_obj.content_type,
                        uploaded_by=request.user if request.user.is_authenticated else None
                    )
                    db_time = time.time() - db_start
                    print(f"✅ Document created with ID: {document.id}")
                    print(f"⏱️ Database creation time: {db_time:.3f}s")
                    
                    # Process document in background
                    print(f"🔄 Starting background processing for {file_obj.name}...")
                    def process_document():
                        try:
                            print(f"🔄 Processing document {document.id} in background...")
                            print(f"📄 Document: {document.title}")
                            print(f"📁 File: {document.file_name}")
                            print(f"📊 Size: {document.file_size} bytes")
                            
                            processing_start = time.time()
                            success = rag_pipeline.process_document(document)
                            processing_time = time.time() - processing_start
                            
                            if success:
                                print(f"✅ Document {document.id} processing completed successfully in {processing_time:.3f}s")
                            else:
                                print(f"❌ Document {document.id} processing failed after {processing_time:.3f}s")
                                
                        except Exception as e:
                            print(f"❌ Background processing error for {document.file_name}: {e}")
                            import traceback
                            traceback.print_exc()
                            document.status = 'failed'
                            document.error_message = str(e)
                            document.save()
                    
                    thread = threading.Thread(target=process_document)
                    thread.start()
                    print(f"✅ Background processing thread started for {file_obj.name}")
                    
                    uploaded_documents.append({
                        'id': document.id,
                        'name': file_obj.name,
                        'title': title,
                        'size': file_obj.size
                    })
                    
                except Exception as e:
                    print(f"❌ Error processing file {file_obj.name}: {e}")
                    failed_files.append({
                        'name': file_obj.name,
                        'error': str(e)
                    })
            
            total_time = time.time() - pipeline_start
            print(f"\n✅ Upload processing completed in {total_time:.3f}s")
            print(f"📊 Summary:")
            print(f"   - Pipeline init: {pipeline_init_time:.3f}s")
            print(f"   - Files processed: {len(uploaded_documents)}")
            print(f"   - Files failed: {len(failed_files)}")
            print(f"   - Total time: {total_time:.3f}s")
            
            # Return response
            response_data = {
                'success': True,
                'message': f'Successfully uploaded {len(uploaded_documents)} file(s)',
                'uploaded_files': uploaded_documents,
                'failed_files': failed_files,
                'total_files': len(files),
                'successful_uploads': len(uploaded_documents),
                'failed_uploads': len(failed_files)
            }
            
            if failed_files:
                response_data['message'] += f', {len(failed_files)} file(s) failed'
            
            return JsonResponse(response_data)
            
        except Exception as e:
            print(f"❌ Error in upload view: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error uploading documents: {e}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    print("📄 Rendering upload template")
    return render(request, 'rag_system/upload.html')

@login_required
def query_view(request):
    """Query page view"""
    # Get documents for filter dropdown
    documents = Document.objects.filter(uploaded_by=request.user, status='processed')
    
    context = {
        'documents': documents,
    }
    return render(request, 'rag_system/query.html', context)

@login_required
def documents_view(request):
    """Documents list view"""
    documents = Document.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    
    context = {
        'documents': documents,
    }
    return render(request, 'rag_system/documents.html', context)

# API views for AJAX calls
@login_required
@require_http_methods(["POST"])
def query_api_view(request):
    """API endpoint for RAG queries"""
    print(f"\n{'='*50}")
    print(f"🔍 QUERY API VIEW CALLED")
    print(f"👤 User: {request.user}")
    print(f"{'='*50}")
    
    try:
        data = json.loads(request.body)
        query_text = data.get('query', '').strip()
        num_results = data.get('num_results', 5)
        filter_metadata = data.get('filter_metadata')
        
        print(f"📝 Query: '{query_text}'")
        print(f"📊 Requesting {num_results} results")
        if filter_metadata:
            print(f"🔍 Filter: {filter_metadata}")
        
        if not query_text:
            print("❌ Empty query provided")
            return JsonResponse({'success': False, 'error': 'Query text is required'})
        
        # Initialize RAG pipeline
        print("🔧 Initializing RAG pipeline for query...")
        pipeline_start = time.time()
        rag_pipeline = RAGPipeline()
        pipeline_init_time = time.time() - pipeline_start
        print(f"✅ RAG pipeline initialized in {pipeline_init_time:.3f}s")
        
        # Perform query
        print("🔍 Performing RAG query...")
        query_start = time.time()
        result = rag_pipeline.query(
            query_text, 
            num_results=num_results,
            filter_metadata=filter_metadata
        )
        query_time = time.time() - query_start
        print(f"✅ Query completed in {query_time:.3f}s")
        
        # Log query
        print("💾 Logging query...")
        log_start = time.time()
        query_log = QueryLog.objects.create(
            user=request.user,
            query_text=query_text,
            num_results=result.get('total_results', 0),
            search_time=result.get('search_time', 0),
            total_time=result.get('total_time', 0)
        )
        log_time = time.time() - log_start
        print(f"✅ Query logged in {log_time:.3f}s")
        
        # Add retrieved chunks to log
        print("🔗 Linking retrieved chunks to log...")
        chunk_link_start = time.time()
        linked_chunks = 0
        for search_result in result.get('results', []):
            chunk_id = search_result.get('id')
            if chunk_id:
                try:
                    chunk = DocumentChunk.objects.get(vector_store_id=chunk_id)
                    query_log.retrieved_chunks.add(chunk)
                    linked_chunks += 1
                except DocumentChunk.DoesNotExist:
                    print(f"⚠️ Chunk not found in database: {chunk_id[:8]}...")
        
        chunk_link_time = time.time() - chunk_link_start
        print(f"✅ Linked {linked_chunks} chunks to query log in {chunk_link_time:.3f}s")
        
        total_time = time.time() - pipeline_start
        print(f"✅ Query API completed successfully in {total_time:.3f}s")
        print(f"📊 Summary:")
        print(f"   - Pipeline init: {pipeline_init_time:.3f}s")
        print(f"   - Query execution: {query_time:.3f}s")
        print(f"   - Query logging: {log_time:.3f}s")
        print(f"   - Chunk linking: {chunk_link_time:.3f}s")
        print(f"   - Total: {total_time:.3f}s")
        print(f"   - Results: {result.get('total_results', 0)}")
        
        return JsonResponse({
            'success': True,
            'data': result
        })
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        print(f"❌ Query API error: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Error in query API: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

# Existing API ViewSets
class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for Document model"""
    
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset by user"""
        return Document.objects.filter(uploaded_by=self.request.user)
    
    def perform_create(self, serializer):
        """Set the uploaded_by field to the current user"""
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a document and process it through the RAG pipeline"""
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            try:
                file_obj = serializer.validated_data['file']
                title = serializer.validated_data.get('title', file_obj.name)
                
                # Initialize RAG pipeline
                rag_pipeline = RAGPipeline()
                
                # Upload to MinIO
                minio_object_name = rag_pipeline.minio_client.upload_file_object(
                    file_obj, file_obj.name
                )
                
                # Create document record
                document = Document.objects.create(
                    title=title,
                    file_name=file_obj.name,
                    minio_object_name=minio_object_name,
                    file_size=file_obj.size,
                    file_type=file_obj.content_type,
                    uploaded_by=request.user
                )
                
                # Process document in background
                def process_document():
                    rag_pipeline.process_document(document)
                
                thread = threading.Thread(target=process_document)
                thread.start()
                
                return Response({
                    'message': 'Document uploaded successfully and processing started',
                    'document_id': document.id,
                    'status': 'processing'
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.error(f"Error uploading document: {e}")
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Reprocess a document through the RAG pipeline"""
        document = self.get_object()
        
        if document.status == 'processing':
            return Response({
                'error': 'Document is already being processed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Clear existing chunks
            document.chunks.all().delete()
            
            # Reprocess document in background
            def reprocess_document():
                rag_pipeline = RAGPipeline()
                rag_pipeline.process_document(document)
            
            thread = threading.Thread(target=reprocess_document)
            thread.start()
            
            return Response({
                'message': 'Document reprocessing started',
                'document_id': document.id,
                'status': 'processing'
            })
            
        except Exception as e:
            logger.error(f"Error reprocessing document: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['delete'])
    def delete_document(self, request, pk=None):
        """Delete a document and all its data"""
        document = self.get_object()
        
        try:
            rag_pipeline = RAGPipeline()
            success = rag_pipeline.delete_document(document)
            
            if success:
                return Response({
                    'message': 'Document deleted successfully'
                })
            else:
                return Response({
                    'error': 'Failed to delete document'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """Upload multiple documents and process them through the RAG pipeline"""
        print(f"\n{'='*50}")
        print(f"📦 BULK UPLOAD API CALLED")
        print(f"👤 User: {request.user}")
        print(f"{'='*50}")
        
        try:
            files = request.FILES.getlist('files')
            title_prefix = request.data.get('title_prefix', '')
            
            print(f"📁 Processing {len(files)} file(s)")
            
            if not files:
                return Response({
                    'error': 'No files provided'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize RAG pipeline once for all files
            print("🔧 Initializing RAG pipeline...")
            pipeline_start = time.time()
            rag_pipeline = RAGPipeline()
            pipeline_init_time = time.time() - pipeline_start
            print(f"✅ RAG pipeline initialized in {pipeline_init_time:.3f}s")
            
            # Process each file
            uploaded_documents = []
            failed_files = []
            
            for i, file_obj in enumerate(files):
                print(f"\n📄 Processing file {i+1}/{len(files)}: {file_obj.name}")
                
                try:
                    # Validate file
                    if not file_obj.name.lower().endswith('.pdf'):
                        print(f"⚠️ Skipping non-PDF file: {file_obj.name}")
                        failed_files.append({
                            'name': file_obj.name,
                            'error': 'Only PDF files are supported'
                        })
                        continue
                    
                    if file_obj.size > 50 * 1024 * 1024:  # 50MB limit
                        print(f"⚠️ File too large: {file_obj.name} ({file_obj.size} bytes)")
                        failed_files.append({
                            'name': file_obj.name,
                            'error': 'File size exceeds 50MB limit'
                        })
                        continue
                    
                    # Generate title
                    title = title_prefix + file_obj.name.replace('.pdf', '').replace('_', ' ') if title_prefix else file_obj.name.replace('.pdf', '').replace('_', ' ')
                    
                    print(f"📝 Title: {title}")
                    print(f"✅ File validated: {file_obj.name}, Size: {file_obj.size}, Type: {file_obj.content_type}")
                    
                    # Upload to MinIO
                    print(f"📤 Uploading {file_obj.name} to MinIO...")
                    minio_start = time.time()
                    minio_object_name = rag_pipeline.minio_client.upload_file_object(file_obj, file_obj.name)
                    minio_time = time.time() - minio_start
                    print(f"✅ MinIO upload successful: {minio_object_name}")
                    print(f"⏱️ MinIO upload time: {minio_time:.3f}s")
                    
                    # Create document record
                    print(f"💾 Creating document record for {file_obj.name}...")
                    db_start = time.time()
                    document = Document.objects.create(
                        title=title,
                        file_name=file_obj.name,
                        minio_object_name=minio_object_name,
                        file_size=file_obj.size,
                        file_type=file_obj.content_type,
                        uploaded_by=request.user
                    )
                    db_time = time.time() - db_start
                    print(f"✅ Document created with ID: {document.id}")
                    print(f"⏱️ Database creation time: {db_time:.3f}s")
                    
                    # Process document in background
                    print(f"🔄 Starting background processing for {file_obj.name}...")
                    def process_document():
                        try:
                            print(f"🔄 Processing document {document.id} in background...")
                            print(f"📄 Document: {document.title}")
                            print(f"📁 File: {document.file_name}")
                            print(f"📊 Size: {document.file_size} bytes")
                            
                            processing_start = time.time()
                            success = rag_pipeline.process_document(document)
                            processing_time = time.time() - processing_start
                            
                            if success:
                                print(f"✅ Document {document.id} processing completed successfully in {processing_time:.3f}s")
                            else:
                                print(f"❌ Document {document.id} processing failed after {processing_time:.3f}s")
                                
                        except Exception as e:
                            print(f"❌ Background processing error for {document.file_name}: {e}")
                            import traceback
                            traceback.print_exc()
                            document.status = 'failed'
                            document.error_message = str(e)
                            document.save()
                    
                    thread = threading.Thread(target=process_document)
                    thread.start()
                    print(f"✅ Background processing thread started for {file_obj.name}")
                    
                    uploaded_documents.append({
                        'id': document.id,
                        'name': file_obj.name,
                        'title': title,
                        'size': file_obj.size
                    })
                    
                except Exception as e:
                    print(f"❌ Error processing file {file_obj.name}: {e}")
                    failed_files.append({
                        'name': file_obj.name,
                        'error': str(e)
                    })
            
            total_time = time.time() - pipeline_start
            print(f"\n✅ Bulk upload processing completed in {total_time:.3f}s")
            print(f"📊 Summary:")
            print(f"   - Pipeline init: {pipeline_init_time:.3f}s")
            print(f"   - Files processed: {len(uploaded_documents)}")
            print(f"   - Files failed: {len(failed_files)}")
            print(f"   - Total time: {total_time:.3f}s")
            
            # Return response
            response_data = {
                'message': f'Successfully uploaded {len(uploaded_documents)} file(s)',
                'uploaded_files': uploaded_documents,
                'failed_files': failed_files,
                'total_files': len(files),
                'successful_uploads': len(uploaded_documents),
                'failed_uploads': len(failed_files)
            }
            
            if failed_files:
                response_data['message'] += f', {len(failed_files)} file(s) failed'
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"❌ Error in bulk upload: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error in bulk upload: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DocumentChunkViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for DocumentChunk model (read-only)"""
    
    queryset = DocumentChunk.objects.all()
    serializer_class = DocumentChunkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter by document and user"""
        return DocumentChunk.objects.filter(
            document__uploaded_by=self.request.user
        )
    
    @action(detail=False)
    def by_document(self, request):
        """Get chunks for a specific document"""
        document_id = request.query_params.get('document_id')
        if not document_id:
            return Response({
                'error': 'document_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        chunks = self.get_queryset().filter(document_id=document_id)
        serializer = self.get_serializer(chunks, many=True)
        return Response(serializer.data)

class QueryViewSet(viewsets.ViewSet):
    """ViewSet for RAG queries"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request):
        """Handle RAG queries"""
        print(f"\n{'='*60}")
        print(f"🔍 QUERY VIEWSET CREATE CALLED")
        print(f"👤 User: {request.user}")
        print(f"📋 Request data: {request.data}")
        print(f"📋 Request method: {request.method}")
        print(f"📋 Content type: {request.content_type}")
        print(f"{'='*60}")
        
        serializer = QuerySerializer(data=request.data)
        print(f"🔍 Validating serializer...")
        
        if serializer.is_valid():
            print(f"✅ Serializer is valid")
            try:
                query_text = serializer.validated_data['query']
                num_results = serializer.validated_data['num_results']
                filter_metadata = serializer.validated_data.get('filter_metadata')
                
                print(f"📝 Query text: '{query_text}'")
                print(f"📊 Num results: {num_results}")
                print(f"🔍 Filter metadata: {filter_metadata}")
                
                # Initialize RAG pipeline
                print(f"🔧 Initializing RAG pipeline...")
                pipeline_start = time.time()
                rag_pipeline = RAGPipeline()
                pipeline_init_time = time.time() - pipeline_start
                print(f"✅ RAG pipeline initialized in {pipeline_init_time:.3f}s")
                
                # Perform query
                print(f"🔍 Performing RAG query...")
                query_start = time.time()
                result = rag_pipeline.query(
                    query_text, 
                    num_results=num_results,
                    filter_metadata=filter_metadata
                )
                query_time = time.time() - query_start
                print(f"✅ Query completed in {query_time:.3f}s")
                print(f"📊 Query result: {result}")
                
                # Log query
                print(f"💾 Logging query...")
                log_start = time.time()
                query_log = QueryLog.objects.create(
                    user=request.user,
                    query_text=query_text,
                    num_results=result.get('total_results', 0),
                    search_time=result.get('search_time', 0),
                    total_time=result.get('total_time', 0)
                )
                log_time = time.time() - log_start
                print(f"✅ Query logged in {log_time:.3f}s")
                
                # Add retrieved chunks to log
                print(f"🔗 Linking retrieved chunks to log...")
                chunk_link_start = time.time()
                linked_chunks = 0
                for search_result in result.get('results', []):
                    chunk_id = search_result.get('id')
                    if chunk_id:
                        try:
                            chunk = DocumentChunk.objects.get(vector_store_id=chunk_id)
                            query_log.retrieved_chunks.add(chunk)
                            linked_chunks += 1
                        except DocumentChunk.DoesNotExist:
                            print(f"⚠️ Chunk not found in database: {chunk_id[:8]}...")
                
                chunk_link_time = time.time() - chunk_link_start
                print(f"✅ Linked {linked_chunks} chunks to query log in {chunk_link_time:.3f}s")
                
                total_time = time.time() - pipeline_start
                print(f"✅ Query ViewSet completed successfully in {total_time:.3f}s")
                print(f"📊 Summary:")
                print(f"   - Pipeline init: {pipeline_init_time:.3f}s")
                print(f"   - Query execution: {query_time:.3f}s")
                print(f"   - Query logging: {log_time:.3f}s")
                print(f"   - Chunk linking: {chunk_link_time:.3f}s")
                print(f"   - Total: {total_time:.3f}s")
                print(f"   - Results: {result.get('total_results', 0)}")
                
                return Response(result)
                
            except Exception as e:
                print(f"❌ Query ViewSet error: {e}")
                import traceback
                traceback.print_exc()
                logger.error(f"Error processing query: {e}")
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            print(f"❌ Serializer validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False)
    def system_info(self, request):
        """Get system information"""
        try:
            rag_pipeline = RAGPipeline()
            info = rag_pipeline.get_system_info()
            return Response(info)
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class QueryLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for QueryLog model (read-only)"""
    
    queryset = QueryLog.objects.all()
    serializer_class = QueryLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user"""
        return QueryLog.objects.filter(user=self.request.user)
