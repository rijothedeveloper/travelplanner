"""Create trips and activities."""

from alembic import op


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE trips2 (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title TEXT NOT NULL,
            destination TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            travelers INTEGER NOT NULL,
            budget_cents BIGINT NOT NULL,

            CONSTRAINT trips_travelers_positive
                CHECK (travelers >= 1),

            CONSTRAINT trips_budget_nonnegative
                CHECK (budget_cents >= 0),

            CONSTRAINT trips_dates_ordered
                CHECK (end_date >= start_date)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE activities2 (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            trip_id UUID NOT NULL,
            title TEXT NOT NULL,
            activity_date DATE NOT NULL,
            cost_cents BIGINT NOT NULL,

            CONSTRAINT activities_trip_fk
                FOREIGN KEY (trip_id)
                REFERENCES trips(id)
                ON DELETE CASCADE,

            CONSTRAINT activities_cost_nonnegative
                CHECK (cost_cents >= 0)
        )
        """
    )


def downgrade() -> None:
    op.drop_table("activities")
    op.drop_table("trips")