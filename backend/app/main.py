"""FastAPI application — mounts public + admin routers."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import ALLOWED_ORIGINS
from .inference import get_detector
from .routers import annotations, auth, datasets, images, inspect

app = FastAPI(
    title="Baja Paint Inspection API",
    description=(
        "Serves YOLO inference for paint-defect detection on BAJA-style "
        "chassis photographed inside the inspection chamber."
    ),
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Public — unchanged contracts.
app.include_router(inspect.router)

# Admin / data plane.
app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(images.router)
app.include_router(annotations.router)


@app.on_event("startup")
def _warmup() -> None:
    # Load weights eagerly so the first /inspect request is fast.
    get_detector()
