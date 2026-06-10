"""Magnus v2 evaluation — TTA, confusion matrix, per-class metrics.

Loads a trained checkpoint and runs a thorough validation pass on the test
split: test-time augmentation for a small mAP bump, a confusion matrix to
spot which defects get confused, and per-class precision/recall/mAP.

Outputs go to `<project>/<name>/` (Ultralytics saves plots automatically:
confusion_matrix.png, PR_curve.png, etc).
"""

from __future__ import annotations

from pathlib import Path


def evaluate(
    weights: str | Path,
    data_yaml: str | Path,
    *,
    img_size: int = 640,
    use_tta: bool = True,
    split: str = "test",
    project: str = "magnus_v2",
    name: str = "eval",
) -> dict:
    from ultralytics import YOLO

    yolo = YOLO(str(weights))
    metrics = yolo.val(
        data=str(data_yaml),
        imgsz=img_size,
        split=split,
        augment=use_tta,           # test-time augmentation
        project=project,
        name=name,
        exist_ok=True,
        plots=True,                # confusion matrix + PR curves
    )

    # Per-class summary.
    print("\n" + "=" * 60)
    print(f"AVALIAÇÃO ({split}, TTA={'on' if use_tta else 'off'})")
    print("=" * 60)
    box = metrics.box
    print(f"mAP50    : {box.map50:.4f}")
    print(f"mAP50-95 : {box.map:.4f}")
    print(f"Precision: {box.mp:.4f}")
    print(f"Recall   : {box.mr:.4f}")

    # box.ap50 is ordered by ap_class_index (classes present in this split),
    # NOT by raw class id — indexing by id silently misattributes scores.
    print("\nPor classe:")
    names = yolo.names
    class_index = getattr(box, "ap_class_index", [])
    for pos, cls_id in enumerate(class_index):
        label = names.get(int(cls_id), str(cls_id))
        print(f"  {label:<18} mAP50={box.ap50[pos]:.3f}")
    missing = set(names) - {int(c) for c in class_index}
    for cls_id in sorted(missing):
        print(f"  {names[cls_id]:<18} (sem amostras no split)")

    # Ultralytics nests results under runs/detect/<project>/<name>; read the
    # real location from the metrics object instead of guessing.
    save_dir = Path(getattr(metrics, "save_dir", Path(project) / name))
    print(f"\n📊 Gráficos em: {save_dir}")
    print("   confusion_matrix.png, PR_curve.png, ...")

    return {
        "map50": float(box.map50),
        "map50_95": float(box.map),
        "precision": float(box.mp),
        "recall": float(box.mr),
        "save_dir": str(save_dir),
    }
