from datetime import datetime
from pydantic import BaseModel


class JobCreateRequest(BaseModel):
    title: str | None = None
    description: str | None = None


class AttachFileRequest(BaseModel):
    file_id: str
    file_type: str  # "cv" | "jd"


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobResponse(BaseModel):
    id: str
    user_id: str
    title: str | None
    description: str | None
    status: str
    cv_file_id: str | None
    jd_file_id: str | None
    candidate_count: int = 0
    analyzed_count: int = 0
    average_score: float | None = None
    best_candidate_name: str | None = None
    best_score: float | None = None
    error_code: str | None
    error_message: str | None
    retry_count: int
    created_at: datetime | None
    queued_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None


class CandidateResponse(BaseModel):
    id: str
    job_id: str
    user_id: str
    cv_file_id: str | None
    name: str | None
    email: str | None
    status: str
    recommendation: str | None
    error_code: str | None
    error_message: str | None
    created_at: datetime | None
    queued_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    failed_at: datetime | None


class CandidateRankingItem(CandidateResponse):
    rank: int | None = None
    overall_score: float | None = None
    skill_match: float | None = None
    role_match: float | None = None
    domain_match: float | None = None
    missing_skills: list[str] = []
    confidence: float | None = None
    confidence_level: str | None = None
    warnings: list[str] = []


class ScoreItem(BaseModel):
    score: float
    weight: int
    description: str


class CompatibilityInfo(BaseModel):
    overall_score: float
    level: str
    recommendation: str
    message: str
    confidence: float


class SkillsAnalysis(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]
    extra_skills: list[str]
    skill_match_ratio: float
    matched_must_have: list[str] = []
    missing_must_have: list[str] = []
    matched_nice_to_have: list[str] = []
    missing_nice_to_have: list[str] = []


class CandidateSummary(BaseModel):
    summary: str | None
    strengths: list[str]
    weaknesses: list[str]
    risk_flags: list[str]


class Recommendations(BaseModel):
    for_recruiter: list[str]
    for_candidate: list[str]


class ResultResponse(BaseModel):
    job_id: str
    candidate_id: str | None = None
    compatibility: CompatibilityInfo
    score_breakdown: dict[str, ScoreItem]
    skills_analysis: SkillsAnalysis
    candidate_summary: CandidateSummary
    recommendations: Recommendations
    interview_questions: list[str]
    alternative_roles: list[str]
    warnings: list[str]
    extracted_text: dict | None = None
    metadata: dict