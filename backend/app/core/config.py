"""Runtime configuration for the inspection backend.

All runtime knobs live here. Everything is read from environment variables
with sane defaults, so the app works out of the box for local development
and adapts to production via HF Spaces secrets.
"""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "models"

# =========================================================
# Inference
# =========================================================

MODEL_WEIGHTS = os.getenv("BAJA_MODEL_WEIGHTS", "yolov8n.pt")
CONF_THRESHOLD = float(os.getenv("BAJA_CONF_THRESHOLD", "0.25"))
MODEL_CACHE_DIR = Path(os.getenv("BAJA_MODEL_CACHE_DIR", "/tmp/baja-models"))

# =========================================================
# CORS
# =========================================================

ALLOWED_ORIGINS = os.getenv(
    "BAJA_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")

# =========================================================
# Supabase
# =========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET_IMAGES = os.getenv("SUPABASE_BUCKET_IMAGES", "baja-images")
SUPABASE_BUCKET_MODELS = os.getenv("SUPABASE_BUCKET_MODELS", "baja-models")

# =========================================================
# Auth (Fase A: senha admin simples + JWT HS256)
# =========================================================

ADMIN_PASSWORD = os.getenv("BAJA_ADMIN_PASSWORD", "")
JWT_SECRET = os.getenv("BAJA_JWT_SECRET", "dev-only-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("BAJA_JWT_EXPIRE_HOURS", "24"))

# =========================================================
# HuggingFace Hub
# =========================================================

HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_MODEL_REPO = os.getenv("BAJA_HF_MODEL_REPO", "")

# =========================================================
# Feature flags
# =========================================================

# If Supabase is down or not configured, set to false to skip inspection
# persistence without redeploying. `/inspect` continues to work.
PERSIST_INSPECTIONS = (
    os.getenv("BAJA_PERSIST_INSPECTIONS", "true").lower() == "true"
)

# =========================================================
# Demo class remap (pre-fine-tuning)
# =========================================================

DEMO_CLASS_MAP: dict[str, str] = {
    "person": "desgaste_generico",
    "bottle": "escorrimento",
    "cup": "bolha",
    "book": "falha_cobertura",
    "cell phone": "risco",
    "remote": "casca_de_laranja",
}

PAINT_DEFECT_CLASSES = [
    "escorrimento",
    "casca_de_laranja",
    "falha_cobertura",
    "bolha",
    "risco",
    "oxidacao",
]


def supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)
