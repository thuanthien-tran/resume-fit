from app.storage.s3 import S3StorageService


class MinIOStorageService(S3StorageService):
    """MinIO/S3-compatible storage.

    Dùng chung implementation với S3StorageService; chỉ cần đặt s3_endpoint_url
    trỏ về MinIO. Giữ lại tên class này cho tương thích ngược.
    """

    pass
