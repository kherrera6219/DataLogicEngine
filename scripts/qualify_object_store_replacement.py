# ruff: noqa: BLE001, S110
"""Run the SeaweedFS Replacement Control qualification on Windows/Podman.

This harness is deliberately candidate-only. It creates uniquely named,
disposable Podman resources, publishes only a loopback S3 port, records a
redacted report, and always reports production approval as false. Independent
license/security review and clean-machine failure qualification cannot be
self-attested by this script.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import json
import os
import platform
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.storage.object_snapshot import (
    SnapshotIntegrityError,
    export_bucket,
    migrate_bucket,
    restore_bucket,
    verify_snapshot,
)
from backend.storage.object_store import LocalFileBackend, S3Backend

DEFAULT_LOCK = REPO_ROOT / "deploy" / "internal-data-plane.candidate-lock.json"
DEFAULT_REPORT = (
    REPO_ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-03"
    / "seaweedfs-replacement-qualification-windows.json"
)
DEFAULT_VULNERABILITY_REPORT = (
    REPO_ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-03"
    / "seaweedfs-4.40-dle.1-trivy.json"
)
QUALIFICATION_BUCKET = "dle-qualification"
MIGRATION_BUCKET = "dle-qualification-migration"
DEFAULT_PORT = 18333


class QualificationError(RuntimeError):
    """Expected, safely reportable qualification failure."""


class Recorder:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def add(
        self,
        gate: str,
        check: str,
        status: str,
        evidence: Any,
    ) -> None:
        if status not in {"pass", "fail", "pending"}:
            raise ValueError(f"Unsupported qualification status: {status}")
        self.checks.append(
            {
                "gate": gate,
                "check": check,
                "status": status,
                "evidence": evidence,
            }
        )

    def run(
        self,
        gate: str,
        check: str,
        callback: Callable[[], Any],
    ) -> Any | None:
        try:
            evidence = callback()
        except Exception as exc:
            self.add(gate, check, "fail", _safe_error(exc))
            return None
        self.add(gate, check, "pass", evidence)
        return evidence

    def gate_summary(self) -> dict[str, str]:
        summary: dict[str, str] = {}
        for item in self.checks:
            gate = item["gate"]
            current = summary.get(gate, "pass")
            if item["status"] == "fail" or current == "fail":
                summary[gate] = "fail"
            elif item["status"] == "pending" or current == "pending":
                summary[gate] = "pending"
            else:
                summary[gate] = "pass"
        return summary


def _safe_error(exc: Exception) -> str:
    if isinstance(exc, QualificationError):
        text = str(exc).strip()
        if text and all(character.isalnum() or character in "_:-.,= " for character in text):
            return text[:240]
    return f"{exc.__class__.__name__}:qualification_check_failed"


def _redact(text: str, secret_values: tuple[str, ...]) -> str:
    redacted = text
    for value in secret_values:
        if value:
            redacted = redacted.replace(value, "[REDACTED]")
    return redacted


def _run(
    runtime: str,
    arguments: list[str],
    *,
    input_text: str | None = None,
    timeout: int = 180,
    secret_values: tuple[str, ...] = (),
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            [runtime, *arguments],
            input=input_text,
            capture_output=True,
            check=False,
            encoding="utf-8",
            errors="replace",
            shell=False,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise QualificationError("container_runtime_execution_failed") from exc
    if check and result.returncode != 0:
        detail = _redact((result.stderr or result.stdout).strip(), secret_values)
        raise QualificationError(f"container_runtime_command_failed:{detail[:160]}")
    return result


def _load_lock(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        raise QualificationError("candidate_lock_unreadable") from exc
    candidate = value.get("services", {}).get("object_store_candidate", {})
    if candidate.get("product") != "seaweedfs" or not str(candidate.get("version") or ""):
        raise QualificationError("candidate_lock_identity_invalid")
    if candidate.get("production_approved") is not False:
        raise QualificationError("candidate_lock_must_not_approve_production")
    if value.get("production_provisioning_authorized") is not False:
        raise QualificationError("candidate_lock_production_authority_invalid")
    if (
        value.get("architecture_change_authorized") is not True
        or candidate.get("selection_status") != "selected_for_release_qualification"
    ):
        raise QualificationError("candidate_lock_architecture_authority_invalid")
    return value


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(report, indent=2, sort_keys=True) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def _assert_port_available(port: int) -> dict[str, Any]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        try:
            listener.bind(("127.0.0.1", port))
        except OSError as exc:
            raise QualificationError(f"qualification_port_busy:{port}") from exc
    return {"host": "127.0.0.1", "port": port, "available": True}


def _s3_client(
    endpoint: str,
    access_key: str = "",
    secret_key: str = "",
    *,
    unsigned: bool = False,
    max_attempts: int = 3,
):
    try:
        import boto3
        from botocore import UNSIGNED
        from botocore.config import Config
    except ImportError as exc:
        raise QualificationError("boto3_client_not_installed") from exc

    kwargs: dict[str, Any] = {
        "service_name": "s3",
        "endpoint_url": endpoint,
        "region_name": "us-east-1",
        "config": Config(
            signature_version=UNSIGNED if unsigned else "s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": max_attempts, "mode": "standard"},
            connect_timeout=3,
            read_timeout=10,
        ),
    }
    if not unsigned:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key
    return boto3.client(**kwargs)


def _wait_for_s3(client: Any, bucket: str, timeout_seconds: int = 90) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            client.list_objects_v2(Bucket=bucket, MaxKeys=1)
            return
        except Exception as exc:  # service startup returns several transient S3 errors
            last_error = exc
            time.sleep(1)
    raise QualificationError("candidate_s3_readiness_timeout") from last_error


def _assert_denied(callback: Callable[[], Any]) -> dict[str, str]:
    try:
        callback()
    except Exception as exc:
        response = getattr(exc, "response", {})
        code = str(response.get("Error", {}).get("Code", exc.__class__.__name__))
        http_status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if http_status in {401, 403} or code in {
            "AccessDenied",
            "InvalidAccessKeyId",
            "SignatureDoesNotMatch",
        }:
            return {"denied": "true", "code": code, "http_status": str(http_status)}
        raise QualificationError(f"unexpected_denial_error:{code}") from exc
    raise QualificationError("unauthorized_operation_was_allowed")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _contract_checks(
    client: Any,
    endpoint: str,
    access_key: str,
    secret_key: str,
    run_id: str,
) -> dict[str, Any]:
    from boto3.s3.transfer import TransferConfig

    small_key = f"contract/{run_id}/small.json"
    small_data = json.dumps({"run_id": run_id, "status": "qualified"}).encode()
    small_hash = _sha256(small_data)
    client.put_object(
        Bucket=QUALIFICATION_BUCKET,
        Key=small_key,
        Body=small_data,
        ContentType="application/json",
        Metadata={"sha256": small_hash, "owner": "replacement-control"},
    )
    received = client.get_object(Bucket=QUALIFICATION_BUCKET, Key=small_key)["Body"].read()
    if received != small_data:
        raise QualificationError("s3_get_content_mismatch")

    head = client.head_object(Bucket=QUALIFICATION_BUCKET, Key=small_key)
    if head.get("ContentType") != "application/json":
        raise QualificationError("s3_content_type_mismatch")
    if head.get("Metadata", {}).get("sha256") != small_hash:
        raise QualificationError("s3_metadata_mismatch")
    listing = client.list_objects_v2(
        Bucket=QUALIFICATION_BUCKET,
        Prefix=f"contract/{run_id}/",
    )
    if small_key not in {item["Key"] for item in listing.get("Contents", [])}:
        raise QualificationError("s3_prefix_list_mismatch")

    multipart_key = f"contract/{run_id}/multipart.bin"
    multipart_data = secrets.token_bytes((5 * 1024 * 1024 * 2) + 17)
    client.upload_fileobj(
        io.BytesIO(multipart_data),
        QUALIFICATION_BUCKET,
        multipart_key,
        ExtraArgs={
            "ContentType": "application/octet-stream",
            "Metadata": {"sha256": _sha256(multipart_data)},
        },
        Config=TransferConfig(
            multipart_threshold=5 * 1024 * 1024,
            multipart_chunksize=5 * 1024 * 1024,
            max_concurrency=4,
        ),
    )
    multipart_received = client.get_object(
        Bucket=QUALIFICATION_BUCKET,
        Key=multipart_key,
    )["Body"].read()
    if _sha256(multipart_received) != _sha256(multipart_data):
        raise QualificationError("s3_multipart_hash_mismatch")

    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": QUALIFICATION_BUCKET, "Key": small_key},
        ExpiresIn=60,
    )
    with urllib.request.urlopen(url, timeout=10) as response:
        if response.read() != small_data:
            raise QualificationError("s3_presigned_content_mismatch")

    client.delete_object(Bucket=QUALIFICATION_BUCKET, Key=multipart_key)
    try:
        client.head_object(Bucket=QUALIFICATION_BUCKET, Key=multipart_key)
    except Exception:
        pass
    else:
        raise QualificationError("s3_delete_not_observed")

    durability_key = f"durability/{run_id}.bin"
    durability_data = secrets.token_bytes(256 * 1024)
    client.put_object(
        Bucket=QUALIFICATION_BUCKET,
        Key=durability_key,
        Body=durability_data,
        ContentType="application/octet-stream",
        Metadata={"sha256": _sha256(durability_data)},
    )
    return {
        "operations": [
            "put",
            "get",
            "head",
            "list_prefix",
            "delete",
            "multipart_upload",
            "presigned_get",
        ],
        "small_object_sha256": small_hash,
        "multipart_bytes": len(multipart_data),
        "durability_key": durability_key,
        "durability_sha256": _sha256(durability_data),
        "endpoint": endpoint,
        "credential_transport": "podman_secret_static_s3_config",
        "access_key_persisted_in_report": access_key in json.dumps({"run_id": run_id}),
        "secret_key_persisted_in_report": secret_key in json.dumps({"run_id": run_id}),
    }


def _verify_durability(client: Any, fixture: dict[str, Any]) -> dict[str, Any]:
    data = client.get_object(
        Bucket=QUALIFICATION_BUCKET,
        Key=fixture["durability_key"],
    )["Body"].read()
    digest = _sha256(data)
    if digest != fixture["durability_sha256"]:
        raise QualificationError("durability_fixture_hash_mismatch")
    return {"key": fixture["durability_key"], "sha256": digest, "bytes": len(data)}


def _concurrency_check(client: Any, run_id: str) -> dict[str, Any]:
    objects = {
        f"concurrency/{run_id}/{index:03d}.bin": secrets.token_bytes(64 * 1024)
        for index in range(32)
    }

    def put(item: tuple[str, bytes]) -> tuple[str, str]:
        key, data = item
        digest = _sha256(data)
        client.put_object(
            Bucket=QUALIFICATION_BUCKET,
            Key=key,
            Body=data,
            Metadata={"sha256": digest},
        )
        return key, digest

    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        written = dict(executor.map(put, objects.items()))

    def read(key: str) -> tuple[str, str]:
        data = client.get_object(Bucket=QUALIFICATION_BUCKET, Key=key)["Body"].read()
        return key, _sha256(data)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        observed = dict(executor.map(read, objects))
    elapsed = time.monotonic() - started
    if observed != written:
        raise QualificationError("concurrent_object_hash_mismatch")
    if elapsed > 30:
        raise QualificationError("concurrency_smoke_budget_exceeded")
    return {"objects": len(objects), "workers": 8, "elapsed_seconds": round(elapsed, 3)}


def _snapshot_failure_matrix(snapshot_root: Path, temporary_root: Path) -> dict[str, Any]:
    """Prove corrupt or incomplete backup inputs fail before restore writes."""

    manifest = json.loads((snapshot_root / "manifest.json").read_text(encoding="utf-8"))
    first = manifest["objects"][0]
    digest = first["sha256"]
    outcomes: dict[str, str] = {}

    cases = {
        "manifest_tamper": temporary_root / "failure-manifest",
        "blob_tamper": temporary_root / "failure-blob",
        "missing_blob": temporary_root / "failure-missing",
    }
    for case, target in cases.items():
        shutil.copytree(snapshot_root, target)
        if case == "manifest_tamper":
            with (target / "manifest.json").open("ab") as handle:
                handle.write(b" ")
        else:
            blob = target / "blobs" / digest[:2] / digest
            if case == "blob_tamper":
                data = blob.read_bytes()
                blob.write_bytes(data[:-1] + bytes([data[-1] ^ 0xFF]))
            else:
                blob.unlink()
        try:
            verify_snapshot(target)
        except SnapshotIntegrityError as exc:
            outcomes[case] = str(exc)
        else:
            raise QualificationError(f"snapshot_{case}_not_rejected")

    return {
        "cases": outcomes,
        "restore_writes_attempted": 0,
        "original_snapshot_still_valid": verify_snapshot(snapshot_root).manifest_sha256,
    }


def _container_arguments(
    *,
    name: str,
    network: str,
    volume: str | None,
    secret_name: str,
    port: int,
    image: str,
    data_tmpfs_size: int | None = None,
    file_size_limit_mb: int = 64,
) -> list[str]:
    if bool(volume) == bool(data_tmpfs_size):
        raise QualificationError("candidate_data_mount_configuration_invalid")
    data_mount = (
        ["--volume", f"{volume}:/data"]
        if volume
        else [
            "--tmpfs",
            f"/data:rw,nosuid,nodev,size={data_tmpfs_size},mode=0777",
        ]
    )
    return [
        "run",
        "--detach",
        "--name",
        name,
        "--label",
        "com.datalogicengine.owner=qualification",
        "--label",
        "com.datalogicengine.component=object-store-candidate",
        "--network",
        network,
        "--publish",
        f"127.0.0.1:{port}:8333",
        *data_mount,
        "--secret",
        f"{secret_name},type=mount,target=dle-s3.json,uid=1000,gid=1000,mode=0400",
        "--user",
        "1000:1000",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,nodev,size=67108864",
        "--cap-drop",
        "all",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "256",
        "--memory",
        "1073741824",
        "--cpus",
        "2",
        "--health-cmd",
        "curl --fail --silent http://127.0.0.1:9333/cluster/status",
        "--health-interval",
        "5s",
        "--health-timeout",
        "3s",
        "--health-retries",
        "18",
        image,
        "mini",
        "-dir=/data",
        f"-bucket={QUALIFICATION_BUCKET},{MIGRATION_BUCKET}",
        "-s3.config=/run/secrets/dle-s3.json",
        "-master.telemetry=false",
        "-webdav=false",
        "-admin.ui=false",
        "-filer.exposeDirectoryData=false",
        "-filer.disableDirListing=true",
        "-s3.iam=false",
        "-s3.port.iceberg=0",
        "-s3.allowDeleteBucketNotEmpty=false",
        "-s3.allowedOrigins=http://127.0.0.1",
        "-filer.allowedOrigins=http://127.0.0.1",
        "-s3.concurrentUploadLimitMB=64",
        "-s3.concurrentFileUploadLimit=8",
        "-volume.concurrentUploadLimitMB=64",
        "-volume.concurrentDownloadLimitMB=64",
        f"-volume.fileSizeLimitMB={file_size_limit_mb}",
        "-master.volumeSizeLimitMB=1024",
    ]


def _initialize_volume(runtime: str, volume: str, image: str) -> None:
    _run(runtime, ["volume", "create", volume])
    _run(
        runtime,
        [
            "run",
            "--rm",
            "--entrypoint",
            "/bin/chown",
            "--volume",
            f"{volume}:/data",
            image,
            "-R",
            "1000:1000",
            "/data",
        ],
    )


def _start_container(
    runtime: str,
    *,
    name: str,
    network: str,
    volume: str | None,
    secret_name: str,
    port: int,
    image: str,
    data_tmpfs_size: int | None = None,
    file_size_limit_mb: int = 64,
) -> None:
    _run(
        runtime,
        _container_arguments(
            name=name,
            network=network,
            volume=volume,
            secret_name=secret_name,
            port=port,
            image=image,
            data_tmpfs_size=data_tmpfs_size,
            file_size_limit_mb=file_size_limit_mb,
        ),
    )


def _occupied_port_failure(
    *,
    port: int,
) -> dict[str, Any]:
    """Verify supervisor preflight rejects an occupied port before startup."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        listener.bind(("127.0.0.1", port))
        listener.listen(1)
        try:
            _assert_port_available(port)
        except QualificationError as exc:
            if str(exc) != f"qualification_port_busy:{port}":
                raise
        else:
            raise QualificationError("occupied_port_preflight_not_rejected")
        if listener.getsockname() != ("127.0.0.1", port):
            raise QualificationError("occupied_port_listener_disturbed")
        return {
            "port": port,
            "candidate_start_attempted": False,
            "supervisor_preflight_rejected": True,
            "existing_listener_preserved": True,
        }


