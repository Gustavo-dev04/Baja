"""Public inspection endpoints — contracts unchanged from MVP."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..core.config import MODEL_WEIGHTS
from ..inference import get_detector
from ..schemas.inspection import HealthResponse, InspectionResult

router = APIRouter(tags=["inspect"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    detector = get_detector()
    return HealthResponse(
        status="ok",
        model=MODEL_WEIGHTS,
        demo_mode=detector.demo_mode,
    )


@router.post("/inspect", response_model=InspectionResult)
async def inspect(file: UploadFile = File(...)) -> InspectionResult:
    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type: {file.content_type!r}",
        )
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file upload.")

    detector = get_detector()
    return detector.detect(data)
