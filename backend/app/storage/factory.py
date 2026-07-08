from app.core.config import settings
from app.storage.base import StorageService
from app.storage.local import LocalStorageService


def get_storage_service() -> StorageService:
    if settings.storage_provider == "s3":
        # Lazy import: chỉ nạp boto3 khi thực sự dùng S3.
        from app.storage.s3 import S3StorageService

        return S3StorageService()
    return LocalStorageService()
