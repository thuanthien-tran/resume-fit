import json

import pytest

worker_loop = pytest.importorskip("worker.worker_loop")


class FakeSQSClient:
    def __init__(self, messages=None, receive_error=None):
        self.messages = messages or []
        self.receive_error = receive_error
        self.deleted = []

    def receive_message(self, **kwargs):
        if self.receive_error:
            raise self.receive_error
        return {"Messages": self.messages}

    def delete_message(self, **kwargs):
        self.deleted.append(kwargs)


def sample_message():
    return {
        "MessageId": "message-1",
        "ReceiptHandle": "receipt-1",
        "Attributes": {"ApproximateReceiveCount": "1"},
        "Body": json.dumps(
            {
                "job_id": "00000000-0000-0000-0000-000000000001",
                "candidate_id": "00000000-0000-0000-0000-000000000002",
                "cv_file_id": "00000000-0000-0000-0000-000000000003",
                "jd_file_id": "00000000-0000-0000-0000-000000000004",
                "timestamp": "2026-07-07T00:00:00+00:00",
                "version": 1,
            }
        ),
    }


def test_process_sqs_message_deletes_only_after_success(monkeypatch):
    client = FakeSQSClient()
    processed = []

    def fake_process(payload):
        processed.append(payload)

    monkeypatch.setattr(worker_loop.settings, "sqs_queue_url", "queue-url")
    monkeypatch.setattr(worker_loop, "process_analysis_job", fake_process)

    assert worker_loop.process_sqs_message(client, sample_message()) is True
    assert processed[0]["job_id"] == "00000000-0000-0000-0000-000000000001"
    assert client.deleted == [{"QueueUrl": "queue-url", "ReceiptHandle": "receipt-1"}]


def test_process_sqs_message_keeps_message_when_processing_fails(monkeypatch):
    client = FakeSQSClient()

    def fake_process(payload):
        raise RuntimeError("temporary failure")

    monkeypatch.setattr(worker_loop.settings, "sqs_queue_url", "queue-url")
    monkeypatch.setattr(worker_loop, "process_analysis_job", fake_process)
    monkeypatch.setattr(worker_loop.time, "sleep", lambda seconds: None)

    assert worker_loop.process_sqs_message(client, sample_message()) is False
    assert client.deleted == []


def test_receive_messages_returns_empty_on_sqs_error(monkeypatch):
    client = FakeSQSClient(receive_error=TimeoutError("sqs timeout"))

    monkeypatch.setattr(worker_loop.settings, "sqs_queue_url", "queue-url")
    monkeypatch.setattr(worker_loop.settings, "sqs_wait_time_seconds", 20)
    monkeypatch.setattr(worker_loop.settings, "sqs_visibility_timeout_seconds", 300)
    monkeypatch.setattr(worker_loop.time, "sleep", lambda seconds: None)

    assert worker_loop.receive_messages(client) == []