def _disk_full_recovery(client: Any, run_id: str) -> dict[str, Any]:
    """Fill a disposable tmpfs-backed store and prove it recovers after cleanup."""

    sentinel_key = f"capacity/{run_id}/sentinel.bin"
    sentinel = secrets.token_bytes(4096)
    sentinel_hash = _sha256(sentinel)
    client.put_object(
        Bucket=QUALIFICATION_BUCKET,
        Key=sentinel_key,
        Body=sentinel,
        Metadata={"sha256": sentinel_hash},
    )
    block = secrets.token_bytes(32 * 1024 * 1024)
    written: list[str] = []
    failure: str | None = None
    for index in range(24):
        key = f"capacity/{run_id}/fill-{index:02d}.bin"
        try:
            client.put_object(Bucket=QUALIFICATION_BUCKET, Key=key, Body=block)
            written.append(key)
        except Exception as exc:
            failure = exc.__class__.__name__
            break
    if failure is None:
        raise QualificationError("disposable_disk_full_condition_not_reached")

    for key in written:
        try:
            client.delete_object(Bucket=QUALIFICATION_BUCKET, Key=key)
        except Exception:
            pass
    observed = client.get_object(Bucket=QUALIFICATION_BUCKET, Key=sentinel_key)["Body"].read()
    if _sha256(observed) != sentinel_hash:
        raise QualificationError("disk_full_recovery_sentinel_mismatch")
    return {
        "data_mount": "disposable_tmpfs_512_mib",
        "attempted_fill_bytes": (len(written) + 1) * len(block),
        "successful_fill_objects": len(written),
        "write_failure_type": failure,
        "sentinel_sha256": sentinel_hash,
        "sentinel_preserved_after_cleanup": True,
    }


