# 5. Thiết Kế Folder Structure (Directory Design)

## 5.1 Cây Thư Mục Hoàn Chỉnh

```
worker-service/
│
├── app/
│   ├── __init__.py
│   ├── main.py                          # Entry point - khởi tạo và chạy worker
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                  # Pydantic Settings - load từ env
│   │   └── constants.py                 # Application constants
│   │
│   ├── models/                          # Domain Entities & Value Objects
│   │   ├── __init__.py
│   │   ├── job.py                       # ProcessingJob entity
│   │   ├── resume.py                    # Resume entity
│   │   ├── job_description.py           # JobDescription entity
│   │   ├── skill.py                     # Skill value object
│   │   ├── match_result.py              # MatchResult entity
│   │   ├── score.py                     # ScoreResult value object
│   │   ├── report.py                    # Report entity
│   │   └── enums.py                     # Status enums, category enums
│   │
│   ├── schemas/                         # DTOs & Validation Schemas
│   │   ├── __init__.py
│   │   ├── sqs_message.py              # SQS message schema
│   │   ├── job_payload.py              # Job payload validation
│   │   └── report_schema.py            # Report output schema
│   │
│   ├── worker/                          # Worker Service Core
│   │   ├── __init__.py
│   │   ├── worker_manager.py           # Quản lý lifecycle của workers
│   │   ├── job_processor.py            # Orchestrate processing pipeline
│   │   └── health_check.py            # Worker health monitoring
│   │
│   ├── queue/                           # SQS Integration
│   │   ├── __init__.py
│   │   ├── sqs_consumer.py            # Poll và receive messages
│   │   ├── sqs_publisher.py           # Publish to DLQ
│   │   └── message_handler.py         # Parse và validate messages
│   │
│   ├── services/                        # Application Services (Use Cases)
│   │   ├── __init__.py
│   │   ├── document_service.py         # Download + Parse orchestration
│   │   ├── extraction_service.py       # Skill extraction orchestration
│   │   ├── matching_service.py         # Matching orchestration
│   │   ├── scoring_service.py          # Scoring orchestration
│   │   ├── analysis_service.py         # AI analysis orchestration
│   │   └── report_service.py           # Report generation
│   │
│   ├── parser/                          # Document Parsing
│   │   ├── __init__.py
│   │   ├── base_parser.py             # Abstract base parser interface
│   │   ├── pdf_parser.py              # PDF parsing (PyMuPDF)
│   │   ├── docx_parser.py            # DOCX parsing (python-docx)
│   │   ├── txt_parser.py             # Plain text parsing
│   │   ├── parser_factory.py          # Factory pattern for parser selection
│   │   └── text_cleaner.py           # Text cleaning & normalization
│   │
│   ├── extractor/                       # Skill Extraction Engine
│   │   ├── __init__.py
│   │   ├── skill_extractor.py         # Main extraction logic
│   │   ├── skill_dictionary.py        # Skill dictionary loader
│   │   ├── alias_mapper.py           # Skill alias mapping
│   │   └── data/
│   │       ├── skills.json            # Master skill dictionary
│   │       └── aliases.json           # Alias mapping data
│   │
│   ├── matcher/                         # Resume Matching Engine
│   │   ├── __init__.py
│   │   ├── base_matcher.py            # Abstract matcher interface
│   │   ├── exact_matcher.py           # Exact string matching
│   │   ├── fuzzy_matcher.py           # RapidFuzz matching
│   │   ├── semantic_matcher.py        # Sentence Transformer matching
│   │   ├── hybrid_matcher.py          # Combine all matchers
│   │   └── embedding_cache.py        # Cache embeddings for performance
│   │
│   ├── scorer/                          # Resume Scoring Engine
│   │   ├── __init__.py
│   │   ├── score_calculator.py        # Main scoring logic
│   │   ├── weight_config.py           # Category weights configuration
│   │   └── bonus_calculator.py        # Experience/Certification bonuses
│   │
│   ├── ai/                              # AI Analysis Service
│   │   ├── __init__.py
│   │   ├── openai_client.py           # OpenAI API client wrapper
│   │   ├── prompt_builder.py          # Prompt engineering
│   │   ├── response_parser.py         # Parse AI response
│   │   └── prompts/
│   │       ├── analysis.txt           # Main analysis prompt template
│   │       ├── interview_questions.txt # Interview question prompt
│   │       └── recommendations.txt    # Career recommendation prompt
│   │
│   ├── report/                          # Report Generator
│   │   ├── __init__.py
│   │   ├── report_builder.py          # Build final report
│   │   └── report_uploader.py         # Upload report to S3
│   │
│   ├── database/                        # Database Infrastructure
│   │   ├── __init__.py
│   │   ├── connection.py              # Connection pool management
│   │   ├── session.py                 # Session/transaction management
│   │   └── migrations/
│   │       ├── 001_create_processing_jobs.sql
│   │       ├── 002_create_matching_results.sql
│   │       └── 003_add_indexes.sql
│   │
│   ├── repositories/                    # Repository Pattern Implementation
│   │   ├── __init__.py
│   │   ├── base_repository.py         # Abstract base repository
│   │   ├── job_repository.py          # Processing jobs CRUD
│   │   ├── result_repository.py       # Matching results CRUD
│   │   ├── resume_repository.py       # Resume read/update
│   │   └── jd_repository.py           # Job description read/update
│   │
│   ├── storage/                         # S3 File Storage
│   │   ├── __init__.py
│   │   └── s3_client.py              # S3 download/upload operations
│   │
│   ├── logger/                          # Structured Logging
│   │   ├── __init__.py
│   │   ├── logger_config.py           # structlog configuration
│   │   └── correlation.py            # Correlation ID management
│   │
│   ├── exceptions/                      # Custom Exceptions
│   │   ├── __init__.py
│   │   ├── base.py                    # Base exception classes
│   │   ├── parsing_errors.py          # Document parsing errors
│   │   ├── matching_errors.py         # Matching engine errors
│   │   ├── storage_errors.py          # S3/DB storage errors
│   │   ├── queue_errors.py            # SQS errors
│   │   └── ai_errors.py              # OpenAI API errors
│   │
│   └── utils/                           # Shared Utilities
│       ├── __init__.py
│       ├── retry.py                   # Retry decorator with backoff
│       ├── timer.py                   # Execution time measurement
│       └── validators.py             # Common validation helpers
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures
│   │
│   ├── unit/                           # Unit Tests
│   │   ├── __init__.py
│   │   ├── test_text_cleaner.py
│   │   ├── test_skill_extractor.py
│   │   ├── test_exact_matcher.py
│   │   ├── test_fuzzy_matcher.py
│   │   ├── test_semantic_matcher.py
│   │   ├── test_score_calculator.py
│   │   ├── test_prompt_builder.py
│   │   ├── test_report_builder.py
│   │   └── test_message_handler.py
│   │
│   ├── integration/                    # Integration Tests
│   │   ├── __init__.py
│   │   ├── test_sqs_consumer.py
│   │   ├── test_s3_client.py
│   │   ├── test_job_repository.py
│   │   ├── test_result_repository.py
│   │   ├── test_openai_client.py
│   │   └── test_pdf_parser.py
│   │
│   ├── e2e/                            # End-to-End Tests
│   │   ├── __init__.py
│   │   ├── test_full_pipeline.py
│   │   └── test_error_scenarios.py
│   │
│   └── fixtures/                       # Test Data
│       ├── sample_resume.pdf
│       ├── sample_resume.docx
│       ├── sample_jd.pdf
│       ├── sample_jd.txt
│       └── expected_outputs/
│           ├── extracted_skills.json
│           ├── match_result.json
│           └── final_report.json
│
├── scripts/
│   ├── run_worker.sh                  # Start worker script
│   ├── run_migrations.sh             # Run DB migrations
│   ├── health_check.sh               # Health check for Docker
│   └── seed_skills.py                # Seed skill dictionary
│
├── Dockerfile
├── docker-compose.yml                 # Local development stack
├── requirements.txt                   # Production dependencies
├── requirements-dev.txt              # Development/test dependencies
├── .env.example                      # Environment template
├── .dockerignore
├── .gitignore
├── pyproject.toml                    # Project metadata + tool configs
└── README.md
```

