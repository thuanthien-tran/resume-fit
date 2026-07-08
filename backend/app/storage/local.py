from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from jose import jwt

from app.core.config import settings
from app.storage.base import StorageService


class LocalStorageService(StorageService):
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.upload_dir)

    def _full_path(self, path: str) -> Path:
        normalized = Path(path)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ValueError("Invalid storage path")
        return self.base_dir / normalized

    def save(self, path: str, content: bytes) -> str:
        full_path = self._full_path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)
        return path

    def read(self, path: str) -> bytes:
        return self._full_path(path).read_bytes()

    def delete(self, path: str) -> None:
        full_path = self._full_path(path)
        if full_path.exists():
            full_path.unlink()

    def exists(self, path: str) -> bool:
        return self._full_path(path).exists()

    def _sign_token(self, path: str, action: str, expires: int) -> str:
        payload = {
            "storage_path": path,
            "action": action,
            "type": "storage_presign",
            "exp": datetime.now(timezone.utc) + timedelta(seconds=expires),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def generate_presigned_upload_url(self, path: str, content_type: str, expires: int) -> str:
        # Local presigned URL giả: client PUT về backend, backend xác thực token rồi save.
        token = self._sign_token(path, "put", expires)
        query = urlencode({"token": token})
        return f"{settings.backend_public_url}{settings.api_prefix}/uploads/local-put?{query}"

    def generate_presigned_download_url(self, path: str, expires: int) -> str:
        token = self._sign_token(path, "get", expires)
        query = urlencode({"token": token})
        return f"{settings.backend_public_url}{settings.api_prefix}/uploads/local-get?{query}"
