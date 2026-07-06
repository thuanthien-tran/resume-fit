# 1. Phân Tích Yêu Cầu (Requirements Analysis)

## 1.1 Tổng Quan Module

**Module:** Worker Service - Skill Matching Engine & AI Analysis  
**Vai trò:** Xử lý CV sau khi Backend đẩy Job vào Amazon SQS  
**Vị trí trong hệ thống:** EC2 Private Subnet, nhận message từ SQS, xử lý và lưu kết quả vào PostgreSQL

## 1.2 Functional Requirements

### FR-01: SQS Message Consumption
- Poll message từ Amazon SQS queue
- Parse message body chứa job_id, resume_s3_key, jd_s3_key
- Acknowledge message sau khi xử lý thành công
- Retry failed messages với exponential backoff
- Move to Dead Letter Queue sau max retries

### FR-02: File Download & Parse
- Download CV (PDF/DOCX) từ Amazon S3
- Download Job Description (PDF/DOCX/TXT) từ Amazon S3
- Parse PDF sử dụng PyMuPDF (fitz)
- Parse DOCX sử dụng python-docx
- Text cleaning & normalization

### FR-03: Skill Extraction
- Extract skills từ CV text
- Extract skills từ JD text
- Sử dụng Skill Dictionary (500+ skills)
- Alias mapping (e.g., "JS" → "JavaScript")
- Category-based extraction (Programming, Framework, Database, Cloud, Soft Skills)

### FR-04: Resume Matching
- Fuzzy matching sử dụng RapidFuzz (token_sort_ratio)
- Semantic matching sử dụng Sentence Transformers
- Cosine similarity calculation
- Hybrid scoring (fuzzy + semantic)

### FR-05: Resume Scoring
- Tính điểm tổng hợp (0-100)
- Weighted scoring theo category
- Experience level bonus
- Certification bonus
- Education relevance score

### FR-06: AI Analysis & Recommendation
- OpenAI GPT-4o integration
- Structured prompt engineering
- Strengths/Weaknesses analysis
- Interview preparation questions
- Career development suggestions

### FR-07: Report Generation
- JSON structured report
- Summary report
- Detailed matching breakdown
- Skill gap analysis

### FR-08: Database Persistence
- Lưu kết quả matching vào PostgreSQL
- Cập nhật job status (processing → completed/failed)
- Store analysis report

## 1.3 Non-Functional Requirements

### NFR-01: Performance
- Xử lý 1 CV trong < 30 seconds (excluding AI call)
- AI analysis < 15 seconds
- Support concurrent processing (multi-thread workers)

### NFR-02: Reliability
- Retry mechanism với exponential backoff
- Dead Letter Queue cho failed messages
- Graceful shutdown handling
- Idempotent processing

### NFR-03: Scalability
- Horizontal scaling qua multiple EC2 instances
- Configurable worker count
- Queue-based load distribution

### NFR-04: Security
- IAM role-based access (không hardcode credentials)
- Encrypted connections (TLS)
- No sensitive data in logs

### NFR-05: Observability
- Structured logging (JSON format)
- Correlation ID tracking
- Metrics collection
- Health check endpoint

### NFR-06: Maintainability
- Clean Architecture
- SOLID principles
- Repository Pattern
- 80%+ test coverage

## 1.4 Technical Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| Queue | Amazon SQS (boto3) |
| Storage | Amazon S3 (boto3) |
| Database | PostgreSQL (asyncpg/psycopg2) |
| PDF Parse | PyMuPDF (fitz) |
| DOCX Parse | python-docx |
| Fuzzy Match | RapidFuzz |
| Embedding | sentence-transformers (all-MiniLM-L6-v2) |
| AI | OpenAI GPT-4o |
| Container | Docker |
| Logging | structlog |
| Config | pydantic-settings |
| Testing | pytest, pytest-asyncio, moto |

## 1.5 Input/Output Design

### Input (SQS Message)
```json
{
  "job_id": "uuid-v4",
  "resume_s3_key": "uploads/resumes/uuid.pdf",
  "jd_s3_key": "uploads/jds/uuid.pdf",
  "user_id": "uuid-v4",
  "created_at": "2024-01-01T00:00:00Z",
  "priority": "normal",
  "options": {
    "include_ai_analysis": true,
    "matching_threshold": 0.6
  }
}
```

### Output (PostgreSQL + Job Status Update)
```json
{
  "job_id": "uuid-v4",
  "status": "completed",
  "result": {
    "overall_score": 78.5,
    "category_scores": {
      "technical_skills": 82.0,
      "soft_skills": 65.0,
      "experience": 80.0,
      "education": 75.0
    },
    "matched_skills": [...],
    "missing_skills": [...],
    "skill_gap_analysis": {...},
    "ai_analysis": {
      "strengths": [...],
      "weaknesses": [...],
      "interview_questions": [...],
      "recommendations": [...]
    },
    "report_url": "s3://bucket/reports/uuid.json"
  },
  "processing_time_ms": 12500,
  "completed_at": "2024-01-01T00:00:30Z"
}
```

## 1.6 Constraints

- Module KHÔNG expose HTTP API (headless worker)
- Module KHÔNG handle file upload (Backend đã upload lên S3)
- Module PHẢI compatible với existing PostgreSQL schema
- Module PHẢI sử dụng IAM Role (không hardcode AWS credentials)
- OpenAI API key qua environment variable
- Module chạy trên EC2 Private Subnet (không public internet trực tiếp, qua NAT Gateway)
