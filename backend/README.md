# Backend API

FastAPI service cho nền tảng phân tích CV ↔ JD: auth (JWT + refresh token),
upload/trích xuất văn bản, tạo job phân tích đa ứng viên, matching engine và
sinh phản hồi AI.

## Cấu trúc

```text
backend/
├── app/
│   ├── api/            # Route handlers (auth, uploads, jobs, admin, health)
│   ├── ai/             # AI service (mock, ollama, xai) + factory
│   ├── auth/           # Tiện ích xác thực
│   ├── core/           # Config, logging, security
│   ├── database/       # Session, Base
│   ├── matching/       # Matching engine (rule-based scoring)
│   ├── models/         # SQLAlchemy models
│   ├── queue/          # Celery queue interface
│   ├── repositories/   # Truy vấn dữ liệu
│   ├── schemas/        # Pydantic schemas
│   ├── scripts/        # Script tiện ích (create_admin)
│   ├── services/       # Trích xuất văn bản, upload, job event
│   ├── storage/        # Local storage + interface cho MinIO/S3
│   └── utils/
├── alembic/            # Migrations
├── tests/
├── Dockerfile
└── requirements.txt
```

## Chạy migration

```bash
alembic upgrade head
```

## Chạy dev local

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Swagger docs: http://localhost:8000/docs
