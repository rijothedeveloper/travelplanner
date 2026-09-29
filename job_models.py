from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from itinerary import ItineraryDraft, PlanningInput


class JobPublic(BaseModel):
    id: UUID
    trip_id: UUID
    status: Literal["queued", "running", "completed", "failed"]
    input_snapshot: PlanningInput
    result: ItineraryDraft | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    attempts: int
    available_at: datetime
    lease_expires_at: datetime | None