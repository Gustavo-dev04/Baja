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

    print("\nPor classe:")
    names = yolo.names
    for i, c in names.items():
        try:
            ap50 = box.ap50[i]
            print(f"  {c:<18} mAP50={ap50:.3f}")
        except (IndexError, TypeError):
            pass

    save_dir = Path(project) / name
    print(f"\n📊 Gráficos em: {save_dir.absolute()}")
    print(f"   confusion_matrix.png, PR_curve.png, ...")

    return {
        "map50": float(box.map50),
        "map50_95": float(box.map),
        "precision": float(box.mp),
        "recall": float(box.mr),
    }
