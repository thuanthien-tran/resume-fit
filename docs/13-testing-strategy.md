# 13. Thiết Kế Testing (Testing Strategy)

## 13.1 Testing Pyramid

```
          ┌───────────┐
          │   E2E     │  2-3 tests (full pipeline)
          │  Tests    │
         ┌┴───────────┴┐
         │ Integration  │  15-20 tests (AWS mocks, DB)
         │   Tests      │
        ┌┴──────────────┴┐
        │   Unit Tests    │  50-70 tests (logic, algorithms)
        └─────────────────┘
```

## 13.2 Testing Stack

| Tool | Purpose |
|------|---------|
| pytest | Test framework |
| pytest-cov | Coverage reporting |
| moto | AWS service mocking (SQS, S3) |
| pytest-mock | General mocking |
| factory-boy | Test data factories |
| testcontainers | PostgreSQL container for integration tests |
| freezegun | Time mocking |

## 13.3 Unit Tests

### 13.3.1 Text Cleaner Tests
```python
# tests/unit/test_text_cleaner.py
class TestTextCleaner:
    def test_normalize_whitespace(self):
        """Multiple spaces/tabs collapsed to single space."""

    def test_remove_urls(self):
        """HTTP/HTTPS URLs removed from text."""

    def test_remove_emails(self):
        """Email addresses removed from text."""

    def test_remove_special_characters(self):
        """Special chars removed but keeps . + #"""

    def test_preserve_skill_relevant_chars(self):
        """C++, C#, .NET preserved correctly."""

    def test_empty_input(self):
        """Empty string returns empty string."""

    def test_unicode_normalization(self):
        """Unicode characters normalized to ASCII where possible."""
```

### 13.3.2 Skill Extractor Tests
```python
# tests/unit/test_skill_extractor.py
class TestSkillExtractor:
    def test_extract_programming_languages(self):
        """Detect Python, Java, JavaScript etc from text."""

    def test_extract_frameworks(self):
        """Detect React, Django, Spring etc from text."""

    def test_alias_resolution(self):
        """'JS' maps to 'JavaScript', 'K8s' maps to 'Kubernetes'."""

    def test_case_insensitive(self):
        """'python' and 'PYTHON' both detected as 'Python'."""

    def test_no_false_positives(self):
        """'java' in 'javascript' not extracted as separate skill."""

    def test_deduplication(self):
        """Same skill mentioned twice returns only once."""

    def test_category_assignment(self):
        """Each skill assigned correct category."""

    def test_empty_text(self):
        """No skills extracted from empty text."""

    def test_skill_boundary_detection(self):
        """'Go' detected only as standalone word, not in 'Google'."""
```

### 13.3.3 Exact Matcher Tests
```python
# tests/unit/test_exact_matcher.py
class TestExactMatcher:
    def test_exact_match_found(self):
        """'Python' matches 'Python' with confidence 1.0."""

    def test_case_insensitive_match(self):
        """'python' matches 'Python'."""

    def test_no_match(self):
        """'Python' does not match 'Java'."""

    def test_returns_remaining(self):
        """Unmatched skills returned as remaining."""

    def test_one_to_one_matching(self):
        """Each JD skill can only be matched once."""
```

### 13.3.4 Fuzzy Matcher Tests
```python
# tests/unit/test_fuzzy_matcher.py
class TestFuzzyMatcher:
    def test_abbreviation_match(self):
        """'PostgreSQL' fuzzy matches 'Postgres' above threshold."""

    def test_below_threshold_rejected(self):
        """'Python' does not fuzzy match 'Java' (score < 0.80)."""

    def test_word_order_invariant(self):
        """'React JS' matches 'JS React'."""

    def test_threshold_boundary(self):
        """Score exactly at threshold is accepted."""

    def test_best_match_selected(self):
        """When multiple candidates, highest score wins."""
```

### 13.3.5 Semantic Matcher Tests
```python
# tests/unit/test_semantic_matcher.py
class TestSemanticMatcher:
    def test_synonym_match(self):
        """'Machine Learning' matches 'ML Engineering'."""

    def test_related_concepts(self):
        """'CI/CD' matches 'Continuous Integration'."""

    def test_unrelated_rejected(self):
        """'Python' does not semantically match 'Marketing'."""

    def test_empty_input(self):
        """Empty lists return empty matches."""

    def test_greedy_assignment(self):
        """Highest similarity pairs matched first."""
```

