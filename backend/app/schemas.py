"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Detection(BaseModel):
    label: str = Field(..., description="Defect class label.")
    raw_label: str = Field(
        ..., description="Original model class name before demo remap."
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: list[float] = Field(
        ..., min_length=4, max_length=4,
        description="Bounding box in pixel coordinates [x1, y1, x2, y2].",
    )


class InspectionResult(BaseModel):
    detections: list[Detection]
    image_size: list[int] = Field(..., min_length=2, max_length=2)
    inference_ms: float
    model: str
    demo_mode: bool = Field(
        default=True,
        description="True while the generic pretrained model is used.",
    )


class HealthResponse(BaseModel):
    status: str
    model: str
    demo_mode: bool
