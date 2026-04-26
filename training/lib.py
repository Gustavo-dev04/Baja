"""Helpers shared by training scripts.

Pulls dataset metadata, image bytes, and annotations directly from Supabase
using the service_role key (read via Colab Secrets — never hard-coded).
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover
    Client = None  # type: ignore[assignment,misc]
    create_client = None  # type: ignore[assignment]

DEFAULT_BUCKET = "baja-images"


def make_supabase(
    url: str | None = None, key: str | None = None,
) -> Client:
    """Return a Supabase client. Reads env vars by default."""
    if create_client is None:
        raise RuntimeError(
            "supabase package not installed. Run `pip install supabase`.",
        )
    url = url or os.environ.get("SUPABASE_URL")
    key = key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required.",
        )
    return create_client(url, key)


def fetch_dataset(client: Client, name: str) -> dict[str, Any]:
    res = (
        client.table("datasets")
        .select("*")
        .eq("name", name)
        .eq("is_active", True)
        .single()
        .execute()
    )
    if not res.data:
        raise RuntimeError(f"Dataset '{name}' not found.")
    return res.data


def fetch_images(
    client: Client, dataset_id: str, page_size: int = 1000,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        res = (
            client.table("images")
            .select("*")
            .eq("dataset_id", dataset_id)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        chunk = res.data or []
        rows.extend(chunk)
        if len(chunk) < page_size:
            break
        offset += page_size
    return rows


def fetch_annotations(
    client: Client, image_ids: Iterable[str],
) -> dict[str, list[dict[str, Any]]]:
    """Return mapping image_id → list of annotation rows."""
    out: dict[str, list[dict[str, Any]]] = {}
    ids = list(image_ids)
    chunk = 200
    for i in range(0, len(ids), chunk):
        batch = ids[i : i + chunk]
        res = (
            client.table("annotations")
            .select("*")
            .in_("image_id", batch)
            .execute()
        )
        for row in res.data or []:
            out.setdefault(row["image_id"], []).append(row)
    return out


def download_image(
    client: Client, storage_path: str, bucket: str = DEFAULT_BUCKET,
) -> bytes:
    return client.storage.from_(bucket).download(storage_path)


def yolo_dataset_dir(
    client: Client,
    dataset_name: str,
    output_dir: str | Path,
    classes: list[str] | None = None,
    split_field: str = "split",  # currently DB column "split"
    valid_fraction: float = 0.2,
) -> Path:
    """Materialize a YOLO-format directory tree in `output_dir`.

    Layout produced (Ultralytics expectation):
        output_dir/
          data.yaml
          images/train/<image_id>.jpg
          images/val/<image_id>.jpg
          labels/train/<image_id>.txt
          labels/val/<image_id>.txt
    """
    import random

    out = Path(output_dir)
    (out / "images" / "train").mkdir(parents=True, exist_ok=True)
    (out / "images" / "val").mkdir(parents=True, exist_ok=True)
    (out / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (out / "labels" / "val").mkdir(parents=True, exist_ok=True)

    ds = fetch_dataset(client, dataset_name)
    dataset_classes = classes or ds["classes"]
    class_to_id = {name: i for i, name in enumerate(dataset_classes)}

    images = fetch_images(client, ds["id"])
    print(f"Imagens no banco: {len(images)}")

    annotations = fetch_annotations(client, [img["id"] for img in images])

    # Filter to images with at least one annotation that maps to our classes.
    usable = [
        img
        for img in images
        if any(
            ann["class_name"] in class_to_id
            for ann in annotations.get(img["id"], [])
        )
    ]
    print(f"Imagens com pelo menos uma anotação válida: {len(usable)}")

    random.seed(42)
    random.shuffle(usable)
    val_n = max(1, int(len(usable) * valid_fraction))
    val_set = set(img["id"] for img in usable[:val_n])

    for img in usable:
        split = "val" if img["id"] in val_set else "train"
        # Honor explicit DB split when present.
        db_split = img.get(split_field)
        if db_split in {"train", "val", "valid"}:
            split = "train" if db_split == "train" else "val"

        try:
            data = download_image(client, img["storage_path"])
        except Exception as exc:  # noqa: BLE001
            print(f"  ! falhou download {img['id']}: {exc}")
            continue

        img_path = out / "images" / split / f"{img['id']}.jpg"
        img_path.write_bytes(data)

        lines: list[str] = []
        for ann in annotations.get(img["id"], []):
            cid = class_to_id.get(ann["class_name"])
            if cid is None:
                continue
            lines.append(
                f"{cid} {ann['x_center']} {ann['y_center']} "
                f"{ann['width']} {ann['height']}",
            )
        (out / "labels" / split / f"{img['id']}.txt").write_text(
            "\n".join(lines),
        )

    yaml_path = out / "data.yaml"
    yaml_path.write_text(
        "path: " + str(out.absolute()) + "\n"
        + "train: images/train\n"
        + "val: images/val\n"
        + f"nc: {len(dataset_classes)}\n"
        + "names: [" + ", ".join(f"'{n}'" for n in dataset_classes) + "]\n",
    )
    print(f"Manifest YOLO: {yaml_path}")
    return yaml_path
