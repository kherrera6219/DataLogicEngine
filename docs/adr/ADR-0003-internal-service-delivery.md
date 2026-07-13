# ADR-0003: App-Owned Internal Service Delivery on Windows

## Metadata

| Field | Value |
|---|---|
| Status | Accepted - implementation qualification open |
| Date | 2026-07-13 |
| Decision owner | Product owner |
| Plan checkpoint | CP0-B |

## Context

Production requires PostgreSQL, Redis, Neo4j, ChromaDB, and MinIO as app-owned
Windows services. The application must install, supervise, secure, upgrade, back
up, restore, diagnose, and uninstall the profile without silent fallbacks.

Current Compose is incomplete: ChromaDB is absent, MinIO uses `latest`, other
services use broad tags, and the installer does not deliver the stack.

## Option A - App-managed pinned Linux containers

Advantages:

- one delivery model for all five services;
- official container guidance exists for Neo4j and ChromaDB;
- digest pinning, private networks, health checks, and volumes are direct.

Constraints:

- requires a qualified runtime and Windows virtualization;
- Docker Desktop requires license acceptance and paid commercial use for larger
  enterprises and government entities;
- startup, WSL2/Hyper-V, offline images, updates, resources, and support ownership
  require qualification;
- runtime redistribution requires separate approval.

## Option B - App-managed native Windows sidecars

Advantages:

- avoids a mandatory Linux-container VM;
- PostgreSQL publishes Windows installers and embeddable ZIP binaries;
- Neo4j documents ZIP, PowerShell, and Windows-service operation;
- MinIO documents Windows operation.

Constraints:

- Redis documentation points Windows users to partner product Memurai, adding a
  license/support decision;
- ChromaDB needs qualification as a packaged Python/server sidecar;
- five lifecycle, account, ACL, logging, update, and recovery models increase
  installer complexity;
- Neo4j adds a JDK and service-account hardening lifecycle.

## Evidence sources

- https://docs.docker.com/desktop/setup/install/windows-install/
- https://www.postgresql.org/download/windows/
- https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/
- https://neo4j.com/docs/operations-manual/current/installation/windows/
- https://docs.trychroma.com/guides/deploy/docker
- https://min.io/docs/minio/windows/operations/concepts.html

## Decision

Use **app-managed, immutable pinned OCI containers**. The production reference
runtime is rootless Podman Machine using WSL2 on supported Windows 11 x64 hosts.
Docker Desktop may be used as a developer compatibility runtime, but it is not a
required shipped dependency or the release-qualification authority.

The owner approved the recommended container direction on 2026-07-13. Podman is
selected because its Windows machine model supports WSL2, official restricted-
environment installation exists, and the project is Apache-2.0 licensed. The
application remains responsible for lifecycle, health, credentials, volumes,
upgrades, backup/restore, diagnostics, and removal of its own service profile.

CP0-B approves the architecture and reference runtime. Qualification remains
open under CP0-C, CP0-F, CP0-G, and Phases 3/14/15 for exact runtime/package
versions, redistribution review, immutable images, supervision, volume security,
backup/restore, resource budgets, and prohibited-runtime environments.

Additional runtime evidence:

- Podman Desktop Windows installation and WSL2 requirements:
  https://podman-desktop.io/docs/installation/windows-install
- Restricted/offline Windows installer:
  https://podman-desktop.io/docs/proxy
- Podman Machine Windows providers and rootless behavior:
  https://docs.podman.io/en/latest/markdown/podman-machine.1.html
- Podman source and license:
  https://github.com/containers/podman

## Consequences if approved

The installer/runtime manager owns a complete private digest-pinned profile. No
service may be reported healthy on probe failure, and production may not silently
fall back to bootstrap storage.
