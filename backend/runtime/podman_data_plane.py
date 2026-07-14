"""App-owned immutable Podman data-plane lifecycle adapter.

The adapter is deliberately strict about authority.  Qualification profiles may
exercise the locked engineering candidates, while a production profile can be
constructed only after the candidate lock explicitly approves every artifact.
It never pulls images, adopts foreign containers, or falls back to another
storage implementation.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .data_plane_delivery import (
    DataPlaneCredentialVault,
    DataPlaneDeliveryError,
    DataPlanePlan,
    build_delivery_plan,
    load_candidate_lock,
)


APP_SERVICE_KEYS = ("postgresql", "redis", "neo4j", "chroma", "minio")
LOCK_SERVICE_KEYS = {
    "postgresql": "postgresql",
    "redis": "redis",
    "neo4j": "neo4j",
    "chroma": "chromadb",
    "minio": "object_store_candidate",
}
REQUIRED_OBJECT_BUCKETS = (
    "audit-logs",
    "simulation-artifacts",
    "deliverables",
    "graphs",
    "evaluation-data",
    "trace-exports",
    "gateway-results",
)


class PodmanDataPlaneError(RuntimeError):
    """Safely reportable data-plane lifecycle failure."""


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True, slots=True)
class ServiceRuntimeSpec:
    name: str
    lock_key: str
    container_name: str
    identity: str
    endpoint: str
    publish: tuple[tuple[int, int], ...]
    memory_bytes: int
    cpus: float
    pids_limit: int
    user: str
    volumes: tuple[tuple[str, str], ...]
    secrets: tuple[tuple[str, str, str], ...]
    environment: tuple[tuple[str, str], ...]
    tmpfs: tuple[str, ...]
    command: tuple[str, ...]


class PodmanDataPlaneManager:
    """Own one installation-specific five-service Podman profile."""

    def __init__(
        self,
        *,
        runtime_root: str | Path,
        installation_id: str,
        profile: str,
        lock_path: str | Path,
        runtime: str = "podman",
        require_dpapi: bool | None = None,
        command_timeout_seconds: float = 180.0,
    ) -> None:
        self.runtime_root = Path(runtime_root).resolve()
        self.installation_id = str(installation_id).strip().lower()
        self.profile = str(profile).strip().lower()
        self.lock_path = Path(lock_path).resolve()
        self.runtime = runtime
        self.command_timeout_seconds = max(5.0, float(command_timeout_seconds))
        self.lock, self.artifacts = load_candidate_lock(self.lock_path)
        self.plan: DataPlanePlan = build_delivery_plan(
            self.lock_path,
            self.installation_id,
            profile=self.profile,
        )
        dpapi_required = os.name == "nt" if require_dpapi is None else bool(require_dpapi)
        self.vault = DataPlaneCredentialVault(
            self.runtime_root / "security" / "data-plane-credentials.json",
            require_dpapi=dpapi_required,
        )
        self.credentials = self.vault.load_or_create(self.installation_id)
        self.prefix = f"dle-{self.installation_id[:12]}"
        self.network_name = self.plan.network_name
        self._last_failure: dict[str, str] = {}
        self._specs = self._build_specs()

    @property
    def last_failure_reasons(self) -> dict[str, str]:
        return dict(self._last_failure)

    def expected_identity(self, service: str) -> str:
        return self._require_spec(service).identity

    def endpoint(self, service: str) -> str:
        return self._require_spec(service).endpoint

    def connection_settings(self) -> dict[str, Any]:
        ports = {item.name: item.host_ports for item in self.plan.services}
        postgres = self.credentials["postgresql"]
        redis = self.credentials["redis"]
        neo4j = self.credentials["neo4j"]
        object_store = self.credentials["object_store_app"]
        postgres_port = ports["postgresql"][0]
        redis_port = ports["redis"][0]
        neo4j_bolt, neo4j_http = ports["neo4j"]
        chroma_port = ports["chromadb"][0]
        object_port = ports["object_store_candidate"][0]
        return {
            "database_url": (
                f"postgresql://{quote(postgres.username, safe='')}:{quote(postgres.password, safe='')}"
                f"@127.0.0.1:{postgres_port}/datalogic"
            ),
            "redis_url": (
                f"redis://{quote(redis.username, safe='')}:{quote(redis.password, safe='')}"
                f"@127.0.0.1:{redis_port}/0"
            ),
            "neo4j_uri": f"bolt://127.0.0.1:{neo4j_bolt}",
            "neo4j_http_uri": f"http://127.0.0.1:{neo4j_http}",
            "neo4j_user": neo4j.username,
            "neo4j_password": neo4j.password,
            "chroma_host": "127.0.0.1",
            "chroma_port": chroma_port,
            "object_endpoint": f"http://127.0.0.1:{object_port}",
            "object_access_key": object_store.access_key,
            "object_secret_key": object_store.secret_key,
            "object_region": "us-east-1",
            "object_buckets": REQUIRED_OBJECT_BUCKETS,
        }

    def migration_connection_settings(self) -> dict[str, str]:
        """Return the dedicated schema-owner connection without changing app credentials."""
        ports = {item.name: item.host_ports for item in self.plan.services}
        credential = self.credentials["postgresql_migration"]
        return {
            "database_url": (
                f"postgresql://{quote(credential.username, safe='')}:"
                f"{quote(credential.password, safe='')}@127.0.0.1:"
                f"{ports['postgresql'][0]}/datalogic"
            )
        }

    def recovery_connection_settings(self) -> dict[str, str]:
        """Return recovery-only credentials that normal application code never uses."""
        ports = {item.name: item.host_ports for item in self.plan.services}
        credential = self.credentials["redis_recovery"]
        return {
            "redis_url": (
                f"redis://{quote(credential.username, safe='')}:"
                f"{quote(credential.password, safe='')}@127.0.0.1:"
                f"{ports['redis'][0]}/0"
            )
        }

    def export_postgresql_logical_backup(self, destination: str | Path) -> dict[str, Any]:
        """Create and verify a custom-format pg_dump with the migration identity."""
        target = Path(destination).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        spec = self._require_spec("postgresql")
        inspected = self._inspect_container(spec.container_name)
        if inspected is None:
            raise PodmanDataPlaneError("postgresql_backup_service_missing")
        self._assert_owned_container(spec, inspected)
        remote = "/tmp/dle-coordinated-backup.dump"
        command = (
            "PGPASSWORD=$(cat /run/secrets/postgres-password) "
            "pg_dump --username=dle_migration --dbname=datalogic "
            f"--format=custom --file={remote}"
        )
        try:
            self._run(["exec", spec.container_name, "sh", "-c", command])
            self._run(["exec", spec.container_name, "pg_restore", "--list", remote])
            self._run(["cp", f"{spec.container_name}:{remote}", str(target)])
        except Exception as exc:
            target.unlink(missing_ok=True)
            raise PodmanDataPlaneError("postgresql_logical_backup_failed") from exc
        finally:
            self._run(
                ["exec", spec.container_name, "rm", "-f", remote],
                check=False,
            )
        if not target.is_file() or target.stat().st_size <= 0:
            target.unlink(missing_ok=True)
            raise PodmanDataPlaneError("postgresql_logical_backup_empty")
        return {
            "format": "pg_dump_custom",
            "size_bytes": target.stat().st_size,
            "schema_revision": "alembic",
        }

    def restore_postgresql_logical_backup(self, source: str | Path) -> dict[str, Any]:
        """Restore a verified custom-format dump into this manager's isolated database."""
        backup = Path(source).expanduser().resolve()
        if not backup.is_file() or backup.stat().st_size <= 0:
            raise PodmanDataPlaneError("postgresql_restore_backup_missing")
        spec = self._require_spec("postgresql")
        inspected = self._inspect_container(spec.container_name)
        if inspected is None:
            raise PodmanDataPlaneError("postgresql_restore_service_missing")
        self._assert_owned_container(spec, inspected)
        remote = "/tmp/dle-coordinated-restore.dump"
        command = (
            "PGPASSWORD=$(cat /run/secrets/postgres-password) "
            "pg_restore --username=dle_migration --dbname=datalogic "
            "--clean --if-exists --no-owner --no-privileges --exit-on-error "
            f"{remote}"
        )
        try:
            self._run(["cp", str(backup), f"{spec.container_name}:{remote}"])
            self._run(["exec", spec.container_name, "pg_restore", "--list", remote])
            self._run(["exec", spec.container_name, "sh", "-c", command])
            revision = self._run(
                [
                    "exec",
                    spec.container_name,
                    "sh",
                    "-c",
                    "PGPASSWORD=$(cat /run/secrets/postgres-password) "
                    "psql --username=dle_migration --dbname=datalogic "
                    "--tuples-only --no-align --command="
                    "'SELECT version_num FROM alembic_version LIMIT 1'",
                ]
            ).stdout.strip()
            table_count = self._run(
                [
                    "exec",
                    spec.container_name,
                    "sh",
                    "-c",
                    "PGPASSWORD=$(cat /run/secrets/postgres-password) "
                    "psql --username=dle_migration --dbname=datalogic "
                    "--tuples-only --no-align --command="
                    "\"SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public'\"",
                ]
            ).stdout.strip()
        except Exception as exc:
            raise PodmanDataPlaneError("postgresql_logical_restore_failed") from exc
        finally:
            self._run(["exec", spec.container_name, "rm", "-f", remote], check=False)
        if not revision or not table_count.isdigit() or int(table_count) <= 0:
            raise PodmanDataPlaneError("postgresql_logical_restore_verification_failed")
        return {
            "schema_revision": revision,
            "table_count": int(table_count),
            "status": "pass",
        }

    def verify_runtime(self) -> dict[str, Any]:
        version = self._run(["version", "--format", "json"])
        info = self._run(["info", "--format", "json"])
        try:
            version_payload = json.loads(version.stdout)
            info_payload = json.loads(info.stdout)
        except ValueError as exc:
            raise PodmanDataPlaneError("container_runtime_metadata_invalid") from exc
        host = info_payload.get("host", {})
        security = host.get("security", {})
        if not security.get("rootless"):
            raise PodmanDataPlaneError("container_runtime_not_rootless")
        if not security.get("seccompEnabled"):
            raise PodmanDataPlaneError("container_runtime_seccomp_disabled")
        if host.get("arch") != "amd64":
            raise PodmanDataPlaneError("container_runtime_architecture_mismatch")
        return {
            "client_version": version_payload.get("Client", {}).get("Version"),
            "server_version": version_payload.get("Server", {}).get("Version"),
            "expected_distributable_version": self.lock["runtime"]["version"],
            "rootless": True,
            "seccomp": True,
            "arch": host.get("arch"),
        }

    def verify_artifacts(self) -> dict[str, dict[str, Any]]:
        evidence: dict[str, dict[str, Any]] = {}
        for service in APP_SERVICE_KEYS:
            spec = self._require_spec(service)
            artifact = self.artifacts[spec.lock_key]
            inspected = self._run(
                ["image", "inspect", artifact.image],
                check=False,
            )
            if inspected.returncode != 0:
                raise PodmanDataPlaneError(f"service_artifact_not_installed:{service}")
            try:
                payload = json.loads(inspected.stdout)[0]
            except (IndexError, TypeError, ValueError) as exc:
                raise PodmanDataPlaneError(f"service_artifact_metadata_invalid:{service}") from exc
            digests = set(payload.get("RepoDigests") or [])
            expected_digest = artifact.image.rsplit("@", 1)[-1]
            if not any(item.endswith(f"@{expected_digest}") for item in digests):
                raise PodmanDataPlaneError(f"service_artifact_digest_mismatch:{service}")
            evidence[service] = {
                "version": artifact.version,
                "image": artifact.image,
                "linux_amd64_digest": artifact.linux_amd64_digest,
                "license": artifact.license,
            }
        return evidence

    def start_all(self) -> dict[str, bool]:
        self.verify_runtime()
        self.verify_artifacts()
        self._ensure_network()
        return {service: self.start_service(service) for service in APP_SERVICE_KEYS}

    def stop_all(self) -> dict[str, bool]:
        return {
            service: self.stop_service(service)
            for service in reversed(APP_SERVICE_KEYS)
        }

    def start_service(self, service: str) -> bool:
        spec = self._require_spec(service)
        self._last_failure.pop(service, None)
        try:
            self._ensure_network()
            for volume_name, _target in spec.volumes:
                self._ensure_volume(volume_name, spec)
            for secret_name, target, secret_type in spec.secrets:
                self._ensure_secret(secret_name, self._secret_payload(service, target), secret_type)

            existing = self._inspect_container(spec.container_name)
            if existing is not None:
                self._assert_owned_container(spec, existing)
                state = existing.get("State", {})
                if not state.get("Running"):
                    self._run(["start", spec.container_name])
            else:
                self._run(self._container_arguments(spec))
            return self._wait_until_ready(service)
        except Exception as exc:
            self._last_failure[service] = self._safe_reason(exc)
            return False

    def stop_service(self, service: str) -> bool:
        spec = self._require_spec(service)
        inspected = self._inspect_container(spec.container_name)
        if inspected is None or not inspected.get("State", {}).get("Running"):
            return True
        result = self._run(
            ["stop", "--time", "20", spec.container_name],
            check=False,
        )
        if result.returncode != 0:
            self._last_failure[service] = "service_stop_failed"
            return False
        return True

    def restart_service(self, service: str) -> bool:
        if not self.stop_service(service):
            return False
        return self.start_service(service)

    def probe_service(self, service: str) -> tuple[bool, str | None]:
        spec = self._require_spec(service)
        try:
            inspected = self._inspect_container(spec.container_name)
            if inspected is None:
                self._last_failure[service] = "service_container_missing"
                return False, None
            self._assert_owned_container(spec, inspected)
            if not inspected.get("State", {}).get("Running"):
                self._last_failure[service] = "service_container_not_running"
                return False, None
            self._assert_loopback_publication(spec, inspected)
            self._probe_protocol(service)
            self._last_failure.pop(service, None)
            container_id = str(inspected.get("Id") or "")[:12]
            return True, f"{spec.identity}:container={container_id}"
        except Exception as exc:
            self._last_failure[service] = self._safe_reason(exc)
            return False, None

    def status_snapshot(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for service in APP_SERVICE_KEYS:
            spec = self._require_spec(service)
            healthy, identity = self.probe_service(service)
            artifact = self.artifacts[spec.lock_key]
            inspected = self._inspect_container(spec.container_name)
            result[service] = {
                "healthy": healthy,
                "state": (
                    "ready"
                    if healthy
                    else "not_installed"
                    if inspected is None
                    else "failed"
                ),
                "safe_reason": None if healthy else self._last_failure.get(service),
                "expected_identity": spec.identity,
                "observed_identity": identity,
                "endpoint": spec.endpoint,
                "version": artifact.version,
                "expected_version": artifact.version,
                "image": artifact.image,
                "profile": self.profile,
                "production_authorized": self.plan.production_authorized,
            }
        return result

    def service_metadata(self) -> dict[str, dict[str, Any]]:
        """Return immutable redaction-safe metadata without performing probes."""
        result: dict[str, dict[str, Any]] = {}
        for service in APP_SERVICE_KEYS:
            spec = self._require_spec(service)
            artifact = self.artifacts[spec.lock_key]
            result[service] = {
                "version": artifact.version,
                "expected_version": artifact.version,
                "image": artifact.image,
                "endpoint": spec.endpoint,
                "profile": self.profile,
                "production_authorized": self.plan.production_authorized,
            }
        return result

    def remove_qualification_profile(self) -> dict[str, bool]:
        if self.profile != "qualification":
            raise PodmanDataPlaneError("production_profile_removal_requires_installer")
        outcomes: dict[str, bool] = {}
        for service in reversed(APP_SERVICE_KEYS):
            spec = self._require_spec(service)
            outcomes[f"container:{service}"] = self._run(
                ["rm", "--force", spec.container_name], check=False
            ).returncode in {0, 1, 125}
        for spec in self._specs.values():
            for secret_name, _target, _secret_type in spec.secrets:
                outcomes[f"secret:{secret_name}"] = self._run(
                    ["secret", "rm", secret_name], check=False
                ).returncode in {0, 1, 125}
            for volume_name, _target in spec.volumes:
                outcomes[f"volume:{volume_name}"] = self._run(
                    ["volume", "rm", "--force", volume_name], check=False
                ).returncode in {0, 1, 125}
        outcomes[f"network:{self.network_name}"] = self._run(
            ["network", "rm", "--force", self.network_name], check=False
        ).returncode in {0, 1, 125}
        return outcomes

    def _build_specs(self) -> dict[str, ServiceRuntimeSpec]:
        deliveries = {item.name: item for item in self.plan.services}
        pg = deliveries["postgresql"]
        redis = deliveries["redis"]
        neo4j = deliveries["neo4j"]
        chroma = deliveries["chromadb"]
        object_store = deliveries["object_store_candidate"]

        def identity(service: str, lock_key: str) -> str:
            artifact = self.artifacts[lock_key]
            return (
                f"datalogicengine:{self.installation_id}:{service}:"
                f"{artifact.product}:{artifact.version}"
            )

        return {
            "postgresql": ServiceRuntimeSpec(
                "postgresql", "postgresql", pg.container_name,
                identity("postgresql", "postgresql"),
                f"127.0.0.1:{pg.host_ports[0]}", ((pg.host_ports[0], 5432),),
                pg.memory_bytes, pg.cpus, pg.pids_limit, "70:70",
                ((f"{self.prefix}-postgresql-data", "/var/lib/postgresql"),),
                ((f"{self.prefix}-postgresql-password", "postgres-password", "mount"),
                 (f"{self.prefix}-postgresql-init", "/docker-entrypoint-initdb.d/010-dle-roles.sql", "mount"),),
                (("POSTGRES_USER", self.credentials["postgresql_migration"].username),
                 ("POSTGRES_DB", "datalogic"),
                 ("POSTGRES_PASSWORD_FILE", "/run/secrets/postgres-password"),
                 ("POSTGRES_INITDB_ARGS", "--auth-host=scram-sha-256 --auth-local=scram-sha-256"),),
                ("/var/run/postgresql:rw,noexec,nosuid,nodev,size=16777216,mode=0777", "/tmp:rw,noexec,nosuid,nodev,size=67108864,mode=1777"),
                (),
            ),
            "redis": ServiceRuntimeSpec(
                "redis", "redis", redis.container_name,
                identity("redis", "redis"),
                f"127.0.0.1:{redis.host_ports[0]}", ((redis.host_ports[0], 6379),),
                redis.memory_bytes, redis.cpus, redis.pids_limit, "999:999",
                ((f"{self.prefix}-redis-data", "/data"),),
                ((f"{self.prefix}-redis-config", "redis.conf", "mount"),),
                (), ("/tmp:rw,noexec,nosuid,nodev,size=33554432",),
                ("redis-server", "/run/secrets/redis.conf"),
            ),
            "neo4j": ServiceRuntimeSpec(
                "neo4j", "neo4j", neo4j.container_name,
                identity("neo4j", "neo4j"),
                f"127.0.0.1:{neo4j.host_ports[0]}",
                ((neo4j.host_ports[0], 7687), (neo4j.host_ports[1], 7474)),
                neo4j.memory_bytes, neo4j.cpus, neo4j.pids_limit, "7474:7474",
                ((f"{self.prefix}-neo4j-data", "/data"),
                 (f"{self.prefix}-neo4j-logs", "/logs"),
                 (f"{self.prefix}-neo4j-conf", "/var/lib/neo4j/conf")),
                ((f"{self.prefix}-neo4j-auth", "NEO4J_AUTH", "env"),),
                (("NEO4J_server_memory_heap_initial__size", "384m"),
                 ("NEO4J_server_memory_heap_max__size", "768m"),
                 ("NEO4J_server_memory_pagecache_size", "384m"),
                 ("NEO4J_server_default__listen__address", "0.0.0.0"),
                 ("NEO4J_dbms_usage__report_enabled", "false"),),
                ("/tmp:rw,nosuid,nodev,size=268435456",), (),
            ),
            "chroma": ServiceRuntimeSpec(
                "chroma", "chromadb", chroma.container_name,
                identity("chroma", "chromadb"),
                f"127.0.0.1:{chroma.host_ports[0]}", ((chroma.host_ports[0], 8000),),
                chroma.memory_bytes, chroma.cpus, chroma.pids_limit, "65534:65534",
                ((f"{self.prefix}-chroma-data", "/data"),), (),
                (("IS_PERSISTENT", "TRUE"), ("PERSIST_DIRECTORY", "/data"),
                 ("ANONYMIZED_TELEMETRY", "FALSE"), ("ALLOW_RESET", "FALSE"),),
                ("/tmp:rw,noexec,nosuid,nodev,size=134217728",), (),
            ),
            "minio": ServiceRuntimeSpec(
                "minio", "object_store_candidate", object_store.container_name,
                identity("minio", "object_store_candidate"),
                f"127.0.0.1:{object_store.host_ports[0]}", ((object_store.host_ports[0], 8333),),
                object_store.memory_bytes, object_store.cpus, object_store.pids_limit, "1000:1000",
                ((f"{self.prefix}-object-data", "/data"),),
                ((f"{self.prefix}-object-s3-config", "dle-s3.json", "mount"),), (),
                ("/tmp:rw,noexec,nosuid,nodev,size=67108864",),
                ("mini", "-dir=/data", f"-bucket={','.join(REQUIRED_OBJECT_BUCKETS)}",
                 "-s3.config=/run/secrets/dle-s3.json", "-master.telemetry=false",
                 "-webdav=false", "-admin.ui=false", "-filer.exposeDirectoryData=false",
                 "-filer.disableDirListing=true", "-s3.iam=false", "-s3.port.iceberg=0",
                 "-s3.allowDeleteBucketNotEmpty=false", "-s3.allowedOrigins=http://127.0.0.1",
                 "-filer.allowedOrigins=http://127.0.0.1", "-s3.concurrentUploadLimitMB=64",
                 "-s3.concurrentFileUploadLimit=8", "-volume.concurrentUploadLimitMB=64",
                 "-volume.concurrentDownloadLimitMB=64", "-volume.fileSizeLimitMB=64",
                 "-master.volumeSizeLimitMB=1024"),
            ),
        }

    def _container_arguments(self, spec: ServiceRuntimeSpec) -> list[str]:
        artifact = self.artifacts[spec.lock_key]
        arguments = [
            "run", "--detach", "--name", spec.container_name,
            "--restart", "no", "--network", self.network_name,
            "--label", "com.datalogicengine.owner=application",
            "--label", f"com.datalogicengine.installation={self.installation_id}",
            "--label", f"com.datalogicengine.service={spec.name}",
            "--label", f"com.datalogicengine.identity={spec.identity}",
            "--read-only", "--cap-drop", "all",
            "--security-opt", "no-new-privileges",
            "--user", spec.user,
            "--pids-limit", str(spec.pids_limit),
            "--memory", str(spec.memory_bytes), "--cpus", str(spec.cpus),
        ]
        for host_port, container_port in spec.publish:
            arguments.extend(["--publish", f"127.0.0.1:{host_port}:{container_port}"])
        for volume_name, target in spec.volumes:
            arguments.extend(["--volume", f"{volume_name}:{target}"])
        for secret_name, target, secret_type in spec.secrets:
            if secret_type == "env":
                arguments.extend(["--secret", f"{secret_name},type=env,target={target}"])
            else:
                arguments.extend([
                    "--secret", f"{secret_name},type=mount,target={target},mode=0444"
                ])
        for key, value in spec.environment:
            arguments.extend(["--env", f"{key}={value}"])
        for tmpfs in spec.tmpfs:
            arguments.extend(["--tmpfs", tmpfs])
        arguments.append(artifact.image)
        arguments.extend(spec.command)
        return arguments

    def _secret_payload(self, service: str, target: str) -> str:
        if service == "postgresql":
            if target == "postgres-password":
                return self.credentials["postgresql_migration"].password
            if target.endswith("010-dle-roles.sql"):
                app = self.credentials["postgresql"]
                return "\n".join(
                    [
                        f"CREATE ROLE {app.username} LOGIN PASSWORD '{app.password}';",
                        f"GRANT CONNECT ON DATABASE datalogic TO {app.username};",
                        f"GRANT USAGE, CREATE ON SCHEMA public TO {app.username};",
                        f"ALTER DEFAULT PRIVILEGES GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {app.username};",
                        f"ALTER DEFAULT PRIVILEGES GRANT USAGE, SELECT ON SEQUENCES TO {app.username};",
                    ]
                )
        if service == "redis":
            credential = self.credentials["redis"]
            recovery = self.credentials["redis_recovery"]
            return "\n".join(
                [
                    "bind 0.0.0.0",
                    "protected-mode yes",
                    "port 6379",
                    "user default off",
                    f"user {credential.username} on >{credential.password} ~* +@all -@dangerous",
                    f"user {recovery.username} on >{recovery.password} ~* +@all",
                    "appendonly yes",
                    "appendfsync everysec",
                    "save 900 1",
                    "save 300 10",
                    "maxmemory 402653184",
                    "maxmemory-policy noeviction",
                    "dir /data",
                    "logfile \"\"",
                ]
            )
        if service == "neo4j":
            credential = self.credentials["neo4j"]
            return f"{credential.username}/{credential.password}"
        if service == "minio":
            bootstrap = self.credentials["object_store_bootstrap"]
            app = self.credentials["object_store_app"]
            actions = [
                f"{action}:{bucket}"
                for bucket in REQUIRED_OBJECT_BUCKETS
                for action in ("Read", "List", "Tagging", "Write")
            ]
            payload = {
                "identities": [
                    {
                        "name": "dle-bootstrap",
                        "credentials": [{"accessKey": bootstrap.access_key, "secretKey": bootstrap.secret_key}],
                        "actions": ["Admin", "Read", "List", "Tagging", "Write"],
                    },
                    {
                        "name": "dle-application",
                        "credentials": [{"accessKey": app.access_key, "secretKey": app.secret_key}],
                        "actions": actions,
                    },
                ]
            }
            return json.dumps(payload, separators=(",", ":"))
        raise PodmanDataPlaneError(f"service_secret_not_supported:{service}:{target}")

    def _ensure_network(self) -> None:
        result = self._run(["network", "inspect", self.network_name], check=False)
        if result.returncode == 0:
            try:
                inspected = json.loads(result.stdout)[0]
            except (IndexError, TypeError, ValueError) as exc:
                raise PodmanDataPlaneError("service_network_metadata_invalid") from exc
            labels = inspected.get("labels") or inspected.get("Labels") or {}
            owner = labels.get("com.datalogicengine.installation")
            if owner != self.installation_id:
                raise PodmanDataPlaneError("foreign_service_network")
            return
        self._run([
            "network", "create", "--internal",
            "--label", f"com.datalogicengine.installation={self.installation_id}",
            self.network_name,
        ])

    def _ensure_volume(self, name: str, spec: ServiceRuntimeSpec) -> None:
        result = self._run(["volume", "inspect", name], check=False)
        if result.returncode == 0:
            try:
                inspected = json.loads(result.stdout)[0]
            except (IndexError, TypeError, ValueError) as exc:
                raise PodmanDataPlaneError("service_volume_metadata_invalid") from exc
            labels = inspected.get("Labels") or {}
            if labels.get("com.datalogicengine.installation") != self.installation_id:
                raise PodmanDataPlaneError("foreign_service_volume")
        else:
            self._run([
                "volume", "create",
                "--label", f"com.datalogicengine.installation={self.installation_id}",
                name,
            ])
        artifact = self.artifacts[spec.lock_key]
        self._run(
            [
                "run", "--rm", "--entrypoint", "/bin/chown",
                "--volume", f"{name}:/dle-volume",
                artifact.image,
                "-R", spec.user, "/dle-volume",
            ]
        )

    def _ensure_secret(self, name: str, payload: str, secret_type: str) -> None:
        result = self._run(["secret", "inspect", name], check=False)
        if result.returncode == 0:
            return
        created = self._run(["secret", "create", name, "-"], input_text=payload)
        if created.returncode != 0:
            raise PodmanDataPlaneError(f"service_secret_creation_failed:{secret_type}")

    def _inspect_container(self, name: str) -> dict[str, Any] | None:
        result = self._run(["inspect", name], check=False)
        if result.returncode != 0:
            return None
        try:
            return json.loads(result.stdout)[0]
        except (IndexError, TypeError, ValueError) as exc:
            raise PodmanDataPlaneError("service_container_metadata_invalid") from exc

    def _assert_owned_container(self, spec: ServiceRuntimeSpec, inspected: dict[str, Any]) -> None:
        labels = inspected.get("Config", {}).get("Labels") or {}
        if labels.get("com.datalogicengine.installation") != self.installation_id:
            raise PodmanDataPlaneError(f"foreign_service_container:{spec.name}")
        if labels.get("com.datalogicengine.identity") != spec.identity:
            raise PodmanDataPlaneError(f"service_container_identity_mismatch:{spec.name}")
        expected_image = self.artifacts[spec.lock_key].image
        configured_image = str(inspected.get("Config", {}).get("Image") or "")
        if configured_image != expected_image:
            raise PodmanDataPlaneError(f"service_container_image_mismatch:{spec.name}")

    def _assert_loopback_publication(self, spec: ServiceRuntimeSpec, inspected: dict[str, Any]) -> None:
        bindings = inspected.get("HostConfig", {}).get("PortBindings") or {}
        expected = {f"{container}/tcp" for _host, container in spec.publish}
        observed = {key for key, value in bindings.items() if value}
        if observed != expected:
            raise PodmanDataPlaneError(f"service_port_contract_mismatch:{spec.name}")
        for values in bindings.values():
            if any(item.get("HostIp") != "127.0.0.1" for item in values or []):
                raise PodmanDataPlaneError(f"service_not_loopback_only:{spec.name}")

    def _wait_until_ready(self, service: str) -> bool:
        deadline = time.monotonic() + self.command_timeout_seconds
        spec = self._require_spec(service)
        while time.monotonic() < deadline:
            healthy, _identity = self.probe_service(service)
            if healthy:
                return True
            inspected = self._inspect_container(spec.container_name)
            state = (inspected or {}).get("State", {})
            if inspected is not None and state.get("Status") in {"exited", "dead"}:
                self._last_failure[service] = (
                    f"service_exited:code={state.get('ExitCode', 'unknown')}"
                )
                return False
            time.sleep(1)
        self._last_failure[service] = "service_readiness_timeout"
        return False

    def _probe_protocol(self, service: str) -> None:
        settings = self.connection_settings()
        if service == "postgresql":
            try:
                import psycopg2

                with psycopg2.connect(settings["database_url"], connect_timeout=3) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT current_database(), current_user")
                        database, user = cursor.fetchone()
                if database != "datalogic" or user != self.credentials["postgresql"].username:
                    raise PodmanDataPlaneError("postgresql_identity_probe_failed")
                return
            except ImportError as exc:
                raise PodmanDataPlaneError("postgresql_client_not_installed") from exc
        if service == "redis":
            try:
                import redis

                client = redis.Redis.from_url(settings["redis_url"], socket_timeout=3)
                if client.ping() is not True:
                    raise PodmanDataPlaneError("redis_ping_failed")
                return
            except ImportError as exc:
                raise PodmanDataPlaneError("redis_client_not_installed") from exc
        if service == "neo4j":
            try:
                from neo4j import GraphDatabase

                driver = GraphDatabase.driver(
                    settings["neo4j_uri"],
                    auth=(settings["neo4j_user"], settings["neo4j_password"]),
                    connection_timeout=3,
                )
                try:
                    driver.verify_connectivity()
                finally:
                    driver.close()
                return
            except ImportError as exc:
                raise PodmanDataPlaneError("neo4j_client_not_installed") from exc
        if service == "chroma":
            url = f"http://{settings['chroma_host']}:{settings['chroma_port']}/api/v2/heartbeat"
            try:
                with urllib.request.urlopen(url, timeout=3) as response:  # noqa: S310 - loopback only
                    payload = json.loads(response.read().decode("utf-8"))
                if "nanosecond heartbeat" not in payload:
                    raise PodmanDataPlaneError("chroma_heartbeat_invalid")
                return
            except (OSError, ValueError, urllib.error.URLError) as exc:
                raise PodmanDataPlaneError("chroma_heartbeat_failed") from exc
        if service == "minio":
            try:
                import boto3
                from botocore.config import Config

                client = boto3.client(
                    "s3",
                    endpoint_url=settings["object_endpoint"],
                    aws_access_key_id=settings["object_access_key"],
                    aws_secret_access_key=settings["object_secret_key"],
                    region_name=settings["object_region"],
                    config=Config(
                        signature_version="s3v4",
                        s3={"addressing_style": "path"},
                        connect_timeout=3,
                        read_timeout=3,
                        retries={"max_attempts": 1},
                    ),
                )
                for bucket in settings["object_buckets"]:
                    client.list_objects_v2(Bucket=bucket, MaxKeys=1)
                return
            except ImportError as exc:
                raise PodmanDataPlaneError("s3_client_not_installed") from exc
        raise PodmanDataPlaneError(f"service_probe_not_supported:{service}")

    def _run(
        self,
        arguments: list[str],
        *,
        input_text: str | None = None,
        check: bool = True,
    ) -> CommandResult:
        try:
            completed = subprocess.run(  # nosec B603 - fixed executable and typed argument list
                [self.runtime, *arguments],
                input=input_text,
                capture_output=True,
                check=False,
                encoding="utf-8",
                errors="replace",
                shell=False,
                timeout=self.command_timeout_seconds,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PodmanDataPlaneError("container_runtime_execution_failed") from exc
        result = CommandResult(completed.returncode, completed.stdout, completed.stderr)
        if check and result.returncode != 0:
            raise PodmanDataPlaneError("container_runtime_command_failed")
        return result

    def _require_spec(self, service: str) -> ServiceRuntimeSpec:
        try:
            return self._specs[service]
        except KeyError as exc:
            raise KeyError(f"Unknown data-plane service: {service}") from exc

    @staticmethod
    def _safe_reason(exc: Exception) -> str:
        if isinstance(exc, (PodmanDataPlaneError, DataPlaneDeliveryError)):
            reason = str(exc).strip()
            if reason and all(character.isalnum() or character in "_:,-." for character in reason):
                return reason[:160]
        if isinstance(exc, (ConnectionError, TimeoutError, socket.timeout)):
            return "service_connection_failed"
        return "service_operation_failed"


def basic_auth_header(username: str, password: str) -> str:
    """Return a Basic auth header without retaining a plaintext joined value."""

    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"
