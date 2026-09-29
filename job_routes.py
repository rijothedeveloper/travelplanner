from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError

from auth_dependencies import get_current_user
from auth_models import UserPublic
from job_models import JobPublic
import job_repository


router = APIRouter(tags=["itinerary jobs"])
CurrentUser = Annotated[UserPublic, Depends(get_current_user)]


@router.post(
    "/trips/{trip_id}/itinerary-jobs",
    response_model=JobPublic,
    status_code=202,
)
def submit_itinerary_job(
    trip_id: UUID,
    current_user: CurrentUser,
    response: Response,
) -> JobPublic:
    try:
        job = job_repository.create_job(trip_id, owner_id=current_user.id)
    except job_repository.PlanningTripNotFoundError:
        raise HTTPException(status_code=404, detail="Trip not found") from None
    except ValidationError:
        raise HTTPException(
            status_code=422,
            detail="Trip is not eligible for planning; use valid dates spanning at most 14 days",
        ) from None

    response.headers["Location"] = f"/itinerary-jobs/{job.id}"
    response.headers["Cache-Control"] = "no-store"
    return job


@router.get("/itinerary-jobs/{job_id}", response_model=JobPublic)
def read_itinerary_job(
    job_id: UUID,
    current_user: CurrentUser,
    response: Response,
) -> JobPublic:
    job = job_repository.get_job(job_id, owner_id=current_user.id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    response.headers["Cache-Control"] = "no-store"
    return job

