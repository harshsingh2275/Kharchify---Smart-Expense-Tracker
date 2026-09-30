"""Monthly summary response schemas."""

from pydantic import BaseModel, ConfigDict


class CategoryTotal(BaseModel):
    """Spending total for a specific category within a month."""

    model_config = ConfigDict(from_attributes=False)

    category_id: int
    category_name: str
    count: int
    total: float


class MonthlySummaryResponse(BaseModel):
    """Monthly spending summary schema."""

    model_config = ConfigDict(from_attributes=False)

    month: str
    total_spent: float
    expense_count: int
    by_category: list[CategoryTotal]
