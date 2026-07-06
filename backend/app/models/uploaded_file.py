import uuid

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.session import Base
from app.models.enums import FileTypeType, StorageTypeType, UploadStatusType


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="SET NULL"), nullable=True, index=True)

    file_type = Column(FileTypeType, nullable=False)
    original_filename = Column(String(512), nullable=False)
    display_name = Column(String(255), nullable=True)

    storage_type = Column(StorageTypeType, nullable=False, default="local")
    storage_path = Column(String, nullable=False)
    bucket_name = Column(String(255), nullable=True)
    object_key = Column(String, nullable=True)

    mime_type = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    checksum = Column(String(128), nullable=False)
    upload_status = Column(UploadStatusType, nullable=False, default="uploaded", index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
