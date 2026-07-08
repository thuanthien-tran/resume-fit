import boto3

from app.core.config import settings
from app.storage.base import StorageService


class S3StorageService(StorageService):
    """Object storage trên Amazon S3 (hoặc MinIO/S3-compatible qua s3_endpoint_url).

    endpoint_url rỗng -> AWS S3 thật; có giá trị -> MinIO/local S3.
    """

    def __init__(self):
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url or None,
        )

    def save(self, path: str, content: bytes) -> str:
        self.client.put_object(Bucket=self.bucket, Key=path, Body=content)
        return path

    def read(self, path: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=path)
        return response["Body"].read()

    def delete(self, path: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=path)

    def exists(self, path: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=path)
            return True
        except self.client.exceptions.ClientError:
            return False

    def generate_presigned_upload_url(self, path: str, content_type: str, expires: int) -> str:
        return self.client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": path, "ContentType": content_type},
            ExpiresIn=expires,
        )

    def generate_presigned_download_url(self, path: str, expires: int) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": path},
            ExpiresIn=expires,
        )
