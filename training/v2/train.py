"""Magnus v2 training — YOLO11s with modern augmentation.

Trains on the unified dataset produced by build_dataset.build(). Adds the
augmentation and schedule knobs that matter for a small, class-imbalanced
paint-defect dataset, optional Weights & Biases tracking, and an optional
push of best.pt to the Hugging Face Hub.

Run on a Colab GPU runtime (T4 is enough for YOLO11s).
"""

from __future__ import annotations

import os
from pathlib import Path


def run_training(
    data_yaml: str | Path,
    *,
    model: str = "yolo11s.pt",
    epochs: int = 150,
    img_size: int = 640,
    batch: int = 16,
    project: str = "magnus_v2",
    name: str = "yolo11s",
    patience: int = 40,
    use_wandb: bool = False,
    push_to_hub: bool = False,
    hf_repo: str | None = None,
) -> Path:
    from ultralytics import YOLO

    if use_wandb:
        try:
            import wandb

            wandb.init(project="magnus-v2", name=name)
        except Exception as exc:  # noqa: BLE001
            print(f"(wandb desativado: {exc})")
            use_wandb = False

    yolo = YOLO(model)

    # Modern training recipe tuned for a small, imbalanced dataset.
    yolo.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=img_size,
        batch=batch,
        project=project,
        name=name,
        exist_ok=True,
        patience=patience,          # early stopping
        optimizer="auto",
        cos_lr=True,                # cosine LR schedule
        label_smoothing=0.1,
        warmup_epochs=5,
        # --- augmentation ---
        hsv_h=0.015, hsv_s=0.7, hsv_v=0.4,
        degrees=10.0,               # paint defects are rotation-invariant
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        flipud=0.0,
        mosaic=1.0,
        close_mosaic=15,            # turn off mosaic for last 15 epochs
        mixup=0.15,                 # blend two images
        copy_paste=0.3,             # instance copy-paste (helps rare classes)
        erasing=0.4,
    )

    save_dir = Path(yolo.trainer.save_dir)
    best = (save_dir / "weights" / "best.pt").resolve()
    print(f"\n✅ best.pt: {best}")

    if push_to_hub:
        if not hf_repo:
            raise ValueError("hf_repo é obrigatório com push_to_hub=True.")
        _push_to_hf(best, hf_repo)

    return best


def _push_to_hf(weights: Path, repo_id: str) -> None:
    from huggingface_hub import HfApi

    weights = Path(weights).resolve()
    if not weights.is_file():
        raise FileNotFoundError(f"best.pt não encontrado em {weights}")
    api = HfApi(token=os.getenv("HF_TOKEN") or None)
    api.create_repo(repo_id=repo_id, exist_ok=True, repo_type="model")
    api.upload_file(
        path_or_fileobj=str(weights),
        path_in_repo="best.pt",
        repo_id=repo_id,
        repo_type="model",
    )
    print(f"✅ Upload no HF Hub: https://huggingface.co/{repo_id}")
