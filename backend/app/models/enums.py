from sqlalchemy.dialects import postgresql

UserRoleType = postgresql.ENUM("user", "admin", name="user_role", create_type=False)
UserStatusType = postgresql.ENUM("active", "inactive", "blocked", name="user_status", create_type=False)
FileTypeType = postgresql.ENUM("cv", "jd", name="file_type", create_type=False)
StorageTypeType = postgresql.ENUM("local", "minio", "s3", name="storage_type", create_type=False)
UploadStatusType = postgresql.ENUM("uploaded", "failed", "deleted", name="upload_status", create_type=False)
JobStatusType = postgresql.ENUM("uploaded", "queued", "processing", "completed", "partial_completed", "failed", "cancelled", name="job_status", create_type=False)
