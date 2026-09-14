# user_repository.py
from psycopg.errors import UniqueViolation

from auth_models import UserCreate, UserPublic
from database import connect_db
from security import hash_password


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