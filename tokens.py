import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError


ALGORITHM = "HS256"
ISSUER = "travel-planner"
AUDIENCE = "travel-planner-api"
ACCESS_TOKEN_MINUTES = 15


def get_jwt_secret() -> str:
    secret = os.getenv("TRAVEL_JWT_SECRET", "")

    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError(
            "TRAVEL_JWT_SECRET must contain at least 32 bytes"
        )

    return secret


def create_access_token(user_id: UUID) -> str:
    now = datetime.now(UTC)

    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
            "iss": ISSUER,
            "aud": AUDIENCE,
        },
        get_jwt_secret(),
        algorithm=ALGORITHM,
    )


def read_access_token(token: str) -> UUID:
    payload = jwt.decode(
        token,
        get_jwt_secret(),
        algorithms=[ALGORITHM],
        issuer=ISSUER,
        audience=AUDIENCE,
        options={
            "require": ["sub", "iat", "exp", "iss", "aud"],
        },
    )

    subject = payload["sub"]

    if not isinstance(subject, str):
        raise InvalidTokenError("Invalid subject")

    try:
        return UUID(subject)
    except ValueError:
        raise InvalidTokenError("Invalid subject") from None