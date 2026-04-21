"""Runtime configuration for the inspection backend."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"

# YOLO weights. Defaults to the smallest Ultralytics model (COCO-pretrained).
# Replace with a fine-tuned checkpoint once paint-defect training data exists.
MODEL_WEIGHTS = os.getenv("BAJA_MODEL_WEIGHTS", "yolov8n.pt")

# Confidence threshold for detections returned to the client.
CONF_THRESHOLD = float(os.getenv("BAJA_CONF_THRESHOLD", "0.25"))


def _parse_allowed_origins(value: str) -> list[str]:
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    if origins:
        return origins
    return ["http://localhost:3000", "http://127.0.0.1:3000"]


# CORS origins allowed to call the API.
ALLOWED_ORIGINS = _parse_allowed_origins(
    os.getenv(
        "BAJA_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
)

# Demo mapping: until a fine-tuned model exists, map generic COCO classes
# to paint-defect labels so the UI demonstrates the intended output.
# Keys are COCO class names, values are the label to surface in the UI.
DEMO_CLASS_MAP: dict[str, str] = {
    "person": "desgaste_generico",
    "bottle": "escorrimento",
    "cup": "bolha",
    "book": "falha_cobertura",
    "cell phone": "risco",
    "remote": "casca_de_laranja",
}

# Paint-defect classes expected once the model is fine-tuned.
PAINT_DEFECT_CLASSES = [
    "escorrimento",
    "casca_de_laranja",
    "falha_cobertura",
    "bolha",
    "risco",
    "oxidacao",
]
