# AI Resume Matching & Interview Preparation Platform

Local-first MVP cho ná»n táº£ng phÃ¢n tÃ­ch má»©c Ä‘á»™ phÃ¹ há»£p giá»¯a CV vÃ  Job Description, tÃ­nh matching score, matched/missing skills, gá»£i Ã½ cáº£i thiá»‡n CV vÃ  táº¡o cÃ¢u há»i phá»ng váº¥n.

## 1. Tech stack

- Backend: FastAPI Python
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migration: Alembic
- Auth: JWT tá»± build + refresh token lÆ°u hash trong DB
- Password hashing: passlib/bcrypt
- Queue: Amazon SQS
- Worker: Python SQS long-polling worker
- Storage: Local storage, cÃ³ interface Ä‘á»ƒ thay MinIO/S3 sau
- AI: MockAIService trÆ°á»›c, cÃ³ placeholder OllamaAIService
- Frontend: React + Vite + TypeScript
- Reverse proxy: Nginx
- Local deploy: Docker Compose

## 2. Cháº¡y local báº±ng VSCode

Má»Ÿ folder nÃ y báº±ng VSCode, sau Ä‘Ã³ cháº¡y trong Terminal:

```bash
cp .env.example .env
docker compose up --build
```

Má»Ÿ trÃ¬nh duyá»‡t:

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
7. Check Status Ä‘áº¿n khi `completed`
8. Get Result

## 4. Táº¡o admin user local

Sau khi container Ä‘ang cháº¡y:

```bash
docker compose exec backend-api python -m app.scripts.create_admin
```

Email/password láº¥y tá»« `.env`:

```env
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=AdminPassword123
```

## 5. Lá»‡nh thÆ°á»ng dÃ¹ng

```bash
# Cháº¡y toÃ n bá»™
docker compose up --build

# Xem log backend
docker compose logs -f backend-api

# Xem log worker
docker compose logs -f worker

# Reset toÃ n bá»™ DB local
docker compose down -v

# Cháº¡y migration thá»§ cÃ´ng
docker compose exec backend-api alembic upgrade head
```

## 6. API chÃ­nh

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

## 7. Cáº¥u trÃºc project

```text
ai-resume-platform/
+-- backend/                 # FastAPI API, database models, services, migrations, tests
¦   +-- app/
¦   ¦   +-- api/
¦   ¦   +-- ai/
¦   ¦   +-- auth/
¦   ¦   +-- core/
¦   ¦   +-- database/
¦   ¦   +-- matching/
¦   ¦   +-- models/
¦   ¦   +-- queue/
¦   ¦   +-- repositories/
¦   ¦   +-- schemas/
¦   ¦   +-- scripts/
¦   ¦   +-- services/
¦   ¦   +-- storage/
¦   ¦   +-- utils/
¦   +-- alembic/
¦   +-- tests/
¦   +-- Dockerfile
¦   +-- requirements.txt
+-- worker/                  # SQS worker source and worker Dockerfile
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
## 8. NguyÃªn táº¯c báº£o máº­t

- KhÃ´ng commit `.env`
- KhÃ´ng commit file upload tháº­t
- KhÃ´ng log password/JWT/refresh token
- KhÃ´ng log ná»™i dung CV/JD
- KhÃ´ng cho user xem job/file/result cá»§a user khÃ¡c

## 9. AWS migration sau khi local final

KhÃ´ng triá»ƒn khai AWS á»Ÿ giai Ä‘oáº¡n Ä‘áº§u. Khi local Ä‘Ã£ á»•n:

- PostgreSQL Docker â†’ Amazon RDS PostgreSQL
- Local Storage/MinIO â†’ Amazon S3
- Amazon SQS cho hang doi job va DLQ
- MockAI/Ollama â†’ Bedrock/OpenAI
- Nginx local â†’ ALB + CloudFront
- `.env` â†’ Secrets Manager/Parameter Store
- Docker Compose â†’ EC2 hoáº·c ECS
- Docker logs â†’ CloudWatch

Chi tiáº¿t xem `docs/AWS_MIGRATION_PLAN.md`.
