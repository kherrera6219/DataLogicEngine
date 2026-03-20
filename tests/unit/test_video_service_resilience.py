import importlib
import sys


def test_video_service_imports_without_opencv(monkeypatch):
    original_module = sys.modules.pop("backend.services.video_service", None)
    original_import_module = importlib.import_module

    def fake_import_module(name, package=None):
        if name == "cv2":
            raise ImportError("libGL.so.1 missing")
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)

    video_service_module = importlib.import_module("backend.services.video_service")
    video_service_module = importlib.reload(video_service_module)

    assert video_service_module.CV2 is None
    assert video_service_module.video_service.extract_frames_sync(b"fake-video") == []

    if original_module is not None:
        sys.modules["backend.services.video_service"] = original_module
    else:
        sys.modules.pop("backend.services.video_service", None)
