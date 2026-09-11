from datetime import date
from pathlib import Path
from uuid import UUID, uuid4

from models import Activity, Trip
from storage import load_trips, save_trips


def test_save_and_load_trips(tmp_path: Path) -> None:
    path = tmp_path / "trips.json"

    activity = Activity(
        id=uuid4(),
        title="Beach picnic",
        activity_date=date(2026, 10, 1),
        cost_cents=12500,
    )
    trip = Trip(
        id=uuid4(),
        title="Hawaii family trip",
        destination="Hawaii",
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 5),
        travelers=4,
        budget_cents=300000,
        activities=[activity],
    )

    save_trips({trip.id: trip}, path)
    loaded = load_trips(path)

    assert path.exists()
    assert loaded == {trip.id: trip}

    restored = loaded[trip.id]
    assert isinstance(restored.id, UUID)
    assert isinstance(restored.start_date, date)
    assert isinstance(restored.activities[0], Activity)
    assert restored is not trip

def test_load_trips_when_file_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "trips2.json"
    loaded = load_trips(path)
    assert loaded == {}
    assert not path.exists()
