# 15. Coding Standards & Conventions

## 15.1 Python Style Guide

| Rule | Standard |
|------|----------|
| Formatter | Black (line-length=100) |
| Linter | Ruff |
| Type Checker | mypy (strict) |
| Docstrings | Google style (only for public interfaces) |
| Imports | isort via Ruff (sections: stdlib, third-party, local) |
| Naming | PEP 8 (snake_case functions, PascalCase classes) |

## 15.2 File Structure Convention

Mỗi Python module file theo thứ tự:
```python
"""Module docstring (one line)."""

# Standard library imports
import json
from typing import List, Optional
from uuid import UUID

# Third-party imports
import structlog
from pydantic import BaseModel

# Local imports
from app.models.enums import JobStatus
from app.exceptions.base import BaseWorkerException
```

## 15.3 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Files | snake_case.py | `score_calculator.py` |
| Classes | PascalCase | `ScoreCalculator` |
| Functions/Methods | snake_case | `calculate_score()` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| Private | _prefix | `_compute_similarity()` |
| Type Vars | PascalCase | `T = TypeVar("T")` |
| Dataclass fields | snake_case | `overall_score: float` |

## 15.4 Type Hints

Type hints bắt buộc cho tất cả:
- Function parameters
- Function return types
- Class attributes

```python
# Good
def calculate(self, match_result: MatchResult, threshold: float = 0.8) -> ScoreResult:
    ...

# Bad
def calculate(self, match_result, threshold=0.8):
    ...
```

Sử dụng:
- `Optional[X]` thay vì `X | None` cho Python 3.11 compatibility
- `List[X]`, `Dict[K, V]` từ typing module
- `Tuple[X, Y]` cho fixed-length tuples

## 15.5 Error Handling Rules

1. Mỗi custom exception PHẢI extend `BaseWorkerException`
2. Mỗi exception PHẢI có `error_code` unique
3. KHÔNG catch bare `Exception` trừ khi ở top-level handler
4. KHÔNG dùng `assert` cho runtime validation
5. Log errors TRƯỚC khi raise
6. Include context trong exception details

```python
# Good
raise FileNotFoundError(
    message=f"File not found: {s3_key}",
    error_code="S3_NOT_FOUND",
    details={"s3_key": s3_key, "bucket": bucket},
)

# Bad
raise Exception(f"File not found: {s3_key}")
```

## 15.6 Logging Rules

1. Sử dụng `structlog.get_logger(__name__)` cho mỗi module
2. Event names dùng snake_case: `"job_processing_started"`
3. KHÔNG log sensitive data (passwords, tokens, PII)
4. KHÔNG log raw file content
5. Include metrics trong log: `duration_ms`, `count`, `size_bytes`
6. Mỗi INFO log phải có business value

```python
# Good
logger.info("skills_extracted", count=15, categories=["programming", "cloud"])

# Bad
logger.info("Done extracting skills")
logger.info(f"Found {len(skills)} skills: {skills}")
```

## 15.7 Testing Rules

1. Test file: `test_{module_name}.py`
2. Test class: `Test{ClassName}`
3. Test method: `test_{behavior_being_tested}`
4. Mỗi test chỉ assert 1 behavior
5. Sử dụng fixtures cho shared setup
6. KHÔNG mock internal implementation details
7. Integration tests mark với `@pytest.mark.integration`

```python
# Good
def test_exact_match_returns_confidence_one(self):
    matched, _, _ = self.matcher.match(["Python"], ["Python"])
    assert matched[0].confidence == 1.0

# Bad
def test_matcher(self):
    # Tests too many things at once
    ...
```

## 15.8 Git Commit Convention

```
<type>(<scope>): <subject>

Types: feat, fix, refactor, test, docs, chore, perf
Scope: worker, parser, matcher, scorer, ai, queue, db

Examples:
  feat(matcher): add semantic matching with sentence transformers
  fix(scorer): cap final score at 100 when bonuses exceed limit
  test(extractor): add alias resolution test cases
  refactor(worker): extract job processing into separate class
```

## 15.9 Dependency Rules

1. Domain layer: NO external dependencies (only stdlib)
2. Application layer: May use structlog for logging
3. Infrastructure layer: May use boto3, psycopg2, openai, etc.
4. KHÔNG import infrastructure từ domain
5. KHÔNG circular imports

## 15.10 Configuration Rules

1. ALL config qua environment variables
2. Sử dụng pydantic-settings cho validation
3. KHÔNG hardcode values (use constants.py)
4. Secrets CHỈQUA env vars, KHÔNG commit vào code
5. Mỗi env var có sensible default cho development
