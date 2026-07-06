# 8. Thiết Kế Thuật Toán Matching (Matching Algorithm Design)

## 8.1 Tổng Quan Matching Pipeline

```
Resume Skills ──┐                          ┌── Matched Skills
                │                          │
                ▼                          ▼
         ┌─────────────────────────────────────┐
         │         HYBRID MATCHER               │
         │                                      │
         │  ┌───────────┐  ┌──────────────┐   │
         │  │   EXACT    │  │    FUZZY     │   │
         │  │  MATCHING  │  │  MATCHING    │   │
         │  │            │  │  (RapidFuzz) │   │
         │  └─────┬──────┘  └──────┬───────┘   │
         │        │                │            │
         │        ▼                ▼            │
         │  ┌──────────────────────────────┐   │
         │  │      SEMANTIC MATCHING       │   │
         │  │  (Sentence Transformers)     │   │
         │  └──────────────┬───────────────┘   │
         │                 │                    │
         │                 ▼                    │
         │  ┌──────────────────────────────┐   │
         │  │     RESULT MERGER            │   │
         │  │  (Dedup + Rank + Threshold)  │   │
         │  └──────────────────────────────┘   │
         └─────────────────────────────────────┘
                           │
                           ▼
                    MatchResult
JD Skills ─────────┘
```

## 8.2 Stage 1: Exact Matching

### Algorithm
```
Input:  resume_skills: List[str], jd_skills: List[str]
Output: exact_matches: List[SkillMatch], remaining_resume: List[str], remaining_jd: List[str]

FUNCTION exact_match(resume_skills, jd_skills):
    matched = []
    remaining_resume = []
    remaining_jd = list(jd_skills)

    FOR skill IN resume_skills:
        normalized = normalize(skill)  # lowercase, strip whitespace
        found = False

        FOR jd_skill IN remaining_jd:
            IF normalize(jd_skill) == normalized:
                matched.append(SkillMatch(
                    resume_skill=skill,
                    jd_skill=jd_skill,
                    match_type=EXACT,
                    confidence=1.0
                ))
                remaining_jd.remove(jd_skill)
                found = True
                BREAK

        IF NOT found:
            remaining_resume.append(skill)

    RETURN matched, remaining_resume, remaining_jd
```

### Normalization Rules
1. Convert to lowercase
2. Strip leading/trailing whitespace
3. Remove special characters (except `.`, `+`, `#`)
4. Collapse multiple spaces to single space
5. Apply alias resolution BEFORE matching

## 8.3 Stage 2: Fuzzy Matching (RapidFuzz)

### Algorithm
```
Input:  remaining_resume: List[str], remaining_jd: List[str], threshold: float = 0.80
Output: fuzzy_matches: List[FuzzyMatch], remaining_resume: List[str], remaining_jd: List[str]

FUNCTION fuzzy_match(remaining_resume, remaining_jd, threshold):
    matches = []
    used_jd = set()
    still_remaining_resume = []

    FOR resume_skill IN remaining_resume:
        best_score = 0.0
        best_jd_skill = None

        FOR idx, jd_skill IN enumerate(remaining_jd):
            IF idx IN used_jd:
                CONTINUE

            # RapidFuzz token_sort_ratio handles word order differences
            score = rapidfuzz.fuzz.token_sort_ratio(
                resume_skill, jd_skill
            ) / 100.0

            # Also try partial_ratio for substring matches
            partial = rapidfuzz.fuzz.partial_ratio(
                resume_skill, jd_skill
            ) / 100.0

            combined = max(score, partial * 0.95)  # slight penalty for partial

            IF combined > best_score:
                best_score = combined
                best_jd_skill = (idx, jd_skill)

        IF best_score >= threshold AND best_jd_skill:
            matches.append(FuzzyMatch(
                resume_skill=resume_skill,
                jd_skill=best_jd_skill[1],
                match_type=FUZZY,
                confidence=best_score
            ))
            used_jd.add(best_jd_skill[0])
        ELSE:
            still_remaining_resume.append(resume_skill)

    still_remaining_jd = [s for i, s in enumerate(remaining_jd) if i not in used_jd]
    RETURN matches, still_remaining_resume, still_remaining_jd
```

### Fuzzy Matching Strategies
| Strategy | Function | Use Case |
|----------|----------|----------|
| `token_sort_ratio` | Sort tokens alphabetically then compare | "React JS" vs "JS React" |
| `partial_ratio` | Best partial substring match | "AWS Lambda" vs "Lambda" |
| `token_set_ratio` | Compare unique token sets | "Node.js Express" vs "Express.js Node" |

### Threshold Justification
- **0.80**: Captures abbreviations và minor spelling differences
- Examples at 0.80+:
  - "JavaScript" vs "Javascript" = 0.95
  - "React.js" vs "ReactJS" = 0.85
  - "PostgreSQL" vs "Postgres" = 0.82
