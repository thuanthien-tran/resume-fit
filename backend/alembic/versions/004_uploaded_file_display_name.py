"""add display_name to uploaded_files

Revision ID: 004_uploaded_file_display_name
Revises: 003_partial_completed_status
Create Date: 2026-07-06
"""

from alembic import op
import sqlalchemy as sa

revision = "004_uploaded_file_display_name"
down_revision = "003_partial_completed_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("uploaded_files", sa.Column("display_name", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("uploaded_files", "display_name")
