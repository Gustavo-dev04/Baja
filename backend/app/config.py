"""Backwards-compatible re-export of configuration.

Historically this module held every runtime knob. After the platform
expansion the real home is `app.core.config` — this shim keeps older
imports (`from app.config import ...`) working.
"""

from .core.config import (  # noqa: F401
    ALLOWED_ORIGINS,
    BASE_DIR,
    CONF_THRESHOLD,
    DEMO_CLASS_MAP,
    MODELS_DIR,
    MODEL_WEIGHTS,
    PAINT_DEFECT_CLASSES,
)
