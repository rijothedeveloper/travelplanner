"""Add bounded retries and claim leases."""
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE itinerary_jobs
        ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0
            CHECK (attempts BETWEEN 0 AND 3),
        ADD COLUMN available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        ADD COLUMN lease_expires_at TIMESTAMPTZ,
        ADD COLUMN claim_token UUID
    """)
    # Old jobs have no attempt history. Count their previous processing as one.
    op.execute("""
        UPDATE itinerary_jobs SET attempts = 1
        WHERE status IN ('running', 'completed', 'failed')
    """)
    # Old workers are stopped. Their unfinished claims can safely be requeued.
    op.execute("""
        UPDATE itinerary_jobs
        SET status = 'queued', started_at = NULL,
            finished_at = NULL, result = NULL, error = NULL
        WHERE status = 'running'
    """)
    op.execute("""
        ALTER TABLE itinerary_jobs ADD CONSTRAINT itinerary_jobs_lease_check
        CHECK (
            (status = 'running' AND claim_token IS NOT NULL
                AND lease_expires_at IS NOT NULL)
            OR
            (status <> 'running' AND claim_token IS NULL
                AND lease_expires_at IS NULL)
        )
    """)
    op.execute("DROP INDEX itinerary_jobs_queue_idx")
    op.execute("""
        CREATE INDEX itinerary_jobs_queue_idx
        ON itinerary_jobs (available_at, created_at, id)
        WHERE status = 'queued'
    """)
    op.execute("""
        CREATE INDEX itinerary_jobs_expired_idx
        ON itinerary_jobs (lease_expires_at, id)
        WHERE status = 'running'
    """)

def downgrade() -> None:
    op.execute("DROP INDEX itinerary_jobs_expired_idx")
    op.execute("DROP INDEX itinerary_jobs_queue_idx")
    op.execute("""
        CREATE INDEX itinerary_jobs_queue_idx
        ON itinerary_jobs (created_at, id) WHERE status = 'queued'
    """)
    op.execute("""
        ALTER TABLE itinerary_jobs
        DROP CONSTRAINT itinerary_jobs_lease_check,
        DROP COLUMN claim_token,
        DROP COLUMN lease_expires_at,
        DROP COLUMN available_at,
        DROP COLUMN attempts
    """)