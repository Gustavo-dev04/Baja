"""Build the unified Magnus v2 dataset from curated Roboflow sources.

Pipeline:
1. Download each curated source (config.SOURCES) in YOLOv8 format.
2. Parse each source's data.yaml to learn its local class names.
3. Remap every box to the unified taxonomy (config.CLASS_MAP); drop boxes
   whose class isn't in our taxonomy.
4. Deduplicate by SOURCE image (stripping Roboflow's baked-in augmentation
   suffix `_jpg.rf.<hash>`), so we don't double-augment later.
5. Write a single YOLO dataset tree + data.yaml with our 8 classes.
6. Print a per-class, per-source report.

Result is consumed by train.py. Run in Colab (see colab.md).
"""

from __future__ import annotations

import os
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from .config import CLASS_TO_ID, CLASS_MAP, SOURCES, UNIFIED_CLASSES

SPLITS = ("train", "valid", "test")


def _source_key(filename: str) -> str:
    """Strip Roboflow's augmentation hash to recover the source image id.

    `ds1_0003_JPEG_jpg.rf.<hash>.jpg` -> `ds1_0003_JPEG`
    `0002_JPEG_jpg.rf.<hash>.jpg`     -> `0002_JPEG`
    """
    if "_jpg.rf." in filename:
        return filename.split("_jpg.rf.")[0]
    if ".rf." in filename:
        return filename.rsplit(".rf.", 1)[0]
    return Path(filename).stem


def _download(rf, source) -> Path:
    project = rf.workspace(source.workspace).project(source.project)
    version = project.versions()[-1]
    location = f"/content/v2_src/{source.project}"
    ds = version.download("yolov8", location=location)
    return Path(ds.location)


def _remap_label_file(
    label_path: Path, local_names: list[str],
) -> list[str]:
    """Read a YOLO .txt and return remapped lines (unified class ids)."""
    out: list[str] = []
    for line in label_path.read_text().strip().splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        local_id = int(parts[0])
        if local_id >= len(local_names):
            continue
        local_name = local_names[local_id]
        unified = CLASS_MAP.get(local_name)
        if unified is None:
            continue  # dropped class
        new_id = CLASS_TO_ID[unified]
        out.append(" ".join([str(new_id), *parts[1:5]]))
    return out


def build(
    output_dir: str = "/content/magnus_v2",
    api_key: str | None = None,
    valid_fraction: float = 0.15,
    test_fraction: float = 0.10,
    seed: int = 42,
) -> Path:
    from roboflow import Roboflow

    api_key = api_key or os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ROBOFLOW_API_KEY não definido (use Colab Secrets ou env var).",
        )
    rf = Roboflow(api_key=api_key)

    out = Path(output_dir)
    if out.exists():
        shutil.rmtree(out)
    for split in ("train", "val", "test"):
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)

    # Collect (image_path, remapped_lines) keyed by source id for dedup.
    seen_sources: set[str] = set()
    samples: list[tuple[Path, list[str], str]] = []  # (img, lines, source)
    per_source_counts: dict[str, Counter] = defaultdict(Counter)

    for source in SOURCES:
        print(f"\n⬇️  Baixando {source} — {source.role}")
        root = _download(rf, source)
        names = yaml.safe_load((root / "data.yaml").read_text())["names"]
        if isinstance(names, dict):
            names = [names[k] for k in sorted(names, key=int)]

        for split in SPLITS:
            img_dir = root / split / "images"
            lbl_dir = root / split / "labels"
            if not img_dir.exists():
                continue
            for img_path in img_dir.iterdir():
                if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                    continue
                key = f"{source.project}/{_source_key(img_path.name)}"
                if key in seen_sources:
                    continue  # drop baked-augmentation duplicate
                label_path = lbl_dir / (img_path.stem + ".txt")
                lines = (
                    _remap_label_file(label_path, names)
                    if label_path.exists()
                    else []
                )
                # Keep image even with 0 lines (negative sample) only if it
                # came from a source that includes good_paint negatives.
                seen_sources.add(key)
                samples.append((img_path, lines, source.project))
                for ln in lines:
                    cid = int(ln.split()[0])
                    per_source_counts[source.project][UNIFIED_CLASSES[cid]] += 1

    print(f"\n📦 Total de imagens-fonte únicas: {len(samples)}")

    # Shuffle once, then slice into test / val / train by index.
    random.seed(seed)
    random.shuffle(samples)
    n = len(samples)
    n_test = int(n * test_fraction)
    n_val = int(n * valid_fraction)

    written = Counter()
    for idx, (img_path, lines, _src) in enumerate(samples):
        if idx < n_test:
            split = "test"
        elif idx < n_test + n_val:
            split = "val"
        else:
            split = "train"
        stem = f"{img_path.stem}_{idx}"
        shutil.copy(img_path, out / "images" / split / f"{stem}.jpg")
        (out / "labels" / split / f"{stem}.txt").write_text("\n".join(lines))
        written[split] += 1

    # data.yaml
    (out / "data.yaml").write_text(
        f"path: {out.absolute()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n"
        f"nc: {len(UNIFIED_CLASSES)}\n"
        "names: [" + ", ".join(f"'{c}'" for c in UNIFIED_CLASSES) + "]\n",
    )

    # Report
    print("\n" + "=" * 60)
    print("DATASET MAGNUS v2")
    print("=" * 60)
    print(f"Splits: train={written['train']} val={written['val']} test={written['test']}")
    print("\nInstâncias por classe (consolidado):")
    total = Counter()
    for counts in per_source_counts.values():
        total.update(counts)
    for c in UNIFIED_CLASSES:
        print(f"  {c:<18} {total[c]:>6}")
    print("\nPor fonte:")
    for src, counts in per_source_counts.items():
        print(f"  {src}: {dict(counts)}")
    print(f"\n✅ data.yaml: {out / 'data.yaml'}")
    return out / "data.yaml"


if __name__ == "__main__":
    build()
