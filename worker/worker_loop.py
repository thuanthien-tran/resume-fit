import json
import logging
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError

from app.core.config import settings
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


def create_sqs_client():
    return boto3.client("sqs", region_name=settings.aws_region)


def poll_sqs_forever() -> None:
    if not settings.sqs_queue_url:
        raise RuntimeError("SQS_QUEUE_URL is required for the SQS worker.")

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
