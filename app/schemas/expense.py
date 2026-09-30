"""Expense request and response schemas."""

from datetime import date
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExpenseCreate(BaseModel):
    """Schema for creating a new expense."""

    title: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0, le=10_000_000)
    category_id: int = Field(ge=1)
    expense_date: date
    note: str | None = Field(default=None, max_length=300)

    @field_validator("title", mode="before")
    @classmethod
    def trim_title(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("amount")
    @classmethod
    def round_amount(cls, value: float) -> float:
        return round(value, 2)

    @field_validator("expense_date")
    @classmethod
    def validate_date_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("expense_date cannot be in the future")
        return value

    @field_validator("note", mode="before")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed if trimmed else None
        return value


class ExpenseUpdate(ExpenseCreate):
    """Schema for replacing/updating an existing expense."""

    pass


class ExpenseResponse(BaseModel):
    """Expense representation returned by API endpoints."""

    model_config = ConfigDict(from_attributes=False)

    id: int
    title: str
    amount: float
    category_id: int
    category_name: str
    expense_date: date
    note: str | None = None
    created_at: str
    updated_at: str


class ExpenseListResponse(BaseModel):
    """Envelope response for paginated expense listings."""

    items: list[ExpenseResponse]
    total: int
    limit: int
    offset: int
