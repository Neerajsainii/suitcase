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
    """Upload page view"""
    print(f"🔍 Upload view called - Method: {request.method}")
    
    if request.method == 'POST':
        print("📤 Processing POST request")
        try:
            print(f"📋 Request FILES: {list(request.FILES.keys())}")
            print(f"📋 Request POST: {list(request.POST.keys())}")
            
            file_obj = request.FILES.get('file')
            title = request.POST.get('title', file_obj.name if file_obj else '')
            
            print(f"📁 File object: {file_obj}")
            print(f"📝 Title: {title}")
            
            if not file_obj:
                print("❌ No file provided")
                return JsonResponse({'success': False, 'error': 'No file provided'})
            
            print(f"✅ File received: {file_obj.name}, Size: {file_obj.size}, Type: {file_obj.content_type}")
            
            # Initialize RAG pipeline
            print("🔧 Initializing RAG pipeline...")
            rag_pipeline = RAGPipeline()
            
            # Upload to MinIO
            print("📤 Uploading to MinIO...")
            minio_object_name = rag_pipeline.minio_client.upload_file_object(file_obj, file_obj.name)
            print(f"✅ MinIO upload successful: {minio_object_name}")
            
            # Create document record
            print("💾 Creating document record...")
            document = Document.objects.create(
                title=title,
                file_name=file_obj.name,
                minio_object_name=minio_object_name,
                file_size=file_obj.size,
                file_type=file_obj.content_type,
                uploaded_by=request.user if request.user.is_authenticated else None
            )
            print(f"✅ Document created with ID: {document.id}")
            
            # Process document in background
            print("🔄 Starting background processing...")
            def process_document():
                try:
                    print(f"🔄 Processing document {document.id} in background...")
                    rag_pipeline.process_document(document)
                    print(f"✅ Document {document.id} processing completed")
                except Exception as e:
                    print(f"❌ Background processing error: {e}")
                    document.status = 'failed'
                    document.error_message = str(e)
                    document.save()
            
            thread = threading.Thread(target=process_document)
            thread.start()
            
            print("✅ Upload view completed successfully")
            return JsonResponse({
                'success': True,
                'message': 'Document uploaded successfully and processing started',
                'document_id': document.id
            })
            
        except Exception as e:
            print(f"❌ Error in upload view: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error uploading document: {e}")
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
    """API endpoint for querying the RAG system"""
    print("🔍 Query API view called")
    try:
        print("📋 Parsing request data...")
        data = json.loads(request.body)
        query_text = data.get('query', '').strip()
        num_results = data.get('num_results', 5)
        filter_metadata = data.get('filter_metadata', {})
        
        print(f"📝 Query: '{query_text}'")
        print(f"📊 Num results: {num_results}")
        print(f"🔍 Filter metadata: {filter_metadata}")
        
        if not query_text:
            print("❌ No query text provided")
            return JsonResponse({'error': 'Query text is required'})
        
        # Initialize RAG pipeline
        print("🔧 Initializing RAG pipeline...")
        rag_pipeline = RAGPipeline()
        
        # Perform query
        print("🔍 Performing query...")
        result = rag_pipeline.query(
            query_text, 
            num_results=num_results,
            filter_metadata=filter_metadata
        )
        
        print(f"✅ Query completed. Found {result.get('total_results', 0)} results")
        
        # Log query
        print("📊 Logging query...")
        query_log = QueryLog.objects.create(
            user=request.user,
            query_text=query_text,
            num_results=result.get('total_results', 0),
            search_time=result.get('search_time', 0),
            total_time=result.get('total_time', 0)
        )
        
        # Add retrieved chunks to log
        for search_result in result.get('results', []):
            chunk_id = search_result.get('id')
            if chunk_id:
                try:
                    chunk = DocumentChunk.objects.get(vector_store_id=chunk_id)
                    query_log.retrieved_chunks.add(chunk)
                except DocumentChunk.DoesNotExist:
                    pass
        
        print("✅ Query API view completed successfully")
        return JsonResponse(result)
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        return JsonResponse({'error': 'Invalid JSON data'})
    except Exception as e:
        print(f"❌ Error in query API view: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Error processing query: {e}")
        return JsonResponse({'error': str(e)})

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
        serializer = QuerySerializer(data=request.data)
        if serializer.is_valid():
            try:
                query_text = serializer.validated_data['query']
                num_results = serializer.validated_data['num_results']
                filter_metadata = serializer.validated_data.get('filter_metadata')
                
                # Initialize RAG pipeline
                rag_pipeline = RAGPipeline()
                
                # Perform query
                result = rag_pipeline.query(
                    query_text, 
                    num_results=num_results,
                    filter_metadata=filter_metadata
                )
                
                # Log query
                query_log = QueryLog.objects.create(
                    user=request.user,
                    query_text=query_text,
                    num_results=result.get('total_results', 0),
                    search_time=result.get('search_time', 0),
                    total_time=result.get('total_time', 0)
                )
                
                # Add retrieved chunks to log
                for search_result in result.get('results', []):
                    chunk_id = search_result.get('id')
                    if chunk_id:
                        try:
                            chunk = DocumentChunk.objects.get(vector_store_id=chunk_id)
                            query_log.retrieved_chunks.add(chunk)
                        except DocumentChunk.DoesNotExist:
                            pass
                
                return Response(result)
                
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                return Response({
                    'error': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
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
