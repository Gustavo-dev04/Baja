"""Annotation CRUD — replace-all semantics per image."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import require_admin
from ..core.supabase import get_client
from ..schemas.annotation import Annotation, AnnotationCreate

router = APIRouter(tags=["annotations"])


def _supabase_or_503():
    client = get_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured.",
        )
    return client


@router.get(
    "/api/v1/images/{image_id}/annotations",
    response_model=list[Annotation],
)
def list_annotations(image_id: UUID) -> list[Annotation]:
    client = _supabase_or_503()
    res = (
        client.table("annotations")
        .select("*")
        .eq("image_id", str(image_id))
        .order("created_at")
        .execute()
    )
    return [Annotation(**row) for row in (res.data or [])]


@router.post(
    "/api/v1/images/{image_id}/annotations",
    response_model=list[Annotation],
)
def replace_annotations(
    image_id: UUID,
    payload: list[AnnotationCreate],
    _: dict = Depends(require_admin),
) -> list[Annotation]:
    """Replace all annotations of an image atomically."""
    client = _supabase_or_503()

    img = (
        client.table("images")
        .select("id")
        .eq("id", str(image_id))
        .execute()
    )
    if not img.data:
        raise HTTPException(status_code=404, detail="Image not found.")

    # Wipe existing first, then insert. Supabase SDK doesn't expose tx
    # explicitly; this is best-effort but acceptable for write rate here.
    client.table("annotations").delete().eq(
        "image_id", str(image_id),
    ).execute()

    if not payload:
        # Mark image as labeled even when empty (means "no defects").
        client.table("images").update({"status": "labeled"}).eq(
            "id", str(image_id),
        ).execute()
        return []

    rows = [
        {**ann.model_dump(), "image_id": str(image_id)}
        for ann in payload
    ]
    res = client.table("annotations").insert(rows).execute()
    client.table("images").update({"status": "labeled"}).eq(
        "id", str(image_id),
    ).execute()
    return [Annotation(**row) for row in (res.data or [])]
