import logging
import signal
from threading import Event

import psycopg

from itinerary import PlanningInput, generate_itinerary
import job_repository


logger = logging.getLogger("travel.worker")


class RetryablePlanningError(Exception):
    """An explicitly classified temporary planning failure."""


def process_one_job() -> bool:
    recovered = job_repository.recover_expired_jobs()
    if recovered:
        logger.warning("jobs_recovered count=%s", recovered)

    job = job_repository.claim_next_job()
    if job is None:
        return False

    job_id = job["id"]
    token = job["claim_token"]
    logger.info("job_started id=%s attempt=%s", job_id, job["attempts"])
    try:
        payload = PlanningInput.model_validate(job["input_snapshot"])
        result = generate_itinerary(payload)
    except Exception as exc:
        status = job_repository.fail_job(
            job_id, token, retryable=isinstance(exc, RetryablePlanningError)
        )
        if status is None:
            logger.warning("job_claim_lost id=%s", job_id)
        else:
            logger.warning(
                "job_attempt_failed id=%s attempt=%s status=%s error_type=%s",
                job_id, job["attempts"], status, type(exc).__name__,
            )
    else:
        if job_repository.complete_job(job_id, token, result):
            logger.info("job_completed id=%s attempt=%s", job_id, job["attempts"])
        else:
            logger.warning("job_claim_lost id=%s", job_id)
    return True


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    stopping = Event()
    signal.signal(signal.SIGTERM, lambda *_: stopping.set())
    signal.signal(signal.SIGINT, lambda *_: stopping.set())
    logger.info("worker_started")
    while not stopping.is_set():
        try:
            processed = process_one_job()
        except psycopg.Error as exc:
            logger.error("worker_database_error error_type=%s", type(exc).__name__)
            raise SystemExit(1) from None
        if not processed:
            stopping.wait(1)
    logger.info("worker_stopped")


if __name__ == "__main__":
    main()