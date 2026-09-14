from uuid import UUID

from fastapi import FastAPI, HTTPException, Response

from models import Activity, ActivityCreate, Trip, TripCreate
from services import calculate_planned_cost
import trip_repository
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from auth_routes import router as auth_router


app = FastAPI(title="Travel Planner")

app.include_router(auth_router)


def _get_trip_or_404(trip_id: UUID) -> Trip:
    trip = trip_repository.get_trip(trip_id)

    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")

    return trip


@app.post("/trips", response_model=Trip, status_code=201)
def create_trip(payload: TripCreate) -> Trip:
    return trip_repository.create_trip(payload)


@app.get("/trips", response_model=list[Trip])
def list_trips() -> list[Trip]:
    return trip_repository.list_trips()


@app.get("/trips/count", response_model=dict[str, int])
def count_trips() -> dict[str, int]:
    return {"count": trip_repository.count_trips()}


@app.get("/trips/{trip_id}", response_model=Trip)
def get_trip(trip_id: UUID) -> Trip:
    return _get_trip_or_404(trip_id)


@app.get("/trips/{trip_id}/activities", response_model=list[Activity])
def get_activities(trip_id: UUID) -> list[Activity]:
    return _get_trip_or_404(trip_id).activities


@app.get("/trips/{trip_id}/budget", response_model=dict[str, int])
def get_budget(trip_id: UUID) -> dict[str, int]:
    trip = _get_trip_or_404(trip_id)
    planned_cost = calculate_planned_cost(trip)

    return {
        "budget_cents": trip.budget_cents,
        "planned_cost_cents": planned_cost,
        "remaining_cents": trip.budget_cents - planned_cost,
    }


@app.post(
    "/trips/{trip_id}/activities",
    response_model=Activity,
    status_code=201,
)
def add_activity(trip_id: UUID, payload: ActivityCreate) -> Activity:
    try:
        return trip_repository.add_activity(trip_id, payload)
    except trip_repository.TripNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        ) from None
    except trip_repository.ActivityDateError:
        raise HTTPException(
            status_code=422,
            detail="Activity date must fall within the trip dates",
        ) from None


@app.delete(
    "/trips/{trip_id}/activities/{activity_id}",
    status_code=204,
)
def delete_activity(trip_id: UUID, activity_id: UUID) -> Response:
    try:
        trip_repository.delete_activity(trip_id, activity_id)
    except trip_repository.TripNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Trip not found",
        ) from None
    except trip_repository.ActivityNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Activity not found",
        ) from None

    return Response(status_code=204)

@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {
                    "loc": error["loc"],
                    "msg": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ]
        },
    )