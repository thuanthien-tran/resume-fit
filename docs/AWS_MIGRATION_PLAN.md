# AWS Migration Plan

Chá»‰ thá»±c hiá»‡n sau khi local MVP cháº¡y á»•n, test Ä‘áº§y Ä‘á»§, code sáº¡ch vÃ  Ä‘Ã£ push GitHub.

## Mapping local sang AWS

| Local | AWS |
|---|---|
| PostgreSQL Docker | Amazon RDS PostgreSQL |
| Local storage / MinIO | Amazon S3 |
| Amazon SQS | Amazon SQS + DLQ |
| Backend container | EC2 hoáº·c ECS service |
| Worker container | EC2 hoáº·c ECS worker service |
| React local | S3 static hosting + CloudFront |
| Nginx local | ALB + CloudFront |
| `.env` | Secrets Manager / Parameter Store |
| Python/Docker logs | CloudWatch Logs |
| MockAI/Ollama | Bedrock/OpenAI |

## Thá»© tá»± triá»ƒn khai

1. Build Docker image backend + worker.
2. Táº¡o RDS PostgreSQL.
3. Cháº¡y Alembic migration lÃªn RDS.
4. Táº¡o S3 bucket.
5. Implement `S3StorageService` theo interface hiá»‡n cÃ³.
6. Táº¡o SQS queue + DLQ.
7. Cau hinh `SQS_QUEUE_URL`, `SQS_DLQ_URL`, IAM role cho backend/worker.
8. Deploy backend lÃªn EC2/ECS.
9. Deploy worker lÃªn EC2/ECS.
10. Deploy frontend lÃªn S3 + CloudFront.
11. Gáº¯n ALB, HTTPS báº±ng ACM.
12. Chuyá»ƒn secrets sang Secrets Manager/Parameter Store.
13. Báº­t CloudWatch Logs, alarm, backup.

## Nhá»¯ng pháº§n code cáº§n thay

- `LocalStorageService` â†’ `S3StorageService`

- `MockAIService` â†’ `BedrockAIService` hoáº·c `OpenAIService`
- `DATABASE_URL` Ä‘á»•i sang RDS endpoint
- Secret loading tá»« `.env` sang Secrets Manager/Parameter Store

## Nhá»¯ng pháº§n khÃ´ng cáº§n thay

- REST API contract
- SQLAlchemy models
- Alembic migrations
- Matching engine
- Auth dependency
- Frontend polling flow
- Business service layer

## Security checklist production

- RDS private subnet
- Backend/Worker private subnet
- ALB public, khÃ´ng expose trá»±c tiáº¿p backend
- S3 block public access
- IAM least privilege
- HTTPS báº±ng ACM
- WAF náº¿u public production
- SQS DLQ
- RDS backup
- KhÃ´ng log CV/JD/token/secret
- CloudWatch alarm cho 5xx, queue depth, failed jobs
