from pathlib import Path
from uuid import UUID, uuid4

from pydantic import TypeAdapter

from models import Trip


trip_list_adapter = TypeAdapter(list[Trip])


def save_trips(trips: dict[UUID, Trip], path: Path) -> None:
    trip_list = list(trips.values())
    content = trip_list_adapter.dump_json(trip_list, indent=2)
    temporary_path = path.with_name(f"{path.name}.{uuid4().hex}.tmp")

    try:
        temporary_path.write_bytes(content)
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def load_trips(path: Path) -> dict[UUID, Trip]:
    try:
        content = path.read_bytes()
    except FileNotFoundError:
        return {}

    trip_list = trip_list_adapter.validate_json(content)

    trips: dict[UUID, Trip] = {}
    for trip in trip_list:
        trips[trip.id] = trip

    return trips