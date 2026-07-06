# Worker

Celery worker source for background CV/JD analysis jobs.

The worker imports shared backend modules from `backend/app` and registers the analysis task consumed from Redis.