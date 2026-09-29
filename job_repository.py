from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from database import connect_db
from itinerary import ItineraryDraft, PlanningInput
from job_models import JobPublic

MAX_ATTEMPTS = 3
LEASE_SECONDS = 60


class PlanningTripNotFoundError(Exception):
    pass


def create_job(trip_id: UUID, *, owner_id: UUID) -> JobPublic:
    with connect_db() as connection:
        trip = connection.execute(
            """
            SELECT destination, start_date, end_date
            FROM trips
            WHERE id = %s AND owner_id = %s
            FOR SHARE
            """,
            (trip_id, owner_id),
        ).fetchone()
        if trip is None:
            raise PlanningTripNotFoundError()

        snapshot = PlanningInput.model_validate(trip)
        row = connection.execute(
            """
            INSERT INTO itinerary_jobs (id, trip_id, owner_id, input_snapshot)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (uuid4(), trip_id, owner_id, Jsonb(snapshot.model_dump(mode="json"))),
        ).fetchone()

    return JobPublic.model_validate(row)


def get_job(job_id: UUID, *, owner_id: UUID) -> JobPublic | None:
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT * FROM itinerary_jobs
            WHERE id = %s AND owner_id = %s
            """,
            (job_id, owner_id),
        ).fetchone()

    return None if row is None else JobPublic.model_validate(row)


def recover_expired_jobs() -> int:
    with connect_db() as connection:
        updated = connection.execute(
            """
            WITH expired AS (
                SELECT id FROM itinerary_jobs
                WHERE status = 'running' AND lease_expires_at <= now()
                ORDER BY lease_expires_at, id
                LIMIT 100
                FOR UPDATE SKIP LOCKED
            )
            UPDATE itinerary_jobs AS job
            SET status = CASE WHEN job.attempts < %s
                              THEN 'queued' ELSE 'failed' END,
                available_at = now() + interval '5 seconds',
                claim_token = NULL, lease_expires_at = NULL,
                result = NULL,
                error = CASE WHEN job.attempts < %s THEN NULL
                             ELSE 'Worker attempts exhausted' END,
                finished_at = CASE WHEN job.attempts < %s THEN NULL
                                   ELSE now() END
            FROM expired
            WHERE job.id = expired.id
            """,
            (MAX_ATTEMPTS, MAX_ATTEMPTS, MAX_ATTEMPTS),
        )
        count = updated.rowcount
    return count

def claim_next_job() -> dict[str, Any] | None:
    with connect_db() as connection:
        row = connection.execute(
            """
            WITH candidate AS (
                SELECT id FROM itinerary_jobs
                WHERE status = 'queued'
                  AND available_at <= now() AND attempts < %s
                ORDER BY available_at, created_at, id
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE itinerary_jobs AS job
            SET status = 'running', attempts = job.attempts + 1,
                started_at = now(), finished_at = NULL,
                error = NULL, result = NULL,
                claim_token = %s,
                lease_expires_at = now() + (%s * interval '1 second')
            FROM candidate
            WHERE job.id = candidate.id
            RETURNING job.id, job.input_snapshot, job.claim_token, job.attempts
            """,
            (MAX_ATTEMPTS, uuid4(), LEASE_SECONDS),
        ).fetchone()
    return row


def complete_job(
    job_id: UUID, claim_token: UUID, result: ItineraryDraft
) -> bool:
    with connect_db() as connection:
        updated = connection.execute(
            """
            UPDATE itinerary_jobs
            SET status = 'completed', result = %s,
                error = NULL, finished_at = now(),
                claim_token = NULL, lease_expires_at = NULL
            WHERE id = %s AND status = 'running' AND claim_token = %s
              AND lease_expires_at > now()
            """,
            (Jsonb(result.model_dump(mode="json")), job_id, claim_token),
        )
        saved = updated.rowcount == 1
    return saved



def fail_job(
    job_id: UUID, claim_token: UUID, *, retryable: bool = False
) -> str | None:
    with connect_db() as connection:
        row = connection.execute(
            """
            UPDATE itinerary_jobs
            SET status = CASE WHEN %s AND attempts < %s
                              THEN 'queued' ELSE 'failed' END,
                available_at = now() + (5 * attempts * interval '1 second'),
                result = NULL, claim_token = NULL, lease_expires_at = NULL,
                error = CASE WHEN %s AND attempts < %s THEN NULL
                             ELSE 'Itinerary generation failed' END,
                finished_at = CASE WHEN %s AND attempts < %s THEN NULL
                                   ELSE now() END
            WHERE id = %s AND status = 'running' AND claim_token = %s
              AND lease_expires_at > now()
            RETURNING status
            """,
            (
                retryable, MAX_ATTEMPTS,
                retryable, MAX_ATTEMPTS,
                retryable, MAX_ATTEMPTS,
                job_id, claim_token,
            ),
        ).fetchone()
    return None if row is None else row["status"]