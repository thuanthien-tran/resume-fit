# 14. Deployment Guide

## 14.1 Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Docker | 24+ | Container runtime |
| AWS CLI | 2.x | AWS resource management |
| Python | 3.11+ | Local development |
| PostgreSQL | 15+ | Database (already deployed by Backend) |

## 14.2 AWS Infrastructure Requirements

### EC2 Instance (Worker Service)
- **Type:** t3.medium (minimum) / t3.large (recommended)
- **Subnet:** Private Subnet (no public IP)
- **Security Group:** Outbound to NAT Gateway, inbound from VPC only
- **IAM Role:** Attached (see 14.3)
- **Storage:** 30GB EBS (for Docker images + model cache)

### NAT Gateway
- Worker ở Private Subnet cần NAT Gateway để:
  - Pull Docker images từ ECR
  - Call OpenAI API
  - (S3/SQS qua VPC Endpoints thì không cần NAT)

### VPC Endpoints (Recommended)
```
com.amazonaws.{region}.sqs        → Gateway/Interface endpoint
com.amazonaws.{region}.s3         → Gateway endpoint
```
Giảm latency và cost cho S3/SQS traffic.

## 14.3 IAM Role Configuration

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SQSAccess",
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:SendMessage",
        "sqs:ChangeMessageVisibility",
        "sqs:GetQueueAttributes"
      ],
      "Resource": [
        "arn:aws:sqs:{region}:{account}:resume-processing-queue",
        "arn:aws:sqs:{region}:{account}:resume-processing-dlq"
      ]
    },
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::resume-matching-bucket/*"
    },
    {
      "Sid": "ECRPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SecretsManager",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:{region}:{account}:secret:worker-service/*"
    }
  ]
}
```

## 14.4 SQS Queue Configuration

### Main Queue
```
Queue Name:           resume-processing-queue
Visibility Timeout:   300 seconds (5 minutes)
Message Retention:    4 days
Receive Wait Time:    20 seconds (long polling)
Redrive Policy:       maxReceiveCount = 3 → DLQ
```

### Dead Letter Queue
```
Queue Name:           resume-processing-dlq
Message Retention:    14 days
```

## 14.5 Deployment Steps

### Step 1: Build & Push Docker Image

```bash
# Login to ECR
aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin {account}.dkr.ecr.ap-southeast-1.amazonaws.com

# Build image
docker build -t worker-service .

# Tag and push
docker tag worker-service:latest {account}.dkr.ecr.ap-southeast-1.amazonaws.com/worker-service:latest
docker push {account}.dkr.ecr.ap-southeast-1.amazonaws.com/worker-service:latest
```

### Step 2: Store Secrets

```bash
aws secretsmanager create-secret \
  --name worker-service/config \
  --secret-string '{
    "OPENAI_API_KEY": "sk-...",
    "DB_PASSWORD": "...",
    "DB_HOST": "your-rds-endpoint.ap-southeast-1.rds.amazonaws.com"
  }'
```

### Step 3: Run Database Migrations

```bash
# From bastion host or CI/CD pipeline with DB access
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migrations/001_create_processing_jobs.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migrations/002_create_matching_results.sql
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f migrations/003_create_resumes_and_jds.sql
```

### Step 4: Deploy on EC2

```bash
# SSH to EC2 instance in private subnet (via bastion)
ssh -J bastion@bastion-ip ec2-user@worker-ip

# Pull latest image
aws ecr get-login-password --region ap-southeast-1 | \
  docker login --username AWS --password-stdin {account}.dkr.ecr.ap-southeast-1.amazonaws.com

docker pull {account}.dkr.ecr.ap-southeast-1.amazonaws.com/worker-service:latest

# Run with environment from Secrets Manager
docker run -d \
  --name worker-service \
  --restart unless-stopped \
  -e AWS_REGION=ap-southeast-1 \
  -e SQS_QUEUE_URL=https://sqs.ap-southeast-1.amazonaws.com/{account}/resume-processing-queue \
  -e SQS_DLQ_URL=https://sqs.ap-southeast-1.amazonaws.com/{account}/resume-processing-dlq \
  -e S3_BUCKET_NAME=resume-matching-bucket \
  -e DB_HOST=your-rds-endpoint.ap-southeast-1.rds.amazonaws.com \
  -e DB_PORT=5432 \
  -e DB_NAME=resume_matching \
  -e DB_USER=worker_user \
  -e DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id worker-service/config --query SecretString --output text | jq -r '.DB_PASSWORD') \
  -e OPENAI_API_KEY=$(aws secretsmanager get-secret-value --secret-id worker-service/config --query SecretString --output text | jq -r '.OPENAI_API_KEY') \
  -e WORKER_COUNT=3 \
  -e LOG_LEVEL=INFO \
  -e LOG_FORMAT=json \
  -e ENVIRONMENT=production \
  -e INCLUDE_AI_ANALYSIS=true \
  {account}.dkr.ecr.ap-southeast-1.amazonaws.com/worker-service:latest
```

## 14.6 Scaling

### Horizontal Scaling
- Deploy multiple EC2 instances in same private subnet
- Each instance runs independent worker containers
- SQS handles message distribution automatically
- No coordination needed between instances

### Vertical Scaling
- Increase `WORKER_COUNT` (threads per instance)
- Recommended: 2-4 workers per vCPU
- Monitor memory: Sentence Transformer model uses ~500MB

### Auto Scaling (Optional)
- Use CloudWatch alarm on SQS `ApproximateNumberOfMessagesVisible`
- Scale out when queue depth > 100 for 5 minutes
- Scale in when queue depth = 0 for 15 minutes

## 14.7 Monitoring & Alerting

### CloudWatch Logs
```
Log Group: /ecs/worker-service (or /ec2/worker-service)
Filter Patterns:
  - ERROR: { $.level = "error" }
  - Slow jobs: { $.duration_ms > 30000 }
  - DLQ: { $.event = "job_moved_to_dlq" }
```

### CloudWatch Alarms
| Metric | Threshold | Action |
|--------|-----------|--------|
| SQS Messages Visible | > 500, 5 min | Alert + Scale Out |
| SQS DLQ Messages | > 0 | Alert team |
| Worker Health Check | Fail 3x | Restart container |
| Processing Time | p95 > 60s | Alert team |

## 14.8 Rollback Strategy

```bash
# Quick rollback: pull previous image tag
docker stop worker-service
docker rm worker-service
docker pull {account}.dkr.ecr.ap-southeast-1.amazonaws.com/worker-service:v1.0.0-prev
docker run -d --name worker-service ... worker-service:v1.0.0-prev

# SQS messages not lost during rollback (visibility timeout)
# In-flight jobs will timeout and become visible again
```

## 14.9 Pre-deployment Checklist

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Docker image builds successfully
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] IAM role attached to EC2
- [ ] Security group allows outbound to NAT/VPC Endpoints
- [ ] SQS queues created with correct settings
- [ ] S3 bucket accessible from private subnet
- [ ] OpenAI API key valid and has sufficient quota
- [ ] CloudWatch log group created
- [ ] CloudWatch alarms configured
- [ ] Sentence Transformer model downloaded (first startup may be slow)
