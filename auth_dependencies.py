from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError

from auth_models import UserPublic
from tokens import read_access_token
import user_repository


bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer),
    ],
) -> UserPublic:
    authentication_error = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise authentication_error

    try:
        user_id = read_access_token(credentials.credentials)
    except InvalidTokenError:
        raise authentication_error from None

    user = user_repository.get_user_by_id(user_id)

    if user is None:
        raise authentication_error

    return user