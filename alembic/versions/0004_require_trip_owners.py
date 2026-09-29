"""require trip owners

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-16 08:32:27.060751

"""
# alembic/versions/0004_require_trip_owners.py
"""Require every trip to have an owner."""

from alembic import op


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE trips ALTER COLUMN owner_id SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE trips ALTER COLUMN owner_id DROP NOT NULL")