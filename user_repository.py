# user_repository.py
from psycopg.errors import UniqueViolation

from auth_models import UserCreate, UserPublic
from database import connect_db
from security import hash_password
from uuid import UUID

from auth_models import UserCredentials


class EmailAlreadyRegisteredError(Exception):
    pass


def create_user(payload: UserCreate) -> UserPublic:
    encoded_hash = hash_password(payload.password.get_secret_value())

    try:
        with connect_db() as connection:
            row = connection.execute(
                """
                INSERT INTO users (email, password_hash)
                VALUES (%s, %s)
                RETURNING id, email
                """,
                (str(payload.email), encoded_hash),
            ).fetchone()

            user = UserPublic.model_validate(row)
    except UniqueViolation as exc:
        if exc.diag.constraint_name == "users_email_unique":
            raise EmailAlreadyRegisteredError() from None
        raise

    return user

def get_user_credentials(email: str) -> UserCredentials | None:
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT id, email, password_hash
            FROM users
            WHERE lower(email) = lower(%s)
            """,
            (email,),
        ).fetchone()

        user = (
            UserCredentials.model_validate(row)
            if row is not None
            else None
        )

    return user


def get_user_by_id(user_id: UUID) -> UserPublic | None:
    with connect_db() as connection:
        row = connection.execute(
            """
            SELECT id, email
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        ).fetchone()

        user = (
            UserPublic.model_validate(row)
            if row is not None
            else None
        )

    return user