# 10. Thiết Kế AI Recommendation (AI Analysis Design)

## 10.1 Tổng Quan AI Integration

```
┌─────────────────────────────────────────────────────────┐
│                 AI ANALYSIS PIPELINE                      │
│                                                          │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │ Context  │───▶│ Prompt       │───▶│ OpenAI API   │  │
│  │ Builder  │    │ Engineering  │    │ (GPT-4o)     │  │
│  └──────────┘    └──────────────┘    └──────┬───────┘  │
│                                             │           │
│                                             ▼           │
│                                      ┌──────────────┐  │
│                                      │ Response     │  │
│                                      │ Parser &     │  │
│                                      │ Validator    │  │
│                                      └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 10.2 OpenAI Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Model | gpt-4o | Best quality/speed ratio |
| Temperature | 0.3 | Low creativity, high consistency |
| Max Tokens | 2000 | Sufficient for structured analysis |
| Top P | 0.9 | Slightly constrained sampling |
| Timeout | 30s | Prevent hanging |
| Retry | 2 times | Handle transient API failures |

## 10.3 Prompt Engineering Strategy

### 10.3.1 System Prompt

```text
You are an expert HR analyst and career advisor specializing in technical recruitment.
Your task is to analyze the fit between a candidate's resume and a job description.

You must respond ONLY in valid JSON format with the exact structure specified.
Do not include any text outside the JSON object.
Be specific, actionable, and constructive in your analysis.
Base your analysis strictly on the provided resume text and job description.
```

### 10.3.2 User Prompt Template

```text
Analyze the following resume against the job description.

## Resume Text
{resume_text}

## Job Description
{jd_text}

## Matching Results (Pre-computed)
- Overall Score: {overall_score}/100
- Matched Skills: {matched_skills_list}
- Missing Skills: {missing_skills_list}
- Match Rate: {match_rate}%

## Instructions
Provide a comprehensive analysis in the following JSON format:

{
  "strengths": [
    "Specific strength 1 with evidence from resume",
    "Specific strength 2 with evidence from resume",
    "Specific strength 3 with evidence from resume"
  ],
  "weaknesses": [
    "Specific gap 1 with context",
    "Specific gap 2 with context",
    "Specific gap 3 with context"
  ],
  "interview_questions": [
    {
      "question": "The interview question text",
      "category": "technical|behavioral|situational",
      "difficulty": "easy|medium|hard",
      "rationale": "Why this question is relevant based on the analysis"
    }
  ],
  "recommendations": [
    "Specific, actionable recommendation 1",
    "Specific, actionable recommendation 2",
    "Specific, actionable recommendation 3"
  ],
  "overall_assessment": "2-3 sentence summary of candidate fit",
  "fit_level": "strong_fit|good_fit|moderate_fit|weak_fit|no_fit"
}

Requirements:
- Provide exactly 3-5 strengths
- Provide exactly 3-5 weaknesses
- Provide exactly 5-8 interview questions (mix of technical, behavioral, situational)
- Provide exactly 3-5 recommendations
- fit_level must align with the overall score provided
- All analysis must reference specific content from the resume or JD
```

### 10.3.3 Prompt Context Building

```python
def build_prompt_context(
    resume_text: str,
    jd_text: str,
    match_result: MatchResult,
    score: ScoreResult
) -> str:
    # Truncate texts to fit token budget
    max_resume_chars = 3000
    max_jd_chars = 2000

    truncated_resume = resume_text[:max_resume_chars]
    truncated_jd = jd_text[:max_jd_chars]

    matched_list = ", ".join(m.jd_skill for m in match_result.matched_skills)
    missing_list = ", ".join(match_result.missing_skills)

    return PROMPT_TEMPLATE.format(
        resume_text=truncated_resume,
        jd_text=truncated_jd,
        overall_score=score.overall_score,
        matched_skills_list=matched_list,
        missing_skills_list=missing_list,
        match_rate=round(match_result.match_rate * 100, 1)
    )
