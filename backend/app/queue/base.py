from abc import ABC, abstractmethod


class QueueService(ABC):
    @abstractmethod
    def enqueue_analysis_job(self, message: dict) -> None:
        pass
