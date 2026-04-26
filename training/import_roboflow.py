"""Import a Roboflow YOLOv8 dataset into the Baja API.

Workflow:
1. Reads `data.yaml` from a Roboflow YOLOv8 download to get class names.
2. Iterates over train/, valid/, test/ splits.
3. Uploads images in batches of 20 to `POST /api/v1/datasets/{id}/images`.
4. For each uploaded image, parses the matching YOLO `.txt` label file,
   maps Roboflow class names to Baja class names, and POSTs the annotations
   to `POST /api/v1/images/{id}/annotations` (replace-all semantics).

Designed to run in Google Colab. Idempotent on re-runs because the API
deduplicates by sha256 (skipped images keep their original IDs).
"""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import requests
import yaml


CLASS_MAP: dict[str, str] = {
    "orange_peel": "casca_de_laranja",
    "runs_sags": "escorrimento",
    "solvent_pop": "bolha",
    "water_spotting": "water_spotting",
}

SPLITS = ("train", "valid", "test")
BATCH = 20


def login(api_url: str, password: str) -> str:
    r = requests.post(
        f"{api_url}/api/v1/auth/admin-token",
        json={"password": password},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["token"]


def ensure_dataset(
    api_url: str, token: str, name: str, classes: list[str], description: str,
) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    existing = requests.get(
        f"{api_url}/api/v1/datasets", timeout=30,
    ).json()
    for ds in existing:
        if ds["name"] == name:
            return ds["id"]
    r = requests.post(
        f"{api_url}/api/v1/datasets",
        headers=headers,
        json={"name": name, "description": description, "classes": classes},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["id"]


def parse_yolo_label(text: str, names: dict[int, str]) -> list[dict[str, Any]]:
    boxes: list[dict[str, Any]] = []
    for line in text.strip().splitlines():
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        cid = int(parts[0])
        x, y, w, h = (float(v) for v in parts[1:5])
        roboflow_name = names.get(cid)
        if roboflow_name is None or roboflow_name == "null":
            continue
        baja_name = CLASS_MAP.get(roboflow_name)
        if baja_name is None:
            continue
        boxes.append(
            {
                "class_name": baja_name,
                "x_center": x,
                "y_center": y,
                "width": max(w, 1e-4),
                "height": max(h, 1e-4),
                "source": "import",
            },
        )
    return boxes


def chunked(items: list, size: int) -> Iterable[list]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def upload_batch(
    api_url: str, token: str, dataset_id: str, paths: list[Path],
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    files = []
    handles = []
    try:
        for p in paths:
            f = open(p, "rb")
            handles.append(f)
            files.append(("files", (p.name, f, "image/jpeg")))
        r = requests.post(
            f"{api_url}/api/v1/datasets/{dataset_id}/images",
            headers=headers,
            files=files,
            timeout=120,
        )
        r.raise_for_status()
        return r.json()
    finally:
        for f in handles:
            f.close()


def find_image_id_by_name(
    api_url: str, dataset_id: str, original_name: str,
) -> str | None:
    # API list endpoint orders by created_at desc and supports pagination.
    # For dedup case we re-query by name fragment is too costly; use list.
    r = requests.get(
        f"{api_url}/api/v1/datasets/{dataset_id}/images",
        params={"limit": 200},
        timeout=30,
    )
    r.raise_for_status()
    for row in r.json():
        if row.get("original_name") == original_name:
            return row["id"]
    return None


def post_annotations(
    api_url: str, token: str, image_id: str, boxes: list[dict[str, Any]],
) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(
        f"{api_url}/api/v1/images/{image_id}/annotations",
        headers=headers,
        json=boxes,
        timeout=30,
    )
    r.raise_for_status()


def import_split(
    api_url: str,
    token: str,
    dataset_id: str,
    split_dir: Path,
    names: dict[int, str],
) -> tuple[int, int, int]:
    images_dir = split_dir / "images"
    labels_dir = split_dir / "labels"
    if not images_dir.exists():
        return (0, 0, 0)

    image_files = sorted(
        p
        for p in images_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    print(f"  → {len(image_files)} imagens em {split_dir.name}")

    uploaded = skipped = annotated = 0
    name_to_id: dict[str, str] = {}

    for batch in chunked(image_files, BATCH):
        result = upload_batch(api_url, token, dataset_id, batch)
        for img in result.get("uploaded", []):
            uploaded += 1
            name_to_id[img["original_name"]] = img["id"]
        for sk in result.get("skipped", []):
            skipped += 1
            if sk.get("reason") == "duplicate":
                # Recover existing image id so we still attach annotations.
                existing = find_image_id_by_name(
                    api_url, dataset_id, sk["name"],
                )
                if existing:
                    name_to_id[sk["name"]] = existing
        time.sleep(0.3)  # be nice to the free CPU

    for img_path in image_files:
        image_id = name_to_id.get(img_path.name)
        if image_id is None:
            continue
        label_path = labels_dir / (img_path.stem + ".txt")
        if not label_path.exists():
            continue
        boxes = parse_yolo_label(label_path.read_text(), names)
        if not boxes:
            continue
        try:
            post_annotations(api_url, token, image_id, boxes)
            annotated += 1
        except requests.HTTPError as exc:
            print(f"    ! falhou anotação {img_path.name}: {exc}")

    return uploaded, skipped, annotated


def import_roboflow_dataset(
    api_url: str,
    admin_password: str,
    dataset_root: str | Path,
    target_dataset_name: str = "paint-defects-pretrain",
) -> None:
    api_url = api_url.rstrip("/")
    root = Path(dataset_root)
    yaml_path = root / "data.yaml"
    if not yaml_path.exists():
        print(f"❌ data.yaml não encontrado em {root}")
        sys.exit(1)

    cfg = yaml.safe_load(yaml_path.read_text())
    raw_names = cfg.get("names", [])
    names: dict[int, str] = {}
    if isinstance(raw_names, list):
        names = {i: n for i, n in enumerate(raw_names)}
    elif isinstance(raw_names, dict):
        names = {int(k): v for k, v in raw_names.items()}

    print("Classes do Roboflow:", names)
    target_classes = sorted(set(CLASS_MAP[n] for n in names.values() if n in CLASS_MAP))
    print("Classes mapeadas para Baja:", target_classes)

    print("Login admin…")
    token = login(api_url, admin_password)

    print(f"Garantindo dataset '{target_dataset_name}'…")
    dataset_id = ensure_dataset(
        api_url,
        token,
        name=target_dataset_name,
        classes=target_classes,
        description="Imported from Roboflow Universe (paint defects).",
    )
    print(f"  dataset_id = {dataset_id}")

    totals = [0, 0, 0]
    for split in SPLITS:
        split_dir = root / split
        if not split_dir.exists():
            continue
        print(f"\nImportando split '{split}'…")
        u, s, a = import_split(api_url, token, dataset_id, split_dir, names)
        totals[0] += u
        totals[1] += s
        totals[2] += a
        print(f"  uploaded={u}  skipped={s}  annotated={a}")

    print("\n" + "=" * 50)
    print(f"TOTAL  uploaded={totals[0]}  skipped={totals[1]}  annotated={totals[2]}")
    print(f"Dataset id: {dataset_id}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--name", default="paint-defects-pretrain")
    args = parser.parse_args()

    import_roboflow_dataset(
        api_url=args.api_url,
        admin_password=args.password,
        dataset_root=args.dataset_root,
        target_dataset_name=args.name,
    )
