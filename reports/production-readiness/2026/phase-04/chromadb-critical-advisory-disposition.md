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

## Engineering mitigation

1. Every collection get/create/get-or-create call explicitly passes
   `embedding_function=None` and an empty creation configuration.
2. Raw `configuration_json` and serialized schema are recursively inspected
   without deserializing embedding functions.
3. Any persisted embedding-function configuration fails closed before the
   collection is used.
4. DataLogicEngine supplies vectors/query vectors itself; it does not ask Chroma
   to load model code.
5. Static regression coverage prevents storage, backup/restore, deletion, and
   qualification code from bypassing the safe helper.

## Disposition

The mitigation is sufficient to continue pre-release engineering under the
plan's documented-release-blocker rule. It is not a production approval. The
candidate lock keeps `production_approved=false` and production provisioning
disabled. Dependabot alert 389 must remain open until a reviewed patched release
is available, upgraded, adversarially qualified on the installed Windows
profile, and independently reviewed.

## Validation

- Locked image inspection confirmed the compiled Rust binary and Rust single-
  node configuration.
- Five focused advisory regressions passed.
- The complete backend suite passed: 1,880 passed, 18 skipped.
- Ruff, documentation references, public-error scanning, and secret scanning
  passed.
