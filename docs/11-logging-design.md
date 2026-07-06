# 11. Thiết Kế Logging (Logging Design)

## 11.1 Logging Strategy

```
┌─────────────────────────────────────────────────────────┐
│                   STRUCTURED LOGGING                     │
│                                                          │
│  Library: structlog                                      │
│  Format: JSON (production) / Console (development)      │
│  Output: stdout (Docker-friendly)                       │
│  Level: Configurable via LOG_LEVEL env var              │
└─────────────────────────────────────────────────────────┘
```

## 11.2 Log Levels & Usage

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Internal state, raw data | "Extracted 15 skills from resume" |
| INFO | Business events, milestones | "Job processing started", "Job completed" |
| WARNING | Recoverable issues | "AI analysis failed, continuing without", "Retry attempt 2/3" |
| ERROR | Failed operations | "Job processing failed", "Database connection lost" |
| CRITICAL | System-level failures | "Worker shutdown due to unrecoverable error" |

## 11.3 Correlation ID

Mỗi job được gán 1 correlation_id (= job_id) để trace toàn bộ processing chain.

```python
# Correlation ID flow
SQS Message → job_id → bound to logger context → all log entries include job_id

# structlog context binding
logger = structlog.get_logger()
log = logger.bind(
    job_id=str(job_id),
    worker_id=worker_id,
    correlation_id=str(job_id)
)

# All subsequent calls carry context
log.info("processing_started")
log.info("skills_extracted", count=15, categories=["programming", "cloud"])
log.info("matching_completed", match_rate=0.78)
```

## 11.4 Log Schema (JSON Format)

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "info",
  "event": "job_processing_completed",
  "logger": "app.worker.job_processor",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "worker_id": "worker-01",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "duration_ms": 12500,
  "overall_score": 78.5,
  "matched_skills_count": 8,
  "missing_skills_count": 3
}
```

## 11.5 Log Points (What to Log)

### Worker Lifecycle
```
INFO  worker_started          {worker_count, queue_url}
INFO  worker_stopped          {reason, in_flight_jobs}
ERROR worker_crash            {error, traceback}
```

### Job Processing
```
INFO  job_received            {job_id, priority}
INFO  job_processing_started  {job_id, resume_id, jd_id}
INFO  file_downloaded         {job_id, s3_key, file_size_bytes, duration_ms}
INFO  document_parsed         {job_id, file_type, text_length, duration_ms}
INFO  skills_extracted        {job_id, source, skill_count, categories}
INFO  matching_completed      {job_id, matched_count, missing_count, match_rate, duration_ms}
INFO  scoring_completed       {job_id, overall_score, fit_level, duration_ms}
INFO  ai_analysis_completed   {job_id, tokens_used, duration_ms}
WARN  ai_analysis_skipped     {job_id, reason}
INFO  report_generated        {job_id, report_s3_key}
INFO  job_processing_completed {job_id, overall_score, total_duration_ms}
ERROR job_processing_failed   {job_id, error, retry_count, traceback}
```

### Retry & DLQ
```
WARN  job_retry_scheduled     {job_id, attempt, next_delay_ms}
ERROR job_moved_to_dlq        {job_id, total_attempts, last_error}
```

### Infrastructure
```
DEBUG sqs_poll_started        {wait_time_seconds}
DEBUG sqs_poll_empty          {}
WARN  db_connection_retry     {attempt, error}
ERROR s3_download_failed      {s3_key, error}
ERROR openai_api_error        {status_code, error}
```

## 11.6 structlog Configuration

```python
import structlog
import logging
import sys

def configure_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ]
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))
```

## 11.7 Sensitive Data Filtering

```python
SENSITIVE_PATTERNS = [
    "password", "secret", "token", "api_key",
    "authorization", "credential"
]

def filter_sensitive(_, __, event_dict):
    """Remove sensitive data from log entries."""
    for key in list(event_dict.keys()):
        if any(pattern in key.lower() for pattern in SENSITIVE_PATTERNS):
            event_dict[key] = "***REDACTED***"
    return event_dict
```

## 11.8 Performance Metrics Logging

```python
# Timer context manager for duration tracking
class LogTimer:
    def __init__(self, logger, event_name: str):
        self.logger = logger
        self.event_name = event_name
        self.start = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        duration_ms = int((time.perf_counter() - self.start) * 1000)
        self.logger.info(
            f"{self.event_name}_completed",
            duration_ms=duration_ms
        )

# Usage
with LogTimer(log, "document_parsing"):
    content = parser.parse(file_bytes)
```

## 11.9 Log Rotation & Retention

```
Production (Docker/CloudWatch):
  - stdout → Docker logging driver → CloudWatch Logs
  - Retention: 30 days (configurable in CloudWatch)
  - No file rotation needed (stdout-based)

Development:
  - Console output with colors
  - Optional file output for debugging
```
