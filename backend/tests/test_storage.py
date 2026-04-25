"""Storage helpers — pure functions, no Supabase calls."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

from app.core.storage import (
    image_dimensions,
    make_thumbnail,
    raw_image_path,
    sha256_bytes,
    thumb_image_path,
)


def _png_bytes(w: int, h: int) -> bytes:
    img = Image.new("RGB", (w, h), color=(10, 20, 30))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_sha256_is_stable():
    assert sha256_bytes(b"abc") == sha256_bytes(b"abc")
    assert sha256_bytes(b"abc") != sha256_bytes(b"abd")


def test_storage_paths():
    assert raw_image_path("ds", "img") == "raw/ds/img.jpg"
    assert thumb_image_path("ds", "img") == "thumbs/ds/img.jpg"


def test_image_dimensions():
    data = _png_bytes(800, 600)
    assert image_dimensions(data) == (800, 600)


def test_make_thumbnail_max_side():
    data = _png_bytes(1024, 768)
    thumb = make_thumbnail(data)
    w, h = image_dimensions(thumb)
    assert max(w, h) <= 320
    assert min(w, h) > 0
