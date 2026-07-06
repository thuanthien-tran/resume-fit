from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.database.session import get_db
from app.models.analysis_job import AnalysisJob
from app.models.job_event import JobEvent
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
def admin_list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(User)
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "status": user.status,
                "created_at": user.created_at,
            }
            for user in users
        ],
    }


@router.get("/jobs")
def admin_list_jobs(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    query = db.query(AnalysisJob)
    if status:
        query = query.filter(AnalysisJob.status == status)
    total = query.count()
    jobs = query.order_by(AnalysisJob.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(job.id),
                "user_id": str(job.user_id),
                "status": job.status,
                "error_code": job.error_code,
                "error_message": job.error_message,
                "created_at": job.created_at,
            }
            for job in jobs
        ],
    }


@router.get("/jobs/{job_id}/events")
def admin_job_events(
    job_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    events = db.query(JobEvent).filter(JobEvent.job_id == job_id).order_by(JobEvent.created_at.asc()).all()
    return [
        {
            "id": str(event.id),
            "job_id": str(event.job_id),
            "event_type": event.event_type,
            "old_status": event.old_status,
            "new_status": event.new_status,
            "message": event.message,
            "metadata": event.metadata_json,
            "created_at": event.created_at,
        }
        for event in events
    ]
