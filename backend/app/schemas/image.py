"""Image schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ImageSplit = Literal["train", "val", "test", "unassigned"]
ImageStatus = Literal["pending", "labeled", "reviewed", "skipped"]


class Image(BaseModel):
    id: UUID
    dataset_id: UUID
    storage_path: str
    width: int
    height: int
    sha256: str
    original_name: str | None
    content_type: str
    bytes: int | None
    split: ImageSplit
    status: ImageStatus
    captured_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ImageWithUrl(Image):
    signed_url: str | None = None
    thumb_url: str | None = None


class ImageUpdate(BaseModel):
    status: ImageStatus | None = None
    split: ImageSplit | None = None


class BulkUploadResult(BaseModel):
    uploaded: list[Image]
    skipped: list[dict] = Field(
        default_factory=list,
        description="Files skipped due to duplicate sha256 or validation.",
    )
