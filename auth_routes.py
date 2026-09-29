from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from auth_dependencies import get_current_user
from auth_models import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserPublic,
)
from security import hash_password, verify_password
from tokens import create_access_token
import user_repository


router = APIRouter(prefix="/auth", tags=["auth"])

_DUMMY_HASH = hash_password("dummy password used only for timing")


@router.post("/register", response_model=UserPublic, status_code=201)
def register_user(payload: UserCreate) -> UserPublic:
    try:
        return user_repository.create_user(payload)
    except user_repository.EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        ) from None


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, response: Response) -> TokenResponse:
    user = user_repository.get_user_credentials(str(payload.email))

    encoded_hash = (
        user.password_hash.get_secret_value()
        if user is not None
        else _DUMMY_HASH
    )

    password_matches = verify_password(
        payload.password.get_secret_value(),
        encoded_hash,
    )

    if user is None or not password_matches:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    return TokenResponse(
        access_token=create_access_token(user.id),
    )


@router.get("/me", response_model=UserPublic)
def read_me(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> UserPublic:
    return current_user