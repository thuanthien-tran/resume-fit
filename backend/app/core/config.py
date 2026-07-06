from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "AI Resume Platform"
    api_prefix: str = "/api"

    database_url: str
    redis_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    auth_provider: str = "local_jwt"  # local_jwt | cognito

    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 10

    # Storage & queue provider selection (local-first, S3/SQS ready)
    storage_provider: str = "local"  # local | s3
    queue_provider: str = "celery"  # celery | sqs
    backend_public_url: str = "http://localhost:8080"

    # S3 (also used for MinIO/S3-compatible via s3_endpoint_url)
    aws_region: str = "ap-southeast-1"
    s3_bucket: str = ""
    s3_endpoint_url: str = ""  # empty = real AWS; set = MinIO/local S3
    presign_expiry_seconds: int = 900

    # SQS
    sqs_queue_url: str = ""
    sqs_dlq_url: str = ""

    ai_provider: str = "mock"
    ai_model: str = "mock-v1"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.1"
    xai_api_key: str = ""
    xai_base_url: str = "https://api.x.ai/v1"
    xai_model: str = "grok-3-mini"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: int = 30

    admin_email: str = "admin@example.com"
    admin_password: str = "AdminPassword123"
    admin_full_name: str = "Local Admin"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
