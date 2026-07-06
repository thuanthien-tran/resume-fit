# 12. Thiết Kế Error Handling (Exception Handling Design)

## 12.1 Exception Hierarchy

```
BaseWorkerException
├── ConfigurationError              # Invalid config, missing env vars
├── QueueError                      # SQS-related errors
│   ├── MessageParseError           # Invalid message format
│   ├── MessageValidationError      # Schema validation failed
│   └── QueueConnectionError        # Cannot connect to SQS
├── StorageError                    # S3-related errors
│   ├── FileNotFoundError           # S3 key doesn't exist
│   ├── FileDownloadError           # Download failed (network)
│   └── FileUploadError             # Upload failed
├── ParsingError                    # Document parsing errors
│   ├── UnsupportedFileTypeError    # Not PDF/DOCX/TXT
│   ├── CorruptedFileError          # File cannot be read
│   └── EmptyDocumentError          # No text extracted
├── ExtractionError                 # Skill extraction errors
│   └── DictionaryLoadError         # Cannot load skill dictionary
├── MatchingError                   # Matching engine errors
│   ├── EmbeddingError              # Model inference failed
│   └── InsufficientDataError       # Not enough data to match
├── ScoringError                    # Scoring errors
│   └── InvalidWeightError          # Weights don't sum to 1.0
├── AIAnalysisError                 # OpenAI errors
│   ├── AITimeoutError              # API call timed out
│   ├── AIRateLimitError            # Rate limited
│   ├── AIResponseParseError        # Cannot parse response
│   └── AIUnavailableError          # Service down
├── DatabaseError                   # PostgreSQL errors
│   ├── ConnectionError             # Cannot connect
│   ├── QueryError                  # Query execution failed
│   └── TransactionError            # Transaction commit failed
└── RetryExhaustedError             # Max retries reached
```

## 12.2 Exception Base Classes

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class BaseWorkerException(Exception):
    message: str
    error_code: str
    details: Dict[str, Any] = field(default_factory=dict)
    retryable: bool = False
    original_error: Optional[Exception] = None

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "retryable": self.retryable,
        }
```

## 12.3 Error Classification

| Error Type | Retryable | Action | Max Retries |
|-----------|-----------|--------|-------------|
| S3 Download Timeout | Yes | Retry with backoff | 3 |
| S3 File Not Found | No | Fail immediately | 0 |
| Corrupted File | No | Fail immediately | 0 |
| DB Connection Lost | Yes | Retry with backoff | 3 |
| DB Query Error | No | Fail immediately | 0 |
| OpenAI Timeout | Yes | Retry once | 1 |
| OpenAI Rate Limit | Yes | Wait + retry | 2 |
| OpenAI Unavailable | No (graceful) | Skip AI, continue | 0 |
| Invalid Message | No | Delete + log | 0 |
| Embedding Model Error | Yes | Retry | 2 |
| SQS Connection | Yes | Retry with backoff | 5 |

## 12.4 Retry Strategy

```python
from functools import wraps
import time
import random

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise RetryExhaustedError(
                            message=f"Max retries ({max_retries}) exhausted",
                            error_code="RETRY_EXHAUSTED",
                            original_error=e,
                            details={"function": func.__name__, "attempts": attempt + 1}
                        )
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    # Add jitter (±25%)
                    jitter = delay * 0.25 * (2 * random.random() - 1)
                    actual_delay = delay + jitter
                    time.sleep(actual_delay)
            raise last_exception
        return wrapper
    return decorator
```

## 12.5 Error Handling Flow

```
┌──────────────────┐
│ Exception Raised │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│ Is it retryable?     │
└────────┬─────────────┘
         │
    ┌────┴────┐
    │         │
   YES        NO
    │         │
    ▼         ▼
┌────────┐  ┌────────────────────────────┐
│ Retry  │  │ Is it critical (blocks job)?│
│ Logic  │  └────────┬───────────────────┘
└───┬────┘           │
    │           ┌────┴────┐
    │          YES        NO
    │           │         │
    │           ▼         ▼
    │    ┌──────────┐  ┌────────────────┐
    │    │Fail Job  │  │Log Warning     │
    │    │Mark Error│  │Continue Process │
    │    │DLQ if max│  │(Graceful Degrade)│
    │    └──────────┘  └────────────────┘
    │
    ▼
