"""
MinIO Client for handling file storage and retrieval
"""
import os
import uuid
from typing import Optional, List, Dict, Any
from minio import Minio
from minio.error import S3Error
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MinIOClient:
    """
    Client for interacting with MinIO object storage
    """
    
    def __init__(self):
        """Initialize MinIO client with settings"""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    def upload_file(self, file_path: str, file_name: Optional[str] = None) -> str:
        """
        Upload a file to MinIO
        
        Args:
            file_path: Path to the file to upload
            file_name: Optional custom file name
            
        Returns:
            str: The object name in MinIO
        """
        try:
            if not file_name:
                file_name = os.path.basename(file_path)
            
            # Generate unique object name
            object_name = f"{uuid.uuid4()}/{file_name}"
            
            # Upload file
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path
            )
            
            logger.info(f"Uploaded file: {file_path} -> {object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            raise
    
    def upload_file_object(self, file_object, file_name: str) -> str:
        """
        Upload a file object (e.g., from Django form) to MinIO
        
        Args:
            file_object: File object to upload
            file_name: Name for the file
            
        Returns:
            str: The object name in MinIO
        """
        try:
            # Generate unique object name
            object_name = f"{uuid.uuid4()}/{file_name}"
            
            # Upload file object
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_object,
                file_object.size
            )
            
            logger.info(f"Uploaded file object: {file_name} -> {object_name}")
            return object_name
            
        except S3Error as e:
            logger.error(f"Error uploading file object {file_name}: {e}")
            raise
    
    def download_file(self, object_name: str, local_path: str) -> bool:
        """
        Download a file from MinIO
        
        Args:
            object_name: Name of the object in MinIO
            local_path: Local path to save the file
            
        Returns:
            bool: True if successful
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Download file
            self.client.fget_object(
                self.bucket_name,
                object_name,
                local_path
            )
            
            logger.info(f"Downloaded file: {object_name} -> {local_path}")
            return True
            
        except S3Error as e:
            logger.error(f"Error downloading file {object_name}: {e}")
            return False
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Get a presigned URL for file access
        
        Args:
            object_name: Name of the object in MinIO
            expires: URL expiration time in seconds
            
        Returns:
            str: Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL for {object_name}: {e}")
            raise
    
    def delete_file(self, object_name: str) -> bool:
        """
        Delete a file from MinIO
        
        Args:
            object_name: Name of the object to delete
            
        Returns:
            bool: True if successful
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted file: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting file {object_name}: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[Dict[str, Any]]:
        """
        List files in the bucket
        
        Args:
            prefix: Optional prefix to filter files
            
        Returns:
            List of file information dictionaries
        """
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            files = []
            
            for obj in objects:
                files.append({
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag
                })
            
            return files
        except S3Error as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in MinIO
        
        Args:
            object_name: Name of the object to check
            
        Returns:
            bool: True if file exists
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_info(self, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from MinIO
        
        Args:
            object_name: Name of the object
            
        Returns:
            Dict with file information or None if not found
        """
        try:
            stat = self.client.stat_object(self.bucket_name, object_name)
            return {
                'name': object_name,
                'size': stat.size,
                'last_modified': stat.last_modified,
                'etag': stat.etag,
                'content_type': stat.content_type
            }
        except S3Error as e:
            logger.error(f"Error getting file info for {object_name}: {e}")
            return None 