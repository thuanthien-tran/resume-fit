# 4. Thiết Kế Workflow (Workflow Design)

## 4.1 Main Processing Pipeline

```
┌─────────────┐
│  SQS Queue  │
└──────┬──────┘
       │ Poll (long polling, 20s)
       ▼
┌─────────────────┐
│ Receive Message │
└──────┬──────────┘
       │ Validate message schema
       ▼
┌─────────────────────┐
│ Parse Job Payload   │──── Invalid ────▶ [Log Error + Delete Message]
└──────┬──────────────┘
       │ Valid
       ▼
┌─────────────────────────┐
│ Update Job Status       │
│ status = 'processing'   │
│ started_at = NOW()      │
│ worker_id = hostname    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Download Files from S3  │──── S3 Error ────▶ [Retry]
│ - Resume (PDF/DOCX)     │
│ - JD (PDF/DOCX/TXT)     │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Parse Documents         │──── Parse Error ──▶ [Retry]
│ - Extract text          │
│ - Clean & normalize     │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Extract Skills          │
│ - Resume skills         │
│ - JD required skills    │
│ - JD preferred skills   │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Match Skills            │
│ - Exact matching        │
│ - Fuzzy matching        │
│ - Semantic matching     │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Score Resume            │
│ - Category scores       │
│ - Weighted total        │
│ - Bonus calculations    │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ AI Analysis (Optional)      │──── API Error ──▶ [Continue without AI]
│ - Strengths/Weaknesses      │
│ - Interview Questions       │
│ - Recommendations           │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Generate Report         │
│ - Compile all results   │
│ - Upload to S3          │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Save Results            │
│ - Insert matching_results│
│ - Update job status     │
│   status = 'completed'  │
└──────┬──────────────────┘
       │
       ▼
┌─────────────────────────┐
│ Delete SQS Message      │
│ (Acknowledge)           │
└─────────────────────────┘
```

## 4.2 Retry Workflow

```
┌──────────────────┐
│ Processing Error │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────┐
│ retry_count < max_retries?│
└──────┬───────────────────┘
       │
   ┌───┴───┐
   │       │
  YES      NO
   │       │
   ▼       ▼
┌────────┐ ┌─────────────────────────┐
│ Retry  │ │ Move to Dead Letter     │
│ - Wait │ │ - Update status='failed'│
│   exp  │ │ - Set error_message     │
│   back │ │ - Delete from main queue│
│ - Incr │ │ - Send to DLQ           │
│   count│ └─────────────────────────┘
└────────┘

Exponential Backoff:
  Attempt 1: wait 2s
  Attempt 2: wait 4s
  Attempt 3: wait 8s
  (base=2, factor=2, max_delay=30s)
```

## 4.3 Graceful Shutdown Workflow

```
┌──────────────────┐
│ SIGTERM received │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────┐
│ Set shutdown_flag = True     │
│ Stop polling new messages    │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Wait for in-flight jobs      │
│ (timeout: 60 seconds)        │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ If jobs still running:       │
│ - Release SQS messages       │
│   (visibility timeout reset) │
│ - Update job status='pending'│
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Close DB connections         │
│ Close AWS clients            │
│ Exit process                 │
└──────────────────────────────┘
```

## 4.4 Worker Lifecycle

```
                    ┌─────────────┐
                    │   STARTUP   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │ Load Config     │
                    │ Init DB Pool    │
                    │ Init AWS Clients│
                    │ Load Models     │
                    └──────┬──────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    RUNNING (Loop)      │◀──────────────────┐
              └──────┬─────────────────┘                   │
                     │                                     │
                     ▼                                     │
              ┌─────────────────┐                          │
              │ Poll SQS        │                          │
              │ (long poll 20s) │                          │
              └──────┬──────────┘                          │
                     │                                     │
              ┌──────┴──────┐                              │
              │             │                              │
         No Message    Has Message                         │
              │             │                              │
              │             ▼                              │
              │      ┌─────────────┐                       │
              │      │ Process Job │                       │
              │      └──────┬──────┘                       │
              │             │                              │
              └─────────────┴──────────────────────────────┘
                     │
                     │ (shutdown_flag = True)
                     ▼
              ┌─────────────────┐
              │    SHUTDOWN     │
              └─────────────────┘
```

## 4.5 State Machine - Job Status

```
                 ┌─────────┐
                 │ pending │ (Created by Backend)
                 └────┬────┘
                      │ Worker picks up
                      ▼
                ┌────────────┐
          ┌─────│ processing │
          │     └─────┬──────┘
          │           │
          │     ┌─────┴─────┐
          │     │           │
          │  Success     Failure
          │     │           │
          │     ▼           ▼
          │ ┌───────────┐ ┌────────┐
          │ │ completed │ │ failed │
          │ └───────────┘ └────┬───┘
          │                    │ retry_count >= max
          │                    ▼
          │              ┌─────────────┐
          └──────────────│ dead_letter │
             (timeout)   └─────────────┘
```

## 4.6 Data Flow Detail

### Step 1: Message Reception
```
Input:  SQS Message (JSON string)
Output: JobPayload dataclass
```

### Step 2: File Download
```
Input:  s3_key (string)
Output: bytes (file content in memory)
```

### Step 3: Document Parsing
```
Input:  bytes + file_type
Output: DocumentContent(raw_text, metadata)
```

### Step 4: Text Cleaning
```
Input:  raw_text (string)
Output: cleaned_text (string) - lowercase, no special chars, normalized whitespace
```

### Step 5: Skill Extraction
```
Input:  cleaned_text + skill_dictionary
Output: ExtractedSkills(skills: List[Skill], categories: Dict)
```

### Step 6: Skill Matching
```
Input:  resume_skills + jd_skills
Output: MatchResult(matched, missing, fuzzy_matches, semantic_matches)
```

### Step 7: Scoring
```
Input:  MatchResult + weights
Output: ScoreResult(overall, technical, soft_skills, experience, education)
```

### Step 8: AI Analysis
```
Input:  resume_text + jd_text + match_result + score
Output: AIAnalysis(strengths, weaknesses, questions, recommendations)
```

### Step 9: Report Generation
```
Input:  All previous outputs
Output: Report(JSON) + S3 upload
```

### Step 10: Persistence
```
Input:  Report + job_id
Output: matching_results row + updated job status
```
