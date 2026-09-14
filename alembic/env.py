import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

raw_url = os.getenv("TRAVEL_DATABASE_URL")

if raw_url is None or not raw_url.strip():
    raise RuntimeError("TRAVEL_DATABASE_URL must be set")

url = make_url(raw_url)

if url.get_backend_name() != "postgresql":
    raise RuntimeError("TRAVEL_DATABASE_URL must use PostgreSQL")

url = url.set(drivername="postgresql+psycopg")


def run_migrations_offline() -> None:
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(
        url,
        poolclass=NullPool,
        connect_args={"connect_timeout": 5},
    )

    try:
        with engine.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=None,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()