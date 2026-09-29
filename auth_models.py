from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
)


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    email: EmailStr
    password: SecretStr = Field(min_length=15, max_length=128, strict=True)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class UserPublic(BaseModel):
    id: UUID
    email: EmailStr

class UserLogin(UserCreate):
    password: SecretStr = Field(
        min_length=1,
        max_length=128,
        strict=True,
    )


class UserCredentials(UserPublic):
    password_hash: SecretStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"