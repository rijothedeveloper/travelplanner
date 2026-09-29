from datetime import date

import pytest
from pydantic import ValidationError

from itinerary import ItineraryDraft, PlanningInput, generate_itinerary


def test_itinerary_includes_every_trip_date() -> None:
    payload = PlanningInput(
        destination="Hawaii",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 5),
    )

    draft = generate_itinerary(payload)

    assert draft.destination == "Hawaii"
    assert [day.day_date for day in draft.days] == [
        date(2026, 10, 1),
        date(2026, 10, 2),
        date(2026, 10, 3),
        date(2026, 10, 4),
        date(2026, 10, 5),
    ]
    assert all(day.suggestion for day in draft.days)


def test_single_day_trip_has_one_planning_day() -> None:
    payload = PlanningInput(
        destination="San Francisco",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 1),
    )

    draft = generate_itinerary(payload)

    assert len(draft.days) == 1
    assert draft.days[0].day_date == date(2026, 10, 1)


def test_planning_limit_accepts_fourteen_days_and_rejects_fifteen() -> None:
    payload = PlanningInput(
        destination="Hawaii",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 14),
    )
    assert len(generate_itinerary(payload).days) == 14

    with pytest.raises(ValidationError, match="at most 14 days"):
        PlanningInput(
            destination="Hawaii",
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 15),
        )


def test_reversed_dates_are_rejected() -> None:
    with pytest.raises(ValidationError, match="on or after start_date"):
        PlanningInput(
            destination="Hawaii",
            start_date=date(2026, 10, 5),
            end_date=date(2026, 10, 1),
        )


def test_draft_survives_json_serialization() -> None:
    draft = generate_itinerary(
        PlanningInput(
            destination="Hawaii",
            start_date=date(2026, 12, 31),
            end_date=date(2027, 1, 1),
        )
    )

    data = draft.model_dump(mode="json")

    assert [day["day_date"] for day in data["days"]] == [
        "2026-12-31",
        "2027-01-01",
    ]
    assert ItineraryDraft.model_validate(data) == draft