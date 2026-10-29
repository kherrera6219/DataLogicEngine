# R-3 model-split ingestion authority qualification

Base: `416cf77b3a79429004e5c16a9c667ba15cc3c43f`, Windows, October 28, 2026.

## Observed result

The handoff's compatibility concern reproduces through real RAG ingestion,
RAG search result/citation construction and governed retrieval against the
disposable SQL test database. The tokenizer, embedding model and vector store
are deterministic test doubles. This does not qualify native PostgreSQL,
Chroma, the actual MiniLM tokenizer, or the installed application.

An unsplit source passes. A split source yields no governed evidence:

- The first vector retains the original `ki_` identifier but contains only a
  substring; SQL authority rejects it with `content_hash_mismatch`.
- Later `:chunk:N` identifiers have no matching canonical SQL chunk and are
  rejected with `postgresql_revision_not_eligible`.
- The writer overwrites canonical `chunk_index` and `chunk_count` with model
  family positions. Search citations consequently describe vector positions.
  They have no exact character span tying the result to its SQL parent.

The rejection is safe. Do not make migration pass by bypassing SQL authority,
trusting a vector's parent/hash assertion, or lowering permission/readiness/
content-defense checks. The active hash-based factory is unchanged.

## Concrete repair proposal for owner review

Preserve canonical ingestion positions. Store the model family index separately
and record exact character offsets, parent identity, parent checksum and span
checksum when deriving a vector. At retrieval, resolve the retained SQL
`KnowledgeGraphNode` and `IngestionChunk`, verify the original content against
the SQL checksum and source revision, verify the exact substring and its
checksum, and enforce the existing job/file/object/materialization readiness,
owner, tenant and content-defense checks before selecting evidence.

There are two externally observable citation choices:

1. **Precise span citations (recommended):** retain a distinct evidence ID per
   model span and extend the citation locator with canonical parent identity
   and character offsets. Proposed locator keys for approval are
   `parent_source_id`, `source_span_start`, and `source_span_end`, with offsets
   defined as zero-based Python Unicode character positions, end exclusive,
   relative to the canonical SQL chunk. Preserve the existing canonical
   `chunk_index`/`chunk_count`. Use the parent identity for graph relationships.
2. **Canonical-parent citations:** collapse model hits to one parent, hydrate
   the canonical SQL text, and reuse the existing citation schema. This changes
   evidence selection and may consume more of the bounded evidence budget;
   later relevant spans may be lost under the existing text truncation limit.

The first option is recommended because it preserves the exact retrieved span
and avoids returning unrelated portions of a large parent. Kevin approved
proceeding with this proposal on October 29, including the proposed locator
fields. Implementation, migration, and cutover require their own verification.

## Verification

Initial focused Windows run: 21 passed, zero failures/setup/collection errors.
The eight new qualification cases cover unsplit acceptance, split rejection and
the locator mismatch, plus pending job, missing original/normalized object,
pending chunk, unsafe content, and tenant mismatch rejection. They document
the activation blocker; passing characterization tests do not close it.

The first full Windows run produced 47 failures, 3,443 passes, 18 skips and
35 warnings, with zero setup/collection errors. The selected
`.venv-release311` lacked `asgiref` and had PyJWT 2.13.0 rather than the locked
2.15.1. Async-route errors dominated; one JWT options test and the new report's
missing documentation classification also failed. The classification is now
registered. Restored `asgiref==3.13.0` and `PyJWT==2.15.1` from the existing
lockfile with hash verification and no dependency resolution. The first run
is retained in `reports/r3-source-authority-windows-20261028.txt`.

The rerun with those locked dependencies passed 3,490 tests with 18 skipped,
35 warnings, and zero failures or setup/collection errors. This was the
qualification checkpoint before the subsequent runtime repair; its output is
`reports/r3-source-authority-windows-locked-20261028.txt`.

Unrestricted Ruff reports 61 existing findings, and format-check reports 875
files needing formatting. The new test file passes both checks. `mypy` is
unavailable in this environment; no type-check success is claimed. Outputs are
retained in the corresponding `reports/r3-source-authority-*` files.

No customer records, runtime behavior, model activation, installer, dependency declaration,
or outbound destination was changed.
