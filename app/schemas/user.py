"""User request and response schemas."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    """Schema for user registration."""

    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[A-Za-z0-9_]+$",
    )
    password: str = Field(min_length=8, max_length=72)

    @field_validator("username", mode="before")
    @classmethod
    def trim_username(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class UserLogin(BaseModel):
    """Schema for user login credentials."""

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)

    @field_validator("username", mode="before")
    @classmethod
    def trim_username(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class UserResponse(BaseModel):
    """Public user representation returned by API endpoints."""

    model_config = ConfigDict(from_attributes=False)

    id: int
    username: str
    created_at: str


class TokenResponse(BaseModel):
    """JWT access token response schema."""

    access_token: str
    token_type: str = "bearer"
