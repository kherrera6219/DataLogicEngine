# Local search evaluation candidate

Status: prepared for Kevin's review; no search activation or acceptance claim.

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

Proposed gates, awaiting owner approval: at least 95% held-out top-four recall,
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