### 13.3.6 Score Calculator Tests
```python
# tests/unit/test_score_calculator.py
class TestScoreCalculator:
    def test_perfect_match_score(self):
        """All skills matched gives technical_score = 100."""

    def test_no_match_score(self):
        """No skills matched gives technical_score = 0."""

    def test_weighted_calculation(self):
        """Final score = sum of weighted category scores."""

    def test_bonus_applied(self):
        """Certifications add bonus points."""

    def test_score_capped_at_100(self):
        """Score never exceeds 100 even with bonuses."""

    def test_fit_level_classification(self):
        """Score 85+ = strong_fit, 70-84 = good_fit etc."""

    def test_default_scores_when_no_jd_data(self):
        """Neutral defaults used when JD lacks certain data."""
```

### 13.3.7 Prompt Builder Tests
```python
# tests/unit/test_prompt_builder.py
class TestPromptBuilder:
    def test_builds_valid_prompt(self):
        """Prompt contains resume text, JD text, and matching data."""

    def test_text_truncation(self):
        """Long texts truncated to fit token budget."""

    def test_special_chars_escaped(self):
        """Prompt injection characters sanitized."""

    def test_all_placeholders_filled(self):
        """No unfilled template placeholders in output."""
```

### 13.3.8 Report Builder Tests
```python
# tests/unit/test_report_builder.py
class TestReportBuilder:
    def test_builds_complete_report(self):
        """Report contains all required sections."""

    def test_report_serializable(self):
        """Report can be serialized to valid JSON."""

    def test_handles_missing_ai_analysis(self):
        """Report valid even without AI analysis."""
```

### 13.3.9 Message Handler Tests
```python
# tests/unit/test_message_handler.py
class TestMessageHandler:
    def test_valid_message_parsed(self):
        """Valid SQS message body parsed to JobPayload."""

    def test_invalid_json_rejected(self):
        """Non-JSON body raises MessageParseError."""

    def test_missing_required_fields(self):
        """Missing job_id raises MessageValidationError."""

    def test_invalid_uuid_rejected(self):
        """Non-UUID job_id raises MessageValidationError."""
```

## 13.4 Integration Tests

### 13.4.1 SQS Consumer (using moto)
```python
# tests/integration/test_sqs_consumer.py
class TestSQSConsumer:
    @mock_aws
    def test_poll_receives_message(self):
        """Consumer receives message from mocked SQS queue."""

    @mock_aws
    def test_acknowledge_deletes_message(self):
        """Acknowledged message removed from queue."""

    @mock_aws
    def test_empty_queue_returns_none(self):
        """Poll on empty queue returns None after wait."""

    @mock_aws
    def test_visibility_timeout_respected(self):
        """Message not visible to other consumers during processing."""
```

### 13.4.2 S3 Client (using moto)
```python
# tests/integration/test_s3_client.py
class TestS3Client:
    @mock_aws
    def test_download_existing_file(self):
        """Download returns file bytes for existing key."""

    @mock_aws
    def test_download_nonexistent_file(self):
        """Download raises FileNotFoundError for missing key."""

    @mock_aws
    def test_upload_file(self):
        """Upload stores file and returns success."""

    @mock_aws
    def test_large_file_download(self):
        """Files > 10MB download correctly."""
```

### 13.4.3 Job Repository (using testcontainers)
```python
# tests/integration/test_job_repository.py
class TestJobRepository:
    def test_get_by_id(self, pg_container):
        """Retrieve job by UUID."""

    def test_update_status(self, pg_container):
        """Status update persists correctly."""

    def test_set_worker_id(self, pg_container):
        """Worker ID assigned to job."""

    def test_nonexistent_job(self, pg_container):
        """None returned for unknown UUID."""
```

### 13.4.4 Result Repository
```python
# tests/integration/test_result_repository.py
class TestResultRepository:
    def test_create_result(self, pg_container):
        """Insert matching result with all fields."""

    def test_get_by_job_id(self, pg_container):
        """Retrieve result by job_id."""

    def test_duplicate_job_id_rejected(self, pg_container):
        """UNIQUE constraint on job_id enforced."""

    def test_jsonb_fields_stored(self, pg_container):
        """JSONB fields (matched_skills, ai_analysis) stored and retrieved."""
```

### 13.4.5 PDF Parser
```python
# tests/integration/test_pdf_parser.py
class TestPDFParser:
    def test_parse_simple_pdf(self):
        """Extract text from single-page PDF."""

    def test_parse_multipage_pdf(self):
        """Extract text from multi-page PDF."""

    def test_parse_pdf_with_tables(self):
        """Tables parsed as readable text."""

    def test_corrupted_pdf_raises(self):
        """CorruptedFileError for invalid PDF bytes."""
```