┌──────────────────┐
│ Retry Exhausted? │
└────────┬─────────┘
    ┌────┴────┐
   YES        NO
    │         │
    ▼         ▼
┌────────┐  ┌──────────┐
│Fail Job│  │ Success  │
│Send DLQ│  │ Continue │
└────────┘  └──────────┘
```

## 12.6 Graceful Degradation Matrix

| Component Failure | System Behavior | User Impact |
|-------------------|-----------------|-------------|
| OpenAI API down | Skip AI analysis, complete with score only | No AI recommendations |
| Semantic model error | Fall back to fuzzy-only matching | Slightly lower match quality |
| S3 upload (report) | Save report in DB instead | Report accessible via API only |
| DB intermittent | Retry 3x, then fail job | Job reprocessed later |
| PDF corruption | Mark job failed with clear error | User asked to re-upload |

## 12.7 Dead Letter Queue (DLQ) Handling

```python
# DLQ Message format
{
    "original_message": { ... },       # Original SQS message
    "error": {
        "code": "PARSING_ERROR",
        "message": "Could not extract text from PDF",
        "traceback": "...",
        "timestamp": "2024-01-15T10:30:45Z"
    },
    "metadata": {
        "job_id": "uuid",
        "retry_count": 3,
        "first_attempt_at": "2024-01-15T10:30:00Z",
        "last_attempt_at": "2024-01-15T10:30:45Z",
        "worker_id": "worker-01"
    }
}
```

### DLQ Processing Rules
1. Messages in DLQ trigger CloudWatch alarm
2. DLQ retention: 14 days
3. Manual review required before reprocessing
4. Reprocessing via admin script (`scripts/reprocess_dlq.py`)

## 12.8 Error Response Structure (Stored in DB)

```python
# processing_jobs.error_message format
{
    "error_code": "PARSING_ERROR",
    "message": "Failed to extract text from PDF file",
    "stage": "document_parsing",  # Which pipeline stage failed
    "details": {
        "file_type": "pdf",
        "s3_key": "uploads/resumes/abc.pdf",
        "file_size": 1048576
    },
    "retries_attempted": 3,
    "timestamp": "2024-01-15T10:30:45Z"
}
```

## 12.9 Global Exception Handler

```python
def handle_job_error(
    job_id: UUID,
    error: Exception,
    job_repo: JobRepositoryProtocol,
    logger: BoundLogger,
) -> None:
    """Central error handler for job processing failures."""

    if isinstance(error, BaseWorkerException):
        error_data = error.to_dict()
    else:
        error_data = {
            "error_code": "UNEXPECTED_ERROR",
            "message": str(error),
            "details": {"type": type(error).__name__},
            "retryable": False,
        }

    logger.error(
        "job_processing_failed",
        error_code=error_data["error_code"],
        error_message=error_data["message"],
        retryable=error_data["retryable"],
    )

    job_repo.update_status(
        job_id=job_id,
        status=JobStatus.FAILED,
        error_message=json.dumps(error_data),
    )
```

## 12.10 Health Check Error Detection

```python
# Worker reports unhealthy if:
# 1. Cannot connect to SQS for > 60 seconds
# 2. Cannot connect to DB for > 30 seconds
# 3. Last 5 consecutive jobs all failed
# 4. Memory usage > 90%

class HealthCheck:
    def __init__(self):
        self.consecutive_failures = 0
        self.last_sqs_success: Optional[datetime] = None
        self.last_db_success: Optional[datetime] = None

    def is_healthy(self) -> bool:
        now = datetime.utcnow()
        if self.last_sqs_success and (now - self.last_sqs_success).seconds > 60:
            return False
        if self.last_db_success and (now - self.last_db_success).seconds > 30:
            return False
        if self.consecutive_failures >= 5:
            return False
        return True
```