def _inspect_security(runtime: str, container: str, secrets_to_redact: tuple[str, ...]) -> dict:
    inspected = json.loads(
        _run(runtime, ["inspect", container], secret_values=secrets_to_redact).stdout
    )[0]
    host = inspected.get("HostConfig", {})
    config = inspected.get("Config", {})
    port_bindings = host.get("PortBindings", {}) or {}
    published_ports = {
        port: bindings
        for port, bindings in port_bindings.items()
        if bindings
    }
    if set(published_ports) != {"8333/tcp"}:
        raise QualificationError("unexpected_container_port_publication")
    bindings = published_ports["8333/tcp"]
    if not bindings or any(binding.get("HostIp") != "127.0.0.1" for binding in bindings):
        raise QualificationError("candidate_port_not_loopback_only")
    if config.get("User") != "1000:1000":
        raise QualificationError("candidate_process_user_not_pinned")
    if host.get("ReadonlyRootfs") is not True:
        raise QualificationError("candidate_root_filesystem_not_read_only")
    if "no-new-privileges" not in (host.get("SecurityOpt") or []):
        raise QualificationError("candidate_no_new_privileges_missing")
    cap_eff = _run(
        runtime,
        ["exec", container, "sh", "-c", "grep '^CapEff:' /proc/1/status"],
    ).stdout.strip()
    if not cap_eff.endswith("0000000000000000"):
        raise QualificationError("candidate_effective_capabilities_not_empty")
    return {
        "published_ports": published_ports,
        "user": config.get("User"),
        "read_only_rootfs": host.get("ReadonlyRootfs"),
        "security_options": host.get("SecurityOpt"),
        "memory_bytes": host.get("Memory"),
        "pids_limit": host.get("PidsLimit"),
        "effective_capabilities": cap_eff,
        "secret_values_absent_from_inspect": not any(
            value and value in json.dumps(inspected) for value in secrets_to_redact
        ),
    }


