# 9. Thiết Kế Thuật Toán Scoring (Scoring Algorithm Design)

## 9.1 Tổng Quan Scoring Formula

```
Final Score = Σ(Category_Score × Weight) + Bonus_Points

Where:
  Category_Score ∈ [0, 100]
  Weight ∈ [0, 1], Σ(Weights) = 1.0
  Bonus_Points ∈ [0, 10]
  Final Score capped at 100
```

## 9.2 Category Weights

| Category | Weight | Rationale |
|----------|--------|-----------|
| Technical Skills | 0.40 | Core requirement cho technical roles |
| Soft Skills | 0.15 | Quan trọng nhưng khó đo chính xác |
| Experience | 0.25 | Kinh nghiệm liên quan trực tiếp |
| Education | 0.20 | Bằng cấp & certifications |
| **Total** | **1.00** | |

Weights có thể configurable qua `WeightConfig` class.

## 9.3 Technical Skills Score

### Formula
```
Technical_Score = (matched_technical / total_required_technical) × 100

Where:
  matched_technical = count of matched skills in categories:
    [programming, framework, database, cloud, devops, tool]
  total_required_technical = count of JD required technical skills

Adjustments:
  - Exact match: weight = 1.0
  - Fuzzy match: weight = confidence_score (0.80 - 1.0)
  - Semantic match: weight = confidence_score × 0.9 (penalty for uncertainty)
```

### Weighted Technical Score Calculation
```python
def calculate_technical_score(match_result: MatchResult, jd_skills: List[Skill]) -> float:
    technical_categories = {PROGRAMMING, FRAMEWORK, DATABASE, CLOUD, DEVOPS, TOOL}

    # Filter JD skills to technical only
    required_technical = [s for s in jd_skills if s.category in technical_categories]
    if not required_technical:
        return 0.0

    weighted_matches = 0.0
    for match in match_result.matched_skills:
        if match.jd_skill_category in technical_categories:
            if match.match_type == EXACT:
                weighted_matches += 1.0
            elif match.match_type == FUZZY:
                weighted_matches += match.confidence
            elif match.match_type == SEMANTIC:
                weighted_matches += match.confidence * 0.9

    score = (weighted_matches / len(required_technical)) * 100
    return min(score, 100.0)
```

## 9.4 Soft Skills Score

### Formula
```
Soft_Skills_Score = (matched_soft / total_required_soft) × 100

Where:
  matched_soft = count of matched skills in category: [soft_skill]
  total_required_soft = count of JD required soft skills

  If no soft skills in JD:
    Soft_Skills_Score = 70.0 (neutral default)
```

### Common Soft Skills Matching
```
Dictionary includes:
  - Communication, Teamwork, Leadership, Problem-solving
  - Time Management, Adaptability, Critical Thinking
  - Collaboration, Creativity, Attention to Detail

Semantic matching especially useful here:
  "Team player" ≈ "Teamwork" (cosine: 0.82)
  "Self-motivated" ≈ "Self-starter" (cosine: 0.88)
```

## 9.5 Experience Score

### Formula
```
Experience_Score = base_score + relevance_bonus

base_score:
  IF resume_years >= jd_required_years:
      base_score = 100.0
  ELIF resume_years >= jd_required_years * 0.7:
      base_score = 70.0 + (resume_years / jd_required_years) * 30.0
  ELSE:
      base_score = (resume_years / jd_required_years) * 70.0

relevance_bonus (max +10):
  - Has relevant industry experience: +5
  - Has similar role title: +5

If JD doesn't specify years:
  Experience_Score = 75.0 (neutral default)
```

### Experience Extraction Heuristics
```
Patterns to detect years of experience from resume text:
  - "X+ years of experience"
  - "X years experience in"
  - "since YYYY" → calculate years from current date
  - Work history section: sum durations of relevant positions
```

## 9.6 Education Score

### Formula
```
Education_Score = degree_score + relevance_score

degree_score (0-60):
  PhD in relevant field:        60
  Master's in relevant field:   50
  Bachelor's in relevant field: 40
  Associate's/Diploma:          25
  No degree listed:             15

relevance_score (0-40):
  Exact field match (CS for dev role):      40
  Related field (Math for data role):       30
  Partially related (Engineering for dev):  20
  Unrelated field:                          10

If JD doesn't specify education:
  Education_Score = 70.0 (neutral default)
```

## 9.7 Bonus Points

