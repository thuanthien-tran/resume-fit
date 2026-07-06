import json

import boto3

from app.core.config import settings
from app.queue.base import QueueService


class SqsQueueService(QueueService):
    """Hàng đợi bất đồng bộ trên Amazon SQS.

    DLQ được cấu hình ở tầng hạ tầng AWS (redrive policy trên queue), không ở code.
    """

    def __init__(self):
        self.queue_url = settings.sqs_queue_url
        self.client = boto3.client("sqs", region_name=settings.aws_region)

    def enqueue_analysis_job(self, message: dict) -> None:
        self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(message),
        )
