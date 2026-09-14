from typing import Any
from uuid import UUID

from database import connect_db
from models import Activity, ActivityCreate, Trip, TripCreate


class TripNotFoundError(Exception):
    pass


class ActivityNotFoundError(Exception):
    pass


class ActivityDateError(Exception):
    pass


_TRIPS_SQL = """
SELECT
    t.id,
    t.title,
    t.destination,
    t.start_date,
    t.end_date,
    t.travelers,
    t.budget_cents,
    a.id AS activity_id,
    a.title AS activity_title,
    a.activity_date,
    a.cost_cents
FROM trips AS t
LEFT JOIN activities AS a ON a.trip_id = t.id
"""


def _trips_from_rows(rows: list[dict[str, Any]]) -> list[Trip]:
    trips_by_id: dict[UUID, Trip] = {}

    for row in rows:
        trip = trips_by_id.get(row["id"])

        if trip is None:
            trip = Trip(
                id=row["id"],
                title=row["title"],
                destination=row["destination"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                travelers=row["travelers"],
                budget_cents=row["budget_cents"],
            )
            trips_by_id[trip.id] = trip

        if row["activity_id"] is not None:
            trip.activities.append(
                Activity(
                    id=row["activity_id"],
                    title=row["activity_title"],
                    activity_date=row["activity_date"],
                    cost_cents=row["cost_cents"],
                )
            )

    return list(trips_by_id.values())


def create_trip(payload: TripCreate) -> Trip:
    with connect_db() as connection:
        row = connection.execute(
            """
            INSERT INTO trips (
                title, destination, start_date, end_date,
                travelers, budget_cents
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, title, destination, start_date, end_date,
                      travelers, budget_cents
            """,
            (
                payload.title,
                payload.destination,
                payload.start_date,
                payload.end_date,
                payload.travelers,
                payload.budget_cents,
            ),
        ).fetchone()

        trip = Trip.model_validate(row)

    return trip


def list_trips() -> list[Trip]:
    with connect_db() as connection:
        rows = connection.execute(
            _TRIPS_SQL
            + " ORDER BY t.start_date, t.id, a.activity_date, a.id"
        ).fetchall()

        trips = _trips_from_rows(rows)

    return trips


def get_trip(trip_id: UUID) -> Trip | None:
    with connect_db() as connection:
        rows = connection.execute(
            _TRIPS_SQL
            + " WHERE t.id = %s ORDER BY a.activity_date, a.id",
            (trip_id,),
        ).fetchall()

        trips = _trips_from_rows(rows)

    return trips[0] if trips else None


def count_trips() -> int:
    with connect_db() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM trips"
        ).fetchone()

        assert row is not None
        count = row["count"]

    return count


def add_activity(
    trip_id: UUID,
    payload: ActivityCreate,
) -> Activity:
    with connect_db() as connection:
        trip = connection.execute(
            """
            SELECT start_date, end_date
            FROM trips
            WHERE id = %s
            FOR UPDATE
            """,
            (trip_id,),
        ).fetchone()

        if trip is None:
            raise TripNotFoundError()

        if not trip["start_date"] <= payload.activity_date <= trip["end_date"]:
            raise ActivityDateError()

        row = connection.execute(
            """
            INSERT INTO activities (
                trip_id, title, activity_date, cost_cents
            )
            VALUES (%s, %s, %s, %s)
            RETURNING id, title, activity_date, cost_cents
            """,
            (
                trip_id,
                payload.title,
                payload.activity_date,
                payload.cost_cents,
            ),
        ).fetchone()

        activity = Activity.model_validate(row)

    return activity


def delete_activity(trip_id: UUID, activity_id: UUID) -> None:
    with connect_db() as connection:
        trip = connection.execute(
            """
            SELECT id
            FROM trips
            WHERE id = %s
            FOR UPDATE
            """,
            (trip_id,),
        ).fetchone()

        if trip is None:
            raise TripNotFoundError()

        deleted = connection.execute(
            """
            DELETE FROM activities
            WHERE trip_id = %s AND id = %s
            RETURNING id
            """,
            (trip_id, activity_id),
        ).fetchone()

        if deleted is None:
            raise ActivityNotFoundError()