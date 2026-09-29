


"""Add trip owners while allowing legacy trips to be assigned."""

from alembic import op


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE trips ADD COLUMN owner_id UUID")
    op.execute(
        """
        ALTER TABLE trips
        ADD CONSTRAINT trips_owner_fk
        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE RESTRICT
        """
    )
    op.execute("CREATE INDEX trips_owner_idx ON trips (owner_id)")


def downgrade() -> None:
    op.drop_index("trips_owner_idx", table_name="trips")
    op.drop_constraint("trips_owner_fk", "trips", type_="foreignkey")
    op.drop_column("trips", "owner_id")