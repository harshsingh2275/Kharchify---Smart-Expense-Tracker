"""Authentication endpoints: register, login, me."""

import logging
import sqlite3

from fastapi import APIRouter, Depends

from app.dependencies import get_current_user, get_db
from app.exceptions import AuthenticationError
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.security import create_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Auth"])


@router.post("/auth/register", response_model=UserResponse, status_code=201, summary="Register a new user")
def register(data: UserCreate, conn: sqlite3.Connection = Depends(get_db)) -> UserResponse:
    """Create a new user account. Returns the created user (no token)."""
    repo = UserRepository(conn)
    # ConflictError from the repository propagates directly (handled globally)
    user = repo.create(data.username, hash_password(data.password))
    logger.info("User registered: %s", data.username)
    return UserResponse(**user)


@router.post("/auth/login", response_model=TokenResponse, summary="Login and receive a JWT")
def login(data: UserLogin, conn: sqlite3.Connection = Depends(get_db)) -> TokenResponse:
    """Authenticate with username and password. Returns an access token on success."""
    repo = UserRepository(conn)
    user = repo.get_by_username(data.username)

    # Same error and log message for both unknown user and wrong password.
    # This prevents user enumeration.
    if user is None or not verify_password(data.password, user["password_hash"]):
        logger.warning("Failed login for username: %s", data.username)
        raise AuthenticationError("Incorrect username or password")

    token = create_access_token(user["id"])
    logger.info("User logged in: %s", data.username)
    return TokenResponse(access_token=token)


@router.get("/auth/me", response_model=UserResponse, summary="Get current user")
def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse(**current_user)
