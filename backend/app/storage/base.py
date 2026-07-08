from abc import ABC, abstractmethod


class StorageService(ABC):
    @abstractmethod
    def save(self, path: str, content: bytes) -> str:
        pass

    @abstractmethod
    def read(self, path: str) -> bytes:
        pass

    @abstractmethod
    def delete(self, path: str) -> None:
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        pass

    @abstractmethod
    def generate_presigned_upload_url(self, path: str, content_type: str, expires: int) -> str:
        """Trả về URL để client PUT file trực tiếp lên storage.

        Trên AWS: URL S3 thật. Trên local: URL giả trỏ về backend (mô phỏng).
        """
        pass

    @abstractmethod
    def generate_presigned_download_url(self, path: str, expires: int) -> str:
        """Trả về URL có thời hạn để tải file về."""
        pass
