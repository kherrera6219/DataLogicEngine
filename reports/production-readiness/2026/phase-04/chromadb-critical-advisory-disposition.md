# ChromaDB Critical Advisory Disposition

## Alert

- GitHub Dependabot alert: 389
- Advisory: `GHSA-f4j7-r4q5-qw2c` / `CVE-2026-45829`
- Severity: Critical
- Affected Python package range: `>=1.0.0, <=1.5.9`
- Patched upstream release available on 2026-07-13: No
- Upstream report: `https://github.com/chroma-core/chroma/issues/6717`

## Live artifact finding

The locked `chromadb/chroma` 1.5.9 image is not the vulnerable Python FastAPI
server. Image inspection shows `chroma run /config.yaml`; the image history
copies `rust/frontend/sample_configs/docker_single_node.yaml` and the compiled
`/chroma/chroma` binary. The Python-server pre-authentication path described by
the advisory is therefore absent from the locked service artifact.

The upstream report also describes a Python-client risk when hostile collection
configuration supplies an embedding function that can enable remote model code.
That path is relevant because DataLogicEngine uses the 1.5.9 Python package as a
client.

## Replacement disposition

1. The vulnerable `chromadb` Python package is no longer a direct or transitive
   dependency and is absent from the hash-locked Python environment.
2. DataLogicEngine now uses an app-owned, restricted Chroma v2 HTTP client that
   accepts only loopback endpoints and caller-supplied vectors.
3. Collection configuration is treated as untrusted data. The client permits
   only Chroma's inert no-embedding markers and rejects named embedding
   functions, remote-code configuration, redirects, non-loopback targets,
   malformed paths, and oversized requests/responses before use.
4. Storage, migration, backup/restore, deletion, lifecycle, and qualification
   callers use the same restricted client boundary.
5. The Rust single-node Chroma service remains digest pinned; the affected
   Python server and vulnerable Python SDK are not shipped or executed.

## Disposition

The affected package has been replaced, so the package-specific production
blocker is remediated rather than suppressed. The candidate lock continues to
keep Chroma production approval and production provisioning disabled until the
rebuilt installed Windows system passes the retained service, security,
recovery, and release gates. GitHub alert 389 is expected to close only after the
replacement manifest is pushed and Dependabot re-evaluates `main`; its server-
side state is recorded separately from this local engineering result.

## Validation

- `requirements.txt` and `requirements.lock` contain no `chromadb` package.
- Eighteen focused client, advisory, and vector-store regressions passed.
- The live five-service data-plane qualification passed real Chroma collection,
  vector add/query/get/delete, restart durability, truthful status, and cleanup
  through the restricted client. Evidence:
  `../phase-03/chroma-sdk-removal-live-qualification.json`.
- An isolated `pip-audit` 2.10.0 run scanned 266 applicable locked dependencies
  and reported zero vulnerabilities. Evidence:
  `../phase-03/chroma-sdk-removal-pip-audit.json`.
