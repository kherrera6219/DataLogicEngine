"""Concurrent DSQP orchestration for persona axes 8-11."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from backend.dsqp.dsqp_chain import AXIS_PERSONA_TYPES, DSQPChain
from backend.dsqp.dsqp_validator import DSQPValidator


class DSQPOrchestrator:
    """Run DSQP chains for the active persona axes."""

    def __init__(
        self,
        chain: DSQPChain | None = None,
        validator: DSQPValidator | None = None,
        timeout_seconds: int | None = None,
    ):
        self.chain = chain or DSQPChain()
        self.validator = validator or DSQPValidator()
        self.timeout_seconds = timeout_seconds or self._default_timeout()

    @staticmethod
    def _default_timeout() -> int:
        if os.environ.get("IS_DESKTOP_APP", "false").lower() in {"1", "true", "yes", "on"}:
            return 30
        return 120

    async def construct_all(
        self,
        query: str,
        axis_vector: dict[str, Any] | None = None,
        *,
        active_axes: list[int] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        axes = active_axes or list(AXIS_PERSONA_TYPES)
        tasks = [
            self._construct_one(query, axis_vector or {}, axis_number, context or {})
            for axis_number in axes
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        profiles: dict[str, Any] = {}
        failures: dict[str, str] = {}
        for axis_number, result in zip(axes, results):
            key = str(axis_number)
            if isinstance(result, Exception):
                failures[key] = str(result)
            else:
                profiles[key] = result
        return {
            "profiles": profiles,
            "failures": failures,
            "partial": bool(failures),
            "timeout_seconds": self.timeout_seconds,
        }

    def construct_all_sync(
        self,
        query: str,
        axis_vector: dict[str, Any] | None = None,
        *,
        active_axes: list[int] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.construct_all(query, axis_vector, active_axes=active_axes, context=context)
            )

        profiles: dict[str, Any] = {}
        failures: dict[str, str] = {}
        for axis_number in active_axes or list(AXIS_PERSONA_TYPES):
            try:
                profiles[str(axis_number)] = self._construct_sync(
                    query,
                    axis_vector or {},
                    axis_number,
                    context or {},
                )
            except Exception as exc:
                failures[str(axis_number)] = str(exc)
        return {
            "profiles": profiles,
            "failures": failures,
            "partial": bool(failures),
            "timeout_seconds": self.timeout_seconds,
        }

    async def _construct_one(
        self,
        query: str,
        axis_vector: dict[str, Any],
        axis_number: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        return await asyncio.wait_for(
            asyncio.to_thread(self._construct_sync, query, axis_vector, axis_number, context),
            timeout=self.timeout_seconds,
        )

    def _construct_sync(
        self,
        query: str,
        axis_vector: dict[str, Any],
        axis_number: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        coordinate_path = str(
            context.get("coordinate_path")
            or context.get(f"axis_{axis_number}")
            or context.get(str(axis_number))
            or f"axis_{axis_number}.default"
        )
        persona = self.chain.construct(
            query,
            axis_vector,
            axis_number=axis_number,
            coordinate_path=coordinate_path,
            context=context,
        )
        validation = self.validator.validate(persona)
        payload = persona.to_dict()
        payload["validation"] = validation
        if not validation["valid"]:
            raise ValueError(f"DSQP coverage below threshold: {validation}")
        return payload
