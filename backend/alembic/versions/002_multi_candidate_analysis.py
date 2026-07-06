"""add candidates and multi cv analysis

Revision ID: 002_multi_candidate_analysis
Revises: 001_init_schema
Create Date: 2026-07-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_multi_candidate_analysis"
down_revision = "001_init_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("analysis_jobs", sa.Column("title", sa.String(255), nullable=True))
    op.add_column("analysis_jobs", sa.Column("description", sa.Text(), nullable=True))

    op.create_table(
        "candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("cv_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("uploaded_files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="uploaded"),
        sa.Column("recommendation", sa.String(100), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_candidates_job_id", "candidates", ["job_id"])
    op.create_index("idx_candidates_user_id", "candidates", ["user_id"])
    op.create_index("idx_candidates_cv_file_id", "candidates", ["cv_file_id"])
    op.create_index("idx_candidates_status", "candidates", ["status"])
    op.create_index("idx_candidates_created_at", "candidates", ["created_at"])

    op.execute("ALTER TABLE analysis_results DROP CONSTRAINT IF EXISTS analysis_results_job_id_key")
    op.add_column("analysis_results", sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_analysis_results_candidate",
        "analysis_results",
        "candidates",
        ["candidate_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("idx_analysis_results_candidate_id", "analysis_results", ["candidate_id"], unique=True)


def downgrade() -> None:
    op.drop_index("idx_analysis_results_candidate_id", table_name="analysis_results")
    op.drop_constraint("fk_analysis_results_candidate", "analysis_results", type_="foreignkey")
    op.drop_column("analysis_results", "candidate_id")
    op.create_unique_constraint("analysis_results_job_id_key", "analysis_results", ["job_id"])

    op.drop_index("idx_candidates_created_at", table_name="candidates")
    op.drop_index("idx_candidates_status", table_name="candidates")
    op.drop_index("idx_candidates_cv_file_id", table_name="candidates")
    op.drop_index("idx_candidates_user_id", table_name="candidates")
    op.drop_index("idx_candidates_job_id", table_name="candidates")
    op.drop_table("candidates")

    op.drop_column("analysis_jobs", "description")
    op.drop_column("analysis_jobs", "title")