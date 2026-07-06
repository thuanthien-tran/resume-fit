from app.core.config import settings
from app.queue.base import QueueService


def get_queue_service() -> QueueService:
    if settings.queue_provider == "sqs":
        # Lazy import: chỉ nạp boto3 khi thực sự dùng SQS.
        from app.queue.sqs_queue import SqsQueueService

        return SqsQueueService()
    from app.queue.celery_queue import queue_service as celery_queue_service

    return celery_queue_service
