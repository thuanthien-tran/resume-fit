# Backend API

FastAPI service cho ná»n táº£ng phÃ¢n tÃ­ch CV â†” JD: auth (JWT + refresh token),
upload/trÃ­ch xuáº¥t vÄƒn báº£n, táº¡o job phÃ¢n tÃ­ch Ä‘a á»©ng viÃªn, matching engine vÃ 
sinh pháº£n há»“i AI.

## Cáº¥u trÃºc

```text
backend/
â”œâ”€â”€ app/
â”‚   â”œâ”€â”€ api/            # Route handlers (auth, uploads, jobs, admin, health)
â”‚   â”œâ”€â”€ ai/             # AI service (mock, ollama, xai) + factory
â”‚   â”œâ”€â”€ auth/           # Tiá»‡n Ã­ch xÃ¡c thá»±c
â”‚   â”œâ”€â”€ core/           # Config, logging, security
â”‚   â”œâ”€â”€ database/       # Session, Base
â”‚   â”œâ”€â”€ matching/       # Matching engine (rule-based scoring)
â”‚   â”œâ”€â”€ models/         # SQLAlchemy models
â”‚   â”œâ”€â”€ repositories/   # Truy váº¥n dá»¯ liá»‡u
â”‚   â”œâ”€â”€ schemas/        # Pydantic schemas
â”‚   â”œâ”€â”€ scripts/        # Script tiá»‡n Ã­ch (create_admin)
â”‚   â”œâ”€â”€ services/       # TrÃ­ch xuáº¥t vÄƒn báº£n, upload, job event, SQS
â”‚   â”œâ”€â”€ storage/        # Local storage + interface cho MinIO/S3
â”‚   â””â”€â”€ utils/
â”œâ”€â”€ alembic/            # Migrations
â”œâ”€â”€ tests/
â”œâ”€â”€ Dockerfile
â””â”€â”€ requirements.txt
```

## Cháº¡y migration

```bash
alembic upgrade head
```

## Cháº¡y dev local

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Swagger docs: http://localhost:8000/docs