### Certification Bonus (max +5)
```
certification_bonus = min(relevant_certs_count × 2.0, 5.0)

Relevant certifications detected by keyword matching:
  - AWS: "AWS Certified", "SAA", "SAP", "CCP"
  - Cloud: "GCP", "Azure Certified"
  - Dev: "CKAD", "CKA", "PMP", "Scrum Master"
  - Data: "TensorFlow Certified", "Databricks"
```

### Keyword Density Bonus (max +3)
```
keyword_bonus:
  IF resume contains >= 80% of JD keywords (non-skill):
      bonus = 3.0
  ELIF resume contains >= 60% of JD keywords:
      bonus = 2.0
  ELIF resume contains >= 40% of JD keywords:
      bonus = 1.0
  ELSE:
      bonus = 0.0
```

### Extra Skills Bonus (max +2)
```
extra_bonus:
  extra_relevant_skills = resume_skills NOT in JD but in same category
  IF extra_relevant_skills >= 5:
      bonus = 2.0
  ELIF extra_relevant_skills >= 3:
      bonus = 1.0
  ELSE:
      bonus = 0.0
```

## 9.8 Final Score Calculation

```python
def calculate_final_score(
    technical: float,
    soft_skills: float,
    experience: float,
    education: float,
    weights: WeightConfig,
    bonuses: BonusResult
) -> ScoreResult:

    weighted_score = (
        technical * weights.technical +      # 0.40
        soft_skills * weights.soft_skills +  # 0.15
        experience * weights.experience +    # 0.25
        education * weights.education        # 0.20
    )

    total_bonus = (
        bonuses.certification +  # max 5
        bonuses.keyword +        # max 3
        bonuses.extra_skills     # max 2
    )

    final_score = min(weighted_score + total_bonus, 100.0)

    return ScoreResult(
        overall_score=round(final_score, 2),
        technical_score=round(technical, 2),
        soft_skills_score=round(soft_skills, 2),
        experience_score=round(experience, 2),
        education_score=round(education, 2),
        breakdown={
            "weighted_base": round(weighted_score, 2),
            "certification_bonus": bonuses.certification,
            "keyword_bonus": bonuses.keyword,
            "extra_skills_bonus": bonuses.extra_skills,
        }
    )
```

## 9.9 Fit Level Classification

| Score Range | Fit Level | Description |
|-------------|-----------|-------------|
| 85 - 100 | Strong Fit | Vượt yêu cầu, nên interview ngay |
| 70 - 84 | Good Fit | Đáp ứng phần lớn yêu cầu |
| 55 - 69 | Moderate Fit | Có tiềm năng nhưng cần bổ sung |
| 40 - 54 | Weak Fit | Thiếu nhiều skills quan trọng |
| 0 - 39 | No Fit | Không phù hợp với vị trí |

## 9.10 Score Validation Rules

```
1. All category scores: 0.0 <= score <= 100.0
2. All weights sum to 1.0 (±0.001 tolerance)
3. Final score: 0.0 <= score <= 100.0
4. Bonus total: 0.0 <= bonus <= 10.0
5. If no JD skills provided: return error (cannot score)
6. If no resume text: return score = 0 with error flag
```

## 9.11 Example Calculation

```
Resume: Python (5yr), AWS, Docker, React, SQL, Communication, Bachelor CS
JD Required: Python, AWS, Kubernetes, React, PostgreSQL, 3+ years, Bachelor's

Technical Matching:
  Python → Python (exact, 1.0)
  AWS → AWS (exact, 1.0)
  Docker → Kubernetes (semantic, 0.65 - below threshold, no match)
  React → React (exact, 1.0)
  SQL → PostgreSQL (fuzzy, 0.82)

Technical Score = (1.0 + 1.0 + 1.0 + 0.82) / 5 × 100 = 76.4

Soft Skills Score:
  Communication → matched (exact)
  But only 1 soft skill in JD
  Score = (1/1) × 100 = 100.0

Experience Score:
  Resume: 5 years, JD: 3 years
  5 >= 3 → base_score = 100.0

Education Score:
  Bachelor CS → degree_score = 40, relevance = 40
  Score = 80.0

Final:
  = 76.4 × 0.40 + 100.0 × 0.15 + 100.0 × 0.25 + 80.0 × 0.20
  = 30.56 + 15.0 + 25.0 + 16.0
  = 86.56

Bonuses:
  Certification: 0 (none detected)
  Keyword: 1.0 (40%+ match)
  Extra skills: 1.0 (Docker is extra relevant)

Final Score = min(86.56 + 2.0, 100) = 88.56
Fit Level: Strong Fit
```
