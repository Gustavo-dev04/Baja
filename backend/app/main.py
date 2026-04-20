"""FastAPI application exposing the paint-inspection endpoint."""

from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOWED_ORIGINS, MODEL_WEIGHTS
from .inference import get_detector
from .schemas import HealthResponse, InspectionResult

app = FastAPI(
    title="Baja Paint Inspection API",
    description=(
        "Serves YOLO inference for paint-defect detection on BAJA-style "
        "chassis photographed inside the inspection chamber."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _warmup() -> None:
    # Load weights eagerly so the first request is fast.
    get_detector()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    detector = get_detector()
    return HealthResponse(
        status="ok",
        model=MODEL_WEIGHTS,
        demo_mode=detector.demo_mode,
    )


@app.post("/inspect", response_model=InspectionResult)
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
