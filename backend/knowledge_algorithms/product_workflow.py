"""Durable, authenticated product workflow for canonical KA execution.

The product API may plan and observe KA work, but it never becomes a second KA
runtime. Every executable plan is built by ``ManifestKASelector`` and dispatched
by ``KAPlanExecutor`` through the one canonical controller.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import secrets
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Event, Lock, Thread
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.exc import IntegrityError

from backend.governed_execution.cancellation import CANCELLATION_REGISTRY
from backend.knowledge_algorithms.contracts import (
    KABudget,
    KAExecutionContext,
    KAExecutionMode,
)
from backend.knowledge_algorithms.ka_master_controller import get_controller
from backend.knowledge_algorithms.selection import (
    KAPlanExecutionReport,
    KASelectionPlan,
    KASelectionRequest,
)
from backend.llm_gateway.job_coordination import (
    GatewayJobCoordinatorUnavailable,
    RedisGatewayJobCoordinator,
)
from backend.llm_gateway.payload_cipher import decrypt_payload, encrypt_payload

logger = logging.getLogger(__name__)
TERMINAL_STATES = frozenset(
    {
        "succeeded",
        "partial",
        "blocked",
        "failed",
        "cancelled",
        "timed_out",
        "dry_run",
        "expired",
    }
)


class KAProductWorkflowError(RuntimeError):
    """Stable public workflow failure with an HTTP-oriented status."""

    def __init__(self, code: str, message: str, *, status: int = 409):
        super().__init__(message)
        self.code = code
        self.public_message = message
        self.status = status


class KAProductPlanRequest(BaseModel):
    """Untrusted product request; authority fields are always server-derived."""

    model_config = ConfigDict(extra="forbid")

    ka_id: str = Field(min_length=1, max_length=64)
    input: dict[str, Any] = Field(default_factory=dict)
    mode: KAExecutionMode = KAExecutionMode.PRODUCTION
    request_id: str | None = Field(default=None, max_length=128)
    idempotency_key: str = Field(min_length=8, max_length=128)
    session_id: str | None = Field(default=None, max_length=128)
    tier: str | None = Field(default=None, max_length=80)
    layer: str | None = Field(default=None, max_length=80)
    persona: str | None = Field(default=None, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)
    budget: dict[str, int] = Field(default_factory=dict)


def validate_plan_request(payload: Any) -> KAProductPlanRequest:
    if not isinstance(payload, dict):
        raise KAProductWorkflowError(
            "KA_PRODUCT_INVALID_REQUEST",
            "JSON body must be an object",
            status=400,
        )
    try:
        return KAProductPlanRequest.model_validate(payload)
    except ValidationError as exc:
        raise KAProductWorkflowError(
            "KA_PRODUCT_INVALID_REQUEST",
            "Knowledge Algorithm plan request is invalid",
            status=422,
        ) from exc


def _sha256_payload(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_sha256(value: Any) -> bool:
    normalized = str(value or "")
    return len(normalized) == 64 and all(
        character in "0123456789abcdef"
        for character in normalized.lower()
    )


def _naive_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=None) if value.tzinfo is not None else value


def product_run_expired(run: Any, *, now: datetime | None = None) -> bool:
    current = now or datetime.now(UTC)
    return bool(
        run.expires_at
        and _naive_utc(run.expires_at) <= _naive_utc(current)
    )


def _confirmation_digest(
    token: str,
    *,
    plan_id: str,
    request_sha256: str,
) -> str:
    return hashlib.sha256(
        f"{token}:{plan_id}:{request_sha256}".encode()
    ).hexdigest()


def _public_plan(plan: KASelectionPlan, *, risk: dict[str, Any]) -> dict[str, Any]:
    included = {
        canonical_id: {
            "canonical_id": entry.canonical_id,
            "name": entry.name,
            "primary_owner": entry.primary_owner,
            "stage": entry.stage,
            "disposition": entry.disposition.value,
            "role": entry.role.value,
            "required": entry.required,
            "dependencies": list(entry.dependencies),
            "effect_class": entry.effect_class,
            "effect_port": entry.effect_port,
            "estimated_ms": entry.estimated_ms,
            "reason": entry.reason,
        }
        for canonical_id, entry in plan.entries.items()
        if entry.role.value != "not_applicable"
    }
    return {
        "schema_version": plan.schema_version,
        "plan_id": plan.plan_id,
        "manifest_version": plan.manifest_version,
        "request_id": plan.request_id,
        "run_id": plan.run_id,
        "mode": plan.mode.value,
        "valid": plan.valid,
        "validation_errors": list(plan.validation_errors),
        "selected_ids": plan.selected_ids,
        "execution_order": plan.execution_order,
        "selected_count": plan.selected_count,
        "dependency_count": plan.dependency_count,
        "effect_proposal_count": plan.effect_proposal_count,
        "estimated_critical_path_ms": plan.estimated_critical_path_ms,
        "risk": risk,
        "entries": included,
    }


def _risk_summary(plan: KASelectionPlan, controller: Any) -> dict[str, Any]:
    risk_classes: set[str] = set()
    effect_ports: set[str] = set()
    effect_ids: list[str] = []
    for canonical_id in plan.selected_ids:
        definition = controller._canonical_controller.manifest.entries[canonical_id]
        risk_classes.update(
            str(value).strip().lower()
            for value in definition.contract.risk_classes
            if str(value).strip()
        )
        if definition.contract.effect_class == "effect_oriented_review_required":
            effect_ids.append(canonical_id)
            if definition.integration.effect_port:
                effect_ports.add(definition.integration.effect_port)
    high_risk = bool(risk_classes & {"high", "critical"})
    effect_oriented = bool(effect_ids)
    risk_tier = (
        "destructive"
        if "critical" in risk_classes and effect_oriented
        else "write"
        if high_risk or effect_oriented
        else "read_only"
    )
    reasons = []
    if high_risk:
        reasons.append("high_or_critical_risk")
    if effect_oriented:
        reasons.append("effect_proposal_review")
    return {
        "tier": risk_tier,
        "risk_classes": sorted(risk_classes),
        "effect_oriented_ids": sorted(effect_ids),
        "effect_ports": sorted(effect_ports),
        "confirmation_reasons": reasons,
    }


def _build_budget(raw: dict[str, int]) -> KABudget:
    values = dict(raw)
    if "timeout_ms" in values and "deadline_ms" not in values:
        values["deadline_ms"] = values.pop("timeout_ms")
    values.setdefault("max_provider_calls", 0)
    values.setdefault("max_effects", 64)
    if values.get("max_provider_calls") != 0:
        raise KAProductWorkflowError(
            "KA_PRODUCT_PROVIDER_CALLS_FORBIDDEN",
            "Knowledge Algorithms cannot make provider calls from the product workflow",
            status=422,
        )
    try:
        return KABudget.model_validate(values)
    except ValidationError as exc:
        raise KAProductWorkflowError(
            "KA_PRODUCT_INVALID_BUDGET",
            "Knowledge Algorithm execution budget is invalid",
            status=422,
        ) from exc


def _effect_service_capabilities(controller: Any) -> set[str]:
    """Return registered proposal review ports without applying their effects."""
    return {
        definition.integration.effect_port
        for definition in controller._canonical_controller.manifest.entries.values()
        if definition.integration.effect_port
        and definition.admission.production_enabled
    }


def plan_product_run(
    payload: KAProductPlanRequest,
    *,
    user_id: int,
    api_key_id: str | None,
    tenant_id: str | None,
    scopes: set[str],
    retention_hours: int = 24,
    confirmation_ttl_minutes: int = 15,
) -> tuple[Any, dict[str, Any], str | None, bool]:
    """Create or idempotently replay one encrypted, principal-owned KA plan."""
    from extensions import db
    from models import KAProductRun

    controller = get_controller()
    principal_key = api_key_id or "desktop"
    try:
        canonical_id = controller._canonical_controller.manifest.resolve_id(
            payload.ka_id
        )
    except KeyError as exc:
        raise KAProductWorkflowError(
            "KA_NOT_FOUND",
            "Knowledge Algorithm was not found",
            status=404,
        ) from exc

    budget = _build_budget(payload.budget)
    request_id = payload.request_id or str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    context = KAExecutionContext(
        request_id=request_id,
        run_id=run_id,
        session_id=payload.session_id,
        principal_id=str(user_id),
        scopes=scopes,
        workflow="ka_product_workflow",
        tier=payload.tier,
        layer=payload.layer,
        persona=payload.persona,
        policy_decisions={
            "product_metadata": dict(payload.metadata),
        },
        capability_state={
            capability: True
            for capability in _effect_service_capabilities(controller)
        },
        budget=budget,
    )
    selection_request = KASelectionRequest(
        requested_ids=[canonical_id],
        shared_input=dict(payload.input),
        service_capabilities=_effect_service_capabilities(controller),
        context=context,
        mode=payload.mode,
    )
    plan = controller.plan_algorithms(selection_request)
    risk = _risk_summary(plan, controller)
    confirmation_required = bool(
        payload.mode != KAExecutionMode.DRY_RUN
        and risk["confirmation_reasons"]
    )
    public_plan = _public_plan(plan, risk=risk)
    fingerprint_payload = {
        "canonical_id": canonical_id,
        "input": payload.input,
        "mode": payload.mode.value,
        "session_id": payload.session_id,
        "tier": payload.tier,
        "layer": payload.layer,
        "persona": payload.persona,
        "metadata": payload.metadata,
        "budget": budget.model_dump(mode="json"),
    }
    fingerprint = _sha256_payload(fingerprint_payload)
    def existing_run() -> Any:
        existing = KAProductRun.query.filter_by(
            user_id=user_id,
            principal_key=principal_key,
            idempotency_key=payload.idempotency_key,
        ).first()
        if existing is None or not product_run_expired(existing):
            return existing
        if existing.status == "running":
            raise KAProductWorkflowError(
                "KA_RUN_EXPIRED",
                "The prior Knowledge Algorithm run expired while active",
            )
        if existing.status == "queued":
            raise KAProductWorkflowError(
                "KA_RUN_EXPIRED",
                "The prior Knowledge Algorithm run is awaiting expiry cleanup",
            )
        db.session.delete(existing)
        db.session.commit()
        return None

    def replay(existing: Any) -> tuple[Any, dict[str, Any], str | None, bool]:
        if existing.request_sha256 != fingerprint:
            raise KAProductWorkflowError(
                "KA_IDEMPOTENCY_CONFLICT",
                "Idempotency key was already used with a different KA request",
            )
        encrypted = decrypt_payload(
            existing.request_encryption,
            existing.request_ciphertext,
        )
        return (
            existing,
            dict(existing.plan_payload),
            encrypted.get("confirmation_token"),
            True,
        )

    existing = existing_run()
    if existing is not None:
        return replay(existing)

    confirmation_token = (
        secrets.token_urlsafe(32) if confirmation_required else None
    )
    encrypted_request = {
        "selection_request": selection_request.model_dump(mode="json"),
        "selection_plan": plan.model_dump(mode="json"),
        "confirmation_token": confirmation_token,
    }
    encryption, ciphertext = encrypt_payload(encrypted_request)
    now = datetime.now(UTC)
    status = "planned" if plan.valid else "blocked"
    run = KAProductRun(
        id=uuid.UUID(run_id),
        request_id=request_id,
        idempotency_key=payload.idempotency_key,
        request_sha256=fingerprint,
        canonical_id=canonical_id,
        manifest_version=plan.manifest_version,
        principal_key=principal_key,
        api_key_id=uuid.UUID(api_key_id) if api_key_id else None,
        user_id=user_id,
        tenant_id=tenant_id,
        status=status,
        mode=payload.mode.value,
        risk_tier=risk["tier"],
        confirmation_required=confirmation_required,
        confirmation_digest=(
            _confirmation_digest(
                confirmation_token,
                plan_id=plan.plan_id,
                request_sha256=fingerprint,
            )
            if confirmation_token
            else None
        ),
        confirmation_expires_at=(
            now + timedelta(minutes=max(1, min(60, confirmation_ttl_minutes)))
            if confirmation_required
            else None
        ),
        plan_payload=public_plan,
        request_encryption=encryption,
        request_ciphertext=ciphertext,
        error_code=(
            "KA_PLAN_BLOCKED" if not plan.valid else None
        ),
        error_message=(
            "Knowledge Algorithm plan did not pass admission"
            if not plan.valid
            else None
        ),
        completed_at=now if not plan.valid else None,
        expires_at=now + timedelta(hours=max(1, min(24 * 30, retention_hours))),
    )
    db.session.add(run)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raced = existing_run()
        if raced is None:
            raise
        return replay(raced)
    return run, public_plan, confirmation_token, False


def confirm_and_queue_product_run(
    run: Any,
    *,
    confirmation_token: str | None,
) -> None:
    """Validate confirmation and move one planned run to the durable queue."""
    from extensions import db

    if run.status != "planned":
        raise KAProductWorkflowError(
            "KA_RUN_NOT_PLANNED",
            "Knowledge Algorithm run is not in a planned state",
        )
    if run.manifest_version != get_controller()._canonical_controller.manifest.manifest_version:
        raise KAProductWorkflowError(
            "KA_PLAN_MANIFEST_STALE",
            "Knowledge Algorithm manifest changed; create a new plan",
        )
    if run.confirmation_required:
        now = datetime.now(UTC)
        if not run.confirmation_expires_at or _naive_utc(
            run.confirmation_expires_at
        ) <= _naive_utc(now):
            raise KAProductWorkflowError(
                "KA_CONFIRMATION_EXPIRED",
                "Knowledge Algorithm confirmation expired; create a new plan",
            )
        encrypted = decrypt_payload(
            run.request_encryption,
            run.request_ciphertext,
        )
        plan_id = str(
            (encrypted.get("selection_plan") or {}).get("plan_id") or ""
        )
        supplied_digest = _confirmation_digest(
            confirmation_token or "",
            plan_id=plan_id,
            request_sha256=run.request_sha256,
        )
        if not run.confirmation_digest or not hmac.compare_digest(
            supplied_digest,
            run.confirmation_digest,
        ):
            raise KAProductWorkflowError(
                "KA_CONFIRMATION_REQUIRED",
                "The exact Knowledge Algorithm plan must be confirmed",
                status=403,
            )
        run.confirmed_at = now
    run.status = "queued"
    db.session.commit()


def decrypt_product_result(run: Any) -> dict[str, Any]:
    if not run.result_encryption or not run.result_ciphertext:
        raise KAProductWorkflowError(
            "KA_RESULT_UNAVAILABLE",
            "Knowledge Algorithm result is not available",
        )
    encoded = run.result_ciphertext.encode("utf-8")
    if not _is_sha256(run.result_sha256) or not hmac.compare_digest(
        hashlib.sha256(encoded).hexdigest(),
        str(run.result_sha256),
    ):
        raise KAProductWorkflowError(
            "KA_RESULT_INTEGRITY_FAILED",
            "Knowledge Algorithm result failed integrity verification",
            status=503,
        )
    return decrypt_payload(run.result_encryption, run.result_ciphertext)


def result_artifacts(result_payload: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = []
    for canonical_id, result in (
        (result_payload.get("report") or {}).get("results") or {}
    ).items():
        for artifact in result.get("artifacts") or []:
            artifacts.append({"canonical_id": canonical_id, **dict(artifact)})
    return artifacts


def result_effects(result_payload: dict[str, Any]) -> list[dict[str, Any]]:
    effects = []
    for canonical_id, result in (
        (result_payload.get("report") or {}).get("results") or {}
    ).items():
        for effect in result.get("effects") or []:
            effects.append({"canonical_id": canonical_id, **dict(effect)})
    return effects


def _validate_applied_effect_receipts(result_payload: dict[str, Any]) -> None:
    plan_id = str((result_payload.get("report") or {}).get("plan_id") or "")
    for effect in result_effects(result_payload):
        if effect.get("status") != "applied":
            continue
        receipt = effect.get("authoritative_receipt")
        required = (
            "service",
            "operation",
            "resource_id",
            "idempotency_key",
            "request_sha256",
            "result_sha256",
        )
        valid = (
            isinstance(receipt, dict)
            and receipt.get("schema_version")
            == "dle.authoritative-effect-receipt.v1"
            and receipt.get("status") == "applied"
            and all(receipt.get(field) for field in required)
            and _is_sha256(receipt.get("request_sha256"))
            and _is_sha256(receipt.get("result_sha256"))
            and effect.get("service") == receipt.get("service")
            and bool(effect.get("idempotency_key"))
            and effect.get("idempotency_key") == receipt.get("idempotency_key")
            and bool(plan_id)
            and receipt.get("ka_plan_id") == plan_id
        )
        if not valid:
            raise KAProductWorkflowError(
                "KA_EFFECT_RECEIPT_INVALID",
                "Applied KA effect is missing a valid authoritative service receipt",
            )


class KAProductRunRunner:
    """Bounded durable worker for already-confirmed canonical KA plans."""

    def __init__(self, app: Any, *, max_workers: int = 2) -> None:
        self.app = app
        self._executor = ThreadPoolExecutor(
            max_workers=max(1, min(8, int(max_workers))),
            thread_name_prefix="dle-ka-product",
        )
        self._futures: dict[str, Future] = {}
        self._lock = Lock()
        self._stopping = False
        self._coordination_retention = max(
            3600,
            int(app.config.get("DLE_KA_PRODUCT_RETENTION_HOURS", 24)) * 3600,
        )
        self._coordination_lease_seconds = max(
            30,
            min(
                3600,
                int(app.config.get("DLE_KA_PRODUCT_LEASE_SECONDS", 300)),
            ),
        )
        self._reconcile_interval_seconds = max(
            5,
            min(
                60,
                int(app.config.get("DLE_KA_PRODUCT_RECONCILE_SECONDS", 15)),
            ),
        )
        self._reconcile_stop = Event()
        self._reconcile_thread: Thread | None = None
        self._coordinator: RedisGatewayJobCoordinator | None = None
        if app.config.get("DLE_USE_REDIS") or app.config.get(
            "DLE_PRODUCTION_MODE"
        ):
            redis_url = app.config.get("DLE_REDIS_URL") or os.environ.get(
                "REDIS_URL",
                "redis://127.0.0.1:6379/0",
            )
            self._coordinator = RedisGatewayJobCoordinator.from_url(
                redis_url,
                prefix="ka:product-runs",
            )

    def _record_coordination_state(self, run_id: str, state: str) -> None:
        if self._coordinator is None:
            return
        try:
            self._coordinator.record_state(
                run_id,
                state,
                retention_seconds=self._coordination_retention,
            )
        except GatewayJobCoordinatorUnavailable:
            logger.error(
                "KA product coordination state update failed for %s",
                run_id,
            )

    def _mark_interrupted(self, run_id: str) -> bool:
        from extensions import db
        from models import KAProductRun

        with self.app.app_context():
            run = db.session.get(KAProductRun, uuid.UUID(run_id))
            if run is None or run.status != "running":
                return False
            run.status = "failed"
            run.error_code = "KA_RUN_INTERRUPTED"
            run.error_message = (
                "The application stopped while this KA run was active; "
                "the run was not replayed."
            )
            run.completed_at = datetime.now(UTC)
            db.session.commit()
        self._record_coordination_state(run_id, "failed")
        return True

    def _reconcile_running_once(self) -> None:
        from extensions import db
        from models import KAProductRun

        with self.app.app_context():
            KAProductRun.query.filter(
                KAProductRun.expires_at <= datetime.now(UTC),
                KAProductRun.status.in_(tuple(TERMINAL_STATES | {"planned"})),
            ).delete(synchronize_session=False)
            db.session.commit()
            running_ids = [
                str(run.id)
                for run in KAProductRun.query.filter_by(status="running").all()
            ]
        for run_id in running_ids:
            if self._coordinator is None:
                self._mark_interrupted(run_id)
                continue
            worker_id = f"reconcile-{uuid.uuid4()}"
            try:
                acquired = self._coordinator.acquire(
                    run_id,
                    worker_id=worker_id,
                    lease_seconds=self._coordination_lease_seconds,
                )
            except GatewayJobCoordinatorUnavailable:
                logger.error(
                    "KA product stale-run reconciliation could not acquire Redis"
                )
                return
            if not acquired:
                continue
            try:
                self._mark_interrupted(run_id)
            finally:
                try:
                    self._coordinator.release(
                        run_id,
                        worker_id=worker_id,
                    )
                except GatewayJobCoordinatorUnavailable:
                    logger.error(
                        "KA product reconciliation lease release failed"
                    )

    def _reconcile_loop(self) -> None:
        while not self._reconcile_stop.wait(
            self._reconcile_interval_seconds
        ):
            try:
                self._reconcile_running_once()
            except Exception:
                logger.exception("KA product stale-run reconciliation failed")

    def start(self) -> None:
        from models import KAProductRun

        self._reconcile_running_once()
        with self.app.app_context():
            queued = [
                str(run.id)
                for run in KAProductRun.query.filter_by(status="queued").all()
            ]
        if self._coordinator is not None and self._reconcile_thread is None:
            self._reconcile_thread = Thread(
                target=self._reconcile_loop,
                name="dle-ka-product-reconciler",
                daemon=True,
            )
            self._reconcile_thread.start()
        for run_id in queued:
            self.submit(run_id)

    def submit(self, run_id: str) -> None:
        normalized = str(uuid.UUID(str(run_id)))
        with self._lock:
            if self._stopping:
                raise RuntimeError("KA product runner is stopping")
            existing = self._futures.get(normalized)
            if existing is not None and not existing.done():
                return
            self._record_coordination_state(normalized, "queued")
            future = self._executor.submit(self._run, normalized)
            self._futures[normalized] = future
            future.add_done_callback(lambda _future: self._forget(normalized))

    def _forget(self, run_id: str) -> None:
        with self._lock:
            self._futures.pop(run_id, None)

    def _run(self, run_id: str) -> None:
        worker_id = str(uuid.uuid4())
        lease_stop = Event()
        lease_lost = Event()
        heartbeat: Thread | None = None
        if self._coordinator is not None:
            try:
                acquired = self._coordinator.acquire(
                    run_id,
                    worker_id=worker_id,
                    lease_seconds=self._coordination_lease_seconds,
                )
            except GatewayJobCoordinatorUnavailable:
                logger.error("KA product run lease acquisition failed")
                return
            if not acquired:
                return

            def renew_lease() -> None:
                interval = max(5, self._coordination_lease_seconds // 3)
                while not lease_stop.wait(interval):
                    try:
                        renewed = self._coordinator.renew(
                            run_id,
                            worker_id=worker_id,
                            lease_seconds=self._coordination_lease_seconds,
                        )
                    except GatewayJobCoordinatorUnavailable:
                        renewed = False
                    if not renewed:
                        lease_lost.set()
                        return

            heartbeat = Thread(
                target=renew_lease,
                name=f"dle-ka-product-lease-{run_id[:8]}",
                daemon=True,
            )
            heartbeat.start()
        try:
            self._run_acquired(run_id, lease_lost=lease_lost)
        finally:
            lease_stop.set()
            if heartbeat is not None:
                heartbeat.join(timeout=2)
            if self._coordinator is not None:
                try:
                    self._coordinator.release(
                        run_id,
                        worker_id=worker_id,
                    )
                except GatewayJobCoordinatorUnavailable:
                    logger.error("KA product run lease release failed")

    def _run_acquired(self, run_id: str, *, lease_lost: Event) -> None:
        from extensions import db
        from models import KAProductRun

        with self.app.app_context():
            run = db.session.get(KAProductRun, uuid.UUID(run_id))
            if run is None or run.status != "queued":
                return
            now = datetime.now(UTC)
            if run.cancellation_requested:
                run.status = "cancelled"
                run.completed_at = now
                db.session.commit()
                self._record_coordination_state(run_id, "cancelled")
                return
            if product_run_expired(run, now=now):
                run.status = "expired"
                run.error_code = "KA_RUN_EXPIRED"
                run.error_message = "Knowledge Algorithm run expired before execution."
                run.completed_at = now
                db.session.commit()
                self._record_coordination_state(run_id, "expired")
                return
            run.status = "running"
            run.started_at = now
            encrypted = decrypt_payload(
                run.request_encryption,
                run.request_ciphertext,
            )
            db.session.commit()
            self._record_coordination_state(run_id, "running")

            def cancellation_requested() -> bool:
                db.session.refresh(run, attribute_names=["cancellation_requested"])
                if run.cancellation_requested or lease_lost.is_set():
                    return True
                if self._coordinator is None:
                    return False
                try:
                    return self._coordinator.is_cancel_requested(run_id)
                except GatewayJobCoordinatorUnavailable:
                    lease_lost.set()
                    return True

            try:
                selection_request = KASelectionRequest.model_validate(
                    encrypted["selection_request"]
                )
                selection_plan = KASelectionPlan.model_validate(
                    encrypted["selection_plan"]
                )
                controller = get_controller()
                report = asyncio.run(
                    controller.execute_algorithm_plan(
                        selection_plan,
                        selection_request,
                        cancellation_check=cancellation_requested,
                    )
                )
                if lease_lost.is_set():
                    raise KAProductWorkflowError(
                        "KA_COORDINATION_LOST",
                        "Knowledge Algorithm execution lost its worker lease",
                        status=503,
                    )
                db.session.refresh(run, attribute_names=["status"])
                if run.status != "running":
                    raise KAProductWorkflowError(
                        "KA_COORDINATION_LOST",
                        "Knowledge Algorithm execution lost its durable claim",
                        status=503,
                    )
                payload = {
                    "schema_version": "dle.ka-product-result.v1",
                    "run_id": run_id,
                    "report": report.model_dump(mode="json"),
                }
                _validate_applied_effect_receipts(payload)
                encryption, ciphertext = encrypt_payload(payload)
                encoded = ciphertext.encode("utf-8")
                run.result_encryption = encryption
                run.result_ciphertext = ciphertext
                run.result_sha256 = hashlib.sha256(encoded).hexdigest()
                run.result_size_bytes = len(encoded)
                run.status = report.status.value
                run.error_code = (
                    "KA_REQUIRED_NODE_FAILED"
                    if report.required_failure
                    else None
                )
                run.error_message = (
                    "A required Knowledge Algorithm did not complete"
                    if report.required_failure
                    else None
                )
            except KAProductWorkflowError as exc:
                logger.warning("KA product result validation failed: %s", exc.code)
                run.status = "failed"
                run.error_code = exc.code
                run.error_message = exc.public_message
            except Exception:
                logger.exception("Durable KA product execution failed")
                run.status = "failed"
                run.error_code = "KA_RUN_INTERNAL_ERROR"
                run.error_message = "Knowledge Algorithm execution failed"
            run.completed_at = datetime.now(UTC)
            db.session.commit()
            self._record_coordination_state(run_id, run.status)

    def cancel(self, run: Any) -> bool:
        run.cancellation_requested = True
        if self._coordinator is not None:
            try:
                self._coordinator.request_cancel(
                    str(run.id),
                    retention_seconds=self._coordination_retention,
                )
                self._record_coordination_state(
                    str(run.id),
                    "cancellation_requested",
                )
            except GatewayJobCoordinatorUnavailable:
                logger.error("KA product Redis cancellation update failed")
        signalled = CANCELLATION_REGISTRY.cancel(run.request_id)
        with self._lock:
            future = self._futures.get(str(run.id))
            if future is not None and future.cancel():
                signalled = True
        return signalled

    def stop(self) -> None:
        from extensions import db
        from models import KAProductRun

        with self._lock:
            self._stopping = True
            futures = list(self._futures.values())
        self._reconcile_stop.set()
        if self._reconcile_thread is not None:
            self._reconcile_thread.join(timeout=2)
        with self.app.app_context():
            active = KAProductRun.query.filter(
                KAProductRun.status.in_(("queued", "running"))
            ).all()
            for run in active:
                run.cancellation_requested = True
                if self._coordinator is not None:
                    try:
                        self._coordinator.request_cancel(
                            str(run.id),
                            retention_seconds=self._coordination_retention,
                        )
                    except GatewayJobCoordinatorUnavailable:
                        logger.error(
                            "KA product shutdown cancellation update failed"
                        )
                CANCELLATION_REGISTRY.cancel(run.request_id)
            db.session.commit()
        for future in futures:
            future.cancel()
        self._executor.shutdown(wait=True, cancel_futures=True)


def get_ka_product_runner(app: Any) -> KAProductRunRunner:
    runner = app.extensions.get("dle_ka_product_runner")
    if runner is None:
        runner = KAProductRunRunner(
            app,
            max_workers=int(app.config.get("DLE_KA_PRODUCT_WORKERS", 2)),
        )
        app.extensions["dle_ka_product_runner"] = runner
        runner.start()
    return runner


def trace_summary(result_payload: dict[str, Any]) -> dict[str, Any]:
    report = KAPlanExecutionReport.model_validate(result_payload["report"])
    return {
        "schema_version": "dle.ka-product-trace.v1",
        "plan_id": report.plan_id,
        "manifest_version": report.manifest_version,
        "request_id": report.request_id,
        "run_id": report.run_id,
        "status": report.status.value,
        "started_at": report.started_at.isoformat(),
        "completed_at": report.completed_at.isoformat(),
        "duration_ms": report.duration_ms,
        "required_failure": report.required_failure,
        "traces": {
            canonical_id: trace.model_dump(mode="json")
            for canonical_id, trace in report.traces.items()
            if trace.events
        },
    }
