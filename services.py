from models import Trip


def calculate_planned_cost(trip: Trip) -> int:
    total = 0

    for activity in trip.activities:
        total += activity.cost_cents

    return total
