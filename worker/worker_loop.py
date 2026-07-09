import json
import logging
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError

from app.core.config import settings
from app.database.session import SessionLocal
from app.models.analysis_job import AnalysisJob
from app.models.candidate import Candidate
from worker.tasks import process_analysis_job

logger = logging.getLogger(__name__)


def receive_messages(client) -> list[dict]:
    logger.info("sqs_receive_message_waiting")
    try:
        response = client.receive_message(
            QueueUrl=settings.sqs_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=settings.sqs_wait_time_seconds,
            VisibilityTimeout=settings.sqs_visibility_timeout_seconds,
            AttributeNames=["ApproximateReceiveCount"],
        )
    except (BotoCoreError, ClientError, EndpointConnectionError, TimeoutError) as exc:
        logger.warning("sqs_receive_message_retry", extra={"error": exc.__class__.__name__})
        time.sleep(2)
        return []
    return response.get("Messages", [])


def process_sqs_message(client, item: dict) -> bool:
    receipt_handle = item["ReceiptHandle"]
    receive_count = item.get("Attributes", {}).get("ApproximateReceiveCount")
    payload = {}
    try:
        payload = json.loads(item["Body"])
        logger.info(
            "sqs_message_received",
            extra={
                "message_id": item.get("MessageId"),
                "job_id": payload.get("job_id"),
                "candidate_id": payload.get("candidate_id"),
                "receive_count": receive_count,
            },
        )
        logger.info(
            "sqs_message_processing",
            extra={"job_id": payload.get("job_id"), "candidate_id": payload.get("candidate_id")},
        )
        process_analysis_job(payload)
        client.delete_message(QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt_handle)
        logger.info(
            "sqs_message_deleted",
            extra={"job_id": payload.get("job_id"), "candidate_id": payload.get("candidate_id")},
        )
        return True
    except Exception:
        logger.exception(
            "sqs_message_failed_not_deleted",
            extra={
                "message_id": item.get("MessageId"),
                "job_id": payload.get("job_id"),
                "candidate_id": payload.get("candidate_id"),
                "receive_count": receive_count,
                "dlq": "SQS redrive policy moves exhausted messages to ResumeMatching-DLQ",
            },
        )
        time.sleep(2)
        return False


def poll_sqs_once(client) -> int:
    messages = receive_messages(client)
    processed = 0
    for item in messages:
        if process_sqs_message(client, item):
            processed += 1
    return processed


def poll_local_db_once() -> int:
    """Process queued candidates directly from Postgres for local/dev mode.

    Production uses SQS. In local setups SQS_QUEUE_URL is often empty, so the API
    marks candidates as queued in the database and this worker picks them up.
    """
    db = SessionLocal()
    try:
        candidate = (
            db.query(Candidate)
            .join(AnalysisJob, Candidate.job_id == AnalysisJob.id)
            .filter(Candidate.status == "queued")
            .filter(AnalysisJob.status.in_(["queued", "processing"]))
            .order_by(Candidate.queued_at.asc().nullslast(), Candidate.created_at.asc())
            .first()
        )
        if not candidate:
            return 0
        job = db.query(AnalysisJob).filter(AnalysisJob.id == candidate.job_id).first()
        if not job or not job.jd_file_id or not candidate.cv_file_id:
            return 0
        payload = {
            "job_id": str(job.id),
            "candidate_id": str(candidate.id),
            "cv_file_id": str(candidate.cv_file_id),
            "jd_file_id": str(job.jd_file_id),
        }
    finally:
        db.close()

    logger.info(
        "local_db_message_processing",
        extra={"job_id": payload["job_id"], "candidate_id": payload["candidate_id"]},
    )
    process_analysis_job(payload)
    return 1


def poll_local_db_forever() -> None:
    logger.info("local_db_worker_started", extra={"reason": "SQS_QUEUE_URL is empty"})
    while True:
        try:
            processed = poll_local_db_once()
            if not processed:
                time.sleep(2)
        except Exception:
            logger.exception("local_db_message_failed")
            time.sleep(2)

def create_sqs_client():
    return boto3.client("sqs", region_name=settings.aws_region)


def poll_sqs_forever() -> None:
    if not settings.sqs_queue_url:
        poll_local_db_forever()
        return

    client = create_sqs_client()
    logger.info(
        "sqs_worker_started",
        extra={
            "queue_url": settings.sqs_queue_url,
            "dlq_url": settings.sqs_dlq_url or "managed_by_sqs_redrive_policy",
            "visibility_timeout_seconds": settings.sqs_visibility_timeout_seconds,
        },
    )

    while True:
        poll_sqs_once(client)
