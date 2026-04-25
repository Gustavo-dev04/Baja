"""Dataset schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    classes: list[str] | None = None


class DatasetUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    classes: list[str] | None = None
    is_active: bool | None = None


class Dataset(BaseModel):
    id: UUID
    name: str
    description: str | None
    classes: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DatasetDetail(Dataset):
    image_count: int = 0
    labeled_count: int = 0
