import json
import logging
import time
from datetime import datetime, timezone
from uuid import UUID

import anyio
import boto3
from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError

from app.core.config import settings

logger = logging.getLogger(__name__)


class SQSService:
    """Small SQS boundary so API controllers never talk to boto3 directly."""

    def __init__(self) -> None:
        self.queue_url = settings.sqs_queue_url
        self.client = None

    async def send_analysis_job(
        self,
        *,
        job_id: UUID,
        candidate_id: UUID,
        cv_file_id: UUID,
        jd_file_id: UUID,
    ) -> None:
        message = {
            "job_id": str(job_id),
            "candidate_id": str(candidate_id),
            "cv_file_id": str(cv_file_id),
            "jd_file_id": str(jd_file_id),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": 1,
        }
        await anyio.to_thread.run_sync(self._send_with_retries, message)

    def _send_with_retries(self, message: dict) -> None:
        if not self.queue_url:
            raise RuntimeError("SQS_QUEUE_URL is required to enqueue analysis jobs.")
        if self.client is None:
            self.client = boto3.client("sqs", region_name=settings.aws_region)
        body = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = self.client.send_message(QueueUrl=self.queue_url, MessageBody=body)
                logger.info(
                    "sqs_message_sent",
                    extra={
                        "message_id": response.get("MessageId"),
                        "job_id": message.get("job_id"),
                        "candidate_id": message.get("candidate_id"),
                        "attempt": attempt,
                    },
                )
                return
            except (BotoCoreError, ClientError, EndpointConnectionError) as exc:
                last_error = exc
                logger.warning(
                    "sqs_send_retry",
                    extra={
                        "job_id": message.get("job_id"),
                        "candidate_id": message.get("candidate_id"),
                        "attempt": attempt,
                        "error": exc.__class__.__name__,
                    },
                )
                if attempt < 3:
                    time.sleep(attempt)
        raise RuntimeError("Could not send analysis job to SQS") from last_error


sqs_service = SQSService()
