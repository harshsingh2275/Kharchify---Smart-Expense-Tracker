"""Categories router."""

import logging
import sqlite3

from fastapi import APIRouter, Depends

from app.dependencies import get_db
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Categories"])


@router.get("/categories", response_model=list[CategoryResponse], summary="List categories")
def list_categories(conn: sqlite3.Connection = Depends(get_db)) -> list[CategoryResponse]:
    """Return all available expense categories."""
    repo = CategoryRepository(conn)
    return [CategoryResponse(**c) for c in repo.list_all()]
