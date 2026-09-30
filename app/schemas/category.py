"""Category response schema."""

from pydantic import BaseModel, ConfigDict


class CategoryResponse(BaseModel):
    """Category representation returned by API endpoints."""

    model_config = ConfigDict(from_attributes=False)

    id: int
    name: str
