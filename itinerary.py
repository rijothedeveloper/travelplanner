from datetime import date, timedelta
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


MAX_PLANNING_DAYS = 14


class PlanningInput(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        frozen=True,
    )

    destination: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        day_count = (self.end_date - self.start_date).days + 1
        if day_count > MAX_PLANNING_DAYS:
            raise ValueError("Itinerary planning supports at most 14 days")
        return self


class ItineraryDay(BaseModel):
    day_date: date
    suggestion: str


class ItineraryDraft(BaseModel):
    destination: str
    days: list[ItineraryDay]


def generate_itinerary(payload: PlanningInput) -> ItineraryDraft:
    day_count = (payload.end_date - payload.start_date).days + 1
    middle_day_themes = (
        "Explore a local neighborhood",
        "Choose a cultural attraction to visit",
        "Plan an outdoor activity suited to the weather",
    )
    days: list[ItineraryDay] = []

    for offset in range(day_count):
        if day_count == 1:
            suggestion = "Choose one main activity and allow time for travel"
        elif offset == 0:
            suggestion = "Arrive, settle in, and explore the surrounding area"
        elif offset == day_count - 1:
            suggestion = "Allow time for a final outing and departure"
        else:
            suggestion = middle_day_themes[(offset - 1) % len(middle_day_themes)]

        days.append(
            ItineraryDay(
                day_date=payload.start_date + timedelta(days=offset),
                suggestion=suggestion,
            )
        )

    return ItineraryDraft(destination=payload.destination, days=days)