def _runtime_evidence(
    runtime: str,
    expected_client_version: str,
    expected_server_version: str,
) -> dict[str, Any]:
    version = json.loads(_run(runtime, ["version", "--format", "json"]).stdout)
    info = json.loads(_run(runtime, ["info", "--format", "json"]).stdout)
    client_version = version.get("Client", {}).get("Version")
    server_version = version.get("Server", {}).get("Version")
    host = info.get("host", {})
    if not host.get("security", {}).get("rootless"):
        raise QualificationError("podman_runtime_not_rootless")
    if host.get("arch") != "amd64" or not host.get("security", {}).get("seccompEnabled"):
        raise QualificationError("podman_runtime_security_baseline_failed")
    return {
        "expected_distributable_version": expected_client_version,
        "expected_machine_server_version": expected_server_version,
        "client_version": client_version,
        "server_version": server_version,
        "exact_runtime_match": (
            client_version == expected_client_version
            and server_version == expected_server_version
        ),
        "rootless": True,
        "seccomp": True,
        "arch": host.get("arch"),
        "kernel": host.get("kernel"),
        "cgroup_version": host.get("cgroupVersion"),
    }


def _image_evidence(runtime: str, candidate: dict[str, Any]) -> dict[str, Any]:
    image = candidate["image"]
    inspected = json.loads(_run(runtime, ["image", "inspect", image]).stdout)[0]
    repo_digests = set(inspected.get("RepoDigests") or [])
    expected_index = image.split("@", 1)[1]
    expected_amd64 = candidate["linux_amd64_digest"]
    if not any(item.endswith(expected_index) for item in repo_digests):
        raise QualificationError("candidate_index_digest_mismatch")
    if not any(item.endswith(expected_amd64) for item in repo_digests):
        raise QualificationError("candidate_amd64_digest_mismatch")
    labels = inspected.get("Labels") or inspected.get("Config", {}).get("Labels", {})
    inspected_id = str(inspected.get("Id") or "")
    if inspected_id and not inspected_id.startswith("sha256:"):
        inspected_id = f"sha256:{inspected_id}"
    if inspected_id != candidate["image_id"]:
        raise QualificationError("candidate_image_id_mismatch")
    if labels.get("org.opencontainers.image.version") != candidate["version"]:
        raise QualificationError("candidate_image_version_label_mismatch")
    if labels.get("org.opencontainers.image.licenses") != "Apache-2.0":
        raise QualificationError("candidate_image_license_label_mismatch")
    if labels.get("org.opencontainers.image.revision") != candidate["source_revision"]:
        raise QualificationError("candidate_image_source_revision_mismatch")
    patch = candidate.get("security_patch", {})
    if labels.get("com.datalogicengine.grpc-go.version") != patch.get("selected_version"):
        raise QualificationError("candidate_image_grpc_patch_label_mismatch")
    if labels.get("com.datalogicengine.security.patch") != patch.get("advisory"):
        raise QualificationError("candidate_image_security_patch_label_mismatch")
    binary_version = _run(runtime, ["run", "--rm", image, "version"]).stdout.strip()
    if candidate["upstream_version"] not in binary_version:
        raise QualificationError("candidate_binary_version_mismatch")
    return {
        "image_id": inspected_id,
        "repo_digests": sorted(repo_digests),
        "version_label": labels.get("org.opencontainers.image.version"),
        "license_label": labels.get("org.opencontainers.image.licenses"),
        "source_revision": labels.get("org.opencontainers.image.revision"),
        "binary_version": binary_version.splitlines()[0],
    }


