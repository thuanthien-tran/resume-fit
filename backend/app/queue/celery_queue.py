from celery import Celery

from app.core.config import settings
from app.queue.base import QueueService

celery_app = Celery(
    "resume_queue_client",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


class CeleryQueueService(QueueService):
    def enqueue_analysis_job(self, message: dict) -> None:
        celery_app.send_task("app.worker.tasks.process_analysis_job", args=[message], queue="celery")


queue_service = CeleryQueueService()