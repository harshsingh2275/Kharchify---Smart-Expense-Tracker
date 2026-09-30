"""Monthly summary endpoint."""

import logging
import sqlite3
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_current_user, get_db
from app.repositories.expense_repository import ExpenseRepository
from app.schemas.summary import CategoryTotal, MonthlySummaryResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Summary"])

# Month must be YYYY-MM with a valid month number
MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.get("/summary", response_model=MonthlySummaryResponse, summary="Monthly summary")
def monthly_summary(
    month: str | None = Query(
        default=None,
        pattern=MONTH_PATTERN,
        description="Month to summarise, in YYYY-MM format. Defaults to current UTC month.",
    ),
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> MonthlySummaryResponse:
    """Return the current user's spending summary for a given month."""
    if month is None:
        month = datetime.now(timezone.utc).strftime("%Y-%m")

    user_id = current_user["id"]
    repo = ExpenseRepository(conn)
    summary = repo.monthly_summary(user_id, month)

    return MonthlySummaryResponse(
        month=month,
        total_spent=summary["total_spent"],
        expense_count=summary["expense_count"],
        by_category=[CategoryTotal(**c) for c in summary["by_category"]],
    )