## 5.2 Mô Tả Chức Năng Từng Thư Mục

| Thư mục | Chức năng | Layer |
|---------|-----------|-------|
| `app/config/` | Application configuration, environment loading | Infrastructure |
| `app/models/` | Domain entities, value objects, business rules | Domain |
| `app/schemas/` | Data transfer objects, message validation | Interface Adapters |
| `app/worker/` | Worker lifecycle management, job dispatching | Interface Adapters |
| `app/queue/` | SQS polling, message parsing, DLQ handling | Infrastructure |
| `app/services/` | Use cases / application services orchestration | Application |
| `app/parser/` | Document parsing (PDF, DOCX, TXT) | Infrastructure |
| `app/extractor/` | Skill extraction from text | Domain Services |
| `app/matcher/` | Skill matching algorithms | Domain Services |
| `app/scorer/` | Score calculation logic | Domain Services |
| `app/ai/` | OpenAI integration, prompt engineering | Infrastructure |
| `app/report/` | Report generation and upload | Application |
| `app/database/` | Database connection, migrations | Infrastructure |
| `app/repositories/` | Data access layer (Repository Pattern) | Interface Adapters |
| `app/storage/` | S3 file operations | Infrastructure |
| `app/logger/` | Structured logging configuration | Infrastructure |
| `app/exceptions/` | Custom exception hierarchy | Domain |
| `app/utils/` | Cross-cutting utilities | Shared |
| `tests/unit/` | Isolated unit tests (no external deps) | - |
| `tests/integration/` | Tests with mocked AWS services (moto) | - |
| `tests/e2e/` | Full pipeline tests | - |
| `tests/fixtures/` | Sample files and expected outputs | - |
| `scripts/` | Operational scripts | - |

## 5.3 File Naming Convention

- Python files: `snake_case.py`
- Test files: `test_<module_name>.py`
- Config files: `snake_case.py`
- Data files: `snake_case.json`
- Prompt templates: `snake_case.txt`
- SQL migrations: `NNN_description.sql`
