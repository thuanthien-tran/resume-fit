import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.database.session import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)

    matching_score = Column(Numeric(5, 2), nullable=False)
    skill_score = Column(Numeric(5, 2), nullable=True)
    experience_score = Column(Numeric(5, 2), nullable=True)
    education_score = Column(Numeric(5, 2), nullable=True)

    matched_skills = Column(JSONB, nullable=False, default=list)
    missing_skills = Column(JSONB, nullable=False, default=list)
    extra_skills = Column(JSONB, nullable=False, default=list)

    summary = Column(Text, nullable=True)
    strengths = Column(JSONB, nullable=False, default=list)
    weaknesses = Column(JSONB, nullable=False, default=list)
    improvement_suggestions = Column(JSONB, nullable=False, default=list)
    interview_questions = Column(JSONB, nullable=False, default=list)

    raw_matching_result = Column(JSONB, nullable=False, default=dict)
    ai_provider = Column(String(100), nullable=True)
    ai_model = Column(String(100), nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    processing_time_seconds = Column(Numeric(10, 3), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)