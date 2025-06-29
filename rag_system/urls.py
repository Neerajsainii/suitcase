"""
URL patterns for the RAG system
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentViewSet, DocumentChunkViewSet, QueryViewSet, QueryLogViewSet,
    home_view, upload_view, query_view, documents_view, query_api_view
)

app_name = "rag_system"

# Create router and register viewsets
router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'chunks', DocumentChunkViewSet, basename='chunk')
router.register(r'queries', QueryViewSet, basename='query')
router.register(r'query-logs', QueryLogViewSet, basename='querylog')

# Template-based URLs
template_urls = [
    path('', home_view, name='home'),
    path('upload/', upload_view, name='upload'),
    path('query/', query_view, name='query'),
    path('documents/', documents_view, name='documents'),
    path('api/query/', query_api_view, name='query_api'),
]

urlpatterns = template_urls + [
    path('api/', include(router.urls)),
] 