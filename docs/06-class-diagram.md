# 6. Thiết Kế Class Diagram

## 6.1 Domain Layer Classes

```
┌─────────────────────────────────────────────────────┐
│                    DOMAIN LAYER                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─────────────────────┐   ┌──────────────────────┐ │
│  │    ProcessingJob     │   │       Resume         │ │
│  ├─────────────────────┤   ├──────────────────────┤ │
│  │ - id: UUID          │   │ - id: UUID           │ │
│  │ - user_id: UUID     │   │ - user_id: UUID      │ │
│  │ - resume_id: UUID   │   │ - filename: str      │ │
│  │ - jd_id: UUID       │   │ - s3_key: str        │ │
│  │ - status: JobStatus │   │ - file_type: FileType│ │
│  │ - priority: Priority│   │ - raw_text: str|None │ │
│  │ - retry_count: int  │   │ - skills: List[Skill]│ │
│  │ - error_message: str│   ├──────────────────────┤ │
│  │ - worker_id: str    │   │ + has_text() -> bool  │ │
│  │ - started_at: dt    │   └──────────────────────┘ │
│  │ - completed_at: dt  │                            │
│  ├─────────────────────┤   ┌──────────────────────┐ │
│  │ + mark_processing() │   │   JobDescription     │ │
│  │ + mark_completed()  │   ├──────────────────────┤ │
│  │ + mark_failed()     │   │ - id: UUID           │ │
│  │ + can_retry() -> bool│  │ - title: str         │ │
│  │ + increment_retry() │   │ - company: str|None  │ │
│  └─────────────────────┘   │ - s3_key: str        │ │
│                             │ - file_type: FileType│ │
│  ┌─────────────────────┐   │ - raw_text: str|None │ │
│  │       Skill         │   │ - required_skills:   │ │
│  ├─────────────────────┤   │     List[Skill]      │ │
│  │ - name: str         │   │ - preferred_skills:  │ │
│  │ - category: Category│   │     List[Skill]      │ │
│  │ - aliases: List[str]│   │ - experience_years:  │ │
│  │ - level: SkillLevel │   │     int|None         │ │
│  ├─────────────────────┤   ├──────────────────────┤ │
│  │ + normalized() -> str│  │ + has_text() -> bool  │ │
│  │ + matches(other)    │   │ + all_skills() ->    │ │
│  │     -> bool         │   │     List[Skill]      │ │
│  └─────────────────────┘   └──────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │              MatchResult                     │    │
│  ├─────────────────────────────────────────────┤    │
│  │ - matched_skills: List[SkillMatch]          │    │
│  │ - missing_skills: List[MissingSkill]        │    │
│  │ - fuzzy_matches: List[FuzzyMatch]           │    │
│  │ - semantic_matches: List[SemanticMatch]     │    │
│  ├─────────────────────────────────────────────┤    │
│  │ + match_rate() -> float                     │    │
│  │ + matched_count() -> int                    │    │
│  │ + missing_count() -> int                    │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │              ScoreResult                     │    │
│  ├─────────────────────────────────────────────┤    │
│  │ - overall_score: float                      │    │
│  │ - technical_score: float                    │    │
│  │ - soft_skills_score: float                  │    │
│  │ - experience_score: float                   │    │
│  │ - education_score: float                    │    │
│  │ - breakdown: Dict[str, float]               │    │
│  ├─────────────────────────────────────────────┤    │
│  │ + is_strong_match() -> bool                 │    │
│  │ + category_scores() -> Dict                 │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  ┌─────────────────────────────────────────────┐    │
│  │              Report                          │    │
│  ├─────────────────────────────────────────────┤    │
│  │ - job_id: UUID                              │    │
│  │ - score: ScoreResult                        │    │
│  │ - match_result: MatchResult                 │    │
│  │ - ai_analysis: AIAnalysis|None              │    │
│  │ - processing_time_ms: int                   │    │
│  │ - created_at: datetime                      │    │
│  ├─────────────────────────────────────────────┤    │
│  │ + to_dict() -> Dict                         │    │
│  │ + summary() -> str                          │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## 6.2 Application Layer Classes (Services / Use Cases)

```
┌───────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              DocumentService                          │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - s3_client: S3ClientProtocol                        │     │
│  │ - parser_factory: ParserFactory                      │     │
│  │ - text_cleaner: TextCleaner                          │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + download_and_parse(s3_key, file_type)              │     │
│  │     -> DocumentContent                               │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              ExtractionService                        │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - skill_extractor: SkillExtractor                    │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + extract_resume_skills(text) -> List[Skill]         │     │
│  │ + extract_jd_skills(text) -> ExtractedJDSkills       │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              MatchingService                          │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - hybrid_matcher: HybridMatcher                      │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + match(resume_skills, jd_skills) -> MatchResult     │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              ScoringService                           │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - calculator: ScoreCalculator                        │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + calculate(match_result, resume, jd) -> ScoreResult │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              AnalysisService                          │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - ai_client: OpenAIClientProtocol                    │     │
│  │ - prompt_builder: PromptBuilder                      │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + analyze(resume_text, jd_text, match_result, score) │     │
│  │     -> AIAnalysis                                    │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              ReportService                            │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - report_builder: ReportBuilder                      │     │
│  │ - report_uploader: ReportUploader                    │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + generate(job_id, score, match, ai_analysis)        │     │
│  │     -> Report                                        │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

