"""Dataset Exporter Module for DataLogicEngine.

Transforms explicitly released governed traces into candidate SFT, DPO, and PRM records.
"""

from __future__ import annotations

from .capture_policy import (
    CAPTURE_FLAG_KEY,
    get_capture_settings_payload,
    is_training_data_capture_enabled,
    set_training_data_capture_enabled,
)
from .exporter_core import DatasetExporter
from .parquet_writer import ParquetWriter
from .privacy_redactor import PrivacyRedactor
from .runtime_capture import (
    RuntimeCaptureError,
    RuntimeCaptureLoadError,
    RuntimeCaptureStorageError,
    capture_stats,
    load_staged_capture_traces,
    maybe_stage_released_trace,
    maybe_stage_training_capture,
    purge_staged_capture_runs,
)

__all__ = [
    "CAPTURE_FLAG_KEY",
    "DatasetExporter",
    "ParquetWriter",
    "PrivacyRedactor",
    "RuntimeCaptureError",
    "RuntimeCaptureLoadError",
    "RuntimeCaptureStorageError",
    "capture_stats",
    "get_capture_settings_payload",
    "is_training_data_capture_enabled",
    "load_staged_capture_traces",
    "maybe_stage_released_trace",
    "maybe_stage_training_capture",
    "purge_staged_capture_runs",
    "set_training_data_capture_enabled",
]
