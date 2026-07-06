"""add partial_completed to job_status enum

Revision ID: 003_partial_completed_status
Revises: 002_multi_candidate_analysis
Create Date: 2026-07-05
"""

from alembic import op

revision = "003_partial_completed_status"
down_revision = "002_multi_candidate_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE không chạy được bên trong transaction block.
    # Dùng autocommit để thêm giá trị mới an toàn trên PostgreSQL.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'partial_completed' AFTER 'completed'"
        )


def downgrade() -> None:
    # PostgreSQL không hỗ trợ xoá giá trị khỏi enum, phải tạo lại type.
    # Quy các job partial_completed về completed trước khi loại giá trị.
    op.execute("UPDATE analysis_jobs SET status = 'completed' WHERE status = 'partial_completed'")
    op.execute("ALTER TYPE job_status RENAME TO job_status_old")
    op.execute(
        "CREATE TYPE job_status AS ENUM "
        "('uploaded', 'queued', 'processing', 'completed', 'failed', 'cancelled')"
    )
    op.execute(
        "ALTER TABLE analysis_jobs ALTER COLUMN status TYPE job_status "
        "USING status::text::job_status"
    )
    op.execute(
        "ALTER TABLE job_events ALTER COLUMN old_status TYPE job_status "
        "USING old_status::text::job_status"
    )
    op.execute(
        "ALTER TABLE job_events ALTER COLUMN new_status TYPE job_status "
        "USING new_status::text::job_status"
    )
    op.execute("DROP TYPE job_status_old")
