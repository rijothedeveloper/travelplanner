from contextlib import asynccontextmanager
from uuid import UUID, uuid4
from fastapi import FastAPI, HTTPException, Response
from models import Activity, ActivityCreate, Trip, TripCreate
from services import calculate_planned_cost
from storage import save_trips, load_trips
from pathlib import Path
from collections.abc import AsyncIterator
from threading import Lock

state_lock = Lock()

DATA_PATH = Path(__file__).with_name("trips.json")

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    global trips
    trips = load_trips(DATA_PATH)
    yield


app = FastAPI(
    title="Travel Planner",
    lifespan=lifespan,
)

trips: dict[UUID, Trip] = {}

@app.post("/trips", response_model=Trip, status_code=201)
def create_trip(payload: TripCreate) -> Trip:
    trip = Trip(id=uuid4(), **payload.model_dump())

    with state_lock:
        _commit_trip(trip)

    return trip

@app.post("/trips/{trip_id}/activities", response_model=Activity, status_code=201)
def add_activity(trip_id: UUID, payload: ActivityCreate) -> Activity:
    with state_lock:
        trip = trips.get(trip_id)
        if trip is None:
            raise HTTPException(
                status_code=404,
                detail="Trip not found",
            )

        if not trip.start_date <= payload.activity_date <= trip.end_date:
            raise HTTPException(
                status_code=422,
                detail="Activity date must fall within the trip dates",
            )

        activity = Activity(
            id=uuid4(),
            **payload.model_dump(),
        )

        updated_trip = trip.model_copy(deep=True)
        updated_trip.activities.append(activity)
        _commit_trip(updated_trip)

        return activity

@app.get("/trips", response_model=list[Trip])
def list_trips() -> list[Trip]:
    return list(trips.values())

@app.get("/trips/count", response_model=dict[str, int])
def count_trips() -> dict[str, int]:
    return {"count": len(trips)}

@app.get("/trips/{trip_id}", response_model=Trip)
def get_trip(trip_id: UUID) -> Trip:
    trip = trips.get(trip_id)

    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    return trip

@app.get("/trips/{trip_id}/budget", response_model=dict[str, int], status_code=200)
def get_budget(trip_id: UUID) -> dict[str, int]:
    trip = trips.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    planned_cost = calculate_planned_cost(trip)
    budget = trip.budget_cents
    remaining_cost = budget - planned_cost
    return {"budget_cents": budget, "planned_cost_cents": planned_cost, "remaining_cents": remaining_cost}

@app.get("/trips/{trip_id}/activities", response_model=list[Activity], status_code=200)
def get_activities(trip_id: UUID) -> list[Activity]:
    trip = trips.get(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    activities = trip.activities
    return activities

@app.delete("/trips/{trip_id}/activities/{activity_id}", status_code=204)
def delete_activity(trip_id: UUID, activity_id: UUID) -> Response:
    with state_lock:
        trip = trips.get(trip_id)
        if trip is None:
            raise HTTPException(
                status_code=404,
                detail="Trip not found",
            )

        for index, activity in enumerate(trip.activities):
            if activity.id == activity_id:
                updated_trip = trip.model_copy(deep=True)
                del updated_trip.activities[index]
                _commit_trip(updated_trip)

                # Stop here after successfully saving the deletion.
                return Response(status_code=204)

        raise HTTPException(
            status_code=404,
            detail="Activity not found",
        )


def _commit_trip(trip: Trip) -> None:
    global trips

    updated_trips = trips.copy()
    updated_trips[trip.id] = trip

    # Save to the path configured in main.py.
    save_trips(updated_trips, DATA_PATH)

    # Update memory only after saving succeeds.
    trips = updated_trips

