from datetime import date
from typing import Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

class ActivityCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str = Field(min_length=1, max_length=100)
    activity_date: date
    cost_cents: int = Field(ge=0, le=9_223_372_036_854_775_807, strict=True)


class Activity(ActivityCreate):
    id: UUID

class TripCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=80, description="The title of the trip")
    start_date: date
    end_date: date
    destination: str = Field(min_length=1, max_length=100)
    travelers: int = Field(ge=1, le=2_147_483_647, strict=True)
    budget_cents: int = Field(ge=0, le=9_223_372_036_854_775_807, strict=True)

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class Trip(TripCreate):
    id: UUID
    activities: list[Activity] = Field(default_factory=list)

class TripSummary(TripCreate):
    id: UUID