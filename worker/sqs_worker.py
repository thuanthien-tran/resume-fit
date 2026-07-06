import json
import logging
import time

import boto3

from app.core.config import settings
from worker.tasks import process_analysis_job

logger = logging.getLogger(__name__)


def poll_sqs_forever() -> None:
    if not settings.sqs_queue_url:
        raise RuntimeError("SQS_QUEUE_URL is required for the SQS worker.")

    client = boto3.client("sqs", region_name=settings.aws_region)
    logger.info("sqs_worker_started", extra={"queue_url": settings.sqs_queue_url})

    while True:
        response = client.receive_message(
            QueueUrl=settings.sqs_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=300,
        )
        messages = response.get("Messages", [])
        if not messages:
            continue

        for item in messages:
            receipt_handle = item["ReceiptHandle"]
            try:
                payload = json.loads(item["Body"])
                process_analysis_job.apply(args=[payload])
                client.delete_message(QueueUrl=settings.sqs_queue_url, ReceiptHandle=receipt_handle)
                logger.info("sqs_message_processed", extra={"job_id": payload.get("job_id"), "candidate_id": payload.get("candidate_id")})
            except Exception:
                logger.exception("sqs_message_failed")
                time.sleep(2)


if __name__ == "__main__":
    poll_sqs_forever()
