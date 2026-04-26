"""Fine-tune a YOLOv8 model on the Baja paint defects dataset.

Usage (Colab GPU runtime):

    from training.train_yolo import run_training
    run_training(
        dataset_name="paint-defects-pretrain",
        output_dir="/content/runs",
        epochs=50,
        model="yolov8n.pt",
    )

Logs metrics, saves `best.pt`, optionally pushes to Hugging Face Hub.
"""

from __future__ import annotations

import os
from pathlib import Path

from .lib import make_supabase, yolo_dataset_dir


def run_training(
    dataset_name: str,
    output_dir: str | Path = "/content/runs",
    *,
    epochs: int = 50,
    img_size: int = 640,
    batch: int = 16,
    model: str = "yolov8n.pt",
    project: str = "baja",
    name: str | None = None,
    valid_fraction: float = 0.2,
    push_to_hub: bool = False,
    hf_repo: str | None = None,
) -> Path:
    from ultralytics import YOLO

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    yolo_dir = out / "yolo-data"

    print(f"\n=== Materializando dataset '{dataset_name}' ===")
    client = make_supabase()
    yaml_path = yolo_dataset_dir(
        client,
        dataset_name=dataset_name,
        output_dir=yolo_dir,
        valid_fraction=valid_fraction,
    )

    print(f"\n=== Treinando ({model}, {epochs} epochs) ===")
    yolo = YOLO(model)
    run_name = name or f"{dataset_name}-ft"
    yolo.train(
        data=str(yaml_path),
        epochs=epochs,
        imgsz=img_size,
        batch=batch,
        project=project,
        name=run_name,
        exist_ok=True,
    )

    best = (Path(project) / run_name / "weights" / "best.pt").resolve()
    print(f"\n✅ best.pt salvo em: {best}")

    if push_to_hub:
        if not hf_repo:
            raise ValueError("hf_repo é obrigatório quando push_to_hub=True.")
        _push_to_hf(best, hf_repo)

    return best


def _push_to_hf(weights: Path, repo_id: str) -> None:
    from huggingface_hub import HfApi

    weights = Path(weights).resolve()
    if not weights.is_file():
        raise FileNotFoundError(f"best.pt não encontrado em {weights}")
    api = HfApi()
    api.create_repo(repo_id=repo_id, exist_ok=True, repo_type="model")
    api.upload_file(
        path_or_fileobj=str(weights),
        path_in_repo="best.pt",
        repo_id=repo_id,
        repo_type="model",
    )
    print(f"✅ Upload no HF Hub: https://huggingface.co/{repo_id}")
