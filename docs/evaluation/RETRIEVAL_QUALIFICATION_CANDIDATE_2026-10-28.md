# Local search evaluation candidate

Status: starting corpus and criteria approved by Kevin on October 28;
qualification in progress, with no search activation or acceptance claim.

This candidate supports R-3 of the frontend/backend/retrieval repair plan.
`retrieval_qualification_v1.json` contains sixteen manually authored fictional
policies, sixteen calibration questions, thirty-two held-out questions, and
twelve unrelated questions. These are fictional test facts, not application
capability claims. These synthetic evaluation runs read or change no retained
customer data; the separate authorized migration preflight is described below.

The generated record is
`reports/retrieval-qualification-candidate-20261028.json`. It includes corpus,
script and model hashes, package versions and per-query results. Run
`python -m scripts.evaluate_retrieval_qualification --help` for the required
local model and fingerprint arguments. Model loading is local-only.

| Method | Calibration top 1 / top 4 | Held-out top 1 / top 4 |
|---|---|---|
| Existing hash projection | 0/16; 1/16 | 2/32; 10/32 |
| Lexical token overlap | 11/16; 14/16 | 16/32; 21/32 |
| Offline MiniLM | 16/16; 16/16 | 29/32; 32/32 |
| Equal-weight reciprocal rank fusion | 15/16; 16/16 | 24/32; 31/32 |

At cosine similarity 0.25, MiniLM retained all thirty-two held-out targets
among the first four results and matched none of twelve unrelated queries.
Warm semantic query encoding/ranking p95 was approximately 27 ms; this excludes
database, application and UI latency. Loading and encoding the sixteen records
took approximately nine seconds on the second process run. This is not a
cold-machine startup bound. Cosine similarity is different from the active
index's existing `1 - squared L2 distance` score: 0.25 is not a drop-in threshold
for the old collection or existing UI confidence.

Owner-approved gates: at least 95% held-out top-four recall,
at most 10% unrelated queries receiving a match, and warm local semantic query
p95 below one second. Scores are retrieval relevance, not answer confidence.

This set remains too small and simple for production accuracy claims. Long
documents and truncation, near-duplicate/version conflicts, multiple owners,
source eligibility, deletion/retention, latency with a larger index, and
interrupted migration/rollback must be qualified separately. The held-out split
must not be repeatedly tuned against; freeze a calibration-selected candidate
and add fresh held-out cases before final acceptance. Permission checks are
mandatory regardless of ranking quality. The active app still uses its existing
hash projection. No model package, collection, customer migration or cutover is
enabled by this artifact.

## Long-document extension

The approved extension places each fictional policy after a repeated handbook
introduction and reuses its two held-out questions. This is a truncation stress
check rather than a new independent accuracy sample. The reproducible tool is
`scripts/evaluate_long_document_retrieval.py`, with per-query output in
`reports/retrieval-long-document-candidate-20261028.json`.

The existing 512-unit chunker produced 32 pieces, all exceeding the model's
256-token input limit (largest 521 tokens), and retained 0/32 intended sources
in the first four results at cosine 0.25. A tokenizer-aware prototype produced
80 exact-source spans, with no piece exceeding 256 tokens, and retained 32/32
intended sources. Its budget reserves the model's two required special tokens
and uses the remaining capacity; it does not lower the model's supported limit.
Source `fa28f99f` integrates this chunker for document ingestion when a local
embedding model is explicitly injected into RAG. Thirty-two focused tests
pass. The repeated real-tokenizer screen in
`reports/retrieval-long-document-integrated-chunker-20261028.json` retains
32/32 targets with no over-limit inputs. The active app factory still uses the
hash projection. Long chat and knowledge entries, permission, retention and
migration checks remain open.

## Windows bundle probe

Later source checkpoint `feb6ca6c` adds replaceable model-sized vector families
and a distinct namespace bound to the model, chunker, dimensions and cosine
metric. The combined focused Windows group passes 73 tests. The disposable
real-service record is `reports/profiled-model-vector-families-probe-20261028.json`:
metric calculation, legacy collection preservation, other-owner exclusion,
active-session exclusion, idempotent retry, shorter-text replacement and complete
deletion pass. These checks do not activate the new namespace or qualify a
retained-data migration. Derived structured caches still need compatibility
checks, and full regression/installed acceptance remain open after these changes.

The separate probe `scripts/probe_offline_embedding_bundle.py` also passed as a
Windows frozen executable with socket connection methods blocked: 384 output
dimensions, zero attempted connections, relevant cosine approximately 0.7396
versus unrelated approximately -0.00017. The frozen process reported about
24.3 seconds for loading, fingerprint checks and three embeddings. This is
not an application startup or installed-app performance measurement.

