# AI Resume Matching & Interview Preparation Platform

Local-first MVP cho nền tảng phân tích mức độ phù hợp giữa CV và Job Description, tính matching score, matched/missing skills, gợi ý cải thiện CV và tạo câu hỏi phỏng vấn.

## 1. Tech stack

- Backend: FastAPI Python
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migration: Alembic
- Auth: JWT tự build + refresh token lưu hash trong DB
- Password hashing: passlib/bcrypt
- Queue: Celery + Redis
- Worker: Python Celery worker
- Storage: Local storage, có interface để thay MinIO/S3 sau
- AI: MockAIService trước, có placeholder OllamaAIService
- Frontend: React + Vite + TypeScript
- Reverse proxy: Nginx
- Local deploy: Docker Compose

## 2. Chạy local bằng VSCode

Mở folder này bằng VSCode, sau đó chạy trong Terminal:

```bash
cp .env.example .env
docker compose up --build
```

Mở trình duyệt:

- Frontend: http://localhost:8080
- Swagger API Docs: http://localhost:8080/docs
- Health: http://localhost:8080/api/health
- Ready: http://localhost:8080/api/ready

## 3. Flow test nhanh

1. Register
2. Login
3. Create Job
4. Upload CV PDF/DOCX
5. Upload JD PDF/DOCX
6. Enqueue Job
7. Check Status đến khi `completed`
8. Get Result

## 4. Tạo admin user local

Sau khi container đang chạy:

```bash
docker compose exec backend-api python -m app.scripts.create_admin
```

Email/password lấy từ `.env`:

```env
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=AdminPassword123
```

## 5. Lệnh thường dùng

```bash
# Chạy toàn bộ
docker compose up --build

# Xem log backend
docker compose logs -f backend-api

# Xem log worker
docker compose logs -f worker

# Reset toàn bộ DB local
docker compose down -v

# Chạy migration thủ công
docker compose exec backend-api alembic upgrade head
```

## 6. API chính

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh-token`
- `POST /api/auth/logout`
- `GET /api/me`

Upload:

- `POST /api/uploads`
- `GET /api/uploads/{file_id}`
- `DELETE /api/uploads/{file_id}`

Jobs:

- `POST /api/jobs`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/enqueue`
- `GET /api/jobs/{job_id}/result`
- `DELETE /api/jobs/{job_id}`

Admin:

- `GET /api/admin/jobs`
- `GET /api/admin/jobs/{job_id}/events`
- `GET /api/admin/users`

## 7. Cấu trúc project

```text
ai-resume-platform/
+-- backend/                 # FastAPI API, database models, services, migrations, tests
�   +-- app/
�   �   +-- api/
�   �   +-- ai/
�   �   +-- auth/
�   �   +-- core/
�   �   +-- database/
�   �   +-- matching/
�   �   +-- models/
�   �   +-- queue/
�   �   +-- repositories/
�   �   +-- schemas/
�   �   +-- scripts/
�   �   +-- services/
�   �   +-- storage/
�   �   +-- utils/
�   +-- alembic/
�   +-- tests/
�   +-- Dockerfile
�   +-- requirements.txt
+-- worker/                  # Celery worker source and worker Dockerfile
+-- frontend/                # React + Vite + TypeScript frontend
+-- docs/                    # Architecture, workflow, API, AWS migration docs
+-- nginx/                   # Reverse proxy config
+-- postman/                 # API collection
+-- uploads/                 # Local uploaded files, ignored except .gitkeep
+-- README.md
+-- .gitignore
+-- .env.example
+-- docker-compose.yml
```
## 8. Nguyên tắc bảo mật

- Không commit `.env`
- Không commit file upload thật
- Không log password/JWT/refresh token
- Không log nội dung CV/JD
- Không cho user xem job/file/result của user khác

## 9. AWS migration sau khi local final

Không triển khai AWS ở giai đoạn đầu. Khi local đã ổn:

- PostgreSQL Docker → Amazon RDS PostgreSQL
- Local Storage/MinIO → Amazon S3
- Celery/Redis → Amazon SQS hoặc Redis managed
- MockAI/Ollama → Bedrock/OpenAI
- Nginx local → ALB + CloudFront
- `.env` → Secrets Manager/Parameter Store
- Docker Compose → EC2 hoặc ECS
- Docker logs → CloudWatch

Chi tiết xem `docs/AWS_MIGRATION_PLAN.md`.
