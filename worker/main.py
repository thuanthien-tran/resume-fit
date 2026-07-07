from app.core.logging import setup_logging
from worker.worker_loop import poll_sqs_forever


def main() -> None:
    setup_logging()
    poll_sqs_forever()


if __name__ == "__main__":
    main()
