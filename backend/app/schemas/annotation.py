"""Annotation schemas (YOLO-normalized bounding boxes)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

AnnotationSource = Literal["human", "model", "import"]


class AnnotationCreate(BaseModel):
    class_name: str = Field(..., min_length=1)
    x_center: float = Field(..., ge=0.0, le=1.0)
    y_center: float = Field(..., ge=0.0, le=1.0)
    width: float = Field(..., gt=0.0, le=1.0)
    height: float = Field(..., gt=0.0, le=1.0)
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    source: AnnotationSource = "human"


class Annotation(AnnotationCreate):
    id: UUID
    image_id: UUID
    created_at: datetime
    updated_at: datetime
