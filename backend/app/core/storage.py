"""Supabase Storage helpers.

Thin wrappers around the Supabase storage client so routers don't have to
know about the underlying bucket layout.
"""

from __future__ import annotations

import hashlib
from datetime import timedelta
from io import BytesIO

from PIL import Image

from . import config
from .supabase import get_client


THUMB_MAX_SIDE = 320
SIGNED_URL_TTL_SECONDS = 3600


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def raw_image_path(dataset_id: str, image_id: str, ext: str = "jpg") -> str:
    return f"raw/{dataset_id}/{image_id}.{ext}"


def thumb_image_path(dataset_id: str, image_id: str, ext: str = "jpg") -> str:
    return f"thumbs/{dataset_id}/{image_id}.{ext}"


def make_thumbnail(image_bytes: bytes) -> bytes:
    """Return a ~320px max-side JPEG thumbnail."""
    img = Image.open(BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((THUMB_MAX_SIDE, THUMB_MAX_SIDE))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def upload_image(
    *,
    path: str,
    data: bytes,
    content_type: str = "image/jpeg",
    bucket: str | None = None,
) -> None:
    client = get_client()
    if client is None:
        raise RuntimeError("Supabase is not configured.")
    bucket_name = bucket or config.SUPABASE_BUCKET_IMAGES
    client.storage.from_(bucket_name).upload(
        path=path,
        file=data,
        file_options={"content-type": content_type, "upsert": "true"},
    )


def signed_url(path: str, bucket: str | None = None) -> str:
    client = get_client()
    if client is None:
        raise RuntimeError("Supabase is not configured.")
    bucket_name = bucket or config.SUPABASE_BUCKET_IMAGES
    resp = client.storage.from_(bucket_name).create_signed_url(
        path, SIGNED_URL_TTL_SECONDS,
    )
    return resp.get("signedURL") or resp.get("signed_url") or ""


def image_dimensions(image_bytes: bytes) -> tuple[int, int]:
    img = Image.open(BytesIO(image_bytes))
    return img.width, img.height
