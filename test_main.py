from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import json_main as main



@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[TestClient]:
    monkeypatch.setattr(main, "DATA_PATH", tmp_path / "trips.json")
    monkeypatch.setattr(main, "trips", {})

    with TestClient(main.app) as test_client:
        yield test_client


def test_list_trips_starts_empty(client: TestClient) -> None:
    response = client.get("/trips")

    assert response.status_code == 200
    assert response.json() == []

@pytest.fixture
def trip_id(client: TestClient) -> str:
    response = client.post(
        "/trips",
        json={
            "title": "Hawaii family trip",
            "destination": "Hawaii",
            "start_date": "2026-10-01",
            "end_date": "2026-10-05",
            "travelers": 4,
            "budget_cents": 300000,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]

def test_deleting_activity_updates_budget(
    client: TestClient, trip_id: str
) -> None:
    activity_url = f"/trips/{trip_id}/activities"
    budget_url = f"/trips/{trip_id}/budget"

    first = client.post(
        activity_url,
        json={
            "title": "Beach picnic",
            "activity_date": "2026-10-01",
            "cost_cents": 12500,
        },
    )
    assert first.status_code == 201

    second = client.post(
        activity_url,
        json={
            "title": "Museum visit",
            "activity_date": "2026-10-05",
            "cost_cents": 7500,
        },
    )
    assert second.status_code == 201

    before = client.get(budget_url)
    assert before.status_code == 200
    assert before.json() == {
        "budget_cents": 300000,
        "planned_cost_cents": 20000,
        "remaining_cents": 280000,
    }

    activity_id = first.json()["id"]
    deleted = client.delete(f"{activity_url}/{activity_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""

    activities = client.get(activity_url)
    assert activities.status_code == 200
    assert activities.json() == [second.json()]

    after = client.get(budget_url)
    assert after.status_code == 200
    assert after.json() == {
        "budget_cents": 300000,
        "planned_cost_cents": 7500,
        "remaining_cents": 292500,
    }

def test_activity_outside_trip_dates_is_rejected(
    client: TestClient, trip_id: str
) -> None:
    activity_url = f"/trips/{trip_id}/activities"
    activity = client.post(
        activity_url,
        json={
            "title": "Beach picnic",
            "activity_date": "2026-10-06",
            "cost_cents": 12500,
        },
    )
    assert activity.status_code == 422
    activities = client.get(activity_url)
    assert activities.status_code == 200
    assert activities.json() == []

def test_trip_survives_restart(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "trips.json"
    monkeypatch.setattr(main, "DATA_PATH", path)
    monkeypatch.setattr(main, "trips", {})

    with TestClient(main.app) as first_client:
        response = first_client.post(
            "/trips",
            json={
                "title": "Hawaii family trip",
                "destination": "Hawaii",
                "start_date": "2026-10-01",
                "end_date": "2026-10-05",
                "travelers": 4,
                "budget_cents": 300000,
            },
        )
        assert response.status_code == 201
        saved_trip = response.json()
        trip_id = saved_trip["id"]

    # Leaving the first with block closes its client.
    assert path.exists()
    main.trips = {}

    # Entering this block runs startup again using the same file.
    with TestClient(main.app) as second_client:
        response = second_client.get(f"/trips/{trip_id}")

        assert response.status_code == 200
        assert response.json() == saved_trip


def test_deleted_activity_stays_deleted_after_restart(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "trips.json"
    monkeypatch.setattr(main, "DATA_PATH", path)
    monkeypatch.setattr(main, "trips", {})

    with TestClient(main.app) as first_client:
        trip_response = first_client.post(
            "/trips",
            json={
                "title": "Hawaii family trip",
                "destination": "Hawaii",
                "start_date": "2026-10-01",
                "end_date": "2026-10-05",
                "travelers": 4,
                "budget_cents": 300000,
            },
        )
        assert trip_response.status_code == 201
        trip_id = trip_response.json()["id"]
        activity_url = f"/trips/{trip_id}/activities"

        first_activity = first_client.post(
            activity_url,
            json={
                "title": "Beach picnic",
                "activity_date": "2026-10-01",
                "cost_cents": 12500,
            },
        )
        assert first_activity.status_code == 201

        second_activity = first_client.post(
            activity_url,
            json={
                "title": "Museum visit",
                "activity_date": "2026-10-05",
                "cost_cents": 7500,
            },
        )
        assert second_activity.status_code == 201
        remaining_activity = second_activity.json()

        # Verify both activities exist before deleting.
        before_delete = first_client.get(activity_url)
        assert before_delete.status_code == 200, before_delete.text
        assert before_delete.json() == [
            first_activity.json(),
            remaining_activity,
        ], before_delete.text

        deleted_id = first_activity.json()["id"]
        deleted = first_client.delete(f"{activity_url}/{deleted_id}")

        # Include the API's error message if deletion fails.
        assert deleted.status_code == 204, deleted.text
        assert deleted.content == b""

    # The first client has closed. Clear memory but keep the file.
    assert path.exists()
    main.trips = {}

    # Startup reloads the saved trips and activities from the same file.
    with TestClient(main.app) as second_client:
        activities = second_client.get(activity_url)
        assert activities.status_code == 200
        assert activities.json() == [remaining_activity]

        budget = second_client.get(f"/trips/{trip_id}/budget")
        assert budget.status_code == 200
        assert budget.json() == {
            "budget_cents": 300000,
            "planned_cost_cents": 7500,
            "remaining_cents": 292500,
        }


