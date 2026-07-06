# 3. Thiết Kế Database (Database Design)

## 3.1 Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────────┐       ┌──────────────────┐
│      users       │       │    processing_jobs    │       │  job_descriptions │
├──────────────────┤       ├──────────────────────┤       ├──────────────────┤
│ id (PK)          │◀──────│ user_id (FK)         │       │ id (PK)          │
│ email            │       │ id (PK)              │──────▶│ user_id (FK)     │
│ name             │       │ resume_id (FK)       │       │ title            │
│ created_at       │       │ jd_id (FK)           │       │ company          │
└──────────────────┘       │ status               │       │ s3_key           │
                           │ priority             │       │ raw_text         │
                           │ retry_count          │       │ required_skills  │
                           │ error_message        │       │ created_at       │
                           │ started_at           │       └──────────────────┘
                           │ completed_at         │
                           │ created_at           │
                           └──────────┬───────────┘
                                      │
                                      │ 1:1
                                      ▼
                           ┌──────────────────────┐
                           │   matching_results   │
                           ├──────────────────────┤
                           │ id (PK)              │
                           │ job_id (FK, UNIQUE)  │
                           │ overall_score        │
                           │ technical_score      │
                           │ soft_skills_score    │
                           │ experience_score     │
                           │ education_score      │
                           │ matched_skills       │
                           │ missing_skills       │
                           │ skill_details        │
                           │ ai_analysis          │
                           │ report_s3_key        │
                           │ processing_time_ms   │
                           │ created_at           │
                           └──────────────────────┘

┌──────────────────┐
│     resumes      │
├──────────────────┤
│ id (PK)          │
│ user_id (FK)     │
│ filename         │
│ s3_key           │
│ file_type        │
│ raw_text         │
│ extracted_skills │
│ parsed_at        │
│ created_at       │
└──────────────────┘
```

## 3.2 Table Definitions

### 3.2.1 processing_jobs

Worker Service chỉ đọc/cập nhật table này (Backend tạo record).

```sql
CREATE TABLE processing_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    resume_id       UUID NOT NULL REFERENCES resumes(id),
    jd_id           UUID NOT NULL REFERENCES job_descriptions(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority        VARCHAR(10) NOT NULL DEFAULT 'normal',
    retry_count     INTEGER NOT NULL DEFAULT 0,
    max_retries     INTEGER NOT NULL DEFAULT 3,
    error_message   TEXT,
    worker_id       VARCHAR(100),
    started_at      TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'dead_letter')),
    CONSTRAINT chk_priority CHECK (priority IN ('low', 'normal', 'high'))
);

