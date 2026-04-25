"""Pydantic schemas re-exported for convenience.

Legacy imports (`from app.schemas import InspectionResult`) keep working
while new code can reach domain-specific modules directly.
"""

from .annotation import Annotation, AnnotationCreate, AnnotationSource
from .auth import LoginRequest, TokenResponse
from .dataset import Dataset, DatasetCreate, DatasetDetail, DatasetUpdate
from .image import (
    BulkUploadResult,
    Image,
    ImageSplit,
    ImageStatus,
    ImageUpdate,
    ImageWithUrl,
)
from .inspection import Detection, HealthResponse, InspectionResult

__all__ = [
    "Annotation",
    "AnnotationCreate",
    "AnnotationSource",
    "BulkUploadResult",
    "Dataset",
    "DatasetCreate",
    "DatasetDetail",
    "DatasetUpdate",
    "Detection",
    "HealthResponse",
    "Image",
    "ImageSplit",
    "ImageStatus",
    "ImageUpdate",
    "ImageWithUrl",
    "InspectionResult",
    "LoginRequest",
    "TokenResponse",
]
