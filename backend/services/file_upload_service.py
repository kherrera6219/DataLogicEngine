"""
File Upload Service

Handles file uploads with ObjectStore integration for persistent storage.
Works with DocumentProcessor for content extraction and RAG for embeddings.
"""

import logging
import uuid
import hashlib
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UploadedFile:
    """Represents an uploaded file."""
    id: str
    filename: str
    mime_type: str
    size_bytes: int
    storage_path: str
    upload_time: datetime
    user_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None
    processed: bool = False
    processing_result: Optional[Dict[str, Any]] = None


class FileUploadService:
    """
    Service for handling file uploads.
    
    Integrates with:
    - ObjectStore: For persisting files (local or S3)
    - DocumentProcessor: For extracting text content
    - RAGService: For storing document embeddings
    """
    
    BUCKET_UPLOADS = "uploads"
    BUCKET_DOCUMENTS = "documents"
    BUCKET_MEDIA = "media"
    BUCKET_EXPORTS = "exports"
    
    # Max file sizes by type (in bytes)
    MAX_SIZES = {
        "application/pdf": 50 * 1024 * 1024,           # 50MB
        "image/png": 10 * 1024 * 1024,                 # 10MB
        "image/jpeg": 10 * 1024 * 1024,                # 10MB
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": 25 * 1024 * 1024,  # 25MB
        "text/plain": 5 * 1024 * 1024,                 # 5MB
        "audio/mpeg": 100 * 1024 * 1024,               # 100MB
        "video/mp4": 500 * 1024 * 1024,                # 500MB
    }

    MAGIC_SIGNATURES = {
        "application/pdf": [b"%PDF-"],
        "image/png": [b"\x89PNG\r\n\x1a\n"],
        "image/jpeg": [b"\xff\xd8\xff"],
        "video/mp4": [b"ftyp"],  # checked in first bytes window
        "audio/mpeg": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [b"PK\x03\x04"],
    }
    
    def __init__(self, object_store=None, document_processor=None, rag_service=None):
        """
        Initialize the file upload service.
        
        Args:
            object_store: ObjectStore instance (uses global if None)
            document_processor: Document processor (uses global if None)
            rag_service: RAG service for embeddings (uses global if None)
        """
        self._object_store = object_store
        self._document_processor = document_processor
        self._rag_service = rag_service
        
    def _get_object_store(self):
        """Lazy load object store."""
        if self._object_store is None:
            try:
                from backend.storage import get_object_store
                self._object_store = get_object_store()
            except Exception as e:
                logger.warning(f"ObjectStore not available: {e}")
                return None
        return self._object_store
    
    def _get_document_processor(self):
        """Lazy load document processor."""
        if self._document_processor is None:
            try:
                from backend.services.document_processor import document_processor
                self._document_processor = document_processor
            except Exception as e:
                logger.warning(f"DocumentProcessor not available: {e}")
                return None
        return self._document_processor
    
    def _get_rag_service(self):
        """Lazy load RAG service."""
        if self._rag_service is None:
            try:
                from backend.services.rag_service import get_rag_service
                self._rag_service = get_rag_service()
            except Exception as e:
                logger.warning(f"RAGService not available: {e}")
                return None
        return self._rag_service
    
    def _compute_checksum(self, data: bytes) -> str:
        """Compute SHA-256 checksum of file data."""
        return hashlib.sha256(data).hexdigest()
    
    def _get_bucket_for_type(self, mime_type: str) -> str:
        """Determine appropriate bucket based on file type."""
        if mime_type.startswith("image/") or mime_type.startswith("video/") or mime_type.startswith("audio/"):
            return self.BUCKET_MEDIA
        elif mime_type in ["application/pdf", "text/plain"] or "document" in mime_type:
            return self.BUCKET_DOCUMENTS
        return self.BUCKET_UPLOADS

    def _matches_magic_signature(self, file_bytes: bytes, mime_type: str) -> bool:
        """Validate file signatures to reduce MIME spoofing risk."""
        if mime_type == "text/plain":
            # Text should not contain NUL bytes in initial window.
            return b"\x00" not in file_bytes[:1024]

        signatures = self.MAGIC_SIGNATURES.get(mime_type)
        if not signatures:
            return False

        window = file_bytes[:64]
        if mime_type == "video/mp4":
            return b"ftyp" in file_bytes[:32]

        return any(window.startswith(sig) for sig in signatures)
    
    def validate_file(self, file_bytes: bytes, filename: str, mime_type: str) -> tuple[bool, str]:
        """
        Validate file before upload.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if empty
        if not file_bytes:
            return False, "File is empty"
        
        # Check file size
        max_size = self.MAX_SIZES.get(mime_type, 10 * 1024 * 1024)  # Default 10MB
        if len(file_bytes) > max_size:
            return False, f"File exceeds maximum size of {max_size // 1024 // 1024}MB"
        
        # Check filename
        if not filename or len(filename) > 255:
            return False, "Invalid filename"

        # Check binary signature to prevent MIME spoofing.
        if not self._matches_magic_signature(file_bytes, mime_type):
            return False, "File signature does not match declared MIME type"
        
        return True, ""
    
    def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        user_id: Optional[int] = None,
        process_content: bool = True,
        extract_embeddings: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UploadedFile:
        """
        Upload a file to object storage.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            mime_type: MIME type of the file
            user_id: Optional user ID who uploaded
            process_content: Whether to extract text content
            extract_embeddings: Whether to generate embeddings for RAG
            metadata: Additional metadata to store
            
        Returns:
            UploadedFile object with upload details
            
        Raises:
            ValueError: If validation fails
            RuntimeError: If storage fails
        """
        # Validate
        is_valid, error = self.validate_file(file_bytes, filename, mime_type)
        if not is_valid:
            raise ValueError(error)
        
        # Generate unique ID and storage path
        file_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)
        date_prefix = timestamp.strftime("%Y/%m/%d")
        ext = filename.split(".")[-1] if "." in filename else ""
        storage_key = f"{date_prefix}/{file_id}.{ext}" if ext else f"{date_prefix}/{file_id}"
        
        # Determine bucket
        bucket = self._get_bucket_for_type(mime_type)
        
        # Compute checksum
        checksum = self._compute_checksum(file_bytes)
        
        # Create result object
        result = UploadedFile(
            id=file_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=len(file_bytes),
            storage_path=f"{bucket}/{storage_key}",
            upload_time=timestamp,
            user_id=user_id,
            metadata=metadata or {},
            checksum=checksum
        )
        
        # Upload to object store
        store = self._get_object_store()
        if store is None:
            raise RuntimeError("Object storage not available")
        
        try:
            store.put(
                bucket=bucket,
                key=storage_key,
                data=file_bytes,
                content_type=mime_type,
                metadata={
                    "original_filename": filename,
                    "upload_id": file_id,
                    "user_id": str(user_id) if user_id else None,
                    "checksum": checksum
                }
            )
            logger.info(f"Uploaded file {filename} to {bucket}/{storage_key}")
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {e}")
            raise RuntimeError(f"Storage failed: {e}")
        
        # Process document content
        if process_content:
            processor = self._get_document_processor()
            if processor:
                try:
                    process_result = processor.process_file(file_bytes, filename, mime_type)
                    result.processed = True
                    result.processing_result = process_result
                    
                    # Extract embeddings for RAG
                    if extract_embeddings and process_result.get("text"):
                        rag = self._get_rag_service()
                        if rag:
                            chunks = rag.ingest_document(
                                doc_id=file_id,
                                text=process_result["text"],
                                metadata={
                                    "filename": filename,
                                    "mime_type": mime_type,
                                    "user_id": user_id,
                                    "storage_path": result.storage_path
                                }
                            )
                            result.metadata["embedded_chunks"] = chunks
                            logger.info(f"Generated {chunks} embeddings for {filename}")
                except Exception as e:
                    logger.warning(f"Content processing failed for {filename}: {e}")
        
        return result
    
    def get_file(self, bucket: str, key: str) -> Optional[bytes]:
        """
        Retrieve a file from object storage.
        
        Args:
            bucket: Storage bucket
            key: File key/path
            
        Returns:
            File bytes or None if not found
        """
        store = self._get_object_store()
        if store is None:
            return None
        
        try:
            return store.get(bucket, key)
        except Exception as e:
            logger.error(f"Failed to retrieve {bucket}/{key}: {e}")
            return None
    
    def delete_file(self, bucket: str, key: str) -> bool:
        """
        Delete a file from object storage.
        
        Args:
            bucket: Storage bucket
            key: File key/path
            
        Returns:
            True if deleted, False otherwise
        """
        store = self._get_object_store()
        if store is None:
            return False
        
        try:
            store.delete(bucket, key)
            logger.info(f"Deleted file {bucket}/{key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {bucket}/{key}: {e}")
            return False
    
    def list_files(self, bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
        """
        List files in a bucket.
        
        Args:
            bucket: Storage bucket
            prefix: Optional key prefix filter
            
        Returns:
            List of file info dictionaries
        """
        store = self._get_object_store()
        if store is None:
            return []
        
        try:
            return store.list_objects(bucket, prefix)
        except Exception as e:
            logger.error(f"Failed to list {bucket}/{prefix}: {e}")
            return []


# Global instance
_file_upload_service: Optional[FileUploadService] = None


def get_file_upload_service() -> FileUploadService:
    """Get or create the global file upload service instance."""
    global _file_upload_service
    if _file_upload_service is None:
        _file_upload_service = FileUploadService()
    return _file_upload_service
