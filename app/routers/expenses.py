"""Expense CRUD endpoints."""

import logging
import sqlite3
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.dependencies import get_current_user, get_db
from app.exceptions import BadRequestError, NotFoundError
from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseResponse,
    ExpenseUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Expenses"])


def _to_response(row: dict) -> ExpenseResponse:
    return ExpenseResponse(**row)


@router.post("/expenses", response_model=ExpenseResponse, status_code=201, summary="Create expense")
def create_expense(
    data: ExpenseCreate,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ExpenseResponse:
    """Create a new expense for the current user."""
    user_id = current_user["id"]
    cat_repo = CategoryRepository(conn)
    if not cat_repo.exists(data.category_id):
        raise BadRequestError("Category does not exist")
    repo = ExpenseRepository(conn)
    row = repo.create(user_id, data)
    logger.info("Expense created: id=%d user_id=%d", row["id"], user_id)
    return _to_response(row)


@router.get("/expenses", response_model=ExpenseListResponse, summary="List expenses")
def list_expenses(
    category_id: int | None = Query(default=None, ge=1),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ExpenseListResponse:
    """List the current user's expenses with optional filters and pagination."""
    if start_date and end_date and start_date > end_date:
        raise BadRequestError("start_date must not be after end_date")
    user_id = current_user["id"]
    repo = ExpenseRepository(conn)
    items, total = repo.list(user_id, category_id, start_date, end_date, limit, offset)
    return ExpenseListResponse(
        items=[_to_response(r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse, summary="Get expense")
def get_expense(
    expense_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ExpenseResponse:
    """Return a single expense belonging to the current user."""
    user_id = current_user["id"]
    repo = ExpenseRepository(conn)
    row = repo.get(user_id, expense_id)
    if row is None:
        raise NotFoundError("Expense not found")
    return _to_response(row)


@router.put("/expenses/{expense_id}", response_model=ExpenseResponse, summary="Update expense")
def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ExpenseResponse:
    """Replace an expense with new data."""
    user_id = current_user["id"]
    cat_repo = CategoryRepository(conn)
    if not cat_repo.exists(data.category_id):
        raise BadRequestError("Category does not exist")
    repo = ExpenseRepository(conn)
    row = repo.update(user_id, expense_id, data)
    if row is None:
        raise NotFoundError("Expense not found")
    logger.info("Expense updated: id=%d user_id=%d", expense_id, user_id)
    return _to_response(row)


@router.delete("/expenses/{expense_id}", status_code=204, summary="Delete expense")
def delete_expense(
    expense_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> Response:
    """Delete an expense. Returns 204 on success."""
    user_id = current_user["id"]
    repo = ExpenseRepository(conn)
    if not repo.delete(user_id, expense_id):
        raise NotFoundError("Expense not found")
    logger.info("Expense deleted: id=%d user_id=%d", expense_id, user_id)
    return Response(status_code=204)
