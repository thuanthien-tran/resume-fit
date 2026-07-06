from sqlalchemy.orm import Session

from app.models.job_event import JobEvent


def create_job_event(
    db: Session,
    job_id,
    event_type: str,
    old_status: str | None = None,
    new_status: str | None = None,
    message: str | None = None,
    metadata: dict | None = None,
) -> JobEvent:
    event = JobEvent(
        job_id=job_id,
        event_type=event_type,
        old_status=old_status,
        new_status=new_status,
        message=message,
        metadata_json=metadata or {},
    )
    db.add(event)
    return event