The test used PyInstaller 6.18.0 in one-directory mode, the pinned cached model
as `offline-model`, and explicit hidden imports for the BERT model/configuration/
tokenizer and SentenceTransformer Transformer/Pooling modules. The generated
probe stdout is `reports/offline-embedding-frozen-probe-20261028.txt`. Its EXE
SHA-256 is `f7fa170c7dc5e20f980411dad8d131577209dc4fd3bb56267c6b06468dbdb04b`.
The entire probe directory has 9,958 files totaling 1,019,374,444 bytes; the EXE
hash alone is not an integrity digest for that directory. Binary output remains
in ignored local build storage, not in the application installer.

The installed library dependency inventory and candidate advisory audit are
`reports/offline-embedding-candidate-inventory.json` and
`reports/offline-embedding-candidate-audit.json`. The candidate advisory scan
found no known vulnerabilities; it does not constitute an audit or license
approval of every file collected into the frozen directory. Full application
bundle inventory, licenses, model inclusion, offline enforcement and installed
startup still need qualification. No dependency pin or installer spec was
changed for this probe.

## End-to-end profiled retrieval and ownership checks

At the source tree merged by PR #101 (`ff2a03b0`), a disposable real Chroma
service and explicitly injected local model test the RAG layer, including model
encoding, loopback HTTP vector search and result mapping. The active factory is
unchanged. The threshold remains cosine 0.25; these runs do not tune against
the held-out questions. They reuse the approved small corpus and its repeated
long-document extension, rather than adding independent accuracy examples.

| Case | Held-out top-four targets | Unrelated queries matched | Warm query p95 |
|---|---|---|---|
| Sixteen short sources / 16 vectors | 32/32 | 0/12 | 0.103 s |
| Sixteen long sources / 80 vectors | 32/32 | 0/12 | 0.091 s |
| Sixteen sources plus 1,000 competing other-owner vectors | 32/32 | Not remeasured | 0.085 s |

The first probe reports zero attempted external connections and no results for
a nonexistent owner. The competition probe adds 1,000 other-owner records with
the same source texts/vectors: no record leaks into the target owner's results.
Deleting the target owner removes all 16 target vectors, reports zero remnants,
and preserves the other 1,000; the other owner's recall still returns results.
The competition test exercises metadata filtering, not a large same-owner
knowledge base. Neither result includes the application gateway, UI, provider,
SQL source-eligibility checks or installed startup. Fresh held-out/version-
conflict, larger same-owner, migration/rollback and installed cases remain open.

Generated aggregate evidence:

- `reports/r3-profiled-rag-end-to-end-20261028.json`
- `reports/r3-semantic-owner-competition-20261028.json`

Temporary containers and internal networks were removed and the previously
stopped data machine was returned to stopped. Customer indexes were untouched.

## Separate retained-data migration preflight

The actual Electron data folder is `DataLogicEngine Desktop`, alongside the
older `DataLogicEngine` folder. The recovery set was extended with 217 desktop
files (108,580,368 bytes), all SHA-256 checked, under the restricted local
recovery directory recorded in `HANDOFF.md`. Private database/configuration/
secret contents are not committed.

Read-only managed PostgreSQL inspection finds three sessions and ten messages;
the older SQLite copy has none. Both have zero knowledge/ingestion records.
Chroma has ten chat-history records and no records in its other six existing
collections. With runtime ownership held, a rolled-back read-only SQL transaction
and search comparison find no missing, unmatched or changed text/session/role/
owner values across those ten records. See
`reports/r3-retained-chat-parity-20261028.json`.

A fresh custom-format SQL logical backup was restored into a temporary
PostgreSQL 18 container with no network, no host ports and memory-only data
storage. All 88 application-table counts and sorted JSON row digests match
(36,062 rows). The first disposable setup used the wrong pre-18 data mount;
after inspecting the startup log, the successful setup mounted the parent
`/var/lib/postgresql` required by the retained PostgreSQL 18 image. The clone was
removed and the source container/data machine stopped again. Only aggregate
evidence is committed in `reports/r3-postgresql-logical-restore-20261028.json`;
the private dump remains in the restricted recovery directory. This qualifies
that logical SQL backup, not the entire disk/user-data/multi-store recovery set.

No customer cleanup, customer reindex, cutover, model activation, version bump
or new local application installer ran. Governed source-span/identity and
citation compatibility must be qualified before migration, as listed first in
the current handoff. Source gates, permissions and content-defense controls
must not be weakened to make a derived chunk pass.
