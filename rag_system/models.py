"""
Django models for the RAG system
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json

class Document(models.Model):
    """Model for storing document information"""
    
    DOCUMENT_STATUS = (
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    )
    
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    minio_object_name = models.CharField(max_length=500, unique=True)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=50)
    
    # Processing status
    status = models.CharField(max_length=20, choices=DOCUMENT_STATUS, default='uploaded')
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Document metadata
    num_pages = models.IntegerField(default=0)
    total_chunks = models.IntegerField(default=0)
    metadata_json = models.TextField(blank=True)  # Store PDF metadata as JSON
    
    # Timestamps
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} ({self.file_name})"
    
    @property
    def metadata(self):
        """Get metadata as dictionary"""
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @metadata.setter
    def metadata(self, value):
        """Set metadata as JSON string"""
        self.metadata_json = json.dumps(value) if value else ""

class DocumentChunk(models.Model):
    """Model for storing document chunks with embeddings"""
    
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_id = models.CharField(max_length=100, unique=True)
    
    # Chunk content
    text = models.TextField()
    chunk_index = models.IntegerField()
    
    # Metadata
    page_number = models.IntegerField(null=True, blank=True)
    start_char = models.IntegerField(null=True, blank=True)
    end_char = models.IntegerField(null=True, blank=True)
    metadata_json = models.TextField(blank=True)
    
    # Vector store info
    vector_store_id = models.CharField(max_length=100, blank=True)
    embedding_dim = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['document', 'chunk_index']
        unique_together = ['document', 'chunk_index']
    
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"
    
    @property
    def metadata(self):
        """Get metadata as dictionary"""
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @metadata.setter
    def metadata(self, value):
        """Set metadata as JSON string"""
        self.metadata_json = json.dumps(value) if value else ""

class QueryLog(models.Model):
    """Model for logging user queries and responses"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query_text = models.TextField()
    response_text = models.TextField(blank=True)
    
    # Search results
    retrieved_chunks = models.ManyToManyField(DocumentChunk, blank=True)
    num_results = models.IntegerField(default=0)
    
    # Performance metrics
    search_time = models.FloatField(null=True, blank=True)  # in seconds
    total_time = models.FloatField(null=True, blank=True)   # in seconds
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Query by {self.user.username} at {self.created_at}"
