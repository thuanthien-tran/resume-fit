# Worker

Python worker service for background CV/JD analysis jobs.

The worker long-polls Amazon SQS, processes one analysis message at a time, and deletes the message only after processing finishes successfully. Failed messages are left in SQS so the queue redrive policy can retry and eventually move exhausted messages to `ResumeMatching-DLQ`.
