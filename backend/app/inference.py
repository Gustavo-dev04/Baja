"""YOLO inference wrapper."""

from __future__ import annotations

import os
import time
from io import BytesIO
from pathlib import Path

from PIL import Image

from .config import CONF_THRESHOLD, DEMO_CLASS_MAP, MODEL_CACHE_DIR, MODEL_WEIGHTS
from .schemas import Detection, InspectionResult


def _resolve_weights(weights: str) -> tuple[str, bool]:
    """Resolve a weights spec to a local path.

    Supports:
        - `yolov8n.pt`, `yolov8s.pt`, ... (Ultralytics auto-download)
        - Local paths
        - `hf://<repo_id>/<filename>` (downloads from Hugging Face Hub
          and caches under MODEL_CACHE_DIR).

    Returns (local_path, is_finetuned).
    """
    if not weights.startswith("hf://"):
        return weights, False

    spec = weights[len("hf://") :]
    parts = spec.split("/")
    if len(parts) < 3:
        raise ValueError(
            f"Invalid hf:// spec: {weights!r}. "
            "Expected hf://<owner>/<repo>/<filename>",
        )
    repo_id = "/".join(parts[:-1])
    filename = parts[-1]

    from huggingface_hub import hf_hub_download

    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    local_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        cache_dir=str(MODEL_CACHE_DIR),
        token=os.getenv("HF_TOKEN") or None,
    )
    return local_path, True


class Detector:
    def __init__(self, weights: str = MODEL_WEIGHTS) -> None:
        # Imported lazily so tests can patch it without the heavy import cost.
        from ultralytics import YOLO

        local_path, is_finetuned = _resolve_weights(weights)
        self.weights = weights  # keep original spec for /health output
        self._local_path = local_path
        self._is_finetuned = is_finetuned
        self.model = YOLO(local_path)

    @property
    def demo_mode(self) -> bool:
        # Fine-tuned models loaded from HF Hub are never demo.
        if self._is_finetuned:
            return False
        # Treat any stock yolov8/yolo11/yolov5 checkpoint as demo.
        name = Path(self._local_path).name.lower()
        return name.startswith(("yolov8", "yolo11", "yolov5"))

    def detect(self, image_bytes: bytes) -> InspectionResult:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")

        start = time.perf_counter()
        results = self.model.predict(
            source=img,
            conf=CONF_THRESHOLD,
            verbose=False,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        detections = self._parse(results)

        return InspectionResult(
            detections=detections,
            image_size=[img.width, img.height],
            inference_ms=round(elapsed_ms, 2),
            model=self.weights,
            demo_mode=self.demo_mode,
        )

    def _parse(self, results) -> list[Detection]:
        if not results:
            return []

        result = results[0]
        names = result.names  # dict[int, str]
        boxes = result.boxes
        if boxes is None or len(boxes) == 0:
            return []

        xyxy = boxes.xyxy.cpu().numpy()
        conf = boxes.conf.cpu().numpy()
        cls = boxes.cls.cpu().numpy().astype(int)

        parsed: list[Detection] = []
        for i in range(len(boxes)):
            raw_label = names.get(int(cls[i]), str(cls[i]))
            # Fine-tuned models already emit Baja class names; the demo map
            # only applies when the stock COCO checkpoint is in use.
            if self._is_finetuned:
                label = raw_label
            else:
                label = DEMO_CLASS_MAP.get(raw_label, raw_label)
            x1, y1, x2, y2 = [float(v) for v in xyxy[i]]
            parsed.append(
                Detection(
                    label=label,
                    raw_label=raw_label,
                    confidence=float(conf[i]),
                    bbox=[x1, y1, x2, y2],
                )
            )
        return parsed


_detector: Detector | None = None


def get_detector() -> Detector:
    global _detector
    if _detector is None:
        _detector = Detector()
    return _detector
