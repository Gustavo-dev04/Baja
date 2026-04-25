"""Smoke tests for main app — endpoint registration and retrocompat."""

from __future__ import annotations

import sys
import types

import numpy as np


class _FakeTensor:
    def __init__(self, a):
        self._a = a

    def cpu(self):
        return self

    def numpy(self):
        return self._a


class _FakeBoxes:
    def __init__(self):
        self.xyxy = _FakeTensor(np.zeros((0, 4)))
        self.conf = _FakeTensor(np.zeros((0,)))
        self.cls = _FakeTensor(np.zeros((0,), dtype=int))

    def __len__(self):
        return 0


class _FakeResult:
    names: dict = {}
    boxes = _FakeBoxes()


class _FakeYOLO:
    def __init__(self, *_a, **_kw):
        pass

    def predict(self, *_a, **_kw):
        return [_FakeResult()]


def _install_fake_ultralytics():
    module = types.ModuleType("ultralytics")
    module.YOLO = _FakeYOLO  # type: ignore[attr-defined]
    sys.modules["ultralytics"] = module


def test_app_routes_registered():
    _install_fake_ultralytics()

    import app.inference as inf

    inf._detector = None  # reset singleton
    from app.main import app

    paths = {route.path for route in app.routes}
    # Public, unchanged contracts.
    assert "/health" in paths
    assert "/inspect" in paths
    # New v1 surface.
    assert "/api/v1/auth/admin-token" in paths
    assert "/api/v1/datasets" in paths
    assert "/api/v1/datasets/{dataset_id}" in paths
    assert "/api/v1/datasets/{dataset_id}/images" in paths
    assert "/api/v1/images/{image_id}" in paths
    assert "/api/v1/images/{image_id}/annotations" in paths
