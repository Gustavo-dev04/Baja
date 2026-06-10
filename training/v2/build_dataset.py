"""Build the unified Magnus v2 dataset from curated Roboflow sources.

Pipeline:
1. Download each curated source (config.SOURCES) in YOLOv8 format.
2. Parse each source's data.yaml to learn its local class names.
3. Remap every box to the unified taxonomy (config.CLASS_MAP); drop boxes
   whose class isn't in our taxonomy.
4. Deduplicate by SOURCE image. The dedup key strips Roboflow's baked-in
   augmentation suffix (`_jpg.rf.<hash>`) and is scoped by WORKSPACE, not
   project — so the three overlapping `baopersonal` projects collapse to
   one copy per original photo, while identically-named files from
   unrelated workspaces don't falsely collide.
5. Drop images that LOST all their annotations in the remap (e.g. a photo
   whose only label was `Dent`): keeping them would teach the model that
   visible damage is "clean paint". Images that were annotated as
   `good_paint` (config.NEGATIVE_OK) or never had labels are kept as
   genuine negatives.
6. Optionally oversample train images containing rare classes.
7. Write a single YOLO dataset tree + data.yaml with our 8 classes.
8. Print a per-class, per-source report.

Result is consumed by train.py. Run in Colab (see colab.md).
"""

from __future__ import annotations

import os
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from .config import (
    CLASS_MAP,
    CLASS_TO_ID,
    NEGATIVE_OK,
    SOURCES,
    UNIFIED_CLASSES,
)

SPLITS = ("train", "valid", "test")

# Classes with few instances get their train images duplicated this many
# extra times (cheap oversampling; augmentation makes copies distinct).
RARE_OVERSAMPLE = 2


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
    versions = project.versions()
    latest = max(versions, key=lambda v: int(v.version))
    location = f"/content/v2_src/{source.project}"
    ds = latest.download("yolov8", location=location)
    return Path(ds.location)


def _remap_label_file(
    label_path: Path, local_names: list[str],
) -> tuple[list[str], bool, bool]:
    """Read a YOLO .txt and remap to unified class ids.

    Returns (remapped_lines, had_any_annotation, had_negative_ok_label).
    """
    out: list[str] = []
    had_any = False
    had_negative_ok = False
    for line in label_path.read_text().strip().splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        had_any = True
        local_id = int(parts[0])
        if local_id >= len(local_names):
            continue
        local_name = local_names[local_id]
        if local_name in NEGATIVE_OK:
            had_negative_ok = True
            continue
        unified = CLASS_MAP.get(local_name)
        if unified is None:
            continue  # dropped class
        new_id = CLASS_TO_ID[unified]
        out.append(" ".join([str(new_id), *parts[1:5]]))
    return out, had_any, had_negative_ok


def build(
    output_dir: str = "/content/magnus_v2",
    api_key: str | None = None,
    valid_fraction: float = 0.15,
    test_fraction: float = 0.10,
    seed: int = 42,
    oversample_rare: bool = True,
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

    # Dedup key is workspace-scoped: overlapping projects from the same
    # author collapse; unrelated workspaces can't falsely collide.
    seen_sources: set[str] = set()
    samples: list[tuple[Path, list[str], str]] = []  # (img, lines, project)
    per_source_counts: dict[str, Counter] = defaultdict(Counter)
    per_source_images: Counter = Counter()
    dropped_lost_labels = 0

    skipped_sources: list[str] = []
    for source in SOURCES:
        print(f"\n⬇️  Baixando {source} — {source.role}")
        try:
            root = _download(rf, source)
        except Exception as exc:  # noqa: BLE001
            # A source can fail because it's a classification project (no
            # boxes), was deleted, or hit a transient API error. Skip it and
            # keep building from the rest instead of aborting everything.
            print(f"   ⚠️  pulado ({type(exc).__name__}): {str(exc)[:120]}")
            skipped_sources.append(str(source))
            continue
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
                key = f"{source.workspace}/{_source_key(img_path.name)}"
                if key in seen_sources:
                    continue  # duplicate (baked augmentation or overlap)

                label_path = lbl_dir / (img_path.stem + ".txt")
                if label_path.exists():
                    lines, had_any, had_neg = _remap_label_file(
                        label_path, names,
                    )
                else:
                    lines, had_any, had_neg = [], False, False

                # An image that HAD annotations but lost all of them in the
                # remap shows out-of-scope damage (dents etc). Keeping it as
                # "background" would poison the negatives — drop it.
                if not lines and had_any and not had_neg:
                    dropped_lost_labels += 1
                    seen_sources.add(key)
                    continue

                seen_sources.add(key)
                samples.append((img_path, lines, source.project))
                per_source_images[source.project] += 1
                for ln in lines:
                    cid = int(ln.split()[0])
                    per_source_counts[source.project][
                        UNIFIED_CLASSES[cid]
                    ] += 1

    print(f"\n📦 Imagens-fonte únicas mantidas: {len(samples)}")
    print(f"🗑️  Descartadas (perderam todos os rótulos no remap): "
          f"{dropped_lost_labels}")

    # Shuffle once, then slice into test / val / train by index.
    random.seed(seed)
    random.shuffle(samples)
    n = len(samples)
    n_test = int(n * test_fraction)
    n_val = int(n * valid_fraction)

    # Identify rare classes (bottom quartile of instance counts) for
    # train-only oversampling. Done AFTER the split indices are fixed, so
    # no image ever appears in two splits.
    total_inst = Counter()
    for counts in per_source_counts.values():
        total_inst.update(counts)
    present = [c for c in UNIFIED_CLASSES if total_inst[c] > 0]
    rare: set[int] = set()
    if oversample_rare and len(present) >= 4:
        threshold = sorted(total_inst[c] for c in present)[len(present) // 4]
        rare = {
            CLASS_TO_ID[c] for c in present if total_inst[c] <= threshold
        }
        print(f"📈 Oversampling x{RARE_OVERSAMPLE + 1} para classes raras: "
              f"{[UNIFIED_CLASSES[i] for i in sorted(rare)]}")

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

        # Oversample rare-class images in TRAIN only (extra copies; the
        # on-the-fly augmentation makes each epoch's view distinct).
        if split == "train" and rare:
            has_rare = any(int(ln.split()[0]) in rare for ln in lines)
            if has_rare:
                for k in range(RARE_OVERSAMPLE):
                    dup = f"{stem}_os{k}"
                    shutil.copy(
                        img_path, out / "images" / "train" / f"{dup}.jpg",
                    )
                    (out / "labels" / "train" / f"{dup}.txt").write_text(
                        "\n".join(lines),
                    )
                    written["train_oversampled"] += 1

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
    print(
        f"Splits: train={written['train']} "
        f"(+{written['train_oversampled']} oversampled) "
        f"val={written['val']} test={written['test']}"
    )
    print("\nImagens únicas contribuídas por fonte (após dedup):")
    for src, n_imgs in per_source_images.most_common():
        print(f"  {src:<40} {n_imgs:>6}")
    print("\nInstâncias por classe (consolidado):")
    for c in UNIFIED_CLASSES:
        print(f"  {c:<18} {total_inst[c]:>6}")
    print("\nPor fonte:")
    for src, counts in per_source_counts.items():
        print(f"  {src}: {dict(counts)}")
    if skipped_sources:
        print("\n⚠️  Fontes puladas:")
        for s in skipped_sources:
            print(f"  - {s}")
    print(f"\n✅ data.yaml: {out / 'data.yaml'}")
    return out / "data.yaml"


if __name__ == "__main__":
    build()
