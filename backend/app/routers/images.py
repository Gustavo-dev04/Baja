"""Image upload and CRUD inside a dataset."""

from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from ..core.auth import require_admin
from ..core.storage import (
    image_dimensions,
    make_thumbnail,
    raw_image_path,
    sha256_bytes,
    signed_url,
    thumb_image_path,
    upload_image,
)
from ..core.supabase import get_client
from ..schemas.image import (
    BulkUploadResult,
    Image,
    ImageUpdate,
    ImageWithUrl,
)

router = APIRouter(tags=["images"])


def _supabase_or_503():
    client = get_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase is not configured.",
        )
    return client


@router.post(
    "/api/v1/datasets/{dataset_id}/images",
    response_model=BulkUploadResult,
    status_code=status.HTTP_201_CREATED,
)
async def upload_images(
    dataset_id: UUID,
    files: list[UploadFile] = File(...),
    _: dict = Depends(require_admin),
) -> BulkUploadResult:
    if len(files) > 20:
        raise HTTPException(
            status_code=400,
            detail="Up to 20 files per request.",
        )
    client = _supabase_or_503()

    # Confirm dataset exists.
    ds = (
        client.table("datasets")
        .select("id")
        .eq("id", str(dataset_id))
        .execute()
    )
    if not ds.data:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    uploaded: list[Image] = []
    skipped: list[dict] = []

    for upload in files:
        if upload.content_type is None or not upload.content_type.startswith(
            "image/",
        ):
            skipped.append(
                {
                    "name": upload.filename,
                    "reason": f"unsupported content type: {upload.content_type!r}",
                },
            )
            continue

        data = await upload.read()
        if not data:
            skipped.append({"name": upload.filename, "reason": "empty"})
            continue

        digest = sha256_bytes(data)
        existing = (
            client.table("images")
            .select("id")
            .eq("dataset_id", str(dataset_id))
            .eq("sha256", digest)
            .execute()
        )
        if existing.data:
            skipped.append({"name": upload.filename, "reason": "duplicate"})
            continue

        try:
            width, height = image_dimensions(data)
        except Exception as exc:  # noqa: BLE001
            skipped.append(
                {"name": upload.filename, "reason": f"decode failed: {exc}"},
            )
            continue

        image_id = str(uuid4())
        raw_path = raw_image_path(str(dataset_id), image_id)
        thumb_path = thumb_image_path(str(dataset_id), image_id)

        upload_image(
            path=raw_path, data=data, content_type=upload.content_type,
        )
        try:
            upload_image(
                path=thumb_path,
                data=make_thumbnail(data),
                content_type="image/jpeg",
            )
        except Exception:  # noqa: BLE001
            # Thumb failure is non-fatal; raw upload is what matters.
            pass

        row = {
            "id": image_id,
            "dataset_id": str(dataset_id),
            "storage_path": raw_path,
            "width": width,
            "height": height,
            "sha256": digest,
            "original_name": upload.filename,
            "content_type": upload.content_type,
            "bytes": len(data),
        }
        res = client.table("images").insert(row).execute()
        if res.data:
            uploaded.append(Image(**res.data[0]))

    return BulkUploadResult(uploaded=uploaded, skipped=skipped)


@router.get(
    "/api/v1/datasets/{dataset_id}/images",
    response_model=list[Image],
)
def list_images(
    dataset_id: UUID,
    status_filter: str | None = None,
    split: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Image]:
    client = _supabase_or_503()
    q = client.table("images").select("*").eq("dataset_id", str(dataset_id))
    if status_filter:
        q = q.eq("status", status_filter)
    if split:
        q = q.eq("split", split)
    res = (
        q.order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return [Image(**row) for row in (res.data or [])]


@router.get("/api/v1/images/{image_id}", response_model=ImageWithUrl)
def get_image(image_id: UUID) -> ImageWithUrl:
    client = _supabase_or_503()
    res = (
        client.table("images")
        .select("*")
        .eq("id", str(image_id))
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Image not found.")
    image = res.data
    try:
        url = signed_url(image["storage_path"])
        thumb = signed_url(
            image["storage_path"].replace("raw/", "thumbs/"),
        )
    except Exception:  # noqa: BLE001
        url, thumb = None, None
    return ImageWithUrl(**image, signed_url=url, thumb_url=thumb)


@router.patch("/api/v1/images/{image_id}", response_model=Image)
def update_image(
    image_id: UUID,
    payload: ImageUpdate,
    _: dict = Depends(require_admin),
) -> Image:
    client = _supabase_or_503()
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")
    res = (
        client.table("images")
        .update(updates)
        .eq("id", str(image_id))
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Image not found.")
    return Image(**res.data[0])


@router.delete(
    "/api/v1/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT,
)
def delete_image(image_id: UUID, _: dict = Depends(require_admin)) -> None:
    client = _supabase_or_503()
    # Cascade in DB removes annotations; storage cleanup is best-effort.
    res = (
        client.table("images")
        .delete()
        .eq("id", str(image_id))
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Image not found.")
