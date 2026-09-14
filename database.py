import os
from typing import Any

import psycopg
from psycopg.rows import dict_row


def connect_db() -> psycopg.Connection[dict[str, Any]]:
    database_url = os.getenv("TRAVEL_DATABASE_URL")
    if database_url is None or not database_url.strip():
        raise RuntimeError("TRAVEL_DATABASE_URL must be set")

    return psycopg.connect(
        database_url,
        row_factory=dict_row,
        connect_timeout=5,
    )