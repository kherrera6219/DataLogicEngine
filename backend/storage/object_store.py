"""
Object Store for DataLogicEngine.

Provides unified interface for object/blob storage with support for:
- Local: Filesystem-based storage
- Cloud: S3-compatible (AWS S3, MinIO, etc.)
"""

import mimetypes
import hashlib
import logging
import re
from pathlib import Path, PurePosixPath
from typing import List, Dict, Optional, BinaryIO, Union
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


def object_store_is_required() -> bool:
    """Return whether the active runtime forbids filesystem/fail-soft storage."""
    try:
        from flask import current_app, has_app_context

        return bool(
            has_app_context()
            and (
                current_app.config.get("DLE_PRODUCTION_MODE")
                or current_app.config.get("DLE_DATA_PLANE_DRIVER") == "podman"
            )
        )
    except ImportError:
        return False


def raise_if_object_store_required(exc: Exception, operation: str) -> None:
    """Fail a required artifact operation without exposing the provider error."""
    if object_store_is_required():
        raise RuntimeError(f"required_object_store_{operation}_failed") from exc


@dataclass
class ObjectInfo:
    """Metadata about a stored object."""
    key: str
    size: int
    content_type: str
    last_modified: datetime
    etag: Optional[str] = None
    metadata: Dict[str, str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ObjectBackend(ABC):
    """Abstract base class for object storage backends."""
    
    @abstractmethod
    def put(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO],
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Store an object. Returns the object key."""
        pass
    
    @abstractmethod
    def get(self, bucket: str, key: str) -> bytes:
        """Retrieve an object's contents."""
        pass
    
    @abstractmethod
    def delete(self, bucket: str, key: str) -> bool:
        """Delete an object."""
        pass
    
    @abstractmethod
    def exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists."""
        pass
    
    @abstractmethod
    def list(self, bucket: str, prefix: str = "") -> List[ObjectInfo]:
        """List objects with optional prefix filter."""
        pass
    
    @abstractmethod
    def get_info(self, bucket: str, key: str) -> Optional[ObjectInfo]:
        """Get metadata about an object."""
        pass
    
    @abstractmethod
    def get_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """Get a URL to access the object."""
        pass
    
    @abstractmethod
    def create_bucket(self, bucket: str) -> bool:
        """Create a new bucket/container."""
        pass


class LocalFileBackend(ObjectBackend):
    """Local filesystem backend for object storage."""

    _BUCKET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    
    def __init__(self, base_path: str = "./databases/objects"):
        self.base_path = Path(base_path).absolute()
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalFileBackend initialized at {self.base_path}")

    def _sanitize_bucket(self, bucket: str) -> str:
        bucket_name = str(bucket or "").strip()
        if not self._BUCKET_RE.fullmatch(bucket_name):
            raise ValueError(f"Invalid bucket name: {bucket!r}")
        return bucket_name

    @staticmethod
    def _sanitize_key(key: str) -> str:
        normalized = str(key or "").replace("\\", "/").strip()
        if not normalized:
            raise ValueError("Object key cannot be empty")
        if "\x00" in normalized:
            raise ValueError("Object key contains invalid null byte")

        path = PurePosixPath(normalized)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Object key path traversal detected")

        safe_key = str(path).lstrip("./")
        if not safe_key:
            raise ValueError("Object key cannot be empty")
        return safe_key
    
    def _get_path(self, bucket: str, key: str) -> Path:
        """Get full filesystem path for an object."""
        safe_bucket = self._sanitize_bucket(bucket)
        safe_key = self._sanitize_key(key)

        bucket_root = (self.base_path / safe_bucket).resolve()
        resolved_path = (bucket_root / safe_key).resolve()
        try:
            resolved_path.relative_to(bucket_root)
        except ValueError as exc:
            raise ValueError("Object key resolved outside bucket root") from exc

        return resolved_path
    
    def _ensure_parent(self, path: Path):
        """Ensure parent directory exists."""
        path.parent.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _compute_etag(data: bytes) -> str:
        """Compute deterministic object hash for ETag metadata."""
        return hashlib.sha256(data).hexdigest()
    
    def put(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO],
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Store an object in local filesystem."""
        try:
            path = self._get_path(bucket, key)
            self._ensure_parent(path)
            
            # Handle both bytes and file-like objects
            if isinstance(data, bytes):
                content = data
            else:
                content = data.read()
            
            # Write object
            path.write_bytes(content)
            
            # Write metadata if provided
            if content_type or metadata:
                meta_path = path.with_suffix(path.suffix + '.meta')
                meta = metadata or {}
                if content_type:
                    meta['_content_type'] = content_type
                
                import json
                meta_path.write_text(json.dumps(meta))
            
            logger.debug(f"Stored object: {bucket}/{key} ({len(content)} bytes)")
            return key
        except Exception as e:
            logger.error(f"Failed to store object {bucket}/{key}: {e}")
            raise
    
    def get(self, bucket: str, key: str) -> bytes:
        """Retrieve an object from local filesystem."""
        try:
            path = self._get_path(bucket, key)
            if not path.exists():
                raise FileNotFoundError(f"Object not found: {bucket}/{key}")
            return path.read_bytes()
        except Exception as e:
            logger.error(f"Failed to get object {bucket}/{key}: {e}")
            raise
    
    def delete(self, bucket: str, key: str) -> bool:
        """Delete an object from local filesystem."""
        try:
            path = self._get_path(bucket, key)
            if path.exists():
                path.unlink()
                
                # Also delete metadata file if exists
                meta_path = path.with_suffix(path.suffix + '.meta')
                if meta_path.exists():
                    meta_path.unlink()
                
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete object {bucket}/{key}: {e}")
            return False
    
    def exists(self, bucket: str, key: str) -> bool:
        """Check if an object exists."""
        try:
            return self._get_path(bucket, key).exists()
        except ValueError:
            return False
    
    def list(self, bucket: str, prefix: str = "") -> List[ObjectInfo]:
        """List objects in a bucket."""
        try:
            safe_bucket = self._sanitize_bucket(bucket)
            bucket_path = (self.base_path / safe_bucket).resolve()
            if not bucket_path.exists():
                return []

            results = []
            safe_prefix = self._sanitize_key(prefix).rstrip('/') if prefix else ""
            
            for file_path in bucket_path.rglob("*"):
                if file_path.is_file() and not file_path.suffix == '.meta':
                    # Calculate relative key
                    relative = file_path.relative_to(bucket_path)
                    key = str(relative).replace("\\", "/")
                    
                    if not safe_prefix or key.startswith(safe_prefix):
                        info = self.get_info(bucket, key)
                        if info:
                            results.append(info)
            
            return sorted(results, key=lambda x: x.key)
        except Exception as e:
            logger.error(f"Failed to list objects in {bucket}: {e}")
            return []
    
    def get_info(self, bucket: str, key: str) -> Optional[ObjectInfo]:
        """Get object metadata."""
        try:
            path = self._get_path(bucket, key)
            if not path.exists():
                return None
            
            stat = path.stat()
            content = path.read_bytes()
            
            # Try to load metadata
            meta_path = path.with_suffix(path.suffix + '.meta')
            metadata = {}
            content_type = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
            
            if meta_path.exists():
                import json
                try:
                    metadata = json.loads(meta_path.read_text())
                    if '_content_type' in metadata:
                        content_type = metadata.pop('_content_type')
                except (OSError, TypeError, ValueError):
                    pass
            
            return ObjectInfo(
                key=key,
                size=stat.st_size,
                content_type=content_type,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                etag=self._compute_etag(content),
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Failed to get object info {bucket}/{key}: {e}")
            return None
    
    def get_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """Get a file:// URL for local objects."""
        path = self._get_path(bucket, key)
        return f"file://{path.as_posix()}"
    
    def create_bucket(self, bucket: str) -> bool:
        """Create a bucket directory."""
        try:
            safe_bucket = self._sanitize_bucket(bucket)
            (self.base_path / safe_bucket).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create bucket {bucket}: {e}")
            return False


class S3Backend(ObjectBackend):
    """S3-compatible backend for cloud object storage."""
    
    def __init__(
        self,
        endpoint_url: Optional[str],
        access_key: str,
        secret_key: str,
        region: str = "us-east-1"
    ):
        self.endpoint_url = endpoint_url
        self.region = region
        self._client = None
        self._access_key = access_key
        self._secret_key = secret_key
    
    @property
    def client(self):
        """Lazy initialization of S3 client."""
        if self._client is None:
            try:
                import boto3
                from botocore.config import Config
                
                self._client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self._access_key,
                    aws_secret_access_key=self._secret_key,
                    region_name=self.region,
                    config=Config(
                        signature_version="s3v4",
                        s3={"addressing_style": "path"},
                        connect_timeout=3,
                        read_timeout=15,
                        retries={"max_attempts": 3, "mode": "standard"},
                    ),
                )
                logger.info(f"S3 client initialized for {self.endpoint_url or 'AWS S3'}")
            except ImportError:
                logger.warning("boto3 not installed. Install with: pip install boto3")
                raise
        return self._client
    
    def put(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO],
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Upload object to S3."""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = metadata
            
            if isinstance(data, bytes):
                self.client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=data,
                    **extra_args
                )
            else:
                self.client.upload_fileobj(
                    data,
                    bucket,
                    key,
                    ExtraArgs=extra_args if extra_args else None
                )
            
            return key
        except Exception as e:
            logger.error(f"S3 put failed for {bucket}/{key}: {e}")
            raise
    
    def get(self, bucket: str, key: str) -> bytes:
        """Download object from S3."""
        try:
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"S3 get failed for {bucket}/{key}: {e}")
            raise
    
    def delete(self, bucket: str, key: str) -> bool:
        """Delete object from S3."""
        try:
            self.client.delete_object(Bucket=bucket, Key=key)
            return True
        except Exception as e:
            logger.error(f"S3 delete failed for {bucket}/{key}: {e}")
            return False
    
    def exists(self, bucket: str, key: str) -> bool:
        """Check if object exists in S3."""
        try:
            self.client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False
    
    def list(self, bucket: str, prefix: str = "") -> List[ObjectInfo]:
        """List objects in S3 bucket."""
        try:
            results = []
            paginator = self.client.get_paginator('list_objects_v2')
            
            pages = paginator.paginate(
                Bucket=bucket,
                Prefix=prefix
            )
            
            for page in pages:
                for obj in page.get('Contents', []):
                    results.append(ObjectInfo(
                        key=obj['Key'],
                        size=obj['Size'],
                        content_type='application/octet-stream',  # HEAD call needed for actual type
                        last_modified=obj['LastModified'],
                        etag=obj.get('ETag', '').strip('"')
                    ))
            
            return results
        except Exception as e:
            logger.error(f"S3 list failed for {bucket}: {e}")
            raise
    
    def get_info(self, bucket: str, key: str) -> Optional[ObjectInfo]:
        """Get object metadata from S3."""
        try:
            response = self.client.head_object(Bucket=bucket, Key=key)
            return ObjectInfo(
                key=key,
                size=response['ContentLength'],
                content_type=response.get('ContentType', 'application/octet-stream'),
                last_modified=response['LastModified'],
                etag=response.get('ETag', '').strip('"'),
                metadata=response.get('Metadata', {})
            )
        except Exception as e:
            logger.error(f"S3 head failed for {bucket}/{key}: {e}")
            return None
    
    def get_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for S3 object."""
        try:
            return self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expires_in
            )
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def create_bucket(self, bucket: str) -> bool:
        """Create S3 bucket."""
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except Exception:
            pass
        try:
            if self.region == 'us-east-1':
                self.client.create_bucket(Bucket=bucket)
            else:
                self.client.create_bucket(
                    Bucket=bucket,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            return True
        except Exception as e:
            logger.error(f"Failed to create bucket {bucket}: {e}")
            return False


class ObjectStore:
    """
    Unified object store interface.

    The production backend is the supervisor-owned internal S3 endpoint.  The
    local filesystem remains available only for development, bounded staging,
    migration, and recovery tooling.
    """
    
    def __init__(self, backend: Optional[ObjectBackend] = None):
        if backend:
            self._backend = backend
        else:
            self._backend = self._create_backend()
    
    def _create_backend(self) -> ObjectBackend:
        """Create appropriate backend based on configuration."""
        from backend.storage.connection_manager import get_connection_manager
        
        config = get_connection_manager().config.object_storage
        
        if config.endpoint_url and config.access_key and config.secret_key:
            logger.info("Using supervisor-owned internal S3-compatible backend")
            return S3Backend(
                config.endpoint_url,
                config.access_key,
                config.secret_key,
                config.region,
            )

        production_required = False
        try:
            from flask import current_app, has_app_context

            if has_app_context():
                production_required = bool(
                    current_app.config.get("DLE_PRODUCTION_MODE")
                    or current_app.config.get("DLE_DATA_PLANE_DRIVER") == "podman"
                )
        except ImportError:
            pass
        if production_required:
            raise RuntimeError("required_internal_object_store_unavailable")

        logger.info("Using bounded development filesystem object backend")
        return LocalFileBackend(base_path=config.local_path)
    
    def put(
        self,
        bucket: str,
        key: str,
        data: Union[bytes, BinaryIO],
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Store an object."""
        return self._backend.put(bucket, key, data, content_type, metadata)
    
    def get(self, bucket: str, key: str) -> bytes:
        """Retrieve an object."""
        return self._backend.get(bucket, key)
    
    def delete(self, bucket: str, key: str) -> bool:
        """Delete an object."""
        return self._backend.delete(bucket, key)
    
    def exists(self, bucket: str, key: str) -> bool:
        """Check if object exists."""
        return self._backend.exists(bucket, key)
    
    def list(self, bucket: str, prefix: str = "") -> List[ObjectInfo]:
        """List objects."""
        return self._backend.list(bucket, prefix)
    
    def get_info(self, bucket: str, key: str) -> Optional[ObjectInfo]:
        """Get object metadata."""
        return self._backend.get_info(bucket, key)
    
    def get_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """Get URL for object."""
        return self._backend.get_url(bucket, key, expires_in)
    
    def create_bucket(self, bucket: str) -> bool:
        """Create a bucket."""
        return self._backend.create_bucket(bucket)


# Singleton instance
_object_store: Optional[ObjectStore] = None


def get_object_store() -> ObjectStore:
    """Return an object store owned by the active application instance."""
    try:
        from flask import current_app, has_app_context

        if has_app_context():
            store = current_app.extensions.get("dle_object_store")
            if store is None:
                store = ObjectStore()
                current_app.extensions["dle_object_store"] = store
            return store
    except ImportError:
        pass

    global _object_store
    if _object_store is None:
        _object_store = ObjectStore()
    return _object_store
