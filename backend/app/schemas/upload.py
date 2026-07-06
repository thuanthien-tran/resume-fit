from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PresignRequest(BaseModel):
    job_id: UUID
    file_type: str
    filename: str
    content_type: str = "application/octet-stream"


class PresignResponse(BaseModel):
    storage_path: str
    upload_url: str
    file_type: str
    original_filename: str


class CompleteUploadRequest(BaseModel):
    job_id: UUID
    file_type: str
    storage_path: str
    original_filename: str
    mime_type: str = "application/octet-stream"


class UploadResponse(BaseModel):
    file_id: str
    job_id: str
    candidate_id: str | None = None
    file_type: str
    original_filename: str
    display_name: str | None = None
    upload_status: str
    file_size: int
    checksum: str


class SavedFileItem(BaseModel):
    id: str
    original_filename: str
    display_name: str | None = None
    file_type: str
    file_size: int
    created_at: datetime | None
    job_id: str | None = None
    job_title: str | None = None


class UploadedFileResponse(BaseModel):
    id: str
    user_id: str
    job_id: str | None
    file_type: str
    original_filename: str
    display_name: str | None = None
    storage_type: str
    storage_path: str
    mime_type: str
    file_size: int
    checksum: str
    upload_status: str
    created_at: datetime | None
    uploaded_at: datetime | None
    deleted_at: datetime | None
