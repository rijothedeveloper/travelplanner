"""Add persistent itinerary jobs."""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE itinerary_jobs (
            id UUID PRIMARY KEY,
            trip_id UUID NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
            owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            status TEXT NOT NULL DEFAULT 'queued'
                CHECK (status IN ('queued', 'running', 'completed', 'failed')),
            input_snapshot JSONB NOT NULL
                CHECK (jsonb_typeof(input_snapshot) = 'object'),
            result JSONB,
            error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ
        )
        """
    )
    op.execute(
        """
        CREATE INDEX itinerary_jobs_queue_idx
        ON itinerary_jobs (created_at, id)
        WHERE status = 'queued'
        """
    )
    op.execute("CREATE INDEX itinerary_jobs_owner_idx ON itinerary_jobs (owner_id)")


def downgrade() -> None:
    op.drop_table("itinerary_jobs")