- Examples below 0.80 (rejected):
  - "Python" vs "Java" = 0.40
  - "AWS" vs "Azure" = 0.33

## 8.4 Stage 3: Semantic Matching (Sentence Transformers)

### Algorithm
```
Input:  remaining_resume: List[str], remaining_jd: List[str], threshold: float = 0.75
Output: semantic_matches: List[SemanticMatch]
Model:  all-MiniLM-L6-v2 (384 dimensions, fast inference)

FUNCTION semantic_match(remaining_resume, remaining_jd, threshold):
    IF NOT remaining_resume OR NOT remaining_jd:
        RETURN []

    # Encode all skills to embeddings
    resume_embeddings = model.encode(remaining_resume)  # shape: (N, 384)
    jd_embeddings = model.encode(remaining_jd)          # shape: (M, 384)

    # Compute cosine similarity matrix
    similarity_matrix = cosine_similarity(resume_embeddings, jd_embeddings)
    # shape: (N, M)

    matches = []
    used_jd = set()

    # Greedy assignment: highest similarity first
    WHILE True:
        # Find maximum similarity in matrix (excluding used)
        max_sim = 0.0
        max_i, max_j = -1, -1

        FOR i IN range(len(remaining_resume)):
            FOR j IN range(len(remaining_jd)):
                IF j IN used_jd:
                    CONTINUE
                IF similarity_matrix[i][j] > max_sim:
                    max_sim = similarity_matrix[i][j]
                    max_i, max_j = i, j

        IF max_sim < threshold OR max_i == -1:
            BREAK

        matches.append(SemanticMatch(
            resume_skill=remaining_resume[max_i],
            jd_skill=remaining_jd[max_j],
            match_type=SEMANTIC,
            confidence=float(max_sim)
        ))
        used_jd.add(max_j)
        # Zero out row to prevent re-matching
        similarity_matrix[max_i] = 0

    RETURN matches
```

### Semantic Match Examples
| Resume Skill | JD Skill | Cosine Similarity |
|-------------|----------|-------------------|
| "Machine Learning" | "ML Engineering" | 0.87 |
| "Data Analysis" | "Business Analytics" | 0.79 |
| "REST API" | "Web Services" | 0.82 |
| "CI/CD" | "Continuous Integration" | 0.91 |
| "Agile" | "Scrum" | 0.78 |

### Model Selection Rationale
- **all-MiniLM-L6-v2**: 384-dim, ~80MB, inference 14k sentences/sec on CPU
- Balance giữa accuracy và speed cho real-time processing
- Pre-trained on 1B+ sentence pairs
- Excellent cho short text (skill names = 1-3 words)

## 8.5 Result Merging & Deduplication

```
FUNCTION merge_results(exact, fuzzy, semantic):
    all_matches = []
    seen_resume_skills = set()
    seen_jd_skills = set()

    # Priority: Exact > Fuzzy > Semantic
    FOR match IN exact + fuzzy + semantic:
        resume_key = normalize(match.resume_skill)
        jd_key = normalize(match.jd_skill)

        IF resume_key IN seen_resume_skills OR jd_key IN seen_jd_skills:
            CONTINUE

        all_matches.append(match)
        seen_resume_skills.add(resume_key)
        seen_jd_skills.add(jd_key)

    # Determine missing skills (in JD but not matched)
    all_matched_jd = {normalize(m.jd_skill) for m in all_matches}
    missing = [s for s in jd_skills if normalize(s) not in all_matched_jd]

    RETURN MatchResult(
        matched_skills=all_matches,
        missing_skills=missing,
        match_rate=len(all_matches) / len(jd_skills) if jd_skills else 0
    )
```

## 8.6 Embedding Cache Strategy

```
┌──────────────────────────────────────────────┐
│           EmbeddingCache (LRU)               │
├──────────────────────────────────────────────┤
│ - cache: Dict[str, ndarray]                  │
│ - max_size: int = 10000                      │
│ - model: SentenceTransformer                 │
├──────────────────────────────────────────────┤
│ + get_or_compute(text) -> ndarray            │
│ + batch_encode(texts) -> List[ndarray]       │
│ + clear() -> None                            │
│ + size() -> int                              │
└──────────────────────────────────────────────┘

- Common skills (top 500) pre-computed at startup
- LRU eviction khi cache full
- Thread-safe via threading.Lock
```

## 8.7 Performance Considerations

| Stage | Time Complexity | Typical Latency |
|-------|----------------|-----------------|
| Exact | O(N × M) | < 1ms |
| Fuzzy | O(N × M × L) | 5-20ms |
| Semantic | O(N + M) encode + O(N × M) similarity | 50-200ms |
| Total | - | < 250ms |

Where N = resume skills count, M = JD skills count, L = avg skill name length
