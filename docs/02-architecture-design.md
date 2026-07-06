# 2. Thiết Kế Kiến Trúc (Architecture Design)

## 2.1 Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                       │
│  (SQS, S3, PostgreSQL, OpenAI API, File System)             │
├─────────────────────────────────────────────────────────────┤
│                    INTERFACE ADAPTERS LAYER                   │
│  (Repositories, Queue Consumer, S3 Client, AI Client)       │
├─────────────────────────────────────────────────────────────┤
│                    APPLICATION LAYER (Use Cases)              │
│  (ProcessResumeUseCase, MatchSkillsUseCase, ScoreUseCase)   │
├─────────────────────────────────────────────────────────────┤
│                    DOMAIN LAYER (Entities & Rules)            │
│  (Resume, JobDescription, SkillMatch, Score, Report)        │
└─────────────────────────────────────────────────────────────┘
```

## 2.2 Dependency Rule

- Domain Layer: KHÔNG phụ thuộc vào bất kỳ layer nào khác
- Application Layer: Chỉ phụ thuộc Domain Layer
- Interface Adapters: Phụ thuộc Application + Domain
- Infrastructure: Phụ thuộc tất cả layers phía trong

```
Infrastructure → Interface Adapters → Application → Domain
     ↓                  ↓                  ↓           ↓
  boto3, DB         Repositories       Use Cases    Entities
  OpenAI SDK        Adapters           Services     Value Objects
  PyMuPDF           Presenters         DTOs         Business Rules
```

## 2.3 Component Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Worker Service                                 │
│                                                                        │
│  ┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐   │
│  │ SQS Consumer │────▶│ Job Dispatcher│────▶│ ProcessResumeUseCase│   │
│  └─────────────┘     └──────────────┘     └──────────┬──────────┘   │
│                                                       │               │
│          ┌────────────────────────────────────────────┼───────┐      │
│          │                                            │       │      │
│          ▼                                            ▼       ▼      │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────┐ ┌─────┐ ┌────┐ │
│  │ S3 Downloader│  │ Document Parser│  │ Skill    │ │Score│ │ AI │ │
│  └──────────────┘  └───────────────┘  │ Extractor│ │     │ │    │ │
│                                        └─────┬─────┘ └──┬──┘ └─┬──┘ │
│                                              │          │      │     │
│                                              ▼          │      │     │
│                                        ┌──────────┐    │      │     │
│                                        │ Matcher  │────┘      │     │
│                                        └──────────┘           │     │
│                                              │                │     │
│                                              ▼                ▼     │
│                                        ┌──────────────────────────┐ │
│                                        │    Report Generator      │ │
│                                        └────────────┬─────────────┘ │
│                                                     │               │
│                                                     ▼               │
│                                        ┌──────────────────────────┐ │
│                                        │  PostgreSQL Repository   │ │
│                                        └──────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

## 2.4 Module Responsibilities

### Domain Layer
| Module | Responsibility |
|--------|---------------|
| `models/resume.py` | Resume entity với extracted data |
| `models/job_description.py` | JD entity với required skills |
| `models/skill.py` | Skill value object |
| `models/match_result.py` | Matching result entity |
| `models/score.py` | Scoring result value object |
| `models/report.py` | Final report entity |
| `models/job.py` | Processing job entity |

### Application Layer (Use Cases)
| Use Case | Responsibility |
|----------|---------------|
| `ProcessResumeUseCase` | Orchestrate toàn bộ pipeline |
| `ParseDocumentUseCase` | Download + Parse document |
| `ExtractSkillsUseCase` | Extract skills từ text |
| `MatchSkillsUseCase` | Match resume skills vs JD skills |
| `ScoreResumeUseCase` | Tính điểm tổng hợp |
| `AnalyzeResumeUseCase` | AI analysis |
| `GenerateReportUseCase` | Tạo report |

### Interface Adapters
| Adapter | Responsibility |
|---------|---------------|
| `SQSConsumer` | Poll và parse SQS messages |
| `S3FileRepository` | Download/upload files từ S3 |
| `PostgresJobRepository` | CRUD job records |
| `PostgresResultRepository` | CRUD matching results |
| `OpenAIAnalysisClient` | Call OpenAI API |
| `DocumentParserAdapter` | PDF/DOCX parsing |

### Infrastructure
| Component | Responsibility |
|-----------|---------------|
| `boto3 SQS client` | AWS SQS SDK |
| `boto3 S3 client` | AWS S3 SDK |
| `psycopg2/asyncpg` | PostgreSQL driver |
| `openai SDK` | OpenAI API calls |
| `PyMuPDF` | PDF text extraction |
| `python-docx` | DOCX text extraction |

## 2.5 SOLID Principles Application

### Single Responsibility
- Mỗi class chỉ có 1 lý do để thay đổi
- `PDFParser` chỉ parse PDF, `DOCXParser` chỉ parse DOCX
- `FuzzyMatcher` chỉ fuzzy match, `SemanticMatcher` chỉ semantic match

### Open/Closed
- `DocumentParser` interface → thêm parser mới không sửa code cũ
- `SkillMatcher` interface → thêm matching strategy mới không ảnh hưởng existing

### Liskov Substitution
- `PDFParser` và `DOCXParser` đều implement `DocumentParser` interface
- Có thể swap bất kỳ implementation nào mà không break system

### Interface Segregation
- `FileRepository` tách biệt với `JobRepository`
- `SkillExtractor` tách biệt với `SkillMatcher`

### Dependency Inversion
- Use Cases depend on abstractions (interfaces), không depend on concrete implementations
- Repository interfaces defined trong Application layer, implemented trong Infrastructure

## 2.6 Design Patterns Used

| Pattern | Where | Why |
|---------|-------|-----|
| Repository | Database access | Tách business logic khỏi data access |
| Strategy | Matching algorithms | Swap matching strategies dễ dàng |
| Factory | Document parsers | Tạo parser phù hợp theo file type |
| Pipeline | Processing flow | Chain processing steps |
| Observer | Job status updates | Decouple status notification |
| Retry | SQS/API calls | Handle transient failures |
| Circuit Breaker | OpenAI calls | Prevent cascade failures |

## 2.7 Error Handling Strategy

```
┌─────────────────┐
│ SQS Message     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     Retry (max 3)      ┌─────────────────┐
│ Process Job     │◀───────────────────────▶│ Retry Handler   │
└────────┬────────┘                         └─────────────────┘
         │                                           │
         │ Failed after max retries                  │
         ▼                                           ▼
┌─────────────────┐                         ┌─────────────────┐
│ Mark Job Failed │                         │ Dead Letter Queue│
└────────┬────────┘                         └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Log & Alert     │
└─────────────────┘
```

## 2.8 Concurrency Model

```
Main Process
     │
     ├── Worker Thread 1 ──▶ Poll SQS ──▶ Process Job
     ├── Worker Thread 2 ──▶ Poll SQS ──▶ Process Job
     ├── Worker Thread 3 ──▶ Poll SQS ──▶ Process Job
     └── Health Check Thread ──▶ Monitor workers
```

- Sử dụng `concurrent.futures.ThreadPoolExecutor`
- Configurable worker count (default: 3)
- Each worker polls independently
- Graceful shutdown via signal handlers (SIGTERM, SIGINT)