CREATE INDEX idx_jobs_status ON processing_jobs(status);
CREATE INDEX idx_jobs_user_id ON processing_jobs(user_id);
CREATE INDEX idx_jobs_created_at ON processing_jobs(created_at);
```

### 3.2.2 matching_results

Worker Service tạo record này sau khi xử lý xong.

```sql
CREATE TABLE matching_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id              UUID NOT NULL UNIQUE REFERENCES processing_jobs(id),
    overall_score       DECIMAL(5,2) NOT NULL,
    technical_score     DECIMAL(5,2) NOT NULL,
    soft_skills_score   DECIMAL(5,2) NOT NULL,
    experience_score    DECIMAL(5,2) NOT NULL,
    education_score     DECIMAL(5,2) NOT NULL,
    matched_skills      JSONB NOT NULL DEFAULT '[]',
    missing_skills      JSONB NOT NULL DEFAULT '[]',
    skill_details       JSONB NOT NULL DEFAULT '{}',
    ai_analysis         JSONB,
    report_s3_key       VARCHAR(500),
    processing_time_ms  INTEGER NOT NULL,
    model_version       VARCHAR(50) NOT NULL DEFAULT 'v1.0',
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_results_job_id ON matching_results(job_id);
CREATE INDEX idx_results_overall_score ON matching_results(overall_score);
```

### 3.2.3 resumes (Read-only cho Worker)

```sql
CREATE TABLE resumes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    filename        VARCHAR(255) NOT NULL,
    s3_key          VARCHAR(500) NOT NULL,
    file_type       VARCHAR(10) NOT NULL,
    file_size_bytes INTEGER,
    raw_text        TEXT,
    extracted_skills JSONB DEFAULT '[]',
    parsed_at       TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_file_type CHECK (file_type IN ('pdf', 'docx'))
);
```

### 3.2.4 job_descriptions (Read-only cho Worker)

```sql
CREATE TABLE job_descriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    title           VARCHAR(255) NOT NULL,
    company         VARCHAR(255),
    s3_key          VARCHAR(500) NOT NULL,
    file_type       VARCHAR(10) NOT NULL,
    raw_text        TEXT,
    required_skills JSONB DEFAULT '[]',
    preferred_skills JSONB DEFAULT '[]',
    experience_years INTEGER,
    education_level VARCHAR(50),
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_jd_file_type CHECK (file_type IN ('pdf', 'docx', 'txt'))
);
```

## 3.3 JSONB Column Schemas

### matched_skills
```json
[
  {
    "skill": "Python",
    "category": "programming",
    "match_type": "exact",
    "confidence": 0.98,
    "source_text": "5 years of Python development"
  }
]
```

### missing_skills
```json
[
  {
    "skill": "Kubernetes",
    "category": "devops",
    "importance": "required",
    "suggestion": "Consider obtaining CKA certification"
  }
]
```

### skill_details
```json
{
  "resume_skills": ["Python", "AWS", "Docker"],
  "jd_required_skills": ["Python", "AWS", "Kubernetes"],
  "jd_preferred_skills": ["Docker", "Terraform"],
  "fuzzy_matches": [
    {"resume": "JS", "jd": "JavaScript", "score": 0.95}
  ],
  "semantic_matches": [
    {"resume": "Machine Learning", "jd": "ML Engineering", "score": 0.88}
  ]
}
```

### ai_analysis
```json
{
  "model": "gpt-4o",
  "strengths": [
    "Strong Python background with 5+ years experience",
    "Solid AWS cloud infrastructure knowledge"
  ],
  "weaknesses": [
    "No container orchestration experience (Kubernetes)",
    "Limited CI/CD pipeline experience"
  ],
  "interview_questions": [
    {
      "question": "Describe your experience with distributed systems",
      "category": "technical",
      "difficulty": "medium",
      "rationale": "Tests depth of systems design knowledge"
    }
  ],
  "recommendations": [
    "Pursue Kubernetes certification (CKA)",
    "Build a CI/CD pipeline project to demonstrate capability"
  ],
  "overall_assessment": "Strong candidate for mid-level position...",
  "fit_level": "good_fit"
}
```

## 3.4 Database Access Pattern (Worker Service)

| Operation | Table | Type | Frequency |
|-----------|-------|------|-----------|
| Get job details | processing_jobs | READ | Per message |
| Update job status to 'processing' | processing_jobs | UPDATE | Per message |
| Get resume data | resumes | READ | Per message |
| Update resume raw_text & skills | resumes | UPDATE | Per message |
| Get JD data | job_descriptions | READ | Per message |
| Update JD raw_text & skills | job_descriptions | UPDATE | Per message |
| Insert matching result | matching_results | INSERT | Per message |
| Update job status to 'completed' | processing_jobs | UPDATE | Per message |
| Update job status to 'failed' | processing_jobs | UPDATE | On error |

## 3.5 Migration Strategy

Worker Service bao gồm migration scripts nhưng KHÔNG tự động run migration trong production.
Migration được run bởi DevOps/DBA trước khi deploy worker.

```
migrations/
├── 001_create_processing_jobs.sql
├── 002_create_matching_results.sql
└── 003_add_indexes.sql
```