```

## 10.4 Response Parsing & Validation

### 10.4.1 Expected Response Schema

```python
AI_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["strengths", "weaknesses", "interview_questions",
                 "recommendations", "overall_assessment", "fit_level"],
    "properties": {
        "strengths": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 5
        },
        "weaknesses": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 5
        },
        "interview_questions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["question", "category", "difficulty", "rationale"],
                "properties": {
                    "question": {"type": "string"},
                    "category": {"enum": ["technical", "behavioral", "situational"]},
                    "difficulty": {"enum": ["easy", "medium", "hard"]},
                    "rationale": {"type": "string"}
                }
            },
            "minItems": 5,
            "maxItems": 8
        },
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 5
        },
        "overall_assessment": {"type": "string"},
        "fit_level": {
            "enum": ["strong_fit", "good_fit", "moderate_fit", "weak_fit", "no_fit"]
        }
    }
}
```

### 10.4.2 Response Parser

```python
def parse_ai_response(raw_response: str) -> AIAnalysis:
    # Step 1: Extract JSON from response
    json_str = extract_json(raw_response)

    # Step 2: Parse JSON
    data = json.loads(json_str)

    # Step 3: Validate against schema
    validate(data, AI_RESPONSE_SCHEMA)

    # Step 4: Map to domain object
    return AIAnalysis(
        strengths=data["strengths"],
        weaknesses=data["weaknesses"],
        interview_questions=[
            InterviewQuestion(**q) for q in data["interview_questions"]
        ],
        recommendations=data["recommendations"],
        overall_assessment=data["overall_assessment"],
        fit_level=FitLevel(data["fit_level"])
    )
```

### 10.4.3 Fallback Strategy

```
IF response parsing fails:
    1. Retry with simplified prompt (1 retry)
    2. If still fails: return partial analysis with available data
    3. Set ai_analysis.partial = True
    4. Log warning (not error - AI is enhancement, not critical path)

IF OpenAI API unavailable:
    1. Skip AI analysis entirely
    2. Set ai_analysis = None in report
    3. Job still completes successfully (score + matching still valid)
```

## 10.5 Token Budget Management

```
Model: GPT-4o
Context Window: 128K tokens
Target Usage per Request: < 6000 tokens total

Budget Breakdown:
  System Prompt:    ~200 tokens
  Resume Text:      ~1500 tokens (3000 chars ≈ 750 words)
  JD Text:          ~1000 tokens (2000 chars ≈ 500 words)
  Matching Context: ~200 tokens
  Instructions:     ~400 tokens
  ─────────────────────────────
  Input Total:      ~3300 tokens
  Output (max):     ~2000 tokens
  ─────────────────────────────
  Total:            ~5300 tokens per request

Cost Estimate (GPT-4o pricing):
  Input:  $2.50 / 1M tokens → $0.00825 per request
  Output: $10.00 / 1M tokens → $0.02000 per request
  Total:  ~$0.029 per resume analysis
```

## 10.6 Rate Limiting & Circuit Breaker

```
┌─────────────────────────────────────────┐
│          CIRCUIT BREAKER                 │
├─────────────────────────────────────────┤
│ States: CLOSED → OPEN → HALF_OPEN      │
│                                          │
│ CLOSED (normal):                        │
│   - All requests pass through           │
│   - Track failure count                 │
│                                          │
│ OPEN (after 5 consecutive failures):    │
│   - All requests immediately fail       │
│   - Return None for AI analysis         │
│   - Wait 60 seconds                     │
│                                          │
│ HALF_OPEN (after wait):                 │
│   - Allow 1 test request                │
│   - If success → CLOSED                 │
│   - If fail → OPEN (reset timer)        │
└─────────────────────────────────────────┘

Rate Limiting:
  - Max 50 requests/minute to OpenAI
  - Token bucket algorithm
  - Configurable via settings
```

## 10.7 AI Analysis Data Model

```python
@dataclass
class InterviewQuestion:
    question: str
    category: str        # technical, behavioral, situational
    difficulty: str      # easy, medium, hard
    rationale: str

@dataclass
class AIAnalysis:
    strengths: List[str]
    weaknesses: List[str]
    interview_questions: List[InterviewQuestion]
    recommendations: List[str]
    overall_assessment: str
    fit_level: FitLevel
    model: str = "gpt-4o"
    partial: bool = False
    tokens_used: int = 0
```

## 10.8 Security Considerations

1. **Prompt Injection Prevention**: Resume text sanitized before injection into prompt
2. **PII Handling**: AI response không được chứa PII từ resume (enforce via system prompt)
3. **API Key**: Loaded from environment, never logged
4. **Response Filtering**: Strip any unexpected fields from AI response
5. **Token Limit**: Hard cap prevents runaway costs
