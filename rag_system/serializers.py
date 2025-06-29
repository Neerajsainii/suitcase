"""
Serializers for the RAG system
"""
from rest_framework import serializers
from .models import Document, DocumentChunk, QueryLog

class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    
    uploaded_by = serializers.ReadOnlyField(source='uploaded_by.username')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file_name', 'minio_object_name', 'file_size', 'file_type',
            'status', 'status_display', 'processing_started', 'processing_completed',
            'error_message', 'num_pages', 'total_chunks', 'metadata', 'uploaded_by',
            'uploaded_at', 'updated_at'
        ]
        read_only_fields = [
            'minio_object_name', 'file_size', 'file_type', 'status', 'processing_started',
            'processing_completed', 'error_message', 'num_pages', 'total_chunks',
            'uploaded_by', 'uploaded_at', 'updated_at'
        ]

class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for DocumentChunk model"""
    
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = DocumentChunk
        fields = [
            'id', 'document', 'document_title', 'chunk_id', 'text', 'chunk_index',
            'page_number', 'start_char', 'end_char', 'metadata', 'vector_store_id',
            'embedding_dim', 'created_at'
        ]
        read_only_fields = [
            'chunk_id', 'vector_store_id', 'embedding_dim', 'created_at'
        ]

class QueryLogSerializer(serializers.ModelSerializer):
    """Serializer for QueryLog model"""
    
    user = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = QueryLog
        fields = [
            'id', 'user', 'query_text', 'response_text', 'num_results',
            'search_time', 'total_time', 'created_at'
        ]
        read_only_fields = [
            'user', 'response_text', 'num_results', 'search_time', 'total_time', 'created_at'
        ]

class DocumentUploadSerializer(serializers.Serializer):
    """Serializer for document upload"""
    
    file = serializers.FileField()
    title = serializers.CharField(max_length=255, required=False)
    
    def validate_file(self, value):
        """Validate uploaded file"""
        # Check file size (max 50MB)
        if value.size > 50 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 50MB")
        
        # Check file type
        allowed_types = ['application/pdf']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only PDF files are allowed")
        
        return value

class QuerySerializer(serializers.Serializer):
    """Serializer for RAG queries"""
    
    query = serializers.CharField(max_length=1000)
    num_results = serializers.IntegerField(default=5, min_value=1, max_value=20)
    filter_metadata = serializers.JSONField(required=False)
    
    def validate_num_results(self, value):
        """Validate number of results"""
        if value < 1 or value > 20:
            raise serializers.ValidationError("Number of results must be between 1 and 20")
        return value

class SearchResultSerializer(serializers.Serializer):
    """Serializer for search results"""
    
    id = serializers.CharField()
    text = serializers.CharField()
    metadata = serializers.JSONField()
    distance = serializers.FloatField(required=False)
    similarity_score = serializers.FloatField(required=False)

class RAGResponseSerializer(serializers.Serializer):
    """Serializer for RAG system responses"""
    
    query = serializers.CharField()
    results = SearchResultSerializer(many=True)
    total_results = serializers.IntegerField()
    search_time = serializers.FloatField()
    total_time = serializers.FloatField()
    model_info = serializers.JSONField(required=False) 