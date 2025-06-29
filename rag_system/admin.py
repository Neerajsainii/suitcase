"""
Admin configuration for the RAG system
"""
from django.contrib import admin
from .models import Document, DocumentChunk, QueryLog

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model"""
    
    list_display = [
        'title', 'file_name', 'status', 'num_pages', 'total_chunks', 
        'uploaded_by', 'uploaded_at'
    ]
    list_filter = ['status', 'file_type', 'uploaded_at']
    search_fields = ['title', 'file_name', 'uploaded_by__username']
    readonly_fields = [
        'minio_object_name', 'file_size', 'file_type', 'processing_started',
        'processing_completed', 'uploaded_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'file_name', 'minio_object_name', 'file_size', 'file_type')
        }),
        ('Processing Status', {
            'fields': ('status', 'processing_started', 'processing_completed', 'error_message')
        }),
        ('Document Metadata', {
            'fields': ('num_pages', 'total_chunks', 'metadata_json')
        }),
        ('User Information', {
            'fields': ('uploaded_by', 'uploaded_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related('uploaded_by')

@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    """Admin interface for DocumentChunk model"""
    
    list_display = [
        'document_title', 'chunk_index', 'page_number', 'embedding_dim',
        'created_at'
    ]
    list_filter = ['page_number', 'embedding_dim', 'created_at']
    search_fields = ['document__title', 'text']
    readonly_fields = [
        'chunk_id', 'vector_store_id', 'embedding_dim', 'created_at'
    ]
    
    def document_title(self, obj):
        return obj.document.title
    document_title.short_description = 'Document'
    
    fieldsets = (
        ('Document Information', {
            'fields': ('document', 'chunk_id', 'chunk_index')
        }),
        ('Content', {
            'fields': ('text', 'page_number', 'start_char', 'end_char')
        }),
        ('Vector Store', {
            'fields': ('vector_store_id', 'embedding_dim', 'metadata_json')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related('document')

@admin.register(QueryLog)
class QueryLogAdmin(admin.ModelAdmin):
    """Admin interface for QueryLog model"""
    
    list_display = [
        'user', 'query_text_short', 'num_results', 'search_time', 
        'total_time', 'created_at'
    ]
    list_filter = ['created_at', 'num_results']
    search_fields = ['user__username', 'query_text', 'response_text']
    readonly_fields = [
        'search_time', 'total_time', 'created_at'
    ]
    
    def query_text_short(self, obj):
        """Show shortened query text"""
        return obj.query_text[:100] + '...' if len(obj.query_text) > 100 else obj.query_text
    query_text_short.short_description = 'Query'
    
    fieldsets = (
        ('Query Information', {
            'fields': ('user', 'query_text', 'response_text')
        }),
        ('Results', {
            'fields': ('retrieved_chunks', 'num_results')
        }),
        ('Performance', {
            'fields': ('search_time', 'total_time')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related fields"""
        return super().get_queryset(request).select_related('user')