## 6.3 Interface Adapters (Repositories & Consumers)

```
┌───────────────────────────────────────────────────────────────┐
│                 INTERFACE ADAPTERS LAYER                        │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  «interface»                    «interface»                    │
│  ┌─────────────────────┐       ┌────────────────────────┐    │
│  │ JobRepositoryProto  │       │ ResultRepositoryProto  │    │
│  ├─────────────────────┤       ├────────────────────────┤    │
│  │ + get_by_id(id)     │       │ + create(result)       │    │
│  │ + update_status()   │       │ + get_by_job_id(id)    │    │
│  │ + set_worker_id()   │       └────────────────────────┘    │
│  └─────────────────────┘                                      │
│          △                              △                     │
│          │                              │                     │
│  ┌───────┴──────────────┐      ┌───────┴────────────────┐   │
│  │ PostgresJobRepository│      │PostgresResultRepository│   │
│  ├──────────────────────┤      ├────────────────────────┤   │
│  │ - db_pool: Pool      │      │ - db_pool: Pool        │   │
│  ├──────────────────────┤      ├────────────────────────┤   │
│  │ + get_by_id(id)      │      │ + create(result)       │   │
│  │ + update_status()    │      │ + get_by_job_id(id)    │   │
│  │ + set_worker_id()    │      └────────────────────────┘   │
│  └──────────────────────┘                                     │
│                                                                │
│  «interface»                    «interface»                    │
│  ┌─────────────────────┐       ┌────────────────────────┐    │
│  │ S3ClientProtocol    │       │ QueueConsumerProtocol  │    │
│  ├─────────────────────┤       ├────────────────────────┤    │
│  │ + download(key)     │       │ + poll() -> Message    │    │
│  │ + upload(key, data) │       │ + acknowledge(msg)     │    │
│  └─────────────────────┘       │ + reject(msg)          │    │
│          △                     └────────────────────────┘    │
│          │                              △                     │
│  ┌───────┴──────────────┐      ┌───────┴────────────────┐   │
│  │    S3Client          │      │     SQSConsumer        │   │
│  ├──────────────────────┤      ├────────────────────────┤   │
│  │ - boto3_client       │      │ - boto3_client         │   │
│  │ - bucket_name: str   │      │ - queue_url: str       │   │
│  ├──────────────────────┤      │ - wait_time: int       │   │
│  │ + download(key)      │      ├────────────────────────┤   │
│  │ + upload(key, data)  │      │ + poll() -> Message    │   │
│  └──────────────────────┘      │ + acknowledge(msg)     │   │
│                                │ + reject(msg)          │   │
│                                └────────────────────────┘   │
│                                                                │
│  «interface»                                                  │
│  ┌─────────────────────────┐                                  │
│  │ OpenAIClientProtocol    │                                  │
│  ├─────────────────────────┤                                  │
│  │ + analyze(prompt) -> str│                                  │
│  └─────────────────────────┘                                  │
│          △                                                    │
│          │                                                    │
│  ┌───────┴─────────────────┐                                  │
│  │    OpenAIClient         │                                  │
│  ├─────────────────────────┤                                  │
│  │ - client: OpenAI        │                                  │
│  │ - model: str            │                                  │
│  │ - max_tokens: int       │                                  │
│  ├─────────────────────────┤                                  │
│  │ + analyze(prompt) -> str│                                  │
│  └─────────────────────────┘                                  │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

## 6.4 Worker & Infrastructure Classes

```
┌───────────────────────────────────────────────────────────────┐
│                    WORKER INFRASTRUCTURE                        │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              WorkerManager                            │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - worker_count: int                                  │     │
│  │ - executor: ThreadPoolExecutor                       │     │
│  │ - shutdown_event: Event                              │     │
│  │ - job_processor: JobProcessor                        │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + start() -> None                                    │     │
│  │ + stop() -> None                                     │     │
│  │ + _worker_loop() -> None                             │     │
│  │ + _handle_signal(sig) -> None                        │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              JobProcessor                             │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - document_service: DocumentService                  │     │
│  │ - extraction_service: ExtractionService              │     │
│  │ - matching_service: MatchingService                  │     │
│  │ - scoring_service: ScoringService                    │     │
│  │ - analysis_service: AnalysisService                  │     │
│  │ - report_service: ReportService                      │     │
│  │ - job_repo: JobRepositoryProtocol                    │     │
│  │ - result_repo: ResultRepositoryProtocol              │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + process(payload: JobPayload) -> Report             │     │
│  │ - _update_job_status(job_id, status) -> None         │     │
│  │ - _handle_error(job_id, error) -> None               │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              ParserFactory                            │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - parsers: Dict[FileType, BaseParser]                │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + get_parser(file_type) -> BaseParser                │     │
│  │ + register(file_type, parser) -> None                │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              TextCleaner                              │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + clean(text: str) -> str                            │     │
│  │ + normalize_whitespace(text) -> str                  │     │
│  │ + remove_special_chars(text) -> str                  │     │
│  │ + remove_urls(text) -> str                           │     │
│  │ + remove_emails(text) -> str                         │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              SkillExtractor                           │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - dictionary: SkillDictionary                        │     │
│  │ - alias_mapper: AliasMapper                          │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + extract(text: str) -> List[Skill]                  │     │
│  │ - _find_skills(text, category) -> List[Skill]        │     │
│  │ - _resolve_aliases(raw_skills) -> List[Skill]        │     │
│  │ - _deduplicate(skills) -> List[Skill]                │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              HybridMatcher                            │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - exact_matcher: ExactMatcher                        │     │
│  │ - fuzzy_matcher: FuzzyMatcher                        │     │
│  │ - semantic_matcher: SemanticMatcher                  │     │
│  │ - fuzzy_threshold: float (default 0.80)              │     │
│  │ - semantic_threshold: float (default 0.75)           │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + match(resume_skills, jd_skills) -> MatchResult     │     │
│  │ - _merge_results(exact, fuzzy, semantic)             │     │
│  │     -> MatchResult                                   │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐     │
│  │              ScoreCalculator                          │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ - weights: WeightConfig                              │     │
│  │ - bonus_calculator: BonusCalculator                  │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ + calculate(match_result, resume, jd) -> ScoreResult │     │
│  │ - _technical_score(match) -> float                   │     │
│  │ - _soft_skills_score(match) -> float                 │     │
│  │ - _experience_score(resume, jd) -> float             │     │
│  │ - _education_score(resume, jd) -> float              │     │
│  │ - _apply_bonuses(base_score) -> float                │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                                │
└───────────────────────────────────────────────────────────────┘
```

## 6.5 Enums & Value Objects

```python
class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"

class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"

class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"

class SkillCategory(str, Enum):
    PROGRAMMING = "programming"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    DEVOPS = "devops"
    SOFT_SKILL = "soft_skill"
    TOOL = "tool"
    OTHER = "other"

class MatchType(str, Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"

class FitLevel(str, Enum):
    STRONG_FIT = "strong_fit"
    GOOD_FIT = "good_fit"
    MODERATE_FIT = "moderate_fit"
    WEAK_FIT = "weak_fit"
    NO_FIT = "no_fit"
```
