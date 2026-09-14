"""Create users."""

from alembic import op


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX users_email_unique
        ON users (lower(email))
        """
    )


def downgrade() -> None:
    op.drop_table("users")