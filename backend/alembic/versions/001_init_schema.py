"""init schema

Revision ID: 001_init_schema
Revises:
Create Date: 2026-06-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_init_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.execute("CREATE TYPE user_role AS ENUM ('user', 'admin')")
    op.execute("CREATE TYPE user_status AS ENUM ('active', 'inactive', 'blocked')")
    op.execute("CREATE TYPE file_type AS ENUM ('cv', 'jd')")
    op.execute("CREATE TYPE storage_type AS ENUM ('local', 'minio', 's3')")
    op.execute("CREATE TYPE upload_status AS ENUM ('uploaded', 'failed', 'deleted')")
    op.execute("CREATE TYPE job_status AS ENUM ('uploaded', 'queued', 'processing', 'completed', 'failed', 'cancelled')")

    user_role = postgresql.ENUM('user', 'admin', name='user_role', create_type=False)
    user_status = postgresql.ENUM('active', 'inactive', 'blocked', name='user_status', create_type=False)
    file_type = postgresql.ENUM('cv', 'jd', name='file_type', create_type=False)
    storage_type = postgresql.ENUM('local', 'minio', 's3', name='storage_type', create_type=False)
    upload_status = postgresql.ENUM('uploaded', 'failed', 'deleted', name='upload_status', create_type=False)
    job_status = postgresql.ENUM('uploaded', 'queued', 'processing', 'completed', 'failed', 'cancelled', name='job_status', create_type=False)

    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('role', user_role, nullable=False, server_default='user'),
        sa.Column('status', user_status, nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_status', 'users', ['status'])

    op.create_table(
        'analysis_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', job_status, nullable=False, server_default='uploaded'),
        sa.Column('cv_file_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('jd_file_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('error_code', sa.String(100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_analysis_jobs_user_id', 'analysis_jobs', ['user_id'])
    op.create_index('idx_analysis_jobs_status', 'analysis_jobs', ['status'])
    op.create_index('idx_analysis_jobs_created_at', 'analysis_jobs', ['created_at'])
    op.create_index('idx_analysis_jobs_user_status', 'analysis_jobs', ['user_id', 'status'])

    op.create_table(
        'uploaded_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analysis_jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('file_type', file_type, nullable=False),
        sa.Column('original_filename', sa.String(512), nullable=False),
        sa.Column('storage_type', storage_type, nullable=False, server_default='local'),
        sa.Column('storage_path', sa.String(), nullable=False),
        sa.Column('bucket_name', sa.String(255), nullable=True),
        sa.Column('object_key', sa.String(), nullable=True),
        sa.Column('mime_type', sa.String(255), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('checksum', sa.String(128), nullable=False),
        sa.Column('upload_status', upload_status, nullable=False, server_default='uploaded'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_uploaded_files_user_id', 'uploaded_files', ['user_id'])
    op.create_index('idx_uploaded_files_job_id', 'uploaded_files', ['job_id'])
    op.create_index('idx_uploaded_files_status', 'uploaded_files', ['upload_status'])
    op.create_index('idx_uploaded_files_created_at', 'uploaded_files', ['created_at'])

    op.create_foreign_key('fk_analysis_jobs_cv_file', 'analysis_jobs', 'uploaded_files', ['cv_file_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_analysis_jobs_jd_file', 'analysis_jobs', 'uploaded_files', ['jd_file_id'], ['id'], ondelete='SET NULL')

    op.create_table(
        'analysis_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analysis_jobs.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('matching_score', sa.Numeric(5, 2), nullable=False),
        sa.Column('skill_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('experience_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('education_score', sa.Numeric(5, 2), nullable=True),
        sa.Column('matched_skills', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('missing_skills', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('extra_skills', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('strengths', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('weaknesses', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('improvement_suggestions', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('interview_questions', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('raw_matching_result', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('ai_provider', sa.String(100), nullable=True),
        sa.Column('ai_model', sa.String(100), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('processing_time_seconds', sa.Numeric(10, 3), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_analysis_results_job_id', 'analysis_results', ['job_id'])

    op.create_table(
        'job_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analysis_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('old_status', job_status, nullable=True),
        sa.Column('new_status', job_status, nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_job_events_job_id', 'job_events', ['job_id'])
    op.create_index('idx_job_events_created_at', 'job_events', ['created_at'])

    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])

    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])
    op.create_index('idx_refresh_tokens_expires_at', 'refresh_tokens', ['expires_at'])


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_table('audit_logs')
    op.drop_table('job_events')
    op.drop_table('analysis_results')
    op.drop_constraint('fk_analysis_jobs_jd_file', 'analysis_jobs', type_='foreignkey')
    op.drop_constraint('fk_analysis_jobs_cv_file', 'analysis_jobs', type_='foreignkey')
    op.drop_table('uploaded_files')
    op.drop_table('analysis_jobs')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS job_status')
    op.execute('DROP TYPE IF EXISTS upload_status')
    op.execute('DROP TYPE IF EXISTS storage_type')
    op.execute('DROP TYPE IF EXISTS file_type')
    op.execute('DROP TYPE IF EXISTS user_status')
    op.execute('DROP TYPE IF EXISTS user_role')
