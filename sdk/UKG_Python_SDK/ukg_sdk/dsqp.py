"""Offline DSQP client for SDK consumers."""

from __future__ import annotations

from typing import Any


class DSQPClient:
    """Small SDK wrapper around the local DSQP implementation."""

    def construct(
        self,
        query: str,
        coordinate: dict[str, Any] | None = None,
        *,
        axis_number: int = 8,
        coordinate_path: str = "sdk.default",
    ) -> dict[str, Any]:
        try:
            from backend.dsqp import DSQPChain

            return DSQPChain().construct(
                query,
                coordinate or {},
                axis_number=axis_number,
                coordinate_path=coordinate_path,
                context={"query": query, "coordinate": coordinate or {}},
            ).to_dict()
        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
                "axis_number": axis_number,
                "coordinate_path": coordinate_path,
            }
