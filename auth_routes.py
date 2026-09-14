# auth_routes.py
from fastapi import APIRouter, HTTPException

from auth_models import UserCreate, UserPublic
import user_repository


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=201)
def register_user(payload: UserCreate) -> UserPublic:
    try:
        return user_repository.create_user(payload)
    except user_repository.EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        ) from None