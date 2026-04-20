"""Smoke tests for the inference layer.

These tests stub out ``ultralytics`` entirely so CI does not need to
install the real package or download model weights.
"""

from __future__ import annotations

import sys
import types
from io import BytesIO

import numpy as np
from PIL import Image


class _FakeTensor:
    def __init__(self, array: np.ndarray) -> None:
        self._a = array

    def cpu(self) -> "_FakeTensor":
        return self

    def numpy(self) -> np.ndarray:
        return self._a


class _FakeBoxes:
    def __init__(self) -> None:
        self.xyxy = _FakeTensor(np.array([[10.0, 20.0, 30.0, 40.0]]))
        self.conf = _FakeTensor(np.array([0.87]))
        self.cls = _FakeTensor(np.array([39]))  # COCO "bottle"

    def __len__(self) -> int:
        return 1


class _FakeResult:
    def __init__(self) -> None:
        self.names = {39: "bottle"}
        self.boxes = _FakeBoxes()


class _FakeYOLO:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def predict(self, *_args, **_kwargs):
        return [_FakeResult()]


def _install_fake_ultralytics() -> None:
    module = types.ModuleType("ultralytics")
    module.YOLO = _FakeYOLO  # type: ignore[attr-defined]
    sys.modules["ultralytics"] = module


def _fake_image_bytes(width: int = 64, height: int = 64) -> bytes:
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_detect_returns_mapped_label():
    _install_fake_ultralytics()

    import app.inference as inf

    inf._detector = None  # reset singleton
    detector = inf.get_detector()
    result = detector.detect(_fake_image_bytes())

    assert result.image_size == [64, 64]
    assert len(result.detections) == 1
    det = result.detections[0]
    assert det.raw_label == "bottle"
    assert det.label == "escorrimento"  # via DEMO_CLASS_MAP
    assert 0.0 <= det.confidence <= 1.0
    assert len(det.bbox) == 4
    assert result.demo_mode is True


def test_detect_no_boxes_returns_empty():
    _install_fake_ultralytics()

    import app.inference as inf

    class _EmptyBoxes:
        xyxy = _FakeTensor(np.zeros((0, 4)))
        conf = _FakeTensor(np.zeros((0,)))
        cls = _FakeTensor(np.zeros((0,), dtype=int))

        def __len__(self) -> int:
            return 0

    class _EmptyResult:
        names = {}
        boxes = _EmptyBoxes()

    inf._detector = None
    detector = inf.get_detector()
    detector.model.predict = lambda *a, **kw: [_EmptyResult()]  # type: ignore[assignment]

    result = detector.detect(_fake_image_bytes())
    assert result.detections == []
    assert result.image_size == [64, 64]
