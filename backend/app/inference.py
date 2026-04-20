"""YOLO inference wrapper."""

from __future__ import annotations

import time
from io import BytesIO

from PIL import Image

from .config import CONF_THRESHOLD, DEMO_CLASS_MAP, MODEL_WEIGHTS
from .schemas import Detection, InspectionResult


class Detector:
    def __init__(self, weights: str = MODEL_WEIGHTS) -> None:
        # Imported lazily so tests can patch it without the heavy import cost.
        from ultralytics import YOLO

        self.weights = weights
        self.model = YOLO(weights)

    @property
    def demo_mode(self) -> bool:
        # Treat any checkpoint whose name starts with the stock yolov8/yolo11
        # prefixes as "demo" — i.e. not yet fine-tuned on paint defects.
        name = self.weights.lower()
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
