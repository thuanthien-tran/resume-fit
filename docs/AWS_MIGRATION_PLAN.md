# AWS Migration Plan

Chỉ thực hiện sau khi local MVP chạy ổn, test đầy đủ, code sạch và đã push GitHub.

## Mapping local sang AWS

| Local | AWS |
|---|---|
| PostgreSQL Docker | Amazon RDS PostgreSQL |
| Local storage / MinIO | Amazon S3 |
| Celery + Redis | Amazon SQS hoặc Redis trên ECS/EC2 |
| Backend container | EC2 hoặc ECS service |
| Worker container | EC2 hoặc ECS worker service |
| React local | S3 static hosting + CloudFront |
| Nginx local | ALB + CloudFront |
| `.env` | Secrets Manager / Parameter Store |
| Python/Docker logs | CloudWatch Logs |
| MockAI/Ollama | Bedrock/OpenAI |

## Thứ tự triển khai

1. Build Docker image backend + worker.
2. Tạo RDS PostgreSQL.
3. Chạy Alembic migration lên RDS.
4. Tạo S3 bucket.
5. Implement `S3StorageService` theo interface hiện có.
6. Tạo SQS queue + DLQ.
7. Implement `SQSQueueService` theo interface hiện có.
8. Deploy backend lên EC2/ECS.
9. Deploy worker lên EC2/ECS.
10. Deploy frontend lên S3 + CloudFront.
11. Gắn ALB, HTTPS bằng ACM.
12. Chuyển secrets sang Secrets Manager/Parameter Store.
13. Bật CloudWatch Logs, alarm, backup.

## Những phần code cần thay

- `LocalStorageService` → `S3StorageService`
- `CeleryQueueService` → `SQSQueueService`
- `MockAIService` → `BedrockAIService` hoặc `OpenAIService`
- `DATABASE_URL` đổi sang RDS endpoint
- Secret loading từ `.env` sang Secrets Manager/Parameter Store

## Những phần không cần thay

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
- ALB public, không expose trực tiếp backend
- S3 block public access
- IAM least privilege
- HTTPS bằng ACM
- WAF nếu public production
- SQS DLQ
- RDS backup
- Không log CV/JD/token/secret
- CloudWatch alarm cho 5xx, queue depth, failed jobs
