# Local search evaluation candidate

Status: starting corpus and criteria approved by Kevin on October 28;
qualification in progress, with no search activation or acceptance claim.

This candidate supports R-3 of the frontend/backend/retrieval repair plan.
`retrieval_qualification_v1.json` contains sixteen manually authored fictional
policies, sixteen calibration questions, thirty-two held-out questions, and
twelve unrelated questions. These are fictional test facts, not application
capability claims. No retained customer data is read or changed.

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