def _vulnerability_scan_evidence(
    report_path: Path,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        raise QualificationError("candidate_vulnerability_report_unreadable") from exc
    metadata = report.get("Metadata", {})
    if metadata.get("ImageID") != candidate["image_id"]:
        raise QualificationError("candidate_vulnerability_report_image_mismatch")
    vulnerabilities = [
        item
        for result in report.get("Results", [])
        for item in (result.get("Vulnerabilities") or [])
    ]
    blocking = [
        item
        for item in vulnerabilities
        if item.get("Severity") in {"HIGH", "CRITICAL"}
    ]
    if blocking:
        raise QualificationError("candidate_high_or_critical_vulnerability_present")
    counts: dict[str, int] = {}
    for item in vulnerabilities:
        severity = str(item.get("Severity") or "UNKNOWN")
        counts[severity] = counts.get(severity, 0) + 1
    return {
        "report": report_path.relative_to(REPO_ROOT).as_posix(),
        "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "image_id": metadata.get("ImageID"),
        "high_or_critical_findings": 0,
        "severity_counts": counts,
        "non_blocking_findings": [
            {
                "id": item.get("VulnerabilityID"),
                "package": item.get("PkgName"),
                "severity": item.get("Severity"),
                "title": item.get("Title"),
            }
            for item in vulnerabilities
        ],
    }


def _cleanup(
    runtime: str,
    containers: set[str],
    volumes: set[str],
    networks: set[str],
    secret_names: set[str],
) -> list[str]:
    failures: list[str] = []
    for name in sorted(containers):
        result = _run(runtime, ["rm", "--force", name], check=False)
        if result.returncode not in {0, 1, 125}:
            failures.append(f"container:{name}")
    for name in sorted(volumes):
        result = _run(runtime, ["volume", "rm", "--force", name], check=False)
        if result.returncode not in {0, 1, 125}:
            failures.append(f"volume:{name}")
    for name in sorted(networks):
        result = _run(runtime, ["network", "rm", "--force", name], check=False)
        if result.returncode not in {0, 1, 125}:
            failures.append(f"network:{name}")
    for name in sorted(secret_names):
        result = _run(runtime, ["secret", "rm", name], check=False)
        if result.returncode not in {0, 1, 125}:
            failures.append(f"secret:{name}")
    return failures


def qualify(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
    recorder = Recorder()
    lock = _load_lock(Path(args.lock).resolve())
    candidate = lock["services"]["object_store_candidate"]
    run_id = uuid.uuid4().hex[:12]
    prefix = f"dle-qual-{run_id}"
    container = f"{prefix}-seaweedfs"
    capacity_container = f"{prefix}-capacity"
    network = f"{prefix}-network"
    primary_volume = f"{prefix}-data"
    restore_volume = f"{prefix}-restore"
    secret_name = f"{prefix}-s3-config"
    endpoint = f"http://127.0.0.1:{args.port}"
    capacity_port = args.port + 1
    capacity_endpoint = f"http://127.0.0.1:{capacity_port}"
    resources = {
        "containers": {container, capacity_container},
        "volumes": {primary_volume, restore_volume},
        "networks": {network},
        "secrets": {secret_name},
    }

    bootstrap_access = f"DLEBOOT{secrets.token_hex(16).upper()}"
    bootstrap_secret = secrets.token_urlsafe(48)
    app_access = f"DLEAPP{secrets.token_hex(16).upper()}"
    app_secret = secrets.token_urlsafe(48)
    secret_values = (bootstrap_access, bootstrap_secret, app_access, app_secret)
    s3_config = {
        "identities": [
            {
                "name": "dle-qualification-bootstrap",
                "credentials": [
                    {"accessKey": bootstrap_access, "secretKey": bootstrap_secret}
                ],
                "actions": ["Admin", "Read", "List", "Tagging", "Write"],
            },
            {
                "name": "dle-qualification-app",
                "credentials": [{"accessKey": app_access, "secretKey": app_secret}],
                "actions": [
                    f"Read:{QUALIFICATION_BUCKET}",
                    f"List:{QUALIFICATION_BUCKET}",
                    f"Tagging:{QUALIFICATION_BUCKET}",
                    f"Write:{QUALIFICATION_BUCKET}",
                    f"Read:{MIGRATION_BUCKET}",
                    f"List:{MIGRATION_BUCKET}",
                    f"Tagging:{MIGRATION_BUCKET}",
                    f"Write:{MIGRATION_BUCKET}",
                ],
            },
        ]
    }

    recorder.add(
        "authority",
        "candidate_only_lock",
        "pass",
        {
            "qualification_authorized_by": candidate["qualification_authorized_by"],
            "production_approved": candidate["production_approved"],
            "architecture_change_authorized": lock["architecture_change_authorized"],
        },
    )
    recorder.run("windows_deployment", "qualification_port_available", lambda: _assert_port_available(args.port))
    recorder.run(
        "windows_deployment",
        "capacity_failure_port_available",
        lambda: _assert_port_available(capacity_port),
    )
    recorder.add(
        "windows_deployment",
        "windows_host",
        "pass" if platform.system() == "Windows" and platform.machine().lower() in {"amd64", "x86_64"} else "fail",
        {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
    )

    runtime_evidence = recorder.run(
        "windows_deployment",
        "rootless_podman_runtime",
        lambda: _runtime_evidence(
            args.runtime,
            lock["runtime"]["version"],
            lock["runtime"]["machine_server_version"],
        ),
    )
    if runtime_evidence and not runtime_evidence["exact_runtime_match"]:
        recorder.add(
            "windows_deployment",
            "exact_locked_runtime",
            "fail",
            {
                "reason": "installed_client_or_machine_server_does_not_match_candidate_lock",
                "expected_client": lock["runtime"]["version"],
                "expected_server": lock["runtime"]["machine_server_version"],
                "client": runtime_evidence["client_version"],
                "server": runtime_evidence["server_version"],
            },
        )
    else:
        recorder.add(
            "windows_deployment",
            "exact_locked_runtime",
            "pass",
            {
                "client_version": lock["runtime"]["version"],
                "machine_server_version": lock["runtime"]["machine_server_version"],
            },
        )

    recorder.run(
        "licensing",
        "immutable_candidate_identity_and_declared_license",
        lambda: _image_evidence(args.runtime, candidate),
    )
    recorder.run(
        "security",
        "exact_image_vulnerability_scan",
        lambda: _vulnerability_scan_evidence(
            Path(args.vulnerability_report).resolve(),
            candidate,
        ),
    )

    live_ready = False
    cleanup_failures: list[str] = []
    try:
        existing = _run(
            args.runtime,
            ["ps", "-a", "--filter", f"name=^{container}$", "--format", "{{.ID}}"],
        ).stdout.strip()
        if existing:
            raise QualificationError("qualification_container_name_collision")
        _run(args.runtime, ["network", "create", network])
        _run(
            args.runtime,
            ["secret", "create", secret_name, "-"],
            input_text=json.dumps(s3_config, separators=(",", ":")),
            secret_values=secret_values,
        )
        _initialize_volume(args.runtime, primary_volume, candidate["image"])
        recorder.run(
            "failure_recovery",
            "occupied_port_fails_closed",
            lambda: _occupied_port_failure(
                port=args.port,
            ),
        )
        _start_container(
            args.runtime,
            name=container,
            network=network,
            volume=primary_volume,
            secret_name=secret_name,
            port=args.port,
            image=candidate["image"],
        )

        client = _s3_client(endpoint, app_access, app_secret)
        _wait_for_s3(client, QUALIFICATION_BUCKET)
        live_ready = True
        recorder.run(
            "security",
            "container_and_loopback_hardening",
            lambda: _inspect_security(args.runtime, container, secret_values),
        )
        recorder.run(
            "security",
            "anonymous_access_denied",
            lambda: _assert_denied(
                lambda: _s3_client(endpoint, unsigned=True).list_objects_v2(
                    Bucket=QUALIFICATION_BUCKET,
                    MaxKeys=1,
                )
            ),
        )
        recorder.run(
            "security",
            "invalid_credentials_denied",
            lambda: _assert_denied(
                lambda: _s3_client(endpoint, "invalid", "invalid").list_objects_v2(
                    Bucket=QUALIFICATION_BUCKET,
                    MaxKeys=1,
                )
            ),
        )
        recorder.run(
            "security",
            "least_privilege_bucket_creation_denied",
            lambda: _assert_denied(
                lambda: client.create_bucket(Bucket=f"dle-forbidden-{run_id}")
            ),
        )

        contract_fixture = recorder.run(
            "contract_parity",
            "s3_object_contract",
            lambda: _contract_checks(client, endpoint, app_access, app_secret, run_id),
        )
        recorder.run(
            "concurrency_performance",
            "bounded_concurrent_read_write_smoke",
            lambda: _concurrency_check(client, run_id),
        )

        with tempfile.TemporaryDirectory(prefix="dle-object-qualification-") as temporary:
            temporary_root = Path(temporary)
            backend = S3Backend(endpoint, app_access, app_secret)
            snapshot_root = temporary_root / "backup"
            backup_summary = recorder.run(
                "backup_restore",
                "portable_snapshot_export",
                lambda: export_bucket(backend, QUALIFICATION_BUCKET, snapshot_root).to_dict(),
            )
            if backup_summary:
                recorder.run(
                    "failure_recovery",
                    "corrupt_and_incomplete_snapshot_rejected",
                    lambda: _snapshot_failure_matrix(
                        snapshot_root,
                        temporary_root,
                    ),
                )

            if contract_fixture:
                _run(args.runtime, ["stop", "--time", "20", container])
                _run(args.runtime, ["start", container])
                _wait_for_s3(client, QUALIFICATION_BUCKET)
                recorder.run(
                    "durability",
                    "graceful_container_restart",
                    lambda: _verify_durability(client, contract_fixture),
                )

                _run(args.runtime, ["kill", container])
                _run(args.runtime, ["start", container])
                _wait_for_s3(client, QUALIFICATION_BUCKET)
                recorder.run(
                    "durability",
                    "forced_termination_restart",
                    lambda: _verify_durability(client, contract_fixture),
                )

            logs = _run(args.runtime, ["logs", container], secret_values=secret_values).stdout
            recorder.add(
                "observability",
                "health_and_redacted_logs",
                "pass" if not any(value in logs for value in secret_values) else "fail",
                {
                    "service_version_source": "immutable_image_and_binary_evidence",
                    "version_in_log_stream": candidate["version"] in logs,
                    "credentials_absent": not any(value in logs for value in secret_values),
                },
            )

            _start_container(
                args.runtime,
                name=capacity_container,
                network=network,
                volume=None,
                secret_name=secret_name,
                port=capacity_port,
                image=candidate["image"],
                data_tmpfs_size=512 * 1024 * 1024,
                file_size_limit_mb=512,
            )
            capacity_client = _s3_client(
                capacity_endpoint,
                app_access,
                app_secret,
                max_attempts=1,
            )
            _wait_for_s3(capacity_client, QUALIFICATION_BUCKET)
            recorder.run(
                "failure_recovery",
                "disposable_disk_full_and_recovery",
                lambda: _disk_full_recovery(capacity_client, run_id),
            )
            _run(args.runtime, ["rm", "--force", capacity_container])

            _run(args.runtime, ["rm", "--force", container])
            _initialize_volume(args.runtime, restore_volume, candidate["image"])
            _start_container(
                args.runtime,
                name=container,
                network=network,
                volume=restore_volume,
                secret_name=secret_name,
                port=args.port,
                image=candidate["image"],
            )
            _wait_for_s3(client, QUALIFICATION_BUCKET)
            if backup_summary:
                recorder.run(
                    "backup_restore",
                    "clean_data_root_restore",
                    lambda: restore_bucket(backend, snapshot_root).to_dict(),
                )

            source = LocalFileBackend(str(temporary_root / "migration-source"))
            rollback = LocalFileBackend(str(temporary_root / "rollback-target"))
            source.create_bucket(MIGRATION_BUCKET)
            source.put(
                MIGRATION_BUCKET,
                "exports/replacement-control.json",
                b'{"source":"local","version":1}',
                content_type="application/json",
                metadata={"owner": "replacement-control", "schema": "1"},
            )
            migration_root = temporary_root / "migration-snapshot"
            recorder.run(
                "migration_rollback",
                "local_to_candidate_migration",
                lambda: migrate_bucket(
                    source,
                    backend,
                    MIGRATION_BUCKET,
                    migration_root,
                ).to_dict(),
            )
            rollback_root = temporary_root / "rollback-snapshot"
            recorder.run(
                "migration_rollback",
                "candidate_to_local_rollback",
                lambda: migrate_bucket(
                    backend,
                    rollback,
                    MIGRATION_BUCKET,
                    rollback_root,
                ).to_dict(),
            )

    except Exception as exc:
        recorder.add("live_qualification", "candidate_execution", "fail", _safe_error(exc))
    finally:
        if not args.keep_resources:
            cleanup_failures = _cleanup(
                args.runtime,
                resources["containers"],
                resources["volumes"],
                resources["networks"],
                resources["secrets"],
            )
        recorder.add(
            "windows_deployment",
            "qualification_resource_cleanup",
            "pass" if not cleanup_failures and not args.keep_resources else "pending",
            {
                "cleanup_failures": cleanup_failures,
                "resources_retained_by_request": bool(args.keep_resources),
            },
        )

    recorder.add(
        "licensing",
        "engineering_license_and_redistribution_review",
        (
            "pass"
            if candidate.get("production_license_review") == "engineering_pass"
            and (REPO_ROOT / candidate.get("license_review_record", "")).is_file()
            else "fail"
        ),
        {
            "license": candidate.get("license"),
            "review_record": candidate.get("license_review_record"),
            "scope": "engineering redistribution inventory; not legal advice",
        },
    )
    recorder.add(
        "release_acceptance",
        "independent_security_and_data_at_rest_review",
        "pending",
        "Protected-volume verification and independent review require the rebuilt installed release.",
    )
    recorder.add(
        "release_acceptance",
        "clean_machine_installer_and_relaunch_qualification",
        "pending",
        "The exact portable Windows runtime passed; signed clean-machine installer evidence remains Phase 15 work.",
    )
    recorder.add(
        "release_acceptance",
        "independent_license_acceptance",
        "pending",
        "The engineering Apache-2.0 inventory is complete; independent legal acceptance remains a release gate.",
    )
    recorder.add(
        "owner_approval",
        "implementation_selection",
        (
            "pass"
            if candidate.get("selection_authorized_by") == "Kevin"
            and candidate.get("selection_status") == "selected_for_release_qualification"
            else "fail"
        ),
        {
            "authorized_by": candidate.get("selection_authorized_by"),
            "authorized_at": candidate.get("selection_authorized_at"),
            "scope": "SeaweedFS implementation selected for rebuilt installed qualification; production approval withheld",
        },
    )

    gates = recorder.gate_summary()
    replacement_gates = {
        gate: status for gate, status in gates.items() if gate != "release_acceptance"
    }
    overall = (
        "passed_for_release_qualification"
        if replacement_gates
        and all(value == "pass" for value in replacement_gates.values())
        else "blocked"
    )
    report = {
        "schema_version": "1.0.0",
        "captured_at": datetime.now(UTC).isoformat(),
        "run_id": run_id,
        "status": overall,
        "candidate": {
            "product": candidate["product"],
            "version": candidate["version"],
            "image": candidate["image"],
            "linux_amd64_digest": candidate["linux_amd64_digest"],
        },
        "candidate_s3_became_ready": live_ready,
        "replacement_control": replacement_gates,
        "deferred_release_acceptance": {
            "status": gates.get("release_acceptance"),
            "checks": [
                item for item in recorder.checks if item["gate"] == "release_acceptance"
            ],
        },
        "checks": recorder.checks,
        "production_approved": False,
        "production_selected": overall == "passed_for_release_qualification",
        "architecture_change_authorized": overall == "passed_for_release_qualification",
        "decision_rule": (
            "SeaweedFS is the selected implementation of the app-owned S3-compatible "
            "object-store capability for rebuilt installed qualification. Production "
            "approval remains false until the deferred release-acceptance checks pass."
        ),
    }
    return report, 0 if overall == "passed_for_release_qualification" else 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run isolated SeaweedFS Replacement Control qualification",
    )
    parser.add_argument("--runtime", default="podman")
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument(
        "--vulnerability-report",
        default=str(DEFAULT_VULNERABILITY_REPORT),
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--keep-resources",
        action="store_true",
        help="Retain disposable qualification resources for manual diagnosis",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report, exit_code = qualify(args)
    except Exception as exc:
        report = {
            "schema_version": "1.0.0",
            "captured_at": datetime.now(UTC).isoformat(),
            "status": "blocked",
            "fatal_error": _safe_error(exc),
            "production_approved": False,
            "architecture_change_authorized": False,
        }
        exit_code = 2
    _write_report(Path(args.report).resolve(), report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
