"""Main DatasetExporter orchestrator for DataLogicEngine."""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .dpo_builder import DPOBuilder
from .parquet_writer import ParquetWriter
from .privacy_redactor import PrivacyRedactor, SecurityError
from .prm_builder import PRMBuilder
from .sft_builder import SFTBuilder

logger = logging.getLogger(__name__)


class DatasetExporter:
    """Orchestrates database queries, trace transformation, security screening, and dataset export."""

    @classmethod
    def export_dataset(
        cls,
        traces: Sequence[dict[str, Any]],
        *,
        export_type: str = "sft",
        output_path: str | Path = "dataset.parquet",
        min_confidence: float = 0.98,
        format_type: str = "parquet",
        base_dir: str | Path = "./datasets",
        compression: str = "snappy",
    ) -> dict[str, Any]:
        """Export explicitly released traces with fail-closed security screening.

        Supported export_type values: 'sft', 'dpo', 'prm'.
        """
        export_type = str(export_type).lower().strip()
        format_type = str(format_type).lower().strip()
        if export_type not in {"sft", "dpo", "prm"}:
            raise ValueError(f"Unsupported export_type: '{export_type}'. Use 'sft', 'dpo', or 'prm'.")
        if format_type not in {"parquet", "jsonl"}:
            raise ValueError("Unsupported format_type. Use 'parquet' or 'jsonl'.")
        if not math.isfinite(min_confidence) or not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be a finite number from 0.0 through 1.0.")

        # Validate security policy on output path
        try:
            validated_path = PrivacyRedactor.validate_safe_path(output_path, base_dir=base_dir)
        except (SecurityError, ValueError) as exc:
            logger.error("Security policy rejected output path %s: %s", output_path, exc)
            raise

        # Filter trace runs by confidence and governance security gates
        filtered_traces: list[dict[str, Any]] = []
        for t in traces:
            if not isinstance(t, dict):
                continue

            # Security screening is deliberately fail-closed: callers must supply
            # explicit release evidence, and both prompt and answer must exist.
            is_quarantined = bool(t.get("quarantine", False) or t.get("quarantined", False))
            is_never_persist = t.get("containment_class") == "never_persist"
            is_authorized = t.get("release_authorized") is True
            try:
                conf = float(t.get("confidence", 0.0))
            except (TypeError, ValueError):
                continue

            if (
                is_quarantined
                or is_never_persist
                or not is_authorized
                or not math.isfinite(conf)
                or not str(t.get("query") or "").strip()
                or not str(t.get("released_answer") or "").strip()
            ):
                logger.debug("Skipping restricted trace run: %s", t.get("run_id"))
                continue

            if conf >= min_confidence:
                filtered_traces.append(t)

        logger.info(
            "Exporting %d / %d trace runs (min_confidence=%.2f, type=%s, format=%s)",
            len(filtered_traces),
            len(traces),
            min_confidence,
            export_type,
            format_type,
        )

        rows: list[dict[str, Any]] = []

        if export_type == "sft":
            for trace in filtered_traces:
                row_model = SFTBuilder.build_row(trace)
                rows.append(row_model.model_dump())

        elif export_type == "dpo":
            for trace in filtered_traces:
                row_model = DPOBuilder.build_row(trace, trace)
                rows.append(row_model.model_dump())

        elif export_type == "prm":
            for trace in filtered_traces:
                row_model = PRMBuilder.build_row(trace)
                rows.append(row_model.model_dump())

        # Redact secrets and PII from all serialized data
        clean_rows = PrivacyRedactor.redact_data(rows)

        # Write dataset to validated path
        if format_type == "jsonl":
            written_path = ParquetWriter.write_jsonl(clean_rows, validated_path, base_dir=base_dir)
        else:
            written_path = ParquetWriter.write_parquet(
                clean_rows,
                validated_path,
                compression=compression,
                base_dir=base_dir,
            )

        return {
            "status": "success",
            "export_type": export_type,
            "format": format_type,
            "total_input_traces": len(traces),
            "exported_rows": len(clean_rows),
            "output_path": written_path,
        }

    @classmethod
    def export_from_db(
        cls,
        db_session: Any,
        *,
        export_type: str = "sft",
        output_path: str | Path = "dataset.parquet",
        min_confidence: float = 0.98,
        format_type: str = "parquet",
        limit: int = 1000,
        base_dir: str | Path = "./datasets",
    ) -> dict[str, Any]:
        """Query TraceRun records from database session and export to dataset."""
        try:
            from models import TraceRun, TraceStage

            if export_type == "dpo":
                raise ValueError(
                    "Database DPO export is unavailable until governed traces persist real rejected candidates."
                )
            if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 10_000:
                raise ValueError("limit must be an integer from 1 through 10000.")
            if not math.isfinite(min_confidence) or not 0.0 <= min_confidence <= 1.0:
                raise ValueError("min_confidence must be a finite number from 0.0 through 1.0.")

            query = (
                db_session.query(TraceRun)
                .filter(TraceRun.confidence >= min_confidence)
                .order_by(TraceRun.created_at.desc())
                .limit(limit)
            )
            trace_records = query.all()

            traces: list[dict[str, Any]] = []
            for record in trace_records:
                stages = (
                    db_session.query(TraceStage)
                    .filter(TraceStage.run_id == record.run_id)
                    .order_by(TraceStage.start_time.asc())
                    .all()
                )
                stage_list = [
                    {
                        "stage": s.name,
                        "status": s.status,
                        "details": s.status or "unknown",
                    }
                    for s in stages
                ]

                snapshot = record.data_snapshot if isinstance(record.data_snapshot, dict) else {}
                status = str(record.status or "").strip().lower()
                truthgate_decision = str(record.truthgate_decision or "").strip().lower()
                release_authorized = (
                    status in {"completed", "succeeded", "success"}
                    and truthgate_decision in {"allow", "release"}
                    and record.regulatory_pass is not False
                    and record.security_pass is not False
                    and bool(str(record.input_message or "").strip())
                    and bool(str(record.final_answer or "").strip())
                )

                trace_dict = {
                    "run_id": str(record.run_id),
                    "query": str(record.input_message or ""),
                    "released_answer": str(record.final_answer or ""),
                    "confidence": float(record.confidence or 0.0),
                    "tier": record.tier,
                    "stages": stage_list,
                    "personas": [],
                    "release_authorized": release_authorized,
                    "quarantine": bool(snapshot.get("quarantine") or snapshot.get("quarantined")),
                    "containment_class": snapshot.get("containment_class"),
                }
                traces.append(trace_dict)

            return cls.export_dataset(
                traces=traces,
                export_type=export_type,
                output_path=output_path,
                min_confidence=min_confidence,
                format_type=format_type,
                base_dir=base_dir,
            )
        except (SecurityError, ValueError):
            raise
        except Exception as exc:
            logger.error("Failed to query database for dataset export: %s", exc)
            raise OSError("Database query export failed.") from exc

    @classmethod
    def export_from_capture(
        cls,
        *,
        export_type: str = "sft",
        output_path: str | Path = "dataset.parquet",
        min_confidence: float = 0.98,
        format_type: str = "parquet",
        limit: int = 1000,
        base_dir: str | Path = "./datasets",
    ) -> dict[str, Any]:
        """Export previously staged runtime-capture rows through the same gates."""

        if export_type == "dpo":
            raise ValueError(
                "Database DPO export is unavailable until governed traces persist real rejected candidates."
            )
        from .runtime_capture import load_staged_capture_traces

        traces = load_staged_capture_traces(base_dir=base_dir, limit=limit)
        return cls.export_dataset(
            traces=traces,
            export_type=export_type,
            output_path=output_path,
            min_confidence=min_confidence,
            format_type=format_type,
            base_dir=base_dir,
        )