### 13.4.6 OpenAI Client (mocked)
```python
# tests/integration/test_openai_client.py
class TestOpenAIClient:
    @patch("openai.OpenAI")
    def test_successful_analysis(self, mock_openai):
        """Valid response parsed to AIAnalysis."""

    @patch("openai.OpenAI")
    def test_timeout_handling(self, mock_openai):
        """Timeout raises AITimeoutError."""

    @patch("openai.OpenAI")
    def test_rate_limit_handling(self, mock_openai):
        """429 response raises AIRateLimitError."""

    @patch("openai.OpenAI")
    def test_invalid_response_handling(self, mock_openai):
        """Non-JSON response raises AIResponseParseError."""
```

## 13.5 End-to-End Tests

### 13.5.1 Full Pipeline Test
```python
# tests/e2e/test_full_pipeline.py
class TestFullPipeline:
    @mock_aws
    def test_complete_processing_flow(self, pg_container):
        """
        Full flow: SQS message → download → parse → extract →
        match → score → AI → report → DB save.
        Verifies final result in PostgreSQL matches expected output.
        """

    @mock_aws
    def test_processing_without_ai(self, pg_container):
        """
        Full flow with AI disabled.
        Verifies job completes successfully without AI analysis.
        """

    @mock_aws
    def test_docx_resume_processing(self, pg_container):
        """
        Full flow with DOCX resume instead of PDF.
        """
```

### 13.5.2 Error Scenario Tests
```python
# tests/e2e/test_error_scenarios.py
class TestErrorScenarios:
    @mock_aws
    def test_corrupted_file_fails_gracefully(self, pg_container):
        """Corrupted PDF marks job as failed with clear error."""

    @mock_aws
    def test_retry_on_transient_error(self, pg_container):
        """Transient S3 error triggers retry and succeeds."""

    @mock_aws
    def test_max_retries_sends_to_dlq(self, pg_container):
        """After max retries, job moved to DLQ."""

    @mock_aws
    def test_graceful_shutdown_during_processing(self, pg_container):
        """SIGTERM during job releases message back to queue."""
```

## 13.6 Test Fixtures

```python
# tests/conftest.py
@pytest.fixture
def sample_resume_text():
    return """John Doe - Software Engineer
    5 years experience in Python, AWS, Docker.
    Built REST APIs with Django and FastAPI.
    Bachelor of Science in Computer Science."""

@pytest.fixture
def sample_jd_text():
    return """Senior Python Developer
    Required: Python, AWS, Kubernetes, PostgreSQL, REST API
    Preferred: Docker, CI/CD, Terraform
    3+ years experience required.
    Bachelor's degree in CS or related field."""

@pytest.fixture
def sample_sqs_message():
    return {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "resume_s3_key": "uploads/resumes/test.pdf",
        "jd_s3_key": "uploads/jds/test.pdf",
        "user_id": "660e8400-e29b-41d4-a716-446655440000",
        "created_at": "2024-01-15T10:00:00Z",
        "priority": "normal",
        "options": {"include_ai_analysis": True, "matching_threshold": 0.6}
    }

@pytest.fixture
def skill_dictionary():
    return SkillDictionary.from_file("app/extractor/data/skills.json")
```

## 13.7 Coverage Requirements

| Layer | Minimum Coverage |
|-------|-----------------|
| Domain (models, enums) | 95% |
| Application (services) | 85% |
| Infrastructure (repos, clients) | 75% |
| Overall | 80% |

## 13.8 Test Configuration

```ini
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=app --cov-report=html --cov-report=term-missing -v"
markers = [
    "unit: Unit tests (no external dependencies)",
    "integration: Integration tests (mocked AWS, real DB)",
    "e2e: End-to-end tests (full pipeline)",
    "slow: Tests that take > 5 seconds",
]

[tool.coverage.run]
source = ["app"]
omit = ["tests/*", "app/config/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

## 13.9 CI Test Pipeline

```
Stage 1 (Fast): Unit Tests
  - No external deps
  - Run in < 30 seconds
  - Gate: must pass before Stage 2

Stage 2 (Medium): Integration Tests
  - moto for AWS
  - testcontainers for PostgreSQL
  - Run in < 2 minutes

Stage 3 (Slow): E2E Tests
  - Full pipeline with fixtures
  - Run in < 5 minutes
  - Gate: must pass before deploy
```
