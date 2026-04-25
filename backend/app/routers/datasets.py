"""CRUD for datasets."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.auth import require_admin
from ..core.supabase import get_client
from ..schemas.dataset import (
    Dataset,
    DatasetCreate,
    DatasetDetail,
    DatasetUpdate,
)

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


def _supabase_or_503():
    client = get_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured.",
        )
    return client


@router.get("", response_model=list[Dataset])
def list_datasets() -> list[Dataset]:
    client = _supabase_or_503()
    res = (
        client.table("datasets")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return [Dataset(**row) for row in (res.data or [])]


@router.post("", response_model=Dataset, status_code=status.HTTP_201_CREATED)
def create_dataset(
    payload: DatasetCreate, _: dict = Depends(require_admin),
) -> Dataset:
    client = _supabase_or_503()
    insert = payload.model_dump(exclude_none=True)
    res = client.table("datasets").insert(insert).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Insert returned no row.")
    return Dataset(**res.data[0])


@router.get("/{dataset_id}", response_model=DatasetDetail)
def get_dataset(dataset_id: UUID) -> DatasetDetail:
    client = _supabase_or_503()
    res = (
        client.table("datasets")
        .select("*")
        .eq("id", str(dataset_id))
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    images = (
        client.table("images")
        .select("status", count="exact")
        .eq("dataset_id", str(dataset_id))
        .execute()
    )
    image_count = images.count or 0
    labeled_count = sum(
        1 for row in (images.data or []) if row.get("status") == "labeled"
    )

    return DatasetDetail(
        **res.data, image_count=image_count, labeled_count=labeled_count,
    )


@router.patch("/{dataset_id}", response_model=Dataset)
def update_dataset(
    dataset_id: UUID,
    payload: DatasetUpdate,
    _: dict = Depends(require_admin),
) -> Dataset:
    client = _supabase_or_503()
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")

    res = (
        client.table("datasets")
        .update(updates)
        .eq("id", str(dataset_id))
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return Dataset(**res.data[0])


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: UUID, _: dict = Depends(require_admin),
) -> None:
    client = _supabase_or_503()
    # Soft delete: mark inactive instead of removing.
    res = (
        client.table("datasets")
        .update({"is_active": False})
        .eq("id", str(dataset_id))
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Dataset not found.")
